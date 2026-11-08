// Settings + local leaderboard. Every storage access is guarded: private mode,
// blocked cookies or a full quota must never break the game.

const SETTINGS_KEY = 'trashed-panda:settings:v2';
const LEGACY_SETTINGS_KEY = 'trashed-panda:settings:v1';
const BOARD_KEY = 'trashed-panda:leaderboard:holiday-2026';
const BOARD_SIZE = 10;

const prefersReducedMotion = () =>
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

export function defaultSettings() {
  const reduced = prefersReducedMotion();
  return { music: 0.6, sfx: 0.8, muted: false, screenShake: !reduced, drunkFx: !reduced, santa: true, reducedMotion: reduced };
}

function read(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable: settings just won't persist */
  }
}

const unit = (v, d) => (Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : d);
const bool = (v, d) => (typeof v === 'boolean' ? v : d);

export function loadSettings() {
  const d = defaultSettings();
  const s = read(SETTINGS_KEY);
  if (s) {
    return {
      music: unit(s.music, d.music), sfx: unit(s.sfx, d.sfx), muted: bool(s.muted, d.muted),
      screenShake: bool(s.screenShake, d.screenShake), drunkFx: bool(s.drunkFx, d.drunkFx),
      santa: bool(s.santa, d.santa), reducedMotion: d.reducedMotion,
    };
  }
  const legacy = read(LEGACY_SETTINGS_KEY);
  if (legacy) {
    d.music = unit(legacy.musicVolume, d.music);
    d.sfx = unit(legacy.sfxVolume, d.sfx);
    d.muted = bool(legacy.muted, d.muted);
    d.screenShake = bool(legacy.screenShake, d.screenShake);
  }
  return d;
}

export function saveSettings(s) {
  const { reducedMotion, ...rest } = s;
  write(SETTINGS_KEY, rest);
}

const validEntry = (e) =>
  e && typeof e.name === 'string' && Number.isFinite(e.score) && typeof e.date === 'string';

export function loadBoard() {
  const b = read(BOARD_KEY);
  return Array.isArray(b) ? b.filter(validEntry).sort((a, z) => z.score - a.score).slice(0, BOARD_SIZE) : [];
}

export function qualifies(score) {
  if (score <= 0) return false;
  const b = loadBoard();
  return b.length < BOARD_SIZE || score > b[b.length - 1].score;
}

export function submitScore(entry) {
  const e = { ...entry, date: new Date().toISOString() };
  const b = [...loadBoard(), e].sort((a, z) => z.score - a.score).slice(0, BOARD_SIZE);
  write(BOARD_KEY, b);
  return { board: b, entry: e };
}

export function bestScore() {
  const b = loadBoard();
  return b.length ? b[0].score : null;
}

export function lastName() {
  try {
    return localStorage.getItem('trashed-panda:name') || '';
  } catch {
    return '';
  }
}

export function rememberName(name) {
  try {
    localStorage.setItem('trashed-panda:name', name);
  } catch {
    /* ignore */
  }
}
