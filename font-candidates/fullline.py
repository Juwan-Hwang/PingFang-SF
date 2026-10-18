import sys; sys.path.insert(0,'.')
from render import *
S=A+'src/'
def fl(name,title,rows,weights=(100,400,700,900),size=44):
    img=Image.new('RGB',(1800,200+len(rows)*len(weights)*80),'white'); d=ImageDraw.Draw(img)
    d.text((20,25),title,font=pf(700,26),fill='black'); y=80
    for label,cand,text in rows:
        d.text((20,y),label,font=pf(600,24),fill=(20,60,160)); y+=40
        for w in weights:
            f=pf(w,size) if cand is None else cand.font(w,size)
            d.text((20,y+50),f'w{w} '+('' if cand is None else cand.wlabel(w)),font=pf(500,20),fill=(110,110,110))
            d.text((250,y+52),text,font=f,fill='black',anchor='ls'); y+=72
    img.crop((0,0,1800,y+20)).save(A+'render/'+name+'.png'); print(name)
ar='العربية ڃڊڱ ݐݑ ٲ ࢠ ۝ كتاب'
fl('arabic_fullline','Arabic: whole line in each font (PF row = existing MiSans Arabic; missing letters show as tofu there)',
  [('PingFang SF (existing MiSans Arabic)',None,ar),('SF Arabic VF',F('',[(S+'apple/SF-Arabic/SF-Arabic.ttf',0,0)]),ar),('Noto Sans Arabic VF',F('',[(S+'gf/NotoSansArabic[wdth,wght].ttf',0,0)]),ar)])
my='မြန်မာစာ ၵႂၢမ်းတႆး ၸၢႆး'
fl('myanmar_fullline','Myanmar: whole line (PF row = existing MiSans Myanmar; Shan letters tofu there)',
  [('PingFang SF (existing MiSans Myanmar)',None,my),('Noto Sans Myanmar VF',F('',[(S+'gf/NotoSansMyanmar[wdth,wght].ttf',0,0)]),my)])
