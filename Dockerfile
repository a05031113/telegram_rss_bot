# 使用 Python 3.11 作為基礎映像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建日誌目錄
RUN mkdir -p /app/logs

# 設置環境變數
ENV PYTHONUNBUFFERED=1

# 運行 bot
CMD ["python", "telegram_rss_bot.py"] 