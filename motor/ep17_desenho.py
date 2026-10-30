#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep17 — o desenho da fechadura de pinos (genérica, sem marca).

Toda peça é uma MÁSCARA (numpy) pintada por `pintar` (contorno escuro, chanfro
e brilho em dither, a luz vindo do alto à esquerda), o mesmo acabamento do ep09
(as funções de máscara e pintura foram copiadas para cá, para o episódio não
depender de outro).

O CILINDRO (vista lateral em corte) é uma conta só, `Cilindro`:

  corpo      parado; tem uma torre com 5 furos (câmaras) em cima do rotor
  rotor      o miolo que gira; a linha de corte é o topo dele (y = Y_S)
  chave      lâmina com 5 cortes em V (flancos a 45 graus); a altura da
             superfície em cada ponto é `superficie(segredo, u)`
  pilha      em cada furo, de baixo para cima: pino (ponta em V), às vezes um
             pino extra fino (chave mestra) e o contrapino; a mola empurra
             tudo para baixo
  contato    a ponta em V do pino desce até encostar na chave em algum ponto
             da sua largura: ponta = min(Y_TIP0, min_c (sup(u + c) + |c|));
             sem chave embaixo ele para em Y_TIP0 (preso pela mola)
  giro       o rotor só gira se em TODA pilha existe um vão exatamente em
             Y_S; o que está abaixo do vão gira junto (desenhado projetado:
             y' = yc + (y - yc) cos theta), o que está acima fica no corpo

Os comprimentos dos pinos saem da chave certa: pino = y_corte(d) - Y_S (a ponta
encosta no fundo do corte e o topo cai exatamente na linha). `checar()` confere
em números inteiros, para toda posição da chave, que: nenhum pino atravessa a
chave, nenhum pino desce além do batente, a mola nunca fica menor que 12 px,
sem chave todo contrapino cruza a linha, com a chave certa todos os vãos caem
EXATAMENTE na linha e com a errada não.
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)

# (contorno, escuro, médio, claro, especular)
MAT = {
    'latao':   (OLEO0, LATAO, OLEO1, AMARELO, CHAMA0),
    'corpo':   (OLEO0, BRASA, LATAO, OLEO1, AMARELO),
    'aco':     (PRETO, ACO1, ACO2, ACO3, ACO4),
    'acoesc':  (PRETO, ACO0, ACO1, ACO2, ACO3),
    'chave':   (PRETO, ACO2, ACO3, ACO4, BRANCO),
    'pino':    (OLEO0, OLEO1, AMARELO, CHAMA0, BRANCO),
    'contra':  (PRETO, FUNDO3, MISTURA, CIANO, MISTURA2),
    'extra':   (PRETO, ROXO, ROSA, ROSA, BRANCO),
    'madeira': (OLEO0, OLEO0, BRASA, LATAO, OLEO1),
    'porta':   (PRETO, BRASA, LATAO, OLEO1, AMARELO),
    'placa':   (PRETO, FUNDO2, FUNDO3, ACO0, ACO1),
    'verde':   (PRETO, AGUA0, AGUA1, VERDE, CHAMA0),
}


# ================================================================ máscara e pintura
class Mascara:
    """Tela de mentira para usar `poligono`/`linha_grossa` e ganhar uma máscara."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w), bool)

    def ret(self, x, y, w, h, cor=1):
        x0, y0 = max(0, int(round(x))), max(0, int(round(y)))
        x1, y1 = min(self.w, int(round(x + w))), min(self.h, int(round(y + h)))
        if x1 > x0 and y1 > y0: self.buf[y0:y1, x0:x1] = bool(cor)

    def disco(self, cx, cy, r, cor=1):
        x0, x1 = max(0, int(cx - r - 1)), min(self.w, int(cx + r + 2))
        y0, y1 = max(0, int(cy - r - 1)), min(self.h, int(cy + r + 2))
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        self.buf[y0:y1, x0:x1][(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = bool(cor)


def _erode(M):
    E = M.copy()
    E[1:] &= M[:-1]; E[:-1] &= M[1:]; E[:, 1:] &= M[:, :-1]; E[:, :-1] &= M[:, 1:]
    E[0, :] = E[-1, :] = False; E[:, 0] = E[:, -1] = False
    return E


def pintar(tela, M, x0, y0, mat, cx=None, cy=None, R=None, contorno=True, chanfro=True, brilho=True, cor_fixa=None):
    """Pinta a máscara M (h, w) com canto em (x0, y0) da tela."""
    h, w = M.shape
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(tela.w, x0 + w), min(PALCO_H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    M = np.pad(M, 1)
    c_out, c_esc, c_med, c_cla, c_esp = MAT[mat]
    out = np.full(M.shape, c_med if cor_fixa is None else cor_fixa, np.uint8)
    yy, xx = np.mgrid[-1:h + 1, -1:w + 1]
    xx = xx + x0; yy = yy + y0
    chk = (xx + yy) % 2 == 0
    if brilho and cor_fixa is None:
        if cx is None:
            ys, xs = np.nonzero(M)
            cx, cy = x0 - 1 + xs.mean(), y0 - 1 + ys.mean()
            R = max(3.0, max(np.ptp(xs), np.ptp(ys)) / 2)
        g = (-(xx - cx) - (yy - cy)) / (R * 1.41)
        out[(g > .22) & chk] = c_cla
        out[g > .52] = c_cla
        out[(g > .78) & chk] = c_esp
        out[(g < -.30) & chk] = c_esc
        out[g < -.60] = c_esc
    E1 = _erode(M)
    if chanfro:
        cima = E1 & ~np.roll(E1, 1, 0); esq = E1 & ~np.roll(E1, 1, 1)
        baixo = E1 & ~np.roll(E1, -1, 0); dir_ = E1 & ~np.roll(E1, -1, 1)
        out[baixo | dir_] = c_esc
        out[cima | esq] = c_esp if cor_fixa is None else c_cla
    if contorno:
        out[M & ~E1] = c_out
    out = out[1:-1, 1:-1]; M = M[1:-1, 1:-1]
    sub = tela.buf[Y0:Y1, X0:X1]
    m = M[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    sub[m] = out[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]


def pintar_tela(tela, Mk, mat, **kw):
    """Pinta uma Mascara do tamanho da tela (recorta a caixa primeiro)."""
    ys, xs = np.nonzero(Mk.buf)
    if len(xs) == 0: return
    a, b, c, d = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pintar(tela, Mk.buf[a:b, c:d], int(c), int(a), mat, **kw)


def pintar_faixas(tela, Mk, mat, y0, y1):
    """Cilindro deitado (o rotor, a lâmina): faixas horizontais de luz, claro
    no terço de cima, escuro embaixo, com dither nas passagens."""
    ys, xs = np.nonzero(Mk.buf)
    if len(xs) == 0: return
    c_out, c_esc, c_med, c_cla, c_esp = MAT[mat]
    u = (ys - y0) / max(1.0, (y1 - y0))
    chk = (xs + ys) % 2 == 0
    cor = np.full(len(xs), c_med, np.uint8)
    cor[(u < .42) & chk] = c_cla
    cor[(u > .14) & (u < .30)] = c_cla
    cor[(u > .18) & (u < .25) & chk] = c_esp
    cor[(u > .66) & chk] = c_esc
    cor[u > .82] = c_esc
    E = _erode(Mk.buf)
    borda = Mk.buf & ~E
    cor[borda[ys, xs]] = c_out
    ok = ys < PALCO_H
    tela.buf[ys[ok], xs[ok]] = cor[ok]


def brilho(tela, x, y, r, cor=AMARELO, forca=1.0):
    """Halo pontilhado em volta de um ponto (só sobre o que é escuro)."""
    x0, x1 = max(0, int(x - r)), min(tela.w, int(x + r + 1))
    y0, y1 = max(0, int(y - r)), min(PALCO_H, int(y + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / max(r, 1e-3)
    sub = tela.buf[y0:y1, x0:x1]
    escuro = sub <= TRACO
    bay = ((xx * 3 + yy * 5) % 4) / 4.0
    m = escuro & (d < 1) & ((1 - d) * forca > bay)
    sub[m] = cor


def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com quadradinho na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.ret(int(x1) - 1, int(y1) - 1, 3, 3, PRETO)
    tela.px(x1, y1, cor)


def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def barra(tela, x, y, w, h, frac, cor, fundo=FUNDO2):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, fundo)
    n = int(round(w * max(0.0, min(1.0, frac))))
    if n > 0:
        tela.ret(x, y, n, h, cor)
        tela.ret(x, y, n, 1, BRANCO if cor in (AMARELO, CIANO, VERDE) else CHAMA0)


def seta(tela, x, y, dx, dy, cor, tam=5):
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if dy: tela.ret(x - w // 2, y + (k if dy > 0 else -k), w, 1, cor)
        else: tela.ret(x + (k if dx > 0 else -k), y - w // 2, 1, w, cor)


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def fundo_bancada(tela):
    """Bancada do chaveiro: azul escuro com grade fina."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24):
        tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24):
        tela.ret(0, y, W, 1, FUNDO2)


def rot_pts(pts, cx, cy, ang):
    """Gira pontos em volta de (cx, cy); ang em graus, horário na tela."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]


def ret_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def mola(tela, x, y0, y1, amp=3.5, n=7, cor=ACO4, sombra=ACO1):
    """Mola em zigue-zague de y0 (presa em cima) a y1 (encosta no contrapino)."""
    if y1 - y0 < 2: return
    pts = [(x, y0)]
    for k in range(1, 2 * n):
        pts.append((x + (amp if k % 2 else -amp), y0 + (y1 - y0) * k / (2 * n)))
    pts.append((x, y1))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        tela.linha(ax + 1, ay + 1, bx + 1, by + 1, sombra)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        tela.linha(ax, ay, bx, by, cor)
    tela.ret(int(x - amp), int(y1) - 1, int(2 * amp) + 1, 1, cor)


# ================================================================ o cilindro
CERTA = [5, 8, 3, 7, 4]          # alturas (0 = sem corte) da chave certa
ERRADA = [5, 4, 3, 9, 4]         # 3 de 5 iguais: o 2º raso demais, o 4º fundo demais
MESTRA = [5, 5, 3, 4, 4]         # a chave mestra: difere da certa no 2º e no 4º
LISA = [0, 0, 0, 0, 0]           # chave virgem (sem corte)


class Cilindro:
    Y_S = 100                    # linha de corte (topo do rotor)
    Y_PB = 156                   # fundo do rotor
    Y_KW0, Y_KW1 = 116, 150      # o rasgo da chave (o "buraco" dentro do rotor)
    Y_KT = 118                   # topo da lâmina sem corte
    Y_KB = 148                   # fundo da lâmina
    Y_TIP0 = 140                 # sem chave, a ponta do pino para aqui
    Y_CT = 42                    # teto das câmaras (onde a mola se apoia)
    STEP = 2                     # px por altura de corte
    L_D = 24                     # contrapino
    PW = 9                       # largura do pino
    CW = 11                      # largura do furo

    def __init__(self, x0, passo, segredo=CERTA, mestra=None):
        self.x0, self.passo = x0, passo
        self.X = [x0 + 40 + passo * i for i in range(5)]
        self.xp1 = self.X[-1] + 34                       # fim do rotor
        self.u = [X - x0 for X in self.X]                # posição de cada corte na chave
        self.u_tip = self.u[-1] + 30
        self.yc = (self.Y_S + self.Y_PB) / 2.0
        self.R = (self.Y_PB - self.Y_S) / 2.0
        self.set_pinos(segredo, mestra)

    def set_pinos(self, segredo, mestra=None):
        """Pilhas a partir da chave certa (e da mestra, se houver): de baixo
        para cima, os comprimentos das peças abaixo do contrapino."""
        self.segredo, self.mestra = list(segredo), (list(mestra) if mestra else None)
        self.pilhas = []
        for i, d in enumerate(segredo):
            g = self.y_corte(d) - self.Y_S
            if mestra and mestra[i] != d:
                gm = self.y_corte(mestra[i]) - self.Y_S
                a, b = sorted((g, gm))
                self.pilhas.append([a, b - a])           # pino + pino extra
            else:
                self.pilhas.append([g])

    def y_corte(self, d):
        return self.Y_KT + self.STEP * d

    # ---------------------------------------------------------- a chave
    def superficie(self, seg, u):
        """Altura (y da tela) da superfície de cima da lâmina na posição u
        (px a partir do encosto). NaN = não tem chave ali."""
        u = np.asarray(u, float)
        y = np.full(u.shape, float(self.Y_KT))
        for i, d in enumerate(seg):
            if d is None or d <= 0: continue
            yc = self.y_corte(d)
            y = np.maximum(y, yc - np.maximum(0.0, np.abs(u - self.u[i]) - 1.5))
        n0 = self.u_tip - 24
        y = np.maximum(y, np.where(u > n0, self.Y_KT + (u - n0) * (self.Y_TIP0 + 4 - self.Y_KT) / 24.0, -1e9))
        return np.where((u < 0) | (u > self.u_tip), np.nan, y)

    def ponta(self, seg, i, o):
        """y da ponta do pino i com a chave `seg` recuada `o` px (0 = toda dentro)."""
        if seg is None: return float(self.Y_TIP0)
        c = np.arange(-4.5, 4.51, .25)
        s = self.superficie(seg, self.u[i] + o + c)
        v = np.where(np.isnan(s), np.inf, s + np.minimum(np.abs(c), 4.0))
        return float(min(self.Y_TIP0, v.min()))

    def pilha(self, seg, i, o):
        """Fronteiras de baixo para cima: [ponta, vão(s)..., topo do contrapino]."""
        b = [self.ponta(seg, i, o)]
        for L in self.pilhas[i]:
            b.append(b[-1] - L)
        b.append(b[-1] - self.L_D)
        return b

    def vao_na_linha(self, b):
        """Índice da fronteira que está EXATAMENTE na linha (ou None)."""
        for k in range(1, len(b) - 1):
            if abs(b[k] - self.Y_S) < 1e-6: return k
        return None

    def no_lugar(self, seg, o):
        return [self.vao_na_linha(self.pilha(seg, i, o)) is not None for i in range(5)]

    def pode_girar(self, seg, o):
        return all(self.no_lugar(seg, o))

    # ---------------------------------------------------------- desenho (vista lateral, em corte)
    def desenhar(self, tela, seg=None, o=0.0, theta=0.0, linha=False, marcar=False, chave_mat='chave',
                 cabeca=True, cortes_brilho=None, so_corpo=False, vis=None, desl=None):
        """`vis`: conjunto do que aparece ('corpo', 'rotor', 'pinos', 'contra',
        'molas', 'linha') para a montagem peça por peça; `desl`: deslocamento
        vertical de entrada de cada grupo."""
        vis = vis or {'corpo', 'rotor', 'pinos', 'contra', 'molas'}
        desl = desl or {}
        if theta and not self.pode_girar(seg, o):
            raise AssertionError('o rotor não pode girar com essa chave')
        c = math.cos(math.radians(theta))
        yc = self.yc
        P = lambda y: yc + (y - yc) * c
        x0, x1 = self.x0, self.xp1
        hw = self.CW / 2.0
        # ---- corpo
        if 'corpo' in vis:
            dy = desl.get('corpo', 0)
            Mk = Mascara()
            Mk.ret(x0, self.Y_S - 8 + dy, x1 - x0, self.Y_PB + 10 - (self.Y_S - 8))
            Mk.ret(self.X[0] - 18, self.Y_CT - 8 + dy, self.X[-1] - self.X[0] + 36, self.Y_S - self.Y_CT + 8)
            Mk.buf[int(self.Y_S + dy):int(self.Y_PB + dy), x0:x1] = False
            for X in self.X:
                Mk.buf[int(self.Y_CT + dy):int(self.Y_S + dy), int(round(X - hw)):int(round(X + hw))] = False
            pintar_tela(tela, Mk, 'latao', cx=(x0 + x1) / 2, cy=70 + dy, R=110)
            # tampinhas das câmaras e parafusos
            for X in self.X:
                tela.ret(int(X - hw) - 1, int(self.Y_CT - 6 + dy), self.CW + 2, 3, OLEO0)
                tela.ret(int(X - hw), int(self.Y_CT - 5 + dy), self.CW, 1, LATAO)
            for X in self.X:
                tela.ret(int(round(X - hw)), int(self.Y_CT + dy), self.CW, int(self.Y_S - self.Y_CT), FUNDO)
                tela.ret(int(round(X - hw)), int(self.Y_CT + dy), 1, int(self.Y_S - self.Y_CT), PRETO)
            tela.ret(x0, int(self.Y_S + dy), x1 - x0, int(self.Y_PB - self.Y_S), FUNDO)
        if so_corpo: return
        # ---- rotor
        if 'rotor' in vis:
            dy = desl.get('rotor', 0)
            dx = desl.get('rotor_x', 0)
            Mk = Mascara()
            Mk.ret(x0 + dx, self.Y_S + dy, x1 - x0, self.Y_PB - self.Y_S)
            pintar_faixas(tela, Mk, 'aco', self.Y_S + dy, self.Y_PB + dy)
            # frisos que andam quando o rotor gira (mostram o giro)
            for k in range(3):
                a = math.radians(theta + 40 + k * 110)
                if math.sin(a) <= 0.05:
                    yv = yc - self.R * math.cos(a) + dy
                    for x in range(x0 + 4 + dx, x1 - 3 + dx, 2):
                        tela.px(x, yv, ACO1)
            # flange da frente do rotor
            Mk = Mascara(); Mk.ret(x0 - 4 + dx, self.Y_S - 3 + dy, 5, self.Y_PB - self.Y_S + 6)
            pintar_tela(tela, Mk, 'aco')
            # rasgo da chave e furos dos pinos (giram com o rotor)
            a, b = sorted((P(self.Y_KW0), P(self.Y_KW1)))
            tela.ret(x0 + 1 + dx, int(round(a + dy)), x1 - x0 - 2, max(1, int(round(b - a))), FUNDO)
            tela.ret(x0 + 1 + dx, int(round(b + dy)), x1 - x0 - 2, 1, ACO0)
            if abs(c) > .3:
                for X in self.X:
                    a, b = sorted((P(self.Y_S), P(self.Y_KW0)))
                    tela.ret(int(round(X - hw)) + dx, int(round(a + dy)), self.CW, max(1, int(round(b - a))), FUNDO)
        # ---- came atrás (gira com o rotor)
        if 'rotor' in vis:
            dy = desl.get('rotor', 0)
            Mk = Mascara()
            Mk.ret(x1, yc - 6 + dy, 6, 12)
            ye = yc + 22 * c
            Mk.ret(x1 + 1, min(yc, ye) - 2 + dy, 5, abs(ye - yc) + 4)
            pintar_tela(tela, Mk, 'aco')
        # ---- chave
        if seg is not None:
            self.desenhar_chave(tela, seg, o, theta, mat=chave_mat, cabeca=cabeca, brilho_cortes=cortes_brilho)
        # ---- pinos
        for i in range(5):
            b = self.pilha(seg, i, o)
            k_v = self.vao_na_linha(b) if theta else None
            X = self.X[i]
            mats = ['pino'] + ['extra'] * (len(b) - 3) + ['contra']
            grupo = ['pinos'] + ['pinos'] * (len(b) - 3) + ['contra']
            for j in range(len(b) - 1):
                if grupo[j] not in vis: continue
                yb, yt = b[j], b[j + 1]
                dy = desl.get(grupo[j], 0)
                gira = theta and k_v is not None and j < k_v
                if gira:
                    yb, yt = P(yb), P(yt)
                    if abs(c) < .3: continue
                Mk = Mascara()
                pw = self.PW / 2.0
                if j == 0:
                    tip = 4 * (abs(c) if gira else 1)
                    poligono(Mk, [(X - pw, yt + dy), (X + pw, yt + dy), (X + pw, yb - tip + dy), (X + .5, yb + dy),
                                  (X - .5, yb + dy), (X - pw, yb - tip + dy)], 1)
                else:
                    Mk.ret(X - pw, yt + dy, self.PW, max(1, yb - yt))
                pintar_tela(tela, Mk, mats[j], cx=X - 2, cy=(yb + yt) / 2 - 3 + dy, R=max(6, (yb - yt) / 2 + 2))
            if 'molas' in vis:
                dy = desl.get('molas', 0)
                mola(tela, X, self.Y_CT + dy, b[-1] + dy)
        # ---- linha de corte
        if linha:
            for x in range(x0 - 6, x1 + 8, 4):
                tela.ret(x, self.Y_S, 2, 1, CIANO)
        if marcar:
            self.marcas(tela, seg, o)

    def marcas(self, tela, seg, o):
        """Cada pilha: verde se tem vão na linha; vermelho no pedaço que cruza."""
        for i in range(5):
            b = self.pilha(seg, i, o)
            X = self.X[i]
            if self.vao_na_linha(b) is not None:
                tela.ret(X - 6, self.Y_S - 1, 13, 2, VERDE)
                tela.px(X - 7, self.Y_S - 1, PRETO); tela.px(X + 7, self.Y_S - 1, PRETO)
            else:
                for j in range(len(b) - 1):
                    if b[j + 1] < self.Y_S < b[j]:
                        brilho(tela, X, self.Y_S, 9, VERMELHO, 1.0)
                        tela.ret(X - 6, self.Y_S - 1, 13, 2, VERMELHO)

    def desenhar_chave(self, tela, seg, o, theta=0.0, mat='chave', cabeca=True, brilho_cortes=None):
        c = math.cos(math.radians(theta))
        yc = self.yc
        P = lambda y: yc + (y - yc) * c
        xs0 = self.x0 - o                               # encosto da chave
        xa, xb = int(math.floor(xs0)), int(math.ceil(xs0 + self.u_tip))
        Mk = Mascara()
        cols = np.arange(max(0, xa), min(W, xb + 1))
        if len(cols):
            top = self.superficie(seg, cols + .5 - xs0)
            for x, tp in zip(cols, top):
                if np.isnan(tp): continue
                a, b = sorted((P(tp), P(self.Y_KB)))
                y0, y1 = int(round(a)), int(round(b))
                if y1 > y0: Mk.buf[max(0, y0):min(H, y1), x] = True
        if cabeca:
            # cabeça (a parte que a mão segura) e o ressalto do encosto
            a, b = sorted((P(self.Y_S + 2), P(self.Y_PB + 2)))
            Mk.ret(xs0 - 4, a, 4, max(1, b - a))
            a, b = sorted((P(self.Y_S - 12), P(self.Y_PB + 12)))
            Mk.ret(xs0 - 40, a + 3, 36, max(1, b - a - 6))
            Mk.ret(xs0 - 37, a, 30, max(1, b - a))
        pintar_faixas(tela, Mk, mat, P(self.Y_S - 12) if c >= 0 else P(self.Y_PB + 12),
                      P(self.Y_PB + 12) if c >= 0 else P(self.Y_S - 12))
        if cabeca and abs(c) > .25:
            # furo da argola e o sulco do perfil ao longo da lâmina
            tela.disco(xs0 - 26, yc, 6 * abs(c) + .5, FUNDO)
            tela.anel(xs0 - 26, yc, 6 * abs(c) + .5, PRETO)
        if abs(c) > .25:
            yv = int(round(P(140)))
            x_a, x_b = int(max(xs0 + 2, self.x0 - 200)), int(xs0 + self.u_tip - 26)
            if x_b > x_a:
                tela.ret(x_a, yv, x_b - x_a, 1, ACO2)
                tela.ret(x_a, yv + 1, x_b - x_a, 1, ACO4)
        if brilho_cortes:
            for i, f in brilho_cortes.items():
                if f > 0:
                    x = xs0 + self.u[i]
                    brilho(tela, x, P(self.y_corte(seg[i])) + 2, 8, AMARELO, f)

    # ---------------------------------------------------------- vista de frente (corte por uma pilha)
    def desenhar_frente(self, tela, cx, cy, esc, i, seg, o=0.0, theta=0.0, came=False, linha=True):
        """O mesmo cilindro visto de frente, cortado no furo i: o rotor é um
        círculo, a torre com a câmara fica em cima. Mesmas alturas da vista
        lateral, em escala `esc`."""
        if theta and not self.pode_girar(seg, o):
            raise AssertionError('o rotor não pode girar com essa chave')
        yc = self.yc
        S = lambda y: cy + (y - yc) * esc               # altura lateral -> tela
        R = self.R * esc
        hw = self.CW / 2.0 * esc
        # corpo: círculo + torre
        Mk = Mascara()
        Mk.disco(cx, cy, R + 9 * esc)
        Mk.ret(cx - 15 * esc, S(self.Y_CT - 8), 30 * esc, cy - S(self.Y_CT - 8))
        pintar_tela(tela, Mk, 'latao', cx=cx - 8, cy=cy - 20, R=R * 1.6)
        tela.ret(int(round(cx - hw)), int(round(S(self.Y_CT))), int(round(2 * hw)),
                 int(round(S(self.Y_S) - S(self.Y_CT))) + 1, FUNDO)
        tela.disco(cx, cy, R + .5, FUNDO)
        if came:
            # came atrás do rotor: um dente que gira junto (aparece fora do círculo)
            Mk = Mascara()
            pts = rot_pts(ret_pts(cx - 4 * esc, cy, cx + 4 * esc, cy + R + 14 * esc), cx, cy, theta)
            poligono(Mk, pts, 1)
            Mk.disco(cx, cy, R + 2)
            pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=R + 14 * esc)
        # rotor
        Mk = Mascara(); Mk.disco(cx, cy, R)
        pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=R)
        # rasgo + furo do pino, girando
        kw = 7 * esc
        pts = rot_pts(ret_pts(cx - kw, S(self.Y_KW0), cx + kw, S(self.Y_KW1)), cx, cy, theta)
        poligono(tela, pts, FUNDO)
        pts = rot_pts(ret_pts(cx - hw, S(self.Y_S) - 1, cx + hw, S(self.Y_KW0) + 1), cx, cy, theta)
        poligono(tela, pts, FUNDO)
        # lâmina da chave (corte): do topo neste furo até o fundo, com o sulco
        if seg is not None:
            tp = self.superficie(seg, np.array([self.u[i] + o]))[0]
            if not np.isnan(tp):
                Mk = Mascara()
                poligono(Mk, rot_pts(ret_pts(cx - 3.5 * esc, S(tp), cx + 3.5 * esc, S(self.Y_KB)), cx, cy, theta), 1)
                poligono(Mk, rot_pts(ret_pts(cx - 4.5 * esc, S(tp) + 3 * esc, cx + 4.5 * esc, S(self.Y_KB) - 2 * esc),
                                     cx, cy, theta), 1)
                pintar_tela(tela, Mk, 'chave')
                g = rot_pts([(cx + 3.5 * esc, S(140))], cx, cy, theta)[0]
                tela.disco(g[0], g[1], 1.6 * esc, FUNDO)
        # pilha
        b = self.pilha(seg, i, o)
        k_v = self.vao_na_linha(b) if theta else None
        mats = ['pino'] + ['extra'] * (len(b) - 3) + ['contra']
        pw = self.PW / 2.0 * esc
        for j in range(len(b) - 1):
            yb, yt = S(b[j]), S(b[j + 1])
            gira = theta and k_v is not None and j < k_v
            tip = 4 * esc if j == 0 else 0
            pts = [(cx - pw, yt), (cx + pw, yt), (cx + pw, yb - tip), (cx, yb), (cx - pw, yb - tip)]
            if gira: pts = rot_pts(pts, cx, cy, theta)
            Mk = Mascara(); poligono(Mk, pts, 1)
            pintar_tela(tela, Mk, mats[j])
        mola(tela, cx, S(self.Y_CT), S(b[-1]), amp=3.0 * esc + .5, n=6)
        if linha:
            for k in range(0, 360, 12):
                a = math.radians(k)
                tela.px(cx + math.cos(a) * (R + .5), cy + math.sin(a) * (R + .5), CIANO)

    # ---------------------------------------------------------- âncoras para rótulos
    def ancoras(self):
        X = self.X
        return dict(corpo=(X[0] - 14, self.Y_CT + 6), rotor=(self.x0 + 10, self.Y_PB - 8),
                    pino=(X[1], 128), contra=(X[2], 86), mola=(X[3], 58),
                    linha=(X[4] + 18, self.Y_S), came=(self.xp1 + 4, self.yc + 18),
                    rasgo=(self.x0 + 12, 146))


def checar(C=None):
    """Confere a geometria do cilindro em números (ver o cabeçalho)."""
    for C in ([C] if C else [Cilindro(40, 36), Cilindro(62, 26)]):
        C.set_pinos(CERTA)
        # sem chave: todo contrapino cruza a linha, mola folgada
        for i in range(5):
            b = C.pilha(None, i, 0)
            assert b[-2] > C.Y_S + 2 and b[-1] < C.Y_S - 4, ('sem chave', i, b)
        # chave certa toda dentro: todos os vãos EXATAMENTE na linha
        assert C.pode_girar(CERTA, 0.0)
        assert not C.pode_girar(CERTA, 2.5)
        assert sum(C.no_lugar(ERRADA, 0.0)) == 3 and not C.pode_girar(ERRADA, 0.0)
        assert sum(C.no_lugar(LISA, 0.0)) == 0
        for k in range(6):
            corte = [CERTA[j] if j < k else 0 for j in range(5)]
            assert sum(C.no_lugar(corte, 0.0)) == k, (k, corte)
        # para toda posição: o pino nunca atravessa a chave nem passa do batente; mola >= 12 px
        for seg in (CERTA, ERRADA, LISA, MESTRA):
            for o in np.arange(0, C.u_tip + C.x0 + 30, .5):
                for i in range(5):
                    b = C.pilha(seg, i, o)
                    assert b[0] <= C.Y_TIP0 + 1e-9
                    cc = np.arange(-4.5, 4.51, .25)
                    s = C.superficie(seg, C.u[i] + o + cc)
                    fundo_pino = np.where(np.abs(cc) <= 4, b[0] - np.abs(cc), b[0] - 4)
                    ok = np.isnan(s) | (fundo_pino <= s + 1e-6)
                    assert ok.all(), ('pino atravessa a chave', seg, o, i)
                    assert b[-1] - C.Y_CT >= 12, ('mola curta', seg, o, i, b)
        # chave mestra: as duas chaves giram o mesmo rotor
        C.set_pinos(CERTA, MESTRA)
        assert C.pode_girar(CERTA, 0.0) and C.pode_girar(MESTRA, 0.0) and not C.pode_girar(ERRADA, 0.0)
        for i in range(5):
            b = C.pilha(None, i, 0)
            assert b[-2] > C.Y_S + 2 and b[-1] < C.Y_S - 4
        C.set_pinos(CERTA)
    return True


# ================================================================ a caixa da fechadura (vista de frente)
class Caixa:
    """Fechadura de embutir genérica, vista de frente com a tampa aberta:
    o cilindro no meio, o came que gira com o rotor e a lingueta (sem mola)
    embaixo dele, e o trinco (com mola, ponta inclinada) em cima, puxado pela
    maçaneta. A lingueta só anda quando a ponta do came está dentro do dente
    dela (|phi| < PHI_ENG em volta de 'para baixo'): x = r sen(phi)."""
    PHI_ENG = 53.0

    def __init__(self, x0=52, y0=18, larg=164, alt=176):
        self.x0, self.y0, self.larg, self.alt = x0, y0, larg, alt
        self.xt = x0 + larg                         # testa (a placa da borda da porta)
        self.cc = (x0 + 62, y0 + 104)               # centro do cilindro
        self.rc = 20                                # raio do came
        self.yl = self.cc[1] + self.rc + 4          # topo da lingueta
        self.mc = (x0 + 62, y0 + 40)                # cubo da maçaneta
        self.curso = 2 * self.rc * math.sin(math.radians(self.PHI_ENG))

    def lingueta(self, phi):
        """Deslocamento da lingueta (0 = recolhida) para o came no ângulo phi
        (graus; 0 = para baixo; positivo = sentido de trancar)."""
        p = max(-self.PHI_ENG, min(self.PHI_ENG, phi))
        return self.rc * (math.sin(math.radians(p)) + math.sin(math.radians(self.PHI_ENG)))

    def desenhar(self, tela, phi, trinco=0.0, macaneta=0.0, rotulos=None, chave=True):
        """phi: ângulo do came; trinco: 0 (pra fora) a 1 (recolhido)."""
        x0, y0, L, A = self.x0, self.y0, self.larg, self.alt
        # caixa (fundo de chapa)
        Mk = Mascara(); Mk.ret(x0, y0, L, A)
        pintar_tela(tela, Mk, 'placa', brilho=False)
        for yy in range(y0 + 6, y0 + A - 4, 8):
            tela.ret(x0 + 4, yy, L - 8, 1, FUNDO2)
        # testa
        Mk = Mascara(); Mk.ret(self.xt, y0 - 10, 7, A + 20)
        pintar_tela(tela, Mk, 'latao')
        for yy in (y0 - 4, y0 + A + 2):
            tela.disco(self.xt + 3, yy, 2, OLEO0)
        # ---- trinco (em cima)
        ty = self.mc[1] - 6
        ex = 26 * (1 - trinco)
        xe = self.xt + 7 + ex - 26 + 22
        Mk = Mascara()
        Mk.ret(self.mc[0] + 14, ty + 2, xe - (self.mc[0] + 14) - 12, 8)
        poligono(Mk, [(xe - 14, ty - 2), (xe, ty - 2), (xe - 12 + 14 - 2, ty + 10 + 4), (xe - 14, ty + 14)], 1)
        Mk.ret(xe - 14, ty - 2, 4, 16)
        cl = (xe - 14 - (self.mc[0] + 14))
        pintar_tela(tela, Mk, 'latao')
        # mola do trinco (atrás, comprime quando ele recolhe)
        mx0 = self.mc[0] + 16
        mx1 = xe - 16
        if mx1 > mx0 + 2:
            n = 6
            pts = [(mx0 + (mx1 - mx0) * k / (2 * n), ty + 6 + (3 if k % 2 else -3)) for k in range(2 * n + 1)]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                tela.linha(ax, ay - 8, bx, by - 8, ACO4)
        # cubo da maçaneta (quadrado que gira) e a alavanca que puxa o trinco
        a = -35 * macaneta
        Mk = Mascara()
        poligono(Mk, rot_pts(ret_pts(self.mc[0] - 9, self.mc[1] - 9, self.mc[0] + 9, self.mc[1] + 9), *self.mc, a), 1)
        Mk.disco(*self.mc, 10)
        pintar_tela(tela, Mk, 'aco')
        q = rot_pts(ret_pts(self.mc[0] - 4, self.mc[1] - 4, self.mc[0] + 4, self.mc[1] + 4), *self.mc, a)
        poligono(tela, q, FUNDO)
        p1 = rot_pts([(self.mc[0] + 2, self.mc[1] - 16)], *self.mc, a)[0]
        Mk = Mascara(); linha_grossa(Mk, self.mc[0], self.mc[1], p1[0], p1[1], 5, 1)
        pintar_tela(tela, Mk, 'aco')
        # ---- lingueta (embaixo do cilindro)
        d = self.lingueta(phi)
        xl0 = self.cc[0] - 34 + d
        xl1 = self.xt + 7 - self.curso + d + 2
        Mk = Mascara()
        Mk.ret(xl0, self.yl, xl1 - xl0, 22)
        pintar_tela(tela, Mk, 'aco', cx=xl0 + 30, cy=self.yl, R=60)
        # o dente onde o came engancha
        nx = self.cc[0] + d - self.rc * math.sin(math.radians(self.PHI_ENG))
        tela.ret(int(nx + self.rc * math.sin(math.radians(self.PHI_ENG)) - 4), self.yl, 9, 9, FUNDO)
        tela.ret(int(nx + self.rc * math.sin(math.radians(self.PHI_ENG)) - 4), self.yl + 9, 9, 1, ACO0)
        # guia (rasgo) da lingueta com o pino
        tela.ret(int(xl0 + 10), self.yl + 14, int(self.curso) + 8, 3, FUNDO)
        tela.disco(self.cc[0] - 24 + self.curso / 2 + 8, self.yl + 15, 2.5, ACO3)
        # ---- cilindro (frente) + came
        cx, cy = self.cc
        Mk = Mascara()
        tip = rot_pts([(cx, cy + self.rc + 3)], cx, cy, phi)[0]
        linha_grossa(Mk, cx, cy, tip[0], tip[1], 9, 1)
        Mk.disco(cx, cy, 12)
        pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=20)
        Mk = Mascara(); Mk.disco(cx, cy, 16); Mk.ret(cx - 8, cy - 30, 16, 20)
        pintar_tela(tela, Mk, 'latao')
        Mk = Mascara(); Mk.disco(cx, cy, 10)
        pintar_tela(tela, Mk, 'aco', cx=cx, cy=cy, R=10)
        pts = rot_pts(ret_pts(cx - 2, cy - 6, cx + 2, cy + 7), cx, cy, phi)
        poligono(tela, pts, FUNDO)
        if chave:
            pts = rot_pts(ret_pts(cx - 1, cy - 5, cx + 1, cy + 6), cx, cy, phi)
            poligono(tela, pts, ACO4)
        return d

    def ancoras(self, phi=0.0):
        d = self.lingueta(phi)
        return dict(cilindro=(self.cc[0] - 12, self.cc[1] - 12), came=(self.cc[0], self.cc[1] + 16),
                    lingueta=(self.xt + 2 + d - self.curso + 14, self.yl + 11), trinco=(self.xt + 4, self.mc[1]),
                    macaneta=(self.mc[0] - 8, self.mc[1] - 8), caixa=(self.x0 + 8, self.y0 + self.alt - 10))


def checar_caixa():
    K = Caixa()
    assert abs(K.lingueta(-90)) < 1e-9 and abs(K.lingueta(-K.PHI_ENG)) < 1e-9
    assert abs(K.lingueta(90) - K.curso) < 1e-9 and abs(K.lingueta(270) - K.curso) < 1e-9
    # fora do engate a ponta do came fica acima do topo da lingueta (não bate)
    for p in range(-180, 181):
        tip_y = K.cc[1] + (K.rc + 3) * math.cos(math.radians(p))
        if abs(p) > K.PHI_ENG + 4:
            assert tip_y < K.yl + 1, p
    return True


# ================================================================ a porta (vista de frente)
def porta(tela, x0, y0, larg, alt, cil_xy, mac_ang=0.0, raio_x=0.0):
    """Porta de madeira genérica com maçaneta de alavanca e o cilindro."""
    Mk = Mascara(); Mk.ret(x0 - 10, y0 - 10, larg + 20, alt + 10)
    pintar_tela(tela, Mk, 'placa', brilho=False)
    Mk = Mascara(); Mk.ret(x0, y0, larg, alt)
    pintar_tela(tela, Mk, 'porta', cx=x0 + 20, cy=y0 + 20, R=larg)
    for k, (a, b) in enumerate(((y0 + 14, y0 + 84), (y0 + 100, y0 + alt - 14))):
        tela.ret(x0 + 14, a, larg - 28, 1, OLEO0); tela.ret(x0 + 14, b, larg - 28, 1, OLEO1)
        tela.ret(x0 + 14, a, 1, b - a, OLEO0); tela.ret(x0 + larg - 15, a, 1, b - a, OLEO1)
    for yy in range(y0 + 4, y0 + alt, 6):
        tela.px(x0 + 6 + (yy * 7) % 5, yy, BRASA)
    cx, cy = cil_xy
    # espelho (placa) da maçaneta e do cilindro
    Mk = Mascara(); Mk.ret(cx - 7, cy - 44, 14, 58); Mk.disco(cx, cy - 37, 7); Mk.disco(cx, cy + 7, 7)
    pintar_tela(tela, Mk, 'aco')
    # alavanca
    a = mac_ang
    p0 = (cx, cy - 34)
    p1 = rot_pts([(cx - 34, cy - 34)], *p0, -a)[0]
    Mk = Mascara(); linha_grossa(Mk, p0[0], p0[1], p1[0], p1[1], 6, 1); Mk.disco(*p0, 5); Mk.disco(p1[0], p1[1], 3)
    pintar_tela(tela, Mk, 'chave')
    # miolo do cilindro com o buraco da chave
    tela.disco(cx, cy + 4, 5, PRETO); tela.disco(cx, cy + 4, 4, LATAO)
    tela.ret(cx - 1, cy + 1, 2, 7, PRETO); tela.disco(cx, cy + 2, 1.5, PRETO)


# ================================================================ a porta (vista de cima) com o trinco
class TrincoCima:
    """Vista de cima: a porta (uma placa grossa) fecha andando em +y contra o
    batente; o trinco sai da borda dela em +x. A face do trinco que chega
    primeiro (lado +y) é inclinada a 45 graus. O canto da contratesta
    (xL, yF..yF+3) tem que ficar fora do trinco: e <= xL - xd + (yc - (yd - 6))."""
    XD = 172                                     # borda da porta
    XL = 176                                     # face do batente
    YF = 80                                      # começo da contratesta
    E_MAX = 18
    W2 = 6                                       # meia largura do trinco

    def yd_fechado(self):
        return self.YF + 3 + 8

    def ext(self, yd, puxado=0.0):
        """Quanto o trinco sai (px) com a porta em yd e a maçaneta puxando `puxado` (0..1)."""
        e = self.E_MAX * (1 - puxado)
        for ycn in (self.YF, self.YF + 3):
            if yd - self.W2 <= ycn <= yd + self.W2:
                e = min(e, self.XL - self.XD + (ycn - (yd - self.W2)))
        return max(0.0, e)

    def bloqueia_abrir(self, yd, e):
        """Indo para trás (-y), a face reta encosta na contratesta se o trinco
        estiver para fora além da face do batente."""
        return e > self.XL - self.XD + .01 and yd - self.W2 >= self.YF + 3 - .01

    def desenhar(self, tela, yd, e, macaneta=0.0, lingueta=0.0):
        XD, XL, YF = self.XD, self.XL, self.YF
        # batente (parede) com o buraco da contratesta e o rebaixo (batente da porta)
        Mk = Mascara(); Mk.ret(XL, 20, 70, 170)
        Mk.buf[int(YF + 3):int(YF + 19), XL:XL + self.E_MAX + 4] = False
        Mk.buf[int(YF + 34):int(YF + 50), XL:XL + 26] = False
        pintar_tela(tela, Mk, 'madeira', cx=XL + 30, cy=40, R=90)
        Mk = Mascara(); Mk.ret(XD - 40, self.yd_fechado() + 14, XL - XD + 40 + 2, 0)
        # contratesta (chapa)
        Mk = Mascara(); Mk.ret(XL - 2, YF - 10, 3, 66); Mk.ret(XL - 6, YF - 10, 5, 3)
        pintar_tela(tela, Mk, 'aco')
        tela.ret(XL - 1, int(YF + 3), 3, 16, FUNDO)
        tela.ret(XL - 1, int(YF + 34), 3, 16, FUNDO)
        # batente de encosto (a porta para aqui)
        Mk = Mascara(); Mk.ret(XD - 60, self.yd_fechado() + 15 + 18, 64, 8)
        # porta (placa grossa)
        Mk = Mascara(); Mk.ret(10, yd - 15, XD - 10, 30)
        pintar_tela(tela, Mk, 'porta', cx=60, cy=yd - 10, R=80)
        for x in range(16, XD - 4, 9):
            tela.px(x, yd - 8 + (x * 3) % 7, BRASA)
        # trinco
        Mk = Mascara()
        poligono(Mk, [(XD - 20, yd - self.W2), (XD + e, yd - self.W2), (XD + e - 2 * self.W2, yd + self.W2),
                      (XD - 20, yd + self.W2)], 1)
        pintar_tela(tela, Mk, 'latao')
        # mola dele (dentro da porta)
        mola_h = 20 - (self.E_MAX - e) * .6
        for k in range(8):
            xk = XD - 22 - k * (mola_h / 8)
            tela.ret(int(xk), int(yd - 4), 1, 9, ACO4 if k % 2 else ACO2)
        # lingueta (embaixo, sem mola, só com a chave)
        yl = yd + 31
        if lingueta > 0 or True:
            Mk = Mascara(); Mk.ret(XD - 24, yd + 7, 24 + lingueta * 22, 6)
            # desenhada como chapa reta (vista de cima, embaixo do trinco)
        return yl

    def ancoras(self, yd, e):
        return dict(trinco=(self.XD + e - 4, yd - 4), contratesta=(self.XL, self.YF - 6),
                    batente=(self.XL + 40, 40), porta=(60, yd))


def checar_trinco():
    T = TrincoCima()
    yf = T.yd_fechado()
    # aberto, longe: todo para fora; passando pela contratesta: recolhe até a folga
    assert T.ext(20) == T.E_MAX
    assert min(T.ext(y) for y in np.arange(20, yf, .25)) <= T.XL - T.XD + 1e-9
    assert T.ext(yf) == T.E_MAX
    # trinco no buraco: cabe (y do trinco dentro do buraco da contratesta)
    assert yf - T.W2 >= T.YF + 3 and yf + T.W2 <= T.YF + 19
    assert T.bloqueia_abrir(yf, T.ext(yf)) and not T.bloqueia_abrir(yf, T.ext(yf, 1.0))
    return True


# ================================================================ fechadura egípcia de madeira
class Egipcia:
    """Fechadura de pinos de madeira (Britannica): um ferrolho de madeira com
    furos em cima; numa peça presa na porta, pinos caem nesses furos e prendem
    o ferrolho. A chave (uma barra com pinos em pé) entra por baixo no ferrolho
    oco e é ERGUIDA: os pinos sobem até o topo do ferrolho e ele desliza."""

    def __init__(self, x0=30, y0=60):
        self.x0, self.y0 = x0, y0
        self.furos = [x0 + 60 + 22 * k for k in range(4)]
        self.yf = y0 + 40                         # topo do ferrolho

    def desenhar(self, tela, chave_x, ergue, desliza):
        """chave_x: quanto a chave entrou (0..1); ergue: 0..1; desliza: px."""
        x0, y0 = self.x0, self.y0
        yf = self.yf
        # porta (tábuas) atrás
        Mk = Mascara(); Mk.ret(0, 10, 300, 190)
        pintar_tela(tela, Mk, 'madeira', brilho=False)
        for x in range(0, 300, 30):
            tela.ret(x, 10, 1, 190, OLEO0)
        # peça fixa (onde ficam os pinos), em cima do ferrolho
        Mk = Mascara(); Mk.ret(x0 + 40, y0 - 20, 110, 60)
        for X in self.furos: Mk.buf[int(y0 - 14):int(yf), X - 4:X + 5] = False
        pintar_tela(tela, Mk, 'porta', cx=x0 + 60, cy=y0 - 10, R=70)
        for X in self.furos:
            tela.ret(X - 4, int(y0 - 14), 9, int(yf - y0 + 14), OLEO0)
        # ferrolho (oco por baixo, com os furos)
        lift = 12 * ergue
        Mk = Mascara(); Mk.ret(x0 + desliza, yf, 250, 24)
        Mk.buf[int(yf + 14):int(yf + 24), int(x0 + desliza + 30):int(x0 + desliza + 200)] = False
        for X in self.furos:
            xx = int(X + desliza)
            Mk.buf[int(yf):int(yf + 14), xx - 4:xx + 5] = False
        pintar_tela(tela, Mk, 'madeira', cx=x0 + 100, cy=yf, R=120)
        # chave (barra com pinos em pé), entra por baixo, no oco
        kx = x0 - 160 + 190 * chave_x + desliza
        ky = yf + 20 - lift
        Mk = Mascara(); Mk.ret(kx, ky, 200, 6)
        for X in self.furos:
            px = X - x0 - 30 + kx - x0 + x0 + 30 - (x0 - 160 + 190) + x0 - x0
            px = kx + (X - (x0 - 160 + 190 + 0))
            Mk.ret(px - 3, ky - 6, 7, 6)
        pintar_tela(tela, Mk, 'latao')
        # pinos: caem nos furos do ferrolho; a chave ergue até o topo dele
        for k, X in enumerate(self.furos):
            base = yf + 13
            if chave_x >= .999:
                base = min(base, ky - 6)
            top = base - 26
            Mk = Mascara(); Mk.ret(X - 3, top, 7, base - top)
            pintar_tela(tela, Mk, 'porta')
        return ky

    def ancoras(self, desliza=0.0):
        return dict(pinos=(self.furos[1], self.y0 - 6), ferrolho=(self.x0 + 230 + desliza, self.yf + 10))


# ================================================================ chave tetra (corte)
def tetra_frente(tela, cx, cy, r, ang, cortes=(3, 6, 2, 5)):
    """Chave cruzada vista de frente: 4 lâminas, cada uma com o seu corte."""
    Mk = Mascara()
    for k in range(4):
        a = ang + 90 * k
        L = r - cortes[k] * 1.4
        pts = rot_pts(ret_pts(cx - 3.5, cy - L, cx + 3.5, cy), cx, cy, a)
        poligono(Mk, pts, 1)
    Mk.disco(cx, cy, 6)
    pintar_tela(tela, Mk, 'chave', cx=cx, cy=cy, R=r)
