import sqlite3
import os
import uvicorn
from datetime import datetime
from tabulate import tabulate
from fastapi import FastAPI,Form,HTTPException
from pydantic import BaseModel
from typing import List,Optional

DB_FILE='personal_finance.db'

# ===================== FastAPI 应用创建 ======================

app=FastAPI(
    title='个人记账app',
    description='基于FastAPI改造的个人财务管理接口',
    version='1.0.0'
)

class RecordAdd(BaseModel):
    amount:float
    category:str
    remark:Optional[str]='无'
#起到数据封装和检验的功效，方便后续record.amount调用


# 移到 get_db_connection 外部，程序启动时执行
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS finance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            remark TEXT DEFAULT '无',
            record_date TEXT NOT NULL,
            create_time TEXT NOT NULL
        );
        """)
        conn.commit()
        conn.close()

# 程序启动时初始化数据库
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn  # 移除建表和commit逻辑


#1.添加记账记录
@app.post('/add',summary='添加一条记账记录')
def api_add_record(record:RecordAdd):
    try:
        amount=record.amount
        category=record.category
        remark=record.remark
        record_date=datetime.now().strftime("%Y-%m-%d")
        create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute(
                """INSERT INTO finance_records (amount, category,remark,record_date,create_time)
                VALUES (?, ?, ?, ?, ?)""",
                (amount, category, remark, record_date,create_time) #添加了create_time记得上面也要加上
            )
            conn.commit()
        return {'code':200,'msg':'记账成功','data':record.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'记账失败:{str(e)}')

#2.按年月查询记录
@app.get('/records',summary='按年月查询记录(分页+数据库统计)')
def api_get_records_by_year_month(
    year:int,
    month:int,
    page:int=1, #页码，默认第一页
    page_size:int=5 #每页页数，默认5
    ):
    try:
        if not(1<=month<=12):
            raise HTTPException(status_code=400,detail='月份范围必须为1-12')
        if page<1 or page_size<1:
            raise HTTPException(status_code=400,detail='页码/每页页数必须>=1')
        date_prefix=f"{year}-{month:02d}"
        offset=(page-1)*page_size
        with get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute('''
                SELECT
                           SUM(CASE WHEN amount >0 THEN amount ELSE 0 END) AS total_income,
                           SUM(CASE WHEN amount <0 THEN ABS(amount) ELSE 0 END) AS total_expense,
                           COUNT(*) AS total_count
                FROM finance_records
                WHERE record_date LIKE ?
            ''',(f'{date_prefix}%',))
            stats=cursor.fetchone()
            total_income=stats['total_income'] or 0.0
            total_expense=stats['total_expense'] or 0.0
            total_count=stats['total_count'] or 0.0
            total_balance=total_income-total_expense

            cursor.execute('''
                SELECT * FROM finance_records
                WHERE record_date LIKE ?
                ORDER BY record_date,id
                LIMIT ? OFFSET ?
            ''',(f'{date_prefix}%',page_size,offset))
            records=[dict(row) for row in cursor.fetchall()]
            result=[]
            for r in records:
                result.append({
                    "id":r['id'],
                    'date':r['record_date'],
                    'create_time':r['create_time'],
                    'type':'收入' if r['amount']>0 else '支出',
                    'amount':abs(r['amount']),
                    'category':r['category'],
                    'remark':r['remark']
                })
        return {
            'code':200,
            'msg':'查询成功',
            'data':{
                'pagination':{
                    'page':page,
                    'page_size':page_size,
                    'total_count':total_count,
                    'total_page':(total_count+page_size-1)//page_size#总页数
                },
                "statistics":{
                    "year":year,
                    "month":month,
                    "total_income":round(total_income,2),
                    "total_expense":round(total_expense,2),
                    "total_balance":round(total_balance,2)
                },
                'detail':result
            }
        }
    except HTTPException:
        raise#主动抛出错误，以免全部被下except Exception捕获    
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'查询失败:{str(e)}')

#3.根据ID删除单条记录
@app.delete('/delete/{record_id}',summary='根据ID删除记录(需二次确认，在confirm中输入yes 或者 y)')
def api_delete_single_record(record_id:int,confirm:str=None):
    try:
        if not confirm or (confirm.lower() not in ['yes', 'y']):
            raise HTTPException(status_code=400,detail='已取消删除，删除需要输入yes or y')
        with get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute("SELECT id FROM finance_records WHERE id=?",(record_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404,detail=f'ID{record_id}不存在')
            cursor.execute("DELETE FROM finance_records WHERE id=?",(record_id,))
            conn.commit()
        return {'code':200,'msg':f'ID{record_id}删除成功'}
    except HTTPException:
        raise#主动抛出错误，以免全部被下except Exception捕获
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'删除失败{str(e)}')

#4.清空指定年月的所有记录
@app.delete('/clear',summary='清空指定年月所有记录(需二次确认，在confirm中输入yes 或者 y)')
def api_clear_records(year:int,month:int,confirm:str=None):
    try:
        if not confirm or (confirm.lower() not in ['yes', 'y']):
            raise HTTPException(status_code=400,detail='已取消删除，删除需要输入yes or y')        
        if not(1<=month<=12):
            raise HTTPException(status_code=400,detail='月份范围必须为1-12')
        date_prefix=f'{year}-{month:02d}'
        with get_db_connection() as conn:
            cursor=conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM finance_records WHERE record_date LIKE ?',(f'{date_prefix}%',))
            total=cursor.fetchone()[0]
            if total==0:
                raise HTTPException(status_code=400,detail=f'{year}年{month}月无记录可清空')
            cursor.execute("DELETE FROM finance_records WHERE record_date LIKE ?",(f"{date_prefix}%",))
            conn.commit()
        return {'code':200,'msg':f'{year}年{month}月 记录已清空'}
    except HTTPException:
        raise#主动抛出错误，以免全部被下except Exception捕获
    except Exception as e:
        raise HTTPException(status_code=400,detail=f'清空失败：{str(e)}')

# =============================== 启动 =====================================
if __name__ == '__main__':
    uvicorn.run(app,host='127.0.0.1',port=8000)
