import os
import sys

# RAG 项目目录（相对于 agent_learn 项目根目录）
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAG_PROJECT_DIR = os.path.join(_BASE_DIR, "rag")
RAG_SRC_DIR = os.path.join(RAG_PROJECT_DIR, "src")
RAG_CONFIG_PATH = os.path.join(RAG_PROJECT_DIR, "config", "config.yaml")

_rag_instance = None


def _get_rag_instance():
    """
    懒加载RAGChain实例

    首次调用时将RAG项目src/加入sys.path，导入并初始化RAGChain，
    加载已有向量索引，缓存实例供后续调用。

    Returns:
        RAGChain实例，初始化失败时返回None
    """
    global _rag_instance

    if _rag_instance is not None:
        return _rag_instance

    try:
        if RAG_SRC_DIR not in sys.path:
            sys.path.insert(0, RAG_SRC_DIR)

        original_cwd = os.getcwd()
        os.chdir(RAG_PROJECT_DIR)

        try:
            from rag_chain import RAGChain

            print(f"\n[RAG] 正在初始化RAGChain...")
            print(f"[RAG] 配置文件: {RAG_CONFIG_PATH}")

            rag = RAGChain(config_path=RAG_CONFIG_PATH)

            chroma_dir = os.path.join(RAG_PROJECT_DIR, "chroma_db")
            if os.path.exists(chroma_dir) and os.listdir(chroma_dir):
                print("[RAG] 加载已有向量索引...")
                rag.load_index(persist_dir=chroma_dir)
            else:
                print("[RAG] 未找到已有索引，正在构建...")
                chunks = rag.load_documents()
                rag.build_index(chunks, persist_dir=chroma_dir)
                print(f"[RAG] 索引构建完成，共{len(chunks)}个文档块")

            _rag_instance = rag
            print("[RAG] 初始化完成")
            return _rag_instance

        finally:
            os.chdir(original_cwd)

    except ImportError as e:
        print(f"\n[RAG] 导入失败: {e}")
        print("[RAG] 请确保已安装RAG项目的依赖: langchain-community, chromadb, sentence-transformers等")
        return None
    except Exception as e:
        print(f"\n[RAG] 初始化失败: {e}")
        return None


def rag_search(query: str, top_k: int = 3) -> str:
    """
    从RAG知识库中检索相关文档并生成回答

    Args:
        query: 搜索查询或问题
        top_k: 返回的相关文档数量

    Returns:
        RAG生成的回答及来源信息，RAG不可用时返回错误信息
    """
    rag = _get_rag_instance()

    if rag is None:
        return "[错误] RAG知识库不可用。请检查Ollama服务是否运行以及RAG依赖是否已安装。"

    try:
        original_cwd = os.getcwd()
        os.chdir(RAG_PROJECT_DIR)

        try:
            result = rag.answer(query, top_k=top_k)
        finally:
            os.chdir(original_cwd)

        answer = result.get("answer", "未生成回答")
        sources = result.get("sources", [])

        output = answer

        if sources:
            source_lines = []
            for s in sources:
                source_name = s.get("source", "未知")
                score = s.get("score", 0)
                source_lines.append(f"  - {source_name} (相关度: {score:.4f})")
            output += f"\n\n[来源]\n" + "\n".join(source_lines)

        return output

    except Exception as e:
        return f"[RAG查询错误] {e}"


def register_rag_tools(registry) -> bool:
    """
    注册RAG工具到注册表

    Args:
        registry: ToolRegistry实例

    Returns:
        True表示注册成功，False表示RAG依赖不可用
    """
    if not os.path.exists(RAG_PROJECT_DIR):
        print(f"\n[RAG] RAG项目目录不存在: {RAG_PROJECT_DIR}")
        print("[RAG] 跳过RAG工具注册")
        return False

    try:
        import yaml  # noqa: F401
        import chromadb  # noqa: F401
    except ImportError as e:
        print(f"\n[RAG] 缺少依赖: {e}")
        print("[RAG] 跳过RAG工具注册。如需使用，请安装: pip install pyyaml chromadb langchain-community")
        return False

    registry.register(
        name="rag_search",
        description=(
            "从RAG知识库中检索相关文档并回答问题。"
            "当用户提出知识性问题、需要查询文档资料时使用。"
            "知识库包含RAG技术介绍、LangChain使用指南等技术文档。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询或问题，例如 '什么是RAG' 或 'LangChain怎么用'"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的相关文档数量，默认为3",
                    "default": 3
                }
            },
            "required": ["query"]
        },
        func=rag_search
    )

    print("[RAG] RAG工具注册成功（懒加载，首次调用时初始化）")
    return True
