"""
Workspace API router — all workspace endpoints.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain import Actor, DomainError, PERSONAS
from app.config import get_settings
from app import repository as repo
from app import service
from app.schemas import (
    WorkspaceSnapshot, WorkspaceRead,
    IdentityRead, SourceRead, AccountRead, EntitlementRead,
    GrantRead, ReviewRead, RemediationRead, PolicyRead,
    AuditRead, CampaignRead,
    ScanRequest, DecideRequest, ExecuteRequest, PolicyUpdate,
    ImportRequest, ActionResponse,
)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


def resolve_actor(x_demo_persona: str = Header(default="admin")) -> Actor:
    """Resolve demo persona to Actor."""
    persona = PERSONAS.get(x_demo_persona)
    if not persona:
        raise HTTPException(status_code=400, detail=f"Unknown persona: {x_demo_persona}")
    settings = get_settings()
    return Actor(
        key=x_demo_persona,
        name=persona["name"],
        role=persona["role"],
        employee_id=persona["employee_key"],
        principal=settings.DEFAULT_PRINCIPAL,
    )


def get_workspace_id() -> uuid.UUID:
    """In production, derive from authenticated principal. Demo uses a fixed ID."""
    return uuid.UUID("00000000-0000-4000-8000-000000000001")


# ---------------------------------------------------------------------------
# GET /api/workspace — workspace snapshot
# ---------------------------------------------------------------------------
@router.get("", response_model=WorkspaceSnapshot)
async def get_workspace_snapshot(
    export: str | None = None,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(resolve_actor),
):
    workspace_id = get_workspace_id()
    workspace = await repo.ensure_workspace(db, workspace_id)
    await db.commit()

    if export == "audit":
        audits = await repo.get_all_audits(db, workspace_id)
        await repo.create_audit(
            db, workspace_id, actor.name, actor.principal,
            "Audit export", "Full audit history", "",
        )
        await db.commit()
        # Build CSV
        csv_lines = ["id,actor,principal,action,target,detail,created_at"]
        for a in audits:
            row = f"{a.id},{_safe(a.actor)},{_safe(a.principal)},{_safe(a.action)},{_safe(a.target)},{_safe(a.detail)},{a.created_at.isoformat()}"
            csv_lines.append(row)
        return Response(
            content="\n".join(csv_lines),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit-export.csv"},
        )

    if export == "reviews":
        reviews = await repo.get_reviews(db, workspace_id)
        await repo.create_audit(
            db, workspace_id, actor.name, actor.principal,
            "Review export", "Review evidence CSV", "",
        )
        await db.commit()
        csv_lines = ["id,grant_id,campaign_id,score,severity,status,recommendation,decided_at,created_at"]
        for r in reviews:
            row = f"{r.id},{r.grant_id},{r.campaign_id},{r.score},{r.severity},{r.status},{_safe(r.recommendation)},{r.decided_at or ''},{r.created_at.isoformat()}"
            csv_lines.append(row)
        return Response(
            content="\n".join(csv_lines),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=reviews-export.csv"},
        )

    # Full snapshot
    data = await repo.snapshot(db, workspace_id)
    return WorkspaceSnapshot(
        workspace=WorkspaceRead.model_validate(workspace),
        identities=[IdentityRead.model_validate(i) for i in data["identities"]],
        sources=[SourceRead.model_validate(s) for s in data["sources"]],
        accounts=[AccountRead.model_validate(a) for a in data["accounts"]],
        entitlements=[EntitlementRead.model_validate(e) for e in data["entitlements"]],
        grants=[GrantRead.model_validate(g) for g in data["grants"]],
        reviews=[ReviewRead.model_validate(r) for r in data["reviews"]],
        remediations=[RemediationRead.model_validate(r) for r in data["remediations"]],
        policies=[PolicyRead.model_validate(p) for p in data["policies"]],
        audits=[AuditRead.model_validate(a) for a in data["audits"]],
        campaigns=[CampaignRead.model_validate(c) for c in data["campaigns"]],
    )


# ---------------------------------------------------------------------------
# POST /api/workspace — actions
# ---------------------------------------------------------------------------
@router.post("", response_model=ActionResponse)
async def perform_action(
    body: dict,
    db: AsyncSession = Depends(get_db),
    actor: Actor = Depends(resolve_actor),
):
    workspace_id = get_workspace_id()
    await repo.ensure_workspace(db, workspace_id)
    await db.commit()

    action = body.get("action")

    try:
        if action == "scan":
            req = ScanRequest(**{k: v for k, v in body.items() if k != "action"})
            result = await service.perform_scan(db, workspace_id, actor, req.name, req.due_days)
            return ActionResponse(**result)

        elif action == "decide":
            req = DecideRequest(**{k: v for k, v in body.items() if k != "action"})
            result = await service.perform_decide(
                db, workspace_id, actor,
                req.id, req.version, req.decision, req.note, req.exception_until,
            )
            return ActionResponse(**result)

        elif action == "execute":
            req = ExecuteRequest(**{k: v for k, v in body.items() if k != "action"})
            result = await service.perform_execute(db, workspace_id, actor, req.id, req.simulate_failure)
            return ActionResponse(**result)

        elif action == "policy":
            policy_id = uuid.UUID(body["id"])
            enabled = body["enabled"]
            threshold = body.get("threshold")
            result = await service.perform_policy_update(db, workspace_id, actor, policy_id, enabled, threshold)
            return ActionResponse(**result)

        elif action == "import":
            req = ImportRequest(**{k: v for k, v in body.items() if k != "action"})
            result = await service.perform_import(db, workspace_id, actor, req.kind, req.csv, req.filename)
            return ActionResponse(**result)

        elif action == "sync":
            # Placeholder for source sync
            return ActionResponse(message="Source synchronized.")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except DomainError as e:
        raise HTTPException(status_code=e.status, detail=str(e))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe(value: str) -> str:
    """Sanitize CSV cell against formula injection."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{value}"
    return value.replace('"', '""')

