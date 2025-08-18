"""MCP Atlassian的I/O实用函数。"""

from mcp_atlassian.utils.env import is_env_extended_truthy


def is_read_only_mode() -> bool:
    """检查服务器是否以只读模式运行。

    只读模式阻止所有写操作（创建、更新、删除），
    同时允许所有读操作。这对于处理
    生产环境Atlassian实例很有用，可以防止意外
    修改。

    返回:
        如果启用只读模式则返回True，否则返回False
    """
    return is_env_extended_truthy("READ_ONLY_MODE", "false")
