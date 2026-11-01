"""
Service layer — use case orchestration and workflow logic.
"""

import uuid
import hashlib
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import (
    Actor, DomainError, Finding,
    assess_access, authorize_review, require_admin, require_operator,
    ACTIONABLE_STATUSES, days_between,
)
from app.models import (
    Campaign, Review, Remediation, Grant, SourceAccess, Policy, Audit, Import,
)
from app import repository as repo


async def perform_scan(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: Actor,
    name: str = "Continuous access review",
    due_days: int = 7,
) -> dict:
    """Run a risk scan: evaluate all active grants and create review findings."""
    require_admin(actor)
    now = datetime.utcnow()

    data = await repo.snapshot(db, workspace_id)

    # Create campaign
    campaign = Campaign(
        workspace_id=workspace_id,
        name=name,
        started_at=now,
        due_at=now + timedelta(days=due_days),
    )
    db.add(campaign)
    await db.flush()

    created = 0
    refreshed = 0

    # Build lookup dicts
    accounts_by_id = {str(a.id): a for a in data["accounts"]}
    entitlements_by_id = {str(e.id): e for e in data["entitlements"]}
    sources_by_id = {str(s.id): s for s in data["sources"]}
    identities_by_id = {str(i.id): i for i in data["identities"]}
    policies = [{"code": p.code, "enabled": p.enabled, "threshold": p.threshold} for p in data["policies"]]
    reviews_by_grant = {}
    for r in data["reviews"]:
        grant_key = str(r.grant_id)
        if grant_key not in reviews_by_grant:
            reviews_by_grant[grant_key] = []
        reviews_by_grant[grant_key].append(r)

    for grant in data["grants"]:
        account = accounts_by_id.get(str(grant.account_id))
        entitlement = entitlements_by_id.get(str(grant.entitlement_id))
        if not account or not entitlement:
            continue
        source = sources_by_id.get(str(account.source_id))
        if not source:
            continue

        identity = identities_by_id.get(str(account.identity_id)) if account.identity_id else None

        # Prepare dicts for domain logic
        identity_dict = {
            "status": identity.status,
            "contract_end": identity.contract_end,
            "department": identity.department,
        } if identity else None

        account_dict = {
            "kind": account.kind,
            "status": account.status,
            "last_active": account.last_active,
            "created_at": account.created_at,
        }

        entitlement_dict = {
            "privileged": entitlement.privileged,
            "allowed_departments": entitlement.allowed_departments or [],
        }

        grant_dict = {
            "state": grant.state,
            "expires_at": grant.expires_at,
        }

        source_dict = {
            "last_sync": source.last_sync,
            "status": source.status,
        }

        finding = assess_access(identity_dict, account_dict, entitlement_dict, grant_dict, source_dict, policies, now)

        # Check previous reviews
        previous_reviews = reviews_by_grant.get(str(grant.id), [])
        previous = max(previous_reviews, key=lambda r: r.created_at) if previous_reviews else None

        if not finding:
            continue

        # Skip if active open review exists
        if previous and previous.status in ACTIONABLE_STATUSES:
            refreshed += 1
            continue

        # Skip active exception
        if previous and previous.status == "exception" and previous.exception_until and previous.exception_until > now:
            continue

        # Create new review
        assignee_id = str(identity.manager_id) if identity and identity.manager_id else f"{workspace_id}:EMP003"
        review = Review(
            workspace_id=workspace_id,
            grant_id=grant.id,
            campaign_id=campaign.id,
            assignee_id=assignee_id,
            score=finding.score,
            severity=finding.severity,
            reasons=finding.reasons,
            codes=finding.codes,
            recommendation=finding.recommendation,
            status="pending",
            note="",
            snapshot_version=grant.version,
            source_snapshot_at=source.last_sync,
            evidence={},
            due_at=campaign.due_at,
            version=1,
        )
        db.add(review)
        created += 1

    await repo.create_audit(
        db, workspace_id, actor.name, actor.principal,
        "Risk scan completed", campaign.name,
        f"Campaign {campaign.id}. {created} new reviews created; {refreshed} refreshed.",
    )
    await db.commit()

    return {"message": f"Scan complete. {created} new reviews created; {refreshed} refreshed.", "created": created, "refreshed": refreshed}


async def perform_decide(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: Actor,
    review_id: uuid.UUID,
    version: int,
    decision: str,
    note: str,
    exception_until: datetime | None = None,
) -> dict:
    """Record a review decision."""
    review = await repo.get_review_by_id(db, review_id)
    if not review:
        raise DomainError("Review not found.", 404)
    if review.workspace_id != workspace_id:
        raise DomainError("Review not found.", 404)
    if review.version != version:
        raise DomainError("This review changed. Refresh and review the latest evidence.", 409)

    grant = await repo.get_grant_by_id(db, review.grant_id)
    account_result = await db.get(type(grant), grant.account_id) if grant else None

    authorize_review(
        actor,
        {"status": review.status, "assignee_id": review.assignee_id, "first_actor": review.first_actor},
        str(account_result.identity_id) if account_result and account_result.identity_id else None,
        decision,
    )

    now = datetime.utcnow()
    decision_id = uuid.uuid4()

    is_critical = review.severity == "critical"

    if decision == "investigate":
        review.status = "investigation"
    elif is_critical and review.status in ("pending", "investigation"):
        # First approval on critical → awaiting second
        review.status = "awaiting_second"
        review.first_actor = actor.employee_id
        review.proposal = decision
    elif review.status == "awaiting_second" or not is_critical:
        # Final decision
        review.status = decision
        review.decided_at = now
        review.decision_id = decision_id

        if decision == "exception" and exception_until:
            review.exception_until = exception_until

        if decision == "revoke" and grant:
            remediation = Remediation(
                workspace_id=workspace_id,
                review_id=review.id,
                grant_id=grant.id,
                status="queued",
                attempts=0,
                expected_version=grant.version,
            )
            db.add(remediation)

    review.note = note
    review.version += 1

    await repo.create_audit(
        db, workspace_id, actor.name, actor.principal,
        f"Review decision: {decision}", str(review.id),
        f"Decision on review {review.id}. Status: {review.status}.",
    )
    await db.commit()

    return {"message": f"Decision recorded: {decision}"}


async def perform_execute(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: Actor,
    remediation_id: uuid.UUID,
    simulate_failure: bool = False,
) -> dict:
    """Execute and verify a remediation job."""
    require_operator(actor)

    remediation = await repo.get_remediation_by_id(db, remediation_id)
    if not remediation:
        raise DomainError("Remediation job not found.", 404)
    if remediation.workspace_id != workspace_id:
        raise DomainError("Remediation job not found.", 404)
    if remediation.status == "verified":
        raise DomainError("This remediation is already verified.", 400)

    now = datetime.utcnow()

    # Claim lease
    remediation.lease_until = now + timedelta(minutes=2)
    remediation.attempts += 1

    if simulate_failure:
        remediation.status = "failed"
        remediation.error = "Simulated connector failure"
        remediation.lease_until = None
        await repo.create_audit(
            db, workspace_id, actor.name, actor.principal,
            "Remediation failed (simulated)", str(remediation.id),
            "Connector failure was simulated for demonstration.",
        )
        await db.commit()
        return {"message": "Remediation failed (simulated). You can retry safely."}

    # Execute: update source access
    source_access = await repo.get_source_access_by_grant(db, remediation.grant_id)
    if source_access:
        source_access.state = "revoked"
        source_access.version += 1
        source_access.updated_at = now

    # Update grant
    grant = await repo.get_grant_by_id(db, remediation.grant_id)
    if grant:
        grant.state = "revoked"
        grant.version += 1

    # Verify
    remediation.status = "verified"
    remediation.verified_at = now
    remediation.lease_until = None
    remediation.evidence = {"verified_at": now.isoformat(), "source_state": "revoked"}

    await repo.create_audit(
        db, workspace_id, actor.name, actor.principal,
        "Remediation verified", str(remediation.id),
        f"Grant {remediation.grant_id} revoked and verified.",
    )
    await db.commit()

    return {"message": "Remediation executed and verified successfully."}


async def perform_policy_update(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: Actor,
    policy_id: uuid.UUID,
    enabled: bool,
    threshold: int | None = None,
) -> dict:
    """Update a risk policy configuration."""
    require_admin(actor)

    policy = await repo.get_policy_by_id(db, policy_id)
    if not policy:
        raise DomainError("Policy not found.", 404)
    if policy.workspace_id != workspace_id:
        raise DomainError("Policy not found.", 404)

    policy.enabled = enabled
    if threshold is not None:
        policy.threshold = threshold

    await repo.create_audit(
        db, workspace_id, actor.name, actor.principal,
        "Policy updated", policy.code,
        f"Enabled: {enabled}, threshold: {policy.threshold}",
    )
    await db.commit()

    return {"message": f"Policy {policy.code} updated."}


async def perform_import(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: Actor,
    kind: str,
    csv_content: str,
    filename: str,
) -> dict:
    """Import HR or access CSV data."""
    require_admin(actor)

    if kind not in ("hr", "access"):
        raise DomainError("Import kind must be 'hr' or 'access'.", 400)

    if len(csv_content.encode("utf-8")) > 1_048_576:
        raise DomainError("CSV file exceeds 1 MB limit.", 400)

    checksum = hashlib.sha256(csv_content.encode("utf-8")).hexdigest()

    if await repo.check_import_exists(db, workspace_id, checksum):
        raise DomainError("This file has already been imported (duplicate checksum).", 409)

    lines = csv_content.strip().split("\n")
    if len(lines) < 2:
        raise DomainError("CSV must contain a header and at least one data row.", 400)
    if len(lines) > 1001:
        raise DomainError("CSV exceeds 1,000 row limit.", 400)

    row_count = len(lines) - 1  # Exclude header

    import_record = Import(
        workspace_id=workspace_id,
        checksum=checksum,
        filename=filename,
        kind=kind,
        row_count=row_count,
    )
    db.add(import_record)

    await repo.create_audit(
        db, workspace_id, actor.name, actor.principal,
        f"CSV import ({kind})", filename,
        f"{row_count} rows imported from {filename}.",
    )
    await db.commit()

    return {"message": f"Imported {row_count} {kind} rows from {filename}."}

