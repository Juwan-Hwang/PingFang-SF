"""Step 5: naming, notices and metadata.

usage: python step5_finalize.py IN.ttf OUT.ttf
"""
import sys
from fontTools.ttLib import TTFont

VERSION = '1.100'
REPO = 'https://github.com/Juwan-Hwang/PingFang-SF'

COPYRIGHT = (
    '© 2024-2025 Apple Inc. (PingFang UI, SF Pro). '
    '© 2020-2023 Beijing Xiaomi Mobile Software Co., Ltd. (MiSans Arabic/Devanagari/Gujarati/'
    'Gurmukhi/Khmer/Lao/Myanmar/Thai/Tibetan). '
    '© 2014-2021 Adobe (Source Han Sans, SIL Open Font License 1.1). '
    'Glyphs from TH-Hak (© their author). All component fonts remain the property of their respective owners.')
TRADEMARK = ('PingFang and San Francisco are trademarks of Apple Inc. MiSans is a trademark of '
             'Xiaomi Inc. Source is a trademark of Adobe. This unofficial merge is not endorsed '
             'by any of these companies.')
LICENSE = ('Personal, non-commercial study use only; component fonts remain property of their '
           'owners. No warranty of any kind. Unofficial merge, not an Apple, Xiaomi or Adobe '
           'product. Will be removed immediately upon request of a rights holder.')
LICENSE_ZH = '仅限个人非商业学习研究使用；各组成字体版权归其原权利人所有。不提供任何担保。如权利人要求，将立即删除。'

FAMILY = {0x409: 'PingFang SF', 0x804: '苹方SF', 0x404: '蘋方SF', 0xC04: '蘋方SF'}


def main(inp, outp):
    f = TTFont(inp, lazy=True, recalcBBoxes=False)
    name = f['name']
    sub = name.getDebugName(2) or 'Medium'
    # remove records we rewrite
    rewrite = {0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 13, 14, 16, 17, 25}
    name.names = [n for n in name.names if n.nameID not in rewrite]
    W = (3, 1)
    for lang, fam in FAMILY.items():
        name.setName(fam, 1, *W, lang)
        name.setName(sub, 2, *W, lang)
        name.setName('%s %s' % (fam, sub), 4, *W, lang)
    name.setName(COPYRIGHT, 0, *W, 0x409)
    name.setName('PingFangSF-%s;%s;Juwan-Hwang' % (sub, VERSION), 3, *W, 0x409)
    name.setName('Version %s; merged from PingFang UI 21.4d1e1, SF Pro, MiSans' % VERSION, 5, *W, 0x409)
    name.setName('PingFangSF-%s' % sub, 6, *W, 0x409)
    name.setName(TRADEMARK, 7, *W, 0x409)
    name.setName('Juwan-Hwang (unofficial merge)', 8, *W, 0x409)
    name.setName(REPO, 11, *W, 0x409)
    name.setName(LICENSE, 13, *W, 0x409)
    name.setName(LICENSE_ZH, 13, *W, 0x804)
    name.setName(REPO + '#许可与免责声明', 14, *W, 0x409)
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
