"""多维表格工具（飞书 Bitable API：列出表格/读取记录/新建记录/更新记录）。"""
import httpx

from backend.db import SessionLocal
from backend.feishu.client import FEISHU_OPEN_BASE, _unwrap
from backend.feishu.token_store import get_valid_token
from backend.tools.base import BaseTool, ToolResult
from backend.tools.registry import register


@register
class BitableTool(BaseTool):
    """飞书多维表格工具：读/写指定多维表格的记录。"""

    name = "bitable"
    high_risk = False
    description = "飞书多维表格：列出表格/读取记录/新建记录/更新记录（写记录高危）"
    args_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {"action": {"type": "string", "enum": ["list_tables", "list_records", "create_record", "update_record"]}},
        "oneOf": [
            {"properties": {"action": {"const": "list_tables"}, "app_token": {"type": "string"}, "user_id": {"type": "integer"}}, "required": ["action", "app_token"]},
            {"properties": {"action": {"const": "list_records"}, "app_token": {"type": "string"}, "table_id": {"type": "string"}, "user_id": {"type": "integer"}}, "required": ["action", "app_token", "table_id"]},
            {"properties": {"action": {"const": "create_record"}, "app_token": {"type": "string"}, "table_id": {"type": "string"}, "fields": {"type": "object"}, "user_id": {"type": "integer"}}, "required": ["action", "app_token", "table_id", "fields"]},
            {"properties": {"action": {"const": "update_record"}, "app_token": {"type": "string"}, "table_id": {"type": "string"}, "record_id": {"type": "string"}, "fields": {"type": "object"}, "user_id": {"type": "integer"}}, "required": ["action", "app_token", "table_id", "record_id", "fields"]},
        ],
    }

    def execute(self, action: str = "", **kwargs) -> ToolResult:
        user_id = int(kwargs.get("user_id") or 1)
        try:
            if action == "list_tables":
                return self.list_tables(app_token=kwargs.get("app_token", ""), user_id=user_id)
            if action == "list_records":
                return self.list_records(app_token=kwargs.get("app_token", ""), table_id=kwargs.get("table_id", ""), user_id=user_id)
            if action == "create_record":
                return self.create_record(app_token=kwargs.get("app_token", ""), table_id=kwargs.get("table_id", ""), fields=kwargs.get("fields", {}), user_id=user_id)
            if action == "update_record":
                return self.update_record(app_token=kwargs.get("app_token", ""), table_id=kwargs.get("table_id", ""), record_id=kwargs.get("record_id", ""), fields=kwargs.get("fields", {}), user_id=user_id)
            return ToolResult(ok=False, message=f"不支持的多维表格动作：{action}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(ok=False, message=f"多维表格操作失败：{exc}")

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _token(self, user_id: int) -> str:
        return get_valid_token(SessionLocal(), user_id).access_token

    def list_tables(self, app_token: str, user_id: int = 1) -> ToolResult:
        resp = httpx.get(
            f"{FEISHU_OPEN_BASE}/bitable/v1/apps/{app_token}/tables",
            headers=self._headers(self._token(user_id)),
            timeout=15,
        )
        data = _unwrap(resp, "列出多维表格")
        items = [{"table_id": t["table_id"], "name": t.get("name", "")} for t in data["data"].get("items", [])]
        return ToolResult(ok=True, message=f"共 {len(items)} 个表格", data={"tables": items})

    def list_records(self, app_token: str, table_id: str, user_id: int = 1) -> ToolResult:
        resp = httpx.get(
            f"{FEISHU_OPEN_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            headers=self._headers(self._token(user_id)),
            timeout=15,
        )
        data = _unwrap(resp, "读取多维表格记录")
        items = [{"record_id": r["record_id"], "fields": r.get("fields", {})} for r in data["data"].get("items", [])]
        return ToolResult(ok=True, message=f"读取 {len(items)} 条记录", data={"records": items})

    def create_record(self, app_token: str, table_id: str, fields: dict, user_id: int = 1) -> ToolResult:
        resp = httpx.post(
            f"{FEISHU_OPEN_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            headers=self._headers(self._token(user_id)),
            json={"fields": fields},
            timeout=15,
        )
        data = _unwrap(resp, "新建多维表格记录")
        return ToolResult(ok=True, message="记录已创建", data={"record_id": data["data"]["record"]["record_id"]})

    def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict, user_id: int = 1) -> ToolResult:
        resp = httpx.put(
            f"{FEISHU_OPEN_BASE}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            headers=self._headers(self._token(user_id)),
            json={"fields": fields},
            timeout=15,
        )
        _unwrap(resp, "更新多维表格记录")
        return ToolResult(ok=True, message="记录已更新", data={"record_id": record_id})
