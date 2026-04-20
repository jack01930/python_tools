# Personal Finance FastAPI 5.0

基于 FastAPI 的个人财务管理系统，集成通义千问 AI 实现自然语言记账。

## ✨ 功能特性

- **AI 自然语言记账**：用中文描述消费，AI 自动解析为结构化记账
- **多轮对话记忆**：Agent 架构支持上下文理解与槽位记忆
- **财务数据分析**：月度统计、分类汇总、消费趋势
- **RESTful API**：完整的用户认证与数据管理接口
- **可扩展架构**：模块化设计，支持 AI 服务多版本迭代

## 🏗️ 技术栈

| 组件 | 技术选型 |
|------|----------|
| **后端框架** | FastAPI + Uvicorn |
| **AI 框架** | LangChain + 通义千问 API |
| **数据库** | SQLite + SQLAlchemy |
| **认证授权** | JWT + bcrypt |
| **数据验证** | Pydantic v2 |
| **向量存储** | ChromaDB (v1.5+) |
| **Embedding** | Sentence-Transformers (v1.5+) |

## 📁 项目结构

```
personal_finance_fastapi_5.0/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── api/v1/                    # API 路由层
│   │   ├── ai.py                  # AI 记账接口 (v1.4/v1.5)
│   │   ├── finance.py             # 手动记账接口
│   │   └── user.py                # 用户认证接口
│   ├── config/                    # 配置模块
│   │   ├── auth.py                # JWT 认证
│   │   ├── database.py            # 数据库连接
│   │   ├── logger.py              # 日志配置
│   │   ├── prompts.py             # AI 提示词模板
│   │   └── settings.py            # 环境变量配置
│   ├── core/llm/                  # LLM 客户端封装
│   │   └── client.py              # 通义千问 API 客户端
│   ├── crud/                      # 数据访问层
│   │   ├── finance.py             # 记账记录 CRUD
│   │   └── user.py                # 用户 CRUD
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── ai.py                  # AI 请求/响应模型
│   │   ├── finance.py             # 记账数据模型
│   │   ├── response.py            # 统一响应格式
│   │   └── user.py                # 用户数据模型
│   ├── services/                  # 业务逻辑层
│   │   ├── ai/                    # AI 服务多版本
│   │   │   ├── v1_1/              # 基础版 (直接解析)
│   │   │   ├── v1_2/              # LangChain Chain 版
│   │   │   ├── v1_3/              # 自定义 LLM 客户端版
│   │   │   ├── v1_4/              # Agent 架构版 (当前主版本)
│   │   │   └── v1_5/              # 长期记忆版 (向量库)
│   │   ├── finance/               # 记账业务逻辑
│   │   └── user/                  # 用户业务逻辑
│   └── utils/                     # 工具函数
├── tests/                         # 测试用例
├── personal_finance.db            # SQLite 数据库文件
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量示例
└── README.md                      # 本文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd personal_finance_fastapi_5.0

# 创建虚拟环境 (Python 3.9+)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
# 通义千问 API 配置
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max

# JWT 配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 数据库配置
DATABASE_URL=sqlite:///personal_finance.db
```

### 3. 初始化数据库

```bash
# 运行初始化脚本 (首次启动会自动创建表)
python -m app.main
```

### 4. 启动服务

```bash
# 开发模式 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

服务启动后访问：http://127.0.0.1:8000/docs

## 🔌 API 文档

### 用户认证
- `POST /api/v1/user/register` - 用户注册
- `POST /api/v1/user/login` - 用户登录
- `GET /api/v1/user/me` - 获取当前用户信息

### 手动记账
- `POST /api/v1/finance/record` - 添加记账记录
- `GET /api/v1/finance/records` - 查询记账记录
- `DELETE /api/v1/finance/record/{record_id}` - 删除记录
- `GET /api/v1/finance/summary/{year}/{month}` - 月度统计

### AI 记账 (v1.4)
- `POST /api/v1/ai/auto_record` - AI 自然语言记账

### AI 记账 (v1.5 - 带长期记忆)
- `POST /api/v1/ai/chat-v2` - AI 记账 (支持多轮对话记忆)

## 🤖 AI 服务架构

### v1.4 Agent 架构

```
Planner → Executor → Evaluator (循环)
```

**工作流程**：
1. **Planner**：分析用户输入，结合历史步骤，决定下一步动作
2. **Executor**：执行工具调用 (记账/查询/删除/统计)
3. **状态管理**：跟踪执行步骤，限制最大步数防止无限循环
4. **统一响应**：格式化返回结果，支持澄清询问和最终回复

**支持的动作类型**：
- `tool_call`：调用工具函数
- `clarify`：向用户询问缺失信息
- `respond`：直接回复用户
- `fail`：处理失败，返回错误原因

### v1.5 长期记忆增强

在 v1.4 基础上增加：
- **向量记忆存储**：使用 ChromaDB 存储对话历史
- **语义检索**：基于 Embedding 的相似对话查找
- **槽位记忆**：跨对话记住已确认的信息 (金额、分类等)
- **会话管理**：支持多轮对话上下文保持

## 💡 使用示例

### 示例 1：AI 自然语言记账

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/auto_record" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "今天中午吃了20元的牛肉面"}'
```

**响应**：
```json
{
  "code": 200,
  "msg": "Agent处理成功",
  "data": {
    "type": "final",
    "answer": "已记录：饮食分类，支出20元，备注：原句：今天中午吃了20元的牛肉面",
    "steps": [
      {
        "step_no": 1,
        "thought": "用户想记录一笔饮食消费",
        "action": "tool_call",
        "tool_name": "add_record",
        "tool_input": {
          "category": "饮食",
          "amount": -20,
          "remark": "原句：今天中午吃了20元的牛肉面"
        }
      }
    ]
  }
}
```

### 示例 2：多轮对话 (v1.5)

```bash
# 第一轮：记录午餐
curl -X POST "http://127.0.0.1:8000/api/v1/ai/chat-v2" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"text": "午餐吃了30元"}'

# 第二轮：查询本月饮食开销 (AI 记得之前的记录)
curl -X POST "http://127.0.0.1:8000/api/v1/ai/chat-v2" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"text": "我这个月吃饭花了多少", "session_id": "<上一轮返回的session_id>"}'
```

## 🔧 开发指南

### 代码规范
```bash
# 代码格式检查
autopep8 --diff <file>
pycodestyle <file>

# 自动格式化
autopep8 --in-place --aggressive --aggressive <file>
```

### 添加新工具
1. 在 `app/services/ai/v1_4/tools/` 创建新工具文件
2. 使用 `@tool` 装饰器定义工具函数
3. 在 `tool_registry.py` 中注册工具
4. 更新 Planner 提示词中的工具描述

### AI 服务版本管理
- **v1.1**：基础版，直接调用 LLM + JSON 解析
- **v1.2**：引入 LangChain chain + 重试机制
- **v1.3**：自定义 llm_client 解耦 + simple_agent
- **v1.4**：完整 Agent 架构 (planner/executor/evaluator)
- **v1.5**：长期记忆 + 向量存储

## 📊 数据库设计

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 用户ID |
| username | VARCHAR(50) UNIQUE | 用户名 |
| hashed_password | VARCHAR(100) | 密码哈希 |
| created_at | DATETIME | 创建时间 |

### finance_records 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 记录ID |
| user_id | INTEGER | 用户ID (外键) |
| category | VARCHAR(20) | 分类 |
| amount | DECIMAL(10,2) | 金额 (负数为支出) |
| remark | TEXT | 备注 |
| record_date | DATE | 记账日期 |
| created_at | DATETIME | 创建时间 |

### ai_conversation_history 表 (v1.5+)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 记录ID |
| user_id | INTEGER | 用户ID |
| session_id | VARCHAR(100) | 会话ID |
| role | VARCHAR(20) | 角色 (user/assistant/system) |
| content | TEXT | 消息内容 |
| slots_filled | JSON | 已填充槽位 |
| metadata | JSON | 元数据 |
| created_at | DATETIME | 创建时间 |

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与联系

如有问题或建议，请通过以下方式联系：
- GitHub Issues: [项目 Issues 页面](https://github.com/yourusername/personal_finance_fastapi_5.0/issues)
- Email: your.email@example.com

---

**提示**：本项目为个人学习项目，不建议直接用于生产环境。使用 AI 服务时请注意 API 调用成本。

## 🚀 下一步计划

- [ ] 实现预算管理功能
- [ ] 添加数据可视化图表
- [ ] 支持多用户家庭账本
- [ ] 集成更多支付平台 API
- [ ] 开发移动端应用
