import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.server import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """模拟Agent实例"""
    with patch("app.api.routes.get_agent") as mock_get:
        agent = MagicMock()

        agent.tool_registry.list_tools.return_value = [
            "get_current_datetime",
            "read_text_file",
        ]
        agent.skills = {"paper_summary": {}, "code_debug": {}}

        agent.run.return_value = "测试回复"
        agent.get_memory_info.return_value = {
            "turn_count": 1,
            "message_count": 2,
        }

        mock_get.return_value = agent
        yield agent


def test_root(client):
    """验证根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Skills Agent API"


def test_health(client, mock_agent):
    """验证健康检查"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["tools_count"] == 2
    assert data["skills_count"] == 2


def test_list_tools(client, mock_agent):
    """验证工具列表"""
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert "get_current_datetime" in data["tools"]


def test_chat(client, mock_agent):
    """验证同步聊天"""
    response = client.post(
        "/api/v1/chat",
        json={"message": "你好"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "测试回复"
    assert data["turn_count"] == 1


def test_chat_empty_message(client, mock_agent):
    """验证空消息被拒绝"""
    response = client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    assert response.status_code == 422


def test_clear_memory(client, mock_agent):
    """验证清空记忆"""
    response = client.post("/api/v1/memory/clear")
    assert response.status_code == 200
    mock_agent.clear_memory.assert_called_once()


def test_memory_info(client, mock_agent):
    """验证记忆状态查询"""
    response = client.get("/api/v1/memory/info")
    assert response.status_code == 200
    data = response.json()
    assert data["turn_count"] == 1
    assert data["message_count"] == 2
