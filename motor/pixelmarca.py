#!/usr/bin/env python3
"""Vinheta CAIU A FICHA em 8 bits.

A vinheta de colagem (`quizbrand.py`) é do quiz: papel rasgado ao lado de
pixel art são dois idiomas, e ela leva 0,25 s por quadro, mais lenta que o
vídeo inteiro. Aqui é a mesma ficha, o mesmo gesto, outro suporte.

Mesmo gesto: a ficha cai girando, bate, a tela treme, e o impacto monta o
nome letra por letra **na batida**. A paleta é fixa — a marca sai igual em
todo vídeo, qualquer que seja a paleta do conteúdo.
"""
import math
import numpy as np
import pixelengine as PX
import quizaudio as A

INTRO_S = 2.30
OUTRO_S = 3.10
T_BAT = .62                  # instante da batida; som e imagem usam o mesmo

ESC, ESC_CLA, ESC_ESC = 6, 7, 4      # latão da ficha, na paleta 'marca'
FUNDO, FUNDO2, FENDA = 0, 1, 3
NOME, ACC = 11, 9     # nome em branco, FICHA no destaque


def ficha(tela, cx, cy, r, giro):
    """A ficha de orelhão, girando no eixo vertical: a largura encolhe por
    |cos|. Quase de perfil ela vira uma lasca de metal, nunca some."""
    rx = max(1.0, abs(math.cos(giro)) * r)
    if rx < r * .16:
        tela.ret(cx - 1, cy - r, 3, 2 * r, ESC_ESC)
        tela.ret(cx, cy - r + 1, 1, 2 * r - 2, ESC_CLA)
        return
    # disco achatado: máscara de elipse, sem suavizar a borda
    x0, x1 = int(cx - rx - 1), int(cx + rx + 2)
    y0, y1 = int(cy - r - 1), int(cy + r + 2)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(tela.w, x1), min(tela.h, y1)
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = ((xx - cx) / rx) ** 2 + ((yy - cy) / r) ** 2
    tela.buf[y0:y1, x0:x1][d <= 1.0] = ESC
    tela.buf[y0:y1, x0:x1][(d <= 1.0) & (d > .74)] = ESC_ESC
    tela.buf[y0:y1, x0:x1][d <= .30] = ESC_CLA
    if rx > r * .34:                       # a fenda do orelhão
        tela.ret(cx - max(1, rx * .10), cy - r * .55,
                 max(1, rx * .20), r * 1.1, FENDA)


def _letras(tela, vert):
    """As linhas do nome e o corpo de cada uma."""
    if vert: return [('CAIU A', 15), ('FICHA', 27)]
    return [('CAIU A FICHA', 20)]


def abertura(W, H, fps, seed=0):
    tela = PX.Tela(W, H, 'marca')
    rng = np.random.default_rng(seed * 101 + 5)
    vert = H > W
    N = int(round(INTRO_S * fps))
    cx, cy = W // 2, int(H * (.36 if vert else .34))
    r = int(min(W, H) * .13)
    linhas = _letras(tela, vert)
    estrelas = [(int(rng.integers(0, W)), int(rng.integers(0, H)),
                 int(rng.integers(0, 3))) for _ in range(70)]
    cacos = [(rng.random() * math.tau, .6 + rng.random() * 1.6,
              int(rng.integers(1, 3))) for _ in range(26)]

    for i in range(N):
        t = i / fps
        te = t - T_BAT
        tremor = 0
        if 0 <= te < .3: tremor = int(round(math.sin(te * 70) * 4 * (1 - te / .3)))

        ly0 = cy + r * (2.2 if vert else 2.0)
        alt_nome = sum(c + 3 for _, c in linhas)
        tela.limpar(FUNDO)
        tela.ret(0, cy - r * 2.6, W, (ly0 + alt_nome + 12) - (cy - r * 2.6), FUNDO2)
        for ex, ey, ec in estrelas:
            tela.px(ex, ey + tremor, ACC if (ec == 2 and 0 <= te < .2) else
                    (ESC_CLA if ec else FUNDO2 + 1))

        if t < T_BAT:                                   # a queda
            u = t / T_BAT
            y = -r + (cy + r) * u * u
            for k in range(4):                          # rastro
                if y - k * r * .7 > -r:
                    ficha(tela, cx, y - k * r * .7, max(1, r - k * 2),
                          u * 11 + k * .5)
            ficha(tela, cx, y, r, u * 11)
        else:
            q = max(0.0, 1 - te / .18)                  # achatou no impacto
            ficha(tela, cx + tremor, cy + r * .2 * q, int(r * (1 + .3 * q)), 0)
            if te < .9:                                 # cacos saltando
                cu = te / .9
                for a, v, c in cacos:
                    px = cx + math.cos(a) * v * W * .5 * cu
                    py = cy + math.sin(a) * v * H * .22 * cu - H * .09 * math.sin(math.pi * cu)
                    if cu < .85: tela.px(px, py, ESC_CLA if c == 2 else ACC)
            if te < .22:                                # clarão
                rr = int(r * (1 + te * 14))
                tela.anel(cx, cy, rr, ESC_CLA, 2)

            # o nome, letra por letra
            ly = ly0
            for li, (txt, corpo) in enumerate(linhas):
                larg = tela.largura_texto(txt, corpo)
                x = (W - larg) / 2
                for ci, ch in enumerate(txt):
                    lw = tela.largura_texto(ch, corpo)
                    if ch != ' ':
                        n = sum(len(l[0]) for l in linhas[:li]) + ci
                        lu = (te - .06 - n * .034) / .22
                        if lu > 0:
                            e = 1 - (1 - min(1.0, lu)) ** 3
                            dy = int((1 - e) * -18)
                            cor = ACC if (li == len(linhas) - 1 and vert) else NOME
                            if lu < .45: cor = ESC_CLA
                            tela.texto(ch, x, ly + li * (corpo + 3) + dy, cor,
                                       tam=corpo, sombra=FUNDO)
                    x += lw
        yield np.clip(tela.quadro(), 0, 255).astype(np.uint8)


def encerramento(W, H, fps, linhas_txt, seed=0):
    """O nome fica, a ficha desce e entra na fenda."""
    tela = PX.Tela(W, H, 'marca')
    rng = np.random.default_rng(seed * 211 + 9)
    vert = H > W
    N = int(round(OUTRO_S * fps))
    cx, cy = W // 2, int(H * (.30 if vert else .28))
    r = int(min(W, H) * .10)
    linhas = _letras(tela, vert)
    fenda_y = cy + int(r * (5.2 if vert else 4.0))
    estrelas = [(int(rng.integers(0, W)), int(rng.integers(0, H)),
                 int(rng.integers(0, 3))) for _ in range(70)]

    for i in range(N):
        t = i / fps
        tela.limpar(FUNDO)
        tela.ret(0, cy - r * 2, W, r * 9, FUNDO2)
        for ex, ey, ec in estrelas:
            tela.px(ex, ey, ESC_CLA if ec == 2 else FUNDO2 + 1)

        ly = cy
        for li, (txt, corpo) in enumerate(linhas):
            larg = tela.largura_texto(txt, corpo)
            x = (W - larg) / 2
            for ci, ch in enumerate(txt):
                lw = tela.largura_texto(ch, corpo)
                if ch != ' ':
                    n = sum(len(l[0]) for l in linhas[:li]) + ci
                    lu = min(1.0, max(0.0, (t - n * .018) / .2))
                    if lu > 0:
                        e = 1 - (1 - lu) ** 3
                        cor = ACC if (li == len(linhas) - 1 and vert) else NOME
                        tela.texto(ch, x, ly + li * (corpo + 3) + int((1 - e) * -14),
                                   cor, tam=corpo, sombra=FUNDO)
                x += lw

        tela.ret(cx - r * .22, fenda_y, max(2, r * .44), max(2, r * .22), FENDA)

        tq = 1.0
        if t > tq:                                    # a ficha entra na fenda
            u = min(1.0, (t - tq) / .9)
            y = cy + r * 3.0 + (fenda_y - cy - r * 3.0) * u * u
            if y < fenda_y - 1: ficha(tela, cx, y, r, u * 9)
            if u > .95:
                tela.anel(cx, fenda_y, int(r * (1 + (u - .95) * 30)), ACC, 1)

        for k, txt in enumerate(linhas_txt[:2]):      # chamadas
            lu = min(1.0, max(0.0, (t - .5 - k * .25) / .3))
            if lu > 0:
                tela.texto_ajustado(txt, W // 2, fenda_y + int(r * 1.3) + k * 14,
                                    NOME if k == 0 else ESC_CLA, 11, W - 16,
                                    centro=True)
        yield np.clip(tela.quadro(), 0, 255).astype(np.uint8)


def som_abertura(seed=0):
    """Assobio da queda, batida de metal, tapinha por letra."""
    SR = A.SR
    rng = np.random.default_rng(seed * 57 + 3)
    n = int(INTRO_S * SR)
    out = np.zeros(n, np.float32)

    def por(x, t0, g=1.0):
        k = int(t0 * SR); m = min(len(x), n - k)
        if m > 0: out[k:k + m] += x[:m].astype(np.float32) * g

    nq = int(T_BAT * SR); t = np.arange(nq) / SR; u = t / T_BAT
    f = 1400 * 2 ** (-2.4 * u ** 1.5)                  # despenca de tom
    por((np.sin(2 * np.pi * np.cumsum(f) / SR) * (u ** 2.4) * .5).astype(np.float32), 0)
    nb = int(1.1 * SR); tb = np.arange(nb) / SR
    met = np.zeros(nb, np.float32)
    for p, dec, amp in ((1840, .40, 1.0), (2760, .28, .55), (4300, .20, .32)):
        met += (np.sin(2 * np.pi * p * tb) * np.exp(-tb / dec) * amp).astype(np.float32)
    por(met / (np.abs(met).max() + 1e-9) * .55, T_BAT)
    por(A.kick(rng, 1.3), T_BAT, .95)
    for i in range(12):                                 # cada letra, um tapinha
        d = int(.07 * SR); td = np.arange(d) / SR
        s = (np.sin(2 * np.pi * (340 + i * 52) * td) * np.exp(-td / .012) * .6
             + A.bp(rng.standard_normal(d), 2000, 8000) * np.exp(-td / .005) * .45)
        por((s / (np.abs(s).max() + 1e-9) * .22).astype(np.float32), T_BAT + .06 + i * .034)
    por(A.stab([57, 61, 64, 69], .8, rng), T_BAT + .22, .40)
    mix = np.stack([out, out], 1).astype(np.float32)
    return A.master(mix, -14.0)[0]


def som_encerramento(seed=0):
    SR = A.SR
    rng = np.random.default_rng(seed * 83 + 11)
    n = int(OUTRO_S * SR)
    out = np.zeros(n, np.float32)

    def por(x, t0, g=1.0):
        k = int(t0 * SR); m = min(len(x), n - k)
        if m > 0: out[k:k + m] += x[:m].astype(np.float32) * g

    por(A.stab([50, 57, 62, 66], 2.2, rng), 0.0, .52)
    for i, m in enumerate((69, 73, 76)): por(A.bell(m, 1.5, rng), .1 + i * .09, .34)
    por(A.whoosh(rng, .5, up=False), 1.0, .5)
    nb = int(.6 * SR); tb = np.arange(nb) / SR
    met = (np.sin(2 * np.pi * 2460 * tb) * np.exp(-tb / .2)).astype(np.float32)
    por(met * .4, 1.88)
    por(A.bell(81, 1.1, rng), 1.92, .4)
    mix = np.stack([out, out], 1).astype(np.float32)
    return A.master(mix, -14.0)[0]
