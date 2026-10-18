import json, collections, re
from fontTools.ttLib import TTFont
f=TTFont('../out/PingFang-SF-Medium.ttf'); cmap=f.getBestCmap(); order=f.getGlyphOrder(); gid={g:i for i,g in enumerate(order)}
orph=open('orphans.txt').read().split()
ids=sorted(gid[g] for g in orph)
# ranges
rs=[];s=p=ids[0]
for i in ids[1:]:
    if i!=p+1: rs.append((s,p)); s=i
    p=i
rs.append((s,p)); print('orphan gid runs',len(rs), rs[:40])
glyf=f['glyf']
print('orphan composites', sum(glyf[g].isComposite() for g in orph))
# in GSUB at all?
gs=f['GSUB'].table; inlook=set()
for L in gs.LookupList.Lookup:
    for st in L.SubTable:
        x=st
        if L.LookupType==7: x=st.ExtSubTable
        for attr in ('mapping','alternates','ligatures'):
            m=getattr(x,attr,None)
            if m:
                for k,v in m.items():
                    inlook.add(k)
                    if isinstance(v,str): inlook.add(v)
                    elif attr=='alternates' or (attr=='mapping'): 
                        if isinstance(v,(list,tuple)): inlook.update(v)
                    if attr=='ligatures':
                        for lg in v: inlook.add(lg.LigGlyph); inlook.update(lg.Component)
print('orphans appearing in some GSUB subtable', sum(g in inlook for g in orph))
used_lookups=set()
for fr in gs.FeatureList.FeatureRecord: used_lookups.update(fr.Feature.LookupListIndex)
print('lookups',len(gs.LookupList.Lookup),'referenced by features',len(used_lookups))
# advances of orphans
hm=f['hmtx'].metrics; print(collections.Counter(hm[g][0] for g in orph).most_common(8))
print('orphan contour counts', collections.Counter(min(glyf[g].numberOfContours,20) for g in orph).most_common(10))
# PUA analysis
rev=collections.defaultdict(set)
for c,g in cmap.items(): rev[g].add(c)
pua=lambda c: 0xE000<=c<=0xF8FF or c>=0xF0000
pua_only=[g for g,cs in rev.items() if all(pua(c) for c in cs)]
print('glyphs reachable only via PUA', len(pua_only))
bmp=sorted(c for c in cmap if 0xE000<=c<=0xF8FF); print('BMP PUA', ['%04X'%c for c in bmp])
sp=sorted(c for c in cmap if c>=0xF0000); print('SPUA range', hex(sp[0]),hex(sp[-1]))
# composites referencing pua-only components
comp=set()
for g in pua_only:
    gg=glyf[g]
    if gg.isComposite(): comp.update(c.glyphName for c in gg.components)
nonpua_need=set()
for g in rev:
    if g in pua_only: continue
    gg=glyf[g]
    if gg.isComposite(): nonpua_need.update(c.glyphName for c in gg.components)
print('components used by PUA glyphs not otherwise mapped', len([c for c in comp if c not in rev and c not in nonpua_need]))
print('gvar sizes skip')
