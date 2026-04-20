import time
from langchain_core.output_parsers import PydanticOutputParser

from app.schemas.ai import AIParseResult
from app.services.ai.v1_3.llm_client import create_llm_client
from app.services.ai.v1_3.prompts import build_prompt
from app.config.logger import info as logger_info, warn as logger_warn, error as logger_error

"""

"""

#创建解析器 ： 让LLM返回AIParseResult格式的JSON字符串
parser = PydanticOutputParser(pydantic_object=AIParseResult)

#创建LLM客户端
llm = create_llm_client()

#使用parser提供的get_format_instructions()
prompt = build_prompt(parser.get_format_instructions())

record_parser_chain = prompt | llm | parser

def parse_user_intent(user_text:str,retry_times: int =2):
    """
    -user_text: 用户输入文本，包含用户意图和相关信息
    -retry_times: 重试次数，默认为2
    """
    logger_info(f"[AI解析] LLM解析 | 用户输入文本:{user_text} | 重试次数:{retry_times}")
    last_error = None
    for i in range(1,retry_times+1):
        try:
            logger_info(f"[AI解析] LLM解析 | 第{i}次 | i输入:{user_text}")
            result = record_parser_chain.invoke({"user_text":user_text})
            logger_info(f"[AI解析] LLM解析 | 第{i}次 | 结果: {result}")
            return result
        except Exception as e:
            logger_error(f"[AI解析] 第{i}次解析失败 | 输入:{user_text} | 信息:{repr(e)}")
            time.sleep(1)
            last_error = e
            # 并不需要continue，除非在except里面就raise了
    logger_error(f"[AI解析] LLM解析失败 | 解析总次数:{retry_times}次 | 输入:{user_text} | 最后一次信息:{last_error}")
    raise ValueError(f"[AI解析] 结构化解析全部失败，请检查输入文本是否正确，错误信息为：{last_error}")
