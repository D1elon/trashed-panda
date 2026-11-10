# Mugshot Tee

**Retail:** $32  ·  **Shop id:** `mugshot-tee`

## Design

The booking photo. The raccoon stands against a height chart in its Santa hat, holding a placard that reads ASHLAND VA, NOV 2025. Verdict underneath: GUILTY of poor life choices.

## Production

| | |
| --- | --- |
| Recommended blank | Printful: Unisex Staple T-Shirt (Bella + Canvas 3001) |
| Technique | DTG |
| Variants | Black, Forest, Heather Oatmeal. Sizes: S-3XL. |

### Placements

| Placement | File | Size / position |
| --- | --- | --- |
| Front | `front-<garment>-garment.png` | 12 x 16 in print area, art 10.93 x 11.89 in, top-aligned (about 3 in below collar) |

### Files (`print/`)

| File | Pixels | Notes |
| --- | --- | --- |
| `front-black-garment.png` | 3600 x 4800 | Black tees. Near-black outline knocked out. Art 10.93 in wide, top of print area. |
| `front-forest-garment.png` | 3600 x 4800 | Forest tees. Dark outline kept (it shows on green). |
| `front-oatmeal-garment.png` | 3600 x 4800 | Heather Oatmeal tees. Dark ink version. |
| `artwork-only-light.png` | 3280 x 3567 | Trimmed artwork for templates with a different print area. |

### Notes

- Use the file that matches the garment colour (three files, one per colour).
- The black-garment file has near-black pixels removed so the shirt itself forms the outline: softer print, no wasted ink.

### Before you publish

- [ ] Upload the files above and check the provider's preview matches `mockups/`.
- [ ] Order one sample.
- [ ] Copy the variant IDs into `js/shop/catalog.js`.
