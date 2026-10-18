import json, os, sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
W='/workspace/projects/435d098d-7608-493c-a6d9-ceebc965f641/work/'
A=W+'addfont/'
PF=W+'out/PingFang-SF-Medium.ttf'
SIZE=44
_meta={}
def meta(path,idx=0):
    k=(path,idx)
    if k not in _meta:
        t=TTFont(path,fontNumber=idx,lazy=True)
        axes=[(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in t['fvar'].axes] if 'fvar' in t else []
        cm=t.getBestCmap(); gs=t.getGlyphSet(); upm=t['head'].unitsPerEm
        def h(ch):
            from fontTools.pens.boundsPen import BoundsPen
            if ord(ch) not in cm: return None
            p=BoundsPen(gs); gs[cm[ord(ch)]].draw(p); return p.bounds[3]/upm if p.bounds else None
        _meta[k]=dict(axes=axes,cmap=set(cm),cap=h('H'),x=h('x'),cjk=h('国'),upm=upm)
    return _meta[k]
class F:
    """candidate: list of (path,idx,weightclass) statics or a single VF"""
    def __init__(s,label,files,scale_by='em',ref_char=None):
        s.label=label; s.files=files; s.scale_by=scale_by
        m=meta(*files[0][:2]); s.m=m
        s.scale=1.0
        pm=meta(PF)
        if scale_by=='cap' and m['cap']: s.scale=pm['cap']/m['cap']
        if scale_by=='x' and m['x']: s.scale=pm['x']/m['x']
    def font(s,w,size=SIZE):
        if len(s.files)>1:
            p,i,_=min(s.files,key=lambda f:abs(f[2]-w)); m=meta(p,i)
        else: p,i,_=s.files[0]; m=meta(p,i)
        f=ImageFont.truetype(p,round(size*s.scale),index=i,layout_engine=ImageFont.Layout.RAQM)
        if m['axes']:
            vals=[]
            for tag,mn,df,mx in m['axes']:
                if tag=='wght': vals.append(max(mn,min(mx,w)))
                elif tag=='opsz': vals.append(max(mn,min(mx,17 if mx>17 else df)))
                else: vals.append(df)
            f.set_variation_by_axes(vals)
        return f
    def wlabel(s,w):
        if len(s.files)>1: return 'w%d'%min(s.files,key=lambda f:abs(f[2]-w))[2]
        m=s.m
        for tag,mn,df,mx in m['axes']:
            if tag=='wght': return 'w%g'%max(mn,min(mx,w))
        return 'static'
def pf(w,size=SIZE):
    f=ImageFont.truetype(PF,size,layout_engine=ImageFont.Layout.RAQM); f.set_variation_by_axes([w,100]); return f
def runs(text,cand):
    pm=meta(PF)['cmap']; out=[]
    for ch in text:
        use_c = ord(ch) not in pm and ord(ch) in cand.m['cmap']
        if ch==' ' and out: use_c=out[-1][1]
        if out and out[-1][1]==use_c: out[-1][0]+=ch
        else: out.append([ch,use_c])
    return out
def sheet(name,title,cands,lines,weights=(100,400,700,900),size=SIZE,width=2000,dir=None):
    rowh=int(size*1.9); lab=360
    H=200+len(cands)*(len(weights)*len(lines)*rowh+60)
    img=Image.new('RGB',(width,H),'white'); d=ImageDraw.Draw(img)
    small=pf(500,22); big=pf(700,30)
    d.text((20,25),title,font=big,fill='black')
    y=90
    for c in cands:
        d.text((20,y),f"{c.label}   (scale ×{c.scale:.2f} by {c.scale_by})",font=pf(600,24),fill=(20,60,160)); y+=40
        for w in weights:
            for ln in lines:
                x=lab; base=y+int(size*1.25)
                d.text((20,base-24),f"PF wght {w} | cand {c.wlabel(w)}",font=small,fill=(110,110,110))
                for txt,isc in runs(ln,c):
                    f=c.font(w,size) if isc else pf(w,size)
                    try: d.text((x,base),txt,font=f,fill=(180,0,0) if isc and False else 'black',anchor='ls',direction=dir)
                    except Exception as e: d.text((x,base),txt,font=f,fill='black',anchor='ls')
                    x+=d.textlength(txt,font=f,direction=dir) if dir else d.textlength(txt,font=f)
                y+=rowh
        d.line((20,y+5,width-20,y+5),fill=(220,220,220)); y+=10
    img=img.crop((0,0,width,y+20))
    img.save(A+'render/'+name+'.png'); print('saved',name, img.size)
