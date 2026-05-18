[Root Directory](../CLAUDE.md) > **config**

# config 模块 -- 配置管理

## 模块职责

集中管理项目所有配置参数，包括模型选择、RAG 超参数、知识库路径、API 配置和 Ollama 连接信息。所有源码模块均从此处读取配置，实现配置与代码分离。

## 配置文件: config.yaml

### 配置项一览

| 分类 | 键 | 当前值 | 说明 |
|------|-----|--------|------|
| **模型** | `models.chat` | `qwen3:4b` | 开发调试用小模型 |
| | `models.chat_large` | `qwen3:8b` | 对比实验用大模型 |
| | `models.embedding` | `bge-m3` | BAAI 中文多语言 embedding |
| **RAG** | `rag.chunk_size` | `512` | 文本块大小（字符数） |
| | `rag.chunk_overlap` | `128` | 文本块重叠（约 25%） |
| | `rag.top_k` | `5` | 最终保留的相关片段数 |
| | `rag.similarity_threshold` | `0.5` | 相似度阈值（当前未使用） |
| | `rag.rerank_model` | `BAAI/bge-reranker-base` | Cross-encoder 精排模型 |
| | `rag.rerank_fetch_k` | `20` | 粗检索条数，精排后保留 top_k |
| **知识库** | `knowledge_base` | `knowledge_base/tech` | 当前使用的技术文档目录 |
| **API** | `api.host` | `0.0.0.0` | API 监听地址 |
| | `api.port` | `8000` | API 端口 |
| **Ollama** | `ollama.base_url` | `http://localhost:11434` | Ollama 服务地址 |

### 知识库切换

切换知识库场景只需修改 `knowledge_base` 字段：
- `knowledge_base/tech` -- 技术领域（当前）
- `knowledge_base/finance` -- 金融领域（预留）
- `knowledge_base/general` -- 通用场景（预留）

修改后需删除 `chroma_db/` 目录并重建索引。

## 关键设计

- 所有代码通过 `yaml.safe_load()` 读取此文件，无硬编码配置
- RAG 参数（chunk_size、top_k、rerank 模型等）的调整只需修改此文件
- 模型名称对应 Ollama 中已拉取的模型标识

## 相关文件

| 文件 | 说明 |
|------|------|
| `config.yaml` | 项目唯一配置文件，所有模块从此读取参数 |

## 变更日志

| 日期 | 变更内容 |
|------|----------|
| 2026-05-14 | 初始创建模块文档 |
