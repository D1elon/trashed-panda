// Home page: the hero (best score, pixel snow, the strolling raccoon), the holiday-drop
// teaser and the cart badge in the nav. The game itself lives on its own page, /play/.

import { PRODUCTS, productById, imageFor, formatPrice } from './shop/catalog.js';
import { cart, bindCartBadges } from './shared/cart.js';
import { shopOpen, applyShopState } from './shared/launch.js';
import { pixelSnow } from './shared/snow.js';
import { bestScore } from './game/storage.js';

applyShopState();

// Drop cart lines for products that no longer exist, so the badge count stays honest.
for (const l of cart.lines) if (!productById(l.productId)) cart.remove(l.id);
bindCartBadges();

// ---------------------------------------------------------------- hero
pixelSnow(document.getElementById('hero-snow'));

const best = bestScore();
if (best !== null) {
  document.getElementById('home-best-val').textContent = best.toLocaleString();
  document.getElementById('home-best').hidden = false;
}

// The raccoon strolls at 44 art px/s (two thirds of its in-game walking speed, matched by
// a slower walk cycle in css/home.css) whatever the screen width.
const hero = document.querySelector('.home-hero');
if (hero) {
  const pace = () => {
    const k = parseFloat(getComputedStyle(hero).getPropertyValue('--k')) || 1;
    const distance = hero.clientWidth + 80 * k;
    hero.style.setProperty('--stroll', `${(distance / (44 * k)).toFixed(2)}s`);
  };
  new ResizeObserver(pace).observe(hero);
}

// ---------------------------------------------------------------- holiday drop teaser
// Product cards only while the shop is open; otherwise the teaser says "coming soon".
const FEATURED = ['ugly-sweater', 'mugshot-tee', 'pixel-ornament'];
const grid = document.getElementById('teaser-grid');
if (grid && shopOpen) {
  grid.innerHTML = FEATURED.map((id) => PRODUCTS.find((p) => p.id === id))
    .filter(Boolean)
    .map((p) => {
      const img = imageFor(p);
      return `
        <a class="card" href="shop/#p=${p.id}">
          <span class="card__art" style="--art-bg:${img.bg}"><img src="${img.src}" width="160" height="160" alt="${p.name}" loading="lazy" /></span>
          <span class="card__body">
            <span class="card__name">${p.name}</span>
            <span class="card__meta"><span class="card__price">${formatPrice(p.price)}</span></span>
          </span>
        </a>`;
    })
    .join('');
}
