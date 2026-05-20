"""
Three new template variants (different from V1):
- TEMPLATE 3: «Spotlight quote» — большая цитата на тёплом градиенте
- TEMPLATE 4: «Stat hero» — крупное число + подпись (минимализм)
- TEMPLATE 5: «Diptych» — split layout, текст слева, графика справа
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "preview_visuals"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def font(size, bold=False, italic=False):
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = (3 if italic else 2) if bold else (1 if italic else 0)
    try:
        return ImageFont.truetype(path, size, index=idx)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


# Palettes — for variation
PALETTE_WARM = {  # тёплый коралл-золото-вино
    "bg_top": (44, 24, 30),
    "bg_bottom": (88, 44, 38),
    "text": "#F4E6D2",
    "accent": "#FFB48C",
    "dim": "#C8A89A",
}
PALETTE_DARK = {  # глубокий чёрный + кремовый
    "bg_top": (10, 10, 12),
    "bg_bottom": (22, 18, 24),
    "text": "#F2E7DA",
    "accent": "#E8A87C",
    "dim": "#8C7A6B",
}
PALETTE_LIGHT = {  # светлый бежевый — для контраста
    "bg_top": (240, 232, 220),
    "bg_bottom": (220, 208, 195),
    "text": "#1A1A1F",
    "accent": "#A85838",
    "dim": "#6B5A4F",
}


def gradient_bg(w, h, palette):
    img = Image.new("RGB", (w, h), palette["bg_top"])
    draw = ImageDraw.Draw(img)
    t_rgb = palette["bg_top"]
    b_rgb = palette["bg_bottom"]
    for y in range(h):
        t = y / h
        r = int(t_rgb[0] + (b_rgb[0] - t_rgb[0]) * t)
        g = int(t_rgb[1] + (b_rgb[1] - t_rgb[1]) * t)
        b = int(t_rgb[2] + (b_rgb[2] - t_rgb[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def wrap(text, max_chars):
    words = text.split()
    lines, cur, n = [], [], 0
    for w in words:
        if n + len(w) + 1 > max_chars and cur:
            lines.append(" ".join(cur))
            cur, n = [w], len(w)
        else:
            cur.append(w)
            n += len(w) + 1
    if cur:
        lines.append(" ".join(cur))
    return lines


# ============ TEMPLATE 3: SPOTLIGHT QUOTE — для анонса книги ============

def make_spotlight_quote_book():
    W, H = 1080, 1080
    pal = PALETTE_WARM
    img = gradient_bg(W, H, pal)
    d = ImageDraw.Draw(img)

    # Open quote mark — large decorative
    d.text((W // 2, 220), "“", fill=pal["accent"], anchor="mm", font=font(220, bold=True))

    # The quote — big, central
    quote = "Гроші починаються\nне в гаманці,\nа в дозволі собі."
    y = 430
    for line in quote.split("\n"):
        d.text((W // 2, y), line, fill=pal["text"], anchor="mm", font=font(58, bold=True))
        y += 80

    # Attribution
    d.text((W // 2, 770), "— з книги «Ген Грошей»", fill=pal["dim"], anchor="mm", font=font(28, italic=True))

    # Footer signature
    d.text((W // 2, 970), "ЮЛІЯ КОЗАЧКОВА", fill=pal["accent"], anchor="mm", font=font(24, bold=True))
    d.text((W // 2, 1010), "психолог · авторка 3 книг", fill=pal["dim"], anchor="mm", font=font(20))

    out = OUT_DIR / "tpl3_spotlight_book.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ TEMPLATE 4: STAT HERO — для анонса видео про советы ============

def make_stat_hero():
    W, H = 1080, 1080
    pal = PALETTE_DARK
    img = gradient_bg(W, H, pal)
    d = ImageDraw.Draw(img)

    # Top label
    d.text((W // 2, 110), "ЮЛІЯ · YOUTUBE", fill=pal["dim"], anchor="mm", font=font(22, bold=True))

    # Stat — massive number
    d.text((W // 2, 360), "78%", fill=pal["accent"], anchor="mm", font=font(280, bold=True))

    # Subtitle
    d.text((W // 2, 550), "людей ігнорують поради,", fill=pal["text"], anchor="mm", font=font(38, bold=True))
    d.text((W // 2, 605), "які могли б змінити їхнє життя.", fill=pal["text"], anchor="mm", font=font(38, bold=True))

    # Why — short
    why = "Не тому, що погана порада.\nА через сором, страх і потребу контролю."
    y = 720
    for line in why.split("\n"):
        d.text((W // 2, y), line, fill=pal["dim"], anchor="mm", font=font(28, italic=True))
        y += 45

    # CTA
    d.line((150, 920, W - 150, 920), fill=pal["dim"], width=2)
    d.text((W // 2, 970), "НОВИЙ ВИПУСК → YOUTUBE", fill=pal["accent"], anchor="mm", font=font(26, bold=True))

    out = OUT_DIR / "tpl4_stat_hero.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ TEMPLATE 5: DIPTYCH — для опроса/интерактива ============

def make_diptych_poll():
    W, H = 1080, 1080
    pal = PALETTE_LIGHT  # light bg for variety
    img = gradient_bg(W, H, pal)
    d = ImageDraw.Draw(img)

    # Left half — question
    # Right half — visual block (5 lines as silhouettes of dialogue bubbles)
    mid = W // 2

    # LEFT: big question
    d.text((80, 200), "Який", fill=pal["text"], anchor="lt", font=font(72, bold=True))
    d.text((80, 280), "внутрішній", fill=pal["text"], anchor="lt", font=font(72, bold=True))
    d.text((80, 360), "голос звучить", fill=pal["text"], anchor="lt", font=font(72, bold=True))
    d.text((80, 440), "у тобі", fill=pal["text"], anchor="lt", font=font(72, bold=True))
    d.text((80, 520), "найчастіше?", fill=pal["accent"], anchor="lt", font=font(72, bold=True))

    # Bottom-left small
    d.text((80, 800), "5 варіантів —", fill=pal["dim"], anchor="lt", font=font(28))
    d.text((80, 840), "у голосуванні нижче ↓", fill=pal["dim"], anchor="lt", font=font(28, italic=True))

    # Bottom-right signature
    d.text((W - 80, 1020), "kozachkova.yuliia", fill=pal["accent"], anchor="rb", font=font(22, bold=True))

    # RIGHT: 5 stacked "voice bubble" shapes — diptych element
    bx = mid + 60
    by = 180
    bubble_w = 380
    voice_labels = ["Критик", "Дитина", "Дорослий", "Батьки", "Інший"]
    for i, label in enumerate(voice_labels):
        y = by + i * 100
        # Filled vs outline depending on idx
        if i == 0:
            # solid accent
            d.rounded_rectangle((bx, y, bx + bubble_w, y + 70), radius=35, fill=pal["accent"])
            d.text((bx + bubble_w // 2, y + 35), label, fill=pal["bg_top"], anchor="mm", font=font(28, bold=True))
        else:
            # outline
            d.rounded_rectangle((bx, y, bx + bubble_w, y + 70), radius=35, outline=pal["text"], width=2)
            d.text((bx + bubble_w // 2, y + 35), label, fill=pal["text"], anchor="mm", font=font(28))

    out = OUT_DIR / "tpl5_diptych_poll.png"
    img.save(out, quality=95, optimize=True)
    return out


if __name__ == "__main__":
    p3 = make_spotlight_quote_book()
    p4 = make_stat_hero()
    p5 = make_diptych_poll()
    print(f"✅ {p3}")
    print(f"✅ {p4}")
    print(f"✅ {p5}")
