#!/bin/bash
# Reliable launcher used by launchd (com.yk.tgbot). Guarantees venv is active
# before exec'ing bot.main — eliminates intermittent "ModuleNotFoundError: dotenv"
# we saw when launchd or caffeinate bypassed venv activation.

set -e
cd /Users/yuliia/yk-bot
# shellcheck source=/dev/null
source venv/bin/activate
exec python -m bot.main
