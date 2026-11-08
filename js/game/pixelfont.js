// 3x5 pixel font for text drawn inside the game world (score popups, signs).
// Text is rendered once per (string, colour, scale) into a tiny outlined canvas
// and then blitted with nearest-neighbour scaling, so it stays perfectly crisp.

import { makeCanvas } from './assets.js';

const G = {
  A: '010101111101101', B: '110101110101110', C: '011100100100011', D: '110101101101110',
  E: '111100110100111', F: '111100110100100', G: '011100101101011', H: '101101111101101',
  I: '111010010010111', J: '001001001101010', K: '101101110101101', L: '100100100100111',
  M: '101111111101101', N: '110101101101101', O: '010101101101010', P: '110101110100100',
  Q: '010101101110011', R: '110101110101101', S: '011100010001110', T: '111010010010010',
  U: '101101101101111', V: '101101101101010', W: '101101111111101', X: '101101010101101',
  Y: '101101010010010', Z: '111001010100111',
  0: '111101101101111', 1: '010110010010111', 2: '110001010100111', 3: '110001010001110',
  4: '101101111001001', 5: '111100110001110', 6: '011100111101111', 7: '111001010010010',
  8: '111101111101111', 9: '111101111001110',
  '+': '000010111010000', '-': '000000111000000', x: '000101010101000', '!': '010010010000010',
  '.': '000000000000010', ':': '000010000010000', '%': '101001010100101', '?': '110001010000010',
  "'": '010010000000000', ' ': '000000000000000', '/': '001001010100100', '♥': '000101111111010',
};

const cache = new Map();

export function textWidth(str) {
  return str.length * 4 - 1;
}

/**
 * Returns an offscreen canvas holding `str` in `color` with a 1px dark outline.
 * `scale` multiplies glyph pixels (1 = 3x5 glyphs, 2 = 6x10 chunky glyphs).
 */
export function renderText(str, color, scale = 1, outline = '#1a120c') {
  const key = `${str}|${color}|${scale}|${outline}`;
  let c = cache.get(key);
  if (c) return c;
  const w = textWidth(str) * scale + 2;
  const h = 5 * scale + 2;
  c = makeCanvas(w, h);
  const g = c.getContext('2d');
  const draw = (ox, oy, col) => {
    g.fillStyle = col;
    let x = 1;
    for (const ch of str) {
      const bits = G[ch] ?? G[ch.toUpperCase()] ?? G[' '];
      for (let i = 0; i < 15; i++) {
        if (bits[i] === '1') g.fillRect(x + (i % 3) * scale + ox, 1 + Math.floor(i / 3) * scale + oy, scale, scale);
      }
      x += 4 * scale;
    }
  };
  if (outline) {
    for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [1, 1]]) draw(dx, dy, outline);
  }
  draw(0, 0, color);
  cache.set(key, c);
  if (cache.size > 300) cache.delete(cache.keys().next().value);
  return c;
}
