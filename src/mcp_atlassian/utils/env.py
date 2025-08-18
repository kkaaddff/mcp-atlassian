"""MCP Atlassian的环境变量实用函数。"""

import os


def is_env_truthy(env_var_name: str, default: str = "") -> bool:
    """检查环境变量是否设置为标准真值。

    将'true'、'1'、'yes'视为真值（不区分大小写）。
    用于大多数MCP环境变量。

    参数:
        env_var_name: 要检查的环境变量名称
        default: 如果环境变量未设置的默认值

    返回:
        如果环境变量设置为真值则返回True，否则返回False
    """
    return os.getenv(env_var_name, default).lower() in ("true", "1", "yes")


def is_env_extended_truthy(env_var_name: str, default: str = "") -> bool:
    """检查环境变量是否设置为扩展真值。

    将'true'、'1'、'yes'、'y'、'on'视为真值（不区分大小写）。
    用于READ_ONLY_MODE和类似标志。

    参数:
        env_var_name: 要检查的环境变量名称
        default: 如果环境变量未设置的默认值

    返回:
        如果环境变量设置为真值则返回True，否则返回False
    """
    return os.getenv(env_var_name, default).lower() in ("true", "1", "yes", "y", "on")


def is_env_ssl_verify(env_var_name: str, default: str = "true") -> bool:
    """检查SSL验证设置并使用安全默认值。

    默认为true，除非明确设置为false值。
    用于SSL_VERIFY环境变量。

    参数:
        env_var_name: 要检查的环境变量名称
        default: 如果环境变量未设置的默认值

    返回:
        除非明确设置为false值，否则返回True
    """
    return os.getenv(env_var_name, default).lower() not in ("false", "0", "no")


def get_custom_headers(env_var_name: str) -> dict[str, str]:
    """从包含逗号分隔的key=value对的环境变量中解析自定义标头。

    参数:
        env_var_name: 要读取的环境变量名称

    返回:
        解析后的标头字典

    示例:
        >>> # With CUSTOM_HEADERS="X-Custom=value1,X-Other=value2"
        >>> parse_custom_headers("CUSTOM_HEADERS")
        {'X-Custom': 'value1', 'X-Other': 'value2'}
        >>> # With unset environment variable
        >>> parse_custom_headers("UNSET_VAR")
        {}
    """
    header_string = os.getenv(env_var_name)
    if not header_string or not header_string.strip():
        return {}

    headers = {}
    pairs = header_string.split(",")

    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue

        if "=" not in pair:
            continue

        key, value = pair.split("=", 1)  # Split on first = only
        key = key.strip()
        value = value.strip()

        if key:  # Only add if key is not empty
            headers[key] = value

    return headers
