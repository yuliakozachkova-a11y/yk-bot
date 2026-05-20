#!/bin/bash
# Install YK Media Bot as a launchd user agent (auto-start on login, keeps running 24/7)
set -e

PROJECT=/Users/yuliia/yk-bot
PLIST_SRC=$PROJECT/launchd/com.yk.tgbot.plist
PLIST_DST=$HOME/Library/LaunchAgents/com.yk.tgbot.plist

echo "📦 Installing YK Media Bot launchd service..."

cp "$PLIST_SRC" "$PLIST_DST"
echo "  ✓ Copied to $PLIST_DST"

launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "  ✓ Service loaded"

sleep 2

if launchctl list | grep -q com.yk.tgbot; then
    echo "✅ YK Media Bot is running as launchd service"
    echo ""
    echo "Useful commands:"
    echo "  launchctl list | grep yk           # check status"
    echo "  tail -f $PROJECT/logs/bot.log      # live logs"
    echo "  launchctl unload $PLIST_DST        # stop"
    echo "  launchctl load $PLIST_DST          # start"
else
    echo "❌ Service not running. Check logs at $PROJECT/logs/launchd.err.log"
    exit 1
fi
