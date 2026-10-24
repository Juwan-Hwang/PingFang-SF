"""PingFang SF launch film: sound effects from earshot's code-generated bank (github.com/Leonxlnx/earshot @ 925ebe5), placed from the comp's
events, PEAK-ALIGNED (each sound's loudest sample lands exactly on its event time, not its file start), put in one
shared room, and mixed under the score.

  python3 sound.py --events audio/events_en.json --music audio/music.wav --out audio/mix_en.wav
Edit SFX: event kind → (earshot id, time offset s, gain dB, pan). Unknown kinds are ignored (and reported).
"""
import argparse, json
from collections import Counter
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt
from earshot.forge import bank

SR = 48000
# EDIT. Offsets: whooshes lead their cut by ~50 ms; "landing" sounds trail it slightly. Keys sit at −21…−24 dB with ±2 dB jitter.
SFX = {
    'key':    ('fit/key/lubed', 0.0, -21, 0.0),
    'tkey':   ('pro_typing_key/soft', 0.0, -22, 0.1),
    'enter':  ('fit/key/thock', 0.0, -17, 0.05),
    'carry':  ('whoosh_fast/crisp', -0.05, -15, 0.0),
    'dive':   ('whoosh_fast/crisp', 0.45, -13, 0.0),
    'swell':  ('pro_whoosh_big/swell', 0.55, -14, 0.0),
    'close':  ('pro_whoosh_big/reverse', -0.1, -18, 0.0),
    'pull':   ('pro_whoosh_big/reverse', 0.2, -15, 0.0),
    'morph':  ('pro_whoosh_big/swell', 0.35, -19, 0.0),
    'whip':   ('whoosh_fast/crisp', 0.25, -16, 0.25),
    'flow':   ('swish/soft', 0.3, -16, 0.0),
    'push':   ('swish/soft', 0.15, -20, 0.0),
    'tick':   ('pro_click/glass', 0.0, -19, 0.0),
    'tap':    ('pro_tap/glass', 0.0, -16, 0.0),
    'out':    ('pro_hover_tick/glass', 0.0, -24, 0.15),
    'open':   ('pro_pop_in/round', 0.0, -17, 0.0),
    'pop':    ('pro_pop/chirp', 0.08, -18, 0.15),
    'rise':   ('swish/soft', 0.2, -22, 0.0),
    'land':   ('pro_impact/short', 0.0, -17, 0.0),
    'hit':    ('pro_whoosh_big/swell', -0.05, -17, 0.0),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--events', default='audio/events.json'); ap.add_argument('--music', default='audio/music.wav')
    ap.add_argument('--out', default='audio/mix.wav'); ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args()
    E = json.load(open(a.events)); EV, DUR = E['events'], E['meta']['dur']
    music, msr = sf.read(a.music, dtype='float32'); assert msr == SR, 'music must be 48 kHz'
    N = int((DUR + 0.2) * SR); fx = np.zeros((N, 2), np.float32); cache = {}

    def snd(sid):
        if sid not in cache:
            y, meta = bank.render(sid); y = np.asarray(y, np.float32)
            sr = meta.get('sr', SR) if isinstance(meta, dict) else SR
            if sr != SR:
                import soxr; y = soxr.resample(y, sr, SR).astype(np.float32)
            if y.ndim == 1: y = np.stack([y, y], 1)
            cache[sid] = (y, int(np.argmax(np.abs(y).sum(1))))
        return cache[sid]

    def place(sid, t, gain_db, pan):
        y, pk = snd(sid); g = 10 ** (gain_db / 20)
        l, r = np.cos((pan + 1) * np.pi / 4) * 1.414, np.sin((pan + 1) * np.pi / 4) * 1.414
        i = int(round(t * SR)) - pk; s0, s1 = max(0, i), min(N, i + len(y))
        if s1 <= s0: return
        seg = y[s0 - i:s1 - i]; fx[s0:s1, 0] += seg[:, 0] * g * l; fx[s0:s1, 1] += seg[:, 1] * g * r

    rk = np.random.default_rng(a.seed); missing = Counter()
    for e in EV:
        kind = e['kind'] + ('.soft' if e.get('soft') and e['kind'] + '.soft' in SFX else '')
        if kind not in SFX: missing[kind] += 1; continue
        sid, off, gdb, pan = SFX[kind]
        if e['kind'] in ('key', 'tkey'): gdb += rk.uniform(-2, 2); pan = rk.uniform(-0.25, 0.25)        # humanise keystrokes
        if e['kind'] == 'tap': pan = -0.3 if e['k'] % 2 else 0.3
        if e['kind'] == 'tick': pan = e.get('pan', 0)
        place(sid, e['t'] + off, gdb, pan)

    n = int(1.2 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(3)                  # ONE room for every effect
    ir = rng.standard_normal((n, 2)) * np.exp(-tt * 5.0)[:, None]
    ir = sosfilt(butter(2, 6000, 'low', fs=SR, output='sos'), ir, axis=0); ir[:500] = 0; ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
    fx = fx + 0.22 * np.stack([fftconvolve(fx[:, c], ir[:, c])[:N] for c in range(2)], 1)
    m = np.zeros((N, 2), np.float32); L = min(N, len(music)); m[:L] = music[:L]
    fade = int(0.9 * SR); m[N - fade:] *= (np.linspace(1, 0, fade) ** 1.5)[:, None]              # the score fades with the picture
    mix = m + fx; peak = float(np.abs(mix).max()); mix = mix / peak * 0.6
    sf.write(a.out, mix.astype(np.float32), SR, subtype='FLOAT')
    print(a.out, 'events', len(EV), 'dur', round(DUR, 2), 'peak', round(peak, 3), 'unmapped kinds', dict(missing))


if __name__ == '__main__':
    main()
