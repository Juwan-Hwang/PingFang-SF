import numpy as np, freetype
from fontTools.ttLib import TTFont
PX=1000
def prof(face,gid,coords,axis,frac=0.5):
    face.set_var_design_coords(coords); face.set_char_size(PX*64,0,72,72)
    face.load_glyph(gid, freetype.FT_LOAD_NO_BITMAP|freetype.FT_LOAD_NO_HINTING); face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
    b=face.glyph.bitmap; a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]/255.0
    line=a[:, int(a.shape[1]*frac)] if axis=='h' else a[int(a.shape[0]*frac),:]
    runs=np.diff(np.concatenate([[0],(line>0.5).astype(int),[0]])); n=(runs==1).sum()
    return line.sum()/max(n,1)
if __name__=='__main__':
    O='../out/PingFang-SF-Medium.ttf'; S='../src/shs/SourceHanSans-VF.ttf'
    fo=freetype.Face(O); fs=freetype.Face(S); to=TTFont(O,lazy=True); ts=TTFont(S,lazy=True); co=to.getBestCmap(); cs=ts.getBestCmap()
    tests=[(0x4E00,'h',.5),(0x4E09,'h',.5),(0x5DDD,'v',.5),(0x4E28,'v',.5),(0x5DE5,'h',.3),(0x76EE,'v',.5),(0x4E8C,'h',.5)]
    T={}
    for c,ax,fr in tests:
        el=prof(fs,ts.getGlyphID(cs[c]),(250,),ax,fr); hv=prof(fs,ts.getGlyphID(cs[c]),(900,),ax,fr)
        m5=prof(fs,ts.getGlyphID(cs[c]),(500,),ax,fr)
        row=[]
        for w in range(100,901,100):
            s=prof(fo,to.getGlyphID(co[c]),(w,100),ax,fr); row.append(round((s-el)/(hv-el),3))
        T[c]=row; print(chr(c),ax,'EL',round(el,1),'H',round(hv,1),'t500shs',round((m5-el)/(hv-el),3),row)
    print('mean',np.round(np.mean(list(T.values()),axis=0),3))
    print('median',np.round(np.median(list(T.values()),axis=0),3))
