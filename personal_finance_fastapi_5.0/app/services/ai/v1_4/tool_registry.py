from langchain_core.tools import BaseTool

from app.services.ai.v1_4.tools.finance_tools import (
    add_record_tool,
    delete_record_tool,
    query_records_tool,
)
from app.services.ai.v1_4.tools.summary_tools import summarize_month_tool


TOOL_REGISTRY: dict[str, BaseTool] = {
    "add_record": add_record_tool,
    "query_records": query_records_tool,
    "delete_record": delete_record_tool,
    "summarize_month": summarize_month_tool,
}


def get_tool(tool_name: str) -> BaseTool | None:
    return TOOL_REGISTRY.get(tool_name)


def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())


def get_tool_descriptions() -> str:
    descriptions: list[str] = []
    for name, tool in TOOL_REGISTRY.items():
        descriptions.append(f"- {name}: {tool.description}")
    return "\n".join(descriptions)

