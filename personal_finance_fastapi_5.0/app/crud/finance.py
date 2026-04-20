#app/crud/finance.py
from datetime import datetime
from app.config.database import get_db

def create_record(request_id:str,amount:float,category:str,remark:str='无',user_id:int=None):
    now=datetime.now()
    record_date=now.strftime('%Y-%m-%d')
    create_time=now.strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute(
            """INSERT OR IGNORE INTO finance_records
            (request_id, amount, category,remark,record_date,create_time,user_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (request_id, amount, category, remark, record_date, create_time, user_id) #添加了create_time记得上面也要加上
        )
        conn.commit()

        affect_rows=cursor.rowcount
        if affect_rows >0:
            from app.config.logger import info as logger_info
            logger_info(f"[INFO] 记账记录新增成功,request_id:{request_id},amount:{amount}")
            return True #成功返回成功
        else:
            from app.config.logger import warn as logger_warn
            logger_warn(f"[WARN] 重复记账请求已被忽略,request:{request_id}")
            return False #失败返回失败，原来不管什么都是return True，api.py无法判断逻辑

def get_records_by_year_month(year:int,month:int,page:int=1,page_size:int=5,user_id:int=None):
    date_prefix=f'{year}-{month:02d}'
    offset=(page-1)*page_size

    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute('''
                SELECT
                           SUM(CASE WHEN amount >0 THEN amount ELSE 0 END) AS total_income,
                           SUM(CASE WHEN amount <0 THEN ABS(amount) ELSE 0 END) AS total_expense,
                           COUNT(*) AS total_count
                FROM finance_records
                WHERE record_date LIKE ? AND user_id = ?
            ''',(f'{date_prefix}%',user_id))
        stats=cursor.fetchone()

        cursor.execute('''
            SELECT * FROM finance_records
            WHERE record_date LIKE ? AND user_id = ?
            ORDER BY record_date,id
            LIMIT ? OFFSET ?
        ''',(f'{date_prefix}%',user_id,page_size,offset))
        records=[dict(row) for row in cursor.fetchall()]
        # 修复：查询后转字典，让api层可以用 r['id']
        return stats,records
    
def delete_record(record_id:int,user_id:int):
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute('DELETE FROM finance_records WHERE id=? AND user_id = ?',(record_id,user_id))
        conn.commit()
        return cursor.rowcount>0
    
def clear_month_records(year:int,month:int,user_id:int):
    date_prefix=f'{year}-{month:02d}'
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute(
            'DELETE FROM finance_records WHERE record_date LIKE ? AND user_id = ?',(f'{date_prefix}%',user_id)
        )
        conn.commit()
        return cursor.rowcount
    
def get_today_max_serial_num(user_id:int):
    today=datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute("""
            SELECT MAX(CAST(SUBSTR(request_id,12) AS INTEGER))
            FROM finance_records
            WHERE request_id LIKE ? AND user_id = ?
        """,(f"{today}%",user_id))
        max_num=cursor.fetchone()[0]
        return max_num if max_num else 0