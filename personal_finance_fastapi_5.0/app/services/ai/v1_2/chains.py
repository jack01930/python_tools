#app/services/ai/v1_2/chains.py
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from app.schemas.ai import AIParseResult
from app.config.prompts import build_prompt
from app.config.settings import settings

parser = PydanticOutputParser(pydantic_object=AIParseResult)

llm=ChatOpenAI(
    model=settings.QWEN_MODEL,
    api_key=settings.QWEN_API_KEY,
    base_url=settings.QWEN_BASE_URL,
    temperature=0.1,
    max_tokens=200
)

prompt=build_prompt(parser.get_format_instructions())

record_parser_chain = prompt | llm | parser
