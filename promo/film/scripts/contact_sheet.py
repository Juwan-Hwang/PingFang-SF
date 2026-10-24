"""Contact sheets for QA. Two modes:

  python3 scripts/contact_sheet.py frames film/out/frames_en sheet.png --t0 0 --t1 59 --step 1.0 [--cols 6 --w 320 --fps 30]
  python3 scripts/contact_sheet.py files sheet.png a.png b.png c.png ... [--cols 3 --w 640]
Every tile is labelled with its time (or file name) so a note like "28.4 s: caption overlaps the pane" is actionable.
Look at the sheet at 100 %: check clipping at the frame edge, text overlapping UI, the accent appearing anywhere but the
carry element, a language leaking into the other cut, typos, a hold that reads empty, and the 3D→vector handoff.
"""
import argparse, glob, os
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['frames', 'files']); ap.add_argument('args', nargs='+')
ap.add_argument('--t0', type=float, default=0); ap.add_argument('--t1', type=float, default=None); ap.add_argument('--step', type=float, default=1.0)
ap.add_argument('--cols', type=int, default=None); ap.add_argument('--w', type=int, default=None); ap.add_argument('--fps', type=int, default=30)
a = ap.parse_args()
if a.mode == 'frames':
    src, out = a.args[0], a.args[1]
    n = len(glob.glob(f'{src}/*.jpg')); t1 = a.t1 if a.t1 is not None else (n - 1) / a.fps
    items = []; t = a.t0
    while t <= t1 + 1e-6:
        f = f'{src}/{int(round(t * a.fps)):05d}.jpg'
        if os.path.exists(f): items.append((f, f'{t:.2f}s'))
        t += a.step
    cols, w = a.cols or 6, a.w or 320
else:
    out, files = a.args[0], a.args[1:]; items = [(f, os.path.basename(f)) for f in files]; cols, w = a.cols or 3, a.w or 640
h = w * 9 // 16; rows = (len(items) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * (h + 20)), (60, 20, 60)); d = ImageDraw.Draw(S)     # magenta gutter: never mistaken for content
for i, (f, lab) in enumerate(items):
    im = Image.open(f).convert('RGB').resize((w, h), Image.LANCZOS); x, y = (i % cols) * w, (i // cols) * (h + 20)
    S.paste(im, (x, y)); d.text((x + 5, y + h + 4), lab, fill=(240, 240, 240))
S.save(out); print(out, len(items), 'tiles')
