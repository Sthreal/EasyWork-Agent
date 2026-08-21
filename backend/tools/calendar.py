"""日历工具（飞书日历 API：建/改自己的日程）。"""


import httpx





from backend.db import SessionLocal


from backend.feishu.client import FEISHU_OPEN_BASE, _unwrap


from backend.feishu.token_store import get_valid_token


from backend.tools.base import BaseTool, ToolResult


from backend.tools.registry import register





TIMEZONE = "Asia/Shanghai"








@register


class CalendarTool(BaseTool):


    """飞书日历工具：只操作自己的日程。"""





    name = "calendar"


    high_risk = False
    description = '飞书日历：创建/修改自己的日程'
    args_schema = {
        "type": "object",
        "required": ["action"],
        "properties": {"action": {"type": "string", "enum": ["create", "update", "list"]}},
        "oneOf": [
            {"properties": {"action": {"const": "create"}, "summary": {"type": "string"}, "start_ts": {"type": "string"}, "end_ts": {"type": "string"}, "description": {"type": "string"}, "user_id": {"type": "integer"}}, "required": ["action", "summary", "start_ts", "end_ts"]},
            {"properties": {"action": {"const": "update"}, "event_id": {"type": "string"}, "summary": {"type": "string"}, "user_id": {"type": "integer"}}, "required": ["action", "event_id", "summary"]},
            {"properties": {"action": {"const": "list"}, "days": {"type": "integer"}, "user_id": {"type": "integer"}}, "required": ["action"]},
        ],
    }  # 更新/修改/删除由高危关键词判定





    def execute(self, action: str = "", **kwargs) -> ToolResult:


        if action == "list":
            return self.list(user_id=int(kwargs.get("user_id") or 1), days=int(kwargs.get("days") or 7))
        if action == "create":


            return self.create(


                summary=kwargs.get("summary", ""),


                start_ts=kwargs.get("start_ts"),


                end_ts=kwargs.get("end_ts"),


                description=kwargs.get("description", ""),


                user_id=kwargs.get("user_id", 1),


            )


        if action == "update":


            return self.update(


                event_id=kwargs.get("event_id", ""),


                summary=kwargs.get("summary", ""),


                user_id=kwargs.get("user_id", 1),


            )


        return ToolResult(ok=False, message=f"不支持的日历动作：{action}")





    def list(self, user_id: int = 1, days: int = 7) -> ToolResult:
        """读取未来 N 天的日程（周报/汇总用，只读不高危）。"""
        from datetime import datetime, timedelta

        start = int(datetime.now().timestamp())
        end = int((datetime.now() + timedelta(days=days)).timestamp())
        try:
            resp = httpx.get(
                f"{FEISHU_OPEN_BASE}/calendar/v4/calendars/primary/events",
                params={"start_time": str(start), "end_time": str(end)},
                headers=self._headers(self._access_token(user_id)),
                timeout=15,
                trust_env=False,
            )
            data = _unwrap(resp, "读取日历事件")
            items = [
                {
                    "summary": e.get("summary", ""),
                    "start": e.get("start_time", {}).get("timestamp", ""),
                    "end": e.get("end_time", {}).get("timestamp", ""),
                }
                for e in data["data"].get("items", [])
            ]
            return ToolResult(ok=True, message=f"读取 {len(items)} 个日程", data={"events": items})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(ok=False, message=f"读取日历失败：{exc}")

    def _access_token(self, user_id: int) -> str:


        db = SessionLocal()


        try:


            return get_valid_token(db, user_id).access_token


        finally:


            db.close()





    def create(self, summary: str, start_ts, end_ts, description: str = "", user_id: int = 1) -> ToolResult:


        if not summary or not start_ts or not end_ts:


            return ToolResult(ok=False, message="缺少日程主题或时间")


        body = {


            "summary": summary,


            "description": description,


            "start_time": {"timestamp": str(int(start_ts)), "timezone": TIMEZONE},


            "end_time": {"timestamp": str(int(end_ts)), "timezone": TIMEZONE},


        }


        try:


            resp = httpx.post(


                f"{FEISHU_OPEN_BASE}/calendar/v4/calendars/primary/events",


                headers=self._headers(self._access_token(user_id)),


                json=body,


                timeout=15,
                trust_env=False,


            )


            data = _unwrap(resp, "创建日程")


            event = data["data"]["event"]


            return ToolResult(ok=True, message=f"日程已创建：{summary}", data={"event_id": event["event_id"]})


        except Exception as exc:  # noqa: BLE001


            return ToolResult(ok=False, message=f"创建日程失败：{exc}")





    def update(self, event_id: str, summary: str, user_id: int = 1) -> ToolResult:


        if not event_id or not summary:


            return ToolResult(ok=False, message="缺少日程 ID 或主题")


        try:


            resp = httpx.patch(


                f"{FEISHU_OPEN_BASE}/calendar/v4/calendars/primary/events/{event_id}",


                headers=self._headers(self._access_token(user_id)),


                json={"summary": summary},


                timeout=15,
                trust_env=False,


            )


            _unwrap(resp, "更新日程")


            return ToolResult(ok=True, message=f"日程已更新：{summary}", data={"event_id": event_id})


        except Exception as exc:  # noqa: BLE001


            return ToolResult(ok=False, message=f"更新日程失败：{exc}")





    @staticmethod


    def _headers(token: str) -> dict:


        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}