# 办公自动化 Agent

员工用自然语言提需求，Agent 拆解为子任务、按需调用工具执行，高危动作先经员工确认，执行后反馈结果。

## 技术选型
Vue + FastAPI + SQLite（预留 PostgreSQL）+ 飞书日历 API + QQ 邮箱 IMAP/SMTP + 本地 Excel/CSV + 飞书登录

## 目录说明
- `config/` 配置与提示词（改配置不动代码）
- `backend/` Python 后端（一个概念一个文件）
- `frontend/` Vue 前端
- `tests/` 测试（镜像 backend）
- `scripts/` 一次性脚本
- `docs/` 文档（PRD / MVP / 技术选型 / 骨架）

## 快速开始

```bash
pip install -r requirements.txt
uvicorn backend.main:app --port 8001 --reload --reload-dir backend --reload-dir config   # 启动后端（只监听代码目录，避免测试写日志触发重启）
pytest                              # 跑后端测试

cd frontend
npm install                          # 安装前端依赖（首次）
npm run dev                          # 启动前端，访问 http://localhost:5173
```

## 开发约定（每个切片）

每加一个功能，按「接口 → 逻辑 → 工具 → 返回 → 测试」顺序完成一个切片；
**每完成一个切片，项目必须可运行**（测试通过 + 服务可启动）。


## 开发约定补充：改动不影响其它功能

改一个功能时，不得影响其它功能。要求：
1. 改动前先跑全量测试确认基线
2. 涉及共享模块时，列出所有调用方并核对
3. 改完立刻回归：全量测试 + 相关功能冒烟
4. 尽量最小修改，不整文件重写；重写必须核对 props/依赖
5. 每次改动独立提交，出问题可回滚