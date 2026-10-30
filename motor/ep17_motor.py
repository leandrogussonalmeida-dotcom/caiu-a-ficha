#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep17 — Como funciona a fechadura e a chave (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (os pinos batendo, o rotor girando, a
                          lingueta), nos mesmos instantes do desenho
A fechadura inteira anda por duas variáveis por capítulo: `o(t)`, quanto a
chave está para fora (0 = toda dentro), e `theta(t)`, o giro do rotor. A altura
de cada pino sai da geometria da chave (`ep17_desenho.Cilindro.pilha`) e o
rotor só gira se todo vão está exatamente na linha de corte: o desenho
recusa (AssertionError) um giro com a chave errada, e `checar()` confere a
geometria em números antes de qualquer quadro.

No capítulo `batida` (house, 120 BPM, compasso de 2 s) a chave lisa sai até o
dente da vez ficar na frente do esmeril (batida 1), o dente é cortado (batida
2), ela volta (batida 3) e o pino daquele dente cai na linha exatamente na
batida 4: PINOS NO LUGAR sobe 1 por compasso.

    python3 ep17_motor.py <saida.mp4>                   # o episódio inteiro
    python3 ep17_motor.py <saida.mp4> certa batida      # só esses capítulos (teste)
    python3 ep17_motor.py --folha <saida.png> [ids]     # quadros por capítulo (FR=.3,.8)
"""
import math, os, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import pixelengine as PX
import ep17_desenho as D
from ep17_desenho import (Cilindro, Caixa, TrincoCima, Egipcia, Mascara, pintar_tela, brilho, fio, rotulo, barra,
                          seta, escurecer, fundo_bancada, rot_pts, ret_pts, tetra_frente, porta, mola,
                          CERTA, ERRADA, MESTRA, LISA)
import ritmo_marca as RM
import idioma as I
from ep17_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2617, 45
GANHO_MUSICA = -10.0          # trilha baixa: o clique dos pinos e o texto mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 304                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
XV = 150                      # centro do recorte vertical (x 60..240)


def milhar(n):
    return I.milhar(int(n))


def novo_cil(mestra=None):
    """Par de cilindros: o largo (vídeo) e o compacto (cortes verticais)."""
    a, b = Cilindro(40, 36), Cilindro(62, 26)
    if mestra:
        a.set_pinos(CERTA, mestra); b.set_pinos(CERTA, mestra)
    return a, b


def rampa(t, a, b, v0, v1, f=ease):
    """v0 antes de a, v1 depois de b, `f` no meio."""
    if t <= a: return v0
    if t >= b: return v1
    return v0 + (v1 - v0) * f((t - a) / (b - a))


def suave2(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (u * 6 - 15) + 10)


# ------------------------------------------------------------ som
def tique(f=3000.0, dur=.03, dec=.006):
    """Um "tic" de seno curtinho (sem ruído: o clique de ruído estoura o pico)."""
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    env = np.minimum(1.0, tt / .003) * np.exp(-tt / dec)      # ataque de 3 ms: o AAC não estoura o pico
    y = (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 1.5 * tt) + .3 * np.sin(2 * np.pi * f * .5 * tt)) * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def baque(f=80.0, dur=.18):
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    y = np.sin(2 * np.pi * (f * tt + 30 * (1 - np.exp(-tt / .03)))) * np.minimum(1, tt / .006) * np.exp(-tt / .05)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def esmeril(dur=.42):
    """O esmeril cortando o dente: senos desafinados com tremido (sem ruído)."""
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    y = sum(np.sin(2 * np.pi * f * tt + k) for k, f in enumerate((1210, 1790, 2430, 3110)))
    y = y * (.6 + .4 * np.sin(2 * np.pi * 47 * tt)) * np.minimum(1, tt / .02) * np.minimum(1, (dur - tt) / .06)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def giro_som(dur=.4):
    """O rotor girando: uma catraquinha de tiques fracos."""
    sr = LG.SR
    out = np.zeros(int(dur * sr) + 2000, np.float32)
    k = 0
    while k * .045 < dur:
        s = tique(1500 + 200 * (k % 2), .02, .004)
        i = int(k * .045 * sr)
        out[i:i + len(s)] += s * .6
        k += 1
    return out / (np.abs(out).max() + 1e-9)


def cliques_pinos(C, seg_de, o_de, t0, t1, dt=1 / 240.0):
    """Instantes em que algum pino termina de descer (bate na chave ou no
    batente) depois de cair 2 px ou mais, e o tamanho da queda."""
    ts = np.arange(t0, t1, dt)
    if len(ts) < 3: return []
    ys = np.array([[C.ponta(seg_de(t), i, o_de(t)) for i in range(5)] for t in ts])
    ev = []
    for i in range(5):
        y = ys[:, i]
        desce = False; y_ini = y[0]
        for k in range(1, len(y)):
            if y[k] > y[k - 1] + 1e-6:
                if not desce: desce, y_ini = True, y[k - 1]
            elif desce:
                if y[k - 1] - y_ini >= 2: ev.append((float(ts[k - 1]), i, float(y[k - 1] - y_ini)))
                desce = False
    return sorted(ev)


def faixa_luz(tela, x, y0, y1, cor, larg=5):
    """Reflexo que corre pela peça: faixa inclinada em xadrez, só sobre a
    peça (não pinta o fundo)."""
    for y in range(int(y0), int(y1)):
        for dx in range(larg):
            xx = int(x + dx - (y - y0) * .3)
            if 0 <= xx < W and 0 <= y < PALCO_H and (xx + y) % 2 == 0 and tela.buf[y, xx] > TRACO:
                tela.buf[y, xx] = cor


# ------------------------------------------------------------ painel e rótulos
def etiqueta(tela, txt, x, y, ax, ay, cor=AMARELO, tam=9, direita=False):
    """Rótulo com fio até a peça. `direita`: o texto termina em x."""
    if VERTICAL: return
    w = tela.largura_texto(txt, tam)
    xt = x - w if direita else x
    rotulo(tela, txt, xt, y, cor, tam)
    hy = y + (3 if tam == 9 else 7)
    x0 = xt - 3
    if ax > xt + w: x0 = xt + w + 3
    fio(tela, x0, hy, ax, ay, cor)


def titulo_painel(tela, l1, l2=None, cor=BRANCO, cor2=AMARELO, y=8):
    if VERTICAL: return
    tela.texto(l1, PX0, y, cor, tam=17, contorno=PRETO)
    if l2: tela.texto(l2, PX0, y + 18, cor2, tam=17, contorno=PRETO)


def hud_vertical(tela, linhas, x=XV):
    """No Short o painel some: uma tarja curta no alto do recorte."""
    if not VERTICAL: return
    for j, (s, cor) in enumerate(linhas):
        w = tela.largura_texto(s, 9) + 10
        painel(tela, x - w // 2, 2 + j * 15, w, 13, borda=cor)
        tela.texto(s, x, 5 + j * 15, cor, tam=9, centro=True)


def placar(tela, lugar, estado=None, y=30, rot='PINOS NO LUGAR'):
    """O placar do protagonista: k DE 5, as 5 luzes e o estado do rotor."""
    k = sum(lugar)
    if VERTICAL:
        linhas = [(f"{rot} {k} DE 5", VERDE if k == 5 else AMARELO)]
        if estado: linhas.append(estado)
        hud_vertical(tela, linhas)
        return
    painel(tela, PX0 - 6, y, 172, 64, borda=VERDE if k == 5 else TRACO)
    tela.texto(rot, PX0 + 2, y + 6, ACO3, tam=9, contorno=PRETO)
    tela.texto(f"{k} DE 5", PX0 + 2, y + 18, VERDE if k == 5 else AMARELO, tam=26, contorno=PRETO)
    for i, ok in enumerate(lugar):
        x = PX0 + 106 + i * 11
        tela.ret(x, y + 22, 9, 14, PRETO)
        tela.ret(x + 1, y + 23, 7, 12, VERDE if ok else FUNDO2)
        if ok: tela.ret(x + 1, y + 23, 7, 1, BRANCO)
    if estado:
        s, cor = estado
        tela.texto(s, PX0 + 2, y + 48, cor, tam=9, contorno=PRETO)


def est_rotor(C, seg, o, theta, travou=False):
    if theta > 1: return ('ROTOR: GIRANDO', VERDE)
    if seg is not None and C.pode_girar(seg, o): return ('ROTOR: LIVRE PARA GIRAR', VERDE)
    if travou: return ('ROTOR: TRAVADO!', VERMELHO)
    return ('ROTOR: TRAVADO', ACO3)


def inset(tela, C, i, seg, o, theta, y=104, cy=160, rot='DE FRENTE', came=True, ix=PX0 + 96):
    """Vista de frente pequena no painel (corte pela pilha i)."""
    if VERTICAL: return
    tela.texto(rot, PX0, y, ACO3, tam=9, contorno=PRETO)
    tela.texto(f"PILHA {i + 1}", PX0, y + 11, ACO2, tam=9, contorno=PRETO)
    C.desenhar_frente(tela, ix, cy, .62, i, seg, o, theta, came=came)


def batidas(tela, t, spb, x=PX0, y=8, cor=CIANO):
    """4 quadradinhos do compasso, o da batida atual aceso."""
    if VERTICAL: return
    b = int(t / spb) % 4
    for j in range(4):
        xx = x + j * 22
        tela.ret(xx, y, 18, 14, cor if j == b else FUNDO2)
        tela.ret_vazado(xx, y, 18, 14, cor)
        tela.texto(str(j + 1), xx + 6, y + 3, PRETO if j == b else cor, tam=9)


class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.spb = 60.0 / cap['bpm']
        self.L = trilha.L
        self.CL, self.CC = novo_cil()
        self.preparar()

    @property
    def C(self):
        return self.CC if VERTICAL else self.CL

    def fora(self, C=None):
        C = C or self.C
        return C.u_tip + C.x0 + 4

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    # a chave e o giro deste capítulo (cada cena diz os seus)
    def seg(self, t): return CERTA
    def o(self, t, C=None): return 0.0
    def theta(self, t): return 0.0

    def sons_pinos(self, fx, t0=0.0, t1=None, ganho=.16, C=None):
        C = C or self.CL
        t1 = self.dur if t1 is None else t1
        for t, i, q in cliques_pinos(C, self.seg, lambda tt: self.o(tt, C), t0, t1):
            fx.put(tique(2300 + 180 * i, .03, .005), self.t0 + t, ganho * min(1.0, .4 + q / 12), -.4 + .2 * i)


# ============================================================ gancho
class Gancho(Cena):
    def o(self, t, C=None):
        f = self.fora(C)
        if t < 8.6: return rampa(t, .3, 3.3, f, 0.0, suave)
        return rampa(t, 8.6, 11.0, 0.0, f, suave)

    def theta(self, t):
        if t < 7.5: return rampa(t, 3.8, 5.0, 0.0, 90.0, suave)
        return rampa(t, 7.5, 8.3, 90.0, 0.0, suave)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        o, th = self.o(t), self.theta(t)
        C.desenhar(tela, CERTA, o, th, linha=th > 0 or (o == 0))
        lugar = C.no_lugar(CERTA, o)
        if th > 0:
            for x in range(C.x0, C.xp1, 3):
                if (x // 3 + int(t * 20)) % 4 == 0: tela.px(x, C.Y_S, AMARELO)
        placar(tela, lugar, est_rotor(C, CERTA, o, th))
        if VERTICAL: return
        titulo_painel(tela, 'SÓ A CHAVE', None, BRANCO, y=8)
        inset(tela, C, 1, CERTA, o, th)

    def sons(self, fx):
        self.sons_pinos(fx, 0, 8.4, .14)
        fx.put(fx.sino(81, .7), self.t0 + 3.3, .14)
        fx.put(giro_som(1.1), self.t0 + 3.9, .12)
        fx.put(baque(110, .15), self.t0 + 5.0, .16)
        fx.put(giro_som(.7), self.t0 + 7.6, .1)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.CL
        # a chave atravessa a tela devagar, por baixo do título
        C.desenhar_chave(tela, CERTA, 300 - t * 60, dy=34)
        n = int(t / .045)
        l1, l2 = "COMO FUNCIONA A", "FECHADURA E A CHAVE"
        larg = tela.largura_texto(l1, 17)
        tela.texto(l1[:n], W // 2 - larg // 2, 34, BRANCO, tam=17, contorno=PRETO, sombra=TRACO)
        larg2 = tela.largura_texto(l2, 26)
        tam2 = 26 if larg2 <= 440 else 17
        larg2 = tela.largura_texto(l2, tam2)
        tela.texto(l2[:max(0, n - 15)], W // 2 - larg2 // 2, 56, AMARELO, tam=tam2, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", W // 2, 96, CIANO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k in range(5):
                x = W // 2 - 50 + k * 22
                on = t > 2.0 + k * .3
                tela.ret(x, 120, 14, 14, PRETO)
                tela.ret(x + 1, 121, 12, 12, VERDE if on else FUNDO2)
                tela.texto(str(k + 1), x + 4, 123, PRETO if on else ACO1, tam=9)

    def sons(self, fx):
        for k in range(5):
            fx.put(tique(2300 + 180 * k, .03, .006), self.t0 + 2.0 + k * .3, .2)
        fx.put(fx.sino(81, .8), self.t0 + 3.5, .12)


# ============================================================ a porta
class Porta(Cena):
    CIL = (196, 122)

    def preparar(self):
        self.tmp = PX.Tela(W, H, paleta=LG.PAL)

    def giro_chave(self, t):
        return rampa(t, 9.0, 12.0, 0.0, 90.0, suave)

    def raio_x(self, t):
        return rampa(t, 8.0, 9.0, 0.0, 1.0) if t < 16 else 1.0

    def desenhar_porta(self, tela, t):
        fundo_bancada(tela)
        cx, cy = self.CIL
        porta(tela, 70, 12, 150, 196, self.CIL)
        # o batente à direita da porta
        Mk = Mascara(); Mk.ret(222, 2, 14, 206)
        pintar_tela(tela, Mk, 'madeira')
        g = self.giro_chave(t)
        # raio X: a caixa da fechadura dentro da porta
        rx = self.raio_x(t)
        if rx > 0:
            antes = tela.buf.copy()
            Mk = Mascara(); Mk.ret(150, 70, 66, 106)
            pintar_tela(tela, Mk, 'placa', brilho=False)
            Mk = Mascara(); Mk.ret(214, 64, 6, 118)
            pintar_tela(tela, Mk, 'latao')
            # trinco (em cima, na altura da maçaneta) e lingueta (embaixo)
            Mk = Mascara(); Mk.ret(180, 84, 48, 9)
            pintar_tela(tela, Mk, 'latao')
            d = 14 * g / 90.0
            Mk = Mascara(); Mk.ret(170 + d, 148, 50 + 0, 12)
            pintar_tela(tela, Mk, 'aco')
            tela.disco(cx, cy + 4, 8, ACO2); tela.disco(cx, cy + 4, 7, LATAO)
            yy, xx = np.mgrid[0:H, 0:W]
            keep = ((xx + yy) % 2 == 0) & (rx < 1)
            tela.buf[keep] = antes[keep]
        # a chave (vista de frente): chega, entra e gira
        u = ease(min(1.0, max(0.0, (t - .5) / 4.0)))
        kx = cx + (1 - u) * 60
        ky = cy + 4 + (1 - u) * 40
        s = .6 + .4 * u
        a = g
        Mk = Mascara()
        pts = rot_pts([(kx - 9 * s, ky - 30 * s), (kx + 9 * s, ky - 30 * s), (kx + 9 * s, ky - 6 * s), (kx + 3 * s, ky - 2 * s),
                       (kx - 3 * s, ky - 2 * s), (kx - 9 * s, ky - 6 * s)], kx, ky, a)
        poligono(Mk, pts, 1)
        pintar_tela(tela, Mk, 'chave')
        h = rot_pts([(kx, ky - 22 * s)], kx, ky, a)[0]
        tela.disco(h[0], h[1], 3 * s, FUNDO)
        return rx

    def desenhar(self, tela, t, tg):
        cx, cy = self.CIL
        rx = self.desenhar_porta(tela, t)
        if 1.0 < t < 16 and not VERTICAL:
            etiqueta(tela, 'MAÇANETA', 8, 40, 162, 88, AMARELO)
            etiqueta(tela, 'CILINDRO', 8, 150, cx - 8, cy + 8, AMARELO)
        if rx >= 1 and t < 16 and not VERTICAL:
            etiqueta(tela, 'TRINCO', 240, 66, 222, 88, CIANO)
            etiqueta(tela, 'LINGUETA', 240, 184, 214 + 14 * self.giro_chave(t) / 90.0, 154, CIANO)
        # zoom: um círculo cresce no cilindro e mostra o corte
        if t >= 16.0:
            r = 300 * suave((t - 16.0) / 3.0)
            T = self.tmp
            fundo_bancada(T)
            C = self.C
            o = rampa(t, 19.0, 24.0, self.fora() + 80, self.fora() - 20, suave)
            C.desenhar(T, CERTA, o, 0.0)
            yy, xx = np.mgrid[0:PALCO_H, 0:W]
            m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
            if not VERTICAL: m &= xx < PX0 - 8
            tela.buf[:PALCO_H][m] = T.buf[:PALCO_H][m]
            if r < 280:
                tela.anel(cx, cy, r, AMARELO, 1.5)
            if t > 20 and not VERTICAL:
                etiqueta(tela, 'CILINDRO EM CORTE', 120, 190, C.X[2], C.Y_PB + 6, AMARELO)
        if VERTICAL:
            hud_vertical(tela, [('A FECHADURA', AMARELO)])
            return
        titulo_painel(tela, 'NA PORTA', None, BRANCO, y=8)
        itens = [('CILINDRO', AMARELO, 1.0), ('MAÇANETA', AMARELO, 2.0), ('LINGUETA', CIANO, 8.5),
                 ('TRINCO', CIANO, 9.5)]
        for j, (txt, cor, ta) in enumerate(itens):
            if t < ta: continue
            u = ease((t - ta) / .4)
            x = int(PX0 + (1 - u) * 160)
            y = 36 + j * 28
            painel(tela, x - 6, y, 160, 22, borda=cor)
            tela.ret(x, y + 7, 8, 8, cor)
            tela.texto(txt, x + 14, y + 3, cor, tam=17, contorno=PRETO)
        if t >= 16:
            tela.texto('POR DENTRO DO', PX0, 156, ACO3, tam=9, contorno=PRETO)
            tela.texto('CILINDRO...', PX0, 168, BRANCO, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(tique(1800, .04), self.t0 + 4.5, .2)
        fx.put(giro_som(1.2), self.t0 + 9.5, .12)
        fx.put(baque(120, .15), self.t0 + 11.9, .2)
        fx.put(fx.sino(76, .9), self.t0 + 16.0, .1)


# ============================================================ peças
PECAS = [('corpo', 'CORPO', LATAO), ('rotor', 'ROTOR', ACO3), ('pinos', 'PINOS', AMARELO),
         ('contra', 'CONTRAPINOS', MISTURA), ('molas', 'MOLAS', ACO4), ('linha', 'LINHA DE CORTE', CIANO)]


class Pecas(Cena):
    def preparar(self):
        self.slot = self.dur / len(PECAS)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        k_at = min(len(PECAS) - 1, int(t / self.slot))
        vis, desl = set(), {}
        for k, (nome, rot, cor) in enumerate(PECAS):
            tk = k * self.slot
            if t >= tk:
                vis.add(nome)
                u = (t - tk) / .7
                if u < 1:
                    if nome == 'rotor':
                        desl['rotor_x'] = int(-300 * (1 - ease(u)))
                    elif nome != 'linha':
                        y = -180 * (1 - u) ** 2 if u < .75 else -4 * math.sin((u - .75) / .25 * math.pi)
                        desl[nome] = int(y)
        C.desenhar(tela, None, 0.0, 0.0, vis=vis, desl=desl, linha=False)
        nome, rot, cor = PECAS[k_at]
        A = C.ancoras()
        # luz que corre pela peça da vez (movimento contínuo)
        if t - k_at * self.slot > .7:
            u = ((t - k_at * self.slot) * .45) % 1.0
            if nome == 'linha':
                for x in range(C.x0 - 6, C.xp1 + 8, 4):
                    tela.ret(x, C.Y_S, 2, 1, CIANO)
                xs = C.x0 + (C.xp1 - C.x0) * u
                brilho(tela, xs, C.Y_S, 10, CIANO, 1.0)
            else:
                ax, ay = A[{'pinos': 'pino', 'contra': 'contra', 'molas': 'mola'}.get(nome, nome)]
                if nome == 'corpo':
                    faixa_luz(tela, C.x0 + (C.xp1 - C.x0) * u, C.Y_CT - 8, C.Y_PB + 10, CHAMA0)
                if nome == 'rotor':
                    faixa_luz(tela, C.x0 + (C.xp1 - C.x0) * u, C.Y_S, C.Y_PB, BRANCO)
                if nome in ('pinos', 'contra', 'molas'):
                    i = int(u * 5) % 5
                    b = C.pilha(None, i, 0)
                    yy = {'pinos': (b[0] + b[1]) / 2, 'contra': (b[-2] + b[-1]) / 2,
                          'molas': (C.Y_CT + b[-1]) / 2}[nome]
                    brilho(tela, C.X[i], yy, 12, AMARELO, .9)
                    tela.ret_vazado(C.X[i] - 7, int(yy) - 3, 15, 7, AMARELO) if int(t * 4) % 2 else None
        if VERTICAL:
            hud_vertical(tela, [(rot, AMARELO)])
            return
        if t - k_at * self.slot > .7:
            pos = {'corpo': (8, 14), 'rotor': (8, 186), 'pinos': (8, 186), 'contra': (8, 14), 'molas': (8, 14),
                   'linha': (8, 82)}[nome]
            ax, ay = A[{'pinos': 'pino', 'contra': 'contra', 'molas': 'mola'}.get(nome, nome)]
            etiqueta(tela, rot, pos[0], pos[1], ax, ay, AMARELO)
        titulo_painel(tela, 'AS PEÇAS', None, BRANCO, y=8)
        for k, (nm, rt, cr) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 34 + k * 24
            at = k == k_at
            painel(tela, PX0 - 6, y, 172, 20, borda=cr if at else TRACO)
            tela.ret(PX0, y + 6, 8, 8, cr)
            tela.texto(rt, PX0 + 14, y + (3 if at else 6), AMARELO if at else ACO2, tam=17 if at else 9, contorno=PRETO)

    def sons(self, fx):
        for k in range(len(PECAS)):
            t = self.t0 + k * self.slot + .5
            fx.put(baque(140 + 20 * k, .12), t, .2)
            fx.put(fx.sino(74 + k * 2, .5), t, .07)


# ============================================================ sem chave
class SemChave(Cena):
    def seg(self, t): return CERTA if t < 4.0 else None

    def o(self, t, C=None):
        return rampa(t, .3, 3.6, 0.0, self.fora(C), suave)

    def tentativas(self):
        return [16.6 + 2.4 * k for k in range(3)]

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        seg, o = self.seg(t), self.o(t)
        C.desenhar(tela, seg, o, 0.0, linha=t > 4.0, marcar=t > 4.0, fase=t * 6)
        foco = None
        if 7.8 <= t < 15.6:
            foco = int((t - 7.8) / 1.56) % 5
            b = C.pilha(None, foco, 0)
            brilho(tela, C.X[foco], C.Y_S, 14, VERMELHO, 1.0)
            tela.ret_vazado(C.X[foco] - 7, int(b[-1]) - 2, 15, int(b[-2] - b[-1]) + 4, AMARELO)
        travou = any(0 <= t - a < .5 for a in self.tentativas())
        if travou:
            for i in range(5):
                brilho(tela, C.X[i], C.Y_S, 10, VERMELHO, 1.0)
        lugar = C.no_lugar(seg, o) if seg else [False] * 5
        placar(tela, lugar, est_rotor(C, seg, o, 0.0, travou))
        if VERTICAL: return
        if 7.8 <= t < 15.6:
            b = C.pilha(None, foco, 0)
            etiqueta(tela, 'CONTRAPINO ATRAVESSADO', 8, 186, C.X[foco], (b[-2] + C.Y_S) / 2 + 2, VERMELHO)
        titulo_painel(tela, 'SEM CHAVE', None, BRANCO, y=8)
        i = foco if foco is not None else 1
        inset(tela, C, i, seg, o, 0.0)
        if t >= 15.8:
            # seta curva: alguém tenta girar
            cx, cy = PX0 + 96, 160
            for a in self.tentativas():
                if 0 <= t - a < .8:
                    for k in range(14):
                        ang = math.radians(-60 + k * 6)
                        tela.px(cx + math.cos(ang) * 34, cy + math.sin(ang) * 34, AMARELO)
                    seta(tela, int(cx + math.cos(math.radians(24)) * 34), int(cy + math.sin(math.radians(24)) * 34), 0, 1, AMARELO, 4)
                    if t - a > .25:
                        tela.texto('NÃO GIRA!', PX0, 186, VERMELHO, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.sons_pinos(fx, 0, 4.2, .15)
        for a in self.tentativas():
            fx.put(baque(70, .2), self.t0 + a + .25, .35)
            fx.put(tique(900, .05, .01), self.t0 + a + .25, .12)


# ============================================================ chave errada
class Errada(Cena):
    def seg(self, t): return ERRADA

    def o(self, t, C=None):
        return rampa(t, .5, 6.5, self.fora(C), 0.0, suave)

    def tentativas(self):
        return [23.6 + 2.0 * k for k in range(3)]

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        o = self.o(t)
        foco = 1 if 7.8 <= t < 15.6 else (3 if 15.8 <= t < 22.8 else None)
        C.desenhar(tela, ERRADA, o, 0.0, linha=t > 6.5, marcar=t > 6.5, fase=t * 6,
                   cortes_brilho={foco: .6 + .4 * math.sin(t * 6)} if foco is not None else None)
        travou = any(0 <= t - a < .5 for a in self.tentativas())
        if foco is not None:
            b = C.pilha(ERRADA, foco, o)
            k = 0 if foco == 1 else len(b) - 2
            tela.ret_vazado(C.X[foco] - 7, int(b[k + 1]) - 2, 15, int(b[k] - b[k + 1]) + 4, AMARELO)
        if travou:
            for i in (1, 3):
                brilho(tela, C.X[i], C.Y_S, 12, VERMELHO, 1.0)
        lugar = C.no_lugar(ERRADA, o)
        placar(tela, lugar, est_rotor(C, ERRADA, o, 0.0, travou))
        if VERTICAL: return
        if foco == 1:
            etiqueta(tela, 'ALTO DEMAIS', 8, 14, C.X[1] - 5, C.Y_S - 4, VERMELHO)
            etiqueta(tela, 'CORTE RASO', 8, 190, C.X[1] - 2, C.y_corte(ERRADA[1]) + 4, AMARELO)
        elif foco == 3:
            etiqueta(tela, 'BAIXO DEMAIS', 120, 14, C.X[3] - 5, C.Y_S + 2, VERMELHO)
            etiqueta(tela, 'CORTE FUNDO', 120, 190, C.X[3] + 2, C.y_corte(ERRADA[3]) + 4, AMARELO)
        titulo_painel(tela, 'CHAVE ERRADA', None, VERMELHO, y=8)
        inset(tela, C, foco if foco is not None else 1, ERRADA, o, 0.0)

    def sons(self, fx):
        self.sons_pinos(fx, 0, 7.0, .15)
        for a in self.tentativas():
            fx.put(baque(70, .2), self.t0 + a + .2, .35)


# ============================================================ chave certa (câmera lenta)
class Certa(Cena):
    T_IN, T_GIRA = 18.0, (27.0, 30.0)

    def o(self, t, C=None):
        f = self.fora(C)
        # entra devagar e desacelera no fim (é ali que ensina)
        return f * (1 - suave(min(1.0, max(0.0, (t - .5) / (self.T_IN - .5))) ** .85)) if t < self.T_IN else 0.0

    def theta(self, t):
        return rampa(t, *self.T_GIRA, 0.0, 90.0, suave)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        o, th = self.o(t), self.theta(t)
        alinhado = C.pode_girar(CERTA, o)
        C.desenhar(tela, CERTA, o, th, fase=t * 6, linha=t > 8.8, marcar=17.8 <= t < self.T_GIRA[0] or (t > 8.8 and th == 0))
        if alinhado and th == 0:
            u = (t - self.T_IN) * 2
            for x in range(C.x0 - 6, C.xp1 + 8, 4):
                if (x // 4 - int(u * 6)) % 6 == 0: tela.ret(x, C.Y_S, 3, 1, VERDE)
        if th > 0:
            brilho(tela, C.xp1 + 4, C.yc + 18, 10, AMARELO, .8)
        lugar = C.no_lugar(CERTA, o)
        placar(tela, lugar, est_rotor(C, CERTA, o, th))
        if VERTICAL: return
        if 8.8 <= t < 17.6:
            i = int((t - 8.8) / 1.76) % 5
            x = C.x0 - o + C.u[i]
            if 0 < x < PX0 - 10:
                etiqueta(tela, f'DENTE {i + 1}', 8, 190, x, C.y_corte(CERTA[i]) + 3, AMARELO)
        if th > 0:
            etiqueta(tela, 'CAME', 250, 190, C.xp1 + 4, C.yc + 20, AMARELO)
        titulo_painel(tela, 'CHAVE CERTA', None, VERDE, y=8)
        inset(tela, C, 1, CERTA, o, th)

    def sons(self, fx):
        self.sons_pinos(fx, 0, self.T_IN + .1, .16)
        fx.put(fx.sino(84, 1.0), self.t0 + self.T_IN, .16)
        fx.put(giro_som(2.9), self.t0 + self.T_GIRA[0], .08)
        fx.put(baque(110, .15), self.t0 + self.T_GIRA[1], .14)


# ============================================================ batida (1 pino por compasso)
class Batida(Cena):
    PADRAO = 'ABABABAAA'                       # compassos 7..15: A = chave certa, B = errada

    def preparar(self):
        self.bar = 4 * self.spb
        self.CC = Cilindro(78, 26)          # no corte vertical o esmeril (x0 - 14) tem que caber no recorte

    def fase(self, t):
        k = int(t / self.bar)
        return k, t - k * self.bar

    def seg(self, t):
        k, u = self.fase(t)
        if k < 5:
            s = [CERTA[j] if j < k else 0 for j in range(5)]
            s[k] = CERTA[k] * rampa(u, 2.2 * self.spb / 2, 1.8 * self.spb, 0.0, 1.0, lambda x: x) if u >= self.spb else 0
            if u >= 2 * self.spb: s[k] = CERTA[k]
            return s
        if k < 7: return CERTA
        return CERTA if self.PADRAO[min(8, k - 7)] == 'A' else ERRADA

    def o(self, t, C=None):
        C = C or self.C
        k, u = self.fase(t)
        sb = self.spb
        if k < 5:
            ok = C.u[k] + 14
            if u < sb: return rampa(u, .02, .45, 0.0, ok, suave)
            if u < 2 * sb: return ok
            return rampa(u, 2 * sb, 3 * sb, ok, 0.0, suave)
        if k < 7: return 0.0
        f = self.fora(C)
        if u < sb: return rampa(u, .1, sb, f, 0.0, suave)
        if u < 3 * sb: return 0.0
        return rampa(u, 3 * sb, 3 * sb + .4, 0.0, f, suave)

    def theta(self, t):
        k, u = self.fase(t)
        sb = self.spb
        if k in (5, 6):
            j = int((t - 5 * self.bar) / sb)
            e = ease(((t - 5 * self.bar) % sb) / .3)
            return 22.5 * (j + e) if j < 4 else 90 - 22.5 * (j - 4 + e)
        if k >= 7 and self.PADRAO[min(8, k - 7)] == 'A':
            if u < sb: return 0.0
            if u < 2 * sb: return 90 * suave((u - sb) / sb)
            return 90 * (1 - suave(min(1.0, (u - 2 * sb) / sb)))
        return 0.0

    def esmeril_xy(self, C, t):
        k, u = self.fase(t)
        xc = C.x0 - 14
        d = 0.0
        if k < 5 and self.spb <= u < 2 * self.spb:
            d = C.y_corte(self.seg(t)[k]) - C.Y_KT
        return xc, C.Y_KT - 10 + d

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        seg, o, th = self.seg(t), self.o(t), self.theta(t)
        k, u = self.fase(t)
        sb = self.spb
        if th > 0 and not C.pode_girar(seg, o): th = 0.0
        acerto = k < 5 and u >= 3 * sb
        C.desenhar(tela, seg, o, th, linha=True, marcar=k < 7 and o == 0,
                   cortes_brilho={k: 1 - (u - 3 * sb) / sb} if acerto else None)
        # esmeril (só nos 5 primeiros compassos)
        if k < 5:
            xc, yc = self.esmeril_xy(C, t)
            cortando = sb <= u < 2 * sb
            Mk = Mascara(); Mk.disco(xc, yc, 10)
            pintar_tela(tela, Mk, 'acoesc', cx=xc, cy=yc, R=10)
            for j in range(6):
                a = math.radians(j * 60 + (t * 900 if cortando else t * 60))
                tela.px(xc + math.cos(a) * 7, yc + math.sin(a) * 7, ACO3)
            tela.disco(xc, yc, 2, ACO4)
            Mk = Mascara(); linha_grossa(Mk, xc, yc, xc, 0, 4, 1)
            pintar_tela(tela, Mk, 'aco')
            if cortando:
                for j in range(8):
                    a = math.radians(200 + j * 18 + (t * 700 + j * 37) % 30)
                    r = 12 + ((t * 90 + j * 11) % 14)
                    tela.px(xc + math.cos(a) * r, yc + 10 + math.sin(a) * r * .5, AMARELO if j % 2 else CHAMA0)
        lugar = C.no_lugar(seg, o)
        travou = k >= 7 and self.PADRAO[min(8, k - 7)] == 'B' and sb <= u < 2.6 * sb
        if travou:
            for i in range(5):
                if not lugar[i]: brilho(tela, C.X[i], C.Y_S, 12, VERMELHO, 1.0)
        if k < 5: chave = 'CORTANDO' if sb <= u < 2 * sb else 'LISA' if k == 0 and u < sb else f'{k + (u >= 2 * sb)} DENTES'
        elif k < 7: chave = 'PRONTA'
        else: chave = 'CERTA' if self.PADRAO[min(8, k - 7)] == 'A' else 'ERRADA'
        placar(tela, lugar, est_rotor(C, seg, o, th, travou), y=30)
        if VERTICAL: return
        batidas(tela, t, sb, PX0, 8, AMARELO if acerto else CIANO)
        tela.texto(f'COMPASSO {k + 1}', PX0 + 92, 11, ACO3, tam=9, contorno=PRETO)
        tela.texto('CHAVE:', PX0, 102, ACO3, tam=9, contorno=PRETO)
        cor = VERMELHO if chave == 'ERRADA' else (VERDE if chave in ('CERTA', 'PRONTA') else AMARELO)
        tela.texto(chave, PX0 + 44, 99, cor, tam=17, contorno=PRETO)
        if k < 5:
            tela.texto(f'DENTE {k + 1}: ALTURA {CERTA[k]}', PX0, 122, BRANCO, tam=9, contorno=PRETO)
        elif k < 7:
            tela.texto('GIRA NA BATIDA', PX0, 122, VERDE, tam=9, contorno=PRETO)
        else:
            tela.texto('VELOCIDADE DE VERDADE', PX0, 122, CIANO, tam=9, contorno=PRETO)
        inset(tela, C, min(k, 4) if k < 5 else 1, seg, o, th, y=150, cy=172, ix=PX0 + 146)

    def sons(self, fx):
        sb = self.spb
        for k in range(16):
            t0 = self.t0 + k * self.bar
            if k < 5:
                fx.put(tique(1700, .03), t0 + .45, .08)
                fx.put(esmeril(sb * .85), t0 + sb, .1)
                fx.put(tique(2900, .035, .007), t0 + 3 * sb, .3)        # o pino cai no lugar: batida 4
                fx.put(fx.sino(79 + k * 2, .5), t0 + 3 * sb, .1)
            elif k < 7:
                for j in range(4):
                    fx.put(tique(2000 + 150 * j, .03), t0 + j * sb, .2)
            else:
                fx.put(tique(2600, .03, .006), t0 + sb, .22)               # chave toda dentro
                if self.PADRAO[min(8, k - 7)] == 'A':
                    fx.put(tique(1500, .04, .008), t0 + 2 * sb, .2)
                    fx.put(tique(1300, .04, .008), t0 + 3 * sb, .16)
                else:
                    fx.put(baque(70, .2), t0 + sb + .05, .3)


# ============================================================ giro (de frente, grande)
class Giro(Cena):
    I = 1

    def o(self, t, C=None):
        return rampa(t, .3, 6.0, self.fora(C), 0.0, suave)

    def theta(self, t):
        if t < 15.6: return rampa(t, 7.0, 15.0, 0.0, 360.0, suave)
        return rampa(t, 16.0, 23.5, 360.0, 720.0, suave)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.CL
        o, th = self.o(t), self.theta(t)
        cx, cy, esc = (150 if VERTICAL else 140), 136, 1.32
        C.desenhar_frente(tela, cx, cy, esc, self.I, CERTA, o, th, came=True)
        if th > 0:
            a = math.radians(th + 90)
            brilho(tela, cx + math.cos(a) * (C.R * esc + 12), cy + math.sin(a) * (C.R * esc + 12), 10, AMARELO,
                   .7 if t >= 15.8 else .3)
        lugar = C.no_lugar(CERTA, o)
        voltas = th / 360.0
        if VERTICAL:
            hud_vertical(tela, [(f'GIRO {int(th) % 360 if th < 720 else 360} GRAUS', VERDE if th else AMARELO)])
            return
        S = lambda y: cy + (y - C.yc) * esc
        b = C.pilha(CERTA, self.I, o)
        etiqueta(tela, 'CORPO', 8, 20, cx - 18, S(60), AMARELO)
        etiqueta(tela, 'MOLA', 236, 14, cx + 4, S(C.Y_CT + 10), ACO3)
        etiqueta(tela, 'CONTRAPINO', 216, 52, cx + 6, S((b[-2] + b[-1]) / 2), CIANO)
        etiqueta(tela, 'LINHA DE CORTE', 196, 96, cx + C.R * esc * .7, cy - C.R * esc * .7, CIANO)
        etiqueta(tela, 'ROTOR', 8, 112, cx - C.R * esc + 6, cy + 4, AMARELO)
        if th == 0:
            etiqueta(tela, 'PINO', 8, 76, cx - 5, S((b[0] + b[1]) / 2), AMARELO)
        if t >= 15.8:
            a = math.radians(th + 90)
            etiqueta(tela, 'CAME', 236, 190, cx + math.cos(a) * (C.R * esc + 10), cy + math.sin(a) * (C.R * esc + 10), AMARELO)
        titulo_painel(tela, 'DE FRENTE', None, BRANCO, y=8)
        placar(tela, lugar, est_rotor(C, CERTA, o, th))
        painel(tela, PX0 - 6, 104, 172, 52, borda=TRACO)
        tela.texto('GIRO DO ROTOR', PX0 + 2, 110, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{int(round(th)) % 360 if th < 719.5 else 360} GRAUS", PX0 + 2, 124, AMARELO, tam=17, contorno=PRETO)
        tela.texto(f"VOLTAS: {I.decimal(voltas, 1)}", PX0 + 2, 144, BRANCO, tam=9, contorno=PRETO)
        # mostrador do ângulo
        gx, gy = PX0 + 140, 132
        tela.anel(gx, gy, 14, ACO2)
        a = math.radians(th - 90)
        tela.linha(gx, gy, gx + math.cos(a) * 12, gy + math.sin(a) * 12, AMARELO)
        tela.disco(gx, gy, 2, AMARELO)

    def sons(self, fx):
        self.sons_pinos(fx, 0, 6.2, .14)
        fx.put(giro_som(7.5), self.t0 + 7.2, .08)
        fx.put(giro_som(7.0), self.t0 + 16.2, .08)


# ============================================================ came e lingueta
class Lingueta(Cena):
    def preparar(self):
        self.K = Caixa()

    def phi(self, t):
        if t < 18: return rampa(t, 2.0, 17.0, -180.0, 180.0, lambda u: suave(u) * .2 + u * .8)
        return rampa(t, 27.0, 34.5, 180.0, -180.0, lambda u: suave(u) * .2 + u * .8)

    def macaneta(self, t):
        if 19.5 <= t < 24.5: return rampa(t, 19.5, 20.5, 0.0, 1.0) if t < 23.5 else rampa(t, 23.5, 24.5, 1.0, 0.0)
        return 0.0

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        K = self.K
        ph = self.phi(t)
        m = self.macaneta(t)
        d = K.desenhar(tela, ph, trinco=m, macaneta=m)
        eng = abs(ph) < K.PHI_ENG
        if eng:
            x, y = K.ponta(ph)
            brilho(tela, x, y, 10, AMARELO, .9)
        fr = d / K.curso
        if VERTICAL:
            hud_vertical(tela, [('LINGUETA ' + ('PARA FORA' if fr > .99 else 'DENTRO' if fr < .01 else 'ANDANDO'),
                                 VERDE if fr > .99 else AMARELO)], x=174)     # recorte x 84..264
            return
        A = K.ancoras(ph)
        etiqueta(tela, 'CAIXA', 8, 196, *A['caixa'], ACO3)
        etiqueta(tela, 'CILINDRO', 8, 96, *A['cilindro'], AMARELO)
        etiqueta(tela, 'CAME', 8, 150, *A['came'], AMARELO if eng else ACO3)
        etiqueta(tela, 'LINGUETA', 240, 184, *A['lingueta'], CIANO)
        etiqueta(tela, 'TRINCO', 248, 30, *A['trinco'], ACO3)
        etiqueta(tela, 'MAÇANETA', 8, 4, *A['macaneta'], ACO3)
        etiqueta(tela, 'BATENTE', 254, 4, K.xt + 30, K.y0 + 2, ACO3)
        titulo_painel(tela, 'A LINGUETA', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 32, 172, 58, borda=VERDE if fr > .99 else TRACO)
        tela.texto('LINGUETA', PX0 + 2, 38, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0 + 2, 52, 120, 10, fr, VERDE if fr > .99 else AMARELO)
        tela.texto(f"{int(round(fr * 100))}%", PX0 + 162, 50, BRANCO, tam=17, centro='d', contorno=PRETO)
        st = 'TRANCADA' if fr > .99 else ('ABERTA' if fr < .01 else 'ANDANDO...')
        tela.texto(st, PX0 + 2, 70, VERDE if fr > .99 else (AMARELO if fr >= .01 else ACO3), tam=17, contorno=PRETO)
        painel(tela, PX0 - 6, 98, 172, 46, borda=AMARELO if eng else TRACO)
        tela.texto('GIRO DA CHAVE', PX0 + 2, 104, ACO3, tam=9, contorno=PRETO)
        volta = (ph + 180) / 360.0
        barra(tela, PX0 + 2, 118, 120, 8, volta, CIANO)
        tela.texto('CAME ENGATADO' if eng else 'CAME SOLTO', PX0 + 2, 132, AMARELO if eng else ACO2, tam=9, contorno=PRETO)
        if 19.5 <= t < 24.5:
            tela.texto('A MAÇANETA SÓ PUXA', PX0, 156, BRANCO, tam=9, contorno=PRETO)
            tela.texto('O TRINCO: A LINGUETA', PX0, 168, BRANCO, tam=9, contorno=PRETO)
            tela.texto('FICA ONDE ESTÁ', PX0, 180, AMARELO, tam=9, contorno=PRETO)
        elif t >= 26.8:
            tela.texto('SEM MOLA: SÓ VOLTA', PX0, 156, BRANCO, tam=9, contorno=PRETO)
            tela.texto('COM A CHAVE', PX0, 168, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        K = self.K
        for a, b in ((2.0, 17.0), (27.0, 34.5)):
            ts = np.arange(a, b, .01)
            eng = [abs(self.phi(t)) < K.PHI_ENG for t in ts]
            for j in range(1, len(ts)):
                if eng[j] != eng[j - 1]:
                    fx.put(tique(1400, .05, .01), self.t0 + ts[j], .25)
                    if not eng[j]: fx.put(baque(95, .16), self.t0 + ts[j], .25)
            for k in range(int((b - a) / .5)):
                fx.put(tique(2600, .02, .004), self.t0 + a + k * .5, .05)
        fx.put(tique(1900, .04, .008), self.t0 + 19.6, .18)
        fx.put(tique(2100, .04, .008), self.t0 + 24.4, .2)


# ============================================================ o trinco (visto de cima)
class Trinco(Cena):
    def preparar(self):
        self.T = TrincoCima()
        self.yf = self.T.yd_fechado()

    def yd(self, t):
        T, yf = self.T, self.yf
        if t < 7.8: return rampa(t, 1.0, 7.8, 14.0, 64.0, suave)
        if t < 16: return rampa(t, 7.8, 15.4, 64.0, yf, lambda u: u)
        if t < 22.0:
            # empurra para abrir sem a maçaneta: a face reta trava na chapa
            if 17.5 <= t < 21.0:
                return yf - .9 * abs(math.sin((t - 17.5) * math.pi * 2))
            return yf
        return rampa(t, 25.6, 29.4, yf, 14.0, suave)

    def puxado(self, t):
        if t < 22.8: return 0.0
        if t < 27.5: return rampa(t, 22.8, 24.4, 0.0, 1.0)
        return rampa(t, 27.5, 28.2, 1.0, 0.0)

    def estado(self, t):
        yd, p = self.yd(t), self.puxado(t)
        return yd, self.T.ext(yd, p), p

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        T = self.T
        yd, e, p = self.estado(t)
        T.desenhar(tela, yd, e)
        # a maçaneta (vista de cima: alavanca na face da porta)
        mx, my = 128, yd - 15
        Mk = Mascara(); Mk.ret(mx - 4, my - 4, 8, 4); Mk.ret(mx - 30, my - 9 + 3 * p, 30, 5)
        pintar_tela(tela, Mk, 'chave' if p == 0 else 'latao')
        clic = 15.0 <= t < 16.2 and e >= T.E_MAX - .01
        if clic:
            brilho(tela, T.XD + e, yd, 12, AMARELO, 1.2 - (t - 15.0))
        bloq = 17.5 <= t < 21.0 and T.bloqueia_abrir(self.yf, e)
        if bloq and int(t * 4) % 2 == 0:
            brilho(tela, T.XL, yd - T.W2, 10, VERMELHO, 1.0)
        if VERTICAL:
            s = 'TRINCO ' + ('ENTRANDO' if e < T.E_MAX - .01 else 'PARA FORA')
            hud_vertical(tela, [(s, AMARELO if e < T.E_MAX - .01 else VERDE)])
            return
        A = T.ancoras(yd, e)
        etiqueta(tela, 'TRINCO', 216, 194, *A['trinco'], AMARELO)
        etiqueta(tela, 'CHAPA', 196, 6, *A['chapa'], ACO3)
        etiqueta(tela, 'BATENTE', 262, 160, T.XL + 50, 150, ACO3)
        etiqueta(tela, 'MOLA', 92, 194, *A['mola'], CIANO)
        etiqueta(tela, 'MAÇANETA', 8, 30 if yd > 50 else 120, mx - 20, my - 7, ACO3 if p == 0 else AMARELO)
        etiqueta(tela, 'PORTA (VISTA DE CIMA)', 8, 194, 40, yd + 10, ACO3)
        titulo_painel(tela, 'O TRINCO', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 32, 172, 58, borda=AMARELO if e < T.E_MAX - .01 else VERDE)
        tela.texto('PARA FORA', PX0 + 2, 38, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0 + 2, 52, 120, 10, e / T.E_MAX, VERDE if e > T.E_MAX - .01 else AMARELO)
        if p > 0: st, cor = 'MAÇANETA PUXA', AMARELO
        elif e < T.E_MAX - .01: st, cor = 'A RAMPA EMPURRA', AMARELO
        elif yd >= self.yf - 1: st, cor = 'FECHADA', VERDE
        else: st, cor = 'SOLTO', ACO3
        tela.texto(st, PX0 + 2, 70, cor, tam=17 if tela.largura_texto(st, 17) < 164 else 9, contorno=PRETO)
        painel(tela, PX0 - 6, 98, 172, 30, borda=TRACO)
        tela.texto('MOLA', PX0 + 2, 104, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0 + 40, 104, 80, 8, 1 - e / T.E_MAX, CIANO)
        tela.texto('APERTADA' if e < 4 else 'FOLGADA', PX0 + 40, 116, CIANO, tam=9, contorno=PRETO)
        if bloq:
            tela.texto('EMPURRAR NÃO ABRE:', PX0, 140, BRANCO, tam=9, contorno=PRETO)
            tela.texto('A FACE RETA TRAVA', PX0, 152, VERMELHO, tam=9, contorno=PRETO)

    def sons(self, fx):
        ts = np.arange(0, self.dur, .005)
        es = [self.estado(t)[1] for t in ts]
        for j in range(1, len(ts)):
            if es[j] - es[j - 1] > 6:
                fx.put(tique(2400, .04, .008), self.t0 + ts[j], .35)       # o clic
                fx.put(baque(160, .1), self.t0 + ts[j], .2)
        for k in range(4):
            fx.put(baque(90, .12), self.t0 + 17.75 + k * .5, .2)
        fx.put(tique(1700, .04, .008), self.t0 + 22.9, .15)


# ============================================================ a chave
class ChaveCena(Cena):
    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.CC
        o = -20 + 3 * math.sin(t * 1.3) if not VERTICAL else 0.0
        dy = -56
        foco = int(t / .8) % 5
        C.desenhar_chave(tela, CERTA, o, 0.0, brilho_cortes={foco: .8} if t < 7.8 else None, dy=dy)
        xs0 = C.x0 - o
        # o formato (de frente): o buraco do rotor e duas chaves chegando
        if t >= 7.8:
            self.perfis(tela, t)
        if VERTICAL:
            hud_vertical(tela, [('A CHAVE', AMARELO)])
            return
        etiqueta(tela, 'CABEÇA', 8, 8, xs0 - 30, C.yc + dy - 18, AMARELO)
        etiqueta(tela, 'HASTE', 120, 8, xs0 + 12, C.Y_KT + dy + 2, AMARELO)
        etiqueta(tela, 'DENTES', 196, 8, xs0 + C.u[2], C.y_corte(CERTA[2]) + dy + 1, AMARELO)
        etiqueta(tela, 'PONTA', 250, 110, xs0 + C.u_tip - 4, C.Y_KB + dy - 4, ACO3)
        etiqueta(tela, 'SULCO', 8, 110, xs0 + 30, 140 + dy, CIANO)
        titulo_painel(tela, 'A CHAVE', None, BRANCO, y=8)
        tela.texto('DENTES = SEGREDO', PX0, 34, ACO3, tam=9, contorno=PRETO)
        for i, d in enumerate(CERTA):
            x = PX0 + i * 30
            on = i == foco and t < 7.8
            painel(tela, x, 48, 26, 30, borda=AMARELO if on else TRACO)
            tela.texto(str(d), x + 13, 53, AMARELO if on else BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto('ALTURA DE CADA DENTE', PX0, 84, ACO2, tam=9)
        if t >= 7.8:
            tela.texto('O FORMATO DO BURACO', PX0, 112, ACO3, tam=9, contorno=PRETO)
            tela.texto('É UMA SEGUNDA TRAVA', PX0, 124, BRANCO, tam=9, contorno=PRETO)
        if t >= 15.8:
            tela.texto('OUTRO FORMATO:', PX0, 146, ACO3, tam=9, contorno=PRETO)
            tela.texto('NEM ENTRA', PX0, 158, VERMELHO, tam=17, contorno=PRETO)

    def perfis(self, tela, t):
        """Vista de frente do buraco (zigue-zague) e duas chaves em corte:
        a do formato certo encolhe até caber; a outra bate na parede."""
        def perfil(cx, cy, s, inv=False):
            pts = [(-3, -16), (3, -16), (3, -8), (6, -4), (3, 0), (3, 6), (0, 10), (3, 14), (3, 18), (-3, 18), (-3, 8),
                   (-6, 4), (-3, 0), (-3, -6), (-6, -10)]
            if inv: pts = [(-x, y) for x, y in pts]
            return [(cx + x * s, cy + y * s) for x, y in pts]
        for j, (cx, ok) in enumerate(((90, True), (200, False))):
            cy = 150
            if VERTICAL and j == 1: cx = 180
            if VERTICAL and j == 0: cx = 100
            # face do rotor com o buraco
            Mk = Mascara(); Mk.disco(cx, cy, 30)
            pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=30)
            poligono(tela, perfil(cx, cy, 1.25), FUNDO)
            # a chave chegando (perto = grande; dentro = do tamanho do buraco)
            u = ((t - 7.8) % 4.0) / 4.0
            if ok:
                s = 2.6 - 1.55 * min(1.0, u / .6)
            else:
                s = 2.6 - 1.25 * min(1.0, u / .6)
                if u > .6: s = 1.35 + .06 * math.sin((u - .6) * 60) * (1 - u)
            Mk = Mascara(); poligono(Mk, perfil(cx, cy, s, inv=not ok), 1)
            pintar_tela(tela, Mk, 'chave', cx=cx, cy=cy, R=20)
            if u > .6:
                if ok:
                    tela.texto('ENTRA', cx, cy + 34, VERDE, tam=9, centro=True, contorno=PRETO)
                else:
                    brilho(tela, cx, cy, 16, VERMELHO, 1.0)
                    tela.texto('BATE', cx, cy + 34, VERMELHO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for k in range(int(self.dur / .8)):
            if k * .8 < 7.8: fx.put(tique(2300 + 150 * (k % 5), .025), self.t0 + k * .8, .1)
        for k in range(5):
            t = 7.8 + k * 4.0 + 2.4
            if t < self.dur:
                fx.put(tique(2000, .04), self.t0 + t, .15)
                fx.put(baque(75, .15), self.t0 + t, .25)


# ============================================================ combinações
class Combinacoes(Cena):
    REGRAS = [([0, 9, 2, 5, 4], 0), ([3, 4, 6, 5, 7], None), ([8, 1, 3, 3, 9], 0), ([2, 3, 5, 4, 4], None)]

    def numero(self, t):
        if t < 8.8: return int(t / .5)
        if t < 26.6: return min(99999, int(17 + 99982 * ((t - 8.8) / 17.4) ** 3.2))
        return None

    def digitos(self, t):
        n = self.numero(t)
        if n is None:
            return self.REGRAS[int((t - 26.6) / 2.25) % 4][0]
        return [int(c) for c in f"{n:05d}"]

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.CC
        dig = self.digitos(t)
        dy = -48
        o = -20 if not VERTICAL else 0
        C.desenhar_chave(tela, dig, o, 0.0, dy=dy)
        xs0 = C.x0 - o
        regra = None
        if self.numero(t) is None:
            regra = self.REGRAS[int((t - 26.6) / 2.25) % 4][1]
        # contadores (um por dente) embaixo da chave
        for i, d in enumerate(dig):
            x = int(xs0 + C.u[i])
            painel(tela, x - 11, 128, 22, 28, borda=VERMELHO if regra is not None and i in (regra, regra + 1) else TRACO)
            tela.texto(str(d), x, 132, AMARELO, tam=17, centro=True, contorno=PRETO)
            tela.linha(x, 124, x, C.y_corte(d) + dy + 3, FUNDO3)
        if regra is not None:
            x = (xs0 + C.u[regra] + xs0 + C.u[regra + 1]) / 2
            brilho(tela, x, C.Y_KT + dy + 10, 16, VERMELHO, 1.0)
            if not VERTICAL: rotulo(tela, 'VIZINHOS MUITO DIFERENTES', 30, 170, VERMELHO, 9)
        elif self.numero(t) is None and not VERTICAL:
            rotulo(tela, 'PERMITIDA', 30, 170, VERDE, 9)
        n = self.numero(t)
        if VERTICAL:
            hud_vertical(tela, [(milhar(n) if n is not None else '100.000', AMARELO)])
            return
        tela.texto('5 DENTES, CADA UM DE 0 A 9', 30, 186, ACO3, tam=9, contorno=PRETO)
        titulo_painel(tela, 'COMBINAÇÕES', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 32, 172, 44, borda=AMARELO)
        tela.texto('ESTA CHAVE É A Nº', PX0 + 2, 38, ACO3, tam=9, contorno=PRETO)
        nn = n if n is not None else int(''.join(str(d) for d in dig))
        tela.texto(milhar(nn + 1), PX0 + 2, 52, AMARELO, tam=17, contorno=PRETO)
        if t >= 8.8:
            tela.texto('PINOS: 5   ALTURAS: 10', PX0, 86, BRANCO, tam=9, contorno=PRETO)
            tela.texto('10X10X10X10X10', PX0, 100, CIANO, tam=17, contorno=PRETO)
        if t >= 17.8:
            tela.texto('= 100.000', PX0, 122, AMARELO, tam=17, contorno=PRETO)
            tela.texto('6 PINOS: 1.000.000', PX0, 144, BRANCO, tam=9, contorno=PRETO)
        if t >= 26.8:
            tela.texto('NA PRÁTICA: MENOS', PX0, 166, VERMELHO, tam=9, contorno=PRETO)
            tela.texto('(REGRAS DE CORTE)', PX0, 178, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        ult = None
        for k in range(int(self.dur / .02)):
            t = k * .02
            n = self.numero(t)
            if n is None: break
            if ult is not None and n != ult and (t < 8.8 or k % 4 == 0):
                fx.put(tique(2500 + (n % 5) * 120, .02, .004), self.t0 + t, .07)
            ult = n
        fx.put(fx.sino(84, 1.0), self.t0 + 17.8, .16)
        for k in range(4):
            t = 26.6 + k * 2.25
            fx.put(baque(70, .15) if self.REGRAS[k][1] is not None else fx.sino(81, .4), self.t0 + t, .2 if k % 2 == 0 else .1)


# ============================================================ chave mestra
class Mestra(Cena):
    CICLO = 7.5

    def preparar(self):
        self.CL, self.CC = novo_cil(MESTRA)

    def seg(self, t):
        return CERTA if int(t / self.CICLO) % 2 == 0 else MESTRA

    def o(self, t, C=None):
        u = t % self.CICLO
        f = self.fora(C)
        if u < 3: return rampa(u, .2, 2.2, f, 0.0, suave)
        return rampa(u, 5.8, 7.3, 0.0, f, suave)

    def theta(self, t):
        u = t % self.CICLO
        if u < 4: return rampa(u, 2.6, 3.6, 0.0, 90.0, suave)
        return rampa(u, 4.9, 5.7, 90.0, 0.0, suave)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        seg, o, th = self.seg(t), self.o(t), self.theta(t)
        mestra = seg is MESTRA
        C.desenhar(tela, seg, o, th, linha=True, marcar=th == 0 and o == 0, chave_mat='latao' if mestra else 'chave')
        lugar = C.no_lugar(seg, o)
        nome = ('CHAVE MESTRA', ROSA) if mestra else ('SUA CHAVE', AMARELO)
        if VERTICAL:
            hud_vertical(tela, [(nome[0], nome[1]), (f"PINOS NO LUGAR {sum(lugar)} DE 5", VERDE if all(lugar) else ACO3)])
            return
        b = C.pilha(seg, 1, o)
        etiqueta(tela, 'PEÇA EXTRA', 8, 14, C.X[1] - 5, (b[1] + b[2]) / 2, ROSA)
        b3 = C.pilha(seg, 3, o)
        etiqueta(tela, 'PEÇA EXTRA', 196, 14, C.X[3] + 5, (b3[1] + b3[2]) / 2, ROSA)
        titulo_painel(tela, nome[0], None, nome[1], y=8)
        placar(tela, lugar, est_rotor(C, seg, o, th))
        inset(tela, C, 1, seg, o, th)
        if o == 0:
            k = C.vao_na_linha(b)
            tela.texto('VÃO DE CIMA' if k == 2 else 'VÃO DE BAIXO', PX0, 186, ROSA if k == 2 else AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for c in range(4):
            a = c * self.CICLO
            self.sons_pinos(fx, a, a + 2.4, .13)
            fx.put(giro_som(.9), self.t0 + a + 2.65, .1)
            fx.put(baque(110, .12), self.t0 + a + 3.6, .2)


# ============================================================ tetra
class Tetra(Cena):
    R_ROTOR = 34.0
    CORTES = (4, 7, 2, 5)

    def alcance(self, t, k):
        """Alcance da lâmina k sob a sua fila de pinos (o dente da vez)."""
        fim = 30.0 - 2.0 * self.CORTES[k]
        if t < 1.0: return 6.0
        if t < 6.0:
            u = (t - 1.0) / 5.0
            return 6.0 + (fim - 6.0) * u + 4 * math.sin(u * 9 * math.pi + k) * (1 - u) ** 2 * (u > .05)
        return fim

    def ang(self, t):
        return rampa(t, 16.5, 22.5, 0.0, 90.0, suave)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        cx, cy = (150 if VERTICAL else 130), 104
        R = self.R_ROTOR
        a = self.ang(t)
        ok = t >= 6.0
        # corpo com 4 câmaras
        Mk = Mascara(); Mk.disco(cx, cy, R + 12)
        for k in range(4):
            poligono(Mk, rot_pts(ret_pts(cx - 9, cy - R - 46, cx + 9, cy), cx, cy, 90 * k), 1)
        pintar_tela(tela, Mk, 'latao', cx=cx - 20, cy=cy - 20, R=R * 2)
        for k in range(4):
            poligono(tela, rot_pts(ret_pts(cx - 5, cy - R - 40, cx + 5, cy - R), cx, cy, 90 * k), FUNDO)
        tela.disco(cx, cy, R + .5, FUNDO)
        Mk = Mascara(); Mk.disco(cx, cy, R)
        pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=R)
        tela.disco(cx, cy, 31, FUNDO)
        alc = [self.alcance(t, k) for k in range(4)]
        tetra_frente(tela, cx, cy, a, alc)
        # pilhas: o pino vai do dente até a linha (só fica certo com a chave toda dentro)
        for k in range(4):
            fim = 30.0 - 2.0 * self.CORTES[k]
            Lp = R - fim
            r0 = alc[k]
            r1 = r0 + Lp
            gira = a > 0
            pts = [(cx - 3.5, cy - r1), (cx + 3.5, cy - r1), (cx + 3.5, cy - r0 - 3), (cx, cy - r0), (cx - 3.5, cy - r0 - 3)]
            pts = rot_pts(pts, cx, cy, 90 * k + (a if gira else 0))
            Mk = Mascara(); poligono(Mk, pts, 1); pintar_tela(tela, Mk, 'pino')
            rc = max(r1, R) if gira else r1
            pts = rot_pts(ret_pts(cx - 3.5, cy - rc - 14, cx + 3.5, cy - rc), cx, cy, 90 * k)
            Mk = Mascara(); poligono(Mk, pts, 1); pintar_tela(tela, Mk, 'contra')
            p0 = rot_pts([(cx, cy - R - 40), (cx, cy - rc - 14)], cx, cy, 90 * k)
            for j in range(8):
                u0, u1 = j / 8, (j + 1) / 8
                q0 = (p0[0][0] + (p0[1][0] - p0[0][0]) * u0, p0[0][1] + (p0[1][1] - p0[0][1]) * u0)
                q1 = (p0[0][0] + (p0[1][0] - p0[0][0]) * u1, p0[0][1] + (p0[1][1] - p0[0][1]) * u1)
                nx, ny = -(p0[1][1] - p0[0][1]), p0[1][0] - p0[0][0]
                L = math.hypot(nx, ny) or 1
                s = 3 if j % 2 else -3
                tela.linha(q0[0] + nx / L * s, q0[1] + ny / L * s, q1[0] - nx / L * s, q1[1] - ny / L * s, ACO4)
        if ok:
            for k in range(36):
                aa = math.radians(k * 10)
                tela.px(cx + math.cos(aa) * (R + .5), cy + math.sin(aa) * (R + .5), CIANO)
        foco = int((t - 7.8) / 2.0) % 4 if 7.8 <= t < 15.6 else None
        if foco is not None:
            p = rot_pts([(cx, cy - R)], cx, cy, 90 * foco)[0]
            brilho(tela, p[0], p[1], 12, AMARELO, 1.0)
        if VERTICAL:
            hud_vertical(tela, [('CHAVE TETRA: 4 FACES', AMARELO)])
            return
        etiqueta(tela, 'CHAVE CRUZADA', 8, 190, cx + 4, cy + 10, AMARELO)
        etiqueta(tela, '4 FILAS DE PINOS', 196, 14, cx + 8, cy - R - 24, CIANO)
        titulo_painel(tela, 'CHAVE TETRA', None, BRANCO, y=8)
        tela.texto('TETRA NÃO É 4 PINOS:', PX0, 34, ACO3, tam=9, contorno=PRETO)
        tela.texto('É O SEGREDO EM 4 FACES', PX0, 46, BRANCO, tam=9, contorno=PRETO)
        for k in range(4):
            y = 64 + k * 20
            on = foco == k
            painel(tela, PX0 - 6, y, 120, 16, borda=AMARELO if on else TRACO)
            tela.texto(f'FACE {k + 1}', PX0 + 2, y + 4, AMARELO if on else ACO3, tam=9, contorno=PRETO)
            tela.ret(PX0 + 60, y + 5, 40, 6, VERDE if ok else FUNDO2)
        if t >= 15.8:
            tela.texto('SEGURANÇA = TUDO:', PX0, 152, ACO3, tam=9, contorno=PRETO)
            tela.texto('PORTA, BATENTE,', PX0, 164, BRANCO, tam=9, contorno=PRETO)
            tela.texto('LINGUETA, CILINDRO', PX0, 176, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(24):
            t = 1.0 + k * .21
            if t < 6.0: fx.put(tique(2200 + 120 * (k % 4), .025), self.t0 + t, .1)
        fx.put(fx.sino(81, .8), self.t0 + 6.0, .14)
        fx.put(giro_som(5.5), self.t0 + 16.7, .08)


# ============================================================ história
class Historia(Cena):
    CICLO = 15.0

    def preparar(self):
        self.E = Egipcia()

    def estado(self, t):
        u = t % self.CICLO
        entra = rampa(u, .8, 4.6, 0.0, 1.0, suave) if u < 12.5 else rampa(u, 12.5, 14.6, 1.0, 0.0, suave)
        ergue = rampa(u, 5.0, 6.4, 0.0, 1.0, suave) if u < 10.5 else rampa(u, 10.5, 11.8, 1.0, 0.0, suave)
        desl = rampa(u, 6.8, 9.0, 0.0, -56.0, suave) if u < 9.5 else rampa(u, 9.5, 10.4, -56.0, 0.0, suave)
        return entra, ergue, desl

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        E = self.E
        entra, ergue, desl = self.estado(t)
        E.desenhar(tela, entra, ergue, desl)
        if VERTICAL:
            hud_vertical(tela, [('EGITO: PINOS DE MADEIRA', AMARELO)])
            return
        A = E.ancoras(desl)
        etiqueta(tela, 'PINOS DE MADEIRA', 160, 16, *A['pinos'], AMARELO)
        etiqueta(tela, 'FERROLHO', 200, 160, *A['ferrolho'], AMARELO)
        etiqueta(tela, 'CHAVE', 8, 160, *A['chave'], AMARELO)
        titulo_painel(tela, 'HISTÓRIA', None, BRANCO, y=8)
        cards = [(0.5, 'EGITO ANTIGO', 'PINOS DE MADEIRA', LATAO), (7.8, 'PODE TER', '4.000 ANOS', AMARELO),
                 (15.8, '1848: LINUS YALE', 'O MESMO PRINCÍPIO', CIANO), (22.8, 'ANOS 1860: O FILHO', 'CILINDRO, CHAVE CHATA', VERDE)]
        for j, (ta, a, b, cor) in enumerate(cards):
            if t < ta: continue
            u = ease((t - ta) / .4)
            x = int(PX0 + (1 - u) * 160)
            y = 34 + j * 40
            painel(tela, x - 6, y, 172, 34, borda=cor)
            tela.texto(a, x + 2, y + 5, cor, tam=9, contorno=PRETO)
            tela.texto(b, x + 2, y + 18, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for c in range(2):
            a = c * self.CICLO
            fx.put(baque(130, .12), self.t0 + a + 4.6, .2)
            fx.put(tique(1200, .05, .012), self.t0 + a + 6.4, .2)
            fx.put(baque(100, .2), self.t0 + a + 9.0, .25)
        fx.put(fx.sino(76, 1.0), self.t0 + 15.8, .14)
        fx.put(fx.sino(81, 1.0), self.t0 + 22.8, .14)


# ============================================================ resumo
class Resumo(Cena):
    CICLO = 10.0
    ETAPAS = [('1 A CHAVE ENTRA', AMARELO), ('2 PINOS NA LINHA', VERDE), ('3 O ROTOR GIRA', CIANO),
              ('4 O CAME MOVE A LINGUETA', ROSA)]

    def preparar(self):
        self.K = Caixa()

    def o(self, t, C=None):
        u = t % self.CICLO
        f = self.fora(C)
        if u < 5: return rampa(u, .2, 3.0, f, 0.0, suave)
        return rampa(u, 8.2, 9.8, 0.0, f, suave)

    def theta(self, t):
        u = t % self.CICLO
        if u < 6.5: return rampa(u, 3.8, 5.2, 0.0, 90.0, suave)
        return rampa(u, 7.0, 8.0, 90.0, 0.0, suave)

    def etapa(self, t):
        u = t % self.CICLO
        if u < 3.0: return 0
        if u < 3.8: return 1
        if u < 5.2: return 2
        return 3 if u < 8.0 else 0

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C = self.C
        o, th = self.o(t), self.theta(t)
        C.desenhar(tela, CERTA, o, th, linha=True, marcar=th == 0 and o == 0)
        k = self.etapa(t)
        lugar = C.no_lugar(CERTA, o)
        if VERTICAL:
            hud_vertical(tela, [(self.ETAPAS[k][0], self.ETAPAS[k][1])])
            return
        titulo_painel(tela, 'RESUMO', None, BRANCO, y=8)
        for j, (s, cor) in enumerate(self.ETAPAS):
            y = 32 + j * 26
            on = j == k
            painel(tela, PX0 - 6, y, 172, 22, borda=cor if on else TRACO)
            tela.texto(s, PX0 + 2, y + 7, cor if on else ACO2, tam=9, contorno=PRETO)
        # a lingueta (mini) acompanha o giro
        fr = th / 90.0
        tela.texto('LINGUETA', PX0, 144, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0, 158, 120, 10, 1 - fr, VERDE if fr < .01 else AMARELO)
        tela.texto('PORTA ABERTA' if fr > .99 else 'TRANCADA' if fr < .01 else '...', PX0, 174,
                   VERDE if fr > .99 else BRANCO, tam=9, contorno=PRETO)
        tela.texto(f"{sum(lugar)} DE 5", PX0 + 130, 144, VERDE if all(lugar) else AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for c in range(3):
            a = c * self.CICLO
            self.sons_pinos(fx, a, a + 3.2, .12)
            fx.put(fx.sino(84, .6), self.t0 + a + 3.0, .1)
            fx.put(giro_som(1.3), self.t0 + a + 3.9, .09)
            fx.put(baque(110, .12), self.t0 + a + 5.2, .2)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def o(self, t, C=None):
        u = (t - RM.OUTRO_S) % 6.0
        f = self.fora(C)
        if u < 3: return rampa(u, .2, 2.0, f, 0.0, suave)
        return rampa(u, 4.4, 5.8, 0.0, f, suave)

    def theta(self, t):
        u = (t - RM.OUTRO_S) % 6.0
        if u < 3.4: return rampa(u, 2.3, 3.0, 0.0, 90.0, suave)
        return rampa(u, 3.6, 4.2, 90.0, 0.0, suave)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            fundo_bancada(tela)
            tela.buf[PALCO_H:] = FUNDO
            C = Cilindro(125, 36)
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 2, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 22, AMARELO, tam=9, centro=True, contorno=PRETO)
            C.desenhar(tela, CERTA, self.o(t, C), self.theta(t), linha=True)

    def tela_pronta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .75)


# longo.py chama `cena.pos(baixo, t)` para a cena que entrega RGB pronto (a vinheta).
Fim.pos = Fim.tela_pronta

CENAS = dict(gancho=Gancho, titulo=Titulo, porta=Porta, pecas=Pecas, semchave=SemChave, errada=Errada, certa=Certa,
             batida=Batida, giro=Giro, lingueta=Lingueta, trinco=Trinco, chave=ChaveCena, combinacoes=Combinacoes,
             mestra=Mestra, tetra=Tetra, historia=Historia, resumo=Resumo, fim=Fim)


def checar_tudo():
    D.checar(); D.checar_caixa(); D.checar_trinco(); D.checar_egipcia()
    return True


if __name__ == '__main__':
    import ep17_motor as EP
    checar_tudo()
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
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
