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

const $ = (id) => document.getElementById(id);

class Game {
  async init() {
    this.settings = loadSettings();
    this.bus = new Bus();
    this.sim = new Sim(this.bus);
    this.audio = new Audio(this.bus, this.settings);
    this.ui = new UI(this);
    this.canvas = $('game');
    this.stage = $('stage');
    this.touchEl = $('touch');
    this.touchOn = false;
    this.installPageGuards();

    try {
      this.assets = await loadAssets();
    } catch (err) {
      console.error(err);
      $('loader').innerHTML = '<span>Couldn’t load the game. Refresh to try again.</span>';
      return;
    }
    this.renderer = new Renderer(this.canvas, this.sim, this.bus, this.assets, this.settings);
    this.input = new Input(this.sim, {
      onPause: () => this.togglePause(),
      onKey: (e) => this.onKey(e),
      onTouchStart: () => this.audio.unlock(),
    });
    this.input.bindTouch({ moveZone: $('move-zone'), pad: $('dpad'), actZone: $('act-zone'), actionBtn: $('abtn') });

    const coarse = matchMedia('(pointer: coarse)');
    this.setTouch(coarse.matches);
    window.addEventListener('touchstart', () => this.setTouch(true), { passive: true, once: true });

    new ResizeObserver(() => this.renderer.resize()).observe(this.canvas);
    this.renderer.resize();
    document.addEventListener('visibilitychange', () => this.onVisibility());
    window.addEventListener('blur', () => this.autoPause());
    for (const ev of ['pointerdown', 'keydown']) window.addEventListener(ev, () => this.audio.unlock(), { once: true });

    this.bus.on('start', () => this.ui.resetHud());
    this.setupFullscreen();

    this.last = performance.now();
    this.acc = 0;
    requestAnimationFrame((t) => this.frame(t));
    this.ui.ready();
    if (!this.touchOn) this.stage.focus({ preventScroll: true });
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
      $('set-muted').checked = this.settings.muted;
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

  vibrate(pattern) {
    if (this.touchOn && navigator.vibrate && !this.settings.muted) {
      try {
        navigator.vibrate(pattern);
      } catch {
        /* unsupported */
      }
    }
  }

  /**
   * The CSS already makes this page an unscrollable, unzoomable app screen (css/game.css).
   * These guards cover the browsers that ignore part of it, mainly iOS Safari, which
   * disregards user-scalable=no and can leave the page offset after the keyboard closes.
   */
  installPageGuards() {
    const zoomed = () => (window.visualViewport ? window.visualViewport.scale > 1.01 : false);
    // Pinch: block it at normal scale, but if the page ever does end up zoomed, let the
    // player pinch back out instead of trapping them.
    for (const type of ['gesturestart', 'gesturechange']) {
      document.addEventListener(type, (e) => {
        if (!zoomed()) e.preventDefault();
      }, { passive: false });
    }
    // Nothing on this page scrolls except menus that overflow (a screen or the panel in it).
    const insideScroller = (el) => {
      for (let n = el; n && n !== this.stage && n !== document.body; n = n.parentElement) {
        if (n.scrollHeight > n.clientHeight + 1) {
          const oy = getComputedStyle(n).overflowY;
          if (oy === 'auto' || oy === 'scroll') return true;
        }
      }
      return false;
    };
    document.addEventListener('touchmove', (e) => {
      if (e.touches.length > 1) {
        if (!zoomed()) e.preventDefault();
        return;
      }
      if (!(e.target instanceof Element) || !insideScroller(e.target)) e.preventDefault();
    }, { passive: false });
    document.addEventListener('dblclick', (e) => e.preventDefault());
    // Keep the page pinned to the top, except while a text field has the keyboard up.
    const typing = () => document.activeElement && document.activeElement.tagName === 'INPUT' && document.activeElement.type !== 'range';
    const pin = () => {
      if (!typing() && (window.scrollX || window.scrollY)) window.scrollTo(0, 0);
    };
    window.addEventListener('scroll', pin, { passive: true });
    window.addEventListener('orientationchange', () => setTimeout(pin, 250));
    document.addEventListener('focusout', () => setTimeout(pin, 60));
    window.visualViewport?.addEventListener('resize', pin);
  }

  setupFullscreen() {
    const btn = $('btn-fullscreen-title');
    const standalone = matchMedia('(display-mode: fullscreen), (display-mode: standalone)').matches || navigator.standalone;
    if (!document.fullscreenEnabled || standalone) return;
    btn.hidden = false;
    btn.addEventListener('click', () => this.toggleFullscreen());
    document.addEventListener('fullscreenchange', () => {
      const on = Boolean(document.fullscreenElement);
      btn.setAttribute('aria-label', on ? 'Exit full screen' : 'Full screen');
      btn.classList.toggle('is-on', on);
      requestAnimationFrame(() => this.renderer?.resize());
    });
  }

  toggleFullscreen() {
    if (!document.fullscreenEnabled) return;
    if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {});
    else $('play').requestFullscreen?.({ navigationUI: 'hide' }).catch(() => {});
  }
}

const game = new Game();
game.init();
window.__trashedPanda = game; // handy for debugging from the console
