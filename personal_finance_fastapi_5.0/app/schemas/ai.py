#app/schemas/ai.py
from pydantic import BaseModel, Field
from typing import Optional

class AIFinanceRequest(BaseModel):
    text:str=Field(...,min_length=1,description="记账的自然语言描述，'今天中午吃了20元的牛肉面'")

class AIParseResult(BaseModel):
    category:str=Field(...,description='记账分类，饮食/工资/交通/购物/娱乐/房租/水电/其他')
    amount:float=Field(...,description='金额，支出为负数，收入为正数')
    remark:Optional[str]=Field(default=None,description='备注，默认带原句')