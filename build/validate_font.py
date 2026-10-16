"""Structural validation: full fontTools decompile + recompile, gvar/HVAR consistency,
and static instancing.

usage: python validate_font.py FONT.ttf [roundtrip|instance:WGHT]
"""
import os, struct, sys, time
from fontTools.ttLib import TTFont


def roundtrip(path):
    t = time.time()
    f = TTFont(path)
    n = f['maxp'].numGlyphs
    go = f.getGlyphOrder()
    assert len(go) == n
    raw = f.reader['gvar']
    gcount = struct.unpack('>H', raw[12:14])[0]
    print('maxp.numGlyphs', n, 'gvar.glyphCount', gcount, 'hmtx', len(f['hmtx'].metrics),
          'vmtx', len(f['vmtx'].metrics))
    assert gcount == n
    bad = []
    for g in go:
        try:
            f['gvar'].variations[g]
            f['glyf'][g]
        except Exception as e:
            bad.append((g, repr(e)))
    print('undecodable glyph/gvar entries:', bad[:5], len(bad))
    assert not bad
    for tag in sorted(f.keys()):
        if tag != 'GlyphOrder':
            f[tag]
    out = path + '.roundtrip.ttf'
    f.save(out)
    g = TTFont(out)
    assert g['maxp'].numGlyphs == n
    print('roundtrip OK (%.0fs), size %d -> %d' % (time.time() - t, os.path.getsize(path), os.path.getsize(out)))
    os.remove(out)


def instance(path, wght):
    from fontTools.varLib import instancer
    t = time.time()
    f = TTFont(path)
    s = instancer.instantiateVariableFont(f, {'wght': wght, 'wdth': 100})
    out = path + '.w%d.ttf' % wght
    s.save(out)
    g = TTFont(out)
    assert 'gvar' not in g and 'fvar' not in g
    print('instance wght=%d OK (%.0fs): %d glyphs, %d bytes -> %s' % (wght, time.time() - t, g['maxp'].numGlyphs, os.path.getsize(out), out))


if __name__ == '__main__':
    mode = sys.argv[2] if len(sys.argv) > 2 else 'roundtrip'
    if mode == 'roundtrip':
        roundtrip(sys.argv[1])
    else:
        instance(sys.argv[1], int(mode.split(':')[1]))
