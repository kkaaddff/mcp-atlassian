"""用于优雅关闭和信号处理的生命周期管理实用函数。"""

import logging
import signal
import sys
import threading
from typing import Any

logger = logging.getLogger("mcp-atlassian.utils.lifecycle")

# Global shutdown event for signal-safe handling
_shutdown_event = threading.Event()


def setup_signal_handlers() -> None:
    """设置用于优雅关闭的信号处理程序。

    注册SIGTERM、SIGINT和SIGPIPE（如果可用）的处理程序，以确保
    应用程序在接收到终止信号时能够干净地关闭。

   这对于运行-i标志的Docker容器特别重要，
    需要正确处理来自父进程的关闭信号。
    """

    def signal_handler(signum: int, frame: Any) -> None:
        """优雅地处理关闭信号。

        使用基于事件的关闭以避免信号安全问题。
        信号处理程序应该尽可能简单，避免复杂操作。
        """
        # 信号处理程序中只允许安全操作 - 设置关闭事件
        _shutdown_event.set()

    # 注册信号处理程序
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 处理父进程关闭管道时发生的SIGPIPE
    try:
        signal.signal(signal.SIGPIPE, signal_handler)
        logger.debug("SIGPIPE handler registered")
    except AttributeError:
        # SIGPIPE在所有平台上都不可用（例如Windows）
        logger.debug("SIGPIPE not available on this platform")


def ensure_clean_exit() -> None:
    """确保退出前刷新所有输出流。

    对于容器化环境这很重要，因为输出可能会被缓冲，
    如果退出前没有正确刷新可能会丢失。

    处理流可能已被父进程关闭的情况，
    特别是在Windows上或作为子进程运行时。
    """
    logger.info("服务器已停止，正在刷新输出流...")

    # Safely flush stdout
    try:
        if hasattr(sys.stdout, "closed") and not sys.stdout.closed:
            sys.stdout.flush()
    except (ValueError, OSError, AttributeError) as e:
        # 流可能已关闭或被重定向
        logger.debug(f"无法刷新stdout: {e}")

    # Safely flush stderr
    try:
        if hasattr(sys.stderr, "closed") and not sys.stderr.closed:
            sys.stderr.flush()
    except (ValueError, OSError, AttributeError) as e:
        # 流可能已关闭或被重定向
        logger.debug(f"无法刷新stderr: {e}")

    logger.debug("输出流已刷新，正在优雅退出")
