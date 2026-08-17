"""测试：工具参数校验。"""
from backend.tools.validation import validate_args, validate_args_by_schema


def test_email_bad_to():
    ok, msg = validate_args("email", {"action": "send", "to": "not-an-email", "subject": "x"})
    assert ok is False
    assert "邮箱" in msg


def test_email_good():
    ok, msg = validate_args("email", {"action": "send", "to": "a@b.com", "subject": "x", "body": "y"})
    assert ok is True
    assert msg == ""


def test_sheets_changes_not_list():
    ok, msg = validate_args("sheets", {"action": "write", "filename": "a.xlsx", "changes": "bad"})
    assert ok is False
    assert "changes" in msg


def test_sheets_change_bad_row():
    ok, msg = validate_args(
        "sheets",
        {"action": "write", "filename": "a.xlsx", "changes": [{"row": 0, "column": "A", "value": "x"}]},
    )
    assert ok is False
    assert "row" in msg


def test_sheets_change_bad_value_type():
    ok, msg = validate_args(
        "sheets",
        {"action": "write", "filename": "a.xlsx", "changes": [{"row": 1, "column": "A", "value": 123}]},
    )
    assert ok is False
    assert "value" in msg


def test_calendar_bad_time():
    ok, msg = validate_args(
        "calendar",
        {"action": "create", "summary": "开会", "start_ts": "not-a-time", "end_ts": "2026-08-14T16:00"},
    )
    assert ok is False
    assert "时间" in msg


def test_calendar_end_before_start():
    ok, msg = validate_args(
        "calendar",
        {"action": "create", "summary": "开会", "start_ts": "2026-08-14T16:00", "end_ts": "2026-08-14T15:00"},
    )
    assert ok is False
    assert "晚于" in msg


def test_calendar_good():
    ok, msg = validate_args(
        "calendar",
        {"action": "create", "summary": "开会", "start_ts": "2026-08-14T15:00", "end_ts": "2026-08-14T16:00"},
    )
    assert ok is True

def test_sheets_write_by_key_good():
    ok, msg = validate_args(
        "sheets",
        {"action": "write_by_key", "filename": "a.xlsx", "key_column": "姓名", "key_value": "张三", "field": "电话", "value": "138"},
    )
    assert ok is True


def test_sheets_write_by_key_missing_field():
    ok, msg = validate_args(
        "sheets",
        {"action": "write_by_key", "filename": "a.xlsx", "key_column": "姓名", "key_value": "张三", "field": "", "value": "138"},
    )
    assert ok is False
    assert "field" in msg


def test_schema_rejects_missing():
    schema = {"type": "object", "required": ["action", "to"], "properties": {"action": {"type": "string"}, "to": {"type": "string"}}}
    ok, msg = validate_args_by_schema({"action": "send"}, schema)
    assert ok is False
    assert "to" in msg or "required" in msg.lower() or "缺少" in msg


def test_schema_rejects_wrong_type():
    schema = {"type": "object", "required": ["limit"], "properties": {"limit": {"type": "integer"}}}
    ok, msg = validate_args_by_schema({"limit": "abc"}, schema)
    assert ok is False


def test_schema_accepts_valid():
    schema = {"type": "object", "required": ["action"], "properties": {"action": {"type": "string"}}}
    ok, msg = validate_args_by_schema({"action": "read"}, schema)
    assert ok is True



def test_sheets_aggregate_good():
    ok, msg = validate_args(
        "sheets", {"action": "aggregate", "filename": "a.csv", "group_by": "专业", "agg": "count"}
    )
    assert ok is True


def test_sheets_aggregate_bad_agg():
    ok, msg = validate_args(
        "sheets", {"action": "aggregate", "filename": "a.csv", "group_by": "专业", "agg": "avg"}
    )
    assert ok is False
    assert "agg" in msg
