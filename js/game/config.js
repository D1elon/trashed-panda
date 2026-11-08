// Gameplay tuning. All distances are in art pixels (the native sprite grid),
// all times in seconds unless the name says otherwise.

export const SIM_DT = 1 / 120;          // fixed simulation step
export const MAX_FRAME_DT = 0.1;        // clamp for long frames / tab switches

export const ROUND_TIME = 60;
export const COUNTDOWN_STEP = 0.6;      // 3, 2, 1, GO
export const DROP_TIME = 0.8;           // falling through the ceiling
export const END_KO_TIME = 1.8;         // passed-out beat before the results screen

// Movement
export const WALK_SPEED = 66;
export const DRUNK_SPEED_PENALTY = 0.25; // fraction of speed lost at 100% drunk
export const CLIMB_TIME = 0.24;
export const CLIMB_COOLDOWN = 0.28;
export const GRAVITY = 720;
export const MAX_FALL_SPEED = 420;
export const EDGE_MARGIN = 6;           // how far inside a shelf the raccoon's centre must stay

// Actions
export const SWIPE_TIME = 0.28;
export const SWIPE_COOLDOWN = 0.2;
export const SWIPE_REACH = 14;          // hit window centre, ahead of the raccoon's centre
export const SWIPE_HALF_WIDTH = 17;     // covers just behind the body to the paw tip
export const DRINK_TIME = 0.62;
export const DRINK_REACH_FWD = 40;
export const DRINK_REACH_BACK = 8;

// Bottles
export const BOTTLE_GRAVITY = 560;
export const RESERVE_PER_RUN = 2;
export const BREAK_FRAME_TIME = 0.07;
export const RESTOCK_DELAY = 3.5;      // an emptied shelf unit refills after this long
export const RESTOCK_RESERVE_CHANCE = 0.3;

// Bottle kinds: points for smashing, buzz for drinking the puddle.
export const KINDS = {
  vodka:   { index: 0, smash: 20, drink: 40, buzz: 10, color: '#9fd3f5' },
  whiskey: { index: 1, smash: 25, drink: 40, buzz: 12, color: '#e79a2c' },
  wine:    { index: 2, smash: 20, drink: 40, buzz: 9,  color: '#b8283f' },
  tequila: { index: 3, smash: 25, drink: 40, buzz: 13, color: '#bcd66a' },
  reserve: { index: 4, smash: 100, drink: 120, buzz: 16, color: '#ff5c58', timeBonus: 5 },
};
export const COMMON_KINDS = ['vodka', 'whiskey', 'wine', 'tequila'];

// Combo: consecutive smashes within the window multiply points.
export const COMBO_WINDOW = 2.5;
export const COMBO_MULT = [1, 1, 1.5, 2, 2.5, 3];

// Buzz: being drunk multiplies every point, but 100% knocks you out.
export const BUZZ_DECAY = 3.5;           // per second
export const BUZZ_TIERS = [
  { min: 0,  name: 'Sober',  mult: 1 },
  { min: 20, name: 'Tipsy',  mult: 1.5 },
  { min: 40, name: 'Buzzed', mult: 2 },
  { min: 60, name: 'Drunk',  mult: 2.5 },
  { min: 80, name: 'Wasted', mult: 3 },
];
export const BLACKOUT_TIME = 3;
export const BLACKOUT_RECOVER_TO = 55;
export const SLIP_START = 50;            // buzz above which climbing can fail
export const SLIP_MAX_CHANCE = 0.14;

// Calibrated with scripted playtests: casual ~1.4k, average ~3k, good ~8.5k, expert 10k+.
export const RANKS = [
  { min: 10000, name: 'Legendary Trash Panda' },
  { min: 5000, name: 'Master Bandit' },
  { min: 2500, name: 'Party Animal' },
  { min: 1000, name: 'Tipsy Troublemaker' },
  { min: 0,    name: 'Amateur Raider' },
];

export function buzzTier(level) {
  let t = BUZZ_TIERS[0];
  for (const tier of BUZZ_TIERS) if (level >= tier.min) t = tier;
  return t;
}

export function rankFor(score) {
  return RANKS.find((r) => score >= r.min) ?? RANKS[RANKS.length - 1];
}
