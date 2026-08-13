"""测试：执行编排。"""
import json

import pytest

from backend.agent import executor
from backend.models.task import TaskItem


class FakeTool:
    name = "fake"

    def execute(self, **kwargs):
        from backend.tools.base import ToolResult
        return ToolResult(ok=True, message="done", data=kwargs)


def test_run_with_missing_args(monkeypatch):
    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool())
    item = TaskItem(tool="email", args=json.dumps({"action": "send", "to": ""}))
    result = executor._run(item)
    assert result["ok"] is False
    assert "参数不足" in result["message"]


def test_run_unknown_tool(monkeypatch):
    monkeypatch.setattr(executor, "get_tool", lambda name: None)
    item = TaskItem(tool="ghost", args="{}")
    result = executor._run(item)
    assert result["ok"] is False
    assert "无法识别工具" in result["message"]


def test_run_success(monkeypatch):
    monkeypatch.setattr(executor, "get_tool", lambda name: FakeTool())
    item = TaskItem(tool="fake", args=json.dumps({"action": "go"}))
    result = executor._run(item)
    assert result["ok"] is True
    assert result["message"] == "done"


def test_calendar_normalize():
    item = TaskItem(tool="calendar", args=json.dumps({"action": "create", "summary": "开会", "start_ts": "2026-08-14T15:00", "end_ts": "2026-08-14T16:00"}))
    args = json.loads(item.args)
    executor._normalize("calendar", args)
    assert isinstance(args["start_ts"], int)