# 使用 Python 3.11 作為基礎映像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序文件
COPY telegram_rss_bot.py .

# 創建數據和日誌目錄
RUN mkdir -p data logs

# 設置環境變數
ENV DB_FILE=/app/data/rss_bot.db
ENV LOG_DIR=/app/logs

# 運行應用
CMD ["python", "telegram_rss_bot.py"] 