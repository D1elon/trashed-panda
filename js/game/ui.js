// DOM layer: HUD, screens, settings, results. The canvas never draws UI chrome;
// keeping it in the DOM keeps text crisp, selectable and screen-reader friendly.

import { buzzTier, RESERVE_PER_RUN } from './config.js';
import * as store from './storage.js';

const $ = (id) => document.getElementById(id);
const SEGMENTS = 10;
const SEG_COLORS = ['#5fb56f', '#5fb56f', '#c9d65a', '#f2c14e', '#f2a93b', '#f08a3a', '#e0533d', '#e0533d', '#d24bc4', '#d24bc4'];

export class UI {
  constructor(game) {
    this.g = game;
    this.stage = $('stage');
    this.hud = $('hud');
    this.screens = ['screen-title', 'screen-help', 'screen-pause', 'screen-settings', 'screen-over'].reduce((m, id) => ((m[id] = $(id)), m), {});
    this.modalStack = [];
    this.last = {};
    this.meterSegs = [];
    const meter = $('hud-meter');
    for (let i = 0; i < SEGMENTS; i++) {
      const s = document.createElement('i');
      s.style.setProperty('--seg', SEG_COLORS[i]);
      meter.appendChild(s);
      this.meterSegs.push(s);
    }
    this.bindButtons();
    this.bindSettings();
    this.subscribe();
    this.refreshBest();
  }

  // ------------------------------------------------------------ screens
  show(id) {
    this.screens[id].hidden = false;
  }

  hide(id) {
    this.screens[id].hidden = true;
  }

  openModal(id) {
    const el = this.screens[id];
    this.modalStack.push({ id, returnFocus: document.activeElement });
    el.hidden = false;
    const first = el.querySelector('[data-close], button, input');
    requestAnimationFrame(() => (el.querySelector('.btn--primary') || first)?.focus({ preventScroll: true }));
  }

  closeModal() {
    const top = this.modalStack.pop();
    if (!top) return false;
    this.screens[top.id].hidden = true;
    top.returnFocus?.focus?.({ preventScroll: true });
    return true;
  }

  get modalOpen() {
    return this.modalStack.length > 0;
  }

  bindButtons() {
    const g = this.g;
    $('btn-play').addEventListener('click', () => g.start());
    $('btn-help').addEventListener('click', () => this.openModal('screen-help'));
    $('btn-help-pause').addEventListener('click', () => this.openModal('screen-help'));
    $('btn-settings-title').addEventListener('click', () => this.openModal('screen-settings'));
    $('btn-settings-pause').addEventListener('click', () => this.openModal('screen-settings'));
    $('btn-pause').addEventListener('click', () => g.pause());
    $('btn-resume').addEventListener('click', () => g.resume());
    $('btn-restart').addEventListener('click', () => g.restart());
    $('btn-quit').addEventListener('click', () => g.quit());
    $('btn-again').addEventListener('click', () => g.restart());
    $('btn-share').addEventListener('click', () => this.share());
    for (const el of document.querySelectorAll('[data-close]')) el.addEventListener('click', () => this.closeModal());
    for (const id of ['screen-help', 'screen-settings']) {
      this.screens[id].addEventListener('pointerdown', (e) => {
        if (e.target === this.screens[id]) this.closeModal();
      });
    }
    $('name-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveName();
    });
    $('name-input').addEventListener('input', (e) => {
      const v = e.target.value.toUpperCase().replace(/[^A-Z0-9 !?.\-]/g, '');
      if (v !== e.target.value) e.target.value = v;
    });
    // clicks on UI must not leak to the page behind
    this.stage.addEventListener('pointerdown', () => g.audio.unlock(), { passive: true });
    for (const b of this.stage.querySelectorAll('button')) b.addEventListener('click', () => g.audio.sfx('click'));
  }

  bindSettings() {
    const g = this.g;
    const s = g.settings;
    const music = $('set-music');
    const sfx = $('set-sfx');
    const set = (patch) => g.applySettings({ ...g.settings, ...patch });
    music.value = Math.round(s.music * 100);
    sfx.value = Math.round(s.sfx * 100);
    $('set-music-out').textContent = music.value;
    $('set-sfx-out').textContent = sfx.value;
    music.addEventListener('input', () => {
      $('set-music-out').textContent = music.value;
      set({ music: music.value / 100 });
    });
    sfx.addEventListener('input', () => {
      $('set-sfx-out').textContent = sfx.value;
      set({ sfx: sfx.value / 100 });
    });
    sfx.addEventListener('change', () => g.audio.sfx('coin'));
    const toggles = { 'set-muted': 'muted', 'set-shake': 'screenShake', 'set-drunkfx': 'drunkFx', 'set-santa': 'santa' };
    for (const [id, key] of Object.entries(toggles)) {
      const el = $(id);
      el.checked = !!s[key];
      el.addEventListener('change', () => set({ [key]: el.checked }));
    }
  }

  // ------------------------------------------------------------ bus
  subscribe() {
    const b = this.g.bus;
    b.on('phase', (p) => this.onPhase(p));
    b.on('countdown', (n) => this.countdown(n > 0 ? String(n) : 'GO!', n === 0));
    b.on('go', () => setTimeout(() => this.countdown(null), 450));
    b.on('timeBonus', ({ seconds }) => {
      const el = $('hud-bonus');
      el.textContent = `+${seconds}`;
      el.hidden = false;
      el.classList.remove('is-pop');
      void el.offsetWidth;
      el.classList.add('is-pop');
      clearTimeout(this.bonusT);
      this.bonusT = setTimeout(() => (el.hidden = true), 1400);
    });
    b.on('over', (r) => setTimeout(() => this.showResults(r), 350));
    b.on('blackout', () => this.g.vibrate([30, 40, 60]));
    b.on('break', () => this.g.vibrate(8));
  }

  onPhase(p) {
    const playing = p === 'dropping' || p === 'ready' || p === 'playing' || p === 'paused' || p === 'ending';
    this.hud.hidden = !(p === 'ready' || p === 'playing' || p === 'paused' || p === 'ending');
    document.body.classList.toggle('is-playing', playing);
    if (p === 'title') {
      this.show('screen-title');
      this.hide('screen-over');
      this.refreshBest();
    } else {
      this.hide('screen-title');
    }
    if (p === 'paused') this.openModal('screen-pause');
    else if (!this.screens['screen-pause'].hidden) {
      while (this.modalOpen) this.closeModal();
    }
    if (p !== 'gameover') this.hide('screen-over');
    this.g.touchVisible(playing);
  }

  countdown(text, go) {
    const el = $('countdown');
    if (!text) {
      el.textContent = '';
      el.className = 'countdown';
      return;
    }
    el.textContent = text;
    el.className = 'countdown';
    void el.offsetWidth;
    el.className = `countdown is-on${go ? ' is-go' : ''}`;
  }

  toast(msg) {
    const el = $('toast');
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(this.toastT);
    this.toastT = setTimeout(() => (el.hidden = true), 2200);
  }

  refreshBest() {
    const best = store.bestScore();
    $('title-best').hidden = best === null;
    if (best !== null) $('title-best-val').textContent = best.toLocaleString();
  }

  ready() {
    const btn = $('btn-play');
    btn.disabled = false;
    btn.textContent = 'Play';
    $('loader').hidden = true;
  }

  // ------------------------------------------------------------ HUD
  update() {
    const sim = this.g.sim;
    if (this.hud.hidden) return;
    const L = this.last;
    if (L.score !== sim.score) {
      const el = $('hud-score');
      el.textContent = sim.score.toLocaleString();
      if (L.score !== undefined) {
        el.classList.remove('is-pop');
        void el.offsetWidth;
        el.classList.add('is-pop');
      }
      L.score = sim.score;
    }
    const t = Math.ceil(sim.timeLeft);
    if (L.time !== t) {
      $('hud-time').textContent = String(Math.max(0, t));
      $('hud-time-box').classList.toggle('is-warn', t <= 10 && sim.phase === 'playing');
      L.time = t;
    }
    const filled = Math.ceil(sim.buzz / 10 - 0.001);
    const tier = buzzTier(sim.buzz);
    if (L.filled !== filled || L.tier !== tier.name) {
      this.meterSegs.forEach((seg, i) => seg.classList.toggle('on', i < filled));
      $('hud-meter').setAttribute('aria-valuenow', String(Math.round(sim.buzz)));
      $('hud-tier').innerHTML = `${tier.name} <b>x${tier.mult}</b>`;
      $('hud-buzz-box').dataset.tier = tier.name.toLowerCase();
      L.filled = filled;
      L.tier = tier.name;
    }
    $('hud-buzz-box').classList.toggle('is-danger', sim.buzz >= 88 && sim.r.koT <= 0);
    const chain = sim.chain;
    const combo = $('hud-combo');
    if (chain >= 2) {
      if (L.chain !== chain) {
        $('hud-combo-text').textContent = `Combo x${sim.comboMult()} · ${chain}`;
        combo.classList.remove('is-pop');
        void combo.offsetWidth;
        combo.classList.add('is-pop');
      }
      combo.hidden = false;
      $('hud-combo-bar').style.transform = `scaleX(${sim.comboRemaining().toFixed(3)})`;
    } else if (!combo.hidden) {
      combo.hidden = true;
    }
    L.chain = chain;
    // context-sensitive touch button
    if (this.g.touchOn) {
      const ctx = sim.context();
      const label = ctx === 'none' ? (sim.r.level >= 0 ? 'Swipe' : 'Drink') : ctx === 'swipe' ? 'Swipe' : 'Drink';
      if (L.ctx !== ctx || L.label !== label) {
        $('abtn-label').textContent = label;
        $('abtn').classList.toggle('is-idle', ctx === 'none');
        $('abtn').classList.toggle('is-drink', label === 'Drink');
        L.ctx = ctx;
        L.label = label;
      }
    }
  }

  resetHud() {
    this.last = {};
    $('hud-combo').hidden = true;
    $('hud-bonus').hidden = true;
  }

  // ------------------------------------------------------------ results
  showResults(r) {
    this.results = r;
    this.saved = null;
    this.show('screen-over');
    $('over-rank').textContent = r.rank;
    $('over-title').textContent = r.blackouts > 0 && r.score < 600 ? 'Blacked out' : 'Passed out';
    const stats = [
      ['Bottles smashed', r.broken],
      ['Best combo', r.bestCombo >= 2 ? `${r.bestCombo} in a row` : '—'],
      ['Puddles drunk', r.drinks],
      ['Peak buzz', `${Math.round(r.maxBuzz)}%`],
      ['Holiday Reserve', `${r.reserves} / ${RESERVE_PER_RUN}`],
      ['Blackouts', r.blackouts],
    ];
    $('over-stats').innerHTML = stats.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
    this.countUp($('over-score'), r.score);
    const form = $('name-form');
    form.hidden = !store.qualifies(r.score);
    this.renderBoard();
    if (!form.hidden) {
      const input = $('name-input');
      input.value = store.lastName();
      if (!this.g.touchOn) requestAnimationFrame(() => input.focus({ preventScroll: true }));
    } else {
      requestAnimationFrame(() => $('btn-again').focus({ preventScroll: true }));
    }
  }

  countUp(el, target) {
    const reduced = this.g.settings.reducedMotion;
    if (reduced || target === 0) {
      el.textContent = target.toLocaleString();
      return;
    }
    const t0 = performance.now();
    const dur = 900;
    const tick = (now) => {
      const k = Math.min(1, (now - t0) / dur);
      el.textContent = Math.round(target * (1 - Math.pow(1 - k, 3))).toLocaleString();
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  saveName() {
    const input = $('name-input');
    const name = input.value.trim().slice(0, 10);
    if (name.length < 2 || !this.results) {
      input.focus();
      return;
    }
    const r = this.results;
    const { entry } = store.submitScore({ name, score: r.score, broken: r.broken, bestCombo: r.bestCombo });
    store.rememberName(name);
    this.saved = entry;
    $('name-form').hidden = true;
    this.renderBoard();
    this.refreshBest();
    $('btn-again').focus({ preventScroll: true });
  }

  renderBoard() {
    const board = store.loadBoard();
    const ol = $('board');
    if (!board.length) {
      ol.innerHTML = '<li class="board__empty">No scores yet. Be the first.</li>';
      return;
    }
    ol.innerHTML = board
      .map((e, i) => {
        const me = this.saved && e.date === this.saved.date && e.score === this.saved.score;
        return `<li class="${me ? 'is-me' : ''}"><span class="board__rank">${i + 1}</span><span class="board__name">${escapeHtml(e.name)}</span><span class="board__score">${e.score.toLocaleString()}</span></li>`;
      })
      .join('');
  }

  async share() {
    const r = this.results;
    if (!r) return;
    const url = 'https://www.trashedpanda.lol/';
    const text = `I scored ${r.score.toLocaleString()} as the Ashland liquor store raccoon (${r.rank}). Can you beat it?`;
    try {
      if (navigator.share) {
        await navigator.share({ title: 'Trashed Panda', text, url });
        return;
      }
      await navigator.clipboard.writeText(`${text} ${url}`);
      this.toast('Copied! Paste it anywhere.');
    } catch (err) {
      if (err && err.name === 'AbortError') return;
      this.toast('Couldn’t share. Copy the link from the address bar.');
    }
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
