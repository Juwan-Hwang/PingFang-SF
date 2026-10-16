"""Step 6 (v1.1.1): real .notdef glyph, source-inconsistency fixes, recomputed global metrics.

usage: python step6_notdef_metrics.py IN.ttf OUT.ttf

1. .notdef: v1.0 left glyph 0 empty, so unmapped characters rendered as blank space.
   We copy PingFang UI TC's own .notdef (box with a ring inside, 4 contours) from the
   ACT-02/PingFangUI-VF 21.4d1e1 source, together with its gvar deltas (stroke weight
   follows wght, width follows wdth: 800/1000/1200 at wdth 80/100/120). Its HVAR advance
   variation is reproduced by pointing glyph 0 at the VarStore entry already used by
   full-width CJK ideographs (U+4E00), which has the identical 800/1000/1200 behaviour.
   vmtx: advance 1000, top side bearing = VORG(860) - yMax.
2. Global metrics are recomputed from the actual glyph outlines (default instance):
   head.xMin/xMax, hhea.advanceWidthMax/minLeftSideBearing/minRightSideBearing/xMaxExtent,
   vhea extents, maxp, OS/2.xAvgCharWidth (OS/2 v2 weighted a-z/space formula).
   NOT changed: hhea ascender/descender/lineGap, OS/2 typo*/winAscent/winDescent, and
   head.yMin/yMax, which stay pinned at PingFang UI's -232/902 on purpose (commit 828631a:
   some renderers derive line spacing from the head bbox; the true outline extremes come
   from stacked Tibetan/Devanagari marks and would loosen line spacing there).

   The widest advance (2872, U+102F90) is legitimate: it is an SF Pro private-use symbol
   (uni102F90.medium, 5882 units @ 2048 UPEM -> 5882*1000/2048 = 2872). See build/README.
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.varStore import VarStoreInstancer
from common import PF_TTC

PF_INDEX = 1   # PingFang UI TC inside the TTC (the base of this font)
HEAD_Y = (-232, 902)


def adv_at(f, g, loc):
    h = f['HVAR'].table
    idx = h.AdvWidthMap.mapping[g]
    return f['hmtx'][g][0] + VarStoreInstancer(h.VarStore, f['fvar'].axes, loc)[idx]


def copy_notdef(f):
    pf = TTFont(PF_TTC, fontNumber=PF_INDEX, lazy=True)
    assert [a.axisTag for a in pf['fvar'].axes] == [a.axisTag for a in f['fvar'].axes]
    assert pf['avar'].segments == f['avar'].segments
    src = pf['glyf']['.notdef']
    assert src.numberOfContours == 4
    glyf = f['glyf']
    glyf['.notdef'] = src
    glyf['.notdef'].recalcBounds(glyf)
    f['hmtx']['.notdef'] = pf['hmtx']['.notdef']                      # (1000, 87)
    f['gvar'].variations['.notdef'] = list(pf['gvar'].variations['.notdef'])
    # HVAR: reuse the varIdx of a full-width ideograph whose advance behaves the same
    locs = [{'wght': w, 'wdth': d} for w in (-1, 0, 1) for d in (-1, 0, 1)]
    want = [round(adv_at(pf, '.notdef', l)) for l in locs]
    ref = f.getBestCmap()[0x4E00]
    assert [round(adv_at(f, ref, l)) for l in locs] == want, (want, ref)
    amap = f['HVAR'].table.AdvWidthMap.mapping
    amap['.notdef'] = amap[ref]
    assert [round(adv_at(f, '.notdef', l)) for l in locs] == want
    # vertical: advance 1000, tsb from vertical origin
    vorg = f['VORG']
    vy = vorg.VOriginRecords.get('.notdef', vorg.defaultVertOriginY)
    f['vmtx']['.notdef'] = (1000, vy - glyf['.notdef'].yMax)
    print('.notdef: contours', src.numberOfContours, 'bbox',
          (src.xMin, src.yMin, src.xMax, src.yMax), 'hmtx', f['hmtx']['.notdef'],
          'vmtx', f['vmtx']['.notdef'], 'advance by wdth', want[:3])


# OS/2 version 0-2 definition of xAvgCharWidth: weighted average of a-z and space
# (fontTools' recalcAvgCharWidth implements the version 3+ all-glyph average instead).
AVG_WEIGHTS = dict(a=64, b=14, c=27, d=35, e=100, f=20, g=14, h=42, i=63, j=3, k=6, l=35, m=20,
                   n=56, o=56, p=17, q=4, r=49, s=56, t=71, u=31, v=10, w=18, x=3, y=18, z=2)


def recalc_avg_char_width(f):
    os2, cmap, hmtx = f['OS/2'], f.getBestCmap(), f['hmtx']
    if os2.version > 2:
        os2.recalcAvgCharWidth(f)
        return
    tot = sum(hmtx[cmap[ord(k)]][0] * w for k, w in AVG_WEIGHTS.items()) + hmtx[cmap[32]][0] * 166
    os2.xAvgCharWidth = round(tot / 1000)


def recalc_metrics(f):
    before = dict(head=(f['head'].xMin, f['head'].xMax),
                  hhea=(f['hhea'].advanceWidthMax, f['hhea'].minLeftSideBearing,
                        f['hhea'].minRightSideBearing, f['hhea'].xMaxExtent),
                  avg=f['OS/2'].xAvgCharWidth)
    keep = (f['hhea'].ascent, f['hhea'].descent, f['hhea'].lineGap,
            f['OS/2'].sTypoAscender, f['OS/2'].sTypoDescender, f['OS/2'].sTypoLineGap,
            f['OS/2'].usWinAscent, f['OS/2'].usWinDescent)
    glyf = f['glyf']
    xs = []
    for g in f.getGlyphOrder():
        G = glyf[g]
        if G.numberOfContours == 0:
            continue
        if not hasattr(G, 'xMin') or G.isComposite():
            G.recalcBounds(glyf)
        xs += [G.xMin, G.xMax]
    f['head'].xMin, f['head'].xMax = min(xs), max(xs)
    f['head'].yMin, f['head'].yMax = HEAD_Y
    f['hhea'].recalc(f)
    f['vhea'].recalc(f)
    f['maxp'].recalc(f)
    recalc_avg_char_width(f)
    assert keep == (f['hhea'].ascent, f['hhea'].descent, f['hhea'].lineGap,
                    f['OS/2'].sTypoAscender, f['OS/2'].sTypoDescender, f['OS/2'].sTypoLineGap,
                    f['OS/2'].usWinAscent, f['OS/2'].usWinDescent)
    after = dict(head=(f['head'].xMin, f['head'].xMax),
                 hhea=(f['hhea'].advanceWidthMax, f['hhea'].minLeftSideBearing,
                       f['hhea'].minRightSideBearing, f['hhea'].xMaxExtent),
                 avg=f['OS/2'].xAvgCharWidth)
    print('metrics before', before)
    print('metrics after ', after)
    widest = max(f['hmtx'].metrics.items(), key=lambda kv: kv[1][0])
    print('widest glyph', widest)


def is_ideograph(cp):
    return (0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
            or 0x20000 <= cp <= 0x3FFFF)


# U+A989..U+A995 (13 Javanese letters) were mapped to empty 1000-unit placeholder glyphs in
# v1.0 (the outlines are blank placeholders).
# Mapping a blank glyph hides the character: no fallback font and no .notdef box. Unmap them.
BLANK_PLACEHOLDERS = range(0xA989, 0xA996)


def fix_source_inconsistencies(f):
    glyf, hmtx, vmtx = f['glyf'], f['hmtx'], f['vmtx']
    cmap = f.getBestCmap()
    # 1. blank placeholders
    removed = []
    for t in f['cmap'].tables:
        for cp in BLANK_PLACEHOLDERS:
            g = t.cmap.get(cp)
            if g is not None:
                assert glyf[g].numberOfContours == 0, (hex(cp), g)
                del t.cmap[cp]
                removed.append(cp)
    print('unmapped blank placeholders:', sorted(set('U+%04X' % c for c in removed)))
    # 2. TH-Hak (UPEM 256) draws ~40 Ext-B ideographs on a 255-unit advance (source quirk);
    #    scaled that is 996, not 1000. The outlines are centred for 1000 (lsb 51, rsb 51).
    adv_fixed = []
    for cp, g in cmap.items():
        if is_ideograph(cp) and hmtx[g][0] == 996:
            hmtx[g] = (1000, hmtx[g][1])
            adv_fixed.append('U+%04X' % cp)
    print('ideograph advance 996 -> 1000:', len(adv_fixed), adv_fixed[:6])
    # 3. vmtx: v1.0 gave 17k imported glyphs (TH-Hak / Source Han Sans / symbols / SF) a
    #    vertical advance of 500 with tsb 0, so upright glyphs overlap in vertical text and
    #    sit at the wrong origin. PingFang UI uses advance 1000 and origin 860 for every glyph.
    vorg = f['VORG'].defaultVertOriginY
    n = 0
    for g, (adv, tsb) in list(vmtx.metrics.items()):
        if adv == 500 and tsb == 0 and hmtx[g][0] > 0:
            G = glyf[g]
            if G.numberOfContours != 0 and not hasattr(G, 'yMax'):
                G.recalcBounds(glyf)
            vmtx[g] = (1000, vorg - G.yMax if G.numberOfContours != 0 else 0)
            n += 1
    print('vmtx (500,0) -> (1000, VORG-yMax):', n)


def main(inp, outp):
    f = TTFont(inp, recalcBBoxes=False)
    copy_notdef(f)
    fix_source_inconsistencies(f)
    recalc_metrics(f)
    f.save(outp, reorderTables=True)
    print('saved', outp)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
