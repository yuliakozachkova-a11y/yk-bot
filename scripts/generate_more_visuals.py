"""
Additional visuals — variety templates, NEVER reuse exact same composition.
- #19 fraza_weekend «Світ не винен» — spotlight quote on dark warm gradient
- #16 marketing_quote alt — split layout (cite left, accent bar right)
- (#17, #18 already exist from V1/V2)
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


# ============ #19 — «Світ не винен» — spotlight on deep dark ============

def make_world_not_indebted():
    W, H = 1080, 1080
    img = gradient_bg(W, H, (8, 10, 18), (30, 18, 28))
    d = ImageDraw.Draw(img)

    # Top label
    d.text((W // 2, 100), "ДУМКА ТИЖНЯ · СУБОТА", fill="#7A6B6F", anchor="mm", font=font(22, bold=True))

    # Big quote — centered
    d.text((W // 2, 360), "Світ був до вас", fill="#F2E7DA", anchor="mm", font=font(62, bold=True))
    d.text((W // 2, 440), "і нічого вам", fill="#F2E7DA", anchor="mm", font=font(62, bold=True))
    d.text((W // 2, 520), "не винен.", fill="#E8A87C", anchor="mm", font=font(62, bold=True))

    # Subtitle
    d.text((W // 2, 660), "Це не жорстокість. Це звільнення.", fill="#A89684", anchor="mm", font=font(28, italic=True))

    # Action triplet
    d.text((W // 2, 770), "Ти нічого не доводиш — ти створюєш.", fill="#D4C8B8", anchor="mm", font=font(26))
    d.text((W // 2, 815), "Ти нічого не чекаєш — ти дієш.", fill="#D4C8B8", anchor="mm", font=font(26))

    # Footer signature
    d.line((W // 2 - 100, 950, W // 2 + 100, 950), fill="#E8A87C", width=2)
    d.text((W // 2, 1000), "ЮЛІЯ КОЗАЧКОВА", fill="#E8A87C", anchor="mm", font=font(24, bold=True))

    out = OUT_DIR / "tpl6_world_not_indebted.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ #16 — «Зручна чи Цінна» — split layout ============

def make_convenient_vs_valuable():
    W, H = 1080, 1080
    img = gradient_bg(W, H, (18, 14, 18), (40, 28, 32))
    d = ImageDraw.Draw(img)

    # Top label
    d.text((W // 2, 90), "ПИТАННЯ ВЕЧОРА · ЧЕТВЕР", fill="#8C7A6B", anchor="mm", font=font(22, bold=True))

    # Two big columns: "ЗРУЧНА" vs "ЦІННА"
    mid = W // 2

    # left column
    d.text((mid - 280, 320), "ЗРУЧНА", fill="#8C7A6B", anchor="mm", font=font(72, bold=True))
    d.text((mid - 280, 405), "тебе беруть", fill="#A89684", anchor="mm", font=font(24, italic=True))
    d.text((mid - 280, 440), "тому що нікого", fill="#A89684", anchor="mm", font=font(24, italic=True))

    # vertical divider
    d.line((mid, 220, mid, 540), fill="#5C4842", width=2)

    # right column — accent
    d.text((mid + 280, 320), "ЦІННА", fill="#E8A87C", anchor="mm", font=font(72, bold=True))
    d.text((mid + 280, 405), "тебе обирають", fill="#F2E7DA", anchor="mm", font=font(24, italic=True))
    d.text((mid + 280, 440), "серед інших", fill="#F2E7DA", anchor="mm", font=font(24, italic=True))

    # Bottom message
    d.text((W // 2, 700), "Повага не народжується з жертви.", fill="#F2E7DA", anchor="mm", font=font(32, bold=True))
    d.text((W // 2, 750), "Вона починається з моменту,", fill="#F2E7DA", anchor="mm", font=font(32, bold=True))
    d.text((W // 2, 800), "коли ти обираєш себе.", fill="#E8A87C", anchor="mm", font=font(32, bold=True))

    # Footer
    d.line((W // 2 - 100, 940, W // 2 + 100, 940), fill="#E8A87C", width=2)
    d.text((W // 2, 990), "KOZACHKOVA.YULIIA", fill="#8C7A6B", anchor="mm", font=font(20, bold=True))

    out = OUT_DIR / "tpl7_convenient_vs_valuable.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ #20 — «Субота — про вибір» — minimal poetic ============

def make_saturday_choice():
    W, H = 1080, 1080
    # Light warm palette for contrast
    img = gradient_bg(W, H, (235, 225, 210), (210, 195, 178))
    d = ImageDraw.Draw(img)

    # Top tiny label
    d.text((W // 2, 100), "СУБОТА · 17:30", fill="#8C7A6B", anchor="mm", font=font(20, bold=True))

    # Vertical poetry — left-aligned, ragged
    lines = [
        ("Субота —", "#1A1A1F", 64, True),
        ("про вибір.", "#A85838", 64, True),
        ("", None, 20, False),
        ("Не між «треба»", "#3A3530", 38, False),
        ("і «хочу».", "#3A3530", 38, False),
        ("", None, 20, False),
        ("А між «жити чуже»", "#3A3530", 38, False),
        ("і «жити своє».", "#A85838", 38, True),
    ]
    y = 290
    for text, color, sz, b in lines:
        if not text:
            y += sz
            continue
        d.text((140, y), text, fill=color, anchor="lt", font=font(sz, bold=b))
        y += sz + 12

    # Bottom signature
    d.text((W - 100, 1010), "ЮЛІЯ КОЗАЧКОВА", fill="#A85838", anchor="rb", font=font(20, bold=True))

    out = OUT_DIR / "tpl8_saturday_choice.png"
    img.save(out, quality=95, optimize=True)
    return out


if __name__ == "__main__":
    p1 = make_world_not_indebted()
    p2 = make_convenient_vs_valuable()
    p3 = make_saturday_choice()
    print(f"✅ {p1.name}")
    print(f"✅ {p2.name}")
    print(f"✅ {p3.name}")
