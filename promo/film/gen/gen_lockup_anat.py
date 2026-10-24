"""Glyph data for the film, read straight from the repo's font file (no font binary is copied into the film).
lockup.json : '苹方SF' and 'PingFang SF' shaped by HarfBuzz at wght 100..900 (step 25); outlines in font units (y up),
              the i's tittle split off as its own path (it is the film's carry element).
anat.json   : TrueType points (on/off curve, as stored in glyf + gvar) of 永 A g at wght 100..900 step 50 (wdth 100)
              and wdth 80..120 step 5 (wght 500), via fontTools getGlyphSet(location=...).
"""
import json, sys, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
P = sys.argv[1] if len(sys.argv) > 1 else '../../PingFang-SF Medium.ttf'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'film/data'
blob = open(P, 'rb').read(); face = hb.Face(blob)

class SVGPen:
    def __init__(s): s.cs = []; s.cur = None
    def f(s, v): return f'{v:.1f}'.rstrip('0').rstrip('.')
def draw_contours(font, gid, dx):
    """returns list of contour path strings (absolute, font units, y up) for one glyph offset by dx"""
    cs = []; cur = []
    def mv(x, y, _): cur.append(f'M{x+dx:.1f} {y:.1f}')
    def ln(x, y, _): cur.append(f'L{x+dx:.1f} {y:.1f}')
    def qd(x1, y1, x, y, _): cur.append(f'Q{x1+dx:.1f} {y1:.1f} {x+dx:.1f} {y:.1f}')
    def cb(x1, y1, x2, y2, x, y, _): cur.append(f'C{x1+dx:.1f} {y1:.1f} {x2+dx:.1f} {y2:.1f} {x+dx:.1f} {y:.1f}')
    def cl(_):
        cur.append('Z'); cs.append(''.join(cur)); cur.clear()
    funcs = hb.DrawFuncs(); funcs.set_move_to_func(mv); funcs.set_line_to_func(ln)
    funcs.set_quadratic_to_func(qd); funcs.set_cubic_to_func(cb); funcs.set_close_path_func(cl)
    funcs.draw_glyph(font, gid, None)
    return cs

def run(text, w, x0=0):
    font = hb.Font(face); font.set_variations({'wght': w, 'wdth': 100})
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': True})
    x = x0; out = []; tittle = None
    for ch, info, pos in zip(range(len(buf.glyph_infos)), buf.glyph_infos, buf.glyph_positions):
        cs = draw_contours(font, info.codepoint, x + pos.x_offset)
        c = text[info.cluster]
        if c == 'i':   # split the tittle (contour entirely above the x-height) from the stem
            def ymin(d):
                import re; ys = [float(v) for v in re.findall(r'-?\d+\.?\d*', d)][1::2]; return min(ys)
            t = [d for d in cs if ymin(d) > 500]; s_ = [d for d in cs if ymin(d) <= 500]
            tittle = t[0]; cs = s_
        if cs: out.append({'ch': c, 'd': ''.join(cs), 'x': x})
        x += pos.x_advance
    return out, x, tittle

L = {'samples': []}
for w in range(100, 901, 25):
    g1, a1, _ = run('苹方SF', w)
    # word space taken from the font's own space at the second run's weight
    font = hb.Font(face); font.set_variations({'wght': w})
    sp = font.get_glyph_h_advance(font.get_nominal_glyph(32))
    L['samples'].append({'w': w, 'run1': g1, 'adv1': a1, 'space': sp})
for w in range(100, 901, 25):
    g2, a2, tit = run('PingFang SF', w)
    L['samples'][(w - 100) // 25].update({'run2': g2, 'adv2': a2, 'tittle': tit})
json.dump(L, open(f'{OUT}/lockup.json', 'w'), separators=(',', ':'))

f = TTFont(P, lazy=True); cm = f.getBestCmap()
def pts(loc, ch):
    gs = f.getGlyphSet(location=loc); g = gs[cm[ord(ch)]]; rp = RecordingPen(); g.draw(rp)
    cons = []; cur = []
    for op, args in rp.value:
        if op == 'moveTo': cur = [[*args[0], 1]]
        elif op == 'lineTo': cur.append([*args[0], 1])
        elif op == 'qCurveTo':
            for a in args[:-1]: cur.append([*a, 0])
            if args[-1] is not None: cur.append([*args[-1], 1])
        elif op == 'curveTo':
            for a in args[:-1]: cur.append([*a, 0])
            cur.append([*args[-1], 1])
        elif op in ('closePath', 'endPath'): cons.append([[round(x, 1), round(y, 1), o] for x, y, o in cur]); cur = []
    return {'adv': round(g.width, 1), 'c': cons}
A = {'wght': [], 'wdth': []}
for w in range(100, 901, 50): A['wght'].append({'v': w, **{ch: pts({'wght': w, 'wdth': 100}, ch) for ch in '永Ag'}})
for d in range(80, 121, 5): A['wdth'].append({'v': d, **{ch: pts({'wght': 500, 'wdth': d}, ch) for ch in '永Ag'}})
json.dump(A, open(f'{OUT}/anat.json', 'w'), separators=(',', ':'), ensure_ascii=False)
s0 = L['samples'][0]; s1 = L['samples'][-1]
print('lockup', len(L['samples']), 'adv1', s0['adv1'], s1['adv1'], 'adv2', s0['adv2'], s1['adv2'], 'space', s0['space'], s1['space'])
print('anat pts', {ch: sum(len(c) for c in A['wght'][0][ch]['c']) for ch in '永Ag'}, 'contours', {ch: len(A['wght'][0][ch]['c']) for ch in '永Ag'})
