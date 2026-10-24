"""PingFang SF launch film: original score, synthesised in numpy: no samples, no licences, fully reproducible (fixed seeds).

120 BPM (bar = 2.000 s), F major (F – Dm – B♭ – C, C pedal in the build), 29.25 bars (58.5 s).
Built on the launch-film skill's template (Zephyr 124 BPM D minor, omni2api 120 BPM A minor). The arrangement is a list of
SECTIONS on the bar grid; the HITS come from the comp's own events (dump_events.py), so every cut lands on a kick +
sub drop, risers END exactly on the hit, and the cursor's typing blips are on the same clock as the picture.

  python3 music.py --events audio/events_en.json            # → audio/music.wav, audio/stems/*.wav, audio/music.json
Edit the CONFIG block; keep the instruments.
"""
import argparse, json, os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

# ───────── CONFIG (EDIT) ─────────
SR = 48000
BPM = 120                                  # must equal the comp's BPM; 120 → bar = 2.0 s, 124 → bar = 1.935 s
SEED = 7
# chords as MIDI voicings; the progression cycles per bar inside 'groove'/'full' sections
CH = {'F': [53, 60, 65, 69], 'Dm': [50, 57, 62, 65], 'Bb': [46, 53, 58, 62], 'C': [48, 55, 60, 64], 'Fadd9': [53, 60, 67, 69]}
ROOT = {'F': 29, 'Dm': 26, 'Bb': 34, 'C': 36, 'Fadd9': 29}
ARP = {'F': [81, 77, 84, 79, 81, 89, 84, 77], 'Dm': [81, 77, 86, 81, 84, 89, 86, 77], 'Bb': [82, 77, 86, 81, 82, 89, 86, 77],
       'C': [79, 76, 84, 79, 83, 88, 84, 76], 'Fadd9': [81, 79, 84, 77, 81, 91, 84, 79]}
PROG = ['F', 'Dm', 'Bb', 'C']
TONIC, PEDAL = 'Fadd9', 'C'
# bars match comp.html's T table: open 0–3, thesis 3–5, specimen 5–11 (harmony bright, variable groove), scripts 11–15,
# glyph grid 15–18, vertical 18–20, terminal 20–23, finale 23–25 (build), 3D reprise + lockup 25–29.25 (resolve)
SECTIONS = [(0, 3, 'air'), (3, 5, 'pulse'), (5, 8, 'bright'), (8, 11, 'groove'), (11, 18, 'full'), (18, 20, 'bright'),
            (20, 23, 'groove'), (23, 25, 'build'), (25, 29.25, 'resolve')]
HIT_KINDS = {'hit'}                        # bar-line cuts: kick + sub drop (+ a riser into them)
BLIP_KINDS = {'tick', 'pop'}               # the dot's voice: metric lines drawing in, the tittle's hop
BELL_KINDS = {'land'}                      # the lockup landing
TAP_KINDS = {'tap'}                        # one pluck per script greeting (eighth notes)
# ─────────────────────────────────

BEAT = 60 / BPM
BAR = BEAT * 4
rng = np.random.default_rng(SEED)


def tb(bar, beat=0.0):
    return bar * BAR + beat * BEAT


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x, axis=0)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x, axis=0)


def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], 'band', fs=SR, output='sos'), x, axis=0)


def env_adsr(n, a, d, s, r):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.ones(n) * s
    if a: e[:a] = np.linspace(0, 1, a, endpoint=False)[:n]
    e[a:a + d] = np.linspace(1, s, max(1, len(e[a:a + d])))
    if r:
        st = max(0, n - r); e[st:] *= (np.linspace(1, 0, r) ** 2)[: n - st]
    return e


def saw(f, n, phase=0.0):
    ph = (f * np.arange(n) / SR + phase) % 1.0
    return 2 * ph - 1


def reverb_ir(sec, damp, pre=0.012):
    n = int(sec * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-damp * t)[:, None]
    ir = lp(ir, 7500); ir[: int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(0, keepdims=True))
    return ir.astype(np.float32)


# ───────── instruments ─────────
def kick(g=1.0):
    n = int(0.55 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = hp(rng.standard_normal(n) * np.exp(-t * 300), 2500) * 0.25
    return np.tanh((body + click) * 1.6) * g


def sub_drop(f0=82, f1=31, sec=2.2):
    n = int(sec * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 2.4)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.18 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return np.tanh(s * 1.4) * np.exp(-t * 1.7) * np.minimum(1, t * 400)


def snap():
    n = int(0.32 * SR); t = np.arange(n) / SR
    e = np.exp(-t * 38) + 0.5 * np.exp(-np.maximum(0, t - 0.011) * 45) * (t > 0.011)
    return bp(rng.standard_normal(n) * e, 900, 5200) * 0.9


def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7800, 3) * np.exp(-t * (14 if open_ else 75)) * 0.5


def pluck(m, sec=0.9, bright=1.0):        # FM glass pluck
    n = int(sec * SR); t = np.arange(n) / SR; f = midi(m)
    mod = np.sin(2 * np.pi * f * 3.0 * t) * (2.2 * bright) * np.exp(-t * 9)
    car = np.sin(2 * np.pi * f * t + mod) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t + mod * 0.5)
    return car * np.exp(-t * 5.2) * np.minimum(1, t * 900) * 0.5


def bell(m, sec=4.5):
    n = int(sec * SR); t = np.arange(n) / SR; f = midi(m)
    s = (np.sin(2 * np.pi * f * t + 1.4 * np.exp(-t * 2) * np.sin(2 * np.pi * f * 3.5 * t))
         + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 2.5) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 4))
    return s * np.exp(-t * 0.9) * np.minimum(1, t * 600) * 0.4


def bass(m, sec, cutoff=520):
    n = int(sec * SR); t = np.arange(n) / SR; f = midi(m)
    s = lp(0.6 * saw(f, n) + 0.4 * saw(f * 1.004, n, 0.3) + 0.5 * np.sin(2 * np.pi * f * t), cutoff, 3)
    return np.tanh(s * env_adsr(n, 0.006, 0.18, 0.62, 0.08) * 1.3) * 0.55


def pad(notes, sec, cutoff=1800, attack=0.9, release=1.6):
    n = int(sec * SR); out = np.zeros((n, 2))
    for m in notes:
        for k, det in enumerate([-0.11, -0.05, 0.0, 0.05, 0.11]):      # 5-voice supersaw, spread across the field
            v = saw(midi(m) * 2 ** (det / 12), n, rng.random()); pan = (k - 2) / 2.2
            out[:, 0] += v * np.cos((pan + 1) * np.pi / 4); out[:, 1] += v * np.sin((pan + 1) * np.pi / 4)
    return lp(out, cutoff, 2) * env_adsr(n, attack, 0.5, 0.85, release)[:, None] * (0.075 / max(1, len(notes) ** 0.5))


def riser(sec, f0=300, f1=6000):          # swept band noise + rising tone, ENDS on its target time
    n = int(sec * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); out = np.zeros(n); k = 24; sl = n // k
    for i in range(k):
        a, b = i * sl, (n if i == k - 1 else (i + 1) * sl); fc = f0 * (f1 / f0) ** (i / (k - 1))
        out[a:b] = bp(x[max(0, a - 2000):b], fc * 0.7, min(fc * 1.4, SR / 2 - 200))[-(b - a):]
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2.0 * t / sec)) / SR) * 0.15
    return (out * 0.8 + tone) * (t / sec) ** 2.2


def air(sec):
    n = int(sec * SR); t = np.arange(n) / SR
    return bp(rng.standard_normal((n, 2)), 400, 3200) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 7.0))[:, None] * 0.06


def blip(m, sec=0.09, g=1.0):              # square-ish terminal blip: the carry element's voice
    n = int(sec * SR); t = np.arange(n) / SR; f = midi(m)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5
    return lp(s * np.exp(-t * 28) * np.minimum(1, t * 3000), 5000) * 0.3 * g


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--events', default='audio/events.json'); ap.add_argument('--out', default='audio')
    a = ap.parse_args()
    E = json.load(open(a.events)); EV = E['events']; DUR = E['meta']['dur'] + 0.1
    if abs(E['meta'].get('bpm', BPM) - BPM) > 1e-6:
        raise SystemExit(f"BPM mismatch: comp {E['meta'].get('bpm')} vs music {BPM}")
    N = int(DUR * SR)
    os.makedirs(f'{a.out}/stems', exist_ok=True)
    buf = lambda: np.zeros((N, 2), np.float32)
    drums, bassb, padb, keys, fx = buf(), buf(), buf(), buf(), buf()

    def add(dst, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i < 0 or i >= N: return
        if sig.ndim == 1:
            l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
        j = min(N, i + len(sig)); dst[i:j] += sig[: j - i] * gain

    def groove_bar(b, c, four=True, hats=True, arp_oct=0, arp_g=0.18):
        for q in range(4):
            if four or q in (0, 2): add(drums, kick(0.95), tb(b, q))
            if q in (1, 3): add(drums, snap(), tb(b, q), 0.40, 0.05)
        if hats:
            for s16 in range(16): add(drums, hat(s16 % 8 == 6), tb(b, s16 * 0.25), 0.17 if s16 % 4 == 2 else 0.07, 0.35)
        for e8 in range(8):
            add(bassb, bass(ROOT[c] + (12 if e8 in (3, 7) else 0), BEAT * 0.45, 380 + 300 * (e8 % 2 == 0)), tb(b, e8 * 0.5), 0.9 if e8 % 2 == 0 else 0.6)
        for i in range(8): add(keys, pluck(ARP[c][i] + arp_oct, 0.45, 0.9), tb(b, i * 0.5), arp_g, -0.45 if i % 2 else 0.45)

    for (b0, b1, en) in SECTIONS:
        bars = np.arange(b0, b1, 1.0)
        for j, b in enumerate(bars):
            c = PROG[int(b) % len(PROG)]
            span = min(1.0, b1 - b) * BAR
            if en == 'air':
                if j == 0: add(fx, air((b1 - b0) * BAR + 2), tb(b), 1.2)
                if j == 1: add(padb, pad(CH[TONIC], (b1 - b) * BAR + 1.2, 900, 0.5, 1.4), tb(b))
            elif en == 'pulse':
                for q in range(4): add(drums, kick(0.55), tb(b, q), 0.55)
                for e8 in range(8): add(bassb, bass(ROOT[c], BEAT * 0.4, 300), tb(b, e8 * 0.5), 0.55)
                add(padb, pad(CH[c], span + 0.7, 1100, 0.3, 0.8), tb(b), 0.8)
            elif en == 'bright':
                for i in range(8): add(keys, pluck(ARP[c][i], 0.5, 1.1), tb(b, i * 0.5), 0.2, -0.45 if i % 2 else 0.45)
                for q in (0, 2): add(drums, kick(0.6), tb(b, q))
                add(padb, pad(CH[c], span + 0.4, 2600, 0.15, 0.6), tb(b))
            elif en in ('groove', 'full'):
                groove_bar(b, c, four=(j > 0 or en == 'full'), arp_oct=12 if en == 'full' else 0, arp_g=0.2 if en == 'full' else 0.16)
                if en == 'full' or j % 2 == 0: add(padb, pad(CH[c], (span if en == 'full' else 2 * BAR) + 0.6, 2600 if en == 'full' else 1500, 0.2, 0.7), tb(b), 0.85)
                if en == 'full': add(keys, bell(CH[c][-1] + 12, 2.0), tb(b), 0.12)
            elif en == 'build':                    # drop to a pedal, snare roll, riser into the next downbeat
                add(padb, pad(CH[PEDAL], span + 0.3, 1800, 0.1, 0.4), tb(b), 0.9)
                for e8 in range(4): add(bassb, bass(ROOT[PEDAL], BEAT * 0.45, 500), tb(b, e8), 0.7)
                for i in range(12): add(drums, snap(), tb(b, 1) + i * BEAT / 4, 0.04 + 0.26 * (i / 11) ** 2)
            elif en == 'resolve' and j == 0:
                add(padb, pad([ROOT[TONIC]] + [m - 12 for m in CH[TONIC]] + CH[TONIC], (b1 - b0) * BAR + 1, 2000, 0.05, 3.0), tb(b), 1.25)
                for m, g, p in [(CH[TONIC][2], 0.32, 0.2), (CH[TONIC][3] + 4, 0.22, -0.25), (CH[TONIC][0], 0.28, 0.0)]: add(keys, bell(m, 7.0), tb(b), g, p)

    hits = sorted({round(e['t'], 3) for e in EV if e['kind'] in HIT_KINDS})
    for k, t in enumerate(hits):
        big = t >= SECTIONS[-1][0] * BAR - 1e-3 or k == 0
        add(drums, kick(1.35 if big else 1.15), t); add(drums, sub_drop(84 if big else 76, 28 if big else 32, 3.4 if big else 1.4), t, 1.0 if big else 0.7)
        if t > 1.0: add(fx, riser(0.6 if not big else 1.2, 500, 9000), t - (0.6 if not big else 1.2), 0.6)
    for e in EV:
        if e['kind'] in BLIP_KINDS:
            k = int(round((e.get('pan', 0) + 0.4) / 0.2)) if e['kind'] == 'tick' else 5; add(keys, blip([72, 74, 77, 79, 81, 84][k % 6], 0.07), e['t'], 0.4, e.get('pan', 0))
        elif e['kind'] in BELL_KINDS:
            add(keys, bell(CH[TONIC][-1] + 12, 3.0), e['t'], 0.16)
        elif e['kind'] in TAP_KINDS:
            k = e.get('k', 0); add(keys, pluck(ARP[PROG[int(e['t'] / BAR) % 4]][k % 8] + 12, 0.35, 1.0), e['t'], 0.16, -0.35 if k % 2 else 0.35)

    drums = hp(sosfilt(butter(1, 18000, 'low', fs=SR, output='sos'), drums, axis=0), 38)
    ih, ir_ = reverb_ir(3.4, 2.1), reverb_ir(1.1, 5.5)
    verb = lambda x, ir, wet: x + np.stack([fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1) * wet
    drums, keys, padb, fx = verb(drums, ir_, 0.18), verb(keys, ih, 0.42), verb(padb, ih, 0.35), verb(fx, ih, 0.3)
    stems = {'drums': drums * 0.55, 'bass': hp(lp(bassb, 3000), 45) * 0.42, 'pad': padb * 2.2, 'keys': keys * 2.3, 'fx': fx * 1.3}
    mix = hp(sum(stems.values()), 28)
    fade = int(0.9 * SR); mix[-fade:] *= (np.linspace(1, 0, fade) ** 1.5)[:, None]
    peak = float(np.abs(mix).max()); g = 0.7 / peak                  # leave headroom: the SFX go on top, loudnorm comes last
    for k, v in stems.items(): sf.write(f'{a.out}/stems/{k}.wav', (v * g).astype(np.float32), SR, subtype='FLOAT')
    sf.write(f'{a.out}/music.wav', (mix * g).astype(np.float32), SR, subtype='FLOAT')
    json.dump({'bpm': BPM, 'beat': BEAT, 'bar': BAR, 'dur': DUR, 'seed': SEED, 'hits': hits, 'sections': SECTIONS}, open(f'{a.out}/music.json', 'w'), indent=1)
    print('music', round(DUR, 2), 's', len(hits), 'hits', hits)


if __name__ == '__main__':
    main()
