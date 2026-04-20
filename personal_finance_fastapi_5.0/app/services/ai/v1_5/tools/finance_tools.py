from typing import Any, Dict

from langchain_core.tools import tool

from app.config.logger import error as logger_error, info as logger_info
from app.schemas.finance import RecordAddInternal
from app.schemas.response import success_response
from app.services.finance.finance_service import (
    add_finance_record,
    delete_finance_record,
    get_finance_records,
)
from app.utils.finance.finance_utils import get_today_max_serial_num

@tool
def add_record_tool(
    user_id: int,
    category: str,
    amount: float,
    remark: str | None = None,
) -> Dict[str, Any]:
    """
    新增一条记账记录，写入数据库。
    入参要求：
    - category: 记账分类，仅支持：饮食、工资、交通、购物、娱乐、房租、水电、其他（必填）
    - amount: 金额，支出为负数，收入为正数，仅数字（必填）
    - remark: 备注，格式必须为「原句: 用户输入的原始内容」（可选）
    返回：标准化的成功/失败响应
    """
    try:
        serial_num = get_today_max_serial_num(user_id) + 1
        record = RecordAddInternal(
            category=category,
            amount=amount,
            remark=remark,
            serial_num=serial_num,
        )
        record_detail = add_finance_record(record, user_id)
        logger_info(f"[AI_TOOL] 添加记账成功 | user_id:{user_id} | record:{record_detail}")
        return success_response(msg="添加记账成功", data=record_detail)
    except Exception as e:
        logger_error(f"[AI_TOOL] 添加记账失败 | user_id:{user_id} | 信息:{repr(e)}")
        raise

@tool
def query_records_tool(
    user_id: int,
    year: int,
    month: int,
) -> Dict[str, Any]:
    """
    查询某年某月的记账记录
    入参要求：
    - year: 查询的年份，整数类型（必填）
    - month: 查询的月份，整数类型（1-12）（必填）
    返回：包含查询结果的标准化响应
    """
    try:
        result = get_finance_records(
            year=year,
            month=month,
            page=1,
            page_size=200,
            user_id=user_id,
        )
        logger_info(f"[AI_TOOL] 查询记账成功 | user_id:{user_id} | year:{year} | month:{month} | records:{result}")
        return success_response(
            msg=f"查询{year}年{month}月记账记录成功",
            data={
                "records": result["detail"],
                "total_count": result["pagination"]["total_count"],
                "statistics": result["statistics"],
            },
        )
    except Exception as e:
        logger_error(f"[AI_TOOL] 查询记账失败 | user_id:{user_id} | 年月:{year}-{month} | 信息:{repr(e)}")
        raise

@tool
def delete_record_tool(
    user_id: int,
    record_id: int,
) -> Dict[str, Any]:
    """
    删除指定的记账记录。
    入参要求：
    - record_id: 要删除的记录ID，整数类型（必填）
    返回：标准化的成功/失败响应
    """
    try:
        result = delete_finance_record(
            record_id=record_id,
            confirm="yes",
            user_id=user_id,
        )
        logger_info(f"[AI_TOOL] 删除记账成功 | user_id:{user_id} | record_id:{record_id}")
        return success_response(msg=f"删除record_id为{record_id}的记录成功", data=result)
    except Exception as e:
        logger_error(f"[AI_TOOL] 删除记账失败 | user_id:{user_id} | record_id:{record_id} | 信息:{repr(e)}")
        raise


__all__ = [
    "add_record_tool",
    "query_records_tool",
    "delete_record_tool",
]