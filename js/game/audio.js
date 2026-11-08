// All audio is synthesised with WebAudio: zero audio files to download.
// Music: chiptune arrangements of public-domain carols (Jingle Bells, 1857;
// Shchedryk / "Carol of the Bells", 1916). SFX are small procedural patches.

const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);
const SMOOTH = 0.03;

// ---------------------------------------------------------------------------
// Note data. Steps are 8th notes. [step, length, midi, voice]
// ---------------------------------------------------------------------------
function jingleBells() {
  // 4/4, 8 steps per bar, C major. Chorus, looped.
  const q = 2;
  const n = [];
  let s = 0;
  const mel = (seq) => { for (const [m, d] of seq) { if (m) n.push([s, d, m, 'lead']); s += d; } };
  const E = 76, G = 79, C = 72, D = 74, F = 77;
  const phraseA = [[E, q], [E, q], [E, q * 2], [E, q], [E, q], [E, q * 2], [E, q], [G, q], [C, 3], [D, 1], [E, q * 4]];
  mel(phraseA);
  mel([[F, q], [F, q], [F, 3], [F, 1], [F, q], [E, q], [E, q], [E, 1], [E, 1], [E, q], [D, q], [D, q], [E, q], [D, q * 2], [G, q * 2]]);
  mel(phraseA);
  mel([[F, q], [F, q], [F, 3], [F, 1], [F, q], [E, q], [E, q], [E, 1], [E, 1], [G, q], [G, q], [F, q], [D, q], [C, q * 4]]);
  const chords = ['C', 'C', 'C', 'C', 'F', 'C', 'D', 'G', 'C', 'C', 'C', 'C', 'F', 'C', 'G', 'C'];
  const roots = { C: 48, F: 41, G: 43, D: 50 };
  const fifths = { C: 55, F: 48, G: 50, D: 45 };
  chords.forEach((c, bar) => {
    for (let b = 0; b < 4; b++) n.push([bar * 8 + b * 2, 2, b % 2 ? fifths[c] : roots[c], 'bass']);
  });
  // glockenspiel sparkle on the downbeat of every other bar
  chords.forEach((c, bar) => {
    if (bar % 2 === 0) n.push([bar * 8, 4, { C: 84, F: 81, G: 83, D: 81 }[c], 'bell']);
  });
  return { bpm: 118, stepsPerBeat: 2, stepsPerBar: 8, length: 16 * 8, notes: n, drums: jingleDrums };
}

function jingleDrums(step, voices) {
  const inBar = step % 8;
  if (inBar % 2 === 0) voices.sleigh(inBar === 0 ? 0.09 : 0.06);
  else voices.sleigh(0.03);
  if (inBar === 0 || inBar === 4) voices.kick(0.22);
}

function carolOfTheBells() {
  // 3/4, 6 steps per bar, G minor. Ostinato Bb-A-Bb-G with descending bass and
  // tolling counter-lines, 16 bars.
  const n = [];
  const ost = (bar, base, voice) => {
    const s = bar * 6;
    n.push([s, 2, base, voice], [s + 2, 1, base - 1, voice], [s + 3, 1, base, voice], [s + 4, 2, base - 3, voice]);
  };
  const bass = [43, 41, 39, 38];
  for (let bar = 0; bar < 16; bar++) {
    ost(bar, 70, 'lead');                                    // Bb4 A4 Bb4 G4
    if (bar >= 4 && bar < 12) ost(bar, 74, 'lead2');          // D5 C5 D5 Bb4
    if (bar >= 12) ost(bar, 58, 'bass2');                     // ostinato in the low register
    const root = bass[bar % 4];
    n.push([bar * 6, 6, root, 'bass']);
    if (bar >= 8 && bar < 12) n.push([bar * 6, 6, [79, 77, 75, 74][bar - 8], 'bell']);  // G F Eb D tolls
    if (bar >= 12) n.push([bar * 6, 3, 79, 'bell'], [bar * 6 + 3, 3, 74, 'bell']);
  }
  return { bpm: 168, stepsPerBeat: 2, stepsPerBar: 6, length: 16 * 6, notes: n, drums: carolDrums };
}

function carolDrums(step, voices, urgent) {
  const inBar = step % 6;
  const section = Math.floor(step / 24);
  if (inBar === 0) voices.kick(0.34);
  if (section >= 2 && inBar === 4) voices.snare(0.16);
  if (urgent || inBar % 2 === 0) voices.hat(inBar % 2 === 0 ? 0.05 : 0.03);
  if (inBar % 2 === 0) voices.sleigh(section >= 1 ? 0.05 : 0.03);
}

// ---------------------------------------------------------------------------
export class Audio {
  constructor(bus, settings) {
    this.bus = bus;
    this.settings = settings;
    this.ctx = null;
    this.unlocked = false;
    this.track = null;
    this.trackName = null;
    this.want = 'title';
    this.step = 0;
    this.nextTime = 0;
    this.timer = null;
    this.buzz = 0;
    this.urgent = false;
    this.voices = 0;
    this.subscribe();
  }

  unlock() {
    if (this.ctx) {
      if (this.ctx.state !== 'running') this.ctx.resume().catch(() => {});
      return;
    }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC();
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.musicBus = ctx.createGain();
    this.sfxBus = ctx.createGain();
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.ratio.value = 4;
    this.musicBus.connect(this.master);
    this.sfxBus.connect(this.master);
    this.master.connect(comp).connect(ctx.destination);
    this.noise = makeNoise(ctx);
    this.pulse25 = makePulse(ctx, 0.25);
    this.pulse125 = makePulse(ctx, 0.125);
    this.apply(this.settings);
    this.unlocked = true;
    if (ctx.state !== 'running') ctx.resume().catch(() => {});
    this.playMusic(this.want);
  }

  apply(s) {
    this.settings = s;
    if (!this.ctx) return;
    const t = this.ctx.currentTime;
    this.master.gain.setTargetAtTime(s.muted ? 0 : 1, t, SMOOTH);
    this.musicBus.gain.setTargetAtTime(s.music * s.music * 0.55, t, SMOOTH);
    this.sfxBus.gain.setTargetAtTime(s.sfx * s.sfx * 0.9, t, SMOOTH);
  }

  suspend() {
    if (this.ctx && this.ctx.state === 'running') this.ctx.suspend().catch(() => {});
  }

  resumeCtx() {
    if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
  }

  // ------------------------------------------------------------ music
  playMusic(name) {
    this.want = name;
    if (!this.ctx) return;
    if (this.trackName === name && this.timer) return;
    this.stopMusic();
    if (!name) return;
    this.track = name === 'title' ? jingleBells() : carolOfTheBells();
    this.trackName = name;
    this.byStep = new Map();
    for (const nt of this.track.notes) {
      if (!this.byStep.has(nt[0])) this.byStep.set(nt[0], []);
      this.byStep.get(nt[0]).push(nt);
    }
    this.step = 0;
    this.nextTime = this.ctx.currentTime + 0.08;
    this.timer = setInterval(() => this.schedule(), 25);
  }

  stopMusic() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.trackName = null;
  }

  pauseMusic() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  resumeMusic() {
    if (!this.ctx || this.timer || !this.track) return;
    this.nextTime = this.ctx.currentTime + 0.06;
    this.timer = setInterval(() => this.schedule(), 25);
  }

  stepDur() {
    const tr = this.track;
    let bpm = tr.bpm;
    if (this.trackName === 'game') bpm += this.buzz * 0.14 + (this.urgent ? 16 : 0);
    return 60 / bpm / tr.stepsPerBeat;
  }

  schedule() {
    const ctx = this.ctx;
    if (!ctx || !this.track) return;
    while (this.nextTime < ctx.currentTime + 0.12) {
      const d = this.stepDur();
      const notes = this.byStep.get(this.step);
      if (notes) for (const [, len, m, v] of notes) this.note(v, m, this.nextTime, len * d);
      this.track.drums(this.step, this.drumVoices(this.nextTime), this.urgent);
      this.nextTime += d;
      this.step = (this.step + 1) % this.track.length;
    }
  }

  note(voice, midi, t, dur) {
    const ctx = this.ctx;
    const out = this.musicBus;
    const f = mtof(midi);
    const wob = this.trackName === 'game' ? this.buzz / 100 : 0;
    if (voice === 'bell') {
      for (const [mult, gain, decay] of [[1, 0.12, 1.1], [2.76, 0.04, 0.5], [5.4, 0.02, 0.25]]) {
        const o = ctx.createOscillator();
        o.type = 'sine';
        o.frequency.value = f * mult;
        const g = ctx.createGain();
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(gain, t + 0.004);
        g.gain.exponentialRampToValueAtTime(0.0001, t + decay);
        o.connect(g).connect(out);
        o.start(t);
        o.stop(t + decay + 0.05);
      }
      return;
    }
    const o = ctx.createOscillator();
    let vol = 0.1;
    if (voice === 'lead') { o.setPeriodicWave(this.pulse25); vol = 0.085; }
    else if (voice === 'lead2') { o.setPeriodicWave(this.pulse125); vol = 0.06; }
    else if (voice === 'bass') { o.type = 'triangle'; vol = 0.2; }
    else if (voice === 'bass2') { o.type = 'triangle'; vol = 0.13; }
    o.frequency.value = f;
    if (wob > 0.05 && (voice === 'lead' || voice === 'lead2')) {
      const lfo = ctx.createOscillator();
      lfo.frequency.value = 5.2;
      const lg = ctx.createGain();
      lg.gain.value = 34 * wob;
      lfo.connect(lg).connect(o.detune);
      o.detune.value = (Math.random() * 2 - 1) * 30 * wob;
      lfo.start(t);
      lfo.stop(t + dur + 0.05);
    }
    const g = ctx.createGain();
    const rel = Math.min(0.06, dur * 0.3);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.006);
    g.gain.setValueAtTime(vol * 0.8, t + Math.max(0.01, dur - rel));
    g.gain.linearRampToValueAtTime(0, t + dur);
    o.connect(g).connect(out);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  drumVoices(t) {
    const ctx = this.ctx;
    const out = this.musicBus;
    const noise = (filterType, freq, q, vol, decay, offset = Math.random()) => {
      const src = ctx.createBufferSource();
      src.buffer = this.noise;
      const fl = ctx.createBiquadFilter();
      fl.type = filterType;
      fl.frequency.value = freq;
      fl.Q.value = q;
      const g = ctx.createGain();
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(vol, t + 0.002);
      g.gain.exponentialRampToValueAtTime(0.0001, t + decay);
      src.connect(fl).connect(g).connect(out);
      src.start(t, offset);
      src.stop(t + decay + 0.02);
    };
    return {
      kick: (vol) => {
        const o = ctx.createOscillator();
        o.frequency.setValueAtTime(150, t);
        o.frequency.exponentialRampToValueAtTime(42, t + 0.11);
        const g = ctx.createGain();
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime(vol, t + 0.003);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.14);
        o.connect(g).connect(out);
        o.start(t);
        o.stop(t + 0.16);
      },
      snare: (vol) => noise('bandpass', 1900, 0.8, vol, 0.1),
      hat: (vol) => noise('highpass', 7200, 0.7, vol, 0.04),
      sleigh: (vol) => {
        noise('bandpass', 9000, 3, vol, 0.07);
        noise('bandpass', 6200, 4, vol * 0.7, 0.05);
      },
    };
  }

  // ------------------------------------------------------------ sfx
  voice(maxLife) {
    if (!this.ctx || this.voices >= 12) return null;
    this.voices++;
    const ctx = this.ctx;
    const pan = ctx.createStereoPanner ? ctx.createStereoPanner() : ctx.createGain();
    if (pan.pan) pan.pan.value = (Math.random() * 2 - 1) * 0.3;
    pan.connect(this.sfxBus);
    setTimeout(() => {
      this.voices = Math.max(0, this.voices - 1);
      try { pan.disconnect(); } catch { /* already gone */ }
    }, (maxLife + 0.3) * 1000);
    return pan;
  }

  env(t, a, d, peak) {
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
    return g;
  }

  osc(type, f, t, dur, peak, out, glideTo) {
    const o = this.ctx.createOscillator();
    if (type === 'pulse') o.setPeriodicWave(this.pulse25);
    else o.type = type;
    o.frequency.setValueAtTime(f, t);
    if (glideTo) o.frequency.exponentialRampToValueAtTime(glideTo, t + dur);
    o.connect(this.env(t, 0.004, dur, peak)).connect(out);
    o.start(t);
    o.stop(t + dur + 0.05);
    return o;
  }

  noiseHit(t, type, freq, q, dur, peak, out, sweepTo) {
    const src = this.ctx.createBufferSource();
    src.buffer = this.noise;
    const f = this.ctx.createBiquadFilter();
    f.type = type;
    f.frequency.setValueAtTime(freq, t);
    if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, t + dur);
    f.Q.value = q;
    src.connect(f).connect(this.env(t, 0.004, dur, peak)).connect(out);
    src.start(t, Math.random());
    src.stop(t + dur + 0.05);
  }

  sfx(name, arg) {
    const out = this.voice(1.2);
    if (!out) return;
    const t = this.ctx.currentTime;
    const r = 0.85 + Math.random() * 0.3;
    switch (name) {
      case 'break': {
        this.noiseHit(t, 'highpass', 2600 * r, 0.8, 0.28, 0.85, out);
        this.noiseHit(t, 'lowpass', 500, 0.7, 0.08, 0.5, out);
        const n = 4 + Math.floor(Math.random() * 3);
        for (let i = 0; i < n; i++) this.osc('sine', (2400 + Math.random() * 3600) * r, t + 0.01 + Math.random() * 0.1, 0.1, 0.18, out);
        break;
      }
      case 'slurp': {
        this.noiseHit(t, 'bandpass', 500, 6, 0.38, 0.4, out, 1400);
        this.osc('sine', 260, t + 0.28, 0.14, 0.2, out, 640);
        break;
      }
      case 'climb': this.noiseHit(t, 'bandpass', 1800 + Math.random() * 600, 3, 0.07, 0.28, out); break;
      case 'land': {
        const hard = arg;
        this.osc('sine', hard ? 160 : 120, t, hard ? 0.26 : 0.12, hard ? 0.8 : 0.4, out, hard ? 38 : 55);
        if (hard) this.noiseHit(t, 'lowpass', 900, 0.7, 0.14, 0.35, out);
        break;
      }
      case 'swipe': this.noiseHit(t, 'bandpass', 2800, 1.4, 0.16, 0.5, out, 420); break;
      case 'fall': {
        const o = this.osc('sine', 1000, t, 0.5, 0.32, out, 220);
        const lfo = this.ctx.createOscillator();
        lfo.frequency.value = 9;
        const lg = this.ctx.createGain();
        lg.gain.value = 24;
        lfo.connect(lg).connect(o.frequency);
        lfo.start(t);
        lfo.stop(t + 0.55);
        break;
      }
      case 'blip': this.osc('pulse', 440, t, 0.09, 0.3, out); break;
      case 'go': this.osc('pulse', 660, t, 0.08, 0.3, out); this.osc('pulse', 880, t + 0.08, 0.24, 0.3, out); break;
      case 'combo': {
        const c = Math.min(Math.max(arg, 0), 12);
        const base = 520 * Math.pow(2, c / 12);
        [1, 1.25, 1.5].forEach((m, i) => this.osc('pulse', base * m, t + i * 0.045, 0.11, 0.17, out));
        break;
      }
      case 'coin': this.osc('pulse', 987.77, t, 0.07, 0.2, out); this.osc('pulse', 1318.5, t + 0.07, 0.2, 0.2, out); break;
      case 'alarm': for (let i = 0; i < 2; i++) this.osc('square', 1180, t + i * 0.14, 0.09, 0.22, out); break;
      case 'click': this.osc('pulse', 760, t, 0.04, 0.16, out); break;
      case 'tier': [0, 4, 7].forEach((st, i) => this.osc('pulse', 660 * Math.pow(2, st / 12), t + i * 0.05, 0.09, 0.14, out)); break;
      case 'bonus': {
        [0, 4, 7, 12, 16].forEach((st, i) => this.osc('pulse', 784 * Math.pow(2, st / 12), t + i * 0.055, 0.12, 0.16, out));
        for (let i = 0; i < 3; i++) this.noiseHit(t + i * 0.08, 'bandpass', 9000, 3, 0.08, 0.25, out);
        break;
      }
      case 'blackout': {
        const o = this.osc('triangle', 520, t, 0.9, 0.35, out, 70);
        const lfo = this.ctx.createOscillator();
        lfo.frequency.value = 6;
        const lg = this.ctx.createGain();
        lg.gain.value = 40;
        lfo.connect(lg).connect(o.frequency);
        lfo.start(t);
        lfo.stop(t + 0.95);
        break;
      }
      case 'hic': this.osc('sine', 540, t, 0.08, 0.25, out, 900); break;
      case 'slip': this.osc('sine', 700, t, 0.25, 0.25, out, 300); break;
      default: break;
    }
  }

  sting() {
    if (!this.ctx) return;
    const t = this.ctx.currentTime + 0.05;
    const out = this.musicBus;
    [64, 62, 60].forEach((m, i) => this.osc('pulse', mtof(m), t + i * 0.24, 0.2, 0.18, out));
    const o = this.ctx.createOscillator();
    o.setPeriodicWave(this.pulse25);
    const t2 = t + 0.72;
    o.frequency.setValueAtTime(mtof(57), t2);
    o.frequency.exponentialRampToValueAtTime(mtof(45), t2 + 0.9);
    const g = this.env(t2, 0.02, 0.95, 0.18);
    o.connect(g).connect(out);
    o.start(t2);
    o.stop(t2 + 1);
  }

  // ------------------------------------------------------------ wiring
  subscribe() {
    const b = this.bus;
    b.on('start', () => this.stopMusic());
    b.on('countdown', (n) => this.sfx(n > 0 ? 'blip' : 'blip'));
    b.on('go', () => { this.sfx('go'); this.urgent = false; this.buzz = 0; this.playMusic('game'); });
    b.on('phase', (p) => {
      if (p === 'paused') this.pauseMusic();
      else if (p === 'playing' || p === 'ready') this.resumeMusic();
      else if (p === 'title') this.playMusic('title');
    });
    b.on('timeUp', () => { this.stopMusic(); this.sting(); });
    b.on('warning', () => { this.sfx('alarm'); this.urgent = true; });
    b.on('drink', ({ buzz }) => { this.sfx('slurp'); this.buzz = buzz; setTimeout(() => this.sfx('coin'), 120); });
    b.on('buzzTier', ({ up }) => { if (up) this.sfx('tier'); });
    b.on('climb', () => this.sfx('climb'));
    b.on('land', ({ hard }) => this.sfx('land', hard));
    b.on('swipe', () => this.sfx('swipe'));
    b.on('fall', () => this.sfx('fall'));
    b.on('slip', () => this.sfx('slip'));
    b.on('break', () => this.sfx('break'));
    b.on('combo', ({ chain }) => this.sfx('combo', chain));
    b.on('timeBonus', () => this.sfx('bonus'));
    b.on('blackout', () => this.sfx('blackout'));
    b.on('wake', () => this.sfx('hic'));
    b.on('restock', () => this.sfx('bonus'));
  }

  setBuzz(v) {
    this.buzz = v;
  }
}

function makeNoise(ctx) {
  const len = Math.floor(ctx.sampleRate * 1.5);
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
  return buf;
}

/** NES-style pulse wave with the given duty cycle. */
function makePulse(ctx, duty) {
  const N = 32;
  const real = new Float32Array(N);
  const imag = new Float32Array(N);
  for (let k = 1; k < N; k++) {
    real[k] = (2 / (k * Math.PI)) * Math.sin(k * Math.PI * duty) * Math.cos(k * Math.PI * duty);
    imag[k] = (2 / (k * Math.PI)) * Math.sin(k * Math.PI * duty) * Math.sin(k * Math.PI * duty);
  }
  return ctx.createPeriodicWave(real, imag);
}
