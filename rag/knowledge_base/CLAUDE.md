[Root Directory](../CLAUDE.md) > **knowledge_base**

# knowledge_base 模块 -- 知识库文档

## 模块职责

存放 RAG 系统的知识库文档，存放 RAG 系统的技术文档。当前包含技术类文档，预留金融和通用目录。文档会被 `rag_chain.py` 的 `load_documents()` 方法加载、切分并索引到 Chroma 向量库中。

## 目录结构

```
knowledge_base/
  tech/               # 技术文档（当前激活）
    rag_basics.txt    # RAG 技术详解（核心知识）
    langchain_intro.txt # LangChain 框架入门指南
    test.pdf          # 测试 PDF 文件
  finance/            # 金融文档（预留，需自行添加）
  general/            # 通用场景文档（预留，需自行添加）
```

## 文档内容概要

| 文件 | 内容 | 大小 |
|------|------|------|
| `rag_basics.txt` | RAG 完整流程、核心优势、chunk/embedding/向量数据库/Prompt 详解、局限性、进阶方向 | 约 78 行 |
| `langchain_intro.txt` | LangChain 核心组件（loaders/splitters/embeddings/vector stores/chains）、与 LlamaIndex 对比、使用方法和常见坑 | 约 94 行 |
| `test.pdf` | PDF 格式测试文件（二进制，不读取内容） | 二进制 |

## 支持的文件格式

- `.txt` -- TextLoader 加载
- `.md` -- TextLoader 加载
- `.pdf` -- PyPDFLoader 加载

文件按目录递归扫描（`**/*.txt`、`**/*.md`、`**/*.pdf`）。

## 使用方式

1. 在对应子目录下放入文档文件
2. 修改 `config/config.yaml` 中的 `knowledge_base` 路径（如需切换场景）
3. 删除 `chroma_db/` 目录
4. 重新运行 `python src/rag_chain.py` 或重启 API 服务

## 相关文件

| 文件 | 说明 |
|------|------|
| `tech/rag_basics.txt` | RAG 技术全面介绍，覆盖流程、策略和进阶方向 |
| `tech/langchain_intro.txt` | LangChain 框架入门，组件介绍和最佳实践 |
| `tech/test.pdf` | PDF 格式测试文件 |

## 变更日志

| 日期 | 变更内容 |
|------|----------|
| 2026-05-14 | 初始创建模块文档 |
