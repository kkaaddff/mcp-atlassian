"""Confluence空间操作模块。"""

import logging
from typing import cast

import requests

from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class SpacesMixin(ConfluenceClient):
    """Confluence空间操作的混入类。"""

    def get_spaces(self, start: int = 0, limit: int = 10) -> dict[str, object]:
        """
        获取所有可用的空间。

        Args:
            start: 分页的起始索引
            limit: 要返回的最大空间数

        Returns:
            包含空间信息和元数据的字典
        """
        spaces = self.confluence.get_all_spaces(start=start, limit=limit)
        # 将返回值转换为预期类型
        return cast(dict[str, object], spaces)

    def get_user_contributed_spaces(self, limit: int = 250) -> dict:
        """
        获取当前用户贡献过的空间。

        Args:
            limit: 要返回的最大结果数

        Returns:
            空间键到空间信息的字典
        """
        try:
            # 使用CQL查找用户贡献过的内容
            cql = "contributor = currentUser() order by lastmodified DESC"
            results = self.confluence.cql(cql=cql, limit=limit)

            # 提取和去重空间
            spaces = {}
            for result in results.get("results", []):
                space_key = None
                space_name = None

                # 尝试从容器中提取空间
                if "resultGlobalContainer" in result:
                    container = result.get("resultGlobalContainer", {})
                    space_name = container.get("title")
                    display_url = container.get("displayUrl", "")
                    if display_url and "/spaces/" in display_url:
                        space_key = display_url.split("/spaces/")[1].split("/")[0]

                # 尝试从内容可扩展项中提取
                if (
                    not space_key
                    and "content" in result
                    and "_expandable" in result["content"]
                ):
                    expandable = result["content"].get("_expandable", {})
                    space_path = expandable.get("space", "")
                    if space_path and space_path.startswith("/rest/api/space/"):
                        space_key = space_path.split("/rest/api/space/")[1]

                # 尝试从URL中提取
                if not space_key and "url" in result:
                    url = result.get("url", "")
                    if url and url.startswith("/spaces/"):
                        space_key = url.split("/spaces/")[1].split("/")[0]

                # 仅在找到空间键且它不在我们的结果中时才添加
                if space_key and space_key not in spaces:
                    # 如果无法提取所有字段，则添加一些默认值
                    space_name = space_name or f"空间 {space_key}"
                    spaces[space_key] = {"key": space_key, "name": space_name}

            return spaces

        except KeyError as e:
            logger.error(f"Confluence空间数据中缺少键: {str(e)}")
            return {}
        except ValueError as e:
            logger.error(f"Confluence空间中的值无效: {str(e)}")
            return {}
        except TypeError as e:
            logger.error(f"处理Confluence空间时发生类型错误: {str(e)}")
            return {}
        except requests.RequestException as e:
            logger.error(f"获取空间时发生网络错误: {str(e)}")
            return {}
        except Exception as e:  # noqa: BLE001 - Intentional fallback with logging
            logger.error(f"获取Confluence空间时发生意外错误: {str(e)}")
            logger.debug("Confluence空间的完整异常详情:", exc_info=True)
            return {}
