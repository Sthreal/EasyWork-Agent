"""测试：本体层（Ontology）——对象注册/查询/按工具过滤注入。"""
from backend.llm.messages import build_planner_messages
from backend.ontology.registry import (
    available_objects,
    get_object,
    objects_prompt,
    register_object,
)
from backend.ontology.registry import ObjectType, Operation


def test_registry_has_builtin_objects():
    names = available_objects()
    assert "报名表" in names and "邮件" in names and "日历" in names
    obj = get_object("报名表")
    assert obj is not None
    assert "write_by_key" in [op.name for op in obj.operations]
    assert "sheets" in obj.tools()


def test_register_and_get():
    register_object(
        ObjectType(
            name="测试对象",
            description="测试用",
            fields=["a"],
            operations=[Operation("do", "执行", tool="sheets", action="read")],
        )
    )
    assert get_object("测试对象") is not None


def test_objects_prompt_filters_by_tools():
    prompt = objects_prompt(tools=["sheets"])
    assert "报名表" in prompt
    assert "邮件" not in prompt
    assert "日历" not in prompt


def test_objects_prompt_all_when_no_filter():
    prompt = objects_prompt()
    assert "报名表" in prompt and "邮件" in prompt and "日历" in prompt


def test_planner_messages_include_object_desc():
    content = build_planner_messages("读取报名表内容")[0]["content"]
    obj_part = content.split("可用业务对象", 1)[1]
    assert "报名表" in obj_part
    assert "邮件" not in obj_part  # 按需：对象段只注入相关对象
