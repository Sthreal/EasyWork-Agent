"""测试：MCP 工具消费（executor 分支 / 按需注入 / 适配）。"""
import json

from backend.agent import executor
from backend.models.task import TaskItem
from backend.tools.base import ToolResult
from backend.tools.selector import select_tools


class FakeMcpTool:
    """模拟已注册的 MCP 工具实例。"""

    name = "mcp_get_weather"

    def __init__(self):
        self.calls = 0

    def execute(self, **kwargs):
        self.calls += 1
        return ToolResult(ok=True, message="多云 26°C", data={"text": "多云 26°C"})


def test_executor_runs_mcp_tool(monkeypatch):
    from backend.mcp import client as mcp_client

    fake = FakeMcpTool()
    monkeypatch.setattr(executor, "get_tool", lambda name: fake if name == fake.name else None)
    monkeypatch.setattr(mcp_client, "ensure_mcp_tools", lambda: True)
    monkeypatch.setattr(executor, "_audit_tool", lambda *a, **k: None)

    item = TaskItem(tool="mcp_get_weather", args=json.dumps({"city": "上海"}, ensure_ascii=False))
    result = executor._run(item)
    assert result["ok"] is True
    assert "多云" in result["message"]
    assert fake.calls == 1


def test_executor_mcp_tool_unavailable(monkeypatch):
    from backend.mcp import client as mcp_client

    monkeypatch.setattr(executor, "get_tool", lambda name: None)
    monkeypatch.setattr(mcp_client, "ensure_mcp_tools", lambda: True)
    monkeypatch.setattr(executor, "_audit_tool", lambda *a, **k: None)

    # 工具未注册时，MCP 分支内报「MCP 工具不可用」
    item = TaskItem(tool="mcp_get_weather", args="{}")
    result = executor._run(item)
    assert result["ok"] is False
    assert "MCP 工具不可用" in result["message"]


def test_selector_picks_weather_tool():
    sel = select_tools("查一下上海的天气")
    assert "mcp_get_weather" in sel
    sel2 = select_tools("明天会下雨吗")
    assert "mcp_get_weather" in sel2
