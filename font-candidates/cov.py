import json,glob,os,sys
from fontTools.ttLib import TTFont, TTCollection
N=json.load(open('/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/addfont/needs.json'))
files=sorted(glob.glob('**/*.tt[fc]',recursive=True)+glob.glob('**/*.otf',recursive=True))
files.append('../../src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf')
rows=[]
for f in files:
    faces=[TTFont(f,fontNumber=i,lazy=True) for i in range(len(TTCollection(f,lazy=True).fonts))] if f.endswith('.ttc') else [TTFont(f,lazy=True)]
    for i,t in enumerate(faces):
        if f.endswith('.ttc') and i>0 and 'SDGothic' not in f and 'Myanmar' not in f and 'cambria' not in f: continue
        cm=set(t.getBestCmap() or {})
        name=t['name'].getDebugName(4)
        ax=' '.join(f"{a.axisTag}{a.minValue:g}-{a.maxValue:g}" for a in t['fvar'].axes) if 'fvar' in t else 'static w%d'%t['OS/2'].usWeightClass
        cov={k:sum(c in cm for c in v) for k,v in N.items()}
        cov={k:v for k,v in cov.items() if v}
        rows.append(dict(file=f,face=i,name=name,axes=ax,upm=t['head'].unitsPerEm,glyphs=t['maxp'].numGlyphs,outl='CFF' if 'CFF ' in t or 'CFF2' in t else 'glyf',cov=cov))
        print(f,i,name,ax,t['head'].unitsPerEm,t['maxp'].numGlyphs,cov,flush=True)
json.dump(rows,open('../coverage.json','w'),indent=0,ensure_ascii=False)
