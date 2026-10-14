#!/usr/bin/env python3
"""Silhuetas em pixel, descritas como lista de ret�ngulos.

Cada forma vive numa caixa de 0 a 100 em x e em y (y=0 � o ch�o, y=100 o topo)
e � desenhada escalada para a altura que o simulador pedir. Ret�ngulo � a
primitiva certa aqui: em pixel art de 180 de largura, um pr�dio ou uma montanha
�, literalmente, alguns ret�ngulos — e escala sem deformar nem exigir arquivo.

Cada forma: (x, y, largura, altura, tom) com tom 0 = corpo, 1 = claro, 2 = escuro.
"""

FORMAS = {
    'pessoa': [(40, 0, 8, 38, 0), (52, 0, 8, 38, 0), (36, 36, 28, 34, 0),
               (42, 70, 16, 16, 1), (28, 52, 10, 20, 0), (62, 52, 10, 20, 0)],

    'cristo': [(30, 0, 40, 14, 2), (36, 14, 28, 10, 2),          # pedestal
               (44, 24, 12, 50, 0),                               # corpo
               (8, 60, 84, 8, 0),                                 # bra�os abertos
               (44, 74, 12, 12, 1), (46, 86, 8, 8, 1)],           # cabe�a

    'predio': [(22, 0, 56, 52, 0), (30, 52, 40, 30, 0), (40, 82, 20, 14, 0),
               (48, 96, 4, 4, 1)],

    # O morro tinha um pino fino de 8 de largura no topo, e num video de
    # montanhas ele lia como antena de predio. Montanha nao tem pino: tem
    # ombro largo e cume curto. Os degraus agora abrem mais embaixo e o
    # topo fecha chato, que e o que sobrevive quando o simulador estreita
    # a forma para caber na metade da tela.
    'morro': [(2, 0, 96, 16, 2), (10, 16, 80, 20, 0), (20, 36, 60, 20, 0),
              (30, 56, 40, 18, 0), (40, 74, 20, 16, 0), (44, 90, 12, 8, 1)],

    'torre': [(30, 0, 40, 6, 2), (38, 6, 24, 40, 0), (30, 46, 40, 10, 1),
              (42, 56, 16, 28, 0), (46, 84, 8, 16, 0)],

    # Tres degraus de 22 a 26 de altura liam como caixas empilhadas quando
    # o desenho e so contorno. Copa e cone: degrau fino e muitos.
    'arvore': [(46, 0, 8, 24, 2),
               (22, 24, 56, 13, 0), (26, 37, 48, 13, 0), (30, 50, 40, 12, 0),
               (34, 62, 32, 12, 0), (38, 74, 24, 11, 0), (43, 85, 14, 9, 0),
               (47, 94, 6, 6, 1)],

    'casa': [(16, 0, 68, 54, 0), (8, 54, 84, 10, 2), (24, 64, 52, 22, 2),
             (62, 72, 10, 26, 1)],

    'aviao': [(10, 30, 80, 16, 0), (36, 12, 20, 60, 1), (26, 46, 40, 10, 0),
              (84, 36, 10, 24, 2)],

    'baleia': [(6, 20, 76, 34, 0), (74, 44, 22, 24, 2), (24, 54, 22, 10, 1),
               (14, 36, 8, 8, 1)],

    'onda': [(0, 0, 100, 26, 2), (6, 26, 40, 20, 0), (46, 26, 48, 28, 0),
             (20, 46, 22, 14, 1), (58, 54, 26, 16, 1)],

    'foguete': [(40, 0, 20, 10, 2), (30, 10, 10, 20, 2), (60, 10, 10, 20, 2),
                (40, 10, 20, 64, 0), (44, 74, 12, 14, 1), (46, 88, 8, 10, 1)],

    'estadio': [(6, 0, 88, 30, 0), (14, 30, 72, 16, 2), (22, 46, 56, 8, 1),
                (30, 10, 40, 14, 1)],

    'carro': [(6, 10, 88, 26, 0), (24, 36, 52, 24, 1), (32, 40, 36, 16, 2),
              (18, 0, 20, 14, 2), (62, 0, 20, 14, 2)],

    'torre_tv': [(26, 0, 48, 8, 2), (40, 8, 20, 30, 0), (30, 38, 40, 14, 1),
                 (44, 52, 12, 28, 0), (48, 80, 4, 20, 2)],

    'gota': [(36, 0, 28, 30, 0), (40, 30, 20, 26, 0), (44, 56, 12, 22, 0),
             (47, 78, 6, 16, 0), (42, 12, 8, 8, 1)],
}


def desenhar(tela, nome, cx, base_y, alt_px, cores, larg_max=None):
    """Desenha a forma com a base em base_y e a altura pedida.

    `cores` s�o tr�s �ndices da paleta: (corpo, claro, escuro). Abaixo de uns
    6 pixels de altura a silhueta vira uma mancha s�, que � o comportamento
    certo — � o que faz a compara��o de escala doer.
    """
    f = FORMAS.get(nome)
    if not f: return
    if alt_px < 3:
        tela.ret(cx - max(1, alt_px // 2), base_y - max(1, alt_px),
                 max(1, alt_px), max(1, alt_px), cores[0])
        return
    k = alt_px / 100.0
    # a largura tem que ser limitada à parte da tela que cabe a esta forma:
    # sem isso um prédio de 200 px de altura sai com 180 px de largura e
    # engole a tela inteira
    larg = alt_px * 0.9
    if larg_max: larg = min(larg, larg_max)
    for x, y, w, h, tom in f:
        px = cx - larg / 2 + x / 100.0 * larg
        py = base_y - (y + h) * k
        tela.ret(round(px), round(py), max(1, round(w / 100.0 * larg)),
                 max(1, round(h * k)), cores[tom])
