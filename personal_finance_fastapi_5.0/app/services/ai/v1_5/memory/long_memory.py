import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config.logger import info as logger_info, error as logger_error
from app.core.llm.client import create_llm_client

from .storage import save_message, get_recent_messages, get_session_slots
from .session import generate_session_id
from .summary import format_conversations, generate_history_summary


class LongMemory:
    """长期记忆管理器"""

    def __init__(self, user_id: int, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = generate_session_id(user_id, session_id)
        self._llm_client = None

    @property
    def llm_client(self):
        """延迟加载 LLM 客户端"""
        if self._llm_client is None:
            try:
                self._llm_client = create_llm_client()
            except Exception as e:
                logger_error(f"[LongMemory] 创建LLM客户端失败 | error:{repr(e)}")
                self._llm_client = None
        return self._llm_client

    def save_message(
        self,
        role: str,
        content: str,
        slots_filled: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """保存一条对话消息"""
        return save_message(
            user_id=self.user_id,
            session_id=self.session_id,
            role=role,
            content=content,
            slots_filled=slots_filled,
            metadata=metadata
        )

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的对话历史"""
        return get_recent_messages(
            user_id=self.user_id,
            session_id=self.session_id,
            limit=limit
        )

    def get_session_slots(self) -> Dict[str, Any]:
        """获取当前会话已填充的所有槽位"""
        return get_session_slots(
            user_id=self.user_id,
            session_id=self.session_id
        )

    def generate_context(
        self,
        max_recent: int = 5,
        max_total: int = 20
    ) -> str:
        """
        生成历史上下文，用于注入 prompt

        策略：
        1. 获取最多 max_total 条历史记录
        2. 如果记录数 <= max_recent，直接格式化返回
        3. 否则，最近 max_recent 条完整显示，更早的生成摘要
        """
        all_conversations = self.get_recent_conversations(limit=max_total)

        if not all_conversations:
            return "无历史对话。"

        if len(all_conversations) <= max_recent:
            # 历史较少，直接完整显示
            return format_conversations(all_conversations)

        # 分割：最近 N 轮完整，更早的生成摘要
        recent = all_conversations[-max_recent:]
        older = all_conversations[:-max_recent]

        summary = generate_history_summary(older, self.llm_client)
        recent_text = format_conversations(recent)

        return f"历史摘要（较早对话）：\n{summary}\n\n最近对话：\n{recent_text}"

    def update_slots_from_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> bool:
        """
        从工具调用结果中提取已填充槽位并保存

        目前仅处理 add_record 工具
        """
        if tool_name != "add_record":
            return False

        try:
            slots = {}
            if "amount" in tool_input:
                slots["amount"] = tool_input["amount"]
            if "category" in tool_input:
                slots["category"] = tool_input["category"]
            if "remark" in tool_input:
                slots["remark"] = tool_input["remark"]

            if slots:
                return self.save_message(
                    role="system",
                    content=f"工具调用成功: {tool_name}",
                    slots_filled=slots,
                    metadata={"tool": tool_name}
                )
            return False
        except Exception as e:
            logger_error(f"[LongMemory] 更新槽位失败 | error:{repr(e)}")
            return False


def create_long_memory(user_id: int, session_id: Optional[str] = None) -> LongMemory:
    """工厂函数，创建 LongMemory 实例"""
    return LongMemory(user_id, session_id)