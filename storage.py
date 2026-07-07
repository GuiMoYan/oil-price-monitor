#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地数据存储模块
使用JSON文件存储各省份上次查询的油价
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'oil_prices.json')


class Storage:
    """本地油价数据存储"""
    
    def __init__(self):
        self._ensure_dir()
    
    def _ensure_dir(self):
        """确保数据目录存在"""
        dir_path = os.path.dirname(DATA_FILE)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    def _load(self):
        """加载所有存储的数据"""
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"读取数据文件失败: {e}")
            return {}
    
    def _save_all(self, data):
        """保存所有数据"""
        self._ensure_dir()
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据文件失败: {e}")
    
    def get(self, province):
        """获取指定省份的上次油价"""
        data = self._load()
        return data.get(province)
    
    def save(self, province, prices):
        """保存指定省份的油价"""
        data = self._load()
        data[province] = prices
        self._save_all(data)
        logger.info(f"已保存 [{province}] 的油价数据")
    
    def get_all(self):
        """获取所有存储的油价数据"""
        return self._load()
    
    def clear(self):
        """清空所有数据"""
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
            logger.info("已清空所有存储的油价数据")
