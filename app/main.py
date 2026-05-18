import os
import sys

# Windows GBK 编码可能无法输出中文，强制 UTF-8
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.agent import Agent


def main() -> None:
    agent = Agent()

    print("=== Skills Agent 启动 ===")
    print("输入内容开始对话，特殊命令:")
    print("  /clear   - 清空对话记忆")
    print("  /history - 查看对话信息")
    print("  /tools   - 查看可用工具")
    print("  exit     - 退出程序\n")

    while True:
        user_input = input(">>> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("再见！")
            break

        if user_input == "/clear":
            agent.clear_memory()
            continue

        if user_input == "/history":
            info = agent.get_memory_info()
            print(f"[对话轮数: {info['turn_count']}] [消息总数: {info['message_count']}]")
            continue

        if user_input == "/tools":
            tools = agent.tool_registry.list_tools()
            print(f"已注册工具({len(tools)}): {', '.join(tools)}")
            continue

        try:
            agent.run(user_input)
        except Exception as e:
            print(f"\n[错误] {e}\n")


if __name__ == "__main__":
    main()
