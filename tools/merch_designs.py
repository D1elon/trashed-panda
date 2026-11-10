"""Merch artwork, designed for how each product is actually made.

Every function returns native-resolution pixel art. The raccoon in every design is the
game's own character, rendered by tools/raccoon.py (the same rig that draws the sprite
sheet), so the merch cannot drift away from the game.

Production constraints are part of the design, not an afterthought:

* Knitwear: jacquard knitting allows 4 yarn colours in total (base included). The knit
  charts are drawn on a 4-role palette (base, cream, charcoal, fur grey), and the grey
  never touches the base colour directly: a mid grey on red or green blurs at the stitch
  level, so it is always fenced in by charcoal.
* Embroidery: at most 6 thread colours and ~1.3 mm minimum detail, so the beanie uses the
  face reduced to 5 thread colours.
* DTG prints on dark garments: near-black outline pixels are knocked out in production
  (the garment shows through), so designs must read without them.
"""
import os

from PIL import Image, ImageDraw

import raccoon as R
from merchkit import (PAL, FACE, FACE_SMALL, HAT, WALK_SANTA, STAND_SANTA, SWIPE_SANTA, CHEER_SANTA, CLIMB_SANTA,
                      PASSED_OUT, RESERVE, hexrgb, upscale, text3x5, text3x5_width, font_text, tiny_text, centered,
                      glyph, ink_outline, bottle, ROOT, SNOWFLAKE, TREE, MINI_BOTTLE)

SEASON = 2026          # printed on the ornament back; bump each year (the story itself is Thanksgiving 2025)

# ---------------------------------------------------------------------------
# Textile face: the game's head reduced to roles for knit / embroidery
# ---------------------------------------------------------------------------
ROLE = {'K': 'dark', 'M': 'dark', 'E': 'dark', 'N': 'dark', 'd': 'dark', 'k': 'dark',
        'W': 'light', 'G': 'light', 'L': 'light', 'Y': 'light', 'y': 'light',
        'F': 'fur', 'H': 'fur', 'S': 'shade', 'm': 'shade',
        'R': 'hat', 'r': 'hat', 'h': 'hat'}


def textile_face(colors, hat=True, small=False, bright_eyes=False):
    """colors: {'dark', 'light', 'fur', 'hat'[, 'shade']} -> rgba ('shade' defaults to 'fur').
    bright_eyes: with only one dark colour the eye would vanish into the mask, so the eye
    is drawn light with a dark pupil instead."""
    colors = dict(colors)
    colors.setdefault('shade', colors['fur'])
    role = dict(ROLE, E='light', G='dark') if bright_eyes else ROLE
    cel = R.face_cel(hat, small=small)
    h, w = cel.c.shape
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            ch = cel.c[y, x]
            if ch != '.':
                px[x, y] = colors[role[ch]]
    return im


# ---------------------------------------------------------------------------
# Knitwear (4 yarn colours)
# ---------------------------------------------------------------------------
YARN = {
    'red':   {'base': '#b3262e', 'cream': '#efe6d2', 'dark': '#2b2522', 'accent': '#8d8578', 'hat': 'base'},
    'green': {'base': '#24553a', 'cream': '#efe6d2', 'dark': '#2b2522', 'accent': '#8d8578', 'hat': 'base'},
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


def _tail_band(im, c, y, rows=2, rings=5):
    """Raccoon-tail rings: charcoal, grey, charcoal ... always starting and ending on charcoal."""
    d = ImageDraw.Draw(im)
    for i in range(rings):
        d.rectangle((0, y + i * rows, im.width - 1, y + (i + 1) * rows - 1), fill=c['dark'] if i % 2 == 0 else c['accent'])
    return y + rings * rows


def _yoke(im, c):
    """Shared top: a ringed-tail band, then a cream zigzag and dots."""
    px = im.load()
    y = _tail_band(im, c, 2)
    px = im.load()
    _zigzag(px, im.width, y + 2, c['cream'])
    _dots(px, im.width, y + 7, c['cream'], 4, 1)
    return y + 9


def _hem(im, c, y):
    d = ImageDraw.Draw(im)
    d.rectangle((0, y, im.width - 1, im.height - 1), fill=c['dark'])
    px = im.load()
    _zigzag(px, im.width, y + 2, c['cream'])


def knit_front(cw):
    """One big face: the game's head at two stitches per pixel, hat in the sweater's own colour."""
    c = _yarn(cw)
    im = Image.new('RGBA', (KNIT_W, KNIT_H), c['base'])
    top = _yoke(im, c)
    face = upscale(textile_face({'dark': c['dark'], 'fur': c['accent'], 'light': c['cream'], 'hat': c['hat']}, bright_eyes=True), 2)
    fx = (KNIT_W - face.width) // 2
    im.alpha_composite(face, (fx, top + 1))
    for side in (0, 1):                       # snowflakes and bottles down both edges, all in cream
        x = 0 if side == 0 else KNIT_W - 7
        im.alpha_composite(glyph(SNOWFLAKE, c['cream']), (x, 30))
        im.alpha_composite(glyph(MINI_BOTTLE, c['cream']), (x + 1, 44))
        im.alpha_composite(glyph(SNOWFLAKE, c['cream']), (x, 58))
    _hem(im, c, 80)
    return im


def knit_back(cw):
    c = _yarn(cw)
    im = Image.new('RGBA', (KNIT_W, KNIT_H), c['base'])
    top = _yoke(im, c)
    for i, word in enumerate(('TRASHED', 'PANDA')):
        t = font_text(word, c['cream'])
        im.alpha_composite(t, ((KNIT_W - t.width) // 2, top + 4 + i * 11))
    y = top + 30
    for i, x in enumerate(range(3, KNIT_W - 6, 9)):
        g = glyph(SNOWFLAKE if i % 2 == 0 else MINI_BOTTLE, c['cream'])
        im.alpha_composite(g, (x + (0 if i % 2 == 0 else 1), y))
    for i, word in enumerate(('ASHLAND VA', 'EST 2025')):
        t = tiny_text(word, c['cream'])
        im.alpha_composite(t, ((KNIT_W - t.width) // 2, y + 12 + i * 8))
    _hem(im, c, 80)
    return im


def knit_sleeve(cw):
    """Sleeves are ringed exactly like the tail: charcoal and grey bands, charcoal cuff."""
    c = _yarn(cw)
    im = Image.new('RGBA', (SLEEVE_W, SLEEVE_H), c['base'])
    d = ImageDraw.Draw(im)
    for i, y in enumerate(range(6, 72, 6)):
        d.rectangle((0, y, SLEEVE_W - 1, y + 5), fill=c['dark'] if i % 2 == 0 else c['accent'])
    d.rectangle((0, 72, SLEEVE_W - 1, SLEEVE_H - 1), fill=c['dark'])
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
# Tee: the mugshot
# ---------------------------------------------------------------------------
def design_mugshot(dark_ink=False):
    """Booking photo: height chart, the raccoon holding its placard, the verdict."""
    ink = PAL['brown_dk'] if dark_ink else PAL['cream']
    faint = hexrgb('#a8997e') if dark_ink else hexrgb('#8d8371')
    red = PAL['red'] if dark_ink else PAL['red_hi']
    board, board_ink = hexrgb('#f6ead2'), hexrgb('#1b1513')
    rac = STAND_SANTA
    w = 80
    floor = 4 + rac.height
    verdict = font_text('GUILTY', red)
    sub = tiny_text('OF POOR LIFE CHOICES', ink)
    im = Image.new('RGBA', (w, floor + 6 + verdict.height + 4 + sub.height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, mark in enumerate(('36', '30', '24', '18', '12')):        # height chart, in inches
        y = 6 + i * 12
        for x in range(12, w, 2):
            im.putpixel((x, y), faint)
        text3x5(im, 0, y - 2, mark, faint)
    d.line((8, floor, w - 1, floor), fill=ink)
    rx = (w + 10 - rac.width) // 2
    im.alpha_composite(rac, (rx, floor - rac.height + 1))
    l1, l2 = tiny_text('ASHLAND VA', board_ink), tiny_text('NOV 2025', board_ink)
    bw, bh = l1.width + 8, 17
    bx, by = rx + rac.width // 2 + 5 - bw // 2, floor - 27
    d.rectangle((bx, by, bx + bw - 1, by + bh - 1), fill=board, outline=board_ink)
    im.alpha_composite(l1, (bx + 4, by + 3))
    im.alpha_composite(l2, (bx + (bw - l2.width) // 2, by + 10))
    for px_ in (bx - 1, bx + bw - 3):                                  # paws gripping the placard
        d.rectangle((px_, by + 5, px_ + 3, by + 9), fill=hexrgb(R.PALETTE['M']), outline=board_ink)
    im.alpha_composite(verdict, centered(verdict, w / 2, floor + 6))
    im.alpha_composite(sub, centered(sub, w / 2, floor + 6 + verdict.height + 4))
    return im


# ---------------------------------------------------------------------------
# Hoodie: face and wordmark on the chest, "last call" on the back
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


def shelf_board(w):
    im = Image.new('RGBA', (w, 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, 3), fill=hexrgb('#8a9296'))
    d.line((0, 0, w - 1, 0), fill=hexrgb('#b9c0c2'))
    d.line((0, 3, w - 1, 3), fill=hexrgb('#5d6569'))
    for x in range(6, w - 4, 16):
        d.rectangle((x, 4, x + 5, 5), fill=hexrgb('#f6f1e7'))
        d.point((x + 2, 5), fill=PAL['red'])
    return ink_outline_pad(im)


def ink_outline_pad(im):
    pad = Image.new('RGBA', (im.width + 2, im.height + 2), (0, 0, 0, 0))
    pad.alpha_composite(im, (1, 1))
    return ink_outline(pad)


def design_last_call(w=84, with_text=True):
    """On the top shelf, mid-swipe, one bottle already on its way down."""
    rac = SWIPE_SANTA
    title = font_text('LAST CALL', PAL['cream'])
    top = title.height + 6 if with_text else 0
    floor = top + rac.height
    foot = tiny_text('ASHLAND VA  EST 2025', PAL['amber'])
    im = Image.new('RGBA', (w, floor + 8 + (foot.height + 3 if with_text else 0)), (0, 0, 0, 0))
    if with_text:
        im.alpha_composite(title, centered(title, w / 2, 0))
    board = shelf_board(w - 2)
    im.alpha_composite(board, (0, floor - 1))
    standing = bottle(0, 0)
    im.alpha_composite(standing, (w - standing.width - 2, floor - standing.height))
    im.alpha_composite(rac, (0, floor - rac.height))
    flying = bottle(1, 1)
    im.alpha_composite(flying, (rac.width - 5, floor - 42))
    if with_text:
        im.alpha_composite(foot, centered(foot, w / 2, floor + 9))
    return im


def design_hoodie_back():
    return design_last_call(84, with_text=True)


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


def ornament_santa_panda():
    """The face, two device pixels per art pixel, on a snowy pine green."""
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#1d4a33'))
    _snow(bg, 44, 3)
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    big = upscale(FACE, 2)
    content.alpha_composite(big, ((ORN - big.width) // 2, (ORN - big.height) // 2))
    return bg, content


def ornament_top_shelf():
    """Seen from behind, halfway up the shelves, on a night-blue sky."""
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#1d2947'))
    _snow(bg, 40, 7)
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    rac = CLIMB_SANTA
    upper, lower = shelf_board(42), shelf_board(58)
    content.alpha_composite(upper, ((ORN - upper.width) // 2, 28))
    content.alpha_composite(lower, ((ORN - lower.width) // 2, 62))
    for kind, x in ((1, 17), (0, 62)):                 # one bottle left standing either side
        b = bottle(kind, 0)
        content.alpha_composite(b, (x, 63 - b.height))
    content.alpha_composite(rac, ((ORN - rac.width) // 2, 14))
    return bg, content


def ornament_passed_out():
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#e8dcc4'))
    d = ImageDraw.Draw(bg)
    for x in range(0, ORN, 15):
        d.line((x, 0, x, ORN), fill=hexrgb('#c9b997'))
    for y in range(4, ORN, 15):
        d.line((0, y, ORN, y), fill=hexrgb('#c9b997'))
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    ko = PASSED_OUT
    content.alpha_composite(ko, ((ORN - ko.width) // 2 + 1, 31))
    z1 = glyph(['###', '..#', '.#.', '#..', '###'], PAL['brown_dk'])
    z2 = glyph(['####', '...#', '..#.', '.#..', '####'], PAL['brown_dk'])
    content.alpha_composite(z1, (56, 24))
    content.alpha_composite(z2, (61, 16))
    return bg, content


def ornament_back():
    bg = Image.new('RGBA', (ORN, ORN), hexrgb('#7d1c25'))
    _snow(bg, 34, 9, PAL['gold_sh'])
    content = Image.new('RGBA', (ORN, ORN), (0, 0, 0, 0))
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    content.alpha_composite(logo, ((ORN - logo.width) // 2, 22))
    for i, s in enumerate(('ASHLAND VA', f'HOLIDAY {SEASON}')):
        t = tiny_text(s, PAL['cream'] if i == 0 else PAL['gold'])
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
    t1 = font_text('POOR LIFE', PAL['red'])
    t2 = font_text('CHOICES', PAL['red'])
    ko = PASSED_OUT
    w = max(ko.width, t1.width) + 2
    im = Image.new('RGBA', (w, ko.height + 26), (0, 0, 0, 0))
    im.alpha_composite(t1, centered(t1, w / 2, 0))
    im.alpha_composite(t2, centered(t2, w / 2, 10))
    im.alpha_composite(ko, centered(ko, w / 2, 24))
    return im


def mug_side_night():
    t = font_text('LAST CALL', PAL['pine'])
    scene = design_last_call(84, with_text=False)
    w = max(scene.width, t.width)
    im = Image.new('RGBA', (w, scene.height + 12), (0, 0, 0, 0))
    im.alpha_composite(t, centered(t, w / 2, 0))
    im.alpha_composite(scene, centered(scene, w / 2, 12))
    return im


def mug_wrap():
    im = Image.new('RGBA', (MUG_W, MUG_H), (0, 0, 0, 0))
    a, b = mug_side_morning(), mug_side_night()
    im.alpha_composite(a, (MUG_W // 4 - a.width // 2, (MUG_H - a.height) // 2))
    im.alpha_composite(b, (MUG_W * 3 // 4 - b.width // 2, (MUG_H - b.height) // 2))
    return im


# ---------------------------------------------------------------------------
# Beanie: embroidered face (5 thread colours)
# ---------------------------------------------------------------------------
THREADS = {'dark': '#111111', 'light': '#f5f5f0', 'fur': '#9a9a9a', 'shade': '#6b6b6b', 'hat': '#c4161c'}


def beanie_embroidery():
    return textile_face({k: hexrgb(v) for k, v in THREADS.items()})


# ---------------------------------------------------------------------------
# Socks, wrap, cards, stickers
# ---------------------------------------------------------------------------
TAIL_DARK, TAIL_LIGHT = hexrgb(R.PALETTE['M']), hexrgb(R.PALETTE['L'])


def sock_tile():
    """Seamless 28x32: the tail's own dark and light rings, with snowflakes and bottles."""
    t = Image.new('RGBA', (28, 32), TAIL_LIGHT)
    d = ImageDraw.Draw(t)
    for y0 in (0, 16):
        d.rectangle((0, y0, 27, y0 + 5), fill=TAIL_DARK)
        d.line((0, y0, 27, y0), fill=hexrgb(R.PALETTE['d']))
    t.alpha_composite(glyph(SNOWFLAKE, PAL['red']), (3, 7))
    t.alpha_composite(glyph(MINI_BOTTLE, PAL['pine']), (18, 7))
    t.alpha_composite(glyph(MINI_BOTTLE, PAL['pine']), (5, 23))
    t.alpha_composite(glyph(SNOWFLAKE, PAL['red']), (17, 23))
    return t


def sock_leg():
    leg = Image.new('RGBA', (28, 72), TAIL_LIGHT)
    dl = ImageDraw.Draw(leg)
    for y0 in (2, 12, 50, 60):
        dl.rectangle((0, y0, 27, y0 + 5), fill=TAIL_DARK)
        dl.line((0, y0, 27, y0), fill=hexrgb(R.PALETTE['d']))
    leg.alpha_composite(FACE_SMALL, (5, 24))
    return leg


def wrap_tile(bg=hexrgb('#1d4a33')):
    """Seamless 60x64 brick repeat: two faces per tile on pine green."""
    t = Image.new('RGBA', (60, 64), bg)
    t.alpha_composite(FACE, (2, 2))
    t.alpha_composite(FACE, (32, 34))
    sf = glyph(SNOWFLAKE, PAL['cream'])
    t.alpha_composite(sf, (41, 6))
    t.alpha_composite(sf, (10, 40))
    b = glyph(MINI_BOTTLE, PAL['gold'])
    for xy in ((52, 20), (22, 54), (33, 22), (4, 54)):
        t.alpha_composite(b, xy)
    for (x, y) in ((56, 2), (30, 30), (2, 34), (58, 60), (46, 30), (16, 62)):
        t.putpixel((x, y), PAL['cream'])
    return t


CARD_W, CARD_H = 75, 105   # x20 = 1500 x 2100 = 5 x 7 in at 300 dpi


def card_front():
    """MERRY TRASHMAS: arms up, hat on, a bottle either side."""
    im = Image.new('RGBA', (CARD_W, CARD_H), PAL['cream'])
    for x in range(2, CARD_W - 2, 2):
        im.putpixel((x, 3), PAL['red'])
        im.putpixel((x, CARD_H - 4), PAL['pine'])
    t1 = font_text('MERRY', PAL['red'])
    t2 = font_text('TRASHMAS', PAL['pine'])
    im.alpha_composite(t1, centered(t1, CARD_W / 2, 10))
    im.alpha_composite(t2, centered(t2, CARD_W / 2, 20))
    rac = CHEER_SANTA
    floor = 92
    d = ImageDraw.Draw(im)
    d.line((8, floor, CARD_W - 9, floor), fill=PAL['cream_sh'])
    im.alpha_composite(rac, (CARD_W // 2 - rac.width // 2 - 2, floor - rac.height + 1))
    for (x, y, big) in ((10, 40, True), (64, 44, True), (15, 60, False), (61, 62, False), (56, 34, False)):
        im.putpixel((x, y), PAL['gold'])
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                im.putpixel((x + dx, y + dy), PAL['gold_sh'])
    s = tiny_text('FROM ASHLAND VA', PAL['brown'])
    im.alpha_composite(s, centered(s, CARD_W / 2, floor + 3))
    return im


def card_back():
    im = Image.new('RGBA', (CARD_W, CARD_H), PAL['cream'])
    im.alpha_composite(FACE_SMALL, centered(FACE_SMALL, CARD_W / 2, 66))
    t = tiny_text('TRASHEDPANDA.LOL', PAL['brown'])
    im.alpha_composite(t, centered(t, CARD_W / 2, 92))
    return im


def sticker_designs():
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    return {
        'santa-panda': FACE,
        'on-the-prowl': WALK_SANTA,
        'passed-out': PASSED_OUT,
        'holiday-reserve': RESERVE,
        'wordmark': logo,
    }
