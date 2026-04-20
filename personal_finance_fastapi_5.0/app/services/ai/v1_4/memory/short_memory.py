from app.services.ai.v1_4.schemas import AgentState
from app.services.ai.v1_4.state import build_state_snapshot


def build_short_memory(state: AgentState) -> str:
    if not state.history and not state.steps:
        return "当前没有历史上下文。"
    return build_state_snapshot(state)

