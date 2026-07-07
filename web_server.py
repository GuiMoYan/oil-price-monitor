#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web 服务（多用户版）
提供注册、登录、配置面板、API接口
"""

import os
import json
import logging
import io
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect

from oil_fetcher import OilPriceFetcher
from models import db, User
from auth import register_user, authenticate_user, login_user, logout_user, get_current_user
from config import UserConfig
from scheduler_service import start_scheduler, stop_scheduler, is_running, trigger_now
from notifier import Notifier

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'oil-monitor-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'users.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# 内存日志缓冲区
LOG_LINES = []
MAX_LOG_LINES = 500


class MemoryLogHandler(logging.Handler):
    """将日志写入内存，供Web UI读取"""
    def emit(self, record):
        msg = self.format(record)
        LOG_LINES.append(msg)
        if len(LOG_LINES) > MAX_LOG_LINES:
            LOG_LINES.pop(0)


memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(memory_handler)


def login_required(f):
    """登录鉴权装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json:
                return jsonify({'success': False, 'error': '请先登录', 'redirect': '/login'}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


# ========== 页面路由 ==========

@app.route('/')
def index():
    """首页重定向"""
    if get_current_user():
        return redirect('/dashboard')
    return redirect('/login')


@app.route('/login')
def login_page():
    """登录页面"""
    if get_current_user():
        return redirect('/dashboard')
    return render_template('login.html')


@app.route('/register')
def register_page():
    """注册页面"""
    if get_current_user():
        return redirect('/dashboard')
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard_page():
    """用户个人面板"""
    return render_template('dashboard.html')


@app.route('/logout')
def logout_page():
    """登出"""
    logout_user()
    return redirect('/login')


# ========== API 路由 ==========

@app.route('/api/register', methods=['POST'])
def api_register():
    """用户注册"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user, msg = register_user(username, password)
    if user:
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'error': msg})


@app.route('/api/login', methods=['POST'])
def api_login():
    """用户登录"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    user, msg = authenticate_user(username, password)
    if user:
        login_user(user.id)
        return jsonify({'success': True, 'message': msg})
    else:
        return jsonify({'success': False, 'error': msg})


@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """获取当前用户配置"""
    user = get_current_user()
    config = UserConfig(user)
    settings = config.to_dict()
    return jsonify({
        'username': user.username,
        'settings': settings,
        'status': {
            'running': is_running(),
            'interval': config.check_interval_hours
        }
    })


@app.route('/api/config', methods=['POST'])
@login_required
def save_config():
    """保存当前用户配置"""
    user = get_current_user()
    data = request.get_json() or {}
    
    if not data.get('target_provinces'):
        return jsonify({'success': False, 'error': '请至少选择一个关注省份'})
    
    # 如果email_password是占位符，保留旧值
    if data.get('email_password') == '***已设置***':
        old = user.get_setting('email_password', '')
        data['email_password'] = old
    
    # 更新所有配置
    for key, value in data.items():
        user.set_setting(key, str(value))
    
    return jsonify({'success': True, 'message': '配置已保存'})


@app.route('/api/toggle', methods=['POST'])
@login_required
def toggle_scheduler():
    """启动/停止全局调度器"""
    if is_running():
        stop_scheduler()
        return jsonify({
            'success': True,
            'message': '监控已停止',
            'status': {'running': False}
        })
    else:
        start_scheduler()
        return jsonify({
            'success': True,
            'message': '监控已启动',
            'status': {'running': True}
        })


@app.route('/api/trigger', methods=['POST'])
@login_required
def trigger_check():
    """立即触发一次全局检查"""
    trigger_now()
    return jsonify({
        'success': True,
        'message': '已触发一次油价检查，请查看日志'
    })


@app.route('/api/test_push', methods=['POST'])
@login_required
def test_push():
    """测试当前用户的推送配置"""
    user = get_current_user()
    config = UserConfig(user)
    
    errors = config.validate()
    if errors:
        return jsonify({'success': False, 'error': errors[0]})
    
    notifier = Notifier(config)
    try:
        notifier.send(f"【测试推送】用户 {user.username} 的油价监控配置测试成功！")
        return jsonify({'success': True, 'message': '测试推送已发送'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取调度器状态（无需登录）"""
    return jsonify({
        'running': is_running(),
        'interval': 1
    })


@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    """获取日志"""
    offset = int(request.args.get('offset', 0))
    lines = LOG_LINES[offset:]
    next_offset = offset + len(lines)
    return jsonify({
        'lines': lines,
        'next_offset': next_offset,
        'total': len(LOG_LINES)
    })


@app.route('/api/prices', methods=['GET'])
@login_required
def get_prices():
    """获取当前用户关注省份的最新油价"""
    user = get_current_user()
    config = UserConfig(user)
    provinces = config.target_provinces
    
    if not provinces:
        return jsonify({'success': False, 'error': '未配置关注省份'})
    
    fetcher = OilPriceFetcher()
    all_prices = fetcher.fetch_all()
    
    if not all_prices:
        return jsonify({'success': False, 'error': '获取油价数据失败'})
    
    result = []
    for prov in provinces:
        if prov in all_prices:
            p = all_prices[prov]
            result.append({
                'province': prov,
                'gas92': p.get('gas92', '--'),
                'gas95': p.get('gas95', '--'),
                'gas98': p.get('gas98', '--'),
                'diesel0': p.get('diesel0', '--'),
                'fetched_at': p.get('fetched_at', '未知')
            })
    
    return jsonify({'success': True, 'prices': result})


def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        logger.info("数据库初始化完成")


def run_web_server(host='0.0.0.0', port=8080):
    """启动Web服务器"""
    init_db()
    logger.info(f"Web 服务已启动: http://{host}:{port}")
    app.run(host=host, port=port, threaded=True, use_reloader=False)
