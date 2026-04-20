#app/schemas/user.py
from pydantic import BaseModel, Field
from typing import Optional

class UserRegisterRequest(BaseModel):
    username:str=Field(...,min_length=3,max_length=20,description='用户名(3-20位)')
    password:str=Field(...,min_length=6,max_length=18,description='用户密码(6-18位)')
    email:Optional[str]=Field(None,description='邮箱(可选)')

    model_config={
        "json_schema_extra":{
            "example":{
                "username":"Mike",
                "password":"12345678",
                "email":"test@example.com"
            }
        }
    }

class UserLoginRequest(BaseModel):
    username:str=Field(...,min_length=3,max_length=20,description='用户名(3-20位)')
    password:str=Field(...,min_length=6,max_length=18,description='用户密码(6-18位)')

class UserInfoResponse(BaseModel):
    id :int
    username:str
    email:Optional[str]
    create_time:str

    class Config:
        from_attributes=True

class UserLoginResponse(BaseModel):
    access_token:str
    token_type:str="bearer"
    user_info:UserInfoResponse