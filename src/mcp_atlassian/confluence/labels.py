"""Confluence标签操作模块。"""

import logging

from ..models.confluence import ConfluenceLabel
from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class LabelsMixin(ConfluenceClient):
    """Confluence标签操作的混入类。"""

    def get_page_labels(self, page_id: str) -> list[ConfluenceLabel]:
        """
        获取特定页面的所有标签。

        Args:
            page_id: 要获取标签的页面ID

        Returns:
            包含标签内容和元数据的ConfluenceLabel模型列表

        Raises:
            Exception: 如果获取标签时发生错误
        """
        try:
            # 获取带有扩展内容的标签
            labels_response = self.confluence.get_page_labels(page_id=page_id)

            # 处理每个标签
            label_models = []
            for label_data in labels_response.get("results"):
                # 使用处理后的内容创建模型
                label_model = ConfluenceLabel.from_api_response(
                    label_data,
                    base_url=self.config.url,
                )

                label_models.append(label_model)

            return label_models

        except Exception as e:
            logger.error(f"从页面{page_id}获取标签失败: {str(e)}")
            raise Exception(
                f"从页面{page_id}获取标签失败: {str(e)}"
            ) from e

    def add_page_label(self, page_id: str, name: str) -> list[ConfluenceLabel]:
        """
        向Confluence页面添加标签。

        Args:
            page_id: 要更新的页面ID
            name: 标签的名称

        Returns:
            包含更新后标签列表的标签模型

        Raises:
            Exception: 如果添加标签时发生错误
        """
        try:
            logger.debug(f"向页面{page_id}添加名为'{name}'的标签")

            update_kwargs = {
                "page_id": page_id,
                "label": name,
            }
            response = self.confluence.set_page_label(**update_kwargs)

            # 更新后，刷新页面数据
            return self.get_page_labels(page_id)
        except Exception as e:
            logger.error(f"向页面{page_id}添加标签'{name}'时发生错误: {str(e)}")
            raise Exception(
                f"向页面{page_id}添加标签'{name}'失败: {str(e)}"
            ) from e
