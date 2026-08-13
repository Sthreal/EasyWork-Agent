"""测试：意图拆解。"""
import json

import pytest

from backend.agent import planner


def test_fake_mode_when_not_configured(monkeypatch):
    monkeypatch.setattr(planner.settings, "llm_api_key", "")
    result = planner.plan("给项目组发邮件")
    assert isinstance(result["tasks"], list)
    assert len(result["tasks"]) >= 1
    assert result["question"] is None


def test_plan_parses_json(monkeypatch):
    monkeypatch.setattr(planner.settings, "llm_api_key", "sk-test")
    monkeypatch.setattr(planner.settings, "llm_base_url", "https://example.com/v1")
    monkeypatch.setattr(planner.settings, "llm_model", "test-model")
    monkeypatch.setattr(
        planner.LLMClient,
        "chat",
        lambda self, messages, **kwargs: json.dumps(
            {
                "tasks": [
                    {"action": "写邮件", "target": "项目组", "params": "明天会议改到3点", "high_risk": False},
                    {"action": "发送邮件", "target": "项目组", "params": "", "high_risk": True},
                ]
            },
            ensure_ascii=False,
        ),
    )
    result = planner.plan("给项目组发邮件，说明明天会议改到3点")
    assert len(result["tasks"]) == 2
    assert result["tasks"][0]["action"] == "写邮件"
    assert result["tasks"][1]["high_risk"] is True
    assert result["question"] is None


def test_plan_asks_clarification(monkeypatch):
    monkeypatch.setattr(planner.settings, "llm_api_key", "sk-test")
    monkeypatch.setattr(planner.settings, "llm_base_url", "https://example.com/v1")
    monkeypatch.setattr(planner.settings, "llm_model", "test-model")
    monkeypatch.setattr(
        planner.LLMClient,
        "chat",
        lambda self, messages, **kwargs: json.dumps(
            {"tasks": [], "question": "你想处理什么？"}, ensure_ascii=False
        ),
    )
    result = planner.plan("帮我处理一下")
    assert result["tasks"] == []
    assert result["question"] == "你想处理什么？"


def test_plan_invalid_json_raises(monkeypatch):
    monkeypatch.setattr(planner.settings, "llm_api_key", "sk-test")
    monkeypatch.setattr(planner.settings, "llm_base_url", "https://example.com/v1")
    monkeypatch.setattr(planner.settings, "llm_model", "test-model")
    monkeypatch.setattr(planner.LLMClient, "chat", lambda self, messages, **kwargs: "不是JSON")
    with pytest.raises(ValueError):
        planner.plan("随便说点什么")