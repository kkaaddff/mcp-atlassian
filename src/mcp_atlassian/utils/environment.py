"""与环境检查相关的实用函数。"""

import logging
import os

from .urls import is_atlassian_cloud_url

logger = logging.getLogger("mcp-confluence.utils.environment")


def get_available_services() -> dict[str, bool | None]:
    """根据环境变量确定哪些服务可用。"""
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_is_setup = False
    if confluence_url:
        is_cloud = is_atlassian_cloud_url(confluence_url)

        if is_cloud:  # Cloud
            if all(
                [
                    os.getenv("CONFLUENCE_USERNAME"),
                    os.getenv("CONFLUENCE_API_TOKEN"),
                ]
            ):
                confluence_is_setup = True
                logger.info("使用 Confluence Cloud 基本身份验证（API 令牌）")
        else:  # Server/Data Center
            if os.getenv("CONFLUENCE_PERSONAL_TOKEN") or (
                os.getenv("CONFLUENCE_USERNAME") and os.getenv("CONFLUENCE_API_TOKEN")
            ):
                confluence_is_setup = True
                logger.info(
                    "使用 Confluence Server/Data Center 身份验证（PAT 或基本身份验证）"
                )

    if not confluence_is_setup:
        logger.info(
            "Confluence 未配置或缺少必需的环境变量。"
        )

    return {"confluence": confluence_is_setup}
