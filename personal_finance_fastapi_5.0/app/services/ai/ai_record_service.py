#app/services/ai/ai_record_service.py
import requests
import json
import re
from datetime import datetime
from typing import Dict,Any,Optional
from langchain_openai import ChatOpenAI

from app.config.settings import settings
from app.config.logger import info as logger_info, warn as logger_warn, error as logger_error
from app.schemas.ai import AIParseResult
from app.schemas.finance import RecordAddInternal
from app.services.finance.finance_service import add_finance_record
from app.crud.finance import get_today_max_serial_num


PROMPT_TEMPLATE = """
你是一个专业的记账助手，仅返回严格符合以下所有规则的JSON字符串，无任何额外内容（解释/空格/换行/注释/转义字符）。
### 强制优先级：JSON格式正确性 > 内容完整性
### 核心规则（违反任意一条则任务失败）：
1. 输出格式：仅返回JSON字符串，字段仅包含category（字符串）、amount（数字）、remark（字符串），无其他字段/逗号/括号；
2. 金额规则：支出为负数（如花20元→amount=-20），收入为正数（如赚100元→amount=100），仅保留数字（无单位/中文）；
3. 分类规则：仅使用【饮食/工资/交通/购物/娱乐/房租/水电/其他】中的一个，无法识别则填“其他”；
4. 备注规则：必须包含用户原句，格式为「原句：用户输入内容」，无多余空格/换行/全角符号，示例："remark":"原句：花20元吃面"；
5. 编码规则：仅使用UTF-8编码的半角字符，禁止返回全角符号（，。：）、特殊表情、不可见字符、乱码；
6. 格式约束：JSON字符串无前置/后置空格、无换行、无缩进、无冒号前后空格，一行完成，示例：{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}。
7. 严禁使用 ```json 或任何代码块包裹

### 用户输入：
{user_text}

### 错误示例（禁止返回此类内容）：
- 错误1（有空格/缩进）：{{"category" : "饮食", "amount" : -20, "remark" : "原句：花20元吃面"}}
- 错误2（全角符号）：{{"category"："饮食","amount"：-20,"remark"："原句：花20元吃面"}}
- 错误3（多余内容）：解析结果：{{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}}
- 错误4（占位符未替换）：{{"category":"饮食","amount":-20,"remark":"原句：{user_text}"}}

### 正确示例（仅参考格式，需替换为真实解析结果）：
{"category":"饮食","amount":-20,"remark":"原句：花20元吃面"}
"""

class OpenAICompatibleLLMClient:
    def __init__(
            self,
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            model=settings.QWEN_MODEL
            ):
        self.api_key=api_key
        self.base_url=base_url
        self.model=model
        self.headers={
            "Content-Type":"application/json", #说明这次发送的请求体pyload是json格式
            "Authorization":f"Bearer {self.api_key}"
        }
    
    def chat_completions_create(
            self,
            messages:list[dict],
            temperature:float=0.1,
            max_tokens:int=200
            )->Dict[str,Any]:
        payload={
            "model":self.model,
            "messages":messages,
            "temperature":temperature,
            "max_tokens":max_tokens
            }
        try:
            response=requests.post(
                url=f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger_error(f"[OpenAI兼容客户端] API调用失败 | 信息：{str(e)}")
            raise ValueError(f"LLM服务调用失败 | 信息：{str(e)}")
        
llm_client=OpenAICompatibleLLMClient()


def call_qwen_api(
        user_text:str
)->AIParseResult:
    # 这里不能直接用 .format()，因为 prompt 里的 JSON 示例本身包含大量 { }。
    # 直接替换占位符可以避免 Python 把示例里的 {category} 之类内容当成格式化参数。
    prompt = PROMPT_TEMPLATE.replace("{user_text}", user_text)
    messages=[{"role":"user","content":prompt}]
    try:
        logger_info(f"[AI] 开始调用LLM API(OpenAI兼容默诵) | 用户输入：{user_text}")
        ai_response=llm_client.chat_completions_create(
            messages=messages,
            temperature=0.1,
            max_tokens=200
        )
        logger_info(f"[AI] API返回结果: {ai_response}")

        ai_content=ai_response["choices"][0]["message"]["content"].strip()
        logger_info(f"[AI] 原始返回内容: {repr(ai_content)}")
        # ai_content=clean_llm_json(ai_content)
        try:
            parse_result=AIParseResult.model_validate_json(ai_content)
            logger_info(f"[AI] JSON解析成功: {parse_result}")
        except Exception as e:
            logger_error(f"[AI] 解析AI返回JSON失败 | 原始内容：{repr(ai_content)} | 错误：{str(e)}")
            raise ValueError(f"AI返回JSON解析失败：{str(e)}")
        if not parse_result.remark:
            parse_result.remark=f"原句：{user_text}"
        return parse_result
    except Exception as e:
        logger_error(f"[AI] AI处理响应异常  | 错误：{str(e)}")
        raise ValueError(f"AI处理异常：{str(e)}")
    
def ai_auto_record(
        user_text:str,
        user_id:int
)->Dict[str,Any]:
    try:
        ai_result=call_qwen_api(user_text)
        logger_info(f"[AI记账] 解析结果 | 分类：{ai_result.category} | 金额：{ai_result.amount} | 备注：{ai_result.remark}")

        serial_num=get_today_max_serial_num(user_id)+1
        today=datetime.now().strftime("%Y-%m-%d")
        request_id=f'{today}-{serial_num:03d}'
        logger_info(f"[AI记账] 生成request_id | {request_id} | serial_num:{serial_num} ")

        record_internal=RecordAddInternal(
            # request_id=request_id,
            serial_num=serial_num,
            amount=float(ai_result.amount),  # 确保amount是浮点数类型
            category=ai_result.category,
            remark=ai_result.remark
        )
        record_detail=add_finance_record(record_internal,user_id)
        logger_info(f"[AI记账] 记账成功 | user_id:{user_id} | request_id:{request_id}")
        return {
            "ai_parse_result":ai_result.model_dump(),
            "record_detail":record_detail
        }
    except Exception as e:
        logger_error(f"[AI记账] 失败 | user_id:{user_id} | 信息：{str(e)}")
        raise e
    
# def clean_llm_json(content: str) -> str:
#     content = content.strip()

#     # 1️⃣ 去掉 ```json ``` 包裹
#     if content.startswith("```"):
#         content = re.sub(r"^```[a-zA-Z]*", "", content)
#         content = content.replace("```", "").strip()

#     # 2️⃣ 去掉“解析结果：”等前缀
#     if "{" in content:
#         content = content[content.find("{"):]

#     # 3️⃣ 处理被整体包成字符串的情况
#     if content.startswith('"') and content.endswith('"'):
#         content = content[1:-1]
#         content = content.replace('\\"', '"')

#     return content

def get_langchain_llm():
    return ChatOpenAI(
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        model_name=settings.QWEN_MODEL,
        temperature=0.1
    )
