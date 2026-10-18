import uharfbuzz as hb, json
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
P="PingFang-SF Medium.ttf"
tt=TTFont(P,lazy=True); gdef=tt['GDEF'].table.GlyphClassDef.classDefs; order=tt.getGlyphOrder()
blob=hb.Blob.from_file_path(P); face=hb.Face(blob); font=hb.Font(face)
def shape(t,w=500,feat=None,nodc=False,props=None):
    font.set_variations({"wght":w})
    b=hb.Buffer(); b.add_str(t); b.guess_segment_properties()
    if nodc: b.flags=hb.BufferFlags.DO_NOT_INSERT_DOTTED_CIRCLE
    hb.shape(font,b,feat or {})
    out=[];x=0
    for i,p in zip(b.glyph_infos,b.glyph_positions):
        pen=SVGPathPen(None); font.draw_glyph_with_pen(i.codepoint,pen)
        out.append(dict(d=pen.getCommands(),x=x+p.x_offset,y=p.y_offset,adv=p.x_advance,cl=i.cluster,
                        cls=gdef.get(order[i.codepoint],0),g=order[i.codepoint]))
        x+=p.x_advance
    return dict(glyphs=out,width=x)
D={}
for w in (100,500,900):
    D[f"AV_k{w}"]=shape("AV",w); D[f"AV_n{w}"]=shape("AV",w,{"kern":False})
    D[f"To_k{w}"]=shape("To",w); D[f"To_n{w}"]=shape("To",w,{"kern":False})
D["beh_iso"]=[shape("ب",600) for _ in range(3)]
D["beh_join"]=shape("ببب",600)
D["bism"]=shape("بِسْمِ اللَّهِ",600)
D["ka"]=shape("क",600); D["vir"]=shape("्",600,nodc=True); D["ssa"]=shape("ष",600)
D["kssa"]=shape("क्ष",600)
D["thai"]=shape("ญี่ปุ่น",600)
D["tib"]=shape("བསྒྲུབས",600)
for k in ("bism","kssa","thai","tib","beh_join","vir"):
    print(k,[(g['g'],g['cls'],g['cl'],g['x'],g['y']) for g in D[k]['glyphs']])
json.dump(D,open("glyphs.json","w"))
D["sep"]=None
for k,v in list(D.items()):
    if v is None: del D[k]
import math
open("glyphs.js","w").write("window.GLY="+json.dumps(D)+";")

# v1.2 additions
pen=SVGPathPen(None); font.set_variations({"wght":500}); font.draw_glyph_with_pen(0,pen)
D2=json.load(open("glyphs.json")); D2["notdef"]=dict(d=pen.getCommands(),adv=font.get_glyph_h_advance(0))
open("glyphs.js","w").write("window.GLY="+json.dumps(D2)+";")
