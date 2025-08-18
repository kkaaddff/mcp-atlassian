"""MCP Atlassian的SSL相关实用函数。"""

import logging
import ssl
from typing import Any
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter
from requests.sessions import Session
from urllib3.poolmanager import PoolManager

logger = logging.getLogger("mcp-atlassian")


class SSLIgnoreAdapter(HTTPAdapter):
    """忽略SSL验证的HTTP适配器。

    一个自定义传输适配器，为特定域名禁用SSL证书验证。
    此实现确保verify_mode设置为CERT_NONE且check_hostname被禁用，
    这是正确忽略SSL证书的必要条件。

    此适配器还启用了传统SSL重新协商，某些旧版服务器可能需要此功能。
    请注意，这会降低安全性，只应在绝对必要时使用。
    """

    def init_poolmanager(
        self, connections: int, maxsize: int, block: bool = False, **pool_kwargs: Any
    ) -> None:
        """初始化禁用SSL验证的连接池管理器。

        创建适配器时会调用此方法，这是完全禁用SSL验证的正确位置。

        参数:
            connections: 在池中保存的连接数
            maxsize: 池中的最大连接数
            block: 当池满时是否阻塞
            pool_kwargs: 池管理器的附加参数
        """
        # 配置SSL上下文以完全禁用验证
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # 启用传统SSL重新协商
        context.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
        context.options |= 0x40000  # SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION

        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=context,
            **pool_kwargs,
        )

    def cert_verify(self, conn: Any, url: str, verify: bool, cert: Any | None) -> None:
        """覆盖证书验证以禁用SSL验证。

        此方法仍包含在代码中是为了向后兼容，但主要的
        SSL禁用操作发生在init_poolmanager中。

        参数:
            conn: 连接
            url: 请求的URL
            verify: 原始verify参数（被忽略）
            cert: 客户端证书路径
        """
        super().cert_verify(conn, url, verify=False, cert=cert)


def configure_ssl_verification(
    service_name: str, url: str, session: Session, ssl_verify: bool
) -> None:
    """为特定服务配置SSL验证。

    如果禁用SSL验证，此函数将配置会话以使用自定义SSL适配器，
    该适配器绕过服务域名的证书验证。

    参数:
        service_name: 用于日志记录的服务名称（例如"Confluence"、"Jira"）
        url: 服务的基础URL
        session: 要配置的请求会话
        ssl_verify: 是否应启用SSL验证
    """
    if not ssl_verify:
        logger.warning(
            f"{service_name} SSL验证已禁用。这不安全，只应在测试环境中使用。"
        )

        # 从配置的URL获取域名
        domain = urlparse(url).netloc

        # 挂载适配器以处理对此域名的请求
        adapter = SSLIgnoreAdapter()
        session.mount(f"https://{domain}", adapter)
        session.mount(f"http://{domain}", adapter)
