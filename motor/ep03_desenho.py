#!/usr/bin/env python3
"""ep03 — as peças desenhadas da jornada da mala (pixel art por geometria).

Tudo é genérico: avião sem pintura de companhia, aeroporto sem nome, códigos
de exemplo. Cada objeto recebe a posição e o instante `t` (para o que se mexe
sozinho: rodinha, luz piscando, etiqueta balançando).

  caixa(...)            retângulo com contorno, luz em cima e sombra pontilhada
  mala_lado / mala_frente / mala_topo     a mala (a protagonista é 'prota')
  etiqueta_mini         a etiqueta pendurada na alça
  barras_i25            o código de barras de verdade (Interleaved 2 of 5)
  esteira / rampa       esteira reta e inclinada, com a lona andando
  fundo_bastidor        a área de malas por trás do saguão (vigas, lâmpadas)
  ld3 / carrinho / trator / elevador / fuselagem / aviao   o lado de fora
  funcionario / silhueta  gente genérica, sem rosto
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)

# (base, luz, sombra)
CORES = {
    'prota': (CHAMA2, LARANJA, BRASA),
    'azul': (MISTURA, MISTURA2, FUNDO3),
    'verde': (AGUA1, VERDE, AGUA0),
    'roxo': (ROXO, ROSA, GAS2),
    'cinza': (ACO1, ACO3, ACO0),
    'marrom': (LATAO, OLEO1, OLEO0),
    'grafite': (GAS, ACO2, GAS2),
}
OUTRAS = ['azul', 'verde', 'roxo', 'cinza', 'marrom', 'grafite']


def outra(i):
    return OUTRAS[(i * 7 + 3) % len(OUTRAS)]


# ===================================================================== básico
def caixa(tela, x, y, w, h, base, luz, sombra, contorno=PRETO):
    """Peça com contorno escuro (cantos arredondados), luz no topo e na
    esquerda, sombra pontilhada embaixo."""
    x, y, w, h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
    if w < 4 or h < 4:
        tela.ret(x, y, w, h, base); return
    tela.ret(x + 1, y, w - 2, h, contorno); tela.ret(x, y + 1, w, h - 2, contorno)
    tela.ret(x + 1, y + 1, w - 2, h - 2, base)
    hs = max(1, (h - 2) // 3)
    dither(tela, x + 1, y + h - 1 - hs, w - 2, hs, base, sombra)
    tela.ret(x + 2, y + h - 2, w - 4, 1, sombra)
    tela.ret(x + 2, y + 1, w - 4, 1, luz)
    tela.ret(x + 1, y + 2, 1, h - 4, luz)


def cone_luz(tela, x, y0, y1, w0, w1, cor, so_em=None):
    """Facho de luz em xadrez (só pinta onde a cor de fundo é `so_em`)."""
    y0, y1 = max(0, int(y0)), min(PALCO_H, int(y1))
    if y1 <= y0: return
    ys = np.arange(y0, y1)
    for yy in ys:
        u = (yy - y0) / max(1, (y1 - y0))
        hw = (w0 + (w1 - w0) * u) / 2
        a, b = max(0, int(x - hw)), min(W, int(x + hw))
        if b <= a: continue
        row = tela.buf[yy, a:b]
        xs = np.arange(a, b)
        m = (xs + yy) % 2 == 0
        if so_em is not None: m &= np.isin(row, so_em)
        row[m] = cor


def seta_baixo(tela, x, y, cor, tam=5):
    for k in range(tam):
        w = (tam - k) * 2 - 1
        tela.ret(int(x) - w // 2, int(y) + k, w, 1, cor)


def marcador(tela, x, y, t, texto=None, cor=AMARELO, xmax=296):
    """Setinha amarela que pula sobre a protagonista (o texto não passa de xmax)."""
    b = int(round(abs(math.sin(t * 4)) * 3))
    seta_baixo(tela, x, y - 7 - b, PRETO, 7)
    seta_baixo(tela, x, y - 6 - b, cor, 5)
    if texto:
        w = tela.largura_texto(texto, 9)
        xt = min(max(int(x), w // 2 + 2), xmax - w // 2 - 2)
        tela.texto(texto, xt, int(y - 19 - b), cor, tam=9, centro=True, contorno=PRETO)


# ===================================================================== etiqueta
I25 = {'0': 'NNWWN', '1': 'WNNNW', '2': 'NWNNW', '3': 'WWNNN', '4': 'NNWNW',
       '5': 'WNWNN', '6': 'NWWNN', '7': 'NNNWW', '8': 'WNNWN', '9': 'NWNWN'}
PLACA = '0042314159'          # número de exemplo: tipo 0, companhia 042, mala 314159
DESTINO = 'PXL'


def barras_i25(digs, n=2, w=5):
    """Elementos (é_barra, largura) do Interleaved 2 of 5: os dígitos ímpares
    viram as barras e os pares os espaços entre elas."""
    els = [(True, n), (False, n), (True, n), (False, n)]
    for a, b in zip(digs[0::2], digs[1::2]):
        for pa, pb in zip(I25[a], I25[b]):
            els.append((True, w if pa == 'W' else n))
            els.append((False, w if pb == 'W' else n))
    els += [(True, w), (False, n), (True, n)]
    return els


def largura_barras(digs, n=2, w=5):
    return sum(l for _, l in barras_i25(digs, n, w))


def desenhar_barras(tela, x, y, h, digs=PLACA, n=2, w=5, cor=PRETO, ate=None):
    xx = x
    for barra, l in barras_i25(digs, n, w):
        if ate is not None and xx >= ate: break
        if barra: tela.ret(xx, y, l, h, cor)
        xx += l
    return xx - x


def etiqueta_mini(tela, x, y, t, balanco=0.0, s=1):
    """Etiqueta pendurada (x, y = ponto da alça). Balança com `balanco`."""
    dx = int(round(math.sin(t * 3.1) * balanco))
    tx, ty = x + 2 + dx, y + 2
    tela.linha(x, y, tx + 2, ty, CERAMICA)
    w, h = 6 * s, 9 * s
    tela.ret(tx - 1, ty - 1, w + 2, h + 2, PRETO)
    tela.ret(tx, ty, w, h, CERAMICA)
    tela.ret(tx, ty, w, 2 * s, VERDE)
    for k in range(3):
        tela.ret(tx + 1, ty + 3 * s + k * 2 * s, w - 2, s, PRETO)


# ===================================================================== a mala
def mala_lado(tela, x, yb, w=30, h=12, cor='prota', t=0.0, tag=False, alca=True, rodas=True, balanco=1.0):
    """Mala deitada vista de lado. (x, yb) = canto esquerdo de baixo."""
    base, luz, sombra = CORES[cor]
    x, yb = int(round(x)), int(round(yb))
    y = yb - h
    if rodas:
        tela.ret(x + w - 1, y + 1, 3, 3, PRETO); tela.ret(x + w - 1, yb - 4, 3, 3, PRETO)
        tela.px(x + w, y + 2, ACO1); tela.px(x + w, yb - 3, ACO1)
    caixa(tela, x, y, w, h, base, luz, sombra)
    n = max(2, w // 7)
    for k in range(1, n):
        xx = x + int(k * w / n)
        tela.ret(xx, y + 2, 1, h - 4, sombra)
        tela.ret(xx - 1, y + 2, 1, h - 4, luz) if h > 9 else None
    tela.ret(x + 1, y + h // 2, w - 2, 1, PRETO)                     # zíper entre as duas cascas
    tela.ret(x + 2, y + h // 2 - 1, w - 4, 1, sombra)
    for cx_, cy_ in ((x + 1, y + 1), (x + w - 3, y + 1), (x + 1, yb - 3), (x + w - 3, yb - 3)):
        tela.ret(cx_, cy_, 2, 2, ACO0)
    if alca:
        cx = x + w // 2
        tela.ret(cx - 4, y - 3, 9, 1, PRETO); tela.ret(cx - 4, y - 2, 1, 2, PRETO); tela.ret(cx + 4, y - 2, 1, 2, PRETO)
        tela.ret(cx - 3, y - 2, 7, 1, ACO1)
        if tag: etiqueta_mini(tela, cx + 4, y - 2, t, balanco)


def mala_frente(tela, cx, yb, s=1.0, cor='prota', t=0.0, puxador=0.0, tag=True, balanco=1.0):
    """Mala em pé, de frente (balcão, chegada). (cx, yb) = meio, chão."""
    base, luz, sombra = CORES[cor]
    w, h = int(round(24 * s)), int(round(32 * s))
    x, y = int(round(cx - w / 2)), int(round(yb - h - 3 * s))
    # puxador telescópico
    if puxador > 0:
        alto = int(round(14 * s * puxador))
        for xx in (x + int(6 * s), x + w - int(7 * s)):
            tela.ret(xx, y - alto, 2, alto, PRETO); tela.px(xx, y - alto, ACO2)
            tela.ret(xx, y - alto + 1, 1, alto - 1, ACO2)
        tela.ret(x + int(5 * s), y - alto - 3, w - int(10 * s), 4, PRETO)
        tela.ret(x + int(6 * s), y - alto - 2, w - int(12 * s), 2, ACO1)
    # rodinhas
    for wx in (x + int(4 * s), x + w - int(4 * s)):
        tela.disco(wx, yb - 2 * s, 2.6 * s, PRETO)
        tela.disco(wx, yb - 2 * s, 1.0 * s, ACO1)
        a = t * 6
        tela.px(wx + math.cos(a) * 1.5 * s, yb - 2 * s + math.sin(a) * 1.5 * s, ACO2)
    caixa(tela, x, y, w, h, base, luz, sombra)
    for k in (1, 2, 3):                                    # frisos da casca
        xx = x + int(k * w / 4)
        tela.ret(xx, y + 3, 1, h - 6, sombra)
        tela.ret(xx - 1, y + 3, 1, h - 6, luz)
    for cx_, cy_ in ((x + 1, y + 1), (x + w - 3, y + 1), (x + 1, y + h - 3), (x + w - 3, y + h - 3)):
        tela.ret(cx_, cy_, 2, 2, ACO0)
    # alça de cima
    ax = x + w // 2
    tela.ret(ax - 4, y - 3, 9, 1, PRETO); tela.ret(ax - 4, y - 2, 1, 2, PRETO); tela.ret(ax + 4, y - 2, 1, 2, PRETO)
    tela.ret(ax - 3, y - 2, 7, 1, ACO1)
    if tag:
        etiqueta_mini(tela, ax + 4, y - 2, t, balanco, s=1 if s < 1.5 else 2)
    return x, y, w, h


def mala_topo(tela, cx, cy, w=14, h=10, cor='azul', t=0.0, tag=False):
    """Mala vista de cima (triagem)."""
    base, luz, sombra = CORES[cor]
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    caixa(tela, x, y, w, h, base, luz, sombra)
    tela.ret(x + 1, y + h // 2, w - 2, 1, sombra)
    tela.ret(x + w // 2 - 3, y + 2, 6, 2, PRETO); tela.ret(x + w // 2 - 2, y + 2, 4, 1, ACO1)
    if tag:
        tela.ret(x + w // 2 + 3, y + 3, 4, 5, PRETO); tela.ret(x + w // 2 + 4, y + 4, 2, 3, CERAMICA)


# ===================================================================== esteiras
def esteira(tela, x0, x1, y, t, vel=30.0, chao=None, pernas=48, fase=0):
    """Esteira reta vista de lado, lona no topo em y. `vel` px/s (sinal = sentido)."""
    x0, x1, y = int(x0), int(x1), int(y)
    L = x1 - x0
    if L <= 4: return
    if chao:
        for xx in range(x0 + 10 + fase % pernas, x1 - 4, pernas):
            tela.ret(xx, y + 9, 4, chao - y - 9, PRETO)
            tela.ret(xx + 1, y + 9, 2, chao - y - 9, FUNDO3)
            tela.ret(xx + 1, y + 9, 1, chao - y - 9, TRACO)
            tela.ret(xx - 2, chao - 2, 8, 2, ACO0)
    tela.ret(x0, y - 1, L, 11, PRETO)
    tela.ret(x0 + 1, y, L - 2, 1, ACO1)
    tela.ret(x0 + 1, y + 1, L - 2, 2, ACO0)
    off = (t * vel) % 8
    for k in range(-1, L // 8 + 2):
        xx = x0 + int(k * 8 + off)
        if x0 + 1 <= xx < x1 - 2: tela.ret(xx, y, 1, 3, FUNDO3)
    tela.ret(x0 + 1, y + 4, L - 2, 5, TRACO)
    dither(tela, x0 + 1, y + 6, L - 2, 3, TRACO, FUNDO3)
    tela.ret(x0 + 1, y + 4, L - 2, 1, ACO0)
    for xx in range(x0 + 6, x1 - 3, 16):
        tela.px(xx, y + 6, ACO2)
    for rx in (x0 + 3, x1 - 4):
        tela.disco(rx, y + 2, 2.5, ACO1)
        a = t * vel / 3.0
        tela.px(rx + math.cos(a) * 1.6, y + 2 + math.sin(a) * 1.6, ACO3)


def rampa(tela, xa, ya, xb, yb, t, vel=30.0, esp=4):
    """Esteira inclinada de (xa, ya) a (xb, yb) (pontos do topo da lona)."""
    L = math.hypot(xb - xa, yb - ya) or 1
    nx, ny = -(yb - ya) / L, (xb - xa) / L
    if ny < 0: nx, ny = -nx, -ny
    linha_grossa(tela, xa + nx * 6, ya + ny * 6, xb + nx * 6, yb + ny * 6, 9, PRETO)
    linha_grossa(tela, xa + nx * 6, ya + ny * 6, xb + nx * 6, yb + ny * 6, 5, TRACO)
    linha_grossa(tela, xa + nx * 2, ya + ny * 2, xb + nx * 2, yb + ny * 2, esp + 2, PRETO)
    linha_grossa(tela, xa + nx * 2, ya + ny * 2, xb + nx * 2, yb + ny * 2, esp, ACO0)
    tela.linha(xa, ya, xb, yb, ACO1)
    off = (t * vel) % 8
    for k in range(0, int(L // 8) + 1):
        u = (k * 8 + off) / L
        if 0 <= u <= 1:
            tela.px(xa + (xb - xa) * u + nx, ya + (yb - ya) * u + ny, FUNDO3)


def cortina(tela, x, y, w, h, t, empurra=0.0, lado=1):
    """Cortina de tiras (a boca do túnel). `empurra` 0..1 abre as tiras."""
    tela.ret(x - 2, y - 3, w + 4, 3, ACO1); tela.ret(x - 2, y - 3, w + 4, 1, ACO3)
    n = max(3, w // 4)
    for k in range(n):
        xx = x + k * w / n
        for yy in range(h):
            u = yy / max(1, h - 1)
            d = empurra * u * u * 6 * lado + math.sin(t * 2 + k) * .4 * u
            cor = ACO2 if k % 2 else ACO1
            tela.px(xx + d, y + yy, cor)
            tela.px(xx + d + 1, y + yy, FUNDO3 if k % 2 else ACO0)


def fundo_bastidor(tela, t, scroll=0.0, chao=196):
    """Bastidores do aeroporto: parede escura, viga, canos e lâmpadas."""
    tela.buf[:PALCO_H] = FUNDO2
    dither(tela, 0, 0, W, 24, FUNDO, FUNDO2)
    tela.ret(0, 0, W, 10, FUNDO)
    for y in range(52, chao, 36):
        tela.ret(0, y, W, 1, FUNDO3)
    # luz das lâmpadas na parede
    for k in range(-1, 6):
        x = int(k * 130 + 70 - (scroll * .6) % 130)
        cone_luz(tela, x, 30, chao, 10, 70, FUNDO3, so_em=[FUNDO2])
    # treliça do teto
    tela.ret(0, 12, W, 3, FUNDO3); tela.ret(0, 12, W, 1, TRACO); tela.ret(0, 4, W, 1, FUNDO3)
    o = int((scroll * .6) % 16)
    for x in range(-o, W, 16):
        tela.linha(x, 5, x + 8, 12, FUNDO3); tela.linha(x + 8, 12, x + 16, 5, FUNDO3)
    # cano
    tela.ret(0, 38, W, 5, PRETO); tela.ret(0, 39, W, 3, TRACO); tela.ret(0, 39, W, 1, ACO0)
    o2 = int((scroll * .6) % 40)
    for x in range(-o2, W, 40):
        tela.ret(x, 37, 3, 7, ACO0)
    # colunas
    for k in range(-1, 5):
        x = int(k * 130 + 10 - (scroll * .6) % 130)
        tela.ret(x, 15, 12, chao - 15, PRETO)
        tela.ret(x + 1, 15, 10, chao - 15, FUNDO3)
        tela.ret(x + 2, 15, 1, chao - 15, TRACO)
        tela.ret(x + 9, 15, 1, chao - 15, FUNDO)
        tela.ret(x - 2, chao - 4, 16, 4, TRACO)
        for yy in range(30, chao - 10, 30):
            tela.px(x + 5, yy, ACO0); tela.px(x + 6, yy, ACO0)
    # lâmpadas
    for k in range(-1, 6):
        x = int(k * 130 + 70 - (scroll * .6) % 130)
        tela.ret(x, 15, 1, 10, ACO0)
        poligono(tela, [(x - 7, 29), (x + 8, 29), (x + 5, 24), (x - 4, 24)], ACO1)
        tela.ret(x - 4, 24, 9, 1, ACO2)
        tela.ret(x - 5, 29, 11, 1, CHAMA0)
    # piso com faixa de segurança
    tela.ret(0, chao, W, PALCO_H - chao, FUNDO3)
    dither(tela, 0, chao + 4, W, PALCO_H - chao - 4, FUNDO3, FUNDO2)
    o3 = int(scroll % 12)
    for x in range(-o3, W, 12):
        tela.ret(x, chao, 6, 2, AMARELO); tela.ret(x + 6, chao, 6, 2, PRETO)


def ceu_noite(tela, t, estrelas, horizonte=110):
    tela.buf[:PALCO_H] = FUNDO
    dither(tela, 0, 40, W, 30, FUNDO, FUNDO2)
    tela.ret(0, 70, W, horizonte - 70, FUNDO2)
    dither(tela, 0, horizonte - 22, W, 22, FUNDO2, FUNDO3)
    dither(tela, 0, horizonte - 6, W, 6, FUNDO3, ROXO)
    for x, y, f in estrelas:
        if y < horizonte - 20 and math.sin(t * 1.7 + f) > -.4:
            tela.px(x, y, BRANCO if f > 4.5 else ACO2)


# ===================================================================== lado de fora
def ld3(tela, x, yb, w=32, h=26, porta='fechada', t=0.0, malas=None, nome=True):
    """Contêiner LD3 (AKE): o topo é mais largo que a base; o canto de baixo
    é chanfrado para encaixar na curva do porão. `porta` = 'fechada',
    'aberta' (mostra as malas) ou 'rede' (malas atrás da rede)."""
    x, yb = int(round(x)), int(round(yb))
    bw = int(round(w * .78))
    kink = yb - int(h * .48)
    top = yb - h

    def borda_dir(y):                      # x da parede direita na altura y
        if y <= kink: return x + w
        return x + bw + (w - bw) * (yb - y) / max(1, yb - kink)

    pts = [(x, top), (x + w, top), (x + w, kink), (x + bw, yb), (x, yb)]
    pts_o = [(x - 1, top - 1), (x + w + 1, top - 1), (x + w + 1, kink), (x + bw + 1, yb + 1), (x - 1, yb + 1)]
    poligono(tela, pts_o, PRETO)
    poligono(tela, pts, ACO1)
    if porta in ('aberta', 'rede'):
        poligono(tela, [(x + 2, top + 2), (x + w - 2, top + 2), (x + w - 2, kink), (x + bw - 1, yb - 2), (x + 2, yb - 2)], FUNDO)
        if malas:
            mw = max(4, (w - 6) // 3 - 1)
            k = 0
            for j in range(3):
                my = yb - 3 - j * 7
                for i in range(3):
                    if k >= len(malas): break
                    mx = x + 3 + i * (mw + 1)
                    if mx + mw > borda_dir(my) - 2 or my - 6 < top + 2: continue
                    b, l, s_ = CORES[malas[k]]
                    tela.ret(mx, my - 6, mw, 6, PRETO)
                    tela.ret(mx + 1, my - 5, mw - 2, 4, b)
                    tela.ret(mx + 1, my - 5, mw - 2, 1, l)
                    tela.ret(mx + 1, my - 2, mw - 2, 1, s_)
                    k += 1
        if porta == 'rede':
            for yy in range(top + 4, yb - 1, 4):
                tela.ret(x + 2, yy, int(borda_dir(yy)) - x - 4, 1, LATAO)
            for xx in range(x + 4, x + w - 2, 5):
                yr = yb - 2
                if xx > x + bw:
                    yr = kink + int((yb - kink) * (x + w - xx) / max(1, w - bw))
                tela.ret(xx, top + 2, 1, yr - top - 2, LATAO)
    else:
        dither(tela, x + 2, top + 2 + (h - 4) // 2, bw - 2, (h - 4) // 2, ACO1, ACO0)
        for xx in range(x + 5, x + w - 3, 5):
            yr = yb - 2
            if xx > x + bw:
                yr = kink + int((yb - kink) * (x + w - xx) / max(1, w - bw))
            tela.ret(xx, top + 3, 1, yr - top - 4, ACO0)
            tela.ret(xx + 1, top + 3, 1, max(1, (yr - top - 4) // 2), ACO2)
    # moldura de alumínio
    tela.ret(x, top, w + 1, 2, ACO3); tela.ret(x, top, w + 1, 1, ACO4)
    tela.ret(x, yb - 1, bw + 1, 2, ACO0)
    tela.ret(x, top, 2, h, ACO2)
    tela.ret(x + w - 1, top, 2, kink - top, ACO2)
    tela.linha(x + w, kink, x + bw, yb, ACO3)
    if nome and w >= 30 and porta == 'fechada':
        tela.ret(x + 4, top + 4, 17, 7, PRETO)
        tela.ret(x + 5, top + 5, 15, 5, CERAMICA)
        for k in range(4):
            tela.ret(x + 6 + k * 4, top + 6, 2, 3, PRETO)


def carrinho(tela, x, yb, w=40, t=0.0, vel=0.0):
    """Carreta (dolly) de contêiner: deck com roletes e 4 rodinhas."""
    x, yb = int(round(x)), int(round(yb))
    tela.ret(x, yb, w, 5, PRETO); tela.ret(x + 1, yb + 1, w - 2, 2, ACO1); tela.ret(x + 1, yb + 1, w - 2, 1, ACO2)
    for xx in range(x + 3, x + w - 2, 5): tela.px(xx, yb + 1, ACO4)
    tela.ret(x - 10, yb + 3, 11, 2, PRETO); tela.ret(x - 10, yb + 3, 10, 1, ACO0)
    for wx in (x + 6, x + w - 7):
        tela.disco(wx, yb + 8, 3.6, PRETO); tela.disco(wx, yb + 8, 1.4, ACO2)
        a = -vel * t / 3.6
        tela.px(wx + math.cos(a) * 2.4, yb + 8 + math.sin(a) * 2.4, ACO1)


def trator(tela, x, yb, t=0.0, vel=0.0):
    """Trator de bagagem genérico (amarelo), virado para a direita. (x, yb) = traseira, chão."""
    x, yb = int(round(x)), int(round(yb))
    # chassi
    poligono(tela, [(x - 1, yb - 7), (x + 37, yb - 7), (x + 41, yb - 13), (x + 41, yb - 3), (x - 1, yb - 3)], PRETO)
    caixa(tela, x + 18, yb - 18, 24, 13, AMARELO, CHAMA0, LATAO)          # capô
    caixa(tela, x, yb - 12, 22, 9, AMARELO, CHAMA0, LATAO)
    # cabine aberta: colunas e teto
    tela.ret(x + 2, yb - 34, 2, 22, PRETO); tela.ret(x + 16, yb - 34, 2, 22, PRETO)
    tela.ret(x + 2, yb - 34, 1, 22, ACO1); tela.ret(x + 16, yb - 34, 1, 22, ACO1)
    tela.ret(x, yb - 36, 20, 3, PRETO); tela.ret(x + 1, yb - 35, 18, 1, ACO2)
    tela.ret(x + 5, yb - 20, 8, 8, FUNDO3); tela.ret(x + 5, yb - 20, 8, 1, ACO0)         # banco
    tela.linha(x + 14, yb - 22, x + 19, yb - 18, PRETO)                                    # volante
    tela.ret(x + 40, yb - 15, 2, 3, CHAMA0)                                                # farol
    tela.ret(x - 2, yb - 7, 3, 2, PRETO)                                                   # engate
    for k in range(3): tela.ret(x + 22 + k * 5, yb - 16, 1, 6, LATAO)
    # giroflex
    pisca = int(t * 3) % 2 == 0
    tela.ret(x + 8, yb - 39, 4, 3, CHAMA1 if pisca else BRASA)
    if pisca: tela.px(x + 9, yb - 39, CHAMA0)
    for wx, r in ((x + 8, 5.5), (x + 34, 4.6)):
        tela.disco(wx, yb - 1, r, PRETO); tela.disco(wx, yb - 1, r * .45, ACO2)
        a = -vel * t / r
        tela.px(wx + math.cos(a) * r * .75, yb - 1 + math.sin(a) * r * .75, ACO1)


def elevador(tela, x, yb, ytopo, w=60):
    """Elevador de contêiner (tesoura). `ytopo` = altura do piso da plataforma."""
    x, yb, ytopo = int(x), int(yb), int(ytopo)
    # base
    caixa(tela, x - 4, yb - 10, w + 8, 9, ACO1, ACO3, ACO0)
    for k in range(0, w + 8, 8):
        tela.ret(x - 3 + k, yb - 9, 4, 1, AMARELO)
    for wx in (x + 4, x + w - 4):
        tela.disco(wx, yb, 4, PRETO); tela.disco(wx, yb, 1.6, ACO2)
    # tesoura
    y0, y1 = ytopo + 5, yb - 10
    if y1 - y0 > 3:
        for a, b in ((x + 6, x + w - 6), (x + w - 6, x + 6)):
            linha_grossa(tela, a, y0, b, y1, 4, PRETO)
            linha_grossa(tela, a, y0, b, y1, 2, ACO2)
        tela.disco(x + w / 2, (y0 + y1) / 2, 2, ACO3)
    # plataforma com roletes e guarda-corpo
    tela.ret(x - 1, ytopo, w + 2, 6, PRETO)
    tela.ret(x, ytopo + 1, w, 4, ACO1); tela.ret(x, ytopo + 1, w, 1, ACO3)
    for xx in range(x + 2, x + w - 1, 4): tela.px(xx, ytopo + 2, ACO4)
    for k in range(0, w, 6):
        tela.ret(x + k, ytopo + 4, 3, 1, AMARELO)


def fuselagem(tela, x0, t=0.0, porta=1.0, porta_x=172, porta_w=52, yc=78, R=46, luzes=True):
    """Lateral de um avião genérico de corpo largo, nariz à esquerda em x0.
    Sem pintura de companhia. `porta` 0..1 = quanto a porta do porão está aberta."""
    top, bot = yc - R, yc + R
    # corpo (até a borda da tela) com nariz em meia elipse
    pts = []
    for k in range(0, 19):
        a = math.pi / 2 + k * math.pi / 18
        pts.append((x0 + 52 + math.cos(a) * 52, yc + 4 - math.sin(a) * (R + 2) + (6 if math.sin(a) < 0 else 0) * abs(math.sin(a))))
    corpo = [(x0 + 52, top), (W + 4, top), (W + 4, bot), (x0 + 52, bot)]
    poligono(tela, [(x - 1 if x < x0 + 52 else x, y) for x, y in pts] + [(x0 + 52, bot + 1), (W + 4, bot + 1), (W + 4, top - 1), (x0 + 52, top - 1)], PRETO)
    poligono(tela, corpo, ACO3)
    poligono(tela, pts + [(x0 + 52, bot), (x0 + 52, top)], ACO3)
    # sombreado de baixo (pontilhado em degraus) — só dentro do corpo
    sub = tela.buf[yc + 10:bot, :]
    yy, xx = np.mgrid[yc + 10:bot, 0:W]
    dentro = sub == ACO3
    m1 = dentro & ((xx + yy) % 2 == 0)
    sub[m1] = ACO2
    sub2 = tela.buf[yc + 28:bot, :]
    yy2, xx2 = np.mgrid[yc + 28:bot, 0:W]
    m2 = np.isin(sub2, [ACO2, ACO3]) & ((xx2 + yy2) % 2 == 0)
    sub2[m2] = ACO1
    tela.ret(x0 + 52, top, W - x0 - 52, 1, ACO4)
    tela.ret(x0 + 40, top + 3, W - x0 - 40, 1, ACO4)
    # janelas de passageiros
    for k in range(12):
        wx = x0 + 96 + k * 13
        if wx > W: break
        tela.ret(wx - 1, yc - 21, 6, 8, PRETO)
        acesa = luzes and ((k * 5 + 2) % 7) != 0
        tela.ret(wx, yc - 20, 4, 6, CHAMA1 if acesa else FUNDO3)
        tela.ret(wx, yc - 20, 4, 2, CHAMA0 if acesa else TRACO)
    # cabine de comando
    poligono(tela, [(x0 + 14, yc - 18), (x0 + 30, yc - 30), (x0 + 44, yc - 32), (x0 + 44, yc - 22), (x0 + 18, yc - 14)], PRETO)
    poligono(tela, [(x0 + 17, yc - 18), (x0 + 30, yc - 28), (x0 + 42, yc - 30), (x0 + 42, yc - 23), (x0 + 19, yc - 16)], FUNDO3)
    tela.linha(x0 + 30, yc - 28, x0 + 30, yc - 20, PRETO)
    tela.linha(x0 + 22, yc - 21, x0 + 38, yc - 28, MISTURA2)
    # porta de passageiros
    tela.ret(x0 + 64, yc - 30, 18, 44, ACO2)
    tela.ret_vazado(x0 + 64, yc - 30, 18, 44, ACO1)
    tela.ret(x0 + 69, yc - 24, 8, 8, PRETO); tela.ret(x0 + 70, yc - 23, 6, 6, FUNDO3)
    # linha do piso / divisão porão
    tela.ret(x0 + 58, yc + 16, W - x0 - 58, 1, ACO1)
    # porta do porão (abre para cima)
    py0, ph = yc + 18, 28
    tela.ret(porta_x - 1, py0 - 1, porta_w + 2, ph + 2, PRETO)
    if porta > 0:
        tela.ret(porta_x, py0, porta_w, ph, FUNDO)
        dither(tela, porta_x, py0, porta_w, 8, FUNDO2, FUNDO)
        tela.ret(porta_x, py0 + ph - 3, porta_w, 3, ACO0)                   # piso de roletes do porão
        for xx in range(porta_x + 2, porta_x + porta_w, 4): tela.px(xx, py0 + ph - 3, ACO2)
        if luzes: tela.ret(porta_x + 4, py0 + 1, porta_w - 8, 1, CHAMA0)
        fecha = int(ph * (1 - porta))
        if fecha > 0:
            tela.ret(porta_x, py0, porta_w, fecha, ACO2); tela.ret(porta_x, py0 + fecha - 1, porta_w, 1, ACO0)
        # a folha aberta, para cima, vista de quina
        ab = int(10 * porta)
        if ab > 1:
            poligono(tela, [(porta_x - 2, py0 - 1), (porta_x + porta_w + 2, py0 - 1), (porta_x + porta_w + 6, py0 - 1 - ab), (porta_x + 2, py0 - 1 - ab)], PRETO)
            poligono(tela, [(porta_x - 1, py0 - 2), (porta_x + porta_w + 1, py0 - 2), (porta_x + porta_w + 4, py0 - 1 - ab + 1), (porta_x + 3, py0 - ab)], ACO2)
    else:
        tela.ret(porta_x, py0, porta_w, ph, ACO3)
        tela.ret_vazado(porta_x, py0, porta_w, ph, ACO1)
    # luzes: farol anticolisão em baixo
    if luzes and int(t * 1.3) % 2 == 0 and (t * 1.3) % 1 < .25:
        tela.disco(x0 + 150, bot + 1, 2, VERMELHO); tela.px(x0 + 150, bot + 1, CHAMA0)
    return top, bot


def trem_pouso(tela, x, ytopo, chao):
    tela.ret(x - 2, ytopo, 5, chao - ytopo - 8, PRETO)
    tela.ret(x - 1, ytopo, 3, chao - ytopo - 8, ACO2)
    tela.ret(x - 1, ytopo, 1, chao - ytopo - 8, ACO3)
    for dx in (-5, 5):
        tela.disco(x + dx, chao - 8, 8, PRETO)
        tela.disco(x + dx, chao - 8, 3.5, ACO1)
        tela.disco(x + dx, chao - 8, 1.5, ACO3)


def aviao(tela, x, yc, t=0.0, corte=None, s=1.0):
    """Avião genérico de lado (voando para a direita). x = cauda. `corte` =
    função que desenha o porão em corte, recebe (tela, x0, y0, x1, y1)."""
    L, R = 250 * s, 15 * s
    xn = x + L
    # deriva (cauda)
    poligono(tela, [(x - 1, yc - R - 34 * s), (x + 22 * s, yc - R - 34 * s), (x + 52 * s, yc - R + 1), (x + 10 * s, yc - R + 1)], PRETO)
    poligono(tela, [(x + 1, yc - R - 32 * s), (x + 21 * s, yc - R - 32 * s), (x + 49 * s, yc - R + 1), (x + 12 * s, yc - R + 1)], ACO2)
    tela.linha(x + 2, yc - R - 31 * s, x + 20 * s, yc - R - 31 * s, ACO3)
    # corpo
    corpo = [(x, yc - R + 4), (x + 30 * s, yc - R), (xn - 22 * s, yc - R), (xn - 8 * s, yc - R + 5 * s), (xn, yc + 2 * s),
             (xn - 8 * s, yc + R - 2 * s), (xn - 30 * s, yc + R), (x + 60 * s, yc + R), (x + 18 * s, yc + 2 * s), (x, yc - R + 9 * s)]
    poligono(tela, [(px + (1 if px > x + L / 2 else -1), py + (1 if py > yc else -1)) for px, py in corpo], PRETO)
    poligono(tela, corpo, ACO3)
    yy0 = int(yc + 4 * s)
    sub = tela.buf[yy0:int(yc + R + 1), :]
    yy, xx = np.mgrid[yy0:yy0 + sub.shape[0], 0:W]
    sub[(sub == ACO3) & ((xx + yy) % 2 == 0)] = ACO2
    tela.ret(x + 30 * s, yc - R, L - 52 * s, 1, ACO4)
    # janelas
    for k in range(int(36 * s)):
        wx = x + 50 * s + k * 5 * s
        if wx > xn - 30 * s: break
        tela.ret(wx, yc - 7 * s, 2, 3, CHAMA1); tela.px(wx, yc - 7 * s, CHAMA0)
    poligono(tela, [(xn - 20 * s, yc - 9 * s), (xn - 9 * s, yc - 8 * s), (xn - 6 * s, yc - 4 * s), (xn - 19 * s, yc - 5 * s)], FUNDO3)
    # porão em corte
    if corte:
        corte(tela, int(x + 172 * s), int(yc + 3 * s), int(x + 228 * s), int(yc + R - 2 * s))
    # asa (vista de lado: perfil fino descendo para trás) e motor
    poligono(tela, [(x + 160 * s, yc + 2 * s), (x + 120 * s, yc + 4 * s), (x + 84 * s, yc + 13 * s), (x + 100 * s, yc + 13 * s), (x + 170 * s, yc + 6 * s)], PRETO)
    poligono(tela, [(x + 158 * s, yc + 3 * s), (x + 121 * s, yc + 5 * s), (x + 90 * s, yc + 12 * s), (x + 101 * s, yc + 12 * s), (x + 167 * s, yc + 6 * s)], ACO1)
    caixa(tela, x + 130 * s, yc + 10 * s, 34 * s, 12 * s, ACO2, ACO4, ACO0)
    tela.ret(x + 163 * s, yc + 11 * s, 2, 10 * s, FUNDO); tela.ret(x + 129 * s, yc + 13 * s, 2, 6 * s, BRASA)
    # estabilizador
    poligono(tela, [(x + 10 * s, yc - 4 * s), (x + 42 * s, yc - 2 * s), (x + 20 * s, yc + 2 * s)], ACO1)
    # luzes de navegação
    if (t * 1.1) % 1 < .12:
        tela.disco(x + 4 * s, yc - R - 33 * s, 2, BRANCO)
    if (t * .9) % 1 < .3:
        tela.disco(x + 120 * s, yc - R - 1, 1.6, VERMELHO)
    tela.px(x + 88 * s, yc + 13 * s, VERDE)


# ===================================================================== gente genérica
def funcionario(tela, x, yb, t=0.0, lado=1, braco=0.0, anda=0.0, scanner=False):
    """Funcionário genérico de pátio (~60 px): colete refletivo, boné e
    protetor de ouvido, sem rosto. `braco` 0 = baixo, 1 = esticado à frente.
    Devolve a posição da mão."""
    x, yb = int(round(x)), int(round(yb))
    p = int(round(math.sin(anda * 7) * 2)) if anda else 0
    # braço de trás (mais escuro)
    linha_grossa(tela, x - lado * 4, yb - 45, x - lado * 5, yb - 28, 5, PRETO)
    linha_grossa(tela, x - lado * 4, yb - 45, x - lado * 5, yb - 28, 3, FUNDO3)
    # pernas e botas
    tela.ret(x - 7, yb - 25, 15, 22, PRETO)
    tela.ret(x - 6 + p, yb - 24, 6, 21, FUNDO3); tela.ret(x + 1 - p, yb - 24, 6, 21, FUNDO3)
    tela.ret(x - 6 + p, yb - 24, 1, 21, TRACO); tela.ret(x + 1 - p, yb - 24, 1, 21, TRACO)
    tela.ret(x, yb - 24, 1, 21, PRETO)
    for bx in (x - 7 + p + (1 if lado > 0 else -1), x + 1 - p + (1 if lado > 0 else -1)):
        tela.ret(bx, yb - 4, 8, 4, PRETO); tela.ret(bx + 1, yb - 4, 6, 1, ACO0)
    # tronco: camisa e colete refletivo
    tela.ret(x - 9, yb - 49, 18, 27, PRETO)
    tela.ret(x - 8, yb - 48, 16, 25, ACO0)
    tela.ret(x - 8, yb - 46, 16, 21, LARANJA)
    dither(tela, x - 8 if lado > 0 else x + 3, yb - 46, 5, 21, LARANJA, CHAMA2)
    tela.ret(x - 8, yb - 46, 16, 1, CHAMA1)
    for yy in (yb - 39, yb - 32):
        tela.ret(x - 8, yy, 16, 2, ACO3); tela.ret(x - 8, yy, 16, 1, ACO4)
    tela.ret(x, yb - 46, 1, 21, CHAMA2)
    tela.ret(x - 8, yb - 25, 16, 2, FUNDO3)                                   # cinto
    # pescoço e cabeça (boné, protetor de ouvido), sem feições
    tela.ret(x - 2, yb - 52, 4, 4, OLEO1)
    tela.ret(x - 6, yb - 62, 12, 12, PRETO)
    tela.ret(x - 5, yb - 61, 10, 10, OLEO1)
    tela.ret(x - 5 if lado > 0 else x + 1, yb - 57, 4, 6, LATAO)              # sombra do rosto
    tela.ret(x - 5, yb - 61, 10, 4, FUNDO3); tela.ret(x - 5, yb - 61, 10, 1, TRACO)
    tela.ret(x + (5 if lado > 0 else -8), yb - 58, 4, 2, FUNDO3)              # aba do boné
    tela.ret(x - lado * 2 - 2, yb - 58, 4, 6, ACO1); tela.ret(x - lado * 2 - 1, yb - 57, 2, 4, ACO2)
    # braço da frente
    sx, sy = x + lado * 4, yb - 45
    ang = math.radians(80 - 85 * braco)
    hx = sx + lado * math.cos(ang) * 19
    hy = sy + math.sin(ang) * 19
    linha_grossa(tela, sx, sy, hx, hy, 6, PRETO)
    linha_grossa(tela, sx, sy, hx, hy, 4, ACO0)
    tela.ret(int(hx) - 2, int(hy) - 2, 5, 5, PRETO); tela.ret(int(hx) - 1, int(hy) - 1, 3, 3, OLEO1)
    if scanner:
        bx = int(hx) + (1 if lado > 0 else -8)
        tela.ret(bx, int(hy) - 4, 8, 5, PRETO); tela.ret(bx + 1, int(hy) - 3, 6, 3, ACO1)
        tela.px(bx + (6 if lado > 0 else 1), int(hy) - 3, CIANO)
    return hx, hy


def silhueta(tela, x, yb, h=44, cor=FUNDO3, t=0.0, fase=0.0):
    """Pessoa genérica em silhueta (de costas, sem detalhe)."""
    x, yb = int(x), int(yb)
    b = int(round(math.sin(t * 1.3 + fase) * .6))
    r = h * .11
    tela.disco(x, yb - h + r + b, r, cor)
    poligono(tela, [(x - h * .17, yb), (x - h * .2, yb - h * .62 + b), (x - h * .12, yb - h * .74 + b),
                    (x + h * .12, yb - h * .74 + b), (x + h * .2, yb - h * .62 + b), (x + h * .17, yb)], cor)
