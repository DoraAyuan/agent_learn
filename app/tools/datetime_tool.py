from datetime import datetime


def get_current_datetime() -> str:
    """
    获取当前日期和时间

    Returns:
        格式化的日期时间字符串，例如 "2026-05-14 15:30:45"
    """
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def register_datetime_tools(registry) -> None:
    """
    注册日期时间工具到注册表

    Args:
        registry: ToolRegistry实例
    """
    registry.register(
        name="get_current_datetime",
        description="获取当前的日期和时间。当用户询问现在几点、今天几号等时间相关问题时使用。",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        },
        func=get_current_datetime
    )
