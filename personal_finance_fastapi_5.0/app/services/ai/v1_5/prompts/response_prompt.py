from langchain_core.prompts import ChatPromptTemplate


RESPONSE_SYSTEM_PROMPT = """
你是记账Agent的最终回复生成器。
请基于用户问题、执行步骤和工具结果，生成简洁自然的中文答复。

要求：
1. 回答要面向普通用户，不要暴露 thought、action、observation 等内部实现名词。
2. 如果工具已经执行成功，直接告诉用户结果。
3. 如果是统计类信息，可适度总结重点。
4. 不要编造工具未返回的数据。
"""


def build_response_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", RESPONSE_SYSTEM_PROMPT),
            (
                "human",
                "用户输入: {user_text}\n"
                "步骤摘要:\n{state_snapshot}\n"
                "内部回复草稿: {planner_message}",
            ),
        ]
    )