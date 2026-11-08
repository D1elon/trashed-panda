// Holiday shop: product grid, product detail, cart drawer and checkout handoff.

import { STORE, PRODUCTS, CATEGORIES, productById, defaultOptions, visualOption, imageFor, designFor, variantLabel, formatPrice } from './catalog.js';
import { cart, bindCartBadges, lineKey } from '../shared/cart.js';

const $ = (sel, root = document) => root.querySelector(sel);
const ICONS = new URL('../../assets/ui/icons.svg', import.meta.url).href;
const icon = (name) => `<svg class="ico" aria-hidden="true"><use href="${ICONS}#i-${name}" /></svg>`;
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

let filter = 'all';

// ---------------------------------------------------------------- grid
function renderChips() {
  const el = $('#chips');
  el.innerHTML = CATEGORIES.map(
    (c) => `<button type="button" class="chip" data-cat="${c.id}" aria-pressed="${c.id === filter}">${esc(c.label)}</button>`,
  ).join('');
  el.addEventListener('click', (e) => {
    const b = e.target.closest('[data-cat]');
    if (!b) return;
    filter = b.dataset.cat;
    for (const c of el.querySelectorAll('.chip')) c.setAttribute('aria-pressed', String(c.dataset.cat === filter));
    renderGrid();
  });
}

function swatches(p) {
  const key = visualOption(p);
  if (!key || key !== 'Color') return '';
  return `<span class="swatches" aria-label="${p.options.Color.length} colours">${p.options.Color.map((o) => `<i style="--sw:${o.swatch}" title="${esc(o.value)}"></i>`).join('')}</span>`;
}

function cardHtml(p) {
  const img = imageFor(p);
  return `
    <a class="card" href="#p=${p.id}" data-product="${p.id}">
      <span class="card__art" style="--art-bg:${img.bg}">
        <img src="${img.src}" width="128" height="128" alt="${esc(p.name)}" loading="lazy" />
        ${p.badge ? `<span class="tag tag--gold card__badge">${esc(p.badge)}</span>` : ''}
      </span>
      <span class="card__body">
        <span class="card__name">${esc(p.name)}</span>
        <span class="card__blurb">${esc(p.blurb)}</span>
        <span class="card__meta"><span class="card__price">${formatPrice(p.price)}</span>${swatches(p)}</span>
      </span>
    </a>`;
}

function renderGrid() {
  const list = PRODUCTS.filter((p) => filter === 'all' || p.category === filter);
  $('#grid').innerHTML = list.map(cardHtml).join('');
}

// ---------------------------------------------------------------- product detail
const pdp = $('#pdp');
let current = null;

function openProduct(id, { push = true } = {}) {
  const p = productById(id);
  if (!p) return;
  current = { p, options: defaultOptions(p), qty: 1, view: 'product' };
  renderProduct();
  if (!pdp.open) pdp.showModal();
  if (push) history.replaceState(null, '', `#p=${id}`);
}

function renderProduct() {
  const { p, options, qty, view } = current;
  const img = imageFor(p, options);
  const design = designFor(p, options);
  const optionHtml = Object.entries(p.options)
    .filter(([, vals]) => vals.length > 1 || typeof vals[0] === 'object')
    .map(([name, vals]) => {
      const visual = typeof vals[0] === 'object';
      const buttons = vals
        .map((v) => {
          const value = visual ? v.value : v;
          const sel = options[name] === value;
          return visual
            ? `<button type="button" class="opt opt--visual" data-opt="${esc(name)}" data-val="${esc(value)}" aria-pressed="${sel}" title="${esc(value)}"><img src="${imageFor(p, { ...options, [name]: value }).src}" width="128" height="128" alt="" /><span>${esc(value)}</span></button>`
            : `<button type="button" class="opt" data-opt="${esc(name)}" data-val="${esc(value)}" aria-pressed="${sel}">${esc(value)}</button>`;
        })
        .join('');
      return `<fieldset class="opts"><legend>${esc(name)}<b>${esc(options[name])}</b></legend><div class="opts__row${visual ? ' opts__row--visual' : ''}">${buttons}</div></fieldset>`;
    })
    .join('');
  const fixed = Object.entries(p.options).filter(([, vals]) => vals.length === 1 && typeof vals[0] === 'string').map(([, v]) => v[0]);

  pdp.innerHTML = `
    <div class="pdp__inner">
      <button class="icon-btn pdp__close" type="button" data-close aria-label="Close">${icon('close')}</button>
      <div class="pdp__media" style="--art-bg:${view === 'design' ? img.designBg : img.bg}">
        <img class="pdp__img" src="${view === 'design' && design ? design : img.src}" alt="${esc(p.name)}${view === 'design' ? ' design' : ''}" data-view="${view}" />
        ${design ? `<div class="seg" role="group" aria-label="Preview"><button type="button" data-view="product" aria-pressed="${view === 'product'}">Product</button><button type="button" data-view="design" aria-pressed="${view === 'design'}">Design</button></div>` : ''}
      </div>
      <div class="pdp__info">
        ${p.badge ? `<span class="tag tag--gold">${esc(p.badge)}</span>` : ''}
        <h2 class="pdp__title" id="pdp-title">${esc(p.name)}</h2>
        <p class="pdp__price">${formatPrice(p.price)}${fixed.length ? ` <small>${esc(fixed.join(' · '))}</small>` : ''}</p>
        <p class="pdp__desc">${esc(p.description)}</p>
        ${optionHtml}
        <div class="buy">
          <div class="qty" role="group" aria-label="Quantity">
            <button type="button" data-qty="-1" aria-label="Decrease quantity">${icon('minus')}</button>
            <output aria-live="polite">${qty}</output>
            <button type="button" data-qty="1" aria-label="Increase quantity">${icon('plus')}</button>
          </div>
          <button class="btn btn--holiday btn--lg buy__add" type="button" data-add>Add to cart · ${formatPrice(p.price * qty)}</button>
        </div>
        <ul class="pdp__details">${p.details.map((d) => `<li>${icon('check')}${esc(d)}</li>`).join('')}</ul>
      </div>
    </div>`;
  if (view === 'design') requestAnimationFrame(fitDesign);
}

// Flat designs have arbitrary sizes: show them at the largest whole-number scale that fits.
function fitDesign() {
  const img = $('.pdp__img[data-view="design"]', pdp);
  if (!img) return;
  const apply = () => {
    const box = img.parentElement.getBoundingClientRect();
    const k = Math.max(1, Math.floor(Math.min((box.width - 48) / img.naturalWidth, (box.height - 120) / img.naturalHeight, 6)));
    img.style.width = `${img.naturalWidth * k}px`;
    img.style.height = `${img.naturalHeight * k}px`;
  };
  if (img.complete && img.naturalWidth) apply();
  else img.addEventListener('load', apply, { once: true });
}

pdp.addEventListener('click', (e) => {
  if (e.target === pdp) return pdp.close();
  const t = e.target.closest('button');
  if (!t || !current) return;
  if (t.hasAttribute('data-close')) return pdp.close();
  if (t.dataset.opt) {
    current.options[t.dataset.opt] = t.dataset.val;
    const keepFocus = `[data-opt="${t.dataset.opt}"][data-val="${t.dataset.val}"]`;
    renderProduct();
    $(keepFocus, pdp)?.focus();
  } else if (t.dataset.view) {
    current.view = t.dataset.view;
    renderProduct();
    $(`.seg [data-view="${current.view}"]`, pdp)?.focus();
  } else if (t.dataset.qty) {
    current.qty = Math.max(1, Math.min(20, current.qty + Number(t.dataset.qty)));
    renderProduct();
    $(`[data-qty="${t.dataset.qty}"]`, pdp)?.focus();
  } else if (t.hasAttribute('data-add')) {
    cart.add(current.p.id, { ...current.options }, current.qty);
    pdp.close();
    openCart();
  }
});

pdp.addEventListener('close', () => {
  if (location.hash.startsWith('#p=')) history.replaceState(null, '', location.pathname + location.search);
});

// ---------------------------------------------------------------- cart
const drawer = $('#cart');

function openCart() {
  renderCart();
  if (!drawer.open) drawer.showModal();
}

function lineHtml(l) {
  const p = productById(l.productId);
  if (!p) return '';
  const img = imageFor(p, l.options);
  const label = variantLabel(l.options);
  return `
    <li class="line" data-line="${esc(l.id)}">
      <span class="line__art" style="--art-bg:${img.bg}"><img src="${img.src}" width="128" height="128" alt="" /></span>
      <span class="line__info">
        <span class="line__name">${esc(p.name)}</span>
        ${label ? `<span class="line__opts">${esc(label)}</span>` : ''}
        <span class="line__row">
          <span class="qty qty--sm" role="group" aria-label="Quantity for ${esc(p.name)}">
            <button type="button" data-step="-1" aria-label="Decrease">${icon('minus')}</button>
            <output>${l.qty}</output>
            <button type="button" data-step="1" aria-label="Increase">${icon('plus')}</button>
          </span>
          <button type="button" class="line__remove" data-remove>Remove</button>
        </span>
      </span>
      <span class="line__price">${formatPrice(p.price * l.qty)}</span>
    </li>`;
}

function subtotal() {
  return cart.lines.reduce((sum, l) => sum + (productById(l.productId)?.price ?? 0) * l.qty, 0);
}

function renderCart() {
  const lines = cart.lines.filter((l) => productById(l.productId));
  const body = $('#cart-body');
  const foot = $('#cart-foot');
  if (!lines.length) {
    body.innerHTML = `
      <div class="empty">
        <img src="../assets/shop/design-passed-out.png" alt="" width="70" height="48" />
        <p><b>Your cart is empty.</b><br />The raccoon took everything.</p>
        <button class="btn btn--primary" type="button" data-close>Keep shopping</button>
      </div>`;
    foot.innerHTML = '';
    return;
  }
  body.innerHTML = `<ul class="lines">${lines.map(lineHtml).join('')}</ul>`;
  foot.innerHTML = `
    <div class="sum"><span>Subtotal</span><b>${formatPrice(subtotal())}</b></div>
    <p class="sum__note">Shipping and taxes are calculated at checkout.${STORE.orderByNote ? ` ${esc(STORE.orderByNote)}` : ''}</p>
    <button class="btn btn--holiday btn--lg btn--block" type="button" data-checkout>Checkout</button>`;
}

drawer.addEventListener('click', (e) => {
  if (e.target === drawer) return drawer.close();
  const t = e.target.closest('button');
  if (!t) return;
  if (t.hasAttribute('data-close')) return drawer.close();
  const line = t.closest('[data-line]');
  if (line) {
    const id = line.dataset.line;
    const l = cart.lines.find((x) => x.id === id);
    if (t.dataset.step && l) cart.setQty(id, l.qty + Number(t.dataset.step));
    if (t.hasAttribute('data-remove')) cart.remove(id);
    renderCart();
    const again = $(`[data-line="${CSS.escape(id)}"] [data-step="${t.dataset.step}"]`, drawer);
    (again || $('[data-checkout], [data-close]', drawer))?.focus();
    return;
  }
  if (t.hasAttribute('data-checkout')) checkout();
});

drawer.addEventListener('close', () => {
  if (location.hash === '#cart') history.replaceState(null, '', location.pathname + location.search);
});

// ---------------------------------------------------------------- checkout
function shopifyVariantId(p, options) {
  const key = Object.values(options).join(' / ');
  return p.shopify?.[key] || null;
}

function checkout() {
  const lines = cart.lines;
  const c = STORE.checkout;
  if (c.provider === 'shopify' && c.shopifyDomain) {
    const parts = [];
    for (const l of lines) {
      const p = productById(l.productId);
      const id = p && shopifyVariantId(p, l.options);
      if (!id) {
        showNotice('Almost there', `“${p ? p.name : l.productId}” in ${variantLabel(l.options) || 'this option'} isn’t available to order yet. Remove it to check out the rest.`);
        return;
      }
      parts.push(`${encodeURIComponent(id)}:${l.qty}`);
    }
    window.location.href = `https://${c.shopifyDomain}/cart/${parts.join(',')}`;
    return;
  }
  showNotice(
    'Orders open soon',
    'The holiday drop is being printed and packed. Your cart is saved on this device, so you can come straight back and check out the moment orders open.',
    STORE.notifyUrl,
  );
}

const notice = $('#notice');
function showNotice(title, text, link) {
  notice.innerHTML = `
    <div class="notice__inner">
      <img src="../assets/ui/raccoon-face.png" width="18" height="22" alt="" />
      <h2 id="notice-title">${esc(title)}</h2>
      <p>${esc(text)}</p>
      <div class="notice__actions">
        ${link ? `<a class="btn btn--holiday" href="${esc(link)}" target="_blank" rel="noopener">Get notified</a>` : ''}
        <button class="btn btn--primary" type="button" data-close>Got it</button>
      </div>
    </div>`;
  notice.showModal();
}
notice.addEventListener('click', (e) => {
  if (e.target === notice || e.target.closest('[data-close]')) notice.close();
});

// ---------------------------------------------------------------- hero snow
function heroSnow() {
  const c = $('#hero-snow');
  if (!c || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const g = c.getContext('2d');
  const flakes = [];
  let w = 0;
  let h = 0;
  const px = 4;
  const resize = () => {
    const r = c.getBoundingClientRect();
    w = Math.ceil(r.width / px);
    h = Math.ceil(r.height / px);
    c.width = w;
    c.height = h;
  };
  new ResizeObserver(resize).observe(c);
  resize();
  for (let i = 0; i < 46; i++) flakes.push({ x: Math.random() * 400, y: Math.random() * 200, v: 4 + Math.random() * 7, p: Math.random() * 6 });
  let last = performance.now();
  const tick = (now) => {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    g.clearRect(0, 0, w, h);
    g.fillStyle = 'rgba(244, 247, 251, 0.85)';
    for (const f of flakes) {
      f.y += f.v * dt;
      f.p += dt * 1.6;
      if (f.y > h) {
        f.y = -1;
        f.x = Math.random() * w;
      }
      g.fillRect(Math.round((f.x + Math.sin(f.p) * 2) % w), Math.round(f.y), 1, 1);
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ---------------------------------------------------------------- toast
let toastT;
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastT);
  toastT = setTimeout(() => (t.hidden = true), 2200);
}

// ---------------------------------------------------------------- routing + boot
function route() {
  const h = location.hash;
  if (h === '#cart') {
    if (pdp.open) pdp.close();
    openCart();
  } else if (h.startsWith('#p=')) {
    if (drawer.open) drawer.close();
    openProduct(decodeURIComponent(h.slice(3)), { push: false });
  }
}

function boot() {
  renderChips();
  renderGrid();
  bindCartBadges();
  cart.subscribe(() => {
    if (drawer.open) renderCart();
  });
  $('#grid').addEventListener('click', (e) => {
    const a = e.target.closest('[data-product]');
    if (!a) return;
    e.preventDefault();
    openProduct(a.dataset.product);
  });
  $('#open-cart').addEventListener('click', openCart);
  for (const d of [pdp, drawer, notice]) d.addEventListener('cancel', () => d.close());
  if (STORE.orderByNote) {
    const n = $('#order-by');
    n.querySelector('span').textContent = STORE.orderByNote;
    n.hidden = false;
  }
  if (STORE.giveBack?.enabled) {
    const g = $('#giveback');
    g.querySelector('p').innerHTML = STORE.giveBack.url
      ? `${esc(STORE.giveBack.text)} <a href="${esc(STORE.giveBack.url)}" rel="noopener">Learn more</a>`
      : esc(STORE.giveBack.text);
    g.hidden = false;
  }
  window.addEventListener('hashchange', route);
  route();
  heroSnow();
  window.__shop = { cart, toast };
}

boot();
export { lineKey };
