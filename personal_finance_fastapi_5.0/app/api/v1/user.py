#app/api/v1/user.py
from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict,Any

from app.schemas.user import UserRegisterRequest,UserLoginRequest,UserLoginResponse
from app.schemas.common import SuccessResponse,EmptyDataResponse
from app.schemas.response import success_response
from app.crud.user import create_user,get_user_by_username,get_user_by_id
from app.config.auth import hash_password,verify_password,create_access_token,ACCESS_TOKEN_EXPIRE_MINUTES,get_user_id_from_token
from app.schemas.response import success_response
from app.config.logger import info as logger_info,error as logger_error
from app.services.user.user_service import service_user_login,service_user_register,service_get_current_user

router=APIRouter(prefix='/user',tags=['用户管理'])
oauth2_scheme=OAuth2PasswordBearer(tokenUrl='/user/login') #FastAPI 提供的OAuth2 密码模式认证工具，专门用于 “用户名 + 密码登录获取令牌” 的场景

def get_current_user(token:str=Depends(oauth2_scheme)):
    user_id=get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401,detail="token无效/过期")
    user=service_get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401,detail='用户不存在')
    return dict(user)
    
@router.post('/register',summary='用户注册',response_model=SuccessResponse)
def register(user:UserRegisterRequest)->Dict[str,Any]:
    try:
        result=service_user_register(user.username,user.password,user.email)
        return success_response(
            msg='注册成功',
            data=result
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'注册失败：{str(e)}')
    
# 登录用POST是为了隐藏敏感的账号密码，同时符合 “提交数据创建登录状态” 的语义
@router.post('/login',summary='用户登录',response_model=UserLoginResponse)
def login(form_data:OAuth2PasswordRequestForm=Depends())->Dict[str,Any]:
    try:
        return service_user_login(form_data.username,form_data.password,ACCESS_TOKEN_EXPIRE_MINUTES)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f'登录失败：{str(e)}')
    
@router.get('/me',summary='获取本人用户信息')
def get_my_info(current_user:dict=Depends(get_current_user)):
    return current_user