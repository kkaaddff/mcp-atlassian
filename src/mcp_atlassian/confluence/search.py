"""Confluence搜索操作模块。"""

import logging

from ..models.confluence import (
    ConfluencePage,
    ConfluenceSearchResult,
    ConfluenceUserSearchResult,
    ConfluenceUserSearchResults,
)
from ..utils.decorators import handle_atlassian_api_errors
from .client import ConfluenceClient
from .utils import quote_cql_identifier_if_needed

logger = logging.getLogger("mcp-atlassian")


class SearchMixin(ConfluenceClient):
    """Confluence搜索操作的混入类。"""

    @handle_atlassian_api_errors("Confluence API")
    def search(
        self, cql: str, limit: int = 10, spaces_filter: str | None = None
    ) -> list[ConfluencePage]:
        """
        使用Confluence查询语言（CQL）搜索内容。

        Args:
            cql: Confluence查询语言字符串
            limit: 要返回的最大结果数
            spaces_filter: 可选的用于过滤的空间键逗号分隔列表，
                覆盖配置

        Returns:
            包含搜索结果的ConfluencePage模型列表

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败
                （401/403）
        """
        # 如果提供了spaces_filter参数，则使用它，否则回退到配置
        filter_to_use = spaces_filter or self.config.spaces_filter

        # 如果存在空间过滤器，则应用它
        if filter_to_use:
            # 按逗号分割空间过滤器并处理可能的空白
            spaces = [s.strip() for s in filter_to_use.split(",")]

            # 使用适当的引用为每个空间键构建空间过滤器查询部分
            space_query = " OR ".join(
                [f"space = {quote_cql_identifier_if_needed(space)}" for space in spaces]
            )

            # 使用括号将空间过滤器添加到现有查询中
            if cql and space_query:
                if "space = " not in cql:  # 仅在尚未按空间过滤时添加
                    cql = f"({cql}) AND ({space_query})"
            else:
                cql = space_query

            logger.info(f"将空间过滤器应用于查询: {cql}")

        # 执行CQL搜索查询
        results = self.confluence.cql(cql=cql, limit=limit)

        # 将响应转换为搜索结果模型
        search_result = ConfluenceSearchResult.from_api_response(
            results,
            base_url=self.config.url,
            cql_query=cql,
        )

        # 将结果摘要处理为内容
        processed_pages = []
        for page in search_result.results:
            # 从原始搜索结果中获取摘要
            for result_item in results.get("results", []):
                if result_item.get("content", {}).get("id") == page.id:
                    excerpt = result_item.get("excerpt", "")
                    if excerpt:
                        # 将摘要作为HTML内容处理
                        space_key = page.space.key if page.space else ""
                        _, processed_markdown = self.preprocessor.process_html_content(
                            excerpt,
                            space_key=space_key,
                            confluence_client=self.confluence,
                        )
                        # 创建带有处理内容的新页面
                        page.content = processed_markdown
                    break

            processed_pages.append(page)

        # 返回带有处理内容的结果页面列表
        return processed_pages

    @handle_atlassian_api_errors("Confluence API")
    def search_user(
        self, cql: str, limit: int = 10
    ) -> list[ConfluenceUserSearchResult]:
        """
        使用Confluence查询语言（CQL）搜索用户。

        Args:
            cql: 用于用户搜索的Confluence查询语言字符串
            limit: 要返回的最大结果数

        Returns:
            包含用户搜索结果的ConfluenceUserSearchResult模型列表

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败
                （401/403）
        """
        # 使用直接API端点执行用户搜索查询
        results = self.confluence.get(
            "rest/api/search/user", params={"cql": cql, "limit": limit}
        )

        # 将响应转换为用户搜索结果模型
        search_result = ConfluenceUserSearchResults.from_api_response(results or {})

        # 返回用户搜索结果列表
        return search_result.results
