"""认证中间件"""

import base64
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import Settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件，处理Confluence Basic Auth认证信息"""
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并添加认证信息"""
        
        # 从请求头中获取Basic Auth认证信息（curl -u username:token）
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Basic "):
            # Basic Auth (curl -u username:token)
            try:
                # 解码 Base64 编码的凭据
                encoded_credentials = auth_header.split(" ", 1)[1].strip()
                decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
                
                # 分割用户名和令牌
                username, token = decoded_credentials.split(":", 1)
                
                request.state.confluence_auth_type = "basic"
                request.state.confluence_username = username
                request.state.confluence_token = token
                logger.debug("使用Basic Auth认证，用户名: %s", username)
                
            except (ValueError, base64.binascii.Error) as e:
                logger.warning(f"Basic Auth解码失败: {e}")
        else:
            # 使用配置中的默认认证信息
            if self.settings.confluence_api_token:
                request.state.confluence_auth_type = "basic"
                request.state.confluence_token = self.settings.confluence_api_token
                request.state.confluence_username = self.settings.confluence_username
                logger.debug("使用配置中的API Token")
            else:
                logger.warning("未提供Basic Auth头或配置中没有API Token")
        
        # 添加其他Confluence配置到请求状态
        request.state.confluence_url = self.settings.confluence_url
        request.state.confluence_ssl_verify = self.settings.confluence_ssl_verify
        request.state.confluence_spaces_filter = self.settings.confluence_spaces_filter
        
        response = await call_next(request)
        return response
