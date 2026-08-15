"""多轮执行循环：执行一批子任务 → 摘要回填 → 模型决定继续/终止。"""
import json
import re

from backend.llm.client import LLMClient
from backend.llm.messages import load_prompt
from backend.models.task import Task

MAX_STEPS = 3


def _val(item, key, default=""):
    """兼容 dict 与 pydantic 模型取值。"""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def build_summary(items_out: list) -> str:
    """把已执行子任务压缩成摘要文本（供模型判断是否继续）。"""
    lines = []
    for i, it in enumerate(items_out, 1):
        status = _val(it, "status")
        message = _val(it, "result")
        lines.append(f"{i}. {_val(it, 'action')} {_val(it, 'target')}（状态：{status}）{message}")
    return "\n".join(lines)


def should_continue(task: Task, summary_text: str, step: int, max_steps: int = MAX_STEPS) -> dict:
    """问模型是否还有后续步骤；无 LLM 或超轮数则终止。"""
    if step >= max_steps:
        return {"done": True, "tasks": []}
    client = LLMClient()
    if not client.available:
        return {"done": True, "tasks": []}
    system = load_prompt("continue.md")
    user = f"任务原文：{task.text}\n已执行摘要：\n{summary_text}\n当前轮次：{step}"
    try:
        content = client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
        )
        return _parse_continue(content)
    except Exception:
        return {"done": True, "tasks": []}


def _parse_continue(content: str) -> dict:
    match = re.search(r"\{.*\}", content, re.S)
    if not match:
        return {"done": True, "tasks": []}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"done": True, "tasks": []}
    raw_tasks = data.get("tasks") or []
    tasks = []
    for t in raw_tasks:
        args = t.get("args")
        tasks.append(
            {
                "action": str(t.get("action", "")),
                "target": str(t.get("target", "")),
                "params": str(t.get("params", "")),
                "high_risk": bool(t.get("high_risk", False)),
                "tool": str(t.get("tool", "")),
                "args": args if isinstance(args, dict) else {},
            }
        )
    done = bool(data.get("done", not tasks))
    return {"done": done, "tasks": tasks}