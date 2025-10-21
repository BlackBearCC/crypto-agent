# -*- coding: utf-8 -*-
"""
会话管理器 - 管理多轮对话和上下文压缩
"""

import threading
from typing import List, Dict, Optional, Any
from datetime import datetime

from database import DatabaseManager


class SessionManager:
    """对话会话管理器 - 数据库持久化"""

    def __init__(self, llm_client, db_manager: DatabaseManager):
        """
        初始化会话管理器

        Args:
            llm_client: LLM客户端，用于概要生成
            db_manager: 数据库管理器
        """
        self.llm_client = llm_client
        self.db_manager = db_manager
        self.cache = {}
        print("Session manager initialized")

    def get_history(self, chat_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        获取对话历史

        Args:
            chat_id: 聊天ID
            limit: 获取最近N条消息

        Returns:
            消息列表 [{'role': 'user', 'content': '...'}, ...]
        """
        if chat_id in self.cache:
            return self.cache[chat_id]

        messages_orm = self.db_manager.get_chat_history(chat_id, limit=limit)
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages_orm
        ]

        self.cache[chat_id] = history
        return history

    def add_message(self, chat_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加消息到历史并保存到数据库

        Args:
            chat_id: 聊天ID
            role: 角色 ('user', 'assistant', 'system')
            content: 消息内容
            metadata: 额外元数据
        """
        round_number = self._get_next_round(chat_id, role)

        self.db_manager.save_chat_message(
            chat_id=chat_id,
            role=role,
            content=content,
            round_number=round_number,
            is_summary=False,
            metadata=metadata
        )

        if chat_id not in self.cache:
            self.cache[chat_id] = []
        self.cache[chat_id].append({'role': role, 'content': content})

        print(f"Message saved: chat={chat_id}, round={round_number}, role={role}")

    def _get_next_round(self, chat_id: str, role: str) -> int:
        """
        获取下一个轮次编号

        Args:
            chat_id: 聊天ID
            role: 当前角色

        Returns:
            轮次编号
        """
        current_round = self.db_manager.get_chat_round_count(chat_id)

        if role == 'user':
            return current_round + 1
        else:
            return current_round if current_round > 0 else 1

    def check_and_compress(self, chat_id: str):
        """
        检查是否需要压缩对话历史

        Args:
            chat_id: 聊天ID
        """
        round_count = self.db_manager.get_chat_round_count(chat_id)

        if round_count >= 5:
            print(f"Triggering compression for chat {chat_id}, round count: {round_count}")
            threading.Thread(
                target=self._async_summarize,
                args=(chat_id, round_count),
                daemon=True
            ).start()

    def _async_summarize(self, chat_id: str, current_round: int):
        """
        异步概要1-4轮对话

        Args:
            chat_id: 聊天ID
            current_round: 当前轮数
        """
        try:
            print(f"Starting compression for chat {chat_id}...")

            messages_to_summarize = self.db_manager.get_chat_messages_by_rounds(
                chat_id, round_start=1, round_end=4
            )

            if not messages_to_summarize:
                print(f"No messages to summarize for chat {chat_id}")
                return

            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in messages_to_summarize
            ])

            summary_prompt = f"""请简要概括以下对话的关键信息（用户需求、已完成操作、重要结论）：

{conversation_text}

用3-5句话总结核心内容。"""

            summary = self.llm_client.call(
                system_prompt_or_full_prompt=summary_prompt,
                agent_name='对话概要'
            )

            self.db_manager.save_chat_message(
                chat_id=chat_id,
                role='system',
                content=f"[历史对话概要] {summary}",
                round_number=current_round,
                is_summary=True
            )

            self.db_manager.archive_chat_messages(chat_id, round_start=1, round_end=4)

            if chat_id in self.cache:
                del self.cache[chat_id]

            print(f"Compression completed: chat {chat_id}, rounds 1-4 archived")

        except Exception as e:
            print(f"Compression error for chat {chat_id}: {e}")
            import traceback
            traceback.print_exc()

    def clear_cache(self, chat_id: Optional[str] = None):
        """
        清空缓存

        Args:
            chat_id: 指定聊天ID，None则清空全部
        """
        if chat_id:
            if chat_id in self.cache:
                del self.cache[chat_id]
        else:
            self.cache.clear()

    def get_session_stats(self, chat_id: str) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            chat_id: 聊天ID

        Returns:
            统计信息字典
        """
        round_count = self.db_manager.get_chat_round_count(chat_id)
        history = self.get_history(chat_id)

        return {
            'chat_id': chat_id,
            'round_count': round_count,
            'message_count': len(history),
            'cached': chat_id in self.cache
        }
