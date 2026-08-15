"""任务服务：创建/查询/去重/预览/状态聚合（业务编排层）。"""
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.agent.executor import execute_item, save_item
from backend.agent.planner import plan
from backend.agent.task_status import refresh_task_status
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

MAX_CLARIFY_ROUNDS = 3
DEDUP_WINDOW_SECONDS = 300


def create_task(payload: TaskCreate, db: Session) -> TaskResponse:
    """接收任务 → 去重(可跳过) → 拆解 → 落库 → 低危执行/高危确认 → 聚合任务状态。"""
    if not payload.force:
        cached = _find_recent_duplicate(db, payload.text, payload.user_id)
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
        task = Task(user_id=payload.user_id, text=payload.text, status="need_clarify", question=result["question"])
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

    task = Task(user_id=payload.user_id, text=payload.text, status="planned", question=None)
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
                row.result = json.dumps({"ok": False, "message": ("等待确认：" + preview_text) if preview_text else "等待确认"}, ensure_ascii=False)
                items_out.append(_item_schema(row, conf.id if conf else None))
        else:
            exec_result = execute_item(row.id, db=db)
            if exec_result:
                row.status = "executed" if exec_result["ok"] else "failed"
                row.result = json.dumps(exec_result, ensure_ascii=False)
            items_out.append(_item_schema(row, None, exec_result))

    final_status = refresh_task_status(db, task.id)
    db.commit()
    return TaskResponse(
        task_id=str(task.id),
        status=final_status or task.status,
        text=task.text,
        tasks=items_out,
    )


def list_tasks(
    db: Session,
    user_id: int | None = None,
    q: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> TaskHistoryResponse:
    """查询任务历史：支持用户/关键词/状态(逗号分隔)/时间范围过滤 + 分页。"""
    query = db.query(Task)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    if q:
        query = query.filter(Task.text.like(f"%{q}%"))
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if statuses:
            query = query.filter(Task.status.in_(statuses))
    if date_from:
        query = query.filter(Task.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Task.created_at < end)

    total = query.count()
    tasks = query.order_by(Task.id.desc()).offset(offset).limit(limit).all()
    return TaskHistoryResponse(
        total=total,
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
        ],
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


def _find_recent_duplicate(db: Session, text: str, user_id: int | None = None) -> Task | None:
    """5 分钟内相同文本且不是追问状态的任务 → 复用结果（按用户隔离）。"""
    cutoff = datetime.utcnow() - timedelta(seconds=DEDUP_WINDOW_SECONDS)
    query = db.query(Task).filter(Task.text == text, Task.status != "need_clarify", Task.created_at >= cutoff)
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)
    return query.order_by(Task.id.desc()).first()


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