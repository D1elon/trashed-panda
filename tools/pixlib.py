"""Shared helpers for the Trashed Panda art pipeline.

The original sprite sheets are high-resolution "pseudo pixel art": soft edges,
JPEG-ish noise and a grid that differs per sheet. These helpers snap them onto a
real, uniform pixel grid so every sprite in the game shares the same pixel size.
"""
from PIL import Image
import numpy as np

ALPHA_CUT = 120  # coverage needed for a downsampled pixel to count as opaque


def repixelize(img, factor, alpha_cut=ALPHA_CUT, size=None):
    """Box-downsample an RGBA image by `factor` with premultiplied alpha and
    hard (1-bit) alpha. Returns a crisp RGBA image at native pixel size."""
    img = img.convert('RGBA')
    w, h = img.size
    nw, nh = size if size else (max(1, round(w / factor)), max(1, round(h / factor)))
    a = np.asarray(img).astype(np.float32)
    alpha = a[..., 3:4] / 255.0
    prem = np.clip(a[..., :3] * alpha, 0, 255).astype(np.uint8)
    rgb = np.asarray(Image.fromarray(prem, 'RGB').resize((nw, nh), Image.BOX)).astype(np.float32)
    A = np.asarray(Image.fromarray(a[..., 3].astype(np.uint8), 'L').resize((nw, nh), Image.BOX)).astype(np.float32)
    rgb = rgb / np.maximum(A, 1)[..., None] * 255.0
    out = np.zeros((nh, nw, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = np.where(A >= alpha_cut, 255, 0)
    out[out[..., 3] == 0] = 0
    return Image.fromarray(out, 'RGBA')


def quantize(img, colors=24, palette_img=None):
    """Reduce the opaque pixels of an RGBA image to a small palette (no dither)."""
    a = np.asarray(img.convert('RGBA')).copy()
    mask = a[..., 3] > 0
    if not mask.any():
        return img
    rgb = Image.fromarray(a[..., :3], 'RGB')
    if palette_img is not None:
        q = rgb.quantize(palette=palette_img, dither=Image.Dither.NONE)
    else:
        # Build the palette from opaque pixels only so transparent black doesn't steal a slot.
        px = a[..., :3][mask].reshape(1, -1, 3)
        pal_src = Image.fromarray(px, 'RGB').quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        q = rgb.quantize(palette=pal_src, dither=Image.Dither.NONE)
    a[..., :3] = np.asarray(q.convert('RGB'))
    a[~mask] = 0
    return Image.fromarray(a, 'RGBA')


def remove_specks(img, min_size=4, light_thresh=None):
    """Drop tiny disconnected opaque islands (noise left by background removal)."""
    a = np.asarray(img).copy()
    mask = a[..., 3] > 0
    h, w = mask.shape
    seen = np.zeros_like(mask)
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                stack = [(y, x)]; comp = []
                seen[y, x] = True
                while stack:
                    cy, cx = stack.pop(); comp.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; stack.append((ny, nx))
                if len(comp) < min_size:
                    for cy, cx in comp:
                        a[cy, cx] = 0
    if light_thresh is not None:
        # isolated near-white pixels with no opaque neighbours above/below are background bleed
        lum = a[..., :3].astype(int).sum(-1)
        for y in range(h):
            for x in range(w):
                if a[y, x, 3] and lum[y, x] > light_thresh:
                    n = 0
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx, 3] and lum[ny, nx] < light_thresh:
                            n += 1
                    if n <= 1:
                        a[y, x] = 0
    return Image.fromarray(a, 'RGBA')


def outline(img, color=(20, 12, 8, 255)):
    """Add a 1px outline around opaque pixels (4-neighbourhood)."""
    a = np.asarray(img).copy()
    m = a[..., 3] > 0
    grow = np.zeros_like(m)
    grow[1:, :] |= m[:-1, :]; grow[:-1, :] |= m[1:, :]
    grow[:, 1:] |= m[:, :-1]; grow[:, :-1] |= m[:, 1:]
    ring = grow & ~m
    a[ring] = color
    return Image.fromarray(a, 'RGBA')


def upscale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def bbox(img):
    return img.getchannel('A').getbbox()


def hexrgb(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


# A tiny 3x5 pixel font for signage that must stay legible at native resolution.
FONT3x5 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'], 'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '##.'],
    '%': ['#.#', '..#', '.#.', '#..', '#.#'], '!': ['.#.', '.#.', '.#.', '...', '.#.'],
    '-': ['...', '...', '###', '...', '...'], '.': ['...', '...', '...', '...', '.#.'],
    "'": ['.#.', '.#.', '...', '...', '...'], ' ': ['...', '...', '...', '...', '...'],
    '&': ['.#.', '#.#', '.#.', '#.#', '.##'], '$': ['.##', '##.', '.#.', '.##', '##.'],
    '/': ['..#', '..#', '.#.', '#..', '#..'], ':': ['...', '.#.', '...', '.#.', '...'],
}


def text3x5(im, x, y, s, color, spacing=1):
    """Draw text with the 3x5 font onto a PIL RGBA image. Returns the width drawn."""
    px = im.load()
    cx = x
    for ch in s.upper():
        g = FONT3x5.get(ch, FONT3x5[' '])
        for gy, row in enumerate(g):
            for gx, c in enumerate(row):
                if c == '#' and 0 <= cx + gx < im.width and 0 <= y + gy < im.height:
                    px[cx + gx, y + gy] = color
        cx += 3 + spacing
    return cx - x - spacing


def text3x5_width(s, spacing=1):
    return len(s) * (3 + spacing) - spacing
