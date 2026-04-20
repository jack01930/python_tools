#app/services/user/user_service.py
from datetime import timedelta

from app.crud.user import create_user, get_user_by_username, get_user_by_id
from app.config.auth import hash_password, verify_password, create_access_token
from app.config.logger import info as logger_info, error as logger_error, warn as logger_warn

def service_user_register(username:str,password:str,email:str=None):
    try:
        if get_user_by_username(username):
            raise Exception("用户名已存在")
        
        pwd_hash=hash_password(password)
        user_id=create_user(username,pwd_hash,email)

        if not user_id:
            raise Exception(f"用户创建失败: {username}")
        
        logger_info(f"用户注册成功 | 用户名： {username}")
        return {"user_id" : user_id}
    except Exception as e:
        logger_error(f'注册失败 | 信息：{str(e)}')
        raise e

def service_user_login(username:str,password:str,ACCESS_TOKEN_EXPIRE_MINUTES:int):
    try:
        db_user=get_user_by_username(username)
        if not db_user or not verify_password(password,db_user['password_hash']):
            logger_warn(f"登录失败 | 用户名：{username} | 原因：用户名或密码错误")
            raise Exception("用户名或密码错误")
        token=create_access_token(
            data={'user_id':db_user['id']},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        logger_info(f"用户登录成功 | 用户名：{username}")
        return {
            'access_token':token,
            'token_type':'bearer',
            'user_info':{
                'id':db_user['id'],
                'username':db_user['username'],
                'email':db_user['email'],
                'create_time':db_user['create_time']
            }
        }
    except Exception as e:
        logger_error(f'登录失败 | 用户名：{username} | 信息：{str(e)}')
        raise e
    
def service_get_current_user(user_id:int):
    return get_user_by_id(user_id)
    

