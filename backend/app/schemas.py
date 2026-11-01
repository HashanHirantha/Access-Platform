import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------
class OrmBase(BaseModel):
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------
class WorkspaceRead(OrmBase):
    id: uuid.UUID
    name: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------
class IdentityRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    employee_id: str
    name: str
    email: str
    department: str
    job_title: str
    manager_id: uuid.UUID | None
    status: str
    contract_end: datetime | None


# ---------------------------------------------------------------------------
# Source
# ---------------------------------------------------------------------------
class SourceRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    category: str
    icon: str
    last_sync: datetime
    status: str
    mode: str


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------
class AccountRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    source_id: uuid.UUID
    identity_id: uuid.UUID | None
    external_id: str
    kind: str
    status: str
    last_active: datetime | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Entitlement
# ---------------------------------------------------------------------------
class EntitlementRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    source_id: uuid.UUID
    name: str
    privileged: bool
    allowed_departments: list[str]


# ---------------------------------------------------------------------------
# Grant
# ---------------------------------------------------------------------------
class GrantRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    account_id: uuid.UUID
    entitlement_id: uuid.UUID
    state: str
    expires_at: datetime | None
    version: int


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------
class CampaignRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    started_at: datetime
    due_at: datetime


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
class ReviewRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    grant_id: uuid.UUID
    campaign_id: uuid.UUID
    assignee_id: str
    score: int
    severity: str
    reasons: list
    codes: list
    recommendation: str
    status: str
    note: str
    first_actor: str | None
    proposal: str | None
    decision_id: uuid.UUID | None
    snapshot_version: int
    source_snapshot_at: datetime
    evidence: dict
    exception_until: datetime | None
    due_at: datetime
    created_at: datetime
    decided_at: datetime | None
    version: int


# ---------------------------------------------------------------------------
# Remediation
# ---------------------------------------------------------------------------
class RemediationRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    review_id: uuid.UUID
    grant_id: uuid.UUID
    status: str
    attempts: int
    expected_version: int
    error: str | None
    evidence: dict | None
    lease_until: datetime | None
    created_at: datetime
    verified_at: datetime | None


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------
class PolicyRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    code: str
    name: str
    description: str
    enabled: bool
    threshold: int


class PolicyUpdate(BaseModel):
    enabled: bool
    threshold: int | None = None


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
class AuditRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    actor: str
    principal: str
    action: str
    target: str
    detail: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
class ImportRead(OrmBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    checksum: str
    filename: str
    kind: str
    row_count: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Workspace Snapshot — full workspace state
# ---------------------------------------------------------------------------
class WorkspaceSnapshot(BaseModel):
    workspace: WorkspaceRead
    identities: list[IdentityRead]
    sources: list[SourceRead]
    accounts: list[AccountRead]
    entitlements: list[EntitlementRead]
    grants: list[GrantRead]
    reviews: list[ReviewRead]
    remediations: list[RemediationRead]
    policies: list[PolicyRead]
    audits: list[AuditRead]
    campaigns: list[CampaignRead]


# ---------------------------------------------------------------------------
# Action request schemas
# ---------------------------------------------------------------------------
class ScanRequest(BaseModel):
    name: str = Field(default="Continuous access review", min_length=3, max_length=80)
    due_days: int = Field(default=7, ge=1, le=30)


class DecideRequest(BaseModel):
    id: uuid.UUID
    version: int
    decision: str  # keep, revoke, investigate, exception
    note: str
    exception_until: datetime | None = None


class ExecuteRequest(BaseModel):
    id: uuid.UUID
    simulate_failure: bool = False


class SyncRequest(BaseModel):
    id: uuid.UUID


class ImportRequest(BaseModel):
    kind: str  # hr, access
    csv: str
    filename: str


class ActionRequest(BaseModel):
    action: str
    # Fields are validated per-action in the service layer


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ActionResponse(BaseModel):
    message: str
    created: int | None = None
    refreshed: int | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str

