"""Confluence API交互的基础客户端模块。"""

import logging
import os

from atlassian import Confluence

from ..exceptions import MCPAtlassianAuthenticationError
from ..utils.logging import get_masked_session_headers, log_config_param
from .config import ConfluenceConfig

# 配置日志记录
logger = logging.getLogger("mcp-atlassian")


class ConfluenceClient:
    """Confluence API交互的基础客户端。"""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        """使用给定或环境配置初始化Confluence客户端。

        Args:
            config: Confluence客户端的配置。如果为None，将从环境加载。

        Raises:
            ValueError: 如果配置无效或缺少环境变量
        """
        self.config = config or ConfluenceConfig.from_env()

        logger.debug(
            f"使用基本身份验证初始化Confluence客户端。"
            f"URL: {self.config.url}, 用户名: {self.config.username}, "
            f"API令牌存在: {bool(self.config.api_token)}, "
            "使用Server/Data Center身份验证"
        )
        self.confluence = Confluence(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API令牌用作密码
            verify_ssl=True,
        )
        
        logger.debug(
            f"Confluence客户端已初始化。"
            f"会话头（Authorization已遮蔽）: "
            f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
        )

  
        # 在此处导入以避免循环导入
        from ..preprocessing.confluence import ConfluencePreprocessor

        self.preprocessor = ConfluencePreprocessor(base_url=self.config.url)

        # 在初始化期间测试身份验证（仅在调试模式下）
        if logger.isEnabledFor(logging.DEBUG):
            try:
                self._validate_authentication()
            except MCPAtlassianAuthenticationError:
                logger.warning(
                    "客户端初始化期间身份验证失败 - "
                    "仍然继续"
                )

    def _validate_authentication(self) -> None:
        """通过进行简单的API调用来验证身份验证。"""
        try:
            logger.debug(
                "通过进行简单的API调用来测试Confluence身份验证..."
            )
            # 进行简单的API调用来测试身份验证
            spaces = self.confluence.get_all_spaces(start=0, limit=1)
            if spaces is not None:
                logger.info(
                    f"Confluence身份验证成功。"
                    f"API调用返回了{len(spaces.get('results', []))}个空间。"
                )
            else:
                logger.warning(
                    "Confluence身份验证测试返回None - "
                    "这可能表示存在问题"
                )
        except Exception as e:
            error_msg = f"Confluence身份验证失败: {e}"
            logger.error(error_msg)
            logger.debug(
                f"失败时的身份验证头: "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )
            raise MCPAtlassianAuthenticationError(error_msg) from e

  
    def _process_html_content(
        self, html_content: str, space_key: str
    ) -> tuple[str, str]:
        """将HTML内容处理为HTML和markdown两种格式。

        Args:
            html_content: 来自Confluence的原始HTML内容
            space_key: 包含内容的空间的键

        Returns:
            (processed_html, processed_markdown)的元组
        """
        return self.preprocessor.process_html_content(
            html_content, space_key, self.confluence
        )
