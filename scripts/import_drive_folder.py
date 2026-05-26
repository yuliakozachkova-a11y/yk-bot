"""Import a public Google Drive folder into drive_photos table.

Usage:
    python3 scripts/import_drive_folder.py FOLDER_ID "Folder label" [auto-approve]

Uses Drive's public embeddedfolderview HTML endpoint — no auth required
as long as the folder is shared 'anyone with link can view'.

If 'auto-approve' is passed as 3rd arg, photos go straight to 'approved'.
Otherwise stays 'pending' for Yulia to review.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bot import drive


def scrape_folder(folder_id: str) -> list[tuple[str, str]]:
    """Return [(file_id, filename), ...] for a public folder.
    Limited to ~50 entries (Drive embedded view limit).
    """
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    # Match file_id + filename from anchor tags
    # Pattern: href="/file/d/FILE_ID/view"...>FILENAME</a>
    pattern = r'/file/d/([a-zA-Z0-9_-]{20,})/view[^"]*"[^>]*>(?:<div[^>]*>)?([^<]+?)(?:</div>)?</a>'
    matches = re.findall(pattern, r.text)
    # Fallback: just file_ids if filename parse fails
    if not matches:
        ids = set(re.findall(r'/file/d/([a-zA-Z0-9_-]{20,})/view', r.text))
        matches = [(fid, f"{fid[:8]}.jpg") for fid in ids]
    # Dedup by file_id, keep first filename
    seen: dict[str, str] = {}
    for fid, name in matches:
        if fid not in seen:
            seen[fid] = name.strip() or f"{fid[:8]}.jpg"
    return list(seen.items())


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: import_drive_folder.py FOLDER_ID 'Folder label' [auto-approve]")
        sys.exit(1)
    folder_id = sys.argv[1]
    folder_label = sys.argv[2]
    auto_approve = len(sys.argv) > 3 and sys.argv[3] == "auto-approve"

    drive.ensure_table()
    files = scrape_folder(folder_id)
    print(f"📁 «{folder_label}» — {len(files)} файлів знайдено")

    new_count = 0
    for file_id, filename in files:
        if drive.add_photo(file_id, filename, folder_label):
            new_count += 1
            if auto_approve:
                drive.update_classification(file_id, "approved")

    print(f"  ➕ Додано нових: {new_count}")
    print(f"  ⏭ Вже були в каталозі: {len(files) - new_count}")
    if auto_approve:
        print(f"  ✓ Усі нові помічено як approved")
    else:
        print(f"  ⚠ Усі pending — потребують візуальної перевірки")


if __name__ == "__main__":
    main()
