"""Step 3: rebuild each MiSans script font in the target design space (variable wght)."""
import json, os, sys
from fontTools.ttLib import TTFont
from common import MISANS, WORK, mi_loc

RANGES = {
    'Arabic': [(0x0600, 0x06FF), (0x0750, 0x077F), (0x0870, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    'Devanagari': [(0x0900, 0x097F), (0xA8E0, 0xA8FF), (0x1CD0, 0x1CFF)],
    'Gujarati': [(0x0A80, 0x0AFF)],
    'Gurmukhi': [(0x0A00, 0x0A7F)],
    'Khmer': [(0x1780, 0x17FF), (0x19E0, 0x19FF)],
    'Lao': [(0x0E80, 0x0EFF)],
    'Myanmar': [(0x1000, 0x109F), (0xA9E0, 0xA9FF), (0xAA60, 0xAA7F)],
    'Thai': [(0x0E00, 0x0E7F)],
    'Tibetan': [(0x0F00, 0x0FFF)],
}

def script_cps(script):
    f = TTFont(MISANS[script], lazy=True)
    return sorted(cp for cp in f.getBestCmap() if any(a <= cp <= b for a, b in RANGES[script]))

def main(scripts):
    import vf_from_masters as V
    W = [500, 100, 200, 300, 400, 600, 700, 800, 900]
    masters = [{'wght': w, 'wdth': 100} for w in W]
    for s in scripts:
        cps = script_cps(s)
        print(s, 'codepoints', len(cps), flush=True)
        V.build(MISANS[s], cps, ['*'], masters, mi_loc, os.path.join(WORK, f'mi_{s}_vf.ttf'), upem=1000, tag='mi_' + s)

if __name__ == '__main__':
    main(sys.argv[1:] or list(MISANS))
