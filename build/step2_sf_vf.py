"""Step 2: rebuild SF Pro (Latin/Greek/Cyrillic) in the target design space."""
import json, os, sys
from fontTools.ttLib import TTFont
from common import SF_TTF, WORK, sf_loc, glyph_struct
import vf_from_masters as V

TARGET = sys.argv[1]
SF_FEATURES = ['ccmp', 'locl', 'liga', 'clig', 'calt', 'rlig', 'case', 'frac', 'numr', 'dnom',
               'sups', 'subs', 'ordn', 'tnum', 'pnum', 'smcp', 'c2sc', 'kern', 'mark', 'mkmk',
               'rtlm'] + ['ss%02d' % i for i in range(1, 21)] + ['cv%02d' % i for i in range(1, 20)]

def is_pua(cp):
    return 0xE000 <= cp <= 0xF8FF or cp >= 0xF0000

def main():
    t = TTFont(TARGET, lazy=True); s = TTFont(SF_TTF, lazy=True)
    tc, sc = t.getBestCmap(), s.getBestCmap()
    cps = []
    for cp, sg in sc.items():
        if is_pua(cp) or cp not in tc: continue
        try:
            if glyph_struct(t['glyf'], tc[cp])[0] == glyph_struct(s['glyf'], sg)[0]:
                cps.append(cp)
        except Exception:
            pass
    print('SF codepoints present in target with SF structure:', len(cps))
    json.dump(sorted(cps), open(os.path.join(WORK, 'sf_cps.json'), 'w'))
    W = [100, 200, 300, 400, 500, 600, 700, 800, 900]
    masters = [{'wght': w, 'wdth': 100} for w in W]
    masters = [masters[4]] + masters[:4] + masters[5:]
    for d in (80, 120):
        for w in (100, 500, 900):
            masters.append({'wght': w, 'wdth': d})
    V.build(SF_TTF, cps, SF_FEATURES, masters, sf_loc, os.path.join(WORK, 'sf_vf.ttf'), upem=1000, tag='sf')

if __name__ == '__main__':
    main()
