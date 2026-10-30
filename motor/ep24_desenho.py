#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep24 — o desenho: roteador, celular e outros aparelhos
genéricos, o ícone de 3 arcos, o pacote de bits que brilha, ondas (trem de
seno, anéis que crescem), a constelação 16-QAM CALCULADA, o mapa de sinal
da casa (inverso do quadrado + paredes) e o painel da direita.

A paleta do episódio é a `oficina` + cores de onda de rádio, concreto,
madeira, plástico do roteador, tela, água, planta e erro. Registrada como
'ep24'; o `longo` passa a usá-la neste processo.

A CONSTELAÇÃO: 16-QAM com código de Gray. Os 4 bits b3 b2 b1 b0 de um
símbolo: b3 b2 escolhem o nível do eixo I, b1 b0 o do eixo Q, com o Gray de
2 bits (00 -> -3, 01 -> -1, 11 -> +1, 10 -> +3). O import confere que os 16
pontos são distintos e que todo par de vizinhos (lado a lado na grade)
difere em exatamente 1 bit. O pedaço de onda de um símbolo é
s(u) = I cos(2 pi c u) - Q sen(2 pi c u), u em [0, 1), c ciclos por símbolo:
a amplitude é raiz(I^2 + Q^2) e a fase é atan2(Q, I).
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, FUNDO, FUNDO2, FUNDO3, TRACO,
                   ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO,
                   ROSA, ROXO, LATAO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, CERAMICA, AGUA0, AGUA1)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#2a1748', '#5b2f9a', '#9a63f0', '#dcc6ff',      # 32..35 onda de rádio (escuro -> luz)
          '#3e3e45', '#62626a', '#8e8e96',                 # 36..38 concreto
          '#3a2414', '#5e3b20', '#8a5c33',                 # 39..41 madeira
          '#1c2134', '#2a3150',                            # 42..43 parede de dentro
          '#7e8698', '#b3bccb', '#e2e8f0',                 # 44..46 plástico do roteador
          '#0f2c44', '#1d5f8c',                            # 47..48 tela
          '#123e66', '#2a78b8', '#7cc4f0',                 # 49..51 água
          '#1a5228', '#2f8f45',                            # 52..53 planta
          '#5a1020', '#a01c34',                            # 54..55 erro
          '#14302a', '#24584a', '#3f8f74', '#8ee0b8']      # 56..59 mapa de sinal (fraco -> forte)
PX.PALETAS['ep24'] = _BASE + _EXTRA
LG.PAL = 'ep24'
(OND0, OND1, OND2, OND3, CON0, CON1, CON2, MAD0, MAD1, MAD2, PAR0, PAR1, PLA0, PLA1, PLA2,
 TEL0, TEL1, AGU0, AGU1, AGU2, PLN0, PLN1, ERR0, ERR1, SIN0, SIN1, SIN2, SIN3) = range(32, 60)

C_LUZ = 299_792_458.0                      # m/s (F5)


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def milhar(n):
    s = f"{abs(int(round(n))):,}".replace(',', '.')
    return ('-' if n < 0 else '') + s
def clamp(u, a=0.0, b=1.0): return max(a, min(b, u))
def lerp(a, b, u): return a + (b - a) * u
def suave(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease(u): u = clamp(u); return 1 - (1 - u) ** 3


def lambda_cm(f_ghz): return C_LUZ / (f_ghz * 1e9) * 100.0


# ------------------------------------------------------------------ a constelação (calculada)
GRAY2 = {0b00: -3, 0b01: -1, 0b11: 1, 0b10: 3}           # Gray de 2 bits -> nível


def qam16():
    """{símbolo de 4 bits: (I, Q)} com Gray nos dois eixos."""
    return {s: (GRAY2[s >> 2], GRAY2[s & 3]) for s in range(16)}


QAM16 = qam16()
QAM16_INV = {v: k for k, v in QAM16.items()}


def _conferir_gray():
    assert len(QAM16_INV) == 16
    for (i, q), s in QAM16_INV.items():
        for di, dq in ((2, 0), (0, 2)):
            v = QAM16_INV.get((i + di, q + dq))
            if v is not None:
                assert bin(s ^ v).count('1') == 1, (s, v)
    return True


GRAY_OK = _conferir_gray()


def bits4(s): return format(s, '04b')


def gray_niveis(m):
    """Níveis de um eixo de uma M-QAM quadrada com Gray: lista de (nível, código)."""
    k = int(round(math.log2(m))) // 2
    n = 2 ** k
    out = []
    for i in range(n):
        out.append((2 * i - (n - 1), i ^ (i >> 1)))
    return out, k


def conferir_gray_m(m):
    niv, k = gray_niveis(m)
    for a, b in zip(niv, niv[1:]):
        assert bin(a[1] ^ b[1]).count('1') == 1
    return True


assert conferir_gray_m(256) and conferir_gray_m(1024)

# os bits do pacote protagonista (4 bytes de carga de exemplo) -> 8 símbolos
PACOTE_BYTES = [0xB2, 0x4D, 0x1E, 0x87]
PACOTE_BITS = ''.join(format(b, '08b') for b in PACOTE_BYTES)
PACOTE_SIMB = [int(PACOTE_BITS[k:k + 4], 2) for k in range(0, 32, 4)]


def onda_simbolo(I, Q, u, ciclos=2):
    """Valor normalizado (máx 1) do pedaço de onda do símbolo (I, Q)."""
    return (I * np.cos(2 * np.pi * ciclos * u) - Q * np.sin(2 * np.pi * ciclos * u)) / (3 * math.sqrt(2))


# ------------------------------------------------------------------ peças de desenho
def halo(tela, cx, cy, r, cor, fase=0):
    """Brilho em xadrez em volta de uma peça luminosa."""
    x0, x1 = max(0, int(cx - r)), min(tela.w, int(cx + r + 1))
    y0, y1 = max(0, int(cy - r)), min(PALCO_H, int(cy + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & ((xx + yy + fase) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def bloco(tela, x0, y0, x1, y1, corpo, luz, sombra):
    """Peça maciça: contorno, corpo, filete de luz, sombra com meio-tom."""
    x0, x1 = sorted((int(round(x0)), int(round(x1)))); y0, y1 = sorted((int(round(y0)), int(round(y1))))
    if x1 - x0 < 1 or y1 - y0 < 1: return
    tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
    tela.ret(x0, y0, x1 - x0, y1 - y0, corpo)
    if y1 - y0 >= 4:
        dither(tela, x0, y0 + (y1 - y0) * 2 // 3, x1 - x0, (y1 - y0) - (y1 - y0) * 2 // 3, corpo, sombra)
    tela.ret(x0, y0, x1 - x0, 1, luz)
    tela.ret(x0, y1 - 1, x1 - x0, 1, sombra)


def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9, cotovelo=None):
    """Texto com fio até a peça; `cotovelo` = ponto do meio (fio em L)."""
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    pts = [(ex, hy)] + ([cotovelo] if cotovelo else []) + [(ax, ay)]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        tela.linha(a, b + 1, c, d + 1, PRETO)
        tela.linha(a + 1, b, c + 1, d, PRETO)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        tela.linha(a, b, c, d, cor)
    tela.disco(ax, ay, 2.2, PRETO); tela.disco(ax, ay, 1.3, cor)
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


def grade_fundo(tela, x1=W, t=0.0, passo=12):
    """Fundo: noite azul-escura com uma grade de pixels bem apagada."""
    tela.buf[:PALCO_H, :x1] = FUNDO
    for x in range(0, x1, passo): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(6, PALCO_H, passo): tela.ret(0, y, x1, 1, FUNDO2)
    k = int(t * 2)
    for j in range(6):
        gx = ((j * 97 + k * 12) % max(1, x1 // passo)) * passo
        gy = ((j * 53 + k * 6) % (PALCO_H // passo)) * passo + 6
        tela.ret(gx + 1, gy + 1, passo - 1, passo - 1, FUNDO2)


# ------------------------------------------------------------------ aparelhos
def icone_wifi(tela, cx, cy, r, n=3, cor=BRANCO, apagado=ACO1, contorno=True):
    """O ícone genérico de 3 arcos (sem logotipo). (cx, cy) = o ponto de baixo."""
    x0, x1 = max(0, int(cx - r - 2)), min(tela.w, int(cx + r + 3))
    y0, y1 = max(0, int(cy - r - 2)), min(tela.h, int(cy + 3))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx, dy = xx - cx, cy - yy
    d = np.sqrt(dx * dx + dy * dy)
    cone = (dy > 0) & (np.abs(dx) <= dy * 1.0 + .5)
    esp = max(1.0, r / 9)
    sub = tela.buf[y0:y1, x0:x1]
    if contorno:
        for k in range(3):
            rr = r * (k + 1) / 3
            sub[cone & (np.abs(d - rr) <= esp + 1)] = PRETO
        sub[d <= esp + 1.6] = PRETO
    for k in range(3):
        rr = r * (k + 1) / 3
        sub[cone & (np.abs(d - rr) <= esp)] = cor if k < n else apagado
    sub[d <= esp + .6] = cor if n > 0 else apagado


def celular(tela, x, y, w, h, t=0.0, cor=ACO1, tela_cor=TEL0, wifi=3, brilho=False):
    """Celular genérico; devolve o retângulo da tela (sx, sy, sw, sh)."""
    tela.ret(x + 1, y - 1, w - 2, h + 2, PRETO); tela.ret(x - 1, y + 1, w + 2, h - 2, PRETO)
    tela.ret(x, y, w, h, cor)
    tela.ret(x + 1, y + 1, w - 2, 1, ACO3); tela.ret(x + 1, y + 1, 1, h - 2, ACO2)
    tela.ret(x + w - 2, y + 2, 1, h - 3, ACO0); tela.ret(x + 2, y + h - 2, w - 3, 1, ACO0)
    tela.ret(x + w, y + h // 4, 1, max(3, h // 8), ACO2)
    m = max(2, w // 10)
    sx, sy, sw, sh = x + m, y + m + 3, w - 2 * m, h - 2 * m - 6
    tela.ret(sx - 1, sy - 1, sw + 2, sh + 2, PRETO)
    tela.ret(sx, sy, sw, sh, tela_cor)
    dither(tela, sx, sy + sh * 2 // 3, sw, sh - sh * 2 // 3, tela_cor, TEL1 if tela_cor == TEL0 else tela_cor)
    tela.ret(x + w // 2 - 3, y + m, 6, 1, PRETO)
    if wifi is not None and sw >= 10:
        r = min(sw, sh) * .32
        icone_wifi(tela, sx + sw / 2, sy + sh * .42 + r * .5, r, wifi, BRANCO, TEL1, contorno=False)
    if brilho: tela.ret(sx, sy, sw, 1, CIANO)
    return sx, sy, sw, sh


def roteador(tela, x, y, t=0.0, s=1.0, ativo=0.0, antenas=True):
    """Roteador genérico de mesa. (x, y) = canto de cima à esquerda do corpo.
    Devolve as pontas das antenas [(x, y), (x, y)]."""
    w, h = int(48 * s), int(14 * s)
    pontas = []
    if antenas:
        for ax in (x + int(7 * s), x + w - int(7 * s)):
            top = y - int(28 * s)
            tela.ret(ax - 2, top - 1, 5, y - top + 2, PRETO)
            tela.ret(ax - 1, top, 3, y - top, ACO0)
            tela.ret(ax - 1, top, 1, y - top, ACO2)
            tela.ret(ax - 2, y - 4, 5, 4, ACO1)
            tela.ret(ax - 1, top, 3, 2, ACO3)
            pontas.append((ax, top))
    # corpo: plástico claro com sombreado
    tela.ret(x + 1, y - 1, w - 2, h + 2, PRETO); tela.ret(x - 1, y + 1, w + 2, h - 2, PRETO)
    tela.ret(x, y, w, h, PLA1)
    tela.ret(x + 1, y, w - 2, 1, PLA2)
    dither(tela, x, y + h * 2 // 3, w, h - h * 2 // 3, PLA1, PLA0)
    tela.ret(x, y + h - 1, w, 1, PLA0)
    # luzes da frente
    for k in range(4):
        lx = x + int(8 * s) + k * int(7 * s)
        ly = y + h // 2 - 1
        acesa = k == 0 or (k == 1 and ativo > 0 and int(t * 12 + k) % 2 == 0) or (k == 2 and int(t * 3) % 3 != 0)
        c = VERDE if acesa else ACO1
        tela.ret(lx, ly, 2, 2, c)
        if acesa and k == 1: tela.px(lx, ly - 1, BRANCO)
    # pezinhos
    tela.ret(x + 3, y + h + 1, 4, 1, PRETO); tela.ret(x + w - 7, y + h + 1, 4, 1, PRETO)
    return pontas


def notebook(tela, x, y, w=40, h=26, t=0.0, ativo=False):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO1)
    tela.ret(x + 2, y + 2, w - 4, h - 4, TEL0)
    dither(tela, x + 2, y + 2 + (h - 4) // 2, w - 4, (h - 4) - (h - 4) // 2, TEL0, TEL1)
    for k in range(3):
        tela.ret(x + 5, y + 5 + k * 5, (w - 14) - (k * 7) % 11, 2, CIANO if ativo and k == int(t * 4) % 3 else ACO2)
    tela.ret(x - 5, y + h + 1, w + 10, 5, PRETO)
    tela.ret(x - 4, y + h + 1, w + 8, 4, ACO2)
    tela.ret(x - 4, y + h + 1, w + 8, 1, ACO4)
    tela.ret(x + w // 2 - 5, y + h + 3, 10, 1, ACO1)


def tv(tela, x, y, w=54, h=32, t=0.0):
    tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
    tela.ret(x - 1, y - 1, w + 2, h + 2, ACO0)
    tela.ret(x, y, w, h, TEL0)
    for k in range(4):
        c = [AGU1, PLN1, LARANJA, OND2][(k + int(t * .7)) % 4]
        tela.ret(x + 2 + k * (w - 4) // 4, y + 2, (w - 4) // 4, h - 4, c)
    tela.ret(x, y, w, 1, ACO3)
    tela.ret(x + w // 2 - 2, y + h + 2, 4, 3, ACO1); tela.ret(x + w // 2 - 9, y + h + 5, 18, 2, ACO1)


def tablet(tela, x, y, w=30, h=40, t=0.0):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO2)
    tela.ret(x + 3, y + 3, w - 6, h - 6, TEL0)
    dither(tela, x + 3, y + 3 + (h - 6) // 2, w - 6, (h - 6) - (h - 6) // 2, TEL0, TEL1)
    tela.ret(x + 6, y + 8, w - 12, 8, ROSA if int(t) % 2 else OND2)


def pacote(tela, cx, cy, n=None, t=0.0, s=1, cor=AMARELO, bits=None, brilho=True, embaralhado=False):
    """O protagonista: um bloco de bits que brilha. (cx, cy) = centro.
    Cabeçalho colorido com o número, carga com 8 bits acesos/apagados."""
    w, h = 30 * s, 14 * s
    x, y = int(cx - w / 2), int(cy - h / 2)
    if brilho:
        halo(tela, cx, cy, w * .72, CHAMA1 if cor == AMARELO else cor, int(t * 8) % 2)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO0)
    hw = 10 * s
    tela.ret(x, y, hw, h, cor)
    dither(tela, x, y + h * 2 // 3, hw, h - h * 2 // 3, cor, LARANJA if cor == AMARELO else ACO2)
    tela.ret(x, y, hw, 1, CHAMA0 if cor == AMARELO else BRANCO)
    tela.ret(x + hw, y, 1, h, PRETO)
    if n is not None:
        tela.texto(str(n), x + hw // 2 + 1, y + h // 2 - 3 * s, PRETO, tam=9 if s == 1 else 17, centro=True)
    bb = bits if bits is not None else PACOTE_BITS[:8]
    cw = (w - hw - 2) // 4
    for k in range(8):
        bx = x + hw + 1 + (k % 4) * cw
        by = y + 1 + (k // 4) * ((h - 2) // 2)
        v = bb[k] == '1'
        if embaralhado: c = ROSA if v else ACO1
        else: c = CHAMA0 if v else ACO1
        tela.ret(bx + 1, by + 1, cw - 1, (h - 2) // 2 - 1, c)
    tela.ret(x, y, w, 1, ACO3 if cor != AMARELO else CHAMA0)


def cadeado(tela, x, y, s=1, cor=AMARELO, aberto=0.0):
    w, h = 8 * s, 6 * s
    ay = y - int(aberto * 3 * s)
    tela.ret(x + 1 * s, ay - 4 * s, 6 * s, 1 * s, PRETO)
    tela.ret(x + 1 * s, ay - 4 * s, 1 * s, 5 * s, PRETO); tela.ret(x + 6 * s, ay - 4 * s, 1 * s, 5 * s if aberto < .5 else 2 * s, PRETO)
    tela.ret(x + 2 * s, ay - 3 * s, 4 * s, 1 * s, ACO3)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, cor)
    tela.ret(x, y, w, 1, CHAMA0 if cor == AMARELO else BRANCO)
    tela.ret(x + w // 2 - 1, y + 2 * s, 2, 2 * s, PRETO)


# ------------------------------------------------------------------ ondas
def onda(tela, x0, x1, yc, amp, lam, fase=0.0, cor=OND2, cor_luz=OND3, sombra=OND0, fn=None, esp=1):
    """Trem de seno de x0 a x1 (traço contínuo com contorno e luz). `amp`
    pode ser número ou função de x; `fn(x)` substitui o seno (valor -1..1)."""
    xs = np.arange(int(x0), int(x1))
    if len(xs) < 2: return
    a = np.array([amp(x) for x in xs]) if callable(amp) else np.full(len(xs), float(amp))
    v = fn(xs) if fn is not None else np.sin(2 * np.pi * (xs - x0) / lam - fase)
    ys = np.round(yc - a * v).astype(int)
    for i in range(len(xs)):
        y_a = ys[i]; y_b = ys[i + 1] if i + 1 < len(xs) else ys[i]
        lo, hi = min(y_a, y_b), max(y_a, y_b)
        tela.ret(xs[i] - 1, lo - 1 - esp // 2, 3, hi - lo + 2 + esp, PRETO)
    for i in range(len(xs)):
        y_a = ys[i]; y_b = ys[i + 1] if i + 1 < len(xs) else ys[i]
        lo, hi = min(y_a, y_b), max(y_a, y_b)
        tela.ret(xs[i], lo - esp // 2, 1, hi - lo + esp, cor)
        if a[i] > 2 and abs(v[i]) > .92: tela.px(xs[i], ys[i] - (1 if v[i] > 0 else -1) * 0, cor_luz)


def aneis(tela, cx, cy, t, vel=40.0, passo=26.0, rmax=260.0, cor=OND2, cor2=OND1, apagar=True, esp=1.0,
          fantasma=False):
    """Frentes de onda (círculos) que nascem em (cx, cy) e crescem: uma a
    cada `passo` px. Mais longe, mais apagadas (pontilhadas)."""
    r0 = (t * vel) % passo
    r = r0
    while r < rmax:
        u = r / rmax
        if fantasma:
            if int(r) % 3 == 0: tela.anel(cx, cy, r, FUNDO3, .5)
        else:
            c = cor if u < .45 else cor2
            tela.anel(cx, cy, r, c, esp if u < .7 else .5)
        r += passo


def barras_sinal(tela, x, y, n, total=4, h=14, cor=VERDE):
    """Barrinhas de sinal: `n` acesas de `total`."""
    for k in range(total):
        bh = int(h * (k + 1) / total)
        bx = x + k * 6
        tela.ret(bx - 1, y + h - bh - 1, 6, bh + 2, PRETO)
        tela.ret(bx, y + h - bh, 4, bh, cor if k < n else FUNDO3)
        if k < n: tela.ret(bx, y + h - bh, 4, 1, BRANCO)


def barras_de_dbm(dbm):
    if dbm is None: return 0
    if dbm >= -50: return 4
    if dbm >= -60: return 3
    if dbm >= -70: return 2
    if dbm >= -82: return 1
    return 0


def cor_dbm(dbm):
    if dbm is None: return ACO2
    return VERDE if dbm >= -60 else (AMARELO if dbm >= -72 else (LARANJA if dbm >= -82 else VERMELHO))


# ------------------------------------------------------------------ a constelação na tela
def constelacao(tela, cx, cy, passo, t=0.0, ativo=None, vizinhos=None, rotulos=True, eixos=True, mostrar=1.0,
                cor_ponto=OND3, alvo_dif=None):
    """Desenha o 16-QAM calculado. `ativo` = símbolo aceso; `vizinhos` =
    símbolos com contorno; `alvo_dif` = símbolo de referência para pintar de
    vermelho o bit que muda."""
    if eixos:
        L = int(passo * 2.2)
        tela.ret(cx - L, cy, 2 * L + 1, 1, TRACO); tela.ret(cx, cy - L, 1, 2 * L + 1, TRACO)
        tela.texto('I', cx + L + 3, cy - 3, ACO2, tam=9, contorno=PRETO)
        tela.texto('Q', cx - 2, cy - L - 10, ACO2, tam=9, contorno=PRETO)
    pts = sorted(QAM16.items(), key=lambda kv: (kv[1][1], kv[1][0]))
    for k, (s, (I, Q)) in enumerate(pts):
        if k >= mostrar * 16: continue
        px = int(cx + I * passo / 2); py = int(cy - Q * passo / 2)
        acesa = ativo == s
        if acesa:
            halo(tela, px, py, 9, CHAMA1, int(t * 8) % 2)
        c = AMARELO if acesa else (CIANO if vizinhos and s in vizinhos else cor_ponto)
        tela.ret(px - 3, py - 3, 7, 7, PRETO)
        tela.ret(px - 2, py - 2, 5, 5, c)
        tela.px(px - 2, py - 2, BRANCO)
        if rotulos:
            b = bits4(s)
            lx = px - tela.largura_texto(b, 9) // 2
            if alvo_dif is not None and s in (vizinhos or ()):
                ref = bits4(alvo_dif)
                xx = lx
                for i, ch in enumerate(b):
                    cc = VERMELHO if ch != ref[i] else ACO4
                    tela.texto(ch, xx, py + 5, cc, tam=9, contorno=PRETO)
                    xx += tela.largura_texto(ch, 9) + 1
            else:
                tela.texto(b, lx, py + 5, AMARELO if acesa else ACO3, tam=9, contorno=PRETO)


def vizinhos16(s):
    I, Q = QAM16[s]
    out = []
    for di, dq in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        v = QAM16_INV.get((I + di, Q + dq))
        if v is not None: out.append(v)
    return out


# ------------------------------------------------------------------ o mapa de sinal da casa
class MapaSinal:
    """Sinal em cada ponto da planta (exemplo): -40 dBm a 1 m, cai com o
    inverso do quadrado (-20 log10 d) e cada obstáculo que o raio
    roteador -> ponto cruza desconta a sua perda (dB). Calculado uma vez,
    numa grade de 2 px."""

    def __init__(self, x0, y0, w, h, m_por_px, rx, ry, obst, passo=2):
        self.x0, self.y0, self.w, self.h, self.passo = x0, y0, w, h, passo
        self.mpp = m_por_px
        gy, gx = np.mgrid[y0:y0 + h:passo, x0:x0 + w:passo].astype(np.float64)
        gx += passo / 2; gy += passo / 2
        d = np.maximum(np.hypot(gx - rx, gy - ry) * m_por_px, .5)
        p = -40.0 - 20 * np.log10(d)
        for (ax, ay, bx, by, perda) in obst:
            p -= perda * _cruza(rx, ry, gx, gy, ax, ay, bx, by)
        self.dbm = p
        self.rx, self.ry, self.obst = rx, ry, obst

    def em(self, x, y):
        i = int(clamp((y - self.y0) / self.passo, 0, self.dbm.shape[0] - 1))
        j = int(clamp((x - self.x0) / self.passo, 0, self.dbm.shape[1] - 1))
        return float(self.dbm[i, j])

    def desenhar(self, tela, revela=1e9, t=0.0, cores=(SIN0, SIN1, SIN2, SIN3, CHAMA0)):
        """Pinta o mapa em 5 faixas com xadrez entre elas; `revela` = raio (px)
        até onde o mapa já foi pintado (a onda chegando)."""
        p = self.passo
        lim = (-82, -72, -62, -49)
        v = self.dbm
        nivel = np.digitize(v, lim)                             # 0..4
        frac = np.clip((v - np.array([-92, -82, -72, -62, -49, -40])[nivel]) / 9.0, 0, 1)
        gy, gx = np.mgrid[0:v.shape[0], 0:v.shape[1]]
        xx = self.x0 + gx * p + p / 2; yy = self.y0 + gy * p + p / 2
        dentro = np.hypot(xx - self.rx, yy - self.ry) <= revela
        bayer = ((gx + gy) % 2 == 0)
        idx = np.where(bayer & (frac > .5) & (nivel < 4), nivel + 1, nivel)
        pal = np.array(cores, dtype=np.uint8)
        img = np.where(dentro, pal[idx], FUNDO).astype(np.uint8)
        big = np.repeat(np.repeat(img, p, 0), p, 1)
        y1 = min(PALCO_H, self.y0 + big.shape[0]); x1 = min(tela.w, self.x0 + big.shape[1])
        tela.buf[self.y0:y1, self.x0:x1] = big[:y1 - self.y0, :x1 - self.x0]


def _cruza(px, py, gx, gy, ax, ay, bx, by):
    """1 onde o segmento (px,py)->(gx,gy) cruza o segmento (ax,ay)-(bx,by)."""
    def lado(x1, y1, x2, y2, x3, y3): return (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    d1 = lado(ax, ay, bx, by, px, py)
    d2 = lado(ax, ay, bx, by, gx, gy)
    d3 = lado(px, py, gx, gy, ax, ay)
    d4 = lado(px, py, gx, gy, bx, by)
    return ((d1 * d2 < 0) & (d3 * d4 < 0)).astype(np.float64)


# ------------------------------------------------------------------ painel da direita
PX0 = 308


def painel_wifi(tela, t, est, x0=PX0):
    """O estado do pacote: frequência, comprimento de onda, bits por
    símbolo, sinal e o número do pacote. Campo ainda não aprendido = '?'.
    `est`: freq, onda, bits, dbm, pacote, destaque (conjunto), nota (lista
    de até 2 linhas), viagem (0..1)."""
    tela.ret(300, 0, 1, PALCO_H, TRACO)
    tela.ret(301, 0, W - 301, PALCO_H, FUNDO)
    dest = est.get('destaque', ())
    pisca = int(t * 4) % 2 == 0

    def campo(k, rot, y, valor, cor_v=BRANCO):
        on = k in dest
        tela.texto(rot, x0, y, AMARELO if on else ACO3, tam=9, contorno=PRETO)
        if on and pisca: tela.ret(x0 - 5, y + 1, 2, 5, AMARELO)
        tela.ret(x0, y + 10, 160, 1, FUNDO3)
        if valor is None:
            tela.texto('?', x0, y + 14, ACO1, tam=17, contorno=PRETO)
        else:
            tela.texto(valor, x0, y + 14, cor_v, tam=17, contorno=PRETO)

    campo('freq', 'FREQUÊNCIA', 4, est.get('freq'))
    campo('onda', 'COMPRIMENTO DE ONDA', 36, est.get('onda'))
    campo('bits', 'BITS POR SÍMBOLO', 68, est.get('bits'))
    dbm = est.get('dbm')
    on = 'dbm' in dest
    tela.texto('SINAL', x0, 100, AMARELO if on else ACO3, tam=9, contorno=PRETO)
    if on and pisca: tela.ret(x0 - 5, 101, 2, 5, AMARELO)
    tela.ret(x0, 110, 160, 1, FUNDO3)
    barras_sinal(tela, x0 + 1, 114, barras_de_dbm(dbm), cor=cor_dbm(dbm))
    if dbm is None: tela.texto('?', x0 + 32, 114, ACO1, tam=17, contorno=PRETO)
    else: tela.texto(f"{int(round(dbm))} DBM", x0 + 32, 114, cor_dbm(dbm), tam=17, contorno=PRETO)
    n = est.get('pacote')
    on = 'pacote' in dest
    tela.texto('PACOTE Nº', x0, 134, AMARELO if on else ACO3, tam=9, contorno=PRETO)
    if on and pisca: tela.ret(x0 - 5, 135, 2, 5, AMARELO)
    tela.ret(x0, 144, 160, 1, FUNDO3)
    if n is not None:
        tela.texto(str(n), x0, 148, AMARELO, tam=17, contorno=PRETO)
        pacote(tela, x0 + 30 + tela.largura_texto(str(n), 17), 155, None, t, brilho=False)
        st = est.get('estado')
        if st: tela.texto(st[0], x0 + 66 + tela.largura_texto(str(n), 17), 152, st[1], tam=9, contorno=PRETO)
    nota = est.get('nota') or ()
    for k, l in enumerate(nota[:2]):
        tela.texto(l[0] if isinstance(l, tuple) else l, x0, 170 + k * 10,
                   l[1] if isinstance(l, tuple) else ACO2, tam=9, contorno=PRETO)
    v = est.get('viagem')
    if v is not None:
        tela.texto('VIAGEM', x0, 194, ACO2, tam=9, contorno=PRETO)
        bx = x0 + 40
        tela.ret(bx, 195, 120, 6, PRETO); tela.ret(bx + 1, 196, 118, 4, FUNDO2)
        ww = int(118 * clamp(v))
        tela.ret(bx + 1, 196, ww, 4, CIANO if v < 1 else VERDE)
        if ww > 1: tela.ret(bx + ww - 1, 196, 2, 4, BRANCO)


# ------------------------------------------------------------------ casa em corte e cozinha
def chao_madeira(tela, x0, x1, y, h=6):
    tela.ret(x0, y, x1 - x0, h, MAD1)
    tela.ret(x0, y, x1 - x0, 1, MAD2)
    dither(tela, x0, y + h // 2, x1 - x0, h - h // 2, MAD1, MAD0)
    for x in range(x0 + 7, x1, 23): tela.ret(x, y + 1, 1, h - 1, MAD0)


def parede_concreto(tela, x, y, w, h):
    tela.ret(x - 1, y, w + 2, h, PRETO)
    tela.ret(x, y, w, h, CON1)
    dither(tela, x + w // 2, y, w - w // 2, h, CON1, CON0)
    tela.ret(x, y, 1, h, CON2)
    for yy in range(y + 5, y + h, 9): tela.px(x + 1 + (yy * 7) % max(1, w - 2), yy, CON0)


def planta(tela, x, yb, t=0.0, s=1.0):
    tela.ret(x - 6, yb - 9, 13, 10, PRETO); tela.ret(x - 5, yb - 8, 11, 8, LATAO)
    dither(tela, x - 5, yb - 4, 11, 4, LATAO, MAD0)
    for k in range(5):
        a = -1.2 + k * .6 + .08 * math.sin(t * 1.5 + k)
        L = (14 + (k % 2) * 6) * s
        x1, y1 = x + math.sin(a) * L, yb - 9 - math.cos(a) * L
        linha_grossa(tela, x, yb - 9, x1, y1, 4, PRETO)
        linha_grossa(tela, x, yb - 9, x1, y1, 2.4, PLN1 if k % 2 else PLN0)
        tela.disco(x1, y1, 2.4, PLN1)


def geladeira(tela, x, y, w=26, h=56):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO3)
    dither(tela, x + w * 2 // 3, y, w - w * 2 // 3, h, ACO3, ACO2)
    tela.ret(x, y, w, 1, ACO4); tela.ret(x, y + h // 3, w, 1, PRETO)
    tela.ret(x + w - 5, y + 4, 2, 8, ACO1); tela.ret(x + w - 5, y + h // 3 + 5, 2, 12, ACO1)


def micro_ondas(tela, x, y, t=0.0, ligado=True, w=110, h=64):
    """Forno de micro-ondas genérico com a porta de vidro, prato que gira e
    a tigela. Devolve o retângulo de dentro (ix, iy, iw, ih)."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO2)
    tela.ret(x, y, w, 1, ACO4)
    dither(tela, x, y + h - 10, w, 10, ACO2, ACO1)
    ix, iy, iw, ih = x + 6, y + 6, w - 36, h - 12
    tela.ret(ix - 1, iy - 1, iw + 2, ih + 2, PRETO)
    tela.ret(ix, iy, iw, ih, FUNDO2)
    if ligado:
        dither(tela, ix, iy, iw, ih, LATAO if int(t * 4) % 2 else MAD1, FUNDO2)
    # grade da porta
    for gx in range(ix, ix + iw, 4):
        for gy in range(iy, iy + ih, 4): tela.px(gx, gy, PRETO)
    # painel de botões
    px = x + w - 26
    tela.ret(px, y + 6, 20, 12, PRETO); tela.ret(px + 1, y + 7, 18, 10, TEL0)
    tela.texto(f"{int(t) % 60:02d}", px + 3, y + 9, VERDE, tam=9)
    for k in range(3):
        tela.ret(px + 2, y + 24 + k * 8, 16, 5, ACO1); tela.ret(px + 2, y + 24 + k * 8, 16, 1, ACO3)
    tela.disco(px + 10, y + 54, 4, ACO1); tela.disco(px + 10, y + 54, 1.5, ACO3)
    return ix, iy, iw, ih


def molecula_agua(tela, x, y, ang, s=1.0):
    """H2O em pixel: O vermelho no meio, dois H brancos a 104° (quase)."""
    for d in (-.91, .91):
        hx = x + math.cos(ang + d) * 3.2 * s; hy = y + math.sin(ang + d) * 3.2 * s
        tela.disco(hx, hy, 1.3 * s, PRETO)
    tela.disco(x, y, 2.2 * s, PRETO)
    tela.disco(x, y, 1.6 * s, VERMELHO)
    for d in (-.91, .91):
        hx = x + math.cos(ang + d) * 3.2 * s; hy = y + math.sin(ang + d) * 3.2 * s
        tela.disco(hx, hy, .9 * s, BRANCO)


def espectro(tela, x, y, w, h, t=0.0, mostrar=1.0, marca_wifi=False, marca_luz=False):
    """A faixa do espectro eletromagnético: rádio (longa) à esquerda,
    raios X à direita. Só a fatia fina da luz visível tem cor de arco-íris."""
    partes = [('RÁDIO', .30, OND1), ('MICRO-ONDAS', .24, OND2), ('INFRAVERMELHO', .2, BRASA),
              ('LUZ', .045, None), ('UV', .09, ROXO), ('RAIOS X', .125, ACO1)]
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    xx = x
    arco = [VERMELHO, LARANJA, AMARELO, VERDE, CIANO, AGU1, ROXO]
    for k, (nome, frac, cor) in enumerate(partes):
        ww = int(round(w * frac)) if k < len(partes) - 1 else x + w - xx
        if (xx - x) / w > mostrar: break
        if cor is None:
            for i in range(ww):
                tela.ret(xx + i, y, 1, h, arco[min(6, i * 7 // max(1, ww))])
        else:
            tela.ret(xx, y, ww, h, cor)
            dither(tela, xx, y + h // 2, ww, h - h // 2, cor, PRETO)
            tela.ret(xx, y, ww, 1, OND3 if cor in (OND1, OND2) else ACO3)
        tela.ret(xx + ww - 1, y, 1, h, PRETO)
        xx += ww
    # onda desenhada por cima: comprimento cai da esquerda para a direita
    xs = np.arange(x, x + int(w * min(1, mostrar)))
    if len(xs):
        u = (xs - x) / w
        fase = np.cumsum(2 * np.pi / (26 * (1 - u) ** 2 + 1.6))
        ys = (y + h / 2 - 3 * np.sin(fase - t * 3)).astype(int)
        for i, xv in enumerate(xs): tela.px(xv, ys[i], BRANCO)
    return x + int(w * (.30 + .24 * .2)), x + int(w * (.30 + .24 + .2 + .0225))   # ponto do Wi-Fi, centro da luz
