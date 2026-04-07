from pydantic import BaseModel,Field,model_validator
from typing import Optional
from datetime import datetime

class RecordAddRequest(BaseModel):
    serial_num:int=Field(
          ...,
          gt=0,
          description='当日请求序号，用于重复提交拦截，同一天内不能重复使用',
    )

    amount:float=Field(
        ...,#...可默认不写，在非Optional时默认该项为必填项
        ne=0,#确保amount不为0
        description='记账金额(单位元，正数为收入，负数为支出)',
    )

    category:str=Field(
        ...,
        min_length=1,#最小长度为1
        description='消费/收入分类（如餐饮、工资）',
    )

    remark:Optional[str]=Field(
        default='无',#default也可省略
        description="记账备注（可选）",
    )

    model_config={
        'json_schema_extra':{
            'example':{
                'serial_num':1,
                'amount':20,
                'category':'餐饮',
                'remark':"午餐吃了牛肉面"
            }
        }
    }

class RecordAddInternal(RecordAddRequest):
    request_id:str=Field(
        description='后端自动生成：当日日期+前端输入的序号'
    )   
     #@classmethod标记这是类方法→cls代表RecordAddInternal类→
     #values是前端传的原始参数字典→你从values拿serial_num生成request_id
     #再放回values，让 Pydantic 校验时能找到request_id
    @model_validator(mode='before') #字段检验前
    @classmethod #标记这是类方法
    def generate_request_id(cls,values:dict): #cls代表这是类本身，values则是前端的原始参数字典
        today_time=datetime.now().strftime('%Y-%m-%d')
        values['request_id']=f'{today_time}-{values['serial_num']:03d}'        
        return values

