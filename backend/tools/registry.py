"""工具注册表。"""
from backend.tools.base import BaseTool

_REGISTRY: dict[str, type[BaseTool]] = {}
_INSTANCES: dict[str, BaseTool] = {}


def register(cls: type[BaseTool]) -> type[BaseTool]:
    """注册工具类（装饰器用法：@register）。"""
    _REGISTRY[cls.name] = cls
    return cls


def register_instance(tool: BaseTool) -> None:
    """注册工具实例（用于 MCP 等动态发现的工具）。"""
    _INSTANCES[tool.name] = tool


def get_tool(name: str) -> BaseTool | None:
    """按名称获取工具实例（优先实例，其次类实例化）。"""
    if name in _INSTANCES:
        return _INSTANCES[name]
    cls = _REGISTRY.get(name)
    return cls() if cls else None


def available_tools() -> list[str]:
    """列出已注册的工具名（含动态实例）。"""
    return sorted(set(_REGISTRY.keys()) | set(_INSTANCES.keys()))