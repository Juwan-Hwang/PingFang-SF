import json, collections, numpy as np, sys
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
d=json.load(open('classify_sh.json'))
f=TTFont('../out/PingFang-SF-Medium.ttf',lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
S=TTFont('../src/shs/SourceHanSans-VF.ttf'); scm=S.getBestCmap()
gsub=S['GSUB'].table; alts=collections.defaultdict(dict)
for sr in gsub.ScriptList.ScriptRecord:
    for ls in sr.Script.LangSysRecord:
        tag=ls.LangSysTag.strip()
        for fi in ls.LangSys.FeatureIndex:
            fr=gsub.FeatureList.FeatureRecord[fi]
            if fr.FeatureTag!='locl': continue
            for li in fr.Feature.LookupListIndex:
                for s in gsub.LookupList.Lookup[li].SubTable:
                    if s.LookupType==7: s=s.ExtSubTable
                    if hasattr(s,'mapping'): alts[tag].update(s.mapping)
def feat(G,gl):
    bp=BoundsPen(G); G[gl].draw(bp); ap=AreaPen(G); G[gl].draw(ap); return bp.bounds, ap.value, G[gl].width
cache={}
def sgs(w):
    if w not in cache: cache[w]=S.getGlyphSet(location={'wght':w})
    return cache[w]
out={}
for k,v in d.items():
    if v['iou']<0.8: continue
    c=int(k,16); og=cm[c]; ob,oa,ow=feat(gs,og)
    reg=v['region']; sg=scm[c] if reg=='JAN' else alts[reg][scm[c]]
    # area-match weight search 250..900 by bisection on area (monotonic)
    best=None
    for w in range(max(250,v['w']-60), min(900,v['w']+60)+1, 5):
        b,a,wd=feat(sgs(w),sg)
        e=abs(a-oa)/max(abs(oa),1)
        if best is None or e<best[0]: best=(e,w,b,wd)
    e,w,b,wd=best
    bd=max(abs(x-y) for x,y in zip(b,ob)) if b and ob else 999
    out[k]=dict(v, wfit=w, area_err=round(e,4), bbox_dev=round(bd,1), adv_ours=ow, adv_shs=wd, sglyph=sg)
json.dump(out,open('refine.json','w'),ensure_ascii=False,indent=0)
ok=[k for k,x in out.items() if x['bbox_dev']<=8 and x['adv_ours']==x['adv_shs'] and x['area_err']<0.03]
print(len(out),'ok',len(ok))
print('wfit distribution',collections.Counter(out[k]['wfit']//10*10 for k in ok).most_common(15))
bad=[(k,x['ch'],x['iou'],x['bbox_dev'],x['adv_ours'],x['adv_shs'],x['area_err']) for k,x in out.items() if k not in ok]
print(len(bad)); print(bad[:60])
