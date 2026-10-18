import pickle, hashlib, collections, glob
import numpy as np
from fontTools.ttLib import TTFont
def sig(font):
    glyf=font['glyf']; hm=font['hmtx']; out={}
    for g in font.getGlyphOrder():
        try: c,e,fl=glyf[g].getCoordinates(glyf)
        except Exception: out[g]=None; continue
        key=hashlib.md5(repr((list(e),[x&1 for x in fl])).encode()).hexdigest()
        out[g]=(key, np.array(c,dtype=np.int32).reshape(-1,2) if len(c) else np.zeros((0,2),np.int32), hm[g][0])
    return out
t=TTFont('PingFang-SF/PingFang-SF Medium.ttf', lazy=True)
ts=sig(t); tcm=t.getBestCmap(); go=t.getGlyphOrder()
th=pickle.load(open('target_hash.pkl','rb')); ph=pickle.load(open('pf21_hash.pkl','rb'))
pfset=set(ph.values())
origin={}
for g in go:
    if th[g] in pfset: origin[g]='PF'
def match(srcfont, label, tol):
    ss=sig(srcfont); scm=srcfont.getBestCmap()
    buckets=collections.defaultdict(list)
    for g,v in ss.items():
        if v: buckets[v[0]].append(g)
    m={}
    for g in go:
        if g in origin: continue
        v=ts[g]
        if not v or len(v[1])==0: continue
        cands=buckets.get(v[0],[])
        best=None
        for c in cands:
            sv=ss[c]
            if abs(sv[2]-v[2])>tol: continue
            d=np.abs(sv[1]-v[1]).max()
            if d<=tol and (best is None or d<best[0]): best=(d,c)
        if best: m[g]=best[1]
    return m
maps={}
for p in sorted(glob.glob('src/mvf/*.ttf')):
    nm=p.split('/')[-1][:-4]
    m=match(TTFont(p), nm, 0)
    for g in m: origin[g]='MI-'+nm
    maps['MI-'+nm]=m
    print(nm, len(m))
m=match(TTFont('work_sf540.ttf'),'SF',3)
for g in m: origin.setdefault(g,'SF')
maps['SF']=m; print('SF',len(m))
cnt=collections.Counter(origin.get(g,'other') for g in go)
print(cnt)
unenc=set(go)-set(tcm.values())
print('unencoded by origin', collections.Counter(origin.get(g,'other') for g in unenc))
pickle.dump((origin,maps),open('origin.pkl','wb'))
# other: show sample cps
oth=[ (hex(cp),g) for cp,g in tcm.items() if g not in origin]
print(len(oth), oth[:10], oth[-10:])
blocks=collections.Counter(int(c,16)>>8 for c,g in oth); print(sorted((hex(k<<8),v) for k,v in blocks.items())[:80])
