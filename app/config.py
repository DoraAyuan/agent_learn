import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> str:
    """
    安全读取环境变量，自动去空格，支持默认值

    Args:
        name:       环境变量名
        default:    默认值

    Returns:
        去空格后的环境变量值

    Raises:
        ValueError: 变量不存在且无默认值，或值为空
    """
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"缺少环境变量: {name}")
    stripped_value = value.strip()
    if not stripped_value and default is None:
        raise ValueError(f"环境变量{name}不能为空")
    return stripped_value


def get_settings() -> dict:
    """
    统一获取所有配置，集中校验

    Returns:
        包含MODEL_API_KEY, MODEL_BASE_URL, MODEL_NAME的配置字典

    Raises:
        RuntimeError: 存在缺失的环境变量
    """
    missing = []
    settings = {}

    try:
        settings["MODEL_API_KEY"] = get_env("MODEL_API_KEY")
    except ValueError:
        missing.append("MODEL_API_KEY")

    try:
        settings["MODEL_BASE_URL"] = get_env("MODEL_BASE_URL")
    except ValueError:
        missing.append("MODEL_BASE_URL")

    try:
        settings["MODEL_NAME"] = get_env("MODEL_NAME")
    except ValueError:
        missing.append("MODEL_NAME")

    if missing:
        raise RuntimeError(
            "缺少环境变量：" + ", ".join(missing)
            + "\n请检查项目根目录下的.env文件。"
        )

    return settings
