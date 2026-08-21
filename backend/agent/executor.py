"""子任务执行编排（调工具/过确认闸门）。"""
import json
import time
from datetime import datetime

from backend.db import SessionLocal
from backend.models.task import TaskItem
from backend.safety.whitelist import is_allowed
from backend.tools.registry import get_tool
from backend.tools.validation import validate_args, validate_args_by_schema

REQUIRED_ARGS = {
    "email": {"send": ["to", "subject"], "read": []},
    "sheets": {"write": ["filename", "changes"], "read": ["filename"], "write_by_key": ["filename", "key_column", "key_value", "field", "value"], "aggregate": ["filename", "group_by", "agg"]},
    "calendar": {"create": ["summary", "start_ts", "end_ts"], "update": ["event_id", "summary"]},
    "bitable": {"list_tables": ["app_token"], "list_records": ["app_token", "table_id"], "create_record": ["app_token", "table_id", "fields"], "update_record": ["app_token", "table_id", "record_id", "fields"]},
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


def execute_item(item_id: int, db=None) -> dict:
    """执行一个子任务。db 为空时自建会话（确认后执行场景）；传入 db 则复用当前会话（任务创建场景）。"""
    if db is not None:
        item = db.get(TaskItem, item_id)
        if item is None:
            return {"ok": False, "message": "子任务不存在"}
        result = _run(item, db)
        item.result = json.dumps(result, ensure_ascii=False)
        item.status = "executed" if result["ok"] else "failed"
        return result

    own = SessionLocal()
    try:
        item = own.get(TaskItem, item_id)
        if item is None:
            return {"ok": False, "message": "子任务不存在"}
        result = _run(item, own)
        item.result = json.dumps(result, ensure_ascii=False)
        item.status = "executed" if result["ok"] else "failed"
        own.commit()
        return result
    finally:
        own.close()


def _run(item: TaskItem, db=None) -> dict:
    try:
        args = json.loads(item.args or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "message": "工具参数格式错误"}
    if item.tool.startswith("mcp_"):
        return _run_mcp(item, args, db)
    tool = get_tool(item.tool)
    if tool is None:
        return {"ok": False, "message": f"无法识别工具：{item.tool or '未指定'}"}
    action = args.get("action", "")
    if not is_allowed(item.tool, action):
        return {"ok": False, "message": f"操作不在白名单：{item.tool}.{action}"}
    missing = _missing_args(item.tool, args)
    if missing:
        return {"ok": False, "message": f"参数不足：{'、'.join(missing)}"}
    if getattr(tool, "args_schema", None):
        ok_schema, err_schema = validate_args_by_schema(args, tool.args_schema)
        if not ok_schema:
            return {"ok": False, "message": f"参数不合法：{err_schema}"}
    if item.tool == "email" and action == "send":
        _inject_mail_config(item, args, db)
    ok, error = validate_args(item.tool, args)
    if not ok:
        return {"ok": False, "message": f"参数不合法：{error}"}
    _normalize(item.tool, args)
    before = None
    if item.tool == "sheets" and action in ("write", "write_by_key"):
        before = _sheet_snapshot(args.get("filename", ""))
    result = tool.execute(**args)
    after = _sheet_snapshot(args.get("filename", "")) if before is not None else None
    _audit_tool(item, args, result, before, after, db)
    return {"ok": result.ok, "message": result.message, "data": result.data}


def _run_mcp(item: TaskItem, args: dict, db=None) -> dict:
    """执行外部 MCP 工具（惰性注册后即授权；演示数据源默认只读低危）。"""
    from backend.mcp.client import ensure_mcp_tools

    ensure_mcp_tools()
    tool = get_tool(item.tool)
    if tool is None:
        return {"ok": False, "message": f"MCP 工具不可用：{item.tool}"}
    result = tool.execute(**args)
    _audit_tool(item, args, result, None, None, db)
    return {"ok": result.ok, "message": result.message, "data": result.data}


def _inject_mail_config(item: TaskItem, args: dict, db=None) -> None:
    """发信时优先用用户绑定的邮箱+授权码，未绑定则用系统默认。"""
    own = db is None
    if own:
        db = SessionLocal()
    try:
        from backend.models.task import Task
        from backend.models.user import User

        task = db.get(Task, item.task_id)
        if task and task.user_id:
            user = db.get(User, task.user_id)
            if user and user.qq_mail_address:
                args["mail_address"] = user.qq_mail_address
                args["mail_auth_code"] = user.qq_mail_auth_code
    finally:
        if own:
            db.close()


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

def _sheet_snapshot(filename: str):
    """读表格快照用于审计 diff；失败返回 None。"""
    try:
        from backend.tools.sheets import SheetTool

        r = SheetTool().execute(action="read", filename=filename, limit=200)
        return r.data.get("rows") if r.ok else None
    except Exception:
        return None


def _audit_tool(item: TaskItem, args: dict, result, before, after, db) -> None:
    """记录工具执行审计（best-effort，失败不影响主流程）。"""
    own = db is None
    if own:
        db = SessionLocal()
    try:
        from backend.models.task import Task
        from backend.safety.audit import log_audit

        task = db.get(Task, item.task_id)
        log_audit(
            db,
            user_id=task.user_id if task else None,
            action=f"tool.{item.tool}.{args.get('action', '')}",
            target=str(item.target or ""),
            detail=result.message,
            diff_before=before,
            diff_after=after,
            status="ok" if result.ok else "failed",
        )
        if own:
            db.commit()
    except Exception:
        pass
    finally:
        if own:
            db.close()
