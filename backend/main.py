"""应用入口：注册路由、启动服务。"""

import logging

import time

import traceback

from contextlib import asynccontextmanager



from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse



from backend.api.v1 import audit, auth, chat, confirmation, task, user

import backend.tools  # noqa: F401 注册工具

from config.logging import setup_logging

from config.settings import settings



logger = logging.getLogger(__name__)



setup_logging()



@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时执行轻量幂等迁移（补齐新增列，不破坏现有数据）。"""
    from backend.db import Base, engine
    from backend.db_migrate import ensure_confirmations_preview

    Base.metadata.create_all(bind=engine)  # 建缺失表（含 chat_messages），幂等
    ensure_confirmations_preview(engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)



app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_methods=["*"],

    allow_headers=["*"],

)



app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

app.include_router(task.router, prefix="/api/v1", tags=["task"])

app.include_router(confirmation.router, prefix="/api/v1", tags=["confirmation"])

app.include_router(user.router, prefix="/api/v1", tags=["user"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])





@app.middleware("http")

async def access_log(request: Request, call_next):

    """记录每个请求：方法 / 路径 / 状态码 / 耗时。"""

    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(

        "%s %s -> %s (%.1fms)",

        request.method,

        request.url.path,

        response.status_code,

        duration_ms,

    )

    return response





@app.exception_handler(Exception)

async def unhandled_exception_handler(request: Request, exc: Exception):

    """未预期异常：记录完整堆栈到日志，返回友好 500，不让服务崩。"""

    logger.error(

        "未捕获异常 %s %s: %s\n%s",

        request.method,

        request.url.path,

        exc,

        traceback.format_exc(),

    )

    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，详情见 logs/app.log"})





@app.get("/health")

def health():

    """健康检查。"""

    return {"status": "ok"}