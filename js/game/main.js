// Boots the game: wires sim, renderer, audio, input and UI together and runs the loop.

import { Bus } from './events.js';
import { Sim } from './sim.js';
import { Renderer } from './render.js';
import { Audio } from './audio.js';
import { Input } from './input.js';
import { UI } from './ui.js';
import { loadAssets } from './assets.js';
import { loadSettings, saveSettings } from './storage.js';
import { SIM_DT, MAX_FRAME_DT } from './config.js';

class Game {
  async init() {
    this.settings = loadSettings();
    this.bus = new Bus();
    this.sim = new Sim(this.bus);
    this.audio = new Audio(this.bus, this.settings);
    this.ui = new UI(this);
    this.canvas = document.getElementById('game');
    this.stage = document.getElementById('stage');
    this.touchEl = document.getElementById('touch');
    this.touchOn = false;

    try {
      this.assets = await loadAssets();
    } catch (err) {
      console.error(err);
      document.getElementById('loader').innerHTML = '<span>Couldn’t load the game. Refresh to try again.</span>';
      return;
    }
    this.renderer = new Renderer(this.canvas, this.sim, this.bus, this.assets, this.settings);
    this.input = new Input(this.sim, {
      onPause: () => this.togglePause(),
      onKey: (e) => this.onKey(e),
      onTouchStart: () => this.audio.unlock(),
    });
    this.input.bindTouch(document.getElementById('dpad'), document.getElementById('abtn'));

    const coarse = matchMedia('(pointer: coarse)');
    this.setTouch(coarse.matches);
    window.addEventListener('touchstart', () => this.setTouch(true), { passive: true, once: true });

    new ResizeObserver(() => this.renderer.resize()).observe(this.canvas);
    this.renderer.resize();
    document.addEventListener('visibilitychange', () => this.onVisibility());
    window.addEventListener('blur', () => this.autoPause());
    for (const ev of ['pointerdown', 'keydown']) window.addEventListener(ev, () => this.audio.unlock(), { once: true });

    this.bus.on('start', () => this.ui.resetHud());
    this.bus.on('phase', (p) => {
      if (p === 'dropping' && this.touchOn) this.focusStage();
    });

    this.last = performance.now();
    this.acc = 0;
    requestAnimationFrame((t) => this.frame(t));
    this.ui.ready();
    if (location.hash === '#play' && !this.touchOn) this.stage.focus({ preventScroll: true });
  }

  frame(now) {
    requestAnimationFrame((t) => this.frame(t));
    const dt = Math.min(Math.max(0, (now - this.last) / 1000), MAX_FRAME_DT);
    this.last = now;
    this.acc += dt;
    let steps = 0;
    while (this.acc >= SIM_DT && steps < 24) {
      this.sim.step(SIM_DT);
      this.acc -= SIM_DT;
      steps++;
    }
    this.renderer.render(dt);
    this.ui.update();
  }

  // ------------------------------------------------------------ lifecycle
  start() {
    this.audio.unlock();
    const p = this.sim.phase;
    if (p !== 'title' && p !== 'gameover') return;
    this.sim.phase = 'title';
    this.sim.start();
  }

  restart() {
    while (this.ui.modalOpen) this.ui.closeModal();
    this.sim.reset();
    this.sim.phase = 'title';
    this.sim.start();
  }

  quit() {
    while (this.ui.modalOpen) this.ui.closeModal();
    this.sim.reset();
    this.sim.setPhase('title');
  }

  pause() {
    if (this.sim.pause()) this.input.releaseAll();
  }

  resume() {
    while (this.ui.modalOpen) this.ui.closeModal();
    this.sim.resume();
    this.last = performance.now();
    this.acc = 0;
  }

  togglePause() {
    if (this.sim.phase === 'paused') {
      if (this.ui.modalStack.length > 1) this.ui.closeModal();
      else this.resume();
    } else this.pause();
  }

  autoPause() {
    if (this.sim.active) this.pause();
  }

  onVisibility() {
    if (document.hidden) {
      this.autoPause();
      this.audio.suspend();
    } else {
      this.audio.resumeCtx();
      this.last = performance.now();
    }
  }

  onKey(e) {
    const p = this.sim.phase;
    if (e.code === 'Escape' && this.ui.modalOpen && p !== 'paused') {
      this.ui.closeModal();
      return true;
    }
    if (e.code === 'Escape' && p === 'paused' && this.ui.modalStack.length > 1) {
      this.ui.closeModal();
      return true;
    }
    if (this.ui.modalOpen && p !== 'paused') return true;
    if (e.code === 'KeyM') {
      this.applySettings({ ...this.settings, muted: !this.settings.muted });
      document.getElementById('set-muted').checked = this.settings.muted;
      this.ui.toast(this.settings.muted ? 'Sound off' : 'Sound on');
      return true;
    }
    if (e.code === 'KeyF') {
      this.toggleFullscreen();
      return true;
    }
    const onButton = e.target && e.target.tagName === 'BUTTON';
    if ((p === 'title' || p === 'gameover') && (e.code === 'Enter' || e.code === 'Space') && !onButton) {
      e.preventDefault();
      if (p === 'title') this.start();
      else this.restart();
      return true;
    }
    return false;
  }

  applySettings(s) {
    this.settings = s;
    saveSettings(s);
    this.audio.apply(s);
    if (this.renderer) this.renderer.settings = s;
  }

  // ------------------------------------------------------------ device
  setTouch(on) {
    this.touchOn = on;
    document.body.classList.toggle('is-touch', on);
    this.touchVisible(this.sim.phase !== 'title' && this.sim.phase !== 'gameover');
  }

  touchVisible(playing) {
    this.touchEl.hidden = !(this.touchOn && playing);
    requestAnimationFrame(() => this.renderer?.resize());
  }

  focusStage() {
    const top = this.stage.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top: Math.max(0, top - (document.body.classList.contains('is-playing') ? 0 : 56)), behavior: 'instant' });
  }

  vibrate(pattern) {
    if (this.touchOn && navigator.vibrate && !this.settings.muted) {
      try {
        navigator.vibrate(pattern);
      } catch {
        /* unsupported */
      }
    }
  }

  toggleFullscreen() {
    const el = document.getElementById('play');
    if (document.fullscreenElement) document.exitFullscreen?.();
    else el.requestFullscreen?.().catch(() => {});
  }
}

const game = new Game();
game.init();
window.__trashedPanda = game; // handy for debugging from the console
