// Pixel snow for page heroes. The canvas runs at one pixel per `px` CSS pixels, so every
// flake is a chunky square that matches the art. It sleeps while offscreen or in a
// background tab, and stays off entirely for prefers-reduced-motion.

export function pixelSnow(canvas, { px = 4, density = 0.0028 } = {}) {
  if (!canvas || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const g = canvas.getContext('2d');
  const flakes = [];
  let w = 1;
  let h = 1;
  let raf = 0;
  let last = 0;
  let onscreen = true;

  const spawn = (f, anywhere) => {
    f.x = Math.random() * w;
    f.y = anywhere ? Math.random() * h : -1;
    f.v = 4 + Math.random() * 7;
    f.p = Math.random() * 6;
    return f;
  };

  const resize = () => {
    const r = canvas.getBoundingClientRect();
    w = Math.max(1, Math.ceil(r.width / px));
    h = Math.max(1, Math.ceil(r.height / px));
    canvas.width = w;
    canvas.height = h;
    const want = Math.max(16, Math.min(160, Math.round(w * h * density)));
    while (flakes.length < want) flakes.push(spawn({}, true));
    flakes.length = want;
  };

  const tick = (now) => {
    raf = 0;
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    g.clearRect(0, 0, w, h);
    g.fillStyle = 'rgba(244, 247, 251, 0.85)';
    for (const f of flakes) {
      f.y += f.v * dt;
      f.p += dt * 1.6;
      if (f.y > h) spawn(f, false);
      g.fillRect(Math.round((f.x + Math.sin(f.p) * 2 + w) % w), Math.round(f.y), 1, 1);
    }
    schedule();
  };

  const schedule = () => {
    if (!raf && onscreen && !document.hidden) raf = requestAnimationFrame(tick);
  };
  const wake = () => {
    last = performance.now();
    schedule();
  };

  new ResizeObserver(resize).observe(canvas);
  new IntersectionObserver(([e]) => {
    onscreen = e.isIntersecting;
    if (onscreen) wake();
  }).observe(canvas);
  document.addEventListener('visibilitychange', wake);
  resize();
  wake();
}
