#!/usr/bin/env bash
# Rebuild every generated asset, in dependency order.
#   bash tools/build_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build_sprites.py   # raccoon, bottles, bathroom  -> assets/game, js/game/sprite-data.js
python3 tools/build_store.py     # store backdrop + world data -> assets/game, js/game/world-data.js
python3 tools/build_ui.py        # icons, logo, favicon, help art -> assets/ui, favicon.*
python3 tools/build_merch.py     # merch mockups, designs, print files -> assets/shop, merch/print-files
python3 tools/build_og.py        # social share images -> assets/ui/og*.png
