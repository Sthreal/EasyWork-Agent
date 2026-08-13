"""测试：工具注册表。"""
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import available_tools, get_tool, register


@register
class DummyTool(BaseTool):
    name = "dummy"
    high_risk = True

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(ok=True, message="done")


def test_register_and_get():
    tool = get_tool("dummy")
    assert tool is not None
    assert tool.name == "dummy"
    assert tool.high_risk is True
    result = tool.execute()
    assert result.ok is True
    assert result.message == "done"


def test_get_unknown_returns_none():
    assert get_tool("not_exist") is None


def test_available_tools_contains_dummy():
    assert "dummy" in available_tools()