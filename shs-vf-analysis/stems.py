import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.basePen import BasePen
import freetype
PX=1000
def stem(face, gid, coords, axis):
    face.set_var_design_coords(coords)
    face.set_char_size(PX*64,0,72,72)
    face.load_glyph(gid, freetype.FT_LOAD_NO_BITMAP|freetype.FT_LOAD_NO_HINTING)
    face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    b=face.glyph.bitmap; a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]/255.0
    if axis=='h': col=a[:, a.shape[1]//2]; return col.sum()   # thickness of horizontal stroke
    else: row=a[a.shape[0]//2,:]; return row.sum()
O='../out/PingFang-SF-Medium.ttf'; S='../src/shs/SourceHanSans-VF.ttf'
fo=freetype.Face(O); fs=freetype.Face(S)
to=TTFont(O,lazy=True); ts=TTFont(S,lazy=True)
co=to.getBestCmap(); cs=ts.getBestCmap()
chars=[(0x4E00,'h'),(0x4E28,'v')]
for c,ax in chars:
    print(chr(c),'ours',[ (w,round(stem(fo,to.getGlyphID(co[c]),(w,100),ax),1)) for w in range(100,901,100)])
    print(chr(c),'shs',[ (w,round(stem(fs,ts.getGlyphID(cs[c]),(w,),ax),1)) for w in range(250,901,50)])
