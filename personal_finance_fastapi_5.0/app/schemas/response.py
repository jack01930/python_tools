from typing import Dict,Any,Optional,TypeVar
from app.schemas.common import BaseResponse,T

ResponseDict=Dict[str,Any]

def success_response(
        msg:str,
        data:Optional[T]=None
) -> ResponseDict:
    return BaseResponse[T](
        code=200,
        msg=msg,
        data=data
    ).model_dump(exclude_none=False)

def error_response(
        code:int,
        msg:str,
        data:Optional[T]=None
) ->ResponseDict:
    return BaseResponse[T](
        code=code,
        msg=msg,
        data=data
    ).model_dump(exclude_none=False)