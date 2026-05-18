from app.llm_client import LLMClient


def main() -> None:
    llm = LLMClient()

    messages = [
        {
            "role": "system",
            "content": "你是一个乐于解释问题的AI助手,请回答得稍微详细一些。"
        },
        {
            "role": "user",
            "content": "请分3点介绍你自己:1.你是什么模型;2.你能做什么;3.你适合帮助什么类型的用户。"
        }
    ]

    llm.chat_stream(messages)


if __name__ == "__main__":
    main()
