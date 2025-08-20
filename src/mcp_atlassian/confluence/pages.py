"""Confluence页面操作模块。"""

import logging

from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAuthenticationError
from ..models.confluence import ConfluencePage
from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class PagesMixin(ConfluenceClient):
    """Confluence页面操作的混入类。"""

    def get_page_content(
        self, page_id: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage:
        """
        获取特定页面的内容。

        Args:
            page_id: 要检索的页面ID
            convert_to_markdown: 当为True时，以markdown格式返回内容，
                               否则返回原始HTML（仅关键字参数）

        Returns:
            包含页面内容和元数据的ConfluencePage模型

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
            Exception: 如果检索页面时发生错误
        """
        try:
            logger.debug(
                f"使用v1 API通过令牌/基本身份验证获取页面'{page_id}'"
            )
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand="body.storage,version,space,children.attachment",
            )

            space_key = page.get("space", {}).get("key", "")
            content = page["body"]["storage"]["value"]
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content, space_key=space_key, confluence_client=self.confluence
            )

            # 根据convert_to_markdown标志使用适当的内容格式
            page_content = processed_markdown if convert_to_markdown else processed_html

            # 创建并返回ConfluencePage模型
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # 使用我们的处理版本覆盖内容
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(
                f"检索页面ID {page_id} 的页面内容时发生错误: {str(e)}"
            )
            raise Exception(f"检索页面内容时发生错误: {str(e)}") from e

    def get_page_ancestors(self, page_id: str) -> list[ConfluencePage]:
        """
        获取特定页面的祖先（父页面）。

        Args:
            page_id: 要获取祖先的页面ID

        Returns:
            表示祖先的ConfluencePage模型列表，按层次顺序排列
                （直接父级在前，根祖先在后）

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
        """
        try:
            # 使用Atlassian Python API获取祖先
            ancestors = self.confluence.get_page_ancestors(page_id)

            # 处理每个祖先
            ancestor_models = []
            for ancestor in ancestors:
                # 创建页面模型而不获取内容
                page_model = ConfluencePage.from_api_response(
                    ancestor,
                    base_url=self.config.url,
                    include_body=False,
                )
                ancestor_models.append(page_model)

            return ancestor_models
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"获取页面{page_id}的祖先时发生错误: {str(e)}")
            logger.debug("完整异常详情:", exc_info=True)
            return []

    def get_page_by_title(
        self, space_key: str, title: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage | None:
        """
        从Confluence空间中按标题获取特定页面。

        Args:
            space_key: 要搜索的空间的键
            title: 要查找的页面标题
            convert_to_markdown: 当为True时，以markdown格式返回内容，
                               否则返回原始HTML（仅关键字参数）

        Returns:
            如果找到则返回ConfluencePage模型，否则返回None

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
            Exception: 如果检索页面时发生错误
        """
        try:
            page = self.confluence.get_page_by_title(
                space_key=space_key,
                title=title,
                expand="body.storage,version,space,children.attachment",
            )

            if not page:
                return None

            space_key = page.get("space", {}).get("key", "")
            content = page["body"]["storage"]["value"]
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                content, space_key=space_key, confluence_client=self.confluence
            )

            # 根据convert_to_markdown标志使用适当的内容格式
            page_content = processed_markdown if convert_to_markdown else processed_html

            # 创建并返回ConfluencePage模型
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # 使用我们的处理版本覆盖内容
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(
                f"检索页面标题{title}的页面内容时发生错误: {str(e)}"
            )
            raise Exception(f"检索页面内容时发生错误: {str(e)}") from e

    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
        content_representation: str | None = None,
    ) -> dict:
        """
        在指定空间中创建新页面。

        Args:
            space_key: 要在其中创建页面的空间的键
            title: 新页面的标题
            body: 新页面的内容
            parent_id: 可选的父页面ID，在其下创建
            content_representation: 内容表示格式（storage、wiki等）

        Returns:
            包含创建的页面信息的字典

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
            Exception: 如果创建页面时发生错误
        """
        try:
            # 确定表示格式
            if content_representation == "markdown":
                # 对于markdown，先转换为存储格式
                final_body = self.preprocessor.convert_to_storage_format(body)
                representation = "storage"
            elif content_representation == "wiki":
                final_body = body
                representation = "wiki"
            else:
                # 按原样使用body和指定的表示格式
                final_body = body
                representation = content_representation or "storage"
            
            logger.debug(
                f"使用v1 API通过令牌/基本身份验证创建页面'{title}'"
            )
            result = self.confluence.create_page(
                space=space_key,
                title=title,
                body=final_body,
                parent_id=parent_id,
                representation=representation,
            )
            return result
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"创建页面'{title}'时发生错误: {str(e)}")
            raise Exception(f"创建页面时发生错误: {str(e)}") from e

    def update_page(
        self,
        page_id: str,
        title: str | None = None,
        body: str | None = None,
        content_representation: str | None = None,
        version_comment: str | None = None,
    ) -> dict:
        """
        更新现有页面。

        Args:
            page_id: 要更新的页面ID
            title: 页面的新标题（可选）
            body: 页面的新内容（可选）
            content_representation: 内容表示格式（storage、wiki等）
            version_comment: 此版本更新的注释

        Returns:
            包含更新页面信息的字典

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
            Exception: 如果更新页面时发生错误
        """
        try:
            # 确定表示格式
            if content_representation == "markdown":
                # 对于markdown，先转换为存储格式
                final_body = self.preprocessor.convert_to_storage_format(body or "")
                representation = "storage"
            elif content_representation == "wiki":
                final_body = body or ""
                representation = "wiki"
            else:
                # 按原样使用body和指定的表示格式
                final_body = body or ""
                representation = content_representation or "storage"
            
            logger.debug(f"更新页面{page_id}，标题为'{title}'")
            logger.debug(
                f"使用v1 API通过令牌/基本身份验证更新页面'{page_id}'"
            )
            response = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=final_body,
                representation=representation,
                version_comment=version_comment,
            )
            return response
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"更新页面'{page_id}'时发生错误: {str(e)}")
            raise Exception(f"更新页面时发生错误: {str(e)}") from e

    def delete_page(self, page_id: str) -> bool:
        """
        根据ID删除页面。

        Args:
            page_id: 要删除的页面ID

        Returns:
            如果页面删除成功则为True，否则为False

        Raises:
            MCPAtlassianAuthenticationError: 如果Confluence API身份验证失败（401/403）
            Exception: 如果删除页面时发生错误
        """
        try:
            logger.debug(f"删除页面{page_id}")
            logger.debug(
                f"使用v1 API通过令牌/基本身份验证删除页面'{page_id}'"
            )
            response = self.confluence.remove_page(page_id=page_id)
            # Atlassian库的remove_page返回REST API调用的原始响应。
            # 对于成功的删除，我们应该得到一个响应对象，但它可能为空（HTTP 204 No Content）。
            return response is not None
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Confluence API身份验证失败（{http_err.response.status_code}）。"
                    "令牌可能已过期或无效。请验证凭据。"
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"API调用期间的HTTP错误: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"删除页面'{page_id}'时发生错误: {str(e)}")
            raise Exception(f"删除页面时发生错误: {str(e)}") from e