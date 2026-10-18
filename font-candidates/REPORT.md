# Add-font source selection: PingFang SF gap fill (P1–P4)

Selection rule: visual match with PingFang/SF first, licence ignored, Apple fonts preferred, multi-weight/variable preferred.
Needed codepoints come from `needs.py` → `needs.json`. Each list is the codepoints still missing from `work/out/PingFang-SF-Medium.ttf`, with emoji excluded.
Coverage of every candidate is in `coverage.json` (`cov.py`). Glyph cost is measured with the fontTools subsetter closure (`cost.py` → `cost.json`).
Renders are in `render/` (`render.py`, `sheets.py`, `mathhybrid.py`, `fullline.py`). Each sheet sets candidate glyphs inside PingFang SF text at wght 100/400/700/900. CJK-like scripts match by em; Latin-like symbols and math match by cap height (the scale factor is printed on each sheet).

## Recommendations

| Cat | Pick | Weights → our wght 100–900 | Coverage of need | Est. glyphs |
|---|---|---|---|---|
| P1 Hangul | **Pretendard Variable** (wght 45–930) + **Noto Sans KR VF** for the 74 it lacks | fully variable | 2,404 + 74 = 2,478/2,478 | **2,479** |
| P2 Yijing, Tai Xuan Jing, Math A/B | **Apple Symbols** | static | 309 | 314 |
| P2 Misc Symbols & Arrows, Enclosed Alnum Suppl, 🉠–🉥, ⏿, rest of Math-A | **Segoe UI Symbol** | static | 265 | 306 |
| P2 Counting rods (whole block, one design) | **Noto Sans Symbols 2** | static | 25 | 25 |
| P2 Supplemental Punctuation | **Noto Sans VF** | wght 100–900 | 91 | 103 |
| P3 Mongolian | **Noto Sans Mongolian 3.002 (the copy macOS ships)** | static | 171 | 1,537 (GF 3.103 build = 3,154) |
| P3 Yi | **Noto Sans Yi** | static | 1,220 | 1,220 |
| P3 Lisu / New Tai Lue | **Noto Sans Lisu VF / New Tai Lue VF** | wght 400–700 | 49 / 83 | 49 / 83 |
| P3 Tai Le | **Noto Sans Tai Le** (Microsoft Tai Le R/B is nearly identical, also fine) | static | 35 | 35 |
| P3 Miao | **Noto Sans Miao** | static | 149 | 368 |
| P3 Nüshu | **Noto Sans Nushu** (sans; Traditional Nushu is brush style and clashes) | static | 396 | 396 |
| P4 Math alphanumerics | **Apple hybrid**: sans styles from SF Pro VF (344), serif bold/italic from New York VF (341), monospace from SF Mono VF (62), script/fraktur/double-struck + 2 leftovers from STIX Two Math (249) | 75% variable (bold = base +300) | 996/996 | 996 |
| P4 Latin Ext-D | **Noto Sans VF** | wght 100–900 (wdth only 62.5–100) | 187/198 | 202 |
| P4 Arabic (real letters only) | **SF Arabic VF** (228) + Noto Sans Arabic VF for 76 more | wght 1–1000 / 100–900 | 304/324 | ~830 |
| P4 Myanmar | **Noto Sans Myanmar VF** | wght 100–900 | 132/152 | 137 |

**Total ≈ 9,100 glyphs.** That is P1 2,479 + P2 748 + P3 3,688 + P4 ~2,165. It is about 1,400 over the 7,700 estimate but well inside the 15,477 slots freed by the cleanup (the result is about 59.2k glyphs).
If slots get tight, cut in this order: Arabic presentation forms (already excluded, would cost 565), the Mongolian GF build (use the macOS copy), Miao, then Arabic.

## Reasons and caveats per category

**P1 Hangul.** Apple SD Gothic Neo is the best visual match: same colour, size and rhythm as PingFang (see `render/hangul.png`). Its 9 weights cover exactly 100–900, but they are static CFF masters that are not interpolation-compatible: only 116 of 2,473 glyphs share contour structure across all 9 weights, and only 586 of 2,473 even between Thin and UltraLight. Turning it into a VF would mean compatibilising about 2,500 outlines by hand. Without that it can only go in as one frozen weight.
Pretendard looks almost identical to SD Gothic Neo in the renders. It was designed as a cross-platform SD Gothic Neo/SF-style face, is natively variable 45–930, and is glyf/gvar, so `vf_from_masters.py` can take it directly. It lacks 74 needed codepoints: archaic compat jamo U+3165–318E and parenthesised/circled syllables (㈎–㈛, ㉮–㉾). Noto Sans KR VF fills those, and it shares Pretendard's Source Han Sans lineage. SD Gothic Neo itself lacks 5 (U+321D, 321E, 327C–327E).
Noto Sans KR alone sets slightly larger and looser. Malgun Gothic has wide spacing and only Regular/Bold.
- If a frozen weight is acceptable, the alternative is Apple SD Gothic Neo Medium for the KS syllables (2,473 glyphs). I would still pick Pretendard for wght variation.

**P2.** No candidate symbol font is variable for these blocks. Noto Sans Symbols VF covers none of the needed codepoints, and SF Pro has none either. So these stay static, except Supplemental Punctuation from Noto Sans VF.
Apple Symbols is the Apple source and is complete for Yijing (64), Tai Xuan Jing (87) and Math-B (121), plus 37/48 of Math-A. It sets small and needs about ×1.31 to match cap height.
Segoe UI Symbol is the only font with near-complete Misc Symbols & Arrows (235/236) in a clean UI style that sits well beside SF arrows. It also has 🉠–🉥, the 7 enclosed alphanumerics and ⏿. 🉠–🉥 could instead be built as composites of PingFang's 福禄寿喜財 inside a circle.
Apple Symbols has only 18/25 counting rods, so the whole counting-rod block comes from Noto Sans Symbols 2 to keep it in one design.
**Gaps, 16 codepoints:** U+2427–2429 (control pictures), U+2B96, and Ideographic Symbols U+16FE0–16FE4 and 16FF0–16FF6. Of those, U+16FE1 (Nüshu iteration mark) is available from Noto Sans Nushu. The rest are Tangut/Khitan/Vietnamese marks; leave them to fallback.

**P3.** macOS itself ships these same Noto fonts, so Noto is effectively Apple's choice. The Windows alternatives look worse next to PingFang (see `render/minority_all.png`):
- Mongolian Baiti sets small and shapes differently.
- Microsoft Yi Baiti is thin and narrow.

Mongolian: use the macOS 3.002 build. It is the same design at half the glyph cost of the GF 3.103 build (1,537 vs 3,154 glyphs with positional/FVS forms). The GF build is only worth it if newer shaping fixes matter.
**Limitation:** Mongolian, Yi, Tai Le, Miao and Nüshu are Regular-only, so they stay a fixed weight across wght 100–900. Lisu and New Tai Lue only vary between 400 and 700 and clamp outside that.
Synthetic 100/900 masters (outline offset) are possible but would be my own invention. I have not tested them.

**P4 math alphanumerics.** All four single-font candidates are serif-math designs: STIX Two Math, Cambria Math, Noto Sans Math, Segoe UI Symbol. Their sans and mono rows do not look like SF (`render/mathalnum.png`).
The hybrid (`render/mathalnum_apple_hybrid.png`) makes 𝗦𝗮𝗻𝘀 rows real SF Pro, serif rows New York and 𝚖𝚘𝚗𝚘 SF Mono, so "fancy text" in usernames matches the system UI. It can also vary: build "bold" glyphs from the source instanced at about base +300.
Hybrid caveats:
- New York's wght axis starts at 400, so serif-regular forms stay at 400 below wght 400.
- SF Mono's axis starts at about 295.
- The 249 STIX glyphs are static.

**P4 Arabic.** SF Arabic is the closest match to the existing MiSans Arabic: near-identical proportions and weight (`render/arabic_fullline.png`). It covers 228 of the 324 missing real letters (Urdu/Sindhi/Kurdish/Quranic, Arabic Supplement, Ext-A/B). Noto Sans Arabic adds 76 more, and 20 are in neither.
Skip the 504 presentation forms U+FB50–FEFF. Shaping doesn't need them, and Noto would charge 565 glyphs for them.
The new letters need GSUB isol/init/medi/fina entries merged into the existing Arabic lookups.

**P4 Myanmar / Latin Ext-D.** In `render/myanmar_fullline.png` Noto Sans Myanmar VF is practically the same design as the existing MiSans Myanmar, so it is a seamless fill. It covers Shan/Mon/Karen/Ext-A/Ext-B (132). Ext-C U+116D0–116E3 (Unicode 16 digits, 20 codepoints) is in no candidate.
Noto Sans VF covers 187/198 of Latin Ext-D, varies 100–900, and its wdth tops out at 100, so it can't follow our wdth 120. Missing there: A7CB–A7CF, A7D2, A7D4, A7DA–A7DC, A7F1 (Unicode 16/17).

**Render caveat.** `render/arabic.png` and `render/myanmar.png` set each run in its own font, so joining and marks break across runs. Judge those two scripts from the `*_fullline.png` sheets instead.

## Files (all under `work/addfont/`)
- `src/osf/`: macOS Tahoe and Windows 11 fonts from github.com/daijro/os-fonts (raw.githubusercontent.com/daijro/os-fonts/master/...). Includes AppleSDGothicNeo.ttc (9 weights × 2), Apple Symbols, STIX Two Math, NewYork/Italic, SFNS/SFNSMono, SFArabic, SFCompact, macOS Noto (Mongolian, Yi, Lisu, New Tai Lue, Tai Le, Miao, Myanmar ttc), Malgun, Mongolian Baiti, MS Yi Baiti, MS New Tai Lue R/B, MS Tai Le R/B, Segoe UI Symbol, Cambria Math, and Noto (Traditional) Nushu.
- `src/apple/`: official developer.apple.com DMGs (`devimages-cdn.apple.com/design/resources/download/{SF-Arabic,NY,SF-Mono}.dmg`), extracted to `SF-Arabic/` (SF-Arabic.ttf VF wght 1–1000 + Rounded), `NY/` (NewYork.ttf and NewYorkItalic.ttf VF; static optical-size OTFs deleted) and `SF-Mono/` (12 static OTFs). SF-Compact.dmg was downloaded and deleted (177 MB, not needed). SF Pro VF is already in `work/src/sf/`.
- `src/gf/`: google/fonts main. Noto Sans KR[wght], Noto Sans[wdth,wght], Symbols[wght], Symbols2, Math, Lisu[wght], NewTaiLue[wght], Myanmar[wdth,wght], Arabic[wdth,wght], Yi, Mongolian, Nushu, Miao, TaiLe.
- `src/pretendard/public/variable/PretendardVariable.ttf`: orioncactus/pretendard v1.3.9 release.
- `tmp/`: de-hinted copies of the Microsoft fonts. Render use only, because FreeType raised "invalid reference" on their bytecode.
- `render/`: hangul, symbols, minority_*.png + minority_all.png, mathalnum, mathalnum_apple_hybrid, latinextd, arabic(_fullline), myanmar(_fullline), p4_misc.
- Tooling note: the sandbox has no 7z and no root. DMGs were unpacked with the static 7-Zip 24.09 arm64 binary from github.com/ip7z/7zip, installed at `~/bin/7zz`.
