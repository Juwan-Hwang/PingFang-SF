"""Accent-colour audit: the accent belongs to ONE carry element. Flags frames where the accent appears as more than one
blob (it leaked onto a UI element, a chart, a caption) or covers a big area outside the moments you allowed (the full-frame
"inside the carry" transitions).

  python3 scripts/qa_accent.py film/out/frames_en --accent FF5B1F --allow 4.5-6.6 30.4-32.6 --step 3
Prints the offending times; exit 1 if any. Tune --tol for anti-aliasing; tiny blobs (< --min-area px) are ignored.
"""
import argparse, glob, sys
import numpy as np
from PIL import Image
from scipy import ndimage

ap = argparse.ArgumentParser(); ap.add_argument('frames'); ap.add_argument('--accent', default='FF5B1F'); ap.add_argument('--tol', type=int, default=38)
ap.add_argument('--allow', nargs='*', default=[]); ap.add_argument('--step', type=int, default=3); ap.add_argument('--fps', type=int, default=30)
ap.add_argument('--max-blobs', type=int, default=1); ap.add_argument('--max-area', type=float, default=0.02); ap.add_argument('--min-area', type=int, default=24)
a = ap.parse_args()
acc = np.array([int(a.accent[i:i + 2], 16) for i in (0, 2, 4)])
allow = [tuple(map(float, r.split('-'))) for r in a.allow]
fs = sorted(glob.glob(f'{a.frames}/*.jpg'))[::a.step]; bad = []
for f in fs:
    t = int(f.split('/')[-1][:-4]) / a.fps
    if any(lo <= t <= hi for lo, hi in allow): continue
    im = np.asarray(Image.open(f).convert('RGB').resize((960, 540))).astype(int)
    m = (np.abs(im - acc).max(-1) < a.tol)
    lab, n = ndimage.label(m); sizes = ndimage.sum(m, lab, range(1, n + 1)) if n else []
    blobs = int((np.asarray(sizes) * 4 >= a.min_area).sum()); area = m.mean()
    if blobs > a.max_blobs or area > a.max_area: bad.append((round(t, 2), blobs, round(float(area), 4)))
for b in bad: print(f'{b[0]:7.2f}s  accent blobs={b[1]}  area={b[2]*100:.2f}%')
print(f'{len(fs)} frames checked, {len(bad)} flagged'); sys.exit(1 if bad else 0)
