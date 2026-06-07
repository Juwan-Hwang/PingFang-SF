# PingFang SF — 超集合并字体

以苹方 UI TC（繁体中文）为底本，合并 HK/SC 多地区字形，替换英文字符为 SF Pro，补充 MiSans 多语种字形与 Source Han Sans 汉字，打造一个覆盖广泛的可变字体。

## 字体信息

| 属性 | 值 |
|------|-----|
| Family Name | PingFang SF |
| 字重范围 | 100 (Thin) — 900 (Black) |
| 字宽范围 | 80 (Condensed) — 120 (Expanded) |
| UPEM | 1000 |
| 格式 | TrueType Variable Font |
| 字形数 | 57,125 |
| 文件大小 | ~55 MB |

## 合并来源

| 来源 | 字重 | 操作 |
|------|------|------|
| **PingFang UI TC** (底本) | Medium | 繁体中文基础字形 + 可变字体框架 |
| **PingFang UI HK** | Medium | 补充 HK 独有字符 (+1,008) |
| **PingFang UI SC** | Medium | 补充 SC 独有字符 (+3,560)，替换中文标点为 SC 版本 |
| **PingFang UI MO** | Medium | 确认无独有字符，跳过 |
| **PingFang UI JA** | Medium | 确认无独有字符，跳过 |
| **SF Pro** | 可变 | 替换 ASCII/拉丁字符为 SF Pro 版本，补充拉丁扩展/希腊/西里尔等 (+~10,000) |
| **汉仪中黑S** | Regular | 补充爪哇文 (+13)，其余 157 个 PUA 字符跳过 |
| **TH-Hak** | Regular | 补充独有汉字 (+5,941)，跳过韩文音节 |
| **Source Han Sans** | Regular | 补充独有汉字 (CFF→TrueType 转换合并) |
| **MiSans Arabic** | 可变→Medium | 补充阿拉伯文 (+430 码位)，含 GSUB 连写规则 |
| **MiSans Devanagari** | 可变→Medium | 补充天城文 (+126) |
| **MiSans Gujarati** | 可变→Medium | 补充古吉拉特文 (+85) |
| **MiSans Gurmukhi** | 可变→Medium | 补充古尔穆基文 (+78) |
| **MiSans Khmer** | 可变→Medium | 补充高棉文 (+110) |
| **MiSans Lao** | 可变→Medium | 补充老挝文 (+82) |
| **MiSans Myanmar** | 可变→Medium | 补充缅甸文 (+91) |
| **MiSans Thai** | 可变→Medium | 补充泰文 (+87) |
| **MiSans Tibetan** | 可变→Medium | 补充藏文 (+211) |

## 技术细节

### UPEM 对齐

SF Pro 原始 UPEM 为 2048，苹方为 1000。合并前通过 `fontTools.ttLib.scaleUpem` 将 SF Pro 缩放至 UPEM=1000，确保字形比例一致。

### 可变字体轴处理

SF Pro 原始有 3 个轴 (wght, wdth, opsz)，苹方有 2 个轴 (wght, wdth)。合并时：
1. 固定 SF Pro 的 opsz=17（Display 尺寸）
2. 缩放 UPEM
3. 重排轴顺序 [wdth, wght] → [wght, wdth] 与苹方对齐
4. 合并 gvar 变体数据

### 复合字形处理

MiSans 的复杂脚本字体（阿拉伯文、天城文等）包含大量复合字形。处理流程：
1. 子集化保留所需字形（subset 自动追踪组件依赖）
2. 保留复合字形原始结构，不展开
3. 复制到目标字体时确保所有组件一并带入

### CFF 转 TrueType

Source Han Sans 使用 CFF 轮廓格式，苹方使用 TrueType 轮廓。合并时通过 `TTGlyphPen` 将 CFF CharStrings 绘制转换为 TrueType 轮廓。

### 中文标点替换

将 TC 底本的中文全角标点替换为 SC 版本（、。！，．：；？等），使标点风格与简体中文一致。

### 阿拉伯文 GSUB Shaping

阿拉伯文合并了 MiSans Arabic 的 GSUB 规则，支持连写：

| Feature | 类型 | 映射数 | 功能 |
|---------|------|--------|------|
| fina | SingleSubst | 82 | 词尾形式 |
| init | SingleSubst | 38 | 词首形式 |
| medi | SingleSubst | 43 | 词中形式 |
| isol | SingleSubst | 1 | 孤立形式 |
| rlig | LigatureSubst | 15 | 必需连字 (لا/لأ/لإ/لآ/الله 等) |

## 字符覆盖

| 分类 | 大致数量 |
|------|----------|
| ASCII / 拉丁 | ~2,000 |
| 希腊 / 西里尔 | ~400 |
| CJK 常用汉字 | ~21,000 |
| CJK 扩展 A | ~2,900 |
| CJK 扩展 B-G | ~13,000 |
| CJK 兼容 | ~300 |
| 阿拉伯文 | ~430 |
| 天城文 | 126 |
| 藏文 | 211 |
| 高棉文 | 110 |
| 泰文 | 87 |
| 老挝文 | 82 |
| 缅甸文 | 91 |
| 古吉拉特文 | 85 |
| 古尔穆基文 | 78 |
| 符号 / 其他 | ~2,000 |
| **总计** | **~53,000 码位** |

## 命名规则

文件名 `PingFang_UI_TC_HK_SC_Medium.ttf` 表示：
- **TC** — 底本为繁体中文
- **HK** — 补充了 HK 独有字符
- **SC** — 补充了 SC 独有字符并替换了标点

如后续再添加其他字体（如 JP），命名追加为 `TC_HK_SC_JP_Medium.ttf`。

安装后的字体名为 **PingFang SF** / **苹方SF**，不会与系统原版苹方冲突。

## CSS 引用

```css
font-family: "PingFang SF", "PingFang SC", sans-serif;
```

## 依赖工具

- [fontTools](https://github.com/fonttools/fonttools) — 字体读写、合并、子集化、UPEM 缩放
- [fontTools.varLib.instancer](https://fonttools.readthedocs.io/) — 可变字体实例化
- [fontTools.subset](https://fonttools.readthedocs.io/) — 字体子集化
- [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) — 阿拉伯文 shaping 验证

## 来源与版权

本字体为个人合并作品，仅供学习研究。各源字体版权归原作者所有：

| 来源 | 版权方 | 来源链接 |
|------|--------|----------|
| PingFang UI | Apple Inc. | [ACT-02/PingFangUI-VF](https://github.com/ACT-02/PingFangUI-VF) |
| SF Pro | Apple Inc. | Apple SF Fonts (内部提取) |
| 汉仪中黑S | 汉仪字库 | — |
| TH-Hak | 开源字体 | — |
| Source Han Sans | Adobe / 开源 | [adobe-fonts/source-han-sans](https://github.com/adobe-fonts/source-han-sans) |
| MiSans | 小米公司 | [miSans](https://hyperos.mi.com/font) |

**免责声明**：本仓库不持有任何源字体的版权。所有字体均为各自版权方的财产。本合并字体仅供个人学习研究使用，请勿用于商业用途。使用本字体即表示您已了解并遵守各源字体的许可协议。
