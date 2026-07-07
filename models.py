#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型
使用 SQLite + Flask-SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    settings = db.relationship('UserSetting', backref='user', lazy=True, cascade='all, delete-orphan')
    oil_prices = db.relationship('UserOilPrice', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def get_setting(self, key, default=''):
        """获取用户配置项"""
        s = UserSetting.query.filter_by(user_id=self.id, key=key).first()
        return s.value if s else default
    
    def set_setting(self, key, value):
        """设置用户配置项"""
        s = UserSetting.query.filter_by(user_id=self.id, key=key).first()
        if s:
            s.value = str(value)
        else:
            s = UserSetting(user_id=self.id, key=key, value=str(value))
            db.session.add(s)
        db.session.commit()
    
    def get_all_settings(self):
        """获取用户所有配置"""
        settings = {}
        for s in self.settings:
            settings[s.key] = s.value
        return settings
    
    def get_oil_price(self, province):
        """获取用户某省份上次油价"""
        return UserOilPrice.query.filter_by(user_id=self.id, province=province).first()
    
    def save_oil_price(self, province, data):
        """保存用户某省份油价"""
        p = UserOilPrice.query.filter_by(user_id=self.id, province=province).first()
        if p:
            p.gas92 = data.get('gas92', '0.00')
            p.gas95 = data.get('gas95', '0.00')
            p.gas98 = data.get('gas98', '0.00')
            p.diesel0 = data.get('diesel0', '0.00')
            p.fetched_at = data.get('fetched_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
        else:
            p = UserOilPrice(
                user_id=self.id,
                province=province,
                gas92=data.get('gas92', '0.00'),
                gas95=data.get('gas95', '0.00'),
                gas98=data.get('gas98', '0.00'),
                diesel0=data.get('diesel0', '0.00'),
                fetched_at=data.get('fetched_at', datetime.now().strftime('%Y-%m-%d %H:%M'))
            )
            db.session.add(p)
        db.session.commit()


class UserSetting(db.Model):
    """用户配置表（键值对）"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    key = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Text, default='')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'key', name='uix_user_setting'),)


class UserOilPrice(db.Model):
    """用户油价记录表"""
    __tablename__ = 'user_oil_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    province = db.Column(db.String(20), nullable=False)
    gas92 = db.Column(db.String(10), default='0.00')
    gas95 = db.Column(db.String(10), default='0.00')
    gas98 = db.Column(db.String(10), default='0.00')
    diesel0 = db.Column(db.String(10), default='0.00')
    fetched_at = db.Column(db.String(20), default='')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'province', name='uix_user_oil_price'),)
