"""
统一日志模块

使用Python标准库logging，同时输出到控制台和文件。
日志文件保存在项目根目录的 logs/ 目录下，按日期轮转。
"""

import logging
import os
import sys

_logger: logging.Logger | None = None


def get_logger(name: str = "agent") -> logging.Logger:
    """
    获取或创建logger实例

    首次调用时初始化全局配置：控制台 + 文件双输出。

    Args:
        name: logger名称，默认为"agent"

    Returns:
        配置好的Logger实例
    """
    global _logger

    if _logger is not None:
        return _logger

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # 控制台输出 — INFO级别
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "[%(levelname)s] %(message)s"
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)

    # 文件输出 — DEBUG级别（保留完整调试记录）
    try:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "agent.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        _logger.addHandler(file_handler)
    except Exception:
        pass

    return _logger


# 便捷函数，直接导入使用
def debug(msg: str) -> None: get_logger().debug(msg)
def info(msg: str) -> None: get_logger().info(msg)
def warning(msg: str) -> None: get_logger().warning(msg)
def error(msg: str) -> None: get_logger().error(msg)
