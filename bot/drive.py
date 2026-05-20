"""Google Drive integration — direct URL streaming, no local copies."""
from __future__ import annotations

from . import db


def drive_download_url(file_id: str, size: int = 2000) -> str:
    """
    Resized Drive URL — works reliably with Telegram bot.send_photo() for large originals.
    Telegram has a ~5MB limit when sending photo by URL; Drive originals are often 10-20MB.
    Using `lh3.googleusercontent.com/d/{id}=w{size}` returns a downsized JPEG — perfect for Telegram.
    """
    return f"https://lh3.googleusercontent.com/d/{file_id}=w{size}"


def drive_original_url(file_id: str) -> str:
    """Original full-size download URL. Only use if you know file is <5MB."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def drive_thumbnail_url(file_id: str, size: int = 2000) -> str:
    """Thumbnail URL — large preview for analysis, also works with Telegram."""
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"


# ----- catalog -----

SCHEMA = """
CREATE TABLE IF NOT EXISTS drive_photos (
    file_id TEXT PRIMARY KEY,
    filename TEXT,
    folder TEXT,
    classification TEXT DEFAULT 'pending',  -- pending|approved|skipped
    mood TEXT,             -- serious|smiling|playful|neutral
    scene TEXT,            -- studio|outdoor|event|office|portrait
    notes TEXT,
    has_other_people INTEGER DEFAULT 0,
    telegram_file_id TEXT,
    added_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT,
    last_used_at TEXT,
    used_in_posts INTEGER DEFAULT 0,
    used_post_ids TEXT          -- JSON list of post ids
);

CREATE INDEX IF NOT EXISTS idx_drive_classification ON drive_photos(classification);
CREATE INDEX IF NOT EXISTS idx_drive_last_used ON drive_photos(last_used_at);
"""

# Hard rule: photo cannot be reused within this many days
MIN_DAYS_BEFORE_REUSE = 180  # 6 months — set by Yulia 2026-05-20


def ensure_table() -> None:
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.executescript(SCHEMA)
    con.commit()
    con.close()


def add_photo(file_id: str, filename: str, folder: str) -> bool:
    """Insert photo if not exists. Returns True if new."""
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    cur = con.cursor()
    existing = cur.execute("SELECT 1 FROM drive_photos WHERE file_id=?", (file_id,)).fetchone()
    if existing:
        con.close()
        return False
    cur.execute(
        "INSERT INTO drive_photos(file_id, filename, folder) VALUES (?, ?, ?)",
        (file_id, filename, folder),
    )
    con.commit()
    con.close()
    return True


def update_classification(file_id: str, classification: str, **fields) -> None:
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    sets = ["classification=?", "reviewed_at=datetime('now')"]
    args = [classification]
    for k, v in fields.items():
        sets.append(f"{k}=?")
        args.append(v)
    args.append(file_id)
    con.execute(f"UPDATE drive_photos SET {', '.join(sets)} WHERE file_id=?", args)
    con.commit()
    con.close()


def mark_photo_used(file_id: str, post_id: int) -> None:
    """Mark a photo as used in a published post. NEVER reuse within MIN_DAYS_BEFORE_REUSE."""
    import json
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    row = cur.execute("SELECT used_post_ids, used_in_posts FROM drive_photos WHERE file_id=?", (file_id,)).fetchone()
    if not row:
        # photo not in catalog yet — add as one-off use
        cur.execute(
            "INSERT INTO drive_photos(file_id, classification, last_used_at, used_in_posts, used_post_ids) "
            "VALUES (?, 'approved', datetime('now'), 1, ?)",
            (file_id, json.dumps([post_id])),
        )
    else:
        existing_ids = json.loads(row["used_post_ids"]) if row["used_post_ids"] else []
        if post_id not in existing_ids:
            existing_ids.append(post_id)
        cur.execute(
            "UPDATE drive_photos SET last_used_at=datetime('now'), used_in_posts=?, used_post_ids=? WHERE file_id=?",
            (len(existing_ids), json.dumps(existing_ids), file_id),
        )
    con.commit()
    con.close()


def pick_unused_approved(min_days_since_use: int = MIN_DAYS_BEFORE_REUSE) -> dict | None:
    """
    Pick a random approved photo NOT used within the last N days.
    Returns None if all approved photos were used recently — caller must surface this.
    """
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        """
        SELECT * FROM drive_photos
        WHERE classification='approved'
          AND (last_used_at IS NULL
               OR julianday('now') - julianday(last_used_at) > ?)
        ORDER BY RANDOM() LIMIT 1
        """,
        (min_days_since_use,),
    ).fetchone()
    con.close()
    return dict(row) if row else None


def days_since_last_use(file_id: str) -> int | None:
    """How many days since this photo was last published. None = never used."""
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT julianday('now') - julianday(last_used_at) AS days FROM drive_photos WHERE file_id=?",
        (file_id,),
    ).fetchone()
    con.close()
    if not row or row["days"] is None:
        return None
    return int(row["days"])


def is_safe_to_reuse(file_id: str) -> bool:
    """Return True if photo was never used OR used > MIN_DAYS_BEFORE_REUSE ago."""
    d = days_since_last_use(file_id)
    return d is None or d >= MIN_DAYS_BEFORE_REUSE


def pick_diverse_approved(avoid_recent_subfolders: int = 2) -> dict | None:
    """
    Pick an approved photo from a subfolder that hasn't been used in the last N picks.
    Rotation rule (Yulia 2026-05-20): never use photos from the same shoot back-to-back.
    """
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row

    # Get last N used subfolders (most recent first)
    recent_folders = [
        r["folder"] for r in con.execute(
            "SELECT DISTINCT folder FROM drive_photos "
            "WHERE last_used_at IS NOT NULL "
            "ORDER BY last_used_at DESC LIMIT ?",
            (avoid_recent_subfolders,),
        ).fetchall()
    ]

    # Pick approved photo NOT from recent folders AND not used <180 days
    placeholders = ",".join("?" * len(recent_folders)) if recent_folders else "''"
    sql = f"""
        SELECT * FROM drive_photos
        WHERE classification='approved'
          AND (last_used_at IS NULL OR julianday('now') - julianday(last_used_at) > {MIN_DAYS_BEFORE_REUSE})
          AND folder NOT IN ({placeholders})
        ORDER BY RANDOM() LIMIT 1
    """
    row = con.execute(sql, recent_folders).fetchone()

    # Fallback: if all approved are in recent folders, allow oldest one
    if not row:
        row = con.execute(
            "SELECT * FROM drive_photos WHERE classification='approved' "
            "AND (last_used_at IS NULL OR julianday('now') - julianday(last_used_at) > ?) "
            "ORDER BY RANDOM() LIMIT 1",
            (MIN_DAYS_BEFORE_REUSE,),
        ).fetchone()
    con.close()
    return dict(row) if row else None


def list_pending(limit: int = 100) -> list[dict]:
    import sqlite3
    from . import config
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM drive_photos WHERE classification='pending' LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]
