"""
Auto-replacement library.
When user deletes a post, bot generates a replacement with same time but different genre/text.
"""
from __future__ import annotations

import random
from pathlib import Path
from . import config

VISUALS = config.DATA_DIR / "preview_visuals"

# Library of ready-to-use alternative posts.
# Each: (genre, text, visual_filename, optional poll spec)
REPLACEMENTS = [
    {
        "genre": "marketing_quote_alt",
        "text": (
            "Уникайте категоричності. Вона вбиває гнучкість 👠\n\n"
            "Жорстко — не значить сильно.\n"
            "Сильно — це коли тримаєш форму, але дозволяєш собі бачити інше.\n\n"
            "Ставте ❤️ якщо відгукується."
        ),
        "visual": "tpl6_world_not_indebted.png",
    },
    {
        "genre": "marketing_quote_alt",
        "text": (
            "Якщо хочете відповісти комусь адекватно — будьте в адекваті 😜\n\n"
            "Реакція з тривоги — не відповідь.\n"
            "Це повторне відтворення того, що тебе зачепило.\n\n"
            "Як думаєш? Пиши в коментарях 👇"
        ),
        "visual": "tpl3_spotlight_book.png",
    },
    {
        "genre": "fraza_weekend_alt",
        "text": (
            "Якщо щось іде не за планом — значить, це план Бога 🙌\n\n"
            "Іноді життя сценарно мудріше за нас.\n"
            "Розслабся. Воно знає, що робить.\n\n"
            "Ставте 🙏 хто погоджується."
        ),
        "visual": "tpl6_world_not_indebted.png",
    },
    {
        "genre": "personal_thought_alt",
        "text": (
            "Не бійтеся залишатися наодинці з собою 🫂\n\n"
            "Це найкращий час для близького знайомства.\n"
            "Поза чужими очікуваннями — там ти справжня.\n\n"
            "Як тобі такі моменти зараз? Чесно у коментарях 👇"
        ),
        "visual": "tpl8_saturday_choice.png",
    },
    {
        "genre": "checklist_alt",
        "text": (
            "3 кроки, як тримати свою цінність 🧲\n\n"
            "1️⃣ Чекни ствердження «треба» — звідки воно?\n"
            "2️⃣ Запитай: «А кому це треба?» Якщо не тобі — відпусти.\n"
            "3️⃣ Постав те, що твоє, в графік сьогодні.\n\n"
            "Який пункт зробиш зараз? Пиши номером 👇"
        ),
        "visual": "checklist_value.png",
    },
    {
        "genre": "marketing_quote_alt",
        "text": (
            "Зниження стандартів заради чиєїсь посередності — це відмова від принципів 🪬\n\n"
            "Тебе ніхто не зменшував. Ти сама погодилась.\n"
            "І тільки ти можеш сказати: «досить».\n\n"
            "Хто з тобою на наступний рівень? Постав ❤️ якщо готова."
        ),
        "visual": "tpl7_convenient_vs_valuable.png",
    },
    {
        "genre": "fraza_evening_alt",
        "text": (
            "Віра в себе має бути такою ж сильною, як віра в те, що хтось зміниться 🕊️\n\n"
            "Дай собі стільки авансу, скільки даєш іншим.\n\n"
            "Ставте 🤍 хто згоден."
        ),
        "visual": "tpl6_world_not_indebted.png",
    },
    {
        "genre": "interactive_alt",
        "text": (
            "Любі, маленьке питання 🤍\n\n"
            "Що ти за останній місяць НЕ зробила,\n"
            "хоча точно знала, що треба?\n\n"
            "Напиши одну дію в коментарях. Часом озвучити = вже зробити перший крок 👇"
        ),
        "visual": "tpl5_diptych_poll.png",
    },
]


def pick_replacement(exclude_text: str = "", exclude_genre: str = "") -> dict:
    """Pick a random replacement that's different from the deleted post."""
    pool = [r for r in REPLACEMENTS
            if r["text"] != exclude_text and r["genre"] != exclude_genre]
    if not pool:
        pool = REPLACEMENTS
    return random.choice(pool)


def get_visual_path(visual_filename: str) -> str:
    return str(VISUALS / visual_filename)
