"""Confluence API交互的基础客户端模块。"""

import logging
import os

from atlassian import Confluence
from requests import Session

from ..exceptions import MCPAtlassianAuthenticationError
from ..utils.logging import get_masked_session_headers, log_config_param, mask_sensitive
from ..utils.ssl import configure_ssl_verification
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

        # 根据身份验证类型初始化Confluence客户端
        if self.config.auth_type == "pat":
            logger.debug(
                f"使用令牌（PAT）身份验证初始化Confluence客户端。"
                f"URL: {self.config.url}, "
                f"令牌（已遮蔽）: {mask_sensitive(str(self.config.personal_token))}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                token=self.config.personal_token,
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
            )
        else:  # 基本身份验证
            logger.debug(
                f"使用基本身份验证初始化Confluence客户端。"
                f"URL: {self.config.url}, 用户名: {self.config.username}, "
                f"API令牌存在: {bool(self.config.api_token)}, "
                f"是否为云: {self.config.is_cloud}"
            )
            self.confluence = Confluence(
                url=self.config.url,
                username=self.config.username,
                password=self.config.api_token,  # API令牌用作密码
                cloud=self.config.is_cloud,
                verify_ssl=self.config.ssl_verify,
            )
            logger.debug(
                f"Confluence客户端已初始化。"
                f"会话头（Authorization已遮蔽）: "
                f"{get_masked_session_headers(dict(self.confluence._session.headers))}"
            )

        # 使用共享工具配置SSL验证
        configure_ssl_verification(
            service_name="Confluence",
            url=self.config.url,
            session=self.confluence._session,
            ssl_verify=self.config.ssl_verify,
        )

        # 代理配置
        proxies = {}
        if self.config.http_proxy:
            proxies["http"] = self.config.http_proxy
        if self.config.https_proxy:
            proxies["https"] = self.config.https_proxy
        if self.config.socks_proxy:
            proxies["socks"] = self.config.socks_proxy
        if proxies:
            self.confluence._session.proxies.update(proxies)
            for k, v in proxies.items():
                log_config_param(
                    logger, "Confluence", f"{k.upper()}_PROXY", v, sensitive=True
                )
        if self.config.no_proxy and isinstance(self.config.no_proxy, str):
            os.environ["NO_PROXY"] = self.config.no_proxy
            log_config_param(logger, "Confluence", "NO_PROXY", self.config.no_proxy)

        # 如果配置了自定义头，则应用它们
        if self.config.custom_headers:
            self._apply_custom_headers()

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

    def _apply_custom_headers(self) -> None:
        """将自定义头应用到Confluence会话。"""
        if not self.config.custom_headers:
            return

        logger.debug(
            f"正在将{len(self.config.custom_headers)}个自定义头应用到Confluence会话"
        )
        for header_name, header_value in self.config.custom_headers.items():
            self.confluence._session.headers[header_name] = header_value
            logger.debug(f"Applied custom header: {header_name}")

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
