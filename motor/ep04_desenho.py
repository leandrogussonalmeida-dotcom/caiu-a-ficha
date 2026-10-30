#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep04 — o desenho: celular genérico, a imagem em níveis
de vermelho/verde/azul, o zoom até os subpixels e os cortes LCD e OLED.

A paleta do episódio é a `oficina` + 17 cores próprias (os subpixels em 4
níveis de brilho, as misturas puras e os pretos de LCD/OLED). Ela é
registrada como 'ep04' e o `longo` passa a usá-la neste processo.

A imagem da tela do celular é guardada como NÍVEIS (0..3 por canal), não
como cor: a vista de longe é a cor mais próxima da soma das três luzes, e a
vista de perto mostra as três listras com o brilho de cada canal. Longe e
perto saem da mesma conta, então nunca discordam.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, painel, BAYER8, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0,
                   ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, OLEO0, VERMELHO, CHAMA0,
                   LATAO, CERAMICA, AGUA0, AGUA1, ROXO, PRETO, MISTURA)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#2e0808', '#7a0000', '#c80000', '#ff1414',     # 32..35 vermelho, nível 0..3
          '#082e0c', '#007a10', '#00c81c', '#20ff30',     # 36..39 verde
          '#0a0a36', '#0c1e8c', '#1a3ae0', '#3a5cff',     # 40..43 azul
          '#ffff28', '#28ffff', '#ff28ff',                # 44..46 amarelo, ciano, magenta puros
          '#2a2a34', '#000000']                           # 47 preto de LCD (vaza), 48 preto de OLED
PX.PALETAS['ep04'] = _BASE + _EXTRA
LG.PAL = 'ep04'
SUB = np.array([[32, 33, 34, 35], [36, 37, 38, 39], [40, 41, 42, 43]], np.uint8)
AMA_P, CIA_P, MAG_P, PRETO_LCD, NEGRO = 44, 45, 46, 47, 48
RGB = PX.paleta_rgb('ep04').astype(int)
NOME_CANAL = ['VERMELHO', 'VERDE', 'AZUL']

# cor de longe para cada combinação de níveis (a mais próxima na paleta)
_cands = [i for i in range(len(RGB)) if i not in (32, 36, 40, PRETO_LCD, 33, 37, 41)]
MEDIA = np.zeros((4, 4, 4), np.uint8)
for r in range(4):
    for g in range(4):
        for b in range(4):
            alvo = np.array([r, g, b]) * 85
            d = [((RGB[i] - alvo) ** 2).sum() for i in _cands]
            MEDIA[r, g, b] = _cands[int(np.argmin(d))]
MEDIA[0, 0, 0] = NEGRO
MEDIA[3, 3, 0] = AMA_P; MEDIA[0, 3, 3] = CIA_P; MEDIA[3, 0, 3] = MAG_P
MEDIA[3, 2, 0] = 17; MEDIA[3, 0, 0] = SUB[0, 3]; MEDIA[0, 3, 0] = SUB[1, 3]; MEDIA[0, 0, 3] = SUB[2, 3]; MEDIA[3, 3, 3] = BRANCO
# versão apagada de cada cor (foco: o que está fora do protagonista escurece)
APAGADA = np.zeros(len(RGB), np.uint8)
_esc = [i for i in range(len(RGB)) if i not in (PRETO_LCD,)]
for i in range(len(RGB)):
    alvo = RGB[i] * .3
    APAGADA[i] = _esc[int(np.argmin([((RGB[j] - alvo) ** 2).sum() for j in _esc]))]
for k in range(3):
    for n in range(4): APAGADA[SUB[k, n]] = SUB[k, max(0, n - 2)]


def apagar_fora(tela, x0, y0, x1, y1, clip):
    """Escurece tudo no `clip` menos o retângulo (x0, y0)-(x1, y1)."""
    c0, c1, c2, c3 = [int(v) for v in clip]
    sub = tela.buf[c1:c3, c0:c2]
    yy, xx = np.mgrid[c1:c3, c0:c2]
    fora = ~((xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1))
    sub[fora] = APAGADA[sub[fora]]


NIVEIS_DE = np.clip(np.round(RGB / 85.0), 0, 3).astype(np.uint8)       # cor da paleta -> níveis


def nome_cor(r, g, b):
    """Nome da mistura de 3 canais (0..3): canal em 1 conta como quase apagado."""
    a = tuple(int(x >= 2) for x in (r, g, b))
    tab = {(1, 0, 0): 'VERMELHO', (0, 1, 0): 'VERDE', (0, 0, 1): 'AZUL', (1, 1, 0): 'AMARELO', (0, 1, 1): 'CIANO',
           (1, 0, 1): 'MAGENTA', (1, 1, 1): 'BRANCO'}
    if a == (0, 0, 0): return 'PRETO' if r + g + b == 0 else 'QUASE PRETO'
    if a == (1, 1, 0) and r > g: return 'LARANJA'
    return tab[a]


# ------------------------------------------------------------------ imagem da tela
IMG_W, IMG_H = 36, 80                 # 9:20, a proporção de uma tela 1.080 x 2.400
SOL = (25, 18)                        # o pixel protagonista (amarelo: R e G acesos)


def _base(noite=False):
    a = np.zeros((IMG_H, IMG_W, 3), np.uint8)
    yy, xx = np.mgrid[0:IMG_H, 0:IMG_W]
    if noite:
        a[:] = (0, 0, 0)
        rng = np.random.default_rng(4)
        for _ in range(26):
            x, y = int(rng.integers(0, IMG_W)), int(rng.integers(4, 44))
            a[y, x] = (3, 3, 3) if rng.random() < .5 else (2, 2, 2)
        lua = (xx - 10) ** 2 + (yy - 14) ** 2 <= 16
        a[lua] = (3, 3, 2)
        a[((xx - 12) ** 2 + (yy - 13) ** 2 <= 9) & lua] = (2, 2, 2)
    else:
        a[:18] = (0, 1, 3); a[18:32] = (1, 2, 3); a[32:48] = (2, 2, 3)
        d = np.hypot(xx - SOL[0], yy - SOL[1])
        a[d <= 5.6] = (3, 2, 0)
        a[d <= 4.6] = (3, 3, 0)
    # montanhas ao fundo, com neve
    for cx, alt, larg in ((9, 30, 16), (27, 36, 13)):
        m = (yy >= alt + np.abs(xx - cx) * 22 / larg) & (yy < 62)
        a[m] = (1, 1, 1) if noite else (1, 1, 2)
        a[m & (yy < alt + 4)] = (2, 2, 2) if noite else (3, 3, 3)
    # morro verde
    morro = yy >= 50 + 4 * np.sin(xx * .25)
    a[morro] = (0, 1, 0) if noite else (0, 2, 0)
    a[morro & (yy >= 66)] = (0, 1, 0)
    # lago
    lago = (yy >= 58) & (yy < 63) & (np.abs(xx - 18) < 10 - (yy - 58))
    a[lago] = (0, 0, 1) if noite else (0, 2, 3)
    # flores
    for x, y, c in ((4, 71, (3, 0, 0)), (12, 74, (3, 0, 3)), (21, 70, (3, 0, 0)), (30, 76, (3, 3, 0)),
                    (7, 78, (3, 3, 3)), (26, 73, (3, 0, 3))):
        a[y, x] = c if not noite else (1, 0, 1)
    # barra de status: preta, com relógio e bateria em branco
    a[0:3] = (0, 0, 0)
    for x in (2, 3, 5, 6): a[1, x] = (3, 3, 3)
    for x in range(29, 33): a[1, x] = (3, 3, 3)
    return a


_DIA, _NOITE = _base(False), _base(True)


_ESTRELAS = np.argwhere((_NOITE[:29].sum(-1) >= 6) & (np.hypot(*np.mgrid[0:29, 0:IMG_W][::-1] - np.array([10, 14])[:, None, None]) > 5))


def paisagem(t, noite=False):
    """A imagem no instante t: nuvens andando e brilho no lago (níveis 0..3)."""
    a = (_NOITE if noite else _DIA).copy()
    if noite:
        for i, (y, x) in enumerate(_ESTRELAS):              # estrelas piscando
            if math.sin(t * 2.3 + i * 1.7) > .55: a[y, x] = (1, 1, 1)
    if not noite:
        for k, (y0, larg, vel, fase) in enumerate(((8, 9, 1.2, 0), (24, 7, .8, 20))):
            x0 = int((t * vel + fase) % (IMG_W + 14)) - 12
            for dx in range(larg):
                x = x0 + dx
                if 0 <= x < IMG_W:
                    a[y0, x] = (3, 3, 3)
                    if 1 < dx < larg - 2: a[y0 - 1, x] = (3, 3, 3)
                    a[y0 + 1, x] = (2, 2, 3)
        k = int(t * 3) % 6
        a[60, 12 + k * 2] = (3, 3, 3)
    return a


def normal_de(lev, preto=None):
    n = MEDIA[lev[..., 0], lev[..., 1], lev[..., 2]]
    if preto is not None:
        n = np.where((lev.sum(-1) == 0), preto, n).astype(np.uint8)
    return n


# ------------------------------------------------------------------ zoom até o subpixel
def render_niveis(tela, lev, normal, ox, oy, z, clip, div=1):
    """Desenha a imagem `lev` (h, w, 3 níveis) com o canto em (ox, oy) e
    `z` pixels de tela por ponto. `div` = pixels de verdade por ponto (o
    vídeo usa 4: cada ponto desenhado vira 4x4). Com o pixel de verdade
    grande (>= 5 px), cada um se abre em 3 listras R, G, B com o brilho do
    seu canal e a grade preta entre eles."""
    x0, y0, x1, y1 = (max(0, int(clip[0])), max(0, int(clip[1])), min(tela.w, int(clip[2])), min(tela.h, int(clip[3])))
    if x1 <= x0 or y1 <= y0: return
    hh, ww = normal.shape
    X = np.arange(x0, x1) + .5
    Y = np.arange(y0, y1) + .5
    u = (X - ox) / z; v = (Y - oy) / z
    iu = np.floor(u).astype(int); iv = np.floor(v).astype(int)
    ok_u = np.nonzero((iu >= 0) & (iu < ww))[0]; ok_v = np.nonzero((iv >= 0) & (iv < hh))[0]
    if len(ok_u) == 0 or len(ok_v) == 0: return
    a0, a1, b0, b1 = ok_u[0], ok_u[-1] + 1, ok_v[0], ok_v[-1] + 1
    u, v, iu, iv = u[a0:a1], v[b0:b1], iu[a0:a1], iv[b0:b1]
    out = normal[iv[:, None], iu[None, :]]
    zc = z / div
    if zc >= 2.5:
        fu = (u * div) % 1.0; fv = (v * div) % 1.0
        if zc < 5 and div > 1:
            grade = ((fu * zc) < 1)[None, :] | ((fv * zc) < 1)[:, None]
            out = np.where(grade, TRACO, out)
        if zc >= 4.5:
            s = np.minimum(2, (fu * 3).astype(int))
            L = lev[iv[:, None], iu[None, :]]                          # (ny, nx, 3)
            Ls = np.take_along_axis(L, np.broadcast_to(s[None, :, None], L.shape[:2] + (1,)), 2)[..., 0]
            listras = SUB[np.broadcast_to(s[None, :], Ls.shape), Ls]
            lx = (fu * 3 - s) * zc / 3
            gx = (lx < 1) if zc / 3 >= 3.5 else np.zeros_like(lx, bool)
            gy = max(1.0, zc * .07) if zc >= 8 else 0.0
            vy = fv * zc
            buraco = gx[None, :] | ((vy < gy) | (vy > zc - gy))[:, None]
            listras = np.where(buraco, NEGRO, listras)
            alfa = min(1.0, (zc - 4.5) / 3.0)
            yy = np.arange(b0, b1)[:, None] + y0; xx = np.arange(a0, a1)[None, :] + x0
            m = BAYER8[yy % 8, xx % 8] < alfa
            out = np.where(m, listras, out)
    tela.buf[y0 + b0:y0 + b1, x0 + a0:x0 + a1] = out


def rret(tela, x, y, w, h, r, cor):
    """Retângulo de cantos arredondados."""
    r = max(0, min(r, w / 2, h / 2))
    tela.ret(x + r, y, w - 2 * r, h, cor)
    tela.ret(x, y + r, w, h - 2 * r, cor)
    for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r), (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        tela.disco(cx, cy, r, cor)


def celular_corpo(tela, sx, sy, sw, sh, b):
    """Corpo de um celular genérico (sem marca) em volta do retângulo da tela."""
    b = max(2.0, b)
    x, y, w, h = sx - b, sy - b * 1.6, sw + 2 * b, sh + 3.2 * b
    r = b * 1.8
    rret(tela, x - 1, y - 1, w + 2, h + 2, r + 1, PRETO)
    rret(tela, x, y, w, h, r, FUNDO3)
    dither(tela, x + w * .62, y + r, w * .38 - 1, h - 2 * r, FUNDO3, TRACO)
    tela.ret(x + 1, y + r, 1, h - 2 * r, ACO2)                      # luz na borda esquerda
    tela.ret(x + r, y + 1, w - 2 * r, 1, ACO1)
    for yy, hh in ((.16, .10), (.30, .16)):                         # botões laterais
        tela.ret(x + w, y + h * yy, max(1, b * .45), h * hh, ACO1)
        tela.ret(x + w + max(1, b * .45), y + h * yy, 1, h * hh, PRETO)
    tela.ret(sx - 1, sy - 1, sw + 2, sh + 2, PRETO)                 # borda preta da tela
    # alto-falante de cima e microfone
    tela.ret(sx + sw * .38, y + b * .55, sw * .24, max(1, b * .3), PRETO)


def celular_camera(tela, sx, sy, sw, sh, b):
    tela.disco(sx + sw / 2, sy + max(2, b * .9), max(1.2, b * .45), NEGRO)
    tela.px(sx + sw / 2 - 1, sy + max(2, b * .9) - 1, ACO2)


def celular(tela, lev, sx, sy, z, t=0.0, preto=None, clip=(0, 0, W, PALCO_H), camera=True):
    """Celular inteiro com a imagem `lev` na tela, `z` px por ponto."""
    sw, sh = IMG_W * z, IMG_H * z
    b = 2.2 * z
    celular_corpo(tela, sx, sy, sw, sh, b)
    render_niveis(tela, lev, normal_de(lev, preto), sx, sy, z, (max(clip[0], sx), max(clip[1], sy),
                                                                min(clip[2], sx + sw), min(clip[3], sy + sh)))
    if camera and z < 8: celular_camera(tela, sx, sy, sw, sh, b)


# ------------------------------------------------------------------ textos
def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9):
    """Texto com fio até a peça (o fio sai do lado do texto mais perto da peça)."""
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    tela.linha(ex, hy, ax, ay, cor)
    tela.disco(ax, ay, 1.5, cor)
    tela.ret(ex - 1, hy - 1, 3, 3, cor)


def centro_preso(tela, txt, cx, y, cor, tam=9, xmin=2, xmax=296):
    w = tela.largura_texto(txt, tam)
    x = int(min(max(cx - w / 2, xmin), xmax - w))
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def amostra(tela, x, y, cor, lado=10):
    tela.ret(x - 1, y - 1, lado + 2, lado + 2, PRETO)
    tela.ret(x, y, lado, lado, cor)
    tela.px(x, y, BRANCO if cor != BRANCO else ACO3)


# ------------------------------------------------------------------ o corte de um pixel
LANES = [(30, 44), (84, 44), (138, 44)]              # y e altura de cada subpixel (R, G, B)
SLAB_Y0, SLAB_Y1 = 24, 188
# o filtro de cor fica no vidro da frente, por dentro; o 2º polarizador, por fora dele
LCD = dict(luz=(8, 28), pol1=(38, 44), vid1=(52, 55), cris=(55, 121), vid2=(121, 124), filt=(128, 136),
           pol2=(144, 150))
SAIDA = (162, 176)
OLED = dict(tft=(8, 34), anodo=(40, 45), org=(45, 96), catodo=(96, 100), vidro=(112, 117))
NOMES_LCD = dict(luz='LUZ DE FUNDO', pol1='POLARIZADOR', cris='CRISTAL LÍQUIDO', pol2='POLARIZADOR 2',
                 filt='FILTRO DE COR')
ORDEM_LCD = ['luz', 'pol1', 'cris', 'pol2', 'filt']
MIX_X, MIX_Y, MIX_L = 200, 86, 40                     # o pixel visto de longe


def _frac(x): return x - math.floor(x)


def _laje(tela, x0, x1, c1, c2, dy=0, borda=PRETO):
    tela.ret(x0 - 1, SLAB_Y0 - 1 + dy, x1 - x0 + 2, SLAB_Y1 - SLAB_Y0 + 2, borda)
    dither(tela, x0, SLAB_Y0 + dy, x1 - x0, SLAB_Y1 - SLAB_Y0, c1, c2)


def _matriz(tela, x0, x1, dy=0):
    """Faixas pretas entre os subpixels (a grade preta da tela)."""
    for k in range(len(LANES) + 1):
        if k == 0: y0, y1 = SLAB_Y0, LANES[0][0]
        elif k == len(LANES): y0, y1 = LANES[-1][0] + LANES[-1][1], SLAB_Y1
        else: y0, y1 = LANES[k - 1][0] + LANES[k - 1][1], LANES[k][0]
        tela.ret(x0, y0 + dy, x1 - x0, y1 - y0, PRETO)


def desenhar_lcd(tela, t, niveis, pecas=None, desloc=None, vaza=False):
    """Corte de um pixel LCD de lado; a luz anda da esquerda (luz de fundo) para
    a direita (quem olha). `niveis` = brilho de cada subpixel 0..3 (3 = sem
    tensão, espiral inteira, luz passa). Devolve o brilho que sai em cada faixa."""
    P = set(ORDEM_LCD) if pecas is None else set(pecas)
    dz = desloc or {}
    D = lambda k: int(dz.get(k, 0))
    # --- lajes
    if 'luz' in P:
        x0, x1 = LCD['luz']; d = D('luz')
        _laje(tela, x0 + 5, x1, BRANCO, ACO4, d)
        dither(tela, x0 + 13, SLAB_Y0 + d, x1 - x0 - 13, SLAB_Y1 - SLAB_Y0, ACO4, ACO3)
        tela.ret(x0 - 1, SLAB_Y0 - 1 + d, 6, SLAB_Y1 - SLAB_Y0 + 2, PRETO)
        tela.ret(x0, SLAB_Y0 + d, 4, SLAB_Y1 - SLAB_Y0, ACO1)
        for k in range(8):                                    # LEDs na borda
            y = SLAB_Y0 + 6 + k * 21 + d
            tela.ret(x0 + 1, y, 4, 6, CHAMA0 if (k + int(t * 2)) % 9 else BRANCO)
            tela.ret(x0 + 2, y + 1, 2, 4, BRANCO)
    for nome in ('pol1', 'pol2'):
        if nome not in P: continue
        x0, x1 = LCD[nome]; d = D(nome)
        _laje(tela, x0, x1, ACO1, ACO1, d)
        if nome == 'pol1':                                    # eixo em pé: risquinhos verticais
            for x in range(x0, x1, 2): tela.ret(x, SLAB_Y0 + d, 1, SLAB_Y1 - SLAB_Y0, ACO3)
        else:                                                 # eixo para dentro da tela: pontos
            for y in range(SLAB_Y0 + 1, SLAB_Y1, 3):
                for x in range(x0 + 1, x1, 3): tela.ret(x, y + d, 2, 2, ACO3)
    torcao = [n / 3.0 for n in niveis]
    if 'cris' in P:
        d = D('cris')
        c0, c1 = LCD['cris']
        for nome in ('vid1', 'vid2'):
            x0, x1 = LCD[nome]
            _laje(tela, x0, x1, ACO4, CIANO, d)
        dither(tela, c0 + 1, SLAB_Y0 + d, c1 - c0 - 1, SLAB_Y1 - SLAB_Y0, FUNDO2, FUNDO3)
        _matriz(tela, c0 + 1, c1, d)
        for k, (ly, lh) in enumerate(LANES):
            tensao = 1.0 - torcao[k]
            for xe in (c0 + 1, c1 - 1):                       # eletrodos transparentes
                tela.ret(xe, ly + 2 + d, 1, lh - 4, AMARELO if tensao > .1 else ACO1)
            cols = list(range(c0 + 6, c1 - 3, 8))
            for j, cx in enumerate(cols):
                p = (cx - c0) / (c1 - c0)
                s = tensao * (.25 if j in (0, len(cols) - 1) else 1.0)
                fi = math.radians(90 * p)
                for cy in range(ly + 6, ly + lh - 3, 8):
                    ccy = cy + d + math.sin(t * 2 + cx * .3 + cy) * .4
                    hx = s * 2.4
                    hy = (1 - s) * 3.0 * math.cos(fi)
                    if hx < .8 and hy < .8:
                        tela.ret(cx, ccy, 2, 2, AGUA1); tela.px(cx, ccy, CIANO)
                    else:
                        tela.linha(cx - hx, ccy - hy, cx + hx, ccy + hy, AGUA1)
                        tela.linha(cx - hx + 1, ccy - hy, cx + hx + 1, ccy + hy, CIANO)
    if 'filt' in P:
        d = D('filt'); x0, x1 = LCD['filt']
        _laje(tela, x0, x1, PRETO, PRETO, d)
        for k, (ly, lh) in enumerate(LANES):
            tela.ret(x0, ly + d, x1 - x0, lh, SUB[k, 2])
            tela.ret(x0, ly + d, 2, lh, SUB[k, 3])
    # --- a luz (fótons) faixa por faixa; peça ainda caindo não conta
    P = {p for p in P if not dz.get(p)}
    if 'luz' not in P: return [0.0, 0.0, 0.0]
    xi, xf = LCD['luz'][1], SAIDA[1]
    span = xf - xi
    saida = []
    for k, (ly, lh) in enumerate(LANES):
        n = 20
        for i in range(n):
            x = xi + _frac(t * 30 / span + i / n + k * .13) * span
            y = ly + 5 + ((i * 7 + k * 3) % 11) * 3.4
            h1, h2 = _frac(i * .7548 + k * .31), _frac(i * .5698 + k * .17)
            estado, ang, cor, morre = 'u', 0.0, BRANCO, None
            if 'pol1' in P and x >= LCD['pol1'][0]:
                if h1 >= .5: morre = LCD['pol1'][0]                    # metade da luz comum fica no 1º
                estado = 'p'
            if 'cris' in P and estado == 'p' and x >= LCD['cris'][0]:
                ang = 90 * torcao[k] * min(1.0, (x - LCD['cris'][0]) / (LCD['cris'][1] - LCD['cris'][0]))
            if 'pol2' in P and x >= LCD['pol2'][0] and morre is None:
                if estado == 'p':
                    passa = h2 < torcao[k] or (vaza and h2 > .8)
                else:
                    passa = h2 < .5
                if not passa: morre = LCD['pol2'][0]
                estado = 'd'
            fraco = vaza and torcao[k] < .05
            if 'filt' in P and x >= LCD['filt'][1]:
                estado = 'c'
            if morre is not None:
                if morre <= x < morre + 4:
                    tela.px(morre - 1, y, ACO3)
                continue
            if x >= xf - 2: continue
            if estado == 'u':
                tela.ret(x - 1, y, 3, 1, BRANCO); tela.ret(x, y - 1, 1, 3, BRANCO)
            elif estado == 'p':
                L = max(1, int(round(5 * math.cos(math.radians(ang)))))
                if L <= 1: tela.ret(x, y, 2, 2, BRANCO)
                else: tela.ret(x, y - L // 2, 1, L, BRANCO)
            elif estado == 'd':
                tela.ret(x, y, 2, 2, ACO3 if fraco else BRANCO)
            else:
                tela.ret(x, y, 2, 2, SUB[k, 1] if fraco else SUB[k, 3])
                tela.px(x - 1, y, SUB[k, 1] if fraco else SUB[k, 2])
        # o que sai desta faixa
        if 'pol2' in P and 'cris' in P:
            f = torcao[k]
            if vaza and f < .05: f = .08
        elif 'pol2' in P: f = 0.0 if 'pol1' in P else .5
        elif 'pol1' in P: f = .5
        else: f = 1.0
        saida.append(f)
    return saida


def janela_saida(tela, saida, filtro=True, vaza=False, preto=None):
    """As 3 janelas por onde a luz sai (o que o olho recebe de cada subpixel)."""
    x0, x1 = SAIDA
    for k, (ly, lh) in enumerate(LANES):
        f = saida[k]
        n = int(round(f * 3))
        if filtro:
            cor = SUB[k, n] if (n > 0 or not vaza) else SUB[k, 0]
            if n == 0 and preto is not None: cor = preto
        else:
            cor = [FUNDO2, ACO1, ACO3, BRANCO][n]
        tela.ret(x0 - 1, ly - 1, x1 - x0 + 2, lh + 2, PRETO)
        tela.ret(x0, ly, x1 - x0, lh, cor)
        if n == 3: tela.ret(x0 + 2, ly + 2, 2, lh - 4, BRANCO)


def pixel_de_longe(tela, saida, rotulo_txt='VISTO DE LONGE', preto=None, t=0.0):
    """O pixel inteiro como o olho vê: a soma das 3 luzes numa cor só."""
    n = [int(round(f * 3)) for f in saida]
    cor = MEDIA[n[0], n[1], n[2]]
    if sum(n) == 0 and preto is not None: cor = preto
    x, y, L = MIX_X, MIX_Y, MIX_L
    for k, (ly, lh) in enumerate(LANES):                     # as 3 luzes convergem
        y0 = ly + lh // 2
        for j in range(0, 24, 3):
            u = (j + (t * 12) % 3) / 24
            tela.px(SAIDA[1] + 2 + u * (x - SAIDA[1] - 4), y0 + (y + L / 2 - y0) * u, SUB[k, max(1, n[k])])
    tela.ret(x - 2, y - 2, L + 4, L + 4, PRETO)
    tela.ret(x - 1, y - 1, L + 2, L + 2, ACO1)
    tela.ret(x, y, L, L, cor)
    if cor not in (NEGRO, PRETO_LCD):
        tela.ret(x + 2, y + 2, L // 3, 1, BRANCO)
    centro_preso(tela, rotulo_txt, x + L / 2, y - 14, ACO3)
    return n, cor


def desenhar_oled(tela, t, niveis, preto_desligado=True):
    """Corte de um pixel OLED: cada faixa tem a SUA camada que acende."""
    x0, x1 = OLED['tft']
    _laje(tela, x0, x1, AGUA0, OLEO0)
    _matriz(tela, x0, x1)
    for k, (ly, lh) in enumerate(LANES):
        on = niveis[k] > .05
        # transistor que manda a corrente desta faixa
        tela.ret(x0 + 4, ly + 10, 12, 10, ACO0); tela.ret(x0 + 5, ly + 11, 10, 8, ACO1)
        tela.ret(x0 + 6, ly + 12, 3, 3, AMARELO if on else ACO2)
        tela.ret(x0 + 16, ly + 14, x1 - x0 - 16, 2, LATAO)
        tela.ret(x0 + 2, ly + 30, x1 - x0 - 4, 1, LATAO)
        if on:
            for j in range(4):
                u = _frac(t * .9 + j / 4)
                tela.ret(x0 + 16 + u * (x1 - x0 - 17), ly + 14, 2, 2, AMARELO)
    for nome, c1, c2 in (('anodo', ACO3, ACO2), ('catodo', ACO4, ACO3), ('vidro', ACO4, CIANO)):
        a, b = OLED[nome]
        _laje(tela, a, b, c1, c2)
    o0, o1 = OLED['org']
    tela.ret(o0, SLAB_Y0 - 1, o1 - o0, SLAB_Y1 - SLAB_Y0 + 2, PRETO)
    _matriz(tela, o0, o1)
    saida = []
    for k, (ly, lh) in enumerate(LANES):
        f = niveis[k]
        n = int(round(f * 3))
        c_luz = SUB[k, n] if n > 0 else (NEGRO if preto_desligado else SUB[k, 0])
        c_meio = SUB[k, max(0, n - 1)] if n > 0 else c_luz
        dither(tela, o0, ly, o1 - o0, lh, c_luz, c_meio, fase=int(t * 4) % 2)
        tela.ret(o0, ly, o1 - o0, 1, c_meio)
        if n > 0:
            for j in range(5):                              # cintilação: a luz nasce aqui dentro
                xx = o0 + 4 + int(_frac(j * .37 + t * .23 + k * .1) * (o1 - o0 - 8))
                yy = ly + 4 + int(_frac(j * .61 + k * .29) * (lh - 8))
                if _frac(t * 1.7 + j * .21) < .5: tela.ret(xx, yy, 2, 2, BRANCO)
        # fótons: nascem na camada orgânica e saem pela frente
        xi, xf = o0 + 20, SAIDA[1]
        span = xf - xi
        for i in range(12):
            if _frac(i * .5698 + k * .17) >= f: continue
            x = xi + _frac(t * 30 / span + i / 12 + k * .13) * span
            if x >= xf - 2 or x < o1 + 1: continue
            y = ly + 5 + ((i * 5 + k * 3) % 7) * 5.4
            tela.ret(x, y, 2, 2, SUB[k, 3]); tela.px(x - 1, y, SUB[k, 2])
        saida.append(f)
    return saida


def cabecalhos(tela, itens, y_a=4, y_b=14):
    """Nomes curtos acima das lajes, em duas fileiras alternadas."""
    for j, (txt, cx, cor) in enumerate(itens):
        centro_preso(tela, txt, cx, y_a if j % 2 == 0 else y_b, cor)
