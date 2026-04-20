from typing import Any, Dict

from langchain_core.tools import tool

from app.config.logger import error as logger_error, info as logger_info
from app.schemas.response import success_response
from app.services.finance.finance_service import get_finance_records


@tool
def summarize_month_tool(
    user_id: int,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """
    查询某年某月的统计摘要。
    适用于"这个月花了多少""帮我总结本月收支"这类问题。
    入参要求：
    - year: 年份（必填）
    - month: 月份（1-12）（必填）
    返回：包含统计信息和所有记录的标准响应（最多1000条）
    """
    try:
        result = get_finance_records(
            year=year,
            month=month,
            page=1,
            page_size=1000,  # 返回所有记录，假设月度记录不超过1000条
            user_id=user_id,
        )
        preview_records = result["detail"]  # 不再切片，返回所有记录
        logger_info(f"[AI_TOOL] 月度总结成功 | user_id:{user_id} | year:{year} | month:{month}")
        return success_response(
            msg=f"{year}年{month}月账单总结成功",
            data={
                "statistics": result["statistics"],
                "preview_records": preview_records,
                "total_count": result["pagination"]["total_count"],
            },
        )
    except Exception as e:
        logger_error(f"[AI_TOOL] 月度总结失败 | user_id:{user_id} | year:{year} | month:{month} | error:{repr(e)}")
        raise