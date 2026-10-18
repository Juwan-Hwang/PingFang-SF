import json
from fontTools.ttLib import TTFont
N=json.load(open('needs.json'))
P2=N['P2_symbols']
subs={'Yijing':(0x4DC0,0x4DFF),'TaiXuan':(0x1D300,0x1D35F),'CountRod':(0x1D360,0x1D37F),'SupPunct':(0x2E00,0x2E7F),'MiscSymArr':(0x2B00,0x2BFF),'MathA':(0x27C0,0x27EF),'MathB':(0x2980,0x29FF),'EnclAlnumS':(0x1F100,0x1F1FF),'IdeoSym':(0x16FE0,0x16FFF),'Fu':(0x1F260,0x1F265),'CtrlPic':(0x2400,0x243F),'23FF':(0x23FF,0x23FF)}
need={k:[c for c in P2 if a<=c<=b] for k,(a,b) in subs.items()}
print('need',{k:len(v) for k,v in need.items()})
F={'AppleSym':'src/osf/Apple Symbols.ttf','SegoeSym':'src/osf/seguisym6_24.ttf','NotoSym2':'src/gf/NotoSansSymbols2-Regular.ttf','NotoMath':'src/gf/NotoSansMath-Regular.ttf','STIX2Math':'src/osf/STIXTwoMath.otf','CambriaMath':'src/osf/cambria6_99.ttc','NotoSans':'src/gf/NotoSans[wdth,wght].ttf','SFPro':'../src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf','NotoSym':'src/gf/NotoSansSymbols[wght].ttf'}
C={}
for n,f in F.items():
    C[n]=set(TTFont(f,fontNumber=1 if 'cambria' in f else 0,lazy=True).getBestCmap())
    print(n.ljust(12),{k:sum(c in C[n] for c in v) for k,v in need.items()})
import itertools
order=['AppleSym','NotoMath','NotoSym2','NotoSans','SegoeSym']
got=set()
for n in order:
    new=set(P2)&C[n]-got; got|=new; print('chain +',n,len(new),'total',len(got))
miss=sorted(set(P2)-got); print('still missing',len(miss),' '.join('%04X'%c for c in miss))
