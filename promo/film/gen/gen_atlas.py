"""Every glyph in the font, in glyph-ID order, 256 per row: GID 0 (.notdef) top-left … GID 65,534 bottom-right,
and the 65,536th cell (GID 65,535) empty, because TrueType's maxp.numGlyphs is a uint16 (max 65,535).
Rendered with FreeType from the repo's font at its default instance (wght 500, wdth 100).
Writes film/atlas/L0_r{row}_c{col}.png (8 x 8 tiles of 1024 px, 32 px cells) and L1 (4096 whole), L2 (2048), L3 (1024)."""
import sys, os, numpy as np, freetype
from PIL import Image

def la(img):   # paper-white glyphs on a transparent ground (coverage = alpha), so the film's ground shows through
    img = img.convert('L'); return Image.merge('LA', (Image.new('L', img.size, 244), img))
P = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
CELL = 32; N = 256
face = freetype.Face(P); face.set_pixel_sizes(0, 24)
ng = face.num_glyphs; print('num_glyphs', ng)
big = np.zeros((N * CELL, N * CELL), np.uint8)
asc = 24 * 0.86; base = int(round((CELL - 24) / 2 + asc))   # em box (−140..860) centred in the cell
for gid in range(ng):
    try:
        face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_LIGHT)
    except Exception:
        continue
    g = face.glyph; bm = g.bitmap
    if bm.width == 0 or bm.rows == 0: continue
    a = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
    adv = g.advance.x / 64
    r, c = divmod(gid, N)
    x = c * CELL + int(round((CELL - adv) / 2)) + g.bitmap_left
    y = r * CELL + base - g.bitmap_top
    x0, y0 = max(x, c * CELL), max(y, r * CELL)
    x1, y1 = min(x + a.shape[1], (c + 1) * CELL), min(y + a.shape[0], (r + 1) * CELL)
    if x1 <= x0 or y1 <= y0: continue
    big[y0:y1, x0:x1] = np.maximum(big[y0:y1, x0:x1], a[y0 - y:y1 - y, x0 - x:x1 - x])
    if gid % 8192 == 0: print(gid, flush=True)
T = 1024
for r in range(N * CELL // T):
    for c in range(N * CELL // T):
        la(Image.fromarray(big[r*T:(r+1)*T, c*T:(c+1)*T])).save(f'{OUT}/L0_r{r}_c{c}.png', optimize=True)
im = Image.fromarray(big)
for lv, s in ((1, 4096), (2, 2048), (3, 1024)):
    la(im.resize((s, s), Image.LANCZOS)).save(f'{OUT}/L{lv}.png', optimize=True)
print('done')
