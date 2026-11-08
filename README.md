# Trashed Panda

**[trashedpanda.lol](https://www.trashedpanda.lol)**: a 60-second pixel-art arcade game based on
the true story of the raccoon who fell through the ceiling of the Ashland, VA ABC store on
Thanksgiving weekend 2025, smashed the shelves, and passed out in the bathroom.
This is the **Holiday Edition**, with a merch shop.

## What's here

| | |
| --- | --- |
| `index.html` | The game, plus the true story and a teaser for the holiday drop |
| `shop/` | The holiday merch store (see [docs/SHOP_SETUP.md](docs/SHOP_SETUP.md) to take orders) |
| `js/game/` | Game engine: simulation, canvas renderer, synthesized audio, input, UI |
| `js/shop/` | Store catalog (`catalog.js`) and storefront logic |
| `css/` | Shared pixel design system (`site.css`) and page styles |
| `assets/` | Generated sprites, UI art, product mockups and fonts |
| `merch/print-files/` | Print-ready artwork for every product (not deployed) |
| `tools/` | Python pipeline that generates every image from the source art (not deployed) |

No build step and no dependencies: it's static HTML, CSS and ES modules, served as-is by
GitHub Pages.

## Run it locally

ES modules need a web server (opening the file directly won't work):

```bash
python3 -m http.server 8000
```

Then visit <http://localhost:8000>.

## How to play

* **Move:** ← → or A D. **Climb:** ↑ ↓ or W S (hold to keep climbing)
* **Swipe / drink:** Space or E. Swipe bottles off a shelf, drink the puddles on the floor.
* Smash bottles back to back for a **combo** (up to x3).
* Drinking raises your **buzz**, which multiplies every point (up to x3). Hit 100% and you
  black out for three seconds.
* Smash a **Holiday Reserve** bottle for +5 seconds. Emptied shelves restock.
* On phones: D-pad plus a context-sensitive paw button.

## Regenerating the art

Every image in `assets/` is generated from the original high-resolution art in
`tools/source-art/` by a small Pillow pipeline. It snaps all sprites onto one shared pixel grid,
repaints the raccoon on a curated palette, draws the store and its holiday decorations, and
renders the merch mockups and print files.

```bash
pip install pillow numpy
bash tools/build_all.sh
```

## Credits

Game, art direction and story adaptation by [D1elon](https://github.com/D1elon).
Fonts: Press Start 2P (CodeMan38) and Pixelify Sans (Stefie Justprince), both under the SIL Open
Font License (see `assets/fonts/OFL.txt`). Music: chiptune arrangements of public-domain carols
("Jingle Bells", "Carol of the Bells"), synthesized live in the browser.

Trashed Panda is a fan project and is not affiliated with Virginia ABC or Hanover County.
