"""YouTube hero-journey mind-map generator (TPL9 parameterised).

Render a 1080x1080 cinematic card with a 5-stage vertical path:
- badge label at top
- 2-line title
- 5 stages with glowing dots + connecting line
- CTA at the bottom

Used by scheduled YouTube digest posts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageFilter


def _font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = (3 if italic else 2) if bold else (1 if italic else 0)
    try:
        return ImageFont.truetype(path, size, index=idx)
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def _gradient_bg(w: int, h: int, top_rgb: tuple, bot_rgb: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h), top_rgb)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _add_soft_glow(img: Image.Image, x: int, y: int, radius: int, color: tuple, opacity: int = 80) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (opacity,))
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius // 2))
    img.paste(blurred, (0, 0), blurred)


def _add_grain(img: Image.Image, intensity: int = 6) -> None:
    import random
    px = img.load()
    w, h = img.size
    for _ in range(w * h // 40):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        r, g, b = px[x, y]
        n = random.randint(-intensity, intensity)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))


def make_mindmap(
    out_path: Path | str,
    badge: str,
    title_line1: str,
    title_line2: str,
    stages: Iterable[tuple[str, str, str]],
    cta_text: str = "ПОВНИЙ РОЗБІР НА YOUTUBE →",
) -> Path:
    """Render a hero-journey mind-map card.

    stages = list of 5 tuples: (number "01", uppercase TITLE, italic subtitle)
    """
    W, H = 1080, 1080
    img = _gradient_bg(W, H, (16, 12, 18), (38, 22, 30)).convert("RGBA")
    _add_soft_glow(img, 200, 540, 400, (232, 168, 124), opacity=40)
    _add_soft_glow(img, 900, 600, 350, (180, 80, 60), opacity=30)
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)

    d.text((W // 2, 90), badge, fill="#8C7A6B", anchor="mm", font=_font(22, bold=True))
    d.text((W // 2, 180), title_line1, fill="#F2E7DA", anchor="mm", font=_font(54, bold=True))
    d.text((W // 2, 240), title_line2, fill="#E8A87C", anchor="mm", font=_font(54, bold=True))

    stages_list = list(stages)
    if len(stages_list) != 5:
        raise ValueError("Need exactly 5 stages for hero-journey card")

    line_x = 130
    y_start = 360
    y_step = 100

    d.line((line_x, y_start, line_x, y_start + y_step * (len(stages_list) - 1)), fill="#5C4842", width=3)

    for i, (num, title, sub) in enumerate(stages_list):
        cy = y_start + i * y_step
        d.ellipse((line_x - 16, cy - 16, line_x + 16, cy + 16), fill="#E8A87C", outline="#FFCFA8", width=2)
        d.text((line_x, cy), num, fill="#1A1015", anchor="mm", font=_font(15, bold=True))
        d.text((line_x + 50, cy - 14), title, fill="#F2E7DA", anchor="lt", font=_font(24, bold=True))
        d.text((line_x + 50, cy + 14), sub, fill="#A89684", anchor="lt", font=_font(18, italic=True))

    d.line((W // 2 - 200, 970, W // 2 + 200, 970), fill="#E8A87C", width=2)
    d.text((W // 2, 1020), cta_text, fill="#E8A87C", anchor="mm", font=_font(22, bold=True))

    _add_grain(img, intensity=6)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95, optimize=True)
    return out_path
