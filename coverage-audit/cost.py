from fontTools.ttLib import TTFont
from fontTools import subset
f=TTFont('../out/PingFang-SF-Medium.ttf'); cmap=f.getBestCmap(); allc=set(cmap)
def closure(cps):
    o=subset.Options(); o.layout_features=['*']; o.notdef_outline=True; o.glyph_names=True
    s=subset.Subsetter(o); s.populate(unicodes=list(cps)); s._prune_pre_subset(f); s._closure_glyphs(f); return len(s.glyphs_retained)
base=closure(allc)
R={'Indic (Deva/Guru/Gujr)':[(0x900,0xAFF),(0xA8E0,0xA8FF)],'Arabic all':[(0x600,0x8FF),(0xFB50,0xFDFF),(0xFE70,0xFEFF)],'Thai+Lao':[(0xE00,0xEFF)],'Tibetan':[(0xF00,0xFFF)],'Myanmar':[(0x1000,0x109F)],'Khmer':[(0x1780,0x17FF),(0x19E0,0x19FF)],'Hebrew+AlphaPres':[(0x590,0x5FF),(0xFB1D,0xFB4F)],'Braille':[(0x2800,0x28FF)],'Greek Ext':[(0x1F00,0x1FFF)],'CJK Ext B..J':[(0x20000,0x3347F)],'CJK compat supp':[(0x2F800,0x2FA1F)],'Singletons Runic/Duployan/Sutton':[(0x16A0,0x16FF),(0x1BC00,0x1BCAF),(0x1D800,0x1DAAF)]}
for k,rs in R.items():
    sub={c for c in allc if not any(a<=c<=b for a,b in rs)}
    print(k, 'cps',len(allc)-len(sub),'glyphs freed if removed', base-closure(sub), flush=True)
