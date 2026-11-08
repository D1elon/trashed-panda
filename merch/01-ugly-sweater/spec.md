# The Ugly Trash Panda Sweater

**Retail:** $64  ·  **Shop id:** `ugly-sweater`

## Design

A real fair-isle chart: a yoke of trees and stars, the Santa Panda framed by snowflakes and bottles over the words HOLIDAY SPIRITS (the sale poster pun from the game), a bottle hem band, TRASHED PANDA across the back, and sleeves ringed like a raccoon tail.

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

| Colourway | Base | Cream | Dark brown | Accent |
| --- | --- | --- | --- | --- |
| Red | `#b3262e` | `#efe6d2` | `#2e2019` | `#24553a` |
| Green | `#24553a` | `#efe6d2` | `#2e2019` | `#b3262e` |

Pick the nearest of Printful's yarn colours to each hex. Base, collar and hem must be among the 4; the charts already use dark brown for the hem band so collar/cuffs/hem can all be dark brown.

### Notes

- Upload each chart in the knitwear Design Maker with **Pixelated** rendering, so every cell becomes one block of stitches.
- Charts are drawn so the accent colour never sits directly next to the base colour (red/green blur together at stitch level); the build checks this.
- If the template's panel is larger than the chart, scale the chart up evenly and fill the remaining area with the base colour or the all-over tile.

### Before you publish

- [ ] Upload the files above and check the provider's preview matches `mockups/`.
- [ ] Order one sample.
- [ ] Copy the variant IDs into `js/shop/catalog.js`.
