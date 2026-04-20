from langchain_core.output_parsers import PydanticOutputParser

from app.services.ai.v1_4.schemas import AgentPlannerOutput


planner_output_parser = PydanticOutputParser(pydantic_object=AgentPlannerOutput)

