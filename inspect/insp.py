from fontTools.ttLib import TTFont
import collections, re
f=TTFont('PingFang-SF/PingFang-SF Medium.ttf', lazy=True)
go=f.getGlyphOrder()
print(len(go), go[:20])
cm=f.getBestCmap()
# name patterns
pat=collections.Counter(re.sub(r'[0-9A-F]{4,6}','#',g.split('.')[0])[:12] for g in go)
print(pat.most_common(40))
suff=collections.Counter(g.split('.',1)[1] if '.' in g else '' for g in go)
print(suff.most_common(60))
for cp in [0x41,0x56,0x628,0x915,0x94D,0xE2A,0x1000,0x1780,0xF40,0x4E00,0xFF0C,0x3002,0x20000]:
    print(hex(cp), cm.get(cp))
print(f['gvar'].version if 'gvar' in f else None)
