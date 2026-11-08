#!/usr/bin/env python3
"""Landing-page art: the store from the game, stocked and lit, as one static scene.

    python3 tools/build_home.py

Composited from the game's own assets (store backdrop, bottle sprites, ceiling tile and
the generated world data), so the landing page always matches the game.

Output: assets/ui/home-scene.png (800 x 270, shown at whole-number scales).
"""
import json
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAME = os.path.join(ROOT, 'assets', 'game')
UI = os.path.join(ROOT, 'assets', 'ui')
PREVIEW = os.environ.get('PREVIEW_DIR')

BW, BH = 40, 34                      # bottle cell (js/game/sprite-data.js)
KINDS = ['vodka', 'whiskey', 'wine', 'tequila', 'reserve']
# same palette as the renderer's twinkling bulbs (js/game/render.js)
BULBS = ['#ff5a52', '#ffd25a', '#58e08a', '#6cb2ff', '#ff9ad0']
HIGHLIGHT = hexrgb('#fffbe8')


def load_world():
    src = open(os.path.join(ROOT, 'js', 'game', 'world-data.js')).read()
    return json.loads(src[src.index('{'):src.rindex('}') + 1])


def blend(im, x, y, w, h, color, alpha):
    over = Image.new('RGBA', (w, h), hexrgb(color)[:3] + (round(255 * alpha),))
    im.alpha_composite(over, (x, y))


def rect(im, x, y, w, h, color):
    im.paste(Image.new('RGBA', (w, h), hexrgb(color) if isinstance(color, str) else color), (x, y))


def stock_shelves(im, world, rnd):
    bottles = Image.open(os.path.join(GAME, 'bottles.png')).convert('RGBA')
    boards = world['shelf']['boardTops']
    slots = [(unit, level, x) for unit, xs in enumerate(world['shelf']['bottleXs'])
             for level in range(len(boards)) for x in xs]
    upper = [i for i, s in enumerate(slots) if s[1] > 0]
    reserves = set(rnd.sample(upper, 2))
    for i, (unit, level, x) in enumerate(slots):
        kind = 4 if i in reserves else rnd.randrange(4)
        cell = bottles.crop((0, kind * BH, BW, (kind + 1) * BH))
        # renderer: top-left = (x - BW/2, (board - 2) + 1 - BH)
        im.alpha_composite(cell, (x - BW // 2, boards[level] - 1 - BH))


def light_bulbs(im, world, rnd):
    def bulb(b, i, size, phase):
        on = BULBS[(i + phase) % len(BULBS)]
        bx = b['x'] - (size >> 1)
        blend(im, bx - 1, b['y'] - 1, size + 2, size + 3, on, 0.2)
        rect(im, bx, b['y'], size, size + 1, on)
        rect(im, bx, b['y'], 1, 1, HIGHLIGHT)

    bulbs = world['bulbs']
    for i, b in enumerate(bulbs['garland']):
        bulb(b, i, 1, 0)
    for i, b in enumerate(bulbs['shelf']):
        bulb(b, i, 2, 2)
    for i, b in enumerate(bulbs['tree']):
        rect(im, b['x'] - 1, b['y'] - 1, 3, 3, '#14301d')
        rect(im, b['x'], b['y'], 2, 2, BULBS[i % len(BULBS)])
        if rnd.random() < 0.6:
            rect(im, b['x'], b['y'], 1, 1, HIGHLIGHT)
    tree = world['tree']
    blend(im, tree['x'] - 4, tree['base'] - 102, 9, 9, '#ffe9a0', 0.32)


def main():
    world = load_world()
    rnd = random.Random(2026)
    im = Image.open(os.path.join(GAME, 'store.png')).convert('RGBA')
    hole = world['hole']
    im.alpha_composite(Image.open(os.path.join(GAME, 'ceiling-tile.png')).convert('RGBA'), (hole['x'], hole['y']))
    stock_shelves(im, world, rnd)
    light_bulbs(im, world, rnd)
    im.save(os.path.join(UI, 'home-scene.png'), optimize=True)
    if PREVIEW:
        upscale(im, 2).save(os.path.join(PREVIEW, 'home-scene.png'))
    print('home ok', im.size)


if __name__ == '__main__':
    main()
