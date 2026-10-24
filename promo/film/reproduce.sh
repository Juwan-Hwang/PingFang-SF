#!/bin/sh
# Rebuild both cuts of the PingFang SF launch film from committed inputs.
#   sh reproduce.sh                → deliver/pingfang-sf-promo-{en,zh}.rebuild.mp4
#   LANGS=zh sh reproduce.sh       → one cut
#   RE3D=1 sh reproduce.sh         → also re-render the 3D open / reprise frames (film/frames/{open,end}) from film/p3d.html
# Audio is seeded (score rng 7, SFX jitter 11, room 3); frames that already exist are skipped (resumable).
set -e
cd "$(dirname "$0")"
sh setup.sh
(python3 -m http.server 8777 --directory film >/tmp/pfsf-film-http.log 2>&1 &)
sleep 1
if [ "${RE3D:-0}" = 1 ]; then
  rm -rf film/frames/open film/frames/end
  python3 r3d_seq.py open 6.0 film/frames/open --page p3d.html --sub 6
  for i in $(seq 57 71); do rm -f film/frames/open/$(printf %04d $i).jpg; done        # the landing swing gets a 20-sample shutter
  python3 r3d_seq.py open 6.0 film/frames/open --page p3d.html --sub 20 --from 57 --to 72
  python3 r3d_seq.py end 2.5 film/frames/end --page p3d.html --sub 7 --handoff "comp.html?lang=en"
fi
python3 scripts/dump_events.py --comp "comp.html?lang=en" --out audio/events_en.json
python3 music.py --events audio/events_en.json --out audio            # one score for both cuts (identical hits)
for L in ${LANGS:-en zh}; do
  python3 scripts/dump_events.py --comp "comp.html?lang=$L" --out "audio/events_$L.json"
  python3 sound.py --events "audio/events_$L.json" --music audio/music.wav --out "audio/mix_$L.wav"
  python3 render_film.py --comp "comp.html?lang=$L" --out "film/out/frames_$L" --workers 2 --from 900 --to 997 --sub 12 --gap 20 --max-seconds 100000
  N=1755
  while [ "$(ls "film/out/frames_$L" 2>/dev/null | grep -c '^[0-9]*\.jpg$')" -lt "$N" ]; do
    python3 render_film.py --comp "comp.html?lang=$L" --out "film/out/frames_$L" --workers 2 --max-seconds 1100
  done
  ./encode.sh "film/out/frames_$L" "audio/mix_$L.wav" "deliver/pingfang-sf-promo-$L.rebuild.mp4"
done
