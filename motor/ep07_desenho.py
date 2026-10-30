#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep07 — o desenho: celular, chat, foto, pacote, cadeado,
chave, torre, ondas de rádio, fibra em corte, mapa, mar, data center e o
painel da viagem. Tudo genérico (nenhuma marca, nenhum logotipo).

A viagem tem um só modelo (`viagem_ms`): o contador de distância e o de tempo
leem a mesma função, com a luz a 300.000 km/s no ar e 200.000 km/s na fibra.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
import idioma as I
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)

# ================================================================ a viagem
ETAPAS = [('BITS', CIANO), ('CADEADO', AMARELO), ('PACOTES', LARANJA), ('RÁDIO', ROXO),
          ('FIBRA', MISTURA2), ('ROTEADORES', VERDE), ('OCEANO', MISTURA), ('SERVIDOR', ROSA),
          ('CHEGADA', CHAMA1)]

KM_RADIO1 = 1.0                       # celular -> antena (exemplo)
KM_FORTALEZA = 1.0 + 2360.0           # + São Paulo -> Fortaleza (IBGE, linha reta)
KM_SINES = KM_FORTALEZA + 5900.0      # + cabo submarino (EllaLink)
KM_LISBOA = KM_SINES + 88.0           # + Sines -> Lisboa (linha reta)
KM_TOTAL = KM_LISBOA + 1.0            # + antena -> celular


def viagem_ms(km):
    """Tempo de viagem (ms) depois de `km`: rádio a 300 km/ms, fibra a 200 km/ms."""
    km = max(0.0, km)
    r1 = min(km, KM_RADIO1)
    fib = max(0.0, min(km, KM_LISBOA) - KM_RADIO1)
    r2 = max(0.0, km - KM_LISBOA)
    return r1 / 300.0 + fib / 200.0 + r2 / 300.0


def fmt_km(km):
    if km <= 0: return '0 KM'
    if km < 10: return f"{I.decimal(km, 1)} KM"
    return f"{I.milhar(km)} KM"


def fmt_ms(ms):
    if ms <= 0: return '0 MS'
    if ms < 1: return f"{I.decimal(ms, 3)} MS"
    return f"{I.decimal(ms, 1)} MS"


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


def halo(tela, cx, cy, r, cor):
    """Brilho em xadrez em volta de algo luminoso (sem alfa: pixel sim, pixel não)."""
    x0, x1 = max(0, int(cx - r)), min(tela.w, int(cx + r + 1))
    y0, y1 = max(0, int(cy - r)), min(tela.h, int(cy + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & ((xx + yy) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def luz(tela, cx, cy, r, nucleo=BRANCO, cor=CIANO, halo_cor=None):
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


def tique(tela, x, y, cor):
    """Um tique (✓) de 7x5."""
    for (a, b), (c, d) in (((x, y + 2), (x + 2, y + 4)), ((x + 2, y + 4), (x + 6, y))):
        tela.linha(a, b, c, d, cor)
        tela.linha(a, b + 1, c, d + 1, cor)


def tiques(tela, x, y, n, cor):
    for k in range(n):
        tique(tela, x + k * 5, y, cor)


def relogio(tela, x, y, cor=ACO3):
    tela.anel(x + 3, y + 3, 3, cor, .5)
    tela.ret(x + 3, y + 1, 1, 3, cor); tela.ret(x + 3, y + 3, 2, 1, cor)


# ================================================================ cadeado e chave
def cadeado(tela, x, y, s=1, cor=AMARELO, aberto=0.0):
    """Cadeado com canto superior esquerdo em (x, y); s = escala (1 = 10x12)."""
    w, h = 10 * s, 7 * s
    ab = int(round(aberto * 4 * s))
    # alça
    cx = x + w / 2
    for esp, c in ((2.2 * s, PRETO), (1.2 * s, ACO3)):
        for a in np.linspace(0, math.pi, 10 + 6 * s):
            px_ = cx - math.cos(a) * 3.2 * s
            py_ = y + 5 * s - math.sin(a) * 4.2 * s - ab
            tela.disco(px_, py_, esp * .5 + .3, c)
        tela.ret(int(cx - 3.2 * s - esp * .5), int(y + 5 * s - ab), max(1, int(esp)), ab + 1, c)
        if aberto < .3:
            tela.ret(int(cx + 3.2 * s - esp * .5), int(y + 5 * s - ab), max(1, int(esp)), ab + 1, c)
    by = y + 5 * s
    caixa(tela, x, by, w, h, cor, luz_=CHAMA0 if cor == AMARELO else ACO4, sombra=OLEO1 if cor == AMARELO else ACO1)
    tela.ret(int(cx) - max(1, s // 2), by + 2 * s, max(2, s), 3 * s, PRETO)


def chave(tela, x, y, s=1, cor=AMARELO, ang=0.0):
    """Chave deitada, argola em (x, y)."""
    c, sn = math.cos(ang), math.sin(ang)
    def P(u, v): return x + u * c - v * sn, y + u * sn + v * c
    ax, ay = P(0, 0)
    tela.disco(ax, ay, 4.2 * s, PRETO); tela.disco(ax, ay, 3.2 * s, cor); tela.disco(ax, ay, 1.4 * s, PRETO)
    bx, by = P(16 * s, 0)
    linha_grossa(tela, ax, ay, bx, by, 3.4 * s, PRETO)
    linha_grossa(tela, ax, ay, bx, by, 1.8 * s, cor)
    for u in (11, 15):
        dx, dy = P(u * s, 0); ex, ey = P(u * s, 3.5 * s)
        linha_grossa(tela, dx, dy, ex, ey, 3 * s, PRETO)
        linha_grossa(tela, dx, dy, ex, ey, 1.4 * s, cor)


# ================================================================ a foto (praia ao pôr do sol)
def foto(tela, x, y, w, h, t=0.0):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    hc = int(h * .55)
    dither(tela, x, y, w, hc // 2, ROXO, CHAMA2)
    dither(tela, x, y + hc // 2, w, hc - hc // 2, CHAMA2, CHAMA1, 1)
    sx, sy = x + w * .62, y + hc - 1
    tela.disco(sx, sy, max(2, w * .14), CHAMA0)
    tela.ret(x, y + hc, w, h - hc, MISTURA)
    dither(tela, x, y + hc + 1, w, max(1, (h - hc) // 2), MISTURA, TRACO)
    for k in range(3):
        yy = y + hc + 1 + k * 2
        ww = max(2, int(w * .25) - k * 2)
        tela.ret(int(sx - ww / 2 + math.sin(t * 2 + k) * 1), yy, ww, 1, CHAMA0)
    ya = y + h - max(2, h // 5)
    tela.ret(x, ya, w, y + h - ya, LATAO)
    tela.ret(x, ya, w, 1, CHAMA0)


# ================================================================ celular e chat
def celular(tela, x, y, w, h, cor=ACO1):
    """Corpo do celular; devolve o retângulo da tela (sx, sy, sw, sh)."""
    tela.ret(x + 1, y - 1, w - 2, h + 2, PRETO); tela.ret(x - 1, y + 1, w + 2, h - 2, PRETO)
    tela.ret(x, y, w, h, cor)
    tela.ret(x + 1, y + 1, w - 2, 1, ACO3); tela.ret(x + 1, y + 1, 1, h - 2, ACO2)
    tela.ret(x + w - 2, y + 2, 1, h - 3, ACO0); tela.ret(x + 2, y + h - 2, w - 3, 1, ACO0)
    tela.ret(x + w, y + h // 4, 1, max(4, h // 8), ACO2)          # botão lateral
    m = max(3, w // 14)
    sx, sy, sw, sh = x + m, y + m + 4, w - 2 * m, h - 2 * m - 8
    tela.ret(sx - 1, sy - 1, sw + 2, sh + 2, PRETO)
    tela.ret(sx, sy, sw, sh, FUNDO)
    tela.ret(x + w // 2 - 4, y + m, 8, 1, PRETO)                  # alto-falante
    tela.px(x + w // 2 + 7, y + m, ACO0)
    tela.ret(x + w // 2 - 5, y + h - m - 2, 10, 1, ACO2)          # barra de baixo
    return sx, sy, sw, sh


def bolha(tela, x, y, w, h, cor=MISTURA, borda=PRETO, rabo=True):
    tela.ret(x + 1, y - 1, w - 2, h + 2, borda); tela.ret(x - 1, y + 1, w + 2, h - 2, borda)
    tela.ret(x, y, w, h, cor)
    tela.ret(x + 1, y, w - 2, 1, MISTURA2 if cor == MISTURA else ACO4)
    if rabo:
        tela.ret(x + w, y + h - 4, 2, 3, cor); tela.ret(x + w + 2, y + h - 2, 1, 1, cor)


def chat(tela, s, t, texto='OI!', foto_on=True, ticks=0, cor_tick=ACO3, digitando=None, apertar=0.0,
         enviada=True, nome='LISBOA', rel=False):
    """A conversa na tela do celular. `s` = retângulo da tela. `ticks` 0 = relógio."""
    sx, sy, sw, sh = s
    tela.ret(sx, sy, sw, 11, TRACO)                                   # barra do contato
    tela.disco(sx + 7, sy + 5, 3.5, ACO2); tela.disco(sx + 7, sy + 4, 1.5, ACO4)
    tela.ret(sx + 5, sy + 7, 5, 1, ACO4)
    tela.texto(nome, sx + 14, sy + 2, BRANCO, tam=9)
    dither(tela, sx, sy + 11, sw, sh - 23, FUNDO, FUNDO2)
    # campo de digitar + botão enviar
    yb = sy + sh - 12
    tela.ret(sx, yb, sw, 12, FUNDO2)
    tela.ret(sx + 2, yb + 2, sw - 16, 8, FUNDO3)
    if digitando:
        tela.texto(digitando, sx + 4, yb + 3, BRANCO, tam=9)
        if int(t * 3) % 2: tela.ret(sx + 5 + tela.largura_texto(digitando, 9), yb + 3, 1, 6, BRANCO)
    bx, by = sx + sw - 7, yb + 6
    rr = 4.5 + apertar * 1.5
    if apertar > 0: halo(tela, bx, by, 9, CIANO)
    tela.disco(bx, by, rr, PRETO); tela.disco(bx, by, rr - 1, VERDE if apertar <= 0 else CIANO)
    seta(tela, bx - 1, by, 1, 0, PRETO, 3); tela.ret(int(bx - 3), int(by), 3, 1, PRETO)
    if not enviada: return None
    # bolhas enviadas (direita)
    cur = sy + 15
    caixas = []
    if foto_on:
        fw = min(sw - 14, 60); fh = int(fw * .66)
        bx0 = sx + sw - fw - 9
        bolha(tela, bx0 - 2, cur, fw + 4, fh + 4, MISTURA, rabo=not texto)
        foto(tela, bx0, cur + 2, fw, fh, t)
        caixas.append((bx0 - 2, cur, fw + 4, fh + 4))
        cur += fh + 8
    if texto:
        tw = tela.largura_texto(texto, 9) + 22
        bx0 = sx + sw - tw - 5
        bolha(tela, bx0, cur, tw, 12, MISTURA)
        tela.texto(texto, bx0 + 3, cur + 3, BRANCO, tam=9)
        if ticks == 0: relogio(tela, bx0 + tw - 10, cur + 3, MISTURA2)
        else: tiques(tela, bx0 + tw - 14, cur + 4, ticks, cor_tick)
        caixas.append((bx0, cur, tw, 12))
        cur += 16
    return caixas


def chat_recebido(tela, s, t, mostra=1.0, nome='SÃO PAULO'):
    """A conversa do lado de quem recebe: bolhas à esquerda."""
    sx, sy, sw, sh = s
    tela.ret(sx, sy, sw, 11, TRACO)
    tela.disco(sx + 7, sy + 5, 3.5, ACO2); tela.disco(sx + 7, sy + 4, 1.5, ACO4)
    tela.ret(sx + 5, sy + 7, 5, 1, ACO4)
    tela.texto(nome, sx + 14, sy + 2, BRANCO, tam=9)
    dither(tela, sx, sy + 11, sw, sh - 11, FUNDO, FUNDO2)
    if mostra <= 0: return
    fw = min(sw - 16, 50); fh = int(fw * .66)
    cur = sy + 16
    hh = int((fh + 4) * min(1, mostra * 2))
    bolha(tela, sx + 5, cur, fw + 4, max(2, hh), FUNDO3, rabo=False)
    if mostra > .5: foto(tela, sx + 7, cur + 2, fw, fh, t)
    cur += fh + 9
    if mostra > .7:
        bolha(tela, sx + 5, cur, 24, 12, FUNDO3, rabo=False)
        tela.texto('OI!', sx + 9, cur + 3, BRANCO, tam=9)


# ================================================================ o pacote (protagonista)
def pacote(tela, x, y, n=1, t=0.0, s=1, trancado=True, cor=AMARELO, brilho=True, rotulo_n=True):
    """Pacote com canto superior esquerdo em (x, y): cabeçalho colorido à
    esquerda (com o número), dados trancados à direita. s=1: 24x14."""
    w, h = 24 * s, 14 * s
    if brilho: halo(tela, x + w / 2, y + h / 2, w * .75, cor if cor != AMARELO else CHAMA1)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, ACO1)
    dither(tela, x + 8 * s, y + 1, w - 8 * s - 1, h - 2, ACO1, ACO0, int(t * 6) % 2)
    tela.ret(x, y, w, 1, ACO3)
    tela.ret(x, y, 8 * s, h, cor)
    tela.ret(x, y, 8 * s, 1, CHAMA0 if cor == AMARELO else BRANCO)
    tela.ret(x + 8 * s, y, 1, h, PRETO)
    if rotulo_n:
        tt = str(n)
        tela.texto(tt, x + 4 * s, y + h // 2 - 3 * (1 if s < 2 else 2) + (0 if s < 2 else 1), PRETO,
                   tam=9 if s < 2 else 17, centro=True)
    if trancado:
        cadeado(tela, x + 12 * s, y + 1 * s, s, AMARELO)


def particulas_bits(tela, x, y, t, n=8, cor=CIANO, larg=30, sobe=20):
    for i in range(n):
        u = (t * .9 + i / n) % 1.0
        xx = x + ((i * 37) % larg) - larg / 2 + math.sin(u * 6 + i) * 2
        yy = y - u * sobe
        tela.texto('1' if (i * 7 + int(t * 3)) % 3 else '0', xx, yy, cor if u < .7 else TRACO, tam=9)


# ================================================================ torre e ondas
def torre(tela, x, yb, h, t, piscar=True, escala=1.0):
    """Torre treliçada com antenas no alto. (x, yb) = pé no chão, centro."""
    topo = yb - h
    lb = 12 * escala; lt = 3 * escala
    pts = []
    for lado in (-1, 1):
        linha_grossa(tela, x + lado * lb, yb, x + lado * lt, topo + 8, 3, PRETO)
    for lado in (-1, 1):
        linha_grossa(tela, x + lado * lb, yb, x + lado * lt, topo + 8, 1.4, ACO3)
    n = max(3, int(h / 14))
    for k in range(n):
        u0, u1 = k / n, (k + 1) / n
        ya, yb2 = yb - u0 * (h - 8), yb - u1 * (h - 8)
        wa, wb = lb + (lt - lb) * u0, lb + (lt - lb) * u1
        tela.linha(x - wa, ya, x + wb, yb2, ACO1)
        tela.linha(x + wa, ya, x - wb, yb2, ACO1)
        tela.ret(int(x - wb), int(yb2), int(2 * wb) + 1, 1, ACO2)
    # mastro e antenas (painéis)
    tela.ret(int(x - 1), int(topo - 6), 2, 16, PRETO); tela.ret(int(x), int(topo - 6), 1, 15, ACO3)
    for k, dx in enumerate((-8, 5)):
        ax = int(x + dx * escala); ay = int(topo)
        caixa(tela, ax, ay, int(4 * escala), int(13 * escala), CERAMICA, luz_=BRANCO, sombra=ACO2)
    caixa(tela, int(x - 2), int(topo + 1), 4, int(11 * escala), ACO4, luz_=BRANCO, sombra=ACO2)
    if piscar and int(t * 1.5) % 2 == 0:
        halo(tela, x, topo - 7, 5, VERMELHO)
        tela.disco(x, topo - 7, 1.6, VERMELHO); tela.px(x, topo - 8, ROSA)
    else:
        tela.disco(x, topo - 7, 1.2, BRASA)
    # gabinete no pé
    caixa(tela, int(x + lb + 3), int(yb - 14), 12, 14, ACO2, luz_=ACO4, sombra=ACO0)
    tela.px(int(x + lb + 6), int(yb - 10), VERDE if int(t * 3) % 2 else ACO1)
    return (x, topo + 6)


def ondas(tela, x0, y0, x1, y1, t, cor=ROXO, n=5, vel=.8, abertura=.55):
    """Frentes de onda (arcos) andando de (x0, y0) para (x1, y1)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    ang = math.atan2(dy, dx)
    for k in range(n):
        u = (t * vel + k / n) % 1.0
        r = 6 + u * (L - 6)
        c = cor if u < .75 else (MISTURA if cor == ROXO else TRACO)
        for a in np.linspace(-abertura, abertura, int(10 + r * abertura * 1.2)):
            px_ = x0 + math.cos(ang + a) * r
            py_ = y0 + math.sin(ang + a) * r
            tela.px(px_, py_, c)
            tela.px(px_ + math.cos(ang + a), py_ + math.sin(ang + a), PRETO)


# ================================================================ cidade (fundo da cena do rádio)
_CACHE = {}


def cidade(tela, t, chao=176, seed=7):
    key = ('cidade', chao, seed)
    if key not in _CACHE:
        T = PX.Tela(W, H, paleta=LG.PAL)
        T.buf[:] = FUNDO
        dither(T, 0, 0, W, 50, FUNDO, FUNDO2)
        dither(T, 0, 50, W, 60, FUNDO2, FUNDO3, 1)
        T.ret(0, 110, W, chao - 110, FUNDO3)
        rng = np.random.default_rng(seed)
        for k in range(30):                                  # estrelas
            T.px(int(rng.integers(0, W)), int(rng.integers(2, 60)), ACO2 if k % 3 else ACO4)
        x = -4
        while x < W:                                         # prédios do fundo
            w = int(rng.integers(14, 30)); h = int(rng.integers(30, 90))
            T.ret(x, chao - h, w, h, FUNDO2); T.ret(x, chao - h, w, 1, TRACO)
            for yy in range(chao - h + 4, chao - 4, 6):
                for xx in range(x + 3, x + w - 3, 5):
                    if rng.random() < .25: T.ret(xx, yy, 2, 2, GAS2)
            x += w + int(rng.integers(0, 4))
        x = -10
        while x < W:                                         # prédios da frente
            w = int(rng.integers(20, 40)); h = int(rng.integers(20, 60))
            T.ret(x - 1, chao - h - 1, w + 2, h + 1, PRETO)
            T.ret(x, chao - h, w, h, TRACO)
            T.ret(x, chao - h, w, 1, ACO0); T.ret(x, chao - h, 1, h, ACO0)
            for yy in range(chao - h + 4, chao - 3, 7):
                for xx in range(x + 3, x + w - 3, 6):
                    T.ret(xx, yy, 3, 3, LATAO if rng.random() < .35 else FUNDO2)
            x += w + int(rng.integers(6, 20))
        T.ret(0, chao, W, PALCO_H - chao, ACO0)
        dither(T, 0, chao + 2, W, PALCO_H - chao - 2, ACO0, FUNDO3)
        T.ret(0, chao, W, 1, ACO2)
        _CACHE[key] = T.buf[:PALCO_H].copy()
    tela.buf[:PALCO_H] = _CACHE[key]


# ================================================================ mapa
SA = [(-80, 12), (-75, 11), (-71.5, 12.3), (-68, 10.6), (-64, 10.6), (-61.5, 10.6), (-60, 8.5), (-58, 6.8),
      (-55, 5.9), (-52, 5), (-51, 4), (-50, 1.8), (-49.5, 0), (-48, -.8), (-46, -1), (-44.4, -2.4), (-42, -2.8),
      (-40, -2.8), (-38.5, -3.7), (-37, -4.8), (-35.3, -5.2), (-34.8, -7.2), (-35, -8.5), (-35.8, -9.7),
      (-37, -11), (-38.3, -12.8), (-39, -14.5), (-39, -17.5), (-39.7, -19.5), (-40.9, -21.8), (-42, -22.9),
      (-43.2, -23), (-44.6, -23.3), (-46.3, -24), (-47.9, -25.2), (-48.6, -26.5), (-48.7, -28.3), (-49.8, -29.5),
      (-50.6, -31), (-52, -32.3), (-53.5, -34), (-55, -35), (-58, -35), (-62, -39), (-80, -40)]
AF = [(25, 37.5), (12, 37.5), (10, 37.2), (8, 36.9), (3, 36.8), (-1, 35.6), (-2.2, 35.1), (-5.4, 35.9),
      (-6.3, 35.2), (-6.8, 34), (-8.5, 33.2), (-9.6, 30.4), (-10, 29), (-11.5, 28), (-13, 27.6), (-14.5, 26),
      (-16, 24), (-16.8, 22), (-17, 21), (-16.2, 19.5), (-16.5, 16.5), (-17.4, 14.7), (-16.8, 13.5),
      (-16.7, 12.3), (-15, 11), (-13.5, 9.5), (-13, 8.4), (-11.5, 7), (-10, 5.8), (-7.5, 4.4), (-5, 5.1),
      (-2, 4.8), (0, 5.6), (2, 6.3), (4.5, 6.3), (6, 4.3), (8.5, 4.5), (9.6, 3), (9.8, 1), (9.3, -1),
      (11, -3.9), (12, -5), (13, -8), (13.5, -12), (12, -17), (14, -22), (15, -27), (16.5, -29), (18, -33),
      (25, -34)]
IB = [(-9.3, 43.1), (-8.9, 42.1), (-8.7, 41), (-9, 40), (-9.4, 39.4), (-9.5, 38.75), (-9.1, 38.6), (-8.8, 38.4),
      (-8.9, 37.95), (-8.8, 37.4), (-8.95, 37), (-8, 37.05), (-7.4, 37.2), (-6.4, 36.8), (-6, 36.2), (-5.6, 36),
      (-4.4, 36.7), (-2.1, 36.7), (-.7, 37.6), (.2, 38.8), (-.3, 39.5), (.9, 41), (3.2, 41.9), (3.1, 42.5),
      (3, 43.3), (4.5, 43.4), (7, 43.7), (9, 44.4), (9, 50), (-2, 50), (-1.3, 44.5), (-1.4, 43.5), (-1.8, 43.4),
      (-4, 43.45), (-6, 43.6), (-8, 43.7)]
CIDADES = {'SÃO PAULO': (-46.63, -23.55), 'FORTALEZA': (-38.54, -3.72), 'SINES': (-8.87, 37.96),
           'LISBOA': (-9.14, 38.72)}


class Mapa:
    """Mapa equirretangular pré-desenhado: lon0/lat1 = canto de cima à esquerda."""

    def __init__(self, lon0, lat1, esc, x0, y0, w, h):
        self.lon0, self.lat1, self.esc, self.x0, self.y0, self.w, self.h = lon0, lat1, esc, x0, y0, w, h
        T = PX.Tela(W, H, paleta=LG.PAL)
        T.buf[:] = FUNDO
        dither(T, x0, y0, w, h, FUNDO, FUNDO2)
        g = 10 if esc < 5 else 5
        for lon in range(-180, 181, g):
            xx = int(self.px(lon, 0)[0])
            if x0 <= xx < x0 + w: T.ret(xx, y0, 1, h, FUNDO3)
        for lat in range(-90, 91, g):
            yy = int(self.px(0, lat)[1])
            if y0 <= yy < y0 + h: T.ret(x0, yy, w, 1, FUNDO3)
        for P in (SA, AF, IB):
            poligono(T, [self.px(a, b) for a, b in P], AGUA0)
        sub = T.buf[y0:y0 + h, x0:x0 + w]
        terra = sub == AGUA0
        yy, xx = np.mgrid[0:h, 0:w]
        sub[terra & ((xx + yy) % 4 == 0)] = TRACO
        sub[terra & ((xx // 2 + yy // 2) % 7 == 0) & ((xx + yy) % 2 == 0)] = AGUA1
        er = terra.copy()
        er[1:] &= terra[:-1]; er[:-1] &= terra[1:]; er[:, 1:] &= terra[:, :-1]; er[:, :-1] &= terra[:, 1:]
        sub[terra & ~er] = AGUA1
        di = terra.copy()
        di[1:] |= terra[:-1]; di[:-1] |= terra[1:]; di[:, 1:] |= terra[:, :-1]; di[:, :-1] |= terra[:, 1:]
        sub[di & ~terra] = PRETO
        self.img = sub.copy()

    def px(self, lon, lat):
        return self.x0 + (lon - self.lon0) * self.esc, self.y0 + (self.lat1 - lat) * self.esc

    def cid(self, nome): return self.px(*CIDADES[nome])

    def desenhar(self, tela):
        tela.buf[self.y0:self.y0 + self.h, self.x0:self.x0 + self.w] = self.img
        tela.ret_vazado(self.x0 - 1, self.y0 - 1, self.w + 2, self.h + 2, TRACO)

    def ponto(self, tela, nome, t, cor=BRANCO, rot=True, lado='d', dy=-4):
        x, y = self.cid(nome)
        tela.disco(x, y, 3, PRETO); tela.disco(x, y, 2, cor)
        if int(t * 2) % 2 == 0: tela.anel(x, y, 4.5, cor, .5)
        if rot:
            if lado == 'd': rotulo(tela, nome, x + 6, y + dy, cor)
            else: rotulo(tela, nome, x - 6, y + dy, cor, centro='d')


def rota_pts(mapa, nos):
    return [mapa.cid(n) if isinstance(n, str) else mapa.px(*n) for n in nos]


def trilha_luz(tela, pts, u, t, cor=AMARELO, esp=2, rastro=True):
    """Desenha a rota até a fração u (0..1 do comprimento total) e devolve a ponta."""
    segs = list(zip(pts, pts[1:]))
    Ls = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    tot = sum(Ls) or 1
    alvo = u * tot
    ponta = pts[0]
    for (a, b), L in zip(segs, Ls):
        if alvo <= 0: break
        f = min(1.0, alvo / L)
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        linha_grossa(tela, a[0], a[1], e[0], e[1], esp + 2, PRETO)
        linha_grossa(tela, a[0], a[1], e[0], e[1], esp, cor)
        ponta = e
        alvo -= L
    return ponta


def rota_tracejada(tela, pts, t, cor=ACO2):
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(L / 4)
        for k in range(n):
            if (k + int(t * 6)) % 2: continue
            u = k / max(1, n)
            tela.px(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, cor)


# ================================================================ painel da viagem
def painel_viagem(tela, k, km, t, estado=None, x0=302, cam_lenta=False, acende=None, tudo_feito=False):
    """Painel da direita: etapa, distância, tempo e o trilho das 9 etapas.
    k = índice da etapa (-1 = ainda não saiu). `estado` = (rótulo, valor, cor).
    `acende` = etapa que pisca no trilho (apresentação); `tudo_feito` = todas cumpridas."""
    tela.ret(x0 - 8, 0, W - x0 + 8, PALCO_H, FUNDO)
    tela.ret(x0 - 8, 0, 1, PALCO_H, TRACO)
    if tudo_feito:
        tela.texto("VIAGEM", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto("COMPLETA", x0, 26, VERDE, tam=17, contorno=PRETO)
    elif k >= 0:
        nome, cor = ETAPAS[k]
        tela.texto(f"ETAPA {k + 1} DE 9", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto(nome, x0, 26, cor, tam=17, contorno=PRETO)
    else:
        tela.texto("PRONTA", x0, 6, ACO3, tam=17, contorno=PRETO)
        tela.texto("PARA SAIR", x0, 26, BRANCO, tam=17, contorno=PRETO)
    tela.texto('DISTÂNCIA', x0, 50, ACO3, tam=9, contorno=PRETO)
    tela.texto(fmt_km(km), x0, 60, BRANCO if km > 0 else ACO2, tam=17, contorno=PRETO)
    tela.texto('TEMPO DE VIAGEM', x0, 84, ACO3, tam=9, contorno=PRETO)
    tela.texto(fmt_ms(viagem_ms(km)), x0, 94, AMARELO if km > 0 else ACO2, tam=17, contorno=PRETO)
    if cam_lenta:
        tela.texto('CÂMERA LENTA', x0 + 166, 84, CIANO if int(t * 2) % 2 else ACO3, tam=9, centro='d', contorno=PRETO)
    # barra SP -> LISBOA
    tela.ret(x0, 113, 166, 4, PRETO); tela.ret(x0 + 1, 114, 164, 2, FUNDO3)
    n = int(164 * min(1.0, km / KM_TOTAL))
    tela.ret(x0 + 1, 114, n, 2, AMARELO)
    if n > 0: tela.ret(x0 + n - 1, 112, 3, 6, BRANCO)
    if estado:
        rot, val, cv = estado
        tela.texto(rot, x0, 124, ACO3, tam=9, contorno=PRETO)
        tela.texto(val, x0, 134, cv, tam=17 if tela.largura_texto(val, 17) <= 166 else 9, contorno=PRETO)
    # trilho das etapas
    for j, (nm, cc) in enumerate(ETAPAS):
        bx = x0 + j * 18
        feito = j < k or tudo_feito or (acende is not None and j < acende)
        atual = (j == k and not tudo_feito) or j == acende
        tela.ret(bx, 162, 15, 15, PRETO)
        if atual:
            tela.ret(bx + 1, 163, 13, 13, cc)
            tela.ret(bx + 1, 163, 13, 1, BRANCO)
        else:
            tela.ret_vazado(bx + 1, 163, 13, 13, cc if feito else ACO0)
        tela.texto(str(j + 1), bx + 8, 166, PRETO if atual else (cc if feito else ACO1), tam=9, centro=True)
    if k >= 0:
        tela.texto('SÃO PAULO → LISBOA', x0, 186, ACO2, tam=9, contorno=PRETO)


# ================================================================ fibra em corte
def fibra_corte(tela, x0, x1, yc, t, bits='01001111', vel=40.0, raio_nucleo=7, intensidade=1.0, rotulos=True,
                destaque_reflexo=False):
    """Fibra deitada de x0 a x1 em corte: capa, casca, núcleo, e a luz em
    zigue-zague dentro do núcleo (pulsos = bits 1, intervalos = bits 0)."""
    rc, rk, rp = raio_nucleo, raio_nucleo + 9, raio_nucleo + 15
    w = x1 - x0
    tela.ret(x0, yc - rp - 1, w, 2 * rp + 3, PRETO)
    tela.ret(x0, yc - rp, w, 2 * rp + 1, ACO1)                             # capa
    tela.ret(x0, yc - rp, w, 2, ACO3); tela.ret(x0, yc + rp - 1, w, 2, ACO0)
    dither(tela, x0, yc - rk, w, 2 * rk + 1, FUNDO3, TRACO)                 # casca (vidro)
    tela.ret(x0, yc - rk, w, 1, MISTURA2); tela.ret(x0, yc + rk, w, 1, ACO2)
    dither(tela, x0, yc - rc, w, 2 * rc + 1, FUNDO2, FUNDO3, 1)             # núcleo
    tela.ret(x0, yc - rc, w, 1, AGUA1); tela.ret(x0, yc + rc, w, 1, AGUA1)
    # caminho em zigue-zague
    per = 4 * rc + 6
    def zy(x):
        f = ((x - x0) / per) % 1.0
        tri = 4 * f - 1 if f < .5 else 3 - 4 * f
        return yc + tri * (rc - 1)
    # pulsos andando
    bitlen = 14
    nb = len(bits)
    for x in range(int(x0), int(x1)):
        pos = (x - x0 - t * vel) / bitlen
        b = bits[int(math.floor(pos)) % nb]
        dentro = (pos % 1.0) < .78
        y = zy(x)
        if b == '1' and dentro:
            tela.px(x, y - 1, CIANO); tela.px(x, y + 1, CIANO)
            tela.px(x, y, BRANCO if intensidade > .5 else MISTURA2)
            if x % 2 == 0: tela.px(x, y - 2, MISTURA); tela.px(x, y + 2, MISTURA)
        else:
            tela.px(x, y, FUNDO3 if b == '1' else TRACO)
    # reflexos na parede
    for k in range(int(w / per) + 1):
        xr = x0 + k * per + per / 4
        if x0 < xr < x1:
            tela.px(xr, yc - rc, BRANCO if destaque_reflexo and int(t * 4) % 2 else MISTURA2)
            xr2 = xr + per / 2
            if xr2 < x1: tela.px(xr2, yc + rc, MISTURA2)
    return zy, (rc, rk, rp)


def laser(tela, x, yc, t, ligado=True):
    """Caixa do transmissor (laser) na ponta esquerda da fibra."""
    caixa(tela, x, yc - 16, 30, 32, ACO2, luz_=ACO4, sombra=ACO0)
    tela.ret(x + 3, yc - 12, 16, 2, ACO0); tela.ret(x + 3, yc - 8, 16, 2, ACO0)
    tela.ret(x + 30, yc - 4, 4, 9, PRETO); tela.ret(x + 30, yc - 3, 3, 7, ACO3)
    if ligado:
        halo(tela, x + 33, yc, 6, VERMELHO)
        tela.disco(x + 33, yc, 2, ROSA)
    tela.ret(x + 22, yc + 7, 4, 4, VERDE if ligado and int(t * 6) % 2 else ACO0)


# ================================================================ o mar
class Mar:
    """Corte lateral do Atlântico: superfície, água, fundo e o cabo."""
    Y_SUP, Y_CABO = 16, 168

    def __init__(self, seed=11):
        rng = np.random.default_rng(seed)
        T = PX.Tela(W, H, paleta=LG.PAL)
        T.buf[:] = FUNDO
        dither(T, 0, 0, W, self.Y_SUP, FUNDO2, FUNDO3)
        bandas = [(MISTURA, TRACO), (TRACO, FUNDO3), (FUNDO3, FUNDO2), (FUNDO2, FUNDO)]
        y = self.Y_SUP
        alturas = [14, 40, 50, 120]
        for (c1, c2), hh in zip(bandas, alturas):
            dither(T, 0, y, W, hh, c1, c2)
            T.ret(0, y, W, 2, c1)
            y += hh
        self.agua = T.buf[:PALCO_H].copy()
        # fundo (areia) num mapa largo, para rolar
        LW = 960
        self.LW = LW
        fundo = np.full((PALCO_H, LW), 255, np.uint8)
        alt = np.zeros(LW)
        for f, a, ph in ((7 / 960, 7, 0.3), (20 / 960, 3, 1.1), (50 / 960, 1.2, 2.0)):
            alt += a * np.sin(np.arange(LW) * 2 * math.pi * f + ph)
        self.alt = (self.Y_CABO + 4 - alt * .6).astype(int)
        for x in range(LW):
            y0 = self.alt[x]
            fundo[y0:, x] = LATAO
            fundo[y0 + 3:, x] = np.where((np.arange(y0 + 3, PALCO_H) + x) % 2 == 0, LATAO, OLEO0)
            fundo[y0 + 12:, x] = np.where((np.arange(y0 + 12, PALCO_H) + x) % 2 == 0, OLEO0, BRASA)
            fundo[y0, x] = CHAMA0 if x % 5 else LATAO
            fundo[max(0, y0 - 1), x] = PRETO
        for k in range(26):                                       # pedras
            x = int(rng.integers(0, LW - 10)); y0 = self.alt[x]
            for dx in range(int(rng.integers(4, 9))):
                fundo[y0 - 2:y0 + 1, (x + dx) % LW] = GAS2 if dx else PRETO
        self.fundo = fundo

    def desenhar(self, tela, t, desloc, peixes=True):
        tela.buf[:PALCO_H] = self.agua
        # superfície com ondas
        for x in range(0, W):
            y = self.Y_SUP + int(1.5 * math.sin(x * .09 + t * 2.0))
            tela.px(x, y, MISTURA2); tela.px(x, y - 1, PRETO)
        # raios de sol fracos
        for k in range(5):
            xx = int((k * 107 - desloc * .2) % (W + 60)) - 30
            for y in range(self.Y_SUP + 3, 90, 2):
                tela.px(xx + (y - self.Y_SUP) * .35, y, TRACO)
        # neve marinha
        for i in range(40):
            xx = (i * 53 - desloc * .5 - t * 3) % W
            yy = (i * 29 + t * 6) % (PALCO_H - 60) + 30
            tela.px(xx, yy, ACO1 if i % 3 else ACO2)
        if peixes:
            for k in range(4):                                   # cardumes
                bx = (k * 151 - desloc * .6 + t * 10) % (W + 80) - 40
                by = 46 + (k * 41) % 80 + math.sin(t * 1.2 + k) * 4
                for j in range(7):
                    peixe(tela, bx + (j % 4) * 9 + (j // 4) * 4, by + (j // 4) * 7 + (j % 2) * 2, 0,
                          AGUA1 if (k + j) % 3 else ACO3)
            for k in range(2):                                   # águas-vivas
                x = (k * 233 - desloc * .3) % (W + 40) - 20
                y = 70 + k * 40 + math.sin(t * 2 + k) * 6
                tela.disco(x, y, 5, PRETO); tela.disco(x, y, 4, ROXO); tela.ret(int(x) - 4, int(y), 9, 4, FUNDO2)
                tela.ret(int(x) - 3, int(y) - 3, 2, 1, ROSA)
                for j in range(3): tela.ret(int(x) - 3 + j * 3, int(y) + 1, 1, 6 + int(2 * math.sin(t * 3 + j)), ROXO)
        # um navio passando lá em cima
        xn = (W + 60) - ((desloc * .25 + t * 4) % (W + 140))
        tela.ret(int(xn), self.Y_SUP - 5, 34, 5, PRETO); tela.ret(int(xn) + 1, self.Y_SUP - 4, 32, 3, ACO1)
        tela.ret(int(xn) + 20, self.Y_SUP - 10, 9, 5, PRETO); tela.ret(int(xn) + 21, self.Y_SUP - 9, 7, 4, CERAMICA)
        # fundo rolando
        off = int(desloc) % self.LW
        cols = (np.arange(W) + off) % self.LW
        f = self.fundo[:, cols]
        m = f != 255
        tela.buf[:PALCO_H][m] = f[m]

    def chao(self, x, desloc):
        return self.alt[int(x + desloc) % self.LW]


def peixe(tela, x, y, lado, cor):
    d = 1 if lado else -1
    if not 0 <= y < 160: return
    tela.ret(int(x - 3), int(y - 1), 7, 3, PRETO)
    tela.ret(int(x - 2), int(y - 1), 5, 2, cor)
    tela.px(x - 4 * d, y - 1, cor); tela.px(x - 4 * d, y + 1, cor); tela.px(x - 4 * d, y, PRETO)
    tela.px(x + 2 * d, y - 1, BRANCO)


def cabo_submarino(tela, x0, x1, y_de_x, t, ponta_x=None, rep_passo=150, desloc=0.0):
    """Cabo apoiado no fundo, com repetidores; `ponta_x` = onde está o pulso de luz."""
    for x in range(int(x0), int(x1)):
        y = y_de_x(x)
        tela.ret(x, y - 3, 1, 6, PRETO)
        tela.ret(x, y - 2, 1, 4, ACO1)
        tela.px(x, y - 2, ACO3)
        tela.px(x, y + 1, ACO0)
    reps = []
    k0 = int((x0 + desloc) // rep_passo) - 1
    for k in range(k0, k0 + int((x1 - x0) / rep_passo) + 3):
        xr = k * rep_passo - desloc
        if x0 - 10 < xr < x1 + 10:
            y = y_de_x(min(max(int(xr), int(x0)), int(x1) - 1))
            caixa(tela, int(xr - 8), int(y - 5), 16, 10, ACO2, luz_=ACO4, sombra=ACO0)
            tela.ret(int(xr - 8), int(y - 1), 16, 2, ACO3)
            reps.append(xr)
    if ponta_x is not None:
        y = y_de_x(int(ponta_x))
        for k in range(30):
            xx = ponta_x - k
            if xx < x0: break
            tela.px(xx, y_de_x(int(xx)) - 1, CIANO if k < 18 else MISTURA)
        luz(tela, ponta_x, y - 1, 2.2, BRANCO, CIANO, MISTURA)
    return reps


def corte_cabo(tela, cx, cy, r, t):
    """O cabo submarino visto de frente: capa, camadas e as fibras no meio."""
    tela.disco(cx, cy, r + 1, PRETO)
    tela.disco(cx, cy, r, ACO0)
    tela.anel(cx, cy, r - 1, ACO1, .6)
    tela.disco(cx, cy, r * .72, ACO2)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        tela.disco(cx + math.cos(a) * r * .62, cy + math.sin(a) * r * .62, r * .09, ACO4)
    tela.disco(cx, cy, r * .45, LATAO)
    tela.disco(cx, cy, r * .36, OLEO0)
    halo(tela, cx, cy, r * .45, CIANO)
    for k in range(8):
        a = k / 8 * 2 * math.pi + t * .3
        x, y = cx + math.cos(a) * r * .18, cy + math.sin(a) * r * .18
        tela.disco(x, y, 1.5, CIANO if (k + int(t * 4)) % 3 else BRANCO)
    tela.disco(cx, cy, 1.2, MISTURA2)


# ================================================================ data center
def rack(tela, x, y, w, h, t, seed=0, destaque=False):
    caixa(tela, x, y, w, h, FUNDO3 if not destaque else TRACO, luz_=ACO1, sombra=FUNDO2)
    rng = np.random.default_rng(seed)
    n = (h - 6) // 9
    for k in range(n):
        yy = y + 3 + k * 9
        tela.ret(x + 2, yy, w - 4, 7, ACO0)
        tela.ret(x + 2, yy, w - 4, 1, ACO2)
        for j in range(3):
            ph = rng.uniform(0, 6); f = rng.uniform(1.5, 6)
            on = math.sin(t * f + ph) > -.2
            c = (VERDE, CIANO, AMARELO)[j] if on else FUNDO2
            tela.px(x + 4 + j * 3, yy + 3, c)
        for j in range(int((w - 20) / 3)):
            tela.px(x + 14 + j * 3, yy + 4, FUNDO2)


def datacenter(tela, t, destaque_x=None):
    key = 'dc_fundo'
    if key not in _CACHE:
        T = PX.Tela(W, H, paleta=LG.PAL)
        T.buf[:] = FUNDO
        dither(T, 0, 0, W, 30, FUNDO, FUNDO2)
        T.ret(0, 30, W, 150, FUNDO2)
        for x in range(0, W, 32): T.ret(x, 30, 1, 150, FUNDO3)
        T.ret(0, 180, W, PALCO_H - 180, ACO0)                 # piso elevado
        for x in range(0, W, 16):
            T.ret(x, 180, 1, PALCO_H - 180, FUNDO3)
        T.ret(0, 180, W, 1, ACO2)
        for x in range(0, W, 16):
            for y in range(184, PALCO_H, 8): T.ret(x + 7, y, 2, 1, FUNDO3)
        T.ret(0, 20, W, 4, PRETO); T.ret(0, 21, W, 2, ACO1)  # calha de cabos
        _CACHE[key] = T.buf[:PALCO_H].copy()
    tela.buf[:PALCO_H] = _CACHE[key]
    # cabos de fibra na calha, com luz correndo
    for k in range(3):
        y = 25 + k * 2
        for x in range(0, W, 2):
            on = ((x - t * 60 + k * 37) % 70) < 6
            tela.px(x, y, CIANO if on else (MISTURA if k == 1 else TRACO))


# ================================================================ cartão de etapa
def cartao(tela, t, k, x=150, vertical=False):
    """Cartão da etapa entrando pela esquerda (0..2 s)."""
    nome, cor = ETAPAS[k]
    if t >= 2.0: return
    u = ease(t / .4)
    s = f"{k + 1}. {nome}"
    larg = tela.largura_texto(s, 26 if not vertical else 17)
    xx = int(x - larg // 2 + (1 - u) * -300)
    painel(tela, xx - 8, 6, larg + 16, 34 if not vertical else 26, borda=cor)
    tela.texto(s, xx, 12, cor, tam=26 if not vertical else 17, contorno=PRETO)
