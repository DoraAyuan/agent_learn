# AI Agent 多架构开发实践

从零手写 AI Agent 核心架构，与 LangGraph、CrewAI 两种主流框架进行对照实现。

## 项目定位

本项目是一个 Agent 开发的学习与实验项目，旨在深入理解 AI Agent 的底层工作机制。实现了完整的 Function Calling 工具系统、RAG 知识库检索、对话记忆管理和技能路由编排，并提供了 FastAPI 服务化接口和 Docker 部署方案。

## 核心特性

- **Function Calling 工具系统**：基于 OpenAI 协议的 ToolRegistry 注册表 + 自动工具调用循环，LLM 自主决策工具调度
- **RAG 知识库检索**：跨项目集成 ChromaDB 向量数据库，懒加载 + 优雅降级设计
- **对话记忆**：滑动窗口 + LLM 摘要压缩，支持长对话上下文管理
- **技能路由**：Markdown 定义 SOP，LLM 意图识别驱动技能选择，零代码扩展
- **多框架对照**：手写架构 vs LangGraph 状态图 vs CrewAI 多角色协作
- **工程化**：FastAPI REST API（含 SSE 流式端点）、Docker 容器化、pytest 自动化测试

## 快速开始

### 环境要求

- Python 3.10+
- Conda（推荐）

### 安装

```bash
git clone https://github.com/DoraAyuan/agent_learn.git
cd agent_learn
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入你的 API 密钥
```

必需变量：
- `MODEL_API_KEY`：LLM API 密钥
- `MODEL_BASE_URL`：LLM API 基础 URL
- `MODEL_NAME`：模型名称

### 运行

```bash
# CLI 交互模式（主入口）
python -m app.main

# FastAPI 服务（http://localhost:8001/docs）
python -m app.server

# LangGraph 状态图 Agent demo
python -m demos.langgraph_agent

# CrewAI 多角色协作 demo
python -m demos.crewai_crew
```

CLI 特殊命令：`/clear`（清空记忆）、`/history`（对话统计）、`/tools`（工具列表）、`exit`（退出）

### RAG 知识库检索

项目内置了 RAG 子模块（`rag/` 目录），包含完整的 RAG 管道实现。运行时 `rag_search` 工具会自动加载向量索引。

使用前需安装依赖并确保 Ollama 服务运行：

```bash
pip install pyyaml chromadb langchain-community langchain-ollama sentence-transformers pypdf
ollama serve  # 需要本地 Ollama
```

## 架构

```
CLI / API 输入
    → file_reader（文件预处理）
    → memory（对话记忆管理）
    → Agent 调度（工具优先 → 技能回退）
        → ToolRegistry + execute_tool_loop（Function Calling）
        → skill_selector（技能路由回退）
    → 流式输出
```

### 已注册工具

| 工具名 | 功能 |
|--------|------|
| `get_current_datetime` | 获取当前日期时间 |
| `read_text_file` | 读取本地文本文件 |
| `list_directory` | 列出目录内容 |
| `rag_search` | RAG 知识库检索 |

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/tools` | GET | 工具列表 |
| `/api/v1/chat` | POST | 同步聊天 |
| `/api/v1/chat/stream` | POST | SSE 流式聊天 |
| `/api/v1/memory/clear` | POST | 清空记忆 |
| `/api/v1/memory/info` | GET | 记忆状态 |

## 技术栈

| 层级 | 技术 |
|------|------|
| Agent 框架 | 手写架构 / LangGraph / CrewAI |
| LLM 通信 | OpenAI SDK（chat / stream / tool_loop 四种模式） |
| 后端服务 | Python 3.10+ / FastAPI / Uvicorn / Pydantic |
| 向量检索 | ChromaDB / RAGChain |
| 工程化 | pytest / Docker / SSE |
| 技能系统 | Markdown SOP / LLM 意图路由 |
| 对话记忆 | 滑动窗口 / LLM 摘要压缩 |

## 项目结构

```
agent_learn/
├── app/                # 核心应用
│   ├── main.py         # CLI 入口
│   ├── server.py       # FastAPI 服务
│   ├── agent.py        # Agent 调度核心
│   ├── llm_client.py   # LLM 通信封装
│   ├── memory.py       # 对话记忆
│   ├── config.py       # 配置管理
│   ├── skill_loader.py # 技能加载
│   ├── skill_selector.py # 技能路由
│   ├── tools/          # 工具系统
│   └── api/            # REST API
├── rag/                # RAG 知识库检索子模块
├── skills/             # 技能定义（Markdown SOP）
├── demos/              # LangGraph / CrewAI 对照 demo
├── tests/              # pytest 测试套件
├── data/               # 示例数据
└── docs/               # 项目文档
```

## 运行测试

```bash
pytest tests/ -v
```

## 许可

MIT License
