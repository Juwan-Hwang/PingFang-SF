import json, pickle, collections
from fontTools.ttLib import TTFont
sel=json.load(open('selection.json'))['sel']
static=set(pickle.load(open('static.pkl','rb')))
f=TTFont('../out/PingFang-SF-Medium.ttf',lazy=True)
def singles(font):
    g=font['GSUB'].table; res=collections.defaultdict(dict)
    for fr in g.FeatureList.FeatureRecord:
        for li in fr.Feature.LookupListIndex:
            L=g.LookupList.Lookup[li]
            for s in L.SubTable:
                if L.LookupType==7: s=s.ExtSubTable
                if hasattr(s,'mapping'): 
                    for a,b in s.mapping.items(): res[fr.FeatureTag].setdefault(a,b)
                elif hasattr(s,'alternates'):
                    for a,b in s.alternates.items(): res[fr.FeatureTag+'_alt'].setdefault(a,b[0])
    return res
os_=singles(f)
selg={x['glyph'] for x in sel.values()}
rel=collections.Counter(); ex=[]
for feat,m in os_.items():
    for a,b in m.items():
        if a in selg: rel[(feat, b in static)]+=1; ex.append((feat,a,b, b in static))
print(rel); print(ex[:40])
# also: glyphs used as components
glyf=f['glyf']; comp=collections.Counter()
for g in f.getGlyphOrder():
    G=glyf[g]
    if G.isComposite():
        for c in G.components:
            if c.glyphName in selg: comp[g]+=1
print('composites using selected', len(comp), list(comp)[:10])
# glyph shared by multiple cps
cm=f.getBestCmap(); rv=collections.defaultdict(list)
for c,g in cm.items(): rv[g].append(c)
print('multi-cp', [(g,[hex(c) for c in rv[g]]) for g in selg if len(rv[g])>1][:20])
print(f['HVAR'].table.AdvWidthMap is not None, len(f['HVAR'].table.VarStore.VarData), f['HVAR'].table.VarStore.VarRegionList.RegionCount)
hv=f['HVAR'].table; m=hv.AdvWidthMap.mapping
for g in list(selg)[:3]: print(g, m.get(g))
