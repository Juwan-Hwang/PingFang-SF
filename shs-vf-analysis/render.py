import sys
from PIL import Image, ImageDraw, ImageFont
OLD='../out/PingFang-SF-Medium.ttf'; NEW=sys.argv[1] if len(sys.argv)>1 else 'out/final.ttf'
OUT='../render_sh/'
rows=[l.rstrip('\n').split('\t') for l in open('../PingFang-SF/build/data/shs_vf_glyphs.tsv',encoding='utf-8') if not l.startswith('#')]
chars=[chr(int(r[0][2:],16)) for r in rows]
LAB=ImageFont.truetype(OLD,18); LAB.set_variation_by_axes([500,100])
W=(100,400,700,900)
def font(path,w,size):
    f=ImageFont.truetype(path,size); f.set_variation_by_axes([w,100]); return f
def sheet(name, lines, size=44, gap=14):
    # lines: list of text; rendered for each weight, old vs new
    H=0; blocks=[]
    width=max(len(t) for t in lines)*size+260
    img=Image.new("L",(width, (len(lines)*2*(size+gap)+60)*len(W)+40),255); d=ImageDraw.Draw(img); y=10
    for w in W:
        d.text((10,y),'wght %d'%w,font=LAB,fill=0); y+=30
        for t in lines:
            for lab,p in (('v1.1.1',OLD),('sh-vf',NEW)):
                d.text((10,y+size//3),lab,font=LAB,fill=110)
                d.text((110,y),t,font=font(p,w,size),fill=0); y+=size+gap
        y+=10; d.line((0,y,width,y),fill=180); y+=10
    img=img.crop((0,0,width,y)); img.save(OUT+name); print(name,img.size)
# 1. kana / symbols mixed with PingFang ideographs (PingFang neighbours: 東京 春 日本語 漢字 口)
sheet('mix_kana.png',['東京の春は美しい。ひらがなとカタカナ、漢字が混ざる文章。',
                      '口あ口ア口ん口ン口ゃ口ヴ口ㇰ口ㆠ口〆口〻口〼口ゟ口ヿ口'])
sheet('mix_symbols.png',['口㈱口㍿口㎏口㎡口㋐口㉑口㊙口㏍口㌔口⁉口🄰口🅐口',
                         '口㇀口㇁口㇂口㇃口㇄口〠口ㆴ口ㆵ口⺀口㉇口㈠口㊀口'])
# 2. Ext-B+ ideographs taken from SHS next to PingFang ideographs
ext=[c for c in chars if ord(c)>=0x20000]
sheet('mix_extB.png',['永'+'永'.join(ext[:16])+'永','漢'+'漢'.join(ext[16:32])+'漢'])
# 3. all affected chars, one sheet per weight (new font only), plus old at 500 for reference
def grid(name,path,w,size=40,per=38):
    n=len(chars); r=(n+per-1)//per
    img=Image.new('L',(per*(size+6)+20, r*(size+14)+50),255); d=ImageDraw.Draw(img)
    d.text((10,8),'%s  wght %d  (%d glyphs)'%(name,w,n),font=LAB,fill=0); f=font(path,w,size)
    for i,c in enumerate(chars):
        d.text((10+(i%per)*(size+6), 40+(i//per)*(size+14)), c, font=f, fill=0)
    img.save(OUT+'all_%s_w%d.png'%(name,w)); print('all',name,w,img.size)
for w in W: grid('new',NEW,w)
grid('old',OLD,500)
