#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep01 — desenhos dos capítulos extras (injetor, faísca,
arrefecimento e carro flex). As cenas moram em `ep01_motor.py`; aqui só o
desenho das peças novas, todas genéricas (nenhuma marca).

  injetor_grande   o injetor em corte: bobina, agulha, bico e o spray
  injetor_mini     o mesmo injetor em miniatura, no duto de admissão do Cilindro
  bobina           a bobina de ignição: núcleo, primário (poucas voltas),
                   secundário (milhares de voltas)
  vela_grande      a vela em pé: isolador de cerâmica, rosca e a folga
  radiador         colmeia de tubos com as caixas de cima e de baixo
  tanque           tanque em corte com a mistura etanol/gasolina
  rotulo           texto com fio até a peça (o padrão do canal)
"""
import math
import numpy as np
from longo import (W, PALCO_H, dither, poligono, linha_grossa, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2,
                   ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2,
                   BRASA, MISTURA, MISTURA2, GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, VERDE, PRETO)
from longo import BAYER8
import motor_pixel as MP

GASOLINA, ETANOL = AMARELO, VERDE          # no posto, o bico do etanol é verde


def hsh(i, k=0):
    """Ruído fixo (0..1) para posições de gotas: o mesmo quadro sai igual sempre."""
    x = math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return x - math.floor(x)


def rotulo(tela, txt, tx, ty, ax, ay, cor=BRANCO, cor_fio=None, tam=9):
    """Texto em (tx, ty) com um fio até o ponto (ax, ay) da peça."""
    cf = cor if cor_fio is None else cor_fio
    w = tela.largura_texto(txt, tam)
    h = 7 if tam == 9 else 14
    if ax >= tx + w:
        x0 = tx + w + 2
    elif ax <= tx:
        x0 = tx - 3
    else:
        x0 = min(max(ax, tx), tx + w)
    y0 = ty + h // 2 if (ax >= tx + w or ax <= tx) else (ty + h + 2 if ay > ty else ty - 3)
    tela.linha(x0, y0, ax, ay, cf)
    tela.disco(ax, ay, 1.4, cf)
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)


def contorno_ret(tela, x, y, w, h, cor, borda=PRETO):
    tela.ret(x - 1, y - 1, w + 2, h + 2, borda)
    tela.ret(x, y, w, h, cor)


def tique(fx, f=1800.0, dur=.035):
    """Tique curto de seno (pico baixo): contador que sobe."""
    import longo as LG
    n = int(dur * LG.SR)
    tt = np.arange(n) / LG.SR
    return (np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / .002) * np.exp(-tt / (dur / 4))).astype(np.float32)


# ======================================================================= injetor
def injetor_grande(tela, cx, y0, abre, energia, t):
    """Injetor em pé, em corte. `abre` 0..1 (agulha levantada), `energia`
    0..1 (bobina ligada). Devolve as âncoras das peças para os rótulos."""
    # tubo de combustível (galeria) chegando por cima
    contorno_ret(tela, cx - 70, y0, 70, 9, ACO1)
    dither(tela, cx - 69, y0 + 2, 69, 5, CHAMA0, GASOLINA)
    for k in range(5):                                         # combustível andando no tubo
        u = (k / 5 + t * .6) % 1.0
        tela.ret(int(cx - 68 + u * 64), y0 + 3, 3, 3, LARANJA)
    # corpo
    x0 = cx - 18
    contorno_ret(tela, x0, y0 + 9, 36, 72, ACO1)
    dither(tela, x0 + 1, y0 + 10, 34, 70, ACO1, ACO2)
    tela.ret(x0, y0 + 9, 1, 72, ACO3)
    tela.ret(x0 + 35, y0 + 9, 1, 72, ACO0)
    # conector elétrico (à direita)
    contorno_ret(tela, cx + 18, y0 + 14, 14, 12, ACO0)
    tela.ret(cx + 20, y0 + 17, 2, 6, LATAO)
    tela.ret(cx + 25, y0 + 17, 2, 6, LATAO)
    # canal central com combustível
    tela.ret(cx - 4, y0 + 9, 8, 80, FUNDO)
    dither(tela, cx - 4, y0 + 9, 8, 80, CHAMA0, GASOLINA, fase=int(t * 8) % 2)
    # bobina (solenoide) dos dois lados do canal
    for lado in (-1, 1):
        bx = cx - 15 if lado < 0 else cx + 6
        for k in range(10):
            y = y0 + 28 + k * 3
            cor = LATAO if energia < .5 else (AMARELO if (k + int(t * 30)) % 3 else CHAMA0)
            tela.ret(bx, y, 9, 2, cor)
            tela.ret(bx, y + 2, 9, 1, OLEO0)
    if energia > .5:                                            # brilho da bobina ligada
        for k in range(6):
            a = t * 9 + k
            tela.px(cx - 20 - (k % 2) * 2, y0 + 30 + (k * 5) % 28, AMARELO)
            tela.px(cx + 20 + (k % 2) * 2, y0 + 32 + (k * 7) % 26, AMARELO)
    # agulha: sobe quando a bobina puxa
    lev = int(round(abre * 4))
    tela.ret(cx - 2, y0 + 24 - lev, 4, 70, ACO3)
    tela.ret(cx - 2, y0 + 24 - lev, 1, 70, ACO4)
    tela.ret(cx - 3, y0 + 22 - lev, 6, 4, ACO2)                   # armadura (o ímã puxa ela)
    # bico afunilado
    pts = [(x0 - 1, y0 + 81), (x0 + 37, y0 + 81), (cx + 6, y0 + 97), (cx - 6, y0 + 97)]
    poligono(tela, pts, PRETO)
    poligono(tela, [(x0, y0 + 81), (x0 + 36, y0 + 81), (cx + 5, y0 + 96), (cx - 5, y0 + 96)], ACO2)
    tela.ret(cx - 2, y0 + 81, 4, 13, FUNDO)
    tela.ret(cx - 1, y0 + 92 - (0 if abre < .5 else 2), 2, 4, ACO4 if abre < .5 else ACO3)
    tela.ret(cx - 1, y0 + 95, 2, 2, FUNDO if abre > .5 else ACO0)  # furo do bico
    return dict(bobina=(cx - 15, y0 + 42), agulha=(cx, y0 + 70 - lev), bico=(cx, y0 + 96),
                conector=(cx + 31, y0 + 20), tubo=(cx - 50, y0 + 4))


def spray(tela, cx, cy, gotas, t, vento=0.0):
    """Gotas de um spray: `gotas` = lista de (t_saida, i). Cada gota sai do
    bico num cone e é levada pelo ar para a direita (`vento` px/s)."""
    for te, i in gotas:
        a = t - te
        if a < 0 or a > 2.2: continue
        ang = math.radians(-24 + 48 * hsh(i, 1))
        v = 70 + 50 * hsh(i, 2)
        sub = min(a, .35)
        x = cx + math.sin(ang) * v * sub + vento * max(0.0, a - .15) * (.6 + .4 * hsh(i, 3))
        y = cy + math.cos(ang) * v * sub + 8 * max(0.0, a - .35) * hsh(i, 4)
        yield x, y, a, i


def injetor_mini(tela, cil, dy=0.0, aceso=False):
    """Injetor pequeno espetado no duto de admissão do `Cilindro` (x -42)."""
    top = MP.TOPO_CAMARA
    s = cil.s
    X = lambda x: cil.ox + x * s
    Y = lambda y: cil.oy + (y + dy) * s
    tela.ret(int(X(-46)) - 1, int(Y(top - 52)) - 1, int(8 * s) + 2, int(30 * s) + 2, PRETO)
    tela.ret(int(X(-46)), int(Y(top - 52)), int(8 * s), int(30 * s), AMARELO if aceso else ACO2)
    tela.ret(int(X(-46)), int(Y(top - 52)), 1, int(30 * s), ACO4)
    tela.ret(int(X(-44)), int(Y(top - 44)), int(4 * s), int(10 * s), LATAO)
    tela.ret(int(X(-43)), int(Y(top - 22)), max(1, int(2 * s)), max(2, int(4 * s)), ACO3)
    tela.ret(int(X(-42)) - 1, int(Y(top - 56)), int(3 * s) + 1, int(4 * s), ACO0)
    return (X(-42), Y(top - 18))


def spray_mini(tela, cil, t, forca):
    """Jato pequeno saindo do injetor mini em direção à válvula de admissão."""
    if forca <= 0: return
    top = MP.TOPO_CAMARA
    s = cil.s
    for i in range(14):
        u = (i / 14 + t * 1.7) % 1.0
        if hsh(i, 5) > forca: continue
        x = -42 + u * 26 + (hsh(i, 6) - .5) * 6 * u
        y = top - 18 + u * 12 + (hsh(i, 7) - .5) * 4 * u
        tela.px(cil.ox + x * s, cil.oy + y * s, CHAMA0 if i % 3 else GASOLINA)


# ======================================================================= ignição
def bateria(tela, x, y, w=62, h=46):
    contorno_ret(tela, x, y, w, h, ACO0)
    dither(tela, x + 1, y + 1, w - 2, h - 2, FUNDO3, ACO0)
    tela.ret(x, y, w, 2, ACO2)
    contorno_ret(tela, x + 8, y - 6, 10, 6, VERMELHO)
    contorno_ret(tela, x + w - 18, y - 6, 10, 6, ACO2)
    tela.texto('+', x + 10, y + 6, VERMELHO, tam=9)
    tela.texto('-', x + w - 16, y + 6, ACO3, tam=9)
    tela.texto('12 V', x + w // 2, y + 18, AMARELO, tam=17, centro=True, contorno=PRETO)
    return (x + 13, y - 6), (x + w - 13, y - 6)


def bobina(tela, x, y, w, h, carga, disparo, t):
    """Bobina de ignição em corte: núcleo de ferro (quadro), primário à
    esquerda (5 voltas grossas), secundário à direita (muitas voltas finas).
    `carga` 0..1 = campo crescendo; `disparo` 0..1 = pulso de alta tensão."""
    e = 10
    contorno_ret(tela, x, y, w, h, ACO1)
    tela.ret(x + e, y + e, w - 2 * e, h - 2 * e, FUNDO)
    dither(tela, x + 1, y + 1, w - 2, e - 1, ACO1, ACO2)
    dither(tela, x + 1, y + h - e, w - 2, e - 1, ACO1, ACO0)
    tela.ret(x, y, w, 1, ACO3)
    # linhas do campo magnético dentro do núcleo (acendem com a carga)
    if carga > .05:
        n = int(carga * 4 + .5)
        for k in range(n):
            m = 3 + k * 3
            per = 2 * ((w - 2 * m) + (h - 2 * m))
            for j in range(0, per, 6):
                p = (j + t * 40) % per
                ww, hh = w - 2 * m, h - 2 * m
                if p < ww: px_, py_ = x + m + p, y + m
                elif p < ww + hh: px_, py_ = x + m + ww, y + m + p - ww
                elif p < 2 * ww + hh: px_, py_ = x + m + ww - (p - ww - hh), y + m + hh
                else: px_, py_ = x + m, y + m + hh - (p - 2 * ww - hh)
                if e - 1 <= px_ - x <= w - e or e - 1 <= py_ - y <= h - e:
                    tela.px(px_, py_, CIANO if k < 2 else AGUA1)
    # primário: perna esquerda, 5 voltas grossas
    for k in range(5):
        yy = y + 16 + k * int((h - 32) / 4.6)
        cor = AMARELO if carga > .2 and (k + int(t * 12)) % 5 == 0 else LATAO
        contorno_ret(tela, x - 5, yy, e + 10, 4, cor)
    # secundário: perna direita, voltas finas coladas
    xs = x + w - e - 6
    for k in range(0, h - 20, 2):
        yy = y + 10 + k
        cor = (BRANCO if k % 4 == 0 else AMARELO) if disparo > .1 else (LATAO if k % 4 == 0 else OLEO1)
        tela.ret(xs, yy, e + 12, 1, cor)
    tela.ret(xs - 1, y + 9, 1, h - 18, PRETO)
    tela.ret(xs + e + 12, y + 9, 1, h - 18, PRETO)
    return dict(primario=(x - 5, y + h // 2), secundario=(xs + e + 12, y + h // 2),
                saida=(xs + e + 6, y + 10), entrada=(x - 5, y + 18), volta=(x - 5, y + h - 18))


def vela_grande(tela, cx, y0, faisca, t):
    """Vela de ignição em pé: terminal, cerâmica com anéis, sextavado,
    rosca, eletrodo central e o eletrodo terra em L. Folga de 6 px."""
    contorno_ret(tela, cx - 3, y0, 6, 6, ACO3)                 # terminal
    contorno_ret(tela, cx - 8, y0 + 6, 16, 50, CERAMICA)        # isolador
    tela.ret(cx - 8, y0 + 6, 2, 50, BRANCO)
    tela.ret(cx + 5, y0 + 6, 3, 50, ACO3)
    for k in range(5):
        tela.ret(cx - 8, y0 + 10 + k * 8, 16, 1, ACO3)
    contorno_ret(tela, cx - 13, y0 + 56, 26, 14, ACO2)          # sextavado
    tela.ret(cx - 13, y0 + 56, 26, 2, ACO4)
    tela.ret(cx - 4, y0 + 56, 1, 14, ACO1); tela.ret(cx + 4, y0 + 56, 1, 14, ACO1)
    contorno_ret(tela, cx - 10, y0 + 70, 20, 30, ACO1)          # rosca
    for k in range(0, 30, 3):
        tela.ret(cx - 10, y0 + 70 + k, 20, 1, ACO3)
        tela.ret(cx - 11, y0 + 71 + k, 1, 1, ACO0); tela.ret(cx + 10, y0 + 71 + k, 1, 1, ACO0)
    contorno_ret(tela, cx - 2, y0 + 100, 4, 8, ACO3)            # eletrodo central
    tela.ret(cx - 2, y0 + 106, 4, 2, ACO4)
    # eletrodo terra: desce do lado e dobra por baixo do central
    tela.ret(cx + 7, y0 + 100, 4, 18, PRETO)
    tela.ret(cx + 8, y0 + 100, 2, 17, ACO2)
    tela.ret(cx - 4, y0 + 114, 15, 4, PRETO)
    tela.ret(cx - 3, y0 + 115, 13, 2, ACO2)
    folga = (y0 + 108, y0 + 114)
    if faisca > 0:
        a, b = folga
        tela.disco(cx, (a + b) / 2, 4 + 4 * faisca, CHAMA2 if faisca < .5 else CHAMA1)
        tela.disco(cx, (a + b) / 2, 2 + 3 * faisca, CHAMA0)
        xx = cx
        for yy in range(a, b + 1):
            xx = cx + int((hsh(yy, int(t * 30)) - .5) * 4)
            tela.ret(xx - 1, yy, 2, 1, BRANCO)
        for k in range(5):
            ang = k * 1.26 + t * 20
            tela.linha(cx, (a + b) / 2, cx + math.cos(ang) * 9 * faisca, (a + b) / 2 + math.sin(ang) * 7 * faisca, AMARELO)
    return dict(ceramica=(cx - 8, y0 + 30), rosca=(cx - 10, y0 + 85), folga=(cx - 3, (folga[0] + folga[1]) // 2),
                terminal=(cx, y0))


def fio(tela, pts, cor=ACO0, cor2=ACO2):
    for (a, b), (c, d) in zip(pts, pts[1:]):
        linha_grossa(tela, a, b, c, d, 3, PRETO)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        tela.linha(a, b, c, d, cor2)


def ponto_no_caminho(pts, u):
    """Ponto a fração u (0..1) do comprimento de uma linha quebrada."""
    seg = [math.hypot(c - a, d - b) for (a, b), (c, d) in zip(pts, pts[1:])]
    L = sum(seg) * (u % 1.0)
    for ((a, b), (c, d)), s in zip(zip(pts, pts[1:]), seg):
        if L <= s or s == seg[-1]:
            k = L / max(s, 1e-6)
            return a + (c - a) * min(1, k), b + (d - b) * min(1, k)
        L -= s
    return pts[-1]


def comprimento(pts):
    return sum(math.hypot(c - a, d - b) for (a, b), (c, d) in zip(pts, pts[1:]))


# ======================================================================= arrefecimento
def radiador(tela, x, y, w, h, quente, fluxo, t):
    """Radiador: caixa de cima, colmeia de tubos e aletas, caixa de baixo.
    `quente` 0..1 pinta a água que chega; `fluxo` liga o movimento."""
    contorno_ret(tela, x, y, w, 10, ACO1)
    tela.ret(x, y, w, 1, ACO3)
    contorno_ret(tela, x, y + h - 10, w, 10, ACO1)
    tela.ret(x - 1, y + 10, w + 2, h - 20, PRETO)
    for k in range(0, w, 4):
        tela.ret(x + k, y + 10, 2, h - 20, FUNDO2)
        for j in range(y + 10, y + h - 10):
            v = (j - y - 10) / (h - 20)
            if quente * (1 - v) > .55: c = LARANJA
            elif quente * (1 - v) > .3: c = BRASA
            else: c = AGUA0 if (j + k) % 3 else AGUA1
            tela.px(x + k, j, c)
        if fluxo > 0:
            yy = y + 10 + ((t * 26 * fluxo + k * 7) % (h - 20))
            tela.px(x + k, yy, BRANCO)
        tela.ret(x + k + 2, y + 10, 1, h - 20, ACO0)
    for j in range(y + 12, y + h - 10, 3):                      # aletas
        tela.ret(x + 1, j, w - 2, 1, ACO0)
    return dict(topo=(x + w // 2, y + 4), meio=(x + w, y + h // 2), base=(x + w // 2, y + h - 4))


def bomba(tela, cx, cy, r, ang):
    tela.disco(cx, cy, r + 1, PRETO)
    tela.disco(cx, cy, r, ACO1)
    tela.disco(cx, cy, r - 2, FUNDO2)
    for k in range(4):
        a = ang + k * math.pi / 2
        tela.linha(cx, cy, cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2), ACO3)
    tela.disco(cx, cy, 1.5, LATAO)


# ======================================================================= flex
def mistura_cor(xx, yy, frac_etanol):
    """Cor do líquido: pontilhado entre gasolina e etanol na proporção certa."""
    return ETANOL if BAYER8[yy % 8, xx % 8] < frac_etanol else GASOLINA


def tanque(tela, x, y, w, h, nivel, frac, t):
    """Tanque em corte com nível 0..1 e fração de etanol 0..1."""
    tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
    tela.ret(x - 1, y - 1, w + 2, h + 2, ACO2)
    tela.ret(x, y, w, h, FUNDO)
    ytopo = int(y + h * (1 - nivel))
    onda = [int(math.sin(t * 3 + k * .4) * 1.2) for k in range(w)]
    for xx in range(w):
        y0 = ytopo + onda[xx]
        for yy in range(max(y, y0), y + h):
            tela.buf[yy, x + xx] = mistura_cor(x + xx, yy, frac)
        if y <= y0 < y + h: tela.buf[y0, x + xx] = CHAMA0
    for k in range(6):                                          # bolhas
        u = (t * .5 + hsh(k, 9)) % 1.0
        by = y + h - 3 - u * (y + h - ytopo - 4)
        if by > ytopo + 2:
            tela.px(x + 6 + hsh(k, 8) * (w - 12), by, BRANCO)
    tela.ret(x + 1, y + 1, 1, h - 2, ACO3)
    return ytopo
