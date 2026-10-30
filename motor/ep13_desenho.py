#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep13 — o desenho do motor elétrico (genérico, sem marca).

Toda peça é uma MÁSCARA (numpy) pintada por `pintar` (mesmo acabamento do
ep09: contorno escuro, chanfro claro em cima/à esquerda, escuro embaixo/à
direita e brilho em dither com a luz do alto à esquerda).

Convenções (valem para o episódio inteiro)
  ângulos   em graus, sentido MATEMÁTICO (y para cima): 0 = direita, 90 = alto.
            Ângulo crescendo = giro ANTI-HORÁRIO na tela.
  polos     NORTE = vermelho, SUL = azul.
  corrente  num fio visto em corte: ponto = saindo da tela, X = entrando.

O MOTOR DE CORRENTE CONTÍNUA em corte (`MotorCC`): norte à esquerda e sul à
direita, então o campo B aponta para a DIREITA. Força num fio: F = I L x B.
  fio com X (entrando, -z):  (-z) x (+x) = -y  -> força para BAIXO
  fio com ponto (saindo, +z): (+z) x (+x) = +y -> força para CIMA
O lado da bobina que está na metade ESQUERDA leva o X (desce) e o da direita
leva o ponto (sobe): a bobina gira ANTI-HORÁRIO. O comutador garante isso:
as escovas ficam em cima (-) e embaixo (+), e a metade do anel ligada a um
lado da bobina troca de escova quando esse lado passa pelo alto ou pelo pé
(bobina em pé, força de giro zero): a cada meia volta. O polo norte da
bobina (regra da mão direita) fica 90 graus à frente do lado com X; ele é
puxado para o sul do estator, à direita.

O MOTOR SEM ESCOVAS (`MotorBL`): 3 bobinas (A, B, C) em dentes opostos com
eixos em 90, 210 e 330 graus: ligar A, B, C em sequência anda o campo 120
graus no sentido anti-horário de cada vez. Bobina k com corrente positiva:
o dente em alfa_k vira SUL (puxa o norte do rotor para lá) e o oposto, NORTE.
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)

# (contorno, escuro, médio, claro, especular)
MAT = {
    'aco':    (PRETO, ACO1, ACO2, ACO3, ACO4),
    'acoesc': (PRETO, ACO0, ACO1, ACO2, ACO3),
    'ferro':  (PRETO, FUNDO3, ACO0, ACO1, ACO2),
    'cobre':  (OLEO0, LATAO, OLEO1, LARANJA, CHAMA1),
    'cobreq': (OLEO0, OLEO1, LARANJA, CHAMA1, CHAMA0),       # cobre com corrente (quente de brilho)
    'ima_n':  (PRETO, BRASA, CHAMA2, VERMELHO, ROSA),
    'ima_s':  (PRETO, FUNDO3, MISTURA, MISTURA2, BRANCO),
    'carvao': (PRETO, FUNDO, FUNDO3, TRACO, ACO0),
    'plast':  (PRETO, FUNDO2, FUNDO3, TRACO, ACO0),
    'branco': (PRETO, ACO2, ACO3, ACO4, BRANCO),
    'verde':  (PRETO, AGUA0, AGUA1, VERDE, BRANCO),
    'pneu':   (PRETO, PRETO, FUNDO2, FUNDO3, TRACO),
    'lataria': (PRETO, FUNDO3, MISTURA, MISTURA2, BRANCO),
    'vidro':  (PRETO, FUNDO2, TRACO, ACO0, ACO2),
}
COR_FASE = {'A': AMARELO, 'B': VERDE, 'C': ROSA}


def P(cx, cy, r, a):
    """Ponto no raio r e ângulo a (graus, sentido matemático) em volta de (cx, cy)."""
    ra = math.radians(a)
    return cx + r * math.cos(ra), cy - r * math.sin(ra)


# ================================================================ máscara e pintura (do ep09)
class Mascara:
    """Tela de mentira para usar `poligono`/`linha_grossa` e ganhar uma máscara."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w), bool)

    def ret(self, x, y, w, h, cor=1):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
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
            if len(xs) == 0: return
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


def pintar_pol(tela, pts, mat, **kw):
    Mk = Mascara(); poligono(Mk, pts, 1); pintar_tela(tela, Mk, mat, **kw)


def pintar_ret(tela, x, y, w, h, mat, **kw):
    Mk = Mascara(); Mk.ret(x, y, w, h); pintar_tela(tela, Mk, mat, **kw)


def pintar_disco(tela, cx, cy, r, mat, **kw):
    Mk = Mascara(); Mk.disco(cx, cy, r); pintar_tela(tela, Mk, mat, cx=cx, cy=cy, R=r, **kw)


def setor(cx, cy, r0, r1, a0, a1):
    """Máscara de um setor de anel (r0..r1, ângulos a0..a1 em graus matemáticos)."""
    x0, y0 = int(math.floor(cx - r1 - 2)), int(math.floor(cy - r1 - 2))
    n = int(2 * r1 + 5)
    yy, xx = np.mgrid[y0:y0 + n, x0:x0 + n]
    dx, dy = xx + .5 - cx - .5, -(yy + .5 - cy - .5)
    r = np.sqrt(dx * dx + dy * dy)
    th = np.degrees(np.arctan2(dy, dx))
    meio, larg = (a0 + a1) / 2.0, (a1 - a0) / 2.0
    d = (th - meio + 180) % 360 - 180
    return (r >= r0) & (r <= r1) & (np.abs(d) <= larg), x0, y0


def pintar_setor(tela, ox, oy, r0, r1, a0, a1, mat, **kw):
    M, x0, y0 = setor(ox, oy, r0, r1, a0, a1)
    pintar(tela, M, x0, y0, mat, **kw)


def brilho(tela, x, y, r, cor=AMARELO, forca=1.0):
    """Halo pontilhado em volta de um ponto (só sobre o que é escuro)."""
    x0, x1 = max(0, int(x - r)), min(tela.w, int(x + r + 1))
    y0, y1 = max(0, int(y - r)), min(PALCO_H, int(y + r + 1))
    if x1 <= x0 or y1 <= y0 or forca <= 0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / max(r, 1e-3)
    sub = tela.buf[y0:y1, x0:x1]
    escuro = sub <= TRACO
    bay = ((xx * 3 + yy * 5) % 4) / 4.0
    m = escuro & (d < 1) & ((1 - d) * forca > bay)
    sub[m] = cor


def fantasma(tela, desenho):
    """Desenha por cima em xadrez: metade dos pixels some e deixa ver o que está embaixo."""
    antes = tela.buf.copy()
    desenho()
    yy, xx = np.mgrid[0:tela.h, 0:tela.w]
    m = (xx + yy) % 2 == 0
    tela.buf[m] = antes[m]


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


# ================================================================ ajudas de texto e setas
def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com quadradinho na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.ret(x1 - 1, y1 - 1, 3, 3, PRETO)
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
    for k in range(1, 10):
        tela.px(x + w * k // 10, y + h - 1, PRETO)


def seta(tela, x0, y0, x1, y1, cor, cab=4, esp=1, contorno=True):
    """Seta de (x0, y0) até a ponta (x1, y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * cab * 1.6, y1 - uy * cab * 1.6
    cabeca = [(x1 + ux, y1 + uy), (bx - uy * cab, by + ux * cab), (bx + uy * cab, by - ux * cab)]
    if contorno:
        linha_grossa(tela, x0, y0, bx, by, esp + 2, PRETO)
        c2 = [(x1 + ux * 2.2, y1 + uy * 2.2), (bx - uy * (cab + 1.4) - ux, by + ux * (cab + 1.4) - uy),
              (bx + uy * (cab + 1.4) - ux, by - ux * (cab + 1.4) - uy)]
        poligono(tela, c2, PRETO)
    if esp <= 1: tela.linha(x0, y0, bx, by, cor)
    else: linha_grossa(tela, x0, y0, bx, by, esp, cor)
    poligono(tela, cabeca, cor)


def seta_arco(tela, cx, cy, r, a0, a1, cor, cab=4):
    """Arco com ponta de seta em a1 (sentido de a0 para a1)."""
    n = max(4, int(abs(a1 - a0) / 4))
    pts = [P(cx, cy, r, a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    for (ax, ay), (bx, by) in zip(pts[:-2], pts[1:-1]):
        linha_grossa(tela, ax, ay, bx, by, 3, PRETO)
    for (ax, ay), (bx, by) in zip(pts[:-2], pts[1:-1]):
        tela.linha(ax, ay, bx, by, cor)
    seta(tela, pts[-3][0], pts[-3][1], pts[-1][0], pts[-1][1], cor, cab=cab)


def fio_corte(tela, x, y, r, sinal, mat='cobre'):
    """Fio visto em corte. sinal > 0: corrente saindo da tela (ponto);
    sinal < 0: entrando (X); 0: sem corrente."""
    pintar_disco(tela, x, y, r, 'cobreq' if sinal else mat)
    if sinal > 0:
        tela.disco(x, y, max(1.2, r * .32), PRETO)
        tela.px(x, y, BRANCO)
    elif sinal < 0:
        k = max(1, int(r * .55))
        for d in range(-k, k + 1):
            tela.px(x + d, y + d, PRETO); tela.px(x + d, y - d, PRETO)


def fundo_oficina(tela, cor=FUNDO2):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24):
        tela.ret(x, 0, 1, PALCO_H, cor)
    for y in range(12, PALCO_H, 24):
        tela.ret(0, y, W, 1, cor)


# ================================================================ ímãs e linhas de campo
def ima_barra(tela, cx, cy, comp, alt, ang, letras=True, fantasma_=False):
    """Ímã em barra: metade NORTE (vermelha) para o lado de `ang`."""
    ux, uy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    vx, vy = -uy, ux
    h, a = comp / 2.0, alt / 2.0
    def q(s0, s1):
        return [(cx + ux * s0 + vx * a, cy + uy * s0 + vy * a), (cx + ux * s1 + vx * a, cy + uy * s1 + vy * a),
                (cx + ux * s1 - vx * a, cy + uy * s1 - vy * a), (cx + ux * s0 - vx * a, cy + uy * s0 - vy * a)]
    pintar_pol(tela, q(0, h), 'ima_n', cx=cx, cy=cy, R=h)
    pintar_pol(tela, q(-h, 0), 'ima_s', cx=cx, cy=cy, R=h)
    if letras:
        tam = 17 if alt >= 22 else 9
        dy = 7 if tam == 17 else 3
        tela.texto('N', cx + ux * h * .5, cy + uy * h * .5 - dy, BRANCO, tam=tam, centro=True, contorno=PRETO)
        tela.texto('S', cx - ux * h * .5, cy - uy * h * .5 - dy, BRANCO, tam=tam, centro=True, contorno=PRETO)


def linhas_dipolo(cx, cy, ang, Ls, meia, n=90):
    """Linhas de campo de um ímã (dipolo): r = L sen^2(phi) em volta do
    centro, phi contado a partir do NORTE. Devolve listas de pontos na ordem
    do campo (sai do norte, entra no sul)."""
    ux, uy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    vx, vy = -uy, ux
    out = []
    for L in Ls:
        for lado in (1, -1):
            pts = []
            for i in range(n + 1):
                phi = .03 + (math.pi - .06) * i / n
                r = L * math.sin(phi) ** 2
                u, v = r * math.cos(phi), lado * r * math.sin(phi)
                if abs(u) < meia[0] + 1 and abs(v) < meia[1] + 1: continue
                pts.append((cx + ux * u + vx * v, cy + uy * u + vy * v))
            if len(pts) > 3: out.append(pts)
    return out


def tracejar(tela, pts, t, cor=FUNDO3, cor2=CIANO, vel=14.0, passo=10.0, forca=1.0):
    """Linha de campo pontilhada com pontos claros andando no sentido do campo."""
    s = 0.0
    fase = (t * vel) % passo
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        k = 0.0
        while k < L:
            x, y = ax + (bx - ax) * k / L, ay + (by - ay) * k / L
            ss = s + k
            if 0 <= y < PALCO_H:
                if ((ss - fase) % passo) < 1.2 and forca > .5:
                    tela.px(x, y, cor2)
                elif int(ss) % 3 == 0 and forca > .2:
                    tela.px(x, y, cor)
            k += 1.0
        s += L


def bussola(tela, x, y, r, ang, cor_caixa='aco'):
    """Bússola: caixa redonda e agulha (ponta NORTE vermelha) apontando para `ang`."""
    pintar_disco(tela, x, y, r + 2, cor_caixa)
    tela.disco(x, y, r, FUNDO)
    tela.anel(x, y, r - 1, FUNDO3, .5)
    ux, uy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    vx, vy = -uy, ux
    L, wd = r - 1.5, max(1.6, r * .28)
    poligono(tela, [(x + ux * L, y + uy * L), (x + vx * wd, y + vy * wd), (x - vx * wd, y - vy * wd)], VERMELHO)
    poligono(tela, [(x - ux * L, y - uy * L), (x + vx * wd, y + vy * wd), (x - vx * wd, y - vy * wd)], ACO3)
    tela.px(x + ux * (L - 2), y + uy * (L - 2), ROSA)
    tela.px(x, y, PRETO)


# ================================================================ pilha
def pilha(tela, x, y, w, h, mais_em_baixo=True, brilho_=0.0):
    """Pilha em pé (corpo verde, tampa de metal). Devolve (ponto +, ponto -)."""
    pintar_ret(tela, x, y, w, h, 'verde')
    tela.ret(x + 1, y + h // 2 - 1, w - 2, 2, AGUA0)
    tb = 4
    if mais_em_baixo:
        pintar_ret(tela, x + w // 2 - 3, y + h - 1, 6, tb, 'aco')
        pintar_ret(tela, x + 2, y - 2, w - 4, 3, 'aco')
        tela.texto('+', x + w // 2, y + h - 12, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto('-', x + w // 2, y + 4, BRANCO, tam=9, centro=True, contorno=PRETO)
        mais, menos = (x + w // 2, y + h + tb - 1), (x + w // 2, y - 2)
    else:
        pintar_ret(tela, x + w // 2 - 3, y - tb + 1, 6, tb, 'aco')
        pintar_ret(tela, x + 2, y + h - 1, w - 4, 3, 'aco')
        mais, menos = (x + w // 2, y - tb + 1), (x + w // 2, y + h + 2)
    if brilho_ > 0: brilho(tela, x + w / 2, y + h / 2, w * 1.4, VERDE, brilho_)
    return mais, menos


def fio_eletrico(tela, pts, t, ativo=True, sentido=1, cor=OLEO1):
    """Fio de ligação (polilinha 2 px) com pontinhos de corrente andando."""
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        linha_grossa(tela, ax, ay, bx, by, 4, PRETO)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        linha_grossa(tela, ax, ay, bx, by, 2, cor)
    if not ativo: return
    s = 0.0
    fase = (t * 30.0 * sentido) % 12.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        k = 0.0
        while k < L:
            if ((s + k - fase) % 12.0) < 1.0:
                x, y = ax + (bx - ax) * k / L, ay + (by - ay) * k / L
                if 0 <= y < PALCO_H - 1: tela.ret(x - .5, y - .5, 2, 2, AMARELO)
            k += 1.0
        s += L


# ================================================================ motor de corrente contínua (em corte)
class MotorCC:
    """Estator de 2 ímãs, rotor de 1 bobina, comutador de 2 metades e 2 escovas."""
    def __init__(self, cx=140, cy=104, R=80):
        self.cx, self.cy, self.R = cx, cy, R
        self.rr = R * .56            # raio dos lados da bobina
        self.rc = 12                 # raio do comutador
        self._est = None

    # ------------------------------------------------ física (a mesma da legenda)
    @staticmethod
    def sinal_A(aA):
        """Corrente no lado A com comutador: X (entrando, -1) na metade
        esquerda, ponto (+1) na direita."""
        return -1 if math.cos(math.radians(aA)) < 0 else 1

    @staticmethod
    def torque(aA, sA):
        """Torque anti-horário (+) com o lado A em aA e corrente sA nele:
        tau = x * Fy; F do lado com X é para baixo."""
        return sA * math.cos(math.radians(aA))

    def ancoras(self, aA=180):
        cx, cy, R = self.cx, self.cy, self.R
        return {'estator': P(cx, cy, R * .88, 140), 'ima_n': P(cx, cy, R * .88, 200), 'ima_s': P(cx, cy, R * .88, -20),
                'rotor': P(cx, cy, self.rr, aA + 180), 'eixo': (cx + 3, cy - 3), 'comutador': P(cx, cy, self.rc, 30),
                'escovas': (cx + 3, cy - self.rc - 6), 'pilha': (24, 104)}

    def _estator(self, tela):
        cx, cy, R = self.cx, self.cy, self.R
        M, x0, y0 = setor(cx, cy, R, R + 8, -180, 180)
        pintar(tela, M, x0, y0, 'aco', cx=cx, cy=cy, R=R + 8)
        for x, y in (P(cx, cy, R + 4, 90 + 12), P(cx, cy, R + 4, 90 - 12), P(cx, cy, R + 4, 270 + 12), P(cx, cy, R + 4, 270 - 12)):
            tela.disco(x, y, 1.5, ACO0)

    def _imas(self, tela, desl=(0, 0)):
        cx, cy, R = self.cx + desl[0], self.cy + desl[1], self.R
        pintar_setor(tela, cx, cy, R * .78, R, 180 - 48, 180 + 48, 'ima_n', cx=cx - R * .5, cy=cy, R=R * .6)
        pintar_setor(tela, cx, cy, R * .78, R, -48, 48, 'ima_s', cx=cx + R * .5, cy=cy, R=R * .6)
        tela.texto('N', cx - R * .89, cy - 7, BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto('S', cx + R * .89, cy - 7, BRANCO, tam=17, centro=True, contorno=PRETO)

    def campo(self, tela, t, forca=1.0):
        """Linhas de campo do estator: do norte (esq.) para o sul (dir.)."""
        cx, cy, R = self.cx, self.cy, self.R
        r0 = R * .78 - 1
        for k in range(-4, 5):
            dy = k * 11
            if abs(dy) >= r0 * .7: continue
            half = math.sqrt(r0 * r0 - dy * dy)
            pts = [(cx - half, cy + dy), (cx + half, cy + dy)]
            tracejar(tela, pts, t + k * .13, FUNDO3, CIANO, vel=16, passo=11, forca=forca)

    def desenhar(self, tela, t, aA, sA=0, vis=None, desl=None, forca=True, polos=True, campo=True,
                 flash=0.0, escova_ok=True, pilha_on=True, comut_corte=True):
        """aA = ângulo do lado A da bobina; sA = corrente em A (+1 ponto, -1 X, 0 sem)."""
        cx, cy, R = self.cx, self.cy, self.R
        vis = vis if vis is not None else {'estator', 'rotor', 'eixo', 'comutador', 'escovas', 'pilha'}
        desl = desl or {}
        def d(nome): return desl.get(nome, (0, 0))
        if 'estator' in vis:
            dx, dy = d('estator')
            if dx == 0 and dy == 0:
                self._estator(tela)
            if campo: self.campo(tela, t, 1.0 if (dx, dy) == (0, 0) else 0.0)
            if dx or dy:
                M, x0, y0 = setor(cx + dx, cy + dy, R, R + 8, -180, 180)
                pintar(tela, M, x0, y0, 'aco', cx=cx + dx, cy=cy + dy, R=R + 8)
            self._imas(tela, (dx, dy))
        # ---- pilha e ligações (atrás do rotor? não: na frente, como fiação)
        top = (cx, cy - self.rc - 9)
        bot = (cx, cy + self.rc + 9)
        if 'pilha' in vis:
            dx, dy = d('pilha')
            on = pilha_on and (dx, dy) == (0, 0)
            mais, menos = pilha(tela, 14 + dx, 72 + dy, 18, 64, True, .3 if on else 0)
            if (dx, dy) == (0, 0) and 'escovas' in vis:
                fio_eletrico(tela, [mais, (mais[0], 201), (cx, 201), (cx, cy + R + 7)], t, on, 1)
                fio_eletrico(tela, [(cx, cy - R - 7), (cx, 7), (menos[0], 7), menos], t, on, 1)
        if 'escovas' in vis and d('escovas') == (0, 0):
            # porta-escovas: hastes de aço presas na carcaça, pelo vão entre os ímãs
            for y0_, y1_ in ((cy - R - 1, cy - self.rc - 10), (cy + self.rc + 10, cy + R + 1)):
                linha_grossa(tela, cx, y0_, cx, y1_, 5, PRETO)
                linha_grossa(tela, cx, y0_, cx, y1_, 3, ACO1)
                for yy in range(int(min(y0_, y1_)) + 3, int(max(y0_, y1_)) - 2, 4):
                    tela.px(cx, yy, ACO3)
        # ---- rotor (bobina vista de lado: os dois lados em corte)
        if 'rotor' in vis:
            dx, dy = d('rotor')
            ax, ay = P(cx + dx, cy + dy, self.rr, aA)
            bx, by = P(cx + dx, cy + dy, self.rr, aA + 180)
            tela.anel(cx + dx, cy + dy, self.rr, FUNDO3, .5)          # caminho dos lados da bobina
            Mk = Mascara(); linha_grossa(Mk, ax, ay, bx, by, 8, 1)
            pintar_tela(tela, Mk, 'cobreq' if sA else 'cobre', cx=cx + dx, cy=cy + dy, R=self.rr)
            # espiras: riscos atravessados na bobina
            ux, uy = (bx - ax) / (2 * self.rr), (by - ay) / (2 * self.rr)
            for k in range(-7, 8):
                if abs(k) < 2: continue
                x, y = P(cx + dx, cy + dy, k * self.rr / 8.0, aA)
                tela.linha(x - uy * 3, y + ux * 3, x + uy * 3, y - ux * 3, OLEO0)
            fio_corte(tela, ax, ay, 8, sA)
            fio_corte(tela, bx, by, 8, -sA)
            if flash > 0:
                brilho(tela, ax, ay, 16, AMARELO, flash); brilho(tela, bx, by, 16, AMARELO, flash)
            if polos and sA:
                mA = aA + 90 if sA < 0 else aA - 90
                nx, ny = P(cx + dx, cy + dy, 30, mA)
                sx, sy = P(cx + dx, cy + dy, 30, mA + 180)
                tela.disco(nx, ny, 6, PRETO); tela.disco(nx, ny, 5, VERMELHO)
                tela.texto('N', nx, ny - 3, BRANCO, tam=9, centro=True)
                tela.disco(sx, sy, 6, PRETO); tela.disco(sx, sy, 5, MISTURA)
                tela.texto('S', sx, sy - 3, BRANCO, tam=9, centro=True)
        if 'eixo' in vis:
            dx, dy = d('eixo')
            pintar_disco(tela, cx + dx, cy + dy, 6, 'aco')
            tela.px(cx + dx, cy + dy, PRETO)
        if 'comutador' in vis:
            dx, dy = d('comutador')
            gap = 16 if comut_corte else 0
            # metade ligada ao lado A fica em aA+90 (vai para a escova de baixo quando A está à esquerda)
            for k, meio in enumerate((aA + 90, aA - 90)):
                lado = 1 if k == 0 else -1          # 1 = ligada ao lado A
                M, x0, y0 = setor(cx + dx, cy + dy, 7.5, self.rc, meio - 90 + gap / 2, meio + 90 - gap / 2)
                pintar(tela, M, x0, y0, 'cobreq' if sA else 'cobre', cx=cx + dx, cy=cy + dy, R=self.rc)
            if not comut_corte:
                tela.anel(cx + dx, cy + dy, 9, LATAO, .8)
            pintar_disco(tela, cx + dx, cy + dy, 5, 'aco')
        if 'escovas' in vis:
            dx, dy = d('escovas')
            for yy, sgn in ((cy - self.rc - 10, -1), (cy + self.rc + 1, 1)):
                pintar_ret(tela, cx - 4 + dx, yy + dy, 9, 10, 'carvao')
                if (dx, dy) == (0, 0):
                    tela.texto('-' if sgn < 0 else '+', cx + 10, yy + 2, BRANCO, tam=9, contorno=PRETO)
            if escova_ok and sA and (dx, dy) == (0, 0):
                brilho(tela, cx, cy + self.rc + 1, 6, AMARELO, .5)
        self.ponta_forca = None
        if forca and sA and 'rotor' in vis:
            for (x, y), s in ((P(cx, cy, self.rr, aA), sA), (P(cx, cy, self.rr, aA + 180), -sA)):
                dirv = 1 if s < 0 else -1               # X desce, ponto sobe
                xs = x + (11 if x > cx else -11)
                seta(tela, xs, y, xs, y + dirv * 20, AMARELO, cab=4, esp=2)
                if x > cx: self.ponta_forca = (xs, y + dirv * 12)


# ================================================================ motor sem escovas / indução / trifásico
class MotorBL:
    FASES = (('A', 90.0), ('B', 210.0), ('C', 330.0))

    def __init__(self, cx=140, cy=104, R=80):
        self.cx, self.cy, self.R = cx, cy, R
        self.rr = R * .44
        self._cache = None

    def eixo_fase(self, k):
        return self.FASES[k][1]

    def _base(self, tela):
        """Carcaça e coroa de ferro (fixas): cacheadas."""
        cx, cy, R = self.cx, self.cy, self.R
        if self._cache is None:
            import pixelengine as PX
            import longo as LG
            T = PX.Tela(W, H, paleta=LG.PAL)
            T.buf[:] = 255
            M, x0, y0 = setor(cx, cy, R, R + 8, -180, 180)
            pintar(T, M, x0, y0, 'aco', cx=cx, cy=cy, R=R + 8)
            M, x0, y0 = setor(cx, cy, R * .86, R, -180, 180)
            pintar(T, M, x0, y0, 'ferro', cx=cx, cy=cy, R=R)
            for x, y in (P(cx, cy, R + 4, 45), P(cx, cy, R + 4, 135), P(cx, cy, R + 4, 225), P(cx, cy, R + 4, 315)):
                T.disco(x, y, 1.5, ACO0)
            self._cache = T.buf.copy()
        m = self._cache != 255
        tela.buf[m] = self._cache[m]

    def dente(self, tela, ang, polo, intens, cor_fase, t):
        """Dente com bobina. polo: +1 = vira SUL na face, -1 = NORTE, 0 = nada."""
        cx, cy, R = self.cx, self.cy, self.R
        r_in, r_out = R * .52, R * .87
        ux, uy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
        vx, vy = -uy, ux
        a = 6.0
        pts = [(cx + ux * r_in + vx * a, cy + uy * r_in + vy * a), (cx + ux * r_out + vx * a, cy + uy * r_out + vy * a),
               (cx + ux * r_out - vx * a, cy + uy * r_out - vy * a), (cx + ux * r_in - vx * a, cy + uy * r_in - vy * a)]
        mat_corpo = 'ferro'
        if intens > .55 and polo: mat_corpo = 'ima_s' if polo > 0 else 'ima_n'
        pintar_pol(tela, pts, mat_corpo, cx=cx, cy=cy, R=R)
        # sapata (a face que olha o rotor)
        mat_face = 'ferro'
        if intens > .15 and polo:
            mat_face = 'ima_s' if polo > 0 else 'ima_n'
        pintar_setor(tela, cx, cy, R * .47, R * .55, ang - 22, ang + 22, mat_face, cx=cx, cy=cy, R=R * .5)
        if .15 < intens < .55 and polo:
            # meio aceso: dither com o ferro
            M, x0, y0 = setor(cx, cy, R * .47 + 1, R * .55 - 1, ang - 20, ang + 20)
            hh, ww = M.shape
            yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + ww]
            m = M & ((xx + yy) % 2 == 0) & (yy >= 0) & (yy < PALCO_H) & (xx >= 0) & (xx < W)
            tela.buf[yy[m], xx[m]] = ACO0
        # bobina enrolada nos dois lados do dente
        q = intens > .55
        for lado in (1, -1):
            r0, r1 = R * .58, R * .82
            b = a + 1
            pts = [(cx + ux * r0 + vx * lado * b, cy + uy * r0 + vy * lado * b),
                   (cx + ux * r1 + vx * lado * b, cy + uy * r1 + vy * lado * b),
                   (cx + ux * r1 + vx * lado * (b + 6), cy + uy * r1 + vy * lado * (b + 6)),
                   (cx + ux * r0 + vx * lado * (b + 5), cy + uy * r0 + vy * lado * (b + 5))]
            pintar_pol(tela, pts, 'cobreq' if q else 'cobre', cx=cx, cy=cy, R=R)
            for k in range(5):
                rr = r0 + (r1 - r0) * (k + .5) / 5
                x, y = cx + ux * rr + vx * lado * (b + 3), cy + uy * rr + vy * lado * (b + 3)
                tela.px(x, y, OLEO0 if not q else LARANJA)
        if intens > .15 and polo:
            x, y = P(cx, cy, R * .70, ang)
            brilho(tela, x, y, 14 * min(1, intens + .2), cor_fase, .55 * intens)

    def desenhar(self, tela, t, rho, corr=(0, 0, 0), tipo='ima', campo=None, barras=None, sensor=None,
                 letras=True, borrao=False, so_estator=False):
        """rho = ângulo do NORTE do rotor; corr = correntes de A, B, C (-1..1);
        campo = (ângulo, tamanho 0..1) para a seta do campo."""
        cx, cy, R = self.cx, self.cy, self.R
        self._base(tela)
        for k, (nome, a) in enumerate(self.FASES):
            i = corr[k]
            pol = 1 if i > 0 else (-1 if i < 0 else 0)
            for aa, pp in ((a, pol), (a + 180, -pol)):
                self.dente(tela, aa, pp, abs(i), COR_FASE[nome], t)
        if letras:
            for k, (nome, a) in enumerate(self.FASES):
                for aa, suf in ((a, ''), (a + 180, "'")):
                    x, y = P(cx, cy, R * .93, aa)
                    tela.texto(nome + suf, x, y - 3, COR_FASE[nome] if abs(corr[k]) > .55 else ACO3, tam=9, centro=True, contorno=PRETO)
        if so_estator: return
        rr = self.rr
        if borrao:
            M, x0, y0 = setor(cx, cy, 0, rr, -180, 180)
            hh, ww = M.shape
            yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + ww]
            ok = M & (yy >= 0) & (yy < PALCO_H)
            cor = np.where((xx + yy) % 2 == 0, CHAMA2 if tipo == 'ima' else ACO1, MISTURA if tipo == 'ima' else ACO2)
            tela.buf[yy[ok], xx[ok]] = cor[ok]
            tela.anel(cx, cy, rr, PRETO, .7)
        elif tipo == 'ima':
            pintar_setor(tela, cx, cy, 0, rr, rho - 90, rho + 90, 'ima_n', cx=cx, cy=cy, R=rr)
            pintar_setor(tela, cx, cy, 0, rr, rho + 90, rho + 270, 'ima_s', cx=cx, cy=cy, R=rr)
            tela.anel(cx, cy, rr, PRETO, .6)
            x, y = P(cx, cy, rr * .58, rho)
            tela.texto('N', x, y - 3, BRANCO, tam=9, centro=True, contorno=PRETO)
            x, y = P(cx, cy, rr * .58, rho + 180)
            tela.texto('S', x, y - 3, BRANCO, tam=9, centro=True, contorno=PRETO)
            x, y = P(cx, cy, rr - 3, rho)
            tela.px(x, y, BRANCO)
        else:                                     # gaiola: ferro com barras
            pintar_disco(tela, cx, cy, rr, 'ferro')
            tela.anel(cx, cy, rr * .55, FUNDO3, .5)
            nb = 14
            for j in range(nb):
                a = rho + j * 360.0 / nb
                x, y = P(cx, cy, rr - 6, a)
                i = barras[j] if barras is not None else 0.0
                mat = 'aco'
                pintar_disco(tela, x, y, 3.2, 'aco')
                if abs(i) > .35:
                    tela.disco(x, y, 2.0, AMARELO if i > 0 else CIANO)
                    if abs(i) > .7: brilho(tela, x, y, 7, AMARELO if i > 0 else CIANO, .5)
            x, y = P(cx, cy, rr * .3, rho)
            tela.disco(x, y, 2, BRANCO)
        pintar_disco(tela, cx, cy, 5, 'aco')
        tela.px(cx, cy, PRETO)
        if sensor is not None:
            ang_s, aceso = sensor
            x, y = P(cx, cy, R * .5, ang_s)
            tela.ret(x - 2, y - 2, 5, 5, PRETO)
            tela.ret(x - 1, y - 1, 3, 3, VERDE if aceso else ACO0)
            if aceso: brilho(tela, x, y, 8, VERDE, .8)
        if campo is not None:
            a, mag = campo
            if mag > .05:
                x, y = P(cx, cy, rr * 1.05 * mag + 6, a)
                seta(tela, cx, cy, x, y, CIANO, cab=4, esp=2)


# ================================================================ aparelhos da casa
def ventoinha(tela, cx, cy, L, ang, corte=0.0, t=0.0):
    """Ventoinha de computador vista de frente (genérica). corte 0..1: o cubo
    fica transparente e mostra as bobinas paradas e o anel de ímãs girando."""
    h = L / 2
    pintar_ret(tela, cx - h, cy - h, L, L, 'plast')
    tela.disco(cx, cy, h - 5, FUNDO)
    tela.anel(cx, cy, h - 5, PRETO, .8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tela.disco(cx + sx * (h - 7), cy + sy * (h - 7), 3, PRETO)
            tela.disco(cx + sx * (h - 7), cy + sy * (h - 7), 1.5, ACO0)
    # pás
    rh = h * .36
    for k in range(7):
        a = ang + k * 360 / 7
        pts = []
        for i in range(9):
            u = i / 8
            r = rh + (h - 9 - rh) * u
            pts.append(P(cx, cy, r, a + 26 * u))
        for i in range(8, -1, -1):
            u = i / 8
            r = rh + (h - 9 - rh) * u
            pts.append(P(cx, cy, r, a + 26 * u + 30 - 6 * u))
        pintar_pol(tela, pts, 'plast', cx=cx, cy=cy, R=h)
    # suportes (braços fixos atrás do cubo)
    # cubo
    pintar_disco(tela, cx, cy, rh + 1, 'plast')
    if corte > 0:
        # anel de ímãs (gira com as pás) e o estator parado no meio
        n = 8
        for k in range(n):
            a0 = ang + k * 360 / n
            pintar_setor(tela, cx, cy, rh - 5, rh, a0 + 2, a0 + 360 / n - 2, 'ima_n' if k % 2 == 0 else 'ima_s', cx=cx, cy=cy, R=rh)
        tela.disco(cx, cy, rh - 6, FUNDO)
        for k in range(6):
            a = 30 + k * 60
            x0, y0 = P(cx, cy, 4, a); x1, y1 = P(cx, cy, rh - 8, a)
            linha_grossa(tela, x0, y0, x1, y1, 4, LATAO)
            on = int(t * 12) % 3 == k % 3
            tela.disco(x1, y1, 2.5, CHAMA1 if on else OLEO1)
        pintar_disco(tela, cx, cy, 3.5, 'aco')
        if corte < 1:
            pass
    else:
        tela.disco(cx, cy, rh * .55, FUNDO3)
        tela.anel(cx, cy, rh * .55, TRACO, .5)


def maquina(tela, cx, cy, ang, t, corte=0.0):
    """Máquina de lavar de frente (genérica): caixa branca, porta com o cesto girando."""
    w, h = 132, 160
    x0, y0 = cx - w // 2, cy - h // 2
    pintar_ret(tela, x0, y0, w, h, 'branco')
    tela.ret(x0 + 3, y0 + 24, w - 6, 1, ACO2)
    # painel de controle
    tela.ret(x0 + 8, y0 + 7, 34, 11, FUNDO); tela.ret(x0 + 10, y0 + 9, 30, 7, AGUA0)
    tela.texto('1200', x0 + 12, y0 + 9, VERDE, tam=9)
    pintar_disco(tela, x0 + w - 18, y0 + 12, 7, 'aco')
    x, y = P(x0 + w - 18, y0 + 12, 5, ang * .02)
    tela.px(x, y, PRETO)
    for k in range(3): tela.ret(x0 + 52 + k * 12, y0 + 10, 8, 5, ACO2)
    # porta
    pcx, pcy, pr = cx, cy + 14, 50
    pintar_disco(tela, pcx, pcy, pr, 'aco')
    tela.disco(pcx, pcy, pr - 7, FUNDO)
    # cesto: furos girando
    for anel_r in (14, 26, 36):
        n = int(anel_r / 2.6)
        for k in range(n):
            x, y = P(pcx, pcy, anel_r, ang + k * 360 / n)
            tela.px(x, y, ACO0)
    # roupa (tombando: sobe com o cesto e cai)
    for j, (cor, fase) in enumerate(((VERMELHO, 0), (MISTURA2, 110), (AMARELO, 220), (VERDE, 300))):
        a = ang * .8 + fase
        r = 22 + 8 * math.sin(math.radians(a * 2 + j))
        x, y = P(pcx, pcy, r, a)
        tela.disco(x, y, 6, PRETO); tela.disco(x, y, 5, cor)
        tela.px(x - 2, y - 2, BRANCO)
    # aletas do cesto
    for k in range(3):
        a = ang + k * 120
        x0_, y0_ = P(pcx, pcy, pr - 15, a); x1_, y1_ = P(pcx, pcy, pr - 8, a)
        linha_grossa(tela, x0_, y0_, x1_, y1_, 4, ACO2)
    # vidro
    for k in range(9): tela.px(pcx - 22 + k, pcy - 28 + k, ACO3)
    tela.anel(pcx, pcy, pr - 7, ACO1, .5)
    pintar_ret(tela, pcx + pr - 6, pcy - 6, 8, 12, 'aco')
    return pcx, pcy


def carro(tela, x, y, ang_roda, t, corte=0.0, brilho_motor=0.0):
    """Carro elétrico genérico de lado (sem marca). (x, y) = canto do chão à esquerda.
    Devolve o centro do motor (no eixo traseiro)."""
    L = 200
    corpo = [(x + 6, y - 20), (x + 6, y - 42), (x + 40, y - 46), (x + 70, y - 70), (x + 136, y - 72), (x + 166, y - 48),
             (x + 194, y - 42), (x + 198, y - 22), (x + 190, y - 14), (x + 12, y - 14)]
    pintar_pol(tela, corpo, 'lataria')
    janela = [(x + 76, y - 48), (x + 80, y - 64), (x + 104, y - 65), (x + 104, y - 48)]
    janela2 = [(x + 110, y - 48), (x + 110, y - 65), (x + 132, y - 65), (x + 154, y - 48)]
    pintar_pol(tela, janela, 'vidro'); pintar_pol(tela, janela2, 'vidro')
    tela.ret(x + 106, y - 66, 3, 20, FUNDO3)
    tela.ret(x + 70, y - 34, 90, 1, FUNDO3)
    tela.ret(x + 112, y - 40, 8, 2, ACO3)
    # faróis
    tela.ret(x + 188, y - 38, 7, 4, CHAMA0); tela.ret(x + 7, y - 38, 5, 4, VERMELHO)
    # bateria no assoalho (corte)
    if corte > 0:
        tela.ret(x + 50, y - 26, 104, 10, PRETO)
        for k in range(12):
            tela.ret(x + 52 + k * 8 + 1, y - 24, 6, 6, VERDE if (k + int(t * 6)) % 12 else AMARELO)
    rodas = []
    for rx in (x + 44, x + 160):
        rodas.append(rx)
        pintar_disco(tela, rx, y - 12, 14, 'pneu')
        pintar_disco(tela, rx, y - 12, 8, 'aco')
        for k in range(5):
            x1, y1 = P(rx, y - 12, 7, ang_roda + k * 72)
            tela.linha(rx, y - 12, x1, y1, ACO0)
        tela.disco(rx, y - 12, 2, PRETO)
    mx, my = x + 44, y - 28
    if corte > 0:
        # motor no eixo traseiro (em corte): estator e rotor girando
        pintar_disco(tela, mx + 24, my + 4, 11, 'aco')
        for k in range(6):
            a = k * 60
            x1, y1 = P(mx + 24, my + 4, 7, a)
            tela.disco(x1, y1, 2, CHAMA1 if (k + int(t * 10)) % 3 == 0 else OLEO1)
        x1, y1 = P(mx + 24, my + 4, 4, ang_roda * 3)
        tela.disco(mx + 24, my + 4, 3, VERMELHO); tela.px(x1, y1, BRANCO)
        if brilho_motor > 0: brilho(tela, mx + 24, my + 4, 18, AMARELO, brilho_motor)
    return (mx + 24, my + 4), rodas


def grade(tela, x0, y0, n_verde, n_faixa, t, t_ini, lado=11, cor_ok=VERDE, cor_perda=VERMELHO):
    """Grade de 100 quadradinhos de energia: verdes viram movimento, vermelhos
    viram calor (com faísquinhas subindo). n_faixa = quadrados em dúvida
    (a faixa de um dado como 87% a 91%), pintados em xadrez."""
    for i in range(100):
        ta = t_ini + i * .012
        if t < ta: continue
        col, lin = i % 10, i // 10
        x, y = x0 + col * lado, y0 + lin * lado
        cor = AMARELO
        k = i
        if t > ta + 1.4:
            cor = cor_ok if k < n_verde else (CIANO if k < n_verde + n_faixa else cor_perda)
        tela.ret(x, y, lado - 2, lado - 2, cor)
        tela.ret(x, y, lado - 2, 1, BRANCO if cor in (AMARELO, VERDE, CIANO) else CHAMA1)
        tela.ret(x + lado - 3, y, 1, lado - 2, PRETO)
        tela.ret(x, y + lado - 3, lado - 2, 1, PRETO)
        if cor == cor_perda and (i * 7) % 4 == 0:
            u = (t * .9 + i * .37) % 1.0
            tela.px(x + 4 + math.sin(t * 5 + i) * 2, y - u * 12, CHAMA1 if u < .5 else BRASA)
