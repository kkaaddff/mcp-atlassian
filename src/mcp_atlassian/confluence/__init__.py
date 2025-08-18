"""Confluence API集成模块。

此模块通过模型上下文协议提供对Confluence内容的访问。
"""

from .client import ConfluenceClient
from .comments import CommentsMixin
from .config import ConfluenceConfig
from .labels import LabelsMixin
from .pages import PagesMixin
from .search import SearchMixin
from .spaces import SpacesMixin
from .users import UsersMixin


class ConfluenceFetcher(
    SearchMixin, SpacesMixin, PagesMixin, CommentsMixin, LabelsMixin, UsersMixin
):
    """Confluence操作的主入口点，提供向后兼容性。

    此类组合了来自各种混入类的功能，以保持与原始ConfluenceFetcher类相同的API。
    """

    pass


__all__ = ["ConfluenceFetcher", "ConfluenceConfig", "ConfluenceClient"]
