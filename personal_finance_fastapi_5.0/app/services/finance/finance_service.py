#app/services/finance/finance_service.py
from sqlite3 import Error as SQLiteError
from app.crud.finance import create_record, get_records_by_year_month, delete_record, clear_month_records
from app.config.logger import error as logger_error, warn as logger_warn, info as logger_info

# 1. 新增记账记录的业务逻辑
def add_finance_record(internal_record,user_id):
    """封装添加记账的核心逻辑"""
    try:
        # 调用CRUD层操作数据库
        is_insert_success = create_record(
            request_id=internal_record.request_id,
            amount=internal_record.amount,
            category=internal_record.category,
            remark=internal_record.remark,
            user_id=user_id
        )
        # 业务逻辑：判断是否重复提交
        if is_insert_success:
            logger_info(f"[ADD] 记账成功 | request_id:{internal_record.request_id} | 金额：{internal_record.amount}")
        else:
            # 重复提交：打印警告、返回业务提示，不会再走成功逻辑
            logger_warn(f"[ADD] 重复记账请求拦截 | request_id:{internal_record.request_id} 已存在")
            raise ValueError("该序号今日已提交过，请勿重复操作")  # 抛业务异常，让API层捕获
        return internal_record.model_dump()  # 返回新增记录信息给API层
    except SQLiteError as e:
        logger_error(f"[ADD] 数据库异常 | {str(e)}")
        raise e  # 抛给API层处理
    except Exception as e:
        logger_error(f"[ADD] 系统异常 | {str(e)}")
        raise e
    
# 2. 按年月查询记录的业务逻辑
def get_finance_records(year, month, page, page_size,user_id):
    """封装查询记账记录的核心逻辑"""
    try:
        # 调用CRUD层查数据
        stats, records = get_records_by_year_month(year, month, page, page_size,user_id=user_id)
        # 业务逻辑：处理查询结果格式（转成前端友好的结构）
        total_income = stats['total_income'] or 0.0
        total_expense = stats['total_expense'] or 0.0
        total_count = stats['total_count'] or 0
        total_balance = total_income - total_expense

        # 转换记录格式
        result = []
        for r in records:
            result.append({
                "id": r['id'],
                'date': r['record_date'],
                'create_time': r['create_time'],
                'type': '收入' if r['amount'] > 0 else '支出',
                'amount': abs(r['amount']),
                'category': r['category'],
                'remark': r['remark'],
            })
        # 组装最终返回给API层的数据
        return {
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_page': (total_count + page_size - 1) // page_size
            },
            "statistics": {
                "year": year,
                "month": month,
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "total_balance": round(total_balance, 2)
            },
            'detail': result
        }
    except SQLiteError as e:
        logger_warn(f"[QUERY] 数据库异常 | {year}-{month} | {str(e)}")
        raise e
    except Exception as e:
        logger_error(f"[QUERY] 系统异常 | {str(e)}")
        raise e
    
# 3. 删除单条记录的业务逻辑
def delete_finance_record(record_id, confirm, user_id):
    """封装删除单条记录的核心逻辑"""
    try:
        # 业务逻辑：校验删除确认
        if not confirm or (confirm.lower() not in ['yes', 'y']):
            raise ValueError('已取消删除，删除需要输入yes or y')
        # 调用CRUD层删数据
        success = delete_record(record_id,user_id)
        if not success:
            raise ValueError(f'ID{record_id}不存在或删除失败')
        return {'message': f'ID{record_id}删除成功'}
    except SQLiteError as e:
        logger_error(f"[DELETE] 数据库异常 | ID:{record_id} | {str(e)}")
        raise e
    except Exception as e:
        logger_error(f"[DELETE] 系统异常 | ID:{record_id} | {str(e)}")
        raise e
    
# 4. 清空年月记录的业务逻辑
def clear_finance_month(year, month, confirm, user_id):
    """封装清空指定年月记录的核心逻辑"""
    try:
        # 业务逻辑：校验删除确认
        if not confirm or (confirm.lower() not in ['yes', 'y']):
            raise ValueError('已取消删除，删除需要输入yes or y')
        # 调用CRUD层清空数据
        total = clear_month_records(year, month, user_id)
        if total == 0:
            raise ValueError(f'{year}年{month}月无记录可清空')
        return {'message':f'{year}年{month}月 记录已清空'}
    except SQLiteError as e:
        logger_warn(f"[CLEAR] 数据库异常 | {year}-{month} | {str(e)}")
        raise e
    except Exception as e:
        logger_error(f"[CLEAR] 系统异常 | {year}-{month} | {str(e)}")
        raise e