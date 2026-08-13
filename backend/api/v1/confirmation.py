"""高危确认接口（确认/挂起列表）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agent.executor import execute_item
from backend.db import get_db
from backend.models.confirmation import Confirmation
from backend.safety.gate import decide_confirmation
from backend.schemas.confirmation import (
    ConfirmationDecideRequest,
    ConfirmationListResponse,
    ConfirmationResponse,
)

router = APIRouter(prefix="/confirmations")


@router.get("", response_model=ConfirmationListResponse)
def list_confirmations(db: Session = Depends(get_db)):
    """待确认动作列表。"""
    rows = (
        db.query(Confirmation)
        .filter_by(status="pending")
        .order_by(Confirmation.id.desc())
        .limit(50)
        .all()
    )
    return ConfirmationListResponse(items=[_to_response(r) for r in rows])


@router.post("/{confirmation_id}/decide", response_model=ConfirmationResponse)
def decide(confirmation_id: int, payload: ConfirmationDecideRequest, db: Session = Depends(get_db)):
    """确认执行（触发真实执行）/ 拒绝。"""
    row = decide_confirmation(db, confirmation_id, payload.approve)
    if row is None:
        raise HTTPException(status_code=404, detail="确认记录不存在或已处理")
    execution_result = None
    if payload.approve and row.task_item_id:
        execution_result = execute_item(row.task_item_id)
    return _to_response(row, execution_result)


def _to_response(row: Confirmation, execution_result: dict | None = None) -> ConfirmationResponse:
    return ConfirmationResponse(
        id=row.id,
        task_id=str(row.task_id) if row.task_id else None,
        action=row.action,
        target=row.target,
        params=row.params,
        status=row.status,
        created_at=row.created_at.isoformat() if row.created_at else None,
        execution_result=execution_result,
    )