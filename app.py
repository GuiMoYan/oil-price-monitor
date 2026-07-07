#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国内油价监控推送工具 - 主入口（多用户版）
同时启动 Web 配置面板 + 后台定时调度器
"""

import sys
import logging

from web_server import run_web_server
from scheduler_service import start_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """同时启动 Web 服务 和 后台调度器"""
    logger.info("=" * 60)
    logger.info("国内油价监控推送工具（多用户版）启动")
    logger.info("=" * 60)
    
    # 启动后台调度器（默认自动启动）
    try:
        start_scheduler()
        logger.info("后台调度器已启动")
    except Exception as e:
        logger.error(f"后台调度器启动失败: {e}")
    
    # 启动 Web 配置面板（阻塞主线程）
    web_host = '0.0.0.0'
    web_port = 8080
    logger.info(f"Web 配置面板地址: http://{web_host}:{web_port}")
    logger.info("在浏览器打开地址即可注册和登录")
    logger.info("=" * 60)
    
    run_web_server(host=web_host, port=web_port)


if __name__ == '__main__':
    main()
