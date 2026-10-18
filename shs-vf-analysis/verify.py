import uharfbuzz as hb, random
from fontTools.ttLib import TTFont
N='out/step7.ttf'; S='../src/shs/SourceHanSans-VF.ttf'; O='../out/PingFang-SF-Medium.ttf'
def hbf(p,loc):
    f=hb.Font(hb.Face(hb.Blob.from_file_path(p))); f.set_variations(loc); return f
T={100:-0.063,400:0.519-0.3*(0.519+0.063),500:0.519,700:0.519+0.4*(0.985-0.519),900:0.985}
# SHS user weight for a given t: invert SHS avar
st=TTFont(S,lazy=True); seg=st['avar'].segments['wght']; ks=sorted(seg.items())
def t2user(t):
    t=max(0,min(1,t))
    for (a,b),(c,d) in zip(ks,ks[1:]):
        if b<=t<=d: n=a+(t-b)*(c-a)/(d-b); return 250+n*650
rows=[l.rstrip('\n').split('\t') for l in open('../PingFang-SF/build/data/shs_vf_glyphs.tsv',encoding='utf-8') if not l.startswith('#')]
random.seed(0); samp=random.sample(rows,60)+[r for r in rows if r[4]=='prop']
worst={}
for w,t in T.items():
    fn=hbf(N,{'wght':w,'wdth':100}); fo=hbf(O,{'wght':w,'wdth':100})
    if t<0: continue  # extrapolated: no SHS instance to compare against
    fs=hbf(S,{'wght':t2user(t)})
    m=0; ma=0
    for r in samp:
        cp=int(r[0][2:],16)
        gn=fn.get_nominal_glyph(cp); gs=fs.get_nominal_glyph(cp)
        if r[3]!='JAN': continue
        en=fn.get_glyph_extents(gn); es=fs.get_glyph_extents(gs)
        d=max(abs(a-b) for a,b in zip((en.x_bearing,en.y_bearing,en.width,en.height),(es.x_bearing,es.y_bearing,es.width,es.height)))
        m=max(m,d)
        if r[4]=='prop':
            ma=max(ma,abs(fn.get_glyph_h_advance(gn)-fs.get_glyph_h_advance(gs)))
        else:
            assert fn.get_glyph_h_advance(gn)==fo.get_glyph_h_advance(fo.get_nominal_glyph(cp)), r
    worst[w]=(round(t,3),round(t2user(t)),m,ma)
print('wght: (t, SHS user wght, max extents dev vs SHS instance, max adv dev prop)',worst)
for r in rows:
    if r[4]=='prop':
        cp=int(r[0][2:],16)
        print(r[0],chr(cp),[ (w,hbf(N,{'wght':w,'wdth':100}).get_glyph_h_advance(hbf(N,{'wght':w}).get_nominal_glyph(cp))) for w in (100,500,900)], 'v1.1.1', hbf(O,{'wght':500}).get_glyph_h_advance(hbf(O,{}).get_nominal_glyph(cp)))
# wdth axis: replaced glyphs must not change with wdth
fa=hbf(N,{'wght':700,'wdth':80}); fb=hbf(N,{'wght':700,'wdth':120})
bad=[r[0] for r in rows if fa.get_glyph_extents(fa.get_nominal_glyph(int(r[0][2:],16)))!=fb.get_glyph_extents(fb.get_nominal_glyph(int(r[0][2:],16)))]
print('wdth-dependent replaced glyphs:',len(bad))
