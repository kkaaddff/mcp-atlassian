"""MCP Atlassian的工具相关实用函数。"""

import logging
import os

logger = logging.getLogger(__name__)


def get_enabled_tools() -> list[str] | None:
    """从环境变量获取已启用工具的列表。

    该函数读取并解析ENABLED_TOOLS环境变量，
    以确定服务器中应提供哪些工具。

    环境变量应包含逗号分隔的工具名称列表。
    工具名称周围的空白字符会被去除。

    返回:
        如果ENABLED_TOOLS已设置且非空，则返回已启用工具名称列表，
        如果ENABLED_TOOLS未设置或去除空白后为空，则返回None。

    示例:
        ENABLED_TOOLS="tool1,tool2" -> ["tool1", "tool2"]
        ENABLED_TOOLS="tool1, tool2 , tool3" -> ["tool1", "tool2", "tool3"]
        ENABLED_TOOLS="" -> None
        ENABLED_TOOLS未设置 -> None
        ENABLED_TOOLS=" , " -> None
    """
    enabled_tools_str = os.getenv("ENABLED_TOOLS")
    if not enabled_tools_str:
        logger.debug("ENABLED_TOOLS environment variable not set or empty.")
        return None

    # 按逗号分割并去除空白字符
    tools = [tool.strip() for tool in enabled_tools_str.split(",")]
    # 过滤掉空字符串
    tools = [tool for tool in tools if tool]

    logger.debug(f"Parsed enabled tools from environment: {tools}")

    return tools if tools else None


def should_include_tool(tool_name: str, enabled_tools: list[str] | None) -> bool:
    """根据已启用工具列表检查是否应包含某个工具。

    参数:
        tool_name: 要检查的工具名称。
        enabled_tools: 已启用工具名称列表，如果为None则包含所有工具。

    返回:
        如果应包含该工具则返回True，否则返回False。
    """
    if enabled_tools is None:
        logger.debug(
            f"包含工具 '{tool_name}'，因为enabled_tools过滤器为None。"
        )
        return True
    should_include = tool_name in enabled_tools
    logger.debug(
        f"工具 '{tool_name}' 已包含: {should_include} (基于enabled_tools: {enabled_tools})"
    )
    return should_include
