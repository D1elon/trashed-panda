#!/usr/bin/env python3
"""Build the game sprites.

    python3 tools/build_sprites.py

Outputs (all at native pixel resolution, drawn with nearest-neighbour scaling):
    assets/game/raccoon.png        6x10 grid of 80x66 frames (rows 0-4 plain, 5-9 Santa hat),
                                   drawn by tools/raccoon.py
    assets/game/bottles.png        frames for 5 bottle types (see BOTTLE_FRAMES)
    js/game/sprite-data.js         frame rects + anchors consumed by the renderer
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import repixelize, quantize, remove_specks, upscale  # noqa: E402
import raccoon  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'tools', 'source-art')
OUT = os.path.join(ROOT, 'assets', 'game')
os.makedirs(OUT, exist_ok=True)

PREVIEW = os.environ.get('PREVIEW_DIR')

# ---------------------------------------------------------------------------
# Raccoon: drawn from scratch by tools/raccoon.py (no source art)
# ---------------------------------------------------------------------------
RC_W, RC_H = raccoon.CW, raccoon.CH
SHEET_ROWS = raccoon.SHEET_ROWS


def grid(frames, cols, cw, ch):
    rows = (len(frames) + cols - 1) // cols
    im = Image.new('RGBA', (cols * cw, rows * ch), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.alpha_composite(f, ((i % cols) * cw, (i // cols) * ch))
    return im


def split(im, cols, cw, ch, n):
    return [im.crop(((i % cols) * cw, (i // cols) * ch, (i % cols) * cw + cw, (i // cols) * ch + ch)) for i in range(n)]


def build_raccoon():
    out, cells = raccoon.sheet()
    for i, c in enumerate(cells):                    # nothing may touch the cell edge (it would be cut off)
        if c is None:
            continue
        op = c.c != '.'
        if op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any():
            raise SystemExit(f'raccoon frame {i} touches the edge of its cell')
    out.save(os.path.join(OUT, 'raccoon.png'), optimize=True)
    return out


# ---------------------------------------------------------------------------
# Bottles
# ---------------------------------------------------------------------------
BT_W, BT_H = 40, 34
BOTTLE_KINDS = ['vodka', 'whiskey', 'wine', 'tequila']
# x ranges of each frame column in the source sheet (found by gap segmentation)
BOTTLE_COLS = [(176, 296), (400, 656), (660, 916), (930, 1256), (1265, 1520), (1570, 1846)]
FRAME_NAMES = ['up', 'tilt', 'crack', 'burst', 'shards', 'puddle']


def build_bottles():
    sheet = Image.open(os.path.join(SRC, 'bottle-sheet.png'))
    H = sheet.height
    rows = []
    for r in range(4):
        y0, y1 = round(r * H / 4), round((r + 1) * H / 4)
        row = []
        for (x0, x1) in BOTTLE_COLS:
            crop = sheet.crop((x0, y0, x1, y1))
            p = repixelize(crop, 8)
            p = remove_specks(p, 3)
            # fit into a BT_W x BT_H cell, bottom-centred
            bb = p.getchannel('A').getbbox()
            p = p.crop(bb)
            cell = Image.new('RGBA', (BT_W, BT_H), (0, 0, 0, 0))
            cell.alpha_composite(p, ((BT_W - p.width) // 2, BT_H - p.height))
            row.append(cell)
        rows.append(row)
    flat = [c for row in rows for c in row]
    q = quantize(grid(flat, 6, BT_W, BT_H), 40)
    flat = split(q, 6, BT_W, BT_H, 24)
    rows = [flat[i * 6:(i + 1) * 6] for i in range(4)]
    rows.append([gold_swap(c) for c in rows[3]])  # Holiday Reserve from the tequila bottle
    # derived spin frames: 90/180/270 rotations of upright, plus rotations of the 45deg tilt
    out_rows = []
    for row in rows:
        up, tilt = row[0], row[1]
        upc = up.crop(up.getchannel('A').getbbox())
        tc = tilt.crop(tilt.getchannel('A').getbbox())
        spin = [upc, tc,
                upc.rotate(-90, expand=True), tc.rotate(-90, expand=True),
                upc.rotate(180, expand=True), tc.rotate(180, expand=True),
                upc.rotate(90, expand=True), tc.rotate(90, expand=True)]
        spin_cells = []
        for s in spin:
            c = Image.new('RGBA', (BT_W, BT_H), (0, 0, 0, 0))
            c.alpha_composite(s, ((BT_W - s.width) // 2, (BT_H - s.height) // 2))
            spin_cells.append(c)
        out_rows.append(row + spin_cells)
    cols = len(out_rows[0])
    img = grid([c for r in out_rows for c in r], cols, BT_W, BT_H)
    img.save(os.path.join(OUT, 'bottles.png'), optimize=True)
    # bottle metrics for placement
    up = out_rows[0][0]
    bb = up.getchannel('A').getbbox()
    return img, {'cols': cols, 'upBox': bb}


def gold_swap(cell):
    """Recolour the pale tequila bottle into a candy-red 'Holiday Reserve' with a gold label."""
    a = np.asarray(cell).astype(np.float32).copy()
    m = a[..., 3] > 0
    rgb = a[..., :3] / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = 0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
    green = (a[..., 1] >= a[..., 0]) & (a[..., 1] >= a[..., 2])
    dark = m & (lum < 45)
    label = m & ~dark & green & (sat > 0.32)
    glass = m & ~dark & ~label & (a[..., 2] > 60) | (m & ~dark & ~label & green)
    t = np.clip((lum - 70) / 170, 0, 1)[..., None]
    red = np.array([120, 14, 28]) * (1 - t) + np.array([255, 92, 88]) * t
    tl = np.clip((lum - 40) / 150, 0, 1)[..., None]
    gold = np.array([140, 84, 14]) * (1 - tl) + np.array([255, 222, 110]) * tl
    a[..., :3] = np.where(glass[..., None], red, a[..., :3])
    a[..., :3] = np.where(label[..., None], gold, a[..., :3])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def main():
    rac = build_raccoon()
    bot, bmeta = build_bottles()
    data = {
        'raccoon': {'w': RC_W, 'h': RC_H, 'cols': 6, 'rows': SHEET_ROWS, 'santaRowOffset': 5,
                    'cx': raccoon.CX, 'climbFeet': raccoon.CLIMB_FEET},
        'bottles': {'w': BT_W, 'h': BT_H, 'kinds': BOTTLE_KINDS + ['reserve'], 'frames': FRAME_NAMES,
                    'spinStart': 6, 'spinCount': 8, 'cols': bmeta['cols'], 'upBox': bmeta['upBox']},
    }
    js = '// Generated by tools/build_sprites.py. Do not edit by hand.\nexport const SPRITES = ' + json.dumps(data, indent=1) + ';\n'
    with open(os.path.join(ROOT, 'js', 'game', 'sprite-data.js'), 'w') as fh:
        fh.write(js)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        for name, im, k in (('raccoon', rac, 3), ('bottles', bot, 4)):
            bg = Image.new('RGBA', im.size, (88, 96, 96, 255))
            bg.alpha_composite(im)
            upscale(bg, k).save(os.path.join(PREVIEW, f'sprite_{name}.png'))
    print('sprites ok', rac.size, bot.size)


if __name__ == '__main__':
    main()
