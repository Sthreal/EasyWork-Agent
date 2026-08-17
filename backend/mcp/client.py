"""MCP 客户端：连接外部 MCP server，发现工具并适配成自研 BaseTool。

每次调用起一次 stdio 会话（演示规模足够）；生产可改为常驻连接。
"""
import asyncio
import os
import sys


def _ensure_pywin32() -> None:
    """mcp 在 Windows 依赖 pywintypes（pywin32）：按 pywin32.pth 补齐相关目录到 sys.path。"""
    if os.name != "nt":
        return
    sp = os.path.join(sys.prefix, "Lib", "site-packages")
    if not os.path.isdir(sp):
        return
    for rel in ("win32", os.path.join("win32", "lib"), "pythonwin", "pywin32_system32"):
        p = os.path.join(sp, rel)
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)
    try:
        import pywin32_bootstrap  # noqa: F401  注册 pywin32 DLL 搜索路径
    except Exception:
        pass


_ensure_pywin32()

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import register_instance


class McpClient:
    """管理到外部 MCP server 的连接（stdio）。"""

    def __init__(self, command: str, args: list[str]):
        self._command = command
        self._args = args

    def _params(self) -> StdioServerParameters:
        return StdioServerParameters(command=self._command, args=self._args)

    def discover(self) -> list[dict]:
        """发现外部 server 暴露的工具（name/description/inputSchema）。"""
        async def _run() -> list[dict]:
            async with stdio_client(self._params()) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    return [
                        {
                            "name": t.name,
                            "description": t.description or "",
                            "schema": t.inputSchema or {"type": "object", "properties": {}},
                        }
                        for t in tools.tools
                    ]

        return asyncio.run(_run())

    def call(self, target: str, arguments: dict) -> ToolResult:
        """同步调用外部 MCP 工具（内部用 asyncio.run 桥接 async 会话）。"""
        async def _run() -> ToolResult:
            async with stdio_client(self._params()) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(target, arguments or {})
                    text = "".join(
                        c.text for c in result.content if getattr(c, "type", None) == "text"
                    )
                    return ToolResult(
                        ok=not getattr(result, "isError", False),
                        message=text or "ok",
                        data={"text": text},
                    )

        return asyncio.run(_run())


class McpTool(BaseTool):
    """把外部 MCP 工具包装成自研 BaseTool 实例，接入现有执行/审计链路。"""

    def __init__(self, name: str, description: str, args_schema: dict, client: McpClient, target: str):
        self.name = name
        self.description = description
        self.args_schema = args_schema
        self.high_risk = False  # 演示数据源默认只读低危
        self._client = client
        self._target = target

    def execute(self, **kwargs) -> ToolResult:
        return self._client.call(self._target, kwargs)


def register_mcp_tools(client: McpClient, prefix: str = "mcp_") -> list[str]:
    """发现外部 MCP 工具并以 mcp_ 前缀注册进 Registry。返回注册的工具名。"""
    names = []
    for t in client.discover():
        name = prefix + t["name"]
        register_instance(McpTool(name, t["description"], t["schema"], client, t["name"]))
        names.append(name)
    return names


_MCP_READY = False


def ensure_mcp_tools() -> bool:
    """惰性注册 MCP 工具（首次调用时发现一次，之后缓存）。失败返回 False 不阻塞。"""
    global _MCP_READY
    if _MCP_READY:
        return True
    try:
        client = McpClient("python", ["-m", "backend.mcp.mock_server"])
        names = register_mcp_tools(client)
        _MCP_READY = True
        return bool(names)
    except Exception:
        return False
