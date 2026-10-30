#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep23 — o desenho: céu de dia, sol, mar tropical, nuvem
branca, a protagonista (molécula que brilha / gota redonda que brilha, com
rastro e sem rosto), gotinhas, grão de sal, árvore da Amazônia em corte,
estômato, mapa da América do Sul, ícones das 9 etapas e o painel da jornada.

Reaproveita (só leitura) os miúdos do ep11 (`ep11_desenho`): rotulo, fio,
halo, caixa, grad_v, agua, nuvem, chuva, morro, interp, ao_longo, arvore.
A paleta do episódio é a do ep11 + cores próprias; ela é registrada como
'ep23' e o `longo` passa a usá-la neste processo.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
import ep11_desenho as E11                      # registra 'ep11' (só leitura)
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, BAYER8,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
from ep11_desenho import (CEU0, CEU1, CEU2, GRAMA0, GRAMA1, GRAMA2, TERRA0, TERRA1, CONC0, CONC1, CONC2,
                          AGP, AGM, AGC, ESPUMA, NUVEM0, NUVEM1,
                          rotulo, fio, halo, caixa, grad_v, agua, chuva, morro, interp, ao_longo, lerp)

# ================================================================ paleta
_EXTRA = ['#2f63ad', '#4a86d0', '#78b0e6', '#b4daf4',     # 52..55 céu de dia (alto -> horizonte)
          '#ffe27a', '#fff8d6',                           # 56..57 sol
          '#0f5d85', '#1f8cb0', '#4cc3d4',                # 58..60 mar tropical
          '#0c2615', '#164a22', '#26742f', '#4fa33a', '#9bd35a',  # 61..65 floresta
          '#3a2312', '#6a4322', '#9a6a3c',                # 66..68 tronco
          '#24160c', '#47301e', '#6b4a2e',                # 69..71 solo
          '#eef0f8', '#b9b2d8',                           # 72..73 sal
          '#7f8ead', '#c3cde0', '#f4f7fc',                # 74..76 nuvem de dia
          '#6b5038', '#a8865e', '#e9e2d6',                # 77..79 Andes (rocha, encosta, neve)
          '#8a9a4a', '#c0b860']                           # 80..81 cerrado (mapa)
PX.PALETAS['ep23'] = list(PX.PALETAS['ep11']) + _EXTRA
LG.PAL = 'ep23'
CEUD0, CEUD1, CEUD2, CEUD3 = 52, 53, 54, 55
SOL0, SOL1 = 56, 57
MAR0, MAR1, MAR2 = 58, 59, 60
FOL0, FOL1, FOL2, FOL3, FOL4 = 61, 62, 63, 64, 65
TRO0, TRO1, TRO2 = 66, 67, 68
SOLO0, SOLO1, SOLO2 = 69, 70, 71
SAL0, SAL1 = 72, 73
NUVD0, NUVD1, NUVD2 = 74, 75, 76
AND0, AND1, AND2 = 77, 78, 79
CER0, CER1 = 80, 81

# ================================================================ a jornada
ETAPAS = [('EVAPORAÇÃO', SOL0), ('SUBIDA', CEUD3), ('CONDENSAÇÃO', NUVD2), ('COLISÃO', AGC),
          ('QUEDA', CIANO), ('FLORESTA', FOL4), ('RIO VOADOR', ESPUMA), ('SUDESTE', CHAMA1),
          ('VOLTA AO MAR', MAR2)]
N_ETAPAS = len(ETAPAS)


def um(u): return min(1.0, max(0.0, u))


def fmt_num(v, casas=0):
    s = f"{v:,.{casas}f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_alt(m):
    return f"{fmt_num(max(0, round(m / 10) * 10))} M"


def fmt_temp(c):
    return f"{int(round(c))} °C"


def fmt_mm(mm):
    if mm < .1: return f"{fmt_num(mm, 2)} MM"
    if mm < 1: return f"{fmt_num(mm, 1)} MM"
    return f"{fmt_num(mm, 0 if abs(mm - round(mm)) < .05 else 1)} MM"


def fmt_dias(d):
    d = int(d)
    return '1 DIA' if d == 1 else f"{fmt_num(d)} DIAS"


# ================================================================ miúdos
def seta(tela, x, y, dirx, diry, cor, tam=5):
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if diry:
            tela.ret(x - w // 2, y + (k if diry > 0 else -k), w, 1, cor)
        else:
            tela.ret(x + (k if dirx > 0 else -k), y - w // 2, 1, w, cor)


def aura(tela, cx, cy, r0, r1, cor, fase=0):
    """Anel de brilho pontilhado (pixel sim, pixel não) entre os raios r0 e r1."""
    x0, x1 = max(0, int(cx - r1 - 1)), min(tela.w, int(cx + r1 + 2))
    y0, y1 = max(0, int(cy - r1 - 1)), min(min(tela.h, PALCO_H), int(cy + r1 + 2))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    m = (d2 <= r1 * r1) & (d2 > r0 * r0) & ((xx + yy + fase) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def mascara_gota(cx, cy, rx, ryt, ryb, x0, y0, x1, y1, covo=0.0):
    yy, xx = np.mgrid[y0:y1, x0:x1]
    dx = (xx + .5 - cx) / max(.5, rx)
    dy = yy + .5 - cy
    ry = np.where(dy < 0, max(.5, ryt), max(.5, ryb))
    m = dx * dx + (dy / ry) ** 2 <= 1.0
    if covo > 0:                                  # paraquedas: a base afunda no meio
        m &= ~((dy > ryb * (1 - covo * 1.6)) & (np.abs(dx) < .55))
    return m


def forma(tela, cx, cy, rx, ryt, ryb, cor, covo=0.0):
    x0, x1 = max(0, int(cx - rx - 2)), min(tela.w, int(cx + rx + 3))
    y0, y1 = max(0, int(cy - ryt - 2)), min(PALCO_H, int(cy + ryb + 3))
    if x1 <= x0 or y1 <= y0: return
    m = mascara_gota(cx, cy, rx, ryt, ryb, x0, y0, x1, y1, covo)
    tela.buf[y0:y1, x0:x1][m] = cor


def gota(tela, cx, cy, r, achata=0.0, covo=0.0, cor=AGC, meio=AGM, luz_=ESPUMA, contorno=PRETO):
    """Gota de chuva de verdade: redonda (achata=0) ou pão de hambúrguer
    (achata ~.5: base reta, cúpula em cima). Contorno, sombra e reflexo."""
    rx = r * (1 + .22 * achata)
    ryt = r * (1 - .12 * achata)
    ryb = r * (1 - .62 * achata)
    forma(tela, cx, cy, rx + 1, ryt + 1, ryb + 1, contorno, covo)
    forma(tela, cx, cy, rx, ryt, ryb, meio, covo)
    forma(tela, cx - rx * .12, cy - ryt * .14, rx * .8, ryt * .8, ryb * .55, cor, covo)
    if r >= 3:
        tela.disco(cx - rx * .42, cy - ryt * .45, max(.7, r * .22), luz_)
        tela.px(cx - rx * .5, cy - ryt * .55, BRANCO)
    else:
        tela.px(cx - 1, cy - 1, luz_)


def prota(tela, cx, cy, r, t, achata=0.0, covo=0.0):
    """A NOSSA gota: redonda, com aura amarela que pulsa e um brilho que gira."""
    p = 1 + .12 * math.sin(t * 6.0)
    aura(tela, cx, cy, r + 1.5, (r + 5) * p + 1, CHAMA0, int(t * 8) % 2)
    gota(tela, cx, cy, r, achata, covo)
    a = t * 3.0
    sx, sy = cx + math.cos(a) * (r + 3.5), cy + math.sin(a) * (r + 3.5)
    tela.px(sx, sy, BRANCO)
    tela.px(sx + 1, sy, AMARELO); tela.px(sx - 1, sy, AMARELO)
    tela.px(sx, sy + 1, AMARELO); tela.px(sx, sy - 1, AMARELO)


def vapor_prota(tela, cx, cy, t, r=2.6):
    """A nossa molécula como vapor: ponto de luz com aura (sem rosto)."""
    p = 1 + .2 * math.sin(t * 7.0)
    aura(tela, cx, cy, r + .5, (r + 5.5) * p, CHAMA0, int(t * 8) % 2)
    aura(tela, cx, cy, r + .5, r + 2.5, AMARELO, int(t * 8 + 1) % 2)
    tela.disco(cx, cy, r + 1, PRETO)
    tela.disco(cx, cy, r, CIANO)
    tela.disco(cx - .4, cy - .4, max(.6, r * .5), BRANCO)


def rastro(tela, fn, t, n=10, dt=.07, r0=2.0, cor=AMARELO, cor2=CHAMA1):
    """Rastro de pontos atrás da protagonista: fn(t) -> (x, y) ou None."""
    for k in range(n, 0, -1):
        p = fn(t - k * dt)
        if p is None: continue
        x, y = p
        rr = r0 * (1 - k / (n + 1))
        if k > n * .6:
            if (k + int(t * 20)) % 2: tela.px(x, y, cor2)
        elif rr >= 1.0:
            tela.disco(x, y, rr, cor if k < n * .3 else cor2)
        else:
            tela.px(x, y, cor)


def gotinha(tela, cx, cy, r, cor=NUVD2, sombra=NUVD0):
    """Gotinha de nuvem (figurante)."""
    if r < 1.2:
        tela.px(cx, cy, cor); return
    tela.disco(cx, cy, r + 1, PRETO)
    tela.disco(cx, cy, r, sombra)
    tela.disco(cx - r * .2, cy - r * .2, r * .7, cor)


def molecula(tela, cx, cy, ang, s=1.0, cor=AGC, prota_=False, t=0.0):
    """H2O: um O grande e dois H a 104,5° (desenho)."""
    if prota_:
        aura(tela, cx, cy, 4 * s, 9 * s * (1 + .12 * math.sin(t * 6)), CHAMA0, int(t * 8) % 2)
    a1, a2 = ang - .91, ang + .91
    for a in (a1, a2):
        hx, hy = cx + math.cos(a) * 3.6 * s, cy + math.sin(a) * 3.6 * s
        tela.disco(hx, hy, 1.7 * s + .8, PRETO)
    tela.disco(cx, cy, 2.8 * s + 1, PRETO)
    tela.disco(cx, cy, 2.8 * s, CIANO if prota_ else cor)
    tela.px(cx - s, cy - s, BRANCO)
    for a in (a1, a2):
        hx, hy = cx + math.cos(a) * 3.6 * s, cy + math.sin(a) * 3.6 * s
        tela.disco(hx, hy, 1.7 * s, BRANCO if prota_ else ACO4)


def sal(tela, cx, cy, s=6, t=0.0):
    """Grão de sal: cubinho em perspectiva, com brilho."""
    a = s
    topo = [(cx - a, cy - a * .4), (cx, cy - a * .9), (cx + a, cy - a * .4), (cx, cy + a * .1)]
    esq = [(cx - a, cy - a * .4), (cx, cy + a * .1), (cx, cy + a * 1.0), (cx - a, cy + a * .5)]
    dir_ = [(cx + a, cy - a * .4), (cx, cy + a * .1), (cx, cy + a * 1.0), (cx + a, cy + a * .5)]
    poligono(tela, [(x + (1 if x > cx else -1 if x < cx else 0), y + (1 if y > cy else -1)) for x, y in
                    [(cx - a, cy - a * .4), (cx, cy - a * .9), (cx + a, cy - a * .4), (cx + a, cy + a * .5),
                     (cx, cy + a * 1.0), (cx - a, cy + a * .5)]], PRETO)
    poligono(tela, topo, SAL0)
    poligono(tela, esq, SAL1)
    poligono(tela, dir_, ACO3)
    if int(t * 2) % 3 == 0: tela.px(cx - a * .3, cy - a * .5, BRANCO)


# ================================================================ céu, sol, mar, nuvem
def ceu_dia(tela, y1=PALCO_H, x0=0, x1=W, cores=(CEUD0, CEUD1, CEUD2, CEUD3)):
    grad_v(tela, x0, 0, x1 - x0, y1, list(cores))


def sol(tela, cx, cy, r, t):
    for k in range(12):
        a = k * math.pi / 6 + t * .25
        L = r + 6 + 3 * math.sin(t * 2 + k)
        tela.linha(cx + math.cos(a) * (r + 3), cy + math.sin(a) * (r + 3),
                   cx + math.cos(a) * L, cy + math.sin(a) * L, SOL0 if k % 2 else SOL1)
    aura(tela, cx, cy, r, r + 4, SOL1, int(t * 4) % 2)
    tela.disco(cx, cy, r, SOL0)
    tela.disco(cx - r * .2, cy - r * .2, r * .7, SOL1)


def mar(tela, x0, x1, ytop, t, ybot=PALCO_H, onda=1.0):
    return agua(tela, x0, x1, ytop, ybot, t, cores=(MAR2, MAR1, MAR1, MAR0, AGP), onda=onda, vel=1.8)


def nuvem_dia(tela, cx, cy, w, carregada=False):
    if carregada:
        E11.nuvem(tela, cx, cy, w, cor=NUVD0, escura=NUVEM1, luz_=NUVD1)
    else:
        E11.nuvem(tela, cx, cy, w, cor=NUVD1, escura=NUVD0, luz_=NUVD2)


def vento(tela, x0, y, L, t, cor=CEUD3, vel=40.0, dirx=-1):
    """Rajada: tracinho que corre com um gancho no fim."""
    u = (t * vel) % (L + 30)
    xa = x0 + dirx * (u - 30)
    for k in range(18):
        x = xa + dirx * k
        if (dirx < 0 and x0 - L <= x <= x0) or (dirx > 0 and x0 <= x <= x0 + L):
            tela.px(x, y + math.sin((x + t * 30) * .12) * 1.2, cor)


def copa(tela, x0, x1, ybase, t, seed=0, alt=18):
    """Fileira de copas de floresta tropical (bolotas sobrepostas, dither)."""
    grad_v(tela, x0, ybase - alt * .3, x1 - x0, PALCO_H - (ybase - alt * .3), [FOL1, FOL0, FOL0])
    k = 0
    x = x0
    while x < x1 + 10:
        r = 7 + ((k * 37 + seed * 11) % 7)
        h = ybase - alt * .3 - ((k * 53 + seed) % 9)
        sway = math.sin(t * 1.3 + k) * .6
        tela.disco(x + sway, h, r + 1, PRETO)
        tela.disco(x + sway, h, r, FOL1)
        tela.disco(x + sway - r * .25, h - r * .3, r * .7, FOL2)
        tela.disco(x + sway - r * .4, h - r * .5, r * .35, FOL3)
        x += r + 3 + (k % 3)
        k += 1


# ================================================================ painel da jornada
def painel_gota(tela, k, t, alt=None, temp=None, tam=None, dias=None, linhas=None, x0=302, cab=None,
                tudo=False, rodape=None):
    """Painel da direita. k = etapa (0..8). As 4 linhas padrão: altitude,
    temperatura, tamanho da gota, dias de viagem. `linhas` troca por outra
    lista [(rótulo, valor, cor)]."""
    tela.ret(x0 - 8, 0, W - x0 + 8, PALCO_H, FUNDO)
    tela.ret(x0 - 8, 0, 1, PALCO_H, TRACO)
    if cab:
        tela.texto(cab[0], x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(cab[1], x0, 26, cab[2], tam=17, contorno=PRETO)
    elif tudo:
        tela.texto('JORNADA', x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto('COMPLETA', x0, 26, VERDE, tam=17, contorno=PRETO)
    else:
        nome, cor = ETAPAS[k]
        tela.texto(f"ETAPA {k + 1} DE {N_ETAPAS}", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(nome, x0, 26, cor, tam=17, contorno=PRETO)
    if linhas is None:
        linhas = [('ALTITUDE', alt, CEUD3), ('TEMPERATURA', temp, CHAMA1),
                  ('TAMANHO DA GOTA', tam, AGC), ('DIAS DE VIAGEM', dias, AMARELO)]
    for j, (rot, val, cv) in enumerate(linhas[:4]):
        y = 48 + j * 29
        tela.texto(rot, x0, y, ACO3, tam=9, contorno=PRETO)
        if val is None: val, cv = '--', ACO1
        tamv = 17 if tela.largura_texto(val, 17) <= 166 else 9
        tela.texto(val, x0, y + 10 + (3 if tamv == 9 else 0), cv, tam=tamv, contorno=PRETO)
    for j, (nm, cc) in enumerate(ETAPAS):
        bx = x0 + j * 18
        feito = j < k or tudo
        atual = j == k and not tudo
        tela.ret(bx, 166, 15, 15, PRETO)
        if atual:
            tela.ret(bx + 1, 167, 13, 13, cc)
            tela.ret(bx + 1, 167, 13, 1, BRANCO)
        else:
            tela.ret_vazado(bx + 1, 167, 13, 13, cc if feito else ACO0)
        tela.texto(str(j + 1), bx + 8, 170, PRETO if atual else (cc if feito else ACO1), tam=9, centro=True)
    tela.texto(rodape or 'DO MAR → AO MAR', x0, 190, ACO2, tam=9, contorno=PRETO)


def selo_vertical(tela, k, cx, txt=None):
    s = txt or f"ETAPA {k + 1} DE {N_ETAPAS}: {ETAPAS[k][0]}"
    w = tela.largura_texto(s, 9) + 10
    cor = ETAPAS[k][1] if txt is None else AMARELO
    painel(tela, cx - w // 2, 1, w, 13, borda=cor)
    tela.texto(s, cx, 4, cor, tam=9, centro=True)


def lupa(tela, cx, cy, r, alvo=None, cor=ACO3):
    """Moldura da lupa (o miolo é a cena desenhada antes, recortada no círculo)."""
    if alvo:
        ax, ay = alvo
        tela.linha(ax, ay, cx + (ax - cx) * r / max(1, math.hypot(ax - cx, ay - cy)),
                   cy + (ay - cy) * r / max(1, math.hypot(ax - cx, ay - cy)), cor)
        tela.anel(ax, ay, 3, cor)
    tela.anel(cx, cy, r + 1.5, PRETO, 1.6)
    tela.anel(cx, cy, r, cor, .8)
    tela.anel(cx, cy, r + 3, ACO1, .6)


def recortar_disco(tela, cx, cy, r, fundo_buf):
    """Mantém o desenho atual só dentro do disco; fora volta o `fundo_buf`."""
    yy, xx = np.mgrid[0:PALCO_H, 0:W]
    fora = (xx - cx) ** 2 + (yy - cy) ** 2 > r * r
    tela.buf[:PALCO_H][fora] = fundo_buf[fora]


def termometro(tela, x, y, h, frac, cor=VERMELHO):
    caixa(tela, x, y, 5, h, FUNDO2)
    n = int(round((h - 2) * um(frac)))
    tela.ret(x + 1, y + h - 1 - n, 3, n, cor)
    tela.disco(x + 2, y + h + 3, 4, PRETO)
    tela.disco(x + 2, y + h + 3, 3, cor)
    tela.px(x + 1, y + h + 2, BRANCO)
    for k in range(0, h, 6): tela.px(x + 6, y + k, ACO2)


# ================================================================ árvore da Amazônia em corte
def arvore_grande(tela, cx, yb, t, h=150, xilema=0.0, fluxo=0.0):
    """Árvore grande: raízes, tronco com casca e um canal de xilema, copa
    larga. `xilema` 0..1 mostra o canal em corte; `fluxo` anima a água."""
    # raízes (no solo)
    for k, (dx, dy) in enumerate(((-34, 18), (-20, 30), (-6, 36), (10, 34), (24, 26), (38, 16))):
        linha_grossa(tela, cx, yb, cx + dx, yb + dy, 4, PRETO)
        linha_grossa(tela, cx, yb, cx + dx, yb + dy, 2.4, TRO1)
        linha_grossa(tela, cx + dx * .6, yb + dy * .6, cx + dx * 1.15, yb + dy * 1.1, 1.6, TRO1)
    # tronco
    top = yb - h
    tw = 14
    poligono(tela, [(cx - tw / 2 - 3, yb + 1), (cx - tw / 2 + 1, top), (cx + tw / 2 - 1, top), (cx + tw / 2 + 3, yb + 1)], PRETO)
    poligono(tela, [(cx - tw / 2 - 2, yb), (cx - tw / 2 + 2, top), (cx + tw / 2 - 2, top), (cx + tw / 2 + 2, yb)], TRO1)
    for y in range(int(top), int(yb), 2):
        u = (y - top) / max(1, yb - top)
        hw = tw / 2 - 2 + 4 * u
        tela.px(cx - hw, y, TRO2)
        tela.px(cx + hw - 1, y, TRO0)
        if (y * 7) % 11 == 0: tela.px(cx - hw * .3, y, TRO0)
    if xilema > 0:
        xw = 2
        tela.ret(cx - xw, top, xw * 2, yb - top, PRETO)
        tela.ret(cx - xw + 1, top, xw * 2 - 2, yb - top, AGM)
        if fluxo > 0:
            for k in range(int((yb - top) / 6)):
                y = yb - ((k * 6 + t * 40) % (yb - top))
                tela.px(cx, y, ESPUMA if k % 2 else AGC)
    # galhos e copa
    for dx, dy in ((-40, -18), (36, -22), (-14, -34), (18, -38)):
        linha_grossa(tela, cx, top + 6, cx + dx, top + dy, 4, PRETO)
        linha_grossa(tela, cx, top + 6, cx + dx, top + dy, 2.5, TRO1)
    bolas = [(-48, -18, 17), (-24, -27, 20), (4, -33, 22), (30, -26, 19), (52, -17, 16), (-6, -15, 18), (22, -12, 15)]
    for dx, dy, r in bolas:
        tela.disco(cx + dx, top + dy, r + 1, PRETO)
    for dx, dy, r in bolas:
        sw = math.sin(t * 1.1 + dx) * .6
        tela.disco(cx + dx + sw, top + dy, r, FOL1)
    for dx, dy, r in bolas:
        sw = math.sin(t * 1.1 + dx) * .6
        tela.disco(cx + dx + sw - r * .2, top + dy - r * .25, r * .72, FOL2)
        tela.disco(cx + dx + sw - r * .35, top + dy - r * .45, r * .36, FOL3)
        tela.px(cx + dx + sw - r * .45, top + dy - r * .6, FOL4)
    return top


def folha_corte(tela, x0, y0, w, h, t, abre):
    """Corte de uma folha visto de perto: epiderme de cima, miolo verde,
    epiderme de baixo com um estômato (duas células-guarda) que abre."""
    caixa(tela, x0, y0, w, h, FOL2, FOL3, FOL1)
    tela.ret(x0, y0, w, 4, FOL3)
    tela.ret(x0, y0 + h - 4, w, 4, FOL3)
    for k in range(w // 8):
        tela.ret_vazado(x0 + k * 8, y0, 8, 4, FOL1)
        tela.ret_vazado(x0 + k * 8, y0 + h - 4, 8, 4, FOL1)
    for k in range(9):
        cx = x0 + 8 + (k * 17) % max(1, w - 14)
        cy = y0 + 8 + (k * 7) % max(1, h - 18)
        tela.disco(cx, cy, 4, FOL1); tela.disco(cx - 1, cy - 1, 3, FOL3)
        tela.px(cx - 1, cy - 1, FOL4)
    sx, sy = x0 + w // 2, y0 + h - 2
    g = 1 + 4 * um(abre)
    for s in (-1, 1):
        tela.disco(sx + s * (g + 3), sy, 4, PRETO)
        tela.disco(sx + s * (g + 3), sy, 3, FOL4)
        tela.px(sx + s * (g + 3) - 1, sy - 1, BRANCO)
    tela.ret(sx - g + 1, sy - 3, max(0, int(2 * g - 2)), 7, FOL0)
    return sx, sy


# ================================================================ mapa da América do Sul
CONTORNO = [(-77.5, 8), (-75, 10.8), (-71.5, 12.4), (-68, 10.5), (-64, 10.7), (-61.5, 10.5), (-60, 8.5),
            (-57, 6), (-54, 5.8), (-51.5, 4.2), (-50, 1.8), (-49.5, 0), (-48, -1), (-44.5, -2.5), (-41, -3),
            (-38.5, -3.7), (-35.2, -5.5), (-34.8, -7.5), (-35.5, -9.5), (-37, -11), (-38.8, -13), (-39, -17.5),
            (-40, -20), (-41, -22), (-43, -23), (-45, -23.8), (-48, -25.5), (-48.6, -28), (-50, -30),
            (-52, -32.5), (-53.5, -34), (-55, -34.9), (-57, -34.5), (-58.5, -34), (-57.5, -36), (-57.6, -38.5),
            (-62, -39.5), (-73.5, -39.5), (-73.5, -38), (-73.6, -36), (-72, -33), (-71.5, -30), (-71.3, -25),
            (-70.4, -20), (-70.3, -18.3), (-71.5, -17), (-75, -15.3), (-76.3, -13.5), (-77.8, -10), (-79.5, -7),
            (-81.2, -5), (-80.3, -3), (-80.8, -1), (-80, .8), (-79, 1.8), (-78.5, 3.5), (-77.3, 4), (-77.5, 6.5)]
ANDES = [(-73.5, 9), (-75.8, 5), (-77.6, 1), (-78.6, -2), (-79, -6), (-77, -10), (-74, -14), (-70.5, -17),
         (-68.6, -21), (-68.8, -26), (-69.6, -31), (-70.4, -36), (-71, -39)]
AMAZONIA = [(-74, -1), (-70, 2), (-64, 3), (-58, 3), (-52, 1.5), (-49, -1.5), (-48.5, -5), (-51, -9), (-56, -11),
            (-62, -12.5), (-67, -11.5), (-72, -9), (-75, -5)]


class Mapa:
    """Projeção simples lon/lat -> pixel."""

    def __init__(self, x0=20, y0=2, s=4.2, lon0=-84, lat0=12.5):
        self.x0, self.y0, self.s, self.lon0, self.lat0 = x0, y0, s, lon0, lat0

    def p(self, lon, lat):
        return self.x0 + (lon - self.lon0) * self.s, self.y0 + (self.lat0 - lat) * self.s

    def desenhar(self, tela, t, x1=292):
        grad_v(tela, 0, 0, x1, PALCO_H, [MAR1, MAR0, MAR0, AGP])
        for k in range(26):                                   # brilho no mar
            x = (k * 61 + int(t * 6)) % x1
            y = (k * 37) % PALCO_H
            tela.ret(x, y, 3, 1, MAR1)
        pts = [self.p(lo, la) for lo, la in CONTORNO]
        poligono(tela, [(x + 1, y + 1) for x, y in pts], PRETO)
        poligono(tela, [(x - 1, y) for x, y in pts], PRETO)
        poligono(tela, pts, CER0)
        # cerrado em xadrez + Amazônia densa
        sent = 254
        bk = tela.buf.copy()
        poligono(tela, pts, sent)
        terra = tela.buf == sent
        tela.buf[:] = bk
        yy, xx = np.mgrid[0:tela.h, 0:tela.w]
        tela.buf[terra & ((xx + yy) % 2 == 0)] = GRAMA1
        bk = tela.buf.copy()
        poligono(tela, [self.p(lo, la) for lo, la in AMAZONIA], sent)
        am = (tela.buf == sent) & terra
        tela.buf[:] = bk
        b = BAYER8[yy % 8, xx % 8]
        tela.buf[am] = np.where(b[am] > .5, FOL2, FOL1)
        tela.buf[am & ((xx * 3 + yy * 5) % 13 == 0)] = FOL3
        # Andes: crista marrom com neve
        cr = [self.p(lo, la) for lo, la in ANDES]
        for (ax, ay), (bx, by) in zip(cr, cr[1:]):
            linha_grossa(tela, ax, ay, bx, by, 7, PRETO)
        for (ax, ay), (bx, by) in zip(cr, cr[1:]):
            linha_grossa(tela, ax, ay, bx, by, 5, AND0)
        for (ax, ay), (bx, by) in zip(cr, cr[1:]):
            linha_grossa(tela, ax - .8, ay, bx - .8, by, 2, AND1)
        for k, (x, y) in enumerate(cr):
            tela.px(x - 1, y, AND2); tela.px(x, y - 1, AND2)
        # contorno da costa
        for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
            tela.linha(ax, ay, bx, by, PRETO)
        # rio Amazonas
        rio = [self.p(lo, la) for lo, la in ((-73, -4), (-69, -3.5), (-65, -3.4), (-60, -3.1), (-56, -2.5), (-52, -1.6), (-50, -.6))]
        for (ax, ay), (bx, by) in zip(rio, rio[1:]):
            tela.linha(ax, ay, bx, by, AGC)
            tela.linha(ax, ay + 1, bx, by + 1, AGM)
        return pts


# ================================================================ ícones das 9 etapas
def icone(tela, k, cx, cy, t, aceso=True):
    """Ícone 32x32 de cada etapa (gancho, resumo)."""
    cor = ETAPAS[k][1]
    painel(tela, cx - 17, cy - 17, 34, 34, borda=cor if aceso else ACO0, fundo=FUNDO2 if aceso else FUNDO, luz=FUNDO3)
    if not aceso:
        tela.texto(str(k + 1), cx, cy - 4, ACO1, tam=9, centro=True)
        return
    if k == 0:
        sol(tela, cx - 5, cy - 7, 4, t)
        mar(tela, cx - 14, cx + 15, cy + 5, t, ybot=cy + 15, onda=.5)
        y = cy + 3 - (t * 8) % 12
        tela.px(cx + 6, y, ESPUMA); tela.px(cx + 9, y + 5, ESPUMA)
    elif k == 1:
        for j in range(3):
            y = cy + 10 - ((t * 10 + j * 7) % 22)
            seta(tela, cx - 6 + j * 6, int(y), 0, -1, CEUD3, 3)
        termometro(tela, cx + 8, cy - 12, 16, .3 + .2 * math.sin(t))
    elif k == 2:
        sal(tela, cx, cy, 4, t)
        aura(tela, cx, cy + 1, 6, 9, ESPUMA, int(t * 4) % 2)
    elif k == 3:
        d = 6 * (1 - (t * .6) % 1.0)
        gotinha(tela, cx - 3 - d, cy, 3, AGC, AGM); gotinha(tela, cx + 3 + d, cy, 3, AGC, AGM)
        if d < 1: gota(tela, cx, cy, 5)
    elif k == 4:
        y = cy - 10 + (t * 16) % 22
        gota(tela, cx, y, 4, .3)
        tela.linha(cx, y - 7, cx, y - 12, ACO2)
    elif k == 5:
        tela.ret(cx - 1, cy, 3, 14, TRO1)
        tela.disco(cx, cy - 4, 11, PRETO); tela.disco(cx, cy - 4, 10, FOL2); tela.disco(cx - 3, cy - 7, 5, FOL3)
    elif k == 6:
        for j in range(3):
            y = cy - 8 + j * 8
            for i in range(26):
                x = cx - 13 + i
                tela.px(x, y + math.sin(i * .4 + t * 4 + j) * 2, ESPUMA if (i + int(t * 10)) % 6 < 4 else AGC)
    elif k == 7:
        nuvem_dia(tela, cx, cy - 8, 22, True)
        for j in range(4):
            x = cx - 8 + j * 5; y = cy + 2 + ((t * 24 + j * 5) % 12)
            tela.linha(x, y, x, y + 2, AGC)
    elif k == 8:
        mar(tela, cx - 15, cx + 16, cy - 2, t, ybot=cy + 16, onda=1.0)
        tela.disco(cx - 6, cy - 9, 3, PRETO); tela.disco(cx - 6, cy - 9, 2, AGC)
