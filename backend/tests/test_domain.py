"""
Unit tests for pure domain logic in AccessGuard.
Tests 6 risk policies, self-review prevention, critical dual approvals.
"""

from datetime import datetime, timedelta
import pytest

from app.domain import (
    assess_access, authorize_review, Actor, DomainError,
    days_between, iso_days_ago
)


@pytest.fixture
def now():
    return datetime(2026, 11, 1, 12, 0, 0)


@pytest.fixture
def base_policies():
    return [
        {"code": "LEAVER", "enabled": True, "threshold": 0},
        {"code": "INACTIVE", "enabled": True, "threshold": 90},
        {"code": "ORPHANED", "enabled": True, "threshold": 0},
        {"code": "ROLE_MISMATCH", "enabled": True, "threshold": 0},
        {"code": "CONTRACT", "enabled": True, "threshold": 0},
        {"code": "EXPIRED", "enabled": True, "threshold": 0},
    ]


@pytest.fixture
def base_context(now):
    identity = {
        "status": "active",
        "contract_end": None,
        "department": "Engineering",
    }
    account = {
        "kind": "user",
        "status": "enabled",
        "last_active": now - timedelta(days=5),
        "created_at": now - timedelta(days=200),
    }
    entitlement = {
        "privileged": False,
        "allowed_departments": ["*"],
    }
    grant = {
        "state": "active",
        "expires_at": None,
    }
    source = {
        "last_sync": now - timedelta(hours=1),
        "status": "healthy",
    }
    return identity, account, entitlement, grant, source


def test_clean_access_returns_none(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is None


def test_leaver_policy_triggers_critical(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    identity["status"] = "terminated"

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "LEAVER" in finding.codes
    assert finding.score == 100
    assert finding.severity == "critical"


def test_orphaned_account_triggers_high(base_context, base_policies, now):
    _, account, entitlement, grant, source = base_context
    identity = None  # No linked identity

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "ORPHANED" in finding.codes
    assert finding.score == 78
    assert finding.severity == "high"


def test_inactive_privileged_policy_triggers(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    account["last_active"] = now - timedelta(days=95)
    entitlement["privileged"] = True

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "INACTIVE" in finding.codes
    assert finding.score == 85
    assert finding.severity == "high"


def test_inactive_ignored_if_employee_on_leave(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    identity["status"] = "leave"
    account["last_active"] = now - timedelta(days=120)

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is None


def test_role_mismatch_policy_triggers(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    identity["department"] = "Marketing"
    entitlement["privileged"] = True
    entitlement["allowed_departments"] = ["Finance", "Engineering"]

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "ROLE_MISMATCH" in finding.codes
    assert finding.score == 82
    assert finding.severity == "high"


def test_contract_expired_policy(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    identity["contract_end"] = now - timedelta(days=2)

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "CONTRACT" in finding.codes
    assert finding.score == 90
    assert finding.severity == "critical"


def test_temporary_permission_expired(base_context, base_policies, now):
    identity, account, entitlement, grant, source = base_context
    grant["expires_at"] = now - timedelta(days=1)

    finding = assess_access(identity, account, entitlement, grant, source, base_policies, now)
    assert finding is not None
    assert "EXPIRED" in finding.codes
    assert finding.score == 88


def test_self_review_prevention():
    actor = Actor(key="reviewer", name="Maya Perera", role="reviewer", employee_id="EMP002", principal="test")
    review = {"status": "pending", "assignee_id": "EMP002"}

    # Attempting to review own identity
    with pytest.raises(DomainError) as exc:
        authorize_review(actor, review, identity_id="EMP002", decision="keep")
    assert "You cannot review your own access" in str(exc.value)


def test_critical_second_approval_requires_independent_actor():
    actor = Actor(key="security", name="Daniel Silva", role="security", employee_id="EMP003", principal="test")
    review = {
        "status": "awaiting_second",
        "assignee_id": "EMP002",
        "first_actor": "EMP003",  # Same actor already gave first approval!
    }

    with pytest.raises(DomainError) as exc:
        authorize_review(actor, review, identity_id="EMP005", decision="keep")
    assert "The same person cannot provide both approvals" in str(exc.value)

