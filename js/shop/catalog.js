// Store configuration + product catalog. This is the only file you need to edit to
// run the shop: prices, copy, variants and checkout. See docs/SHOP_SETUP.md.

export const STORE = {
  currency: 'USD',

  // Checkout. Until a provider is connected the shop is fully browsable, the cart
  // works, and "Checkout" explains that orders open soon.
  //   provider: 'none'     -> pre-launch mode
  //   provider: 'shopify'  -> hand the cart to Shopify (fill in shopifyDomain and every
  //                           product's `shopify` variant IDs below)
  checkout: {
    provider: 'none',
    shopifyDomain: '', // e.g. 'trashed-panda.myshopify.com'
  },

  // Optional link for "Get notified when orders open" in pre-launch mode
  // (a Google Form, Mailchimp/Buttondown signup page, etc.). Leave empty to hide.
  notifyUrl: '',

  // Holiday shipping note shown in the hero and cart. Set to '' to hide.
  orderByNote: 'Order by Dec 12 for delivery before the holidays (US).',

  // Optional give-back banner. Only turn this on once you have actually arranged it.
  giveBack: {
    enabled: false,
    text: 'A share of every order goes to Hanover County Animal Protection & Shelter, who looked after the real raccoon.',
    url: '',
  },
};

const APPAREL_SIZES = ['S', 'M', 'L', 'XL', '2XL', '3XL'];

export const CATEGORIES = [
  { id: 'all', label: 'Everything' },
  { id: 'apparel', label: 'Apparel' },
  { id: 'gifts', label: 'Gifts & decor' },
];

export const PRODUCTS = [
  {
    id: 'ugly-sweater',
    name: 'The Ugly Trash Panda Sweater',
    category: 'apparel',
    price: 64,
    badge: 'Holiday',
    blurb: 'Fair-isle snowflakes, tiny bottles and a raccoon in a Santa hat.',
    description:
      'Charted stitch by stitch from the game’s pixel art: snowflake yoke, zigzag bands, a row of bottles and the Santa Panda front and centre. The ugliest sweater at the party, and the only one with a backstory.',
    details: ['Knit-look all-over print', 'Five-colour chart: one pixel, one stitch', 'Unisex fit', 'Printed to order'],
    options: {
      Color: [
        { value: 'Red', image: 'sweater-red.png', swatch: '#b8323a', bg: '#1d3324', design: 'design-sweater-red.png' },
        { value: 'Green', image: 'sweater-green.png', swatch: '#2c6b3e', bg: '#3a1a1c', design: 'design-sweater-green.png' },
      ],
      Size: APPAREL_SIZES,
    },
    shopify: {}, // 'Red / M': '1234567890'
  },
  {
    id: 'naughty-list-tee',
    name: 'Naughty List Tee',
    category: 'apparel',
    price: 32,
    blurb: 'Fell through a ceiling, drank the inventory. Santa made a call.',
    description:
      'He fell through a ceiling, drank the inventory and fell asleep next to the toilet. Santa made a decision. Big chunky pixels, printed edge-to-edge sharp.',
    details: ['Front print, 12 in wide', 'Light ink on dark tees, dark ink on oatmeal', 'Unisex fit', 'Printed to order'],
    options: {
      Color: [
        { value: 'Black', image: 'tee-black.png', swatch: '#29221d', bg: '#3a2619', design: 'design-naughty-light.png', designBg: '#29221d' },
        { value: 'Forest', image: 'tee-forest.png', swatch: '#2a5d40', bg: '#2a1d14', design: 'design-naughty-light.png', designBg: '#2a5d40' },
        { value: 'Oatmeal', image: 'tee-oatmeal.png', swatch: '#e3d8c1', bg: '#203325', design: 'design-naughty-dark.png', designBg: '#e3d8c1' },
      ],
      Size: APPAREL_SIZES,
    },
    shopify: {},
  },
  {
    id: 'pixel-ornament',
    name: 'Pixel Ornament',
    category: 'gifts',
    price: 18,
    badge: 'Collect 3',
    blurb: 'Three moments from the night of the crime.',
    description:
      'Through the ceiling, the Holiday Reserve, and passed out on the floor: three scenes from the night, each on a glossy round ornament. Collect all three for a tree with a criminal record.',
    details: ['Round ornament, about 3 in', 'Ribbon included', 'Design on the front', 'Printed to order'],
    options: {
      Design: [
        { value: 'Through the Ceiling', image: 'ornament-drop.png', swatch: '#dedad1', bg: '#1d3324', design: 'design-drop.png' },
        { value: 'Holiday Reserve', image: 'ornament-reserve.png', swatch: '#ff5c58', bg: '#3a1a1c', design: 'design-reserve.png' },
        { value: 'Passed Out', image: 'ornament-passed-out.png', swatch: '#76643c', bg: '#22283a', design: 'design-passed-out.png' },
      ],
    },
    shopify: {},
  },
  {
    id: 'trashed-panda-hoodie',
    name: 'Trashed Panda Hoodie',
    category: 'apparel',
    price: 58,
    blurb: 'The wordmark, the face, the hometown.',
    description:
      'The game’s wordmark with the Santa Panda on top and Ashland, VA underneath. Kangaroo pocket for snacks you definitely paid for.',
    details: ['Chest print, 10 in wide', 'Kangaroo pocket, lined hood', 'Unisex fit', 'Printed to order'],
    design: 'design-wordmark.png',
    options: {
      Color: [
        { value: 'Black', image: 'hoodie-black.png', swatch: '#29221d', bg: '#203325' },
        { value: 'Heather', image: 'hoodie-heather.png', swatch: '#5f5e61', bg: '#3a2619' },
      ],
      Size: APPAREL_SIZES,
    },
    shopify: {},
  },
  {
    id: 'poor-life-choices-mug',
    name: 'Poor Life Choices Mug',
    category: 'gifts',
    price: 18,
    blurb: 'For the morning after.',
    description:
      'Our hero, feet up, hat off, sleeping it off. The design is on both sides, so left-handed coffee drinkers get judged too.',
    details: ['11 oz ceramic mug', 'Design on both sides', 'Printed to order'],
    design: 'design-choices.png',
    options: { Size: ['11 oz'] },
    image: 'mug.png',
    bg: '#22283a',
    shopify: {},
  },
  {
    id: 'tail-stripe-socks',
    name: 'Tail Stripe Socks',
    category: 'apparel',
    price: 20,
    blurb: 'Ringed like the real thing.',
    description:
      'Brown rings like a raccoon’s tail, red heel and toe, and a Santa Panda on each ankle. Ideal for sliding across tile floors.',
    details: ['Crew length', 'All-over print', 'Printed to order'],
    options: { Size: ['S/M', 'L/XL'] },
    image: 'socks.png',
    bg: '#3a1a1c',
    shopify: {},
  },
  {
    id: 'santa-panda-beanie',
    name: 'Santa Panda Beanie',
    category: 'apparel',
    price: 30,
    blurb: 'Cuffed knit, pom-pom, pixel patch.',
    description:
      'A cuffed knit beanie with a pom-pom and a woven patch of the raccoon’s face. Keeps your ears warm while you think about your choices.',
    details: ['Cuffed knit with pom-pom', 'Woven pixel patch', 'One size', 'Made to order'],
    options: {
      Color: [
        { value: 'Black', image: 'beanie-black.png', swatch: '#29221d', bg: '#203325' },
        { value: 'Red', image: 'beanie-red.png', swatch: '#b8323a', bg: '#22283a' },
      ],
    },
    shopify: {},
  },
  {
    id: 'gift-wrap',
    name: 'Evidence Gift Wrap',
    category: 'gifts',
    price: 22,
    blurb: 'Wrap their present in evidence.',
    description:
      'Santa Panda faces, gold bottles and snowflakes on festive red. A seamless repeat, so every fold lines up.',
    details: ['Set of 3 sheets', 'Seamless pattern', 'Printed to order'],
    design: 'design-wrap.png',
    options: { Size: ['3 sheets'] },
    image: 'wrap.png',
    bg: '#1d3324',
    shopify: {},
  },
  {
    id: 'bathroom-floor-cards',
    name: 'Bathroom Floor Holiday Cards',
    category: 'gifts',
    price: 16,
    blurb: 'Season’s greetings from the bathroom floor.',
    description:
      'A holiday card for people who appreciate a story. Blank inside for your own confession.',
    details: ['Pack of 6, 5×7 in', 'Blank inside', 'Envelopes included', 'Printed to order'],
    design: 'design-greetings.png',
    options: { Size: ['Pack of 6'] },
    image: 'cards.png',
    bg: '#3a2619',
    shopify: {},
  },
  {
    id: 'sticker-pack',
    name: 'Sticker Pack',
    category: 'gifts',
    price: 9,
    blurb: 'Five die-cut stickers.',
    description:
      'The wordmark, the Santa face, the Holiday Reserve, a whiskey bottle and the raccoon, passed out. Stocking-stuffer sized.',
    details: ['5 die-cut vinyl stickers', 'White border', 'Printed to order'],
    options: { Size: ['5 stickers'] },
    image: 'stickers.png',
    bg: '#22283a',
    shopify: {},
  },
];

export const IMG = new URL('../../assets/shop/', import.meta.url).href;

export function productById(id) {
  return PRODUCTS.find((p) => p.id === id);
}

/** Default option selection: first value of every option. */
export function defaultOptions(p) {
  const o = {};
  for (const [k, vals] of Object.entries(p.options)) o[k] = typeof vals[0] === 'string' ? vals[0] : vals[0].value;
  return o;
}

/** The option that drives the picture (Color or Design), if any. */
export function visualOption(p) {
  return Object.keys(p.options).find((k) => typeof p.options[k][0] === 'object');
}

export function imageFor(p, options = {}) {
  const key = visualOption(p);
  if (!key) return { src: IMG + p.image, bg: p.bg, designBg: p.bg };
  const val = options[key] ?? p.options[key][0].value;
  const opt = p.options[key].find((o) => o.value === val) ?? p.options[key][0];
  return { src: IMG + opt.image, bg: opt.bg, designBg: opt.designBg || opt.bg, design: opt.design ? IMG + opt.design : p.design ? IMG + p.design : null };
}

export function designFor(p, options = {}) {
  return imageFor(p, options).design ?? (p.design ? IMG + p.design : null);
}

export function variantLabel(options) {
  return Object.values(options).filter((v) => !/^(11 oz|3 sheets|Pack of 6|5 stickers)$/.test(v)).join(' / ');
}

export function formatPrice(n) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: STORE.currency, minimumFractionDigits: n % 1 ? 2 : 0 }).format(n);
}
