import pickle,collections,json,math
rows,tv,W=pickle.load(open('data/ranked.pkl','rb'))
A=pickle.load(open('data/agg.pkl','rb'))
BASE=50102;TARGET=65435
def cband(d):
    d*=1e6
    for t,l in [(100,'A ≥100'),(10,'B 10–100'),(1,'C 1–10'),(0.3,'D 0.3–1'),(0.1,'E 0.1–0.3'),(0,'F <0.1')]:
        if d>=t and d>0: return l
    return 'G 0'
FAM={'Hangul KS X 1001':'Hangul','Hangul non-KS':'Hangul','Hangul compat jamo / enclosed':'Hangul'}
g=collections.OrderedDict()
for i,r in enumerate(rows):
    d=r['value']/r['glyphs']
    whole=r['cat'].startswith(('script:','addfont:P'))
    k=(r['IN'], r['cat'] if whole else (r['cat'],cband(d)))
    x=g.setdefault(k,dict(IN=r['IN'],cat=r['cat'],band='whole unit' if whole else cband(d),src=r['src'],cps=[],glyphs=0.0,value=0.0,maxd=d,first=i))
    x['cps']+=r['cps']; x['glyphs']+=r['glyphs']; x['value']+=r['value']
L=sorted(g.values(),key=lambda x:(not x['IN'],-x['value']/x['glyphs']))
cum=BASE
for n,x in enumerate(L,1):
    cum+=x['glyphs']; x['rank']=n; x['cum']=round(cum); x['glyphs']=round(x['glyphs'])
    x['density']=x['value']/max(1,x['glyphs'])*1e6
    # evidence: max df per corpus
    x['maxdf']={l:max([A[l]['df'].get(c,0) for c in x['cps']]+[0]) for l in ['zh','ko','en','yue','classical']}
pickle.dump(L,open('data/condensed.pkl','wb'))
for x in L:
    print(f"{x['rank']:3d} {'IN ' if x['IN'] else 'out'} {x['cat'][:30]:30s} {x['band']:10s} cps {len(x['cps']):5d} gl {x['glyphs']:5d} cum {x['cum']:6d} dens {x['density']:9.3f} {x['maxdf']}")
