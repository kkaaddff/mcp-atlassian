"""Confluence集成的FastMCP服务器主设置。"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal, Optional

from cachetools import TTLCache
from fastmcp import FastMCP
from fastmcp.tools import Tool as FastMCPTool
from mcp.types import Tool as MCPTool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.utils.environment import get_available_services
from mcp_atlassian.utils.io import is_read_only_mode
from mcp_atlassian.utils.logging import mask_sensitive
from mcp_atlassian.utils.tools import get_enabled_tools, should_include_tool

from .confluence import confluence_mcp
from .context import MainAppContext

logger = logging.getLogger("mcp-confluence.server.main")


async def health_check(request: Request) -> JSONResponse:
    """健康检查端点"""
    return JSONResponse({"status": "ok"})


@asynccontextmanager
async def main_lifespan(app: FastMCP[MainAppContext]) -> AsyncIterator[dict]:
    """主应用程序生命周期管理器"""
    logger.info("主Confluence MCP服务器生命周期启动中...")
    services = get_available_services()
    read_only = is_read_only_mode()
    enabled_tools = get_enabled_tools()

    loaded_confluence_config: ConfluenceConfig | None = None

    if services.get("confluence"):
        try:
            confluence_config = ConfluenceConfig.from_env()
            if confluence_config.is_auth_configured():
                loaded_confluence_config = confluence_config
                logger.info(
                    "Confluence配置已加载，身份验证已配置。"
                )
            else:
                logger.warning(
                    "找到Confluence URL，但身份验证未完全配置。Confluence工具将不可用。"
                )
        except Exception as e:
            logger.error(f"加载Confluence配置失败: {e}", exc_info=True)

    app_context = MainAppContext(
        full_confluence_config=loaded_confluence_config,
        read_only=read_only,
        enabled_tools=enabled_tools,
    )
    logger.info(f"只读模式: {'已启用' if read_only else '已禁用'}")
    logger.info(f"启用的工具过滤器: {enabled_tools or '所有工具已启用'}")

    try:
        yield {"app_lifespan_context": app_context}
    except Exception as e:
        logger.error(f"生命周期期间发生错误: {e}", exc_info=True)
        raise
    finally:
        logger.info("主Confluence MCP服务器生命周期关闭中...")
        # 在此执行任何必要的清理工作
        try:
            # 如果需要，关闭任何打开的连接
            if loaded_confluence_config:
                logger.debug("清理Confluence资源...")
        except Exception as e:
            logger.error(f"清理期间发生错误: {e}", exc_info=True)
        logger.info("主Confluence MCP服务器生命周期关闭完成。")


class ConfluenceMCP(FastMCP[MainAppContext]):
    """用于Confluence集成的自定义FastMCP服务器类，具有工具过滤功能。"""

    async def _mcp_list_tools(self) -> list[MCPTool]:
        # 根据生命周期上下文中的enabled_tools、read_only模式和服务配置过滤工具。
        req_context = self._mcp_server.request_context
        if req_context is None or req_context.lifespan_context is None:
            logger.warning(
                "在_main_mcp_list_tools调用期间生命周期上下文不可用。"
            )
            return []

        lifespan_ctx_dict = req_context.lifespan_context
        app_lifespan_state: MainAppContext | None = (
            lifespan_ctx_dict.get("app_lifespan_context")
            if isinstance(lifespan_ctx_dict, dict)
            else None
        )
        read_only = (
            getattr(app_lifespan_state, "read_only", False)
            if app_lifespan_state
            else False
        )
        enabled_tools_filter = (
            getattr(app_lifespan_state, "enabled_tools", None)
            if app_lifespan_state
            else None
        )
        logger.debug(
            f"_main_mcp_list_tools: read_only={read_only}, enabled_tools_filter={enabled_tools_filter}"
        )

        all_tools: dict[str, FastMCPTool] = await self.get_tools()
        logger.debug(
            f"过滤前聚合了{len(all_tools)}个工具: {list(all_tools.keys())}"
        )

        filtered_tools: list[MCPTool] = []
        for registered_name, tool_obj in all_tools.items():
            tool_tags = tool_obj.tags

            if not should_include_tool(registered_name, enabled_tools_filter):
                logger.debug(f"排除工具'{registered_name}'（未启用）")
                continue

            if tool_obj and read_only and "write" in tool_tags:
                logger.debug(
                    f"由于只读模式和'write'标签，排除工具'{registered_name}'"
                )
                continue

            # 如果配置未完全通过身份验证，排除Confluence工具
            is_confluence_tool = "confluence" in tool_tags
            service_configured_and_available = True
            if app_lifespan_state:
                if is_confluence_tool and not app_lifespan_state.full_confluence_config:
                    logger.debug(
                        f"排除Confluence工具'{registered_name}'，因为Confluence配置/身份验证不完整。"
                    )
                    service_configured_and_available = False
            elif is_confluence_tool:
                logger.warning(
                    f"排除工具'{registered_name}'，因为应用程序上下文不可用，无法验证服务配置。"
                )
                service_configured_and_available = False

            if not service_configured_and_available:
                continue

            filtered_tools.append(tool_obj.to_mcp_tool(name=registered_name))

        logger.debug(
            f"_main_mcp_list_tools: 过滤后的工具总数: {len(filtered_tools)}"
        )
        return filtered_tools

    def http_app(
        self,
        path: str | None = None,
        middleware: list[Middleware] | None = None,
        transport: Literal["streamable-http", "sse"] = "streamable-http",
    ) -> "Starlette":
        """创建带有用户令牌中间件的HTTP应用程序"""
        user_token_mw = Middleware(UserTokenMiddleware, mcp_server_ref=self)
        final_middleware_list = [user_token_mw]
        if middleware:
            final_middleware_list.extend(middleware)
        app = super().http_app(
            path=path, middleware=final_middleware_list, transport=transport
        )
        return app


token_validation_cache: TTLCache[
    int, tuple[bool, str | None, ConfluenceFetcher | None]
] = TTLCache(maxsize=100, ttl=300)


class UserTokenMiddleware(BaseHTTPMiddleware):
    """从Authorization头中提取Atlassian用户令牌/凭据的中间件。"""

    def __init__(
        self, app: Any, mcp_server_ref: Optional["ConfluenceMCP"] = None
    ) -> None:
        """初始化用户令牌中间件"""
        super().__init__(app)
        self.mcp_server_ref = mcp_server_ref
        if not self.mcp_server_ref:
            logger.warning(
                "UserTokenMiddleware在未提供mcp_server_ref的情况下初始化。如果需要设置，MCP端点的路径匹配可能会失败。"
            )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        """处理HTTP请求并提取用户令牌"""
        logger.debug(
            f"UserTokenMiddleware.dispatch: 进入请求处理，路径='{request.url.path}', 方法='{request.method}'"
        )
        mcp_server_instance = self.mcp_server_ref
        if mcp_server_instance is None:
            logger.debug(
                "UserTokenMiddleware.dispatch: self.mcp_server_ref为None。跳过MCP身份验证逻辑。"
            )
            return await call_next(request)

        mcp_path = mcp_server_instance.settings.streamable_http_path.rstrip("/")
        request_path = request.url.path.rstrip("/")
        logger.debug(
            f"UserTokenMiddleware.dispatch: 比较request_path='{request_path}'与mcp_path='{mcp_path}'。请求方法='{request.method}'"
        )
        if request_path == mcp_path and request.method == "POST":
            auth_header = request.headers.get("Authorization")
            cloud_id_header = request.headers.get("X-Atlassian-Cloud-Id")

            token_for_log = mask_sensitive(
                auth_header.split(" ", 1)[1].strip()
                if auth_header and " " in auth_header
                else auth_header
            )
            logger.debug(
                f"UserTokenMiddleware: Path='{request.url.path}', AuthHeader='{mask_sensitive(auth_header)}', ParsedToken(masked)='{token_for_log}', CloudId='{cloud_id_header}'"
            )

            # 提取并保存cloudId（如果提供）
            if cloud_id_header and cloud_id_header.strip():
                request.state.user_atlassian_cloud_id = cloud_id_header.strip()
                logger.debug(
                    f"UserTokenMiddleware: 从头中提取cloudId: {cloud_id_header.strip()}"
                )
            else:
                request.state.user_atlassian_cloud_id = None
                logger.debug(
                    "UserTokenMiddleware: 未提供cloudId头，将使用全局配置"
                )

            # 检查mcp-session-id头用于调试
            mcp_session_id = request.headers.get("mcp-session-id")
            if mcp_session_id:
                logger.debug(
                    f"UserTokenMiddleware: MCP-Session-ID header found: {mcp_session_id}"
                )
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Bearer token"},
                        status_code=401,
                    )
                logger.debug(
                    f"UserTokenMiddleware.dispatch: Bearer token extracted (masked): ...{mask_sensitive(token, 8)}"
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "basic"
                request.state.user_atlassian_email = None
                logger.debug(
                    f"UserTokenMiddleware.dispatch: Set request.state (pre-validation): "
                    f"auth_type='{getattr(request.state, 'user_atlassian_auth_type', 'N/A')}', "
                    f"token_present={bool(getattr(request.state, 'user_atlassian_token', None))}"
                )
            elif auth_header and auth_header.startswith("Token "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Token (PAT)"},
                        status_code=401,
                    )
                logger.debug(
                    f"UserTokenMiddleware.dispatch: PAT (Token scheme) extracted (masked): ...{mask_sensitive(token, 8)}"
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "pat"
                request.state.user_atlassian_email = (
                    None  # PAT本身不携带邮箱信息
                )
                logger.debug(
                    "UserTokenMiddleware.dispatch: 为PAT身份验证设置request.state。"
                )
            elif auth_header:
                logger.warning(
                    f"Unsupported Authorization type for {request.url.path}: {auth_header.split(' ', 1)[0] if ' ' in auth_header else 'UnknownType'}"
                )
                return JSONResponse(
                    {
                        "error": "Unauthorized: Only 'Bearer <APIToken>' or 'Token <PAT>' types are supported."
                    },
                    status_code=401,
                )
            else:
                logger.debug(
                    f"{request.url.path}未提供Authorization头。如果适用，将使用全局/回退服务器配置继续。"
                )
        response = await call_next(request)
        logger.debug(
            f"UserTokenMiddleware.dispatch: 退出请求处理，路径='{request.url.path}'"
        )
        return response


main_mcp = ConfluenceMCP(name="Confluence MCP", lifespan=main_lifespan)  # 创建主MCP服务器实例
main_mcp.mount("confluence", confluence_mcp)  # 挂载Confluence MCP服务器


@main_mcp.custom_route("/healthz", methods=["GET"], include_in_schema=False)
async def _health_check_route(request: Request) -> JSONResponse:
    """健康检查路由端点"""
    return await health_check(request)


logger.info("添加了/healthz端点用于Kubernetes探针")
