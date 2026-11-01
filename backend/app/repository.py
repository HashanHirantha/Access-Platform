"""
Repository — tenant-scoped PostgreSQL data access layer.
"""

import uuid
from datetime import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Workspace, Identity, Source, Account, Entitlement,
    Grant, SourceAccess, Campaign, Review, Remediation,
    Policy, Audit, Import,
)


async def get_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def ensure_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        workspace = Workspace(id=workspace_id, name="Northstar workspace")
        db.add(workspace)
        await db.flush()
    return workspace


async def get_identities(db: AsyncSession, workspace_id: uuid.UUID) -> list[Identity]:
    result = await db.execute(select(Identity).where(Identity.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_sources(db: AsyncSession, workspace_id: uuid.UUID) -> list[Source]:
    result = await db.execute(select(Source).where(Source.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_accounts(db: AsyncSession, workspace_id: uuid.UUID) -> list[Account]:
    result = await db.execute(select(Account).where(Account.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_entitlements(db: AsyncSession, workspace_id: uuid.UUID) -> list[Entitlement]:
    result = await db.execute(select(Entitlement).where(Entitlement.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_grants(db: AsyncSession, workspace_id: uuid.UUID) -> list[Grant]:
    result = await db.execute(select(Grant).where(Grant.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_reviews(db: AsyncSession, workspace_id: uuid.UUID) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.workspace_id == workspace_id).order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())


async def get_remediations(db: AsyncSession, workspace_id: uuid.UUID) -> list[Remediation]:
    result = await db.execute(select(Remediation).where(Remediation.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_policies(db: AsyncSession, workspace_id: uuid.UUID) -> list[Policy]:
    result = await db.execute(select(Policy).where(Policy.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_campaigns(db: AsyncSession, workspace_id: uuid.UUID) -> list[Campaign]:
    result = await db.execute(select(Campaign).where(Campaign.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_audits(db: AsyncSession, workspace_id: uuid.UUID, limit: int = 500) -> list[Audit]:
    result = await db.execute(
        select(Audit)
        .where(Audit.workspace_id == workspace_id)
        .order_by(Audit.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_all_audits(db: AsyncSession, workspace_id: uuid.UUID) -> list[Audit]:
    result = await db.execute(
        select(Audit).where(Audit.workspace_id == workspace_id).order_by(Audit.created_at.desc())
    )
    return list(result.scalars().all())


async def get_imports(db: AsyncSession, workspace_id: uuid.UUID) -> list[Import]:
    result = await db.execute(select(Import).where(Import.workspace_id == workspace_id))
    return list(result.scalars().all())


async def get_review_by_id(db: AsyncSession, review_id: uuid.UUID) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_remediation_by_id(db: AsyncSession, remediation_id: uuid.UUID) -> Remediation | None:
    result = await db.execute(select(Remediation).where(Remediation.id == remediation_id))
    return result.scalar_one_or_none()


async def get_grant_by_id(db: AsyncSession, grant_id: uuid.UUID) -> Grant | None:
    result = await db.execute(select(Grant).where(Grant.id == grant_id))
    return result.scalar_one_or_none()


async def get_source_access_by_grant(db: AsyncSession, grant_id: uuid.UUID) -> SourceAccess | None:
    result = await db.execute(select(SourceAccess).where(SourceAccess.grant_id == grant_id))
    return result.scalar_one_or_none()


async def get_policy_by_id(db: AsyncSession, policy_id: uuid.UUID) -> Policy | None:
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    return result.scalar_one_or_none()


async def check_import_exists(db: AsyncSession, workspace_id: uuid.UUID, checksum: str) -> bool:
    result = await db.execute(
        select(Import.id).where(
            and_(Import.workspace_id == workspace_id, Import.checksum == checksum)
        )
    )
    return result.scalar_one_or_none() is not None


async def create_audit(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    actor: str,
    principal: str,
    action: str,
    target: str,
    detail: str = "",
) -> Audit:
    audit = Audit(
        workspace_id=workspace_id,
        actor=actor,
        principal=principal,
        action=action,
        target=target,
        detail=detail,
    )
    db.add(audit)
    return audit


async def snapshot(db: AsyncSession, workspace_id: uuid.UUID) -> dict:
    """Load complete workspace state for domain processing."""
    return {
        "identities": await get_identities(db, workspace_id),
        "sources": await get_sources(db, workspace_id),
        "accounts": await get_accounts(db, workspace_id),
        "entitlements": await get_entitlements(db, workspace_id),
        "grants": await get_grants(db, workspace_id),
        "reviews": await get_reviews(db, workspace_id),
        "remediations": await get_remediations(db, workspace_id),
        "policies": await get_policies(db, workspace_id),
        "campaigns": await get_campaigns(db, workspace_id),
        "audits": await get_audits(db, workspace_id),
    }

