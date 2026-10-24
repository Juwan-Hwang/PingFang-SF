"""Check the 3D → vector handoff is pixel-matched: compare the last 3D end frame with the comp's vector lockup frame.

  python3 scripts/handoff_check.py film/frames/end/0074.jpg review/vec_34.50.png --accent FF5B1F
Prints the accent element's bounding box in both (it must agree to ≤ 1 px) and writes handoff_diff.png (side by side + diff).
If they disagree by a constant offset: ppu/sx/sy are stale (re-run r3d_seq.py end … --handoff comp.html after any lockup
change). If the 3D one is smaller and shifted toward the centre: the front cap is culled (mirrored geometry, fix winding).
"""
import argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser(); ap.add_argument('a3d'); ap.add_argument('bvec'); ap.add_argument('--accent', default='FF5B1F'); ap.add_argument('--tol', type=int, default=40)
a = ap.parse_args(); acc = np.array([int(a.accent[i:i + 2], 16) for i in (0, 2, 4)])
A = np.asarray(Image.open(a.a3d).convert('RGB')).astype(int); B = np.asarray(Image.open(a.bvec).convert('RGB')).astype(int)
def box(x):
    m = np.abs(x - acc).max(-1) < a.tol; ys, xs = np.nonzero(m)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())) if len(xs) else None
ba, bb = box(A), box(B); print('3D accent box  ', ba); print('vector accent  ', bb)
if ba and bb: d = max(abs(p - q) for p, q in zip(ba, bb)); print('max edge error', d, 'px', 'OK' if d <= 1 else 'MISMATCH')
D = np.abs(A - B).clip(0, 255).astype('uint8'); W = A.shape[1]
Image.fromarray(np.concatenate([A.astype('uint8'), B.astype('uint8'), D], 1)).resize((W * 3 // 2, A.shape[0] // 2)).save('handoff_diff.png')
