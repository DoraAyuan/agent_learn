from typing import Optional
from app.llm_client import LLMClient
from app.logger import info, error


class ConversationMemory:
    """
    对话记忆管理器

    维护消息历史，支持滑动窗口和LLM摘要压缩。

    Attributes:
        _messages:           完整消息历史
        _summary:            旧对话的摘要文本
        _max_turns:          保留的最大轮数
        _summary_threshold:  触发摘要压缩的消息数量阈值
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        max_turns: int = 10,
        summary_threshold: int = 20,
    ) -> None:
        """
        Args:
            llm:               LLMClient实例，用于摘要压缩
            max_turns:         滑动窗口保留的最大轮数
            summary_threshold: 触发摘要压缩的消息数量阈值
        """
        self._messages: list[dict] = []
        self._summary: str = ""
        self._llm = llm
        self._max_turns = max_turns
        self._summary_threshold = summary_threshold

    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self._messages.append({
            "role": "user",
            "content": content
        })
        self._maybe_compress()

    def add_assistant_message(self, content: str) -> None:
        """添加助手回复消息"""
        self._messages.append({
            "role": "assistant",
            "content": content
        })

    def add_tool_message(
        self, tool_call_id: str, name: str, content: str
    ) -> None:
        """
        添加工具调用结果消息

        Args:
            tool_call_id: 与assistant消息中tool_calls对应的ID
            name:         工具名称
            content:      工具执行结果
        """
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content,
        })

    def get_messages(self) -> list[dict]:
        """
        获取用于LLM调用的近期消息列表

        Returns:
            最近max_turns轮的消息
        """
        window_size = self._max_turns * 2
        if len(self._messages) > window_size:
            recent = self._messages[-window_size:]
        else:
            recent = self._messages
        return list(recent)

    def get_summary(self) -> str:
        """返回对话摘要文本"""
        return self._summary

    def clear(self) -> None:
        """清空所有记忆"""
        self._messages.clear()
        self._summary = ""

    @property
    def turn_count(self) -> int:
        """当前对话轮数"""
        return sum(1 for m in self._messages if m["role"] == "user")

    @property
    def message_count(self) -> int:
        """当前消息总数"""
        return len(self._messages)

    def _maybe_compress(self) -> None:
        """
        检查是否需要压缩历史

        超过summary_threshold时取前半部分消息用LLM生成摘要，保留后半部分。
        """
        if not self._llm:
            return

        if len(self._messages) < self._summary_threshold:
            return

        split_point = len(self._messages) // 2
        old_messages = self._messages[:split_point]

        conversation_text = self._format_messages_for_summary(old_messages)

        summary_prompt = [
            {
                "role": "system",
                "content": (
                    "你是一个对话摘要助手。请将以下对话历史压缩成简洁的摘要，"
                    "保留关键信息（用户的问题、讨论的主题、重要的结论）。"
                    "摘要不超过200字。"
                )
            },
            {
                "role": "user",
                "content": f"请总结以下对话:\n\n{conversation_text}"
            }
        ]

        try:
            new_summary = self._llm.chat(summary_prompt, temperature=0.3)

            if self._summary:
                self._summary = f"{self._summary}\n{new_summary}"
            else:
                self._summary = new_summary

            self._messages = self._messages[split_point:]
            info(f"对话已压缩: {split_point}条→摘要，保留{len(self._messages)}条")

        except Exception as e:
            error(f"对话压缩失败: {e}")

    def _format_messages_for_summary(self, messages: list[dict]) -> str:
        """将消息列表格式化为可读文本用于摘要"""
        parts = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "user":
                parts.append(f"用户: {content}")
            elif role == "assistant":
                parts.append(f"助手: {content}")
            elif role == "tool":
                name = msg.get("name", "unknown")
                parts.append(f"[工具{name}]: {content[:100]}")

        return "\n".join(parts)
