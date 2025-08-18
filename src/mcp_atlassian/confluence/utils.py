"""Confluence操作特定的实用工具函数。"""

import logging

from .constants import RESERVED_CQL_WORDS

logger = logging.getLogger(__name__)


def quote_cql_identifier_if_needed(identifier: str) -> str:
    """
    如果需要，为Confluence标识符添加引号以便在CQL字面量中安全使用。

    处理：
    - 以'~'开头的个人空间键。
    - 匹配保留CQL字的标识符（不区分大小写）。
    - 以数字开头的标识符。
    - 在标识符内转义内部引号（'"'）和反斜杠（'\\'）
      *在* 引用之前。

    Args:
        identifier: 标识符字符串（例如，空间键）。

    Returns:
        如果需要，正确引用和转义的标识符，
        否则返回原始标识符。
    """
    needs_quoting = False
    identifier_lower = identifier.lower()

    # 规则1：以~开头（个人空间键）
    if identifier.startswith("~"):
        needs_quoting = True
        logger.debug(f"标识符'{identifier}'需要引用（以~开头）。")

    # 规则2：是保留字（不区分大小写检查）
    elif identifier_lower in RESERVED_CQL_WORDS:
        needs_quoting = True
        logger.debug(f"标识符'{identifier}'需要引用（保留字）。")

    # 规则3：以数字开头
    elif identifier and identifier[0].isdigit():
        needs_quoting = True
        logger.debug(f"标识符'{identifier}'需要引用（以数字开头）。")

    # 规则4：包含内部引号或反斜杠（总是需要引用+转义）
    elif '"' in identifier or "\\" in identifier:
        needs_quoting = True
        logger.debug(
            f"标识符'{identifier}'需要引用（包含引号/反斜杠）。"
        )

    # 如果其他字符被证明有问题，请在此处添加更多规则（例如，空格、连字符）
    # elif ' ' in identifier or '-' in identifier:
    #    needs_quoting = True

    if needs_quoting:
        # 首先转义内部反斜杠，然后转义双引号
        escaped_identifier = identifier.replace("\\", "\\\\").replace('"', '\\"')
        quoted_escaped = f'"{escaped_identifier}"'
        logger.debug(f"引用和转义的标识符: {quoted_escaped}")
        return quoted_escaped
    else:
        # 如果不需要引用，则返回原始标识符
        logger.debug(f"标识符'{identifier}'不需要引用。")
        return identifier
