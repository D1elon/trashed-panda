// Coming-soon switch shared by the home page and the shop (STORE.comingSoon in
// js/shop/catalog.js). Elements marked data-when="open" or data-when="soon" are shown
// for that state only; css/site.css shows the "soon" ones until this runs, which matches
// the live site and also covers visitors without JavaScript.
//
// While the shop is closed, add ?preview to any page URL to see the open shop. It is
// remembered for the browser tab; ?preview=off goes back to the public view.

import { STORE } from '../shop/catalog.js';

const KEY = 'trashed-panda:preview';

function previewing() {
  const q = new URLSearchParams(location.search).get('preview');
  const off = q === '0' || q === 'off' || q === 'false';
  try {
    if (q !== null) {
      if (off) sessionStorage.removeItem(KEY);
      else sessionStorage.setItem(KEY, '1');
    }
    return sessionStorage.getItem(KEY) === '1';
  } catch {
    return q !== null && !off; // storage blocked: honour the URL only
  }
}

export const shopOpen = !STORE.comingSoon || previewing();

/** Show/hide the data-when content. `badge: false` skips the preview badge (the game
 *  page keeps its corners free for the touch controls). */
export function applyShopState({ badge = true } = {}) {
  document.documentElement.dataset.shop = shopOpen ? 'open' : 'soon';
  if (!shopOpen && STORE.notifyUrl) {
    for (const a of document.querySelectorAll('a[data-notify]')) {
      a.href = STORE.notifyUrl;
      a.hidden = false;
    }
  }
  if (badge && shopOpen && STORE.comingSoon) previewBadge();
}

function previewBadge() {
  const url = new URL(location.href);
  url.searchParams.set('preview', 'off');
  const el = document.createElement('p');
  el.className = 'preview-badge';
  el.innerHTML = `<b>Preview</b> Visitors see “coming soon”. <a href="${url.pathname}${url.search}${url.hash}">Exit preview</a>`;
  document.body.append(el);
}
