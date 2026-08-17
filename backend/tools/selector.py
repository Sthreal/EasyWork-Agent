"""按需注入工具选择器（RequestSelector）：按意图只返回相关工具，省 token、降低误选。"""
from backend.tools.registry import available_tools

# 每类工具的强信号关键词（宁缺毋滥：命中少、误伤低；无命中回退全部工具）
_TOOL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "email": ("邮件", "发信", "发邮件", "收件", "邮箱", "抄送", "附件", "mail", "email"),
    "sheets": ("表格", "报名表", "名单", "excel", "csv", "单元格", "表头", "工作表", "统计", "分布", "人数", "合计", "汇总", "图表", "占比"),
    "calendar": ("会议", "日程", "日历", "预约", "参会", "空闲", "calendar"),
    "mcp_get_weather": ("天气", "气温", "下雨", "预报", "温度", "weather"),
}


def select_tools(user_text: str) -> list[str]:
    """按关键词命中返回工具子集；无命中回退全部工具（宁多勿漏，保证不破坏）。"""
    text = user_text.lower()
    matched = [name for name, kws in _TOOL_KEYWORDS.items() if any(k.lower() in text for k in kws)]
    if matched:
        return matched
    return available_tools()
