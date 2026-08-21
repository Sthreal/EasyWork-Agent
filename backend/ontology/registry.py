"""本体注册表：把业务对象建模成「字段 + 操作」，供 Agent 按对象理解需求。

本层是读模型——只描述与路由，逻辑仍在工具层；对象操作映射到现有工具动作。
"""
from dataclasses import dataclass, field

from backend.tools.registry import available_tools


@dataclass
class Operation:
    """对象上的一个可执行操作，映射到工具动作。"""

    name: str
    description: str
    high_risk: bool = False
    tool: str = ""
    action: str = ""


@dataclass
class ObjectType:
    """业务对象类型：名称/描述/字段/操作/数据源。"""

    name: str
    description: str
    fields: list[str] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    source: str = ""

    def tools(self) -> set[str]:
        return {op.tool for op in self.operations if op.tool}

    def to_prompt(self) -> str:
        lines = [f"- {self.name}（工具 {'/'.join(sorted(self.tools()))}）：{self.description}"]
        if self.fields:
            lines.append(f"    字段：{'、'.join(self.fields)}（以实际表头为准）")
        for op in self.operations:
            risk = "（高危，需确认）" if op.high_risk else ""
            lines.append(f"    操作：{op.name} - {op.description}{risk}")
        return "\n".join(lines)


_REGISTRY: dict[str, ObjectType] = {}


def register_object(obj: ObjectType) -> ObjectType:
    _REGISTRY[obj.name] = obj
    return obj


def get_object(name: str) -> ObjectType | None:
    return _REGISTRY.get(name)


def available_objects() -> list[str]:
    return sorted(_REGISTRY.keys())


def objects_prompt(tools: list[str] | None = None) -> str:
    """生成「可用业务对象」提示段；tools 非空时只列出与这些工具相关的对象。"""
    allowed = set(tools or available_tools())
    lines = ["", "## 可用业务对象（按对象理解需求；生成 args 时用括号里的工具与操作）"]
    for name in available_objects():
        obj = _REGISTRY[name]
        if tools is not None and not (obj.tools() & allowed):
            continue
        lines.append(obj.to_prompt())
    return "\n".join(lines)


# ===== 内置对象（报名表/邮件/日历；多维表格在 bitable 工具就绪后补）=====
register_object(
    ObjectType(
        name="报名表",
        description="本地 Excel/CSV 表格，支持按表头定位读写与分组统计",
        fields=["姓名", "电话", "专业", "备注"],
        source="本地 Excel/CSV",
        operations=[
            Operation("read", "读取表格内容", tool="sheets", action="read"),
            Operation("write_by_key", "按表头定位修改某个单元格（高危，需确认）", high_risk=True, tool="sheets", action="write_by_key"),
            Operation("aggregate", "按某列表头分组统计（count/sum）并出图", tool="sheets", action="aggregate"),
        ],
    )
)
register_object(
    ObjectType(
        name="邮件",
        description="QQ 邮箱：发送/读取邮件",
        source="QQ 邮箱 IMAP/SMTP",
        operations=[
            Operation("send", "发送邮件（高危，需确认）", high_risk=True, tool="email", action="send"),
            Operation("read", "读取邮件", tool="email", action="read"),
        ],
    )
)
register_object(
    ObjectType(
        name="日历",
        description="飞书日历：创建/修改日程",
        source="飞书日历 API",
        operations=[
            Operation("create", "创建日程", tool="calendar", action="create"),
            Operation("update", "修改日程", tool="calendar", action="update"),
        ],
    )
)
