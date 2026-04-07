import sqlite3
import os
from contextlib import contextmanager

DB_FILE='personal_finance.db'

def init_db():
    if not os.path.exists(DB_FILE):
        conn=sqlite3.connect(DB_FILE)
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

def get_db_connection():
    conn=sqlite3.connect(DB_FILE)
    conn.row_factory=sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn=get_db_connection()
    try:
        yield conn
    except:
        conn.close()

init_db()