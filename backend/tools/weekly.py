"""周报工具：编排读日历/邮件/报名表 → LLM 汇总生成周报（多工具编排 demo）。

只生成文本；发送走 email.send（高危确认）。
"""
from backend.llm.client import LLMClient
from backend.llm.messages import load_prompt
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import register


@register
class WeeklyReportTool(BaseTool):
    """周报：读本周日历/邮件/报名表，汇总生成周报文本。"""

    name = "weekly_report"
    high_risk = False
    description = "周报：读取本周日历/最近邮件/报名表，汇总生成周报文本"
    args_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {"action": {"type": "string", "enum": ["generate"]}, "user_id": {"type": "integer"}},
    }

    def execute(self, action: str = "", **kwargs) -> ToolResult:
        if action != "generate":
            return ToolResult(ok=False, message=f"不支持的周报动作：{action}")
        return self.generate(user_id=int(kwargs.get("user_id") or 1))

    def generate(self, user_id: int = 1) -> ToolResult:
        sources = {
            "calendar": self._read_calendar(user_id),
            "mail": self._read_mail(user_id),
            "sheet": self._read_sheet(),
        }
        text = self._compose(sources, user_id)
        return ToolResult(
            ok=True,
            message="周报已生成",
            data={"text": text, "sources": {k: len(v) for k, v in sources.items()}},
        )

    def _read_calendar(self, user_id: int) -> list:
        try:
            from backend.tools.calendar import CalendarTool

            r = CalendarTool().execute(action="list", user_id=user_id, days=7)
            if r.ok:
                return r.data.get("events", [])
        except Exception:  # noqa: BLE001
            pass
        return []

    def _read_mail(self, user_id: int) -> list:
        try:
            from backend.tools.email import EmailTool

            r = EmailTool().execute(action="read", user_id=user_id, limit=10)
            if r.ok:
                return r.data.get("emails", [])
        except Exception:  # noqa: BLE001
            pass
        return []

    def _read_sheet(self) -> list:
        try:
            from backend.tools.sheets import SheetTool

            r = SheetTool().execute(action="read", filename="报名表.xlsx", limit=20)
            if r.ok:
                return r.data.get("rows", [])
        except Exception:  # noqa: BLE001
            pass
        return []

    def _compose(self, sources: dict, user_id: int) -> str:
        client = LLMClient()
        if not client.available:
            return self._fallback(sources)
        system = load_prompt("weekly.md")
        user = (
            f"本周日程：{sources['calendar']}\n"
            f"最近邮件：{sources['mail']}\n"
            f"报名表数据：{sources['sheet']}\n"
            "请生成本周工作周报（Markdown）。"
        )
        try:
            return client.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
            )
        except Exception:  # noqa: BLE001
            return self._fallback(sources)

    def _fallback(self, sources: dict) -> str:
        lines = ["# 本周周报（演示）", ""]
        lines.append(
            f"- 本周日程 {len(sources['calendar'])} 项；邮件 {len(sources['mail'])} 封；"
            f"报名表 {len(sources['sheet'])} 行"
        )
        return "\n".join(lines)
