#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep22 — Como o balão de ar quente sobe (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (jatos do queimador, paraquedas, ventoinha)

A física manda no desenho: o voo de "gancho", "subir" e "descer" sai de
`D.Voo` (queimador, perda de calor, paraquedas, empuxo x peso, arrasto). Os
jatos do queimador começam nas batidas da música (`T.L`); o painel, a chama, a
altura do chão na tela e a régua leem o mesmo instante.

    python3 ep22_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep22_motor.py <saida.mp4> subir descer        # só esses capítulos (teste)
    python3 ep22_motor.py --folha <saida.png>             # 2 quadros por capítulo (FR=.3,.8)
    python3 ep22_motor.py --folha <saida.png> subir       # 5 quadros (FR=.1,.3,.5,.7,.9)
    python3 ep22_motor.py --folha <saida.png> subir 0.2 0.6
"""
import math, os, sys
import numpy as np
import longo as LG
import ep22_desenho as D          # registra a paleta do episódio (LG.PAL = 'ep22')
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep22_desenho import (pol, contorno, brilho, gradiente, seta_forca, barra, hsh, Paisagem, Particulas,
                          CEU0, CEU1, CEU2, CEU3, CEU4, CEU5, CAMPO0, CAMPO1, CAMPO2, CAMPO3, NEVOA, MORRO0,
                          MORRO1, VERM, AMAR, AZUL, BRAN, TEAL, VIME0, VIME1, VIME2, INTQ0, INTQ1, INTF0, INTF1)
import ritmo_marca as RM
import quizaudio as QA
from ep22_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2622, 45
GANHO_MUSICA = -10.0          # trilha baixa: o texto manda
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
SR = LG.SR
PAIS = Paisagem()
K = PAIS.ppm * D.M_POR_U      # px por unidade do perfil nas cenas de voo (~1,3)
CX = 150                      # o balão nas cenas de voo
MY = PAIS.y_cesto() - (D.S_FUNDO - 100) * K       # a boca do balão na tela
PESO = D.Voo.M


def milhar(n): return f"{int(round(n)):,}".replace(',', '.')
def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')


def rampa(t, marcos):
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * (t - a) / (b - a)
    return marcos[-1][1]


def x_corte(cap):
    for c in CORTES:
        if c['de'][0] == cap or c['ate'][0] == cap: return c['x']
    return 60


def tit(tela, txt, y, cor=BRANCO, tam=17, x=PX0, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO, centro=centro)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def hud_v(tela, cap, linhas, y=6):
    """No corte vertical o painel some: os números vão para o alto do recorte."""
    if not VERTICAL: return
    x = x_corte(cap) + 90
    for k, (txt, cor) in enumerate(linhas):
        w = tela.largura_texto(txt, 9) + 8
        painel(tela, x - w // 2, y + k * 15 - 3, w, 14, borda=cor)
        tela.texto(txt, x, y + k * 15, cor, tam=9, centro=True)


def etiqueta(tela, txt, x, y, cor, tam=9, centro=True):
    w = tela.largura_texto(txt, tam)
    hh = 14 if tam < 14 else 22
    xx = x - w // 2 if centro else x
    painel(tela, xx - 5, y - 4, w + 10, hh + 2, borda=cor)
    tela.texto(txt, xx, y, cor, tam=tam)


def rotulo(tela, txt, x, y, ax, ay, cor=AMARELO, direita=False):
    """Rótulo 1x com fio até a peça (ax, ay) e bolinha na ponta."""
    w = tela.largura_texto(txt, 9)
    tx = x - w if direita else x
    tela.texto(txt, tx, y, cor, tam=9, contorno=PRETO)
    lx = (tx - 3) if ax < tx else (tx + w + 2)
    tela.linha(lx, y + 3, ax, ay, cor)
    tela.disco(ax, ay, 1.5, cor)


def seta(tela, x0, y0, x1, y1, cor, esp=4, cab=7):
    seta_forca(tela, x0, y0, x1, y1, cor, esp, cab)


def barra_kg(tela, x, y, w, kg, kmax, cor, nome):
    tela.texto(nome, x, y, cor, tam=9, contorno=PRETO)
    tela.texto(f"{milhar(kg)} KG", x + w, y, BRANCO, tam=9, contorno=PRETO, centro='d')
    barra(tela, x, y + 10, w, 6, kg / kmax, cor)


def temp_cor(T):
    if T < 40: return CIANO
    if T < 80: return AMARELO
    if T < 110: return LARANJA
    return VERMELHO


# ----------------------------------------------------------------- sons
_RNG = np.random.default_rng(22)


def tique(f=1800, dur=.03):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))).astype(np.float32)


def jato_som(dur):
    """Jato do queimador: ruído grave e macio (filtrado), sem estalo."""
    n = max(64, int((dur + .3) * SR))
    x = _RNG.standard_normal(n).astype(np.float32)
    a = QA.bp(x, 120, 700)
    b = QA.lp(QA.lp(x, 160), 160)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / .08) * np.clip((dur + .3 - tt) / .3, 0, 1)
    env *= 1 + .12 * np.sin(2 * np.pi * 7 * tt)
    y = (a * .7 + b * 1.4) * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def sopro(dur, f_lo=900, f_hi=3200):
    """Ar escapando (paraquedas) ou soprado (ventoinha)."""
    n = max(64, int(dur * SR))
    x = QA.bp(_RNG.standard_normal(n).astype(np.float32), f_lo, f_hi)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / .4) * np.clip((dur - tt) / .5, 0, 1)
    y = x * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def zumbido(dur, f=95):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * 2 * f * tt)) * np.minimum(1, np.minimum(tt, dur - tt) / .4)
    return (y * .7).astype(np.float32)


def baque(f=70, dur=.4):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f * tt - 10 * tt * tt)) * np.exp(-tt / (dur / 4)) * np.minimum(1, tt / .004)
    return y.astype(np.float32)


# ================================================================== cenas
class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def batidas(self, tipo='batida'):
        return [e['t'] - self.t0 for e in self.T.L.lista(tipo) if self.t0 - 1e-6 <= e['t'] < self.t0 + self.dur - 1e-6]


def jatos_de(inicios, dur):
    """Lista de (início, fim) dos jatos; e a função 0/1 correspondente."""
    js = [(a, a + dur) for a in inicios]

    def f(t, *_):
        for a, b in js:
            if a <= t < b: return 1.0
        return 0.0
    return js, f


def chama_de(js, t):
    """Força visual da chama: acende rápido, apaga rápido."""
    for a, b in js:
        if a - .02 <= t < b + .15:
            return min(1.0, (t - a + .02) / .08) * min(1.0, (b + .15 - t) / .15)
    return 0.0


def cena_voo(tela, t, h, X, e, x1=W, regua=True, cx=CX):
    """Paisagem vista do balão + o balão + a régua de altitude."""
    PAIS.desenhar(tela, h, X, t, x1)
    # sombra do balão no chão (quando o chão embaixo dele aparece)
    ys = PAIS.hy + PAIS.F * (h + PAIS.CAM) / PAIS.D
    if ys < PALCO_H + 4:
        w = 34 * max(.4, 1 - h / 120)
        for i in range(int(cx - w), int(cx + w)):
            for j in range(-2, 3):
                if ((i + j) % 2 == 0) and ((i - cx) / w) ** 2 + (j / 2.5) ** 2 <= 1:
                    tela.px(i, ys + j, D.CAMPO0 if (i + j) % 4 else PRETO)
    D.balao(tela, cx, MY, K, t, e, x1=x1)
    PAIS.arvores_(tela, h, X, x1, frente=True)
    if regua and not VERTICAL: PAIS.regua(tela, h)


def painel_voo(tela, q, ritmo_txt=('TEMPO REAL', VERDE), extra=None):
    fundo_painel(tela)
    tela.texto(ritmo_txt[0], W - 10, 9, ritmo_txt[1], tam=9, centro='d', contorno=PRETO)
    tit(tela, 'BALÃO', 9, ACO3, 9)
    tit(tela, 'ALTITUDE', 24, ACO3, 9)
    tit(tela, f"{milhar(q['h'])} M", 34, AMARELO, 17)
    tit(tela, 'AR DENTRO', 56, ACO3, 9)
    T = q['T']
    tit(tela, f"{milhar(T)} °C", 66, temp_cor(T), 17)
    barra(tela, PX0 + 82, 70, 76, 6, (T - 20) / 100, temp_cor(T))
    v = q['v']
    tit(tela, 'SUBINDO' if v > .05 else ('DESCENDO' if v < -.05 else 'PARADO'), 88, ACO3, 9)
    tit(tela, f"{dec(abs(v), 1)} M/S", 98, BRANCO, 17)
    if abs(v) > .05:
        x = PX0 + 120
        if v > 0: seta(tela, x, 113, x, 98, VERDE, 3, 5)
        else: seta(tela, x, 98, x, 113, VERMELHO, 3, 5)
    barra_kg(tela, PX0, 122, 156, q['L'], 900, VERDE, 'EMPUXO')
    barra_kg(tela, PX0, 142, 156, PESO, 900, VERMELHO, 'PESO')
    acesa = q.get('chama', 0) > .3
    tela.ret(PX0, 165, 7, 7, PRETO); tela.ret(PX0 + 1, 166, 5, 5, LARANJA if acesa else ACO0)
    tela.texto('QUEIMADOR ' + ('ACESO' if acesa else 'APAGADO'), PX0 + 11, 165, LARANJA if acesa else ACO2, tam=9,
               contorno=PRETO)
    ab = q.get('vent', 0) > .02
    tela.ret(PX0, 180, 7, 7, PRETO); tela.ret(PX0 + 1, 181, 5, 5, CIANO if ab else ACO0)
    tela.texto('PARAQUEDAS ' + ('ABERTO' if ab else 'FECHADO'), PX0 + 11, 180, CIANO if ab else ACO2, tam=9,
               contorno=PRETO)
    if extra: extra(tela)


def hud_voo(tela, cap, q):
    hud_v(tela, cap, [(f"ALTITUDE {milhar(q['h'])} M", AMARELO), (f"AR DENTRO {milhar(q['T'])} °C", temp_cor(q['T']))])


def ar_quente_saindo(tela, t, cx, my, k, forca):
    """Ar quente escapando pela fresta do paraquedas: fiapos tremidos que sobem."""
    yt = my - 100 * k
    for i in range(14):
        u = (t * .7 + i / 14) % 1
        x = cx + (hsh(i, 3) - .5) * 40 * k * (1 + u) + math.sin(t * 5 + i) * 2
        y = yt + 8 * k - u * 30
        if forca * (1 - u) > .15:
            tela.px(x, y, CEU3 if i % 3 else BRANCO)
            tela.px(x + 1, y - 1, CEU2)


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        bs = self.batidas('batida')
        ini = [b for k, b in enumerate(bs) if k % 4 in (0, 2)]
        self.js, f = jatos_de(ini, .7)
        Ta, rho = D.ar_fora(60)
        Teq = Ta / (1 - PESO / (D.VOLUME * rho))
        self.voo = D.Voo(self.dur + 1, f, lambda t: 0.0, h0=60, v0=.8, Tin0=Teq + 1.2)

    def desenhar(self, tela, t, tg):
        q = self.voo.q(t)
        q['chama'] = chama_de(self.js, t)
        x1 = W if VERTICAL else PX0 - 8
        cena_voo(tela, t, q['h'], 4 * t, dict(chama=q['chama']), x1=W)
        hud_voo(tela, 'gancho', q)
        if VERTICAL: return
        painel_voo(tela, q)

    def sons(self, fx):
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .07)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        PAIS.ceu(tela, 0, t, W, sol=True)
        PAIS.chao(tela, 400, 30 * t, t, W)
        k = .62
        my = 120 + math.sin(t * 1.3) * 2
        ch = 1.0 if (t % 3) < .8 else 0.0
        D.balao(tela, 390, my, k, t, dict(chama=ch))
        D.balao(tela, 452, 52 + math.sin(t * 1.1 + 1), .3, t + 3, dict(chama=0, rot=1.0))
        n = int(t / .045)
        for j, linha in enumerate(("COMO O BALÃO", "DE AR QUENTE SOBE")):
            vis = linha[:max(0, n - j * 13)]
            tela.texto(vis, 22, 40 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("COMO VOA / FLUTUA", 22, 112, AMARELO, tam=17, contorno=PRETO)

    def sons(self, fx):
        for k in range(3):
            fx.put(fx.blip(72 + k * 4, .1), self.t0 + 1.2 + k * .25, .2)
        fx.put(jato_som(.8), self.t0, .05)
        fx.put(jato_som(.8), self.t0 + 3, .05)


# ============================================================ moléculas
class Particulas_(Cena):
    N = 60
    T_AQ0, T_AQ1 = 8.0, 21.0

    def preparar(self):
        self.pa = Particulas(self.N, 11)
        self.pb = Particulas(self.N, 12)
        ts = np.arange(0, self.dur + 1, 1 / 60)
        vel = np.array([.22 * (1 + .9 * self.calor(x)) for x in ts])
        self.ts, self.fase_b = ts, np.concatenate([[0], np.cumsum(vel[:-1]) / 60])
        # quando cada molécula sai (a última primeiro)
        self.sai = {}
        for i in range(self.N - 1, -1, -1):
            for x in ts:
                if self.n_fica(x) <= i:
                    self.sai[i] = float(x); break

    def calor(self, t): return suave((t - self.T_AQ0) / (self.T_AQ1 - self.T_AQ0))
    def temp(self, t): return 20 + 79 * self.calor(t)
    def n_fica(self, t): return int(round(self.N * 293.15 / (self.temp(t) + 273.15)))
    def massa(self, t): return 1.2041 * 293.15 / (self.temp(t) + 273.15)

    def fase(self, t): return float(np.interp(t, self.ts, self.fase_b))

    def caixas(self):
        if VERTICAL:
            x0 = x_corte('particulas')
            return (x0 + 8, 52, 76, 96), (x0 + 96, 52, 76, 96)
        return (32, 50, 104, 104), (168, 50, 104, 104)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        o = int(t * 3) % 24
        for x in range(-o, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(10, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        A, B = self.caixas()
        T = self.temp(t)
        n = self.n_fica(t)
        # chama embaixo da caixa quente
        acesa = self.T_AQ0 - .5 <= t < 30.0
        gx = B[0] + B[2] / 2
        for (x, y, w, h), quente in ((A, False), (B, True)):
            painel(tela, x - 4, y - 4, w + 8, h + 8, borda=TRACO, fundo=PRETO, luz=FUNDO3)
            dither(tela, x, y, w, h, FUNDO2 if not quente or T < 40 else INTQ0, PRETO)
            if quente:
                gw = int(w * .3)
                tela.ret(x + w // 2 - gw // 2, y + h, gw, 4, PRETO)        # boca aberta embaixo
                tela.ret(x + w // 2 - gw // 2, y + h - 1, gw, 1, FUNDO)
            nome = 'AR QUENTE' if quente else 'AR FRIO'
            tela.texto(nome, x + w // 2, y - 17, LARANJA if quente else CIANO, tam=9, centro=True, contorno=PRETO)
            tela.texto('1 METRO CÚBICO', x + w // 2, y + h + 8, ACO3, tam=9, centro=True, contorno=PRETO)
        if acesa:
            D.chama(tela, gx, B[1] + B[3] + 34, 1.1, .9 + .1 * math.sin(t * 9), t, 3)
            tela.ret(gx - 6, B[1] + B[3] + 34, 12, 6, ACO2)
            tela.ret(gx - 6, B[1] + B[3] + 34, 12, 1, ACO4)
        # moléculas
        fa = .22 * t
        fb = self.fase(t)
        self.pa.desenhar(tela, A[0] + 2, A[1] + 2, A[2] - 4, A[3] - 4, fa, CIANO, FUNDO3)
        cb = CHAMA1 if T > 70 else (LARANJA if T > 40 else CIANO)
        self.pb.desenhar(tela, B[0] + 2, B[1] + 2, B[2] - 4, B[3] - 4, fb, cb, BRASA if T > 40 else FUNDO3,
                         idx=[i for i in range(self.N) if not (i in self.sai and t >= self.sai[i])])
        # as que saem pela boca
        p_all = self.pb.pos
        for i, ts in self.sai.items():
            u = t - ts
            if u < 0 or u > 2.2: continue
            p0 = p_all(self.fase(ts))[i]
            sx, sy = B[0] + 2 + p0[0] * (B[2] - 4), B[1] + 2 + p0[1] * (B[3] - 4)
            bx, by = gx + (hsh(i, 1) - .5) * B[2] * .2, B[1] + B[3]
            if u < .7:
                f = u / .7
                x, y = sx + (bx - sx) * f, sy + (by - sy) * f
            else:
                f = (u - .7) / 1.5
                lado = -1 if i % 2 else 1
                x, y = bx + lado * f * 40, by + 4 + f * 22
            if u < 2.0:
                tela.ret(x - 1, y - 1, 2, 2, cb)
        # termômetros e números
        for (x, y, w, h), TT in ((A, 20.0), (B, T)):
            tx = x + w + 2 if not VERTICAL else x + w - 6
            if not VERTICAL:
                tela.ret(tx + 1, y + 10, 5, h - 18, PRETO)
                tela.ret(tx + 2, y + 11, 3, h - 20, FUNDO3)
                hh = int((h - 20) * (TT + 10) / 120)
                tela.ret(tx + 2, y + h - 9 - hh, 3, hh, temp_cor(TT))
                tela.disco(tx + 3.5, y + h - 7, 4, PRETO)
                tela.disco(tx + 3.5, y + h - 7, 3, temp_cor(TT))
            tela.texto(f"{milhar(TT)} °C", x + w // 2, y + 4, temp_cor(TT), tam=9, centro=True, contorno=PRETO)
        if t >= 23.8:
            for (x, y, w, h), m in ((A, 1.2041), (B, self.massa(t))):
                etiqueta(tela, f"{dec(m, 2)} KG", x + w // 2, y + h - 16, AMARELO if m > 1 else LARANJA)
        if t >= 39.8:
            u = (t - 39.8) % 1.6 / 1.6
            x = B[0] + B[2] // 2
            seta(tela, x, B[1] - 26 - u * 4, x, B[1] - 40 - u * 4, VERDE, 3, 5)
        if VERTICAL:
            hud_v(tela, 'particulas', [(f"MOLÉCULAS: 60 E {n}", BRANCO)], y=180)
            return
        fundo_painel(tela)
        tit(tela, '1 METRO CÚBICO DE AR', 9, ACO3, 9)
        tit(tela, 'FRIO', 26, CIANO, 9)
        tit(tela, '20 °C', 36, CIANO, 17)
        tit(tela, 'QUENTE', 26, LARANJA, 9, x=PX0 + 84)
        tit(tela, f"{milhar(T)} °C", 36, temp_cor(T), 17, x=PX0 + 84)
        tit(tela, 'MOLÉCULAS (DESENHO)', 64, ACO3, 9)
        tit(tela, '60', 74, BRANCO, 17)
        tit(tela, str(n), 74, BRANCO if n == 60 else LARANJA, 17, x=PX0 + 84)
        tit(tela, 'VELOCIDADE', 100, ACO3, 9)
        barra(tela, PX0, 112, 70, 6, .45, CIANO)
        barra(tela, PX0 + 84, 112, 70, 6, .45 * (1 + .9 * self.calor(t)), LARANJA)
        if t >= 23.8:
            tit(tela, 'MASSA', 130, ACO3, 9)
            tit(tela, '1,20 KG', 140, AMARELO, 17)
            tit(tela, f"{dec(self.massa(t), 2)} KG", 140, LARANJA, 17, x=PX0 + 84)
        if t >= 39.8:
            tit(tela, 'MENOS DENSO:', 166, VERDE, 9)
            tit(tela, 'MAIS LEVE QUE O AR FRIO', 178, BRANCO, 9)

    def sons(self, fx):
        fx.put(jato_som(30.0 - self.T_AQ0 + .5), self.t0 + self.T_AQ0 - .5, .03)
        for i, ts in self.sai.items():
            fx.put(tique(2400 + (i % 5) * 120, .02), self.t0 + ts, .05)
        fx.put(fx.blip(76, .1), self.t0 + 23.8, .12)
        fx.put(fx.blip(79, .1), self.t0 + 31.8, .12)


# ============================================================ empuxo
class Empuxo(Cena):
    def preparar(self):
        self.pf = Particulas(130, 21)
        self.pq = Particulas(103, 22)

    def desenhar(self, tela, t, tg):
        cx = 215 if not VERTICAL else x_corte('empuxo') + 90
        gradiente(tela, 0, 0, W, PALCO_H, [(0, CEU0), (.6, CEU2), (.9, CEU3), (1, CEU4)])
        for x in range(0, W):
            tela.ret(x, PAIS.morro0[x] + 92, 1, PALCO_H, MORRO1)
            tela.ret(x, PAIS.morro1[x] + 100, 1, PALCO_H, MORRO0)
        # tanque de água (o navio do ep06)
        if not VERTICAL:
            x0, y0, w, h = 16, 62, 112, 104
            painel(tela, x0 - 4, y0 - 4, w + 8, h + 8, borda=TRACO, fundo=PRETO, luz=FUNDO3)
            dither(tela, x0, y0, w, h, FUNDO2, FUNDO)
            ya = y0 + 46
            dither(tela, x0, ya, w, y0 + h - ya, AGUA0, AGUA1)
            tela.ret(x0, ya, w, 1, CIANO)
            by = ya - 4 + math.sin(t * 1.6) * 1.5
            bx = x0 + w // 2
            tela.disco(bx, by, 15, PRETO)
            tela.disco(bx, by, 14, D.VERM[1])
            tela.disco(bx - 4, by - 5, 6, D.VERM[0])
            dither(tela, bx - 14, ya, 29, by + 14 - ya, AGUA0, D.VERM[2])
            tela.ret(x0, ya, w, 1, CIANO)
            seta(tela, bx + 24, by + 18, bx + 24, by - 14, VERDE, 4, 6)
            seta(tela, bx - 24, by - 14, bx - 24, by + 18, VERMELHO, 4, 6)
            tela.texto('ÁGUA', bx, y0 + h - 12, CIANO, tam=9, centro=True, contorno=PRETO)
            tela.texto('EMPUXO', bx + 24, by - 26, VERDE, tam=9, centro=True, contorno=PRETO)
            tela.texto('PESO', bx - 24, by + 24, VERMELHO, tam=9, centro=True, contorno=PRETO)
            if t < 7.6 and int(t * 3) % 2 == 0:
                tela.ret_vazado(x0 - 6, y0 - 6, w + 12, h + 12, AMARELO)
        # o balão
        k = .95
        sobe = max(0.0, t - 28.6)
        my = 150 - sobe * sobe * .25
        corte = 1.0 if 14.6 <= t < 28.6 else 0.0
        quente = 1.0 if t >= 21.6 else 0.0
        bs = self.batidas('batida')
        ch = 1.0 if (any(b <= t < b + .6 for b in bs[::4]) and t >= 21.6) else 0.0
        m = D.balao(tela, cx, my, k, t, dict(corte=corte, quente=quente, chama=ch))
        if corte:
            x0, y0 = cx - 46 * k, my - 100 * k
            if quente:
                self.pq.desenhar(tela, x0, y0, 92 * k, 100 * k, .5 * t, CHAMA1, BRASA, mask=m)
            else:
                self.pf.desenhar(tela, x0, y0, 92 * k, 100 * k, .25 * t, CIANO, INTF1, mask=m)
        # setas
        if 7.6 <= t < 14.6 or t >= 28.6:
            u = (t * .8) % 1
            L = 30 if t < 14.6 else 44
            seta(tela, cx - 64, my - 30 + 10, cx - 64, my - 30 - L + 10 - u * 3, VERDE, 4, 7)
            tela.texto('EMPUXO' if t < 28.6 else '720 KG', cx - 64, my - 30 - L - 2, VERDE, tam=9, centro=True,
                       contorno=PRETO)
        if 14.6 <= t < 21.6:
            etiqueta(tela, 'AR FRIO: 3.380 KG', cx, my - 108 * k - 8, CIANO)
        elif 21.6 <= t < 28.6:
            etiqueta(tela, 'AR QUENTE: 2.660 KG', cx, my - 108 * k - 8, LARANJA)
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'ARQUIMEDES NO AR', 9, ACO3, 9)
        tit(tela, 'BALÃO DE 2.800', 24, BRANCO, 9)
        tit(tela, 'METROS CÚBICOS', 35, BRANCO, 9)
        y = 58
        if t >= 14.6:
            barra_kg(tela, PX0, y, 156, 3380, 3600, CIANO, 'AR FRIO DESLOCADO'); y += 26
        if t >= 21.6:
            barra_kg(tela, PX0, y, 156, 2660, 3600, LARANJA, 'AR QUENTE DENTRO'); y += 26
        if t >= 28.6:
            tela.ret(PX0, y - 4, 156, 1, ACO1)
            barra_kg(tela, PX0, y, 156, 720, 3600, VERDE, 'SOBRA: EMPUXO'); y += 26
        if t < 14.6:
            tit(tela, 'EMPUXO = PESO DO', 70, VERDE, 9)
            tit(tela, 'FLUIDO DESLOCADO', 82, VERDE, 9)
            tit(tela, 'NA ÁGUA E NO AR', 100, BRANCO, 9)

    def sons(self, fx):
        for a in (14.6, 21.6, 28.6):
            fx.put(fx.blip(74, .1), self.t0 + a, .12)
        bs = self.batidas('batida')
        for b in bs[::4]:
            if b >= 21.6: fx.put(jato_som(.6), self.t0 + b, .05)


# ============================================================ a conta
class Conta(Cena):
    def preparar(self):
        bs = self.batidas('batida')
        self.js, _ = jatos_de([b for k, b in enumerate(bs) if k % 8 == 0], .9)

    def casa(self, tela, x, yb, e):
        w, h = 9 * e, 6 * e
        pts = [(x - w / 2 - e * .6, yb - h), (x, yb - h - 3.5 * e), (x + w / 2 + e * .6, yb - h)]
        contorno(tela, pts, PRETO); pol(tela, pts, D.VERM[2])
        tela.ret(x - w / 2 - 1, yb - h - 1, w + 2, h + 2, PRETO)
        dither(tela, x - w / 2, yb - h, w, h, CERAMICA, ACO4)
        for j in (-1, 1):
            tela.ret(x + j * w * .25 - e * .6, yb - h * .75, e * 1.2, e * 1.2, FUNDO2)
            tela.ret(x + j * w * .25 - e * .6, yb - h * .4, e * 1.2, e * 1.2, FUNDO2)
        tela.ret(x - e * .5, yb - e * 2, e, e * 2, OLEO0)

    def desenhar(self, tela, t, tg):
        bx = 100
        PAIS.desenhar(tela, 0, 0, t, PX0 - 8)
        e = PAIS.ppm
        self.casa(tela, 228, PAIS.y_cesto(), e)
        ch = chama_de(self.js, t)
        cheio = 14.6 <= t < 21.6
        m = D.balao(tela, bx, MY, K, t, dict(chama=ch, corte=1.0 if cheio else 0.0, quente=1.0))
        if cheio:
            nivel = MY - 100 * K * suave((t - 14.6) / 6.0)
            g = e
            ys, xs = np.nonzero(m)
            sel = (ys >= nivel) & (ys < MY - 1)
            ys, xs = ys[sel], xs[sel]
            linha = (((ys - MY) % g) < 1) | (((xs - bx) % g) < 1)
            tela.buf[ys[linha], xs[linha]] = LARANJA
        if t < 7.6:
            cx, cy = bx + 30, PAIS.y_cesto() - e
            tela.ret(cx - 1, cy - e - 1, e + 2, e + 2, PRETO)
            tela.ret(cx, cy - e, e, e, AMARELO)
            rotulo(tela, '1 METRO CÚBICO', cx + 22, 150, cx + e / 2, cy - e)
        if 21.6 <= t < 28.6:
            xr = bx - 70
            yt, yb2 = MY - 100 * K, MY
            tela.ret(xr, yt, 1, yb2 - yt, AMARELO)
            tela.ret(xr - 3, yt, 7, 1, AMARELO); tela.ret(xr - 3, yb2, 7, 1, AMARELO)
            etiqueta(tela, f"{dec(D.ALTURA_M, 1)} M", xr, (yt + yb2) / 2 - 4, AMARELO)
            rotulo(tela, 'CASA', 250, 138, 232, PAIS.y_cesto() - 6 * e)
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'A CONTA DO BALÃO', 9, ACO3, 9)
        if t < 14.6:
            # o cubo de 1 metro levanta 0,26 kg; 3,9 cubos levantam 1 kg
            n = 1 if t < 7.6 else 4
            for j in range(n):
                x = PX0 + 8 + j * 30
                y = 40
                tela.ret(x - 1, y - 1, 24, 24, PRETO)
                tela.ret(x, y, 22, 22, LARANJA if j < 3 or t >= 7.6 else LARANJA)
                tela.ret(x, y, 22, 2, CHAMA1)
                tela.ret(x + 20, y, 2, 22, BRASA)
                if j == 3:
                    tela.ret(x + 20 - int(22 * .1), y, int(22 * .1) + 2, 22, FUNDO)
            if t < 7.6:
                tit(tela, '1 METRO CÚBICO A 99 °C', 72, BRANCO, 9)
                tit(tela, 'LEVANTA', 88, ACO3, 9)
                tit(tela, '0,26 KG', 98, AMARELO, 17)
            else:
                tit(tela, '3,9 METROS CÚBICOS', 72, BRANCO, 9)
                tit(tela, 'LEVANTAM', 88, ACO3, 9)
                tit(tela, '1 KG', 98, AMARELO, 17)
        elif t < 21.6:
            f = suave((t - 14.6) / 6.0)
            tit(tela, 'METROS CÚBICOS', 30, ACO3, 9)
            tit(tela, milhar(2800 * f), 40, LARANJA, 17)
            tit(tela, 'LEVANTA', 66, ACO3, 9)
            tit(tela, f"{milhar(723.5 * f)} KG", 76, AMARELO, 17)
            barra(tela, PX0, 100, 156, 8, f, LARANJA)
        elif t < 28.6:
            tit(tela, '2.800 METROS CÚBICOS', 30, LARANJA, 9)
            tit(tela, 'ALTURA', 50, ACO3, 9)
            tit(tela, f"~{dec(D.ALTURA_M, 1)} M", 60, AMARELO, 17)
            tit(tela, 'LARGURA', 84, ACO3, 9)
            tit(tela, f"~{dec(D.LARGURA_M, 1)} M", 94, AMARELO, 17)
            tit(tela, 'LEVA DE 3 A 5 PESSOAS', 122, BRANCO, 9)
        else:
            tit(tela, 'AR DENTRO E O QUE LEVANTA', 30, ACO3, 9)
            u = suave((t - 28.6) / 3)
            for j, (T, kg) in enumerate(((99, 723.5), (120, 867.3))):
                y = 48 + j * 30
                tit(tela, f"{T} °C", y, temp_cor(T), 17)
                if j == 0 or u > .5:
                    tela.texto(f"{milhar(kg)} KG", W - 12, y + 4, AMARELO, tam=9, centro='d', contorno=PRETO)
            T = 99 + 21 * u
            barra(tela, PX0, 112, 156, 8, (T - 20) / 110, temp_cor(T))
            tela.ret(PX0 + int(156 * 100 / 110), 108, 1, 16, VERMELHO)
            tit(tela, 'LIMITE ~120 °C', 130, VERMELHO, 9)
            tit(tela, 'O NÁILON ENFRAQUECE', 144, BRANCO, 9)

    def sons(self, fx):
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .05)
        for a in (7.6, 14.6, 21.6, 28.6):
            fx.put(fx.blip(74, .1), self.t0 + a, .1)


# ============================================================ partes
PECAS = [('ENVELOPE', 'NÁILON QUE AGUENTA CALOR', (40, -32), 'env'),
         ('PARAQUEDAS', 'TAMPA NO TOPO', (5, 0), 'par'),
         ('SAIA', 'TECIDO QUE RESISTE AO FOGO', (103, -9.6), 'saia'),
         ('QUEIMADOR', 'CHAMA DE PROPANO', (112.5, -3), 'queimador'),
         ('BOTIJÕES', 'GÁS PROPANO', (121, -2), 'botijoes'),
         ('CESTO', 'VIME TRANÇADO', (122, 5.4), 'cesto')]


class Partes(Cena):
    TS = [0.3, 8.3, 16.3, 24.3, 32.3, 40.3]
    KP = 1.42

    def preparar(self):
        bs = self.batidas('batida')
        self.js, _ = jatos_de([b for k, b in enumerate(bs) if (24.3 <= b < 32 and k % 2 == 0) or k % 16 == 0], .6)

    def ativo(self, t):
        return max([k for k, a in enumerate(self.TS) if t >= a] or [0])

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        o = int(t * 4) % 24
        for x in range(-o, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(6, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        k_at = self.ativo(t)
        nome, sub, (s, u), chave = PECAS[k_at]
        k = self.KP
        cx = 140 if not VERTICAL else x_corte('partes') + 90
        my = 12 + 100 * k
        vent = 0.0
        if chave == 'par':
            vent = .7 * max(0.0, math.sin((t - 8.3) * 1.2)) ** 2 if t > 9 else 0.0
        ch = chama_de(self.js, t)
        D.balao(tela, cx, my, k, t, dict(chama=ch, vent=vent, corte_cesto=(chave in ('botijoes', 'cesto')),
                                         acesos=(chave,)))
        if vent > .05: ar_quente_saindo(tela, t, cx, my, k, vent)
        ax, ay = D.pt(cx, my, k, s, u)
        if chave == 'env':
            pts = [D.pt(cx, my, k, ss, -D.r_env(np.array([ss]))[0] - 1.5) for ss in range(2, 100, 4)]
            if int(t * 4) % 2 == 0:
                for a, b in zip(pts, pts[1:]): tela.linha(a[0], a[1], b[0], b[1], AMARELO)
        if VERTICAL:
            etiqueta(tela, nome, cx, 6, AMARELO, 9)
            return
        fundo_painel(tela)
        for j, (n, sb, _, _) in enumerate(PECAS):
            y = 10 + j * 27
            cor = ACO1 if j > k_at else (AMARELO if j == k_at else ACO3)
            tela.ret(PX0, y + 1, 5, 5, cor)
            tela.texto(n, PX0 + 9, y, cor, tam=9, contorno=PRETO)
            if j == k_at:
                tela.texto(sb, PX0 + 9, y + 11, BRANCO, tam=9, contorno=PRETO)
                yy = y + 3
                tela.linha(PX0 - 2, yy, PX0 - 10, yy, AMARELO)
                tela.linha(PX0 - 10, yy, ax + (8 if ax < PX0 - 10 else 0), ay, AMARELO)
                tela.disco(ax, ay, 2, AMARELO)
        tela.texto(f"PEÇA {k_at + 1} DE 6", PX0 + 2, 186, ACO3, tam=9)
        for j in range(6):
            tela.ret(PX0 + 96 + j * 10, 187, 8, 5, AMARELO if j <= k_at else ACO0)

    def sons(self, fx):
        for k, a in enumerate(self.TS):
            fx.put(fx.blip(72 + k, .08), self.t0 + a, .12)
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .05)
        fx.put(sopro(5.0), self.t0 + 9.5, .02)


# ============================================================ enchendo
class Inflar(Cena):
    T_QUEIMA, T_LEV0, T_LEV1 = 9.0, 14.6, 23.0

    def preparar(self):
        bs = self.batidas('batida')
        self.js, _ = jatos_de([b for k, b in enumerate(bs) if self.T_QUEIMA <= b < self.T_LEV1 + 3 and k % 2 == 0]
                              + [b for k, b in enumerate(bs) if b >= self.T_LEV1 + 3 and k % 8 == 0], .9)

    def fill(self, t):
        return rampa(t, [(0, .08), (self.T_QUEIMA, .6), (self.T_LEV0, .95), (self.T_LEV1, 1.0)])

    def ang(self, t):
        return (-math.pi / 2 + .08) * (1 - suave((t - self.T_LEV0) / (self.T_LEV1 - self.T_LEV0)))

    def boca(self, t, k, xb):
        """Boca posta de modo que o canto mais baixo do cesto toque o chão em x = xb."""
        a = self.ang(t)
        cs = D.extremos_cesto(k, a)
        dy = max(c[1] for c in cs)
        dx = sum(c[0] for c in cs) / 4
        return xb - dx, PAIS.y_cesto() - dy, a

    def desenhar(self, tela, t, tg):
        x1 = W if VERTICAL else PX0 - 8
        PAIS.desenhar(tela, 0, 0, t, x1)
        ch = chama_de(self.js, t)
        xb = 236 if not VERTICAL else x_corte('inflar') + 140
        mx, my, a = self.boca(t, K, xb)
        f = self.fill(t)
        chao = int(PAIS.y_cesto()) + 1
        if a > -.02:
            D.balao(tela, mx, my, K, t, dict(chama=ch))
        else:
            D.envelope(tela, mx, my, K, t, ang=a, fill=f, chama=ch, chao=chao)
            D.cesto_girado(tela, mx, my, K, a, t, chama_f=ch)
        # a ventoinha
        vent_on = t < self.T_LEV0 + 1
        fx_, fy = xb + 30, PAIS.y_cesto() - 12
        tela.ret(fx_ - 2, fy + 6, 4, 6, ACO1)
        tela.ret(fx_ - 8, fy + 11, 16, 2, ACO0)
        tela.disco(fx_, fy, 11, PRETO)
        tela.disco(fx_, fy, 10, ACO1)
        tela.anel(fx_, fy, 9, ACO3, .6)
        rot = t * 14 if vent_on else 0
        for j in range(4):
            aa = rot + j * math.pi / 2
            tela.linha(fx_, fy, fx_ + math.cos(aa) * 8, fy + math.sin(aa) * 8, ACO4)
        tela.disco(fx_, fy, 2, ACO2)
        if vent_on and a < -1.2:
            for i in range(9):
                uu = (t * 1.3 + i / 9) % 1
                x = fx_ - 14 - uu * (fx_ - 14 - mx)
                y = fy - 6 + (hsh(i, 2) - .5) * 16 * (1 - uu) + (my - fy + 6) * uu * .6
                tela.ret(x, y, 4, 1, CIANO if i % 2 else BRANCO)
        hud_v(tela, 'inflar', [(f"CHEIO {milhar(f * 100)}%", CIANO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'ENCHENDO', 9, ACO3, 9)
        tit(tela, 'ENVELOPE CHEIO', 26, ACO3, 9)
        tit(tela, f"{milhar(f * 100)}%", 36, CIANO, 17)
        barra(tela, PX0, 58, 156, 6, f, CIANO)
        T = rampa(t, [(0, 20), (self.T_QUEIMA, 20), (self.T_LEV1, 85), (30, 92)])
        tit(tela, 'AR DENTRO', 76, ACO3, 9)
        tit(tela, f"{milhar(T)} °C", 86, temp_cor(T), 17)
        barra(tela, PX0, 108, 156, 6, (T - 20) / 100, temp_cor(T))
        etapas = [('1. VENTOINHA: AR FRIO', 0), ('2. QUEIMADOR ACENDE', self.T_QUEIMA),
                  ('3. O ENVELOPE SOBE', self.T_LEV0), ('4. CESTO DE PÉ', self.T_LEV1)]
        for j, (txt, a0) in enumerate(etapas):
            ativo = t >= a0 and (j == 3 or t < etapas[j + 1][1])
            cor = AMARELO if ativo else (ACO3 if t >= a0 else ACO0)
            tela.texto(txt, PX0, 128 + j * 14, cor, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(zumbido(self.T_LEV0 + 1, 70), self.t0, .025)
        fx.put(sopro(self.T_LEV0 + 1, 300, 1200), self.t0, .015)
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .06)
        fx.put(baque(60, .5), self.t0 + self.T_LEV1, .08)


# ============================================================ subir
class Subir(Cena):
    def preparar(self):
        bs = self.batidas('batida')

        def plano(k):
            bar, bt = k // 4, k % 4
            if bar < 7: return bt in (0, 1, 2)
            if bar < 10: return bt in (0, 1)
            return bt == 0
        self.js, f = jatos_de([b for k, b in enumerate(bs) if plano(k)], .7)
        self.voo = D.Voo(self.dur + 1, f, lambda t: 0.0, h0=0.0, v0=0.0, Tin0=273.15 + 95.5)
        self.t_dec = next(float(r[0]) for r in self.voo.a if r[1] > .05)

    def desenhar(self, tela, t, tg):
        q = self.voo.q(t)
        q['chama'] = chama_de(self.js, t)
        x1 = W
        cena_voo(tela, t, q['h'], .6 * t, dict(chama=q['chama']), x1=x1)
        if t < self.t_dec + 2.5 and t > self.t_dec - .3 and not VERTICAL:
            tela.texto('DECOLOU!', CX, 14, AMARELO, tam=17, centro=True, contorno=PRETO)
        hud_voo(tela, 'subir', q)
        if VERTICAL: return
        painel_voo(tela, q)

    def sons(self, fx):
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .07)
        fx.put(tique(1600, .05), self.t0 + self.t_dec, .1)


# ============================================================ descer
class Descer(Cena):
    R = 1.5
    H0 = 63.0
    V0, V1 = 14.6, 22.0                 # paraquedas aberto (vídeo)
    PILOTO = 21.0

    def preparar(self):
        R = self.R
        bs = [b * R for b in self.batidas('batida')]
        st = dict(ate=-1.0, jatos=[])

        def queim(tf, h, v, Tin):
            if tf < st['ate']: return 1.0
            if tf < self.PILOTO * R or h <= .05: return 0.0
            L = D.empuxo_kg(Tin, h); Ta, rho = D.ar_fora(h); m_in = D.VOLUME * rho * Ta / Tin
            a = ((L - PESO) * 9.81 - .5 * rho * D.Voo.CDA * v * abs(v)) / (PESO + m_in)
            alvo = -2.2 if h > 45 else -(.5 + h * .035)
            for b in bs:
                if abs(tf - b) < .026 and v + a * 8 < alvo:
                    st['ate'] = b + 1.5 * R
                    st['jatos'].append((b / R, b / R + 1.5))
                    return 1.0
            return 0.0

        a0, a1 = self.V0 * R, self.V1 * R

        def vent(tf):
            return .3 * min(1, max(0, (tf - a0) / 1.5)) * min(1, max(0, (a1 - tf) / 1.5))
        Ta, rho = D.ar_fora(self.H0)
        Teq = Ta / (1 - PESO / (D.VOLUME * rho))
        self.voo = D.Voo(self.dur * R + 1, queim, vent, h0=self.H0, v0=0.0, Tin0=Teq + .3, travar=True)
        self.js = st['jatos']
        self.t_pouso = next((float(r[0]) / R for r in self.voo.a if r[0] > 1 and r[1] <= 0), self.dur)

    def desenhar(self, tela, t, tg):
        q = self.voo.q(t * self.R)
        q['chama'] = chama_de(self.js, t)
        vis_vent = q['vent'] / .3
        if t > self.t_pouso + 1.0:
            vis_vent = min(1.0, (t - self.t_pouso - 1.0) / 2)        # pousou: abre tudo para esvaziar
            q['vent'] = .3
        cena_voo(tela, t, q['h'], .9 * t, dict(chama=q['chama'], vent=vis_vent))
        if vis_vent > .05:
            ar_quente_saindo(tela, t, CX, MY, K, vis_vent)
            # a corda do paraquedas: do cesto até o topo
            a = D.pt(CX, MY, K, D.S_CESTO, 1); b = D.pt(CX, MY, K, 12, 2)
            tela.linha(a[0], a[1], b[0], b[1], CIANO)
        if 0 <= t - self.t_pouso < 2.5 and not VERTICAL:
            tela.texto('POUSOU!', CX, 14, AMARELO, tam=17, centro=True, contorno=PRETO)
        hud_voo(tela, 'descer', q)
        if VERTICAL: return
        painel_voo(tela, q, (f"ACELERADO {dec(self.R, 1)}X", LARANJA))
        if t < 3.5:
            tela.texto('MAIS TARDE...', W - 10, 196 - 6, ACO3, tam=9, centro='d', contorno=PRETO)

    def sons(self, fx):
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .07)
        fx.put(sopro(self.V1 - self.V0, 700, 2600), self.t0 + self.V0, .025)
        fx.put(baque(55, .6), self.t0 + self.t_pouso, .1)
        fx.put(sopro(self.dur - self.t_pouso - 1, 700, 2600), self.t0 + self.t_pouso + 1, .02)


# ============================================================ vento
class Vento(Cena):
    R = 20.0                     # acelerado 20x
    MPX = 15.0                   # metros por pixel no mapa
    Y0, HMAX, ALT = 184, 900.0, 170.0

    @staticmethod
    def vento(h):
        """Exemplo de camadas: embaixo para a direita (+), em cima para a esquerda (-)."""
        if h <= 280: return 6.0
        if h >= 520: return -7.0
        return 6.0 + (h - 280) / 240 * -13.0

    def preparar(self):
        marcos = [(0, 0), (6, 0), (130, 250), (380, 250), (520, 700), (820, 700), (1010, 0)]
        tf = np.arange(0, self.dur * self.R + 1, .5)
        hs = np.array([self._h(x, marcos) for x in tf])
        xs = np.concatenate([[0], np.cumsum([self.vento(h) * .5 for h in hs[:-1]])])
        xs = np.where(hs <= 0.01, np.where(tf > 500, xs, 0), xs)
        pouso = next(i for i in range(len(tf)) if tf[i] > 500 and hs[i] <= .01)
        xs[pouso:] = xs[pouso]
        self.tf, self.hs, self.xs = tf, hs, xs
        self.t_pouso = tf[pouso] / self.R
        lo, hi = xs.min() / self.MPX, xs.max() / self.MPX
        self.x0 = 150 - (lo + hi) / 2
        self.x_alvo = self.x0 + xs[pouso] / self.MPX
        bs = self.batidas('batida')
        sobe = []
        for b in bs:
            i = int(b * self.R / .5)
            if i + 2 < len(hs) and hs[i + 2] > hs[i] + .5: sobe.append(b)
        self.js, _ = jatos_de(sobe[::2], .6)

    @staticmethod
    def _h(t, marcos):
        for (a, x), (b, y) in zip(marcos, marcos[1:]):
            if t <= b: return x + (y - x) * suave((t - a) / (b - a))
        return marcos[-1][1]

    def y_de(self, h): return self.Y0 - h / self.HMAX * self.ALT

    def estado(self, t):
        tf = min(t * self.R, self.tf[-1])
        h = float(np.interp(tf, self.tf, self.hs)); x = float(np.interp(tf, self.tf, self.xs))
        return tf, h, x

    def desenhar(self, tela, t, tg):
        x1 = W if VERTICAL else PX0 - 8
        gradiente(tela, 0, 0, x1, self.Y0, [(0, CEU0), (.6, CEU1), (.9, CEU2), (1, CEU3)])
        # camadas de vento
        camadas = [(0, 280, 6.0, VERDE, 'VENTO PARA A DIREITA'), (520, 900, -7.0, CIANO, 'VENTO PARA A ESQUERDA')]
        for h0, h1, v, cor, nome in camadas:
            ya, yb = self.y_de(h1), self.y_de(h0)
            for y in range(int(ya), int(yb), 2):
                for x in range(0, x1, 2):
                    if (x + y) % 8 == 0: tela.px(x, y, CEU2 if v > 0 else CEU1)
            for i in range(26):
                yy = ya + 6 + (hsh(i, 1)) * (yb - ya - 12)
                xx = (hsh(i, 2) * (x1 + 40) + t * v * 4 * (.8 + .4 * hsh(i, 3))) % (x1 + 40) - 20
                L = 8
                tela.ret(xx - (L if v > 0 else 0), yy, L, 1, BRANCO if i % 3 else cor)
                if v > 0: tela.px(xx, yy - 1, BRANCO); tela.px(xx, yy + 1, BRANCO)
                else: tela.px(xx - L, yy - 1, BRANCO); tela.px(xx - L, yy + 1, BRANCO)
            tela.ret(0, ya, x1, 1, cor)
            tela.texto(nome, 8, ya + 4, cor, tam=9, contorno=PRETO)
        tela.texto('QUASE SEM VENTO', 8, self.y_de(430), ACO4, tam=9, contorno=PRETO)
        # chão
        dither(tela, 0, self.Y0, x1, PALCO_H - self.Y0, CAMPO1, CAMPO2)
        tela.ret(0, self.Y0, x1, 1, CAMPO0)
        for i in range(30):
            x = hsh(i, 5) * x1
            tela.disco(x, self.Y0 - 1, 2 + hsh(i, 6) * 2, CAMPO0)
        # escala de altitude
        if not VERTICAL:
            for a in range(0, 901, 300):
                y = self.y_de(a)
                tela.ret(x1 - 30, y, 6, 1, BRANCO)
                tela.texto(f"{a} M", x1 - 4, y - 3, BRANCO, tam=9, centro='d', contorno=PRETO)
        # alvo (campo de pouso)
        xa = self.x_alvo
        tela.ret(xa - 14, self.Y0 + 3, 28, 6, CAMPO3)
        tela.linha(xa - 4, self.Y0 + 3, xa + 4, self.Y0 + 8, VERMELHO)
        tela.linha(xa + 4, self.Y0 + 3, xa - 4, self.Y0 + 8, VERMELHO)
        tela.texto('POUSO', xa, self.Y0 + 12, BRANCO, tam=9, centro=True, contorno=PRETO)
        # o caminho
        tf, h, x = self.estado(t)
        xs_px = self.x0 + self.xs / self.MPX
        n = int(tf / .5)
        for i in range(0, n, 6):
            tela.px(xs_px[i], self.y_de(self.hs[i]) - 2, AMARELO)
        # o balão (fora de escala)
        k = .34
        bx = self.x0 + x / self.MPX
        by = self.y_de(h)
        my = by - (D.S_FUNDO - 100) * k
        ch = chama_de(self.js, t)
        D.balao(tela, bx, my, k, t, dict(chama=ch))
        hud_v(tela, 'vento', [(f"ALTITUDE {milhar(h)} M", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'VISTA DE LADO', 9, ACO3, 9)
        tela.texto('ACELERADO 20X', W - 10, 9, LARANJA, tam=9, centro='d', contorno=PRETO)
        tit(tela, 'ALTITUDE', 26, ACO3, 9)
        tit(tela, f"{milhar(h)} M", 36, AMARELO, 17)
        v = self.vento(h)
        tit(tela, 'VENTO NA ALTURA DO BALÃO', 62, ACO3, 9)
        cor = VERDE if v > 1 else (CIANO if v < -1 else ACO3)
        tit(tela, f"{milhar(abs(v) * 3.6)} KM/H", 72, cor, 17)
        xa0 = PX0 + 120
        if v > 1: seta(tela, xa0, 80, xa0 + 30, 80, cor, 4, 6)
        elif v < -1: seta(tela, xa0 + 30, 80, xa0, 80, cor, 4, 6)
        tit(tela, 'O PILOTO SÓ ESCOLHE', 104, BRANCO, 9)
        tit(tela, 'A ALTURA', 116, BRANCO, 9)
        dist = (x - 0) / 1000
        tit(tela, 'DISTÂNCIA DA DECOLAGEM', 140, ACO3, 9)
        tit(tela, f"{dec(abs(dist), 1)} KM", 150, BRANCO, 17)
        if t >= self.t_pouso:
            tit(tela, 'POUSOU!', 178, AMARELO, 9)

    def sons(self, fx):
        for a, b in self.js:
            fx.put(jato_som(b - a), self.t0 + a, .05)
        fx.put(baque(60, .5), self.t0 + self.t_pouso, .08)


# ============================================================ história
class Historia(Cena):
    def desenhar(self, tela, t, tg):
        x1 = W
        if t < 21.6:
            self.lisboa(tela, t)
            card, ano = '8 DE AGOSTO DE 1709 - LISBOA', 0
        elif t < 35.6:
            self.franca(tela, t - 21.6)
            card, ano = '1783 - FRANÇA', 1
        else:
            PAIS.desenhar(tela, 80, 3 * t, t, x1)
            D.balao(tela, 240 if not VERTICAL else 150, MY - 10, K * .8, t, dict(chama=1.0 if (t % 3) < .7 else 0))
            card, ano = 'HOJE', 2
        # linha do tempo embaixo
        y = 196
        painel(tela, 6, y - 8, W - 12, 14, borda=TRACO)
        xs = [60, 250, 420]
        tela.ret(xs[0], y - 1, xs[2] - xs[0], 1, ACO2)
        for j, (x, n) in enumerate(zip(xs, ('1709', '1783', 'HOJE'))):
            cor = AMARELO if j == ano else ACO2
            tela.disco(x, y - 1, 3, cor)
            tela.texto(n, x + 6, y - 5, cor, tam=9, contorno=PRETO)
        etiqueta(tela, card, W // 2, 8, AMARELO)

    def lisboa(self, tela, t):
        # uma sala: paredes, arcos, piso xadrez (genérico, sem pessoas)
        tela.buf[:PALCO_H] = FUNDO2
        dither(tela, 0, 30, W, 120, CERAMICA, ACO4)
        tela.ret(0, 26, W, 6, OLEO0)
        tela.ret(0, 30, W, 1, LATAO)
        for x in range(40, W, 100):
            tela.ret(x - 20, 60, 40, 80, FUNDO3)
            tela.disco(x, 60, 20, FUNDO3)
            dither(tela, x - 16, 62, 32, 76, CEU2, CEU3)
            tela.disco(x, 62, 16, CEU3)
            tela.ret(x - 1, 46, 2, 94, OLEO0)
            tela.ret(x - 16, 98, 32, 2, OLEO0)
        for j in range(8):
            yy = 150 + j * 7
            for i in range(-2, 34):
                xx = i * 16 + (j % 2) * 8 - j * 2
                tela.ret(xx, yy, 8, 7, ACO3 if (i + j) % 2 else ACO1)
        tela.ret(0, 150, W, 1, PRETO)
        # o balãozinho: sobe até o teto
        cx = 210 if not VERTICAL else x_corte('historia') + 90
        u = suave((t - 1.5) / 10)
        y = 140 - u * (140 - 46) + (math.sin(t * 6) * 1.5 if u >= .99 else 0)
        tela.disco(cx, y - 14, 13, PRETO)
        tela.disco(cx, y - 14, 12, CERAMICA)
        tela.disco(cx - 4, y - 18, 5, BRANCO)
        dither(tela, cx - 11, y - 10, 22, 6, CERAMICA, ACO3)
        tela.linha(cx - 9, y - 6, cx - 4, y + 4, ACO1)
        tela.linha(cx + 9, y - 6, cx + 4, y + 4, ACO1)
        tela.ret(cx - 5, y + 4, 10, 3, LATAO)
        D.chama(tela, cx, y + 4, .35, 1.0, t, 4)
        if u < .05:
            tela.ret(cx - 18, 146, 36, 4, OLEO0)

    def franca(self, tela, t):
        PAIS.ceu(tela, 0, t + 21.6, W)
        dither(tela, 0, PAIS.hy, W, PALCO_H - PAIS.hy, CAMPO1, CAMPO2)
        # vila genérica ao longe
        for i in range(14):
            x = 10 + i * 34
            hh = 10 + hsh(i, 7) * 10
            tela.ret(x, PAIS.hy - hh + 4, 22, hh, MORRO0)
            pol(tela, [(x - 2, PAIS.hy - hh + 4), (x + 11, PAIS.hy - hh - 6), (x + 24, PAIS.hy - hh + 4)], MORRO1)
        cx = 210 if not VERTICAL else x_corte('historia') + 90
        sobe = suave((t - 1) / 12)
        y = 150 - sobe * 55
        # balão redondo, azul com enfeites dourados (desenho genérico)
        R = 36
        tela.disco(cx, y - R, R + 1, PRETO)
        tela.disco(cx, y - R, R, D.AZUL[1])
        tela.disco(cx - 9, y - R - 10, R * .55, D.AZUL[0])
        dither(tela, cx + 10, y - R - 20, 24, 40, D.AZUL[1], D.AZUL[2])
        for j in range(-3, 4):
            tela.disco(cx + j * 9, y - R + 4 + abs(j) * 1.5, 2, AMARELO)
        tela.anel(cx, y - R, R - 6, LATAO, .5)
        pol(tela, [(cx - 16, y - 6), (cx + 16, y - 6), (cx + 10, y + 6), (cx - 10, y + 6)], D.AZUL[2])
        tela.ret(cx - 10, y + 6, 20, 4, OLEO0)
        D.chama(tela, cx, y + 5, .55, .8, t, 5)
        if t >= 7.0:
            etiqueta(tela, '21/11/1783: PRIMEIRO VOO LIVRE', W // 2, 168, BRANCO)

    def sons(self, fx):
        fx.put(fx.blip(72, .1), self.t0 + .5, .12)
        fx.put(fx.blip(76, .1), self.t0 + 21.6, .12)
        fx.put(fx.blip(79, .1), self.t0 + 35.6, .12)
        fx.put(baque(90, .25), self.t0 + 11.5, .05)


# ============================================================ resumo
class Resumo(Cena):
    CX = [64, 178, 292, 406]
    NOMES = [('AR QUENTE', 'MENOS DENSO'), ('EMPUXO', 'AR FRIO EMPURRA'), ('QUEIMADOR SOBE', 'ESFRIAR DESCE'),
             ('CAMADAS', 'DE VENTO')]
    TS = [0.5, 7.3, 14.3, 21.3, 28.3]

    def desenhar(self, tela, t, tg):
        gradiente(tela, 0, 0, W, PALCO_H, [(0, CEU0), (.7, CEU1), (1, CEU2)])
        k_at = max([k for k, a in enumerate(self.TS) if t >= a] or [0])
        lei = k_at == 4
        for k in range(4):
            cx = self.CX[k]
            if VERTICAL and k != min(k_at, 3): continue
            if VERTICAL: cx = x_corte('resumo') + 90
            aceso = k == k_at
            cor = AMARELO if aceso else ACO1
            painel(tela, cx - 52, 18, 104, 150, borda=cor)
            self._icone(tela, k, cx, 74, t, aceso)
            tela.texto(self.NOMES[k][0], cx, 134, AMARELO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(self.NOMES[k][1], cx, 148, BRANCO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(str(k + 1), cx - 44, 24, cor, tam=9)
        if lei:
            for yy in range(0, PALCO_H):
                tela.buf[yy, (yy % 2)::2] = PRETO
            u = suave((t - 28.3) / .5)
            w, h = 330, 92
            x0, y0 = W // 2 - w // 2, 40 + int((1 - u) * 160)
            painel(tela, x0, y0, w, h, borda=VERMELHO)
            tela.texto('LEI 9.605/1998, ART. 42', W // 2, y0 + 10, VERMELHO, tam=17, centro=True, contorno=PRETO)
            tela.texto('FABRICAR, VENDER, TRANSPORTAR OU SOLTAR', W // 2, y0 + 40, BRANCO, tam=9, centro=True,
                       contorno=PRETO)
            tela.texto('BALÕES QUE POSSAM PROVOCAR INCÊNDIOS', W // 2, y0 + 54, BRANCO, tam=9, centro=True,
                       contorno=PRETO)
            tela.texto('É CRIME.', W // 2, y0 + 70, AMARELO, tam=9, centro=True, contorno=PRETO)

    def _icone(self, tela, k, cx, cy, t, aceso):
        x0, y0, w, h = cx - 44, cy - 46, 88, 92
        dither(tela, x0, y0, w, h, FUNDO2, FUNDO)
        if k == 0:
            for j, (cor, vel, n) in enumerate(((CIANO, .2, 14), (LARANJA, .45, 10))):
                bx = x0 + 6 + j * 42
                tela.ret(bx - 1, y0 + 19, 38, 52, PRETO)
                tela.ret(bx, y0 + 20, 36, 50, FUNDO3)
                p = Particulas(n, 40 + j).pos(t * vel if aceso else 1.0)
                for i in range(n):
                    tela.ret(bx + 2 + p[i, 0] * 31, y0 + 22 + p[i, 1] * 45, 2, 2, cor)
        elif k == 1:
            yy = cy + 34 - ((t * 6) % 10 if aceso else 0)
            D.balao(tela, cx, yy - 24 * .45, .45, t, dict(chama=1.0 if aceso and (t % 1.5) < .5 else 0))
            seta(tela, cx + 32, cy + 24, cx + 32, cy - 16, VERDE, 3, 5)
        elif k == 2:
            u = .5 + .5 * math.sin(t * 1.5) if aceso else .5
            D.balao(tela, cx, cy + 12, .45, t, dict(chama=1.0 if u > .6 else 0.0, vent=.8 if u < .3 else 0.0))
        else:
            for j, (v, cor) in enumerate(((-1, CIANO), (1, VERDE))):
                y = cy - 22 + j * 40
                xo = ((t * 12) % 20) if aceso else 0
                for i in range(4):
                    x = x0 + 8 + ((i * 22 + xo * v) % 80)
                    tela.ret(x, y, 10, 1, cor)
                    tela.px(x + (10 if v > 0 else -1), y - 1, cor); tela.px(x + (10 if v > 0 else -1), y + 1, cor)
            D.balao(tela, cx, cy + 4 + (math.sin(t) * 16 if aceso else 0) - 11, .22, t, dict(chama=0.0))

    def sons(self, fx):
        for k, ta in enumerate(self.TS):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + ta, .14)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            PAIS.ceu(tela, 0, t, W)
            PAIS.chao(tela, 300, 10 * t, t, W)
            u = t - RM.OUTRO_S
            x = -40 + u * 40
            D.balao(tela, x, 150 + math.sin(t) * 3, .7, t, dict(chama=1.0 if (t % 3) < .6 else 0))
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 30, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 52, AMARELO, tam=9, centro=True, contorno=PRETO)

    def fim_vinheta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# longo.py chama `pos` (RGB pronto) quando a cena tem esse método: só o Fim usa.
Fim.pos = Fim.fim_vinheta

CENAS = dict(gancho=Gancho, titulo=Titulo, particulas=Particulas_, empuxo=Empuxo, conta=Conta, partes=Partes,
             inflar=Inflar, subir=Subir, descer=Descer, vento=Vento, historia=Historia, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep22_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if len(sys.argv) > 3:
            c = next(c for c in trilha.caps if c['id'] == sys.argv[3])
            fr = [float(x) for x in sys.argv[4:]] or [float(x) for x in os.environ.get('FR', '.1,.3,.5,.7,.9').split(',')]
            ts = [c['t0'] + c['dur'] * f for f in fr]
        else:
            fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
            for c in trilha.caps:
                ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
