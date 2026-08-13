"""测试：日历工具（mock 飞书接口）。"""
import pytest

from backend.tools import calendar as calendar_tool
from backend.tools.registry import get_tool


class FakeToken:
    access_token = "token123"


def _fake_resp(payload, status=200):
    class FakeResp:
        status_code = status
        text = str(payload)

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return payload

    return FakeResp()


def test_create_success(monkeypatch):
    monkeypatch.setattr(calendar_tool, "get_valid_token", lambda db, user_id: FakeToken())

    def fake_post(url, headers=None, json=None, timeout=None):
        assert "/calendar/v4/calendars/primary/events" in url
        assert json["summary"] == "测试日程"
        assert json["start_time"]["timezone"] == "Asia/Shanghai"
        return _fake_resp({"code": 0, "event": {"event_id": "evt_123", "summary": "测试日程"}})

    monkeypatch.setattr(calendar_tool.httpx, "post", fake_post)
    tool = calendar_tool.CalendarTool()
    result = tool.execute(action="create", summary="测试日程", start_ts=1780000000, end_ts=1780003600)
    assert result.ok is True
    assert result.data["event_id"] == "evt_123"


def test_create_missing_params():
    tool = calendar_tool.CalendarTool()
    result = tool.execute(action="create", summary="", start_ts=1780000000, end_ts=1780003600)
    assert result.ok is False
    assert "缺少" in result.message


def test_update_success(monkeypatch):
    monkeypatch.setattr(calendar_tool, "get_valid_token", lambda db, user_id: FakeToken())

    def fake_patch(url, headers=None, json=None, timeout=None):
        assert "evt_123" in url
        assert json["summary"] == "新主题"
        return _fake_resp({"code": 0, "event": {"event_id": "evt_123", "summary": "新主题"}})

    monkeypatch.setattr(calendar_tool.httpx, "patch", fake_patch)
    tool = calendar_tool.CalendarTool()
    result = tool.execute(action="update", event_id="evt_123", summary="新主题")
    assert result.ok is True


def test_unsupported_action():
    tool = calendar_tool.CalendarTool()
    result = tool.execute(action="fly")
    assert result.ok is False


def test_calendar_registered():
    tool = get_tool("calendar")
    assert tool is not None
    assert isinstance(tool, calendar_tool.CalendarTool)