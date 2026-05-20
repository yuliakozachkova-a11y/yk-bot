"""Fetch and store YouTube transcripts for deep content extraction."""
from __future__ import annotations

import json
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

from . import config

TRANSCRIPTS_DIR = config.DATA_DIR / "transcripts"
TRANSCRIPTS_DIR.mkdir(exist_ok=True)


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> str | None:
    """Fetch transcript text. Returns None if unavailable."""
    languages = languages or ["uk", "ru", "en"]
    try:
        ytt = YouTubeTranscriptApi()
        t = ytt.fetch(video_id, languages=languages)
        text = " ".join(s.text for s in t)
        return text
    except Exception:
        return None


def cache_transcript(video_id: str) -> str | None:
    """Fetch and cache transcript locally. Returns cached if already exists."""
    cache_file = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if cache_file.exists():
        return cache_file.read_text()
    text = fetch_transcript(video_id)
    if text:
        cache_file.write_text(text)
    return text


def get_cached(video_id: str) -> str | None:
    cache_file = TRANSCRIPTS_DIR / f"{video_id}.txt"
    if cache_file.exists():
        return cache_file.read_text()
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = cache_transcript(sys.argv[1])
        if text:
            print(f"✅ Cached transcript: {len(text)} chars")
            print(text[:500])
        else:
            print("❌ No transcript available")
