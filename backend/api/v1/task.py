"""任务接口（发起/查询/结果）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.agent.planner import plan
from backend.db import get_db
from backend.models.task import Task, TaskItem
from backend.schemas.task import (
    TaskCreate,
    TaskHistoryResponse,
    TaskItem as TaskItemSchema,
    TaskRecord,
    TaskResponse,
)

router = APIRouter(prefix="/tasks")


@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """接收任务 → 意图拆解 → 落库 → 返回结果。"""
    result = plan(payload.text)
    status = "need_clarify" if result["question"] else "planned"

    task = Task(
        user_id=None,  # 登录态接入后填用户（M2）
        text=payload.text,
        status=status,
        question=result["question"],
    )
    db.add(task)
    db.flush()
    for item in result["tasks"]:
        db.add(TaskItem(task_id=task.id, **item))
    db.commit()
    db.refresh(task)

    return TaskResponse(
        task_id=str(task.id),
        status=task.status,
        text=task.text,
        tasks=result["tasks"],
        question=result["question"],
    )


@router.get("", response_model=TaskHistoryResponse)
def list_tasks(db: Session = Depends(get_db)):
    """查询最近 50 条任务历史。"""
    tasks = db.query(Task).order_by(Task.id.desc()).limit(50).all()
    return TaskHistoryResponse(
        items=[
            TaskRecord(
                task_id=str(t.id),
                text=t.text,
                status=t.status,
                question=t.question,
                created_at=t.created_at.isoformat() if t.created_at else None,
                tasks=[
                    TaskItemSchema(
                        action=i.action, target=i.target, params=i.params, high_risk=i.high_risk
                    )
                    for i in t.items
                ],
            )
            for t in tasks
        ]
    )