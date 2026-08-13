"""工具参数校验（类型/格式）。"""
from datetime import datetime


def validate_args(tool: str, args: dict) -> tuple[bool, str]:
    """校验工具参数，返回 (是否合法, 错误信息)。"""
    if tool == "email":
        return _validate_email(args)
    if tool == "sheets":
        return _validate_sheets(args)
    if tool == "calendar":
        return _validate_calendar(args)
    return True, ""


def _validate_email(args: dict) -> tuple[bool, str]:
    if args.get("action") == "send":
        to = args.get("to", "")
        if not isinstance(to, str) or "@" not in to or not to.strip():
            return False, "收件人邮箱格式不正确"
        if not isinstance(args.get("subject"), str) or not args["subject"].strip():
            return False, "邮件主题不能为空"
    return True, ""


def _validate_sheets(args: dict) -> tuple[bool, str]:
    action = args.get("action", "")
    if action in ("read", "write", "write_by_key"):
        filename = args.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            return False, "文件名不能为空"
    if action == "write_by_key":
        for k in ("key_column", "key_value", "field", "value"):
            if not isinstance(args.get(k), str) or not args[k].strip():
                return False, f"{k} 不能为空"
        return True, ""
    if action == "write":
        changes = args.get("changes")
        if not isinstance(changes, list) or not changes:
            return False, "changes 必须是非空列表"
        for i, c in enumerate(changes):
            if not isinstance(c, dict):
                return False, f"changes[{i}] 必须是对象"
            if not isinstance(c.get("row"), int) or c["row"] < 1:
                return False, f"changes[{i}] 的 row 必须是 >=1 的整数"
            col = c.get("column")
            if not ((isinstance(col, int) and col >= 1) or (isinstance(col, str) and col.strip())):
                return False, f"changes[{i}] 的 column 不合法"
            if not isinstance(c.get("value"), str):
                return False, f"changes[{i}] 的 value 必须是字符串"
    return True, ""


def _validate_calendar(args: dict) -> tuple[bool, str]:
    action = args.get("action", "")
    if action == "create":
        if not isinstance(args.get("summary"), str) or not args["summary"].strip():
            return False, "日程主题不能为空"
        start = _parse_ts(args.get("start_ts"))
        end = _parse_ts(args.get("end_ts"))
        if start is None or end is None:
            return False, "日程时间格式不正确（需 ISO 时间或时间戳）"
        if end <= start:
            return False, "结束时间必须晚于开始时间"
    if action == "update":
        if not isinstance(args.get("event_id"), str) or not args["event_id"].strip():
            return False, "日程 ID 不能为空"
        if not isinstance(args.get("summary"), str) or not args["summary"].strip():
            return False, "日程主题不能为空"
    return True, ""


def _parse_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(datetime.fromisoformat(value).timestamp())
        except ValueError:
            return None
    return None