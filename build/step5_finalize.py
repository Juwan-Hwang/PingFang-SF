"""Step 5: naming, notices and metadata.

usage: python step5_finalize.py IN.ttf OUT.ttf
"""
import sys
from fontTools.ttLib import TTFont

VERSION = '1.200'
REPO = 'https://github.com/Juwan-Hwang/PingFang-SF'
NOTICE_URL = REPO + '/blob/main/NOTICE.md'
THHAK_URL = 'http://cheonhyeong.com/Simplified/download.html'

# --- name table text (v1.1.1; v1.2.0 adds the variable Source Han Sans glyphs). Every component, its true rights holder and its licence. ---
# Sources of each statement: the component fonts' own name tables (PingFang UI 21.4d1e1,
# SF Pro 22.0d5e4, MiSans VF 1.000/1.100, TH-Hak V4.0.0/U15.0/220812), Adobe's OFL notice,
# and the TH-Hak download page + readme (THHAK_URL).
COPYRIGHT = {
    0x409: (
        'PingFang SF is an unofficial merge by Juwan-Hwang; all glyphs remain the property of '
        'their owners. Components: '
        'PingFang UI: © 2024-2025 Apple Inc. All rights reserved. '
        'SF Pro: © 2015-2026 Apple Inc. All rights reserved. '
        'MiSans (Arabic, Devanagari, Gujarati, Gurmukhi, Khmer, Lao, Myanmar, Thai, Tibetan): '
        '© 2020-2023 Beijing Xiaomi Mobile Software Co., Ltd. All Rights Reserved. '
        'Source Han Sans: © 2014-2021 Adobe (http://www.adobe.com/), with Reserved Font Name '
        "'Source'. "
        'TH-Hak (Tianheng Hei): Copyright TH-fonts, compiled by Shen Tianheng; per its author '
        'the outlines are by Zhongyi, DynaComware, Iwata, Besta and Founder.'),
    0x804: (
        '苹方SF 为 Juwan-Hwang 制作的非官方合并字体，所有字形版权归原权利人所有。组成：'
        '苹方 UI © 2024-2025 Apple Inc.；SF Pro © 2015-2026 Apple Inc.；'
        'MiSans（阿拉伯、天城、古吉拉特、古木基、高棉、老挝、缅甸、泰、藏文）© 2020-2023 北京小米移动软件有限公司；'
        '思源黑体 Source Han Sans © 2014-2021 Adobe（保留字体名称“Source”）；'
        '天珩字库-黑体（TH-Hak）© TH-fonts，沈天珩整理，据作者说明其字形版权属中易、华康、Iwata、Besta、方正。'),
    0x404: (
        '蘋方SF 為 Juwan-Hwang 製作的非官方合併字型，所有字形版權歸原權利人所有。組成：'
        '蘋方 UI © 2024-2025 Apple Inc.；SF Pro © 2015-2026 Apple Inc.；'
        'MiSans（阿拉伯、天城、古吉拉特、古木基、高棉、寮、緬甸、泰、藏文）© 2020-2023 北京小米移動軟件有限公司；'
        '思源黑體 Source Han Sans © 2014-2021 Adobe（保留字型名稱「Source」）；'
        '天珩字庫-黑體（TH-Hak）© TH-fonts，沈天珩整理，據作者說明其字形版權屬中易、華康、Iwata、Besta、方正。'),
}
TRADEMARK = ('San Francisco is a trademark of Apple Inc. PingFang, MiSans, Source Han Sans '
             'and TH-Hak are names of fonts of their respective owners; any trademarks belong to '
             'those owners. This unofficial merge is not affiliated with or endorsed by Apple, '
             'Xiaomi, Adobe or TH-fonts.')
MANUFACTURER = {0x409: 'Juwan-Hwang (unofficial personal merge)',
                0x804: 'Juwan-Hwang（非官方个人合并）', 0x404: 'Juwan-Hwang（非官方個人合併）'}
DESIGNER = {
    0x409: ('PingFang UI, SF Pro: Apple Inc. | MiSans: Xiaomi (produced by Monotype Imaging Inc.) | '
            'Source Han Sans: Adobe | TH-Hak: Shen Tianheng '
            '(TH-fonts) | merge: Juwan-Hwang'),
    0x804: ('苹方 UI、SF Pro：Apple Inc.｜MiSans：小米（Monotype 制作）｜思源黑体：Adobe｜'
            '天珩字库-黑体：沈天珩（TH-fonts）｜合并：Juwan-Hwang'),
    0x404: ('蘋方 UI、SF Pro：Apple Inc.｜MiSans：小米（Monotype 製作）｜思源黑體：Adobe｜'
            '天珩字庫-黑體：沈天珩（TH-fonts）｜合併：Juwan-Hwang'),
}
DESCRIPTION = {
    0x409: ('PingFang SF v1.2.0: PingFang UI (TC/HK/SC, variable wght 100-900, wdth 80-120, from '
            'the ACT-02/PingFangUI-VF 21.4d1e1 reconstruction) + SF Pro Latin/Greek/Cyrillic and '
            'symbols + MiSans for Arabic and 8 South/Southeast Asian scripts + extra CJK from Source '
            'Han Sans (variable 2.005) and TH-Hak 4.0.0 (' + THHAK_URL + '). '
            'Not an Apple, Xiaomi, Adobe or TH-fonts product.'),
    0x804: ('苹方SF v1.2.0：苹方 UI（繁/港/简，可变字重 100-900、字宽 80-120，取自 ACT-02/PingFangUI-VF 21.4d1e1 重建版）'
            '+ SF Pro 拉丁/希腊/西里尔字母与符号 + MiSans 阿拉伯文及 8 种南亚/东南亚文字 + 思源黑体（可变 2.005）与天珩字库-黑体 4.0.0 补充汉字。'
            '非 Apple、小米、Adobe 或天珩字库的官方产品。'),
    0x404: ('蘋方SF v1.2.0：蘋方 UI（繁/港/簡，可變字重 100-900、字寬 80-120，取自 ACT-02/PingFangUI-VF 21.4d1e1 重建版）'
            '+ SF Pro 拉丁/希臘/西里爾字母與符號 + MiSans 阿拉伯文及 8 種南亞/東南亞文字 + 思源黑體（可變 2.005）與天珩字庫-黑體 4.0.0 補充漢字。'
            '非 Apple、小米、Adobe 或天珩字庫的官方產品。'),
}
LICENSE = {
    0x409: (
        'No licence is granted by the merger. Each component keeps its own licence: PingFang UI - '
        'Apple proprietary font, licensed only with Apple software; SF Pro - Apple "License '
        'Agreement for the Apple San Francisco Font" (UI mock-ups for Apple platforms only, no '
        'redistribution or embedding); MiSans - Xiaomi "MiSans Font Intellectual Property License '
        'Agreement"; Source Han Sans - SIL Open Font License 1.1; '
        'TH-Hak - per its author a non-profit study/research collection, '
        'free of charge, no commercial use (' + THHAK_URL + '). This merge is provided for '
        'personal, non-commercial study only, AS IS, without warranty of any kind; all rights '
        'remain with the respective owners, and it will be taken down on request of any rights '
        'holder. Details: ' + NOTICE_URL),
    0x804: (
        '合并者不授予任何许可，各组成部分适用其原许可：苹方 UI 为 Apple 专有字体（仅随 Apple 软件授权）；'
        'SF Pro 适用 Apple《San Francisco 字体许可协议》（仅限为 Apple 平台制作界面样稿，禁止再分发或嵌入）；'
        'MiSans 适用小米《MiSans 字体知识产权许可协议》；思源黑体适用 SIL Open Font License 1.1；'
        '天珩字库-黑体据作者声明为非盈利学习研究用字库，不得收费、不得商用（' + THHAK_URL + '）。'
        '本合并字体仅供个人非商业学习研究，按“原样”提供，不作任何担保；一切权利归原权利人所有，权利人要求时立即下架。'
        '详见 ' + NOTICE_URL),
    0x404: (
        '合併者不授予任何授權，各組成部分適用其原授權：蘋方 UI 為 Apple 專有字型（僅隨 Apple 軟體授權）；'
        'SF Pro 適用 Apple《San Francisco 字型授權協議》（僅限為 Apple 平台製作介面樣稿，禁止再散布或嵌入）；'
        'MiSans 適用小米《MiSans 字體知識產權許可協議》；思源黑體適用 SIL Open Font License 1.1；'
        '天珩字庫-黑體據作者聲明為非營利學習研究用字庫，不得收費、不得商用（' + THHAK_URL + '）。'
        '本合併字型僅供個人非商業學習研究，按「原樣」提供，不作任何擔保；一切權利歸原權利人所有，權利人要求時立即下架。'
        '詳見 ' + NOTICE_URL),
}

FAMILY = {0x409: 'PingFang SF', 0x804: '苹方SF', 0x404: '蘋方SF', 0xC04: '蘋方SF'}


def main(inp, outp):
    f = TTFont(inp, lazy=True, recalcBBoxes=False)
    name = f['name']
    sub = name.getDebugName(2) or 'Medium'
    # remove records we rewrite
    rewrite = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 25}
    name.names = [n for n in name.names if n.nameID not in rewrite]
    W = (3, 1)
    for lang, fam in FAMILY.items():
        name.setName(fam, 1, *W, lang)
        name.setName(sub, 2, *W, lang)
        name.setName('%s %s' % (fam, sub), 4, *W, lang)
    name.setName('PingFangSF-%s;%s;Juwan-Hwang' % (sub, VERSION), 3, *W, 0x409)
    name.setName('Version %s; PingFang SF v1.2.0, merged from PingFang UI 21.4d1e1, SF Pro, '
                 'MiSans, Source Han Sans, TH-Hak' % VERSION, 5, *W, 0x409)
    name.setName('PingFangSF-%s' % sub, 6, *W, 0x409)
    name.setName(TRADEMARK, 7, *W, 0x409)
    for lang in (0x409, 0x804, 0x404):
        name.setName(COPYRIGHT[lang], 0, *W, lang)
        name.setName(MANUFACTURER[lang], 8, *W, lang)
        name.setName(DESIGNER[lang], 9, *W, lang)
        name.setName(DESCRIPTION[lang], 10, *W, lang)
        name.setName(LICENSE[lang], 13, *W, lang)
    name.setName(REPO, 11, *W, 0x409)
    name.setName(REPO, 12, *W, 0x409)
    name.setName(NOTICE_URL, 14, *W, 0x409)
    name.setName('PingFangSF', 25, *W, 0x409)
    # named-instance PostScript names still said PingFangUITC-*
    for n in name.names:
        if n.nameID > 255:
            s = n.toUnicode()
            if s.startswith('PingFangUITC-'):
                n.string = 'PingFangSF-' + s[len('PingFangUITC-'):]
    for inst in f['fvar'].instances:
        assert name.getDebugName(inst.subfamilyNameID)
        if inst.postscriptNameID != 0xFFFF:
            assert name.getDebugName(inst.postscriptNameID).startswith('PingFangSF-')
    head = f['head']
    head.fontRevision = float(VERSION)
    # keep the original PingFang UI vertical bounds: some renderers derive line spacing
    # from head.yMin/yMax (see commit 828631a)
    head.yMin, head.yMax = -232, 902
    f['maxp'].maxZones = 1
    os2 = f['OS/2']
    os2.fsType = 4          # Preview & Print: strictest of the sources (PingFang UI = 4)
    f.save(outp, reorderTables=True)
    print('saved', outp)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
