import pickle, collections
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
static=set(pickle.load(open('static.pkl','rb')))
f=TTFont('../out/PingFang-SF-Medium.ttf',lazy=True); cm=f.getBestCmap()
gs=f.getGlyphSet()
S=TTFont('../src/shs/SourceHanSans-VF.ttf',lazy=True); scm=S.getBestCmap()
H=TTFont('../src/thhak/TH-Hak.ttf',lazy=True); hcm=H.getBestCmap(); hgs=H.getGlyphSet()
def feat(gs,g,scale=1):
    bp=BoundsPen(gs); gs[g].draw(bp); ap=AreaPen(gs); gs[g].draw(ap)
    b=bp.bounds
    return (tuple(round(x*scale) for x in b) if b else None, round(ap.value*scale*scale), gs[g].width*scale)
sgs={w:S.getGlyphSet(location={'wght':w}) for w in (250,300,350,400,500,700,900)}
rows=[]
cps=sorted(c for c,g in cm.items() if g in static)
import random
random.seed(1)
samp=[c for c in cps if 0x2E80<=c<=0x9FFF or c>=0x20000 or 0xF900<=c<=0xFAFF or 0x3000<=c<=0x33FF or 0xFF00<=c<=0xFFEF]
print(len(cps),'cjkish',len(samp),'inSHS',sum(c in scm for c in cps),'inTH',sum(c in hcm for c in cps),'both',sum(c in scm and c in hcm for c in cps), 'neither',sum(c not in scm and c not in hcm for c in cps))
for c in random.sample(samp,25):
    g=cm[c]; o=feat(gs,g)
    line=[hex(c),chr(c),str(o)]
    if c in hcm: line.append('TH'+str(feat(hgs,hcm[c],1000/256)))
    if c in scm:
        best=min(((abs(feat(sgs[w],scm[c])[1]-o[1]),w) for w in sgs))
        line.append('SHS'+str(feat(sgs[best[1]],scm[c]))+' w%d'%best[1])
    print(*line)
