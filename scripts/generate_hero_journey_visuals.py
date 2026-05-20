"""
Generation V3 — visually rich templates (per Yulia 2026-05-20):
- Decorative elements (lines, dots, soft shapes)
- Cinematic gradients
- Iconography (arrows, points, stages)
- "Not just text on a flat background"

Templates:
- TPL9: HERO JOURNEY — 5-stage path with connecting line + dots
- TPL10: INTERACTIVE QUIZ CARD — visual quiz styled
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "preview_visuals"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def font(size, bold=False, italic=False):
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = (3 if italic else 2) if bold else (1 if italic else 0)
    try:
        return ImageFont.truetype(path, size, index=idx)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def gradient_bg(w, h, top_rgb, bot_rgb):
    img = Image.new("RGB", (w, h), top_rgb)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def add_soft_glow(img, x, y, radius, color, opacity=80):
    """Add a soft radial glow at (x,y)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (opacity,))
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius // 2))
    img.paste(blurred, (0, 0), blurred)


def add_grain(img, intensity=8):
    """Subtle film grain for cinematic feel."""
    import random
    px = img.load()
    w, h = img.size
    for _ in range(w * h // 40):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        r, g, b = px[x, y]
        n = random.randint(-intensity, intensity)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))


# ============ TPL9: HERO JOURNEY ============

def make_hero_journey():
    W, H = 1080, 1080
    # Deep cinematic background
    img = gradient_bg(W, H, (16, 12, 18), (38, 22, 30)).convert("RGBA")
    # Glow on left side
    add_soft_glow(img, 200, 540, 400, (232, 168, 124), opacity=40)
    # Glow on right
    add_soft_glow(img, 900, 600, 350, (180, 80, 60), opacity=30)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    # Top label
    d.text((W // 2, 90), "ШЛЯХ ГЕРОЯ · 5 ЕТАПІВ", fill="#8C7A6B", anchor="mm", font=font(22, bold=True))
    # Big title
    d.text((W // 2, 180), "Як вийти з", fill="#F2E7DA", anchor="mm", font=font(54, bold=True))
    d.text((W // 2, 240), "функціональної депресії", fill="#E8A87C", anchor="mm", font=font(54, bold=True))

    # 5 stages — vertical path with connecting line + glowing dots
    stages = [
        ("01", "ЗАПЕРЕЧЕННЯ", "«У мене все нормально»"),
        ("02", "ВТРАТА СМАКУ", "Дії є — задоволення немає"),
        ("03", "СПРОБА «БІЛЬШЕ»", "Більше відпочинку, мотивації… без ефекту"),
        ("04", "ВПІЗНАВАННЯ", "Це не втома. Це порожнеча."),
        ("05", "ПОВОРОТ", "Чесна розмова з собою → перший крок"),
    ]
    line_x = 130  # path on left
    y_start = 360
    y_step = 100

    # Draw connecting vertical path
    d.line((line_x, y_start, line_x, y_start + y_step * (len(stages) - 1)), fill="#5C4842", width=3)

    for i, (num, title, sub) in enumerate(stages):
        cy = y_start + i * y_step
        # Glowing dot
        d.ellipse((line_x - 16, cy - 16, line_x + 16, cy + 16), fill="#E8A87C", outline="#FFCFA8", width=2)
        d.text((line_x, cy), num, fill="#1A1015", anchor="mm", font=font(15, bold=True))
        # Title
        d.text((line_x + 50, cy - 14), title, fill="#F2E7DA", anchor="lt", font=font(24, bold=True))
        # Sub
        d.text((line_x + 50, cy + 14), sub, fill="#A89684", anchor="lt", font=font(18, italic=True))

    # Bottom CTA
    d.line((W // 2 - 200, 970, W // 2 + 200, 970), fill="#E8A87C", width=2)
    d.text((W // 2, 1020), "ПОВНИЙ РОЗБІР НА YOUTUBE →", fill="#E8A87C", anchor="mm", font=font(22, bold=True))

    add_grain(img, intensity=6)
    out = OUT_DIR / "tpl9_hero_journey.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ TPL10: INTERACTIVE QUIZ CARD ============

def make_quiz_card():
    W, H = 1080, 1080
    # Warm cinematic
    img = gradient_bg(W, H, (28, 16, 22), (60, 32, 36)).convert("RGBA")
    add_soft_glow(img, 540, 200, 500, (255, 200, 160), opacity=35)
    add_soft_glow(img, 200, 900, 350, (180, 80, 60), opacity=40)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    # Big number label — playful
    d.text((W // 2, 120), "ТЕСТ · 3 ПИТАННЯ", fill="#FFB48C", anchor="mm", font=font(26, bold=True))
    d.text((W // 2, 180), "Хто ти зараз?", fill="#F2E7DA", anchor="mm", font=font(64, bold=True))

    # 3 question cards (preview only)
    cards = [
        ("01", "У понеділок ранок ти…", "перевіряєш плани VS втікаєш у скроли"),
        ("02", "Коли тебе хвалять — ти…", "берешся вище VS знецінюєш"),
        ("03", "Коли ти втомлена — ти…", "робиш паузу VS біжиш далі"),
    ]
    cy = 340
    for num, q, hint in cards:
        # Card outline
        d.rounded_rectangle((80, cy, W - 80, cy + 140), radius=20, outline="#E8A87C", width=2)
        # Inner accent block (number)
        d.rounded_rectangle((100, cy + 20, 180, cy + 120), radius=12, fill="#E8A87C")
        d.text((140, cy + 70), num, fill="#1A1015", anchor="mm", font=font(36, bold=True))
        # Question text
        d.text((210, cy + 40), q, fill="#F2E7DA", anchor="lt", font=font(28, bold=True))
        d.text((210, cy + 90), hint, fill="#C8AB94", anchor="lt", font=font(20, italic=True))
        cy += 165

    # Bottom CTA — pointed
    d.line((W // 2 - 150, 920, W // 2 + 150, 920), fill="#FFB48C", width=2)
    d.text((W // 2, 970), "ВІДПОВІДАЙ У ОПИТУВАННІ НИЖЧЕ", fill="#FFB48C", anchor="mm", font=font(22, bold=True))
    d.text((W // 2, 1015), "kozachkova.yuliia · збережи собі", fill="#8C7A6B", anchor="mm", font=font(18))

    add_grain(img, intensity=5)
    out = OUT_DIR / "tpl10_quiz_card.png"
    img.save(out, quality=95, optimize=True)
    return out


if __name__ == "__main__":
    p9 = make_hero_journey()
    p10 = make_quiz_card()
    print(f"✅ {p9.name}")
    print(f"✅ {p10.name}")
