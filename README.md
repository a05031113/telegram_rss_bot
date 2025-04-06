# Telegram RSS Bot

這是一個 Telegram 機器人，用於訂閱和接收 RSS feed 更新。

## 功能

- 訂閱 RSS feed
- 自動檢查 feed 更新（每15分鐘）
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

## 創建流程

### 1. 創建 Telegram Bot
1. 在 Telegram 中搜尋 `@BotFather`
2. 發送 `/newbot` 命令
3. 按照提示設定 bot 名稱和用戶名
4. 保存 BotFather 提供的 token

### 2. 設置開發環境
```bash
# 創建專案目錄
mkdir telegram-rss-bot
cd telegram-rss-bot

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate  # Windows

# 安裝必要套件
pip install python-telegram-bot feedparser python-dotenv
```

### 3. 創建必要文件
1. 創建 `.env` 文件：
```
TELEGRAM_TOKEN=your_bot_token
```

2. 創建 `requirements.txt`：
```
python-telegram-bot==13.7
feedparser==6.0.10
python-dotenv==0.19.0
```

### 4. 設置自動啟動（macOS）
```bash
# 創建 launchd 配置文件
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

# 加載服務
launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist
```

### 5. 測試 Bot
1. 在 Telegram 中搜尋您的 bot
2. 發送 `/start` 命令
3. 測試其他命令：
   - `/showid` - 顯示用戶 ID
   - `/subscribe <URL>` - 訂閱 RSS feed
   - `/list` - 查看訂閱列表
   - `/check` - 手動檢查更新

### 6. 故障排除
1. 檢查 bot 是否運行：
```bash
ps aux | grep "python telegram_rss_bot.py"
```

2. 查看日誌：
```bash
cat bot.log bot.error.log
```

3. 重新啟動：
```bash
# 停止所有 bot 進程
pkill -9 -f "python telegram_rss_bot.py"

# 清理日誌文件
rm -f bot.pid bot.log bot.error.log

# 重新啟動 bot
cd /path/to/your/bot && source venv/bin/activate && nohup python telegram_rss_bot.py > bot.log 2> bot.error.log &
```

### 7. 維護建議
- 定期檢查日誌文件
- 確保 RSS feed URL 有效
- 監控 bot 的運行狀態
- 定期更新依賴套件

## 安裝

1. 克隆此倉庫：
```bash
git clone https://github.com/yourusername/telegram-rss-bot.git
cd telegram-rss-bot
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

## 運行

### 手動運行
```bash
python telegram_rss_bot.py
```

### 自動啟動（macOS）
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
        <string>cd /Users/yanghaoyu/Documents/Telegram_Bot/RSS && source venv/bin/activate && python telegram_rss_bot.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yanghaoyu/Documents/Telegram_Bot/RSS/bot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yanghaoyu/Documents/Telegram_Bot/RSS/bot.error.log</string>
</dict>
</plist>
EOF
```

2. 加載服務：
```bash
launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist
```

## 日誌

- 標準輸出日誌：`bot.log`
- 錯誤日誌：`bot.error.log`

## 故障排除

如果 bot 沒有響應：
1. 檢查 bot 是否正在運行：`ps aux | grep "python telegram_rss_bot.py"`
2. 檢查日誌文件：`cat bot.log bot.error.log`
3. 重新啟動 bot：
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.telegram.rssbot.plist
   launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist
   ```

## 注意事項

1. Bot 會自動在系統啟動時運行
2. 如果 bot 崩潰，系統會自動重啟它
3. 所有日誌都會保存在 `bot.log` 檔案中
4. 訂閱資訊和更新記錄都保存在 `rss_bot.db` 資料庫中
5. 如果遇到 "Conflict" 錯誤，表示有多個 bot 實例在運行，請使用進程管理指令停止所有實例後重新啟動

## 常見問題

1. **Bot 沒有回應**
   - 檢查 bot 是否正在運行：`launchctl list | grep rssbot`
   - 查看日誌：`tail -f bot.log`

2. **訂閱失敗**
   - 確認 RSS feed URL 是否正確
   - 檢查日誌中的錯誤訊息

3. **收到重複的更新**
   - 這可能是因為有多個 bot 實例在運行
   - 使用 `pkill -f "python telegram_rss_bot.py"` 停止所有實例
   - 重新啟動單一實例

## 資料儲存

- 訂閱資訊：`rss_bot.db`
- 日誌檔案：`bot.log`
- 系統服務設定：`~/Library/LaunchAgents/com.telegram.rssbot.plist` 