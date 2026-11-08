// Keyboard and touch input. Touch uses pointer events with per-pointer tracking,
// so you can hold the D-pad with one thumb and tap the action button with the other.

const KEYS = {
  left: ['ArrowLeft', 'KeyA'],
  right: ['ArrowRight', 'KeyD'],
  up: ['ArrowUp', 'KeyW'],
  down: ['ArrowDown', 'KeyS'],
  action: ['Space', 'KeyE', 'KeyJ', 'KeyK'],
  pause: ['Escape', 'KeyP'],
};
const GAME_KEYS = new Set(Object.values(KEYS).flat());

export class Input {
  constructor(sim, handlers) {
    this.sim = sim;
    this.h = handlers;
    this.held = new Set();
    this.touchDir = { left: false, right: false, up: false, down: false };
    this.onKeyDown = this.onKeyDown.bind(this);
    this.onKeyUp = this.onKeyUp.bind(this);
    this.onBlur = () => this.releaseAll();
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    window.addEventListener('blur', this.onBlur);
  }

  /** True only for fields that take text; checkboxes and sliders must not swallow keys. */
  typing(e) {
    const t = e.target;
    if (!t) return false;
    if (t.tagName === 'TEXTAREA' || t.isContentEditable) return true;
    return t.tagName === 'INPUT' && /^(text|search|email|number|password|tel|url)$/.test(t.type || 'text');
  }

  onKeyDown(e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.code === 'Escape' && this.h.onKey && this.h.onKey(e)) return;
    if (this.typing(e)) return;
    // sliders and toggles in open menus keep their own arrow/space behaviour
    if (e.target && e.target.tagName === 'INPUT' && !this.sim.active) return;
    const code = e.code;
    const sim = this.sim;
    if (GAME_KEYS.has(code) && (sim.active || sim.phase === 'dropping')) e.preventDefault();
    if (this.h.onKey && this.h.onKey(e)) return;
    if (e.repeat && !KEYS.left.includes(code) && !KEYS.right.includes(code)) return;
    this.held.add(code);
    if (KEYS.up.includes(code)) sim.climbUp();
    else if (KEYS.down.includes(code)) sim.climbDown();
    else if (KEYS.action.includes(code)) sim.action();
    else if (KEYS.pause.includes(code)) this.h.onPause?.();
    this.sync();
  }

  onKeyUp(e) {
    this.held.delete(e.code);
    this.sync();
  }

  releaseAll() {
    this.held.clear();
    this.touchDir = { left: false, right: false, up: false, down: false };
    this.sync();
  }

  any(list) {
    return list.some((k) => this.held.has(k));
  }

  sync() {
    const i = this.sim.input;
    i.left = this.any(KEYS.left) || this.touchDir.left;
    i.right = this.any(KEYS.right) || this.touchDir.right;
    i.up = this.any(KEYS.up) || this.touchDir.up;
    i.down = this.any(KEYS.down) || this.touchDir.down;
  }

  /** Wire the on-screen D-pad and action button. */
  bindTouch(pad, actionBtn) {
    const pointers = new Map();
    const recompute = () => {
      const d = { left: false, right: false, up: false, down: false };
      for (const v of pointers.values()) Object.assign(d, Object.fromEntries(Object.entries(v).filter(([, on]) => on)));
      const was = this.touchDir;
      this.touchDir = d;
      if (d.up && !was.up) this.sim.climbUp();
      if (d.down && !was.down) this.sim.climbDown();
      pad.dataset.dir = Object.keys(d).filter((k) => d[k]).join(' ');
      this.sync();
    };
    const dirFor = (e) => {
      const r = pad.getBoundingClientRect();
      const x = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
      const y = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
      const d = { left: false, right: false, up: false, down: false };
      if (Math.hypot(x, y) < 0.18) return d;
      const ang = Math.atan2(y, x);
      // 8-way with generous horizontal sectors: walking matters most
      const deg = (ang * 180) / Math.PI;
      if (deg > -60 && deg < 60) d.right = true;
      if (deg > 120 || deg < -120) d.left = true;
      if (deg < -30 && deg > -150) d.up = true;
      if (deg > 30 && deg < 150) d.down = true;
      return d;
    };
    pad.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      try {
        pad.setPointerCapture(e.pointerId);
      } catch {
        /* capture is a nicety (keeps tracking off-pad); movement works without it */
      }
      pointers.set(e.pointerId, dirFor(e));
      this.h.onTouchStart?.();
      recompute();
    });
    pad.addEventListener('pointermove', (e) => {
      if (!pointers.has(e.pointerId)) return;
      pointers.set(e.pointerId, dirFor(e));
      recompute();
    });
    const end = (e) => {
      pointers.delete(e.pointerId);
      recompute();
    };
    pad.addEventListener('pointerup', end);
    pad.addEventListener('pointercancel', end);
    pad.addEventListener('lostpointercapture', end);
    pad.addEventListener('contextmenu', (e) => e.preventDefault());

    actionBtn.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      actionBtn.classList.add('is-down');
      this.h.onTouchStart?.();
      this.sim.action();
    });
    const up = () => actionBtn.classList.remove('is-down');
    actionBtn.addEventListener('pointerup', up);
    actionBtn.addEventListener('pointercancel', up);
    actionBtn.addEventListener('pointerleave', up);
    actionBtn.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  destroy() {
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    window.removeEventListener('blur', this.onBlur);
  }
}
