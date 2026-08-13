"""测试：敏感操作白名单。"""
from backend.agent import executor
from backend.models.task import TaskItem
from backend.safety.whitelist import is_allowed


def test_allowed_operations():
    assert is_allowed("email", "send") is True
    assert is_allowed("email", "read") is True
    assert is_allowed("sheets", "write") is True
    assert is_allowed("calendar", "create") is True


def test_denied_operations():
    assert is_allowed("email", "delete") is False
    assert is_allowed("sheets", "drop") is False
    assert is_allowed("calendar", "destroy") is False
    assert is_allowed("shell", "exec") is False


def test_executor_rejects_not_in_whitelist(monkeypatch):
    monkeypatch.setattr(executor, "get_tool", lambda name: object())
    item = TaskItem(tool="email", args='{"action": "delete", "to": "a@b.com"}')
    result = executor._run(item)
    assert result["ok"] is False
    assert "白名单" in result["message"]

def test_sheets_write_by_key_allowed():
    assert is_allowed("sheets", "write_by_key") is True
