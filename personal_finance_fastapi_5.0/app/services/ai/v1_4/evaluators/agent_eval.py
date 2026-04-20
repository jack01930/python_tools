from app.services.ai.v1_4.schemas import AgentState


EVAL_CASES = [
    {"text": "今天午饭18元", "expected": "add_record"},
    {"text": "查询2026年4月账单", "expected": "query_records"},
    {"text": "帮我删掉ID为8的记录", "expected": "delete_record"},
    {"text": "帮我总结这个月的花销", "expected": "summarize_month"},
    {"text": "删掉昨天那条", "expected": "clarify"},
]


def build_eval_snapshot(state: AgentState) -> dict:
    return {
        "user_text": state.user_text,
        "steps_count": len(state.steps),
        "last_step": state.steps[-1].model_dump() if state.steps else None,
    }

