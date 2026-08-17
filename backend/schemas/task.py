"""任务请求/响应结构。"""
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="任务描述")
    round: int = Field(1, ge=1, le=99, description="追问轮数")
    user_id: int | None = Field(None, description="用户ID")
    force: bool = Field(False, description="绕过 5 分钟去重（历史重发用）")


class TaskItem(BaseModel):
    action: str
    target: str = ""
    params: str = ""
    high_risk: bool = False
    tool: str = ""
    args: dict = {}
    status: str = "pending"
    result: str = ""
    confirmation_id: int | None = None
    in_workspace: bool | None = None
    preview: list | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    text: str
    tasks: list[TaskItem] = []
    question: str | None = None
    message: str | None = None


class TaskRecord(BaseModel):
    task_id: str
    text: str
    status: str
    question: str | None = None
    created_at: str | None = None
    tasks: list[TaskItem] = []


class TaskHistoryResponse(BaseModel):
    items: list[TaskRecord] = []
    total: int = 0