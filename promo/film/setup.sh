#!/bin/sh
# One-time setup (safe to re-run). Python deps + Chromium, three.js r170, earshot @ 925ebe5, and the film's derived data.
# The font is NOT copied into git: it is this repo's own "PingFang-SF Medium.ttf" (two folders up), linked into film/fonts/.
set -e
cd "$(dirname "$0")"
pip install -q -r requirements.txt
python3 -m playwright install --with-deps chromium || python3 -m playwright install chromium
[ -d film/node_modules/three ] || npm install --silent --no-save --prefix film three@0.170.0
mkdir -p film/fonts
FONT="../../PingFang-SF Medium.ttf"
[ -f "$FONT" ] || { echo "font not found: run from promo/film inside a PingFang-SF checkout"; exit 1; }
[ -f film/fonts/PingFangSF.ttf ] || cp "$FONT" film/fonts/PingFangSF.ttf
if [ ! -d repos/earshot ]; then
  git clone -q https://github.com/Leonxlnx/earshot repos/earshot
  git -C repos/earshot checkout -q 925ebe56a1b755e5d354ab642bb8f344440cfa9c
fi
pip install -q --no-deps -e repos/earshot
# derived glyph data (committed too, regenerated here only if missing): outlines, specimen points, the 65,535-glyph atlas
[ -f film/data/lockup.json ] || python3 gen/gen_lockup_anat.py "$FONT" film/data
[ -f film/data/spec.json ] || python3 gen/gen_spec.py "$FONT" film/data
[ -f film/atlas/L1.png ] || python3 gen/gen_atlas.py "$FONT" film/atlas
[ -f film/atlas/hi_end.png ] || python3 gen/gen_atlas_hi.py "$FONT" film/atlas
echo "setup ok: python3 -m http.server 8777 --directory film, then open http://localhost:8777/comp.html?lang=en&t=0"
