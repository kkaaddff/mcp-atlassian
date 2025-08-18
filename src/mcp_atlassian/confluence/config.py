"""Confluence客户端的配置模块。"""

import logging
import os
from dataclasses import dataclass
from typing import Literal

from ..utils.env import get_custom_headers, is_env_ssl_verify


@dataclass
class ConfluenceConfig:
    """Confluence API配置。

    处理Confluence Server/Data Center的身份验证：
    - Server/DC：个人访问令牌或基本身份验证
    """

    url: str  # Confluence的基础URL
    auth_type: Literal["basic", "pat"]  # 身份验证类型
    username: str | None = None  # 邮箱或用户名
    api_token: str | None = None  # 用作密码的API令牌
    personal_token: str | None = None  # 个人访问令牌（Server/DC）
    ssl_verify: bool = True  # 是否验证SSL证书
    spaces_filter: str | None = None  # 用于过滤搜索的空间键列表
    http_proxy: str | None = None  # HTTP代理URL
    https_proxy: str | None = None  # HTTPS代理URL
    no_proxy: str | None = None  # 绕过代理的主机逗号分隔列表
    socks_proxy: str | None = None  # SOCKS代理URL（可选）
    custom_headers: dict[str, str] | None = None  # 自定义HTTP头


    @property
    def verify_ssl(self) -> bool:
        """旧代码的兼容性属性。

        Returns:
            ssl_verify值
        """
        return self.ssl_verify

    @classmethod
    def from_env(cls) -> "ConfluenceConfig":
        """从环境变量创建配置。

        Returns:
            包含环境变量值的ConfluenceConfig

        Raises:
            ValueError: 如果缺少任何必需的环境变量
        """
        url = os.getenv("CONFLUENCE_URL")
        if not url:
            error_msg = "缺少必需的CONFLUENCE_URL环境变量"
            raise ValueError(error_msg)

        # 根据可用的环境变量确定身份验证类型
        username = os.getenv("CONFLUENCE_USERNAME")
        api_token = os.getenv("CONFLUENCE_API_TOKEN")
        personal_token = os.getenv("CONFLUENCE_PERSONAL_TOKEN")

        auth_type = None

        if personal_token:
            auth_type = "pat"
        elif username and api_token:
            # 基本身份验证
            auth_type = "basic"
        else:
            error_msg = "Server/Data Center身份验证需要CONFLUENCE_PERSONAL_TOKEN或CONFLUENCE_USERNAME和CONFLUENCE_API_TOKEN"
            raise ValueError(error_msg)

        # SSL验证（用于Server/DC）
        ssl_verify = is_env_ssl_verify("CONFLUENCE_SSL_VERIFY")

        # 获取空间过滤器（如果提供）
        spaces_filter = os.getenv("CONFLUENCE_SPACES_FILTER")

        # 代理设置
        http_proxy = os.getenv("CONFLUENCE_HTTP_PROXY", os.getenv("HTTP_PROXY"))
        https_proxy = os.getenv("CONFLUENCE_HTTPS_PROXY", os.getenv("HTTPS_PROXY"))
        no_proxy = os.getenv("CONFLUENCE_NO_PROXY", os.getenv("NO_PROXY"))
        socks_proxy = os.getenv("CONFLUENCE_SOCKS_PROXY", os.getenv("SOCKS_PROXY"))

        # 自定义头 - 仅限服务特定
        custom_headers = get_custom_headers("CONFLUENCE_CUSTOM_HEADERS")

        return cls(
            url=url,
            auth_type=auth_type,
            username=username,
            api_token=api_token,
            personal_token=personal_token,
            ssl_verify=ssl_verify,
            spaces_filter=spaces_filter,
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
            socks_proxy=socks_proxy,
            custom_headers=custom_headers,
        )

    def is_auth_configured(self) -> bool:
        """检查当前身份验证配置是否完整且有效，可以进行API调用。

        Returns:
            bool: 如果身份验证完全配置则为True，否则为False。
        """
        logger = logging.getLogger("mcp-confluence.confluence.config")
        if self.auth_type == "pat":
            return bool(self.personal_token)
        elif self.auth_type == "basic":
            return bool(self.username and self.api_token)
        logger.warning(
            f"ConfluenceConfig中未知或不受支持的auth_type: {self.auth_type}"
        )
        return False
