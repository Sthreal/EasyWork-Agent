"""请求上下文组装。"""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "config" / "prompts"


def load_prompt(name: str) -> str:
    """读取 config/prompts 下的提示词文件。"""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def build_planner_messages(user_text: str) -> list[dict]:
    """组装意图拆解的对话上下文。"""
    return [
        {"role": "system", "content": load_prompt("planner.md")},
        {"role": "user", "content": user_text},
    ]