"""测试：飞书多维表格工具（mock 飞书 API）。"""
import httpx

from backend.tools import bitable as bitable_mod
from backend.tools.base import ToolResult
from backend.tools.registry import get_tool
from backend.tools.selector import select_tools
from backend.safety.whitelist import is_allowed
from backend.tools.validation import validate_args


def _fake_resp(payload: dict, status: int = 200):
    return httpx.Response(status, json=payload, request=httpx.Request("GET", "http://x"))


def test_bitable_list_tables(monkeypatch):
    monkeypatch.setattr(bitable_mod, "get_valid_token", lambda db, uid: type("T", (), {"access_token": "tk"})())
    monkeypatch.setattr(
        bitable_mod.httpx, "get",
        lambda *a, **k: _fake_resp({"code": 0, "data": {"items": [{"table_id": "tbl1", "name": "报名表"}, {"table_id": "tbl2", "name": "订单"}]}}),
    )
    tool = get_tool("bitable")
    result = tool.execute(action="list_tables", app_token="app1", user_id=1)
    assert result.ok is True
    assert result.data["tables"][0]["table_id"] == "tbl1"


def test_bitable_create_record(monkeypatch):
    monkeypatch.setattr(bitable_mod, "get_valid_token", lambda db, uid: type("T", (), {"access_token": "tk"})())
    monkeypatch.setattr(
        bitable_mod.httpx, "post",
        lambda *a, **k: _fake_resp({"code": 0, "data": {"record": {"record_id": "rec1"}}}),
    )
    tool = get_tool("bitable")
    result = tool.execute(action="create_record", app_token="app1", table_id="tbl1", fields={"姓名": "张三"}, user_id=1)
    assert result.ok is True
    assert result.data["record_id"] == "rec1"


def test_bitable_api_error(monkeypatch):
    monkeypatch.setattr(bitable_mod, "get_valid_token", lambda db, uid: type("T", (), {"access_token": "tk"})())
    monkeypatch.setattr(
        bitable_mod.httpx, "get",
        lambda *a, **k: _fake_resp({"code": 99991663, "msg": "权限不足"}),
    )
    tool = get_tool("bitable")
    result = tool.execute(action="list_tables", app_token="app1", user_id=1)
    assert result.ok is False
    assert "失败" in result.message


def test_bitable_whitelist_and_validation():
    assert is_allowed("bitable", "list_records") is True
    assert is_allowed("bitable", "delete") is False
    ok, msg = validate_args("bitable", {"action": "create_record", "app_token": "a", "table_id": "t", "fields": {"x": 1}})
    assert ok is True
    ok2, msg2 = validate_args("bitable", {"action": "create_record", "app_token": "a", "table_id": "t", "fields": {}})
    assert ok2 is False


def test_selector_picks_bitable():
    sel = select_tools("读取多维表格里的记录")
    assert "bitable" in sel
