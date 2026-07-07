#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
油价抓取模块
从公开数据源获取全国各省油价
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


class OilPriceFetcher:
    """油价数据抓取器"""
    
    # 全国省份列表
    PROVINCES = [
        "北京", "上海", "天津", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
        "广东", "广西", "海南", "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
        "青海", "宁夏", "新疆", "内蒙古"
    ]
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def fetch_all(self):
        """
        获取全国所有省份的最新油价
        返回: {省份名: {gas92, gas95, gas98, diesel0, fetched_at}}
        """
        # 优先尝试46.la数据源
        result = self._fetch_from_46la()
        if result:
            return result
        
        # 如果失败，尝试其他数据源
        result = self._fetch_from_tuanyou()
        if result:
            return result
        
        logger.error("所有数据源均获取失败")
        return {}
    
    def _fetch_from_46la(self):
        """从46.la抓取油价数据"""
        try:
            url = "https://www.46.la/tool/today-fuel-price"
            logger.info(f"正在从 {url} 获取油价数据...")
            
            resp = requests.get(url, timeout=20, headers=self.headers)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            result = {}
            fetched_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            for line in lines:
                for prov in self.PROVINCES:
                    if prov in line:
                        prices = re.findall(r'(\d+\.\d{2})', line)
                        if len(prices) >= 4:
                            result[prov] = {
                                'gas92': prices[0],
                                'gas95': prices[1],
                                'gas98': prices[2],
                                'diesel0': prices[3],
                                'fetched_at': fetched_at
                            }
                        break
            
            if len(result) >= 20:  # 至少获取20个省份才算成功
                logger.info(f"从46.la成功获取 {len(result)} 个省份数据")
                return result
            else:
                logger.warning(f"46.la数据不完整，仅获取 {len(result)} 个省份")
                return {}
                
        except Exception as e:
            logger.warning(f"从46.la获取数据失败: {e}")
            return {}
    
    def _fetch_from_tuanyou(self):
        """从团友网抓取油价数据（备用数据源）"""
        try:
            url = "https://www.tuanyou.net/youjia/92hao/"
            logger.info(f"正在从 {url} 获取油价数据...")
            
            resp = requests.get(url, timeout=20, headers=self.headers)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            result = {}
            fetched_at = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            for line in lines:
                for prov in self.PROVINCES:
                    if prov in line:
                        prices = re.findall(r'(\d+\.\d{2})', line)
                        if len(prices) >= 4:
                            result[prov] = {
                                'gas92': prices[0],
                                'gas95': prices[1],
                                'gas98': prices[2],
                                'diesel0': prices[3],
                                'fetched_at': fetched_at
                            }
                        break
            
            if len(result) >= 20:
                logger.info(f"从团友网成功获取 {len(result)} 个省份数据")
                return result
            else:
                logger.warning(f"团友网数据不完整，仅获取 {len(result)} 个省份")
                return {}
                
        except Exception as e:
            logger.warning(f"从团友网获取数据失败: {e}")
            return {}
