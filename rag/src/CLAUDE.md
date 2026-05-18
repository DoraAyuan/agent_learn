[Root Directory](../CLAUDE.md) > **src**

# src 模块 -- RAG 核心源码

## 模块职责

包含 RAG 系统的全部 Python 代码：核心检索-生成管道、FastAPI 接口层、三套评估脚本。该模块是整个项目的核心，负责文档加载、文本切分、向量化、检索、重排序、LLM 生成的完整链路。

## 入口与启动

| 入口 | 命令 | 说明 |
|------|------|------|
| rag_chain.py | `python src/rag_chain.py` | 独立运行：构建索引 + 测试问答 |
| api.py | `python -m uvicorn src.api:app --port 8000` | 启动 FastAPI 服务 |
| eval.py | `python src/eval.py` | 运行对比实验 |
| eval_ragas.py | `python src/eval_ragas.py` | RAGAS 量化评估 |
| eval_embedding.py | `python src/eval_embedding.py` | Embedding 模型对比 |

## 外部接口

### FastAPI 接口 (api.py)

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/rag/query` | POST | `{"question": str, "top_k?": int}` | `{"answer": str, "sources": [...]}` | 标准 RAG 问答 |
| `/rag/stream` | POST | 同上 | SSE 流 | 流式逐 token 生成 |
| `/health` | GET | - | `{"status": "ok", "index_ready": bool}` | 健康检查 |

### RAGChain 类 (rag_chain.py) -- 核心方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `load_documents(kb_path?)` | 可选知识库路径 | `list[Document]` | 加载 txt/md/pdf 并切分 |
| `build_index(chunks?, kb_path?, persist_dir?)` | 可选参数 | `int` (chunk 数) | 构建 Chroma 向量索引 |
| `load_index(persist_dir?)` | 可选持久化路径 | - | 加载已有向量索引 |
| `retrieve(query, top_k?)` | 查询字符串 | `list[(Document, score)]` | 向量相似度检索 |
| `answer(question, top_k?)` | 问题字符串 | `dict` {answer, sources} | 完整 RAG 回答 |
| `stream_answer(question, top_k?)` | 问题字符串 | Generator | 流式 RAG 回答 |

## 关键依赖

| 依赖 | 用途 |
|------|------|
| langchain_community | Document loaders (TextLoader, PyPDFLoader, Chroma) |
| langchain_ollama | OllamaEmbeddings, ChatOllama |
| langchain_text_splitters | RecursiveCharacterTextSplitter |
| langchain_core | ChatPromptTemplate, StrOutputParser |
| sentence_transformers | CrossEncoder (reranker) |
| fastapi + pydantic | REST API 框架 |
| pyyaml | 配置文件解析 |

## 关键设计

1. **Rerank 两阶段检索**: 先粗检索 `rerank_fetch_k=20` 条，再用 `BAAI/bge-reranker-base` cross-encoder 精排保留 `top_k=5`
2. **流式输出**: `stream_answer()` 先发 sources 事件，再逐 token 发送
3. **Prompt 模板**: 系统 prompt 要求仅基于上下文回答、不编造信息、引用来源
4. **启动自动索引**: API 启动时自动检测 `chroma_db/` 是否存在，不存在则重建

## 测试与评估

项目没有单元测试框架，通过三个评估脚本进行效果验证：
- **eval.py**: 三组对比实验 -- 模型大小(4B vs 8B)、chunk_size(256/512/1024)、top_k(3/5/10)
- **eval_ragas.py**: 使用本地 LLM 模拟 RAGAS 评估（faithfulness/relevancy/coverage 各 1-5 分）
- **eval_embedding.py**: 对比 nomic-embed-text 与 bge-m3 的中文检索效果

评估结果输出到项目根目录的 `eval_ragas_results.txt` 和 `eval_embedding_results.txt`。

## 相关文件

| 文件 | 说明 |
|------|------|
| `rag_chain.py` | RAG 核心管道类 RAGChain，全链路实现 |
| `api.py` | FastAPI 接口封装，启动时自动建索引 |
| `eval.py` | 对比实验：模型大小、chunk 策略、top-k |
| `eval_ragas.py` | RAGAS 量化评估脚本 |
| `eval_embedding.py` | 中文 Embedding 模型对比 |
| `__init__.py` | 空文件，标记 src 为 Python 包 |

## 变更日志

| 日期 | 变更内容 |
|------|----------|
| 2026-05-14 | 初始创建模块文档 |
