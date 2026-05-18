# 本地知识库 RAG 问答系统

基于 LangChain + Ollama + Chroma 构建的本地 RAG 系统，支持文档切分、向量检索、Rerank 精排、流式生成和 API 接口封装。

## 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| LLM | Qwen3:4b / 8b (Ollama) | 本地推理，无需 API Key |
| Embedding | BAAI/bge-m3 (Ollama) | 中文多语言 embedding，效果优于 nomic-embed-text |
| Reranker | BAAI/bge-reranker-base | Cross-Encoder 精排模型，粗检索后二次排序 |
| 框架 | LangChain | LLM 应用开发主流框架 |
| 向量库 | Chroma | 持久化存储，支持 metadata 过滤 |
| API | FastAPI | REST 接口 + SSE 流式输出 |
| 评估 | RAGAS (本地 LLM 打分) | Faithfulness / Relevancy / Coverage 量化评估 |
| 环境 | Python 3.11 + Windows | conda env: llm |

## 项目结构

```
RAG/
├── config/config.yaml          # 集中配置：模型、RAG 参数、知识库路径
├── src/
│   ├── rag_chain.py            # RAG 核心管道（加载→切分→向量化→检索→rerank→生成）
│   ├── api.py                  # FastAPI 接口（/rag/query, /rag/stream, /health）
│   ├── eval.py                 # 对比实验（模型大小、chunk 策略、top-k）
│   ├── eval_ragas.py           # RAGAS 质量评估（faithfulness/relevancy/coverage）
│   └── eval_embedding.py       # Embedding 模型对比实验
├── knowledge_base/
│   ├── tech/                   # 技术文档（当前使用）
│   ├── finance/                # 金融文档（预留，切换场景时使用）
│   └── general/                # 通用文档（预留）
├── chroma_db/                  # 向量库持久化目录
├── eval_ragas_results.txt      # RAGAS 评估结果（自动生成）
├── eval_embedding_results.txt  # Embedding 对比结果（自动生成）
└── README.md
```

## 快速开始

### 1. 环境要求

- Ollama 已安装，模型已拉取：
  ```bash
  ollama pull qwen3:4b
  ollama pull bge-m3
  ```
- Python 3.11+，conda 环境 `llm` 已配置依赖
- Reranker 模型首次运行时自动从 HuggingFace 下载（BAAI/bge-reranker-base）

### 2. 使用 RAG 管道

```bash
cd D:\AiLearning\LLM\RAG
python src/rag_chain.py
```

### 3. 启动 API 服务

```bash
cd D:\AiLearning\LLM\RAG
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

接口说明：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/rag/query` | POST | 同步问答，返回 answer + sources |
| `/rag/stream` | POST | SSE 流式输出，先发 sources 再逐 token 返回 |
| `/health` | GET | 健康检查，返回索引就绪状态 |

示例调用：
```python
import requests
resp = requests.post("http://localhost:8000/rag/query",
    json={"question": "什么是 RAG？", "top_k": 5})
print(resp.json())
```

### 4. 运行对比实验

```bash
# 需要先拉取 qwen3:8b
ollama pull qwen3:8b
python src/eval.py
```

实验内容：
- 模型大小对比：4B vs 8B（回答质量、延迟）
- Chunk 大小对比：256 vs 512 vs 1024（检索准确率）
- Top-K 对比：3 vs 5 vs 10（召回覆盖度）

### 5. 运行 RAGAS 评估

```bash
python src/eval_ragas.py
# 结果输出到 eval_ragas_results.txt
```

### 6. 切换知识库场景

切换知识库场景时，修改 `config/config.yaml`：

```yaml
knowledge_base: "knowledge_base/tech"    # 投技术岗
knowledge_base: "knowledge_base/finance"  # 投金融岗
knowledge_base: "knowledge_base/general"  # 通用场景
```

然后删除 `chroma_db/` 目录，重新运行 `python src/rag_chain.py` 重建索引。

## RAG 全链路流程

```
文档加载 (txt/md/pdf)
  → 文本切分 (RecursiveCharacterTextSplitter, chunk=512, overlap=128)
    → 向量化 (bge-m3, Ollama)
      → 向量存储 (Chroma, 持久化)
        → 用户提问 → 问题向量化
          → 粗检索 (top_k × 4 = 20 条)
            → Cross-Encoder 精排 (bge-reranker-base)
              → 保留 Top-K (5 条)
                → Prompt 拼接 (context + question)
                  → LLM 生成 (Qwen3:4b, temperature=0)
                    → 返回 answer + sources
```

## 核心设计原则

- **KISS**：全链路约 200 行 Python，直接用 LangChain 最简 API
- **YAGNI**：不预先实现 Agent、多模态、Graph RAG，保持核心流程简洁
- **DRY**：配置文件集中管理，`_prepare_context()` 复用检索+rerank 逻辑
- **配置分离**：知识库路径、模型名、RAG 参数全在 yaml 中，切换场景无需改代码

## 核心能力覆盖

| 能力 | 实现 |
|----------|---------|
| RAG 完整流程 | `rag_chain.py` 实现了含 rerank 的两阶段检索流程 |
| chunk size 选择 | `eval.py` 有 256/512/1024 对比实验数据 |
| Embedding 选型 | `eval_embedding.py` 对比了不同 embedding 模型 |
| Rerank 机制 | 粗检索+精排两阶段，提升检索精度 |
| RAG 质量评估 | RAGAS 框架，Faithfulness/Relevancy/Coverage 三维度量化 |
| 流式输出 | SSE (Server-Sent Events)，FastAPI StreamingResponse |
| API 封装 | `api.py` FastAPI 接口，Pydantic 校验 |
