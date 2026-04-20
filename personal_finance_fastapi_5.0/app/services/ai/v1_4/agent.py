from langchain_core.output_parsers import StrOutputParser

from app.config.logger import error as logger_error, info as logger_info
from app.schemas.response import success_response
from app.core.llm.client import create_llm_client
from app.services.ai.v1_4.executor import execute_tool
from app.services.ai.v1_4.planner import plan_next_step
from app.services.ai.v1_4.prompts.clarify_prompt import build_clarify_prompt
from app.services.ai.v1_4.prompts.response_prompt import build_response_prompt
from app.services.ai.v1_4.state import append_planner_step, build_state_snapshot, create_initial_state

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


def process_ai_request(user_text: str, user_id: int) -> dict:
    state = create_initial_state(user_text=user_text, user_id=user_id, max_steps=3)
    logger_info(f"[AI_V1_4] Agent开始执行 | user_id:{user_id} | user_text:{user_text}")

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
                continue

            if step.action == "clarify":
                question = _render_clarify_question(user_text=user_text, planner_message=step.message or "")
                return success_response(
                    msg="需要补充信息",
                    data={
                        "type": "clarify",
                        "question": question,
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
                return success_response(
                    msg="Agent处理成功",
                    data={
                        "type": "final",
                        "answer": reply,
                        "steps": [item.model_dump() for item in state.steps],
                    },
                )

            if step.action == "fail":
                raise ValueError(step.message or "Agent执行失败")

        raise ValueError("超过最大推理步数，Agent未能完成任务")
    except Exception as e:
        logger_error(f"[AI_V1_4] Agent执行失败 | user_id:{user_id} | user_text:{user_text} | error:{repr(e)}")
        raise

