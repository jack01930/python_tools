from langchain_core.prompts import ChatPromptTemplate


CLARIFY_SYSTEM_PROMPT = """
你是记账Agent的对话润色器。
请把内部的澄清原因，改写成一句自然、简洁、礼貌的追问。
不要输出多余解释，只输出最终给用户的话。
"""


def build_clarify_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", CLARIFY_SYSTEM_PROMPT),
            (
                "human",
                "用户原始输入: {user_text}\n"
                "内部澄清原因: {planner_message}",
            ),
        ]
    )

