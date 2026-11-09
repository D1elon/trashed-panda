#!/usr/bin/env python3
"""UI art: pixel icon sprite (SVG), favicon, logo and the social share image.

    python3 tools/build_ui.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import hexrgb, upscale, outline  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UI = os.path.join(ROOT, 'assets', 'ui')
GAME = os.path.join(ROOT, 'assets', 'game')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'press-start-2p-latin.woff2')
os.makedirs(UI, exist_ok=True)
PREVIEW = os.environ.get('PREVIEW_DIR')

ICONS = {
    'pause': ['........', '.##..##.', '.##..##.', '.##..##.', '.##..##.', '.##..##.', '.##..##.', '........'],
    'play': ['.#......', '.##.....', '.###....', '.####...', '.####...', '.###....', '.##.....', '.#......'],
    'gear': ['...##...', '.#.##.#.', '..####..', '###..###', '###..###', '..####..', '.#.##.#.', '...##...'],
    'close': ['##....##', '###..###', '.######.', '..####..', '..####..', '.######.', '###..###', '##....##'],
    'cart': ['##.......', '.#.......', '.########', '.#######.', '.######..', '.#.......', '.#######.', '..#...#..'],
    'share': ['....##..', '...####.', '..######', '....##..', '##..##..', '#......#', '#......#', '########'],
    'trophy': ['########', '#.####.#', '#.####.#', '.######.', '..####..', '...##...', '..####..', '.######.'],
    'clock': ['..####..', '.#.##.#.', '#..##..#', '#..###.#', '#......#', '#......#', '.#....#.', '..####..'],
    'sound': ['...#....', '..##..#.', '####.#..', '####.#.#', '####.#.#', '####.#..', '..##..#.', '...#....'],
    'mute': ['...#....', '..##....', '####.#.#', '####..#.', '####..#.', '####.#.#', '..##....', '...#....'],
    'up': ['...##...', '..####..', '.######.', '########', '........', '........', '........', '........'],
    'down': ['........', '........', '........', '........', '########', '.######.', '..####..', '...##...'],
    'left': ['...#....', '..##....', '.###....', '####....', '####....', '.###....', '..##....', '...#....'],
    'right': ['....#...', '....##..', '....###.', '....####', '....####', '....###.', '....##..', '....#...'],
    'paw': ['..##.##..', '..##.##..', '#.......#', '##.....##', '...###...', '..#####..', '.#######.', '.##...##.'],
    'snow': ['...#...', '.#.#.#.', '..###..', '#######', '..###..', '.#.#.#.', '...#...'],
    'star': ['...#...', '...#...', '#######', '.#####.', '..###..', '.##.##.', '.#...#.'],
    'fullscreen': ['###..###', '#......#', '#......#', '........', '........', '#......#', '#......#', '###..###'],
    'help': ['.######.', '##....##', '.....##.', '....##..', '...##...', '...##...', '........', '...##...'],
    'gift': ['..#..#..', '...##...', '########', '#..##..#', '########', '#..##..#', '#..##..#', '########'],
    'truck': ['#####...', '#####.#.', '#####.##', '########', '########', '.##..##.', '........', '........'],
    'tag': ['....####', '...#...#', '..#..#.#', '.#.....#', '#.....#.', '.#...#..', '..#.#...', '...#....'],
    'minus': ['........', '........', '........', '########', '########', '........', '........', '........'],
    'plus': ['...##...', '...##...', '...##...', '########', '########', '...##...', '...##...', '...##...'],
    'check': ['.......#', '......##', '.....##.', '#...##..', '##.##...', '.###....', '..#.....', '........'],
    'heart': ['.##..##.', '########', '########', '########', '.######.', '..####..', '...##...', '........'],
    'home': ['...##...', '..####..', '.######.', '########', '.##..##.', '.##..##.', '.##..##.', '.##..##.'],
}


def icon_svg():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none">']
    for name, rows in ICONS.items():
        h, w = len(rows), max(len(r) for r in rows)
        d = []
        for y, row in enumerate(rows):
            x = 0
            while x < len(row):
                if row[x] == '#':
                    x0 = x
                    while x < len(row) and row[x] == '#':
                        x += 1
                    d.append(f'M{x0} {y}h{x - x0}v1h-{x - x0}z')
                else:
                    x += 1
        out.append(f'<symbol id="i-{name}" viewBox="0 0 {w} {h}"><path fill="currentColor" d="{"".join(d)}"/></symbol>')
    out.append('</svg>')
    with open(os.path.join(UI, 'icons.svg'), 'w') as fh:
        fh.write('\n'.join(out) + '\n')


# Hand-drawn front-facing raccoon head: the brand mark (favicon, nav, share image, merch).
# The in-game front face (tools/build_sprites.py HEAD_FRONT) at brand-mark size, so it
# matches the side view too: tan-rimmed ears, crown highlight and centre stripe, a cream
# brow, dark mask patches wrapping the eyes with a cream ring under them, cream muzzle,
# dark nose, tan cheeks; both eyes are the profile's eye, glancing the same way.
#   K outline  D mask  N shadow fur  F fur  H highlight  L tan  W cream  E pupil  G glint
FACE = [
    '.KK............KK.',
    'KLDK..........KDLK',
    'KLDNKKKKKKKKKKNDLK',
    'KFNFFHHHNNHHHFFNFK',
    'KFFFFFFHNNHFFFFFFK',
    'KWWWWWWFNNFWWWWWWK',
    'KDDDDEEDNNDDEEDDDK',
    'KDDDWEGDNNDWEGDDDK',
    'KDDDWEEDWWDWEEDDDK',
    'KWDDDDDWWWWDDDDDWK',
    '.KWWDDWWWWWWDDWWK.',
    '.KLWWWWKKKKWWWWLK.',
    '..KLWWWWKKWWWWLK..',
    '...KLLWWWWWWLLK...',
    '....KKKKKKKKKK....',
]
FACE_PAL = {
    'K': '#1a120c', 'D': '#402d20', 'N': '#62502f', 'F': '#76643c', 'H': '#8d7a50', 'L': '#b29c72',
    'W': '#ece2cc', 'E': '#0b0705', 'G': '#fffcf4',
}
HAT = [
    '..KKK..........',
    '.KWWWK.KKKK....',
    'KWWWwKKRRRRK...',
    'KwwwKRRRRRRrK..',
    '.KKKRRRhRRRRrK.',
    '...KRRRRRRRRrK.',
    '..KRRRRRRRRRRrK',
    '.KWWWWWWWWWWWWK',
    '.KWWWWWWWWWWWWK',
    '.KwwwwwwwwwwwwK',
]
HAT_PAL = {'K': '#2a1410', 'R': '#d8343a', 'r': '#9c1f2b', 'h': '#f26a5e', 'W': '#f6f1e7', 'w': '#c8bfb2'}


def paint(rows, pal):
    im = Image.new('RGBA', (max(len(r) for r in rows), len(rows)), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                px[x, y] = hexrgb(pal[ch])
    return im


def raccoon_face(santa=True):
    face = paint(FACE, FACE_PAL)
    if not santa:
        return face
    hat = paint(HAT, HAT_PAL)
    im = Image.new('RGBA', (face.width, face.height + 7), (0, 0, 0, 0))
    im.alpha_composite(face, (0, 7))
    im.alpha_composite(hat, (2, 0))
    return im


def build_favicon():
    face = raccoon_face(True)
    fw, fh = face.size
    fav = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    fav.alpha_composite(face, ((32 - fw) // 2, (32 - fh) // 2 + 1))
    fav.save(os.path.join(ROOT, 'favicon.png'))
    fav.save(os.path.join(ROOT, 'favicon.ico'), sizes=[(16, 16), (32, 32)])
    apple = Image.new('RGBA', (180, 180), hexrgb('#1a120c'))
    a = upscale(face, 7)
    apple.alpha_composite(a, ((180 - a.width) // 2, (180 - a.height) // 2 + 4))
    apple.save(os.path.join(ROOT, 'apple-touch-icon.png'))
    face.save(os.path.join(UI, 'raccoon-face.png'))
    return face


def build_app_icons(face):
    """Home-screen / install icons (web app manifest). The face sits inside the central
    safe zone so the same file also works as a maskable icon."""
    for size in (192, 512):
        icon = Image.new('RGBA', (size, size), hexrgb('#1a120c'))
        k = max(1, int(size * 0.56) // face.height)
        a = upscale(face, k)
        icon.alpha_composite(a, ((size - a.width) // 2, (size - a.height) // 2 + k // 2))
        icon.save(os.path.join(UI, f'icon-{size}.png'), optimize=True)


def pixel_text(text, color, outline_color=(26, 18, 12, 255), shadow=None):
    font = ImageFont.truetype(FONT, 8)
    w = len(text) * 8 + 4
    im = Image.new('RGBA', (w, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.fontmode = '1'
    d.text((2, 2), text, font=font, fill=color)
    im = im.crop(im.getbbox())
    pad = Image.new('RGBA', (im.width + 4, im.height + 4), (0, 0, 0, 0))
    pad.alpha_composite(im, (2, 2))
    out = outline(pad, outline_color)
    if shadow:
        sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
        mask = out.getchannel('A')
        sh.paste(Image.new('RGBA', out.size, shadow), (0, 0), mask)
        base = Image.new('RGBA', (out.width + 1, out.height + 1), (0, 0, 0, 0))
        base.alpha_composite(sh, (1, 1))
        base.alpha_composite(out, (0, 0))
        out = base
    return out


def build_logo():
    """'TRASHED PANDA' wordmark with snow on the letters and a Santa hat on the T."""
    cream = hexrgb('#fff4dc')
    top = pixel_text('TRASHED', cream, shadow=hexrgb('#b06a14'))
    bot = pixel_text('PANDA', hexrgb('#ffc24a'), shadow=hexrgb('#8a4a12'))
    w = max(top.width, bot.width) + 2
    logo = Image.new('RGBA', (w, top.height + bot.height + 6), (0, 0, 0, 0))
    logo.alpha_composite(top, ((w - top.width) // 2, 4))
    logo.alpha_composite(bot, ((w - bot.width) // 2, top.height + 5))
    # snow caps: white on the top edge of each glyph in the top word
    px = logo.load()
    snow = hexrgb('#ffffff')
    for x in range(logo.width):
        for y in range(logo.height):
            if px[x, y][3] and px[x, y][:3] == cream[:3]:
                if y > 0 and px[x, y - 1][3] and px[x, y - 1][:3] == (26, 18, 12):
                    if (x * 7 + y) % 3:
                        px[x, y - 1] = snow
                break
    logo.save(os.path.join(UI, 'logo.png'))
    return logo


def build_help_icons():
    bottles = Image.open(os.path.join(GAME, 'bottles.png'))
    BW, BH = 40, 34
    cell = lambda col, row: bottles.crop((col * BW, row * BH, col * BW + BW, row * BH + BH))
    cell(1, 0).save(os.path.join(UI, 'help-swipe.png'))
    cell(5, 1).save(os.path.join(UI, 'help-drink.png'))
    res = cell(0, 4).copy()
    px = res.load()
    for (x, y) in ((11, 6), (28, 12), (9, 20)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = hexrgb('#fff1c2') if (dx, dy) == (0, 0) else hexrgb('#ffd36b')
    res.save(os.path.join(UI, 'help-reserve.png'))
    # buzz meter about to max out, with dizzy stars
    m = Image.new('RGBA', (BW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    d.rectangle((3, 14, 36, 23), fill=hexrgb('#1a120c'))
    cols = ['#5fb56f', '#5fb56f', '#c9d65a', '#f2c14e', '#f2a93b', '#f08a3a', '#e0533d', '#e0533d', '#d24bc4', '#d24bc4']
    for i, c in enumerate(cols):
        d.rectangle((5 + i * 3, 16, 6 + i * 3, 21), fill=hexrgb(c))
    for (x, y) in ((8, 6), (20, 4), (31, 7)):
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            m.putpixel((x + dx, y + dy), hexrgb('#fff3b0') if (dx, dy) == (0, 0) else hexrgb('#ffd34a'))
    m.save(os.path.join(UI, 'help-buzz.png'))


def build_snow_tile():
    import random
    rnd = random.Random(11)
    t = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    for i in range(16):
        x, y = rnd.randrange(64), rnd.randrange(64)
        a = rnd.choice((26, 34, 48))
        t.putpixel((x, y), (244, 247, 251, a))
        if i % 5 == 0:
            t.putpixel(((x + 1) % 64, y), (244, 247, 251, a))
    t.save(os.path.join(UI, 'snow-tile.png'))


def main():
    icon_svg()
    build_snow_tile()
    build_help_icons()
    face = build_favicon()
    build_app_icons(face)
    logo = build_logo()
    if PREVIEW:
        upscale(logo, 6).save(os.path.join(PREVIEW, 'logo.png'))
        upscale(face, 8).save(os.path.join(PREVIEW, 'face.png'))
    print('ui ok', logo.size, face.size)


if __name__ == '__main__':
    main()
