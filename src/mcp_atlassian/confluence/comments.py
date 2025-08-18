"""Confluence评论操作模块。"""

import logging

import requests

from ..models.confluence import ConfluenceComment
from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class CommentsMixin(ConfluenceClient):
    """Confluence评论操作的混入类。"""

    def get_page_comments(
        self, page_id: str, *, return_markdown: bool = True
    ) -> list[ConfluenceComment]:
        """
        获取特定页面的所有评论。

        Args:
            page_id: 要获取评论的页面ID
            return_markdown: 当为True时，以markdown格式返回内容，
                           否则返回原始HTML（仅关键字参数）

        Returns:
            包含评论内容和元数据的ConfluenceComment模型列表
        """
        try:
            # 获取页面信息以提取空间详情
            page = self.confluence.get_page_by_id(page_id=page_id, expand="space")
            space_key = page.get("space", {}).get("key", "")

            # 获取带有扩展内容的评论
            comments_response = self.confluence.get_page_comments(
                content_id=page_id, expand="body.view.value,version", depth="all"
            )

            # 处理每个评论
            comment_models = []
            for comment_data in comments_response.get("results", []):
                # 根据格式获取内容
                body = comment_data["body"]["view"]["value"]
                processed_html, processed_markdown = (
                    self.preprocessor.process_html_content(
                        body, space_key=space_key, confluence_client=self.confluence
                    )
                )

                # 创建评论数据的副本以进行修改
                modified_comment_data = comment_data.copy()

                # 根据返回格式修改body值
                if "body" not in modified_comment_data:
                    modified_comment_data["body"] = {}
                if "view" not in modified_comment_data["body"]:
                    modified_comment_data["body"]["view"] = {}

                # 根据返回格式设置适当的内容
                modified_comment_data["body"]["view"]["value"] = (
                    processed_markdown if return_markdown else processed_html
                )

                # 使用处理后的内容创建模型
                comment_model = ConfluenceComment.from_api_response(
                    modified_comment_data,
                    base_url=self.config.url,
                )

                comment_models.append(comment_model)

            return comment_models

        except KeyError as e:
            logger.error(f"评论数据中缺少键: {str(e)}")
            return []
        except requests.RequestException as e:
            logger.error(f"获取评论时发生网络错误: {str(e)}")
            return []
        except (ValueError, TypeError) as e:
            logger.error(f"处理评论数据时发生错误: {str(e)}")
            return []
        except Exception as e:  # noqa: BLE001 - Intentional fallback with full logging
            logger.error(f"获取评论时发生意外错误: {str(e)}")
            logger.debug("评论的完整异常详情:", exc_info=True)
            return []

    def add_comment(self, page_id: str, content: str) -> ConfluenceComment | None:
        """
        向Confluence页面添加评论。

        Args:
            page_id: 要添加评论的页面ID
            content: 评论的内容（以Confluence存储格式）

        Returns:
            如果评论添加成功则返回ConfluenceComment对象，否则返回None
        """
        try:
            # 获取页面信息以提取空间详情
            page = self.confluence.get_page_by_id(page_id=page_id, expand="space")
            space_key = page.get("space", {}).get("key", "")

            # 如果需要，将markdown转换为Confluence存储格式
            # atlassian-python-api期望内容以Confluence存储格式提供
            if not content.strip().startswith("<"):
                # 如果内容看起来不是HTML/XML，则将其视为markdown
                content = self.preprocessor.markdown_to_confluence_storage(content)

            # 通过Confluence API添加评论
            response = self.confluence.add_comment(page_id, content)

            if not response:
                logger.error("添加评论失败：空响应")
                return None

            # 处理评论以返回一致的模型
            processed_html, processed_markdown = self.preprocessor.process_html_content(
                response.get("body", {}).get("view", {}).get("value", ""),
                space_key=space_key,
                confluence_client=self.confluence,
            )

            # 修改响应以包含处理后的内容
            modified_response = response.copy()
            if "body" not in modified_response:
                modified_response["body"] = {}
            if "view" not in modified_response["body"]:
                modified_response["body"]["view"] = {}

            modified_response["body"]["view"]["value"] = processed_markdown

            # 创建并返回评论模型
            return ConfluenceComment.from_api_response(
                modified_response,
                base_url=self.config.url,
            )

        except requests.RequestException as e:
            logger.error(f"添加评论时发生网络错误: {str(e)}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"处理评论数据时发生错误: {str(e)}")
            return None
        except Exception as e:  # noqa: BLE001 - Intentional fallback with full logging
            logger.error(f"添加评论时发生意外错误: {str(e)}")
            logger.debug("添加评论的完整异常详情:", exc_info=True)
            return None
