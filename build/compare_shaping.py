"""A/B shaping regression: OLD.ttf vs NEW.ttf of PingFang SF (glyph IDs may differ).

usage: python compare_shaping.py OLD.ttf NEW.ttf [report.txt]

Each sample is shaped with HarfBuzz in both fonts at wght 100/400/700/900 (wdth 100, plus
wdth 80/120 at 400) and every resulting glyph is compared by its *drawn outline*
(HarfBuzz draw, at that variation location), advance and offset.  Glyph IDs/names are
ignored, so merged duplicates and pruned slots compare equal when the rendering is equal.
Samples cover Arabic (incl. lam-alef, marks, presentation forms, Arabic digits), Latin /
Greek / Cyrillic incl. every merged look-alike pair and kerning, CJK (+ zh-Hant/ja locl,
vertical), and the other MiSans scripts.  Code points that are intentionally unmapped in
NEW (SF Symbols PUA, Emoji_Presentation) are reported separately, not as regressions.
"""
import sys
import uharfbuzz as hb
from fontTools.pens.recordingPen import RecordingPen

ARABIC = ['بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ', 'لا إله إلا الله', 'ببب', 'كتب', 'مرحبا بالعالم',
          'السلام عليكم ورحمة الله وبركاته', 'لأ لإ لآ لا', 'پچژگ ٹڈڑ ۂۃۀ ہۓے', 'ئۇيغۇرچە يېزىق',
          '٠١٢٣٤٥٦٧٨٩ ۰۱۲۳۴۵۶۷۸۹ ١٢:٣٤', 'ﷲ ﻻ ﺑ ﺒ ﺐ ﷺ', 'فِي ٱلْبَدْءِ كَانَ ٱلْكَلِمَةُ', 'هههه ةـة ۀ', 'كیف حالك؟ نعم، شكراً']
LGC = ['AV To Today office fi fl Wave Type', 'ΑΥΓΟ Жизнь', 'HIKMNOPTXY ΗΙΚΜΝΟΡΤΧΥ НІКМОРТХУ',
       'oο ɛε ɩι ƆϽ ϹⲤ ϛ Ͱ', 'ΤΑΥ ΧΑΟΣ ΟΥΤΟΠΙΑ ΗΜΕΡΑ ΚΑΙ ΜΙΑ ΝΥΞ', 'ΜΟΝΟ ΤΙΤΛΟΣ ΡΗΤΟΡ',
       'Ӏ І Ԑ Ɛ ⌧ ☒ ↵ ↲ ⮕ ➡ ⩕ ⨇ ༌ ་', 'The quick brown fox jumps over the lazy dog.', '1/2 3/4 H₂O x²',
       'ᶟ ᵌ ᶢ ᵍ ᶦ ᶥ ʹ ʹ ͻ ᴐ Ͱ Ⱶ']
CJK = ['漢字，中文。「引號」（括號）《書名》…——', '東京の春は美しい。ひらがなとカタカナ',
       '豈 更 車 賈 滑 串 句 龜 龜 契 金 喇 奈 懶 癩 羅 蘿 螺 裸 邏', '㒚曶 𠀀𠀁', '﨑髙 ₽ ₸ $ € ₿']
# intentional v1.2.0 changes (ZHT forms, new P0 glyphs, unmapped emoji): reported as INFO
EXPECTED = ['⁇⁈⁉㍿🈻𣟱𨓜', '⃀ ⃁', '⌚☕⚽🆗🈯']
OTHER = ['क्ष स्त्र क्षत्रिय स्त्री हिन्दी र्क द्ध ँ ं ़', 'ગુજરાતી ભાષા ક્ષ શ્રી ઁ ં ઼', 'ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਗੁਰਮੁਖੀ ਼',
         'ភាសាខ្មែរ ស្ត្រី កម្ពុជា', 'ພາສາລາວ ສະບາຍດີ', 'မြန်မာဘာသာ ကြည့်', 'สวัสดีครับ ภาษาไทย ที่นี่ ปั้น',
         'བོད་ཡིག བསྒྲུབས ཀྲྀ ༌', '֢֪ ॑ ॑']
LOCS = [(w, 100) for w in (100, 400, 700, 900)] + [(400, 80), (400, 120)]


def font(path, w, d):
    f = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    f.set_variations({'wght': w, 'wdth': d})
    return f


def outline(f, gid, cache):
    if gid not in cache:
        p = RecordingPen()
        f.draw_glyph_with_pen(gid, p)
        cache[gid] = tuple((op, tuple(tuple(round(c) for c in pt) for pt in args)) for op, args in p.value)
    return cache[gid]


def run(f, text, cache, lang=None, direction=None):
    b = hb.Buffer(); b.add_str(text); b.guess_segment_properties()
    if lang:
        b.language = lang
    if direction:
        b.direction = direction
    hb.shape(f, b, {})
    return [(i.cluster, p.x_advance, p.y_advance, p.x_offset, p.y_offset, outline(f, i.codepoint, cache))
            for i, p in zip(b.glyph_infos, b.glyph_positions)]


def main(old, new, rep=None):
    lines, fails, n = [], 0, 0
    for w, d in LOCS:
        fo, fn = font(old, w, d), font(new, w, d)
        co, cn = {}, {}
        for group, texts in (('Arabic', ARABIC), ('LGC', LGC), ('CJK', CJK), ('Other', OTHER), ('EXPECTED', EXPECTED)):
            for t in texts:
                for lang, dirn in ((None, None),) + ((('zh-Hant', None), ('ja', None), ('zh-Hant', 'ttb')) if group == 'CJK' else ()):
                    a, b = run(fo, t, co, lang, dirn), run(fn, t, cn, lang, dirn)
                    if group == 'EXPECTED':
                        if a != b and w == 400 and d == 100 and not lang:
                            lines.append('INFO intended change at wght 400: %s' % t)
                        continue
                    n += 1
                    if a != b:
                        notdef_new = sum(1 for x in b if not x[5])
                        diff = [k for k, (x, y) in enumerate(zip(a, b)) if x != y] if len(a) == len(b) else 'len %d vs %d' % (len(a), len(b))
                        lines.append('DIFF %-6s wght=%d wdth=%d %s %s %s: %s' % (group, w, d, lang or '', dirn or '', t, diff))
                        fails += 1
    lines.append('A/B shaping: %d runs compared, %d differ' % (n, fails))
    print('\n'.join(lines))
    if rep:
        open(rep, 'w').write('\n'.join(lines) + '\n')
    return fails


if __name__ == '__main__':
    sys.exit(1 if main(*sys.argv[1:]) else 0)
