"""子任务执行编排（调工具/过确认闸门）。"""
import json
import time
from datetime import datetime

from backend.db import SessionLocal
from backend.models.task import TaskItem
from backend.tools.registry import get_tool
from backend.tools.validation import validate_args

REQUIRED_ARGS = {
    "email": {"send": ["to", "subject"], "read": []},
    "sheets": {"write": ["filename", "changes"], "read": ["filename"]},
    "calendar": {"create": ["summary", "start_ts", "end_ts"], "update": ["event_id", "summary"]},
}


def save_item(db, task_id: int, item: dict) -> TaskItem:
    """把拆解出的子任务写入 task_items。"""
    row = TaskItem(
        task_id=task_id,
        action=item.get("action", ""),
        target=item.get("target", ""),
        params=item.get("params", ""),
        high_risk=bool(item.get("high_risk", False)),
        tool=item.get("tool", ""),
        args=json.dumps(item.get("args") or {}, ensure_ascii=False),
        status="pending",
    )
    db.add(row)
    return row


def execute_item(item_id: int) -> dict:
    """执行一个子任务（低危直接调 / 高危确认后调）。"""
    db = SessionLocal()
    try:
        item = db.get(TaskItem, item_id)
        if item is None:
            return {"ok": False, "message": "子任务不存在"}
        result = _run(item)
        item.result = json.dumps(result, ensure_ascii=False)
        item.status = "executed" if result["ok"] else "failed"
        db.commit()
        return result
    finally:
        db.close()


def _run(item: TaskItem) -> dict:
    tool = get_tool(item.tool)
    if tool is None:
        return {"ok": False, "message": f"无法识别工具：{item.tool or '未指定'}"}
    try:
        args = json.loads(item.args or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "message": "工具参数格式错误"}
    missing = _missing_args(item.tool, args)
    if missing:
        return {"ok": False, "message": f"参数不足：{'、'.join(missing)}"}
    ok, error = validate_args(item.tool, args)
    if not ok:
        return {"ok": False, "message": f"参数不合法：{error}"}
    _normalize(item.tool, args)
    result = tool.execute(**args)
    return {"ok": result.ok, "message": result.message, "data": result.data}


def _missing_args(tool: str, args: dict) -> list[str]:
    action = args.get("action", "")
    required = REQUIRED_ARGS.get(tool, {}).get(action, [])
    return [k for k in required if not args.get(k)]


def _normalize(tool: str, args: dict) -> None:
    if tool == "calendar" and args.get("action") == "create":
        for key in ("start_ts", "end_ts"):
            v = args.get(key)
            if isinstance(v, str):
                try:
                    args[key] = int(time.mktime(datetime.fromisoformat(v).timetuple()))
                except ValueError:
                    args[key] = None