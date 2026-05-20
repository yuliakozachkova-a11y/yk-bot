"""
Generate visual cards for preview posts (PIL — programmatic, no AI).
- mind_map_depression.png  — для поста про функціональну депресію
- checklist_value.png      — для поста-чек-листа про доводження цінності

These are illustrative MVP visuals. Later we can swap for NBP/AI-generated.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "preview_visuals"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Palette — теплая, женственная, как в её бренде
BG_DARK = "#0E0E10"           # глубокий чёрный
BG_GRAD = "#1A1417"            # с тёплым вином
TEXT_PRIMARY = "#F2E7DA"       # тёплый кремовый
TEXT_ACCENT = "#E8A87C"        # коралл
TEXT_DIM = "#8C7A6B"           # серо-бежевый
LINE = "#2E2530"               # карбон

# Fonts
def font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    """HelveticaNeue with Cyrillic support. Indices vary by weight."""
    # HelveticaNeue.ttc indices: 0=Regular, 1=Italic, 2=Bold, 3=BoldItalic, etc.
    path = "/System/Library/Fonts/HelveticaNeue.ttc"
    idx = 0
    if bold and italic:
        idx = 3
    elif bold:
        idx = 2
    elif italic:
        idx = 1
    try:
        return ImageFont.truetype(path, size, index=idx)
    except Exception:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=2 if bold else 0)
        except Exception:
            return ImageFont.load_default()


def make_gradient_bg(w: int, h: int) -> Image.Image:
    """Subtle radial-ish gradient from BG_DARK center to BG_GRAD edges."""
    img = Image.new("RGB", (w, h), BG_DARK)
    draw = ImageDraw.Draw(img)
    # Vertical gradient
    top_rgb = (14, 14, 16)
    bottom_rgb = (26, 20, 23)
    for y in range(h):
        t = y / h
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Wrap text into lines of ~max_chars."""
    words = text.split()
    lines = []
    current = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + 1 > max_chars and current:
            lines.append(" ".join(current))
            current = [w]
            cur_len = len(w)
        else:
            current.append(w)
            cur_len += len(w) + 1
    if current:
        lines.append(" ".join(current))
    return lines


# ============ 1. MIND MAP — Депресія ============

def make_mind_map_depression() -> Path:
    W, H = 1080, 1080
    img = make_gradient_bg(W, H)
    d = ImageDraw.Draw(img)

    # Top label
    label = "ЛЮСТЕРКО · ВИПУСК"
    d.text((W // 2, 60), label, fill=TEXT_DIM, anchor="mm", font=font(20, bold=True))

    # Center title
    title_lines = ["ФУНКЦІОНАЛЬНА", "ДЕПРЕСІЯ", "26-го РОКУ"]
    y = 130
    for line in title_lines:
        d.text((W // 2, y), line, fill=TEXT_PRIMARY, anchor="mm", font=font(56, bold=True))
        y += 70

    # Center oval marker
    cx, cy = W // 2, 410
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=TEXT_ACCENT)

    # 5 markers — vertical column under center, with dot bullets
    markers = [
        ("01", "Втома, що не проходить", "навіть після відпочинку"),
        ("02", "Сплощення емоцій", "ні гострої радості, ні горя"),
        ("03", "Внутрішнє: «треба більше мотивації»", "класична самопастка"),
        ("04", "Життя без смаку", "інерція замість бажань"),
        ("05", "Префронтальна кора виснажена", "від тотальної невизначеності"),
    ]
    y = 480
    for num, headline, sub in markers:
        # number badge
        d.rounded_rectangle((80, y - 6, 150, y + 50), radius=8, outline=TEXT_ACCENT, width=2)
        d.text((115, y + 22), num, fill=TEXT_ACCENT, anchor="mm", font=font(26, bold=True))
        # text
        d.text((180, y + 4), headline, fill=TEXT_PRIMARY, anchor="lt", font=font(28, bold=True))
        d.text((180, y + 36), sub, fill=TEXT_DIM, anchor="lt", font=font(22))
        y += 88

    # bottom CTA
    d.line((100, H - 100, W - 100, H - 100), fill=LINE, width=2)
    d.text((W // 2, H - 50), "ДИВИТИСЯ ВИПУСК НА YOUTUBE", fill=TEXT_ACCENT, anchor="mm", font=font(22, bold=True))

    out = OUT_DIR / "mind_map_depression.png"
    img.save(out, quality=95, optimize=True)
    return out


# ============ 2. CHECK-LIST — 5 кроків як перестати доводити цінність ============

def make_checklist_value() -> Path:
    W, H = 1080, 1350
    img = make_gradient_bg(W, H)
    d = ImageDraw.Draw(img)

    # Top label
    d.text((W // 2, 80), "ЧЕК-ЛИСТ · КОЗАЧКОВА", fill=TEXT_DIM, anchor="mm", font=font(22, bold=True))

    # Title (multi-line)
    title = "Як перестати\nдоводити свою\nцінність"
    y = 170
    for line in title.split("\n"):
        d.text((W // 2, y), line, fill=TEXT_PRIMARY, anchor="mm", font=font(64, bold=True))
        y += 80

    # 5 numbered points
    steps = [
        ("01", "Відмовся від потреби доводити", "Той, хто твій — не змусить тебе доводити нічого"),
        ("02", "Стань власним «ліфтом»", "Магнітизуй своє коло, не ганяйся за чужим"),
        ("03", "Розвивай здоровий професіоналізм", "Глибина у своїй темі — це твоя валюта"),
        ("04", "Встанови високі стандарти", "Вимоги — не жорсткість, а самоповага"),
        ("05", "Працюй над EQ", "Ким ти стаєш у конфлікті — там зрілість"),
    ]
    y = 540
    for num, headline, sub in steps:
        # accent left bar
        d.rectangle((70, y, 78, y + 95), fill=TEXT_ACCENT)
        # number
        d.text((110, y + 4), num, fill=TEXT_ACCENT, anchor="lt", font=font(34, bold=True))
        # headline
        d.text((180, y + 4), headline, fill=TEXT_PRIMARY, anchor="lt", font=font(30, bold=True))
        # sub
        sub_lines = wrap_text(sub, 56)
        sy = y + 44
        for sl in sub_lines:
            d.text((180, sy), sl, fill=TEXT_DIM, anchor="lt", font=font(22))
            sy += 30
        y += 130

    # bottom signature
    d.line((100, H - 110, W - 100, H - 110), fill=LINE, width=2)
    d.text((W // 2, H - 60), "kozachkova.yuliia · збережи собі", fill=TEXT_ACCENT, anchor="mm", font=font(22, bold=True))

    out = OUT_DIR / "checklist_value.png"
    img.save(out, quality=95, optimize=True)
    return out


if __name__ == "__main__":
    p1 = make_mind_map_depression()
    p2 = make_checklist_value()
    print(f"✅ {p1}")
    print(f"✅ {p2}")
