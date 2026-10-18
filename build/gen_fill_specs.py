"""Turn the ranked fill plan (data/fillplan.json) into part specs (data/fill_sources.json).

One part per source font (in-plan tranches merged), plus one part per backfill tranche
(ranked after the cut line, used to fill the font to exactly 65,535 glyphs).
Mathematical alphanumerics are split into style parts drawn from Apple's text faces.

usage: python gen_fill_specs.py data/fillplan.json data/fill_sources.json
"""
import json, sys, unicodedata, re
from collections import OrderedDict

# source path (relative to PFSF_FILL_SRC) -> (wmap, OpenType script tags merged into the target)
SRC = OrderedDict([
    ('addfont/src/pretendard/public/variable/PretendardVariable.ttf', ('same', [])),
    ('addfont/src/gf/NotoSansKR[wght].ttf', ('same', [])),
    ('fillplan/src/PlangothicP1-Regular.ttf', ('static', [])),
    ('fillplan/src/PlangothicP2-Regular.ttf', ('static', [])),
    ('addfont/src/osf/Apple Symbols.ttf', ('static', [])),
    ('addfont/src/osf/seguisym6_24.ttf', ('static', [])),
    ('addfont/src/gf/NotoSansSymbols2-Regular.ttf', ('static', [])),
    ('fillplan/src/gf/NotoMusic-Regular.ttf', ('static', [])),
    ('addfont/src/gf/NotoSans[wdth,wght].ttf', ('same', [])),
    ('addfont/src/apple/SF-Arabic/SF-Arabic.ttf', ('sf', ['arab'])),
    ('addfont/src/gf/NotoSansArabic[wdth,wght].ttf', ('same', ['arab'])),
    ('fillplan/src/SFGeorgian.ttf', ('sf', [])),
    ('fillplan/src/SFArmenian.ttf', ('sf', ['armn'])),
    ('fillplan/src/SFIndia.ttc#0', ('sf', ['bng2', 'beng'])),
    ('fillplan/src/SFIndia.ttc#4', ('sf', ['knd2', 'knda'])),
    ('fillplan/src/SFIndia.ttc#5', ('sf', ['mlm2', 'mlym'])),
    ('fillplan/src/SFIndia.ttc#6', ('sf', ['ory2', 'orya'])),
    ('fillplan/src/SFIndia.ttc#7', ('sf', ['tml2', 'taml'])),
    ('fillplan/src/SFIndia.ttc#8', ('sf', ['tel2', 'telu'])),
    ('addfont/src/gf/NotoSansLisu[wght].ttf', ('same', ['lisu'])),
    ('addfont/src/osf/NotoSansMongolian-Regular.ttf', ('static', ['mong'])),
    ('addfont/src/gf/NotoSansTaiLe-Regular.ttf', ('static', ['tale'])),
    ('fillplan/src/gf/NotoSansThaana[wght].ttf', ('same', ['thaa'])),
    ('fillplan/src/gf/NotoSansSinhala[wdth,wght].ttf', ('same', ['sinh'])),
    ('fillplan/src/gf/NotoSansTifinagh-Regular.ttf', ('static', ['tfng'])),
    ('fillplan/src/gf/NotoSansSyriac[wght].ttf', ('same', ['syrc'])),
    ('fillplan/src/gf/NotoSansCoptic-Regular.ttf', ('static', ['copt'])),
    ('fillplan/src/KefaIII.ttf', ({'100': 300, '500': 500, '900': 800}, ['ethi'])),
    ('addfont/src/gf/NotoSansMyanmar[wdth,wght].ttf', ('same', ['mym2', 'mymr'])),
    ('fillplan/src/gf/NotoSansSundanese[wght].ttf', ('same', ['sund'])),
    ('addfont/src/gf/NotoSansNewTaiLue[wght].ttf', ('same', ['talu'])),
    ('fillplan/src/gf/NotoSansNKo-Regular.ttf', ('static', ['nko '])),
    ('fillplan/src/gf/NotoSansCanadianAboriginal[wght].ttf', ('same', ['cans'])),
    ('fillplan/src/gf/NotoSansJavanese[wght].ttf', ('same', ['java'])),
    ('fillplan/src/gf/NotoSansCherokee[wght].ttf', ('same', ['cher'])),
    ('fillplan/src/gf/NotoSansOlChiki[wght].ttf', ('same', ['olck'])),
    ('fillplan/src/gf/NotoSansGlagolitic-Regular.ttf', ('static', ['glag'])),
    ('fillplan/src/gf/NotoSansCham[wght].ttf', ('same', ['cham'])),
    ('fillplan/src/gf/NotoSansMeeteiMayek[wght].ttf', ('same', ['mtei'])),
    ('fillplan/src/gf/NotoSansGeorgian[wdth,wght].ttf', ('same', ['geor'])),
    ('fillplan/src/gf/NotoSansBalinese[wght].ttf', ('same', ['bali'])),
    ('fillplan/src/gf/NotoSansPhagsPa-Regular.ttf', ('static', ['phag'])),
    ('fillplan/src/gf/NotoSansTaiViet-Regular.ttf', ('static', ['tavt'])),
    ('fillplan/src/gf/NotoSansAdlam[wght].ttf', ('same', ['adlm'])),
    ('fillplan/src/gf/NotoSansTaiTham[wght].ttf', ('same', ['lana'])),
    ('fillplan/src/gf/NotoSansVai-Regular.ttf', ('static', ['vai '])),
    ('src/shs/SourceHanSans-VF.ttf', ({'100': 250, '500': 500, '900': 900}, ['hang'])),
    ('addfont/src/gf/NotoSansYi-Regular.ttf', ('static', ['yi  '])),
    ('addfont/src/gf/NotoSansNushu-Regular.ttf', ('static', ['nshu'])),
    ('addfont/src/gf/NotoSansMiao-Regular.ttf', ('static', ['plrd'])),
])
SHAPED = {k for k, (w, s) in SRC.items() if s}

SFP = 'src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf'
SFI = 'src/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro-Italic.ttf'
NY = 'addfont/src/apple/NY/NewYork.ttf'
NYI = 'addfont/src/apple/NY/NewYorkItalic.ttf'
MONO = 'addfont/src/osf/SFNSMono.ttf'
STIX = 'addfont/src/osf/STIXTwoMath.otf'
STIX_SCALE = 705 / 657      # STIX cap height 657 -> SF Pro cap height in this font (705)
DIGITS = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE']


def norm_src(k):
    k = k.split('/work/', 1)[-1]
    k = re.sub(r'^fillplan/\.\./addfont/src/\.\./\.\./', '', k)
    return k


def math_route(cp):
    """-> (source, bold, base cp) or (STIX, False, cp)"""
    n = unicodedata.name(chr(cp), '')
    parts = n.split()
    base = None
    if 'CAPITAL' in parts and len(parts[-1]) == 1:
        base = parts[-1]
    elif 'SMALL' in parts and len(parts[-1]) == 1:
        base = parts[-1].lower()
    elif 'DIGIT' in parts:
        base = str(DIGITS.index(parts[-1]))
    if base is None or any(p in parts for p in ('SCRIPT', 'FRAKTUR', 'DOUBLE-STRUCK')):
        return STIX, False, cp
    bold, ital = 'BOLD' in parts, 'ITALIC' in parts
    if 'MONOSPACE' in parts:
        return MONO, False, ord(base)
    if 'SANS-SERIF' in parts:
        return (SFI if ital else SFP), bold, ord(base)
    return (NYI if ital else NY), bold, ord(base)


def math_specs(cps, tag):
    groups = OrderedDict()
    for cp in cps:
        src, bold, base = math_route(cp)
        groups.setdefault((src, bold), {})[cp] = base
    out = []
    for (src, bold), m in groups.items():
        name = {SFP: 'sans', SFI: 'sansit', NY: 'serif', NYI: 'serifit', MONO: 'mono', STIX: 'stix'}[src]
        s = {'id': f'{tag}_{name}{"_b" if bold else ""}', 'src': src, 'kind': 'math'}
        if src == STIX:
            s.update(wmap='static', cps=sorted(m), scale=STIX_SCALE)
        else:
            s.update(wmap='sf', bold=bold, cpmap={str(k): v for k, v in sorted(m.items())},
                     pin={'YAXS': 400})
        out.append(s)
    return out


def main(plan_path, out_path, trim_path=None):
    d = json.load(open(plan_path))
    tr = sorted(d['tranches'], key=lambda t: t['rank'])
    # data/fill_trim.json: measured glyph costs exceeded the plan's estimates (mostly the
    # Arabic letters' GSUB closure), so the lowest-ranked in-plan per-character tranches are
    # dropped/trimmed until the font holds exactly 65,535 glyphs.
    trim = json.load(open(trim_path)) if trim_path else {'drop_ranks': [], 'trim_tail': {}}
    for t in tr:
        if t['in_plan'] and t['rank'] in trim['drop_ranks']:
            t['in_plan'] = False
            t['_dropped'] = True
        n = trim['trim_tail'].get(str(t['rank']))
        if t['in_plan'] and n:
            srcs = t['sources'] if isinstance(t['sources'], dict) else eval(t['sources'])
            assert len(srcs) == 1, t['rank']
            k = next(iter(srcs))
            srcs[k] = srcs[k][:len(srcs[k]) - n]
            t['sources'] = srcs
    parts = OrderedDict()
    math_in = []
    backfill = []
    for t in tr:
        srcs = t['sources']
        if isinstance(srcs, str):
            srcs = eval(srcs)
        if t['in_plan']:
            for k, cps in srcs.items():
                cps = [int(c, 16) for c in cps]
                if k.startswith('addfont hybrid'):
                    math_in += cps
                    continue
                k = norm_src(k)
                parts.setdefault(k, []).extend(cps)
        elif not t.get('_dropped'):
            for k, cps in srcs.items():
                cps = [int(c, 16) for c in cps]
                bf = {'rank': t['rank'], 'category': t['category'], 'specs': []}
                if k.startswith('addfont hybrid'):
                    bf['specs'] = math_specs(cps, 'bf%d_math' % t['rank'])
                    bf['whole'] = False
                else:
                    k = norm_src(k)
                    path, _, face = k.partition('#')
                    w, scripts = SRC[k]
                    bf['specs'] = [{'id': 'bf%d_%s' % (t['rank'], re.sub(r'\W+', '', path.rsplit('/', 1)[-1].split('.')[0] + face)),
                                    'src': path, 'face': int(face or 0), 'wmap': w, 'scripts': scripts, 'cps': cps}]
                    bf['whole'] = k in SHAPED
                backfill.append(bf)
    specs = []
    for k, cps in parts.items():
        path, _, face = k.partition('#')
        w, scripts = SRC[k]
        pid = re.sub(r'\W+', '', path.rsplit('/', 1)[-1].split('.')[0] + face)
        specs.append({'id': pid, 'src': path, 'face': int(face or 0), 'wmap': w, 'scripts': scripts,
                      'cps': sorted(set(cps))})
    specs += math_specs(sorted(set(math_in)), 'math')
    json.dump({'plan': specs, 'backfill': backfill}, open(out_path, 'w'), indent=0)
    print(len(specs), 'plan parts;', len(backfill), 'backfill tranches')


if __name__ == '__main__':
    main(*sys.argv[1:4])
