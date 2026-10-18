import time, resource
from fontTools.ttLib import TTFont
t0=time.time()
f=TTFont('PingFang-SF/PingFang-SF Medium.ttf')
gv=f['gvar']; n=0
for g in f.getGlyphOrder():
    n+=len(gv.variations.get(g,[]))
print('gvar tuples',n, time.time()-t0, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6,'GB')
gl=f['glyf']
for g in f.getGlyphOrder(): gl[g]
print('glyf', time.time()-t0, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6,'GB')
print(f['gvar'].reserved if hasattr(f['gvar'],'reserved') else '', [a.axisTag for a in f['fvar'].axes])
