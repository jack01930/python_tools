from datetime import datetime, timezone, timedelta # 处理时间（设置token过期时间）
from jose import JWTError, jwt # 生成/解析JWT token的核心库
from passlib.context import CryptContext # 密码哈希加密的库

from app.config.settings import settings

pwd_context=CryptContext(schemes=['bcrypt'],deprecated='auto') #指定用不可逆bcrypt 算法加密密码，自动弃用过时的加密方式

SECRET_KEY=settings.SECRET_KEY
ALGORITHM=settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES=settings.ACCESS_TOKEN_EXPIRE_MINUTES

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta=None):
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+(expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({'exp':expire,'sub':str(data['user_id'])}) #给令牌加 “身份标签” 和 “过期时间”
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM) #用密钥把数据加密成最终的令牌字符串

def get_user_id_from_token(token:str):
    try:
        print(f"正在验证令牌: {token[:20]}...")  # 只打印前20个字符
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        print(f"解码后的payload: {payload}")
        sub = payload.get('sub')
        print(f"sub值: {sub}, 类型: {type(sub)}")
        if sub is None:
            return None
        try:
            return int(sub)
        except (TypeError, ValueError):
            return None
    except JWTError as e:
        print(f"JWT解码失败: {str(e)}")
        return None

