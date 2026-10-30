#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep11 — o desenho: céu, nuvem, chuva, água, a gota,
barragem, conduto, caracol e rotor da turbina, gerador, transformador,
torre e fios, subestação, poste, casa, tomada, lâmpada, os ícones das 9
etapas e o painel da jornada. Tudo genérico (nenhuma marca, nenhum logotipo).

A paleta do episódio é a `oficina` + 20 cores próprias (céu, grama, terra,
concreto, água em 4 tons, cobre e nuvem). Ela é registrada como 'ep11' e o
`longo` passa a usá-la neste processo (como o ep04 faz com a dele).
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
import idioma as I
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, BAYER8,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)

# ================================================================ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#101a36', '#1c2d57', '#2d4680',          # 32..34 céu (noite -> entardecer)
          '#163a24', '#24602f', '#4a9a3c',          # 35..37 grama
          '#3a2618', '#6a4428',                     # 38..39 terra
          '#555a66', '#878c97', '#b9bcc3',          # 40..42 concreto
          '#0b2552', '#17519e', '#3a8ee0', '#a6e0ff',  # 43..46 água: funda, meio, clara, espuma
          '#6e3416', '#b8642a', '#f0a462',          # 47..49 cobre
          '#3a4462', '#66729a']                     # 50..51 nuvem
PX.PALETAS['ep11'] = _BASE + _EXTRA
LG.PAL = 'ep11'
CEU0, CEU1, CEU2 = 32, 33, 34
GRAMA0, GRAMA1, GRAMA2 = 35, 36, 37
TERRA0, TERRA1 = 38, 39
CONC0, CONC1, CONC2 = 40, 41, 42
AGP, AGM, AGC, ESPUMA = 43, 44, 45, 46
COBRE0, COBRE1, COBRE2 = 47, 48, 49
NUVEM0, NUVEM1 = 50, 51

# ================================================================ a jornada
ETAPAS = [('CHUVA', AGC), ('REPRESA', ESPUMA), ('CONDUTO', CONC2), ('TURBINA', LARANJA),
          ('GERADOR', AMARELO), ('TRANSFORMADOR', COBRE2), ('TRANSMISSÃO', CIANO),
          ('SUBESTAÇÃO', VERDE), ('SUA CASA', CHAMA1)]
FORMAS = [('POTENCIAL', AGC), ('MOVIMENTO', LARANJA), ('ELÉTRICA', AMARELO)]

V_GERADOR = 13_800.0          # exemplo: 13,8 kV (padronizada; gerador de 480 V a 22 kV)
V_LINHA = 500_000.0           # 500 kV (padronizada)
V_SUB = 138_000.0             # 138 kV
V_DIST = 13_800.0             # 13,8 kV, distribuição primária
V_CASA = 220.0                # 220/127 V


def fmt_v(v):
    if v <= 0: return '0 V'
    if v < 1000: return f"{int(round(v))} V"
    kv = v / 1000.0
    if kv < 100 and abs(kv - round(kv)) > .05: return f"{I.decimal(kv, 1)} KV"
    return f"{I.milhar(kv)} KV"


def lerp(a, b, u): return a + (b - a) * u


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


def mira(tela, x, y, t, r=10):
    c = BRANCO if int(t * 4) % 2 else AMARELO
    for sx in (-1, 1):
        for sy in (-1, 1):
            tela.ret(int(x + sx * r) - (3 if sx > 0 else 0), int(y + sy * r), 4, 1, c)
            tela.ret(int(x + sx * r), int(y + sy * r) - (3 if sy > 0 else 0), 1, 4, c)


def caixa(tela, x, y, w, h, cor, luz_=None, sombra=None):
    """Bloco com contorno preto, luz em cima/esquerda e sombra embaixo/direita."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, cor)
    if luz_ is not None:
        tela.ret(x, y, w, 1, luz_); tela.ret(x, y, 1, h, luz_)
    if sombra is not None:
        tela.ret(x, y + h - 1, w, 1, sombra); tela.ret(x + w - 1, y, 1, h, sombra)


def grad_v(tela, x, y, w, h, cores, mascara=None, fase=0):
    """Degradê vertical com Bayer 8x8 entre a lista de cores (de cima para baixo)."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(tela.w, int(x + w)), min(tela.h, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u = (yy - y) / max(1.0, h - 1) * (len(cores) - 1)
    b = BAYER8[(yy + fase) % 8, xx % 8]
    i = np.clip(np.floor(u) + (u - np.floor(u) > b), 0, len(cores) - 1).astype(int)
    v = np.array(cores, np.uint8)[i]
    if mascara is not None:
        m = mascara(xx, yy)
        tela.buf[y0:y1, x0:x1][m] = v[m]
    else:
        tela.buf[y0:y1, x0:x1] = v


def grad_h(tela, x, y, w, h, cores):
    """Degradê horizontal (cilindro visto de lado: luz, meio, sombra)."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(tela.w, int(x + w)), min(tela.h, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    u = (xx - x) / max(1.0, w - 1) * (len(cores) - 1)
    b = BAYER8[yy % 8, xx % 8]
    i = np.clip(np.floor(u) + (u - np.floor(u) > b), 0, len(cores) - 1).astype(int)
    tela.buf[y0:y1, x0:x1] = np.array(cores, np.uint8)[i]


def ceu(tela, y1=PALCO_H, x0=0, x1=W, t=0.0, estrelas=True, cores=(CEU0, CEU0, CEU1, CEU2)):
    grad_v(tela, x0, 0, x1 - x0, y1, list(cores))
    if estrelas:
        for k in range(28):
            x = x0 + (k * 97 + 13) % max(1, x1 - x0)
            y = (k * 53 + 7) % max(1, int(y1 * .5))
            if math.sin(t * 1.7 + k * 2.3) > -.2: tela.px(x, y, BRANCO if k % 4 == 0 else ACO3)


def nuvem(tela, cx, cy, w, cor=NUVEM1, escura=NUVEM0, luz_=ACO3, chuva=False):
    """Nuvem de pixel: discos sobrepostos, contorno, base achatada e luz no topo."""
    bolas = [(-.38, .10, .26), (-.16, -.12, .32), (.12, -.18, .30), (.34, .02, .24), (.0, .1, .3)]
    for dx, dy, r in bolas:
        tela.disco(cx + dx * w, cy + dy * w, r * w + 1, PRETO)
    for dx, dy, r in bolas:
        tela.disco(cx + dx * w, cy + dy * w, r * w, escura if chuva else cor)
    for dx, dy, r in bolas:
        tela.disco(cx + dx * w - r * w * .18, cy + dy * w - r * w * .22, r * w * .7, cor if chuva else luz_)
    tela.ret(cx - .62 * w, cy + .2 * w, 1.24 * w, .2 * w + 1, PRETO)
    dither(tela, cx - .6 * w, cy + .14 * w, 1.2 * w, .08 * w + 1, escura, cor if chuva else escura)


def chuva(tela, x0, x1, ytop, ybase, t, n=40, vel=150.0, cor=AGC, seed=0, chao=None):
    """Riscos de chuva caindo inclinados. `chao(x)` = altura onde cada gota some."""
    for k in range(n):
        fase = ((k * 0.6180339 + seed * .37) % 1.0)
        x = x0 + ((k * 73 + seed * 31) % max(1, int(x1 - x0)))
        h = ybase - ytop
        y = ytop + ((t * vel + fase * h) % h)
        xx = x - (y - ytop) * .18
        lim = chao(xx) if chao else ybase
        if y > lim: continue
        tela.linha(xx, y, xx + 1, y - 5, cor)
        if k % 5 == 0: tela.px(xx, y, ESPUMA)


def respingo(tela, x, y, u, cor=ESPUMA):
    """Respingo de gota ao bater (u de 0 a 1)."""
    if not 0 <= u < 1: return
    r = 1 + u * 4
    tela.px(x - r, y - 1 - (1 - u) * 2, cor); tela.px(x + r, y - 1 - (1 - u) * 2, cor)
    tela.px(x, y - 2 - (1 - u) * 3, cor)


def agua(tela, x0, x1, ytop, ybot, t, cores=(AGC, AGM, AGM, AGP, AGP), onda=1.0, brilho=True, vel=1.6, ondas_k=.14):
    """Bloco de água com superfície ondulando, degradê de profundidade e
    reflexos que correm. Devolve a função de altura da superfície."""
    x0, x1 = int(x0), int(x1)
    if x1 <= x0: return lambda x: ytop
    xs = np.arange(x0, x1)
    sup = ytop + np.round(onda * np.sin(xs * ondas_k + t * vel) + onda * .5 * np.sin(xs * .05 - t * .9)).astype(int)
    y0 = int(sup.min())
    grad_v(tela, x0, y0, x1 - x0, ybot - y0, list(cores), mascara=lambda xx, yy: yy >= sup[xx - x0])
    for i, x in enumerate(xs):
        tela.px(x, sup[i], ESPUMA if (x + int(t * 8)) % 9 < 6 else AGC)
    if brilho:
        for k in range(max(1, (x1 - x0) // 22)):
            xx = x0 + ((k * 37 + int(t * 14)) % max(1, x1 - x0 - 8))
            yy = ytop + 3 + (k * 7) % max(1, min(14, ybot - ytop - 4))
            if yy < ybot - 1: tela.ret(xx, yy, 4 + k % 3, 1, AGC)
    return lambda x: ytop + onda * math.sin(x * ondas_k + t * vel)


# ================================================================ a gota (protagonista)
def gota(tela, cx, cy, s=1.0, t=0.0, prota=True, cor=AGC, sombra=AGM):
    """Gota em lágrima: corpo redondo embaixo, ponta para cima. A nossa
    (prota) tem brilho amarelo piscando ao lado para nunca se perder."""
    r = 3.2 * s
    topo = (cx, cy - r * 2.5)
    a = math.asin(min(1.0, r / (r * 2.5)))
    tx = r * math.cos(a)
    ty = cy - r * math.sin(a)
    tela.disco(cx, cy, r + 1, PRETO)
    poligono(tela, [(topo[0], topo[1] - 1.3), (cx + tx + 1.1, ty), (cx - tx - 1.1, ty)], PRETO)
    tela.disco(cx, cy, r, cor)
    poligono(tela, [topo, (cx + tx, ty + .5), (cx - tx, ty + .5)], cor)
    tela.disco(cx + r * .35, cy + r * .3, r * .6, sombra)
    tela.disco(cx + r * .1, cy + r * .05, r * .55, cor)
    tela.disco(cx - r * .4, cy - r * .35, max(.6, r * .28), ESPUMA)
    tela.px(cx - r * .45, cy - r * .45, BRANCO)
    if prota:
        k = int(t * 3) % 4
        bx, by = cx + r + 3, cy - r * 1.6
        if k < 3:
            tela.px(bx, by, AMARELO); tela.px(bx - 1, by, AMARELO); tela.px(bx + 1, by, AMARELO)
            tela.px(bx, by - 1, AMARELO); tela.px(bx, by + 1, AMARELO)
            if k == 1: tela.px(bx, by, BRANCO)


def marca_gota(tela, x, y, t, txt='A NOSSA GOTA', lado=1, dy=-22, cor=AMARELO):
    """Rótulo com fio apontando para a gota."""
    w = tela.largura_texto(txt, 9)
    lx = x + lado * 14 - (w if lado < 0 else 0)
    ly = y + dy
    rotulo(tela, txt, lx, ly, cor)
    fio(tela, x + lado * 12, ly + 9, x + lado * 3, y - 5, cor)


def faisca(tela, x, y, t, r=2.5):
    """A energia (protagonista depois da turbina): um ponto de luz que pulsa."""
    p = 1 + .25 * math.sin(t * 12)
    luz(tela, x, y, r * p, BRANCO, AMARELO, CHAMA1)


# ================================================================ terreno
def morro(tela, pts, cor, luz_=None, base=PALCO_H):
    poligono(tela, [(pts[0][0], base)] + pts + [(pts[-1][0], base)], cor)
    if luz_ is not None:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            tela.linha(ax, ay, bx, by, luz_)


def interp(pts, x):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if ax <= x <= bx:
            return ay + (by - ay) * (x - ax) / max(1e-6, bx - ax)
    return pts[-1][1] if x > pts[-1][0] else pts[0][1]


def ao_longo(pts, u):
    """Ponto a fração u (0..1) do comprimento de uma poligonal."""
    seg = [math.hypot(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(pts, pts[1:])]
    L = sum(seg) or 1
    d = max(0.0, min(1.0, u)) * L
    for (a, b), s in zip(zip(pts, pts[1:]), seg):
        if d <= s:
            v = d / max(1e-6, s)
            return a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v
        d -= s
    return pts[-1]


def arvore(tela, x, yb, h=12, cor=GRAMA1, escura=GRAMA0):
    tela.ret(x - 1, yb - h // 3, 2, h // 3, TERRA1)
    tela.disco(x, yb - h * .62, h * .42 + 1, PRETO)
    tela.disco(x, yb - h * .62, h * .42, escura)
    tela.disco(x - 1, yb - h * .7, h * .3, cor)


# ================================================================ metal, tubo, parafuso
def tubo(tela, x0, y0, x1, y1, esp, t=0.0, fluxo=True, vel=60.0, aberto=1.0, parede=ACO1, luz_=ACO3, agua_on=True):
    """Tubo em corte (parede de aço, água correndo por dentro)."""
    linha_grossa(tela, x0, y0, x1, y1, esp + 4, PRETO)
    linha_grossa(tela, x0, y0, x1, y1, esp + 2, parede)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    tela.linha(x0 + nx * (-esp / 2 - .5), y0 + ny * (-esp / 2 - .5), x1 + nx * (-esp / 2 - .5), y1 + ny * (-esp / 2 - .5), luz_)
    if agua_on:
        linha_grossa(tela, x0, y0, x1, y1, esp - 2, AGM)
        linha_grossa(tela, x0 - nx * esp * .2, y0 - ny * esp * .2, x1 - nx * esp * .2, y1 - ny * esp * .2, esp * .35, AGC)
        if fluxo and aberto > 0:
            for k in range(int(L / 9)):
                u = ((k * 9 + t * vel * aberto) % L) / L
                off = ((k * 5) % 7 - 3) / 7 * esp * .7
                px, py = x0 + dx * u + nx * off, y0 + dy * u + ny * off
                tela.linha(px, py, px - dx / L * 4, py - dy / L * 4, ESPUMA if k % 3 == 0 else AGC)
    else:
        linha_grossa(tela, x0, y0, x1, y1, esp - 2, FUNDO2)
    return nx, ny


def parafusos_anel(tela, cx, cy, r, n, ang, cor=ACO3):
    for k in range(n):
        a = ang + k * 2 * math.pi / n
        tela.px(cx + math.cos(a) * r, cy + math.sin(a) * r, cor)


# ================================================================ painel da jornada
def painel_jornada(tela, k, t, forma=None, tensao=None, estado=None, cab=None, x0=302,
                   acende=None, tudo=False, rodape=None, linhas=None):
    """Painel da direita. k = índice da etapa (0..8). `forma` = 0, 1 ou 2
    (potencial, movimento, elétrica). `tensao` em volts (None = esconde).
    `estado` = (rótulo, valor, cor). `cab` = (linha1, linha2, cor) troca o
    cabeçalho ETAPA. `linhas` = [(rótulo, valor, cor)] no lugar de forma/tensão."""
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
        tela.texto(f"ETAPA {k + 1} DE 9", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(nome, x0, 26, cor, tam=17, contorno=PRETO)
    if linhas is None:
        tela.texto('FORMA DA ENERGIA', x0, 48, ACO3, tam=9, contorno=PRETO)
        for j, (nm, cc) in enumerate(FORMAS):
            y = 59 + j * 10
            if forma is not None and j == forma:
                tela.ret(x0, y, 7, 7, PRETO); tela.ret(x0 + 1, y + 1, 5, 5, cc)
                tela.px(x0 + 2, y + 2, BRANCO)
                tela.texto(nm, x0 + 11, y, cc, tam=9, contorno=PRETO)
                if int(t * 3) % 2 == 0: tela.texto('<', x0 + 13 + tela.largura_texto(nm, 9), y, cc, tam=9)
            elif forma is not None and j < forma:
                tela.ret_vazado(x0 + 1, y + 1, 5, 5, ACO2)
                tela.texto(nm, x0 + 11, y, ACO2, tam=9)
            else:
                tela.ret_vazado(x0 + 1, y + 1, 5, 5, ACO0)
                tela.texto(nm, x0 + 11, y, ACO1, tam=9)
        tela.texto('TENSÃO NO FIO', x0, 92, ACO3, tam=9, contorno=PRETO)
        v = tensao or 0
        tela.texto(fmt_v(v), x0, 102, AMARELO if v > 0 else ACO2, tam=17, contorno=PRETO)
    else:
        for j, (rot, val, cv) in enumerate(linhas[:2]):
            y = 48 + j * 40
            tela.texto(rot, x0, y, ACO3, tam=9, contorno=PRETO)
            tela.texto(val, x0, y + 10, cv, tam=17 if tela.largura_texto(val, 17) <= 166 else 9, contorno=PRETO)
    if estado:
        rot, val, cv = estado
        tela.texto(rot, x0, 126, ACO3, tam=9, contorno=PRETO)
        tela.texto(val, x0, 136, cv, tam=17 if tela.largura_texto(val, 17) <= 166 else 9, contorno=PRETO)
    for j, (nm, cc) in enumerate(ETAPAS):
        bx = x0 + j * 18
        feito = j < k or tudo or (acende is not None and j < acende)
        atual = (j == k and not tudo and acende is None) or j == acende
        tela.ret(bx, 162, 15, 15, PRETO)
        if atual:
            tela.ret(bx + 1, 163, 13, 13, cc)
            tela.ret(bx + 1, 163, 13, 1, BRANCO)
        else:
            tela.ret_vazado(bx + 1, 163, 13, 13, cc if feito else ACO0)
        tela.texto(str(j + 1), bx + 8, 166, PRETO if atual else (cc if feito else ACO1), tam=9, centro=True)
    tela.texto(rodape or 'DA CHUVA → À TOMADA', x0, 186, ACO2, tam=9, contorno=PRETO)


def selo_vertical(tela, k, cx, txt=None):
    """No Short o painel fica de fora: a etapa vai num selo no alto do recorte."""
    s = txt or f"ETAPA {k + 1} DE 9: {ETAPAS[k][0]}"
    w = tela.largura_texto(s, 9) + 10
    painel(tela, cx - w // 2, 1, w, 13, borda=ETAPAS[k][1] if txt is None else AMARELO)
    tela.texto(s, cx, 4, ETAPAS[k][1] if txt is None else AMARELO, tam=9, centro=True)


# ================================================================ barragem e usina (corte)
def concreto(tela, pts, t=0.0, juntas=True, cores=(CONC2, CONC1, CONC1, CONC0)):
    """Polígono de concreto com contorno, degradê e juntas de concretagem."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    poligono(tela, pts, PRETO)
    inner = []
    cxm, cym = sum(xs) / len(xs), sum(ys) / len(ys)
    for x, y in pts:
        dx, dy = cxm - x, cym - y
        L = math.hypot(dx, dy) or 1
        inner.append((x + dx / L * 1.2, y + dy / L * 1.2))
    tmp = np.zeros_like(tela.buf[:PALCO_H])
    # máscara do polígono: desenha numa cor sentinela e lê de volta
    sent = 255
    bk = tela.buf.copy()
    poligono(tela, inner, sent)
    m = tela.buf == sent
    tela.buf[:] = bk
    def masc(xx, yy): return m[yy, xx]
    grad_v(tela, x0, y0, x1 - x0 + 1, y1 - y0 + 1, list(cores), mascara=masc)
    if juntas:
        for yj in range(int(y0) + 12, int(y1), 12):
            row = np.nonzero(m[yj])[0] if 0 <= yj < tela.h else []
            if len(row): tela.ret(row[0], yj, row[-1] - row[0] + 1, 1, CONC0)
    return m


def casa_de_forca(tela, x, y, w, h, t=0.0, janelas=True):
    caixa(tela, x, y, w, h, CONC1, CONC2, CONC0)
    tela.ret(x - 2, y - 3, w + 4, 3, PRETO); tela.ret(x - 1, y - 2, w + 2, 1, ACO2)
    if janelas:
        for k in range(max(1, (w - 6) // 9)):
            jx = x + 4 + k * 9
            on = (math.sin(t * 1.3 + k * 1.7) > -.6)
            tela.ret(jx, y + 4, 5, 4, PRETO); tela.ret(jx + 1, y + 5, 3, 2, CHAMA1 if on else FUNDO3)


# ================================================================ turbina Francis (vista de cima)
class Caracol:
    """Caixa espiral (caracol) vista de cima: a água entra por um tubo à
    esquerda no alto e dá a volta no sentido horário, com o raio caindo de
    R0 a RI; por dentro, o anel das palhetas e o rotor."""

    def __init__(self, cx, cy, R0=92.0, RI=56.0, RG=50.0, RR=40.0):
        self.cx, self.cy, self.R0, self.RI, self.RG, self.RR = cx, cy, R0, RI, RG, RR

    def R(self, s):
        """s em 0..1: fração da volta a partir do alto (-90°)."""
        return self.R0 + (self.RI - self.R0) * s

    def p(self, s, r):
        a = -math.pi / 2 + s * 2 * math.pi
        return self.cx + math.cos(a) * r, self.cy + math.sin(a) * r

    def contorno(self, n=90):
        return [self.p(i / n, self.R(i / n)) for i in range(n + 1)]

    def desenhar(self, tela, t, abertura=1.0, ang_rotor=0.0, fluxo=1.0):
        cx, cy = self.cx, self.cy
        ext = self.contorno()
        # tubo de entrada: do canto esquerdo até o começo da espiral
        y_top, y_bot = cy - self.R0, cy - self.RI
        poli = [(-2, y_top)] + ext + [(cx, y_bot), (-2, y_bot)]
        # parede (aço) por fora
        grossa = [(x, y) for x, y in ext]
        for (ax, ay), (bx, by) in zip(grossa, grossa[1:]):
            linha_grossa(tela, ax, ay, bx, by, 9, PRETO)
        for (ax, ay), (bx, by) in zip(grossa, grossa[1:]):
            linha_grossa(tela, ax, ay, bx, by, 6, ACO1)
        for (ax, ay), (bx, by) in zip(grossa, grossa[1:]):
            tela.linha(ax + (ax - cx) * .045, ay + (ay - cy) * .045, bx + (bx - cx) * .045, by + (by - cy) * .045, ACO3)
        tela.ret(0, y_top - 5, cx, 5, PRETO); tela.ret(0, y_top - 4, cx, 3, ACO1)
        tela.ret(0, y_top - 4, cx, 1, ACO3)
        # água
        poligono(tela, poli, AGM)
        xl = cx - self.RI * .2
        y_esq = y_bot
        tela.ret(0, y_bot, xl - 40, 4, PRETO); tela.ret(0, y_bot + 1, xl - 40, 2, ACO1)
        tela.disco(cx, cy, self.RI, AGM)
        # faixas de cor seguindo a espiral (mais clara por fora)
        for i in range(0, 90, 1):
            s = i / 90
            for fr, cor in ((.82, AGC), (.55, AGM)):
                x, y = self.p(s, self.RI + (self.R(s) - self.RI) * fr)
                tela.px(x, y, cor)
        tela.ret(0, y_top + 3, cx, 2, AGC)
        # correnteza: tracinhos andando pela espiral
        for k in range(46):
            u = (k / 46 + t * .09 * fluxo) % 1.0
            if k % 2 == 0:
                # no tubo de entrada (u em 0..1 -> x de 0 a cx)
                x = u * cx
                y = y_top + 6 + (k * 7) % int(self.R0 - self.RI - 10)
                tela.ret(x, y, 4, 1, ESPUMA if k % 6 == 0 else AGC)
            else:
                fr = .25 + .55 * ((k * 37) % 10) / 10
                x, y = self.p(u, self.RI + (self.R(u) - self.RI) * fr)
                x2, y2 = self.p(u - .015, self.RI + (self.R(u - .015) - self.RI) * fr)
                tela.linha(x2, y2, x, y, ESPUMA if k % 5 == 1 else AGC)
        # anel fixo e palhetas
        tela.anel(cx, cy, self.RI + .5, PRETO, 1.2)
        n = 16
        for k in range(n):
            a = k * 2 * math.pi / n
            px, py = cx + math.cos(a) * self.RG * 1.04, cy + math.sin(a) * self.RG * 1.04
            # fechada: tangente; aberta: gira 50° para dentro
            ang = a + math.pi / 2 + (1 - abertura) * 0.0 - abertura * .9
            L = 6.5
            ux, uy = math.cos(ang) * L, math.sin(ang) * L
            linha_grossa(tela, px - ux, py - uy, px + ux, py + uy, 4, PRETO)
            linha_grossa(tela, px - ux, py - uy, px + ux, py + uy, 2.2, ACO3)
            tela.px(px, py, ACO4)
        # rotor (corredor) girando
        self.rotor(tela, t, ang_rotor)

    def rotor(self, tela, t, ang):
        cx, cy, RR = self.cx, self.cy, self.RR
        tela.disco(cx, cy, RR + 1, PRETO)
        tela.disco(cx, cy, RR, FUNDO3)
        dither(tela, cx - RR, cy - RR, 2 * RR, 2 * RR, FUNDO3, FUNDO3)
        tela.disco(cx, cy, RR, AGP)
        nb = 13
        for b in range(nb):
            pts = []
            for i in range(9):
                r = 12 + (RR - 13) * i / 8
                a = ang + b * 2 * math.pi / nb + .75 * (i / 8) ** 1.3
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                linha_grossa(tela, ax, ay, bx, by, 4.2, PRETO)
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                linha_grossa(tela, ax, ay, bx, by, 2.4, ACO2)
            for (ax, ay), (bx, by) in zip(pts[:5], pts[1:5]):
                tela.linha(ax, ay, bx, by, ACO4)
        tela.anel(cx, cy, RR, ACO1, 1.0)
        tela.disco(cx, cy, 13, PRETO)
        tela.disco(cx, cy, 12, ACO2)
        tela.disco(cx - 3, cy - 3, 6, ACO3)
        tela.disco(cx, cy, 4, ACO1)
        parafusos_anel(tela, cx, cy, 9, 8, ang, ACO4)


# ================================================================ gerador (de frente)
def gerador_frente(tela, cx, cy, ang, t, Rext=84, polos=12, brilho_bobina=None, lento=True):
    """Estator (anel com bobinas) e rotor com polos N/S alternados.
    `brilho_bobina(phi)` -> valor -1..1 da corrente na bobina na posição phi."""
    # carcaça
    tela.disco(cx, cy, Rext + 2, PRETO)
    tela.disco(cx, cy, Rext, ACO1)
    for r, c in ((Rext - 3, ACO0), (Rext - 6, ACO1)):
        tela.anel(cx, cy, r, c, .6)
    tela.anel(cx, cy, Rext - 1, ACO3, .5)
    parafusos_anel(tela, cx, cy, Rext - 3, 32, 0, ACO3)
    # anel de bobinas
    Rb0, Rb1 = 62, 74
    tela.disco(cx, cy, Rb1 + 1, PRETO)
    tela.disco(cx, cy, Rb1, ACO0)
    nb = 24
    for k in range(nb):
        phi = -math.pi / 2 + k * 2 * math.pi / nb
        v = brilho_bobina(phi) if brilho_bobina else 0.0
        if v > .45: c1, c2 = CHAMA0, AMARELO
        elif v < -.45: c1, c2 = MISTURA2, CIANO
        else: c1, c2 = COBRE2, COBRE1
        for i in range(5):
            r = Rb0 + 1 + i * 2.4
            a0 = phi - .09
            a1 = phi + .09
            x0, y0 = cx + math.cos(a0) * r, cy + math.sin(a0) * r
            x1, y1 = cx + math.cos(a1) * r, cy + math.sin(a1) * r
            linha_grossa(tela, x0, y0, x1, y1, 2.0, COBRE0 if i % 2 else c2)
        xa, ya = cx + math.cos(phi - .1) * (Rb0 + 6), cy + math.sin(phi - .1) * (Rb0 + 6)
        tela.px(xa, ya, c1)
    # entreferro
    tela.disco(cx, cy, Rb0 - 1, PRETO)
    # rotor
    Rr = 58
    tela.disco(cx, cy, Rr - 14, ACO0)
    for k in range(polos):
        a = ang + k * 2 * math.pi / polos
        n = k % 2 == 0
        cor, cl = (VERMELHO, ROSA) if n else (MISTURA, MISTURA2)
        w = .18
        pts = [(cx + math.cos(a + s * w) * r, cy + math.sin(a + s * w) * r) for s, r in ((-1, 40), (-1.15, Rr), (1.15, Rr), (1, 40))]
        poligono(tela, [(x + (1 if x > cx else -1) * 0, y) for x, y in pts], PRETO)
        pts2 = [(cx + math.cos(a + s * w * .82) * r, cy + math.sin(a + s * w * .82) * r) for s, r in ((-1, 41), (-1.12, Rr - 1.5), (1.12, Rr - 1.5), (1, 41))]
        poligono(tela, pts2, cor)
        lx, ly = cx + math.cos(a - w * .5) * (Rr - 3), cy + math.sin(a - w * .5) * (Rr - 3)
        tela.px(lx, ly, cl)
        tx, ty = cx + math.cos(a) * 49, cy + math.sin(a) * 49
        tela.texto('N' if n else 'S', tx, ty - 3, BRANCO, tam=9, centro=True, contorno=PRETO)
    tela.disco(cx, cy, 39, PRETO)
    tela.disco(cx, cy, 38, ACO1)
    for k in range(6):
        a = ang + k * math.pi / 3 + math.pi / 12
        linha_grossa(tela, cx + math.cos(a) * 14, cy + math.sin(a) * 14, cx + math.cos(a) * 37, cy + math.sin(a) * 37, 5, ACO2)
        tela.linha(cx + math.cos(a) * 15, cy + math.sin(a) * 15, cx + math.cos(a) * 36, cy + math.sin(a) * 36, ACO3)
    tela.anel(cx, cy, 37, ACO0, .6)
    tela.disco(cx, cy, 14, PRETO)
    tela.disco(cx, cy, 13, ACO2)
    tela.disco(cx - 3, cy - 3, 6, ACO3)
    tela.disco(cx, cy, 5, ACO0)
    parafusos_anel(tela, cx, cy, 10, 8, ang, ACO4)


# ================================================================ transformador
def bobina(tela, x, y0, y1, w, voltas, t, corrente=1.0, fase=0.0, esp=3, cor=COBRE1, luz_=COBRE2, sombra=COBRE0):
    """Bobina enrolada numa perna vertical do núcleo (x = centro)."""
    n = max(1, voltas)
    passo = (y1 - y0) / n
    for k in range(n):
        y = y0 + k * passo + passo / 2
        tela.ret(x - w // 2 - 1, y - esp / 2 - 1, w + 2, esp + 2, PRETO)
        tela.ret(x - w // 2, y - esp / 2, w, esp, cor)
        tela.ret(x - w // 2, y - esp / 2, w, 1, luz_)
        tela.ret(x + w // 2 - 3, y - esp / 2, 3, esp, sombra)
    # a corrente: pontinhos correndo pelas espiras (sobe e desce com a fase)
    if corrente > 0:
        nd = int(4 + corrente * 4)
        for k in range(nd):
            u = (k / nd + math.sin(t * 2 * math.pi * .5 + fase) * .12) % 1.0
            kk = int(u * n)
            y = y0 + kk * passo + passo / 2
            xx = x - w // 2 + 2 + ((u * n) % 1.0) * (w - 4)
            r = .6 + corrente * 1.2
            tela.disco(xx, y, r, AMARELO)


def nucleo(tela, x, y, w, h, perna=22, t=0.0, fluxo=0.0):
    """Núcleo magnético em lâminas (vista de frente) com o fluxo circulando."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    for yy in range(y, y + h, 2):
        tela.ret(x, yy, w, 1, ACO1); tela.ret(x, yy + 1, w, 1, ACO0)
    tela.ret(x + perna, y + perna, w - 2 * perna, h - 2 * perna, FUNDO)
    tela.ret_vazado(x + perna - 1, y + perna - 1, w - 2 * perna + 2, h - 2 * perna + 2, PRETO)
    tela.ret(x, y, w, 1, ACO3); tela.ret(x, y, 1, h, ACO3)
    # fluxo: setas que andam no anel (sentido troca com a corrente)
    if abs(fluxo) > .05:
        per = 2 * ((w - perna) + (h - perna))
        n = 10
        for k in range(n):
            s = (k / n + t * .25 * (1 if fluxo > 0 else -1)) % 1.0
            d = s * per
            a, b = w - perna, h - perna
            m = perna / 2
            if d < a: px, py, dx, dy = x + m + d, y + m, 1, 0
            elif d < a + b: px, py, dx, dy = x + w - m, y + m + (d - a), 0, 1
            elif d < 2 * a + b: px, py, dx, dy = x + w - m - (d - a - b), y + h - m, -1, 0
            else: px, py, dx, dy = x + m, y + h - m - (d - 2 * a - b), 0, -1
            if fluxo < 0: dx, dy = -dx, -dy
            cor = ROXO if abs(fluxo) > .5 else FUNDO3
            if dx: seta(tela, px, py, dx, 0, cor, 3)
            else: seta(tela, px, py, 0, dy, cor, 3)


def transformador_tanque(tela, x, yb, w, h, t, buchas=3, alta=True):
    """Transformador de subestação (tanque, aletas de radiador, buchas)."""
    caixa(tela, x, yb - h, w, h, ACO1, ACO2, ACO0)
    for k in range(4, w - 3, 4):
        tela.ret(x + k, yb - h + 4, 1, h - 8, ACO0)
    tela.ret(x - 6, yb - h + 6, 5, h - 10, PRETO); tela.ret(x - 5, yb - h + 7, 3, h - 12, ACO2)
    for k in range(buchas):
        bx = x + 6 + k * (w - 12) // max(1, buchas - 1)
        hh = 14 if alta else 9
        tela.ret(bx - 2, yb - h - hh, 5, hh, PRETO)
        for j in range(0, hh, 3):
            tela.ret(bx - 2 + (0 if j % 6 else 0), yb - h - hh + j, 5, 2, CERAMICA if j % 6 else ACO3)
        tela.ret(bx - 1, yb - h - hh - 2, 3, 2, ACO3)
    tela.ret(x + 3, yb, 3, 3, PRETO); tela.ret(x + w - 6, yb, 3, 3, PRETO)


# ================================================================ transmissão
def torre(tela, x, yb, h, cor=ACO2, escura=ACO0):
    """Torre de treliça de linha de transmissão (silhueta com cruzetas)."""
    topo = yb - h
    base = h * .28
    # pernas
    for s in (-1, 1):
        linha_grossa(tela, x + s * base, yb, x + s * 3, topo + 6, 3, PRETO)
        tela.linha(x + s * base, yb, x + s * 3, topo + 6, cor)
    # treliça (X)
    n = 6
    for i in range(n):
        ya = yb - h * i / n * .92
        yb2 = yb - h * (i + 1) / n * .92
        wa = base - (base - 3) * i / n
        wb = base - (base - 3) * (i + 1) / n
        tela.linha(x - wa, ya, x + wb, yb2, escura)
        tela.linha(x + wa, ya, x - wb, yb2, escura)
        tela.linha(x - wb, yb2, x + wb, yb2, escura)
    # cruzetas
    for j, (yy, ww) in enumerate(((topo + 8, 20), (topo + 18, 14))):
        tela.ret(x - ww, yy, 2 * ww + 1, 3, PRETO); tela.ret(x - ww, yy + 1, 2 * ww + 1, 1, cor)
    tela.ret(x - 1, topo, 3, 9, PRETO); tela.px(x, topo + 1, cor)
    return [(x - 19, topo + 12), (x + 19, topo + 12), (x - 13, topo + 22), (x + 13, topo + 22)]


def isolador(tela, x, y, n=3):
    for k in range(n):
        tela.ret(x - 2, y + k * 2, 5, 1, CERAMICA); tela.px(x, y + k * 2 + 1, ACO2)


def catenaria(tela, ax, ay, bx, by, flecha, cor, esp=1):
    n = int(abs(bx - ax)) + 1
    pts = []
    for i in range(n + 1):
        u = i / max(1, n)
        x = ax + (bx - ax) * u
        y = ay + (by - ay) * u + flecha * 4 * u * (1 - u)
        pts.append((x, y))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if esp > 1: linha_grossa(tela, x0, y0, x1, y1, esp, cor)
        else: tela.linha(x0, y0, x1, y1, cor)
    return pts


def ponto_cat(ax, ay, bx, by, flecha, u):
    return ax + (bx - ax) * u, ay + (by - ay) * u + flecha * 4 * u * (1 - u)


# ================================================================ poste, casa, tomada, lâmpada
def poste(tela, x, yb, h, t=0.0, trafo=True):
    topo = yb - h
    tela.ret(x - 3, topo, 7, h, PRETO)
    tela.ret(x - 2, topo, 5, h, CONC1)
    tela.ret(x - 2, topo, 1, h, CONC2); tela.ret(x + 2, topo, 1, h, CONC0)
    # cruzeta
    tela.ret(x - 22, topo + 6, 45, 4, PRETO); tela.ret(x - 21, topo + 7, 43, 2, TERRA1)
    for dx in (-18, 0, 18):
        isolador(tela, x + dx, topo + 2, 2)
    if trafo:
        tx, ty = x + 6, topo + 28
        caixa(tela, tx, ty, 16, 24, ACO1, ACO3, ACO0)
        tela.ret(tx + 3, ty + 4, 10, 1, ACO0); tela.ret(tx + 3, ty + 18, 10, 1, ACO0)
        tela.ret(tx + 2, ty - 4, 3, 4, CERAMICA); tela.ret(tx + 11, ty - 4, 3, 4, CERAMICA)
    # cruzeta baixa (fios da rua)
    tela.ret(x - 12, topo + 62, 25, 3, PRETO); tela.ret(x - 11, topo + 63, 23, 1, ACO2)
    return topo


def lampada(tela, x, y, acesa, t=0.0, fio_ate=None):
    """Lâmpada pendurada (bulbo com contorno). `acesa` de 0 a 1."""
    if fio_ate is not None:
        tela.ret(x, fio_ate, 1, y - fio_ate - 6, PRETO)
    tela.ret(x - 3, y - 7, 7, 5, PRETO); tela.ret(x - 2, y - 6, 5, 3, ACO2)
    if acesa > .05:
        r = 14 + 20 * acesa + math.sin(t * 6) * 1.2
        halo(tela, x, y + 3, r, CHAMA0 if acesa > .5 else LATAO)
        halo(tela, x, y + 3, r * .55, AMARELO, fase=1)
    tela.disco(x, y + 3, 6, PRETO)
    tela.disco(x, y + 3, 5, CHAMA0 if acesa > .5 else (ACO3 if acesa < .05 else LATAO))
    if acesa > .5:
        tela.disco(x - 1, y + 2, 2.5, BRANCO)
    else:
        tela.disco(x - 2, y + 1, 1.5, ACO4)


def tomada(tela, x, y, s=1, t=0.0, viva=0.0):
    """Tomada genérica de 3 furos (placa, espelho sextavado, furos)."""
    w, h = 22 * s, 30 * s
    caixa(tela, x - w // 2, y - h // 2, w, h, CERAMICA, BRANCO, ACO3)
    r = 8 * s
    pts = [(x + math.cos(a) * r, y + math.sin(a) * r) for a in [k * math.pi / 3 + math.pi / 6 for k in range(6)]]
    poligono(tela, [(px, py) for px, py in pts], ACO3)
    poligono(tela, [(x + (px - x) * .85, y + (py - y) * .85) for px, py in pts], ACO4)
    for dx, dy in ((-3 * s, 1 * s), (3 * s, 1 * s), (0, -3 * s)):
        tela.disco(x + dx, y + dy, 1.1 * s, PRETO)
    if viva > 0:
        for dx, dy in ((-3 * s, 1 * s), (3 * s, 1 * s)):
            if int(t * 8) % 2: tela.px(x + dx, y + dy, AMARELO)


def interruptor(tela, x, y, ligado):
    caixa(tela, x - 4, y - 6, 9, 12, CERAMICA, BRANCO, ACO3)
    tela.ret(x - 1, y - 3 if ligado else y, 3, 3, ACO2)


def medidor(tela, x, y, t, ligado=True):
    caixa(tela, x, y, 16, 20, ACO1, ACO3, ACO0)
    tela.ret(x + 2, y + 3, 12, 5, PRETO)
    n = int(t * 3) % 1000 if ligado else 0
    tela.texto(f"{n:03d}", x + 8, y + 3, VERDE, tam=9, centro=True)
    tela.disco(x + 8, y + 14, 3, ACO3)
    a = t * 4 if ligado else 0
    tela.linha(x + 8, y + 14, x + 8 + math.cos(a) * 3, y + 14 + math.sin(a) * 3, PRETO)


# ================================================================ ícones das 9 etapas
def icone(tela, k, cx, cy, t, aceso=True):
    """Ícone 40x40 de cada etapa (resumo, gancho, título)."""
    c_fundo = FUNDO2 if aceso else FUNDO
    painel(tela, cx - 21, cy - 21, 42, 42, borda=ETAPAS[k][1] if aceso else ACO0, fundo=c_fundo, luz=FUNDO3)
    if not aceso:
        tela.texto(str(k + 1), cx, cy - 4, ACO1, tam=9, centro=True)
        return
    if k == 0:
        nuvem(tela, cx, cy - 8, 26, chuva=True)
        for j in range(5):
            x = cx - 10 + j * 5
            y = cy + 2 + ((t * 30 + j * 7) % 14)
            tela.linha(x, y, x - 1, y + 3, AGC)
    elif k == 1:
        agua(tela, cx - 19, cx - 1, cy - 8, cy + 19, t, onda=.6, brilho=False)
        poligono(tela, [(cx - 2, cy - 12), (cx + 3, cy - 12), (cx + 12, cy + 19), (cx - 2, cy + 19)], PRETO)
        poligono(tela, [(cx - 1, cy - 11), (cx + 3, cy - 11), (cx + 11, cy + 19), (cx - 1, cy + 19)], CONC1)
        tela.ret(cx - 1, cy - 11, 4, 1, CONC2)
        agua(tela, cx + 12, cx + 20, cy + 12, cy + 19, t, onda=.4, brilho=False)
    elif k == 2:
        tubo(tela, cx - 15, cy - 12, cx + 14, cy + 13, 8, t)
    elif k == 3:
        C = Caracol(cx, cy, 18, 12, 10.5, 9)
        tela.disco(cx, cy, 18, PRETO); tela.disco(cx, cy, 17, AGM)
        C.rotor(tela, t, t * 3)
    elif k == 4:
        gerador_mini(tela, cx, cy, t)
    elif k == 5:
        nucleo(tela, cx - 15, cy - 13, 30, 26, 8, t)
        bobina(tela, cx - 11, cy - 11, cy + 11, 10, 3, t, 0)
        bobina(tela, cx + 11, cy - 11, cy + 11, 10, 7, t, 0, esp=2)
    elif k == 6:
        torre(tela, cx, cy + 19, 36)
    elif k == 7:
        transformador_tanque(tela, cx - 12, cy + 17, 24, 16, t)
        tela.ret(cx - 19, cy + 17, 38, 2, CONC0)
    elif k == 8:
        poligono(tela, [(cx - 16, cy - 2), (cx, cy - 16), (cx + 16, cy - 2)], PRETO)
        poligono(tela, [(cx - 14, cy - 3), (cx, cy - 14), (cx + 14, cy - 3)], VERMELHO)
        caixa(tela, cx - 12, cy - 2, 24, 20, CERAMICA, BRANCO, ACO3)
        on = (int(t * 2) % 4) != 0
        tela.ret(cx - 4, cy + 2, 8, 8, PRETO); tela.ret(cx - 3, cy + 3, 6, 6, CHAMA0 if on else FUNDO3)


def gerador_mini(tela, cx, cy, t):
    tela.disco(cx, cy, 18, PRETO); tela.disco(cx, cy, 17, ACO1)
    for k in range(12):
        a = -math.pi / 2 + k * math.pi / 6
        tela.disco(cx + math.cos(a) * 14, cy + math.sin(a) * 14, 2, COBRE1)
    tela.disco(cx, cy, 11, PRETO)
    for k in range(6):
        a = t * 2 + k * math.pi / 3
        tela.disco(cx + math.cos(a) * 7, cy + math.sin(a) * 7, 3, VERMELHO if k % 2 == 0 else MISTURA)
    tela.disco(cx, cy, 3, ACO3)
