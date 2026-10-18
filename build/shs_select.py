"""Find the static glyphs whose outline is Source Han Sans, and measure the weight mapping.

usage: python shs_select.py FONT_BEFORE_STEP7.ttf [SourceHanSans-VF.ttf] > data/shs_vf_glyphs.tsv
       python shs_select.py --stems FONT.ttf [SourceHanSans-VF.ttf]     (weight-mapping table)

Not run by build.sh (the result is committed as data/shs_vf_glyphs.tsv); kept so the list
can be regenerated and audited.  Needs freetype-py and numpy.

Selection, per code point that is static (no non-zero gvar delta) and present in SHS:
  1. rasterise ours (96 px) and every SHS regional form of the character (default=JAN plus
     the ZHS/ZHT/ZHH/KOR `locl` alternates) at wght 250..900 step 50; keep the best IoU;
  2. refine the SHS weight in steps of 5 by matching the outline area;
  3. accept when IoU >= 0.9, bbox deviation <= 8 units (TH-Hak re-quantised SHS to a 256 grid,
     ≈ 4 units), area error < 5 % (a reversed contour direction gives exactly 200 % and is
     accepted), and the SHS glyph itself varies (max master delta >= 5 units);
  4. region preference (v1.2.0, user decision): PingFang SF is a Traditional-Chinese-based
     font, so when SHS has a ZHT `locl` form that differs from the matched form, the ZHT
     form is used (for the 759 selected glyphs this affects exactly 7: U+2047 U+2048 U+2049
     U+337F U+1F23B U+237F1 U+284DC; their ZHT form == ZHH form).  The weight mapping is
     unchanged.
"""
import sys, os, collections
import numpy as np
import freetype
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('PFSF_SRC', os.path.join(HERE, '..', 'sources'))
SHS_DEFAULT = os.path.join(SRC, 'shs', 'SourceHanSans-VF.ttf')
PX = 96
FT_FLAGS = freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_HINTING


def raster(face, gid, px=PX):
    face.load_glyph(gid, FT_FLAGS)
    face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    b = face.glyph.bitmap
    a = np.zeros((px * 2, px * 2), np.float32)
    if b.rows:
        arr = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] / 255.0
        x, y = face.glyph.bitmap_left + px // 4, px * 3 // 2 - face.glyph.bitmap_top
        try:
            a[y:y + b.rows, x:x + b.width] = arr
        except ValueError:
            pass
    return a


def locl_alternates(S):
    gsub = S['GSUB'].table
    alts = collections.defaultdict(dict)
    for sr in gsub.ScriptList.ScriptRecord:
        for ls in sr.Script.LangSysRecord:
            tag = ls.LangSysTag.strip()
            for fi in ls.LangSys.FeatureIndex:
                fr = gsub.FeatureList.FeatureRecord[fi]
                if fr.FeatureTag != 'locl':
                    continue
                for li in fr.Feature.LookupListIndex:
                    for st in gsub.LookupList.Lookup[li].SubTable:
                        if st.LookupType == 7:
                            st = st.ExtSubTable
                        if hasattr(st, 'mapping'):
                            alts[tag].update(st.mapping)
    return alts


def static_glyphs(f):
    gv, glyf = f['gvar'], f['glyf']
    out = set()
    for g in f.getGlyphOrder():
        if glyf[g].numberOfContours == 0:
            continue
        if not any(c and c != (0, 0) for v in gv.variations.get(g, []) for c in v.coordinates):
            out.add(g)
    return out


def feat(gs, g):
    bp, ap = BoundsPen(gs), AreaPen(gs)
    gs[g].draw(bp)
    gs[g].draw(ap)
    return bp.bounds, ap.value, gs[g].width


def select(ours_path, shs_path):
    f = TTFont(ours_path, lazy=True)
    S = TTFont(shs_path)
    cm, scm = f.getBestCmap(), S.getBestCmap()
    st = static_glyphs(f)
    alts = locl_alternates(S)
    fo, fs = freetype.Face(ours_path), freetype.Face(shs_path)
    fo.set_pixel_sizes(PX, PX)
    fs.set_pixel_sizes(PX, PX)
    cps = sorted(c for c, g in cm.items() if g in st and c in scm)
    ours = {c: raster(fo, f.getGlyphID(cm[c])) for c in cps}
    cands = {}
    for c in cps:
        g = scm[c]
        cands[c] = {'JAN': g}
        for tag in ('ZHS', 'ZHT', 'ZHH', 'KOR'):
            if g in alts[tag]:
                cands[c][tag] = alts[tag][g]
    best = {c: (0.0, None, None) for c in cps}
    for w in range(250, 901, 50):
        fs.set_var_design_coords((w,))
        for c in cps:
            for tag, g in cands[c].items():
                b = raster(fs, S.getGlyphID(g))
                v = float(np.minimum(ours[c], b).sum() / max(np.maximum(ours[c], b).sum(), 1e-6))
                if v > best[c][0]:
                    best[c] = (v, tag, w)
    gs = f.getGlyphSet()
    sgs = {}
    gvS = S['gvar']
    rows = []
    for c in cps:
        iou, tag, w0 = best[c]
        if iou < 0.9:
            continue
        sg = cands[c][tag]
        ob, oa, _ = feat(gs, cm[c])
        fit = None
        for w in range(max(250, w0 - 60), min(900, w0 + 60) + 1, 5):
            if w not in sgs:
                sgs[w] = S.getGlyphSet(location={'wght': w})
            b, a, _ = feat(sgs[w], sg)
            e = abs(a - oa) / max(abs(oa), 1)
            if fit is None or e < fit[0]:
                fit = (e, b)
        e, b = fit
        if abs(e - 2) < 0.05:
            e = 0.0                      # same outline, reversed contour direction
        bd = max(abs(x - y) for x, y in zip(b, ob)) if b and ob else 999
        vs = gvS.variations.get(sg, [])
        md = max([abs(x) for v in vs for p in v.coordinates[:-4] if p for x in p] or [0])
        if bd > 8 or e >= 0.05 or md < 5:
            continue
        if 'ZHT' in cands[c] and cands[c]['ZHT'] != sg:     # prefer the TC form (rule 4)
            tag, sg = 'ZHT', cands[c]['ZHT']
            vs = gvS.variations.get(sg, [])
        prop = any(v.coordinates[-3] and v.coordinates[-3][0] for v in vs)
        rows.append((c, cm[c], sg, tag, 'prop' if prop else 'fixed'))
    print('# codepoint\tglyph (PingFang SF)\tglyph (SourceHanSans-VF.ttf 2.005)\tregion form\tadvance')
    for r in rows:
        print('U+%04X\t%s\t%s\t%s\t%s' % r)
    print('selected %d of %d static code points present in SHS (%d static glyphs total)'
          % (len(rows), len(cps), len(st)), file=sys.stderr)


def stem(face, gid, coords, axis, frac=0.5, px=1000):
    face.set_var_design_coords(coords)
    face.set_char_size(px * 64, 0, 72, 72)
    face.load_glyph(gid, FT_FLAGS)
    face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    b = face.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] / 255.0
    line = a[:, int(a.shape[1] * frac)] if axis == 'h' else a[int(a.shape[0] * frac), :]
    runs = np.diff(np.concatenate([[0], (line > 0.5).astype(int), [0]]))
    return line.sum() / max((runs == 1).sum(), 1)


def stems(ours_path, shs_path):
    """t = (stem_PingFang(w) - stem_SHS_EL) / (stem_SHS_Heavy - stem_SHS_EL) for w = 100..900"""
    tests = [(0x4E00, 'h', .5), (0x4E09, 'h', .5), (0x5DDD, 'v', .5), (0x4E28, 'v', .5),
             (0x5DE5, 'h', .3), (0x76EE, 'v', .5), (0x4E8C, 'h', .5)]
    fo, fs = freetype.Face(ours_path), freetype.Face(shs_path)
    to, ts = TTFont(ours_path, lazy=True), TTFont(shs_path, lazy=True)
    co, cs = to.getBestCmap(), ts.getBestCmap()
    T = []
    for c, ax, fr in tests:
        gs = ts.getGlyphID(cs[c])
        el, hv = stem(fs, gs, (250,), ax, fr), stem(fs, gs, (900,), ax, fr)
        row = [(stem(fo, to.getGlyphID(co[c]), (w, 100), ax, fr) - el) / (hv - el)
               for w in range(100, 901, 100)]
        T.append(row)
        print(chr(c), ' '.join('%6.3f' % x for x in row))
    print('mean', ' '.join('%6.3f' % x for x in np.mean(T, axis=0)))


if __name__ == '__main__':
    if sys.argv[1] == '--stems':
        stems(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else SHS_DEFAULT)
    else:
        select(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else SHS_DEFAULT)
