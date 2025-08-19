"""日志配置工具"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    stream: Optional[object] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """设置日志配置
    
    Args:
        level: 日志级别
        stream: 输出流，默认为stderr
        format_string: 日志格式字符串
        
    Returns:
        配置好的logger实例
    """
    if stream is None:
        stream = sys.stderr
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # 创建根logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 清除现有的handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建新的handler
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    
    # 设置格式
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # 添加handler到logger
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger
    
    Args:
        name: logger名称
        
    Returns:
        logger实例
    """
    return logging.getLogger(name)
