#!/usr/bin/env python3
"""Social share images (1200x630), composed as pixel art and upscaled by whole numbers.

    python3 tools/build_og.py      (run after build_store, build_ui and build_merch)
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, outline, text3x5, text3x5_width  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(ROOT, 'assets', 'game')
UI = os.path.join(ROOT, 'assets', 'ui')
SHOP = os.path.join(ROOT, 'assets', 'shop')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'press-start-2p-latin.woff2')


def text8(s, color, ol=hexrgb('#120c09')):
    f = ImageFont.truetype(FONT, 8)
    im = Image.new('RGBA', (len(s) * 8 + 6, 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((3, 3), s, font=f, fill=color)
    return outline(im.crop(im.getbbox()).crop((-1, -1, im.getbbox()[2] - im.getbbox()[0] + 1, im.getbbox()[3] - im.getbbox()[1] + 1)), ol)


def band(w, text, bg, fg):
    tw = text3x5_width(text)
    im = Image.new('RGBA', (tw + 10, 9), bg)
    text3x5(im, 5, 2, text, fg)
    ImageDraw.Draw(im).rectangle((0, 0, im.width - 1, im.height - 1), outline=hexrgb('#120c09'))
    return im


def og_home():
    W, H = 240, 126
    store = Image.open(os.path.join(GAME, 'store.png')).convert('RGBA')
    im = store.crop((40, 120, 40 + W, 120 + H)).copy()
    shade = Image.new('RGBA', (W, H), (12, 8, 6, 120))
    im.alpha_composite(shade)
    rac = Image.open(os.path.join(GAME, 'raccoon.png')).convert('RGBA')
    walk = rac.crop((0, 5 * 66, 80, 6 * 66))
    im.alpha_composite(walk, (150, H - 66 - 4))
    logo = Image.open(os.path.join(UI, 'logo.png')).convert('RGBA')
    big = upscale(logo, 2)
    im.alpha_composite(big, (16, 30))
    kick = band(W, 'HOLIDAY EDITION', hexrgb('#d23a3a'), hexrgb('#fff4dc'))
    im.alpha_composite(kick, (16 + (big.width - kick.width) // 2, 18))
    sub = 'A 60 SECOND PIXEL ARCADE GAME'
    sw = text3x5_width(sub)
    plate = Image.new('RGBA', (sw + 8, 9), (12, 8, 6, 210))
    text3x5(plate, 4, 2, sub, hexrgb('#f6ead2'))
    im.alpha_composite(plate, (16 + (big.width - plate.width) // 2, 30 + big.height + 4))
    url = 'TRASHEDPANDA.LOL'
    uw = text3x5_width(url)
    u = Image.new('RGBA', (uw + 8, 9), hexrgb('#f2a93b'))
    text3x5(u, 4, 2, url, hexrgb('#120c09'))
    im.alpha_composite(u, (16 + (big.width - u.width) // 2, 30 + big.height + 16))
    upscale(im, 5).save(os.path.join(UI, 'og.png'), optimize=True)


def og_shop():
    W, H = 400, 210                         # x3 = 1200 x 630
    im = Image.new('RGBA', (W, H), hexrgb('#1d3324'))
    d = ImageDraw.Draw(im)
    d.rectangle((0, H - 34, W, H), fill=hexrgb('#2a1b11'))
    d.line((0, H - 34, W, H - 34), fill=hexrgb('#4a3222'))
    import random
    rnd = random.Random(5)
    for _ in range(110):
        im.putpixel((rnd.randrange(W), rnd.randrange(H - 34)), (244, 247, 251, 170))
    for name, x, y in (('ornament-santa-panda.png', -8, 14), ('mug-morning.png', 236, 34), ('sweater-red-front.png', 120, 30)):
        im.alpha_composite(Image.open(os.path.join(SHOP, name)).convert('RGBA'), (x, y))
    t = text8('THE HOLIDAY DROP', hexrgb('#fff4dc'))
    plate = Image.new('RGBA', (t.width + 10, t.height + 8), hexrgb('#d23a3a'))
    plate.alpha_composite(t, (5, 4))
    ImageDraw.Draw(plate).rectangle((0, 0, plate.width - 1, plate.height - 1), outline=hexrgb('#120c09'))
    im.alpha_composite(plate, ((W - plate.width) // 2, 4))
    url = 'TRASHEDPANDA.LOL/SHOP'
    u = Image.new('RGBA', (text3x5_width(url) + 8, 9), hexrgb('#f2a93b'))
    text3x5(u, 4, 2, url, hexrgb('#120c09'))
    im.alpha_composite(u, ((W - u.width) // 2, H - 19))
    upscale(im, 3).save(os.path.join(UI, 'og-shop.png'), optimize=True)


if __name__ == '__main__':
    og_home()
    og_shop()
    print('og ok')
