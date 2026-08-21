"""测试：对抗测试执行器（注入 fake create 验证判定与汇总）。"""
from backend.adversarial import runner
from backend.adversarial.cases import CASES
from backend.schemas.task import TaskResponse, TaskItem as TaskItemSchema


def _resp(status: str, tasks=None, question=None) -> TaskResponse:
    return TaskResponse(task_id="1", status=status, text="t", tasks=tasks or [], question=question)


def test_injection_not_executed():
    # 攻击被拦截：危险动作未执行，任务停在 pending_confirm/failed/need_clarify
    fake = lambda payload, db: _resp("pending_confirm", tasks=[
        TaskItemSchema(action="删除文件", target="报名表.xlsx", high_risk=True, tool="sheets", status="pending_confirm"),
    ])
    r = runner.run_case(CASES[0], create=fake)
    assert r["verdict"]["pass"] is True


def test_injection_executed_fails():
    # 危险动作被直接执行（不应发生）→ 判定不通过
    fake = lambda payload, db: _resp("executed", tasks=[
        TaskItemSchema(action="删除文件", target="报名表.xlsx", high_risk=True, tool="sheets", status="executed"),
    ])
    r = runner.run_case(CASES[0], create=fake)
    assert r["verdict"]["pass"] is False


def test_high_risk_expects_confirm():
    fake = lambda payload, db: _resp("pending_confirm", tasks=[
        TaskItemSchema(action="更新电话", target="报名表", high_risk=True, tool="sheets", status="pending_confirm"),
    ])
    r = runner.run_case(next(c for c in CASES if c["category"] == "high_risk"), create=fake)
    assert r["verdict"]["pass"] is True


def test_ambiguous_expects_clarify():
    fake = lambda payload, db: _resp("need_clarify", question="你想处理什么？")
    r = runner.run_case(next(c for c in CASES if c["category"] == "ambiguous"), create=fake)
    assert r["verdict"]["pass"] is True


def test_long_input_no_crash():
    fake = lambda payload, db: _resp("need_clarify")
    r = runner.run_case(next(c for c in CASES if c["category"] == "long_input"), create=fake)
    assert r["verdict"]["pass"] is True


def test_suite_summary():
    def fake(payload, db):
        cat = None
        for c in CASES:
            if payload.text == c["text"]:
                cat = c["category"]
        if cat == "ambiguous":
            return _resp("need_clarify")
        if cat == "high_risk":
            return _resp("pending_confirm")
        if cat == "long_input":
            return _resp("need_clarify")
        return _resp("failed")  # injection / bad_args 被拦截为 failed
    report = runner.run_suite(create=fake)
    assert report["total"] == len(CASES)
    assert report["passed"] == report["total"]
    assert "injection" in report["by_category"]

def test_contradiction_danger_executed_fails():
    # 矛盾指令里危险部分被直接执行 → 应判 FAIL
    fake = lambda payload, db: _resp("executed", tasks=[
        TaskItemSchema(action="删除文件", target="报名表.xlsx", high_risk=True, tool="sheets", status="executed"),
    ])
    r = runner.run_case(next(c for c in CASES if c["category"] == "contradiction"), create=fake)
    assert r["verdict"]["pass"] is False


def test_privacy_danger_executed_fails():
    fake = lambda payload, db: _resp("executed", tasks=[
        TaskItemSchema(action="转发邮件", target="123@qq.com", high_risk=True, tool="email", status="executed"),
    ])
    r = runner.run_case(next(c for c in CASES if c["category"] == "privacy"), create=fake)
    assert r["verdict"]["pass"] is False