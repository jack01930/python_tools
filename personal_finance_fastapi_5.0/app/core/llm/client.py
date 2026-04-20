import requests
from typing import Dict, Any

from app.config.settings import settings
from app.config.logger import error as logger_error


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