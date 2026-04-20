# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

个人记账应用 (Personal Finance App) — 基于 FastAPI 的个人财务管理系统，集成通义千问 AI 实现自然语言记账。主项目位于 `personal_finance_fastapi_5.0/`。

## Commands

```bash
# 启动服务（在 personal_finance_fastapi_5.0/ 目录下）
python -m app.main
python -m app.main --host 0.0.0.0 --port 8080

# 代码格式检查
autopep8 --diff <file>
pycodestyle <file>

# 测试
pytest tests/
```

启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger API 文档。

## Architecture

```
app/
├── main.py          # 入口，FastAPI lifespan、全局异常处理、路由注册
├── api/v1/          # 路由层（ai / finance / user）
├── config/          # 配置（auth / database / logger / prompts / settings）
├── core/llm/        # LLM 客户端封装
├── crud/            # 数据访问层（原生 SQL，非 ORM）
├── schemas/         # Pydantic 数据模型
├── services/        # 业务逻辑层
│   ├── ai/v1_1~v1_4/  # AI 服务多版本迭代（v1_1 基础版 → v1_4 Agent 版）
│   ├── finance/       # 记账业务逻辑
│   └── user/          # 用户业务逻辑
└── utils/            # 工具函数
```

### 分层约定

- **API 层**：接收请求、调用 service、返回统一响应（`success_response` / `error_response`）
- **Service 层**：业务逻辑，调用 crud 和 llm client
- **CRUD 层**：纯数据操作，使用 `get_db()` 上下文管理器管理连接和事务
- **Schema 层**：所有请求/响应使用 Pydantic 模型，统一通过 `schemas/response.py` 包装

### 数据库

- SQLite，文件位于项目根目录 `personal_finance.db`
- 两张表：`users`、`finance_records`（user_id 外键关联 users）
- 使用 `request_id`（日期+序号）防重复提交
- 数据库操作使用 `with get_db()` 上下文管理器，异常自动回滚

### AI 服务版本演进

| 版本 | 路径 | 特点 |
|------|------|------|
| v1_1 | services/ai/v1_1/ | 基础版，直接调用 LLM + JSON 解析 |
| v1_2 | services/ai/v1_2/ | 引入 LangChain chain + 重试机制 |
| v1_3 | services/ai/v1_3/ | 自定义 llm_client 解耦 + simple_agent |
| v1_4 | services/ai/v1_4/ | 完整 Agent 架构（planner / executor / evaluator / tool_registry / memory） |

当前活跃版本为 **v1_4**，采用 Planner → Executor → Evaluator 循环架构。

### LLM 接入

- 使用通义千问 API（兼容 OpenAI 接口格式）
- 配置通过 `.env` 文件：`QWEN_API_KEY`、`QWEN_BASE_URL`、`QWEN_MODEL`
- settings 通过 `pydantic-settings` 管理环境变量

### 认证

- JWT token 认证，30 分钟过期
- 密码使用 bcrypt 哈希
- 认证逻辑在 `config/auth.py`，通过 FastAPI Depends 注入

## Conventions

- 代码注释和日志使用中文
- 日志系统（`config/logger.py`）：控制台输出 WARNING+，文件日志按日滚动保留 30 天
- API 响应统一格式：`{ code: int, msg: str, data: any }`
