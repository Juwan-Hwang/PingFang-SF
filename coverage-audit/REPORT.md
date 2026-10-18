# PingFang SF (Medium VF) — coverage audit (read-only)

Font: `work/out/PingFang-SF-Medium.ttf` — 62,782 glyphs, 52,994 cmap cps, axes wght+wdth, no cmap14, no morx.
Reference: Unicode 17.0 UCD (Blocks/UnicodeData/emoji-data from unicode.org/Public/17.0.0, saved in `audit/ucd/`).
Scripts: `audit/audit.py` (blocks + glyph hygiene + orphans), `gaps.py`/`gaps2.py` (charset & gap checks), `cost.py` (glyph cost per script via fontTools subsetter closure).

## 1. Top findings
1. **Chinese core is complete**: URO 20,992/20,992, Ext A 6,592/6,592, GB2312, GBK, 通用规范汉字表 8,105 (incl. all 196 non-BMP), Big5 (cp950), Big5-HKSCS-2004 (18,388), JIS X 0213:2004, Kana, Bopomofo, Kangxi/radicals, CJK strokes, CJK Symbols & Punctuation, Fullwidth forms, pinyin (incl. ü-tones, ḿ ǹ, combining marks), Vietnamese, IPA, Uyghur Arabic letters, Thai, Tibetan, Box drawing, Arrows, Math operators: all 0 missing.
2. **Hangul is the biggest everyday gap**: 0 of 11,172 syllables, 0 compat jamo (ㄱㅋ), 0 jamo; 34 circled/parenthesised Hangul missing. KS X 1001 subset alone = 2,350 syllables.
3. **~10,833 glyphs are SF Symbols (PUA)**: 8,447 PUA cps (8,329 in SPUA-B U+100000–1042F5 + 118 BMP PUA incl. U+F8FF). Removing all PUA except U+F8FF frees 10,833 glyphs (8,446 PUA-only glyphs + their private components). Unusable in normal text, dead weight on Windows, and SF Symbols has its own restrictive licence.
4. **1,891 orphan glyphs** (not reachable from cmap, any GSUB feature lookup, or composites; measured with the fontTools subsetter closure, all features kept). About 600 sit in the Arabic range (mostly composites of Arabic presentation forms / marks), about 650 in the PingFang area after the CJK compatibility ideographs (probably alternates that were only reachable through AAT/morx in the source), and the rest are Latin/Greek/Cyrillic/superscript leftovers. 1,212 are composites and 64 are empty. List: `audit/orphans.txt`. **Pruning them frees 1,891 slots** (62,782 → 60,891).
5. **Hygiene is clean**: no cmapped non-space character has an empty glyph (the only empty ones are U+F860/F861, Apple-internal PUA), nothing is mapped to `.notdef` or to a copy of the `.notdef` box, and no unassigned (Unicode 17) codepoints are mapped. 207 groups of identical outline+gvar+advance glyphs (216 redundant slots), almost all Latin↔Greek↔Cyrillic homoglyphs (H/Eta, o/omicron, ɛ/epsilon…), are low-value dedupe candidates.
6. **Small but visible gaps**: U+20C0 ⃀ (Som, Unicode 14) and U+20C1 (Saudi Riyal, Unicode 17); no glyph for default-ignorables: variation selectors FE00–FE0F (incl. FE0F) and E0100–E01EF, 180E, 2061–2064, 2066–2069 (bidi isolates), 061C, tag characters E0001/E0020–E007F, Hangul fillers 3164/FFA0/115F/1160. Modern shapers hide these anyway, but GDI and some apps show a box.
7. **65 Emoji_Presentation characters are monochrome glyphs in the font** (⌚⌛⏩–⏳ ☔☕ ♈–♓ ♿ ⚓⚡⚽⚾⛄⛅⛔⛪⛲⛳⛵⛺⛽ 🆎🆑–🆚 🈁🈚🈯🈲–🈺 🉐🉑). In apps that don't force the emoji presentation (DirectWrite/GDI on Windows) these show as black-and-white text instead of colour emoji. Other emoji (1F300–1FAFF, ✅❌ etc.) are absent, which is correct: they fall back to Apple Color Emoji / Segoe UI Emoji.
8. Overall: 44,543 of 159,801 assigned non-PUA Unicode 17 characters (27.9%). Blocks: 51 full, 47 partial, 245 missing (mostly historic/minority scripts). Odd singletons (1 cp each in Runic, Duployan, Sutton SignWriting, Ext I, Ext J, Arabic Suppl, Arabic Ext-A, Devanagari Ext) are harmless.

## 2. Where the slots go today (glyphs freed if a range is removed)
| Range | cps | glyphs |
|---|---|---|
| SF Symbols PUA (keep U+F8FF) | 8,446 | **10,833** |
| CJK Ext B–J (Source Han / TH-Hak supplement) | 8,674 | 8,678 |
| Orphans | — | **1,891** |
| Tibetan | 211 | 1,902 |
| Devanagari/Gurmukhi/Gujarati | 291 | 1,668 |
| Arabic (all blocks) | 433 | 675 |
| Khmer 315 · Thai+Lao 251 · Braille 256 · Greek Ext 233 · Myanmar 165 · Hebrew 133 | | |

## 3. Gaps by real-world value (Chinese-speaking user)
| Prio | Gap | Missing cps | Est. glyph cost | Open source |
|---|---|---|---|---|
| P0 | U+20C0, U+20C1 currency | 2 | 2 | Noto Sans (20C0); 20C1 draw (Unicode 17, few fonts yet) |
| P0 | Default-ignorables → one shared zero-width glyph | ~400 cps | 1–3 | none needed |
| P1 | Hangul KS X 1001 syllables + compat jamo + enclosed Hangul (㉠㈀) | 2,350+94+34 | ~2,480 | Noto Sans CJK KR / Source Han Sans K (OFL; CFF2→TT conversion), or Pretendard (OFL, variable TTF) |
| P1-alt | Full Hangul 11,172 + Jamo 256 + Jamo Ext A/B | ~11,500 | ~11,600 | same |
| P2 | Chinese-culture & UI symbols: 🉠–🉥 (6), Yijing hexagrams (64), Tai Xuan Jing (87), Counting rods (25), Ideographic Symbols 16FE0 (Nüshu/Tangut marks, 𖿰𖿱), Supplemental Punctuation (91), Misc Symbols & Arrows (~233 non-emoji), Misc Math Symbols-A/B (48+121), 🄍🄎🄏🅭🅮🅯 (6), Control Pictures (8), ⏿ | ~700 | ~700 (🉠–🉥 can be composites of existing 福禄寿喜財 glyphs and a circle) | Noto Sans Symbols / Symbols 2, Noto Sans Math (OFL) |
| P3 | China minority scripts: Mongolian (158 cps), Yi (1,220 + radicals), Lisu, New Tai Lue, Tai Le, Pollard Miao, Nüshu (397) | ~2,100 | ~3,500 (Mongolian ~1,000–1,500 with positional forms/FVS) | Noto Sans Mongolian, Yi, Lisu, New Tai Lue, Tai Le, Miao; Noto Traditional Nushu (all OFL) |
| P4 | Mathematical Alphanumerics (𝐀𝑨𝓐𝔸, used as "fancy text" in social-media names) | 996 | 996 | Noto Sans Math / STIX Two Math (OFL) |
| P4 | Myanmar completion (Shan/Mon), Arabic completion (Quranic marks, Arabic Suppl/Ext-A), Latin Ext-D (198), Khmer 4, Lao 1, Hebrew 1 | ~430 | ~1,000–1,500 incl. shaping forms | Noto Sans Myanmar/Arabic UI/Noto Sans |
| Leave to fallback | Remaining CJK Ext B (35,414), C (3,298), D (174), E (5,562), F (7,428), G (4,809), H (4,188), I (621), J (4,297); Tangut 6,959; Khitan 471; Hentaigana 306; colour emoji; Ethiopic, South-Indian, Sinhala, Armenian, Georgian, historic scripts | >80,000 | impossible | Plangothic 遍黑体 (OFL, Source-Han-based, covers Ext B–J) as a companion font |

## 4. Recommended plan (budget)
Current 62,782 / 65,535 → 2,753 free.

**Delete**
1. Orphans: −1,891 → 60,891 (4,644 free). Before deleting, A/B-test Arabic (and zh/ja `vert`/`locl`) shaping with `build/validate_shaping.py`. If ~600 Arabic orphans were meant to be reached through a lost lookup (the merged Arabic GSUB has ccmp/isol/init/medi/fina/rlig/dlig only, and 162 of 441 lookups are unreferenced), fix the merge instead of pruning those glyphs.
2. SF Symbols / PUA except U+F8FF: −10,833 → 50,058 (**15,477 free**).
3. Optional: drop the 65 Emoji_Presentation cmap entries (≤65 glyphs) so emoji always reach the colour emoji font; dedupe the 216 homoglyph duplicates by cmap aliasing (check kerning/locl first); Indic (−1,668) only if more room is needed (Nirmala UI / macOS fallbacks are good).

**Add (in order)**: P0 (≈5) → P1 KS Hangul (≈2,480) → P2 (≈700) → P3 (≈3,500) → P4 math alnum (≈1,000) = ≈7,700 → ~57,750 glyphs, ~7,800 free.
Full Hangul (+~9,100 beyond the KS subset) does **not** fit together with P3+P4. Choose either "full Hangul" or "minority scripts + math alnum". For a Chinese user I'd pick KS Hangul + P2/P3. KS X 1001 covers practically all modern Korean text, and Windows (Malgun Gothic) and macOS (Apple SD Gothic Neo) already fall back for the rest.

**Leave to OS fallback / companion font**: there are 159,801 assigned characters in Unicode 17 against a 65,535-glyph ceiling per font (the glyph ID is uint16), and CJK ideographs alone are ~98k. No single font can do it, and a TTC doesn't lift the per-face limit. Tofu-free in practice means **(a)** a companion font, for example "PingFang SF Ext" built from Plangothic for the remaining Ext B–J characters, plus **(b)** a proper fallback chain. On Windows that means a `HKLM\…\FontLink\SystemLink` entry for "PingFang SF" listing PingFang SF Ext, Segoe UI Emoji, Segoe UI Symbol, Malgun Gothic, Nirmala UI, Mongolian Baiti, Microsoft Yi Baiti, Microsoft Himalaya, Ebrima, SimSun-ExtB/ExtG. On macOS the system cascade already does this, and CSS can list the companion font.

## 5. Not verified / caveats
- The HKSCS check uses Python's big5hkscs (HKSCS-2004). The 2008/2016 additions were not checked. GB 18030-2022 levels were approximated by GBK + 通用规范 (both complete).
- Orphan detection follows GSUB features (all scripts), composites and cmap. Anything referenced only by tables the subsetter ignores would be miscounted, but this font has no morx/MATH/COLR/cmap14.
- Glyph costs for complex scripts are estimates from Noto glyph counts. Cost for scripts already in the font was measured exactly.

Files: `audit/blocks.csv` (per-block assigned/covered/missing/pct/status, Unicode 17), `audit/audit_raw.json`, `audit/orphans.txt`, `audit/charset_missing.json`, `audit/ucd/*`.
