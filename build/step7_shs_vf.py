"""Step 7 (v1.2.0): make the Source Han Sans-derived glyphs weight-variable.

usage: python step7_shs_vf.py IN.ttf OUT.ttf [SourceHanSans-VF.ttf]

v1.0 imported ~5,950 code points from TH-Hak 4.0.0 (天珩字库-黑体) without variation data.
For 759 of them (kana, bopomofo extensions, CJK symbols, enclosed/squared CJK, CJK strokes,
some Ext-B..H ideographs, symbols) the TH-Hak outline is itself Source Han Sans, Japanese
default form, at roughly Regular weight (re-quantised to TH-Hak's 256 UPM).  They are
listed in data/shs_vf_glyphs.tsv (produced by shs_select.py, which compares the current
outline with every Source Han Sans regional form at every weight).  The TSV's third column
names the SHS glyph actually used: the JAN default form, or (since v1.2.0, 7 glyphs:
⁇ ⁈ ⁉ ㍿ 🈻 𣟱 𨓜) the ZHT `locl` form where Traditional Chinese differs.

Each listed glyph is replaced IN PLACE (same glyph name/ID, same cmap, same GSUB/GPOS
references; glyph count unchanged) by the same glyph from Adobe's variable
Source Han Sans 2.005 (Variable/TTF/SourceHanSans-VF.ttf, glyf, UPM 1000 = ours).

Weight mapping.  Source Han Sans VF is a 2-master design: outline = EL + t*(Heavy-EL),
t in [0,1] (t is the post-avar normalised coordinate).  Matching the stem thickness of
PingFang UI's own ideographs (一 三 川 丨 工 目 二, measured by shs_select.py --stems)
at our wght 100..900 gives, in OUR post-avar normalised coordinate n:
      wght 100 (n=-1): t = -0.063   (PingFang Ultralight is thinner than SHS ExtraLight;
                                     6% extrapolation of the SHS master vector)
      wght 500 (n= 0): t =  0.519   (≈ SHS user weight 476)
      wght 900 (n=+1): t =  0.985   (≈ SHS Heavy)
and t is linear in n on each side of the default (all 9 named instances fit within 0.01),
so every glyph needs only the two tuples PingFang itself uses: wght(-1,-1,0) and wght(0,1,1).
No wdth variation (as before).

Metrics: advance widths stay as they were, except for 5 proportional glyphs whose SHS
advance varies with weight (⁇ ⁈ ⁉ 🄯 🅬): their default advance and HVAR deltas
follow SHS (HVAR rows appended to the VarData that already holds region 14/15 rows).
lsb = xMin; vmtx keeps the vertical advance and recomputes tsb = VORG - yMax.
"""
import sys, os, copy
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.varLib.iup import iup_delta
from step6_notdef_metrics import recalc_metrics

T_MIN, T_DEF, T_MAX = -0.063, 0.519, 0.985
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, 'data', 'shs_vf_glyphs.tsv')
SRC = os.environ.get('PFSF_SRC', os.path.join(HERE, '..', 'sources'))
SHS_DEFAULT = os.path.join(SRC, 'shs', 'SourceHanSans-VF.ttf')
REG_MIN = {'wght': (-1.0, -1.0, 0.0)}
REG_MAX = {'wght': (0.0, 1.0, 1.0)}


def load_list():
    rows = []
    for line in open(TSV, encoding='utf-8'):
        if line.startswith('#') or not line.strip():
            continue
        cp, ours, shs, region, adv = line.rstrip('\n').split('\t')
        rows.append((int(cp[2:], 16), ours, shs, region, adv))
    return rows


def shs_master_vector(S, g):
    """(EL coordinates, Heavy-EL deltas incl. 4 phantom points, endPts, glyph)"""
    glyf = S['glyf']
    G = glyf[g]
    assert not G.isComposite() and G.numberOfContours > 0, g
    co, ends, _ = G.getCoordinates(glyf)
    n = len(co)
    vs = S['gvar'].variations.get(g, [])
    assert len(vs) == 1 and vs[0].axes == {'wght': (0.0, 1.0, 1.0)}, (g, [v.axes for v in vs])
    d = vs[0].coordinates
    adv = S['hmtx'][g][0]
    phantom = [(G.xMin - S['hmtx'][g][1], 0), (G.xMin - S['hmtx'][g][1] + adv, 0), (0, 0), (0, 0)]
    if any(c is None for c in d):
        d = iup_delta(list(d), list(co) + phantom, list(ends))
    return list(co), [tuple(x) for x in d], list(ends), G, adv


def main(inp, out, shs_path=SHS_DEFAULT):
    rows = load_list()
    f = TTFont(inp, recalcBBoxes=False, recalcTimestamp=False)
    S = TTFont(shs_path)
    assert S['head'].unitsPerEm == f['head'].unitsPerEm == 1000
    assert [a.axisTag for a in S['fvar'].axes] == ['wght']
    glyf, gvar, hmtx, vmtx = f['glyf'], f['gvar'], f['hmtx'], f['vmtx']
    vorg = f['VORG']
    hv = f['HVAR'].table
    amap = hv.AdvWidthMap.mapping
    regions = hv.VarStore.VarRegionList.Region

    def reg_idx(spec):
        for i, r in enumerate(regions):
            ax = {a: (round(x.StartCoord, 3), round(x.PeakCoord, 3), round(x.EndCoord, 3))
                  for a, x in zip(('wght', 'wdth'), r.VarRegionAxis)
                  if (x.StartCoord, x.PeakCoord, x.EndCoord) != (0, 0, 0)}
            if ax == spec:
                return i
        raise KeyError(spec)
    rmin, rmax = reg_idx(REG_MIN), reg_idx(REG_MAX)
    # VarData holding exactly [region(-1), region(+1)] rows, for proportional glyphs
    vd_i = next(i for i, d in enumerate(hv.VarStore.VarData)
                if sorted(d.VarRegionIndex) == sorted([rmin, rmax]) and d.ItemCount < 65000)
    vd = hv.VarStore.VarData[vd_i]
    col = {r: vd.VarRegionIndex.index(r) for r in (rmin, rmax)}
    zero_rows = []  # an existing all-zero advance row, for fixed-advance glyphs

    def adv_deltas(g):
        idx = amap[g]
        return hv.VarStore.VarData[idx >> 16].Item[idx & 0xFFFF]

    n_before = len(f.getGlyphOrder())
    cmap = f.getBestCmap()
    done = 0
    for cp, ours, shs, region, advmode in rows:
        assert cmap.get(cp) == ours, (hex(cp), cmap.get(cp), ours)
        assert not any(c for v in gvar.variations.get(ours, []) for c in v.coordinates if c and c != (0, 0)), ours
        el, D, ends, SG, sadv = shs_master_vector(S, shs)
        n = len(el)

        def at(t):
            return [(round(x + t * dx), round(y + t * dy)) for (x, y), (dx, dy) in zip(el, D[:n])]
        p0, pm, pM = at(T_DEF), at(T_MIN), at(T_MAX)
        G = copy.deepcopy(SG)
        G.coordinates = GlyphCoordinates(p0)
        if hasattr(G, 'program'):
            G.program.fromBytecode(b'')
        glyf[ours] = G
        G.recalcBounds(glyf)
        old_adv = hmtx[ours][0]
        if advmode == 'prop':
            dadv = D[n + 1][0] - D[n][0]
            a0 = round(sadv + T_DEF * dadv)
            am, aM = round(sadv + T_MIN * dadv) - a0, round(sadv + T_MAX * dadv) - a0
            item = [0] * len(vd.VarRegionIndex)
            item[col[rmin]], item[col[rmax]] = am, aM
            vd.Item.append(item)
            vd.ItemCount = len(vd.Item)
            amap[ours] = (vd_i << 16) | (vd.ItemCount - 1)
        else:
            a0, am, aM = old_adv, 0, 0
            assert not any(adv_deltas(ours)), (ours, adv_deltas(ours))
        hmtx[ours] = (a0, G.xMin)
        vy = vorg.VOriginRecords.get(ours, vorg.defaultVertOriginY)
        vmtx[ours] = (vmtx[ours][0], vy - G.yMax)
        # gvar: two tuples, phantom points carry the advance change (rsb phantom)
        orig = GlyphCoordinates(p0 + [(0, 0), (a0, 0), (0, 0), (0, 0)])
        tvs = []
        for axes, pts, da in ((REG_MIN, pm, am), (REG_MAX, pM, aM)):
            deltas = [(a - b, c - d) for (a, c), (b, d) in zip(pts, p0)] + [(0, 0), (da, 0), (0, 0), (0, 0)]
            tv = TupleVariation(dict(axes), deltas)
            tv.optimize(orig, ends, tolerance=0.5)
            tvs.append(tv)
        gvar.variations[ours] = tvs
        done += 1
    assert len(f.getGlyphOrder()) == n_before
    recalc_metrics(f)          # head x-extent, hhea/vhea, maxp (head.yMin/yMax stay pinned)
    f.save(out, reorderTables=True)
    print('step7: %d glyphs made weight-variable from %s; glyphs %d -> %d'
          % (done, os.path.basename(shs_path), n_before, len(TTFont(out, lazy=True).getGlyphOrder())))


if __name__ == '__main__':
    main(*sys.argv[1:])
