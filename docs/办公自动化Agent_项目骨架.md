# 办公自动化 Agent 项目骨架（MVP，仅规划，未创建）

> 默认技术栈：Python + FastAPI / Vue / SQLite 起步 / 境内大模型 API。
> 工具接入已定：日历=飞书 API、邮件=QQ邮箱 IMAP/SMTP、表格=本地 Excel/CSV、登录=飞书。
> 核心原则：**一个概念一个文件**。文件名 = 概念名；看到路径和文件名，就知道这个文件只负责什么。
> 原则：**目录即约定**——每个目录只放一类东西，不需要读业务代码。

---

## 1. 目录总览

```
office-agent/
├── README.md               # 项目说明、启动步骤、目录说明
├── .env.example            # 环境变量样例（真实密钥不进仓库）
├── .gitignore
├── requirements.txt        # Python 依赖
├── config/                 # 配置与提示词（改配置不动代码）
├── backend/                # 后端（Python）
├── frontend/               # 前端（Vue）
├── tests/                  # 测试（镜像 backend 结构）
├── scripts/                # 一次性脚本（建库、初始化工具账号）
└── docs/                   # PRD、MVP 定义、本骨架说明
```

## 2. 后端 backend/（一个概念一个文件）

```
backend/
├── main.py                 # 概念：应用入口。只做启动和路由注册
├── db.py                   # 概念：数据库连接。唯一连接入口
├── api/
│   └── v1/                 # 概念：HTTP 接口层。一个资源 = 一个文件
│       ├── auth.py             # 登录接口（含飞书OAuth回调）
│       ├── task.py             # 任务接口（发起/查询/结果）
│       └── confirmation.py     # 高危确认接口（确认/挂起列表）
├── schemas/                # 概念：数据结构。与接口一一对应
│   ├── auth.py                 # 登录请求/响应结构
│   ├── task.py                 # 任务请求/响应结构
│   └── confirmation.py         # 确认请求/响应结构
├── agent/                  # 概念：Agent 编排。一个环节 = 一个文件
│   ├── planner.py              # 意图拆解 → 子任务列表
│   ├── clarify.py              # 反问澄清
│   ├── executor.py             # 子任务执行编排（调工具/过确认闸门）
│   └── feedback.py             # 结果汇总与反馈生成
├── tools/                  # 概念：工具层。一个工具 = 一个文件
│   ├── base.py                 # 工具统一接口 + 是否高危声明
│   ├── registry.py             # 工具注册表
│   ├── email.py                # 邮件工具（QQ邮箱 IMAP/SMTP：读/发）
│   ├── calendar.py             # 日历工具（飞书日历 API：建/改日程）
│   └── sheets.py               # 表格工具（本地 Excel/CSV：读/写/预览）
├── feishu/                 # 概念：飞书集成。一个职责 = 一个文件
│   ├── client.py               # 飞书 API 客户端（统一封装调用）
│   ├── auth.py                 # 飞书登录/授权（OAuth 流程）
│   └── token_store.py          # 授权令牌存取与刷新
├── safety/                 # 概念：安全与确认。一个机制 = 一个文件
│   ├── high_risk.py            # 高危判定（删除/覆盖/发送/外发）
│   ├── gate.py                 # 确认闸门（待确认/超时挂起/放行/拒绝）
│   └── audit.py                # 操作日志（谁、何时、做了什么）
├── llm/                    # 概念：大模型。一个职责 = 一个文件
│   ├── client.py               # 模型 API 客户端（全项目只此一处调模型）
│   └── messages.py             # 请求上下文组装
├── models/                 # 概念：数据表。一个表 = 一个文件
│   ├── user.py                 # 用户表
│   ├── task.py                 # 任务/子任务表
│   ├── confirmation.py         # 高危确认记录表
│   ├── audit_log.py            # 操作日志表
│   └── feishu_token.py         # 飞书授权令牌表
└── utils/                  # 概念：通用工具。一个工具 = 一个文件，禁止大杂烩
    ├── time_utils.py           # 时间处理
    └── id_utils.py             # ID 生成
```

## 3. 前端 frontend/（一个页面/组件 = 一个文件）

```
frontend/
└── src/
    ├── pages/                  # 概念：页面
    │   ├── LoginPage.vue           # 登录页（跳转飞书授权）
    │   ├── ChatPage.vue            # 对话/任务发起页
    │   └── ConfirmationPage.vue    # 高危确认页
    ├── components/             # 概念：组件
    │   ├── TaskInput.vue           # 任务输入框
    │   ├── ConfirmModal.vue        # 确认弹窗
    │   └── ResultCard.vue          # 结果卡片
    └── api/                    # 概念：后端接口封装，与后端资源对应
        ├── auth.ts                 # 登录接口
        ├── task.ts                 # 任务接口
        └── confirmation.ts         # 确认接口
```

## 4. 放置规则（背这 10 条）

| 你要做的事 | 文件放哪 | 概念 |
|-----------|----------|------|
| 新增一个接口资源 | `backend/api/v1/<资源名>.py` + `schemas/<资源名>.py` | 资源 |
| 新增 Agent 环节 | `backend/agent/<环节名>.py` | 环节 |
| 新增一个工具 | `backend/tools/<工具名>.py` + 在 `registry.py` 登记 | 工具 |
| 飞书相关 | `backend/feishu/`（client / auth / token_store） | 集成 |
| 改高危规则 | `backend/safety/high_risk.py` | 机制 |
| 改确认流程 | `backend/safety/gate.py` | 机制 |
| 改提示词 | `config/prompts/<用途>.md`（不动代码） | 提示词 |
| 换大模型 | 只改 `backend/llm/client.py` | 大模型 |
| 新增数据表 | `backend/models/<表名>.py`，类名 = 表名 | 表 |
| 写测试 | `tests/` 镜像 backend，如 `tests/safety/test_gate.py` | 被测概念 |

## 5. “一个概念一个文件”的判定标准

一个文件里出现以下情况，就必须拆：

1. **出现两个不相关的业务概念** → 拆成两个文件
2. **改 A 功能要动 B 功能的代码** → A、B 各建文件
3. **文件超过约 200 行且承担多个职责** → 按职责拆
4. **通用工具类**：不允许一个 `utils.py` 装所有杂项，每个工具概念一个文件

命名：文件名 = 概念名（Python 小写下划线；前端组件大驼峰）。

## 6. 已定决策与前置（详见《办公自动化Agent_技术选型.md》）

- 已定：Vue / SQLite（预留 PostgreSQL）/ 飞书日历 API（用户身份）/ QQ 邮箱 IMAP/SMTP / 本地 Excel/CSV / 飞书登录（默认）
- 飞书权限申请：`calendar:calendar:readonly` + `calendar:calendar` + 用户信息
- 配置：飞书 app_id/app_secret/redirect_uri、QQ 邮箱授权码等全部放 `.env`，只从 `config/settings.py` 读取
- 实施前置：飞书自建应用 + 权限审批；QQ 邮箱开启 IMAP/SMTP 并生成授权码；Excel 文件清单；内测名单（≤50人）