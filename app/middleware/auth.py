"""认证中间件"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import Settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件，处理Confluence认证信息"""
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加认证信息"""
        
        # 从请求头中获取认证信息
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            if auth_header.startswith("Bearer "):
                # Bearer token (API Token)
                token = auth_header.split(" ", 1)[1].strip()
                request.state.confluence_auth_type = "basic"
                request.state.confluence_token = token
                logger.debug("使用Bearer token认证")
                
            elif auth_header.startswith("Token "):
                # Personal Access Token
                token = auth_header.split(" ", 1)[1].strip()
                request.state.confluence_auth_type = "pat"
                request.state.confluence_token = token
                logger.debug("使用Personal Access Token认证")
            else:
                logger.warning(f"不支持的认证类型: {auth_header.split(' ', 1)[0]}")
        else:
            # 使用配置中的默认认证信息
            if self.settings.confluence_personal_token:
                request.state.confluence_auth_type = "pat"
                request.state.confluence_token = self.settings.confluence_personal_token
                logger.debug("使用配置中的Personal Access Token")
            elif self.settings.confluence_api_token:
                request.state.confluence_auth_type = "basic"
                request.state.confluence_token = self.settings.confluence_api_token
                request.state.confluence_username = self.settings.confluence_username
                logger.debug("使用配置中的API Token")
        
        # 添加其他Confluence配置到请求状态
        request.state.confluence_url = self.settings.confluence_url
        request.state.confluence_ssl_verify = self.settings.confluence_ssl_verify
        request.state.confluence_spaces_filter = self.settings.confluence_spaces_filter
        
        response = await call_next(request)
        return response
