"""任务接口（发起/查询/结果）。"""

import json



from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session



from backend.agent.executor import execute_item, save_item

from backend.agent.planner import plan

from backend.db import get_db

from backend.models.confirmation import Confirmation

from backend.models.task import Task, TaskItem

from backend.safety.gate import create_confirmation

from backend.schemas.task import (

    TaskCreate,

    TaskHistoryResponse,

    TaskItem as TaskItemSchema,

    TaskRecord,

    TaskResponse,

)



router = APIRouter(prefix="/tasks")





@router.post("", response_model=TaskResponse)

def create_task(payload: TaskCreate, db: Session = Depends(get_db)):

    """接收任务 → 意图拆解 → 落库 → 低危直接执行/高危建确认。"""

    result = plan(payload.text)

    status = "need_clarify" if result["question"] else "planned"



    task = Task(

        user_id=None,

        text=payload.text,

        status=status,

        question=result["question"],

    )

    db.add(task)

    db.flush()



    items_out = []

    for item in result["tasks"]:

        row = save_item(db, task.id, item)

        db.flush()

        if item.get("high_risk") and item.get("tool"):

            conf = create_confirmation(

                db,

                task_id=task.id,

                task_item_id=row.id,

                action=item["action"],

                target=item["target"],

                params=item["params"],

            )

            row.status = "pending_confirm"

            row.result = json.dumps({"ok": False, "message": "等待确认"}, ensure_ascii=False)

            items_out.append(_item_schema(row, conf.id if conf else None))

        else:

            exec_result = execute_item(row.id)

            if exec_result:

                row.status = "executed" if exec_result["ok"] else "failed"

                row.result = json.dumps(exec_result, ensure_ascii=False)


            items_out.append(_item_schema(row, None, exec_result))



    db.commit()



    return TaskResponse(

        task_id=str(task.id),

        status=task.status,

        text=task.text,

        tasks=items_out,

        question=result["question"],

    )





@router.get("", response_model=TaskHistoryResponse)

def list_tasks(db: Session = Depends(get_db)):

    """查询最近 50 条任务历史。"""

    tasks = db.query(Task).order_by(Task.id.desc()).limit(50).all()

    return TaskHistoryResponse(

        items=[

            TaskRecord(

                task_id=str(t.id),

                text=t.text,

                status=t.status,

                question=t.question,

                created_at=t.created_at.isoformat() if t.created_at else None,

                tasks=[_item_schema(i, _confirmation_id(db, i.id)) for i in t.items],

            )

            for t in tasks

        ]

    )





def _confirmation_id(db: Session, item_id: int) -> int | None:

    conf = (

        db.query(Confirmation)

        .filter(Confirmation.task_item_id == item_id, Confirmation.status == "pending")

        .first()

    )

    return conf.id if conf else None





def _item_schema(row: TaskItem, confirmation_id: int | None = None, exec_result: dict | None = None) -> TaskItemSchema:

    try:

        args = json.loads(row.args or "{}")

    except json.JSONDecodeError:

        args = {}

    return TaskItemSchema(

        action=row.action,

        target=row.target,

        params=row.params,

        high_risk=row.high_risk,

        tool=row.tool,

        args=args,

        status=row.status,

        result=row.result,

        confirmation_id=confirmation_id,

    )