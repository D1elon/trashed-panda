// Loads sprite sheets and derives what the renderer needs from the pixels themselves
// (mirrored raccoon frames, per-frame foot rows) so art changes never need code changes.

import { SPRITES } from './sprite-data.js';

const BASE = new URL('../../assets/game/', import.meta.url);

function loadImage(name) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load ${name}`));
    img.src = new URL(name, BASE).href;
  });
}

function makeCanvas(w, h) {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

/** Mirror every cell of a grid sheet in place (so cell (c, r) is the flipped frame). */
function mirrorCells(img, cw, ch) {
  const c = makeCanvas(img.width, img.height);
  const g = c.getContext('2d');
  const cols = Math.round(img.width / cw);
  const rows = Math.round(img.height / ch);
  for (let r = 0; r < rows; r++) {
    for (let col = 0; col < cols; col++) {
      g.save();
      g.translate(col * cw + cw, r * ch);
      g.scale(-1, 1);
      g.drawImage(img, col * cw, r * ch, cw, ch, 0, 0, cw, ch);
      g.restore();
    }
  }
  return c;
}

/** Bottom-most opaque row of every cell. */
function measureFeet(img, cw, ch) {
  const c = makeCanvas(img.width, img.height);
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  const data = g.getImageData(0, 0, img.width, img.height).data;
  const cols = Math.round(img.width / cw);
  const rows = Math.round(img.height / ch);
  const feet = [];
  for (let r = 0; r < rows; r++) {
    for (let col = 0; col < cols; col++) {
      let bottom = -1;
      for (let y = ch - 1; y >= 0 && bottom < 0; y--) {
        const row = (r * ch + y) * img.width;
        for (let x = 0; x < cw; x++) {
          if (data[(row + col * cw + x) * 4 + 3] > 0) {
            bottom = y;
            break;
          }
        }
      }
      feet.push(bottom < 0 ? ch - 1 : bottom);
    }
  }
  return feet;
}

export async function loadAssets() {
  const [raccoon, bottles, store, tile, bathroom] = await Promise.all([
    loadImage('raccoon.png'),
    loadImage('bottles.png'),
    loadImage('store.png'),
    loadImage('ceiling-tile.png'),
    loadImage('bathroom.png'),
  ]);
  const R = SPRITES.raccoon;
  return {
    raccoon,
    raccoonFlip: mirrorCells(raccoon, R.w, R.h),
    raccoonFeet: measureFeet(raccoon, R.w, R.h),
    bottles,
    store,
    tile,
    bathroom,
  };
}

export { makeCanvas };
