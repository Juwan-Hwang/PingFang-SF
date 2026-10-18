"""v1.2.0 fill checks: every added script shapes in the merged font exactly as in its part
(drawn outlines, advances and offsets via HarfBuzz at wght 100/500/900), every planned
codepoint is mapped to a non-empty glyph (except true spaces/format chars), and the font
has exactly 65,535 glyphs with U+F8FF and the 118 BMP PUA mappings intact.

usage: python validate_fill.py MERGED.ttf PARTS_DIR [data/fill_sources.json] [report.txt]
"""
import json, os, sys, unicodedata
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from common import target_norm

SAMPLES = {
    'PretendardVariable': ['대한민국 서울특별시 한국어 위키백과', '똠방각하 뷁 햏 쌰 됬 웻 슌', 'ㄱㄴㄷ ㉠㉡ ㈀'],
    'NotoSansKRwght': ['㉮㉯㉰ ㈜ ㉿', 'ㆀㆆ'],
    'PlangothicP1Regular': ['𠀀𪚥𫝀𬺰𭕄'],
    'PlangothicP2Regular': ['𰀀𰁀𱍐'],
    'SFArabic': ['ٻ ڀ ڄ ڃ', 'ڄڄڄ ڃڃڃ'],
    'SFArmenian': ['Հայերեն լեզու', 'Երևան ﬓ'],
    'SFGeorgian': ['ქართული ენა', 'თბილისი'],
    'SFIndia0': ['বাংলা ভাষা', 'ক্ষ র্ক শ্রী স্ত্র', 'কলকাতা'],
    'SFIndia4': ['ಕನ್ನಡ ಭಾಷೆ', 'ಬೆಂಗಳೂರು ಕ್ಷ ರ್ಕ'],
    'SFIndia5': ['മലയാളം ഭാഷ', 'ക്ഷ ന്റ ർ'],
    'SFIndia6': ['ଓଡ଼ିଆ ଭାଷା', 'କ୍ଷ ର୍କ'],
    'SFIndia7': ['தமிழ் மொழி', 'க்ஷ ஸ்ரீ சென்னை'],
    'NotoSansSinhalawdthwght': ['සිංහල භාෂාව', 'ශ්‍රී ලංකාව ක්‍ෂ'],
    'NotoSansMongolianRegular': ['ᠮᠣᠩᠭᠣᠯ ᠪᠢᠴᠢᠭ', 'ᠬᠥᠬᠡᠬᠣᠲᠠ'],
    'NotoSansSyriacwght': ['ܠܫܢܐ ܣܘܪܝܝܐ', 'ܐܠܗܐ'],
    'NotoSansThaanawght': ['ދިވެހި ބަސް', 'މާލެ'],
    'KefaIII': ['አማርኛ ቋንቋ', 'አዲስ አበባ ግዕዝ'],
    'NotoSansTifinaghRegular': ['ⵜⴰⵎⴰⵣⵉⵖⵜ ⵜⴰⵏⴰⵡⴰⵢⵜ'],
    'NotoSansCopticRegular': ['ⲧⲙⲛⲧⲣⲉⲙⲛⲕⲏⲙⲉ'],
    'NotoSansLisuwght': ['ꓡꓲ-ꓢꓴ ꓫꓵꓽ'],
    'NotoSansTaiLeRegular': ['ᥖᥭᥰ ᥘᥫᥴ'],
    'NotoSansNewTaiLuewght': ['ᦑᦲᧈᦟᦹᧉ'],
    'NotoSansSundanesewght': ['ᮃᮊ᮪ᮞᮛ ᮞᮥᮔ᮪ᮓ'],
    'NotoSansMyanmarwdthwght': ['ꩠꩡꩢ ꧠꧡ'],
    'NotoSanswdthwght': ['˥˩ ˦˨ ꜀ ꞔ ꟊ'],
    'math_stix': ['𝓗𝓮𝓵𝓵𝓸 𝔥𝔢𝔩𝔩𝔬 𝕙𝕖𝕝𝕝𝕠 𝛂𝛃𝛄'],
    'math_serif_b': ['𝐇𝐞𝐥𝐥𝐨 𝟏𝟐𝟑'],
    'math_serifit': ['𝐻𝑒𝑙𝑙𝑜'],
    'math_serifit_b': ['𝑯𝒆𝒍𝒍𝒐'],
    'math_sans_b': ['𝗛𝗲𝗹𝗹𝗼 𝟭𝟮𝟯'],
    'math_mono': ['𝙷𝚎𝚕𝚕𝚘 𝟷𝟸𝟹'],
}
WEIGHTS = (100, 500, 900)
HANGUL_FILLERS = {0x115F, 0x1160, 0x3164, 0xFFA0}   # Default_Ignorable: zero-width glyph on purpose


def shape(face, font_vars, text):
    """-> {cluster: [(outline, advance, x_off, y_off)]}, set of clusters holding .notdef.
    Empty zero-advance glyphs (default ignorables such as ZWJ) are left out: the merged font
    maps them to its shared zero-width glyph, the part does not map them at all."""
    font = hb.Font(face)
    font.set_variations(font_vars)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf)
    out, nd = {}, set()
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        if info.codepoint == 0:
            nd.add(info.cluster)
        pen = RecordingPen()
        font.draw_glyph_with_pen(info.codepoint, pen)
        if not pen.value and pos.x_advance == 0:
            continue
        out.setdefault(info.cluster, []).append((tuple(pen.value), pos.x_advance, pos.x_offset, pos.y_offset))
    return out, nd


def _pts(outline):
    return [pt for op, args in outline for pt in args]


def same_glyphs(xs, ys):
    """equal, allowing the whole outline to sit 1 unit apart horizontally: step 9 sets
    lsb = xMin for every added glyph, while a part rescaled to 1000 UPM may carry an lsb
    rounded 1 unit off its xMin (HarfBuzz shifts drawings by xMin - lsb in variable fonts)."""
    if xs is None or ys is None or len(xs) != len(ys):
        return False
    for (oa, *ma), (ob, *mb) in zip(xs, ys):
        if ma != mb or [op for op, _ in oa] != [op for op, _ in ob]:
            return False
        pa, pb = _pts(oa), _pts(ob)
        if not pa:
            continue
        dx = pb[0][0] - pa[0][0]
        if abs(dx) > 1 or any(abs(b[0] - a[0] - dx) > 1e-6 or abs(b[1] - a[1]) > 1e-6 for a, b in zip(pa, pb)):
            return False
    return True


def cluster_text(text, cl, clusters):
    """characters of cluster cl (clusters are UTF-32 indices with uharfbuzz add_str)."""
    nxt = min([c for c in clusters if c > cl], default=len(text))
    return text[cl:nxt]


def main(merged, parts_dir, spec_path=None, report=None):
    spec_path = spec_path or os.path.join(os.path.dirname(__file__), 'data', 'fill_sources.json')
    specs = {s['id']: s for s in json.load(open(spec_path))['plan']}
    lines, fails = [], 0
    F = TTFont(merged, lazy=True)
    n = F['maxp'].numGlyphs
    ok = n == 65535
    fails += not ok
    lines.append('%s numGlyphs = %d' % ('PASS' if ok else 'FAIL', n))
    cmap = F.getBestCmap()
    glyf = F['glyf']
    pua = [c for c in cmap if 0xE000 <= c <= 0xF8FF]
    ok = 0xF8FF in cmap and len(pua) == 118 and not any(0x100000 <= c <= 0x1042F5 for c in cmap)
    fails += not ok
    lines.append('%s U+F8FF kept, BMP PUA mapped: %d (want 118), SF Symbols PUA absent' % ('PASS' if ok else 'FAIL', len(pua)))
    # every planned codepoint mapped & non-empty
    missing, empty = [], []
    for s in specs.values():
        part = json.load(open(os.path.join(parts_dir, s['id'] + '.json')))
        bad = set(int(x, 16) for x in part['missing'])
        cps = [int(c) for c in (s['cpmap'].keys() if s.get('cpmap') else s['cps'])]
        for cp in cps:
            if cp in bad:
                continue
            g = cmap.get(cp)
            if g is None:
                missing.append(cp); continue
            cat = unicodedata.category(chr(cp))
            if cat not in ('Zs', 'Cf', 'Mn', 'Me') and cp not in HANGUL_FILLERS and glyf[g].numberOfContours == 0:
                empty.append(cp)
    ok = not missing and not empty
    fails += not ok
    lines.append('%s planned codepoints: missing %d, empty %d %s' % ('PASS' if ok else 'FAIL', len(missing), len(empty),
                                                                  ['%04X' % c for c in (missing + empty)[:20]]))
    # all mapped visible glyphs non-empty
    blank = [cp for cp, g in cmap.items() if unicodedata.category(chr(cp)) not in ('Zs', 'Cf', 'Mn', 'Me', 'Cc', 'Zl', 'Zp', 'Co', 'Cn')
             and glyf[g].numberOfContours == 0]
    lines.append('INFO mapped non-space codepoints drawing nothing: %d %s' % (len(blank), ['%04X' % c for c in blank[:30]]))
    mface = hb.Face(open(merged, 'rb').read())
    base = os.environ.get('PFSF_FILL_BASE')
    base_cps = set(TTFont(base, lazy=True).getBestCmap()) if base else set()
    new_cps = set(cmap) - base_cps
    for pid, texts in SAMPLES.items():
        if pid not in specs:
            continue
        pface = hb.Face(open(os.path.join(parts_dir, pid + '.ttf'), 'rb').read())
        for w in WEIGHTS:
            nw = target_norm({'wght': w, 'wdth': 100})['wght'] * 1000
            for t in texts:
                a, and_ = shape(pface, {'wght': nw, 'wdth': 0}, t)
                b, bnd = shape(mface, {'wght': w, 'wdth': 100}, t)
                cls = sorted(set(a) | set(b) | and_ | bnd)
                checked, bad = 0, []
                for cl in cls:
                    chars = cluster_text(t, cl, cls)
                    if cl in and_ or not any(ord(ch) in new_cps for ch in chars):
                        continue      # not drawn by this part (space, existing character, ...)
                    checked += 1
                    if cl in bnd or not same_glyphs(a.get(cl), b.get(cl)):
                        bad.append(chars)
                if bad or not checked:
                    fails += 1
                    lines.append('FAIL %s w%d %r: %d clusters checked, differing %r' % (pid, w, t, checked, bad[:8]))
                else:
                    lines.append('PASS %s w%d %r (%d new clusters identical)' % (pid, w, t, checked))
    lines.append('FAILURES: %d' % fails)
    txt = '\n'.join(lines)
    print(txt)
    if report:
        open(report, 'w').write(txt + '\n')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main(*sys.argv[1:])
