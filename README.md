# 国内油价监控推送工具（多用户版）

> 部署在 **Debian VPS** 上，打开浏览器就能注册账号、配置推送。支持多用户同时使用，每个用户独立关注不同省份、独立接收推送。

## 一、功能介绍

- **多用户注册**：任何人都可以在浏览器注册账号
- **个人独立配置**：每个用户独立设置关注省份、邮箱、Bark Key
- **独立推送**：油价变动时，每个用户只收到自己关注省份的推送
- **Web 上实时显示关注城市的当前油价**
- **自动抓取全国 31 省** 最新油价（92/95/98汽油 + 0号柴油）
- **有变动才推送**，不会骚扰
- 支持邮件推送 + Bark 推送（iPhone），可同时开启
- 支持手动"立即检查"和"测试推送"
- 实时查看运行日志

## 二、文件结构

```
oil-price-monitor/
├── app.py                 # 主入口（启动Web + 调度器）
├── web_server.py          # Flask Web服务（注册/登录/配置面板/API）
├── scheduler_service.py   # 后台定时任务（遍历所有用户检查）
├── models.py              # 数据库模型（SQLite + SQLAlchemy）
├── auth.py                # 用户认证（注册/登录/密码哈希）
├── oil_fetcher.py         # 油价抓取（不用改）
├── notifier.py            # 推送模块（不用改）
├── config.py              # 用户配置类（不用改）
├── storage.py             # 兼容旧版，不再使用
├── requirements.txt       # Python依赖
├── Dockerfile             # Docker镜像
├── docker-compose.yml     # Docker Compose配置
├── templates/
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   └── dashboard.html     # 用户个人面板
└── README.md              # 本文档
```

## 三、前置准备

你需要一台 **Debian/Ubuntu VPS**，并且已安装 Docker。

```bash
docker --version
docker-compose --version
```

如果没有，执行：

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 重新登录SSH生效
```

## 四、部署步骤（VPS 上执行）

### 第1步：上传项目到 VPS

```bash
mkdir -p /opt/oil-price-monitor
cd /opt/oil-price-monitor
# 把项目文件全部上传到这个目录
```

### 第2步：构建并运行（docker run）

```bash
cd /opt/oil-price-monitor

# 构建镜像
docker build -t oil-price-monitor:latest .

# 运行容器
docker run -d \
  --name oil-price-monitor \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /opt/oil-price-monitor/data:/app/data \
  -e SECRET_KEY=your-random-secret-key-here \
  oil-price-monitor:latest
```

> **SECRET_KEY** 用于加密用户 session，建议改成随机字符串，但也可以留空（会用默认的）。

### 方式二：直接拉取 Docker Hub 镜像（推荐，不用构建）

镜像地址：https://hub.docker.com/r/mrchengshi/oil-price-monitor

```bash
# 直接拉取并运行（一行命令搞定）
docker run -d \
  --name oil-price-monitor \
  --restart unless-stopped \
  -p 8080:8080 \
  -v /opt/oil-price-monitor/data:/app/data \
  -e SECRET_KEY=your-random-secret-key-here \
  mrchengshi/oil-price-monitor:latest
```

> 不需要上传代码、不需要构建，直接拉取镜像运行即可。

### 方式三：docker-compose 方式

```bash
cd /opt/oil-price-monitor
docker-compose up -d
```

### 第3步：打开浏览器使用

```
http://你的VPS_IP地址:8080
```

**首次使用流程：**
1. 点击 **"没有账号？立即注册"** → 填用户名密码 → 注册
2. 注册成功后自动跳转登录 → 登录
3. 进入个人面板：
   - 选省份（可多选）
   - 勾选邮件/Bark推送，填信息
   - 点击 **「保存配置」**
   - 点击 **「测试推送」** 验证是否能收到
   - 点击 **「启动监控」**
4. 点击 **「立即检查」** 测试一下

> **首次运行**只会记录油价，不会推送。从第二次开始才会对比变化并推送。

### 第4步：开放防火墙端口

云服务器（阿里云/腾讯云等）需要在控制台**安全组**里放行 **8080 端口**。

如果 VPS 上有 `ufw`：

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

## 五、多用户说明

- **每个用户账号独立**：不同用户登录后只能看到自己的配置
- **推送互不影响**：用户A关注北京，用户B关注上海，各自只收到自己的推送
- **油价数据共用**：后台只抓取一次全国油价，所有用户共用同一批数据
- **没有管理员后台**：所有人自行注册，没有限制

## 六、VPS 常用操作

### 查看日志

```bash
docker logs -f oil-price-monitor
```

### 停止程序

```bash
docker stop oil-price-monitor
docker rm oil-price-monitor
```

### 重启程序（更新代码后）

```bash
docker stop oil-price-monitor
docker rm oil-price-monitor
docker build -t oil-price-monitor:latest .
docker run -d --name oil-price-monitor --restart unless-stopped -p 8080:8080 -v /opt/oil-price-monitor/data:/app/data -e SECRET_KEY=your-random-secret-key-here oil-price-monitor:latest
```

### 查看容器状态

```bash
docker ps | grep oil-price-monitor
```

### 进入容器调试

```bash
docker exec -it oil-price-monitor /bin/bash
```

### 查看数据库（用户数据）

```bash
docker exec -it oil-price-monitor sqlite3 /app/data/users.db "SELECT id, username, created_at FROM users;"
```

## 七、配置项说明

### 邮件推送（以 QQ 邮箱为例）

| 字段 | 填写内容 | 说明 |
|------|----------|------|
| 启用邮件推送 | ☑️ 勾选 | 开关 |
| SMTP 服务器 | `smtp.qq.com` | QQ邮箱服务器 |
| SMTP 端口 | `465` | QQ邮箱用465（SSL） |
| 发件邮箱 | `123456@qq.com` | 你的QQ邮箱地址 |
| 授权码 / 密码 | `abc123def...` | **是授权码，不是登录密码！** |
| 发件人显示名 | `油价监控` | 邮件里显示的发件人名字 |
| 收件人邮箱 | `123456@qq.com` | 可以是同一个邮箱 |

**获取 QQ 邮箱授权码：**
1. 登录 [QQ邮箱](https://mail.qq.com)
2. 点击顶部【设置】→【账户】
3. 找到 "POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启 "SMTP服务"，复制弹出的 **16位授权码**

### Bark 推送（iPhone）

| 字段 | 填写内容 | 说明 |
|------|----------|------|
| 启用 Bark 推送 | ☑️ 勾选 | 开关 |
| Bark Key | `xxxxxxxxxx` | 从 Bark App 复制的设备Key |
| Bark 服务器 | 留空 | 使用官方服务器 |

**获取 Bark Key：**
1. App Store 搜索 **"Bark"**，下载安装
2. 打开 App，点击 **"注册设备"**
3. 点击右上角 **+** 号添加服务器，选择 **"默认服务器"**
4. 回到首页，长按设备，点击 **"复制测试链接"**
5. 链接格式：`https://api.day.app/xxxxxxxxxx/`
6. 其中 `xxxxxxxxxx` 就是 **Bark Key**

### 关注省份列表

以下31个省份全部可选：

北京、上海、天津、重庆、河北、山西、辽宁、吉林、黑龙江、江苏、浙江、安徽、福建、江西、山东、河南、湖北、湖南、广东、广西、海南、四川、贵州、云南、西藏、陕西、甘肃、青海、宁夏、新疆、内蒙古

## 八、常见问题

### Q1：浏览器打不开页面？

1. 确认 VPS 防火墙或云服务器安全组已放行 **8080 端口**
2. 确认容器正在运行：`docker ps | grep oil-price-monitor`
3. 确认 VPS 的 IP 地址正确

### Q2：想绑定域名访问？

在 VPS 上装 Nginx 做反向代理：

```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/oil-monitor
```

```nginx
server {
    listen 80;
    server_name oil.yourdomain.com;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/oil-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Q3：推送没有收到？

- **Bark**：检查 iPhone 通知权限；检查 Bark Key 是否填对；在 Bark App 里测试推送
- **邮件**：检查 `EMAIL_PASSWORD` 是不是**授权码**（不是登录密码）；检查 QQ邮箱 SMTP 服务是否开启

### Q4：多久检查一次？

后台每小时扫描一次所有用户。每个用户首次记录油价后，从第二次开始对比变化并推送。国内油价通常每10个工作日调整一次，所以推送不会太频繁。

### Q5：用户数据保存在哪里？

所有用户数据和配置保存在 VPS 本地的 SQLite 数据库：`/opt/oil-price-monitor/data/users.db`。即使删除容器重新创建，数据也不会丢失。

### Q6：VPS 重启后程序还在吗？

在。因为加了 `--restart unless-stopped`，Docker 会自动在系统启动时拉起容器。

### Q7：数据来源可靠吗？

数据从公开油价查询网站（46.la / 团友网）抓取，来源于国家发改委及各地加油站公开信息，仅供参考。实际加油价格以当地加油站为准。

### Q8：密码安全性如何？

用户密码使用 **Werkzeug** 的 `generate_password_hash` 进行哈希存储，数据库里不会保存明文密码。SESSION 使用 Flask 内置的 secure cookie 机制。

## 九、技术架构

| 组件 | 说明 |
|------|------|
| Web 框架 | Flask 3.x + Flask-SQLAlchemy |
| 数据库 | SQLite（用户表、配置表、油价记录表）|
| 定时调度 | APScheduler，每小时遍历所有用户 |
| 数据抓取 | requests + BeautifulSoup，双源自动切换 |
| 密码安全 | Werkzeug bcrypt 哈希 |
| 容器 | Python 3.11 slim，暴露 8080 端口 |

## 十、更新日志

- **v3.0**：新增多用户注册/登录，每个用户独立配置和推送，适配 SQLite 数据库
- **v2.0**：新增 Web UI 配置面板，支持浏览器一键配置，适配 VPS 部署
- **v1.0**：邮件推送、Bark推送、多省份监控、Docker 部署

---

如遇到问题，查看日志排查：

```bash
docker logs -f oil-price-monitor
```
