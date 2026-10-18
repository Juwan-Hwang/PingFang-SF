import json, collections
from fontTools.ttLib import TTFont
r=json.load(open('refine.json'))
S=TTFont('../src/shs/SourceHanSans-VF.ttf',lazy=True); gv=S['gvar']; hm=S['hmtx']
def maxdelta(g):
    m=0
    for v in gv.variations.get(g,[]):
        for c in v.coordinates[:-4]:
            if c: m=max(m,abs(c[0]),abs(c[1]))
    return m
def advdelta(g):
    for v in gv.variations.get(g,[]):
        c=v.coordinates[-3]  # rsb phantom
        if c and c[0]: return c[0]
    return 0
sel={}; rej={}
for k,x in r.items():
    flip = abs(x['area_err']-2)<0.05
    ae = 0 if flip else x['area_err']
    reasons=[]
    if x['bbox_dev']>8: reasons.append('bbox_dev %s'%x['bbox_dev'])
    if ae>=0.05: reasons.append('area_err %s'%x['area_err'])
    if x['iou']<0.9: reasons.append('iou %s'%x['iou'])
    md=maxdelta(x['sglyph'])
    if md==0: reasons.append('SHS glyph not variable')
    x['flip']=flip; x['shs_maxdelta']=md; x['shs_advdelta']=advdelta(x['sglyph'])
    (rej if reasons else sel)[k]=dict(x,reasons=reasons)
print('selected',len(sel),'rejected',len(rej))
print('flip',sum(x['flip'] for x in sel.values()))
print('adv varies',[(k,x['ch'],x['adv_ours'],x['shs_advdelta']) for k,x in sel.items() if x['shs_advdelta']])
print('adv differs',[(k,x['ch'],x['adv_ours'],x['adv_shs']) for k,x in sel.items() if abs(x['adv_ours']-x['adv_shs'])>=1])
print('w250 sel',[(k,x['ch'],x['shs_maxdelta']) for k,x in sel.items() if x['wfit']<=260][:80])
print('rej', [(k,x['ch'],x['reasons']) for k,x in rej.items()])
json.dump({'sel':sel,'rej':rej},open('selection.json','w'),ensure_ascii=False,indent=0)
