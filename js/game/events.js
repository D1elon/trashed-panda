// Minimal synchronous event bus shared by the sim, renderer, audio and UI.
export class Bus {
  constructor() {
    this.map = new Map();
  }

  on(name, fn) {
    if (!this.map.has(name)) this.map.set(name, new Set());
    this.map.get(name).add(fn);
    return () => this.map.get(name)?.delete(fn);
  }

  emit(name, payload) {
    const set = this.map.get(name);
    if (!set) return;
    for (const fn of set) {
      try {
        fn(payload);
      } catch (err) {
        console.error(`[bus] "${name}" handler failed`, err);
      }
    }
  }
}
