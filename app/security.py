"""
输入安全模块：基础提示词注入防御和输入净化

设计原则（YAGNI）：
- 不做完整的 WAF 或 NLP 安全分析（不是安全产品）
- 只拦截最常见的 prompt injection 模式和 token 耗尽攻击
- 改动量极小，不引入外部依赖
"""

from app.logger import warning

# 常见提示词注入特征模式
_DANGEROUS_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "忽略之前的指令",
    "忽略所有之前的指令",
    "ignore the above",
    "忽略上述",
    "disregard previous",
    "forget all previous",
    "system prompt",
    "系统提示词",
    "your instructions are",
    "你的指令是",
    "you are now",
    "你现在是",
    "pretend you are",
    "假装你是",
    "act as if",
]

_MAX_INPUT_CHARS = 4000


def sanitize_user_input(text: str) -> str | None:
    """
    净化用户输入，检测潜在注入攻击

    返回 None 表示输入安全，返回字符串表示检测到问题（作为安全提示返回）

    Args:
        text: 用户原始输入

    Returns:
        None 表示通过检测，str 表示被拦截（该字符串就是给用户的安全提示）
    """
    # 1. 检测常见注入模式
    text_lower = text.lower()
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.lower() in text_lower:
            warning(f"检测到潜在提示词注入模式: {pattern}")
            return (
                "[安全提示] 检测到潜在的提示词注入行为，已过滤原始输入。"
                "如有正当需求，请重新描述您的问题。"
            )

    return None


def truncate_input(text: str, max_chars: int = _MAX_INPUT_CHARS) -> str:
    """
    截断超长输入，防止 token 耗尽攻击

    Args:
        text: 用户原始输入
        max_chars: 最大允许字符数，默认 4000

    Returns:
        截断后的文本
    """
    if len(text) > max_chars:
        warning(f"输入过长({len(text)}字符)，已截断至{max_chars}字符")
        return text[:max_chars] + "...(输入已截断)"
    return text
