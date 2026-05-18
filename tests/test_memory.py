from unittest.mock import MagicMock
from app.memory import ConversationMemory


def test_add_and_get_messages():
    """验证消息添加和获取"""
    memory = ConversationMemory(max_turns=10)

    memory.add_user_message("你好")
    memory.add_assistant_message("你好！有什么可以帮助你的？")

    messages = memory.get_messages()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[1]["role"] == "assistant"


def test_turn_and_message_count():
    """验证轮数和消息计数"""
    memory = ConversationMemory(max_turns=10)

    assert memory.turn_count == 0
    assert memory.message_count == 0

    memory.add_user_message("问题1")
    memory.add_assistant_message("回答1")
    memory.add_user_message("问题2")

    assert memory.turn_count == 2
    assert memory.message_count == 3


def test_clear_memory():
    """验证清空记忆"""
    memory = ConversationMemory(max_turns=10)

    memory.add_user_message("测试")
    memory.add_assistant_message("回复")
    memory.clear()

    assert memory.turn_count == 0
    assert memory.message_count == 0
    assert memory.get_summary() == ""


def test_sliding_window():
    """验证滑动窗口只保留最近的消息"""
    memory = ConversationMemory(max_turns=2)

    for i in range(5):
        memory.add_user_message(f"用户消息{i}")
        memory.add_assistant_message(f"助手消息{i}")

    messages = memory.get_messages()

    assert len(messages) <= 4


def test_add_tool_message():
    """验证工具消息添加"""
    memory = ConversationMemory(max_turns=10)

    memory.add_tool_message("call_123", "get_time", "当前时间是12:00")

    messages = memory.get_messages()
    assert len(messages) == 1
    assert messages[0]["role"] == "tool"
    assert messages[0]["tool_call_id"] == "call_123"
    assert messages[0]["name"] == "get_time"


def test_compression_triggered():
    """验证超过阈值时触发压缩"""
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "这是对话摘要"

    memory = ConversationMemory(
        llm=mock_llm, max_turns=10, summary_threshold=6
    )

    for i in range(4):
        memory.add_user_message(f"消息{i}")
        memory.add_assistant_message(f"回复{i}")

    assert memory.get_summary() == "这是对话摘要"
    assert mock_llm.chat.called


def test_compression_not_triggered_below_threshold():
    """验证低于阈值时不触发压缩"""
    mock_llm = MagicMock()

    memory = ConversationMemory(
        llm=mock_llm, max_turns=10, summary_threshold=20
    )

    memory.add_user_message("你好")
    memory.add_assistant_message("你好！")

    assert memory.get_summary() == ""
    assert not mock_llm.chat.called
