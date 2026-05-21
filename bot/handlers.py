"""Bot command handlers (DM-only — only the owner uses these)."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from html import escape
from zoneinfo import ZoneInfo

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)


def fmt_local(iso_utc: str) -> str:
    if not iso_utc:
        return "—"
    dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return dt.astimezone(TZ).strftime("%d.%m %H:%M")


def is_owner(update: Update) -> bool:
    """Allow only the owner to control the bot in DM."""
    owner_id = db.get_setting("owner_tg_id")
    if not owner_id:
        # First /start sets owner.
        return True
    return update.effective_user and update.effective_user.id == int(owner_id)


# ---------- /start ----------

MENU_MESSAGE = (
    "📌 YK MEDIA BOT · КОЗАЧКОВА ЮЛІЯ\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "🎯 ЦИКЛ — 3 дні вперед\n"
    "Кожного вс/пн ранку я даю план на 3 дні.\n"
    "Воскресенье — твоя ручна Карта тижня.\n\n"
    "📋 ПЛАН\n"
    "/next3 — наступні 3 дні (головне)\n"
    "/today — сьогодні\n"
    "/tomorrow — завтра\n"
    "/plan — весь горизонт\n"
    "/missed — пропущені (коли Mac був off)\n"
    "/howstats — як надсилати стат каналу\n\n"
    "🎛 НА КОЖНОМУ ПОСТІ КНОПКИ\n"
    "📤 Publish Now · ✏️ Edit Text\n"
    "🖼 Change Image · ⏰ Reschedule · 🗑 Delete\n\n"
    "📊 АНАЛІТИКА\n"
    "/stats — підписники + прогрес\n"
    "/weekly — звіт (авто вс 12:00)\n\n"
    "⏸ КОНТРОЛЬ\n"
    "/pause · /resume · /status\n\n"
    "📐 ПРАВИЛА:\n"
    "✓ Кожен пост — фото АБО інфографіка\n"
    "✓ Фото з Drive не повторюються 180 днів\n"
    "✓ Воскресенье 13:00 — твоя Карта тижня\n"
    "✓ Пропущені пости НЕ публікуються автоматом —\n"
    "  тільки вручну через 📤 Publish Now"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    owner_id = db.get_setting("owner_tg_id")
    user = update.effective_user
    if not owner_id and user:
        db.set_setting("owner_tg_id", user.id)
        db.set_setting("owner_username", user.username or "")
        await update.message.reply_text(f"👋 Привіт, {user.first_name}! Зафіксував тебе як власника.")
        await update.message.reply_text(MENU_MESSAGE)
    elif owner_id and user and user.id == int(owner_id):
        await update.message.reply_text(MENU_MESSAGE)
    else:
        await update.message.reply_text("Цей бот керується тільки власником каналу 🔒")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    await update.message.reply_text(MENU_MESSAGE)


# ---------- /plan ----------

def post_keyboard(post_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📤 Publish Now", callback_data=f"pubnow:{post_id}"),
            ],
            [
                InlineKeyboardButton("✏️ Edit Text", callback_data=f"edit:{post_id}"),
                InlineKeyboardButton("🖼 Change Image", callback_data=f"editimg:{post_id}"),
            ],
            [
                InlineKeyboardButton("⏰ Reschedule", callback_data=f"resched:{post_id}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"del:{post_id}"),
            ],
        ]
    )


async def _show_posts_window(update, start_local, end_local, label: str) -> None:
    """Show posts as they will appear in channel: photo + full caption + buttons."""
    import json
    from . import drive
    start_utc = start_local.astimezone(timezone.utc).isoformat()
    end_utc = end_local.astimezone(timezone.utc).isoformat()
    posts_all = db.list_posts(after=start_utc, before=end_utc, limit=50)
    posts = [p for p in posts_all if p["status"] in ("scheduled", "paused", "published")]
    if not posts:
        await update.message.reply_text(f"📋 {label}: постів немає.")
        return

    await update.message.reply_text(f"📋 {label} ({len(posts)} постів)")

    for p in posts:
        status_emoji = {"scheduled": "🟢", "paused": "🟡", "published": "✅"}.get(p["status"], "❓")
        text_full = p["text"] or ""
        poll_q = p.get("poll_question")
        poll_opts = json.loads(p["poll_options"]) if p["poll_options"] else []
        kb = post_keyboard(p["id"])

        # Header
        header = f"{status_emoji} #{p['id']} · {fmt_local(p['scheduled_at'])} · {p['genre'] or 'general'}"
        await update.message.reply_text(header)

        # Caption = exactly what will be in channel
        caption = text_full

        # Send media as in channel — ALWAYS with photo if available
        try:
            if p["media_file_id"] and not p["media_path"]:
                # Drive photo
                photo_url = drive.drive_download_url(p["media_file_id"])
                await update.message.reply_photo(
                    photo=photo_url, caption=caption or None,
                    reply_markup=kb if not poll_q else None,
                )
            elif p["media_path"]:
                with open(p["media_path"], "rb") as f:
                    await update.message.reply_photo(
                        photo=f, caption=caption or None,
                        reply_markup=kb if not poll_q else None,
                    )
            else:
                # No media — warn (rule: every post must have a visual)
                await update.message.reply_text(
                    f"⚠️ #{p['id']} БЕЗ ВІЗУАЛУ — додати фото або інфографіку через 🖼 Change Image\n\n{caption}",
                    reply_markup=kb,
                )
                continue

            # If post has a poll → send it after the photo
            if poll_q:
                await update.message.reply_poll(question=poll_q, options=poll_opts, is_anonymous=True)
                await update.message.reply_text(f"⤴ Опитування для #{p['id']}", reply_markup=kb)
        except Exception as e:
            await update.message.reply_text(f"❌ #{p['id']} помилка показу: {e}\n\n{caption}", reply_markup=kb)


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plan for next 7 days."""
    if not is_owner(update):
        return
    now = datetime.now(TZ)
    end = now + timedelta(days=7)
    await _show_posts_window(update, now, end, "План на 7 днів")


async def cmd_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plan for tomorrow only — recommended daily check."""
    if not is_owner(update):
        return
    now = datetime.now(TZ)
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)
    label = f"Завтра ({tomorrow_start.strftime('%a %d.%m')})"
    await _show_posts_window(update, tomorrow_start, tomorrow_end, label)


async def cmd_next3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plan for the next 3 days — main planning view per Yulia 2026-05-20."""
    if not is_owner(update):
        return
    now = datetime.now(TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = start + timedelta(days=3)
    label = f"Наступні 3 дні ({start.strftime('%a %d.%m')} — {(end - timedelta(days=1)).strftime('%a %d.%m')})"
    await _show_posts_window(update, start, end, label)


# ---------- /today ----------

async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    now = datetime.now(TZ)
    start_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    await _show_posts_window(update, start_local, end_local, f"Сьогодні ({start_local.strftime('%a %d.%m')})")


# ---------- /preview, /delete, /pause, /resume, /stats ----------

async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update) or not context.args:
        await update.message.reply_text("Використання: /preview <id>")
        return
    try:
        pid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID має бути числом.")
        return
    p = db.get_post(pid)
    if not p:
        await update.message.reply_text(f"Пост #{pid} не знайдено.")
        return
    msg = (
        f"Превʼю #{pid}\n"
        f"📅 {fmt_local(p['scheduled_at'])} · {p['genre']} · {p['media_type']}\n"
        f"🏷 {p['source']} · status: {p['status']}\n\n"
        f"---\n{p['text'] or '(без тексту)'}\n---"
    )
    await update.message.reply_text(msg, reply_markup=post_keyboard(pid))


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update) or not context.args:
        await update.message.reply_text("Використання: /delete <id>")
        return
    pid = int(context.args[0])
    db.delete_post(pid)
    await update.message.reply_text(f"🗑 Пост #{pid} видалено.")


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    db.set_setting("global_pause", True)
    await update.message.reply_text("⏸ <b>ПАУЗА.</b> Бот не публікуватиме нічого, доки ти не /resume.", parse_mode=ParseMode.HTML)


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    db.set_setting("global_pause", False)
    await update.message.reply_text("▶️ Публікації поновлено.")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    try:
        cnt = await context.bot.get_chat_member_count(config.CHANNEL_ID)
        baseline = db.get_setting("baseline_subscribers", 6218)
        delta = cnt - int(baseline)
        goal = config.GOAL_NEW_SUBSCRIBERS
        progress = (delta / goal * 100) if goal else 0
        scheduled = len(db.list_posts(status="scheduled", limit=999))
        days_left = (datetime.fromisoformat(config.GOAL_DEADLINE).date() - datetime.now(TZ).date()).days
        msg = (
            f"📊 Статистика каналу\n\n"
            f"👥 Підписників: {cnt}\n"
            f"📈 З 20.05: +{delta} (мета +{goal})\n"
            f"🎯 Прогрес: {progress:.1f}%\n\n"
            f"📋 Заплановано постів: {scheduled}\n"
            f"📭 До 30.06: {days_left} днів"
        )
    except Exception as e:
        msg = f"⚠️ Помилка: {e}"
    await update.message.reply_text(msg)


# ---------- /status ----------

async def cmd_howstats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show instruction how to take channel statistics screenshot."""
    if not is_owner(update):
        return
    msg = (
        "📊 ЯК ЗРОБИТИ СКРІН СТАТИСТИКИ КАНАЛУ\n\n"
        "Це потрібно раз на тиждень — щоб я бачив перегляди постів і покращував контент.\n\n"
        "━━━ НА ТЕЛЕФОНІ ━━━\n\n"
        "1. Відкрий додаток Telegram\n"
        "2. Зайди в канал «КОЗАЧКОВА ЮЛІЯ»\n"
        "3. Натисни на назву каналу вгорі\n"
        "4. У меню обери «Статистика» (Statistics)\n"
        "5. Прокрути екран — побачиш:\n"
        "   • Зростання підписників\n"
        "   • Перегляди постів\n"
        "   • Графіки активності\n"
        "6. Зроби 2-3 скріни (статистика + список постів з переглядами)\n"
        "7. Надішли всі скріни в цей чат\n\n"
        "━━━ НА КОМПʼЮТЕРІ ━━━\n\n"
        "1. Telegram Desktop\n"
        "2. Канал → ⋮ (три крапки) → Statistics\n"
        "3. Cmd+Shift+4 (Mac) → скрін\n"
        "4. Надішли в цей чат\n\n"
        "━━━ ЩО Я ЗРОБЛЮ ━━━\n\n"
        "✓ Збережу скріни локально з датою\n"
        "✓ Обчислю engagement по жанрах\n"
        "✓ Розрахую які формати заходять найкраще\n"
        "✓ У наступному batch — більше тих що зайшли, менше тих що ні\n\n"
        "📅 НАГАДУВАННЯ: кожне воскресенье 20:00 я нагадаю.\n"
        "Можеш надсилати раніше — я завжди приймаю."
    )
    await update.message.reply_text(msg)


async def cmd_missed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show posts that missed their slot — Yulia decides what to do."""
    if not is_owner(update):
        return
    missed = db.list_posts(status="missed", limit=30)
    if not missed:
        await update.message.reply_text("✅ Пропущених постів немає.")
        return

    await update.message.reply_text(f"⏰ Пропущені пости ({len(missed)}):\nЩо хочеш — опублікувати зараз / перенести / видалити")

    import json
    from . import drive
    for p in missed:
        text_full = p["text"] or (p.get("poll_question") or "(без тексту)")
        try:
            if p["media_file_id"] and not p["media_path"]:
                photo_url = drive.drive_download_url(p["media_file_id"])
                await update.message.reply_photo(photo=photo_url, caption=text_full, reply_markup=post_keyboard(p["id"]))
            elif p["media_path"]:
                with open(p["media_path"], "rb") as f:
                    await update.message.reply_photo(photo=f, caption=text_full, reply_markup=post_keyboard(p["id"]))
            else:
                await update.message.reply_text(f"#{p['id']} · {fmt_local(p['scheduled_at'])}\n\n{text_full}", reply_markup=post_keyboard(p["id"]))
        except Exception as e:
            await update.message.reply_text(f"#{p['id']}: {e}", reply_markup=post_keyboard(p["id"]))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    paused = db.get_setting("global_pause", False)
    photos_url = db.get_setting("photos_drive_url", "")
    msg = (
        f"⚙️ Стан системи\n\n"
        f"🤖 Bot: ✅ онлайн\n"
        f"📋 Pause: {'⏸ так' if paused else '▶️ ні'}\n"
        f"📁 Drive: {'✅' if photos_url else '❌'}"
    )
    await update.message.reply_text(msg)


async def cmd_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update) or not context.args:
        await update.message.reply_text("Використання: /photos <Google Drive URL>")
        return
    url = " ".join(context.args)
    db.set_setting("photos_drive_url", url)
    await update.message.reply_text(f"📁 Google Drive збережено:\n{url}\n\nЯ підтягну фото під час планування постів.")


# ---------- inline callbacks ----------

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    q = update.callback_query
    await q.answer()
    action, _, payload = (q.data or "").partition(":")
    try:
        pid = int(payload)
    except ValueError:
        return

    if action == "pubnow":
        # Publish this post to channel RIGHT NOW (skip the schedule)
        post = db.get_post(pid)
        if not post:
            await q.message.reply_text(f"#{pid} не знайдено.")
            return
        if post["status"] == "published":
            await q.message.reply_text(f"⚠️ #{pid} вже опубліковано.")
            return
        try:
            from .publisher import _publish_one
            await _publish_one(context.bot, post)
            await q.message.reply_text(f"✅ #{pid} опубліковано в канал просто зараз 📤")
        except Exception as e:
            await q.message.reply_text(f"❌ Помилка публікації #{pid}: {e}")
        return

    if action == "del":
        # Get info BEFORE deleting (for replacement)
        old = db.get_post(pid)
        if not old:
            await q.edit_message_text(f"#{pid} не знайдено.")
            return
        db.delete_post(pid)
        await q.edit_message_text(f"🗑 #{pid} видалено. Готую заміну…")

        # Auto-generate replacement on the same time slot
        from . import auto_replacement
        repl = auto_replacement.pick_replacement(
            exclude_text=old.get("text", ""),
            exclude_genre=old.get("genre", ""),
        )
        new_pid = db.add_post(
            scheduled_at=old["scheduled_at"],
            text=repl["text"],
            media_type="photo",
            media_path=auto_replacement.get_visual_path(repl["visual"]),
            source="auto_replacement",
            genre=repl["genre"],
            metadata={"replaces_post_id": pid},
        )
        # Send preview of replacement
        with open(auto_replacement.get_visual_path(repl["visual"]), "rb") as f:
            await q.message.reply_photo(
                photo=f,
                caption=(
                    f"🔄 ЗАМІНА #{pid} → #{new_pid}\n"
                    f"📅 Той же час: {fmt_local(old['scheduled_at'])}\n"
                    f"🎭 Жанр: {repl['genre']}\n\n"
                    f"{repl['text']}"
                ),
                reply_markup=post_keyboard(new_pid),
            )
        return
    elif action == "prev":
        p = db.get_post(pid)
        if not p:
            await q.edit_message_text(f"#{pid} не знайдено.")
            return
        msg = (
            f"Превʼю #{pid}\n"
            f"📅 {fmt_local(p['scheduled_at'])} · {p['genre']} · {p['media_type']}\n\n"
            f"---\n{p['text'] or '(без тексту)'}\n---"
        )
        await q.message.reply_text(msg)
    elif action == "edit":
        context.user_data["editing_post_id"] = pid
        await q.message.reply_text(f"✏️ Надішли новий текст для поста #{pid} наступним повідомленням.")
    elif action == "editimg":
        context.user_data["editing_image_post_id"] = pid
        await q.message.reply_text(
            f"🖼 Надішли нове фото для #{pid}:\n"
            f"• або фотографію (як зображення)\n"
            f"• або посилання на файл у Google Drive\n\n"
            f"Стара картинка буде замінена."
        )
    elif action == "resched":
        context.user_data["rescheduling_post_id"] = pid
        await q.message.reply_text(
            f"⏰ Надішли новий час для #{pid} у форматі: ДД.ММ ГГ:ХВ\n"
            f"Наприклад: 22.05 14:30"
        )


# ---------- generic text handler (edit/reschedule continuation) ----------

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_owner(update):
        return
    msg = update.message
    text = msg.text or ""

    # Forwarded messages → silently store as content material for future posts
    if msg.forward_origin or msg.forward_from or msg.forward_from_chat:
        db.log_event("forward_received", {
            "from": str(getattr(msg.forward_origin, "type", "") or msg.forward_from_chat.title if msg.forward_from_chat else "user"),
            "text_preview": text[:200],
        })
        return  # no reply — Yulia uses forwards to share material

    # Edit text continuation
    pid = context.user_data.pop("editing_post_id", None)
    if pid:
        db.update_post(pid, text=text)
        await msg.reply_text(f"✅ Текст поста #{pid} оновлено.")
        return

    # Reschedule continuation
    pid = context.user_data.pop("rescheduling_post_id", None)
    if pid:
        try:
            now = datetime.now(TZ)
            dt = datetime.strptime(text.strip(), "%d.%m %H:%M").replace(year=now.year, tzinfo=TZ)
            if dt < now:
                dt = dt.replace(year=now.year + 1)
            iso = dt.astimezone(timezone.utc).isoformat()
            db.update_post(pid, scheduled_at=iso, status="scheduled")
            await msg.reply_text(f"✅ #{pid} перенесено на {dt.strftime('%d.%m %H:%M')}.")
        except ValueError:
            await msg.reply_text("❌ Формат невірний. Очікую: ДД.ММ ГГ:ХВ")
        return

    # If user is in "edit image" mode and sends a Drive URL → use as media
    pid_img = context.user_data.pop("editing_image_post_id", None)
    if pid_img and ("drive.google.com" in text.lower()):
        # Extract file_id from common Drive URL forms
        import re
        m = re.search(r"/d/([A-Za-z0-9_-]{20,})", text) or re.search(r"[?&]id=([A-Za-z0-9_-]{20,})", text)
        if m:
            file_id = m.group(1)
            db.update_post(pid_img, media_type="photo", media_file_id=file_id, media_path=None)
            await msg.reply_text(f"✅ Картинку #{pid_img} замінено на нове фото з Drive.")
            return
        else:
            await msg.reply_text("❌ Не зміг розпізнати file_id у посиланні. Скинь повне Drive-посилання вигляду https://drive.google.com/file/d/XXXXX/view")
            context.user_data["editing_image_post_id"] = pid_img  # restore state
            return

    # Detect Google Drive URL → save as photos folder (default behavior)
    lowered = text.lower()
    if "drive.google.com" in lowered or "docs.google.com" in lowered:
        db.set_setting("photos_drive_url", text.strip())
        await msg.reply_text(f"📁 Зафіксував Google Drive як папку з фото:\n{text.strip()}")
        return

    # Otherwise — gentle hint, only short message
    await msg.reply_text("🤖 Команди: /plan /today /stats /help")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Photo received from owner. Routes:
    - 'editing image' mode → attach to post
    - otherwise → save as channel statistics screenshot
    """
    if not is_owner(update):
        return
    msg = update.message
    photo = msg.photo[-1]
    tg_file_id = photo.file_id

    # Mode: editing post image
    pid = context.user_data.pop("editing_image_post_id", None)
    if pid:
        db.update_post(pid, media_type="photo", media_file_id=tg_file_id, media_path=None)
        await msg.reply_text(f"✅ Картинку #{pid} замінено на твоє нове фото.")
        return

    # Otherwise — assume it's a stats screenshot, save it
    import os
    from datetime import datetime
    from . import config
    stats_dir = config.DATA_DIR / "stats_screenshots"
    stats_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file = await msg.photo[-1].get_file()
    out_path = stats_dir / f"stats_{ts}.jpg"
    await file.download_to_drive(str(out_path))

    # Update last stats received
    db.set_setting("last_views_screenshot_at", datetime.now().isoformat())
    count = len(list(stats_dir.glob("stats_*.jpg")))

    caption = (msg.caption or "").strip()
    db.log_event("stats_screenshot_received", {
        "file_id": tg_file_id,
        "path": str(out_path),
        "caption": caption,
    })

    await msg.reply_text(
        f"📊 Скрін статистики збережено\n"
        f"Файл: stats_{ts}.jpg ({count}-й за весь час)\n"
        f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"При наступному відкритті Claude я проаналізую цей скрін і додам дані у engagement-розрахунок.\n\n"
        f"Дякую 🤍"
    )
