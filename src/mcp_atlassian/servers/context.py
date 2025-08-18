from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_atlassian.confluence.config import ConfluenceConfig


@dataclass(frozen=True)
class MainAppContext:
    """
    上下文，保存服务器启动时从环境变量加载的完全配置的Confluence配置。
    这些配置包括任何全局/默认身份验证详细信息。
    """

    full_confluence_config: ConfluenceConfig | None = None
    read_only: bool = False
    enabled_tools: list[str] | None = None
