# 办公自动化 Agent

员工用自然语言提需求，Agent 拆解为子任务、按需调用工具执行；高危动作先经员工确认（写盘前可看 diff），执行后反馈结果。带可视化工作台、底部悬浮聊天与外部 MCP 工具消费。

## 功能亮点

**Agent 核心**
- 意图拆解 → 子任务编排 → 多轮执行循环（结果回填，MAX_STEPS 防死循环）
- 工具契约：BaseTool + Registry + JSON Schema 校验 + 操作白名单
- 工具按需注入（RequestSelector）：按意图只把相关工具 Schema 给模型，省 token、降低误选

**安全可控**
- 高危动作两段式确认：工作区内联确认（5 分钟）→ 待确认队列（30 分钟超时挂起）
- 写盘前结构化 diff 预览（表格 old → new，表头感知定位，杜绝改错列）
- JWT 登录 + 用户隔离 + 全链路审计（任务/工具/确认/登录/稍后）

**工作台 UI（Vue）**
- 顶部栏 + 头像个人中心（QQ 邮箱绑定 / 权限预留 / 历史）
- KPI + 图表（ECharts 按需引入）：今日任务 / 成功率 / 状态分布 / 近 7 天任务量
- 待确认板块（内联确认 + diff）、最近任务（搜索 / 筛选）
- 底部悬浮聊天：点击展开 / 点空白关闭（草稿保留）/ 拖拽调大小 / 历史持久化

**数据可视化**
- 表格聚合出图：`aggregate` 按表头分组统计 → 聊天卡片直接出柱状图

**外部能力（MCP 消费）**
- Agent 通过标准 MCP 协议发现并调用外部 MCP server 的工具，适配进自研 Registry、走同一套审计
- 演示源为本地 mock（`backend/mcp/mock_server.py`），生产接真实 MCP server 只改连接地址

**工程化**
- 141+ 自动化测试（20 黄金 Case / 3 类评分器 / Trace，见 `docs/自动化测试方案.md`）
- 切片开发：每片「接口 → 逻辑 → 工具 → 返回 → 测试」，可运行可回滚

## 技术选型

Vue 3 + FastAPI + SQLite（预留 PostgreSQL）+ ECharts + 飞书登录/日历 + QQ 邮箱 IMAP/SMTP + 本地 Excel/CSV + MCP（fastmcp）

## 目录说明

- `config/` 配置与提示词（改配置不动代码）
- `backend/` Python 后端（一个概念一个文件）
  - `agent/` 拆解 / 执行 / 多轮循环 / 任务状态
  - `tools/` 工具（email / sheets / calendar）+ 注册表 + 按需注入
  - `safety/` 高危确认闸门 / 白名单 / 审计
  - `mcp/` MCP 客户端与 mock server
  - `api/v1/` REST 接口
- `frontend/` Vue 前端（工作台 / 悬浮聊天 / 个人中心）
- `tests/` 测试（镜像 backend）
- `scripts/` 一次性脚本
- `docs/` 文档（PRD / MVP / 部署 / 自动化测试 / 面试讲解 / UI 原型 v1–v16）

## 快速开始

```bash
pip install -r requirements.txt
uvicorn backend.main:app --port 8001 --reload --reload-dir backend --reload-dir config   # 后端
pytest                              # 后端测试

cd frontend
npm install                          # 前端依赖（首次）
npm run dev                          # 前端，访问 http://localhost:5173
```

MCP 演示：后端启动后，在聊天框说「查一下上海的天气」——Agent 会通过 MCP 协议调用本地 mock server 的 `get_weather` 工具。

## 演示场景

1. **改表格（安全确认）**：把报名表里张三的电话更新为 138xxxx → 工作台/聊天卡片显示 diff（old → new）→ 确认执行
2. **统计出图（可视化）**：统计报名表各专业报名人数 → 聊天卡片直接出柱状图
3. **查天气（MCP 消费）**：查一下上海的天气 → Agent 调用外部 MCP server 工具

## 开发约定（每个切片）

每加一个功能，按「接口 → 逻辑 → 工具 → 返回 → 测试」顺序完成一个切片；
**每完成一个切片，项目必须可运行**（测试通过 + 服务可启动）。

**改动不影响其它功能**：改前跑全量测试确认基线；涉及共享模块列出调用方核对；改完立刻全量回归；尽量最小修改；每次改动独立提交可回滚。
