from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from app.api.v1.ai import router as ai_router
from app.api.v1.user import router as user_router
from app.api.v1.finance import router as finance_router
from app.config.database import init_db
from app.schemas.response import error_response
from app.config.logger import error as logger_error,warn as logger_warn,info as logger_info
# ========================
# ✅ FastAPI官方标准生命周期
# ========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 之前：服务启动时执行（仅执行1次）
    init_db()  # 数据库初始化
    logger_info("✅ 数据库已初始化")
    yield
    # yield 之后：服务关闭时执行（可选，后续可加资源释放逻辑）
    logger_info("🛑 服务已关闭，资源已释放")

# 把 lifespan 传入 FastAPI 构造函数
app = FastAPI(
    title='个人记账app',
    description='基于FastAPI的个人财务管理系统',
    version='1.2.0',
    lifespan=lifespan,  # 官方要求的标准写法
    docs_url='/docs',
    redoc_url='/redoc'
)

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    logger_warn(f"业务异常 | 路径：{request.url.path} | 状态码： {exc.status_code} | 信息：{exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(code=exc.status_code,msg=exc.detail)
    )

@app.exception_handler(Exception)
async def global_exception_handler(
    request:Request,
    exc:Exception
) ->JSONResponse:
    logger_error(f"系统异常 | 路径：{request.url.path} | 异常信息：{str(exc)}")
    return JSONResponse(
        status_code=500,
        content=error_response(code=500,msg=f"系统异常：{str(exc)}")
    )

app.include_router(finance_router)
app.include_router(user_router)
app.include_router(ai_router)

def main(host:str="127.0.0.1",port:int=8000)->None:
    uvicorn.run(
        app='app.main:app',
        host=host,
        port=port,
        reload=False
    )


if __name__=='__main__':
    import argparse  # 导入参数解析模块
    parser = argparse.ArgumentParser()  # 创建参数解析器
    # 添加--host参数，默认值127.0.0.1，有帮助说明
    parser.add_argument('--host', default='127.0.0.1', help='服务监听地址')
    # 添加--port参数，类型为整数，默认值8000
    parser.add_argument('--port', type=int, default=8000, help='服务监听端口')
    args = parser.parse_args()  # 解析命令行传入的参数
    main(host=args.host,port=args.port)