# PingFang SF: fill plan to 65,435 glyphs (single font, no companion)

Inputs: `audit/REPORT.md`, `addfont/REPORT.md` (+ needs/cost/coverage JSON), the cleanup result `render_cleanup/step8_report.json`, Unicode 17 UCD + Unihan 17.
Output: this file and `fillplan.json`, which lists every codepoint per tranche with its source font file path.
Scripts are in `work/fillplan/`: `scan2.py`/`scanko.py` (corpus scan), `agg.py`, `costs.py` (subsetter-closure glyph costs), `rank.py` (greedy), `condense.py`, `emit.py`.
Nothing in the repo or in `sh-vf` was touched.

## 0. Bottom line (all calls made; nothing left open)

1. **The baseline is 50,102 glyphs, not ~47.3k.** That is the actual cleanup output (`step8_report.json`: glyphs_out 50,102, free 15,433). So addfont + fill together have **15,333 slots** to reach 65,435 (100 spare). The plan uses 15,332 (cut line at **65,434**).
2. **Ranking method.** Each candidate is scored by real-text frequency, measured by scanning Wikipedia dumps for every character this font lacks. The score is the number of pages it appears on, weighted by an assumed reading mix for a Chinese-speaking user (zh 71%, en 20%, ko 4%, yue 4%, classical 1%). Candidates are then filled greedily by **value per glyph**.
   - Shaped scripts go in as whole units. Their glyph cost is the measured closure, including GSUB/GPOS forms.
   - Everything else (Han, Hangul, symbols, Arabic letters) goes in per character.
   - The addfont picks were re-ranked in the same pool. Sensitivity runs (ko 1–10%, en up to 40%) change only the last ~1,000 slots.
3. **Result:** this removes **99.96% of the measured missing-character page occurrences in zhwiki**, 99.5% in enwiki, 99.7% in yuewiki and 99.997% in kowiki. Residual non-covered Hangul is 0.003% of Korean syllable tokens.
4. **Decisions I made:**
   - **Hangul:** Pretendard VF, not all 11,172 syllables. Take all 2,350 KS + the 948 non-KS syllables actually seen + 128 jamo/enclosed = 3,426. The other 7,874 non-KS syllables appear only on list pages (kowiki df ≤ 1).
   - **CJK Ext B–J:** Plangothic (static, Source-Han-derived), only the **4,376** characters seen in text. Every HKSCS-2016, Macao, IICore and UnihanCore2020 character is *already* in the font, so standards lists give no further signal.
   - **Compatibility Ideographs Supplement: none.** NFC normalises them away and there were 0 hits.
   - **Old-Hangul jamo: none.** Costs 2,214 glyphs for almost no value.
   - **Indic:** **Apple SF India** (variable) for Bengali, Tamil, Malayalam, Kannada and Odia. **Telugu is the first item below the cut** (873 glyphs).
   - **Other new scripts:** Apple SF Armenian and SF Georgian, Apple Kefa III (Ethiopic), plus Noto for Sinhala, Syriac, Thaana, Tifinagh, Coptic and Sundanese.
   - **Addfont re-check:** keep Mongolian, Lisu, Tai Le, New Tai Lue, Myanmar and most of Math alnum. **Drop Yi (1,220), Nüshu (396), Miao (368)** and 472 of the 706 P2 symbols, because the evidence for them is near zero. Arabic is now **per letter** (149 letters ≈ 371 glyphs) instead of the whole 830-glyph block.
5. **Needs user login: none.** Every preferred source was downloaded without an account:
   - Apple fonts from the daijro/os-fonts GitHub mirror and Apple's public developer DMGs.
   - Plangothic from its GitHub release.
   - Noto from google/fonts.

## 1. Evidence base

| Corpus (2026-10 dumps, multistream slices) | Pages | Text |
|---|---|---|
| zhwiki: 8 × 200 MB compressed slices spread over the file | 1,836,187 | 6.6 GB |
| kowiki: 4 slices | 515,306 | 1.5 GB |
| enwiki: 2 slices | 132,512 | 0.64 GB |
| zh_yuewiki: full | 309,190 | 0.6 GB |
| zh_classicalwiki: first 30 MB | 83,012 | 0.11 GB |

- **Metric.** For every codepoint not in the current font we count document frequency (pages containing it). We use page frequency, not token counts, so one table-heavy page cannot dominate.
- **List-page noise floor.** We subtract a floor where whole-block listing pages exist:
  - yue: 3. Two pages list ~52.6k Ext chars, which gives 52,575 chars at df = 2.
  - classical: 2.
  - ko: 1. A syllable-table page gives 8,119 non-KS syllables at df = 1.
- **Script units.** A script's value is its most frequent letter's page frequency (a lower bound of "page contains the script").
- **What the data says:**
  - CJK Ext. The font already covers about 79% of Ext-plane tokens in zhwiki. The missing Ext chars total 1,873 distinct and occur ~9 times per million Han tokens. All Unihan kIICore / kUnihanCore2020 / kIRG_HSource (HKSCS-2016) / kIRG_MSource (Macao) Ext characters are **already covered** (0 missing).
  - Korean. Non-KS syllables are **0.0082%** of syllable tokens in kowiki. Only 908 have df ≥ 2, and the top ones are 슌 됭 푈 녓 몐 솁 웻 쫒 됬 똠 뷁 햏 쌰…. OpenSubtitles frequency lists were unusable here: they are EUC-KR-derived and contain 0 non-KS syllables.
  - zhwiki pages very often contain Hangul (Korean names) and Mongolian/Tamil/Armenian/Georgian/Bengali (native-script names). That is why these rank high for a Chinese reader.
- **Caveats.**
  - Wikipedia is wikitext, not the open web. Social-media "fancy text" (math alnum) is probably under-counted, and Mongolian/Yi on government sites too.
  - The en weight is low-sample (132k pages).
  - Ranks in the bottom ~1,500 slots rest on df of 1–2 and are close to noise. Treat that band as "reasonable fill", not "proven".

## 2. Single ranked table (greedy fill; ✅ = in plan; cut line at 65,434)

Baseline 50,102 → each row adds its glyphs.
- **Value band** is value per glyph in "expected page occurrences per million pages read".
- **Evidence** is the largest raw page count of any codepoint in the row (zh of 1.84M pages, ko of 515k, en of 133k).
- Han and Hangul tranches are per-character slices of one block grouped by evidence band. Whole scripts are one row.
- Per-codepoint lists and exact source paths are in `fillplan.json`.

| # | In | Tranche | Value band (per glyph, per 1M pages) | cps | glyphs | Cumulative | Max page df (sample pages) | Source font | VF? | Shaping |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ✅ | Hangul KS X 1001 | A ≥100 | 1048 | 1048 | 51150 | zh 6572 · ko 396655 · en 80 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 2 | ✅ | Hangul compat jamo / enclosed | A ≥100 | 6 | 6 | 51156 | zh 96 · ko 4616 · en 2 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 3 | ✅ | Hangul KS X 1001 | B 10–100 | 522 | 522 | 51678 | zh 109 · ko 1278 · en 2 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 4 | ✅ | Hangul non-KS | B 10–100 | 2 | 2 | 51680 | zh 3 · ko 828 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 5 | ✅ | Han Ext B-J | B 10–100 | 10 | 10 | 51690 | zh 40 · ko 1 · en 0 | PlangothicP1-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 6 | ✅ | P2 symbols (addfont) | B 10–100 | 5 | 5 | 51695 | zh 100 · ko 63 · en 10 | Apple Symbols.ttf, seguisym6_24.ttf | static (Supplemental Punct. from Noto Sans VF) | none |
| 7 | ✅ | Hangul compat jamo / enclosed | B 10–100 | 33 | 33 | 51728 | zh 81 · ko 673 · en 1 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 8 | ✅ | Mahjong | B 10–100 | 4 | 4 | 51732 | zh 56 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 9 | ✅ | ToneLetters | B 10–100 | 1 | 1 | 51733 | zh 18 · ko 5 · en 5 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 10 | ✅ | Arabic additions (per letter) | B 10–100 | 1 | 3 | 51736 | zh 74 · ko 13 · en 7 | SF-Arabic.ttf | variable (SF Arabic / Noto) | add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py) |
| 11 | ✅ | Music | B 10–100 | 2 | 2 | 51738 | zh 29 · ko 39 · en 2 | NotoMusic-Regular.ttf | static | none |
| 12 | ✅ | Latin Ext-D (addfont) | B 10–100 | 1 | 1 | 51739 | zh 17 · ko 6 · en 3 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 13 | ✅ | addfont Math alnum | B 10–100 | 62 | 62 | 51801 | zh 1796 · ko 2 · en 0 | mathhybrid.py | mostly variable (hybrid) | none |
| 14 | ✅ | Hangul KS X 1001 | C 1–10 | 384 | 384 | 52185 | zh 10 · ko 127 · en 2 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 15 | ✅ | Music | C 1–10 | 3 | 3 | 52189 | zh 15 · ko 6 · en 0 | NotoMusic-Regular.ttf | static | none |
| 16 | ✅ | Mahjong | C 1–10 | 1 | 1 | 52190 | zh 9 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 17 | ✅ | Cards | C 1–10 | 1 | 1 | 52191 | zh 8 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 18 | ✅ | Domino | C 1–10 | 1 | 1 | 52192 | zh 8 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 19 | ✅ | Georgian | whole unit | 94 | 94 | 52286 | zh 534 · ko 155 · en 34 | SFGeorgian.ttf | variable (SF Georgian wght 1–1000) | none |
| 20 | ✅ | CtrlOCR | C 1–10 | 3 | 3 | 52289 | zh 3 · ko 2 · en 2 | NotoSansSymbols2-Regular.ttf | static | none |
| 21 | ✅ | Hangul compat jamo / enclosed | C 1–10 | 60 | 60 | 52349 | zh 17 · ko 36 · en 0 | NotoSansKR[wght].ttf, PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 22 | ✅ | Hangul non-KS | C 1–10 | 94 | 94 | 52443 | zh 17 · ko 120 · en 1 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 23 | ✅ | Latin Ext-D (addfont) | C 1–10 | 15 | 15 | 52458 | zh 13 · ko 4 · en 2 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 24 | ✅ | P2 symbols (addfont) | C 1–10 | 24 | 25 | 52483 | zh 13 · ko 3 · en 2 | Apple Symbols.ttf, NotoSans[wdth,wght].ttf, seguisym6_24.ttf | static (Supplemental Punct. from Noto Sans VF) | none |
| 25 | ✅ | Arabic additions (per letter) | C 1–10 | 20 | 46 | 52529 | zh 32 · ko 13 · en 5 | SF-Arabic.ttf | variable (SF Arabic / Noto) | add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py) |
| 26 | ✅ | Han Ext B-J | C 1–10 | 342 | 342 | 52871 | zh 24 · ko 5 · en 1 | PlangothicP1-Regular.ttf, PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 27 | ✅ | Tamil | whole unit | 72 | 170 | 53041 | zh 590 · ko 149 · en 82 | SFIndia.ttc#7 | variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar | Indic tml2: akhn + GPOS marks |
| 28 | ✅ | Alchemical | C 1–10 | 3 | 3 | 53044 | zh 7 · ko 1 · en 1 | Apple Symbols.ttf | static | none |
| 29 | ✅ | ToneLetters | C 1–10 | 11 | 11 | 53055 | zh 7 · ko 0 · en 1 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 30 | ✅ | Armenian | whole unit | 94 | 161 | 53216 | zh 548 · ko 145 · en 51 | SFArmenian.ttf | variable (SF Armenian wght 1–1000) | liga only |
| 31 | ✅ | CyrExt | C 1–10 | 50 | 51 | 53268 | zh 10 · ko 7 · en 1 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 32 | ✅ | Hentaigana | C 1–10 | 3 | 3 | 53271 | zh 5 · ko 7 · en 0 | PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 33 | ✅ | LatinExtE | C 1–10 | 1 | 1 | 53272 | zh 0 · ko 0 · en 1 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 34 | ✅ | CDMExt | C 1–10 | 1 | 1 | 53273 | zh 0 · ko 0 · en 1 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 35 | ✅ | Ornamental | C 1–10 | 1 | 1 | 53274 | zh 3 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 36 | ✅ | Hangul compat jamo / enclosed | D 0.3–1 | 28 | 28 | 53302 | zh 2 · ko 3 · en 0 | NotoSansKR[wght].ttf | variable (Pretendard wght 45–930) | none |
| 37 | ✅ | ToneLetters | D 0.3–1 | 8 | 8 | 53310 | zh 2 · ko 2 · en 0 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 38 | ✅ | CtrlOCR | D 0.3–1 | 1 | 1 | 53311 | zh 2 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 39 | ✅ | Hentaigana | D 0.3–1 | 7 | 7 | 53318 | zh 2 · ko 3 · en 0 | PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 40 | ✅ | Malayalam | whole unit | 118 | 193 | 53511 | zh 148 · ko 27 · en 39 | SFIndia.ttc#5 | variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar | Indic mlm2: akhn/pref/pstf/rphf/pres + GPOS |
| 41 | ✅ | addfont P3_lisu | whole unit | 49 | 49 | 53560 | zh 76 · ko 1 · en 0 | NotoSansLisu[wght].ttf | variable 400–700 | none |
| 42 | ✅ | Hangul KS X 1001 | D 0.3–1 | 148 | 148 | 53708 | zh 2 · ko 13 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 43 | ✅ | Hangul non-KS | D 0.3–1 | 200 | 200 | 53908 | zh 2 · ko 13 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 44 | ✅ | Arabic additions (per letter) | D 0.3–1 | 52 | 94 | 54002 | zh 6 · ko 5 · en 1 | NotoSansArabic[wdth,wght].ttf, SF-Arabic.ttf | variable (SF Arabic / Noto) | add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py) |
| 45 | ✅ | LatinExtE | D 0.3–1 | 6 | 6 | 54008 | zh 2 · ko 0 · en 0 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 46 | ✅ | CyrExt | D 0.3–1 | 70 | 72 | 54079 | zh 2 · ko 3 · en 0 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 47 | ✅ | addfont Math alnum | D 0.3–1 | 423 | 423 | 54502 | zh 157 · ko 6 · en 1 | mathhybrid.py | mostly variable (hybrid) | none |
| 48 | ✅ | Latin Ext-D (addfont) | D 0.3–1 | 57 | 58 | 54561 | zh 2 · ko 4 · en 0 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 49 | ✅ | Ornamental | D 0.3–1 | 45 | 45 | 54606 | zh 2 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 50 | ✅ | ArrowsC | D 0.3–1 | 136 | 136 | 54742 | zh 2 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 51 | ✅ | Han Ext B-J | D 0.3–1 | 1870 | 1870 | 56612 | zh 2 · ko 5 · en 0 | PlangothicP1-Regular.ttf, PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 52 | ✅ | P2 symbols (addfont) | D 0.3–1 | 203 | 215 | 56827 | zh 2 · ko 5 · en 0 | Apple Symbols.ttf, NotoSans[wdth,wght].ttf, seguisym6_24.ttf | static (Supplemental Punct. from Noto Sans VF) | none |
| 53 | ✅ | Music | D 0.3–1 | 4 | 4 | 56831 | zh 2 · ko 1 · en 0 | NotoMusic-Regular.ttf | static | none |
| 54 | ✅ | Bengali | whole unit | 94 | 629 | 57460 | zh 436 · ko 171 · en 49 | SFIndia.ttc#0 | variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar | Indic bng2: full akhn/rphf/blwf/half/pstf/init/pres + GPOS |
| 55 | ✅ | GeomExt | D 0.3–1 | 85 | 85 | 57545 | zh 2 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 56 | ✅ | Mahjong | D 0.3–1 | 38 | 38 | 57583 | zh 1 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 57 | ✅ | Cards | D 0.3–1 | 4 | 4 | 57587 | zh 1 · ko 1 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 58 | ✅ | Alchemical | D 0.3–1 | 5 | 5 | 57592 | zh 1 · ko 0 · en 0 | Apple Symbols.ttf | static | none |
| 59 | ✅ | addfont P3_mongolian | whole unit | 171 | 1537 | 59129 | zh 1146 · ko 117 · en 5 | NotoSansMongolian-Regular.ttf | static | Mongolian: isol/init/medi/fina + FVS1–4 + rlig, vertical |
| 60 | ✅ | addfont P3_taile | whole unit | 35 | 35 | 59164 | zh 23 · ko 0 · en 1 | NotoSansTaiLe-Regular.ttf | static | none |
| 61 | ✅ | Thaana | whole unit | 50 | 52 | 59216 | zh 27 · ko 12 · en 1 | NotoSansThaana[wght].ttf | variable (Noto) | GPOS marks |
| 62 | ✅ | Sinhala | whole unit | 91 | 304 | 59520 | zh 107 · ko 60 · en 19 | NotoSansSinhala[wdth,wght].ttf | variable (Noto) | Indic sinh: akhn/rphf/vatu/pres + GPOS |
| 63 | ✅ | Tifinagh | whole unit | 59 | 142 | 59662 | zh 56 · ko 17 · en 7 | NotoSansTifinagh-Regular.ttf | static | none (optional ligatures) |
| 64 | ✅ | Kannada | whole unit | 90 | 594 | 60256 | zh 65 · ko 29 · en 66 | SFIndia.ttc#4 | variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar | Indic knd2: rphf/blwf/pres/rclt + GPOS |
| 65 | ✅ | Syriac | whole unit | 77 | 200 | 60456 | zh 76 · ko 28 · en 6 | NotoSansSyriac[wght].ttf | variable (Noto) | joining (isol/init/medi/fina/rlig) + marks |
| 66 | ✅ | Hangul KS X 1001 | E 0.1–0.3 | 113 | 113 | 60569 | zh 0 · ko 4 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 67 | ✅ | Hangul non-KS | E 0.1–0.3 | 213 | 213 | 60782 | zh 0 · ko 4 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 68 | ✅ | Arabic additions (per letter) | E 0.1–0.3 | 75 | 225 | 61007 | zh 2 · ko 3 · en 0 | NotoSansArabic[wdth,wght].ttf, SF-Arabic.ttf | variable (SF Arabic / Noto) | add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py) |
| 69 | ✅ | Hangul compat jamo / enclosed | E 0.1–0.3 | 1 | 1 | 61008 | zh 0 · ko 3 · en 0 | NotoSansKR[wght].ttf | variable (Pretendard wght 45–930) | none |
| 70 | ✅ | Han Ext B-J | E 0.1–0.3 | 2093 | 2093 | 63101 | zh 0 · ko 4 · en 0 | PlangothicP1-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 71 | ✅ | addfont Math alnum | E 0.1–0.3 | 255 | 255 | 63356 | zh 31 · ko 39 · en 1 | mathhybrid.py | mostly variable (hybrid) | none |
| 72 | ✅ | Coptic | whole unit | 123 | 123 | 63479 | zh 23 · ko 6 · en 5 | NotoSansCoptic-Regular.ttf | static | none |
| 73 | ✅ | Ethiopic | whole unit | 495 | 503 | 63982 | zh 58 · ko 39 · en 19 | KefaIII.ttf | variable (Kefa III wght 300–800) | none |
| 74 | ✅ | Odia | whole unit | 91 | 509 | 64491 | zh 45 · ko 12 · en 14 | SFIndia.ttc#6 | variable CFF2 (SF India wght 1–1000) → convert to glyf/gvar | Indic ory2: rphf/blwf/pstf/pres + GPOS |
| 75 | ✅ | Han Ext B-J | F <0.1 | 43 | 43 | 64534 | zh 0 · ko 2 · en 0 | PlangothicP1-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 76 | ✅ | Hangul non-KS | F <0.1 | 439 | 439 | 64973 | zh 0 · ko 2 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 77 | ✅ | CtrlOCR | F <0.1 | 1 | 1 | 64974 | zh 0 · ko 2 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 78 | ✅ | Hentaigana | F <0.1 | 3 | 3 | 64977 | zh 0 · ko 2 · en 0 | PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 79 | ✅ | Hangul KS X 1001 | F <0.1 | 114 | 114 | 65091 | zh 0 · ko 2 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 80 | ✅ | addfont P4_myanmar | whole unit | 152 | 137 | 65228 | zh 19 · ko 3 · en 2 | NotoSansMyanmar[wdth,wght].ttf | variable (Noto) | merge into existing mym2 lookups |
| 81 | ✅ | P2 symbols (addfont) | F <0.1 | 2 | 2 | 65230 | zh 0 · ko 2 · en 0 | seguisym6_24.ttf | static (Supplemental Punct. from Noto Sans VF) | none |
| 82 | ✅ | Music | F <0.1 | 1 | 1 | 65231 | zh 0 · ko 2 · en 0 | NotoMusic-Regular.ttf | static | none |
| 83 | ✅ | Sundanese | whole unit | 72 | 78 | 65309 | zh 6 · ko 1 · en 2 | NotoSansSundanese[wght].ttf | variable (Noto) | USE: marks |
| 84 | ✅ | addfont P3_newtailue | whole unit | 83 | 83 | 65392 | zh 14 · ko 2 · en 0 | NotoSansNewTaiLue[wght].ttf | variable 400–700 | USE (simple) |
| 85 | ✅ | Arabic additions (per letter) | F <0.1 | 1 | 3 | 65395 | zh 0 · ko 2 · en 0 | SF-Arabic.ttf | variable (SF Arabic / Noto) | add init/medi/fina/isol + mark anchors into existing Arabic GSUB/GPOS (merge_arabic_gsub.py) |
| 86 | ✅ | Hangul KS X 1001 | G 0 | 21 | 21 | 65416 | zh 0 · ko 1 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 87 | ✅ | Han Ext B-J | G 0 | 18 | 18 | 65434 | zh 0 · ko 1 · en 0 | PlangothicP1-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |

**── CUT LINE: 65,434 glyphs (101 spare under 65,535) ──**

First 30 rows below the cut, in order. This is the order to add them if any slot frees up later, e.g. if SF India's CFF2→glyf conversion or the Mongolian merge comes in cheaper:

| # | In | Tranche | Value band (per glyph, per 1M pages) | cps | glyphs | Cumulative | Max page df (sample pages) | Source font | VF? | Shaping |
|---|---|---|---|---|---|---|---|---|---|---|
| 88 | — | Telugu | whole unit | 100 | 873 | 66307 | zh 68 · ko 22 · en 24 | SFIndia.ttc#8 | static | none |
| 89 | — | addfont Math alnum | F <0.1 | 216 | 216 | 66523 | zh 12 · ko 3 · en 1 | mathhybrid.py | mostly variable (hybrid) | none |
| 90 | — | NKo | whole unit | 62 | 166 | 66689 | zh 15 · ko 5 · en 1 | NotoSansNKo-Regular.ttf | static | none |
| 91 | — | UCAS | whole unit | 726 | 742 | 67431 | zh 25 · ko 6 · en 5 | NotoSansCanadianAboriginal[wght].ttf | static | none |
| 92 | — | Javanese | whole unit | 91 | 391 | 67822 | zh 14 · ko 4 · en 7 | NotoSansJavanese[wght].ttf | static | none |
| 93 | — | Cherokee | whole unit | 172 | 258 | 68080 | zh 15 · ko 3 · en 1 | NotoSansCherokee[wght].ttf | static | none |
| 94 | — | OlChiki | whole unit | 48 | 48 | 68128 | zh 3 · ko 1 · en 0 | NotoSansOlChiki[wght].ttf | static | none |
| 95 | — | Glagolitic | whole unit | 132 | 132 | 68260 | zh 7 · ko 2 · en 0 | NotoSansGlagolitic-Regular.ttf | static | none |
| 96 | — | Cham | whole unit | 83 | 107 | 68367 | zh 3 · ko 14 · en 0 | NotoSansCham[wght].ttf | static | none |
| 97 | — | Meetei | whole unit | 79 | 83 | 68450 | zh 4 · ko 2 · en 0 | NotoSansMeeteiMayek[wght].ttf | static | none |
| 98 | — | Georgian-rest | whole unit | 80 | 126 | 68576 | zh 5 · ko 1 · en 0 | NotoSansGeorgian[wdth,wght].ttf | static | none |
| 99 | — | Balinese | whole unit | 124 | 345 | 68921 | zh 7 · ko 3 · en 1 | NotoSansBalinese[wght].ttf | static | none |
| 100 | — | PhagsPa | whole unit | 56 | 344 | 69265 | zh 10 · ko 3 · en 0 | NotoSansPhagsPa-Regular.ttf | static | none |
| 101 | — | TaiViet | whole unit | 72 | 72 | 69337 | zh 2 · ko 0 · en 0 | NotoSansTaiViet-Regular.ttf | static | none |
| 102 | — | Adlam | whole unit | 88 | 299 | 69636 | zh 6 · ko 4 · en 0 | NotoSansAdlam[wght].ttf | static | none |
| 103 | — | HangulJamo | whole unit | 357 | 2214 | 71850 | zh 18 · ko 112 · en 0 | SourceHanSans-VF.ttf | static | none |
| 104 | — | addfont P3_yi | whole unit | 1220 | 1220 | 73070 | zh 12 · ko 9 · en 0 | NotoSansYi-Regular.ttf | static | none |
| 105 | — | TaiTham | whole unit | 127 | 777 | 73847 | zh 8 · ko 0 · en 0 | NotoSansTaiTham[wght].ttf | static | none |
| 106 | — | Vai | whole unit | 300 | 300 | 74147 | zh 2 · ko 0 · en 0 | NotoSansVai-Regular.ttf | static | none |
| 107 | — | addfont P3_nushu | whole unit | 396 | 396 | 74543 | zh 1 · ko 0 · en 0 | NotoSansNushu-Regular.ttf | static | none |
| 108 | — | Han Ext B-J | G 0 | 61415 | 61415 | 135958 | zh 0 · ko 1 · en 0 | PlangothicP1-Regular.ttf, PlangothicP2-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 109 | — | Han compat (supplement) | G 0 | 477 | 477 | 136435 | zh 0 · ko 0 · en 0 | PlangothicP1-Regular.ttf | STATIC (Plangothic Regular 400; no gvar) | none |
| 110 | — | Hangul non-KS | G 0 | 7874 | 7874 | 144309 | zh 0 · ko 1 · en 0 | PretendardVariable.ttf | variable (Pretendard wght 45–930) | none |
| 111 | — | P2 symbols (addfont) | G 0 | 472 | 500 | 144810 | zh 0 · ko 1 · en 0 | Apple Symbols.ttf, NotoSansSymbols2-Regular.ttf, NotoSans[wdth,wght… | static (Supplemental Punct. from Noto Sans VF) | none |
| 112 | — | Latin Ext-D (addfont) | G 0 | 125 | 127 | 144937 | zh 0 · ko 1 · en 0 | NotoSans[wdth,wght].ttf | variable (Noto Sans wght 100–900) | none |
| 113 | — | Cards | G 0 | 76 | 76 | 145013 | zh 0 · ko 1 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 114 | — | Domino | G 0 | 99 | 99 | 145112 | zh 0 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 115 | — | Chess | G 0 | 98 | 98 | 145210 | zh 0 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 116 | — | GeomExt | G 0 | 5 | 5 | 145215 | zh 0 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |
| 117 | — | ArrowsC | G 0 | 14 | 14 | 145229 | zh 0 · ko 0 · en 0 | NotoSansSymbols2-Regular.ttf | static | none |

## 3. What the plan adds, by family (15,332 glyphs)

| Family | cps | glyphs | Source (decision, reason) | VF? |
|---|---|---|---|---|
| Han Ext B–J, seen in text | 4,376 | 4,376 | **Plangothic P1/P2 2.9.5795**. It is Source-Han-derived, so it matches the existing SHS/TH-Hak Ext glyphs better than TH-Hak's remaining gaps or MiSans L3. TH-Hak and SHS VF have **0** of the missing chars, and Plangothic has all of them. | static (Regular 400, UPM 1000), like the current Ext glyphs |
| Hangul KS X 1001 (all) | 2,350 | 2,350 | **Pretendard VF** (has all 11,172). It looks closest to SD Gothic Neo/PingFang and is glyf + gvar. Addfont's choice is confirmed. | wght 45–930 |
| Hangul non-KS, seen (df ≥ 2 ko or any zh) | 948 | 948 | Pretendard VF | var |
| Hangul compat jamo + enclosed | 128 | 128 | Pretendard + Noto Sans KR VF for 74 | var |
| Mongolian | 171 | 1,537 | Noto Sans Mongolian 3.002 (the macOS copy, half the glyphs of the GF build). zhwiki has Mongolian on 1,146 sample pages. | static |
| Math alphanumerics (740 of 996) | 740 | 740 | Addfont Apple hybrid (SF Pro / New York / SF Mono + STIX). The 256 left out are the plain/italic/bold-italic sans-serif styles and 40 Greek variant symbols, which had near-zero hits. | ~75% var |
| Bengali, Tamil, Malayalam, Kannada, Odia | 465 | 2,095 | **Apple SF India** (SF Bangla/Tamil/Malayalam/Kannada/Odia). Native SF design, wght 1–1000, OpenType GSUB/GPOS present (not morx). It is CFF2, so it must be converted to quadratic glyf/gvar. | var after conversion |
| Ethiopic | 495 | 503 | **Apple Kefa III** VF. It is Apple's own and glyf. | wght 300–800 |
| Sinhala, Syriac, Thaana, Sundanese | 290 | 634 | Noto Sans VF builds. No Apple sans exists (Sinhala Sangam is static and old). | var |
| Armenian, Georgian | 188 | 255 | **Apple SF Armenian / SF Georgian** VF (glyf, UPM 2048), so they are visually identical to SF Pro. Georgian Asomtavruli/Nuskhuri (ecclesiastical) fell below the cut. | wght 1–1000 |
| Tifinagh, Coptic | 182 | 265 | Noto (static) | static |
| Arabic additions, per letter (Kurdish ڕ ڵ ێ, Jawi ڠ ڬ ݢ, Sindhi…) | 149 | ~371 | SF Arabic VF first, Noto Sans Arabic VF for the rest (as addfont) | var |
| Myanmar, Lisu, Tai Le, New Tai Lue (addfont) | 319 | 304 | as addfont | mixed |
| P2 symbols, kept part | 234 | 247 | As addfont's split. In: Misc Symbols & Arrows 122, Yijing 64, Supplemental Punctuation 15 (incl. ⸺ ⸻), Misc Math A 15, Math B 7, Tai Xuan Jing 6. | static |
| Symbols new: Arrows-C 136, Geometric Shapes Ext 85, Ornamental 46, Mahjong 43, Music 10, Alchemical 8, Cards 5, Control/OCR 5, Domino 1 | 339 | 339 | Noto Sans Symbols 2. Music from Noto Music, Alchemical from Apple Symbols. | static |
| Cyrillic Ext-A/B/C, Latin Ext-D/E, Modifier Tone Letters (Chinese-dialect tone marks ꜀ ˥ etc.), CDM Ext | 221 | 225 | Noto Sans VF | wght 100–900 |
| Hentaigana, seen | 13 | 13 | Plangothic P2 | static |

## 4. Re-check of the addfont picks under the same ranking

| Addfont pick | Glyphs | Verdict | Why |
|---|---|---|---|
| P1 Hangul KS + jamo/enclosed | 2,479 | **Keep, and extend +948 non-KS** | Highest value per glyph of anything. 21 KS syllables have essentially no hits but are kept to complete the legacy set (21 glyphs). |
| P2 symbols | 748 | **Keep 247, drop ~500** | 472 cps had no page hits in 2.8M pages: most of Math-B, Tai Xuan Jing, Counting Rods, 🉠–🉥, 76 Supplemental Punctuation. Counting rods and 🉠–🉥 are culturally Chinese, but the data doesn't support them. |
| Mongolian (macOS Noto) | 1,537 | **Keep** | 1,146 zh pages. Cheaper than everything else below it per unit of value. |
| Yi | 1,220 | **Drop** | Max 12 zh pages. Density 0.004, which is 100× below the cut. |
| Nüshu | 396 | **Drop** | 1 page |
| Miao | 368 | **Drop** | 0 pages |
| Lisu 49, Tai Le 35, New Tai Lue 83 | 167 | **Keep** | Cheap. 76 / 23 / 14 zh pages. |
| Math alnum | 996 | **Keep 740** | Monospace, bold, italic, fraktur, double-struck and bold-script are used (monospace 𝚟𝚝𝚎 hits 1,796 zh pages). |
| Latin Ext-D | 202 | **Keep 74** | The rest had 0 hits |
| Arabic additions | 830 | **Re-cut per letter: 149 letters, ~371 glyphs** | The block-level unit was too coarse |
| Myanmar additions | 137 | **Keep** (marginal) | |

Net: the addfont picks shrink from ~9,080 to ~6,100 glyphs. The freed ~3,000 plus the rest of the budget go to Han Ext (4,376), non-KS Hangul (948), 5 Indic scripts, Ethiopic, Armenian/Georgian and the symbols above.

## 5. Build notes and risks (for the executor)

- **CFF2 → glyf.** SF India (5 faces) is CFF2 VF.
  - Recommended route: instantiate the masters at the wght extremes (and default) with `fontTools.varLib.instancer`, convert them together with `cu2qu` (`fonts_to_quadratic` on UFOs via ufo2ft/extractor, so the masters stay compatible), then rebuild gvar. Check opsz first (pin opsz = 17).
  - If compatibility fails, the fallback is **Noto Sans Bengali / Kannada / Oriya / Malayalam / Tamil VF**. These are glyf. Bengali Noto costs only 377 vs 629, so the fallback fits the budget too (it frees ~250).
- **Indic shaping.** Each new script needs its own LangSys (bng2/tml2/mlm2/knd2/ory2/sinh) and its GSUB/GPOS lookups appended. The glyph sets are disjoint from the existing deva/gujr/guru, so the merge is additive, using the same pattern as the MiSans merge.
  - After the merge, re-run `build/validate_shaping.py`-style A/B tests with HarfBuzz against the source fonts for each script (sample words: ক্ষ্ম, ஸ்ரீ, ക്ക, ಕ್ಷ, କ୍ଷ, ශ්‍රී).
- **Mongolian.** Needs the macOS Noto GSUB (isol/init/medi/fina, FVS1–4, rlig) intact and vertical behaviour checked. It is the single biggest shaping risk after Indic.
- **Syriac.** Arabic-style joining. Keep its lookups under script `syrc` only.
- **Arabic letters.** Add their isol/init/medi/fina into the existing Arabic lookups (`merge_arabic_gsub.py`). Add mark anchors from SF Arabic.
- **Scaling.** Pretendard, SF Armenian and SF Georgian are UPM 2048, so scale them to 1000. Kefa, SF India and Plangothic are already 1000.
- **Static glyphs in the VF.** Han Ext (Plangothic), Mongolian, Tifinagh, Coptic and the symbols get no gvar, so they stay at one weight across wght 100–900, just as today's TH-Hak Ext glyphs do. Making them variable is out of scope; no variable source exists for Ext B–J.
- **Glyph-count check.** Costs are subsetter closures on the source fonts.
  - After `glyf` dedupe the real count can be a few dozen lower (more room).
  - Merged GSUB can need a few more (fewer rows).
  - Fill or trim in table order: below the cut, next comes Telugu (873, too big), then the per-character rows that follow it.
- **Order of execution.** Run in table order. Everything above row ~60 is robust to the weighting assumptions. Rows near the cut can swap places without mattering.

## 6. Not done / limits

- No real web crawl (Common Crawl) was used; Wikipedia only. kowiki/enwiki are samples of ~35% and ~2%.
- One kowiki scan was lost when the sandbox killed background jobs, and was redone with smaller slices.
- No fonts were merged or rendered in this step. The glyph costs are measured; visual checks of SF India, Kefa, SF Armenian/Georgian and Plangothic next to PingFang are still to do.
- Ideographic Description chars, CJK strokes, Kangxi/radicals supplement, Bopomofo Ext, kana extensions, Greek Ext, Hebrew, Thai, Lao, Khmer, Tibetan and Devanagari were checked and are already complete or near-complete in the font. Hebrew 1 and Lao 1 missing; Khmer 4 missing are not in the plan (0 hits).

## Files

- `work/fillplan/REPORT.md`: this file.
- `work/fillplan/fillplan.json`: 130 tranches (87 in plan). Each has codepoints grouped by source font path, glyphs, cumulative total, evidence, VF status and shaping needs.
- `work/fillplan/src/`: downloaded sources.
  - Apple, from the daijro/os-fonts mirror: SFIndia.ttc, SFArmenian.ttf, SFGeorgian.ttf, SFHebrew.ttf, KefaIII.ttf, KohinoorBangla/Telugu, Sinhala/Tamil/Malayalam Sangam MN, EuphemiaCAS, PlantagenetCherokee, NotoSansKannada/Oriya.ttc, NISC18030 (BMP bitmap only, useless).
  - PlangothicP1/P2-Regular.ttf.
  - `gf/`: 25 Noto fonts (Sinhala, Cherokee, Canadian Aboriginal, Thaana, Syriac, Adlam, Ol Chiki, Javanese, Tai Tham, Tai Viet, Cham, Meetei Mayek, Balinese, Sundanese, Ethiopic, Bengali, Music, NKo, Georgian, Armenian, Tifinagh, Vai, Coptic, Glagolitic, PhagsPa).
- `work/fillplan/data/`: Unihan 17, corpus counts (`d_*.pkl`, `agg.pkl`), `script_costs.json`, ranked and condensed pickles.
