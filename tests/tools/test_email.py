"""测试：邮件工具（mock 网络）。"""
import pytest

from backend.tools import email as email_tool
from backend.tools.base import ToolResult
from backend.tools.registry import get_tool


class FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.logged_in = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login(self, user, pwd):
        self.logged_in = True

    def send_message(self, msg):
        self.sent = msg


def test_send_without_config_returns_error(monkeypatch):
    monkeypatch.setattr(email_tool.settings, "qq_mail_address", "")
    monkeypatch.setattr(email_tool.settings, "qq_mail_auth_code", "")
    tool = email_tool.EmailTool()
    result = tool.execute(action="send", subject="测试", to="a@b.com", body="内容")
    assert result.ok is False
    assert "未配置" in result.message


def test_send_success(monkeypatch):
    monkeypatch.setattr(email_tool.settings, "qq_mail_address", "me@qq.com")
    monkeypatch.setattr(email_tool.settings, "qq_mail_auth_code", "code")
    monkeypatch.setattr(email_tool.smtplib, "SMTP_SSL", FakeSMTP)
    tool = email_tool.EmailTool()
    result = tool.send(subject="主题", to="you@qq.com", body="正文")
    assert result.ok is True
    assert "you@qq.com" in result.message


def test_unsupported_action():
    tool = email_tool.EmailTool()
    result = tool.execute(action="fly")
    assert result.ok is False


def test_email_registered():
    tool = get_tool("email")
    assert tool is not None
    assert isinstance(tool, email_tool.EmailTool)