import os

# 支持的文件格式
SUPPORTED_EXTENSIONS = (".txt", ".md", ".docx")


def read_text_file(file_path: str) -> str:
    """
    读取txt/md文本文件内容

    Args:
        file_path: 文件路径

    Returns:
        文件内容字符串，读取失败时返回错误描述
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()
        except Exception as e:
            return f"[文件编码错误: {e}]"
    except Exception as e:
        return f"[读取文件失败: {e}]"


def read_docx_file(file_path: str) -> str:
    """
    读取Word(.docx)文件内容

    提取所有段落文本，段落间保留换行。

    Args:
        file_path: .docx文件路径

    Returns:
        文件文本内容，读取失败时返回错误描述
    """
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except ImportError:
        return "[读取Word文件需要安装python-docx: pip install python-docx]"
    except Exception as e:
        return f"[读取Word文件失败: {e}]"


def resolve_file_path(user_input: str) -> str | None:
    """
    尝试把用户输入解析为支持的文件路径

    支持直接输入文件路径和file:前缀两种触发方式。
    依次尝试: 原始路径 → 当前工作目录拼接 → 项目根目录拼接 → data/目录查找

    Args:
        user_input: 用户原始输入

    Returns:
        找到文件时返回绝对路径，找不到时返回None
    """
    input_path = user_input.strip()
    if not input_path:
        return None

    is_supported = input_path.lower().endswith(SUPPORTED_EXTENSIONS)
    is_file_prefix = input_path.lower().startswith("file:")

    if not (is_supported or is_file_prefix):
        return None

    if is_file_prefix:
        input_path = input_path[5:].strip()

    cwd = os.getcwd()
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(tools_dir)
    project_root = os.path.dirname(app_dir)
    file_name_only = os.path.basename(input_path)

    candidate_paths = [
        input_path,
        os.path.join(cwd, input_path),
        os.path.join(project_root, input_path),
        os.path.join(project_root, "data", file_name_only),
    ]

    checked_paths = []

    for path in candidate_paths:
        normalized_path = os.path.normpath(path)
        absolute_path = os.path.abspath(normalized_path)

        if absolute_path in checked_paths:
            continue
        checked_paths.append(absolute_path)

        if os.path.exists(absolute_path) and os.path.isfile(absolute_path):
            return absolute_path

    return None


def read_file(file_path: str) -> str:
    """
    根据文件扩展名选择对应的读取方式

    Args:
        file_path: 文件路径

    Returns:
        文件内容字符串
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        return read_docx_file(file_path)
    else:
        return read_text_file(file_path)


def build_file_prompt(file_content: str, max_chars: int = 5000) -> str:
    """
    把文件内容包装成给模型的用户请求

    Args:
        file_content: 文件文本内容
        max_chars:    最多截取字符数
    """
    return f"请基于以下文件内容回答我的问题:\n\n{file_content[:max_chars]}"


def prepare_user_query(user_input: str) -> str:
    """
    统一处理用户输入，检测文件路径并读取

    支持 .txt / .md / .docx 格式。

    Args:
        user_input: 用户原始输入

    Returns:
        可直接进入Agent主流程的user_query
    """
    real_file_path = resolve_file_path(user_input)

    if real_file_path is None:
        return user_input

    from app.logger import info
    info(f"检测到本地文件: {real_file_path}")
    file_content = read_file(real_file_path)

    return build_file_prompt(file_content)
