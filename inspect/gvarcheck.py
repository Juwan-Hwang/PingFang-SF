import time, resource, collections, pickle, struct
from fontTools.ttLib import TTFont
f=TTFont('PingFang-SF/PingFang-SF Medium.ttf')
raw=f.reader['gvar']; print('gvar glyphCount field', struct.unpack('>H',raw[12:14])[0], 'numGlyphs', f['maxp'].numGlyphs)
gv=f['gvar']; bad=[]; n=0
origin,_=pickle.load(open('origin.pkl','rb'))
for g in f.getGlyphOrder():
    try: n+=len(gv.variations[g])
    except Exception as e: bad.append(g)
print('bad',len(bad), collections.Counter(origin.get(g,'other') for g in bad), bad[:10])
cm={v:k for k,v in f.getBestCmap().items()}
print([hex(cm[g]) for g in bad if g in cm][:40])
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6,'GB')
