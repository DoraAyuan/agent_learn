import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# 确保项目根目录在sys.path中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_env_vars():
    """为所有测试提供模拟环境变量，避免读取真实.env"""
    env = {
        "MODEL_API_KEY": "test-key",
        "MODEL_BASE_URL": "http://localhost:1234/v1",
        "MODEL_NAME": "test-model",
    }
    with patch.dict(os.environ, env, clear=False):
        yield env


@pytest.fixture
def mock_llm_client():
    """模拟LLMClient，不发送真实API请求"""
    client = MagicMock()
    client.model = "test-model"
    client.chat.return_value = "测试回复"
    client.chat_stream.return_value = "流式测试回复"
    client.chat_stream.return_value = "流式测试回复"
    return client


@pytest.fixture
def sample_messages():
    """标准测试消息列表"""
    return [
        {"role": "system", "content": "你是一个AI助手"},
        {"role": "user", "content": "你好"},
    ]
