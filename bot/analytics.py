"""
Weekly analytics — composes feedback report for Yulia.
Delivered in @YK_Media_Bot DM every Sunday 12:00 + on /weekly demand.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)


def _q(sql: str, args=()):
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, args).fetchall()
    con.close()
    return rows


def _fmt(n: int) -> str:
    return f"+{n}" if n > 0 else str(n)


def compose_weekly_report() -> str:
    """Build the weekly report string."""
    now = datetime.now(TZ)
    week_ago = now - timedelta(days=7)
    week_ago_iso = week_ago.astimezone(timezone.utc).isoformat()
    today_iso = now.astimezone(timezone.utc).isoformat()

    # 1. Subscribers progress
    snapshots = _q("SELECT count, snapshot_at FROM subscribers_snapshot ORDER BY snapshot_at DESC LIMIT 8")
    current = snapshots[0]["count"] if snapshots else None
    week_ago_count = snapshots[-1]["count"] if len(snapshots) >= 7 else (snapshots[0]["count"] if snapshots else None)
    baseline = db.get_setting("baseline_subscribers", 6218)
    goal = config.GOAL_NEW_SUBSCRIBERS
    goal_deadline = config.GOAL_DEADLINE

    # 2. Published this week
    published = _q(
        "SELECT id, genre, scheduled_at, published_at, media_type FROM posts "
        "WHERE status='published' AND published_at >= ? ORDER BY published_at DESC",
        (week_ago_iso,)
    )

    # 3. Reactions (top by reaction count)
    reactions = _q(
        "SELECT post_id, message_id, reaction, count FROM reactions "
        "WHERE snapshot_at >= ? ORDER BY count DESC LIMIT 10",
        (week_ago_iso,)
    )

    # 4. Comments (if bot is in linked group)
    comments = _q(
        "SELECT COUNT(*) AS n, post_message_id FROM comments "
        "WHERE created_at >= ? GROUP BY post_message_id ORDER BY n DESC LIMIT 5",
        (week_ago_iso,)
    )

    # 5. Scheduled for next week
    next_7_days = (now + timedelta(days=7)).astimezone(timezone.utc).isoformat()
    scheduled = _q(
        "SELECT id, genre, scheduled_at FROM posts "
        "WHERE status='scheduled' AND scheduled_at >= ? AND scheduled_at < ?",
        (today_iso, next_7_days)
    )

    # 6. New YouTube videos seen
    new_videos = _q(
        "SELECT title, channel_handle FROM youtube_videos WHERE seen_at >= ? ORDER BY published_at DESC LIMIT 5",
        (week_ago_iso,)
    )

    # 7. Stats screenshots received
    stats_received = db.get_setting("last_views_screenshot_at", None)

    # 8. Missed posts
    missed = _q("SELECT COUNT(*) AS n FROM posts WHERE status='missed'")[0]["n"]

    # ── compose ──
    lines = []
    lines.append(f"📊 ТИЖНЕВИЙ ФІДБЕК · {now.strftime('%d.%m.%Y')}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("")

    # Subscribers
    lines.append("👥 ПІДПИСНИКИ")
    if current:
        delta_baseline = current - int(baseline)
        if week_ago_count:
            delta_week = current - week_ago_count
            lines.append(f"  Зараз: {current}")
            lines.append(f"  За тиждень: {_fmt(delta_week)}")
            lines.append(f"  За весь час: {_fmt(delta_baseline)} (мета +{goal} до {goal_deadline})")
            progress = delta_baseline / goal * 100 if goal else 0
            lines.append(f"  Прогрес: {progress:.1f}%")
        else:
            lines.append(f"  Зараз: {current} (за весь час {_fmt(delta_baseline)})")
    else:
        lines.append("  Даних ще немає (snapshot щодня о 23:55)")
    lines.append("")

    # Posts published
    lines.append(f"📝 ОПУБЛІКОВАНО ({len(published)} постів)")
    if published:
        by_genre = {}
        for p in published:
            by_genre[p["genre"] or "?"] = by_genre.get(p["genre"] or "?", 0) + 1
        for g, n in sorted(by_genre.items(), key=lambda x: -x[1]):
            lines.append(f"  · {g}: {n}")
    else:
        lines.append("  Жодного цього тижня")
    lines.append("")

    # Reactions
    if reactions:
        lines.append("❤️ ТОП РЕАКЦІЇ")
        for r in reactions[:5]:
            lines.append(f"  · пост #{r['post_id']}: {r['reaction']} ×{r['count']}")
        lines.append("")
    else:
        lines.append("❤️ РЕАКЦІЇ — поки 0 даних")
        lines.append("")

    # Comments
    if comments:
        lines.append("💬 КОМЕНТАРІ")
        for c in comments:
            lines.append(f"  · повідомлення {c['post_message_id']}: {c['n']} коментарів")
        lines.append("")
    else:
        lines.append("💬 КОМЕНТАРІ — 0 (бот ще не в linked-group або тиждень тихий)")
        lines.append("")

    # Missed
    if missed:
        lines.append(f"⏰ ПРОПУЩЕНІ: {missed} (натисни /missed)")
        lines.append("")

    # Stats screenshot reminder
    if stats_received:
        try:
            ts = datetime.fromisoformat(stats_received)
            days_since = (datetime.now() - ts.replace(tzinfo=None)).days
            lines.append(f"📷 Останній скрін стат каналу: {days_since} дн тому")
        except Exception:
            pass
    else:
        lines.append("📷 Скрін стат каналу — ще НЕ отримав. /howstats")
    lines.append("")

    # YouTube new
    if new_videos:
        lines.append(f"🎬 НОВІ ВІДЕО НА YOUTUBE ({len(new_videos)})")
        for v in new_videos:
            lines.append(f"  · [{v['channel_handle']}] {v['title'][:50]}")
        lines.append("")

    # Next week schedule
    lines.append(f"📅 ЗАПЛАНОВАНО НА НАСТУПНИЙ ТИЖДЕНЬ: {len(scheduled)} постів")
    lines.append("")

    # Summary recommendation
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 Що я бачу:")
    if not reactions and not comments:
        lines.append("  • Engagement даних поки замало для глибокого аналізу")
        lines.append("  • Через 1-2 тижні матиму базу для оптимізації жанрів")
    elif reactions:
        # Find which genre got most reactions
        top_post = reactions[0]
        top_post_data = _q("SELECT genre FROM posts WHERE id=?", (top_post["post_id"],))
        if top_post_data:
            lines.append(f"  • Найбільше реакцій зібрав жанр: {top_post_data[0]['genre']}")
            lines.append(f"  • Це сигнал — додам більше таких у наступному batch")
    lines.append("")
    lines.append("Скинь скрін стат каналу — буду розраховувати найповніше")

    return "\n".join(lines)
