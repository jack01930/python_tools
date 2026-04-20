#app/services/ai/v1_2/retry.py
import time

from app.services.ai.v1_2.chains import record_parser_chain
from app.config.logger import error as logger_error ,info as logger_info

def invoke_record_chain(user_text: str, retry_times: int = 1):
    logger_info(f"[AI解析] LLM解析 | retry_times:{retry_times} | input:{user_text}")
    last_error = None

    for _ in range(retry_times+1):
        try:
            logger_info(f"[AI解析] LLM解析 | retry_times:{_+1}次 | input:{user_text}")
            result =record_parser_chain.invoke({"user_text": user_text})
            logger_info(f"[AI解析] LLM解析 | retry_times:{_+1}次 | 结果: {result}")
            return result
        except Exception as e:
            logger_error(f"[AI解析] 第{_+1}次结构化解析失败 | input:{user_text} | 信息：{e}")
            time.sleep(1)
            last_error = e
    logger_error(f"[AI解析] LLM解析全部失败 | 总次数：{_+1}次 | input:{user_text} | 信息：{last_error}")
    raise ValueError(f"[AI解析] 结构化解析失败，请检查输入文本是否正确，错误信息为：{last_error}")
