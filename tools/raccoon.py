"""The raccoon, drawn from scratch.

One character model for the whole project: the game's sprite sheet, the brand face, the
passed-out scene and every merch design are all rendered from this file, so they cannot
drift apart.

The heads are hand-placed pixel art (they carry the likeness). Bodies, limbs and the
ringed tail are built from a few soft shapes rasterised straight onto the pixel grid and
then shaded with a fixed ramp, so every pose shares the same proportions, light and line.

Raccoon notes this model follows: a grizzled grey coat (not brown); a black "bandit" mask
that slants down and out from the eyes; white brows and a white muzzle around a black nose;
a dark stripe up the bridge of the nose; rounded, white-rimmed ears; cheek ruffs; a hunched
back with the hips higher than the shoulders; dark paws; a bushy tail with dark rings and a
dark tip.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

CW, CH = 80, 66          # sprite cell
CX = 39                  # body centre inside the cell (the game anchors on this column)
SS = 6                   # supersampling used to rasterise the soft shapes

# K outline  M mask / rings / paws  d deep shadow  S shadow fur  F fur  H highlight
# L light fur  W white  E eye  G glint  N nose  m closed lid  P/p tongue
# hat: k outline  R red  r shade  h highlight  Y trim  y trim shade      A/a motion arc
PALETTE = {
    'K': '#1b1513', 'M': '#352d29', 'd': '#4c453f', 'S': '#655e55', 'F': '#8a8275',
    'H': '#aca392', 'L': '#c8beab', 'W': '#f2ecdf', 'E': '#0b0808', 'G': '#ffffff',
    'N': '#120d0c', 'm': '#6a5d55', 'P': '#e8798f', 'p': '#b24a62',
    'k': '#2a1410', 'R': '#d8343a', 'r': '#9c1f2b', 'h': '#f26a5e', 'Y': '#f6f1e7', 'y': '#c8bfb2',
    'A': '#f6efe0', 'a': '#d9ccae',
}


def rgba(ch):
    v = PALETTE[ch].lstrip('#')
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255)


# ---------------------------------------------------------------------------
# shapes
# ---------------------------------------------------------------------------
def _raster(fn, w=CW, h=CH):
    im = Image.new('L', (w * SS, h * SS), 0)
    fn(ImageDraw.Draw(im))
    return np.asarray(im.resize((w, h), Image.BOX)) >= 128


def ellipse(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return _raster(lambda d: d.ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS), fill=255))


def poly(pts):
    return _raster(lambda d: d.polygon([(x * SS, y * SS) for x, y in pts], fill=255))


def _spline(pts, steps=10):
    """Catmull-Rom through (x, y, r) points."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (np.array(q, float) for q in p[i - 1:i + 3])
        for s in range(steps):
            t = s / steps
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(np.array(pts[-1], float))
    return out


def tube(pts, smooth=True):
    """A soft limb through (x, y, radius) points. Returns (mask, samples)."""
    sm = _spline(pts) if smooth and len(pts) > 2 else None
    if sm is None:
        sm = []
        for a, b in zip(pts, pts[1:]):
            for s in range(12):
                sm.append(np.array(a, float) + (np.array(b, float) - np.array(a, float)) * s / 12)
        sm.append(np.array(pts[-1], float))

    def draw(d):
        for x, y, r in sm:
            d.ellipse(((x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS), fill=255)
    return _raster(draw), sm


def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, ye = max(0, dy), h + min(0, dy)
    xs, xe = max(0, dx), w + min(0, dx)
    out[ys:ye, xs:xe] = m[ys - dy:ye - dy, xs - dx:xe - dx]
    return out


def grow(m):
    return m | shift(m, 1, 0) | shift(m, -1, 0) | shift(m, 0, 1) | shift(m, 0, -1)


def top_band(m, n):
    return m & ~shift(m, 0, n)


def bottom_band(m, n):
    return m & ~shift(m, 0, -n)


def jag(m, band, pattern):
    """A band whose depth follows `pattern` across the columns: a furry, uneven edge."""
    out = np.zeros_like(m)
    cols = np.arange(m.shape[1])
    for depth in set(pattern):
        if depth <= 0:
            continue
        sel = np.array([pattern[x % len(pattern)] == depth for x in cols])
        out[:, sel] = band(m, depth)[:, sel]
    return out


HI = [2, 2, 3, 2, 3, 3, 2, 2, 3, 2, 2, 3, 3]
LO = [3, 2, 3, 3, 2, 3, 2, 2, 3, 3, 2]


# ---------------------------------------------------------------------------
# canvas
# ---------------------------------------------------------------------------
class Cel:
    def __init__(self, w=CW, h=CH):
        self.c = np.full((h, w), '.', '<U1')

    def paint(self, m, ch):
        self.c[m] = ch

    def part(self, m, ch='F', sep='d'):
        """Lay a part over what is already there, with a soft dividing line around it."""
        if sep:
            self.c[grow(m) & ~m & (self.c != '.')] = sep
        self.c[m] = ch

    def fur(self, m, hi=HI, lo=LO, sep='d'):
        self.part(m, 'F', sep)
        if hi:
            self.c[jag(m, top_band, hi)] = 'H'
        if lo:
            self.c[jag(m, bottom_band, lo)] = 'S'

    def stamp(self, rows, x, y, flipx=False, flipy=False, soft=False):
        """Place hand-drawn rows. soft: outline pixels landing on fur become a dividing line."""
        rows = [r[::-1] for r in rows] if flipx else list(rows)
        rows = rows[::-1] if flipy else rows
        h, w = self.c.shape
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != '.' and 0 <= y + j < h and 0 <= x + i < w:
                    if soft and ch == 'K' and self.c[y + j, x + i] not in ('.', 'K'):
                        ch = 'd'
                    self.c[y + j, x + i] = ch

    def ticks(self, m, seed=0, every=23):
        """A few short darker strokes in the mid-tone: grizzled fur, without noise."""
        f = self.c == 'F'
        inner = m & f & shift(f, 1, 0) & shift(f, -1, 0) & shift(f, 0, 1) & shift(f, 0, -1) & shift(f, -2, 0)
        ys, xs = np.nonzero(inner)
        for y, x in zip(ys, xs):
            if (x * 7 + y * 13 + seed) % every == 0:
                self.c[y, x] = 'S'
                self.c[y, x + 1] = 'S'

    def outline(self):
        op = self.c != '.'
        inked = np.isin(self.c, ('K', 'k', 'A', 'a'))
        self.c[grow(op & ~inked) & ~op] = 'K'

    def image(self):
        h, w = self.c.shape
        a = np.zeros((h, w, 4), np.uint8)
        for ch in np.unique(self.c):
            if ch != '.':
                a[self.c == ch] = rgba(ch)
        return Image.fromarray(a, 'RGBA')


# ---------------------------------------------------------------------------
# heads (hand-placed)
# ---------------------------------------------------------------------------
# Profile, facing right. 22 x 20.
HEAD_SIDE = [
    '....KKKK..............',
    '...KWWWWK....KK.......',
    '..KWMMMMWK..KWWK......',
    '..KWMMMMMWK.KWMSK.....',
    '..KWSMMMMFKKKSMFSK....',
    '..KFFSSSFHHHHFFFFSK...',
    '.KFFFFFHHHHHHHHFFFSK..',
    '.KFFFFHHHHHHHHHHFFSK..',
    'KFFFFHHHWWWWWWWWWFSSK.',
    'KFFFHHHWWMMMMMMMWWSSK.',
    'KFFHHHMMMMMMEGMMMWSSSK',
    'KFHHMMMMMMMMEEMMMMWWSK',
    'KHHHHMMMMMMMMMMMMWWWNN',
    'KLLHHWWMMMMMMMWWWWWWNN',
    'KLLLLHWWWWWWWWWWWWWWWK',
    '.KLLLHHWWWWWWWWKKKKKK.',
    '.KLLLLLHHWWWWWWWWK....',
    'KLLLLLLLLHHWWWWKK.....',
    '.KKLLLLLLLLLWKK.......',
    '...KKKKKKKKKK.........',
]
EYE_SIDE = (12, 10)       # top-left of the 2 x 2 eye inside HEAD_SIDE

# Front. 26 x 22.
HEAD_FRONT = [
    '....KKK............KKK....',
    '...KWWWK..........KWWWK...',
    '..KWMMMWK........KWMMMWK..',
    '..KWMMMSWKKKKKKKKWSMMMWK..',
    '..KFSMSFHHHHSSHHHHFSMSFK..',
    '..KFFFFHHHHHSSHHHHHFFFFK..',
    '.KFFFFHHHHHFSSFHHHHHFFFFK.',
    '.KFFWWWWWWHFSSFHWWWWWWFFK.',
    'KFFWWWWWWWWFSSFWWWWWWWWFFK',
    'KLWWMMMMMMWWSSWWMMMMMMWWLK',
    'KLWMMMMEEMMWSSWMMEEMMMMWLK',
    'KKMMMMMEGMMMSSMMMEGMMMMMKK',
    '.KMMMMMMMMMWWWWMMMMMMMMMK.',
    'KLLMMMMMMWWWWWWWWMMMMMMLLK',
    'KLLLMMMWWWWWWWWWWWWMMMLLLK',
    '.KLLLLWWWWWNNNNWWWWWLLLLK.',
    '..KLLLWWWWWWNNWWWWWWLLLK..',
    '...KLLLWWWWWKKWWWWWLLLK...',
    '....KLLLWWWKWWKWWWLLLK....',
    '.....KKLLWWWWWWWWLLKK.....',
    '.......KKLLLLLLLLKK.......',
    '.........KKKKKKKK.........',
]
EYES_FRONT = ((7, 10), (17, 10))

# Back of the head (climbing). 20 x 15.
HEAD_BACK = [
    '..KKK..........KKK..',
    '.KWSSK........KSSWK.',
    '.KWSSSK......KSSSWK.',
    '.KWSSSSKKKKKKSSSSWK.',
    '.KFSSFHHHHHHHHFSSFK.',
    'KFFFHHHHHHHHHHHHFFFK',
    'KFFHHHHHHFFHHHHHHFFK',
    'KFFHHHHFFFFFFHHHHFFK',
    'KLFFHHFFFFFFFFHHFFLK',
    'KLLFFFFFFSSFFFFFFLLK',
    '.KLLFFFFSSSSFFFFLLK.',
    '.KKLFFFSSSSSSFFFLKK.',
    '...KKFFFSSSSFFFKK...',
    '.....KFFFFFFFFK.....',
    '......FFFFFFFF......',
]

EYES = {
    'open': ['EG', 'EE'],
    'closed': ['MM', 'mm'],
    'ko': None,           # drawn as a cross, see _eye
}

# Santa hats: side (tail flops back), back (climbing) and front (brand face).
HAT_SIDE = [
    '.......kkkk.....',
    '.....kkRRRRk....',
    '...kkRRRhRRrk...',
    '..kRRRRRRRRRrk..',
    '.kRRkkkRRRRRRrk.',
    'kYYk..kRRRRRRrk.',
    'kYYyk.kRRRRRRRrk',
    'kyyyk.kRRRRRRRrk',
    '.kkk.kYYYYYYYYYk',
    '....kYYYYYYYYYYk',
    '....kyyyyyyyyyyk',
    '.....kkkkkkkkkk.',
]
HAT_BACK = [
    '..kkk..........',
    '.kYYYk.kkkk....',
    'kYYYykkRRRRk...',
    'kyyykRRRRRRrk..',
    '.kkkRRRhRRRRrk.',
    '...kRRRRRRRRrk.',
    '..kRRRRRRRRRRrk',
    '..kRRRRRRRRRRrk',
    '.kYYYYYYYYYYYYk',
    '.kYYYYYYYYYYYYk',
    '.kyyyyyyyyyyyyk',
    '..kkkkkkkkkkkk.',
]


def _eye(cel, x, y, kind):
    if kind == 'ko':
        for dx, dy in ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)):
            cel.c[y + dy, x + dx] = 'W'
        return
    cel.stamp(EYES[kind], x, y)


# ---------------------------------------------------------------------------
# tail
# ---------------------------------------------------------------------------
RING = 3.2


def tail(cel, pts, behind=True):
    """Bushy tail through (x, y, r) points, base first: dark rings, dark tip."""
    m, sm = tube(pts)
    s = [0.0]
    for a, b in zip(sm, sm[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = s[-1]
    ys, xs = np.nonzero(m)
    px = np.array([q[0] for q in sm])
    py = np.array([q[1] for q in sm])
    sv = np.array(s)
    if behind:
        cel.c[m] = 'L'
    else:
        cel.part(m, 'L')
    lower = bottom_band(m, 2)
    for y, x in zip(ys, xs):
        i = int(np.argmin((px - (x + 0.5)) ** 2 + (py - (y + 0.5)) ** 2))
        from_tip = total - sv[i]
        dark = from_tip < RING * 0.9 or int((from_tip - RING * 0.9) // RING) % 2 == 1
        if dark:
            cel.c[y, x] = 'M'
        elif lower[y, x]:
            cel.c[y, x] = 'H'
    return m


# ---------------------------------------------------------------------------
# limbs
# ---------------------------------------------------------------------------
def left_band(m, n):
    return m & ~shift(m, n, 0)


def right_band(m, n):
    return m & ~shift(m, -n, 0)


def _paw(cel, x0, y0, x1, y1, far=False):
    paw = _raster(lambda d: d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), radius=1.2 * SS, fill=255))
    cel.c[paw] = 'M'
    if not far:
        cel.c[top_band(paw, 1)] = 'd'
    return paw


def _hand(cel, x, y, r=2.2):
    m = ellipse(x, y, r)
    cel.part(m, 'M')
    cel.c[top_band(m, 1) & left_band(m, 2)] = 'd'
    return m


def _walk_leg(cel, top, foot, r, far=False, hind=False, haunch=None):
    """A leg from `top` down to a flat paw at `foot` (x, ground y)."""
    tx, ty = top
    fx, fy = foot
    m, _ = tube([(tx, ty, r + 0.5), (fx - (0.6 if hind else 0), fy - r, r - 0.2)], smooth=False)
    if haunch is not None:
        m = m | haunch
    if far:
        cel.c[m] = 'S'
        cel.c[bottom_band(m, 2) & right_band(m, 1)] = 'd'
    else:
        cel.part(m, 'F')
        if haunch is not None:
            cel.c[jag(haunch, top_band, [1, 2, 2, 1, 2])] = 'H'
        cel.c[right_band(m, 1) & (cel.c == 'F')] = 'S'
    _paw(cel, fx - 2.0, fy - 2.4, fx + (3.6 if hind else 3.0), fy, far)


# ---------------------------------------------------------------------------
# side poses: walk, blink, drink
# ---------------------------------------------------------------------------
GROUND = 51.0     # the outline's bottom row sits on this row of the cell


def _step(u, reach=4.0):
    """Foot offset (dx, lift) at walk-cycle position u in [0, 1)."""
    u %= 1.0
    if u < 0.5:
        return reach - 4 * reach * u, 0.0
    v = (u - 0.5) * 2
    return -reach + 2 * reach * v, 2.4 * math.sin(math.pi * v)


def side(phase=0.0, eye='open', hat=False, mode='walk', lick=0):
    """Profile raccoon facing right. mode: 'walk' | 'drink'."""
    cel = Cel()
    g = GROUND
    i6 = int(round(phase * 6)) % 6
    drink = mode == 'drink'
    bob = 1 if (not drink and i6 in (1, 4)) else 0
    dip = (0, 1, 1, 0, 0, 0)[lick % 6] if drink else 0
    hip = (30.0, 33.0 + bob)
    chest = (46.0, 36.2 + bob) if not drink else (45.5, 40.4)
    sway = (0, 1, 1, 0, -1, -1)[i6] if not drink else (0, 0, 1, 1, 0, 0)[lick % 6]
    tail(cel, [(20.5, 36.0 + bob, 4.0), (14.5, 39.5 + bob, 5.2), (9.0, 43.6 + bob + sway * 0.5, 5.0), (5.4, 46.6 + bob * 0.5 + sway * 0.5, 3.4)])
    if drink:
        feet = {'nh': (26.5, g), 'fh': (32.0, g), 'nf': (50.0, g), 'ff': (54.0, g)}
    else:
        feet = {}
        for key, base, ph in (('nf', 46.5, 0.0), ('fh', 32.0, 0.0), ('nh', 26.5, 0.5), ('ff', 50.0, 0.5)):
            dx, lift = _step(phase + ph)
            feet[key] = (base + dx, g - lift)
    _walk_leg(cel, (33.0, 41.0 + bob), feet['fh'], 2.9, far=True, hind=True)
    _walk_leg(cel, (50.0, 41.0 + bob) if not drink else (50.5, 44.5), feet['ff'], 2.5, far=True)
    # body: hips higher than the shoulders
    mid = ((hip[0] + chest[0]) / 2, (hip[1] + chest[1]) / 2 - 0.8)
    body, _ = tube([(hip[0], hip[1], 11.6), (mid[0], mid[1], 10.8), (chest[0], chest[1], 9.6)], smooth=False)
    cel.fur(body, sep=None)
    haunch = ellipse(27.0, 38.8 + bob, 6.6, 6.8)
    _walk_leg(cel, (27.0, 42.5 + bob), feet['nh'], 3.0, hind=True, haunch=haunch)
    _walk_leg(cel, (46.5, 41.5 + bob) if not drink else (46.5, 44.5), feet['nf'], 2.6)
    # head
    hx, hy = (50, 19 + bob) if not drink else (51, 30 + dip)
    neck = ellipse(hx + 4.0, hy + 12.0, 6.0, 6.5)
    cel.c[neck & (cel.c == '.')] = 'F'
    cel.stamp(HEAD_SIDE, hx, hy, soft=True)
    _eye(cel, hx + EYE_SIDE[0], hy + EYE_SIDE[1], eye)
    if drink:
        # the tongue comes out of the front of the mouth, under the nose, and laps the floor
        n = (1, 2, 3, 3, 2, 1)[lick % 6]
        for k in range(n):
            y = min(hy + 16 + k, int(g) - 1)
            cel.c[y, hx + 18] = 'P'
            cel.c[y, hx + 19] = 'P' if k < n - 1 else 'p'
    if hat:
        cel.stamp(HAT_SIDE, hx + 1, hy - 6)
    cel.outline()
    return cel


# ---------------------------------------------------------------------------
# front poses: stand, swipe, fall
# ---------------------------------------------------------------------------
STAND_GROUND = 62.0
# right-hand positions for the swipe row: 0 rest, 1 wind-up, 2 swing, 3 full reach, 4 follow-through, 5 flail
SWIPE = [
    {'r': (49.5, 46.5), 'l': (30.5, 46.5)},
    {'r': (53.5, 31.5), 'l': (31.0, 46.0)},
    {'r': (59.0, 35.5), 'l': (30.5, 45.5), 'arc': 1},
    {'r': (61.0, 40.5), 'l': (30.0, 45.5), 'arc': 2},
    {'r': (58.5, 45.5), 'l': (30.5, 46.0), 'arc': 3},
    {'r': (54.5, 29.5), 'l': (25.0, 30.5)},
]


def _arm(cel, shoulder, hand, bend=1.0):
    sx, sy = shoulder
    hx, hy = hand
    ex, ey = (sx + hx) / 2 + bend * (1.5 if hx >= sx else -1.5), (sy + hy) / 2 + 1.2
    m, _ = tube([(sx, sy, 3.0), (ex, ey, 2.6), (hx, hy, 2.2)])
    cel.part(m, 'F')
    cel.c[jag(m, top_band, [1, 1, 2]) & (cel.c == 'F')] = 'H'
    _hand(cel, hx, hy)


def _arc(cel, kind):
    """Motion streak following the swiping paw."""
    if kind == 1:
        outer, inner = ellipse(53.5, 38.5, 11.5, 11.0), ellipse(52.0, 40.0, 10.6, 10.6)
        keep = poly([(52, 24), (68, 24), (68, 33), (58, 31), (52, 29)])
    elif kind == 2:
        outer, inner = ellipse(53.5, 38.5, 13.0, 12.0), ellipse(51.5, 39.5, 12.0, 11.8)
        keep = poly([(56, 24), (70, 24), (70, 37), (64, 36), (58, 30)])
    else:
        outer, inner = ellipse(52.5, 37.5, 13.2, 12.0), ellipse(50.5, 37.5, 12.4, 11.6)
        keep = poly([(62, 30), (70, 30), (70, 43), (64, 43)])
    m = outer & ~inner & keep & (cel.c == '.')
    cel.c[m] = 'A'
    cel.c[m & ~shift(m, 0, 2)] = 'a'


def front(pose=0, eye='open', hat=False, mouth=None):
    """Standing, facing the viewer. pose indexes SWIPE."""
    cel = Cel()
    g = STAND_GROUND
    p = SWIPE[pose]
    tail(cel, [(31.0, 55.6, 3.4), (23.0, 57.4, 4.3), (14.5, 56.4, 4.5), (8.6, 51.3, 4.1), (5.6, 45.2, 3.0)])
    torso, _ = tube([(39.5, 35.5, 8.6), (39.5, 44.0, 9.8), (39.5, 50.6, 10.6)])
    cel.part(torso, 'F', sep=None)
    cel.c[left_band(torso, 2)] = 'H'
    cel.c[right_band(torso, 2)] = 'S'
    cel.c[jag(torso, bottom_band, [2, 3])] = 'S'
    belly = ellipse(40.0, 46.5, 5.8, 9.2) & torso
    cel.c[belly] = 'L'
    cel.c[right_band(belly, 1) | bottom_band(belly, 1)] = 'H'
    for side_, cx in ((-1, 31.2), (1, 47.8)):
        thigh = ellipse(cx, 54.3, 5.2, 6.0)
        cel.part(thigh, 'F')
        cel.c[(left_band(thigh, 2) if side_ < 0 else top_band(thigh, 1)) & thigh] = 'H'
        if side_ > 0:
            cel.c[right_band(thigh, 2)] = 'S'
        _paw(cel, cx - 4.6, g - 3.2, cx + 4.6, g)
    _arm(cel, (33.2, 37.5), p['l'], bend=-0.6)
    _arm(cel, (45.8, 37.5), p['r'])
    hx, hy = 27, 9
    cel.stamp(HEAD_FRONT, hx, hy, soft=True)
    for ex, ey in EYES_FRONT:
        _eye(cel, hx + ex, hy + ey, eye)
    if mouth == 'o' or pose == 5:
        cel.stamp(['KK', 'PP'], hx + 12, hy + 18)
    if hat:
        cel.stamp(HAT_BACK, hx + 5, hy - 7)
    if p.get('arc'):
        _arc(cel, p['arc'])
    cel.outline()
    return cel


# ---------------------------------------------------------------------------
# back pose: climbing
# ---------------------------------------------------------------------------
CLIMB_FEET = 50   # row of the cell the game pins to the shelf while climbing


def back(i=0, hat=False):
    cel = Cel()
    up = round(3 * math.sin(2 * math.pi * i / 6))
    for sx, s_ in ((-1, 1), (1, -1)):
        d = up * s_
        hand = (39.5 + sx * 13.2, 15.5 - d)
        m, _ = tube([(39.5 + sx * 7.0, 28.0, 3.2), (39.5 + sx * 12.6, 23.5 - d * 0.5, 2.8), (hand[0], hand[1] + 1.5, 2.4)])
        cel.c[m] = 'F'
        cel.c[(left_band(m, 1) if sx < 0 else right_band(m, 1))] = 'S' if sx > 0 else 'H'
        _hand(cel, hand[0], hand[1], 2.4)
        foot = (39.5 + sx * 11.6, 48.6 + d * 0.7)
        m, _ = tube([(39.5 + sx * 5.5, 42.0, 3.8), (39.5 + sx * 10.6, 44.5 + d * 0.5, 3.2), (foot[0], foot[1] - 1.0, 2.6)])
        cel.c[m] = 'F'
        cel.c[bottom_band(m, 1)] = 'S'
        _hand(cel, foot[0] + sx * 0.4, foot[1], 2.5)
    body, _ = tube([(39.5, 27.5, 8.2), (39.5, 35.5, 9.6), (39.5, 41.0, 10.0)])
    cel.part(body, 'F')
    cel.c[jag(body, top_band, HI) | left_band(body, 2)] = 'H'
    cel.c[right_band(body, 2) | jag(body, bottom_band, [2, 3, 3])] = 'S'
    for y in range(31, 44, 3):                      # a broken line down the spine
        cel.c[y, 39] = 'S'
        cel.c[y + 1, 40] = 'S'
    sw = round(3 * math.sin(2 * math.pi * (i - 1) / 6))
    tail(cel, [(39.5, 46.0, 3.4), (39.5 + sw * 0.25, 51.5, 4.4), (39.5 + sw * 0.7, 57.0, 4.3), (39.5 + sw, 61.2, 3.0)], behind=False)
    hx, hy = 30, 10
    cel.stamp(HEAD_BACK, hx, hy, soft=True)
    if hat:
        cel.stamp(HAT_BACK, hx + 2, hy - 7)
    cel.outline()
    return cel


# ---------------------------------------------------------------------------
# flat on its back: knocked out / asleep
# ---------------------------------------------------------------------------
def lying(eye='ko', hat=False, tongue=True):
    cel = Cel()
    tail(cel, [(21.5, 46.2, 3.4), (14.0, 47.0, 3.8), (6.6, 47.4, 3.1)])
    for (tx, ty), (kx, ky) in (((31.5, 36.5), (33.0, 30.6)), ((47.5, 38.5), (50.5, 34.2))):
        m, _ = tube([(tx, ty, 2.5), (kx, ky, 1.9)], smooth=False)
        cel.c[m] = 'S'
        _hand(cel, kx + 0.3, ky - 1.2, 2.0)
    body, _ = tube([(29.0, 42.0, 8.5), (44.5, 42.4, 8.2)], smooth=False)
    cel.part(body, 'F', sep=None)
    belly = jag(body, top_band, [4, 5, 5, 4, 5])
    cel.c[belly] = 'L'
    cel.c[shift(belly, 0, 1) & body & (cel.c == 'F')] = 'H'
    cel.c[jag(body, bottom_band, [2, 2, 3])] = 'S'
    for (tx, ty), (kx, ky) in (((26.0, 37.5), (23.4, 31.0)), ((42.5, 37.5), (44.4, 32.0))):
        m, _ = tube([(tx, ty, 2.8), (kx, ky, 2.0)], smooth=False)
        cel.part(m, 'F')
        cel.c[left_band(m, 1) & (cel.c == 'F')] = 'H'
        _hand(cel, kx - 0.2, ky - 1.3, 2.1)
    hx, hy = 52, 31
    neck = ellipse(hx + 3.0, hy + 9.0, 5.5, 6.0)
    cel.c[neck & (cel.c == '.')] = 'F'
    cel.stamp(HEAD_SIDE, hx, hy, flipy=True, soft=True)
    ex, ey = hx + EYE_SIDE[0], hy + len(HEAD_SIDE) - EYE_SIDE[1] - 2
    if eye == 'ko':
        cel.stamp(['MM', 'MM'], ex, ey)
        _eye(cel, ex, ey + 1, 'ko')
    else:
        cel.stamp(['mm', 'MM'], ex, ey)
    if tongue:
        cel.stamp(['.p', 'PP'], hx + 18, hy + 2)
    if hat:
        cel.stamp(HAT_SIDE, 14, 20)
    cel.outline()
    return cel


# ---------------------------------------------------------------------------
# sprite sheet
# ---------------------------------------------------------------------------
ROWS = ['walk', 'climb', 'drink', 'swipe']
SHEET_ROWS = ROWS + ['extra']     # extra: 0 blink, 1 knocked out, 2 asleep


def frames(hat=False):
    """The game's 5 rows of 6 cells, as Cel objects (None = empty cell)."""
    out = [side(i / 6, hat=hat) for i in range(6)]
    out += [back(i, hat=hat) for i in range(6)]
    out += [side(mode='drink', lick=i, hat=hat) for i in range(6)]
    out += [front(i, hat=hat) for i in range(6)]
    out += [side(0, eye='closed', hat=hat), lying('ko', hat=hat), lying('closed', hat=hat, tongue=False), None, None, None]
    return out


def sheet():
    cells = frames(False) + frames(True)
    im = Image.new('RGBA', (6 * CW, 10 * CH), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        if c is not None:
            im.alpha_composite(c.image(), ((i % 6) * CW, (i // 6) * CH))
    return im, cells


def sheet_preview(scale=3, bg=(70, 78, 78, 255)):
    im, _ = sheet()
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out.resize((im.width * scale, im.height * scale), Image.NEAREST)


# ---------------------------------------------------------------------------
# stand-alone pieces for the rest of the site and the merch
# ---------------------------------------------------------------------------
def rows_image(rows):
    cel = Cel(max(len(r) for r in rows), len(rows))
    cel.stamp(rows, 0, 0)
    return cel.image()


def hat(kind='side'):
    return rows_image(HAT_SIDE if kind == 'side' else HAT_BACK)


FACE_HAT_RISE = 7     # rows the hat adds above the head

# The same face at icon size (nav, favicon, small repeats on merch). 18 x 14.
FACE_SMALL = [
    '.KKK..........KKK.',
    'KWMWK........KWMWK',
    'KWMMSKKKKKKKKSMMWK',
    'KFSFHHHHSSHHHHFSFK',
    'KFFHHHHFSSFHHHHFFK',
    'KWWWWWWFSSFWWWWWWK',
    'KMMMMEGMSSMEGMMMMK',
    'KMMMMEEMWWMEEMMMMK',
    'KLMMMMWWWWWWMMMMLK',
    '.KLMMWWNNNNWWMMLK.',
    '.KLLWWWWNNWWWWLLK.',
    '..KLWWWKWWKWWWLK..',
    '...KLLWWWWWWLLK...',
    '....KKKKKKKKKK....',
]
HAT_SMALL = [
    '..kkk..........',
    '.kYYYk.kkkk....',
    'kYYYykkRRRRk...',
    'kyyykRRRRRRrk..',
    '.kkkRRRhRRRRrk.',
    '...kRRRRRRRRrk.',
    '..kRRRRRRRRRRrk',
    '.kYYYYYYYYYYYYk',
    '.kYYYYYYYYYYYYk',
    '.kyyyyyyyyyyyyk',
]


def face_cel(santa=True, eye='open', small=False):
    head, hat_rows, hat_x = (FACE_SMALL, HAT_SMALL, 2) if small else (HEAD_FRONT, HAT_BACK, 5)
    top = FACE_HAT_RISE if santa else 0
    cel = Cel(len(head[0]), len(head) + top)
    cel.stamp(head, 0, top)
    if not small:
        for ex, ey in EYES_FRONT:
            _eye(cel, ex, top + ey, eye)
    if santa:
        cel.stamp(hat_rows, hat_x, 0)
    return cel


def face(santa=True, eye='open', small=False):
    """The brand mark: the front-facing head exactly as it appears in the game
    (small=True: the same face redrawn at icon size)."""
    return face_cel(santa, eye, small).image()


def pose(cel):
    """Image of a pose, cropped to its pixels."""
    im = cel.image()
    return im.crop(im.getbbox())
