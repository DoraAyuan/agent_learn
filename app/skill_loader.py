import os
import re


def parse_skill_markdown(content: str) -> dict:
    """
    解析单个skill markdown文件为结构化数据

    Args:
        content: markdown文件的完整文本内容

    Returns:
        包含title和sections字典的结构化数据
    """
    lines = content.splitlines()

    title = ""
    sections = {}
    current_section = None
    current_buffer = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):
            title = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_section is not None:
                sections[current_section] = "\n".join(current_buffer).strip()

            current_section = stripped[3:].strip()
            current_buffer = []
            continue

        if current_section is not None:
            current_buffer.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_buffer).strip()

    return {
        "title": title,
        "sections": sections
    }


def load_all_skills(skills_dir: str = "skills") -> dict:
    """
    加载skills目录下所有md文件并解析为结构化数据

    Args:
        skills_dir: 技能文件所在目录路径

    Returns:
        以skill_name为key的字典，每个value包含name, file_name, raw_content, title, sections

    Raises:
        FileNotFoundError: skills目录不存在
    """
    skills = {}

    if not os.path.exists(skills_dir):
        raise FileNotFoundError(f"skills目录不存在: {skills_dir}")

    for filename in os.listdir(skills_dir):
        if not filename.endswith(".md"):
            continue

        skill_name = filename[:-3]
        file_path = os.path.join(skills_dir, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        parsed = parse_skill_markdown(raw_content)

        skills[skill_name] = {
            "name": skill_name,
            "file_name": filename,
            "raw_content": raw_content,
            "title": parsed["title"],
            "sections": parsed["sections"]
        }

    return skills
