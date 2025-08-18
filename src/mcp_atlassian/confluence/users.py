"""Confluence用户操作模块。"""

import logging
from typing import Any

from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAuthenticationError
from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class UsersMixin(ConfluenceClient):
    """Confluence用户操作的混入类。"""

    def get_user_details_by_accountid(
        self, account_id: str, expand: str = None
    ) -> dict[str, Any]:
        """根据账户ID获取用户详情。

        Args:
            account_id: 用户的账户ID。
            expand: 可选的expand参数用于获取用户状态。可能的参数是"status"。结果是"Active, Deactivated"。

        Returns:
            用户详情字典。

        Raises:
            如果用户不存在或存在权限问题，则从Atlassian API引发各种异常。
        """
        return self.confluence.get_user_details_by_accountid(account_id, expand)

    def get_user_details_by_username(
        self, username: str, expand: str = None
    ) -> dict[str, Any]:
        """根据用户名获取用户详情。

        这通常用于Confluence Server/DC实例，其中用户名可能用作标识符。

        Args:
            username: 用户的用户名。
            expand: 可选的expand参数用于获取用户状态。可能的参数是"status"。结果是"Active, Deactivated"。

        Returns:
            用户详情字典。

        Raises:
            如果用户不存在或存在权限问题，则从Atlassian API引发各种异常。
        """
        return self.confluence.get_user_details_by_username(username, expand)

    def get_current_user_info(self) -> dict[str, Any]:
        """
        通过调用Confluence的'/rest/api/user/current'端点检索当前身份验证用户的详细信息。

        Returns:
            dict[str, Any]: API返回的用户详细信息。

        Raises:
            MCPAtlassianAuthenticationError: 如果身份验证失败或响应不是有效的用户数据。
        """
        try:
            user_data = self.confluence.get("rest/api/user/current")
            if not isinstance(user_data, dict):
                logger.error(
                    f"Confluence /rest/api/user/current端点返回了非字典数据类型: {type(user_data)}。 "
                    f"响应文本（部分）: {str(user_data)[:500]}"
                )
                raise MCPAtlassianAuthenticationError(
                    "Confluence令牌验证失败：未从/rest/api/user/current端点接收到有效的JSON用户数据。"
                )
            return user_data
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                logger.warning(
                    f"Confluence令牌验证失败，HTTP状态码为{http_err.response.status_code}，对应/rest/api/user/current。"
                )
                raise MCPAtlassianAuthenticationError(
                    f"Confluence令牌验证失败：从/rest/api/user/current返回{http_err.response.status_code}"
                ) from http_err
            logger.error(
                f"调用Confluence /rest/api/user/current时发生HTTPError: {http_err}",
                exc_info=True,
            )
            raise MCPAtlassianAuthenticationError(
                f"Confluence令牌验证失败，HTTPError: {http_err}"
            ) from http_err
        except Exception as e:
            logger.error(
                f"获取当前Confluence用户详细信息时发生意外错误: {e}",
                exc_info=True,
            )
            raise MCPAtlassianAuthenticationError(
                f"Confluence令牌验证失败: {e}"
            ) from e
