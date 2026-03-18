from fastapi import FastAPI
import uvicorn
from api import router

app=FastAPI(
    title='个人记账app',
    description='基于FastAPI的个人财务管理系统',
    version='1.1.0'
)

app.include_router(router)

if __name__=='__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)
    