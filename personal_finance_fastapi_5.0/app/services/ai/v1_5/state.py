from app.services.ai.v1_5.memory import create_long_memory
from app.services.ai.v1_5.schemas import AgentPlannerOutput, AgentState, AgentStep


def create_initial_state(
    user_text: str,
    user_id: int,
    max_steps: int = 3,
    session_id: str = None
) -> AgentState:
    """创建初始状态，加载历史记忆"""
    # 创建长期记忆实例
    long_memory = create_long_memory(user_id, session_id)

    # 获取当前会话已填充槽位
    filled_slots = long_memory.get_session_slots()

    # 获取历史上下文（用于 planner）
    history_context = long_memory.generate_context(max_recent=3, max_total=10)

    # 创建状态对象
    state = AgentState(
        user_id=user_id,
        user_text=user_text,
        max_steps=max_steps,
        history=[],  # 保留字段，可用于存储短期上下文
    )

    # 将槽位信息和历史上下文存储在 metadata 中
    state.metadata = {
        "filled_slots": filled_slots,
        "session_id": long_memory.session_id,
        "history_context": history_context
    }

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
    """构建状态快照，现在包含历史上下文和已填槽位"""
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