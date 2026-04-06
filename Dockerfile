FROM python:3.9-slim

WORKDIR /app

# 复制文件
COPY . .

# 新增：列出目录内容作为调试
RUN ls -la

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# 使用 gunicorn 启动，绑定到 0.0.0.0:5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
