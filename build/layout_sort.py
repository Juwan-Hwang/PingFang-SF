"""Re-sort Coverage tables (and the arrays that run parallel to them) by target glyph ID.

Layout tables translated from another font keep the *source* glyph order inside every
Coverage. fontTools would emit such coverages as out-of-order ranges (rejected by OTS and
browser sanitizers), so every coverage is re-sorted here, together with its parallel
records, and duplicate glyphs are dropped (first occurrence wins).
"""
from fontTools.ttLib.tables import otTables as ot


def _perm(glyphs, gid):
    seen, idx = set(), []
    for i, g in sorted(enumerate(glyphs), key=lambda x: (gid(x[1]), x[0])):
        if g in seen:
            continue
        seen.add(g)
        idx.append(i)
    return idx


def _sort_cov(cov, gid, *parallel):
    """sort coverage; return list of permuted parallel lists"""
    idx = _perm(cov.glyphs, gid)
    cov.glyphs = [cov.glyphs[i] for i in idx]
    return [[p[i] for i in idx] for p in parallel]


def _sort_plain(cov, gid):
    if cov is not None:
        _sort_cov(cov, gid)


def fix_subtable(st, gid):
    name = type(st).__name__
    fmt = getattr(st, 'Format', None)
    if name in ('SingleSubst', 'MultipleSubst', 'AlternateSubst', 'LigatureSubst'):
        return
    if name == 'SinglePos':
        if fmt == 1:
            _sort_plain(st.Coverage, gid)
        else:
            (st.Value,) = _sort_cov(st.Coverage, gid, st.Value)
            st.ValueCount = len(st.Value)
    elif name == 'PairPos':
        if fmt == 1:
            (st.PairSet,) = _sort_cov(st.Coverage, gid, st.PairSet)
            st.PairSetCount = len(st.PairSet)
            for ps in st.PairSet:
                seen, recs = set(), []
                for r in sorted(ps.PairValueRecord, key=lambda r: gid(r.SecondGlyph)):
                    if r.SecondGlyph in seen:
                        continue
                    seen.add(r.SecondGlyph); recs.append(r)
                ps.PairValueRecord = recs
                ps.PairValueCount = len(recs)
        else:
            _sort_plain(st.Coverage, gid)
    elif name == 'CursivePos':
        (st.EntryExitRecord,) = _sort_cov(st.Coverage, gid, st.EntryExitRecord)
        st.EntryExitCount = len(st.EntryExitRecord)
    elif name == 'MarkBasePos':
        (st.MarkArray.MarkRecord,) = _sort_cov(st.MarkCoverage, gid, st.MarkArray.MarkRecord)
        st.MarkArray.MarkCount = len(st.MarkArray.MarkRecord)
        (st.BaseArray.BaseRecord,) = _sort_cov(st.BaseCoverage, gid, st.BaseArray.BaseRecord)
        st.BaseArray.BaseCount = len(st.BaseArray.BaseRecord)
    elif name == 'MarkLigPos':
        (st.MarkArray.MarkRecord,) = _sort_cov(st.MarkCoverage, gid, st.MarkArray.MarkRecord)
        st.MarkArray.MarkCount = len(st.MarkArray.MarkRecord)
        (st.LigatureArray.LigatureAttach,) = _sort_cov(st.LigatureCoverage, gid, st.LigatureArray.LigatureAttach)
        st.LigatureArray.LigatureCount = len(st.LigatureArray.LigatureAttach)
    elif name == 'MarkMarkPos':
        (st.Mark1Array.MarkRecord,) = _sort_cov(st.Mark1Coverage, gid, st.Mark1Array.MarkRecord)
        st.Mark1Array.MarkCount = len(st.Mark1Array.MarkRecord)
        (st.Mark2Array.Mark2Record,) = _sort_cov(st.Mark2Coverage, gid, st.Mark2Array.Mark2Record)
        st.Mark2Array.Mark2Count = len(st.Mark2Array.Mark2Record)
    elif name in ('ContextSubst', 'ContextPos'):
        sub = 'Sub' if name == 'ContextSubst' else 'Pos'
        if fmt == 1:
            attr = sub + 'RuleSet'
            (rs,) = _sort_cov(st.Coverage, gid, getattr(st, attr))
            setattr(st, attr, rs); setattr(st, attr + 'Count', len(rs))
        elif fmt == 2:
            _sort_plain(st.Coverage, gid)
        else:
            for c in st.Coverage:
                _sort_plain(c, gid)
    elif name in ('ChainContextSubst', 'ChainContextPos'):
        sub = 'ChainSub' if name == 'ChainContextSubst' else 'ChainPos'
        if fmt == 1:
            attr = sub + 'RuleSet'
            (rs,) = _sort_cov(st.Coverage, gid, getattr(st, attr))
            setattr(st, attr, rs); setattr(st, attr + 'Count', len(rs))
        elif fmt == 2:
            _sort_plain(st.Coverage, gid)
        else:
            for c in st.BacktrackCoverage + st.InputCoverage + st.LookAheadCoverage:
                _sort_plain(c, gid)
    elif name == 'ReverseChainSingleSubst':
        (st.Substitute,) = _sort_cov(st.Coverage, gid, st.Substitute)
        st.GlyphCount = len(st.Substitute)
        for c in st.BacktrackCoverage + st.LookAheadCoverage:
            _sort_plain(c, gid)
    else:
        raise NotImplementedError(name)


def sort_lookups(lookups, font):
    order = {g: i for i, g in enumerate(font.getGlyphOrder())}
    gid = order.__getitem__
    for lk in lookups:
        for st in lk.SubTable:
            if type(st).__name__ in ('ExtensionSubst', 'ExtensionPos'):
                st = st.ExtSubTable
            fix_subtable(st, gid)
