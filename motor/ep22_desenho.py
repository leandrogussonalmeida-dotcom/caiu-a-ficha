#!/usr/bin/env python3
"""ep22 — desenho: o balão de ar quente, a paisagem vista do balão, o voo calculado.

  envelope   o "balão" em si, desenhado por pixel: perfil de gota (meia esfera
             em cima, afinando até a boca), 24 gomos listrados que giram
             devagar, luz de cima/esquerda com pontilhado, fitas horizontais,
             saia embaixo, paraquedas no topo (abre uma fresta), corte (vê o ar
             de dentro). Gira em volta da boca (deitado, na hora de encher).
  cesto      cesto de vime trançado, queimador com serpentina, cabos, botijões.
  chama      a chama do queimador sobe para dentro da boca, com halo.
  Paisagem   céu do amanhecer, morros no horizonte e o chão em perspectiva
             (plano projetado linha a linha): quando o balão sobe, os campos
             encolhem e o chão "afunda" na tela de verdade, sem truque.
  Voo        o voo CALCULADO (passo de 0,05 s): ar de dentro esquenta com o
             queimador e esfria devagar (mais rápido com o paraquedas aberto);
             empuxo = volume x densidade do ar de fora x (1 - Tfora/Tdentro);
             peso 700 kg; arrasto do ar; ar de fora mais ralo com a altitude
             (atmosfera padrão).

Escala: 100 unidades do perfil = altura do envelope. O volume do perfil é
calculado e a escala sai dele: 2.800 metros cúbicos -> cerca de 19,5 m de
altura e 17,5 m de largura.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO,
                   CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS,
                   GAS2, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep02_desenho import pol, contorno, brilho, gradiente, seta_forca, barra

BAY = LG.BAYER8

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#3a78c8', '#5d9ad8', '#8dbbe4', '#c4d9e6', '#ffd9b0', '#ffb98a',      # 32..37 céu do amanhecer
          '#2f5a2c', '#4a7d35', '#6f9a3c', '#a5a24a',                            # 38..41 campos
          '#9fb6b8', '#6f8fa8', '#86a6bb',                                       # 42..44 névoa, morros
          '#ff7a6b', '#e23d4f', '#9a2138',                                       # 45..47 listra vermelha
          '#ffe680', '#f6b93b', '#b97d1f',                                       # 48..50 listra amarela
          '#7fd4ff', '#3592e0', '#1f559e',                                       # 51..53 listra azul
          '#fbfbf6', '#d5dbe6', '#97a1b5',                                       # 54..56 listra branca
          '#8ef0c0', '#35b783', '#1f6e52',                                       # 57..59 faixa verde
          '#e2b066', '#b07b3e', '#6d4524',                                       # 60..62 vime
          '#8a8478',                                                             # 63 estrada
          '#5a2416', '#8a3a1c', '#1d2f4f', '#2a446a']                            # 64..67 ar de dentro
PX.PALETAS['ep22'] = _BASE + _EXTRA
LG.PAL = 'ep22'
CEU0, CEU1, CEU2, CEU3, CEU4, CEU5 = 32, 33, 34, 35, 36, 37
CAMPO0, CAMPO1, CAMPO2, CAMPO3 = 38, 39, 40, 41
NEVOA, MORRO0, MORRO1 = 42, 43, 44
VERM, AMAR, AZUL, BRAN, TEAL = (45, 46, 47), (48, 49, 50), (51, 52, 53), (54, 55, 56), (57, 58, 59)
VIME0, VIME1, VIME2 = 60, 61, 62
ESTRADA = 63
INTQ0, INTQ1, INTF0, INTF1 = 64, 65, 66, 67

PADRAO = [VERM, AMAR, VERM, AZUL, BRAN, AZUL]        # gomos: listras inventadas
N_GOMOS = 24


def hsh(i, k=0):
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


def hsh_np(a, b):
    x = np.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return x - np.floor(x)


# =================================================================== perfil
S_BOCA, S_SAIA, S_QUEIM, S_CESTO, S_FUNDO = 100.0, 106.0, 111.0, 117.0, 124.0
CESTO_HW = 5.5


def r_env(s):
    """Meia-largura do envelope (unidades) na posição s (0 = topo, 100 = boca, 106 = fim da saia)."""
    s = np.asarray(s, float)
    r = np.zeros_like(s)
    a = (s >= 0) & (s <= 45)
    r[a] = np.sqrt(np.maximum(0.0, 45.0 ** 2 - (45.0 - s[a]) ** 2))
    b = (s > 45) & (s <= 100)
    u = (s[b] - 45) / 55
    r[b] = 9 + 36 * np.cos(np.pi / 2 * u) ** 1.1
    c = (s > 100) & (s <= S_SAIA)
    r[c] = 9 + (s[c] - 100) * .2
    return r


_ss = np.linspace(0, 100, 4001)
VOL_U = float(np.sum(np.pi * r_env(_ss) ** 2) * (_ss[1] - _ss[0]))
VOLUME = 2800.0                                     # metros cúbicos
M_POR_U = (VOLUME / VOL_U) ** (1 / 3)               # ~0,195 m por unidade
ALTURA_M = 100 * M_POR_U
LARGURA_M = 90 * M_POR_U


# =================================================================== envelope
def envelope(tela, mx, my, k, t, ang=0.0, fill=1.0, vent=0.0, corte=0.0, quente=0.0, rot=None, chama=0.0,
             chao=None, x0=0, x1=W, sem_contorno=False):
    """Desenha o envelope com a boca (s = 100) em (mx, my). `ang` gira em volta
    da boca (0 = de pé; -pi/2 = deitado com o topo à esquerda). Devolve a
    máscara (tela inteira) do que é envelope."""
    sa, ca = math.sin(ang), math.cos(ang)
    dx, dy = sa, -ca                     # da boca para o topo
    nx, ny = ca, sa
    cant = []
    for s_, u_ in ((0, -46), (0, 46), (S_SAIA, -46), (S_SAIA, 46)):
        a_ = (100 - s_) * k
        cant.append((mx + a_ * dx + u_ * k * nx, my + a_ * dy + u_ * k * ny))
    bx0 = max(x0, int(min(c[0] for c in cant)) - 2); bx1 = min(x1, int(max(c[0] for c in cant)) + 3)
    by0 = max(0, int(min(c[1] for c in cant)) - 2); by1 = min(PALCO_H, int(max(c[1] for c in cant)) + 3)
    mask_full = np.zeros((tela.h, tela.w), bool)
    if bx1 <= bx0 or by1 <= by0: return mask_full
    yy, xx = np.mgrid[by0:by1, bx0:bx1]
    rx, ry = xx + .5 - mx, yy + .5 - my
    s = 100 - (rx * dx + ry * dy) / k
    u = (rx * nx + ry * ny) / k
    r = r_env(np.clip(s, 0, S_SAIA))
    if fill < 1:
        f = .12 + .88 * fill
        rug = (1 - fill) * (1.6 * np.sin(s * .9 + t * 2.0) + 1.0 * np.sin(s * 2.3 - t * 1.3))
        r = np.where(s < 100, r * f + rug, r)
    m = (s >= 0) & (s <= S_SAIA) & (np.abs(u) <= r)
    if chao is not None: m &= yy < chao
    nu = np.clip(u / np.maximum(r, 1e-3), -1, 1)
    phi = np.arcsin(nu)
    rot = (t * .05) if rot is None else rot
    gf = (phi + rot) / (np.pi / 12)
    g = np.floor(gf).astype(int) % N_GOMOS
    fr = gf - np.floor(gf)
    # luz de cima e da esquerda
    luz = .78 * np.sqrt(1 - nu ** 2) - .42 * nu + .35 * (1 - np.clip(s, 0, 100) / 100) - .1
    bay = BAY[yy % 8, xx % 8]
    lvl = np.clip(np.floor((1.08 - luz) * 2.7 + bay - .2), 0, 2).astype(int)
    out = np.zeros(m.shape, np.uint8)
    pad = np.array([c for c in PADRAO])                      # (6, 3)
    cores = pad[g % len(PADRAO)]                             # (..., 3)
    # faixa em zigue-zague
    zz = 1 - np.abs(((gf * 2) % 2) - 1)
    banda = (s > 52 + 3 * zz) & (s < 60 + 3 * zz)
    cores = np.where(banda[..., None], np.array(TEAL)[None, None, :], cores)
    out = np.take_along_axis(cores, lvl[..., None], axis=2)[..., 0].astype(np.uint8)
    esc = cores[..., 2].astype(np.uint8)
    # costuras dos gomos (mais finas na borda, onde o gomo fica de lado)
    larg_px = np.sqrt(1 - nu ** 2) * r * k * (np.pi / 12)
    cost = fr * larg_px < .9
    out = np.where(cost & (s < 100), esc, out)
    # fitas horizontais e a costura do paraquedas
    for sf in (28.0, 75.0, 90.0):
        out = np.where((np.abs(s - sf) * k < .55), esc, out)
    out = np.where((np.abs(s - 11.0) * k < .6) & (np.abs(u) < r * .97), PRETO, out)
    # saia: tecido que não pega fogo (cinza), iluminada por dentro quando há chama
    saia = s > 100
    sc = np.where((xx + yy) % 2 == 0, ACO2, ACO1)
    sc = np.where(nu > .3, np.where((xx + yy) % 2 == 0, ACO1, ACO0), sc)
    if chama > .05:
        sc = np.where((np.abs(nu) < .55) & ((xx + yy) % 2 == 0), LARANJA, sc)
    out = np.where(saia, sc, out)
    # corte: o envelope fica "transparente" e mostra o ar de dentro
    if corte > 0:
        if quente > .5:
            it = np.where((xx + yy) % 2 == 0, INTQ1, INTQ0)
        elif quente > .2:
            it = np.where((xx + yy) % 2 == 0, INTQ0, INTF0)
        else:
            it = np.where((xx + yy) % 2 == 0, INTF1, INTF0)
        borda = (np.abs(nu) > .93)
        dentro = (s < 99.5) & ~borda & (np.abs(s - 11) * k >= .6)
        it = np.where(cost, TRACO, it)
        out = np.where(dentro, it, out)
    # paraquedas aberto: fresta perto do topo, mostra o fundo escuro de dentro
    if vent > 0:
        gap = (s > 11.2) & (s < 11.2 + 7 * vent) & (np.abs(u) < r * .9)
        out = np.where(gap, np.where((xx + yy) % 2 == 0, INTQ0, PRETO), out)
    reg = tela.buf[by0:by1, bx0:bx1]
    if not sem_contorno:
        dil = m.copy()
        dil[1:, :] |= m[:-1, :]; dil[:-1, :] |= m[1:, :]
        dil[:, 1:] |= m[:, :-1]; dil[:, :-1] |= m[:, 1:]
        reg[dil & ~m] = PRETO
    reg[m] = out[m]
    mask_full[by0:by1, bx0:bx1] = m
    return mask_full


def pt(mx, my, k, s, u, ang=0.0):
    """Ponto (s, u) do balão na tela."""
    sa, ca = math.sin(ang), math.cos(ang)
    a_ = (100 - s) * k
    return mx + a_ * sa + u * k * ca, my - a_ * ca + u * k * sa


# =================================================================== chama
def chama(tela, x, y, k, forca, t, seed=0, para_cima=True):
    """Chama do queimador saindo de (x, y) para cima."""
    if forca <= .02: return
    fl = .82 + .18 * math.sin(t * 37 + seed) * math.sin(t * 23.3 + seed * 2)
    L = (14 + 3 * math.sin(t * 17 + seed)) * k * forca * fl
    sg = -1 if para_cima else 1
    brilho(tela, x, y + sg * L * .45, max(6, L * .8), LARANJA)
    for frac, larg, cor in ((1.0, 3.0, CHAMA2), (.78, 2.2, CHAMA1), (.5, 1.3, CHAMA0)):
        Lc = L * frac
        w = larg * k * (.7 + .3 * forca)
        tipx = x + math.sin(t * 13 + seed + frac * 3) * k * 1.2
        pts = [(x - w * .45, y), (x - w * .55, y + sg * Lc * .35), (tipx - w * .15, y + sg * Lc * .8),
               (tipx, y + sg * Lc), (tipx + w * .15, y + sg * Lc * .8), (x + w * .55, y + sg * Lc * .35),
               (x + w * .45, y)]
        pol(tela, pts, cor)
    tela.disco(x, y + sg * 2, max(1, k * .8), BRANCO)


def piloto(tela, x, y, t):
    """A chama-piloto, pequena e azulada, sempre acesa."""
    tela.px(x, y - 1, CIANO)
    if math.sin(t * 19) > -.3: tela.px(x, y - 2, BRANCO)


# =================================================================== cesto
def cesto(tela, mx, my, k, t, chama_f=0.0, corte=False, botijoes=True, acesos=(), cabos=True, seed=0):
    """Cesto, queimador e cabos, pendurados embaixo da boca (mx, my) do balão de pé."""
    def P(s, u): return mx + u * k, my + (s - 100) * k
    # cabos: dos cantos do cesto até a borda da saia
    if cabos:
        for su, uu in ((-1, CESTO_HW), (1, CESTO_HW)):
            a = P(S_CESTO, su * uu); b = P(S_SAIA, su * 10.2)
            tela.linha(a[0], a[1], b[0], b[1], ACO1)
            a2 = P(S_CESTO, su * uu * .45); b2 = P(S_SAIA, su * 5.5)
            tela.linha(a2[0], a2[1], b2[0], b2[1], TRACO)
    # armação e queimador
    for su in (-1, 1):
        a = P(S_CESTO, su * CESTO_HW * .9); b = P(S_QUEIM + 1.5, su * 3.2)
        tela.linha(a[0], a[1], b[0], b[1], ACO2)
    qx0, qy0 = P(S_QUEIM, -3.2)
    qx1, qy1 = P(S_QUEIM + 3, 3.2)
    tela.ret(qx0 - 1, qy0 - 1, qx1 - qx0 + 2, qy1 - qy0 + 2, PRETO)
    tela.ret(qx0, qy0, qx1 - qx0, qy1 - qy0, ACO2)
    tela.ret(qx0, qy0, qx1 - qx0, 1, ACO4)
    # serpentina (o propano passa por ela e vira gás)
    for j in range(int((qx1 - qx0) // 2)):
        tela.px(qx0 + 1 + j * 2, qy0 + 1 + (j % 2), ACO3 if chama_f < .1 else LARANJA)
    bico = P(S_QUEIM, 0)
    if 'queimador' in acesos and int(t * 4) % 2 == 0:
        tela.ret_vazado(qx0 - 3, qy0 - 3, qx1 - qx0 + 6, qy1 - qy0 + 6, AMARELO)
    # cesto: vime trançado
    cx0, cy0 = P(S_CESTO, -CESTO_HW)
    cx1, cy1 = P(S_FUNDO, CESTO_HW)
    X0, Y0, X1, Y1 = int(round(cx0)), int(round(cy0)), int(round(cx1)), int(round(cy1))
    tela.ret(X0 - 1, Y0 - 1, X1 - X0 + 2, Y1 - Y0 + 2, PRETO)
    if X1 > X0 and Y1 > Y0:
        ya, xa = np.mgrid[Y0:Y1, X0:X1]
        tr = ((xa // 2 + ya // 2) % 2 == 0)
        c = np.where(tr, VIME0, VIME1)
        c = np.where(ya % 3 == 0, VIME2, c)
        c = np.where((xa - X0) > (X1 - X0) * .62, np.where(tr, VIME1, VIME2), c)
        y_a, y_b = max(0, Y0), min(tela.h, Y1)
        x_a, x_b = max(0, X0), min(tela.w, X1)
        if y_b > y_a and x_b > x_a:
            tela.buf[y_a:y_b, x_a:x_b] = c[y_a - Y0:y_b - Y0, x_a - X0:x_b - X0]
        tela.ret(X0, Y0, X1 - X0, max(1, int(k * 1.2)), OLEO0)       # borda de couro
        tela.ret(X0, Y0, X1 - X0, 1, VIME0)
        if corte:
            # sem a parede da frente: o fundo escuro e os botijões
            ix0, iy0 = X0 + 2, Y0 + max(2, int(k * 1.4))
            dither(tela, ix0, iy0, X1 - X0 - 4, Y1 - iy0 - 2, OLEO0, PRETO)
            if botijoes:
                nb = 3
                bw = max(3, int((X1 - X0 - 8) / nb) - 1)
                for j in range(nb):
                    bx = ix0 + 2 + j * (bw + 1)
                    bh = int((Y1 - iy0) * .78)
                    by = Y1 - 2 - bh
                    tela.ret(bx - 1, by - 1, bw + 2, bh + 2, PRETO)
                    tela.ret(bx, by, bw, bh, ACO3)
                    tela.ret(bx, by, 1, bh, ACO4)
                    tela.ret(bx + bw - 1, by, 1, bh, ACO1)
                    tela.ret(bx + bw // 2 - 1, by - 2, 2, 2, LATAO)
            if 'botijoes' in acesos and int(t * 4) % 2 == 0:
                tela.ret_vazado(X0 - 3, Y0 - 3, X1 - X0 + 6, Y1 - Y0 + 6, AMARELO)
        if 'cesto' in acesos and int(t * 4) % 2 == 0:
            tela.ret_vazado(X0 - 3, Y0 - 3, X1 - X0 + 6, Y1 - Y0 + 6, AMARELO)
    if chama_f > .02:
        chama(tela, bico[0], bico[1], k * .9, chama_f, t, seed)
    else:
        piloto(tela, bico[0], bico[1], t)
    return (X0, Y0, X1, Y1)


def balao(tela, mx, my, k, t, e=None, x0=0, x1=W):
    """O balão inteiro de pé: envelope + cesto. `e`: dict com chama, vent, corte, quente, acesos, rot."""
    e = e or {}
    ch = e.get('chama', 0.0)
    m = envelope(tela, mx, my, k, t, vent=e.get('vent', 0.0), corte=e.get('corte', 0.0),
                 quente=e.get('quente', 1.0), rot=e.get('rot'), chama=ch, x0=x0, x1=x1)
    # a chama entra pela boca: o brilho aparece na boca
    if ch > .05:
        bx, by = pt(mx, my, k, 104, 0)
        brilho(tela, bx, by, 6 * k * ch, CHAMA1)
    cesto(tela, mx, my, k, t, chama_f=ch, corte=e.get('corte_cesto', False), acesos=e.get('acesos', ()),
          seed=e.get('seed', 0))
    return m


# =================================================================== partículas
class Particulas:
    """Moléculas que quicam numa caixa. A posição sai de uma "fase" (a
    integral da velocidade), então dá para acelerar sem pulo."""

    def __init__(self, n, seed=0):
        rng = np.random.default_rng(seed)
        self.p0 = rng.random((n, 2))
        a = rng.random(n) * 2 * np.pi
        v = rng.uniform(.6, 1.4, n)
        self.v = np.stack([np.cos(a) * v, np.sin(a) * v], 1)
        self.n = n

    @staticmethod
    def _tri(x):
        return 1 - np.abs((x % 2.0) - 1)

    def pos(self, fase):
        return self._tri(self.p0 * 2 + self.v * fase)

    def desenhar(self, tela, x, y, w, h, fase, cor, cor_rastro, dfase=.05, idx=None, mask=None, r=1.0):
        p = self.pos(fase)
        q = self.pos(fase - dfase)
        sel = range(self.n) if idx is None else idx
        for i in sel:
            px, py = x + p[i, 0] * w, y + p[i, 1] * h
            qx, qy = x + q[i, 0] * w, y + q[i, 1] * h
            if mask is not None:
                ix, iy = int(px), int(py)
                if not (0 <= ix < tela.w and 0 <= iy < tela.h) or not mask[iy, ix]: continue
            if abs(px - qx) < 14 and abs(py - qy) < 14:
                tela.linha(qx, qy, px, py, cor_rastro)
            if r <= 1.0:
                tela.ret(px - 1, py - 1, 2, 2, cor)
            else:
                tela.disco(px, py, r, cor)


# =================================================================== paisagem
class Paisagem:
    """Céu, morros e chão em perspectiva. A câmera fica 15 m acima do cesto,
    a 60 m de distância do balão, e sobe junto com ele."""
    F, D, CAM = 400.0, 60.0, 15.0

    def __init__(self, hy=95, cx=150, seed=4):
        self.hy, self.cx = hy, cx
        rng = np.random.default_rng(seed)
        self.arvores = [(float(rng.uniform(-260, 260)), float(rng.uniform(30, 420)), float(rng.uniform(6, 11)))
                        for _ in range(26)]
        self.nuvens = [(float(rng.uniform(-900, 900)), float(rng.uniform(500, 1600)), float(rng.uniform(120, 900)),
                        int(rng.integers(0, 14))) for _ in range(12)]
        from ep02_desenho import Ceu
        self.ceu2 = Ceu(seed=9)
        x = np.arange(W)
        self.morro0 = (self.hy - 8 - 6 * np.sin(x * .021 + 1) - 4 * np.sin(x * .057 + 2) - 2 * np.sin(x * .13)).astype(int)
        self.morro1 = (self.hy - 2 - 3 * np.sin(x * .034 + 4) - 2 * np.sin(x * .09 + 1)).astype(int)

    @property
    def ppm(self): return self.F / self.D            # px por metro no plano do balão

    def y_cesto(self): return self.hy + self.F * self.CAM / self.D

    def y_de(self, alt, h):
        """Altura `alt` (m) no plano do balão, com o cesto a `h` m."""
        return self.y_cesto() - (alt - h) * self.ppm

    def ceu(self, tela, h, t, x1=W, sol=True):
        gradiente(tela, 0, 0, x1, self.hy + 1, [(0, CEU0), (.45, CEU1), (.75, CEU2), (.9, CEU3), (1.0, CEU4)])
        if sol:
            sx, sy = 262, self.hy - 14
            brilho(tela, sx, sy, 20, CEU5)
            tela.disco(sx, sy, 8, CHAMA1)
            tela.disco(sx, sy, 6, CHAMA0)
            tela.disco(sx - 2, sy - 2, 2, BRANCO)
        for x in range(0, x1):
            tela.ret(x, self.morro0[x], 1, self.hy - self.morro0[x] + 1, MORRO1)
        for x in range(0, x1):
            tela.ret(x, self.morro1[x], 1, self.hy - self.morro1[x] + 1, MORRO0)

    def nuvens_(self, tela, h, X, t, x1=W, frente=False):
        for wx, z, hc, idx in self.nuvens:
            if (z < self.D) != frente: continue
            esc = self.F / z * 1.6
            x = self.cx + (wx - X - t * 1.5) * self.F / z
            y = self.hy - self.F * (hc - (h + self.CAM)) / z
            if -80 < x < x1 + 80 and -30 < y < PALCO_H + 30:
                self.ceu2.nuvem(tela, x, y, self.ceu2.nuvens[idx], min(2.5, esc), luz=True)

    def chao(self, tela, h, X, t, x1=W):
        He = h + self.CAM
        y0 = self.hy + 1
        ys = np.arange(y0, PALCO_H)[:, None].astype(float)
        xs = np.arange(0, x1)[None, :].astype(float)
        z = self.F * He / (ys - self.hy + .5)
        wx = (xs - self.cx) * z / self.F + X
        ix = np.floor(wx / 70.0)
        iz = np.floor(z / 55.0)
        hv = hsh_np(ix, iz)
        cor = np.where(hv < .3, CAMPO1, np.where(hv < .6, CAMPO2, np.where(hv < .82, CAMPO0, CAMPO3)))
        # cerca viva entre os campos (1 px na tela)
        bx = (wx / 70.0 - ix) * 70.0 < np.maximum(.9, 1.1 * z / self.F)
        bz = (z / 55.0 - iz) * 55.0 < z * z / (self.F * He) * 1.0
        cor = np.where(bx | bz, CAMPO0, cor)
        # estrada
        cor = np.where(np.abs(wx - 35) < 3.5, ESTRADA, cor)
        # névoa ao longe
        yy = ys.astype(int); xx = xs.astype(int)
        b = BAY[yy % 8, xx % 8]
        nv = np.clip((z - 1500) / 5000, 0, .9)
        cor = np.where(nv > b, NEVOA, cor)
        tela.buf[y0:PALCO_H, 0:x1] = cor.astype(np.uint8)
        tela.ret(0, self.hy, x1, 1, NEVOA)

    def arvores_(self, tela, h, X, x1=W, frente=False):
        He = h + self.CAM
        for wx, z, alt in sorted(self.arvores, key=lambda a: -a[1]):
            if (z < self.D) != frente: continue
            e = self.F / z
            x = self.cx + (wx - X) * e
            yb = self.hy + self.F * He / z
            if yb > PALCO_H + 40 or x < -30 or x > x1 + 30: continue
            hh = alt * e
            if hh < 2:
                tela.px(x, yb - 1, CAMPO0); continue
            tela.ret(x - max(1, hh * .06), yb - hh * .35, max(1, hh * .12), hh * .35, OLEO0)
            r = hh * .32
            tela.disco(x, yb - hh * .62, r + 1, PRETO)
            tela.disco(x, yb - hh * .62, r, CAMPO0)
            tela.disco(x - r * .25, yb - hh * .7, r * .65, CAMPO1)
            tela.disco(x - r * .35, yb - hh * .78, r * .3, CAMPO2)

    def regua(self, tela, h, x=4, passo=10, cor=ACO3):
        """Régua de altitude na beira esquerda: anda quando o balão sobe."""
        yb = self.y_cesto()
        a0 = int((h - 40) // passo) * passo
        for a in range(max(0, a0), int(h + 60), passo):
            y = self.y_de(a, h)
            if 0 <= y < PALCO_H:
                big = a % 50 == 0
                tela.ret(x, y, 9 if big else 5, 1, PRETO)
                tela.ret(x, y - 1, 9 if big else 5, 1, BRANCO if big else cor)
                if big: tela.texto(f"{a} M", x + 12, y - 4, BRANCO, tam=9, contorno=PRETO)

    def desenhar(self, tela, h, X, t, x1=W):
        self.ceu(tela, h, t, x1)
        self.nuvens_(tela, h, X, t, x1)
        self.chao(tela, h, X, t, x1)
        self.arvores_(tela, h, X, x1)


# =================================================================== o voo
G = 9.81
RHO0, T0 = 1.204, 293.15                # ar a 20 °C (densidade do ar, F2)


def ar_fora(h):
    """Atmosfera padrão a partir de 20 °C no chão: temperatura (K) e densidade."""
    Ta = T0 - .0065 * h
    return Ta, RHO0 * (Ta / T0) ** 4.256


def empuxo_kg(Tin, h=0.0, V=VOLUME):
    """Quanto o balão levanta (kg): ar de fora deslocado - ar quente de dentro."""
    Ta, rho = ar_fora(h)
    return V * rho * (1 - Ta / Tin)


class Voo:
    """Voo calculado. queim(tf, h, v, Tin) e vent(tf) em 0..1. Estado: h (m), v (m/s), T (K)."""
    M = 700.0                     # balão + cesto + gás + pessoas (kg)
    P = 2.0e6                     # calor útil de um jato do queimador (W)
    KP = .0029                    # perda de calor pelo tecido (1/s)
    KV = .045                     # perda extra com o paraquedas aberto (1/s)
    CDA = .5 * 240.0              # coeficiente de arrasto x área (m²)

    def __init__(self, dur, queim, vent, h0=0.0, v0=0.0, Tin0=365.0, dt=.05):
        h, v, Tin = h0, v0, Tin0
        rows = []
        t = 0.0
        n = int(dur / dt) + 2
        for i in range(n):
            Ta, rho = ar_fora(h)
            m_in = VOLUME * rho * Ta / Tin
            L = empuxo_kg(Tin, h)
            q, ve = queim(t, h, v, Tin), vent(t)
            rows.append((t, h, v, Tin, L, q, ve))
            dT = q * self.P / (m_in * 1005.0) - (self.KP + self.KV * ve) * (Tin - Ta)
            Tin += dT * dt
            inercia = self.M + m_in + .5 * rho * VOLUME
            Fz = (L - self.M) * G - .5 * rho * self.CDA * v * abs(v)
            a = Fz / inercia
            v += a * dt
            h += v * dt
            if h <= 0:
                h = 0.0
                v = max(0.0, v)
            t += dt
        self.a = np.array(rows)
        self.dt = dt

    def q(self, tf):
        i = min(len(self.a) - 2, max(0, int(tf / self.dt)))
        u = min(1.0, max(0.0, (tf - i * self.dt) / self.dt))
        r = self.a[i] * (1 - u) + self.a[i + 1] * u
        return dict(t=tf, h=r[1], v=r[2], T=r[3] - 273.15, L=r[4], queim=self.a[i][5], vent=r[6])

    def fim(self):
        r = self.a[-1]
        return dict(h=r[1], v=r[2], Tin=r[3])
