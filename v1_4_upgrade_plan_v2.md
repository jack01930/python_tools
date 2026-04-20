# AI 记账助手 v1.4 升级方案（两步走）

## 概述
根据您的反馈，将升级计划分为两个阶段：**第一步**解决核心体验问题（AI记忆、量化指标、前端界面）；**第二步**扩展功能与可视化。本方案优先探索AI记忆持久化的多种方案，并提供具体实施建议。

## 第一步：核心体验升级（2-3周）

### 1. AI 记忆能力持久化

#### 问题分析
当前 `memory/short_memory.py` 仅构建当前轮次状态快照，`AgentState.history` 字段未使用，导致：
- 多轮对话中无法记住已澄清的槽位（金额、时间、分类）
- 每次对话都是独立的，用户体验差
- 无法实现上下文感知的个性化服务

#### 可选方案对比

| 方案 | 描述 | 优点 | 缺点 | 推荐度 |
|------|------|------|------|--------|
| **A. 新增数据库表** `ai_conversation_history` | 在现有 SQLite 中新增表存储每轮对话 | 1. 数据持久可靠<br>2. 支持复杂查询<br>3. 与现有架构一致 | 需修改数据库模式 | ★★★★★ |
| **B. 扩展 users 表 JSON 字段** | 在 `users` 表添加 `conversation_history` JSON 字段 | 1. 无需新增表<br>2. 结构灵活 | 1. JSON 查询性能差<br>2. users 表臃肿<br>3. 难以维护 | ★★☆☆☆ |
| **C. 文件存储** | 每个用户一个 JSON 文件（`conversations/{user_id}.json`） | 1. 简单易实现<br>2. 无需数据库变更 | 1. 缺乏事务保证<br>2. 备份困难<br>3. 查询效率低 | ★★★☆☆ |
| **D. 向量数据库（Chroma）** | 存储对话嵌入向量，支持语义检索 | 1. 支持相似问题匹配<br>2. 适合长上下文 | 1. 架构复杂<br>2. 维护成本高<br>3. 过度设计 | ★★☆☆☆ |
| **E. 依赖 Qwen 长上下文** | 在 prompt 中携带完整历史（利用 128K 上下文） | 1. 无存储开销<br>2. 模型直接感知历史 | 1. Token 消耗大<br>2. 历史过长会截断<br>3. 无法跨会话 | ★★★☆☆ |

#### 推荐方案：**A + E 混合策略**
- **持久化存储**：新增 `ai_conversation_history` 表，确保数据可靠。
- **智能上下文**：从数据库检索最近 N 轮对话，通过 LLM 生成摘要，再注入 prompt。
- **Qwen 长上下文利用**：对于最近对话（如最近 5 轮），直接包含原文；更早历史使用摘要。

#### 表结构设计
```sql
CREATE TABLE ai_conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    session_id TEXT NOT NULL,  -- 会话标识（如日期+随机数）
    role TEXT NOT NULL,        -- 'user' 或 'assistant'
    content TEXT NOT NULL,     -- 消息内容
    slots_filled TEXT,         -- JSON 格式已填充槽位，如 {"amount": 100, "category": "饮食"}
    metadata TEXT,             -- JSON 格式附加信息（响应时间、工具调用等）
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_user_session ON ai_conversation_history(user_id, session_id);
CREATE INDEX idx_created_at ON ai_conversation_history(created_at);
```

#### 实施步骤
1. 在 `config/database.py` 的 `init_db()` 中添加新表创建语句。
2. 创建 `app/services/ai/v1_4/memory/long_memory.py`：
   - `save_conversation(user_id, session_id, role, content, slots_filled)`
   - `get_recent_conversations(user_id, limit=10)`
   - `get_session_slots(user_id, session_id)` 获取当前会话已填充槽位
3. 修改 `agent.py`：
   - 会话开始时从数据库加载历史（最近 5 轮）和已填充槽位。
   - 每轮对话结束后保存用户输入和 AI 响应。
4. 更新 `planner_prompt.py`：在 prompt 模板中加入历史上下文和槽位状态。
5. **摘要生成**：当历史超过 5 轮时，调用 Qwen 生成历史摘要，减少 token 消耗。

### 2. 量化指标系统

#### 目标
实时监控 AI 性能，支持数据驱动迭代。

#### 指标定义
| 指标 | 类型 | 描述 |
|------|------|------|
| `ai_intent_recognition_total` | Counter | 意图识别总次数（按意图类型标签） |
| `ai_tool_call_success_total` | Counter | 工具调用成功次数（按工具名标签） |
| `ai_tool_call_failure_total` | Counter | 工具调用失败次数（按工具名、错误类型标签） |
| `ai_clarification_required_total` | Counter | 需要澄清的对话轮次 |
| `ai_slot_filling_success_total` | Counter | 槽位填充成功次数（金额、时间、分类） |
| `ai_response_time_seconds` | Histogram | 从请求到响应的耗时分布 |
| `ai_conversation_length` | Gauge | 当前活跃会话数 |

#### 方案选择
- **轻量级**：自定义 `/metrics` 端点，返回 JSON 格式指标（适合初期）。
- **标准方案**：集成 `prometheus-client`，提供 `/metrics` Prometheus 格式端点，便于 Grafana 集成。

#### 实施步骤
1. 安装 `prometheus-client`：`pip install prometheus-client`
2. 创建 `app/config/metrics.py`：
   - 定义全局指标对象。
   - 提供装饰器函数 `record_metrics`。
3. 在关键位置打点：
   - `agent.py`：记录响应时间、意图识别。
   - `planner.py`：记录澄清需求。
   - `executor.py`：记录工具调用成功/失败。
   - `finance_tools.py`：记录槽位填充。
4. 在 `main.py` 中添加 `/metrics` 端点。
5. （可选）配置 Grafana 数据源和仪表盘。

### 3. 前端界面改善

#### 当前状态
纯后端 API，仅提供 Swagger UI/Redoc 文档。

#### 短期优化（不开发完整前端）
1. **增强 Swagger UI 体验**：
   - 定制主题，添加项目 logo。
   - 为每个 API 端点添加详细示例请求/响应。
   - 增加 `try it out` 预填充示例数据。
2. **提供 Postman 集合**：
   - 导出完整的 `postman_collection.json`。
   - 包含环境变量（base_url、token）。
   - 编写使用指南。
3. **简化 API 调用**：
   - 确保 API 响应格式统一、文档清晰。
   - 提供常见用例的 curl 命令示例。

#### 长期计划（第二步之后）
- 开发轻量级 Vue/React 前端，集成图表组件。
- 或使用现成 Admin 模板（如 Django Admin 风格）。

#### 实施步骤
1. 在 `main.py` 中定制 Swagger 配置（`openapi_url`、`swagger_ui_parameters`）。
2. 为每个 Pydantic schema 添加 `example` 字段。
3. 使用 `fastapi.openapi.utils.get_openapi` 生成增强文档。
4. 编写 `docs/postman_guide.md` 说明如何使用 Postman 测试。

## 第二步：功能与可视化扩展（2-3周）

### 1. 功能匮乏解决

#### 图片识别记账
- **方案**：集成 Tesseract OCR（离线免费） + Qwen 解析。
- **实施**：
  1. 安装 `pytesseract`、`Pillow`。
  2. 创建 `app/services/ocr_service.py`：提供 `extract_text_from_image(image_bytes)`。
  3. 新增 `tools/image_tools.py`：`upload_receipt_tool`，调用 OCR 服务，将文本传给 LLM 解析为记账参数。
  4. 在 `tool_registry` 中注册。
  5. API 端点：`POST /api/v1/ai/upload-receipt`（支持 multipart/form-data）。

#### 记录修改功能
- **方案**：新增 `update_record_tool`。
- **实施**：
  1. 在 `finance_service.py` 中添加 `update_finance_record(record_id, updates, user_id)`。
  2. 在 `finance_tools.py` 中创建 `update_record_tool`，支持部分字段更新。
  3. 注册到 `tool_registry`。

#### 高级工具
- `set_budget_tool`：设置月度预算，存储到 `users` 表或新表 `user_budgets`。
- `analyze_spending_tool`：消费分析，给出超支提醒、分类建议。

### 2. 数据可视化

#### 方案选择
- **后端生成图表**：使用 `matplotlib` 生成 PNG，简单但不够灵活。
- **前端渲染图表**：API 返回结构化数据，前端用 Chart.js 渲染（推荐）。
- **混合方案**：后端提供数据集，前端使用 ECharts/Vue-Chartjs。

#### 实施步骤
1. 扩展 `finance_service.get_finance_records()` 返回图表数据集：
   ```json
   {
     "statistics": {...},
     "charts": {
       "category_distribution": [{"category": "饮食", "amount": 500}, ...],
       "daily_trend": [{"date": "2024-01-01", "income": 0, "expense": 100}, ...]
     }
   }
   ```
2. 新增端点 `/api/v1/finance/charts/monthly` 返回图表数据。
3. 若开发前端，则集成 Chart.js 组件。

## 实施路线图

### 第一阶段（2-3周）
| 周 | 任务 |
|----|------|
| 1 | 1. 设计并实现 `ai_conversation_history` 表<br>2. 实现 `long_memory.py` 基础 CRUD<br>3. 修改 `agent.py` 集成历史加载 |
| 2 | 1. 更新 `planner_prompt` 加入历史上下文<br>2. 实现摘要生成逻辑（可选）<br>3. 集成 `prometheus-client`，定义指标 |
| 3 | 1. 在关键位置添加指标打点<br>2. 定制 Swagger UI，编写 Postman 集合<br>3. 测试记忆与指标功能 |

### 第二阶段（2-3周）
| 周 | 任务 |
|----|------|
| 4 | 1. 集成 Tesseract OCR，实现图片识别工具<br>2. 添加 `update_record_tool` 和 `set_budget_tool` |
| 5 | 1. 扩展 `finance_service` 返回图表数据集<br>2. 新增图表数据端点<br>3. 前端原型（可选） |
| 6 | 1. 端到端测试所有新功能<br>2. 性能优化，文档完善 |

## 技术选型确认

- **记忆存储**：SQLite 新增表（可靠、易查询）
- **量化监控**：`prometheus-client`（标准、可扩展）
- **OCR**：Tesseract（离线免费，精度可接受）
- **图表**：Chart.js（前端渲染，轻量灵活）
- **前端推迟**：先优化 Swagger + Postman，后期视需求开发

## 风险与缓解

- **Qwen Token 消耗**：历史摘要策略可控制 token 使用；监控 token 用量。
- **OCR 识别率**：结合 LLM 后处理提升鲁棒性；提供手动修正界面。
- **数据库性能**：对话历史表建立索引，定期归档旧数据。
- **指标存储**：Prometheus 默认内存存储，可配置持久化。

---

**下一步**：请审核此分步方案，重点确认：
1. AI 记忆混合策略（数据库表 + Qwen 上下文）是否可行？
2. 量化指标使用 Prometheus 是否接受？
3. 第一阶段暂不开发完整前端，仅优化 API 文档，是否同意？

待您批准后，即可开始第一阶段实施。