"""Poll YouTube channels via RSS, store new videos in DB."""
from __future__ import annotations
import asyncio
import re
from datetime import datetime, timezone

import feedparser
import httpx

from . import config, db

CHANNEL_ID_CACHE: dict[str, str] = {}


async def resolve_channel_id(handle: str) -> str | None:
    """Convert @handle to channelId by scraping the channel page once."""
    if handle in CHANNEL_ID_CACHE:
        return CHANNEL_ID_CACHE[handle]
    url = f"https://www.youtube.com/{handle}"
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        return None
    m = re.search(r'"channelId":"(UC[\w-]{20,})"', r.text) or re.search(r'channel/(UC[\w-]{20,})', r.text)
    if not m:
        return None
    cid = m.group(1)
    CHANNEL_ID_CACHE[handle] = cid
    return cid


async def fetch_channel_videos(handle: str, label: str) -> int:
    """Fetch RSS for channel, store new videos. Returns count of new."""
    cid = await resolve_channel_id(handle)
    if not cid:
        db.log_event("youtube_resolve_failed", {"handle": handle})
        return 0

    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(feed_url)
    if r.status_code != 200:
        db.log_event("youtube_fetch_failed", {"handle": handle, "status": r.status_code})
        return 0

    feed = feedparser.parse(r.text)
    new_count = 0
    for entry in feed.entries:
        vid = entry.get("yt_videoid") or entry.id.split(":")[-1]
        thumbnail = None
        if "media_thumbnail" in entry:
            thumbnail = entry.media_thumbnail[0].get("url")
        is_new = db.add_youtube_video(
            vid,
            channel_handle=handle,
            title=entry.title,
            description=entry.get("summary", ""),
            published_at=entry.published,
            url=entry.link,
            thumbnail_url=thumbnail,
        )
        if is_new:
            new_count += 1
    db.log_event("youtube_poll", {"handle": handle, "label": label, "new": new_count, "total_in_feed": len(feed.entries)})
    return new_count


async def poll_all_channels() -> dict[str, int]:
    results = {}
    for ch in config.YOUTUBE_CHANNELS:
        try:
            results[ch["handle"]] = await fetch_channel_videos(ch["handle"], ch["label"])
        except Exception as e:
            db.log_event("youtube_poll_error", {"handle": ch["handle"], "error": str(e)})
            results[ch["handle"]] = -1
    return results


if __name__ == "__main__":
    db.init_db()
    res = asyncio.run(poll_all_channels())
    print("YouTube poll results:")
    for handle, n in res.items():
        marker = "❌" if n < 0 else "✅"
        print(f"  {marker} {handle}: {n} new videos")
