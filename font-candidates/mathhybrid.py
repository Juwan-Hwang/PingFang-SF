import sys, unicodedata
sys.path.insert(0,'.')
from render import *
S=A+'src/'
SFP=W+'src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf'; SFI=W+'src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro-Italic.ttf'
NY=S+'apple/NY/NewYork.ttf'; NYI=S+'apple/NY/NewYorkItalic.ttf'; MONO=S+'osf/SFNSMono.ttf'; STIX=S+'osf/STIXTwoMath.otf'
def vf(path,size,w):
    f=ImageFont.truetype(path,size,layout_engine=ImageFont.Layout.RAQM); m=meta(path)
    vals=[]
    for tag,mn,df,mx in m['axes']:
        vals.append(max(mn,min(mx,w)) if tag in('wght','YAXS') else (17 if tag=='opsz' and mn<=17<=mx else df))
    if vals: f.set_variation_by_axes(vals)
    return f
def route(ch,w,size):
    n=unicodedata.name(ch,'')
    if not n.startswith('MATHEMATICAL'): return ch,pf(w,size)
    parts=n.split()
    base=None
    if 'CAPITAL' in parts: base=parts[-1]
    elif 'SMALL' in parts: base=parts[-1].lower()
    elif 'DIGIT' in parts: base=str(['ZERO','ONE','TWO','THREE','FOUR','FIVE','SIX','SEVEN','EIGHT','NINE'].index(parts[-1]))
    if base is None or len(base)!=1:  # greek etc
        return ch,ImageFont.truetype(STIX,size)
    bold='BOLD' in parts; ital='ITALIC' in parts; b=min(w+300,1000) if bold else w
    sc=meta(PF)['cap']
    if 'SCRIPT' in parts or 'FRAKTUR' in parts or 'DOUBLE-STRUCK' in parts:
        return ch,ImageFont.truetype(STIX,round(size*sc/meta(STIX)['cap']))
    if 'MONOSPACE' in parts: return base,vf(MONO,round(size*sc/meta(MONO)['cap']),max(w,300))
    if 'SANS-SERIF' in parts: return base,vf(SFI if ital else SFP,round(size*sc/meta(SFP)['cap']),b)
    p=NYI if ital else NY
    return base,vf(p,round(size*sc/meta(p)['cap']),max(400,b if bold else w))
lines=['𝐇𝐞𝐥𝐥𝐨 𝑯𝒆𝒍𝒍𝒐 𝐻𝑒𝑙𝑙𝑜 𝓗𝓮𝓵𝓵𝓸 𝔥𝔢𝔩𝔩𝔬 ℍ𝕖𝕝𝕝𝕠 你好','𝖧𝖾𝗅𝗅𝗈 𝗛𝗲𝗹𝗹𝗼 𝘏𝘦𝘭𝘭𝘰 𝙃𝙚𝙡𝙡𝙤 𝙷𝚎𝚕𝚕𝚘 𝟏𝟐𝟑 𝟭𝟮𝟯 Hello']
size=44; img=Image.new('RGB',(2000,1100),'white'); d=ImageDraw.Draw(img)
d.text((20,25),'P4 Math alphanumerics — Apple hybrid preview: serif=New York VF, sans=SF Pro VF (bold = base+300), mono=SF Mono VF, script/fraktur/double-struck=STIX Two Math',font=pf(700,24),fill='black')
y=90
for w in (100,400,700,900):
    for ln in lines:
        x=360; base=y+55
        d.text((20,base-24),f'PF wght {w}',font=pf(500,22),fill=(110,110,110))
        for ch in ln:
            t,f=route(ch,w,size); d.text((x,base),t,font=f,fill='black',anchor='ls'); x+=d.textlength(t,font=f)
        y+=82
img.crop((0,0,2000,y+20)).save(A+'render/mathalnum_apple_hybrid.png'); print('ok')
