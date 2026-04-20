from app.services.ai.v1_4.schemas import AgentPlannerOutput, AgentState, AgentStep


def create_initial_state(user_text: str, user_id: int, max_steps: int = 3) -> AgentState:
    return AgentState(user_id=user_id, user_text=user_text, max_steps=max_steps)


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
    if not state.steps:
        return "暂无历史步骤。"

    lines: list[str] = []
    for step in state.steps:
        lines.append(
            f"step={step.step_no} | action={step.action} | "
            f"tool={step.tool_name} | message={step.message} | observation={step.observation}"
        )
    return "\n".join(lines)

