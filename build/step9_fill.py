"""Step 9 (v1.2.0 / font 1.200): fill the font to the TrueType limit of 65,535 glyphs.

usage: python step9_fill.py IN.ttf PARTS_DIR OUT.ttf [data/fill_sources.json]

Each part (built by fill_parts.py from data/fill_sources.json, which gen_fill_specs.py
derives from the frequency-ranked data/fillplan.json) is appended as new glyphs:
outlines, advances, gvar deltas (parts already live in the target's normalized wght/wdth
space), cmap entries for codepoints the font does not have yet, and, for shaped scripts,
the part's GSUB/GPOS/GDEF registered under that script's OpenType tags only. The target's
own layout is the first LayoutMerger source and is carried over unchanged (including its
FeatureVariations). Vertical metrics: advance 1000, tsb = VORG - yMax. HVAR is rebuilt from
gvar, global metrics recomputed (head.yMin/yMax stay pinned, see step 6).
"""
import json, os, sys
from fontTools.ttLib import TTFont
from step4_integrate import Target, integrate, log
from layout_merge import LayoutMerger, translate_tables
from step6_notdef_metrics import recalc_metrics

VERSION = '1.200'
FILL_COPYRIGHT = {
    0x409: (' v1.2.0 additions: Pretendard (c) 2023 Kil Hyung-jin; Plangothic (c) 2024 Fitzgerald P. Koeingsegg; '
            'Noto Sans KR (c) 2014-2021 Adobe; Noto fonts (c) 2022-2023 The Noto Project Authors; STIX Two Math '
            '(c) 2001-2021 The STIX Fonts Project Authors (all SIL OFL 1.1); SF India, SF Armenian, SF Georgian, '
            'SF Arabic, SF Mono, New York, Apple Symbols (c) Apple Inc.; Kefa (c) 2022 Black Foundry; '
            'Segoe UI Symbol (c) 2022 Microsoft Corporation.'),
    0x804: (' v1.2.0 补字：Pretendard © 2023 Kil Hyung-jin；Plangothic © 2024 Fitzgerald P. Köeingsegg；'
            'Noto Sans KR © 2014-2021 Adobe；Noto 系列 © 2022-2023 The Noto Project Authors；STIX Two Math '
            '© 2001-2021 The STIX Fonts Project Authors（以上 SIL OFL 1.1）；SF India、SF Armenian、SF Georgian、'
            'SF Arabic、SF Mono、New York、Apple Symbols © Apple Inc.；Kefa © 2022 Black Foundry；'
            'Segoe UI Symbol © 2022 Microsoft Corporation。'),
}
FILL_COPYRIGHT[0x404] = FILL_COPYRIGHT[0x804].replace('补字', '補字').replace('系列', '系列').replace('以上', '以上')
LIMIT = 65535


def dflt_as_script(tabs, scripts):
    """Parts whose source registers its features only under DFLT: expose them as `scripts`."""
    from fontTools.ttLib.tables import otTables as ot
    import copy
    for tag in ('GSUB', 'GPOS'):
        t = tabs.get(tag)
        if t is None or t.ScriptList is None:
            continue
        have = {sr.ScriptTag for sr in t.ScriptList.ScriptRecord}
        if have & set(scripts):
            continue
        d = [sr for sr in t.ScriptList.ScriptRecord if sr.ScriptTag in ('DFLT', 'latn')]
        if not d:
            continue
        for s in scripts:
            sr = ot.ScriptRecord(); sr.ScriptTag = s; sr.Script = copy.deepcopy(d[0].Script)
            t.ScriptList.ScriptRecord.append(sr)
        t.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
        t.ScriptList.ScriptCount = len(t.ScriptList.ScriptRecord)
        log('   %s: features of %s exposed as %s' % (tag, d[0].ScriptTag, scripts))


def main(inp, parts_dir, outp, spec_path=None):
    spec_path = spec_path or os.path.join(os.path.dirname(__file__), 'data', 'fill_sources.json')
    specs = json.load(open(spec_path))['plan']
    target = Target(inp)
    f = target.f
    f.recalcBBoxes = False      # head.yMin/yMax stay pinned; glyph bounds recomputed below
    for tag in f.keys():        # decompile everything now: the glyph order changes below
        if tag != 'GlyphOrder':
            f[tag]
    n0 = len(target.go)
    merger = LayoutMerger(axis_count=len(f['fvar'].axes))
    ident = {g: g for g in target.go}
    merger.add_source(translate_tables(f, ident), fv_conditions_fn=lambda c: c)
    report = {'glyphs_in': n0, 'parts': []}
    for s in specs:
        pid = s['id']
        P = TTFont(os.path.join(parts_dir, pid + '.ttf'))
        name_map, modes = {}, {}
        for g in P.getGlyphOrder():
            if g == '.notdef':
                name_map[g], modes[g] = '.notdef', 'keep'
                continue
            n = target.unique('%s.%s' % (pid, g))
            target.names.add(n)
            name_map[g], modes[g] = n, 'new'
        integrate(target, P, name_map, modes, pid)
        added = 0
        for cp, g in sorted(P.getBestCmap().items()):
            if cp not in target.cmap:
                target.add_cmap(cp, name_map[g])
                added += 1
        if s.get('scripts'):
            tabs = translate_tables(P, name_map)
            dflt_as_script(tabs, s['scripts'])
            merger.add_source(tabs, scripts_filter=s['scripts'], override_classes=False)
        report['parts'].append({'id': pid, 'glyphs': len(P.getGlyphOrder()) - 1, 'new_codepoints': added,
                                'scripts': s.get('scripts') or []})
        log('   %s: +%d glyphs, +%d codepoints, total %d' % (pid, len(P.getGlyphOrder()) - 1, added, len(target.go)))
    assert len(target.go) <= LIMIT, len(target.go)
    # The (3,1) format-4 cmap was already 64,982 of its 65,535 bytes: its BMP glyph IDs were
    # scattered, so almost every character needed its own glyphIdArray entry. Renumber the
    # glyphs (names, and therefore all tables, are unchanged): .notdef, then glyphs in order
    # of the first code point mapping to them, then unmapped glyphs in their old order. Runs
    # of consecutive code points then get consecutive glyph IDs and compress to idDelta
    # segments in format 4 and sequential groups in format 12.
    seen, order = {'.notdef'}, ['.notdef']
    for cp in sorted(target.cmap):
        g = target.cmap[cp]
        if g not in seen:
            seen.add(g); order.append(g)
    order += [g for g in target.go if g not in seen]
    assert len(order) == len(target.go) and set(order) == set(target.go)
    target.go = order
    f.setGlyphOrder(target.go)
    target.glyf.glyphOrder = target.go
    merger.build(f)
    log('layout merged: GSUB lookups', len(f['GSUB'].table.LookupList.Lookup),
        'GPOS lookups', len(f['GPOS'].table.LookupList.Lookup))
    for g in target.changed:
        target.glyf[g].recalcBounds(target.glyf)
    vorg = f['VORG'].defaultVertOriginY
    for g in target.changed:
        gl = target.glyf[g]
        target.vmtx.metrics[g] = (1000, (vorg - gl.yMax) if gl.numberOfContours != 0 else 0)
        adv = target.hmtx.metrics[g][0]
        target.hmtx.metrics[g] = (adv, getattr(gl, 'xMin', 0) if gl.numberOfContours != 0 else 0)
    from fontTools.varLib.hvar import add_HVAR
    del f['HVAR']
    add_HVAR(f)
    log('HVAR rebuilt')
    f['OS/2'].recalcUnicodeRanges(f)
    recalc_metrics(f)
    f['head'].fontRevision = float(VERSION)
    name = f['name']
    for n in list(name.names):
        if n.nameID in (3, 5):
            s = n.toUnicode()
            if n.nameID == 5:
                s = s.replace(', TH-Hak', ', TH-Hak, Pretendard, Plangothic, SF India, SF Armenian, SF Georgian, '
                              'SF Arabic, New York, SF Mono, Kefa, Apple Symbols, Segoe UI Symbol, STIX Two, Noto')
            n.string = s
    for n in list(name.names):
        if n.nameID == 0 and n.platformID == 3 and n.langID in FILL_COPYRIGHT and 'v1.2.0' not in n.toUnicode():
            n.string = n.toUnicode() + FILL_COPYRIGHT[n.langID]
    report['glyphs_out'] = len(target.go)
    report['codepoints_out'] = len(target.cmap)
    if 'DSIG' in f:  # empty stub must carry flag 1: signtool hashes with flag 1 but keeps the stub's flag -> Windows 0x80096010
        f['DSIG'].usFlag = 1
    f.save(outp)
    json.dump(report, open(outp + '.step9.json', 'w'), indent=1)
    log('saved', outp, os.path.getsize(outp), 'glyphs', len(target.go))


if __name__ == '__main__':
    main(*sys.argv[1:])
