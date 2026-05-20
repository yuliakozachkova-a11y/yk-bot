"""Centralized config loaded from .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "YK_Media_Bot")
BOT_ID = int(os.environ["TELEGRAM_BOT_ID"])

CHANNEL_ID = int(os.environ["TELEGRAM_CHANNEL_ID"])
CHANNEL_TITLE = os.environ.get("TELEGRAM_CHANNEL_TITLE", "КОЗАЧКОВА ЮЛІЯ")

# Юля — только она пишет боту и получает отчёты.
# При первом /start пользовательский ID сохраняется автоматически в settings table.
OWNER_TG_ID = int(os.environ.get("OWNER_TG_ID", 0)) or None

DB_PATH = ROOT / "data" / "posts.db"
DATA_DIR = ROOT / "data"
PHOTOS_DIR = ROOT / "photos"
LOGS_DIR = ROOT / "logs"

for p in (DATA_DIR, PHOTOS_DIR, LOGS_DIR):
    p.mkdir(exist_ok=True)

# YouTube channels to watch (RSS)
YOUTUBE_CHANNELS = [
    {"handle": "@kozachkova.yuliia", "label": "Основний канал"},
    {"handle": "@lyusterko", "label": "Люстерко"},
]

# Timezone for scheduling
TIMEZONE = "Europe/Kyiv"

# Default time slots for daily posts
DAILY_SLOTS = {
    "morning": "09:30",   # fraza dnya (only after 2026-06-11)
    "noon": "13:00",      # польза / YouTube digest / памятка
    "evening": "17:30",   # продукт / эмоция / интерактив
}

# Project dates
FRAZA_HANDOVER_DATE = "2026-06-12"  # с этой даты бот сам генерит fraza dnya
GOAL_DEADLINE = "2026-06-30"
GOAL_NEW_SUBSCRIBERS = 500
