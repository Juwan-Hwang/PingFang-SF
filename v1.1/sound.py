#!/usr/bin/env python3
"""Procedural soundtrack for the PingFang SF promo, locked to promo.html's timeline.
Everything is synthesized here (numpy/scipy) — no samples."""
import numpy as np, scipy.signal as ss, scipy.io.wavfile as wav, pyloudnorm as pyln

SR = 48000
DUR = 40.6
N = int(SR * DUR)
rng = np.random.default_rng(1234)
L = np.zeros(N); R = np.zeros(N)          # dry bus
RL = np.zeros(N); RR = np.zeros(N)        # reverb send

def t_(n): return np.arange(n) / SR
def idx(t): return int(round(t * SR))
def add(sig, t0, gain=1.0, pan=0.0, rev=0.25, sigR=None):
    """pan -1..1 (equal power); sigR optional separate right channel"""
    i0 = idx(t0)
    if i0 >= N: return
    if i0 < 0: sig = sig[-i0:]; sigR = None if sigR is None else sigR[-i0:]; i0 = 0
    n = min(len(sig), N - i0)
    a = (pan + 1) * np.pi / 4
    gl, gr = np.cos(a) * gain * np.sqrt(2), np.sin(a) * gain * np.sqrt(2)
    s2 = sig if sigR is None else sigR
    L[i0:i0+n] += sig[:n] * gl; R[i0:i0+n] += s2[:n] * gr
    RL[i0:i0+n] += sig[:n] * gl * rev; RR[i0:i0+n] += s2[:n] * gr * rev

def sos(kind, f, order=2):
    if isinstance(f, (list, tuple)): f = [min(x, SR/2*0.95) for x in f]
    else: f = min(f, SR/2*0.95)
    return ss.butter(order, f, btype=kind, fs=SR, output='sos')
def filt(x, kind, f, order=2): return ss.sosfilt(sos(kind, f, order), x)
def env_adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a*SR), int(d*SR), int(r*SR)
    sl = n - a - d - r if sus_len is None else int(sus_len*SR)
    sl = max(sl, 0)
    e = np.concatenate([np.linspace(0, 1, max(a,1)), np.linspace(1, s, max(d,1)), np.full(sl, s), np.linspace(s, 0, max(r,1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n-len(e)))
def expdec(n, tau): return np.exp(-t_(n) / tau)
def noise(n): return rng.standard_normal(n)
def sweep_sine(n, f0, f1, curve=3.0):
    tt = t_(n); T = n / SR
    f = f1 + (f0 - f1) * np.exp(-curve * tt / T * 3)  # fast exp drop
    return np.sin(2*np.pi*np.cumsum(f)/SR)
def tvfilter(x, kind, fc_func, block=256, order=2):
    """time-varying butterworth: fc_func(t_seconds_array_of_block_starts) -> Hz"""
    out = np.zeros_like(x); zi = None
    for b0 in range(0, len(x), block):
        fc = float(fc_func(b0 / SR))
        s = sos(kind, max(20, fc), order)
        if zi is None: zi = np.zeros((s.shape[0], 2))
        out[b0:b0+block], zi = ss.sosfilt(s, x[b0:b0+block], zi=zi)
    return out
def note(m): return 440.0 * 2 ** ((m - 69) / 12)

# ---------------- elements ----------------
def thump(f=52, dur=0.5, click=0.4):
    n = int(dur*SR); tt = t_(n)
    f_ = f * (1 + 1.6*np.exp(-tt/0.025))
    s = np.sin(2*np.pi*np.cumsum(f_)/SR) * expdec(n, dur/4)
    c = filt(noise(n), 'lowpass', 1800) * expdec(n, 0.006) * click
    return np.tanh(1.6*(s + c))
def boom(dur=5.0, big=1.0):
    n = int(dur*SR); tt = t_(n)
    f = 28 + 110*np.exp(-tt/0.08) + 20*np.exp(-tt/0.9)
    sub = np.sin(2*np.pi*np.cumsum(f)/SR) * (expdec(n, 0.6*big))
    body = filt(noise(n), 'lowpass', 420) * expdec(n, 0.45*big) * 1.6
    crack = filt(noise(n), 'highpass', 1500) * expdec(n, 0.09) * 1.6
    mid = filt(noise(n), 'bandpass', [120, 2400]) * expdec(n, 0.35) * 1.5
    x = sub*1.25 + body + crack + mid
    return np.tanh(1.3*x) * env_adsr(n, 0.002, 0.01, 1, 0.3)
def shimmer(dur=3.5, base=2400, seed=0):
    n = int(dur*SR); tt = t_(n); r = np.random.default_rng(seed); x = np.zeros(n)
    for k in range(14):
        f = base * (1 + r.random()*2.6); ph = r.random()*6.28
        x += np.sin(2*np.pi*f*tt + ph) * (0.6 + 0.4*np.sin(2*np.pi*(5+r.random()*7)*tt + ph)) / 14
    hiss = filt(noise(n), 'highpass', 6000) * 0.25
    return (x + hiss) * expdec(n, dur/3.2) * env_adsr(n, 0.01, 0.1, 1, 0.5)
def whoosh(dur=1.2, f0=300, f1=4000, peak=0.6, q=0.35):
    """filtered noise with pitch (centre freq) sweep and doppler-ish swell; peak = rel. position of max"""
    n = int(dur*SR); x = noise(n)
    pk = peak*dur
    def fc(t): return f0 * (f1/f0) ** min(1, t/pk) if t < pk else f1 * (f0*1.6/f1) ** ((t-pk)/(dur-pk))
    lo = tvfilter(x, 'lowpass', lambda t: fc(t)*1.6)
    y = tvfilter(lo, 'highpass', lambda t: fc(t)*q)
    tt = t_(n); e = np.where(tt < pk, (tt/pk)**2.2, np.exp(-(tt-pk)/((dur-pk)/3)))
    return y * e
def pluck(m, dur=1.2, bright=6000, harm=8):
    n = int(dur*SR); tt = t_(n); f = note(m); x = np.zeros(n)
    for h in range(1, harm+1):
        if f*h > 16000: break
        x += np.sin(2*np.pi*f*h*tt) * (1/h**1.3) * np.exp(-tt*(2.0 + h*1.2))
    x += np.sin(2*np.pi*f*2.01*tt) * 0.15 * np.exp(-tt*6)
    return filt(x, 'lowpass', bright) * env_adsr(n, 0.002, 0.05, 1, 0.1)
def bell(m, dur=3.0):
    n = int(dur*SR); tt = t_(n); f = note(m); x = np.zeros(n)
    for ratio, a, d in [(1, 1, 1.6), (2.0, .5, 1.0), (2.76, .35, .7), (5.4, .2, .35), (8.93, .1, .2)]:
        x += a*np.sin(2*np.pi*f*ratio*tt) * np.exp(-tt/d)
    return x * env_adsr(n, 0.003, 0.05, 1, 0.3) * 0.5
def blip(f=1800, dur=0.07, f2=None):
    n = int(dur*SR); tt = t_(n); f2 = f if f2 is None else f2
    ff = f + (f2 - f) * tt/dur
    return np.sin(2*np.pi*np.cumsum(ff)/SR) * expdec(n, dur/4) * env_adsr(n, 0.001, 0.01, 1, 0.01)
def tick(dur=0.018, f=4200):
    n = int(dur*SR)
    return filt(noise(n), 'bandpass', [f*0.7, f*1.4]) * expdec(n, 0.003) + np.sin(2*np.pi*f*0.5*t_(n))*expdec(n, 0.004)*0.4
def brush(dur=0.35, fc=2600, seed=0):
    n = int(dur*SR); r = np.random.default_rng(seed)
    x = r.standard_normal(n)
    gr = (r.random(n) < 0.08) * r.random(n) * 3  # grainy fibre texture
    x = filt(x*0.6 + gr, 'bandpass', [fc*0.45, fc*1.8])
    tt = t_(n); e = np.sin(np.pi*np.clip(tt/dur, 0, 1))**1.5
    return x * e
def riser(dur, f0=200, f1=3000, tone=True):
    n = int(dur*SR); tt = t_(n); p = tt/dur
    x = tvfilter(noise(n), 'bandpass_dummy' if False else 'lowpass', lambda t: f0*(f1/f0)**(t/dur)) * p**2.2
    x = filt(x, 'highpass', 160)
    if tone:
        ff = 70*(1+3*p**2)
        x += 0.15*np.sin(2*np.pi*np.cumsum(ff)/SR) * p**2
    return x

# ---------------- PAD / chord bed ----------------
def pad_voice(freqs, n, bright=1800, seed=0):
    r = np.random.default_rng(seed); tt = t_(n); x = np.zeros(n)
    for f in freqs:
        for det in (-0.07, 0.0, 0.065):
            ff = f * 2**(det/12)
            ph = r.random()*6.28
            for h in range(1, 9):
                if ff*h > 9000: break
                x += np.sin(2*np.pi*ff*h*tt + ph*h) / h**1.15
    lfo = 0.5 + 0.5*np.sin(2*np.pi*0.11*tt + r.random()*6)
    x = filt(x, 'lowpass', bright) * (0.85 + 0.15*lfo)
    x = filt(x, 'highpass', 70)
    return x / (len(freqs)*3)
CH = [  # (start, end, midi notes) key of D
    (3.25, 9.6,  [38, 50, 57, 62, 66, 73]),        # Dmaj9-ish  D A D F# C#
    (9.3, 17.6,  [35, 47, 54, 62, 66, 69, 73]),    # Bm9
    (17.3, 24.6, [31, 43, 50, 59, 66, 69]),        # Gmaj7(9)
    (24.3, 29.0, [28, 40, 47, 55, 62, 66]),        # Em9
    (28.7, 34.15,[33, 45, 52, 57, 62, 64]),        # Asus
    (35.4, 40.6, [26, 38, 45, 50, 54, 57, 64, 69]),# D add9 resolve
]
for k, (a, b, notes) in enumerate(CH):
    n = idx(b - a)
    fr = [note(m) for m in notes]
    bright = 1400 if k < 5 else 2600
    v = pad_voice(fr, n, bright, seed=k)
    fi = 1.6 if k in (0, 5) else 1.0
    fo = 0.9 if k != 4 else 0.12
    e = np.clip(t_(n)/fi, 0, 1)**1.5 * np.clip((b - a - t_(n))/fo, 0, 1)
    g = 0.13 if k < 5 else 0.20
    vl = v * e * g
    vr = pad_voice(fr, n, bright, seed=k+50) * e * g   # decorrelated right
    add(vl, a, 1.0, 0, rev=0.5, sigR=vr)

# ---------------- S1 cold open ----------------
for tc in (0.12, 0.52):
    add(tick(0.02, 3000), tc, 0.18, 0.0, rev=0.3)
add(whoosh(0.9, 200, 2400, 0.5) * 0.5, 0.55, 0.35, 0, rev=0.6)     # 永 breathes in
add(pluck(50, 2.5, 1200) * 0.6, 0.8, 0.25, 0, rev=0.7)                 # low D note
for i, tb in enumerate((1.36, 1.9, 2.42, 2.8)):                       # heartbeat lub-dub, growing
    g = 0.10 + 0.07*i
    add(thump(48 + 2*i, 0.55, 0.3 + 0.15*i), tb - 0.02, g, 0, rev=0.15)
    add(thump(44 + 2*i, 0.45, 0.2), tb + 0.13, g*0.6, 0, rev=0.15)
r1 = riser(1.85, 150, 6000) ; add(r1, 1.15, 0.2, 0, rev=0.4)
# reverse-swell suck right before flash
n = idx(0.45); sw = filt(noise(n), 'highpass', 900) * np.linspace(0, 1, n)**3
add(sw, 2.56, 0.35, 0, rev=0.2)
# IMPACT at 3.00
add(boom(5.0, 1.0), 3.0, 1.25, 0, rev=0.55)
sh = shimmer(3.8, 2600, 1); add(sh, 3.0, 0.35, -0.3, rev=0.8, sigR=shimmer(3.8, 2700, 2))
# debris scatter: many small crackles panned
for k in range(40):
    tk = 3.02 + rng.random()**1.6 * 1.2
    add(tick(0.012, 2500 + rng.random()*5000) * (1 - (tk-3)/1.4), tk, 0.10, rng.uniform(-0.9, 0.9), rev=0.4)
# title punch tonal accent
add(bell(74, 3.0), 3.08, 0.18, 0, rev=0.8)

# ---------------- S2 harmony ----------------
add(whoosh(1.1, 250, 3800, 0.55), 4.62, 0.35, -0.7, rev=0.3)   # Hello from left
add(whoosh(1.1, 280, 3600, 0.55), 4.64, 0.35, 0.7, rev=0.3)    # 你好 from right
add(thump(70, 0.3, 0.6), 5.72, 0.2, 0, rev=0.3)               # lock-in
add(pluck(74, 1.4, 5000), 5.74, 0.22, 0, rev=0.5)
for i, tl in enumerate((5.2, 5.36, 5.52)):                      # guide lines drawing (zips)
    add(whoosh(0.5, 1500, 7000, 0.35, 0.5) * 0.5, tl, 0.22, -0.4 + 0.4*i, rev=0.3)
    add(blip(2400 + 300*i, 0.06), tl + 0.55, 0.08, -0.4 + 0.4*i, rev=0.5)
add(shimmer(1.4, 3500, 3), 5.9, 0.16, 0, rev=0.7)               # glint along baseline
# weight change sweep 6.8–8.8 (wght 600→200→860→600) — filtered saw chord
def weight_sweep(t0, dur, wf, base=[62, 69, 74]):
    n = idx(dur); tt = t_(n); x = np.zeros(n)
    for m in base:
        f = note(m)
        for h in range(1, 20):
            if f*h > 14000: break
            x += np.sin(2*np.pi*f*h*tt) / h
    y = tvfilter(x, 'lowpass', lambda t: 250 + (wf(t0 + t) - 100)/800 * 5200)
    e = np.clip(tt/0.4, 0, 1) * np.clip((dur - tt)/0.6, 0, 1)
    return y * e / len(base)
def kf(t, keys):
    if t <= keys[0][0]: return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            p = (t - keys[i-1][0]) / (keys[i][0] - keys[i-1][0]); p = 4*p**3 if p < .5 else 1 - (-2*p+2)**3/2
            return keys[i-1][1] + (keys[i][1] - keys[i-1][1]) * p
    return keys[-1][1]
w2 = lambda t: kf(t - 4.6, [[0, 600], [2.2, 600], [2.9, 200], [3.6, 860], [4.2, 600]])
add(weight_sweep(6.6, 2.4, w2), 6.6, 0.16, 0, rev=0.4)
add(whoosh(0.7, 3000, 300, 0.3), 8.95, 0.22, 0, rev=0.4)       # exit

# ---------------- S3 world ----------------
greet_d = [.15 + i*.12 for i in range(15)]
for i, d in enumerate(greet_d):
    add(whoosh(1.5, 180 + 40*(i % 4), 2600 + 200*(i % 5), 0.62), 9.4 + d, 0.17, float(np.sin(i*2.4)) * 0.8, rev=0.35)
add(riser(1.6, 100, 1500, tone=False) * 0.6, 10.0, 0.25, 0, rev=0.6)  # nucleus forms
add(bell(66, 3.0), 11.2, 0.15, 0, rev=0.8)
# arrival chimes, pentatonic
penta = [62, 64, 66, 69, 71, 74, 76, 78, 81]
for i, d in enumerate(greet_d[::2]):
    add(pluck(penta[i % len(penta)] + 12, 0.9, 7000), 9.4 + d + 1.0, 0.07, float(np.sin(i*1.7))*0.6, rev=0.6)
# counters 12.4–14.4: ticks whose rate follows d(eo3)/dt
t = 12.4
while t < 14.4:
    p = (t - 12.4) / 2.0
    rate = 3 * (1 - p)**2 / 2.0 * 26 + 2   # ticks/s
    add(tick(0.014, 4800), t, 0.13, float(rng.uniform(-0.5, 0.5)), rev=0.2)
    t += 1 / rate
add(bell(78, 2.5), 14.4, 0.2, 0, rev=0.7); add(pluck(66, 1.5), 14.42, 0.15, 0, rev=0.5)
add(riser(0.85, 200, 9000, tone=False), 16.6, 0.35, 0, rev=0.3)   # zoom out exit
add(thump(60, 0.35, 0.4), 17.42, 0.18, 0, rev=0.4)

# ---------------- S4 variable ----------------
def w4(t):
    lt = max(0, t - 17.4 - 0.2); return 500 - 400*np.cos(2*np.pi*0.38*lt)
def d4(t):
    lt = max(0, t - 17.4 - 0.2); return 100 + 20*np.sin(2*np.pi*0.57*lt)
n = idx(3.9); tt = t_(n); x = np.zeros(n); xr = np.zeros(n)
DET = 1 + 0.004*(100 + 20*np.sin(2*np.pi*0.57*np.maximum(0, tt-0.2)) - 100)/20 + 0.002
for m in (43, 50, 55, 59, 62):
    f = note(m)
    for h in range(1, 24):
        if f*h > 15000: break
        x += np.sin(2*np.pi*f*h*tt) / h
        # wdth -> detune spread on right channel
        xr += np.sin(2*np.pi*f*h*np.cumsum(DET)/SR) / h
fc4 = lambda t: 180 + (w4(17.4 + t) - 100)/800 * 6500
yl = tvfilter(x, 'lowpass', fc4); yr = tvfilter(xr, 'lowpass', fc4)
e = np.clip(tt/0.5, 0, 1) * np.clip((3.9 - tt)/0.6, 0, 1)
add(filt(yl*e/5,'highpass',90), 17.4, 0.2, 0, rev=0.45, sigR=filt(yr*e/5,'highpass',90))
# subtle sub pulse following weight peaks
for k in range(3):
    tp = 17.6 + (k + 0.5)/0.38
    if tp < 21: add(thump(46, 0.6, 0.1), tp, 0.12, 0, rev=0.2)
# waterfall plucks ascending
for i in range(9):
    add(pluck([50, 54, 57, 59, 62, 66, 69, 71, 74][i] + 12, 1.1, 3000 + 600*i), 17.4 + 3.55 + i*0.085 + 0.05, 0.13, -0.6 + i*0.15, rev=0.6)
add(whoosh(1.4, 800, 9000, 0.5, 0.6), 22.35, 0.18, 0, rev=0.5)   # light sweep
add(shimmer(1.6, 4000, 5), 22.6, 0.10, 0, rev=0.7)

# ---------------- S5 vertical / ink ----------------
TXT5 = '「竖排」时，《书名》与标点各就各位。真的吗？是的！'
PUN = '「」《》，。：？！、（）'
for i in range(len(TXT5)):                       # ink reveal (sweep of soft brush)
    if i % 2 == 0: add(brush(0.3, 3200, i), 24.4 + 0.05 + i*0.022, 0.06, -0.8 + i*0.065, rev=0.4)
for i, c in enumerate(TXT5):                     # each char travels: brush stroke
    st = 24.4 + 0.85 + i*0.034
    add(brush(0.55, 1800 + (i % 5)*250, 100 + i), st + 0.2, 0.07, 0.6 - i*0.04, rev=0.45)
    if c in PUN:
        add(pluck(81 + (i % 3)*2, 0.8, 9000), st + 1.0, 0.07, 0.0, rev=0.7)
add(bell(69, 3.0), 27.3, 0.12, 0, rev=0.8)
add(whoosh(0.6, 2500, 400, 0.25), 28.4, 0.15, 0, rev=0.4)

# ---------------- S6 nerd montage ----------------
base6 = 28.8
for i in range(4):
    add(blip(1200 + 260*i, 0.05, 1600 + 260*i), base6 + i*0.32, 0.20, -0.5 + i*0.33, rev=0.2)
    add(tick(0.01, 6000), base6 + i*0.32 + 0.03, 0.12, -0.5 + i*0.33, rev=0.1)
# kerning slide 29.35–30.15 : two tight slides + clicks
add(whoosh(0.6, 2000, 5000, 0.7, 0.6) * 0.6, base6 + 0.55, 0.12, -0.5, rev=0.2)
add(blip(2600, 0.04), base6 + 1.35, 0.16, -0.6, rev=0.2); add(blip(2900, 0.04), base6 + 1.40, 0.14, -0.4, rev=0.2)
# kern counter ticks
for k in range(10): add(tick(0.008, 7000), base6 + 0.6 + k*0.075, 0.05, -0.5, rev=0.1)
# arabic join 29.7–30.5
add(blip(900, 0.12, 1400), base6 + 1.55, 0.16, 0.5, rev=0.3)
for mi in range(5): add(blip(2200 - mi*150, 0.06, 1400 - mi*120), base6 + 1.4 + mi*0.13 + 0.25, 0.12, 0.6, rev=0.4)
# devanagari conjunct flash 30.92
add(blip(700, 0.15, 1100), base6 + 1.8, 0.12, -0.4, rev=0.3)
add(pluck(74, 1.0, 8000), base6 + 2.1, 0.14, -0.4, rev=0.5); add(pluck(81, 1.0, 8000), base6 + 2.12, 0.1, -0.4, rev=0.5)
# thai marks + tibetan stack
for mi in range(4): add(blip(1900 + mi*180, 0.05), base6 + 1.95 + mi*0.16 + 0.25, 0.11, 0.5, rev=0.4)
add(whoosh(0.9, 400, 3000, 0.8, 0.5) * 0.7, base6 + 2.1, 0.12, 0.6, rev=0.3)
# subtle tech pulse bed through montage (16th ticks)
for k in range(int(4.6 / 0.125)):
    add(tick(0.006, 9000), base6 + 0.2 + k*0.125, 0.03 + (0.02 if k % 4 == 0 else 0), 0.3*np.sin(k), rev=0.05)

# ---------------- S7 finale ----------------
T7 = 34.0; BANG = T7 + 1.12
# implosion: reverse swell (reversed noise burst through long reverb) + rising suck
n = idx(1.12); tt = t_(n); p = tt/1.12
rev_sw = tvfilter(noise(n), 'lowpass', lambda s: 300 + 9000*(s/1.12)**2) * p**3.2
add(rev_sw, T7, 0.55, 0, rev=0.5)
ff = 40 + 260*p**3
add(np.sin(2*np.pi*np.cumsum(ff)/SR) * p**2.5 * 0.7, T7, 0.35, 0, rev=0.3)
# reversed boom tail (classic suck-in)
bt = boom(1.1, 0.6)[::-1]; add(bt * np.linspace(0, 1, len(bt))**2, BANG - 1.1, 0.35, 0, rev=0.3)
# BIG BANG
add(boom(5.5, 1.4), BANG, 1.15, 0, rev=0.6)
add(thump(36, 1.2, 0.8), BANG, 0.6, 0, rev=0.2)
add(shimmer(4.5, 2200, 7), BANG, 0.42, 0, rev=0.9, sigR=shimmer(4.5, 2300, 8))
for k in range(70):
    tk = BANG + 0.02 + rng.random()**1.8 * 1.8
    add(tick(0.012, 2000 + rng.random()*7000) * max(0, 1 - (tk - BANG)/2.0), tk, 0.09, rng.uniform(-1, 1), rev=0.5)
# logo resolve: bells and the D add9 chord (pad above) + low D
add(pluck(38, 4.0, 900), 35.45, 0.45, 0, rev=0.5)
for i, m in enumerate((62, 66, 69, 74, 76)):
    add(bell(m + 12, 4.0), 35.5 + i*0.06, 0.09, -0.4 + i*0.2, rev=0.9)
add(bell(81, 3.0), 36.6, 0.10, 0.2, rev=0.9)           # tagline
add(tick(0.015, 3500), 37.3, 0.10, 0, rev=0.4)          # version text

# ---------------- reverb ----------------
def make_ir(dur=2.8, seed=9):
    r = np.random.default_rng(seed); n = idx(dur); tt = t_(n)
    ir = r.standard_normal(n) * np.exp(-tt/0.55)
    ir = filt(ir, 'lowpass', 7000) ; ir[:idx(0.012)] *= np.linspace(0, 1, idx(0.012))
    return ir / np.sqrt(np.sum(ir**2))
wetL = ss.fftconvolve(RL, make_ir(seed=9))[:N]; wetR = ss.fftconvolve(RR, make_ir(seed=10))[:N]
mixL = L + wetL*0.9; mixR = R + wetR*0.9
mix = np.stack([mixL, mixR], 1)
mix = ss.sosfilt(sos('highpass', 24), mix, axis=0)   # DC/rumble cleanup

# final fade 40.0 -> 40.6 (matches the visual fade to black)
tt = t_(N); fade = np.clip((DUR - 0.02 - tt)/0.58, 0, 1)**1.6
mix *= fade[:, None]

# ---------------- mastering ----------------
meter = pyln.Meter(SR)
def true_peak(x):
    up = ss.resample_poly(x, 4, 1, axis=0); return 20*np.log10(np.max(np.abs(up)) + 1e-12)
def limiter(x, ceil_db=-1.6, look=0.004, rel=0.08):
    ceil = 10**(ceil_db/20); up = np.max(np.abs(ss.resample_poly(x, 4, 1, axis=0)), 1); a = up[:len(x)*4].reshape(-1, 4).max(1)
    g = np.minimum(1, ceil / np.maximum(a, 1e-9))
    w = idx(look)
    gmin = -ss.minimum_filter1d if False else None
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    g = minimum_filter1d(g, size=2*w+1)
    # release smoothing (one-pole, attack instant)
    out = np.empty_like(g); c = np.exp(-1/(rel*SR)); y = 1.0
    for i in range(len(g)):  # python loop ~2M — acceptable (~1-2 s)
        gi = g[i]; y = gi if gi < y else c*y + (1-c)*gi; out[i] = y
    out = uniform_filter1d(out, size=w)  # smooth attack
    return x * out[:, None]
target = -14.0
for it in range(7):
    lu = meter.integrated_loudness(mix)
    mix = mix * 10**((target - lu)/20)
    mix = limiter(mix, -2.4)
    tp = true_peak(mix); lu2 = meter.integrated_loudness(mix)
    print(f"iter{it}: LUFS {lu2:.2f}  TP {tp:.2f} dBTP")
    if abs(lu2 - target) < 0.12 and tp <= -2.0: break
if true_peak(mix) > -2.2: mix *= 10**((-2.3 - true_peak(mix))/20)
print("final LUFS", round(meter.integrated_loudness(mix), 2), "TP", round(true_peak(mix), 2))
wav.write("soundtrack.wav", SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
np.save("mix_tmp.npy", mix.astype(np.float32))
