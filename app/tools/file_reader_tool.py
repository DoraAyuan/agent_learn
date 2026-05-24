import os
from app.tools.file_reader import read_file as _read_file, resolve_file_path


def read_file(file_path: str) -> str:
    """
    读取指定路径的文件（支持 .txt / .md / .docx）

    Args:
        file_path: 文件路径，相对或绝对路径均可

    Returns:
        文件内容，截取前5000字符，文件不存在时返回错误信息
    """
    resolved = resolve_file_path(file_path)

    if resolved:
        content = _read_file(resolved)
    else:
        if os.path.exists(file_path):
            content = _read_file(file_path)
        else:
            return f"[错误] 文件不存在: {file_path}"

    max_chars = 5000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n... [文件内容截断，共{len(content)}字符]"

    return content


def list_directory(directory_path: str = ".") -> str:
    """
    列出指定目录下的文件和子目录

    Args:
        directory_path: 目录路径，默认为当前目录

    Returns:
        文件和目录列表，目录不存在时返回错误信息
    """
    if not os.path.exists(directory_path):
        return f"[错误] 目录不存在: {directory_path}"

    if not os.path.isdir(directory_path):
        return f"[错误] 不是目录: {directory_path}"

    try:
        entries = os.listdir(directory_path)
        if not entries:
            return f"目录{directory_path}为空"

        result = []
        for entry in sorted(entries):
            full_path = os.path.join(directory_path, entry)
            if os.path.isdir(full_path):
                result.append(f"  [目录] {entry}/")
            else:
                size = os.path.getsize(full_path)
                result.append(f"  [文件] {entry} ({size}字节)")

        return f"目录{directory_path}的内容:\n" + "\n".join(result)

    except Exception as e:
        return f"[错误] 无法列出目录: {e}"


def register_file_reader_tools(registry) -> None:
    """
    注册文件读取工具到注册表

    Args:
        registry: ToolRegistry实例
    """
    registry.register(
        name="read_text_file",
        description=(
            "读取本地文件的内容。"
            "当用户要求读取文件、分析文件内容、或者提到了具体文件路径时使用。"
            "支持.txt、.md、.docx文件。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要读取的文件路径，例如 'data/paper.txt' 或 'notes.md'"
                }
            },
            "required": ["file_path"]
        },
        func=read_file
    )

    registry.register(
        name="list_directory",
        description=(
            "列出指定目录下的文件和子目录。"
            "当用户想知道某个目录下有什么文件时使用。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "要列出的目录路径，默认为当前目录"
                }
            },
            "required": []
        },
        func=list_directory
    )
