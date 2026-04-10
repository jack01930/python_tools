
from app.crud.finance import get_today_max_serial_num as _get_today_max_serial_num
from app.config.logger import warn as logger_warn

def get_today_max_serial_num(user_id: int) -> int:
    """封装CRUD调用，作为工具函数供上层服务使用"""
    try:
        return _get_today_max_serial_num(user_id)
    except Exception as e:
        logger_warn(f"[工具函数] 获取当日最大序号失败 | user_id:{user_id} | 错误：{str(e)}")
        return 0