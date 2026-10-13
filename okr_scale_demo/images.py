"""Small PIL helpers generating the demo pictures (avatars and reward images)."""
import base64
import io
import math

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - Pillow is a dependency of Odoo
    Image = None

NAVY = (17, 52, 106)
BLUE = (23, 139, 236)
WHITE = (255, 255, 255)

AVATAR_COLORS = [
    (17, 52, 106), (23, 139, 236), (0, 150, 136), (233, 115, 41), (142, 68, 173),
    (39, 174, 96), (211, 84, 0), (41, 128, 185), (192, 57, 43), (22, 160, 133),
    (243, 156, 18), (52, 73, 94),
]

FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
    'DejaVuSans-Bold.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]


def _font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _encode(image):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return base64.b64encode(buffer.getvalue())


def _text_center(draw, box, text, font, fill=WHITE):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    width, height = right - left, bottom - top
    x = box[0] + (box[2] - box[0] - width) / 2 - left
    y = box[1] + (box[3] - box[1] - height) / 2 - top
    draw.text((x, y), text, font=font, fill=fill)


def initials(name):
    words = [w for w in name.replace('BS.', '').split() if w]
    if len(words) >= 2:
        return (words[-2][0] + words[-1][0]).upper()
    return (words[0][:2] if words else '?').upper()


def avatar(name, index=0, size=256):
    """Colored disc with the initials of ``name`` (base64 PNG), or False without Pillow."""
    if Image is None:
        return False
    color = AVATAR_COLORS[index % len(AVATAR_COLORS)]
    image = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(image)
    _text_center(draw, (0, 0, size, size), initials(name), _font(int(size * 0.4)))
    return _encode(image)


def _gradient(size, start, end):
    image = Image.new('RGB', (size, size), start)
    draw = ImageDraw.Draw(image)
    for y in range(size):
        for_ratio = y / size
        color = tuple(int(start[i] + (end[i] - start[i]) * for_ratio) for i in range(3))
        draw.line([(0, y), (size, y)], fill=color)
    return image


def _icon_coffee(draw, cx, cy, s):
    draw.rounded_rectangle([cx - s, cy - s * 0.6, cx + s * 0.6, cy + s * 0.9], radius=s * 0.25, fill=WHITE)
    draw.arc([cx + s * 0.25, cy - s * 0.25, cx + s * 1.1, cy + s * 0.55], -90, 90, fill=WHITE, width=int(s * 0.2))
    for dx in (-0.6, -0.2, 0.2):
        draw.arc([cx + s * dx - s * 0.15, cy - s * 1.35, cx + s * dx + s * 0.15, cy - s * 0.75], 90, 270,
                 fill=WHITE, width=int(s * 0.1))
    draw.rounded_rectangle([cx - s * 1.25, cy + s * 0.95, cx + s * 0.85, cy + s * 1.1], radius=s * 0.07, fill=WHITE)


def _icon_calendar(draw, cx, cy, s):
    draw.rounded_rectangle([cx - s, cy - s * 0.8, cx + s, cy + s], radius=s * 0.18, fill=WHITE)
    draw.rectangle([cx - s, cy - s * 0.8, cx + s, cy - s * 0.35], fill=(255, 210, 90))
    for dx in (-0.5, 0.5):
        draw.rounded_rectangle([cx + s * dx - s * 0.08, cy - s * 1.05, cx + s * dx + s * 0.08, cy - s * 0.55],
                               radius=s * 0.06, fill=NAVY)
    for row in range(3):
        for col in range(4):
            x = cx - s * 0.75 + col * s * 0.5
            y = cy - s * 0.15 + row * s * 0.38
            draw.rectangle([x, y, x + s * 0.25, y + s * 0.22], fill=BLUE if (row, col) != (1, 2) else (233, 115, 41))


def _icon_course(draw, cx, cy, s):
    draw.polygon([(cx - s * 1.2, cy - s * 0.3), (cx, cy - s * 0.9), (cx + s * 1.2, cy - s * 0.3), (cx, cy + s * 0.3)],
                 fill=WHITE)
    draw.polygon([(cx - s * 0.7, cy), (cx + s * 0.7, cy), (cx + s * 0.7, cy + s * 0.65), (cx, cy + s * 0.95),
                  (cx - s * 0.7, cy + s * 0.65)], fill=WHITE)
    draw.line([(cx + s * 1.0, cy - s * 0.2), (cx + s * 1.0, cy + s * 0.7)], fill=(255, 210, 90), width=int(s * 0.1))
    draw.ellipse([cx + s * 0.88, cy + s * 0.65, cx + s * 1.12, cy + s * 0.9], fill=(255, 210, 90))


def _icon_headphones(draw, cx, cy, s):
    draw.arc([cx - s, cy - s * 1.0, cx + s, cy + s * 1.0], 180, 360, fill=WHITE, width=int(s * 0.22))
    for side in (-1, 1):
        x = cx + side * s * 0.9
        draw.rounded_rectangle([x - s * 0.28, cy - s * 0.1, x + s * 0.28, cy + s * 0.9], radius=s * 0.2, fill=WHITE)


def _icon_dinner(draw, cx, cy, s):
    draw.ellipse([cx - s * 0.8, cy - s * 0.8, cx + s * 0.8, cy + s * 0.8], fill=WHITE)
    draw.ellipse([cx - s * 0.55, cy - s * 0.55, cx + s * 0.55, cy + s * 0.55], outline=BLUE, width=int(s * 0.06))
    # fork
    x = cx - s * 1.15
    draw.rectangle([x - s * 0.05, cy - s * 0.2, x + s * 0.05, cy + s * 0.9], fill=WHITE)
    for dx in (-0.15, 0, 0.15):
        draw.rectangle([x + s * dx - s * 0.03, cy - s * 0.8, x + s * dx + s * 0.03, cy - s * 0.2], fill=WHITE)
    # knife
    x = cx + s * 1.15
    draw.polygon([(x - s * 0.08, cy - s * 0.85), (x + s * 0.1, cy - s * 0.6), (x + s * 0.08, cy + s * 0.1),
                  (x - s * 0.08, cy + s * 0.1)], fill=WHITE)
    draw.rectangle([x - s * 0.06, cy + s * 0.1, x + s * 0.06, cy + s * 0.9], fill=WHITE)


def _icon_shirt(draw, cx, cy, s):
    draw.polygon([(cx - s * 0.35, cy - s), (cx - s * 1.1, cy - s * 0.6), (cx - s * 0.8, cy - s * 0.1),
                  (cx - s * 0.6, cy - s * 0.25), (cx - s * 0.6, cy + s), (cx + s * 0.6, cy + s),
                  (cx + s * 0.6, cy - s * 0.25), (cx + s * 0.8, cy - s * 0.1), (cx + s * 1.1, cy - s * 0.6),
                  (cx + s * 0.35, cy - s)], fill=WHITE)
    draw.arc([cx - s * 0.35, cy - s * 1.25, cx + s * 0.35, cy - s * 0.7], 0, 180, fill=NAVY, width=int(s * 0.1))
    _text_center(draw, (cx - s * 0.6, cy - s * 0.2, cx + s * 0.6, cy + s * 0.6), 'DMAG', _font(int(s * 0.32)), fill=NAVY)


def _icon_tooth(draw, cx, cy, s):
    draw.polygon([(cx - s * 0.9, cy - s * 0.6), (cx - s * 0.5, cy - s), (cx, cy - s * 0.75), (cx + s * 0.5, cy - s),
                  (cx + s * 0.9, cy - s * 0.6), (cx + s * 0.75, cy + s * 0.2), (cx + s * 0.5, cy + s),
                  (cx + s * 0.2, cy + s), (cx, cy + s * 0.35), (cx - s * 0.2, cy + s), (cx - s * 0.5, cy + s),
                  (cx - s * 0.75, cy + s * 0.2)], fill=WHITE)
    for angle in range(0, 360, 45):
        x = cx + s * 1.2 * math.cos(math.radians(angle))
        y = cy - s * 0.9 + s * 0.3 * math.sin(math.radians(angle))
        if angle in (0, 45, 315):
            draw.ellipse([x - s * 0.07, y - s * 0.07, x + s * 0.07, y + s * 0.07], fill=(255, 210, 90))


def _icon_gift(draw, cx, cy, s):
    draw.rectangle([cx - s, cy - s * 0.3, cx + s, cy + s], fill=WHITE)
    draw.rectangle([cx - s * 1.1, cy - s * 0.6, cx + s * 1.1, cy - s * 0.25], fill=WHITE)
    draw.rectangle([cx - s * 0.15, cy - s * 0.6, cx + s * 0.15, cy + s], fill=(233, 115, 41))
    draw.ellipse([cx - s * 0.7, cy - s * 1.1, cx - s * 0.05, cy - s * 0.55], outline=(233, 115, 41), width=int(s * 0.12))
    draw.ellipse([cx + s * 0.05, cy - s * 1.1, cx + s * 0.7, cy - s * 0.55], outline=(233, 115, 41), width=int(s * 0.12))


ICONS = {
    'coffee': _icon_coffee,
    'calendar': _icon_calendar,
    'course': _icon_course,
    'headphones': _icon_headphones,
    'dinner': _icon_dinner,
    'shirt': _icon_shirt,
    'tooth': _icon_tooth,
    'gift': _icon_gift,
}

GRADIENTS = {
    'coffee': ((111, 78, 55), (23, 139, 236)),
    'calendar': (NAVY, (39, 174, 96)),
    'course': (NAVY, (142, 68, 173)),
    'headphones': ((34, 34, 59), BLUE),
    'dinner': ((192, 57, 43), (243, 156, 18)),
    'shirt': (NAVY, BLUE),
    'tooth': ((0, 150, 136), BLUE),
    'gift': ((142, 68, 173), (233, 115, 41)),
}


def reward_image(icon, label, size=512):
    """Gradient card with a simple drawn icon and a caption (base64 PNG)."""
    if Image is None:
        return False
    start, end = GRADIENTS.get(icon, (NAVY, BLUE))
    image = _gradient(size, start, end)
    draw = ImageDraw.Draw(image)
    # decorative circles
    draw.ellipse([size * 0.62, -size * 0.18, size * 1.18, size * 0.38], outline=(255, 255, 255), width=3)
    draw.ellipse([-size * 0.2, size * 0.7, size * 0.3, size * 1.2], outline=(255, 255, 255), width=3)
    ICONS.get(icon, _icon_gift)(draw, size / 2, size * 0.42, size * 0.2)
    draw.rounded_rectangle([size * 0.08, size * 0.74, size * 0.92, size * 0.9], radius=size * 0.05,
                           fill=(255, 255, 255))
    font_size = int(size * 0.07)
    font = _font(font_size)
    while draw.textlength(label, font=font) > size * 0.8 and font_size > 14:
        font_size -= 2
        font = _font(font_size)
    _text_center(draw, (size * 0.08, size * 0.74, size * 0.92, size * 0.9), label, font, fill=NAVY)
    _text_center(draw, (size * 0.05, size * 0.03, size * 0.4, size * 0.12), 'DMAG', _font(int(size * 0.05)))
    return _encode(image)
