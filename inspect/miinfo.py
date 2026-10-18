import glob
from fontTools.ttLib import TTFont
for p in sorted(glob.glob('src/mvf/*.ttf')):
    f=TTFont(p, lazy=True)
    ax=[(a.axisTag,a.minValue,a.defaultValue,a.maxValue) for a in f['fvar'].axes]
    gs=f['GSUB'].table if 'GSUB' in f else None; gp=f['GPOS'].table if 'GPOS' in f else None
    print(p.split('/')[-1], f['head'].unitsPerEm, f['maxp'].numGlyphs, ax, 'avar' in f, [ (i.coordinates['wght'], f['name'].getDebugName(i.subfamilyNameID)) for i in f['fvar'].instances])
    for nm,g in (('GSUB',gs),('GPOS',gp)):
        if g: print('  ',nm,[ (sr.ScriptTag,[l.LangSysTag for l in sr.Script.LangSysRecord]) for sr in g.ScriptList.ScriptRecord], sorted(set(fr.FeatureTag for fr in g.FeatureList.FeatureRecord)), len(g.LookupList.Lookup), getattr(g,'FeatureVariations',None) is not None)
    if 'GDEF' in f:
        gd=f['GDEF'].table; print('   GDEF', hex(gd.Version), gd.VarStore is not None if hasattr(gd,'VarStore') else None, gd.MarkAttachClassDef is not None, getattr(gd,'MarkGlyphSetsDef',None) is not None)
    print('   tables',sorted(f.keys()), 'fsType', f['OS/2'].fsType, '|', f['name'].getDebugName(0), '|', (f['name'].getDebugName(13) or '')[:150])
