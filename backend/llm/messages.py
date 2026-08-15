"""请求上下文组装。"""
import json
from pathlib import Path

from backend.tools.registry import available_tools, get_tool

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "config" / "prompts"


def load_prompt(name: str) -> str:
    """读取 config/prompts 下的提示词文件。"""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def _tools_schema_text() -> str:
    """把已注册工具的参数 Schema 拼进提示词，引导模型按 schema 生成 args。"""
    lines = ["", "## 工具参数 Schema（严格按此生成 args）"]
    for name in available_tools():
        tool = get_tool(name)
        if tool is None:
            continue
        lines.append(f"- {name}（{tool.description}）：")
        lines.append(json.dumps(tool.args_schema, ensure_ascii=False))
    return "\n".join(lines)


def build_planner_messages(user_text: str) -> list[dict]:
    """组装意图拆解的对话上下文（含工具 Schema）。"""
    system = load_prompt("planner.md") + _tools_schema_text()
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]