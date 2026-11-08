// Home page extras: cart badge in the nav and the holiday-drop teaser under the game.

import { PRODUCTS, imageFor, formatPrice } from './shop/catalog.js';
import { bindCartBadges } from './shared/cart.js';

bindCartBadges();

const FEATURED = ['ugly-sweater', 'pixel-ornament', 'naughty-list-tee', 'poor-life-choices-mug'];
const grid = document.getElementById('teaser-grid');
if (grid) {
  grid.innerHTML = FEATURED.map((id) => PRODUCTS.find((p) => p.id === id))
    .filter(Boolean)
    .map((p) => {
      const img = imageFor(p);
      return `
        <a class="card" href="shop/#p=${p.id}">
          <span class="card__art" style="--art-bg:${img.bg}"><img src="${img.src}" width="128" height="128" alt="${p.name}" loading="lazy" /></span>
          <span class="card__body">
            <span class="card__name">${p.name}</span>
            <span class="card__meta"><span class="card__price">${formatPrice(p.price)}</span></span>
          </span>
        </a>`;
    })
    .join('');
}
