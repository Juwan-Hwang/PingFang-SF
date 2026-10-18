import re
from fontTools.ttLib import TTFont
f=TTFont('../out/PingFang-SF-Medium.ttf',lazy=True); cps=set(f.getBestCmap())
t=[int(l.split('\t')[1],16) for l in open('ucd/tygf.txt',encoding='utf-8-sig') if '\t' in l and not l.startswith('#')]
m=[c for c in t if c not in cps]; print('通用规范', len(t), 'nonBMP', sum(c>0xFFFF for c in t), 'missing', len(m), ''.join(map(chr,m)))
ep=set()
for l in open('ucd/emoji-data.txt'):
    mm=re.match(r'([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*; Emoji_Presentation',l)
    if mm:
        a=int(mm[1],16); b=int(mm[2] or mm[1],16); ep.update(range(a,b+1))
inter=sorted(ep&cps); print('Emoji_Presentation chars present in font', len(inter), ''.join(map(chr,inter)))
ug='ئابپتجچخدرزژسشغفقكگڭلمنھوۇۆۈۋېىيەۉ،؛؟ـ'
print('Uyghur missing', [c for c in ug if ord(c) not in cps])
fa='آأإةپچژکگیۀ'; print('Persian/Urdu misc missing',[c for c in fa+'ٹڈڑںہےۓ' if ord(c) not in cps])
py='āáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜüêńňǹḿ'; print('pinyin missing',[c for c in py+'ê̄ế̌ề' if ord(c) not in cps])
for c in [0x0304,0x0301,0x030C,0x0300,0x0308,0x2E80,0x3000,0x2014,0x2E3A,0x00A0,0x200B,0x200C,0x200D,0xFEFF,0x2060,0x00AD,0x034F,0x180E,0xFE0E,0xFE0F,0x3164,0xFFA0,0x115F,0x1160,0x2028,0x2029,0x061C,0x200E,0x200F,0x202A,0x202E,0x2066,0x2069,0xE0001,0xE0020,0x1F3FB,0x20E3,0x20E0,0x20DD,0x2028]:
    print('U+%04X'%c, 'Y' if c in cps else 'MISSING', end='; ')
print()
# vertical forms, compat forms, small forms
for nm,(a,b) in {'Vertical Forms':(0xFE10,0xFE1F),'CJK Compat Forms':(0xFE30,0xFE4F),'Small Form Variants':(0xFE50,0xFE6F),'Ideographic Description':(0x2FF0,0x2FFF),'Kanbun':(0x3190,0x319F),'Ideo Sym & Punct 16FE0':(0x16FE0,0x16FFF),'Counting rods':(0x1D360,0x1D37F),'Tai Xuan Jing':(0x1D300,0x1D35F),'Yijing hexagram':(0x4DC0,0x4DFF),'Mahjong/Domino/Cards':(0x1F000,0x1F0FF),'Supp Arrows-C':(0x1F800,0x1F8FF),'Geometric Ext':(0x1F780,0x1F7FF),'Misc Sym Arrows':(0x2B00,0x2BFF),'Supp Punct':(0x2E00,0x2E7F),'Latin Ext-B':(0x180,0x24F),'Latin Ext-D':(0xA720,0xA7FF),'Latin Ext-E':(0xAB30,0xAB6F),'Phonetic Ext':(0x1D00,0x1D7F),'Cyrillic Ext-B':(0xA640,0xA69F),'Greek Ext':(0x1F00,0x1FFF),'Letterlike':(0x2100,0x214F),'Number Forms':(0x2150,0x218F),'Supp Math Ops':(0x2A00,0x2AFF),'Misc Math Sym-A/B':(0x27C0,0x27EF)}.items():
    print(nm, sum(1 for c in range(a,b+1) if c in cps),'/',b-a+1)
