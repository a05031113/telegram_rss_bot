# Telegram RSS Bot

這是一個 Telegram 機器人，用於訂閱和接收 RSS feed 更新。

## 功能

- 訂閱 RSS feed
- 自動檢查 feed 更新（每20分鐘）
- 手動檢查 feed 更新
- 查看訂閱列表
- 取消訂閱

## 命令列表

- `/start` - 開始使用 bot
- `/showid` - 顯示您的用戶 ID
- `/subscribe <URL>` - 訂閱 RSS feed
- `/list` - 查看您的訂閱列表
- `/unsubscribe <URL>` - 取消訂閱
- `/check` - 手動檢查所有訂閱的更新

## 部署方式

### 方式一：Docker 部署（推薦）

1. 安裝必要軟體：
```bash
# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安裝 Docker Compose
sudo apt-get install docker-compose  # Ubuntu/Debian
# 或
sudo yum install docker-compose      # CentOS
```

2. 克隆專案：
```bash
git clone <您的專案倉庫URL>
cd <專案目錄>
```

3. 設置環境變數：
```bash
# 創建 .env 文件
echo "TELEGRAM_TOKEN=your_bot_token" > .env
```

4. 創建必要的目錄：
```bash
mkdir -p data logs
```

5. 啟動服務：
```bash
docker-compose up -d
```

Docker 相關命令：
- 查看日誌：`docker-compose logs -f`
- 停止服務：`docker-compose down`
- 重新啟動：`docker-compose restart`
- 查看容器狀態：`docker-compose ps`

### 方式二：直接部署

1. 克隆此倉庫：
```bash
git clone <您的專案倉庫URL>
cd <專案目錄>
```

2. 創建並激活虛擬環境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

3. 安裝依賴：
```bash
pip install -r requirements.txt
```

4. 創建 `.env` 文件並設置環境變數：
```
TELEGRAM_TOKEN=your_bot_token
```

### 方式三：macOS 自動啟動

1. 創建 `launchd` 配置文件：
```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.telegram.rssbot.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram.rssbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/your/bot && source venv/bin/activate && python telegram_rss_bot.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/your/bot/bot.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/your/bot/bot.error.log</string>
</dict>
</plist>
EOF
```

2. 加載服務：
```bash
launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist
```

## 文件說明

- `telegram_rss_bot.py`：主程式
- `requirements.txt`：Python 依賴
- `Dockerfile`：Docker 映像檔配置
- `docker-compose.yml`：Docker Compose 配置
- `.env`：環境變數配置
- `data/rss_bot.db`：SQLite 資料庫（訂閱資訊）
- `logs/`：日誌目錄
  - `bot.log`：一般日誌
  - `bot.error.log`：錯誤日誌

## 資料持久化

### Docker 部署
- 資料庫文件：`./data/rss_bot.db`
- 日誌文件：`./logs/`

### 直接部署
- 資料庫文件：`rss_bot.db`
- 日誌文件：`bot.log` 和 `bot.error.log`

## 故障排除

### Docker 部署
1. 檢查容器狀態：
```bash
docker-compose ps
```

2. 查看日誌：
```bash
docker-compose logs -f
```

3. 重新啟動服務：
```bash
docker-compose restart
```

### 直接部署
1. 檢查進程：
```bash
ps aux | grep "python telegram_rss_bot.py"
```

2. 查看日誌：
```bash
cat bot.log bot.error.log
```

### macOS 服務
1. 檢查服務狀態：
```bash
launchctl list | grep telegram
```

2. 重新啟動服務：
```bash
launchctl unload ~/Library/LaunchAgents/com.telegram.rssbot.plist
launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist
``` 