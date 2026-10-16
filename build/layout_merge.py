"""Merge OpenType layout (GSUB/GPOS/GDEF) from several prepared source fonts into one.

Every source is first *translated* into the target's glyph names: its compiled table bytes
are decompiled again against a fake font whose glyph order holds the target name of each
source glyph.  Then lookups, features, scripts/langsys, GDEF classes, mark-glyph-sets and
the GDEF ItemVariationStore are concatenated with all indices remapped.  Nothing of the
existing target layout is thrown away: the target's own tables are the first source.
"""
import copy
from collections import OrderedDict, defaultdict
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot


def translate_tables(src_font, name_map, tags=('GSUB', 'GPOS', 'GDEF')):
    """Return {tag: otTables table} decompiled with glyph names from name_map."""
    fake = TTFont()
    fake.setGlyphOrder([name_map[g] for g in src_font.getGlyphOrder()])
    out = {}
    for tag in tags:
        if tag not in src_font:
            continue
        data = src_font.getTableData(tag)   # compiled from memory if the table was modified
        t = newTable(tag)
        t.decompile(data, fake)
        t.table.ensureDecompiled(recurse=True)
        out[tag] = t.table
    return out


def _walk(obj, fn, seen=None):
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return
    seen.add(id(obj))
    fn(obj)
    if isinstance(obj, (list, tuple)):
        for x in obj:
            _walk(x, fn, seen)
    elif hasattr(obj, '__dict__'):
        for k, v in list(vars(obj).items()):
            if isinstance(v, (str, int, float, bytes, dict)) or v is None:
                continue
            _walk(v, fn, seen)


def _shift_lookup_records(lookup, off):
    def fn(o):
        if isinstance(o, (ot.SubstLookupRecord, ot.PosLookupRecord)):
            o.LookupListIndex += off
    _walk(lookup.SubTable, fn)


def _shift_devices(obj, outer_off):
    def fn(o):
        if isinstance(o, ot.Device) and getattr(o, 'DeltaFormat', 0) == 0x8000:
            o.StartSize += outer_off
    _walk(obj, fn)


class LayoutMerger:
    def __init__(self, axis_count):
        self.axis_count = axis_count
        self.lookups = {'GSUB': [], 'GPOS': []}
        # scripts[tag][script][source_id] = {'dflt': {feat: [lk]}, 'langs': {lang: {feat: [lk]}}}
        self.scripts = {'GSUB': OrderedDict(), 'GPOS': OrderedDict()}
        self.fv = []          # (source_id, src_feature_lookups, alt_lookups, conditions)
        self.glyph_class = {}
        self.mark_attach = {}
        self.mark_attach_base = 0
        self.mark_sets = []
        self.regions = []      # list of tuples
        self.region_index = {}
        self.vardata = []
        self.nsrc = 0

    # ---- GDEF -------------------------------------------------------------
    def _merge_gdef(self, gdef, override_classes):
        mac_map, mfs_off = {}, len(self.mark_sets)
        if gdef is None:
            return mac_map, mfs_off, 0
        if gdef.GlyphClassDef:
            for g, c in gdef.GlyphClassDef.classDefs.items():
                if override_classes or g not in self.glyph_class:
                    self.glyph_class[g] = c
        if gdef.MarkAttachClassDef:
            classes = sorted(set(gdef.MarkAttachClassDef.classDefs.values()))
            for c in classes:
                self.mark_attach_base += 1
                mac_map[c] = self.mark_attach_base
            for g, c in gdef.MarkAttachClassDef.classDefs.items():
                self.mark_attach[g] = mac_map[c]
        if getattr(gdef, 'MarkGlyphSetsDef', None):
            for cov in gdef.MarkGlyphSetsDef.Coverage:
                self.mark_sets.append(list(cov.glyphs))
        outer_off = len(self.vardata)
        vs = getattr(gdef, 'VarStore', None)
        if vs is not None:
            rl = vs.VarRegionList
            assert rl.RegionAxisCount == self.axis_count, 'VarStore axis count mismatch'
            rmap = []
            for r in rl.Region:
                key = tuple((a.StartCoord, a.PeakCoord, a.EndCoord) for a in r.VarRegionAxis)
                if key not in self.region_index:
                    self.region_index[key] = len(self.regions)
                    self.regions.append(key)
                rmap.append(self.region_index[key])
            for vd in vs.VarData:
                vd = copy.deepcopy(vd)
                vd.VarRegionIndex = [rmap[i] for i in vd.VarRegionIndex]
                self.vardata.append(vd)
        return mac_map, mfs_off, outer_off

    # ---- GSUB / GPOS ------------------------------------------------------
    def add_source(self, tables, scripts_filter=None, override_classes=False, fv_conditions_fn=None,
                   scripts_exclude=()):
        sid = self.nsrc
        self.nsrc += 1
        mac_map, mfs_off, outer_off = self._merge_gdef(tables.get('GDEF'), override_classes)
        for tag in ('GSUB', 'GPOS'):
            t = tables.get(tag)
            if t is None or t.LookupList is None:
                continue
            off = len(self.lookups[tag])
            for lk in t.LookupList.Lookup:
                lk = copy.deepcopy(lk)
                _shift_lookup_records(lk, off)
                flag = lk.LookupFlag
                mac = (flag >> 8) & 0xFF
                if mac:
                    flag = (flag & 0x00FF) | (mac_map[mac] << 8)
                if flag & 0x0010:
                    lk.MarkFilteringSet += mfs_off
                lk.LookupFlag = flag
                if tag == 'GPOS' and outer_off:
                    _shift_devices(lk, outer_off)
                self.lookups[tag].append(lk)
            feats = [(fr.FeatureTag, [i + off for i in fr.Feature.LookupListIndex])
                     for fr in t.FeatureList.FeatureRecord]

            def langsys_feats(ls):
                d = OrderedDict()
                idx = list(ls.FeatureIndex)
                if ls.ReqFeatureIndex != 0xFFFF:
                    idx.append(ls.ReqFeatureIndex)
                for fi in idx:
                    ftag, lks = feats[fi]
                    d.setdefault(ftag, [])
                    d[ftag] += [x for x in lks if x not in d[ftag]]
                    d.setdefault('__fi__' + ftag, []).append(fi)
                return d

            for sr in t.ScriptList.ScriptRecord:
                if scripts_filter and sr.ScriptTag not in scripts_filter:
                    continue
                if sr.ScriptTag in scripts_exclude:
                    continue
                ent = {'dflt': langsys_feats(sr.Script.DefaultLangSys) if sr.Script.DefaultLangSys else OrderedDict(),
                       'langs': OrderedDict((l.LangSysTag, langsys_feats(l.LangSys)) for l in sr.Script.LangSysRecord)}
                self.scripts[tag].setdefault(sr.ScriptTag, OrderedDict())[sid] = ent
            fvs = getattr(t, 'FeatureVariations', None) if tag == 'GSUB' else None
            if fvs is not None and fv_conditions_fn is not None:
                for rec in fvs.FeatureVariationRecord:
                    conds = fv_conditions_fn(rec.ConditionSet)
                    if conds is None:
                        continue
                    subs = []
                    for st in rec.FeatureTableSubstitution.SubstitutionRecord:
                        ftag, lks = feats[st.FeatureIndex]
                        subs.append((sid, st.FeatureIndex, ftag, lks, [i + off for i in st.Feature.LookupListIndex]))
                    if subs:
                        self.fv.append((conds, subs))
        return sid

    def _build_table(self, tag):
        T = ot.GSUB() if tag == 'GSUB' else ot.GPOS()
        T.Version = 0x00010000
        T.LookupList = ot.LookupList()
        T.LookupList.Lookup = self.lookups[tag]
        T.FeatureList = ot.FeatureList()
        T.FeatureList.FeatureRecord = []
        T.ScriptList = ot.ScriptList()
        T.ScriptList.ScriptRecord = []
        feat_index = {}
        provenance = defaultdict(list)    # feature index -> [(sid, src_fi)]

        def feature(ftag, lks, prov):
            key = (ftag, tuple(sorted(lks)), tuple(prov))
            if key not in feat_index:
                fr = ot.FeatureRecord()
                fr.FeatureTag = ftag
                fr.Feature = ot.Feature()
                fr.Feature.FeatureParams = None
                fr.Feature.LookupListIndex = sorted(lks)
                fr.Feature.LookupCount = len(lks)
                feat_index[key] = len(T.FeatureList.FeatureRecord)
                T.FeatureList.FeatureRecord.append(fr)
                provenance[feat_index[key]] = list(prov)
            return feat_index[key]

        def make_langsys(per_source):
            # per_source: list of (sid, featdict)
            merged = OrderedDict()
            prov = defaultdict(list)
            for sid, fd in per_source:
                for ftag, lks in fd.items():
                    if ftag.startswith('__fi__'):
                        prov[ftag[6:]] += [(sid, fi) for fi in lks]
                        continue
                    merged.setdefault(ftag, [])
                    merged[ftag] += [x for x in lks if x not in merged[ftag]]
            ls = ot.LangSys()
            ls.LookupOrder = None
            ls.ReqFeatureIndex = 0xFFFF
            ls.FeatureIndex = sorted(feature(ft, l, prov[ft]) for ft, l in merged.items() if l)
            ls.FeatureCount = len(ls.FeatureIndex)
            return ls

        for stag in sorted(self.scripts[tag]):
            srcs = self.scripts[tag][stag]
            langs = []
            for ent in srcs.values():
                for l in ent['langs']:
                    if l not in langs:
                        langs.append(l)
            sr = ot.ScriptRecord()
            sr.ScriptTag = stag
            sr.Script = ot.Script()
            sr.Script.DefaultLangSys = make_langsys([(sid, e['dflt']) for sid, e in srcs.items()])
            sr.Script.LangSysRecord = []
            for l in sorted(langs):
                lr = ot.LangSysRecord()
                lr.LangSysTag = l
                lr.LangSys = make_langsys([(sid, e['langs'].get(l, e['dflt'])) for sid, e in srcs.items()])
                sr.Script.LangSysRecord.append(lr)
            sr.Script.LangSysCount = len(sr.Script.LangSysRecord)
            T.ScriptList.ScriptRecord.append(sr)
        T.ScriptList.ScriptCount = len(T.ScriptList.ScriptRecord)
        # Feature records must be sorted by tag; re-sort and remap indices.
        order = sorted(range(len(T.FeatureList.FeatureRecord)),
                       key=lambda i: (T.FeatureList.FeatureRecord[i].FeatureTag, i))
        remap = {old: new for new, old in enumerate(order)}
        T.FeatureList.FeatureRecord = [T.FeatureList.FeatureRecord[i] for i in order]
        T.FeatureList.FeatureCount = len(order)
        provenance = {remap[k]: v for k, v in provenance.items()}
        for sr in T.ScriptList.ScriptRecord:
            for ls in [sr.Script.DefaultLangSys] + [l.LangSys for l in sr.Script.LangSysRecord]:
                ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex)
        if tag == 'GSUB' and self.fv:
            T.Version = 0x00010001
            fvs = ot.FeatureVariations()
            fvs.Version = 0x00010000
            fvs.FeatureVariationRecord = []
            for conds, subs in self.fv:
                rec = ot.FeatureVariationRecord()
                rec.ConditionSet = conds
                rec.FeatureTableSubstitution = ot.FeatureTableSubstitution()
                rec.FeatureTableSubstitution.Version = 0x00010000
                rec.FeatureTableSubstitution.SubstitutionRecord = []
                for fi, fr in enumerate(T.FeatureList.FeatureRecord):
                    prov = provenance.get(fi, [])
                    for sid, src_fi, ftag, src_lks, alt_lks in subs:
                        if (sid, src_fi) in prov and fr.FeatureTag == ftag:
                            new = [x for x in fr.Feature.LookupListIndex if x not in src_lks] + alt_lks
                            st = ot.FeatureTableSubstitutionRecord()
                            st.FeatureIndex = fi
                            st.Feature = ot.Feature()
                            st.Feature.FeatureParams = None
                            st.Feature.LookupListIndex = sorted(set(new))
                            st.Feature.LookupCount = len(st.Feature.LookupListIndex)
                            rec.FeatureTableSubstitution.SubstitutionRecord.append(st)
                            break
                rec.FeatureTableSubstitution.SubstitutionCount = len(rec.FeatureTableSubstitution.SubstitutionRecord)
                if rec.FeatureTableSubstitution.SubstitutionRecord:
                    fvs.FeatureVariationRecord.append(rec)
            fvs.FeatureVariationCount = len(fvs.FeatureVariationRecord)
            T.FeatureVariations = fvs
        else:
            T.FeatureVariations = None
        T.LookupList.LookupCount = len(T.LookupList.Lookup)
        return T

    def build(self, font):
        from layout_sort import sort_lookups
        order = {g: i for i, g in enumerate(font.getGlyphOrder())}
        for tag in ('GSUB', 'GPOS'):
            sort_lookups(self.lookups[tag], font)
            T = self._build_table(tag)
            if not T.LookupList.Lookup:
                if tag in font:
                    del font[tag]
                continue
            wrapper = newTable(tag)
            wrapper.table = T
            font[tag] = wrapper
        G = ot.GDEF()
        G.Version = 0x00010000
        G.GlyphClassDef = ot.GlyphClassDef()
        G.GlyphClassDef.classDefs = dict(self.glyph_class)
        G.AttachList = None
        G.LigCaretList = None
        G.MarkAttachClassDef = None
        if self.mark_attach:
            G.MarkAttachClassDef = ot.MarkAttachClassDef()
            G.MarkAttachClassDef.classDefs = dict(self.mark_attach)
        if self.mark_sets:
            G.Version = 0x00010002
            G.MarkGlyphSetsDef = ot.MarkGlyphSetsDef()
            G.MarkGlyphSetsDef.MarkSetTableFormat = 1
            G.MarkGlyphSetsDef.Coverage = []
            for gl in self.mark_sets:
                c = ot.Coverage()
                c.glyphs = sorted(set(gl), key=order.__getitem__)
                G.MarkGlyphSetsDef.Coverage.append(c)
            G.MarkGlyphSetsDef.MarkSetCount = len(self.mark_sets)
        else:
            G.MarkGlyphSetsDef = None
        if self.vardata:
            G.Version = 0x00010003
            if G.MarkGlyphSetsDef is None:
                G.MarkGlyphSetsDef = None
            vs = ot.VarStore()
            vs.Format = 1
            rl = ot.VarRegionList()
            rl.RegionAxisCount = self.axis_count
            rl.Region = []
            for key in self.regions:
                r = ot.VarRegion()
                r.VarRegionAxis = []
                for s, p, e in key:
                    a = ot.VarRegionAxis()
                    a.StartCoord, a.PeakCoord, a.EndCoord = s, p, e
                    r.VarRegionAxis.append(a)
                rl.Region.append(r)
            rl.RegionCount = len(rl.Region)
            vs.VarRegionList = rl
            vs.VarData = self.vardata
            vs.VarDataCount = len(self.vardata)
            G.VarStore = vs
        else:
            G.VarStore = None
        w = newTable('GDEF')
        w.table = G
        font['GDEF'] = w
