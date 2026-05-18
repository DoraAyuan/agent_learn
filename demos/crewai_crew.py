"""
CrewAI 多角色协作演示

展示核心概念:
- Agent: 具有角色、目标和背景故事的AI代理
- Task: 具体任务，关联到Agent
- Crew: 协作团队，编排多个Agent完成多个Task
- Process: 执行策略（sequential顺序执行）

角色设计:
    研究员 --> 作家 --> 编辑
    (调研)    (写作)    (审校)

运行方式:
    python -m demos.crewai_crew
    python -m demos.crewai_crew "请写一篇关于AI在教育领域应用的短文"
"""
import os
import sys

# Windows GBK 编码无法输出 CrewAI 事件日志中的 emoji，强制 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import get_settings


def _create_llm():
    """
    从项目配置创建CrewAI LLM实例

    使用CrewAI的LLM类以支持任意OpenAI兼容平台（如MiMo）。
    """
    from crewai import LLM

    config = get_settings()
    return LLM(
        model=f"openai/{config['MODEL_NAME']}",
        api_key=config["MODEL_API_KEY"],
        base_url=config["MODEL_BASE_URL"],
    )


def build_crew(topic: str) -> "Crew":
    """
    构建多角色协作团队

    Args:
        topic: 写作主题

    Returns:
        配置好的Crew实例
    """
    from crewai import Agent, Crew, Process, Task

    llm = _create_llm()

    # ============================================================
    # 定义Agent
    # ============================================================

    researcher = Agent(
        role="研究分析师",
        goal=f"深入调研{topic}领域的最新进展和关键数据",
        backstory="""你是一位资深的研究分析师，擅长从复杂信息中提取关键洞察。
你关注行业趋势、技术突破和数据驱动的结论。""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role="技术作家",
        goal="将研究资料转化为结构清晰、通俗易懂的中文文章",
        backstory="""你是一位经验丰富的技术作家，擅长用简洁的语言解释复杂概念。
你的文章结构严谨，逻辑清晰，适合大众阅读。""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    editor = Agent(
        role="内容编辑",
        goal="确保文章质量，修正逻辑错误和表述不当",
        backstory="""你是一位严格的内容编辑，关注文章的准确性、流畅性和可读性。
你会检查事实准确性、逻辑连贯性和语言表达。""",
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ============================================================
    # 定义Task（任务链，context传递）
    # ============================================================

    research_task = Task(
        description=f"""调研"{topic}"的相关资料，包括:
1. 核心概念和技术原理
2. 当前主流应用案例
3. 关键数据和趋势
4. 面临的挑战和局限

输出结构化的调研笔记。""",
        expected_output="包含关键数据、案例和趋势的结构化调研笔记",
        agent=researcher,
    )

    writing_task = Task(
        description="""基于调研结果撰写一篇800字左右的中文文章，要求:
1. 标题醒目
2. 开头引入话题
3. 中间分3-4个小节展开
4. 结尾总结展望
5. 语言通俗易懂""",
        expected_output="一篇结构完整、语言流畅的中文文章",
        agent=writer,
        context=[research_task],
    )

    editing_task = Task(
        description="""审校文章，检查并修正:
1. 事实准确性
2. 逻辑连贯性
3. 语言表达和错别字
4. 整体结构和可读性

输出最终定稿。""",
        expected_output="经过审校和修正的最终文章",
        agent=editor,
        context=[writing_task],
    )

    # ============================================================
    # 组建Crew
    # ============================================================

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, writing_task, editing_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew


# ============================================================
# 主程序
# ============================================================

def main() -> None:
    """运行CrewAI多角色协作演示"""
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI在医疗健康领域的应用"

    print("=" * 50)
    print("CrewAI 多角色协作演示")
    print("=" * 50)
    print(f"\n主题: {topic}")
    print(f"\n协作流程: 研究员 --> 作家 --> 编辑")
    print("-" * 50)

    crew = build_crew(topic)
    result = crew.kickoff()

    print("\n" + "=" * 50)
    print("最终输出:")
    print("-" * 50)
    print(result)
    print("=" * 50)


if __name__ == "__main__":
    main()
