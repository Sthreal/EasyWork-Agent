"""本地 MCP mock server（演示用）：通过真实 MCP stdio 协议暴露「天气查询」工具。

生产环境可换成任意公开/自建 MCP server，只需改 McpClient 的连接命令/地址。
"""
from fastmcp import FastMCP

mcp = FastMCP("office-agent-mock")


@mcp.tool()
def get_weather(city: str) -> str:
    """查询指定城市当前天气（演示数据源）。"""
    data = {
        "上海": "多云 26°C 东南风3级",
        "北京": "晴 24°C 西北风2级",
        "广州": "雷阵雨 29°C 南风4级",
        "深圳": "小雨 28°C 东风3级",
    }
    return data.get(city, f"暂无 {city} 的天气数据（演示用）")


if __name__ == "__main__":
    mcp.run()
