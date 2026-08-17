"""任务接口（发起/查询/结果）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models.task import Task
from backend.schemas.task import TaskCreate, TaskHistoryResponse, TaskResponse
from backend.security import get_current_user
from backend.services import task_service

router = APIRouter(prefix="/tasks")


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    """按 ID 查询任务最新状态（聊天历史恢复时刷新快照用）。"""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if current_user is not None and task.user_id is not None and task.user_id != current_user:
        raise HTTPException(status_code=403, detail="无权查看该任务")
    return task_service._task_response(db, task)


@router.post("", response_model=TaskResponse)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: int | None = Depends(get_current_user),
):
    return task_service.create_task(payload, db, effective_user_id=current_user)


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
    current_user: int | None = Depends(get_current_user),
):
    effective_user = current_user if current_user is not None else user_id
    return task_service.list_tasks(db, effective_user, q, status, date_from, date_to, limit, offset)