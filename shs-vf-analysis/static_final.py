import pickle, collections
from fontTools.ttLib import TTFont
f=TTFont('out/final.ttf', lazy=True)
go=f.getGlyphOrder(); gv=f['gvar']; glyf=f['glyf']
cm=f.getBestCmap(); rev=collections.defaultdict(list)
for c,g in cm.items(): rev[g].append(c)
static=[]
for g in go:
    vs=gv.variations.get(g, [])
    nz=any(any(c is not None and c!=(0,0) for c in v.coordinates) for v in vs)
    if not nz:
        G=glyf[g]
        if G.numberOfContours!=0: static.append(g)
print("glyphs",len(go),'static non-empty',len(static))
pickle.dump(static,open('static_final.pkl','wb'))
st=set(static)
cps=[c for c,g in cm.items() if g in st]
print('static cps',len(cps))
b=collections.Counter(c>>8 for c in cps)
print(sorted((hex(k<<8),v) for k,v in b.items()))
print('composites among static', sum(1 for g in static if glyf[g].isComposite()))
