#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep16 — o desenho: bits que brilham, fios que levam 0 e 1,
o transistor (MOSFET) em corte, as portas lógicas, o somador, o processador
de brinquedo (memória, PC, registradores, ULA) e o chip.

A paleta é a `oficina` + silício (dopado N e P), óxido, cobre, o chip e a
placa. Registrada como 'ep16' e o `longo` passa a usá-la neste processo.

A LÓGICA NÃO É DESENHADA À MÃO. `Circuito` calcula o valor de cada fio a
partir das entradas, com atraso: o valor de uma porta no instante t é a
função lógica das entradas em t - atraso, e um ponto a uma fração u do fio
mostra o valor da origem em t - u * atraso_do_fio. Assim o bit "anda" pelo
fio e a saída só muda quando ele chega — e nunca mostra conta errada.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, FUNDO, FUNDO2, FUNDO3, TRACO,
                   ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO,
                   ROSA, ROXO, LATAO, MISTURA, MISTURA2, CHAMA0, CHAMA1, AGUA1)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#241c33', '#3a2d50', '#55456f',                 # 32..34 silício tipo P
          '#14295a', '#2a4f9a', '#5a88e0',                 # 35..37 silício tipo N
          '#4f6f7a', '#a9d3da',                            # 38..39 óxido (isolante)
          '#4a200e', '#9a4a22', '#e08a4a',                 # 40..42 cobre
          '#0d1a24', '#15303f', '#24526a', '#3f88a8',      # 43..46 o chip (die)
          '#0c2418', '#1b4a30', '#2f7a50',                 # 47..49 placa
          '#1d2b44', '#2e4568', '#4b6fa0',                 # 50..52 corpo das portas
          '#20283a']                                       # 53 fio em 0
PX.PALETAS['ep16'] = _BASE + _EXTRA
LG.PAL = 'ep16'
(SIP0, SIP1, SIP2, SIN0, SIN1, SIN2, OX0, OX1, COB0, COB1, COB2, DIE0, DIE1, DIE2, DIE3,
 PCB0, PCB1, PCB2, POR0, POR1, POR2, FIO0) = range(32, 54)

FIO1 = AMARELO                 # fio em 1


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def milhar(n):
    s = f"{abs(int(round(n))):,}".replace(',', '.')
    return ('-' if n < 0 else '') + s
def clamp(u, a=0.0, b=1.0): return max(a, min(b, u))
def lerp(a, b, u): return a + (b - a) * u
def suave(u): u = clamp(u); return u * u * (3 - 2 * u)
def binario(n, bits=4): return format(int(n) & ((1 << bits) - 1), f'0{bits}b')


# ------------------------------------------------------------------ textos e setas
def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9):
    """Texto com fio até a peça (o fio sai do lado do texto mais perto da peça)."""
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    tela.linha(ex, hy + 1, ax, ay + 1, PRETO)
    tela.linha(ex, hy, ax, ay, cor)
    tela.disco(ax, ay, 2, PRETO); tela.disco(ax, ay, 1.2, cor)
    tela.ret(ex - 1, hy - 1, 3, 3, cor)
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)


def centro_preso(tela, txt, cx, y, cor, tam=9, xmin=2, xmax=296):
    w = tela.largura_texto(txt, tam)
    x = int(min(max(cx - w / 2, xmin), xmax - w))
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def seta(tela, x0, y0, x1, y1, cor, esp=2, ponta=5):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * ponta, y1 - uy * ponta
    linha_grossa(tela, x0, y0, bx, by, esp + 2, PRETO)
    linha_grossa(tela, x0, y0, bx, by, esp, cor)
    nx, ny = -uy, ux
    poligono(tela, [(x1 + ux * 1.5, y1 + uy * 1.5), (bx + nx * (ponta + 1.5), by + ny * (ponta + 1.5)),
                    (bx - nx * (ponta + 1.5), by - ny * (ponta + 1.5))], PRETO)
    poligono(tela, [(x1, y1), (bx + nx * ponta, by + ny * ponta), (bx - nx * ponta, by - ny * ponta)], cor)


def bloco(tela, x0, y0, x1, y1, corpo, luz, sombra, textura=None):
    """Peça maciça: contorno preto, corpo, filete de luz em cima, sombra embaixo
    e meio-tom em xadrez no terço de baixo."""
    x0, x1 = sorted((int(round(x0)), int(round(x1)))); y0, y1 = sorted((int(round(y0)), int(round(y1))))
    if x1 - x0 < 1 or y1 - y0 < 1: return
    tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
    tela.ret(x0, y0, x1 - x0, y1 - y0, corpo)
    if y1 - y0 >= 4:
        dither(tela, x0, y0 + (y1 - y0) * 2 // 3, x1 - x0, (y1 - y0) - (y1 - y0) * 2 // 3, corpo, sombra)
    tela.ret(x0, y0, x1 - x0, 1, luz)
    tela.ret(x0, y1 - 1, x1 - x0, 1, sombra)
    if textura is not None and x1 - x0 > 3:
        for k in range(y0 + 2, y1 - 1, 3):
            tela.px(x0 + 1 + (k * 7) % max(1, x1 - x0 - 2), k, textura)


def caixa(tela, x, y, w, h, titulo=None, borda=ACO1, ativo=False, cor_tit=ACO3):
    """Bloco do processador: painel com título pequeno em cima."""
    painel(tela, x, y, w, h, borda=AMARELO if ativo else borda, fundo=PRETO, luz=FUNDO3)
    if titulo:
        tela.texto(titulo, x + 3, y + 3, AMARELO if ativo else cor_tit, tam=9, contorno=PRETO)


def grade_fundo(tela, x1=W, t=0.0):
    """Fundo de placa: escuro, com trilhas apagadas em ângulo reto."""
    tela.buf[:PALCO_H, :x1] = FUNDO
    for x in range(0, x1, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(8, PALCO_H, 16): tela.ret(0, y, x1, 1, FUNDO2)
    for k in range(0, x1, 48):
        tela.ret(k + 8, 8, 1, 1, FUNDO3)


# ------------------------------------------------------------------ o bit que brilha
def bit_luz(tela, x, y, v=1, r=3.0, cor=AMARELO):
    """O protagonista: um pixel aceso (1) com halo, ou apagado (0)."""
    x, y = int(round(x)), int(round(y))
    if v:
        dither(tela, x - int(r) - 2, y - int(r) - 2, 2 * int(r) + 5, 2 * int(r) + 5, FUNDO, FUNDO2) if r >= 6 else None
        tela.disco(x, y, r + 1.2, PRETO)
        tela.disco(x, y, r, cor)
        tela.disco(x, y, max(.6, r * .55), CHAMA0)
        tela.ret(x - 1, y - 1, 2, 2, BRANCO)
    else:
        tela.disco(x, y, r + 1.2, PRETO)
        tela.disco(x, y, r, FUNDO3)
        tela.disco(x, y, max(.6, r * .55), FUNDO2)


def celula(tela, x, y, w, h, v, tam=17, rotulo_txt=True, pulso=0.0):
    """Casa de um número binário: acesa = 1 (amarela, brilha), apagada = 0."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    if v:
        tela.ret(x, y, w, h, AMARELO)
        dither(tela, x, y + h * 2 // 3, w, h - h * 2 // 3, AMARELO, LARANJA)
        tela.ret(x, y, w, 1, CHAMA0)
        tela.ret(x + 1, y + 1, 2, 2, BRANCO)
        if pulso > 0:
            tela.ret(x - 2, y - 2, w + 4, 1, CHAMA0 if pulso > .5 else AMARELO)
            tela.ret(x - 2, y + h + 1, w + 4, 1, CHAMA0 if pulso > .5 else AMARELO)
    else:
        tela.ret(x, y, w, h, FUNDO2)
        dither(tela, x, y + h * 2 // 3, w, h - h * 2 // 3, FUNDO2, FUNDO)
        tela.ret(x, y, w, 1, FUNDO3)
    if rotulo_txt:
        txt = '1' if v else '0'
        tela.texto(txt, x + w // 2, y + (h - (7 if tam == 9 else 14 if tam == 17 else 21)) // 2,
                   PRETO if v else ACO1, tam=tam, centro=True)


# ------------------------------------------------------------------ fios
class Fio:
    """Fio em ângulo reto por uma lista de pontos. `desenhar(val)` pinta cada
    pixel com o valor val(u), u = 0 na origem e 1 no destino."""

    def __init__(self, pts):
        self.pts = [(float(a), float(b)) for a, b in pts]
        seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(self.pts, self.pts[1:])]
        self.L = max(1e-6, sum(seg))
        amostras = []
        acc = 0.0
        for (a, b), s in zip(zip(self.pts, self.pts[1:]), seg):
            n = max(1, int(round(s)))
            for i in range(n):
                f = i / n
                amostras.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (acc + s * f) / self.L))
            acc += s
        amostras.append((self.pts[-1][0], self.pts[-1][1], 1.0))
        self.am = amostras

    def ponto(self, u):
        u = clamp(u)
        d = u * self.L
        for a, b in zip(self.pts, self.pts[1:]):
            s = math.hypot(b[0] - a[0], b[1] - a[1])
            if d <= s or b == self.pts[-1]:
                f = 0 if s == 0 else clamp(d / s)
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            d -= s
        return self.pts[-1]

    def desenhar(self, tela, val, t=0.0, esp=2, fluxo=True, herois=True, r=2.4):
        """Pinta o fio e devolve as frentes de subida (onde um 1 novo está
        chegando): lá o bit protagonista brilha."""
        vs = [val(u) for _, _, u in self.am]
        for x, y, u in self.am:
            tela.ret(int(x) - 1, int(y) - 1, esp + 2, esp + 2, PRETO)
        for k, (x, y, u) in enumerate(self.am):
            if vs[k]:
                cor = CHAMA0 if (fluxo and (k - int(t * 40)) % 9 == 0) else FIO1
            else:
                cor = FIO0
            tela.ret(int(x), int(y), esp, esp, cor)
        frentes = []
        for k in range(len(vs) - 1):
            if vs[k] and not vs[k + 1]:
                frentes.append((self.am[k][0] + esp / 2 - .5, self.am[k][1] + esp / 2 - .5))
        if herois:
            for x, y in frentes: bit_luz(tela, x, y, 1, r)
        return frentes


# ------------------------------------------------------------------ o circuito (a lógica de verdade)
FUNCOES = {
    'E': lambda v: int(v[0] and v[1]),
    'OU': lambda v: int(v[0] or v[1]),
    'NAO': lambda v: int(not v[0]),
    'XOR': lambda v: int(v[0] != v[1]),
    'SOMA': lambda v: int(v[0] ^ v[1] ^ v[2]),               # S = A xor B xor Cin
    'VAI': lambda v: int((v[0] and v[1]) or (v[2] and (v[0] != v[1]))),   # Cout = AB + Cin(A xor B)
}


def _num(x, t): return x(t) if callable(x) else x


class Circuito:
    """Valores dos fios no tempo. entrada(nome, fn) com fn(t) -> 0/1;
    porta(nome, tipo, [(fio, atraso_do_fio), ...], atraso_da_porta)."""

    def __init__(self):
        self.ent, self.pt = {}, {}

    def entrada(self, nome, fn): self.ent[nome] = fn
    def porta(self, nome, tipo, ins, dg): self.pt[nome] = (tipo, ins, dg)

    def val(self, nome, t):
        if nome in self.ent: return int(self.ent[nome](t))
        tipo, ins, dg = self.pt[nome]
        tt = t - _num(dg, t)
        return FUNCOES[tipo]([self.val(n, tt - _num(dw, tt)) for n, dw in ins])

    def no_fio(self, nome, dw, t):
        """Função u -> valor de um fio que sai de `nome` e leva dw segundos."""
        d = _num(dw, t)
        return lambda u: self.val(nome, t - u * d)


# ------------------------------------------------------------------ máscara e peça sombreada
def mascara_poligono(pts, pad=2):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = int(math.floor(min(xs))) - pad, int(math.floor(min(ys))) - pad
    x1, y1 = int(math.ceil(max(xs))) + pad, int(math.ceil(max(ys))) + pad
    m = np.zeros((y1 - y0 + 1, x1 - x0 + 1), bool)
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + .5
        cr = []
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                cr.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        cr.sort()
        for k in range(0, len(cr) - 1, 2):
            a, b = int(round(cr[k])) - x0, int(round(cr[k + 1])) - x0
            if b > a: m[y - y0, a:b] = True
    return m, x0, y0


def _dil(m):
    d = m.copy()
    d[1:] |= m[:-1]; d[:-1] |= m[1:]; d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
    return d


def pintar(tela, m, x0, y0, corpo, luz, sombra, contorno=PRETO, meio=None):
    """Pinta uma máscara como peça: contorno, corpo, luz no topo, dither embaixo."""
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    gy, gx = ys + y0, xs + x0
    ok = (gx >= 0) & (gx < tela.w) & (gy >= 0) & (gy < tela.h)
    d = _dil(m)
    meio = (np.nonzero(m.any(1))[0].mean() if m.any() else 0) if meio is None else meio - y0
    sel = d & ~m & ok
    tela.buf[gy[sel], gx[sel]] = contorno
    topo = m & ~np.vstack([np.zeros((1, w), bool), m[:-1]])
    base = m & (ys > meio + (h - meio) * .25) & ((xs + ys) % 2 == 0)
    for mm, c in ((m, corpo), (base, sombra), (topo, luz)):
        s = mm & ok
        tela.buf[gy[s], gx[s]] = c


# ------------------------------------------------------------------ portas lógicas
def porta_forma(tipo, x0, y, s=1.0):
    """Contorno de uma porta lógica (padrão americano), com a frente em x0 e o
    meio em y. Devolve (pontos, entradas, saída)."""
    hh = 11 * s
    y0, y1 = y - hh, y + hh
    ent = [(x0, y - 6 * s), (x0, y + 6 * s)]
    if tipo in ('E',):
        pts = [(x0, y0), (x0 + 14 * s, y0)]
        for k in range(1, 20):
            a = -math.pi / 2 + math.pi * k / 20
            pts.append((x0 + 14 * s + math.cos(a) * hh, y + math.sin(a) * hh))
        pts += [(x0 + 14 * s, y1), (x0, y1)]
        return pts, ent, (x0 + 14 * s + hh, y)
    if tipo in ('OU', 'XOR'):
        dx = 4 * s if tipo == 'XOR' else 0
        pts = []
        for k in range(0, 21):
            u = k / 20
            pts.append((x0 + dx + 28 * s * u, y0 + hh * u ** 1.8))
        for k in range(1, 21):
            u = 1 - k / 20
            pts.append((x0 + dx + 28 * s * u, y1 - hh * u ** 1.8))
        for k in range(1, 20):
            v = 1 - k / 20
            pts.append((x0 + dx + 5 * s * math.sin(math.pi * v), y0 + 2 * hh * v))
        ent = [(x0 + 3 * s, y - 6 * s), (x0 + 3 * s, y + 6 * s)]
        return pts, ent, (x0 + dx + 28 * s, y)
    if tipo == 'NAO':
        pts = [(x0, y0 + 2 * s), (x0 + 20 * s, y), (x0, y1 - 2 * s)]
        return pts, [(x0, y)], (x0 + 26 * s, y)
    raise ValueError(tipo)


NOMES_PORTA = {'E': 'E', 'OU': 'OU', 'NAO': 'NÃO', 'XOR': 'XOR'}


def porta(tela, tipo, x0, y, s=1.0, saida=0, nome=True, destaque=False):
    """Desenha a porta e devolve (entradas, saída) para ligar os fios."""
    pts, ent, out = porta_forma(tipo, x0, y, s)
    m, mx, my = mascara_poligono(pts)
    c0, c1, c2 = (POR0, POR1, POR2) if not destaque else (POR1, POR2, ACO4)
    pintar(tela, m, mx, my, c1, c2, c0)
    if tipo == 'XOR':
        for k in range(0, 21):
            v = k / 20
            xx = x0 + 5 * s * math.sin(math.pi * v) - 1; yy = y - 11 * s + 22 * s * v
            tela.ret(xx - 1, yy - 1, 3, 3, PRETO)
        for k in range(0, 21):
            v = k / 20
            xx = x0 + 5 * s * math.sin(math.pi * v) - 1; yy = y - 11 * s + 22 * s * v
            tela.px(xx, yy, c2)
    if tipo == 'NAO':
        bx = x0 + 22.5 * s
        tela.disco(bx, y, 2.6 * s + 1, PRETO)
        tela.disco(bx, y, 2.6 * s, c1)
        tela.px(bx - 1, y - 1, c2)
    # LED da saída
    lx = out[0] - (8 * s if tipo != 'NAO' else 12 * s)
    if nome and s >= .9:
        txt = NOMES_PORTA[tipo]
        tw = tela.largura_texto(txt, 9)
        cx = (x0 + (out[0] - (6 * s if tipo == 'NAO' else 0))) / 2 + (2 * s if tipo in ('OU', 'XOR') else -1 * s)
        if tipo == 'NAO': cx = x0 + 7 * s
        tela.texto(txt, int(cx - tw / 2), int(y - 3), BRANCO if destaque else ACO4, tam=9, contorno=PRETO)
    return ent, out


# ------------------------------------------------------------------ o transistor
class Mosfet:
    """MOSFET canal N em corte, visto de lado. (x, y) = canto de cima à
    esquerda do silício; s = escala. vg em 0..1 = tensão na porta."""

    def __init__(self, x, y, s=1.0, seed=3):
        self.x, self.y, self.s = x, y, s
        rng = np.random.default_rng(seed)
        self.w, self.h = 200 * s, 92 * s
        # elétrons livres nas regiões N (fonte e dreno)
        self.eN = [(rng.uniform(4, 58), rng.uniform(4, 30), rng.uniform(0, 6.28)) for _ in range(34)]
        self.eD = [(rng.uniform(142, 196), rng.uniform(4, 30), rng.uniform(0, 6.28)) for _ in range(34)]
        # buracos (+) no silício P
        self.bP = [(rng.uniform(6, 194), rng.uniform(40, 88), rng.uniform(0, 6.28)) for _ in range(30)]
        self.canal = [rng.uniform(0, 1) for _ in range(26)]

    def P(self, a, b): return self.x + a * self.s, self.y + b * self.s

    def regioes(self):
        return dict(fonte=self.P(30, 16), dreno=self.P(170, 16), porta=self.P(100, -22), oxido=self.P(100, -4),
                    canal=self.P(100, 4), silicio=self.P(100, 66))

    def desenhar(self, tela, vg, t, corrente=True, rot=True):
        s = self.s
        X, Y = self.x, self.y
        Wd, Hd = self.w, self.h
        # silício P (o corpo)
        tela.ret(X - 1, Y - 1, Wd + 2, Hd + 2, PRETO)
        dither(tela, X, Y, Wd, Hd, SIP1, SIP0)
        tela.ret(X, Y, Wd, Hd * .5, SIP1)
        dither(tela, X, Y + Hd * .5, Wd, Hd * .5, SIP1, SIP0)
        tela.ret(X, Y + Hd - 2, Wd, 2, SIP0)
        # regiões N (fonte e dreno)
        for a in (0, 140):
            x0, y0 = self.P(a, 0); x1, y1 = self.P(a + 60, 34)
            tela.ret(x0, y0, x1 - x0, y1 - y0, SIN1)
            dither(tela, x0, y0 + (y1 - y0) * .6, x1 - x0, (y1 - y0) * .4 + 1, SIN1, SIN0)
            tela.ret(x0, y1, x1 - x0, 1, PRETO)
            tela.ret(x1 if a == 0 else x0 - 1, y0, 1, y1 - y0, PRETO)
        # elétrons
        for lst in (self.eN, self.eD):
            for ex, ey, f in lst:
                xx, yy = self.P(ex + 1.5 * math.sin(t * 2.2 + f), ey + 1.2 * math.cos(t * 1.7 + f * 2))
                tela.px(xx, yy, CIANO); tela.px(xx + 1, yy, AGUA1)
        for bx, by, f in self.bP:
            xx, yy = self.P(bx + math.sin(t * 1.3 + f), by + math.cos(t * 1.1 + f))
            tela.px(xx, yy, SIP2)
        # canal: uma faixa fina de elétrons logo abaixo do óxido
        x0c, y0c = self.P(60, 0); x1c, _ = self.P(140, 0)
        cw = x1c - x0c
        if vg > .05:
            esp = max(1, int(round(4 * s * vg)))
            dither(tela, x0c, y0c, cw, esp, SIN1 if vg > .6 else SIN0, SIP1)
            n = int(len(self.canal) * vg)
            vel = 30 * s if corrente else 0
            for k in range(n):
                xx = x0c + ((self.canal[k] * cw + t * vel) % cw)
                yy = y0c + 1 + (k % max(1, esp - 1))
                tela.px(xx, yy, CIANO); tela.px(xx + 1, yy, BRANCO if vg > .8 else AGUA1)
        # óxido (isolante fino)
        xo0, yo0 = self.P(56, -5); xo1, yo1 = self.P(144, 0)
        tela.ret(xo0 - 1, yo0 - 1, xo1 - xo0 + 2, yo1 - yo0 + 1, PRETO)
        tela.ret(xo0, yo0, xo1 - xo0, yo1 - yo0, OX0)
        tela.ret(xo0, yo0, xo1 - xo0, 1, OX1)
        # porta (metal)
        xg0, yg0 = self.P(60, -30); xg1, yg1 = self.P(140, -5)
        bloco(tela, xg0, yg0, xg1, yg1 - 1, ACO2 if vg < .5 else ACO3, ACO4, ACO0)
        if vg > .3:
            for k in range(7):
                px_, py_ = xg0 + 6 * s + k * (xg1 - xg0 - 12 * s) / 6, yg1 - 6 * s
                tela.ret(px_ - 1, py_, 3, 1, AMARELO); tela.ret(px_, py_ - 1, 1, 3, AMARELO)
        # contatos de metal: fonte, porta, dreno
        for a, b0 in ((30, 0), (170, 0)):
            cx, cy = self.P(a, b0)
            bloco(tela, cx - 7 * s, cy - 18 * s, cx + 7 * s, cy, COB1, COB2, COB0)
        cx, cy = self.P(100, -30)
        bloco(tela, cx - 6 * s, cy - 14 * s, cx + 6 * s, cy, COB1, COB2, COB0)

    def topo_contatos(self):
        s = self.s
        return dict(fonte=self.P(30, -18), dreno=self.P(170, -18), porta=self.P(100, -44))


def chave_mos(tela, x, y, tipo, ligado, s=1.0, val_porta=0):
    """Símbolo simples de transistor: duas pontas na vertical (x, y-12..y+12),
    a porta à esquerda (x-12, y). P tem a bolinha na porta (liga com 0)."""
    cor = AMARELO if ligado else ACO1
    tela.ret(x - 1, y - 13 * s, 4, 6 * s + 1, PRETO); tela.ret(x, y - 12 * s, 2, 6 * s, cor if ligado else ACO2)
    tela.ret(x - 1, y + 6 * s, 4, 7 * s + 1, PRETO); tela.ret(x, y + 7 * s, 2, 6 * s, cor if ligado else ACO2)
    # canal: barra vertical, cheia quando ligado
    tela.ret(x - 1, y - 7 * s, 4, 14 * s + 1, PRETO)
    if ligado:
        tela.ret(x, y - 6 * s, 2, 13 * s, AMARELO)
    else:
        for k in range(int(-6 * s), int(7 * s), 3):
            tela.ret(x, y + k, 2, 1, ACO1)
    # a porta (placa ao lado)
    tela.ret(x - 6 * s - 1, y - 7 * s, 3, 14 * s + 1, PRETO)
    tela.ret(x - 6 * s, y - 6 * s, 1, 13 * s, ACO4 if val_porta else ACO2)
    if tipo == 'p':
        tela.disco(x - 9 * s, y, 2.4 * s + 1, PRETO); tela.disco(x - 9 * s, y, 2.4 * s, ACO3)
        return (x - 12 * s, y)
    return (x - 7 * s, y)


# ------------------------------------------------------------------ tabela-verdade
def tabela(tela, x, y, cab, linhas, atual=-1, vistos=(), larg=None, alto=12, n_out=1):
    """cab: títulos das colunas; linhas: listas de valores (0/1). Linha atual
    em amarelo; linhas ainda não vistas ficam apagadas, com '?'."""
    n = len(cab)
    larg = larg or [22] * n
    xx = x
    for j, c in enumerate(cab):
        tela.texto(c, xx + larg[j] // 2, y, ACO3 if j < n - n_out else LARANJA, tam=9, centro=True, contorno=PRETO)
        xx += larg[j]
    tela.ret(x, y + 10, sum(larg), 1, FUNDO3)
    for i, ln in enumerate(linhas):
        yy = y + 14 + i * alto
        if i == atual:
            tela.ret(x - 2, yy - 2, sum(larg) + 4, alto - 1, FUNDO3)
        xx = x
        for j, v in enumerate(ln):
            if j >= n - n_out and i not in vistos and i != atual:
                txt, cor = '?', ACO1
            else:
                txt = str(v)
                cor = (AMARELO if v else ACO2) if i == atual else (ACO4 if v else ACO1)
                if j >= n - n_out and i == atual: cor = CHAMA0 if v else ACO3
            tela.texto(txt, xx + larg[j] // 2, yy, cor, tam=9, centro=True, contorno=PRETO)
            xx += larg[j]


# ------------------------------------------------------------------ o chip
def die(tela, x, y, w, h, t=0.0, nucleos=4, aceso=None, grade=True):
    """Pastilha de silício vista de cima: núcleos, memória rápida (cache) em
    grade e o anel de contatos na borda. Genérica, sem marca."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, DIE1)
    dither(tela, x, y + h * 2 // 3, w, h - h * 2 // 3, DIE1, DIE0)
    tela.ret(x, y, w, 1, DIE3)
    if w < 16: return []
    # anel de contatos
    for k in range(x + 3, x + w - 3, 4):
        tela.px(k, y + 2, COB2); tela.px(k, y + h - 3, COB2)
    for k in range(y + 3, y + h - 3, 4):
        tela.px(x + 2, k, COB2); tela.px(x + w - 3, k, COB2)
    # núcleos em cima, cache embaixo
    m = 6
    cw = (w - 2 * m - (nucleos - 1) * 3) / nucleos
    caixas = []
    for i in range(nucleos):
        cx0 = x + m + i * (cw + 3)
        cy0, ch = y + m, (h - 2 * m) * .55
        on = aceso is None or i in aceso
        tela.ret(cx0, cy0, cw, ch, DIE2 if on else DIE1)
        tela.ret(cx0, cy0, cw, 1, DIE3)
        if grade and cw > 8:
            for k in range(int(cx0) + 2, int(cx0 + cw) - 1, 3):
                for j in range(int(cy0) + 3, int(cy0 + ch) - 1, 3):
                    if (k * 7 + j * 3 + int(t * 6) * (i + 1)) % 11 < 3:
                        tela.px(k, j, DIE3 if on else DIE2)
        caixas.append((cx0, cy0, cw, ch))
    yc = y + m + (h - 2 * m) * .55 + 3
    hc = y + h - m - yc
    if hc > 4:
        tela.ret(x + m, yc, w - 2 * m, hc, DIE0)
        for k in range(x + m + 1, x + w - m - 1, 2):
            for j in range(int(yc) + 1, int(yc + hc) - 1, 2):
                tela.px(k, j, DIE2 if (k + j) % 4 == 0 else DIE1)
    return caixas


def placa(tela, x, y, w, h):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    dither(tela, x, y, w, h, PCB1, PCB0)
    tela.ret(x, y, w, 1, PCB2)
    for k in range(6):
        yy = y + 8 + k * (h - 16) / 5
        tela.ret(x + 4, yy, w - 8, 1, PCB2 if k % 2 else PCB1)


def pacote(tela, cx, cy, lado, t=0.0, nucleos=4, aceso=None):
    """Chip montado: base verde com pinos, pastilha no meio."""
    b = lado * 1.5
    x0, y0 = cx - b / 2, cy - b / 2
    tela.ret(x0 - 1, y0 - 1, b + 2, b + 2, PRETO)
    dither(tela, x0, y0, b, b, PCB2, PCB1)
    tela.ret(x0, y0, b, 1, ACO3)
    for k in range(int(x0) + 2, int(x0 + b) - 1, 3):
        tela.px(k, y0 + b - 2, LATAO); tela.px(k, y0 + 1, LATAO)
    return die(tela, cx - lado / 2, cy - lado / 2, lado, lado, t=t, nucleos=nucleos, aceso=aceso)


# ------------------------------------------------------------------ o processador de brinquedo
OPS = {1: 'CARREGA A', 2: 'CARREGA B', 3: 'SOMA A+B', 4: 'GUARDA A', 5: 'PULA'}
PROGRAMA = [(1, 8), (2, 9), (3, 0), (4, 10), (5, 2)]     # endereços 0..4
DADOS = {8: 5, 9: 3, 10: 0}


def palavra(op, arg): return (op << 4) | arg


def texto_instr(op, arg):
    if op == 1: return f"A = M{arg}"
    if op == 2: return f"B = M{arg}"
    if op == 3: return "A = A + B"
    if op == 4: return f"M{arg} = A"
    if op == 5: return f"VAI P/ {arg}"
    return ""


class CPU:
    """A máquina de verdade, simulada: cada etapa muda o estado.
    BUSCA: IR = M[PC]; PC = PC + 1.  DECODIFICA: o controle lê o IR.
    EXECUTA: faz a operação."""

    def __init__(self):
        self.mem = [0] * 16
        for i, (op, arg) in enumerate(PROGRAMA): self.mem[i] = palavra(op, arg)
        for k, v in DADOS.items(): self.mem[k] = v
        self.pc, self.ir, self.a, self.b = 0, 0, 0, 0
        self.etapa = 2                      # a próxima é BUSCA
        self.n_instr = 0

    def estado(self):
        return dict(mem=list(self.mem), pc=self.pc, ir=self.ir, a=self.a, b=self.b, etapa=self.etapa,
                    n=self.n_instr)

    def passo(self):
        self.etapa = (self.etapa + 1) % 3
        if self.etapa == 0:
            self.ir = self.mem[self.pc]; self.pc = (self.pc + 1) & 15
        elif self.etapa == 2:
            op, arg = self.ir >> 4, self.ir & 15
            if op == 1: self.a = self.mem[arg]
            elif op == 2: self.b = self.mem[arg]
            elif op == 3: self.a = (self.a + self.b) & 255
            elif op == 4: self.mem[arg] = self.a
            elif op == 5: self.pc = arg
            self.n_instr += 1
        return self.estado()


ETAPAS = ['BUSCA', 'DECODIFICA', 'EXECUTA']
