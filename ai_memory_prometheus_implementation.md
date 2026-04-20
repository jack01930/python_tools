# AI 记忆与量化指标实现方案（详细版）

## 一、AI 记忆混合策略实现

### 1.1 数据库表设计

在 `app/config/database.py` 的 `init_db()` 函数中添加：

```python
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute('PRAGMA foreign_keys=ON;')
        # ... 现有 users 和 finance_records 表创建 ...
        
        # 新增 AI 对话历史表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            slots_filled TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        # 创建索引提升查询性能
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_session ON ai_conversation_history(user_id, session_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON ai_conversation_history(created_at);")
        
        conn.commit()
        conn.close()
        logger_info("数据库初始化完成，AI对话历史表已创建")
    except sqlite3.Error as e:
        logger_error(f"数据库初始化失败 | 信息：{str(e)}")
        raise e
```

**字段说明：**
- `session_id`：会话标识，建议格式 `{user_id}_{timestamp}_{random}`，如 `1_20240101_1234`
- `role`：`user` 或 `assistant`
- `content`：消息内容
- `slots_filled`：JSON 格式已填充槽位，如 `{"amount": 100, "category": "饮食", "date": "2024-01-01"}`
- `metadata`：JSON 格式附加信息，如 `{"response_time": 1.2, "tool_called": "add_record"}`
- `created_at`：创建时间，自动生成

### 1.2 长期记忆模块实现

创建 `app/services/ai/v1_4/memory/long_memory.py`：

```python
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.config.logger import info as logger_info, error as logger_error
from app.config.database import get_db_connection


class LongMemory:
    def __init__(self, user_id: int, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id or self._generate_session_id()
    
    def _generate_session_id(self) -> str:
        """生成会话ID：用户ID_日期_随机数"""
        import uuid
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = str(uuid.uuid4())[:8]
        return f"{self.user_id}_{date_str}_{random_str}"
    
    def save_message(self, role: str, content: str, slots_filled: Optional[Dict] = None, metadata: Optional[Dict] = None) -> bool:
        """保存一条对话消息"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ai_conversation_history 
                (user_id, session_id, role, content, slots_filled, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.user_id,
                self.session_id,
                role,
                content,
                json.dumps(slots_filled) if slots_filled else None,
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger_info(f"[LongMemory] 保存消息成功 | user_id:{self.user_id} | role:{role}")
            return True
        except Exception as e:
            logger_error(f"[LongMemory] 保存消息失败 | user_id:{self.user_id} | error:{repr(e)}")
            return False
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话历史"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role, content, slots_filled, created_at
                FROM ai_conversation_history
                WHERE user_id = ? AND session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (self.user_id, self.session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 反转顺序，按时间正序排列
            conversations = []
            for row in reversed(rows):
                conversations.append({
                    "role": row["role"],
                    "content": row["content"],
                    "slots_filled": json.loads(row["slots_filled"]) if row["slots_filled"] else {},
                    "created_at": row["created_at"]
                })
            
            return conversations
        except Exception as e:
            logger_error(f"[LongMemory] 获取历史失败 | user_id:{self.user_id} | error:{repr(e)}")
            return []
    
    def get_session_slots(self) -> Dict[str, Any]:
        """获取当前会话已填充的所有槽位"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT slots_filled
                FROM ai_conversation_history
                WHERE user_id = ? AND session_id = ? AND slots_filled IS NOT NULL
            """, (self.user_id, self.session_id))
            
            rows = cursor.fetchall()
            conn.close()
            
            # 合并所有槽位，后出现的覆盖先出现的
            merged_slots = {}
            for row in rows:
                if row["slots_filled"]:
                    slots = json.loads(row["slots_filled"])
                    merged_slots.update(slots)
            
            return merged_slots
        except Exception as e:
            logger_error(f"[LongMemory] 获取槽位失败 | user_id:{self.user_id} | error:{repr(e)}")
            return {}
    
    def generate_history_summary(self, llm_client, max_rounds: int = 5) -> str:
        """
        生成历史摘要
        策略：最近 N 轮完整显示，更早的生成摘要
        """
        all_conversations = self.get_recent_conversations(limit=20)
        
        if len(all_conversations) <= max_rounds:
            # 历史较少，直接完整显示
            return self._format_conversations(all_conversations)
        
        # 分割：最近 N 轮完整，更早的生成摘要
        recent = all_conversations[-max_rounds:]
        older = all_conversations[:-max_rounds]
        
        summary = self._generate_llm_summary(older, llm_client)
        recent_text = self._format_conversations(recent)
        
        return f"历史摘要（较早对话）：\n{summary}\n\n最近对话：\n{recent_text}"
    
    def _format_conversations(self, conversations: List[Dict]) -> str:
        """格式化对话历史为文本"""
        lines = []
        for conv in conversations:
            lines.append(f"{conv['role']}: {conv['content']}")
            if conv.get('slots_filled'):
                lines.append(f"  已填槽位: {json.dumps(conv['slots_filled'], ensure_ascii=False)}")
        return "\n".join(lines)
    
    def _generate_llm_summary(self, conversations: List[Dict], llm_client) -> str:
        """使用 LLM 生成历史摘要"""
        if not conversations:
            return "无更早历史。"
        
        # 构建摘要 prompt
        history_text = self._format_conversations(conversations)
        prompt = f"""
请将以下记账对话历史总结为简洁的摘要，保留关键信息：
- 用户的主要需求
- 已确认的记账参数（金额、分类、时间等）
- 已完成的记账操作

对话历史：
{history_text}

摘要：
"""
        
        try:
            response = llm_client.invoke(prompt)
            return response.strip()
        except Exception:
            # LLM 失败时返回简单摘要
            return f"共 {len(conversations)} 轮较早对话，涉及记账操作。"


def create_long_memory(user_id: int, session_id: Optional[str] = None) -> LongMemory:
    """工厂函数，创建 LongMemory 实例"""
    return LongMemory(user_id, session_id)
```

### 1.3 修改 Agent 状态管理

修改 `app/services/ai/v1_4/state.py`：

```python
from app.services.ai.v1_4.schemas import AgentPlannerOutput, AgentState, AgentStep
from app.services.ai.v1_4.memory.long_memory import create_long_memory


def create_initial_state(user_text: str, user_id: int, max_steps: int = 3, session_id: Optional[str] = None) -> AgentState:
    """创建初始状态，加载历史记忆"""
    # 创建长期记忆实例
    long_memory = create_long_memory(user_id, session_id)
    
    # 获取当前会话已填充槽位
    filled_slots = long_memory.get_session_slots()
    
    # 创建状态对象
    state = AgentState(
        user_id=user_id,
        user_text=user_text,
        max_steps=max_steps,
        history=[],  # 保留字段，可用于存储短期上下文
    )
    
    # 将槽位信息存储在 state 的 metadata 中
    state.metadata = {"filled_slots": filled_slots, "session_id": long_memory.session_id}
    
    return state


def append_planner_step(state: AgentState, planner_output: AgentPlannerOutput) -> AgentStep:
    action = planner_output.action
    step = AgentStep(
        step_no=len(state.steps) + 1,
        thought=planner_output.thought,
        action=action.action,
        tool_name=action.tool_name,
        tool_input=action.tool_input,
        message=action.message,
    )
    state.steps.append(step)
    return step


def build_state_snapshot(state: AgentState) -> str:
    """构建状态快照，现在包含历史上下文"""
    lines = []
    
    # 1. 显示已填充槽位
    if state.metadata and "filled_slots" in state.metadata:
        filled_slots = state.metadata.get("filled_slots", {})
        if filled_slots:
            lines.append("已确认信息：")
            for key, value in filled_slots.items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
    
    # 2. 显示当前轮次执行步骤
    if state.steps:
        lines.append("当前执行步骤：")
        for step in state.steps:
            lines.append(
                f"step={step.step_no} | action={step.action} | "
                f"tool={step.tool_name} | observation={step.observation}"
            )
    
    return "\n".join(lines) if lines else "暂无历史步骤。"
```

### 1.4 修改 Agent 主流程

修改 `app/services/ai/v1_4/agent.py`：

```python
from app.services.ai.v1_4.memory.long_memory import create_long_memory
from app.services.ai.v1_4.state import create_initial_state, append_planner_step, build_state_snapshot


def process_ai_request(user_text: str, user_id: int) -> dict:
    # 创建长期记忆实例
    long_memory = create_long_memory(user_id)
    
    # 加载历史对话（用于 planner 上下文）
    recent_history = long_memory.get_recent_conversations(limit=5)
    
    # 创建初始状态（会自动加载已填充槽位）
    state = create_initial_state(
        user_text=user_text, 
        user_id=user_id, 
        max_steps=3,
        session_id=long_memory.session_id
    )
    
    # 保存用户输入到历史
    long_memory.save_message(
        role="user",
        content=user_text,
        metadata={"request_time": datetime.now().isoformat()}
    )
    
    logger_info(f"[AI_V1_4] Agent开始执行 | user_id:{user_id} | session:{long_memory.session_id}")
    
    try:
        for _ in range(state.max_steps):
            # 构建历史上下文字符串
            history_context = "\n".join([
                f"{conv['role']}: {conv['content']}" 
                for conv in recent_history[-3:]  # 最近3轮对话
            ]) if recent_history else "无历史对话。"
            
            # 将历史上下文注入到 state 中，供 planner 使用
            state.history_context = history_context
            
            planner_output = plan_next_step(state)
            step = append_planner_step(state, planner_output)
            
            if step.action == "tool_call":
                step.observation = execute_tool(
                    tool_name=step.tool_name or "",
                    tool_input=step.tool_input,
                    user_id=user_id,
                )
                
                # 检查工具调用是否填充了槽位
                self._update_slots_from_tool_call(step, long_memory)
                continue
            
            if step.action == "clarify":
                question = _render_clarify_question(user_text=user_text, planner_message=step.message or "")
                
                # 保存 AI 澄清问题到历史
                long_memory.save_message(
                    role="assistant",
                    content=question,
                    metadata={"action": "clarify"}
                )
                
                return success_response(...)
            
            if step.action == "respond":
                state_snapshot = build_state_snapshot(state)
                reply = _render_final_reply(...)
                
                # 保存 AI 回复到历史
                long_memory.save_message(
                    role="assistant",
                    content=reply,
                    metadata={"action": "respond"}
                )
                
                return success_response(...)
            
            if step.action == "fail":
                raise ValueError(step.message or "Agent执行失败")
        
        raise ValueError("超过最大推理步数，Agent未能完成任务")
    except Exception as e:
        logger_error(f"[AI_V1_4] Agent执行失败 | user_id:{user_id} | error:{repr(e)}")
        raise
    
    def _update_slots_from_tool_call(self, step: AgentStep, long_memory: LongMemory):
        """从工具调用结果中提取已填充槽位并保存"""
        if step.tool_name == "add_record" and step.observation:
            try:
                # 从 tool_input 提取槽位信息
                tool_input = step.tool_input
                slots = {}
                if "amount" in tool_input:
                    slots["amount"] = tool_input["amount"]
                if "category" in tool_input:
                    slots["category"] = tool_input["category"]
                if "remark" in tool_input:
                    slots["remark"] = tool_input["remark"]
                
                # 保存槽位到历史
                if slots:
                    long_memory.save_message(
                        role="system",
                        content=f"工具调用成功: {step.tool_name}",
                        slots_filled=slots,
                        metadata={"tool": step.tool_name}
                    )
            except Exception as e:
                logger_error(f"[AI] 更新槽位失败 | error:{repr(e)}")
```

### 1.5 更新 Planner Prompt

修改 `app/services/ai/v1_4/prompts/planner_prompt.py`：

```python
PLANNER_SYSTEM_PROMPT = """
你是一个"可控型记账Agent"的规划器，负责决定下一步动作。

你的目标：
1. 理解用户当前问题，结合历史对话上下文。
2. 利用已确认的信息（槽位），避免重复询问。
3. 结合已执行步骤，决定下一步是：
   - tool_call: 调用一个工具
   - clarify: 缺少关键信息时向用户追问
   - respond: 已经可以直接回复用户
   - fail: 明确无法处理时返回失败原因

你必须遵守以下规则：
1. 只允许从给定工具列表中选择 tool_name。
2. 如果是 tool_call，tool_input 必须是一个 JSON 对象。
3. 如果用户已在历史中提供过某些信息（如金额、分类、时间），请直接使用，不要再询问。
4. 涉及删除、查询、总结等操作时，参数不完整就先 clarify，不要瞎猜。
5. 对"今天、本月、这个月、今年"这类时间表达，你可以转成明确年月。
6. 当前项目专注个人记账，偏离记账领域的问题可以 respond，礼貌说明能力边界。
7. 你的输出必须严格符合格式要求。
"""

def build_planner_prompt(format_instructions: str) -> ChatPromptTemplate:
    safe_format_instructions = format_instructions.replace("{", "{{").replace("}", "}}")
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                PLANNER_SYSTEM_PROMPT
                + "\n\n可用工具如下：\n{tool_descriptions}\n\n"
                + "输出格式要求：\n"
                + safe_format_instructions,
            ),
            (
                "human",
                "用户ID: {user_id}\n"
                "当前日期: {today}\n"
                "历史对话上下文:\n{history_context}\n"
                "已确认信息（槽位）:\n{filled_slots}\n"
                "用户输入: {user_text}\n"
                "已执行步骤:\n{state_snapshot}",
            ),
        ]
    )
```

修改 `app/services/ai/v1_4/planner.py`：

```python
def plan_next_step(state: AgentState) -> AgentPlannerOutput:
    state_snapshot = build_short_memory(state)
    
    # 获取已填充槽位
    filled_slots = state.metadata.get("filled_slots", {}) if state.metadata else {}
    filled_slots_text = "\n".join([f"- {k}: {v}" for k, v in filled_slots.items()]) if filled_slots else "无已确认信息"
    
    # 获取历史上下文
    history_context = getattr(state, "history_context", "无历史对话。")
    
    payload = {
        "user_id": state.user_id,
        "today": datetime.now().strftime("%Y-%m-%d"),
        "user_text": state.user_text,
        "state_snapshot": state_snapshot,
        "tool_descriptions": get_tool_descriptions(),
        "history_context": history_context,
        "filled_slots": filled_slots_text,
    }
    
    logger_info(f"[AI_V1_4] planner开始规划 | user_id:{state.user_id} | session:{state.metadata.get('session_id', 'unknown')}")
    try:
        result = planner_chain.invoke(payload)
        logger_info(f"[AI_V1_4] planner规划成功 | result:{result.model_dump()}")
        return result
    except Exception as e:
        logger_error(f"[AI_V1_4] planner规划失败 | user_id:{state.user_id} | error:{repr(e)}")
        raise ValueError(f"Agent规划失败: {repr(e)}")
```

## 二、量化指标系统实现

### 2.1 安装依赖

```bash
pip install prometheus-client
```

### 2.2 创建指标配置文件

创建 `app/config/metrics.py`：

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# AI 相关指标
AI_INTENT_RECOGNITION_TOTAL = Counter(
    'ai_intent_recognition_total',
    '意图识别总次数',
    ['intent_type', 'success']
)

AI_TOOL_CALL_TOTAL = Counter(
    'ai_tool_call_total',
    '工具调用总次数',
    ['tool_name', 'status']  # status: success, failure
)

AI_CLARIFICATION_REQUIRED_TOTAL = Counter(
    'ai_clarification_required_total',
    '需要澄清的对话轮次'
)

AI_SLOT_FILLING_TOTAL = Counter(
    'ai_slot_filling_total',
    '槽位填充总次数',
    ['slot_type', 'source']  # slot_type: amount, category, date; source: user, inferred, default
)

AI_RESPONSE_TIME_SECONDS = Histogram(
    'ai_response_time_seconds',
    'AI响应时间分布',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

AI_CONVERSATION_LENGTH = Gauge(
    'ai_conversation_length',
    '当前活跃会话数'
)

# 业务指标
FINANCE_RECORDS_TOTAL = Counter(
    'finance_records_total',
    '记账记录操作总次数',
    ['operation']  # operation: create, read, update, delete
)

USER_AUTH_TOTAL = Counter(
    'user_auth_total',
    '用户认证总次数',
    ['action', 'success']  # action: login, register, logout
)

# 装饰器函数
def record_response_time(func):
    """记录函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            AI_RESPONSE_TIME_SECONDS.observe(elapsed)
            return result
        except Exception:
            elapsed = time.time() - start_time
            AI_RESPONSE_TIME_SECONDS.observe(elapsed)
            raise
    return wrapper

def get_metrics():
    """返回 Prometheus 格式的指标数据"""
    return generate_latest()

# 指标记录辅助函数
def record_intent_recognition(intent_type: str, success: bool = True):
    AI_INTENT_RECOGNITION_TOTAL.labels(
        intent_type=intent_type,
        success='true' if success else 'false'
    ).inc()

def record_tool_call(tool_name: str, success: bool = True):
    AI_TOOL_CALL_TOTAL.labels(
        tool_name=tool_name,
        status='success' if success else 'failure'
    ).inc()

def record_clarification():
    AI_CLARIFICATION_REQUIRED_TOTAL.inc()

def record_slot_filling(slot_type: str, source: str = 'user'):
    AI_SLOT_FILLING_TOTAL.labels(
        slot_type=slot_type,
        source=source
    ).inc()

def record_finance_operation(operation: str):
    FINANCE_RECORDS_TOTAL.labels(operation=operation).inc()

def record_user_auth(action: str, success: bool = True):
    USER_AUTH_TOTAL.labels(
        action=action,
        success='true' if success else 'false'
    ).inc()
```

### 2.3 在 Agent 中添加指标打点

修改 `app/services/ai/v1_4/agent.py`：

```python
from app.config.metrics import (
    record_response_time, record_intent_recognition, 
    record_tool_call, record_clarification, record_slot_filling,
    AI_CONVERSATION_LENGTH
)

@record_response_time
def process_ai_request(user_text: str, user_id: int) -> dict:
    # 增加活跃会话计数
    AI_CONVERSATION_LENGTH.inc()
    
    try:
        # 记录意图识别（这里简化，实际可以从 planner 结果中提取）
        if "记账" in user_text or "花费" in user_text:
            intent_type = "add_record"
        elif "查询" in user_text or "查看" in user_text:
            intent_type = "query_records"
        elif "删除" in user_text:
            intent_type = "delete_record"
        else:
            intent_type = "other"
        
        record_intent_recognition(intent_type=intent_type, success=True)
        
        # ... 原有逻辑 ...
        
        for _ in range(state.max_steps):
            planner_output = plan_next_step(state)
            step = append_planner_step(state, planner_output)
            
            if step.action == "tool_call":
                # 记录工具调用
                record_tool_call(tool_name=step.tool_name or "unknown", success=True)
                
                step.observation = execute_tool(...)
                continue
            
            if step.action == "clarify":
                # 记录澄清需求
                record_clarification()
                # ... 原有逻辑 ...
            
            if step.action == "respond":
                # 如果响应的内容中包含槽位信息，记录槽位填充
                if "金额" in step.message or "amount" in step.message:
                    record_slot_filling(slot_type="amount", source="inferred")
                # ... 原有逻辑 ...
    
    except Exception as e:
        # 记录失败的工具调用
        record_tool_call(tool_name="unknown", success=False)
        raise
    finally:
        # 减少活跃会话计数
        AI_CONVERSATION_LENGTH.dec()
```

修改 `app/services/ai/v1_4/tools/finance_tools.py`：

```python
from app.config.metrics import record_finance_operation

@tool
def add_record_tool(user_id: int, category: str, amount: float, remark: str | None = None) -> Dict[str, Any]:
    try:
        # ... 原有逻辑 ...
        record_finance_operation("create")  # 记录记账操作
        return success_response(...)
    except Exception as e:
        record_finance_operation("create_failed")
        raise

@tool
def delete_record_tool(user_id: int, record_id: int) -> Dict[str, Any]:
    try:
        # ... 原有逻辑 ...
        record_finance_operation("delete")
        return success_response(...)
    except Exception as e:
        record_finance_operation("delete_failed")
        raise
```

### 2.4 在 API 中添加指标端点

修改 `app/main.py`：

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from app.config.metrics import get_metrics

app = FastAPI(...)

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus 指标端点"""
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 2.5 在认证模块添加指标

修改 `app/api/v1/user.py`：

```python
from app.config.metrics import record_user_auth

@router.post("/login")
async def login(...):
    try:
        # ... 原有逻辑 ...
        record_user_auth(action="login", success=True)
        return success_response(...)
    except Exception as e:
        record_user_auth(action="login", success=False)
        raise

@router.post("/register")
async def register(...):
    try:
        # ... 原有逻辑 ...
        record_user_auth(action="register", success=True)
        return success_response(...)
    except Exception as e:
        record_user_auth(action="register", success=False)
        raise
```

## 三、前端界面临时优化

### 3.1 增强 Swagger UI 配置

修改 `app/main.py`：

```python
app = FastAPI(
    title="个人记账助手 API",
    description="""
## 个人记账助手 API 文档
    
基于 FastAPI 的个人财务管理系统，集成通义千问 AI 实现自然语言记账。

### 主要功能
- **用户认证**：注册、登录、JWT 令牌管理
- **记账管理**：添加、查询、删除记账记录
- **AI 记账**：通过自然语言对话完成记账
- **月度统计**：消费分类统计、收支平衡

### AI 能力
- 理解自然语言记账请求
- 多轮对话澄清缺失信息
- 自动识别金额、分类、时间
- 支持图片发票识别（开发中）

### 使用示例
1. 先注册/登录获取 token
2. 在右上角点击 "Authorize" 输入 `Bearer {token}`
3. 在 AI 聊天端点测试自然语言记账
    """,
    version="1.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": -1,
    }
)
```

### 3.2 为 Schema 添加示例

在 `app/schemas/` 下的各个 Pydantic 模型中添加 `example`：

```python
from pydantic import BaseModel, Field

class UserLogin(BaseModel):
    username: str = Field(..., example="zhangsan")
    password: str = Field(..., example="password123")

class RecordAdd(BaseModel):
    category: str = Field(..., example="饮食", description="记账分类：饮食、交通、购物、娱乐、房租、水电、工资、其他")
    amount: float = Field(..., example=-50.0, description="金额：支出为负数，收入为正数")
    remark: Optional[str] = Field(None, example="午餐外卖", description="备注信息")
```

### 3.3 提供 Postman 集合

创建 `docs/postman_collection.json`：

```json
{
  "info": {
    "name": "个人记账助手 API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://127.0.0.1:8000",
      "type": "string"
    },
    {
      "key": "token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "用户认证",
      "item": [
        {
          "name": "用户注册",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "url": "{{base_url}}/api/v1/user/register",
            "body": {
              "mode": "raw",
              "raw": "{\"username\": \"testuser\", \"password\": \"testpass123\", \"email\": \"test@example.com\"}"
            }
          }
        },
        {
          "name": "用户登录",
          "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "url": "{{base_url}}/api/v1/user/login",
            "body": {
              "mode": "raw",
              "raw": "{\"username\": \"testuser\", \"password\": \"testpass123\"}"
            }
          }
        }
      ]
    },
    {
      "name": "AI 记账",
      "item": [
        {
          "name": "自然语言记账",
          "request": {
            "method": "POST",
            "header": [
              {"key": "Content-Type", "value": "application/json"},
              {"key": "Authorization", "value": "Bearer {{token}}"}
            ],
            "url": "{{base_url}}/api/v1/ai/chat",
            "body": {
              "mode": "raw",
              "raw": "{\"message\": \"今天中午吃饭花了50元\"}"
            }
          }
        }
      ]
    }
  ]
}
```

创建 `docs/postman_guide.md`：

```markdown
# Postman 使用指南

## 1. 导入集合
1. 打开 Postman
2. 点击 "Import" → 选择 `postman_collection.json`
3. 导入后可在左侧看到 "个人记账助手 API" 集合

## 2. 设置环境变量
1. 点击右上角眼睛图标 "Environment quick look"
2. 添加新环境 "个人记账助手"
3. 添加变量：
   - `base_url`: `http://127.0.0.1:8000`
   - `token`: (留空，登录后更新)

## 3. 测试流程
1. 先运行 "用户注册" 或 "用户登录"
2. 复制响应中的 `data.access_token`
3. 更新环境变量 `token` 为获取的 token
4. 测试其他需要认证的接口
```

## 四、实施顺序建议

### 第一阶段：AI 记忆混合策略（1-2周）
1. **第1天**：创建数据库表，实现 `long_memory.py`
2. **第2-3天**：修改 `state.py` 和 `agent.py` 集成记忆
3. **第4天**：更新 `planner_prompt.py` 和 `planner.py`
4. **第5天**：测试记忆功能，确保槽位不重复询问

### 第二阶段：量化指标（3-5天）
1. **第1天**：安装 `prometheus-client`，创建 `metrics.py`
2. **第2天**：在 `agent.py` 和 `tools/` 中添加指标打点
3. **第3天**：在 `user.py` 和 `finance.py` 中添加业务指标
4. **第4天**：添加 `/metrics` 端点，测试指标收集
5. **第5天**：（可选）配置 Grafana 仪表盘

### 第三阶段：前端临时优化（2-3天）
1. **第1天**：增强 Swagger UI 配置，添加示例
2. **第2天**：创建 Postman 集合和指南
3. **第3天**：更新 README，提供完整使用说明

## 五、测试验证要点

### AI 记忆功能测试
1. 多轮对话中，已确认的槽位不应重复询问
2. 历史对话能正确加载到上下文
3. 会话结束后，对话历史保存到数据库
4. 跨会话（同一天）能记住已填槽位

### 量化指标测试
1. 访问 `/metrics` 端点查看指标数据
2. 执行 AI 对话，观察指标变化
3. 验证工具调用成功/失败计数准确
4. 检查响应时间分布是否记录

### API 文档测试
1. Swagger UI 能正常访问，示例数据正确
2. Postman 集合能成功导入和执行
3. 所有 API 端点都有详细文档

---

## 六、注意事项

1. **数据库迁移**：如果已部署的生产环境，需要谨慎处理数据库表变更，确保向后兼容。
2. **性能影响**：记忆检索和指标打点可能增加响应时间，需监控性能变化。
3. **Token 消耗**：历史上下文会增加 prompt token 数，需监控 Qwen API 用量。
4. **错误处理**：记忆存储失败不应影响核心功能，要有降级策略。

---

**下一步**：如果您同意此实现方案，我将开始实施第一阶段（AI 记忆混合策略）。请确认是否按此方案执行。