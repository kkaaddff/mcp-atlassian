"""
MCP Atlassian集成的实用函数。
此包提供在整个代码库中使用的各种实用函数。
"""

from .date import parse_date
from .io import is_read_only_mode

# 导出生命周期实用函数
from .lifecycle import (
    ensure_clean_exit,
    setup_signal_handlers,
)
from .logging import setup_logging

from .ssl import SSLIgnoreAdapter, configure_ssl_verification

# 为向后兼容导出所有实用函数
__all__ = [
    "SSLIgnoreAdapter",
    "configure_ssl_verification",
    "is_read_only_mode",
    "setup_logging",
    "parse_date",
    "parse_iso8601_date",
    "setup_signal_handlers",
    "ensure_clean_exit",
]
