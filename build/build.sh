#!/usr/bin/env bash
# 完整构建：v1.0 合并字体（基底） -> v1.1.x （排版表 + 可变化 + 命名修复 + .notdef/度量 + 思源黑体可变化）
# 用法: build/build.sh            （先运行 build/fetch_sources.sh）
# 环境变量: PFSF_SRC 源字体目录（默认 ../sources），PFSF_WORK 中间文件目录（默认 ../build_work）
set -euo pipefail
cd "$(dirname "$0")"
WORK="${PFSF_WORK:-../build_work}"; mkdir -p "$WORK"
BASE="$WORK/base_v1.0.ttf"
OUT="${1:-../PingFang-SF Medium.ttf}"
# v1.0 的合并字体（苹方 UI TC/HK/SC + SF Pro + TH-Hak + Source Han Sans + MiSans 字形）
# 是本次修复的基底，取自 git 历史中的提交 ad938e1。
[ -f "$BASE" ] || git -C .. show 'ad938e1:PingFang-SF Medium.ttf' > "$BASE"
python3 step2_sf_vf.py "$BASE"                 # SF Pro -> 目标设计空间的可变字体（含 kern）
python3 step3_misans_vf.py                     # 9 个 MiSans 文字 -> 目标设计空间的可变字体
python3 step4_integrate.py "$BASE" "$WORK/step4.ttf" 2> >(grep -v 'Coverage is not sorted' >&2)
python3 step5_finalize.py "$WORK/step4.ttf" "$WORK/step5.ttf"   # 命名与版权/许可信息
python3 step6_notdef_metrics.py "$WORK/step5.ttf" "$WORK/step6.ttf"   # v1.1.1: .notdef 方框 + 重算全局度量
python3 step7_shs_vf.py "$WORK/step6.ttf" "$WORK/step7.ttf"   # v1.2.0: 759 个思源黑体来源的静态字形改用思源黑体可变字体（原位替换；7 个用 ZHT 字形）
python3 step8_cleanup.py "$WORK/step7.ttf" "$WORK/step8.ttf" "$WORK/step8_report.json"   # v1.2.0: 删除 SF Symbols PUA、取消 emoji 默认呈现字符映射、合并重复字形、补 U+20C0/20C1 与零宽字形、清除孤立字形
# v1.2.0: 按频率排名补字到 TrueType 上限 65,535 个字形（韩文、扩展 B–J 汉字、孟加拉/泰米尔等 5 种印度文字、
# 亚美尼亚/格鲁吉亚/埃塞俄比亚/蒙古等文字、数学字母、阿拉伯文新增字母、符号）。源字体见 data/fill_sources.sha256，
# 放在 $PFSF_FILL_SRC 下（默认 ../sources/fill）。
FILL_SRC="${PFSF_FILL_SRC:-../sources/fill}"
(cd "$FILL_SRC" && sha256sum -c --quiet "$OLDPWD/data/fill_sources.sha256")
python3 gen_fill_specs.py data/fillplan.json data/fill_sources.json data/fill_trim.json
PFSF_FILL_SRC="$FILL_SRC" python3 fill_parts.py data/fill_sources.json "$WORK/fill_parts"
python3 step9_fill.py "$WORK/step8.ttf" "$WORK/fill_parts" "$OUT" data/fill_sources.json
python3 - "$OUT" <<'PY'                          # 空 DSIG 占位（不含签名，兼容旧版 Office 的 OpenType 功能）
import sys
from fontTools.ttLib import TTFont, newTable
f = TTFont(sys.argv[1], recalcBBoxes=False, recalcTimestamp=False)
t = newTable("DSIG"); t.ulVersion = 1; t.usFlag = 1; t.usNumSigs = 0; t.signatureRecords = []
f["DSIG"] = t; f.save(sys.argv[1])
PY
ots-sanitize "$OUT" "$WORK/ots.ttf"
python3 validate_font.py "$OUT" roundtrip
python3 validate_shaping.py "$OUT" "$WORK/shaping_report.txt"
PFSF_FILL_BASE="$WORK/step8.ttf" python3 validate_fill.py "$OUT" "$WORK/fill_parts" data/fill_sources.json "$WORK/fill_report.txt"
python3 coverage_stats.py "$OUT"
