from typing import Generator
from app.skill_loader import load_all_skills
from app.skill_selector import select_skill
from app.llm_client import LLMClient
from app.memory import ConversationMemory
from app.tools.tool_registry import ToolRegistry
from app.tools.file_reader import prepare_user_query
from app.tools.datetime_tool import register_datetime_tools
from app.tools.file_reader_tool import register_file_reader_tools
from app.tools.rag_tool import register_rag_tools


class Agent:
    """
    Agent核心调度模块

    注册工具、维护对话记忆、根据用户输入决定使用工具还是回退到技能系统。
    """

    def __init__(self) -> None:
        """
        初始化LLM客户端、加载技能、注册工具、创建对话记忆
        """
        self.llm = LLMClient()
        self.skills = load_all_skills()
        self.memory = ConversationMemory(llm=self.llm)
        self.tool_registry = ToolRegistry()

        self._register_tools()

    def _register_tools(self) -> None:
        """注册所有可用工具到注册表"""
        register_datetime_tools(self.tool_registry)
        register_file_reader_tools(self.tool_registry)
        register_rag_tools(self.tool_registry)

        tools = self.tool_registry.list_tools()
        print(f"\n[Agent] 已注册{len(tools)}个工具: {tools}")

    def run(self, user_query: str) -> str:
        """
        执行一次完整Agent流程

        Args:
            user_query: 用户输入的原始文本

        Returns:
            Agent的回答文本
        """
        user_query = prepare_user_query(user_query)

        self.memory.add_user_message(user_query)

        system_prompt = self._build_system_prompt()
        history_messages = self.memory.get_messages()
        messages = [{"role": "system", "content": system_prompt}] + history_messages

        tools_schema = self.tool_registry.get_tools_schema()

        print("\n[Agent] 正在处理...")
        response = self._execute_with_tools(messages, tools_schema, user_query)

        if response:
            print(f"\n{response}")
        else:
            response = self._run_skill(user_query)

        if response:
            self.memory.add_assistant_message(response)

        return response

    def _execute_with_tools(
        self, messages: list, tools_schema: list, user_query: str
    ) -> str:
        """
        使用execute_tool_loop执行带工具的LLM调用

        Returns:
            LLM的文本回复，空字符串表示需要回退到skill
        """
        if not tools_schema:
            return ""

        try:
            response = self.llm.execute_tool_loop(
                messages=messages,
                tools=tools_schema,
                tool_executor=self.tool_registry.execute,
                max_rounds=5
            )
            return response
        except Exception as e:
            print(f"\n[Agent] 工具调用出错: {e}")
            return ""

    def _run_skill(self, user_query: str) -> str:
        """
        回退方案: 使用原有skill系统执行

        Args:
            user_query: 用户查询

        Returns:
            skill执行结果
        """
        print("\n[Agent] 未触发工具调用，回退到skill模式...")

        skill_name, prompt = self._build_skill_prompt(user_query)

        print(f"[2] 已选择skill: {skill_name}")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_query},
        ]

        response = self.llm.chat_stream(messages)
        return response

    def _build_skill_prompt(self, user_query: str) -> tuple[str, str]:
        """
        选择skill并构建system prompt

        Args:
            user_query: 用户查询

        Returns:
            (skill_name, system_prompt) 元组
        """
        print("[1] 正在选择skill...")
        selection = select_skill(user_query, self.skills, llm=self.llm)

        skill_name = selection["skill_name"]
        reason = selection.get("reason", "")

        print(f"[2] 已选择skill: {skill_name}")
        if reason:
            print(f"[2.1] 选择理由: {reason}")

        if skill_name not in self.skills:
            raise ValueError(f"模型返回了不存在的skill: {skill_name}")

        skill_data = self.skills[skill_name]
        sections = skill_data.get("sections", {})

        system_prompt = f"""
你是一个严格按照skill SOP执行任务的AI助手。

当前skill_name:
{skill_name}

Purpose:
{sections.get("Purpose", "")}

When to use:
{sections.get("When to use", "")}

Input:
{sections.get("Input", "")}

Steps:
{sections.get("Steps", "")}

Output Format:
{sections.get("Output Format", "")}

Constraints:
{sections.get("Constraints", "")}

要求:
1. 严格遵循上面的skill结构执行
2. 如果用户提供的信息不足, 明确说明信息不足
3. 不要编造不存在的论文细节
"""

        return skill_name, system_prompt

    def run_stream(self, user_query: str) -> Generator[dict, None, None]:
        """
        流式版本的run，逐事件yield

        事件类型:
        - {"type": "tool_call", "tool_name": str, "arguments": dict, "round": int}
        - {"type": "tool_result", "tool_name": str, "result": str, "round": int}
        - {"type": "text", "content": str}
        - {"type": "done", "full_response": str}
        - {"type": "error", "message": str}

        Args:
            user_query: 用户输入的原始文本

        Yields:
            事件字典
        """
        user_query = prepare_user_query(user_query)
        self.memory.add_user_message(user_query)

        system_prompt = self._build_system_prompt()
        history_messages = self.memory.get_messages()
        messages = [{"role": "system", "content": system_prompt}] + history_messages
        tools_schema = self.tool_registry.get_tools_schema()

        full_response = ""

        if tools_schema:
            try:
                for event in self.llm.execute_tool_loop_stream(
                    messages=messages,
                    tools=tools_schema,
                    tool_executor=self.tool_registry.execute,
                    max_rounds=5,
                ):
                    if event["type"] == "text":
                        full_response += event["content"]

                    yield event

            except Exception as e:
                yield {"type": "error", "message": f"工具调用出错: {e}"}

        if not full_response:
            skill_name, prompt = self._build_skill_prompt(user_query)

            skill_messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_query},
            ]

            for text in self.llm.chat_stream_yield(skill_messages):
                full_response += text
                yield {"type": "text", "content": text}

        if full_response:
            self.memory.add_assistant_message(full_response)

        yield {"type": "done", "full_response": full_response}

    def _build_system_prompt(self) -> str:
        """
        构建包含工具说明、技能列表和对话摘要的系统提示词

        Returns:
            完整的system prompt文本
        """
        tools_section = ""
        tools = self.tool_registry.get_tools_schema()
        if tools:
            tools_section = "## 可用工具\n\n"
            tools_section += "你可以调用以下工具来帮助回答用户问题:\n\n"
            for tool_schema in tools:
                func = tool_schema["function"]
                tools_section += f"### {func['name']}\n"
                tools_section += f"- 描述: {func['description']}\n"

                params = func.get("parameters", {}).get("properties", {})
                if params:
                    tools_section += "- 参数:\n"
                    for param_name, param_info in params.items():
                        desc = param_info.get("description", "")
                        tools_section += f"  - {param_name}: {desc}\n"

                tools_section += "\n"

        skills_section = "## 可用技能\n\n"
        skills_section += "如果以上工具都不适合，你还可以引导用户使用以下技能:\n\n"
        for skill_name, skill_data in self.skills.items():
            sections = skill_data.get("sections", {})
            purpose = sections.get("Purpose", "")
            skills_section += f"- **{skill_name}**: {purpose}\n"

        summary = self.memory.get_summary()
        memory_section = ""
        if summary:
            memory_section = f"## 对话摘要\n\n以下是之前对话的总结，请参考上下文回答:\n{summary}\n"

        prompt = f"""你是一个智能Agent助手。

{tools_section}
{skills_section}
## 行为准则

1. 优先使用工具来获取信息或执行操作
2. 如果用户的问题可以通过工具回答，直接调用工具
3. 如果需要多个步骤，可以连续调用多个工具
4. 回答要简洁、准确、用中文
5. 如果工具无法解决问题，说明原因

{memory_section}"""

        return prompt

    def clear_memory(self) -> None:
        """清空对话记忆"""
        self.memory.clear()
        print("[Agent] 对话记忆已清空")

    def get_memory_info(self) -> dict:
        """返回当前记忆的状态信息"""
        return {
            "turn_count": self.memory.turn_count,
            "message_count": self.memory.message_count,
        }
