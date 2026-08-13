"""应用入口：注册路由、启动服务。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import auth, confirmation, task
from config.settings import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(task.router, prefix="/api/v1", tags=["task"])
app.include_router(confirmation.router, prefix="/api/v1", tags=["confirmation"])


@app.get("/health")
def health():
    """健康检查。"""
    return {"status": "ok"}