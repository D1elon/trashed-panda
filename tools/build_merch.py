#!/usr/bin/env python3
"""Holiday merch: pixel designs, pixel product mockups and print-ready files.

    python3 tools/build_merch.py

Every design is built from the game's own pixel art (the raccoon sprites, the brand
face, the bottles, Press Start 2P lettering), so the merch and the game share one
visual language. Outputs:

    assets/shop/<product>-<variant>.png   128x128 pixel mockups (shown at 2x / 3x)
    assets/shop/<product>-design.png      the flat design at native resolution
    merch/print-files/...                 integer-upscaled, print-ready PNGs (300 dpi)
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, text3x5, text3x5_width  # noqa: E402
from build_ui import raccoon_face  # noqa: E402
from build_sprites import art, HAT_SIDE, HAT_PAL as HAT_SIDE_PAL  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(ROOT, 'assets', 'game')
SHOP = os.path.join(ROOT, 'assets', 'shop')
PRINT = os.path.join(ROOT, 'merch', 'print-files')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'press-start-2p-latin.woff2')
PREVIEW = os.environ.get('PREVIEW_DIR')
os.makedirs(SHOP, exist_ok=True)
os.makedirs(PRINT, exist_ok=True)

S = 128  # mockup canvas
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
_RAC = Image.open(os.path.join(GAME, 'raccoon.png')).convert('RGBA')
_BOT = Image.open(os.path.join(GAME, 'bottles.png')).convert('RGBA')


def rac(col, row):
    f = _RAC.crop((col * 80, row * 66, col * 80 + 80, row * 66 + 66))
    return f.crop(f.getbbox())


def bottle(kind_row, col=0):
    f = _BOT.crop((col * 40, kind_row * 34, col * 40 + 40, kind_row * 34 + 34))
    return f.crop(f.getbbox())


FACE = raccoon_face(True)            # 18 x 22, Santa hat
FACE_PLAIN = raccoon_face(False)
WALK_SANTA = rac(0, 5)
STAND_SANTA = rac(0, 8)
KO = rac(1, 4)
KO_SANTA = rac(1, 9)
FALL_SANTA = rac(2, 8)
RESERVE = bottle(4)
LYING_HAT = art(HAT_SIDE, HAT_SIDE_PAL).rotate(28, expand=True, resample=Image.NEAREST)


def passed_out_raccoon():
    """X-eyed, feet up, with the Santa hat knocked off beside its head."""
    im = Image.new('RGBA', (KO.width + 12, KO.height + 4), (0, 0, 0, 0))
    im.alpha_composite(KO, (0, 4))
    im.alpha_composite(LYING_HAT, (KO.width - 8, KO.height - LYING_HAT.height + 6))
    return im.crop(im.getbbox())

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


# ---------------------------------------------------------------------------
# designs (native pixel art, transparent background)
# ---------------------------------------------------------------------------
def design_naughty(fg=PAL['cream']):
    """NAUGHTY / brand face / LIST."""
    top = font_text('NAUGHTY', fg)
    bot = font_text('LIST', PAL['red_hi'])
    w = max(top.width, bot.width, FACE.width) + 2
    h = top.height + FACE.height + bot.height + 8
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.alpha_composite(top, centered(top, w / 2, 0))
    im.alpha_composite(FACE, centered(FACE, w / 2, top.height + 3))
    im.alpha_composite(bot, centered(bot, w / 2, top.height + FACE.height + 6))
    return im


def design_wordmark():
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    sub = tiny_text('ASHLAND VA', PAL['cream_sh'])
    w = max(logo.width, sub.width) + 2
    h = FACE.height + logo.height + sub.height + 6
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.alpha_composite(FACE, centered(FACE, w / 2, 0))
    im.alpha_composite(logo, centered(logo, w / 2, FACE.height + 1))
    im.alpha_composite(sub, centered(sub, w / 2, FACE.height + logo.height + 4))
    return im


def design_reserve():
    im = Image.new('RGBA', (44, 52), (0, 0, 0, 0))
    im.alpha_composite(RESERVE, centered(RESERVE, 22, 4))
    for (x, y, big) in ((8, 8, True), (35, 14, True), (10, 30, False), (36, 30, False), (22, 1, False)):
        im.putpixel((x, y), PAL['snow'])
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                im.putpixel((x + dx, y + dy), PAL['gold'])
    t1 = tiny_text('HOLIDAY', PAL['gold'])
    t2 = tiny_text('RESERVE', PAL['gold'])
    im.alpha_composite(t1, centered(t1, 22, 37))
    im.alpha_composite(t2, centered(t2, 22, 44))
    return im


def design_passed_out(text_color=PAL['brown_dk']):
    ko = passed_out_raccoon()
    im = Image.new('RGBA', (ko.width + 4, ko.height + 12), (0, 0, 0, 0))
    im.alpha_composite(ko, (0, 12))
    z = glyph(['###', '..#', '.#.', '#..', '###'], text_color)
    zb = glyph(['####', '...#', '..#.', '.#..', '####'], text_color)
    im.alpha_composite(z, (ko.width - 18, 6))
    im.alpha_composite(zb, (ko.width - 12, 0))
    return im


def design_drop(w=92):
    """Falling through the ceiling: a drop-ceiling band with a broken tile, the raccoon
    tumbling head-first, its Santa hat flying off, speed lines and tile chunks."""
    body = rac(0, 3).transpose(Image.FLIP_TOP_BOTTOM)    # standing pose, upside down
    hat = art(HAT_SIDE, HAT_SIDE_PAL).rotate(-20, expand=True, resample=Image.NEAREST)
    h = body.height + 26
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tile, tbar, dark = hexrgb('#dedad1'), hexrgb('#a9a69d'), hexrgb('#1a1412')
    d.rectangle((0, 0, w - 1, 9), fill=tile)
    for x in range(w // 2 % 16, w, 16):
        d.line((x, 0, x, 9), fill=tbar)
    d.line((0, 9, w - 1, 9), fill=hexrgb('#8f8c84'))
    hx0, hx1 = w // 2 - 12, w // 2 + 12
    d.rectangle((hx0, 0, hx1, 7), fill=dark)
    for i, x in enumerate(range(hx0, hx1 + 1)):
        y = 8 + (1 if i % 5 in (1, 2) else 0) + (1 if i % 7 == 3 else 0)
        d.line((x, 7, x, y), fill=dark)
    for x in (hx0 + 4, hx0 + 10, hx1 - 5):
        d.line((x, 8, x, 11), fill=hexrgb('#d9c79a'))
    rx = w // 2 - body.width // 2 + 4
    ry = 22
    cream = hexrgb('#f6ead2')
    for (x, y0, y1) in ((rx + 8, 13, 19), (rx + 20, 12, 20), (rx + body.width - 12, 14, 19), (w // 2 + 2, 12, 17)):
        d.line((x, y0, x, y1), fill=cream)
    for (x, y, c) in ((rx - 6, 20, tile), (rx + body.width, 28, tile), (rx + body.width - 4, 44, tbar), (rx - 9, 38, tbar)):
        d.rectangle((x, y, x + 2, y + 1), fill=c)
    im = ink_outline(im)
    im.alpha_composite(body, (rx, ry))
    im.alpha_composite(hat, (hx1 + 3, 12))
    return im


def design_choices():
    t1 = tiny_text('POOR LIFE', PAL['red'])
    t2 = tiny_text('CHOICES', PAL['red'])
    ko = passed_out_raccoon()
    w = max(ko.width, t1.width) + 2
    im = Image.new('RGBA', (w, ko.height + 16), (0, 0, 0, 0))
    im.alpha_composite(t1, centered(t1, w / 2, 0))
    im.alpha_composite(t2, centered(t2, w / 2, 7))
    im.alpha_composite(ko, centered(ko, w / 2, 15))
    return im


def design_greetings():
    t1 = font_text("SEASON'S", PAL['red'])
    t2 = font_text('GREETINGS', PAL['pine'])
    s1 = tiny_text('FROM THE', PAL['brown'])
    s2 = tiny_text('BATHROOM FLOOR', PAL['brown'])
    ko = passed_out_raccoon()
    w = max(t2.width, ko.width) + 2
    im = Image.new('RGBA', (w, t1.height + t2.height + ko.height + 24), (0, 0, 0, 0))
    y = 0
    im.alpha_composite(t1, centered(t1, w / 2, y)); y += t1.height + 2
    im.alpha_composite(t2, centered(t2, w / 2, y)); y += t2.height + 4
    im.alpha_composite(ko, centered(ko, w / 2, y)); y += ko.height + 3
    im.alpha_composite(s1, centered(s1, w / 2, y)); y += 7
    im.alpha_composite(s2, centered(s2, w / 2, y))
    return im


def sweater_knit(w, h, base, accent, light, dark):
    """Fair-isle knit chart: snowflake + tree yoke, zigzags, centre face, bottle band.
    Limited to five yarn colours so it can be knitted for real."""
    im = Image.new('RGBA', (w, h), base)
    px = im.load()
    # zigzag bands
    def zigzag(y, col):
        for x in range(w):
            k = x % 6
            yy = y + (k if k < 3 else 6 - k)
            px[x, yy] = col
    def dots(y, col, step=4, off=0):
        for x in range(off, w, step):
            px[x, y] = col
    dots(1, light, 4, 1)
    zigzag(3, light)
    # snowflake / tree band
    for i, x in enumerate(range(2, w - 6, 12)):
        g = glyph(SNOWFLAKE if i % 2 == 0 else TREE, light if i % 2 == 0 else accent)
        im.alpha_composite(g, (x, 9))
    zigzag(18, light)
    dots(23, light, 4, 3)
    # centre motif: face in a cream medallion framed by bottles
    cy = 30
    med = Image.new('RGBA', (26, 30), (0, 0, 0, 0))
    ImageDraw.Draw(med).ellipse((0, 0, 25, 29), fill=light)
    im.alpha_composite(med, centered(med, w / 2, cy))
    im.alpha_composite(FACE, centered(FACE, w / 2, cy + 4))
    for side in (-1, 1):
        b = glyph(MINI_BOTTLE, light)
        for k in range(2):
            im.alpha_composite(b, (int(w / 2 + side * (19 + k * 9) - 2), cy + 12))
        sf = glyph(SNOWFLAKE, accent)
        im.alpha_composite(sf, (int(w / 2 + side * 24 - 3), cy + 1))
    # lower bands
    yb = cy + 34
    dots(yb, light, 4, 1)
    zigzag(yb + 2, light)
    for x in range(1, w - 4, 8):
        im.alpha_composite(glyph(MINI_BOTTLE, accent if (x // 8) % 2 else light), (x, yb + 9))
    zigzag(yb + 17, light)
    return im


# ---------------------------------------------------------------------------
# mockups
# ---------------------------------------------------------------------------
def new():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))


TEE_PTS = [(50, 22), (29, 27), (9, 44), (17, 60), (30, 53), (30, 121), (98, 121), (98, 53), (111, 60), (119, 44), (99, 27), (78, 22), (73, 29), (64, 32), (55, 29)]


def mock_tee(color, design):
    rp = ramp(color)
    mask = poly_mask(TEE_PTS)
    im = shaded(mask, rp)
    # collar rib + inner neck
    neck = poly_mask([(50, 22), (55, 29), (64, 32), (73, 29), (78, 22), (73, 25), (64, 27), (55, 25)])
    im.alpha_composite(shaded(neck, [rp[3]] * 4))
    paint_line(im, [(52, 23), (56, 28), (64, 31), (72, 28), (76, 23)], rp[0])
    # sleeve hems + body hem stitching
    paint_line(im, [(12, 50), (19, 58)], rp[2])
    paint_line(im, [(116, 50), (109, 58)], rp[2])
    for x in range(32, 97, 2):
        im.putpixel((x, 117), rp[2])
    # soft folds
    paint_line(im, [(33, 60), (36, 90)], rp[2])
    paint_line(im, [(95, 60), (92, 92)], rp[2])
    paint_line(im, [(58, 108), (64, 118)], rp[2])
    paste(im, design, centered(design, 64, 40), mask)
    return ink_outline(im)


def mock_sweater(color, knit_colors):
    rp = ramp(color)
    body = poly_mask([(31, 24), (50, 20), (55, 26), (64, 28), (73, 26), (78, 20), (97, 24), (99, 112), (29, 112)])
    lsl = poly_mask([(32, 24), (17, 31), (6, 97), (19, 101), (31, 50)])
    rsl = poly_mask([(96, 24), (111, 31), (122, 97), (109, 101), (97, 50)])
    im = new()
    for m in (lsl, rsl):
        im.alpha_composite(shaded(m, rp))
    im.alpha_composite(shaded(body, rp))
    # knit chart on the body
    knit = sweater_knit(68, 88, rp[1], *knit_colors)
    paste(im, knit, (30, 24), body)
    # knit texture: alternating column tint gives the ribbed look
    a = np.array(im)
    m = (body | lsl | rsl)
    cols = np.zeros_like(m)
    cols[:, ::2] = True
    tint = m & cols
    a[tint, :3] = (a[tint, :3].astype(int) * 0.92).astype(np.uint8)
    im = Image.fromarray(a, 'RGBA')
    # ribbed cuffs, hem, collar
    def rib(mask_box_pts):
        rm = poly_mask(mask_box_pts)
        r = shaded(rm, [rp[2], rp[2], rp[3], rp[3]], shadow_w=1)
        ra = np.array(r)
        ra[:, ::2][rm[:, ::2]] = rp[3]
        return Image.fromarray(ra, 'RGBA')
    im.alpha_composite(rib([(29, 104), (99, 104), (99, 112), (29, 112)]))
    im.alpha_composite(rib([(6, 92), (19, 95), (19, 101), (6, 97)]))
    im.alpha_composite(rib([(122, 92), (109, 95), (109, 101), (122, 97)]))
    im.alpha_composite(rib([(50, 20), (55, 26), (64, 28), (73, 26), (78, 20), (74, 21), (64, 24), (54, 21)]))
    return ink_outline(im)


def rib_panel(pts, rp):
    rm = poly_mask(pts)
    r = shaded(rm, [rp[2], rp[2], rp[3], rp[3]], shadow_w=1)
    ra = np.array(r)
    cols = np.zeros_like(rm)
    cols[:, ::2] = True
    ra[rm & cols] = rp[3]
    return Image.fromarray(ra, 'RGBA')


def mock_hoodie(color, design):
    rp = ramp(color)
    im = new()
    hood = poly_mask([(41, 30), (43, 13), (52, 5), (76, 5), (85, 13), (87, 30)])
    im.alpha_composite(shaded(hood, [rp[1], rp[2], rp[3], rp[3]]))
    lsl = poly_mask([(32, 26), (17, 33), (6, 99), (19, 103), (31, 52)])
    rsl = poly_mask([(96, 26), (111, 33), (122, 99), (109, 103), (97, 52)])
    body = poly_mask([(31, 26), (48, 22), (80, 22), (97, 26), (99, 116), (29, 116)])
    for m in (lsl, rsl, body):
        im.alpha_composite(shaded(m, rp))
    # hood opening + drawstrings
    opening = poly_mask([(50, 22), (54, 13), (64, 10), (74, 13), (78, 22), (70, 28), (58, 28)])
    im.alpha_composite(shaded(opening, [rp[3]] * 4))
    for x0, x1 in ((58, 57), (70, 71)):
        paint_line(im, [(x0, 28), (x1, 48)], PAL['cream_sh'])
        im.putpixel((x1, 49), PAL['gold_sh'])
        im.putpixel((x1, 50), PAL['gold_sh'])
    # kangaroo pocket
    pk = [(42, 86), (86, 86), (91, 106), (37, 106)]
    paint_line(im, pk + [pk[0]], rp[2])
    paint_line(im, [(43, 87), (85, 87)], rp[0])
    for m in ([(29, 108), (99, 108), (99, 116), (29, 116)], [(6, 93), (19, 96), (19, 103), (6, 99)], [(122, 93), (109, 96), (109, 103), (122, 99)]):
        im.alpha_composite(rib_panel(m, rp))
    paste(im, design, centered(design, 64, 34), body)
    return ink_outline(im)


def mock_ornament(design):
    im = new()
    cx, cy, r = 64, 72, 46
    ball = ellipse_mask((cx - r, cy - r, cx + r, cy + r))
    ys, xs = np.mgrid[0:S, 0:S]
    d = np.hypot(xs - (cx - 18), ys - (cy - 20)) / (r * 1.75)
    tones = [hexrgb('#fffdf8'), hexrgb('#f3ecdf'), hexrgb('#e2d8c6'), hexrgb('#c9bda8')]
    a = np.zeros((S, S, 4), np.uint8)
    for i, t in enumerate((0.0, 0.33, 0.62, 0.9)):
        a[ball & (d >= t)] = tones[i]
    im = Image.fromarray(a, 'RGBA')
    top = cy - design.height // 2 + 2 if design.width < 80 else cy - r + 8
    paste(im, design, centered(design, cx, top), ball)
    # glossy highlight
    for (x, y) in ((36, 46), (37, 44), (39, 42), (41, 40), (44, 39), (35, 49), (34, 52)):
        im.putpixel((x, y), hexrgb('#ffffff'))
    im = ink_outline(im)
    # metal cap + ribbon loop
    cap = shaded(rect_mask((55, 20, 73, 29)), [PAL['gold_hi'], PAL['gold'], PAL['gold_sh'], hexrgb('#7d5a1c')], shadow_w=2)
    ca = np.array(cap)
    for x in range(57, 72, 3):
        ca[21:28, x] = PAL['gold_sh']
    im.alpha_composite(ink_outline(Image.fromarray(ca, 'RGBA')))
    rib = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(rib)
    dr.line((63, 3, 63, 19), fill=PAL['red'], width=2)
    dr.ellipse((58, 0, 69, 9), outline=PAL['red'], width=2)
    im.alpha_composite(ink_outline(rib))
    return im


SOCK_PTS = [(22, 8), (50, 8), (50, 72), (78, 84), (83, 95), (79, 106), (68, 111), (34, 111), (24, 103), (22, 90)]


def sock(rp, face=True, dx=0, dy=0):
    pts = [(x + dx, y + dy) for x, y in SOCK_PTS]
    m = poly_mask(pts)
    im = shaded(m, rp)
    a = np.array(im)
    # tail-ring stripes
    for y0 in (18, 26, 62, 70):
        band = m & (np.arange(S)[:, None] >= y0 + dy) & (np.arange(S)[:, None] < y0 + dy + 4)
        a[band] = PAL['brown']
        a[band & (np.arange(S)[:, None] == y0 + dy)] = hexrgb('#6e553e')
    # heel + toe
    heel = m & ellipse_mask((16 + dx, 88 + dy, 44 + dx, 116 + dy))
    toe = m & ellipse_mask((62 + dx, 84 + dy, 90 + dx, 116 + dy))
    a[heel] = PAL['red']
    a[toe] = PAL['red']
    a[(heel | toe) & ~np.roll(m, -2, axis=0)] = PAL['red_sh']
    im = Image.fromarray(a, 'RGBA')
    im.alpha_composite(rib_panel([(22 + dx, 8 + dy), (50 + dx, 8 + dy), (50 + dx, 15 + dy), (22 + dx, 15 + dy)], rp))
    if face:
        paste(im, FACE, (27 + dx, 36 + dy), m)
    return ink_outline(im)


def mock_socks():
    im = new()
    im.alpha_composite(sock(ramp('oatmeal'), face=True, dx=30, dy=6))
    im.alpha_composite(sock(ramp('cream'), face=True, dx=4, dy=2))
    return im


def mock_beanie(color):
    rp = ramp(color)
    im = new()
    pom = ellipse_mask((50, 6, 78, 32))
    pim = shaded(pom, ramp('cream'))
    pa = np.array(pim)
    rng = np.random.default_rng(4)
    for _ in range(60):
        x, y = rng.integers(50, 78), rng.integers(6, 32)
        if pom[y, x]:
            pa[y, x] = ramp('cream')[2]
    im.alpha_composite(ink_outline(Image.fromarray(pa, 'RGBA')))
    dome = ellipse_mask((20, 24, 108, 112)) & (np.arange(S)[:, None] < 72)
    dim = shaded(dome, rp)
    da = np.array(dim)
    cols = np.zeros_like(dome)
    cols[:, ::3] = True
    da[dome & cols & ~np.roll(~dome, 1, axis=1)] = rp[2]
    im.alpha_composite(ink_outline(Image.fromarray(da, 'RGBA')))
    im.alpha_composite(ink_outline(rib_panel([(17, 66), (111, 66), (111, 98), (17, 98)], [rp[0], rp[1], rp[1], rp[2]])))
    patch = rect_mask((50, 69, 78, 96))
    pi = shaded(patch, [PAL['cream'], PAL['cream'], PAL['cream_sh'], PAL['cream_sh']], shadow_w=1)
    im.alpha_composite(ink_outline(pi, PAL['brown_dk']))
    for x in range(51, 78, 2):
        im.putpixel((x, 70), PAL['brown'])
        im.putpixel((x, 95), PAL['brown'])
    im.alpha_composite(FACE_PLAIN, centered(FACE_PLAIN, 64, 75))
    return im


def mock_mug(design):
    im = new()
    white = [hexrgb('#ffffff'), hexrgb('#f1ece2'), hexrgb('#d9d1c2'), hexrgb('#bdb3a2')]
    handle = ellipse_mask((84, 44, 116, 96)) & ~ellipse_mask((92, 54, 108, 86))
    im.alpha_composite(ink_outline(shaded(handle, white, shadow_w=2)))
    body = rect_mask((18, 30, 96, 110)) | ellipse_mask((18, 102, 95, 118))
    bim = shaded(body, white, shadow_w=4)
    paste(bim, design, centered(design, 57, 46), body)
    im.alpha_composite(ink_outline(bim))
    rim = ellipse_mask((18, 23, 95, 37))
    im.alpha_composite(ink_outline(shaded(rim, white, shadow_w=1)))
    inside = ellipse_mask((22, 25, 91, 35))
    im.alpha_composite(shaded(inside, [hexrgb('#6b4a32'), hexrgb('#4a2f1d'), hexrgb('#3a2414'), hexrgb('#2a190d')], shadow_w=1))
    for (x, y) in ((24, 44), (24, 46), (24, 48), (24, 50), (25, 52)):
        im.putpixel((x, y), hexrgb('#ffffff'))
    return im


def sticker(art_img, border=2):
    w, h = art_img.width + border * 2 + 2, art_img.height + border * 2 + 2
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    base.alpha_composite(art_img, (border, border))
    m = np.asarray(base)[..., 3] > 0
    grown = m.copy()
    for _ in range(border):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    out = np.zeros((h, w, 4), np.uint8)
    shadow = np.roll(np.roll(grown, 1, axis=0), 1, axis=1) & ~grown
    out[shadow] = (0, 0, 0, 70)
    out[grown] = hexrgb('#ffffff')
    im = Image.fromarray(out, 'RGBA')
    im.alpha_composite(art_img, (border, border))
    return im


def mock_stickers():
    im = new()
    sheet = rect_mask((10, 6, 118, 122))
    im.alpha_composite(ink_outline(shaded(sheet, [hexrgb('#fbf6ec'), hexrgb('#efe6d2'), hexrgb('#d8cbb1'), hexrgb('#c4b597')], shadow_w=2)))
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    items = [
        (sticker(logo), (64, 10)),
        (sticker(FACE), (30, 47)),
        (sticker(RESERVE), (63, 44)),
        (sticker(bottle(1)), (94, 46)),
        (sticker(passed_out_raccoon()), (64, 82)),
    ]
    for st, (cx, y) in items:
        im.alpha_composite(st, centered(st, cx, y))
    return im


def wrap_tile(bg=PAL['red']):
    t = Image.new('RGBA', (48, 48), bg)
    t.alpha_composite(FACE, (3, 2))
    t.alpha_composite(FACE, (27, 26))
    sf = glyph(SNOWFLAKE, PAL['cream'])
    t.alpha_composite(sf, (32, 6))
    t.alpha_composite(sf, (8, 32))
    b = glyph(MINI_BOTTLE, PAL['gold'])
    t.alpha_composite(b, (40, 16))
    t.alpha_composite(b, (16, 40))
    t.alpha_composite(b, (22, 12))
    for (x, y) in ((44, 2), (2, 26), (26, 46), (46, 40), (20, 30)):
        t.putpixel((x, y), PAL['cream'])
    return t


def tiled(tile, w, h, ox=0, oy=0):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y in range(-tile.height + oy % tile.height, h, tile.height):
        for x in range(-tile.width + ox % tile.width, w, tile.width):
            im.alpha_composite(tile, (x, y))
    return im


def mock_wrap():
    im = new()
    tile = wrap_tile()
    sheet = rect_mask((10, 6, 118, 96))
    sim = tiled(tile, S, S, 10, 6)
    im.alpha_composite(ink_outline(clip(sim, sheet)))
    roll = rect_mask((8, 92, 118, 118))
    ri = clip(tiled(tile, S, S, 4, 2), roll)
    ra = np.array(ri)
    ra[92:95, 8:118][roll[92:95, 8:118]] = np.clip(ra[92:95, 8:118][roll[92:95, 8:118]].astype(int) + 40, 0, 255).astype(np.uint8)
    ra[112:118, 8:118][roll[112:118, 8:118]] = (ra[112:118, 8:118][roll[112:118, 8:118]].astype(int) * 0.6).astype(np.uint8)
    im.alpha_composite(ink_outline(Image.fromarray(ra, 'RGBA')))
    cap = ellipse_mask((112, 92, 124, 118))
    im.alpha_composite(ink_outline(shaded(cap, ramp('cream'), shadow_w=1)))
    for (x, y) in ((117, 101), (118, 102), (119, 104), (118, 106), (116, 107), (115, 105)):
        im.putpixel((x, y), PAL['cream_sh'])
    return im


def mock_cards(design):
    im = new()
    env = rect_mask((56, 36, 122, 108))
    ei = shaded(env, [PAL['red_hi'], PAL['red'], PAL['red_sh'], hexrgb('#64161d')], shadow_w=2)
    paint_line(ei, [(57, 37), (89, 66), (121, 37)], PAL['red_sh'])
    im.alpha_composite(ink_outline(ei))
    card = rect_mask((8, 10, 84, 122))
    ci = shaded(card, [hexrgb('#fffaf0'), PAL['cream'], PAL['cream_sh'], hexrgb('#bfae8e')], shadow_w=2)
    paste(ci, design, centered(design, 46, 20), card)
    for x in range(12, 81, 2):
        ci.putpixel((x, 13), PAL['red'])
        ci.putpixel((x, 118), PAL['pine'])
    im.alpha_composite(ink_outline(ci))
    return im


def save(img, name):
    img.save(os.path.join(SHOP, name), optimize=True)


def mockups(designs):
    out = {}
    for c in ('black', 'forest', 'oatmeal'):
        d = design_naughty(PAL['cream'] if c != 'oatmeal' else PAL['brown_dk'])
        out[f'tee-{c}'] = mock_tee(c, d)
    out['sweater-red'] = mock_sweater('red', (PAL['pine'], PAL['cream'], PAL['brown_dk']))
    out['sweater-green'] = mock_sweater('green', (PAL['red'], PAL['cream'], PAL['brown_dk']))
    for c in ('black', 'heather'):
        out[f'hoodie-{c}'] = mock_hoodie(c, designs['wordmark'])
    for k in ('drop', 'reserve', 'passed-out'):
        out[f'ornament-{k}'] = mock_ornament(designs[k])
    out['socks'] = mock_socks()
    for c in ('black', 'red'):
        out[f'beanie-{c}'] = mock_beanie(c)
    out['mug'] = mock_mug(designs['choices'])
    out['stickers'] = mock_stickers()
    out['wrap'] = mock_wrap()
    out['cards'] = mock_cards(designs['greetings'])
    return out


def main():
    designs = {
        'naughty': design_naughty(),
        'wordmark': design_wordmark(),
        'reserve': design_reserve(),
        'passed-out': design_passed_out(),
        'drop': design_drop(),
        'choices': design_choices(),
        'greetings': design_greetings(),
    }
    out = mockups(designs)
    for k, v in out.items():
        save(v, f'{k}.png')
    for k, v in designs.items():
        save(v, f'design-{k}.png')
    save(sweater_knit(68, 88, ramp('red')[1], PAL['pine'], PAL['cream'], PAL['brown_dk']), 'design-sweater-red.png')
    save(sweater_knit(68, 88, ramp('green')[1], PAL['red'], PAL['cream'], PAL['brown_dk']), 'design-sweater-green.png')
    save(design_naughty(PAL['cream']), 'design-naughty-light.png')
    save(design_naughty(PAL['brown_dk']), 'design-naughty-dark.png')
    save(wrap_tile(), 'design-wrap.png')
    if os.environ.get('SKIP_PRINT') != '1':
        write_print_readme(export_prints(designs))
    if PREVIEW:
        tiles = list(out.values())
        cols = 6
        W = cols * (S * 2 + 10)
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new('RGBA', (W, rows * (S * 2 + 10)), hexrgb('#24331f'))
        for i, t in enumerate(tiles):
            sheet.alpha_composite(upscale(t, 2), ((i % cols) * (S * 2 + 10), (i // cols) * (S * 2 + 10)))
        sheet.save(os.path.join(PREVIEW, 'merch_sheet.png'))
        dsheet = Image.new('RGBA', (900, 300), hexrgb('#3a2619'))
        x = 4
        for v in designs.values():
            dsheet.alpha_composite(upscale(v, 2), (x, 4))
            x += v.width * 2 + 10
        dsheet.save(os.path.join(PREVIEW, 'merch_designs.png'))
    print('merch ok', len(out))


# ---------------------------------------------------------------------------
# print files
# ---------------------------------------------------------------------------
def fit(img, target_w, target_h=None):
    """Largest integer nearest-neighbour upscale that fits the target box."""
    k = target_w // img.width
    if target_h:
        k = min(k, target_h // img.height)
    return upscale(img, max(1, k)), max(1, k)


def on_canvas(img, w, h, bg=(0, 0, 0, 0), y=None):
    c = Image.new('RGBA', (w, h), bg)
    c.alpha_composite(img, ((w - img.width) // 2, (h - img.height) // 2 if y is None else y))
    return c


def export_prints(designs):
    specs = []

    def put(rel, img, note):
        path = os.path.join(PRINT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path, optimize=True, dpi=(300, 300))
        specs.append((rel, img.size, note))

    # Tee: 12 in wide front print
    for name, fg in (('light-ink', PAL['cream']), ('dark-ink', PAL['brown_dk'])):
        big, k = fit(design_naughty(fg), 3600, 4200)
        put(f'tee-naughty-list/front-{name}.png', big, f'Front print, {k}x pixel scale. Light ink for black/forest, dark ink for oatmeal.')
    # Hoodie: 10 in chest print
    big, k = fit(designs['wordmark'], 3000, 3000)
    put('hoodie-wordmark/front.png', big, f'Chest print, {k}x pixel scale.')
    # Sweater: knit chart (1 pixel = 1 stitch) + preview
    for colour, (base, accent) in {'red': (ramp('red')[1], PAL['pine']), 'green': (ramp('green')[1], PAL['red'])}.items():
        chart = sweater_knit(68, 88, base, accent, PAL['cream'], PAL['brown_dk'])
        put(f'ugly-sweater/{colour}-stitch-chart-1x.png', chart, 'Knitting chart: 1 pixel = 1 stitch, 5 yarn colours.')
        put(f'ugly-sweater/{colour}-front-40x.png', upscale(chart, 40), 'Front panel artwork for all-over-print knit-look sweaters.')
    # Ornaments: 3 in round, 1200 px canvas
    for k_name in ('drop', 'reserve', 'passed-out'):
        d = designs[k_name]
        big, k = fit(d, 1000, 1000)
        put(f'ornament/{k_name}.png', on_canvas(big, 1200, 1200), f'Round ornament, centred on 1200x1200, {k}x scale.')
    # Mug: 11 oz wrap (two sides of the handle)
    big, k = fit(designs['choices'], 1050, 1050)
    wrap = Image.new('RGBA', (2475, 1155), (255, 255, 255, 255))
    for cx in (2475 // 4, 2475 * 3 // 4):
        wrap.alpha_composite(big, (cx - big.width // 2, (1155 - big.height) // 2))
    put('mug-poor-life-choices/11oz-wrap.png', wrap, f'11 oz mug wrap 2475x1155, design on both sides, {k}x scale.')
    # Beanie: embroidery patch art (plain face, 9 colours)
    big, k = fit(FACE_PLAIN, 720, 720)
    put('beanie/patch-embroidery.png', big, f'Woven/embroidered patch, {k}x scale, 9 thread colours.')
    # Socks: leg panel
    leg = Image.new('RGBA', (28, 72), PAL['cream'])
    dl = ImageDraw.Draw(leg)
    for y0 in (4, 12, 52, 60):
        dl.rectangle((0, y0, 27, y0 + 3), fill=PAL['brown'])
        dl.line((0, y0, 27, y0), fill=hexrgb('#6e553e'))
    leg.alpha_composite(FACE, (5, 24))
    put('socks/leg-panel.png', upscale(leg, 25), 'Leg panel for sublimated crew socks; heel and toe in red #c8323a.')
    # Stickers: individual die-cut artwork
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    for nm, art_img in (('wordmark', logo), ('santa-face', FACE), ('holiday-reserve', RESERVE), ('passed-out', passed_out_raccoon()), ('whiskey', bottle(1))):
        st = sticker(art_img)
        big, k = fit(st, 900, 900)
        put(f'stickers/{nm}.png', big, f'Die-cut sticker with white border, {k}x scale.')
    # Gift wrap: seamless tile
    t = wrap_tile()
    put('gift-wrap/seamless-tile-12x.png', upscale(t, 12), 'Seamless repeat tile (576 px). Tile across any sheet size.')
    put('gift-wrap/seamless-tile-24x.png', upscale(t, 24), 'Seamless repeat tile (1152 px), larger pixels.')
    # Holiday cards: 5x7 in front
    big, k = fit(designs['greetings'], 1300, 1700)
    card = on_canvas(big, 1500, 2100, PAL['cream'])
    put('holiday-cards/front-5x7.png', card, f'5x7 in card front at 300 dpi, {k}x scale.')
    return specs


def write_print_readme(specs):
    lines = [
        '# Print files',
        '',
        'Generated by `python3 tools/build_merch.py`. Every file is the pixel design scaled by a',
        'whole number with nearest-neighbour sampling, so edges stay razor sharp at any print size.',
        'All files are 300 dpi PNGs with transparent backgrounds unless noted.',
        '',
        '| File | Size (px) | Notes |',
        '| --- | --- | --- |',
    ]
    for rel, size, note in specs:
        lines.append(f'| `{rel}` | {size[0]} x {size[1]} | {note} |')
    lines += [
        '',
        'Upload these to your print-on-demand provider (Printful, Printify, etc.) when creating',
        'each product. Provider templates differ slightly; keep the artwork centred and scale it',
        'only by whole-number factors if you need a different size.',
    ]
    with open(os.path.join(PRINT, 'README.md'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
