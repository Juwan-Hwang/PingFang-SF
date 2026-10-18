"""v1.2.0 fill: build one self-contained "part" font per source, in the target design space.

A part is a subset of one source font holding the codepoints a fill tranche asks for (plus
every glyph its own GSUB reaches), scaled to 1000 UPM and

  * variable sources: instanced at the source weight that matches target wght 100/500/900
    and rebuilt as a variable font on the *normalized* target axes (wght/wdth, -1000..1000,
    like vf_from_masters.py), so its gvar / GDEF VarStore can be copied into the target;
    CFF/CFF2 masters are converted to quadratic TrueType *jointly* (Cu2QuMultiPen), so the
    masters stay point-compatible;
  * static sources: kept static (no gvar); CFF converted with Cu2QuPen.

A spec may also remap codepoints (`cpmap`: target cp -> source cp), used for the
mathematical alphanumerics, which are drawn from the plain letters of SF Pro / New York /
SF Mono at the matching style.

usage: python fill_parts.py SPEC.json OUTDIR [part-id ...]
"""
import json, os, sys, copy
from fontTools.ttLib import TTFont, newTable
from fontTools.varLib import instancer, build as varlib_build
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.cu2quPen import Cu2QuMultiPen, Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.varLib.models import piecewiseLinearMap
from fontTools import subset
from common import target_norm, SF_WGHT_MAP

DROP = ['MERG', 'trak', 'MVAR', 'STAT', 'meta', 'DSIG', 'VVAR', 'vhea', 'vmtx', 'kern', 'morx', 'feat',
        'VORG', 'BASE', 'JSTF', 'MATH', 'hdmx', 'LTSH', 'VDMX', 'gasp', 'prep', 'fpgm', 'cvt ', 'cvar',
        'ankr', 'just', 'prop', 'opbd', 'lcar', 'fond', 'Zapf', 'bsln', 'cmap_', 'COLR', 'CPAL', 'SVG ',
        'sbix', 'CBDT', 'CBLC', 'EBDT', 'EBLC', 'avar', 'xref', 'mort', 'Silf', 'Glat', 'Gloc', 'Feat', 'Sill']
TARGET_W = (100, 500, 900)
SRC_ROOT = os.environ.get('PFSF_FILL_SRC', os.path.join(os.path.dirname(__file__), '..', '..'))


def wmap_value(spec, w):
    """source wght for target wght w."""
    kind = spec.get('wmap', 'same')
    if kind == 'static':
        return None
    if spec.get('bold'):
        w = min(w + 300, 900)
    if kind == 'sf':
        v = piecewiseLinearMap(w, {float(k): float(x) for k, x in SF_WGHT_MAP.items()})
    elif isinstance(kind, dict):
        v = float(kind[str(w)])
    else:
        v = float(w)
    return v


def src_loc(font, spec, w):
    loc = {}
    for a in font['fvar'].axes:
        if a.axisTag == 'wght':
            v = wmap_value(spec, w)
        elif a.axisTag == 'opsz':
            v = 17 if a.minValue <= 17 <= a.maxValue else a.defaultValue
        elif a.axisTag == 'wdth':
            v = 100 if a.minValue <= 100 <= a.maxValue else a.defaultValue
        else:
            v = spec.get('pin', {}).get(a.axisTag, a.defaultValue)
        loc[a.axisTag] = max(a.minValue, min(a.maxValue, v))
    return loc


def do_subset(f, unicodes, keep_layout, scripts):
    opts = subset.Options()
    opts.layout_features = ['*'] if keep_layout else []
    opts.layout_scripts = scripts if (keep_layout and scripts) else ['*']
    opts.name_IDs = ['*']; opts.name_languages = ['*']
    opts.glyph_names = True; opts.notdef_outline = True; opts.hinting = False
    opts.layout_closure = True; opts.drop_tables += DROP
    opts.prune_unicode_ranges = False; opts.recalc_bounds = True
    opts.legacy_kern = False; opts.desubroutinize = True
    opts.ignore_missing_unicodes = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=unicodes)
    sub.subset(f)
    if not keep_layout:
        for t in ('GSUB', 'GPOS', 'GDEF'):
            if t in f:
                del f[t]
    return f


class _KeepPen(TTGlyphPen):
    """TTGlyphPen that keeps a contour's duplicate closing point; dropped later only when it
    is a duplicate in every master (TTGlyphPen decides per master, breaking compatibility)."""
    def closePath(self):
        endPt = len(self.points) - 1
        if endPt == 0 or (self.endPts and endPt == self.endPts[-1] + 1):
            self._popPoint()
            return
        if not self.points:
            return
        self.endPts.append(endPt)


def _joint_dedupe(pens):
    n = len(pens[0].endPts)
    assert all(len(p.endPts) == n and len(p.points) == len(pens[0].points) for p in pens)
    drop = []
    start = 0
    for e in pens[0].endPts:
        if e > start and all(p.points[start] == p.points[e] and p.types[e] == 1 for p in pens):
            drop.append(e)
        start = e + 1
    for p in pens:
        for e in reversed(drop):
            del p.points[e]; del p.types[e]
        ends, k = [], 0
        for e in p.endPts:
            k += 1 if e in drop else 0
            ends.append(e - (sum(1 for d in drop if d <= e)))
        p.endPts = ends


def cff_to_glyf(masters, gsets=None):
    """Convert one or more point-compatible CFF/CFF2 fonts to TrueType outlines in place.
    gsets: glyph sets to draw from (default: the masters' own); for CFF2 masters these are
    the source VF's glyph sets at the master locations, because instanced CFF2 charstrings
    are re-specialized per master and lose point compatibility."""
    order = masters[0].getGlyphOrder()
    gsets = gsets or [m.getGlyphSet() for m in masters]
    glyphs = [{} for _ in masters]
    for g in order:
        recs = []
        for gs in gsets:
            rp = RecordingPen()
            gs[g].draw(rp)
            recs.append(rp)
        pens = [_KeepPen(None) for _ in masters]
        if len(masters) > 1:
            mp = Cu2QuMultiPen(pens, max_err=1.0, reverse_direction=False)
            for ops in zip(*[r.value for r in recs]):
                op = ops[0][0]
                assert all(o[0] == op for o in ops), (g, [o[0] for o in ops])
                if op in ('closePath', 'endPath'):
                    getattr(mp, op)()
                else:
                    getattr(mp, op)([o[1] for o in ops])
        else:
            p = Cu2QuPen(pens[0], max_err=1.0, reverse_direction=False)
            recs[0].replay(p)
        _joint_dedupe(pens)
        for i, pen in enumerate(pens):
            glyphs[i][g] = pen.glyph()
    for i, m in enumerate(masters):
        for t in ('CFF ', 'CFF2', 'VORG'):
            if t in m:
                del m[t]
        glyf = newTable('glyf'); glyf.glyphOrder = order; glyf.glyphs = glyphs[i]
        m['glyf'] = glyf
        m['loca'] = newTable('loca')
        m['head'].glyphDataFormat = 0
        maxp = m['maxp']
        maxp.tableVersion = 0x00010000
        for k in ('maxZones', 'maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs',
                  'maxStackElements', 'maxSizeOfInstructions', 'maxComponentElements', 'maxPoints',
                  'maxContours', 'maxCompositePoints', 'maxCompositeContours', 'maxComponentDepth'):
            setattr(maxp, k, 0)
        maxp.maxZones = 1
        post = m['post']
        if post.formatType == 3.0:
            post.formatType = 2.0
            post.extraNames = []; post.mapping = {}
        for g in order:
            glyphs[i][g].recalcBounds(glyf)
        # lsb = xMin for TrueType
        hm = m['hmtx'].metrics
        for g in order:
            gl = glyphs[i][g]
            hm[g] = (hm[g][0], getattr(gl, 'xMin', 0) if gl.numberOfContours else 0)
        if 'HVAR' in m:
            del m['HVAR']


def apply_cpmap(f, cpmap):
    """cmap := {target cp: glyph of source cp}"""
    cm = f.getBestCmap()
    new = {int(t): cm[int(s)] for t, s in cpmap.items() if int(s) in cm}
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    if not any(t.format == 12 for t in f['cmap'].tables):
        st = CmapSubtable.newSubtable(12); st.platformID, st.platEncID, st.language = 3, 10, 0
        st.cmap = {}
        f['cmap'].tables.append(st)
    for t in f['cmap'].tables:
        if t.isUnicode():
            t.cmap = {cp: g for cp, g in new.items() if t.format != 4 or cp <= 0xFFFF}
    return new


def scale(f, factor):
    upm = f['head'].unitsPerEm
    if factor == 1.0 and upm == 1000:
        return
    f['head'].unitsPerEm = upm / factor
    scale_upem(f, 1000)
    f['head'].unitsPerEm = 1000


def build_part(spec, outdir):
    pid = spec['id']
    path = os.path.join(SRC_ROOT, spec['src'])
    f = TTFont(path, fontNumber=spec.get('face', 0), lazy=False)
    for t in DROP:
        if t in f:
            del f[t]
    cpmap = spec.get('cpmap')
    cps = [int(c) for c in (cpmap.values() if cpmap else spec['cps'])]
    keep_layout = bool(spec.get('scripts'))
    pre_ms = None; vf_gsets = None
    if 'CFF2' in f and 'fvar' in f and spec.get('wmap') != 'static':
        # the instancer cannot handle subset CFF2 (vsindex/blend after desubroutinizing):
        # instance the full face first, then subset each master identically.
        pre_ms = [instancer.instantiateVariableFont(f, src_loc(f, spec, w), inplace=False, updateFontNames=False)
                  for w in TARGET_W]
        for m in pre_ms:
            do_subset(m, cps, keep_layout, spec.get('scripts') or [])
            if cpmap:
                apply_cpmap(m, cpmap)
            assert m.getGlyphOrder() == pre_ms[0].getGlyphOrder()
        vf_gsets = [f.getGlyphSet(location=src_loc(f, spec, w), normalized=False) for w in TARGET_W]
        f = pre_ms[0]
    else:
        do_subset(f, cps, keep_layout, spec.get('scripts') or [])
        if cpmap:
            apply_cpmap(f, cpmap)
    have = set(f.getBestCmap())
    want = set(int(c) for c in (cpmap.keys() if cpmap else spec['cps']))
    missing = sorted(want - have)
    is_cff = 'CFF ' in f or 'CFF2' in f
    variable = (pre_ms is not None) or ('fvar' in f and spec.get('wmap') != 'static')
    if 'fvar' in f and not variable and pre_ms is None:
        f = instancer.instantiateVariableFont(f, src_loc(f, spec, 500), inplace=False, updateFontNames=False)
    if 'GSUB' in f and getattr(f['GSUB'].table, 'FeatureVariations', None) is not None:
        f['GSUB'].table.FeatureVariations = None
        f['GSUB'].table.Version = 0x00010000
    sc = float(spec.get('scale', 1.0))
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, pid + '.ttf')
    if not variable:
        if is_cff:
            cff_to_glyf([f])
        scale(f, sc)
        for t in ('fvar', 'gvar', 'HVAR', 'avar', 'cvar', 'STAT'):
            if t in f:
                del f[t]
        f.save(out)
    else:
        if pre_ms is not None:
            ms = pre_ms
        else:
            locs = [src_loc(f, spec, w) for w in TARGET_W]
            ms = [instancer.instantiateVariableFont(f, l, inplace=False, updateFontNames=False) for l in locs]
        if is_cff:
            cff_to_glyf(ms, vf_gsets if pre_ms is not None else None)
        tmp = os.path.join(outdir, '_m_' + pid)
        os.makedirs(tmp, exist_ok=True)
        ds = DesignSpaceDocument()
        for t in ('wght', 'wdth'):
            a = AxisDescriptor(); a.tag = t; a.name = t
            a.minimum, a.default, a.maximum = -1000, 0, 1000
            ds.addAxis(a)
        for i, (w, m) in enumerate(zip(TARGET_W, ms)):
            scale(m, sc)
            for t in ('fvar', 'gvar', 'HVAR', 'avar', 'STAT'):
                if t in m:
                    del m[t]
            p = os.path.join(tmp, f'm{i}.ttf'); m.save(p)
            n = target_norm({'wght': w, 'wdth': 100})
            s = SourceDescriptor(); s.path = p; s.name = f'm{i}'
            s.location = {'wght': n['wght'] * 1000, 'wdth': n['wdth'] * 1000}
            ds.addSource(s)
        vf, _, _ = varlib_build(ds, exclude=['STAT', 'MVAR', 'name'], optimize=True)
        vf.save(out)
    g = TTFont(out)
    info = {'id': pid, 'src': spec['src'], 'face': spec.get('face', 0), 'variable': variable,
            'glyphs': len(g.getGlyphOrder()) - 1, 'codepoints': len(set(g.getBestCmap()) & want),
            'missing': ['%04X' % c for c in missing], 'scripts': spec.get('scripts') or [],
            'locs': [src_loc(TTFont(path, fontNumber=spec.get('face', 0), lazy=True), spec, w) for w in TARGET_W]
            if variable else None}
    json.dump(info, open(out[:-4] + '.json', 'w'), indent=1)
    print(pid, info['glyphs'], 'glyphs', info['codepoints'], 'cps', 'missing', len(missing), flush=True)
    return info


if __name__ == '__main__':
    specs = json.load(open(sys.argv[1]))
    if isinstance(specs, dict):
        specs = specs['plan'] + [s for b in specs['backfill'] for s in b['specs']]
    outdir = sys.argv[2]
    only = set(sys.argv[3:])
    for s in specs:
        if only and s['id'] not in only:
            continue
        if os.path.exists(os.path.join(outdir, s['id'] + '.json')) and os.environ.get('FORCE') != '1':
            print('skip', s['id']); continue
        build_part(s, outdir)
