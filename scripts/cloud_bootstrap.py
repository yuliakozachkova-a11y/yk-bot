"""
First-run bootstrap on cloud.
If DB is empty (fresh deploy) — populate with the current local snapshot.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import db, drive

db.init_db()
drive.ensure_table()


def is_fresh_deploy() -> bool:
    """Check if this is the very first run on cloud (DB is essentially empty)."""
    posts_count = len(db.list_posts(limit=1))
    photos_count = 0
    import sqlite3
    from bot import config
    con = sqlite3.connect(config.DB_PATH)
    photos_count = con.execute("SELECT COUNT(*) FROM drive_photos").fetchone()[0]
    con.close()
    return posts_count == 0 and photos_count == 0


def bootstrap():
    """Seed critical state for first cloud run."""
    print("🌱 Cloud bootstrap starting…")

    # Baseline settings
    db.set_setting("baseline_subscribers", 6218)
    db.set_setting("linked_chat_id", "-1002045261900")
    db.set_setting("owner_username", "pashysta_lina")
    db.set_setting("admins", ["YK_Media_Bot", "angelinatrachuk", "pashysta_lina",
                              "a_morozovvv", "kozachkova_yuliia", "kiselevva1", "leshamakhonin"])
    db.set_setting("book_gen_groshei_purchase_url", "https://kozachkova.online/page122008116.html")
    db.set_setting("book_gen_groshei_presentation_url", "https://kozachkova.online/money_gen")
    db.set_setting("photos_drive_url", "")
    print("  ✓ Settings seeded")

    # Seed first week if posts empty
    if len(db.list_posts(limit=1)) == 0:
        try:
            import subprocess
            ROOT = Path(__file__).resolve().parent.parent
            subprocess.run(["python3", str(ROOT / "scripts" / "seed_first_week.py")], check=False, cwd=str(ROOT))
            print("  ✓ First week of posts seeded")
        except Exception as e:
            print(f"  ⚠️  Seed failed: {e}")

    # Seed drive photo catalog
    try:
        import subprocess
        ROOT = Path(__file__).resolve().parent.parent
        subprocess.run(["python3", str(ROOT / "scripts" / "inventory_drive_from_logs.py")], check=False, cwd=str(ROOT))
        print("  ✓ Drive photo catalog seeded")
    except Exception as e:
        print(f"  ⚠️  Drive catalog failed: {e}")

    print("✅ Bootstrap done")


if __name__ == "__main__":
    if is_fresh_deploy():
        print("Fresh deploy detected — bootstrapping…")
        bootstrap()
    else:
        print("Existing DB found — skipping bootstrap")
