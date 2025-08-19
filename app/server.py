#!/usr/bin/env python3
"""TFA算法服务器主入口点"""

import argparse
import logging
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.application import create_app
from app.core.config import Settings
from app.utils.logging import setup_logging


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Confluence MCP服务器')
    parser.add_argument(
        '-name', 
        '--name',
        default='confluence-mcp',
        help='服务器名称 (默认: confluence-mcp)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='服务器主机地址 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='服务器端口 (默认: 8000)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='启用自动重载 (开发模式)'
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level)
    
    # 创建配置
    settings = Settings(
        app_name=args.name,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower(),
        reload=args.reload
    )
    
    # 创建应用
    app = create_app(settings)
    
    logger.info(f"启动 {args.name} 服务器")
    logger.info(f"服务器地址: http://{args.host}:{args.port}")
    logger.info(f"日志级别: {args.log_level}")
    
    # 启动服务器
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
            reload=args.reload
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
