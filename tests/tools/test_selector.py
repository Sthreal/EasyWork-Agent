"""测试：按需注入工具选择器（切片C）。"""
from backend.tools.selector import select_tools


def test_email_keywords():
    assert "email" in select_tools("给项目组发邮件")
    assert "email" in select_tools("读取收件箱")


def test_sheets_keywords():
    sel = select_tools("读取报名表内容")
    assert "sheets" in sel
    assert "email" not in sel


def test_calendar_keywords():
    sel = select_tools("帮我约明天下午和HR的会议")
    assert "calendar" in sel
    assert "sheets" not in sel


def test_multi_tool_text():
    sel = select_tools("发邮件说明会议改到3点")
    assert "email" in sel and "calendar" in sel


def test_unknown_text_falls_back_to_all():
    sel = select_tools("随便做点什么")
    assert "email" in sel and "sheets" in sel and "calendar" in sel
