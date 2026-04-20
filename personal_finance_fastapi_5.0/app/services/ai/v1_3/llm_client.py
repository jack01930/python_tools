from langchain_openai import ChatOpenAI

from app.config.settings import settings

def create_llm_client():
    """
    创建LLM(model=qwen-turbo)客户端实例
    """
    llm=ChatOpenAI(
        model=settings.QWEN_MODEL,
        api_key=settings.QWEN_API_KEY,
        base_url=settings.QWEN_BASE_URL,
        temperature=0.1,
        max_tokens=500
    )

    return llm