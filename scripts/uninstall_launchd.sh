#!/bin/bash
# Stop and remove YK Media Bot launchd service
set -e

PLIST_DST=$HOME/Library/LaunchAgents/com.yk.tgbot.plist

if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST" 2>/dev/null || true
    rm "$PLIST_DST"
    echo "✅ YK Media Bot service removed"
else
    echo "ℹ️  Service not installed"
fi
