"""Shared helpers for the PingFang SF build pipeline."""
import hashlib, os
from fontTools.varLib.models import normalizeValue, piecewiseLinearMap

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('PFSF_SRC', os.path.join(ROOT, '..', 'sources'))
WORK = os.environ.get('PFSF_WORK', os.path.join(ROOT, '..', 'build_work'))
os.makedirs(WORK, exist_ok=True)

PF_TTC = os.path.join(SRC, 'v21', 'PingFangUI.tahoe.26.4.1.wght.wdth.ttc')
SF_TTF = os.path.join(SRC, 'sf', 'SFProFontsPackage.pkg', 'Library', 'Fonts', 'SF-Pro.ttf')
MISANS = {s: os.path.join(SRC, 'mvf', s + '.ttf') for s in
          ['Arabic', 'Devanagari', 'Gujarati', 'Gurmukhi', 'Khmer', 'Lao', 'Myanmar', 'Thai', 'Tibetan']}

# Target (PingFang UI) axes: wght 100-500-900, wdth 80-100-120, with this avar.
TARGET_AXES = {'wght': (100, 500, 900), 'wdth': (80, 100, 120)}
TARGET_AVAR = {'wght': {-1.0: -1.0, -0.75: -0.79998779296875, -0.5: -0.5999755859375,
                        -0.25: -0.29998779296875, 0.0: 0.0, 0.25: 0.199951171875,
                        0.5: 0.39996337890625, 0.75: 0.5999755859375, 1.0: 1.0},
               'wdth': {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}}

def target_norm(loc):
    """target user location -> normalized (post-avar) location"""
    out = {}
    for tag, (mn, df, mx) in TARGET_AXES.items():
        v = normalizeValue(loc.get(tag, df), (mn, df, mx))
        out[tag] = piecewiseLinearMap(v, TARGET_AVAR[tag])
    return out

# SF Pro location used for each target location. Fitted against the Latin that
# Apple ships inside PingFang UI (which is SF Pro drawn at these weights):
SF_WGHT_MAP = {100: 236, 200: 296, 300: 356, 400: 450, 500: 540, 600: 640,
               700: 740, 800: 840, 900: 1000}
def sf_loc(tloc):
    w = piecewiseLinearMap(tloc['wght'], {float(k): float(v) for k, v in SF_WGHT_MAP.items()})
    return {'wght': w, 'wdth': tloc['wdth'], 'opsz': 17}

# MiSans (wght 150-330-700): PingFang named weights -> MiSans named weights.
MI_WGHT_MAP = {100: 150, 200: 200, 300: 250, 400: 330, 500: 380, 600: 520,
               700: 630, 800: 680, 900: 700}
def mi_loc(tloc):
    return {'wght': piecewiseLinearMap(tloc['wght'], {float(k): float(v) for k, v in MI_WGHT_MAP.items()})}

def glyph_struct(glyf, name):
    """(structure-hash, coords, endpts) of a flattened glyph, or None."""
    g = glyf[name]
    c, e, fl = g.getCoordinates(glyf)
    key = hashlib.md5(repr((list(e), [x & 1 for x in fl])).encode()).hexdigest()
    return key, list(c)
