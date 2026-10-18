import json
from fontTools.ttLib import TTFont
from fontTools import subset
N=json.load(open('needs.json'))
def cost(path,cps,idx=0,feats=None,exclude_have=None):
    f=TTFont(path,fontNumber=idx,lazy=False); cm=f.getBestCmap()
    cps=[c for c in cps if c in cm and (exclude_have is None or c not in exclude_have)]
    o=subset.Options(); o.layout_features=feats or ['*']; o.notdef_outline=True; o.layout_scripts=['*']; o.glyph_names=True
    s=subset.Subsetter(o); s.populate(unicodes=cps); s.subset(f)
    return len(cps), len(f.getGlyphOrder())-1
S='src/'
pret=S+'pretendard/public/variable/PretendardVariable.ttf'
pm=set(TTFont(pret,lazy=True).getBestCmap())
P2=set(N['P2_symbols'])
aps=set(TTFont(S+'osf/Apple Symbols.ttf',lazy=True).getBestCmap())
def blk(a,b): return {c for c in P2 if a<=c<=b}
rod=blk(0x1D360,0x1D37F); sup=blk(0x2E00,0x2E7F)
apple_part=(blk(0x4DC0,0x4DFF)|blk(0x1D300,0x1D35F)|blk(0x27C0,0x27EF)|blk(0x2980,0x29FF))&aps
seg_part=P2-apple_part-rod-sup
J=[
 ('Hangul: Pretendard VF',pret,N['P1_hangul'],0,['ccmp','locl','kern']),
 ('Hangul: Noto Sans KR VF fill (not in Pretendard)',S+'gf/NotoSansKR[wght].ttf',[c for c in N['P1_hangul'] if c not in pm],0,['ccmp','locl']),
 ('Hangul alt: Apple SD Gothic Neo',S+'osf/AppleSDGothicNeo.ttc',N['P1_hangul'],0,['ccmp','locl','kern']),
 ('Hangul alt: Noto Sans KR VF all',S+'gf/NotoSansKR[wght].ttf',N['P1_hangul'],0,['ccmp','locl','kern']),
 ('P2: Apple Symbols part',S+'osf/Apple Symbols.ttf',sorted(apple_part),0,None),
 ('P2: Segoe UI Symbol part',S+'osf/seguisym6_24.ttf',sorted(seg_part),0,None),
 ('P2: Noto Sans Symbols 2 counting rods',S+'gf/NotoSansSymbols2-Regular.ttf',sorted(rod),0,None),
 ('P2: Noto Sans VF suppl. punct',S+'gf/NotoSans[wdth,wght].ttf',sorted(sup),0,None),
 ('P3 Mongolian: Noto (GF)',S+'gf/NotoSansMongolian-Regular.ttf',N['P3_mongolian'],0,None),
 ('P3 Mongolian: Noto (macOS)',S+'osf/NotoSansMongolian-Regular.ttf',N['P3_mongolian'],0,None),
 ('P3 Mongolian: Mongolian Baiti',S+'osf/monbaiti5_54.ttf',N['P3_mongolian'],0,None),
 ('P3 Yi: Noto (GF)',S+'gf/NotoSansYi-Regular.ttf',N['P3_yi'],0,None),
 ('P3 Yi: Noto (macOS)',S+'osf/NotoSansYi-Regular.ttf',N['P3_yi'],0,None),
 ('P3 Lisu: Noto VF',S+'gf/NotoSansLisu[wght].ttf',N['P3_lisu'],0,None),
 ('P3 New Tai Lue: Noto VF',S+'gf/NotoSansNewTaiLue[wght].ttf',N['P3_newtailue'],0,None),
 ('P3 Tai Le: Noto (GF)',S+'gf/NotoSansTaiLe-Regular.ttf',N['P3_taile'],0,None),
 ('P3 Tai Le: Microsoft Tai Le',S+'osf/taile6_00.ttf',N['P3_taile'],0,None),
 ('P3 Miao: Noto (GF)',S+'gf/NotoSansMiao-Regular.ttf',N['P3_miao'],0,None),
 ('P3 Nushu: Noto Sans Nushu (GF)',S+'gf/NotoSansNushu-Regular.ttf',N['P3_nushu'],0,None),
 ('P4 math: STIX Two Math',S+'osf/STIXTwoMath.otf',N['P4_mathalnum'],0,['ccmp']),
 ('P4 LatinExtD: Noto Sans VF',S+'gf/NotoSans[wdth,wght].ttf',N['P4_latinextd'],0,['ccmp','locl','mark','mkmk']),
 ('P4 Arabic letters: SF Arabic',S+'apple/SF-Arabic/SF-Arabic.ttf',[c for c in N['P4_arabic'] if not 0xFB50<=c<=0xFEFF],0,['ccmp','isol','init','medi','fina','rlig','mark','mkmk']),
 ('P4 Arabic letters: Noto Arabic (all real)',S+'gf/NotoSansArabic[wdth,wght].ttf',[c for c in N['P4_arabic'] if not 0xFB50<=c<=0xFEFF],0,['ccmp','isol','init','medi','fina','rlig','mark','mkmk']),
 ('P4 Arabic pres. forms: Noto Arabic',S+'gf/NotoSansArabic[wdth,wght].ttf',[c for c in N['P4_arabic'] if 0xFB50<=c<=0xFEFF],0,['ccmp']),
 ('P4 Myanmar: Noto VF',S+'gf/NotoSansMyanmar[wdth,wght].ttf',N['P4_myanmar'],0,None),
]
out=[]
for lab,p,c,i,ft in J:
    n,g=cost(p,c,i,ft); out.append((lab,n,g)); print(f'{lab:50s} cps {n:5d} glyphs {g:5d}',flush=True)
json.dump(out,open('cost.json','w'),indent=1)
