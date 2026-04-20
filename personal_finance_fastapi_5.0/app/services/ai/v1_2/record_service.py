#app/services/ai/v1_2/record_service.py
from typing import Dict, Any

from app.services.ai.v1_2.retry import invoke_record_chain
from app.utils.ai.ai_utils import add_record_tool
from app.config.logger import info as logger_info ,error as logger_error ,warn as logger_warn

def ai_auto_record(user_text: str, user_id: int) -> Dict[str, Any]:
    logger_info(f"[AI解析] 开始解析用户输入 | user_id:{user_id} | 输入文本：{user_text}")
    cmd=invoke_record_chain(user_text)
    logger_info(f"[AI解析] 解析结果：{cmd.model_dump()}")
    if cmd.intent!="add_record":
        logger_error(f"[AI解析] 无法识别的意图：{cmd.intent} | input:{user_text}")
        raise ValueError(f"无法识别的意图：{cmd.intent}，目前仅支持add_record")
    try:
        result=add_record_tool.invoke({
            "user_id":user_id,
            "category":cmd.category,
            "amount":cmd.amount,
            "remark":cmd.remark,
        })
        logger_info(f"[AI解析] 记录成功 | user_id:{user_id} | category:{cmd.category} | amount:{cmd.amount}")
        return {"ai_parse_result":cmd.model_dump(),
                "record_detail":result
                }
    except Exception as e:
        logger_error(f"[AI解析] 记录失败 | user_id:{user_id} | category:{cmd.category} | amount:{cmd.amount} | {e}")
        raise ValueError(f"记录失败，请检查输入文本是否正确，错误信息为：{e}")