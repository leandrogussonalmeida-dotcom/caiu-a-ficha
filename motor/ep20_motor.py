#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep20 — Como funciona o QR code (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

Protagonista: o código sendo montado, módulo a módulo, com o contador
"MÓDULOS n DE 625" no painel. Nenhum módulo é desenhado à mão: tudo vem do
codificador de `ep20_desenho.py` (versão 2, nível Q, a frase NOSSO MUNDO
PIXEL). Os módulos e os bytes chegam nas batidas da trilha (eventos
'batida' de longo.Trilha), as mesmas que viram som.

    python3 ep20_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep20_motor.py <saida.mp4> bytes mancha     # só esses capítulos (teste)
    python3 ep20_motor.py --folha <saida.png> [ids]    # quadros por capítulo (FR=.3,.8)
"""
import math, os, sys, bisect
import numpy as np
import longo as LG
import ep20_desenho as D                      # registra a paleta 'ep20' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, texto_marcado,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, VERDE, PRETO, ROSA, ROXO, LATAO, CHAMA0, CHAMA1, MISTURA2)
from ep20_desenho import (N, S, CX0, CY0, CARTAO, PAPEL, IDX, ORDEM, FINAL, CRU, MASC, Q, LOC, SEP, SIN, ALI,
                          FMT, ESC, N_DADOS, N_ECC, LETRAS_BITS, TEXTO, rotulo, centro_preso, seta, bloco,
                          celula_bit, grade_fundo, centro_mod, cores_de, cartao, imagem_qr, colar, colar_girado,
                          colar_torto, flash, contorno_mods, milhar, clamp, lerp, suave, ease,
                          PAP0, PAP1, PAP2, PAP3, TIN0, TIN1, TIN2, LOC_E, LOC_C, SIN_E, SIN_C, ALI_E, ALI_C,
                          FMT_E, FMT_C, DAD_E, DAD_C, ECC_E, ECC_C, CAF0, CAF1, CAF2, CAR0, CAR1, CAR2, MAD0, MAD1)
import ritmo_marca as RM
from ep20_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2020, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que fica fora do recorte
PX0 = 306                     # coluna do painel da direita
LX = 208                      # coluna dos rótulos (entre o código e o painel)
SR = LG.SR
INF = 1e9
TOTAL = N * N
NB_DADOS = N_DADOS * 8                     # 176 bits
NB_TODOS = (N_DADOS + N_ECC) * 8           # 352 bits
NB_MOD = len(ORDEM)                        # 359 módulos de dados (com os 7 de sobra)
M_PECA = {k: (PAPEL == k) for k in (LOC, SEP, SIN, ALI, FMT, ESC)}
M_DADO = IDX >= 0
FIXOS_SEM_FMT = int((PAPEL > 0).sum() - M_PECA[FMT].sum())     # 236
CORES_PECA = dict(LOCALIZADOR=LOC_E, SINCRONIA=SIN_E, ALINHAMENTO=ALI_E, FORMATO=FMT_E, DADOS=DAD_E,
                  CORRECAO=ECC_E)
LUZ_PECA = {LOC_E: CIANO, SIN_E: VERDE, ALI_E: ROXO, FMT_E: LARANJA, DAD_E: AMARELO, ECC_E: ROSA}


def anel_loc(x, y):
    """Anel do localizador a que o módulo pertence: 0 borda escura, 1 clara, 2 miolo."""
    ox = 0 if x < 8 else N - 7
    oy = 0 if y < 8 else N - 7
    d = max(abs(x - ox - 3), abs(y - oy - 3))
    return 0 if d == 3 else (1 if d == 2 else 2)


def qual_loc(x, y):
    return 0 if (x < 9 and y < 9) else (1 if x > 15 else 2)


def valor_cru():
    v = CRU.copy()
    v[M_PECA[FMT]] = 0
    return v


def valor_mascara(k, formato=True):
    v = Q['todas'][k].copy()
    if not formato: v[M_PECA[FMT]] = 0
    return v


class Cena:
    legenda = True
    brilho = .3
    XV = CARTAO[0] + 99          # centro do recorte vertical

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.L = trilha.L
        self.bt = [e['t'] - self.t0 for e in self.L.entre('batida', self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]
        if len(self.bt) < 2:
            p = 60.0 / cap['bpm']
            self.bt = [k * p for k in range(int(self.dur / p) + 1)]
        self.ta = np.full((N, N), INF)
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    # ---- batidas
    def nb(self, t): return bisect.bisect_right(self.bt, t + 1e-6)

    def tb(self, k):
        if k < len(self.bt): return self.bt[k]
        p = self.bt[1] - self.bt[0]
        return self.bt[-1] + (k - len(self.bt) + 1) * p

    def desde_batida(self, t):
        k = self.nb(t) - 1
        return t - self.tb(k) if k >= 0 else 9.0

    # ---- moldura
    def fundo(self, tela, t):
        grade_fundo(tela, W, t)
        if not VERTICAL:
            tela.ret(300, 0, 1, PALCO_H, TRACO)
            tela.ret(301, 0, W - 301, PALCO_H, FUNDO)

    def ptxt(self, tela, txt, y, cor=ACO3, tam=9, x=PX0):
        if not VERTICAL: tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)

    def ptit(self, tela, txt, y=6, cor=ACO3):
        if VERTICAL: return
        tela.texto(txt, PX0, y, cor, tam=9, contorno=PRETO)
        tela.ret(PX0, y + 10, 162, 1, FUNDO3)

    def vtxt(self, tela, txt, cor=BRANCO, y=8, tam=9):
        """Leitura curta no topo do recorte vertical (só nos Shorts)."""
        if VERTICAL: centro_preso(tela, txt, self.XV, y, cor, tam=tam, xmin=self.XV - 88, xmax=self.XV + 88)

    def rot(self, tela, *a, **k):
        if not VERTICAL: rotulo(tela, *a, **k)

    def contador(self, tela, n, y=6, t=0.0):
        """O objetivo que sobe: MÓDULOS n DE 625, com barra."""
        self.ptit(tela, "MÓDULOS", y)
        cor = AMARELO if n >= TOTAL else BRANCO
        self.ptxt(tela, f"{milhar(n)} DE 625", y + 14, cor, 17)
        if not VERTICAL:
            tela.ret(PX0, y + 34, 162, 6, PRETO)
            tela.ret(PX0 + 1, y + 35, 160, 4, FUNDO2)
            w = int(160 * n / TOTAL)
            tela.ret(PX0 + 1, y + 35, w, 4, AMARELO if n >= TOTAL else CIANO)
            if w > 2: tela.ret(PX0 + w - 1, y + 35, 2, 4, BRANCO)
        self.vtxt(tela, f"MÓDULOS {n} DE 625", AMARELO if n >= TOTAL else BRANCO)

    # ---- o código
    def codigo(self, tela, t, valor, colorido=True, ta=None, x=None, y=None, extra_vis=None, flash_on=True):
        ta = self.ta if ta is None else ta
        vis = ta <= t
        if extra_vis is not None: vis = vis | extra_vis
        col = np.full((N, N), bool(colorido)) if np.isscalar(colorido) or isinstance(colorido, bool) else colorido
        cores = cores_de(valor, vis, col)
        x = CARTAO[0] if x is None else x
        y = CARTAO[1] if y is None else y
        cartao(tela, cores, x, y)
        if flash_on:
            idade = t - ta
            ys, xs = np.nonzero((idade >= 0) & (idade < .35))
            for yy, xx in zip(ys, xs):
                c = int(D.PAR_E[yy, xx])
                flash(tela, xx, yy, idade[yy, xx], x + 24, y + 24, cor=LUZ_PECA.get(c, AMARELO))
        return int(vis.sum())

    def n_definidos(self, t, ta=None):
        ta = self.ta if ta is None else ta
        return int((ta <= t).sum())

    # ---- sons curtos (seno com decaimento: pico baixo, sem estalo)
    def tique(self, fx, t, f=1500.0, dur=.05, g=.06, pan=0.0):
        n = int(dur * SR); tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4)) * np.minimum(1, tt / .002)
        fx.put(y.astype(np.float32), self.t0 + t, g, pan)

    def nota(self, fx, t, m, dur=.08, g=.05, pan=0.0):
        self.tique(fx, t, 440 * 2 ** ((m - 69) / 12), dur, g, pan)

    def bipe(self, fx, t, m=88, g=.05):
        n = int(.12 * SR); tt = np.arange(n) / SR
        f = 440 * 2 ** ((m - 69) / 12)
        y = np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / .004) * np.minimum(1, (.12 - tt) / .02)
        fx.put(y.astype(np.float32), self.t0 + t, g)

    def pan_mod(self, x): return -.5 + x / N * .6


# ------------------------------------------------------------------ chegada das peças (tempos)
def ta_antes(*pecas, kbits=0, fmt=False):
    """Matriz de chegada com as peças de capítulos anteriores já no lugar."""
    ta = np.full((N, N), INF)
    for p in pecas: ta[M_PECA[p]] = -INF
    if fmt: ta[M_PECA[FMT]] = -INF
    if kbits: ta[M_DADO & (IDX < kbits)] = -INF
    return ta


# ============================================================ 0 gancho
class Gancho(Cena):
    def preparar(self):
        rng = np.random.default_rng(20)
        self.chega = np.zeros((N, N))
        self.ori = np.zeros((N, N, 2))
        ordem = rng.permutation(N * N)
        for k, idx in enumerate(ordem):
            y, x = divmod(int(idx), N)
            self.chega[y, x] = .4 + 4.0 * k / (N * N) + rng.uniform(0, .25)
            a = rng.uniform(0, 2 * math.pi)
            self.ori[y, x] = (103 + math.cos(a) * rng.uniform(150, 260), 104 + math.sin(a) * rng.uniform(120, 200))
        self.ta = self.chega.copy()

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        n = self.codigo(tela, t, FINAL, colorido=False, flash_on=False)
        voo = .9
        ys, xs = np.nonzero((self.chega > t) & (self.chega - voo < t))
        for y, x in zip(ys, xs):
            u = ease(1 - (self.chega[y, x] - t) / voo)
            cx, cy = centro_mod(x, y)
            px = lerp(self.ori[y, x, 0], cx, u) - 3; py = lerp(self.ori[y, x, 1], cy, u) - 3
            if FINAL[y, x]:
                tela.ret(px - 1, py - 1, 8, 8, PRETO); tela.ret(px, py, 6, 6, int(D.PAR_E[y, x]))
                tela.px(px, py, LUZ_PECA.get(int(D.PAR_E[y, x]), BRANCO))
            else:
                tela.ret(px - 1, py - 1, 8, 8, PRETO); tela.ret(px, py, 6, 6, PAP2)
        self.contador(tela, n)
        # a leitura
        if t > 5.2:
            u = (t - 5.2) / 1.6
            if u < 1:
                yl = int(CY0 - 8 + (N * S + 16) * suave(u))
                tela.ret(CX0 - 10, yl, N * S + 20, 1, VERMELHO)
                tela.ret(CX0 - 10, yl - 1, N * S + 20, 1, CHAMA1)
            D.mira(tela, CX0 - 8, CY0 - 8, N * S + 16, N * S + 16, VERDE if t > 6.8 else BRANCO)
        if not VERTICAL:
            self.ptit(tela, "A CÂMERA LÊ:", 64)
            if t > 6.8:
                k = int((t - 6.8) / .07)
                tela.texto(TEXTO[:k], PX0, 80, VERDE, tam=9, contorno=PRETO)
                if t > 8.5:
                    D.celular(tela, 350, 104, 54, 96, t)
                    sx, sy, sw, sh = 353, 112, 48, 80
                    tela.ret(sx, sy, sw, sh, FUNDO)
                    mini = cores_de(FINAL, np.ones((N, N), bool), np.zeros((N, N), bool))
                    colar(tela, imagem_qr(mini, 1, 2, encaixe=False), sx + 9, sy + 6)
                    tela.texto("OK", sx + sw // 2, sy + 52, VERDE, tam=17, centro=True, contorno=PRETO)
        elif t > 6.8:
            self.vtxt(tela, TEXTO, VERDE, y=190)

    def sons(self, fx):
        for k, tb in enumerate(self.bt):
            if .3 < tb < 4.8: self.nota(fx, tb, 72 + [0, 3, 7, 10, 12, 15, 19][k % 7], .07, .04)
        self.tique(fx, 5.2, 900, .3, .025)
        self.bipe(fx, 6.8, 88, .06)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        grade_fundo(tela, W, t)
        # localizadores girando nos cantos (as peças do código)
        for k, (cx, cy) in enumerate(((52, 40), (428, 40), (52, 170))):
            img = imagem_qr(cores_de(np.array([[1] * 7] + [[1, 0, 0, 0, 0, 0, 1]] + [[1, 0, 1, 1, 1, 0, 1]] * 3 +
                                              [[1, 0, 0, 0, 0, 0, 1]] + [[1] * 7]),
                                     np.ones((7, 7), bool), np.full((7, 7), True)), 4, 1, escuros=None)
            colar_girado(tela, img, cx, cy, t * .5 + k, .8 + .05 * math.sin(t * 3 + k))
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA", "O QR CODE")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 13)]
            tela.texto(vis, W // 2 - larg // 2, 66 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("FEITO DE PIXELS", W // 2, 140, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 1.8:
            for k in range(25):
                v = FINAL[12, k]
                x = W // 2 - 75 + k * 6
                if (t - 1.8) * 30 > k:
                    tela.ret(x, 166, 5, 5, TIN0 if v else PAP3)

    def sons(self, fx):
        self.nota(fx, 1.2, 79, .2, .05)


# ============================================================ 2 a grade
class Grade(Cena):
    def preparar(self):
        self.vazio = np.ones((N, N), bool)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        linhas = int(clamp((t - .3) / 5.5) * N + .999) if t > .3 else 0
        vis_slot = np.zeros((N, N), bool); vis_slot[:linhas] = True
        cores = np.full((N, N), -1, np.int16)
        img = imagem_qr(cores, S, encaixe=True)
        # linhas ainda não abertas: papel liso
        o = 24
        img[o + linhas * S:o + N * S, o:o + N * S] = PAP3
        tela.ret(CARTAO[0] - 1, CARTAO[1] - 1, CARTAO[2] + 2, CARTAO[3] + 2, PRETO)
        dither(tela, CARTAO[0] + 4, CARTAO[1] + 4, CARTAO[2], CARTAO[3], FUNDO, PRETO)
        colar(tela, img, CARTAO[0], CARTAO[1])
        # um módulo pisca: escuro / claro
        if 7.4 <= t < 14.6:
            k = self.nb(t)
            v = k % 2
            px, py = CX0 + 12 * S, CY0 + 12 * S
            tela.ret(px, py, S, S, TIN0 if v else PAP3)
            tela.ret_vazado(px - 2, py - 2, S + 4, S + 4, AMARELO)
            self.rot(tela, "1 MÓDULO", LX, 98, px + S + 2, py + 3)
            if not VERTICAL:
                for j, (nome, val) in enumerate((("ESCURO", 1), ("CLARO", 0))):
                    yy = 70 + j * 40
                    aceso = v == val
                    bloco(tela, PX0, yy, PX0 + 30, yy + 30, TIN0 if val else PAP3, TIN1 if val else BRANCO,
                          TIN0 if val else PAP2)
                    if aceso: tela.ret_vazado(PX0 - 3, yy - 3, 37, 37, AMARELO)
                    tela.texto(nome, PX0 + 40, yy + 8, AMARELO if aceso else ACO2, tam=17, contorno=PRETO)
                self.ptxt(tela, "CADA MÓDULO GUARDA 1 BIT", 152, BRANCO)
        # réguas: 25 por 25
        if 14.8 <= t < 22.2:
            u = clamp((t - 14.8) / 4.0)
            k = int(u * N * N)
            for i in range(min(k, N * N)):
                yy, xx = divmod(i, N)
                if (i * 7) % 11 == 0 or i == k - 1:
                    tela.ret(CX0 + xx * S + 2, CY0 + yy * S + 2, 2, 2, CIANO)
            if not VERTICAL:
                tela.ret(CX0, CY0 - 10, N * S, 1, AMARELO)
                tela.ret(CX0, CY0 - 13, 1, 7, AMARELO); tela.ret(CX0 + N * S - 1, CY0 - 13, 1, 7, AMARELO)
                tela.texto("25", CX0 + N * S // 2 - 5, CY0 - 22, AMARELO, tam=9, contorno=PRETO)
                tela.ret(CX0 + N * S + 10, CY0, 1, N * S, AMARELO)
                tela.ret(CX0 + N * S + 7, CY0, 7, 1, AMARELO); tela.ret(CX0 + N * S + 7, CY0 + N * S - 1, 7, 1, AMARELO)
                tela.texto("25", CX0 + N * S + 14, CY0 + N * S // 2 - 3, AMARELO, tam=9, contorno=PRETO)
            self.ptit(tela, "VERSÃO 2", 64)
            self.ptxt(tela, "25 X 25", 80, BRANCO, 17)
            self.ptxt(tela, f"= {milhar(min(k, 625))} MÓDULOS", 102, AMARELO, 17)
            self.ptxt(tela, "A VERSÃO 1 TEM 21 X 21", 130, ACO3)
            self.vtxt(tela, f"25 X 25 = {min(k, 625)}", AMARELO, y=192)
        # a margem
        if t >= 22.2:
            fase = int(t * 6) % 4
            x0, y0, w, h = CARTAO
            for k in range(0, w, 4):
                c = AMARELO if (k // 4 + fase) % 2 else LARANJA
                tela.ret(x0 + k, y0 + 2, 2, 2, c); tela.ret(x0 + k, y0 + h - 4, 2, 2, c)
                tela.ret(x0 + 2, y0 + k, 2, 2, c); tela.ret(x0 + w - 4, y0 + k, 2, 2, c)
            tela.ret_vazado(CX0 - 1, CY0 - 1, N * S + 2, N * S + 2, CIANO)
            u = suave((t - 22.2) / .8)
            tela.ret(x0, y0 + h // 2, int(24 * u), 1, AMARELO)
            if u > .9: tela.texto("4", x0 + 9, y0 + h // 2 - 10, PRETO, tam=9)
            self.rot(tela, "MARGEM", LX, 150, x0 + w - 6, 160)
            self.ptit(tela, "MARGEM", 64)
            self.ptxt(tela, "4 MÓDULOS", 80, BRANCO, 17)
            self.ptxt(tela, "DE PAPEL LIMPO EM VOLTA", 102, ACO3)
            self.vtxt(tela, "MARGEM: 4 MÓDULOS", AMARELO, y=192)
        self.contador(tela, 0)
        if t < 7.4:
            self.ptit(tela, "QR", 64)
            self.ptxt(tela, "QUICK", 80, BRANCO, 17)
            self.ptxt(tela, "RESPONSE", 98, BRANCO, 17)
            if t > 2.5: self.ptxt(tela, "= RESPOSTA RÁPIDA", 124, AMARELO)
            self.ptxt(tela, f"ENCAIXES: {milhar(linhas * N)}", 150, ACO3)

    def sons(self, fx):
        for k in range(N):
            self.nota(fx, .3 + 5.5 * k / N, 67 + (k % 5) * 2, .04, .02)
        for tb in self.bt:
            if 7.4 <= tb < 14.6: self.tique(fx, tb, 1200, .04, .03)
        self.nota(fx, 22.3, 79, .15, .04)


# ============================================================ 3 localizadores
class Localizador(Cena):
    def preparar(self):
        ys, xs = np.nonzero(M_PECA[LOC])
        for y, x in zip(ys, xs):
            k = 1 + qual_loc(x, y) * 3 + anel_loc(x, y)
            cx, cy = (3 if x < 9 else N - 4), (3 if y < 9 else N - 4)
            a = (math.atan2(y - cy, x - cx) + math.pi) / (2 * math.pi)
            self.ta[y, x] = self.tb(k) + a * .12
        ys, xs = np.nonzero(M_PECA[SEP])
        for y, x in zip(ys, xs):
            self.ta[y, x] = self.tb(38 + qual_loc(x, y)) + ((x + y) % 9) * .01
        self.ang_alvos = [0, math.pi / 2, math.pi, 3 * math.pi / 2, 2 * math.pi]

    def angulo(self, t):
        if not (14.8 <= t < 22.6): return 0.0
        u = (t - 14.8) / 7.6 * 4
        k = int(u); f = u - k
        return (k + suave(clamp(f / .55))) * math.pi / 2

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        val = valor_cru()
        a = self.angulo(t)
        if a % (2 * math.pi) != 0 and 14.8 <= t < 22.6:
            vis = self.ta <= t
            cores = cores_de(val, vis, np.ones((N, N), bool))
            img = imagem_qr(cores, S)
            colar_girado(tela, img, CARTAO[0] + 99, CARTAO[1] + 99, a, .78)
        else:
            self.codigo(tela, t, val)
        n = self.n_definidos(t)
        self.contador(tela, n)
        # rótulos dos 3 localizadores
        girando = 14.8 <= t < 22.6
        if t > .6 and not girando:
            if t >= self.tb(1): self.rot(tela, "LOCALIZADOR", LX, 10, CX0 + 21, CY0 - 1, CIANO, cotovelo=(CX0 + 21, 13))
            if t >= self.tb(4): self.rot(tela, "LOCALIZADOR", LX, 44, CX0 + N * S + 1, CY0 + 21, CIANO)
            if t >= self.tb(7): self.rot(tela, "LOCALIZADOR", LX, 186, CX0 + 21, CY0 + N * S + 1, CIANO,
                                         cotovelo=(CX0 + 21, 189))
        # 1:1:3:1:1
        if 7.4 <= t < 14.8:
            cx, cy = CX0 + 3.5 * S, CY0 + 3.5 * S
            ang = (t - 7.4) * .55
            dx, dy = math.cos(ang), math.sin(ang)
            L = 3.5 * S * (1 / max(abs(dx), abs(dy)))
            tela.linha(cx - dx * (L + 6), cy - dy * (L + 6) + 1, cx + dx * (L + 6), cy + dy * (L + 6) + 1, PRETO)
            tela.linha(cx - dx * (L + 6), cy - dy * (L + 6), cx + dx * (L + 6), cy + dy * (L + 6), VERMELHO)
            for s in (-1, 1):
                tela.disco(cx + s * dx * (L + 6), cy + s * dy * (L + 6), 2, VERMELHO)
            if not VERTICAL:
                self.ptit(tela, "A LINHA CRUZA:", 64)
                x = PX0
                partes = ((1, TIN0, "1"), (1, PAP3, "1"), (3, TIN0, "3"), (1, PAP3, "1"), (1, TIN0, "1"))
                u = 22
                for k, (w, cor, rot) in enumerate(partes):
                    vis = (t - 7.6) * 3 > k
                    if not vis: x += w * u; continue
                    bloco(tela, x, 82, x + w * u - 2, 102, cor, BRANCO if cor == PAP3 else TIN2, PAP1 if cor == PAP3 else TIN0)
                    tela.texto(rot, x + (w * u) // 2 - 3, 108, AMARELO, tam=9, contorno=PRETO)
                    x += w * u
                self.ptxt(tela, "ESCURO-CLARO-ESCURO-", 126, ACO3)
                self.ptxt(tela, "CLARO-ESCURO, EM QUALQUER", 136, ACO3)
                self.ptxt(tela, "DIREÇÃO", 146, ACO3)
            self.vtxt(tela, "1 : 1 : 3 : 1 : 1", AMARELO, y=192)
        # o giro
        if girando and not VERTICAL:
            self.ptit(tela, "A CÂMERA VÊ GIRADO...", 64)
            self.ptxt(tela, "...E DESGIRA:", 132, ACO3)
            vis = self.ta <= t
            mini = imagem_qr(cores_de(val, vis, np.ones((N, N), bool)), 2, 2, encaixe=False)
            colar(tela, mini, PX0 + 4, 80 - 0)
            k = int(((t - 14.8) / 7.6 * 4)) % 4
            for j, (nome, a2) in enumerate((("0°", 0), ("90°", 1), ("180°", 2), ("270°", 3))):
                tela.texto(nome, PX0 + 76, 82 + j * 12, AMARELO if j == k else ACO1, tam=9, contorno=PRETO)
            seta(tela, PX0 + 140, 112, PX0 + 140, 82, VERDE)
            tela.texto("TOPO", PX0 + 120, 116, VERDE, tam=9, contorno=PRETO)
            # quem falta: o canto sem localizador
            self.ptxt(tela, "O CANTO SEM QUADRADO", 146, BRANCO)
            self.ptxt(tela, "FICA EMBAIXO, À DIREITA", 156, BRANCO)
        elif girando:
            self.vtxt(tela, "ONDE É O TOPO?", AMARELO, y=192)
        # os separadores e o 8 X 8
        if t >= 22.8:
            for k in range(3):
                if t < self.tb(38 + k): continue
                ox = 0 if k != 1 else N - 8
                oy = 0 if k != 2 else N - 8
                mods = [(x, y) for y in range(oy, oy + 8) for x in range(ox, ox + 8)]
                pulso = int(t * 4) % 2
                contorno_mods(tela, mods, AMARELO if pulso else LARANJA)
            if t >= self.tb(38):
                self.rot(tela, "SEPARADOR", LX, 74, CX0 + 7 * S + 3, CY0 + 4 * S, AMARELO)
            if not VERTICAL:
                self.ptit(tela, "CADA CANTO:", 64)
                self.ptxt(tela, "7 X 7 + FAIXA = 8 X 8", 80, BRANCO, 9)
                self.ptxt(tela, f"3 X 49 = 147 ESCUROS E CLAROS", 96, ACO3)
                self.ptxt(tela, "3 X 15 = 45 DA FAIXA", 108, ACO3)
            self.vtxt(tela, "8 X 8 EM CADA CANTO", AMARELO, y=192)
        if t < 7.4 and not VERTICAL:
            self.ptit(tela, "PEÇA 1: LOCALIZADORES", 64)
            for k in range(3):
                for j in range(3):
                    kk = 1 + k * 3 + j
                    on = t >= self.tb(kk)
                    tela.ret(PX0 + j * 14, 82 + k * 16, 10, 10, CIANO if on else FUNDO2)
                tela.texto(("CANTO DE CIMA, ESQ.", "CANTO DE CIMA, DIR.", "CANTO DE BAIXO, ESQ.")[k],
                           PX0 + 46, 83 + k * 16, BRANCO if t >= self.tb(1 + k * 3) else ACO1, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(1, 10):
            self.nota(fx, self.tb(k), [60, 67, 72][(k - 1) % 3] + 12 * ((k - 1) // 3 == 1) + 5 * ((k - 1) // 3 == 2),
                      .1, .05, (-.4, .4, -.4)[(k - 1) // 3])
        for k in range(38, 41): self.nota(fx, self.tb(k), 76, .06, .035)
        for k in range(4):
            self.tique(fx, 14.8 + k * 1.9, 700, .12, .025)


# ============================================================ 4 sincronia e alinhamento
class Sincronia(Cena):
    def preparar(self):
        self.ta = ta_antes(LOC, SEP)
        for i in range(8, N - 8):
            k = 1 + (i - 8)
            self.ta[6, i] = self.tb(k)
            self.ta[i, 6] = self.tb(k) + .05
        ys, xs = np.nonzero(M_PECA[ALI])
        for y, x in zip(ys, xs):
            d = max(abs(x - 18), abs(y - 18))
            self.ta[y, x] = self.tb(21 + (2 - d))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        val = valor_cru()
        torto = 18.0 <= t < 23.6
        if torto:
            amp = math.sin(clamp((t - 18.0) / 5.6) * math.pi)
            vis = self.ta <= t
            img = imagem_qr(cores_de(val, vis, np.ones((N, N), bool)), S)
            tela.ret(CARTAO[0] - 8, CARTAO[1] - 4, CARTAO[2] + 16, CARTAO[3] + 8, FUNDO)
            sx, sy = colar_torto(tela, img, CARTAO[0], CARTAO[1], amp, t)
            # onde foi parar o alinhamento e os localizadores
            alvos = [(24 + 18.5 * S, 24 + 18.5 * S, ROXO), (24 + 3.5 * S, 24 + 3.5 * S, CIANO),
                     (24 + 21.5 * S, 24 + 3.5 * S, CIANO), (24 + 3.5 * S, 24 + 21.5 * S, CIANO)]
            x0, y0 = max(0, CARTAO[0] - 10), max(0, CARTAO[1] - 10)
            for ax, ay, cor in alvos:
                d = (sx - ax) ** 2 + (sy - ay) ** 2
                j = np.unravel_index(np.argmin(d), d.shape)
                px, py = x0 + j[1], y0 + j[0]
                tela.anel(px, py, 9 + 2 * math.sin(t * 8), PRETO, 2)
                tela.anel(px, py, 8 + 2 * math.sin(t * 8), cor, 1)
            self.ptit(tela, "IMAGEM TORTA", 64)
            self.ptxt(tela, "OS 3 LOCALIZADORES E O", 80, BRANCO)
            self.ptxt(tela, "ALINHAMENTO SÃO PONTOS", 90, BRANCO)
            self.ptxt(tela, "DE REFERÊNCIA PARA", 100, BRANCO)
            self.ptxt(tela, "DESENTORTAR A GRADE", 110, BRANCO)
            self.vtxt(tela, "IMAGEM TORTA? ELE AJUDA", AMARELO, y=192)
        else:
            self.codigo(tela, t, val)
        self.contador(tela, self.n_definidos(t))
        if t > .8 and t < 15.2 and not torto:
            self.rot(tela, "SINCRONIA", LX, 30, CX0 + 15 * S, CY0 + 6 * S + 3, VERDE, cotovelo=(CX0 + 15 * S, CY0 + 3 * S + 4))
            self.rot(tela, "SINCRONIA", LX, 120, CX0 + 6 * S + 3, CY0 + 15 * S, VERDE, cotovelo=(CX0 + 6 * S + 3, CY0 + 13 * S))
        if t < 7.8 and not VERTICAL:
            self.ptit(tela, "PEÇA 2: SINCRONIA", 64)
            k = min(9, max(0, self.nb(t) - 1))
            for i in range(9):
                v = 1 - i % 2
                on = i < k
                tela.ret(PX0 + i * 16, 82, 14, 14, PRETO)
                tela.ret(PX0 + i * 16 + 1, 83, 12, 12, (SIN_E if v else SIN_C) if on else FUNDO2)
            self.ptxt(tela, "ESCURO, CLARO, ESCURO...", 104, ACO3)
            self.ptxt(tela, "NA LINHA 6 E NA COLUNA 6", 114, ACO3)
        # a régua: varre colunas e linhas
        if 7.8 <= t < 15.2:
            u = (t - 7.8) / 7.4
            col = int(u * 2 * N) % N if u < .5 else 6
            lin = 6 if u < .5 else int((u - .5) * 2 * N) % N
            if u < .5:
                tela.ret_vazado(CX0 + col * S - 1, CY0 - 1, S + 2, N * S + 2, AMARELO)
                tela.ret_vazado(CX0 + col * S - 1, CY0 + 6 * S - 1, S + 2, S + 2, BRANCO)
            else:
                tela.ret_vazado(CX0 - 1, CY0 + lin * S - 1, N * S + 2, S + 2, AMARELO)
                tela.ret_vazado(CX0 + 6 * S - 1, CY0 + lin * S - 1, S + 2, S + 2, BRANCO)
            self.ptit(tela, "A RÉGUA", 64)
            self.ptxt(tela, f"COLUNA {col}" if u < .5 else "COLUNA 6", 80, BRANCO, 17)
            self.ptxt(tela, f"LINHA {lin}", 100, BRANCO, 17)
            self.ptxt(tela, "CONTANDO OS MÓDULOS DA", 124, ACO3)
            self.ptxt(tela, "SINCRONIA, A CÂMERA SABE", 134, ACO3)
            self.ptxt(tela, "ONDE ESTÁ CADA UM", 144, ACO3)
            self.vtxt(tela, f"COLUNA {col}  LINHA {lin}", AMARELO, y=192)
        if 15.2 <= t < 18.0:
            if t >= self.tb(21): self.rot(tela, "ALINHAMENTO", LX, 140, CX0 + 20.5 * S + 1, CY0 + 18.5 * S, ROXO)
            self.ptit(tela, "PEÇA 3: ALINHAMENTO", 64)
            self.ptxt(tela, "5 X 5 = 25 MÓDULOS", 80, BRANCO)
            self.ptxt(tela, "A VERSÃO 1 NÃO TEM;", 96, ACO3)
            self.ptxt(tela, "A 2 TEM 1", 106, ACO3)

    def sons(self, fx):
        for k in range(1, 10): self.nota(fx, self.tb(k), 72 + (k % 2) * 7, .06, .045, -.2 + .05 * k)
        for k in range(21, 24): self.nota(fx, self.tb(k), [65, 69, 72][k - 21], .12, .05)
        for k in range(int(7.4 / .3)):
            self.tique(fx, 7.8 + k * .3, 2400, .02, .012)


# ============================================================ 5 formato
class Formato(Cena):
    def preparar(self):
        self.ta = ta_antes(LOC, SEP, SIN, ALI)
        a, b = D.posicoes_formato()
        for i, (x, y) in enumerate(a): self.ta[y, x] = self.tb(1 + i // 5) + (i % 5) * .06
        for i, (x, y) in enumerate(b): self.ta[y, x] = self.tb(5 + i // 5) + (i % 5) * .06
        self.ta[N - 8, 8] = self.tb(9)
        self.a, self.b = a, b

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        val = valor_cru()
        self.codigo(tela, t, val)
        # formato "em branco": um pontinho no meio de cada módulo
        for (x, y) in self.a + self.b:
            if self.ta[y, x] <= t:
                cx, cy = centro_mod(x, y)
                if int(t * 3 + x + y) % 3: tela.ret(cx - 1, cy - 1, 2, 2, FMT_E)
        n = self.n_definidos(t) - int(((self.ta <= t) & M_PECA[FMT]).sum())
        self.contador(tela, n)
        if t >= self.tb(1):
            self.rot(tela, "FORMATO", LX, 86, CX0 + 8 * S + 1, CY0 + 8 * S + 3, LARANJA, cotovelo=(CX0 + 12 * S, CY0 + 9 * S - 1))
        if t >= self.tb(5):
            self.rot(tela, "CÓPIA 2", LX, 60, CX0 + 20 * S, CY0 + 8 * S + 3, LARANJA, cotovelo=(CX0 + 20 * S, CY0 + 6 * S))
            self.rot(tela, "CÓPIA 2", LX, 170, CX0 + 9 * S, CY0 + 21 * S, LARANJA)
        # leitura dos 15 bits, em ordem
        if t >= 15.8:
            i = int((t - 15.8) / .35) % 15
            for cop in (self.a, self.b):
                x, y = cop[i]
                tela.ret_vazado(CX0 + x * S - 2, CY0 + y * S - 2, S + 4, S + 4, BRANCO)
        if not VERTICAL:
            self.ptit(tela, "PEÇA 4: FORMATO (15 BITS)", 64)
            for k in range(15):
                x = PX0 + k * 11 - (0 if k < 2 else -3) + (3 if k >= 5 else 0)
                if k < 2:
                    v = (D.EC_BITS >> (1 - k)) & 1
                    if t >= 7.8: celula_bit(tela, x, 82, v, 8, 11, cor1=LARANJA)
                    else: self._interroga(tela, x, 82)
                else:
                    self._interroga(tela, x, 82)
            tela.texto("NÍVEL", PX0, 98, LARANJA if t >= 7.8 else ACO2, tam=9, contorno=PRETO)
            tela.texto("MÁSCARA", PX0 + 25, 108, ACO2, tam=9, contorno=PRETO)
            tela.texto("PROTEÇÃO", PX0 + 64, 98, ACO2, tam=9, contorno=PRETO)
            if t >= 7.8:
                self.ptxt(tela, "NÍVEL Q = 11", 124, BRANCO, 17)
                self.ptxt(tela, "MÁSCARA: AINDA NÃO", 146, ACO3)
                self.ptxt(tela, "SABEMOS (VEM NO FIM)", 156, ACO3)
            if t >= 15.8:
                self.ptxt(tela, "A CÂMERA LÊ ISTO PRIMEIRO", 176, AMARELO)
        self.vtxt(tela, "FORMATO: 15 BITS X 2", LARANJA, y=192)

    def _interroga(self, tela, x, y, v=None):
        tela.ret(x - 1, y - 1, 10, 13, PRETO)
        tela.ret(x, y, 8, 11, FUNDO2)
        tela.texto("?", x + 2, y + 2, ACO2, tam=9)

    def sons(self, fx):
        for k in range(1, 10): self.nota(fx, self.tb(k), 74 + (k % 3) * 3, .06, .04, -.3 if k < 5 else .3)
        for k in range(int(7.8 / .35)): self.tique(fx, 15.8 + k * .35, 1800, .03, .015)


# ============================================================ 6 a frase vira bits
class Texto(Cena):
    def preparar(self):
        self.cods = list(TEXTO.encode('latin-1'))
        # N devagar (uma casa por batida), as outras letras rápidas
        self.t_N = 7.8
        self.t_resto = 15.2

    def letra_ativa(self, t):
        if t < self.t_N: return -1
        if t < self.t_resto: return 0
        return min(16, 1 + int((t - self.t_resto) / .4))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        n_tipo = int(clamp((t - .5) / 3.0) * 17 + .999) if t > .5 else 0
        k_at = self.letra_ativa(t)
        x0 = 12
        for i, ch in enumerate(TEXTO):
            if i >= n_tipo: break
            x = x0 + i * 16
            ativo = i == k_at
            feito = i < k_at or (k_at == 16 and t > self.t_resto + 16 * .4 + .4)
            dy = -4 if ativo else 0
            bloco(tela, x, 14 + dy, x + 14, 32 + dy, PAP3 if not ativo else AMARELO, BRANCO, PAP1 if not ativo else LARANJA)
            if ch != ' ': tela.texto(ch, x + 2, 18 + dy, TIN0, tam=9)
            else: tela.ret(x + 4, 27 + dy, 6, 1, PAP0)
            if feito: tela.ret(x + 3, 35, 8, 2, VERDE)
        if k_at >= 0:
            ch = TEXTO[k_at]; c = self.cods[k_at]
            tela.texto("'" + (ch if ch != ' ' else 'ESPAÇO') + "'", 20, 52, AMARELO, tam=17, contorno=PRETO)
            tela.texto(f"= {c}", 20 + tela.largura_texto("'" + (ch if ch != ' ' else 'ESPAÇO') + "'", 17) + 8, 52,
                       BRANCO, tam=17, contorno=PRETO)
            nbits = 8
            if k_at == 0: nbits = min(8, max(0, self.nb(t) - self.nb(self.t_N - .01)))
            for b in range(8):
                v = (c >> (7 - b)) & 1
                x = 20 + b * 32
                if b < nbits:
                    celula_bit(tela, x, 80, v, 26, 30, pulso=1.0 if (k_at == 0 and b == nbits - 1 and self.desde_batida(t) < .2) else 0)
                else:
                    tela.ret(x - 1, 79, 28, 32, PRETO); tela.ret(x, 80, 26, 30, FUNDO2)
                tela.texto(str(2 ** (7 - b)), x + 13 - tela.largura_texto(str(2 ** (7 - b)), 9) // 2, 114, ACO2, tam=9, contorno=PRETO)
            if k_at == 0 and nbits == 8:
                tela.texto("64 + 8 + 4 + 2 = 78", 20, 128, CIANO, tam=9, contorno=PRETO)
        # a fita de bits: modo + tamanho + letras
        if t >= 22.6:
            bits = Q['bits']
            nfita = int(clamp((t - 22.6) / 5.0) * 148)
            for i in range(min(nfita, 148)):
                b, r = bits[i]
                col, lin = i % 37, i // 37
                x, y = 2 + col * 8, 144 + lin * 9
                cor = CIANO if r[0] == 'modo' else (VERDE if r[0] == 'conta' else AMARELO)
                tela.ret(x, y, 7, 8, PRETO)
                tela.ret(x + 1, y + 1, 5, 6, cor if b else FUNDO3)
            tela.texto("MODO 0100", 2, 132, CIANO, tam=9, contorno=PRETO)
            tela.texto("TAMANHO 00010001 = 17", 70, 132, VERDE, tam=9, contorno=PRETO)
            tela.texto("LETRAS...", 206, 132, AMARELO, tam=9, contorno=PRETO)
        # painel: a tabela que se forma
        if not VERTICAL:
            self.ptit(tela, "LETRA   NÚMERO   BITS", 4)
            ult = -1 if k_at < 0 else (k_at if k_at > 0 else (0 if self.nb(t) - self.nb(self.t_N - .01) >= 8 else -1))
            for i in range(ult + 1):
                c = self.cods[i]; y = 18 + i * 10
                cor = AMARELO if i == k_at else BRANCO
                tela.texto(TEXTO[i] if TEXTO[i] != ' ' else '_', PX0 + 4, y, cor, tam=9, contorno=PRETO)
                tela.texto(str(c), PX0 + 46, y, cor, tam=9, contorno=PRETO)
                tela.texto(format(c, '08b'), PX0 + 96, y, cor, tam=9, contorno=PRETO)
        self.vtxt(tela, "1 LETRA = 8 BITS", AMARELO, y=192)

    def sons(self, fx):
        for k in range(17): self.tique(fx, .5 + 3.0 * k / 17, 2600, .02, .02)
        for tb in self.bt:
            if self.t_N <= tb < self.t_N + 6.1: self.nota(fx, tb, 76, .06, .04)
        for k in range(16): self.nota(fx, self.t_resto + .4 + k * .4, 72 + (k % 4) * 2, .05, .03)
        for k in range(30): self.tique(fx, 22.6 + k * 5.0 / 30, 3000, .015, .012)


# ============================================================ 7 os bits em zigue-zague
class Bytes(Cena):
    T_LETRA = 7.0
    def preparar(self):
        self.ta = ta_antes(LOC, SEP, SIN, ALI, ESC, fmt=True)
        self.tbit = np.full(NB_MOD, INF)
        bits = Q['bits']
        for i in range(NB_DADOS):
            r = bits[i][1]
            if r[0] in ('modo', 'conta'):
                tt = self.tb(2 + i)
            elif r[0] == 'letra':
                k = r[1]; j = (i - 12) % 8
                tt = self.tb(14 + 2 * k) + j * .045
            else:
                j = i - (12 + 136)
                tt = self.tb(48) + j * .06
            self.tbit[i] = tt
            x, y = ORDEM[i]
            self.ta[y, x] = tt
        self.rep0, self.rep1 = 26.0, 39.6

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        val = valor_cru()
        self.codigo(tela, t, val)
        # rastro do caminho
        k = int(np.searchsorted(np.sort(self.tbit[:NB_DADOS]), t, side='right'))
        pts = [centro_mod(*ORDEM[i]) for i in range(k)]
        if t < self.rep0:
            for (a, b), (c, d) in zip(pts[max(0, k - 40):], pts[max(0, k - 40) + 1:]):
                tela.linha(a, b, c, d, AMARELO)
            if k:
                hx, hy = pts[-1]
                tela.anel(hx, hy, 4 + math.sin(t * 10), BRANCO)
        # replay: a cabeça corre o caminho e a letra acende
        letra = None
        if t >= self.rep0:
            u = clamp((t - self.rep0) / (self.rep1 - self.rep0 - .6))
            h = int(u * (NB_DADOS - 1))
            for i in range(max(0, h - 14), h):
                (a, b), (c, d) = centro_mod(*ORDEM[i]), centro_mod(*ORDEM[i + 1])
                tela.linha(a, b, c, d, BRANCO if i > h - 5 else AMARELO)
            r = Q['bits'][h][1]
            if r[0] == 'letra':
                letra = r[1]
                contorno_mods(tela, LETRAS_BITS[letra], BRANCO)
            hx, hy = centro_mod(*ORDEM[h])
            tela.disco(hx, hy, 3, BRANCO)
        n = self.n_definidos(t) - int(M_PECA[FMT].sum())
        self.contador(tela, n)
        if t < 7.4:
            self.rot(tela, "COMEÇA AQUI", LX, 172, CX0 + N * S - 3, CY0 + N * S - 3, AMARELO)
            if t > 2:
                sub = (self.nb(t) // 2) % 2
                seta(tela, CX0 + N * S + 10, CY0 + N * S - 6, CX0 + N * S + 10, CY0 + N * S - 40, AMARELO)
        # painel: o byte da vez
        i_at = max(0, min(NB_DADOS - 1, k - 1)) if t < self.rep0 else None
        if not VERTICAL:
            if t < self.rep0 and k > 0:
                r = Q['bits'][i_at][1]
                nome = {'modo': 'MODO (BYTE)', 'conta': 'TAMANHO', 'fim': 'FIM', 'enche': 'ENCHIMENTO'}.get(r[0])
                if r[0] == 'letra':
                    ch = TEXTO[r[1]]
                    self.ptit(tela, f"LETRA {r[1] + 1} DE 17", 64)
                    tela.texto(ch if ch != ' ' else '_', PX0, 80, AMARELO, tam=26, contorno=PRETO)
                    ini = 12 + r[1] * 8
                    bb = [Q['bits'][ini + j][0] for j in range(8)]
                else:
                    self.ptit(tela, nome, 64)
                    if r[0] == 'modo': ini, nn = 0, 4
                    elif r[0] == 'conta': ini, nn = 4, 8
                    else: ini, nn = 148, 28
                    bb = [Q['bits'][ini + j][0] for j in range(min(8, nn))] if r[0] != 'enche' and r[0] != 'fim' else []
                    if r[0] in ('enche', 'fim'):
                        self.ptxt(tela, "0000 + 11101100", 82, BRANCO)
                        self.ptxt(tela, "00010001 11101100", 94, BRANCO)
                for j, v in enumerate(bb):
                    on = (ini + j) < k
                    x = PX0 + 30 + j * 16
                    if on: celula_bit(tela, x, 84, v, 13, 16)
                    else: tela.ret(x - 1, 83, 15, 18, PRETO); tela.ret(x, 84, 13, 16, FUNDO2)
                byte_n = min(22, (k + 7) // 8)
                self.ptxt(tela, f"BYTE {byte_n} DE 22", 112, BRANCO, 17)
                self.ptxt(tela, f"BIT {k} DE 176", 132, ACO3)
            elif letra is not None:
                self.ptit(tela, "ONDE FICOU CADA LETRA", 64)
                ch = TEXTO[letra]
                tela.texto(ch if ch != ' ' else '_', PX0, 80, BRANCO, tam=26, contorno=PRETO)
                self.ptxt(tela, f"LETRA {letra + 1} DE 17", 84, AMARELO, 17, x=PX0 + 30)
                texto_marcado(tela, ''.join(('*' + c + '*') if j == letra else c for j, c in enumerate(TEXTO)).replace('**', ''),
                              PX0, 118, 9)
            elif t >= self.rep0:
                self.ptit(tela, "ONDE FICOU CADA LETRA", 64)
                self.ptxt(tela, "MODO E TAMANHO", 84, CIANO, 17)
            self.ptxt(tela, "AMARELO: DADOS", 160, AMARELO)
            self.ptxt(tela, "22 BYTES = 176 BITS", 170, ACO3)
        if t < self.rep0 and k > 0:
            r = Q['bits'][max(0, k - 1)][1]
            self.vtxt(tela, f"LETRA {TEXTO[r[1]]}" if r[0] == 'letra' and TEXTO[r[1]] != ' ' else
                      ("ESPAÇO" if r[0] == 'letra' else {'modo': 'MODO', 'conta': 'TAMANHO'}.get(r[0], 'ENCHIMENTO')),
                      AMARELO, y=192)

    def sons(self, fx):
        for i in range(12): self.nota(fx, self.tbit[i], 79 if Q['bits'][i][0] else 72, .05, .04)
        for k in range(17):
            self.nota(fx, self.tb(14 + 2 * k), 72 + [0, 2, 4, 7, 9][k % 5], .08, .045, self.pan_mod(ORDEM[12 + 8 * k][0]))
        self.nota(fx, self.tb(48), 67, .1, .04)


# ============================================================ 8 correção de erro
class Correcao(Cena):
    def preparar(self):
        self.ta = ta_antes(LOC, SEP, SIN, ALI, ESC, fmt=True, kbits=NB_DADOS)
        for i in range(NB_DADOS, NB_MOD):
            j = i - NB_DADOS
            if i < NB_TODOS: tt = self.tb(1 + j // 8) + (j % 8) * .035
            else: tt = 14.4 + (i - NB_TODOS) * .05
            x, y = ORDEM[i]; self.ta[y, x] = tt
        rng = np.random.default_rng(5)
        self.sumir = sorted(int(b) for b in rng.choice(N_DADOS, 3, replace=False))
        self.nivel_t = [23.0 + k * 1.2 for k in range(4)]
        ordem = list(range(NB_TODOS)); rng.shuffle(ordem)
        self.rank = np.full((N, N), 9999)
        for r, i in enumerate(ordem):
            x, y = ORDEM[i]; self.rank[y, x] = r

    def nivel(self, t):
        if t < 23.0: return None
        if t >= 31.4: return 2
        return min(3, int((t - 23.0) / 2.0))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        val = valor_cru()
        self.codigo(tela, t, val)
        # bytes que somem e voltam
        if 15.2 <= t < 22.6:
            fase = (t - 15.2) / 7.4
            for b in self.sumir:
                mods = [ORDEM[b * 8 + j] for j in range(8)]
                if fase < .55:
                    for (x, y) in mods:
                        px, py = CX0 + x * S, CY0 + y * S
                        tela.ret(px, py, S, S, PAP2)
                        if int(t * 4) % 2: tela.px(px + 2, py + 2, VERMELHO); tela.px(px + 3, py + 3, VERMELHO)
                    contorno_mods(tela, mods, VERMELHO)
                else:
                    contorno_mods(tela, mods, VERDE if int(t * 6) % 2 else BRANCO)
        # nível: área que pode se perder
        nv = self.nivel(t)
        if nv is not None:
            pct = (7, 15, 25, 30)[nv]
            lim = int(NB_TODOS * pct / 100)
            ys, xs = np.nonzero(self.rank < lim)
            for y, x in zip(ys, xs):
                px, py = CX0 + x * S, CY0 + y * S
                for k in range(0, S, 2):
                    tela.px(px + k, py + (k + int(t * 4)) % S, VERMELHO)
                    tela.px(px + (k + 3) % S, py + k, VERMELHO)
        n = self.n_definidos(t) - int(M_PECA[FMT].sum())
        self.contador(tela, n)
        if t >= self.tb(1) and t < 15.2:
            self.rot(tela, "CORREÇÃO", LX, 100, CX0 + 10 * S, CY0 + 12 * S, ROSA, cotovelo=(CX0 + 12 * S, CY0 + 13 * S - 2))
        if t >= 14.4 and t < 15.2:
            self.rot(tela, "SOBRA: 7", LX, 150, CX0 + 9 * S, CY0 + 22 * S, ACO3)
        if not VERTICAL:
            if t < 23.0:
                self.ptit(tela, "REED-SOLOMON", 64)
                ne = max(0, min(22, self.nb(t) - 1)) if t >= self.tb(1) else 0
                for j in range(22):
                    x = PX0 + (j % 11) * 15; y = 80 + (j // 11) * 12
                    tela.ret(x, y, 13, 10, PRETO); tela.ret(x + 1, y + 1, 11, 8, DAD_E)
                    tela.ret(x + 1, y + 1, 11, 1, AMARELO)
                    if 15.2 <= t < 22.6 and j in self.sumir:
                        f = (t - 15.2) / 7.4
                        tela.ret(x + 1, y + 1, 11, 8, VERMELHO if f < .55 else VERDE)
                tela.texto("22 DE DADOS", PX0, 104, AMARELO, tam=9, contorno=PRETO)
                seta(tela, PX0 + 80, 108, PX0 + 80, 120, ROSA)
                for j in range(22):
                    x = PX0 + (j % 11) * 15; y = 124 + (j // 11) * 12
                    tela.ret(x, y, 13, 10, PRETO)
                    tela.ret(x + 1, y + 1, 11, 8, ECC_E if j < ne else FUNDO2)
                    if j < ne: tela.ret(x + 1, y + 1, 11, 1, ROSA)
                    if j == ne - 1: tela.ret_vazado(x - 1, y - 1, 15, 12, BRANCO)
                tela.texto(f"{ne} DE 22 DE CORREÇÃO", PX0, 148, ROSA, tam=9, contorno=PRETO)
                if ne:
                    tela.texto(f"BYTE {ne}: {Q['ecc'][ne - 1]}", PX0, 160, ACO3, tam=9, contorno=PRETO)
                if 15.2 <= t < 22.6:
                    f = (t - 15.2) / 7.4
                    tela.texto("3 BYTES SUMIRAM..." if f < .55 else "...E FORAM REFEITOS!", PX0, 176,
                               VERMELHO if f < .55 else VERDE, tam=9, contorno=PRETO)
            elif t < 31.4:
                self.ptit(tela, "QUANTO PODE SE PERDER", 64)
                self._barras(tela, t, nv)
            else:
                self.ptit(tela, "NA VERSÃO 2 CABEM:", 64)
                for j, (nome, cap) in enumerate((("L", 32), ("M", 26), ("Q", 20), ("H", 14))):
                    y = 80 + j * 18
                    cor = AMARELO if nome == 'Q' else ACO2
                    tela.texto(nome, PX0, y, cor, tam=17, contorno=PRETO)
                    w = int(cap * 3.2 * clamp((t - 31.4 - j * .3) / .6))
                    bloco(tela, PX0 + 16, y + 2, PX0 + 16 + max(1, w), y + 12, DAD_E if nome == 'Q' else ACO0,
                          AMARELO if nome == 'Q' else ACO2, TIN0)
                    tela.texto(f"{cap} LETRAS", PX0 + 22 + w, y + 3, cor, tam=9, contorno=PRETO)
                tela.ret(PX0 + 16 + int(17 * 3.2), 76, 1, 74, BRANCO)
                tela.texto("NOSSAS 17", PX0 + 16 + int(17 * 3.2) - 22, 152, BRANCO, tam=9, contorno=PRETO)
        if nv is not None:
            self.vtxt(tela, f"NÍVEL {'LMQH'[nv]}: {(7, 15, 25, 30)[nv]}%", AMARELO, y=192)
        elif t < 15.2:
            self.vtxt(tela, "BYTES DE CORREÇÃO", ROSA, y=192)

    def _barras(self, tela, t, nv):
        for j, (nome, pct) in enumerate((("L", 7), ("M", 15), ("Q", 25), ("H", 30))):
            if t < self.nivel_t[j] - .6: continue
            x = PX0 + 6 + j * 40
            h = int(pct * 3.2 * clamp((t - self.nivel_t[j] + .6) / .5))
            cor = AMARELO if j == nv else ACO1
            bloco(tela, x, 172 - h, x + 24, 172, VERMELHO if j == nv else ACO0, cor, TIN0)
            tela.texto(nome, x + 8, 176, cor, tam=9, contorno=PRETO)
            tela.texto(f"{pct}%", x + 12 - tela.largura_texto(f"{pct}%", 9) // 2, 160 - h, cor, tam=9, contorno=PRETO)

    def sons(self, fx):
        for j in range(22): self.nota(fx, self.tb(1 + j), 64 + [0, 3, 5, 7, 10][j % 5] + 12 * (j // 11), .07, .04)
        for k in range(4): self.nota(fx, self.nivel_t[k] - .6, 60 + k * 4, .12, .04)
        self.nota(fx, 15.2 + 7.4 * .55, 84, .2, .05)


# ============================================================ 9 a máscara
class Mascara(Cena):
    def preparar(self):
        self.ta = ta_antes(LOC, SEP, SIN, ALI, ESC, fmt=True, kbits=NB_MOD)
        self.ciclo0 = 15.2
        a, b = D.posicoes_formato()
        self.fmt_t = {}
        for i, (x, y) in enumerate(a): self.fmt_t[(x, y)] = self.tb(62 + i // 3) + (i % 3) * .1
        for i, (x, y) in enumerate(b): self.fmt_t[(x, y)] = self.tb(62 + i // 3) + (i % 3) * .1 + .05
        self.t_tinta = self.tb(70)
        # problemas do código sem máscara: fileiras de 5+ e blocos 2x2 de dados
        v = valor_cru()
        self.prob = set()
        for y in range(N):
            run = 1
            for x in range(1, N + 1):
                if x < N and v[y, x] == v[y, x - 1] and M_DADO[y, x] and M_DADO[y, x - 1]: run += 1
                else:
                    if run >= 5: self.prob |= {(xx, y) for xx in range(x - run, x)}
                    run = 1
        for y in range(N - 1):
            for x in range(N - 1):
                q = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                if all(M_DADO[b2, a2] for a2, b2 in q) and len({int(v[b2, a2]) for a2, b2 in q}) == 1:
                    self.prob |= set(q)
        self.notas = [n[0] for n in Q['notas']]

    def mascara_em(self, t):
        if t < self.ciclo0: return None
        if t < self.ciclo0 + 8.0: return int((t - self.ciclo0) / 1.0)
        return MASC

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        mk = self.mascara_em(t)
        fmt_escrito = np.zeros((N, N), bool)
        for (x, y), tt in self.fmt_t.items():
            if t >= tt: fmt_escrito[y, x] = True
        if mk is None:
            val = valor_cru()
            if 7.8 <= t < 15.2:
                # varredura da máscara 0: inverte coluna a coluna
                u = clamp((t - 9.4) / 4.0)
                corte = int(u * (N + 1))
                m0 = valor_mascara(0, formato=False)
                val = val.copy()
                val[:, :corte] = m0[:, :corte]
        else:
            val = valor_mascara(mk, formato=False)
            if mk == MASC:
                val = np.where(fmt_escrito, FINAL, val)
        tinta = clamp((t - self.t_tinta) / 2.0)
        col = np.ones((N, N), bool)
        if tinta > 0:
            ordem = (np.arange(N)[None, :] + np.arange(N)[:, None]) / (2 * N - 2)
            col = ordem >= tinta
        self.codigo(tela, t, val, colorido=col)
        # problemas piscando
        if t < 7.8 and int(t * 3) % 2 == 0:
            for (x, y) in self.prob:
                px, py = CX0 + x * S, CY0 + y * S
                tela.ret_vazado(px, py, S, S, VERMELHO)
        # o desenho da máscara por cima
        if 7.8 <= t < 15.2:
            u = clamp((t - 9.4) / 4.0); corte = int(u * (N + 1))
            for (x, y) in ORDEM:
                if D.MASCARAS[0](x, y) and x >= corte:
                    cx, cy = centro_mod(x, y)
                    tela.ret(cx - 1, cy - 1, 2, 2, CIANO)
            if t >= 9.4:
                xx = CX0 + min(corte, N) * S
                tela.ret(xx - 1, CY0 - 6, 2, N * S + 12, BRANCO)
        if mk is not None and t < self.ciclo0 + 8.0:
            for (x, y) in ORDEM:
                if D.MASCARAS[mk](x, y) and (x * 7 + y * 3) % 4 == 0:
                    cx, cy = centro_mod(x, y)
                    tela.px(cx, cy, CIANO)
        n = self.n_definidos(t) - int(M_PECA[FMT].sum()) + int(fmt_escrito.sum())
        self.contador(tela, n)
        if not VERTICAL:
            if t < 7.8:
                self.ptit(tela, "SEM MÁSCARA", 64)
                self.ptxt(tela, "BLOCOS E FILEIRAS", 80, VERMELHO, 17)
                self.ptxt(tela, "DO MESMO TOM", 98, VERMELHO, 17)
                self.ptxt(tela, "PODEM CONFUNDIR A CÂMERA", 124, ACO3)
                self.ptxt(tela, "(E ATÉ PARECER UM", 134, ACO3)
                self.ptxt(tela, "LOCALIZADOR)", 144, ACO3)
            elif t < self.ciclo0:
                self.ptit(tela, "MÁSCARA 0", 64)
                self._icone(tela, 0, PX0, 80, 4)
                self.ptxt(tela, "ONDE A MÁSCARA MARCA,", 80, BRANCO, x=PX0 + 52)
                self.ptxt(tela, "O MÓDULO INVERTE:", 90, BRANCO, x=PX0 + 52)
                tela.ret(PX0 + 52, 104, 10, 10, TIN0); seta(tela, PX0 + 66, 109, PX0 + 84, 109, CIANO, 1, 3)
                tela.ret(PX0 + 88, 104, 10, 10, PAP3)
                tela.ret(PX0 + 108, 104, 10, 10, PAP3); seta(tela, PX0 + 122, 109, PX0 + 140, 109, CIANO, 1, 3)
                tela.ret(PX0 + 144, 104, 10, 10, TIN0)
                self.ptxt(tela, "SÓ NOS DADOS. AS PEÇAS", 132, ACO3)
                self.ptxt(tela, "FIXAS NÃO MUDAM.", 142, ACO3)
            else:
                self.ptit(tela, "PONTOS DE CASTIGO", 64)
                testadas = 8 if t >= self.ciclo0 + 8.0 else int(t - self.ciclo0) + 1
                mx = max(self.notas)
                for k in range(8):
                    x = PX0 + 2 + k * 20
                    if k >= testadas:
                        tela.texto(str(k), x + 5, 176, ACO1, tam=9, contorno=PRETO)
                        continue
                    f = clamp((t - self.ciclo0 - k) / .5) if t < self.ciclo0 + 8.0 else 1.0
                    h = int(self.notas[k] / mx * 70 * f)
                    vence = k == MASC and t >= self.ciclo0 + 8.0
                    atual = k == mk
                    cor = VERDE if vence else (AMARELO if atual else ACO1)
                    bloco(tela, x, 170 - h, x + 14, 170, VERDE if vence else (DAD_E if atual else ACO0), cor, TIN0)
                    tela.texto(str(k), x + 5, 176, cor, tam=9, contorno=PRETO)
                    if atual or vence or t >= self.ciclo0 + 8.0:
                        num = str(int(self.notas[k] * f))
                        tela.texto(num, x + 7 - tela.largura_texto(num, 9) // 2, 160 - h, cor, tam=9, contorno=PRETO)
                if mk is not None:
                    self._icone(tela, mk, PX0 + 120, 78, 2)
                    tela.texto(f"MÁSCARA {mk}", PX0, 80, AMARELO if t < self.ciclo0 + 8 else VERDE, tam=17, contorno=PRETO)
                if t >= self.ciclo0 + 8.0:
                    self.ptxt(tela, "VENCE: MENOS PONTOS", 98, VERDE)
                if t >= 30.8:
                    self.ptxt(tela, "FORMATO:", 112, LARANJA)
                    f = Q['formato']
                    for i in range(15):
                        x = PX0 + 48 + i * 7
                        on = any(t >= tt for (xy, tt) in self.fmt_t.items() if xy == D.posicoes_formato()[0][i])
                        b = (f >> (14 - i)) & 1
                        tela.texto(str(b) if on else '?', x, 112, LARANJA if on else ACO1, tam=9, contorno=PRETO)
        if mk is not None:
            self.vtxt(tela, f"MÁSCARA {mk}: {self.notas[mk]} PONTOS", VERDE if t >= self.ciclo0 + 8 else AMARELO, y=192)
        if t >= self.t_tinta + 2.0:
            u = (t - self.t_tinta - 2.0)
            if u < 1.5:
                for k in range(12):
                    a = k * math.pi / 6 + u * 2
                    r = 30 + u * 70
                    tela.px(CX0 + 75 + math.cos(a) * r, CY0 + 75 + math.sin(a) * r, AMARELO)
            self.rot(tela, "PRONTO!", LX, 100, CX0 + N * S + 2, CY0 + 75, VERDE)

    def _icone(self, tela, k, x, y, s=2, n=12):
        for yy in range(n):
            for xx in range(n):
                tela.ret(x + xx * s, y + yy * s, s, s, CIANO if D.MASCARAS[k](xx, yy) else FUNDO2)
        tela.ret_vazado(x - 1, y - 1, n * s + 2, n * s + 2, ACO1)

    def sons(self, fx):
        for k in range(8):
            self.nota(fx, self.ciclo0 + k, 67 + [0, 2, 4, 5, 7, 9, 11, 12][k], .08, .045)
        self.nota(fx, self.ciclo0 + 8.0, 84, .25, .05)
        for tt in sorted(set(self.fmt_t.values()))[::3]: self.tique(fx, tt, 2200, .03, .02)
        for k, m in enumerate((72, 76, 79, 84)): self.nota(fx, self.t_tinta + 2.0 + k * .12, m, .2, .05)
        for k in range(26): self.tique(fx, 9.4 + k * 4.0 / 26, 1600, .02, .012)


# ============================================================ 10 a mancha de café
class Mancha(Cena):
    PONTO = (CX0 + 12.5 * S, CY0 + 12.5 * S)
    R1 = 19.0                # primeira mancha (px)

    def preparar(self):
        self.ta = np.full((N, N), -INF)
        self.t_cai = 2.2
        self.t_cresce = 23.8
        self.t_limite = None
        self.serie = []
        for k in range(0, 61):
            r = self.R1 + k * .5
            m = self.mascara(r)
            est = D.bytes_estragados(D.mods_sob_mancha(m))
            self.serie.append((r, len(est), est))
        # raio em que passa de 11 bytes
        self.r_lim = next(r for r, n, _ in self.serie if n > 11)

    def mascara(self, r):
        return D.mascara_mancha(self.PONTO[0], self.PONTO[1], r, seed=4, gotas=r > 4)

    def raio(self, t):
        if t < self.t_cai: return 0.0
        if t < self.t_cresce: return self.R1 * ease((t - self.t_cai) / 1.2)
        u = clamp((t - self.t_cresce) / 6.0)
        return self.R1 + (self.r_lim + 1.0 - self.R1) * suave(u)

    def estado(self, r):
        if r <= 0: return 0, []
        best = self.serie[0]
        for s in self.serie:
            if s[0] <= r + 1e-6: best = s
        if r < self.R1 - .01:
            m = self.mascara(r)
            est = D.bytes_estragados(D.mods_sob_mancha(m))
            return len(est), est
        return best[1], best[2]

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        self.codigo(tela, t, FINAL, colorido=False, flash_on=False)
        r = self.raio(t)
        # a gota caindo
        if 0.6 <= t < self.t_cai:
            u = (t - .6) / (self.t_cai - .6)
            gx, gy = self.PONTO[0], -10 + (self.PONTO[1] + 10) * u * u
            tela.disco(gx, gy, 5, PRETO); tela.disco(gx, gy, 4, CAF1)
            tela.ret(gx - 1, gy - 9, 2, 6, CAF1); tela.px(gx - 2, gy - 2, CAF2)
        if r > 0:
            m = self.mascara(r) if r < self.R1 - .01 or t >= self.t_cresce else self._m1()
            D.pintar_mancha(tela, m)
            # brilho que mexe na superfície
            a = t * 1.3
            tela.px(self.PONTO[0] + math.cos(a) * r * .5, self.PONTO[1] + math.sin(a) * r * .4, CAF2)
        n_est, est = self.estado(r)
        lido = n_est <= 11
        # leitura
        if 7.8 <= t:
            u = ((t - 7.8) % 3.0) / 1.6
            if u < 1:
                yl = int(CY0 - 6 + (N * S + 12) * suave(u))
                tela.ret(CX0 - 10, yl, N * S + 20, 1, VERMELHO); tela.ret(CX0 - 10, yl - 1, N * S + 20, 1, CHAMA1)
            D.mira(tela, CX0 - 8, CY0 - 8, N * S + 16, N * S + 16, VERDE if lido else VERMELHO)
        if 15.4 <= t < 23.4:
            for b in est:
                mods = [ORDEM[b * 8 + j] for j in range(8)]
                ok = (t - 15.4) > 1 + est.index(b) * .6
                contorno_mods(tela, mods, VERDE if ok else (VERMELHO if int(t * 4) % 2 else BRANCO))
        self.contador(tela, TOTAL)
        if not VERTICAL:
            self.ptit(tela, "OS 44 BYTES", 64)
            for j in range(44):
                x = PX0 + (j % 11) * 15; y = 80 + (j // 11) * 12
                tela.ret(x, y, 13, 10, PRETO)
                cor = DAD_E if j < 22 else ECC_E
                if j in est:
                    cor = VERMELHO
                    if 15.4 <= t < 23.4 and (t - 15.4) > 1 + est.index(j) * .6: cor = VERDE
                tela.ret(x + 1, y + 1, 11, 8, cor)
            tela.texto(f"ESTRAGADOS: {n_est}", PX0, 132, VERMELHO if n_est else ACO3, tam=17, contorno=PRETO)
            if t >= 23.8:
                tela.texto("LIMITE: 11 (UM QUARTO)", PX0, 152, AMARELO, tam=9, contorno=PRETO)
            if t >= 9.0:
                if lido:
                    tela.texto("LEU:", PX0, 166, VERDE, tam=9, contorno=PRETO)
                    tela.texto(TEXTO, PX0, 178, VERDE, tam=9, contorno=PRETO)
                else:
                    tela.texto("NÃO LÊ MAIS", PX0, 168, VERMELHO, tam=17, contorno=PRETO)
        if t >= 9.0:
            self.vtxt(tela, TEXTO if lido else "NÃO LÊ MAIS", VERDE if lido else VERMELHO, y=192)
        if t >= 7.8:
            self.vtxt(tela, f"BYTES ESTRAGADOS: {n_est}", VERMELHO, y=8)

    def _m1(self):
        if not hasattr(self, '_cache1'): self._cache1 = self.mascara(self.R1)
        return self._cache1

    def sons(self, fx):
        n = int(.25 * SR); tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * (300 * tt - 500 * tt * tt)) * np.exp(-tt / .06) * np.minimum(1, tt / .003)
        fx.put(y.astype(np.float32), self.t0 + self.t_cai, .09)
        for k in range(10):
            if 7.8 + 3.0 * k + 1.6 < self.t_cresce + 6: self.bipe(fx, 7.8 + 3.0 * k + 1.6, 88, .045)
        t_falha = self.t_cresce + 6.0
        for k in range(3): self.tique(fx, t_falha + k * .25, 180, .2, .05)


# ============================================================ 11 como a câmera lê
class Leitura(Cena):
    PASSOS = ("ACHA OS LOCALIZADORES", "ENDIREITA A IMAGEM", "MONTA A GRADE", "LÊ O FORMATO",
              "TIRA A MÁSCARA", "LÊ OS BYTES", "CORRIGE OS ERROS")
    T_PASSO = (0.5, 4.2, 7.8, 11.4, 15.4, 19.2, 23.4)

    def passo(self, t):
        return max(-1, bisect.bisect_right(self.T_PASSO, t) - 1)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        p = self.passo(t)
        ang = -.32 * (1 - suave((t - 4.2) / 2.0))
        val = FINAL.copy()
        if p >= 4:
            u = clamp((t - 15.4) / 2.5)
            corte = int(u * (N + 1))
            val[:, :corte] = valor_mascara(MASC)[:, :corte] ^ 0
            cr = CRU.copy(); cr[M_PECA[FMT]] = FINAL[M_PECA[FMT]]
            val[:, :corte] = cr[:, :corte]
        cores = cores_de(val, np.ones((N, N), bool), np.zeros((N, N), bool))
        img = imagem_qr(cores, S)
        cx, cy = CARTAO[0] + 99, CARTAO[1] + 99
        esc = .8 + .2 * suave((t - 4.2) / 2.0)
        if abs(ang) > 1e-3 or esc < .999:
            colar_girado(tela, img, cx, cy, ang, esc)
        else:
            cartao(tela, cores)
        D.mira(tela, cx - 92, cy - 92, 184, 184, BRANCO if p < 6 else VERDE, 12)

        def ponto(mx, my):
            dx, dy = (24 + mx * S) - 99, (24 + my * S) - 99
            return cx + (math.cos(ang) * dx - math.sin(ang) * dy) * esc, cy + (math.sin(ang) * dx + math.cos(ang) * dy) * esc
        if p == 0 or p == 1:
            for (mx, my) in ((3.5, 3.5), (21.5, 3.5), (3.5, 21.5)):
                x, y = ponto(mx, my)
                rr = 26 * esc + 2 * math.sin(t * 9)
                tela.anel(x, y, rr, PRETO, 2); tela.anel(x, y, rr - 1, CIANO, 1)
        if p == 2:
            kmax = int((t - 7.8) * 12)
            for k in range(min(N, kmax) + 1):
                cor = BRANCO if k % 5 == 0 else CIANO
                tela.ret(CX0 + k * S - (1 if k else 0), CY0, 1, N * S, cor)
                tela.ret(CX0, CY0 + k * S - (1 if k else 0), N * S, 1, cor)
        if p == 3:
            a, b = D.posicoes_formato()
            mods = a + b
            for (x, y) in mods:
                tela.ret_vazado(CX0 + x * S - 1, CY0 + y * S - 1, S + 2, S + 2, LARANJA)
        if p == 4:
            u = clamp((t - 15.4) / 2.5)
            xx = CX0 + int(u * (N + 1)) * S
            tela.ret(min(xx, CX0 + N * S) - 1, CY0 - 6, 2, N * S + 12, CIANO)
        if p == 5:
            u = clamp((t - 19.2) / 3.8)
            h = int(u * (NB_TODOS - 1))
            for i in range(max(0, h - 20), h):
                (a2, b2), (c2, d2) = centro_mod(*ORDEM[i]), centro_mod(*ORDEM[i + 1])
                tela.linha(a2, b2, c2, d2, AMARELO if i < NB_DADOS else ROSA)
            hx, hy = centro_mod(*ORDEM[h]); tela.disco(hx, hy, 3, BRANCO)
            self.vtxt(tela, f"BYTE {h // 8 + 1} DE 44", AMARELO, y=192)
        if not VERTICAL:
            self.ptit(tela, "A CÂMERA, PASSO A PASSO", 6)
            for k, nome in enumerate(self.PASSOS):
                y = 22 + k * 15
                feito = k < p; atual = k == p
                tela.ret(PX0, y, 9, 9, PRETO)
                tela.ret(PX0 + 1, y + 1, 7, 7, VERDE if feito else (AMARELO if atual else FUNDO2))
                if feito:
                    tela.px(PX0 + 2, y + 4, PRETO); tela.px(PX0 + 3, y + 5, PRETO); tela.px(PX0 + 4, y + 4, PRETO)
                    tela.px(PX0 + 5, y + 3, PRETO); tela.px(PX0 + 6, y + 2, PRETO)
                tela.texto(f"{k + 1}. {nome}", PX0 + 13, y + 1, BRANCO if atual else (VERDE if feito else ACO1),
                           tam=9, contorno=PRETO)
            if p >= 3:
                tela.texto("NÍVEL Q, MÁSCARA 2", PX0 + 13, 134, LARANJA, tam=9, contorno=PRETO)
            if t >= 26.0:
                k = int((t - 26.0) / .08)
                self.ptit(tela, "RESULTADO", 150)
                tela.texto(TEXTO[:k], PX0, 166, VERDE, tam=9, contorno=PRETO)
                if k >= len(TEXTO):
                    tela.texto("LIDO!", PX0, 180, VERDE, tam=17, contorno=PRETO)
        if p >= 0 and p != 5:
            self.vtxt(tela, f"{p + 1}. {self.PASSOS[p]}", AMARELO, y=192)
        if t >= 26.0:
            self.vtxt(tela, TEXTO, VERDE, y=8)

    def sons(self, fx):
        for k, tt in enumerate(self.T_PASSO): self.nota(fx, tt, 72 + k * 2, .1, .045)
        self.bipe(fx, 26.0, 88, .06)


# ============================================================ 12 as versões
class Versoes(Cena):
    SEQ = ((1, 0.0), (2, 4.0), (3, 7.8), (5, 10.4), (10, 13.0), (20, 15.4), (40, 18.0))
    def preparar(self):
        self.mats = {v: D.versao(v) for v, _ in self.SEQ}
        self.rng = np.random.default_rng(12)
        self.hash = {v: self.rng.random(self.mats[v].shape) for v, _ in self.SEQ}

    def ver(self, t):
        v, t0 = self.SEQ[0]
        for vv, tt in self.SEQ:
            if t >= tt: v, t0 = vv, tt
        return v, t0

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        v, tv = self.ver(t)
        m = self.mats[v]
        n = m.shape[0]
        s = max(1, min(8, 180 // n))
        u = clamp((t - tv) / .5)
        vis = self.hash[v] < u
        cores = np.where(vis, np.where(m.astype(bool), TIN0, PAP3), -1).astype(np.int16)
        img = imagem_qr(cores, s, 2, encaixe=False)
        if u < 1:
            img[img == PAP2] = PAP3
        h = img.shape[0]
        cx, cy = CARTAO[0] + 99, 104
        x0, y0 = int(cx - h / 2), int(cy - h / 2)
        tela.ret(x0 - 1, y0 - 1, h + 2, h + 2, PRETO)
        colar(tela, img, x0, y0)
        # alinhamentos espalhados na versão 40
        if v == 40 and t >= 31.4:
            pos = (6, 30, 58, 86, 114, 142, 170)
            for a in pos:
                for b in pos:
                    if (a, b) in ((6, 6), (6, 170), (170, 6)): continue
                    px, py = x0 + 2 * s + a * s, y0 + 2 * s + b * s
                    if int(t * 3 + a + b) % 2: tela.ret_vazado(px - 3, py - 3, 7, 7, ROXO)
        if not VERTICAL:
            self.ptit(tela, "VERSÕES", 6)
            tela.texto(f"VERSÃO {v}", PX0, 20, AMARELO, tam=17, contorno=PRETO)
            tela.texto(f"{n} X {n}", PX0, 40, BRANCO, tam=17, contorno=PRETO)
            tela.texto(f"= {milhar(n * n)} MÓDULOS", PX0, 60, BRANCO, tam=9, contorno=PRETO)
            tela.texto(f"LADO = 4 X {v} + 17", PX0, 72, CIANO, tam=9, contorno=PRETO)
            # quadrados de tamanho real, um dentro do outro
            base_x, base_y = PX0 + 4, 88
            for vv, tt in self.SEQ:
                if t < tt: break
                nn = 4 * vv + 17
                lado = int(nn / 177 * 96)
                cor = AMARELO if vv == v else ACO1
                tela.ret_vazado(base_x, base_y + 96 - lado, lado, lado, cor)
            tela.texto("V1", base_x + 2, base_y + 86, ACO2, tam=9) if t < 18 else None
            if t >= 23.4:
                self.ptxt(tela, "VERSÃO 40-L CABE:", 104, ACO3, x=PX0 + 104 - 104 + 104)
            if t >= 23.4:
                tela.texto("2.953", PX0 + 104, 120, AMARELO, tam=17, contorno=PRETO)
                tela.texto("BYTES", PX0 + 104, 140, BRANCO, tam=9, contorno=PRETO)
                tela.texto("7.089", PX0 + 104, 154, AMARELO, tam=17, contorno=PRETO)
                tela.texto("ALGARISMOS", PX0 + 104, 174, BRANCO, tam=9, contorno=PRETO)
        self.vtxt(tela, f"VERSÃO {v}: {n} X {n}", AMARELO, y=192)

    def sons(self, fx):
        for k, (v, tt) in enumerate(self.SEQ): self.nota(fx, tt, 60 + k * 3, .14, .05)


# ============================================================ 13 história
class Historia(Cena):
    def preparar(self):
        v1 = D.versao(1)
        self.etq = imagem_qr(np.where(v1.astype(bool), TIN0, PAP3).astype(np.int16), 1, 2, encaixe=False)
        self.vel = 34.0
        self.scan_x = 190
        self.icones = ('engrenagem', 'pistao', 'disco')

    def caixas(self, t):
        out = []
        for k in range(12):
            x = -70 + (t * self.vel + k * 80) % (12 * 80) - 80 * 4
            out.append((k, x))
        return out

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        # parede da fábrica: chapas e janelas altas
        for x in range(0, 300, 40):
            tela.ret(x, 0, 39, 120, FUNDO2); tela.ret(x, 0, 1, 120, FUNDO3)
        for x in range(10, 300, 80):
            tela.ret(x, 18, 30, 40, TRACO); dither(tela, x + 1, 19, 28, 38, FUNDO3, TRACO)
            tela.ret(x + 14, 18, 2, 40, FUNDO2)
        for k, x in enumerate((60, 160, 260)):
            tela.ret(x, 0, 1, 12, ACO1); tela.ret(x - 7, 12, 15, 4, ACO2)
            tela.ret(x - 5, 16, 11, 2, CHAMA0)
            for j in range(3): tela.px(x - 4 + j * 4, 20 + j % 2, AMARELO)
        # esteira
        tela.ret(0, 152, 300, 8, ACO0); tela.ret(0, 152, 300, 1, ACO3)
        off = int(t * self.vel) % 12
        for x in range(-off, 300, 12):
            tela.ret(x, 154, 6, 2, ACO2)
        for x in range(8, 300, 24):
            tela.disco(x, 164, 5, PRETO); tela.disco(x, 164, 4, ACO1)
            a = t * self.vel / 4
            tela.px(x + math.cos(a) * 2.5, 164 + math.sin(a) * 2.5, ACO4)
        tela.ret(0, 170, 300, 38, FUNDO2)
        for x in range(4, 300, 24): tela.ret(x, 170, 3, 38, TRACO)
        lidos = 0
        for k, x in self.caixas(t):
            if x < -60 or x > 300: continue
            D.caixa_papelao(tela, x, 112, 56, 40, self.etq, self.icones[k % 3], t)
        # leitor (arco)
        sx = self.scan_x
        bloco(tela, sx - 4, 70, sx + 4, 152, ACO1, ACO3, ACO0)
        bloco(tela, sx - 16, 64, sx + 16, 72, ACO1, ACO3, ACO0)
        ativo = any(sx - 52 < x + 4 < sx - 20 for k, x in self.caixas(t))
        tela.ret(sx - 12, 72, 24, 2, VERMELHO if ativo else BRASA_)
        if ativo:
            for k in range(3):
                yy = 74 + (int(t * 60) + k * 13) % 76
                tela.ret(sx - 10, yy, 20, 1, VERMELHO)
        tela.disco(sx + 10, 68, 2, VERDE if ativo else ACO0)
        # painel: o diário da fábrica
        if not VERTICAL:
            self.ptit(tela, "JAPÃO, 1994", 6)
            tela.texto("1994", PX0, 22, AMARELO, tam=26, contorno=PRETO)
            self.ptxt(tela, "DENSO WAVE", 52, BRANCO, 17)
            self.ptxt(tela, "ETIQUETAS DE PEÇAS DE CARRO", 72, ACO3)
            self.ptit(tela, "CAIXAS LIDAS", 90)
            nl = int((t * self.vel + 80 * 4 + 70 - (sx - 30)) // 80)
            for j in range(5):
                num = nl - j
                if num <= 0: continue
                tela.texto(f"CAIXA {num:04d}  OK", PX0, 104 + j * 10, VERDE if j == 0 else ACO2, tam=9, contorno=PRETO)
            if t >= 15.8:
                self.ptit(tela, "DEPOIS", 160)
                self.ptxt(tela, "2000: NORMA ISO/IEC", 174, AMARELO)
                self.ptxt(tela, "HOJE: EM TODO LUGAR", 186, BRANCO)
        if t >= 15.8:
            u = suave((t - 15.8) / .5)
            x = 60; y = 80
            if u > 0:
                tela.ret(x - 2, y - 2, 104, 24, PRETO)
                tela.ret(x, y, 100, 20, VERMELHO); tela.ret(x + 2, y + 2, 96, 16, BRANCO); tela.ret(x + 3, y + 3, 94, 14, VERMELHO)
                tela.texto("ISO/IEC 2000", x + 50, y + 7, BRANCO, tam=9, centro=True, contorno=PRETO)
        self.vtxt(tela, "1994: PEÇAS DE CARRO", AMARELO, y=192)

    def sons(self, fx):
        for k in range(30):
            x0 = -70 + k * 80 - 80 * 4
            t_ = (self.scan_x - 36 - x0) / self.vel
            t_ = t_ % (12 * 80 / self.vel)
            if 0 < t_ < self.dur: self.bipe(fx, t_, 91, .035)
        self.nota(fx, 15.8, 67, .2, .05)


BRASA_ = 19


# ============================================================ 14 Pix
class Pix(Cena):
    def preparar(self):
        self.plaq = imagem_qr(cores_de(FINAL, np.ones((N, N), bool), np.zeros((N, N), bool)), 2, 4, encaixe=False)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        # céu de fim de tarde em degraus e a barraca
        dither(tela, 0, 0, 300, 40, FUNDO2, FUNDO3)
        tela.ret(0, 40, 300, 168, FUNDO2)
        for k in range(10):
            x = 10 + k * 28
            cor = VERMELHO if k % 2 == 0 else BRANCO
            poligono(tela, [(x, 30), (x + 28, 30), (x + 28, 50), (x + 14, 56), (x, 50)], cor)
            tela.ret(x, 30, 28, 1, PRETO)
        tela.ret(10, 28, 280, 3, MAD1)
        tela.ret(14, 56, 4, 92, MAD1); tela.ret(282, 56, 4, 92, MAD1)
        # bancada
        bloco(tela, 6, 148, 294, 206, MAD1, CAR1, MAD0)
        for x in range(6, 294, 32): tela.ret(x, 152, 1, 54, MAD0)
        # caixotes de fruta
        for j, (x, cor, luz) in enumerate(((30, LARANJA, CHAMA0), (100, VERDE, BRANCO))):
            bloco(tela, x, 124, x + 60, 148, CAR0, CAR1, MAD0)
            for k in range(6):
                fx_ = x + 8 + k * 9; fy = 120 - (k % 2) * 4 + math.sin(t * 2 + k) * .5
                tela.disco(fx_, fy, 5, PRETO); tela.disco(fx_, fy, 4, cor); tela.px(fx_ - 1, fy - 2, luz)
            tela.ret(x + 10, 96, 40, 16, PRETO); tela.ret(x + 11, 97, 38, 14, PAP3)
            tela.texto("R$ 5" if j == 0 else "R$ 7", x + 30, 101, TIN0, tam=9, centro=True)
        # a placa com o código
        px, py = 190, 72
        h = self.plaq.shape[0]
        bloco(tela, px - 6, py - 16, px + h + 6, py + h + 6, ACO1, ACO3, ACO0)
        tela.texto("PAGUE COM PIX", px + h // 2, py - 12, BRANCO, tam=9, centro=True, contorno=PRETO)
        colar(tela, self.plaq, px, py)
        tela.ret(px + h // 2 - 3, py + h + 6, 6, 18, ACO0)
        # o celular chega e lê
        u = suave((t - 1.5) / 2.0) - suave((t - 20.0) / 2.0)
        cx = int(lerp(320, 222, u)); cy = int(70 + 4 * math.sin(t * 1.7))
        if not VERTICAL or cx < 300:
            tela_ = D.celular(tela, cx, cy, 46, 84, t)
            sx, sy, sw, sh = tela_
            ok = t > 5.0 and u > .9
            tela.ret(sx, sy, sw, sh, FUNDO if not ok else FUNDO2)
            if not ok and u > .5:
                yy = sy + int((t * 40) % sh)
                tela.ret(sx, yy, sw, 1, VERMELHO)
                D.mira(tela, sx + 4, sy + 14, sw - 8, sw - 8, BRANCO, 5)
            elif ok:
                tela.texto("PIX", sx + sw // 2, sy + 6, CIANO, tam=9, centro=True)
                tela.disco(sx + sw // 2, sy + 34, 10, VERDE)
                linha_grossa(tela, sx + sw // 2 - 5, sy + 34, sx + sw // 2 - 1, sy + 38, 2, PRETO)
                linha_grossa(tela, sx + sw // 2 - 1, sy + 38, sx + sw // 2 + 6, sy + 29, 2, PRETO)
                tela.texto("PAGO", sx + sw // 2, sy + 52, VERDE, tam=9, centro=True)
        # painel: estático e dinâmico
        if not VERTICAL:
            self.ptit(tela, "BR CODE (BANCO CENTRAL)", 6)
            est = t < 15.8
            for j, (nome, y) in enumerate((("ESTÁTICO", 22), ("DINÂMICO", 104))):
                ativo = (j == 0 and 7.8 <= t < 15.8) or (j == 1 and t >= 15.8)
                painel(tela, PX0 - 2, y, 166, 76, borda=AMARELO if ativo else TRACO)
                tela.texto(nome, PX0 + 4, y + 5, AMARELO if ativo else ACO2, tam=9, contorno=PRETO)
                # mini código
                tela.ret(PX0 + 4, y + 20, 26, 26, PAP3)
                for a in range(0, 24, 4):
                    for b in range(0, 24, 4):
                        if FINAL[b, a]: tela.ret(PX0 + 5 + a, y + 21 + b, 4, 4, TIN0)
                if j == 0:
                    itens = ("CHAVE", "VALOR", "TEXTO")
                    for k, it in enumerate(itens):
                        on = ativo and (t - 8.2) > k * .6
                        bloco(tela, PX0 + 42, y + 18 + k * 17, PX0 + 110, y + 30 + k * 17, DAD_E if on else ACO0,
                              AMARELO if on else ACO1, TIN0)
                        tela.texto(it, PX0 + 46, y + 21 + k * 17, BRANCO if on else ACO2, tam=9, contorno=PRETO)
                    tela.texto("DENTRO", PX0 + 116, y + 36, AMARELO if ativo else ACO1, tam=9, contorno=PRETO)
                else:
                    on = ativo
                    bloco(tela, PX0 + 42, y + 26, PX0 + 98, y + 38, DAD_E if on else ACO0, AMARELO if on else ACO1, TIN0)
                    tela.texto("ENDEREÇO", PX0 + 45, y + 29, BRANCO if on else ACO2, tam=9, contorno=PRETO)
                    f = (t - 16.3) * 1.5
                    if on:
                        seta(tela, PX0 + 100, y + 32, PX0 + 124, y + 32, CIANO, 1, 3)
                        bloco(tela, PX0 + 128, y + 18, PX0 + 156, y + 50, ACO1, ACO3, ACO0)
                        for k in range(3):
                            tela.ret(PX0 + 132, y + 23 + k * 8, 20, 3, ACO0)
                            tela.px(PX0 + 150, y + 24 + k * 8, VERDE if int(t * 4 + k) % 2 else ACO2)
                        tela.texto("CONSULTA", PX0 + 42, y + 50, CIANO, tam=9, contorno=PRETO)
                        tela.texto("NA HORA", PX0 + 42, y + 60, CIANO, tam=9, contorno=PRETO)
        self.vtxt(tela, "PIX: BR CODE", AMARELO, y=192)

    def sons(self, fx):
        self.bipe(fx, 5.0, 88, .06)
        self.nota(fx, 5.15, 93, .2, .04)


# ============================================================ 15 resumo
class Resumo(Cena):
    PECAS = (("LOCALIZADOR", LOC, CIANO, (CX0 + N * S + 1, CY0 + 21)),
             ("SINCRONIA", SIN, VERDE, (CX0 + 15 * S, CY0 + 6 * S + 3)),
             ("ALINHAMENTO", ALI, ROXO, (CX0 + 20.5 * S + 1, CY0 + 18.5 * S)),
             ("FORMATO", FMT, LARANJA, (CX0 + 8 * S + 3, CY0 + 2 * S)),
             ("DADOS", 'd', AMARELO, (CX0 + 23 * S, CY0 + 23 * S)),
             ("CORREÇÃO", 'e', ROSA, (CX0 + 3 * S, CY0 + 12 * S)))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        u = clamp((t - 9.8) / 6.0)
        if t < 19.8:
            rank = (IDX.astype(float) / NB_MOD)
            rank[IDX < 0] = (np.mgrid[0:N, 0:N][0] / N)[IDX < 0]
            col = rank >= u
        else:
            col = np.zeros((N, N), bool)
        self.codigo(tela, t, FINAL, colorido=col, flash_on=False)
        if t < 9.8:
            for k, (nome, p, cor, (ax, ay)) in enumerate(self.PECAS):
                if t < .5 + k * 1.2: continue
                y = 14 + k * 30
                cot = None
                if nome == "FORMATO": cot = (CX0 + 8 * S + 3, CY0 + 4)
                if nome == "CORREÇÃO": cot = (CX0 + 12 * S, CY0 + 12 * S)
                self.rot(tela, nome, LX, y, ax, ay, cor)
        self.contador(tela, TOTAL)
        if not VERTICAL:
            self.ptit(tela, "O NOSSO CÓDIGO", 64)
            linhas = ("VERSÃO 2 (25 X 25)", "NÍVEL Q (25%)", "MÁSCARA 2", "17 LETRAS EM BYTES",
                      "22 + 22 = 44 BYTES")
            for k, l in enumerate(linhas):
                self.ptxt(tela, l, 80 + k * 12, BRANCO if k % 2 == 0 else ACO3)
            if t >= 19.8:
                D.celular(tela, 400 + int(4 * math.sin(t * 2)), 130, 36, 64, t)
                seta(tela, 392, 160 + int(2 * math.sin(t * 2)), 312, 160, AMARELO)
                tela.texto("APONTE", PX0, 140, AMARELO, tam=9, contorno=PRETO)
        if t >= 19.8:
            self.vtxt(tela, "APONTE A CÂMERA", AMARELO, y=8)

    def sons(self, fx):
        for k in range(6): self.nota(fx, .5 + k * 1.2, 72 + [0, 4, 7, 11, 12, 16][k], .1, .045)


# ============================================================ 16 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))
        self.mini = imagem_qr(cores_de(FINAL, np.ones((N, N), bool), np.zeros((N, N), bool)), 3, 3, encaixe=False)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            grade_fundo(tela, W, t)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            colar_girado(tela, self.mini, W // 2, 130, .15 * math.sin(t * 1.2), 1.0)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, grade=Grade, localizador=Localizador, sincronia=Sincronia,
             formato=Formato, texto=Texto, bytes=Bytes, correcao=Correcao, mascara=Mascara, mancha=Mancha,
             leitura=Leitura, versoes=Versoes, historia=Historia, pix=Pix, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep20_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        so = sys.argv[3:] or None
        fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = int(os.environ.get('COLS', 4 if len(ims) > 4 else len(ims)))
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
