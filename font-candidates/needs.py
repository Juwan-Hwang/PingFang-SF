import json
from fontTools.ttLib import TTFont
W='/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/'
have=set(TTFont(W+'out/PingFang-SF-Medium.ttf',lazy=True).getBestCmap())
assigned={}
for l in open(W+'audit/ucd/UnicodeData.txt'):
    f=l.split(';'); assigned[int(f[0],16)]=f[2]
# expand ranges
rng=[];prev=None
for l in open(W+'audit/ucd/UnicodeData.txt'):
    f=l.split(';')
    if f[1].endswith('First>'): prev=int(f[0],16)
    elif f[1].endswith('Last>'):
        for c in range(prev,int(f[0],16)+1): assigned[c]=f[2]
emoji=set()
for l in open(W+'audit/ucd/emoji-data.txt'):
    l=l.split('#')[0].strip()
    if not l: continue
    r,p=[x.strip() for x in l.split(';')]
    if p!='Emoji_Presentation': continue
    a,_,b=r.partition('..'); b=b or a
    emoji|=set(range(int(a,16),int(b,16)+1))
def blk(*rs):
    s=set()
    for a,b in rs: s|={c for c in range(a,b+1) if c in assigned and assigned[c] not in('Cc','Cs','Co')}
    return sorted(s-have-emoji)
ks=[]
for b1 in range(0xb0,0xc9):
    for b2 in range(0xa1,0xff):
        try: ks.append(ord(bytes([b1,b2]).decode('euc-kr')))
        except: pass
N={
'P1_hangul': sorted((set(ks)|set(range(0x3131,0x318F))|set(blk((0x3200,0x321E),(0x3260,0x327F))))-have),
'P2_symbols': blk((0x4DC0,0x4DFF),(0x1D300,0x1D35F),(0x1D360,0x1D37F),(0x2E00,0x2E7F),(0x2B00,0x2BFF),(0x27C0,0x27EF),(0x2980,0x29FF),(0x1F100,0x1F1FF),(0x16FE0,0x16FFF),(0x1F260,0x1F265),(0x2400,0x243F),(0x23FF,0x23FF)),
'P3_mongolian': blk((0x1800,0x18AF),(0x11660,0x1167F)),
'P3_yi': blk((0xA000,0xA4CF)),
'P3_lisu': blk((0xA4D0,0xA4FF),(0x11FB0,0x11FBF)),
'P3_newtailue': blk((0x1980,0x19DF)),
'P3_taile': blk((0x1950,0x197F)),
'P3_miao': blk((0x16F00,0x16F9F)),
'P3_nushu': blk((0x1B170,0x1B2FF)),
'P4_mathalnum': blk((0x1D400,0x1D7FF)),
'P4_latinextd': blk((0xA720,0xA7FF)),
'P4_arabic': blk((0x0600,0x06FF),(0x0750,0x077F),(0x0870,0x089F),(0x08A0,0x08FF),(0xFB50,0xFDFF),(0xFE70,0xFEFF),(0x10EC0,0x10EFF)),
'P4_myanmar': blk((0x1000,0x109F),(0xAA60,0xAA7F),(0xA9E0,0xA9FF),(0x116D0,0x116FF)),
}
for k,v in N.items(): print(k,len(v))
json.dump(N,open('needs.json','w'))
