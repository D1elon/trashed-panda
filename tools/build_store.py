#!/usr/bin/env python3
"""Draw the ABC-store backdrop as native-resolution pixel art, decorated for the holidays.

    python3 tools/build_store.py

The layout matches the original game's background (restroom door on the left, two
metal liquor shelves, white tile floor) but is redrawn on the same pixel grid as the
sprites. Every coordinate the game needs (shelf boards, door, lights) is exported to
js/game/world-data.js so art and collision can never drift apart.
"""
import json
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, text3x5, text3x5_width  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets', 'game')
PREVIEW = os.environ.get('PREVIEW_DIR')

W, H = 800, 270
CEIL_H = 12
WALL_BOTTOM = 196          # wall / floor junction
FLOOR_LANE = 232           # raccoon feet when on the floor
SHELF_W = 268
SHELF_BASE = 208
BOARD_TOPS = [196, 158, 120, 82]   # level 0..3 board surfaces (feet / bottle base)
SHELF_TOP = 38
SHELF_XS = [140, 456]
BOTTLES_PER_ROW = 8
DOOR = (18, 106, 86, WALL_BOTTOM)  # x0, y0, x1, y1
SPAWN_X = 112
TREE_X = 766

C = {k: hexrgb(v) for k, v in {
    'out': '#1f2424', 'wall': '#c4c4c5', 'wall_hi': '#cdcdce', 'wall_sh': '#b6b6b8', 'wall_sh2': '#aeaeb0',
    'ceil': '#dedad1', 'ceil_sh': '#cfcbc1', 'tbar': '#a9a69d', 'tbar_dk': '#8f8c84',
    'lamp': '#f7f8f2', 'lamp_edge': '#d9dbd2',
    'base_hi': '#a3aaa8', 'base': '#6a7472', 'base_dk': '#4a5251',
    'tile': '#fbfbfa', 'tile2': '#f2f2f1', 'grout': '#b4b4b2', 'grout_lt': '#d3d3d1', 'refl': '#e6e7e6',
    'sh_cap_top': '#adb5b2', 'sh_cap': '#949d9a', 'sh_cap_dk': '#7d8784',
    'sh_face_hi': '#8a9491', 'sh_face': '#6c7875', 'sh_face_dk': '#56615f',
    'sh_surf': '#7c8784', 'sh_back': '#5d6664', 'sh_back_dk': '#4b5352', 'sh_side': '#68726f', 'sh_side_dk': '#4f5857',
    'tag': '#f1efe6', 'tag_ln': '#9aa09d', 'tag_red': '#c8463c',
    'door': '#8e664f', 'door_hi': '#a57a5f', 'door_dk': '#745b4c', 'door_dk2': '#5e4a3e',
    'frame': '#6b7270', 'frame_hi': '#8b9290', 'knob': '#9aa1a0', 'knob_hi': '#d6dbda',
    'sign': '#23497a', 'sign_hi': '#3a66a0', 'sign_fg': '#e9eef5',
    'pine': '#2f6b3f', 'pine_hi': '#4b8f53', 'pine_dk': '#1d4a2b', 'pine_out': '#14301d',
    'red': '#d23a3a', 'red_dk': '#94202b', 'red_hi': '#f2706a', 'gold': '#f2c14e', 'gold_dk': '#b9862a',
    'trunk': '#6b4630', 'trunk_dk': '#4b3021', 'wire': '#2b3a2e',
    'gift_a': '#c63a3a', 'gift_b': '#2f7d4a', 'gift_c': '#e7c35a', 'ribbon': '#f6f1e7', 'ribbon2': '#d23a3a',
}.items()}


class Canvas:
    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.im = Image.new('RGBA', (w, h), fill)
        self.px = self.im.load()
        self.w, self.h = w, h

    def p(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[x, y] = c

    def rect(self, x0, y0, x1, y1, c):  # inclusive-exclusive
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[x, y] = c

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y + 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x + 1, y1, c)

    def frame(self, x0, y0, x1, y1, c):
        self.hline(x0, x1, y0, c); self.hline(x0, x1, y1 - 1, c)
        self.vline(x0, y0, y1, c); self.vline(x1 - 1, y0, y1, c)

    def blit(self, other, x, y):
        self.im.alpha_composite(other.im if isinstance(other, Canvas) else other, (x, y))
        self.px = self.im.load()


def draw_wall(cv):
    cv.rect(0, 0, W, WALL_BOTTOM, C['wall'])
    # soft shading under the ceiling
    cv.hline(0, W, CEIL_H, C['wall_sh2'])
    cv.hline(0, W, CEIL_H + 1, C['wall_sh'])
    cv.hline(0, W, CEIL_H + 2, C['wall_sh'])
    for x in range(0, W, 2):
        cv.p(x, CEIL_H + 3, C['wall_sh'])
    # baseboard
    cv.rect(0, WALL_BOTTOM - 8, W, WALL_BOTTOM, C['base'])
    cv.hline(0, W, WALL_BOTTOM - 8, C['base_hi'])
    cv.hline(0, W, WALL_BOTTOM - 1, C['base_dk'])


def draw_ceiling(cv):
    cv.rect(0, 0, W, CEIL_H, C['ceil'])
    for x in range(0, W, 32):
        cv.vline(x, 0, CEIL_H, C['tbar'])
    cv.hline(0, W, CEIL_H - 1, C['tbar_dk'])
    cv.hline(0, W, CEIL_H - 2, C['tbar'])
    # speckled acoustic tile texture
    rnd = random.Random(7)
    for _ in range(420):
        x, y = rnd.randrange(W), rnd.randrange(CEIL_H - 2)
        if x % 32:
            cv.p(x, y, C['ceil_sh'])
    # fluorescent panels
    for x in (224, 384, 544, 704):
        cv.rect(x + 2, 1, x + 30, CEIL_H - 2, C['lamp'])
        cv.frame(x + 2, 1, x + 30, CEIL_H - 2, C['lamp_edge'])
    # the hole the raccoon drops through
    hx = SPAWN_X - 16
    cv.rect(hx + 1, 0, hx + 32, CEIL_H - 2, hexrgb('#141313'))
    cv.hline(hx + 1, hx + 32, CEIL_H - 3, hexrgb('#2a2826'))
    for x in range(hx + 3, hx + 30, 5):  # dangling insulation scraps
        cv.p(x, CEIL_H - 2, hexrgb('#d9c79a'))


def draw_floor(cv):
    top = WALL_BOTTOM
    cv.rect(0, top, W, H, C['tile'])
    # rows get taller toward the viewer (light perspective)
    y, h, rows = top, 7, []
    while y < H:
        rows.append((y, min(H, y + h)))
        y += h; h += 2
    for i, (y0, y1) in enumerate(rows):
        for xi, x in enumerate(range(0, W, 22)):
            if (i + xi) % 2:
                cv.rect(x + 1, y0 + 1, x + 22, y1, C['tile2'])
        cv.hline(0, W, y0, C['grout'])
        cv.hline(0, W, y0 + 1, C['grout_lt']) if y0 + 1 < y1 else None
    for x in range(0, W, 22):
        cv.vline(x, top, H, C['grout'])
    # faint reflections of the door and shelves on the glossy tiles
    for (x0, x1) in [(DOOR[0], DOOR[2])] + [(sx, sx + SHELF_W) for sx in SHELF_XS]:
        for yy in range(SHELF_BASE + 1 if x0 > 100 else top + 1, min(H, SHELF_BASE + 22)):
            for xx in range(x0 + 2, x1 - 2):
                if cv.px[xx, yy] in (C['tile'], C['tile2']) and (xx + yy) % 2 == 0:
                    cv.p(xx, yy, C['refl'])


def draw_door(cv):
    x0, y0, x1, y1 = DOOR
    cv.rect(x0 - 3, y0 - 3, x1 + 3, y1, C['frame'])
    cv.hline(x0 - 3, x1 + 3, y0 - 3, C['frame_hi'])
    cv.frame(x0 - 4, y0 - 4, x1 + 4, y1 + 1, C['out'])
    cv.rect(x0, y0, x1, y1, C['door'])
    cv.vline(x0, y0, y1, C['door_hi']); cv.hline(x0, x1, y0, C['door_hi'])
    cv.vline(x1 - 1, y0, y1, C['door_dk'])
    # two recessed panels with vertical grooves (matches the original door)
    for (py0, py1) in ((y0 + 8, y0 + 44), (y0 + 52, y1 - 8)):
        cv.frame(x0 + 8, py0, x1 - 8, py1, C['door_dk2'])
        cv.hline(x0 + 9, x1 - 8, py1, C['door_hi'])
        for gx in range(x0 + 18, x1 - 9, 11):
            cv.vline(gx, py0 + 3, py1 - 3, C['door_dk'])
            cv.vline(gx + 1, py0 + 3, py1 - 3, C['door_hi'])
    # hinges + knob
    for hy in (y0 + 10, y1 - 16):
        cv.rect(x0 - 1, hy, x0 + 1, hy + 6, C['knob'])
    kx, ky = x1 - 10, y0 + 50
    cv.rect(kx - 2, ky - 2, kx + 3, ky + 3, C['knob'])
    cv.frame(kx - 3, ky - 3, kx + 4, ky + 4, C['out'])
    cv.p(kx - 1, ky - 1, C['knob_hi'])
    # restroom sign
    sx, sy = x1 + 10, y0 + 22
    cv.rect(sx, sy, sx + 26, sy + 16, C['sign'])
    cv.frame(sx - 1, sy - 1, sx + 27, sy + 17, C['out'])
    cv.hline(sx, sx + 26, sy, C['sign_hi'])
    for fx in (sx + 7, sx + 18):          # two little figures
        cv.rect(fx, sy + 3, fx + 2, sy + 5, C['sign_fg'])
        cv.rect(fx - 1, sy + 6, fx + 3, sy + 10, C['sign_fg'])
        cv.vline(fx, sy + 10, sy + 13, C['sign_fg']); cv.vline(fx + 1, sy + 10, sy + 13, C['sign_fg'])
    cv.rect(sx + 17, sy + 9, sx + 21, sy + 11, C['sign_fg'])  # skirt
    cv.vline(sx + 13, sy + 3, sy + 14, C['sign_hi'])
    # wreath with a red bow
    draw_wreath(cv, (x0 + x1) // 2, y0 + 26)


def draw_wreath(cv, cx, cy, r=9):
    for y in range(-r - 2, r + 3):
        for x in range(-r - 2, r + 3):
            d = math.hypot(x, y)
            if r - 4.5 <= d <= r + 0.5:
                shade = C['pine_hi'] if (x + y) % 3 == 0 and y < 0 else C['pine'] if (x * 7 + y * 3) % 5 else C['pine_dk']
                cv.p(cx + x, cy + y, shade)
            elif r + 0.5 < d <= r + 1.6 or r - 5.6 <= d < r - 4.5:
                cv.p(cx + x, cy + y, C['pine_out'])
    for ang in range(0, 360, 45):
        bx = cx + round(math.cos(math.radians(ang)) * (r - 2))
        by = cy + round(math.sin(math.radians(ang)) * (r - 2))
        cv.p(bx, by, C['red'])
    # bow
    bow = ['K..K..K..K', 'KRRK.KRRK.', 'KRrRKRrRK.', '.KRRRRRK..', '..KRhRK...', '.KRK.KRK..', 'KRK...KRK.', 'KK.....KK.']
    pal = {'K': C['out'], 'R': C['red'], 'r': C['red_dk'], 'h': C['red_hi']}
    for y, row in enumerate(bow):
        for x, ch in enumerate(row):
            if ch in pal:
                cv.p(cx - 4 + x, cy + r - 3 + y, pal[ch])


def draw_shelf(cv, x0):
    x1 = x0 + SHELF_W
    top, base = SHELF_TOP, SHELF_BASE
    # back panel
    cv.rect(x0, top, x1, base, C['sh_back'])
    # side uprights
    for (sx0, sx1, inner) in ((x0, x0 + 7, x0 + 6), (x1 - 7, x1, x1 - 7)):
        cv.rect(sx0, top, sx1, base, C['sh_side'])
        cv.vline(inner, top, base, C['sh_side_dk'])
    cv.vline(x0 + 1, top, base, C['sh_cap'])
    # top cap
    cv.rect(x0, top, x1, top + 4, C['sh_cap_top'])
    cv.rect(x0, top + 4, x1, top + 10, C['sh_cap'])
    cv.hline(x0, x1, top + 10, C['sh_cap_dk'])
    # boards
    for i, by in enumerate(BOARD_TOPS):
        # compartment shadow under the board above
        above = (BOARD_TOPS[i + 1] + 5) if i + 1 < len(BOARD_TOPS) else top + 11
        cv.rect(x0 + 7, above, x1 - 7, above + 3, C['sh_back_dk'])
        cv.rect(x0 + 7, by - 3, x1 - 7, by, C['sh_surf'])
        cv.rect(x0, by, x1, by + 5, C['sh_face'])
        cv.hline(x0, x1, by, C['sh_face_hi'])
        cv.hline(x0, x1, by + 4, C['sh_face_dk'])
        cv.hline(x0, x1, by + 5, C['out'])
        # price tags on the board lip
        for k in range(BOTTLES_PER_ROW):
            tx = x0 + 18 + k * 32
            cv.rect(tx, by + 1, tx + 7, by + 4, C['tag'])
            cv.hline(tx + 1, tx + 6, by + 2, C['tag_ln'])
            if (k * 3 + i) % 7 == 0:
                cv.hline(tx + 1, tx + 4, by + 2, C['tag_red'])
    # kick plate below the bottom board
    cv.rect(x0, BOARD_TOPS[0] + 6, x1, base, C['sh_side_dk'])
    # outline
    cv.frame(x0 - 1, top - 1, x1 + 1, base + 1, C['out'])
    cv.hline(x0, x1, top + 4, C['sh_cap_dk'])
    return [{'x': x0 + 22 + k * 32} for k in range(BOTTLES_PER_ROW)]


def draw_garland(cv):
    """Scalloped pine garland along the ceiling line with bows and bulb positions."""
    bulbs = []
    swag = 40
    for sx in range(0, W, swag):
        for x in range(sx, sx + swag):
            t = (x - sx) / swag
            y = CEIL_H + 2 + round(math.sin(t * math.pi) * 7)
            for dy in range(-1, 3):
                c = C['pine'] if dy in (0, 1) else C['pine_dk'] if dy == 2 else C['pine_hi']
                if (x * 5 + dy * 3) % 7 == 0:
                    c = C['pine_hi']
                cv.p(x, y + dy, c)
            cv.p(x, y + 3, C['pine_out'])
            if x % 2 == 0 and (x // 2) % 3 == 0:
                cv.p(x, y - 2, C['pine_dk'])
        # bow at each swag join
        bx = sx
        for (dx, dy, c) in ((-2, 0, 'red'), (-1, 0, 'red_hi'), (1, 0, 'red_hi'), (2, 0, 'red'),
                            (-2, 1, 'red_dk'), (2, 1, 'red_dk'), (0, 1, 'red'), (-1, 2, 'red'), (1, 2, 'red'),
                            (-1, 3, 'red_dk'), (1, 3, 'red_dk'), (0, 0, 'red_dk')):
            cv.p(bx + dx, CEIL_H + 1 + dy, C[c])
        for k in (0.25, 0.5, 0.75):
            x = sx + round(swag * k)
            y = CEIL_H + 2 + round(math.sin(k * math.pi) * 7) + 3
            bulbs.append({'x': x, 'y': y})
    return bulbs


def draw_shelf_lights(cv, x0):
    """A sagging light string along the shelf's top cap. Bulbs are drawn (and twinkle) at runtime."""
    bulbs = []
    x1 = x0 + SHELF_W
    span = 33.5
    n = int(SHELF_W / span)
    for i in range(n):
        sx = x0 + i * span
        for x in range(int(sx), int(sx + span) + 1):
            t = (x - sx) / span
            y = SHELF_TOP + 6 + round(math.sin(t * math.pi) * 4)
            if x0 <= x < x1:
                cv.p(x, y, C['wire'])
        bx = round(sx + span / 2)
        bulbs.append({'x': bx, 'y': SHELF_TOP + 11})
    return bulbs


def draw_tree(cv, cx):
    """Little store Christmas tree with presents, at the right end of the aisle."""
    base = WALL_BOTTOM + 4
    cv.rect(cx - 3, base - 12, cx + 4, base + 2, C['trunk'])
    cv.vline(cx + 3, base - 12, base + 2, C['trunk_dk'])
    cv.frame(cx - 4, base - 12, cx + 5, base + 3, C['out'])
    # tiers: (bottom y, half width, height); drawn top-down so lower tiers overlap
    tiers = [(base - 70, 9, 18), (base - 54, 14, 20), (base - 38, 19, 22), (base - 22, 24, 24), (base - 8, 29, 24)]
    ornament_spots = []
    for (by, half, h) in tiers:
        for row in range(h):
            y = by - h + row
            t = (row + 1) / h
            w = max(1, round(half * (0.25 + 0.75 * t)))
            for x in range(cx - w, cx + w + 1):
                rel = (x - cx) / max(1, w)
                if x in (cx - w, cx + w):
                    c = C['pine_out']
                elif row >= h - 2:
                    c = C['pine_dk']
                elif rel < -0.35 and (row + x) % 3 != 0:
                    c = C['pine_hi']
                elif rel > 0.45:
                    c = C['pine_dk'] if (row + x) % 2 else C['pine']
                else:
                    c = C['pine'] if (x * 3 + row) % 5 else C['pine_hi']
                cv.p(x, y, c)
        # scalloped bottom edge
        w = half
        for x in range(cx - w, cx + w + 1):
            if (x - cx) % 4 in (0, 1):
                cv.p(x, by, C['pine_out'])
            else:
                cv.p(x, by, C['pine_dk'])
        for k in range(-half + 5, half - 3, 7):
            ornament_spots.append((cx + k, by - 3))
    # star
    star = ['...K...', '..KYK..', 'KKKYKKK', 'KYYwYYK', '.KYYYK.', 'KYK.KYK', 'KK...KK']
    sy = tiers[0][0] - tiers[0][2] - 5
    for y, row in enumerate(star):
        for x, ch in enumerate(row):
            c = {'K': C['gold_dk'], 'Y': C['gold'], 'w': hexrgb('#fff6cf')}.get(ch)
            cv.p(cx - 3 + x, sy + y, c)
    # presents
    for (gx, gw, gh, col, rib) in ((cx - 31, 16, 12, 'gift_a', 'ribbon'), (cx + 12, 17, 10, 'gift_b', 'ribbon2'), (cx - 13, 12, 8, 'gift_c', 'ribbon2')):
        gy = base + 8 - gh
        cv.rect(gx, gy, gx + gw, gy + gh, C[col])
        cv.vline(gx + gw // 2, gy, gy + gh, C[rib]); cv.hline(gx, gx + gw, gy + gh // 2 - 1, C[rib])
        cv.frame(gx - 1, gy - 1, gx + gw + 1, gy + gh + 1, C['out'])
        cv.p(gx + gw // 2 - 1, gy - 2, C[rib]); cv.p(gx + gw // 2 + 1, gy - 2, C[rib])
    return [{'x': x, 'y': y} for (x, y) in ornament_spots]


def draw_poster(cv, x0, y0):
    """'HOLIDAY SPIRITS' sale poster taped to the wall."""
    w, h = 34, 42
    cv.rect(x0, y0, x0 + w, y0 + h, C['red'])
    cv.frame(x0, y0, x0 + w, y0 + h, C['red_dk'])
    cv.frame(x0 - 1, y0 - 1, x0 + w + 1, y0 + h + 1, C['out'])
    cv.rect(x0 + 2, y0 + 2, x0 + w - 2, y0 + 15, C['ribbon'])
    for i, word in enumerate(('HOLIDAY', 'SPIRITS')):
        tw = text3x5_width(word, 1)
        text3x5(cv.im, x0 + (w - tw) // 2, y0 + 3 + i * 6, word, C['red_dk'])
    cv.px = cv.im.load()
    # little bottle + percent
    bx = x0 + 7
    cv.rect(bx + 1, y0 + 19, bx + 3, y0 + 22, C['gold'])
    cv.rect(bx, y0 + 22, bx + 4, y0 + 33, C['gold'])
    cv.rect(bx + 1, y0 + 25, bx + 3, y0 + 29, C['ribbon'])
    cv.frame(bx - 1, y0 + 21, bx + 5, y0 + 34, C['red_dk'])
    text3x5(cv.im, x0 + 15, y0 + 21, '25%', C['ribbon'])
    text3x5(cv.im, x0 + 15, y0 + 28, 'OFF', C['ribbon'])
    cv.px = cv.im.load()
    text3x5(cv.im, x0 + 5, y0 + 36, 'NOV-DEC', C['gold'], spacing=0)
    cv.px = cv.im.load()
    # tape
    for (tx, ty) in ((x0 - 2, y0 - 2), (x0 + w - 3, y0 - 2)):
        cv.rect(tx, ty, tx + 5, ty + 3, hexrgb('#e8e2c8'))


def main():
    cv = Canvas(W, H)
    draw_wall(cv)
    draw_ceiling(cv)
    draw_floor(cv)
    draw_door(cv)
    draw_poster(cv, 98, 54)
    rows = [draw_shelf(cv, x) for x in SHELF_XS]
    light_bulbs = draw_garland(cv)
    shelf_bulbs = []
    for x in SHELF_XS:
        shelf_bulbs += draw_shelf_lights(cv, x)
    tree_bulbs = draw_tree(cv, TREE_X)
    cv.im.save(os.path.join(OUT, 'store.png'), optimize=True)

    # intact ceiling tile (drawn over the hole until the raccoon crashes through)
    tile = Canvas(31, CEIL_H - 2)
    tile.rect(0, 0, 31, CEIL_H - 2, C['ceil'])
    rnd = random.Random(3)
    for _ in range(30):
        tile.p(rnd.randrange(31), rnd.randrange(CEIL_H - 2), C['ceil_sh'])
    tile.hline(0, 31, CEIL_H - 3, C['tbar'])
    tile.im.save(os.path.join(OUT, 'ceiling-tile.png'))

    world = {
        'w': W, 'h': H, 'ceilH': CEIL_H, 'wallBottom': WALL_BOTTOM, 'floorLane': FLOOR_LANE,
        'shelf': {'w': SHELF_W, 'top': SHELF_TOP, 'base': SHELF_BASE, 'boardTops': BOARD_TOPS, 'xs': SHELF_XS,
                  'bottleXs': [[b['x'] for b in r] for r in rows]},
        'door': {'x0': DOOR[0], 'y0': DOOR[1], 'x1': DOOR[2], 'y1': DOOR[3]},
        'spawnX': SPAWN_X, 'hole': {'x': SPAWN_X - 15, 'y': 0, 'w': 31, 'h': CEIL_H - 2},
        'bulbs': {'garland': light_bulbs, 'shelf': shelf_bulbs, 'tree': tree_bulbs},
        'tree': {'x': TREE_X, 'base': WALL_BOTTOM + 6},
    }
    js = '// Generated by tools/build_store.py. Do not edit by hand.\nexport const WORLD = ' + json.dumps(world, indent=1) + ';\n'
    with open(os.path.join(ROOT, 'js', 'game', 'world-data.js'), 'w') as fh:
        fh.write(js)
    if PREVIEW:
        upscale(cv.im, 2).save(os.path.join(PREVIEW, 'store.png'))
    print('store ok', cv.im.size, len(light_bulbs), len(shelf_bulbs), len(tree_bulbs))


if __name__ == '__main__':
    main()
