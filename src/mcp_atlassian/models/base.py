"""
MCP Atlassian API模型的基础模型和实用类。

此模块提供了由Jira和Confluence模型使用的基础类和混入类，
以确保一致的行为并减少代码重复。
"""

from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel

from .constants import EMPTY_STRING

# Type variable for the return type of from_api_response
T = TypeVar("T", bound="ApiModel")


class ApiModel(BaseModel):
    """
    所有API模型的基础模型，具有通用转换方法。

    这提供了将API响应转换为模型以及将模型转换为简化
    字典用于API响应的标准接口。
    """

    @classmethod
    def from_api_response(cls: type[T], data: dict[str, Any], **kwargs: Any) -> T:
        """
        将API响应转换为模型实例。

        参数:
            data: API响应数据
            **kwargs: 附加上下文参数

        返回:
            模型实例

        引发:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("Subclasses must implement from_api_response")

    def to_simplified_dict(self) -> dict[str, Any]:
        """
        将模型转换为用于API响应的简化字典。

        返回:
            仅包含API响应必需字段的字典
        """
        return self.model_dump(exclude_none=True)


class TimestampMixin:
    """
    用于处理Atlassian API时间戳格式的混入类。
    """

    @staticmethod
    def format_timestamp(timestamp: str | None) -> str:
        """
        将Atlassian时间戳格式化为人类可读格式。

        参数:
            timestamp: ISO 8601时间戳字符串

        返回:
            格式化的日期字符串，如果输入无效则返回空字符串
        """
        if not timestamp:
            return EMPTY_STRING

        try:
            # 解析ISO 8601格式，如"2024-01-01T10:00:00.000+0000"
            # 将Z格式转换为+00:00以与fromisoformat兼容
            ts = timestamp.replace("Z", "+00:00")

            # 处理不带冒号的时区格式（+0000 -> +00:00）
            if "+" in ts and ":" not in ts[-5:]:
                tz_pos = ts.rfind("+")
                if tz_pos != -1 and len(ts) >= tz_pos + 5:
                    ts = ts[: tz_pos + 3] + ":" + ts[tz_pos + 3 :]
            elif "-" in ts and ":" not in ts[-5:]:
                tz_pos = ts.rfind("-")
                if tz_pos != -1 and len(ts) >= tz_pos + 5:
                    ts = ts[: tz_pos + 3] + ":" + ts[tz_pos + 3 :]

            dt = datetime.fromisoformat(ts)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return timestamp or EMPTY_STRING

    @staticmethod
    def is_valid_timestamp(timestamp: str | None) -> bool:
        """
        检查字符串是否为有效的ISO 8601时间戳。

        参数:
            timestamp: 要检查的字符串

        返回:
            如果字符串是有效时间戳则返回True，否则返回False
        """
        if not timestamp:
            return False

        try:
            # 将Z格式转换为+00:00以与fromisoformat兼容
            ts = timestamp.replace("Z", "+00:00")

            # 处理不带冒号的时区格式（+0000 -> +00:00）
            if "+" in ts and ":" not in ts[-5:]:
                tz_pos = ts.rfind("+")
                if tz_pos != -1 and len(ts) >= tz_pos + 5:
                    ts = ts[: tz_pos + 3] + ":" + ts[tz_pos + 3 :]
            elif "-" in ts and ":" not in ts[-5:]:
                tz_pos = ts.rfind("-")
                if tz_pos != -1 and len(ts) >= tz_pos + 5:
                    ts = ts[: tz_pos + 3] + ":" + ts[tz_pos + 3 :]

            datetime.fromisoformat(ts)
            return True
        except (ValueError, TypeError):
            return False
