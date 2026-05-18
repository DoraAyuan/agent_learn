import json
from typing import Callable, Generator, Optional
from openai import OpenAI
from app.config import get_settings


class LLMClient:
    """
    OpenAI兼容API客户端

    支持四种调用模式: chat, chat_stream, chat_with_tools, execute_tool_loop
    """

    def __init__(self) -> None:
        """
        从.env读取配置并创建OpenAI兼容客户端
        """
        config = get_settings()

        self.client = OpenAI(
            api_key=config["MODEL_API_KEY"],
            base_url=config["MODEL_BASE_URL"],
            timeout=120,
        )

        self.model = config["MODEL_NAME"]

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """
        非流式调用，一次性返回完整回答文本

        Args:
            messages:    消息列表
            temperature: 温度参数

        Returns:
            模型回复文本，content为None时返回空字符串
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )

        content = response.choices[0].message.content

        if content is None:
            return ""

        return content

    def chat_stream(self, messages: list, temperature: float = 0.7) -> str:
        """
        流式调用，边接收边打印，返回完整文本

        Args:
            messages:    消息列表
            temperature: 温度参数

        Returns:
            拼接后的完整回复文本
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        full_response = ""

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)

            if content:
                print(content, end="", flush=True)
                full_response += content

        print()
        return full_response

    def chat_with_tools(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.7,
    ) -> dict:
        """
        支持function calling的非流式调用

        Args:
            messages:    消息列表
            tools:       OpenAI function calling格式的工具列表
            temperature: 温度参数

        Returns:
            包含content, tool_calls, message三个字段的字典
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        # 提取reasoning_content（MiMo等推理模型需要在多轮中回传）
        reasoning_content = getattr(message, "reasoning_content", None)

        return {
            "content": message.content,
            "tool_calls": message.tool_calls,
            "message": message,
            "reasoning_content": reasoning_content,
        }

    def execute_tool_loop(
        self,
        messages: list,
        tools: list,
        tool_executor: Callable[[str, dict], str],
        max_rounds: int = 5,
        temperature: float = 0.7,
    ) -> str:
        """
        自动执行tool calling循环

        调用LLM后，如果返回tool_calls则逐个执行并回传结果，直到LLM返回文本回复。

        Args:
            messages:       初始消息列表
            tools:          OpenAI function calling格式的工具列表
            tool_executor:  工具执行函数，签名为 (tool_name, arguments) -> str
            max_rounds:     最大循环轮数
            temperature:    温度参数

        Returns:
            最终的文本回复
        """
        current_messages = list(messages)

        for round_num in range(max_rounds):
            result = self.chat_with_tools(
                current_messages, tools=tools, temperature=temperature
            )

            # 模型返回文本，流程结束
            if result["content"] and not result["tool_calls"]:
                return result["content"]

            # 模型要求调用工具
            if result["tool_calls"]:
                assistant_msg = {
                    "role": "assistant",
                    "content": result["content"] or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in result["tool_calls"]
                    ]
                }
                # MiMo等推理模型需要回传reasoning_content
                if result.get("reasoning_content"):
                    assistant_msg["reasoning_content"] = result["reasoning_content"]
                current_messages.append(assistant_msg)

                for tool_call in result["tool_calls"]:
                    func_name = tool_call.function.name

                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    print(f"\n[Tool] 调用{func_name}({arguments})")

                    tool_result = tool_executor(func_name, arguments)
                    print(f"[Tool] {func_name}返回: {tool_result[:200]}")

                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                continue

            # content和tool_calls都为空
            return result["content"] or ""

        print(f"\n[警告] 工具调用已达到最大轮数({max_rounds})，强制返回")
        return result.get("content") or ""

    def chat_stream_yield(
        self, messages: list, temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        流式调用生成器版本，逐块yield文本而非直接打印

        Args:
            messages:    消息列表
            temperature: 温度参数

        Yields:
            每个文本chunk
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)

            if content:
                yield content

    def execute_tool_loop_stream(
        self,
        messages: list,
        tools: list,
        tool_executor: Callable[[str, dict], str],
        max_rounds: int = 5,
        temperature: float = 0.7,
    ) -> Generator[dict, None, None]:
        """
        execute_tool_loop的生成器版本，逐事件yield

        工具调用阶段为非流式，最终文本回复为流式逐块yield。

        Args:
            messages:       初始消息列表
            tools:          OpenAI function calling格式的工具列表
            tool_executor:  工具执行函数，签名为 (tool_name, arguments) -> str
            max_rounds:     最大循环轮数
            temperature:    温度参数

        Yields:
            事件字典:
            - {"type": "tool_call", "tool_name": str, "arguments": dict, "round": int}
            - {"type": "tool_result", "tool_name": str, "result": str, "round": int}
            - {"type": "text", "content": str}
            - {"type": "error", "message": str}
        """
        current_messages = list(messages)

        for round_num in range(max_rounds):
            result = self.chat_with_tools(
                current_messages, tools=tools, temperature=temperature
            )

            if result["content"] and not result["tool_calls"]:
                yield {"type": "text", "content": result["content"]}
                return

            if result["tool_calls"]:
                assistant_msg = {
                    "role": "assistant",
                    "content": result["content"] or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in result["tool_calls"]
                    ]
                }
                # MiMo等推理模型需要回传reasoning_content
                if result.get("reasoning_content"):
                    assistant_msg["reasoning_content"] = result["reasoning_content"]
                current_messages.append(assistant_msg)

                for tool_call in result["tool_calls"]:
                    func_name = tool_call.function.name

                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    yield {
                        "type": "tool_call",
                        "tool_name": func_name,
                        "arguments": arguments,
                        "round": round_num + 1,
                    }

                    try:
                        tool_result = tool_executor(func_name, arguments)
                    except Exception as e:
                        tool_result = f"工具执行出错: {e}"

                    yield {
                        "type": "tool_result",
                        "tool_name": func_name,
                        "result": tool_result,
                        "round": round_num + 1,
                    }

                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                continue

            if result["content"]:
                yield {"type": "text", "content": result["content"]}
            return

        yield {"type": "text", "content": result.get("content") or ""}
