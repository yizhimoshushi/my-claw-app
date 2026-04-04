# 1. 基于 Python 3.9 镜像
FROM python:3.9-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 复制所有文件到容器
COPY . .

# 4. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 暴露 5000 端口
EXPOSE 5000

# 6. 启动命令
CMD ["python", "app.py"]