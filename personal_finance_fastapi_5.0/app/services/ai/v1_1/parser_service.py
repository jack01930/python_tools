# app/services/ai/parser_service.py

from app.core.llm.client import llm_client
from app.config.prompts import PROMPT_TEMPLATE # 后续配置外置
from app.schemas.ai import AIParseResult
from app.config.logger import info as logger_info, error as logger_error

def build_prompt(user_text: str) -> str:
    """仅负责Prompt模板替换，无其他逻辑"""
    return PROMPT_TEMPLATE.replace("{user_text}", user_text.strip())

def parse_llm_response(content: str, user_text: str) -> AIParseResult:
    """仅负责AI响应的JSON解析、规则校验"""
    try:
        result = AIParseResult.model_validate_json(content)
        # 补充业务规则校验（贴合原有规则）
        valid_categories = ["饮食","工资","交通","购物","娱乐","房租","水电","其他"]
        if result.category not in valid_categories:
            raise ValueError("分类不符合规则")
        if not result.remark or not result.remark.startswith(f"原句：{user_text}"):
            result.remark = f"原句：{user_text}"
        return result
    except Exception as e:
        logger_error(f"[AI] 解析AI返回JSON失败 | 原始内容：{repr(content)} | 错误：{str(e)}")
        raise ValueError(f"AI返回JSON解析失败：{str(e)}")

def call_qwen_api(user_text: str) -> AIParseResult:
    """仅串联：构建Prompt → 调用LLM → 解析响应"""
    prompt = build_prompt(user_text)
    messages = [{"role": "user", "content": prompt}]
    logger_info(f"[AI] 开始调用LLM API | 用户输入：{user_text}")
    
    ai_response = llm_client.chat_completions_create(
        messages=messages,
        temperature=0.1,
        max_tokens=200
    )
    ai_content = ai_response["choices"][0]["message"]["content"].strip()
    logger_info(f"[AI] 原始返回内容: {repr(ai_content)}")
    
    return parse_llm_response(ai_content, user_text)