#!/usr/bin/env python3
"""
merge_arabic_gsub.py — 把阿拉伯文字体的 OpenType 排版规则 *合并* 进目标字体

解决的问题：
  合并阿拉伯文字形后字母不连写（全部显示为孤立形）、元音符号（ḥarakāt）位置错误。
  原因是 GSUB 的 init/medi/fina/isol/rlig/calt/ccmp 以及 GPOS 的 mark/mkmk
  和 GDEF 字形类别没有被正确合并。

v1.1 起与旧版的区别：
  * 不再“从头重建 GSUB 并替换整个表”——目标字体原有的所有脚本、特性、查找表
    （CJK vert/locl、拉丁 liga/kern 等）全部保留，只追加/替换 'arab' 脚本。
  * 复制源字体查找表的原始 LookupFlag（如 IgnoreMarks / RightToLeft / 标记过滤集），
    并合并 GDEF 字形类别（基字/连字/标记），源字体没有 GDEF 时按 Unicode 类别生成。
  * 可选 --gpos：同时合并 GPOS（mark/mkmk/kern），否则元音符号不会定位。
  * 源字体中目标字体缺失的形式字形（词首/词中/词尾形、连字、组件）会连同组件、
    度量和 gvar（双方轴一致时）一起复制。
  * verify 会断言连写结果，失败时以非零状态退出。

用法：
  python merge_arabic_gsub.py --target TARGET.ttf --source SOURCE.ttf [--output OUT.ttf] [--gpos]

依赖：pip install fonttools uharfbuzz ；并需要本仓库的 build/ 目录（layout_merge.py 等）。
"""
import argparse
import copy
import hashlib
import os
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build'))

from fontTools.ttLib import TTFont                      # noqa: E402
from fontTools import subset                            # noqa: E402
from layout_merge import LayoutMerger, translate_tables  # noqa: E402

ARABIC_RANGES = [(0x0600, 0x06FF), (0x0750, 0x077F), (0x0870, 0x08FF),
                 (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)]


def is_arabic(cp):
    return any(a <= cp <= b for a, b in ARABIC_RANGES)


def load_target(path):
    """Load fully; reset gvar entries that cannot be decoded (instead of crashing)."""
    f = TTFont(path)
    if 'gvar' in f:
        gv = f['gvar']
        fixed = {}
        for g in f.getGlyphOrder():
            try:
                fixed[g] = gv.variations[g]
            except Exception:
                print('  警告: 字形 %s 的 gvar 数据损坏，已重置为静态' % g)
                fixed[g] = []
        gv.variations = fixed
    return f


def outline_hash(font, name):
    glyf, hm = font['glyf'], font['hmtx']
    try:
        c, e, fl = glyf[name].getCoordinates(glyf)
    except Exception:
        return None
    return hashlib.md5(repr((list(c), list(e), [x & 1 for x in fl], hm[name][0])).encode()).hexdigest()


def prepare_source(path, with_gpos):
    src = TTFont(path)
    cps = [cp for cp in src.getBestCmap() if is_arabic(cp)]
    if not cps:
        sys.exit('错误: 源字体没有阿拉伯文码位')
    opts = subset.Options()
    opts.layout_features = ['*']
    opts.layout_scripts = ['arab']
    opts.glyph_names = True
    opts.notdef_outline = True
    opts.hinting = False
    opts.layout_closure = True
    opts.name_IDs = ['*']
    if not with_gpos:
        opts.drop_tables += ['GPOS']
    s = subset.Subsetter(opts)
    s.populate(unicodes=cps)
    s.subset(src)
    return src


def map_glyphs(target, src):
    """source glyph -> (target glyph, is_new)"""
    tcmap = target.getBestCmap()
    tset = set(target.getGlyphOrder())
    rev = {}
    for cp, g in src.getBestCmap().items():
        rev.setdefault(g, cp)
    thash = {}
    tenc = set(tcmap.values())
    for g in target.getGlyphOrder():
        if g not in tenc:
            thash.setdefault(outline_hash(target, g), g)
    m, used = {}, set()
    for g in src.getGlyphOrder():
        if g == '.notdef':
            m[g] = ('.notdef', False)
            continue
        cp = rev.get(g)
        tg = tcmap.get(cp) if cp is not None else None
        if tg is None and cp is None:
            cand = thash.get(outline_hash(src, g))
            if cand and cand not in used:
                tg = cand
        if tg is not None and tg not in used:
            used.add(tg)
            m[g] = (tg, False)
        else:
            n, i = 'arab.' + g, 1
            while n in tset:
                i += 1
                n = 'arab.%s.%d' % (g, i)
            tset.add(n)
            m[g] = (n, True)
    return m


def copy_new_glyphs(target, src, m):
    """copy glyphs that do not exist in target (with components, metrics, gvar)."""
    go = list(target.getGlyphOrder())
    same_axes = ('fvar' in target and 'fvar' in src and
                 [a.axisTag for a in target['fvar'].axes] == [a.axisTag for a in src['fvar'].axes])
    if 'fvar' in target and 'fvar' in src and not same_axes:
        print('  警告: 源/目标轴不同，新增字形将为静态（无 gvar）')
    added = 0
    for g, (tg, new) in m.items():
        if not new:
            continue
        gl = copy.deepcopy(src['glyf'][g])
        if gl.isComposite():
            for c in gl.components:
                c.glyphName = m[c.glyphName][0]
        target['glyf'].glyphs[tg] = gl
        target['hmtx'].metrics[tg] = src['hmtx'][g]
        if 'vmtx' in target:                      # vmtx 不一定存在（旧版 KeyError）
            if 'vmtx' in src and g in src['vmtx'].metrics:
                target['vmtx'].metrics[tg] = src['vmtx'][g]
            else:
                asc = target['hhea'].ascent
                target['vmtx'].metrics[tg] = (target['head'].unitsPerEm, max(0, asc - getattr(gl, 'yMax', asc)))
        if 'gvar' in target:
            target['gvar'].variations[tg] = (copy.deepcopy(src['gvar'].variations.get(g, []))
                                             if same_axes and 'gvar' in src else [])
        go.append(tg)
        added += 1
    target.setGlyphOrder(go)
    target['glyf'].glyphOrder = go
    for g, (tg, new) in m.items():
        if new:
            target['glyf'][tg].recalcBounds(target['glyf'])
    return added                                  # 旧版这里恒为 0


def synthesize_gdef(src, tables, name_map):
    """source has no GDEF: classify by Unicode category (marks=3, ligatures=2, bases=1)."""
    from fontTools.ttLib.tables import otTables as ot
    cls = {}
    rev = {}
    for cp, g in src.getBestCmap().items():
        rev.setdefault(g, cp)
    ligs = set()
    gsub = tables.get('GSUB')
    if gsub:
        for lk in gsub.LookupList.Lookup:
            for st in lk.SubTable:
                st = getattr(st, 'ExtSubTable', st)
                if type(st).__name__ == 'LigatureSubst':
                    for ls in st.ligatures.values():
                        ligs.update(l.LigGlyph for l in ls)
    for g in src.getGlyphOrder():
        tg = name_map[g]
        cp = rev.get(g)
        if cp is not None and unicodedata.category(chr(cp)) in ('Mn', 'Me'):
            cls[tg] = 3
        elif tg in ligs:
            cls[tg] = 2
        else:
            cls[tg] = 1
    gd = ot.GDEF()
    gd.Version = 0x00010000
    gd.GlyphClassDef = ot.GlyphClassDef()
    gd.GlyphClassDef.classDefs = cls
    gd.AttachList = gd.LigCaretList = gd.MarkAttachClassDef = None
    return gd


def verify_shaping(font_path):
    """HarfBuzz check; returns number of failures."""
    try:
        import uharfbuzz as hb
    except ImportError:
        print('警告: 未安装 uharfbuzz，跳过验证')
        return 0
    face = hb.Face(hb.Blob.from_file_path(font_path))
    font = hb.Font(face)

    def shape(t):
        b = hb.Buffer()
        b.add_str(t)
        b.guess_segment_properties()
        hb.shape(font, b)
        return [i.codepoint for i in b.glyph_infos], [p.x_offset for p in b.glyph_positions], \
               [p.y_offset for p in b.glyph_positions]

    def isol(ch):
        return shape(ch)[0][0]

    fails = 0
    g, _, _ = shape('ببب')
    ok = len(g) == 3 and len(set(g)) == 3 and isol('ب') not in g
    print('  %s ببب -> %s（应为 词尾/词中/词首 三个不同字形）' % ('OK  ' if ok else 'FAIL', g))
    fails += not ok
    g, _, _ = shape('لا')
    ok = len(g) == 1
    print('  %s لا -> %s（应为 1 个 lam-alef 连字）' % ('OK  ' if ok else 'FAIL', g))
    fails += not ok
    g, xo, yo = shape('بِ')
    ok = len(g) == 2 and any(v != 0 for v in xo + yo)
    print('  %s بِ -> 偏移 x=%s y=%s（合并 GPOS 后元音符号应有非零偏移）' % ('OK  ' if ok else 'INFO', xo, yo))
    return fails


def main():
    ap = argparse.ArgumentParser(description='把阿拉伯文 OpenType 规则合并进目标字体（不破坏已有规则）')
    ap.add_argument('--target', required=True)
    ap.add_argument('--source', required=True, help='带正确阿拉伯文 GSUB/GPOS 的源字体（如 MiSans Arabic）')
    ap.add_argument('--output')
    ap.add_argument('--gpos', action='store_true', help='同时合并 GPOS（mark/mkmk/kern）')
    ap.add_argument('--no-verify', action='store_true')
    a = ap.parse_args()
    out = a.output or a.target

    print('加载目标字体:', a.target)
    target = load_target(a.target)
    print('加载并子集化源字体:', a.source)
    src = prepare_source(a.source, a.gpos)
    if 'fvar' in src and ('fvar' not in target or [x.axisTag for x in src['fvar'].axes]
                          != [x.axisTag for x in target['fvar'].axes]):
        # 轴不一致时 gvar / GPOS 变体数据无法直接复用：先把源字体实例化为默认静态字重
        from fontTools.varLib import instancer
        print('  源字体轴与目标不同，按源默认位置实例化为静态字体')
        src = instancer.instantiateVariableFont(src, {x.axisTag: None for x in src['fvar'].axes})
    if src['head'].unitsPerEm != target['head'].unitsPerEm:
        from fontTools.ttLib.scaleUpem import scale_upem
        scale_upem(src, target['head'].unitsPerEm)

    m = map_glyphs(target, src)
    print('字形映射: %d 个（其中新增 %d 个）' % (len(m), sum(1 for v in m.values() if v[1])))
    added = copy_new_glyphs(target, src, m)
    print('已复制缺失字形:', added)

    name_map = {g: v[0] for g, v in m.items()}
    own = translate_tables(target, {g: g for g in target.getGlyphOrder()})
    tabs = translate_tables(src, name_map, ('GSUB', 'GPOS', 'GDEF') if a.gpos else ('GSUB', 'GDEF'))
    if 'GDEF' not in tabs:
        tabs['GDEF'] = synthesize_gdef(src, tabs, name_map)
    merger = LayoutMerger(axis_count=len(target['fvar'].axes) if 'fvar' in target else 0)
    merger.add_source(own, scripts_exclude=('arab',))   # 保留目标原有的一切，只替换旧的 arab 脚本
    merger.add_source(tabs, scripts_filter=['arab'], override_classes=True)
    merger.build(target)
    if 'HVAR' in target:
        from fontTools.varLib.hvar import add_HVAR
        del target['HVAR']
        add_HVAR(target)

    target.save(out)
    print('已保存:', out)
    if not a.no_verify and verify_shaping(out):
        sys.exit('验证失败')


if __name__ == '__main__':
    main()
