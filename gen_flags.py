"""flags.js: one byte per glyph ID of the v1.2.0 font, 1 = glyph added in v1.2.0 (used by scene 08's mosaic).
Usage: python3 gen_flags.py base_before_fill.ttf "PingFang-SF Medium.ttf"
Glyphs are matched by name; base glyphs that v1.2.0 renamed (post table) are matched by outline."""
import sys, base64, hashlib
from fontTools.ttLib import TTFont
B = TTFont(sys.argv[1]); F = TTFont(sys.argv[2])
def h(gs, n):
    g = gs[n]
    if g.isComposite(): return 'C' + str([(c.x, c.y) for c in g.components])
    if g.numberOfContours == 0: return 'E'
    return hashlib.md5(repr((list(g.coordinates), list(g.endPtsOfContours))).encode()).hexdigest()
bs = set(B.getGlyphOrder()); fo = F.getGlyphOrder(); fs = set(fo)
gone = {}
for n in B.getGlyphOrder():
    if n not in fs: k = h(B['glyf'], n); gone[k] = gone.get(k, 0) + 1
fl = []
for n in fo:
    if n in bs: fl.append(0); continue
    k = h(F['glyf'], n)
    if gone.get(k, 0): gone[k] -= 1; fl.append(0)
    else: fl.append(1)
print(len(fo), 'glyphs,', sum(fl), 'added')
open('flags.js', 'w').write('window.FLAGS="' + base64.b64encode(bytes(fl)).decode() + '";')
