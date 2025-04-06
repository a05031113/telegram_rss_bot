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

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 資料庫設定
DB_FILE = 'rss_bot.db'

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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feed_url TEXT NOT NULL,
            feed_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, feed_url)
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

def get_user_subscriptions(user_id):
    """獲取用戶的訂閱列表"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT feed_url, feed_title FROM subscriptions WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

def add_subscription(user_id, feed_url, feed_title):
    """添加新的訂閱"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO subscriptions (user_id, feed_url, feed_title) VALUES (?, ?, ?)',
                (user_id, feed_url, feed_title)
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
            'DELETE FROM subscriptions WHERE user_id = ? AND feed_url = ?',
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

def start(update, context):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(
        f'Hi {user.first_name}! I can help you track RSS feeds.\n\n'
        'Commands:\n'
        '/subscribe <url> - Subscribe to an RSS feed\n'
        '/list - List all your subscriptions\n'
        '/unsubscribe <number> - Unsubscribe from a feed\n'
        '/check - Check for new posts now'
    )

def subscribe(update, context):
    """Subscribe to an RSS feed."""
    if not context.args:
        update.message.reply_text('請提供 RSS feed 的 URL：/subscribe <url>')
        return

    feed_url = context.args[0]
    user_id = update.effective_user.id
    
    try:
        logger.info(f"嘗試解析 feed: {feed_url}")
        feed = fetch_feed(feed_url)
        
        if feed.bozo:
            error_msg = f"Feed 解析錯誤: {feed.bozo_exception}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        if not hasattr(feed, 'feed') or not hasattr(feed.feed, 'title'):
            error_msg = "Feed 格式不正確：缺少必要的 feed 資訊"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Store feed title for later reference
        feed_title = feed.feed.title
        logger.info(f"成功解析 feed: {feed_title}")
        
        # Add subscription to database
        if add_subscription(user_id, feed_url, feed_title):
            # Initialize the tracking of last entries for this feed
            feed_hash = hashlib.md5(feed_url.encode()).hexdigest()
            if feed.entries:
                last_entry_id = feed.entries[0].get('id', feed.entries[0].get('link', ''))
                update_last_entry(feed_hash, last_entry_id)
            
            update.message.reply_text(f'成功訂閱：{feed_title}')
        else:
            update.message.reply_text(f'您已經訂閱了這個 feed。')
            
    except Exception as e:
        logger.error(f"訂閱 feed 時發生錯誤: {str(e)}")
        update.message.reply_text(f'訂閱 feed 時發生錯誤：{str(e)}\n請確認 URL 是否為有效的 RSS feed。')

def list_subscriptions(update, context):
    """List all subscribed feeds."""
    user_id = update.effective_user.id
    subscriptions = get_user_subscriptions(user_id)
    
    if not subscriptions:
        update.message.reply_text('您目前沒有任何訂閱。')
        return
    
    message = '您的訂閱列表：\n\n'
    for i, (feed_url, feed_title) in enumerate(subscriptions, 1):
        message += f'{i}. {feed_title or "未知標題"}\n{feed_url}\n\n'
    
    update.message.reply_text(message)

def unsubscribe(update, context):
    """Unsubscribe from a feed by index number."""
    if not context.args:
        update.message.reply_text('請提供要取消訂閱的 feed 編號：/unsubscribe <編號>')
        return
    
    try:
        index = int(context.args[0]) - 1
        user_id = update.effective_user.id
        subscriptions = get_user_subscriptions(user_id)
        
        if not subscriptions:
            update.message.reply_text('您目前沒有任何訂閱。')
            return
        
        if index < 0 or index >= len(subscriptions):
            update.message.reply_text('無效的訂閱編號。使用 /list 查看您的訂閱列表。')
            return
        
        feed_url = subscriptions[index][0]
        if remove_subscription(user_id, feed_url):
            update.message.reply_text(f'已取消訂閱：{subscriptions[index][1] or feed_url}')
        else:
            update.message.reply_text('取消訂閱失敗，請稍後再試。')
    except ValueError:
        update.message.reply_text('請提供有效的編號：/unsubscribe <編號>')

def check_feeds(context: CallbackContext):
    """Check all feeds for updates and notify users."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT feed_url FROM subscriptions')
        all_feeds = cursor.fetchall()
        
        for (feed_url,) in all_feeds:
            try:
                feed = fetch_feed(feed_url)
                feed_hash = hashlib.md5(feed_url.encode()).hexdigest()
                
                # Get the last processed entry for this feed
                last_entry_id = get_last_entry(feed_hash)
                
                if not last_entry_id and feed.entries:
                    # First time checking this feed
                    last_entry_id = feed.entries[0].get('id', feed.entries[0].get('link', ''))
                    update_last_entry(feed_hash, last_entry_id)
                    continue
                
                # Find new entries
                new_entries = []
                for entry in feed.entries:
                    entry_id = entry.get('id', entry.get('link', ''))
                    if entry_id == last_entry_id:
                        break
                    new_entries.append(entry)
                
                # Update the last entry ID if we have new entries
                if new_entries and feed.entries:
                    update_last_entry(feed_hash, feed.entries[0].get('id', feed.entries[0].get('link', '')))
                
                # Get all users subscribed to this feed
                cursor.execute('SELECT user_id FROM subscriptions WHERE feed_url = ?', (feed_url,))
                subscribers = cursor.fetchall()
                
                # Send updates to all subscribers
                for entry in reversed(new_entries):
                    title = entry.get('title', 'No title')
                    link = entry.get('link', '')
                    published = entry.get('published', 'Unknown date')
                    
                    if 'summary' in entry:
                        summary = entry.summary
                    elif 'description' in entry:
                        summary = entry.description
                    else:
                        summary = ''
                    
                    summary = summary.replace('<p>', '').replace('</p>', '\n\n')
                    summary = summary[:200] + '...' if len(summary) > 200 else summary
                    
                    message = f"<b>{feed.feed.title}</b>\n\n"
                    message += f"<b>{title}</b>\n"
                    message += f"{published}\n\n"
                    message += f"{summary}\n\n"
                    message += f"<a href='{link}'>閱讀更多</a>"
                    
                    for (user_id,) in subscribers:
                        try:
                            context.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode=telegram.ParseMode.HTML,
                                disable_web_page_preview=False
                            )
                        except Exception as e:
                            logger.error(f"發送更新給用戶 {user_id} 時發生錯誤: {e}")
                            
            except Exception as e:
                logger.error(f"檢查 feed {feed_url} 時發生錯誤: {e}")

def check_now(update, context):
    """Manually check feeds for a specific user."""
    user_id = update.effective_user.id
    
    if user_id not in subscriptions or not subscriptions[user_id]:
        update.message.reply_text('You have no active subscriptions to check.')
        return
    
    update.message.reply_text('Checking your feeds...')
    
    # Create a temporary context just for this user
    temp_context = {'user_id': user_id}
    
    # Call the check_feeds function for just this user
    for feed_url in subscriptions[user_id]:
        try:
            feed = feedparser.parse(feed_url)
            feed_hash = hashlib.md5(feed_url.encode()).hexdigest()
            
            # If there are entries, send the latest one
            if feed.entries:
                entry = feed.entries[0]
                title = entry.get('title', 'No title')
                link = entry.get('link', '')
                published = entry.get('published', 'Unknown date')
                
                # Try to get a summary or content
                if 'summary' in entry:
                    summary = entry.summary
                elif 'description' in entry:
                    summary = entry.description
                else:
                    summary = ''
                
                # Remove HTML tags from summary (very basic approach)
                summary = summary.replace('<p>', '').replace('</p>', '\n\n')
                summary = summary[:200] + '...' if len(summary) > 200 else summary
                
                message = f"<b>{feed.feed.title}</b>\n\n"
                message += f"<b>{title}</b>\n"
                message += f"{published}\n\n"
                message += f"{summary}\n\n"
                message += f"<a href='{link}'>Read more</a>"
                
                context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=telegram.ParseMode.HTML,
                    disable_web_page_preview=False
                )
        except Exception as e:
            logger.error(f"Error checking feed {feed_url}: {e}")
            context.bot.send_message(
                chat_id=user_id,
                text=f"Error checking feed: {feed_url}\nError: {str(e)}"
            )
    
    update.message.reply_text('Feed check completed.')

def error(update, context):
    """Log errors caused by updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Get the API token from environment variables
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        logger.error("在環境變數中找不到 TELEGRAM_TOKEN！")
        return
    
    # Create the Updater and pass it your bot's token
    updater = Updater(token)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("list", list_subscriptions))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dp.add_handler(CommandHandler("check", check_now))
    
    # Register error handler
    dp.add_error_handler(error)
    
    # Start the scheduled job to check feeds every 15 minutes
    job_queue = updater.job_queue
    job_queue.run_repeating(check_feeds, interval=15*60, first=0)
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot 已啟動")
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()