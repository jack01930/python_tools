#app/schemas/ai.py
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

class AIFinanceRequest(BaseModel):
    text:str=Field(...,min_length=1,description="记账的自然语言描述，'今天中午吃了20元的牛肉面'")
    session_id: Optional[str] = Field(None, description="会话ID，用于多轮对话记忆，如不提供则生成新会话")

class AIParseResult(BaseModel):
    intent:Literal["add_record","query_records","delete_record","other"]=Field(...,description='意图，支持四种类型：add_record(记账)、query_records(查询年月记账)、delete_record(根据ID删除记账)、other(其他)')
    category:Optional[Literal["饮食","工资","交通","购物","娱乐","房租","水电","其他"]]=Field(None,description='记账分类')
    amount:Optional[float]=Field(None,description='金额，支出为负数，收入为正数')
    remark:Optional[str]=Field(None,description='备注，默认带原句')
    year:Optional[int]=Field(None,description='年份，用于查询年月记账')
    month:Optional[int]=Field(None,description='月份，用于查询年月记账')
    record_id:Optional[int]=Field(None,description='记录ID，用于删除记账')

    @field_validator('remark', mode='before')
    @classmethod
    def validate_remark(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith("原句："):
            raise ValueError("备注必须以'原句：'开头")
        return value
