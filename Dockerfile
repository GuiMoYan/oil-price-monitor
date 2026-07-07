# 使用Python 3.11官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区为北京时间
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# 暴露Web配置面板端口
EXPOSE 8080

# 先安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY *.py .
COPY templates ./templates

# 创建数据目录
RUN mkdir -p /app/data

# 容器启动时运行主程序
CMD ["python", "app.py"]
