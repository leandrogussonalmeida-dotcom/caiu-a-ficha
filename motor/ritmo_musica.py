#!/usr/bin/env python3
"""NO RITMO — a música eletrônica que manda no vídeo.

A regra da série: **o visual nunca adivinha o som**. Cada bumbo, caixa,
chimbal, nota de baixo e nota de melodia nasce aqui como um EVENTO com o
instante exato em segundos; o mesmo evento vira amostra no áudio e
movimento na tela. Não existe detecção de batida, nem aproximação: se o
herói pisa no quadro 412, é porque o bumbo foi posto na amostra 657.920.

Uma faixa é uma lista de SEÇÕES. Cada seção tem gênero, andamento, número
de compassos e papel (intro, build, drop, break). O andamento pode mudar de
seção para seção — é o que faz o "do lo-fi 80 ao drum and bass 174" — e a
grade de tempo é acumulada, não multiplicada, então a troca não escorrega.

Uso:
    f = compor(secoes, seed)        # -> Faixa com .audio, .eventos
    f.audio                         # estéreo float32, já masterizado a -14 LUFS
    f.eventos                       # [{'t':..., 'tipo':'kick', ...}, ...]
"""
import math
import numpy as np
import scipy.signal as sg
import quizaudio as QA

SR = 48000
g = QA.g


def hz(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)


def _env(n, a, d, s=0.0, r=0.0):
    return QA.env(n, a, d, s, r)


def _lp(x, f): return QA.lp(x, f)
def _hp(x, f): return QA.hp(x, f)
def _bp(x, lo, hi): return QA.bp(x, lo, hi)


def _norm(x, pk=1.0):
    m = np.abs(x).max()
    return (x / m * pk).astype(np.float32) if m > 0 else x.astype(np.float32)


def _saw(f, t, fase=0.0):
    """Dente de serra com fase; `f` pode ser vetor (glide)."""
    if np.ndim(f):
        ph = np.cumsum(f) / SR + fase
    else:
        ph = f * t + fase
    return 2.0 * (ph - np.floor(ph + .5))


def _sq(f, t, duty=.5):
    ph = (np.cumsum(f) / SR) if np.ndim(f) else f * t
    return np.where((ph % 1.0) < duty, 1.0, -1.0)


def _tri(f, t):
    ph = (np.cumsum(f) / SR) if np.ndim(f) else f * t
    return 4 * np.abs((ph % 1.0) - .5) - 1


def _sweep(x, curva, cortes=(160, 420, 1100, 2800, 7000)):
    """Filtro com corte que se move, sem filtro variante no tempo.

    Filtra o sinal UMA vez em cada corte fixo e cruza entre as versões pela
    curva (0 = escuro, 1 = aberto). Cinco filtros por nota em vez de um por
    bloco: é o que deixa wobble, acid e sweep de build baratos o bastante
    para trinta vídeos."""
    vs = [_lp(x, c) for c in cortes]
    k = len(vs) - 1
    pos = np.clip(curva, 0, 1) * k
    i = np.minimum(pos.astype(int), k - 1)
    fr = (pos - i).astype(np.float32)
    out = np.zeros_like(x, dtype=np.float32)
    for j in range(k):
        m = (i == j)
        if m.any():
            out[m] = vs[j][m] * (1 - fr[m]) + vs[j + 1][m] * fr[m]
    return out


# =================================================================== bateria
class Bateria:
    """Os timbres de percussão de um gênero, sintetizados uma vez e reusados.
    Cada gênero escolhe o seu sabor de bumbo, caixa e chimbal."""

    def __init__(self, rng, sabor):
        self.rng = rng
        self.s = sabor
        self.cache = {}

    def get(self, nome, **kw):
        ch = (nome, tuple(sorted(kw.items())))
        if ch not in self.cache:
            self.cache[ch] = getattr(self, '_' + nome)(**kw)
        return self.cache[ch]

    # ---- bumbos
    def _kick(self, nota=None):
        r, s = self.rng, self.s
        n = int(.55 * SR); t = np.arange(n) / SR
        if s == 'lofi':
            f = 48 + 70 * np.exp(-t / .03)
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .003, .16)
            return _norm(_lp(y, 900) * .9, .85)
        if s == 'chip':
            f = 40 + 260 * np.exp(-t / .02)
            y = _sq(f, t, .5) * _env(n, .001, .07)
            return _norm(_lp(y, 3000), .8)
        if s == 'hard':
            # bumbo de hardstyle: estalo + corpo distorcido com cauda afinada
            base = hz(nota if nota else 33)
            f = base + 260 * np.exp(-t / .016) + 40 * np.exp(-t / .09)
            y = np.sin(2 * np.pi * np.cumsum(f) / SR)
            y = np.tanh(y * 7) * _env(n, .001, .30, r=.04)
            y = _lp(y, 5200) + .4 * _bp(r.standard_normal(n), 1500, 6000) * _env(n, .0005, .008)
            return _norm(y, .95)
        if s == 'gabber':
            f = 55 + 300 * np.exp(-t / .02)
            y = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 12) * _env(n, .001, .22)
            return _norm(_lp(y, 6000), .95)
        if s == '808':
            f = 45 + 110 * np.exp(-t / .03)
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .002, .28)
            return _norm(QA.sat(y, 1.4), .95)
        punch = {'house': 1.1, 'techno': 1.0, 'dnb': 1.2, 'trance': 1.05}.get(s, 1.0)
        f = 50 + 125 * punch * np.exp(-t / .026)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .002, .19 if s != 'techno' else .26)
        y += .45 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * _env(n, .001, .03)
        y += .35 * _bp(r.standard_normal(n), 1500, 7000) * _env(n, .0005, .005)
        return _norm(QA.sat(y * 1.2, 1.7), .95)

    # ---- caixas e palmas
    def _snare(self):
        r, s = self.rng, self.s
        n = int(.45 * SR); t = np.arange(n) / SR
        if s == 'chip':
            y = r.standard_normal(n) * _env(n, .001, .09)
            y += .5 * _sq(220 * np.exp(-t / .1) + 120, t) * _env(n, .001, .04)
            return _norm(_lp(y, 7000), .7)
        if s == 'lofi':
            tone = np.sin(2 * np.pi * 190 * t) * _env(n, .001, .05)
            nz = _bp(r.standard_normal(n), 900, 5200) * _env(n, .002, .11)
            return _norm(_lp(.5 * tone + _norm(nz), 4200), .62)
        tone = (np.sin(2 * np.pi * 185 * t) + .6 * np.sin(2 * np.pi * 330 * t)) * _env(n, .001, .05)
        nz = _bp(r.standard_normal(n), 1500, 10000) * _env(n, .001, .13 if s != 'dnb' else .09)
        y = .6 * tone + _norm(nz)
        if s == 'gated':      # caixa gigante dos anos 80: cauda longa cortada seca
            tail = _bp(r.standard_normal(n), 900, 7000) * (t < .26) * .55
            y = y + tail
        return _norm(QA.sat(y, 1.4), .8)

    def _clap(self):
        return _norm(QA.clap(self.rng), .75)

    def _rim(self):
        n = int(.08 * SR); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 1700 * t) * np.exp(-t / .006) + .5 * _bp(self.rng.standard_normal(n), 3000, 9000) * np.exp(-t / .004)
        return _norm(y, .5)

    def _hat(self, aberto=False):
        r = self.rng
        n = int((.32 if aberto else .07) * SR)
        if self.s == 'chip':
            y = r.standard_normal(n) * _env(n, .0005, .05 if aberto else .012)
            return _norm(_hp(y, 6000), .45)
        # chimbal metálico: soma de quadradas inarmônicas, como as máquinas
        t = np.arange(n) / SR
        y = np.zeros(n)
        for fr in (205.3, 304.4, 369.6, 522.7, 540, 800):
            y += _sq(fr * 2.4, t, .5)
        y = _hp(y + .6 * r.standard_normal(n), 7000)
        y = y * _env(n, .0005, .09 if aberto else .018)
        if self.s == 'lofi': y = _lp(y, 7500)
        return _norm(y, .42 if not aberto else .40)

    def _shaker(self):
        return _norm(QA.shaker(self.rng), .35)

    def _cow(self, nota=None):
        """Cowbell de phonk: duas quadradas em quinta, passa-banda. Com nota,
        vira instrumento melódico, que é o som do gênero."""
        n = int(.32 * SR); t = np.arange(n) / SR
        f = hz(nota) if nota else 540
        y = _sq(f, t, .5) + .8 * _sq(f * 1.48, t, .5)
        y = _bp(y, 500, 4200) * _env(n, .001, .09)
        return _norm(y, .55)

    def _tom(self, nota=45):
        return _norm(QA.tom(self.rng, nota), .7)

    def _crash(self):
        n = int(1.8 * SR)
        y = _hp(self.rng.standard_normal(n), 5000) * _env(n, .001, .55)
        return _norm(y, .45)

    def _ride(self):
        n = int(.5 * SR); t = np.arange(n) / SR
        y = np.zeros(n)
        for fr in (3150, 4400, 5900, 7100):
            y += np.sin(2 * np.pi * fr * t)
        y = (y * .4 + _hp(self.rng.standard_normal(n), 8000)) * _env(n, .001, .16)
        return _norm(y, .3)


# =================================================================== tonais
def baixo(tipo, m, dur, bpm, rng, glide_de=None):
    n = max(1, int(dur * SR)); t = np.arange(n) / SR
    f0 = hz(m)
    if tipo == 'sub':
        y = np.sin(2 * np.pi * f0 * t) + .25 * np.sin(4 * np.pi * f0 * t)
        return _norm(y * _env(n, .005, dur * .9, s=.7, r=.03), .9)
    if tipo == 'organ':          # baixo de house: seno + oitava, curtinho
        y = np.sin(2 * np.pi * f0 * t) + .5 * np.sin(4 * np.pi * f0 * t) + .2 * np.sin(6 * np.pi * f0 * t)
        return _norm(QA.sat(y, 1.5) * _env(n, .003, min(dur, .22), r=.02), .9)
    if tipo == 'saw':
        y = _saw(f0, t) * .7 + _saw(f0 * 1.004, t, .3) * .5 + np.sin(2 * np.pi * f0 / 2 * t) * .6
        y = _sweep(y, .25 + .55 * np.exp(-t / .12), (180, 500, 1400, 3200, 6000))
        return _norm(y * _env(n, .004, dur, s=.6, r=.03), .9)
    if tipo == 'reese':
        y = _saw(f0, t) + _saw(f0 * 1.0075, t, .2) + _saw(f0 * .9932, t, .6)
        mov = .35 + .2 * np.sin(2 * np.pi * .7 * t + rng.uniform(0, 6))
        y = _sweep(y, mov, (120, 300, 700, 1500, 3000)) + .8 * np.sin(2 * np.pi * f0 / 2 * t)
        return _norm(QA.sat(y * _env(n, .01, dur, s=.85, r=.04), 1.6), .9)
    if tipo == 'wobble':
        # LFO travado no andamento: 1/8, 1/16 ou tercina, sorteado por nota
        div = rng.choice([2, 4, 3, 6])
        lfo = .5 - .5 * np.cos(2 * np.pi * (bpm / 60) * (div / 2) * t)
        y = _saw(f0, t) + _sq(f0 * 1.003, t, .45) * .7 + _saw(f0 * 2.002, t) * .3
        y = _sweep(y, .05 + .95 * lfo, (90, 260, 800, 2200, 6500))
        y = QA.sat(y + .7 * np.sin(2 * np.pi * f0 / 2 * t), 2.6)
        return _norm(y * _env(n, .004, dur, s=.95, r=.03), .95)
    if tipo == '808':
        f = np.full(n, f0)
        if glide_de is not None:
            k = min(n, int(.07 * SR))
            f[:k] = np.linspace(hz(glide_de), f0, k)
        f = f * (1 + .6 * np.exp(-t / .015))
        y = np.sin(2 * np.pi * np.cumsum(f) / SR)
        y = QA.sat(y * _env(n, .002, dur * 1.2, s=.75, r=.05), 2.4)
        return _norm(y, .95)
    if tipo == 'acid':
        # 303 de mentira: serra, corte que abre e fecha a cada nota, ressonância
        y = _saw(f0, t)
        env_f = np.exp(-t / .09) * rng.uniform(.5, 1.0)
        y = _sweep(y, .15 + .85 * env_f, (200, 500, 1200, 2600, 5200))
        res = sg.lfilter(*sg.iirpeak(min(f0 * 6, 4000), 6, fs=SR), y)
        y = QA.sat(y + .9 * res * env_f, 2.2)
        return _norm(y * _env(n, .002, dur * .8, s=.3, r=.01), .85)
    if tipo == 'tri':            # baixo de console
        y = _tri(f0, t)
        return _norm(y * _env(n, .002, dur, s=.8, r=.01), .9)
    if tipo == 'rasgado':        # 808 estourado do phonk
        f = f0 * (1 + .8 * np.exp(-t / .02))
        y = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 5)
        y = _lp(y, 2600) * _env(n, .002, dur * 1.1, s=.7, r=.04)
        return _norm(y, .95)
    raise ValueError(tipo)


def nota(tipo, m, dur, rng, bpm=120):
    """Timbres de melodia e acorde (uma nota só; acorde = soma)."""
    n = max(1, int(dur * SR)); t = np.arange(n) / SR
    f0 = hz(m)
    if tipo == 'supersaw':
        y = np.zeros(n)
        for k, d in enumerate((-22, -13, -6, 0, 6, 13, 22)):
            y += _saw(f0 * 2 ** (d / 1200), t, rng.uniform(0, 1)) * (1 if d else 1.2)
        y = _lp(y, 7500) * _env(n, .004, dur, s=.7, r=min(.08, dur * .3))
        return _norm(y, .5)
    if tipo == 'pluck':
        y = _saw(f0, t) + _saw(f0 * 1.006, t, .4)
        y = _sweep(y, np.exp(-t / .06), (300, 900, 2200, 4500, 9000))
        return _norm(y * _env(n, .002, dur * .6, r=.02), .5)
    if tipo == 'bell':
        y = np.zeros(n)
        for r_, a, d in ((1, 1, .9), (2.0, .45, .4), (3.01, .3, .25), (4.2, .18, .12)):
            y += a * np.sin(2 * np.pi * f0 * r_ * t) * np.exp(-t / (d * max(.25, dur)))
        return _norm(y * np.clip(t / .002, 0, 1), .45)
    if tipo == 'square':         # console: quadrada com vibrato que entra devagar
        vib = 1 + .006 * np.sin(2 * np.pi * 6 * t) * np.clip((t - .12) / .2, 0, 1)
        y = _sq(f0 * vib, t, .25 if m % 2 else .5)
        return _norm(_lp(y, 9000) * _env(n, .002, dur, s=.7, r=.02), .38)
    if tipo == 'arpchip':        # acorde em arpejo de 1/32 — o som do console
        y = _sq(f0, t, .125)
        return _norm(y * _env(n, .001, dur, s=.6, r=.005), .32)
    if tipo == 'rhodes':
        mod = np.sin(2 * np.pi * f0 * 1.0 * t) * 1.4 * np.exp(-t / .25)
        y = np.sin(2 * np.pi * f0 * t + mod) + .2 * np.sin(2 * np.pi * f0 * 2 * t) * np.exp(-t / .3)
        y = y * (1 + .12 * np.sin(2 * np.pi * 4.5 * t))        # tremolo
        return _norm(_lp(y * _env(n, .004, dur * 1.2, s=.25, r=.06), 3500), .45)
    if tipo == 'piano':          # stab de piano de house
        y = np.zeros(n)
        for h in range(1, 9):
            y += np.sin(2 * np.pi * f0 * h * (1 + .0004 * h * h) * t) * h ** -1.3 * np.exp(-t * (2 + h * 1.4))
        return _norm(y * np.clip(t / .002, 0, 1) * _env(n, .001, dur, s=1, r=.03), .5)
    if tipo == 'pad':
        y = np.zeros(n)
        for d in (-9, -3, 4, 10):
            y += _saw(f0 * 2 ** (d / 1200), t, rng.uniform(0, 1))
        y = _lp(y, 2600) * _env(n, min(.35, dur * .4), dur, s=.9, r=min(.3, dur * .3))
        return _norm(y, .4)
    if tipo == 'vox':
        # sílaba "ah" de sintetizador: serra em dois formantes, recortada
        y = _saw(f0, t) + _saw(f0 * 1.004, t, .5)
        y = (_bp(y, 650, 950) * 1.0 + _bp(y, 1050, 1400) * .7 + _bp(y, 2400, 2900) * .3)
        y = y * (1 + .01 * np.sin(2 * np.pi * 5.5 * t))
        return _norm(y * _env(n, .006, dur, s=.8, r=.03), .5)
    if tipo == 'saw':
        y = _saw(f0, t) + _saw(f0 * 1.008, t, .3) * .8
        y = _lp(y, 5200) * _env(n, .003, dur, s=.75, r=.03)
        return _norm(y, .45)
    if tipo == 'screech':        # lead rasgado de hardstyle
        lfo = 1 + .02 * np.sin(2 * np.pi * 7 * t)
        y = np.tanh((_saw(f0 * lfo, t) + _sq(f0 * 1.5, t, .3)) * 3)
        y = _sweep(y, .5 + .5 * np.sin(2 * np.pi * (bpm / 60) * 2 * t), (600, 1400, 2600, 4800, 9000))
        return _norm(y * _env(n, .002, dur, s=.8, r=.02), .42)
    if tipo == 'marimba':
        y = np.sin(2 * np.pi * f0 * t) * np.exp(-t / .22) + .4 * np.sin(2 * np.pi * f0 * 4 * t) * np.exp(-t / .03)
        return _norm(y * np.clip(t / .001, 0, 1), .5)
    if tipo == 'flauta':
        vib = 1 + .005 * np.sin(2 * np.pi * 5 * t)
        y = np.sin(2 * np.pi * np.cumsum(np.full(n, f0) * vib) / SR) + .08 * _lp(rng.standard_normal(n), 3000)
        return _norm(y * _env(n, .04, dur, s=.8, r=.05), .4)
    raise ValueError(tipo)


# =================================================================== efeitos
def fx(tipo, dur, rng, m=60):
    n = max(1, int(dur * SR)); t = np.arange(n) / SR; u = t / max(dur, 1e-6)
    if tipo == 'riser':
        nz = rng.standard_normal(n)
        y = _sweep(nz, u ** 1.6, (300, 900, 2400, 6000, 14000)) * (u ** 1.8)
        f = hz(m) * 2 ** (2.0 * u ** 1.5)
        y = y * .7 + np.sin(2 * np.pi * np.cumsum(f) / SR) * u ** 2 * .45
        return _norm(y, .55)
    if tipo == 'impacto':
        f = 40 + 60 * np.exp(-t / .08)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .5)
        y += .5 * _lp(rng.standard_normal(n), 1600) * np.exp(-t / .35)
        return _norm(QA.sat(y, 1.5), .9)
    if tipo == 'queda':          # downlifter
        nz = rng.standard_normal(n)
        y = _sweep(nz, (1 - u) ** 1.4, (200, 700, 2000, 5000, 11000)) * (1 - u) ** 1.2
        return _norm(y, .45)
    if tipo == 'reverso':        # prato ao contrário, puxa para o drop
        y = _hp(rng.standard_normal(n), 4000) * u ** 3
        return _norm(y, .45)
    if tipo == 'vinil':
        y = _lp(rng.standard_normal(n), 5000) * .04
        k = rng.random(n) < 12 / SR
        y[k] += rng.uniform(-.18, .18, k.sum())
        # estalo filtrado: impulso cru estourava o pico depois do AAC (+1,3 dBFS)
        return _lp(y, 4500).astype(np.float32)
    if tipo == 'parada':         # tape stop: o pitch despenca
        y = np.sin(2 * np.pi * np.cumsum(hz(m) * (1 - u) ** 2) / SR) * (1 - u)
        return _norm(y, .5)
    raise ValueError(tipo)


# =================================================================== harmonia
MENOR = [0, 2, 3, 5, 7, 8, 10]
MAIOR = [0, 2, 4, 5, 7, 9, 11]
PROGS_MENOR = [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6], [0, 5, 3, 4], [5, 3, 0, 4], [0, 2, 5, 6]]
PROGS_MAIOR = [[0, 4, 5, 3], [0, 5, 3, 4], [3, 4, 0, 5], [0, 3, 4, 4]]


def triade(escala, grau, raiz):
    """Tríade diatônica + sétima, como MIDI."""
    out = []
    for k in (0, 2, 4, 6):
        i = grau + k
        out.append(raiz + escala[i % 7] + 12 * (i // 7))
    return out


def voicing(ch, ant, centro=60):
    """Inversão que menos anda em relação ao acorde anterior."""
    base = ch[:3]
    opcoes = []
    for inv in range(3):
        v = sorted([(base[(i + inv) % 3] + (12 if i + inv >= 3 else 0)) for i in range(3)])
        while np.mean(v) > centro + 6: v = [x - 12 for x in v]
        while np.mean(v) < centro - 6: v = [x + 12 for x in v]
        opcoes.append(v)
    if not ant: return opcoes[0]
    return min(opcoes, key=lambda v: sum(abs(a - b) for a, b in zip(v, ant)))


# =================================================================== gêneros
# Cada gênero: andamento de referência, sabor de bateria, timbres, swing,
# meio tempo (a caixa no 3 em vez de no 2 e 4) e se a escala é maior.
GENEROS = {
    'lofi':      dict(nome='LO-FI', bpm=80, kit='lofi', baixo='sub', acorde='rhodes', lead='pluck', swing=.20, meio=False, maior=False),
    'synthwave': dict(nome='SYNTHWAVE', bpm=100, kit='gated', baixo='saw', acorde='pad', lead='saw', swing=0, meio=False, maior=False),
    'dembow':    dict(nome='REGGAETON', bpm=96, kit='house', baixo='sub', acorde='pad', lead='marimba', swing=0, meio=False, maior=False),
    'house':     dict(nome='HOUSE', bpm=124, kit='house', baixo='organ', acorde='piano', lead='vox', swing=.06, meio=False, maior=False),
    'funk':      dict(nome='FUNK', bpm=130, kit='808', baixo='808', acorde=None, lead='vox', swing=0, meio=False, maior=False),
    'phonk':     dict(nome='PHONK', bpm=130, kit='808', baixo='rasgado', acorde=None, lead='cow', swing=0, meio=False, maior=False),
    'garage':    dict(nome='UK GARAGE', bpm=132, kit='house', baixo='reese', acorde='piano', lead='vox', swing=.14, meio=False, maior=False),
    'techno':    dict(nome='TECHNO', bpm=132, kit='techno', baixo='acid', acorde=None, lead='pluck', swing=0, meio=False, maior=False),
    'trance':    dict(nome='TRANCE', bpm=138, kit='trance', baixo='saw', acorde='supersaw', lead='supersaw', swing=0, meio=False, maior=False),
    'dubstep':   dict(nome='DUBSTEP', bpm=140, kit='house', baixo='wobble', acorde='pad', lead='bell', swing=0, meio=True, maior=False),
    'trap':      dict(nome='TRAP', bpm=140, kit='808', baixo='808', acorde='pad', lead='bell', swing=0, meio=True, maior=False),
    'future':    dict(nome='FUTURE BASS', bpm=150, kit='house', baixo='808', acorde='supersaw', lead='vox', swing=0, meio=True, maior=True),
    'chiptune':  dict(nome='CHIPTUNE', bpm=150, kit='chip', baixo='tri', acorde='arpchip', lead='square', swing=0, meio=False, maior=True),
    'hardstyle': dict(nome='HARDSTYLE', bpm=150, kit='hard', baixo=None, acorde='supersaw', lead='screech', swing=0, meio=False, maior=False),
    'dnb':       dict(nome='DRUM AND BASS', bpm=174, kit='dnb', baixo='reese', acorde='pad', lead='pluck', swing=0, meio=False, maior=False),
    'gabber':    dict(nome='GABBER', bpm=190, kit='gabber', baixo=None, acorde='supersaw', lead='screech', swing=0, meio=False, maior=False),
}


def P(s):
    """Padrão de 16 passos em texto: 'x...x...' -> posições ligadas."""
    return [i for i, c in enumerate(s) if c in 'xX']


# =================================================================== a faixa
class Faixa:
    def __init__(self):
        self.eventos = []
        self.secoes = []
        self.batidas = []        # (t, n_global, secao_idx, batida_no_compasso)
        self.total = 0.0
        self.audio = None
        self.lufs = self.tp = None

    def ev(self, t, tipo, **kw):
        d = dict(t=float(t), tipo=tipo); d.update(kw)
        self.eventos.append(d)
        return d


def compor(secoes, seed=1, raiz=None, cauda=1.2):
    """Monta a faixa inteira: eventos primeiro, áudio depois, a partir deles.

    secoes: [{'gen': 'house', 'bars': 4, 'papel': 'drop', 'bpm': opcional,
              'rotulo': opcional}, ...]
    papel: intro | build | drop | break | fim
    """
    rng = np.random.default_rng(seed * 7717 + 3)
    F = Faixa()
    if raiz is None: raiz = int(rng.integers(45, 52))        # A2..D#3
    # progressão fixa para a faixa inteira: troca de gênero não troca a música
    prog_m = PROGS_MENOR[int(rng.integers(len(PROGS_MENOR)))]
    prog_M = PROGS_MAIOR[int(rng.integers(len(PROGS_MAIOR)))]
    # motivo de melodia: ritmo e contorno, sorteados uma vez e variados
    motivos = _motivos(rng)

    t = 0.0
    n_bat = 0
    bar_glob = 0
    ant_voic = None
    for si, sec in enumerate(secoes):
        G = GENEROS[sec['gen']]
        bpm = float(sec.get('bpm', G['bpm']))
        spb = 60.0 / bpm
        st = spb / 4                      # duração de um passo de 1/16
        papel = sec.get('papel', 'drop')
        bars = int(sec['bars'])
        maior = G['maior']
        esc = MAIOR if maior else MENOR
        prog = prog_M if maior else prog_m
        sw = G['swing']
        t0_sec = t
        F.secoes.append(dict(i=si, t0=t, t1=t + bars * 4 * spb, gen=sec['gen'],
                             nome=sec.get('rotulo', G['nome']), bpm=bpm, papel=papel,
                             bars=bars, spb=spb))
        F.ev(t, 'secao', i=si, gen=sec['gen'], bpm=bpm, papel=papel,
             nome=sec.get('rotulo', G['nome']))
        if papel == 'drop': F.ev(t, 'drop', i=si)
        mot = motivos[si % len(motivos)] if sec.get('motivo') is None else motivos[sec['motivo']]

        for b in range(bars):
            tb = t + b * 4 * spb
            grau = prog[bar_glob % len(prog)]
            ch = triade(esc, grau, raiz)
            ant_voic = voicing(ch, ant_voic, 62)
            F.ev(tb, 'compasso', n=bar_glob, secao=si, acorde=ch[:3], grau=grau)
            for k in range(4):
                F.batidas.append((tb + k * spb, n_bat, si, k))
                F.ev(tb + k * spb, 'batida', n=n_bat, k=k, secao=si)
                n_bat += 1
            ultimo = (b == bars - 1)
            prox = secoes[si + 1] if si + 1 < len(secoes) else None
            vai_dropar = ultimo and prox is not None and prox.get('papel') == 'drop'
            u_sec = (b + .5) / bars

            def T(passo):
                """Instante do passo, com swing nas semicolcheias ímpares."""
                s = tb + passo * st
                if sw and int(passo) % 2 == 1: s += sw * st
                return s

            _padrao(F, sec['gen'], G, papel, b, bars, T, st, spb, ch, ant_voic,
                    esc, raiz, grau, mot, rng, vai_dropar, u_sec, bpm, bar_glob)
            bar_glob += 1
        t += bars * 4 * spb
        if sec['gen'] == 'lofi' or sec.get('vinil'):
            F.ev(t0_sec, 'fx', nome='vinil', dur=t - t0_sec, ganho=1.0)

    F.total = t + cauda
    F.ev(t, 'fim')
    F.eventos.sort(key=lambda e: e['t'])
    _sintetizar(F, seed, raiz)
    return F


def _motivos(rng):
    """Quatro motivos de 1 compasso: (passos, graus, durações em passos).
    Um motivo bom é curto e se repete; a variação está no fim da frase."""
    ritmos = [
        [0, 3, 6, 8, 10, 12], [0, 2, 4, 7, 10, 12, 14], [0, 3, 6, 10, 12],
        [0, 4, 6, 8, 11, 14], [0, 2, 3, 6, 8, 11, 12, 14], [0, 6, 8, 12, 14],
        [2, 4, 6, 10, 12, 14], [0, 3, 4, 7, 8, 11, 12, 15],
    ]
    out = []
    for _ in range(5):
        r = ritmos[int(rng.integers(len(ritmos)))]
        g0 = int(rng.integers(0, 3)) * 2            # começa em 1, 3 ou 5
        graus = []
        gg = g0
        for i in range(len(r)):
            passo = int(rng.choice([-2, -1, -1, 1, 1, 2, 0, 3]))
            gg = int(np.clip(gg + passo, -2, 9))
            graus.append(gg)
        durs = [max(1, (r[i + 1] - r[i]) if i + 1 < len(r) else 16 - r[i]) for i in range(len(r))]
        out.append((r, graus, durs))
    return out


def _grau_nota(esc, raiz, grau_acorde, g, oit=0):
    i = grau_acorde + g
    return raiz + 12 + 12 * oit + esc[i % 7] + 12 * (i // 7)


def _padrao(F, gen, G, papel, b, bars, T, st, spb, ch, voic, esc, raiz, grau,
            mot, rng, vai_dropar, u_sec, bpm, bar_glob):
    """Escreve os eventos de UM compasso do gênero. É aqui que mora o estilo."""
    cheio = papel in ('drop', 'fim')
    intro = papel == 'intro'
    build = papel == 'build'
    pausa = papel == 'break'
    meio = G['meio']
    kit = G['kit']
    raiz_b = ch[0] - 12 if ch[0] >= 48 else ch[0]
    while raiz_b > 45: raiz_b -= 12
    while raiz_b < 33: raiz_b += 12

    def K(p, vel=1.0, **kw): F.ev(T(p), 'kick', vel=vel, **kw)
    def S(p, vel=1.0, ghost=False): F.ev(T(p), 'snare', vel=vel, ghost=ghost)
    def C(p, vel=1.0): F.ev(T(p), 'clap', vel=vel)
    def H(p, vel=1.0, aberto=False): F.ev(T(p), 'hat', vel=vel, aberto=aberto)
    def Bx(p, m, dur, **kw): F.ev(T(p), 'baixo', m=int(m), dur=dur * st, tipo_b=G['baixo'], **kw)
    def L(p, m, dur, tipo=None, vel=1.0): F.ev(T(p), 'lead', m=int(m), dur=dur * st, tipo_l=tipo or G['lead'], vel=vel)
    def A(p, notas, dur, tipo=None, vel=1.0): F.ev(T(p), 'acorde', ms=[int(x) for x in notas], dur=dur * st, tipo_a=tipo or G['acorde'], vel=vel)

    # ------------------------------------------------------- build universal
    # Caixa acelerando (1/4 -> 1/8 -> 1/16), riser e corte de grave: o
    # vocabulário do "vai cair" que todo ouvido reconhece.
    if build:
        frac = (b + 1) / bars
        passo = 4 if frac <= .5 else (2 if frac < 1 else 1)
        if bars == 1: passo = 2
        for p in range(0, 16, passo):
            v = .45 + .55 * ((b * 16 + p) / (bars * 16))
            S(p, v)
        if b == 0:
            F.ev(T(0), 'fx', nome='riser', dur=bars * 4 * spb, m=ch[0] + 12, ganho=.9)
            F.ev(T(0), 'build', dur=bars * 4 * spb)
        if b < bars - 1 or bars == 1:
            K(0, .8)
            if bars > 1: K(8, .7)
        if G['acorde']:
            A(0, voic, 16, vel=.5 + .4 * frac)
        if vai_dropar:
            F.ev(T(12), 'fx', nome='reverso', dur=4 * st, ganho=.8)
        return

    if pausa:
        if G['acorde']:
            A(0, voic, 16, tipo='pad', vel=.8)
        L(0, _grau_nota(esc, raiz, grau, mot[1][0], 0), 8, vel=.6)
        if b % 2 == 1: L(8, _grau_nota(esc, raiz, grau, mot[1][-1], 0), 8, vel=.5)
        H(0, .4); H(8, .4)
        if vai_dropar:
            F.ev(T(8), 'fx', nome='riser', dur=8 * st, m=ch[0] + 12, ganho=.8)
            for p in range(8, 16, 1): S(p, .3 + .05 * (p - 8))
        return

    # crash na cabeça de toda seção cheia
    if cheio and b == 0:
        F.ev(T(0), 'crash', vel=1.0)
        F.ev(T(0), 'fx', nome='impacto', dur=1.4, ganho=.8)

    # ------------------------------------------------------- bateria por gênero
    if gen == 'lofi':
        for p in P('x.........x.....'): K(p, .9)
        if b % 2 == 1: K(7, .6)
        for p in (4, 12): S(p, .8)
        for p in range(0, 16, 2): H(p, .55 if p % 4 else .75)
    elif gen == 'synthwave':
        for p in P('x.......x.x.....'): K(p)
        for p in (4, 12): S(p)
        for p in range(0, 16, 2): H(p, .6)
    elif gen == 'dembow':
        for p in (0, 4, 8, 12): K(p)
        for p in (3, 6, 11, 14): S(p, .85)
        for p in range(0, 16, 2): H(p, .5)
    elif gen in ('house', 'garage'):
        if gen == 'house':
            for p in (0, 4, 8, 12): K(p)
        else:
            for p in P('x.........x.....'): K(p)
            if b % 2: K(7, .7)
        for p in (4, 12): C(p)
        for p in (2, 6, 10, 14): H(p, .8, aberto=(gen == 'house'))
        if gen == 'garage':
            for p in (1, 5, 9, 13): H(p + .35, .45)
        else:
            for p in range(0, 16, 1):
                if p % 4 != 2: H(p, .3)
    elif gen == 'funk':
        # tamborzão: 3+3+2 no bumbo, palmas respondendo
        for p in P('x..x..x...x..x..'): K(p)
        for p in P('....x..x....x.x.'): C(p, .9)
        for p in (2, 5, 9, 11, 14): F.ev(T(p), 'perc', nome='tom', m=48 + (p % 3) * 3, vel=.7)
        for p in range(0, 16, 2): H(p, .45)
    elif gen == 'phonk':
        for p in P('x.....x...x.....'): K(p)
        for p in (4, 12): S(p)
        for p in range(0, 16, 1): H(p, .5 if p % 2 else .7)
    elif gen == 'techno':
        for p in (0, 4, 8, 12): K(p)
        for p in range(16): H(p, .35 + (.45 if p % 4 == 2 else 0), aberto=(p % 4 == 2))
        if b % 2 == 1: C(12, .7)
        for p in (4, 12): F.ev(T(p), 'perc', nome='rim', vel=.5)
    elif gen == 'trance':
        for p in (0, 4, 8, 12): K(p)
        for p in (4, 12): C(p, .8)
        for p in (2, 6, 10, 14): H(p, .9, aberto=True)
        for p in range(0, 16, 1): H(p, .25)
    elif gen in ('dubstep', 'trap', 'future'):
        if gen == 'dubstep':
            for p in P('x.........x.....'): K(p)
        elif gen == 'trap':
            for p in P('x......x..x.....') if b % 2 == 0 else P('x.....x...x..x..'): K(p)
        else:
            for p in P('x......x..x.....'): K(p)
        S(8)
        if gen == 'trap':
            # chimbal de trap: colcheias com rajadas de 1/32 e tercinas
            for p in range(0, 16, 2): H(p, .55)
            rolo = int(rng.integers(0, 3))
            if rolo == 0:
                for k in range(6): H(12 + k * (4 / 6), .35 + .08 * k)
            elif rolo == 1:
                for k in range(8): H(14 + k * .25, .3 + .07 * k)
        else:
            for p in range(0, 16, 2): H(p, .6)
            if gen == 'dubstep': H(14, .7, aberto=True)
    elif gen == 'chiptune':
        for p in P('x.....x.x.......'): K(p)
        for p in (4, 12): S(p)
        for p in range(0, 16, 2): H(p, .6)
    elif gen == 'hardstyle':
        for p in (0, 4, 8, 12): K(p, nota=raiz_b)
        for p in (2, 6, 10, 14): H(p, .8, aberto=True)
        if b % 2 == 1: C(12, .8)
    elif gen == 'dnb':
        for p in P('x.........x.....'): K(p)
        if b % 2: K(11, .8)
        S(4); S(12)
        S(7, .3, ghost=True); S(9, .3, ghost=True); S(15, .35, ghost=True)
        for p in range(0, 16, 2): H(p, .55)
        H(14, .6, aberto=True)
    elif gen == 'gabber':
        for p in (0, 4, 8, 12): K(p)
        for p in (2, 6, 10, 14): H(p, .8, aberto=True)
        for p in range(16): H(p, .3)

    if intro:
        # intro: tira o grave da bateria pela metade — é o que cria a fome
        pass

    # virada no último compasso de seção cheia (antes de troca)
    if cheio and b == bars - 1 and not vai_dropar and gen not in ('lofi',):
        for k, p in enumerate((12, 13, 14, 15)):
            F.ev(T(p), 'perc', nome='tom', m=50 - k * 3, vel=.8)

    if vai_dropar:
        F.ev(T(12), 'fx', nome='reverso', dur=4 * st, ganho=.7)

    # ------------------------------------------------------- baixo
    tb_ = G['baixo']
    if tb_ and not intro:
        r = raiz_b
        if gen == 'lofi':
            Bx(0, r, 8); Bx(10, r + (7 if b % 2 else 0), 6)
        elif gen in ('synthwave',):
            for p in range(0, 16, 2): Bx(p, r + (12 if p % 4 == 2 else 0), 2)
        elif gen == 'dembow':
            Bx(0, r, 3); Bx(3, r, 3); Bx(6, r + 7, 2); Bx(8, r, 3); Bx(11, r, 3); Bx(14, r + 5, 2)
        elif gen == 'house':
            for p in (2, 6, 10, 14): Bx(p, r + 12, 2)
        elif gen == 'garage':
            Bx(0, r, 6); Bx(7, r, 3); Bx(10, r + 3, 6)
        elif gen in ('funk',):
            for p in P('x..x..x...x..x..'): Bx(p, r, 3)
        elif gen == 'phonk':
            Bx(0, r, 6); Bx(6, r, 4); Bx(10, r + (3 if b % 2 else 0), 6)
        elif gen == 'techno':
            linha = [0, 0, 12, 0, 3, 0, 12, 7, 0, 0, 10, 0, 12, 3, 0, 7]
            for p in range(16):
                if rng.random() < .85: Bx(p, r + 12 + linha[(p + b * 3) % 16], 1)
        elif gen == 'trance':
            for p in range(16):
                if p % 4 != 0: Bx(p, r + 12, 1)
        elif gen == 'dubstep':
            Bx(0, r, 6); Bx(6, r + (3 if b % 2 else 0), 4); Bx(10, r + (7 if b % 2 else -2), 6)
        elif gen in ('trap', 'future'):
            Bx(0, r, 7)
            Bx(7, r + (7 if b % 2 else 3), 3, glide=r)
            Bx(10, r, 6)
        elif gen == 'chiptune':
            for p in range(0, 16, 2): Bx(p, r + 12 + (12 if p % 4 == 2 else 0), 2)
        elif gen == 'dnb':
            Bx(0, r, 10); Bx(10, r + (3 if b % 2 else 5), 6)

    # ------------------------------------------------------- acordes
    ta = G['acorde']
    if ta:
        if gen == 'house' or gen == 'garage':
            for p in (0, 3, 6, 10) if gen == 'house' else (0, 6, 10):
                A(p, voic, 2 if gen == 'house' else 3, vel=.9)
        elif gen in ('trance', 'future'):
            # serra gigante em 1/16 com bombeamento: o som da festa
            for p in range(16):
                if gen == 'trance' or p % 2 == 0 or p in (3, 11):
                    A(p, [v + 12 for v in voic], 1 if gen == 'trance' else 2, vel=.75 if p % 4 else 1.0)
        elif gen == 'chiptune':
            # arpejo de 1/32: o acorde do console
            notas = voic + [voic[0] + 12]
            for k in range(32):
                F.ev(T(k / 2), 'acorde', ms=[notas[k % 4] + 12], dur=st / 2, tipo_a='arpchip', vel=.7)
        elif gen in ('hardstyle', 'gabber'):
            if b % 2 == 0: A(0, [v + 12 for v in voic], 16, tipo='supersaw', vel=.55)
        elif gen == 'lofi':
            A(0, voic, 14, vel=.9)
            if b % 2: A(14, voic, 2, vel=.5)
        else:
            A(0, voic, 16, vel=.7)

    # ------------------------------------------------------- melodia
    if not intro or gen == 'lofi':
        ritmo, graus, durs = mot
        ult_frase = (b % 4 == 3)
        oit = 2 if G['lead'] in ('square', 'bell') else 1
        if gen in ('dubstep',) and b % 2 == 0: return
        if gen == 'phonk':
            # melodia de cowbell em 1/16: o motivo inteiro, sempre igual
            for p in range(16):
                if p in (0, 3, 6, 8, 10, 11, 14):
                    gi = graus[(p * 3) % len(graus)] % 5
                    F.ev(T(p), 'lead', m=int(_grau_nota(esc, raiz, 0, gi, 1)), dur=st,
                         tipo_l='cow', vel=.9)
            return
        for i, (p, gr, d) in enumerate(zip(ritmo, graus, durs)):
            if ult_frase and i == len(ritmo) - 1:
                gr = 0                        # a frase resolve na tônica do acorde
            if gen == 'lofi' and rng.random() < .35: continue
            m = _grau_nota(esc, raiz, grau, gr, oit)
            L(p, m, min(d, 4) if gen not in ('trance', 'synthwave') else d, vel=.95 if i == 0 else .82)


# =================================================================== síntese
# Ganhos medidos contra a curva de mix eletrônico comercial e pensando no
# alto-falante de celular, que é onde o Short toca: abaixo de 120 Hz ele
# quase não reproduz, então o grave não pode carregar a música sozinho.
GANHO = dict(kick=-5.5, snare=-5.0, clap=-5.5, hat=-5.0, perc=-8.0, crash=-11.0,
             baixo=-10.0, lead=-5.0, acorde=-8.0, fx=-9.0)


def _reverb(x, rng, dur=1.6, mix=.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (dur / 5.5))
        ir = _lp(ir, 6500); ir[:int(.012 * SR)] = 0
        ir = ir / np.sqrt((ir ** 2).sum())
        out[:, c] = sg.oaconvolve(x[:, c], ir.astype(np.float32), 'full')[:len(x)]
    return out * mix


def _eco(x, atraso, fb=.38, mix=.25):
    k = int(atraso * SR)
    out = np.zeros_like(x)
    y = x.copy()
    for i in range(1, 5):
        sh = np.zeros_like(x)
        if k * i < len(x):
            sh[k * i:] = y[:-k * i] * (fb ** i)
            # pingue-pongue: alterna canal
            if i % 2: sh = sh[:, ::-1]
            out += sh
    return out * mix


def _sidechain(F, n, profundidade=.55, rel=.18):
    """Bombeamento: a música abaixa em cada bumbo e volta. Construído a
    partir dos próprios eventos de bumbo — o mesmo instante que faz a tela
    pulsar."""
    gm = np.ones(n, np.float32)
    rk = int(rel * SR)
    curva = 1 - profundidade * np.exp(-np.arange(rk) / SR / (rel / 3.2))
    for e in F.eventos:
        if e['tipo'] != 'kick': continue
        i = int(e['t'] * SR)
        j = min(n, i + rk)
        if j > i: gm[i:j] = np.minimum(gm[i:j], curva[:j - i])
    return gm


def _put(buf, s, t0, ganho=1.0, pan=0.0):
    a = (pan + 1) * np.pi / 4
    i = int(round(t0 * SR)); j = min(i + len(s), len(buf))
    if j <= i or i < 0: return
    seg = s[:j - i] * ganho
    buf[i:j, 0] += math.cos(a) * seg
    buf[i:j, 1] += math.sin(a) * seg


def _sintetizar(F, seed, raiz):
    rng = np.random.default_rng(seed * 104729 + 11)
    n = int(F.total * SR) + SR
    bat = np.zeros((n, 2), np.float32)
    grave = np.zeros((n, 2), np.float32)
    mus = np.zeros((n, 2), np.float32)
    efx = np.zeros((n, 2), np.float32)
    kits = {}
    cache_n = {}

    def kit_de(t):
        for s in reversed(F.secoes):
            if t >= s['t0'] - 1e-6: return s
        return F.secoes[0]

    for e in F.eventos:
        tp = e['tipo']; t = e['t']
        sec = kit_de(t)
        G = GENEROS[sec['gen']]
        kn = G['kit']
        if kn not in kits:
            kits[kn] = Bateria(np.random.default_rng(seed * 31 + len(kits)), kn)
        K = kits[kn]
        v = e.get('vel', 1.0)
        if tp == 'kick':
            s = K.get('kick', nota=e.get('nota'))
            _put(bat, s, t, g(GANHO['kick']) * v)
            if kn == 'trance' or kn == 'techno':       # cauda de rumble
                pass
        elif tp == 'snare':
            s = K.get('snare')
            _put(bat, s, t, g(GANHO['snare']) * v * (.6 if e.get('ghost') else 1), -.05)
        elif tp == 'clap':
            _put(bat, K.get('clap'), t, g(GANHO['clap']) * v, .05)
        elif tp == 'hat':
            s = K.get('hat', aberto=bool(e.get('aberto')))
            _put(bat, s, t, g(GANHO['hat']) * v, .25)
        elif tp == 'perc':
            if e['nome'] == 'tom': s = K.get('tom', nota=e['m'])
            else: s = K.get('rim')
            _put(bat, s, t, g(GANHO['perc']) * v, -.3)
        elif tp == 'crash':
            _put(bat, K.get('crash'), t, g(GANHO['crash']) * v, .1)
        elif tp == 'baixo':
            ch = ('b', e['tipo_b'], e['m'], round(e['dur'], 3), e.get('glide'))
            if ch not in cache_n or e['tipo_b'] == 'wobble':
                cache_n[ch] = baixo(e['tipo_b'], e['m'], e['dur'] + .02, sec['bpm'], rng,
                                    glide_de=e.get('glide'))
            _put(grave, cache_n[ch], t, g(GANHO['baixo']))
        elif tp == 'lead':
            if e['tipo_l'] == 'cow':
                s = K.get('cow', nota=e['m'])
                _put(mus, s, t, g(GANHO['lead'] + 3) * v, .1)
                continue
            ch = ('l', e['tipo_l'], e['m'], round(e['dur'], 3))
            if ch not in cache_n:
                cache_n[ch] = nota(e['tipo_l'], e['m'], e['dur'] + .03, rng, sec['bpm'])
            _put(mus, cache_n[ch], t, g(GANHO['lead']) * v, .12)
        elif tp == 'acorde':
            for k, m in enumerate(e['ms']):
                ch = ('a', e['tipo_a'], m, round(e['dur'], 3))
                if ch not in cache_n:
                    cache_n[ch] = nota(e['tipo_a'], m, e['dur'] + .03, rng, sec['bpm'])
                _put(mus, cache_n[ch], t, g(GANHO['acorde']) * v / max(1, len(e['ms'])) ** .35,
                     -.35 + .7 * k / max(1, len(e['ms']) - 1))
        elif tp == 'fx':
            s = fx(e['nome'], e.get('dur', 1.0), rng, e.get('m', 60))
            _put(efx, s, t, g(GANHO['fx']) * e.get('ganho', 1.0))

    # bombeamento em tudo que não é bateria, nos gêneros que vivem disso
    gm = _sidechain(F, n)
    secs_bomba = [(s['t0'], s['t1']) for s in F.secoes
                  if s['gen'] in ('house', 'trance', 'future', 'garage', 'dubstep', 'synthwave', 'hardstyle', 'gabber', 'funk')]
    bomba = np.ones(n, np.float32)
    for a, b_ in secs_bomba:
        i, j = int(a * SR), min(n, int(b_ * SR))
        bomba[i:j] = gm[i:j]
    mus *= bomba[:, None]
    grave *= (.35 + .65 * bomba)[:, None]

    # ambiência: reverb na música e na caixa, eco na melodia
    rv_rng = np.random.default_rng(seed + 99)
    mus_w = mus + _reverb(mus, rv_rng, 1.8, .28)
    spb_medio = float(np.mean([s['spb'] for s in F.secoes]))
    mus_w = mus_w + _eco(mus, spb_medio * .75, .35, .18)
    bat_w = bat + _reverb(bat, rv_rng, .9, .10)
    efx_w = efx + _reverb(efx, rv_rng, 2.2, .3)

    # o grave ganha harmônicos (saturação paralela em 200-900 Hz): é o que
    # faz o baixo existir no alto-falante do celular, que não toca o sub
    gr = _hp(grave.T, 30).T.astype(np.float32)
    harm = np.stack([_bp(np.tanh(gr[:, c] * 4.0), 180, 900) for c in range(2)], 1)
    mix = bat_w + gr + .32 * harm.astype(np.float32) + mus_w + efx_w
    # inclinação de master: tira sub, abre o brilho
    sub = np.stack([_lp(mix[:, c], 90) for c in range(2)], 1)
    ar = np.stack([_hp(mix[:, c], 5500) for c in range(2)], 1)
    pres = np.stack([_bp(mix[:, c], 1800, 5200) for c in range(2)], 1)
    mix = (mix - .42 * sub + .8 * ar + 1.1 * pres).astype(np.float32)
    mix = mix[:int(F.total * SR)]
    # cola: saturação leve no barramento
    mix = (np.tanh(mix * 1.15) / 1.15).astype(np.float32)
    # fim: fade curto para não estalar no laço
    k = int(.25 * SR)
    mix[-k:] *= np.linspace(1, 0, k)[:, None]
    mix, lu, tp = QA.master(mix, -14.0)
    F.audio, F.lufs, F.tp = mix.astype(np.float32), lu, tp
    # espectro por quadro, para cenas que leem o som de verdade
    F.espectro = None
    return F


def espectro(F, fps=30, bandas=24, fmin=40, fmax=12000):
    """Energia por banda em cada quadro, medida no áudio final. É a única
    leitura do som que o vídeo faz — e lê o som que ele mesmo gerou."""
    x = F.audio.mean(1)
    hop = SR // fps
    win = 2048
    nq = int(len(x) / hop) + 1
    xp = np.concatenate([np.zeros(win // 2), x, np.zeros(win)])
    w = np.hanning(win).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    bordas = np.geomspace(fmin, fmax, bandas + 1)
    idx = [(np.searchsorted(freqs, bordas[i]), max(np.searchsorted(freqs, bordas[i + 1]), np.searchsorted(freqs, bordas[i]) + 1)) for i in range(bandas)]
    out = np.zeros((nq, bandas), np.float32)
    for q in range(nq):
        seg = xp[q * hop:q * hop + win]
        if len(seg) < win: break
        mag = np.abs(np.fft.rfft(seg * w))
        out[q] = [mag[a:b].mean() for a, b in idx]
    out = 20 * np.log10(out + 1e-6)
    lo, hi = np.percentile(out, 5), np.percentile(out, 99.5)
    out = np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)
    # cada banda normalizada pelo próprio teto: senão o grave domina tudo
    out = out / (np.percentile(out, 98, axis=0) + 1e-3)
    return np.clip(out, 0, 1)
