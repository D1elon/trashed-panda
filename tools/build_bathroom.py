#!/usr/bin/env python3
"""The passed-out scene: the restroom of the store, the next morning.

    python3 tools/build_bathroom.py

Drawn natively on the same pixel grid and in the same flat side view as the store
(tools/build_store.py), with the game's own sprites: the raccoon in its end-of-round pose
(on its back, feet up) but asleep instead of knocked out, its Santa hat on the tiles and
an empty Holiday Reserve beside it. Run after build_sprites.py and build_store.py.

Output: assets/game/bathroom.png (352 x 184, shown at whole-number scales on the results
screen and the home page).
"""
import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, text3x5, text3x5_width  # noqa: E402
from build_store import Canvas, C as STORE  # noqa: E402
from build_sprites import RC_W, RC_H, BT_W, BT_H  # noqa: E402
import raccoon  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(ROOT, 'assets', 'game')
PREVIEW = os.environ.get('PREVIEW_DIR')

W, H = 352, 184
FLOOR_TOP = 118          # wall / floor junction
OUT = STORE['out']

C = {k: hexrgb(v) for k, v in {
    # warm restroom walls: painted upper wall, tiled wainscot
    'wall': '#c9a982', 'wall_hi': '#d3b58f', 'wall_sh': '#b9976f', 'wall_sh2': '#ad8b64',
    'wtile': '#e3d3b4', 'wtile2': '#dccaa8', 'wgrout': '#b9a17c', 'cap': '#a68862', 'cap_hi': '#c2a47c',
    'base': '#8a6f50', 'base_hi': '#a3876a', 'base_dk': '#6b543b',
    'tile': '#eee6d3', 'tile2': '#e6dcc6', 'grout': '#bfae8e', 'grout_lt': '#d8ccb3', 'refl': '#e2d8c2',
    # porcelain, chrome, plastic
    'por': '#f7f6f1', 'por_sh': '#dddbd3', 'por_dk': '#bdbab0', 'water': '#a9c4cc', 'water_dk': '#86a5ae',
    'chrome': '#aab3b6', 'chrome_hi': '#e4eaeb', 'chrome_dk': '#7b8588',
    'glass': '#b9cdd1', 'glass_hi': '#dbe8ea', 'glass_dk': '#9fb6bb',
    'bin': '#3c4144', 'bin_hi': '#5a6266', 'bin_dk': '#2a2e30',
    'paper': '#f4f1e8', 'paper_sh': '#d6d1c4',
    'sign': '#f4f1e8', 'ink': '#3a2e28',
    'shadow': '#000000',
}.items()}


def ellipse(cv, cx, cy, rx, ry, color):
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x / (rx + 0.5)) ** 2 + (y / (ry + 0.5)) ** 2 <= 1:
                cv.p(cx + x, cy + y, color)


def shade(cv, x0, y0, x1, y1, alpha):
    """Darken a rectangle (contact shadows), like the renderer's 18% black."""
    over = Image.new('RGBA', (x1 - x0, y1 - y0), C['shadow'][:3] + (round(255 * alpha),))
    cv.im.alpha_composite(over, (x0, y0))
    cv.px = cv.im.load()


def soft_shadow(cv, cx, y, w):
    shade(cv, cx - w // 2, y - 1, cx + w // 2, y + 1, 0.16)
    shade(cv, cx - w // 2 + 3, y - 2, cx + w // 2 - 3, y - 1, 0.16)


def outline(cv, x0, y0, x1, y1, inside):
    """Outline every pixel in the box that matches `inside` and touches something else."""
    px = cv.im.load()
    pts = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if px[x, y] in inside:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < W and 0 <= ny < H) or px[nx, ny] not in inside:
                        pts.append((x, y))
                        break
    for (x, y) in pts:
        cv.p(x, y, OUT)


# ---------------------------------------------------------------------------
# room
# ---------------------------------------------------------------------------
def draw_room(cv):
    wainscot = 64
    cv.rect(0, 0, W, FLOOR_TOP, C['wall'])
    for x in range(0, W, 2):                      # soft shade under the ceiling line
        cv.p(x, 3, C['wall_sh'])
    cv.hline(0, W, 0, C['wall_sh2']); cv.hline(0, W, 1, C['wall_sh']); cv.hline(0, W, 2, C['wall_sh'])
    # tiled wainscot
    cv.rect(0, wainscot, W, FLOOR_TOP, C['wtile'])
    for i, y in enumerate(range(wainscot + 3, FLOOR_TOP, 9)):
        cv.hline(0, W, y, C['wgrout'])
        for x in range(4 if i % 2 else 0, W, 9):
            cv.vline(x, y + 1, min(FLOOR_TOP, y + 9), C['wgrout'])
            if (x // 9 + i) % 3 == 0:
                cv.rect(x + 1, y + 1, min(W, x + 9), min(FLOOR_TOP, y + 9), C['wtile2'])
    cv.rect(0, wainscot, W, wainscot + 3, C['cap'])
    cv.hline(0, W, wainscot, C['cap_hi'])
    cv.hline(0, W, wainscot + 3, C['wall_sh2'])
    # baseboard
    cv.rect(0, FLOOR_TOP - 5, W, FLOOR_TOP, C['base'])
    cv.hline(0, W, FLOOR_TOP - 5, C['base_hi'])
    cv.hline(0, W, FLOOR_TOP - 1, C['base_dk'])
    # floor: the store's tile pattern (rows taller toward the viewer), in warmer tiles
    cv.rect(0, FLOOR_TOP, W, H, C['tile'])
    y, h, rows = FLOOR_TOP, 7, []
    while y < H:
        rows.append((y, min(H, y + h)))
        y += h
        h += 2
    for i, (y0, y1) in enumerate(rows):
        for xi, x in enumerate(range(0, W, 22)):
            if (i + xi) % 2:
                cv.rect(x + 1, y0 + 1, x + 22, y1, C['tile2'])
        cv.hline(0, W, y0, C['grout'])
        if y0 + 1 < y1:
            cv.hline(0, W, y0 + 1, C['grout_lt'])
    for x in range(0, W, 22):
        cv.vline(x, FLOOR_TOP, H, C['grout'])


def draw_garland(cv):
    """The store's pine garland with bows and lit bulbs, along the top of the wall."""
    pine, pine_hi, pine_dk, pine_out = STORE['pine'], STORE['pine_hi'], STORE['pine_dk'], STORE['pine_out']
    bulbs = ['#ff5a52', '#ffd25a', '#58e08a', '#6cb2ff', '#ff9ad0']
    swag = 44
    n = 0
    for sx in range(-8, W, swag):
        for x in range(sx, sx + swag):
            t = (x - sx) / swag
            y = 5 + round(math.sin(t * math.pi) * 6)
            for dy in range(-1, 3):
                c = pine if dy in (0, 1) else pine_dk if dy == 2 else pine_hi
                if (x * 5 + dy * 3) % 7 == 0:
                    c = pine_hi
                cv.p(x, y + dy, c)
            cv.p(x, y + 3, pine_out)
        for (dx, dy, c) in ((-2, 0, 'red'), (-1, 0, 'red_hi'), (1, 0, 'red_hi'), (2, 0, 'red'), (-2, 1, 'red_dk'),
                            (2, 1, 'red_dk'), (0, 1, 'red'), (-1, 2, 'red'), (1, 2, 'red'), (0, 0, 'red_dk')):
            cv.p(sx + dx, 4 + dy, STORE[c])
        for k in (0.3, 0.7):
            x = sx + round(swag * k)
            y = 5 + round(math.sin(k * math.pi) * 6) + 3
            col = hexrgb(bulbs[n % len(bulbs)])
            n += 1
            cv.rect(x, y, x + 1, y + 2, col)
            cv.p(x, y, hexrgb('#fffbe8'))


def draw_mirror_and_sink(cv, x0):
    # mirror
    mx0, my0, mx1, my1 = x0 + 6, 18, x0 + 54, 58
    cv.rect(mx0 - 2, my0 - 2, mx1 + 2, my1 + 2, C['chrome'])
    cv.hline(mx0 - 2, mx1 + 2, my0 - 2, C['chrome_hi'])
    cv.hline(mx0 - 2, mx1 + 2, my1 + 1, C['chrome_dk'])
    cv.frame(mx0 - 3, my0 - 3, mx1 + 3, my1 + 3, OUT)
    cv.rect(mx0, my0, mx1, my1, C['glass'])
    for k in range(0, 34, 1):                     # two diagonal reflection streaks
        for (off, wdt) in ((8, 3), (20, 1)):
            for t in range(wdt):
                x, y = mx0 + off + k + t, my1 - 1 - k
                if mx0 <= x < mx1 and my0 <= y < my1:
                    cv.p(x, y, C['glass_hi'])
    cv.hline(mx0, mx1, my1 - 1, C['glass_dk'])
    # sink: wall-mounted basin with a chrome tap and trap
    sx0, sx1, sy = x0, x0 + 60, 74
    cv.rect(sx0 + 2, sy, sx1 - 2, sy + 4, C['por'])            # rim
    cv.rect(sx0 + 4, sy + 4, sx1 - 4, sy + 12, C['por'])       # bowl
    cv.rect(sx0 + 8, sy + 12, sx1 - 8, sy + 15, C['por_sh'])
    cv.hline(sx0 + 2, sx1 - 2, sy, C['por'])
    cv.hline(sx0 + 4, sx1 - 4, sy + 3, C['por_sh'])
    cv.rect(sx1 - 10, sy + 4, sx1 - 4, sy + 12, C['por_sh'])
    outline(cv, sx0, sy - 1, sx1, sy + 16, {C['por'], C['por_sh']})
    tx = (sx0 + sx1) // 2
    cv.rect(tx - 2, sy - 6, tx + 2, sy, C['chrome'])            # tap
    cv.rect(tx - 1, sy - 8, tx + 6, sy - 6, C['chrome'])
    cv.p(tx - 1, sy - 8, C['chrome_hi'])
    outline(cv, tx - 3, sy - 9, tx + 7, sy + 1, {C['chrome'], C['chrome_hi']})
    cv.rect(tx - 2, sy + 15, tx + 2, FLOOR_TOP - 12, C['chrome'])   # trap into the wall
    cv.vline(tx - 2, sy + 15, FLOOR_TOP - 12, C['chrome_hi'])
    cv.rect(tx - 2, FLOOR_TOP - 14, tx + 10, FLOOR_TOP - 10, C['chrome'])
    outline(cv, tx - 3, sy + 15, tx + 11, FLOOR_TOP - 9, {C['chrome'], C['chrome_hi']})


def draw_sign(cv, x0, y0):
    lines = ['EMPLOYEES', 'MUST WASH', 'HANDS']
    w = max(text3x5_width(s) for s in lines) + 8
    h = len(lines) * 7 + 5
    cv.rect(x0, y0, x0 + w, y0 + h, C['sign'])
    cv.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1, OUT)
    cv.hline(x0, x0 + w, y0 + h - 1, C['paper_sh'])
    for i, s in enumerate(lines):
        text3x5(cv.im, x0 + (w - text3x5_width(s)) // 2, y0 + 3 + i * 7, s, C['ink'])
    cv.px = cv.im.load()


def draw_bin(cv, x0):
    x1, top, bot = x0 + 30, 84, FLOOR_TOP + 6
    soft_shadow(cv, (x0 + x1) // 2, bot, x1 - x0 + 4)
    for y in range(top + 3, bot):                 # tapers a little toward the bottom
        inset = 1 + (y - top - 3) * 3 // (bot - top - 3)
        cv.hline(x0 + inset, x1 - inset, y, C['bin'])
        cv.p(x0 + inset + 4, y, C['bin_hi']); cv.p(x0 + inset + 5, y, C['bin_hi'])
        cv.p(x1 - inset - 4, y, C['bin_dk'])
    cv.rect(x0, top, x1, top + 4, C['bin_hi'])    # rim
    cv.hline(x0, x1, top + 3, C['bin_dk'])
    # crumpled paper towel poking out
    for (dx, dy, c) in ((9, -2, 'paper'), (10, -3, 'paper'), (11, -3, 'paper_sh'), (12, -2, 'paper'),
                        (13, -1, 'paper'), (8, -1, 'paper_sh'), (11, -1, 'paper'), (12, -1, 'paper_sh')):
        cv.p(x0 + dx, top + dy, C[c])
    outline(cv, x0 - 1, top - 5, x1 + 1, bot + 1, {C['bin'], C['bin_hi'], C['bin_dk'], C['paper'], C['paper_sh']})


def draw_toilet(cv, cx):
    """Front view: tank with its lid and flush handle, the seat ring with water, bowl, pedestal."""
    floor = FLOOR_TOP + 5
    soft_shadow(cv, cx, floor, 40)
    # tank
    cv.rect(cx - 19, 56, cx + 20, 80, C['por'])
    cv.rect(cx + 13, 57, cx + 20, 80, C['por_sh'])
    cv.vline(cx - 19, 57, 80, C['por_sh'])
    cv.rect(cx - 21, 51, cx + 22, 57, C['por'])          # lid, a touch wider
    cv.hline(cx - 21, cx + 22, 56, C['por_sh'])
    cv.rect(cx + 15, 52, cx + 22, 56, C['por_sh'])
    cv.rect(cx - 15, 60, cx - 8, 63, C['chrome'])        # flush handle
    cv.p(cx - 15, 60, C['chrome_hi'])
    cv.rect(cx - 6, 80, cx + 7, 84, C['por_sh'])         # neck into the bowl
    # seat ring + water, seen from the front and a little above
    ellipse(cv, cx, 89, 25, 7, C['por'])
    ellipse(cv, cx, 89, 19, 4, C['water'])
    ellipse(cv, cx + 2, 90, 13, 2, C['water_dk'])
    cv.hline(cx - 22, cx + 23, 95, C['por_sh'])
    # bowl and pedestal
    for y in range(96, floor):
        k = (y - 96) / (floor - 96)
        half = round(22 - 10 * min(1, k * 1.6))
        cv.hline(cx - half, cx + half + 1, y, C['por'])
        cv.hline(cx + half - 5, cx + half + 1, y, C['por_sh'])
    cv.hline(cx - 12, cx + 13, floor - 1, C['por_dk'])
    outline(cv, cx - 26, 50, cx + 27, floor, {C['por'], C['por_sh'], C['por_dk'], C['water'], C['water_dk'], C['chrome'], C['chrome_hi']})


def draw_paper_roll(cv, x0, y0, floor_path):
    """Holder on the wall; the paper hangs straight down to the floor, then lies across the
    tiles as a thin (foreshortened) ribbon with a soft shadow, gently curling as it goes."""
    cv.rect(x0, y0 + 3, x0 + 4, y0 + 5, C['chrome'])            # arm
    cv.rect(x0 + 3, y0, x0 + 12, y0 + 8, C['paper'])            # roll (mostly unrolled)
    cv.rect(x0 + 9, y0, x0 + 12, y0 + 8, C['paper_sh'])
    outline(cv, x0 - 1, y0 - 1, x0 + 13, y0 + 9, {C['paper'], C['paper_sh'], C['chrome']})
    # hanging sheet: 6px wide, perforated every 8px, one shaded edge
    hx, top, bottom = x0 + 4, y0 + 8, FLOOR_TOP + 9
    for y in range(top, bottom):
        for d in range(6):
            cv.p(hx + d, y, C['paper_sh'] if d == 5 else C['paper'])
        if (y - top) % 8 == 7:
            cv.hline(hx + 1, hx + 5, y, C['paper_sh'])
    cv.vline(hx - 1, top, bottom, OUT)
    cv.vline(hx + 6, top, bottom, OUT)
    # on the floor: a ribbon 3px thick through the path (smooth), shadowed underneath; where it
    # twists it shows its edge (1px)
    pts = [(hx + 3, bottom - 1)] + floor_path
    curve = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        for i in range(n):
            t = i / n
            t = t * t * (3 - 2 * t)              # ease each span so the bends are soft
            curve.append((round(ax + (bx - ax) * i / n), round(ay + (by - ay) * t)))
    curve.append(pts[-1])
    seen = set()
    for i, (x, y) in enumerate(curve):
        if x in seen:
            continue
        seen.add(x)
        thick = 1 if (i // 14) % 5 == 4 else 3   # an occasional twist
        for d in range(thick):
            cv.p(x, y + d, C['paper'])
        cv.p(x, y + thick, C['paper_sh'])
        cv.p(x, y + thick + 1, C['grout'])       # soft shadow on the tiles, not a black outline
        cv.p(x, y - 1, C['paper_sh'] if thick == 3 else C['paper'])


# ---------------------------------------------------------------------------
# the scene
# ---------------------------------------------------------------------------
def sprite(sheet, col, row, w, h):
    return sheet.crop((col * w, row * h, col * w + w, row * h + h))


def main():
    cv = Canvas(W, H)
    draw_room(cv)
    draw_garland(cv)
    draw_mirror_and_sink(cv, 22)
    draw_sign(cv, 104, 30)
    draw_bin(cv, 110)
    draw_toilet(cv, 236)

    rac = Image.open(os.path.join(GAME, 'raccoon.png')).convert('RGBA')
    bottles = Image.open(os.path.join(GAME, 'bottles.png')).convert('RGBA')
    # asleep on its back: the game's knocked-out pose with its eyes closed (sheet cell
    # extra/2), head to the left so the DOM "z z Z" (css/game.css .over__zzz) rises over the tiles
    asleep = sprite(rac, 2, 4, RC_W, RC_H).transpose(Image.FLIP_LEFT_RIGHT)
    bb = asleep.getbbox()
    cx, floor = 196, 168
    rx = cx - (bb[0] + bb[2]) // 2
    ry = floor - bb[3]
    # toilet paper: off the holder, down the wall, across the tiles and under the raccoon
    draw_paper_roll(cv, 272, 92, [(262, 132), (246, 141), (228, 151), (206, 159), (180, 165), (160, 172), (142, 178)])
    soft_shadow(cv, cx, floor, bb[2] - bb[0] - 6)
    # the empty Holiday Reserve (bottle spin frame 2 = lying flat) rolled off under the sink
    reserve, spin_flat, puddle = 4, 6 + 2, 5
    pud = sprite(bottles, puddle, reserve, BT_W, BT_H)
    cv.blit(pud, 60, 170 - BT_H + 2)
    lying = sprite(bottles, spin_flat, reserve, BT_W, BT_H)
    lb = lying.getbbox()
    soft_shadow(cv, 82, 169, lb[2] - lb[0] - 4)
    cv.blit(lying, 82 - (lb[0] + lb[2]) // 2, 169 - lb[3])
    cv.blit(asleep, rx, ry)
    # the Santa hat came off: on the tiles by its head
    hat = raccoon.hat('side').transpose(Image.FLIP_LEFT_RIGHT)       # upright: rotating pixel art smears it
    hx = rx + bb[0] - hat.width - 3
    soft_shadow(cv, hx + hat.width // 2, 172, hat.width - 6)
    cv.blit(hat, hx, 172 - hat.height + 1)

    cv.im.save(os.path.join(GAME, 'bathroom.png'), optimize=True)
    head = (rx + bb[0] + 10, ry + bb[1] - 8)           # where the z's start: just above the head
    if PREVIEW:
        upscale(cv.im, 3).save(os.path.join(PREVIEW, 'bathroom.png'))
    print('bathroom ok', cv.im.size, 'head at', head, f'({head[0] / W:.0%}, {head[1] / H:.0%})')


if __name__ == '__main__':
    main()
