from fontTools.ttLib import TTFont
import pickle,sys
fs={'cur':'out/PingFang-SF-Medium.ttf','shsvf':'src/shs/SourceHanSans-VF.ttf','notosc':'src/shs/NotoSansSC-wght.ttf','notohk':'src/shs/NotoSansHK-wght.ttf','notatc':'src/shs/NotoSansTC-wght.ttf','thhak':'src/thhak/TH-Hak.ttf','pret':'addfont/src/pretendard/public/variable/PretendardVariable.ttf','notokr':'addfont/src/gf/NotoSansKR[wght].ttf','sdgn':'addfont/src/osf/AppleSDGothicNeo.ttc','cjksf':'addfont/src/osf/CJKSymbolsFallback.ttc'}
out={}
for k,p in fs.items():
    try:
        f=TTFont(p,fontNumber=0,lazy=True)
        out[k]=(set(f.getBestCmap()),len(f.getGlyphOrder()),'fvar' in f, f['name'].getDebugName(4))
        print(k,len(out[k][0]),out[k][1],out[k][2],out[k][3])
    except Exception as e: print(k,e)
pickle.dump(out,open('fillplan/data/cmaps.pkl','wb'))
