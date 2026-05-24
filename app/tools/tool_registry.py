from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    """
    单个工具的定义

    Attributes:
        name:        工具名称，LLM通过此名称调用工具
        description: 工具描述，帮助LLM理解何时使用
        parameters:  JSON Schema格式的参数定义
        callable:    实际执行的Python函数
    """
    name: str
    description: str
    parameters: dict
    callable: Callable


class ToolRegistry:
    """
    工具注册表

    管理所有可用工具，生成OpenAI function calling格式的tools列表，
    根据工具名称分发调用到对应函数。
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        func: Callable,
    ) -> None:
        """
        注册一个工具

        Args:
            name:        工具名称，唯一标识
            description: 工具功能描述
            parameters:  JSON Schema格式的参数定义
            func:        实际执行的函数
        """
        if name in self._tools:
            from app.logger import warning
            warning(f"工具'{name}'已存在，将被覆盖")

        self._tools[name] = Tool(
            name=name,
            description=description,
            parameters=parameters,
            callable=func
        )

    def get_tools_schema(self) -> list[dict]:
        """
        生成OpenAI function calling格式的tools列表

        Returns:
            OpenAI tools格式的列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self._tools.values()
        ]

    def execute(self, tool_name: str, arguments: dict) -> str:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数字典

        Returns:
            工具执行结果的字符串

        Raises:
            不抛出异常，工具不存在或执行失败时返回错误描述
        """
        if tool_name not in self._tools:
            return f"[错误] 未找到工具: {tool_name}"

        tool = self._tools[tool_name]

        try:
            result = tool.callable(**arguments)
            return str(result)
        except Exception as e:
            return f"[工具执行错误] {tool_name}: {e}"

    def list_tools(self) -> list[str]:
        """返回所有已注册工具的名称列表"""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._tools
