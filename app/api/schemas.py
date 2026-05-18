from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求体"""
    message: str = Field(..., min_length=1, description="用户消息内容")


class ChatResponse(BaseModel):
    """同步聊天响应体"""
    response: str = Field(..., description="Agent的回答文本")
    turn_count: int = Field(..., description="当前对话轮数")
    message_count: int = Field(..., description="当前消息总数")


class MemoryInfoResponse(BaseModel):
    """记忆状态响应体"""
    turn_count: int
    message_count: int


class HealthResponse(BaseModel):
    """健康检查响应体"""
    status: str = "ok"
    version: str = "1.0.0"
    tools_count: int = 0
    skills_count: int = 0


class ToolsResponse(BaseModel):
    """工具列表响应体"""
    tools: list[str]
    count: int
