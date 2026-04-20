from typing import Any, Dict

from app.services.ai.parser_service import call_qwen_api
from app.services.finance.finance_service import add_finance_record
from app.schemas.finance import RecordAddInternal
from app.utils.finance_utils import get_today_max_serial_num
from app.config.logger import error as logger_error, info as logger_info

def ai_auto_record(user_text: str, user_id: int) -> Dict[str, Any]:
    """仅负责：AI解析结果 → 生成记账参数 → 调用财务服务入库"""
    try:
        # 1. 调用AI解析服务
        ai_result = call_qwen_api(user_text)
        logger_info(f"[AI记账] 解析结果 | 分类：{ai_result.category} | 金额：{ai_result.amount}")
        
        # 2. 生成记账参数（替换原有直接调用CRUD的逻辑）
        serial_num = get_today_max_serial_num(user_id) + 1
        record_internal = RecordAddInternal(
            serial_num=serial_num,
            amount=float(ai_result.amount),
            category=ai_result.category,
            remark=ai_result.remark
        )
        
        # 3. 调用财务服务入库（贴合原有逻辑）
        record_detail = add_finance_record(record_internal, user_id)
        logger_info(f"[AI记账] 记账成功 | user_id:{user_id} | request_id:{record_internal.request_id}")
        
        return {
            "ai_parse_result": ai_result.model_dump(),
            "record_detail": record_detail
        }
    except Exception as e:
        logger_error(f"[AI记账] 失败 | user_id:{user_id} | 信息：{str(e)}")
        raise e