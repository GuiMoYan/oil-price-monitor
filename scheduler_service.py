#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台定时任务调度器（多用户版）
遍历所有用户，为每个用户独立检查油价并推送
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from models import User, db
from oil_fetcher import OilPriceFetcher
from notifier import Notifier
from config import UserConfig

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_job_id = 'oil_check'


def _check_user(user, current_prices):
    """为单个用户检查油价并推送"""
    config = UserConfig(user)
    
    target_provinces = config.target_provinces
    if not target_provinces:
        logger.info(f"[用户:{user.username}] 未配置关注省份，跳过")
        return
    
    logger.info(f"[用户:{user.username}] 关注省份: {', '.join(target_provinces)}")
    
    has_changes = False
    change_messages = []
    
    for province in target_provinces:
        if province not in current_prices:
            logger.warning(f"[用户:{user.username}] 未找到省份 [{province}] 的油价数据")
            continue
        
        current = current_prices[province]
        previous = user.get_oil_price(province)
        
        if previous is None:
            logger.info(f"[用户:{user.username}][{province}] 首次记录油价: 92#{current['gas92']} 95#{current['gas95']} 98#{current['gas98']} 0#柴油{current['diesel0']}")
            user.save_oil_price(province, current)
            continue
        
        changed_oils = []
        for oil_type in ['gas92', 'gas95', 'gas98', 'diesel0']:
            current_price = current.get(oil_type, '0.00')
            previous_price = getattr(previous, oil_type, '0.00')
            if current_price != previous_price:
                changed_oils.append({
                    'type': oil_type,
                    'previous': previous_price,
                    'current': current_price
                })
        
        if changed_oils:
            has_changes = True
            msg = f"【{province}】油价变动：\n"
            for change in changed_oils:
                type_name = {
                    'gas92': '92号汽油',
                    'gas95': '95号汽油',
                    'gas98': '98号汽油',
                    'diesel0': '0号柴油'
                }.get(change['type'], change['type'])
                
                prev = float(change['previous'])
                curr = float(change['current'])
                diff = curr - prev
                diff_str = f"{'↑' if diff > 0 else '↓'} {abs(diff):.2f}元"
                
                msg += f"  {type_name}: {change['previous']} → {change['current']} ({diff_str})\n"
            
            msg += f"\n  当前价格:\n"
            msg += f"    92号汽油: {current['gas92']} 元/升\n"
            msg += f"    95号汽油: {current['gas95']} 元/升\n"
            msg += f"    98号汽油: {current['gas98']} 元/升\n"
            msg += f"    0号柴油: {current['diesel0']} 元/升\n"
            msg += f"  数据更新时间: {current.get('fetched_at', '未知')}"
            
            change_messages.append(msg)
            user.save_oil_price(province, current)
            logger.info(f"[用户:{user.username}][{province}] 油价发生变动！")
        else:
            logger.info(f"[用户:{user.username}][{province}] 油价无变化")
    
    if has_changes and change_messages:
        full_message = f"【用户:{user.username}】\n" + "\n".join(change_messages)
        logger.info(f"[用户:{user.username}] 检测到油价变动，准备发送推送...")
        notifier = Notifier(config)
        try:
            notifier.send(full_message)
        except Exception as e:
            logger.error(f"[用户:{user.username}] 推送失败: {e}")
    else:
        logger.info(f"[用户:{user.username}] 本次检查未发现油价变动")


def _check_all_users():
    """定时执行的核心检查任务：遍历所有用户"""
    logger.info("=" * 50)
    logger.info("开始检查油价...")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取所有用户
    users = User.query.all()
    if not users:
        logger.info("系统中没有用户，跳过本次检查")
        return
    
    logger.info(f"共 {len(users)} 个用户需要检查")
    
    # 只抓取一次油价数据，所有用户共用
    fetcher = OilPriceFetcher()
    logger.info("正在获取最新油价数据...")
    current_prices = fetcher.fetch_all()
    
    if not current_prices:
        logger.error("获取油价数据失败，跳过本次检查")
        return
    
    logger.info(f"成功获取 {len(current_prices)} 个省份的油价数据")
    
    # 为每个用户检查
    for user in users:
        try:
            _check_user(user, current_prices)
        except Exception as e:
            logger.error(f"[用户:{user.username}] 检查过程出错: {e}")
    
    logger.info("检查完成")
    logger.info("=" * 50)


def start_scheduler():
    """启动定时调度器"""
    scheduler.add_job(
        _check_all_users,
        trigger=IntervalTrigger(hours=1),  # 每小时检查一次，内部根据用户各自的间隔处理
        id=_job_id,
        name='油价检查',
        replace_existing=True
    )
    
    # 首次立即执行一次
    _check_all_users()
    
    scheduler.start()
    logger.info("定时调度器已启动，每小时扫描一次所有用户")


def stop_scheduler():
    """停止定时调度器"""
    scheduler.shutdown(wait=False)
    logger.info("定时调度器已停止")


def trigger_now():
    """立即触发一次检查"""
    scheduler.add_job(
        _check_all_users,
        trigger='date',
        run_date=datetime.now(),
        id='oil_check_now',
        replace_existing=True
    )
    logger.info("已手动触发一次油价检查")


def is_running():
    """检查调度器是否正在运行"""
    return scheduler.state == 1  # STATE_RUNNING = 1
