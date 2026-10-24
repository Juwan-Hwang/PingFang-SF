import sys
from fontTools.ttLib import TTFont
import json,collections
f=TTFont(sys.argv[1] if len(sys.argv) > 1 else '../../PingFang-SF Medium.ttf',lazy=True)
o={}
o['numGlyphs']=f['maxp'].numGlyphs
cm=f.getBestCmap(); o['codepoints']=len(cm)
o['upem']=f['head'].unitsPerEm
o['axes']=[(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in f['fvar'].axes]
nm=f['name']
o['instances']=[(nm.getDebugName(i.subfamilyNameID),i.coordinates) for i in f['fvar'].instances]
os2=f['OS/2']; o['os2']=dict(capH=os2.sCapHeight,xH=os2.sxHeight,asc=os2.sTypoAscender,desc=os2.sTypoDescender,gap=os2.sTypoLineGap,winA=os2.usWinAscent,winD=os2.usWinDescent,fsType=os2.fsType)
hh=f['hhea']; o['hhea']=(hh.ascent,hh.descent,hh.lineGap)
for t in ['GSUB','GPOS']:
  T=f[t].table; o[t+'_lookups']=len(T.LookupList.Lookup)
  o[t+'_features']=sorted(set(fr.FeatureTag for fr in T.FeatureList.FeatureRecord))
  o[t+'_scripts']=sorted(sr.ScriptTag for sr in T.ScriptList.ScriptRecord)
o['tables']=sorted(f.keys())
o['name']={i:nm.getDebugName(i) for i in [1,2,3,4,5,6,16,17]}
# block counts
def cnt(a,b): return sum(1 for c in cm if a<=c<=b)
o['cjk_basic']=cnt(0x4E00,0x9FFF); o['extA']=cnt(0x3400,0x4DBF); o['hangul_syll']=cnt(0xAC00,0xD7A3)
o['ascii_printable']=cnt(0x20,0x7E)
json.dump(o,open('analysis/facts.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(o,ensure_ascii=False,indent=1)[:6000])
