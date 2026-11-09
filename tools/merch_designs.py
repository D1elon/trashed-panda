"""Merch artwork, designed for how each product is actually made.

Every function returns native-resolution pixel art. Production constraints are part of
the design, not an afterthought:

* Knitwear: jacquard knitting allows 4 yarn colours in total (base included). The knit
  charts are drawn on a 4-role palette, and accent colour never touches the base colour
  directly (low-contrast neighbours blur at the stitch level).
* Embroidery: at most 6 thread colours and ~1.3 mm minimum detail, so the beanie uses a
  simplified textile version of the face in 4 universal thread colours.
* DTG prints on dark garments: near-black outline pixels are knocked out in production
  (the garment shows through), so designs must read without them.
"""
from PIL import Image, ImageDraw

from merchkit import (PAL, FACE, KO, RESERVE, FALL_SANTA, STAND_SANTA, LYING_HAT, hexrgb, upscale,
                      text3x5, text3x5_width, font_text, tiny_text, centered, glyph, ink_outline, rac,
                      bottle, passed_out_raccoon, from_rows, art, HAT_SIDE, HAT_SIDE_PAL, ROOT, GAME,
                      SNOWFLAKE, TREE, MINI_BOTTLE)
from build_ui import FACE as FACE_ROWS, HAT as HAT_ROWS
import os

SEASON = 2026          # printed on the ornament back; bump each year (the story itself is Thanksgiving 2025)

# ---------------------------------------------------------------------------
# Textile face: the brand face reduced to roles for knit / embroidery
# ---------------------------------------------------------------------------
FACE_ROLE = {'K': 'dark', 'D': 'dark', 'E': 'dark', 'N': 'fur', 'F': 'fur', 'H': 'fur', 'L': 'light', 'W': 'light', 'S': 'light', 'G': 'light'}
HAT_ROLE = {'K': 'dark', 'R': 'hat', 'r': 'hat', 'h': 'hat', 'W': 'light', 'w': 'light'}


def textile_face(colors, hat=True):
    """colors: {'dark', 'fur', 'light', 'hat'} -> rgba. Pass fur=dark for a two-tone face."""
    face = from_rows(FACE_ROWS, {k: colors[v] for k, v in FACE_ROLE.items()})
    if not hat:
        return face
    hat_img = from_rows(HAT_ROWS, {k: colors[v] for k, v in HAT_ROLE.items()})
    im = Image.new('RGBA', (face.width, face.height + 7), (0, 0, 0, 0))
    im.alpha_composite(face, (0, 7))
    im.alpha_composite(hat_img, (2, 0))
    return im


# ---------------------------------------------------------------------------
# Knitwear (4 yarn colours)
# ---------------------------------------------------------------------------
YARN = {
    'red':   {'base': '#b3262e', 'cream': '#efe6d2', 'dark': '#2e2019', 'accent': '#24553a', 'hat': 'base'},
    'green': {'base': '#24553a', 'cream': '#efe6d2', 'dark': '#2e2019', 'accent': '#b3262e', 'hat': 'accent'},
}
KNIT_W, KNIT_H = 68, 88       # front/back chart: 1 cell = 1-2 stitches on a real sweater
SLEEVE_W, SLEEVE_H = 30, 84


def _yarn(cw):
    y = YARN[cw]
    c = {k: hexrgb(v) for k, v in y.items() if k != 'hat'}
    c['hat'] = c[y['hat']]
    return c


def _zigzag(px, w, y, col):
    for x in range(w):
        k = x % 6
        px[x, y + (k if k < 3 else 6 - k)] = col


def _dots(px, w, y, col, step=4, off=0):
    for x in range(off, w, step):
        px[x, y] = col


def _yoke(im, c):
    """Shared top band: dots, zigzag, a cream band of base-colour trees with accent stars."""
    w = im.width
    px = im.load()
    _dots(px, w, 1, c['cream'], 4, 1)
    _zigzag(px, w, 3, c['cream'])
    d = ImageDraw.Draw(im)
    d.rectangle((0, 9, w - 1, 20), fill=c['cream'])
    star = ['..#..', '.###.', '#####', '.###.', '..#..']
    for i, x in enumerate(range(1, w - 6, 9)):
        if i % 2 == 0:
            im.alpha_composite(glyph(TREE, c['base']), (x, 11))
        else:
            im.alpha_composite(glyph(star, c['accent']), (x + 1, 12))
    px = im.load()
    _zigzag(px, w, 22, c['cream'])
    _dots(px, w, 27, c['cream'], 4, 3)


def _hem(im, c, y):
    w = im.width
    d = ImageDraw.Draw(im)
    d.rectangle((0, y, w - 1, y + 11), fill=c['dark'])
    for i, x in enumerate(range(2, w - 4, 8)):
        im.alpha_composite(glyph(MINI_BOTTLE, c['cream']), (x, y + 2))
    px = im.load()
    _dots(px, w, y + 13, c['cream'], 4, 1)


def knit_front(cw):
    c = _yarn(cw)
    im = Image.new('RGBA', (KNIT_W, KNIT_H), c['base'])
    _yoke(im, c)
    face = textile_face({'dark': c['dark'], 'fur': c['dark'], 'light': c['cream'], 'hat': c['hat']})
    fx = (KNIT_W - face.width) // 2
    im.alpha_composite(face, (fx, 31))
    # snowflakes and bottles flank the face, all in cream (never accent on base)
    for side in (-1, 1):
        im.alpha_composite(glyph(SNOWFLAKE, c['cream']), (KNIT_W // 2 + side * 22 - 3, 33))
        im.alpha_composite(glyph(MINI_BOTTLE, c['cream']), (KNIT_W // 2 + side * 20 - 2, 45))
    for i, word in enumerate(('HOLIDAY', 'SPIRITS')):
        t = tiny_text(word, c['cream'])
        im.alpha_composite(t, ((KNIT_W - t.width) // 2, 56 + i * 7))
    px = im.load()
    _zigzag(px, KNIT_W, 70, c['cream'])
    _hem(im, c, 76 - 2)
    return im


def knit_back(cw):
    c = _yarn(cw)
    im = Image.new('RGBA', (KNIT_W, KNIT_H), c['base'])
    _yoke(im, c)
    for i, word in enumerate(('TRASHED', 'PANDA')):
        t = font_text(word, c['cream'])
        im.alpha_composite(t, ((KNIT_W - t.width) // 2, 36 + i * 11))
    px = im.load()
    for (x, y) in ((9, 62), (34, 63), (59, 62)):
        im.alpha_composite(glyph(SNOWFLAKE, c['cream']), (x - 3, y - 3))
    for (x, y) in ((4, 32), (63, 32), (21, 31), (47, 31)):
        im.putpixel((x, y), c['cream'])
    _zigzag(px, KNIT_W, 70, c['cream'])
    _hem(im, c, 74)
    return im


def knit_sleeve(cw):
    """Sleeves are ringed like a raccoon's tail."""
    c = _yarn(cw)
    im = Image.new('RGBA', (SLEEVE_W, SLEEVE_H), c['base'])
    d = ImageDraw.Draw(im)
    for y in range(6, SLEEVE_H - 14, 14):
        d.rectangle((0, y, SLEEVE_W - 1, y + 4), fill=c['dark'])
        for x in range(1, SLEEVE_W, 4):
            im.putpixel((x, y + 9), c['cream'])
    d.rectangle((0, SLEEVE_H - 10, SLEEVE_W - 1, SLEEVE_H - 1), fill=c['dark'])
    return im


def knit_tile(cw):
    """Seamless 24x24 all-over fill (for templates with extra panels)."""
    c = _yarn(cw)
    t = Image.new('RGBA', (24, 24), c['base'])
    t.alpha_composite(glyph(SNOWFLAKE, c['cream']), (2, 2))
    t.alpha_composite(glyph(MINI_BOTTLE, c['cream']), (15, 14))
    for (x, y) in ((16, 4), (5, 17)):
        t.putpixel((x, y), c['cream'])
    return t


# ---------------------------------------------------------------------------
# Tee: the Naughty List
# ---------------------------------------------------------------------------
def design_naughty_list(dark_ink=False):
    ink = PAL['brown_dk'] if dark_ink else PAL['cream']
    red = PAL['red'] if dark_ink else PAL['red_hi']
    head1 = font_text('NAUGHTY', ink)
    head2 = font_text('LIST', red)
    items = ['BROKE IN', 'SMASHED THE SHELVES', 'DRANK THE EVIDENCE', 'PASSED OUT']
    item_w = max(text3x5_width(i) for i in items) + 9
    w = max(FACE.width + 4 + head1.width, item_w)
    h = FACE.height + 3 + len(items) * 9 + 1
    im = Image.new('RGBA', (w + 2, h), (0, 0, 0, 0))
    hx = (w - (FACE.width + 4 + head1.width)) // 2
    im.alpha_composite(FACE, (hx, 0))
    im.alpha_composite(head1, (hx + FACE.width + 4, 6))
    im.alpha_composite(head2, (hx + FACE.width + 4, 6 + head1.height + 3))
    d = ImageDraw.Draw(im)
    ix = (w - item_w) // 2
    y = FACE.height + 4
    for it in items:
        d.rectangle((ix, y, ix + 4, y + 4), outline=ink)
        for (dx, dy) in ((1, 2), (2, 3), (3, 2), (4, 1), (5, 0)):   # red check overflowing the box
            im.putpixel((ix + dx, y + dy), red)
        text3x5(im, ix + 9, y, it, ink)
        y += 9
    return im


# ---------------------------------------------------------------------------
# Hoodie: wordmark front, "dropped in" back
# ---------------------------------------------------------------------------
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


def ceiling_band(w, h=10):
    im = Image.new('RGBA', (w, h + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tile, tbar, dark = hexrgb('#dedad1'), hexrgb('#a9a69d'), hexrgb('#1a1412')
    d.rectangle((0, 0, w - 1, h - 1), fill=tile)
    for x in range(w // 2 % 16, w, 16):
        d.line((x, 0, x, h - 1), fill=tbar)
    d.line((0, h - 1, w - 1, h - 1), fill=hexrgb('#8f8c84'))
    hx0, hx1 = w // 2 - 12, w // 2 + 12
    d.rectangle((hx0, 0, hx1, h - 3), fill=dark)
    for i, x in enumerate(range(hx0, hx1 + 1)):
        yy = h - 2 + (1 if i % 5 in (1, 2) else 0) + (1 if i % 7 == 3 else 0)
        d.line((x, h - 3, x, yy), fill=dark)
    for x in (hx0 + 4, hx0 + 10, hx1 - 5):
        d.line((x, h - 2, x, h + 1), fill=hexrgb('#d9c79a'))
    return im


def tumbling_raccoon():
    """Standing pose upside down: head-first through the ceiling."""
    return rac(0, 3).transpose(Image.FLIP_TOP_BOTTOM)


def design_drop(w=92, with_text=False):
    body = tumbling_raccoon()
    hat = art(HAT_SIDE, HAT_SIDE_PAL).rotate(-20, expand=True, resample=Image.NEAREST)
    h = body.height + 26 + (22 if with_text else 0)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    band = ceiling_band(w)
    im.alpha_composite(ink_outline(band), (0, 0))
    d = ImageDraw.Draw(im)
    rx = w // 2 - body.width // 2 + 4
    cream = PAL['cream']
    for (x, y0, y1) in ((rx + 8, 13, 19), (rx + 20, 12, 20), (rx + body.width - 12, 14, 19), (w // 2 + 2, 12, 17)):
        d.line((x, y0, x, y1), fill=cream)
    for (x, y, c) in ((rx - 6, 20, hexrgb('#dedad1')), (rx + body.width, 28, hexrgb('#dedad1')), (rx + body.width - 4, 44, hexrgb('#a9a69d')), (rx - 9, 38, hexrgb('#a9a69d'))):
        d.rectangle((x, y, x + 2, y + 1), fill=c)
    im.alpha_composite(body, (rx, 22))
    im.alpha_composite(hat, (w // 2 + 15, 12))
    if with_text:
        t1 = font_text('DROPPED IN', PAL['cream'])
        t2 = tiny_text('FOR THE HOLIDAYS', PAL['amber'])
        y = 22 + body.height + 3
        im.alpha_composite(t1, centered(t1, w / 2, y))
        im.alpha_composite(t2, centered(t2, w / 2, y + t1.height + 3))
    return im


def design_hoodie_back():
    return design_drop(84, with_text=True)


# ---------------------------------------------------------------------------
# Ornaments: full-bleed scenes on a 90x90 canvas (x10 = 900 px, about 3 in)
# ---------------------------------------------------------------------------
ORN = 90
ORN_SAFE = 78   # keep artwork inside this diameter


def _snow(im, n, seed, color=(244, 247, 251, 255), area=None):
    import random
    rnd = random.Random(seed)
    x0, y0, x1, y1 = area or (0, 0, im.width, im.height)
    for _ in range(n):
        im.putpixel((rnd.randrange(x0, x1), rnd.randrange(y0, y1)), color)


def ornament_drop():
    """Feet still in the hole, head-first toward the viewer, hat flying off."""
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#1d2947'))
    _snow(bg, 40, 3)
    band = ink_outline(ceiling_band(ORN))
    bg.alpha_composite(band, (0, 5))
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    body = tumbling_raccoon()
    hat = art(HAT_SIDE, HAT_SIDE_PAL).rotate(-20, expand=True, resample=Image.NEAREST)
    bx = ORN // 2 - body.width // 2 + 2
    content.alpha_composite(body, (bx, 15))
    content.alpha_composite(hat, (ORN // 2 + 14, 18))
    return bg, content


def ornament_reserve():
    s = 45                       # drawn at half size, then doubled: chunky pixels, consistent scale
    bg = Image.new('RGBA', (s, s), hexrgb('#7d1c25'))
    _snow(bg, 18, 5, PAL['gold_sh'])
    content = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    content.alpha_composite(RESERVE, ((s - RESERVE.width) // 2, (s - RESERVE.height) // 2))
    for (x, y, big) in ((12, 12, True), (33, 15, True), (13, 30, False), (32, 29, False), (22, 5, False)):
        content.putpixel((x, y), PAL['snow'])
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                content.putpixel((x + dx, y + dy), PAL['gold'])
    return upscale(bg, 2), upscale(content, 2)


def ornament_passed_out():
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#e8dcc4'))
    d = ImageDraw.Draw(bg)
    for x in range(0, ORN, 15):
        d.line((x, 0, x, ORN), fill=hexrgb('#c9b997'))
    for y in range(4, ORN, 15):
        d.line((0, y, ORN, y), fill=hexrgb('#c9b997'))
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    kx = 12                                            # placement found to sit fully in the safe circle
    content.alpha_composite(KO, (kx, 32))
    content.alpha_composite(LYING_HAT, (kx + KO.width - 30, 32 + KO.height - 8))
    z1 = glyph(['###', '..#', '.#.', '#..', '###'], PAL['brown_dk'])
    z2 = glyph(['####', '...#', '..#.', '.#..', '####'], PAL['brown_dk'])
    content.alpha_composite(z1, (50, 24))
    content.alpha_composite(z2, (55, 17))
    return bg, content


def ornament_back():
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#1d3324'))
    _snow(bg, 34, 9)
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    content.alpha_composite(logo, ((ORN - logo.width) // 2, 22))
    for i, s in enumerate(('ASHLAND VA', f'HOLIDAY {SEASON}')):
        t = tiny_text(s, PAL['cream_sh'] if i == 0 else PAL['gold'])
        content.alpha_composite(t, ((ORN - t.width) // 2, 56 + i * 8))
    return bg, content


def compose(layers):
    bg, content = layers
    out = bg.copy()
    out.alpha_composite(content)
    return out


def outside_safe(layers, safe=ORN_SAFE):
    """Count content pixels outside the safe circle (must be 0)."""
    _, content = layers
    a = content.getchannel('A').load()
    n = 0
    r = safe / 2
    c = (content.width - 1) / 2
    for y in range(content.height):
        for x in range(content.width):
            if a[x, y] and ((x - c) ** 2 + (y - c) ** 2) ** 0.5 > r:
                n += 1
    return n


# ---------------------------------------------------------------------------
# Mug: two sides, the night before and the morning after (wrap 270x105 -> 2700x1050)
# ---------------------------------------------------------------------------
MUG_W, MUG_H = 270, 105


def mug_side_morning():
    t1 = tiny_text('POOR LIFE', PAL['red'])
    t2 = tiny_text('CHOICES', PAL['red'])
    ko = passed_out_raccoon()
    w = max(ko.width, t1.width) + 2
    im = Image.new('RGBA', (w, ko.height + 16), (0, 0, 0, 0))
    im.alpha_composite(t1, centered(t1, w / 2, 0))
    im.alpha_composite(t2, centered(t2, w / 2, 7))
    im.alpha_composite(ko, centered(ko, w / 2, 15))
    return im


def mug_side_night():
    t = tiny_text('LAST CALL', PAL['pine'])
    stand = rac(1, 8)                                  # standing, Santa hat, swipe arc
    flying = bottle(1, 1)                               # tipped whiskey bottle
    w = stand.width + 18
    im = Image.new('RGBA', (w, stand.height + 10), (0, 0, 0, 0))
    im.alpha_composite(t, centered(t, w / 2, 0))
    im.alpha_composite(stand, (0, 9))
    im.alpha_composite(flying, (stand.width - 6, 14))
    return im


def mug_wrap():
    im = Image.new('RGBA', (MUG_W, MUG_H), (0, 0, 0, 0))
    a, b = mug_side_morning(), mug_side_night()
    im.alpha_composite(a, (MUG_W // 4 - a.width // 2, (MUG_H - a.height) // 2))
    im.alpha_composite(b, (MUG_W * 3 // 4 - b.width // 2, (MUG_H - b.height) // 2))
    return im


# ---------------------------------------------------------------------------
# Beanie: embroidered face (4 universal thread colours)
# ---------------------------------------------------------------------------
THREADS = {'dark': '#111111', 'light': '#f5f5f0', 'fur': '#8c8c8c', 'hat': '#c4161c'}


def beanie_embroidery():
    return textile_face({k: hexrgb(v) for k, v in THREADS.items()})


# ---------------------------------------------------------------------------
# Socks, wrap, cards, stickers
# ---------------------------------------------------------------------------
def sock_tile():
    """Seamless 28x32: raccoon-tail rings, snowflakes and bottles."""
    t = Image.new('RGBA', (28, 32), PAL['cream'])
    d = ImageDraw.Draw(t)
    d.rectangle((0, 0, 27, 4), fill=PAL['brown'])
    d.line((0, 0, 27, 0), fill=hexrgb('#6e553e'))
    t.alpha_composite(glyph(SNOWFLAKE, PAL['red']), (3, 10))
    t.alpha_composite(glyph(MINI_BOTTLE, PAL['pine']), (18, 9))
    d.rectangle((0, 18, 27, 22), fill=PAL['brown'])
    d.line((0, 18, 27, 18), fill=hexrgb('#6e553e'))
    t.alpha_composite(glyph(MINI_BOTTLE, PAL['pine']), (5, 24))
    t.alpha_composite(glyph(SNOWFLAKE, PAL['red']), (17, 24))
    return t


def sock_leg():
    leg = Image.new('RGBA', (28, 72), PAL['cream'])
    dl = ImageDraw.Draw(leg)
    for y0 in (4, 12, 52, 60):
        dl.rectangle((0, y0, 27, y0 + 3), fill=PAL['brown'])
        dl.line((0, y0, 27, y0), fill=hexrgb('#6e553e'))
    leg.alpha_composite(FACE, (5, 24))
    return leg


def wrap_tile(bg=PAL['red']):
    t = Image.new('RGBA', (48, 48), bg)
    t.alpha_composite(FACE, (3, 2))
    t.alpha_composite(FACE, (27, 26))
    sf = glyph(SNOWFLAKE, PAL['cream'])
    t.alpha_composite(sf, (32, 6))
    t.alpha_composite(sf, (8, 32))
    b = glyph(MINI_BOTTLE, PAL['gold'])
    for xy in ((40, 16), (16, 40), (22, 12)):
        t.alpha_composite(b, xy)
    for (x, y) in ((44, 2), (2, 26), (26, 46), (46, 40), (20, 30)):
        t.putpixel((x, y), PAL['cream'])
    return t


CARD_W, CARD_H = 75, 105   # x20 = 1500 x 2100 = 5 x 7 in at 300 dpi


def card_front():
    im = Image.new('RGBA', (CARD_W, CARD_H), PAL['cream'])
    d = ImageDraw.Draw(im)
    for x in range(2, CARD_W - 2, 2):
        im.putpixel((x, 3), PAL['red'])
        im.putpixel((x, CARD_H - 4), PAL['pine'])
    t1 = font_text("SEASON'S", PAL['red'])
    t2 = font_text('GREETINGS', PAL['pine'])
    ko = passed_out_raccoon()
    s1 = tiny_text('FROM THE', PAL['brown'])
    s2 = tiny_text('BATHROOM FLOOR', PAL['brown'])
    y = 12
    for img, gap in ((t1, 2), (t2, 10), (ko, 8), (s1, 2), (s2, 0)):
        im.alpha_composite(img, centered(img, CARD_W / 2, y))
        y += img.height + gap
    return im


def card_back():
    im = Image.new('RGBA', (CARD_W, CARD_H), PAL['cream'])
    face = FACE
    im.alpha_composite(face, centered(face, CARD_W / 2, 66))
    t = tiny_text('TRASHEDPANDA.LOL', PAL['brown'])
    im.alpha_composite(t, centered(t, CARD_W / 2, 92))
    return im


def sticker_designs():
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    store = Image.open(os.path.join(GAME, 'store.png')).convert('RGBA')
    poster = store.crop((95, 51, 135, 99))
    poster = poster.crop(poster.getbbox())
    return {
        'santa-panda': FACE,
        'holiday-reserve': RESERVE,
        'passed-out': passed_out_raccoon(),
        'wordmark': logo,
        'holiday-spirits': poster,
    }
