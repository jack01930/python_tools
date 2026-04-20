from datetime import datetime
from langchain_core.output_parsers import StrOutputParser

from app.config.logger import error as logger_error, info as logger_info
from app.schemas.response import success_response
from app.core.llm.client import create_llm_client
from app.services.ai.v1_5.executor import execute_tool
from app.services.ai.v1_5.planner import plan_next_step
from app.services.ai.v1_5.prompts.clarify_prompt import build_clarify_prompt
from app.services.ai.v1_5.prompts.response_prompt import build_response_prompt
from app.services.ai.v1_5.state import append_planner_step, build_state_snapshot, create_initial_state
from app.services.ai.v1_5.memory import create_long_memory

llm = create_llm_client()
clarify_chain = build_clarify_prompt() | llm | StrOutputParser()
response_chain = build_response_prompt() | llm | StrOutputParser()


def _render_clarify_question(user_text: str, planner_message: str) -> str:
    try:
        return clarify_chain.invoke(
            {
                "user_text": user_text,
                "planner_message": planner_message,
            }
        )
    except Exception:
        return planner_message


def _render_final_reply(user_text: str, state_snapshot: str, planner_message: str) -> str:
    try:
        return response_chain.invoke(
            {
                "user_text": user_text,
                "state_snapshot": state_snapshot,
                "planner_message": planner_message,
            }
        )
    except Exception:
        return planner_message


def process_ai_request(user_text: str, user_id: int, session_id: str = None) -> dict:
    # 创建长期记忆实例
    long_memory = create_long_memory(user_id, session_id)

    # 保存用户输入到历史
    long_memory.save_message(
        role="user",
        content=user_text,
        metadata={"request_time": datetime.now().isoformat()}
    )

    # 创建初始状态（会自动加载历史槽位和上下文）
    state = create_initial_state(
        user_text=user_text,
        user_id=user_id,
        max_steps=3,
        session_id=long_memory.session_id
    )

    logger_info(f"[AI_V1_5] Agent开始执行 | user_id:{user_id} | session:{long_memory.session_id} | user_text:{user_text}")

    try:
        for _ in range(state.max_steps):
            planner_output = plan_next_step(state)
            step = append_planner_step(state, planner_output)

            if step.action == "tool_call":
                step.observation = execute_tool(
                    tool_name=step.tool_name or "",
                    tool_input=step.tool_input,
                    user_id=user_id,
                )

                # 检查工具调用是否填充了槽位，如果是则保存
                if step.tool_name and step.tool_input:
                    long_memory.update_slots_from_tool_call(step.tool_name, step.tool_input)

                continue

            if step.action == "clarify":
                question = _render_clarify_question(user_text=user_text, planner_message=step.message or "")

                # 保存 AI 澄清问题到历史
                long_memory.save_message(
                    role="assistant",
                    content=question,
                    metadata={"action": "clarify"}
                )

                return success_response(
                    msg="需要补充信息",
                    data={
                        "type": "clarify",
                        "question": question,
                        "session_id": long_memory.session_id,
                        "steps": [item.model_dump() for item in state.steps],
                    },
                )

            if step.action == "respond":
                state_snapshot = build_state_snapshot(state)
                reply = _render_final_reply(
                    user_text=user_text,
                    state_snapshot=state_snapshot,
                    planner_message=step.message or "",
                )

                # 保存 AI 回复到历史
                long_memory.save_message(
                    role="assistant",
                    content=reply,
                    metadata={"action": "respond"}
                )

                return success_response(
                    msg="Agent处理成功",
                    data={
                        "type": "final",
                        "answer": reply,
                        "session_id": long_memory.session_id,
                        "steps": [item.model_dump() for item in state.steps],
                    },
                )

            if step.action == "fail":
                raise ValueError(step.message or "Agent执行失败")

        raise ValueError("超过最大推理步数，Agent未能完成任务")
    except Exception as e:
        logger_error(f"[AI_V1_5] Agent执行失败 | user_id:{user_id} | session:{long_memory.session_id} | error:{repr(e)}")
        raise