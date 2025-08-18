"""日期操作的实用函数。"""

import logging
from datetime import datetime, timezone

import dateutil.parser

logger = logging.getLogger("mcp-atlassian")


def parse_date(date_str: str | int | None) -> datetime | None:
    """
    将日期字符串从任何格式解析为datetime对象以实现类型一致性。

    输入字符串`date_str`接受：
    - None
    - 纪元时间戳（仅包含数字且为毫秒）
    - `dateutil.parser`支持的其他格式（ISO 8601、RFC 3339等）

    参数:
        date_str: 日期字符串

    返回:
        解析后的日期字符串，如果date_str为None/空字符串则返回None
    """

    if not date_str:
        return None
    if isinstance(date_str, int) or date_str.isdigit():
        return datetime.fromtimestamp(int(date_str) / 1000, tz=timezone.utc)
    return dateutil.parser.parse(date_str)
