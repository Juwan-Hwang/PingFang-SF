# PingFang SF · launch film

**58.5 s · 1920×1080 · 30 fps · H.264 High CRF 16 · AAC 256 kb/s 48 kHz · −14.0 LUFS, −1.3 dBTP (two-pass loudnorm) · 120 BPM (bar = 2.000 s)**
Two cuts from one comp: `deliver/pingfang-sf-promo-en.mp4` (English copy only) and `deliver/pingfang-sf-promo-zh.mp4` (Chinese copy only).

The film is the specimen. Every glyph on screen is this repo's own `PingFang-SF Medium.ttf` (v1.2.0, font version 1.200): live text in Chromium with the font loaded through `@font-face`, or outlines and points read straight out of the file with HarfBuzz / fontTools / FreeType (`gen/*.py`). No other typeface is loaded, the terminal included. The font binary is **not** copied onto this branch: `setup.sh` takes it from the repo root.

Message: **One font. Every script. / 一个字体，书写世界.** The carry element is the **tittle of the i in “PingFang”**, a single blue dot (#8AB4FF, the blue of the repo's poster). It is the only accent-coloured thing in the film and it crosses every cut.

## Storyboard (hits on the bar lines)

| t (s) | bars | scene | what happens | carry into the next scene |
|---|---|---|---|---|
| 0–6 | 0–3 | 3D open | Dark. The blue tittle blinks three times. On **2.0** the wordmark 苹方SF PingFang SF swings in as a hairline (wght 100), thickens to Black (900) on the whip orbit, settles at its lockup weights (800 / 300) square-on with a light sweep. 4.55–5.85 the camera pushes into the tittle. | the blue field closes onto the dot |
| 6–10 | 3–5 | thesis | The dot writes “Chinese and Latin, / set as one.” · 「中文与拉丁，/ 浑然一体」 at a fixed duration per line. | the dot drops onto the i of the specimen |
| 10–16 | 5–8 | harmony | **Align 对齐** at 300 px, drawn from the font's outlines, rises around the dot. Metric lines draw in: em top 860, cap height 705, x-height 532, baseline 0, em bottom −140 (font units, measured from the file). Spring push to where n meets 对. | camera dives into the tittle |
| 16–22 | 8–11 | anatomy · variable | Inside the dot the word turns into its own TrueType contours: on-curve squares, off-curve circles, handles (glyf + gvar). Pull back; wght 500 → 100 → 900 → 500, then wdth 100 → 80 → 120 → 100, every point interpolating. Live `wght` / `wdth` readout. | the word collapses, the dot slides to the reel |
| 22–30 | 11–15 | every script | 24 greetings, one per eighth note: Hello, こんにちは, 안녕하세요, Γειά σου, Привет, مرحبا, नमस्ते, ਸਤ ਸ੍ਰੀ ਅਕਾਲ, નમસ્તે, নমস্কার, வணக்கம், ನಮಸ್ಕಾರ, നമസ്കാരം, ନମସ୍କାର, ආයුබෝවන්, สวัสดี, ສະບາຍດີ, မင်္ဂလာပါ, ជំរាបសួរ, བཀྲ་ཤིས་བདེ་ལེགས, Բարեւ, გამარჯობა, ሰላም, 你好, shaped by Chromium/HarfBuzz with the font's own GSUB/GPOS (all 24 checked: every code point in the cmap, no .notdef). | dive into 好 |
| 30–36 | 15–18 | 65,535 | 好 is one cell. Pull back to every glyph in the font in glyph-ID order, 256 per row, while a counter runs to 65,535. Whip to the corner: GID 65,534 is the last glyph, and the 65,536th cell stays empty (maxp.numGlyphs is a uint16). | the dot (cell marker) flies to the next line |
| 36–40 | 18–20 | vertical | 「天地玄黄，宇宙洪荒。」 is written horizontally, then flows into a vertical-rl column; the punctuation swaps to its vertical forms (the font's `vert`). | the dot becomes the terminal's block cursor |
| 40–46 | 20–23 | install (real) | A terminal opens out of the cursor. The real Linux install from the README: `cp … ~/.local/share/fonts/`, `fc-cache -f`, `fc-list "PingFang SF" style` (nine named instances), `fc-match "苹方SF"` → PingFang SF. | the cursor glides to the finale |
| 46–50 | 23–25 | finale | “One font. Every script.” · 「一个字体，书写世界」. 48.85 the dot swells to fill the frame. | we are inside the tittle |
| 50–52.5 | 25–26.25 | 3D reprise | Pull back out of the tittle; the wordmark flips in, weight breathing from 900 to 800 / 300, and lands pixel-matched on the vector lockup (handoff check: 0 px). | crossfade 52.25–52.5 |
| 52.5–58.5 | | lockup | 苹方SF PingFang SF (outlines from the font). The tittle hops once and lands. github.com/Juwan-Hwang/PingFang-SF · “v1.2.0 · For personal, non-commercial use” · 「v1.2.0 · 仅供个人非商业学习研究」. Fade. | — |

## All on-screen copy

| key | EN | ZH |
|---|---|---|
| thesis | Chinese and Latin, / set as one. | 中文与拉丁，/ 浑然一体 |
| harmony | SF Pro Latin. PingFang Chinese. / One em square, one baseline, matched weights. | SF Pro 的拉丁，苹方的汉字 / 同一个字身框，同一条基线，字重彼此匹配 |
| metric labels | em top · cap height · x-height · baseline · em bottom | 字身框顶 · 大写高度 · 小写高度 · 基线 · 字身框底 |
| variable | Variable, from 100 to 900. / Weight and width axes. Every point moves. | 从 100 到 900，连续可变 / 字重、字宽两个轴，每个点都在移动 |
| scripts | 56,497 characters. / Latin, Greek, Cyrillic, Arabic, Indic, Southeast Asian, Hangul, Han — one file. | 56,497 个字符 / 拉丁、希腊、西里尔、阿拉伯、印度诸文、东南亚诸文、韩文、汉字，同在一个文件 |
| script names | Latin … Ethiopic | 拉丁文 … 埃塞俄比亚文 |
| glyphs | 65,535 glyphs. / Every slot TrueType allows, filled. · last glyph · no 65,536th slot | 65,535 个字形 / TrueType 允许的字形数，一个不剩 · 最后一个字形 · 没有第 65,536 格 |
| vertical | Vertical, too. / Punctuation turns with the line. | 竖排，同样从容 / 标点随行转向 |
| install | Terminal · Install once. Nine named weights. / Found by its English or Chinese name. | 终端 · 装一次，九个字重齐备 / 中文名、英文名，都能找到 |
| finale | One font. Every script. | 一个字体，书写世界 |
| lockup | v1.2.0 · For personal, non-commercial use | v1.2.0 · 仅供个人非商业学习研究 |

**Data, kept identical in both cuts:** the specimens (Align 对齐, the 24 greetings, 好, 「天地玄黄，宇宙洪荒。」, the wordmark), glyph IDs, OpenType axis tags, and the terminal transcript. `scripts/lint_copy.py` is clean with exactly these strings allowed.

## What is real

Every number was read from the font file (`analysis/facts.py` → `analysis/facts.json`, fontTools 4.61.1):

| claim | source |
|---|---|
| 65,535 glyphs | `maxp.numGlyphs` = 65,535 (the TrueType maximum; GID 65,534 is the last glyph) |
| 56,497 characters | code points in the best cmap = 56,497 |
| wght 100–900, wdth 80–120, nine named weights | `fvar`: Ultralight 100 … Black 900; `fc-list` lists the same nine |
| em top 860 / em bottom −140 / cap height 705 / x-height 532 | OS/2 typo ascender/descender; top of H and of x in `glyf` (UPM 1000) |
| SF Pro Latin, PingFang Chinese, matched weights | the repo README (Latin rebuilt from SF Pro with the weight mapping fitted to PingFang UI's built-in Latin) |
| vertical punctuation | the font's `vert` feature, applied by Chromium in `writing-mode: vertical-rl` |
| the terminal | a real session on 2026-10-24 (Debian 13 aarch64, fontconfig): `session/term_final.txt`, shown verbatim |
| 24 greetings | `gen/greet.py`: every code point in the cmap, HarfBuzz shaping with no .notdef |

Not claimed on purpose: the README's “37 scripts” (not derivable from the file alone) and the older “440 GSUB lookups” (the v1.2.0 file has 747).

## How it is made

| file | role |
|---|---|
| `film/comp.html` | the whole film as one seekable timeline (`__ready / __seek / __motion / __events / __handoff / __copy`), `?lang=en|zh`, `?t=` for stills |
| `film/p3d.html` | three.js r170 open (6.0 s) and reprise (2.5 s). The wordmark is extruded from HarfBuzz outlines at wght 100…900 (step 25, interpolated in between, since gvar keeps the point structure) |
| `film/frames/{open,end}` | the rendered 3D frames (linear-light shutter blur: 6 samples, 20 on the landing swing 1.9–2.4 s, 7 on the reprise) |
| `film/data/` | `lockup.json`, `spec.json` (TrueType points of Align 对齐 at 17 weights and 9 widths), `greet.json`, `term.txt` |
| `gen/` | the generators for `film/data` and `film/atlas` (the atlas, 65,535 glyphs at 32 px cells plus two 8× close-ups, is rebuilt by `setup.sh` and not committed) |
| `render_film.py` | Playwright frame renderer with adaptive motion blur; the zoom-through at 30.0–33.2 s uses 12 samples |
| `music.py` | original score in numpy: 120 BPM, F major (F–Dm–B♭–C, C pedal into the reprise), seed 7, stems in `audio/stems/` |
| `sound.py` | earshot SFX @ 925ebe56a1b755e5d354ab642bb8f344440cfa9c, peak-aligned to the comp's events, one room |
| `encode.sh` | two-pass loudnorm −14 LUFS, H.264 High CRF 16 BT.709, AAC 256k |
| `scripts/` | QA: contact sheets, stills, accent audit, copy lint, handoff check, loudness and hit onsets, secret scan |

QA at delivery: handoff 0 px; every hit within +5…+20 ms of an onset; accent audit flags only the intended full-frame dot moments; copy lint clean; secret scan clean.

## Rebuild

```sh
cd promo/film
sh reproduce.sh                 # both cuts → deliver/*.rebuild.mp4  (RE3D=1 also re-renders the 3D frames)
```
Versions and seeds are pinned (`requirements.txt`, three.js 0.170.0, earshot 925ebe5, chrome-headless-shell 1248). A different Chromium build can move edge pixels slightly, never content or timing. A full rebuild was not run for this delivery, by request.

License note: the font remains for personal, non-commercial study only (see the repo's NOTICE). This branch carries no font binary.
