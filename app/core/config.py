"""应用配置模块"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用设置"""
    
    # 应用基本信息
    app_name: str = Field(default="confluence-mcp", description="应用名称")
    version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    log_level: str = Field(default="info", description="日志级别")
    reload: bool = Field(default=False, description="自动重载")
    
    # Confluence配置
    confluence_url: Optional[str] = Field(default=None, env="CONFLUENCE_URL", description="Confluence URL")
    confluence_username: Optional[str] = Field(default=None, env="CONFLUENCE_USERNAME", description="Confluence用户名")
    confluence_api_token: Optional[str] = Field(default=None, env="CONFLUENCE_API_TOKEN", description="Confluence API令牌")
    confluence_ssl_verify: bool = Field(default=True, env="CONFLUENCE_SSL_VERIFY", description="SSL验证")
    confluence_spaces_filter: Optional[str] = Field(default=None, env="CONFLUENCE_SPACES_FILTER", description="空间过滤器")
    
    # 代理配置
    http_proxy: Optional[str] = Field(default=None, env="HTTP_PROXY", description="HTTP代理")
    https_proxy: Optional[str] = Field(default=None, env="HTTPS_PROXY", description="HTTPS代理")
    socks_proxy: Optional[str] = Field(default=None, env="SOCKS_PROXY", description="SOCKS代理")
    no_proxy: Optional[str] = Field(default=None, env="NO_PROXY", description="不使用代理的地址")
    
    # 其他配置
    read_only_mode: bool = Field(default=False, env="READ_ONLY_MODE", description="只读模式")
    enabled_tools: Optional[str] = Field(default=None, env="ENABLED_TOOLS", description="启用的工具")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局设置实例
settings = Settings()
