#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep15 — o desenho: paleta do corpo (pele de manequim,
mucosa, intestino, fígado, bile, pâncreas, sangue, quimo), a garfada
(protagonista), o mapa do corpo em corte (vista de frente), tubos com
volume (esôfago, estômago, intestinos), o painel da jornada e miúdos
(rótulo com fio, seta, brilho, relógio, grão de arroz, feijão, bactérias).

Tudo é estilizado: um manequim sem rosto, órgãos em corte simplificado,
nada de sangue realista. A paleta é a `oficina` + 42 cores próprias,
registrada como 'ep15' (o `longo` passa a usá-la neste processo).

Volume: as formas orgânicas são máscaras (polígono, elipse ou tubo de raio
variável). O tubo sabe a distância de cada pixel ao eixo (0 no centro, 1 na
parede): isso vira o sombreado cilíndrico em dither Bayer, com contorno
escuro na borda.
"""
import math
import numpy as np
from scipy.ndimage import distance_transform_edt, binary_erosion
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, BAYER8,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)

# ================================================================ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#3b2a33', '#66505a', '#9a8088', '#c9b3b5',          # 32..35 manequim (pele neutra)
          '#1e0c14', '#3a1424',                                # 36..37 cavidade (fundo do corte)
          '#5c1a30', '#9a3048', '#d0607a', '#f4a2b0', '#ffd6dc',  # 38..42 mucosa (rosa) .. muco
          '#4a2016', '#8a4430', '#c97858', '#f0aa88',          # 43..46 intestino (salmão)
          '#300c10', '#5e1a1e', '#8e3030', '#c05a4e',          # 47..50 fígado
          '#2c4410', '#5e8a1c', '#a8d040',                     # 51..53 bile / vesícula
          '#6a4a1c', '#b08a40', '#e8c878',                     # 54..56 pâncreas
          '#9c9480', '#d8d0bc',                                # 57..58 arroz
          '#2a1208', '#5a2a14', '#8c4a28',                     # 59..61 feijão
          '#4a0610', '#8e1420', '#d83040',                     # 62..64 sangue (estilizado)
          '#6a5a2a', '#a89048', '#d8c27a',                     # 65..67 quimo
          '#5a7a10', '#c8f040',                                # 68..69 ácido
          '#3a2618', '#6a4428',                                # 70..71 madeira (mesa)
          '#4e3a28', '#7a5c3e', '#26303e']                     # 72..74 resto (discreto) / azul-noite
PX.PALETAS['ep15'] = _BASE + _EXTRA
LG.PAL = 'ep15'
PELE0, PELE1, PELE2, PELE3 = 32, 33, 34, 35
CAV0, CAV1 = 36, 37
MUC0, MUC1, MUC2, MUC3, MUCO = 38, 39, 40, 41, 42
INT0, INT1, INT2, INT3 = 43, 44, 45, 46
FIG0, FIG1, FIG2, FIG3 = 47, 48, 49, 50
BILE0, BILE1, BILE2 = 51, 52, 53
PAN0, PAN1, PAN2 = 54, 55, 56
ARROZ0, ARROZ1 = 57, 58
FEI0, FEI1, FEI2 = 59, 60, 61
SANG0, SANG1, SANG2 = 62, 63, 64
QUI0, QUI1, QUI2 = 65, 66, 67
ACI0, ACI1 = 68, 69
MAD0, MAD1 = 70, 71
RES0, RES1, NOITE = 72, 73, 74

C_MUC = [MUC0, MUC1, MUC2, MUC3]
C_INT = [INT0, INT1, INT2, INT3]
C_FIG = [FIG0, FIG1, FIG2, FIG3]
C_BILE = [BILE0, BILE1, BILE2]
C_PAN = [PAN0, PAN1, PAN2]
C_PELE = [PELE0, PELE1, PELE2, PELE3]
C_QUI = [QUI0, QUI1, QUI2]
C_SANG = [SANG0, SANG1, SANG2]
C_RES = [RES0, RES1, INT1]

# ================================================================ a jornada
ETAPAS = [('BOCA', MUC3), ('GARGANTA', CIANO), ('ESÔFAGO', MUC2), ('ESTÔMAGO', ACI1),
          ('INT. DELGADO', INT3), ('INT. GROSSO', PAN2), ('SAÍDA', ACO3)]
NE = len(ETAPAS)


def lerp(a, b, u): return a + (b - a) * u
def um(u): return min(1.0, max(0.0, u))


# ================================================================ miúdos
def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com bolinha na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.disco(x1, y1, 1.6, cor)


def seta(tela, x, y, dirx, diry, cor, tam=5):
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if diry:
            tela.ret(x - w // 2, y + (k if diry > 0 else -k), w, 1, cor)
        else:
            tela.ret(x + (k if dirx > 0 else -k), y - w // 2, 1, w, cor)


def halo(tela, cx, cy, r, cor, fase=0):
    """Brilho em xadrez (pixel sim, pixel não) em volta de algo luminoso."""
    x0, x1 = max(0, int(cx - r)), min(tela.w, int(cx + r + 1))
    y0, y1 = max(0, int(cy - r)), min(tela.h, int(cy + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & ((xx + yy + fase) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def luz(tela, cx, cy, r, nucleo=BRANCO, cor=AMARELO, halo_cor=None):
    halo(tela, cx, cy, r * 2.2, halo_cor if halo_cor is not None else cor)
    tela.disco(cx, cy, r, cor)
    tela.disco(cx, cy, max(.6, r * .5), nucleo)


def brilho_estrela(tela, x, y, t, cor=AMARELO):
    """O marcador da protagonista: estrelinha que pisca (nunca se perde)."""
    k = int(t * 3) % 4
    if k < 3:
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            tela.px(x + dx, y + dy, cor)
        if k == 1:
            tela.px(x, y, BRANCO); tela.px(x - 2, y, cor); tela.px(x + 2, y, cor)
            tela.px(x, y - 2, cor); tela.px(x, y + 2, cor)


def grad_v(tela, x, y, w, h, cores, fase=0):
    """Degradê vertical com Bayer 8x8 entre a lista de cores (de cima para baixo)."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(tela.w, int(x + w)), min(tela.h, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u = (yy - y) / max(1.0, h - 1) * (len(cores) - 1)
    b = BAYER8[(yy + fase) % 8, xx % 8]
    i = np.clip(np.floor(u) + (u - np.floor(u) > b), 0, len(cores) - 1).astype(int)
    tela.buf[y0:y1, x0:x1] = np.array(cores, np.uint8)[i]


def caixa(tela, x, y, w, h, cor, luz_=None, sombra=None):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, cor)
    if luz_ is not None:
        tela.ret(x, y, w, 1, luz_); tela.ret(x, y, 1, h, luz_)
    if sombra is not None:
        tela.ret(x, y + h - 1, w, 1, sombra); tela.ret(x + w - 1, y, 1, h, sombra)


def relogio(tela, cx, cy, r, t, vel=1.0, cor=BRANCO):
    """Relógio pequeno com ponteiro girando (o tempo passando)."""
    tela.disco(cx, cy, r + 1, PRETO)
    tela.disco(cx, cy, r, ACO0)
    tela.anel(cx, cy, r, cor)
    a = t * vel * 2 * math.pi
    tela.linha(cx, cy, cx + math.sin(a) * (r - 1.5), cy - math.cos(a) * (r - 1.5), AMARELO)
    b = a / 12
    tela.linha(cx, cy, cx + math.sin(b) * (r - 3), cy - math.cos(b) * (r - 3), cor)
    tela.px(cx, cy, BRANCO)


def gotinha(tela, x, y, cor=MISTURA2, escura=MISTURA):
    """Gota pequena (saliva, suco, bile, água)."""
    tela.disco(x, y, 1.9, PRETO)
    tela.px(x, y - 2, PRETO)
    tela.disco(x, y, 1.2, cor)
    tela.px(x, y - 1, cor)
    tela.px(x + 1, y + 1, escura)
    tela.px(x - 1, y - 1, BRANCO)


# ================================================================ volume (máscaras)
def _grade(x0, y0, x1, y1):
    x0, y0 = int(math.floor(x0)), int(math.floor(y0))
    x1, y1 = int(math.ceil(x1)) + 1, int(math.ceil(y1)) + 1
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return x0, y0, xx + .5, yy + .5


def pintar(tela, ox, oy, m, val, cores, contorno=PRETO, fase=0):
    """Pinta a máscara `m` (bool, h x w) em (ox, oy). `val` 0..1 escolhe a cor
    da lista (escura -> clara) com dither Bayer; a borda sai em `contorno`."""
    h, w = m.shape
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(w, tela.w - ox), min(h, tela.h - oy)
    if sx1 <= sx0 or sy1 <= sy0: return
    mm = m[sy0:sy1, sx0:sx1]
    reg = tela.buf[oy + sy0:oy + sy1, ox + sx0:ox + sx1]
    if np.isscalar(val) or val is None:
        reg[mm] = cores[0] if val is None else cores[int(round(um(float(val)) * (len(cores) - 1)))]
    else:
        vv = val[sy0:sy1, sx0:sx1]
        yy, xx = np.mgrid[oy + sy0:oy + sy1, ox + sx0:ox + sx1]
        n = len(cores)
        u = np.clip(vv, 0, 1) * (n - 1)
        b = BAYER8[(yy + fase) % 8, xx % 8]
        i = np.clip(np.floor(u) + ((u - np.floor(u)) > b), 0, n - 1).astype(int)
        reg[mm] = np.array(cores, np.uint8)[i][mm]
    if contorno is not None:
        er = binary_erosion(m, iterations=1, border_value=0)[sy0:sy1, sx0:sx1]
        reg[mm & ~er] = contorno


class Forma:
    """Máscara pronta: ox, oy, m (bool), dn (0 eixo .. 1 borda), s (ao longo
    do tubo), lado (+1/-1) e X, Y (centros dos pixels)."""

    def __init__(self, ox, oy, m, dn, X, Y, s=None, lado=None):
        self.ox, self.oy, self.m, self.dn, self.X, self.Y, self.s, self.lado = ox, oy, m, dn, X, Y, s, lado

    def cilindro(self, luz_lado=1.0, base=.12, amp=.78):
        """Sombreado de tubo: claro no meio, escuro na parede, um lado mais claro."""
        dn = np.clip(self.dn, 0, 1)
        v = base + amp * np.sqrt(np.clip(1 - dn * dn, 0, 1))
        if self.lado is not None:
            v = v + .22 * luz_lado * self.lado * dn
        return np.clip(v, 0, 1)

    def pintar(self, tela, cores, val=None, contorno=PRETO, fase=0):
        pintar(tela, self.ox, self.oy, self.m, self.cilindro() if val is None else val, cores, contorno, fase)


def tubo(pts, raios, pad=2):
    """Tubo de raio variável ao longo de uma polilinha (raio por ponto)."""
    P = np.array(pts, np.float32)
    R = np.array(raios if hasattr(raios, '__len__') else [raios] * len(pts), np.float32)
    rmax = float(R.max())
    ox, oy, X, Y = _grade(P[:, 0].min() - rmax - pad, P[:, 1].min() - rmax - pad,
                          P[:, 0].max() + rmax + pad, P[:, 1].max() + rmax + pad)
    best = np.full(X.shape, 9.0, np.float32)
    s = np.zeros(X.shape, np.float32)
    lado = np.zeros(X.shape, np.float32)
    acc = 0.0
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        d = b - a
        L2 = float(d @ d)
        L = math.sqrt(max(L2, 1e-9))
        u = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / max(L2, 1e-9), 0, 1)
        px, py = a[0] + u * d[0], a[1] + u * d[1]
        dist = np.hypot(X - px, Y - py)
        r = R[i] + (R[i + 1] - R[i]) * u
        dn = dist / np.maximum(r, .5)
        cr = np.sign((X - a[0]) * d[1] - (Y - a[1]) * d[0])
        mel = dn < best
        best = np.where(mel, dn, best)
        s = np.where(mel, acc + u * L, s)
        lado = np.where(mel, cr, lado)
        acc += L
    return Forma(ox, oy, best < 1.0, best, X, Y, s, lado)


def elipse(cx, cy, rx, ry, pad=1):
    ox, oy, X, Y = _grade(cx - rx - pad, cy - ry - pad, cx + rx + pad, cy + ry + pad)
    dn = np.sqrt(((X - cx) / max(rx, .5)) ** 2 + ((Y - cy) / max(ry, .5)) ** 2)
    return Forma(ox, oy, dn < 1, dn, X, Y)


def poli(pts, pad=1):
    """Polígono com 'dn' vindo da distância à borda (1 na borda, 0 no miolo)."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ox, oy, X, Y = _grade(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
    m = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        if ay == by: continue
        cond = ((ay <= Y) & (Y < by)) | ((by <= Y) & (Y < ay))
        xint = ax + (Y - ay) * (bx - ax) / (by - ay)
        m ^= cond & (X < xint)
    d = distance_transform_edt(m).astype(np.float32)
    dn = 1 - np.clip(d / max(2.0, min(8.0, float(d.max()) * .7 if d.size else 1)), 0, 1)
    return Forma(ox, oy, m, dn, X, Y)


def volume(f, luz=(-.55, -.8), base=.1, amp=.7, brilho=.35):
    """Sombreado de 'almofada' para elipse/polígono: miolo claro, borda
    escura, luz vindo de cima à esquerda."""
    m = f.m
    if not m.any(): return np.zeros(m.shape, np.float32)
    ys, xs = np.nonzero(m)
    cx, cy = f.X[ys, xs].mean(), f.Y[ys, xs].mean()
    w = max(2.0, (xs.max() - xs.min()) / 2); h = max(2.0, (ys.max() - ys.min()) / 2)
    lx, ly = (f.X - cx) / w, (f.Y - cy) / h
    v = base + amp * np.sqrt(np.clip(1 - np.clip(f.dn, 0, 1) ** 2, 0, 1)) - brilho * (lx * luz[0] + ly * luz[1])
    return np.clip(v, 0, 1)


_CACHE = {}


def guardado(chave, fazer):
    if chave not in _CACHE: _CACHE[chave] = fazer()
    return _CACHE[chave]


def ao_longo(pts, u):
    """Ponto na fração u (0..1) do comprimento de uma polilinha."""
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    tot = sum(segs)
    alvo = um(u) * tot
    for (a, b), L in zip(zip(pts, pts[1:]), segs):
        if alvo <= L:
            k = alvo / L if L else 0
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        alvo -= L
    return pts[-1]


def comprimento(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def u_do_ponto(pts, i):
    """Fração do comprimento até o vértice i."""
    return comprimento(pts[:i + 1]) / comprimento(pts)


# ================================================================ comida
def grao(tela, x, y, d=0, quebrado=False):
    """Grão de arroz cozido (3x2) com luz e sombra; d = 0 deitado, 1 inclinado."""
    x, y = int(x), int(y)
    if quebrado:
        tela.px(x, y, ARROZ1); tela.px(x + 1, y, ARROZ0)
        return
    if d == 0:
        tela.ret(x - 1, y - 1, 5, 4, PRETO)
        tela.ret(x, y, 3, 2, ARROZ1); tela.px(x, y, BRANCO); tela.ret(x + 1, y + 1, 2, 1, ARROZ0)
    else:
        for k in range(3):
            tela.ret(x + k - 1, y + k - 1, 3, 3, PRETO)
        for k in range(3):
            tela.px(x + k, y + k, ARROZ1)
            tela.px(x + k + 1, y + k, ARROZ1 if k < 2 else ARROZ0)
        tela.px(x, y, BRANCO)


def feijao(tela, x, y, s=1.0):
    """Feijão-carioca/preto estilizado: oval marrom com brilho e o 'olho'."""
    rx, ry = 2.6 * s, 1.7 * s
    f = elipse(x, y, rx, ry)
    pintar(tela, f.ox, f.oy, f.m, volume(f), [FEI0, FEI1, FEI2], PRETO)
    tela.px(x - rx * .4, y - ry * .4, ARROZ1)
    tela.px(x + .5, y + ry * .3, ARROZ0)


def garfada(tela, cx, cy, s=1.0, t=0.0, fase='bolo', prota=True, molhado=0.0, quebra=0.0, seed=5):
    """A protagonista. 'bolo' = bolinha mastigada com pedaços de arroz e
    feijão; 'quimo' = pasta mole; 'resto' = o que sobra para o intestino grosso.
    `quebra` 0..1 deixa os grãos em pedaços; `molhado` põe brilho de saliva."""
    rng = np.random.default_rng(seed)
    if fase == 'quimo':
        r = 6.5 * s
        pts = [(cx + math.cos(a) * r * (1 + .12 * math.sin(3 * a + t * 3)),
                cy + math.sin(a) * r * .85 * (1 + .1 * math.sin(2 * a - t * 2.4))) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)]
        f = poli(pts)
        pintar(tela, f.ox, f.oy, f.m, volume(f), C_QUI, PRETO)
        for k in range(int(5 * s)):
            a, rr = rng.random() * 6.28, rng.random() * r * .6
            tela.px(cx + math.cos(a + t * .5) * rr, cy + math.sin(a + t * .5) * rr * .8, QUI2 if k % 2 else FEI2)
    elif fase == 'resto':
        r = 6.0 * s
        f = elipse(cx, cy, r * 1.15, r * .8)
        pintar(tela, f.ox, f.oy, f.m, volume(f), C_RES, PRETO)
        for k in range(int(5 * s)):
            a, rr = rng.random() * 6.28, rng.random() * r * .7
            tela.px(cx + math.cos(a) * rr, cy + math.sin(a) * rr * .6, QUI1 if k % 2 else ARROZ0)
    else:
        r = 6.0 * s
        f = elipse(cx, cy, r * 1.1, r * .95)
        pintar(tela, f.ox, f.oy, f.m, volume(f), [QUI0, QUI1, ARROZ0, ARROZ1], PRETO)
        n = int(7 * s)
        for k in range(n):
            a, rr = rng.random() * 6.28, rng.random() * r * .65
            gx, gy = cx + math.cos(a) * rr, cy + math.sin(a) * rr * .8
            if k % 3 == 2:
                if quebra < .6: tela.ret(int(gx), int(gy), 2, 2, FEI1); tela.px(gx, gy, FEI2)
                else: tela.px(gx, gy, FEI1)
            else:
                if quebra < .5: tela.ret(int(gx), int(gy), 2, 1, BRANCO)
                else: tela.px(gx, gy, BRANCO)
        if molhado > 0:
            for k in range(int(3 + 4 * molhado)):
                a = rng.random() * 6.28
                tela.px(cx + math.cos(a) * r * .8, cy + math.sin(a) * r * .7, MISTURA2)
    if prota:
        brilho_estrela(tela, cx + r * 1.1 + 3, cy - r - 1, t)


def marca(tela, x, y, txt, lado=1, dy=-20, cor=AMARELO):
    """Rótulo com fio apontando para a protagonista."""
    w = tela.largura_texto(txt, 9)
    lx = x + lado * 14 - (w if lado < 0 else 0)
    ly = y + dy
    rotulo(tela, txt, lx, ly, cor)
    fio(tela, x + lado * 12, ly + (9 if dy < 0 else -2), x + lado * 4, y + (-4 if dy < 0 else 4), cor)


# ================================================================ bactérias e moléculas
def glicose(tela, x, y, cor=AMARELO):
    """Açúcar (glicose): hexágono pequeno."""
    for dx, dy in ((-1, -2), (0, -2), (1, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), (2, 1), (-1, 2), (0, 2), (1, 2)):
        tela.px(x + dx, y + dy, PRETO)
    tela.ret(int(x) - 1, int(y) - 1, 3, 3, cor)
    tela.px(x - 1, y - 1, BRANCO)


def aminoacido(tela, x, y, cor=VERDE):
    tela.disco(x, y, 2.0, PRETO)
    tela.disco(x, y, 1.3, cor)
    tela.px(x - 1, y - 1, BRANCO)


def bacteria(tela, x, y, tipo, ang, t, s=1.0):
    """Bactérias estilizadas: bastonete, coco em cadeia, espiral."""
    if tipo == 0:
        c, sn = math.cos(ang), math.sin(ang)
        L = 6 * s
        f = tubo([(x - c * L, y - sn * L), (x + c * L, y + sn * L)], 2.6 * s)
        f.pintar(tela, [ROXO, ROSA, MUC3])
        tela.px(x - c * L * .4, y - sn * L * .4 - 1, BRANCO)
        # flagelo
        for k in range(5):
            u = k / 4
            tela.px(x - c * (L + 3 + k * 1.5) + math.sin(t * 9 + k) * sn * 1.5,
                    y - sn * (L + 3 + k * 1.5) - math.sin(t * 9 + k) * c * 1.5, ROXO)
    elif tipo == 1:
        for k in range(3):
            px_ = x + math.cos(ang) * k * 4.2 * s
            py_ = y + math.sin(ang) * k * 4.2 * s + math.sin(t * 4 + k) * .6
            tela.disco(px_, py_, 2.4 * s, PRETO)
            tela.disco(px_, py_, 1.7 * s, VERDE)
            tela.px(px_ - 1, py_ - 1, BRANCO)
    else:
        pts = [(x + k * 1.6 * s * math.cos(ang) - math.sin(k * 1.2 + t * 6) * 2.2 * s * math.sin(ang),
                y + k * 1.6 * s * math.sin(ang) + math.sin(k * 1.2 + t * 6) * 2.2 * s * math.cos(ang)) for k in range(9)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            linha_grossa(tela, ax, ay, bx, by, 3.2, PRETO)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            tela.linha(ax, ay, bx, by, CIANO)


# ================================================================ o corpo (vista de frente, em corte)
CX = 147
TORSO = [(104, 64), (120, 57), (174, 57), (190, 64), (197, 82), (193, 120), (185, 150), (191, 180), (194, 212),
         (100, 212), (103, 180), (109, 150), (101, 120), (97, 82)]
CORTE = [(111, 70), (183, 70), (188, 84), (184, 120), (176, 150), (182, 180), (185, 212), (109, 212), (112, 180),
         (118, 150), (110, 120), (106, 84)]
BRACO_E = [(98, 66), (88, 74), (82, 130), (78, 178), (86, 182), (92, 134), (101, 92)]
BRACO_D = [(2 * CX - x, y) for x, y in BRACO_E]
ESOF = [(147, 40), (147, 50), (147, 62), (149, 80), (153, 93)]
ESTOM = [(153, 93), (163, 91), (174, 95), (180, 105), (175, 114), (166, 118), (160, 119)]
ESTOM_R = [3, 7, 9, 9, 7, 4, 2.5]
FIGADO = [(107, 94), (150, 91), (160, 95), (158, 103), (147, 111), (128, 116), (112, 112), (105, 102)]
PANC = [(150, 126), (164, 124), (180, 121)]
DUOD = [(160, 119), (161, 125), (156, 130), (149, 131), (143, 128)]
JEJ = [(143, 128), (139, 135), (134, 143)]
GROSSO = [(124, 186), (119, 174), (118, 150), (121, 138), (136, 135), (154, 137), (170, 135), (181, 139),
          (184, 152), (184, 175), (178, 188), (165, 193), (153, 195), (148, 201)]
RETO = [(148, 201), (148, 206), (148, 212)]


def _serpentina():
    pts = [(134, 143)]
    linhas = [146, 153, 160, 167, 174, 181]
    for j, y in enumerate(linhas):
        xs = np.linspace(131, 173, 8) if j % 2 == 0 else np.linspace(173, 131, 8)
        for k, x in enumerate(xs):
            pts.append((float(x), y + math.sin(float(x) * .35) * .9))
    pts += [(128, 184), (124, 186)]
    return pts


DELG = _serpentina()
ROTA = [(147, 37), (147, 42)] + ESOF[1:] + [(166, 96), (176, 105), (171, 114), (160, 119)] + DUOD[1:] + JEJ[1:] + DELG[1:] + GROSSO[1:] + RETO[1:]
_IDX = {}
for _nome, _p in (('boca', (147, 37)), ('garganta', (147, 42)), ('esofago', (147, 50)), ('estomago', (153, 93)),
                  ('delgado', (160, 119)), ('grosso', (124, 186)), ('saida', (148, 201))):
    _IDX[_nome] = ROTA.index(_p)
U_ETAPA = [u_do_ponto(ROTA, _IDX[k]) for k in ('boca', 'garganta', 'esofago', 'estomago', 'delgado', 'grosso', 'saida')] + [1.0]


def _formas_corpo():
    F = {}
    F['torso'] = poli(TORSO)
    F['be'] = poli(BRACO_E); F['bd'] = poli(BRACO_D)
    F['cabeca'] = elipse(CX, 27, 16, 20)
    F['pescoco'] = poli([(139, 42), (155, 42), (157, 62), (137, 62)])
    F['corte'] = poli(CORTE)
    F['pulmao_e'] = elipse(126, 86, 13, 15)
    F['pulmao_d'] = elipse(168, 84, 12, 14)
    F['esof'] = tubo(ESOF, 2.2)
    F['estom'] = tubo(ESTOM, ESTOM_R)
    F['figado'] = poli(FIGADO)
    F['vesicula'] = elipse(134, 114, 4, 3)
    F['panc'] = tubo(PANC, [4, 3.4, 2])
    F['duod'] = tubo(DUOD, 2.6)
    F['jej'] = tubo(JEJ, 2.6)
    F['delg'] = tubo(DELG, 2.8)
    rs = []
    acc = 0
    for a, b in zip(GROSSO, GROSSO[1:] + [GROSSO[-1]]):
        rs.append(4.6)
    F['grosso'] = tubo(GROSSO, rs)
    F['reto'] = tubo(RETO, 2.6)
    return F


def corpo(tela, t, atual=None, dx=0, acesos=(), sangue=None, brilho_org=None):
    """Mapa do corpo em corte. `atual` = nome do órgão que pisca;
    `acesos` = órgãos já visitados (mais claros); `sangue` = função que desenha
    por cima (veia porta etc.)."""
    F = guardado('corpo', _formas_corpo)

    def p(nome, cores, val=None, contorno=PRETO):
        f = F[nome]
        v = f.cilindro() if val is None and f.s is not None else (volume(f) if val is None else val)
        pintar(tela, f.ox + dx, f.oy, f.m, v, cores, contorno)

    def destaca(nome, cor=AMARELO):
        f = F[nome]
        if int(t * 4) % 2 == 0:
            er = binary_erosion(f.m, iterations=1, border_value=0)
            m = f.m & ~er
            ys, xs = np.nonzero(m)
            ok = (xs + f.ox + dx >= 0) & (xs + f.ox + dx < tela.w) & (ys + f.oy >= 0) & (ys + f.oy < tela.h)
            tela.buf[ys[ok] + f.oy, xs[ok] + f.ox + dx] = cor

    # manequim
    p('be', C_PELE); p('bd', C_PELE)
    p('torso', C_PELE)
    p('pescoco', C_PELE)
    p('cabeca', C_PELE)
    # sem rosto: só a boca, para saber onde a viagem começa
    tela.ret(CX - 5 + dx, 36, 11, 3, PRETO); tela.ret(CX - 4 + dx, 37, 9, 1, MUC1)
    # corte: o fundo escuro do tronco
    f = F['corte']
    yy = f.Y
    pintar(tela, f.ox + dx, f.oy, f.m, np.clip((yy - 60) / 200, 0, 1) * .6 + .2, [CAV0, CAV1], TRACO)
    p('pulmao_e', [FUNDO2, FUNDO3, TRACO], contorno=FUNDO2)
    p('pulmao_d', [FUNDO2, FUNDO3, TRACO], contorno=FUNDO2)
    # diafragma
    for x in range(110, 186, 2): tela.px(x + dx, 103 + 3 * math.cos((x - 147) / 30), MUC0)

    def cores(nome, base):
        if nome in acesos or nome == atual: return base
        return base

    p('esof', C_MUC)
    p('panc', C_PAN)
    p('duod', C_INT)
    p('jej', C_INT)
    p('estom', [MUC0, MUC1, MUC2, MUC3])
    p('figado', C_FIG)
    p('vesicula', C_BILE)
    p('grosso', [RES0, INT1, INT2, INT3])
    p('delg', C_INT)
    p('reto', [RES0, INT1, INT2])
    # pregas do intestino grosso (haustros)
    for k in range(0, len(GROSSO) - 3):
        (ax, ay), (bx, by) = GROSSO[k], GROSSO[k + 1]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        L = math.hypot(bx - ax, by - ay) or 1
        nx, ny = -(by - ay) / L, (bx - ax) / L
        tela.linha(mx - nx * 3.5 + dx, my - ny * 3.5, mx + nx * 3.5 + dx, my + ny * 3.5, INT0)
    if sangue: sangue(tela)
    grupos = dict(boca=None, garganta='esof', esofago='esof', estomago='estom', delgado='delg',
                  grosso='grosso', saida='reto', figado='figado', vesicula='vesicula', pancreas='panc', duodeno='duod')
    if atual:
        alvo = grupos.get(atual)
        if alvo: destaca(alvo)
        if atual == 'delgado': destaca('duod')
        if atual == 'boca' and int(t * 4) % 2 == 0:
            tela.ret_vazado(CX - 7 + dx, 34, 15, 7, AMARELO)


# ================================================================ painel da jornada
def painel_jornada(tela, k, t, linhas=None, estado=None, cab=None, x0=302, tudo=False, rodape=None):
    """Painel da direita. k = etapa (0..6). `linhas` = [(rótulo, valor, cor)]
    (um rótulo que começa com TEMPO ganha o relógio). `estado` = a garfada agora.
    `cab` = (linha1, linha2, cor) troca o cabeçalho ETAPA."""
    tela.ret(x0 - 8, 0, W - x0 + 8, PALCO_H, FUNDO)
    tela.ret(x0 - 8, 0, 1, PALCO_H, TRACO)
    if cab:
        tela.texto(cab[0], x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(cab[1], x0, 26, cab[2], tam=17, contorno=PRETO)
    elif tudo:
        tela.texto("JORNADA", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto("COMPLETA", x0, 26, VERDE, tam=17, contorno=PRETO)
    else:
        nome, cor = ETAPAS[k]
        tela.texto(f"ETAPA {k + 1} DE {NE}", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(nome, x0, 26, cor, tam=17, contorno=PRETO)
    for j, (rot, val, cv) in enumerate((linhas or [])[:2]):
        y = 50 + j * 36
        tela.texto(rot, x0, y, ACO3, tam=9, contorno=PRETO)
        if rot.startswith('TEMPO'):
            relogio(tela, x0 + tela.largura_texto(rot, 9) + 9, y + 3, 4, t, vel=.5)
        tam = 17 if tela.largura_texto(val, 17) <= 166 else 9
        tela.texto(val, x0, y + 11, cv, tam=tam, contorno=PRETO)
    if estado:
        rot, val, cv = estado
        tela.texto(rot, x0, 124, ACO3, tam=9, contorno=PRETO)
        tam = 17 if tela.largura_texto(val, 17) <= 166 else 9
        tela.texto(val, x0, 135, cv, tam=tam, contorno=PRETO)
    for j, (nm, cc) in enumerate(ETAPAS):
        bx = x0 + j * 23
        feito = j < k or tudo
        atual = j == k and not tudo and not cab
        tela.ret(bx, 160, 20, 16, PRETO)
        if atual:
            tela.ret(bx + 1, 161, 18, 14, cc)
            tela.ret(bx + 1, 161, 18, 1, BRANCO)
        else:
            tela.ret_vazado(bx + 1, 161, 18, 14, cc if feito else ACO0)
        tela.texto(str(j + 1), bx + 10, 164, PRETO if atual else (cc if feito else ACO1), tam=9, centro=True)
    tela.texto(rodape or 'DA BOCA → À SAÍDA', x0, 186, ACO2, tam=9, contorno=PRETO)


def selo_vertical(tela, k, cx, txt=None):
    """No Short o painel fica de fora: a etapa vai num selo no alto do recorte."""
    s = txt or f"ETAPA {k + 1} DE {NE}: {ETAPAS[k][0]}"
    cor = ETAPAS[k][1] if txt is None else AMARELO
    w = tela.largura_texto(s, 9) + 10
    painel(tela, cx - w // 2, 1, w, 13, borda=cor)
    tela.texto(s, cx, 4, cor, tam=9, centro=True)
