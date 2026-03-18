from datetime import datetime
from database import get_db

def create_record(amount:float,category:str,remark:str='无'):
    record_date=datetime.now().strftime('%Y-%m-%d')
    create_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute(
            """INSERT INTO finance_records (amount, category,remark,record_date,create_time)
            VALUES (?, ?, ?, ?, ?)""",
            (amount, category, remark, record_date,create_time) #添加了create_time记得上面也要加上
        )
        conn.commit()
    return True

def get_records_by_year_month(year:int,month:int,page:int=1,page_size:int=5):
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
                WHERE record_date LIKE ?
            ''',(f'{date_prefix}%',))
        stats=cursor.fetchone()

        cursor.execute('''
            SELECT * FROM finance_records
            WHERE record_date LIKE ?
            ORDER BY record_date,id
            LIMIT ? OFFSET ?
        ''',(f'{date_prefix}%',page_size,offset))
        records=cursor.fetchall()

        return stats,records
    
def delete_record(record_id:int):
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM finance_records WHERE id=?',(record_id,))
        total=cursor.fetchone()[0]
        if total==0:
            return False
        cursor.execute('DELETE FROM finance_records WHERE id=?',(record_id,))
        conn.commit()
        return True
    
def clear_month_records(year:int,month:int):
    date_prefix=f'{year}-{month:02d}'
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM finance_records WHERE record_date LIKE ?',(f'{date_prefix}%',)
        )
        total=cursor.fetchone()[0]
        if total==0:
            return 0
        cursor.execute(
            'DELETE FROM finance_records WHERE record_date LIKE ?',(f'{date_prefix}%',)
        )
        conn.commit()
        return total
    
        