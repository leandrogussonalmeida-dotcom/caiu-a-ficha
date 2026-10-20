#!/usr/bin/env python3
"""Acabamento de imagem do RITMO PIXEL: a luz que a paleta chapada não tem.

Tudo roda na tela BAIXA (180x320), antes de ampliar 6x por vizinho mais
próximo. Por isso o brilho, a vinheta e o flash também são blocos de 6x6:
a imagem continua sendo pixel art, só que iluminada, como em jogo moderno de
pixel (luz por cima do sprite), e não um filtro borrado em 1080p.

  brilho     o que é claro vaza luz em volta (bloom), em degraus, e respira
             com o bumbo
  vinheta    bordas mais escuras em anéis pontilhados (matriz de Bayer), o
             jeito 8-bit de fazer degradê
  flash      o drop clareia a tela por 1-2 quadros
  aberração  no impacto do drop o vermelho e o azul se separam 1 pixel
  troca      na mudança de gênero, a tela fecha em blocos de 4x4 (padrão
             de Bayer) e abre de uma vez no quadro do drop

Cada efeito obedece aos eventos da faixa (`Linha`), nunca ao áudio: o flash
cai no quadro do drop porque o drop é um evento, não porque foi detectado.

Força por peça em cfg['acabamento'] = dict(brilho=.55, vinheta=.32, ...);
`acabamento=False` desliga tudo (para comparar antes/depois).
"""
import numpy as np
from scipy.ndimage import gaussian_filter

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + .5) / 16

PADRAO = dict(brilho=.55, limiar=.58, raio=1.6, raio_largo=5.0, respira=.6,
              vinheta=.32, flash=.22, aberracao=True, troca=True, dur_troca=.16)


def iluminar(x, forca=.55, limiar=.58, raio=1.6, raio_largo=5.0, resp=1.0):
    """Bloom em degraus sobre RGB float (H, W, 3) em 0..1, na tela baixa."""
    lum = x.max(2)
    m = np.clip((lum - limiar) / (1 - limiar), 0, 1) ** 1.4
    fonte = x * m[..., None]
    g = gaussian_filter(fonte, (raio, raio, 0)) * .65 + \
        gaussian_filter(fonte, (raio_largo, raio_largo, 0)) * .55
    g = np.floor(g * resp * forca * 10) / 10                     # degraus de luz
    return x + g


class Acabamento:
    def __init__(self, L, cfg, W, H):
        c = cfg.get('acabamento', {})
        self.ligado = c is not False
        self.p = dict(PADRAO, **(c if isinstance(c, dict) else {}))
        self.L, self.W, self.H = L, W, H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
        bay = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
        # vinheta em 4 degraus, a passagem entre degraus pontilhada
        v = np.clip((r - .45) / .55, 0, 1) ** 1.6 * 4
        nivel = np.floor(v + bay)                                   # 0..4
        self.vin = (1 - self.p['vinheta'] * nivel / 4).astype(np.float32)[..., None]
        # blocos 4x4 para a transição: cada bloco tem um limiar de Bayer
        by, bx = np.mgrid[0:H, 0:W]
        self.bloco = BAYER4[(by // 4) % 4, (bx // 4) % 4].astype(np.float32)
        # trocas de gênero: instantes em que o gênero muda de uma seção para a próxima
        sec = L.F.secoes
        self.trocas = [sec[i]['t0'] for i in range(1, len(sec))
                       if sec[i]['gen'] != sec[i - 1]['gen'] and sec[i]['papel'] != 'fim']

    def aplicar(self, tela, t):
        """Índices da tela -> RGB baixo (H, W, 3) uint8, acabado."""
        rgb = tela.rgb[tela.buf]
        if not self.ligado: return rgb
        p, L = self.p, self.L
        x = rgb.astype(np.float32) / 255.0
        # ---- brilho: o que passa do limiar acende o entorno, em degraus
        if p['brilho'] > 0:
            x = iluminar(x, p['brilho'], p['limiar'], p['raio'], p['raio_largo'],
                         1 + p['respira'] * L.env('kick', t, .11))
        # ---- flash do drop
        if p['flash'] > 0:
            f = L.env('drop', t, .07) * p['flash']
            if f > .01: x = x + f
        x = x * self.vin
        # ---- aberração no impacto do drop
        if p['aberracao'] and L.desde('drop', t) < .1 and t > .5:
            x[:, 1:, 0] = x[:, :-1, 0]
            x[:, :-1, 2] = x[:, 1:, 2]
        out = (np.clip(x, 0, 1) * 255).astype(np.uint8)
        # ---- troca de gênero: fecha e abre em blocos
        if p['troca'] and self.trocas:
            # fecha nos últimos instantes ANTES da troca e abre de uma vez na
            # batida: o mundo novo aparece no quadro do drop, que é o impacto
            prox = [a for a in self.trocas if a > t]
            if prox:
                u = (prox[0] - t) / p['dur_troca']       # 1 -> 0 chegando na troca
                if u < 1:
                    m = self.bloco < (1 - u) * .94
                    out[m] = tela.rgb[0]
        return out
