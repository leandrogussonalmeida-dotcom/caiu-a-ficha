#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep25 — Como funciona o motor a jato (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (ronco grave e baixo, tiques), nos
                          mesmos instantes do desenho

O ar manda no desenho: a posição do nosso pedacinho de ar (x, em unidades do
motor) é uma função do tempo por capítulo, e o painel lê o MESMO x no modelo
(`ep25_desenho.MOD`): pressão sobe no compressor, fica na câmara, cai na
turbina e no bocal; a temperatura também. Os 13 estágios do compressor acendem
nos compassos da música (house a 120 bpm) e os 4 tempos caem nas batidas.

    python3 ep25_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep25_motor.py <saida.mp4> compressor bocal    # só esses capítulos (teste)
    python3 ep25_motor.py --folha <saida.png>             # 2 quadros por capítulo (FR=.3,.8)
    python3 ep25_motor.py --folha <saida.png> compressor  # 5 quadros (FR=.1,.3,.5,.7,.9)
"""
import math, os, sys
import numpy as np
import longo as LG
import ep25_desenho as D          # registra a paleta do episódio (LG.PAL = 'ep25')
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep25_desenho import (MOD, TEMPOS, Turbofan, Camera, Aviao, parcela, cor_calor, escala_calor, ceu_dia,
                          pa_corte, pol, contorno, brilho, gradiente, seta_forca, barra, hsh, milhar, dec,
                          CEU0, CEU1, CEU2, CEU3, CEU4, CEU5, GRAMA0, GRAMA1, CONCRETO, ASFALTO,
                          CASCO, CASCO2, CASCO3, FRIO0, FRIO1, Q4, Q6)
import motor_pixel as MP
import ritmo_marca as RM
import quizaudio as QA
import pixelengine as PX
from ep25_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2625, 45
GANHO_MUSICA = -10.0          # trilha baixa: o texto manda; o ronco fica por baixo da música
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
SR = LG.SR
TF = Turbofan()
AV = Aviao()
NOMES_CARRO = ['ADMISSÃO', 'COMPRESSÃO', 'COMBUSTÃO', 'ESCAPE']


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


def rotulo(tela, txt, x, y, ax, ay, cor=AMARELO, direita=False, tam=9):
    """Rótulo com fio até a peça (ax, ay) e bolinha na ponta."""
    w = tela.largura_texto(txt, tam)
    hh = 7 if tam < 14 else 14
    tx = x - w if direita else x
    painel(tela, tx - 3, y - 3, w + 6, hh + 6, borda=cor)
    tela.texto(txt, tx, y, cor, tam=tam)
    lx = (tx - 3) if ax < tx else (tx + w + 3)
    if tx - 3 <= ax <= tx + w + 3: lx = ax
    ly = y + hh // 2 if not (tx - 3 <= ax <= tx + w + 3) else (y - 3 if ay < y else y + hh + 3)
    tela.linha(lx, ly, ax, ay, cor)
    tela.disco(ax, ay, 1.5, cor)


def seta(tela, x0, y0, x1, y1, cor, esp=4, cab=7):
    seta_forca(tela, x0, y0, x1, y1, cor, esp, cab)


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def fundo_oficina(tela, t=0.0):
    """Parede escura com grade de oficina (a mesma do ep01)."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24):
        tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24):
        tela.ret(0, y, W, 1, FUNDO2)


def check(tela, x, y, cor=VERDE):
    """Sinal de "feito" desenhado (a fonte não tem o glifo)."""
    for i, (dx, dy) in enumerate(((0, 3), (1, 4), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1), (7, 0))):
        tela.ret(x + dx, y + dy, 2, 2, cor)


def painel_ar(tela, x, tempo=None, extra=None, sem_vel=False):
    """O painel de sempre: tempo (1..4), onde o ar está, pressão, temperatura, velocidade."""
    fundo_painel(tela)
    nome, est, tot, k = MOD.onde(x)
    if tempo is not None: k = tempo
    tit(tela, f"TEMPO {k + 1} DE 4", 9, ACO3, 9)
    tit(tela, TEMPOS[k][0], 20, TEMPOS[k][1], 17)
    tit(tela, 'ONDE ESTÁ O AR', 44, ACO3, 9)
    tit(tela, nome, 54, BRANCO, 17)
    if tot:
        tit(tela, f"ESTÁGIO {est} DE {tot}", 74, CIANO, 9)
        for j in range(tot):
            c = CIANO if j < est else ACO0
            tela.ret(PX0 + 92 + j * (5 if tot > 8 else 9), 75, 4 if tot > 8 else 7, 6, c)
    p, T = MOD.p(x), MOD.T(x)
    tit(tela, 'PRESSÃO', 88, ACO3, 9)
    tit(tela, f"{dec(p, 1)} X", 98, AMARELO, 17)
    tela.texto('A DE FORA', PX0 + 64 if p < 10 else PX0 + 76, 104, ACO2, tam=9)
    barra(tela, PX0 + 1, 118, 156, 4, math.log(max(p, 1.0)) / math.log(40.0), AMARELO)
    tit(tela, 'TEMPERATURA', 128, ACO3, 9)
    tit(tela, f"{milhar(T)} °C", 138, cor_calor(T, .5), 17)
    escala_calor(tela, PX0 + 1, 158, 156, 3)
    mx = PX0 + 1 + int(155 * min(1.0, max(0.0, (T - 15) / 1585)))
    tela.ret(mx - 1, 155, 3, 9, BRANCO)
    tela.ret(mx, 156, 1, 7, PRETO)
    if not sem_vel:
        tit(tela, 'VELOCIDADE', 170, ACO3, 9)
        barra(tela, PX0 + 72, 172, 85, 4, MOD.v(x) / 165, BRANCO)
    if extra: extra(tela)


def cam_vertical(cap, x_alvo, cy, k):
    """Câmera que põe o ponto x_alvo (unidades do motor) no meio do recorte vertical."""
    return Camera(x_corte(cap) + 90 - x_alvo * k, cy, k)


# ----------------------------------------------------------------- sons
_RNG = np.random.default_rng(25)


def tique(f=1800, dur=.03):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))).astype(np.float32)


def ronco(dur, fc=110.0, ataque=.6, solta=.8):
    """Ronco do motor: ruído grave filtrado (abaixo de ~150 Hz), sem estalo."""
    n = max(16, int(dur * SR))
    x = _RNG.standard_normal(n).astype(np.float32)
    x = QA.lp(QA.lp(x, fc), fc)
    x = QA.hp(x, 30)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / max(ataque, 1e-3)) * np.minimum(1, (dur - tt) / max(solta, 1e-3))
    env *= 1 + .1 * np.sin(2 * np.pi * 2.3 * tt)
    y = x * np.clip(env, 0, None)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def sopro(dur, lo=300, hi=1600):
    """Ar passando: ruído em banda, bem suave."""
    n = max(16, int(dur * SR))
    x = QA.bp(_RNG.standard_normal(n).astype(np.float32), lo, hi)
    tt = np.linspace(0, 1, n)
    env = np.sin(np.pi * tt) ** 1.2
    y = x * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


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

    def ronco_fundo(self, fx, ganho=.05, fc=100):
        fx.put(ronco(self.dur, fc, 1.0, 1.0), self.t0, ganho)


def rampa(t, marcos):
    """Interpola com suavidade entre marcos [(t, valor)]."""
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * suave((t - a) / (b - a))
    return marcos[-1][1]


def linear(t, marcos):
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * (t - a) / (b - a)
    return marcos[-1][1]


# ============================================================ 0 gancho: carro x jato
class Gancho(Cena):
    def preparar(self):
        self.cil = MP.Cilindro(118, 176, .62, seed=3)
        self.bs = self.batidas('batida')
        self.spb = 60.0 / self.c['bpm']

    def teta(self, t):
        """Um tempo (180°) por batida, com o pistão andando o tempo todo."""
        n = t / self.spb
        return n * 180.0

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        # ---- o carro: um tempo de cada vez
        th = self.teta(t)
        self.cil.desenhar(tela, th, t)
        k = int((th % 720) // 180)
        painel(tela, 22, 6, 196, 40, borda=TRACO)
        tela.texto('CARRO', 120, 11, ACO3, tam=9, centro=True)
        tela.texto(f"{k + 1}. {NOMES_CARRO[k]}", 120, 24, MP.TEMPOS[k][3], tam=17, centro=True, contorno=PRETO)
        for j in range(4):
            tela.ret(64 + j * 30, 49, 24, 4, MP.TEMPOS[j][3] if j == k else ACO0)
        # ---- o jato: os 4 ao mesmo tempo
        aceso = t >= 7.6
        cam = Camera(352, 116, .78)
        pulso = 0.0
        if aceso:
            pulso = math.exp(-((t % self.spb) / .25))
        TF.desenhar(tela, cam, t, zonas=1.0 if aceso else 0.0, giro=1.0, jato=1.0)
        painel(tela, 244, 6, 232, 40, borda=AMARELO if aceso else TRACO)
        tela.texto('MOTOR A JATO', 360, 11, ACO3, tam=9, centro=True)
        xs = (-82, -30, 13, 50)
        for j, (nome, cor) in enumerate(TEMPOS):
            px, py = cam.P(xs[j], 44)
            cx = 272 + j * 56
            on = aceso
            c = cor if on else ACO1
            tela.texto(nome, cx, 26, BRANCO if (on and pulso > .5) else c, tam=9, centro=True, contorno=PRETO)
            if on:
                tela.linha(cx, 36, px, py - 4, c)
                tela.disco(px, py - 4, 1.5, c)
        if not aceso:
            escurecer(tela, 246, 48, 232, 158)
        else:
            tela.texto('TODOS AO MESMO TEMPO', 360, 196, AMARELO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for b in self.bs:
            fx.put(tique(1500, .03), self.t0 + b, .06)
        fx.put(ronco(self.dur - 7.0, 95, 1.0, 1.0), self.t0 + 7.0, .05)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        cam = Camera(330, 140, 1.0)
        TF.desenhar(tela, cam, t + 3, giro=1.0)
        escurecer(tela, 0, 0, W, PALCO_H)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA", "O MOTOR A JATO")):
            vis = linha[:max(0, n - j * 14)]
            tela.texto(vis, 26, 40 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", 26, 112, AMARELO, tam=17, contorno=PRETO)
        if t > 2.0:
            for j, (nome, cor) in enumerate(TEMPOS):
                if t > 2.0 + j * .3:
                    tela.texto(nome, 26 + j * 62, 140, cor, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(4):
            fx.put(fx.blip(72 + k * 3, .1), self.t0 + 2.0 + k * .3, .14)


# ============================================================ 2 o avião
class AviaoCena(Cena):
    def preparar(self):
        self.tmp = PX.Tela(W, H, paleta=LG.PAL)

    def desenhar(self, tela, t, tg):
        if t < 13.6:
            ceu_dia(tela, t, desloc=t * 30)
            bob = math.sin(t * .9) * 2
            s = 3.0 + suave((t - 9) / 4.6) * 1.2
            ox = 230 - suave((t - 9) / 4.6) * 30
            P = AV.desenhar(tela, ox, 92 + bob, s, ang=0.0, t=t, giro=1.0, empuxo=.6)
            mx, my = P(-4, 8.2)
            if t > 1.0:
                rotulo(tela, 'MOTOR TURBOFAN', 40, 168, mx - 6 * s, my + 3, AMARELO)
            if 7.0 <= t:
                tela.texto('GENÉRICO: SEM MARCA', 470, 196, ACO4, tam=9, centro='d', contorno=PRETO)
            return
        # o motor de perto, depois aberto ao meio (uma "tampa" que corre da esquerda para a direita)
        u = t - 13.6
        cam = Camera(176 - u * 1.2, 100, 1.5)
        ceu_dia(tela, t, desloc=t * 30)
        if t < 19.6:
            TF.desenhar(tela, cam, t, fechado=True)
            # pilone até a asa
            a, b = cam.P(-40, 55), cam.P(20, 52)
            pol(tela, [(a[0], 0), (b[0] + 30, 0), (b[0], b[1]), (a[0], a[1])], CASCO2, CASCO)
            return
        v = suave((t - 19.6) / 3.0)
        corte = int(v * W)
        TF.desenhar(tela, cam, t)
        self.tmp.buf[:] = 0
        tmp = self.tmp
        ceu_dia(tmp, t, desloc=t * 30)
        TF.desenhar(tmp, cam, t, fechado=True)
        a, b = cam.P(-40, 55), cam.P(20, 52)
        pol(tmp, [(a[0], 0), (b[0] + 30, 0), (b[0], b[1]), (a[0], a[1])], CASCO2, CASCO)
        tela.buf[:PALCO_H, corte:] = tmp.buf[:PALCO_H, corte:]
        if 0 < corte < W:
            tela.ret(corte, 0, 2, PALCO_H, AMARELO)
            tela.ret(corte + 2, 0, 1, PALCO_H, BRANCO)

    def sons(self, fx):
        fx.put(ronco(self.dur, 90, 1.5, 1.0), self.t0, .05)
        fx.put(sopro(2.6, 600, 2400), self.t0 + 19.6, .05)


# ============================================================ 3 as peças
class Pecas(Cena):
    PECAS = [('fan', 'FAN', 'PUXA O AR', -77, 40), ('compressor', 'COMPRESSOR', 'APERTA O AR', -30, 16),
             ('camara', 'CÂMARA DE', 'QUEIMA', 14, 11), ('turbina', 'TURBINA', 'GIRA COM O GÁS', 40, 15),
             ('eixos', 'EIXOS', 'LEVAM O GIRO', -10, 2), ('bocal', 'BOCAL', 'SOLTA O GÁS', 72, 10)]
    TS = [0.0, 8.0, 16.0, 24.0, 32.0, 40.0]

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        i = max(j for j, a in enumerate(self.TS) if t >= a)
        foco, nome, fun, xa, ra = self.PECAS[i]
        cam = Camera(150, 104, 1.5)
        TF.desenhar(tela, cam, t, foco=None if foco == 'eixos' else foco, spools=(foco == 'eixos'), x1=PX0 - 8)
        if foco == 'eixos':
            escurecer(tela, 0, 0, PX0 - 8, 104 - 12 * 1.5)
            escurecer(tela, 0, 104 + 12 * 1.5, PX0 - 8, PALCO_H)
        ax, ay = cam.P(xa, ra, -1)
        u = t - self.TS[i]
        if u > .3:
            nm = nome if foco != 'camara' else 'CÂMARA'
            lx = max(8, min(ax - 30, 220))
            rotulo(tela, nm, lx, 8, ax, ay, AMARELO, tam=17)
        # painel: a lista das peças
        fundo_painel(tela)
        tit(tela, 'AS PEÇAS', 9, ACO3, 9)
        for j, (_, n, f, _, _) in enumerate(self.PECAS):
            y = 24 + j * 30
            if j < i:
                check(tela, PX0, y + 3)
                tela.texto(n if j != 2 else 'CÂMARA', PX0 + 14, y, ACO3, tam=9)
            elif j == i:
                tela.ret(PX0 - 3, y - 3, 162, 26, FUNDO2)
                tela.texto(n if j != 2 else 'CÂMARA', PX0 + 2, y, AMARELO, tam=17 if j != 2 else 17, contorno=PRETO)
                tela.texto(f if j != 2 else 'O COMBUSTÍVEL QUEIMA', PX0 + 2, y + 16, BRANCO, tam=9)
            else:
                tela.texto(n if j != 2 else 'CÂMARA', PX0 + 14, y, ACO1, tam=9)

    def sons(self, fx):
        for k, a in enumerate(self.TS):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + a + .3, .12)
        self.ronco_fundo(fx, .04)


# ============================================================ 4 admissão: SUGA
class Admissao(Cena):
    def x(self, t):
        return rampa(t, [(0, -150), (6.5, -108), (8.5, -88), (11.5, -70), (13.0, -66), (27.0, -64.5), (31, -63.5),
                         (36.0, -60.5)])

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        k = 2.15
        cam = Camera(100 + 77 * k, 104, k) if not VERTICAL else cam_vertical('admissao', -80, 104, k)
        TF.desenhar(tela, cam, t, x1=PX0 - 8 if not VERTICAL else W)
        x = self.x(t)
        px, py = parcela(tela, cam, x, t)
        if t < 13.0 and t > .5:
            rotulo(tela, 'O NOSSO AR', int(px) - 30, max(4, int(py) - 30), px, py - 4, BRANCO)
        # a divisão: 1 kg no miolo, 10 por fora
        if 13.6 <= t < 27.4:
            ax, ay = cam.P(-58, 33, -1)
            bx, by = cam.P(-58, 15, -1)
            seta(tela, ax - 30, ay, ax + 26, ay, CIANO, 4, 6)
            seta(tela, bx - 30, by, bx + 14, by, AMARELO, 3, 5)
            etiqueta(tela, 'POR FORA', int(ax + 2), int(ay) - 18, CIANO)
            etiqueta(tela, 'MIOLO', int(bx - 10), int(by) + 6, AMARELO)
        if t >= 27.6:
            # a ponta da pá do fan: ondas de choque
            tx, ty = cam.P(-76, 46, -1)
            for j in range(3):
                r = ((t * 3 + j / 3) % 1.0) * 14
                for a in np.linspace(-1.2, 1.2, 14):
                    tela.px(int(tx + 6 + math.cos(a) * r), int(ty + 6 + math.sin(a) * r), BRANCO if j == 0 else ACO4)
            brilho(tela, tx, ty + 4, 6, BRANCO)
            rotulo(tela, 'PONTA: MAIS RÁPIDA QUE O SOM', 8 if not VERTICAL else x_corte('admissao') + 4, 190,
                   tx + 2, ty + 6, AMARELO)
        if VERTICAL:
            hud_v(tela, 'admissao', [(f"PRESSÃO {dec(MOD.p(x), 1)} X", AMARELO), (f"{milhar(MOD.T(x))} °C", CIANO)])
            return
        painel_ar(tela, x, tempo=0, extra=self.extra(t))

    def extra(self, t):
        def f(tela):
            if 13.6 <= t < 20.6:
                tit(tela, 'POR FORA, PARA 1 KG', 182, CIANO, 9)
                n = 5 + int(min(7, (t - 13.6) / 6.8 * 8))
                tit(tela, f"NO MIOLO: {n} KG", 193, BRANCO, 9)
                for j in range(12):
                    tela.ret(PX0 + 100 + (j % 6) * 9, 182 + (j // 6) * 9, 7, 7, CIANO if j < n else ACO0)
            elif 20.6 <= t < 27.6:
                tit(tela, 'EMPURRÃO', 182, ACO3, 9)
                tela.texto('FAN', PX0, 194, CIANO, tam=9)
                barra(tela, PX0 + 34, 195, 120, 4, .8, CIANO)
                tela.texto('MIOLO', PX0 + 70, 182, AMARELO, tam=9)
                barra(tela, PX0 + 110, 183, 44, 4, .5, AMARELO)
            elif t >= 27.6:
                tit(tela, 'PONTA DO FAN:', 182, ACO3, 9)
                tit(tela, 'SUPERSÔNICA', 193, AMARELO, 9)
        return f

    def sons(self, fx):
        self.ronco_fundo(fx, .05)
        fx.put(sopro(3.0, 400, 2200), self.t0 + 8.0, .05)
        for j in range(8):
            fx.put(tique(2600, .02), self.t0 + 28.0 + j * .9, .03)


# ============================================================ 5 compressor: ESPREME (no ritmo)
class Compressor(Cena):
    def preparar(self):
        cs = [c for c in self.batidas('compasso') if c >= 3.9]
        self.st = cs[:13]                                    # um estágio por compasso
        self.bs = self.batidas('batida')
        self.rot = TF.ROT_C

    def estagio(self, t):
        return sum(1 for a in self.st if t >= a)             # 0..13

    def x(self, t):
        n = self.estagio(t)
        if n == 0:
            return linear(t, [(0, -66.0), (self.st[0], -60.5)])
        if t >= self.st[-1] + 1.8:
            return linear(t, [(self.st[-1] + 1.8, 1.5), (self.dur, 5.0)])
        xr = self.rot[n - 1][0]
        a = self.st[n - 1]
        x_prev = self.rot[n - 2][0] + 2.2 if n > 1 else -60.5
        return x_prev + (xr + 2.2 - x_prev) * ease(min(1.0, (t - a) / .45))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        k = 2.8
        cam = Camera(150 + 30 * k, 104, k) if not VERTICAL else cam_vertical('compressor', -30, 104, k)
        n = self.estagio(t)
        bat = math.exp(-min((t - b) for b in self.bs if b <= t + 1e-6) / .15) if any(b <= t for b in self.bs) else 0
        aceso = {}
        for j in range(13):
            if j < n - 1: aceso[('c', j)] = 0.0
        if n > 0:
            aceso[('c', n - 1)] = .4 + .6 * bat
        TF.desenhar(tela, cam, t, aceso=aceso, x1=PX0 - 8 if not VERTICAL else W)
        x = self.x(t)
        parcela(tela, cam, x, t)
        # números dos estágios em cima
        for j, (xr, _, _) in enumerate(self.rot):
            px, py = cam.P(xr, r_top(xr) + 2.0, -1)
            if 0 < px < (PX0 - 10 if not VERTICAL else W):
                cor = AMARELO if j == n - 1 else (CIANO if j < n else ACO1)
                tela.texto(str(j + 1), int(px), int(py) - 10, cor, tam=9, centro=True, contorno=PRETO)
        if VERTICAL:
            hud_v(tela, 'compressor', [(f"ESTÁGIO {max(1, n)} DE 13", CIANO), (f"PRESSÃO {dec(MOD.p(x), 1)} X", AMARELO),
                                       (f"{milhar(MOD.T(x))} °C", cor_calor(MOD.T(x)))], y=PALCO_H - 46)
            return
        painel_ar(tela, x, tempo=1, extra=self.grafico(t), sem_vel=True)

    def grafico(self, t):
        def f(tela):
            n = self.estagio(t)
            tit(tela, 'PRESSÃO EM CADA ESTÁGIO', 168, ACO3, 9)
            for j in range(13):
                p = MOD.PI_FAN * (MOD.PI_TOT / MOD.PI_FAN) ** ((j + 1) / 13)
                h = max(1, int(24 * p / 40))
                x = PX0 + 4 + j * 12
                tela.ret(x, 203 - h, 9, h, (AMARELO if j == n - 1 else CIANO) if j < n else ACO0)
        return f

    def sons(self, fx):
        self.ronco_fundo(fx, .05, 110)
        for j, a in enumerate(self.st):
            fx.put(tique(900 * 2 ** (j / 12), .05), self.t0 + a, .1)


def r_top(x):
    return D.r_cc(x)


# ============================================================ 6 combustão: QUEIMA
class Combustao(Cena):
    def x(self, t):
        return rampa(t, [(0, -2.0), (5.0, 4.0), (8.0, 8.0), (20.0, 18.0), (27.0, 22.0), (33.0, 26.0), (36.0, 28.0)])

    def chama(self, t):
        return min(1.0, max(0.0, (t - 3.0) / 1.2))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        k = 5.0
        cam = Camera(150 - 14 * k, 104, k) if not VERTICAL else cam_vertical('combustao', 14, 104, k)
        ch = self.chama(t)
        TF.desenhar(tela, cam, t, chama=ch, x1=PX0 - 8 if not VERTICAL else W)
        x = self.x(t)
        if ch < 1:
            # antes de acender: o ar ainda não esquentou
            pass
        parcela(tela, cam, x, t)
        bx, by = cam.P(D.COMB[0] - .5, D.r_cc(D.COMB[0]) - 1, -1)
        if 1.0 < t < 14:
            xl = 92 if not VERTICAL else x_corte('combustao') + 6
            rotulo(tela, 'BICO DE COMBUSTÍVEL', xl, 22, bx, by, LATAO)
        if t >= 7.0 and t < 14.0:
            self.carro(tela, t)
        if VERTICAL:
            hud_v(tela, 'combustao', [(f"{milhar(MOD.T(x))} °C", cor_calor(MOD.T(x))),
                                      (f"PRESSÃO {dec(MOD.p(x), 1)} X", AMARELO)], y=PALCO_H - 32)
            return
        painel_ar(tela, x, tempo=2, extra=self.extra(t))

    def carro(self, tela, t):
        """Inset: no carro, uma queima de cada vez (estouros)."""
        x0 = 8 if not VERTICAL else x_corte('combustao') + 4
        painel(tela, x0, 124, 74, 80, borda=TRACO)
        cil = MP.Cilindro(x0 + 37, 196, .4, seed=7)
        th = (t - 7.0) * 2.2 * 360
        cil.desenhar(tela, th, t)
        tela.texto('CARRO', x0 + 37, 128, ACO3, tam=9, centro=True, contorno=PRETO)

    def extra(self, t):
        def f(tela):
            if t >= 7.0:
                tit(tela, 'CHAMA', 182, ACO3, 9)
                tit(tela, 'SEMPRE ACESA', 193, CHAMA1, 9)
        return f

    def sons(self, fx):
        self.ronco_fundo(fx, .05, 100)
        fx.put(sopro(1.6, 1500, 5000), self.t0 + 2.0, .04)
        fx.put(ronco(self.dur - 3.0, 160, .8, 1.0), self.t0 + 3.0, .05)
        for k in range(int(7 * 2.2 / 2)):                    # estouros do carrinho (1 a cada 2 voltas)
            fx.put(fx.explosao(.6), self.t0 + 7.0 + (k + .9) * 2 / 2.2, .05)


# ============================================================ 7 turbina
class Turbina(Cena):
    def preparar(self):
        self.ts = [3.0 + j * 3.4 for j in range(7)]

    def x(self, t):
        rot = TF.ROT_T
        n = sum(1 for a in self.ts if t >= a)
        if n == 0: return linear(t, [(0, 21.0), (3.0, 24.6)])
        if t >= self.ts[-1] + 1.0:
            return rampa(t, [(self.ts[-1] + 1.0, rot[-1][0] + 1.5), (self.dur, 64.0)])
        xr = rot[n - 1][0]
        x_prev = rot[n - 2][0] + 1.5 if n > 1 else 24.6
        return x_prev + (xr + 1.5 - x_prev) * ease(min(1.0, (t - self.ts[n - 1]) / .7))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        k = 3.6
        cam = Camera(150 - 40 * k, 104, k)
        x = self.x(t)
        n = sum(1 for a in self.ts if t >= a)
        aceso = {('t', n - 1): .7} if 0 < n <= 7 and t < self.ts[-1] + 1.0 else {}
        TF.desenhar(tela, cam, t, aceso=aceso, x1=PX0 - 8)
        parcela(tela, cam, x, t)
        for j, (xr, sp, _) in enumerate(TF.ROT_T):
            px, py = cam.P(xr, D.r_cc(xr) + 2.0, -1)
            cor = AMARELO if j == n - 1 else (CIANO if j < n else ACO1)
            tela.texto(str(j + 1), int(px), int(py) - 10, cor, tam=9, centro=True, contorno=PRETO)
        a, b = cam.P(24.5, 26, -1), cam.P(33, 26, -1)
        tela.texto('ALTA', int((a[0] + b[0]) / 2), 2, LARANJA, tam=9, centro=True, contorno=PRETO)
        a, b = cam.P(34, 26, -1), cam.P(57, 26, -1)
        tela.texto('BAIXA', int((a[0] + b[0]) / 2), 2, VERDE, tam=9, centro=True, contorno=PRETO)
        if 14.0 <= t < 21.0:
            # o giro indo para a frente pelos eixos
            for j in range(6):
                u = ((t * .9 + j / 6) % 1.0)
                xx = 56 - u * 140
                for (rr, cor) in ((4.3, LARANJA), (0.0, VERDE)):
                    if rr > 0 and xx < -40: continue
                    p = cam.P(xx, rr, -1)
                    if p[0] > 0: brilho(tela, p[0], p[1], 3, cor); tela.disco(p[0], p[1], 1.5, BRANCO)
            seta(tela, 120, 14, 24, 14, AMARELO, 4, 7)
            tela.texto('PARA O COMPRESSOR E O FAN', 24, 24, AMARELO, tam=9, contorno=PRETO)
        painel_ar(tela, x, tempo=3)

    def sons(self, fx):
        self.ronco_fundo(fx, .05, 100)
        for j, a in enumerate(self.ts):
            fx.put(tique(1400 * 2 ** (-j / 12), .05), self.t0 + a, .08)


# ============================================================ 8 dois eixos
class Eixos(Cena):
    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        cam = Camera(150, 104, 1.5)
        fase = 0 if t < 6.2 else (1 if t < 12.2 else 2)
        sp = True if fase == 0 else ('HP' if fase == 1 else 'LP')
        TF.desenhar(tela, cam, t, spools=sp, ar=.5, x1=PX0 - 8)
        if fase == 1:
            a = cam.P(-38, 13, -1); b = cam.P(31, 13, -1)
            rotulo(tela, 'EIXO DE ALTA', 40, 6, (a[0] + b[0]) / 2, a[1], LARANJA, tam=17)
        elif fase == 2:
            a = cam.P(-77, 40, -1)
            rotulo(tela, 'EIXO DE BAIXA', 40, 6, a[0], a[1], VERDE, tam=17)
            if t >= 18.2:
                tx, ty = cam.P(-76, 46, -1)
                tela.anel(tx, ty, 5 + math.sin(t * 6), AMARELO)
                rotulo(tela, 'PONTA DO FAN', 150, 190, tx + 3, ty + 4, AMARELO)
        fundo_painel(tela)
        tit(tela, 'DOIS EIXOS', 9, BRANCO, 17)
        for j, (nome, cor, rps, lig) in enumerate((('ALTA', LARANJA, 1.9, 'COMPRESSOR + TURBINA DA FRENTE'),
                                                    ('BAIXA', VERDE, 1.1, 'FAN + TURBINA DE TRÁS'))):
            y = 34 + j * 76
            on = (fase == 0) or (fase == 1 and j == 0) or (fase == 2 and j == 1)
            c = cor if on else ACO1
            tit(tela, f"EIXO DE {nome}", y, c, 9)
            tit(tela, lig.split(' + ')[0] + ' +', y + 12, BRANCO if on else ACO1, 9)
            tit(tela, lig.split(' + ')[1], y + 23, BRANCO if on else ACO1, 9)
            cx, cy = PX0 + 135, y + 30
            tela.disco(cx, cy, 15, PRETO); tela.anel(cx, cy, 15, c)
            a = t * rps * 2 * math.pi
            for q in range(3):
                b = a + q * 2 * math.pi / 3
                tela.linha(cx, cy, cx + math.cos(b) * 13, cy + math.sin(b) * 13, c)
            tela.disco(cx, cy, 2, BRANCO)
            if j == 1:
                tit(tela, 'MAIS DEVAGAR', y + 38, VERDE if on else ACO1, 9)

    def sons(self, fx):
        self.ronco_fundo(fx, .04)
        for a in (6.2, 12.2, 18.2):
            fx.put(fx.blip(76, .1), self.t0 + a, .1)


# ============================================================ 9 calor: a pá que não derrete
class Calor(Cena):
    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        frio = 1.0 if t >= 7.6 else 0.0
        furos = suave((t - 14.6) / 2.0)
        camada = 1.0 if t >= 21.6 else 0.0
        s = 3.1 if not VERTICAL else 2.3
        cx = 150 if not VERTICAL else x_corte('calor') + 90
        pa_corte(tela, cx, 104, s, t, frio=frio, furos=furos, camada=camada)
        perigo = t < 7.6
        if perigo:
            brilho(tela, cx, 104, 40 * (1 + .1 * math.sin(t * 7)), VERMELHO)
        xl = 8 if not VERTICAL else x_corte('calor') + 4
        tela.texto('GÁS A 1.500 °C', xl, 8, Q6, tam=9, contorno=PRETO)
        if t >= 7.6:
            seta(tela, cx - 20 * s, 190, cx - 20 * s, 162, FRIO1, 3, 5)
            tela.texto('AR DO COMPRESSOR', xl, 194, FRIO1, tam=9, contorno=PRETO)
        if t >= 21.6:
            px, py = cx - 6 * s, 104 - 7.5 * s
            rotulo(tela, 'CAMADA ISOLANTE', cx + 20, 26, px, py, CERAMICA)
        if VERTICAL:
            return
        fundo_painel(tela)
        tit(tela, 'TEMPERATURA', 9, ACO3, 9)
        tit(tela, 'GÁS', 24, BRANCO, 9)
        tit(tela, '1.500 °C', 34, Q6, 17)
        tit(tela, 'O METAL DA PÁ', 58, BRANCO, 9)
        tit(tela, 'DERRETE A', 69, BRANCO, 9)
        tit(tela, '1.030 A 1.130 °C', 80, VERMELHO, 9)
        escala_calor(tela, PX0 + 1, 96, 156, 4)
        for T, cor in ((1500, BRANCO), (1080, VERMELHO)):
            mx = PX0 + 1 + int(155 * (T - 15) / 1585)
            tela.ret(mx, 92, 1, 12, cor)
        itens = [('AR POR DENTRO', 7.6), ('FUROS: PELE DE AR', 14.6), ('CAMADA ISOLANTE', 21.6)]
        for j, (txt, a) in enumerate(itens):
            y = 118 + j * 20
            if t >= a:
                check(tela, PX0, y + 2)
                tela.texto(txt, PX0 + 14, y, FRIO1, tam=9, contorno=PRETO)
            else:
                tela.ret(PX0 + 1, y + 1, 7, 7, ACO0)
                tela.texto(txt, PX0 + 14, y, ACO1, tam=9)
        if t >= 21.6:
            tit(tela, 'A PÁ AGUENTA!', 186, VERDE, 9)
        elif perigo:
            tit(tela, 'SEM PROTEÇÃO:', 180, VERMELHO, 9)
            tit(tela, 'DERRETERIA', 191, VERMELHO, 9)

    def sons(self, fx):
        fx.put(ronco(self.dur, 80, 1.0, 1.0), self.t0, .04)
        for a in (7.6, 14.6, 21.6):
            fx.put(fx.blip(79, .1), self.t0 + a, .1)
        fx.put(sopro(5.0, 2000, 6000), self.t0 + 14.6, .03)


# ============================================================ 10 bocal: SOPRA + Newton
class Bocal(Cena):
    def x(self, t):
        return rampa(t, [(0, 48.0), (4.0, 64.0), (6.8, 120.0), (7.0, 150.0)])

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        k = 2.2
        emp = 0.0
        if t >= 28.0: emp = -3 * suave((t - 28.0) / 2.0)          # o motor anda um pouquinho para a frente
        cam = Camera(150 - 50 * k + emp, 104, k) if not VERTICAL else cam_vertical('bocal', 46, 104, k)
        TF.desenhar(tela, cam, t, x1=PX0 - 8 if not VERTICAL else W)
        x = self.x(t)
        if t < 7.0:
            parcela(tela, cam, x, t)
        xc = x_corte('bocal') if VERTICAL else 0
        if 7.0 <= t < 14.0:
            a = cam.P(50, 31, -1)
            rotulo(tela, 'AR DO FAN: FRIO', int(a[0]) - 10, 8, a[0], a[1], CIANO)
            a2 = cam.P(80, 6, -1)
            rotulo(tela, 'GÁS QUENTE', int(a2[0]) + 14, 30, a2[0], a2[1], LARANJA)
        if t >= 14.0:
            # ação: o motor empurra o ar para trás (direita)
            gx, gy = cam.P(86, 0, 1)
            x_lim = (PX0 - 14) if not VERTICAL else xc + 176
            seta(tela, gx, 176, min(gx + 58, x_lim), 176, CIANO, 5, 8)
            tela.texto('AR PARA TRÁS', min(gx + 58, x_lim), 188, CIANO, tam=9, centro='d', contorno=PRETO)
            # reação: o ar empurra o motor para a frente (esquerda)
            mx, my = cam.P(20, 0, 1)
            x_min = 8 if not VERTICAL else xc + 6
            if t >= 15.0:
                seta(tela, mx, 18, max(mx - 70, x_min), 18, AMARELO, 6, 9)
                tela.texto('MOTOR PARA A FRENTE', max(mx - 70, x_min), 30, AMARELO, tam=9, contorno=PRETO)
        if t >= 21.0 and not VERTICAL:
            self.foguete_mini(tela, 250, 120, t)
        if t >= 28.0:
            mx, my = cam.P(20, 0, 1)
            etiqueta(tela, 'EMPUXO', int(mx) - 12 if not VERTICAL else xc + 50, 46, AMARELO, tam=17)
        if VERTICAL:
            return
        painel_ar(tela, min(x, 150.0), tempo=3, extra=self.extra(t))

    def foguete_mini(self, tela, x, y, t):
        corpo = [(x - 4, y - 22), (x + 4, y - 22), (x + 4, y + 8), (x - 4, y + 8)]
        contorno(tela, corpo, PRETO)
        pol(tela, corpo, CASCO, CASCO2)
        pol(tela, [(x - 4, y - 22), (x, y - 32), (x + 4, y - 22)], VERMELHO)
        pol(tela, [(x - 4, y + 2), (x - 9, y + 10), (x - 4, y + 8)], ACO2)
        pol(tela, [(x + 4, y + 2), (x + 9, y + 10), (x + 4, y + 8)], ACO2)
        for i in range(10):
            u = (hsh(i, 41) + t * 3) % 1.0
            tela.px(int(x + (hsh(i, 42) - .5) * 6 * (1 + u)), int(y + 10 + u * 16), CHAMA0 if u < .3 else CHAMA1)
        tela.texto('FOGUETE', x, y + 30, ACO3, tam=9, centro=True, contorno=PRETO)

    def extra(self, t):
        def f(tela):
            if t >= 14.0:
                tit(tela, 'AÇÃO E REAÇÃO', 182, AMARELO, 9)
                tit(tela, '3ª LEI DE NEWTON', 193, BRANCO, 9)
        return f

    def sons(self, fx):
        self.ronco_fundo(fx, .05, 95)
        fx.put(sopro(4.0, 250, 1500), self.t0 + 2.0, .05)
        fx.put(fx.blip(74, .12), self.t0 + 14.0, .1)
        fx.put(fx.blip(79, .12), self.t0 + 15.0, .1)


# ============================================================ 11 decolagem
class Decolagem(Cena):
    def preparar(self):
        # velocidade (px/s de chão) e altura (px) do avião, integradas
        ts = np.arange(0, self.dur + .05, 1 / 30)
        v = np.clip((ts - 1.5) / 14.5, 0, None) ** 1.2 * 420
        v = np.minimum(v, 460)
        self.ts = ts
        self.xm = np.concatenate([[0], np.cumsum((v[1:] + v[:-1]) / 2 / 30)])
        self.v = v
        alt = np.where(ts > 16.0, (ts - 16.0) ** 1.6 * 4.0, 0.0)
        self.alt = alt

    def desenhar(self, tela, t, tg):
        i = min(len(self.ts) - 1, int(t * 30))
        xm, v, alt = self.xm[i], self.v[i], self.alt[i]
        ang = -min(.16, max(0.0, (t - 15.0) / 1.2) * .16) if t >= 15.0 else 0.0
        ceu_dia(tela, t, desloc=xm * .1)
        gy = 168 + alt * .5
        if gy < PALCO_H:
            tela.ret(0, int(gy), W, PALCO_H - int(gy), GRAMA0)
            dither(tela, 0, int(gy), W, 3, GRAMA1, GRAMA0)
            tela.ret(0, int(gy) + 6, W, 14, ASFALTO)
            tela.ret(0, int(gy) + 6, W, 1, CONCRETO)
            for j in range(-1, W // 40 + 2):
                xx = (j * 40 + xm) % (W + 40) - 40
                tela.ret(int(xx), int(gy) + 12, 20, 2, BRANCO)
            for j in range(-1, W // 70 + 2):
                xx = (j * 70 + xm * 1.0) % (W + 70) - 70
                tela.disco(xx, int(gy) + 4, 1.5, AMARELO)
        ox, oy = 170, 140 - alt
        trem = 1.0 if t < 22 else max(0.0, 1 - (t - 22) / 2)
        forca = min(1.0, t / 2.0)
        P = AV.desenhar(tela, ox, oy, 2.6, ang=ang, t=t, giro=.5 + forca, trem=trem, empuxo=forca)
        mx, my = P(5.0, 8.2)
        # forças: empuxo (para a frente = esquerda), atrito/ar (para trás)
        if t >= 2.0:
            seta(tela, mx, my, mx - 30 - 30 * forca, my, AMARELO, 4, 7)
            tela.texto('EMPUXO', int(mx - 60 - 30 * forca), int(my) + 8, AMARELO, tam=9, contorno=PRETO)
        if 7.6 <= t < 21.0:
            arr = 10 + v / 460 * 26
            tx, ty = P(52, -2)
            seta(tela, tx + 4, ty, tx + 4 + arr, ty, VERMELHO, 3, 5)
            tela.texto('ATRITO E AR', int(tx + 6), int(ty) - 12, VERMELHO, tam=9, contorno=PRETO)
        if t >= 14.6:
            wx, wy = P(6, 4)
            sust = min(1.0, (t - 14.6) / 2.0)
            seta(tela, wx, wy, wx, wy - 26 - 22 * sust, VERDE, 4, 7)
            tela.texto('ASA: SUSTENTAÇÃO', int(wx) + 6, int(wy - 48 - 22 * sust), VERDE, tam=9, contorno=PRETO)
        fundo_painel(tela)
        tit(tela, 'DECOLAGEM', 9, BRANCO, 17)
        tit(tela, 'EMPUXO DOS MOTORES', 36, ACO3, 9)
        barra(tela, PX0, 48, 156, 6, forca, AMARELO)
        tit(tela, 'VELOCIDADE', 64, ACO3, 9)
        barra(tela, PX0, 76, 156, 6, v / 460, BRANCO)
        tit(tela, 'NO AR' if alt > 1 else 'NA PISTA', 92, VERDE if alt > 1 else ACO3, 17)
        tit(tela, 'VEJA O EP. DO AVIÃO', 180, ACO2, 9)
        tit(tela, 'PARA A ASA', 191, ACO2, 9)

    def sons(self, fx):
        fx.put(ronco(self.dur, 120, 2.0, 2.0), self.t0, .07)
        fx.put(sopro(self.dur - 2, 200, 900), self.t0 + 1.0, .04)


# ============================================================ 12 jato x foguete
class Foguete(Cena):
    def desenhar(self, tela, t, tg):
        meio = 240
        # esquerda: espaço e foguete
        tela.ret(0, 0, meio, PALCO_H, PRETO)
        for i in range(60):
            x, y = int(hsh(i, 1) * meio), int(hsh(i, 2) * PALCO_H)
            if math.sin(t * 1.5 + i) > -.5: tela.px(x, y, BRANCO if i % 4 == 0 else ACO2)
        fx_, fy = 80, 96 + math.sin(t * 2) * 2
        corpo = [(fx_ - 10, fy - 50), (fx_ + 10, fy - 50), (fx_ + 10, fy + 30), (fx_ - 10, fy + 30)]
        contorno(tela, corpo, PRETO)
        pol(tela, corpo, CASCO, CASCO2)
        pol(tela, [(fx_ - 10, fy - 50), (fx_, fy - 72), (fx_ + 10, fy - 50)], ACO3)
        # tanques em corte
        tela.ret(fx_ - 7, fy - 44, 14, 30, D.FRIO0)
        tela.ret(fx_ - 7, fy - 12, 14, 34, LATAO)
        for i in range(14):
            u = (hsh(i, 51) + t * 2.4) % 1.0
            tela.disco(fx_ + (hsh(i, 52) - .5) * 10 * (1 + u), fy + 34 + u * 40, 3 - u * 2,
                       CHAMA0 if u < .3 else (CHAMA1 if u < .6 else BRASA))
        brilho(tela, fx_, fy + 40, 12, CHAMA1)
        rotulo(tela, 'OXIDANTE', 128, 46, fx_ + 7, fy - 30, CIANO)
        rotulo(tela, 'COMBUSTÍVEL', 128, 76, fx_ + 7, fy + 6, LATAO)
        tela.texto('FOGUETE', 120, 8, BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto('LEVA TUDO A BORDO', 120, 186, ACO3, tam=9, centro=True, contorno=PRETO)
        # direita: jato no céu (que escurece no fim, quando o ar acaba)
        sobe = suave((t - 15.6) / 6.0)
        tmp_y = PALCO_H
        gradiente(tela, meio, 0, W - meio, PALCO_H, [(0, CEU4 if sobe < .5 else PRETO), (1, CEU2 if sobe < .3 else (CEU5 if sobe < .8 else PRETO))])
        tela.ret(meio, 0, 2, PALCO_H, PRETO)
        cam = Camera(372, 110, .82)
        ar = max(0.0, 1 - sobe)
        TF.desenhar(tela, cam, t, ar=ar, chama=ar, giro=.3 + .7 * ar, jato=ar)
        if t >= 7.6 and ar > .2:
            for j in range(6):
                u = (t * .8 + j / 6) % 1.0
                x = meio + 8 + u * 40
                y = 70 + j * 14
                tela.texto('O2', int(x), int(y), CIANO, tam=9, contorno=PRETO)
        tela.texto('MOTOR A JATO', 360, 8, BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto('USA O AR DE FORA' if sobe < .5 else 'SEM AR: APAGA', 360, 186, AMARELO if sobe < .5 else VERMELHO,
                   tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        fx.put(ronco(self.dur, 90, 1.0, 1.0), self.t0, .04)


# ============================================================ 13 ritmo: os 4 tempos nas batidas
class Ritmo(Cena):
    def preparar(self):
        self.bs = self.batidas('batida')
        self.spb = 60.0 / self.c['bpm']

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        n = sum(1 for b in self.bs if b <= t + 1e-6) - 1
        n = max(0, n)
        dt = t - (self.bs[n] if self.bs else 0)
        u = ease(min(1.0, dt / (self.spb * .8)))
        th = (n + u) * 180.0
        k = int((th % 720) // 180)
        pulso = math.exp(-dt / .15)
        if VERTICAL:
            xc = x_corte('ritmo') + 90
            cil = MP.Cilindro(xc, 96, .42, seed=4)
            cil.desenhar(tela, th, t)
            tela.texto(NOMES_CARRO[k], xc, 6, MP.TEMPOS[k][3], tam=9, centro=True, contorno=PRETO)
            cam = Camera(xc + 14, 160, .5)
            TF.desenhar(tela, cam, t, zonas=1.0 if pulso > .3 else .5, jato=1.0)
            for j, (nome, cor) in enumerate(TEMPOS):
                tela.texto(nome, xc - 84 + j * 44 + 20, 192, BRANCO if pulso > .5 else cor, tam=9, centro=True, contorno=PRETO)
            return
        cil = MP.Cilindro(118, 178, .62, seed=4)
        cil.desenhar(tela, th, t)
        painel(tela, 22, 6, 196, 40, borda=MP.TEMPOS[k][3] if pulso > .4 else TRACO)
        tela.texto('CARRO: 1 POR BATIDA', 120, 11, ACO3, tam=9, centro=True)
        tela.texto(f"{k + 1}. {NOMES_CARRO[k]}", 120, 24, MP.TEMPOS[k][3], tam=17, centro=True, contorno=PRETO)
        cam = Camera(352, 116, .78)
        TF.desenhar(tela, cam, t, zonas=1.0 if pulso > .3 else .5, jato=1.0)
        painel(tela, 244, 6, 232, 40, borda=AMARELO if pulso > .4 else TRACO)
        tela.texto('JATO: OS 4 EM TODA BATIDA', 360, 11, ACO3, tam=9, centro=True)
        xs = (-82, -30, 13, 50)
        for j, (nome, cor) in enumerate(TEMPOS):
            px, py = cam.P(xs[j], 44)
            cx = 272 + j * 56
            tela.texto(nome, cx, 26, BRANCO if pulso > .5 else cor, tam=9, centro=True, contorno=PRETO)
            tela.linha(cx, 36, px, py - 4, cor)
        tela.texto(f"BATIDA {n + 1}", 360, 196, ACO3, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for j, b in enumerate(self.bs):
            fx.put(tique(1200 if j % 4 else 1800, .03), self.t0 + b, .05)
        self.ronco_fundo(fx, .04)


# ============================================================ 14 história (só texto e máquinas, ninguém desenhado)
class Historia(Cena):
    MARCOS = [(0.5, '1930', 'A PATENTE'), (7.8, '1937', 'MOTORES EM TESTE'), (21.8, '1939', 'O 1º AVIÃO A JATO'),
              (28.6, 'HOJE', 'TURBOFANS')]

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        # linha do tempo embaixo
        tela.ret(20, 182, 270, 2, ACO1)
        for j, (a, ano, txt) in enumerate(self.MARCOS):
            x = 34 + j * 80
            on = t >= a
            tela.disco(x, 183, 4, AMARELO if on else ACO0)
            tela.texto(ano, x, 190, AMARELO if on else ACO1, tam=9, centro=True, contorno=PRETO)
        i = max([j for j, (a, _, _) in enumerate(self.MARCOS) if t >= a] or [0])
        if t < 7.8:
            self.patente(tela, t)
        elif t < 21.8:
            self.bancada(tela, t, dois=t >= 14.8)
        elif t < 28.6:
            self.jatinho(tela, t - 21.8)
        else:
            cam = Camera(150, 96, 1.2)
            TF.desenhar(tela, cam, t, x1=PX0 - 8)
        fundo_painel(tela)
        a, ano, txt = self.MARCOS[i]
        tit(tela, ano, 12, AMARELO, 26)
        tit(tela, txt, 44, BRANCO, 9)
        notas = {0: ['FRANK WHITTLE,', 'INGLATERRA'], 1: ['WHITTLE (ABRIL)', 'VON OHAIN (SET.)'],
                 2: ['27 DE AGOSTO', 'MOTOR DE VON OHAIN'], 3: ['O MESMO MIOLO', '+ UM FAN GIGANTE']}
        if i == 1 and t >= 14.8:
            notas[1] = ['WHITTLE (ABRIL)', 'VON OHAIN (SET.),', 'NA ALEMANHA']
        for j, l in enumerate(notas[i]):
            tit(tela, l, 64 + j * 12, ACO3, 9)
        tit(tela, 'SÓ MÁQUINAS:', 170, ACO2, 9)
        tit(tela, 'NINGUÉM DESENHADO', 181, ACO2, 9)

    def patente(self, tela, t):
        x0, y0 = 40, 22
        painel(tela, x0, y0, 220, 146, borda=CEU1, fundo=CEU5)
        for y in range(y0 + 8, y0 + 146, 10):
            tela.ret(x0 + 2, y, 216, 1, CEU4)
        u = min(1.0, t / 5.0)
        # desenho técnico de um motor a jato simples (linhas brancas que vão aparecendo)
        pts = [(60, 96), (90, 70), (200, 74), (236, 88), (236, 104), (200, 118), (90, 122), (60, 96)]
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        resto = L * u
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            f = min(1.0, max(0.0, resto / d))
            tela.linha(a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, BRANCO)
            resto -= d
        if u >= 1:
            tela.anel(110, 96, 18, CEU0)
            tela.ret(140, 84, 30, 24, CEU5); tela.ret(140, 84, 30, 1, BRANCO); tela.ret(140, 107, 30, 1, BRANCO)
            for k in range(4): tela.linha(178 + k * 5, 80, 178 + k * 5, 112, CEU0)
            tela.texto('PATENTE', x0 + 6, y0 + 126, BRANCO, tam=9)
        tela.texto('1930', x0 + 214, y0 + 6, CEU0, tam=9, centro='d')

    def bancada(self, tela, t, dois=False):
        """Motor a jato antigo (compressor centrífugo) numa bancada de teste."""
        for j in range(2 if dois else 1):
            cx, cy, s = (150, 100, 1.0) if not dois else ((90, 88, .7) if j == 0 else (220, 132, .7))
            tela.ret(cx - 60 * s, cy + 30 * s, 120 * s, 6 * s, ACO1)
            for q in (-40, 40): tela.ret(cx + q * s, cy + 18 * s, 4 * s, 14 * s, ACO0)
            corpo = [(cx - 50 * s, cy - 22 * s), (cx + 20 * s, cy - 16 * s), (cx + 55 * s, cy - 10 * s),
                     (cx + 55 * s, cy + 10 * s), (cx + 20 * s, cy + 16 * s), (cx - 50 * s, cy + 22 * s)]
            contorno(tela, corpo, PRETO)
            pol(tela, corpo, ACO2, ACO3)
            tela.disco(cx - 34 * s, cy, 18 * s, ACO1)
            a = t * 9
            for q in range(8):
                b = a + q * math.pi / 4
                tela.linha(cx - 34 * s, cy, cx - 34 * s + math.cos(b) * 16 * s, cy + math.sin(b) * 16 * s, ACO4)
            tela.ret(cx - 4 * s, cy - 8 * s, 22 * s, 16 * s, FUNDO2)
            for q in range(10):
                u = (hsh(q, 61 + j) + t * 2) % 1
                tela.ret(cx + (-2 + u * 18) * s, cy + (hsh(q, 62) - .5) * 12 * s, 2, 2, CHAMA0 if u < .4 else CHAMA1)
            for q in range(12):
                u = (hsh(q, 63 + j) + t * 1.6) % 1
                tela.px(int(cx + (56 + u * 40) * s), int(cy + (hsh(q, 64) - .5) * (10 + u * 14) * s), GAS2 if u > .5 else BRASA)
            tela.texto('INGLATERRA' if j == 0 else 'ALEMANHA', cx, cy - 38 * s, ACO3, tam=9, centro=True, contorno=PRETO)

    def jatinho(self, tela, u):
        ceu_dia(tela, u, y1=176, desloc=u * 40)
        P = AV.desenhar(tela, 170 - u * 6, 100 + math.sin(u) * 3, 1.6, t=u, giro=1.0, empuxo=.8)
        tela.texto('UM PRIMEIRO JATO (GENÉRICO)', 150, 12, BRANCO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for a, _, _ in self.MARCOS:
            fx.put(fx.blip(74, .12), self.t0 + a, .12)


# ============================================================ 15 resumo
class Resumo(Cena):
    def x(self, t):
        return linear(t, [(0, -140), (7.6, -63), (15.0, 3), (22.4, 24), (32.6, 130), (33.0, 140)])

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela, t)
        cam = Camera(150, 96, 1.4)
        TF.desenhar(tela, cam, t, x1=PX0 - 8)
        x = self.x(t)
        parcela(tela, cam, min(x, 120), t)
        k = 0 if t < 7.8 else (1 if t < 15.2 else (2 if t < 22.6 else 3))
        xs = (-82, -30, 13, 50)
        for j, (nome, cor) in enumerate(TEMPOS):
            px, py = cam.P(xs[j], 0, 1)
            tela.texto(nome, int(px), 188, cor if j <= k else ACO1, tam=9, centro=True, contorno=PRETO)
        # painel: o gráfico de pressão e temperatura ao longo do motor
        fundo_painel(tela)
        tit(tela, TEMPOS[k][0], 9, TEMPOS[k][1], 17)
        tit(tela, 'PRESSÃO', 32, AMARELO, 9)
        tit(tela, 'TEMPERATURA', 32, VERMELHO, 9, x=PX0 + 70)
        gx, gy, gw, gh = PX0 + 2, 48, 154, 120
        tela.ret(gx, gy, gw, gh, FUNDO)
        tela.ret(gx, gy + gh, gw, 1, ACO1)
        tela.ret(gx, gy, 1, gh, ACO1)
        xs_ = np.linspace(-110, 100, 150)
        ant = None
        for i, xx in enumerate(xs_):
            if xx > x: break
            pxx = gx + 1 + i * (gw - 2) / 150
            yp = gy + gh - 2 - MOD.p(xx) / 41 * (gh - 4)
            yt = gy + gh - 2 - MOD.T(xx) / 1600 * (gh - 4)
            if ant:
                tela.linha(ant[0], ant[1], pxx, yp, AMARELO)
                tela.linha(ant[0], ant[2], pxx, yt, VERMELHO)
            ant = (pxx, yp, yt)
        tit(tela, 'ENTRADA', 172, ACO2, 9)
        tela.texto('SAÍDA', W - 12, 172, ACO2, tam=9, centro='d')
        tit(tela, f"{dec(MOD.p(min(x, 120)), 1)} X   {milhar(MOD.T(min(x, 120)))} °C", 186, BRANCO, 9)

    def sons(self, fx):
        self.ronco_fundo(fx, .045)
        for a in (0.5, 7.8, 15.2, 22.6):
            fx.put(fx.blip(72, .1), self.t0 + a, .1)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            fundo_oficina(tela, t)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            cam = Camera(W // 2 + 10, 140, .85)
            TF.desenhar(tela, cam, t)

    def fim_vinheta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# longo.py chama `pos` (RGB pronto) quando a cena tem esse método: só o Fim usa.
Fim.pos = Fim.fim_vinheta

CENAS = dict(gancho=Gancho, titulo=Titulo, aviao=AviaoCena, pecas=Pecas, admissao=Admissao, compressor=Compressor,
             combustao=Combustao, turbina=Turbina, eixos=Eixos, calor=Calor, bocal=Bocal, decolagem=Decolagem,
             foguete=Foguete, ritmo=Ritmo, historia=Historia, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep25_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if len(sys.argv) > 3:
            for cid in sys.argv[3:]:
                c = next(c for c in trilha.caps if c['id'] == cid)
                fr = [float(x) for x in os.environ.get('FR', '.1,.3,.5,.7,.9').split(',')]
                ts += [c['t0'] + c['dur'] * f for f in fr]
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
