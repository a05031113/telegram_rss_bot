#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python telegram_rss_bot.py 
launchctl unload ~/Library/LaunchAgents/com.telegram.rssbot.plist
launchctl load ~/Library/LaunchAgents/com.telegram.rssbot.plist 