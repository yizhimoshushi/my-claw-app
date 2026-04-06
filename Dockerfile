FROM python:3.9-slim

WORKDIR /app

COPY . .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# 使用 gunicorn 启动，绑定到 0.0.0.0:5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
