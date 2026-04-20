from typing import Any, Dict

from app.config.logger import error as logger_error, info as logger_info
from app.services.ai.v1_5.tool_registry import get_tool


def execute_tool(tool_name: str, tool_input: dict[str, Any], user_id: int) -> Dict[str, Any]:
    tool = get_tool(tool_name)
    if tool is None:
        raise ValueError(f"未知工具: {tool_name}")

    final_tool_input = dict(tool_input)
    final_tool_input.setdefault("user_id", user_id)
    logger_info(f"[AI_V1_5] executor执行工具 | tool:{tool_name} | input:{final_tool_input}")

    try:
        result = tool.invoke(final_tool_input)
        logger_info(f"[AI_V1_5] executor执行成功 | tool:{tool_name} | result:{result}")
        return result
    except Exception as e:
        logger_error(f"[AI_V1_5] executor执行失败 | tool:{tool_name} | input:{final_tool_input} | error:{repr(e)}")
        raise ValueError(f"工具执行失败: {repr(e)}")