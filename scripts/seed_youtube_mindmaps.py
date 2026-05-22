"""Seed 3 YouTube hero-journey mind-map posts.

Picks 3 content-rich videos (not livestreams, not 'Жива книга'), generates a
TPL9 mind-map card for each, inserts a scheduled post that pairs the card with
a teaser text + 'Дивитись повне відео' button.

Stages are written by hand here — they're the editorial interpretation of each
episode. Yulia can edit any post via the bot before publish_due fires.

Run once:
    python3 scripts/seed_youtube_mindmaps.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bot import db
from bot.youtube_mindmap import make_mindmap


VIDEOS = [
    {
        "video_id": "D_VMURsLxbM",
        "channel": "@lyusterko",
        "title": "Депресія 2.0: усміхаєшся і одночасно вмираєш всередині?",
        "url": "https://youtu.be/D_VMURsLxbM",
        "badge": "ШЛЯХ ГЕРОЯ · 5 ЕТАПІВ",
        "title_line1": "Як вийти з",
        "title_line2": "функціональної депресії",
        "stages": [
            ("01", "ЗАПЕРЕЧЕННЯ", "«У мене все нормально»"),
            ("02", "ВТРАТА СМАКУ", "Дії є — задоволення немає"),
            ("03", "СПРОБА «БІЛЬШЕ»", "Більше відпочинку, мотивації… без ефекту"),
            ("04", "ВПІЗНАВАННЯ", "Це не втома. Це порожнеча."),
            ("05", "ПОВОРОТ", "Чесна розмова з собою → перший крок"),
        ],
        "scheduled_at": "2026-06-02T10:00:00+00:00",
        "text": (
            "Любі, я записала випуск про депресію, яку важко впізнати 🤍\n\n"
            "Ти усміхаєшся. Працюєш. Виглядаєш ОК.\n"
            "А всередині — порожньо.\n\n"
            "Це не лінь і не «у мене все добре».\n"
            "Це функціональна депресія — і вона має 5 етапів, через які проходить кожен.\n\n"
            "Подивись повний випуск — там розбираю кожен етап і перший крок виходу.\n\n"
            "Що ти впізнаєш у собі прямо зараз?"
        ),
    },
    {
        "video_id": "Icz-TvSGyaQ",
        "channel": "@lyusterko",
        "title": "Синдром жертви: чому СТРАЖДАТИ ВИГІДНО і як з цього вийти",
        "url": "https://youtu.be/Icz-TvSGyaQ",
        "badge": "ШЛЯХ ГЕРОЯ · 5 ЕТАПІВ",
        "title_line1": "Як вийти з",
        "title_line2": "ролі жертви",
        "stages": [
            ("01", "СКАРГА", "«Зі мною завжди так»"),
            ("02", "ВТОРИННА ВИГОДА", "Турбота, увага, право не діяти"),
            ("03", "ЗВИНУВАЧЕННЯ", "Винні всі — крім себе"),
            ("04", "ВПІЗНАВАННЯ", "Я обираю цю роль щодня"),
            ("05", "АВТОРСТВО", "Я — автор. Я можу інакше."),
        ],
        "scheduled_at": "2026-06-03T10:00:00+00:00",
        "text": (
            "Любі, є непомітна правда 🥺\n\n"
            "Іноді страждати — вигідно.\n"
            "Бо в ролі жертви тебе шкодують, тобі дозволено не діяти, тебе не критикують.\n\n"
            "Я записала розбір про 5 етапів виходу з цієї ролі — без жалості, з повагою.\n\n"
            "У відео — і як впізнати, і що робити з цією вторинною вигодою.\n\n"
            "А ти впізнаєш себе на якомусь з етапів?"
        ),
    },
    {
        "video_id": "fnmPT0Y6HJw",
        "channel": "@kozachkova.yuliia",
        "title": "Чому ви ЗАСТРЯГЛИ - подивіться на своє ОТОЧЕННЯ",
        "url": "https://youtu.be/fnmPT0Y6HJw",
        "badge": "ШЛЯХ ГЕРОЯ · 5 ЕТАПІВ",
        "title_line1": "Як оточення",
        "title_line2": "тримає тебе на місці",
        "stages": [
            ("01", "ЗВИЧНЕ КОЛО", "«Зі своїми спокійно»"),
            ("02", "НЕВИДИМА СТЕЛЯ", "Вище рівня кола — лячно"),
            ("03", "ОПІР НА ЗМІНИ", "«Ти змінилася» — як докор"),
            ("04", "ВИБІР", "Лояльність до своїх чи до себе"),
            ("05", "НОВЕ КОЛО", "Люди мого зросту → новий рівень"),
        ],
        "scheduled_at": "2026-06-04T10:00:00+00:00",
        "text": (
            "Любі, чесний випуск про оточення 🤍\n\n"
            "Ти не застрягла через лінь.\n"
            "І не через «не та робота».\n\n"
            "Найчастіше — застрягла, бо твоє коло не дозволяє рости вище за себе.\n\n"
            "У новому відео — 5 етапів, як оточення непомітно тримає тебе на місці.\n"
            "І що з цим робити, не зриваючи всіх зв'язків.\n\n"
            "Хто навколо тебе зараз — тягне вгору чи тримає?"
        ),
    },
]


def insert_post(video: dict, image_path: Path) -> int:
    return db.add_post(
        scheduled_at=video["scheduled_at"],
        text=video["text"],
        media_type="photo",
        media_path=str(image_path),
        inline_buttons=[{"text": "Дивитись повне відео ▶︎", "url": video["url"]}],
        source="youtube",
        genre="youtube_mindmap",
        metadata={
            "video_id": video["video_id"],
            "channel": video["channel"],
            "video_title": video["title"],
        },
    )


def main() -> None:
    out_dir = ROOT / "data" / "preview_visuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    for v in VIDEOS:
        img_path = out_dir / f"yt_mindmap_{v['video_id']}.png"
        make_mindmap(
            out_path=img_path,
            badge=v["badge"],
            title_line1=v["title_line1"],
            title_line2=v["title_line2"],
            stages=v["stages"],
        )
        post_id = insert_post(v, img_path)
        db.mark_video_processed(v["video_id"])
        print(f"  post #{post_id} · {v['scheduled_at']} · {img_path.name}")

    print(f"\nSeeded {len(VIDEOS)} YouTube mind-map posts.")


if __name__ == "__main__":
    main()
