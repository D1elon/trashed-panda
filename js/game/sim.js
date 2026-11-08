// Game simulation: pure state + rules, no DOM or canvas. Runs at a fixed step.
// Coordinates are art pixels, y grows downward. The raccoon's (x, y) is the centre
// of its body horizontally and the row its feet stand on vertically.

import { WORLD } from './world-data.js';
import * as C from './config.js';

const BOARDS = WORLD.shelf.boardTops;
const TOP_LEVEL = BOARDS.length - 1;
const FLOOR = WORLD.floorLane;
const X_MIN = 12;
const X_MAX = WORLD.w - 12;

export class Sim {
  constructor(bus) {
    this.bus = bus;
    this.input = { left: false, right: false, up: false, down: false };
    this.phase = 'title';
    this.reset();
  }

  // ---------------------------------------------------------------- lifecycle
  reset() {
    this.t = 0;                 // sim clock (seconds)
    this.freezeT = 0;           // hit-stop
    this.timeLeft = C.ROUND_TIME;
    this.lastTick = C.ROUND_TIME;
    this.countdown = 3;
    this.countdownT = 0;
    this.dropT = 0;
    this.endT = 0;
    this.r = {
      x: WORLD.spawnX, y: -20, vy: 0, facing: 1, moving: false,
      level: -1, unit: -1, climb: null, falling: false, fallKind: null,
      drinkT: 0, swipeT: 0, swipeCd: 0, climbCd: 0, koT: 0, stumbleT: 0, anim: 0,
      visible: false,
    };
    this.buzz = 0;
    this.buzzTierName = 'Sober';
    this.score = 0;
    this.chain = 0;
    this.lastBreakAt = -99;
    this.stats = { broken: 0, drinks: 0, bestCombo: 0, maxBuzz: 0, reserves: 0, blackouts: 0, bonusTime: 0 };
    this.puddles = [];
    this.seq = 0;
    this.restockAt = WORLD.shelf.xs.map(() => 0);
    this.spawnBottles();
  }

  start() {
    if (this.phase !== 'title' && this.phase !== 'gameover') return;
    this.reset();
    this.r.visible = true;
    this.setPhase('dropping');
    this.bus.emit('start');
  }

  pause() {
    if (this.phase !== 'playing' && this.phase !== 'ready') return false;
    this.pausedFrom = this.phase;
    this.setPhase('paused');
    return true;
  }

  resume() {
    if (this.phase !== 'paused') return false;
    this.setPhase(this.pausedFrom || 'playing');
    return true;
  }

  setPhase(p) {
    this.phase = p;
    this.bus.emit('phase', p);
  }

  get active() {
    return this.phase === 'playing' || this.phase === 'ready';
  }

  // ---------------------------------------------------------------- setup
  spawnBottles() {
    const slots = [];
    WORLD.shelf.xs.forEach((sx, unit) => {
      for (let level = 0; level < BOARDS.length; level++) {
        for (const x of WORLD.shelf.bottleXs[unit]) slots.push({ unit, level, x });
      }
    });
    const reserveIdx = new Set();
    while (reserveIdx.size < C.RESERVE_PER_RUN) {
      const i = Math.floor(Math.random() * slots.length);
      if (slots[i].level > 0) reserveIdx.add(i); // never on the bottom board: make them climb
    }
    this.bottles = slots.map((s, i) => ({
      id: this.seq++,
      kind: reserveIdx.has(i) ? 'reserve' : C.COMMON_KINDS[Math.floor(Math.random() * 4)],
      unit: s.unit, level: s.level,
      x: s.x, y: BOARDS[s.level] - 2,
      state: 'shelf', vx: 0, vy: 0, angle: 0, spin: 0, frame: 0, frameT: 0, groundY: 0,
      wobble: 0,
    }));
  }

  restock(unit) {
    this.bottles = this.bottles.filter((b) => !(b.unit === unit && b.state === 'gone'));
    const reserveSlot = Math.random() < C.RESTOCK_RESERVE_CHANCE ? Math.floor(Math.random() * (BOARDS.length - 1) * 8) + 8 : -1;
    let i = 0;
    for (let level = 0; level < BOARDS.length; level++) {
      for (const x of WORLD.shelf.bottleXs[unit]) {
        this.bottles.push({
          id: this.seq++,
          kind: i === reserveSlot ? 'reserve' : C.COMMON_KINDS[Math.floor(Math.random() * 4)],
          unit, level, x, y: BOARDS[level] - 2,
          state: 'shelf', vx: 0, vy: 0, angle: 0, spin: 0, frame: 0, frameT: 0, groundY: 0,
          wobble: 0.3 + level * 0.08,
        });
        i++;
      }
    }
    this.bus.emit('restock', { unit });
  }

  stepRestock() {
    for (let u = 0; u < this.restockAt.length; u++) {
      if (this.restockAt[u] > 0) {
        if (this.t >= this.restockAt[u]) {
          this.restockAt[u] = 0;
          this.restock(u);
        }
      } else if (!this.bottles.some((b) => b.unit === u && b.state === 'shelf')) {
        this.restockAt[u] = this.t + C.RESTOCK_DELAY;
      }
    }
  }

  // ---------------------------------------------------------------- queries
  unitAt(x) {
    const xs = WORLD.shelf.xs;
    for (let i = 0; i < xs.length; i++) {
      if (x >= xs[i] + C.EDGE_MARGIN && x <= xs[i] + WORLD.shelf.w - C.EDGE_MARGIN) return i;
    }
    return -1;
  }

  canAct() {
    const r = this.r;
    return this.active && r.koT <= 0 && r.stumbleT <= 0 && !r.falling && !r.climb;
  }

  context() {
    // What the action button will do right now (used by touch UI hints).
    const r = this.r;
    if (!this.canAct()) return 'none';
    if (r.level >= 0) return 'swipe';
    return this.findPuddle() ? 'drink' : 'none';
  }

  findPuddle() {
    const r = this.r;
    if (r.level !== -1 || r.y < FLOOR - 1) return null;
    let best = null;
    let bestD = Infinity;
    for (const p of this.puddles) {
      if (p.draining) continue;
      const dx = (p.x - r.x) * r.facing;
      if (dx < -C.DRINK_REACH_BACK || dx > C.DRINK_REACH_FWD) continue;
      const d = Math.abs(dx - 22);
      if (d < bestD) { bestD = d; best = p; }
    }
    return best;
  }

  buzzMult() {
    return C.buzzTier(this.buzz).mult;
  }

  comboMult() {
    return C.COMBO_MULT[Math.min(this.chain, C.COMBO_MULT.length - 1)];
  }

  // ---------------------------------------------------------------- actions
  climbUp() {
    const r = this.r;
    if (!this.canAct() || r.climbCd > 0) return;
    const unit = r.level >= 0 ? r.unit : this.unitAt(r.x);
    if (unit === -1 || r.level >= TOP_LEVEL) return;
    r.climbCd = C.CLIMB_COOLDOWN;
    if (this.buzz > C.SLIP_START) {
      const chance = ((this.buzz - C.SLIP_START) / (100 - C.SLIP_START)) * C.SLIP_MAX_CHANCE;
      if (Math.random() < chance) {
        this.bus.emit('slip', { x: r.x, y: r.y, level: r.level });
        if (r.level === -1) {
          r.stumbleT = 0.4;
          this.bus.emit('land', { x: r.x, y: r.y, hard: true });
        } else {
          this.startFall('slip');
        }
        return;
      }
    }
    this.startClimb(r.level + 1, unit, 'up');
  }

  climbDown() {
    const r = this.r;
    if (!this.canAct() || r.climbCd > 0 || r.level < 0) return;
    r.climbCd = C.CLIMB_COOLDOWN;
    this.startClimb(r.level - 1, r.level - 1 >= 0 ? r.unit : -1, 'down');
  }

  startClimb(level, unit, dir) {
    const r = this.r;
    r.climb = { fromY: r.y, toY: level >= 0 ? BOARDS[level] : FLOOR, t: 0 };
    r.level = level;
    r.unit = unit;
    r.anim = 0;
    this.bus.emit('climb', { dir, level });
  }

  action() {
    const r = this.r;
    if (!this.canAct()) return;
    if (r.level >= 0) this.swipe();
    else this.drink();
  }

  swipe() {
    const r = this.r;
    if (r.swipeCd > 0) return;
    r.swipeT = C.SWIPE_TIME;
    r.swipeCd = C.SWIPE_COOLDOWN;
    r.drinkT = 0;
    r.anim = 0;
    const cx = r.x + r.facing * C.SWIPE_REACH;
    let hits = 0;
    for (const b of this.bottles) {
      if (b.state !== 'shelf' || b.unit !== r.unit || b.level !== r.level) continue;
      if (Math.abs(b.x - cx) > C.SWIPE_HALF_WIDTH) continue;
      b.state = 'falling';
      b.vx = r.facing * (24 + Math.random() * 26);
      b.vy = -70 - Math.random() * 40;
      b.spin = r.facing * (9 + Math.random() * 6);
      b.angle = 0;
      b.groundY = FLOOR + 1 + Math.round(Math.random() * 4 - 1);
      hits++;
    }
    // nudge neighbours so the shelf feels physical
    for (const b of this.bottles) {
      if (b.state === 'shelf' && b.unit === r.unit && b.level === r.level && Math.abs(b.x - cx) < 46) b.wobble = 0.35;
    }
    this.bus.emit('swipe', { hits, x: cx, y: r.y });
  }

  drink() {
    const r = this.r;
    const p = this.findPuddle();
    if (!p) {
      this.bus.emit('drinkMiss');
      return;
    }
    const kind = C.KINDS[p.kind];
    p.draining = true;
    p.drainT = 0;
    r.drinkT = C.DRINK_TIME;
    r.anim = 0;
    if (p.x !== r.x) r.facing = p.x > r.x ? 1 : -1;
    this.stats.drinks++;
    const pts = this.addPoints(kind.drink, 1, p.x, FLOOR - 26, 'drink');
    this.addBuzz(kind.buzz);
    this.bus.emit('drink', { kind: p.kind, buzz: this.buzz, points: pts });
  }

  addPoints(base, combo, x, y, kind) {
    const buzz = this.buzzMult();
    const pts = Math.round(base * combo * buzz);
    this.score += pts;
    this.bus.emit('score', { points: pts, base, combo, buzz, x, y, kind, total: this.score });
    return pts;
  }

  addBuzz(amount) {
    this.buzz = Math.min(100, this.buzz + amount);
    this.stats.maxBuzz = Math.max(this.stats.maxBuzz, this.buzz);
    this.checkTier();
    if (this.buzz >= 100) this.blackout();
  }

  checkTier() {
    const name = C.buzzTier(this.buzz).name;
    if (name !== this.buzzTierName) {
      const up = C.BUZZ_TIERS.findIndex((t) => t.name === name) > C.BUZZ_TIERS.findIndex((t) => t.name === this.buzzTierName);
      this.buzzTierName = name;
      this.bus.emit('buzzTier', { name, up });
    }
  }

  blackout() {
    const r = this.r;
    this.stats.blackouts++;
    r.koT = C.BLACKOUT_TIME;
    r.drinkT = 0;
    r.swipeT = 0;
    this.endChain();
    this.bus.emit('blackout', { x: r.x, y: r.y });
    if (r.level >= 0 || r.climb) this.startFall('blackout');
  }

  startFall(kind) {
    const r = this.r;
    r.climb = null;
    r.falling = true;
    r.fallKind = kind;
    r.vy = kind === 'slip' ? -40 : 0;
    r.level = -1;
    r.unit = -1;
    this.bus.emit('fall', { kind });
  }

  freeze(t) {
    this.freezeT = Math.max(this.freezeT, t);
  }

  // ---------------------------------------------------------------- stepping
  step(dt) {
    if (this.phase === 'paused' || this.phase === 'title' || this.phase === 'gameover') {
      this.stepBottlesIdle(dt);
      return;
    }
    if (this.freezeT > 0) {
      this.freezeT -= dt;
      return;
    }
    this.t += dt;
    switch (this.phase) {
      case 'dropping': this.stepDrop(dt); break;
      case 'ready': this.stepCountdown(dt); this.stepRaccoon(dt); break;
      case 'playing': this.stepTimer(dt); this.stepBuzz(dt); this.stepRaccoon(dt); this.stepRestock(); break;
      case 'ending': this.stepEnding(dt); break;
      default: break;
    }
    this.stepBottles(dt);
    this.stepPuddles(dt);
    this.stepCombo();
  }

  stepDrop(dt) {
    const r = this.r;
    this.dropT += dt;
    const k = Math.min(1, this.dropT / C.DROP_TIME);
    const startY = WORLD.ceilH - 4;
    r.y = startY + (FLOOR - startY) * k * k;
    r.anim += dt;
    if (k >= 1) {
      r.y = FLOOR;
      this.bus.emit('land', { x: r.x, y: r.y, hard: true, intro: true });
      this.setPhase('ready');
      this.countdown = 3;
      this.countdownT = 0;
      this.bus.emit('countdown', 3);
    }
  }

  stepCountdown(dt) {
    this.countdownT += dt;
    while (this.countdownT >= C.COUNTDOWN_STEP) {
      this.countdownT -= C.COUNTDOWN_STEP;
      this.countdown--;
      if (this.countdown >= 0) {
        this.bus.emit('countdown', this.countdown);
      } else {
        this.setPhase('playing');
        this.bus.emit('go');
        return;
      }
    }
  }

  stepTimer(dt) {
    this.timeLeft -= dt;
    const whole = Math.ceil(this.timeLeft);
    if (whole !== this.lastTick) {
      this.lastTick = whole;
      this.bus.emit('tick', whole);
      if (whole === 10) this.bus.emit('warning');
    }
    if (this.timeLeft <= 0) {
      this.timeLeft = 0;
      this.endRun();
    }
  }

  stepBuzz(dt) {
    if (this.r.koT > 0) return;
    this.buzz = Math.max(0, this.buzz - C.BUZZ_DECAY * dt);
    this.checkTier();
  }

  endRun() {
    const r = this.r;
    this.endChain();
    r.drinkT = 0;
    r.swipeT = 0;
    r.koT = 999;
    this.endT = 0;
    this.setPhase('ending');
    this.bus.emit('timeUp');
    if (r.level >= 0 || r.climb) this.startFall('blackout');
  }

  stepEnding(dt) {
    const r = this.r;
    this.stepVertical(dt);
    if (!r.falling) {
      this.endT += dt;
      if (this.endT >= C.END_KO_TIME) {
        this.setPhase('gameover');
        this.bus.emit('over', this.results());
      }
    }
  }

  results() {
    return {
      score: this.score,
      ...this.stats,
      rank: C.rankFor(this.score).name,
    };
  }

  stepRaccoon(dt) {
    const r = this.r;
    r.climbCd = Math.max(0, r.climbCd - dt);
    r.swipeCd = Math.max(0, r.swipeCd - dt);
    r.swipeT = Math.max(0, r.swipeT - dt);
    r.drinkT = Math.max(0, r.drinkT - dt);
    r.stumbleT = Math.max(0, r.stumbleT - dt);
    if (r.koT > 0) {
      if (!r.falling) {
        r.koT -= dt;
        if (r.koT <= 0) {
          r.koT = 0;
          this.buzz = C.BLACKOUT_RECOVER_TO;
          this.checkTier();
          this.bus.emit('wake');
        }
      }
      this.stepVertical(dt);
      r.moving = false;
      return;
    }

    // held up/down climbs repeatedly (cooldown-limited)
    if (this.input.up) this.climbUp();
    if (this.input.down) this.climbDown();

    const left = this.input.left && !this.input.right;
    const right = this.input.right && !this.input.left;
    const busy = r.drinkT > 0 || r.stumbleT > 0;
    r.moving = (left || right) && !r.climb && !busy;

    if (r.climb) {
      r.climb.t += dt / C.CLIMB_TIME;
      if (r.climb.t >= 1) {
        r.y = r.climb.toY;
        r.climb = null;
        this.bus.emit('land', { x: r.x, y: r.y, hard: false });
      } else {
        const k = 1 - Math.pow(1 - r.climb.t, 3);
        r.y = r.climb.fromY + (r.climb.toY - r.climb.fromY) * k;
      }
    } else if (r.moving) {
      const speed = C.WALK_SPEED * (1 - C.DRUNK_SPEED_PENALTY * (this.buzz / 100));
      const sway = this.buzz > 60 ? Math.sin(this.t * 7.3) * (this.buzz - 60) * 0.25 : 0;
      r.facing = left ? -1 : 1;
      r.x = clamp(r.x + (r.facing * speed + sway) * dt, X_MIN, X_MAX);
      if (r.swipeT > 0) r.swipeT = 0;
    }
    if (!r.climb) this.stepVertical(dt);
    if (r.moving || r.climb || r.drinkT > 0 || r.swipeT > 0 || r.falling) r.anim += dt;
    else r.anim = 0;
  }

  stepVertical(dt) {
    const r = this.r;
    if (r.falling) {
      r.vy = Math.min(C.MAX_FALL_SPEED, r.vy + C.GRAVITY * dt);
      const prev = r.y;
      const next = r.y + r.vy * dt;
      const unit = r.fallKind === 'slip' || r.fallKind === 'edge' ? this.unitAt(r.x) : -1;
      if (unit !== -1) {
        for (let lv = TOP_LEVEL; lv >= 0; lv--) {
          const by = BOARDS[lv];
          if (prev < by && next >= by && r.vy > 0) {
            this.land(by, unit, lv);
            return;
          }
        }
      }
      if (next >= FLOOR) {
        this.land(FLOOR, -1, -1);
        return;
      }
      r.y = next;
      return;
    }
    // walked off the end of a shelf?
    if (r.level >= 0 && this.unitAt(r.x) !== r.unit) {
      r.level = -1;
      r.unit = -1;
      r.falling = true;
      r.fallKind = 'edge';
      r.vy = 0;
      this.bus.emit('fall', { kind: 'edge' });
    }
  }

  land(y, unit, level) {
    const r = this.r;
    const hard = r.vy > 200 || r.fallKind === 'slip' || r.fallKind === 'blackout';
    r.y = y;
    r.falling = false;
    r.vy = 0;
    r.unit = unit;
    r.level = level;
    if (hard && r.koT <= 0) r.stumbleT = 0.3;
    this.bus.emit('land', { x: r.x, y, hard });
    r.fallKind = null;
  }

  stepBottlesIdle(dt) {
    for (const b of this.bottles) if (b.wobble > 0) b.wobble = Math.max(0, b.wobble - dt);
  }

  stepBottles(dt) {
    for (const b of this.bottles) {
      if (b.wobble > 0) b.wobble = Math.max(0, b.wobble - dt);
      if (b.state === 'falling') {
        b.vy += C.BOTTLE_GRAVITY * dt;
        b.x += b.vx * dt;
        b.y += b.vy * dt;
        b.angle += b.spin * dt;
        if (b.y >= b.groundY && b.vy > 0) {
          b.y = b.groundY;
          b.state = 'breaking';
          b.frame = 0;
          b.frameT = 0;
          this.registerBreak(b);
        }
      } else if (b.state === 'breaking') {
        b.frameT += dt;
        if (b.frameT >= C.BREAK_FRAME_TIME) {
          b.frameT -= C.BREAK_FRAME_TIME;
          b.frame++;
          if (b.frame >= 3) {
            b.state = 'gone';
            this.puddles.push({ id: this.seq++, x: Math.round(b.x), y: b.groundY, kind: b.kind, draining: false, drainT: 0, born: this.t });
          }
        }
      }
    }
  }

  registerBreak(b) {
    if (this.chain > 0 && this.t - this.lastBreakAt > C.COMBO_WINDOW) this.endChain();
    this.chain++;
    this.lastBreakAt = this.t;
    this.stats.broken++;
    const kind = C.KINDS[b.kind];
    const combo = this.comboMult();
    const pts = this.addPoints(kind.smash, combo, b.x, b.y - 20, 'smash');
    if (this.chain >= 2) {
      this.stats.bestCombo = Math.max(this.stats.bestCombo, this.chain);
      this.bus.emit('combo', { chain: this.chain, mult: combo });
      if (this.chain === 5 || this.chain === 10) this.freeze(0.05);
    }
    if (kind.timeBonus && this.phase === 'playing') {
      this.timeLeft += kind.timeBonus;
      this.stats.bonusTime += kind.timeBonus;
      this.stats.reserves++;
      this.freeze(0.07);
      this.bus.emit('timeBonus', { seconds: kind.timeBonus, x: b.x, y: b.y - 34 });
    }
    this.bus.emit('break', { x: b.x, y: b.y, kind: b.kind, points: pts });
  }

  stepPuddles(dt) {
    for (const p of this.puddles) {
      if (p.draining) p.drainT += dt / C.DRINK_TIME;
    }
    if (this.puddles.some((p) => p.drainT >= 1)) this.puddles = this.puddles.filter((p) => p.drainT < 1);
  }

  stepCombo() {
    if (this.chain > 0 && this.t - this.lastBreakAt > C.COMBO_WINDOW) this.endChain();
  }

  endChain() {
    const c = this.chain;
    this.chain = 0;
    if (c >= 2) this.bus.emit('comboEnd', { chain: c });
  }

  comboRemaining() {
    if (this.chain < 1) return 0;
    return Math.max(0, 1 - (this.t - this.lastBreakAt) / C.COMBO_WINDOW);
  }
}

function clamp(v, a, b) {
  return v < a ? a : v > b ? b : v;
}
