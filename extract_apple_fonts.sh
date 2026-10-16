#!/usr/bin/env bash
# 从 Apple 字体 .dmg 中提取 TTF/OTF（参考 AUR apple-fonts 的 PKGBUILD）
# 用法: ./extract_apple_fonts.sh SF-Pro.dmg OUTDIR
# 依赖: 7z (p7zip-full)
set -euo pipefail
DMG="$1"; OUT="${2:-apple_fonts}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
7z e -y -o"$TMP" "$DMG" >/dev/null                 # dmg -> *.pkg
cd "$TMP"
for pkg in *.pkg; do
  7z x -y -txar "$pkg" >/dev/null                  # xar -> Payload
done
for payload in $(find . -name Payload -type f); do
  d="$(dirname "$payload")"
  (cd "$d" && 7z x -y Payload >/dev/null && { [ -f 'Payload~' ] && 7z x -y 'Payload~' >/dev/null || true; })
done
mkdir -p "$OLDPWD/$OUT" 2>/dev/null || mkdir -p "$OUT"
find . -path '*Library/Fonts/*' \( -name '*.ttf' -o -name '*.otf' \) -exec cp {} "$OLDPWD/$OUT/" \;
echo "fonts extracted to $OUT"
