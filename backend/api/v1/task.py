"""任务接口（发起/查询/结果）。"""
import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.agent.executor import execute_item, save_item
from backend.agent.planner import plan
from backend.db import get_db
from backend.models.confirmation import Confirmation
from backend.models.task import Task, TaskItem
from backend.safety.gate import create_confirmation
from backend.schemas.task import (
    TaskCreate,
    TaskHistoryResponse,
    TaskItem as TaskItemSchema,
    TaskRecord,
    TaskResponse,
)

router = APIRouter(prefix="/tasks")

MAX_CLARIFY_ROUNDS = 3
DEDUP_WINDOW_SECONDS = 300


@router.post("", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """接收任务 → 去重 → 拆解 → 落库 → 低危执行/高危确认。"""
    cached = _find_recent_duplicate(db, payload.text)
    if cached:
        return _task_response(db, cached)

    result = plan(payload.text)

    if result["question"]:
        if payload.round > MAX_CLARIFY_ROUNDS:
            return TaskResponse(
                task_id="",
                status="too_many_rounds",
                text=payload.text,
                tasks=[],
                message="追问次数已达上限，请重新描述任务",
            )
        task = Task(user_id=None, text=payload.text, status="need_clarify", question=result["question"])
        db.add(task)
        db.commit()
        db.refresh(task)
        return TaskResponse(
            task_id=str(task.id),
            status=task.status,
            text=task.text,
            tasks=[],
            question=result["question"],
        )

    task = Task(user_id=None, text=payload.text, status="planned", question=None)
    db.add(task)
    db.flush()

    items_out = []
    for item in result["tasks"]:
        row = save_item(db, task.id, item)
        db.flush()
        if item.get("high_risk") and item.get("tool"):
            preview_text, preview_error = _sheets_preview(item)
            if preview_error:
                row.status = "failed"
                row.result = json.dumps({"ok": False, "message": preview_error}, ensure_ascii=False)
                items_out.append(_item_schema(row, None))
            else:
                conf = create_confirmation(
                    db,
                    task_id=task.id,
                    task_item_id=row.id,
                    action=item["action"],
                    target=item["target"],
                    params=preview_text or item["params"],
                )
                row.status = "pending_confirm"
                row.result = json.dumps({"ok": False, "message": "等待确认"}, ensure_ascii=False)
                items_out.append(_item_schema(row, conf.id if conf else None))
        else:
            exec_result = execute_item(row.id, db=db)
            if exec_result:
                row.status = "executed" if exec_result["ok"] else "failed"
                row.result = json.dumps(exec_result, ensure_ascii=False)
            items_out.append(_item_schema(row, None, exec_result))

    db.commit()
    return TaskResponse(
        task_id=str(task.id),
        status=task.status,
        text=task.text,
        tasks=items_out,
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
                tasks=[_item_schema(i, _confirmation_id(db, i.id)) for i in t.items],
            )
            for t in tasks
        ]
    )


def _sheets_preview(item: dict) -> tuple[str, str | None]:
    """改表格高危动作：先读表定位，生成人话预览。返回 (预览文本, 错误)。"""
    args = item.get("args") or {}
    if item.get("tool") != "sheets" or args.get("action") != "write_by_key":
        return item.get("params", ""), None
    try:
        from backend.tools.sheets import SheetTool

        target = SheetTool().find_cell(
            filename=args["filename"],
            key_column=args.get("key_column", "姓名"),
            key_value=args.get("key_value", ""),
            field=args.get("field", ""),
        )
        preview = (
            f"将修改 {args['filename']}：{args.get('key_column')}={args.get('key_value')} 的 "
            f"{args.get('field')}（第{target['row']}行{target['column']}列），"
            f"{target['old']} → {args.get('value')}"
        )
        return preview, None
    except Exception as exc:  # noqa: BLE001
        return "", str(exc)


def _find_recent_duplicate(db: Session, text: str) -> Task | None:
    """5 分钟内相同文本且不是追问状态的任务 → 复用结果。"""
    cutoff = datetime.utcnow() - timedelta(seconds=DEDUP_WINDOW_SECONDS)
    return (
        db.query(Task)
        .filter(Task.text == text, Task.status != "need_clarify", Task.created_at >= cutoff)
        .order_by(Task.id.desc())
        .first()
    )


def _task_response(db: Session, task: Task) -> TaskResponse:
    return TaskResponse(
        task_id=str(task.id),
        status=task.status,
        text=task.text,
        question=task.question,
        tasks=[_item_schema(i, _confirmation_id(db, i.id)) for i in task.items],
    )


def _confirmation_id(db: Session, item_id: int) -> int | None:
    conf = (
        db.query(Confirmation)
        .filter(Confirmation.task_item_id == item_id, Confirmation.status == "pending")
        .first()
    )
    return conf.id if conf else None


def _item_schema(row: TaskItem, confirmation_id: int | None = None, exec_result: dict | None = None) -> TaskItemSchema:
    try:
        args = json.loads(row.args or "{}")
    except json.JSONDecodeError:
        args = {}
    return TaskItemSchema(
        action=row.action,
        target=row.target,
        params=row.params,
        high_risk=row.high_risk,
        tool=row.tool,
        args=args,
        status=row.status,
        result=row.result,
        confirmation_id=confirmation_id,
    )