from typing import Any, Dict

from app.config.logger import error as logger_error, info as logger_info, warn as logger_warn
from app.schemas.ai import AIParseResult


def handle_add_record(
    cmd: AIParseResult,
    user_id: int,
    add_record_tool,
) -> Dict[str, Any]:
    """
    处理记账指令
    :param cmd: 解析后的指令
    :param user_id: 用户ID
    :param add_record_tool: 记账工具
    """
    if cmd.amount is None or cmd.category is None:
        logger_warn(f"[AI_HANDLER] 记账指令缺少必要信息 | user_id:{user_id} | cmd:{cmd}")
        raise ValueError("记账指令必须包含金额和分类")
    try:
        result = add_record_tool.invoke(
            {
                "user_id": user_id,
                "amount": cmd.amount,
                "category": cmd.category,
                "remark": cmd.remark,
            }
        )
        logger_info(f"[AI_HANDLER] 记账指令成功 | user_id:{user_id} | category:{cmd.category} | amount:{cmd.amount} | remark:{cmd.remark}")
        return result
    except Exception as e:
        logger_error(f"[AI_HANDLER] 记账指令失败 | user_id:{user_id} | category:{cmd.category} | amount:{cmd.amount} | remark:{cmd.remark} | error:{repr(e)}")
        raise ValueError(f"记账指令失败:{repr(e)}")


def handle_query_records(
    cmd: AIParseResult,
    user_id: int,
    query_records_tool,
) -> Dict[str, Any]:
    """
    处理查询指令
    :param cmd: 解析后的指令
    :param user_id: 用户ID
    :param query_records_tool: 查询工具
    """
    if cmd.year is None or cmd.month is None:
        logger_warn(f"[AI_HANDLER] 查询指令缺少必要信息 | user_id:{user_id} | cmd:{cmd}")
        raise ValueError("查询指令必须包含年份和月份")
    try:
        result = query_records_tool.invoke(
            {
                "user_id": user_id,
                "year": cmd.year,
                "month": cmd.month,
            }
        )
        logger_info(f"[AI_HANDLER] 查询指令成功 | user_id:{user_id} | year:{cmd.year} | month:{cmd.month} | records:{result}")
        return result
    except Exception as e:
        logger_error(f"[AI_HANDLER] 查询指令失败 | user_id:{user_id} | year:{cmd.year} | month:{cmd.month} | error:{repr(e)}")
        raise ValueError(f"查询指令失败:{repr(e)}")
    
def handle_delete_record(
    cmd: AIParseResult,
    user_id: int,
    delete_record_tool,
) -> Dict[str, Any]:
    """
    处理删除指令
    :param cmd: 解析后的指令
    :param user_id: 用户ID
    :param delete_record_tool: 删除工具
    """
    if cmd.record_id is None:
        logger_warn(f"[AI_HANDLER] 删除指令缺少必要信息 | user_id:{user_id} | cmd:{cmd}")
        raise ValueError("删除指令必须包含记录ID")
    try:
        result = delete_record_tool.invoke(
            {
                "user_id": user_id,
                "record_id": cmd.record_id,
            }
        )
        logger_info(f"[AI_HANDLER] 删除指令成功 | user_id:{user_id} | record_id:{cmd.record_id}")
        return result
    except Exception as e:
        logger_error(f"[AI_HANDLER] 删除指令失败 | user_id:{user_id} | record_id:{cmd.record_id} | error:{repr(e)}")
        raise ValueError(f"删除指令失败:{repr(e)}")

def handle_other_intent(cmd: AIParseResult) -> Dict[str, Any]:
    """
    处理其他意图
    :param cmd: 解析后的指令
    """
    logger_info(f"[AI_HANDLER] 其他意图 | cmd:{cmd}")
    return {
        "code": 200,
        "msg": "未识别的其他意图",
        "data": {"intent": cmd.intent},
    }
