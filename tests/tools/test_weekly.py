"""测试：周报生成工具（mock 数据源与 LLM）。"""
from backend.tools.base import ToolResult
from backend.tools.registry import get_tool
from backend.tools.selector import select_tools
from backend.safety.whitelist import is_allowed


def _stub_tool_result(ok=True, data=None, message="ok"):
    return ToolResult(ok=ok, message=message, data=data or {})


def test_weekly_fallback_without_llm(monkeypatch):
    from backend.tools import weekly as weekly_mod

    monkeypatch.setattr(weekly_mod.LLMClient, "available", False)
    monkeypatch.setattr(
        "backend.tools.calendar.CalendarTool",
        type("C", (), {"execute": lambda self, **k: _stub_tool_result(data={"events": [{"summary": "项目周会"}]})}),
    )
    monkeypatch.setattr(
        "backend.tools.email.EmailTool",
        type("E", (), {"execute": lambda self, **k: _stub_tool_result(data={"emails": [{"subject": "Q3 目标"}]})}),
    )
    monkeypatch.setattr(
        "backend.tools.sheets.SheetTool",
        type("S", (), {"execute": lambda self, **k: _stub_tool_result(data={"rows": [["姓名", "专业"], ["张三", "计算机"]]})}),
    )

    tool = get_tool("weekly_report")
    result = tool.execute(action="generate", user_id=1)
    assert result.ok is True
    assert "本周周报" in result.data["text"]
    assert result.data["sources"] == {"calendar": 1, "mail": 1, "sheet": 2}


def test_weekly_with_llm(monkeypatch):
    from backend.tools import weekly as weekly_mod

    monkeypatch.setattr(weekly_mod.LLMClient, "available", True)
    monkeypatch.setattr(weekly_mod.LLMClient, "chat", lambda self, messages, **k: "# 周报\n- 会议 1 项")
    monkeypatch.setattr(
        "backend.tools.calendar.CalendarTool",
        type("C", (), {"execute": lambda self, **k: _stub_tool_result(data={"events": []})}),
    )
    monkeypatch.setattr("backend.tools.email.EmailTool", type("E", (), {"execute": lambda self, **k: _stub_tool_result(data={"emails": []})}))
    monkeypatch.setattr("backend.tools.sheets.SheetTool", type("S", (), {"execute": lambda self, **k: _stub_tool_result(data={"rows": []})}))

    tool = get_tool("weekly_report")
    result = tool.execute(action="generate", user_id=1)
    assert result.ok is True
    assert "# 周报" in result.data["text"]


def test_weekly_sources_tolerate_failure(monkeypatch):
    from backend.tools import weekly as weekly_mod

    monkeypatch.setattr(weekly_mod.LLMClient, "available", False)
    monkeypatch.setattr(
        "backend.tools.calendar.CalendarTool",
        type("C", (), {"execute": lambda self, **k: _stub_tool_result(ok=False, message="token 过期")}),
    )
    monkeypatch.setattr("backend.tools.email.EmailTool", type("E", (), {"execute": lambda self, **k: (_ for _ in ()).throw(Exception("no"))}))
    monkeypatch.setattr("backend.tools.sheets.SheetTool", type("S", (), {"execute": lambda self, **k: _stub_tool_result(data={"rows": [["a"]]})}))

    tool = get_tool("weekly_report")
    result = tool.execute(action="generate", user_id=1)
    assert result.ok is True  # 数据源失败不崩，降级生成
    assert result.data["sources"]["calendar"] == 0


def test_weekly_whitelist_and_selector():
    assert is_allowed("weekly_report", "generate") is True
    assert is_allowed("weekly_report", "delete") is False
    sel = select_tools("帮我生成这周的周报")
    assert "weekly_report" in sel


def test_calendar_list_allowed():
    assert is_allowed("calendar", "list") is True
