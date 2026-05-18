import json
import queue
import asyncio
import threading
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.agent import Agent
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MemoryInfoResponse,
    ToolsResponse,
)

router = APIRouter()

_agent: Agent | None = None


def get_agent() -> Agent:
    """获取或创建全局Agent单例"""
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    agent = get_agent()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        tools_count=len(agent.tool_registry.list_tools()),
        skills_count=len(agent.skills),
    )


@router.get("/tools", response_model=ToolsResponse)
async def list_tools():
    """返回已注册的工具列表"""
    agent = get_agent()
    tools = agent.tool_registry.list_tools()
    return ToolsResponse(tools=tools, count=len(tools))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    同步聊天接口

    等待Agent完整处理后返回结果。
    """
    agent = get_agent()
    response = agent.run(request.message)
    info = agent.get_memory_info()

    return ChatResponse(
        response=response,
        turn_count=info["turn_count"],
        message_count=info["message_count"],
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE流式聊天接口

    在独立线程中运行Agent.run_stream()，通过Queue将事件实时传递给异步生成器。
    使用stdlib queue.Queue保证跨线程安全。

    事件格式:
    - event: tool_call   — 工具调用通知
    - event: tool_result — 工具执行结果
    - event: text        — 文本内容chunk
    - event: done        — 流式结束
    - event: error       — 错误信息
    """
    agent = get_agent()
    event_queue: queue.Queue = queue.Queue()
    _SENTINEL = None

    def _run_agent():
        """在线程中运行Agent并将事件推入Queue"""
        try:
            for event in agent.run_stream(request.message):
                event_queue.put(event)
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})
        finally:
            event_queue.put(_SENTINEL)

    thread = threading.Thread(target=_run_agent, daemon=True)
    thread.start()

    async def event_generator():
        loop = asyncio.get_event_loop()

        while True:
            event = await loop.run_in_executor(None, event_queue.get)

            if event is _SENTINEL:
                break

            event_type = event.get("type", "text")

            if event_type == "text":
                data = json.dumps(
                    {"content": event["content"]}, ensure_ascii=False
                )
            elif event_type in ("tool_call", "tool_result"):
                data = json.dumps(event, ensure_ascii=False)
            elif event_type == "error":
                data = json.dumps(
                    {"message": event["message"]}, ensure_ascii=False
                )
            elif event_type == "done":
                data = json.dumps(
                    {"full_response": event["full_response"]}, ensure_ascii=False
                )
            else:
                continue

            yield f"event: {event_type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/memory/clear")
async def clear_memory():
    """清空对话记忆"""
    agent = get_agent()
    agent.clear_memory()
    return {"status": "ok", "message": "对话记忆已清空"}


@router.get("/memory/info", response_model=MemoryInfoResponse)
async def memory_info():
    """查询当前对话记忆状态"""
    agent = get_agent()
    info = agent.get_memory_info()
    return MemoryInfoResponse(**info)
