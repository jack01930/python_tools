from fastapi import APIRouter,HTTPException,Query,Path,Depends
from sqlite3 import Error as SQLiteError
from typing import Dict,Any,Optional,List
from datetime import datetime

from app.api.v1.user import get_current_user
from app.schemas.finance import RecordAddRequest,RecordAddInternal
from app.schemas.common import SuccessResponse,EmptyDataResponse
from app.schemas.response import success_response
from app.services.finance.finance_service import add_finance_record, get_finance_records, delete_finance_record, clear_finance_month
from app.config.logger import error as logger_error,warn as logger_warn,info as logger_info

router=APIRouter(prefix='/finance',tags=['记账管理'])

@router.post('/add',summary='添加一条记账记录',response_model=SuccessResponse)
def add_record(record:RecordAddRequest,
               current_user:dict=Depends(get_current_user)) ->Dict[str,Any]:
    try:
        logger_info(f"[ADD] 接口被调用，参数：{record.model_dump()}")
        internal_record=RecordAddInternal(**record.model_dump())
        record_detail=add_finance_record(internal_record,current_user['id'])
        return success_response(
            msg='记账成功',
            data={'detail':record_detail}
        )
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e)) #主动抛出错误，以免全部被下except Exception捕获 FastAPI 的 HTTPException 是 Exception 的子类，如果你不单独捕获，它会被下面的 except Exception 捕获，然后被包装成一个新的 HTTPException
    except SQLiteError as e:  # 专门捕获数据库异常
        raise HTTPException(status_code=500, detail=f'数据库操作失败，请稍后重试')
    except Exception as e:
        raise HTTPException(status_code=500,detail=f'记账失败:{str(e)}')#系统异常500 业务逻辑错误400
    
@router.get('/records',summary='按年月查询记录',response_model=SuccessResponse)
def get_records(
    year:int=Query(...,description='查询年份'),
    month:int=Query(...,ge=1,le=12,description='查询月份1-12'),
    page:int=Query(default=1,ge=1,description='页码>=1'),
    page_size:int=Query(default=5,ge=1,description='每页条数>=1'),
    current_user:dict=Depends(get_current_user)
    )-> Dict[str,Any]:
    try:        
        result_data=get_finance_records(year,month,page,page_size,user_id=current_user['id'])
        return success_response(
            msg='查询成功',
            data=result_data
        )
    except HTTPException as e:
        raise e  #FastAPI 的 HTTPException 是 Exception 的子类，如果你不单独捕获，它会被下面的 except Exception 捕获，然后被包装成一个新的 HTTPException
    except SQLiteError as e:  # 专门捕获数据库异常
        raise HTTPException(status_code=500, detail=f'数据库操作失败，请稍后重试')
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'查询失败:{str(e)}')
    
@router.delete('/delete/{record_id}',summary='根据ID删除',response_model=EmptyDataResponse)
def delete_record(
    record_id:int=Path(...,gt=0,description='记录ID'),
    confirm:Optional[str]= Query(default=None,description='删除确认(yes / y)'),
    current_user:dict=Depends(get_current_user)
    ) ->Dict[str,Any] :
        try:
            msg=delete_finance_record(record_id,confirm,user_id=current_user['id'])
            ## 问题：`crud.delete_record`返回False可能是“记录不存在”，也可能是“删除操作失败”，统一抛404不符合HTTP状态码规范
            return success_response(msg=msg)
        except ValueError as e:
            status_code=404 if '不存在' in str(e) else 400
            raise HTTPException(status_code=status_code,detail=str(e)) #主动抛出错误，以免全部被下except Exception捕获 FastAPI 的 HTTPException 是 Exception 的子类，如果你不单独捕获，它会被下面的 except Exception 捕获，然后被包装成一个新的 HTTPException
        except SQLiteError as e:  # 专门捕获数据库异常
            raise HTTPException(status_code=500, detail=f'数据库操作失败，请稍后重试')
        except Exception as e:
            raise HTTPException(status_code=400,detail=f'删除失败{str(e)}')
        
@router.delete('/clear',summary='清空指定年月记账记录',response_model=EmptyDataResponse)
def clear_month(
    year:int=Query(...,description='查询年份'),
    month:int=Query(...,ge=1,le=12,description='查询月份1-12'),
    confirm:Optional[str]= Query(default=None,description='删除确认(yes / y)'),
    current_user:dict=Depends(get_current_user)
    )->Dict[str,Any]:
    try:
        msg=clear_finance_month(year,month,confirm,user_id=current_user['id'])
        return success_response(msg=msg)
    except ValueError as e:
        if '无记录可清空' in str(e):
            # 正常场景直接返回成功响应
            return success_response(msg=str(e))
        else:
            raise HTTPException(status_code=400,detail=str(e)) #主动抛出错误，以免全部被下except Exception捕获 FastAPI 的 HTTPException 是 Exception 的子类，如果你不单独捕获，它会被下面的 except Exception 捕获，然后被包装成一个新的 HTTPException
    except SQLiteError as e:  # 专门捕获数据库异常
        raise HTTPException(status_code=500, detail=f'数据库操作失败，请稍后重试')    
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'清空失败：{str(e)}')
    

        

    