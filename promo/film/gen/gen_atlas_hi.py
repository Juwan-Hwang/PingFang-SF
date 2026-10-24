"""Hi-res crops of the glyph grid for the close-ups (same layout as gen_atlas.py, 8x: 256 px cells, 192 px em):
hi_hao.png  rows 69-77, cols 82-98 (around 好, GID 18,778 = row 73, col 90)
hi_end.png  rows 248-255, cols 238-255 (the last glyphs; GID 65,534 is row 255 col 254, cell 65,535 stays empty)"""
import sys, numpy as np, freetype
from PIL import Image

def la(img):   # paper-white glyphs on a transparent ground (coverage = alpha), so the film's ground shows through
    img = img.convert('L'); return Image.merge('LA', (Image.new('L', img.size, 244), img))
P, OUT = sys.argv[1], sys.argv[2]
K = 8; CELL = 32 * K; EM = 24 * K; N = 256
face = freetype.Face(P); face.set_pixel_sizes(0, EM); ng = face.num_glyphs
base = int(round((CELL - EM) / 2 + EM * 0.86))
def crop(r0, r1, c0, c1, name):
    big = np.zeros(((r1 - r0 + 1) * CELL, (c1 - c0 + 1) * CELL), np.uint8)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            gid = r * N + c
            if gid >= ng: continue
            face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_LIGHT)
            g = face.glyph; bm = g.bitmap
            if bm.width == 0 or bm.rows == 0: continue
            a = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
            x = (c - c0) * CELL + int(round((CELL - g.advance.x / 64) / 2)) + g.bitmap_left
            y = (r - r0) * CELL + base - g.bitmap_top
            cx0, cy0 = (c - c0) * CELL, (r - r0) * CELL
            x0, y0 = max(x, cx0), max(y, cy0); x1, y1 = min(x + a.shape[1], cx0 + CELL), min(y + a.shape[0], cy0 + CELL)
            if x1 > x0 and y1 > y0: big[y0:y1, x0:x1] = np.maximum(big[y0:y1, x0:x1], a[y0 - y:y1 - y, x0 - x:x1 - x])
    la(Image.fromarray(big)).save(f'{OUT}/{name}', optimize=True); print(name, big.shape)
crop(69, 77, 82, 98, 'hi_hao.png'); crop(248, 255, 238, 255, 'hi_end.png')
