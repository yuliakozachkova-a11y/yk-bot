"""Modular visual kit — registry of renderable templates.

Each template is a function: (params: dict, out_path: Path) -> Path
Register a new template by adding it to TEMPLATES at the bottom.

Brand palette (Yulia Kozachkova): cinematic navy → wine → gold accents.
All templates are 1080x1080 PNG, ready for Telegram bot.send_photo().

Usage:
    from bot.visual_kit import render
    path = render("hero_journey", {
        "badge": "ШЛЯХ ГЕРОЯ · 5 ЕТАПІВ",
        "title_line1": "Як вийти з",
        "title_line2": "функціональної депресії",
        "stages": [("01", "ЗАПЕРЕЧЕННЯ", "«У мене все нормально»"), ...],
        "cta": "ПОВНИЙ РОЗБІР НА YOUTUBE →",
    })
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ---------- palettes ----------

PALETTE_CINEMATIC = {
    "bg_top": (16, 12, 18),
    "bg_bottom": (38, 22, 30),
    "glow_warm": (232, 168, 124),
    "glow_wine": (180, 80, 60),
    "text": "#F2E7DA",
    "accent": "#E8A87C",
    "dim": "#8C7A6B",
    "line": "#5C4842",
}

PALETTE_WARM = {
    "bg_top": (44, 24, 30),
    "bg_bottom": (88, 44, 38),
    "glow_warm": (255, 200, 160),
    "glow_wine": (180, 80, 60),
    "text": "#F4E6D2",
    "accent": "#FFB48C",
    "dim": "#C8A89A",
    "line": "#705048",
}

PALETTE_LIGHT = {
    "bg_top": (242, 234, 222),
    "bg_bottom": (224, 212, 198),
    "glow_warm": (232, 168, 124),
    "glow_wine": (168, 88, 56),
    "text": "#1A1A1F",
    "accent": "#A85838",
    "dim": "#6B5A4F",
    "line": "#A09080",
}


# ---------- low-level helpers ----------

def _font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = (3 if italic else 2) if bold else (1 if italic else 0)
    try:
        return ImageFont.truetype(path, size, index=idx)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def _gradient_bg(w: int, h: int, palette: dict) -> Image.Image:
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


def _glow(img: Image.Image, x: int, y: int, radius: int, color: tuple, opacity: int = 60) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (opacity,))
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius // 2))
    img.paste(blurred, (0, 0), blurred)


def _grain(img: Image.Image, intensity: int = 6) -> None:
    import random
    px = img.load()
    w, h = img.size
    for _ in range(w * h // 40):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        r, g, b = px[x, y]
        n = random.randint(-intensity, intensity)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))


def _wrap(text: str, max_chars: int) -> list[str]:
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


# ============ TEMPLATE: hero_journey (5-stage path) ============

def make_hero_journey(params: dict, out_path: Path) -> Path:
    """params: badge, title_line1, title_line2, stages (list of 5 tuples), cta (optional)"""
    W, H = 1080, 1080
    p = PALETTE_CINEMATIC
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 200, 540, 400, p["glow_warm"], opacity=40)
    _glow(img, 900, 600, 350, p["glow_wine"], opacity=30)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((W // 2, 90), params["badge"], fill=p["dim"], anchor="mm", font=_font(22, bold=True))
    d.text((W // 2, 180), params["title_line1"], fill=p["text"], anchor="mm", font=_font(54, bold=True))
    d.text((W // 2, 240), params["title_line2"], fill=p["accent"], anchor="mm", font=_font(54, bold=True))

    stages = list(params["stages"])
    if len(stages) != 5:
        raise ValueError("hero_journey needs exactly 5 stages")
    line_x, y_start, y_step = 130, 360, 100
    d.line((line_x, y_start, line_x, y_start + y_step * 4), fill=p["line"], width=3)
    for i, (num, title, sub) in enumerate(stages):
        cy = y_start + i * y_step
        d.ellipse((line_x - 16, cy - 16, line_x + 16, cy + 16), fill=p["accent"], outline="#FFCFA8", width=2)
        d.text((line_x, cy), num, fill="#1A1015", anchor="mm", font=_font(15, bold=True))
        d.text((line_x + 50, cy - 14), title, fill=p["text"], anchor="lt", font=_font(24, bold=True))
        d.text((line_x + 50, cy + 14), sub, fill=p["dim"], anchor="lt", font=_font(18, italic=True))

    cta = params.get("cta", "ПОВНИЙ РОЗБІР НА YOUTUBE →")
    d.line((W // 2 - 200, 970, W // 2 + 200, 970), fill=p["accent"], width=2)
    d.text((W // 2, 1020), cta, fill=p["accent"], anchor="mm", font=_font(22, bold=True))

    _grain(img, 6)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ============ TEMPLATE: checklist (1-7 items) ============

def make_checklist(params: dict, out_path: Path) -> Path:
    """params: badge, title, items (list of 5-7 strings), cta (optional)"""
    W, H = 1080, 1080
    p = PALETTE_WARM
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 540, 200, 500, p["glow_warm"], opacity=35)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((W // 2, 80), params["badge"], fill=p["accent"], anchor="mm", font=_font(22, bold=True))
    title_lines = _wrap(params["title"], 24)
    y = 150
    for line in title_lines[:2]:
        d.text((W // 2, y), line, fill=p["text"], anchor="mm", font=_font(48, bold=True))
        y += 60

    items = list(params["items"])[:7]
    item_y = max(y + 40, 320)
    box_h = 70
    for i, item in enumerate(items):
        cy = item_y + i * box_h
        # circle marker
        d.ellipse((80, cy - 18, 120, cy + 18), fill=p["accent"], outline="#FFCFA8", width=2)
        d.text((100, cy), str(i + 1), fill="#2C181E", anchor="mm", font=_font(20, bold=True))
        # text
        item_lines = _wrap(item, 36)
        d.text((150, cy), item_lines[0], fill=p["text"], anchor="lm", font=_font(22, bold=False))

    cta = params.get("cta")
    if cta:
        d.line((W // 2 - 180, 970, W // 2 + 180, 970), fill=p["accent"], width=2)
        d.text((W // 2, 1020), cta, fill=p["accent"], anchor="mm", font=_font(22, bold=True))

    _grain(img, 5)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ============ TEMPLATE: quote_hero (large quote + author) ============

def make_quote_hero(params: dict, out_path: Path) -> Path:
    """params: quote (str), author (str, default 'Юлія Козачкова'), source (optional, e.g. 'Ген Грошей')"""
    W, H = 1080, 1080
    p = PALETTE_CINEMATIC
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 540, 540, 600, p["glow_warm"], opacity=35)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    # giant quote mark
    d.text((100, 200), "“", fill=p["accent"], anchor="lm", font=_font(220, bold=True))

    quote = params["quote"]
    lines = _wrap(quote, 26)
    line_height = 70
    total_h = len(lines) * line_height
    y = H // 2 - total_h // 2
    for line in lines:
        d.text((W // 2, y), line, fill=p["text"], anchor="mm", font=_font(46, bold=True))
        y += line_height

    author = params.get("author", "Юлія Козачкова")
    source = params.get("source")
    bottom_y = H - 130
    d.line((W // 2 - 120, bottom_y, W // 2 + 120, bottom_y), fill=p["accent"], width=2)
    d.text((W // 2, bottom_y + 35), f"— {author}", fill=p["accent"], anchor="mm", font=_font(24, bold=True))
    if source:
        d.text((W // 2, bottom_y + 70), source, fill=p["dim"], anchor="mm", font=_font(20, italic=True))

    _grain(img, 6)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ============ TEMPLATE: live_announce (Tuesday 8:30 reading) ============

def make_live_announce(params: dict, out_path: Path) -> Path:
    """params:
        episode_num (int) — 'Зустріч №N'
        book_title (str)
        date_label (str) — 'Сьогодні' / 'Завтра' / '02.06'
        time_label (str) — '08:30'
        url (str, optional)
    """
    W, H = 1080, 1080
    p = PALETTE_CINEMATIC
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 540, 300, 500, p["glow_warm"], opacity=50)
    _glow(img, 540, 900, 400, p["glow_wine"], opacity=35)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    # LIVE pill
    pill_w, pill_h = 180, 60
    pill_x = (W - pill_w) // 2
    pill_y = 90
    d.rounded_rectangle((pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius=30, fill=p["accent"])
    d.text((W // 2, pill_y + pill_h // 2), "● ЕФІР", fill="#1A1015", anchor="mm", font=_font(26, bold=True))

    # Big date+time
    d.text((W // 2, 240), params["date_label"], fill=p["text"], anchor="mm", font=_font(44, bold=True))
    d.text((W // 2, 340), params["time_label"], fill=p["accent"], anchor="mm", font=_font(140, bold=True))
    d.text((W // 2, 440), "за київським часом", fill=p["dim"], anchor="mm", font=_font(20, italic=True))

    # Divider
    d.line((W // 2 - 260, 510, W // 2 + 260, 510), fill=p["line"], width=2)

    # Episode + book
    d.text((W // 2, 580), f"Жива книга. Зустріч №{params['episode_num']}", fill=p["text"], anchor="mm", font=_font(34, bold=True))
    book_lines = _wrap(f"«{params['book_title']}»", 32)
    y = 640
    for line in book_lines[:2]:
        d.text((W // 2, y), line, fill=p["accent"], anchor="mm", font=_font(38, bold=True))
        y += 50

    # Description
    d.text((W // 2, 800), "Читаю книгу й ділюся думками між сторінками.", fill=p["dim"], anchor="mm", font=_font(22, italic=True))
    d.text((W // 2, 840), "Прямо зараз — без монтажу, без сценарію.", fill=p["dim"], anchor="mm", font=_font(22, italic=True))

    # Bottom CTA
    d.line((W // 2 - 200, 950, W // 2 + 200, 950), fill=p["accent"], width=2)
    d.text((W // 2, 1000), "ДИВИТИСЬ НА YOUTUBE →", fill=p["accent"], anchor="mm", font=_font(24, bold=True))

    _grain(img, 6)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ============ TEMPLATE: trichlen (three-word manifesto) ============

def make_trichlen(params: dict, out_path: Path) -> Path:
    """params: words (list of 3 strings), subtitle (optional), source (optional)"""
    W, H = 1080, 1080
    p = PALETTE_CINEMATIC
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 540, 540, 700, p["glow_warm"], opacity=45)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    words = list(params["words"])[:3]
    if len(words) < 3:
        raise ValueError("trichlen needs 3 words")

    # Top accent
    d.line((W // 2 - 80, 200, W // 2 + 80, 200), fill=p["accent"], width=3)

    # Three big words stacked
    y_centers = [340, 540, 740]
    for word, cy in zip(words, y_centers):
        d.text((W // 2, cy), word.upper(), fill=p["text"], anchor="mm", font=_font(96, bold=True))
        d.text((W // 2 + 50, cy + 50), ".", fill=p["accent"], anchor="mm", font=_font(96, bold=True))

    # Bottom accent + subtitle
    d.line((W // 2 - 80, 880, W // 2 + 80, 880), fill=p["accent"], width=3)
    sub = params.get("subtitle")
    if sub:
        d.text((W // 2, 940), sub, fill=p["dim"], anchor="mm", font=_font(24, italic=True))
    source = params.get("source", "@kozachkova_yuliia")
    d.text((W // 2, 1020), source, fill=p["dim"], anchor="mm", font=_font(20))

    _grain(img, 5)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ============ TEMPLATE: book_excerpt ============

def make_book_excerpt(params: dict, out_path: Path) -> Path:
    """params: chapter (str), excerpt (str), book_title (str)"""
    W, H = 1080, 1080
    p = PALETTE_WARM
    img = _gradient_bg(W, H, p).convert("RGBA")
    _glow(img, 200, 540, 500, p["glow_warm"], opacity=30)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    # Top — book label
    d.text((W // 2, 80), f"📖  «{params['book_title']}»", fill=p["accent"], anchor="mm", font=_font(22, bold=True))

    # Chapter
    chapter_lines = _wrap(params.get("chapter", ""), 30)
    y = 160
    for line in chapter_lines[:2]:
        d.text((W // 2, y), line, fill=p["text"], anchor="mm", font=_font(36, bold=True))
        y += 50

    d.line((W // 2 - 120, y + 30, W // 2 + 120, y + 30), fill=p["accent"], width=2)

    # Excerpt
    excerpt = params["excerpt"]
    excerpt_lines = _wrap(excerpt, 32)
    start_y = max(y + 100, H // 2 - len(excerpt_lines) * 20)
    for i, line in enumerate(excerpt_lines[:10]):
        d.text((W // 2, start_y + i * 50), line, fill=p["text"], anchor="mm", font=_font(28, italic=True))

    # Bottom
    d.line((W // 2 - 180, 970, W // 2 + 180, 970), fill=p["accent"], width=2)
    d.text((W // 2, 1020), params.get("cta", "ЧИТАТИ ПОВНІСТЮ →"), fill=p["accent"], anchor="mm", font=_font(22, bold=True))

    _grain(img, 5)
    img.save(out_path, quality=95, optimize=True)
    return out_path


# ---------- registry ----------

TEMPLATES: dict[str, Callable[[dict, Path], Path]] = {
    "hero_journey": make_hero_journey,
    "checklist": make_checklist,
    "quote_hero": make_quote_hero,
    "live_announce": make_live_announce,
    "trichlen": make_trichlen,
    "book_excerpt": make_book_excerpt,
}


DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "preview_visuals"


def render(template: str, params: dict, out_path: Path | None = None, filename_hint: str | None = None) -> Path:
    """Render a template by name. Returns path to PNG.
    If out_path not provided, a timestamped filename is used in DEFAULT_OUT_DIR.
    """
    if template not in TEMPLATES:
        raise KeyError(f"Unknown template '{template}'. Available: {list(TEMPLATES.keys())}")
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    if out_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        hint = filename_hint or template
        out_path = DEFAULT_OUT_DIR / f"{hint}_{ts}.png"
    return TEMPLATES[template](params, out_path)


def list_templates() -> list[str]:
    return list(TEMPLATES.keys())
