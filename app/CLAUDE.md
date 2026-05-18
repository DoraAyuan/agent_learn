[Root Directory](../CLAUDE.md) > **app/**

# app 模块

## Module Responsibilities

`app/` 是项目的核心应用模块，实现了完整的 AI Agent 工作流：

- CLI 交互入口与特殊命令
- Agent 核心调度（工具优先 → 技能回退）
- Function Calling 工具注册与分发
- RAG 知识库检索工具集成（跨项目、懒加载、优雅降级）
- 对话记忆管理（滑动窗口 + LLM摘要压缩）
- 技能文件的加载与 Markdown 解析
- 基于 LLM 的技能选择路由
- OpenAI 兼容 API 的通信封装（4种调用模式）
- FastAPI REST API 服务（同步+SSE流式）

## Entry and Startup

**主入口**：`app/main.py`

```bash
python -m app.main
```

**API 服务入口**：`app/server.py`

```bash
python -m app.server
# 或
uvicorn app.server:app --reload
```

启动流程：
1. `main()` 创建 `Agent` 实例
2. `Agent.__init__()` 加载所有技能文件、注册工具、创建对话记忆
3. 进入 `while True` 交互循环
4. 调用 `agent.run(user_input)` 执行完整流程

API 服务启动流程：
1. `create_app()` 创建 FastAPI 实例并配置 CORS
2. 首次请求时 `get_agent()` 懒创建 Agent 单例
3. `/api/v1/chat/stream` 端点通过线程+Queue桥接同步生成器与异步SSE

## 架构：工具优先，技能回退

```
用户输入
  --> file_reader(文件预处理)
  --> memory.add_user_message(存入记忆)
  --> _build_system_prompt(含工具说明+技能列表+对话摘要)
  --> memory.get_messages(获取历史)
  --> execute_tool_loop(LLM自主决策)
       --> tool_registry.execute(分发到工具)
       --> 工具结果回传LLM
  --> 流式输出
  --> memory.add_assistant_message(存入记忆)

回退路径: LLM未调用任何工具 --> skill_selector --> skill执行
```

## External Interfaces

### 用户交互接口
- CLI 输入输出（`input()` / `print()`）
- 支持直接文本输入和 `.txt` 文件路径输入
- 特殊命令：`/clear`、`/history`、`/tools`、`exit`/`quit`

### LLM API 接口
- 通过 OpenAI 兼容协议调用外部 LLM
- 四种调用模式：`chat()`, `chat_stream()`, `chat_with_tools()`, `execute_tool_loop()`
- 两种流式生成器：`chat_stream_yield()`, `execute_tool_loop_stream()`
- 超时设置：10 秒

### REST API 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/tools` | GET | 工具列表 |
| `/api/v1/chat` | POST | 同步聊天 |
| `/api/v1/chat/stream` | POST | SSE流式聊天 |
| `/api/v1/memory/clear` | POST | 清空记忆 |
| `/api/v1/memory/info` | GET | 记忆状态 |

## 已注册工具

| 工具名 | 类型 | 来源文件 |
|--------|------|----------|
| `get_current_datetime` | 基础 | `tools/datetime_tool.py` |
| `read_text_file` | 文件 | `tools/file_reader_tool.py` |
| `list_directory` | 文件 | `tools/file_reader_tool.py` |
| `rag_search` | RAG | `tools/rag_tool.py` |

## Key Dependencies and Configuration

### 外部依赖
| 包名 | 用途 |
|------|------|
| `openai` | OpenAI 兼容 API 客户端 |
| `python-dotenv` | `.env` 文件环境变量加载 |

### RAG 工具可选依赖
使用时需安装：`pyyaml`, `chromadb`, `langchain-community`, `langchain-ollama`, `langchain-core`, `sentence-transformers`, `pypdf`

### 环境变量
| 变量名 | 用途 | 必需 |
|--------|------|------|
| `MODEL_API_KEY` | LLM API 密钥 | 是 |
| `MODEL_BASE_URL` | LLM API 基础 URL | 是 |
| `MODEL_NAME` | 使用的模型名称 | 是 |

## Related File List

| 文件 | 职责 |
|------|------|
| `__init__.py` | 包初始化 |
| `main.py` | CLI入口，交互循环，特殊命令 |
| `agent.py` | Agent核心调度，工具注册，技能回退 |
| `llm_client.py` | OpenAI兼容API，4种调用模式 |
| `memory.py` | 对话记忆，滑动窗口+摘要压缩 |
| `config.py` | 环境变量统一配置管理 |
| `skill_loader.py` | 技能文件加载与Markdown解析 |
| `skill_selector.py` | LLM驱动的技能选择路由 |
| `tools/__init__.py` | 工具包子模块索引 |
| `tools/tool_registry.py` | 工具注册表，OpenAI tools schema生成 |
| `tools/datetime_tool.py` | 日期时间工具 |
| `tools/file_reader.py` | 本地文件路径解析与读取 |
| `tools/file_reader_tool.py` | 文件读取Function Calling工具 |
| `tools/rag_tool.py` | RAG检索工具，跨项目集成 |
| `server.py` | FastAPI服务入口，CORS配置 |
| `api/__init__.py` | API包初始化 |
| `api/schemas.py` | Pydantic请求/响应模型 |
| `api/routes.py` | API端点路由，SSE流式处理 |
| `test_llm.py` | LLM客户端测试 |
| `test_loader.py` | 技能加载测试 |
| `test_selector.py` | 技能选择测试 |
| `../demos/langgraph_agent.py` | LangGraph状态图Agent demo |
| `../demos/crewai_crew.py` | CrewAI多角色协作demo |
| `../tests/test_api.py` | API端点集成测试 |
| `../tests/test_memory.py` | 对话记忆单元测试 |
| `../tests/test_tools.py` | 工具注册表单元测试 |

## Change Log

| 日期 | 变更内容 |
|------|---------|
| 2026-05-14 | v1.0: FastAPI服务化、Docker容器化、pytest（20用例）、LangGraph/CrewAI demo |
| 2026-05-14 | v0.3: 全量代码按coding_standards.md规范化 |
| 2026-05-14 | v0.2: 新增Function Calling、RAG工具、对话记忆 |
| 2026-05-05 | v0.1: 初始化项目，技能选择+执行基础流程 |
