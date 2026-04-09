#app/api/v1/ai.py
from fastapi import APIRouter, HTTPException, Depends
from sqlite3 import Error as SQLiteError
from typing import Dict, Any

from app.api.v1.user import get_current_user
from app.schemas.ai import AIFinanceRequest
from app.schemas.common import SuccessResponse
from app.schemas.response import success_response
from app.services.ai.ai_record_service import ai_auto_record
from app.config.logger import error as logger_error ,info as logger_info

router=APIRouter(prefix='/ai',tags=['AI记账'])

@router.post('/auto_record',summary='AI自动记账(自然语言转账记录)',response_model=SuccessResponse)
def ai_auto_record_api(
    req:AIFinanceRequest,
    current_user:dict=Depends(get_current_user)
)->Dict[str,Any]:
    try:
        logger_info(f'[AI接口] 收到请求 | user_id:{current_user["id"]} | 输入：{req.text}')
        result=ai_auto_record(req.text,current_user['id'])
        return success_response(
            msg='AI自动记账成功',
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
    except SQLiteError as e:
        raise HTTPException(status_code=500,detail="数据库操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500,detail=f'AI记账失败：{str(e)}')