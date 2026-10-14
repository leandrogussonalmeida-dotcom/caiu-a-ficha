#!/usr/bin/env python3
"""Desenho de traço contínuo montado por geometria, não digitado à mão.

A primeira tentativa foi digitar vértices num JSON. O peixe saiu aceitável,
o gato saiu um borrão com orelhas. Digitar contorno de bicho em coordenadas
é difícil de fazer bem e impossível de fazer 125 vezes.

Aqui o desenho é composto: elipse, arco, polígono, e um `juntar` que liga as
peças na ordem em que a mão as faria. A saída é a mesma lista de pontos que
a LOUSA e a NANQUIM já consomem, então nada no motor muda.

Convenção: caixa de 0 a 100 em x e em y, **y para cima** (0 é o chão), que é
a mesma das `formas`.
"""
import math


def elipse(cx, cy, rx, ry, a0=0, a1=360, n=None, giro=0):
    """Arco de elipse de a0 a a1 graus. n pontos — por padrão um a cada 12°."""
    n = n or max(6, int(abs(a1 - a0) / 12))
    pts = []
    g = math.radians(giro)
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * math.cos(g) - y * math.sin(g),
                    cy + x * math.sin(g) + y * math.cos(g)))
    return pts


def poli(*pts):
    return [tuple(p) for p in pts]


LEVANTA = (None, None)      # a pena sai do papel entre uma peça e a seguinte


def juntar(*partes):
    """Liga as peças numa linha só, sem repetir o ponto de emenda.
    Uma peça igual a [LEVANTA] tira a pena do papel ali."""
    saida = []
    for p in partes:
        if (saida and p and saida[-1] != LEVANTA and p[0] != LEVANTA
                and abs(saida[-1][0] - p[0][0]) < .01
                and abs(saida[-1][1] - p[0][1]) < .01):
            p = p[1:]
        saida.extend(p)
    return saida


def arredondar(pts, casas=1):
    return [[None, None] if (x is None or y is None)
            else [round(x, casas), round(y, casas)] for x, y in pts]


def caber(pts, margem=6):
    """Reescala o desenho para ocupar a caixa inteira com uma margem.

    Sem isso cada bicho sai de um tamanho e o vídeo fica desigual — e o
    pequeno fica ilegível na miniatura, que é onde a pessoa decide se assiste.
    """
    reais = [p for p in pts if p[0] is not None]
    xs = [p[0] for p in reais]; ys = [p[1] for p in reais]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w <= 0 or h <= 0: return pts
    k = min((100 - 2 * margem) / w, (100 - 2 * margem) / h)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return [LEVANTA if x is None else (50 + (x - cx) * k, 50 + (y - cy) * k)
            for x, y in pts]


# ---------------------------------------------------------------- bichos
def peixe():
    corpo = elipse(52, 50, 34, 20, 160, -160, 22)      # corpo, aberto na cauda
    cauda = poli((18, 50), (4, 66), (8, 50), (4, 34), (18, 50))
    olho = elipse(70, 56, 4, 4)
    barb = elipse(52, 50, 20, 11, -150, -30, 10)       # linha lateral
    return juntar(corpo, cauda, [LEVANTA], barb, [LEVANTA], olho)


def passaro():
    """Corpo em gota, cabeca encaixada e bico. O que nao lia era a asa
    desenhada por cima do corpo: duas elipses sobrepostas viram um no.
    A asa agora e um arco solto dentro do corpo, com a pena levantada."""
    corpo = juntar(
        elipse(44, 44, 28, 20, 150, -60, 18),      # costas e peito
        poli((58, 28), (34, 22), (14, 32)),        # barriga ate a cauda
        poli((14, 32), (2, 24), (6, 42), (0, 50), (16, 52)))
    cabeca = elipse(74, 60, 13, 13, 200, -40, 14)
    bico = poli((86, 52), (99, 56), (85, 62))
    asa = elipse(44, 46, 16, 8, 20, 200, 12)
    olho = elipse(78, 64, 2.6, 2.6)
    return juntar(corpo, cabeca, bico, [LEVANTA], asa, [LEVANTA], olho)


def gato():
    """Um contorno so: sobe pelo lado esquerdo, as duas orelhas no topo, e
    desce pelo direito. Corpo e cabeca em pecas separadas davam uma cabeca
    boa flutuando sobre um borrao."""
    lado_e = poli((34, 6), (28, 24), (26, 44), (28, 60))
    orelha_e = poli((28, 60), (24, 84), (42, 70))
    topo = elipse(50, 66, 22, 14, 160, 20, 12)
    orelha_d = poli((58, 70), (76, 84), (72, 60))
    lado_d = poli((72, 60), (74, 44), (72, 24), (66, 6))
    base = poli((66, 6), (34, 6))
    # o rabo estava centrado em x=22, dentro do corpo (26 a 74):
    # parecia um risco solto atravessando o gato
    rabo = elipse(82, 26, 14, 20, 110, -70, 12)
    oe = elipse(42, 62, 3, 3)
    od = elipse(58, 62, 3, 3)
    focinho = poli((50, 54), (46, 58), (54, 58), (50, 54))
    return juntar(lado_e, orelha_e, topo, orelha_d, lado_d, base,
                  [LEVANTA], rabo, [LEVANTA], focinho, [LEVANTA], oe,
                  [LEVANTA], od)


def caracol():
    casca = []
    for i in range(70):                                 # espiral de verdade
        a = math.radians(i * 16)
        r = 4 + i * .5
        casca.append((58 + r * math.cos(a), 56 + r * math.sin(a)))
    casca.reverse()
    corpo = poli((casca[-1][0], casca[-1][1]), (24, 26), (10, 22), (6, 16),
                 (16, 12), (44, 12), (58, 18))
    antena = poli((16, 12), (10, 30), (12, 34), (8, 30), (16, 12))
    return juntar(casca, corpo, antena)


def borboleta():
    """As quatro asas saem do mesmo eixo e o traco VOLTA ao eixo entre uma
    e outra. Sem essa volta as asas se cruzavam no meio da figura."""
    baixo, alto = (50, 26), (50, 76)
    asa_se = elipse(32, 64, 20, 15, -30, 210, 16)
    asa_sd = elipse(68, 64, 20, 15, 210, -30, 16)
    asa_ie = elipse(34, 38, 15, 12, 170, -10, 12)
    asa_id = elipse(66, 38, 15, 12, 190, 10, 12)
    ant = poli(alto, (40, 92), (43, 94), alto, (60, 92), (57, 94))
    return juntar([baixo], [alto], asa_se, [alto], asa_sd, [baixo],
                  asa_id, [baixo], asa_ie, [baixo], [alto], ant)


def tartaruga():
    casco = elipse(50, 52, 32, 24, 0, 180, 18)
    barriga = elipse(50, 52, 32, 8, 180, 360, 12)
    cabeca = elipse(86, 50, 12, 9, 150, -150, 12)
    pata1 = poli((26, 34), (18, 24), (30, 28))
    pata2 = poli((62, 32), (58, 20), (70, 28))
    rabo = poli((18, 48), (6, 44), (18, 42))
    linhas = elipse(50, 52, 16, 12, 0, 180, 10)
    return juntar(casco, barriga, rabo, pata1, pata2, cabeca, linhas)


def elefante():
    corpo = elipse(44, 48, 30, 24, 20, 340, 22)
    cabeca = elipse(76, 56, 18, 18, 120, -120, 16)
    tromba = poli((84, 42), (92, 28), (88, 14), (78, 10), (74, 18), (82, 22))
    orelha = elipse(70, 60, 14, 16, -60, 240, 14)
    perna1 = poli((28, 24), (26, 6), (38, 6), (38, 26))
    perna2 = poli((54, 24), (54, 6), (66, 6), (64, 26))
    olho = elipse(80, 62, 3, 3)
    return juntar(corpo, perna1, perna2, cabeca, orelha, olho, tromba)


BICHOS = {'PEIXE': peixe, 'PASSARO': passaro, 'GATO': gato,
          'CARACOL': caracol, 'BORBOLETA': borboleta,
          'TARTARUGA': tartaruga, 'ELEFANTE': elefante}


def desenho(nome):
    return {'nome': nome, 'pontos': arredondar(caber(BICHOS[nome]()))}
