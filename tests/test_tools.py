from app.tools.tool_registry import ToolRegistry


def test_register_and_list():
    """验证工具注册和列表"""
    registry = ToolRegistry()

    def dummy_func(query: str) -> str:
        return f"结果: {query}"

    registry.register(
        name="test_tool",
        description="测试工具",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "查询内容"}
            },
            "required": ["query"],
        },
        func=dummy_func,
    )

    tools = registry.list_tools()
    assert "test_tool" in tools
    assert len(tools) == 1


def test_get_tools_schema():
    """验证OpenAI tools schema格式生成"""
    registry = ToolRegistry()

    registry.register(
        name="search",
        description="搜索文档",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["query"],
        },
        func=lambda query: "found",
    )

    schema = registry.get_tools_schema()
    assert len(schema) == 1

    tool = schema[0]
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "search"
    assert tool["function"]["description"] == "搜索文档"
    assert "query" in tool["function"]["parameters"]["properties"]


def test_execute():
    """验证工具执行分发"""
    registry = ToolRegistry()

    def add(a: int, b: int) -> str:
        return str(a + b)

    registry.register(
        name="add",
        description="加法",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
        },
        func=add,
    )

    result = registry.execute("add", {"a": 3, "b": 5})
    assert result == "8"


def test_execute_unknown_tool():
    """验证调用未注册工具时返回错误字符串"""
    registry = ToolRegistry()

    result = registry.execute("nonexistent", {})
    assert "错误" in result or "nonexistent" in result


def test_datetime_tool_registration():
    """验证datetime工具注册"""
    from app.tools.datetime_tool import register_datetime_tools

    registry = ToolRegistry()
    register_datetime_tools(registry)

    tools = registry.list_tools()
    assert "get_current_datetime" in tools

    result = registry.execute("get_current_datetime", {})
    assert len(result) > 0


def test_file_reader_tool_registration():
    """验证file_reader工具注册"""
    from app.tools.file_reader_tool import register_file_reader_tools

    registry = ToolRegistry()
    register_file_reader_tools(registry)

    tools = registry.list_tools()
    assert "read_text_file" in tools
    assert "list_directory" in tools
