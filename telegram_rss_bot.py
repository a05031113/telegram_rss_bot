import os
import logging
import feedparser
import time
from datetime import datetime
import hashlib
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import ssl
import urllib.request
import urllib.error
import sqlite3
from contextlib import contextmanager
import sys
from telegram import Update
import re

# Load environment variables from .env file
load_dotenv()

# 資料庫設定
DB_FILE = os.getenv('DB_FILE', 'data/rss_bot.db')

# 日誌設定
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'bot.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'bot.error.log')

# 確保日誌和資料目錄存在
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# 配置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.FileHandler(ERROR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 檢查環境變數
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    logger.error("未設置 TELEGRAM_TOKEN 環境變數")
    sys.exit(1)

@contextmanager
def get_db():
    """資料庫連接管理器"""
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """初始化資料庫表格"""
    with get_db() as conn:
        cursor = conn.cursor()
        # 建立訂閱表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            chat_id INTEGER,
            feed_url TEXT,
            last_entry TEXT,
            PRIMARY KEY (chat_id, feed_url)
        )
        ''')
        
        # 建立最後更新記錄表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_hash TEXT NOT NULL UNIQUE,
            last_entry_id TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        logger.info("資料庫初始化完成")

def get_user_subscriptions(user_id):
    """獲取用戶的訂閱列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT feed_url, last_entry FROM subscriptions WHERE chat_id = ?', (user_id,))
        return cursor.fetchall()

def add_subscription(user_id, feed_url, feed_title):
    """添加新的訂閱"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO subscriptions (chat_id, feed_url, last_entry) VALUES (?, ?, ?)',
                (user_id, feed_url, '')
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_subscription(user_id, feed_url):
    """移除訂閱"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM subscriptions WHERE chat_id = ? AND feed_url = ?',
            (user_id, feed_url)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_last_entry(feed_hash):
    """獲取 feed 的最後更新記錄"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT last_entry_id FROM last_entries WHERE feed_hash = ?', (feed_hash,))
        result = cursor.fetchone()
        return result[0] if result else None

def update_last_entry(feed_hash, last_entry_id):
    """更新 feed 的最後更新記錄"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO last_entries (feed_hash, last_entry_id, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (feed_hash, last_entry_id))
        conn.commit()

def fetch_feed(url):
    """安全地獲取 RSS feed 內容"""
    try:
        # 創建一個自定義的 SSL 上下文
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 使用 urllib 獲取 feed 內容
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context) as response:
            feed_content = response.read().decode('utf-8')
            return feedparser.parse(feed_content)
    except urllib.error.URLError as e:
        logger.error(f"URL 錯誤: {str(e)}")
        raise Exception(f"無法訪問 feed URL: {str(e)}")
    except Exception as e:
        logger.error(f"獲取 feed 時發生錯誤: {str(e)}")
        raise Exception(f"獲取 feed 時發生錯誤: {str(e)}")

def start(update: Update, context: CallbackContext) -> None:
    """處理 /start 命令"""
    update.message.reply_text(
        '歡迎使用 RSS Feed Bot！\n'
        '使用 /subscribe <RSS feed URL> 來訂閱一個 feed\n'
        '使用 /list 來查看您的訂閱\n'
        '使用 /unsubscribe 來取消訂閱'
    )
    logger.info(f"用戶 {update.effective_user.id} 開始使用 bot")

def show_id(update, context):
    """顯示用戶的 ID"""
    user = update.effective_user
    update.message.reply_text(f'您的用戶 ID 是：{user.id}')

def subscribe(update: Update, context: CallbackContext) -> None:
    """處理 /subscribe 命令"""
    if not context.args:
        update.message.reply_text('請提供 RSS feed URL，例如：/subscribe https://example.com/feed.xml')
        return

    feed_url = context.args[0]
    chat_id = update.effective_chat.id

    try:
        # 禁用 SSL 驗證
        ssl._create_default_https_context = ssl._create_unverified_context
        feed = fetch_feed(feed_url)
        
        if feed.bozo:
            update.message.reply_text('無法解析此 RSS feed，請確認 URL 是否正確')
            logger.error(f"無法解析 feed: {feed_url}, 錯誤: {feed.bozo_exception}")
            return
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO subscriptions (chat_id, feed_url, last_entry) VALUES (?, ?, ?)',
                         (chat_id, feed_url, ''))
            conn.commit()

        update.message.reply_text(f'成功訂閱 {feed_url}')
        logger.info(f"用戶 {chat_id} 訂閱了 {feed_url}")

    except Exception as e:
        update.message.reply_text('訂閱失敗，請確認 URL 是否正確')
        logger.error(f"訂閱失敗: {str(e)}")

def list_subscriptions(update: Update, context: CallbackContext) -> None:
    """處理 /list 命令"""
    chat_id = update.effective_chat.id
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT feed_url FROM subscriptions WHERE chat_id = ?', (chat_id,))
        subscriptions = cursor.fetchall()

    if not subscriptions:
        update.message.reply_text('您目前沒有任何訂閱')
        return
    
    message = '您的訂閱列表：\n\n'
    for sub in subscriptions:
        message += f'- {sub[0]}\n'
    
    update.message.reply_text(message)
    logger.info(f"用戶 {chat_id} 查看了訂閱列表")

def unsubscribe(update: Update, context: CallbackContext) -> None:
    """處理 /unsubscribe 命令"""
    if not context.args:
        update.message.reply_text('請提供要取消訂閱的 RSS feed URL')
        return

    feed_url = context.args[0]
    chat_id = update.effective_chat.id

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subscriptions WHERE chat_id = ? AND feed_url = ?',
                      (chat_id, feed_url))
        conn.commit()

    update.message.reply_text(f'已取消訂閱 {feed_url}')
    logger.info(f"用戶 {chat_id} 取消訂閱了 {feed_url}")

def send_user_update(context: CallbackContext, feed_title, entry):
    """發送更新給指定用戶"""
    user_id = os.getenv('USER_ID')
    if not user_id:
        logger.warning("未設定用戶 ID，無法發送更新")
        return
    
    try:
        title = entry.get('title', '無標題')
        link = entry.get('link', '')
        published = entry.get('published', '未知日期')
        
        if 'summary' in entry:
            summary = entry.summary
        elif 'description' in entry:
            summary = entry.description
        else:
            summary = ''
        
        summary = summary.replace('<p>', '').replace('</p>', '\n\n')
        summary = summary[:200] + '...' if len(summary) > 200 else summary
        
        message = f"📢 <b>{feed_title}</b>\n\n"
        message += f"<b>{title}</b>\n"
        message += f"📅 {published}\n\n"
        message += f"{summary}\n\n"
        message += f"🔗 <a href='{link}'>閱讀更多</a>"
        
        context.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode=telegram.ParseMode.HTML,
            disable_web_page_preview=False
        )
    except Exception as e:
        logger.error(f"發送用戶更新時發生錯誤: {e}")

def check_feeds(context: CallbackContext) -> None:
    """檢查所有訂閱的 feed 是否有更新"""
    logger.info("開始檢查 feed 更新")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id, feed_url, last_entry FROM subscriptions')
        subscriptions = cursor.fetchall()

    # 禁用 SSL 驗證
    ssl._create_default_https_context = ssl._create_unverified_context

    for chat_id, feed_url, last_entry in subscriptions:
        try:
            feed = fetch_feed(feed_url)
            
            if feed.bozo:
                logger.error(f"解析 feed 失敗: {feed_url}, 錯誤: {feed.bozo_exception}")
                continue

            if not feed.entries:
                continue

            latest_entry = feed.entries[0]
            latest_entry_id = latest_entry.get('id', latest_entry.get('link', ''))

            if latest_entry_id and latest_entry_id != last_entry:
                # 更新最後一條記錄
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE subscriptions SET last_entry = ? WHERE chat_id = ? AND feed_url = ?',
                                 (latest_entry_id, chat_id, feed_url))
                    conn.commit()

                # 發送更新通知
                title = latest_entry.get('title', '無標題')
                link = latest_entry.get('link', '')
                published = latest_entry.get('published', '未知日期')
                
                # 獲取摘要或內容
                if 'summary' in latest_entry:
                    summary = latest_entry.summary
                elif 'description' in latest_entry:
                    summary = latest_entry.description
                else:
                    summary = ''
                
                # 移除 HTML 標籤
                summary = re.sub(r'<[^>]+>', '', summary)  # 移除所有 HTML 標籤
                summary = summary.replace('\n', ' ').strip()  # 移除換行符
                summary = ' '.join(summary.split())  # 移除多餘的空白
                summary = summary[:500] + '...' if len(summary) > 500 else summary
                
                message = f"📢 <b>{feed.feed.title}</b>\n\n"
                message += f"<b>{title}</b>\n"
                message += f"📅 {published}\n\n"
                message += f"{summary}\n\n"
                message += f"🔗 <a href='{link}'>閱讀更多</a>"
                
                try:
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=telegram.ParseMode.HTML,
                        disable_web_page_preview=False
                    )
                    logger.info(f"已發送更新通知給用戶 {chat_id}")
                except Exception as e:
                    logger.error(f"發送消息失敗: {str(e)}")

        except Exception as e:
            logger.error(f"檢查 feed 時出錯: {str(e)}")

def check_now(update, context):
    """手動檢查特定用戶的 feed"""
    user_id = update.effective_user.id
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT feed_url FROM subscriptions WHERE chat_id = ?', (user_id,))
        user_subscriptions = cursor.fetchall()
    
    if not user_subscriptions:
        update.message.reply_text('您目前沒有任何訂閱。')
        return
    
    update.message.reply_text('正在檢查您的訂閱...')
    
    for feed_url in user_subscriptions:
        try:
            feed = fetch_feed(feed_url[0])
            
            if feed.bozo:
                logger.error(f"解析 feed 失敗: {feed_url[0]}, 錯誤: {feed.bozo_exception}")
                continue

            if not feed.entries:
                continue

            entry = feed.entries[0]
            title = entry.get('title', '無標題')
            link = entry.get('link', '')
            published = entry.get('published', '未知日期')
            
            # 處理摘要或內容
            if 'summary' in entry:
                summary = entry.summary
            elif 'description' in entry:
                summary = entry.description
            else:
                summary = ''
            
            # 清理 HTML 標籤
            summary = re.sub(r'<[^>]+>', '', summary)  # 移除所有 HTML 標籤
            summary = summary.replace('\n', ' ').strip()  # 移除換行符
            summary = ' '.join(summary.split())  # 移除多餘的空白
            summary = summary[:500] + '...' if len(summary) > 500 else summary
            
            # 移除網址
            url_pattern = r'https?://\S+'
            urls = re.findall(url_pattern, summary)
            summary = re.sub(url_pattern, '', summary)
            
            message = f"📢 <b>{feed.feed.title}</b>\n\n"
            message += f"<b>{title}</b>\n"
            message += f"📅 {published}\n\n"
            message += f"{summary}\n\n"
            
            # 如果有網址，單獨顯示
            if urls:
                message += "🔗 相關連結：\n"
                for url in urls:
                    message += f"- {url}\n"
                
                context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=telegram.ParseMode.HTML,
                    disable_web_page_preview=False
                )
        except Exception as e:
            logger.error(f"檢查 feed 時出錯: {str(e)}")
            context.bot.send_message(
                chat_id=user_id,
                text=f"檢查 feed 時出錯: {feed_url[0]}\n錯誤: {str(e)}"
            )
    
    update.message.reply_text('檢查完成。')

def error(update: Update, context: CallbackContext) -> None:
    """處理錯誤"""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    """主程序"""
    logger.info("Bot 啟動中...")
    
    # 初始化資料庫
    init_db()
    
    # 創建 Updater 和 Dispatcher
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # 添加命令處理器
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("showid", show_id))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("list", list_subscriptions))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("check", check_now))

    # 添加錯誤處理器
    dispatcher.add_error_handler(error)

    # 啟動 job queue
    job_queue = updater.job_queue
    job_queue.run_repeating(check_feeds, interval=1200, first=0)  # 每20分鐘檢查一次
    logger.info("已設置定時檢查任務")

    # 開始輪詢
    updater.start_polling()
    logger.info("Bot 已啟動並開始運行")

    # 運行 bot 直到按 Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()