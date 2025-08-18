"""Utility functions related to environment checking."""

import logging
import os

from .urls import is_atlassian_cloud_url

logger = logging.getLogger("mcp-confluence.utils.environment")


def get_available_services() -> dict[str, bool | None]:
    """Determine which services are available based on environment variables."""
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_is_setup = False
    if confluence_url:
        is_cloud = is_atlassian_cloud_url(confluence_url)

        # OAuth check (highest precedence, applies to Cloud)
        if all(
            [
                os.getenv("CONFLUENCE_OAUTH_CLIENT_ID"),
                os.getenv("CONFLUENCE_OAUTH_CLIENT_SECRET"),
                os.getenv("CONFLUENCE_OAUTH_REDIRECT_URI"),
                os.getenv("CONFLUENCE_OAUTH_SCOPE"),
                os.getenv(
                    "CONFLUENCE_OAUTH_CLOUD_ID"
                ),  # CLOUD_ID is essential for OAuth client init
            ]
        ):
            confluence_is_setup = True
            logger.info(
                "Using Confluence OAuth 2.0 (3LO) authentication (Cloud-only features)"
            )
        elif all(
            [
                os.getenv("CONFLUENCE_OAUTH_ACCESS_TOKEN"),
                os.getenv("CONFLUENCE_OAUTH_CLOUD_ID"),
            ]
        ):
            confluence_is_setup = True
            logger.info(
                "Using Confluence OAuth 2.0 (3LO) authentication (Cloud-only features) "
                "with provided access token"
            )
        elif is_cloud:  # Cloud non-OAuth
            if all(
                [
                    os.getenv("CONFLUENCE_USERNAME"),
                    os.getenv("CONFLUENCE_API_TOKEN"),
                ]
            ):
                confluence_is_setup = True
                logger.info("Using Confluence Cloud Basic Authentication (API Token)")
        else:  # Server/Data Center non-OAuth
            if os.getenv("CONFLUENCE_PERSONAL_TOKEN") or (
                os.getenv("CONFLUENCE_USERNAME") and os.getenv("CONFLUENCE_API_TOKEN")
            ):
                confluence_is_setup = True
                logger.info(
                    "Using Confluence Server/Data Center authentication (PAT or Basic Auth)"
                )
    elif os.getenv("CONFLUENCE_OAUTH_ENABLE", "").lower() in ("true", "1", "yes"):
        confluence_is_setup = True
        logger.info(
            "Using Confluence minimal OAuth configuration - expecting user-provided tokens via headers"
        )

    if not confluence_is_setup:
        logger.info(
            "Confluence is not configured or required environment variables are missing."
        )

    return {"confluence": confluence_is_setup}
