"""Shared toolkit for the merch pipeline: palette, pixel drawing helpers, source sprites.

Imported by merch_designs.py, merch_mockups.py and build_merch.py.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, text3x5, text3x5_width  # noqa: E402
import raccoon as R  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(ROOT, 'assets', 'game')
SHOP = os.path.join(ROOT, 'assets', 'shop')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'press-start-2p-latin.woff2')
PREVIEW = os.environ.get('PREVIEW_DIR')
os.makedirs(SHOP, exist_ok=True)

S = 160  # mockup canvas (shown at 1x/2x/3x)
INK = hexrgb('#120c09')

PAL = {k: hexrgb(v) for k, v in {
    'cream': '#f6ead2', 'cream_sh': '#dccaa7', 'snow': '#ffffff',
    'red': '#c8323a', 'red_hi': '#e0534f', 'red_sh': '#8f2129',
    'pine': '#2f6b3f', 'pine_hi': '#4f9a5c', 'pine_sh': '#1b4429',
    'gold': '#f2c14e', 'gold_sh': '#b9862a', 'gold_hi': '#ffe39a',
    'brown': '#5a4330', 'brown_dk': '#33231a', 'tan': '#b29c72',
    'amber': '#f2a93b', 'amber_sh': '#a8620f',
}.items()}

# Garment colour ramps: (highlight, base, shadow, deep shadow)
RAMPS = {
    'black':   ('#3a322b', '#29221d', '#1b1612', '#120e0b'),
    'forest':  ('#3a7a55', '#2a5d40', '#1d432e', '#143120'),
    'oatmeal': ('#f4ecdc', '#e3d8c1', '#c9bca2', '#ad9f85'),
    'red':     ('#d9504f', '#b8323a', '#8a2229', '#64161d'),
    'green':   ('#3f8a52', '#2c6b3e', '#1d4c2b', '#12341d'),
    'heather': ('#7a7a7d', '#5f5e61', '#47464a', '#353437'),
    'cream':   ('#fbf4e6', '#efe4cf', '#d8cbb1', '#bcae93'),
    'navy':    ('#3a4c7a', '#2a3a62', '#1d2947', '#131c33'),
}


def ramp(name):
    return [hexrgb(c) for c in RAMPS[name]]


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------
def poly_mask(points, size=(S, S)):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).polygon(points, fill=255)
    return np.asarray(m) > 0


def ellipse_mask(box, size=(S, S)):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).ellipse(box, fill=255)
    return np.asarray(m) > 0


def rect_mask(box, size=(S, S)):
    m = np.zeros((size[1], size[0]), bool)
    x0, y0, x1, y1 = box
    m[y0:y1, x0:x1] = True
    return m


def shaded(mask, rp, light=(-1, -1), shadow_w=3):
    """Fill a mask with a 4-tone ramp lit from the top-left, plus a 1px ink outline."""
    hi, base, sh, deep = rp
    h, w = mask.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[mask] = base

    def shifted(dx, dy):
        s = np.zeros_like(mask)
        ys, ye = max(0, dy), h + min(0, dy)
        xs, xe = max(0, dx), w + min(0, dx)
        s[ys:ye, xs:xe] = mask[ys - dy:ye - dy, xs - dx:xe - dx]
        return s

    shadow = np.zeros_like(mask)
    for k in range(1, shadow_w + 1):
        shadow |= mask & ~shifted(-k, 0)
    shadow |= mask & ~shifted(0, -2) & ~shifted(0, -1) | (mask & ~shifted(0, -1))
    out[shadow] = sh
    out[mask & ~shifted(-1, 0) & ~shifted(0, -1)] = deep
    highlight = mask & (~shifted(1, 0) | ~shifted(0, 1))
    out[highlight & ~shadow] = hi
    return Image.fromarray(out, 'RGBA')


def ink_outline(img, color=INK):
    a = np.array(img)
    m = a[..., 3] > 0
    ring = np.zeros_like(m)
    ring[1:, :] |= m[:-1, :]
    ring[:-1, :] |= m[1:, :]
    ring[:, 1:] |= m[:, :-1]
    ring[:, :-1] |= m[:, 1:]
    ring &= ~m
    a[ring] = color
    return Image.fromarray(a, 'RGBA')


def clip(img, mask):
    a = np.array(img)
    a[~mask] = 0
    return Image.fromarray(a, 'RGBA')


def paste(dst, src, xy, mask=None):
    """Alpha-composite src at xy, optionally clipped to a canvas-sized mask."""
    if mask is not None:
        layer = Image.new('RGBA', dst.size, (0, 0, 0, 0))
        layer.alpha_composite(src, xy)
        layer = clip(layer, mask)
        dst.alpha_composite(layer)
    else:
        dst.alpha_composite(src, xy)


def paint_line(img, pts, color, width=1):
    d = ImageDraw.Draw(img)
    d.line(pts, fill=color, width=width)


def recolor(img, mapping):
    a = np.array(img)
    out = a.copy()
    for src, dst in mapping.items():
        m = (a[..., :3] == np.array(src[:3])).all(-1) & (a[..., 3] > 0)
        out[m] = dst
    return Image.fromarray(out, 'RGBA')


def solid(img, color):
    a = np.array(img)
    m = a[..., 3] > 0
    a[m] = color
    return Image.fromarray(a, 'RGBA')


def font_text(text, color, outline=None):
    font = ImageFont.truetype(FONT, 8)
    im = Image.new('RGBA', (len(text) * 8 + 4, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((2, 2), text, font=font, fill=color)
    im = im.crop(im.getbbox())
    if outline:
        pad = Image.new('RGBA', (im.width + 2, im.height + 2), (0, 0, 0, 0))
        pad.alpha_composite(im, (1, 1))
        im = ink_outline(pad, outline)
    return im


def tiny_text(text, color, spacing=1):
    w = text3x5_width(text, spacing)
    im = Image.new('RGBA', (w, 5), (0, 0, 0, 0))
    text3x5(im, 0, 0, text, color, spacing)
    return im


def centered(img, cx, y):
    return (int(cx - img.width // 2), int(y))


# ---------------------------------------------------------------------------
# source art from the game
# ---------------------------------------------------------------------------
_BOT = Image.open(os.path.join(GAME, 'bottles.png')).convert('RGBA')


def bottle(kind_row, col=0):
    f = _BOT.crop((col * 40, kind_row * 34, col * 40 + 40, kind_row * 34 + 34))
    return f.crop(f.getbbox())


# The character, straight from the rig that draws the game sprites (tools/raccoon.py).
FACE = R.face(True)                      # 26 x 29: the game's front-facing head, Santa hat
FACE_PLAIN = R.face(False)
FACE_SMALL = R.face(True, small=True)    # 18 x 21: the same face at icon size
HAT = R.hat('side')
WALK_SANTA = R.pose(R.side(0, hat=True))
STAND_SANTA = R.pose(R.front(0, hat=True))
SWIPE_SANTA = R.pose(R.front(3, hat=True))
CHEER_SANTA = R.pose(R.front(5, hat=True))
CLIMB_SANTA = R.pose(R.back(1, hat=True))
KO = R.pose(R.lying('ko'))
PASSED_OUT = R.pose(R.lying('ko', hat=True))     # X eyes, tongue out, hat hooked on a foot
RESERVE = bottle(4)


def passed_out_raccoon():
    return PASSED_OUT

SNOWFLAKE = ['...#...', '.#.#.#.', '..###..', '#######', '..###..', '.#.#.#.', '...#...']
TREE = ['...#...', '..###..', '.#####.', '..###..', '.#####.', '#######', '...#...']
MINI_BOTTLE = ['..#..', '..#..', '.###.', '#####', '#...#', '#####', '#####']


def glyph(rows, color):
    im = Image.new('RGBA', (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#':
                px[x, y] = color
    return im



def tiled(tile, w, h, ox=0, oy=0):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y in range(-tile.height + oy % tile.height, h, tile.height):
        for x in range(-tile.width + ox % tile.width, w, tile.width):
            im.alpha_composite(tile, (x, y))
    return im


def colours(img):
    """Distinct opaque colours in an image (used to validate yarn / thread limits)."""
    a = np.asarray(img.convert('RGBA'))
    m = a[..., 3] > 0
    return {tuple(int(v) for v in c) for c in a[..., :3][m].reshape(-1, 3)}


def flatten(img, bg):
    out = Image.new('RGBA', img.size, bg)
    out.alpha_composite(img)
    return out


def from_rows(rows, pal):
    """Build an image from character rows and a {char: rgba} palette ('.' = transparent)."""
    w = max(len(r) for r in rows)
    im = Image.new('RGBA', (w, len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in pal and pal[ch] is not None:
                px[x, y] = pal[ch]
    return im
