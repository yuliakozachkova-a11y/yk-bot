"""
BIG BATCH week 2: Sun 24.05 → Sat 30.05 (~13 posts).
Yulia 2026-05-21: «I roblyu novyy batch z urakhuvannyam engagement» kozhen tyzhden.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from zoneinfo import ZoneInfo

from bot import db

TZ = ZoneInfo("Europe/Kyiv")
db.init_db()


def utc(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, tzinfo=TZ).astimezone(ZoneInfo("UTC")).isoformat()


VISUAL_DIR = "data/preview_visuals"

# Photo file_ids from Мудрик 2026 (approved solo portraits, not used yet)
PHOTO_MUDRYK_BLACK_BLAZER = "1agBqChxSb5FfIL9o5dZ7JHVJXD4ufoDX"   # 3M4A1249
PHOTO_MUDRYK_LIGHT_FLORAL = "1vv9Ybz-GMAJwMP_D9bjT4o3J36X5ENCd"   # 3M4A6513
PHOTO_MUDRYK_WHITE_BLAZER = "1Cr5mfQiJgLVEU4nGn8Nzv1oIDWUwUCq_"   # 3M4A8456


POSTS = [
    # ===== ВС 24.05 — Карта тижня (13:00 її ручна), я ставлю тільки вечір =====
    {
        "scheduled_at": utc(2026, 5, 24, 17, 30),
        "genre": "calm_sunday",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl8_saturday_choice.png",
        "text": """Любі, недільний вечір 🤍

Не для планів.
Не для «треба».

Час побути з собою.
Запитати: «Як я?»
І чесно почути відповідь.

Бо понеділок все одно настане.
Питання — у якому стані ти його зустрінеш.

Як ти зараз? Одним словом — у коментарях 👇""",
    },

    # ===== ПН 25.05 =====
    {
        "scheduled_at": utc(2026, 5, 25, 9, 0),
        "genre": "monday_manifest",
        "media_type": "photo",
        "media_file_id": PHOTO_MUDRYK_BLACK_BLAZER,
        "text": """Любі, новий тиждень. Нова сцена 🎯

Ти або входиш у нього як автор свого життя — з планом, силою, ясністю.
Або як виконавець чужих сценаріїв — реагуючи на чужі очікування.

Третього не дано.

Хто ти на цьому тижні? Чесно — в коментарях 👇""",
    },
    {
        "scheduled_at": utc(2026, 5, 25, 17, 30),
        "genre": "product_book",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl3_spotlight_book.png",
        "text": """Любі, нагадую — моя книга «Ген Грошей» 📖

Це не про техніки заробляти більше.
Це про те, що в голові заважає тобі дозволити собі більше.

✔️ Друкована — 1 600 ₴ (зі знижкою)
✔️ PDF / EPUB — 777 ₴

👉 https://kozachkova.online/page122008116.html

P.S. Якщо ловиш себе на «це не для мене» — точно тобі 🤍""",
    },

    # ===== ВТ 26.05 — день ефіру «Жива книга» о 8:30! =====
    {
        "scheduled_at": utc(2026, 5, 26, 7, 30),
        "genre": "youtube_anonce_live",
        "media_type": "none",
        "text": """Друзі, о 8:30 чекаю на YouTube 🤍

Щовівторка ми разом смакуємо книгу «Мистецтво бути в цей: час» — прямою трансляцією.

Не просто читаємо — а розбираємо.
Сенси. Історії. Те, як народжувалась ця книга.

🔗 ПРИЄДНАТИСЯ ТУТ 🔗 https://youtube.com/@kozachkova.yuliia

P.S. Якщо ще не з нами — починай з 1 зустрічі. Або підключайся живцем 👋""",
    },
    {
        "scheduled_at": utc(2026, 5, 26, 13, 0),
        "genre": "live_recap",
        "media_type": "photo",
        "media_file_id": PHOTO_MUDRYK_WHITE_BLAZER,
        "text": """Любі, по гарячих слідах ефіру ❤️‍🔥

Сьогодні ми говорили про те, як бути в цьому часі.
Не біжати від нього.
Не чекати «коли буде краще».
А вчитися дихати в тому, що є.

Це найскладніше — і одночасно найважливіше мистецтво.

Запис уже на YouTube. Наступний вівторок о 8:30.

P.S. Яка думка з ефіру взяла за душу? Поділись 👇""",
    },
    {
        "scheduled_at": utc(2026, 5, 26, 17, 30),
        "genre": "poll_evening",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl5_diptych_poll.png",
        "text": """Любі, маленький тест на щирість 🤍

Який стан тобі найближче зараз?""",
        "poll_question": "Твій поточний стан:",
        "poll_options": [
            "🌿 Спокій — все на місці",
            "⚡️ Рух — нагадую собі що жива",
            "🌊 Перевертає — багато змін",
            "🌫 Туман — не знаю куди",
            "🔥 Вибух — все одночасно",
        ],
    },

    # ===== СР 27.05 =====
    {
        "scheduled_at": utc(2026, 5, 27, 13, 0),
        "genre": "youtube_anonce",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl4_stat_hero.png",
        "text": """Любі, чому ми ігноруємо поради, які могли б змінити життя?

Розбираю у випуску — три внутрішні причини, які працюють непомітно. Жодна з них не про «погана порада».

👉 https://www.youtube.com/watch?v=w6eEkrXJ7jg

Яку пораду ти останньою проігнорувала — і пожаліла? 👇""",
    },
    # #14 уже в БД на Ср 27.05 17:30 — не дублюємо

    # ===== ЧТ 28.05 =====
    {
        "scheduled_at": utc(2026, 5, 28, 13, 0),
        "genre": "checklist",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/checklist_value.png",  # reuse for now, генерую нову вечером
        "text": """Любі, 5 ознак що ти переростаєш своє оточення 🧲

1️⃣ Розмови з людьми тепер «маленькі» — про побут, не про сенси.

2️⃣ Тобі складно знайти спільну тему. Раніше було легко.

3️⃣ Ти відчуваєш втому після зустрічі з тими, з ким раніше «заряджалась».

4️⃣ Тобі не хочеться розповідати про свої перемоги — бо знаєш реакцію.

5️⃣ Ти все частіше думаєш: «Я тут чужа.»

Це не гордість. Це етап.
І це означає — час шукати нове коло.

Скільки ознак співпало? Цифру в коментарях 👇""",
    },
    {
        "scheduled_at": utc(2026, 5, 28, 17, 30),
        "genre": "personal_thought",
        "media_type": "photo",
        "media_file_id": PHOTO_MUDRYK_LIGHT_FLORAL,
        "text": """Любі, маленька думка вечора 🤍

Бути собою — це щодня нова валюта.

Ти платиш нею за свободу.
Платиш нею за зрілість.
Платиш нею за справжні стосунки.

Не зекономиш — отримаєш чужe життя.
Заплатиш — отримаєш своє.

Готова платити? ❤️""",
    },

    # ===== ПТ 29.05 =====
    {
        "scheduled_at": utc(2026, 5, 29, 13, 0),
        "genre": "checklist",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl9_hero_journey.png",  # reuse, перегенерую нову
        "text": """Любі, 3 фрази, які варто перестати говорити собі 🚫

«Мені вже пізно почати.»
Не пізно. Це — найзручніше виправдання психіки.

«Я недостатньо ___ (розумна / гарна / молода / готова).»
Достатньо. Ця думка тримає тебе у безпеці автопілоту.

«Спочатку розберусь із собою — потім почну.»
Це нескінченний цикл. Розбиратись будеш все життя.
Починати треба зараз.

Яку фразу ловиш в собі найчастіше? Пиши цифру 👇""",
    },
    {
        "scheduled_at": utc(2026, 5, 29, 17, 30),
        "genre": "poll_evening",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl10_quiz_card.png",
        "text": """Любі, тест на щирість вечора п'ятниці 🤍

Що тобі зараз найскладніше у роботі з собою?""",
        "poll_question": "Найскладніше зараз:",
        "poll_options": [
            "Назвати свою ціну (грошову / емоційну)",
            "Сказати «ні» тому, що тягне вниз",
            "Не зменшуватись поруч з кимось",
            "Робити навіть коли страшно",
            "Чути себе у потоці чужих думок",
        ],
    },

    # ===== СБ 30.05 =====
    {
        "scheduled_at": utc(2026, 5, 30, 13, 0),
        "genre": "weekend_quote",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl6_world_not_indebted.png",
        "text": """Любі, думка для суботи 🪽

Достаток — це не цифра на рахунку.

Достаток — це стан опори.
На свої цінності. На свою працю. На свого Бога.

Багатий — той, хто перестав хотіти.
Бідний — той, кому завжди мало, незалежно від суми.

Ставте ❤️ якщо відгукується.""",
    },
    {
        "scheduled_at": utc(2026, 5, 30, 17, 30),
        "genre": "weekend_test",
        "media_type": "photo",
        "media_path": f"{VISUAL_DIR}/tpl7_convenient_vs_valuable.png",
        "text": """Любі, тест вечора 🤍

Який твій тип реакції на гроші, коли вони з'являються?""",
        "poll_question": "Коли в тебе з'являються несподівані гроші — ти:",
        "poll_options": [
            "💎 Інвестую (бізнес, освіта, активи)",
            "🎁 Витрачаю на себе (одяг, краса, подорожі)",
            "🤝 Допомагаю іншим (близьким, благодійність)",
            "🏦 Зберігаю (відкладаю на чорний день)",
            "😰 Тривожусь і не знаю що робити",
        ],
    },
]


def main():
    # Clean up existing posts in Sun 24 → Sun 31 (idempotent re-run)
    import sqlite3
    from bot import config
    con = sqlite3.connect(config.DB_PATH)
    con.execute("""
        DELETE FROM posts
        WHERE scheduled_at >= '2026-05-24'
          AND scheduled_at < '2026-05-31'
          AND source = 'batch_week2'
    """)
    con.commit()
    con.close()

    inserted = 0
    for post in POSTS:
        post_id = db.add_post(
            scheduled_at=post["scheduled_at"],
            text=post.get("text", ""),
            media_type=post.get("media_type", "none"),
            media_file_id=post.get("media_file_id"),
            media_path=post.get("media_path"),
            poll_question=post.get("poll_question"),
            poll_options=post.get("poll_options"),
            source="batch_week2",
            genre=post.get("genre", "general"),
            metadata={"batch": "week2", "auto_generated": True},
        )
        local = datetime.fromisoformat(post["scheduled_at"].replace("Z", "+00:00")).astimezone(TZ)
        media_marker = "🖼Drive" if post.get("media_file_id") else ("📊AI" if post.get("media_path") else "🔗URL")
        print(f"  #{post_id:>3} · {local.strftime('%a %d.%m %H:%M')} · {post['genre']:<20s} · {media_marker}")
        inserted += 1

    print(f"\n✅ Inserted: {inserted} posts (batch_week2)")


if __name__ == "__main__":
    main()
