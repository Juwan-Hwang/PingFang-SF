import csv, collections, json
from fontTools.ttLib import TTFont
f=TTFont('../out/PingFang-SF-Medium.ttf',lazy=True); cps=set(f.getBestCmap())
def dbcs(codec, lead, trail):
    s=set()
    for a in lead:
        for b in trail:
            try: t=bytes([a,b]).decode(codec)
            except: continue
            for ch in t: s.add(ord(ch))
    return s
def rep(name, s):
    s={c for c in s if c>0x7f}
    m=sorted(s-cps); print(f'{name}: {len(s)} chars, missing {len(m)}', ' '.join(chr(c) for c in m[:60]), '...' if len(m)>60 else '')
    return m
R=range(0x81,0xFF); T=range(0x40,0xFF)
out={}
out['GB2312']=rep('GB2312', dbcs('gb2312',range(0xA1,0xFF),range(0xA1,0xFF)))
out['GBK']=rep('GBK', dbcs('gbk',R,T))
out['Big5']=rep('Big5(cp950)', dbcs('cp950',R,T))
hk=dbcs('big5hkscs',R,T)
out['HKSCS']=rep('Big5-HKSCS-2004 (python)', hk)
hkB=[c for c in out['HKSCS'] if c>=0x20000]; print('  HKSCS missing in SIP:',len(hkB),' BMP:',len(out['HKSCS'])-len(hkB))
out['JIS2004']=rep('JIS X 0213:2004 (euc_jis_2004)', dbcs('euc_jis_2004',range(0xA1,0xFF),range(0xA1,0xFF))|{ord(ch) for a in range(0xA1,0xFF) for b in range(0xA1,0xFF) for ch in (lambda x: x)( (lambda bb: (bb.decode('euc_jis_2004','ignore')))(bytes([0x8F,a,b])) )})
out['KSX1001']=rep('KS X 1001 (euc_kr)', dbcs('euc_kr',range(0xA1,0xFF),range(0xA1,0xFF)))
ksh=[c for c in out['KSX1001'] if 0xAC00<=c<=0xD7A3]; print('  of which hangul syllables', len(ksh))
# GB18030 BMP: all BMP decodable except surrogates/pua
import unicodedata
def blk(a,b): return {c for c in range(a,b+1)}
U='ucd/'
gc={}
first=None
for line in open(U+'UnicodeData.txt'):
    p=line.split(';'); cp=int(p[0],16)
    if p[1].endswith(', First>'): first=cp; continue
    if p[1].endswith(', Last>'):
        for c in range(first,cp+1): gc[c]=p[2]
        continue
    gc[cp]=p[2]
def assigned(a,b): return {c for c in range(a,b+1) if c in gc and gc[c] not in ('Cs','Co','Cc')}
sets={
 'URO 4E00-9FFF':assigned(0x4E00,0x9FFF),'ExtA':assigned(0x3400,0x4DBF),'ExtB':assigned(0x20000,0x2A6DF),
 'ExtC':assigned(0x2A700,0x2B73F),'ExtD':assigned(0x2B740,0x2B81F),'ExtE':assigned(0x2B820,0x2CEAF),'ExtF':assigned(0x2CEB0,0x2EBEF),'ExtI':assigned(0x2EBF0,0x2EE5F),
 'ExtG':assigned(0x30000,0x3134F),'ExtH':assigned(0x31350,0x323AF),'ExtJ':assigned(0x323B0,0x3347F),
 'Kana':assigned(0x3040,0x30FF)|assigned(0x31F0,0x31FF),'Kana Supp/ExtA/B/Small':assigned(0x1AFF0,0x1B16F),
 'Hangul syllables':assigned(0xAC00,0xD7AF),'Hangul Jamo':assigned(0x1100,0x11FF),'Hangul compat jamo':assigned(0x3130,0x318F),
 'Emoji-ish 1F300-1FAFF':assigned(0x1F300,0x1FAFF),'Currency 20A0':assigned(0x20A0,0x20CF),
 'Combining diacritics 0300':assigned(0x0300,0x036F),'Latin Ext Additional (Vietnamese)':assigned(0x1E00,0x1EFF),
 'Thai':assigned(0xE00,0xE7F),'Lao':assigned(0xE80,0xEFF),'Khmer':assigned(0x1780,0x17FF),'Myanmar':assigned(0x1000,0x109F),'Tibetan':assigned(0xF00,0xFFF),
 'Mongolian':assigned(0x1800,0x18AF),'Arabic':assigned(0x600,0x6FF),'Hebrew':assigned(0x590,0x5FF),'Armenian':assigned(0x530,0x58F),'Georgian':assigned(0x10A0,0x10FF),
 'Ethiopic':assigned(0x1200,0x139F),'Bengali':assigned(0x980,0x9FF),'Tamil':assigned(0xB80,0xBFF),'Telugu':assigned(0xC00,0xC7F),'Kannada':assigned(0xC80,0xCFF),'Malayalam':assigned(0xD00,0xD7F),'Sinhala':assigned(0xD80,0xDFF),'Oriya':assigned(0xB00,0xB7F),
 'Yi':assigned(0xA000,0xA4CF),'Bopomofo+Ext':assigned(0x3100,0x312F)|assigned(0x31A0,0x31BF),'Kangxi radicals+supp':assigned(0x2E80,0x2FDF),'CJK strokes':assigned(0x31C0,0x31EF),
 'Enclosed CJK':assigned(0x3200,0x32FF),'CJK compat 3300':assigned(0x3300,0x33FF),'Enclosed Alnum':assigned(0x2460,0x24FF),'Enclosed Alnum Supp':assigned(0x1F100,0x1F1FF),'Enclosed Ideo Supp':assigned(0x1F200,0x1F2FF),
 'Box drawing/blocks':assigned(0x2500,0x259F),'Arrows':assigned(0x2190,0x21FF),'Math operators':assigned(0x2200,0x22FF),'Misc Technical':assigned(0x2300,0x23FF),'Geometric shapes':assigned(0x25A0,0x25FF),'Misc symbols':assigned(0x2600,0x26FF),'Dingbats':assigned(0x2700,0x27BF),
 'General Punct':assigned(0x2000,0x206F),'CJK Sym Punct':assigned(0x3000,0x303F),'Half/Fullwidth':assigned(0xFF00,0xFFEF),'IPA':assigned(0x250,0x2AF),'Spacing modifiers':assigned(0x2B0,0x2FF),
 'Symbols for Legacy Computing':assigned(0x1FB00,0x1FBFF),'Math alnum':assigned(0x1D400,0x1D7FF),'Musical':assigned(0x1D100,0x1D1FF),'Tai Le/NewTaiLue/Lisu/Miao/Nüshu':assigned(0x1950,0x19DF)|assigned(0xA4D0,0xA4FF)|assigned(0x16F00,0x16F9F)|assigned(0x1B170,0x1B2FF),
 'Tangut':assigned(0x17000,0x18AFF)|assigned(0x18D00,0x18D8F),'Khitan':assigned(0x18B00,0x18CFF),'Braille':assigned(0x2800,0x28FF),'Variation selectors':assigned(0xFE00,0xFE0F)|assigned(0xE0100,0xE01EF),
}
rows=[]
for k,s in sets.items():
    m=s-cps; rows.append((k,len(s),len(s)-len(m),len(m)))
    print(f'{k:40s} assigned {len(s):6d} covered {len(s)-len(m):6d} missing {len(m):6d}', (' e.g. '+' '.join(chr(c) for c in sorted(m)[:20])) if 0<len(m)<=400 else '')
json.dump({k:[hex(c) for c in v] for k,v in out.items()}, open('charset_missing.json','w'))
for c in (0x20C0,0x20C1,0x20BF,0x20BE,0x2E3A,0x2E3B,0x3007,0x303E,0x30FF,0x2FFC,0x31E4,0x31E5,0x31EF,0x9FFF,0x9FEA,0x2B73A,0x2EBF0,0x1F6DC):
    print('U+%04X'%c, gc.get(c), 'Y' if c in cps else 'MISSING')
