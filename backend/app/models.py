import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


# ---------------------------------------------------------------------------
# Workspaces — tenant isolation root
# ---------------------------------------------------------------------------
class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    identities: Mapped[list["Identity"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    sources: Mapped[list["Source"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    policies: Mapped[list["Policy"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    audits: Mapped[list["Audit"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    imports: Mapped[list["Import"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Identities — employee / people records from HR
# ---------------------------------------------------------------------------
class Identity(Base):
    __tablename__ = "identities"
    __table_args__ = (
        Index("ix_identities_workspace", "workspace_id"),
        Index("ix_identities_employee", "workspace_id", "employee_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, terminated, leave
    contract_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="identities")
    manager: Mapped["Identity | None"] = relationship(remote_side=[id])
    accounts: Mapped[list["Account"]] = relationship(back_populates="identity")


# ---------------------------------------------------------------------------
# Sources — external systems providing access data
# ---------------------------------------------------------------------------
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # cloud, devops, finance, etc.
    icon: Mapped[str] = mapped_column(String(100), nullable=False)
    last_sync: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="healthy")  # healthy, degraded
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="read")

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="sources")
    accounts: Mapped[list["Account"]] = relationship(back_populates="source")
    entitlements: Mapped[list["Entitlement"]] = relationship(back_populates="source")


# ---------------------------------------------------------------------------
# Accounts — provider-specific user accounts
# ---------------------------------------------------------------------------
class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_workspace", "workspace_id"),
        Index("ix_accounts_source", "source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("identities.id", ondelete="SET NULL"), nullable=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="user")  # user, service, emergency
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="enabled")  # enabled, disabled
    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    source: Mapped["Source"] = relationship(back_populates="accounts")
    identity: Mapped["Identity | None"] = relationship(back_populates="accounts")
    grants: Mapped[list["Grant"]] = relationship(back_populates="account")


# ---------------------------------------------------------------------------
# Entitlements — permissions / roles within a source system
# ---------------------------------------------------------------------------
class Entitlement(Base):
    __tablename__ = "entitlements"
    __table_args__ = (
        Index("ix_entitlements_source", "source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    privileged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_departments: Mapped[list] = mapped_column(ARRAY(String), nullable=False, default=list)

    # relationships
    source: Mapped["Source"] = relationship(back_populates="entitlements")
    grants: Mapped[list["Grant"]] = relationship(back_populates="entitlement")


# ---------------------------------------------------------------------------
# Grants — links accounts to entitlements (who has what access)
# ---------------------------------------------------------------------------
class Grant(Base):
    __tablename__ = "grants"
    __table_args__ = (
        Index("ix_grants_workspace_state", "workspace_id", "state"),
        Index("ix_grants_account", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    entitlement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entitlements.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, revoked
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # relationships
    account: Mapped["Account"] = relationship(back_populates="grants")
    entitlement: Mapped["Entitlement"] = relationship(back_populates="grants")
    reviews: Mapped[list["Review"]] = relationship(back_populates="grant")
    source_access: Mapped[list["SourceAccess"]] = relationship(back_populates="grant")
    remediations: Mapped[list["Remediation"]] = relationship(back_populates="grant")


# ---------------------------------------------------------------------------
# SourceAccess — independent mock source state for remediation verification
# ---------------------------------------------------------------------------
class SourceAccess(Base):
    __tablename__ = "source_access"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    grant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grants.id", ondelete="CASCADE"), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, revoked
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    grant: Mapped["Grant"] = relationship(back_populates="source_access")


# ---------------------------------------------------------------------------
# Campaigns — review campaign grouping
# ---------------------------------------------------------------------------
class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="campaigns")
    reviews: Mapped[list["Review"]] = relationship(back_populates="campaign")


# ---------------------------------------------------------------------------
# Reviews — access review findings with evidence, scores, decisions
# ---------------------------------------------------------------------------
class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_workspace_status", "workspace_id", "status"),
        Index("ix_reviews_grant", "grant_id"),
        # Partial unique index: at most one open review per grant
        Index(
            "ix_reviews_one_open_per_grant",
            "grant_id",
            unique=True,
            postgresql_where="status IN ('pending', 'investigation', 'awaiting_second')",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    grant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grants.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    assignee_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Risk assessment
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="low")  # critical, high, medium, low
    reasons: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Decision state
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending, investigation, awaiting_second, keep, revoke, exception
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    first_actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proposal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Evidence
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    exception_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # relationships
    grant: Mapped["Grant"] = relationship(back_populates="reviews")
    campaign: Mapped["Campaign"] = relationship(back_populates="reviews")
    remediations: Mapped[list["Remediation"]] = relationship(back_populates="review")


# ---------------------------------------------------------------------------
# Remediations — remediation job tracking for revoked access
# ---------------------------------------------------------------------------
class Remediation(Base):
    __tablename__ = "remediations"
    __table_args__ = (
        Index("ix_remediations_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    review_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    grant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("grants.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")  # queued, failed, verified
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_version: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    review: Mapped["Review"] = relationship(back_populates="remediations")
    grant: Mapped["Grant"] = relationship(back_populates="remediations")


# ---------------------------------------------------------------------------
# Policies — configurable risk detection policies
# ---------------------------------------------------------------------------
class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (
        Index("ix_policies_workspace_code", "workspace_id", "code", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # LEAVER, INACTIVE, ORPHANED, etc.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="policies")


# ---------------------------------------------------------------------------
# Audits — append-only audit trail
# ---------------------------------------------------------------------------
class Audit(Base):
    __tablename__ = "audits"
    __table_args__ = (
        Index("ix_audits_workspace_date", "workspace_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    principal: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="audits")


# ---------------------------------------------------------------------------
# Imports — import deduplication and history
# ---------------------------------------------------------------------------
class Import(Base):
    __tablename__ = "imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # hr, access
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="imports")

