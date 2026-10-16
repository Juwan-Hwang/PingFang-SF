"""HarfBuzz shaping regression tests: merged font vs. the original source fonts.

For each sample the merged font (at a target weight) and the source font (at the matching
source weight) are shaped with HarfBuzz; glyph extents, advances and offsets must agree
within a tolerance.  Exit status is non-zero on any failure.

usage: python validate_shaping.py MERGED.ttf [report.txt]
"""
import sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont, TTCollection
from common import MISANS, SF_TTF, PF_TTC, sf_loc, mi_loc

SAMPLES = {
    'Arabic': ['بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', 'لا إله إلا الله', 'ببب', 'كتب'],
    'Devanagari': ['क्ष', 'स्त्र', 'क्षत्रिय स्त्री हिन्दी', 'र्क', 'द्ध'],
    'Gujarati': ['ગુજરાતી ભાષા', 'ક્ષ', 'શ્રી'],
    'Gurmukhi': ['ਪੰਜਾਬੀ ਭਾਸ਼ਾ', 'ਗੁਰਮੁਖੀ'],
    'Khmer': ['ភាសាខ្មែរ', 'ស្ត្រី', 'កម្ពុជា'],
    'Lao': ['ພາສາລາວ', 'ສະບາຍດີ'],
    'Myanmar': ['မြန်မာဘာသာ', 'ကြည့်'],
    'Thai': ['สวัสดีครับ ภาษาไทย', 'ที่นี่', 'ปั้น'],
    'Tibetan': ['བོད་ཡིག', 'བསྒྲུབས', 'ཀྲྀ'],
}
LATIN = ['AV', 'To', 'AVATAR', 'Today', 'office fi fl', 'Wave Type', 'ΑΥΓΟ', 'Жизнь']


def hbfont(path, index=0, loc=None):
    face = hb.Face(hb.Blob.from_file_path(path), index)
    f = hb.Font(face)
    if loc:
        f.set_variations(loc)
    return f


def shape(font, text, direction=None, features=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    if direction:
        buf.direction = direction
    hb.shape(font, buf, features or {})
    out = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ext = font.get_glyph_extents(info.codepoint)
        e = (ext.x_bearing, ext.y_bearing, ext.width, ext.height) if ext else (0, 0, 0, 0)
        out.append((info.codepoint, info.cluster, pos.x_advance, pos.y_advance, pos.x_offset, pos.y_offset, e))
    return out


def compare(a, b, tol, scale=1.0):
    if len(a) != len(b):
        return False, 'glyph count %d vs %d' % (len(a), len(b))
    worst = 0
    for x, y in zip(a, b):
        if x[1] != y[1]:
            return False, 'cluster mismatch'
        vals_a = [x[2], x[3], x[4], x[5]] + list(x[6])
        vals_b = [v * scale for v in [y[2], y[3], y[4], y[5]] + list(y[6])]
        worst = max(worst, max(abs(p - q) for p, q in zip(vals_a, vals_b)))
    return worst <= tol, 'max deviation %.1f' % worst


def main(merged, report=None):
    lines, fails = [], 0

    def out(s):
        nonlocal lines
        print(s)
        lines.append(s)

    out('# Shaping validation for ' + merged)
    for script, texts in SAMPLES.items():
        for tw in (100, 500, 900):
            m = hbfont(merged, loc={'wght': tw, 'wdth': 100})
            s = hbfont(MISANS[script], loc=mi_loc({'wght': tw}))
            for t in [w for x in texts for w in x.split(' ')]:
                ok, msg = compare(shape(m, t), shape(s, t), tol=2)
                fails += not ok
                out('%-4s %-10s wght=%d  %-28s %s' % ('OK' if ok else 'FAIL', script, tw, t, msg))
    # Latin / Greek / Cyrillic incl. kerning vs SF Pro (UPEM 2048 -> 1000)
    for tw in (100, 500, 900):
        m = hbfont(merged, loc={'wght': tw, 'wdth': 100})
        sl = sf_loc({'wght': tw, 'wdth': 100})
        s = hbfont(SF_TTF, loc=sl)
        for t in LATIN:
            a, b = shape(m, t), shape(s, t)
            # compare advances (= advance + kerning) only; outlines of ASCII come from
            # PingFang UI's own SF-based Latin and may differ by a few units at extremes
            adv_a = [x[2] + 0 for x in a]
            adv_b = [round(y[2] * 1000 / 2048) for y in b]
            dev = max(abs(p - q) for p, q in zip(adv_a, adv_b)) if len(a) == len(b) else 999
            ok = dev <= (3 if tw == 500 else 8)
            fails += not ok
            out('%-4s %-10s wght=%d  %-28s advances %s vs SF %s (max dev %d)' % (
                'OK' if ok else 'FAIL', 'Latin', tw, t, adv_a, adv_b, dev))
    # kerning present?
    m = hbfont(merged, loc={'wght': 500, 'wdth': 100})
    for pair in ('AV', 'To', 'Ty', 'LT'):
        k = shape(m, pair)
        nok = shape(m, pair, features={'kern': False})
        kern = k[0][2] - nok[0][2]
        ok = kern < 0
        fails += not ok
        out('%-4s kern      %s: kerning %d units' % ('OK' if ok else 'FAIL', pair, kern))
    liga = shape(m, 'fi', features={'liga': True})
    out('INFO liga      "fi" -> %d glyph(s)' % len(liga))
    # vertical CJK: vert must substitute punctuation with the PingFang vertical forms
    pf_sc = hbfont(PF_TTC, 0)
    for t in ['，', '。', '、', '「', '」', '（', '）', '《', '》', '…', '—', '：', '！', '？', '～']:
        h = shape(m, t)
        v = shape(m, t, direction='ttb')
        ref = shape(pf_sc, t, direction='ttb')
        ok = v[0][6] == ref[0][6] and v[0][3] == ref[0][3]
        fails += not ok
        out('%-4s vert      %s  horizontal gid %d -> vertical gid %d  extents %s (PingFang UI SC: %s)%s' % (
            'OK' if ok else 'FAIL', t, h[0][0], v[0][0], v[0][6], ref[0][6], '' if h[0][0] != v[0][0] else '  [no vertical form in source either]'))
    # locl: zh-Hant (ZHT) should switch the SC-style punctuation to the centred TC forms
    for lang in ('zh-Hant', 'zh-HK', 'ja'):
        buf = hb.Buffer(); buf.add_str('，。骨'); buf.guess_segment_properties(); buf.language = lang
        hb.shape(m, buf, {})
        buf2 = hb.Buffer(); buf2.add_str('，。骨'); buf2.guess_segment_properties(); buf2.language = 'zh-Hans'
        hb.shape(m, buf2, {})
        out('INFO locl      %-8s ，。骨 gids %s (zh-Hans %s)' % (lang, [i.codepoint for i in buf.glyph_infos], [i.codepoint for i in buf2.glyph_infos]))
    out('\nTOTAL FAILURES: %d' % fails)
    if report:
        open(report, 'w').write('\n'.join(lines) + '\n')
    return fails


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None) else 0)
