"""Re-express a variable source font in the target (PingFang UI) design space.

The source is subset, optionally UPEM-scaled, instanced at the source location that
corresponds to each target master location, and the static masters are re-built into a
variable font whose axes are the *normalized* target axes (wght, wdth in -1..1, stored
as user values -1000..1000).  Its gvar / GDEF VarStore / GPOS device tables can then be
copied verbatim into the target font.
"""
import os, sys, tempfile
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer, build as varlib_build
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools import subset
from common import target_norm, WORK

DROP = ['MERG', 'trak', 'MVAR', 'STAT', 'meta', 'DSIG', 'VVAR', 'vhea', 'vmtx', 'kern', 'morx', 'feat']

def subset_font(font, unicodes, features, glyphs=()):
    opts = subset.Options()
    opts.layout_features = features
    opts.name_IDs = ['*']; opts.name_languages = ['*']
    opts.glyph_names = True; opts.notdef_outline = True; opts.hinting = False
    opts.layout_closure = True; opts.drop_tables += DROP
    opts.prune_unicode_ranges = False; opts.recalc_bounds = False
    opts.legacy_kern = False; opts.layout_scripts = ['*']
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=unicodes, glyphs=list(glyphs))
    sub.subset(font)
    return font

def build(src_path, unicodes, features, master_tlocs, src_loc_fn, out_path, upem=None, tag='src'):
    f = TTFont(src_path)
    for t in DROP:
        if t in f: del f[t]
    subset_font(f, unicodes, features)
    if upem and f['head'].unitsPerEm != upem:
        scale_upem(f, upem)
    f.save(out_path.replace('.ttf', '_subset.ttf'))
    f = TTFont(out_path.replace('.ttf', '_subset.ttf'))
    # FeatureVariations are ported separately from the *_subset.ttf (step 4); masters must
    # share an identical GSUB, so drop them here.
    if 'GSUB' in f and getattr(f['GSUB'].table, 'FeatureVariations', None) is not None:
        f['GSUB'].table.FeatureVariations = None
        f['GSUB'].table.Version = 0x00010000
    tmp = os.path.join(WORK, 'masters_' + tag); os.makedirs(tmp, exist_ok=True)
    ds = DesignSpaceDocument()
    for t in ('wght', 'wdth'):
        a = AxisDescriptor(); a.tag = t; a.name = t
        a.minimum, a.default, a.maximum = -1000, 0, 1000
        ds.addAxis(a)
    for i, tl in enumerate(master_tlocs):
        sl = src_loc_fn(tl)
        axes_present = {a.axisTag for a in f['fvar'].axes}
        sl = {k: v for k, v in sl.items() if k in axes_present}
        inst = instancer.instantiateVariableFont(f, sl, inplace=False, updateFontNames=False)
        p = os.path.join(tmp, f'm{i}.ttf'); inst.save(p)
        n = target_norm(tl)
        s = SourceDescriptor(); s.path = p; s.name = f'm{i}'
        s.location = {'wght': n['wght'] * 1000, 'wdth': n['wdth'] * 1000}
        ds.addSource(s)
        print(f'  [{tag}] master {i} target {tl} -> source {sl}', flush=True)
    vf, _, _ = varlib_build(ds, exclude=['STAT', 'MVAR', 'name'] , optimize=True)
    vf.save(out_path)
    return out_path
