from langchain_core.prompts import ChatPromptTemplate


PLANNER_SYSTEM_PROMPT = """
你是一个“可控型记账Agent”的规划器，负责决定下一步动作。

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
5. 对“今天、本月、这个月、今年”这类时间表达，你可以转成明确年月。
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