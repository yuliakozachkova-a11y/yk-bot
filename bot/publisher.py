"""Publishes scheduled posts to the channel by JobQueue every minute."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import config, db, drive


def _resolve_media(media_file_id: str | None, media_path: str | None) -> str | object | None:
    """
    Resolve a media reference to what Telegram bot.send_photo() expects:
    - Telegram file_id (starts with AgAC… or similar Base64) → return as is
    - Google Drive file_id (alphanumeric + -_ , 25-44 chars) → convert to direct download URL
    - Local path → open file
    """
    if media_file_id:
        # Telegram file_ids are long Base64-like strings; Drive IDs are shorter alphanumeric
        if media_file_id.startswith("AgAC") or len(media_file_id) > 50:
            return media_file_id  # Telegram file_id
        # Heuristic: Drive ID
        return drive.drive_download_url(media_file_id)
    if media_path:
        return open(media_path, "rb")
    return None

log = logging.getLogger(__name__)


def _build_markup(post: dict) -> InlineKeyboardMarkup | None:
    btns = post.get("inline_buttons")
    if not btns:
        return None
    try:
        parsed = json.loads(btns) if isinstance(btns, str) else btns
        rows = [[InlineKeyboardButton(b["text"], url=b["url"]) for b in parsed]]
        return InlineKeyboardMarkup(rows)
    except Exception:
        return None


async def publish_due(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback — runs every minute.

    1. Publishes posts whose scheduled_at is within the last GRACE_WINDOW_MIN (=30 min).
    2. Marks anything older as 'missed' → Yulia decides what to do (publish now / reschedule / delete).
    """
    if db.get_setting("global_pause", False):
        return

    bot = context.bot
    owner_id_raw = db.get_setting("owner_tg_id")
    owner_id = int(owner_id_raw) if owner_id_raw else None

    # 1. Handle overdue posts (Mac was off) — mark as 'missed', notify Yulia ONCE
    overdue = db.overdue_posts(limit=20)
    if overdue:
        # Mark each as missed
        for p in overdue:
            db.mark_missed(p["id"])
        # Notify owner with summary (so she doesn't get spam — one notification for batch)
        if owner_id:
            try:
                from .handlers import fmt_local
                lines = ["⏰ ПРОПУЩЕНІ ПОСТИ (Mac був вимкнений)\n"]
                for p in overdue:
                    lines.append(f"  #{p['id']} · {fmt_local(p['scheduled_at'])} · {p['genre']}")
                lines.append("\nВони НЕ опубліковані автоматично.")
                lines.append("Щоб опублікувати — /missed → 📤 Publish Now на кожному.")
                lines.append("Або /next3 → знайди ці пости та зміни час.")
                await bot.send_message(owner_id, "\n".join(lines))
            except Exception:
                log.exception("notify-missed failed")

    # 2. Publish posts within grace window (normal flow)
    due = db.due_posts(limit=3)
    if not due:
        return

    for post in due:
        try:
            await _publish_one(bot, post)
        except Exception as e:
            log.exception("publish failed for post %s", post["id"])
            db.mark_failed(post["id"], str(e))
            if owner_id:
                await bot.send_message(owner_id, f"⚠️ Не вдалося опублікувати #{post['id']}: {e}")


async def _publish_one(bot, post: dict) -> None:
    text = post["text"] or ""
    media_type = post["media_type"]
    media_path = post["media_path"]
    media_file_id = post["media_file_id"]
    markup = _build_markup(post)
    has_media = media_type in ("photo", "video") and (media_file_id or media_path)
    has_poll = bool(post.get("poll_question"))

    sent = None  # last sent message — for marking published

    # 1) Photo (or video) FIRST — if there is media
    if has_media:
        # CRITICAL: never reuse a Drive photo within 180 days
        if media_file_id and not (media_file_id.startswith("AgAC") or len(media_file_id) > 50):
            drive.mark_photo_used(media_file_id, post["id"])

        media = _resolve_media(media_file_id, media_path)
        if media_type == "photo":
            sent = await bot.send_photo(
                chat_id=config.CHANNEL_ID,
                photo=media,
                caption=(text if not has_poll else None) or None,  # if poll → text goes with poll question, not caption
                reply_markup=markup if not has_poll else None,
            )
        else:  # video
            sent = await bot.send_video(
                chat_id=config.CHANNEL_ID,
                video=media,
                caption=(text if not has_poll else None) or None,
                reply_markup=markup if not has_poll else None,
            )

    # 2) Poll AFTER media (if both present) — or as primary if no media
    if has_poll:
        opts = json.loads(post["poll_options"]) if post["poll_options"] else []
        sent = await bot.send_poll(
            chat_id=config.CHANNEL_ID,
            question=post["poll_question"],
            options=opts,
            is_anonymous=True,
        )

    # 3) Plain text — only if no media AND no poll
    if not has_media and not has_poll:
        sent = await bot.send_message(
            chat_id=config.CHANNEL_ID,
            text=text,
            reply_markup=markup,
            disable_web_page_preview=False,
        )

    if sent:
        db.mark_published(post["id"], sent.message_id)
        db.log_event("published", {"post_id": post["id"], "message_id": sent.message_id})


async def snapshot_subscribers(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily snapshot of subscriber count."""
    try:
        cnt = await context.bot.get_chat_member_count(config.CHANNEL_ID)
        db.snapshot_subscribers(cnt)
        log.info("subscribers snapshot: %d", cnt)
    except Exception as e:
        log.exception("snapshot failed")
        db.log_event("snapshot_failed", str(e))


async def sunday_stats_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Every Sunday 20:00 Kyiv — remind Yulia to send channel stats screenshot."""
    owner_id_raw = db.get_setting("owner_tg_id")
    if not owner_id_raw:
        return
    try:
        await context.bot.send_message(
            int(owner_id_raw),
            "📊 НЕДІЛЬНЕ НАГАДУВАННЯ — статистика каналу\n\n"
            "Скинь мені скрін статистики каналу за цей тиждень. Це дасть мені перегляди постів, які я не бачу через Bot API.\n\n"
            "━━━ ШВИДКА ІНСТРУКЦІЯ ━━━\n"
            "1. Telegram → канал «КОЗАЧКОВА ЮЛІЯ» → назва каналу вгорі → «Статистика»\n"
            "2. Скрін(и) екрану (Cmd+Shift+4 на Mac, скрін на телефоні)\n"
            "3. Надішли всі скріни в цей чат\n\n"
            "Потрібно: ~2 хв твого часу.\n"
            "Я збережу скріни → проаналізую → у наступному batch постів врахую що зайшло, а що ні.\n\n"
            "Повна інструкція: /howstats"
        )
    except Exception as e:
        log.exception("sunday_stats_reminder failed: %s", e)
