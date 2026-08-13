"""表格工具（本地 Excel/CSV：读/写/预览）。"""
import csv
from pathlib import Path

from config.settings import settings
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import register

DATA_DIR = Path(settings.sheets_data_dir)


@register
class SheetTool(BaseTool):
    """本地表格工具：只允许操作 DATA_DIR 内文件。"""

    name = "sheets"
    high_risk = False  # 写操作由高危关键词判定（更新/写入=高危）

    def execute(self, action: str = "", **kwargs) -> ToolResult:
        try:
            if action == "read":
                return self.read(filename=kwargs.get("filename", ""), limit=int(kwargs.get("limit", 10)))
            if action == "preview":
                return self.preview(filename=kwargs.get("filename", ""), changes=kwargs.get("changes", []))
            if action == "write":
                return self.write(filename=kwargs.get("filename", ""), changes=kwargs.get("changes", []))
            return ToolResult(ok=False, message=f"不支持的表格动作：{action}")
        except ValueError as exc:
            return ToolResult(ok=False, message=str(exc))

    def _resolve(self, filename: str) -> Path:
        if not filename:
            raise ValueError("缺少文件名")
        base = DATA_DIR.resolve()
        path = (base / filename).resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"路径越权：只允许操作 {base} 内文件")
        return path

    def read(self, filename: str, limit: int = 10) -> ToolResult:
        path = self._resolve(filename)
        if not path.exists():
            return ToolResult(ok=False, message=f"文件不存在：{filename}")
        rows = _read_rows(path, limit)
        return ToolResult(ok=True, message=f"读取 {len(rows)} 行", data={"file": filename, "rows": rows})

    def preview(self, filename: str, changes: list) -> ToolResult:
        path = self._resolve(filename)
        if not path.exists():
            return ToolResult(ok=False, message=f"文件不存在：{filename}")
        rows = _read_rows(path, 200)
        preview = []
        for c in changes:
            old = _cell_value(rows, c.get("row"), c.get("column"))
            preview.append(
                {
                    "row": c.get("row"),
                    "column": c.get("column"),
                    "old": old,
                    "new": c.get("value", ""),
                }
            )
        return ToolResult(ok=True, message=f"生成 {len(preview)} 处变更预览", data={"preview": preview})

    def write(self, filename: str, changes: list) -> ToolResult:
        path = self._resolve(filename)
        if not path.exists():
            return ToolResult(ok=False, message=f"文件不存在：{filename}")
        count = _apply_changes(path, changes)
        return ToolResult(ok=True, message=f"已更新 {count} 个单元格", data={"file": filename})


def _read_rows(path: Path, limit: int) -> list:
    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as f:
            return [row for row in csv.reader(f)][:limit]
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    return [[ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)] for r in range(1, ws.max_row + 1)][:limit]


def _cell_value(rows: list, row, column) -> str:
    try:
        idx = _col_index(column) - 1
        value = rows[row - 1][idx]
        return "" if value is None else str(value)
    except (IndexError, TypeError):
        return ""


def _apply_changes(path: Path, changes: list) -> int:
    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        for c in changes:
            row, col, value = int(c["row"]), _col_index(c["column"]), str(c.get("value", ""))
            while len(rows) < row:
                rows.append([])
            while len(rows[row - 1]) < col:
                rows[row - 1].append("")
            rows[row - 1][col - 1] = value
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
        return len(changes)

    import openpyxl

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    for c in changes:
        ws.cell(row=int(c["row"]), column=_col_index(c["column"]), value=str(c.get("value", "")))
    wb.save(path)
    return len(changes)


def _col_index(column) -> int:
    if isinstance(column, int):
        return column
    col = str(column).upper()
    result = 0
    for ch in col:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result