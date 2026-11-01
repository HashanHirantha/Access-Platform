"""
Pure domain logic — risk assessment, authorization, decision rules.
No I/O, no database access. Mirrors lib/domain.ts from the frontend.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
Severity = Literal["critical", "high", "medium", "low"]
ReviewStatus = Literal["pending", "investigation", "awaiting_second", "keep", "revoke", "exception"]

ACTIONABLE_STATUSES = {"pending", "investigation", "awaiting_second"}

PERSONAS = {
    "admin": {"name": "Hashan Hirantha", "label": "Workspace admin", "role": "admin", "employee_key": "EMP001", "initials": "HH"},
    "reviewer": {"name": "Maya Perera", "label": "Department reviewer", "role": "reviewer", "employee_key": "EMP002", "initials": "MP"},
    "security": {"name": "Daniel Silva", "label": "Security reviewer", "role": "security", "employee_key": "EMP003", "initials": "DS"},
    "auditor": {"name": "Alex Morgan", "label": "Read-only auditor", "role": "auditor", "employee_key": "EMP004", "initials": "AM"},
}


@dataclass
class Actor:
    key: str
    name: str
    role: str
    employee_id: str
    principal: str


class DomainError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def days_between(earlier: datetime, later: datetime) -> int:
    return (later - earlier).days


def iso_days_ago(days: int, now: datetime | None = None) -> datetime:
    return (now or datetime.utcnow()) - timedelta(days=days)


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    score: int
    severity: Severity
    reasons: list[str]
    codes: list[str]
    recommendation: str


def assess_access(
    identity: dict | None,
    account: dict,
    entitlement: dict,
    grant: dict,
    source: dict,
    policies: list[dict],
    now: datetime,
) -> Finding | None:
    """Evaluate a single grant against enabled policies. Returns None if clean."""
    reasons: list[str] = []
    codes: list[str] = []
    scores: list[int] = []

    def active(code: str) -> dict | None:
        return next((p for p in policies if p["code"] == code and p["enabled"]), None)

    def flag(code: str, score: int, reason: str):
        codes.append(code)
        scores.append(score)
        reasons.append(reason)

    if grant["state"] != "active" or account["status"] != "enabled":
        return None

    # Data quality
    stale = days_between(source["last_sync"], now) > 2 or source["status"] != "healthy"
    if stale:
        flag("DATA_QUALITY", 45, "Source evidence is stale or unavailable. Refresh the source before deciding.")

    # Orphaned account
    if not identity and account["kind"] == "user" and active("ORPHANED"):
        flag("ORPHANED", 78, "No verified employee owner is linked to this human account. Investigate the identity mapping.")

    # Leaver
    if identity and identity["status"] == "terminated" and active("LEAVER"):
        flag("LEAVER", 100, "The employee has left the organization, but this account is still enabled.")

    # Expired contractor
    if identity and identity.get("contract_end") and identity["contract_end"] < now and active("CONTRACT"):
        flag("CONTRACT", 90, "The contractor end date has passed while access remains active.")

    # Expired temporary permission
    if grant.get("expires_at") and grant["expires_at"] < now and active("EXPIRED"):
        flag("EXPIRED", 88, "This temporary permission has passed its approved expiry date.")

    # Inactive
    inactive_policy = active("INACTIVE")
    if inactive_policy and account["kind"] == "user" and (not identity or identity["status"] != "leave"):
        threshold = inactive_policy["threshold"]
        account_age = days_between(account["created_at"], now)
        if account_age >= threshold:
            if account.get("last_active"):
                inactive_days = days_between(account["last_active"], now)
                if inactive_days >= threshold:
                    score = 85 if entitlement["privileged"] else 56
                    flag("INACTIVE", score, f"No successful application activity for {inactive_days} days (policy: {threshold} days).")
            else:
                flag("DATA_QUALITY", 40, "Successful activity data is missing. Confirm usage before removing access.")

    # Role mismatch
    if (identity and entitlement["privileged"] and active("ROLE_MISMATCH")
            and "*" not in entitlement["allowed_departments"]
            and identity["department"] not in entitlement["allowed_departments"]):
        flag("ROLE_MISMATCH", 82, f"This privileged permission is outside the approved access baseline for {identity['department']}.")

    if not scores:
        return None

    score = max(scores)
    severity: Severity = "critical" if score >= 90 else "high" if score >= 70 else "medium" if score >= 40 else "low"

    uncertain = stale or "ORPHANED" in codes or (len(codes) == 1 and codes[0] == "DATA_QUALITY")
    recommendation = (
        "Investigate the uncertain evidence before deciding"
        if uncertain
        else "Remove access immediately" if score >= 90
        else "Review and remove access" if score >= 70
        else "Confirm the current business requirement"
    )

    return Finding(score=score, severity=severity, reasons=reasons, codes=codes, recommendation=recommendation)


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------
def authorize_review(actor: Actor, review: dict, identity_id: str | None, decision: str):
    """Check that the actor is allowed to decide on this review."""
    if actor.role == "auditor":
        raise DomainError("Auditors cannot make review decisions.", 403)

    # Self-review prevention
    if identity_id and actor.employee_id == identity_id:
        raise DomainError("You cannot review your own access.", 403)

    status = review["status"]

    if status == "awaiting_second":
        # Second approval must be independent
        if review.get("first_actor") == actor.employee_id:
            raise DomainError("The same person cannot provide both approvals for a critical review.", 403)
        if actor.role not in ("admin", "security"):
            raise DomainError("Only an admin or security reviewer can provide the second approval.", 403)
    elif status in ("pending", "investigation"):
        # Must be assigned reviewer, admin, or security
        is_assigned = review["assignee_id"] == actor.employee_id
        if not is_assigned and actor.role not in ("admin", "security"):
            raise DomainError("You are not assigned to this review.", 403)
    else:
        raise DomainError(f"This review is already decided ({status}).", 400)


def require_admin(actor: Actor):
    if actor.role != "admin":
        raise DomainError("Only the workspace admin can perform this action.", 403)


def require_operator(actor: Actor):
    if actor.role not in ("admin", "security"):
        raise DomainError("An admin or security reviewer is required.", 403)

