# The Ugly Trash Panda Sweater

**Retail:** $64  ·  **Shop id:** `ugly-sweater`

## Design

One big face: the game's own raccoon head knitted at two stitches per pixel across the chest, in real raccoon colours (charcoal mask, grey fur, cream brows and muzzle), wearing a Santa hat in the sweater's own colour. A ringed-tail band runs across the yoke, TRASHED PANDA sits on the back, and both sleeves are ringed charcoal and grey exactly like the tail.

## Production

| | |
| --- | --- |
| Recommended blank | Printful knitwear: Unisex Classic Fit Knitted Crew Neck Sweater |
| Technique | Jacquard knitting (knitwear) |
| Variants | Colourways: Red, Green. Sizes: S-3XL. |

### Placements

| Placement | File | Size / position |
| --- | --- | --- |
| Front | `front-<colour>-chart-1x.png` | full front panel |
| Back | `back-<colour>-chart-1x.png` | full back panel |
| Sleeves | `sleeve-<colour>-chart-1x.png` | both sleeves |

### Files (`print/`)

| File | Pixels | Notes |
| --- | --- | --- |
| `front-red-chart-1x.png` | 68 x 88 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `front-red-20x.png` | 1360 x 1760 | Same chart enlarged for viewing and for templates that want large files. |
| `back-red-chart-1x.png` | 68 x 88 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `back-red-20x.png` | 1360 x 1760 | Same chart enlarged for viewing and for templates that want large files. |
| `sleeve-red-chart-1x.png` | 30 x 84 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `sleeve-red-20x.png` | 600 x 1680 | Same chart enlarged for viewing and for templates that want large files. |
| `all-over-tile-red.png` | 480 x 480 | Seamless fill for any extra panels (collar, pocket, hood). |
| `front-green-chart-1x.png` | 68 x 88 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `front-green-20x.png` | 1360 x 1760 | Same chart enlarged for viewing and for templates that want large files. |
| `back-green-chart-1x.png` | 68 x 88 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `back-green-20x.png` | 1360 x 1760 | Same chart enlarged for viewing and for templates that want large files. |
| `sleeve-green-chart-1x.png` | 30 x 84 | Knit chart, 1 cell = 1 stitch group. Upload in Pixelated mode. |
| `sleeve-green-20x.png` | 600 x 1680 | Same chart enlarged for viewing and for templates that want large files. |
| `all-over-tile-green.png` | 480 x 480 | Seamless fill for any extra panels (collar, pocket, hood). |

### Yarn colours (4 per colourway)

| Colourway | Base | Cream | Charcoal | Fur grey |
| --- | --- | --- | --- | --- |
| Red | `#b3262e` | `#efe6d2` | `#2b2522` | `#8d8578` |
| Green | `#24553a` | `#efe6d2` | `#2b2522` | `#8d8578` |

Pick the nearest of Printful's yarn colours to each hex. Base, collar and hem must be among the 4; the charts already use charcoal for the hem band and cuffs, so collar/cuffs/hem can all be charcoal.

### Notes

- Upload each chart in the knitwear Design Maker with **Pixelated** rendering, so every cell becomes one block of stitches.
- Charts are drawn so the fur grey never sits directly next to the base colour (a mid grey blurs into red or green at stitch level): it is always fenced in by charcoal. The build checks this.
- If the template's panel is larger than the chart, scale the chart up evenly and fill the remaining area with the base colour or the all-over tile.

### Before you publish

- [ ] Upload the files above and check the provider's preview matches `mockups/`.
- [ ] Order one sample.
- [ ] Copy the variant IDs into `js/shop/catalog.js`.
