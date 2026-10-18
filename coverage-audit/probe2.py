import collections
from fontTools.ttLib import TTFont
from fontTools import subset
f=TTFont('../out/PingFang-SF-Medium.ttf'); cmap=f.getBestCmap(); glyf=f['glyf']
rev=collections.defaultdict(list)
for c,g in cmap.items(): rev[g].append(c)
orph=open('orphans.txt').read().split()
base=collections.Counter()
for g in orph:
    gg=glyf[g]
    if gg.isComposite():
        for c in gg.components:
            for cp in rev.get(c.glyphName,[])[:1]: base['%04X %s'%(cp,chr(cp))]+=1
print('orphan composite component bases', base.most_common(40))
gid={g:i for i,g in enumerate(f.getGlyphOrder())}
print('first cmapped glyph gid near orphan start:', [(i, ['%04X'%c for c in rev[g]][:3]) for g,i in gid.items() if 35380<i<35402 and g in rev][:10])
def closure(cps):
    o=subset.Options(); o.layout_features=['*']; o.notdef_outline=True; o.glyph_names=True
    s=subset.Subsetter(o); s.populate(unicodes=cps); s._prune_pre_subset(f); s._closure_glyphs(f); return len(s.glyphs_retained)
pua=lambda c: 0xE000<=c<=0xF8FF or c>=0xF0000
allc=list(cmap)
n=f['maxp'].numGlyphs
a=closure(allc); b=closure([c for c in allc if not pua(c)]); c=closure([c for c in allc if not pua(c) or c==0xF8FF])
print('numGlyphs',n,'closure all',a,'no PUA',b,'no PUA but keep F8FF',c)
