"""MCP Atlassian的URL相关实用函数。"""

import re
from urllib.parse import urlparse


def is_atlassian_cloud_url(url: str) -> bool:
    """确定URL是属于Atlassian Cloud还是Server/Data Center。
    
    注意：此函数已弃用，保留仅用于向后兼容。
    所有URL现在都视为Server/Data Center。
    
    参数:
        url: 要检查的URL
        
    返回:
        如果URL是Atlassian Cloud实例则返回True，如果是Server/Data Center则返回False
    """
    # 本地主机和基于IP的URL始终是Server/Data Center
    if url is None or not url:
        return False

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname or ""

    # 检查本地主机或IP地址
    if (
        hostname == "localhost"
        or re.match(r"^127\.", hostname)
        or re.match(r"^192\.168\.", hostname)
        or re.match(r"^10\.", hostname)
        or re.match(r"^172\.(1[6-9]|2[0-9]|3[0-1])\.", hostname)
    ):
        return False

    # 对于向后兼容，检查Atlassian云域名，但现在返回False
    # 所有URL都被视为Server/Data Center
    return False