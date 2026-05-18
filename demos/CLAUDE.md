[Root Directory](../CLAUDE.md) > **demos/**

# demos 模块

## Module Responsibilities

`demos/` 目录包含两个主流 Agent 框架的对照演示，用于展示不同 Agent 架构风格与本项目手写实现的对比：

- **LangGraph 状态图 Agent**：展示 `StateGraph` + 条件边 + 工具调用的有状态工作流
- **CrewAI 多角色协作**：展示多 Agent 角色分工（研究员 -> 作家 -> 编辑）的顺序协作流程

两个 demo 均复用项目的 `app/config.py` 配置管理，共享同一套 LLM API 密钥。

## Entry and Startup

```bash
# LangGraph 状态图 Agent demo
python -m demos.langgraph_agent
python -m demos.langgraph_agent "计算 15 乘以 7 再除以 3"

# CrewAI 多角色协作 demo
python -m demos.crewai_crew
python -m demos.crewai_crew "请写一篇关于AI在教育领域应用的短文"
```

## langgraph_agent.py 详解

### 架构

```
START --> llm_call ──(有 tool_calls)──> tool_node --> llm_call
            │                                       |
            └──(无 tool_calls)──> END <─────────────┘
```

### 核心概念

| 概念 | 实现 |
|------|------|
| `StateGraph` | 定义 `AgentState`（messages + llm_calls） |
| Node | `llm_call`（LLM 决策）、`tool_node`（工具执行） |
| Conditional Edge | `should_continue()` 判断是否继续调用工具 |
| Tool | `@tool` 装饰器定义 `add`、`multiply`、`divide` |

### 依赖

| 包名 | 用途 |
|------|------|
| `langgraph` | 状态图框架 |
| `langchain-openai` | ChatOpenAI 模型封装 |
| `langchain-core` | 消息类型和工具定义 |

## crewai_crew.py 详解

### 角色设计

```
研究员(调研) --> 作家(写作) --> 编辑(审校)
```

| Agent | 角色 | 目标 |
|-------|------|------|
| `researcher` | 研究分析师 | 深入调研主题领域的最新进展和关键数据 |
| `writer` | 技术作家 | 将研究资料转化为结构清晰的中文文章 |
| `editor` | 内容编辑 | 确保文章质量，修正逻辑错误和表述不当 |

### 依赖

| 包名 | 用途 |
|------|------|
| `crewai` | 多 Agent 协作框架 |

### 配置

CrewAI 使用 `openai/` 前缀的模型名格式，demo 自动处理前缀拼接。

## Key Dependencies and Configuration

两个 demo 均通过 `app/config.get_settings()` 读取环境变量：

| 变量名 | 用途 |
|--------|------|
| `MODEL_API_KEY` | LLM API 密钥 |
| `MODEL_BASE_URL` | LLM API 基础 URL |
| `MODEL_NAME` | 模型名称 |

## Related File List

| 文件 | 说明 |
|------|------|
| `__init__.py` | 包初始化（空文件） |
| `langgraph_agent.py` | LangGraph 状态图 Agent 演示（数学计算工具） |
| `crewai_crew.py` | CrewAI 多角色协作演示（主题写作流水线） |

## Change Log

| 日期 | 变更内容 |
|------|---------|
| 2026-05-14 | 初始化模块 AI 上下文文档 |
