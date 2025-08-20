"""Confluence客户端的配置模块。"""

import os
from dataclasses import dataclass



@dataclass
class ConfluenceConfig:
    """Confluence API配置。

    处理Confluence Basic Auth身份验证。
    """

    url: str  # Confluence的基础URL
    username: str  # 邮箱或用户名
    api_token: str  # 用作密码的API令牌


  
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

        # 只支持 Basic Auth
        username = os.getenv("CONFLUENCE_USERNAME")
        api_token = os.getenv("CONFLUENCE_API_TOKEN")

        if not (username and api_token):
            error_msg = "Basic Auth需要CONFLUENCE_USERNAME和CONFLUENCE_API_TOKEN"
            raise ValueError(error_msg)

        return cls(
            url=url,
            username=username,
            api_token=api_token,
        )

    def is_auth_configured(self) -> bool:
        """检查当前身份验证配置是否完整且有效，可以进行API调用。

        Returns:
            bool: 如果身份验证完全配置则为True，否则为False。
        """
        return bool(self.username and self.api_token)
