#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户配置类
每个用户独立配置，从数据库读写
"""

from models import User


class UserConfig:
    """用户配置（绑定到具体用户）"""

    def __init__(self, user):
        self.user = user

    # ===== 通用配置 =====
    @property
    def target_provinces(self):
        provinces = self.user.get_setting('target_provinces', '北京')
        return [p.strip() for p in provinces.split(',') if p.strip()]

    @property
    def check_interval_hours(self):
        try:
            return int(self.user.get_setting('check_interval_hours', '12'))
        except ValueError:
            return 12

    # ===== 邮件配置 =====
    @property
    def email_enabled(self):
        return self.user.get_setting('email_enabled', 'false').lower() == 'true'

    @property
    def email_smtp_server(self):
        return self.user.get_setting('email_smtp_server', '')

    @property
    def email_smtp_port(self):
        try:
            return int(self.user.get_setting('email_smtp_port', '465'))
        except ValueError:
            return 465

    @property
    def email_username(self):
        return self.user.get_setting('email_username', '')

    @property
    def email_password(self):
        return self.user.get_setting('email_password', '')

    @property
    def email_sender(self):
        return self.user.get_setting('email_sender', '')

    @property
    def email_receiver(self):
        return self.user.get_setting('email_receiver', '')

    # ===== Bark配置 =====
    @property
    def bark_enabled(self):
        return self.user.get_setting('bark_enabled', 'false').lower() == 'true'

    @property
    def bark_key(self):
        return self.user.get_setting('bark_key', '')

    @property
    def bark_server(self):
        return self.user.get_setting('bark_server', 'https://api.day.app')

    def validate(self):
        """验证配置是否有效"""
        errors = []
        if not self.email_enabled and not self.bark_enabled:
            errors.append("未启用任何推送方式，请至少开启邮件或Bark推送")
        if self.email_enabled:
            if not self.email_smtp_server:
                errors.append("邮件推送已开启但未配置 SMTP服务器")
            if not self.email_username:
                errors.append("邮件推送已开启但未配置 邮箱用户名")
            if not self.email_password:
                errors.append("邮件推送已开启但未配置 邮箱密码/授权码")
            if not self.email_receiver:
                errors.append("邮件推送已开启但未配置 收件人邮箱")
        if self.bark_enabled and not self.bark_key:
            errors.append("Bark推送已开启但未配置 Bark Key")
        return errors

    def to_dict(self):
        """导出配置（脱敏）"""
        return {
            'target_provinces': self.user.get_setting('target_provinces', ''),
            'check_interval_hours': self.check_interval_hours,
            'email_enabled': self.email_enabled,
            'email_smtp_server': self.email_smtp_server,
            'email_smtp_port': self.email_smtp_port,
            'email_username': self.email_username[:3] + '***' if self.email_username else '',
            'email_sender': self.email_sender,
            'email_receiver': self.email_receiver[:3] + '***' if self.email_receiver else '',
            'bark_enabled': self.bark_enabled,
            'bark_key': self.bark_key[:3] + '***' if self.bark_key else '',
            'bark_server': self.bark_server,
        }

    def update_from_dict(self, data):
        """从字典更新配置"""
        for key, value in data.items():
            self.user.set_setting(key, str(value))
