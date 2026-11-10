// Canvas renderer. Everything is drawn at an integer multiple of the art pixel grid
// in *device* pixels, so pixels stay perfectly square and crisp on every screen.
// Sprite positions are rounded to device pixels (not art pixels) so motion and the
// camera stay smooth.

import { WORLD } from './world-data.js';
import { SPRITES } from './sprite-data.js';
import { KINDS, SWIPE_TIME } from './config.js';
import { renderText, textWidth } from './pixelfont.js';
import { makeCanvas } from './assets.js';

const RW = SPRITES.raccoon.w;
const RH = SPRITES.raccoon.h;
const BW = SPRITES.bottles.w;
const BH = SPRITES.bottles.h;
const ROW = { walk: 0, climb: 1, drink: 2, swipe: 3, extra: 4 };
const SANTA_ROWS = SPRITES.raccoon.santaRowOffset;
const SPIN0 = SPRITES.bottles.spinStart;
const RACCOON_CX = SPRITES.raccoon.cx;            // body centre inside the cell
const CLIMB_FEET = SPRITES.raccoon.climbFeet;    // anchor row for the back-view climbing frames
const FLOOR = WORLD.floorLane;

const BULBS = [
  ['#ff5a52', '#6e2222'], ['#ffd25a', '#6e5418'], ['#58e08a', '#1d5233'],
  ['#6cb2ff', '#213f6b'], ['#ff9ad0', '#6b2d4e'],
];
const SHARDS = {
  vodka: ['#e4f5ff', '#8cc6ec', '#ffffff'], whiskey: ['#f6bd62', '#a3561a', '#ffe0a3'],
  wine: ['#4b7a32', '#c43049', '#2c4a20'], tequila: ['#eef5d6', '#b5cf68', '#ffffff'],
  reserve: ['#ff6f63', '#ffd36b', '#fff1c2'],
};
const POP_COLORS = { smash: '#fff4dc', drink: '#8ef0a8', combo: '#ffc24a', bonus: '#ffd36b', tier: '#ff9ad0', bad: '#ff6b6b' };

export class Renderer {
  constructor(canvas, sim, bus, assets, settings) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d', { alpha: false });
    this.sim = sim;
    this.bus = bus;
    this.a = assets;
    this.settings = settings;
    this.buffer = makeCanvas(1, 1);
    this.bctx = this.buffer.getContext('2d', { alpha: false });
    this.s = 4;
    this.w = 1;
    this.h = 1;
    this.viewW = 200;
    this.viewH = 200;
    this.cam = { x: 0, y: WORLD.h - 200 };
    this.time = 0;
    this.particles = [];
    this.popups = [];
    this.snow = [];
    this.snowAcc = 0;
    this.snowPile = 0;
    this.tile = null;
    this.tileIntact = true;
    this.shakeT = 0;
    this.shakeDur = 0.0001;
    this.shakeAmp = 0;
    this.flash = 0;
    this.blinkT = 0;
    this.nextBlink = 2.5;
    this.zzzAcc = 0;
    this.subscribe();
  }

  // ---------------------------------------------------------------- sizing
  resize() {
    const rect = this.canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const w = Math.max(1, Math.round(rect.width * dpr));
    const h = Math.max(1, Math.round(rect.height * dpr));
    if (w === this.w && h === this.h) return;
    this.canvas.width = w;
    this.canvas.height = h;
    this.buffer.width = w;
    this.buffer.height = h;
    this.w = w;
    this.h = h;
    this.s = chooseScale(w, h);
    this.viewW = w / this.s;
    this.viewH = h / this.s;
    for (const c of [this.ctx, this.bctx]) c.imageSmoothingEnabled = false;
    this.snapCamera();
  }

  // ---------------------------------------------------------------- events
  subscribe() {
    const b = this.bus;
    b.on('start', () => {
      this.particles.length = 0;
      this.popups.length = 0;
      this.snow.length = 0;
      this.snowPile = 0;
      this.tileIntact = false;
      const hole = WORLD.hole;
      this.tile = { x: hole.x, y: hole.y, vy: 60 };
      this.snapCamera(true);
    });
    b.on('phase', (p) => {
      if (p === 'title') {
        this.tileIntact = true;
        this.tile = null;
        this.snow.length = 0;
        this.snowPile = 0;
      }
    });
    b.on('land', ({ x, y, hard, intro }) => {
      this.dust(x, y, intro ? 14 : hard ? 9 : 4);
      if (hard) this.addShake(intro ? 3 : 2, 0.22);
    });
    b.on('break', ({ x, y, kind }) => {
      const cols = SHARDS[kind];
      const liquid = KINDS[kind].color;
      for (let i = 0; i < 9; i++) {
        this.particles.push({
          x: x + rand(-4, 4), y: y - rand(2, 8), vx: rand(-70, 70), vy: rand(-110, -40), g: 520,
          life: rand(0.5, 0.9), color: cols[i % cols.length], size: 1, floor: y + rand(0, 3), bounce: true,
        });
      }
      for (let i = 0; i < 7; i++) {
        this.particles.push({
          x: x + rand(-3, 3), y: y - 3, vx: rand(-55, 55), vy: rand(-140, -60), g: 600,
          life: rand(0.35, 0.6), color: liquid, size: i % 3 === 0 ? 2 : 1, floor: y + 1,
        });
      }
      if (kind === 'reserve') {
        this.flash = 0.18;
        this.sparkles(x, y - 10, 14);
      }
      this.addShake(1.2, 0.12);
    });
    b.on('score', ({ points, combo, x, y, kind }) => {
      const text = `+${points}`;
      this.popup(x, y, text, kind === 'drink' ? POP_COLORS.drink : POP_COLORS.smash, 1);
      if (combo > 1) this.popup(x, y - 8, `x${combo}`, POP_COLORS.combo, 1, 0.05);
    });
    b.on('combo', ({ chain }) => {
      if (chain === 3 || chain === 5 || chain % 5 === 0) {
        const r = this.sim.r;
        this.popups = this.popups.filter((p) => !p.combo);
        this.popup(r.x, r.y - 52, chain >= 5 ? `${chain} COMBO!` : `COMBO x${chain}`, POP_COLORS.combo, 2);
        this.popups[this.popups.length - 1].combo = true;
      }
    });
    b.on('timeBonus', ({ seconds, x, y }) => {
      this.popup(x, y - 12, `+${seconds} SEC`, POP_COLORS.bonus, 2);
    });
    b.on('buzzTier', ({ name, up }) => {
      if (!up) return;
      const r = this.sim.r;
      this.popup(r.x, r.y - 60, name.toUpperCase() + '!', POP_COLORS.tier, 1);
    });
    b.on('blackout', ({ x, y }) => {
      this.popups = this.popups.filter((p) => p.color !== POP_COLORS.tier);
      this.popup(x, y - 56, 'BLACKOUT!', POP_COLORS.bad, 2);
      for (let i = 0; i < 8; i++) {
        this.particles.push({ x, y: y - 30, vx: rand(-60, 60), vy: rand(-90, -30), g: 200, life: 0.8, color: '#ffd34a', shape: 'cross' });
      }
      this.addShake(2.5, 0.3);
    });
    b.on('slip', ({ x, y }) => this.popup(x, y - 48, 'WHOA!', POP_COLORS.bad, 1));
    b.on('restock', ({ unit }) => {
      const x0 = WORLD.shelf.xs[unit];
      for (let i = 0; i < 26; i++) {
        const lv = i % WORLD.shelf.boardTops.length;
        this.particles.push({ x: x0 + 12 + Math.random() * (WORLD.shelf.w - 24), y: WORLD.shelf.boardTops[lv] - rand(4, 30), vx: rand(-12, 12), vy: rand(-30, -8), g: 0, life: rand(0.4, 0.9), color: i % 2 ? '#fff1c2' : '#9fe0ff', shape: 'cross' });
      }
      const r = this.sim.r;
      const cx = clamp(x0 + WORLD.shelf.w / 2, this.cam.x + 40, this.cam.x + this.viewW - 40);
      this.popup(cx, Math.min(r.y - 58, WORLD.shelf.boardTops[2]), 'RESTOCKED!', '#9fe0ff', 2);
    });
    b.on('swipe', ({ hits, x, y }) => {
      if (hits === 0) {
        for (let i = 0; i < 3; i++) this.particles.push({ x: x + rand(-4, 4), y: y - rand(10, 24), vx: this.sim.r.facing * rand(40, 70), vy: 0, g: 0, life: 0.18, color: '#f4efe6', size: 1 });
      }
    });
  }

  addShake(amp, dur) {
    if (!this.settings.screenShake) return;
    if (amp >= this.shakeAmp * (this.shakeT / this.shakeDur)) {
      this.shakeAmp = amp;
      this.shakeDur = dur;
      this.shakeT = dur;
    }
  }

  popup(x, y, text, color, scale, delay = 0) {
    this.popups.push({ x, y, text, color, scale, life: 0.95 + delay, max: 0.95 + delay, delay });
  }

  dust(x, y, n) {
    for (let i = 0; i < n; i++) {
      this.particles.push({
        x: x + rand(-14, 14), y: y - rand(0, 3), vx: rand(-45, 45), vy: rand(-28, -6), g: 30, drag: 3,
        life: rand(0.35, 0.65), color: i % 2 ? '#d9d2c3' : '#bfb6a5', size: i % 3 === 0 ? 2 : 1,
      });
    }
  }

  sparkles(x, y, n) {
    for (let i = 0; i < n; i++) {
      this.particles.push({ x: x + rand(-10, 10), y: y + rand(-10, 10), vx: rand(-30, 30), vy: rand(-50, 0), g: 40, life: rand(0.4, 0.8), color: i % 2 ? '#fff1c2' : '#ffd36b', shape: 'cross' });
    }
  }

  // ---------------------------------------------------------------- camera
  cameraTarget() {
    const sim = this.sim;
    const r = sim.r;
    const W = WORLD.w;
    const H = WORLD.h;
    let tx;
    let ty;
    if (sim.phase === 'title' || !r.visible) {
      const span = Math.max(0, W - this.viewW);
      tx = span * (0.5 + 0.5 * Math.sin(this.time * 0.09 - Math.PI / 2));
      ty = H - this.viewH;
    } else {
      tx = r.x - this.viewW / 2 + r.facing * this.viewW * 0.08;
      ty = r.y - this.viewH * 0.68;
    }
    tx = this.viewW >= W ? (W - this.viewW) / 2 : clamp(tx, 0, W - this.viewW);
    ty = this.viewH >= H ? H - this.viewH : clamp(ty, 0, H - this.viewH);
    return { tx, ty };
  }

  snapCamera(force) {
    const { tx, ty } = this.cameraTarget();
    if (force || !Number.isFinite(this.cam.x)) {
      this.cam.x = tx;
      this.cam.y = ty;
    } else {
      this.cam.x = tx;
      this.cam.y = ty;
    }
  }

  updateCamera(dt) {
    const { tx, ty } = this.cameraTarget();
    const k = 1 - Math.exp(-dt * (this.sim.phase === 'title' ? 20 : 7));
    this.cam.x += (tx - this.cam.x) * k;
    this.cam.y += (ty - this.cam.y) * k;
  }

  // ---------------------------------------------------------------- frame
  render(dt) {
    const sim = this.sim;
    const paused = sim.phase === 'paused';
    this.time += dt;
    if (!paused) {
      this.updateParticles(dt);
      this.updateSnow(dt);
      this.updateTile(dt);
      this.shakeT = Math.max(0, this.shakeT - dt);
      this.flash = Math.max(0, this.flash - dt);
    }
    this.updateCamera(dt);

    const buzz = sim.buzz;
    const fx = this.settings.drunkFx && sim.active && buzz >= 40;
    const g = fx ? this.bctx : this.ctx;
    const s = this.s;
    let shx = 0;
    let shy = 0;
    if (this.shakeT > 0) {
      const a = this.shakeAmp * (this.shakeT / this.shakeDur) * s;
      shx = Math.round(rand(-a, a));
      shy = Math.round(rand(-a, a));
    }
    this.ox = Math.round(this.cam.x * s) - shx;
    this.oy = Math.round(this.cam.y * s) - shy;

    g.fillStyle = '#141010';
    g.fillRect(0, 0, this.w, this.h);
    this.drawStore(g);
    this.drawBulbs(g);
    this.drawSnowPile(g);
    this.drawShelfBottles(g);
    this.drawPuddles(g);
    if (sim.r.visible) this.drawRaccoon(g, dt);
    this.drawLooseBottles(g);
    this.drawTile(g);
    this.drawParticles(g);
    this.drawSnow(g);
    this.drawPopups(g, dt, paused);

    if (fx) this.composeDrunk(buzz);
    const ctx = this.ctx;
    if (sim.r.koT > 0 && sim.phase === 'playing') {
      ctx.fillStyle = 'rgba(12, 6, 24, 0.38)';
      ctx.fillRect(0, 0, this.w, this.h);
    }
    if (this.settings.drunkFx && buzz > 60 && sim.active) {
      ctx.fillStyle = `rgba(190, 70, 200, ${(((buzz - 60) / 40) * 0.08).toFixed(3)})`;
      ctx.fillRect(0, 0, this.w, this.h);
    }
    if (this.flash > 0) {
      ctx.fillStyle = `rgba(255, 236, 170, ${(this.flash * 1.6).toFixed(3)})`;
      ctx.fillRect(0, 0, this.w, this.h);
    }
  }

  X(wx) {
    return Math.round(wx * this.s) - this.ox;
  }

  Y(wy) {
    return Math.round(wy * this.s) - this.oy;
  }

  blit(g, img, sx, sy, sw, sh, wx, wy) {
    const s = this.s;
    g.drawImage(img, sx, sy, sw, sh, this.X(wx), this.Y(wy), sw * s, sh * s);
  }

  px(g, wx, wy, w, h, color) {
    g.fillStyle = color;
    g.fillRect(this.X(wx), this.Y(wy), w * this.s, h * this.s);
  }

  drawStore(g) {
    const W = WORLD.w;
    const H = WORLD.h;
    const x0 = clamp(Math.floor(this.cam.x) - 1, 0, W);
    const y0 = clamp(Math.floor(this.cam.y) - 1, 0, H);
    const x1 = clamp(Math.ceil(this.cam.x + this.viewW) + 2, 0, W);
    const y1 = clamp(Math.ceil(this.cam.y + this.viewH) + 2, 0, H);
    if (x1 > x0 && y1 > y0) this.blit(g, this.a.store, x0, y0, x1 - x0, y1 - y0, x0, y0);
  }

  drawBulbs(g) {
    const t = this.time * (this.settings.reducedMotion ? 0.35 : 1);
    const { garland, shelf, tree } = WORLD.bulbs;
    const s = this.s;
    const bulb = (b, i, size, phase) => {
      const [on, off] = BULBS[(i + phase) % BULBS.length];
      const lit = Math.sin(t * 2.1 + i * 1.37) + Math.sin(t * 0.63 + i * 0.71) > -0.7;
      const bx = b.x - (size >> 1);
      if (lit) {
        g.globalAlpha = 0.2;
        g.fillStyle = on;
        g.fillRect(this.X(bx - 1), this.Y(b.y - 1), (size + 2) * s, (size + 3) * s);
        g.globalAlpha = 1;
      }
      this.px(g, bx, b.y, size, size + 1, lit ? on : off);
      if (lit) this.px(g, bx, b.y, 1, 1, '#fffbe8');
    };
    garland.forEach((b, i) => bulb(b, i, 1, 0));
    shelf.forEach((b, i) => bulb(b, i, 2, 2));
    tree.forEach((b, i) => {
      const c = BULBS[i % BULBS.length];
      this.px(g, b.x - 1, b.y - 1, 3, 3, '#14301d');
      this.px(g, b.x, b.y, 2, 2, c[0]);
      const lit = Math.sin(t * 3 + i * 2.3) > 0.2;
      if (lit) this.px(g, b.x, b.y, 1, 1, '#fffbe8');
    });
    // star glow on the tree
    const tw = (Math.sin(t * 2.5) + 1) / 2;
    g.globalAlpha = 0.18 + tw * 0.2;
    this.px(g, WORLD.tree.x - 4, WORLD.tree.base - 102, 9, 9, '#ffe9a0');
    g.globalAlpha = 1;
  }

  drawShelfBottles(g) {
    const img = this.a.bottles;
    for (const b of this.sim.bottles) {
      if (b.state !== 'shelf') continue;
      const row = KINDS[b.kind].index;
      const dx = b.wobble > 0 ? (Math.floor(b.wobble * 40) % 2 ? 1 : -1) : 0;
      this.blit(g, img, 0, row * BH, BW, BH, b.x - BW / 2 + dx, b.y + 1 - BH);
      if (b.kind === 'reserve') this.drawReserveSparkle(g, b);
    }
  }

  drawReserveSparkle(g, b) {
    const cycle = (this.time + b.id * 0.37) % 1.1;
    if (cycle > 0.36) return;
    const spots = [[-5, -24], [4, -14], [-3, -8], [5, -27]];
    const [sx, sy] = spots[Math.floor((this.time + b.id) / 1.1) % spots.length];
    const big = cycle > 0.1 && cycle < 0.26;
    const cx = b.x + sx;
    const cy = b.y + sy;
    this.px(g, cx, cy, 1, 1, '#ffffff');
    if (big) {
      this.px(g, cx - 1, cy, 1, 1, '#ffd36b');
      this.px(g, cx + 1, cy, 1, 1, '#ffd36b');
      this.px(g, cx, cy - 1, 1, 1, '#ffd36b');
      this.px(g, cx, cy + 1, 1, 1, '#ffd36b');
    }
  }

  drawPuddles(g) {
    const img = this.a.bottles;
    for (const p of this.sim.puddles) {
      const row = KINDS[p.kind].index;
      const f = p.draining ? 1 - p.drainT : 1;
      const w = Math.max(2, Math.round(BW * f));
      const sx = Math.round((BW - w) / 2);
      this.blit(g, img, 5 * BW + sx, row * BH, w, BH, p.x - BW / 2 + sx, p.y + 2 - BH);
      if (p.kind === 'reserve' && !p.draining) this.drawReserveSparkle(g, { x: p.x, y: p.y + 18, id: p.id });
    }
  }

  drawLooseBottles(g) {
    const img = this.a.bottles;
    for (const b of this.sim.bottles) {
      const row = KINDS[b.kind].index;
      if (b.state === 'falling') {
        const idx = ((Math.round(b.angle / (Math.PI / 4)) % 8) + 8) % 8;
        this.blit(g, img, (SPIN0 + idx) * BW, row * BH, BW, BH, b.x - BW / 2, b.y - 15 - BH / 2);
      } else if (b.state === 'breaking') {
        this.blit(g, img, (2 + b.frame) * BW, row * BH, BW, BH, b.x - BW / 2, b.y + 1 - BH);
      }
    }
  }

  raccoonFrame() {
    const sim = this.sim;
    const r = sim.r;
    if ((r.koT > 0 && !r.falling) || (sim.phase === 'ending' && !r.falling) || sim.phase === 'gameover') return [ROW.extra, 1];
    if (r.falling || sim.phase === 'dropping') return [ROW.swipe, Math.floor(r.anim / 0.08) % 2 ? 2 : 5];
    if (r.climb) return [ROW.climb, Math.min(5, Math.floor(r.climb.t * 6))];
    if (r.swipeT > 0) {
      const k = Math.min(3, Math.floor(((SWIPE_TIME - r.swipeT) / SWIPE_TIME) * 4));
      return [ROW.swipe, [1, 2, 3, 4][k]];
    }
    if (r.drinkT > 0) return [ROW.drink, Math.floor(r.anim / 0.1) % 6];
    if (r.stumbleT > 0) return [ROW.swipe, 0];
    if (r.moving) return [ROW.walk, Math.floor(r.anim / 0.095) % 6];
    if (this.blinkT > 0) return [ROW.extra, 0];
    return [ROW.walk, 0];
  }

  drawRaccoon(g, dt) {
    const sim = this.sim;
    const r = sim.r;
    // idle blink timer
    this.nextBlink -= dt;
    if (this.nextBlink <= 0) {
      this.blinkT = 0.13;
      this.nextBlink = rand(2.2, 4.5);
    }
    this.blinkT = Math.max(0, this.blinkT - dt);

    const [row, col] = this.raccoonFrame();
    const sheetRow = row + (this.settings.santa ? SANTA_ROWS : 0);
    const feet = row === ROW.climb ? CLIMB_FEET : this.a.raccoonFeet[sheetRow * 6 + col];
    const flip = r.facing < 0;
    const img = flip ? this.a.raccoonFlip : this.a.raccoon;
    const left = r.x - (flip ? RW - RACCOON_CX : RACCOON_CX);
    const top = Math.round(r.y) - feet;

    // contact shadow
    const groundY = r.level >= 0 ? WORLD.shelf.boardTops[r.level] : FLOOR;
    const lift = Math.max(0, groundY - r.y);
    if (sim.phase !== 'dropping' || r.y > FLOOR - 120) {
      const w = Math.max(6, Math.round(26 - lift * 0.12));
      g.globalAlpha = 0.18;
      this.px(g, Math.round(r.x - w / 2), groundY - 1, w, 2, '#000');
      this.px(g, Math.round(r.x - w / 2) + 3, groundY - 2, w - 6, 1, '#000');
      g.globalAlpha = 1;
    }
    this.blit(g, img, col * RW, sheetRow * RH, RW, RH, Math.round(left), top);

    // drunk / KO flourishes around the head
    const ko = row === ROW.extra && col === 1;
    const headX = ko ? r.x + r.facing * 23 : r.x + r.facing * (row === ROW.swipe ? 1 : 21);
    const headY = ko ? r.y - 16 : r.y - (row === ROW.swipe ? 46 : 30);
    if (ko || (sim.buzz >= 60 && sim.active)) {
      const n = ko ? 3 : sim.buzz >= 80 ? 3 : 2;
      for (let i = 0; i < n; i++) {
        const a = this.time * 3.2 + (i * Math.PI * 2) / n;
        const sx = Math.round(headX + Math.cos(a) * 9);
        const sy = Math.round(headY - 6 + Math.sin(a) * 2.5);
        this.px(g, sx, sy, 1, 1, '#fff3b0');
        this.px(g, sx - 1, sy, 1, 1, '#ffd34a');
        this.px(g, sx + 1, sy, 1, 1, '#ffd34a');
        this.px(g, sx, sy - 1, 1, 1, '#ffd34a');
        this.px(g, sx, sy + 1, 1, 1, '#ffd34a');
      }
    }
    if (ko && sim.phase !== 'paused') {
      this.zzzAcc += dt;
      if (this.zzzAcc > 0.55) {
        this.zzzAcc = 0;
        this.popups.push({ x: headX + 6, y: headY - 10, text: 'Z', color: '#e8eef8', scale: 1, life: 1.2, max: 1.2, delay: 0, drift: 8 });
      }
    }
  }

  drawTile(g) {
    const hole = WORLD.hole;
    if (this.tileIntact) this.blit(g, this.a.tile, 0, 0, hole.w, hole.h, hole.x, hole.y);
    if (this.tile) {
      const wob = Math.round(Math.sin(this.time * 30));
      this.blit(g, this.a.tile, 0, 0, hole.w, hole.h, this.tile.x + wob, Math.round(this.tile.y));
    }
  }

  updateTile(dt) {
    if (!this.tile) return;
    this.tile.vy += 820 * dt;
    this.tile.y += this.tile.vy * dt;
    if (this.tile.y + WORLD.hole.h >= FLOOR + 2) {
      const cx = this.tile.x + WORLD.hole.w / 2;
      for (let i = 0; i < 14; i++) {
        this.particles.push({ x: cx + rand(-14, 14), y: FLOOR - 2, vx: rand(-70, 70), vy: rand(-90, -20), g: 500, life: rand(0.4, 0.8), color: i % 3 ? '#dedad1' : '#a9a69d', size: i % 2 ? 2 : 1, floor: FLOOR + rand(0, 3), bounce: true });
      }
      this.dust(cx, FLOOR, 10);
      this.tile = null;
    }
  }

  updateSnow(dt) {
    const sim = this.sim;
    if (this.tileIntact || sim.phase === 'title') return;
    this.snowAcc += dt;
    const rate = this.settings.reducedMotion ? 1.2 : 3.2;
    while (this.snowAcc > 1 / rate) {
      this.snowAcc -= 1 / rate;
      const hole = WORLD.hole;
      this.snow.push({ x: hole.x + rand(3, hole.w - 3), y: hole.y + hole.h - 1, vy: rand(11, 19), ph: rand(0, 6), big: Math.random() < 0.25 });
    }
    for (const f of this.snow) {
      f.y += f.vy * dt;
      f.ph += dt * 2;
    }
    const before = this.snow.length;
    this.snow = this.snow.filter((f) => f.y < FLOOR + 1);
    if (this.snow.length < before) this.snowPile = Math.min(40, this.snowPile + (before - this.snow.length));
  }

  drawSnow(g) {
    for (const f of this.snow) {
      const x = Math.round(f.x + Math.sin(f.ph) * 3);
      this.px(g, x, Math.round(f.y), f.big ? 2 : 1, 1, '#ffffff');
    }
  }

  drawSnowPile(g) {
    const n = this.snowPile;
    if (n < 2) return;
    const h = Math.min(3, Math.floor(n / 10) + 1);
    const cx = WORLD.spawnX;
    for (let i = 0; i < h; i++) {
      const w = 6 + Math.min(n, 30) * 0.5 - i * 4;
      this.px(g, Math.round(cx - w / 2), FLOOR + 1 - i, Math.round(w), 1, i === h - 1 ? '#ffffff' : '#e6eef5');
    }
  }

  updateParticles(dt) {
    const ps = this.particles;
    for (const p of ps) {
      p.life -= dt;
      p.vy += (p.g || 0) * dt;
      if (p.drag) {
        p.vx *= Math.exp(-p.drag * dt);
        p.vy *= Math.exp(-p.drag * dt);
      }
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.floor !== undefined && p.y > p.floor && p.vy > 0) {
        p.y = p.floor;
        if (p.bounce) {
          p.vy *= -0.3;
          p.vx *= 0.5;
          p.bounce = false;
        } else {
          p.vy = 0;
          p.vx *= 0.6;
          p.g = 0;
        }
      }
    }
    if (ps.some((p) => p.life <= 0)) this.particles = ps.filter((p) => p.life > 0);
  }

  drawParticles(g) {
    for (const p of this.particles) {
      const x = Math.round(p.x);
      const y = Math.round(p.y);
      if (p.shape === 'cross') {
        this.px(g, x, y, 1, 1, '#ffffff');
        if (p.life > 0.2) {
          this.px(g, x - 1, y, 1, 1, p.color);
          this.px(g, x + 1, y, 1, 1, p.color);
          this.px(g, x, y - 1, 1, 1, p.color);
          this.px(g, x, y + 1, 1, 1, p.color);
        }
      } else {
        this.px(g, x, y, p.size || 1, p.size || 1, p.color);
      }
    }
  }

  drawPopups(g, dt, paused) {
    const s = this.s;
    for (const p of this.popups) {
      if (!paused) p.life -= dt;
      if (p.life > p.max - p.delay) continue;
      const age = p.max - p.delay - p.life;
      const k = age / (p.max - p.delay);
      if (k > 0.72 && Math.floor(age * 18) % 2) continue; // pixel-style blink out
      const img = renderText(p.text, p.color, p.scale);
      const rise = Math.round((1 - Math.pow(1 - Math.min(1, k * 1.6), 2)) * 14);
      const drift = p.drift ? Math.round(Math.sin(age * 4) * 2 + age * p.drift) : 0;
      const pop = age < 0.06 ? -1 : 0;
      const tw = textWidth(p.text) * p.scale + 2;
      const minX = this.cam.x + 2;
      const maxX = this.cam.x + this.viewW - tw - 2;
      const wx = Math.round(clamp(p.x - tw / 2, minX, Math.max(minX, maxX))) + drift;
      const maxY = this.cam.y + this.viewH - img.height - 4;
      const minY = this.cam.y + 30;
      const wy = Math.round(clamp(p.y - rise, minY, Math.max(minY, maxY))) + pop;
      g.drawImage(img, this.X(wx), this.Y(wy), img.width * s, img.height * s);
    }
    if (!paused && this.popups.some((p) => p.life <= 0)) this.popups = this.popups.filter((p) => p.life > 0);
  }

  composeDrunk(buzz) {
    const ctx = this.ctx;
    const s = this.s;
    const amp = clamp((buzz - 40) / 60, 0, 1) * 2.6 * s;
    ctx.drawImage(this.buffer, 0, 0);
    const strip = s * 2;
    const t = this.time;
    for (let y = 0; y < this.h; y += strip) {
      const off = Math.round(Math.sin((y / s) * 0.085 + t * 2.3) * amp);
      if (off !== 0) ctx.drawImage(this.buffer, 0, y, this.w, strip, off, y, this.w, strip);
    }
    if (buzz >= 70) {
      ctx.globalAlpha = ((buzz - 70) / 30) * 0.28;
      ctx.drawImage(this.buffer, Math.round(Math.sin(t * 1.3) * 4 * s), Math.round(Math.cos(t * 0.9) * s));
      ctx.globalAlpha = 1;
    }
  }

  /** World point -> CSS pixel position inside the canvas (for DOM overlays). */
  toCss(wx, wy) {
    const dpr = this.w / this.canvas.getBoundingClientRect().width;
    return { x: (this.X(wx)) / dpr, y: (this.Y(wy)) / dpr };
  }
}

export function chooseScale(w, h) {
  const TARGET_H = 200;
  let s = Math.max(1, Math.round(h / TARGET_H));
  while (s > 1 && w / s < 190) s--;
  while (h / s > WORLD.h) s++;
  return s;
}

function rand(a, b) {
  return a + Math.random() * (b - a);
}

function clamp(v, a, b) {
  return v < a ? a : v > b ? b : v;
}
