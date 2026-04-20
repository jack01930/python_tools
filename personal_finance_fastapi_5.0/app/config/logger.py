#app/config/logger.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler #解决日志时间切割问题

# 修复路径：从config目录往上找项目根目录
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CONFIG_DIR)
PROJECT_ROOT = os.path.dirname(APP_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")  # 日志目录在项目根
#__file__为当前文件名，每套一层os.path.dirname就会往上走一层
os.makedirs(LOG_DIR,exist_ok=True) #exist_ok=False若存在会报错

INFO_LOG_FILE=os.path.join(LOG_DIR,"finance_app.log")
ERROR_LOG_FILE=os.path.join(LOG_DIR,"error.log")

LOG_FORMAT="%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s"
#(astime)时间戳，s表示字符串格式，d表示整数格式，-8s左对齐占8个字符
DATE_FORMAT='%Y-%m-%d %H:%M:%S'
formatter=logging.Formatter(LOG_FORMAT,datefmt=DATE_FORMAT)
#封装为格式化工具

logger=logging.getLogger()
#获取日志核心入口
logger.setLevel(logging.INFO)
#设置级别为info
logger.handlers.clear()
#清除热加载的日志

console_handler=logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)
#logging.WARNING才是级别 logging.warning是记录日志的函数
logger.addHandler(console_handler)

file_handler = TimedRotatingFileHandler(
    filename=INFO_LOG_FILE,  # 日志文件路径
    when="midnight",         # 切割时机：每天午夜（0点）
    interval=1,              # 切割间隔：1天
    backupCount=30,          # 保留30天的历史日志，超过自动删除
    encoding="utf-8"         # 日志文件编码，避免中文乱码
)

file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

error_file_handler= TimedRotatingFileHandler(
    filename=ERROR_LOG_FILE,
    when="midnight",     
    interval=1,         
    backupCount=30,         
    encoding="utf-8"    
)

error_file_handler.setFormatter(formatter)
error_file_handler.setLevel(logging.ERROR)
logger.addHandler(error_file_handler)

def info(msg, *args, **kwargs):
    if not isinstance(msg, str):
        msg = str(msg)
    logger.info(msg, *args, **kwargs)

def warn(msg, *args, **kwargs):
    if not isinstance(msg, str):
        msg = str(msg)
    logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    if not isinstance(msg, str):
        msg = str(msg)
    logger.error(msg, *args, **kwargs)

def exception(msg, *args, **kwargs):
    if not isinstance(msg, str):
        msg = str(msg)
    logger.exception(msg, *args, **kwargs)


