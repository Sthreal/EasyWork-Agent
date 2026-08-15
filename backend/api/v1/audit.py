"""审计查询接口（谁在何时做了什么）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.audit import AuditLog
from backend.schemas.audit import AuditListResponse, AuditRecord
from backend.security import get_current_user

router = APIRouter(prefix="/audit")


@router.get("", response_model=AuditListResponse)
def list_audit(
    user_id: int | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    """最近审计记录；已登录时只返回自己的操作。"""
    query = db.query(AuditLog)
    if current_user is not None:
        query = query.filter(AuditLog.user_id == current_user)
    elif user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    rows = query.order_by(AuditLog.id.desc()).limit(limit).all()
    return AuditListResponse(
        items=[
            AuditRecord(
                id=r.id,
                user_id=r.user_id,
                action_type=r.action_type,
                target=r.target,
                detail=r.detail,
                diff_before=r.diff_before,
                diff_after=r.diff_after,
                status=r.status,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in rows
        ]
    )