"""RAGAS 评估: 量化 RAG 系统的 faithfullness / relevancy / recall / precision"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from rag_chain import RAGChain
from langchain_ollama import ChatOllama
import yaml

with open("config/config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

eval_llm = ChatOllama(
    model=config["models"]["chat"],
    base_url=config["ollama"]["base_url"],
    temperature=0,
)

# 测试用例: (问题, 参考答案)
test_cases = [
    (
        "LangChain 主要包含哪些组件？",
        "LangChain 包含文档加载器、文本分割器、向量存储、链、提示模板等核心组件。",
    ),
    (
        "什么是 RAG？",
        "RAG 是检索增强生成，结合信息检索与文本生成，先检索外部文档再将片段与问题一起交给 LLM 生成答案。",
    ),
    (
        "LangChain 和 LlamaIndex 有什么区别？",
        "LangChain 定位更广，强项在流程编排和 Agent；LlamaIndex 更专注于数据接入和检索，强项在文档索引和查询引擎。",
    ),
    (
        "Chroma 和 FAISS 有什么区别？",
        "Chroma 是完整的向量数据库，支持持久化和 metadata 过滤；FAISS 是高性能向量检索库，功能更底层。",
    ),
]


def run_eval():
    rag = RAGChain()
    rag.load_index()

    results = []
    for question, reference in test_cases:
        print(f"评估: {question[:40]}...")
        result = rag.answer(question)

        contexts = [
            doc.page_content
            for doc, _ in rag.retrieve(question, top_k=rag.top_k)
        ]

        results.append({
            "question": question,
            "answer": result["answer"],
            "contexts": contexts,
            "reference": reference,
        })

    return results


OUTPUT_FILE = Path(__file__).parent.parent / "eval_ragas_results.txt"


def simple_score(results):
    """用本地 LLM 做简单打分 (不依赖 ragas 的复杂评估链)"""
    lines = []
    lines.append("=" * 50)
    lines.append("RAG 质量评估 (RAGAS)")
    lines.append("=" * 50)

    scores = {"faithfulness": [], "relevancy": [], "coverage": []}

    for i, r in enumerate(results, 1):
        lines.append(f"\n--- Q{i}: {r['question']} ---")
        lines.append(f"回答: {r['answer'][:200]}")

        # Faithfulness: 答案是否忠于上下文
        faith_prompt = f"""仅根据以下上下文判断答案是否忠实。只回答 1-5 的数字。
上下文: {r['contexts'][0][:500]}
答案: {r['answer'][:300]}
1=完全编造 3=部分忠实 5=完全忠实
分数:"""
        faith_score = int(eval_llm.invoke(faith_prompt).content.strip()[0])
        scores["faithfulness"].append(faith_score)

        # Relevancy: 答案是否切题
        rel_prompt = f"""判断以下答案是否切题。只回答 1-5 的数字。
问题: {r['question']}
答案: {r['answer'][:300]}
1=完全不切题 3=部分切题 5=完全切题
分数:"""
        rel_score = int(eval_llm.invoke(rel_prompt).content.strip()[0])
        scores["relevancy"].append(rel_score)

        # Coverage: 上下文覆盖度
        cov_prompt = f"""检索到的上下文是否能支撑回答问题？只回答 1-5 的数字。
问题: {r['question']}
上下文: {r['contexts'][0][:500]}
1=完全不支撑 3=部分支撑 5=完全支撑
分数:"""
        cov_score = int(eval_llm.invoke(cov_prompt).content.strip()[0])
        scores["coverage"].append(cov_score)

        lines.append(f"  Faithfulness: {faith_score}/5  Relevancy: {rel_score}/5  Coverage: {cov_score}/5")

    lines.append("\n" + "=" * 50)
    lines.append("汇总")
    lines.append("=" * 50)
    for metric, vals in scores.items():
        avg = sum(vals) / len(vals)
        lines.append(f"  {metric}: {avg:.1f}/5")

    report = "\n".join(lines)
    print(report)

    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(f"\n结果已保存到 {OUTPUT_FILE}")


if __name__ == "__main__":
    results = run_eval()
    simple_score(results)
