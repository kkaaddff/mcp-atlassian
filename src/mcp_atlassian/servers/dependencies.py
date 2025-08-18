"""具有上下文感知能力的ConfluenceFetcher依赖提供程序。

提供get_confluence_fetcher供工具函数使用。
"""

from __future__ import annotations

import dataclasses
import logging
from typing import TYPE_CHECKING, Any

from fastmcp import Context
from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

from mcp_atlassian.confluence import ConfluenceConfig, ConfluenceFetcher
from mcp_atlassian.servers.context import MainAppContext

if TYPE_CHECKING:
    from mcp_atlassian.confluence.config import (
        ConfluenceConfig as UserConfluenceConfigType,
    )

logger = logging.getLogger("mcp-confluence.servers.dependencies")


def _create_user_config_for_fetcher(
    base_config: ConfluenceConfig,
    auth_type: str,
    credentials: dict[str, Any],
    cloud_id: str | None = None,
) -> ConfluenceConfig:
    """为Confluence获取器创建用户特定的配置。

    Args:
        base_config: 要克隆和修改的基础ConfluenceConfig。
        auth_type: 身份验证类型（'basic'或'pat'）。
        credentials: 凭据字典（token、email等）。
        cloud_id: 可选的云ID（basic/PAT身份验证不使用）。

    Returns:
        具有用户特定凭据的ConfluenceConfig。

    Raises:
        ValueError: 如果缺少必需的凭据或auth_type不受支持。
        TypeError: 如果base_config不是受支持的类型。
    """
    if auth_type not in ["basic", "pat"]:
        raise ValueError(
            f"用于创建用户特定配置的auth_type'{auth_type}'不受支持。应为'basic'或'pat'。"
        )

    username_for_config: str | None = credentials.get("user_email_context")

    logger.debug(
        f"为获取器创建用户配置。身份验证类型: {auth_type}, 凭据键: {credentials.keys()}"
    )

    common_args: dict[str, Any] = {
        "url": base_config.url,
        "auth_type": auth_type,
        "ssl_verify": base_config.ssl_verify,
        "http_proxy": base_config.http_proxy,
        "https_proxy": base_config.https_proxy,
        "no_proxy": base_config.no_proxy,
        "socks_proxy": base_config.socks_proxy,
    }

    if auth_type == "pat":
        user_pat = credentials.get("personal_access_token")
        if not user_pat:
            raise ValueError("用户auth_type'pat'的凭据中缺少PAT")

        # 如果使用PAT身份验证提供了cloud_id，记录警告（通常不需要）
        if cloud_id:
            logger.warning(
                f"使用PAT身份验证提供了云ID'{cloud_id}'。"
                "PAT身份验证通常直接使用基础URL，不需要cloud_id覆盖。"
            )

        common_args.update(
            {
                "personal_token": user_pat,
                "username": None,
                "api_token": None,
            }
        )
    elif auth_type == "basic":
        username = credentials.get("username")
        api_token = credentials.get("api_token")
        if not username or not api_token:
            raise ValueError("基本身份验证需要用户名和API令牌")

        common_args.update(
            {
                "username": username,
                "api_token": api_token,
                "personal_token": None,
            }
        )

    if isinstance(base_config, ConfluenceConfig):
        user_confluence_config: UserConfluenceConfigType = dataclasses.replace(
            base_config, **common_args
        )
        user_confluence_config.spaces_filter = base_config.spaces_filter
        return user_confluence_config
    else:
        raise TypeError(f"不支持的base_config类型: {type(base_config)}")




async def get_confluence_fetcher(ctx: Context) -> ConfluenceFetcher:
    """返回适合当前请求上下文的ConfluenceFetcher实例。

    Args:
        ctx: FastMCP上下文。

    Returns:
        当前用户或全局配置的ConfluenceFetcher实例。

    Raises:
        ValueError: 如果配置或凭据无效。
    """
    logger.debug(f"get_confluence_fetcher: 进入。上下文ID: {id(ctx)}")
    try:
        request: Request = get_http_request()
        logger.debug(
            f"get_confluence_fetcher: 在HTTP请求上下文中。请求URL: {request.url}。"
            f"State.confluence_fetcher存在: {hasattr(request.state, 'confluence_fetcher') and request.state.confluence_fetcher is not None}。"
            f"State.user_auth_type: {getattr(request.state, 'user_atlassian_auth_type', 'N/A')}。"
            f"State.user_token_present: {hasattr(request.state, 'user_atlassian_token') and request.state.user_atlassian_token is not None}。"
        )
        if (
            hasattr(request.state, "confluence_fetcher")
            and request.state.confluence_fetcher
        ):
            logger.debug(
                "get_confluence_fetcher: 从request.state返回ConfluenceFetcher。"
            )
            return request.state.confluence_fetcher
        user_auth_type = getattr(request.state, "user_atlassian_auth_type", None)
        logger.debug(f"get_confluence_fetcher: 用户身份验证类型: {user_auth_type}")
        if user_auth_type in ["basic", "pat"] and hasattr(
            request.state, "user_atlassian_token"
        ):
            user_token = getattr(request.state, "user_atlassian_token", None)
            user_email = getattr(request.state, "user_atlassian_email", None)
            user_cloud_id = getattr(request.state, "user_atlassian_cloud_id", None)

            if not user_token:
                raise ValueError("在状态中找到用户Atlassian令牌但为空。")
            credentials = {"user_email_context": user_email}
            if user_auth_type == "basic":
                credentials["api_token"] = user_token
                credentials["username"] = user_email
            elif user_auth_type == "pat":
                credentials["personal_access_token"] = user_token
            lifespan_ctx_dict = ctx.request_context.lifespan_context  # type: ignore
            app_lifespan_ctx: MainAppContext | None = (
                lifespan_ctx_dict.get("app_lifespan_context")
                if isinstance(lifespan_ctx_dict, dict)
                else None
            )
            if not app_lifespan_ctx or not app_lifespan_ctx.full_confluence_config:
                raise ValueError(
                    "Confluence全局配置（URL、SSL）无法从生命周期上下文中获取。"
                )

            cloud_id_info = f" 带有cloudId {user_cloud_id}" if user_cloud_id else ""
            logger.info(
                f"为用户{user_email or 'unknown'}创建用户特定的ConfluenceFetcher（类型: {user_auth_type}）（令牌...{str(user_token)[-8:]}）{cloud_id_info}"
            )
            user_specific_config = _create_user_config_for_fetcher(
                base_config=app_lifespan_ctx.full_confluence_config,
                auth_type=user_auth_type,
                credentials=credentials,
                cloud_id=user_cloud_id,
            )
            try:
                user_confluence_fetcher = ConfluenceFetcher(config=user_specific_config)
                current_user_data = user_confluence_fetcher.get_current_user_info()
                # 尝试从Confluence获取邮箱（如果未提供）（使用PAT时可能发生）
                derived_email = (
                    current_user_data.get("email")
                    if isinstance(current_user_data, dict)
                    else None
                )
                display_name = (
                    current_user_data.get("displayName")
                    if isinstance(current_user_data, dict)
                    else None
                )
                logger.debug(
                    f"get_confluence_fetcher: 已验证Confluence令牌。用户上下文: Email='{user_email or derived_email}', DisplayName='{display_name}'"
                )
                request.state.confluence_fetcher = user_confluence_fetcher
                if (
                    not user_email
                    and derived_email
                    and current_user_data
                    and isinstance(current_user_data, dict)
                    and current_user_data.get("email")
                ):
                    request.state.user_atlassian_email = current_user_data["email"]
                return user_confluence_fetcher
            except Exception as e:
                logger.error(
                    f"get_confluence_fetcher: 创建/验证用户特定的ConfluenceFetcher失败: {e}"
                )
                raise ValueError(f"无效的用户Confluence令牌或配置: {e}")
        else:
            logger.debug(
                f"get_confluence_fetcher: 没有用户特定的ConfluenceFetcher。身份验证类型: {user_auth_type}。令牌存在: {hasattr(request.state, 'user_atlassian_token')}。将使用全局回退。"
            )
    except RuntimeError:
        logger.debug(
            "不在HTTP请求上下文中。尝试为非HTTP使用全局ConfluenceFetcher。"
        )
    lifespan_ctx_dict_global = ctx.request_context.lifespan_context  # type: ignore
    app_lifespan_ctx_global: MainAppContext | None = (
        lifespan_ctx_dict_global.get("app_lifespan_context")
        if isinstance(lifespan_ctx_dict_global, dict)
        else None
    )
    if app_lifespan_ctx_global and app_lifespan_ctx_global.full_confluence_config:
        logger.debug(
            "get_confluence_fetcher: 从lifespan_context使用全局ConfluenceFetcher。"
            f"全局配置auth_type: {app_lifespan_ctx_global.full_confluence_config.auth_type}"
        )
        return ConfluenceFetcher(config=app_lifespan_ctx_global.full_confluence_config)
    logger.error("无法解析Confluence配置。")
    raise ValueError(
        "Confluence客户端（获取器）不可用。确保服务器配置正确。"
    )
