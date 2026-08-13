"""邮件工具（QQ邮箱 IMAP/SMTP：读/发）。"""
import imaplib
import smtplib
from email.header import decode_header
from email.message import EmailMessage
from email.utils import formataddr

from config.settings import settings
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import register

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
IMAP_HOST = "imap.qq.com"
IMAP_PORT = 993


@register
class EmailTool(BaseTool):
    """QQ 邮箱工具：发送邮件（高危）/ 读取收件箱。"""

    name = "email"
    high_risk = False

    def execute(self, action: str = "", **kwargs) -> ToolResult:
        if action == "send":
            return self.send(
                subject=kwargs.get("subject", ""),
                to=kwargs.get("to", ""),
                body=kwargs.get("body", ""),
            )
        if action == "read":
            return self.read(limit=int(kwargs.get("limit", 10)))
        return ToolResult(ok=False, message=f"不支持的邮件动作：{action}")

    def send(self, subject: str, to: str, body: str) -> ToolResult:
        if not settings.qq_mail_address or not settings.qq_mail_auth_code:
            return ToolResult(ok=False, message="QQ 邮箱未配置（QQ_MAIL_ADDRESS / QQ_MAIL_AUTH_CODE）")
        if not to or not subject:
            return ToolResult(ok=False, message="收件人和主题不能为空")
        msg = EmailMessage()
        msg["From"] = formataddr(("办公自动化 Agent", settings.qq_mail_address))
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.login(settings.qq_mail_address, settings.qq_mail_auth_code)
                server.send_message(msg)
            return ToolResult(ok=True, message=f"邮件已发送至 {to}")
        except Exception as exc:
            return ToolResult(ok=False, message=f"发送失败：{exc}")

    def read(self, limit: int = 10) -> ToolResult:
        if not settings.qq_mail_address or not settings.qq_mail_auth_code:
            return ToolResult(ok=False, message="QQ 邮箱未配置")
        try:
            with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=15) as conn:
                conn.login(settings.qq_mail_address, settings.qq_mail_auth_code)
                conn.select("INBOX")
                _, data = conn.search(None, "ALL")
                ids = data[0].split()
                recent = ids[-limit:][::-1]
                items = []
                for mid in recent:
                    _, msg_data = conn.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
                    items.append(_parse_header(msg_data[0][1]))
                return ToolResult(ok=True, message=f"读取到 {len(items)} 封邮件", data={"emails": items})
        except Exception as exc:
            return ToolResult(ok=False, message=f"读取失败：{exc}")


def _parse_header(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="replace")
    result = {"from": "", "subject": "", "date": ""}
    for line in text.splitlines():
        if line.lower().startswith("from:"):
            result["from"] = _decode(line[5:].strip())
        elif line.lower().startswith("subject:"):
            result["subject"] = _decode(line[8:].strip())
        elif line.lower().startswith("date:"):
            result["date"] = line[5:].strip()
    return result


def _decode(value: str) -> str:
    try:
        parts = decode_header(value)
        return "".join(
            part.decode(charset or "utf-8", errors="replace") if isinstance(part, bytes) else part
            for part, charset in parts
        )
    except Exception:
        return value