#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep15 — A jornada de uma garfada pelo corpo (PT-BR).

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (mastigar, gole, aperto do esôfago,
                          bolhas do ácido, gotas, porta), nos mesmos instantes
A posição da garfada (e depois dos nutrientes) sai de uma função do tempo em
cada capítulo; o painel lê o mesmo estado (etapa, tempo típico, tamanho).
No esôfago, cada aperto da peristalse cai num bumbo da música (`trilha.L`).

    python3 ep15_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep15_motor.py <saida.mp4> boca esofago        # só esses capítulos (teste)
    python3 ep15_motor.py --folha <saida.png> [ids]       # quadros por capítulo (FR=.1,.5,.9)
    python3 ep15_motor.py --quadros <saida.png> id:t ...  # quadros escolhidos
"""
import math, os, sys
import numpy as np
import ep15_desenho as D                      # registra a paleta 'ep15' (antes de qualquer Tela)
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep15_desenho import (PELE0, PELE1, PELE2, PELE3, CAV0, CAV1, MUC0, MUC1, MUC2, MUC3, MUCO,
                          INT0, INT1, INT2, INT3, FIG0, FIG1, FIG2, FIG3, BILE0, BILE1, BILE2,
                          PAN0, PAN1, PAN2, ARROZ0, ARROZ1, FEI0, FEI1, FEI2, SANG0, SANG1, SANG2,
                          QUI0, QUI1, QUI2, ACI0, ACI1, MAD0, MAD1, RES0, RES1, NOITE,
                          C_MUC, C_INT, C_FIG, C_BILE, C_PAN, C_PELE, C_QUI, C_SANG, C_RES,
                          ETAPAS, NE, rotulo, fio, seta, halo, luz, grad_v, caixa, relogio, gotinha,
                          pintar, tubo, elipse, poli, volume, guardado, ao_longo, lerp, um,
                          grao, feijao, garfada, marca, glicose, aminoacido, bacteria, brilho_estrela,
                          ROTA, U_ETAPA)
import ritmo_marca as RM
from ep15_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 1515, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = -1.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
SR = LG.SR


def fase(t, a, b): return um((t - a) / max(1e-6, b - a))


# ================================================================ sons (senos curtos: pico sob controle)
def _env(n, a, d):
    tt = np.arange(n) / SR
    return (np.minimum(1, tt / max(a, 1e-4)) * np.exp(-tt / d)).astype(np.float32)


def tique(f=900.0, dur=.05, dec=.012):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt) * _env(n, .002, dec)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def varre(f0, f1, dur, harm=.25):
    """Seno que desliza de f0 a f1 (gole, bolha, porta)."""
    n = int(dur * SR)
    u = np.arange(n) / n
    f = f0 * (f1 / f0) ** u
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + harm * np.sin(2 * ph)) * np.sin(np.pi * u) ** .7
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def grave(f=70.0, dur=.18, dec=.05):
    """Baque surdo (aperto de músculo)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f * tt + 8 * (1 - np.exp(-tt / .03)))) * _env(n, .004, dec)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


# ================================================================ base das cenas
class Cena:
    legenda = True
    brilho = None
    K = 0
    VX = 147                  # centro do recorte vertical (selo da etapa no Short)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.L = trilha.L
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def painel(self, tela, t, selo=None, **kw):
        if VERTICAL:
            D.selo_vertical(tela, self.K, self.VX, selo)
        else:
            D.painel_jornada(tela, self.K, t, **kw)

    def rot(self, tela, txt, x, y, cor=BRANCO, alvo=None, centro=False):
        """Rótulo com fio opcional; no Short some se sair do recorte."""
        w = tela.largura_texto(txt, 9)
        xa = x - w // 2 if centro else x
        if VERTICAL and (xa < self.VX - 89 or xa + w > self.VX + 89): return
        rotulo(tela, txt, x, y, cor, centro=centro)
        if alvo:
            ax = xa + w // 2
            ay = y + 9 if alvo[1] > y else y - 2
            fio(tela, ax, ay, alvo[0], alvo[1], cor)

    def batidas(self, tipo='kick'):
        return [e['t'] - self.t0 for e in self.L.lista(tipo) if self.t0 - .01 <= e['t'] < self.t0 + self.dur]


def tecido(tela, x0=0, x1=294, cores=(CAV0, CAV1), seed=1, t=0.0):
    """Fundo de dentro do corpo: escuro, com manchas suaves (não é sangue)."""
    grad_v(tela, x0, 0, x1 - x0, PALCO_H, [cores[0], cores[1], cores[0]])
    rng = np.random.default_rng(seed)
    for k in range(26):
        x = x0 + rng.random() * (x1 - x0); y = rng.random() * PALCO_H
        r = 6 + rng.random() * 14
        halo(tela, x + math.sin(t * .3 + k) * 2, y, r, cores[1] if k % 2 else MUC0, fase=k)


def grade(tela, x0=0, x1=W):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(x0, x1, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(x0, y, x1 - x0, 1, FUNDO2)


def inset(tela, x, y, w, h, titulo=None, cor=AMARELO):
    painel(tela, x, y, w, h, borda=cor)
    if titulo: tela.texto(titulo, x + 4, y + 3, cor, tam=9, contorno=PRETO)


def vapor(tela, x, y, t, n=3, alt=30):
    for k in range(n):
        for j in range(alt):
            u = ((t * 14 + j + k * 11) % alt)
            yy = y - u
            xx = x + k * 9 + math.sin(u * .25 + t * 2 + k) * 3
            if (j + k) % 3 == 0 and u < alt - 4:
                tela.px(xx, yy, FUNDO3 if u > alt * .5 else ACO1)


# ================================================================ o prato
def prato(tela, cx, cy, t, falta=0.0):
    """Prato de arroz com feijão visto de cima, meio inclinado."""
    f = guardado('prato_borda', lambda: elipse(cx, cy, 84, 32))
    pintar(tela, f.ox, f.oy, f.m, D.volume(f, luz=(-.3, -.9)), [ACO1, ACO2, ACO3, ACO4], PRETO)
    g = guardado('prato_meio', lambda: elipse(cx, cy + 2, 64, 22))
    pintar(tela, g.ox, g.oy, g.m, D.volume(g, luz=(.3, .9), amp=.5), [ACO2, ACO3, CERAMICA], ACO1)
    # arroz (esquerda): monte de grãos
    a = guardado('prato_arroz', lambda: elipse(cx - 26, cy, 32, 15))
    pintar(tela, a.ox, a.oy, a.m, D.volume(a), [ARROZ0, ARROZ1, CERAMICA, BRANCO], ARROZ0)
    rng = np.random.default_rng(4)
    for k in range(70):
        ang = rng.random() * 6.28; rr = math.sqrt(rng.random())
        x = cx - 26 + math.cos(ang) * rr * 29; y = cy + math.sin(ang) * rr * 13
        if falta > 0 and math.hypot(x - (cx - 10), (y - cy) * 2) < 14 * falta: continue
        grao(tela, x, y, k % 2)
    # feijão (direita): caldo e grãos
    b = guardado('prato_feijao', lambda: elipse(cx + 28, cy + 1, 30, 15))
    pintar(tela, b.ox, b.oy, b.m, D.volume(b), [FEI0, FEI1, FEI1, FEI2], FEI0)
    for k in range(26):
        ang = rng.random() * 6.28; rr = math.sqrt(rng.random())
        feijao(tela, cx + 28 + math.cos(ang) * rr * 25, cy + 1 + math.sin(ang) * rr * 11, .9)
    vapor(tela, cx - 30, cy - 18, t, 4, 34)


def garfo(tela, x, y, ang=-.5, t=0.0, carga=True, s=1.0):
    """Garfo genérico: cabo longo e 4 dentes; (x, y) = ponta da carga."""
    c, sn = math.cos(ang), math.sin(ang)
    cabo0 = (x + c * 24 * s, y + sn * 24 * s)
    cabo1 = (x + c * 120 * s, y + sn * 120 * s)
    linha_grossa(tela, cabo0[0], cabo0[1], cabo1[0], cabo1[1], 7 * s, PRETO)
    linha_grossa(tela, cabo0[0], cabo0[1], cabo1[0], cabo1[1], 5 * s, ACO3)
    linha_grossa(tela, cabo0[0] - sn, cabo0[1] + c, cabo1[0] - sn, cabo1[1] + c, 1.6 * s, ACO4)
    # pescoço e dentes
    nx, ny = -sn, c
    for k in range(4):
        o = (k - 1.5) * 3.2 * s
        a0 = (x + nx * o, y + ny * o)
        a1 = (x + c * 22 * s + nx * o * .6, y + sn * 22 * s + ny * o * .6)
        linha_grossa(tela, a0[0], a0[1], a1[0], a1[1], 2.4 * s, PRETO)
    for k in range(4):
        o = (k - 1.5) * 3.2 * s
        a0 = (x + nx * o, y + ny * o)
        a1 = (x + c * 22 * s + nx * o * .6, y + sn * 22 * s + ny * o * .6)
        tela.linha(a0[0], a0[1], a1[0], a1[1], ACO4 if k == 0 else ACO3)
    poligono(tela, [(x + c * 20 * s + nx * 6 * s, y + sn * 20 * s + ny * 6 * s), (x + c * 26 * s + nx * 3 * s, y + sn * 26 * s + ny * 3 * s),
                    (x + c * 26 * s - nx * 3 * s, y + sn * 26 * s - ny * 3 * s), (x + c * 20 * s - nx * 6 * s, y + sn * 20 * s - ny * 6 * s)], ACO2)
    if carga:
        rng = np.random.default_rng(9)
        for k in range(12):
            gx = x + c * (4 + rng.random() * 12) * s + nx * (rng.random() - .5) * 12 * s
            gy = y + sn * (4 + rng.random() * 12) * s + ny * (rng.random() - .5) * 12 * s - 2
            grao(tela, gx, gy, k % 2)
        for k in range(3):
            feijao(tela, x + c * (6 + k * 4) * s + nx * (k - 1) * 4 * s, y + sn * (6 + k * 4) * s - 4, .9 * s)


# ============================================================ gancho
class Gancho(Cena):
    def desenhar(self, tela, t, tg):
        if t < 6.0:
            self.mesa(tela, t)
        else:
            self.rota(tela, t - 6.0)

    def mesa(self, tela, t):
        grad_v(tela, 0, 0, W, 70, [NOITE, FUNDO2, FUNDO3])
        grad_v(tela, 0, 70, W, PALCO_H - 70, [MAD1, MAD0, MAD0])
        tela.ret(0, 69, W, 2, PRETO)
        for y in range(84, PALCO_H, 18): tela.ret(0, y, W, 1, MAD0)
        prato(tela, 240, 128, t, falta=fase(t, 2.0, 2.6))
        # o garfo: desce, pega, sobe
        if t < 1.2: x, y = lerp(420, 300, ease(t / 1.2)), lerp(40, 100, ease(t / 1.2))
        elif t < 2.6: x, y = lerp(300, 228, ease((t - 1.2) / 1.4)), lerp(100, 124, ease((t - 1.2) / 1.4))
        else:
            u = ease((t - 2.6) / 2.4)
            x, y = lerp(228, 150, u), lerp(124, 44, u)
        garfo(tela, x, y, -.45 + .25 * fase(t, 2.6, 5), t, carga=t > 2.3, s=1.3)
        if t > 2.6:
            marca(tela, x, y - 4, 'A NOSSA GARFADA', lado=-1, dy=-16)
            brilho_estrela(tela, x + 12, y - 14, t)

    def rota(self, tela, u):
        grade(tela)
        dx = -30
        prog = um(u / 4.6)
        D.corpo(tela, u, atual=None, dx=dx)
        n = int(prog * 120)
        for k in range(n):
            x, y = ao_longo(ROTA, k / 120)
            tela.px(x + dx, y, AMARELO if k % 2 else CHAMA1)
        x, y = ao_longo(ROTA, prog)
        luz(tela, x + dx, y, 2.4, BRANCO, AMARELO, CHAMA1)
        self.rot(tela, 'ENTRA AQUI', 170, 30, AMARELO, alvo=(122, 37))
        if prog >= 1:
            self.rot(tela, 'SAI LÁ NO FIM', 170, 190, AMARELO, alvo=(122, 204))
        if u > .6: tela.texto('QUANTOS METROS?', 330, 80, BRANCO, tam=17, centro=True, contorno=PRETO)
        if u > 1.6: tela.texto('QUANTAS HORAS?', 330, 108, AMARELO, tam=17, centro=True, contorno=PRETO)

    def sons(self, fx):
        fx.put(tique(1800, .05, .01), self.t0 + 2.3, .25)
        fx.put(tique(2400, .05, .01), self.t0 + 2.45, .2)
        for k in range(10):
            fx.put(D_blip(fx, 76 + k), self.t0 + 6.0 + k * .46, .1)


def D_blip(fx, m):
    return fx.blip(m, .06)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        rng = np.random.default_rng(2)
        for k in range(36):
            x = rng.random() * W; v = 20 + rng.random() * 30
            y = (rng.random() * 220 + t * v) % 220 - 10
            if k % 4 == 0: feijao(tela, x, y, .9)
            else: grao(tela, x, y, k % 2)
        tela.texto('SÉRIE A JORNADA', W // 2, 18, ACO3, tam=9, centro=True, contorno=PRETO)
        n = int(t / .045)
        for j, linha in enumerate(("A JORNADA DE", "UMA GARFADA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 12)]
            tela.texto(vis, W // 2 - larg // 2, 38 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto('PELO CORPO', W // 2, 112, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - NE * 22 // 2 + k * 22
                c = cor if t > 2.0 + k * .35 else FUNDO2
                tela.ret(x, 140, 18, 16, PRETO); tela.ret(x + 1, 141, 16, 14, c)
                tela.texto(str(k + 1), x + 9, 144, PRETO, tam=9, centro=True)
        y = 176 - abs(math.sin(t * 3.2)) * 14
        garfada(tela, W // 2, y, 1.5, t, 'bolo')

    def sons(self, fx):
        for k in range(NE):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 12)[k], .08), self.t0 + 2.0 + k * .35, .14)


# ============================================================ a garfada (close)
class Prato(Cena):
    def preparar(self):
        rng = np.random.default_rng(11)
        self.graos = []
        for k in range(34):
            a = rng.random() * 6.28; r = math.sqrt(rng.random())
            self.graos.append((math.cos(a) * r * 40, math.sin(a) * r * 17 - 6, rng.random() * 3.1, rng.random()))
        self.feijoes = [(-20, 6, .3), (8, 10, 1.2), (28, -2, .7), (-4, -14, 2.0), (36, 14, 2.6)]

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 294, PALCO_H, [NOITE, FUNDO2, FUNDO])
        cx, cy = 132 + math.sin(t * .8) * 3, 104 + math.sin(t * 1.3) * 2
        # garfo grande
        garfo(tela, cx - 10, cy + 20, .55, t, carga=False, s=2.2)
        # a carga: feijões por baixo, grãos por cima
        for fx_, fy, a in self.feijoes:
            c, s = math.cos(a), math.sin(a)
            f = tubo([(cx + fx_ - c * 5, cy + fy - s * 5), (cx + fx_ + c * 5, cy + fy + s * 5)], 6.5)
            f.pintar(tela, [FEI0, FEI1, FEI2])
            tela.px(cx + fx_ - 2, cy + fy - 3, ARROZ1); tela.px(cx + fx_ - 1, cy + fy - 3, ARROZ1)
        for gx, gy, a, v in self.graos:
            c, s = math.cos(a), math.sin(a)
            f = tubo([(cx + gx - c * 3.2, cy + gy - s * 3.2), (cx + gx + c * 3.2, cy + gy + s * 3.2)], 3.0)
            f.pintar(tela, [ARROZ0, ARROZ1, ARROZ1, CERAMICA], contorno=QUI0)
        vapor(tela, cx - 20, cy - 30, t, 4, 40)
        brilho_estrela(tela, cx + 52, cy - 34, t)
        # rótulos e zoom
        if t > 6.6:
            gx, gy = self.graos[3][0] + cx, self.graos[3][1] + cy
            self.rot(tela, 'ARROZ', 20, 40, ARROZ1, alvo=(gx, gy))
            if t < 18.4: self.zoom_amido(tela, 8, 140, t - 6.6)
        if t > 12.6:
            fx_, fy, _ = self.feijoes[3]
            self.rot(tela, 'FEIJÃO', 220, 40, FEI2, alvo=(cx + fx_, cy + fy))
            self.zoom_feijao(tela, 196, 120, t - 12.6)
        if t > 18.4:
            self.dupla(tela, t - 18.4)
        est = ('A GARFADA AGORA', 'NO GARFO', AMARELO)
        self.painel(tela, t, cab=('ANTES DA', 'VIAGEM', AMARELO),
                    linhas=[('ARROZ', 'AMIDO', ARROZ1), ('FEIJÃO', 'PROTEÍNA, FIBRA', FEI2)], estado=est,
                    selo='A GARFADA')

    def zoom_amido(self, tela, x, y, u):
        if VERTICAL: return
        inset(tela, x, y, 92, 50, 'AMIDO', ARROZ1)
        n = 7
        for k in range(n):
            px_ = x + 12 + k * 11
            py_ = y + 30 + math.sin(k * 1.3 + u * 2) * 3
            if k < n - 1: tela.linha(px_, py_, px_ + 11, y + 30 + math.sin((k + 1) * 1.3 + u * 2) * 3, ARROZ0)
            glicose(tela, px_, py_, ARROZ1)
        tela.texto('MUITOS AÇÚCARES', x + 6, y + 40, ACO3, tam=9)

    def zoom_feijao(self, tela, x, y, u):
        if VERTICAL: return
        inset(tela, x, y, 94, 70, None, FEI2)
        itens = [('PROTEÍNA', VERDE), ('FERRO', ACO3), ('FIBRA', ARROZ0)]
        for k, (nm, cor) in enumerate(itens):
            if u < k * .8: continue
            yy = y + 8 + k * 20
            if k == 0:
                for j in range(4): aminoacido(tela, x + 10 + j * 5, yy + 4, VERDE if j % 2 else CIANO)
            elif k == 1:
                tela.disco(x + 16, yy + 4, 4, PRETO); tela.disco(x + 16, yy + 4, 3, ACO2); tela.px(x + 15, yy + 3, BRANCO)
            else:
                for j in range(3): tela.linha(x + 8 + j * 3, yy + 8, x + 22 + j * 3, yy, ARROZ0)
            tela.texto(nm, x + 32, yy + 1, cor, tam=9, contorno=PRETO)

    def dupla(self, tela, u):
        """Arroz + feijão: as duas metades dos aminoácidos essenciais se completam."""
        if VERTICAL: return
        x0, y0 = 70, 186
        cores = [VERDE, CIANO, AMARELO, ROSA, ROXO, LARANJA, MUC3, BILE2, ACO4]
        j = ease(u / 2.0)
        for k, c in enumerate(cores):
            de_arroz = k % 2 == 0
            xs = x0 + k * 16
            xi = xs + (-40 if de_arroz else 40) * (1 - j)
            aminoacido(tela, xi, y0, c)
        if j >= 1:
            tela.texto('COMPLETO!', x0 + 64, y0 - 14, VERDE, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.sino(79, .8), self.t0 + 6.7, .14)
        fx.put(fx.sino(76, .8), self.t0 + 12.7, .14)
        fx.put(fx.sino(84, 1.0), self.t0 + 20.4, .16)


# ============================================================ o mapa
ORG_ROT = [  # (etapa, texto, x, y, alvo) — o fio vai até o órgão
    (0, 'BOCA', 12, 30, (142, 37)),
    (2, 'ESÔFAGO', 12, 58, (147, 62)),
    (3, 'ESTÔMAGO', 214, 84, (176, 100)),
    (4, 'INT. DELGADO', 6, 158, (132, 160)),
    (5, 'INT. GROSSO', 214, 150, (184, 150)),
    (6, 'SAÍDA', 214, 196, (149, 204)),
]
AJ_ROT = [('FÍGADO', 12, 96, (118, 102)), ('VESÍCULA', 12, 118, (132, 114)), ('PÂNCREAS', 214, 120, (176, 122))]


def etapa_de_u(u):
    k = 0
    for i in range(NE):
        if u >= U_ETAPA[i] - 1e-6: k = i
    return k


class Mapa(Cena):
    K, VX = 0, 147

    def u(self, t): return ease(fase(t, .5, 18.0) ** .8)

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 294)
        u = self.u(t)
        k = etapa_de_u(u)
        D.corpo(tela, t, atual=['boca', 'garganta', 'esofago', 'estomago', 'delgado', 'grosso', 'saida'][k])
        for j in range(int(u * 160)):
            x, y = ao_longo(ROTA, j / 160)
            if j % 3 == 0: tela.px(x, y, AMARELO)
        x, y = ao_longo(ROTA, u)
        garfada(tela, x, y, .7, t, 'bolo' if k < 3 else ('quimo' if k < 5 else 'resto'), prota=True)
        for e, txt, lx, ly, alvo in ORG_ROT:
            if k >= e: self.rot(tela, f"{e + 1} {txt}", lx, ly, ETAPAS[e][1], alvo=alvo)
        if 12.6 < t < 18.4 or t > 18.4 and not VERTICAL:
            pisca = 12.6 < t < 18.4 and int(t * 3) % 2
            for txt, lx, ly, alvo in AJ_ROT:
                self.rot(tela, txt, lx, ly, AMARELO if pisca else ACO3, alvo=alvo)
        self.K = k
        self.painel(tela, t, linhas=[('COMEÇA NA', 'BOCA', MUC3), ('TERMINA NA', 'SAÍDA', ACO3)],
                    estado=('A GARFADA ESTÁ', ['NA BOCA', 'ENGOLINDO', 'DESCENDO', 'NO ESTÔMAGO', 'NO DELGADO', 'NO GROSSO', 'SAINDO'][k], AMARELO))

    def sons(self, fx):
        ant = -1
        for i in range(int(self.dur * 10)):
            t = i / 10
            k = etapa_de_u(self.u(t))
            if k != ant:
                fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 12)[k], .08), self.t0 + t, .14)
                ant = k


# ============================================================ 1 boca (perfil, em corte)
JANELA_BOCA = [(116, 52), (248, 50), (262, 66), (262, 82), (254, 92), (256, 130), (226, 150), (196, 156),
               (176, 208), (108, 208), (110, 120)]


class Boca(Cena):
    K, VX = 0, 178

    def abre(self, t):
        if t < .4: return 0.0
        if t < 3.4: return .9 * um((t - .4) / .5) * (1 - um((t - 2.9) / .5)) + .1
        if t < 25.2: return .5 - .5 * math.cos(2 * math.pi * (t - 3.4) / .8)
        return .05

    def pos_bolo(self, t):
        if t < 2.6:
            u = ease(um((t - .5) / 2.1))
            return lerp(300, 232, u), 96, 'inteira'
        if t < 4.0:
            u = ease((t - 2.6) / 1.4)
            return lerp(232, 210, u), 96, 'inteira'
        if t < 25.4: return 210, 96, 'bolo'
        if t < 31.4:
            u = ease((t - 25.4) / 3.0)
            return lerp(210, 196, u), lerp(96, 98, u), 'bolo'
        u = ease((t - 31.4) / 4.0)
        return lerp(196, 154, u), lerp(98, 104, u), 'bolo'

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 294, PALCO_H, [NOITE, FUNDO2, FUNDO])
        ab = self.abre(t)
        dy = ab * 9
        # cabeça (manequim) e pescoço
        cab = guardado('boca_cab', lambda: poli([(34, -6), (238, -6), (246, 30), (250, 46), (270, 66), (270, 74), (254, 78),
                                                    (256, 90), (248, 93), (150, 94), (112, 132), (80, 150), (36, 118), (24, 50)]))
        pintar(tela, cab.ox, cab.oy, cab.m, volume(cab), C_PELE, PRETO)
        pes = guardado('boca_pes', lambda: poli([(80, 120), (180, 136), (186, 210), (76, 210)]))
        pintar(tela, pes.ox, pes.oy, pes.m, volume(pes), C_PELE, PRETO)
        mand = poli([(150, 96 + dy * .3), (248, 96 + dy), (254, 100 + dy), (254, 112 + dy), (246, 118 + dy), (250, 132 + dy),
                     (240, 146 + dy), (200, 152 + dy * .6), (172, 148), (150, 120)])
        pintar(tela, mand.ox, mand.oy, mand.m, volume(mand), C_PELE, PRETO)
        # orelha (só para ler como cabeça)
        tela.anel(92, 80, 9, PELE0, 1.2); tela.anel(92, 80, 7, PELE1)
        # janela do corte
        jan = poli([(116, 52), (246, 50), (256, 66), (256, 80), (250, 92), (252 , 100 + dy), (250, 128 + dy),
                    (224, 148 + dy * .6), (196, 154), (178, 208), (108, 208), (110, 120)])
        pintar(tela, jan.ox, jan.oy, jan.m, volume(jan, amp=.5), [MUC0, MUC1, MUC1], PRETO)
        # cavidade do nariz e palato
        poligono(tela, [(124, 58), (236, 56), (246, 70), (240, 76), (126, 78)], CAV1)
        pal = [(124, 80), (238, 78), (240, 84), (150, 88), (126, 92)]
        poligono(tela, pal, PELE3)
        tela.linha(126, 92, 238, 84, ARROZ0)
        # palato mole e úvula
        uv = tubo([(126, 88), (116, 98), (114, 106)], [4, 3, 2.4])
        uv.pintar(tela, C_MUC)
        # boca (cavidade) e faringe
        poligono(tela, [(130, 92), (240, 86), (250, 92 + dy * .5), (246, 102 + dy), (200, 112 + dy * .7), (140, 118)], CAV0)
        far = tubo([(118, 100), (122, 140), (130, 210)], [8, 7, 6])
        pintar(tela, far.ox, far.oy, far.m, .2, [CAV0], MUC0)
        # língua
        ly = 110 + dy * .6
        bomb = math.sin(math.pi * fase(t, 25.4, 31.0)) * 4 if 25.4 < t < 31.4 else 0
        emp = fase(t, 31.4, 34.0)
        lin = tubo([(236 - emp * 8, ly), (200, ly - 3 - bomb), (166, ly - 2 + emp * 2), (148, ly + 12)], [6, 11, 12, 10])
        lin.pintar(tela, [MUC1, MUC2, MUC3])
        # dentes: de cima fixos, de baixo descem com a mandíbula
        self.dentes(tela, 92, False)
        self.dentes(tela, 98 + dy, True)
        # glândulas salivares (desenho por cima, como raio-X)
        self.glandula(tela, 76, 104, t, 'par')
        self.glandula(tela, 184, 140 + dy * .4, t, 'sub')
        # saliva andando pelos dutos
        if t > 12.0 or 4 < t < 25:
            for k in range(3):
                u = ((t * .7 + k / 3) % 1.0)
                if t > 12.8 or k == 0:
                    gotinha(tela, lerp(84, 206, u), lerp(100, 88, u) - math.sin(u * math.pi) * 8)
                    gotinha(tela, lerp(184, 226, u), lerp(136, 106 + dy * .5, u))
        # a garfada
        bx, by, fs = self.pos_bolo(t)
        by += dy * .4 if 4 < t < 25.4 else 0
        q = um((t - 4) / 16)
        if fs == 'inteira':
            garfada(tela, bx, by, 1.4, t, 'bolo', molhado=0, quebra=0)
        else:
            sc = 1.4 - .4 * q + (.3 * fase(t, 25.4, 29) if t > 25.4 else 0)
            garfada(tela, bx, by - 2, sc, t, 'bolo', molhado=fase(t, 12.8, 17), quebra=q)
        if t > 25.4: marca(tela, bx, by - 4, 'BOLO ALIMENTAR', lado=-1, dy=-30)
        # rótulos
        if not VERTICAL or True:
            if not (VERTICAL and 6.8 < t < 25.2): self.rot(tela, 'DENTES', 196, 26, BRANCO, alvo=(218, 90))
            if t > 12.8: self.rot(tela, 'GLÂNDULA SALIVAR', 12, 140, PAN2, alvo=(70, 110))
            if t > 12.8: self.rot(tela, 'SALIVA', 204, 176, MISTURA2, alvo=(214, 118))
            if t > 25.4 or t < 12.8: self.rot(tela, 'LÍNGUA', 150, 176, MUC3, alvo=(170, ly + 2))
        # zoom (canto de cima)
        ix = self.VX - 88 if VERTICAL else 6
        iy = 18 if VERTICAL else 4
        if 6.8 < t < 12.6: self.arcada(tela, ix, iy, t - 6.8)
        if 12.8 < t < 25.2: self.amilase(tela, ix, iy, t - 12.8)
        est = ('A GARFADA AGORA', 'INTEIRA' if t < 4 else ('TRITURADA' if t < 25.4 else 'BOLO'), QUI2)
        self.painel(tela, t, linhas=[('DENTES (ADULTO)', '32', BRANCO), ('ENZIMA DA SALIVA', 'AMILASE', MISTURA2)],
                    estado=est)

    def dentes(self, tela, y, baixo):
        xs = [(200, 8), (209, 8), (218, 7), (226, 5), (232, 5), (238, 4), (243, 4)]
        for x, w in xs:
            h = 7 if w >= 7 else (8 if w == 5 else 7)
            yy = y if baixo else y - h
            tela.ret(x - 1, yy - 1, w + 1, h + 2, PRETO)
            tela.ret(x, yy, w - 1, h, CERAMICA)
            tela.ret(x, yy, 1, h, BRANCO)
            tela.ret(x + w - 2, yy, 1, h, ARROZ0)
        g = y + 7 if baixo else y - 9
        tela.ret(199, g, 50, 2, MUC2)

    def glandula(self, tela, x, y, t, tipo):
        rng = np.random.default_rng(3 if tipo == 'par' else 5)
        n = 9 if tipo == 'par' else 6
        for k in range(n):
            a = rng.random() * 6.28; r = rng.random() * 8
            tela.disco(x + math.cos(a) * r, y + math.sin(a) * r * 1.2, 4.2, PRETO)
        for k in range(n):
            a = rng.random() * 6.28; r = rng.random() * 8
        rng = np.random.default_rng(3 if tipo == 'par' else 5)
        for k in range(n):
            a = rng.random() * 6.28; r = rng.random() * 8
            cx, cy = x + math.cos(a) * r, y + math.sin(a) * r * 1.2
            tela.disco(cx, cy, 3.2, PAN1)
            tela.px(cx - 1, cy - 1, PAN2)
        alvo = (206, 88) if tipo == 'par' else (226, 106)
        for k in range(0, 24, 2):
            u = k / 24
            tela.px(lerp(x + 6, alvo[0], u), lerp(y - 4, alvo[1], u) - math.sin(u * math.pi) * (8 if tipo == 'par' else 0), PAN2)

    def arcada(self, tela, x, y, u):
        """A arcada vista de cima: 16 dentes em cima (x2 = 32)."""
        inset(tela, x, y, 108, 70, '32 DENTES', BRANCO)
        cx, cy = x + 54, y + 62
        for k in range(16):
            a = math.pi * (k + .5) / 16
            px_ = cx - math.cos(a) * 40
            py_ = cy - math.sin(a) * 46
            frente = 5 <= k <= 10
            atras = k <= 2 or k >= 13
            w = 3 if frente else (5 if atras else 4)
            cor = AMARELO if (frente and int(u * 2) % 2 == 0 and u < 3) else (MISTURA2 if atras and u > 3 else CERAMICA)
            tela.ret(px_ - w // 2 - 1, py_ - 3, w + 2, 6, PRETO)
            tela.ret(px_ - w // 2, py_ - 2, w, 4, cor)
        tela.texto('FRENTE', cx, cy - 34, ACO3, tam=9, centro=True)

    def amilase(self, tela, x, y, u):
        """A amilase (pac-man) cortando a corrente de amido."""
        inset(tela, x, y, 108, 52, 'AMILASE + AMIDO', MISTURA2)
        n = 7
        corte = int(um((u - 6.2) / 5.0) * 4) if u > 6.2 else 0
        cortes = [1, 3, 5, 2][:corte]
        off = 0
        for k in range(n):
            if k in cortes: off += 4
            px_ = x + 12 + k * 12 + off
            py_ = y + 32 + math.sin(k + u * 2) * 2
            if k < n - 1 and (k + 1) not in cortes:
                tela.linha(px_, py_, px_ + 12, y + 32 + math.sin(k + 1 + u * 2) * 2, ARROZ0)
            glicose(tela, px_, py_, ARROZ1)
        if u > 6.2:
            alvo = [1, 3, 5, 2][min(3, corte)]
            ax = x + 12 + alvo * 12 + math.sin(u * 3) * 3
            m = abs(math.sin(u * 10)) * .9
            tela.disco(ax, y + 20, 4.5, PRETO); tela.disco(ax, y + 20, 3.5, CIANO)
            poligono(tela, [(ax, y + 20), (ax + 5, y + 20 - 4 * m), (ax + 5, y + 20 + 4 * m)], PRETO)

    def sons(self, fx):
        t = 3.4
        while t < 25.2:
            fx.put(tique(260, .07, .02), self.t0 + t + .4, .16)
            fx.put(tique(1300 + (int(t * 7) % 3) * 160, .03, .006), self.t0 + t + .42, .08)
            t += .8
        fx.put(fx.chiado(8.0, 2000, 5000), self.t0 + 13.0, .025)
        fx.put(varre(300, 520, .35), self.t0 + 25.6, .1)


# ============================================================ 2 engolir (garganta em perfil)
class Engolir(Cena):
    K, VX = 1, 160

    def fecha(self, t):          # 0 epiglote em pé, 1 dobrada sobre a laringe
        return suave(fase(t, 7.4, 9.6)) * (1 - suave(fase(t, 19.0, 21.0)))

    def palato(self, t):         # 1 = palato mole levantado (fecha o nariz)
        return suave(fase(t, 6.0, 7.6)) * (1 - suave(fase(t, 18.0, 19.6)))

    def pos_bolo(self, t):       # a garfada
        if t < 6.0:
            u = ease(fase(t, .5, 6.0))
            return lerp(232, 166, u), lerp(42, 46, u)
        if t < 12.4:
            u = suave(fase(t, 6.0, 12.4))
            return lerp(166, 128, u), lerp(46, 104, u) - math.sin(u * math.pi) * 6
        if t < 18.4:
            u = suave(fase(t, 12.4, 18.4))
            return 128, lerp(104, 176, u)
        u = fase(t, 18.4, 23.0)
        return 128, lerp(176, 236, u)

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 294, PALCO_H, [NOITE, FUNDO2, FUNDO])
        sil = guardado('eng_sil', lambda: poli([(20, -6), (272, -6), (278, 40), (264, 66), (244, 74), (232, 100), (226, 126),
                                                 (216, 142), (216, 212), (60, 212), (50, 120), (20, 60)]))
        pintar(tela, sil.ox, sil.oy, sil.m, volume(sil), C_PELE, PRETO)
        jan = guardado('eng_jan', lambda: poli([(60, -6), (262, -6), (266, 40), (252, 62), (230, 96), (222, 128), (208, 144),
                                                 (208, 212), (70, 212), (64, 120)]))
        pintar(tela, jan.ox, jan.oy, jan.m, volume(jan, amp=.4), [MUC0, MUC1, MUC1], PRETO)
        fe, pa = self.fecha(t), self.palato(t)
        # céu da boca, nariz
        poligono(tela, [(102, -6), (262, -6), (264, 10), (150, 16), (104, 16)], CAV1)
        poligono(tela, [(146, 12), (262, 8), (262, 16), (150, 20)], PELE3)
        # boca e faringe (cavidade)
        poligono(tela, [(148, 20), (256, 16), (256, 38), (236, 58), (150, 60)], CAV0)
        poligono(tela, [(100, 16 if pa < .5 else 18), (148, 22), (152, 100), (204, 112), (204, 126), (172, 128),
                        (142, 130), (106, 130), (100, 60)], CAV0)
        # palato mole: desce (respirando) ou sobe e fecha o nariz
        ang = lerp(2.3, 3.0, pa)
        px_, py_ = 148, 20
        tip = (px_ + math.cos(ang) * 30, py_ + math.sin(ang) * 30 * lerp(1, .2, pa))
        pm = tubo([(px_, py_), ((px_ + tip[0]) / 2, (py_ + tip[1]) / 2 + 2), tip], [6, 5, 3])
        pm.pintar(tela, C_MUC)
        # língua
        lin = tubo([(250, 44), (214, 38 - 4 * fase(t, .5, 6) * (1 - fase(t, 7, 9))), (178, 58), (168, 92), (178, 108)],
                   [10, 16, 17, 14, 9])
        lin.pintar(tela, [MUC1, MUC2, MUC3])
        # traqueia (frente) com anéis e esôfago (atrás)
        tr = guardado('eng_tr', lambda: tubo([(186, 126), (186, 214)], 15))
        pintar(tela, tr.ox, tr.oy, tr.m, tr.cilindro(), [ACO0, CERAMICA, ARROZ1], PRETO)
        for y in range(132, 210, 7):
            tela.ret(173, y, 27, 2, ARROZ0)
        tela.ret(178, 124, 16, 86, CAV0)
        x_bolo, y_bolo = self.pos_bolo(t)
        abre = max(0.0, 1 - abs(y_bolo - 150) / 22) if 12.4 < t else 0.0
        es = tubo([(128, 128), (128, 214)], 12)
        pintar(tela, es.ox, es.oy, es.m, es.cilindro(), C_MUC, PRETO)
        # luz do esôfago: fechada, abre onde passa a garfada
        for y in range(128, 210):
            w = 1 + 7 * max(0.0, 1 - abs(y - y_bolo) / 12) if t > 11 else 1
            tela.ret(128 - w // 2, y, max(1, int(w)), 1, CAV0)
        # ar na traqueia
        if fe < .5:
            ciclo = (t * .6) % 1.0
            sobe = ciclo < .5
            for k in range(3):
                yy = 200 - ((t * 30 + k * 26) % 76) if sobe else 126 + ((t * 30 + k * 26) % 76)
                seta(tela, 186, yy, 0, -1 if sobe else 1, CIANO, 4)
        else:
            tela.linha(180, 150, 192, 162, VERMELHO); tela.linha(192, 150, 180, 162, VERMELHO)
        # epiglote: dobradiça na frente da laringe
        hx, hy = 200, 116
        a = lerp(-1.75, -3.3, fe)
        ep = tubo([(hx, hy), (hx + math.cos(a) * 12, hy + math.sin(a) * 12), (hx + math.cos(a + .2 * fe) * 22, hy + math.sin(a + .2 * fe) * 22)],
                  [4, 3.4, 2.2])
        ep.pintar(tela, [MUC1, MUC3, MUCO])
        # garfada
        garfada(tela, x_bolo, y_bolo, 1.2, t, 'bolo', molhado=1, quebra=1)
        # câmera lenta
        if 5.0 < t < 19.0 and not VERTICAL:
            if int(t * 2) % 2: tela.disco(16, 14, 3, VERMELHO)
            tela.texto('CÂMERA LENTA', 24, 10, BRANCO, tam=9, contorno=PRETO)
        self.rot(tela, 'LÍNGUA', 236, 84, MUC3, alvo=(214, 60))
        self.rot(tela, 'EPIGLOTE', 226, 104, AMARELO if 6.4 < t < 19 else MUCO,
                 alvo=(hx + math.cos(a) * 14, hy + math.sin(a) * 14))
        self.rot(tela, 'TRAQUEIA: AR', 214, 186, CIANO, alvo=(198, 176))
        self.rot(tela, 'ESÔFAGO: COMIDA', 30, 186, QUI2, alvo=(116, 176))
        self.painel(tela, t, linhas=[('CANO DO AR', 'FECHADO' if fe > .5 else 'ABERTO', VERMELHO if fe > .5 else VERDE),
                                     ('QUEM FECHA', 'EPIGLOTE', CIANO)],
                    estado=('A GARFADA AGORA', 'BOLO', QUI2))

    def sons(self, fx):
        fx.put(varre(420, 180, .5), self.t0 + 7.6, .16)
        fx.put(grave(80, .3, .08), self.t0 + 9.4, .3)
        fx.put(varre(200, 120, .8), self.t0 + 13.0, .12)
        fx.put(fx.chiado(3.0, 300, 1200), self.t0 + 1.0, .04)
        fx.put(fx.chiado(3.0, 300, 1200), self.t0 + 20.6, .04)


# ============================================================ 3 esôfago (no ritmo)
ESO_Y0, ESO_Y1 = 10, 168          # 0 cm e 25 cm


class Esofago(Cena):
    K, VX = 2, 147

    def preparar(self):
        self.kicks = [k for k in self.batidas('kick') if k >= .4]
        if len(self.kicks) < 20:
            self.kicks = [.5 + .5 * i for i in range(58)]

    def n_kicks(self, t):
        return sum(1 for k in self.kicks if k <= t)

    def ybolo(self, t):
        """A garfada desce um passo a cada bumbo (o aperto empurra)."""
        n = 0; frac = 0.0
        for k in self.kicks:
            if k <= t:
                n += 1
                frac = ease(um((t - k) / .3))
        n = max(0, n - 1) + frac if n else 0.0
        y = ESO_Y0 + n * 4.0
        if y >= ESO_Y1 - 6:
            y = ESO_Y1 - 6
            t_che = self.t_chegada()
            if t > t_che + .8:
                y = lerp(ESO_Y1 - 6, 212, ease(fase(t, t_che + .8, t_che + 3.0)))
        return y

    def t_chegada(self):
        n = int((ESO_Y1 - 6 - ESO_Y0) / 4.0) + 1
        return self.kicks[min(len(self.kicks) - 1, n)] if self.kicks else 20.0

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, seed=3, t=t)
        # costelas ao fundo
        for k in range(6):
            y = 20 + k * 30
            for sx in (-1, 1):
                for j in range(40):
                    u = j / 39
                    x = 147 + sx * (24 + u * 90)
                    yy = y + math.sin(u * 2.4) * 16
                    tela.px(x, yy, TRACO); tela.px(x, yy + 1, FUNDO3)
        yb = self.ybolo(t)
        tq = self.t_chegada()
        ab_esf = suave(fase(t, tq + .2, tq + 1.0)) * (1 - suave(fase(t, tq + 3.4, tq + 4.4)))
        desde = self.L.desde('kick', self.t0 + t) if t < tq + .4 else 9.0
        aperto = math.exp(-desde / .14) if desde < 1 else 0.0
        # o tubo (vertical): parede de músculo com anéis; luz fechada, abre na garfada
        yy, xx = np.mgrid[0:PALCO_H, 100:195].astype(np.float32)
        dx = xx - 147.0
        r_ext = 15 + 4 * np.exp(-((yy - yb) / 10) ** 2)
        anel_y = yb - 13
        r_ext = r_ext - (4 + 3 * aperto) * np.exp(-((yy - anel_y) / 5) ** 2)
        r_ext = np.where(yy > ESO_Y1, 15 - 6 * (1 - ab_esf) * np.exp(-((yy - ESO_Y1 - 4) / 5) ** 2), r_ext)
        dn = np.abs(dx) / r_ext
        m = dn < 1
        lado = np.sign(dx)
        val = .12 + .78 * np.sqrt(np.clip(1 - dn * dn, 0, 1)) - .2 * lado * dn
        val = val + .12 * (((yy + 0) % 4) < 1)
        pintar(tela, 100, 0, m, np.clip(val, 0, 1), C_MUC, PRETO)
        # luz (lúmen)
        r_in = 1.2 + 7.5 * np.exp(-((yy - yb) / 8) ** 2)
        r_in = np.where(yy > ESO_Y1, 1.2 + 6 * ab_esf, r_in)
        mi = (np.abs(dx) < r_in) & m
        pintar(tela, 100, 0, mi, .3, [CAV0, MUC0], None)
        # o anel que aperta (brilha na batida)
        if t < tq + .6:
            cor = MUCO if aperto > .4 else MUC3
            for sx in (-1, 1):
                for k in range(3):
                    x = 147 + sx * (13 - 3 * aperto + k)
                    tela.ret(x, anel_y - 2, 1, 5, cor if k == 0 else MUC2)
                seta(tela, 147 + sx * (24 - 3 * aperto), anel_y, -sx, 0, AMARELO if aperto > .3 else ACO2, 4)
        # estômago lá embaixo
        st = guardado('eso_st', lambda: tubo([(147, 176), (190, 196), (240, 214)], [16, 30, 34]))
        pintar(tela, st.ox, st.oy, st.m, st.cilindro(), C_MUC, PRETO)
        tela.ret(140, 182, 14, 2, MUC0)
        if yb < 214:
            garfada(tela, 147, yb, 1.15, t, 'bolo', molhado=1, quebra=1)
        # régua
        if not VERTICAL or True:
            rx = 72
            tela.ret(rx, ESO_Y0, 2, ESO_Y1 - ESO_Y0 + 1, ACO2)
            for c in range(0, 26):
                y = ESO_Y0 + c * (ESO_Y1 - ESO_Y0) / 25
                w = 6 if c % 5 == 0 else 3
                tela.ret(rx - w, int(y), w, 1, ACO3 if c % 5 == 0 else ACO1)
                if c % 5 == 0: tela.texto(str(c), rx - 8, int(y) - 3, ACO3, tam=9, centro='d')
            tela.texto('CM', rx - 8, ESO_Y1 + 6, ACO2, tam=9, centro='d')
            cm = um((min(yb, ESO_Y1) - ESO_Y0) / (ESO_Y1 - ESO_Y0)) * 25
            ym = min(yb, ESO_Y1)
            seta(tela, rx + 6, int(ym), -1, 0, AMARELO, 4)
            tela.texto(f"{int(round(cm))} CM", rx + 10, int(ym) - 3, AMARELO, tam=9, contorno=PRETO)
        # rótulos
        mostra_anel = 6.0 < t < tq + .4
        if not mostra_anel or anel_y > 70: self.rot(tela, 'ESÔFAGO', 196, 24, MUC3, alvo=(160, 30))
        if mostra_anel:
            self.rot(tela, 'ANEL APERTA', 200, max(8, anel_y - 24), AMARELO, alvo=(164, anel_y - 2))
        if t > tq - 2:
            self.rot(tela, 'ESFÍNCTER', 200, 150, MUCO if ab_esf > .3 else ACO3, alvo=(162, ESO_Y1 + 3))
            self.rot(tela, 'ESTÔMAGO', 210, 190, ACI1, alvo=(200, 200))
        nb = min(self.n_kicks(t), self.n_kicks(tq))
        if 11.6 < t < tq + 1 and not VERTICAL:
            # pulsa no bumbo
            r = 7 + 3 * aperto
            tela.disco(258, 60, r + 1, PRETO); tela.disco(258, 60, r, AMARELO if aperto > .3 else LARANJA)
            tela.texto('BUM', 258, 76, AMARELO, tam=9, centro=True, contorno=PRETO)
        if t > tq + 5.0 and not VERTICAL:
            # a próxima garfada já vem descendo
            garfada(tela, 147, ESO_Y0 + (t - tq - 5.0) * 8, .9, t, 'bolo', prota=False)
        self.painel(tela, t, linhas=[('TAMANHO', 'UNS 25 CM', MUC3), ('TEMPO (BOCA AO ESTÔMAGO)', '4 A 8 S', AMARELO)],
                    estado=('APERTOS NO RITMO', str(nb), AMARELO))

    def sons(self, fx):
        tq = self.t_chegada()
        for k in self.kicks:
            if k <= tq: fx.put(grave(60, .16, .04), self.t0 + k, .18)
        fx.put(tique(500, .08, .02), self.t0 + tq + .3, .2)
        fx.put(varre(260, 110, .6), self.t0 + tq + 1.0, .14)


# ============================================================ 4 estômago
EST_SP = [(96, 46), (104, 80), (124, 116), (162, 146), (210, 154), (250, 140), (272, 122), (300, 114)]
EST_R = [40, 52, 54, 46, 34, 18, 9, 7]
NIVEL = 84


class Estomago(Cena):
    K, VX = 3, 160

    def preparar(self):
        rng = np.random.default_rng(15)
        self.bolhas = [(rng.random(), rng.random(), 2 + rng.random() * 3) for _ in range(18)]
        self.cadeias = [(170 + rng.random() * 40, 110 + rng.random() * 30) for _ in range(3)]

    def onda(self, t):
        """Posição (0..1 do eixo) da onda de mistura: uma por compasso de 2,4 s."""
        return .25 + .75 * ((t / 2.4) % 1.0)

    def campo(self, t):
        sw = self.onda(t)
        P = np.array(EST_SP, np.float32)
        segs = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
        S = np.concatenate([[0], np.cumsum(segs)]) / segs.sum()
        R = [r * (1 - .22 * math.exp(-((s - sw) / .06) ** 2)) * (1 + .015 * math.sin(t * 2)) for r, s in zip(EST_R, S)]
        return tubo(EST_SP, R)

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, seed=5, t=t)
        # esôfago entrando por cima
        es = guardado('est_eso', lambda: tubo([(132, -8), (130, 30)], 8))
        pintar(tela, es.ox, es.oy, es.m, es.cilindro(), C_MUC, PRETO)
        f = self.campo(t)
        dn = f.dn
        # parede (fora), muco (faixa clara), luz (dentro)
        val = f.cilindro()
        pintar(tela, f.ox, f.oy, f.m, val, C_MUC, PRETO)
        muco = f.m & (dn >= .64) & (dn < .72)
        destaque_muco = 16.2 < t < 21.4 and int(t * 3) % 2 == 0
        pintar(tela, f.ox, f.oy, muco, .5 + .5 * destaque_muco, [MUC3, MUCO], None)
        luz_ = f.m & (dn < .66)
        Y = f.Y
        q = fase(t, 8, 31)                           # o quanto virou quimo
        conteudo = luz_ & (Y > NIVEL + 3 * np.sin(f.X * .08 + t * 2.0))
        ar = luz_ & ~conteudo
        pintar(tela, f.ox, f.oy, ar, np.clip((Y - 30) / 80, 0, 1), [CAV0, CAV1], None)
        cv = np.clip(.35 + .45 * np.sin(f.X * .21 + t) * np.sin(f.Y * .27 - t * .7) * (1 - q) + .3 * q, 0, 1)
        pintar(tela, f.ox, f.oy, conteudo, cv, [QUI0, QUI1, QUI2] if q > .5 else [FEI1, QUI0, QUI1, QUI2], None)
        # pregas (rugas) na parede interna
        for k in range(14):
            u = k / 14
            x, y = ao_longo(EST_SP[:6], u)
            tela.px(x - 2, y + 18, MUC2)
        # bolhas de ácido subindo
        if t > 10.0:
            for k, (a, b, r) in enumerate(self.bolhas):
                x = 100 + a * 140
                y = 170 - ((t * 10 * (1 + b) + b * 80) % 80)
                if y > NIVEL + 4:
                    tela.anel(x, y, 1.6, ACI1); tela.px(x - 1, y - 1, BRANCO)
        # pepsina cortando as proteínas
        if t > 21.4:
            for k, (cx, cy) in enumerate(self.cadeias):
                u = fase(t, 21.4 + k * .6, 26 + k * .6)
                for j in range(5):
                    sep = (j - 2) * (5 + 6 * u)
                    aminoacido(tela, cx + sep + math.sin(t * 2 + j) * .6, cy + math.sin(t + j) * 1.5, VERDE if j % 2 else CIANO)
                ax = cx - 14 + 28 * ((t * .5 + k * .3) % 1.0)
                mm = abs(math.sin(t * 9 + k)) * .9
                tela.disco(ax, cy - 7, 4.2, PRETO); tela.disco(ax, cy - 7, 3.2, ROXO)
                poligono(tela, [(ax, cy - 7), (ax + 5, cy - 7 - 4 * mm), (ax + 5, cy - 7 + 4 * mm)], PRETO)
        # a garfada: cai, boia e se desfaz
        if t < 2.2:
            gx, gy = 131, lerp(-6, 96, ease(t / 2.2))
        else:
            gx, gy = 150 + math.sin(t * .9) * 18, 110 + math.sin(t * .7) * 8
        if t < 26.6:
            garfada(tela, gx, gy, 1.5 - .3 * q, t, 'bolo', molhado=1, quebra=1)
        else:
            garfada(tela, gx, gy, 1.5, t, 'quimo')
        # piloro solta aos poucos
        if t > 31.4:
            for k in range(3):
                u = ((t - 31.4) * .5 + k / 3) % 1.0
                x, y = lerp(266, 300, u), lerp(124, 114, u)
                tela.disco(x, y, 2.4, PRETO); tela.disco(x, y, 1.6, QUI2)
        # rótulos
        self.rot(tela, 'ESÔFAGO', 150, 4, MUC3, alvo=(138, 16))
        if t > 11: self.rot(tela, 'ÁCIDO', 6, 150, ACI1, alvo=(108, 150))
        if t > 16.2: self.rot(tela, 'MUCO', 22, 46, MUCO, alvo=(64, 56))
        if t > 21.4: self.rot(tela, 'PEPSINA', 196, 186, ROXO, alvo=(self.cadeias[0][0] + 4, self.cadeias[0][1] - 6))
        if t > 26.6: marca(tela, gx, gy - 4, 'QUIMO', lado=1, dy=-22)
        self.rot(tela, 'PILORO', 236, 92, ACO3 if t < 31.4 else AMARELO, alvo=(268, 116))
        # tamanho: punho x 4 litros
        if 5.8 < t < 11.0 and not VERTICAL:
            inset(tela, 190, 4, 100, 58, None, ACO3)
            e1 = elipse(212, 36, 8, 10)
            pintar(tela, e1.ox, e1.oy, e1.m, volume(e1), C_MUC, PRETO)
            r = 10 + 10 * suave(fase(t, 7.5, 9.5))
            e2 = elipse(262, 36, r * .8, r)
            pintar(tela, e2.ox, e2.oy, e2.m, volume(e2), C_MUC, PRETO)
            tela.texto('VAZIO', 212, 50, ACO3, tam=9, centro=True, contorno=PRETO)
            tela.texto('4 L', 262, 50, AMARELO, tam=9, centro=True, contorno=PRETO)
        est = 'BOLO' if t < 8 else ('VIRANDO QUIMO' if t < 26.6 else 'QUIMO')
        self.painel(tela, t, linhas=[('TEMPO AQUI (EM GERAL)', '2 A 4 HORAS', AMARELO), ('ACIDEZ', 'PH 1,5 A 3,5', ACI1)],
                    estado=('A GARFADA AGORA', est, QUI2))

    def sons(self, fx):
        fx.put(varre(300, 120, .5), self.t0 + 1.9, .14)
        rng = np.random.default_rng(4)
        t = 10.0
        while t < 36:
            fx.put(varre(600 + rng.random() * 500, 1400 + rng.random() * 600, .06, 0), self.t0 + t, .05)
            t += .25 + rng.random() * .5
        for k in range(15):
            fx.put(grave(55, .5, .2), self.t0 + k * 2.4 + .3, .12)
        for k in range(8):
            fx.put(tique(700, .05, .015), self.t0 + 31.6 + k * .5, .08)


# ============================================================ 5 intestino delgado
def _serp_grande():
    pts = [(-8, 20), (30, 26)]
    linhas = [26, 58, 90, 122, 154, 186]
    for j, y in enumerate(linhas):
        if j % 2 == 0:
            xs = np.linspace(30, 262, 10)
        else:
            xs = np.linspace(262, 30, 10)
        for x in xs: pts.append((float(x), y + math.sin(float(x) * .05 + j) * 3))
    return pts


SERP = _serp_grande()


def reamostrar(pts, n):
    return [ao_longo(pts, k / (n - 1)) for k in range(n)]


class Delgado(Cena):
    K, VX = 4, 147

    def preparar(self):
        self.P = reamostrar(SERP, 140)
        self.Lr = [(lerp(16, 16 + 260 * .8, k / 139), 96.0) for k in range(140)]   # termina em 4 m, no meio da faixa

    def desenrola(self, t):
        return suave(fase(t, 6.8, 8.8)) * (1 - suave(fase(t, 11.6, 13.0)))

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, seed=8, t=t)
        a = self.desenrola(t)
        if a <= 0:
            f = guardado('serp', lambda: tubo(SERP, 12))
            pintar(tela, f.ox, f.oy, f.m, f.cilindro(), C_INT, PRETO)
            # luz em corte: o quimo escorrendo dentro
            dentro = f.m & (f.dn < .42)
            pintar(tela, f.ox, f.oy, dentro, np.clip(.5 + .5 * np.sin(f.s * .25 - t * 5), 0, 1), [QUI0, QUI1, QUI2], None)
            # segmentação: anéis que apertam aqui e ali
            if t > 13:
                for k in range(24):
                    u = (k + .5) / 24
                    p0 = ao_longo(SERP, u)
                    p1 = ao_longo(SERP, min(1, u + .004))
                    vx, vy = p1[0] - p0[0], p1[1] - p0[1]
                    L = math.hypot(vx, vy) or 1
                    nx, ny = -vy / L, vx / L
                    aperta = (math.sin(t * 4 + k * 1.7) > .3) if k % 2 == int(t * 1.6) % 2 else False
                    if aperta:
                        r = 13
                        tela.linha(p0[0] - nx * r, p0[1] - ny * r, p0[0] + nx * r, p0[1] + ny * r, INT0)
                        tela.linha(p0[0] - nx * (r - 1) + vx / L, p0[1] - ny * (r - 1) + vy / L,
                                   p0[0] + nx * (r - 1) + vx / L, p0[1] + ny * (r - 1) + vy / L, INT3)
            # duodeno em destaque
            if 12.8 < t < 18.8:
                for k in range(40):
                    x, y = ao_longo(SERP, k / 40 * .06)
                    if int(t * 4) % 2 == 0: tela.disco(x, y, 2, AMARELO)
                self.rot(tela, 'DUODENO: UNS 25 CM', 40, 44, AMARELO, alvo=(30, 30))
            # a protagonista: quimo andando
            u = .02 + .9 * fase(t, 0, 34) if not (6.6 < t < 13) else .02 + .9 * fase(6.6, 0, 34)
            x, y = ao_longo(SERP, u)
            garfada(tela, x, y, 1.0, t, 'quimo')
            if t > 30.6:
                xe, ye = ao_longo(SERP, 1.0)
                halo(tela, 30, 186, 10 + math.sin(t * 6) * 2, AMARELO)
                self.rot(tela, 'AQUI A DIGESTÃO TERMINA', 60, 168, AMARELO, alvo=(34, 184))
            self.rot(tela, 'DO ESTÔMAGO', 4, 4, ACO3)
        else:
            # desenrolando: o mesmo tubo vira uma linha reta ao lado da régua
            pts = [(lerp(p[0], q[0], a), lerp(p[1], q[1], a)) for p, q in zip(self.P, self.Lr)]
            r = lerp(12, 6, a)
            for x, y in pts[::2]: tela.disco(x, y, r + 1, PRETO)
            for x, y in pts[::2]: tela.disco(x, y, r, INT2)
            for x, y in pts[::2]: tela.disco(x - r * .2, y - r * .35, r * .45, INT3)
            if a > .95:
                # régua de 0 a 5 m, faixa de 3 a 5 m
                x0, x1, yr = 16, 276, 124
                tela.ret(x0, yr, x1 - x0, 2, ACO2)
                for mtr in range(6):
                    x = x0 + (x1 - x0) * mtr / 5
                    tela.ret(int(x), yr - 4, 1, 9, ACO3)
                    tela.texto(f"{mtr} M", int(x), yr + 8, ACO3, tam=9, centro=True, contorno=PRETO)
                xa, xb = x0 + (x1 - x0) * 3 / 5, x1
                tela.ret(int(xa), 140, int(xb - xa), 3, AMARELO)
                tela.texto('3 A 5 METROS', int((xa + xb) / 2), 148, AMARELO, tam=17, centro=True, contorno=PRETO)
                tela.texto('ESTICADO', 147, 60, BRANCO, tam=17, centro=True, contorno=PRETO)
        est = ('A GARFADA AGORA', 'QUIMO', QUI2)
        self.painel(tela, t, linhas=[('TAMANHO', '3 A 5 METROS', INT3), ('TEMPO AQUI (EM GERAL)', '3 A 5 HORAS', AMARELO)],
                    estado=est)

    def sons(self, fx):
        fx.put(varre(200, 500, 1.6), self.t0 + 6.8, .08)
        fx.put(varre(500, 200, 1.2), self.t0 + 11.7, .08)
        rng = np.random.default_rng(6)
        t = 13.5
        while t < 36:
            fx.put(grave(90 + rng.random() * 30, .14, .04), self.t0 + t, .1)
            t += .6 + rng.random() * .6


# ============================================================ fígado, vesícula, pâncreas
FIG_P = [(6, 8), (150, 2), (186, 18), (178, 42), (146, 62), (96, 74), (40, 72), (8, 52)]
DUO_P = [(222, 40), (196, 66), (166, 92), (150, 128), (154, 164), (180, 188), (220, 194), (262, 184), (296, 176)]
PAN_P = [(186, 142), (222, 132), (256, 122), (290, 112)]
BILE_P = [(110, 66), (124, 86), (136, 104), (148, 124), (158, 140)]
CIST_P = [(118, 96), (124, 86)]
PDUTO_P = [(288, 114), (240, 128), (200, 138), (168, 142), (158, 140)]
AMPOLA = (158, 140)


class Ajudantes(Cena):
    K, VX = 4, 150

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, seed=12, t=t)
        st = guardado('aj_st', lambda: tubo([(300, 6), (262, 22), (226, 38)], [30, 22, 10]))
        pintar(tela, st.ox, st.oy, st.m, st.cilindro(), C_MUC, PRETO)
        fg = guardado('aj_fig', lambda: poli(FIG_P))
        pintar(tela, fg.ox, fg.oy, fg.m, volume(fg), C_FIG, PRETO)
        for k in range(5):
            tela.px(40 + k * 22, 24 + (k % 2) * 6, FIG3)
        pan = guardado('aj_pan', lambda: tubo(PAN_P, [17, 13, 10, 6]))
        v = pan.cilindro() + .12 * (np.sin(pan.X * .7) * np.sin(pan.Y * .7) > .3)
        pintar(tela, pan.ox, pan.oy, pan.m, np.clip(v, 0, 1), C_PAN, PRETO)
        du = guardado('aj_duo', lambda: tubo(DUO_P, 13))
        pintar(tela, du.ox, du.oy, du.m, du.cilindro(), C_INT, PRETO)
        dentro = du.m & (du.dn < .45)
        pintar(tela, du.ox, du.oy, dentro, np.clip(.5 + .5 * np.sin(du.s * .3 - t * 4), 0, 1), [QUI0, QUI1, QUI2], None)
        ves = guardado('aj_ves', lambda: tubo([(114, 70), (118, 96)], [7, 11]))
        cheia = 1.0 if t < 12.2 else 1 - .25 * fase(t, 14, 17)
        pintar(tela, ves.ox, ves.oy, ves.m, ves.cilindro() * cheia, C_BILE, PRETO)
        # dutos
        for (ax, ay), (bx, by) in zip(BILE_P, BILE_P[1:]):
            linha_grossa(tela, ax, ay, bx, by, 4, PRETO)
        for (ax, ay), (bx, by) in zip(BILE_P, BILE_P[1:]):
            linha_grossa(tela, ax, ay, bx, by, 2, BILE1)
        for (ax, ay), (bx, by) in zip(PDUTO_P, PDUTO_P[1:]):
            tela.linha(ax, ay, bx, by, PAN0)
        # sucos andando pelos dutos
        if t > 6.4:
            for k in range(5):
                u = (t * .35 + k / 5) % 1.0
                x, y = ao_longo(BILE_P, u)
                gotinha(tela, x, y, BILE2, BILE1)
        if t > 23.8:
            for k in range(5):
                u = (t * .35 + k / 5) % 1.0
                x, y = ao_longo(PDUTO_P, u)
                gotinha(tela, x, y, PAN2, PAN1)
        # nuvenzinha dos sucos entrando no duodeno
        if t > 6.4:
            for k in range(6):
                a = t * 2 + k
                tela.px(AMPOLA[0] - 6 + math.cos(a) * 5, AMPOLA[1] + 4 + math.sin(a) * 4, BILE2 if k % 2 else PAN2)
        # a garfada (quimo) passando pelo duodeno
        u = .1 + .5 * fase(t, 0, 36)
        x, y = ao_longo(DUO_P, u)
        garfada(tela, x, y, .95, t, 'quimo')
        # rótulos
        self.rot(tela, 'FÍGADO', 60, 30, FIG3)
        self.rot(tela, 'VESÍCULA', 30, 104, BILE2, alvo=(110, 92))
        self.rot(tela, 'BILE', 92, 128, BILE2, alvo=(140, 112))
        self.rot(tela, 'PÂNCREAS', 224, 150, PAN2, alvo=(236, 128))
        self.rot(tela, 'DUODENO', 200, 196, INT3, alvo=(196, 190)) if False else self.rot(tela, 'DUODENO', 96, 180, INT3, alvo=(150, 166))
        # caixinha explicando
        if 18.0 < t < 23.8: self.emulsao(tela, 6, 4 + 0, t - 18.0)
        if 29.8 < t: self.enzimas(tela, 6, 4, t - 29.8)
        self.painel(tela, t, linhas=[('BILE (DO FÍGADO)', '1 L POR DIA', BILE2), ('SUCO DO PÂNCREAS', '+ DE 1 L/DIA', PAN2)],
                    estado=('A GARFADA AGORA', 'QUIMO + SUCOS', QUI2))

    def emulsao(self, tela, x, y, u):
        if VERTICAL: return
        inset(tela, x, y, 120, 72, 'GORDURA + BILE', BILE2)
        cx, cy = x + 60, y + 42
        q = ease(um(u / 3.5))
        if q < .5:
            r = 14 * (1 - q * .4)
            tela.disco(cx, cy, r + 1, PRETO); tela.disco(cx, cy, r, CHAMA0); tela.disco(cx - r * .3, cy - r * .3, r * .3, BRANCO)
        n = int(q * 14)
        for k in range(n):
            a = k * 2.4; rr = 6 + (k % 4) * 6 * q
            px_, py_ = cx + math.cos(a + u) * rr * 1.6, cy + math.sin(a + u) * rr * .8
            tela.disco(px_, py_, 3, PRETO); tela.disco(px_, py_, 2, CHAMA0); tela.px(px_ - 1, py_ - 1, BRANCO)
            tela.px(px_ + 3, py_, BILE2)
        tela.texto('GOTINHAS', cx, y + 62, ACO3, tam=9, centro=True)

    def enzimas(self, tela, x, y, u):
        if VERTICAL: return
        inset(tela, x, y, 128, 78, None, PAN2)
        itens = [('AMILASE', 'AMIDO', ARROZ1), ('LIPASE', 'GORDURA', CHAMA0), ('TRIPSINA', 'PROTEÍNA', VERDE)]
        for k, (enz, alvo, cor) in enumerate(itens):
            if u < k * .6: continue
            yy = y + 8 + k * 16
            tela.texto(enz, x + 6, yy, PAN2, tam=9, contorno=PRETO)
            tela.texto('→', x + 62, yy, ACO3, tam=9)
            tela.texto(alvo, x + 74, yy, cor, tam=9, contorno=PRETO)
        # medidor de acidez
        yy = y + 60
        tela.texto('ÁCIDO', x + 6, yy - 1, ACI1, tam=9)
        tela.ret(x + 40, yy + 1, 60, 4, PRETO)
        for i in range(58):
            tela.px(x + 41 + i, yy + 2, ACI1 if i < 20 else (VERDE if i < 40 else CIANO))
            tela.px(x + 41 + i, yy + 3, ACI1 if i < 20 else (VERDE if i < 40 else CIANO))
        p = x + 44 + 30 * ease(um(u / 3))
        seta(tela, int(p), yy - 1, 0, 1, BRANCO, 3)

    def sons(self, fx):
        for k in range(30):
            fx.put(tique(1800 + (k % 4) * 200, .04, .01), self.t0 + 6.6 + k * .35, .04)
        fx.put(fx.sino(81, .8), self.t0 + 18.4, .12)
        for k in range(8):
            fx.put(tique(2400 - k * 90, .03, .008), self.t0 + 19.2 + k * .25, .06)
        for k in range(18):
            fx.put(tique(1400 + (k % 3) * 150, .04, .01), self.t0 + 24.0 + k * .35, .04)


# ============================================================ vilosidades
class Vilosidades(Cena):
    K, VX = 4, 147

    def preparar(self):
        rng = np.random.default_rng(21)
        self.parts = []
        for i in range(26):
            tipo = ['g', 'a', 'w', 'g', 'a', 'f'][i % 6]
            self.parts.append(dict(tipo=tipo, t0=rng.random() * 30, alvo=int(rng.random() * 7), y0=10 + rng.random() * 50,
                                   x0=rng.random() * 294, v=.6 + rng.random() * .5))

    def esc(self, t):
        return lerp(.35, 1.0, suave(fase(t, 5.0, 7.5)))

    def vilos(self, s):
        n = int(round(7 / s))
        larg = 294 / n
        return [((k + .5) * larg, larg) for k in range(n)]

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, cores=(CAV0, CAV1), seed=21, t=t)
        s = self.esc(t)
        base = 192
        h = 116 * s
        # vaso de sangue (veia) embaixo, correndo para a direita
        tela.ret(0, base, 294, PALCO_H - base, SANG0)
        tela.ret(0, base, 294, 2, PRETO)
        for k in range(18):
            x = (k * 23 + t * 30) % 300 - 6
            tela.disco(x, base + 8, 3, PRETO); tela.disco(x, base + 8, 2.2, SANG2); tela.px(x - 1, base + 7, BRANCO)
        vs = self.vilos(s)
        for k, (x, larg) in enumerate(vs):
            sway = math.sin(t * 1.2 + k) * 3 * s
            topo = (x + sway, base - h)
            r = larg * .36
            f = tubo([(x, base + 2), (x + sway * .5, base - h * .5), topo], [r * 1.1, r, r * .95])
            f.pintar(tela, [MUC0, MUC1, MUC2, MUC3])
            # borda em escova (microvilosidades)
            if s > .6:
                for j in range(14):
                    a = math.pi * (j / 13)
                    tela.px(topo[0] - math.cos(a) * (r + 1), topo[1] - math.sin(a) * (r + 1) + 1, MUCO)
            # capilar (sobe vermelho, desce escuro) e o lácteo no meio
            if s > .5:
                for j in range(int(h * .9)):
                    yy = base - j
                    off = r * .5
                    sw = sway * j / h
                    tela.px(x - off + sw, yy, SANG2)
                    tela.px(x + off + sw, yy, SANG1)
                    if j % 2 == 0: tela.px(x + sw, yy, ARROZ1)
                tela.anel(topo[0], topo[1] + r * .5, r * .5, SANG2)
        # partículas: glicose, aminoácidos, água entram; fibra passa reto
        if t > 10 and s > .9:
            for p in self.parts:
                u = ((t - 10) * .09 * p['v'] + p['t0'] / 30) % 1.0
                vx, larg = vs[p['alvo'] % len(vs)]
                if p['tipo'] == 'f':
                    x = (p['x0'] + (t - 10) * 18) % 320 - 10
                    y = p['y0'] + 6
                    for j in range(4):
                        tela.linha(x + j * 3, y, x + 8 + j * 3, y - 4, ARROZ0)
                    continue
                if u < .45:
                    x = lerp(p['x0'], vx, u / .45); y = lerp(p['y0'], base - h - 6, u / .45)
                elif u < .8:
                    w = (u - .45) / .35
                    x = vx + larg * .18; y = lerp(base - h + 4, base + 4, w)
                else:
                    w = (u - .8) / .2
                    x = vx + larg * .18 + w * 60; y = base + 8
                if p['tipo'] == 'g': glicose(tela, x, y)
                elif p['tipo'] == 'a': aminoacido(tela, x, y, VERDE)
                else: gotinha(tela, x, y)
        # rótulos
        if s > .9:
            vx, larg = vs[3]
            self.rot(tela, 'VILOSIDADE', 210, 22, MUC3, alvo=(vs[5][0] - 4, base - h + 4))
            self.rot(tela, 'VASINHOS DE SANGUE', 6, 186, SANG2, alvo=(vs[0][0] - 4, base - 30))
            if 12.2 < t < 24:
                lx = 66 if VERTICAL else 12
                dyv = 8 if VERTICAL else 0
                tela.texto('GLICOSE', lx, 14 + dyv, AMARELO, tam=9, contorno=PRETO); glicose(tela, lx - 6, 17 + dyv)
                tela.texto('AMINOÁCIDOS', lx, 26 + dyv, VERDE, tam=9, contorno=PRETO); aminoacido(tela, lx - 6, 29 + dyv)
                tela.texto('FIBRA: PASSA RETO', lx, 38 + dyv, ARROZ1, tam=9, contorno=PRETO)
            if t > 18: self.rot(tela, 'PARA O FÍGADO →', 196, 178, BRANCO)
        else:
            self.rot(tela, 'PAREDE DO DELGADO', 6, 6, MUC3)
            if 1.0 < t < 6.2:
                x, y = 147, base - h - 10
                for k in range(4):
                    tela.ret_vazado(x - 30 + k * 2, y - 24 + k * 2, 60 - k * 4, 48 - k * 4, AMARELO if int(t * 4) % 2 else ACO3)
                tela.texto('ZOOM', x, y - 34, AMARELO, tam=9, centro=True, contorno=PRETO)
        # área: 30 metros quadrados
        if 23.8 < t < 29.8 and not VERTICAL:
            inset(tela, 150, 4, 140, 82, None, AMARELO)
            n = int(min(30, (t - 23.8) / 3.0 * 30))
            for i in range(30):
                cx_, cy_ = 158 + (i % 10) * 13, 12 + (i // 10) * 13
                tela.ret(cx_, cy_, 11, 11, PRETO)
                tela.ret(cx_ + 1, cy_ + 1, 9, 9, AMARELO if i < n else FUNDO2)
            tela.texto(f"{n} METROS QUADRADOS", 220, 56, AMARELO, tam=9, centro=True, contorno=PRETO)
            tela.texto('1 QUADRADINHO = 1 M X 1 M', 220, 70, ACO3, tam=9, centro=True)
        self.painel(tela, t, linhas=[('ÁREA, EM METROS QUADRADOS', 'UNS 30', AMARELO), ('ÁGUA ABSORVIDA AQUI', 'UNS 90%', MISTURA2)],
                    estado=('A GARFADA AGORA', 'NUTRIENTES', AMARELO))

    def sons(self, fx):
        fx.put(varre(300, 900, 1.8), self.t0 + 5.0, .07)
        rng = np.random.default_rng(8)
        t = 10.5
        while t < 36:
            fx.put(tique(1500 + rng.random() * 800, .04, .01), self.t0 + t, .04)
            t += .3 + rng.random() * .5
        for k in range(30):
            fx.put(fx.blip(76 + (k % 5), .03), self.t0 + 23.8 + k * .1, .04)


# ============================================================ o sangue (veia porta)
PORTA = [(150, 162), (146, 146), (142, 130), (134, 116), (128, 104)]
SISTEMA = [(128, 100), (138, 88), (150, 80)]
LINFA = [(150, 160), (152, 140), (154, 110), (152, 80), (150, 58)]


class Sangue(Cena):
    K, VX = 4, 147

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 294)

        def veias(tl):
            for (ax, ay), (bx, by) in zip(PORTA, PORTA[1:]):
                linha_grossa(tl, ax, ay, bx, by, 4, PRETO)
                linha_grossa(tl, ax, ay, bx, by, 2.4, SANG1)
            if t > 18:
                for (ax, ay), (bx, by) in zip(LINFA, LINFA[1:]):
                    for j in range(0, 12, 3):
                        u = j / 12
                        tl.px(lerp(ax, bx, u), lerp(ay, by, u), CHAMA0)

        D.corpo(tela, t, atual='figado' if 6.4 < t < 18 else None, sangue=veias)
        # nutrientes subindo pela veia porta
        for k in range(8):
            u = (t * .25 + k / 8) % 1.0
            x, y = ao_longo(PORTA, u)
            (glicose if k % 2 else aminoacido)(tela, x, y)
        if t > 6.4:
            halo(tela, 132, 104, 18 + math.sin(t * 5) * 2, FIG3)
        # depois do fígado, para o corpo todo
        if t > 12.2:
            for k in range(14):
                u = ((t - 12.2) * .3 + k / 14) % 1.0
                a = k * 2 * math.pi / 14
                x = 132 + math.cos(a) * u * 70
                y = 104 + math.sin(a) * u * 90
                tela.disco(x, y, 2, PRETO); tela.disco(x, y, 1.3, SANG2)
        if t > 18:
            for k in range(3):
                u = (t * .3 + k / 3) % 1.0
                x, y = ao_longo(LINFA, u)
                tela.disco(x, y, 2.2, PRETO); tela.disco(x, y, 1.5, CHAMA0)
        self.rot(tela, 'VEIA PORTA', 210, 150, SANG2, alvo=(146, 146))
        self.rot(tela, 'FÍGADO', 12, 96, FIG3, alvo=(118, 102))
        if t > 12.2: self.rot(tela, 'CORPO TODO', 214, 70, BRANCO, alvo=(190, 84))
        if t > 18: self.rot(tela, 'LINFA (GORDURA)', 6, 60, CHAMA0, alvo=(152, 80))
        self.painel(tela, t, linhas=[('CAMINHO', 'VEIA PORTA', SANG2), ('PRIMEIRA PARADA', 'FÍGADO', FIG3)],
                    estado=('A GARFADA AGORA', 'NO SANGUE', SANG2))

    def sons(self, fx):
        for k in range(24):
            fx.put(grave(65, .2, .05), self.t0 + .4 + k * 1.0, .1)
            fx.put(grave(55, .2, .05), self.t0 + .7 + k * 1.0, .07)


# ============================================================ 6 intestino grosso
GR_SP = [(52, 214), (48, 180), (44, 120), (48, 56), (70, 32), (146, 26), (222, 32), (244, 56), (246, 140),
         (238, 170), (210, 186), (170, 192), (150, 214)]


def _grosso_forma():
    P = GR_SP
    f = tubo(P, 1.0)       # só para o comprimento
    L = D.comprimento(P)
    # raio com pregas: cada ponto vira vários
    dens = reamostrar(P, 90)
    rs = [22 * (1 + .12 * math.sin(k * 1.1)) for k in range(90)]
    return tubo(dens, rs)


class Grosso(Cena):
    K, VX = 5, 147

    def desenhar(self, tela, t, tg):
        tecido(tela, 0, 294, seed=30, t=t)
        # delgado ao fundo, apagado
        fs = guardado('gr_delg', lambda: tubo([(x * .52 + 70, y * .6 + 52) for x, y in SERP[2:]], 6))
        pintar(tela, fs.ox, fs.oy, fs.m, fs.cilindro() * .5, [INT0, INT1], CAV0)
        f = guardado('gr', _grosso_forma)
        pintar(tela, f.ox, f.oy, f.m, f.cilindro(), [RES0, INT1, INT2, INT3], PRETO)
        # pregas (haustros)
        for k in range(1, 28):
            u = k / 28
            p0 = ao_longo(GR_SP, u); p1 = ao_longo(GR_SP, min(1, u + .005))
            vx, vy = p1[0] - p0[0], p1[1] - p0[1]
            Ls = math.hypot(vx, vy) or 1
            nx, ny = -vy / Ls, vx / Ls
            tela.linha(p0[0] - nx * 20, p0[1] - ny * 20, p0[0] - nx * 12, p0[1] - ny * 12, INT0)
            tela.linha(p0[0] + nx * 20, p0[1] + ny * 20, p0[0] + nx * 12, p0[1] + ny * 12, INT0)
        # conteúdo: de mole (claro) a firme (escuro)
        dentro = f.m & (f.dn < .5)
        S = f.s / max(1.0, float(f.s.max()))
        val = np.clip(1 - S * 1.2 + .15 * np.sin(f.s * .3 - t * 1.5), 0, 1)
        pintar(tela, f.ox, f.oy, dentro, val, [RES0, RES1, QUI1, QUI2], None)
        # água e sais saindo pela parede
        n = 6 if t < 12.2 else 14
        for k in range(n):
            u = (k / n + t * .02) % 1.0
            px_, py_ = ao_longo(GR_SP, u)
            p1 = ao_longo(GR_SP, min(1, u + .005))
            vx, vy = p1[0] - px_, p1[1] - py_
            Ls = math.hypot(vx, vy) or 1
            nx, ny = -vy / Ls, vx / Ls
            sgn = 1 if k % 2 else -1
            w = (t * .6 + k * .37) % 1.0
            d = 6 + w * 26
            gotinha(tela, px_ + nx * d * sgn, py_ + ny * d * sgn)
        # a protagonista: o que sobrou
        u = .05 + .55 * fase(t, 0, 30)
        x, y = ao_longo(GR_SP, u)
        garfada(tela, x, y, 1.2, t, 'resto')
        marca(tela, x, y, 'O QUE SOBROU', lado=1, dy=-22 if y > 60 else 18)
        self.rot(tela, 'INTESTINO GROSSO', 92, 96, PAN2, alvo=(64, 110))
        self.rot(tela, 'DELGADO (ATRÁS)', 104, 64, INT2)
        if t > 12.2: self.rot(tela, 'ÁGUA E SAIS', 196, 92, MISTURA2, alvo=(236, 100))
        est = 'FIBRA E ÁGUA' if t < 12.2 else 'MAIS FIRME'
        self.painel(tela, t, linhas=[('TAMANHO', 'UNS 1,8 M', PAN2), ('TEMPO AQUI (EM GERAL)', '12 H A 2 DIAS', AMARELO)],
                    estado=('A GARFADA AGORA', est, QUI2))

    def sons(self, fx):
        rng = np.random.default_rng(9)
        t = 1.0
        while t < 30:
            fx.put(tique(2200 + rng.random() * 600, .05, .015), self.t0 + t, .04)
            t += .5 + rng.random() * .8
        for k in range(10):
            fx.put(grave(50, .5, .2), self.t0 + 1.5 + k * 3.0, .08)


# ============================================================ bactérias
class Bacterias(Cena):
    K, VX = 5, 147

    def preparar(self):
        rng = np.random.default_rng(31)
        self.bs = [dict(x=rng.random() * 290, y=40 + rng.random() * 130, tipo=int(rng.random() * 3), a=rng.random() * 6.28,
                        v=.5 + rng.random(), f=rng.random() * 6.28) for _ in range(34)]
        self.fibras = [(30 + k * 70 + rng.random() * 20, 70 + rng.random() * 90, rng.random() * 6.28) for k in range(4)]
        self.kicks = self.batidas('kick')

    def desenhar(self, tela, t, tg):
        # parede em cima e embaixo, conteúdo no meio
        grad_v(tela, 0, 0, 294, PALCO_H, [INT1, RES0, CAV1, CAV0, CAV1, RES0, INT1])
        for x in range(0, 294, 2):
            yt = 22 + 6 * math.sin(x * .07 + t * .5)
            yb = 186 + 6 * math.sin(x * .07 + 1 + t * .5)
            tela.ret(x, 0, 2, int(yt), INT2); tela.ret(x, int(yt), 2, 2, PRETO)
            tela.ret(x, int(yb), 2, PALCO_H - int(yb), INT2); tela.ret(x, int(yb) - 1, 2, 2, PRETO)
        pulso = math.exp(-self.L.desde('kick', tg) / .12) if self.L.desde('kick', tg) < 1 else 0
        # fibras do feijão: diminuem
        come = fase(t, 6.4, 30)
        for k, (fx_, fy, a) in enumerate(self.fibras):
            L = 30 * (1 - .6 * come)
            for j in range(3):
                pts = [(fx_ + math.cos(a) * s + math.sin(s * .2 + t + j) * 2, fy + math.sin(a) * s + j * 3) for s in np.linspace(-L, L, 10)]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    tela.linha(ax, ay, bx, by, ARROZ0 if j else QUI2)
        # bactérias
        for k, b in enumerate(self.bs):
            ang = b['a'] + math.sin(t * .5 + b['f']) * .8
            x = (b['x'] + t * 6 * b['v']) % 300 - 4
            y = b['y'] + math.sin(t * b['v'] + b['f']) * 6
            if k < 8 and t > 6.4:
                fx_, fy, a = self.fibras[k % 4]
                x, y = fx_ + math.cos(k * 1.7 + t * .4) * 18, fy + math.sin(k * 1.7 + t * .4) * 10
            bacteria(tela, x, y, b['tipo'], ang, t, 1.0 + .25 * pulso)
        # gases
        if t > 12.2:
            for k in range(10):
                x = 20 + k * 27 + math.sin(t + k) * 4
                y = 186 - ((t * 20 + k * 37) % 170)
                r = 2.5 + (k % 3)
                tela.anel(x, y, r, ACO3); tela.px(x - 1, y - 1, BRANCO)
        # vitamina K
        if t > 18:
            for k in range(6):
                u = ((t - 18) * .25 + k / 6) % 1.0
                b = self.bs[k * 3]
                x = (b['x'] + 20) % 290
                y = lerp(110, 26, u)
                tela.disco(x, y, 4, PRETO); tela.disco(x, y, 3.2, AMARELO)
                tela.texto('K', x, y - 3, PRETO, tam=9, centro=True)
        self.rot(tela, 'BACTÉRIAS', 8, 36, VERDE, alvo=(self.bs[0]['x'] % 290, self.bs[0]['y']) if False else None)
        if t > 6.4: self.rot(tela, 'FIBRA DO FEIJÃO', 150, 36, ARROZ1, alvo=(self.fibras[2][0], self.fibras[2][1] - 4))
        if t > 12.2: self.rot(tela, 'GASES', 230, 150, ACO3)
        if t > 18: self.rot(tela, 'VITAMINA K', 8, 150, AMARELO)
        est = ('ELAS FAZEM', 'VITAMINA K', AMARELO) if t > 18 else ('ELAS COMEM', 'A FIBRA', ARROZ1)
        self.painel(tela, t, linhas=[('BACTÉRIAS', 'TRILHÕES', VERDE), ('ESPÉCIES', 'MAIS DE 700', ROXO)], estado=est)

    def sons(self, fx):
        rng = np.random.default_rng(10)
        t = 12.4
        while t < 30:
            fx.put(varre(500 + rng.random() * 300, 1100 + rng.random() * 400, .07, 0), self.t0 + t, .05)
            t += .4 + rng.random() * .7
        for k in range(6):
            fx.put(fx.blip(84 + k % 3, .05), self.t0 + 18.2 + k * 1.2, .06)


# ============================================================ 7 saída (discreta)
class Saida(Cena):
    K, VX = 6, 170

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 294, PALCO_H, [FUNDO, FUNDO2, FUNDO])
        # parede com porta
        tela.ret(196, 0, 98, PALCO_H, ACO0)
        for y in range(0, PALCO_H, 10):
            tela.ret(196, y, 98, 1, FUNDO3)
        ab = suave(fase(t, 5.0, 6.0)) * (1 - suave(fase(t, 9.0, 10.0)))
        caixa(tela, 212, 56, 58, 118, FUNDO, ACO2, PRETO)
        larg = int(56 * (1 - ab * .8))
        caixa(tela, 213, 57, larg, 116, LATAO, CHAMA0, OLEO0)
        tela.disco(213 + larg - 8, 118, 2, PRETO); tela.disco(213 + larg - 8, 118, 1.2, AMARELO)
        # placa
        caixa(tela, 218, 30, 46, 16, VERDE, BRANCO, PRETO)
        tela.texto('SAÍDA', 241, 34, PRETO, tam=9, centro=True)
        # o tubo até a porta (estilizado)
        f = guardado('sai_tubo', lambda: tubo([(-10, 120), (100, 118), (196, 116)], 20))
        pintar(tela, f.ox, f.oy, f.m, f.cilindro(), [RES0, INT1, INT2, INT3], PRETO)
        # o resto anda até a porta e sai
        if t < 10:
            u = ease(fase(t, .3, 8.0))
            x = lerp(30, 250, u)
            if x < 270:
                garfada(tela, x, 117, 1.3, t, 'resto', prota=x < 212)
        if t > 9.6:
            for k in range(6):
                a = k * 1.05 + t
                tela.px(241 + math.cos(a) * 16, 112 + math.sin(a) * 16, AMARELO)
        seta(tela, 180, 92, 1, 0, AMARELO, 6)
        tela.ret(150, 92, 30, 1, AMARELO)
        # o que vai junto
        if t > 6.2:
            itens = [('FIBRA', ARROZ1), ('ÁGUA', MISTURA2), ('SAIS', BRANCO), ('BACTÉRIAS', VERDE), ('CÉLULAS VELHAS', MUC3)]
            for k, (nm, cor) in enumerate(itens):
                if t < 6.2 + k * .5: continue
                y = 10 + k * 13
                tela.disco(14, y + 3, 3, PRETO); tela.disco(14, y + 3, 2, cor)
                tela.texto(nm, 22, y, cor, tam=9, contorno=PRETO)
        if t > 12.0:
            tela.texto('FIM DA', 98, 160, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto('JORNADA', 98, 180, AMARELO, tam=17, centro=True, contorno=PRETO)
        est = ('A JORNADA', 'TERMINOU', VERDE) if t > 12 else ('A GARFADA AGORA', 'O RESTO', RES1)
        self.painel(tela, t, linhas=[('O QUE SAI', 'O QUE SOBROU', QUI2)], estado=est)

    def sons(self, fx):
        fx.put(tique(300, .1, .03), self.t0 + 5.0, .2)
        fx.put(tique(260, .12, .04), self.t0 + 9.9, .22)
        fx.put(fx.sino(84, 1.2), self.t0 + 12.1, .16)


# ============================================================ o relógio
FAIXAS = [('BOCA → ESTÔMAGO', 4, 8, MUC2, 0.5), ('ESTÔMAGO', 2 * 3600, 4 * 3600, ACI1, 6.8),
          ('INT. DELGADO', 3 * 3600, 5 * 3600, INT3, 9.6), ('INT. GROSSO', 12 * 3600, 48 * 3600, PAN2, 12.8),
          ('TOTAL', 17 * 3600, 54 * 3600, AMARELO, 24.8)]
LOGMAX = math.log10(3 * 86400)


def x_tempo(s, x0=96, x1=286):
    return x0 + (x1 - x0) * math.log10(max(1.0, s)) / LOGMAX


class Relogio(Cena):
    K, VX = 0, 147

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 294)
        # relógio grande girando
        cx, cy, r = 36, 40, 28
        tela.disco(cx, cy, r + 2, PRETO); tela.disco(cx, cy, r, FUNDO2); tela.anel(cx, cy, r, ACO3, 1.5)
        for k in range(12):
            a = k * math.pi / 6
            tela.px(cx + math.sin(a) * (r - 4), cy - math.cos(a) * (r - 4), BRANCO)
        tela.linha(cx, cy, cx + math.sin(t * 6) * (r - 6), cy - math.cos(t * 6) * (r - 6), AMARELO)
        tela.linha(cx, cy, cx + math.sin(t * .5) * (r - 14), cy - math.cos(t * .5) * (r - 14), BRANCO)
        tela.disco(cx, cy, 2, BRANCO)
        tela.texto('EM GERAL', 172, 14, ACO3, tam=17, centro=True, contorno=PRETO)
        tela.texto('(VARIA MUITO)', 172, 34, ACO2, tam=9, centro=True, contorno=PRETO)
        # eixo (escala que cresce rápido: segundos, minutos, horas, dias)
        ya = 186
        tela.ret(96, ya, 191, 1, ACO2)
        for s, nm in ((1, '1 S'), (60, '1 MIN'), (3600, '1 H'), (86400, '1 DIA')):
            x = int(x_tempo(s))
            tela.ret(x, ya - 3, 1, 7, ACO3)
            tela.texto(nm, x, ya + 6, ACO3, tam=9, centro=True, contorno=PRETO)
        for k, (nm, a, b, cor, t_in) in enumerate(FAIXAS):
            if t < t_in: continue
            y = 82 + k * 19
            u = ease(fase(t, t_in, t_in + 1.2))
            xa, xb = x_tempo(a), x_tempo(b)
            xb = lerp(xa, xb, u)
            tela.texto(nm, 92, y + 2, cor, tam=9, centro='d', contorno=PRETO)
            tela.ret(int(xa), y, max(6, int(xb - xa)), 12, PRETO)
            tela.ret(int(xa) + 1, y + 1, max(4, int(xb - xa) - 2), 10, cor)
            tela.ret(int(xa) + 1, y + 1, max(4, int(xb - xa) - 2), 1, BRANCO)
            if k == 1 and t > 18.8:
                # comida gordurosa: 6 h ou mais
                x6 = x_tempo(6 * 3600)
                for x in range(int(xb), int(x6), 3): tela.ret(x, y + 4, 2, 2, cor)
                tela.texto('GORDUROSA: 6 H OU MAIS', 172, 52, cor, tam=9, centro=True, contorno=PRETO)
                tela.linha(172, 61, int(x6), y, cor)
        # a garfada andando no eixo do tempo
        ts = [0.5, 6.8, 9.6, 12.8, 24.8, 36]
        alvo = [6, 3 * 3600, 7 * 3600, 30 * 3600, 30 * 3600, 30 * 3600]
        s_atual = 1.0
        for i in range(len(ts) - 1):
            if t >= ts[i]:
                s_atual = 10 ** lerp(math.log10(max(1, alvo[i - 1] if i else 1)), math.log10(alvo[i]), ease(fase(t, ts[i], ts[i] + 3)))
        garfada(tela, x_tempo(s_atual), ya - 10, .8, t, 'bolo' if s_atual < 3600 else ('quimo' if s_atual < 12 * 3600 else 'resto'))
        linhas = [('NO ESTÔMAGO', '2 A 4 HORAS', ACI1), ('NO DELGADO', '3 A 5 HORAS', INT3)]
        if t > 12.8: linhas = [('NO GROSSO', '12 H A 2 DIAS', PAN2), ('SOMANDO', '17 H A 2 DIAS+', AMARELO) if t > 24.8 else ('NO DELGADO', '3 A 5 HORAS', INT3)]
        self.painel(tela, t, cab=('O RELÓGIO', 'DA GARFADA', AMARELO), linhas=linhas,
                    estado=('ATÉ O ESTÔMAGO', '4 A 8 S', MUC2), selo='O RELÓGIO DA GARFADA')

    def sons(self, fx):
        for k in range(72):
            fx.put(tique(1900 if k % 2 else 1500, .03, .006), self.t0 + .5 * k, .05)
        for _, _, _, _, t_in in FAIXAS:
            fx.put(fx.sino(79, .7), self.t0 + t_in, .12)


# ============================================================ resumo
class Resumo(Cena):
    K, VX = 0, 147

    def u(self, t):
        if t < 7.4: return lerp(0, U_ETAPA[3], ease(t / 7.4))
        if t < 14.6: return lerp(U_ETAPA[3], U_ETAPA[5] - .02, ease((t - 7.6) / 7.0))
        if t < 22.0: return U_ETAPA[5] - .02
        return lerp(U_ETAPA[5] - .02, 1.0, ease((t - 22.0) / 7.0))

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 294)
        u = self.u(t)
        k = etapa_de_u(u)

        def veias(tl):
            if 14.8 < t < 22.0:
                for (ax, ay), (bx, by) in zip(PORTA, PORTA[1:]):
                    linha_grossa(tl, ax, ay, bx, by, 4, PRETO); linha_grossa(tl, ax, ay, bx, by, 2.4, SANG1)

        D.corpo(tela, t, atual=['boca', 'garganta', 'esofago', 'estomago', 'delgado', 'grosso', 'saida'][k], sangue=veias)
        for j in range(int(u * 160)):
            x, y = ao_longo(ROTA, j / 160)
            if j % 3 == 0: tela.px(x, y, AMARELO)
        x, y = ao_longo(ROTA, u)
        garfada(tela, x, y, .8, t, 'bolo' if k < 3 else ('quimo' if k < 5 else 'resto'))
        if 14.8 < t < 22.0:
            for j in range(8):
                uu = (t * .3 + j / 8) % 1.0
                px_, py_ = ao_longo(PORTA, uu)
                (glicose if j % 2 else aminoacido)(tela, px_, py_)
            for j in range(10):
                uu = ((t - 14.8) * .3 + j / 10) % 1.0
                a = j * 2 * math.pi / 10
                tela.disco(132 + math.cos(a) * uu * 60, 104 + math.sin(a) * uu * 80, 1.3, SANG2)
        for e, txt, lx, ly, alvo in ORG_ROT:
            if k >= e: self.rot(tela, f"{e + 1} {txt}", lx, ly, ETAPAS[e][1], alvo=alvo)
        self.K = k
        fim = u >= 1.0
        self.painel(tela, t, tudo=fim, linhas=[('PERCURSO', 'BOCA → SAÍDA', AMARELO)],
                    estado=('A GARFADA ESTÁ', ['NA BOCA', 'ENGOLINDO', 'DESCENDO', 'NO ESTÔMAGO', 'NO DELGADO', 'NO GROSSO', 'SAINDO'][k] if not fim else 'FORA', AMARELO))

    def sons(self, fx):
        for i, a in enumerate((0.5, 7.6, 14.8, 22.0)):
            fx.put(fx.sino(76 + i * 2, .9), self.t0 + a, .12)
        fx.put(fx.sino(84, 1.2), self.t0 + 29.0, .14)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS A JORNADA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            grade(tela)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            prato(tela, W // 2, 130, t)
            y = 90 - abs(math.sin(t * 3)) * 12
            garfada(tela, W // 2 + 60, y, 1.4, t, 'bolo')

    def tela_pronta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .8)


# longo.py chama `cena.pos(baixo, t)` para a cena que entrega RGB pronto (a vinheta).
Fim.pos = Fim.tela_pronta

CENAS = dict(gancho=Gancho, titulo=Titulo, prato=Prato, mapa=Mapa, boca=Boca, engolir=Engolir, esofago=Esofago,
             estomago=Estomago, delgado=Delgado, ajudantes=Ajudantes, vilosidades=Vilosidades, sangue=Sangue,
             grosso=Grosso, bacterias=Bacterias, saida=Saida, relogio=Relogio, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep15_motor as EP
    if sys.argv[1] in ('--folha', '--quadros'):
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if sys.argv[1] == '--folha':
            so = sys.argv[3:] or None
            fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
            for c in trilha.caps:
                if so and c['id'] not in so: continue
                ts += [c['t0'] + c['dur'] * f for f in fr]
        else:
            for a in sys.argv[3:]:
                cid, tt = a.split(':')
                c = next(x for x in trilha.caps if x['id'] == cid)
                ts.append(c['t0'] + float(tt))
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else max(1, len(ims))
        if sys.argv[1] == '--folha' and 1 < len(fr) <= 5: cols = len(fr)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
