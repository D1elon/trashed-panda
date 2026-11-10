#!/usr/bin/env python3
"""Build the holiday merch: shop mockups and the production package.

    python3 tools/build_merch.py

Outputs
    assets/shop/*.png             160x160 pixel mockups + flat print previews for the shop
    merch/<nn>-<product>/print/   print-ready files (integer-scaled, 300 dpi unless noted)
    merch/<nn>-<product>/mockups/ mockups at 3x for listings and approvals
    merch/<nn>-<product>/spec.md  production spec sheet (blank, technique, placement, colours)
    merch/README.md               ordering guide + pre-flight check results
    merch/line-sheet.pdf          printable line sheet

The build fails if any pre-flight check fails (yarn/thread colour limits, ornament safe
area, file sizes), so nothing un-producible can be shipped by accident.
"""
import os
import shutil
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import merch_designs as D
import merch_mockups as M
from merchkit import ROOT, SHOP, S, PAL, hexrgb, upscale, colours, tiled, flatten

MERCH = os.path.join(ROOT, 'merch')
PREVIEW = os.environ.get('PREVIEW_DIR')
DPI = 300

checks = []   # (label, ok, detail)


def check(label, ok, detail=''):
    checks.append((label, bool(ok), detail))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def fit_scale(img, box_w, box_h):
    return max(1, min(box_w // img.width, box_h // img.height))


def canvas_with(img, w, h, k, bg=(0, 0, 0, 0), align='top', y_off=0):
    big = upscale(img, k)
    c = Image.new('RGBA', (w, h), bg)
    y = y_off if align == 'top' else (h - big.height) // 2
    c.alpha_composite(big, ((w - big.width) // 2, y))
    return c


def knockout_dark(img, threshold=45):
    """For black garments: drop near-black pixels so the shirt shows through (no wasted ink)."""
    a = np.array(img)
    lum = 0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
    m = (a[..., 3] > 0) & (lum < threshold)
    a[m] = 0
    return Image.fromarray(a, 'RGBA'), int(m.sum())


def save(img, path, dpi=DPI):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True, dpi=(dpi, dpi))
    return img.size


def shop(img, name):
    save(img, os.path.join(SHOP, name), dpi=72)


def inches(px, dpi=DPI):
    return f'{px / dpi:.2f}'.rstrip('0').rstrip('.')


# ---------------------------------------------------------------------------
# products: each builder writes its files and returns a spec dict
# ---------------------------------------------------------------------------
def p_sweater(out):
    files, mocks = [], {}
    for cw in ('red', 'green'):
        y = D.YARN[cw]
        front, back, sleeve, tile = D.knit_front(cw), D.knit_back(cw), D.knit_sleeve(cw), D.knit_tile(cw)
        for part, img in (('front', front), ('back', back), ('sleeve', sleeve)):
            n = len(colours(img))
            check(f'Sweater {cw} {part}: yarn colours', n <= 4, f'{n} of 4 allowed')
            base, accent = hexrgb(y['base'])[:3], hexrgb(y['accent'])[:3]
            a = np.asarray(img)[..., :3]
            is_b = (a == base).all(-1)
            is_a = (a == accent).all(-1)
            touch = int((is_a[:, 1:] & is_b[:, :-1]).sum() + (is_a[:, :-1] & is_b[:, 1:]).sum()
                        + (is_a[1:, :] & is_b[:-1, :]).sum() + (is_a[:-1, :] & is_b[1:, :]).sum())
            check(f'Sweater {cw} {part}: fur grey never touches base', touch == 0, f'{touch} contacts (mid grey on {cw} blurs at stitch level)')
            files.append((f'{part}-{cw}-chart-1x.png', save(img, f'{out}/print/{part}-{cw}-chart-1x.png'), f'Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode.'))
            files.append((f'{part}-{cw}-20x.png', save(upscale(img, 20), f'{out}/print/{part}-{cw}-20x.png'), 'Same chart enlarged for viewing and for templates that want large files.'))
        files.append((f'all-over-tile-{cw}.png', save(upscale(tile, 20), f'{out}/print/all-over-tile-{cw}.png'), 'Seamless fill for any extra panels (collar, pocket, hood).'))
        for side in ('front', 'back'):
            mk = M.mock_sweater(cw, side)
            shop(mk, f'sweater-{cw}-{side}.png')
            mocks[f'{cw}-{side}'] = mk
        shop(front, f'print-sweater-{cw}.png')
    yarn_rows = [f"| {cw.title()} | " + ' | '.join(f"`{D.YARN[cw][k]}`" for k in ('base', 'cream', 'dark', 'accent')) + ' |' for cw in ('red', 'green')]
    return {
        'name': 'The Ugly Trash Panda Sweater', 'shop_id': 'ugly-sweater',
        'concept': 'One big face: the game\'s own raccoon head knitted at two stitches per pixel across the chest, in real raccoon colours (charcoal mask, grey fur, cream brows and muzzle), wearing a Santa hat in the sweater\'s own colour. A ringed-tail band runs across the yoke, TRASHED PANDA sits on the back, and both sleeves are ringed charcoal and grey exactly like the tail.',
        'blank': 'Printful knitwear: Unisex Classic Fit Knitted Crew Neck Sweater', 'technique': 'Jacquard knitting (knitwear)',
        'variants': 'Colourways: Red, Green. Sizes: S-3XL.',
        'files': files, 'mockups': mocks,
        'art': [('Front chart', D.knit_front('red'), None), ('Back chart', D.knit_back('red'), None), ('Sleeve', D.knit_sleeve('red'), None), ('Front, green', D.knit_front('green'), None)],
        'placements': [('Front', 'front-<colour>-chart-1x.png', 'full front panel'), ('Back', 'back-<colour>-chart-1x.png', 'full back panel'), ('Sleeves', 'sleeve-<colour>-chart-1x.png', 'both sleeves')],
        'extra': ['### Yarn colours (4 per colourway)', '', '| Colourway | Base | Cream | Charcoal | Fur grey |', '| --- | --- | --- | --- | --- |', *yarn_rows, '',
                  'Pick the nearest of Printful\'s yarn colours to each hex. Base, collar and hem must be among the 4; the charts already use charcoal for the hem band and cuffs, so collar/cuffs/hem can all be charcoal.'],
        'notes': ['Upload each chart in the knitwear Design Maker with **Pixelated** rendering, so every cell becomes one block of stitches.',
                  'Charts are drawn so the fur grey never sits directly next to the base colour (a mid grey blurs into red or green at stitch level): it is always fenced in by charcoal. The build checks this.',
                  'If the template\'s panel is larger than the chart, scale the chart up evenly and fill the remaining area with the base colour or the all-over tile.'],
    }


def p_tee(out):
    light, dark = D.design_mugshot(False), D.design_mugshot(True)
    W, H = 12 * DPI, 16 * DPI
    k = fit_scale(light, int(11 * DPI), H)
    files = []
    ko, removed = knockout_dark(light)
    check('Tee black-garment file: near-black ink knocked out', removed > 0, f'{removed} px removed before scaling')
    files.append(('front-black-garment.png', save(canvas_with(ko, W, H, k), f'{out}/print/front-black-garment.png'), f'Black tees. Near-black outline knocked out. Art {inches(light.width * k)} in wide, top of print area.'))
    files.append(('front-forest-garment.png', save(canvas_with(light, W, H, k), f'{out}/print/front-forest-garment.png'), 'Forest tees. Dark outline kept (it shows on green).'))
    files.append(('front-oatmeal-garment.png', save(canvas_with(dark, W, H, k), f'{out}/print/front-oatmeal-garment.png'), 'Heather Oatmeal tees. Dark ink version.'))
    files.append(('artwork-only-light.png', save(upscale(light, k), f'{out}/print/artwork-only-light.png'), 'Trimmed artwork for templates with a different print area.'))
    mocks = {}
    for c, d in (('black', light), ('forest', light), ('oatmeal', dark)):
        mk = M.mock_tee(c, d)
        shop(mk, f'tee-{c}.png')
        mocks[c] = mk
    shop(light, 'print-tee-light.png')
    shop(dark, 'print-tee-dark.png')
    return {
        'name': 'Mugshot Tee', 'shop_id': 'mugshot-tee',
        'concept': 'The booking photo. The raccoon stands against a height chart in its Santa hat, holding a placard that reads ASHLAND VA, NOV 2025. Verdict underneath: GUILTY of poor life choices.',
        'blank': 'Printful: Unisex Staple T-Shirt (Bella + Canvas 3001)', 'technique': 'DTG',
        'variants': 'Black, Forest, Heather Oatmeal. Sizes: S-3XL.', 'files': files, 'mockups': mocks,
        'art': [('Light ink', light, None), ('Dark ink', dark, '#e3d8c1')],
        'placements': [('Front', 'front-<garment>-garment.png', f'12 x 16 in print area, art {inches(light.width * k)} x {inches(light.height * k)} in, top-aligned (about 3 in below collar)')],
        'notes': ['Use the file that matches the garment colour (three files, one per colour).',
                  'The black-garment file has near-black pixels removed so the shirt itself forms the outline: softer print, no wasted ink.'],
    }


def p_ornament(out):
    files, mocks = [], {}
    designs = {'santa-panda': D.ornament_santa_panda(), 'top-shelf': D.ornament_top_shelf(), 'passed-out': D.ornament_passed_out()}
    back = D.ornament_back()
    for name, layers in list(designs.items()) + [('back', back)]:
        n = D.outside_safe(layers)
        check(f'Ornament {name}: artwork inside 2.6 in safe circle', n == 0, f'{n} px outside')
        img = D.compose(layers)
        k = 900 // img.width
        files.append((f'{name}.png', save(upscale(img, k), f'{out}/print/{name}.png'), 'Full-bleed square; background runs past the cut, artwork stays inside the safe circle.'))
        mk = M.mock_ornament(img)
        shop(mk, f'ornament-{name}.png')
        mocks[name] = mk
        if name != 'back':
            shop(img, f'print-ornament-{name}.png')
    return {
        'name': 'Pixel Ornament', 'shop_id': 'pixel-ornament',
        'concept': f'Three full-bleed porcelain discs: the Santa Panda face on snowy pine green, the climb to the top shelf seen from behind on a night sky, and passed out on the bathroom tiles with the hat hooked on one foot. The back of every ornament carries the wordmark and HOLIDAY {D.SEASON}, so each year\'s ornament is a dated keepsake.',
        'blank': 'Printful: Ceramic Ornaments, 2-Side Print (circle, 2.99 in)', 'technique': 'Sublimation on porcelain, both sides',
        'variants': 'Design: Santa Panda, Top Shelf, Passed Out. Back is shared.', 'files': files, 'mockups': mocks,
        'art': [(n.replace('-', ' ').title(), D.compose(l), None) for n, l in list(designs.items()) + [('back', back)]],
        'placements': [('Front', '<design>.png', '900 x 900 px (3 x 3 in) square; cut circle 2.99 in; safe circle 2.6 in'), ('Back', 'back.png', 'same size, same for all three designs')],
        'notes': ['Backgrounds are full bleed on purpose: they extend past the cut line so there is no white edge.',
                  'The build verifies that no character or text pixel falls outside the 2.6 in safe circle.'],
    }


def p_hoodie(out):
    front, back = D.design_wordmark(), D.design_hoodie_back()
    kf = fit_scale(front, int(9 * DPI), 10 * DPI)
    kb = fit_scale(back, int(11 * DPI), 15 * DPI)
    files = [
        ('front.png', save(canvas_with(front, 12 * DPI, 10 * DPI, kf), f'{out}/print/front.png'), f'Chest print, art {inches(front.width * kf)} in wide, top-aligned.'),
        ('back.png', save(canvas_with(back, 12 * DPI, 16 * DPI, kb), f'{out}/print/back.png'), f'Back print, art {inches(back.width * kb)} in wide, top-aligned (about 4 in below collar seam).'),
    ]
    mocks = {}
    for c in ('black', 'heather'):
        for side, d in (('front', front), ('back', back)):
            mk = M.mock_hoodie(c, d, side)
            shop(mk, f'hoodie-{c}-{side}.png')
            mocks[f'{c}-{side}'] = mk
    shop(back, 'print-hoodie-back.png')
    return {
        'name': 'Trashed Panda Hoodie', 'shop_id': 'trashed-panda-hoodie',
        'concept': 'Front: the Santa Panda face over the game wordmark and the hometown. Back: LAST CALL, the raccoon up on the top shelf mid-swipe with one bottle already on its way down.',
        'blank': 'Printful: Unisex Premium Hoodie (Cotton Heritage M2580)', 'technique': 'DTG, front + back',
        'variants': 'Black, Heather (use the blank\'s mid-grey, e.g. Carbon Grey). Sizes: S-3XL.', 'files': files, 'mockups': mocks,
        'art': [('Front', front, None), ('Back', back, None)],
        'placements': [('Front', 'front.png', f'chest, 12 x 10 in area, art {inches(front.width * kf)} in wide'), ('Back', 'back.png', f'12 x 16 in area, art {inches(back.width * kb)} in wide')],
        'notes': ['Both prints read on dark and mid-grey fleece; no knock-out needed because the grey fur, steel shelf and cream text carry the composition.'],
    }


def p_mug(out):
    wrap = D.mug_wrap()
    k = 2700 // wrap.width
    files = [('11oz-wrap.png', save(upscale(wrap, k), f'{out}/print/11oz-wrap.png'), f'{wrap.width * k} x {wrap.height * k} px (9 x 3.5 in). Night side and morning side, one either side of the handle.')]
    mocks = {'morning': M.mock_mug(D.mug_side_morning()), 'night': M.mock_mug(D.mug_side_night())}
    shop(mocks['morning'], 'mug-morning.png')
    shop(mocks['night'], 'mug-night.png')
    return {
        'name': 'Poor Life Choices Mug', 'shop_id': 'poor-life-choices-mug',
        'concept': 'Two sides, two moods: LAST CALL (up on the shelf, mid-swipe, a whiskey bottle flying) and POOR LIFE CHOICES (flat on its back, paws up, hat hooked on a foot). Turn the mug to match your morning.',
        'blank': 'Printful: White Glossy Mug, 11 oz', 'technique': 'Sublimation, full wrap',
        'variants': '11 oz.', 'files': files, 'mockups': mocks,
        'art': [('Full wrap', wrap, '#ffffff')],
        'placements': [('Wrap', '11oz-wrap.png', '9 x 3.5 in; the two scenes sit at the quarter points so they face out on either side of the handle')],
        'notes': ['White background is left transparent (the mug is white).'],
    }


def p_socks(out):
    tile, leg = D.sock_tile(), D.sock_leg()
    files = [
        ('all-over-tile.png', save(upscale(tile, 20), f'{out}/print/all-over-tile.png'), 'Seamless repeat for the full sock template (pattern fill).'),
        ('leg-motif.png', save(upscale(leg, 25), f'{out}/print/leg-motif.png'), 'Optional: placed on the outer leg below the cuff.'),
    ]
    mk = M.mock_socks()
    shop(mk, 'socks.png')
    shop(tiled(tile, 84, 96), 'print-socks.png')
    return {
        'name': 'Tail Stripe Socks', 'shop_id': 'tail-stripe-socks',
        'concept': 'Ringed in the tail\'s own charcoal and pale grey, scattered with red snowflakes and tiny green bottles, with the Santa Panda on the ankle.',
        'blank': 'Printful: Sublimation Socks (crew)', 'technique': 'Sublimation, all-over',
        'variants': 'S/M, L/XL (per blank).', 'files': files, 'mockups': {'pair': mk},
        'art': [('Repeat tile', tile, None), ('Tile, repeated', tiled(tile, 84, 64), None), ('Leg motif', leg, None)],
        'placements': [('All over', 'all-over-tile.png', 'use as pattern fill across the whole template'), ('Leg', 'leg-motif.png', 'outer leg, below cuff')],
        'notes': ['Sock templates differ between models; the tile is seamless so it fits any of them.'],
    }


def p_beanie(out):
    emb = D.beanie_embroidery()
    n = len(colours(emb))
    check('Beanie embroidery: thread colours', n <= 6, f'{n} of 6 allowed')
    k = 16
    px_mm = (k / DPI) * 25.4
    check('Beanie embroidery: smallest detail above 1.27 mm', px_mm >= 1.27, f'1 pixel = {px_mm:.2f} mm')
    files = [('embroidery.png', save(upscale(emb, k), f'{out}/print/embroidery.png'), f'{inches(emb.width * k)} x {inches(emb.height * k)} in, transparent background.')]
    mocks = {}
    for c in ('black', 'red'):
        mk = M.mock_beanie(c)
        shop(mk, f'beanie-{c}.png')
        mocks[c] = mk
    shop(emb, 'print-beanie.png')
    threads = ', '.join(f'{k} `{v}`' for k, v in D.THREADS.items())
    return {
        'name': 'Santa Panda Beanie', 'shop_id': 'santa-panda-beanie',
        'concept': 'The Santa Panda face embroidered on the cuff: the game\'s own head, reduced to five thread colours so the mask, brows and grey fur all stay crisp in thread.',
        'blank': 'Printful: Pom-Pom Knit Cap (or Cuffed Beanie)', 'technique': 'Embroidery, front cuff',
        'variants': 'Black, Red. One size.', 'files': files, 'mockups': mocks,
        'art': [('Embroidery, 5 threads', emb, None)],
        'placements': [('Front cuff', 'embroidery.png', f'{inches(emb.width * k)} x {inches(emb.height * k)} in, centred (max area about 5 x 1.75 in)')],
        'extra': ['### Threads (5 of 6 allowed)', '', threads, '', 'Map to the nearest of Printful\'s standard thread colours: black, white, light grey, dark grey, red.'],
        'notes': ['The face is the game sprite mapped onto thread: the mask, eyes and outline share black, and the white brows and muzzle define it. One pixel is one 1.35 mm stitch block, above the 1.27 mm minimum.',
                  'On the red beanie the red hat blends into the fabric; the black outline keeps its shape.'],
    }


def p_wrap(out):
    tile = D.wrap_tile()
    sheet = tiled(tile, 250, 375)            # x12 = 3000 x 4500 = 20 x 30 in at 150 dpi
    files = [
        ('seamless-tile-150dpi.png', save(upscale(tile, 12), f'{out}/print/seamless-tile-150dpi.png', dpi=150), f'Repeat tile, {tile.width * 12 / 150:.2f} x {tile.height * 12 / 150:.2f} in at 150 dpi.'),
        ('sheet-20x30in-150dpi.png', save(upscale(sheet, 12), f'{out}/print/sheet-20x30in-150dpi.png', dpi=150), 'Full sheet, ready to upload as-is.'),
    ]
    mk = M.mock_wrap()
    shop(mk, 'wrap.png')
    shop(tiled(tile, 120, 128), 'print-wrap.png')
    return {
        'name': 'Evidence Gift Wrap', 'shop_id': 'gift-wrap',
        'concept': 'Santa Panda faces, gold bottles and snowflakes on deep pine green, in a seamless brick repeat so every fold lines up.',
        'blank': 'Printful: Gift Wrap Papers (or Printify Wrapping Papers)', 'technique': 'Digital print on paper',
        'variants': 'Set of 3 sheets.', 'files': files, 'mockups': {'sheet': mk},
        'art': [('Repeat tile', tile, None), ('Tile, repeated', tiled(tile, 120, 128), None)],
        'placements': [('All over', 'sheet-20x30in-150dpi.png', '20 x 30 in at 150 dpi (large-format recommended resolution)')],
        'notes': ['For other sheet sizes, tile `seamless-tile-150dpi.png` edge to edge; it repeats perfectly.'],
    }


def p_cards(out):
    front, back = D.card_front(), D.card_back()
    k = 20                                  # 75x105 -> 1500x2100 = 5x7 in
    bleed = -(-DPI // 8)                   # 0.125 in, rounded up (38 px) so the bleed is never short
    W, H = 2 * front.width * k + 2 * bleed, front.height * k + 2 * bleed
    spread = Image.new('RGBA', (W, H), PAL['cream'])
    spread.alpha_composite(upscale(back, k), (bleed, bleed))
    spread.alpha_composite(upscale(front, k), (bleed + front.width * k, bleed))
    files = [
        ('outside-spread-with-bleed.png', save(spread, f'{out}/print/outside-spread-with-bleed.png'), f'{W} x {H} px: 10 x 7 in flat (back on the left, front on the right) + 0.125 in bleed.'),
        ('front-5x7.png', save(upscale(front, k), f'{out}/print/front-5x7.png'), 'Front panel only (for single-face templates).'),
        ('back-5x7.png', save(upscale(back, k), f'{out}/print/back-5x7.png'), 'Back panel only.'),
    ]
    mocks = {'front': M.mock_card(front), 'back': M.mock_card(back, envelope=False)}
    shop(mocks['front'], 'cards-front.png')
    shop(mocks['back'], 'cards-back.png')
    shop(front, 'print-cards.png')
    return {
        'name': 'Merry Trashmas Cards', 'shop_id': 'trashmas-cards',
        'concept': 'MERRY TRASHMAS: the raccoon with both arms in the air and its Santa hat on, FROM ASHLAND WITH LOVE underneath. The face and the site are on the back. Blank inside for your own confession.',
        'blank': 'Folded greeting card, 5 x 7 in (Printful or Printify greeting cards)', 'technique': 'Digital print',
        'variants': 'Pack of 6 with envelopes.', 'files': files, 'mockups': mocks,
        'art': [('Front', front, None), ('Back', back, None)],
        'placements': [('Outside', 'outside-spread-with-bleed.png', '10 x 7 in flat + 0.125 in bleed; fold down the middle'), ('Inside', '-', 'blank')],
        'notes': ['If your provider\'s card is a different size, use the single-panel files and scale by a whole number.'],
    }


def p_stickers(out):
    files, mocks = [], {}
    for name, art_img in D.sticker_designs().items():
        k = fit_scale(art_img, 1400, 1400)
        c = canvas_with(art_img, 1650, 1650, k, align='center')
        files.append((f'{name}.png', save(c, f'{out}/print/{name}.png'), f'1650 x 1650 px (5.5 in), art {inches(art_img.width * k)} in wide, transparent.'))
        mk = M.mock_sticker(art_img)
        shop(mk, f'sticker-{name}.png')
        mocks[name] = mk
        if name == 'passed-out':            # also used by the empty cart and the 404 page
            shop(art_img, 'print-sticker-passed-out.png')
    return {
        'name': 'Kiss-Cut Stickers', 'shop_id': 'kiss-cut-sticker',
        'concept': 'Five die-cut stickers from the game: the Santa Panda face, the raccoon on the prowl, passed out with the hat on one foot, the Holiday Reserve bottle, and the wordmark.',
        'blank': 'Printful: Kiss-Cut Stickers', 'technique': 'Digital print on white vinyl, kiss-cut',
        'variants': 'Design: 5 options. Size: 4 x 4 in (3, 4 and 5.5 in all work from the same file).', 'files': files, 'mockups': mocks,
        'art': [(n.replace('-', ' ').title(), a, '#ffffff') for n, a in D.sticker_designs().items()],
        'placements': [('Sticker', '<design>.png', 'centred; transparent background')],
        'notes': ['Do not add a white border: Printful prints on white vinyl and cuts its own border around the artwork.'],
    }


PRODUCTS = [
    ('01-ugly-sweater', p_sweater, 64), ('02-mugshot-tee', p_tee, 32), ('03-pixel-ornaments', p_ornament, 18),
    ('04-trashed-panda-hoodie', p_hoodie, 58), ('05-poor-life-choices-mug', p_mug, 18), ('06-tail-stripe-socks', p_socks, 20),
    ('07-santa-panda-beanie', p_beanie, 30), ('08-gift-wrap', p_wrap, 22), ('09-holiday-cards', p_cards, 16), ('10-stickers', p_stickers, 6),
]


# ---------------------------------------------------------------------------
# docs
# ---------------------------------------------------------------------------
def spec_md(folder, spec, price):
    lines = [f"# {spec['name']}", '', f"**Retail:** ${price}  ·  **Shop id:** `{spec['shop_id']}`", '',
             '## Design', '', spec['concept'], '',
             '## Production', '', '| | |', '| --- | --- |',
             f"| Recommended blank | {spec['blank']} |", f"| Technique | {spec['technique']} |", f"| Variants | {spec['variants']} |", '',
             '### Placements', '', '| Placement | File | Size / position |', '| --- | --- | --- |']
    lines += [f'| {a} | `{b}` | {c} |' for a, b, c in spec['placements']]
    lines += ['', '### Files (`print/`)', '', '| File | Pixels | Notes |', '| --- | --- | --- |']
    lines += [f'| `{n}` | {w} x {h} | {note} |' for n, (w, h), note in spec['files']]
    if spec.get('extra'):
        lines += [''] + spec['extra']
    lines += ['', '### Notes', ''] + [f'- {n}' for n in spec['notes']]
    lines += ['', '### Before you publish', '', '- [ ] Upload the files above and check the provider\'s preview matches `mockups/`.',
              '- [ ] Order one sample.', '- [ ] Copy the variant IDs into `js/shop/catalog.js`.', '']
    with open(os.path.join(folder, 'spec.md'), 'w') as fh:
        fh.write('\n'.join(lines))


def readme(specs):
    ok = all(c[1] for c in checks)
    lines = [
        '# Trashed Panda: Holiday Drop production package', '',
        'Everything needed to set the merch up with a print-on-demand provider. Each product folder holds',
        'print-ready files (`print/`), approval mockups (`mockups/`) and a spec sheet (`spec.md`) with the',
        'recommended blank, technique, placement and colours. `line-sheet.pdf` has the whole drop on a few pages.', '',
        'Regenerate everything with `bash tools/build_all.sh` (it fails if any check below fails).', '',
        '## The drop', '', '| # | Product | Technique | Blank | Retail |', '| --- | --- | --- | --- | --- |',
    ]
    for (folder, _, price), spec in zip(PRODUCTS, specs):
        lines.append(f"| {folder[:2]} | [{spec['name']}]({folder}/spec.md) | {spec['technique']} | {spec['blank']} | ${price} |")
    lines += [
        '', '## How the files are made', '',
        '- **Pixel art, scaled in whole numbers.** Every file is the native pixel design enlarged by an integer factor with',
        '  nearest-neighbour sampling, so edges stay razor sharp at any size. Never resize these files by a fraction.',
        '- **300 dpi** for apparel, ceramics, stickers and cards; **150 dpi** for large-format gift wrap.',
        '- **Transparent backgrounds** wherever the product colour should show through.',
        '- **Built for the process:** knit charts use 4 yarn colours, embroidery uses 5 threads (limit 6), ornament art sits',
        '  inside the safe circle, black-garment tees have near-black ink knocked out.', '',
        '## Setting up with Printful + Shopify', '',
        '1. Connect Printful to your Shopify store.',
        '2. For each product, create it in Printful with the blank from its spec sheet and upload the files from `print/`.',
        '3. Match the variants (colours/sizes/designs) to the ones listed in `js/shop/catalog.js`. Check each blank\'s current base cost and shipping before confirming the retail prices above.',
        '4. Order a sample of each product before launch, especially the knit sweater and the embroidered beanie.',
        '5. Copy the Shopify variant IDs into `js/shop/catalog.js` and switch checkout on (see `docs/SHOP_SETUP.md`).', '',
        'Provider templates change over time and differ between providers. Each spec sheet gives physical sizes in inches,',
        'so if a template differs, keep the artwork centred at the stated width and scale by whole numbers only.', '',
        f"## Pre-flight checks ({'all passed' if ok else 'FAILED'})", '', '| Check | Result | Detail |', '| --- | --- | --- |',
    ]
    lines += [f"| {label} | {'pass' if passed else '**FAIL**'} | {detail} |" for label, passed, detail in checks]
    with open(os.path.join(MERCH, 'README.md'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------------------
# line sheet (PDF)
# ---------------------------------------------------------------------------
PX_FONT = os.path.join(ROOT, 'assets', 'fonts', 'press-start-2p-latin.woff2')
BODY_FONT = os.path.join(ROOT, 'assets', 'fonts', 'pixelify-sans-latin.woff2')
PW, PH = 1650, 1275            # US Letter landscape at 150 dpi
INKC, BG, CREAM, AMBER, MUTED = hexrgb('#140d09'), hexrgb('#f6ead2'), hexrgb('#fffaf0'), hexrgb('#a8620f'), hexrgb('#6e5c45')


def _font(path, size):
    return ImageFont.truetype(path, size)


def _wrap(draw, text, font, width):
    words, line, out = text.split(), '', []
    for w in words:
        t = (line + ' ' + w).strip()
        if draw.textlength(t, font=font) <= width:
            line = t
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def _page_base(title, subtitle=''):
    page = Image.new('RGB', (PW, PH), BG[:3])
    d = ImageDraw.Draw(page)
    d.rectangle((0, 0, PW, 96), fill=INKC[:3])
    d.fontmode = '1'
    d.text((60, 32), title.upper(), font=_font(PX_FONT, 32), fill=CREAM[:3])
    d.fontmode = 'L'
    if subtitle:
        d.text((60, 110), subtitle, font=_font(BODY_FONT, 26), fill=MUTED[:3])
    d.text((PW - 60, PH - 44), 'Trashed Panda · Holiday Drop · trashedpanda.lol', font=_font(BODY_FONT, 20), fill=MUTED[:3], anchor='ra')
    return page, d


def line_sheet(specs):
    pages = []
    # cover
    page, d = _page_base('Holiday Drop', 'Line sheet · 10 products · pixel art from the Trashed Panda game')
    logo = Image.open(os.path.join(ROOT, 'assets', 'ui', 'logo.png')).convert('RGBA')
    big = upscale(logo, 8)
    page.paste(big, (60, 170), big)
    f_name = _font(BODY_FONT, 20)
    cols, gap = 5, 54
    cell = (PW - 120 - (cols - 1) * gap) // cols
    for i, ((folder, _, price), spec) in enumerate(zip(PRODUCTS, specs)):
        x, y = 60 + (i % cols) * (cell + gap), 460 + (i // cols) * 380
        mk = upscale(next(iter(spec['mockups'].values())), 1)
        bgc = Image.new('RGBA', (cell, cell), hexrgb('#2a1b11'))
        bgc.alpha_composite(mk, ((cell - mk.width) // 2, (cell - mk.height) // 2))
        page.paste(bgc.convert('RGB'), (x, y))
        ty = y + cell + 14
        for ln in _wrap(d, f"{folder[:2]}  {spec['name']}", f_name, cell):
            d.text((x, ty), ln, font=f_name, fill=INKC[:3])
            ty += 26
        d.text((x, ty), f'${price}', font=f_name, fill=AMBER[:3])
    pages.append(page)
    # products
    f_cap = _font(BODY_FONT, 18)
    for (folder, _, price), spec in zip(PRODUCTS, specs):
        page, d = _page_base(spec['name'], f"${price} · {spec['technique']} · {spec['blank']}")
        mks = list(spec['mockups'].values())[:4]
        k = 3 if len(mks) <= 2 else 2
        mx, my, mg = 60, 170, 16
        right, bottom = mx, my
        for i, mk in enumerate(mks):
            t = upscale(mk, k)
            bgc = Image.new('RGBA', (t.width + 24, t.height + 24), hexrgb('#2a1b11'))
            bgc.alpha_composite(t, (12, 12))
            px = mx + (i % 2) * (bgc.width + mg)
            py = my + (i // 2) * (bgc.height + mg)
            page.paste(bgc.convert('RGB'), (px, py))
            right, bottom = max(right, px + bgc.width), max(bottom, py + bgc.height)
        tx = right + 70
        tw = PW - tx - 60
        ty = 170
        f_h, f_b = _font(PX_FONT, 16), _font(BODY_FONT, 22)
        def section(title, body_lines):
            nonlocal ty
            d.fontmode = '1'
            d.text((tx, ty), title.upper(), font=f_h, fill=AMBER[:3])
            d.fontmode = 'L'
            ty += 34
            for para in body_lines:
                for ln in _wrap(d, para, f_b, tw):
                    d.text((tx, ty), ln, font=f_b, fill=INKC[:3])
                    ty += 30
                ty += 6
            ty += 14
        section('Design', [spec['concept']])
        section('Variants', [spec['variants']])
        section('Placements', [f'{a}: {c}' for a, _, c in spec['placements']])
        nf = 8
        section('Print files', [f"{n} ({w}x{h})" for n, (w, h), _ in spec['files'][:nf]] + ([f"+ {len(spec['files']) - nf} more in print/"] if len(spec['files']) > nf else []))
        # flat artwork strip under the mockups, integer-scaled; spans the page if the text column is short
        arts = spec.get('art', [])
        if arts:
            ay = bottom + 40
            d.fontmode = '1'
            d.text((mx, ay), 'ARTWORK', font=_font(PX_FONT, 16), fill=AMBER[:3])
            d.fontmode = 'L'
            ay += 34
            avail_h = PH - 60 - ay - 30
            avail_w = (PW - 60 - mx) if ty < ay - 20 else (right - mx)
            def step(a, k_, label):
                return max(a.width * k_ + 16, int(d.textlength(label, font=f_cap)) + 4) + 20
            ka = 1
            for cand in range(8, 0, -1):
                w = sum(step(a, cand, lb) for lb, a, _ in arts) - 20
                h = max(a.height for _, a, _ in arts) * cand + 16
                if w <= avail_w and h <= avail_h:
                    ka = cand
                    break
            ax = mx
            cap_y = ay + max(a.height for _, a, _ in arts) * ka + 16 + 8
            for label, a, abg in arts:
                t = upscale(a, ka)
                bgc = Image.new('RGBA', (t.width + 16, t.height + 16), hexrgb(abg or '#2a1b11'))
                bgc.alpha_composite(t, (8, 8))
                page.paste(bgc.convert('RGB'), (ax, ay))
                d.text((ax, cap_y), label, font=f_cap, fill=MUTED[:3])
                ax += step(a, ka, label)
            d.text((mx, PH - 44), f'Artwork shown at {ka}x (1 square = 1 pixel of the design). Print files are the same art at whole-number scale.', font=_font(BODY_FONT, 18), fill=MUTED[:3])
        pages.append(page)
    # palette
    page, d = _page_base('Colour reference', 'Brand colours and the production colours used in the knit and embroidery files')
    groups = [('Brand', ['#140d09', '#f6ead2', '#f2a93b', '#d23a3a', '#2f6b3f', '#f2c14e']),
              ('Knit: red colourway', [D.YARN['red'][k] for k in ('base', 'cream', 'dark', 'accent')]),
              ('Knit: green colourway', [D.YARN['green'][k] for k in ('base', 'cream', 'dark', 'accent')]),
              ('Embroidery threads', list(D.THREADS.values()))]
    y = 190
    for title, hexes in groups:
        d.text((60, y), title, font=_font(BODY_FONT, 28), fill=INKC[:3])
        x = 60
        for hx in hexes:
            d.rectangle((x, y + 44, x + 120, y + 124), fill=hexrgb(hx)[:3], outline=INKC[:3], width=3)
            d.text((x, y + 134), hx, font=_font(BODY_FONT, 20), fill=INKC[:3])
            x += 150
        y += 220
    pages.append(page)
    pages[0].save(os.path.join(MERCH, 'line-sheet.pdf'), save_all=True, append_images=pages[1:], resolution=150)
    if PREVIEW:
        for i, pg in enumerate(pages):
            pg.resize((PW // 2, PH // 2)).save(os.path.join(PREVIEW, f'linesheet_{i}.png'))
    return len(pages)


# ---------------------------------------------------------------------------
def main():
    specs = []
    for folder, fn, price in PRODUCTS:
        out = os.path.join(MERCH, folder)
        if os.path.isdir(os.path.join(out, 'print')):
            shutil.rmtree(os.path.join(out, 'print'))
        if os.path.isdir(os.path.join(out, 'mockups')):
            shutil.rmtree(os.path.join(out, 'mockups'))
        spec = fn(out)
        for name, mk in spec['mockups'].items():
            save(upscale(mk, 3), os.path.join(out, 'mockups', f'{name}.png'), dpi=72)
        spec_md(out, spec, price)
        specs.append(spec)
    readme(specs)
    n_pages = line_sheet(specs)
    failed = [c for c in checks if not c[1]]
    for label, ok, detail in checks:
        print(('  ok  ' if ok else ' FAIL ') + label + (f'  ({detail})' if detail else ''))
    n_files = sum(len(s['files']) for s in specs)
    print(f'merch ok: {len(specs)} products, {n_files} print files, line sheet {n_pages} pages')
    if failed:
        raise SystemExit(f'{len(failed)} pre-flight check(s) failed')


if __name__ == '__main__':
    main()
