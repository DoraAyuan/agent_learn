[Root Directory](../CLAUDE.md) > **tests/**

# tests 模块

## Module Responsibilities

`tests/` 目录包含项目的 pytest 自动化测试套件，覆盖三个核心关注点：

- **API 端点集成测试**：验证 FastAPI 路由的行为、状态码和响应结构
- **对话记忆单元测试**：验证 `ConversationMemory` 的消息管理、滑动窗口和 LLM 摘要压缩
- **工具注册表单元测试**：验证 `ToolRegistry` 的注册、schema 生成、执行分发和具体工具注册

所有测试通过 `conftest.py` 中的 `mock_env_vars` fixture 自动注入模拟环境变量，无需真实 `.env` 文件。

## Entry and Startup

```bash
# 运行全部测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_api.py -v
pytest tests/test_memory.py -v
pytest tests/test_tools.py -v
```

## Key Dependencies and Configuration

| 依赖 | 用途 |
|------|------|
| `pytest` | 测试框架 |
| `pytest-asyncio` | 异步测试支持（当前未使用，预留） |
| `httpx` | FastAPI TestClient 底层 HTTP 传输 |
| `unittest.mock` | 标准库 mock，用于模拟 LLMClient 和 Agent |

### 关键 Fixture（conftest.py）

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `mock_env_vars` | `autouse=True` | 自动为所有测试注入 `MODEL_API_KEY`、`MODEL_BASE_URL`、`MODEL_NAME` 模拟值 |
| `mock_llm_client` | 函数级 | 模拟 LLMClient 实例，`chat()` 返回 `"测试回复"` |
| `sample_messages` | 函数级 | 标准测试消息列表 `[{system, user}]` |

## Testing Details

### test_api.py (7 用例)

| 测试函数 | 验证目标 |
|---------|---------|
| `test_root` | 根路径 `/` 返回服务信息 |
| `test_health` | `/api/v1/health` 返回 ok 状态和正确的工具/技能计数 |
| `test_list_tools` | `/api/v1/tools` 返回已注册工具列表 |
| `test_chat` | `/api/v1/chat` 同步聊天返回正确回复和记忆状态 |
| `test_chat_empty_message` | 空消息被 422 拒绝 |
| `test_clear_memory` | `/api/v1/memory/clear` 调用 `agent.clear_memory()` |
| `test_memory_info` | `/api/v1/memory/info` 返回正确的记忆状态 |

使用 `mock_agent` fixture 模拟 `get_agent()`，避免创建真实 Agent 实例。

### test_memory.py (7 用例)

| 测试函数 | 验证目标 |
|---------|---------|
| `test_add_and_get_messages` | 消息添加和获取的基本流程 |
| `test_turn_and_message_count` | 轮数和消息计数的准确性 |
| `test_clear_memory` | 清空后轮数、消息数和摘要均归零 |
| `test_sliding_window` | `max_turns=2` 时只保留最近 4 条消息 |
| `test_add_tool_message` | 工具消息的 role/tool_call_id/name 正确存储 |
| `test_compression_triggered` | 超过 `summary_threshold` 时 LLM 摘要被调用 |
| `test_compression_not_triggered_below_threshold` | 低于阈值时不触发压缩 |

### test_tools.py (6 用例)

| 测试函数 | 验证目标 |
|---------|---------|
| `test_register_and_list` | 工具注册后出现在列表中 |
| `test_get_tools_schema` | 生成的 schema 符合 OpenAI function calling 格式 |
| `test_execute` | 工具执行分发返回正确结果 |
| `test_execute_unknown_tool` | 调用未注册工具返回错误字符串而非抛异常 |
| `test_datetime_tool_registration` | `datetime_tool` 注册并执行成功 |
| `test_file_reader_tool_registration` | `file_reader_tool` 注册了 `read_text_file` 和 `list_directory` |

## Related File List

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包初始化（空文件） |
| `conftest.py` | 共享 fixture：mock 环境变量、mock LLMClient、标准消息 |
| `test_api.py` | FastAPI 端点集成测试 |
| `test_memory.py` | ConversationMemory 单元测试 |
| `test_tools.py` | ToolRegistry 和具体工具单元测试 |

## Change Log

| 日期 | 变更内容 |
|------|---------|
| 2026-05-14 | 初始化模块 AI 上下文文档 |
