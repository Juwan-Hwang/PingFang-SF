# 苹方SF · PingFang SF

https://github.com/user-attachments/assets/a2d30dc7-78d6-407a-9442-e9c643997dc7

<p align="center"><a href="https://github.com/Juwan-Hwang/PingFang-SF/releases/download/v1.1.0/PingFang-SF-promo-1080p.mp4">▶ 观看高清版宣传片（1080p · 有声 · MP4）</a></p>

![PingFang SF](docs/images/hero.png)

以 **苹方 UI（PingFang UI）** 可变字体为底本，拉丁/希腊/西里尔文使用 **SF Pro**，并补充 **MiSans** 的 9 种文字与 Source Han Sans 等来源汉字的个人合并字体。一个文件、两个可变轴（字重 100–900、字宽 80–120），覆盖中文简繁、港澳字、拉丁、阿拉伯、印度与东南亚文字。

> ⚠️ **仅供个人、非商业的学习研究使用。** 本仓库不提供任何开源许可，各组成字体版权归原权利人所有。详见文末 [许可与免责声明](#许可与免责声明) 和 [NOTICE.md](NOTICE.md)。

## 特性

- **可变字体**：`wght` 100–900（9 个命名实例 Ultralight → Black），`wdth` 80–120。
- **完整的 OpenType 排版**（v1.1 起，GSUB 441 个查找表 / GPOS 67 个 / GDEF）：
  - 中文：`vert` 竖排标点、`locl` 地区字形（zh-Hant / zh-HK / zh-MO / ja）、`fwid` / `hwid` / `pwid` / `nalt`；
  - 拉丁：**可变字距 `kern`**（随字重与字宽变化）、`ccmp`、`locl`、`case`、`frac`、`numr` / `dnom`、`sups` / `subs`、`tnum` / `pnum`、`smcp` / `c2sc`、`ordn`，以及 SF Pro 的 `ss01–ss14`、`cv01–cv13` 等；
  - 阿拉伯文：连写（`init` / `medi` / `fina` / `isol`）、`rlig` 连字（لا、الله 等）、`calt`、元音符号 `mark` / `mkmk` 定位与 GDEF 标记类别；
  - 天城文、古吉拉特文、古尔穆基文、高棉文、老挝文、缅甸文、泰文、藏文：MiSans 的全部 GSUB / GPOS / GDEF（连字、半体、reph、上下标叠放、标记定位）。
- **9 种 MiSans 文字也可变字重**（v1.1 起，原为静态）。
- 中英文名均可识别：`PingFang SF` / `苹方SF` / `蘋方SF`，不与系统自带苹方冲突。

### 字重

![字重 100–900](docs/images/weights.png)

### 多语种

![多语种覆盖](docs/images/scripts.png)

### 竖排

![竖排标点](docs/images/vertical.png)

## 下载

到 [Releases](https://github.com/Juwan-Hwang/PingFang-SF/releases/latest) 下载最新的 `PingFang-SF-Medium.ttf`（约 63 MB，与仓库中的 `PingFang-SF Medium.ttf` 相同）。

## 安装

- **Windows**：右键 TTF →「为所有用户安装」。
- **macOS**：双击 TTF → 字体册「安装」。
- **Linux**：复制到 `~/.local/share/fonts/`（或 `~/.fonts/`），运行 `fc-cache -f`，然后用 `fc-list | grep "PingFang SF"` 确认。

## CSS 用法

已安装到系统时：

```css
body {
  font-family: "PingFang SF", "苹方SF", "PingFang SC", sans-serif;
  font-weight: 500;            /* 100–900 任意值 */
}
```

作为网页字体自托管时请先确认你有权这样做（本字体**不允许**再分发，见下文）；仅本地测试时可以：

```css
@font-face {
  font-family: "PingFang SF";
  src: url("PingFang-SF-Medium.ttf") format("truetype");
  font-weight: 100 900;
  font-stretch: 80% 120%;
}
.vertical { writing-mode: vertical-rl; }   /* 竖排时自动启用 vert */
```

## 可变轴

| 轴 | 范围 | 默认 | 命名实例 |
|---|---|---|---|
| `wght` 字重 | 100 – 900 | 500（Medium） | 100 Ultralight · 200 Thin · 300 Light · 400 Regular · 500 Medium · 600 Semibold · 700 Bold · 800 Heavy · 900 Black |
| `wdth` 字宽 | 80 – 120 | 100 | — |

各部分的可变情况：

| 部分 | 字重 | 字宽 | 说明 |
|---|:-:|:-:|---|
| 苹方汉字、假名、标点（含扩展 A 全部） | ✅ | ✅ | 苹方 UI 原生可变数据 |
| 拉丁 / 希腊 / 西里尔（SF Pro，约 1,740 个码位，含 ASCII） | ✅ | ✅ | v1.1 用 SF Pro 在 15 个母版位置重建（opsz=17），字距同步可变 |
| MiSans 9 种文字 | ✅ | — | MiSans 150–700 映射到 100–900（500 ↔ MiSans Medium 380），字宽轴不改变这些文字 |
| Source Han Sans / TH-Hak / 补充字及部分符号（约 5,960 个码位） | — | — | 静态，详见已知限制 |

## 字符覆盖

由 `build/coverage_stats.py` 统计（v1.1.0）：

| 分类 | 码位数 |
|---|--:|
| 基本拉丁 / 拉丁扩展 / IPA / 组合符号 | 1,364 |
| 希腊文 | 368 |
| 西里尔文 | 313 |
| 阿拉伯文（含表现形式） | 433 |
| 天城文 | 128 |
| 古尔穆基文 | 78 |
| 古吉拉特文 | 85 |
| 泰文 | 87 |
| 老挝文 | 82 |
| 藏文 | 211 |
| 缅甸文 | 91 |
| 高棉文 | 142 |
| 爪哇文 | 13 |
| 标点 / 符号 / 箭头 / 数学 / 几何等 | 2,755 |
| CJK 符号与标点 / 假名 / 注音 / 部首 / 笔画 | 1,486 |
| CJK 统一汉字（基本区 U+4E00–9FFF） | 20,992 |
| CJK 扩展 A | 6,592 |
| CJK 扩展 B | 7,306（部分，例如 U+20000 𠀀 不含） |
| CJK 扩展 C–I | 1,302（部分） |
| CJK 兼容汉字 | 537 |
| 私用区（主要为 SF Symbols） | 8,447 |
| 其他 | 195 |
| **总计** | **53,007 码位 / 62,782 个字形** |

韩文音节未收录。

## 合并来源

| 来源 | 用途 |
|---|---|
| **PingFang UI TC**（底本，可变 wght+wdth，`21.4d1e1`） | 繁体字形、可变框架、GSUB（vert / locl / 全半角） |
| **PingFang UI HK / SC** | 补充香港字 +1,008、简体字 +3,560；中文标点使用 SC 字形 |
| **SF Pro**（可变） | 拉丁（含 ASCII）、希腊、西里尔等；字距（kern）与拉丁特性 |
| **MiSans** Arabic / Devanagari / Gujarati / Gurmukhi / Khmer / Lao / Myanmar / Thai / Tibetan（可变） | 9 种文字的字形与全部排版规则 |
| **Source Han Sans**、**TH-Hak** | 补充扩展区汉字（静态） |

## 构建 / 复现

v1.0 的合并（苹方 UI + SF Pro + 各补字来源）是基底，保存在 git 历史的 `ad938e1` 提交中；v1.1 的修复全部由 `build/` 中的脚本完成，可完整复现：

```bash
pip install fonttools uharfbuzz numpy brotli
sudo apt install p7zip-full opentype-sanitizer      # 7z 解包 DMG；ots-sanitize 校验
build/fetch_sources.sh        # 下载苹方 UI(VF)、SF Pro.dmg、MiSans 全家桶并解包到 sources/
build/build.sh                # 生成 "PingFang-SF Medium.ttf" 并运行全部校验
```

流程：

1. `step2_sf_vf.py`：选出基底中 SF 结构的拉丁/希腊/西里尔码位，从 SF Pro 子集化（含特性闭包），缩放 UPEM 2048→1000，在 15 个目标位置实例化（opsz=17；wght 映射拟合苹方 UI 内置拉丁：100→236 … 500→540 … 900→1000；wdth 不变），再用 `varLib` 重建为目标坐标系下的可变字体。
2. `step3_misans_vf.py`：同样方式把 9 个 MiSans 可变字体在 9 个字重位置实例化并重建（MiSans 150/200/250/330/380/520/630/680/700 ↔ 100…900）。
3. `step4_integrate.py`：
   - 用轮廓哈希把苹方 UI TC 的字形对应到基底字形，子集化苹方 GSUB（vert/locl/fwid/hwid/pwid/nalt）并补入缺失的 822 个竖排/地区字形（含 gvar）；
   - 用重建结果替换 SF（1,687 个）/ MiSans（1,578 个）字形的轮廓与 gvar，并补入 SF 的 1,436 个、MiSans 的 3,399 个替代/连字/组件字形；
   - `layout_merge.py` 把各来源的 GSUB / GPOS / GDEF（含 GDEF ItemVariationStore、MarkAttachClass、MarkGlyphSets、高棉文 FeatureVariations）合并为一套，`layout_sort.py` 按目标字形 ID 重排所有 Coverage 及并行数组；
   - 修正 8,049 个纵向前进宽度为 0 的字形（vmtx）、把 7 个带三次曲线标志的字形转为二次曲线、由 gvar 重建 HVAR。
4. `step5_finalize.py`：中英文名称、版权/商标/许可说明、命名实例的 PostScript 名、head.yMin/yMax（保持苹方原值 −232/902）。
5. 校验：`ots-sanitize`、`validate_font.py`（fontTools 完整读写往返、gvar glyphCount、wght=100/900 静态实例化）、`validate_shaping.py`（HarfBuzz 与各源字体逐字形比对，见下）。

另外 `extract_apple_fonts.sh` 可从任意 Apple 字体 DMG 中提取 TTF/OTF；`merge_arabic_gsub.py` 是独立的小工具，把阿拉伯文排版规则**合并**（而非替换）进其他字体。

### 校验结果（v1.1.0）

- `ots-sanitize`：通过（v1.0 因三次曲线标志无法通过）。
- fontTools 读写往返、gvar `glyphCount` = `maxp.numGlyphs` = 62,782、wght 100/900 实例化：通过。
- HarfBuzz 对比（157 项，0 失败）：9 种文字的样例在 wght 100 / 500 / 900 下与对应 MiSans 源字体的字形、前进宽度、标记偏移一致（偏差 ≤ 1 单位）；`AV` `To` `Ty` `LT` 字距分别为 −63 / −96 / −48 / −92；竖排 `，。、「」（）《》：！？` 与苹方 UI SC 的竖排字形一致。完整报告见 [docs/validation/shaping_report.txt](docs/validation/shaping_report.txt)。
- 重新运行 `build/build.sh` 得到的字体与发布文件逐表一致（`head` 时间戳除外）。

## 已知限制

- **授权**：组成字体均非开源（SF Pro 许可明确禁止再分发），本仓库只是个人研究用途的合并实验，存在版权风险。
- **静态部分**：约 5,960 个码位（主要是 Source Han Sans / TH-Hak 补充的扩展 B 以后汉字中的 1,777 个、盲文 / 数学 / 技术符号、希腊扩展、IPA 扩展、爪哇文等）没有可变数据，在任何字重下都保持原样。
- **MiSans 文字**只随字重变化，不随字宽变化；MiSans 最粗只有 700（Heavy），所以 800–900 与 700 差别很小；MiSans 最细 150 对应 100。
- **拉丁字重对应**沿用苹方 UI 内置拉丁的关系（wght 100 ↔ SF Pro 236，500 ↔ 540，900 ↔ 1000），因此 Ultralight 的拉丁比 SF Pro 自己的 Ultralight 粗；拉丁使用 SF Pro 的 Text 光学尺寸（opsz 17），字距也取自该尺寸。默认字重下 ASCII 与 v1.0 的差异 ≤ 1 个单位（实例化取整）。
- **底本是繁体（TC）**：简体中文（zh-Hans）文本里同一码位的地区字形仍是繁体/台湾写法（苹方 UI 的 `locl` 只提供 ZHT/ZHH/JAN/ZHTM，没有 ZHS 分支）；标点使用 SC 字形，zh-Hant 下自动换成居中的 TC 标点。
- **竖排**：`… — ～ ー` 等在源字体中也没有竖排字形，依赖排版引擎旋转；中文没有 `vpal` / `palt` 标点挤压（源字体也没有 GPOS）。
- CJK 扩展 B 及以后只覆盖一部分（例如 U+20000 𠀀 缺字）；韩文音节未收录。
- 文件较大（约 63 MB），不适合直接作为网页字体。

## 更新日志

### v1.1.0（2026-10-16）

- 恢复 OpenType 排版：苹方 CJK 的 `vert` / `locl` / 全半角特性；SF Pro 的可变字距与拉丁特性；9 种 MiSans 文字完整的 GSUB + GPOS + GDEF（阿拉伯文元音、印度文字连字与叠放、东南亚文字标记定位）。v1.0 只有阿拉伯文的 5 个 GSUB 特性，没有 GPOS / GDEF。
- 9 种 MiSans 文字改为可变字重；默认字重从 MiSans Regular(330) 改为与苹方 Medium 匹配的 MiSans Medium(380)。
- 拉丁 / 希腊 / 西里尔统一由 SF Pro 在正确字重下重建（v1.0 中拉丁扩展、希腊、西里尔实际是 SF Pro 400，与 ASCII 的 540 不一致）。
- 修复 HVAR：v1.0 中后加入的字形被映射到汉字的宽度变化数据，在 wdth=80/120 时前进宽度错误（例如 Ж 变窄 200 单位）。
- 修复 8,049 个字形的纵向前进宽度为 0、`yen` 的 gvar 数据损坏、7 个字形带有三次曲线标志（导致 OTS / 浏览器拒绝）。
- 新增中文名称：`苹方SF`（zh-CN）、`蘋方SF`（zh-TW / zh-HK）；命名实例 PostScript 名改为 `PingFangSF-*`；补充版权、商标与许可说明。
- `merge_arabic_gsub.py`：修复 `arab_mappings` NameError、gvar 补丁重复执行、复制组件缺少 gvar / vmtx 时 KeyError、返回值恒为 0、验证只打印不判定等问题；改为合并进现有 GSUB 并处理 GDEF 与 LookupFlag。
- 新增可复现构建脚本 `build/`、`extract_apple_fonts.sh` 和校验脚本。

### v1.0.0

- 初始合并版本。

## 许可与免责声明

**本字体仅供个人、非商业的学习研究使用。** 本仓库不持有任何组成字体的版权，也不授予任何许可：

- PingFang（苹方）与 SF Pro 为 Apple Inc. 的财产与商标；MiSans 为小米公司的财产与商标；Source Han Sans 为 Adobe 依 SIL OFL 1.1 发布；TH-Hak 归其作者。
- 本字体按“原样”提供，**不附带任何担保**；使用者须自行遵守各组成字体的许可协议，并自行承担使用后果。请勿商用、再分发或嵌入到产品中。
- 本项目与上述任何公司无关，也未获得其认可。
- **如权利人要求，将立即删除。** 请通过 [GitHub Issues](https://github.com/Juwan-Hwang/PingFang-SF/issues) 联系。

完整的来源与版权声明见 [NOTICE.md](NOTICE.md)。
