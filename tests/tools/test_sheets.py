"""测试：表格工具。"""
import csv

import pytest

from backend.tools import sheets as sheets_tool


@pytest.fixture()
def tmp_sheets(tmp_path, monkeypatch):
    monkeypatch.setattr(sheets_tool, "DATA_DIR", tmp_path)
    xlsx = tmp_path / "报名表.xlsx"
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["姓名", "电话"])
    ws.append(["张三", "13800000000"])
    ws.append(["李四", "13900000000"])
    wb.save(xlsx)

    csv_path = tmp_path / "名单.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([["姓名"], ["张三"]])
    return tmp_path


def test_read_xlsx(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="read", filename="报名表.xlsx")
    assert result.ok is True
    assert result.data["rows"][0] == ["姓名", "电话"]
    assert result.data["rows"][1][0] == "张三"


def test_read_csv(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="read", filename="名单.csv")
    assert result.ok is True
    assert result.data["rows"][0] == ["姓名"]


def test_preview_does_not_change_file(tmp_sheets):
    xlsx = tmp_sheets / "报名表.xlsx"
    before = xlsx.read_bytes()
    tool = sheets_tool.SheetTool()
    result = tool.execute(
        action="preview",
        filename="报名表.xlsx",
        changes=[{"row": 2, "column": "B", "value": "13811112222"}],
    )
    assert result.ok is True
    assert result.data["preview"][0]["old"] == "13800000000"
    assert result.data["preview"][0]["new"] == "13811112222"
    assert xlsx.read_bytes() == before  # 预览不改文件


def test_write_updates_cell(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(
        action="write",
        filename="报名表.xlsx",
        changes=[{"row": 2, "column": "B", "value": "13811112222"}],
    )
    assert result.ok is True
    check = tool.execute(action="read", filename="报名表.xlsx")
    assert check.data["rows"][1][1] == "13811112222"


def test_path_traversal_rejected(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="read", filename="../../secret.txt")
    assert result.ok is False
    assert "越权" in result.message


def test_missing_file(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="read", filename="不存在.xlsx")
    assert result.ok is False
    assert "不存在" in result.message


def test_unsupported_action():
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="fly")
    assert result.ok is False

def test_find_cell_by_header(tmp_sheets):
    tool = sheets_tool.SheetTool()
    target = tool.find_cell("报名表.xlsx", "姓名", "张三", "电话")
    assert target["row"] == 2
    assert target["column"] == "B"
    assert target["old"] == "13800000000"


def test_write_by_key(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(
        action="write_by_key",
        filename="报名表.xlsx",
        key_column="姓名",
        key_value="张三",
        field="电话",
        value="13899999999",
    )
    assert result.ok is True
    check = tool.execute(action="read", filename="报名表.xlsx")
    assert check.data["rows"][1][1] == "13899999999"


def test_find_cell_missing_header(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="write_by_key", filename="报名表.xlsx", key_column="姓名", key_value="张三", field="邮箱", value="x@y.com")
    assert result.ok is False
    assert "找不到表头" in result.message



def test_aggregate_count_by_column(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="aggregate", filename="报名表.xlsx", group_by="姓名", agg="count")
    assert result.ok is True
    chart = result.data["chart"]
    assert chart["chart_type"] == "bar"
    assert chart["y_label"] == "人数"
    assert len(chart["data"]) == 2
    assert any(d["label"] == "张三" and d["value"] == 1 for d in chart["data"])


def test_aggregate_sum_by_column(tmp_sheets):
    import csv

    p = tmp_sheets / "订单.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows([["部门", "金额"], ["A", "100"], ["A", "50"], ["B", "30"]])
    tool = sheets_tool.SheetTool()
    result = tool.execute(
        action="aggregate", filename="订单.csv", group_by="部门", agg="sum", value_column="金额"
    )
    assert result.ok is True
    chart = result.data["chart"]
    assert chart["y_label"] == "金额 合计"
    by = {d["label"]: d["value"] for d in chart["data"]}
    assert by["A"] == 150
    assert by["B"] == 30


def test_aggregate_missing_group_column(tmp_sheets):
    tool = sheets_tool.SheetTool()
    result = tool.execute(action="aggregate", filename="报名表.xlsx", group_by="不存在", agg="count")
    assert result.ok is False
    assert "找不到表头" in result.message
