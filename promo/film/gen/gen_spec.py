"""spec.json: the specimen 'Align 对齐' as TrueType points (on/off curve exactly as stored in glyf, deltas from gvar)
at wght 100..900 step 50 (wdth 100) and wdth 80..120 step 5 (wght 500). Glyph positions come from HarfBuzz shaping
(kern on) at the same location; the i's tittle is flagged (contour entirely above y=500)."""
import json, sys, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
P, OUT = sys.argv[1], sys.argv[2]
TEXT = 'Align 对齐'
f = TTFont(P, lazy=True); go = f.getGlyphOrder()
face = hb.Face(open(P, 'rb').read())
def at(loc):
    font = hb.Font(face); font.set_variations(loc)
    buf = hb.Buffer(); buf.add_str(TEXT); buf.guess_segment_properties(); hb.shape(font, buf, {'kern': True})
    gs = f.getGlyphSet(location=loc); x = 0; out = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ch = TEXT[info.cluster]; rp = RecordingPen(); gs[go[info.codepoint]].draw(rp)
        cons = []; cur = []
        for op, args in rp.value:
            if op == 'moveTo': cur = [[*args[0], 1]]
            elif op == 'lineTo': cur.append([*args[0], 1])
            elif op == 'qCurveTo':
                for a in args[:-1]: cur.append([*a, 0])
                if args[-1] is not None: cur.append([*args[-1], 1])
            elif op in ('closePath', 'endPath'): cons.append([[round(p[0], 1), round(p[1], 1), p[2]] for p in cur]); cur = []
        tit = [k for k, c in enumerate(cons) if ch == 'i' and min(p[1] for p in c) > 500]
        if cons: out.append({'ch': ch, 'x': x + pos.x_offset, 'c': cons, 'tit': tit[0] if tit else -1})
        x += pos.x_advance
    return {'adv': x, 'g': out}
D = {'text': TEXT, 'wght': [{'v': w, **at({'wght': w, 'wdth': 100})} for w in range(100, 901, 50)],
     'wdth': [{'v': d, **at({'wght': 500, 'wdth': d})} for d in range(80, 121, 5)]}
json.dump(D, open(f'{OUT}/spec.json', 'w'), separators=(',', ':'), ensure_ascii=False)
w5 = D['wght'][8]; print('adv@500', w5['adv'], [(g['ch'], g['x'], sum(len(c) for c in g['c'])) for g in w5['g']])
print('struct same', len(set(json.dumps([[len(c) for c in g['c']] for g in s['g']]) for s in D['wght'] + D['wdth'])) == 1)
