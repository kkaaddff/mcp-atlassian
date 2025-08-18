"""Confluence FastMCP服务器实例和工具定义。"""

import json
import logging
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import BeforeValidator, Field

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError
from mcp_atlassian.servers.dependencies import get_confluence_fetcher
from mcp_atlassian.utils.decorators import (
    check_write_access,
)

logger = logging.getLogger(__name__)

confluence_mcp = FastMCP(
    name="Confluence MCP Service",
    description="提供与Atlassian Confluence交互的工具。",
)


@confluence_mcp.tool(tags={"confluence", "read"})
async def search(
    ctx: Context,
    query: Annotated[
        str,
        Field(
            description=(
                "Search query - can be either a simple text (e.g. 'project documentation') or a CQL query string. "
                "Simple queries use 'siteSearch' by default, to mimic the WebUI search, with an automatic fallback "
                "to 'text' search if not supported. Examples of CQL:\n"
                "- Basic search: 'type=page AND space=DEV'\n"
                "- Personal space search: 'space=\"~username\"' (note: personal space keys starting with ~ must be quoted)\n"
                "- Search by title: 'title~\"Meeting Notes\"'\n"
                "- Use siteSearch: 'siteSearch ~ \"important concept\"'\n"
                "- Use text search: 'text ~ \"important concept\"'\n"
                "- Recent content: 'created >= \"2023-01-01\"'\n"
                "- Content with specific label: 'label=documentation'\n"
                "- Recently modified content: 'lastModified > startOfMonth(\"-1M\")'\n"
                "- Content modified this year: 'creator = currentUser() AND lastModified > startOfYear()'\n"
                "- Content you contributed to recently: 'contributor = currentUser() AND lastModified > startOfWeek()'\n"
                "- Content watched by user: 'watcher = \"user@domain.com\" AND type = page'\n"
                '- Exact phrase in content: \'text ~ "\\"Urgent Review Required\\"" AND label = "pending-approval"\'\n'
                '- Title wildcards: \'title ~ "Minutes*" AND (space = "HR" OR space = "Marketing")\'\n'
                'Note: Special identifiers need proper quoting in CQL: personal space keys (e.g., "~username"), '
                "reserved words, numeric IDs, and identifiers with special characters."
            )
        ),
    ],
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results (1-50)",
            default=10,
            ge=1,
            le=50,
        ),
    ] = 10,
    spaces_filter: Annotated[
        str | None,
        Field(
            description=(
                "(Optional) Comma-separated list of space keys to filter results by. "
                "Overrides the environment variable CONFLUENCE_SPACES_FILTER if provided. "
                "Use empty string to disable filtering."
            ),
            default=None,
        ),
    ] = None,
) -> str:
    """Search Confluence content using simple terms or CQL.

    Args:
        ctx: FastMCP上下文。
        query: 搜索查询 - 可以是简单文本或CQL查询字符串。
        limit: 最大结果数（1-50）。
        spaces_filter: 用于过滤的逗号分隔的空间键列表。

    Returns:
        表示简化的Confluence页面对象列表的JSON字符串。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    # 检查查询是简单搜索词还是已经是CQL查询
    if query and not any(
        x in query for x in ["=", "~", ">", "<", " AND ", " OR ", "currentUser()"]
    ):
        original_query = query
        try:
            query = f'siteSearch ~ "{original_query}"'
            logger.info(
                f"将简单搜索词转换为使用siteSearch的CQL: {query}"
            )
            pages = confluence_fetcher.search(
                query, limit=limit, spaces_filter=spaces_filter
            )
        except Exception as e:
            logger.warning(f"siteSearch失败（'{e}'），回退到文本搜索。")
            query = f'text ~ "{original_query}"'
            logger.info(f"回退到使用CQL的文本搜索: {query}")
            pages = confluence_fetcher.search(
                query, limit=limit, spaces_filter=spaces_filter
            )
    else:
        pages = confluence_fetcher.search(
            query, limit=limit, spaces_filter=spaces_filter
        )
    search_results = [page.to_simplified_dict() for page in pages]
    return json.dumps(search_results, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "read"})
async def get_page(
    ctx: Context,
    page_id: Annotated[
        str | None,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be found in the page URL). "
                "For example, in the URL 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title', "
                "the page ID is '123456789'. "
                "Provide this OR both 'title' and 'space_key'. If page_id is provided, title and space_key will be ignored."
            ),
            default=None,
        ),
    ] = None,
    title: Annotated[
        str | None,
        Field(
            description=(
                "The exact title of the Confluence page. Use this with 'space_key' if 'page_id' is not known."
            ),
            default=None,
        ),
    ] = None,
    space_key: Annotated[
        str | None,
        Field(
            description=(
                "The key of the Confluence space where the page resides (e.g., 'DEV', 'TEAM'). Required if using 'title'."
            ),
            default=None,
        ),
    ] = None,
    include_metadata: Annotated[
        bool,
        Field(
            description="Whether to include page metadata such as creation date, last update, version, and labels.",
            default=True,
        ),
    ] = True,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description=(
                "Whether to convert page to markdown (true) or keep it in raw HTML format (false). "
                "Raw HTML can reveal macros (like dates) not visible in markdown, but CAUTION: "
                "using HTML significantly increases token usage in AI responses."
            ),
            default=True,
        ),
    ] = True,
) -> str:
    """Get content of a specific Confluence page by its ID, or by its title and space key.

    Args:
        ctx: FastMCP上下文。
        page_id: Confluence页面ID。如果提供，将忽略'title'和'space_key'。
        title: 页面的确切标题。必须与'space_key'一起使用。
        space_key: 空间的键。必须与'title'一起使用。
        include_metadata: 是否包含页面元数据。
        convert_to_markdown: 将内容转换为markdown（true）或保持原始HTML格式（false）。

    Returns:
        表示页面内容和/或元数据的JSON字符串，如果未找到或参数无效则返回错误。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    page_object = None

    if page_id:
        if title or space_key:
            logger.warning(
                "提供了page_id；title和space_key参数将被忽略。"
            )
        try:
            page_object = confluence_fetcher.get_page_content(
                page_id, convert_to_markdown=convert_to_markdown
            )
        except Exception as e:
            logger.error(f"通过ID'{page_id}'获取页面时出错: {e}")
            return json.dumps(
                {"error": f"通过ID'{page_id}'检索页面失败: {e}"},
                indent=2,
                ensure_ascii=False,
            )
    elif title and space_key:
        page_object = confluence_fetcher.get_page_by_title(
            space_key, title, convert_to_markdown=convert_to_markdown
        )
        if not page_object:
            return json.dumps(
                {
                    "error": f"在空间'{space_key}'中未找到标题为'{title}'的页面。"
                },
                indent=2,
                ensure_ascii=False,
            )
    else:
        raise ValueError(
            "必须提供'page_id'或同时提供'title'和'space_key'。"
        )

    if not page_object:
        return json.dumps(
            {"error": "使用提供的标识符未找到页面。"},
            indent=2,
            ensure_ascii=False,
        )

    if include_metadata:
        result = {"metadata": page_object.to_simplified_dict()}
    else:
        result = {"content": {"value": page_object.content}}

    return json.dumps(result, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "read"})
async def get_page_children(
    ctx: Context,
    parent_id: Annotated[
        str,
        Field(
            description="The ID of the parent page whose children you want to retrieve"
        ),
    ],
    expand: Annotated[
        str,
        Field(
            description="Fields to expand in the response (e.g., 'version', 'body.storage')",
            default="version",
        ),
    ] = "version",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of child pages to return (1-50)",
            default=25,
            ge=1,
            le=50,
        ),
    ] = 25,
    include_content: Annotated[
        bool,
        Field(
            description="Whether to include the page content in the response",
            default=False,
        ),
    ] = False,
    convert_to_markdown: Annotated[
        bool,
        Field(
            description="Whether to convert page content to markdown (true) or keep it in raw HTML format (false). Only relevant if include_content is true.",
            default=True,
        ),
    ] = True,
    start: Annotated[
        int,
        Field(description="Starting index for pagination (0-based)", default=0, ge=0),
    ] = 0,
) -> str:
    """Get child pages of a specific Confluence page.

    Args:
        ctx: FastMCP上下文。
        parent_id: 父页面的ID。
        expand: 要展开的字段。
        limit: 子页面的最大数量。
        include_content: 是否包含页面内容。
        convert_to_markdown: 如果include_content为true，将内容转换为markdown。
        start: 分页的起始索引。

    Returns:
        表示子页面对象列表的JSON字符串。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    if include_content and "body" not in expand:
        expand = f"{expand},body.storage" if expand else "body.storage"

    try:
        pages = confluence_fetcher.get_page_children(
            page_id=parent_id,
            start=start,
            limit=limit,
            expand=expand,
            convert_to_markdown=convert_to_markdown,
        )
        child_pages = [page.to_simplified_dict() for page in pages]
        result = {
            "parent_id": parent_id,
            "count": len(child_pages),
            "limit_requested": limit,
            "start_requested": start,
            "results": child_pages,
        }
    except Exception as e:
        logger.error(
            f"获取/处理页面ID {parent_id}的子页面时出错: {e}",
            exc_info=True,
        )
        result = {"error": f"获取子页面失败: {e}"}

    return json.dumps(result, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "read"})
async def get_comments(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be parsed from URL, "
                "e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' "
                "-> '123456789')"
            )
        ),
    ],
) -> str:
    """Get comments for a specific Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: Confluence页面ID。

    Returns:
        表示评论对象列表的JSON字符串。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    comments = confluence_fetcher.get_page_comments(page_id)
    formatted_comments = [comment.to_simplified_dict() for comment in comments]
    return json.dumps(formatted_comments, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "read"})
async def get_labels(
    ctx: Context,
    page_id: Annotated[
        str,
        Field(
            description=(
                "Confluence page ID (numeric ID, can be parsed from URL, "
                "e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' "
                "-> '123456789')"
            )
        ),
    ],
) -> str:
    """Get labels for a specific Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: Confluence页面ID。

    Returns:
        表示标签对象列表的JSON字符串。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.get_page_labels(page_id)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def add_label(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    name: Annotated[str, Field(description="The name of the label")],
) -> str:
    """Add label to an existing Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: 要更新的页面ID。
        name: 标签的名称。

    Returns:
        表示页面更新后的标签对象列表的JSON字符串。

    Raises:
        ValueError: 如果处于只读模式或Confluence客户端不可用。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    labels = confluence_fetcher.add_page_label(page_id, name)
    formatted_labels = [label.to_simplified_dict() for label in labels]
    return json.dumps(formatted_labels, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def create_page(
    ctx: Context,
    space_key: Annotated[
        str,
        Field(
            description="The key of the space to create the page in (usually a short uppercase code like 'DEV', 'TEAM', or 'DOC')"
        ),
    ],
    title: Annotated[str, Field(description="The title of the page")],
    content: Annotated[
        str,
        Field(
            description="The content of the page. Format depends on content_format parameter. Can be Markdown (default), wiki markup, or storage format"
        ),
    ],
    parent_id: Annotated[
        str | None,
        Field(
            description="(Optional) parent page ID. If provided, this page will be created as a child of the specified page",
            default=None,
        ),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description="(Optional) The format of the content parameter. Options: 'markdown' (default), 'wiki', or 'storage'. Wiki format uses Confluence wiki markup syntax",
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
) -> str:
    """Create a new Confluence page.

    Args:
        ctx: FastMCP上下文。
        space_key: 空间的键。
        title: 页面的标题。
        content: 页面的内容（格式取决于content_format）。
        parent_id: 可选的父页面ID。
        content_format: 内容的格式（'markdown'、'wiki'或'storage'）。
        enable_heading_anchors: 是否启用标题锚点（仅限markdown）。

    Returns:
        表示创建的页面对象的JSON字符串。

    Raises:
        ValueError: 如果处于只读模式、Confluence客户端不可用或content_format无效。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # 验证content_format
    if content_format not in ["markdown", "wiki", "storage"]:
        raise ValueError(
            f"无效的content_format: {content_format}。必须是'markdown'、'wiki'或'storage'"
        )

    # 根据内容格式确定参数
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # 将转换为存储格式
    else:
        is_markdown = False
        content_representation = content_format  # 直接传递'wiki'或'storage'

    page = confluence_fetcher.create_page(
        space_key=space_key,
        title=title,
        body=content,
        parent_id=parent_id,
        is_markdown=is_markdown,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
    )
    result = page.to_simplified_dict()
    return json.dumps(
        {"message": "Page created successfully", "page": result},
        indent=2,
        ensure_ascii=False,
    )


@confluence_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def update_page(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to update")],
    title: Annotated[str, Field(description="The new title of the page")],
    content: Annotated[
        str,
        Field(
            description="The new content of the page. Format depends on content_format parameter"
        ),
    ],
    is_minor_edit: Annotated[
        bool, Field(description="Whether this is a minor edit", default=False)
    ] = False,
    version_comment: Annotated[
        str | None, Field(description="Optional comment for this version", default=None)
    ] = None,
    parent_id: Annotated[
        str | None,
        Field(description="Optional the new parent page ID", default=None),
        BeforeValidator(lambda x: str(x) if x is not None else None),
    ] = None,
    content_format: Annotated[
        str,
        Field(
            description="(Optional) The format of the content parameter. Options: 'markdown' (default), 'wiki', or 'storage'. Wiki format uses Confluence wiki markup syntax",
            default="markdown",
        ),
    ] = "markdown",
    enable_heading_anchors: Annotated[
        bool,
        Field(
            description="(Optional) Whether to enable automatic heading anchor generation. Only applies when content_format is 'markdown'",
            default=False,
        ),
    ] = False,
) -> str:
    """Update an existing Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: 要更新的页面ID。
        title: 页面的新标题。
        content: 页面的新内容（格式取决于content_format）。
        is_minor_edit: 是否为小编辑。
        version_comment: 此版本的可选注释。
        parent_id: 可选的新父页面ID。
        content_format: 内容的格式（'markdown'、'wiki'或'storage'）。
        enable_heading_anchors: 是否启用标题锚点（仅限markdown）。

    Returns:
        表示更新的页面对象的JSON字符串。

    Raises:
        ValueError: 如果Confluence客户端未配置、不可用或content_format无效。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # 验证content_format
    if content_format not in ["markdown", "wiki", "storage"]:
        raise ValueError(
            f"无效的content_format: {content_format}。必须是'markdown'、'wiki'或'storage'"
        )

    # 根据内容格式确定参数
    if content_format == "markdown":
        is_markdown = True
        content_representation = None  # 将转换为存储格式
    else:
        is_markdown = False
        content_representation = content_format  # 直接传递'wiki'或'storage'

    updated_page = confluence_fetcher.update_page(
        page_id=page_id,
        title=title,
        body=content,
        is_minor_edit=is_minor_edit,
        version_comment=version_comment,
        is_markdown=is_markdown,
        parent_id=parent_id,
        enable_heading_anchors=enable_heading_anchors
        if content_format == "markdown"
        else False,
        content_representation=content_representation,
    )
    page_data = updated_page.to_simplified_dict()
    return json.dumps(
        {"message": "Page updated successfully", "page": page_data},
        indent=2,
        ensure_ascii=False,
    )


@confluence_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def delete_page(
    ctx: Context,
    page_id: Annotated[str, Field(description="The ID of the page to delete")],
) -> str:
    """Delete an existing Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: 要删除的页面ID。

    Returns:
        表示成功或失败的JSON字符串。

    Raises:
        ValueError: 如果Confluence客户端未配置或不可用。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    try:
        result = confluence_fetcher.delete_page(page_id=page_id)
        if result:
            response = {
                "success": True,
                "message": f"Page {page_id} deleted successfully",
            }
        else:
            response = {
                "success": False,
                "message": f"Unable to delete page {page_id}. API request completed but deletion unsuccessful.",
            }
    except Exception as e:
        logger.error(f"删除Confluence页面{page_id}时出错: {str(e)}")
        response = {
            "success": False,
            "message": f"删除页面{page_id}时出错",
            "error": str(e),
        }

    return json.dumps(response, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "write"})
@check_write_access
async def add_comment(
    ctx: Context,
    page_id: Annotated[
        str, Field(description="The ID of the page to add a comment to")
    ],
    content: Annotated[
        str, Field(description="The comment content in Markdown format")
    ],
) -> str:
    """Add a comment to a Confluence page.

    Args:
        ctx: FastMCP上下文。
        page_id: 要添加评论的页面ID。
        content: Markdown格式的评论内容。

    Returns:
        表示创建的评论的JSON字符串。

    Raises:
        ValueError: 如果处于只读模式或Confluence客户端不可用。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)
    try:
        comment = confluence_fetcher.add_comment(page_id=page_id, content=content)
        if comment:
            comment_data = comment.to_simplified_dict()
            response = {
                "success": True,
                "message": "Comment added successfully",
                "comment": comment_data,
            }
        else:
            response = {
                "success": False,
                "message": f"Unable to add comment to page {page_id}. API request completed but comment creation unsuccessful.",
            }
    except Exception as e:
        logger.error(f"向Confluence页面{page_id}添加评论时出错: {str(e)}")
        response = {
            "success": False,
            "message": f"向页面{page_id}添加评论时出错",
            "error": str(e),
        }

    return json.dumps(response, indent=2, ensure_ascii=False)


@confluence_mcp.tool(tags={"confluence", "read"})
async def search_user(
    ctx: Context,
    query: Annotated[
        str,
        Field(
            description=(
                "Search query - a CQL query string for user search. "
                "Examples of CQL:\n"
                "- Basic user lookup by full name: 'user.fullname ~ \"First Last\"'\n"
                'Note: Special identifiers need proper quoting in CQL: personal space keys (e.g., "~username"), '
                "reserved words, numeric IDs, and identifiers with special characters."
            )
        ),
    ],
    limit: Annotated[
        int,
        Field(
            description="Maximum number of results (1-50)",
            default=10,
            ge=1,
            le=50,
        ),
    ] = 10,
) -> str:
    """Search Confluence users using CQL.

    Args:
        ctx: FastMCP上下文。
        query: 搜索查询 - 用于用户搜索的CQL查询字符串。
        limit: 最大结果数（1-50）。

    Returns:
        表示简化的Confluence用户搜索结果对象列表的JSON字符串。
    """
    confluence_fetcher = await get_confluence_fetcher(ctx)

    # 如果查询看起来不像CQL，将其包装为用户全名搜索
    if query and not any(
        x in query for x in ["=", "~", ">", "<", " AND ", " OR ", "user."]
    ):
        # 简单搜索词 - 按全名搜索
        query = f'user.fullname ~ "{query}"'
        logger.info(f"将简单搜索词转换为用户CQL: {query}")

    try:
        user_results = confluence_fetcher.search_user(query, limit=limit)
        search_results = [user.to_simplified_dict() for user in user_results]
        return json.dumps(search_results, indent=2, ensure_ascii=False)
    except MCPAtlassianAuthenticationError as e:
        logger.error(f"用户搜索期间身份验证错误: {e}", exc_info=False)
        return json.dumps(
            {
                "error": "身份验证失败。请检查您的凭据。",
                "details": str(e),
            },
            indent=2,
            ensure_ascii=False,
        )
    except Exception as e:
        logger.error(f"搜索用户时出错: {str(e)}")
        return json.dumps(
            {
                "error": f"搜索用户时发生意外错误: {str(e)}"
            },
            indent=2,
            ensure_ascii=False,
        )
