from fontTools.ttLib import TTFont
import collections,re
f=TTFont('PingFang-SF/PingFang-SF Medium.ttf', lazy=True)
go=f.getGlyphOrder()
cm=f.getBestCmap()
print('cmap', len(cm), 'max', hex(max(cm)))
blocks=collections.Counter()
for cp in cm:
    blocks[cp>>12]+=1
print(sorted((hex(k<<12),v) for k,v in blocks.items()))
enc=set(cm.values())
un=[g for g in go if g not in enc]
print('unencoded',len(un), un[:30], un[-30:])
idx={g:i for i,g in enumerate(go)}
# positions of glyph#### names
gl=[i for i,g in enumerate(go) if g.startswith('glyph')]
print(gl[:5],gl[-5:])
print([t for t in f['cmap'].tables and [(t.platformID,t.platEncID,t.format,len(t.cmap)) for t in f['cmap'].tables]])
for i in [0,1,2,3,4,5,6,7,8,13,14,16,17,18,19,25]:
    try:print(i, f['name'].getDebugName(i))
    except: pass
for n in f['name'].names: print(n.nameID,n.platformID,hex(n.langID),n.toUnicode()[:80])
print(f['fvar'].instances and [(i.subfamilyNameID,i.coordinates,i.postscriptNameID) for i in f['fvar'].instances])
print(f['OS/2'].fsType, f['OS/2'].usWeightClass, f['head'].unitsPerEm, f['maxp'].numGlyphs)
print([ (a.axisTag,a.axisNameID) for a in f['fvar'].axes])
