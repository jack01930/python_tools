#app/config/database.py
import sqlite3
import os
from contextlib import contextmanager

from app.config.logger import info as logger_info,error as logger_error
# 修复路径：从config目录往上找项目根目录
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))  # app/config/
APP_DIR = os.path.dirname(CONFIG_DIR)                    # app/
PROJECT_ROOT = os.path.dirname(APP_DIR)                  # 项目根目录
DB_FILE = os.path.join(PROJECT_ROOT, 'personal_finance.db')  # 数据库文件在项目根

def init_db():
    try:
        conn=sqlite3.connect(DB_FILE)
        conn.execute('PRAGMA foreign_keys=ON;') #开启外键约束
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            create_time TEXT NOT NULL
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS finance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            remark TEXT DEFAULT '无',
            record_date TEXT NOT NULL,
            create_time TEXT NOT NULL,
            user_id INTEGER REFERENCES users(id)
        );                  
        """)
        #给旧表加user_id（关联用户）
        # 3. 兼容低版本SQLite：先检查user_id列是否存在，不存在再添加
        # 4. 创建 AI 对话历史表
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            slots_filled TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        # 创建索引提升查询性能
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_session ON ai_conversation_history(user_id, session_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON ai_conversation_history(created_at);")
        logger_info("AI对话历史表初始化完成")
        cursor = conn.cursor()
        # 查询finance_records表的所有列名
        cursor.execute("PRAGMA table_info(finance_records);")
        columns = [col[1] for col in cursor.fetchall()]  # col[1]是列名
        
        if 'user_id' not in columns:
            # 列不存在，执行添加列操作（无IF NOT EXISTS）
            cursor.execute("""
            ALTER TABLE finance_records
            ADD COLUMN user_id INTEGER REFERENCES users(id);
            """)
            logger_info("已为finance_records表添加user_id列")
        else:
            logger_info("finance_records表已存在user_id列，无需重复添加")
        conn.commit()
        conn.close()
        logger_info("数据库初始化完成，表结构校验通过")
    except sqlite3.Error as e:
        logger_error(f"数据库初始化失败 | 信息：{str(e)}")
        raise e

def get_db_connection():
    conn=sqlite3.connect(DB_FILE)
    conn.row_factory=sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn=get_db_connection()
    try:
        yield conn
    except Exception as e:
        logger_error(f'数据库操作异常：| 信息：{str(e)}')
        conn.rollback() #异常时会回滚未提交事务
        raise e
    finally:
        conn.close()