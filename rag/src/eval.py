"""对比实验脚本: 模型大小 / chunk 策略 / top-k 对 RAG 效果的影响"""

import time
from pathlib import Path

import yaml
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_chain import RAGChain


def load_docs(config, kb_path=None):
    path = kb_path or config["knowledge_base"]
    from langchain_community.document_loaders import TextLoader, DirectoryLoader

    loader = DirectoryLoader(
        path, glob="**/*.txt", loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def eval_model_size():
    """对比 4B vs 8B 的回答质量和延迟"""
    print("=" * 50)
    print("实验一: 模型大小对比 (4B vs 8B)")
    print("=" * 50)

    questions = [
        "什么是 RAG？它的核心流程是什么？",
        "embedding 在 RAG 中的作用是什么？",
    ]
    models = ["qwen3:4b", "qwen3:8b"]
    ollama_url = "http://localhost:11434"
    results = {}

    for model in models:
        print(f"\n--- 测试模型: {model} ---")
        llm = ChatOllama(model=model, base_url=ollama_url, temperature=0)
        times = []
        for q in questions:
            start = time.time()
            resp = llm.invoke(q)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Q: {q[:40]}...")
            print(f"  A: {resp.content[:100]}...")
            print(f"  耗时: {elapsed:.2f}s")

        results[model] = {
            "avg_time": sum(times) / len(times),
            "total_time": sum(times),
        }

    print("\n--- 汇总 ---")
    for model, r in results.items():
        print(f"{model}: 平均延迟 {r['avg_time']:.2f}s")
    return results


def eval_chunk_size():
    """对比不同 chunk size 的检索效果"""
    print("\n" + "=" * 50)
    print("实验二: Chunk 大小对比 (256 / 512 / 1024)")
    print("=" * 50)

    with open("config/config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    documents = load_docs(config)
    ollama_url = config["ollama"]["base_url"]
    embeddings = OllamaEmbeddings(
        model=config["models"]["embedding"], base_url=ollama_url
    )
    query = "RAG 技术的核心流程"
    results = {}

    for chunk_size in [256, 512, 1024]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_size // 4,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunks = splitter.split_documents(documents)

        import tempfile, uuid
        tmp_dir = Path(tempfile.gettempdir()) / f"chroma_eval_{uuid.uuid4().hex[:8]}"
        vs = Chroma.from_documents(chunks, embeddings, persist_directory=str(tmp_dir))
        docs = vs.similarity_search_with_score(query, k=3)

        results[chunk_size] = {
            "chunk_count": len(chunks),
            "top3_scores": [round(float(s), 4) for _, s in docs],
            "avg_chars": sum(len(d.page_content) for d in chunks) / len(chunks),
        }
        print(f"\n  chunk_size={chunk_size}: {len(chunks)} 块, "
              f"平均长度 {results[chunk_size]['avg_chars']:.0f} 字符, "
              f"top3 相似度 {results[chunk_size]['top3_scores']}")

        # cleanup
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n--- 建议 ---")
    best = min(results, key=lambda cs: sum(results[cs]["top3_scores"]) / len(results[cs]["top3_scores"]))
    print(f"chunk_size={best} 检索平均相似度最高")
    return results


def eval_topk():
    """不同 top-k 的检索覆盖度"""
    print("\n" + "=" * 50)
    print("实验三: Top-K 对比 (3 / 5 / 10)")
    print("=" * 50)

    rag = RAGChain()
    if Path("chroma_db").exists() and any(Path("chroma_db").iterdir()):
        rag.load_index()
    else:
        chunks = rag.load_documents()
        rag.build_index(chunks)

    query = "如何使用本地模型构建 RAG 系统"

    for k in [3, 5, 10]:
        docs = rag.retrieve(query, top_k=k)
        scores = [round(float(s), 4) for _, s in docs]
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"  top_k={k}: 平均相似度 {avg_score:.4f}, 得分分布 {scores}")


if __name__ == "__main__":
    print("RAG 系统对比实验")
    print("注意: 实验一需要提前通过 ollama pull 下载对应模型\n")

    try:
        eval_model_size()
    except Exception as e:
        print(f"实验一失败 (可能模型未下载): {e}")

    try:
        eval_chunk_size()
    except Exception as e:
        print(f"实验二失败: {e}")

    try:
        eval_topk()
    except Exception as e:
        print(f"实验三失败: {e}")
