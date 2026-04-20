from langchain_core.output_parsers import PydanticOutputParser

from app.services.ai.v1_4.schemas import AgentResponse


agent_response_parser = PydanticOutputParser(pydantic_object=AgentResponse)

