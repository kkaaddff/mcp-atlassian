"""Confluence服务层"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException

# 重用现有的Confluence模块
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.confluence.pages import PagesMixin
from mcp_atlassian.confluence.search import SearchMixin
from mcp_atlassian.confluence.spaces import SpacesMixin
from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


class ConfluenceService(PagesMixin, SearchMixin, SpacesMixin):
    """Confluence服务类，整合所有Confluence操作"""
    
    def __init__(self, config: Optional[ConfluenceConfig] = None):
        """初始化Confluence服务
        
        Args:
            config: Confluence配置，如果为None则从环境变量加载
        """
        try:
            super().__init__(config)
            logger.info("Confluence服务初始化成功")
        except Exception as e:
            logger.error(f"Confluence服务初始化失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Confluence服务初始化失败: {str(e)}"
            )
    
    @classmethod
    def create_from_request(
        cls, 
        confluence_url: Optional[str] = None,
        confluence_token: Optional[str] = None,
        confluence_username: Optional[str] = None,
        auth_type: str = "basic",
        ssl_verify: bool = True,
        spaces_filter: Optional[str] = None
    ) -> "ConfluenceService":
        """从请求参数创建Confluence服务实例
        
        Args:
            confluence_url: Confluence URL
            confluence_token: 认证令牌
            confluence_username: 用户名（基本认证时需要）
            auth_type: 认证类型 ("basic" 或 "pat")
            ssl_verify: SSL验证
            spaces_filter: 空间过滤器
            
        Returns:
            ConfluenceService实例
            
        Raises:
            HTTPException: 配置无效时
        """
        if not confluence_url:
            raise HTTPException(
                status_code=400,
                detail="缺少Confluence URL配置"
            )
        
        if not confluence_token:
            raise HTTPException(
                status_code=400,
                detail="缺少Confluence认证令牌"
            )
        
        try:
            if auth_type == "pat":
                config = ConfluenceConfig(
                    url=confluence_url,
                    personal_token=confluence_token,
                    ssl_verify=ssl_verify,
                    spaces_filter=spaces_filter
                )
            else:  # basic
                if not confluence_username:
                    raise HTTPException(
                        status_code=400,
                        detail="基本认证需要用户名"
                    )
                config = ConfluenceConfig(
                    url=confluence_url,
                    username=confluence_username,
                    api_token=confluence_token,
                    ssl_verify=ssl_verify,
                    spaces_filter=spaces_filter
                )
            
            return cls(config)
            
        except MCPAtlassianAuthenticationError as e:
            logger.error(f"Confluence认证失败: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Confluence认证失败: {str(e)}"
            )
        except Exception as e:
            logger.error(f"创建Confluence服务失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"创建Confluence服务失败: {str(e)}"
            )
    
    async def get_page_by_id(
        self, 
        page_id: str, 
        convert_to_markdown: bool = True
    ) -> Dict[str, Any]:
        """获取页面内容
        
        Args:
            page_id: 页面ID
            convert_to_markdown: 是否转换为Markdown格式
            
        Returns:
            页面内容字典
        """
        try:
            page = self.get_page_content(page_id, convert_to_markdown=convert_to_markdown)
            return page.model_dump()
        except MCPAtlassianAuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取页面失败: {str(e)}")
    
    async def search_content(
        self, 
        cql: str, 
        limit: int = 10, 
        spaces_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """搜索内容
        
        Args:
            cql: CQL查询语句
            limit: 结果限制
            spaces_filter: 空间过滤器
            
        Returns:
            搜索结果列表
        """
        try:
            results = self.search(cql, limit=limit, spaces_filter=spaces_filter)
            return [result.model_dump() for result in results]
        except MCPAtlassianAuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
    
    async def get_all_spaces(
        self, 
        start: int = 0, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """获取所有空间
        
        Args:
            start: 起始索引
            limit: 结果限制
            
        Returns:
            空间信息字典
        """
        try:
            spaces = self.get_spaces(start=start, limit=limit)
            return spaces
        except MCPAtlassianAuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            logger.error(f"获取空间失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取空间失败: {str(e)}")
    
    async def get_user_spaces(self, limit: int = 250) -> Dict[str, Any]:
        """获取用户贡献的空间
        
        Args:
            limit: 结果限制
            
        Returns:
            用户空间字典
        """
        try:
            spaces = self.get_user_contributed_spaces(limit=limit)
            return spaces
        except MCPAtlassianAuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
        except Exception as e:
            logger.error(f"获取用户空间失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取用户空间失败: {str(e)}")
