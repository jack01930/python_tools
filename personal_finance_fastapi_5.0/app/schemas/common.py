#app/schemas/common.py
from pydantic import BaseModel,Field
from typing import Optional,TypeVar,Generic,Dict,Any

T=TypeVar('T',dict,list,str,int,None)

class BaseResponse(BaseModel,Generic[T]):
    code:int=Field(...,description='业务状态码 (200成功/4xx业务异常/5xx系统异常)')
    msg:str=Field(...,description='用户可读的提示信息')
    data:Optional[T]=Field(default=None,description='业务数据(泛型类型，可选)')

    class Config:
        from_attributes=True
        json_schema_extra={
            "examples":[
                {"code":200,"msg":"操作成功","data":{"id":1,"amount":20}},
                {"code":400,"msg":"参数错误","data":None},
                {"code":500,"msg":"系统异常","data":None},
            ]
        }

SuccessResponse=BaseResponse[Dict[str,Any]]
EmptyDataResponse=BaseResponse[None]