# 办公自动化 Agent MVP 开发任务清单（M1/M2/M3）

> 来源：MVP 定义（默认 T+8 周：M1 ~2周 / M2 ~3周 / M3 ~3周）。
> 每个任务尽量只动一个概念文件（遵循骨架「一个概念一个文件」）。
> 风险均为推测。

---

## 0. 并行前置（第一周启动，非编码任务，别等开发完）

| # | 事项 | 说明 |
|---|------|------|
| P1 | 飞书自建应用 + 权限审批 | 申请：`calendar:calendar:readonly`、`calendar:calendar`、用户信息；管理员审批可能慢 |
| P2 | QQ 邮箱授权码 | 内测员工开启 IMAP/SMTP，生成授权码（≠登录密码） |
| P3 | Excel 文件清单 | 确定允许 Agent 读写的文件、格式（xlsx/csv）、路径 |
| P4 | 内测名单 | ≤50 人 |
| P5 | 仓库初始化 | git init + 环境安装 |

---

## M1 基础（第 1-2 周）：登录 + 输入 + 拆解 + 反问

| # | 任务 | 涉及文件 | 验收标准 |
|---|------|---------|----------|
| M1-1 | 后端工程初始化 | `backend/main.py`、`backend/db.py`、`config/settings.py`、`requirements.txt` | 服务可启动；配置从 .env 读取 |
| M1-2 | 用户表 + 建库脚本 ✅ | `backend/models/user.py`、`scripts/init_db.py` | 建表成功，可存用户 |
| M1-3 | 飞书登录/OAuth ✅ | `backend/feishu/auth.py`、`backend/api/v1/auth.py`、`backend/schemas/auth.py`、`frontend/src/pages/LoginPage.vue` | 飞书授权后能登录，回调正常 |
| M1-4 | 授权令牌存取与刷新 | `backend/feishu/token_store.py`、`backend/models/feishu_token.py` | token 落库，过期可刷新 |
| M1-5 | 对话页基础 | `frontend/src/pages/ChatPage.vue`、`frontend/src/components/TaskInput.vue`、`frontend/src/api/task.ts` | 能输入并提交任务文本 |
| M1-6 | 大模型封装 | `backend/llm/client.py`、`backend/llm/messages.py` | 统一调模型，错误可处理 |
| M1-7 | 意图拆解 | `backend/agent/planner.py`、`config/prompts/planner.md` | 一句话 → 结构化子任务列表 |
| M1-8 | 反问澄清 | `backend/agent/clarify.py`、`config/prompts/clarify.md` | 信息不足时反问，补齐后再拆解 |
| M1-9 | 任务落库与查询 | `backend/models/task.py`、`backend/api/v1/task.py`、`backend/schemas/task.py` | 任务/子任务可保存、可查 |

**M1 完成标志**：登录 → 输入 → （反问）→ 子任务列表落库，全链路通。

---

## M2 工具接入（第 3-5 周）：工具 + 高危确认 + 反馈

| # | 任务 | 涉及文件 | 验收标准 |
|---|------|---------|----------|
| M2-1 | 工具框架 | `backend/tools/base.py`、`backend/tools/registry.py` | 新工具按统一接口注册即可用 |
| M2-2 | 邮件工具 | `backend/tools/email.py` | QQ 邮箱读信/发信成功（真实账号） |
| M2-3 | 日历工具 | `backend/tools/calendar.py` | 飞书建/改日程成功（员工本人身份） |
| M2-4 | 表格工具 | `backend/tools/sheets.py` | 本地 Excel 读/写/变更预览成功 |
| M2-5 | 高危判定 | `backend/safety/high_risk.py` | 删除/覆盖/发送/外发四类能识别 |
| M2-6 | 确认闸门 | `backend/safety/gate.py`、`backend/api/v1/confirmation.py`、`backend/models/confirmation.py`、`backend/schemas/confirmation.py` | 高危拦截→确认→放行；超时挂起 |
| M2-7 | 确认页/弹窗 | `frontend/src/pages/ConfirmationPage.vue`、`frontend/src/components/ConfirmModal.vue`、`frontend/src/api/confirmation.ts` | 能看到待确认动作并点按钮 |
| M2-8 | 执行编排 | `backend/agent/executor.py` | 子任务按顺序执行，高危走闸门 |
| M2-9 | 结果反馈 | `backend/agent/feedback.py`、`config/prompts/feedback.md`、`frontend/src/components/ResultCard.vue` | 汇总成功/失败，失败有原因 |

**M2 完成标志**：三个工具真实可用；高危必须确认；执行后有汇总反馈。

---

## M3 闭环打磨（第 6-8 周）：日志 + 联调 + 内测

| # | 任务 | 涉及文件 | 验收标准 |
|---|------|---------|----------|
| M3-1 | 操作日志 | `backend/safety/audit.py`、`backend/models/audit_log.py` | 每次操作记录谁/何时/做了什么 |
| M3-2 | 三场景端到端联调 | 全链路 | 发邮件、建日程、改表格三个场景走通 |
| M3-3 | 异常处理 | 各工具 + `backend/agent/executor.py` | token 过期、邮箱失败、Excel 不存在等给出明确报错 |
| M3-4 | 测试补齐 | `tests/agent`、`tests/safety`、`tests/tools` | 核心逻辑有自动化测试 |
| M3-5 | 内测（≤50人） | — | 内测用户跑通三场景，收集反馈并修复 |
| M3-6 | 部署与文档 | `README.md`、`scripts/` | 内网部署完成，启动步骤可照做 |

**M3 完成标志**：MVP 验收标准 6 条全部满足（见《MVP 定义》第 5 节）。

---

## 风险与注意（推测）

| 事项 | 注意 |
|------|------|
| 飞书权限审批慢 | 前置 P1 第一周提交 |
| 建日程分两步（先建日程，再加参与人） | M2-3 按飞书官方文档实现 |
| QQ 邮箱授权码易泄露 | 只存 .env，不进仓库 |
| Excel 多人同时写冲突 | 写前预览 + 内测小范围可接受 |
| token 过期/员工离职 | 明确报错 + 引导重新授权 |
---

## 开发约定（每个切片）

每加一个功能，按「**接口 → 逻辑 → 工具 → 返回 → 测试**」顺序完成一个切片：
1. **接口**：先定义 API（路由 + 数据结构）
2. **逻辑**：实现业务逻辑（agent / safety 等）
3. **工具**：接入或调用工具（邮件/日历/表格/LLM）
4. **返回**：统一响应与反馈
5. **测试**：为该切片补测试

**验收**：每完成一个切片，项目必须可运行（`pytest` 通过 + 服务可启动）。
