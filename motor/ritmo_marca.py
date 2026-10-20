#!/usr/bin/env python3
"""Vinheta RITMO PIXEL.

O gesto (instrução do projeto): um pixel cai, quica no tempo da música e se
multiplica até formar o nome do canal bloco a bloco.

  batida 1   o pixel cai e bate no chão
  batida 2   quica, bate de novo e vira 4
  batida 3   os 4 explodem em blocos que voam, cada um para a sua casa nas
             letras, da esquerda para a direita (um tique por bloco no som)
  batida 4   o nome fecha: acorde, flash, e o brilho respira até o fim

Imagem e som saem da MESMA tabela de tempos (`_tempos`): quiques, explosão
e acorde caem no quadro da batida, e os pousos acontecem na janela dos tiques. A paleta é fixa (a marca sai igual em todo vídeo).
Encerramento em 2,8 s (limite 3 s); abertura em 1,8 s (limite 2 s), para os
vídeos longos.

    for q in encerramento(W, H, fps, ['SUBSCRIBE'], seed): ...   # RGB 1080x1920
    som = som_encerramento(seed)                                   # estéreo 48 kHz
"""
import math
import numpy as np
import pixelengine as PX
import pixelfonte as PF
import ritmo_acabamento as AC

SR = 48000
PAL = 'ritmo_pixel'
PX.PALETAS[PAL] = ['#0b0a14', '#14112a', '#221b44', '#3a2f66', '#5a4a98', '#ff8fb5',
                   '#a8f2ff', '#6b5bb0', '#9d8fe0', '#ff3d7f', '#3de0ff', '#ffffff',
                   '#ffd23f', '#8a1f4a', '#17708c', '#ffe9a8']
ROSA, ROSA_L, ROSA_E = 9, 5, 13
CIANO, CIANO_L, CIANO_E = 10, 6, 14
AMARELO, BRANCO, CHAO = 12, 11, 3

OUTRO_S = 2.8
INTRO_S = 1.8
B = 4                     # lado do bloco das letras, em pixels da tela baixa


def _tempos(spb):
    """Batidas da vinheta (s): queda, quique, explosão, nome fechado."""
    return dict(b1=spb, b2=2 * spb, b3=3 * spb, b4=4 * spb, spb=spb)


def _alvos(W, H):
    """Casas dos blocos: as células acesas de RITMO e PIXEL na grade 5x7."""
    out = []
    for k, (palavra, cor, luz, esc) in enumerate((('RITMO', ROSA, ROSA_L, ROSA_E),
                                                  ('PIXEL', CIANO, CIANO_L, CIANO_E))):
        m = PF.mascara(palavra, 1)
        h, w = m.shape
        x0 = W // 2 - (w * B) // 2
        y0 = H // 2 - 40 + k * (h * B + 7)
        for yy, xx in zip(*np.nonzero(m)):
            out.append(dict(x=x0 + xx * B, y=y0 + yy * B, cor=cor, luz=luz, esc=esc, col=xx + k * 2))
    return out


def _bloco(tela, x, y, cor, luz, esc, lado=B):
    tela.ret(x, y, lado, lado, cor)
    tela.px(x, y, luz)
    if lado > 2: tela.px(x + lado - 1, y + lado - 1, esc)


def _rodar(W, H, fps, dur, spb, linhas_txt, seed):
    T = _tempos(spb)
    alvos = _alvos(W, H)
    rng = np.random.default_rng(seed + 404)
    chao = H // 2 + 40
    cx = W // 2
    n = len(alvos)
    # ordem de pouso: coluna (esquerda -> direita), com um tremor pequeno
    ordem = np.argsort([a['col'] + rng.uniform(0, .8) for a in alvos])
    janela = T['b4'] - T['b3'] - spb * .25
    for r, i in enumerate(ordem):
        alvos[i]['pousa'] = T['b3'] + spb * .12 + janela * r / max(1, n - 1)
        alvos[i]['sai'] = alvos[i]['pousa'] - .22
        alvos[i]['de'] = (cx + rng.uniform(-6, 6), chao - 3)
    tela = PX.Tela(W, H, paleta=PAL)
    yy, xx = np.mgrid[0:H, 0:W]
    N = int(round(dur * fps))
    for q in range(N):
        t = q / fps
        tela.limpar(0)
        # chão: uma linha que acende no impacto
        imp = max(math.exp(-abs(t - T[k]) / .08) if t >= T[k] else 0 for k in ('b1', 'b2', 'b3'))
        if t < T['b3'] + spb:
            tela.ret(cx - 40, chao, 80, 1, BRANCO if imp > .5 else CHAO)
        # pixel caindo e quicando (b1, b2), depois 4 (b2 -> b3)
        if t < T['b3']:
            if t < T['b1']:
                u = t / T['b1']; y = (chao - 4) * u * u - 4 * (1 - u)
                pts = [(cx - 2, y)]
            elif t < T['b2']:
                u = (t - T['b1']) / spb; y = chao - 4 - 34 * 4 * u * (1 - u)
                pts = [(cx - 2, y)]
            else:
                u = (t - T['b2']) / spb; y = chao - 4 - 22 * 4 * u * (1 - u)
                pts = [(cx - 2 + d * u * 14, y) for d in (-1.5, -.5, .5, 1.5)]
            for (x, y) in pts:
                _bloco(tela, x, y, AMARELO, BRANCO, 13, lado=5)
        # blocos: voando em arco até a casa, depois pousados
        for a in alvos:
            if t < a['sai'] or t < T['b3']: continue
            if t >= a['pousa']:
                cor, luz = a['cor'], a['luz']
                if t - a['pousa'] < 1.5 / fps: cor = luz = BRANCO
                _bloco(tela, a['x'], a['y'], cor, luz, a['esc'])
            else:
                u = (t - max(a['sai'], T['b3'])) / max(1e-3, a['pousa'] - max(a['sai'], T['b3']))
                x0, y0 = a['de']
                x = x0 + (a['x'] - x0) * u
                y = y0 + (a['y'] - y0) * u - 30 * 4 * u * (1 - u)
                _bloco(tela, x, y, AMARELO, BRANCO, 13, lado=2)
        # brilho que corre pelas letras depois de fechar, uma volta por batida
        if t >= T['b4']:
            fase = ((t - T['b4']) / spb) % 1.0
            xs = W // 2 - 60 + fase * 150
            for a in alvos:
                if abs(a['x'] - xs) < 3: tela.ret(a['x'], a['y'], B, 1, BRANCO)
            if linhas_txt and t >= T['b4'] + spb * .5:
                tela.texto(linhas_txt[0], W // 2, chao + 24, BRANCO, tam=9, centro=True)
                if len(linhas_txt) > 1:
                    tela.texto(linhas_txt[1], W // 2, chao + 36, 8, tam=9, centro=True)
        # luz: bloom que respira com as batidas, flash no nome fechado
        x = tela.rgb[tela.buf].astype(np.float32) / 255
        bat = max([math.exp(-(t - T[k]) / .12) for k in ('b1', 'b2', 'b3', 'b4') if t >= T[k]] + [0])
        pos = [T['b4'] + k * spb for k in range(1, 6)]
        bat = max([bat] + [math.exp(-(t - p) / .14) * .6 for p in pos if t >= p])
        x = AC.iluminar(x, .75, .5, 1.4, 6.0, 1 + .8 * bat)
        if t >= T['b4']: x = x + .25 * math.exp(-(t - T['b4']) / .06)
        # fim: apaga nos últimos 4 quadros para o laço do Short não estalar
        rest = dur - t
        if rest < 4 / fps: x = x * (rest * fps / 4)
        rgb = (np.clip(x, 0, 1) * 255).astype(np.uint8)
        yield np.repeat(np.repeat(rgb, PX.ESCALA, 0), PX.ESCALA, 1)


def encerramento(W, H, fps, linhas_txt=('SUBSCRIBE',), seed=0):
    return _rodar(W, H, fps, OUTRO_S, OUTRO_S / 7.0, list(linhas_txt), seed)


def abertura(W, H, fps, seed=0):
    return _rodar(W, H, fps, INTRO_S, INTRO_S / 6.0, [], seed)


# =================================================================== som
def _env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def _quadrada(f, n, duty=.5):
    ph = (np.arange(n) / SR * f) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def _put(buf, s, t, ganho, pan=0.0):
    i = int(round(t * SR)); j = min(len(buf), i + len(s))
    if j <= i: return
    a = (pan + 1) * math.pi / 4
    buf[i:j, 0] += s[:j - i] * ganho * math.cos(a)
    buf[i:j, 1] += s[:j - i] * ganho * math.sin(a)


def _som(dur, spb, seed):
    import scipy.signal as sg
    rng = np.random.default_rng(seed + 77)
    T = _tempos(spb)
    n = int(dur * SR)
    out = np.zeros((n, 2), np.float32)
    raiz = 60 + int(rng.integers(0, 5))
    # quiques: blip de onda quadrada que sobe uma terça a cada batida + um bumbo curto
    for k, (chave, semi) in enumerate((('b1', 0), ('b2', 4), ('b3', 7))):
        m = int(.18 * SR)
        f = 440 * 2 ** ((raiz + 12 + semi - 69) / 12)
        tt = np.arange(m) / SR
        blip = _quadrada(f, m, .25) * _env(m, .002, .06)
        kick = np.sin(2 * np.pi * (45 + 120 * np.exp(-tt / .03)) * tt) * _env(m, .001, .09)
        _put(out, blip * .35 + kick * .8, T[chave], 1.0)
    # tiques de pouso: arpejo pentatônico subindo, um por bloco agrupado em 1/32
    penta = [0, 2, 4, 7, 9]
    passo = spb / 8
    for j in range(8):
        t = T['b3'] + spb * .12 + j * passo
        g = penta[j % 5] + 12 * (j // 5)
        m = int(.09 * SR)
        f = 440 * 2 ** ((raiz + 24 + g - 69) / 12)
        _put(out, _quadrada(f, m, .125) * _env(m, .001, .035) * .22, t, 1.0, -.5 + j / 7)
    # nome fechado: acorde de serras abafado + sub + ruído de prato
    m = int((dur - T['b4']) * SR)
    tt = np.arange(m) / SR
    acorde = np.zeros(m)
    for semi in (0, 7, 12, 16, 19):
        f = 440 * 2 ** ((raiz + semi - 69) / 12)
        for d in (-7, 0, 7):
            acorde += 2 * ((f * 2 ** (d / 1200) * tt + rng.uniform()) % 1) - 1
    b, a = sg.butter(2, 2600 / (SR / 2))
    acorde = sg.lfilter(b, a, acorde) / 15 * _env(m, .004, .9)
    sub = np.sin(2 * np.pi * 440 * 2 ** ((raiz - 24 - 69) / 12) * tt) * _env(m, .003, .7)
    rui = rng.standard_normal(m) * _env(m, .001, .35)
    b, a = sg.butter(2, 6000 / (SR / 2), 'high')
    rui = sg.lfilter(b, a, rui) * .12
    _put(out, acorde * .8 + sub * .5, T['b4'], 1.0)
    _put(out, rui, T['b4'], 1.0, .2); _put(out, rui, T['b4'] + .004, .8, -.2)
    k = int(.08 * SR)
    out[-k:] *= np.linspace(1, 0, k)[:, None]
    pk = np.abs(out).max()
    return (out / pk * .7).astype(np.float32) if pk > 0 else out


def som_encerramento(seed=0):
    return _som(OUTRO_S, OUTRO_S / 7.0, seed)


def som_abertura(seed=0):
    return _som(INTRO_S, INTRO_S / 6.0, seed)
