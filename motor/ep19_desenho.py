#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep19 — o desenho: o contêiner (de lado, de frente e em
perspectiva), o código ISO 6346, caminhão, portão com câmeras, RTG do pátio,
guindaste de cais (STS), o navio em corte e de lado, mar, céu, cais e o painel
da jornada. Tudo genérico: navio, guindastes e caminhão sem nome nem logotipo;
o código do dono (MPX) é inventado para o vídeo.

A paleta do episódio é a `oficina` + cores próprias (céu, mar, cinco tons do
laranja do contêiner, contêineres azuis, verdes, vermelhos e cinza, asfalto,
concreto, casco). Ela é registrada como 'ep19' e o `longo` passa a usá-la
neste processo (como o ep11 faz com a dele).

Vista "de frente" (pela ponta) = olhando ao longo do cais: o contêiner aparece
pela porta, o navio em corte (fileiras x camadas) e o guindaste com a lança
por cima do navio. É a vista dos desenhos de engenharia de porto.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
import idioma as I
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, BAYER8,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)

# ================================================================ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#0d1430', '#1a2652', '#33447a', '#6b5583', '#d98a6c',   # 32..36 céu (noite -> horizonte)
          '#061a33', '#0c3560', '#1d5b93', '#5aa3d6', '#cfeeff',   # 37..41 mar (fundo -> espuma)
          '#4a1d0c', '#9a3e16', '#d9612a', '#ff9447', '#ffc48a',   # 42..46 laranja do contêiner
          '#11284a', '#245290', '#5288c6',                         # 47..49 contêiner azul
          '#163a28', '#2c7446', '#5aaa74',                         # 50..52 contêiner verde
          '#45131a', '#93282f', '#cf5258',                         # 53..55 contêiner vermelho
          '#3a3e47', '#6a707d', '#a3aab7',                         # 56..58 contêiner cinza
          '#17191f', '#262932', '#3a3e4a',                         # 59..61 asfalto
          '#565b66', '#8a8f9a', '#b8bcc4',                         # 62..64 concreto
          '#12161f', '#232a38',                                    # 65..66 casco
          '#3d74b4', '#8cc2ea', '#fff4c8']                         # 67..69 céu de dia e sol
PX.PALETAS['ep19'] = _BASE + _EXTRA
LG.PAL = 'ep19'
CEU0, CEU1, CEU2, CEU3, CEU4 = 32, 33, 34, 35, 36
MAR0, MAR1, MAR2, MAR3, ESPUMA = 37, 38, 39, 40, 41
LAR0, LAR1, LAR2, LAR3, LAR4 = 42, 43, 44, 45, 46
AZC0, AZC1, AZC2 = 47, 48, 49
VDC0, VDC1, VDC2 = 50, 51, 52
VMC0, VMC1, VMC2 = 53, 54, 55
CIN0, CIN1, CIN2 = 56, 57, 58
ASF0, ASF1, ASF2 = 59, 60, 61
CON0, CON1, CON2 = 62, 63, 64
CAS0, CAS1 = 65, 66
CEUD0, CEUD1, SOL = 67, 68, 69

# tons de cada contêiner: (mais escuro, escuro, meio, claro, brilho)
P_LAR = (LAR0, LAR1, LAR2, LAR3, LAR4)            # o NOSSO (laranja)
P_AZ = (PRETO, AZC0, AZC1, AZC2, AZC2)
P_VD = (PRETO, VDC0, VDC1, VDC2, VDC2)
P_VM = (PRETO, VMC0, VMC1, VMC2, VMC2)
P_CI = (PRETO, CIN0, CIN1, CIN2, CIN2)
P_BR = (PRETO, ACO2, ACO3, ACO4, BRANCO)
OUTRAS = [P_AZ, P_VD, P_VM, P_CI, P_BR, P_AZ, P_CI, P_VD]

# ================================================================ a jornada
ETAPAS = [('FÁBRICA', LAR3), ('PORTÃO', CIANO), ('PÁTIO', AMARELO), ('GUINDASTE', ACO4),
          ('NO NAVIO', VERDE), ('AMARRAÇÃO', ROSA), ('VIAGEM', MAR3), ('CHEGADA', CHAMA1)]

# ---------------------------------------------------------------- o código ISO 6346 (inventado)
DONO, CAT, SERIE = 'MPX', 'U', '190426'


def valor_letra(c):
    """Letras: A=10 e sobe, pulando os múltiplos de 11 (11, 22, 33)."""
    v = 10
    for x in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if v % 11 == 0: v += 1
        if x == c: return v
        v += 1
    raise ValueError(c)


def conta_digito(s=DONO + CAT + SERIE):
    """(valores, pesos, produtos, soma, resto) da conta do dígito verificador."""
    vals = [valor_letra(c) if c.isalpha() else int(c) for c in s]
    pesos = [2 ** i for i in range(len(s))]
    prods = [int(v) * int(p) for v, p in zip(vals, pesos)]
    soma = sum(prods)
    return vals, pesos, prods, soma, soma % 11


DIGITO = conta_digito()[4] % 10
CODIGO = f"{DONO}{CAT} {SERIE} {DIGITO}"          # MPXU 190426 5


def checar_codigo():
    assert conta_digito('CSQU305438')[4] == 3      # exemplo da Wikipedia (ISO 6346)
    v, p, pr, s, r = conta_digito()
    assert s == 4878 and r == 5 and DIGITO == 5, (s, r)
    return True


def lerp(a, b, u): return a + (b - a) * u
def um(u): return min(1.0, max(0.0, u))


# ================================================================ miúdos
def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com bolinha na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.disco(x1, y1, 1.6, PRETO)
    tela.disco(x1, y1, 1.0, cor)


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
    y0, y1 = max(0, int(cy - r)), min(PALCO_H, int(cy + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & ((xx + yy + fase) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def luz(tela, cx, cy, r, nucleo=BRANCO, cor=AMARELO, halo_cor=None):
    halo(tela, cx, cy, r * 2.2, halo_cor if halo_cor is not None else cor)
    tela.disco(cx, cy, r, cor)
    tela.disco(cx, cy, max(.6, r * .5), nucleo)


def mira(tela, x, y, t, r=10, ry=None):
    """Cantoneiras piscando em volta do protagonista."""
    ry = r if ry is None else ry
    c = BRANCO if int(t * 4) % 2 else AMARELO
    for sx in (-1, 1):
        for sy in (-1, 1):
            xx, yy = int(x + sx * r), int(y + sy * ry)
            tela.ret(xx - (3 if sx > 0 else 0), yy, 4, 1, c)
            tela.ret(xx, yy - (3 if sy > 0 else 0), 1, 4, c)


def caixa(tela, x, y, w, h, cor, luz_=None, sombra=None):
    """Bloco com contorno preto, luz em cima/esquerda e sombra embaixo/direita."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, cor)
    if luz_ is not None:
        tela.ret(x, y, w, 1, luz_); tela.ret(x, y, 1, h, luz_)
    if sombra is not None:
        tela.ret(x, y + h - 1, w, 1, sombra); tela.ret(x + w - 1, y, 1, h, sombra)


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


def check(tela, x, y, cor=VERDE):
    """Sinal de certo em pixels (a fonte não tem ✓)."""
    for dx, dy in ((0, 3), (1, 4), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1), (7, 0)):
        tela.ret(x + dx, y + dy, 1, 2, cor)


def xis(tela, x, y, cor=VERMELHO, s=7):
    for k in range(s):
        tela.ret(x + k, y + k, 2, 1, cor); tela.ret(x + s - 1 - k, y + k, 2, 1, cor)


def lampada_aviso(tela, x, y, t, cor=CHAMA1, fase=0.0):
    """Luz de aviso piscando (guindaste, caminhão)."""
    if math.sin(t * 6 + fase) > 0:
        halo(tela, x, y, 4, cor)
        tela.disco(x, y, 1.3, BRANCO)
    else:
        tela.px(x, y, BRASA)


# ================================================================ céu, mar, chão
def ceu(tela, y1=PALCO_H, t=0.0, estrelas=True, cores=(CEU0, CEU0, CEU1, CEU2, CEU3), x0=0, x1=W):
    grad_v(tela, x0, 0, x1 - x0, y1, list(cores))
    if estrelas:
        for k in range(30):
            x = x0 + (k * 97 + 13) % max(1, x1 - x0)
            y = (k * 53 + 7) % max(1, int(y1 * .45))
            if math.sin(t * 1.7 + k * 2.3) > -.2: tela.px(x, y, BRANCO if k % 4 == 0 else ACO3)


def nuvem(tela, cx, cy, w, cor=CEU2, luz_=CEU3):
    bolas = [(-.38, .10, .22), (-.14, -.08, .28), (.14, -.12, .26), (.36, .04, .2), (0, .1, .26)]
    for dx, dy, r in bolas:
        tela.disco(cx + dx * w, cy + dy * w, r * w, cor)
    for dx, dy, r in bolas:
        tela.disco(cx + dx * w - r * w * .2, cy + dy * w - r * w * .25, r * w * .6, luz_)
    tela.ret(int(cx - w * .5), int(cy + w * .18), int(w), 2, cor)


def mar(tela, x0, x1, ytop, ybot, t, vel=1.0, onda=1.0, scroll=0.0):
    """Mar com degradê, superfície que ondula e reflexos correndo."""
    x0, x1 = max(0, int(x0)), min(W, int(x1))
    if x1 <= x0: return
    grad_v(tela, x0, ytop, x1 - x0, ybot - ytop, [MAR2, MAR1, MAR1, MAR0, MAR0])
    for x in range(x0, x1):
        xs = x + scroll
        d = int(round(onda * (math.sin(xs * .19 - t * 2.4 * vel) + .6 * math.sin(xs * .051 + t * 1.1))))
        tela.px(x, ytop - max(0, d), MAR3)
        if d > 0: tela.px(x, ytop, MAR2)
        if (int(xs) * 7 + int(t * 5)) % 29 == 0: tela.px(x, ytop - max(0, d), ESPUMA)
    for k in range(max(1, (x1 - x0) // 18)):
        xx = x0 + int((k * 41 - scroll * (1 + k % 3) * .5 + t * 9 * (1 + k % 2)) % max(1, x1 - x0 - 8))
        yy = ytop + 4 + (k * 11) % max(1, min(26, ybot - ytop - 6))
        if yy < ybot - 1: tela.ret(xx, yy, 3 + k % 4, 1, MAR2 if k % 3 else MAR3)


def cais(tela, x0, x1, y, chao=PALCO_H, borda=True, trilhos=()):
    """Cais de concreto: laje com juntas, borda com defensas, trilhos do guindaste."""
    grad_v(tela, x0, y, x1 - x0, chao - y, [CON1, CON0, CON0, ASF2])
    tela.ret(x0, y, x1 - x0, 1, CON2)
    for x in range(x0 + 12, x1, 30): tela.ret(x, y + 2, 1, chao - y - 2, CON0)
    for tx in trilhos:
        tela.ret(tx - 3, y - 1, 7, 2, ACO1); tela.ret(tx - 2, y - 1, 5, 1, ACO3)
    if borda:
        tela.ret(x1 - 2, y, 2, chao - y, CON0)
        for yy in range(y + 4, chao - 4, 14):
            tela.ret(x1, yy, 3, 7, PRETO); tela.ret(x1, yy + 1, 2, 5, ASF2)   # defensa de borracha
        tela.ret(x1 - 8, y - 4, 5, 4, PRETO); tela.ret(x1 - 7, y - 3, 3, 3, ACO1)  # cabeço de amarração


def asfalto(tela, y, t=0.0, scroll=0.0, faixa=True, chao=PALCO_H):
    grad_v(tela, 0, y, W, chao - y, [ASF2, ASF1, ASF1, ASF0])
    tela.ret(0, y, W, 1, CON1)
    if faixa:
        yy = y + (chao - y) // 2
        for k in range(-1, W // 30 + 2):
            x = int(k * 30 - scroll % 30)
            tela.ret(x, yy, 14, 2, CHAMA0)


# ================================================================ o contêiner
def _castanha(tela, x, y, s=1):
    """Peça de canto (corner casting) com o furo oval."""
    if s <= 1:
        tela.px(x, y, ACO0)
        return
    tela.ret(x, y, 3 * s, 3 * s - 1, PRETO)
    tela.ret(x + 1, y + 1, 3 * s - 2, 3 * s - 3, CIN1)
    tela.ret(x + s, y + s, s, max(1, s - 1), PRETO)


def cont_lado(tela, x, y, w, h, pal=P_LAR, t=0.0, codigo=False, raiox=None, portas=0.0, castanhas=True):
    """Contêiner visto de lado (comprido). x, y = canto de cima à esquerda.
    `raiox` = função(tela, x, y, w, h) que desenha o interior (corte).
    `portas` 0..1 = portas abertas na ponta da direita."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    passo = 6 if w >= 120 else (4 if w >= 40 else 3)
    if raiox:
        dither(tela, x, y, w, h, FUNDO2, FUNDO)
        raiox(tela, x, y, w, h)
        tela.ret(x, y, w, 2, pal[2]); tela.ret(x, y + h - 2, w, 2, pal[1])
        tela.ret(x, y, 2, h, pal[2]); tela.ret(x + w - 2, y, 2, h, pal[1])
        tela.ret(x, y, w, 1, pal[3])
    else:
        # chapa corrugada: nervuras verticais luz / meio / sombra
        for k in range(0, w, passo):
            a = passo // 3 or 1
            tela.ret(x + k, y, a, h, pal[3])
            tela.ret(x + k + a, y, a, h, pal[2])
            tela.ret(x + k + 2 * a, y, passo - 2 * a, h, pal[1])
        # sombra embaixo (degradê pontilhado)
        dither(tela, x, y + h - max(2, h // 4), w, max(2, h // 4), pal[1], pal[0] if pal[0] != PRETO else pal[1])
        # trilhos de cima e de baixo, colunas de canto
        tr_ = min(3, max(1, h // 12))
        tela.ret(x, y, w, tr_, pal[4]); tela.ret(x, y + tr_, w, 1, pal[1])
        tela.ret(x, y + h - max(1, h // 10), w, max(1, h // 10), pal[0] if pal[0] != PRETO else pal[1])
        cw = max(1, w // 40)
        tela.ret(x, y, cw, h, pal[1]); tela.ret(x + w - cw, y, cw, h, pal[1])
        if cw > 1: tela.ret(x + 1, y, 1, h, pal[3])
    if portas > 0:
        # portas abrindo para fora (vistas de lado: chapas finas saindo da ponta)
        L = int(h * .55 * portas)
        tela.ret(x + w, y + 1, L + 1, 2, PRETO); tela.ret(x + w, y + 1, L, 1, pal[3])
        tela.ret(x + w, y + h - 3, L + 1, 2, PRETO); tela.ret(x + w, y + h - 3, L, 1, pal[2])
        tela.ret(x + w + L - 1, y + 1, 2, h - 2, pal[1])
    if castanhas:
        s = 2 if h >= 40 else 1
        k = 3 * s if s > 1 else 1
        for cx_, cy_ in ((x, y), (x + w - k, y), (x, y + h - k), (x + w - k, y + h - k)):
            _castanha(tela, cx_, cy_, s)
    if codigo and h >= 30:
        tam = 17 if h >= 70 else 9
        cx_ = x + w - 8 - tela.largura_texto(CODIGO, tam)
        tela.texto(CODIGO, cx_, y + max(4, h // 9), BRANCO, tam=tam, contorno=pal[0] if pal[0] != PRETO else None)
        if h >= 70:
            tela.texto('22G1', cx_, y + max(4, h // 9) + 22, BRANCO, tam=9)
    elif codigo and h >= 10:
        # marquinhas brancas no lugar do código (pequeno demais para ler)
        tela.ret(x + w - 12, y + 2, 4, 1, BRANCO); tela.ret(x + w - 7, y + 2, 5, 1, BRANCO)


def cont_frente(tela, x, y, w=10, h=11, pal=P_LAR, codigo=False, contorno=True):
    """Contêiner visto pela ponta (as portas). Escala livre."""
    x, y = int(x), int(y)
    if contorno: tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, pal[2])
    tela.ret(x, y, w, 1, pal[4] if w >= 16 else pal[3])
    tela.ret(x, y + h - 1, w, 1, pal[1])
    tela.ret(x, y, 1, h, pal[3]); tela.ret(x + w - 1, y, 1, h, pal[1])
    if w >= 16:
        # duas portas, 4 barras de trava, dobradiças
        tela.ret(x + w // 2, y + 1, 1, h - 2, pal[0] if pal[0] != PRETO else pal[1])
        for bx in (w * .2, w * .38, w * .62, w * .8):
            tela.ret(x + int(bx), y + 2, 1, h - 4, pal[1])
            tela.px(x + int(bx), y + h // 2, ACO3)
        for hy in (h * .15, h * .5, h * .85):
            tela.ret(x + 1, y + int(hy), 2, 2, pal[0] if pal[0] != PRETO else pal[1])
            tela.ret(x + w - 3, y + int(hy), 2, 2, pal[0] if pal[0] != PRETO else pal[1])
        s = 2 if w >= 30 else 1
        if s > 1:
            for cx_, cy_ in ((x, y), (x + w - 6, y), (x, y + h - 6), (x + w - 6, y + h - 6)):
                _castanha(tela, cx_, cy_, s)
        else:
            for cx_, cy_ in ((x, y), (x + w - 2, y), (x, y + h - 2), (x + w - 2, y + h - 2)):
                tela.ret(cx_, cy_, 2, 2, CIN1)
        if codigo and w >= 40:
            tela.texto(CODIGO[:4], x + w - 4 - tela.largura_texto(CODIGO[:4], 9), y + 4, BRANCO, tam=9)
            tela.texto(CODIGO[5:], x + w - 4 - tela.largura_texto(CODIGO[5:], 9), y + 13, BRANCO, tam=9)
    else:
        tela.ret(x + w // 2, y + 1, 1, h - 2, pal[1])
        tela.ret(x + 2, y + 2, 1, h - 4, pal[1]); tela.ret(x + w - 3, y + 2, 1, h - 4, pal[1])
        if codigo: tela.ret(x + w - 4, y + 2, 2, 1, BRANCO)


def cont_iso(tela, x, y, w, h, d, pal=P_LAR, t=0.0, codigo=True, acesas=(), castanhas=True):
    """Contêiner em perspectiva (lado comprido + ponta das portas + teto).
    x, y = canto de cima à esquerda do lado comprido; d = profundidade (px).
    `acesas` = índices (0..7) das peças de canto acesas. Devolve as 8 posições."""
    dx, dy = d, -int(d * .6)
    xr = x + w
    # teto
    poligono(tela, [(x - 1, y), (x + dx - 1, y + dy - 1), (xr + dx + 1, y + dy - 1), (xr + 1, y)], PRETO)
    poligono(tela, [(x, y), (x + dx, y + dy), (xr + dx, y + dy), (xr, y)], pal[3])
    for k in range(0, w, 8):
        tela.linha(x + k, y - 1, x + k + dx, y + dy, pal[2])
    # ponta (portas), parede da direita em paralelogramo
    poligono(tela, [(xr, y - 1), (xr + dx + 1, y + dy - 1), (xr + dx + 1, y + dy + h + 1), (xr, y + h + 1)], PRETO)
    poligono(tela, [(xr, y), (xr + dx, y + dy), (xr + dx, y + dy + h), (xr, y + h)], pal[1])
    for k, f in enumerate((.2, .4, .6, .8)):
        bx = xr + dx * f
        tela.linha(bx, y + dy * f + 3, bx, y + dy * f + h - 3, pal[0] if pal[0] != PRETO else pal[2])
        tela.px(bx + 1, y + dy * f + h // 2, ACO3)
    tela.linha(xr + dx * .5 + 1, y + dy * .5 + 2, xr + dx * .5 + 1, y + dy * .5 + h - 2, pal[2])
    # lado comprido
    cont_lado(tela, x, y, w, h, pal, t, codigo=codigo, castanhas=False)
    pos = [(x, y), (xr, y), (x, y + h), (xr, y + h),
           (x + dx, y + dy), (xr + dx, y + dy), (x + dx, y + dy + h), (xr + dx, y + dy + h)]
    if castanhas:
        for i, (px_, py_) in enumerate(pos):
            if i == 6: continue                       # escondida atrás
            s = 2 if h >= 40 else 1
            cx_ = int(px_) - (3 * s if px_ > x + w // 2 else 0)
            cy_ = int(py_) - (3 * s - 1 if py_ > y + dy + 2 and i in (2, 3, 7) else 0)
            if i in (4, 5): cy_ = int(py_)
            if i in (4,): cx_ = int(px_)
            _castanha(tela, cx_, cy_, s)
            if i in acesas:
                halo(tela, cx_ + 3 * s // 2, cy_ + 3 * s // 2, 6, AMARELO)
                _castanha(tela, cx_, cy_, s)
    return pos


# ================================================================ caminhão (de lado)
def roda(tela, x, y, r, ang, cor=ASF0):
    tela.disco(x, y, r + 1, PRETO)
    tela.disco(x, y, r, cor)
    tela.disco(x, y, r * .5, ACO2)
    for k in range(3):
        a = ang + k * 2.094
        tela.px(x + math.cos(a) * r * .35, y + math.sin(a) * r * .35, ACO0)
    tela.px(x - r * .3, y - r * .3, ACO4)


def caminhao(tela, x, yb, t=0.0, dist=0.0, cont=True, pal=P_LAR, cw=61, ch=26, cab_cor=(CIN0, CIN1, CIN2),
             codigo=True, raiox=None, portas=0.0, luzes=True):
    """Cavalo + carreta com um contêiner de 20 pés. x = traseira da carreta,
    yb = chão. A cabine fica à direita (vai para a direita). `dist` = metros
    andados (gira as rodas). Devolve (x, y, w, h) do contêiner."""
    x, yb = int(x), int(yb)
    ang = dist / 3.0
    # carreta
    cx0, cx1 = x, x + cw + 6
    tela.ret(cx0 - 1, yb - 12, cx1 - cx0 + 2, 5, PRETO)
    tela.ret(cx0, yb - 11, cx1 - cx0, 3, ACO1); tela.ret(cx0, yb - 11, cx1 - cx0, 1, ACO2)
    for k in range(2):
        roda(tela, x + 8 + k * 9, yb - 4, 4, ang)
    tela.ret(x + 3, yb - 9, 16, 2, PRETO)                        # para-lama
    tela.ret(x - 1, yb - 10, 2, 4, VERMELHO if int(t * 2) % 2 else VMC0)  # lanterna
    # cavalo (cabine)
    k0 = cx1 - 4
    tela.ret(k0 - 1, yb - 10, 30, 4, PRETO); tela.ret(k0, yb - 9, 28, 2, ACO1)
    roda(tela, k0 + 4, yb - 4, 4, ang); roda(tela, k0 + 22, yb - 4, 4, ang)
    c0, c1, c2 = cab_cor
    pts = [(k0 + 10, yb - 8), (k0 + 10, yb - 33), (k0 + 22, yb - 33), (k0 + 29, yb - 22), (k0 + 30, yb - 8)]
    poligono(tela, [(px_ - (1 if px_ <= k0 + 10 else -1), py_ + (-1 if py_ < yb - 20 else 1)) for px_, py_ in pts], PRETO)
    poligono(tela, pts, c1)
    tela.ret(k0 + 11, yb - 32, 10, 1, c2)
    poligono(tela, [(k0 + 21, yb - 30), (k0 + 26, yb - 22), (k0 + 21, yb - 22)], MAR3)   # para-brisa
    tela.ret(k0 + 13, yb - 29, 6, 6, MAR2); tela.ret(k0 + 13, yb - 29, 6, 1, MAR3)       # janela
    tela.ret(k0 + 11, yb - 20, 18, 1, c0)
    tela.ret(k0 + 18, yb - 18, 1, 8, c0)                                                   # porta
    tela.ret(k0 + 8, yb - 36, 2, 26, PRETO); tela.ret(k0 + 8, yb - 35, 1, 24, ACO3)         # escapamento
    if luzes:
        tela.ret(k0 + 28, yb - 13, 2, 2, CHAMA0)
        halo(tela, k0 + 31, yb - 12, 3, CHAMA0)
    r = (x + 2, yb - 12 - ch, cw, ch)
    if cont:
        # pinos de trava (twistlocks) da carreta
        tela.ret(x + 2, yb - 13, 2, 1, ACO3); tela.ret(x + cw, yb - 13, 2, 1, ACO3)
        cont_lado(tela, r[0], r[1], cw, ch, pal, t, codigo=codigo, raiox=raiox, portas=portas)
    return r


def caminhao_frente(tela, cx, yb, t=0.0, cont=True, pal=P_LAR, w=10, h=11, codigo=True):
    """Caminhão visto pela traseira (vista do cais): chassi, rodas e o contêiner."""
    cx, yb = int(cx), int(yb)
    x0 = cx - w // 2 - 1
    tela.ret(x0 - 1, yb - 7, w + 4, 3, PRETO); tela.ret(x0, yb - 6, w + 2, 1, ACO2)
    for dx in (0, w - 1):
        tela.ret(x0 + dx, yb - 4, 3, 4, PRETO); tela.ret(x0 + dx + 1, yb - 4, 1, 3, ASF2)
    tela.px(x0, yb - 6, VERMELHO); tela.px(x0 + w + 1, yb - 6, VERMELHO)
    if cont:
        cont_frente(tela, cx - w // 2, yb - 7 - h, w, h, pal, codigo=codigo)
    return cx - w // 2, yb - 7 - h


# ================================================================ spreader e cabos
def spreader(tela, cx, y, w=10, travado=0.0, t=0.0, cor=AMARELO, escala=1):
    """Spreader visto pela ponta: viga com 2 pinos (os outros 2 ficam atrás).
    `travado` 0..1: o pino gira (de oval de pé para deitado) e a luz fica verde."""
    s = escala
    x0 = int(cx - w // 2 - 2 * s)
    ww = w + 4 * s
    tela.ret(x0 - 1, int(y) - 1, ww + 2, 3 * s + 2, PRETO)
    tela.ret(x0, int(y), ww, 3 * s, cor); tela.ret(x0, int(y), ww, 1, CHAMA0 if cor == AMARELO else ACO4)
    tela.ret(x0 + ww // 2 - 2 * s, int(y) - 2 * s, 4 * s, 2 * s, LATAO)
    for px_ in (x0 + 2 * s, x0 + ww - 3 * s):
        tela.ret(px_, int(y) + 3 * s, s, 2 * s, ACO3 if travado < .5 else ACO4)
    # luzes de trava: vermelho -> verde
    for px_ in (x0 + 1, x0 + ww - 2):
        tela.px(px_, int(y) + 1, VERDE if travado >= 1 else (VERMELHO if travado <= 0 else CHAMA1))


def cabos(tela, x0, y0, x1, y1, cor=ACO2, n=2, abre=2):
    for k in range(n):
        off = (k - (n - 1) / 2) * abre
        tela.linha(x0 + off * .5, y0, x1 + off, y1, cor)


# ================================================================ guindaste de cais (STS), vista do cais
STS = dict(xl=40, xs=128, yq=150, yb=34, x_ini=6, x_fim=290, ytopo=6)


def sts(tela, t, trole_x, gancho_y, travado=0.0, carga=None, cab=True, luzes=True, g=STS, carga_pal=P_LAR,
        carga_codigo=True):
    """Guindaste pórtico de cais (vista ao longo do cais). Pernas sobre trilhos,
    lança horizontal por cima do navio, carrinho (trole) com cabine pendurada,
    cabos até o spreader. `carga` = True leva um contêiner preso ao spreader."""
    xl, xs, yq, yb = g['xl'], g['xs'], g['yq'], g['yb']
    xa, xb = g['x_ini'], g['x_fim']
    ytopo = g['ytopo']
    C0, C1, C2 = ACO1, ACO3, ACO4                   # aço claro (pintura clara)
    # estais (cabos da lança) do topo do "A" até a ponta e a traseira
    apex = ((xl + xs) // 2 + 8, ytopo)
    tela.linha(apex[0], apex[1], xb - 4, yb, ACO2)
    tela.linha(apex[0], apex[1] + 3, xb - 40, yb, ACO1)
    tela.linha(apex[0], apex[1], xa + 2, yb, ACO2)
    # torre em A sobre o pórtico
    for xx in (xl + 6, xs - 2):
        linha_grossa(tela, xx, yb + 2, apex[0], apex[1] + 2, 4, PRETO)
        linha_grossa(tela, xx, yb + 2, apex[0], apex[1] + 2, 2, C1)
    tela.ret(apex[0] - 3, apex[1] - 2, 7, 5, PRETO); tela.ret(apex[0] - 2, apex[1] - 1, 5, 3, VERMELHO)
    if luzes: lampada_aviso(tela, apex[0], apex[1] - 3, t, VERMELHO)
    # pernas (lado terra e lado mar) com travessas
    for xx in (xl, xs):
        tela.ret(xx - 3, yb + 4, 8, yq - yb - 8, PRETO)
        tela.ret(xx - 2, yb + 5, 6, yq - yb - 10, C1)
        tela.ret(xx - 2, yb + 5, 2, yq - yb - 10, C2)
        tela.ret(xx + 3, yb + 5, 1, yq - yb - 10, C0)
        # truque (rodas sobre o trilho)
        tela.ret(xx - 6, yq - 6, 14, 5, PRETO); tela.ret(xx - 5, yq - 5, 12, 3, ACO1)
        for k in range(3): tela.disco(xx - 3 + k * 4, yq - 2, 1.6, ASF0)
    # viga do pórtico (embaixo da lança) e diagonais
    tela.ret(xl - 3, yb + 22, xs - xl + 8, 6, PRETO); tela.ret(xl - 2, yb + 23, xs - xl + 6, 4, C1)
    tela.ret(xl - 2, yb + 23, xs - xl + 6, 1, C2)
    tela.ret(xl - 3, yq - 46, xs - xl + 8, 4, PRETO); tela.ret(xl - 2, yq - 45, xs - xl + 6, 2, C0)
    # faixas de aviso nas pernas
    for xx in (xl, xs):
        for k in range(4):
            tela.ret(xx - 2, yq - 20 + k * 3, 6, 1, VERMELHO if k % 2 == 0 else BRANCO)
    # lança (treliça)
    tela.ret(xa - 1, yb - 1, xb - xa + 2, 8, PRETO)
    tela.ret(xa, yb, xb - xa, 6, C1)
    tela.ret(xa, yb, xb - xa, 1, C2)
    tela.ret(xa, yb + 5, xb - xa, 1, C0)
    for x in range(xa + 2, xb - 2, 6):
        tela.linha(x, yb + 1, x + 3, yb + 4, C0)
    # casa de máquinas atrás
    tela.ret(xa + 2, yb - 10, 26, 10, PRETO); tela.ret(xa + 3, yb - 9, 24, 8, CERAMICA)
    tela.ret(xa + 3, yb - 9, 24, 1, BRANCO)
    for k in range(4): tela.ret(xa + 6 + k * 5, yb - 6, 3, 2, ACO1)
    if luzes:
        lampada_aviso(tela, xb - 3, yb - 2, t, VERMELHO, 1.3)
        for k in range(3):                                         # holofotes embaixo da lança
            hx = 150 + k * 50
            if hx < xb - 10:
                tela.ret(hx, yb + 6, 3, 2, CHAMA0)
    # trole (carrinho) e cabine pendurada
    tx = int(trole_x)
    tela.ret(tx - 8, yb + 5, 17, 5, PRETO); tela.ret(tx - 7, yb + 6, 15, 3, ACO2)
    tela.disco(tx - 5, yb + 5, 1.5, ASF0); tela.disco(tx + 5, yb + 5, 1.5, ASF0)
    if cab:
        cx0 = tx - 18
        tela.ret(cx0, yb + 9, 1, 3, ACO1)
        tela.ret(cx0 - 5, yb + 11, 11, 9, PRETO); tela.ret(cx0 - 4, yb + 12, 9, 7, CERAMICA)
        tela.ret(cx0 - 3, yb + 13, 7, 3, MAR3 if not luzes else CHAMA0)
        tela.ret(cx0 - 3, yb + 13, 7, 1, BRANCO)
        tela.ret(cx0 + 1, yb + 9, 17, 1, ACO1)
    gy = int(gancho_y)
    cabos(tela, tx, yb + 10, tx, gy - 2, ACO3, n=2, abre=6)
    spreader(tela, tx, gy, 10, travado, t)
    if carga:
        cont_frente(tela, tx - 5, gy + 3 + 2, 10, 11, carga_pal, codigo=carga_codigo)
        return (tx - 5, gy + 5)
    return None


# ================================================================ RTG do pátio (vista pela ponta)
def rtg(tela, x0, x1, yb, ytopo, trole_x, gancho_y, travado=0.0, t=0.0, carga=None, s=2, pal=P_LAR,
        codigo=True):
    """Pórtico sobre pneus que monta as pilhas do pátio. Duas pernas (com pneus)
    que passam por cima das fileiras e da faixa do caminhão; viga em cima com o
    trole e os cabos."""
    Y0, Y1, Y2 = LATAO, AMARELO, CHAMA0
    for xx in (x0, x1):
        # perna dupla com travessa e pneus
        tela.ret(xx - 4, ytopo, 9, yb - ytopo - 8, PRETO)
        tela.ret(xx - 3, ytopo + 1, 7, yb - ytopo - 10, Y1)
        tela.ret(xx - 3, ytopo + 1, 2, yb - ytopo - 10, Y2)
        tela.ret(xx + 3, ytopo + 1, 1, yb - ytopo - 10, Y0)
        tela.ret(xx - 9, yb - 12, 19, 5, PRETO); tela.ret(xx - 8, yb - 11, 17, 3, Y0)
        for dx in (-5, 5):
            tela.disco(xx + dx, yb - 5, 5, PRETO); tela.disco(xx + dx, yb - 5, 4, ASF1)
            tela.disco(xx + dx, yb - 5, 1.8, ACO2)
    # viga superior
    tela.ret(x0 - 6, ytopo - 8, x1 - x0 + 13, 10, PRETO)
    tela.ret(x0 - 5, ytopo - 7, x1 - x0 + 11, 8, Y1)
    tela.ret(x0 - 5, ytopo - 7, x1 - x0 + 11, 1, Y2)
    tela.ret(x0 - 5, ytopo, x1 - x0 + 11, 1, Y0)
    for x in range(x0, x1, 8): tela.linha(x, ytopo - 6, x + 4, ytopo - 1, Y0)
    # cabine do operador
    tela.ret(x1 - 22, ytopo + 2, 14, 12, PRETO); tela.ret(x1 - 21, ytopo + 3, 12, 10, CERAMICA)
    tela.ret(x1 - 20, ytopo + 5, 10, 4, MAR3); tela.ret(x1 - 20, ytopo + 5, 10, 1, BRANCO)
    lampada_aviso(tela, x0 - 2, ytopo - 10, t, CHAMA1)
    lampada_aviso(tela, x1 + 2, ytopo - 10, t, CHAMA1, 2.0)
    # trole
    tx = int(trole_x)
    tela.ret(tx - 10, ytopo - 3, 21, 7, PRETO); tela.ret(tx - 9, ytopo - 2, 19, 5, ACO2)
    tela.ret(tx - 9, ytopo - 2, 19, 1, ACO4)
    gy = int(gancho_y)
    cabos(tela, tx, ytopo + 4, tx, gy - 2, ACO3, n=2, abre=12)
    w = 10 * s
    spreader(tela, tx, gy, w, travado, t, escala=s)
    if carga:
        cont_frente(tela, tx - w // 2, gy + 3 * s + 2, w, 11 * s, pal, codigo=codigo)
        return (tx - w // 2, gy + 3 * s + 2)
    return None


# ================================================================ navio em corte (pela ponta)
class Corte:
    """Navio porta-contêineres em corte transversal: casco, porão com guias de
    célula, tampa da escotilha e as pilhas do convés. Fileiras numeradas do
    centro para fora (pares à esquerda/bombordo, ímpares à direita/boreste);
    camadas de baixo para cima."""

    def __init__(self, x0=176, rows=10, deck_y=140, tiers_h=4, tiers_d=4, s=1, cw=10, ch=11):
        self.s = s
        self.cw, self.ch = cw * s, ch * s
        self.x0, self.rows = x0, rows
        self.deck_y = deck_y
        self.th, self.td = tiers_h, tiers_d
        self.hf = deck_y + 4 * s + tiers_h * self.ch           # piso do porão
        self.x1 = x0 + rows * self.cw
        self.slots = {}                                         # (row, tier) -> paleta

    def numero_fileira(self, r):
        """r = 0 (esquerda) .. rows-1; devolve o número da fileira (02, 01...)."""
        m = self.rows // 2
        return 2 * (m - r) if r < m else 2 * (r - m) + 1

    def xy(self, r, k):
        """Canto de cima à esquerda do slot (fileira r, camada k: 0 = fundo do porão)."""
        x = self.x0 + r * self.cw
        if k < self.th:
            y = self.hf - (k + 1) * self.ch
        else:
            y = self.deck_y - (k - self.th + 1) * self.ch
        return x, y

    def casco(self, tela, yw, t=0.0, tampa=True, guias=True, cheio_porao=True):
        s = self.s
        xa, xb = self.x0 - 6 * s, self.x1 + 6 * s
        yd = self.deck_y + 4 * s
        yfundo = self.hf + 4 * s
        pts = [(xa, yd - 6 * s), (xb, yd - 6 * s), (xb, yfundo - 8 * s), (xb - 8 * s, yfundo), (xa + 8 * s, yfundo),
               (xa, yfundo - 8 * s)]
        poligono(tela, [(px_ + (1 if px_ > (xa + xb) / 2 else -1), py_ + (1 if py_ > yd else -1)) for px_, py_ in pts], PRETO)
        poligono(tela, pts, CAS1)
        # pintura de baixo (vermelha) até a linha d'água
        sub_y = int(yw)
        for y in range(sub_y, int(yfundo) + 1):
            for x in range(int(xa), int(xb) + 1):
                if tela.buf[y, x] == CAS1:
                    tela.buf[y, x] = VMC1 if (x + y) % 2 else VMC0
        tela.ret(xa, yd - 6 * s, xb - xa, 1, ACO2)
        # interior do porão
        dither(tela, self.x0 - 1, self.deck_y + 4 * s, self.x1 - self.x0 + 2, self.hf - self.deck_y - 4 * s, FUNDO, FUNDO2)
        tela.ret(self.x0 - 2, self.hf, self.x1 - self.x0 + 4, 3 * s, ACO1)          # duplo fundo
        tela.ret(self.x0 - 2, self.hf, self.x1 - self.x0 + 4, 1, ACO2)
        tela.ret(self.x0 - 3, self.deck_y + 4 * s, 2, self.hf - self.deck_y - 4 * s, ACO0)
        tela.ret(self.x1 + 1, self.deck_y + 4 * s, 2, self.hf - self.deck_y - 4 * s, ACO0)
        if guias:
            for r in range(self.rows + 1):
                gx = self.x0 + r * self.cw - (1 if r == self.rows else 0)
                tela.ret(gx, self.deck_y + 4 * s, 1, self.hf - self.deck_y - 4 * s, ACO2)
        # brazola (borda da escotilha) e tampa
        tela.ret(xa, self.deck_y + 2 * s, self.x0 - xa - 1, 2 * s, ACO2)
        tela.ret(self.x1 + 1, self.deck_y + 2 * s, xb - self.x1 - 1, 2 * s, ACO2)
        if tampa:
            self.tampa(tela, self.deck_y)

    def tampa(self, tela, y):
        s = self.s
        tela.ret(self.x0 - 3, int(y) - 1, self.x1 - self.x0 + 6, 4 * s + 2, PRETO)
        tela.ret(self.x0 - 2, int(y), self.x1 - self.x0 + 4, 4 * s, ACO2)
        tela.ret(self.x0 - 2, int(y), self.x1 - self.x0 + 4, 1, ACO4)
        for x in range(self.x0 + 4, self.x1, 12 * s): tela.ret(x, int(y) + 1, 1, 4 * s - 1, ACO1)

    def cargas(self, tela, t=0.0, so=None, peao=True, ate_tier=None):
        for (r, k), pal in self.slots.items():
            if so and (r, k) not in so: continue
            if ate_tier is not None and k > ate_tier: continue
            x, y = self.xy(r, k)
            cont_frente(tela, x + 1, y + 1, self.cw - 1, self.ch - 1, pal, codigo=(pal is P_LAR), contorno=False)
            tela.ret(x, y, self.cw, 1, PRETO); tela.ret(x, y, 1, self.ch, PRETO)
        if peao:
            # travas (twistlocks) entre as camadas do convés
            for (r, k) in self.slots:
                if k >= self.th:
                    x, y = self.xy(r, k)
                    tela.px(x + 1, y + self.ch, ACO4); tela.px(x + self.cw - 1, y + self.ch, ACO4)

    def amarras(self, tela, cor=ACO3, ate=2):
        """Barras de amarração em X nas portas das camadas de baixo do convés."""
        for r in range(self.rows):
            for k in range(self.th, self.th + ate):
                if (r, k) not in self.slots: continue
                x, y = self.xy(r, k)
                yb = self.deck_y
                tela.linha(x + 1, yb - 1, x + self.cw - 1, y + 1, cor)
                tela.linha(x + self.cw - 1, yb - 1, x + 1, y + 1, cor)


# ================================================================ navio de lado
def navio_lado(tela, x0, yw, L, t=0.0, D=24, n_baias=None, cores_seed=1, nosso=None, alturas=None, ponte_u=.78,
               fumaca=True, arfagem=0.0, escala=1.0):
    """Navio porta-contêineres de lado (proa à direita). x0 = popa, yw = linha
    d'água, L = comprimento em px, D = pontal acima da água (px).
    `nosso` = (baia, camada) do nosso contêiner (desenhado laranja + mira).
    Devolve a posição (x, y) do nosso, ou None."""
    x0 = int(x0); yw = int(yw)
    dyp = lambda u: int(round(arfagem * (u - .5) * 6))     # arfagem (proa sobe/desce)
    yd = yw - D                                             # convés
    calado = max(6, D // 2)
    pts = [(x0 + 4, yd + dyp(0)), (x0 + L - 18, yd + dyp(1)), (x0 + L, yd - 4 + dyp(1)), (x0 + L - 6, yw + calado - 4 + dyp(1)),
           (x0 + L - 22, yw + calado + dyp(1)), (x0 + 14, yw + calado + dyp(0)), (x0, yw + 2 + dyp(0)), (x0 - 2, yd + 4 + dyp(0))]
    poligono(tela, [(px_ + (1 if px_ > x0 + L / 2 else -1), py_ + (1 if py_ > yw else -1)) for px_, py_ in pts], PRETO)
    poligono(tela, pts, CAS1)
    # costado: chapas e faixa
    for u in range(x0 + 10, x0 + L - 20, 14):
        tela.ret(u, yd + 3 + dyp((u - x0) / L), 1, D - 6, CAS0)
    yf = yd + 2
    tela.linha(x0 + 2, yf + dyp(0), x0 + L - 14, yf + dyp(1), ACO1)
    # pintura vermelha abaixo da água
    for x in range(max(0, x0 - 2), min(W, x0 + L + 2)):
        for y in range(yw + dyp((x - x0) / L), min(PALCO_H, yw + calado + 3)):
            if tela.buf[y, x] == CAS1: tela.buf[y, x] = VMC1 if (x + y) % 2 else VMC0
    # bulbo de proa / onda de proa
    xb = x0 + L - 8
    for k in range(4):
        u = (t * 1.6 + k / 4) % 1.0
        tela.px(xb + u * 6, yw - 1 - (1 - u) * 2 + dyp(1), ESPUMA)
    # contêineres no convés, em baias
    cw = max(4, int(round(6 * escala)))
    ch = max(3, int(round(3 * escala)))
    nb = n_baias or max(4, int((L * ponte_u - 26) // (cw + 1)))
    aux = None
    u_ponte = int(L * ponte_u)
    baias = []
    xa = x0 + 22
    for b in range(nb):
        bx = xa + b * (cw + 1)
        if bx + cw > x0 + u_ponte - 2 and bx < x0 + u_ponte + 14:
            continue
        if bx + cw > x0 + L - 26: break
        baias.append(bx)
    rng = np.random.default_rng(cores_seed)
    for b, bx in enumerate(baias):
        hmax = alturas[b] if alturas else int(3 + rng.integers(0, 3))
        for k in range(hmax):
            pal = OUTRAS[int(rng.integers(0, len(OUTRAS)))]
            y = yd - (k + 1) * (ch + 1) + dyp((bx - x0) / L)
            eh = nosso is not None and nosso[0] == b and nosso[1] == k
            if eh: pal = P_LAR
            tela.ret(bx - 1, y - 1, cw + 2, ch + 2, PRETO)
            tela.ret(bx, y, cw, ch, pal[2]); tela.ret(bx, y, cw, 1, pal[3])
            if cw >= 6: tela.ret(bx + cw // 2, y + 1, 1, ch - 1, pal[1])
            if eh: aux = (bx + cw // 2, y + ch // 2)
    # superestrutura (ponte de comando)
    sx = x0 + u_ponte
    h_ponte = int(D * 1.9)
    sy = yd - h_ponte + dyp(ponte_u)
    tela.ret(sx - 1, sy - 1, 14, h_ponte + 1, PRETO)
    tela.ret(sx, sy, 12, h_ponte, CERAMICA); tela.ret(sx, sy, 3, h_ponte, BRANCO)
    for k in range(2, h_ponte - 2, 5):
        tela.ret(sx + 4, sy + k, 6, 2, CHAMA0 if (k + int(t)) % 3 else ACO1)
    tela.ret(sx - 3, sy - 3, 18, 3, PRETO); tela.ret(sx - 2, sy - 2, 16, 1, BRANCO)
    tela.ret(sx + 5, sy - 9, 1, 6, ACO3)
    lampada_aviso(tela, sx + 5, sy - 10, t, VERMELHO)
    # casa de máquinas e chaminé na popa
    cx_ = x0 + 8
    tela.ret(cx_ - 1, yd - 15 + dyp(0), 10, 16, PRETO); tela.ret(cx_, yd - 14 + dyp(0), 8, 14, ACO2)
    tela.ret(cx_, yd - 14 + dyp(0), 8, 2, CAS0)
    if fumaca:
        for k in range(6):
            u = (t * .4 + k / 6) % 1.0
            tela.disco(cx_ + 4 - u * 30, yd - 18 - u * 16 + dyp(0), 1.2 + u * 3, ACO1 if u > .5 else ACO2)
    # mastro de proa
    tela.ret(x0 + L - 14, yd - 10 + dyp(1), 1, 10, ACO3)
    lampada_aviso(tela, x0 + L - 14, yd - 11 + dyp(1), t + .7, VERDE)
    # esteira na popa
    for k in range(6):
        u = (t * 1.2 + k / 6) % 1.0
        tela.ret(int(x0 - 4 - u * 40), yw + (k % 3) - 1, 4 + k % 3, 1, ESPUMA if u < .5 else MAR3)
    return aux


# ================================================================ painel da jornada
def painel_jornada(tela, k, t, mov=None, estado=None, cab=None, linhas=None, x0=302, acende=None, tudo=False,
                   rodape=None, codigo=True):
    """Painel da direita. k = etapa (0..7). `mov` = movimentos do nosso contêiner.
    `estado` = (rótulo, valor, cor). `cab` = (linha1, linha2, cor) troca o
    cabeçalho. `linhas` = [(rótulo, valor, cor)] (até 2) no lugar do código."""
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
        tela.texto(f"ETAPA {k + 1} DE 8", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(nome, x0, 26, cor, tam=17, contorno=PRETO)
    if linhas is None:
        tela.texto('O NOSSO CONTÊINER', x0, 48, ACO3, tam=9, contorno=PRETO)
        tela.ret(x0, 59, 7, 7, PRETO); tela.ret(x0 + 1, 60, 5, 5, LAR2); tela.px(x0 + 2, 61, LAR4)
        if codigo:
            tela.texto(CODIGO, x0 + 11, 59, LAR3, tam=9, contorno=PRETO)
            tela.texto("20 PÉS  22G1", x0 + 11, 69, ACO2, tam=9, contorno=PRETO)
        tela.texto('MOVIMENTOS DE GUINDASTE', x0, 86, ACO3, tam=9, contorno=PRETO)
        if mov is not None:
            n = int(mov)
            tela.texto(str(n), x0, 96, AMARELO if n > 0 else ACO2, tam=17, contorno=PRETO)
            for j in range(min(n, 8)):
                cont_frente(tela, x0 + 22 + j * 12, 98, 9, 10, P_LAR if j == n - 1 else P_CI)
        else:
            tela.texto('0', x0, 96, ACO2, tam=17, contorno=PRETO)
    else:
        for j, (rot, val, cv) in enumerate(linhas[:2]):
            y = 48 + j * 36
            tela.texto(rot, x0, y, ACO3, tam=9, contorno=PRETO)
            tela.texto(val, x0, y + 10, cv, tam=17 if tela.largura_texto(val, 17) <= 166 else 9, contorno=PRETO)
    if estado:
        rot, val, cv = estado
        tela.texto(rot, x0, 122, ACO3, tam=9, contorno=PRETO)
        tela.texto(val, x0, 132, cv, tam=17 if tela.largura_texto(val, 17) <= 166 else 9, contorno=PRETO)
    for j, (nm, cc) in enumerate(ETAPAS):
        bx = x0 + j * 21
        feito = j < k or tudo or (acende is not None and j < acende)
        atual = (j == k and not tudo and acende is None) or j == acende
        tela.ret(bx, 160, 17, 17, PRETO)
        if atual:
            tela.ret(bx + 1, 161, 15, 15, cc)
            tela.ret(bx + 1, 161, 15, 1, BRANCO)
        else:
            tela.ret_vazado(bx + 1, 161, 15, 15, cc if feito else ACO0)
        tela.texto(str(j + 1), bx + 9, 165, PRETO if atual else (cc if feito else ACO1), tam=9, centro=True)
    tela.texto(rodape or 'DA FÁBRICA → AO DESTINO', x0, 186, ACO2, tam=9, contorno=PRETO)


def selo_vertical(tela, k, cx, txt=None):
    """No Short o painel fica de fora: a etapa vai num selo no alto do recorte."""
    s = txt or f"ETAPA {k + 1} DE 8: {ETAPAS[k][0]}"
    w = tela.largura_texto(s, 9) + 10
    painel(tela, cx - w // 2, 1, w, 13, borda=ETAPAS[k][1] if txt is None else AMARELO)
    tela.texto(s, cx, 4, ETAPAS[k][1] if txt is None else AMARELO, tam=9, centro=True)


# ================================================================ ícones das 8 etapas (resumo)
def icone(tela, k, cx, cy, t, aceso=True):
    """Ícone 40x30 de cada etapa."""
    cx, cy = int(cx), int(cy)
    cor = ETAPAS[k][1] if aceso else ACO1
    tela.ret(cx - 21, cy - 16, 43, 33, PRETO)
    tela.ret(cx - 20, cy - 15, 41, 31, FUNDO2 if aceso else FUNDO)
    tela.ret_vazado(cx - 21, cy - 16, 43, 33, cor)
    if not aceso:
        tela.texto('?', cx, cy - 4, ACO1, tam=9, centro=True)
        return
    yb = cy + 12
    if k == 0:      # fábrica
        tela.ret(cx - 16, yb - 14, 22, 14, CIN1); tela.ret(cx - 16, yb - 14, 22, 1, CIN2)
        for j in range(3): tela.ret(cx - 16 + j * 7, yb - 18, 6, 4, CIN0)
        tela.ret(cx + 8, yb - 22, 3, 22, ACO1)
        tela.disco(cx + 9 - (t * 4) % 4, yb - 25 - (t * 4) % 4, 2, ACO2)
        cont_lado(tela, cx - 12, yb - 9, 16, 7, P_LAR, castanhas=False)
    elif k == 1:    # portão
        tela.ret(cx - 16, yb - 22, 3, 22, ACO2); tela.ret(cx + 13, yb - 22, 3, 22, ACO2)
        tela.ret(cx - 16, yb - 23, 32, 3, ACO3)
        ang = .5 + .5 * math.sin(t * 2)
        tela.linha(cx - 12, yb - 8, cx - 12 + 20 * math.cos(ang), yb - 8 - 20 * math.sin(ang), VERMELHO)
        if int(t * 3) % 2: tela.ret(cx - 2, yb - 20, 4, 14, CIANO)
    elif k == 2:    # pátio
        for j in range(3):
            for i in range(3 - (j % 2)):
                cont_frente(tela, cx - 15 + j * 11, yb - 9 - i * 9, 9, 8, OUTRAS[(i + j) % 5] if (i, j) != (0, 1) else P_LAR)
    elif k == 3:    # guindaste
        tela.ret(cx - 14, yb - 26, 3, 26, ACO3); tela.ret(cx - 2, yb - 26, 3, 26, ACO3)
        tela.ret(cx - 18, yb - 26, 38, 3, ACO4)
        tx = cx + 6 + 4 * math.sin(t * 2)
        tela.linha(tx, yb - 23, tx, yb - 14, ACO2)
        cont_frente(tela, int(tx) - 4, yb - 13, 9, 8, P_LAR)
    elif k == 4:    # no navio (corte)
        poligono(tela, [(cx - 18, yb - 12), (cx + 18, yb - 12), (cx + 14, yb), (cx - 14, yb)], CAS1)
        for i in range(4):
            for j in range(2):
                cont_frente(tela, cx - 15 + i * 8, yb - 20 - j * 8, 7, 7, P_LAR if (i, j) == (2, 1) else (P_CI if j else P_AZ))
    elif k == 5:    # amarração
        cont_frente(tela, cx - 12, yb - 22, 24, 20, P_LAR)
        tela.linha(cx - 12, yb, cx + 11, yb - 21, ACO4); tela.linha(cx + 11, yb, cx - 12, yb - 21, ACO4)
    elif k == 6:    # viagem
        mar(tela, cx - 20, cx + 21, yb - 4, yb + 4, t)
        poligono(tela, [(cx - 16, yb - 9), (cx + 16, yb - 9), (cx + 12, yb - 2), (cx - 14, yb - 2)], CAS1)
        for i in range(5): tela.ret(cx - 12 + i * 5, yb - 13, 4, 3, OUTRAS[i] [2] if i != 2 else LAR2)
    elif k == 7:    # chegada (porta aberta, caixas)
        cont_lado(tela, cx - 16, yb - 14, 24, 14, P_LAR, castanhas=False, portas=1.0)
        for j in range(2): tela.ret(cx + 12, yb - 6 - j * 6, 6, 5, CERAMICA)
