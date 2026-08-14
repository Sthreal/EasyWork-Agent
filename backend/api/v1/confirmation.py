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

router = APIRouter(prefix="/confirmations")


@router.get("", response_model=ConfirmationListResponse)
def list_confirmations(db: Session = Depends(get_db)):
    """待确认动作列表（含超时挂起标记）。"""
    rows = (
        db.query(Confirmation)
        .filter_by(status="pending")
        .order_by(Confirmation.id.desc())
        .limit(50)
        .all()
    )
    return ConfirmationListResponse(items=[_to_response(r, is_expired=is_expired(r)) for r in rows])


@router.post("/{confirmation_id}/decide", response_model=ConfirmationResponse)
def decide(confirmation_id: int, payload: ConfirmationDecideRequest, db: Session = Depends(get_db)):
    """确认执行（触发真实执行）/ 拒绝；已处理幂等；跨用户拦截；拒绝标记子任务并聚合任务状态。"""
    row = db.get(Confirmation, confirmation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="确认记录不存在")
    if payload.user_id is not None and row.task_id:
        owner = db.get(Task, row.task_id)
        if owner and owner.user_id is not None and owner.user_id != payload.user_id:
            raise HTTPException(status_code=403, detail="无权处理该确认（任务属于其他用户）")
    if row.status != "pending":
        return _to_response(row)

    row = decide_confirmation(db, confirmation_id, payload.approve)
    execution_result = None
    if payload.approve and row.task_item_id:
        execution_result = execute_item(row.task_item_id)
    else:
        # 拒绝：把对应子任务标记为 rejected，结果记录“已拒绝”
        if row.task_item_id:
            item = db.get(TaskItem, row.task_item_id)
            if item:
                item.status = "rejected"
                item.result = json.dumps({"ok": False, "message": "已拒绝"}, ensure_ascii=False)
    if row.task_id:
        refresh_task_status(db, row.task_id)
        db.commit()
    return _to_response(row, execution_result)


def _to_response(row: Confirmation, execution_result: dict | None = None, is_expired: bool = False) -> ConfirmationResponse:
    return ConfirmationResponse(
        id=row.id,
        task_id=str(row.task_id) if row.task_id else None,
        action=row.action,
        target=row.target,
        params=row.params,
        status=row.status,
        created_at=row.created_at.isoformat() if row.created_at else None,
        execution_result=execution_result,
        is_expired=is_expired,
    )