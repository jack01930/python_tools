#app/api/v1/ai.py
from sqlite3 import Error as SQLiteError
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.user import get_current_user
from app.config.logger import info as logger_info
from app.schemas.ai import AIFinanceRequest
from app.schemas.common import SuccessResponse
from app.services.ai.v1_4.agent import process_ai_request

router = APIRouter(prefix="/ai", tags=["AI记账"])


@router.post("/auto_record", summary="AI自动记账(自然语言转账记录)", response_model=SuccessResponse)
def ai_auto_record_api(
    req: AIFinanceRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    try:
        logger_info(f'[AI接口] 收到请求 | user_id:{current_user["id"]} | 输入：{req.text}')
        return process_ai_request(req.text, current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLiteError:
        raise HTTPException(status_code=500, detail="数据库操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI记账失败：{str(e)}")


@router.post("/chat-v2", summary="AI记账 v1.5（带长期记忆）", response_model=SuccessResponse)
def ai_chat_v2_api(
    req: AIFinanceRequest,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    AI记账 v1.5 版本，支持长期记忆和多轮对话

    可选参数（通过请求体扩展字段）:
    - session_id: 会话ID，用于继续之前的对话
    """
    try:
        from app.services.ai.v1_5.agent import process_ai_request as process_ai_request_v5

        # 从请求中提取session_id（如果存在）
        session_id = None
        if hasattr(req, 'session_id') and req.session_id:
            session_id = req.session_id

        logger_info(f'[AI接口 v1.5] 收到请求 | user_id:{current_user["id"]} | session:{session_id} | 输入：{req.text}')
        return process_ai_request_v5(req.text, current_user["id"], session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLiteError:
        raise HTTPException(status_code=500, detail="数据库操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI记账失败：{str(e)}")
