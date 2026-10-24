"""Audio QA: loudness of the delivered file, and whether every planned hit actually lands on its cut.

  python3 scripts/qa_audio.py deliver/product-en.mp4 --music audio/music.json [--tol 0.03]
Loudness via ffmpeg ebur128 (target −14 LUFS integrated, true peak ≤ −1 dBTP). Hits: the low band (< 150 Hz) onset nearest
to each time in music.json "hits" must be within --tol seconds.
"""
import argparse, json, re, subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument('media'); ap.add_argument('--music', default=None); ap.add_argument('--tol', type=float, default=0.03)
a = ap.parse_args()
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', a.media, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); P = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
print(f'integrated {I:.1f} LUFS, true peak {P:.1f} dBTP'); ok = abs(I + 14) <= 1.0 and P <= -1.0
if a.music:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.media, '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], capture_output=True).stdout
    x = sosfilt(butter(4, 150, 'low', fs=8000, output='sos'), np.frombuffer(raw, np.float32))
    hop = 40; e = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))[::hop]; flux = np.maximum(0, np.diff(e, prepend=e[0]))
    for h in json.load(open(a.music))['hits']:
        i0, i1 = int((h - 0.08) * 200), int((h + 0.08) * 200); k = i0 + int(np.argmax(flux[i0:i1])); dt = k / 200 - h
        flag = abs(dt) > a.tol; ok &= not flag
        print(f'hit {h:7.3f}s  onset {dt*1000:+5.0f} ms {"  <-- off" if flag else ""}')
sys.exit(0 if ok else 1)
