"""Generate distinctive placeholder avatars for the demo dataset.

Creates one PNG per employee listed in data/team.csv, saving them under
data/photos/. Avatars are deterministic initials-on-gradient designs with a
stylised face so that visual modes (mirror, pixelation, scrambled_face) remain
recognisable when the demo dataset is used.

Usage:
    uv run python tools/generate_demo_avatars.py
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 400
PALETTE = [
    ((239, 68, 68), (252, 165, 165)),    # red
    ((249, 115, 22), (253, 186, 116)),   # orange
    ((234, 179, 8), (253, 224, 71)),     # amber
    ((34, 197, 94), (134, 239, 172)),    # green
    ((20, 184, 166), (94, 234, 212)),    # teal
    ((14, 165, 233), (125, 211, 252)),   # sky
    ((99, 102, 241), (165, 180, 252)),   # indigo
    ((168, 85, 247), (216, 180, 254)),   # purple
    ((236, 72, 153), (249, 168, 212)),   # pink
    ((120, 113, 108), (214, 211, 209)),  # stone
]


def _pick_palette(seed: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    idx = int(hashlib.md5(seed.encode('utf-8')).hexdigest(), 16) % len(PALETTE)
    return PALETTE[idx]


def _vertical_gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    img = Image.new('RGB', (size, size), top)
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))
    return img


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        '/Library/Fonts/Arial Bold.ttf',
        'C:/Windows/Fonts/arialbd.ttf',
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_face(draw: ImageDraw.ImageDraw, accent: tuple[int, int, int]) -> None:
    # Face oval centred in the top two-thirds so it survives being cropped into
    # horizontal stripes by scrambled_face mode.
    cx, cy = SIZE // 2, SIZE // 2 - 30
    face_w, face_h = 180, 210
    draw.ellipse(
        (cx - face_w // 2, cy - face_h // 2, cx + face_w // 2, cy + face_h // 2),
        fill=(255, 229, 201),
        outline=(80, 60, 40),
        width=3,
    )
    # Eyes
    eye_y = cy - 20
    for ex in (cx - 35, cx + 35):
        draw.ellipse((ex - 10, eye_y - 7, ex + 10, eye_y + 7), fill=(50, 50, 50))
        draw.ellipse((ex - 3, eye_y - 3, ex + 3, eye_y + 3), fill=(255, 255, 255))
    # Mouth
    draw.arc(
        (cx - 30, cy + 20, cx + 30, cy + 60),
        start=0, end=180, fill=(160, 40, 60), width=4,
    )
    # Hair / hat (uses accent colour)
    draw.chord(
        (cx - 95, cy - 130, cx + 95, cy - 40),
        start=180, end=360, fill=accent,
    )


def _draw_initials(img: Image.Image, initials: str) -> None:
    draw = ImageDraw.Draw(img)
    font = _load_font(72)
    bbox = draw.textbbox((0, 0), initials, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (SIZE - w) // 2 - bbox[0]
    y = SIZE - h - 40 - bbox[1]
    # Pill background behind the initials for readability.
    pad_x, pad_y = 20, 10
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y),
        radius=18, fill=(0, 0, 0, 0),
    )
    # Simpler approach: solid dark pill, then white text.
    draw.rounded_rectangle(
        (x + bbox[0] - pad_x, y + bbox[1] - pad_y,
         x + bbox[0] + w + pad_x, y + bbox[1] + h + pad_y),
        radius=18, fill=(0, 0, 0),
    )
    draw.text((x, y), initials, font=font, fill=(255, 255, 255))


def make_avatar(first: str, last: str, out_path: Path) -> None:
    seed = f'{first}-{last}'.lower()
    top, bottom = _pick_palette(seed)
    img = _vertical_gradient(SIZE, top, bottom)
    draw = ImageDraw.Draw(img)
    accent = tuple(max(0, c - 40) for c in top)  # darker accent from top colour
    _draw_face(draw, accent)
    initials = (first[:1] + last[:1]).upper()
    _draw_initials(img, initials)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format='PNG', optimize=True)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    csv_path = root / 'demo' / 'team.csv'
    photos_dir = root / 'demo' / 'photos'
    with csv_path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            photo = row['photo'].lstrip('/')
            basename = Path(photo).name
            stem = Path(basename).stem
            target = photos_dir / f'{stem}.png'
            make_avatar(row['first_name'], row['last_name'], target)
            print(f'wrote {target.relative_to(root)}')


if __name__ == '__main__':
    main()
