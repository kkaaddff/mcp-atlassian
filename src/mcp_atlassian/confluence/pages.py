"""Module for Confluence page operations."""

import logging

import requests
from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAuthenticationError
from ..models.confluence import ConfluencePage
from .client import ConfluenceClient

logger = logging.getLogger("mcp-atlassian")


class PagesMixin(ConfluenceClient):
    """Mixin for Confluence page operations."""

    def get_page_content(
        self, page_id: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage:
        """
        Get content of a specific page.

        Args:
            page_id: The ID of the page to retrieve
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            ConfluencePage model containing the page content and metadata

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error retrieving the page
        """
        try:
            logger.debug(
                f"Using v1 API for token/basic authentication to get page '{page_id}'"
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

            # Use the appropriate content format based on the convert_to_markdown flag
            page_content = processed_markdown if convert_to_markdown else processed_html

            # Create and return the ConfluencePage model
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # Override content with our processed version
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                is_cloud=self.config.is_cloud,
            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(
                f"Error retrieving page content for page ID {page_id}: {str(e)}"
            )
            raise Exception(f"Error retrieving page content: {str(e)}") from e

    def get_page_ancestors(self, page_id: str) -> list[ConfluencePage]:
        """
        Get ancestors (parent pages) of a specific page.

        Args:
            page_id: The ID of the page to get ancestors for

        Returns:
            List of ConfluencePage models representing the ancestors in hierarchical order
                (immediate parent first, root ancestor last)

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
        """
        try:
            # Use the Atlassian Python API to get ancestors
            ancestors = self.confluence.get_page_ancestors(page_id)

            # Process each ancestor
            ancestor_models = []
            for ancestor in ancestors:
                # Create the page model without fetching content
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
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"Error fetching ancestors for page {page_id}: {str(e)}")
            logger.debug("Full exception details:", exc_info=True)
            return []

    def get_page_by_title(
        self, space_key: str, title: str, *, convert_to_markdown: bool = True
    ) -> ConfluencePage | None:
        """
        Get a specific page by its title from a Confluence space.

        Args:
            space_key: The key of the space to search in
            title: The title of the page to find
            convert_to_markdown: When True, returns content in markdown format,
                               otherwise returns raw HTML (keyword-only)

        Returns:
            ConfluencePage model if found, None otherwise

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error retrieving the page
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

            # Use the appropriate content format based on the convert_to_markdown flag
            page_content = processed_markdown if convert_to_markdown else processed_html

            # Create and return the ConfluencePage model
            return ConfluencePage.from_api_response(
                page,
                base_url=self.config.url,
                include_body=True,
                # Override content with our processed version
                content_override=page_content,
                content_format="storage" if not convert_to_markdown else "markdown",
                is_cloud=self.config.is_cloud,
            )
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(
                f"Error retrieving page content for page ID {title}: {str(e)}"
            )
            raise Exception(f"Error retrieving page content: {str(e)}") from e

    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
        content_representation: str | None = None,
    ) -> dict:
        """
        Create a new page in the specified space.

        Args:
            space_key: The key of the space to create the page in
            title: The title of the new page
            body: The content of the new page
            parent_id: Optional parent page ID to create under
            content_representation: Content representation format (storage, wiki, etc.)

        Returns:
            Dict containing the created page information

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error creating the page
        """
        try:
            # Determine representation
            if content_representation == "markdown":
                # For markdown, convert to storage format first
                final_body = self.preprocessor.convert_to_storage_format(body)
                representation = "storage"
            elif content_representation == "wiki":
                final_body = body
                representation = "wiki"
            else:
                # Use body as-is with specified representation
                final_body = body
                representation = content_representation or "storage"
            
            logger.debug(
                f"Using v1 API for token/basic authentication to create page '{title}'"
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
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"Error creating page '{title}': {str(e)}")
            raise Exception(f"Error creating page: {str(e)}") from e

    def update_page(
        self,
        page_id: str,
        title: str | None = None,
        body: str | None = None,
        content_representation: str | None = None,
        version_comment: str | None = None,
    ) -> dict:
        """
        Update an existing page.

        Args:
            page_id: The ID of the page to update
            title: New title for the page (optional)
            body: New content for the page (optional)
            content_representation: Content representation format (storage, wiki, etc.)
            version_comment: Comment for this version update

        Returns:
            Dict containing the updated page information

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error updating the page
        """
        try:
            # Determine representation
            if content_representation == "markdown":
                # For markdown, convert to storage format first
                final_body = self.preprocessor.convert_to_storage_format(body or "")
                representation = "storage"
            elif content_representation == "wiki":
                final_body = body or ""
                representation = "wiki"
            else:
                # Use body as-is with specified representation
                final_body = body or ""
                representation = content_representation or "storage"
            
            logger.debug(f"Updating page {page_id} with title '{title}'")
            logger.debug(
                f"Using v1 API for token/basic authentication to update page '{page_id}'"
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
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"Error updating page '{page_id}': {str(e)}")
            raise Exception(f"Error updating page: {str(e)}") from e

    def delete_page(self, page_id: str) -> bool:
        """
        Delete a page by its ID.

        Args:
            page_id: The ID of the page to delete

        Returns:
            True if the page was deleted successfully, False otherwise

        Raises:
            MCPAtlassianAuthenticationError: If authentication fails with the Confluence API (401/403)
            Exception: If there is an error deleting the page
        """
        try:
            logger.debug(f"Deleting page {page_id}")
            logger.debug(
                f"Using v1 API for token/basic authentication to delete page '{page_id}'"
            )
            response = self.confluence.remove_page(page_id=page_id)
            # The Atlassian library's remove_page returns the raw response from
            # the REST API call. For a successful deletion, we should get a
            # response object, but it might be empty (HTTP 204 No Content).
            return response is not None
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence API ({http_err.response.status_code}). "
                    "Token may be expired or invalid. Please verify credentials."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            else:
                logger.error(f"HTTP error during API call: {http_err}", exc_info=False)
                raise http_err
        except Exception as e:
            logger.error(f"Error deleting page '{page_id}': {str(e)}")
            raise Exception(f"Error deleting page: {str(e)}") from e