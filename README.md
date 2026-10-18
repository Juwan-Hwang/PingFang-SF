# PingFang SF · 开发工具（tools 分支）

这个分支只放构建字体时用过的分析与辅助脚本，不含任何字体文件、语料或第三方数据。字体本身的可复现构建流程在主分支的 `build/` 目录中，这里的脚本是做决策时用的“前期调研”和检查工具。

> 脚本是在开发环境中直接写成的，多数用了绝对路径或相对 `work/` 目录的路径（如 `PingFang-SF/PingFang-SF Medium.ttf`、`src/...`），使用前请按自己的目录调整。依赖：Python 3.11+、`fontTools`、`uharfbuzz`、`numpy`、`Pillow`，部分渲染脚本需要 `playwright`（Chromium）。

| 目录 | 用途 |
|---|---|
| `coverage-audit/` | v1.2.0 前的覆盖审计：按 Unicode 区块 / 文字统计已覆盖与缺失码位，对照 通用规范汉字表、GBK、Big5、HKSCS 等字符集，找出空白字形、孤立字形和按需补字的字形成本。结论见 `REPORT.md`。需要 UCD 文件（`Blocks.txt`、`Scripts.txt`、`UnicodeData.txt`、`emoji-data.txt`，可从 unicode.org 下载）。 |
| `fill-plan/` | v1.2.0 补字计划：扫描维基百科（中 / 英 / 韩 / 粤 / 文言）转储中本字体缺失字符出现的页面数（`scan2.py`、`scanko.py`），汇总（`agg.py`），用 fontTools subsetter 计算每项补字的实际字形闭包成本（`costs.py`），按“每个字形带来的价值”贪心排序（`rank.py`），输出 `fillplan.json`（`emit.py`）。完整说明与数据见 `REPORT.md`。需要自行下载维基百科转储与 Unihan。 |
| `font-candidates/` | 候选补字字体比较：各候选字体对缺字的覆盖（`cov.py`、`needs.py`）、字形成本（`cost.py`）、与苹方并排渲染的对比图（`render.py`、`sheets.py`、`fullline.py`），数学字母的混合来源方案（`mathhybrid.py`）。结论见 `REPORT.md`。 |
| `shs-vf-analysis/` | 思源黑体可变化的分析：把静态字形与思源黑体各地区写法逐一栅格化比较（`classify_sh.py`、`sel.py`、`refine.py`），按笔画粗细拟合苹方与思源字重的对应（`stems.py`、`stems2.py`、`stemcheck.py`），以及替换后的校验（`verify.py`、`render.py`）。主分支的 `build/shs_select.py` 是其整理后的版本。 |
| `inspect/` | 小工具：字形来源分类（`classify.py`）、gvar 完整性检查（`gvarcheck.py`）、轮廓哈希映射（`hashmap.py`）、字体结构速查（`insp*.py`）、大字体加载耗时（`loadtest.py`）、可变字体轴信息（`miinfo.py`）。 |
| `ots-build/` | 在没有 C 编译器的环境里用 zig 编译 OTS（`ots-sanitize`）时用的编译器包装：`cc` / `c++` / `ar` 转给 `python3 -m ziglang`（`pip install ziglang`），并加 `-mcpu=generic` 以兼容 ARM 虚拟机。用法：`CC=$PWD/cc CXX=$PWD/c++ AR=$PWD/ar meson setup build && ninja -C build`。 |
| `readme-images/` | 生成主分支 README 配图（`docs/images/hero.png`、`scripts-v120.png`）：HTML 用本字体排版，`shot.py` 用 Chromium 截图。 |

宣传视频的源码在 `promo` 分支。
