#!/usr/bin/env python3
"""Trilha e efeitos do quiz, tudo sintetizado. Nada de banco de sons.

Uma trilha = bateria + baixo + acordes + arpejo, montada a partir de um KIT
(timbres) e de uma PROGRESSAO (harmonia), ambos sorteados pelo SEED. Com
6 kits x 6 progressoes x 5 andamentos x transposicao livre, dois videos nunca
saem com a mesma trilha.
"""
import math, numpy as np, scipy.signal as sg

SR = 48000


def g(db): return 10.0 ** (db / 20.0)
def hz(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)


def env(n, a, d, s=0.0, r=0.0, sus=0.0):
    """ADSR em amostras."""
    t = np.arange(n) / SR
    e = np.clip(t / max(a, 1e-5), 0, 1)
    dec = np.exp(-np.maximum(t - a, 0) / max(d, 1e-5))
    e = e * (s + (1 - s) * dec) if s else e * dec
    if r:
        k = int(r * SR)
        if k and k < n: e[-k:] *= np.linspace(1, 0, k)
    return e.astype(np.float32)


def sat(x, k=2.2): return np.tanh(x * k) / math.tanh(k)


def lp(x, f, q=0.7): return sg.sosfilt(sg.butter(2, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x)
def hp(x, f): return sg.sosfilt(sg.butter(2, max(f, 20), 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return sg.sosfilt(sg.butter(2, [lo, min(hi, SR / 2 - 100)], 'band', fs=SR, output='sos'), x)


def lp_var(x, fcurve, blocks=20):
    """Low-pass whose cutoff moves over time (filter sweep), block-wise with crossfade."""
    n = len(x); out = np.zeros(n, np.float32); bs = max(1, n // blocks)
    prev = None
    for i in range(0, n, bs):
        j = min(n, i + bs)
        f = float(np.mean(fcurve[i:j])) if hasattr(fcurve, '__len__') else float(fcurve)
        y = lp(x, f)[i:j]
        if prev is not None:
            k = min(len(y), max(1, bs // 8)); r = np.linspace(0, 1, k)
            y[:k] = prev[-k:] * (1 - r) + y[:k] * r if len(prev) >= k else y[:k]
        out[i:j] = y; prev = y
    return out


# ------------------------------------------------------------------ percussão
def kick(rng, punch=1.0):
    n = int(.42 * SR); t = np.arange(n) / SR
    f = 52 + 115 * np.exp(-t / .028) * punch
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .20)
    s += .5 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * env(n, .001, .035)
    click = bp(rng.standard_normal(n), 1200, 5000) * env(n, .0005, .006)
    return (sat(s * 1.25 + .3 * click, 1.6) * .95).astype(np.float32)


def snare(rng, bright=1.0):
    n = int(.34 * SR); t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 182 * t) + .7 * np.sin(2 * np.pi * 331 * t)) * env(n, .001, .055)
    nz = bp(rng.standard_normal(n), 1400 * bright, 9500) * env(n, .001, .115)
    return (sat(.55 * tone + .85 * nz / (np.abs(nz).max() + 1e-9), 1.4) * .75).astype(np.float32)


def clap(rng):
    n = int(.4 * SR); out = np.zeros(n, np.float32)
    for i, d in enumerate([0, .011, .022, .034]):
        k = int(d * SR); m = n - k
        nz = bp(rng.standard_normal(m), 1100, 7200) * env(m, .0008, .035 if i < 3 else .16)
        out[k:] += (nz / (np.abs(nz).max() + 1e-9) * (.85 if i < 3 else 1.0)).astype(np.float32)
    return (out * .62).astype(np.float32)


def hat(rng, open_=False):
    n = int((.30 if open_ else .085) * SR)
    nz = hp(rng.standard_normal(n), 7200)
    return (nz / (np.abs(nz).max() + 1e-9) * env(n, .0004, .085 if open_ else .022) * .34).astype(np.float32)


def shaker(rng):
    n = int(.11 * SR)
    nz = bp(rng.standard_normal(n), 5200, 12000)
    return (nz / (np.abs(nz).max() + 1e-9) * env(n, .006, .035) * .26).astype(np.float32)


def tom(rng, m):
    n = int(.36 * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + .5 * np.exp(-t / .05))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .14)
    return (sat(s, 1.3) * .70).astype(np.float32)


# ------------------------------------------------------------------ timbres melódicos
def pluck(m, dur, rng, bright=2600, detune=6):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m); s = np.zeros(n, np.float32)
    for c in (-1, 1):
        d = 2 ** (c * detune / 1200)
        for h in range(1, 9):
            s += (h ** -1.35 * np.sin(2 * np.pi * f * h * d * t + rng.uniform(0, 6.3))).astype(np.float32)
    e = env(n, .004, dur * .38)
    s = lp(s * e, bright * (0.35 + 0.65 * np.exp(-2.5)))
    return (.22 * s / (np.abs(s).max() + 1e-9)).astype(np.float32)


def bass(m, dur, rng, kind='sub'):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m - 12)
    if kind == 'sub':
        s = np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * 2 * f * t)
    else:
        s = sg.sawtooth(2 * np.pi * f * t) * .6 + sg.square(2 * np.pi * f * t, .42) * .3
        s = lp_var(s, 240 + 900 * np.exp(-t / .18))
    s = s * env(n, .006, dur * .5, s=.55, r=.04)
    return (sat(.40 * s / (np.abs(s).max() + 1e-9), 1.8)).astype(np.float32)


def stab(ch, dur, rng, kind='saw'):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n, np.float32)
    for m in ch:
        f = hz(m)
        for c in (-1, 1):
            d = 2 ** (c * rng.uniform(4, 11) / 1200)
            w = sg.sawtooth(2 * np.pi * f * d * t) if kind == 'saw' else sg.square(2 * np.pi * f * d * t, .35)
            s += (w * .5).astype(np.float32)
    s = lp_var(s * env(n, .006, dur * .33, r=.03), 1500 + 2600 * np.exp(-t / .12))
    return (.17 * s / (np.abs(s).max() + 1e-9)).astype(np.float32)


def bell(m, dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m); s = np.zeros(n, np.float32)
    for r_, a, d in [(1, 1, dur * .55), (2.01, .5, dur * .3), (3.02, .3, dur * .2), (4.9, .16, dur * .12)]:
        s += (a * np.sin(2 * np.pi * f * r_ * t) * np.exp(-t / d)).astype(np.float32)
    s *= np.clip(t / .003, 0, 1)
    return (.26 * s / (np.abs(s).max() + 1e-9)).astype(np.float32)


# ------------------------------------------------------------------ kits e harmonia
KITS = [
    dict(name='pop',     bpm=112, bass='sub',  lead='pluck', drums='four',  hats='eighth'),
    dict(name='funk',    bpm=104, bass='saw',  lead='stab',  drums='break', hats='sixteenth'),
    dict(name='arcade',  bpm=126, bass='saw',  lead='bell',  drums='four',  hats='eighth'),
    dict(name='lofi',    bpm=88,  bass='sub',  lead='pluck', drums='lazy',  hats='shaker'),
    dict(name='marcha',  bpm=118, bass='sub',  lead='stab',  drums='stomp', hats='none'),
    dict(name='tropical',bpm=108, bass='sub',  lead='bell',  drums='latin', hats='shaker'),
]

PROGS = [
    [(0, 'min'), (5, 'maj'), (3, 'maj'), (7, 'maj')],
    [(0, 'min'), (7, 'min'), (5, 'maj'), (3, 'maj')],
    [(0, 'maj'), (9, 'min'), (5, 'maj'), (7, 'maj')],
    [(0, 'min'), (3, 'maj'), (7, 'min'), (5, 'maj')],
    [(0, 'maj'), (5, 'maj'), (7, 'maj'), (5, 'maj')],
    [(0, 'min'), (10, 'maj'), (8, 'maj'), (7, 'maj')],
]
TRI = dict(maj=[0, 4, 7, 11], min=[0, 3, 7, 10])


def pick_kit(seed):
    rng = np.random.default_rng(seed * 7919 + 13)
    k = dict(KITS[rng.integers(len(KITS))])
    k['prog'] = PROGS[rng.integers(len(PROGS))]
    k['root'] = int(rng.integers(53, 62))          # F3..Bb3
    k['bpm'] = k['bpm'] + int(rng.integers(-5, 6))
    k['swing'] = float(rng.uniform(0, .055))
    return k


# ------------------------------------------------------------------ montagem
def put(buf, s, t0, gain=1.0, pan=0.0):
    a = (pan + 1) * np.pi / 4
    i = int(t0 * SR); j = min(i + len(s), len(buf))
    if j <= i or i < 0: return
    seg = s[:j - i] * gain
    buf[i:j, 0] += np.cos(a) * seg; buf[i:j, 1] += np.sin(a) * seg


def groove(total, kit, seed, energy_at):
    """Trilha completa. energy_at(t) -> 0..1 controla densidade e brilho."""
    rng = np.random.default_rng(seed * 104729 + 7)
    out = np.zeros((int(total * SR) + SR, 2), np.float32)
    spb = 60.0 / kit['bpm']; bar = 4 * spb
    K, S, C = kick(rng), snare(rng), clap(rng)
    H, HO, SH = hat(rng), hat(rng, True), shaker(rng)
    TOMS = [tom(rng, m) for m in (50, 47, 43)]
    nbars = int(total / bar) + 2
    prog = kit['prog']; root = kit['root']

    for b in range(nbars):
        t0 = b * bar
        if t0 > total: break
        e = energy_at(t0)
        ch_root, qual = prog[b % len(prog)]
        ch = [root + ch_root + i for i in TRI[qual]]
        fill = (b % 8 == 7) and e > .35

        # --- bateria
        for beat in range(4):
            tb = t0 + beat * spb
            if kit['drums'] == 'four':
                put(out, K, tb, g(-7))
                if beat in (1, 3): put(out, S if e > .5 else C, tb, g(-10))
            elif kit['drums'] == 'break':
                if beat in (0, 2): put(out, K, tb, g(-7))
                if beat == 2: put(out, K, tb + spb * .75, g(-11))
                if beat in (1, 3): put(out, S, tb, g(-9.5))
            elif kit['drums'] == 'lazy':
                if beat in (0, 2): put(out, K, tb, g(-8.5))
                if beat == 2: put(out, C, tb, g(-13))
            elif kit['drums'] == 'stomp':
                put(out, K, tb, g(-6.5))
                if beat in (1, 3): put(out, C, tb, g(-9))
            else:  # latin
                if beat in (0, 2): put(out, K, tb, g(-8))
                put(out, S if beat == 3 else C, tb + spb * .5, g(-14))
            # --- chimbau
            if kit['hats'] == 'eighth':
                for k in (0, .5):
                    put(out, HO if (beat == 3 and k == .5 and e > .5) else H,
                        tb + k * spb + (kit['swing'] * spb if k else 0), g(-15 + 3 * e), .12)
            elif kit['hats'] == 'sixteenth' and e > .3:
                for k in (0, .25, .5, .75):
                    put(out, H, tb + k * spb, g(-18 + 4 * e), .15 if k % .5 else -.1)
            elif kit['hats'] == 'shaker':
                for k in (0, .5):
                    put(out, SH, tb + k * spb, g(-14 + 3 * e), -.14)
        if fill:
            for i, tt in enumerate([.0, .25, .5, .75]):
                put(out, TOMS[min(i, 2)], t0 + 3 * spb + tt * spb, g(-9), -.3 + .2 * i)

        # --- baixo
        patt = [(0, 1.0), (1.5, .5), (2, 1.0), (3.5, .5)] if e > .4 else [(0, 2.0), (2, 2.0)]
        for off, ln in patt:
            m = ch[0] if off < 2 else ch[0] + (0 if qual == 'min' else 0)
            put(out, bass(m, ln * spb, rng, kit['bass']), t0 + off * spb, g(-9 - 2 * (1 - e)))

        # --- acordes e arpejo
        if kit['lead'] == 'stab':
            for off in ([0, 2, 3.5] if e > .45 else [0, 2]):
                put(out, stab(ch[:3], spb * .75, rng), t0 + off * spb, g(-17 - 5 * (1 - e)), .08)
        else:
            steps = [0, .5, 1, 1.5, 2, 2.5, 3, 3.5] if e > .45 else [0, 1, 2, 3]
            voic = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24]
            for i, off in enumerate(steps):
                m = voic[i % len(voic)]
                f = pluck if kit['lead'] == 'pluck' else bell
                put(out, f(m, spb * .9, rng), t0 + off * spb, g(-19 - 6 * (1 - e)),
                    -.22 + .44 * ((i % 4) / 3))
    return out


# ------------------------------------------------------------------ efeitos de cena
def whoosh(rng, dur=.7, up=True):
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    w = rng.standard_normal(n); y = np.zeros(n)
    for lo, hi, wt in [(220, 800, .5), (800, 3200, 1.0), (3200, 9000, .6)]:
        y += wt * bp(w, lo, hi)
    sweep = (u if up else 1 - u)
    y *= np.sin(np.pi * u) ** 1.6 * (.25 + .75 * sweep)
    return (.42 * y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def riser(rng, dur, key):
    """Sobe de tensão até a revelação: ruído filtrado + nota subindo + tremolo."""
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    nz = rng.standard_normal(n)
    y = np.zeros(n)
    for i in range(6):
        c = 400 * 2 ** (2.6 * u + i * .1)
        y += bp(nz, 300, 9000) * .2
    f = hz(key + 12) * 2 ** (1.2 * u ** 1.7)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (.35 + .25 * np.sin(2 * np.pi * (3 + 14 * u) * t))
    y = y / (np.abs(y).max() + 1e-9) * (u ** 2.2) + tone * (u ** 1.5) * .55
    y *= np.minimum(1, (1 - u) * 14 + .35)
    return (.34 * y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def tick(rng, i, n_total):
    """Tique do cronômetro, sobe de tom conforme o tempo acaba."""
    k = i / max(1, n_total - 1)
    d = int(.075 * SR); t = np.arange(d) / SR
    f = 980 + 620 * k
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / .011) + .45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .005)
    nz = bp(rng.standard_normal(d), 2600, 9500)
    s = s + .3 * nz / (np.abs(nz).max() + 1e-9) * np.exp(-t / .004)
    s[:20] *= np.linspace(0, 1, 20)
    return (.52 * (.75 + .45 * k) * s).astype(np.float32)


def pop(rng, i):
    n = int(.26 * SR); t = np.arange(n) / SR
    f = (480 + 72 * i) * (1 + 1.05 * np.exp(-t / .022))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .003, .05)
    s += .38 * np.sin(2 * np.pi * np.cumsum(2.02 * f) / SR) * env(n, .002, .024)
    s += .2 * bp(rng.standard_normal(n), 2000, 7000) * env(n, .001, .012)
    return (.50 * s / (np.abs(s).max() + 1e-9)).astype(np.float32)


def correct(rng, key):
    """Acerto: impacto + arpejo ascendente + brilho."""
    n = int(2.9 * SR); out = np.zeros(n, np.float32)
    imp = np.sin(2 * np.pi * np.cumsum(np.full(int(.3 * SR), 70.0)) / SR) * env(int(.3 * SR), .001, .09)
    out[:len(imp)] += (sat(imp * 1.3, 1.5) * .55).astype(np.float32)
    for i, m in enumerate([key + 12, key + 16, key + 19, key + 24]):
        s = bell(m, 2.2, rng) * (1.0 - .14 * i)
        k = int(i * .075 * SR); out[k:k + len(s)] += s[:n - k] * 1.25
    spark = hp(rng.standard_normal(int(.9 * SR)), 6500)
    spark = spark / (np.abs(spark).max() + 1e-9) * env(len(spark), .01, .22)
    out[:len(spark)] += (spark * .20).astype(np.float32)
    return (out / (np.abs(out).max() + 1e-9) * .78).astype(np.float32)


def page(rng, key):
    n = int(.9 * SR); t = np.arange(n) / SR; s = np.zeros(n, np.float32)
    for m, a in [(key, 1.0), (key + 7, .45), (key + 12, .3)]:
        s += (a * np.sin(2 * np.pi * hz(m) * t) * np.exp(-t / .28)).astype(np.float32)
    s *= np.clip(t / .005, 0, 1)
    sw = bp(rng.standard_normal(int(.3 * SR)), 1800, 7000)
    s[:len(sw)] += (sw / (np.abs(sw).max() + 1e-9) * env(len(sw), .002, .05) * .3).astype(np.float32)
    return (.30 * s / (np.abs(s).max() + 1e-9)).astype(np.float32)


def fanfare(rng, key, kit):
    """Encerramento: acorde grande, subida e prato."""
    n = int(4.2 * SR); out = np.zeros(n, np.float32)
    for i, m in enumerate([key, key + 4, key + 7, key + 12, key + 16]):
        s = bell(m, 3.4, rng) * (1 - .1 * i)
        k = int(i * .105 * SR); out[k:k + len(s)] += s[:n - k]
    out[:int(2.4 * SR)] += stab([key + 12, key + 16, key + 19], 2.4, rng)[:int(2.4 * SR)] * 1.4
    cr = hp(rng.standard_normal(int(2.6 * SR)), 4200)
    cr = cr / (np.abs(cr).max() + 1e-9) * env(len(cr), .004, .85)
    out[:len(cr)] += (cr * .30).astype(np.float32)
    return (out / (np.abs(out).max() + 1e-9) * .82).astype(np.float32)


def duck(mix, times, depth=.45, pre=.09, hold=.26, rel=.34):
    """Abaixa a trilha onde há narração, para a voz ficar na frente."""
    gmask = np.ones(len(mix), np.float32)
    for t0, dur in times:
        a = max(0, int((t0 - pre) * SR)); b = min(len(mix), int((t0 + dur + hold) * SR))
        r = min(len(mix) - b, int(rel * SR))
        if b <= a: continue
        gmask[a:b] = np.minimum(gmask[a:b], 1 - depth)
        if r > 0: gmask[b:b + r] = np.minimum(gmask[b:b + r], np.linspace(1 - depth, 1, r))
        f = min(int(pre * SR), b - a)
        if f > 0: gmask[a:a + f] = np.minimum(gmask[a:a + f], np.linspace(1, 1 - depth, f))
    return mix * gmask[:, None]


# ------------------------------------------------------------------ masterização
def lufs(x):
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    blk, hop = int(.4 * SR), int(.1 * SR); z = 0
    for ch in range(2):
        y = sg.lfilter(b2, a2, sg.lfilter(b1, a1, np.asarray(x[:, ch], np.float64)))
        c = np.concatenate([[0], np.cumsum(y ** 2)]); st = np.arange(0, max(1, len(y) - blk), hop)
        z = z + (c[st + blk] - c[st]) / blk
    l = -.691 + 10 * np.log10(z + 1e-20); z = z[l > -70]
    if not len(z): return -70.0
    rel = -.691 + 10 * np.log10(z.mean()) - 10
    sel = z[-.691 + 10 * np.log10(z) > rel]
    return -.691 + 10 * np.log10(sel.mean() if len(sel) else z.mean())


def master(mix, target=-14.0):
    from scipy.ndimage import minimum_filter1d
    def limit(x, ceil, A=900):
        req = np.minimum(1.0, ceil / (np.abs(x).max(1) + 1e-12)).astype(np.float32)
        if req.min() >= 1.0: return
        gmin = minimum_filter1d(req, 2 * A + 1); win = np.hanning(2 * A + 3)[1:-1]; win /= win.sum()
        gp = np.concatenate([np.full(A + 1, gmin[0]), gmin, np.full(A + 1, gmin[-1])])
        gs = sg.oaconvolve(gp, win.astype(np.float32), 'same')[A + 1:-(A + 1)]
        x *= np.minimum(gs, 1.0)[:, None]
    for _ in range(2):
        mix *= g(target - lufs(mix)); limit(mix, g(-1.6))
    seg = np.asarray(mix[:min(len(mix), 60 * SR)], np.float64)
    tp = 20 * np.log10(np.abs(sg.resample_poly(seg, 4, 1, axis=0)).max() + 1e-12)
    if tp > -1.0:
        mix *= g(-1.0 - tp); tp = -1.0
    return mix, round(lufs(mix), 2), round(float(tp), 2)
