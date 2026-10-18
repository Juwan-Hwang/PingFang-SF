# PingFang SF · 宣传视频源码（promo 分支）

1080p / 30 fps 宣传视频的全部源码。画面是一个 HTML 页面（`promo.html`），用本字体实时排版，按时间逐帧截图；配乐全部由 `sound.py` 程序合成，不用任何采样，并对齐画面时间轴。

本分支不含字体文件。使用前把主分支的 `PingFang-SF Medium.ttf` 复制到本目录。

## 场景（v1.2.0，52.2 秒）

| 时间 | 场景 | 内容 |
|---|---|---|
| 0–4.6 s | 01 | 「永」随字重心跳，标题入场 |
| 4.6–9.4 s | 02 HARMONY | SF Pro 拉丁 × 苹方汉字，大写高度 / x 高度 / 基线 |
| 9.4–17.4 s | 03 ONE FONT · EVERY SCRIPT | 25 种问候语沿螺旋排列，计数 56,497 码位 / 65,535 字形 / 37 种文字 |
| 17.4–24.4 s | 04 VARIABLE | wght × wdth 实时变化，9 个字重瀑布（含韩文） |
| 24.4–28.8 s | 05 VERTICAL | 横排 → 竖排，标点由 `vert` 替换 |
| 28.8–34.0 s | 06 FOR TYPE NERDS | 可变字距、阿拉伯文连写与元音定位、天城文结合字、泰文 / 藏文叠放（HarfBuzz 实际排版结果） |
| 34.0–39.6 s | 07 NO MORE TOFU | 8 个 `.notdef` 方框翻转成 v1.2.0 新增的字：𰻞 한 অ த 𝔸 ሰ Ա ශ |
| 39.6–45.6 s | 08 65,535 | 65,535 个字形 ID 的点阵，按 ID 顺序填满；蓝色为 v1.2.0 新增 |
| 45.6–52.2 s | 09 | 字符粒子内爆 / 外爆，标志定格 |

v1.2.0 起去掉了 v1.1 的橙色辉光（text-shadow、径向光晕、发光圆环），改为冷蓝色细线、描边回声与平面色块。v1.1 版源码保留在 `v1.1/` 中以供对比。

## 文件

- `promo.html`：全部画面。`render(t)` 绘制第 t 秒的一帧，`window.READY` 为真后可调用。
- `gen_glyphs.py` → `glyphs.js`：场景 06 与 07 用到的字形轮廓与 HarfBuzz 排版结果（SVG 路径），以及 `.notdef`。
- `gen_flags.py` → `flags.js`：每个字形 ID 是否为 v1.2.0 新增（场景 08）。需要补字前的字体做对照。
- `cap.py`：Playwright（Chromium）逐帧截图。`python3 cap.py frames 30 0 1566` 渲染全部帧；可分段并行，例如 `0 522`、`522 1044`、`1044 1566`。`python3 cap.py test times 35.5,44` 只截指定时刻。
- `sound.py` → `soundtrack.wav`：程序合成配乐（numpy / scipy / pyloudnorm），响度 −14 LUFS，真峰值 ≤ −2 dBTP。
- `enc.sh`：用 ffmpeg 合成母版（CRF 15）和 README 用的 2-pass 小文件（视频 1600 kbps，约 10 MB）。

## 依赖

Python 3.11+，`playwright`（`python3 -m playwright install chromium-headless-shell`），`fontTools`，`uharfbuzz`，`numpy`，`scipy`，`pyloudnorm`，`Pillow`，ffmpeg。
