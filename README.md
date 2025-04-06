# Telegram RSS Bot 使用說明

這是一個 Telegram RSS Bot，可以幫助您訂閱和追蹤 RSS feed 的更新。

## 基本指令

### Bot 指令
在 Telegram 中與 bot 對話時可以使用以下指令：

- `/start` - 開始使用 bot，顯示歡迎訊息和可用指令
- `/subscribe <url>` - 訂閱新的 RSS feed
  - 範例：`/subscribe https://example.com/feed.xml`
- `/list` - 查看您目前的所有訂閱
- `/unsubscribe <編號>` - 取消訂閱指定的 feed
  - 範例：`/unsubscribe 1`（取消訂閱列表中的第一個 feed）
- `/check` - 立即檢查所有訂閱的 feed 是否有新內容

## 系統管理指令

### 啟動/停止 Bot
- 啟動 bot：
  ```bash
  launchctl load ~/Library/LaunchAgents/com.rssbot.plist
  ```

- 停止 bot：
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.rssbot.plist
  ```

- 重新啟動 bot：
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.rssbot.plist
  launchctl load ~/Library/LaunchAgents/com.rssbot.plist
  ```

### 查看狀態
- 查看 bot 運行狀態：
  ```bash
  launchctl list | grep rssbot
  ```

- 查看 bot 日誌：
  ```bash
  tail -f bot.log
  ```

### 進程管理
- 強制停止所有 bot 實例：
  ```bash
  pkill -f "python telegram_rss_bot.py"
  ```

- 檢查是否有 bot 實例在運行：
  ```bash
  ps aux | grep "python telegram_rss_bot.py"
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
- 系統服務設定：`~/Library/LaunchAgents/com.rssbot.plist` 