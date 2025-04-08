# Telegram RSS Bot

這是一個 Telegram 機器人，用於訂閱和接收 RSS feed 更新。

## 前置準備

### 1. 創建 Telegram Bot

1. 在 Telegram 中搜索並聯繫 [@BotFather](https://t.me/BotFather)
2. 發送 `/newbot` 命令
3. 按照提示設置：
   - 輸入機器人名稱（例如：RSS Bot）
   - 輸入機器人用戶名（必須以 bot 結尾，例如：rss_bot）
4. 保存 BotFather 提供的 API Token

### 2. 獲取您的用戶 ID

1. 在 Telegram 中搜索並聯繫 [@userinfobot](https://t.me/userinfobot)
2. 發送任意消息
3. 保存機器人回覆中的 `Id` 值

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

### Docker 部署

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
echo "USER_ID=your_user_id" >> .env
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

## 使用說明

1. 在 Telegram 中搜索您的機器人（使用之前設置的用戶名）
2. 發送 `/start` 命令開始使用
3. 使用以下命令管理 RSS 訂閱：
   - `/subscribe <URL>` - 訂閱新的 RSS feed
   - `/list` - 查看當前訂閱列表
   - `/unsubscribe <URL>` - 取消訂閱
   - `/check` - 手動檢查更新

## 文件說明

- `telegram_rss_bot.py`：主程式
- `requirements.txt`：Python 依賴
- `Dockerfile`：Docker 映像檔配置
- `docker-compose.yml`：Docker Compose 配置
- `.env`：環境變數配置
- `rss_bot.db`：SQLite 資料庫（訂閱資訊）
- `bot.log`：運行日誌
- `bot.error.log`：錯誤日誌

## 資料持久化

- 資料庫文件：`./data/rss_bot.db`
- 日誌文件：`./logs/`

## 故障排除

### 檢查容器狀態
```bash
docker-compose ps
```

### 查看日誌
```bash
docker-compose logs -f
```

### 常見問題
1. Bot 無法接收命令：
   - 確保容器正在運行
   - 檢查 Telegram Token 是否正確
   - 重新啟動 Telegram 應用

2. 容器無法啟動：
   - 檢查日誌中的錯誤信息
   - 確認環境變數設置正確
   - 確保必要的目錄權限正確 