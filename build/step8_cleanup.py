"""Step 8 (v1.2.0): glyph-slot cleanup and P0 additions.

usage: python step8_cleanup.py IN.ttf OUT.ttf [report.json]

In order:
  1. SF Symbols: unmap U+100000..U+1042F5 (Supplementary PUA-B).  Their glyphs, and every
     glyph only reachable through them (GSUB alternates, composite-only parts), are dropped
     by the prune in step 6.  U+F8FF and the rest of the BMP PUA (GB 18030 / HKSCS legacy)
     are kept unchanged.
  2. Emoji: unmap the characters whose Unicode default presentation is emoji
     (Emoji_Presentation=Yes, list in data/emoji_presentation_unmap.txt, generated from
     Unicode 17 emoji-data.txt), so the OS colour-emoji font is used.  Text-default
     characters (VS15/VS16 behaviour) are untouched.  Glyphs still referenced elsewhere
     survive the prune; the rest are dropped.
  3. Exact duplicates: cmapped, non-empty glyphs with identical outline (incl. instructions),
     gvar tuples (all axes), advance/LSB, vmtx, VORG, HVAR advance deltas, GDEF glyph class,
     mark-attachment class, mark-set membership, attach points and caret list.  A pair is
     merged only if the two glyphs are *interchangeable in every GSUB/GPOS lookup*: every
     input-side fact (coverage membership, ClassDef class, substitution input, ligature
     first glyph / component position, context rule position, kerning pair / class,
     anchors, value records) of one glyph equals that of the other once the two names are
     identified.  Different kern classes, GDEF classes or GSUB contexts -> pair skipped.
     The loser's cmap entries, composite references and GSUB *output* references are
     repointed to the keeper; its input-side entries become unreachable and the prune
     removes the glyph (and those entries).
  4. P0 additions:
       U+20C1 SAUDI RIYAL SIGN  - SF Pro's own glyph (riyalsaudisign), variable wght+wdth,
                                  built in the same design space as step 2's SF Pro masters;
       U+20C0 SOM SIGN          - not in SF Pro: constructed per master from SF Pro's
                                  Cyrillic Es (U+0421) plus an underline bar spanning the
                                  Es and taking the thickness / position of SF Pro's own
                                  underscore at that master (NBKR: "capital letter C with
                                  an underscore"), so it varies in wght and wdth like ₽ ₸;
       one shared empty zero-advance glyph 'ignorable.zw' for default-ignorable / invisible
       characters not yet mapped (FE00-FE0F, E0100-E01EF, 180B-180F, 2060-2064,
       2066-2069, 061C, E0001, E0020-E007F, Hangul fillers 115F 1160 3164 FFA0).
       The font has no cmap14 / morx, so variation selectors keep working: HarfBuzz /
       DirectWrite treat them as default-ignorable and they no longer show as tofu in GDI.
  5. HVAR rebuilt from gvar phantom points (as in step 4).
  6. Prune: fontTools subsetter closure over the remaining cmap with all scripts/features,
     composites and GSUB closure; drops true orphans (incl. ~1,270 leftover v1.0 Arabic
     glyphs that no lookup of the merged MiSans Arabic GSUB references), the glyphs freed
     by 1-3, and unreferenced lookups.  Tables, names, BASE/VORG/STAT are kept.
"""
import sys, os, json, copy, collections, time
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools import subset
from step6_notdef_metrics import recalc_metrics

HERE = os.path.dirname(os.path.abspath(__file__))
EMOJI_LIST = os.path.join(HERE, 'data', 'emoji_presentation_unmap.txt')
SF_SYMBOLS = (0x100000, 0x1042F5)
IGNORABLES = (list(range(0xFE00, 0xFE10)) + list(range(0xE0100, 0xE01F0)) + list(range(0x180B, 0x1810))
              + list(range(0x2060, 0x2065)) + list(range(0x2066, 0x206A)) + [0x061C, 0xE0001]
              + list(range(0xE0020, 0xE0080)) + [0x115F, 0x1160, 0x3164, 0xFFA0])
T0 = time.time()


def log(*a):
    print('[step8 %6.1fs]' % (time.time() - T0), *a, flush=True)


# ------------------------------------------------------------------ cmap helpers
def unicode_subtables(f):
    return [t for t in f['cmap'].tables if t.isUnicode()]


def unmap(f, cps):
    n = 0
    for t in unicode_subtables(f):
        for c in cps:
            if c in t.cmap:
                del t.cmap[c]
                n += 1
    return n


def add_map(f, cp, g):
    for t in unicode_subtables(f):
        if t.format == 4 and cp > 0xFFFF:
            continue
        t.cmap[cp] = g


def closure(f, cps):
    """glyphs reachable from cps (+ .notdef) via GSUB (all features) and composites."""
    o = subset.Options()
    o.layout_features = ['*']; o.layout_scripts = ['*']; o.notdef_outline = True
    o.glyph_names = True; o.layout_closure = True; o.drop_tables = []
    s = subset.Subsetter(o)
    s.populate(unicodes=list(cps))
    s._closure_glyphs(f)
    return set(s.glyphs_retained)


# ------------------------------------------------------------------ layout facts
class G(tuple):
    """a glyph reference inside a fact (so names can be identified safely)"""
    def __new__(cls, n):
        return tuple.__new__(cls, ('\0g', n))


def ser(o, depth=0):
    if o is None or isinstance(o, (int, float, str, bytes)):
        return o
    if isinstance(o, (list, tuple)):
        return tuple(ser(x, depth + 1) for x in o)
    if isinstance(o, dict):
        return tuple(sorted((k, ser(v, depth + 1)) for k, v in o.items()))
    if hasattr(o, '__dict__'):
        return (type(o).__name__,) + tuple(sorted((k, ser(v, depth + 1)) for k, v in vars(o).items()
                                                 if not k.startswith('_')))
    return repr(o)


def unwrap(L):
    for st in L.SubTable:
        yield st.ExtSubTable if L.LookupType in (7, 9) and hasattr(st, 'ExtSubTable') else st


def cov(c):
    return c.glyphs if c is not None else []


def layout_facts(f, cand):
    """{glyph: [facts]} for glyphs in cand, input side of every GSUB/GPOS lookup."""
    F = collections.defaultdict(list)

    def add(g, *fact):
        if g in cand:
            F[g].append(fact)

    def ctx_rules(tag, li, si, st):
        fmt = st.Format
        chain = hasattr(st, 'BacktrackCoverage') or hasattr(st, 'BacktrackClassDef') or \
            any(hasattr(st, a) for a in ('ChainSubRuleSet', 'ChainPosRuleSet', 'ChainSubClassSet', 'ChainPosClassSet'))
        if fmt == 1:
            sets = next(getattr(st, a) for a in ('SubRuleSet', 'PosRuleSet', 'ChainSubRuleSet', 'ChainPosRuleSet')
                        if hasattr(st, a))
            for first, rs in zip(cov(st.Coverage), sets):
                if rs is None:
                    continue
                rules = next(getattr(rs, a) for a in ('SubRule', 'PosRule', 'ChainSubRule', 'ChainPosRule') if hasattr(rs, a))
                srl = []
                for ri, r in enumerate(rules):
                    seqs = {k: [G(x) for x in getattr(r, k, [])] for k in ('Backtrack', 'Input', 'LookAhead')}
                    recs = tuple((x.SequenceIndex, x.LookupListIndex) for x in
                                 (getattr(r, 'SubstLookupRecord', None) or getattr(r, 'PosLookupRecord', None) or []))
                    srl.append((tuple(tuple(v) for v in seqs.values()), recs))
                    for k in ('Backtrack', 'Input', 'LookAhead'):
                        for p, x in enumerate(getattr(r, k, [])):
                            add(x, tag, li, si, 'c1r', G(first), ri, k, p)
                add(first, tag, li, si, 'c1f', tuple(srl))
        elif fmt == 2:
            for g in cov(st.Coverage):
                add(g, tag, li, si, 'c2cov')
            for k in ('ClassDef', 'BacktrackClassDef', 'InputClassDef', 'LookAheadClassDef'):
                cd = getattr(st, k, None)
                if cd is not None:
                    for g, c in cd.classDefs.items():
                        if c:
                            add(g, tag, li, si, 'c2cls', k, c)
        elif fmt == 3:
            for k in ('Coverage', 'BacktrackCoverage', 'InputCoverage', 'LookAheadCoverage'):
                for ci, c in enumerate(getattr(st, k, None) or []):
                    for g in cov(c):
                        add(g, tag, li, si, 'c3', k, ci)

    for tag in ('GSUB', 'GPOS'):
        if tag not in f:
            continue
        t = f[tag].table
        for li, L in enumerate(t.LookupList.Lookup):
            typ = L.LookupType
            for si, st in enumerate(unwrap(L)):
                ty = st.LookupType if hasattr(st, 'LookupType') else typ
                if tag == 'GSUB':
                    if ty == 1:
                        for a, b in st.mapping.items():
                            add(a, tag, li, si, 's1', G(b))
                    elif ty == 2:
                        for a, b in st.mapping.items():
                            add(a, tag, li, si, 's2', tuple(G(x) for x in b))
                    elif ty == 3:
                        for a, b in st.alternates.items():
                            add(a, tag, li, si, 's3', tuple(G(x) for x in b))
                    elif ty == 4:
                        for first, ligs in st.ligatures.items():
                            desc = tuple(sorted((tuple(G(c) for c in lg.Component), G(lg.LigGlyph)) for lg in ligs))
                            add(first, tag, li, si, 's4f', desc)
                            for lg in ligs:
                                comps = tuple(G(c) for c in lg.Component)
                                for p, c in enumerate(lg.Component):
                                    add(c, tag, li, si, 's4c', G(first), comps, p, G(lg.LigGlyph))
                    elif ty in (5, 6):
                        ctx_rules(tag, li, si, st)
                    elif ty == 8:
                        for k in ('BacktrackCoverage', 'LookAheadCoverage'):
                            for ci, c in enumerate(getattr(st, k, None) or []):
                                for g in cov(c):
                                    add(g, tag, li, si, 'r8ctx', k, ci)
                        for g, s in zip(cov(st.Coverage), st.Substitute):
                            add(g, tag, li, si, 'r8', G(s))
                else:
                    if ty == 1:
                        if st.Format == 1:
                            for g in cov(st.Coverage):
                                add(g, tag, li, si, 'p1', ser(st.Value))
                        else:
                            for g, v in zip(cov(st.Coverage), st.Value):
                                add(g, tag, li, si, 'p1', ser(v))
                    elif ty == 2:
                        if st.Format == 1:
                            for first, ps in zip(cov(st.Coverage), st.PairSet):
                                recs = tuple(sorted((G(r.SecondGlyph), ser(getattr(r, 'Value1', None)), ser(getattr(r, 'Value2', None)))
                                                    for r in ps.PairValueRecord))
                                add(first, tag, li, si, 'p2f', recs)
                                for r in ps.PairValueRecord:
                                    add(r.SecondGlyph, tag, li, si, 'p2s', G(first), ser(getattr(r, 'Value1', None)),
                                        ser(getattr(r, 'Value2', None)))
                        else:
                            for g in cov(st.Coverage):
                                add(g, tag, li, si, 'p2cov')
                            for k in ('ClassDef1', 'ClassDef2'):
                                for g, c in getattr(st, k).classDefs.items():
                                    if c:
                                        add(g, tag, li, si, 'p2cls', k, c)
                    elif ty == 3:
                        for g, r in zip(cov(st.Coverage), st.EntryExitRecord):
                            add(g, tag, li, si, 'p3', ser(r))
                    elif ty in (4, 5, 6):
                        if ty == 6:
                            mc, bc, ma, ba, bk, an = st.Mark1Coverage, st.Mark2Coverage, st.Mark1Array, st.Mark2Array, 'Mark2Record', 'Mark2Anchor'
                        elif ty == 4:
                            mc, bc, ma, ba, bk, an = st.MarkCoverage, st.BaseCoverage, st.MarkArray, st.BaseArray, 'BaseRecord', 'BaseAnchor'
                        else:
                            mc, bc, ma, ba, bk, an = st.MarkCoverage, st.LigatureCoverage, st.MarkArray, st.LigatureArray, 'LigatureAttach', None
                        for g, r in zip(cov(mc), ma.MarkRecord):
                            add(g, tag, li, si, 'pm', r.Class, ser(r.MarkAnchor))
                        for g, r in zip(cov(bc), getattr(ba, bk)):
                            add(g, tag, li, si, 'pb', ser(r))
                    elif ty in (7, 8):
                        ctx_rules(tag, li, si, st)
    return F


def norm_facts(facts, a, b):
    def sub(x):
        if isinstance(x, G):
            return G('@') if x[1] in (a, b) else x
        if isinstance(x, tuple):
            return tuple(sub(y) for y in x)
        return x
    return sorted(repr(sub(x)) for x in facts)


# ------------------------------------------------------------------ duplicates
def glyph_key(f, g, hvar_row):
    glyf, gvar = f['glyf'], f['gvar']
    G_ = glyf[g]
    if G_.numberOfContours == 0:
        return None
    if G_.isComposite():
        out = ('C', tuple((c.glyphName, c.x, c.y, c.flags & ~0x0020 & ~0x0100 & ~0x0400,
                           getattr(c, 'transform', None) and tuple(map(tuple, c.transform))) for c in G_.components))
    else:
        out = ('S', tuple(G_.coordinates), tuple(G_.endPtsOfContours), tuple(x & 1 for x in G_.flags))
    prog = G_.program.getBytecode() if hasattr(G_, 'program') else b''
    var = tuple((tuple(sorted(v.axes.items())), tuple(v.coordinates)) for v in gvar.variations.get(g, []))
    vorg = f['VORG'].VOriginRecords.get(g, f['VORG'].defaultVertOriginY) if 'VORG' in f else None
    return (out, prog, var, f['hmtx'][g], f['vmtx'][g] if 'vmtx' in f else None, vorg, hvar_row(g))


def gdef_key(f, g):
    if 'GDEF' not in f:
        return None
    t = f['GDEF'].table
    gc = t.GlyphClassDef.classDefs.get(g, 0) if t.GlyphClassDef else 0
    mac = t.MarkAttachClassDef.classDefs.get(g, 0) if t.MarkAttachClassDef else 0
    ms = tuple(i for i, c in enumerate(t.MarkGlyphSetsDef.Coverage) if g in c.glyphs) if getattr(t, 'MarkGlyphSetsDef', None) else ()
    ap = None
    if t.AttachList and g in t.AttachList.Coverage.glyphs:
        ap = ser(t.AttachList.AttachPoint[t.AttachList.Coverage.glyphs.index(g)])
    lc = None
    if t.LigCaretList and g in t.LigCaretList.Coverage.glyphs:
        lc = ser(t.LigCaretList.LigGlyph[t.LigCaretList.Coverage.glyphs.index(g)])
    return (gc, mac, ms, ap, lc)


def dedupe(f, report):
    hv = f['HVAR'].table
    amap = hv.AdvWidthMap.mapping

    def hvar_row(g):
        idx = amap.get(g)
        if idx is None:
            return None
        return tuple(hv.VarStore.VarData[idx >> 16].Item[idx & 0xFFFF]) if (idx >> 16) < len(hv.VarStore.VarData) else idx
    cm = dict(f.getBestCmap())
    gid = {g: i for i, g in enumerate(f.getGlyphOrder())}
    mapped = sorted(set(cm.values()), key=gid.get)
    groups = collections.defaultdict(list)
    for g in mapped:
        if g == '.notdef':
            continue
        k = glyph_key(f, g, hvar_row)
        if k is not None:
            groups[(k, gdef_key(f, g))].append(g)
    groups = [v for v in groups.values() if len(v) > 1]
    cand = set(g for v in groups for g in v)
    log('dedupe: %d identical groups (%d redundant slots) by outline/gvar/metrics/GDEF' %
        (len(groups), sum(len(v) - 1 for v in groups)))
    facts = layout_facts(f, cand)
    rename, skipped = {}, []
    for v in groups:
        keep = v[0]
        for a in v[1:]:
            if norm_facts(facts.get(a, []), a, keep) == norm_facts(facts.get(keep, []), a, keep):
                rename[a] = keep
            else:
                skipped.append((a, keep))
    log('dedupe: merge %d, skipped %d pairs (layout not interchangeable)' % (len(rename), len(skipped)))
    # repoint cmap
    for t in unicode_subtables(f):
        for c, g in list(t.cmap.items()):
            if g in rename:
                t.cmap[c] = rename[g]
    # composites
    glyf = f['glyf']
    ncomp = 0
    for g in f.getGlyphOrder():
        G_ = glyf[g]
        if G_.isComposite():
            for c in G_.components:
                if c.glyphName in rename:
                    c.glyphName = rename[c.glyphName]
                    ncomp += 1
    # GSUB outputs
    nout = 0
    if 'GSUB' in f:
        for L in f['GSUB'].table.LookupList.Lookup:
            for st in unwrap(L):
                ty = st.LookupType if hasattr(st, 'LookupType') else L.LookupType
                if ty == 1:
                    for k, x in st.mapping.items():
                        if x in rename:
                            st.mapping[k] = rename[x]; nout += 1
                elif ty in (2, 3):
                    m = st.mapping if ty == 2 else st.alternates
                    for k, xs in m.items():
                        if any(x in rename for x in xs):
                            m[k] = [rename.get(x, x) for x in xs]; nout += 1
                elif ty == 4:
                    for ligs in st.ligatures.values():
                        for lg in ligs:
                            if lg.LigGlyph in rename:
                                lg.LigGlyph = rename[lg.LigGlyph]; nout += 1
                elif ty == 8:
                    if any(x in rename for x in st.Substitute):
                        st.Substitute = [rename.get(x, x) for x in st.Substitute]; nout += 1
    log('dedupe: repointed %d composite refs, %d GSUB outputs' % (ncomp, nout))
    rc = collections.defaultdict(list)
    for c, g in cm.items():
        rc[g].append(c)
    report['dedupe'] = dict(
        groups=len(groups), candidate_slots=sum(len(v) - 1 for v in groups), merged=len(rename),
        skipped=len(skipped), composite_refs=ncomp, gsub_outputs=nout,
        merged_pairs=[['U+%04X' % rc[a][0], a, 'U+%04X' % rc[b][0], b] for a, b in rename.items()],
        skipped_pairs=[['U+%04X' % rc[a][0], a, 'U+%04X' % rc[b][0], b] for a, b in skipped])
    return rename


# ------------------------------------------------------------------ P0 glyphs
def build_currency_vf(work):
    """mini VF (target normalised design space, UPM 1000) holding uni20C0 + uni20C1."""
    from fontTools.varLib import instancer, build as varlib_build
    from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
    from fontTools.ttLib.scaleUpem import scale_upem
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from common import SF_TTF, sf_loc, target_norm
    import vf_from_masters as V
    out = os.path.join(work, 'p0_currency_vf.ttf')
    src = TTFont(SF_TTF)
    for t in V.DROP:
        if t in src:
            del src[t]
    V.subset_font(src, [0x20C1, 0x0421, 0x005F], [])
    scale_upem(src, 1000)
    W = [100, 200, 300, 400, 500, 600, 700, 800, 900]
    masters = [{'wght': w, 'wdth': 100} for w in W]
    masters = [masters[4]] + masters[:4] + masters[5:]
    for d in (80, 120):
        for w in (100, 500, 900):
            masters.append({'wght': w, 'wdth': d})
    tmp = os.path.join(work, 'masters_p0'); os.makedirs(tmp, exist_ok=True)
    ds = DesignSpaceDocument()
    for t in ('wght', 'wdth'):
        a = AxisDescriptor(); a.tag = t; a.name = t
        a.minimum, a.default, a.maximum = -1000, 0, 1000
        ds.addAxis(a)
    for i, tl in enumerate(masters):
        sl = {k: v for k, v in sf_loc(tl).items() if k in {a.axisTag for a in src['fvar'].axes}}
        inst = instancer.instantiateVariableFont(src, sl, inplace=False, updateFontNames=False)
        cm = inst.getBestCmap()
        gs = inst.getGlyphSet()
        es, us, ri = cm[0x0421], cm[0x005F], cm[0x20C1]
        glyf, hmtx = inst['glyf'], inst['hmtx']
        # flatten Es (composite in SF Pro) and draw Som = Es + underline bar
        rec = DecomposingRecordingPen(gs); gs[es].draw(rec)
        ub = glyf[us]; ub.recalcBounds(glyf)
        eg = TTGlyphPen(gs); rec.replay(eg); E = eg.glyph(); E.recalcBounds(None)
        pen = TTGlyphPen(gs); rec.replay(pen)
        x0, x1 = E.xMin, E.xMax
        y0, y1 = ub.yMin, ub.yMax
        pen.moveTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.lineTo((x0, y0)); pen.closePath()
        som = pen.glyph(); som.recalcBounds(None)
        rp = DecomposingRecordingPen(gs); gs[ri].draw(rp)
        rpen = TTGlyphPen(gs); rp.replay(rpen); riy = rpen.glyph(); riy.recalcBounds(None)
        order = ['.notdef', 'uni20C0', 'uni20C1']
        nd = glyf['.notdef']
        newg = {'.notdef': nd, 'uni20C0': som, 'uni20C1': riy}
        mets = {'.notdef': hmtx['.notdef'], 'uni20C0': (hmtx[es][0], som.xMin), 'uni20C1': (hmtx[ri][0], riy.xMin)}
        for tag in ('GSUB', 'GPOS', 'GDEF', 'post', 'cmap'):
            pass
        m = TTFont()
        from fontTools.fontBuilder import FontBuilder
        fb = FontBuilder(1000, isTTF=True)
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap({0x20C0: 'uni20C0', 0x20C1: 'uni20C1'})
        fb.setupGlyf(newg)
        fb.setupHorizontalMetrics(mets)
        fb.setupHorizontalHeader(ascent=1000, descent=-250)
        fb.setupNameTable({'familyName': 'P0', 'styleName': 'Regular'})
        fb.setupOS2(); fb.setupPost(); fb.setupMaxp()
        p = os.path.join(tmp, 'm%d.ttf' % i)
        fb.font.save(p)
        n = target_norm(tl)
        s = SourceDescriptor(); s.path = p; s.name = 'm%d' % i
        s.location = {'wght': n['wght'] * 1000, 'wdth': n['wdth'] * 1000}
        ds.addSource(s)
    vf, _, _ = varlib_build(ds, exclude=['STAT', 'MVAR', 'name'], optimize=True)
    vf.save(out)
    return TTFont(out)


def add_glyph(f, name, glyph, adv_lsb, vmtx, gvar_list):
    go = list(f.getGlyphOrder())
    assert name not in go, name
    go.append(name)
    f['glyf'].glyphs[name] = glyph
    f['glyf'].glyphOrder = go
    f.setGlyphOrder(go)
    f['hmtx'].metrics[name] = adv_lsb
    f['vmtx'].metrics[name] = vmtx
    f['gvar'].variations[name] = gvar_list
    if 'post' in f and hasattr(f['post'], 'extraNames'):
        pass


def add_p0(f, work, report):
    cm = dict(f.getBestCmap())
    added = {}
    # zero-width ignorable
    todo = [c for c in IGNORABLES if c not in cm]
    zw = Glyph(); zw.numberOfContours = 0
    add_glyph(f, 'ignorable.zw', zw, (0, 0), (0, 0), [])
    for c in todo:
        add_map(f, c, 'ignorable.zw')
    added['ignorable.zw'] = len(todo)
    log('P0: ignorable.zw mapped to %d default-ignorable code points' % len(todo))
    # currency
    P = build_currency_vf(work)
    vorg = f['VORG'].defaultVertOriginY if 'VORG' in f else f['hhea'].ascent
    gdef = f['GDEF'].table if 'GDEF' in f else None
    ref_cls = gdef.GlyphClassDef.classDefs.get(cm.get(0x20BF)) if gdef and gdef.GlyphClassDef else None
    for cp, name in ((0x20C0, 'uni20C0'), (0x20C1, 'uni20C1')):
        if cp in cm:
            log('P0: U+%04X already mapped, skipped' % cp)
            continue
        G_ = copy.deepcopy(P['glyf'][name])
        G_.recalcBounds(P['glyf'])
        add_glyph(f, name, G_, P['hmtx'][name], (1000, vorg - G_.yMax),
                  copy.deepcopy(P['gvar'].variations.get(name, [])))
        add_map(f, cp, name)
        if ref_cls:
            gdef.GlyphClassDef.classDefs[name] = ref_cls
        added[name] = 'U+%04X adv %d, %d gvar tuples' % (cp, P['hmtx'][name][0], len(P['gvar'].variations.get(name, [])))
        log('P0:', name, added[name])
    report['p0'] = dict(added=added, ignorables_mapped=['U+%04X' % c for c in todo])


# ------------------------------------------------------------------ main
def prune(f):
    o = subset.Options()
    o.layout_features = ['*']; o.layout_scripts = ['*']; o.layout_closure = True
    o.glyph_names = True; o.notdef_glyph = True; o.notdef_outline = True
    o.name_IDs = ['*']; o.name_languages = ['*']; o.name_legacy = True
    o.legacy_cmap = True; o.symbol_cmap = True; o.hinting = True
    o.drop_tables = ['DSIG']; o.passthrough_tables = True
    o.prune_unicode_ranges = False; o.prune_codepage_ranges = False
    o.recalc_bounds = False; o.recalc_timestamp = False; o.retain_gids = False
    o.recalc_average_width = False; o.recalc_max_context = False; o.canonical_order = False
    o.harfbuzz_repacker = True
    s = subset.Subsetter(o)
    s.populate(unicodes=list(f.getBestCmap()))
    s.subset(f)


def main(inp, out, rep=None):
    report = {}
    f = TTFont(inp, recalcBBoxes=False, recalcTimestamp=False)
    work = os.environ.get('PFSF_WORK', os.path.join(HERE, '..', 'build_work'))
    n0 = len(f.getGlyphOrder())
    cm0 = dict(f.getBestCmap())
    reach0 = closure(f, cm0)
    report['glyphs_in'] = n0
    report['orphans_in'] = n0 - len(reach0)
    log('input: %d glyphs, %d cps, %d unreachable (orphans)' % (n0, len(cm0), n0 - len(reach0)))
    # 1. SF Symbols
    sfs = [c for c in cm0 if SF_SYMBOLS[0] <= c <= SF_SYMBOLS[1]]
    unmap(f, sfs)
    reach1 = closure(f, f.getBestCmap())
    report['sf_symbols'] = dict(cps_unmapped=len(sfs), glyphs_freed=len(reach0) - len(reach1))
    log('SF Symbols: %d cps unmapped, %d glyphs freed' % (len(sfs), len(reach0) - len(reach1)))
    # 2. emoji presentation
    em = [int(l.split()[0][2:], 16) for l in open(EMOJI_LIST, encoding='utf-8') if l.startswith('U+')]
    em_present = [c for c in em if c in cm0]
    unmap(f, em_present)
    reach2 = closure(f, f.getBestCmap())
    report['emoji'] = dict(cps_unmapped=len(em_present), glyphs_freed=len(reach1) - len(reach2),
                           glyphs_kept_still_referenced=len(set(cm0[c] for c in em_present) & reach2))
    log('Emoji_Presentation: %d cps unmapped, %d glyphs freed, %d kept (still referenced)'
        % (len(em_present), len(reach1) - len(reach2), report['emoji']['glyphs_kept_still_referenced']))
    # 3. duplicates
    dedupe(f, report)
    reach3 = closure(f, f.getBestCmap())
    report['dedupe']['glyphs_freed'] = len(reach2) - len(reach3)
    log('dedupe: %d glyphs freed' % (len(reach2) - len(reach3)))
    # 4. P0
    add_p0(f, work, report)
    # 5. HVAR
    from fontTools.varLib.hvar import add_HVAR
    del f['HVAR']
    add_HVAR(f)
    log('HVAR rebuilt')
    # 6. prune
    prune(f)
    n1 = len(f.getGlyphOrder())
    f['OS/2'].recalcUnicodeRanges(f)
    recalc_metrics(f)
    report['glyphs_out'] = n1
    report['free_slots'] = 65535 - n1
    report['cps_out'] = len(f.getBestCmap())
    f.save(out, reorderTables=True)
    log('glyphs %d -> %d (%d free of 65,535); cps %d -> %d' % (n0, n1, 65535 - n1, len(cm0), report['cps_out']))
    if rep:
        json.dump(report, open(rep, 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main(*sys.argv[1:])
