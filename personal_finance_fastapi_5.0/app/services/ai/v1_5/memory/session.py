import uuid
from datetime import datetime
from typing import Optional


def generate_session_id(user_id: int, existing_session_id: Optional[str] = None) -> str:
    """
    生成会话ID

    格式: {user_id}_{date}_{random}
    例如: 1_20240101_abcd1234

    如果已有session_id，则返回原值（保持会话连续）
    """
    if existing_session_id and existing_session_id.strip():
        return existing_session_id.strip()

    date_str = datetime.now().strftime("%Y%m%d")
    random_str = str(uuid.uuid4())[:8]  # 取前8位随机字符
    return f"{user_id}_{date_str}_{random_str}"


def parse_session_id(session_id: str) -> dict:
    """
    解析会话ID，提取信息

    返回: {
        "user_id": int or None,
        "date": str or None,
        "random": str or None,
        "valid": bool
    }
    """
    if not session_id or "_" not in session_id:
        return {"valid": False}

    parts = session_id.split("_")
    if len(parts) != 3:
        return {"valid": False}

    try:
        user_id = int(parts[0])
        date_str = parts[1]
        random_str = parts[2]

        # 验证日期格式
        datetime.strptime(date_str, "%Y%m%d")

        return {
            "user_id": user_id,
            "date": date_str,
            "random": random_str,
            "valid": True
        }
    except (ValueError, TypeError):
        return {"valid": False}