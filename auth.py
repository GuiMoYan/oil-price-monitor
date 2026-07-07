#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证工具
"""

import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from models import User, db


def validate_username(username):
    """验证用户名：2-20位，字母/数字/下划线/中文"""
    if not username or len(username) < 2 or len(username) > 20:
        return False, '用户名长度需在2-20个字符之间'
    if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', username):
        return False, '用户名只能包含中文、字母、数字和下划线'
    return True, ''


def validate_password(password):
    """验证密码：至少6位"""
    if not password or len(password) < 6:
        return False, '密码长度至少6位'
    return True, ''


def register_user(username, password):
    """注册新用户"""
    ok, msg = validate_username(username)
    if not ok:
        return None, msg
    
    ok, msg = validate_password(password)
    if not ok:
        return None, msg
    
    # 检查用户名是否已存在
    existing = User.query.filter_by(username=username).first()
    if existing:
        return None, '用户名已被注册，请换一个'
    
    # 创建用户
    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    
    # 初始化默认配置
    user.set_setting('target_provinces', '北京')
    user.set_setting('check_interval_hours', '12')
    user.set_setting('email_enabled', 'false')
    user.set_setting('email_smtp_server', 'smtp.qq.com')
    user.set_setting('email_smtp_port', '465')
    user.set_setting('email_username', '')
    user.set_setting('email_password', '')
    user.set_setting('email_sender', '油价监控')
    user.set_setting('email_receiver', '')
    user.set_setting('bark_enabled', 'false')
    user.set_setting('bark_key', '')
    user.set_setting('bark_server', 'https://api.day.app')
    
    return user, '注册成功'


def authenticate_user(username, password):
    """验证用户登录"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, '用户名或密码错误'
    if not check_password_hash(user.password_hash, password):
        return None, '用户名或密码错误'
    return user, '登录成功'


def login_user(user_id):
    """将用户登录状态写入session"""
    session['user_id'] = user_id
    session.permanent = True


def logout_user():
    """登出用户"""
    session.pop('user_id', None)


def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def is_logged_in():
    """检查是否已登录"""
    return 'user_id' in session
