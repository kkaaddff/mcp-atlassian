import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import requests
from fastmcp import Context
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def check_write_access(func: F) -> F:
    """
    用于FastMCP工具的装饰器，检查应用程序是否处于只读模式。
    如果处于只读模式，则引发ValueError。
    假设被装饰的函数是异步的，并且具有`ctx: Context`作为其第一个参数。
    """

    @wraps(func)
    async def wrapper(ctx: Context, *args: Any, **kwargs: Any) -> Any:
        lifespan_ctx_dict = ctx.request_context.lifespan_context
        app_lifespan_ctx = (
            lifespan_ctx_dict.get("app_lifespan_context")
            if isinstance(lifespan_ctx_dict, dict)
            else None
        )  # type: ignore

        if app_lifespan_ctx is not None and app_lifespan_ctx.read_only:
            tool_name = func.__name__
            action_description = tool_name.replace(
                "_", " "
            )  # e.g., "create_issue" -> "create issue"
            logger.warning(f"Attempted to call tool '{tool_name}' in read-only mode.")
            raise ValueError(f"Cannot {action_description} in read-only mode.")

        return await func(ctx, *args, **kwargs)

    return wrapper  # type: ignore


def handle_atlassian_api_errors(service_name: str = "Atlassian API") -> Callable:
    """
    处理常见Atlassian API异常（Jira、Confluence等）的装饰器。

    参数:
        service_name: 用于错误日志记录的服务名称（例如"Jira API"）。
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code in [
                    401,
                    403,
                ]:
                    error_msg = (
                        f"{service_name} 身份验证失败 "
                        f"({http_err.response.status_code}). "
                        "令牌可能已过期或无效。请验证凭据。"
                    )
                    logger.error(error_msg)
                    raise MCPAtlassianAuthenticationError(error_msg) from http_err
                else:
                    operation_name = getattr(func, "__name__", "API operation")
                    logger.error(
                        f"{operation_name}期间发生HTTP错误: {http_err}",
                        exc_info=False,
                    )
                    raise http_err
            except KeyError as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"{operation_name}结果中缺少键: {str(e)}")
                return []
            except requests.RequestException as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"{operation_name}期间发生网络错误: {str(e)}")
                return []
            except (ValueError, TypeError) as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"处理{operation_name}结果时出错: {str(e)}")
                return []
            except Exception as e:  # noqa: BLE001 - Intentional fallback with logging
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"{operation_name}期间发生意外错误: {str(e)}")
                logger.debug(
                    f"{operation_name}的完整异常详细信息:", exc_info=True
                )
                return []

        return wrapper

    return decorator
