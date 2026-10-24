#!/bin/sh
# encode.sh FRAMES_DIR MIX_WAV OUT.mp4 [FPS]
# JPEG frames + float WAV → H.264 High CRF 16 (yuv420p, BT.709 limited range, faststart, -tune film) + AAC 256k 48 kHz,
# loudness-normalised with TWO-PASS loudnorm to −14 LUFS integrated / −1.5 dBTP (the streaming target; one-pass loudnorm
# is dynamic and pumps). Prints the measured loudness of the result so QA can check it.
#   ./encode.sh film/out/frames_en audio/mix_en.wav deliver/product-launch-en.mp4
set -e
FR=${1:?frames dir}; MIX=${2:?mix wav}; OUT=${3:?out mp4}; FPS=${4:-30}
mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp /tmp/encode.XXXXXX).mp4   # mux on local disk: the +faststart rewrite failed once on a network filesystem (I/O error on the trailer)
J=$(ffmpeg -hide_banner -i "$MIX" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
set -- $(echo "$J" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")
ffmpeg -y -hide_banner -loglevel error -framerate "$FPS" -i "$FR/%05d.jpg" -i "$MIX" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$1:measured_TP=$2:measured_LRA=$3:measured_thresh=$4:offset=$5:linear=true,aresample=48000" \
  -vf "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p" -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -tune film -movflags +faststart \
  -c:a aac -b:a 256k -ar 48000 -shortest "$TMP"
cp "$TMP" "$OUT" && rm -f "$TMP"
ffmpeg -hide_banner -nostats -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|Peak:|LRA:)" | tr -s ' ' | sed 's/^/  /'
echo "done $OUT"
