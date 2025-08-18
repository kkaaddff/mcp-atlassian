"""与环境检查相关的实用函数。"""

import logging
import os

logger = logging.getLogger("mcp-confluence.utils.environment")


def get_available_services() -> dict[str, bool | None]:
    """根据环境变量确定哪些服务可用。"""
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_is_setup = False
    if confluence_url:
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
