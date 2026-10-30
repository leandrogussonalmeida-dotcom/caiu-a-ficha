#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep23 — A jornada de uma gota de chuva (PT-BR).

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (ondas, vento, o "pop" de cada
                          molécula que gruda, o choque das gotinhas, a gota
                          batendo na folha, a chuva), nos mesmos instantes
A posição da protagonista sai de uma função do tempo em cada capítulo
(`p_gota`); o rastro, o painel e o som leem a mesma função. Os "pops" da
condensação e das colisões caem nas batidas da trilha (`trilha.L`).

    python3 ep23_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep23_motor.py <saida.mp4> queda floresta      # só esses capítulos (teste)
    python3 ep23_motor.py --folha <saida.png> [ids]       # quadros por capítulo (FR=.3,.8)
    python3 ep23_motor.py --quadros <saida.png> id:t ...  # quadros escolhidos
"""
import math, os, sys
import numpy as np
import ep23_desenho as D                      # registra a paleta 'ep23' (antes de qualquer Tela)
import ep11_desenho as E11
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
from ep11_desenho import (CEU0, CEU1, CEU2, GRAMA0, GRAMA1, GRAMA2, TERRA0, TERRA1, CONC0, CONC1, CONC2,
                          AGP, AGM, AGC, ESPUMA, NUVEM0, NUVEM1,
                          rotulo, fio, halo, caixa, grad_v, agua, chuva, morro, interp, ao_longo, arvore, lerp)
from ep23_desenho import (CEUD0, CEUD1, CEUD2, CEUD3, SOL0, SOL1, MAR0, MAR1, MAR2, FOL0, FOL1, FOL2, FOL3, FOL4,
                          TRO0, TRO1, TRO2, SOLO0, SOLO1, SOLO2, SAL0, SAL1, NUVD0, NUVD1, NUVD2, AND0, AND1, AND2,
                          ETAPAS, um, seta, aura, gota, prota, vapor_prota, rastro, gotinha, molecula, sal,
                          ceu_dia, sol, mar, nuvem_dia, vento, copa, lupa, recortar_disco, termometro,
                          fmt_num, fmt_alt, fmt_temp, fmt_mm, fmt_dias)
import ritmo_marca as RM
import quizaudio as QA
from ep23_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2623, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
SR = LG.SR

T_MAR = 25.0                  # exemplo: 25 °C no nível do mar (F14)
BASE_NUVEM = 1000.0           # base da nuvem neste exemplo (m)


def fase(t, a, b): return um((t - a) / max(1e-6, b - a))


def temp_de(alt):
    """Temperatura do exemplo: 9,8 °C/km até a base da nuvem, ~5 °C/km acima (F2, F14)."""
    if alt <= BASE_NUVEM: return T_MAR - 9.8 * alt / 1000
    return T_MAR - 9.8 * BASE_NUVEM / 1000 - 5.0 * (alt - BASE_NUVEM) / 1000


def caminho(pts, u):
    return ao_longo(pts, u)


# ================================================================ sons sintetizados
def tique(f=1200.0, dur=.05):
    """Tique curto de seno puro (pico baixo, sem estalo)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / .002) * np.exp(-tt / (dur / 4))
    return (np.sin(2 * np.pi * f * tt) * env).astype(np.float32)


def pinga(f0=1400.0, dur=.16):
    """Pingo: seno que sobe rápido (o "plic" de uma gota na água)."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 * (1 + 1.2 * (1 - np.exp(-tt / .03)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, tt / .002) * np.exp(-tt / (dur / 5))
    return (np.sin(ph) * env).astype(np.float32)


def pop(f=700.0, dur=.08):
    """Bolha que estoura: seno que desce."""
    n = int(dur * SR)
    tt = np.arange(n) / SR
    fr = f * (1.6 - .6 * np.minimum(1, tt / dur))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    env = np.minimum(1, tt / .003) * np.exp(-tt / (dur / 4))
    return (np.sin(ph) * env).astype(np.float32)


def respingo_som(fx, dur=.22):
    """Gota batendo: ruído agudo filtrado, curto e baixo."""
    return fx.chiado(dur, 1800, 6500, ataque=.004)


# ================================================================ base
class Cena:
    legenda = True
    brilho = None
    K = 0                     # etapa do painel (0..8)
    VX = 146                  # centro do recorte vertical (x = 56 nos CORTES)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.L = trilha.L
        self.t0, self.dur = cap['t0'], cap['dur']
        self.bt = [e['t'] - self.t0 for e in self.L.entre('batida', self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]
        self.kk = [e['t'] - self.t0 for e in self.L.entre('kick', self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def painel(self, tela, t, selo=None, **kw):
        if VERTICAL:
            D.selo_vertical(tela, max(0, self.K), self.VX, selo)
        else:
            D.painel_gota(tela, self.K, t, **kw)

    def rot(self, tela, txt, x, y, cor=BRANCO, alvo=None, centro=False, tam=9):
        """Rótulo com fio opcional; no Short some se sair do recorte."""
        w = tela.largura_texto(txt, tam)
        xa = x - w // 2 if centro else x
        if VERTICAL and (xa < self.VX - 88 or xa + w > self.VX + 88): return
        if not VERTICAL and xa + w > 292: return
        if alvo:
            ax = xa + w // 2
            ay = y + 9 if alvo[1] > y else y - 2
            fio(tela, ax, ay, alvo[0], alvo[1], cor)
        rotulo(tela, txt, x, y, cor, tam=tam, centro=centro)

    def caixa_txt(self, tela, linhas, x, y, borda=AMARELO, centro=False):
        """Quadrinho de destaque com 1 a 3 linhas [(texto, tam, cor)]."""
        w = max(tela.largura_texto(s, tm) for s, tm, _ in linhas) + 12
        h = sum(18 if tm == 17 else 11 for _, tm, _ in linhas) + 8
        xx = x - w // 2 if centro else x
        if VERTICAL:
            xx = int(min(max(xx, self.VX - 89), self.VX + 89 - w))
        painel(tela, xx, y, w, h, borda=borda)
        yy = y + 5
        for s, tm, c in linhas:
            tela.texto(s, xx + w // 2, yy, c, tam=tm, centro=True, contorno=PRETO)
            yy += 18 if tm == 17 else 11
        return xx, w, h

    def beats(self, a, b):
        return [x for x in self.bt if a <= x < b]

    def kicks(self, a, b):
        ks = [x for x in self.kk if a <= x < b]
        return ks if len(ks) >= 4 else self.beats(a, b)


def grade(tela, x0=0, x1=W):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(x0, x1, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(x0, y, x1 - x0, 1, FUNDO2)


# ============================================================ gancho
ICX = [30 + i * 52.5 for i in range(9)]
NOMES_CURTOS = ['MAR', 'SOBE', 'NÚCLEO', 'JUNTA', 'CAI', 'ÁRVORE', 'VENTO', 'CHUVA', 'MAR']


class Gancho(Cena):
    T_BATE = 4.6

    def p_gota(self, t):
        u = um(t / self.T_BATE)
        return 150 + 6 * math.sin(t * 1.3), -14 + 150 * (u ** 1.6)

    def desenhar(self, tela, t, tg):
        if t < 6.0: self.folha(tela, t)
        else: self.trilha(tela, t - 6.0)

    def folha(self, tela, t):
        grad_v(tela, 0, 0, W, PALCO_H, [FOL0, FOL1, FOL0, FOL0])
        for k in range(7):                                  # folhas do fundo (fora de foco)
            cx = (k * 83 + 30) % W; cy = 40 + (k * 47) % 140
            tela.disco(cx, cy, 22 + (k % 3) * 6, FOL1)
            LG.dither(tela, cx - 10, cy - 6, 20, 12, FOL1, FOL2)
        chuva(tela, 0, W, 0, PALCO_H, t, n=50, vel=120, cor=FOL3, seed=4)
        # a folha grande, em diagonal
        pts = [(60, 176), (150, 140), (250, 132), (340, 146), (420, 178), (330, 196), (200, 194), (110, 190)]
        sway = math.sin(t * 1.5) * 1.5
        if t > self.T_BATE: sway += 6 * math.exp(-(t - self.T_BATE) * 3) * math.sin((t - self.T_BATE) * 18)
        pts = [(x, y + sway * (x - 60) / 360) for x, y in pts]
        poligono(tela, [(x, y + 2) for x, y in pts], PRETO)
        poligono(tela, pts, FOL2)
        poligono(tela, [(x, y + 6) for x, y in pts[:5]] + [(330, 186), (200, 184), (110, 182)], FOL3)
        for k in range(8):
            x = 90 + k * 40
            tela.linha(x, 160 + sway * (x - 60) / 360 + 6, x + 22, 150 + sway * (x - 60) / 360, FOL4)
        tela.linha(60, 176 + 2, 420, 176 + sway, FOL4)
        if t < self.T_BATE:
            rastro(tela, self.p_gota, t, n=8, dt=.05)
            x, y = self.p_gota(t)
            prota(tela, x, y, 10, t, achata=.15)
            if t > .8: self.rot(tela, 'A NOSSA GOTA', int(x) + 22, int(y) - 20, AMARELO, alvo=(x + 9, y - 6))
        else:
            u = t - self.T_BATE
            x0, y0 = self.p_gota(self.T_BATE)
            for k in range(8):                               # respingo
                a = math.pi + k * math.pi / 7
                d = 6 + u * 70
                yy = y0 - math.sin(-a) * d + 120 * u * u
                if u < .7: gota(tela, x0 + math.cos(a) * d, yy, 3 - k % 2)
            # o que sobra escorre pela folha, ainda brilhando
            xs = x0 + u * 26
            prota(tela, xs, 136 + u * 6 + sway, 6, t, achata=.45)

    def trilha(self, tela, u):
        grade(tela)
        tela.texto('POR ONDE ELA PASSOU?', W // 2, 18, ACO3, tam=17, centro=True, contorno=PRETO)
        prog = um(u / 4.6)
        for i in range(9):
            aceso = prog * 9 >= i + .3
            D.icone(tela, i, ICX[i], 96, u, aceso=aceso)
            tela.texto(str(i + 1), ICX[i], 120, ETAPAS[i][1] if aceso else ACO1, tam=9, centro=True, contorno=PRETO)
            if aceso: tela.texto(NOMES_CURTOS[i], ICX[i], 132, BRANCO, tam=9, centro=True, contorno=PRETO)
            if i < 8:
                xa, xb = ICX[i] + 18, ICX[i + 1] - 18
                tela.ret(xa, 96, xb - xa, 1, ETAPAS[i][1] if prog * 9 >= i + 1.3 else ACO0)
        fn = lambda tt: (lerp(ICX[0], ICX[8], ease(um(tt / 4.6))), 62 + 4 * math.sin(tt * 5))
        rastro(tela, fn, u, n=10, dt=.06)
        x, y = fn(u)
        if prog < .6 or prog >= 1: vapor_prota(tela, x, y, u) if prog < 1 else prota(tela, x, y, 5, u)
        else: prota(tela, x, y, 4, u)
        if prog >= 1:
            tela.texto('E VOLTOU PARA O MAR', W // 2, 156, AMARELO, tam=17, centro=True, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(6.0, 2500, 7000), self.t0, .045)
        fx.put(respingo_som(fx), self.t0 + self.T_BATE, .32)
        fx.put(pinga(1300), self.t0 + self.T_BATE + .01, .22)
        for i in range(9):
            fx.put(tique(880 * 2 ** ((0, 2, 4, 5, 7, 9, 11, 12, 14)[i] / 12), .08), self.t0 + 6.0 + (i + .3) / 9 * 4.6, .16)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        chuva(tela, 0, W, 0, PALCO_H, t, n=50, vel=110, cor=FUNDO3, seed=3)
        tela.texto('SÉRIE A JORNADA', W // 2, 18, ACO3, tam=9, centro=True, contorno=PRETO)
        n = int(t / .045)
        for j, linha in enumerate(("A JORNADA DE", "UMA GOTA DE CHUVA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 12)]
            tela.texto(vis, W // 2 - larg // 2, 40 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto('DO ATLÂNTICO À AMAZÔNIA, E DE VOLTA', W // 2, 116, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 9 * 18 // 2 + k * 18
                c = cor if t > 2.0 + k * .3 else FUNDO2
                tela.ret(x, 146, 14, 14, PRETO); tela.ret(x + 1, 147, 12, 12, c)
                tela.texto(str(k + 1), x + 7, 150, PRETO, tam=9, centro=True)
        fn = lambda tt: (60 + 4 * math.sin(tt * 2), 30 + (tt * 34) % 160)
        rastro(tela, fn, t, n=7, dt=.05)
        prota(tela, *fn(t), 6, t)
        gota(tela, 420, 30 + (t * 34 + 80) % 160, 4)

    def sons(self, fx):
        for k in range(9):
            fx.put(tique(880 * 2 ** ((0, 2, 4, 5, 7, 9, 11, 12, 14)[k] / 12), .07), self.t0 + 2.0 + k * .3, .14)


# ============================================================ 1 oceano
SUP = 122                     # superfície do mar (y)
LUPA_O = (226, 154, 44)


class Oceano(Cena):
    K = 0
    T_ESCAPA = 13.4

    def p_gota(self, t):
        """Depois de escapar: o vapor sobe devagar e o vento o puxa para a terra (esquerda)."""
        if t < self.T_ESCAPA: return None
        u = t - self.T_ESCAPA
        return 150 - 2.2 * u - 3 * math.sin(u * .9), SUP - 3 - 3.6 * u + 2 * math.sin(u * 1.7)

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, SUP + 4)
        sol(tela, 252, 30, 12, t)
        nuvem_dia(tela, 90 + math.sin(t * .2) * 6, 26, 50)
        # a costa do Brasil, à esquerda
        costa = [(-2, 92), (14, 86), (30, 96), (44, 112), (58, SUP + 2)]
        morro(tela, costa, GRAMA1, GRAMA2)
        for x in (6, 18, 30): arvore(tela, x, interp(costa, x) + 4, 12)
        tela.ret(0, SUP - 2, 62, 3, CERAMICA)
        mar(tela, 0, 292, SUP, t, onda=1.0)
        for k in range(10):                                   # cristas
            x = (k * 47 + int(t * 9)) % 292
            tela.ret(x, SUP + 6 + (k % 4) * 9, 6, 1, MAR2)
        # raios de sol esquentando a água
        if 5.5 < t < 22:
            a = fase(t, 5.5, 7.0) * (1 - fase(t, 20.5, 22))
            for k in range(5):
                x0 = 236 - k * 26
                u = (t * .9 + k * .23) % 1.0
                ya = 44 + u * (SUP - 50)
                if a > .3:
                    for j in range(6):
                        yy = ya + j * 2
                        if yy < SUP: tela.px(x0 - (yy - 30) * .55 + math.sin(yy * .3) * 1.5, yy, SOL0 if j < 3 else SOL1)
        # vapor (pintado: de verdade é invisível)
        for k in range(22):
            per = 9.0 + (k % 5)
            u = ((t + k * 1.37) % per) / per
            x = (k * 29 + 13) % 280 + 6 - u * 40
            y = SUP - 2 - u * 100 + math.sin(t * 2 + k) * 2
            if (k + int(t * 6)) % 3 and y > 6: tela.px(x, y, ESPUMA if u < .5 else CEUD3)
        if t > 19.5 and not VERTICAL:
            self.rot(tela, 'VAPOR (PINTADO)', 160, 70, ESPUMA, alvo=(140, 86))
        # a nossa molécula, já vapor
        p = self.p_gota(t)
        if p:
            rastro(tela, self.p_gota, t, n=12, dt=.12, r0=1.6)
            vapor_prota(tela, p[0], p[1], t)
            if t > 15 and p[1] > 14:
                self.rot(tela, 'A NOSSA MOLÉCULA', int(p[0]) + 12, int(p[1]) - 18, AMARELO, alvo=(p[0] + 4, p[1] - 4))
        if t < 22.0:
            self.lupa(tela, t)
        if not VERTICAL:
            self.rot(tela, 'BRASIL', 6, 74, GRAMA2)
            self.rot(tela, 'OCEANO ATLÂNTICO', 70, 190 if t < 22 else 186, MAR2)
            if t > 6.7: self.rot(tela, 'SOL', 230, 48, SOL0, alvo=(244, 38))
        # números do planeta
        if t >= 25.9:
            self.barras(tela, t)
        tam = 'MOLÉCULA' if t < self.T_ESCAPA else 'VAPOR'
        self.painel(tela, t, alt='0 M' if t < self.T_ESCAPA else fmt_alt(max(0, (SUP - self.p_gota(t)[1]) * 2)),
                    temp=fmt_temp(T_MAR), tam=tam, dias=fmt_dias(0))

    def barras(self, tela, t):
        x0, y0, w = 14, 10, 150
        n = 2 if t >= 31.9 else 1
        painel(tela, x0, y0, w + 16, 22 + n * 24, borda=MAR2)
        itens = [('EVAPORAÇÃO NO MAR', 86, 25.9, MAR2), ('ÁGUA NOS OCEANOS', 97, 31.9, AGC)]
        for j in range(n):
            nm, pc, ta, cor = itens[j]
            y = y0 + 6 + j * 24
            tela.texto(nm, x0 + 8, y, BRANCO, tam=9, contorno=PRETO)
            f = ease(fase(t, ta + .2, ta + 1.6)) * pc / 100
            tela.ret(x0 + 8, y + 11, w, 8, PRETO)
            tela.ret(x0 + 9, y + 12, int((w - 2) * f), 6, cor)
            tela.ret(x0 + 9 + int((w - 2) * f), y + 12, w - 2 - int((w - 2) * f), 6, FUNDO2)
            tela.texto(f"{int(round(f * 100))}%", x0 + w - 20, y, AMARELO, tam=9, contorno=PRETO)

    def lupa(self, tela, t):
        cx, cy, r = LUPA_O
        r = r * (1 - ease(fase(t, 20.8, 22.0)))
        if r < 3: return
        fundo = tela.buf[:PALCO_H].copy()
        sup = cy - 8
        tela.ret(cx - r - 2, cy - r - 2, 2 * r + 4, sup - (cy - r) + 2, CEUD3)
        LG.dither(tela, cx - r - 2, cy - r - 2, 2 * r + 4, sup - (cy - r) + 2, CEUD3, CEUD2)
        grad_v(tela, cx - r - 2, sup, 2 * r + 4, cy + r - sup + 3, [MAR1, MAR0, AGP])
        for x in range(int(cx - r), int(cx + r)):
            tela.px(x, sup + round(math.sin(x * .2 + t * 2)), MAR2)
        calor = .6 + 2.6 * fase(t, 6.0, 13.0)
        for i in range(4):
            for j in range(5):
                bx, by = cx - 30 + j * 15 + (i % 2) * 7, sup + 9 + i * 10
                k = i * 5 + j
                a = math.sin(t * (5 + k % 3) + k * 1.9) * calor
                b = math.cos(t * (6 + k % 4) + k * 1.3) * calor
                if (i, j) == (0, 2): continue
                molecula(tela, bx + a, by + b, t * 1.5 + k, .75, AGC)
        # a nossa
        bx, by = cx, sup + 9
        if t < self.T_ESCAPA:
            a = math.sin(t * 9) * calor; b = math.cos(t * 11) * calor
            molecula(tela, bx + a, by + b, t * 3, .85, prota_=True, t=t)
        else:
            u = ease(fase(t, self.T_ESCAPA, self.T_ESCAPA + 1.6))
            molecula(tela, bx + 10 * u, by - 46 * u + math.sin(t * 4) * 2, t * 3, .85, prota_=True, t=t)
        recortar_disco(tela, cx, cy, r, fundo)
        lupa(tela, cx, cy, r, alvo=(150, SUP))
        if r > 30:
            tela.texto('ÁGUA', cx + r - 30, sup + 3, MAR2, tam=9, contorno=PRETO)
            tela.texto('AR', cx - r + 12, cy - r + 12, CEUD0, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(9):
            fx.put(fx.chiado(4.6, 150, 700, ataque=1.2), self.t0 + k * 4.0, .07, -.2 + .1 * (k % 4))
        fx.put(pinga(900, .3), self.t0 + self.T_ESCAPA, .25)
        fx.put(tique(1320, .1), self.t0 + 26.1, .15)
        fx.put(tique(1480, .1), self.t0 + 32.1, .15)


# ============================================================ 2 subida
Y0_SUB = 182                  # nível do mar no desenho
PX_KM = 128.0                 # pixels por km de altitude


class Subida(Cena):
    K = 1

    def alt(self, t):
        return 80 + 920 * suave(fase(t, 6.0, 31.5))

    def p_gota(self, t):
        x = lerp(262, 170, ease(fase(t, 0, 6.2))) - 60 * suave(fase(t, 6.0, 33.0))
        return x + 3 * math.sin(t * 1.1), Y0_SUB - self.alt(t) / 1000 * PX_KM

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, Y0_SUB + 2)
        sol(tela, 270, 18, 8, t)
        # terra (esquerda) e mar (direita)
        copa(tela, 0, 172, Y0_SUB + 8, t, seed=2, alt=10)
        mar(tela, 172, 292, Y0_SUB, t, onda=.8)
        tela.ret(168, Y0_SUB - 2, 8, 4, CERAMICA)
        # ventos alísios
        for k in range(7):
            y = 30 + k * 20
            vento(tela, 292, y, 292, t + k * .7, CEUD3 if k % 2 else BRANCO, vel=60 + k * 6)
        # régua da altitude
        for a in range(0, 1501, 100):
            y = Y0_SUB - a / 1000 * PX_KM
            if y < 2: continue
            tela.ret(4, int(y), 6 if a % 500 == 0 else 3, 1, BRANCO if a % 500 == 0 else ACO3)
            if a % 500 == 0 and a > 0:
                tela.texto(fmt_alt(a) if a < 1000 else ('1 KM' if a == 1000 else '1,5 KM'), 12, int(y) - 3, BRANCO, tam=9, contorno=PRETO)
        # a parcela de ar
        x, y = self.p_gota(t)
        R = 15 + 7 * (self.alt(t) - 80) / 920
        satura = fase(t, 31.5, 34.0)
        aura(tela, x, y, R - 2, R, BRANCO if satura > .5 else CEUD3, int(t * 6) % 2)
        tela.anel(x, y, R, ACO4 if satura < .5 else NUVD2, .5)
        for k in range(9):
            a = k * .7 + t * .8
            rr = (k * 37 % 11) / 11 * (R - 4)
            px, py = x + math.cos(a) * rr, y + math.sin(a * 1.3) * rr * .8
            if satura > .2 and k % 2 == 0:
                gotinha(tela, px, py, 1.5 * satura)
            else:
                tela.px(px, py, ESPUMA)
        if satura > .3:
            nuvem_dia(tela, x, y - 2, R * 2.2 * satura)
        rastro(tela, self.p_gota, t, n=12, dt=.25, r0=1.6)
        vapor_prota(tela, x + 2, y + 1, t)
        # expansão: setas para fora
        if 13.1 < t < 25:
            for k in range(8):
                a = k * math.pi / 4
                d = R + 3 + 2 * ((t * 2) % 1)
                tela.px(x + math.cos(a) * d, y + math.sin(a) * d, BRANCO)
                tela.px(x + math.cos(a) * (d + 1.5), y + math.sin(a) * (d + 1.5), BRANCO)
        # termômetro ao lado da parcela
        tc = temp_de(self.alt(t))
        tx = x + R + 10
        termometro(tela, tx, y - 14, 22, (tc - 5) / 25, VERMELHO if tc > 18 else LARANJA if tc > 12 else CIANO)
        tela.texto(fmt_temp(tc), tx + 12, y - 6, AMARELO, tam=9, contorno=PRETO)
        if t > 1.0: self.rot(tela, 'VENTOS ALÍSIOS', 190, 6, BRANCO)
        if t > 1.0: seta(tela, 186, 10, -1, 0, BRANCO, 4)
        if t > 6.7: self.rot(tela, 'AR QUENTE E ÚMIDO', int(x - 50), int(y + R + 5), ESPUMA)
        if 13.1 < t < 25.7: self.rot(tela, 'O AR SE EXPANDE', int(x - 44), int(y - R - 14), BRANCO)
        if t >= 19.5 and t < 31.9:
            self.caixa_txt(tela, [('SOBE 1 KM:', 9, BRANCO), ('-10 °C', 17, CIANO)], 40, 22)
        if not VERTICAL:
            self.rot(tela, 'MAR', 250, Y0_SUB + 10, MAR2)
            self.rot(tela, 'CONTINENTE', 60, Y0_SUB + 12, FOL4)
        self.painel(tela, t, alt=fmt_alt(self.alt(t)), temp=fmt_temp(tc),
                    tam='VAPOR' if satura < .9 else 'VAI CONDENSAR', dias=fmt_dias(0 if t < 18 else 1))

    def sons(self, fx):
        for k in range(6):
            fx.put(fx.chiado(6.5, 200, 900, ataque=1.5), self.t0 + k * 6.0, .08, .3 - .12 * k)
        for a in range(100, 1001, 100):        # um tique a cada 100 m
            tt = 6.0 + (31.5 - 6.0) * self._inv(a)
            fx.put(tique(700 + a * .6, .05), self.t0 + tt, .09)
        fx.put(fx.sino(84, 1.0), self.t0 + 32.0, .18)

    def _inv(self, a):
        u = (a - 80) / 920
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            if suave(m) < u: lo = m
            else: hi = m
        return lo


# ============================================================ 3 núcleo
LC = (146, 98, 80)            # lupa grande (centro x, y, raio)


class Nucleo(Cena):
    K = 2
    T_GRUDA = 16.0

    def preparar(self):
        self.ev = [b for b in self.beats(2.6, 25.0)]
        self.N = len(self.ev)

    def n_grudadas(self, t):
        return sum(1 for e in self.ev if e <= t)

    def raio_casca(self, t):
        n = self.n_grudadas(t)
        r = 10 + 30 * math.sqrt(n / max(1, self.N))
        if self.ev and t > self.ev[0]:
            d = t - max(e for e in self.ev if e <= t)
            r += 1.6 * math.exp(-d / .12)
        return r

    def zoom(self, t):
        return 1 - .82 * ease(fase(t, 31.0, 35.0))

    def desenhar(self, tela, t, tg):
        cx, cy, R = LC
        # fora da lupa: o céu com a nuvem nascendo
        ceu_dia(tela, PALCO_H, 0, 292)
        for k in range(3):
            nuvem_dia(tela, 40 + k * 110 + math.sin(t * .3 + k) * 4, 180 - k * 6, 40 + 30 * fase(t, 10, 34))
        fundo = tela.buf[:PALCO_H].copy()
        LG.dither(tela, cx - R, cy - R, 2 * R, 2 * R, CEUD2, CEUD3)
        z = self.zoom(t)
        rc = self.raio_casca(t) * z
        # moléculas soltas no ar (vapor)
        for k in range(14):
            a = k * 2.39 + t * (.25 + (k % 3) * .08)
            rr = 46 + 22 * math.sin(t * .5 + k)
            if t > 25 and k % 2 == 0: continue
            molecula(tela, cx + math.cos(a) * rr, cy + math.sin(a) * rr * .85, t * 2 + k, .8 * max(.4, z), ACO4)
        # moléculas indo grudar (uma por batida)
        for i, e in enumerate(self.ev):
            if e - .55 <= t < e:
                u = ease((t - (e - .55)) / .55)
                a = i * 2.39
                r0, r1 = 70, self.raio_casca(e - .01) * z
                rr = lerp(r0, r1, u)
                molecula(tela, cx + math.cos(a) * rr, cy + math.sin(a) * rr, t * 4 + i, .8 * max(.4, z), AGC)
            if e <= t < e + .25:
                a = i * 2.39
                rr = self.raio_casca(e) * z
                tela.anel(cx + math.cos(a) * rr, cy + math.sin(a) * rr, 2 + (t - e) * 18, BRANCO, .5)
        # a casca de água em volta do sal
        if rc > 10 * z + .5:
            tela.disco(cx, cy, rc + 1, PRETO)
            tela.disco(cx, cy, rc, AGM)
            aura(tela, cx, cy, 0, rc - 1, AGC, 0)
            tela.disco(cx - rc * .35, cy - rc * .35, rc * .28, AGC)
            tela.disco(cx - rc * .45, cy - rc * .45, max(1, rc * .1), ESPUMA)
        sal(tela, cx, cy, 8 * z, t)
        if t > 1.5 and z > .5: self.rot(tela, 'GRÃO DE SAL', cx + 22, cy + 46, SAL0, alvo=(cx + 6, cy + 4))
        # a nossa molécula
        if t < self.T_GRUDA - 1.2:
            a = t * .55 + 1.0
            px, py = cx + math.cos(a) * 58, cy + math.sin(a) * 40
        else:
            u = ease(fase(t, self.T_GRUDA - 1.2, self.T_GRUDA))
            a0 = (self.T_GRUDA - 1.2) * .55 + 1.0
            sx, sy = cx + math.cos(a0) * 58, cy + math.sin(a0) * 40
            ex, ey = cx - 6 * z, cy - 6 * z - (self.raio_casca(t) * z - 12 * z) * .5
            px, py = lerp(sx, ex, u), lerp(sy, ey, u)
        molecula(tela, px, py, t * 3, .9 * max(.5, z), prota_=True, t=t)
        if t > 3 and t < self.T_GRUDA + 3:
            self.rot(tela, 'A NOSSA MOLÉCULA', int(px) - 40, int(py) - 22, AMARELO)
        # calor da condensação
        if 25.9 <= t < 31.5:
            for i, b in enumerate(self.beats(25.9, 31.5)):
                if b <= t < b + .6:
                    u = (t - b) / .6
                    for k in range(6):
                        a = k * math.pi / 3 + i
                        d = rc + 4 + u * 18
                        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
                        tela.px(x, y, CHAMA1); tela.px(x + 1, y - 1, LARANJA)
            self.rot(tela, 'CALOR', cx + 50, cy - 60, CHAMA1)
        # zoom out: outras gotinhas formando a nuvem
        if t > 31.0:
            for k in range(26):
                a = k * 2.39; rr = 14 + (k * 13) % 60
                gotinha(tela, cx + math.cos(a) * rr * (1.2 - z), cy + math.sin(a) * rr * (1.2 - z), 3 * (1 - z) + .5)
        recortar_disco(tela, cx, cy, R, fundo)
        lupa(tela, cx, cy, R)
        # régua do tamanho
        if 19.5 <= t < 31:
            y = cy + R - 14
            w = int(2 * self.raio_casca(t) * z)
            tela.ret(cx - w // 2, y, w, 1, AMARELO)
            tela.ret(cx - w // 2, y - 2, 1, 5, AMARELO); tela.ret(cx + w // 2, y - 2, 1, 5, AMARELO)
            tela.texto('0,02 MM', cx, y - 12, AMARELO, tam=9, centro=True, contorno=PRETO)
        if t > 31.9:
            self.rot(tela, 'NUVEM', cx, cy + R - 20, BRANCO, centro=True)
        n = self.n_grudadas(t)
        tam = 'VAPOR' if t < self.T_GRUDA else fmt_mm(.005 + .015 * min(1, n / max(1, self.N)))
        altm = 1000 + 400 * fase(t, 0, 36)
        self.painel(tela, t, alt=fmt_alt(altm), temp=fmt_temp(temp_de(altm)), tam=tam,
                    dias=fmt_dias(1 if t < 20 else 2))

    def sons(self, fx):
        for i, e in enumerate(self.ev):
            fx.put(pop(500 + (i % 8) * 60, .07), self.t0 + e, .2, -.3 + .6 * ((i * 7) % 5) / 4)
        fx.put(pinga(1500, .25), self.t0 + self.T_GRUDA, .28)
        for b in self.beats(25.9, 31.5):
            fx.put(tique(330, .12), self.t0 + b, .12)


# ============================================================ 4 colisão
class Colisao(Cena):
    K = 3
    TC0, TC1 = 6.7, 25.0          # contador de gotinhas: de 1 a 1 milhão
    T_CAI = 31.9

    def preparar(self):
        self.ev = self.kicks(6.7, 30.5)

    def conta(self, t):
        if t < self.TC0: return 1.0
        return 10 ** (6 * suave(fase(t, self.TC0, self.TC1)))

    def raio(self, t):
        base = 3 + 11 * math.log10(self.conta(t)) / 6
        if self.ev and t > self.ev[0]:
            d = t - max(e for e in self.ev if e <= t)
            base += 1.2 * math.exp(-d / .1)
        return base

    def p_gota(self, t):
        return 146 + 3 * math.sin(t * .8), 92 + 2 * math.sin(t * 1.4) + 140 * ease(fase(t, self.T_CAI + .5, 35.8)) ** 2

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 292, PALCO_H, [NUVD1, NUVD0, NUVD0, NUVEM1])
        for k in range(30):                              # névoa da nuvem passando
            vy = 8 + 30 * fase(t, self.T_CAI, 36)
            x = (k * 53) % 292
            y = (k * 37 - t * (6 + k % 5) - vy * t * .2) % (PALCO_H + 20) - 10
            tela.disco(x, y, 6 + k % 6, NUVD1 if k % 2 else NUVD0)
        for k in range(60):                              # gotinhas de nuvem (sobem em relação à nossa)
            x = (k * 47 + 11) % 292
            y = (k * 29 - t * (10 + (k % 4) * 3)) % (PALCO_H + 8) - 4
            gotinha(tela, x, y, 1.0 + (k % 3) * .6)
        gx, gy = self.p_gota(t)
        R = self.raio(t)
        # gotinhas indo de encontro à nossa (uma por bumbo)
        for i, e in enumerate(self.ev):
            if e - .45 <= t < e:
                u = (t - (e - .45)) / .45
                a = -math.pi / 2 + ((i * 1.3) % 1.6 - .8)
                d = lerp(46, R, u ** 1.4)
                gotinha(tela, gx + math.cos(a) * d, gy - abs(math.sin(a)) * d, 2.2, AGC, AGM)
            if e <= t < e + .22:
                tela.anel(gx, gy, R + 3 + (t - e) * 30, BRANCO, .5)
        rastro(tela, self.p_gota, t, n=8, dt=.05, r0=R * .4)
        prota(tela, gx, gy, R, t, achata=.1 * fase(t, self.TC1, self.TC1 + 2))
        if t < 6.5:
            self.rot(tela, 'GOTINHA DE NUVEM', 66, 150, BRANCO, alvo=(98, 166))
            self.rot(tela, 'CAI A ~1 CM/S', 66, 140, AMARELO)
        if 6.7 <= t < 13 and gy > 20:
            self.rot(tela, 'A NOSSA GOTA', int(gx) + 20, int(gy) - 30, AMARELO, alvo=(gx + R * .7, gy - R * .7))
        # contador
        if t >= self.TC0 and t < 32.5:
            n = int(self.conta(t))
            self.caixa_txt(tela, [('GOTINHAS JUNTADAS', 9, BRANCO), (fmt_num(n), 17, AMARELO)], 146, 6, centro=True)
        if 25.9 <= t < 31.9:
            self.comparacao(tela, t)
        if not VERTICAL and t >= 13.1 and t < 25.9:
            self.rot(tela, 'MAIOR CAI MAIS RÁPIDO', 186, 150, CIANO)
            seta(tela, 238, 140, 0, 1, CIANO, 5)
        mm = .02 * self.conta(t) ** (1 / 3)
        altm = 1400 - 400 * ease(fase(t, self.T_CAI, 36))
        self.painel(tela, t, alt=fmt_alt(altm), temp=fmt_temp(temp_de(altm)), tam=fmt_mm(mm),
                    dias=fmt_dias(2 if t < 20 else 3))

    def comparacao(self, tela, t):
        x0, y0 = 74, 140
        painel(tela, x0, y0, 146, 62, borda=AMARELO)
        gotinha(tela, x0 + 18, y0 + 30, 1.5, AGC, AGM)
        tela.texto('0,02', x0 + 18, y0 + 40, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto('MM', x0 + 18, y0 + 50, BRANCO, tam=9, centro=True, contorno=PRETO)
        gota(tela, x0 + 120, y0 + 28, 14)
        tela.texto('2 MM', x0 + 120, y0 + 46, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto('LARGURA X 100', x0 + 66, y0 + 10, BRANCO, tam=9, centro=True, contorno=PRETO)
        if t > 28.0:
            tela.texto('ÁGUA X', x0 + 66, y0 + 26, AMARELO, tam=9, centro=True, contorno=PRETO)
            tela.texto('1.000.000', x0 + 66, y0 + 37, AMARELO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for i, e in enumerate(self.ev):
            fx.put(pop(380 + 30 * min(10, i), .09), self.t0 + e, .24, .1 * math.sin(i))
        fx.put(fx.chiado(4.0, 300, 1500, ataque=.8), self.t0 + self.T_CAI, .1)


# ============================================================ 5 queda
class Queda(Cena):
    K = 4

    def alt(self, t):
        return 1000 - 960 * fase(t, 0, 41.5)

    def p_gota(self, t):
        return 146 + 2 * math.sin(t * .9), 74 + 1.5 * math.sin(t * 2.1)

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, PALCO_H, 0, 292)
        # nuvem ficando para cima, copa chegando por baixo
        ny = -10 - 50 * fase(t, 0, 8)
        nuvem_dia(tela, 120, ny, 140, True)
        nuvem_dia(tela, 230, ny + 6, 100, True)
        yc = PALCO_H + 30 - 62 * ease(fase(t, 36.0, 42.0))
        if yc < PALCO_H + 20: copa(tela, 0, 292, yc, t, seed=5, alt=12)
        # outras gotas caindo junto e o ar passando
        for k in range(16):
            x = (k * 59 + 17) % 292
            y = (k * 41 + t * 18 * (1 + k % 3 * .1)) % (PALCO_H + 20) - 10
            if abs(x - 146) < 24: continue
            gota(tela, x, y, 2 + (k % 3) * .6, .1 * (k % 3))
        for k in range(14):                                 # linhas de ar (sobem: a gota cai)
            x = (k * 23 + 40) % 292
            y = (PALCO_H - (t * 160 + k * 37) % (PALCO_H + 30))
            tela.linha(x, y, x, y + 9, CEUD3)
        gx, gy = self.p_gota(t)
        # forma de lágrima? não
        if t < 6.5:
            E11.gota(tela, 80, 154, 2.4, t, prota=False)
            xa = fase(t, 1.5, 2.0)
            if xa > 0:
                linha_grossa(tela, 66, 132, 66 + 28 * xa, 132 + 32 * xa, 3, VERMELHO)
                linha_grossa(tela, 94, 132, 94 - 28 * xa, 132 + 32 * xa, 3, VERMELHO)
            self.rot(tela, 'LÁGRIMA? NÃO', 54, 178, VERMELHO)
            gota(tela, 214, 154, 8)
            if t > 2.5:
                tela.linha(204, 170, 210, 176, VERDE); tela.linha(210, 176, 224, 162, VERDE)
                self.rot(tela, 'DE VERDADE', 186, 178, VERDE)
        elif t < 25.9:
            self.formas(tela, t)
        elif t < 31.9:
            self.caixa_txt(tela, [('VELOCIDADE', 9, BRANCO), ('6,5 M/S', 17, AMARELO), ('= 23 KM/H', 9, BRANCO)], 146, 128, centro=True)
        else:
            self.corrida(tela, t)
        rastro(tela, self.p_gota, t, n=6, dt=.05)
        # linhas de vento grudadas na gota
        for k in range(5):
            u = (t * 3 + k * .2) % 1.0
            tela.px(gx - 12 + k * 6, gy + 14 - u * 40, BRANCO)
        prota(tela, gx, gy, 12, t, achata=.12)
        if t > .8 and t < 25.9:
            self.rot(tela, 'A NOSSA GOTA: 2 MM', int(gx) + 20, int(gy) - 26, AMARELO, alvo=(gx + 9, gy - 8))
        if not VERTICAL and t > 1:
            self.rot(tela, 'TEMPO ACELERADO', 194, 4, ACO4)
        altm = self.alt(t)
        self.painel(tela, t, alt=fmt_alt(altm), temp=fmt_temp(temp_de(altm)), tam='2 MM', dias=fmt_dias(3))

    def formas(self, tela, t):
        """A régua das formas: redonda, pão de hambúrguer, rasgando."""
        y = 160
        painel(tela, 60, 118, 172, 84, borda=ACO2)
        tela.texto('FORMA DA GOTA CAINDO', 146, 122, ACO3, tam=9, centro=True, contorno=PRETO)
        gota(tela, 84, y, 5)
        tela.texto('PEQUENA', 84, y + 18, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto('REDONDA', 84, y + 28, AGC, tam=9, centro=True, contorno=PRETO)
        if t >= 13.1:
            a = .55 + .05 * math.sin(t * 6)
            gota(tela, 144, y, 11, achata=a)
            tela.texto('MAIOR', 144, y + 18, BRANCO, tam=9, centro=True, contorno=PRETO)
            tela.texto('HAMBÚRGUER', 144, y + 28, AGC, tam=9, centro=True, contorno=PRETO)
        if t >= 19.5:
            u = ((t - 19.5) % 3.0) / 3.0
            if u < .55:
                gota(tela, 204, y, 12 + 3 * u, achata=.7, covo=u * 1.2)
            else:
                v = (u - .55) / .45
                for k in range(5):
                    a = -math.pi / 2 + (k - 2) * .55
                    gota(tela, 204 + math.cos(a) * 14 * v, y + 2 - math.sin(a) * 6 * v + 10 * v, 3 + (k % 2), .2)
            tela.texto('GRANDE', 204, y + 18, BRANCO, tam=9, centro=True, contorno=PRETO)
            tela.texto('SE PARTE', 204, y + 28, VERMELHO, tam=9, centro=True, contorno=PRETO)

    def corrida(self, tela, t):
        """1 km de queda: a gota de 2 mm leva ~2,5 min; a gotinha, mais de 1 dia."""
        painel(tela, 60, 118, 172, 84, borda=ACO2)
        tela.texto('PARA CAIR 1 KM', 146, 122, ACO3, tam=9, centro=True, contorno=PRETO)
        u = ease(fase(t, 32.2, 35.5))
        for j, (nm, val, f, cor) in enumerate((('GOTA 2 MM', '~2,5 MIN', 1.0, AGC), ('GOTINHA', '+ DE 1 DIA', .0016, NUVD2))):
            y = 140 + j * 28
            tela.texto(nm, 68, y, BRANCO, tam=9, contorno=PRETO)
            tela.texto(val, 226, y, AMARELO, tam=9, centro='d', contorno=PRETO)
            tela.ret(68, y + 11, 156, 7, PRETO)
            w = max(1, int(154 * u * f))
            tela.ret(69, y + 12, w, 5, cor)
            tela.ret(69 + w, y + 12, 154 - w, 5, FUNDO2)

    def sons(self, fx):
        fx.put(fx.chiado(42.0, 300, 1100, ataque=2.0), self.t0, .06)
        fx.put(tique(1100, .08), self.t0 + 1.6, .14)
        fx.put(tique(1650, .08), self.t0 + 2.6, .14)
        for a in (6.7, 13.1, 19.5): fx.put(tique(990, .08), self.t0 + a + .1, .12)
        for k in range(4):
            fx.put(pop(300, .1), self.t0 + 19.5 + k * 3.0 + 1.65, .14)


# ============================================================ 6 floresta
YB = 150                      # chão (base do tronco)
TX = 146                      # x do tronco
FOLHA_ALVO = (186, 26)        # folha onde fica o estômato
LUPA_F = (196, 120, 38)


class Floresta(Cena):
    K = 5
    CAM = [(0.0, 128, -12), (2.6, 116, 28), (3.4, 112, 36), (4.2, 104, 60), (5.0, 100, 70),
           (6.4, 98, YB - 1), (9.5, 106, 164), (10.5, 110, 168), (13.1, TX, YB), (19.0, TX, YB - 106),
           (21.0, FOLHA_ALVO[0], FOLHA_ALVO[1])]

    def p_gota(self, t):
        if t >= 21.0:
            if t < 28.0: return FOLHA_ALVO
            u = t - 28.0
            return FOLHA_ALVO[0] - 1.5 * u + 2 * math.sin(u), FOLHA_ALVO[1] - 3.2 * u
        for (ta, xa, ya), (tb, xb, yb) in zip(self.CAM, self.CAM[1:]):
            if ta <= t < tb:
                u = (t - ta) / (tb - ta)
                if ta == 0.0 or ta == 4.2 + .8: u = u * u
                return lerp(xa, xb, u), lerp(ya, yb, u)
        return self.CAM[-1][1:]

    def onde(self, t):
        if t < 6.4: return 'NAS FOLHAS'
        if t < 10.5: return 'NO SOLO'
        if t < 13.1: return 'NA RAIZ'
        if t < 19.0: return 'NO TRONCO'
        if t < 28.0: return 'NA FOLHA'
        return 'NO AR'

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, YB + 2, 0, 292)
        copa(tela, 0, 292, YB + 6, t, seed=7, alt=60)
        # solo em corte
        grad_v(tela, 0, YB, 292, PALCO_H - YB, [SOLO2, SOLO1, SOLO0, SOLO0])
        tela.ret(0, YB, 292, 2, FOL1)
        for k in range(30):
            x = (k * 41) % 292; y = YB + 6 + (k * 17) % (PALCO_H - YB - 8)
            tela.px(x, y, SOLO2 if k % 2 else SOLO0)
        if 6.4 < t < 13.5:                              # mancha molhada no solo
            a = fase(t, 6.4, 8.0) * (1 - fase(t, 12.0, 13.5))
            aura(tela, 104, 162, 0, 6 + 8 * a, AGM, 0)
        E11.arvore  # (só leitura)
        D.arvore_grande(tela, TX, YB, t, h=106, xilema=fase(t, 12.0, 13.0), fluxo=1.0 if t > 13 else 0.0)
        # a protagonista
        x, y = self.p_gota(t)
        if t < 6.4:
            rastro(tela, self.p_gota, t, n=8, dt=.05, r0=2.5)
            prota(tela, x, y, 5, t, achata=.15)
        elif t < 21.0:
            rastro(tela, self.p_gota, t, n=10, dt=.12, r0=2)
            prota(tela, x, y, 3, t)
        elif t >= 28.0:
            rastro(tela, self.p_gota, t, n=12, dt=.15, r0=1.6)
            vapor_prota(tela, x, y, t)
        else:
            vapor_prota(tela, x, y, t, 1.5)
        # vapor saindo de toda a floresta
        if t > 26.0:
            dens = fase(t, 26, 30) + fase(t, 37.9, 40)
            for k in range(int(26 * dens)):
                per = 5.0 + k % 4
                u = ((t + k * .73) % per) / per
                px = (k * 37) % 292 - u * 20
                py = 60 - u * 70 + (k * 13) % 30
                if py > 2 and (k + int(t * 8)) % 2: tela.px(px, py, ESPUMA)
        # rótulos
        if 6.7 <= t < 13.1: self.rot(tela, 'RAIZ', 70, 186, TRO2, alvo=(112, 168))
        if 13.1 <= t < 19.5: self.rot(tela, 'XILEMA', 160, 100, ESPUMA, alvo=(TX + 1, 104))
        if t < 6.4 and t > .8:
            self.rot(tela, 'A NOSSA GOTA', int(x) - 80, int(y) - 4, AMARELO, alvo=(x - 6, y))
        if 19.5 <= t < 31.7:
            self.lupa(tela, t)
        if 31.9 <= t < 37.8:
            self.barra(tela, t)
        if 37.9 <= t < 43.8:
            n = int(1000 * ease(fase(t, 38.1, 42.5)))
            self.caixa_txt(tela, [('ESTA ÁRVORE, HOJE:', 9, BRANCO),
                                  (('+ DE ' if n >= 1000 else '') + f"{fmt_num(n)} L", 17, ESPUMA)], 146, 158, centro=True)
        dias = 3 + int(9 * fase(t, 6.4, 13.1))
        tam = '2 MM' if t < 6.4 else ('MOLÉCULA' if t >= 21 else 'MISTURADA')
        if t >= 28: tam = 'VAPOR'
        self.painel(tela, t, linhas=[('ONDE ESTÁ', self.onde(t), FOL4), ('TEMPERATURA', fmt_temp(T_MAR), CHAMA1),
                                     ('TAMANHO DA GOTA', tam, AGC), ('DIAS DE VIAGEM', fmt_dias(dias), AMARELO)])

    def lupa(self, tela, t):
        cx, cy, r = LUPA_F
        if VERTICAL: cx = min(cx, self.VX + 88 - r - 4)
        r = r * ease(fase(t, 19.5, 20.3)) * (1 - ease(fase(t, 31.0, 31.7)))
        if r < 3: return
        fundo = tela.buf[:PALCO_H].copy()
        LG.dither(tela, cx - r, cy - r, 2 * r, 2 * r, CEUD3, CEUD2)
        abre = fase(t, 21.5, 24.5)
        sx, sy = D.folha_corte(tela, int(cx - 36), int(cy - 30), 72, 34, t, abre)
        if t < 26.0:
            u = fase(t, 20.4, 25.0)
            mx, my = lerp(cx - 18, sx, u), lerp(cy - 20, sy - 6, u)
        else:
            u = ease(fase(t, 26.0, 29.0))
            mx, my = sx + 4 * u, sy + 30 * u
        molecula(tela, mx, my, t * 3, .8, prota_=True, t=t)
        for k in range(5):                                   # outras saindo
            if t > 25:
                u = ((t + k * .6) % 3.0) / 3.0
                molecula(tela, sx - 6 + k * 3, sy + 4 + u * 30, t * 2 + k, .6, AGC)
        recortar_disco(tela, cx, cy, r, fundo)
        lupa(tela, cx, cy, r, alvo=FOLHA_ALVO)
        if r > 30:
            self.rot(tela, 'ESTÔMATO', int(cx - 24), int(cy + r - 13), FOL4)
            self.rot(tela, 'FOLHA', int(cx - 14), int(cy - r + 4), FOL4)

    def barra(self, tela, t):
        x0, y0, w = 62, 160, 168
        painel(tela, x0 - 6, y0 - 6, w + 12, 46, borda=ESPUMA)
        tela.texto('ÁGUA QUE A RAIZ PUXA', x0, y0 - 2, BRANCO, tam=9, contorno=PRETO)
        u = ease(fase(t, 32.2, 34.5))
        tela.ret(x0, y0 + 10, w, 10, PRETO)
        wv = int((w - 2) * .98 * u)
        tela.ret(x0 + 1, y0 + 11, wv, 8, ESPUMA)
        tela.ret(x0 + 1 + wv, y0 + 11, w - 2 - wv, 8, FOL3 if u > .99 else FUNDO2)
        tela.texto('VIRA VAPOR: 97% A 99,5%', x0, y0 + 24, ESPUMA, tam=9, contorno=PRETO)

    def sons(self, fx):
        for tt, f in ((2.6, 1500), (3.4, 1300), (4.2, 1250), (5.0, 1100)):
            fx.put(pinga(f, .14), self.t0 + tt, .22, -.2)
        fx.put(respingo_som(fx, .3), self.t0 + 6.4, .2)
        fx.put(fx.chiado(3.0, 200, 700, ataque=1.0), self.t0 + 6.8, .06)
        for k in range(12):
            fx.put(tique(500 + k * 60, .05), self.t0 + 13.1 + k * .5, .07)
        fx.put(tique(1800, .07), self.t0 + 21.6, .14)
        fx.put(fx.chiado(2.6, 1200, 4000, ataque=.4), self.t0 + 26.0, .07)
        for k in range(10):
            fx.put(tique(1320 + k * 40, .04), self.t0 + 38.1 + k * .44, .08)


# ============================================================ 7 rios voadores
CAM_RIO = [(-36, 1.0), (-42, 0.0), (-48, -1.4), (-54, -2.6), (-60, -3.8), (-66, -5.6), (-71.5, -8.6),
           (-71.5, -12.5), (-68, -16.0), (-63, -18.0), (-57, -19.5), (-51.5, -21.0), (-47.0, -22.8)]
U_FLOR, U_ANDES, U_SE = .30, .52, 1.0


class Rios(Cena):
    K = 6

    def mapa(self):
        return D.Mapa(x0=44, y0=2, s=3.9) if VERTICAL else D.Mapa(x0=38, y0=2, s=4.2)

    def u_prota(self, t):
        if t < 13.1: return lerp(U_FLOR, .36, t / 13.1)
        if t < 19.3: return lerp(.36, U_ANDES, ease(fase(t, 13.1, 19.3)))
        if t < 39.5: return lerp(U_ANDES, .86, fase(t, 19.5, 39.5))
        return lerp(.86, U_SE, ease(fase(t, 39.5, 45.0)))

    def ponto(self, M, u):
        pts = [M.p(lo, la) for lo, la in CAM_RIO]
        return caminho(pts, u)

    def desenhar(self, tela, t, tg):
        M = self.mapa()
        M.desenhar(tela, t, 292)
        pts = [M.p(lo, la) for lo, la in CAM_RIO]
        # o rio voador: faixa pontilhada que corre
        rev = um(.38 + .62 * ease(fase(t, 1.0, 26.0)))
        n = 120
        for i in range(int(n * rev)):
            u = i / n
            x, y = caminho(pts, u)
            w = 4 + 2 * math.sin(u * 9)
            if (i + int(t * 12)) % 3 != 0:
                for dy in range(-int(w), int(w) + 1, 2):
                    tela.px(x + (dy % 3) - 1, y + dy, ESPUMA if abs(dy) < w * .5 else CIANO)
        for k in range(14):                                     # bolinhas de vapor correndo
            u = ((t * .045 + k / 14) % 1.0) * rev
            x, y = caminho(pts, u)
            tela.disco(x, y, 1.6, BRANCO)
        # alísios saindo do Atlântico
        if 6.7 <= t < 26:
            for k in range(4):
                xa, ya = M.p(-28 + 0, 2 - k * 3.5)
                u = (t * .5 + k * .25) % 1.0
                x = xa - u * 40
                if x < M.p(-35, 0)[0] + 2 and k > 1: continue
                tela.linha(x, ya, x + 10, ya, BRANCO); seta(tela, int(x), int(ya), -1, 0, BRANCO, 3)
        # a nossa molécula
        fn = lambda tt: self.ponto(M, self.u_prota(tt))
        rastro(tela, fn, t, n=12, dt=.3, r0=2.0)
        x, y = fn(t)
        vapor_prota(tela, x, y, t, 2.4)
        if t >= 13.1:                                           # a parede dos Andes
            ax, ay = M.p(-76.5, -10)
            if t < 26: aura(tela, ax, ay, 2, 10 + 2 * math.sin(t * 5), AND2, int(t * 6) % 2)
        if t >= 39.5:
            sx, sy = M.p(-47.0, -22.8)
            tela.anel(sx, sy, 6 + 3 * ((t * 1.5) % 1), AMARELO, .6)
        # rótulos
        lab = lambda s, lo, la, cor, ali=False: self.rot(tela, s, int(M.p(lo, la)[0]), int(M.p(lo, la)[1]), cor, centro=ali)
        lab('ATLÂNTICO', -42, 8.5, MAR2)
        lab('AMAZÔNIA', -63, 0.8, FOL4, True)
        if t >= 13.1: self.rot(tela, 'ANDES', int(M.p(-80, -16)[0]) + (6 if VERTICAL else 0), int(M.p(-80, -16)[1]), AND2)
        if t >= 19.5:
            lab('CENTRO-OESTE', -60, -12.5, CER1)
            lab('SUDESTE', -45.0, -19.0, CHAMA1)
            lab('SUL', -55, -28, BRANCO)
        if 25.9 <= t < 39.4:
            self.barras(tela, t, M)
        dias = 12 + int(6 * fase(t, 0, 45))
        onde = 'AMAZÔNIA' if t < 17 else ('ANDES' if t < 21 else ('CENTRO-OESTE' if t < 39.5 else 'SUDESTE'))
        self.painel(tela, t, linhas=[('ONDE ESTÁ', onde, ESPUMA),
                                     ('RIO VOADOR', '20 BI T/DIA' if t >= 25.9 else '?', ESPUMA if t >= 25.9 else ACO2),
                                     ('RIO AMAZONAS', '17 BI T/DIA' if t >= 32.7 else '?', AGC if t >= 32.7 else ACO2),
                                     ('DIAS DE VIAGEM', fmt_dias(dias), AMARELO)])

    def barras(self, tela, t, M):
        x0 = 150 if not VERTICAL else 124
        y0, w = 150, 110
        painel(tela, x0 - 6, y0 - 6, w + 12, 54, borda=ESPUMA)
        tela.texto('TONELADAS DE ÁGUA/DIA', x0, y0 - 2, BRANCO, tam=9, contorno=PRETO)
        for j, (nm, v, ta, cor) in enumerate((('NO CÉU', 20, 25.9, ESPUMA), ('NO RIO', 17, 32.7, AGC))):
            if t < ta: continue
            y = y0 + 10 + j * 18
            f = ease(fase(t, ta + .2, ta + 1.8)) * v / 20
            tela.texto(nm, x0, y + 1, BRANCO, tam=9, contorno=PRETO)
            tela.ret(x0 + 40, y, int((w - 40) * f), 8, PRETO)
            tela.ret(x0 + 41, y + 1, max(0, int((w - 40) * f) - 2), 6, cor)
            tela.texto(f"{v} BI", x0 + 42 + int((w - 40) * f) - 30, y + 10, cor, tam=9, contorno=PRETO) if f > .9 else None

    def sons(self, fx):
        for k in range(8):
            fx.put(fx.chiado(6.4, 180, 800, ataque=1.5), self.t0 + k * 6.0, .07, -.3 + .1 * k)
        fx.put(pop(160, .25), self.t0 + 19.3, .3)
        fx.put(tique(1320, .1), self.t0 + 26.1, .14)
        fx.put(tique(1180, .1), self.t0 + 32.9, .14)
        fx.put(fx.sino(84, 1.0), self.t0 + 45.0, .2)


# ============================================================ 8 sudeste
MORRO_SE = [(-2, 120), (30, 96), (64, 100), (96, 122), (130, 138), (170, 146), (230, 150), (294, 152)]
CORR_SE = [(64, 101), (78, 112), (94, 124), (110, 134), (132, 142), (160, 150), (196, 156), (224, 160)]
DAM_X = 252


class Sudeste(Cena):
    K = 7

    def p_gota(self, t):
        if t < 13.1: return 70 + 4 * math.sin(t), 40
        if t < 16.0:
            u = fase(t, 13.1, 16.0) ** 2
            return lerp(70, 64, u), lerp(46, 100, u)
        if t < 19.5: return ao_longo(CORR_SE, .45 * suave(fase(t, 16.0, 19.5)))
        if t < 25.5: return ao_longo(CORR_SE, .45 + .55 * suave(fase(t, 19.5, 25.5)))
        return 224 + 10 * fase(t, 25.5, 30) + 2 * math.sin(t), 162 + math.sin(t * 2)

    def onde(self, t):
        if t < 13.1: return 'NA NUVEM'
        if t < 16.0: return 'CAINDO'
        if t < 19.5: return 'NO CÓRREGO'
        if t < 24.5: return 'NO RIO'
        return 'NA REPRESA'

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, PALCO_H, 0, 292)
        fundo = [(x, 92 - 16 * math.sin(x * .025 + .6) - 6 * math.sin(x * .08)) for x in range(-4, 300, 8)]
        morro(tela, fundo, GRAMA0, TRACO)
        poligono(tela, [(-2, PALCO_H)] + MORRO_SE + [(294, PALCO_H)], GRAMA1)
        for (ax, ay), (bx, by) in zip(MORRO_SE, MORRO_SE[1:]): tela.linha(ax, ay, bx, by, GRAMA2)
        for x in (10, 22, 40, 120, 150, 190):
            arvore(tela, x, interp(MORRO_SE, x) + 2, 12 + x % 4)
        # córrego e rio
        for (ax, ay), (bx, by) in zip(CORR_SE, CORR_SE[1:]):
            w = 3 + 6 * (ax - 64) / 160
            linha_grossa(tela, ax, ay, bx, by, w + 2, PRETO)
            linha_grossa(tela, ax, ay, bx, by, w, AGM)
        for k in range(18):
            p = ao_longo(CORR_SE, (k / 18 + t * .1) % 1.0)
            tela.px(p[0], p[1] - 1, ESPUMA if k % 3 == 0 else AGC)
        # represa e barragem
        agua(tela, 200, DAM_X, 156, 178, t, onda=.6)
        E11.concreto(tela, [(DAM_X, 140), (DAM_X + 10, 140), (DAM_X + 26, 196), (DAM_X, 196)], t)
        agua(tela, DAM_X + 26, 292, 186, 198, t, onda=.4)
        tela.ret(200, 178, DAM_X - 200, PALCO_H - 178, TERRA0)
        # nuvem crescendo e chovendo
        g = fase(t, 0, 9)
        dx = math.sin(t * .2) * 5
        if t < 6.7:
            for k in range(5):                                   # ar subindo pelo morro
                u = ((t * .4 + k * .2) % 1.0)
                tela.px(40 + k * 12, 110 - u * 60, BRANCO); seta(tela, 40 + k * 12, int(108 - u * 60), 0, -1, BRANCO, 3)
        if 6.7 <= t < 12.9:
            for i, b in enumerate(self.beats(6.7, 12.9)):
                if b <= t < b + .3:
                    a = i * 2.1
                    tela.anel(70 + math.cos(a) * 30, 34 + math.sin(a) * 10, 1 + (t - b) * 14, BRANCO, .5)
        if t >= 12.5:
            chuva(tela, 10, 200, 46, PALCO_H, t, n=40, vel=150, chao=lambda x: interp(MORRO_SE, x))
        nuvem_dia(tela, 80 + dx, 30, 60 + 50 * g, carregada=t > 9)
        nuvem_dia(tela, 190 + dx * .5, 24, 30 + 40 * g, carregada=t > 9)
        # a gota
        x, y = self.p_gota(t)
        if t < 13.1:
            vapor_prota(tela, x, y, t) if t < 8 else prota(tela, x, y, 2 + 2 * fase(t, 8, 12.5), t)
        else:
            rastro(tela, self.p_gota, t, n=8, dt=.08, r0=2)
            prota(tela, x, y, 4 if t < 16 else 3, t)
        if 15.95 < t < 16.6: E11.respingo(tela, 64, 100, (t - 15.95) / .65)
        if t > 1 and t < 26:
            self.rot(tela, 'A NOSSA GOTA', int(x) + 12, int(y) - 22 if y > 40 else int(y) + 12, AMARELO, alvo=(x + 4, y - 4 if y > 40 else y + 4))
        if 13.1 <= t: self.rot(tela, 'CÓRREGO', 92, 104, AGC, alvo=(98, 126))
        if 19.5 <= t: self.rot(tela, 'RIO', 160, 166, AGC)
        if 19.5 <= t: self.rot(tela, 'REPRESA', 206, 182, ESPUMA)
        if 19.5 <= t: self.rot(tela, 'BARRAGEM', 238, 124, CONC2, alvo=(DAM_X + 4, 142))
        if 25.9 <= t:
            E11.lampada(tela, 280, 100, .5 + .5 * math.sin(t * 3) ** 2 if t > 27 else 0.0, t, fio_ate=86)
            tela.linha(DAM_X + 20, 180, 280, 112, AMARELO) if t > 27 and int(t * 4) % 2 else None
        if 32.7 <= t:
            self.cartao(tela, t)
        dias = 18 + int(fase(t, 13, 26))
        tam = 'VAPOR' if t < 8 else ('0,02 MM' if t < 11 else '2 MM')
        if t >= 16: tam = 'NO RIO'
        self.painel(tela, t, linhas=[('ONDE ESTÁ', self.onde(t), CHAMA1), ('TAMANHO DA GOTA', tam, AGC),
                                     ('DIAS DE VIAGEM', fmt_dias(dias), AMARELO), ('PRÓXIMA PARADA', 'O MAR', MAR2)])

    def cartao(self, tela, t):
        u = ease(fase(t, 32.7, 33.4))
        x0, y0, w, h = 54, 50 + int((1 - u) * 160), 186, 64
        painel(tela, x0, y0, w, h, borda=AMARELO)
        tela.texto('A JORNADA CONTINUA', x0 + w // 2, y0 + 6, ACO3, tam=9, centro=True, contorno=PRETO)
        tela.texto('EPISÓDIO DA ÁGUA', x0 + w // 2, y0 + 18, AMARELO, tam=17, centro=True, contorno=PRETO)
        tela.texto('DA REPRESA ATÉ A SUA TOMADA', x0 + w // 2, y0 + 40, BRANCO, tam=9, centro=True, contorno=PRETO)
        prota(tela, x0 + 16, y0 + 50, 3, t)
        k = int(t * 3) % 3
        for j in range(3):
            seta(tela, x0 + 132 + j * 10, y0 + 50, 1, 0, AMARELO if j == k else ACO1, 4)
        E11.lampada(tela, x0 + w - 14, y0 + 44, 1.0, t, fio_ate=y0 + 38)

    def sons(self, fx):
        fx.put(fx.chiado(6.0, 200, 800, ataque=1.0), self.t0, .06)
        for b in self.beats(6.7, 12.9):
            fx.put(pop(620, .06), self.t0 + b, .14)
        fx.put(fx.chiado(29.0, 2500, 7000, ataque=1.0), self.t0 + 12.6, .045)
        fx.put(respingo_som(fx), self.t0 + 16.0, .24)
        fx.put(pinga(1250), self.t0 + 16.0, .18)
        fx.put(fx.chiado(10.0, 300, 1200, ataque=1.5), self.t0 + 16.0, .06)
        fx.put(tique(1320, .1), self.t0 + 33.0, .14)


# ============================================================ 9 de volta ao mar
RIO_MAR = [(-4, 44), (30, 52), (60, 70), (84, 64), (110, 78), (140, 96), (164, 104), (184, 118)]
COSTA_X = 186
SUP_M = 118


class Mar(Cena):
    K = 8

    def p_gota(self, t):
        if t < 13.1: return ao_longo(RIO_MAR, suave(fase(t, 0.5, 13.1)))
        if t < 19.5:
            u = ease(fase(t, 13.1, 16.0))
            return lerp(184, 214, u), SUP_M + 4 + 4 * u
        if t < 25.9:
            u = suave(fase(t, 19.5, 24.5))
            return 214 + 20 * u + 3 * math.sin(t), lerp(126, 186, u)
        u = ease(fase(t, 25.9, 30.0))
        if t < 30.0: return 234 - 10 * u, lerp(186, SUP_M + 2, u)
        v = t - 30.0
        return 224 - 2 * v, SUP_M - 2 - 9 * v

    def desenhar(self, tela, t, tg):
        ceu_dia(tela, SUP_M + 2, 0, 292)
        sol(tela, 262, 22, 10, t)
        # planície e o rio
        terra = [(-2, 40), (60, 54), (120, 80), (170, 104), (COSTA_X, SUP_M + 2)]
        poligono(tela, [(-2, PALCO_H)] + terra + [(COSTA_X, PALCO_H)], GRAMA1)
        grad_v(tela, 0, 60, COSTA_X, PALCO_H - 60, [GRAMA1, GRAMA0, TERRA0], mascara=lambda xx, yy: yy > np.array([interp(terra, x) + 8 for x in range(0, COSTA_X)])[np.minimum(xx, COSTA_X - 1)])
        for x in (14, 40, 70, 100, 130):
            arvore(tela, x, interp(terra, x) + 3, 11)
        for (ax, ay), (bx, by) in zip(RIO_MAR, RIO_MAR[1:]):
            linha_grossa(tela, ax, ay, bx, by, 8, PRETO)
            linha_grossa(tela, ax, ay, bx, by, 6, AGM)
        for k in range(20):
            p = ao_longo(RIO_MAR, (k / 20 + t * .06) % 1.0)
            tela.px(p[0], p[1], ESPUMA if k % 3 == 0 else AGC)
        # o mar em corte
        mar(tela, COSTA_X - 4, 292, SUP_M, t, onda=1.0)
        LG.dither(tela, COSTA_X, 176, 292 - COSTA_X, PALCO_H - 176, AGP, MAR0)
        poligono(tela, [(COSTA_X - 6, SUP_M + 2), (COSTA_X + 14, PALCO_H), (COSTA_X - 6, PALCO_H)], TERRA1)
        for k in range(8):
            x = COSTA_X + 10 + (k * 23 + int(t * 7)) % (292 - COSTA_X - 14)
            tela.ret(x, SUP_M + 8 + (k % 4) * 14, 5, 1, MAR2)
        # a gota
        x, y = self.p_gota(t)
        rastro(tela, self.p_gota, t, n=10, dt=.12, r0=2)
        if t < 30.0: prota(tela, x, y, 3, t)
        else: vapor_prota(tela, x, y, t)
        if t < 13.1 and t > 1: self.rot(tela, 'RIO', 40, 74, AGC)
        if t > 13.1: self.rot(tela, 'OCEANO ATLÂNTICO', 196, 134, MAR2)
        if 19.5 <= t < 26:
            self.caixa_txt(tela, [('AQUI, EM MÉDIA:', 9, BRANCO), ('3.200 ANOS', 17, AMARELO)], 30, 140)
        if 6.7 <= t < 13:
            self.caixa_txt(tela, [('NO RIO, EM MÉDIA:', 9, BRANCO), ('2 A 6 MESES', 17, AMARELO)], 60, 150)
        if t >= 25.9 and t < 31.9:
            for k in range(5):
                u = (t * .9 + k * .23) % 1.0
                tela.px(250 - k * 12 - u * 20, 36 + u * 70, SOL0)
        if t >= 31.9:
            tela.anel(x, y, 8 + 2 * math.sin(t * 4), AMARELO, .6)
            self.rot(tela, 'DE VOLTA AO INÍCIO', int(x) - 100, int(y) - 4, AMARELO)
        dias = 19 + int(111 * suave(fase(t, 0.5, 13.1)))
        onde = 'NO RIO' if t < 13.1 else ('NO MAR' if t < 19.5 else ('NO FUNDO DO MAR' if t < 26 else ('NO MAR' if t < 30 else 'NO AR')))
        self.painel(tela, t, linhas=[('ONDE ESTÁ', onde, MAR2), ('TEMPO MÉDIO AQUI',
                                     '2 A 6 MESES' if t < 13.1 else '3.200 ANOS' if t < 30 else '9 DIAS', AMARELO),
                                     ('DIAS DE VIAGEM', fmt_dias(dias), AMARELO), ('ETAPAS FEITAS', f"{9 if t > 13 else 8} DE 9", VERDE)])

    def sons(self, fx):
        fx.put(fx.chiado(13.0, 300, 1200, ataque=1.5), self.t0, .06)
        for k in range(6):
            fx.put(fx.chiado(4.6, 150, 700, ataque=1.2), self.t0 + 13.0 + k * 4.0, .07)
        fx.put(pinga(900, .25), self.t0 + 13.4, .2)
        fx.put(pinga(1500, .3), self.t0 + 30.0, .2)
        fx.put(fx.sino(81, 1.0), self.t0 + 31.9, .18)


# ============================================================ tempo de residência
RESID = [('ATMOSFERA', 'SÓ 9 DIAS', 9, None, 6.7, CEUD3),
         ('UMIDADE DO SOLO', '1 A 2 MESES', 30, 60, 6.7, SOLO2),
         ('RIOS', '2 A 6 MESES', 60, 180, 6.7, AGC),
         ('GELEIRAS', '20 A 100 ANOS', 20 * 365, 100 * 365, 13.1, NUVD2),
         ('OCEANOS', '3.200 ANOS', 3200 * 365, None, 13.1, MAR2),
         ('ÁGUA SUBTERRÂNEA FUNDA', '10.000 ANOS', 10000 * 365, None, 19.5, TRO2)]
DEC_MAX = 6.8                 # escala: 1 dia (10^0) até 10^6,8 dias


class Tempo(Cena):
    K = -1

    def desenhar(self, tela, t, tg):
        grade(tela)
        if VERTICAL:
            x0, x1, y0, dy, tit_y = self.VX - 84, self.VX + 84, 22, 30, 4
        else:
            x0, x1, y0, dy, tit_y = 176, 462, 30, 26, 6
        tela.texto('TEMPO MÉDIO DA ÁGUA EM CADA LUGAR', self.VX if VERTICAL else W // 2, tit_y + (14 if VERTICAL else 0),
                   ACO3, tam=9, centro=True, contorno=PRETO)
        if not VERTICAL:
            # eixo (escala de 10 em 10 vezes)
            ya = y0 + dy * len(RESID) + 2
            for d, nm in ((1, '1 DIA'), (30, '1 MÊS'), (365, '1 ANO'), (36500, '100 ANOS'), (3650000, '10.000 ANOS')):
                x = x0 + (x1 - x0) * math.log10(d) / DEC_MAX
                tela.ret(int(x), y0 - 4, 1, ya - y0 + 4, FUNDO3)
                tela.texto(nm, int(x), ya + 4, ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto('CADA PASSO DA ESCALA = MUITO MAIS TEMPO', W // 2, ya + 18, ACO1, tam=9, centro=True)
        for i, (nm, val, a, b, ta, cor) in enumerate(RESID):
            if t < ta: continue
            y = y0 + i * dy
            f = ease(fase(t, ta + i % 3 * .4, ta + i % 3 * .4 + 1.6))
            xa = x0 + (x1 - x0) * math.log10(a) / DEC_MAX
            xb = x0 + (x1 - x0) * math.log10(b) / DEC_MAX if b else None
            if VERTICAL:
                tela.texto(nm, x0, y - 10, BRANCO, tam=9, contorno=PRETO)
                tela.texto(val, x1, y - 10, cor, tam=9, centro='d', contorno=PRETO)
            else:
                tela.texto(nm, x0 - 6, y - 1, BRANCO, tam=9, centro='d', contorno=PRETO)
            xf = x0 + (xa - x0) * f
            tela.ret(x0, y, int(xf - x0) + 1, 8, PRETO)
            tela.ret(x0 + 1, y + 1, int(xf - x0) - 1, 6, cor)
            tela.ret(x0 + 1, y + 1, int(xf - x0) - 1, 1, BRANCO)
            if xb and f >= 1:
                g = ease(fase(t, ta + 2.0, ta + 3.0))
                LG.dither(tela, xa, y + 1, (xb - xa) * g, 6, cor, FUNDO)
            if f > 0 and f < 1:
                gota(tela, xf, y + 4, 3)
            if not VERTICAL and f >= 1:
                tela.texto(val, int((xb or xa)) + 6, y - 1, cor, tam=9, contorno=PRETO)
        # a nossa gota pulando de lugar em lugar
        k = min(len(RESID) - 1, int((t * .7) % len(RESID)))
        vis = [i for i, r in enumerate(RESID) if t >= r[4] + 1.6]
        if vis:
            i = vis[int(t * .6) % len(vis)]
            r = RESID[i]
            xa = x0 + (x1 - x0) * math.log10(r[2]) / DEC_MAX
            prota(tela, xa, y0 + i * dy + 4, 3, t)
        if t >= 25.9:
            y = y0
            tela.anel(x0 + (x1 - x0) * math.log10(9) / DEC_MAX, y + 4, 8 + 2 * math.sin(t * 5), AMARELO, .6)

    def sons(self, fx):
        for i, r in enumerate(RESID):
            fx.put(tique(660 * 2 ** (i * 2 / 12), .09), self.t0 + r[4] + i % 3 * .4, .13)


# ============================================================ resumo
class Resumo(Cena):
    LIGA = [0.8, 2.0, 3.4, 4.8, 7.0, 8.6, 10.6, 14.0, 16.4]
    CX, CY, RR = 146, 104, 78

    def p_ic(self, i):
        a = -math.pi / 2 + i * 2 * math.pi / 9
        return self.CX + math.cos(a) * self.RR, self.CY + math.sin(a) * self.RR * .98

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 292)
        tela.anel(self.CX, self.CY, self.RR, FUNDO3, .6)
        for i in range(9):
            a = -math.pi / 2 + (i + .5) * 2 * math.pi / 9
            if t >= self.LIGA[i]:
                seta(tela, int(self.CX + math.cos(a) * self.RR), int(self.CY + math.sin(a) * self.RR), -math.sin(a) > 0 and -1 or 1, 0, ETAPAS[i][1], 3)
        for i in range(9):
            x, y = self.p_ic(i)
            D.icone(tela, i, x, y, t, aceso=t >= self.LIGA[i])
        sol(tela, self.CX, self.CY - 6, 9, t)
        tela.texto('O CICLO', self.CX, self.CY + 14, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto('DA ÁGUA', self.CX, self.CY + 24, BRANCO, tam=9, centro=True, contorno=PRETO)
        # a gota dando a volta
        def fn(tt):
            k = sum(1 for a in self.LIGA if tt >= a) - 1
            if k < 0: return self.p_ic(0)
            if tt >= 20.7:
                a = -math.pi / 2 + (tt - 20.7) * 1.2
                return self.CX + math.cos(a) * self.RR, self.CY + math.sin(a) * self.RR
            nxt = self.LIGA[k + 1] if k + 1 < 9 else self.LIGA[k] + 1
            u = ease(fase(tt, nxt - .6, nxt))
            (ax, ay), (bx, by) = self.p_ic(k), self.p_ic(min(8, k + 1))
            return lerp(ax, bx, u), lerp(ay, by, u) - 22
        rastro(tela, fn, t, n=10, dt=.06)
        x, y = fn(t)
        prota(tela, x, y, 4, t)
        self.painel(tela, t, tudo=True, linhas=[('GOTINHAS NUMA GOTA', '1 MILHÃO', AGC), ('VELOCIDADE DA GOTA', '23 KM/H', CIANO),
                                                ('NO AR, EM MÉDIA', '9 DIAS', CEUD3), ('NO OCEANO, EM MÉDIA', '3.200 ANOS', MAR2)])

    def sons(self, fx):
        for i, a in enumerate(self.LIGA):
            fx.put(tique(880 * 2 ** ((0, 2, 4, 5, 7, 9, 11, 12, 14)[i] / 12), .1), self.t0 + a, .16)
        fx.put(fx.sino(84, 1.2), self.t0 + 20.7, .2)


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
            nuvem_dia(tela, W // 2, 92, 70, True)
            chuva(tela, W // 2 - 40, W // 2 + 40, 104, 190, t, n=16, vel=100)
            fn = lambda tt: (W // 2 + 6, 110 + (tt * 30) % 70)
            rastro(tela, fn, t, n=6, dt=.05)
            prota(tela, *fn(t), 5, t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, oceano=Oceano, subida=Subida, nucleo=Nucleo, colisao=Colisao,
             queda=Queda, floresta=Floresta, rios=Rios, sudeste=Sudeste, mar=Mar, tempo=Tempo,
             resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep23_motor as EP
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
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
