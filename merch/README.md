# Trashed Panda: Holiday Drop production package

Everything needed to set the merch up with a print-on-demand provider. Each product folder holds
print-ready files (`print/`), approval mockups (`mockups/`) and a spec sheet (`spec.md`) with the
recommended blank, technique, placement and colours. `line-sheet.pdf` has the whole drop on a few pages.

Regenerate everything with `bash tools/build_all.sh` (it fails if any check below fails).

## The drop

| # | Product | Technique | Blank | Retail |
| --- | --- | --- | --- | --- |
| 01 | [The Ugly Trash Panda Sweater](01-ugly-sweater/spec.md) | Jacquard knitting (knitwear) | Printful knitwear: Unisex Classic Fit Knitted Crew Neck Sweater | $64 |
| 02 | [Mugshot Tee](02-mugshot-tee/spec.md) | DTG | Printful: Unisex Staple T-Shirt (Bella + Canvas 3001) | $32 |
| 03 | [Pixel Ornament](03-pixel-ornaments/spec.md) | Sublimation on porcelain, both sides | Printful: Ceramic Ornaments, 2-Side Print (circle, 2.99 in) | $18 |
| 04 | [Trashed Panda Hoodie](04-trashed-panda-hoodie/spec.md) | DTG, front + back | Printful: Unisex Premium Hoodie (Cotton Heritage M2580) | $58 |
| 05 | [Poor Life Choices Mug](05-poor-life-choices-mug/spec.md) | Sublimation, full wrap | Printful: White Glossy Mug, 11 oz | $18 |
| 06 | [Tail Stripe Socks](06-tail-stripe-socks/spec.md) | Sublimation, all-over | Printful: Sublimation Socks (crew) | $20 |
| 07 | [Santa Panda Beanie](07-santa-panda-beanie/spec.md) | Embroidery, front cuff | Printful: Pom-Pom Knit Cap (or Cuffed Beanie) | $30 |
| 08 | [Evidence Gift Wrap](08-gift-wrap/spec.md) | Digital print on paper | Printful: Gift Wrap Papers (or Printify Wrapping Papers) | $22 |
| 09 | [Merry Trashmas Cards](09-holiday-cards/spec.md) | Digital print | Folded greeting card, 5 x 7 in (Printful or Printify greeting cards) | $16 |
| 10 | [Kiss-Cut Stickers](10-stickers/spec.md) | Digital print on white vinyl, kiss-cut | Printful: Kiss-Cut Stickers | $6 |

## How the files are made

- **Pixel art, scaled in whole numbers.** Every file is the native pixel design enlarged by an integer factor with
  nearest-neighbour sampling, so edges stay razor sharp at any size. Never resize these files by a fraction.
- **300 dpi** for apparel, ceramics, stickers and cards; **150 dpi** for large-format gift wrap.
- **Transparent backgrounds** wherever the product colour should show through.
- **Built for the process:** knit charts use 4 yarn colours, embroidery uses 5 threads (limit 6), ornament art sits
  inside the safe circle, black-garment tees have near-black ink knocked out.

## Setting up with Printful + Shopify

1. Connect Printful to your Shopify store.
2. For each product, create it in Printful with the blank from its spec sheet and upload the files from `print/`.
3. Match the variants (colours/sizes/designs) to the ones listed in `js/shop/catalog.js`. Check each blank's current base cost and shipping before confirming the retail prices above.
4. Order a sample of each product before launch, especially the knit sweater and the embroidered beanie.
5. Copy the Shopify variant IDs into `js/shop/catalog.js` and switch checkout on (see `docs/SHOP_SETUP.md`).

Provider templates change over time and differ between providers. Each spec sheet gives physical sizes in inches,
so if a template differs, keep the artwork centred at the stated width and scale by whole numbers only.

## Pre-flight checks (all passed)

| Check | Result | Detail |
| --- | --- | --- |
| Sweater red front: yarn colours | pass | 4 of 4 allowed |
| Sweater red front: fur grey never touches base | pass | 0 contacts (mid grey on red blurs at stitch level) |
| Sweater red back: yarn colours | pass | 4 of 4 allowed |
| Sweater red back: fur grey never touches base | pass | 0 contacts (mid grey on red blurs at stitch level) |
| Sweater red sleeve: yarn colours | pass | 3 of 4 allowed |
| Sweater red sleeve: fur grey never touches base | pass | 0 contacts (mid grey on red blurs at stitch level) |
| Sweater green front: yarn colours | pass | 4 of 4 allowed |
| Sweater green front: fur grey never touches base | pass | 0 contacts (mid grey on green blurs at stitch level) |
| Sweater green back: yarn colours | pass | 4 of 4 allowed |
| Sweater green back: fur grey never touches base | pass | 0 contacts (mid grey on green blurs at stitch level) |
| Sweater green sleeve: yarn colours | pass | 3 of 4 allowed |
| Sweater green sleeve: fur grey never touches base | pass | 0 contacts (mid grey on green blurs at stitch level) |
| Tee black-garment file: near-black ink knocked out | pass | 490 px removed before scaling |
| Ornament santa-panda: artwork inside 2.6 in safe circle | pass | 0 px outside |
| Ornament top-shelf: artwork inside 2.6 in safe circle | pass | 0 px outside |
| Ornament passed-out: artwork inside 2.6 in safe circle | pass | 0 px outside |
| Ornament back: artwork inside 2.6 in safe circle | pass | 0 px outside |
| Beanie embroidery: thread colours | pass | 5 of 6 allowed |
| Beanie embroidery: smallest detail above 1.27 mm | pass | 1 pixel = 1.35 mm |
