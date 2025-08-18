"""MCP Atlassian的日志记录实用函数。

此模块为MCP Atlassian提供增强的日志记录功能，
包括基于级别的流处理，根据日志的级别将其路由到适当的输出流。
"""

import logging
import sys
from typing import TextIO


def setup_logging(
    level: int = logging.WARNING, stream: TextIO = sys.stderr
) -> logging.Logger:
    """
    配置MCP-Atlassian日志记录，使用基于级别的流路由。

    参数:
        level: 要显示的最低日志级别（默认：WARNING）
        stream: 写入日志的流（默认：sys.stderr）

    返回:
        配置的日志记录器实例
    """
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 删除现有的处理程序以防止重复
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加基于级别的处理程序
    handler = logging.StreamHandler(stream)
    formatter = logging.Formatter("%(levelname)s - %(name)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # 配置特定的日志记录器
    loggers = ["mcp-atlassian", "mcp.server", "mcp.server.lowlevel.server", "mcp-jira"]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # 返回应用程序日志记录器
    return logging.getLogger("mcp-atlassian")


def mask_sensitive(value: str | None, keep_chars: int = 4) -> str:
    """为日志记录遮蔽敏感字符串。

    参数:
        value: 要遮蔽的字符串
        keep_chars: 在开头和结尾保留可见的字符数量

    返回:
        大多数字符被星号替换的遮蔽字符串
    """
    if not value:
        return "Not Provided"
    if len(value) <= keep_chars * 2:
        return "*" * len(value)
    start = value[:keep_chars]
    end = value[-keep_chars:]
    middle = "*" * (len(value) - keep_chars * 2)
    return f"{start}{middle}{end}"


def get_masked_session_headers(headers: dict[str, str]) -> dict[str, str]:
    """获取带有遮蔽敏感值的安全日志记录的会话标头。

    参数:
        headers: HTTP标头字典

    返回:
        带有遮蔽敏感标头的字典
    """
    sensitive_headers = {"Authorization", "Cookie", "Set-Cookie", "Proxy-Authorization"}
    masked_headers = {}

    for key, value in headers.items():
        if key in sensitive_headers:
            if key == "Authorization":
                # 保留身份验证类型但遮掩凭据
                if value.startswith("Basic "):
                    masked_headers[key] = f"Basic {mask_sensitive(value[6:])}"
                elif value.startswith("Bearer "):
                    masked_headers[key] = f"Bearer {mask_sensitive(value[7:])}"
                else:
                    masked_headers[key] = mask_sensitive(value)
            else:
                masked_headers[key] = mask_sensitive(value)
        else:
            masked_headers[key] = str(value)

    return masked_headers


def log_config_param(
    logger: logging.Logger,
    service: str,
    param: str,
    value: str | None,
    sensitive: bool = False,
) -> None:
    """记录配置参数，如果是敏感参数则进行遮蔽。

    参数:
        logger: 要使用的日志记录器
        service: 服务名称（Jira或Confluence）
        param: 参数名称
        value: 参数值
        sensitive: 值是否应该被遮蔽
    """
    display_value = mask_sensitive(value) if sensitive else (value or "Not Provided")
    logger.info(f"{service} {param}: {display_value}")
