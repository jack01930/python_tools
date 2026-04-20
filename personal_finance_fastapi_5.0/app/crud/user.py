#app/crud/user.py
from datetime import datetime
from sqlite3 import IntegrityError

from app.config.database import get_db

def create_user(username:str,password_hash:str,email:str=None):
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor=conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO users (username, password_hash, email, create_time)
                VALUES (?, ?, ?, ?)""",
                (username, password_hash, email, now)
            )
            conn.commit()
            return cursor.lastrowid
        except IntegrityError as e:  # 精准捕获完整性约束异常
            if "UNIQUE" in str(e).upper():  # 不区分大小写匹配
                return None
            raise e
        except Exception as e:
            raise e
        
def get_user_by_username(username:str):
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?",(username,))
        user=cursor.fetchone()
        return user if user else None
        # return dict(user) if user else None
        # 因为conn.row_factory=sqlite3.Row

def get_user_by_id(id:int):
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?",(id,)) #将user_id改名为id
        user=cursor.fetchone()
        return user if user else None