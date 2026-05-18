import json
from typing import Optional
from app.llm_client import LLMClient


def build_skill_summary(skills: dict) -> str:
    """
    将结构化skills转成给模型看的简要说明
    """
    parts = []

    for skill_name, skill_data in skills.items():
        sections = skill_data.get("sections", {})
        purpose = sections.get("Purpose", "")
        when_to_use = sections.get("When to use", "")

        summary = (
            f"skill_name: {skill_name}\n"
            f"Purpose: {purpose}\n"
            f"When to use: {when_to_use}\n"
        )
        parts.append(summary)

    return "\n".join(parts)


def extract_json_text(response: str) -> str:
    """
    从模型返回中提取第一个完整JSON对象

    支持纯JSON、markdown代码块、JSON前后夹杂说明文字等情况。

    Args:
        response: 模型原始返回文本

    Returns:
        提取出的JSON文本，未找到完整JSON时返回原文本
    """
    response = response.strip()

    if response.startswith("```"):
        lines = response.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response = "\n".join(lines).strip()

    start = response.find("{")
    if start == -1:
        return response

    brace_count = 0
    in_string = False
    escape = False

    for i in range(start, len(response)):
        ch = response[i]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if not in_string:
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1

                if brace_count == 0:
                    return response[start:i + 1]

    return response


def select_skill(
    user_query: str,
    skills: dict,
    llm: Optional[LLMClient] = None,
) -> dict:
    """
    根据用户输入选择最合适的skill

    Args:
        user_query: 用户输入
        skills:     可用技能字典
        llm:        可复用的LLMClient实例

    Returns:
        包含skill_name和reason的字典

    Raises:
        ValueError: 模型返回非法JSON或不存在的skill_name
    """
    if llm is None:
        llm = LLMClient()

    available_skill_names = list(skills.keys())
    skill_summary = build_skill_summary(skills)

    prompt = f"""
你是一个skill路由器。

任务:
根据用户问题,从已有的skill中选择最合适的一个。

用户问题:
{user_query}

可用skills:
{skill_summary}

可选skill_name只能是以下之一:
{available_skill_names}

请严格返回且只返回一个JSON对象。
不要返回任何额外文字。
不要返回markdown代码块。
不要在JSON前后添加解释。

返回格式必须严格如下:
{{
  "skill_name": "paper_summary",
  "reason": "用户要求总结论文"
}}
"""

    messages = [
        {
            "role": "system",
            "content": "你是一个严格返回JSON的助手。你只能从给定skill_name列表中选择。"
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = llm.chat(messages)

    if not response:
        raise ValueError("模型没有返回skill选择结果")

    json_text = extract_json_text(response)

    try:
        result = json.loads(json_text)
    except json.JSONDecodeError as e:
        print("\n[调试] 模型原始返回内容:")
        print(response)
        print("\n[调试] 提取出的JSON文本:")
        print(json_text)
        raise ValueError("模型返回的不是合法JSON") from e

    if "skill_name" not in result:
        raise ValueError(f"模型返回的JSON缺少skill_name字段: {result}")

    skill_name = result["skill_name"]

    if skill_name not in available_skill_names:
        raise ValueError(
            f"模型返回了不存在的skill: {skill_name}. "
            f"允许的skill只有: {available_skill_names}"
        )

    if "reason" not in result:
        result["reason"] = ""

    return result
