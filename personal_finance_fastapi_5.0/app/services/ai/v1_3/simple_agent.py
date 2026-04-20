from typing import Any, Dict

from app.config.logger import error as logger_error, info as logger_info
from app.services.ai.v1_3.ai_finance_service import (
    handle_add_record,
    handle_delete_record,
    handle_other_intent,
    handle_query_records,
)
from app.services.ai.v1_3.ai_utils import add_record_tool, delete_record_tool, query_records_tool
from app.services.ai.v1_3.parser import parse_user_intent

def process_ai_request(
    user_text: str,
    user_id: int,
) -> Dict[str, Any]:
    """
    处理用户请求
    :param user_text: 用户输入的文本
    :param user_id: 用户ID
    """
    logger_info(f"[AI_AGENT] 开始处理用户请求 | user_id:{user_id} | user_text:{user_text}")
    try:
        cmd = parse_user_intent(user_text)
        logger_info(f"[AI_AGENT] 解析用户请求成功 | 结果:{cmd.model_dump()}")
        if cmd.intent == "add_record":
            result = handle_add_record(cmd, user_id, add_record_tool)
        elif cmd.intent == "query_records":
            result = handle_query_records(cmd, user_id, query_records_tool)
        elif cmd.intent == "delete_record":
            result = handle_delete_record(cmd, user_id, delete_record_tool)
        elif cmd.intent == "other":
            result = handle_other_intent(cmd)
        else:
            raise ValueError(f"[AI_AGENT] 未知的用户意图 | user_id:{user_id} | intent:{cmd.intent}")
        logger_info(f"[AI_AGENT] 处理用户请求成功 | user_id:{user_id} | intent:{cmd.intent} | result:{result}")
        return result
    except Exception as e:
        logger_error(f"[AI_AGENT] 处理用户请求失败 | user_id:{user_id} | user_text:{user_text} | error:{repr(e)}")
        raise


def ai_auto_record(user_text: str, user_id: int) -> Dict[str, Any]:
    """
    兼容旧入口名称，内部统一走 v1_3 的多意图处理链路。
    """
    return process_ai_request(user_text=user_text, user_id=user_id)
