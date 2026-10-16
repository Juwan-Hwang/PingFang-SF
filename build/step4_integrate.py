"""Step 4: integrate PingFang UI GSUB, SF Pro (variable, with kerning) and the MiSans
script fonts (variable, with full GSUB/GPOS/GDEF) into the merged PingFang SF font.

usage: python step4_integrate.py IN.ttf OUT.ttf
"""
import copy, hashlib, json, os, sys, time
from collections import defaultdict
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot
from fontTools.varLib.models import piecewiseLinearMap
from fontTools import subset
from common import (PF_TTC, MISANS, WORK, MI_WGHT_MAP, target_norm)
from layout_merge import LayoutMerger, translate_tables
from step3_misans_vf import RANGES

PF_FEATURES = ['vert', 'locl', 'fwid', 'hwid', 'pwid', 'nalt']
SF_SCRIPTS = ['DFLT', 'latn', 'grek', 'cyrl']
# Only the script's own OpenType script tags are taken from each MiSans font; their
# DFLT/latn records only carry rules for the Latin glyphs that are not merged.
MI_SCRIPTS = {'Arabic': ['arab'], 'Devanagari': ['dev2', 'deva'], 'Gujarati': ['gjr2', 'gujr'],
              'Gurmukhi': ['gur2', 'guru'], 'Khmer': ['khmr'], 'Lao': ['lao '], 'Myanmar': ['mym2', 'mymr'],
              'Thai': ['thai'], 'Tibetan': ['tibt']}
T0 = time.time()


def log(*a):
    print('[%6.1fs]' % (time.time() - T0), *a, flush=True)


def ghash(font, name):
    glyf, hm = font['glyf'], font['hmtx']
    try:
        c, e, fl = glyf[name].getCoordinates(glyf)
    except Exception:
        return None
    return hashlib.md5(repr((list(c), list(e), [x & 1 for x in fl], hm[name][0])).encode()).hexdigest()


class Target:
    def __init__(self, path):
        self.f = TTFont(path)
        f = self.f
        self.go = list(f.getGlyphOrder())
        self.names = set(self.go)
        self.glyf, self.hmtx, self.vmtx = f['glyf'], f['hmtx'], f['vmtx']
        gv = f['gvar']
        v = {}
        bad = []
        for g in self.go:
            try:
                v[g] = gv.variations[g]
            except Exception:
                v[g] = []
                bad.append(g)
        gv.variations = v
        self.gvar = v
        log('target loaded; glyphs', len(self.go), 'undecodable gvar entries reset:', bad)
        self.cmap = f.getBestCmap()
        self.changed = set()
        self.hash = None

    def hashes(self):
        if self.hash is None:
            self.hash = defaultdict(list)
            for g in self.go:
                self.hash[ghash(self.f, g)].append(g)
        return self.hash

    def unique(self, base):
        n, i = base, 1
        while n in self.names:
            i += 1
            n = '%s.%d' % (base, i)
        return n

    def put_glyph(self, name, src, sname, name_map, new):
        """copy glyph sname from font src into target slot `name`."""
        g = copy.deepcopy(src['glyf'][sname])
        if g.isComposite():
            for c in g.components:
                c.glyphName = name_map[c.glyphName]
        if new:
            self.go.append(name)
            self.names.add(name)
        self.glyf.glyphs[name] = g
        self.hmtx.metrics[name] = src['hmtx'][sname]
        if 'vmtx' in src and sname in src['vmtx'].metrics:
            self.vmtx.metrics[name] = src['vmtx'][sname]
        elif new or name not in self.vmtx.metrics:
            self.vmtx.metrics[name] = (0, 0)       # fixed up later
        else:
            self.vmtx.metrics[name] = (0, 0)
        if 'gvar' in src:
            self.gvar[name] = copy.deepcopy(src['gvar'].variations.get(sname, []))
        else:
            self.gvar[name] = []
        self.changed.add(name)

    def add_cmap(self, cp, name):
        for t in self.f['cmap'].tables:
            if not t.isUnicode():
                continue
            if t.format == 4 and cp > 0xFFFF:
                continue
            t.cmap[cp] = name
        self.cmap[cp] = name


def integrate(target, P, name_map, modes, label):
    """modes[g] in {'keep','replace','new'} for every glyph g of P."""
    n = defaultdict(int)
    for g in P.getGlyphOrder():
        m = modes[g]
        n[m] += 1
        if m in ('replace', 'new'):
            target.put_glyph(name_map[g], P, g, name_map, m == 'new')
    log(label, dict(n))


# ---------------------------------------------------------------- PingFang UI
def prepare_pf(target):
    pf = TTFont(PF_TTC, fontNumber=1)       # PingFang UI TC (all faces share glyphs+GSUB)
    th = target.hashes()
    pf_go = pf.getGlyphOrder()
    keep = [g for g in pf_go if ghash(pf, g) in th]
    log('PF glyphs found in target', len(keep), 'of', len(pf_go))
    opts = subset.Options()
    opts.layout_features = PF_FEATURES
    opts.glyph_names = True; opts.notdef_outline = True; opts.hinting = False
    opts.name_IDs = ['*']; opts.name_languages = ['*']; opts.layout_closure = True
    opts.recalc_bounds = False; opts.prune_unicode_ranges = False
    s = subset.Subsetter(opts)
    s.populate(glyphs=keep)
    s.subset(pf)
    name_map, modes = {}, {}
    pcm = {}
    for cp, g in pf.getBestCmap().items():
        pcm.setdefault(g, cp)
    used = set()
    for g in pf.getGlyphOrder():
        h = ghash(pf, g)
        cands = th.get(h, [])
        tgt = None
        if cands:
            cp = pcm.get(g)
            if cp is not None and target.cmap.get(cp) in cands:
                tgt = target.cmap[cp]
            else:
                free = [c for c in cands if c not in used]
                tgt = (free or cands)[0]
        if tgt:
            name_map[g], modes[g] = tgt, 'keep'
            used.add(tgt)
        else:
            name_map[g], modes[g] = target.unique('pf.' + g), 'new'
            target.names.add(name_map[g])
    return pf, name_map, modes


# ---------------------------------------------------------------- SF Pro
def prepare_sf(target, pf_hashes):
    P = TTFont(os.path.join(WORK, 'sf_vf.ttf'))
    rc = {}
    for cp, g in P.getBestCmap().items():
        rc.setdefault(g, cp)
    name_map, modes, used = {}, {}, set()
    for g in P.getGlyphOrder():
        if g == '.notdef':
            name_map[g], modes[g] = '.notdef', 'keep'
            continue
        cp = rc.get(g)
        tg = target.cmap.get(cp) if cp is not None else None
        if tg and tg not in used:
            used.add(tg)
            name_map[g] = tg
            modes[g] = 'keep' if ghash(target.f, tg) in pf_hashes else 'replace'
        else:
            name_map[g] = target.unique('sf.' + g)
            target.names.add(name_map[g])
            modes[g] = 'new'
    return P, name_map, modes


# ---------------------------------------------------------------- MiSans
def prepare_mi(target, script):
    P = TTFont(os.path.join(WORK, f'mi_{script}_vf.ttf'))
    S = TTFont(os.path.join(WORK, f'mi_{script}_vf_subset.ttf'))
    assert S.getGlyphOrder() == P.getGlyphOrder()
    th = target.hashes()
    rc = {}
    for cp, g in P.getBestCmap().items():
        rc.setdefault(g, []).append(cp)
    tenc = set(target.cmap.values())
    name_map, modes, used, newcps = {}, {}, set(), []
    for g in P.getGlyphOrder():
        if g == '.notdef':
            name_map[g], modes[g] = '.notdef', 'keep'
            continue
        tg = None
        for cp in rc.get(g, []):
            if cp in target.cmap and target.cmap[cp] not in used:
                tg = target.cmap[cp]
                break
        if tg is None and g not in rc:
            for c in th.get(ghash(S, g), []):
                if c not in used and c not in tenc:
                    tg = c
                    break
        if tg is not None:
            used.add(tg)
            name_map[g], modes[g] = tg, 'replace'
        else:
            name_map[g] = target.unique('mi%s.%s' % (script, g))
            target.names.add(name_map[g])
            modes[g] = 'new'
            for cp in rc.get(g, []):
                if cp not in target.cmap:
                    newcps.append((cp, name_map[g]))
    return P, S, name_map, modes, newcps


def mi_fv_conditions(src_font):
    ax = src_font['fvar'].axes[0]
    inv = {float(v): float(k) for k, v in MI_WGHT_MAP.items()}

    def fn(condset):
        out = ot.ConditionSet()
        out.ConditionTable = []
        for c in condset.ConditionTable:
            def conv(v):
                user = ax.defaultValue + v * ((ax.maxValue - ax.defaultValue) if v >= 0 else (ax.defaultValue - ax.minValue))
                tu = piecewiseLinearMap(user, inv)
                return round(target_norm({'wght': tu})['wght'], 4)
            n = ot.ConditionTable()
            n.Format = 1
            n.AxisIndex = 0
            n.FilterRangeMinValue = conv(c.FilterRangeMinValue)
            n.FilterRangeMaxValue = conv(c.FilterRangeMaxValue)
            out.ConditionTable.append(n)
        out.ConditionCount = len(out.ConditionTable)
        log('   FeatureVariations condition', [(c.FilterRangeMinValue, c.FilterRangeMaxValue) for c in condset.ConditionTable],
            '->', [(c.FilterRangeMinValue, c.FilterRangeMaxValue) for c in out.ConditionTable])
        return out
    return fn


def main(inp, outp):
    target = Target(inp)
    f = target.f
    merger = LayoutMerger(axis_count=len(f['fvar'].axes))

    # 1. PingFang UI: CJK GSUB (vert/locl/fwid/hwid/pwid/nalt) + missing alternates
    pf, pmap, pmodes = prepare_pf(target)
    integrate(target, pf, pmap, pmodes, 'PingFang UI')
    pf_hashes = set(ghash(pf, g) for g in pf.getGlyphOrder())
    merger.add_source(translate_tables(pf, pmap))
    del pf

    # 2. SF Pro
    P, smap, smodes = prepare_sf(target, pf_hashes)
    integrate(target, P, smap, smodes, 'SF Pro')
    merger.add_source(translate_tables(P, smap), scripts_filter=SF_SCRIPTS, override_classes=True)

    # 3. MiSans scripts
    for script in MISANS:
        P, S, mmap, mmodes, newcps = prepare_mi(target, script)
        integrate(target, P, mmap, mmodes, 'MiSans ' + script)
        for cp, name in newcps:
            target.add_cmap(cp, name)
        tabs = translate_tables(P, mmap, ('GPOS', 'GDEF'))
        gsub = translate_tables(S, mmap, ('GSUB',))
        tabs.update(gsub)
        merger.add_source(tabs, scripts_filter=MI_SCRIPTS[script], override_classes=True,
                          fv_conditions_fn=mi_fv_conditions(S))
        log('   new codepoints', len(newcps))

    # 4. commit glyph order + layout
    f.setGlyphOrder(target.go)
    target.glyf.glyphOrder = target.go
    merger.build(f)
    log('layout merged: GSUB lookups', len(f['GSUB'].table.LookupList.Lookup),
        'GPOS lookups', len(f['GPOS'].table.LookupList.Lookup))

    # 5. bounds for changed glyphs, vertical metrics for glyphs that had none
    for g in target.changed:
        target.glyf[g].recalcBounds(target.glyf)
    vorg = f['VORG'].defaultVertOriginY if 'VORG' in f else f['hhea'].ascent
    fixed = 0
    for g in target.go:
        adv, tsb = target.vmtx.metrics.get(g, (0, 0))
        if adv == 0 and target.hmtx.metrics[g][0] > 0:
            gl = target.glyf[g]
            ymax = getattr(gl, 'yMax', None)
            target.vmtx.metrics[g] = (1000, (vorg - ymax) if ymax is not None and gl.numberOfContours != 0 else 0)
            fixed += 1
    log('vmtx fixed for', fixed, 'glyphs with zero vertical advance')

    # 5b. a few glyphs (from the original CFF->TrueType conversion) carry cubic-curve
    # flags (0x80), which OTS/browsers/Windows reject -> convert them to quadratic.
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    ncub = 0
    for g in target.go:
        gl = target.glyf[g]
        if gl.numberOfContours > 0 and any(fl & 0x80 for fl in gl.flags):
            assert not target.gvar.get(g), g
            pen = TTGlyphPen(None)
            gl.draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=False), target.glyf)
            ng = pen.glyph()
            ng.recalcBounds(target.glyf)
            target.glyf.glyphs[g] = ng
            adv = target.hmtx.metrics[g][0]
            target.hmtx.metrics[g] = (adv, getattr(ng, 'xMin', 0))
            ncub += 1
    log('cubic glyphs converted to quadratic:', ncub)

    # 6. HVAR from gvar phantom points (the old HVAR mapped added glyphs to CJK deltas)
    from fontTools.varLib.hvar import add_HVAR
    if 'HVAR' in f:
        del f['HVAR']
    add_HVAR(f)
    log('HVAR rebuilt')

    f['OS/2'].recalcUnicodeRanges(f)
    f.save(outp)
    log('saved', outp, os.path.getsize(outp))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
