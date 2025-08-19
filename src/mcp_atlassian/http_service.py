"""Confluence 的 HTTP 服务包装器，具有可配置的基础 URL 和基于请求的认证。"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp_atlassian.confluence import ConfluenceFetcher, ConfluenceConfig

logger = logging.getLogger("confluence-mcp.http_service")


class ConfluenceAuthRequest(BaseModel):
    """具有认证的 Confluence 操作的请求模型。"""
    
    base_url: str = Field(..., description="Confluence 实例的基础 URL")
    auth_type: str = Field(..., description="认证类型：'basic' 或 'pat'")
    username: Optional[str] = Field(None, description="基础认证的用户名")
    api_token: Optional[str] = Field(None, description="基础认证的 API 令牌")
    personal_token: Optional[str] = Field(None, description="Server/DC 的个人访问令牌")
    operation: str = Field(..., description="要执行的操作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作的参数")


class ConfluenceAuthService:
    """用于处理具有基于请求认证的 Confluence 操作的服务。"""
    
    def __init__(self):
        self.logger = logging.getLogger("confluence-mcp.auth_service")
    
    async def create_config_from_request(self, request: ConfluenceAuthRequest) -> ConfluenceConfig:
        """根据请求参数创建 ConfluenceConfig。"""
        
        
        if request.auth_type == "basic":
            if not request.username or not request.api_token:
                raise HTTPException(status_code=400, detail="基础认证需要用户名和 API 令牌")
        
        elif request.auth_type == "pat":
            if not request.personal_token:
                raise HTTPException(status_code=400, detail="PAT 认证需要个人令牌")
        
        elif request.auth_type == "pat":
            if not request.personal_token:
                raise HTTPException(status_code=400, detail="PAT 认证需要个人令牌")
        else:
            raise HTTPException(status_code=400, detail=f"不支持的认证类型：{request.auth_type}")
        
        # 创建 ConfluenceConfig
        config = ConfluenceConfig(
            url=request.base_url,
            auth_type=request.auth_type,
            username=request.username,
            api_token=request.api_token,
            personal_token=request.personal_token,
            ssl_verify=True,  # 默认 SSL 验证
        )
        
        # 验证配置
        if not config.is_auth_configured():
            raise HTTPException(status_code=400, detail="认证配置不完整")
        
        return config
    
    async def execute_operation(self, config: ConfluenceConfig, operation: str, parameters: Dict[str, Any]) -> Any:
        """使用给定的配置执行 Confluence 操作。"""
        
        try:
            # 使用配置创建 ConfluenceFetcher
            fetcher = ConfluenceFetcher(config=config)
            
            # 执行请求的操作
            if operation == "get_page":
                page_id = parameters.get("page_id")
                if not page_id:
                    raise HTTPException(status_code=400, detail="get_page 操作需要 page_id")
                return await fetcher.get_page_by_id(page_id)
            
            elif operation == "search_pages":
                query = parameters.get("query", "")
                space_key = parameters.get("space_key")
                limit = parameters.get("limit", 50)
                return await fetcher.search_content(query, space_key=space_key, limit=limit)
            
            elif operation == "get_space":
                space_key = parameters.get("space_key")
                if not space_key:
                    raise HTTPException(status_code=400, detail="get_space 操作需要 space_key")
                return await fetcher.get_space(space_key)
            
            elif operation == "list_spaces":
                limit = parameters.get("limit", 50)
                return await fetcher.get_spaces(limit=limit)
            
            elif operation == "create_page":
                space_key = parameters.get("space_key")
                title = parameters.get("title")
                content = parameters.get("content")
                parent_id = parameters.get("parent_id")
                
                if not all([space_key, title, content]):
                    raise HTTPException(status_code=400, detail="create_page 操作需要 space_key、title 和 content")
                
                return await fetcher.create_page(space_key, title, content, parent_id)
            
            elif operation == "update_page":
                page_id = parameters.get("page_id")
                title = parameters.get("title")
                content = parameters.get("content")
                version = parameters.get("version")
                
                if not page_id:
                    raise HTTPException(status_code=400, detail="update_page 操作需要 page_id")
                
                return await fetcher.update_page(page_id, title, content, version)
            
            else:
                raise HTTPException(status_code=400, detail=f"不支持的操作：{operation}")
        
        except Exception as e:
            self.logger.error(f"执行操作 {operation} 时出错：{e}")
            raise HTTPException(status_code=500, detail=f"内部服务器错误：{str(e)}")


# 初始化 FastAPI 应用
app = FastAPI(
    title="Confluence HTTP 服务",
    description="具有可配置基础 URL 和基于请求认证的 Confluence 操作 HTTP 服务",
    version="1.0.0"
)

# 初始化认证服务
auth_service = ConfluenceAuthService()


@app.post("/confluence/execute")
async def execute_confluence_operation(request: ConfluenceAuthRequest):
    """使用提供的认证执行 Confluence 操作。"""
    
    try:
        # 从请求创建配置
        config = await auth_service.create_config_from_request(request)
        
        # 执行操作
        result = await auth_service.execute_operation(config, request.operation, request.parameters)
        
        return JSONResponse(content={"success": True, "data": result})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"execute_confluence_operation 中出现意外错误：{e}")
        raise HTTPException(status_code=500, detail=f"内部服务器错误：{str(e)}")


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "healthy", "service": "confluence-http-service"}


@app.get("/")
async def root():
    """包含服务信息的根端点。"""
    return {
        "service": "Confluence HTTP 服务",
        "version": "1.0.0",
        "description": "具有可配置基础 URL 和基于请求认证的 Confluence 操作 HTTP 服务",
        "endpoints": {
            "POST /confluence/execute": "执行 Confluence 操作",
            "GET /health": "健康检查",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)