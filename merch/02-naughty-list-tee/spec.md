# Naughty List Tee

**Retail:** $32  ·  **Shop id:** `naughty-list-tee`

## Design

Santa's list, already filled in: BROKE IN, SMASHED THE SHELVES, DRANK THE EVIDENCE, PASSED OUT, each one ticked in red, signed with the Santa Panda.

## Production

| | |
| --- | --- |
| Recommended blank | Printful: Unisex Staple T-Shirt (Bella + Canvas 3001) |
| Technique | DTG |
| Variants | Black, Forest, Heather Oatmeal. Sizes: S-3XL. |

### Placements

| Placement | File | Size / position |
| --- | --- | --- |
| Front | `front-<garment>-garment.png` | 12 x 16 in print area, art 10.89 x 7.85 in, top-aligned (about 3 in below collar) |

### Files (`print/`)

| File | Pixels | Notes |
| --- | --- | --- |
| `front-black-garment.png` | 3600 x 4800 | Black tees. Cream ink, near-black outline knocked out. Art 10.89 in wide, top of print area. |
| `front-forest-garment.png` | 3600 x 4800 | Forest tees. Cream ink with dark outline kept (it shows on green). |
| `front-oatmeal-garment.png` | 3600 x 4800 | Heather Oatmeal tees. Dark ink version. |
| `artwork-only-light.png` | 3268 x 2356 | Trimmed artwork for templates with a different print area. |

### Notes

- Use the file that matches the garment colour (three files, one per colour).
- The black-garment file has near-black pixels removed so the shirt itself forms the outline: softer print, no wasted ink.

### Before you publish

- [ ] Upload the files above and check the provider's preview matches `mockups/`.
- [ ] Order one sample.
- [ ] Copy the variant IDs into `js/shop/catalog.js`.
