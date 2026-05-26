"""Automated weekly posts around Tuesday 08:30 YouTube live readings.

Two jobs (both BEFORE the live, never after — Yulia 2026-05-26):
  • monday_evening_preview   — Mon 19:00 Kyiv: 'завтра о 8:30' anticipation card
  • tuesday_morning_reminder — Tue 08:00 Kyiv: 'сьогодні о 8:30' final reminder

Both are JobQueue.run_daily with days=(0,) for Monday or (1,) for Tuesday.
Python-telegram-bot day numbering: 0=Mon, 1=Tue, ..., 6=Sun.

Episode catalog is the fixed list of scheduled live streams created on YouTube
(см. memory project_youtube_readings.md). Edit LIVE_EPISODES when you add new
streams after 2026-07-28.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

from . import config, db, visual_kit


log = logging.getLogger(__name__)
TZ = ZoneInfo(config.TIMEZONE)

BOOK_TITLE = "Мистецтво бути в Цей: Час"

# Pre-created scheduled YouTube live streams (see memory: project_youtube_readings.md)
LIVE_EPISODES = [
    {"date": "2026-05-26", "num": 1, "url": "https://youtu.be/MmAtPGzVmNM"},
    {"date": "2026-06-02", "num": 2, "url": "https://youtu.be/leWTbabuWyQ"},
    {"date": "2026-06-09", "num": 3, "url": "https://youtu.be/5FVGd8l1GDQ"},
    {"date": "2026-06-16", "num": 4, "url": "https://youtu.be/WIfKBMGDCmw"},
    {"date": "2026-06-23", "num": 5, "url": "https://youtu.be/S_Q4KPbjXhY"},
    {"date": "2026-06-30", "num": 6, "url": "https://youtu.be/zCzjtGn3eGs"},
    {"date": "2026-07-07", "num": 7, "url": "https://youtu.be/PQ_8psm321s"},
    {"date": "2026-07-14", "num": 8, "url": "https://youtu.be/FoIbV-9rlKY"},
    {"date": "2026-07-21", "num": 9, "url": "https://youtu.be/MAVTaaywnA8"},
    {"date": "2026-07-28", "num": 10, "url": "https://youtu.be/BV_IhsSP_i4"},
]


def _episode_for_today(today: date) -> dict | None:
    """Return the live episode happening today, or None."""
    iso = today.isoformat()
    for ep in LIVE_EPISODES:
        if ep["date"] == iso:
            return ep
    return None


# ---------- Tuesday 08:00 morning reminder ----------

async def tuesday_morning_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a 'live announce' card + schedule for immediate publish.

    publish_due will pick it up within 60s. We don't bypass the 3/day quota —
    if today already has 3 posts, the publisher will mark this as missed and
    notify Yulia.
    """
    now = datetime.now(TZ)
    if now.weekday() != 1:  # 1 = Tuesday in Python's weekday()
        return

    ep = _episode_for_today(now.date())
    if not ep:
        log.info("No live episode today (%s) — skip morning reminder", now.date().isoformat())
        return

    try:
        img_path = visual_kit.render(
            "live_announce",
            {
                "episode_num": ep["num"],
                "book_title": BOOK_TITLE,
                "date_label": "Сьогодні",
                "time_label": "08:30",
            },
            filename_hint=f"live_morning_ep{ep['num']}",
        )
    except Exception as e:
        log.exception("live_announce visual failed: %s", e)
        return

    text = (
        f"Любі, доброго ранку 🌅\n\n"
        f"О 8:30 — жива книга на YouTube.\n"
        f"Сьогодні Зустріч №{ep['num']}: «{BOOK_TITLE}».\n\n"
        f"Читаю по-чесному, без сценарію — між сторінками діляся думками.\n\n"
        f"Постав чашку кави, приєднуйся 🤍"
    )

    pid = db.add_post(
        scheduled_at=now.astimezone(timezone.utc).isoformat(),
        text=text,
        media_type="photo",
        media_path=str(img_path),
        inline_buttons=[{"text": "Дивитись о 8:30 ▶︎", "url": ep["url"]}],
        source="auto_live",
        genre="live_morning_reminder",
        metadata={"episode_num": ep["num"], "url": ep["url"]},
    )
    db.log_event("auto_live_morning_seeded", {"post_id": pid, "episode": ep["num"]})
    log.info("Tuesday morning reminder seeded post #%s for episode %s", pid, ep["num"])


# ---------- Monday 19:00 evening preview (next-day anticipation) ----------

async def monday_evening_preview(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mon 19:00 Kyiv — 'завтра о 8:30' anticipation card for tomorrow's live."""
    now = datetime.now(TZ)
    if now.weekday() != 0:  # 0 = Monday
        return

    tomorrow = now.date() + timedelta(days=1)
    ep = _episode_for_today(tomorrow)
    if not ep:
        log.info("No live episode tomorrow (%s) — skip Monday preview", tomorrow.isoformat())
        return

    try:
        img_path = visual_kit.render(
            "live_announce",
            {
                "episode_num": ep["num"],
                "book_title": BOOK_TITLE,
                "date_label": "Завтра",
                "time_label": "08:30",
            },
            filename_hint=f"live_monday_preview_ep{ep['num']}",
        )
    except Exception as e:
        log.exception("Monday preview visual failed: %s", e)
        return

    text = (
        f"Любі, нагадую — завтра о 8:30 жива книга на YouTube 🤍\n\n"
        f"Зустріч №{ep['num']}: «{BOOK_TITLE}».\n"
        f"Читаю по-чесному, між сторінками діляся думками.\n\n"
        f"Зранку ще нагадаю — тут і кав'ярка готова буде ☕"
    )

    pid = db.add_post(
        scheduled_at=now.astimezone(timezone.utc).isoformat(),
        text=text,
        media_type="photo",
        media_path=str(img_path),
        inline_buttons=[{"text": "Поставити нагадування ▶︎", "url": ep["url"]}],
        source="auto_live",
        genre="live_monday_preview",
        metadata={"episode_num": ep["num"], "url": ep["url"]},
    )
    db.log_event("auto_live_monday_seeded", {"post_id": pid, "episode": ep["num"]})
    log.info("Monday evening preview seeded post #%s for ep %s", pid, ep["num"])
