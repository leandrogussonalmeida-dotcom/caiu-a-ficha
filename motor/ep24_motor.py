#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep24 — Como funciona o Wi-Fi (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

Protagonista: o PACOTE Nº 1 (um bloco de bits que brilha), do celular até o
roteador e dali para a internet. O painel da direita vai sendo preenchido à
medida que o vídeo ensina: frequência, comprimento de onda, bits por
símbolo, sinal (dBm) e o número do pacote; embaixo, a barra da VIAGEM sobe
do começo ao fim do episódio. Os símbolos e os pacotes saem nas batidas da
trilha (eventos 'batida' de longo.Trilha), as mesmas que viram som. O mapa
16-QAM e o pedaço de onda de cada símbolo vêm de `ep24_desenho` (calculados).

    python3 ep24_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep24_motor.py <saida.mp4> qam vez          # só esses capítulos (teste)
    python3 ep24_motor.py --folha <saida.png> [ids]    # quadros por capítulo (FR=.3,.8)
"""
import math, os, sys, bisect
import numpy as np
import longo as LG
import ep24_desenho as D                      # registra a paleta 'ep24' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1,
                   ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO, ROSA, ROXO, LATAO,
                   CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2)
from ep24_desenho import (OND0, OND1, OND2, OND3, CON0, CON1, CON2, MAD0, MAD1, MAD2, PAR0, PAR1, PLA0, PLA1,
                          PLA2, TEL0, TEL1, AGU0, AGU1, AGU2, PLN0, PLN1, ERR0, ERR1, SIN0, SIN1, SIN2, SIN3,
                          QAM16, QAM16_INV, PACOTE_BITS, PACOTE_SIMB, bits4, onda_simbolo, lambda_cm, dec, milhar,
                          clamp, lerp, suave, ease, halo, bloco, rotulo, centro_preso, seta, grade_fundo,
                          icone_wifi, celular, roteador, notebook, tv, tablet, pacote, cadeado, onda, aneis,
                          barras_sinal, barras_de_dbm, cor_dbm, constelacao, vizinhos16, MapaSinal, painel_wifi,
                          chao_madeira, parede_concreto, planta, geladeira, micro_ondas, molecula_agua, espectro,
                          C_LUZ)
import ritmo_marca as RM
from ep24_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2424, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que fica fora do recorte
SR = LG.SR
ORDEM = [c['id'] for c in CAPITULOS]
F24 = '2,4 GHZ'
L24 = dec(lambda_cm(2.4)) + ' CM'                 # 12,5 CM
L5 = dec(lambda_cm(5.0)) + ' CM'                  # 6,0 CM
L6 = dec(lambda_cm(6.0)) + ' CM'                  # 5,0 CM
B16 = '4 (16-QAM)'


def escurecer(tela, x, y, w, h):
    """Apaga metade dos pixels de uma área em xadrez (fundo fora de foco)."""
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    tela.buf[y0:y1, x0:x1][(xx + yy) % 2 == 0] = FUNDO


def xadrez(tela, x, y, w, h, cor, fase=0):
    """Pinta só metade dos pixels (luz translúcida em 8 bits)."""
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    tela.buf[y0:y1, x0:x1][(xx + yy + fase) % 2 == 0] = cor


class Cena:
    legenda = True
    brilho = .3
    XV = 120                     # centro do recorte vertical (x da tela larga)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.L = trilha.L
        self.bt = [e['t'] - self.t0 for e in self.L.entre('batida', self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]
        if len(self.bt) < 2:
            p = 60.0 / cap['bpm']
            self.bt = [k * p for k in range(int(self.dur / p) + 1)]
        self.spb = 60.0 / cap['bpm']
        self.i = ORDEM.index(cap['id'])
        caps = {c['id']: c for c in trilha.caps}
        self.v0, self.v1 = caps['casa']['t0'], caps['internet']['t1']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    # ---- batidas
    def nb(self, t): return bisect.bisect_right(self.bt, t + 1e-6)

    def tb(self, k):
        if k < len(self.bt): return self.bt[k]
        return self.bt[-1] + (k - len(self.bt) + 1) * self.spb

    def desde_batida(self, t):
        k = self.nb(t) - 1
        return t - self.tb(k) if k >= 0 else 9.0

    # ---- o painel: o que já foi aprendido até aqui
    def depois(self, cap, t, t_cap):
        """Verdadeiro se o instante (deste capítulo, t) já passou de `t_cap`
        dentro do capítulo `cap`."""
        j = ORDEM.index(cap)
        return self.i > j or (self.i == j and t >= t_cap)

    def est(self, t, **kw):
        e = dict(freq=F24 if self.depois('frequencia', t, .5) else None,
                 onda=L24 if self.depois('frequencia', t, 21.4) else None,
                 bits=B16 if self.depois('qam', t, 15.2) else None,
                 dbm=-55.0 if self.depois('distancia', t, 18.6) else None,
                 pacote=1, destaque=(), nota=(),
                 viagem=clamp((self.t0 + t - self.v0) / (self.v1 - self.v0)) if self.i >= 2 else None)
        e.update(kw)
        return e

    def painel(self, tela, t, **kw):
        if not VERTICAL: painel_wifi(tela, t, self.est(t, **kw))

    def vtxt(self, tela, txt, cor=BRANCO, y=8, tam=9):
        """Leitura curta no topo do recorte vertical (só nos Shorts)."""
        if VERTICAL:
            if y > 170: y = 4                  # embaixo fica a legenda do Short
            centro_preso(tela, txt, self.XV, y, cor, tam=tam, xmin=self.XV - 88, xmax=self.XV + 88)

    def rot(self, tela, *a, **k):
        if not VERTICAL or (self.XV - 90 <= a[1] and a[1] + tela.largura_texto(a[0], k.get('tam', 9)) <= self.XV + 90):
            rotulo(tela, *a, **k)

    def fundo(self, tela, t):
        grade_fundo(tela, 300, t)

    # ---- sons curtos (seno com decaimento: pico baixo, sem estalo)
    def tique(self, fx, t, f=1500.0, dur=.05, g=.06, pan=0.0):
        n = int(dur * SR); tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4)) * np.minimum(1, tt / .002)
        fx.put(y.astype(np.float32), self.t0 + t, g, pan)

    def nota(self, fx, t, m, dur=.08, g=.05, pan=0.0):
        self.tique(fx, t, 440 * 2 ** ((m - 69) / 12), dur, g, pan)

    def bipe(self, fx, t, m=88, g=.05, dur=.12, pan=0.0):
        n = int(dur * SR); tt = np.arange(n) / SR
        f = 440 * 2 ** ((m - 69) / 12)
        y = np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / .004) * np.minimum(1, (dur - tt) / .02)
        fx.put(y.astype(np.float32), self.t0 + t, g, pan)

    def zumbido(self, fx, t, dur=.3, f=140.0, g=.05):
        n = int(dur * SR); tt = np.arange(n) / SR
        y = (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 1.5 * tt)) * np.minimum(1, tt / .01) * \
            np.minimum(1, (dur - tt) / .05) / 1.4
        fx.put(y.astype(np.float32), self.t0 + t, g)


def voo(tela, x0, y0, x1, y1, u, t, n=None, cor=AMARELO, bits=None, emb=False, rastro=True, s=1):
    """Pacote voando de (x0, y0) a (x1, y1), com um trem de onda no rastro."""
    x, y = lerp(x0, x1, u), lerp(y0, y1, u)
    if rastro and u > 0:
        L = math.hypot(x1 - x0, y1 - y0) or 1
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        k = int(min(u * L, 60))
        for i in range(0, k, 1):
            d = i
            px = x - ux * d; py = y - uy * d
            a = 5 * (1 - d / 62) * math.sin(d / 3.0 - t * 14)
            tela.px(px - uy * a, py + ux * a, OND2 if d < 30 else OND1)
    pacote(tela, x, y, n, t, s=s, cor=cor, bits=bits, embaralhado=emb)
    return x, y


def ack(tela, x0, y0, x1, y1, u, t, cor=VERDE, txt='ACK'):
    x, y = lerp(x0, x1, u), lerp(y0, y1, u)
    halo(tela, x, y, 11, cor, int(t * 8) % 2)
    w = tela.largura_texto(txt, 9) + 6
    tela.ret(x - w // 2 - 1, y - 6, w + 2, 12, PRETO)
    tela.ret(x - w // 2, y - 5, w, 10, cor)
    tela.ret(x - w // 2, y - 5, w, 1, BRANCO)
    tela.texto(txt, x - w // 2 + 3, y - 3, PRETO, tam=9)
    return x, y


# ============================================================ 0 gancho
class Gancho(Cena):
    XV = 140

    def preparar(self):
        self.saidas = [b for b in self.bt if b < 6.0]
        self.lento = 6.2
        self.n_prota = len(self.saidas) + 1
        self.PX, self.PY = 70, 100
        self.RX, self.RY = 238, 104

    def u_voo(self, k, t):
        if k < len(self.saidas): return (t - self.saidas[k]) / .6
        return (t - self.lento) / 5.4                                   # câmera lenta no protagonista

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        celular(tela, 36, 70, 30, 58, t)
        roteador(tela, 214, 108, t, 1.0, ativo=1)
        n_ok = 0
        for k in range(len(self.saidas) + (1 if t >= self.lento else 0)):
            u = self.u_voo(k, t)
            if u < 0: continue
            if u < 1:
                prota = k == len(self.saidas)
                x, y = voo(tela, self.PX, self.PY, self.RX, self.RY, ease(u) if not prota else u, t, k + 1,
                           cor=AMARELO if prota else CIANO, s=1)
                if prota and not VERTICAL:
                    rotulo(tela, f"PACOTE Nº {k + 1}", 120, 40, x, y - 9, AMARELO, cotovelo=(x, 47))
                if prota and VERTICAL:
                    centro_preso(tela, f"PACOTE Nº {k + 1}", x, 40, AMARELO, xmin=self.XV - 88, xmax=self.XV + 88)
            else:
                n_ok += 1
                ua = (u - 1) / .5 if k < len(self.saidas) else (u - 1) * 5.4 / .8
                if ua < 1: ack(tela, self.RX, self.RY - 14, self.PX, self.PY - 14, ease(ua), t)
        if t >= self.lento:
            tela.texto("CÂMERA LENTA", 150 if not VERTICAL else self.XV, 184, CIANO, tam=9, contorno=PRETO,
                       centro=True)
        n = min(len(self.saidas) + 1, sum(1 for k in range(len(self.saidas)) if t >= self.saidas[k]) +
                (1 if t >= self.lento else 0))
        self.painel(tela, t, pacote=max(1, n), destaque=('pacote',), viagem=None,
                    nota=[("ENTREGUES: " + str(n_ok), VERDE)])
        self.vtxt(tela, f"PACOTES: {n}", BRANCO, y=8)

    def sons(self, fx):
        for k, s in enumerate(self.saidas):
            self.nota(fx, s, 76 + (k % 4) * 2, .06, .04, -.3)
            self.bipe(fx, s + .6, 88, .02, .06, .3)
        self.nota(fx, self.lento, 72, .3, .05)
        self.bipe(fx, self.lento + 5.4, 91, .04, .1, .3)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        grade_fundo(tela, W, t)
        for k in range(5):
            u = (t * .35 + k / 5) % 1.0
            pacote(tela, (24, 62, 418, 456, 100)[k], 200 - u * 200 if k < 4 else 214 - u * 40, None, t, brilho=False,
                   cor=CIANO if k % 2 else AMARELO)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA", "O WI-FI")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 13)]
            tela.texto(vis, W // 2 - larg // 2, 50 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("FEITO DE PIXELS", W // 2, 124, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 1.6:
            nn = 1 + int((t - 1.6) * 3) % 3
            icone_wifi(tela, W // 2, 196, 36, nn, CIANO, FUNDO3)

    def sons(self, fx):
        self.nota(fx, 1.2, 79, .2, .05)


# ============================================================ 2 casa
class Casa(Cena):
    XV = 150
    RX, RY = 216, 104                 # meio das antenas do roteador
    CX, CY = 66, 138                  # celular

    def lampada(self, tela, x, y, t, acesa=True):
        tela.ret(x, 52, 1, y - 52, ACO1)
        if acesa:
            pul = int(t * 2) % 2
            for k in range(50):
                w = 6 + k * .9
                if k > 24 and (k + pul) % 2: continue
                xadrez(tela, x - w / 2, y + 6 + k, w, 1, CHAMA1 if k < 22 else LATAO, k // 2 + pul)
        tela.ret(x - 6, y - 2, 13, 5, PRETO); tela.ret(x - 5, y - 1, 11, 3, ACO2)
        tela.disco(x, y + 4, 3.5, PRETO); tela.disco(x, y + 4, 2.6, CHAMA0 if acesa else ACO2)

    def casa(self, tela, t):
        tela.ret(8, 44, 286, 8, PRETO); tela.ret(10, 45, 282, 6, CON1); tela.ret(10, 45, 282, 1, CON2)
        tela.ret(10, 52, 282, 126, PAR0)
        dither(tela, 10, 52, 282, 30, PAR0, PAR1)
        tela.ret(8, 52, 3, 126, CON1); tela.ret(291, 52, 3, 126, CON1)
        parede_concreto(tela, 148, 52, 8, 126)
        chao_madeira(tela, 10, 292, 178, 8)
        # sala: mesa com o celular; quarto: estante com o roteador
        tela.ret(38, 152, 62, 4, PRETO); tela.ret(39, 152, 60, 3, MAD2); tela.ret(39, 155, 60, 1, MAD0)
        tela.ret(44, 156, 3, 22, MAD0); tela.ret(91, 156, 3, 22, MAD0)
        tela.ret(186, 128, 72, 4, PRETO); tela.ret(187, 128, 70, 3, MAD2)
        tela.ret(190, 132, 2, 46, MAD0); tela.ret(252, 132, 2, 46, MAD0)
        planta(tela, 120, 178, t, .8)
        self.lampada(tela, 60, 70, t)
        self.lampada(tela, 220, 70, t)

    def desenhar(self, tela, t, tg):
        grade_fundo(tela, 300, t)
        self.casa(tela, t)
        # as ondas: invisíveis (quase nada) até 22,2 s, depois desenhadas
        vis = suave((t - 22.2) / 1.2)
        if vis < 1:
            aneis(tela, self.RX, self.RY, t, 34, 22, 210, fantasma=True)
        if vis > 0:
            aneis(tela, self.RX, self.RY, t, 34, 22, 20 + 190 * vis, OND2, OND1)
            self.casa_frente(tela, t)
        else:
            self.casa_frente(tela, t)
        roteador(tela, self.RX - 24, 114, t, 1.0, ativo=1)
        celular(tela, self.CX - 8, 126, 16, 26, t, wifi=3)
        if t < 22.2 and not VERTICAL:
            tela.texto("(AS ONDAS ESTÃO AQUI, MAS", 160, 186, ACO2, tam=9, contorno=PRETO, centro=True)
            tela.texto("NINGUÉM VÊ)", 160, 196, ACO2, tam=9, contorno=PRETO, centro=True)
        # rótulos
        if t > .8:
            self.rot(tela, "ROTEADOR", 236, 58, self.RX + 18, 112, AMARELO, cotovelo=(self.RX + 18, 62))
            self.rot(tela, "CELULAR", 18, 104, self.CX, 128, AMARELO, cotovelo=(self.CX, 108))
        # o espectro no céu
        if t >= 7.4:
            u = suave((t - 7.4) / 1.5)
            pw, pl = espectro(tela, 14, 6, 276, 10, t, mostrar=u)
            if t >= 9.0 and not VERTICAL:
                for nome, cx, linha in (("RÁDIO", 14 + 41, 0), ("MICRO-ONDAS", 14 + 140, 0),
                                        ("INFRAVERMELHO", 14 + 176, 1), ("LUZ", pl, 0), ("UV", 14 + 233, 1),
                                        ("RAIOS X", 14 + 260, 0)):
                    tela.texto(nome, int(cx), 20 + linha * 10, ACO3 if nome != 'LUZ' else AMARELO, tam=9,
                               contorno=PRETO, centro=True)
            if t >= 14.8:
                pis = int(t * 3) % 2
                seta(tela, pw, 42 if not VERTICAL else 30, pw, 18, OND3 if pis else OND2, 2, 4)
                tela.texto("WI-FI", pw - 6, 33, OND3, tam=9, contorno=PRETO, centro='d')
                if not VERTICAL:
                    tela.ret(pl - 7, 4, 15, 1, AMARELO); tela.ret(pl - 7, 4, 1, 3, AMARELO)
                    tela.ret(pl + 7, 4, 1, 3, AMARELO)
        self.painel(tela, t, destaque=(), nota=[("ONDAS DE RÁDIO:", OND3), ("INVISÍVEIS AO OLHO", ACO2)])
        if t >= 22.2: self.vtxt(tela, "AS ONDAS, DESENHADAS", OND3, y=190)

    def casa_frente(self, tela, t):
        parede_concreto(tela, 148, 52, 8, 126)

    def sons(self, fx):
        self.nota(fx, 7.4, 72, .2, .04)
        self.nota(fx, 14.8, 79, .2, .05)
        for k in range(6): self.nota(fx, 22.2 + k * .2, 72 + k * 2, .08, .035)


# ============================================================ 3 antena
class Antena(Cena):
    XV = 116
    AX = 66                       # x da antena
    Y0, Y1 = 26, 160              # topo e pé da antena
    F_TELA = .55                  # vaivéns por segundo na tela (câmera lenta)
    V = 66.0                      # px/s da onda no desenho
    T_ONDA = 15.4

    def desl(self, t): return 9 * math.sin(2 * math.pi * self.F_TELA * t)

    def campo(self, x, t):
        """O campo que chega em x no instante t é o balanço da antena de antes."""
        te = t - (x - self.AX) / self.V
        return np.where(te >= self.T_ONDA, np.sin(2 * np.pi * self.F_TELA * te), 0.0)

    def rx(self): return 172 if VERTICAL else 246

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ax = self.AX
        # a caixa do roteador
        bloco(tela, 26, 160, 108, 188, PLA1, PLA2, PLA0)
        for k in range(4): tela.ret(40 + k * 12, 172, 3, 3, VERDE if (k + int(t * 4)) % 3 else ACO1)
        if not VERTICAL: tela.texto("ROTEADOR", 67, 192, ACO3, tam=9, contorno=PRETO, centro=True)
        # a antena: um tubo de metal com elétrons dentro
        tela.ret(ax - 6, self.Y0 - 2, 13, self.Y1 - self.Y0 + 4, PRETO)
        tela.ret(ax - 5, self.Y0, 11, self.Y1 - self.Y0, ACO2)
        tela.ret(ax - 5, self.Y0, 2, self.Y1 - self.Y0, ACO4)
        dither(tela, ax + 2, self.Y0, 4, self.Y1 - self.Y0, ACO2, ACO1)
        tela.ret(ax - 3, self.Y0 + 2, 7, self.Y1 - self.Y0 - 4, ACO0)
        d = self.desl(t)
        n = 11
        for k in range(n):
            ey = self.Y0 + 10 + k * (self.Y1 - self.Y0 - 20) / (n - 1) - d
            halo(tela, ax, ey, 4, OND1)
            tela.disco(ax, ey, 2.2, PRETO); tela.disco(ax, ey, 1.6, CIANO); tela.px(ax - 1, ey - 1, BRANCO)
        # cargas nas pontas
        if abs(d) > 2:
            cima = '-' if d > 0 else '+'
            for (yy, s) in ((self.Y0 - 10, cima), (self.Y1 + 2, '+' if cima == '-' else '-')):
                c = CIANO if s == '-' else VERMELHO
                tela.texto(s, ax + 10, yy, c, tam=17, contorno=PRETO)
        # vaivém (seta da velocidade dos elétrons)
        if t >= 7.8:
            v = math.cos(2 * math.pi * self.F_TELA * t)
            if abs(v) > .15:
                y0 = (self.Y0 + self.Y1) / 2
                seta(tela, ax - 16, y0 + 18 * v, ax - 16, y0 - 22 * v, AMARELO, 2, 4)
            self.rot(tela, "VAIVÉM", 4, 60, ax - 16, 78, AMARELO)
        # a onda: só nasce em T_ONDA, e anda para a direita
        rx = self.rx()
        if t >= self.T_ONDA:
            xs = np.arange(ax + 10, rx - 6)
            e = self.campo(xs, t)
            for x in range(ax + 14, rx - 6, 10):
                v = float(self.campo(np.array([x]), t)[0])
                if abs(v) > .08:
                    y1 = 96 - v * 30
                    tela.ret(x, min(96, y1), 1, abs(96 - y1) + 1, OND1)
            frente = ax + 10 + (t - self.T_ONDA) * self.V
            onda(tela, ax + 10, int(min(rx - 6, frente)), 96, 30, 1, fn=lambda xs: self.campo(xs, t))
            if frente < rx - 6:
                halo(tela, frente, 96, 6, OND3, int(t * 8) % 2)
        # o celular que recebe, com a antena dele
        cx = rx
        celular(tela, cx - 4, 72, 30, 56, t, wifi=3 if t >= 23.0 else 0, brilho=t >= 23.0)
        e_r = float(self.campo(np.array([cx]), t)[0])
        tela.ret(cx + 10, 40, 4, 32, PRETO); tela.ret(cx + 11, 41, 2, 31, ACO3)
        for k in range(3):
            tela.disco(cx + 12, 48 + k * 9 - 3 * e_r, 1.4, CIANO)
        # rótulos
        if t > .6:
            self.rot(tela, "ANTENA", 96, 30, ax + 6, 34, AMARELO)
            self.rot(tela, "ELÉTRONS", 96, 120, ax + 3, 128 - d, CIANO)
        if t >= self.T_ONDA + 1.5:
            self.rot(tela, "ONDA", 150 if not VERTICAL else 120, 140, 150 if not VERTICAL else 120, 112, OND3)
        if t >= 23.0:
            self.rot(tela, "SINAL!", rx - 46, 152 if not VERTICAL else 160, cx + 12, 128, VERDE)
        self.painel(tela, t, nota=[("CÂMERA LENTA", CIANO), ("DE VERDADE: BILHÕES/S", ACO2)])
        self.vtxt(tela, "CÂMERA LENTA", CIANO, y=196)

    def sons(self, fx):
        k = 0
        while True:
            tt = (k + .5) / (2 * self.F_TELA)
            if tt > self.dur - .3: break
            self.tique(fx, tt, 520 if k % 2 else 440, .08, .025)
            k += 1
        self.nota(fx, self.T_ONDA, 76, .3, .04)
        self.bipe(fx, 23.0, 88, .05)


# ============================================================ 4 frequência
class Frequencia(Cena):
    XV = 110
    ESC = 6.0                            # px por cm (desenho em escala)

    def lam_px(self, t):
        if t < 28.4: return lambda_cm(2.4) * self.ESC
        if t < 31.6: return lerp(lambda_cm(2.4), lambda_cm(5.0), suave((t - 28.4) / 1.2)) * self.ESC
        return lerp(lambda_cm(5.0), lambda_cm(6.0), suave((t - 31.6) / 1.2)) * self.ESC

    def faixa(self, t):
        if t < 28.4: return F24, L24
        if t < 31.6: return '5 GHZ', L5
        return '6 GHZ', L6

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 14.4:
            self.vaivem(tela, t)
        elif t < 21.4:
            self.viagem(tela, t)
        else:
            self.escala(tela, t)
        f, l = self.faixa(t)
        dest = ('freq',) if t < 14.4 else (('onda',) if 21.4 <= t < 35.4 else ())
        self.painel(tela, t, freq=f if t >= .5 else None, onda=l if t >= 21.4 else None, destaque=dest,
                    nota=[("CÂMERA LENTA", CIANO)] if t < 21.4 else [("DESENHO EM ESCALA", ACO2)])

    # ---- A: contar os vaivéns
    def vaivem(self, tela, t):
        f = 1.0
        x0, yc = 40, 100
        tela.ret(x0, 50, 1, 100, TRACO)
        y = yc - 36 * math.sin(2 * math.pi * f * t)
        halo(tela, x0, y, 7, OND1)
        tela.disco(x0, y, 4, PRETO); tela.disco(x0, y, 3, CIANO); tela.px(x0 - 1, y - 1, BRANCO)
        # rastro: o gráfico do vaivém andando para a direita
        dens = 1.0 if t < 7.4 else 1.0 + 6.0 * suave((t - 7.4) / 3.0)
        onda(tela, x0 + 4, 290, yc, 36, 1, fn=lambda xs: np.sin(2 * np.pi * f * (t - (xs - x0) / 70.0 * dens)),
             cor=OND2)
        n = int(t * f)
        if t < 7.4:
            tela.texto(f"VAIVÉNS: {n}", 160 if not VERTICAL else self.XV, 20, BRANCO, tam=17, contorno=PRETO,
                       centro=True)
            tela.texto("1 POR SEGUNDO = 1 HZ", 160 if not VERTICAL else self.XV, 170, ACO3, tam=9, contorno=PRETO,
                       centro=True)
        else:
            pis = int(t * 4) % 2
            cx = 160 if not VERTICAL else self.XV
            tela.texto("2,4 BILHÕES", cx, 14, AMARELO, tam=17, contorno=PRETO, centro=True)
            tela.texto("POR SEGUNDO", cx, 34, AMARELO if pis else CHAMA1, tam=17, contorno=PRETO, centro=True)
            tela.texto("2,4 GHZ = 2.400.000.000 HZ", cx, 170, ACO3, tam=9, contorno=PRETO, centro=True)

    # ---- B: a onda voa na velocidade da luz
    def viagem(self, tela, t):
        u = t - 14.4
        celular(tela, 12, 70, 26, 50, t)
        frente = 44 + ((u * 120) % 260)
        lam = 30
        onda(tela, 44, int(frente), 95, 20, lam, fase=t * 12)
        halo(tela, frente, 95, 8, OND3, int(t * 8) % 2)
        for k in range(3):
            xx = frente - 10 - k * 9
            tela.ret(int(xx), 80, 6 - k * 2, 1, BRANCO); tela.ret(int(xx), 110, 6 - k * 2, 1, BRANCO)
        cx = 160 if not VERTICAL else self.XV
        tela.texto("299.792 KM/S", cx, 20, AMARELO, tam=17, contorno=PRETO, centro=True)
        tela.texto("A VELOCIDADE DA LUZ", cx, 40, ACO3, tam=9, contorno=PRETO, centro=True)

    # ---- C/D/E: em escala, ao lado de um celular
    def escala(self, tela, t):
        esc = self.ESC
        # celular de 7 x 15 cm
        cw, ch = int(7 * esc), int(15 * esc)
        cx0, cy0 = 18, 152 - ch
        celular(tela, cx0, cy0, cw, ch, t)
        tela.texto("15 CM", cx0 + cw // 2, cy0 - 12, ACO3, tam=9, contorno=PRETO, centro=True)
        lam = self.lam_px(t)
        x0, x1, yc = 70, 294, 96
        fase = t * 2 * math.pi * .6
        onda(tela, x0, x1, yc, 26, lam, fase=fase)
        # duas cristas e a medida entre elas
        k0 = math.ceil(((x0 + 30 - x0) / lam - (fase + math.pi / 2) / (2 * math.pi)))
        xc = x0 + lam * (k0 + (fase + math.pi / 2) / (2 * math.pi))
        lim = (self.XV + 84) if VERTICAL else x1 - 4
        while xc + lam > lim and xc - lam > x0: xc -= lam
        a, b = int(round(xc)), int(round(xc + lam))
        for xx in (a, b):
            tela.ret(xx, yc - 40, 1, 12, AMARELO); tela.ret(xx, yc - 26, 1, 2, AMARELO)
        tela.ret(a, yc - 34, b - a, 1, AMARELO)
        f, l = self.faixa(t)
        tela.texto(l, (a + b) // 2, yc - 50, AMARELO, tam=17 if not VERTICAL else 9, contorno=PRETO, centro=True)
        # régua em cm
        ry = 160
        tela.ret(x0 - 52, ry, 278, 10, PRETO)
        tela.ret(x0 - 51, ry + 1, 276, 8, LATAO)
        dither(tela, x0 - 51, ry + 5, 276, 4, LATAO, MAD1)
        for cm in range(0, 46):
            xx = int(x0 - 50 + cm * esc)
            if xx > x1: break
            hh = 5 if cm % 5 == 0 else 2
            tela.ret(xx, ry + 1, 1, hh, PRETO)
            if cm % 10 == 0:
                tela.texto(str(cm), xx, ry + 12, ACO3, tam=9, contorno=PRETO, centro=True)
        tela.texto("CM", x0 + 232, ry + 12, ACO3, tam=9, contorno=PRETO)
        tela.texto(f, 180 if not VERTICAL else self.XV, 18, BRANCO, tam=17, contorno=PRETO, centro=True)
        if t >= 35.4:
            self.anatel(tela, t)

    def anatel(self, tela, t):
        u = ease((t - 35.4) / .6)
        x, y, w, h = 64, int(lerp(220, 40, u)), 196, 100
        escurecer(tela, 0, 0, 300, PALCO_H)
        tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
        tela.ret(x, y, w, h, LG.CERAMICA)
        dither(tela, x, y + h - 20, w, 20, LG.CERAMICA, ACO4)
        tela.ret(x, y, w, 12, AGU0)
        tela.texto("BRASIL", x + 6, y + 3, BRANCO, tam=9)
        tela.texto("25/02/2021", x + w - 6, y + 3, BRANCO, tam=9, centro='d')
        tela.texto("ANATEL", x + 8, y + 18, PRETO, tam=17)
        tela.texto("FAIXA DE 6 GHZ:", x + 8, y + 40, PRETO, tam=9)
        tela.texto("5,925 A 7,125 GHZ", x + 8, y + 52, AGU0, tam=9)
        tela.texto("PARA O WI-FI 6E", x + 8, y + 64, PRETO, tam=9)
        if t >= 36.6:
            v = ease((t - 36.6) / .25)
            sx, sy = x + 140, y + 62
            r = 34 - 6 * v
            tela.anel(sx, sy, r, ERR1, 1.5)
            tela.texto("2021", sx, sy - 7, ERR1, tam=17, centro=True)

    def sons(self, fx):
        for k in range(1, 8): self.tique(fx, k * 1.0, 900, .05, .03)
        self.nota(fx, 7.4, 84, .2, .05)
        self.nota(fx, 21.4, 76, .2, .04)
        self.nota(fx, 28.4, 79, .2, .04)
        self.nota(fx, 31.6, 83, .2, .04)
        self.zumbido(fx, 36.6, .12, 180, .05)


# ============================================================ 5 bits na onda
class Bits(Cena):
    XV = 130
    X0, X1, YC = 46, 292, 100
    V = 50.0                             # px/s
    CICLOS = 2

    def preparar(self):
        self.ts = 2 * self.spb               # 1 símbolo a cada 2 batidas
        self.bits = PACOTE_BITS * 4

    def modo(self, te):
        if te < 7.8: return 0
        if te < 15.8: return 1
        if te < 23.8: return 2
        return 3

    def simbolo(self, k):
        """(amplitude, sinal, rótulo) do símbolo k (emitido em k * ts)."""
        te = k * self.ts
        m = self.modo(te)
        if m == 0: return 1.0, 1, ''
        if m == 1:
            b = self.bits[k]
            return (1.0 if b == '1' else .35), 1, b
        if m == 2:
            b = self.bits[k]
            return 1.0, (1 if b == '0' else -1), b
        b = self.bits[2 * k:2 * k + 2]
        return (1.0 if b[0] == '1' else .35), (1 if b[1] == '0' else -1), b

    def valor(self, xs, t):
        te = t - (xs - self.X0) / self.V
        k = np.floor(te / self.ts).astype(int)
        u = te / self.ts - k
        out = np.zeros(len(xs))
        for kk in np.unique(k):
            if kk < 0: continue
            a, s, _ = self.simbolo(int(kk))
            m = k == kk
            out[m] = a * s * np.sin(2 * np.pi * self.CICLOS * u[m])
        out[te < 0] = 0
        return out

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        celular(tela, 8, 72, 30, 56, t)
        onda(tela, self.X0, int(min(self.X1, self.X0 + t * self.V)), self.YC, 34, 1, fn=lambda xs: self.valor(xs, t))
        # fronteiras e rótulos dos símbolos
        kmax = int(t / self.ts)
        for k in range(max(0, kmax - 6), kmax + 1):
            xb = self.X0 + (t - k * self.ts) * self.V
            if xb > self.X1: continue
            for yy in range(54, 146, 4): tela.px(int(xb), yy, TRACO)
            a, s, r = self.simbolo(k)
            xm = xb - self.ts * self.V / 2
            if r and self.X0 + 6 < xm < self.X1 - 4:
                c = AMARELO if k == kmax - 1 else BRANCO
                tela.texto(r, int(xm), 40, c, tam=17, contorno=PRETO, centro=True)
                m = self.modo(k * self.ts)
                if m in (1, 3): tela.texto('ALTA' if a > .5 else 'BAIXA', int(xm), 150, ACO3, tam=9,
                                           contorno=PRETO, centro=True)
                if m in (2, 3): tela.texto('SOBE' if s > 0 else 'DESCE', int(xm), 160 if m == 3 else 150,
                                           OND3, tam=9, contorno=PRETO, centro=True)
        # pulsinho na antena do celular a cada símbolo
        d = (t % self.ts)
        if d < .2: halo(tela, 38, 76, 8 - d * 20, OND3)
        m = self.modo(t)
        bps = {0: '0', 1: '1', 2: '1', 3: '2'}[m]
        nomes = {0: ("SÓ BALANÇA", ACO2), 1: ("ALTURA: ALTA = 1", AMARELO), 2: ("FASE: SOBE = 0", OND3),
                 3: ("ALTURA + FASE", AMARELO)}
        self.painel(tela, t, bits=bps, destaque=('bits',), nota=[nomes[m], ("1 SÍMBOLO A CADA 2 BATIDAS", ACO2)])
        tela.texto("DIREÇÃO DA ONDA", 170 if not VERTICAL else self.XV, 186, ACO2, tam=9, contorno=PRETO,
                   centro=True)
        if not VERTICAL: seta(tela, 214, 189, 240, 189, ACO2, 1, 3)
        self.vtxt(tela, f"BITS POR SÍMBOLO: {bps}", AMARELO, y=8)

    def sons(self, fx):
        k = 0
        while k * self.ts < self.dur - .2:
            a, s, r = self.simbolo(k)
            m = 72 if not r else (79 if a > .5 else 74) + (0 if s > 0 else -5)
            self.nota(fx, k * self.ts, m, .07, .035, .2)
            k += 1


# ============================================================ 6 o mapa 16-QAM
class Qam(Cena):
    XV = 218
    CX, CY, P = 222, 96, 34

    def preparar(self):
        self.t_envio = 30.8

    def ponto_livre(self, t):
        a = .55 + .35 * math.sin(t * .9)
        f = t * .7
        return a * 3 * math.sqrt(2) * math.cos(f), a * 3 * math.sqrt(2) * math.sin(f)

    def estado(self, t):
        """(I, Q, símbolo ou None, índice no pacote ou None)"""
        if t < 15.2:
            I, Q = self.ponto_livre(t)
            return I, Q, None, None
        if t < 23.0:
            I, Q = self.ponto_livre(t)
            Ii = int(clamp(round((I + 3) / 2) * 2 - 3, -3, 3)); Qi = int(clamp(round((Q + 3) / 2) * 2 - 3, -3, 3))
            return Ii, Qi, QAM16_INV[(Ii, Qi)], None
        if t < self.t_envio:
            k = int((t - 23.0) / (2 * self.spb))
            s = [5, 15, 0, 9, 6, 12, 3, 10][k % 8]
            I, Q = QAM16[s]
            return I, Q, s, None
        k = min(7, int((t - self.t_envio) / self.spb))
        s = PACOTE_SIMB[k]
        I, Q = QAM16[s]
        return I, Q, s, k

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        I, Q, s, kp = self.estado(t)
        cx, cy, p = self.CX, self.CY, self.P
        mostrar = clamp((t - 15.2) / 4.8) if t >= 15.2 else 0.0
        viz = vizinhos16(s) if (s is not None and 23.0 <= t < self.t_envio) else None
        constelacao(tela, cx, cy, p, t, ativo=s if mostrar > 0 else None, vizinhos=viz, rotulos=mostrar > 0,
                    mostrar=mostrar, alvo_dif=s if viz else None)
        # o ponto e a linha até o centro (amplitude) + arco (fase)
        px, py = cx + I * p / 2, cy - Q * p / 2
        linha_grossa(tela, cx, cy, px, py, 3, PRETO)
        tela.linha(cx, cy, px, py, OND3 if t < 15.2 else AMARELO)
        fase = math.atan2(Q, I)
        r = 14
        for k in range(24):
            a = fase * k / 23
            tela.px(cx + math.cos(a) * r, cy - math.sin(a) * r, CIANO)
        if t < 15.2 or mostrar < .2:
            halo(tela, px, py, 8, OND3, int(t * 8) % 2)
            tela.disco(px, py, 3.2, PRETO); tela.disco(px, py, 2.4, OND3)
        if t >= 7.8 and t < 23.0 and not VERTICAL:
            self.rot(tela, "AMPLITUDE", 150, 172, int((cx + px) / 2), int((cy + py) / 2), OND3)
            self.rot(tela, "FASE", 250, 172, int(cx + math.cos(fase / 2) * r), int(cy - math.sin(fase / 2) * r),
                     CIANO)
        # coluna da esquerda: o pacote e o pedaço de onda
        if not VERTICAL:
            self.coluna(tela, t, I, Q, s, kp)

        bits_txt = B16 if t >= 15.2 else None
        nota = [("AMPLITUDE: " + dec(math.hypot(I, Q) / (3 * math.sqrt(2)) * 100, 0) + "%", OND3),
                ("FASE: " + str(int(round(math.degrees(fase)) % 360)) + "°", CIANO)]
        if kp is not None: nota = [(f"SÍMBOLO {kp + 1} DE 8", AMARELO), ("BITS: " + bits4(s), AMARELO)]
        self.painel(tela, t, bits=bits_txt, destaque=('bits',) if t >= 15.2 else (), nota=nota)
        if kp is not None: self.vtxt(tela, f"SÍMBOLO {kp + 1} DE 8: {bits4(s)}", AMARELO, y=6)
        elif t >= 15.2: self.vtxt(tela, "16 PONTOS = 4 BITS", AMARELO, y=6)

    def onda_baixo(self, tela, t, I, Q, x0, x1, yc, amp):
        def fn(xs):
            u = (xs - x0) / (x1 - x0) * 2 + t * .8
            return (I * np.cos(2 * np.pi * u) - Q * np.sin(2 * np.pi * u)) / (3 * math.sqrt(2))
        tela.ret(x0, yc, x1 - x0, 1, FUNDO3)
        onda(tela, x0, x1, yc, amp, 1, fn=fn)

    def coluna(self, tela, t, I, Q, s, kp):
        tela.texto("O PACOTE", 10, 6, ACO3, tam=9, contorno=PRETO)
        for g in range(8):
            gx, gy = 10 + (g % 4) * 32, 18 + (g // 4) * 14
            b = bits4(PACOTE_SIMB[g])
            feito = kp is not None and g < kp
            agora = kp is not None and g == kp
            c = AMARELO if agora else (ACO2 if feito else BRANCO)
            if agora: tela.ret(gx - 2, gy - 2, 28, 11, FUNDO3)
            tela.texto(b, gx, gy, c, tam=9, contorno=PRETO)
        # a onda deste símbolo (2 ciclos)
        x0, x1, yc = 10, 136, 100
        tela.ret(x0, yc, x1 - x0, 1, FUNDO3)
        if kp is None:
            self.onda_baixo(tela, t, I, Q, x0, x1, yc, 30)
        else:
            # os símbolos já enviados, um atrás do outro, saindo pela direita
            def fn(xs):
                out = np.zeros(len(xs))
                w = (x1 - x0) / 3.0
                pos = (t - self.t_envio) / self.spb
                for j, x in enumerate(xs):
                    kk = pos - (x - x0) / w
                    k = int(math.floor(kk))
                    if 0 <= k <= min(7, int(pos)):
                        Ii, Qi = QAM16[PACOTE_SIMB[k]]
                        u = kk - k
                        out[j] = onda_simbolo(Ii, Qi, 1 - u)
                return out
            onda(tela, x0, x1, yc, 30, 1, fn=fn)
        tela.texto("A ONDA DESTE SÍMBOLO" if kp is None else "SAINDO DO CELULAR", 73, 140, ACO3, tam=9,
                   contorno=PRETO, centro=True)
        celular(tela, 52, 150, 20, 34, t, wifi=3)
        if kp is not None and self.desde_batida(t) < .25:
            halo(tela, 62, 152, 9, OND3)

    def sons(self, fx):
        for k in range(16): self.nota(fx, 15.2 + k * .3, 67 + (k % 8) * 2, .05, .03)
        k = 0
        while 23.0 + k * 2 * self.spb < self.t_envio - .1:
            self.nota(fx, 23.0 + k * 2 * self.spb, 76, .08, .035); k += 1
        for k in range(8):
            s = PACOTE_SIMB[k]
            self.nota(fx, self.t_envio + k * self.spb, 64 + s, .09, .04, .2)


# ============================================================ 7 256 e 1024-QAM com ruído
class Pontos(Cena):
    XV = 150
    CX, CY, R = 150, 104, 78            # meio lado da caixa

    def m(self, t):
        if t < 2.0: return 16
        if t < 7.8: return 256
        if t < 26.4: return 1024
        return 16

    def preparar(self):
        self.rng = np.random.default_rng(24)
        n = int(self.dur * 40) + 10
        self.amostras = self.rng.random((n, 2))
        self.ruido = self.rng.standard_normal((n, 2))

    def grade(self, m):
        k = int(round(math.sqrt(m)))
        passo = 2 * self.R / k
        return k, passo

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cx, cy, R = self.CX, self.CY, self.R
        m = self.m(t)
        k, passo = self.grade(m)
        tela.ret(cx - R - 2, cy - R - 2, 2 * R + 5, 2 * R + 5, PRETO)
        tela.ret(cx - R - 1, cy - R - 1, 2 * R + 3, 2 * R + 3, FUNDO2)
        tela.ret(cx - R - 1, cy, 2 * R + 3, 1, TRACO); tela.ret(cx, cy - R - 1, 1, 2 * R + 3, TRACO)
        sz = 4 if k == 4 else (2 if k == 16 else 1)
        for i in range(k):
            for j in range(k):
                px = int(cx - R + passo * (i + .5)); py = int(cy - R + passo * (j + .5))
                tela.ret(px - sz // 2, py - sz // 2, max(1, sz), max(1, sz), OND3 if k < 32 else OND2)
        # antes do ruído: um símbolo por batida acende no mapa (o ponto da vez)
        if t < 15.4:
            kb = self.nb(t)
            ii = int(self.amostras[kb % len(self.amostras), 0] * k)
            jj = int(self.amostras[kb % len(self.amostras), 1] * k)
            px = int(cx - R + passo * (ii + .5)); py = int(cy - R + passo * (jj + .5))
            halo(tela, px, py, 7 - 4 * min(1, self.desde_batida(t) / .4), CHAMA1, int(t * 8) % 2)
            tela.ret(px - 1, py - 1, 3, 3, AMARELO)
        # ruído: amostras recebidas = ponto certo + espalhamento
        erros, total = 0, 0
        if t >= 15.4:
            sigma = 2.3                                       # px, o mesmo para qualquer M
            n_now = int((t - 15.4) * 40)
            for a in range(max(0, n_now - 90), n_now):
                idade = (n_now - a) / 90
                ii = int(self.amostras[a, 0] * k); jj = int(self.amostras[a, 1] * k)
                tx = cx - R + passo * (ii + .5); ty = cy - R + passo * (jj + .5)
                rx = tx + self.ruido[a, 0] * sigma; ry = ty + self.ruido[a, 1] * sigma
                di = int(clamp(math.floor((rx - (cx - R)) / passo), 0, k - 1))
                dj = int(clamp(math.floor((ry - (cy - R)) / passo), 0, k - 1))
                erro = (di, dj) != (ii, jj)
                total += 1; erros += erro
                if t >= 22.8 and erro:
                    tela.ret(int(rx) - 1, int(ry) - 1, 3, 3, VERMELHO)
                    if k <= 16: tela.ret(int(tx) - 3, int(ty) - 3, 7, 1, VERMELHO)
                else:
                    tela.px(rx, ry, CIANO if idade < .6 else AGU1)
        nome = f"{m}-QAM"
        bits = {16: 4, 256: 8, 1024: 10}[m]
        tela.texto(nome, cx, 6, BRANCO, tam=17, contorno=PRETO, centro=True)
        if not VERTICAL:
            tela.texto(f"{milhar(m)}", 236, 30, ACO3, tam=9, contorno=PRETO)
            tela.texto("PONTOS", 236, 40, ACO3, tam=9, contorno=PRETO)
            tela.texto(f"{bits} BITS", 236, 52, AMARELO, tam=9, contorno=PRETO)
            if t >= 15.4:
                tela.texto("RUÍDO", 236, 84, CIANO, tam=9, contorno=PRETO)
            if t >= 22.8 and total:
                tela.texto("ERROS", 236, 110, VERMELHO, tam=9, contorno=PRETO)
                tela.texto(f"{int(round(100 * erros / total))}%", 236, 120, VERMELHO, tam=17, contorno=PRETO)
            if t >= 26.4:
                tela.texto("LONGE:", 236, 150, ACO3, tam=9, contorno=PRETO)
                tela.texto("MENOS", 236, 160, ACO3, tam=9, contorno=PRETO)
                tela.texto("PONTOS", 236, 170, ACO3, tam=9, contorno=PRETO)
        else:
            if t >= 22.8 and total: self.vtxt(tela, f"ERROS: {int(round(100 * erros / total))}%", VERMELHO, y=196)
        geracao = {16: "", 256: "WI-FI 5", 1024: "WI-FI 6"}[m]
        nota = [(geracao, ACO3)] if geracao else [("PERTO OU LONGE", ACO3)]
        self.painel(tela, t, bits=f"{bits} ({m}-QAM)", destaque=('bits',), nota=nota)

    def sons(self, fx):
        self.nota(fx, 2.0, 76, .15, .04)
        self.nota(fx, 7.8, 83, .15, .04)
        self.tique(fx, 15.4, 2400, .3, .015)
        for b in self.bt:
            if b < 15.4: self.tique(fx, b, 1800, .04, .015, .2)
        self.nota(fx, 26.4, 72, .2, .04)


# ============================================================ 8 distância
class Distancia(Cena):
    XV = 110
    SX, SY = 32, 96                      # o celular (fonte)
    PM = 16.0                            # px por metro

    def d_rx(self, t):
        """Distância (m) do roteador que mede o sinal (só a partir de 18,6 s)."""
        u = (t - 18.6) / 17.0
        return 1.0 + 8.0 * (.5 - .5 * math.cos(math.pi * 2 * clamp(u) * .75))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        sx, sy, pm = self.SX, self.SY, self.PM
        celular(tela, 8, 68, 22, 44, t)
        # régua em metros
        ry = 176
        tela.ret(sx - 1, ry, 12 * pm + 3, 4, PRETO); tela.ret(sx, ry + 1, 12 * pm + 1, 2, ACO2)
        for m_ in range(0, 13):
            xx = int(sx + m_ * pm)
            tela.ret(xx, ry - (4 if m_ % 2 == 0 else 2), 1, 4 if m_ % 2 == 0 else 2, ACO3)
            if m_ % 2 == 0: tela.texto(str(m_), xx, ry + 7, ACO3, tam=9, contorno=PRETO, centro=True)
        tela.texto("M", int(sx + 12 * pm) + 6, ry + 7, ACO3, tam=9, contorno=PRETO)
        if t < 12.6:
            self.voo(tela, t)
        elif t < 18.6:
            self.quadrado(tela, t)
        else:
            self.termometro(tela, t)

    def voo(self, tela, t):
        sx, sy, pm = self.SX, self.SY, self.PM
        u = ((t - .8) % 5.8) / 5.2 if t >= .8 else 0.0
        d = 12.0 * clamp(u)
        x = sx + d * pm
        for k in range(5):
            r = d * pm - k * 12
            if r > 4: tela.anel(sx, sy, r, OND2 if k < 2 else OND1, .6)
        if t >= .8:
            pacote(tela, x, sy, 1, t)
        ns = d / C_LUZ * 1e9
        cx = 150 if not VERTICAL else self.XV
        tela.texto(f"{dec(d, 1)} M", cx, 14, BRANCO, tam=17, contorno=PRETO, centro=True)
        tela.texto(f"{dec(ns, 1)} NANOSSEGUNDOS", cx, 34, AMARELO, tam=9, contorno=PRETO, centro=True)
        if t >= 6.6:
            xf = int(sx + 10 * pm)
            for yy in range(50, 170, 3): tela.px(xf, yy, AMARELO)
            tela.texto("10 M = 33 NS", xf, 150, AMARELO, tam=9, contorno=PRETO, centro=True)
        dbm = -40 - 20 * math.log10(max(d, 1.0))
        self.painel(tela, t, destaque=('pacote',), nota=[("CÂMERA LENTA:", CIANO), ("33 NS VIRAM 5 S", ACO2)])
        self.vtxt(tela, "CÂMERA LENTA", CIANO, y=196)

    def quadrado(self, tela, t):
        """Inverso do quadrado: a mesma energia passa por 1, 4, 9 quadradinhos."""
        sx, sy, pm = self.SX, self.SY, self.PM
        lado1 = 12
        for n, dm in ((1, 3), (2, 6), (3, 9)):
            x = sx + dm * pm
            hh = lado1 * n
            for i in range(n):
                for j in range(n):
                    yy = sy - hh / 2 + j * lado1
                    xx = x + i * 3
                    tela.ret(int(xx) - 1, int(yy), 3, lado1 - 1, PRETO)
                    tela.ret(int(xx), int(yy) + 1, 2, lado1 - 3, OND1 if n > 1 else OND2)
            frac = "1" if n == 1 else f"1/{n * n}"
            tela.texto(frac, int(x) + 2, int(sy + hh / 2) + 6, AMARELO if n == 2 else BRANCO, tam=17 if n == 2 else 9,
                       contorno=PRETO, centro=True)
            tela.texto(f"{dm} M", int(x) + 2, int(sy - hh / 2) - 12, ACO3, tam=9, contorno=PRETO, centro=True)
        # bordas do cone
        x9 = sx + 9 * pm
        for s in (-1, 1):
            tela.linha(sx, sy, x9 + 4, sy + s * lado1 * 1.5 * 3 / 1.0 / 1, TRACO)
        # partículas de energia: 36 que saem juntas e se espalham
        rng = np.random.default_rng(5)
        alvos = rng.random((36, 2)) - .5
        for k in range(36):
            u = ((t - 12.6) * .35 + k / 36) % 1.0
            dm = u * 10.0
            x = sx + dm * pm
            y = sy + alvos[k, 1] * lado1 * dm / 3
            tela.px(x, y, CHAMA0); tela.px(x + 1, y, CHAMA1)
        self.painel(tela, t, nota=[("2 X DISTÂNCIA =", ACO3), ("1/4 DA POTÊNCIA (-6 DB)", AMARELO)])
        self.vtxt(tela, "2 X LONGE = 1/4", AMARELO, y=196)

    def termometro(self, tela, t):
        sx, sy, pm = self.SX, self.SY, self.PM
        d = self.d_rx(t)
        dbm = -40 - 20 * math.log10(d)
        xr = sx + d * pm
        for k in range(4):
            r = ((t * 40) % 24) + k * 24
            if r < d * pm: tela.anel(sx, sy, r, OND1, .5)
        pt = roteador(tela, int(xr) - 12, sy + 14, t, .5, ativo=1)
        # régua de dBm em pé
        x0, y0, y1 = 252 if not VERTICAL else 176, 18, 168
        tela.ret(x0 - 1, y0 - 1, 8, y1 - y0 + 2, PRETO)
        for k in range(y1 - y0):
            v = -10 - 90 * k / (y1 - y0)
            tela.ret(x0, y0 + k, 6, 1, cor_dbm(v))
        for v in range(0, -101, -10):
            yy = int(y0 + (-10 - v) / 90 * (y1 - y0)) if v <= -10 else y0 - 8
            if v == 0: continue
            tela.ret(x0 + 7, yy, 3, 1, ACO3)
            tela.texto(str(v), x0 + 12, yy - 3, ACO3 if v not in (-10, -100) or t < 30.4 else AMARELO, tam=9,
                       contorno=PRETO)
        ym = int(y0 + (-10 - dbm) / 90 * (y1 - y0))
        tela.ret(x0 - 8, ym - 1, 7, 3, BRANCO); tela.ret(x0 - 10, ym - 3, 3, 7, BRANCO)
        tela.texto(f"{int(round(dbm))} DBM", x0 - 12, ym - 3, cor_dbm(dbm), tam=9, contorno=PRETO, centro='d')
        cx = 130 if not VERTICAL else self.XV - 20
        tela.texto(f"{dec(d, 1)} M", int(xr), sy - 30, BRANCO, tam=9, contorno=PRETO, centro=True)
        if t >= 24.6 and not VERTICAL:
            for k, (a, b) in enumerate((("0 DBM", "1 MW"), ("-10 DBM", "1/10 MW"), ("-20 DBM", "1/100 MW"),
                                        ("-30 DBM", "1/1.000 MW"))):
                tela.texto(a, 80, 20 + k * 11, ACO3, tam=9, contorno=PRETO)
                tela.texto(b, 140, 20 + k * 11, AMARELO, tam=9, contorno=PRETO)
        if t >= 30.4:
            tela.texto("PERTO", x0 - 4, y0 - 12, VERDE, tam=9, contorno=PRETO, centro='d')
            tela.texto("QUASE NADA", x0 - 4, y1 + 2, VERMELHO, tam=9, contorno=PRETO, centro='d')
        self.painel(tela, t, dbm=dbm, destaque=('dbm',), nota=[("A 1 M: -40 DBM (EXEMPLO)", ACO2)])
        self.vtxt(tela, f"{int(round(dbm))} DBM A {dec(d, 1)} M", cor_dbm(dbm), y=196)

    def sons(self, fx):
        self.nota(fx, .8, 76, .1, .04)
        self.bipe(fx, 6.0, 88, .04)
        self.nota(fx, 12.6, 72, .2, .04)
        self.nota(fx, 18.6, 79, .2, .04)


# ============================================================ 9 paredes
class Paredes(Cena):
    XV = 104
    RX, RY = 214, 50
    MPP = .05                            # metros por pixel (planta de 14 x 9,6 m)

    def preparar(self):
        X0, Y0, X1, Y1 = 10, 8, 290, 200
        self.caixa = (X0, Y0, X1, Y1)
        P = 8.0
        paredes = [(150, Y0, 150, 104, P), (150, 134, 150, Y1, P), (X0, 112, 100, 112, P), (126, 112, 150, 112, P),
                   (150, 120, 230, 120, P), (256, 120, X1, 120, P)]
        self.paredes = paredes
        gx0, gy0, gx1, gy1 = 30, 136, 58, 186             # geladeira (metal)
        G = 22.0
        self.gel = (gx0, gy0, gx1, gy1)
        gel = [(gx0, gy0, gx1, gy0, G), (gx1, gy0, gx1, gy1, G), (gx0, gy1, gx1, gy1, G), (gx0, gy0, gx0, gy1, G)]
        self.plantas = [(110, 66), (124, 76), (112, 84)]
        A = 3.0
        agua = []
        for (px, py) in self.plantas:
            agua += [(px - 6, py - 6, px + 6, py + 6, A), (px - 6, py + 6, px + 6, py - 6, A)]
        args = (X0, Y0, X1 - X0, Y1 - Y0, self.MPP, self.RX, self.RY)
        self.mapas = [MapaSinal(*args, []), MapaSinal(*args, paredes), MapaSinal(*args, paredes + gel),
                      MapaSinal(*args, paredes + gel + agua),
                      MapaSinal(*args, [(a, b, c, d, p * 1.6) for (a, b, c, d, p) in paredes + gel + agua])]
        self.trocas = [0.0, 2.6, 7.8, 14.8, 21.8]
        cam = [(60, 40), (120, 30), (130, 96), (80, 150), (110, 180), (200, 170), (270, 160), (264, 90),
               (240, 30), (180, 80), (100, 60)]
        self.caminho = cam

    def mapa_idx(self, t):
        return max(i for i, a in enumerate(self.trocas) if t >= a)

    def celular_xy(self, t):
        cam = self.caminho
        L = len(cam)
        u = (t * .22) % L
        i = int(u); f = suave(u - i)
        a, b = cam[i], cam[(i + 1) % L]
        return lerp(a[0], b[0], f), lerp(a[1], b[1], f)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H, :300] = FUNDO
        if t < 28.8:
            self.planta_casa(tela, t)
        else:
            self.alcance(tela, t)

    def planta_casa(self, tela, t):
        X0, Y0, X1, Y1 = self.caixa
        i = self.mapa_idx(t)
        ta = self.trocas[i]
        if i > 0:
            self.mapas[i - 1].desenhar(tela)
        self.mapas[i].desenhar(tela, revela=(t - ta) * 260 if i > 0 else (t + .3) * 260, t=t)
        # paredes de fora e de dentro
        tela.ret_vazado(X0 - 1, Y0 - 1, X1 - X0 + 2, Y1 - Y0 + 2, PRETO)
        tela.ret_vazado(X0 - 2, Y0 - 2, X1 - X0 + 4, Y1 - Y0 + 4, CON1)
        if t >= 2.6:
            for (a, b, c, d, p) in self.paredes:
                linha_grossa(tela, a, b, c, d, 5, PRETO)
                linha_grossa(tela, a, b, c, d, 3, CON1 if i < 4 else CON2)
        if t >= 7.8:
            gx0, gy0, gx1, gy1 = self.gel
            bloco(tela, gx0, gy0, gx1, gy1, ACO3, ACO4, ACO1)
            tela.ret(gx0 + 3, gy0 + 3, gx1 - gx0 - 6, 1, ACO1)
            self.rot(tela, "GELADEIRA", 64, 140, gx1, gy0 + 10, AMARELO)
            self.rot(tela, "METAL", 64, 150, gx1, gy0 + 20, ACO3)
        if t >= 14.8:
            for (px, py) in self.plantas:
                for k in range(5):
                    a = k * 1.26 + .1 * math.sin(t * 2 + k)
                    tela.disco(px + math.cos(a) * 3, py + math.sin(a) * 3, 3, PRETO)
                for k in range(5):
                    a = k * 1.26 + .1 * math.sin(t * 2 + k)
                    tela.disco(px + math.cos(a) * 3, py + math.sin(a) * 3, 2.2, PLN1 if k % 2 else PLN0)
            self.rot(tela, "PLANTAS (ÁGUA)", 22, 40, 106, 66, AGU2, cotovelo=(100, 44))
        # o roteador (de cima) e as ondas
        aneis(tela, self.RX, self.RY, t, 50, 30, 120 if i < 4 else 90, OND3, OND2, esp=.5)
        tela.ret(self.RX - 9, self.RY - 5, 19, 11, PRETO); tela.ret(self.RX - 8, self.RY - 4, 17, 9, PLA1)
        tela.ret(self.RX - 8, self.RY - 4, 17, 1, PLA2); tela.px(self.RX - 5, self.RY, VERDE); tela.px(self.RX - 2, self.RY, VERDE)
        self.rot(tela, "ROTEADOR", 236, 24, self.RX + 6, self.RY - 4, AMARELO)
        # o celular passeando
        x, y = self.celular_xy(t)
        dbm = self.mapas[i].em(x, y)
        tela.ret(int(x) - 5, int(y) - 8, 11, 17, PRETO); tela.ret(int(x) - 4, int(y) - 7, 9, 15, ACO1)
        tela.ret(int(x) - 3, int(y) - 5, 7, 10, TEL1)
        by = int(y) - 26 if y > 40 else int(y) + 12
        barras_sinal(tela, int(x) - 10, by, barras_de_dbm(dbm), h=10, cor=cor_dbm(dbm))
        tela.texto(f"{int(round(dbm))}", int(x) + 16, by + 3, cor_dbm(dbm), tam=9, contorno=PRETO)
        freq = '5 GHZ' if i == 4 else F24
        self.painel(tela, t, freq=freq, onda=L5 if i == 4 else L24, dbm=dbm,
                    destaque=('dbm',) if i < 4 else ('freq', 'dbm'),
                    nota=[("MAPA: CLARO = FORTE", SIN3), ("ESCURO = FRACO", SIN1)])
        self.vtxt(tela, f"{freq}: {int(round(dbm))} DBM", cor_dbm(dbm), y=196 if y < 150 else 4)
        if i == 4:
            tela.texto("5 GHZ", 156, 186 if not VERTICAL else 92, AMARELO, tam=17, contorno=PRETO, centro=True)

    def alcance(self, tela, t):
        u = ease((t - 28.8) / 1.0)
        cx, cy = 150, 104
        s = lerp(1.0, .25, u)
        # casinha encolhendo (contorno)
        X0, Y0, X1, Y1 = self.caixa
        def P(x, y): return cx + (x - self.RX) * s, cy + (y - self.RY) * s
        a = P(X0, Y0); b = P(X1, Y1)
        grade_fundo(tela, 300, t)
        tela.ret(int(a[0]), int(a[1]), int(b[0] - a[0]), int(b[1] - a[1]), FUNDO2)
        tela.ret_vazado(int(a[0]), int(a[1]), int(b[0] - a[0]), int(b[1] - a[1]), CON2)
        for (x0, y0, x1, y1, p) in self.paredes:
            p0, p1 = P(x0, y0), P(x1, y1)
            tela.linha(p0[0], p0[1], p1[0], p1[1], CON1)
        r = 20.0 / (self.MPP / .25) * u if u > 0 else 0
        r = 20.0 / (self.MPP / s)
        if u > .3:
            for k in range(3):
                rr = r * (1 - k * .02)
                tela.anel(cx, cy, rr, OND2 if k == 0 else OND1, .6)
            aneis(tela, cx, cy, t, 30, 20, r, OND1, OND0, esp=.5)
            tela.linha(cx, cy, cx + r, cy, AMARELO)
            tela.texto("20 M", int(cx + r / 2), cy + 4, AMARELO, tam=17, contorno=PRETO, centro=True)
        tela.disco(cx, cy, 3, PRETO); tela.disco(cx, cy, 2, PLA2)
        self.painel(tela, t, dbm=-80.0, destaque=(), nota=[("ALCANCE TÍPICO", ACO3), ("DENTRO DE CASA", ACO3)])
        self.vtxt(tela, "ALCANCE: UNS 20 M", AMARELO, y=4)

    def sons(self, fx):
        for a in self.trocas[1:]:
            self.tique(fx, a, 700, .2, .03)
        self.nota(fx, 28.8, 72, .3, .04)


# ============================================================ 10 micro-ondas
class Microondas(Cena):
    XV = 118
    PX_, PY_ = 136, 120                  # celular
    RX, RY = 186, 112                    # meio do roteador

    def preparar(self):
        self.saidas = [b for b in self.bt[1:] if b < self.dur - 1.2][::2]

    def vaza(self, t): return t >= 15.8 and (t % 3.0) < 2.0

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H, :300] = FUNDO
        dither(tela, 0, 0, 300, 150, PAR0, PAR1)
        tela.ret(0, 150, 300, 4, PRETO); tela.ret(0, 151, 300, 3, LG.CERAMICA)
        tela.ret(0, 154, 300, 54, MAD1); dither(tela, 0, 170, 300, 38, MAD1, MAD0)
        for x in range(30, 300, 60): tela.ret(x, 158, 1, 50, MAD0)
        ix, iy, iw, ih = micro_ondas(tela, 20, 86, t, True, w=100, h=64)
        # dentro: prato que gira, tigela, onda indo e voltando, moléculas
        tela.ret(ix + 6, iy + ih - 6, iw - 12, 3, ACO3)
        ang = t * 1.4
        bx = ix + iw // 2 + int(6 * math.sin(ang))
        tela.ret(bx - 12, iy + ih - 18, 24, 12, PRETO); tela.ret(bx - 11, iy + ih - 17, 22, 10, LG.CERAMICA)
        tela.ret(bx - 10, iy + ih - 17, 20, 3, AGU1)
        onda(tela, ix + 1, ix + iw - 1, iy + 14, 6, 20, fase=0, fn=lambda xs: np.sin(2 * np.pi * (xs - ix) / 22.0) *
             math.cos(t * 9), cor=LARANJA, cor_luz=CHAMA0, sombra=BRASA)
        for k in range(4):
            mx = bx - 9 + k * 6; my = iy + ih - 24 - (k % 2) * 4
            molecula_agua(tela, mx, my, t * 12 + k * 1.7, .9)
        if t >= 7.8:
            for k in range(4):
                u = (t * .5 + k * .25) % 1
                tela.px(bx - 6 + k * 4 + math.sin(u * 8 + k) * 2, iy + ih - 30 - u * 18, BRANCO if u < .5 else ACO3)
        if not VERTICAL or True:
            self.rot(tela, "ÁGUA", 30, 70, bx - 6, iy + ih - 24, AGU2)
        # o vazamento: anéis laranja saindo da porta
        if self.vaza(t):
            aneis(tela, ix + iw, iy + ih // 2, t, 60, 18, 150, LARANJA, BRASA, esp=.6)
        # bancada da direita: celular e roteador
        celular(tela, self.PX_ - 8, self.PY_ - 2, 16, 30, t)
        roteador(tela, self.RX - 24, 136, t, 1.0, ativo=1)
        for k, s in enumerate(self.saidas):
            u = (t - s) / .7
            if 0 <= u < 1:
                ruim = self.vaza(s + .35)
                voo(tela, self.PX_, self.PY_ - 14, self.RX, self.RY - 6, ease(u), t, k + 1,
                    cor=ERR1 if ruim and u > .4 else AMARELO, bits=None, rastro=True)
            elif 1 <= u < 1.8:
                ruim = self.vaza(s + .35)
                if ruim:
                    xx, yy = self.RX, self.RY - 20
                    tela.texto("X", xx, yy - 6, VERMELHO, tam=17, contorno=PRETO, centro=True)
                else:
                    ack(tela, self.RX, self.RY - 14, self.PX_, self.PY_ - 24, ease((u - 1) / .6), t)
        self.rot(tela, "MICRO-ONDAS", 40, 24, 60, 86, AMARELO)
        if t >= .5:
            tela.texto("2,45 GHZ", 70 if not VERTICAL else 160, 158 if not VERTICAL else 40, LARANJA, tam=17, contorno=PRETO, centro=True)
        perdas = sum(1 for s in self.saidas if s + .7 < t and self.vaza(s + .35))
        self.painel(tela, t, destaque=('freq',) if t >= 15.8 else (),
                    nota=[("FORNO: 2,45 GHZ", LARANJA), (f"PACOTES PERDIDOS: {perdas}", VERMELHO if perdas else ACO2)])
        self.vtxt(tela, f"PERDIDOS: {perdas}", VERMELHO if perdas else ACO3, y=4)

    def sons(self, fx):
        self.zumbido(fx, .3, 7.0, 110, .025)
        self.zumbido(fx, 8.0, 7.0, 110, .025)
        self.zumbido(fx, 16.0, 7.6, 110, .025)
        for k, s in enumerate(self.saidas):
            self.nota(fx, s, 79, .05, .03, .3)
            if self.vaza(s + .35): self.tique(fx, s + .7, 300, .12, .04, .3)
            else: self.bipe(fx, s + .7, 88, .02, .05, .3)


# ============================================================ 11 canais
class Canais(Cena):
    X1, PXM, BASE, ALT = 50, 3.0, 150, 66

    def cx(self, ch): return self.X1 + (ch - 1) * 5 * self.PXM

    def corcova(self, tela, ch, cor, cor2, cheio=False, fantasma=False, alt=None):
        c = self.cx(ch); hw = 10 * self.PXM
        alt = self.ALT if alt is None else alt
        prev = None
        for x in range(int(c - hw), int(c + hw) + 1):
            u = (x - c) / hw
            y = self.BASE - alt * max(0, math.cos(u * math.pi / 2)) ** 1.4
            if cheio and not fantasma:
                for yy in range(int(y) + 1, self.BASE):
                    if (x + yy) % 2 == 0: tela.px(x, yy, cor2)
            if fantasma:
                if x % 2 == 0: tela.px(x, y, cor)
            else:
                if prev is not None: tela.ret(x, min(prev, int(y)) - 1, 1, abs(prev - int(y)) + 3, PRETO)
                prev = int(y)
        if not fantasma:
            prev = None
            for x in range(int(c - hw), int(c + hw) + 1):
                u = (x - c) / hw
                y = int(self.BASE - alt * max(0, math.cos(u * math.pi / 2)) ** 1.4)
                if prev is not None: tela.ret(x, min(prev, y), 1, abs(prev - y) + 1, cor)
                prev = y

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        tela.ret(14, self.BASE, 280, 1, ACO3)
        tela.texto("FAIXA DE 2,4 GHZ", 156, 4, BRANCO, tam=17, contorno=PRETO, centro=True)
        n_vis = min(14, int(t / .45) + 1)
        tres = (1, 6, 11)
        cores = {1: CIANO, 6: AMARELO, 11: ROSA}
        respira = 1 + .04 * math.sin(t * 3)
        for ch in range(1, n_vis + 1):
            if t >= 15.4:
                if ch in tres:
                    self.corcova(tela, ch, cores[ch], cores[ch], cheio=True, alt=self.ALT * respira)
                else:
                    self.corcova(tela, ch, ACO1, ACO1, fantasma=True)
            elif 7.8 <= t:
                if ch == 1:
                    self.corcova(tela, ch, CIANO, CIANO, cheio=True)
                elif ch in (2, 3, 4):
                    self.corcova(tela, ch, VERMELHO, ERR1, cheio=True, alt=self.ALT * .9)
                else:
                    self.corcova(tela, ch, OND2, OND1)
            else:
                self.corcova(tela, ch, OND2, OND1, alt=self.ALT * (respira if ch == n_vis else 1))
            c = int(self.cx(ch))
            cor_n = (cores[ch] if (t >= 15.4 and ch in tres) else ACO3)
            tela.texto(str(ch), c, self.BASE + 4, cor_n, tam=9, contorno=PRETO, centro=True)
        if 7.8 <= t < 15.4:
            a, b = int(self.cx(1) - 30), int(self.cx(1) + 30)
            y = self.BASE - self.ALT - 10
            tela.ret(a, y, b - a, 1, BRANCO); tela.ret(a, y, 1, 4, BRANCO); tela.ret(b, y, 1, 4, BRANCO)
            tela.texto("20 MHZ", (a + b) // 2, y - 10, BRANCO, tam=9, contorno=PRETO, centro=True)
            a2, b2 = int(self.cx(1)), int(self.cx(2))
            tela.ret(a2, self.BASE + 14, b2 - a2, 1, AMARELO)
            tela.texto("5 MHZ", b2 + 4, self.BASE + 12, AMARELO, tam=9, contorno=PRETO)
            tela.texto("SE ATROPELAM!", int(self.cx(4)) + 30, 70, VERMELHO, tam=9, contorno=PRETO)
        if t >= 15.4:
            for ch in tres:
                c = int(self.cx(ch))
                roteador(tela, c - 12, 46, t + ch, .5, ativo=1)
                aneis(tela, c, 34, t + ch * .3, 20, 10, 26, cores[ch], cores[ch], esp=.5)
        if t >= 22.8:
            for k, (nome, n) in enumerate((("EUA", 11), ("EUROPA", 13), ("JAPÃO", 14))):
                y = 168 + k * 12
                if VERTICAL: continue
                tela.texto(nome, 6, y, ACO3, tam=9, contorno=PRETO)
                a = int(self.cx(1) - 4); b = int(self.cx(n) + 4)
                w = int((b - a) * ease((t - 22.8 - k * .4) / .6))
                if w > 0:
                    tela.ret(a, y + 1, w, 6, PRETO); tela.ret(a + 1, y + 2, max(0, w - 2), 4, VERDE)
                    tela.texto(str(n), a + w + 4, y, VERDE, tam=9, contorno=PRETO)
        nota = [("14 CANAIS, 5 MHZ", ACO3), ("CADA SINAL: 20 MHZ", ACO3)]
        if t >= 15.4: nota = [("SEM SE TOCAR:", ACO3), ("1, 6 E 11", AMARELO)]
        self.painel(tela, t, destaque=('freq',), nota=nota)
        self.vtxt(tela, "CANAIS 1, 6 E 11" if t >= 15.4 else "14 CANAIS", AMARELO, y=196)

    def sons(self, fx):
        for k in range(14): self.nota(fx, k * .45, 60 + k, .06, .03)
        self.zumbido(fx, 7.8, .25, 160, .04)
        for k, m in enumerate((72, 76, 79)): self.nota(fx, 15.4 + k * .25, m, .15, .045)


# ============================================================ 12 cada um na sua vez (CSMA/CA)
class Vez(Cena):
    XV = 110
    R = (170, 86)
    POS = dict(cel=(40, 40), note=(36, 130), tab=(120, 150), tv=(250, 34))
    COR = dict(cel=AMARELO, note=CIANO, tab=ROSA, tv=VERDE)

    def preparar(self):
        # (quem, início, fim, tipo, n) — tipo: 'dado', 'ack', 'col'
        E = []
        def dado(q, a, n=None, d=1.0, ack_=True):
            E.append((q, a, a + d, 'dado', n))
            if ack_: E.append((q, a + d + .1, a + d + .5, 'ack', n))
        dado('note', .5); dado('tv', 2.5); dado('note', 4.5); dado('tab', 6.5, d=1.5); dado('tv', 9.0, d=1.5)
        dado('note', 13.0, d=2.0); dado('tv', 16.0, d=1.0)
        dado('cel', 18.5, 1, d=1.2); dado('cel', 21.0, 2, d=1.2); dado('cel', 23.5, 3, d=1.2)
        dado('cel', 26.5, 4, d=1.2)
        E.append(('cel', 30.5, 31.7, 'dado', 5)); E.append(('tab', 30.5, 31.7, 'dado', None))
        E.append(('x', 30.9, 31.7, 'col', None))
        dado('cel', 34.0, 5, d=1.2)
        self.E = E
        # o que o celular "pensa" (estado) em cada trecho
        self.ESTADOS = [(0.0, "NA FILA", ACO3), (6.6, "ESCUTANDO", CIANO), (12.6, "SORTEOU: 4", LARANJA),
                        (15.5, "ESPERA: 3", LARANJA), (16.0, "PAUSA: OCUPADO", LARANJA),
                        (17.5, "ESPERA: 2", LARANJA), (18.0, "ESPERA: 1", LARANJA), (18.5, "FALANDO", AMARELO),
                        (19.7, "ESPERA O ACK", ACO3), (20.2, "RECEBIDO!", VERDE), (21.0, "FALANDO", AMARELO),
                        (22.2, "ESPERA O ACK", ACO3), (22.7, "RECEBIDO!", VERDE), (23.5, "FALANDO", AMARELO),
                        (24.7, "ESPERA O ACK", ACO3), (25.2, "RECEBIDO!", VERDE), (26.5, "FALANDO", AMARELO),
                        (27.7, "ESPERA O ACK", ACO3), (28.2, "RECEBIDO!", VERDE), (30.5, "FALANDO", AMARELO),
                        (31.7, "SEM ACK...", VERMELHO), (32.5, "SORTEOU: 2", LARANJA), (33.0, "ESPERA: 1", LARANJA),
                        (34.0, "DE NOVO", AMARELO), (35.2, "ESPERA O ACK", ACO3), (35.7, "RECEBIDO!", VERDE)]

    def ocupado(self, t):
        return any(a <= t < b for q, a, b, tp, n in self.E if tp != 'col')

    def estado(self, t):
        e = self.ESTADOS[0]
        for x in self.ESTADOS:
            if t >= x[0]: e = x
        return e

    def aparelho(self, tela, q, t):
        x, y = self.POS[q]
        if q == 'cel': celular(tela, x - 10, y - 18, 20, 36, t)
        elif q == 'note': notebook(tela, x - 18, y - 14, 36, 22, t, ativo=True)
        elif q == 'tab': tablet(tela, x - 13, y - 17, 26, 34, t)
        else: tv(tela, x - 24, y - 14, 48, 28, t)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H, :300] = FUNDO
        dither(tela, 4, 4, 292, 166, MAD1, MAD0)
        for x in range(4, 296, 24): tela.ret(x, 4, 1, 166, MAD0)
        tela.ret_vazado(3, 3, 294, 168, PRETO)
        rx, ry = self.R
        roteador(tela, rx - 24, ry, t, 1.0, ativo=1 if self.ocupado(t) else 0)
        for q in self.POS: self.aparelho(tela, q, t)
        # escutando: arcos entrando no celular
        nome, cor_e = self.estado(t)[1], self.estado(t)[2]
        cx, cy = self.POS['cel']
        if 6.6 <= t < 18.5:
            for k in range(3):
                u = ((t * 1.2) + k / 3) % 1
                r = 22 - u * 14
                for a in np.linspace(-.6, .6, 9):
                    tela.px(cx + 14 + math.cos(a) * r, cy + math.sin(a) * r, CIANO if u > .3 else FUNDO3)
            st = "OCUPADO" if self.ocupado(t) else "LIVRE"
            tela.texto(st, cx + 34, cy + 16, VERMELHO if st == "OCUPADO" else VERDE, tam=9, contorno=PRETO)
        # balão de estado do celular
        if not VERTICAL:
            w = tela.largura_texto(nome, 9) + 8
            tela.ret(cx + 14, cy - 30, w + 2, 13, PRETO); tela.ret(cx + 15, cy - 29, w, 11, FUNDO2)
            tela.texto(nome, cx + 19, cy - 27, cor_e, tam=9)
        # o que está no ar
        acks = 0
        for q, a, b, tp, n in self.E:
            if tp == 'col':
                if a <= t < b + .6:
                    u = (t - a) / .9
                    for k in range(10):
                        ang = k * .63 + t * 3
                        rr = 6 + u * 16
                        tela.ret(int(rx + math.cos(ang) * rr), int(ry - 18 + math.sin(ang) * rr), 2, 2,
                                 VERMELHO if k % 2 else CHAMA1)
                    tela.texto("COLISÃO!", rx, ry - 50, VERMELHO, tam=17, contorno=PRETO, centro=True)
                continue
            if q == 'x': continue
            x0, y0 = self.POS[q]
            if tp == 'ack' and t >= b and q == 'cel': acks += 1
            if not (a <= t < b): continue
            u = (t - a) / (b - a)
            if tp == 'dado':
                colide = any(tp2 == 'col' and a2 <= t + .4 for q2, a2, b2, tp2, n2 in self.E if a2 >= a and a2 < b)
                fim = .6 if colide else 1.0
                voo(tela, x0, y0, rx, ry - 14, ease(u) * fim, t, n, cor=self.COR[q] if q != 'cel' else AMARELO)
            else:
                ack(tela, rx, ry - 14, x0, y0, ease(u), t)
        if 24.6 <= t < 26.0:
            tela.texto("ACK = RECEBI!", rx, 150, VERDE, tam=17, contorno=PRETO, centro=True)
        # a linha do tempo do canal
        self.linha_tempo(tela, t)
        n_atual = max([n for q, a, b, tp, n in self.E if q == 'cel' and tp == 'dado' and t >= a] or [1])
        self.painel(tela, t, pacote=n_atual, destaque=('pacote',), estado=(nome, cor_e),
                    nota=[("CANAL 6", ACO3), (f"ACKS RECEBIDOS: {acks}", VERDE)])
        self.vtxt(tela, f"PACOTE Nº {n_atual}: {nome}", cor_e, y=196)

    def linha_tempo(self, tela, t):
        if VERTICAL: return
        y0, x0, x1 = 178, 64, 296
        tela.texto("O AR:", 8, y0 + 4, ACO3, tam=9, contorno=PRETO)
        tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, 20, PRETO)
        tela.ret(x0, y0, x1 - x0, 18, FUNDO2)
        janela = 8.0
        px_s = (x1 - x0) / janela
        for q, a, b, tp, n in self.E:
            if b < t - janela or a > t: continue
            xa = x1 - (t - a) * px_s; xb = x1 - (t - min(b, t)) * px_s
            xa = max(x0, xa)
            if xb <= xa: continue
            if tp == 'col':
                tela.ret(int(xa), y0, int(xb - xa) + 1, 18, VERMELHO); continue
            c = VERDE if tp == 'ack' else (self.COR[q] if q in self.COR else ACO2)
            yy = y0 + (12 if tp == 'ack' else 2)
            tela.ret(int(xa), yy, int(xb - xa) + 1, 4 if tp == 'ack' else 8, c)
        tela.ret(x1 - 1, y0 - 2, 2, 22, BRANCO)

    def sons(self, fx):
        for q, a, b, tp, n in self.E:
            if tp == 'dado': self.nota(fx, a, 79 if q == 'cel' else 72, .06, .03 if q == 'cel' else .02)
            elif tp == 'ack': self.bipe(fx, a, 91, .02 if q != 'cel' else .04, .06)
            elif tp == 'col': self.zumbido(fx, a, .35, 120, .05)
        for tt in (12.6, 15.5, 17.5, 18.0, 32.5, 33.0): self.tique(fx, tt, 1200, .04, .03)


# ============================================================ 13 a senha
class Senha(Cena):
    XV = 140
    PX_, PY_ = 30, 100
    RX, RY = 254, 104
    VX, VY = 144, 166                     # o vizinho

    def preparar(self):
        rng = np.random.default_rng(13)
        self.chave = ''.join('1' if b else '0' for b in rng.integers(0, 2, 16))
        self.bits = PACOTE_BITS[:16]
        self.ar = ''.join('1' if a != b else '0' for a, b in zip(self.bits, self.chave))
        self.saidas = [2.0 + k * 3.0 for k in range(10)]

    def linha_bits(self, tela, rot, y, bits, cor1, n=16, x0=70):
        tela.texto(rot, x0 - 6, y + 2, ACO3, tam=9, contorno=PRETO, centro='d')
        for k in range(16):
            x = x0 + k * 11
            v = bits[k] == '1' if k < n else None
            tela.ret(x - 1, y - 1, 11, 13, PRETO)
            if v is None:
                tela.ret(x, y, 9, 11, FUNDO2); continue
            tela.ret(x, y, 9, 11, cor1 if v else FUNDO3)
            tela.texto('1' if v else '0', x + 2, y + 2, PRETO if v else ACO2, tam=9)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cripto = t >= 7.8
        # as linhas de bits (em cima)
        if t < 22.8:
            self.linha_bits(tela, "BITS", 6, self.bits, AMARELO)
        if cripto and t < 22.8:
            n = int(clamp((t - 8.6) / 2.4) * 16)
            self.linha_bits(tela, "CHAVE", 22, self.chave, LATAO, n=int(clamp((t - 7.8) / .8) * 16))
            self.linha_bits(tela, "NO AR", 38, self.ar, ROSA, n=n)
            if 8.6 <= t < 11.2:
                xk = 70 + min(15, n) * 11 + 4
                tela.ret(int(xk) - 1, 4, 3, 48, BRANCO)
        # aparelhos
        celular(tela, self.PX_ - 14, self.PY_ - 26, 26, 50, t)
        roteador(tela, self.RX - 24, self.RY + 10, t, 1.0, ativo=1)
        celular(tela, self.VX - 12, self.VY - 20, 22, 40, t, tela_cor=ERR0 if t >= 15.4 else TEL0, wifi=None)
        self.rot(tela, "VIZINHO", 186, 182, self.VX + 10, self.VY, ACO3)
        aneis(tela, self.PX_ + 8, self.PY_ - 10, t, 50, 24, 150, OND2, OND1, esp=.5)
        # pacotes que saem: um vai para o roteador, uma cópia chega ao vizinho
        for k, s in enumerate(self.saidas):
            u = (t - s) / 1.2
            if 0 <= u < 1:
                emb = s >= 9.0
                bb = (self.ar if emb else self.bits)[:8]
                voo(tela, self.PX_ + 14, self.PY_ - 10, self.RX, self.RY - 4, ease(u), t, 1, bits=bb, emb=emb)
                voo(tela, self.PX_ + 14, self.PY_ - 10, self.VX, self.VY - 34, ease(u), t, None, bits=bb, emb=emb,
                    cor=ACO2, rastro=False)
        # o que cada um lê
        leu_emb = any(s >= 9.0 and s + 1.2 <= t for s in self.saidas)
        vt = "????????" if (leu_emb and t >= 12.0) else self.bits[:8]
        tela.texto(vt, self.VX - 1, self.VY - 32, VERMELHO if vt[0] == '?' else BRANCO, tam=9, centro=True,
                   contorno=PRETO)
        if leu_emb and t >= 12.0:
            cadeado(tela, self.RX + 18, self.RY - 30, 2, AMARELO, aberto=clamp((t - 15.4) / .4))
            tela.texto(self.bits[:8], self.RX, self.RY - 48, VERDE, tam=9, contorno=PRETO, centro=True)
            self.rot(tela, "TEM A CHAVE", 196, 70, self.RX + 18, self.RY - 26, VERDE)
            if not VERTICAL: tela.texto("SEM A CHAVE", self.VX - 18, self.VY - 4, VERMELHO, tam=9, contorno=PRETO,
                                        centro='d')
        if t >= 22.8 and not VERTICAL:
            for k, (a, b) in enumerate((("WPA2", "2004"), ("WPA3", "2018"))):
                x, y = 76 + k * 70, 12
                u = ease((t - 22.8 - k * .5) / .4)
                if u <= 0: continue
                tela.ret(x - 1, y - 1, 58, 30, PRETO); tela.ret(x, y, 56, 28, FUNDO2)
                tela.ret(x, y, 56, 1, AMARELO if k else ACO3)
                tela.texto(a, x + 28, y + 4, AMARELO if k else BRANCO, tam=17, contorno=PRETO, centro=True)
                tela.texto(b, x + 28, y + 19, ACO3, tam=9, contorno=PRETO, centro=True)
        nota = [("SEM CRIPTOGRAFIA", VERMELHO)] if not cripto else [("BITS + CHAVE = NO AR", ROSA)]
        if t >= 22.8: nota = [("WPA2: 2004", ACO3), ("WPA3: ANUNCIADO 2018", AMARELO)]
        self.painel(tela, t, nota=nota, estado=("CIFRADO", ROSA) if t >= 9.0 else None)
        self.vtxt(tela, "VIZINHO: ????????" if (leu_emb and t >= 12) else "TODOS RECEBEM", ROSA, y=196)

    def sons(self, fx):
        for s in self.saidas: self.nota(fx, s, 76, .05, .03)
        for k in range(16): self.tique(fx, 8.6 + k * .15, 1400 + k * 30, .03, .02)
        self.nota(fx, 15.4, 84, .2, .04)


# ============================================================ 14 para a internet
class Internet(Cena):
    def preparar(self):
        self.rx, self.ry = 64, 100
        self.mx, self.my = 156, 132
        self.gx, self.gy = 246, 76
        self.ciclo = 4.0

    def caminho(self, u):
        """u em [0, 1): celular -> roteador (rádio), roteador -> modem -> internet (cabo)."""
        pts = [(18, 40), (self.rx, self.ry - 18), (self.rx + 24, self.ry + 6), (self.mx - 20, self.my + 4),
               (self.mx + 20, self.my), (self.gx - 30, self.gy + 10)]
        segs = list(zip(pts, pts[1:]))
        Ls = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
        d = u * sum(Ls)
        for (a, b), L in zip(segs, Ls):
            if d <= L: return a[0] + (b[0] - a[0]) * d / L, a[1] + (b[1] - a[1]) * d / L, segs.index((a, b))
            d -= L
        return pts[-1][0], pts[-1][1], len(segs) - 1

    def globo(self, tela, t):
        gx, gy, r = self.gx, self.gy, 36
        tela.disco(gx, gy, r + 1, PRETO); tela.disco(gx, gy, r, AGU0)
        for k in range(-2, 3):
            tela.anel(gx, gy, r, AGU1, .6)
        for k in range(5):
            a = t * .4 + k * .63
            xx = gx + math.sin(a) * r * .9
            if math.cos(a) > 0:
                for yy in range(gy - r + 4, gy + r - 4, 3): tela.px(xx, yy, AGU2)
        for k in range(-2, 3): tela.ret(gx - r + 6, gy + k * 12, 2 * r - 12, 1, AGU1)
        for k in range(6):
            a = k * 1.05 + t * .3
            nx, ny = gx + math.cos(a) * r * .65, gy + math.sin(a) * r * .55
            tela.disco(nx, ny, 2.2, AMARELO if (k + int(t * 2)) % 3 == 0 else BRANCO)
        tela.texto("INTERNET", gx, gy + r + 6, BRANCO, tam=9, contorno=PRETO, centro=True)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        celular(tela, 6, 20, 22, 40, t)
        roteador(tela, self.rx - 24, self.ry, t, 1.0, ativo=1)
        bloco(tela, self.mx - 20, self.my - 10, self.mx + 20, self.my + 8, ACO1, ACO3, ACO0)
        tela.texto("MODEM", self.mx, self.my + 14, ACO3, tam=9, contorno=PRETO, centro=True)
        for k in range(3): tela.ret(self.mx - 14 + k * 6, self.my - 4, 2, 2, VERDE if (k + int(t * 5)) % 2 else ACO2)
        # cabos
        tela.linha(self.rx + 24, self.ry + 7, self.mx - 20, self.my + 5, PRETO)
        tela.linha(self.rx + 24, self.ry + 6, self.mx - 20, self.my + 4, ACO2)
        tela.linha(self.mx + 20, self.my + 1, self.gx - 30, self.gy + 11, PRETO)
        tela.linha(self.mx + 20, self.my, self.gx - 30, self.gy + 10, CIANO)
        self.globo(tela, t)
        self.rot(tela, "ROTEADOR", 20, 140, self.rx - 10, self.ry + 10, AMARELO)
        self.rot(tela, "CABO", 100, 150, (self.rx + self.mx) // 2, (self.ry + self.my) // 2 + 5, ACO3)
        # pacotes em fila
        for k in range(6):
            s = .3 + k * self.ciclo / 2
            u = (t - s) / self.ciclo
            if not (0 <= u < 1): continue
            x, y, seg = self.caminho(u)
            if seg == 0:
                pacote(tela, x, y, k + 1, t)
                aneis(tela, 18, 40, t, 40, 16, math.hypot(x - 18, y - 40), OND2, OND1, esp=.5)
            else:
                halo(tela, x, y, 7, CIANO, int(t * 8) % 2)
                pacote(tela, x, y, k + 1, t, brilho=False)
        if t >= 15.8:
            self.cartao(tela, t)
        self.painel(tela, t, destaque=('pacote',), nota=[("RÁDIO -> CABO", ACO3), ("-> INTERNET", CIANO)])

    def cartao(self, tela, t):
        u = ease((t - 15.8) / .5)
        x, y, w, h = 30, int(lerp(220, 34, u)), 240, 120
        escurecer(tela, 0, 0, 300, PALCO_H)
        tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
        tela.ret(x, y, w, h, FUNDO2)
        tela.ret(x, y, w, 1, AMARELO)
        tela.texto("VEJA TAMBÉM", x + 8, y + 6, AMARELO, tam=9, contorno=PRETO)
        # miniatura: celular, rota e mar
        mx, my, mw, mh = x + 8, y + 18, 80, 60
        tela.ret(mx - 1, my - 1, mw + 2, mh + 2, PRETO)
        tela.ret(mx, my, mw, mh, AGU0)
        dither(tela, mx, my + mh // 2, mw, mh // 2, AGU0, FUNDO2)
        tela.ret(mx, my + mh - 14, 24, 14, PLN0); tela.ret(mx + mw - 20, my, 20, 22, PLN0)
        for k in range(20):
            a = k / 19
            tela.px(mx + 10 + a * 60, my + mh - 10 - a * 40 - math.sin(a * 3) * 6, AMARELO)
        uu = (t * .4) % 1
        pacote(tela, mx + 10 + uu * 60, my + mh - 10 - uu * 40 - math.sin(uu * 3) * 6, None, t, brilho=False)
        tela.texto("A JORNADA DE UMA", x + 96, y + 26, BRANCO, tam=9, contorno=PRETO)
        tela.texto("MENSAGEM DE", x + 96, y + 38, BRANCO, tam=9, contorno=PRETO)
        tela.texto("CELULAR", x + 96, y + 50, BRANCO, tam=17, contorno=PRETO)
        tela.texto("EPISÓDIO 7", x + 96, y + 70, ACO3, tam=9, contorno=PRETO)
        tela.texto("NOSSO MUNDO PIXEL", x + 8, y + h - 14, ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(6):
            s = .3 + k * self.ciclo / 2
            self.nota(fx, s, 76, .05, .03)
            self.tique(fx, s + self.ciclo * .3, 900, .05, .02)
        self.nota(fx, 15.8, 79, .25, .05)


# ============================================================ 15 resumo
class Resumo(Cena):
    PASSOS = ["ANTENA", "ONDA", "QAM", "PAREDE", "VEZ", "ACK", "SENHA"]
    LUZ = [0.5, 2.0, 4.5, 9.8, 12.0, 15.0, 19.8]

    def icone(self, tela, k, x, y, t, aceso):
        c = AMARELO if aceso else ACO1
        if k == 0:
            tela.ret(x - 2, y - 14, 5, 28, PRETO); tela.ret(x - 1, y - 13, 3, 26, ACO2 if aceso else ACO0)
            for j in range(4): tela.disco(x, y - 9 + j * 6 - 3 * math.sin(t * 3) * aceso, 1.3, CIANO if aceso else ACO1)
        elif k == 1:
            onda(tela, x - 14, x + 15, y, 8 if aceso else 4, 14, fase=t * 6 * aceso, cor=OND2 if aceso else ACO1)
        elif k == 2:
            for (I, Q) in QAM16.values():
                tela.ret(int(x + I * 3) - 1, int(y - Q * 3) - 1, 2, 2, OND3 if aceso else ACO1)
            if aceso:
                I, Q = QAM16[PACOTE_SIMB[int(t * 2) % 8]]
                tela.ret(int(x + I * 3) - 2, int(y - Q * 3) - 2, 4, 4, AMARELO)
        elif k == 3:
            parede_concreto(tela, x - 3, y - 14, 6, 28)
            barras_sinal(tela, x + 6, y - 6, 2 if aceso else 0, h=12, cor=AMARELO)
        elif k == 4:
            tela.ret(x - 14, y - 6, 8, 14, PRETO); tela.ret(x - 13, y - 5, 6, 12, AMARELO if aceso else ACO1)
            tela.ret(x + 6, y - 6, 8, 14, PRETO); tela.ret(x + 7, y - 5, 6, 12, ACO2)
            if aceso and int(t * 2) % 2: tela.texto("1", x - 3, y - 4, AMARELO, tam=9)
        elif k == 5:
            ack(tela, x, y, x, y, 0, t if aceso else 0, cor=VERDE if aceso else ACO1)
        else:
            cadeado(tela, x - 8, y - 2, 2, AMARELO if aceso else ACO1)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        xs = [24 + k * 42 for k in range(7)]
        y = 92
        tela.ret(xs[0], y, xs[-1] - xs[0], 1, FUNDO3)
        n_aceso = sum(1 for a in self.LUZ if t >= a)
        for k, x in enumerate(xs):
            aceso = k < n_aceso
            tela.ret(x - 19, y - 22, 39, 44, PRETO)
            tela.ret(x - 18, y - 21, 37, 42, FUNDO2 if aceso else FUNDO)
            if aceso: tela.ret(x - 18, y - 21, 37, 1, AMARELO)
            self.icone(tela, k, x, y, t, aceso)
            tela.texto(self.PASSOS[k], x, y + 28, AMARELO if aceso else ACO2, tam=9, contorno=PRETO, centro=True)
        # o pacote andando pelos passos
        if n_aceso:
            alvo = xs[min(6, n_aceso - 1)]
            ultimo = self.LUZ[min(6, n_aceso - 1)]
            ant = xs[max(0, n_aceso - 2)]
            u = ease((t - ultimo) / .8)
            px = lerp(ant, alvo, u) if n_aceso > 1 else alvo
            pacote(tela, px, y - 44, 1, t, s=1)
        # a viagem inteira, embaixo: celular -> roteador -> internet
        yl = 176
        tela.ret(30, yl, 222, 1, FUNDO3)
        celular(tela, 12, yl - 18, 18, 32, t)
        roteador(tela, 126, yl - 4, t, .6, ativo=1)
        tela.disco(264, yl, 13, PRETO); tela.disco(264, yl, 12, AGU0)
        for k in (-6, 0, 6): tela.ret(254, yl + k, 21, 1, AGU1)
        tela.texto("INTERNET", 264, yl + 16, ACO3, tam=9, contorno=PRETO, centro=True)
        uu = clamp(n_aceso / 7 * .5 + (.5 * ease((t - 24.0) / 3.0) if t >= 24.0 else 0))
        px2 = lerp(30, 250, uu)
        for k in range(1, 30):
            xx = px2 - k * 2
            if xx < 30: break
            tela.px(xx, yl + 3 * math.sin(xx / 3 - t * 10) * (1 if xx < 150 else 0), OND2 if xx < 150 else CIANO)
        pacote(tela, px2, yl - 12, 1, t, brilho=False)
        if t >= 24.0:
            tela.texto("E O PACOTE Nº 1 CHEGOU", 152, 136, VERDE, tam=17, contorno=PRETO, centro=True)
        self.painel(tela, t, estado=("ENTREGUE", VERDE) if t >= 24.0 else None, viagem=1.0,
                    nota=[("ELÉTRONS -> ONDA", ACO3), ("-> BITS -> ACK", ACO3)])

    def sons(self, fx):
        for k, a in enumerate(self.LUZ): self.nota(fx, a, 72 + [0, 2, 4, 7, 9, 12, 14][k], .1, .04)
        self.bipe(fx, 24.0, 91, .05)


# ============================================================ 16 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            grade_fundo(tela, W, t)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            icone_wifi(tela, W // 2, 170, 60, 1 + int(t * 2) % 3, CIANO, FUNDO3)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, casa=Casa, antena=Antena, frequencia=Frequencia, bits=Bits, qam=Qam,
             pontos=Pontos, distancia=Distancia, paredes=Paredes, microondas=Microondas, canais=Canais, vez=Vez,
             senha=Senha, internet=Internet, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep24_motor as EP
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
