from pydantic import BaseModel,Field
from typing import Optional

class RecordAdd(BaseModel):
    amount:float=Field(
        ...,
        gt=0,
        description='记账金额(单位元，正数为收入，负数为支出)',
        example=100.5
    )

    category:str=Field(
        ...,
        min_length=1,
        description='消费/收入分类（如餐饮、工资）',
        example='餐饮'
    )

    remark:Optional[str]=Field(
        '无',
        description="记账备注（可选）",
        example="午餐吃了牛肉面"
    )