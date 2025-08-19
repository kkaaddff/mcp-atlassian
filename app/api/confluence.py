"""Confluence API路由"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field

from ..services.confluence_service import ConfluenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/confluence", tags=["confluence"])


# 请求和响应模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    cql: str = Field(..., description="CQL查询语句")
    limit: int = Field(default=10, ge=1, le=100, description="结果数量限制")
    spaces_filter: Optional[str] = Field(default=None, description="空间过滤器")


class PageResponse(BaseModel):
    """页面响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Dict[str, Any] = Field(..., description="页面数据")


class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: List[Dict[str, Any]] = Field(..., description="搜索结果")
    total: int = Field(..., description="结果总数")


class SpacesResponse(BaseModel):
    """空间响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Dict[str, Any] = Field(..., description="空间数据")


def get_confluence_service(request: Request) -> ConfluenceService:
    """获取Confluence服务实例的依赖项"""
    try:
        # 从请求状态获取认证信息
        confluence_url = getattr(request.state, 'confluence_url', None)
        confluence_token = getattr(request.state, 'confluence_token', None)
        confluence_username = getattr(request.state, 'confluence_username', None)
        auth_type = getattr(request.state, 'confluence_auth_type', 'basic')
        ssl_verify = getattr(request.state, 'confluence_ssl_verify', True)
        spaces_filter = getattr(request.state, 'confluence_spaces_filter', None)
        
        return ConfluenceService.create_from_request(
            confluence_url=confluence_url,
            confluence_token=confluence_token,
            confluence_username=confluence_username,
            auth_type=auth_type,
            ssl_verify=ssl_verify,
            spaces_filter=spaces_filter
        )
    except Exception as e:
        logger.error(f"创建Confluence服务失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"无法创建Confluence服务: {str(e)}"
        )


@router.get("/health")
async def confluence_health():
    """Confluence服务健康检查"""
    return {"status": "ok", "service": "confluence"}


@router.get("/pages/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: str,
    convert_to_markdown: bool = Query(default=True, description="是否转换为Markdown格式"),
    confluence_service: ConfluenceService = Depends(get_confluence_service)
):
    """获取指定页面的内容
    
    Args:
        page_id: 页面ID
        convert_to_markdown: 是否转换为Markdown格式
        confluence_service: Confluence服务实例
        
    Returns:
        页面内容响应
    """
    logger.info(f"获取页面: {page_id}")
    
    try:
        page_data = await confluence_service.get_page_by_id(
            page_id, 
            convert_to_markdown=convert_to_markdown
        )
        
        return PageResponse(
            success=True,
            data=page_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取页面失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取页面失败: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_content(
    search_request: SearchRequest,
    confluence_service: ConfluenceService = Depends(get_confluence_service)
):
    """搜索Confluence内容
    
    Args:
        search_request: 搜索请求参数
        confluence_service: Confluence服务实例
        
    Returns:
        搜索结果响应
    """
    logger.info(f"搜索内容: {search_request.cql}")
    
    try:
        results = await confluence_service.search_content(
            cql=search_request.cql,
            limit=search_request.limit,
            spaces_filter=search_request.spaces_filter
        )
        
        return SearchResponse(
            success=True,
            data=results,
            total=len(results)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse)
async def search_content_get(
    cql: str = Query(..., description="CQL查询语句"),
    limit: int = Query(default=10, ge=1, le=100, description="结果数量限制"),
    spaces_filter: Optional[str] = Query(default=None, description="空间过滤器"),
    confluence_service: ConfluenceService = Depends(get_confluence_service)
):
    """使用GET方法搜索Confluence内容
    
    Args:
        cql: CQL查询语句
        limit: 结果数量限制
        spaces_filter: 空间过滤器
        confluence_service: Confluence服务实例
        
    Returns:
        搜索结果响应
    """
    logger.info(f"GET搜索内容: {cql}")
    
    search_request = SearchRequest(
        cql=cql,
        limit=limit,
        spaces_filter=spaces_filter
    )
    
    return await search_content(search_request, confluence_service)


@router.get("/spaces", response_model=SpacesResponse)
async def get_spaces(
    start: int = Query(default=0, ge=0, description="起始索引"),
    limit: int = Query(default=10, ge=1, le=100, description="结果数量限制"),
    confluence_service: ConfluenceService = Depends(get_confluence_service)
):
    """获取所有可用的空间
    
    Args:
        start: 起始索引
        limit: 结果数量限制
        confluence_service: Confluence服务实例
        
    Returns:
        空间信息响应
    """
    logger.info(f"获取空间: start={start}, limit={limit}")
    
    try:
        spaces_data = await confluence_service.get_all_spaces(
            start=start,
            limit=limit
        )
        
        return SpacesResponse(
            success=True,
            data=spaces_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取空间失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取空间失败: {str(e)}"
        )


@router.get("/spaces/user", response_model=SpacesResponse)
async def get_user_spaces(
    limit: int = Query(default=250, ge=1, le=1000, description="结果数量限制"),
    confluence_service: ConfluenceService = Depends(get_confluence_service)
):
    """获取用户贡献的空间
    
    Args:
        limit: 结果数量限制
        confluence_service: Confluence服务实例
        
    Returns:
        用户空间信息响应
    """
    logger.info(f"获取用户空间: limit={limit}")
    
    try:
        spaces_data = await confluence_service.get_user_spaces(limit=limit)
        
        return SpacesResponse(
            success=True,
            data=spaces_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户空间失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取用户空间失败: {str(e)}"
        )
