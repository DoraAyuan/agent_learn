"""RAG 核心链路: 文档加载→切分→向量化→检索→rerank→生成"""

from pathlib import Path
from typing import Optional

import yaml
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import CrossEncoder


class RAGChain:
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        rag_cfg = self.config["rag"]
        ollama_cfg = self.config["ollama"]
        model_cfg = self.config["models"]

        self.embeddings = OllamaEmbeddings(
            model=model_cfg["embedding"],
            base_url=ollama_cfg["base_url"],
        )
        self.llm = ChatOllama(
            model=model_cfg["chat"],
            base_url=ollama_cfg["base_url"],
            temperature=0,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_cfg["chunk_size"],
            chunk_overlap=rag_cfg["chunk_overlap"],
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        self.vectorstore: Optional[Chroma] = None
        self.top_k = rag_cfg["top_k"]

        # Reranker: 跨编码器精排，中文用 BAAI/bge-reranker-base
        rerank_model = rag_cfg.get("rerank_model", "BAAI/bge-reranker-base")
        self.reranker = CrossEncoder(rerank_model) if rerank_model else None
        self.rerank_fetch_k = rag_cfg.get("rerank_fetch_k", self.top_k * 4)

    def load_documents(self, kb_path: Optional[str] = None):
        """加载知识库目录下的所有 txt/md/pdf 文件"""
        path = Path(kb_path or self.config["knowledge_base"])
        if not path.exists():
            raise FileNotFoundError(f"知识库目录 {path} 不存在")

        documents = []
        for ext, loader_cls in [("*.txt", TextLoader), ("*.md", TextLoader)]:
            for fp in path.glob(f"**/{ext}"):
                try:
                    documents.extend(
                        loader_cls(str(fp), encoding="utf-8").load()
                    )
                except Exception as exc:
                    print(f"  跳过 {fp.name}: {exc}")

        for fp in path.glob("**/*.pdf"):
            try:
                documents.extend(PyPDFLoader(str(fp)).load())
            except Exception as exc:
                print(f"  跳过 {fp.name}: {exc}")

        if not documents:
            raise FileNotFoundError(f"知识库目录 {path} 中没有找到可处理的文件")

        chunks = self.text_splitter.split_documents(documents)
        return chunks

    def build_index(self, chunks=None, kb_path: Optional[str] = None, persist_dir: str = "./chroma_db"):
        """构建向量索引并持久化"""
        if chunks is None:
            chunks = self.load_documents(kb_path)
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_dir,
        )
        return len(chunks)

    def load_index(self, persist_dir: str = "./chroma_db"):
        """加载已有向量索引"""
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
        )

    def retrieve(self, query: str, top_k: Optional[int] = None):
        """检索 top-k 相关片段"""
        if self.vectorstore is None:
            raise RuntimeError("向量库未初始化，请先调用 build_index 或 load_index")
        k = top_k or self.top_k
        docs = self.vectorstore.similarity_search_with_score(query, k=k)
        return docs  # [(Document, score), ...]

    def build_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", """你是一个基于知识库的问答助手。请根据以下上下文回答用户的问题。

规则：
1. 仅根据上下文回答，不要编造信息
2. 如果上下文不足以回答，请明确说"根据提供的资料，我无法回答这个问题"
3. 回答时引用具体的来源片段
4. 使用中文回答

上下文：
{context}"""),
            ("human", "{question}"),
        ])

    def _prepare_context(self, question: str, top_k: Optional[int] = None):
        """检索 + rerank，返回 (context_str, docs_with_scores)"""
        k = top_k or self.top_k
        fetch_k = max(k, self.rerank_fetch_k)

        docs_with_scores = self.retrieve(question, fetch_k)
        if not docs_with_scores:
            return "", []

        if self.reranker and len(docs_with_scores) > k:
            docs = [d for d, _ in docs_with_scores]
            pairs = [[question, d.page_content] for d in docs]
            rerank_scores = self.reranker.predict(pairs)
            ranked = sorted(
                zip(docs, rerank_scores), key=lambda x: x[1], reverse=True
            )[:k]
            docs_with_scores = [(d, float(s)) for d, s in ranked]

        context = "\n\n---\n\n".join(
            doc.page_content for doc, _ in docs_with_scores[:k]
        )
        return context, docs_with_scores[:k]

    def answer(self, question: str, top_k: Optional[int] = None) -> dict:
        """完整 RAG 回答: 检索 → rerank → 生成"""
        context, docs_with_scores = self._prepare_context(question, top_k)
        if not context:
            return {"answer": "未找到相关文档。", "sources": []}

        prompt = self.build_prompt()
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})

        sources = []
        for doc, score in docs_with_scores:
            source = doc.metadata.get("source", "未知来源")
            sources.append({
                "source": Path(source).name,
                "score": round(float(score), 4),
                "preview": doc.page_content[:150] + "...",
            })

        return {"answer": answer, "sources": sources}

    def stream_answer(self, question: str, top_k: Optional[int] = None):
        """流式 RAG 回答: 逐 token 生成"""
        context, docs_with_scores = self._prepare_context(question, top_k)
        if not context:
            yield {"answer": "未找到相关文档。", "sources": []}
            return

        prompt = self.build_prompt()
        chain = prompt | self.llm | StrOutputParser()

        # 先发 sources，再流 answer
        sources = []
        for doc, score in docs_with_scores:
            source = doc.metadata.get("source", "未知来源")
            sources.append({
                "source": Path(source).name,
                "score": round(float(score), 4),
                "preview": doc.page_content[:150] + "...",
            })
        yield {"type": "sources", "data": sources}

        for chunk in chain.stream({"context": context, "question": question}):
            yield {"type": "token", "data": chunk}


if __name__ == "__main__":
    rag = RAGChain()
    chunks = rag.load_documents()
    print(f"共切分 {len(chunks)} 个文本块")

    rag.build_index(chunks)
    print("向量索引构建完成")

    result = rag.answer("介绍一下 RAG 的完整流程")
    print("\n=== 回答 ===")
    print(result["answer"])
    print("\n=== 引用来源 ===")
    for s in result["sources"]:
        print(f"  [{s['score']:.4f}] {s['source']}: {s['preview']}")
