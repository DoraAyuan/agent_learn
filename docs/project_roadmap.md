# 项目路线图

> Skills Agent Starter — AI Agent 技能管理系统
> 最后更新: 2026-05-14

---

## 项目定位

面向AI学习者的Agent开发入门项目，目标是覆盖主流Agent开发岗位的核心技术栈。

---

## 代码架构

### v0.1 — 基础技能系统（初始版本）

```
用户输入 --> file_reader(预处理) --> skill_selector(LLM选技能) --> agent(构建prompt) --> llm_client(调用LLM) --> 流式输出
```

核心模块:

| 模块 | 职责 |
|------|------|
| `main.py` | CLI入口，交互循环 |
| `agent.py` | Agent调度，串联完整工作流 |
| `skill_loader.py` | 加载skills/目录，解析Markdown |
| `skill_selector.py` | 调用LLM从已有技能中选择最匹配的一个 |
| `llm_client.py` | OpenAI兼容API封装（chat + chat_stream） |
| `config.py` | 环境变量配置管理 |
| `tools/file_reader.py` | 本地文本文件读取和路径解析 |

### v0.2 — Function Calling + RAG + 记忆

```
用户输入
  --> file_reader(文件预处理)
  --> memory(读取对话历史)
  --> agent(构建含工具+技能说明的prompt)
  --> llm.execute_tool_loop(LLM自主决策调工具)
       --> tool_registry.execute(分发到具体工具)
            --> datetime_tool / file_reader_tool / rag_search
       --> 工具结果回传LLM
  --> 流式输出最终回答
  --> memory(存入记忆)

回退路径: LLM未调用任何工具 --> skill_selector --> skill执行
```

新增模块:

| 模块 | 职责 |
|------|------|
| `tools/tool_registry.py` | 工具注册表，生成OpenAI兼容的tools schema |
| `tools/datetime_tool.py` | 日期时间工具，验证pipeline |
| `tools/file_reader_tool.py` | 包装file_reader为Function Calling工具 |
| `tools/rag_tool.py` | 包装RAGChain为rag_search工具（懒加载+优雅降级） |
| `memory.py` | 对话记忆，滑动窗口+LLM摘要压缩 |

### v1.0 — 工程化（当前版本）

```
                     +-----------------+
                     |   FastAPI 服务   |
                     |  SSE 流式接口    |
                     |  REST API 端点   |
                     +--------+--------+
                              |
                     +--------v--------+
                     |    Agent 核心    |
                     |  run / run_stream|
                     +--+-----+-----+--+
                        |     |     |
               +--------+  +--+--+  +--------+
               | Skill  |  |Tool |  | RAG   |
               | System |  |Reg. |  | Search|
               +--------+  +--+--+  +--------+
                              |
               +--------------+--------------+
               |              |              |
          datetime      file_reader     rag_search
```

### v2.0 — 多Agent协作（远期目标）

```
用户输入 --> 路由Agent --> 子Agent1(研究) / 子Agent2(写作) / 子Agent3(代码)
                             |                |                 |
                         RAG检索           模板执行          代码执行
                             +--------+--------+------+
                                      |
                                  汇总Agent --> 最终输出
```

---

## 迭代版本规划

### v0.1 基础技能系统 — 已完成

**目标**: 验证"选技能→执行"的基本流程

- [x] CLI交互入口
- [x] Markdown技能文件加载与解析
- [x] LLM驱动的技能选择路由
- [x] OpenAI兼容API通信封装
- [x] 本地文件读取与路径解析
- [x] 集中式环境变量校验

### v0.2 Function Calling + RAG + 记忆 — 已完成

**目标**: 覆盖Agent开发三大核心能力

- [x] ToolRegistry工具注册表（OpenAI function calling协议）
- [x] LLMClient.execute_tool_loop自动工具调用循环
- [x] 4个内置工具: datetime, file_reader, list_directory, rag_search
- [x] RAG项目跨项目集成（sys.path + 懒加载 + 优雅降级）
- [x] ConversationMemory对话记忆（滑动窗口 + LLM摘要压缩）
- [x] Agent统一流程: 工具优先 → 技能回退
- [x] conda环境合并（llm环境，Python 3.11）

### v0.3 代码规范化 — 已完成

**目标**: 按照编码规范重构全部源码，建立工程化基础

- [x] 全量代码按coding_standards.md规范化（16个Python文件）
- [x] 项目路线图与架构文档

### v1.0 工程化 — 已完成

**目标**: 达到可部署、可演示的工程状态

- [x] FastAPI服务化接口（SSE流式输出，6个API端点）
- [x] Dockerfile + docker-compose
- [x] 补充单元测试（pytest，20个测试用例全通过）
- [x] LangGraph demo（条件分支有状态Agent）
- [x] CrewAI demo（多角色协作）

### v1.1 能力扩展 — 待开始

**目标**: 扩展更多实际应用能力

- [ ] Web搜索工具（集成搜索API）
- [ ] 代码执行工具（安全沙箱）
- [ ] 多模态输入支持（图片理解）
- [ ] RAG混合检索（BM25 + 向量融合）
- [ ] RAG项目问题修复（requirements.txt、文档不一致、死配置）

### v2.0 多Agent系统 — 远期

**目标**: 从单Agent扩展到多Agent协作

- [ ] 多Agent协作架构
- [ ] Agent通信协议
- [ ] 工作流编排引擎
- [ ] 微调经验（LoRA/QLoRA）

---

## 技术能力覆盖

| 能力项 | 当前状态 | 来源 |
|----------|----------|------|
| Function Calling / Tool Use | 已覆盖 | v0.2 |
| RAG全链路 | 已覆盖 | RAG 项目 |
| 对话记忆 | 已覆盖 | v0.2 |
| LangChain框架 | 已覆盖 | RAG 项目 |
| 向量数据库Chroma | 已覆盖 | RAG 项目 |
| Prompt工程 | 已覆盖 | — |
| LLM调用封装 | 已覆盖 | — |
| 流式输出 | 已覆盖 | — |
| FastAPI服务化 | 已覆盖 | v1.0 |
| Docker部署 | 已覆盖 | v1.0 |
| Agent框架(LangGraph) | 已覆盖 | v1.0 |
| 多Agent协作 | 已覆盖 | v1.0 |
| 评估体系 | 已覆盖 | RAG 项目 |
| 微调(LoRA/QLoRA) | 未覆盖 | v2.0 |
| 代码规范化 | 已完成 | v0.3 |
| pytest单元测试 | 已覆盖 | v1.0 |
