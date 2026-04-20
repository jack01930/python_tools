import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config.logger import error as logger_error, info as logger_info
from app.config.database import get_db_connection


def save_message(
    user_id: int,
    session_id: str,
    role: str,
    content: str,
    slots_filled: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """保存一条对话消息到数据库"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_conversation_history
            (user_id, session_id, role, content, slots_filled, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            session_id,
            role,
            content,
            json.dumps(slots_filled, ensure_ascii=False) if slots_filled else None,
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        logger_info(f"[LongMemory.Storage] 保存消息成功 | user_id:{user_id} | role:{role}")
        return True
    except sqlite3.Error as e:
        logger_error(f"[LongMemory.Storage] 保存消息失败 | user_id:{user_id} | error:{repr(e)}")
        return False
    except Exception as e:
        logger_error(f"[LongMemory.Storage] 保存消息异常 | user_id:{user_id} | error:{repr(e)}")
        return False


def get_recent_messages(
    user_id: int,
    session_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """获取指定会话最近的对话消息"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT role, content, slots_filled, metadata, created_at
            FROM ai_conversation_history
            WHERE user_id = ? AND session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, session_id, limit))

        rows = cursor.fetchall()
        conn.close()

        # 反转顺序，按时间正序排列
        messages = []
        for row in reversed(rows):
            messages.append({
                "role": row["role"],
                "content": row["content"],
                "slots_filled": json.loads(row["slots_filled"]) if row["slots_filled"] else {},
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"]
            })

        return messages
    except sqlite3.Error as e:
        logger_error(f"[LongMemory.Storage] 获取消息失败 | user_id:{user_id} | error:{repr(e)}")
        return []
    except Exception as e:
        logger_error(f"[LongMemory.Storage] 获取消息异常 | user_id:{user_id} | error:{repr(e)}")
        return []


def get_session_slots(
    user_id: int,
    session_id: str
) -> Dict[str, Any]:
    """获取当前会话已填充的所有槽位"""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT slots_filled
            FROM ai_conversation_history
            WHERE user_id = ? AND session_id = ? AND slots_filled IS NOT NULL
        """, (user_id, session_id))

        rows = cursor.fetchall()
        conn.close()

        # 合并所有槽位，后出现的覆盖先出现的
        merged_slots = {}
        for row in rows:
            if row["slots_filled"]:
                try:
                    slots = json.loads(row["slots_filled"])
                    merged_slots.update(slots)
                except json.JSONDecodeError:
                    continue

        return merged_slots
    except sqlite3.Error as e:
        logger_error(f"[LongMemory.Storage] 获取槽位失败 | user_id:{user_id} | error:{repr(e)}")
        return {}
    except Exception as e:
        logger_error(f"[LongMemory.Storage] 获取槽位异常 | user_id:{user_id} | error:{repr(e)}")
        return {}