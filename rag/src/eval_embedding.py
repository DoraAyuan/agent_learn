"""对比 nomic-embed-text vs bge-m3 中文 embedding 效果"""

import time
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from rag_chain import RAGChain


OUTPUT_FILE = Path(__file__).parent.parent / "eval_embedding_results.txt"
REPORT_LINES = []


def test_embedding(name: str, model_id: str):
    """用同一批文档测试一个 embedding 模型"""
    REPORT_LINES.append(f"\n--- {name} ({model_id}) ---")

    rag = RAGChain()
    rag.embeddings = OllamaEmbeddings(
        model=model_id, base_url=rag.config["ollama"]["base_url"]
    )

    chunks = rag.load_documents()
    REPORT_LINES.append(f"  chunks: {len(chunks)}")

    import tempfile, uuid
    tmp = Path(tempfile.gettempdir()) / f"chroma_emb_{uuid.uuid4().hex[:8]}"
    vs = Chroma.from_documents(chunks, rag.embeddings, persist_directory=str(tmp))

    queries = [
        "LangChain 框架包含哪些核心组件？",
        "什么是检索增强生成？",
        "LangChain 怎么用？",
        "如何选择 chunk 大小？",
    ]

    for q in queries:
        docs = vs.similarity_search_with_score(q, k=3)
        scores = [round(float(s), 4) for _, s in docs]
        sources = [Path(d.metadata["source"]).name for d, _ in docs]
        REPORT_LINES.append(f"  '{q}': 最佳匹配 {sources[0]} (距离={scores[0]:.4f})")

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return vs


if __name__ == "__main__":
    REPORT_LINES.append("中文 Embedding 模型对比")
    test_embedding("英文基线", "nomic-embed-text")
    test_embedding("中文优化", "bge-m3")

    report = "\n".join(REPORT_LINES)
    print(report)
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(f"\n结果已保存到 {OUTPUT_FILE}")
