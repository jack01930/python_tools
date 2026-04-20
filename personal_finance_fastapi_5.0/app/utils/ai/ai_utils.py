#app/utils/ai/ai_utils.py
from langchain_core.tools import tool
from typing import Dict,Any

from app.schemas.response import success_response
from app.schemas.finance import RecordAddInternal
from app.services.finance.finance_service import add_finance_record
from app.utils.finance.finance_utils import get_today_max_serial_num
from app.config.logger import error as logger_error, info as logger_info
@tool
def add_record_tool(user_id:int,
                    category:str,
                    amount:float,
                    remark:str|None=None,
                    
)->Dict[str,Any]:
    """
    给指定用户新增一条记账记录，写入数据库。
    入参要求：
    - user_id: 用户的ID，数字类型
    - category: 记账分类，仅支持：饮食、工资、交通、购物、娱乐、房租、水电、其他
    - amount: 金额，支出为负数，收入为正数，仅数字
    - remark: 备注，格式必须为「原句: 用户输入的原始内容」
    返回：标准化的成功/失败响应
    """
    try:
        serial_num=get_today_max_serial_num(user_id)+1
        record=RecordAddInternal(
            category=category,
            amount=amount,
            remark=remark,
            serial_num=serial_num
        )

        record_detail=add_finance_record(record,user_id)
        logger_info(f"[AI记账] 添加成功 | user_id:{user_id} | record:{record_detail}")
        return success_response(msg="添加成功",data=record_detail)
    except Exception as e:
        logger_error(f"[AI记账] 添加失败 | user_id:{user_id} | 信息：{str(e)}")
        raise e
