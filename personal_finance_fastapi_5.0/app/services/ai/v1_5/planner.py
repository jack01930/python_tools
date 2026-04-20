from datetime import datetime

from app.config.logger import error as logger_error, info as logger_info
from app.core.llm.client import create_llm_client
from app.services.ai.v1_5.memory.short_memory import build_short_memory
from app.services.ai.v1_5.parser.action_parser import planner_output_parser
from app.services.ai.v1_5.prompts.planner_prompt import build_planner_prompt
from app.services.ai.v1_5.schemas import AgentPlannerOutput, AgentState
from app.services.ai.v1_5.tool_registry import get_tool_descriptions

llm = create_llm_client()
planner_prompt = build_planner_prompt(planner_output_parser.get_format_instructions())
planner_chain = planner_prompt | llm | planner_output_parser


def plan_next_step(state: AgentState) -> AgentPlannerOutput:
    state_snapshot = build_short_memory(state)

    # 获取历史上下文和已填槽位
    history_context = state.metadata.get("history_context", "无历史对话。") if state.metadata else "无历史对话。"
    filled_slots = state.metadata.get("filled_slots", {}) if state.metadata else {}

    # 格式化已填槽位文本
    filled_slots_text = "\n".join([f"- {k}: {v}" for k, v in filled_slots.items()]) if filled_slots else "无已确认信息"

    payload = {
        "user_id": state.user_id,
        "today": datetime.now().strftime("%Y-%m-%d"),
        "user_text": state.user_text,
        "state_snapshot": state_snapshot,
        "tool_descriptions": get_tool_descriptions(),
        "history_context": history_context,
        "filled_slots": filled_slots_text,
    }
    logger_info(f"[AI_V1_5] planner开始规划 | user_id:{state.user_id} | session:{state.metadata.get('session_id', 'unknown')}")
    try:
        result = planner_chain.invoke(payload)
        logger_info(f"[AI_V1_5] planner规划成功 | result:{result.model_dump()}")
        return result
    except Exception as e:
        logger_error(f"[AI_V1_5] planner规划失败 | user_id:{state.user_id} | error:{repr(e)}")
        raise ValueError(f"Agent规划失败: {repr(e)}")