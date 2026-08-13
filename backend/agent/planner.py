"""意图拆解 → 子任务列表。"""
import json
import re

from backend.llm.client import LLMClient
from backend.llm.messages import build_planner_messages
from config.settings import settings


def plan(user_text: str) -> list[dict]:
    """把一句话任务拆成子任务列表；未配置大模型时返回假数据。"""
    client = LLMClient()
    if not client.available:
        return _fake_plan(user_text)
    content = client.chat(build_planner_messages(user_text))
    return _parse_tasks(content)


def _parse_tasks(content: str) -> list[dict]:
    match = re.search(r"\{.*\}", content, re.S)
    if not match:
        raise ValueError("拆解结果不是 JSON")
    data = json.loads(match.group(0))
    tasks = data.get("tasks", [])
    return [
        {
            "action": str(t.get("action", "")),
            "target": str(t.get("target", "")),
            "params": str(t.get("params", "")),
            "high_risk": bool(t.get("high_risk", False)),
        }
        for t in tasks
    ]


def _fake_plan(user_text: str) -> list[dict]:
    """未配置大模型时的兜底：整句作为一条待执行任务。"""
    return [{"action": "执行", "target": user_text, "params": "", "high_risk": False}]