import json,pickle,sys
from fontTools.ttLib import TTFont
from fontTools import subset
cm=pickle.load(open('data/cmaps.pkl','rb')); cur=cm['cur'][0]
assigned=set()
for l in open('../audit/ucd/UnicodeData.txt'):
    f=l.split(';'); c=int(f[0],16)
    if f[1].endswith('First>'): a=c; continue
    if f[1].endswith('Last>'): assigned|=set(range(a,c+1)); continue
    assigned.add(c)
emo=set()
for l in open('../audit/ucd/emoji-data.txt'):
    if 'Emoji_Presentation' in l and not l.startswith('#'):
        r=l.split(';')[0].strip(); a,b=(r.split('..')+[r])[:2]; emo|=set(range(int(a,16),int(b,16)+1))
def need(*rngs):
    s=set()
    for a,b in rngs: s|={c for c in range(a,b+1) if c in assigned and c not in cur and c not in emo}
    return s
def cost(path,cps,idx=0,feats=None):
    f=TTFont(path,fontNumber=idx); fc=f.getBestCmap()
    have=[c for c in cps if c in fc]
    o=subset.Options(); o.layout_features=feats or ['*']; o.notdef_outline=True; o.layout_scripts=['*']; o.glyph_names=True; o.name_IDs=[]
    s=subset.Subsetter(o); s.populate(unicodes=have); s.subset(f)
    return have, len(f.getGlyphOrder())-1
S='src/'; G='src/gf/'; A='../addfont/src/'
J=[
 ('Armenian','SF Armenian VF (Apple, glyf, wght 1-1000)',S+'SFArmenian.ttf',0,[(0x530,0x58F),(0xFB13,0xFB17)]),
 ('Georgian','SF Georgian VF (Apple) Mkhedruli+Mtavruli',S+'SFGeorgian.ttf',0,[(0x10A0,0x10FF),(0x1C90,0x1CBF)]),
 ('Georgian-rest','Noto Sans Georgian VF (Asomtavruli/Nuskhuri)',G+'NotoSansGeorgian[wdth,wght].ttf',0,[(0x10A0,0x10FF),(0x2D00,0x2D2F)]),
 ('Bengali','SF Bangla VF (Apple SF India, CFF2)',S+'SFIndia.ttc',0,[(0x980,0x9FF)]),
 ('Bengali-noto','Noto Sans Bengali VF',G+'NotoSansBengali[wdth,wght].ttf',0,[(0x980,0x9FF)]),
 ('Tamil','SF Tamil VF (Apple SF India, CFF2)',S+'SFIndia.ttc',7,[(0xB80,0xBFF)]),
 ('Telugu','SF Telugu VF',S+'SFIndia.ttc',8,[(0xC00,0xC7F)]),
 ('Kannada','SF Kannada VF',S+'SFIndia.ttc',4,[(0xC80,0xCFF)]),
 ('Malayalam','SF Malayalam VF',S+'SFIndia.ttc',5,[(0xD00,0xD7F)]),
 ('Odia','SF Odia VF',S+'SFIndia.ttc',6,[(0xB00,0xB7F)]),
 ('Sinhala','Noto Sans Sinhala VF',G+'NotoSansSinhala[wdth,wght].ttf',0,[(0xD80,0xDFF)]),
 ('Ethiopic','Kefa III VF (Apple, wght 300-800)',S+'KefaIII.ttf',0,[(0x1200,0x139F),(0x2D80,0x2DDF),(0xAB00,0xAB2F)]),
 ('Ethiopic-noto','Noto Sans Ethiopic VF',G+'NotoSansEthiopic[wdth,wght].ttf',0,[(0x1200,0x139F),(0x2D80,0x2DDF),(0xAB00,0xAB2F),(0x1E7E0,0x1E7FF)]),
 ('Cherokee','Noto Sans Cherokee VF',G+'NotoSansCherokee[wght].ttf',0,[(0x13A0,0x13FF),(0xAB70,0xABBF)]),
 ('UCAS','Noto Sans Canadian Aboriginal VF',G+'NotoSansCanadianAboriginal[wght].ttf',0,[(0x1400,0x167F),(0x18B0,0x18FF),(0x11AB0,0x11ABF)]),
 ('Thaana','Noto Sans Thaana VF',G+'NotoSansThaana[wght].ttf',0,[(0x780,0x7BF)]),
 ('Syriac','Noto Sans Syriac VF',G+'NotoSansSyriac[wght].ttf',0,[(0x700,0x74F),(0x860,0x86F)]),
 ('NKo','Noto Sans NKo',G+'NotoSansNKo-Regular.ttf',0,[(0x7C0,0x7FF)]),
 ('Adlam','Noto Sans Adlam VF',G+'NotoSansAdlam[wght].ttf',0,[(0x1E900,0x1E95F)]),
 ('OlChiki','Noto Sans Ol Chiki VF',G+'NotoSansOlChiki[wght].ttf',0,[(0x1C50,0x1C7F)]),
 ('Javanese','Noto Sans Javanese VF',G+'NotoSansJavanese[wght].ttf',0,[(0xA980,0xA9DF)]),
 ('TaiTham','Noto Sans Tai Tham VF (Lanna, Xishuangbanna Dai)',G+'NotoSansTaiTham[wght].ttf',0,[(0x1A20,0x1AAF)]),
 ('TaiViet','Noto Sans Tai Viet',G+'NotoSansTaiViet-Regular.ttf',0,[(0xAA80,0xAADF)]),
 ('Cham','Noto Sans Cham VF',G+'NotoSansCham[wght].ttf',0,[(0xAA00,0xAA5F)]),
 ('Meetei','Noto Sans Meetei Mayek VF',G+'NotoSansMeeteiMayek[wght].ttf',0,[(0xABC0,0xABFF),(0xAAE0,0xAAFF)]),
 ('Balinese','Noto Sans Balinese VF',G+'NotoSansBalinese[wght].ttf',0,[(0x1B00,0x1B7F)]),
 ('Sundanese','Noto Sans Sundanese VF',G+'NotoSansSundanese[wght].ttf',0,[(0x1B80,0x1BBF),(0x1CC0,0x1CCF)]),
 ('Tifinagh','Noto Sans Tifinagh',G+'NotoSansTifinagh-Regular.ttf',0,[(0x2D30,0x2D7F)]),
 ('Vai','Noto Sans Vai',G+'NotoSansVai-Regular.ttf',0,[(0xA500,0xA63F)]),
 ('Coptic','Noto Sans Coptic',G+'NotoSansCoptic-Regular.ttf',0,[(0x2C80,0x2CFF)]),
 ('Glagolitic','Noto Sans Glagolitic',G+'NotoSansGlagolitic-Regular.ttf',0,[(0x2C00,0x2C5F),(0x1E000,0x1E02F)]),
 ('PhagsPa','Noto Sans PhagsPa',G+'NotoSansPhagsPa-Regular.ttf',0,[(0xA840,0xA87F)]),
 ('Music','Noto Music',G+'NotoMusic-Regular.ttf',0,[(0x1D100,0x1D1FF)]),
 ('Mahjong','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F000,0x1F02F)]),
 ('Cards','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F0A0,0x1F0FF)]),
 ('Domino','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F030,0x1F09F)]),
 ('Chess','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1FA00,0x1FA6F)]),
 ('GeomExt','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F780,0x1F7FF)]),
 ('ArrowsC','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F800,0x1F8FF)]),
 ('Legacy','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1FB00,0x1FBFF)]),
 ('Ornamental','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x1F650,0x1F67F)]),
 ('Alchemical','Apple Symbols',A+'osf/Apple Symbols.ttf',0,[(0x1F700,0x1F77F)]),
 ('CtrlOCR','Noto Sans Symbols 2',A+'gf/NotoSansSymbols2-Regular.ttf',0,[(0x2400,0x245F)]),
 ('CyrExt','Noto Sans VF (Cyrillic Ext-A/B)',A+'gf/NotoSans[wdth,wght].ttf',0,[(0x2DE0,0x2DFF),(0xA640,0xA69F),(0x1C80,0x1C8F)]),
 ('LatinExtE','Noto Sans VF (Latin Ext-E)',A+'gf/NotoSans[wdth,wght].ttf',0,[(0xAB30,0xAB6F)]),
 ('ToneLetters','Noto Sans VF (Modifier Tone Letters, Chinese dialect tones)',A+'gf/NotoSans[wdth,wght].ttf',0,[(0xA700,0xA71F)]),
 ('CDMExt','Noto Sans VF (Combining Diacritical Ext)',A+'gf/NotoSans[wdth,wght].ttf',0,[(0x1AB0,0x1AFF),(0x1DC0,0x1DFF)]),
 ('Hentaigana','Plangothic P2 (Kana Supplement/Ext-A/B)',S+'PlangothicP2-Regular.ttf',0,[(0x1B000,0x1B12F),(0x1AFF0,0x1AFFF),(0x1B130,0x1B16F)]),
 ('HangulJamo','Source Han Sans VF (old Hangul jamo + ljmo/vjmo/tjmo)',A+'../../src/shs/SourceHanSans-VF.ttf',0,[(0x1100,0x11FF),(0xA960,0xA97F),(0xD7B0,0xD7FF)]),
 ('HangulJamoNoFeat','Source Han Sans VF jamo, no composition',A+'../../src/shs/SourceHanSans-VF.ttf',0,[(0x1100,0x11FF),(0xA960,0xA97F),(0xD7B0,0xD7FF)]),
]
out={}
for key,lab,p,i,r in J:
    n=need(*r)
    feats=['ccmp','locl'] if key=='HangulJamoNoFeat' else None
    try:
        have,g=cost(p,sorted(n),i,feats)
    except Exception as e:
        print(key,'ERR',e); continue
    out[key]=dict(label=lab,font=p,idx=i,need=len(n),have=len(have),glyphs=g,cps=sorted(have),missing_in_src=sorted(n-set(have)))
    print(f'{key:16s} need {len(n):4d} have {len(have):4d} glyphs {g:5d}  {lab}',flush=True)
json.dump(out,open('data/script_costs.json','w'))
