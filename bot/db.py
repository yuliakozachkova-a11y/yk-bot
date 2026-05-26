"""SQLite storage for post schedule, metrics, settings."""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_at TEXT NOT NULL,       -- ISO8601 UTC
    text TEXT,
    media_type TEXT,                  -- photo|video|none
    media_file_id TEXT,
    media_path TEXT,
    poll_question TEXT,
    poll_options TEXT,                -- JSON list
    inline_buttons TEXT,              -- JSON [{text,url}]
    status TEXT DEFAULT 'scheduled',  -- scheduled|paused|published|failed|deleted
    published_at TEXT,
    published_message_id INTEGER,
    source TEXT,                      -- manual|youtube|fraza|generated
    genre TEXT,                       -- fraza|youtube_anonce|cheklist|product|personal|...
    metadata TEXT,                    -- JSON
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_posts_scheduled ON posts(scheduled_at, status);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);

CREATE TABLE IF NOT EXISTS reactions (
    post_id INTEGER,
    message_id INTEGER,
    reaction TEXT,
    count INTEGER,
    snapshot_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (message_id, reaction, snapshot_at)
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_message_id INTEGER,
    user_id INTEGER,
    user_name TEXT,
    text TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subscribers_snapshot (
    snapshot_at TEXT DEFAULT (datetime('now')),
    count INTEGER,
    PRIMARY KEY (snapshot_at)
);

CREATE TABLE IF NOT EXISTS youtube_videos (
    video_id TEXT PRIMARY KEY,
    channel_handle TEXT,
    title TEXT,
    description TEXT,
    published_at TEXT,
    url TEXT,
    thumbnail_url TEXT,
    processed INTEGER DEFAULT 0,
    seen_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS channel_activity (
    message_id INTEGER PRIMARY KEY,
    source TEXT,                       -- 'bot' | 'manual'
    author_name TEXT,                  -- channel signature, if available
    text_preview TEXT,                 -- first 80 chars
    has_media INTEGER DEFAULT 0,
    posted_at TEXT DEFAULT (datetime('now'))  -- UTC
);
CREATE INDEX IF NOT EXISTS idx_channel_activity_posted ON channel_activity(posted_at);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT,                         -- 'text' | 'voice' | 'photo' | 'forward'
    branch TEXT DEFAULT 'inbox',       -- 'planning' | 'ideas' | 'comms' | 'stats' | 'settings' | 'inbox'
    content TEXT,                      -- text content OR file path for voice/photo
    transcript TEXT,                   -- voice transcript (filled later)
    tags TEXT,                         -- JSON array of tags (optional)
    used_in_post_id INTEGER,           -- if used in a published post — link
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_notes_unused ON notes(used_in_post_id);
"""

# Hard quota: max posts per Kyiv day across bot + manual.
DAILY_POST_QUOTA = 3


def init_db() -> None:
    with sqlite3.connect(config.DB_PATH) as conn:
        conn.executescript(SCHEMA)
        # Lightweight migrations for older DBs that don't have the new columns
        for table, col, definition in (
            ("notes", "branch", "TEXT DEFAULT 'inbox'"),
        ):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists
        # Indexes that depend on migrated columns
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_branch ON notes(branch)")
        except sqlite3.OperationalError:
            pass
        conn.commit()


@contextmanager
def cursor():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


# ---------- Settings ----------

def get_setting(key: str, default: Any = None) -> Any:
    with cursor() as cur:
        row = cur.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]


def set_setting(key: str, value: Any) -> None:
    payload = json.dumps(value) if not isinstance(value, str) else value
    with cursor() as cur:
        cur.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')",
            (key, payload),
        )


# ---------- Posts ----------

def add_post(
    scheduled_at: str,
    text: str = "",
    media_type: str = "none",
    media_file_id: str | None = None,
    media_path: str | None = None,
    poll_question: str | None = None,
    poll_options: list | None = None,
    inline_buttons: list | None = None,
    source: str = "manual",
    genre: str = "general",
    metadata: dict | None = None,
) -> int:
    with cursor() as cur:
        cur.execute(
            """INSERT INTO posts (scheduled_at, text, media_type, media_file_id, media_path,
                                  poll_question, poll_options, inline_buttons, source, genre, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scheduled_at,
                text,
                media_type,
                media_file_id,
                media_path,
                poll_question,
                json.dumps(poll_options) if poll_options else None,
                json.dumps(inline_buttons) if inline_buttons else None,
                source,
                genre,
                json.dumps(metadata) if metadata else None,
            ),
        )
        return cur.lastrowid


def get_post(post_id: int) -> dict | None:
    with cursor() as cur:
        row = cur.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        return dict(row) if row else None


def list_posts(
    status: str | None = None,
    after: str | None = None,
    before: str | None = None,
    limit: int = 30,
) -> list[dict]:
    sql = "SELECT * FROM posts WHERE 1=1"
    args: list = []
    if status:
        sql += " AND status=?"
        args.append(status)
    if after:
        sql += " AND scheduled_at >= ?"
        args.append(after)
    if before:
        sql += " AND scheduled_at < ?"
        args.append(before)
    sql += " ORDER BY scheduled_at ASC LIMIT ?"
    args.append(limit)
    with cursor() as cur:
        return [dict(r) for r in cur.execute(sql, args).fetchall()]


def due_posts(now_utc_iso: str | None = None, limit: int = 5) -> list[dict]:
    """Posts that should have been published by now and are still scheduled.

    Rule: post is published only if scheduled_at was within the last GRACE_WINDOW_MIN
    minutes. Older posts are NOT auto-published — they should be marked 'missed' by the caller.
    """
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc)
    now_utc_iso = now_utc_iso or now_dt.isoformat()
    GRACE_WINDOW_MIN = 30
    earliest = (now_dt - timedelta(minutes=GRACE_WINDOW_MIN)).isoformat()
    with cursor() as cur:
        return [
            dict(r)
            for r in cur.execute(
                "SELECT * FROM posts WHERE status='scheduled' "
                "AND scheduled_at > ? AND scheduled_at <= ? "
                "ORDER BY scheduled_at ASC LIMIT ?",
                (earliest, now_utc_iso, limit),
            ).fetchall()
        ]


def overdue_posts(limit: int = 50) -> list[dict]:
    """Posts that missed their slot (Mac was off): scheduled_at > GRACE_WINDOW_MIN ago, still 'scheduled'.

    These are NOT published automatically — Yulia must publish manually via 📤 Publish Now
    or reschedule them.
    """
    from datetime import timedelta
    now_dt = datetime.now(timezone.utc)
    GRACE_WINDOW_MIN = 30
    cutoff = (now_dt - timedelta(minutes=GRACE_WINDOW_MIN)).isoformat()
    with cursor() as cur:
        return [
            dict(r)
            for r in cur.execute(
                "SELECT * FROM posts WHERE status='scheduled' AND scheduled_at <= ? "
                "ORDER BY scheduled_at ASC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        ]


def mark_missed(post_id: int) -> None:
    """Mark a post as missed (was not published due to system being down)."""
    update_post(post_id, status="missed")


def update_post(post_id: int, **fields) -> None:
    if not fields:
        return
    set_clauses = ", ".join(f"{k}=?" for k in fields) + ", updated_at=datetime('now')"
    args = list(fields.values()) + [post_id]
    with cursor() as cur:
        cur.execute(f"UPDATE posts SET {set_clauses} WHERE id=?", args)


def mark_published(post_id: int, message_id: int) -> None:
    update_post(
        post_id,
        status="published",
        published_at=datetime.now(timezone.utc).isoformat(),
        published_message_id=message_id,
    )


def mark_failed(post_id: int, error: str) -> None:
    update_post(post_id, status="failed", metadata=json.dumps({"error": error}))


def delete_post(post_id: int) -> None:
    update_post(post_id, status="deleted")


def pause_post(post_id: int) -> None:
    update_post(post_id, status="paused")


def resume_post(post_id: int) -> None:
    update_post(post_id, status="scheduled")


# ---------- Metrics ----------

def snapshot_subscribers(count: int) -> None:
    with cursor() as cur:
        cur.execute("INSERT OR REPLACE INTO subscribers_snapshot(count) VALUES (?)", (count,))


def record_reaction(message_id: int, reaction: str, count: int, post_id: int | None = None) -> None:
    with cursor() as cur:
        cur.execute(
            "INSERT OR REPLACE INTO reactions(post_id, message_id, reaction, count) VALUES (?, ?, ?, ?)",
            (post_id, message_id, reaction, count),
        )


def add_comment(post_message_id: int, user_id: int, user_name: str, text: str) -> None:
    with cursor() as cur:
        cur.execute(
            "INSERT INTO comments(post_message_id, user_id, user_name, text) VALUES (?, ?, ?, ?)",
            (post_message_id, user_id, user_name, text),
        )


def add_note(kind: str, content: str, branch: str = "inbox", tags: list | None = None) -> int:
    """Store a note/thought from Yulia. Returns new note id."""
    with cursor() as cur:
        cur.execute(
            "INSERT INTO notes(kind, branch, content, tags) VALUES (?, ?, ?, ?)",
            (kind, branch, content, json.dumps(tags) if tags else None),
        )
        return cur.lastrowid


def list_notes(limit: int = 20, only_unused: bool = False, branch: str | None = None) -> list[dict]:
    """List recent notes, newest first. Filter by branch if specified."""
    sql = "SELECT * FROM notes"
    where = []
    params: list = []
    if only_unused:
        where.append("used_in_post_id IS NULL")
    if branch:
        where.append("branch=?")
        params.append(branch)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with cursor() as cur:
        rows = cur.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def mark_note_used(note_id: int, post_id: int) -> None:
    with cursor() as cur:
        cur.execute("UPDATE notes SET used_in_post_id=? WHERE id=?", (post_id, note_id))


def notes_today_count() -> int:
    with cursor() as cur:
        row = cur.execute(
            "SELECT COUNT(*) FROM notes WHERE date(created_at,'localtime')=date('now','localtime')"
        ).fetchone()
    return row[0] if row else 0


def record_channel_post(
    message_id: int,
    source: str,
    author_name: str | None = None,
    text_preview: str | None = None,
    has_media: bool = False,
) -> None:
    """Log a channel post (bot-published OR manual from Yulia/team). Idempotent."""
    with cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO channel_activity(message_id, source, author_name, text_preview, has_media) "
            "VALUES (?, ?, ?, ?, ?)",
            (message_id, source, author_name, (text_preview or "")[:80], 1 if has_media else 0),
        )


def posts_today_count() -> int:
    """Count posts in channel today (Kyiv local day) — bot + manual combined."""
    with cursor() as cur:
        row = cur.execute(
            "SELECT COUNT(*) FROM channel_activity "
            "WHERE date(posted_at, 'localtime') = date('now', 'localtime')"
        ).fetchone()
    return row[0] if row else 0


def posts_today_breakdown() -> dict:
    """Today's posts grouped by source — for quota messages."""
    with cursor() as cur:
        rows = cur.execute(
            "SELECT source, COUNT(*) FROM channel_activity "
            "WHERE date(posted_at, 'localtime') = date('now', 'localtime') "
            "GROUP BY source"
        ).fetchall()
    return {r[0]: r[1] for r in rows}


def log_event(kind: str, payload: dict | str | None = None) -> None:
    with cursor() as cur:
        cur.execute(
            "INSERT INTO event_log(kind, payload) VALUES (?, ?)",
            (kind, json.dumps(payload) if isinstance(payload, dict) else payload),
        )


# ---------- YouTube ----------

def add_youtube_video(video_id: str, **fields) -> bool:
    """Return True if inserted (new), False if already known."""
    with cursor() as cur:
        existing = cur.execute("SELECT 1 FROM youtube_videos WHERE video_id=?", (video_id,)).fetchone()
        if existing:
            return False
        cols = ["video_id"] + list(fields.keys())
        placeholders = ", ".join("?" * len(cols))
        cur.execute(
            f"INSERT INTO youtube_videos({', '.join(cols)}) VALUES ({placeholders})",
            [video_id] + list(fields.values()),
        )
        return True


def unprocessed_videos(limit: int = 5) -> list[dict]:
    with cursor() as cur:
        return [
            dict(r)
            for r in cur.execute(
                "SELECT * FROM youtube_videos WHERE processed=0 ORDER BY published_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        ]


def mark_video_processed(video_id: str) -> None:
    with cursor() as cur:
        cur.execute("UPDATE youtube_videos SET processed=1 WHERE video_id=?", (video_id,))


if __name__ == "__main__":
    init_db()
    print(f"✅ Database initialized: {config.DB_PATH}")
