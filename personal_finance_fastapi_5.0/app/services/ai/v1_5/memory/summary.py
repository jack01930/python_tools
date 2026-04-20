import json
from typing import List, Dict, Any

from app.config.logger import error as logger_error
from app.core.llm.client import create_llm_client


def format_conversations(conversations: List[Dict[str, Any]]) -> str:
    """格式化对话历史为文本"""
    lines = []
    for conv in conversations:
        lines.append(f"{conv['role']}: {conv['content']}")
        if conv.get('slots_filled'):
            lines.append(f"  已填槽位: {json.dumps(conv['slots_filled'], ensure_ascii=False)}")
    return "\n".join(lines)


def generate_history_summary(
    conversations: List[Dict[str, Any]],
    llm_client=None
) -> str:
    """
    使用 LLM 生成历史摘要

    策略：
    1. 如果历史为空，返回默认文本
    2. 如果 LLM 可用，调用生成摘要
    3. 如果 LLM 失败，返回简单统计
    """
    if not conversations:
        return "无历史对话。"

    # 构建摘要 prompt
    history_text = format_conversations(conversations)
    prompt = f"""
请将以下记账对话历史总结为简洁的摘要，保留关键信息：
- 用户的主要需求
- 已确认的记账参数（金额、分类、时间等）
- 已完成的记账操作

对话历史：
{history_text}

摘要：
"""

    # 尝试使用 LLM 生成摘要
    if llm_client is None:
        try:
            llm_client = create_llm_client()
        except Exception:
            llm_client = None

    if llm_client:
        try:
            response = llm_client.invoke(prompt)
            # 处理不同类型的响应
            if hasattr(response, 'content'):
                summary = str(response.content).strip()
            else:
                summary = str(response).strip()
            if summary:
                return summary
        except Exception as e:
            logger_error(f"[LongMemory.Summary] LLM摘要生成失败 | error:{repr(e)}")

    # LLM 失败时返回简单摘要
    return f"共 {len(conversations)} 轮较早对话，涉及记账操作。"