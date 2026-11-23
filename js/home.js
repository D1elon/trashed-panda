// Home page: the hero (best score, pixel snow, the strolling raccoon). The game itself
// lives on its own page, /play/.

import { pixelSnow } from './shared/snow.js';
import { bestScore } from './game/storage.js';

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

