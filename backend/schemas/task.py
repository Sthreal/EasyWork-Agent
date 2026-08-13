"""任务请求/响应结构。"""
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="任务描述")


class TaskItem(BaseModel):
    action: str
    target: str = ""
    params: str = ""
    high_risk: bool = False


class TaskResponse(BaseModel):
    task_id: str
    status: str
    text: str
    tasks: list[TaskItem] = []
    question: str | None = None