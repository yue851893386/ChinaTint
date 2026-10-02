FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HF Spaces 要求监听 7860（PORT 环境变量已自动注入）
CMD ["python", "app.py"]
