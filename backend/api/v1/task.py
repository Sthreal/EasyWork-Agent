"""任务接口（发起/查询/结果）。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.schemas.task import TaskCreate, TaskHistoryResponse, TaskResponse
from backend.services import task_service

router = APIRouter(prefix="/tasks")


@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return task_service.create_task(payload, db)


@router.get("", response_model=TaskHistoryResponse)
def list_tasks(
    user_id: int | None = None,
    q: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return task_service.list_tasks(db, user_id, q, status, date_from, date_to, limit, offset)