"""
Synthetic workspace seed generator for PostgreSQL.
Generates realistic initial people, systems, accounts, entitlements,
grants, policies, review findings, and historical audits.
"""

import uuid
from datetime import datetime, timedelta

from app.domain import assess_access
from app.models import (
    Workspace, Identity, Source, Entitlement, Account,
    Grant, SourceAccess, Policy, Campaign, Review, Audit
)

# Namespace for deterministic UUID generation
WORKSPACE_SEED_NS = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d")


def deterministic_uuid(workspace_id: uuid.UUID, key: str) -> uuid.UUID:
    return uuid.uuid5(WORKSPACE_SEED_NS, f"{workspace_id}:{key}")


def days_ago(days: float, now: datetime) -> datetime:
    return now - timedelta(days=days)


async def seed_workspace_data(db, workspace: Workspace, now: datetime | None = None):
    """Seed a workspace with complete synthetic demo governance data."""
    if now is None:
        now = datetime.utcnow()

    ws_id = workspace.id

    def uid(key: str) -> uuid.UUID:
        return deterministic_uuid(ws_id, key)

    def at(days: float) -> datetime:
        return days_ago(days, now)

    # -----------------------------------------------------------------------
    # 1. Identities (32 employees across departments)
    # -----------------------------------------------------------------------
    people_data = [
        ("Hashan Hirantha", "Engineering", "Cloud Engineer"),
        ("Maya Perera", "Engineering", "Engineering Manager"),
        ("Daniel Silva", "Security", "Security Lead"),
        ("Alex Morgan", "Compliance", "Internal Auditor"),
        ("Nimal Jayawardena", "Finance", "Financial Analyst"),
        ("Kavindi Fernando", "Marketing", "Marketing Executive"),
        ("Chamath Wijesinghe", "Engineering", "Platform Engineer"),
        ("Sarah Mitchell", "Finance", "Finance Manager"),
        ("Dinuka Rathnayake", "Operations", "Operations Analyst"),
        ("Amaya Senanayake", "Engineering", "Software Engineer"),
        ("Ravindu Madushan", "Engineering", "DevOps Engineer"),
        ("Emma Wilson", "Marketing", "Brand Manager"),
        ("Tharushi De Silva", "Finance", "Accountant"),
        ("Kasun Bandara", "Engineering", "Backend Engineer"),
        ("Olivia Chen", "Security", "Security Analyst"),
        ("Isuru Dissanayake", "Operations", "IT Administrator"),
        ("Nethmi Gunasekara", "Marketing", "Content Strategist"),
        ("Liam Anderson", "Engineering", "Frontend Engineer"),
        ("Sahan Kumara", "Finance", "Payments Specialist"),
        ("Ayesha Hassan", "Compliance", "Risk Analyst"),
        ("Dulani Peiris", "Operations", "Service Coordinator"),
        ("Noah Williams", "Engineering", "QA Engineer"),
        ("Yasith Perera", "Engineering", "Data Engineer"),
        ("Sophie Taylor", "Marketing", "Product Designer"),
        ("Malith Karunaratne", "Operations", "Support Engineer"),
        ("Hiruni Wickramasinghe", "Finance", "Financial Analyst"),
        ("Ryan Thomas", "Engineering", "Site Reliability Engineer"),
        ("Anjali Raman", "Security", "IAM Analyst"),
        ("Pasindu Lakshan", "Marketing", "Campaign Analyst"),
        ("Zara Ahmed", "Operations", "Project Coordinator"),
        ("Ashen Silva", "Engineering", "Software Engineer"),
        ("Emily Brown", "Compliance", "Compliance Analyst"),
    ]

    identities: list[Identity] = []
    for i, (name, department, job_title) in enumerate(people_data):
        emp_code = f"EMP{str(i+1).zfill(3)}"
        # Manager logic
        mgr_code = "EMP003" if i in (1, 7) else "EMP008" if department == "Finance" else "EMP002"
        manager_uid = uid(mgr_code) if emp_code != mgr_code else None

        status = "terminated" if i in (4, 18) else "leave" if i == 20 else "active"
        contract_end = at(12) if i == 8 else None

        ident = Identity(
            id=uid(emp_code),
            workspace_id=ws_id,
            employee_id=emp_code,
            name=name,
            email=f"{name.lower().replace(' ', '.')}@northstar.example",
            department=department,
            job_title=job_title,
            manager_id=manager_uid,
            status=status,
            contract_end=contract_end,
        )
        identities.append(ident)
        db.add(ident)

    await db.flush()

    # -----------------------------------------------------------------------
    # 2. Sources (5 connected systems)
    # -----------------------------------------------------------------------
    sources_spec = [
        ("hr", "People directory", "Human resources", "people", 0.04, "Synthetic directory"),
        ("aws", "AWS IAM", "Cloud infrastructure", "aws", 0.08, "Mock connector"),
        ("github", "GitHub Enterprise", "Source control", "github", 0.06, "Mock connector"),
        ("finance", "Finance ERP", "Business application", "finance", 0.12, "Mock connector"),
        ("m365", "Microsoft 365", "Productivity", "microsoft", 0.10, "Mock connector"),
    ]

    sources: dict[str, Source] = {}
    for code, name, category, icon, sync_days, mode in sources_spec:
        src = Source(
            id=uid(code),
            workspace_id=ws_id,
            name=name,
            category=category,
            icon=icon,
            last_sync=at(sync_days),
            status="healthy",
            mode=mode,
        )
        sources[code] = src
        db.add(src)

    # -----------------------------------------------------------------------
    # 3. Entitlements
    # -----------------------------------------------------------------------
    ent_specs = [
        ("aws", "ReadOnlyAccess", False, ["*"]),
        ("aws", "AdministratorAccess", True, ["Engineering", "Security"]),
        ("aws", "BillingAdmin", True, ["Finance"]),
        ("github", "Repository read", False, ["*"]),
        ("github", "Organization owner", True, ["Engineering", "Security"]),
        ("github", "Repository write", False, ["*"]),
        ("finance", "View reports", False, ["*"]),
        ("finance", "Approve payments", True, ["Finance"]),
        ("finance", "Manage payroll", True, ["Finance"]),
        ("m365", "Standard user", False, ["*"]),
        ("m365", "Global administrator", True, ["Operations", "Security"]),
    ]

    entitlements: list[Entitlement] = []
    for i, (src_code, name, privileged, allowed_depts) in enumerate(ent_specs):
        ent = Entitlement(
            id=uid(f"ent{i}"),
            workspace_id=ws_id,
            source_id=sources[src_code].id,
            name=name,
            privileged=privileged,
            allowed_departments=allowed_depts,
        )
        entitlements.append(ent)
        db.add(ent)

    await db.flush()

    # -----------------------------------------------------------------------
    # 4. Accounts & Grants
    # -----------------------------------------------------------------------
    accounts: list[Account] = []
    grants: list[Grant] = []

    for i, ident in enumerate(identities):
        apps = ["m365", "aws" if i % 3 == 0 else "github" if i % 3 == 1 else "finance"]
        if i == 5:
            apps.append("finance")

        for app_code in set(apps):
            src = sources[app_code]
            acc = Account(
                id=uid(f"acc-{i}-{app_code}"),
                workspace_id=ws_id,
                source_id=src.id,
                identity_id=ident.id,
                external_id=ident.email.split("@")[0],
                kind="user",
                status="enabled",
                last_active=at(124 + i) if (i % 7 == 6) else at((i % 8) + 0.2),
                created_at=at(240),
            )
            accounts.append(acc)
            db.add(acc)

            # Assign entitlements
            app_ents = [e for e in entitlements if e.source_id == src.id]
            selected = [app_ents[0]]
            if (i % 4 == 0 or i % 7 == 6 or i == 5 or i == 8) and len(app_ents) > 1:
                selected.append(app_ents[1])

            for k, selected_ent in enumerate(selected):
                grant_id = uid(f"grant-{i}-{app_code}-{k}")
                expires_at = at(4) if (i == 13 and k == 1) else None
                grant = Grant(
                    id=grant_id,
                    workspace_id=ws_id,
                    account_id=acc.id,
                    entitlement_id=selected_ent.id,
                    state="active",
                    expires_at=expires_at,
                    version=1,
                )
                grants.append(grant)
                db.add(grant)

                db.add(SourceAccess(
                    id=grant_id,
                    workspace_id=ws_id,
                    grant_id=grant_id,
                    state="active",
                    version=1,
                    updated_at=now,
                ))

    # Special accounts (orphan & service bot)
    orphan_acc = Account(
        id=uid("acc-orphan"),
        workspace_id=ws_id,
        source_id=sources["aws"].id,
        identity_id=None,
        external_id="legacy.admin",
        kind="user",
        status="enabled",
        last_active=at(106),
        created_at=at(300),
    )
    service_acc = Account(
        id=uid("acc-service"),
        workspace_id=ws_id,
        source_id=sources["github"].id,
        identity_id=None,
        external_id="ci-deployment-bot",
        kind="service",
        status="enabled",
        last_active=None,
        created_at=at(300),
    )
    accounts.extend([orphan_acc, service_acc])
    db.add(orphan_acc)
    db.add(service_acc)

    for i, (spec_acc, ent_idx) in enumerate([(orphan_acc, 1), (service_acc, 5)]):
        g_id = uid(f"grant-special-{i}")
        g = Grant(
            id=g_id,
            workspace_id=ws_id,
            account_id=spec_acc.id,
            entitlement_id=entitlements[ent_idx].id,
            state="active",
            expires_at=None,
            version=1,
        )
        grants.append(g)
        db.add(g)
        db.add(SourceAccess(
            id=g_id,
            workspace_id=ws_id,
            grant_id=g_id,
            state="active",
            version=1,
            updated_at=now,
        ))

    await db.flush()

    # -----------------------------------------------------------------------
    # 5. Policies
    # -----------------------------------------------------------------------
    policy_specs = [
        ("LEAVER", "Departed employees", "Flag enabled accounts belonging to employees who have left.", 0),
        ("INACTIVE", "Inactive access", "Review human accounts with no successful application activity.", 90),
        ("ORPHANED", "Unverified account owners", "Investigate human accounts without a verified employee mapping.", 0),
        ("ROLE_MISMATCH", "Privileged role mismatch", "Compare privileged permissions with approved department baselines.", 0),
        ("CONTRACT", "Expired contractors", "Flag access retained beyond a contractor end date.", 0),
        ("EXPIRED", "Expired temporary access", "Review temporary grants after their approved expiry date.", 0),
    ]

    policies: list[Policy] = []
    for code, name, description, threshold in policy_specs:
        pol = Policy(
            id=uid(f"policy-{code}"),
            workspace_id=ws_id,
            code=code,
            name=name,
            description=description,
            threshold=threshold,
            enabled=True,
        )
        policies.append(pol)
        db.add(pol)

    # -----------------------------------------------------------------------
    # 6. Campaign
    # -----------------------------------------------------------------------
    campaign = Campaign(
        id=uid("campaign-initial"),
        workspace_id=ws_id,
        name="Quarterly access certification",
        started_at=at(6),
        due_at=at(-7),
    )
    db.add(campaign)
    await db.flush()

    # -----------------------------------------------------------------------
    # 7. Reviews
    # -----------------------------------------------------------------------
    policy_dicts = [{"code": p.code, "enabled": p.enabled, "threshold": p.threshold} for p in policies]
    accounts_by_id = {str(a.id): a for a in accounts}
    entitlements_by_id = {str(e.id): e for e in entitlements}
    identities_by_id = {str(i.id): i for i in identities}
    sources_by_id = {str(s.id): s for s in sources.values()}

    reviews: list[Review] = []
    for g in grants:
        acc = accounts_by_id.get(str(g.account_id))
        ent = entitlements_by_id.get(str(g.entitlement_id))
        if not acc or not ent:
            continue
        src = sources_by_id.get(str(acc.source_id))
        if not src:
            continue
        person = identities_by_id.get(str(acc.identity_id)) if acc.identity_id else None

        id_dict = {
            "status": person.status,
            "contract_end": person.contract_end,
            "department": person.department,
        } if person else None

        acc_dict = {
            "kind": acc.kind,
            "status": acc.status,
            "last_active": acc.last_active,
            "created_at": acc.created_at,
        }

        ent_dict = {
            "privileged": ent.privileged,
            "allowed_departments": ent.allowed_departments or [],
        }

        finding = assess_access(
            id_dict, acc_dict, ent_dict,
            {"state": g.state, "expires_at": g.expires_at},
            {"last_sync": src.last_sync, "status": src.status},
            policy_dicts,
            now,
        )
        if not finding:
            continue

        review_id = uid(f"review-{len(reviews) + 1}")
        assignee = str(person.manager_id) if person and person.manager_id else str(uid("EMP003"))

        rev = Review(
            id=review_id,
            workspace_id=ws_id,
            grant_id=g.id,
            campaign_id=campaign.id,
            assignee_id=assignee,
            score=finding.score,
            severity=finding.severity,
            reasons=finding.reasons,
            codes=finding.codes,
            recommendation=finding.recommendation,
            status="pending",
            note="",
            snapshot_version=1,
            source_snapshot_at=src.last_sync,
            evidence={
                "identity": id_dict,
                "account": acc_dict,
                "entitlement": ent_dict,
            },
            due_at=campaign.due_at,
            created_at=at(6 - (len(reviews) % 5)),
            version=1,
        )
        reviews.append(rev)
        db.add(rev)

    # -----------------------------------------------------------------------
    # 8. Historical synthetic decisions and audits
    # -----------------------------------------------------------------------
    non_critical = [r for r in reviews if r.severity != "critical"][-6:]
    for i, r in enumerate(non_critical):
        r.status = "keep"
        r.note = "Demo historical review: owner confirmed a documented business requirement."
        r.decided_at = at(5 - i)
        r.version = 2
        db.add(Audit(
            id=uid(f"audit-historical-{i}"),
            workspace_id=ws_id,
            actor="Maya Perera",
            principal="synthetic-seed",
            action="Access retained",
            target=str(r.id),
            detail=r.note,
            created_at=r.decided_at,
        ))

    db.add(Audit(
        id=uid("audit-seed"),
        workspace_id=ws_id,
        actor="AccessGuard",
        principal="synthetic-seed",
        action="Workspace initialized",
        target="Demo environment",
        detail="Synthetic people, source accounts and review evidence loaded into PostgreSQL. No live credentials required.",
        created_at=now,
    ))

    await db.flush()

