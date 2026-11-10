# Opening the holiday shop

The shop at `/shop/` is fully built: products, variants, cart and checkout button.
Everything you need to change lives in **`js/shop/catalog.js`**.

## 0. Coming soon (the live default)

While `STORE.comingSoon` is `true`, the live site says the holiday drop is **coming soon**:

* `/shop/` shows the hero and a "coming soon" message. No products, cart or FAQ, and old
  product or cart links (`#p=...`, `#cart`) land on that page.
* The home page teaser, the nav badge and the link on the game-over screen say "coming
  soon" and link to no products.
* If you set `notifyUrl`, a **Get notified** button appears on both pages.

To review the full shop while it is hidden, add **`?preview`** to any URL
(e.g. `https://www.trashedpanda.lol/shop/?preview`). A yellow badge marks preview mode; it
is remembered for that browser tab, and **Exit preview** (or `?preview=off`) goes back to
the public view. Anyone who knows the trick can use it, so treat it as a curtain, not a lock.

When you're ready, set `comingSoon: false` and deploy. If checkout isn't connected yet,
the shop then runs in **pre-launch mode**: everything is browsable, carts are saved on the
visitor's device, and the Checkout button explains that orders open soon.

## 1. Pick how orders get fulfilled

Everything is designed for print-on-demand, so you never hold inventory. The shop hands
the cart to **Shopify** at checkout, and Shopify talks to the print company:

1. Create a Shopify store. The cheapest plan is enough, since your site is the storefront.
2. Install **Printful** or **Printify** from the Shopify app store.
3. In Printful/Printify, create each product from the **production package** in `merch/`.
   Every product has a folder with print-ready files (`print/`), approval mockups
   (`mockups/`) and a `spec.md` naming the recommended blank, technique, placement,
   sizes and colours. Start with [`merch/README.md`](../merch/README.md); `merch/line-sheet.pdf`
   has the whole drop on a few printable pages.
   Use the same option names and values as `catalog.js` (Color: Red/Green, Size: S..3XL,
   and so on) so they're easy to match up.
4. Check each blank's base cost and shipping, set your retail prices in Shopify, then copy
   the same prices into `catalog.js`.
5. Order a sample of each product before launch, especially the knitted sweater and the
   embroidered beanie, and compare it with the mockups.

> The ugly sweater is a real jacquard knitting chart (four yarn colours, which is the
> knitwear limit), the beanie face is reduced to five thread colours for embroidery, and the build checks both
> against the production limits every time it runs.

## 2. Copy the variant IDs into the catalog

Every product in `catalog.js` has a `shopify: {}` map. Fill it with one entry per variant,
keyed by the option values joined with ` / ` in the order they're listed in the product:

```js
shopify: {
  'Red / S': '44012345678901',
  'Red / M': '44012345678902',
  // ...
  'Green / 3XL': '44012345678912',
},
```

Fixed single-value options count too. The mug is
`'11 oz': '...'`, the ornament is `'Holiday Reserve': '...'` and a sticker is
`'Wordmark / 4 in': '...'`.

To find a variant ID in Shopify: open the product, click a variant, and copy the number at
the end of the URL (`.../variants/44012345678901`). You can also add `.json` to a product's
storefront URL to see every variant ID at once.

## 3. Switch checkout on

```js
checkout: {
  provider: 'shopify',
  shopifyDomain: 'your-store.myshopify.com',
},
```

Checkout now sends the whole cart to Shopify's secure checkout
(`https://your-store.myshopify.com/cart/<variant>:<qty>,...`), where customers pay and
Printful/Printify fulfils the order automatically. If a line in the cart has no variant ID,
the customer sees a friendly message instead of a broken checkout.

## Other settings in `STORE`

| Setting | What it does |
| --- | --- |
| `orderByNote` | Holiday cut-off message in the hero and the cart. Set `''` to hide. |
| `notifyUrl` | In pre-launch mode, adds a "Get notified" button (e.g. a Google Form or newsletter signup page). |
| `giveBack` | Optional banner announcing a donation. Only enable it once you've actually arranged one. |

## Editing products

* **Copy and prices:** edit the product entry in `catalog.js`.
* **Pictures:** each colour or design option lists its `views` (front, back, print art).
  The first view is the product card. All images are in `assets/shop/`.
* **Artwork:** designs live in `tools/merch_designs.py`, product mockups in
  `tools/merch_mockups.py`, and `tools/build_merch.py` exports the shop images, print
  files, spec sheets and line sheet. Run `bash tools/build_all.sh` after any change; it
  stops with an error if a design breaks a production limit (yarn or thread colours,
  ornament safe area, embroidery detail size).
* **New garment colours:** add a ramp to `RAMPS` in `tools/merchkit.py`, render the extra
  mockup in the product's builder in `build_merch.py`, then add the option to `catalog.js`.

## Before you launch, check

- [ ] `comingSoon` is `false` in `catalog.js`.
- [ ] Prices in `catalog.js` match Shopify.
- [ ] A sample of each product has been checked against `merch/<product>/mockups/`.
- [ ] The returns and shipping answers in the FAQ (`shop/index.html`) match your provider's policies.
- [ ] `orderByNote` uses your provider's real holiday cut-off date.
- [ ] Place a test order end to end.
