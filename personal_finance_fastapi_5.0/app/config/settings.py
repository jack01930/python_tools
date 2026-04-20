#app/config/settings.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


#当前SECRET_KEY/ALGORITHM等字段只需要 “类型正确”（如str/int），Pydantic BaseSettings通过类型注解就能完成基础校验，无需额外的Field
class Settings(BaseSettings): 
    SECRET_KEY:str=os.getenv("SECRET_KEY","Z(RJ*b]Y77eayQfs(VETLmrQ-{%1wLJq") #读取环境变量，无则使用默认值
    ALGORITHM:str="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int=30

    QWEN_API_KEY:str=os.getenv("QWEN_API_KEY","")
    QWEN_BASE_URL:str=os.getenv("QWEN_BASE_URL","https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL:str=os.getenv("QWEN_MODEL","qwen-turbo")
settings=Settings()
