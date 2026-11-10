"""Pixel-art product mockups (160x160), built from the real production artwork.

Designs are placed at 1:1 so a mockup never shows anything the print file doesn't
contain, and print proportions stay close to reality (a 12 in print on a ~20 in chest).
"""
import numpy as np
from PIL import Image, ImageDraw

from merchkit import (S, PAL, ramp, hexrgb, poly_mask, ellipse_mask, rect_mask, shaded, ink_outline,
                      clip, paste, paint_line, centered, tiled, upscale)
import merch_designs as D


def new():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))


def mirror(pts):
    return [(S - x, y) for x, y in pts]


def tint_columns(im, mask, k=0.92, step=2):
    a = np.array(im)
    cols = np.zeros_like(mask)
    cols[:, ::step] = True
    t = mask & cols
    a[t, :3] = (a[t, :3].astype(int) * k).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def rib(pts, rp):
    rm = poly_mask(pts)
    r = shaded(rm, [rp[2], rp[2], rp[3], rp[3]], shadow_w=1)
    a = np.array(r)
    cols = np.zeros_like(rm)
    cols[:, ::2] = True
    a[rm & cols] = rp[3]
    return Image.fromarray(a, 'RGBA')


# ---------------------------------------------------------------------------
# Tee
# ---------------------------------------------------------------------------
TEE = [(62, 26), (34, 32), (9, 55), (20, 76), (36, 67), (36, 151), (124, 151), (124, 67), (140, 76), (151, 55), (126, 32), (98, 26), (92, 34), (80, 38), (68, 34)]


def mock_tee(color, design):
    rp = ramp(color)
    mask = poly_mask(TEE)
    im = shaded(mask, rp)
    neck = poly_mask([(62, 26), (68, 34), (80, 38), (92, 34), (98, 26), (92, 30), (80, 33), (68, 30)])
    im.alpha_composite(shaded(neck, [rp[3]] * 4))
    paint_line(im, [(64, 27), (69, 33), (80, 37), (91, 33), (96, 27)], rp[0])
    paint_line(im, [(13, 62), (22, 72)], rp[2])
    paint_line(im, [(147, 62), (138, 72)], rp[2])
    for x in range(38, 123, 2):
        im.putpixel((x, 146), rp[2])
    paint_line(im, [(40, 76), (44, 116)], rp[2])
    paint_line(im, [(120, 76), (116, 118)], rp[2])
    paste(im, design, centered(design, 80, 50), mask)
    return ink_outline(im)


# ---------------------------------------------------------------------------
# Knitted sweater (front + back) straight from the knit charts
# ---------------------------------------------------------------------------
SW_BODY_FRONT = [(46, 30), (62, 26), (68, 32), (80, 34), (92, 32), (98, 26), (114, 30), (114, 118), (46, 118)]
SW_BODY_BACK = [(46, 30), (62, 26), (80, 28), (98, 26), (114, 30), (114, 118), (46, 118)]
SW_SLEEVE = [(47, 30), (30, 38), (15, 120), (30, 124), (45, 58)]


def _yarn_ramp(hex_base):
    base = hexrgb(hex_base)
    hi = tuple(min(255, int(c * 1.15)) for c in base[:3]) + (255,)
    sh = tuple(int(c * 0.78) for c in base[:3]) + (255,)
    dp = tuple(int(c * 0.6) for c in base[:3]) + (255,)
    return [hi, base, sh, dp]


def mock_sweater(cw, side='front'):
    y = D.YARN[cw]
    rp = _yarn_ramp(y['base'])
    dark = _yarn_ramp(y['dark'])
    chart = D.knit_front(cw) if side == 'front' else D.knit_back(cw)
    sleeve_chart = D.knit_sleeve(cw)
    body = poly_mask(SW_BODY_FRONT if side == 'front' else SW_BODY_BACK)
    ls, rs = poly_mask(SW_SLEEVE), poly_mask(mirror(SW_SLEEVE))
    im = new()
    for m, x0 in ((ls, 15), (rs, 115)):
        layer = shaded(m, rp)
        paste(layer, sleeve_chart, (x0, 36), m)
        im.alpha_composite(layer)
    layer = shaded(body, rp)
    paste(layer, chart, (46, 30), body)
    im.alpha_composite(layer)
    im = tint_columns(im, body | ls | rs)
    im.alpha_composite(rib([(46, 116), (114, 116), (114, 124), (46, 124)], dark))
    im.alpha_composite(rib([(15, 114), (30, 118), (30, 124), (15, 120)], dark))
    im.alpha_composite(rib([(145, 114), (130, 118), (130, 124), (145, 120)], dark))
    if side == 'front':
        im.alpha_composite(rib([(62, 26), (68, 32), (80, 34), (92, 32), (98, 26), (93, 27), (80, 30), (67, 27)], dark))
    else:
        im.alpha_composite(rib([(62, 26), (80, 28), (98, 26), (98, 29), (80, 31), (62, 29)], dark))
    return ink_outline(im)


# ---------------------------------------------------------------------------
# Hoodie (front + back)
# ---------------------------------------------------------------------------
HD_SLEEVE = [(37, 36), (20, 44), (8, 136), (24, 140), (36, 66)]
HD_BODY = [(36, 36), (60, 30), (100, 30), (124, 36), (126, 157), (34, 157)]


def mock_hoodie(color, design, side='front'):
    rp = ramp(color)
    im = new()
    if side == 'front':
        hood = poly_mask([(54, 40), (56, 16), (68, 6), (92, 6), (104, 16), (106, 40)])
        im.alpha_composite(shaded(hood, [rp[1], rp[2], rp[3], rp[3]]))
    ls, rs, body = poly_mask(HD_SLEEVE), poly_mask(mirror(HD_SLEEVE)), poly_mask(HD_BODY)
    for m in (ls, rs, body):
        im.alpha_composite(shaded(m, rp))
    if side == 'front':
        opening = poly_mask([(62, 30), (68, 18), (80, 14), (92, 18), (98, 30), (88, 38), (72, 38)])
        im.alpha_composite(shaded(opening, [rp[3]] * 4))
        for x0, x1 in ((72, 71), (88, 89)):
            paint_line(im, [(x0, 38), (x1, 62)], PAL['cream_sh'])
            for yy in (63, 64):
                im.putpixel((x1, yy), PAL['gold_sh'])
        pk = [(54, 114), (106, 114), (112, 138), (48, 138)]
        paint_line(im, pk + [pk[0]], rp[2])
        paint_line(im, [(55, 115), (105, 115)], rp[0])
        paste(im, design, centered(design, 80, 44), body)
    else:
        hood = poly_mask([(56, 36), (58, 14), (68, 5), (92, 5), (102, 14), (104, 36), (94, 41), (66, 41)])
        hl = shaded(hood, rp)
        paint_line(hl, [(80, 7), (80, 39)], rp[2])
        paste(im, design, centered(design, 80, 43), body)
        im.alpha_composite(ink_outline(hl))
    for pts in ([(34, 147), (126, 147), (126, 157), (34, 157)], [(8, 130), (24, 134), (24, 140), (8, 136)], [(152, 130), (136, 134), (136, 140), (152, 136)]):
        im.alpha_composite(rib(pts, rp))
    return ink_outline(im)


# ---------------------------------------------------------------------------
# Ornament: a flat porcelain disc on a gold cord (front or back)
# ---------------------------------------------------------------------------
def mock_ornament(art):
    im = new()
    cx, cy, r = 80, 92, 45
    disc = ellipse_mask((cx - r, cy - r, cx + r, cy + r))
    face = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    face.alpha_composite(art, (cx - r, cy - r))
    face = clip(face, disc)
    a = np.array(face)
    ys, xs = np.mgrid[0:S, 0:S]
    d = np.hypot(xs - cx, ys - cy)
    edge = disc & (d > r - 1.5)
    a[edge, :3] = (a[edge, :3].astype(int) * 0.7).astype(np.uint8)
    gloss = disc & (np.hypot(xs - (cx - 18), ys - (cy - 20)) < 22) & (np.hypot(xs - (cx - 12), ys - (cy - 14)) > 20)
    a[gloss, :3] = np.clip(a[gloss, :3].astype(int) + 60, 0, 255).astype(np.uint8)
    im.alpha_composite(ink_outline(Image.fromarray(a, 'RGBA')))
    cord = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(cord)
    dr.line((78, cy - r + 4, 72, 22, 80, 10, 88, 22, 82, cy - r + 4), fill=PAL['gold'], width=2)
    im.alpha_composite(cord)
    hole = ellipse_mask((77, cy - r + 3, 83, cy - r + 9))
    a = np.array(im)
    a[hole] = hexrgb('#2a1b11')
    return Image.fromarray(a, 'RGBA')


# ---------------------------------------------------------------------------
# Beanie with embroidered face
# ---------------------------------------------------------------------------
def mock_beanie(color):
    rp = ramp(color)
    im = new()
    pom = ellipse_mask((62, 6, 98, 40))
    pa = np.array(shaded(pom, ramp('cream')))
    rng = np.random.default_rng(4)
    for _ in range(90):
        x, y = rng.integers(62, 98), rng.integers(6, 40)
        if pom[y, x]:
            pa[y, x] = ramp('cream')[2]
    im.alpha_composite(ink_outline(Image.fromarray(pa, 'RGBA')))
    dome = ellipse_mask((24, 30, 136, 140)) & (np.arange(S)[:, None] < 90)
    dl = shaded(dome, rp)
    dl = tint_columns(dl, dome, 0.86, 3)
    im.alpha_composite(ink_outline(dl))
    cuff = [(21, 84), (139, 84), (139, 124), (21, 124)]
    im.alpha_composite(ink_outline(rib(cuff, [rp[0], rp[1], rp[1], rp[2]])))
    emb = D.beanie_embroidery()
    ea = np.array(emb)
    ea[1::2, :, :3] = (ea[1::2, :, :3].astype(int) * 0.9).astype(np.uint8)   # satin-stitch rows
    im.alpha_composite(Image.fromarray(ea, 'RGBA'), centered(emb, 80, 93))
    return im


# ---------------------------------------------------------------------------
# Mug (one side per view)
# ---------------------------------------------------------------------------
def mock_mug(side_art):
    im = new()
    white = [hexrgb('#ffffff'), hexrgb('#f1ece2'), hexrgb('#d9d1c2'), hexrgb('#bdb3a2')]
    handle = ellipse_mask((110, 58, 148, 122)) & ~ellipse_mask((119, 69, 139, 111))
    im.alpha_composite(ink_outline(shaded(handle, white, shadow_w=2)))
    body = rect_mask((22, 40, 120, 138)) | ellipse_mask((22, 128, 119, 148))
    bl = shaded(body, white, shadow_w=5)
    paste(bl, side_art, centered(side_art, 71, 94 - side_art.height // 2), body)
    im.alpha_composite(ink_outline(bl))
    rim = ellipse_mask((22, 32, 119, 48))
    im.alpha_composite(ink_outline(shaded(rim, white, shadow_w=1)))
    inside = ellipse_mask((26, 34, 115, 46))
    im.alpha_composite(shaded(inside, [hexrgb('#6b4a32'), hexrgb('#4a2f1d'), hexrgb('#3a2414'), hexrgb('#2a190d')], shadow_w=1))
    for y in range(56, 70, 2):
        im.putpixel((28, y), hexrgb('#ffffff'))
    return im


# ---------------------------------------------------------------------------
# Socks: all-over tile, tail-ring cuffs, face on the leg
# ---------------------------------------------------------------------------
SOCK = [(28, 10), (62, 10), (62, 90), (98, 105), (104, 119), (99, 132), (85, 139), (42, 139), (30, 129), (28, 112)]


def sock_layer(dx, dy, darker=False):
    pts = [(x + dx, y + dy) for x, y in SOCK]
    m = poly_mask(pts)
    pattern = tiled(D.sock_tile(), S, S, dx + 28, dy + 18)
    layer = clip(pattern, m)
    a = np.array(layer)
    sh = shaded(m, [(0, 0, 0, 0)] * 4)
    # shade right edge
    ys, xs = np.nonzero(m)
    edge = m & ~np.roll(m, -3, axis=1)
    a[edge, :3] = (a[edge, :3].astype(int) * 0.82).astype(np.uint8)
    if darker:
        a[m, :3] = (a[m, :3].astype(int) * 0.9).astype(np.uint8)
    layer = Image.fromarray(a, 'RGBA')
    heel = m & ellipse_mask((20 + dx, 110 + dy, 56 + dx, 146 + dy))
    toe = m & ellipse_mask((78 + dx, 104 + dy, 112 + dx, 146 + dy))
    a = np.array(layer)
    a[heel | toe] = PAL['red']
    layer = Image.fromarray(a, 'RGBA')
    cuff = rib([(28 + dx, 10 + dy), (62 + dx, 10 + dy), (62 + dx, 19 + dy), (28 + dx, 19 + dy)], ramp('cream'))
    layer.alpha_composite(cuff)
    return ink_outline(layer), m


def mock_socks():
    im = new()
    back, _ = sock_layer(36, 8, darker=True)
    im.alpha_composite(back)
    front, m = sock_layer(4, 4)
    face_bg = rect_mask((35, 38, 59, 66)) & m
    a = np.array(front)
    a[face_bg] = PAL['cream']
    front = Image.fromarray(a, 'RGBA')
    front.alpha_composite(D.FACE_SMALL, (38, 41))
    im.alpha_composite(front)
    return im


# ---------------------------------------------------------------------------
# Stickers, gift wrap, cards
# ---------------------------------------------------------------------------
def mock_sticker(art):
    k = max(1, 156 // (max(art.width, art.height) + 4))      # art plus its white border must fit the tile
    big = upscale(art, k)
    border = 2 * k
    w, h = big.width + border * 2, big.height + border * 2
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    base.alpha_composite(big, (border, border))
    m = np.asarray(base)[..., 3] > 0
    grown = m.copy()
    for _ in range(border):
        g = grown.copy()
        g[1:, :] |= grown[:-1, :]
        g[:-1, :] |= grown[1:, :]
        g[:, 1:] |= grown[:, :-1]
        g[:, :-1] |= grown[:, 1:]
        grown = g
    out = np.zeros((h + 3, w + 3, 4), np.uint8)
    out[3:, 3:][grown] = (0, 0, 0, 80)
    out[:h, :w][grown] = hexrgb('#ffffff')
    st = Image.fromarray(out, 'RGBA')
    st.alpha_composite(big, (border, border))
    im = new()
    im.alpha_composite(st, ((S - st.width) // 2, (S - st.height) // 2))
    return im


def mock_wrap():
    im = new()
    tile = D.wrap_tile()
    sheet = rect_mask((12, 8, 148, 120))
    im.alpha_composite(ink_outline(clip(tiled(tile, S, S, 12, 8), sheet)))
    roll = rect_mask((10, 116, 146, 148))
    ra = np.array(clip(tiled(tile, S, S, 6, 4), roll))
    top = roll & (np.arange(S)[:, None] < 120)
    bot = roll & (np.arange(S)[:, None] >= 140)
    ra[top, :3] = np.clip(ra[top, :3].astype(int) + 40, 0, 255).astype(np.uint8)
    ra[bot, :3] = (ra[bot, :3].astype(int) * 0.6).astype(np.uint8)
    im.alpha_composite(ink_outline(Image.fromarray(ra, 'RGBA')))
    cap = ellipse_mask((140, 116, 154, 148))
    im.alpha_composite(ink_outline(shaded(cap, ramp('cream'), shadow_w=1)))
    for (x, y) in ((146, 128), (147, 130), (148, 132), (147, 134), (145, 135), (144, 133)):
        im.putpixel((x, y), PAL['cream_sh'])
    return im


def mock_card(panel, envelope=True):
    im = new()
    if envelope:
        env = rect_mask((72, 50, 152, 140))
        el = shaded(env, [PAL['red_hi'], PAL['red'], PAL['red_sh'], hexrgb('#64161d')], shadow_w=2)
        paint_line(el, [(73, 51), (112, 86), (151, 51)], PAL['red_sh'])
        im.alpha_composite(ink_outline(el))
    x0, y0 = 14, 26
    card = rect_mask((x0, y0, x0 + panel.width, y0 + panel.height))
    cl = shaded(card, [hexrgb('#fffaf0'), PAL['cream'], PAL['cream_sh'], hexrgb('#bfae8e')], shadow_w=2)
    paste(cl, panel, (x0, y0), card)
    im.alpha_composite(ink_outline(cl))
    return im
