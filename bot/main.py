"""Entry point: starts the bot polling + schedules jobs."""
from __future__ import annotations

import logging
import os
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import config, db
from .handlers import (
    cmd_delete,
    cmd_help,
    cmd_howstats,
    cmd_missed,
    cmd_next3,
    cmd_pause,
    cmd_photos,
    cmd_plan,
    cmd_preview,
    cmd_resume,
    cmd_start,
    cmd_stats,
    cmd_status,
    cmd_today,
    cmd_tomorrow,
    cmd_weekly,
    on_callback,
    on_photo,
    on_text,
)
from .publisher import publish_due, snapshot_subscribers, sunday_stats_reminder, weekly_report_job
from .youtube_watcher import poll_all_channels

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("yk_bot")


async def youtube_poll_job(context):
    res = await poll_all_channels()
    log.info("youtube poll: %s", res)


def build_app() -> Application:
    db.init_db()

    # Cloud-safe startup: ensure visuals + schema exist (idempotent)
    try:
        import subprocess
        subprocess.run(
            ["python3", str(Path(__file__).resolve().parent.parent / "scripts" / "startup_check.py")],
            check=False,
        )
    except Exception as e:
        log.warning("startup_check failed (non-fatal): %s", e)

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("tomorrow", cmd_tomorrow))
    app.add_handler(CommandHandler("next3", cmd_next3))
    app.add_handler(CommandHandler("preview", cmd_preview))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("missed", cmd_missed))
    app.add_handler(CommandHandler("howstats", cmd_howstats))
    app.add_handler(CommandHandler("weekly", cmd_weekly))
    app.add_handler(CommandHandler("photos", cmd_photos))

    # Inline buttons
    app.add_handler(CallbackQueryHandler(on_callback))

    # Free text (edit/reschedule/drive-url continuation)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    # Photo messages (for 'change image' workflow)
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))

    # JobQueue
    tz = ZoneInfo(config.TIMEZONE)
    if app.job_queue:
        # Publish due posts every 60 seconds
        app.job_queue.run_repeating(publish_due, interval=60, first=5)

        # YouTube watcher every 30 minutes
        app.job_queue.run_repeating(youtube_poll_job, interval=1800, first=30)

        # Daily subscribers snapshot — at 23:55 Kyiv time
        app.job_queue.run_daily(snapshot_subscribers, time(hour=23, minute=55, tzinfo=tz))

        # Sunday 12:00 Kyiv — weekly feedback report (auto)
        app.job_queue.run_daily(
            weekly_report_job,
            time(hour=12, minute=0, tzinfo=tz),
            days=(6,),
        )

        # Sunday 20:00 Kyiv — ping Yulia to send channel stats screenshot
        app.job_queue.run_daily(
            sunday_stats_reminder,
            time(hour=20, minute=0, tzinfo=tz),
            days=(6,),  # 6 = Sunday in python-telegram-bot's day numbering
        )

    return app


def main() -> None:
    """
    Run bot with failover-aware polling.

    Architecture (Yulia 2026-05-21):
    - Mac (launchd) is PRIMARY — always runs when Mac is on
    - Cloud (Render) is BACKUP — takes over when Mac is off
    - Coordination via native Telegram Conflict (409) mechanism:
      only one client can poll a bot token; the other gets 409 → sleeps.
    """
    import asyncio
    from telegram.error import Conflict

    role = os.environ.get("BOT_ROLE", "primary")  # 'primary' (Mac) or 'backup' (Cloud)
    log.info(f"YK Media Bot starting in role: {role}")

    while True:
        try:
            app = build_app()
            log.info("Polling started")
            app.run_polling(allowed_updates=["message", "callback_query", "message_reaction", "message_reaction_count"])
            break  # graceful shutdown
        except Conflict as e:
            wait = 120 if role == "backup" else 30
            log.warning(f"Conflict (another bot polling). Sleeping {wait}s. Role={role}")
            import time
            time.sleep(wait)
        except KeyboardInterrupt:
            log.info("Interrupted, exiting.")
            break
        except Exception as e:
            log.exception(f"Unexpected error: {e}. Restarting in 30s.")
            import time
            time.sleep(30)


if __name__ == "__main__":
    main()
