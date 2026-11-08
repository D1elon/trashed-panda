#!/usr/bin/env python3
"""Build all game sprites from the original high-res art.

    python3 tools/build_sprites.py

Outputs (all at native pixel resolution, drawn with nearest-neighbour scaling):
    assets/game/raccoon.png        6x10 grid of 80x66 frames (rows 0-4 plain, 5-9 Santa hat)
    assets/game/bottles.png        frames for 5 bottle types (see BOTTLE_FRAMES)
    assets/game/bathroom.png       game-over scene
    js/game/sprite-data.js         frame rects + anchors consumed by the renderer
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import repixelize, quantize, remove_specks, upscale, hexrgb  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'tools', 'source-art')
OUT = os.path.join(ROOT, 'assets', 'game')
os.makedirs(OUT, exist_ok=True)

PREVIEW = os.environ.get('PREVIEW_DIR')

# ---------------------------------------------------------------------------
# Raccoon
# ---------------------------------------------------------------------------
RC_W, RC_H = 80, 66
ROWS = ['walk', 'climb', 'drink', 'swipe']
SHEET_ROWS = ROWS + ['extra']  # extra: 0 blink, 1 knocked out
PINK = hexrgb('#e8798f')
PINK_DARK = hexrgb('#b24a62')


def load_raccoon_frames():
    sheet = Image.open(os.path.join(SRC, 'raccoon-sheet.png'))
    H = sheet.height
    frames, pink_masks = [], []
    for row in range(4):
        for col in range(6):
            y0 = round(row * H / 4)
            cell = sheet.crop((col * 320, y0, col * 320 + 320, y0 + 262))
            p = repixelize(cell, 4, size=(RC_W, RC_H))
            p = remove_specks(p, 6, light_thresh=600)
            a = np.asarray(p).astype(int)
            pink = (a[..., 3] > 0) & (a[..., 0] > a[..., 1] + 45) & (a[..., 0] > a[..., 2] + 15) & (a[..., 0] > 150)
            frames.append(p)
            pink_masks.append(pink)
    return frames, pink_masks


def grid(frames, cols, cw, ch):
    rows = (len(frames) + cols - 1) // cols
    im = Image.new('RGBA', (cols * cw, rows * ch), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.alpha_composite(f, ((i % cols) * cw, (i // cols) * ch))
    return im


def split(im, cols, cw, ch, n):
    return [im.crop(((i % cols) * cw, (i // cols) * ch, (i % cols) * cw + cw, (i // cols) * ch + ch)) for i in range(n)]


# Santa hat, side view, facing right. Brim sits on the head, tail flops back.
#   K outline  R red  r shadow red  h highlight  W fur  w fur shade
HAT_SIDE = [
    '.......KKKK.....',
    '.....KKRRRRK....',
    '...KKRRRhRRrK...',
    '..KRRRRRRRRRrK..',
    '.KRRKKKRRRRRRrK.',
    'KWWK..KRRRRRRrK.',
    'KWWwK.KRRRRRRRrK',
    'KwwwK.KRRRRRRRrK',
    '.KKK.KWWWWWWWWWK',
    '....KWWWWWWWWWWK',
    '....KwwwwwwwwwwK',
    '.....KKKKKKKKKK.',
]
# Back view (climbing): symmetric cone, tip flopped to the left.
HAT_BACK = [
    '..KKK..........',
    '.KWWWK.KKKK....',
    'KWWWwKKRRRRK...',
    'KwwwKRRRRRRrK..',
    '.KKKRRRhRRRRrK.',
    '...KRRRRRRRRrK.',
    '..KRRRRRRRRRRrK',
    '..KRRRRRRRRRRrK',
    '.KWWWWWWWWWWWWK',
    '.KWWWWWWWWWWWWK',
    '.KwwwwwwwwwwwwK',
    '..KKKKKKKKKKKK.',
]
HAT_PAL = {
    'K': hexrgb('#2a1410'), 'R': hexrgb('#d8343a'), 'r': hexrgb('#9c1f2b'),
    'h': hexrgb('#f26a5e'), 'W': hexrgb('#f6f1e7'), 'w': hexrgb('#c8bfb2'),
}


def art(rows, pal, flip=False):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                px[x, y] = pal[ch]
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


# Where the hat sits for each row: head search window (x range) and a nudge.
HAT_RULES = {
    # row: (x0, x1, dx, dy, hat)
    'walk':  (48, 74, -1, -5, 'side'),
    'climb': (20, 60, 0, 2, 'back'),
    'drink': (48, 74, -1, -5, 'side'),
    'swipe': (26, 58, 0, -5, 'side'),
}


def head_anchor(frame, x0, x1):
    a = np.asarray(frame)[..., 3] > 0
    sub = a[:, x0:x1]
    ys = np.where(sub.any(1))[0]
    top = int(ys[0])
    band = sub[top:top + 9]
    xs = np.where(band.any(0))[0]
    cx = x0 + (int(xs[0]) + int(xs[-1])) / 2
    return cx, top


def feet_y(frame):
    a = np.asarray(frame)[..., 3] > 0
    return int(np.where(a.any(1))[0][-1])


# Curated raccoon palette: one ramp, chosen by hand, instead of the noisy source colours.
RACCOON_RAMP = [  # (max luminance, colour)
    (24, '#1a120c'),   # 0 outline
    (44, '#402d20'),   # 1 mask + tail rings (light enough for a black pupil to read)
    (62, '#4d3b25'),   # 2 deep shadow
    (80, '#62502f'),   # 3 shadow fur
    (100, '#76643c'),  # 4 base fur
    (122, '#8d7a50'),  # 5 highlight fur
    (999, '#b29c72'),  # 6 light tan / muzzle / belly
]
R_PAL = [hexrgb(c) for _, c in RACCOON_RAMP]
PINK_IDX = 100


def _lum(p):
    return 0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]


def clean_frame(img):
    """Repaint a re-pixelized frame onto the curated ramp, kill speckle noise,
    add rim light / belly shadow and a uniform 1px outline."""
    a = np.asarray(img)
    h, w = a.shape[:2]
    idx = np.full((h, w), -1, int)
    for y in range(h):
        for x in range(w):
            p = a[y, x]
            if p[3] == 0:
                continue
            if int(p[0]) > int(p[1]) + 40:
                idx[y, x] = PINK_IDX
                continue
            L = _lum(p)
            for i, (m, _) in enumerate(RACCOON_RAMP):
                if L < m:
                    idx[y, x] = i
                    break
    # majority filter: pixels with no 4-neighbour of their own colour join the local majority
    for _ in range(2):
        out = idx.copy()
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                v = idx[y, x]
                if v < 0 or v in (0, PINK_IDX):
                    continue
                if any(idx[y + dy, x + dx] == v for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                nb = [idx[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx)]
                nb = [n for n in nb if n > 0 and n != PINK_IDX] or [n for n in nb if n >= 0]
                vals, counts = np.unique(nb, return_counts=True)
                out[y, x] = vals[counts.argmax()]
        idx = out
    opaque = idx >= 0
    # rim light along the back, shadow along the belly (per column)
    for x in range(w):
        col = np.where(opaque[:, x])[0]
        if len(col) < 6:
            continue
        top, bot = col[0], col[-1]
        for y in (top + 1, top + 2):
            if idx[y, x] == 4:
                idx[y, x] = 5
        for y in (bot - 1, bot - 2):
            if idx[y, x] == 4:
                idx[y, x] = 3
    # uniform outline on every edge pixel
    for y in range(h):
        for x in range(w):
            if not opaque[y, x] or idx[y, x] == PINK_IDX:
                continue
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if not (0 <= ny < h and 0 <= nx < w) or not opaque[ny, nx]:
                    idx[y, x] = 0
                    break
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            v = idx[y, x]
            if v < 0:
                continue
            out[y, x] = a[y, x] if v == PINK_IDX else R_PAL[v]
    return Image.fromarray(out, 'RGBA')


# eye search boxes per row (cell coordinates); climb is a back view so no eyes
EYE_BOXES = {'walk': (56, 22, 69, 32), 'climb': None, 'drink': (55, 28, 69, 40), 'swipe': None}


# The source art's "eye" was a 1px sliver of outline colour lost inside the dark mask.
# Every face-visible frame gets a hand-designed eye stamped at the detected position.
#   B pupil  W glint  S sclera (cream, behind the pupil so it reads at any size)
EYE_OPEN = ['.BB.', 'SBWB', 'SBBB', '.BB.']
EYE_CLOSED = ['....', '.BB.', 'B..B', '....']   # happy closed lid for the idle blink
EYE_KO = ['S..S', '.SS.', '.SS.', 'S..S']        # X eyes for the knocked-out pose
EYE_PAL = {'B': hexrgb('#0b0705'), 'W': hexrgb('#fffcf4'), 'S': hexrgb('#ece2cc')}


def find_eye(frame, box):
    """Interior outline-coloured pixels inside the eye box = the original eye sliver."""
    a = np.asarray(frame)
    x0, y0, x1, y1 = box
    k = R_PAL[0][:3]
    pts = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if a[y, x, 3] and tuple(a[y, x, :3]) == k:
                if all(a[y + dy, x + dx, 3] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    pts.append((x, y))
    if not pts:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return pts, cx, cy


def stamp_eye(frame, eye, pattern, dx=-1):
    a = np.array(frame)
    pts, cx, cy = eye
    for (x, y) in pts:
        a[y, x] = R_PAL[1]
    h, w = len(pattern), len(pattern[0])
    ox = round(cx - (w - 1) / 2 + 0.3) + dx
    oy = round(cy - (h - 1) / 2)
    for yy, line in enumerate(pattern):
        for xx, ch in enumerate(line):
            if ch in EYE_PAL:
                a[oy + yy, ox + xx] = EYE_PAL[ch]
            elif a[oy + yy, ox + xx, 3] and tuple(a[oy + yy, ox + xx, :3]) == R_PAL[0][:3]:
                a[oy + yy, ox + xx] = R_PAL[1]
    return Image.fromarray(a, 'RGBA')


# The standing (swipe) pose faces the camera three-quarters, so its head needs two eyes.
# The source head was a single dark blob, so it is replaced with a hand-drawn head in the
# same style as the brand mark, sized to cover the old jaw and blend into the shoulders.
HEAD_FRONT = [
    '.......KKKK.......KKKK....',
    '......KLLLLK.....KLLLLK...',
    '......KLDDLLKKKKKLLDDLK...',
    '.....KFLDDHHHHHHHHHDDLFK..',
    '.....KFFLHHHHHHHHHHHLFFK..',
    '....KFFFFHHHHHHDDHHHHFFFK.',
    '....KFFFFFFFFFFDDFFFFFFFK.',
    '...KFFFWWWWWWFFDDFFWWWWFFK',
    '...KFFWWWWWWWWFDDFWWWWWWFK',
    '...KDDDDDDDDDWWDDWWDDDDDDK',
    '..KDDDDDSGEDDDWWWWDSGEDDDK',
    '..KDDDDDSEEDDDWWWWDSEEDDDK',
    '..KDDDDDSEEDDWWWWWDSEEDDDK',
    '..KLDDDDDDDDWWWWWWWDDDDDLK',
    '.KLLLDDDDWWWWWWWWWWWWDDLLK',
    '.KLLLLLWWWWWWWKKKKWWWLLLLK',
    'KLLLLLLWWWWWWWWKKWWWWLLLK.',
    'FLLLLLWWWWWWWWKWWKWWWLLK..',
    'FFLLLLLWWWWWWWWKKWWWLLK...',
    'FFFLLLLLWWWWWWWWWWLLLK....',
    'FFFFLLLLLLWWWWWWLLLKK.....',
    'FFFFFSLLLLLLLLLLKKK.......',
]
HEAD_POS = (27, 8)
HEAD_PAL = {'K': '#1a120c', 'D': '#402d20', 'S': '#62502f', 'F': '#76643c', 'H': '#8d7a50',
            'L': '#b29c72', 'W': '#ece2cc', 'E': '#0b0705', 'G': '#fffcf4'}
ARC_LIGHT, ARC_MID = hexrgb('#f6efe0'), hexrgb('#d9ccae')


def replace_head(frame):
    hx, hy = HEAD_POS
    head = art(HEAD_FRONT, {k: hexrgb(v) for k, v in HEAD_PAL.items()})
    a = np.array(frame)
    bottom = hy + head.height
    a[2:hy + 16, hx - 1:60] = 0          # old head
    a[hy + 16:bottom, hx + 1:60] = 0     # old jaw (keeps the back outline on the left)
    im = Image.fromarray(a, 'RGBA')
    im.alpha_composite(head, (hx, hy))
    a = np.array(im)
    op = a[..., 3] > 0
    for y in range(hy - 1, bottom + 2):   # re-seal the silhouette where head meets body
        for x in range(hx - 3, hx + head.width + 1):
            if op[y, x] and not all(op[y + dy, x + dx] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                a[y, x] = R_PAL[0]
    return Image.fromarray(a, 'RGBA')


def lighten_arcs(frame):
    """Swipe motion arcs are separate specks of pixels: paint them as light streaks, no outline."""
    a = np.array(frame)
    op = a[..., 3] > 0
    h, w = op.shape
    seen = np.zeros_like(op)
    comps = []
    for y in range(h):
        for x in range(w):
            if op[y, x] and not seen[y, x]:
                stack, comp = [(y, x)], []
                seen[y, x] = True
                while stack:
                    cy, cx = stack.pop()
                    comp.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and op[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                stack.append((ny, nx))
                comps.append(comp)
    comps.sort(key=len, reverse=True)
    for comp in comps[1:]:
        ys = [p[0] for p in comp]
        mid = (min(ys) + max(ys)) / 2
        for (y, x) in comp:
            a[y, x] = ARC_LIGHT if y >= mid else ARC_MID
    return Image.fromarray(a, 'RGBA')


FACE_LIGHT_BOXES = {'walk': (50, 22, 75, 35), 'drink': (50, 30, 73, 44)}


def recolor_box(frame, box, src, dst):
    a = np.array(frame)
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    m = (sub[..., :3] == src[:3]).all(-1) & (sub[..., 3] > 0)
    sub[m] = dst
    return Image.fromarray(a, 'RGBA')


def build_raccoon():
    frames, pinks = load_raccoon_frames()
    sheet = grid(frames, 6, RC_W, RC_H)
    q = quantize(sheet, 18)
    frames = split(q, 6, RC_W, RC_H, 24)
    # restore tongue colour that palette reduction merged away
    for f, pm in zip(frames, pinks):
        a = np.asarray(f).copy()
        if pm.any():
            ys, xs = np.where(pm)
            for y, x in zip(ys, xs):
                a[y, x] = PINK if (y == ys.min()) else PINK_DARK if y == ys.max() else PINK
            f.paste(Image.fromarray(a, 'RGBA'))
    frames = [clean_frame(f) for f in frames]
    # profile faces: brows, cheek ring and muzzle in cream to match the front-facing head
    for i, f in enumerate(frames):
        box = FACE_LIGHT_BOXES.get(ROWS[i // 6])
        if box:
            frames[i] = recolor_box(f, box, R_PAL[6], hexrgb(HEAD_PAL['W']))
    eyes = []
    last = {}
    for i, f in enumerate(frames):
        row = ROWS[i // 6]
        box = EYE_BOXES[row]
        if box is None:
            eyes.append(None)
            continue
        e = find_eye(f, box) or last.get(row)
        if e is None:
            raise SystemExit(f'no eye found in frame {i} ({row})')
        last[row] = e
        eyes.append(e)
    base_walk0 = frames[0]
    frames = [stamp_eye(f, e, EYE_OPEN) if e else f for f, e in zip(frames, eyes)]
    frames = [lighten_arcs(replace_head(f)) if ROWS[i // 6] == 'swipe' else f for i, f in enumerate(frames)]
    # extra row: idle blink, knocked-out (flat on its back, feet up, X eyes)
    extra = [stamp_eye(base_walk0, eyes[0], EYE_CLOSED),
             stamp_eye(base_walk0, eyes[0], EYE_KO).transpose(Image.FLIP_TOP_BOTTOM)]
    extra += [Image.new('RGBA', (RC_W, RC_H), (0, 0, 0, 0))] * (6 - len(extra))
    hats = {'side': art(HAT_SIDE, HAT_PAL), 'back': art(HAT_BACK, HAT_PAL)}
    santa, meta = [], []
    for i, f in enumerate(frames):
        row = ROWS[i // 6]
        x0, x1, dx, dy, kind = HAT_RULES[row]
        cx, top = head_anchor(f, x0, x1)
        hat = hats[kind]
        hx = int(round(cx - hat.width / 2 + dx))
        hy = int(top - hat.height + dy + 9)
        s = f.copy()
        s.alpha_composite(hat, (max(0, hx), max(0, hy)))
        santa.append(s)
        meta.append({'row': row, 'headX': cx, 'headTop': top, 'feet': feet_y(f)})
    hat0 = santa[0].copy()
    hat_only = Image.fromarray(np.where((np.asarray(hat0) != np.asarray(frames[0])).any(-1, keepdims=True), np.asarray(hat0), 0).astype(np.uint8), 'RGBA')
    santa_blink = extra[0].copy(); santa_blink.alpha_composite(hat_only)
    santa_ko = extra[1].transpose(Image.FLIP_TOP_BOTTOM).copy(); santa_ko.alpha_composite(hat_only)
    santa_extra = [santa_blink, santa_ko.transpose(Image.FLIP_TOP_BOTTOM)] + extra[2:]
    out = grid(frames + extra + santa + santa_extra, 6, RC_W, RC_H)
    out.save(os.path.join(OUT, 'raccoon.png'), optimize=True)
    return out, meta


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


# ---------------------------------------------------------------------------
# Bathroom (game over)
# ---------------------------------------------------------------------------
def build_bathroom():
    im = Image.open(os.path.join(SRC, 'bathroom.png')).convert('RGBA')
    p = repixelize(im, 4)  # 352 x 184
    p = quantize(p, 40)
    # the Santa hat fell off: lying on the tiles next to the raccoon's head
    hat = art(HAT_SIDE, HAT_PAL).rotate(-24, expand=True, resample=Image.NEAREST)
    p.alpha_composite(hat, (118, 126))
    p.save(os.path.join(OUT, 'bathroom.png'), optimize=True)
    return p


def main():
    rac, rmeta = build_raccoon()
    bot, bmeta = build_bottles()
    bath = build_bathroom()
    data = {
        'raccoon': {'w': RC_W, 'h': RC_H, 'cols': 6, 'rows': SHEET_ROWS, 'santaRowOffset': 5, 'frames': rmeta},
        'bottles': {'w': BT_W, 'h': BT_H, 'kinds': BOTTLE_KINDS + ['reserve'], 'frames': FRAME_NAMES,
                    'spinStart': 6, 'spinCount': 8, 'cols': bmeta['cols'], 'upBox': bmeta['upBox']},
        'bathroom': {'w': bath.width, 'h': bath.height},
    }
    js = '// Generated by tools/build_sprites.py. Do not edit by hand.\nexport const SPRITES = ' + json.dumps(data, indent=1) + ';\n'
    with open(os.path.join(ROOT, 'js', 'game', 'sprite-data.js'), 'w') as fh:
        fh.write(js)
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        for name, im, k in (('raccoon', rac, 3), ('bottles', bot, 4), ('bathroom', bath, 2)):
            bg = Image.new('RGBA', im.size, (88, 96, 96, 255))
            bg.alpha_composite(im)
            upscale(bg, k).save(os.path.join(PREVIEW, f'sprite_{name}.png'))
    print('sprites ok', rac.size, bot.size, bath.size)


if __name__ == '__main__':
    main()
