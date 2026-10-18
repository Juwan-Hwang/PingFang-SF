import pickle, collections, numpy as np, freetype, json, sys
from fontTools.ttLib import TTFont
static=pickle.load(open('static.pkl','rb')); st=set(static)
OURS='../out/PingFang-SF-Medium.ttf'; SHSF='../src/shs/SourceHanSans-VF.ttf'
f=TTFont(OURS,lazy=True); cm=f.getBestCmap()
S=TTFont(SHSF); scm=S.getBestCmap()
# locl alternates per language
gsub=S['GSUB'].table; alts=collections.defaultdict(dict)
for sr in gsub.ScriptList.ScriptRecord:
    for ls in sr.Script.LangSysRecord:
        tag=ls.LangSysTag.strip()
        for fi in ls.LangSys.FeatureIndex:
            fr=gsub.FeatureList.FeatureRecord[fi]
            if fr.FeatureTag!='locl': continue
            for li in fr.Feature.LookupListIndex:
                for st_ in gsub.LookupList.Lookup[li].SubTable:
                    if st_.LookupType==7: st_=st_.ExtSubTable
                    if hasattr(st_,'mapping'): alts[tag].update(st_.mapping)
print({k:len(v) for k,v in alts.items()}, file=sys.stderr)
PX=96
def ftface(path):
    fa=freetype.Face(path); fa.set_pixel_sizes(PX,PX); return fa
fo=ftface(OURS); fs=ftface(SHSF)
def render(face,gid):
    face.load_glyph(gid, freetype.FT_LOAD_NO_BITMAP|freetype.FT_LOAD_NO_HINTING|freetype.FT_LOAD_TARGET_NORMAL)
    face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    b=face.glyph.bitmap; a=np.zeros((PX*2,PX*2),np.float32)
    if b.rows==0: return a
    arr=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]/255.0
    x=face.glyph.bitmap_left+PX//4; y=PX*3//2-face.glyph.bitmap_top
    try: a[y:y+b.rows, x:x+b.width]=arr
    except Exception: pass
    return a
def iou(a,b):
    return np.minimum(a,b).sum()/max(np.maximum(a,b).sum(),1e-6)
cps=sorted(c for c,g in cm.items() if g in st and c in scm)
W=list(range(250,901,50))
res={}
cache={}
def srender(gid,w):
    k=(gid,w)
    if k not in cache:
        fs.set_var_design_coords((w,)); cache[k]=render(fs,gid)
    return cache[k]
# iterate weight outer to minimize var switching
ours={c:render(fo,f.getGlyphID(cm[c])) for c in cps}
cands={}
for c in cps:
    g=scm[c]; cs={'JAN':g}
    for tag in ('ZHS','ZHT','ZHH','KOR'):
        if g in alts[tag]: cs[tag]=alts[tag][g]
    cands[c]=cs
best={c:(0,None,None) for c in cps}
for w in W:
    fs.set_var_design_coords((w,))
    for c in cps:
        for tag,g in cands[c].items():
            v=iou(ours[c], render(fs,S.getGlyphID(g)))
            if v>best[c][0]: best[c]=(v,tag,w)
out={hex(c):{'ch':chr(c),'iou':round(float(best[c][0]),4),'region':best[c][1],'w':best[c][2],'glyph':cm[c],'regions':sorted(cands[c])} for c in cps}
json.dump(out,open('classify_sh.json','w'),ensure_ascii=False,indent=0)
v=np.array([best[c][0] for c in cps])
print('n',len(cps),'iou>.95',(v>.95).sum(),'>.9',(v>.9).sum(),'>.8',(v>.8).sum())
print(collections.Counter((best[c][1],best[c][2]) for c in cps if best[c][0]>.9).most_common(30))
