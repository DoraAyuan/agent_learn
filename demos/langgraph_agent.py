"""
LangGraph 状态图 Agent 演示

展示核心概念:
- StateGraph: 状态图定义工作流
- Node: 节点封装处理逻辑
- Conditional Edge: 条件边实现分支路由
- Tool Calling: LLM自动调用工具

架构:
    START --> llm_call ──(有tool_calls)──> tool_node --> llm_call
                │                                        │
                └──(无tool_calls)──> END  <──────────────┘

运行方式:
    python -m demos.langgraph_agent
    python -m demos.langgraph_agent "计算 15 乘以 7 再除以 3"
"""
import operator
import os
import sys
from typing import Literal

# Windows GBK 编码无法输出中文和特殊字符，强制 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import Annotated, TypedDict


class ChatMiMo(ChatOpenAI):
    """
    ChatOpenAI 子类，支持 MiMo 推理模型的 reasoning_content 回传。

    MiMo 思考模式要求在多轮对话中将 reasoning_content 传递回 API，
    但 LangChain 默认不处理这个非标准字段。
    - _create_chat_result: 从原始响应提取 reasoning_content 存入 additional_kwargs
    - _get_request_payload: 将 additional_kwargs 中的 reasoning_content 注入请求
    """

    def _create_chat_result(self, response, generation_info=None):
        result = super()._create_chat_result(response, generation_info)
        # 从原始响应的message中提取reasoning_content
        if result.generations:
            gen = result.generations[0]
            try:
                raw_msg = response.choices[0].message
                reasoning = getattr(raw_msg, "reasoning_content", None)
                if reasoning:
                    gen.message.additional_kwargs["reasoning_content"] = reasoning
            except (AttributeError, IndexError, TypeError):
                pass
        return result

    def _get_request_payload(self, input_, *, stop=None, **kwargs):
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        if isinstance(input_, list):
            # 索引对应：payload["messages"][i] 由 input_[i] 转换而来
            msg_dicts = payload.get("messages", [])
            for i, msg in enumerate(input_):
                if isinstance(msg, AIMessage) and i < len(msg_dicts):
                    reasoning = msg.additional_kwargs.get("reasoning_content")
                    if reasoning:
                        msg_dicts[i]["reasoning_content"] = reasoning
        return payload

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import get_settings


# ============================================================
# Step 1: 定义工具
# ============================================================

@tool
def add(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """计算两个数的积"""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """计算两个数的商"""
    if b == 0:
        return 0.0
    return a / b


TOOLS = [add, multiply, divide]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ============================================================
# Step 2: 初始化模型并绑定工具
# ============================================================

def _create_model() -> ChatMiMo:
    """从项目配置创建ChatMiMo实例（兼容MiMo推理模型的reasoning_content）"""
    config = get_settings()
    return ChatMiMo(
        api_key=config["MODEL_API_KEY"],
        base_url=config["MODEL_BASE_URL"],
        model=config["MODEL_NAME"],
        temperature=0,
        timeout=120,
    )


model = _create_model()
model_with_tools = model.bind_tools(TOOLS)


# ============================================================
# Step 3: 定义状态
# ============================================================

class AgentState(TypedDict):
    """
    Agent状态

    messages: 消息列表，使用operator.add自动追加新消息
    llm_calls: LLM调用计数器
    """
    messages: Annotated[list, operator.add]
    llm_calls: int


# ============================================================
# Step 4: 定义节点
# ============================================================

def llm_call(state: AgentState) -> dict:
    """
    LLM调用节点

    将系统提示和历史消息一起发送给LLM，LLM自主决定是调用工具还是直接回答。
    自动处理MiMo推理模型的reasoning_content回传。
    """
    response = model_with_tools.invoke(
        [SystemMessage(content="你是一个数学计算助手，可以使用工具进行加法、乘法和除法运算。请用中文回答。")]
        + state["messages"]
    )
    # 提取reasoning_content保存到additional_kwargs，供下一轮回传
    response_meta = response.response_metadata or {}
    reasoning = response_meta.get("reasoning_content")
    if reasoning:
        response.additional_kwargs["reasoning_content"] = reasoning

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: AgentState) -> dict:
    """
    工具执行节点

    遍历最后一条消息中的tool_calls，逐个执行并收集结果。
    """
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = TOOLS_BY_NAME[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}


# ============================================================
# Step 5: 定义条件路由
# ============================================================

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    """
    条件边: 判断是否继续调用工具

    如果LLM返回了tool_calls，则路由到tool_node执行工具；
    否则路由到END，流程结束。
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_node"
    return "__end__"


# ============================================================
# Step 6: 构建状态图
# ============================================================

def build_agent() -> StateGraph:
    """
    构建并编译LangGraph Agent

    图结构:
        START --> llm_call ──(tool_calls)──> tool_node --> llm_call
                    │                                     │
                    └──(no tool_calls)──> END <────────────┘

    Returns:
        编译后的可执行Agent
    """
    graph = StateGraph(AgentState)

    graph.add_node("llm_call", llm_call)
    graph.add_node("tool_node", tool_node)

    graph.add_edge(START, "llm_call")
    graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    graph.add_edge("tool_node", "llm_call")

    return graph.compile()


# ============================================================
# 主程序
# ============================================================

def main() -> None:
    """运行LangGraph Agent演示"""
    agent = build_agent()

    query = sys.argv[1] if len(sys.argv) > 1 else "请计算 (3 + 5) * 12 的结果"

    print("=" * 50)
    print("LangGraph Agent 演示")
    print("=" * 50)
    print(f"\n用户输入: {query}")
    print(f"\n图结构: START --> llm_call <--> tool_node --> END")
    print("-" * 50)

    result = agent.invoke({"messages": [HumanMessage(content=query)]})

    print("\n" + "=" * 50)
    print("执行路径:")
    for i, msg in enumerate(result["messages"]):
        role = msg.__class__.__name__.replace("Message", "")
        content = msg.content[:100] if msg.content else ""
        tool_calls = ""
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            calls = [f"{tc['name']}({tc['args']})" for tc in msg.tool_calls]
            tool_calls = f" -> tool_calls: {', '.join(calls)}"
        print(f"  [{i+1}] {role}: {content}{tool_calls}")

    print(f"\nLLM调用次数: {result.get('llm_calls', 0)}")

    final = result["messages"][-1].content
    print(f"\n最终回答: {final}")
    print("=" * 50)


if __name__ == "__main__":
    main()
