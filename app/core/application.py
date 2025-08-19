"""FastAPI应用创建和配置"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .config import Settings
from ..api import confluence_router
from ..middleware.auth import AuthMiddleware
from ..middleware.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    """创建FastAPI应用实例"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="TFA算法服务器 - 基于Confluence的HTTP API服务",
        debug=settings.debug
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加自定义中间件
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=settings)
    
    # 注册路由
    app.include_router(confluence_router, prefix="/api/v1")
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {"status": "ok", "app": settings.app_name, "version": settings.version}
    
    # 根路径
    @app.get("/")
    async def root():
        """根路径信息"""
        return {
            "message": f"欢迎使用 {settings.app_name}",
            "version": settings.version,
            "docs": "/docs",
            "health": "/health"
        }
    
    # 全局异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "status_code": exc.status_code}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "内部服务器错误", "status_code": 500}
        )
    
    logger.info(f"FastAPI应用已创建: {settings.app_name} v{settings.version}")
    return app
