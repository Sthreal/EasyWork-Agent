"""工具注册表。"""
from backend.tools.base import BaseTool

_REGISTRY: dict[str, type[BaseTool]] = {}


def register(cls: type[BaseTool]) -> type[BaseTool]:
    """注册工具类（装饰器用法：@register）。"""
    _REGISTRY[cls.name] = cls
    return cls


def get_tool(name: str) -> BaseTool | None:
    """按名称获取工具实例。"""
    cls = _REGISTRY.get(name)
    return cls() if cls else None


def available_tools() -> list[str]:
    """列出已注册的工具名。"""
    return sorted(_REGISTRY.keys())