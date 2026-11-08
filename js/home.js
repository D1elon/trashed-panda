// Home page extras: cart badge in the nav and the holiday-drop teaser under the game.

import { PRODUCTS, productById, imageFor, formatPrice } from './shop/catalog.js';
import { cart, bindCartBadges } from './shared/cart.js';
import { shopOpen, applyShopState } from './shared/launch.js';

applyShopState();

// Drop cart lines for products that no longer exist, so the badge count stays honest.
for (const l of cart.lines) if (!productById(l.productId)) cart.remove(l.id);
bindCartBadges();

// Product cards only while the shop is open; otherwise the teaser says "coming soon".
const FEATURED = ['ugly-sweater', 'naughty-list-tee', 'pixel-ornament'];
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
