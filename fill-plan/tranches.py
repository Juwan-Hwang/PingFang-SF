import pickle,json,math,collections
rows,totalV,W=pickle.load(open('data/ranked.pkl','rb'))
BASE=50102; TARGET=65435
def band(r):
    d=r['value']/r['glyphs']
    if d<=0: return -99
    return math.floor(math.log10(d)*2)/2   # half-decade bands
# group by (band, category), keep first-appearance order
groups=collections.OrderedDict()
for i,r in enumerate(rows):
    k=(band(r),r['cat'],r['IN']) if not r['cat'].startswith(('script:','addfont:P')) else (i,r['cat'])
    if r['value']<=0: k=('zero',r['cat'],r['prior'][0],r['IN'])
    g=groups.setdefault(k,dict(IN=r['IN'],cat=r['cat'],src=r['src'],cps=[],glyphs=0,value=0,first=i,keys=[]))
    g['cps']+=r['cps']; g['glyphs']+=r['glyphs']; g['value']+=r['value']; g['keys'].append(r['key'])
gl=sorted(groups.values(),key=lambda g:g['first'])
gl=[g for g in gl if g['IN']]+[g for g in gl if not g['IN']]
cum=BASE; cumV=0; out=[]
for n,g in enumerate(gl,1):
    cum+=g['glyphs']; cumV+=g['value']
    g.update(rank=n,cum=round(cum),cum_share=cumV/totalV,density=g['value']/g['glyphs'])
    out.append(g)
pickle.dump(out,open('data/tranches.pkl','wb'))
for g in out[:200]:
    flag='IN ' if g['IN'] else 'out'
    print(f"{g['rank']:3d} {flag} {g['cat'][:30]:30s} cps {len(g['cps']):6d} gl {g['glyphs']:7.0f} cum {g['cum']:6d} dens {g['density']*1e6:9.3f} cumshare {g['cum_share']:.4f}")
