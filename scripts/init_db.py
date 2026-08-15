"""一次性脚本：建库。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.db import Base, engine  # noqa: E402
from backend.models import audit, confirmation, feishu_token, task, user  # noqa: E402, F401 注册模型


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成：users, feishu_tokens, tasks, task_items, confirmations")


if __name__ == "__main__":
    main()