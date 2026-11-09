// Game page extras that belong to the site rather than the game: the coming-soon switch
// for shop links (nav badge, results-screen merch link) and the cart badge.

import { applyShopState } from './shared/launch.js';
import { bindCartBadges } from './shared/cart.js';

applyShopState({ badge: false });
bindCartBadges();
