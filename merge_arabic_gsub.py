#!/usr/bin/env python3
"""
merge_arabic_gsub.py — 合并阿拉伯文字体的 GSUB shaping 规则

解决的核心问题：
  合并阿拉伯文字体后，字母不连写（全部显示为孤立形式）。
  原因是 GSUB 中的 init/medi/fina/isol/rlig 规则没有被正确合并。

用法：
  python merge_arabic_gsub.py --target TARGET.ttf --source SOURCE.ttf [--output OUTPUT.ttf]

  TARGET: 目标字体（已有阿拉伯文字形但缺少 GSUB 规则）
  SOURCE: 源字体（有正确的阿拉伯文 GSUB 规则，如 MiSans Arabic）
  OUTPUT: 输出路径（默认覆盖 TARGET）

原理：
  1. 通过 Unicode 码位建立源→目标字形名映射
  2. 从源字体提取 init/medi/fina/isol/rlig 的替换规则
  3. 用映射将源字形名翻译为目标字形名
  4. 从头构建 GSUB 表（不深拷贝，避免 fontTools 编译缓存问题）
  5. 只保留源和目标都存在的映射

依赖：
  pip install fonttools uharfbuzz
"""

import argparse
import copy
import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_v_a_r import table__g_v_a_r
from fontTools.ttLib.tables.G_S_U_B_ import table_G_S_U_B_
from fontTools.ttLib.tables import otTables
import struct


def patch_gvar_decompile(font):
    """修复 fontTools gvar lazy loading 问题。

    当字体的 gvar.glyphCount 与实际字形数不匹配时，
    fontTools 的 decompile 会抛 AssertionError。
    这个补丁在 decompile 前强制对齐 glyphCount。
    """
    _orig = table__g_v_a_r.decompile

    def _patched(self, data, f):
        fixed = data[:12] + struct.pack('>H', len(f.getGlyphOrder())) + data[14:]
        _orig(self, fixed, f)

    table__g_v_a_r.decompile = _patched
    return _orig


def restore_gvar_decompile(orig):
    table__g_v_a_r.decompile = orig


def fix_gvar_lazy_dict(font):
    """强制 gvar 完整 decompile 到内存，替换 lazydict 为普通 dict。

    不写 gvar 条目 = 该字形在所有轴上 delta=0（OpenType 规范允许）。
    """
    if 'gvar' not in font:
        return
    gvar = font['gvar']
    go = font.getGlyphOrder()
    good = {}
    for g in go:
        try:
            good[g] = gvar.variations[g] if g in gvar.variations else []
        except Exception:
            good[g] = []  # 损坏的条目 → 静态字形
    gvar.variations = good


def build_name_map(source, target):
    """通过 Unicode 码位建立 源字形名→目标字形名 映射。"""
    src_cmap = source['cmap'].getBestCmap()
    tgt_cmap = target['cmap'].getBestCmap()
    name_map = {}
    for cp in set(src_cmap) & set(tgt_cmap):
        name_map[src_cmap[cp]] = tgt_cmap[cp]
    return name_map


def extract_arabic_mappings(source, name_map, target_glyphs):
    """从源字体提取阿拉伯文 positional substitution 映射。

    返回 {(目标字形名, feature_tag): 目标替换字形名}
    """
    gsub = source['GSUB'].table
    gsub.ensureDecompiled(recurse=True)
    result = {}

    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag != 'arab':
            continue
        dl = sr.Script.DefaultLangSys
        for fi in dl.FeatureIndex:
            fr = gsub.FeatureList.FeatureRecord[fi]
            tag = fr.FeatureTag
            if tag not in ('init', 'medi', 'fina', 'isol'):
                continue
            for lk_idx in fr.Feature.LookupListIndex:
                lk = gsub.LookupList.Lookup[lk_idx]
                if lk.LookupType == 1:  # SingleSubst
                    for st in lk.SubTable:
                        st.ensureDecompiled()
                        if hasattr(st, 'mapping'):
                            for src, dst in st.mapping.items():
                                tgt_src = name_map.get(src, src)
                                tgt_dst = name_map.get(dst, dst)
                                if tgt_src in target_glyphs and tgt_dst in target_glyphs:
                                    result[(tgt_src, tag)] = tgt_dst
                elif lk.LookupType == 6:  # ChainContextSubst (isol 可能用这个)
                    _extract_chain_context(lk, gsub, name_map, target_glyphs, tag, result)

    return result


def _extract_chain_context(lk, gsub, name_map, target_glyphs, tag, result):
    """从 ChainContextSubst lookup 中提取实际的 SingleSubst 映射。"""
    for st in lk.SubTable:
        st.ensureDecompiled()
        if not hasattr(st, 'SubstLookupRecord') or not st.SubstLookupRecord:
            continue
        for lr in st.SubstLookupRecord:
            sub_lk = gsub.LookupList.Lookup[lr.LookupListIndex]
            if sub_lk.LookupType == 1:
                for sst in sub_lk.SubTable:
                    sst.ensureDecompiled()
                    if hasattr(sst, 'mapping'):
                        for src, dst in sst.mapping.items():
                            tgt_src = name_map.get(src, src)
                            tgt_dst = name_map.get(dst, dst)
                            if tgt_src in target_glyphs and tgt_dst in target_glyphs:
                                result[(tgt_src, tag)] = tgt_dst


def extract_rlig_ligatures(source, name_map, target_glyphs):
    """从源字体提取 rlig (Required Ligature) 映射。

    返回 [(first_glyph, [components], ligature_glyph)]
    """
    gsub = source['GSUB'].table
    gsub.ensureDecompiled(recurse=True)
    result = []

    for sr in gsub.ScriptList.ScriptRecord:
        if sr.ScriptTag != 'arab':
            continue
        dl = sr.Script.DefaultLangSys
        for fi in dl.FeatureIndex:
            fr = gsub.FeatureList.FeatureRecord[fi]
            if fr.FeatureTag != 'rlig':
                continue
            for lk_idx in fr.Feature.LookupListIndex:
                lk = gsub.LookupList.Lookup[lk_idx]
                if lk.LookupType == 4:  # LigatureSubst
                    for st in lk.SubTable:
                        st.ensureDecompiled()
                        if hasattr(st, 'ligatures'):
                            for first, lig_list in st.ligatures.items():
                                tgt_first = name_map.get(first, first)
                                if tgt_first not in target_glyphs:
                                    continue
                                for lig in lig_list:
                                    tgt_comp = [name_map.get(c, c) for c in lig.Component]
                                    tgt_lig = name_map.get(lig.LigGlyph, lig.LigGlyph)
                                    if (all(c in target_glyphs for c in tgt_comp)
                                            and tgt_lig in target_glyphs):
                                        result.append((tgt_first, tgt_comp, tgt_lig))
    return result


def build_gsub(arabic_mappings, rlig_ligatures):
    """从头构建 GSUB 表。

    关键：不深拷贝源字体的 GSUB 对象，避免 fontTools 编译缓存问题。
    fontTools 的 dirty 标记机制不可靠，从头构建最安全。
    """
    gsub_ot = otTables.GSUB()
    gsub_ot.Version = 0x00010000

    # ScriptList
    gsub_ot.ScriptList = otTables.ScriptList()
    gsub_ot.ScriptList.ScriptRecord = []
    arab_script = otTables.ScriptRecord()
    arab_script.ScriptTag = 'arab'
    arab_script.Script = otTables.Script()
    arab_script.Script.DefaultLangSys = otTables.LangSys()
    arab_script.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
    arab_script.Script.DefaultLangSys.LangSysRecord = []

    # FeatureList
    gsub_ot.FeatureList = otTables.FeatureList()
    gsub_ot.FeatureList.FeatureRecord = []

    # LookupList
    gsub_ot.LookupList = otTables.LookupList()
    gsub_ot.LookupList.Lookup = []

    feature_indices = []

    # SingleSubst features: fina, init, medi, isol
    for tag in ['fina', 'init', 'medi', 'isol']:
        mapping = {src: dst for (src, t), dst in arab_mappings.items() if t == tag}
        if not mapping:
            continue

        lookup = otTables.Lookup()
        lookup.LookupType = 1
        lookup.LookupFlag = 0
        lookup.SubTableCount = 1
        st = otTables.SingleSubst()
        st.mapping = mapping
        lookup.SubTable = [st]

        lk_idx = len(gsub_ot.LookupList.Lookup)
        gsub_ot.LookupList.Lookup.append(lookup)

        fr = otTables.FeatureRecord()
        fr.FeatureTag = tag
        fr.Feature = otTables.Feature()
        fr.Feature.FeatureParams = None
        fr.Feature.LookupListIndex = [lk_idx]
        fr.Feature.LookupCount = 1

        fi = len(gsub_ot.FeatureList.FeatureRecord)
        gsub_ot.FeatureList.FeatureRecord.append(fr)
        feature_indices.append(fi)

    # LigatureSubst feature: rlig
    if rlig_ligatures:
        ligatures_by_first = {}
        for first, comp, lig in rlig_ligatures:
            if first not in ligatures_by_first:
                ligatures_by_first[first] = []
            lig_obj = otTables.Ligature()
            lig_obj.Component = comp
            lig_obj.LigGlyph = lig
            lig_obj.CompCount = len(comp) + 1
            ligatures_by_first[first].append(lig_obj)

        lookup = otTables.Lookup()
        lookup.LookupType = 4
        lookup.LookupFlag = 0
        lookup.SubTableCount = 1
        st = otTables.LigatureSubst()
        st.ligatures = ligatures_by_first
        lookup.SubTable = [st]

        lk_idx = len(gsub_ot.LookupList.Lookup)
        gsub_ot.LookupList.Lookup.append(lookup)

        fr = otTables.FeatureRecord()
        fr.FeatureTag = 'rlig'
        fr.Feature = otTables.Feature()
        fr.Feature.FeatureParams = None
        fr.Feature.LookupListIndex = [lk_idx]
        fr.Feature.LookupCount = 1

        fi = len(gsub_ot.FeatureList.FeatureRecord)
        gsub_ot.FeatureList.FeatureRecord.append(fr)
        feature_indices.append(fi)

    arab_script.Script.DefaultLangSys.FeatureIndex = feature_indices
    arab_script.Script.DefaultLangSys.FeatureCount = len(feature_indices)
    gsub_ot.ScriptList.ScriptRecord.append(arab_script)
    gsub_ot.ScriptList.ScriptCount = 1

    wrapper = table_G_S_U_B_()
    wrapper.table = gsub_ot
    return wrapper


def fix_composite_glyphs(target, source):
    """修复目标字体中复合字形引用了不存在组件的问题。

    从源字体复制缺失的组件字形。
    """
    go_set = set(target.getGlyphOrder())
    glyf = target['glyf']
    src_glyf = source['glyf']
    src_go = set(source.getGlyphOrder())
    hmtx = target['hmtx']
    vmtx = target['vmtx']
    src_hmtx = source['hmtx']
    src_vmtx = source['vmtx'] if 'vmtx' in source else None
    go_list = list(target.getGlyphOrder())

    for iteration in range(5):
        broken = []
        for gn in go_list:
            g = glyf.glyphs.get(gn)
            if g is None:
                continue
            if hasattr(g, 'isComposite') and g.isComposite() and hasattr(g, 'components'):
                for comp in g.components:
                    if comp.glyphName not in go_set:
                        broken.append(comp.glyphName)

        if not broken:
            break

        added = 0
        for comp_name in set(broken):
            if comp_name not in go_set and comp_name in src_go:
                src_g = src_glyf[comp_name]
                try:
                    src_g.expand(src_glyf)
                except Exception:
                    pass
                go_list.append(comp_name)
                go_set.add(comp_name)
                glyf[comp_name] = copy.deepcopy(src_g)
                hmtx.metrics[comp_name] = src_hmtx.metrics.get(comp_name, (500, 0))
                vmtx.metrics[comp_name] = (
                    src_vmtx.metrics.get(comp_name, (1000, 0))
                    if src_vmtx else (1000, 0)
                )
                added += 1

        if added == 0:
            break
        target.setGlyphOrder(go_list)

    return len(go_list) - len(target.getGlyphOrder())


def pre_expand_glyphs(font):
    """预展开所有复合字形，防止保存时 RecursionError。

    fontTools 的 glyf.__getitem__ 会调用 expand()，
    如果组件是 lazy 壳会导致无限递归。
    """
    glyf = font['glyf']
    for gname in font.getGlyphOrder():
        g = glyf.glyphs.get(gname)
        if g is None:
            continue
        try:
            g.expand(glyf)
        except Exception:
            pass
        if hasattr(g, 'isComposite') and g.isComposite():
            if not hasattr(g, 'xMin') or g.xMin is None:
                g.xMin = g.yMin = g.xMax = g.yMax = 0


def verify_shaping(font_path, test_strings=None):
    """用 HarfBuzz 验证阿拉伯文 shaping。"""
    try:
        import uharfbuzz as hb
    except ImportError:
        print("警告: uharfbuzz 未安装，跳过 shaping 验证")
        return

    font_obj = TTFont(font_path)
    go = font_obj.getGlyphOrder()

    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    hb_font = hb.Font(face)

    if test_strings is None:
        test_strings = [
            ('ببب', '三个 ب (应得到 fina/medi/init)'),
            ('لا', 'لا (应得到 lam-alef 连字)'),
            ('الله', 'الله (应得到 Allah 合字)'),
        ]

    print("\n=== Shaping 验证 ===")
    for text, label in test_strings:
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hb_font, buf)
        result = []
        for info in buf.glyph_infos:
            name = go[info.codepoint] if info.codepoint < len(go) else f'gid{info.codepoint}'
            result.append(name)
        print(f'  {label}: {result}')


def main():
    parser = argparse.ArgumentParser(
        description='合并阿拉伯文字体的 GSUB shaping 规则到目标字体')
    parser.add_argument('--target', required=True, help='目标字体路径')
    parser.add_argument('--source', required=True, help='源字体路径（有正确的阿拉伯文 GSUB）')
    parser.add_argument('--output', default=None, help='输出路径（默认覆盖 target）')
    parser.add_argument('--no-verify', action='store_true', help='跳过 shaping 验证')
    args = parser.parse_args()

    output = args.output or args.target

    # 加载目标字体（带 gvar 补丁）
    orig_decompile = patch_gvar_decompile(None)
    # 需要先设置补丁再加载
    orig_decompile = patch_gvar_decompile(None)
    _orig = table__g_v_a_r.decompile
    def _patch(self, data, font):
        _orig(self, data[:12] + struct.pack('>H', len(font.getGlyphOrder())) + data[14:], font)
    table__g_v_a_r.decompile = _patch

    print(f'加载目标字体: {args.target}')
    target = TTFont(args.target)
    table__g_v_a_r.decompile = _orig

    fix_gvar_lazy_dict(target)

    print(f'加载源字体: {args.source}')
    source = TTFont(args.source)

    target_glyphs = set(target.getGlyphOrder())
    print(f'目标字形数: {len(target_glyphs)}')

    # 建立映射
    name_map = build_name_map(source, target)
    print(f'字形名映射: {len(name_map)} 条')

    # 提取映射
    arabic_mappings = extract_arabic_mappings(source, name_map, target_glyphs)
    for tag in ['init', 'medi', 'fina', 'isol']:
        count = sum(1 for (s, t) in arabic_mappings if t == tag)
        print(f'  {tag}: {count} 映射')

    rlig_ligatures = extract_rlig_ligatures(source, name_map, target_glyphs)
    print(f'  rlig: {len(rlig_ligatures)} 连字')

    if not arabic_mappings and not rlig_ligatures:
        print('错误: 没有找到有效的阿拉伯文映射')
        sys.exit(1)

    # 修复复合字形组件
    added = fix_composite_glyphs(target, source)
    if added:
        print(f'修复复合字形组件: +{added}')

    # 构建 GSUB
    print('构建 GSUB...')
    gsub = build_gsub(arabic_mappings, rlig_ligatures)

    if 'GSUB' in target.tables:
        del target.tables['GSUB']
    target['GSUB'] = gsub

    # 预展开 + 保存
    print('预展开字形...')
    pre_expand_glyphs(target)
    target.recalcBBoxes = False

    print(f'保存: {output}')
    target.save(output)
    print('保存成功')

    # 验证
    if not args.no_verify:
        verify_shaping(output)


if __name__ == '__main__':
    main()
