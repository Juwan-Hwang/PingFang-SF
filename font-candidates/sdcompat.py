import json,random
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
N=json.load(open('needs.json'))['P1_hangul']
faces={}
for i in range(0,18,2):
    t=TTFont('src/osf/AppleSDGothicNeo.ttc',fontNumber=i,lazy=True); faces[t['OS/2'].usWeightClass]=t
ws=sorted(faces); print(ws)
def sig(t,c):
    g=t.getBestCmap()[c]; p=RecordingPen(); t.getGlyphSet()[g].draw(p)
    return tuple(op for op,_ in p.value), t['hmtx'][g][0]
ok=bad=0; badl=[]; adv=set()
for c in N:
    s=[sig(faces[w],c) for w in ws]
    adv.add(tuple(x[1] for x in s))
    if all(x[0]==s[0][0] for x in s): ok+=1
    else:
        bad+=1; badl.append(c)
        if len(badl)<6: print('%04X'%c,[len(x[0]) for x in s])
print('compatible',ok,'incompatible',bad, 'advance sets',list(adv)[:5])
# partial: which weight pairs compatible
import collections
pair=collections.Counter()
for c in badl:
    s=[sig(faces[w],c)[0] for w in ws]
    for i in range(len(ws)-1): pair[(ws[i],ws[i+1])]+= s[i]!=s[i+1]
print(pair)
