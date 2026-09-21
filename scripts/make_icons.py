#!/usr/bin/env python3
"""
AI Daily News - app icon generator

Design: "open book"
  ink-black background + an open cream book seen from the front, "A" on the
  left page and "I" on the right page, the right page's corner curling as it
  turns (the site turns issues like book pages) + a red bookmark ribbon.

Output (icons/ at the project root):
  icon-512.png / icon-192.png      -- standard (purpose=any)
  maskable-512.png                 -- maskable (content kept inside the center safe zone)
  apple-touch-icon.png (180)       -- iOS
  favicon-32.png                   -- browser tab
  icon.svg                         -- vector (favicon + manifest any)

Re-runnable: python3 scripts/make_icons.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

# Brand colors (match assets/style.css)
INK = (26, 26, 26)          # #1a1a1a ink black
CREAM = (255, 254, 248)     # #fffef8 cream paper
PAGE_SHADE = (236, 228, 212)  # #ece4d4 page shading near the spine
SEPIA = (139, 90, 43)       # #8b5a2b sepia
BRICK = (192, 57, 43)       # #c0392b bookmark ribbon

FONT_CANDIDATES = [
    "C:/Windows/Fonts/georgiab.ttf",                              # Windows
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",        # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",      # Linux
]

SUPERSAMPLE = 4  # draw large, then downscale for smooth edges

# Geometry in a 512 x 512 design space (the SVG below uses the same numbers)
LEFT_PAGE = [(256, 176), (70, 146), (70, 380), (256, 410)]
RIGHT_PAGE = [(256, 176), (442, 146), (442, 318), (380, 388), (256, 410)]
SPINE_SHADE_L = [(256, 176), (226, 171), (226, 405), (256, 410)]
SPINE_SHADE_R = [(256, 176), (286, 171), (286, 405), (256, 410)]
CURL = [(442, 318), (380, 388), (398, 336)]           # underside of the turning corner
CURL_SHADOW = [(442, 318), (398, 336), (380, 388), (388, 346)]
RIBBON = [(242, 150), (270, 150), (270, 244), (256, 230), (242, 244)]
SPINE = [(256, 176), (256, 410)]
LETTER_A = (164, 282)   # centers of the letters
LETTER_I = (350, 282)
LETTER_SIZE = 172


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_icon(size: int, maskable: bool = False) -> Image.Image:
    """Draw one icon. With maskable=True the artwork shrinks to stay inside the central 80% safe zone."""
    big = size * SUPERSAMPLE
    img = Image.new("RGB", (big, big), INK)
    d = ImageDraw.Draw(img)

    scale = big / 512 * (0.78 if maskable else 1.0)
    offset = (big - 512 * scale) / 2

    def pt(p):
        return (offset + p[0] * scale, offset + p[1] * scale)

    def poly(points, fill):
        d.polygon([pt(p) for p in points], fill=fill)

    poly(LEFT_PAGE, CREAM)
    poly(RIGHT_PAGE, CREAM)
    # Soft shading along the spine
    poly(SPINE_SHADE_L, PAGE_SHADE)
    poly(SPINE_SHADE_R, PAGE_SHADE)
    d.line([pt(SPINE[0]), pt(SPINE[1])], fill=SEPIA, width=max(1, round(4 * scale)))
    # Turning corner
    poly(CURL_SHADOW, SEPIA)
    poly(CURL, PAGE_SHADE)
    # Bookmark ribbon
    poly(RIBBON, BRICK)

    font = _font(round(LETTER_SIZE * scale))
    for letter, center in (("A", LETTER_A), ("I", LETTER_I)):
        cx, cy = pt(center)
        d.text((cx, cy), letter, font=font, fill=INK, anchor="mm")

    return img.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="AI Daily News">
  <rect width="512" height="512" fill="#1a1a1a"/>
  <polygon points="256,176 70,146 70,380 256,410" fill="#fffef8"/>
  <polygon points="256,176 442,146 442,318 380,388 256,410" fill="#fffef8"/>
  <polygon points="256,176 226,171 226,405 256,410" fill="#ece4d4"/>
  <polygon points="256,176 286,171 286,405 256,410" fill="#ece4d4"/>
  <line x1="256" y1="176" x2="256" y2="410" stroke="#8b5a2b" stroke-width="4"/>
  <polygon points="442,318 398,336 380,388 388,346" fill="#8b5a2b"/>
  <polygon points="442,318 380,388 398,336" fill="#ece4d4"/>
  <polygon points="242,150 270,150 270,244 256,230 242,244" fill="#c0392b"/>
  <text x="164" y="282" text-anchor="middle" dominant-baseline="central"
        font-family="Georgia, 'Times New Roman', serif" font-weight="bold" font-size="172" fill="#1a1a1a">A</text>
  <text x="350" y="282" text-anchor="middle" dominant-baseline="central"
        font-family="Georgia, 'Times New Roman', serif" font-weight="bold" font-size="172" fill="#1a1a1a">I</text>
</svg>
"""


def main() -> None:
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(project_dir, "icons")
    os.makedirs(out_dir, exist_ok=True)

    for name, size, maskable in [
        ("icon-512.png", 512, False),
        ("icon-192.png", 192, False),
        ("apple-touch-icon.png", 180, False),
        ("favicon-32.png", 32, False),
        ("maskable-512.png", 512, True),
    ]:
        draw_icon(size, maskable).save(os.path.join(out_dir, name), "PNG")
        print(f"✓ {name} ({size}×{size})")

    with open(os.path.join(out_dir, "icon.svg"), "w", encoding="utf-8") as f:
        f.write(SVG)
    print("✓ icon.svg")

    print(f"\n✓ Icons generated in {out_dir}")


if __name__ == "__main__":
    main()
