#!/usr/bin/env bash
# 下载并解包构建所需的源字体到 ../sources（不随仓库分发）
# 依赖: gh (GitHub CLI) 或 curl, 7z, unzip
set -euo pipefail
cd "$(dirname "$0")/.."
S=sources; mkdir -p "$S/v21" "$S/mvf" "$S/sf"
# 1) PingFang UI 可变字体 TTC（ACT-02/PingFangUI-VF, release 21.4d1e1）
if [ ! -f "$S/v21/PingFangUI.tahoe.26.4.1.wght.wdth.ttc" ]; then
  gh release download 21.4d1e1 -R ACT-02/PingFangUI-VF -D "$S/v21" -p 'PingFangUI.tahoe.26.4.1.wght.wdth.ttc'
fi
# 2) SF Pro（Apple Developer 官方 DMG）
if [ ! -f "$S/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf" ]; then
  curl -L -C - -o "$S/SF-Pro.dmg" https://devimages-cdn.apple.com/design/resources/download/SF-Pro.dmg
  ( cd "$S/sf" && 7z e -y ../SF-Pro.dmg >/dev/null && 7z x -y -txar SFProFonts.pkg >/dev/null \
    && cd SFProFontsPackage.pkg && 7z x -y Payload >/dev/null && 7z x -y 'Payload~' >/dev/null )
fi
# 3) MiSans 多语种（小米官方 https://hyperos.mi.com/font/download 的“一键下载全部”包）
if [ ! -f "$S/mvf/Tibetan.ttf" ]; then
  until curl -L -C - -o "$S/MiSans_Global_ALL.zip" https://hyperos.mi.com/font-download/MiSans_Global_ALL.zip; do sleep 2; done
  T="$S/misans"; mkdir -p "$T"; unzip -q -o "$S/MiSans_Global_ALL.zip" -d "$T" -x '__MACOSX/*'
  B="$T/MiSans Global _ALL"
  ( cd "$B" && for z in *.zip; do unzip -q -o "$z" -x '__MACOSX/*'; done )
  cp "$B/ MiSans Lao/MiSansLaoVF.ttf"                 "$S/mvf/Lao.ttf"
  cp "$B/MiSana Arabic/MiSansArabicVF.ttf"            "$S/mvf/Arabic.ttf"
  cp "$B/MiSans Devanagari/MiSans Devanagari VF.ttf"  "$S/mvf/Devanagari.ttf"
  cp "$B/MiSans Gujarati/MiSans Gujarati VF.ttf"      "$S/mvf/Gujarati.ttf"
  cp "$B/MiSans Gurmukhi/MiSans Gurmukhi VF.ttf"      "$S/mvf/Gurmukhi.ttf"
  cp "$B/MiSans Khmer/MiSansKhmerVF.ttf"              "$S/mvf/Khmer.ttf"
  cp "$B/MiSans Myanmar/MiSans Myanmar VF.ttf"        "$S/mvf/Myanmar.ttf"
  cp "$B/MiSans Thai /MiSansThaiVF.ttf"               "$S/mvf/Thai.ttf"
  cp "$B/MiSans Tibetan/MiSansTibetanVF.ttf"          "$S/mvf/Tibetan.ttf"
fi
sha256sum "$S/v21/"*.ttc "$S/sf/SFProFontsPackage.pkg/Library/Fonts/SF-Pro.ttf" "$S/mvf/"*.ttf
