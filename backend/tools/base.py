"""工具统一接口 + 是否高危声明。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """工具执行结果。"""

    ok: bool
    message: str = ""
    data: dict = field(default_factory=dict)


class BaseTool(ABC):
    """所有工具必须实现 execute；high_risk=True 表示执行前需员工确认。"""

    name: str = "base"
    high_risk: bool = False

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具动作。"""