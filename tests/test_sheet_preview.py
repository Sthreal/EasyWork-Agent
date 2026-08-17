"""测试：表格高危动作的结构化 diff 预览（切片A后端）。"""
from backend.services.task_service import _sheets_preview
from backend.tools.base import ToolResult


def test_preview_write_by_key(monkeypatch):
    from backend.tools import sheets as sheets_mod

    monkeypatch.setattr(
        sheets_mod.SheetTool,
        "find_cell",
        lambda self, **kw: {"row": 2, "column": "B", "old": "138"},
    )
    monkeypatch.setattr(
        sheets_mod.SheetTool,
        "execute",
        lambda self, **kw: ToolResult(
            ok=True,
            message="生成 1 处变更预览",
            data={"preview": [{"row": 2, "column": "B", "old": "138", "new": "139"}]},
        ),
    )
    item = {
        "tool": "sheets",
        "action": "write_by_key",
        "params": "补充说明",
        "args": {
            "action": "write_by_key",
            "filename": "报名表.xlsx",
            "key_column": "姓名",
            "key_value": "张三",
            "field": "电话",
            "value": "139",
        },
    }
    text, diffs, err = _sheets_preview(item)
    assert err is None
    assert "报名表.xlsx" in text
    assert "138 → 139" in text
    assert diffs == [{"row": 2, "column": "B", "old": "138", "new": "139"}]


def test_preview_write(monkeypatch):
    from backend.tools import sheets as sheets_mod

    monkeypatch.setattr(
        sheets_mod.SheetTool,
        "execute",
        lambda self, **kw: ToolResult(
            ok=True,
            message="生成 2 处变更预览",
            data={
                "preview": [
                    {"row": 2, "column": "B", "old": "138", "new": "139"},
                    {"row": 3, "column": "C", "old": "北京", "new": "上海"},
                ]
            },
        ),
    )
    item = {
        "tool": "sheets",
        "action": "write",
        "params": "",
        "args": {
            "action": "write",
            "filename": "名单.csv",
            "changes": [{"row": 2, "column": "B", "value": "139"}],
        },
    }
    text, diffs, err = _sheets_preview(item)
    assert err is None
    assert len(diffs) == 2
    assert "第2行B列" in text
    assert "第3行C列" in text


def test_preview_non_sheets_passthrough():
    item = {"tool": "email", "action": "send", "params": "收件人：a@b.com", "args": {}}
    text, diffs, err = _sheets_preview(item)
    assert (text, diffs, err) == ("收件人：a@b.com", None, None)


def test_preview_error(monkeypatch):
    from backend.tools import sheets as sheets_mod

    def boom(self, **kw):
        raise ValueError("找不到表头：电话")

    monkeypatch.setattr(sheets_mod.SheetTool, "find_cell", boom)
    item = {
        "tool": "sheets",
        "action": "write_by_key",
        "params": "",
        "args": {"action": "write_by_key", "filename": "报名表.xlsx", "field": "电话"},
    }
    text, diffs, err = _sheets_preview(item)
    assert text == ""
    assert diffs is None
    assert "找不到表头" in err
