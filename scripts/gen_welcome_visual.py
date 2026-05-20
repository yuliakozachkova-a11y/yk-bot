"""Quick welcome visual for test post."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "data" / "preview_visuals"
OUT.mkdir(parents=True, exist_ok=True)


def font(size, bold=False, italic=False):
    idx = (3 if italic else 2) if bold else (1 if italic else 0)
    return ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", size, index=idx)


def gradient_bg(w, h, top, bot):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def soft_glow(img, x, y, radius, color, opacity=60):
    o = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(o)
    od.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color + (opacity,))
    o = o.filter(ImageFilter.GaussianBlur(radius // 2))
    img.paste(o, (0, 0), o)


W, H = 1080, 1080
img = gradient_bg(W, H, (12, 10, 14), (38, 24, 32)).convert("RGBA")
soft_glow(img, 540, 540, 500, (255, 200, 160), opacity=60)
soft_glow(img, 200, 850, 280, (180, 80, 60), opacity=40)
img = img.convert("RGB")
d = ImageDraw.Draw(img)

# Top label
d.text((W // 2, 130), "ВЕЧІРНЄ НАГАДУВАННЯ", fill="#8C7A6B", anchor="mm", font=font(22, bold=True))

# Big quote — italic
d.text((W // 2, 380), "Бути собою —", fill="#F2E7DA", anchor="mm", font=font(64, italic=True))
d.text((W // 2, 470), "це не виклик.", fill="#F2E7DA", anchor="mm", font=font(64, italic=True))
d.text((W // 2, 610), "Це факт.", fill="#E8A87C", anchor="mm", font=font(80, bold=True))

# Soft message
d.text((W // 2, 770), "Дайте собі повітря 🤍", fill="#A89684", anchor="mm", font=font(30, italic=True))

# Bottom signature
d.line((W // 2 - 100, 950, W // 2 + 100, 950), fill="#E8A87C", width=2)
d.text((W // 2, 1000), "ЮЛІЯ КОЗАЧКОВА", fill="#E8A87C", anchor="mm", font=font(24, bold=True))

out_file = OUT / "test_welcome_19_25.png"
img.save(out_file, quality=95)
print(f"✅ {out_file}")
