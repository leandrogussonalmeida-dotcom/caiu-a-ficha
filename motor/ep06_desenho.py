#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep06 — o desenho: mar, tanque de vidro, o navio e os medidores.

A água é sempre desenhada POR CIMA do que está dentro dela, em xadrez (metade
dos pixels vira água): o casco submerso aparece "visto através da água", e a
linha d'água fica onde a física manda.

  água salgada (mar)  azul      MISTURA / FUNDO3
  água doce (rio, tanque)  verde-água  AGUA1 / AGUA0

O navio é genérico: casco escuro com fundo vermelho, casario na popa,
contêineres de cores lisas, sem nome nem logotipo. Coordenadas do navio:
u = 0 (popa) .. L (proa), v = altura acima da quilha; na tela x = x0 + u,
y = yq - v. O calado em pixels é 2 px por metro (16 m = 32 px).
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
import idioma as I

PX_M = 2.0                    # pixels por metro de calado (navio)
PX_CM = 4.6                   # pixels por centímetro (tanque)
RHO_ACO, RHO_MAR, RHO_DOCE = 7.85, 1.025, 1.0


# ================================================================ pequenos
def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com bolinha na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.disco(x1, y1, 1.6, PRETO)
    tela.disco(x1, y1, 1.0, cor)


def seta(tela, x, y, dirx, diry, cor, tam=5):
    """Setinha cheia apontando em (dirx, diry) (um dos 4 sentidos)."""
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if diry:
            yy = y + (k if diry > 0 else -k)
            tela.ret(x - w // 2, yy, w, 1, cor)
        else:
            xx = x + (k if dirx > 0 else -k)
            tela.ret(xx, y - w // 2, 1, w, cor)


def forca(tela, x, y, comp, para_cima, cor):
    """Seta de força vertical com contorno: base em (x, y), comprimento em px."""
    comp = int(round(comp))
    if comp < 2: return
    s = -1 if para_cima else 1
    y1 = y + s * comp
    a, b = sorted((y, y1))
    tela.ret(x - 2, a - 1, 5, b - a + 2, PRETO)
    tela.ret(x - 1, a, 3, b - a, cor)
    ponta = y1 + s * 5
    for k in range(7):
        w = (7 - k) * 2 - 1
        yy = ponta - s * (6 - k)
        tela.ret(x - w // 2 - 1, yy, w + 2, 1, PRETO)
    seta(tela, x, ponta - s * 1, 0, s, cor, 6)


def bolha(tela, x, y, r=1.5):
    tela.anel(x, y, r, MISTURA2, .5)
    tela.px(x - .5, y - .8, BRANCO)


def raio_luz(tela, x, y, t, cor=AMARELO):
    """Lampadinha que pisca (luz de mastro, janela)."""
    tela.px(x, y, cor if int(t * 2) % 2 == 0 else CHAMA0)


# ================================================================ céu e água
def ceu(tela, t, y1=PALCO_H, estrelas=True):
    tela.ret(0, 0, W, y1, FUNDO)
    dither(tela, 0, int(y1 * .45), W, int(y1 * .25), FUNDO, FUNDO2)
    tela.ret(0, int(y1 * .70), W, y1 - int(y1 * .70), FUNDO2)
    dither(tela, 0, int(y1 * .86), W, y1 - int(y1 * .86), FUNDO2, FUNDO3)
    if estrelas:
        for k in range(26):
            x = (k * 97 + 13) % W; y = (k * 53 + 7) % int(y1 * .55)
            if (int(t * 1.5) + k) % 7: tela.px(x, y, ACO2 if k % 3 else ACO4)
    # nuvens baixas andando devagar
    for k in range(4):
        x = int((k * 151 - t * (3 + k)) % (W + 80)) - 40
        y = int(y1 * .42) + k * 9
        for j in range(5):
            tela.ret(x + j * 7, y - (2 if j in (1, 2) else 0), 12, 3 + (j % 2), FUNDO3)
            tela.ret(x + j * 7, y - (2 if j in (1, 2) else 0), 12, 1, ACO0)


CORES_MAR = [(MISTURA, FUNDO3), (FUNDO3, FUNDO2), (FUNDO2, FUNDO)]
CORES_DOCE = [(AGUA1, AGUA0), (AGUA0, FUNDO3), (AGUA0, FUNDO2)]


def agua_fundo(tela, x0, yw, x1, y1, doce=False):
    """Corpo d'água (atrás de tudo): faixas de dither escurecendo com a fundura."""
    cores = CORES_DOCE if doce else CORES_MAR
    h = y1 - yw
    for k, (a, b) in enumerate(cores):
        ya = yw + int(h * k / 3); yb = yw + int(h * (k + 1) / 3)
        dither(tela, x0, ya, x1 - x0, yb - ya, a, b)


def agua_por_cima(tela, x0, yw, x1, y1, t, doce=False, onda=True, ondas_de=None):
    """Água por cima do que está dentro: xadrez + linha da superfície com ondinhas.
    `ondas_de` = função x -> desvio da superfície (opcional)."""
    x0, x1 = max(0, int(x0)), min(W, int(x1))
    yw = int(yw); y1 = min(PALCO_H, int(y1))
    if x1 <= x0 or y1 <= yw: return
    cores = CORES_DOCE if doce else CORES_MAR
    h = max(1, y1 - yw)
    yy, xx = np.mgrid[yw:y1, x0:x1]
    sub = tela.buf[yw:y1, x0:x1]
    banda = np.minimum(2, ((yy - yw) * 3) // h)
    cor = np.array([c[0] for c in cores], np.uint8)[banda]
    m = (xx + yy) % 2 == 0
    sub[m] = cor[m]
    # superfície: linha clara com ondinhas que correm
    sup = MISTURA2 if not doce else AGUA1
    for x in range(x0, x1):
        d = 0
        if onda:
            d = 1 if math.sin(x * .21 - t * 2.6) + .6 * math.sin(x * .07 + t * 1.3) > 1.0 else 0
        tela.px(x, yw - d, sup)
        if d == 0 and (x * 7 + int(t * 6)) % 23 == 0: tela.px(x, yw, BRANCO)
        tela.px(x, yw + 1, cores[0][0])


# ================================================================ tanque de vidro
class Tanque:
    """Aquário de vidro de frente. Dentro: x TX0..TX1, fundo TY1."""
    TX0, TX1, TY0, TY1 = 52, 222, 70, 192
    PROF_CM = 20.0                               # profundidade (para dentro da tela)

    def __init__(self, nivel=112, bico=False):
        self.nivel0 = nivel
        self.bico = bico

    def area_cm2(self):
        return (self.TX1 - self.TX0) / PX_CM * self.PROF_CM

    def fundo(self, tela, nivel):
        X0, X1, Y0, Y1 = self.TX0, self.TX1, self.TY0, self.TY1
        # mesa
        tela.ret(0, Y1 + 4, 300, PALCO_H - Y1 - 4, OLEO0)
        dither(tela, 0, Y1 + 6, 300, PALCO_H - Y1 - 6, OLEO0, FUNDO)
        tela.ret(0, Y1 + 4, 300, 1, LATAO)
        # interior (ar)
        dither(tela, X0, Y0, X1 - X0, Y1 - Y0, FUNDO, FUNDO2)
        agua_fundo(tela, X0, int(nivel), X1, Y1, doce=True)
        # pedrinhas no fundo
        for k in range(18):
            x = X0 + 4 + (k * 37) % (X1 - X0 - 8)
            tela.ret(x, Y1 - 2 - (k % 2), 4, 2 + (k % 2), ACO1 if k % 3 else ACO2)

    def frente(self, tela, nivel, t):
        X0, X1, Y0, Y1 = self.TX0, self.TX1, self.TY0, self.TY1
        agua_por_cima(tela, X0, int(nivel), X1, Y1, t, doce=True)
        # vidro: paredes, borda, reflexo
        for x in (X0 - 3, X1):
            tela.ret(x, Y0 - 2, 3, Y1 - Y0 + 5, PRETO)
            tela.ret(x + 1, Y0 - 1, 1, Y1 - Y0 + 3, MISTURA2 if x < X0 else ACO3)
        tela.ret(X0 - 3, Y1, X1 - X0 + 6, 4, PRETO)
        tela.ret(X0 - 2, Y1 + 1, X1 - X0 + 4, 2, ACO2)
        tela.ret(X0 - 2, Y1 + 1, X1 - X0 + 4, 1, ACO4)
        tela.ret(X0 - 4, Y0 - 3, 5, 2, ACO3); tela.ret(X1 - 1, Y0 - 3, 5, 2, ACO3)
        for k in range(3):                                   # reflexo no vidro
            tela.ret(X0 + 6 + k * 4, Y0 + 8 + k * 6, 1, 26 - k * 6, ACO2)
        # régua em cm na parede da direita
        for k in range(0, int((Y1 - Y0) / PX_CM) + 1):
            y = int(Y1 - k * PX_CM)
            tela.ret(X1 - 4, y, 3 if k % 5 else 4, 1, ACO3 if k % 5 else BRANCO)
        if self.bico:
            yb = Y0 + 1
            tela.ret(X1 + 2, yb - 1, 16, 5, PRETO)
            tela.ret(X1 + 3, yb, 14, 3, ACO3); tela.ret(X1 + 3, yb, 14, 1, ACO4)


def jarra(tela, x, y, w, h, frac, rot, cor=AGUA1, marcas=(), t=0.0):
    """Jarra medidora: copo de vidro com nível `frac` (0..1) e marcas (frac, texto)."""
    tela.ret(x - 2, y - 1, w + 4, h + 3, PRETO)
    dither(tela, x, y, w, h, FUNDO, FUNDO2)
    n = int(round(max(0.0, min(1.0, frac)) * h))
    if n > 0:
        dither(tela, x, y + h - n, w, n, cor, AGUA0)
        tela.ret(x, y + h - n, w, 1, MISTURA2)
    tela.ret(x - 1, y, 1, h + 1, MISTURA2); tela.ret(x + w, y, 1, h + 1, ACO3)
    tela.ret(x - 1, y + h, w + 2, 1, ACO3)
    tela.ret(x + w, y + 3, 4, 2, ACO3)                      # bico
    for f, txt in marcas:
        yy = int(y + h - f * h)
        tela.ret(x, yy, 4, 1, BRANCO)
        if txt: tela.texto(txt, x + w + 6, yy - 3, ACO3, tam=9, contorno=PRETO)
    if rot: tela.texto(rot, x + w // 2, y + h + 5, ACO3, tam=9, centro=True, contorno=PRETO)


def balanca(tela, cx, y, leitura, cor_vis=VERDE, w=70):
    """Balança digital de cozinha: prato em y, visor embaixo."""
    tela.ret(cx - w // 2 - 1, y - 1, w + 2, 6, PRETO)
    tela.ret(cx - w // 2, y, w, 4, ACO3); tela.ret(cx - w // 2, y, w, 1, ACO4)
    tela.ret(cx - w // 2 + 6, y + 5, w - 12, 22, PRETO)
    tela.ret(cx - w // 2 + 7, y + 6, w - 14, 20, ACO1); tela.ret(cx - w // 2 + 7, y + 6, w - 14, 1, ACO2)
    tela.ret(cx - 26, y + 9, 52, 13, PRETO)
    tela.texto(leitura, cx, y + 12, cor_vis, tam=9, centro=True)


def medidor_densidade(tela, x, y, w, marcas, vmax=8.0, t=0.0):
    """Régua de densidade 0..vmax com a faixa 'flutua' (abaixo da água)."""
    px = lambda v: x + int(v / vmax * w)
    tela.ret(x - 1, y - 1, w + 2, 9, PRETO)
    tela.ret(x, y, px(RHO_DOCE) - x, 7, AGUA0)
    dither(tela, px(RHO_DOCE), y, x + w - px(RHO_DOCE), 7, FUNDO3, BRASA)
    tela.ret(px(RHO_DOCE), y - 4, 1, 15, AGUA1)
    for v in range(0, int(vmax) + 1):
        tela.ret(px(v), y + 8, 1, 3, ACO3)
        tela.texto(str(v), px(v), y + 13, ACO3, tam=9, centro=True)
    for v, txt, cor, cima in marcas:
        xx = px(min(v, vmax))
        if cima:
            tela.ret(xx - 1, y - 7, 3, 7, PRETO); tela.ret(xx, y - 6, 1, 6, cor)
            tela.disco(xx, y - 8, 2.5, PRETO); tela.disco(xx, y - 8, 1.6, cor)
            tela.texto(txt, xx, y - 20, cor, tam=9, centro=True, contorno=PRETO)
        else:
            tela.ret(xx - 1, y + 7, 3, 9, PRETO); tela.ret(xx, y + 7, 1, 8, cor)
            tela.texto(txt, xx, y + 25, cor, tam=9, centro=True, contorno=PRETO)


def barra_forca(tela, x, y, w, valor, vmax, cor, rot, txt):
    tela.texto(rot, x, y, ACO3, tam=9, contorno=PRETO)
    tela.texto(txt, x + w, y, cor, tam=9, centro='d', contorno=PRETO)
    tela.ret(x, y + 11, w, 6, PRETO)
    tela.ret(x + 1, y + 12, w - 2, 4, FUNDO2)
    n = int((w - 2) * max(0.0, min(1.0, valor / vmax)))
    if n > 0:
        tela.ret(x + 1, y + 12, n, 4, cor)
        tela.ret(x + 1, y + 12, n, 1, BRANCO if cor in (AMARELO, VERDE, MISTURA2) else CHAMA0)


def kg(v, casas=2):
    return f"{I.decimal(v, casas)} KG"


# ================================================================ objetos de aço do tanque
def gancho_corda(tela, x, y_obj, t, folga=0.0):
    """Corda descendo do alto até o objeto (com folga = curva quando solta)."""
    if y_obj <= 0: return
    if folga <= 0:
        tela.ret(int(x), 0, 1, int(y_obj) - 2, ACO4)
    else:
        n = int(y_obj)
        for yy in range(0, n - 2):
            d = math.sin(yy / max(1, n) * math.pi) * folga * 6
            tela.px(x + d, yy, ACO4)
    tela.ret(int(x) - 2, int(y_obj) - 4, 5, 3, PRETO); tela.ret(int(x) - 1, int(y_obj) - 3, 3, 1, ACO3)


def cubo(tela, cx, y_base, lado, t=0.0):
    """Cubo de aço maciço visto de frente com um pouco de topo (base em y_base)."""
    x0, y0 = int(cx - lado / 2), int(y_base - lado)
    l = int(lado)
    tela.ret(x0 - 1, y0 - 4, l + 5, l + 5, PRETO)
    poligono(tela, [(x0, y0), (x0 + 3, y0 - 3), (x0 + l + 3, y0 - 3), (x0 + l, y0)], ACO4)   # topo
    tela.ret(x0 + l, y0 - 2, 3, l, ACO1)                                                     # lado
    dither(tela, x0, y0, l, l, ACO2, ACO3)
    dither(tela, x0, y0 + l // 2, l, l - l // 2, ACO2, ACO1)
    tela.ret(x0, y0, l, 1, BRANCO)
    tela.ret(x0, y0, 1, l, ACO4)
    tela.px(x0 + 2, y0 + 2, BRANCO)


def caixa(tela, cx, y_base, larg, alt, t=0.0, agua_dentro=0.0, furo=False, ar=True, cor_ar=ACO1):
    """Caixa aberta de chapa fina (a 'tigela'), em corte: paredes de 2 px.
    agua_dentro = altura (px) da água que entrou."""
    x0, x1 = int(cx - larg / 2), int(cx + larg / 2)
    yb, yt = int(y_base), int(y_base - alt)
    # interior: ar (pontinhos claros subindo devagar)
    if ar:
        for k in range(14):
            u = (t * .25 + k / 14) % 1.0
            x = x0 + 4 + (k * 13) % max(1, (x1 - x0 - 8))
            y = yb - 4 - u * (alt - 8)
            if y > yb - agua_dentro - 2: continue
            tela.px(x, y, cor_ar)
    if agua_dentro > 0:
        a = int(agua_dentro)
        dither(tela, x0 + 2, yb - 2 - a, x1 - x0 - 4, a, AGUA1, AGUA0)
        tela.ret(x0 + 2, yb - 2 - a, x1 - x0 - 4, 1, MISTURA2)
    # paredes
    for x in (x0, x1 - 2):
        tela.ret(x - 1, yt - 1, 4, alt + 2, PRETO)
        tela.ret(x, yt, 2, alt, ACO3); tela.ret(x, yt, 1, alt, ACO4)
    tela.ret(x0 - 1, yb - 3, x1 - x0 + 2, 4, PRETO)
    tela.ret(x0, yb - 2, x1 - x0, 2, ACO3); tela.ret(x0, yb - 1, x1 - x0, 1, ACO1)
    tela.ret(x0 - 2, yt - 1, 4, 1, BRANCO); tela.ret(x1 - 2, yt - 1, 4, 1, BRANCO)
    if furo:
        hx = int(cx + larg * .2)
        tela.ret(hx, yb - 2, 3, 2, PRETO)


def chapa(tela, cx, y_base, larg, esp=2):
    x0 = int(cx - larg / 2)
    tela.ret(x0 - 1, int(y_base) - esp - 1, int(larg) + 2, esp + 2, PRETO)
    tela.ret(x0, int(y_base) - esp, int(larg), esp, ACO3)
    tela.ret(x0, int(y_base) - esp, int(larg), 1, ACO4)


def boia(tela, cx, y_base, larg, alt, t=0.0):
    """Boia fechada (caixa laranja) — o objeto do teste de Arquimedes."""
    x0, y0 = int(cx - larg / 2), int(y_base - alt)
    tela.ret(x0 - 1, y0 - 1, larg + 2, alt + 2, PRETO)
    dither(tela, x0, y0, larg, alt, LARANJA, CHAMA1)
    dither(tela, x0, y0 + alt // 2, larg, alt - alt // 2, LARANJA, BRASA)
    tela.ret(x0, y0, larg, 1, CHAMA0)
    for k in range(1, 4):
        tela.ret(x0 + 2, y0 + k * alt // 4, larg - 4, 1, BRASA)
    tela.ret(x0 + 3, y0 + 3, 3, 2, CHAMA0)
    tela.ret(int(cx) - 3, y0 - 4, 7, 4, PRETO); tela.ret(int(cx) - 2, y0 - 3, 5, 2, ACO3)   # alça


def parafuso(tela, cx, cy, ang=0.0):
    """Parafuso de aço (para o gancho): cabeça sextavada e rosca."""
    ca, sa = math.cos(ang), math.sin(ang)
    P = lambda a, b: (cx + a * ca - b * sa, cy + a * sa + b * ca)
    corpo = [P(-3, 0), P(3, 0), P(3, 22), P(0, 26), P(-3, 22)]
    cab = [P(-7, -6), P(7, -6), P(7, 0), P(-7, 0)]
    poligono(tela, [(x - 1, y) for x, y in corpo], PRETO); poligono(tela, [(x + 1, y) for x, y in corpo], PRETO)
    poligono(tela, corpo, ACO3)
    poligono(tela, [(x, y - 1) for x, y in cab], PRETO); poligono(tela, [(x, y + 1) for x, y in cab], PRETO)
    poligono(tela, cab, ACO4)
    for k in range(6):
        a, b = P(-3, 3 + k * 3.4), P(3, 4.5 + k * 3.4)
        tela.linha(a[0], a[1], b[0], b[1], ACO1)


# ================================================================ o navio
CORES_CONT = [LARANJA, VERMELHO, CIANO, VERDE, AMARELO, ROXO, MISTURA, CERAMICA]
ESCURA = {LARANJA: BRASA, VERMELHO: BRASA, CIANO: AGUA0, VERDE: AGUA0, AMARELO: LATAO, ROXO: FUNDO3,
          MISTURA: FUNDO3, CERAMICA: ACO2}
CLARA = {LARANJA: CHAMA1, VERMELHO: ROSA, CIANO: MISTURA2, VERDE: AGUA1, AMARELO: CHAMA0, ROXO: ROSA,
         MISTURA: MISTURA2, CERAMICA: BRANCO}


def conteiner(tela, x, y, cor, w=10, h=5):
    tela.ret(x, y, w, h, PRETO)
    tela.ret(x + 1, y + 1, w - 2, h - 1, cor)
    tela.ret(x + 1, y + 1, w - 2, 1, CLARA[cor])
    for k in range(3, w - 2, 3): tela.ret(x + k, y + 2, 1, h - 2, ESCURA[cor])


class Navio:
    L, D = 256, 46                       # comprimento e pontal (px)
    BAIAS, ANDARES = 17, 6
    U_CARGA0 = 58                        # primeira baia (u)
    V_MAX = 32                           # calado máximo (16 m) em px: linha S da marca

    def __init__(self, L=256):
        self.L = L
        self.BAIAS = max(4, (L - 22 - self.U_CARGA0) // 10)
        L, D = self.L, self.D
        self.casco = [(2, D + 3), (0, D + 3), (0, 28), (5, 20), (14, 14), (20, 8), (28, 2), (34, 0),
                      (L - 30, 0), (L - 20, 1), (L - 12, 3), (L - 8, 7), (L - 10, 11), (L - 17, 13),
                      (L - 15, 20), (L - 8, 32), (L + 2, D + 6), (L - 24, D + 5), (L - 40, D + 3)]
        # anteparas (u) e porões
        self.ante = [50] + [self.U_CARGA0 + 10 * k * 2 + 6 for k in range(1, 9)
                            if self.U_CARGA0 + 20 * k + 6 < L - 26]
        self.ante.append(L - 26)
        self.n_comp = len(self.ante) - 1
        self.slots = [(i, j) for j in range(self.ANDARES) for i in range(self.BAIAS)]
        self.slots.sort(key=lambda s: (s[1] // 2, s[0], s[1]))

    def tela_xy(self, x0, yq, u, v): return x0 + u, yq - v

    def _poli(self, x0, yq, pts):
        return [(x0 + u, yq - v) for u, v in pts]

    def mascara_casco(self, x0, yq):
        """Máscara booleana (H, W) do casco (para recortes)."""
        from pixelengine import Tela
        return None

    def desenhar(self, tela, x0, yq, t, n_cont=0, corte=False, alagados=(), nivel_agua_v=None,
                 marcas=True, plimsoll=True, fumaca=True, holofote=None, rotulos=None, inclina=0.0,
                 agua_comp=None):
        """yq = y da quilha na tela. n_cont = contêineres no convés (0..BAIAS*ANDARES).
        corte = mostra o interior (porões, anteparas). alagados = índices de compartimentos
        com água até `nivel_agua_v` (altura da água de fora, em v)."""
        L, D = self.L, self.D
        x0 = int(x0); yq = int(yq)
        P = lambda pts: self._poli(x0, yq, pts)
        casco = P(self.casco)
        # contorno (1 px em volta) e corpo
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            poligono(tela, [(x + dx, y + dy) for x, y in casco], PRETO)
        poligono(tela, casco, FUNDO3)
        # pintura: obras vivas vermelhas até a linha S, faixa clara, costado escuro
        vs = self.V_MAX
        for y in range(yq - D - 6, yq + 1):
            v = yq - y
            if v <= vs:
                row = tela.buf[y, max(0, x0 - 2):min(W, x0 + L + 4)]
                m = row == FUNDO3
                xs = np.arange(max(0, x0 - 2), min(W, x0 + L + 4))
                c = np.where((xs + y) % 2 == 0, BRASA, VERMELHO) if v > 3 else np.full(xs.shape, BRASA)
                row[m] = c[m]
            elif v <= vs + 2:
                row = tela.buf[y, max(0, x0 - 2):min(W, x0 + L + 4)]
                row[row == FUNDO3] = ACO0
            elif v >= D - 2:
                row = tela.buf[y, max(0, x0 - 2):min(W, x0 + L + 4)]
                row[row == FUNDO3] = ACO1
        tela.ret(x0 + 2, yq - D - 3, L - 42, 1, ACO3)              # borda do convés
        tela.ret(x0 + L - 40, yq - D - 4, 30, 1, ACO3)
        # chapas do costado (linhas verticais discretas)
        for u in range(40, L - 30, 16):
            for v in range(vs + 4, D - 2, 2):
                tela.px(x0 + u, yq - v, TRACO)
        if corte:
            self._interior(tela, x0, yq, t, n_cont, alagados, nivel_agua_v, agua_comp)
        # hélice e leme (popa, embaixo)
        hx, hy = x0 + 18, yq - 8
        ang = t * 6
        for k in range(3):
            a = ang + k * 2.094
            tela.linha(hx, hy, hx + 5 * math.cos(a), hy + 7 * math.sin(a), PRETO)
            tela.linha(hx + 1, hy, hx + 1 + 5 * math.cos(a), hy + 7 * math.sin(a), LATAO)
        tela.disco(hx, hy, 2, PRETO); tela.disco(hx, hy, 1.2, CHAMA1)
        tela.ret(x0 + 5, yq - 16, 5, 15, PRETO); tela.ret(x0 + 6, yq - 15, 3, 13, ACO1)   # leme
        tela.ret(x0 + 6, yq - 15, 1, 13, ACO2)
        # marcas de calado (proa e popa): tracinhos a cada 2 m
        if marcas:
            for ub in (L - 26, 32):
                for m in range(2, 21, 2):
                    v = int(m * PX_M)
                    if v > D: break
                    tela.ret(x0 + ub, yq - v, 3 if m % 4 else 4, 1, BRANCO)
        if plimsoll:
            cx, cy = x0 + L // 2, yq - vs
            tela.anel(cx, cy, 3, BRANCO, .5)
            tela.ret(cx - 5, cy, 11, 1, BRANCO)
            tela.ret(cx + 8, cy - 4, 1, 8, BRANCO)
            for k, dy in enumerate((-3, -1, 0, 2)):
                tela.ret(cx + 9, cy + dy, 3, 1, BRANCO)
        # superestrutura (casario) na popa
        sx0, sx1, sb = x0 + 20, x0 + 48, yq - D - 3
        tela.ret(sx0 - 1, sb - 37, sx1 - sx0 + 2, 38, PRETO)
        dither(tela, sx0, sb - 36, sx1 - sx0, 36, CERAMICA, BRANCO)
        dither(tela, sx0 + (sx1 - sx0) // 2, sb - 36, (sx1 - sx0) // 2, 36, CERAMICA, ACO4)
        for r in range(5):
            for c in range(5):
                lit = (r * 5 + c + int(t * .3)) % 7 != 0
                tela.ret(sx0 + 3 + c * 5, sb - 32 + r * 6, 3, 2, AMARELO if lit else FUNDO3)
        tela.ret(sx0 - 6, sb - 40, sx1 - sx0 + 12, 4, PRETO)                 # passadiço (ponte)
        tela.ret(sx0 - 5, sb - 39, sx1 - sx0 + 10, 2, BRANCO)
        tela.ret(sx0 - 3, sb - 43, sx1 - sx0 + 4, 4, PRETO)
        tela.ret(sx0 - 2, sb - 42, sx1 - sx0 + 2, 2, MISTURA2)
        tela.ret(sx0 + 10, sb - 52, 1, 9, ACO3)                              # mastro do radar
        tela.ret(sx0 + 6, sb - 52, 9, 1, ACO3 if int(t * 2) % 2 else ACO4)
        raio_luz(tela, sx0 + 10, sb - 53, t, VERMELHO)
        # chaminé
        cx0 = x0 + 8
        tela.ret(cx0 - 1, sb - 30, 12, 31, PRETO)
        tela.ret(cx0, sb - 29, 10, 29, ACO1); tela.ret(cx0, sb - 29, 3, 29, ACO2)
        tela.ret(cx0, sb - 24, 10, 4, VERMELHO); tela.ret(cx0, sb - 29, 10, 2, PRETO)
        if fumaca:
            for k in range(8):
                u = (t * .35 + k / 8) % 1.0
                fx_ = cx0 + 5 - u * 46 + math.sin(u * 7 + k) * 2
                fy = sb - 32 - u * 26
                r = 1.5 + u * 4
                tela.disco(fx_, fy, r, ACO1 if u > .5 else ACO2)
        # mastro de proa com luz
        mx = x0 + L - 14
        tela.ret(mx, yq - D - 22, 1, 17, ACO3)
        raio_luz(tela, mx, yq - D - 23, t + .5, AMARELO)
        # contêineres no convés
        n = int(n_cont)
        for k in range(min(n, len(self.slots))):
            i, j = self.slots[k]
            cor = CORES_CONT[(i * 5 + j * 3) % len(CORES_CONT)]
            conteiner(tela, x0 + self.U_CARGA0 + i * 10, yq - D - 3 - (j + 1) * 5, cor)
        # escotilhas (tampa dos porões) quando o convés está vazio
        for i in range(self.BAIAS):
            if not any(self.slots[k][0] == i for k in range(min(n, len(self.slots)))):
                tela.ret(x0 + self.U_CARGA0 + i * 10 + 1, yq - D - 5, 8, 2, ACO2)

    def _interior(self, tela, x0, yq, t, n_cont, alagados, nivel_v, agua_comp=None):
        L, D = self.L, self.D
        a0, a1 = self.ante[0], self.ante[-1]
        top = D - 1
        # ar dos porões
        dither(tela, x0 + a0, yq - top, a1 - a0, top - 5, FUNDO, FUNDO2)
        # duplo fundo
        tela.ret(x0 + a0, yq - 5, a1 - a0, 2, ACO2); tela.ret(x0 + a0, yq - 4, a1 - a0, 1, ACO1)
        # praça de máquinas (embaixo do casario)
        tela.ret(x0 + 22, yq - 30, 26, 24, PRETO)
        dither(tela, x0 + 23, yq - 29, 24, 22, FUNDO, FUNDO2)
        tela.ret(x0 + 26, yq - 22, 18, 14, ACO1); tela.ret(x0 + 26, yq - 22, 18, 2, ACO3)
        for k in range(3):
            tela.ret(x0 + 28 + k * 6, yq - 27, 3, 5, ACO2 if int(t * 8 + k) % 2 else ACO3)
        tela.ret(x0 + 18, yq - 9, 8, 2, ACO3)                                    # eixo
        # carga nos porões (contêineres embaixo do convés)
        cheio = min(1.0, n_cont / 40.0)
        for ci in range(self.n_comp):
            ua, ub = self.ante[ci], self.ante[ci + 1]
            filas = int(round(cheio * 6))
            for r in range(filas):
                for c in range((ub - ua - 3) // 10):
                    cor = CORES_CONT[(ci * 3 + r * 5 + c) % len(CORES_CONT)]
                    conteiner(tela, x0 + ua + 2 + c * 10, yq - 6 - (r + 1) * 6, cor, 10, 5)
        # ar: pontinhos subindo
        for k in range(30):
            u = (t * .2 + k / 30) % 1.0
            x = x0 + a0 + 3 + (k * 41) % (a1 - a0 - 6)
            y = yq - 7 - u * (top - 10)
            if tela.buf[int(y), int(x)] in (FUNDO, FUNDO2): tela.px(x, y, ACO2)
        # água nos compartimentos alagados
        for ci in alagados:
            if ci < 0 or ci >= self.n_comp: continue
            ua, ub = self.ante[ci], self.ante[ci + 1]
            lv = nivel_v if agua_comp is None else agua_comp.get(ci, nivel_v)
            lv = min(top - 1, lv)
            if lv <= 5: continue
            ya = yq - int(lv)
            dither(tela, x0 + ua, ya, ub - ua, yq - 5 - ya, MISTURA, FUNDO3)
            tela.ret(x0 + ua, ya, ub - ua, 1, MISTURA2)
            for k in range(4):
                u = (t * .9 + k / 4) % 1.0
                bolha(tela, x0 + ua + 4 + (k * 7) % max(1, ub - ua - 8), yq - 7 - u * (lv - 8))
        # anteparas
        for u in self.ante:
            tela.ret(x0 + u - 1, yq - top, 3, top - 3, PRETO)
            tela.ret(x0 + u, yq - top + 1, 1, top - 5, ACO3)
        # convés por cima
        tela.ret(x0 + a0, yq - top - 1, a1 - a0, 2, ACO2)

    def pos_peca(self, x0, yq, nome):
        L, D = self.L, self.D
        return {'casco': (x0 + L - 60, yq - 38), 'porao': (x0 + 120, yq - 20),
                'antepara': (x0 + self.ante[3], yq - 30), 'linha': (x0 + L - 70, yq - self.V_MAX + 2),
                'helice': (x0 + 18, yq - 8), 'leme': (x0 + 7, yq - 10),
                'casario': (x0 + 34, yq - D - 24), 'plimsoll': (x0 + L // 2, yq - self.V_MAX)}[nome]


def calado_px(frac):
    """Calado (px) para a fração de carga 0..1 (vazio = 7 m, exemplo; cheio = 16 m)."""
    return (7.0 + 9.0 * frac) * PX_M


def regua_calado(tela, x, y, h, calado_m, cor_agua=MISTURA, rotulo_max=True, vmax=18):
    """Close das marcas de calado da proa: números em metros e a água subindo."""
    tela.ret(x - 1, y - 1, 46, h + 2, PRETO)
    pxm = h / vmax
    yw = int(y + h - calado_m * pxm)
    dither(tela, x, y, 44, h, VERMELHO, BRASA)
    tela.ret(x, y, 44, max(0, int(h - 16.5 * pxm)), FUNDO3)
    for m in range(2, vmax + 1, 2):
        yy = int(y + h - m * pxm)
        tela.ret(x + 4, yy, 6, 1, BRANCO)
        tela.texto(str(m), x + 12, yy - 3, BRANCO, tam=9, contorno=PRETO)
    if yw < y + h:
        yy, xx = np.mgrid[yw:y + h, x:x + 44]
        sub = tela.buf[yw:y + h, x:x + 44]
        sub[(xx + yy) % 2 == 0] = cor_agua
        tela.ret(x, yw, 44, 1, MISTURA2 if cor_agua == MISTURA else AGUA1)


def marca_plimsoll(tela, cx, cy, esc, nivel_y=None, ativa=None, t=0.0):
    """A marca de Plimsoll em close (esc = px por unidade). Linhas à direita:
    T, S, W, WNA; à esquerda: TF, F. S fica na altura do centro do disco.
    Devolve {letra: y}."""
    cor = BRANCO
    r = 9 * esc
    # linha do convés acima
    tela.ret(cx - int(14 * esc), cy - int(16 * esc), int(28 * esc), max(2, int(1.2 * esc)), cor)
    tela.anel(cx, cy, r, cor, max(1.0, .9 * esc))
    tela.ret(cx - int(13 * esc), cy - max(1, int(.6 * esc)), int(26 * esc), max(2, int(1.2 * esc)), cor)
    xv = cx + int(18 * esc)
    tela.ret(xv, cy - int(8 * esc), max(2, int(1.2 * esc)), int(16 * esc), cor)
    ys = {'TF': -6.5, 'F': -4.0, 'T': -2.5, 'S': 0.0, 'W': 2.5, 'WNA': 5.0}
    out = {}
    for k, d in ys.items():
        y = cy + int(d * esc) - (max(1, int(.6 * esc)) if k == 'S' else 0)
        out[k] = y
        esq = k in ('TF', 'F')
        c = AMARELO if ativa == k else cor
        if esq:
            tela.ret(xv - int(6 * esc), y, int(6 * esc), max(2, int(1.2 * esc)), c)
            tela.texto(k, xv - int(6 * esc) - 3, y - 3, c, tam=9, centro='d', contorno=PRETO)
        else:
            tela.ret(xv, y, int(6 * esc), max(2, int(1.2 * esc)), c)
            tela.texto(k, xv + int(6 * esc) + 4, y - 3, c, tam=9, contorno=PRETO)
    return out
