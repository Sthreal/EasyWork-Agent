"""高危确认接口（确认/挂起列表）。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agent.executor import execute_item
from backend.agent.task_status import refresh_task_status
from backend.db import get_db
from backend.models.confirmation import Confirmation
from backend.models.task import Task, TaskItem
from backend.safety.gate import decide_confirmation, is_expired
from backend.schemas.confirmation import (
    ConfirmationDecideRequest,
    ConfirmationListResponse,
    ConfirmationResponse,
)
from backend.security import get_current_user

router = APIRouter(prefix="/confirmations")


@router.get("", response_model=ConfirmationListResponse)
def list_confirmations(
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    """待确认动作列表（含超时挂起标记）；已登录时只返回自己任务的确认。"""
    query = db.query(Confirmation).filter_by(status="pending")
    if current_user is not None:
        query = query.join(Task, Task.id == Confirmation.task_id).filter(Task.user_id == current_user)
    rows = query.order_by(Confirmation.id.desc()).limit(50).all()
    return ConfirmationListResponse(items=[_to_response(r, is_expired=is_expired(r)) for r in rows])


@router.post("/{confirmation_id}/decide", response_model=ConfirmationResponse)
def decide(
    confirmation_id: int,
    payload: ConfirmationDecideRequest,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    """确认执行（触发真实执行）/ 拒绝；已处理幂等；跨用户拦截；拒绝标记子任务并聚合任务状态。"""
    effective_user = current_user if current_user is not None else payload.user_id
    row = db.get(Confirmation, confirmation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="确认记录不存在")
    if effective_user is not None and row.task_id:
        owner = db.get(Task, row.task_id)
        if owner and owner.user_id is not None and owner.user_id != effective_user:
            raise HTTPException(status_code=403, detail="无权处理该确认（任务属于其他用户）")
    if row.status != "pending":
        return _to_response(row)

    row = decide_confirmation(db, confirmation_id, payload.approve)
    execution_result = None
    if payload.approve and row.task_item_id:
        execution_result = execute_item(row.task_item_id)
    else:
        if row.task_item_id:
            item = db.get(TaskItem, row.task_item_id)
            if item:
                item.status = "rejected"
                item.result = json.dumps({"ok": False, "message": "已拒绝"}, ensure_ascii=False)
    if row.task_id:
        refresh_task_status(db, row.task_id)
    from backend.safety.audit import log_audit
    log_audit(
        db,
        user_id=effective_user,
        action="confirmation.approve" if payload.approve else "confirmation.reject",
        target=f"{row.action} {row.target}",
        detail={"task_id": row.task_id, "execution_result": execution_result},
        confirmation_id=row.id,
        status=row.status,
    )
    db.commit()
    return _to_response(row, execution_result)


def _parse_preview(raw: str) -> list | None:
    """解析确认记录里的结构化 diff（JSON 字符串 → 列表）；空/坏数据返回 None。"""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _to_response(row: Confirmation, execution_result: dict | None = None, is_expired: bool = False) -> ConfirmationResponse:
    return ConfirmationResponse(
        id=row.id,
        task_id=str(row.task_id) if row.task_id else None,
        action=row.action,
        target=row.target,
        params=row.params,
        preview=_parse_preview(row.preview),
        status=row.status,
        created_at=row.created_at.isoformat() if row.created_at else None,
        execution_result=execution_result,
        is_expired=is_expired,
    )