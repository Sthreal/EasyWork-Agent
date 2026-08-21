#!/usr/bin/env python3
"""对抗测试 CLI：跑全套用例调主 Agent，输出分类报告。

用法: python scripts/run_adversarial.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.adversarial.runner import run_suite  # noqa: E402
from backend.db import SessionLocal  # noqa: E402


def main() -> int:
    db = SessionLocal()
    try:
        report = run_suite(db=db)
    finally:
        db.close()

    print("=" * 60)
    print(f"对抗测试报告：{report['passed']}/{report['total']} 通过")
    for cat, info in report["by_category"].items():
        print(f"  [{cat}] {info['passed']}/{info['total']}")
        for item in info["items"]:
            mark = "[PASS]" if item["verdict"]["pass"] else "[FAIL]"
            print(f"    {mark} {item['name']} — {item['verdict']['reason']}")
    print("=" * 60)
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
