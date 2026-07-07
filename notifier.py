#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送通知模块
支持邮件和Bark两种推送方式
"""

import os
import re
import json
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

logger = logging.getLogger(__name__)


class Notifier:
    """推送通知器"""
    
    def __init__(self, config):
        self.config = config
    
    def send(self, message):
        """发送推送通知（所有已配置的渠道）"""
        results = []
        
        # 邮件推送
        if self.config.email_enabled:
            try:
                self._send_email(message)
                results.append("邮件推送成功")
            except Exception as e:
                logger.error(f"邮件推送失败: {e}")
                results.append(f"邮件推送失败: {e}")
        
        # Bark推送
        if self.config.bark_enabled:
            try:
                self._send_bark(message)
                results.append("Bark推送成功")
            except Exception as e:
                logger.error(f"Bark推送失败: {e}")
                results.append(f"Bark推送失败: {e}")
        
        if not results:
            logger.warning("没有配置任何推送方式，请检查环境变量配置")
        else:
            logger.info(f"推送结果: {'; '.join(results)}")
    
    def _send_email(self, message):
        """发送邮件通知"""
        smtp_server = self.config.email_smtp_server
        smtp_port = self.config.email_smtp_port
        username = self.config.email_username
        password = self.config.email_password
        sender = self.config.email_sender
        receiver = self.config.email_receiver
        
        if not all([smtp_server, username, password, receiver]):
            raise ValueError("邮件配置不完整，请检查 SMTP_SERVER, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECEIVER")
        
        if not sender:
            sender = username
        
        # 创建邮件内容
        subject = f"【油价变动提醒】{datetime.now().strftime('%m月%d日')}"
        
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = Header(sender, 'utf-8')
        msg['To'] = Header(receiver, 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(username, password)
            server.sendmail(sender, [receiver], msg.as_string())
        
        logger.info(f"邮件已发送至 {receiver}")
    
    def _send_bark(self, message):
        """发送Bark推送通知"""
        bark_key = self.config.bark_key
        bark_server = self.config.bark_server
        
        if not bark_key:
            raise ValueError("Bark推送未配置，请设置 BARK_KEY")
        
        # 使用默认Bark服务器或自定义服务器
        if not bark_server:
            bark_server = "https://api.day.app"
        
        # 清理URL末尾斜杠
        bark_server = bark_server.rstrip('/')
        
        # 准备推送内容
        title = f"油价变动提醒 {datetime.now().strftime('%m-%d')}"
        
        # 对内容进行URL编码处理
        # Bark支持URL格式: /{key}/{title}/{body}
        body = message
        
        # 构建推送URL
        # 注意：如果内容太长，Bark可能会截断
        url = f"{bark_server}/{bark_key}/{requests.utils.quote(title)}/{requests.utils.quote(body)}"
        
        # 可选参数
        params = {
            'group': '油价监控',  # 消息分组
            'isArchive': '1',     # 保存到历史记录
        }
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        result = resp.json()
        if result.get('code') == 200 or result.get('message') == 'success':
            logger.info(f"Bark推送已发送至 {bark_key}")
        else:
            logger.warning(f"Bark返回未知状态: {result}")
