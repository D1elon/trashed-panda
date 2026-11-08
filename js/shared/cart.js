// Cart state shared by every page (persisted in localStorage, synced across tabs).

const KEY = 'trashed-panda:cart:v1';
const listeners = new Set();

function read() {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || '[]');
    return Array.isArray(v) ? v.filter((l) => l && typeof l.id === 'string' && Number.isInteger(l.qty) && l.qty > 0) : [];
  } catch {
    return [];
  }
}

let lines = read();

function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify(lines));
  } catch {
    /* storage blocked: cart lives for this page view only */
  }
  for (const fn of listeners) fn(lines);
}

window.addEventListener('storage', (e) => {
  if (e.key === KEY) {
    lines = read();
    for (const fn of listeners) fn(lines);
  }
});

/** A line is one product + variant combination. */
export function lineKey(productId, options) {
  const opt = Object.keys(options || {}).sort().map((k) => `${k}=${options[k]}`).join('&');
  return opt ? `${productId}?${opt}` : productId;
}

export const cart = {
  get lines() {
    return lines.map((l) => ({ ...l }));
  },
  get count() {
    return lines.reduce((n, l) => n + l.qty, 0);
  },
  add(productId, options = {}, qty = 1) {
    const id = lineKey(productId, options);
    const line = lines.find((l) => l.id === id);
    if (line) line.qty = Math.min(20, line.qty + qty);
    else lines.push({ id, productId, options, qty: Math.min(20, qty) });
    save();
  },
  setQty(id, qty) {
    const line = lines.find((l) => l.id === id);
    if (!line) return;
    if (qty <= 0) lines = lines.filter((l) => l.id !== id);
    else line.qty = Math.min(20, qty);
    save();
  },
  remove(id) {
    lines = lines.filter((l) => l.id !== id);
    save();
  },
  clear() {
    lines = [];
    save();
  },
  subscribe(fn) {
    listeners.add(fn);
    fn(lines);
    return () => listeners.delete(fn);
  },
};

/** Keep every [data-cart-count] badge on the page in sync. */
export function bindCartBadges(root = document) {
  let prev = cart.count;
  cart.subscribe(() => {
    const n = cart.count;
    for (const el of root.querySelectorAll('[data-cart-count]')) {
      el.textContent = String(n);
      el.hidden = n === 0;
      if (n > prev) {
        el.classList.remove('is-bump');
        void el.offsetWidth;
        el.classList.add('is-bump');
      }
    }
    prev = n;
  });
}
