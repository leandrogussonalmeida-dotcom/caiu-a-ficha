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



# --------------------------------------------------------------- plantas
def folha():
    esq = elipse(50, 50, 26, 44, 90, 270, 16)
    dir_ = elipse(50, 50, 26, 44, 270, 450, 16)
    talo = poli((50, 6), (50, 94))
    nerv = []
    for k in range(1, 6):
        y = 20 + k * 12
        nerv += [LEVANTA, (50, y), (50 - 18 + k * 1.4, y + 10)]
        nerv += [LEVANTA, (50, y), (50 + 18 - k * 1.4, y + 10)]
    return juntar(esq, dir_, [LEVANTA], talo, nerv)


def flor():
    pet = []
    for k in range(6):
        a = k * 60
        pet += [LEVANTA] + elipse(50 + 22 * math.cos(math.radians(a + 90)),
                                  62 + 22 * math.sin(math.radians(a + 90)),
                                  13, 9, 0, 360, 12, giro=a + 90)
    miolo = elipse(50, 62, 9, 9)
    caule = poli((50, 53), (48, 24), (50, 6))
    f1 = elipse(36, 28, 13, 7, -20, 170, 10)
    f2 = elipse(64, 20, 13, 7, 10, 200, 10)
    return juntar([LEVANTA], caule, [LEVANTA], f1, [LEVANTA], f2,
                  pet, [LEVANTA], miolo)


def cacto():
    """O braco e um contorno COM ESPESSURA, nao uma linha: sai do tronco,
    sobe e volta. Montado com arco solto ele nao encostava no corpo e
    parecia um risco ao lado do cacto."""
    tronco = juntar(poli((38, 4), (38, 62)),
                    elipse(50, 62, 12, 12, 180, 0, 12),
                    poli((62, 62), (62, 4), (38, 4)))
    braco_e = juntar(poli((38, 34), (24, 34)),
                     elipse(24, 42, 8, 8, 270, 180, 8),
                     poli((16, 42), (16, 62)),
                     elipse(23, 62, 7, 7, 180, 0, 8),
                     poli((30, 62), (30, 48)),
                     elipse(34, 48, 4, 4, 180, 270, 5),
                     poli((34, 44), (38, 44)))
    braco_d = juntar(poli((62, 46), (76, 46)),
                     elipse(76, 54, 8, 8, 270, 0, 8),
                     poli((84, 54), (84, 72)),
                     elipse(77, 72, 7, 7, 0, 180, 8),
                     poli((70, 72), (70, 60)),
                     elipse(66, 60, 4, 4, 0, -90, 5),
                     poli((66, 56), (62, 56)))
    espinhos = []
    for y in range(12, 60, 11):
        espinhos += [LEVANTA, (38, y), (33, y + 3)]
        espinhos += [LEVANTA, (62, y), (67, y + 3)]
    return juntar(tronco, [LEVANTA], braco_e, [LEVANTA], braco_d, espinhos)


def cogumelo():
    chapeu = elipse(50, 56, 34, 24, 0, 180, 18)
    base = poli((16, 56), (36, 54), (64, 54), (84, 56))
    pe = poli((38, 54), (36, 14), (44, 8), (56, 8), (64, 14), (62, 54))
    pin = juntar(elipse(36, 66, 6, 5), [LEVANTA], elipse(58, 70, 5, 4),
                 [LEVANTA], elipse(68, 60, 4, 3))
    return juntar(chapeu, base, [LEVANTA], pe, [LEVANTA], pin)


# --------------------------------------------------------------- objetos
def chave():
    anel = elipse(20, 50, 15, 15, 40, 320, 16)
    haste = poli((31, 60), (84, 60), (84, 44), (78, 44), (78, 54),
                 (70, 54), (70, 40), (64, 40), (64, 54), (31, 54))
    furo = elipse(20, 50, 6, 6)
    return juntar(anel, haste, [LEVANTA], furo)


def tesoura():
    l1 = poli((46, 46), (90, 86), (96, 78), (54, 40))
    l2 = poli((54, 46), (96, 14), (90, 6), (46, 40))
    a1 = elipse(26, 60, 14, 12, -40, 300, 14)
    a2 = elipse(26, 30, 14, 12, 60, 400, 14)
    par = elipse(50, 43, 3, 3)
    return juntar(l1, [LEVANTA], l2, [LEVANTA], a1, [LEVANTA], a2,
                  [LEVANTA], par)


def xicara():
    corpo = poli((26, 66), (30, 18), (38, 10), (62, 10), (70, 18), (74, 66))
    boca = elipse(50, 66, 24, 7)
    asa = elipse(80, 44, 14, 16, 280, 80, 12)
    pires = juntar(poli((14, 10), (86, 10)), elipse(50, 10, 36, 6, 180, 360, 12))
    return juntar(corpo, boca, [LEVANTA], asa, [LEVANTA], pires)


def oculos():
    le = elipse(28, 50, 19, 15)
    ld = elipse(72, 50, 19, 15)
    ponte = elipse(50, 54, 9, 7, 0, 180, 8)
    h1 = poli((9, 56), (0, 66))
    h2 = poli((91, 56), (100, 66))
    return juntar(le, [LEVANTA], ld, [LEVANTA], ponte, [LEVANTA], h1,
                  [LEVANTA], h2)


def ampulheta():
    cx = juntar(poli((20, 94), (80, 94)), poli((74, 94), (54, 52), (74, 10)),
                poli((74, 10), (20, 10)), poli((26, 10), (46, 52), (26, 94)))
    areia_c = poli((30, 88), (70, 88), (52, 60), (48, 60), (30, 88))
    areia_b = poli((34, 14), (66, 14), (58, 28), (42, 28), (34, 14))
    fio = poli((50, 58), (50, 22))
    return juntar(cx, [LEVANTA], areia_c, [LEVANTA], areia_b, [LEVANTA], fio)


# ----------------------------------------------------------- arquitetura
def igreja():
    corpo = poli((22, 4), (22, 54), (50, 76), (78, 54), (78, 4), (22, 4))
    torre = poli((44, 76), (44, 88), (50, 96), (56, 88), (56, 76))
    cruz = juntar(poli((50, 96), (50, 100)), [LEVANTA], poli((46, 98), (54, 98)))
    porta = juntar(poli((44, 4), (44, 24)), elipse(50, 24, 6, 8, 180, 0, 8),
                   poli((56, 24), (56, 4)))
    jan = juntar(elipse(32, 36, 5, 7), [LEVANTA], elipse(68, 36, 5, 7))
    return juntar(corpo, [LEVANTA], torre, cruz, [LEVANTA], porta,
                  [LEVANTA], jan)


def farol():
    corpo = poli((34, 4), (40, 62), (60, 62), (66, 4), (34, 4))
    topo = poli((36, 62), (64, 62), (62, 70), (38, 70), (36, 62))
    casa = poli((40, 70), (40, 84), (60, 84), (60, 70))
    teto = poli((36, 84), (50, 94), (64, 84))
    luz = juntar([LEVANTA], poli((40, 77), (20, 72)), [LEVANTA],
                 poli((60, 77), (80, 72)), [LEVANTA], poli((40, 79), (22, 86)),
                 [LEVANTA], poli((60, 79), (78, 86)))
    faixas = []
    for y in (18, 34, 50):
        faixas += [LEVANTA, (35 + y * .04, y), (65 - y * .04, y)]
    return juntar(corpo, topo, casa, teto, luz, faixas)


def ponte():
    """Era arco e cabo ao mesmo tempo e virava um emaranhado. Ponte pensil
    tem tres coisas: o tabuleiro, as duas torres e o cabo pendurado entre
    elas - e os tirantes verticais ligando cabo e tabuleiro."""
    tab = poli((2, 40), (98, 40))
    t1 = juntar(poli((18, 34), (18, 88)), [LEVANTA], poli((24, 34), (24, 88)),
                [LEVANTA], poli((18, 88), (24, 88)),
                [LEVANTA], poli((18, 70), (24, 70)))
    t2 = juntar(poli((76, 34), (76, 88)), [LEVANTA], poli((82, 34), (82, 88)),
                [LEVANTA], poli((76, 88), (82, 88)),
                [LEVANTA], poli((76, 70), (82, 70)))
    def cabo_y(x):
        f = (x - 50) / 29.0
        return 50 + 38 * f * f
    cabo = [(x, cabo_y(x)) for x in range(21, 81, 4)]
    rampa = [LEVANTA, (2, 76), (21, cabo_y(21)), LEVANTA, (98, 76), (79, cabo_y(79))]
    tirantes = []
    for x in range(25, 78, 7):
        tirantes += [LEVANTA, (x, 40), (x, cabo_y(x))]
    agua = [LEVANTA, (2, 30), (98, 30), LEVANTA, (6, 24), (44, 24),
            LEVANTA, (56, 24), (94, 24)]
    return juntar(tab, [LEVANTA], t1, [LEVANTA], t2, [LEVANTA], cabo,
                  rampa, tirantes, agua)


def guarda_chuva():
    cupula = elipse(50, 52, 38, 30, 0, 180, 20)
    festo = []
    for k in range(4):
        x0 = 12 + k * 19
        festo += [LEVANTA, (x0, 52)] + elipse(x0 + 9.5, 52, 9.5, 8, 180, 360, 8)
    cabo = juntar(poli((50, 52), (50, 14)), elipse(42, 14, 8, 8, 0, 180, 8))
    ponta = poli((50, 82), (50, 92))
    return juntar(cupula, festo, [LEVANTA], cabo, [LEVANTA], ponta)


def violao():
    corpo = juntar(elipse(40, 34, 26, 24, 90, 450, 24))
    cintura = juntar(elipse(56, 58, 19, 17, 100, 440, 20))
    braco = poli((64, 70), (86, 88), (92, 82), (70, 64))
    cabeca = poli((86, 88), (92, 98), (99, 92), (92, 82))
    boca = elipse(42, 36, 8, 8)
    cordas = []
    for k in range(4):
        cordas += [LEVANTA, (30 + k * 6, 14), (78 + k * 3, 76)]
    return juntar(corpo, [LEVANTA], cintura, [LEVANTA], braco, cabeca,
                  [LEVANTA], boca, cordas)


def lampada():
    bulbo = elipse(50, 58, 26, 28, -60, 240, 20)
    gargalo = poli((37, 36), (37, 26), (63, 26), (63, 36))
    rosca = []
    for k in range(3):
        y = 24 - k * 6
        rosca += [LEVANTA, (37, y), (63, y)]
    base = poli((37, 6), (63, 6))
    fil = juntar(poli((44, 50), (46, 62)), poli((46, 62), (50, 54)),
                 poli((50, 54), (54, 62)), poli((54, 62), (56, 50)))
    return juntar(bulbo, gargalo, rosca, [LEVANTA], base, [LEVANTA], fil)


def relogio():
    aro = elipse(50, 50, 38, 38)
    aro2 = elipse(50, 50, 33, 33)
    marcas = []
    for k in range(12):
        a = math.radians(k * 30)
        marcas += [LEVANTA, (50 + 30 * math.cos(a), 50 + 30 * math.sin(a)),
                   (50 + 25 * math.cos(a), 50 + 25 * math.sin(a))]
    pont = juntar(poli((50, 50), (50, 74)), [LEVANTA], poli((50, 50), (68, 42)))
    return juntar(aro, [LEVANTA], aro2, marcas, [LEVANTA], pont)


PLANTAS = {'FOLHA': folha, 'FLOR': flor, 'CACTO': cacto, 'COGUMELO': cogumelo}
OBJETOS = {'CHAVE': chave, 'TESOURA': tesoura, 'XICARA': xicara,
           'OCULOS': oculos, 'AMPULHETA': ampulheta,
           # VIOLAO ficou de fora: o corpo em duas elipses com o braco por
           # cima vira um no, e desenho que nao se reconhece nao entra num
           # video chamado "adivinha o desenho".
           'GUARDA-CHUVA': guarda_chuva,
           'LAMPADA': lampada, 'RELOGIO': relogio}
PREDIOS = {'IGREJA': igreja, 'FAROL': farol, 'PONTE': ponte}


BICHOS = {'PEIXE': peixe, 'PASSARO': passaro, 'GATO': gato,
          'CARACOL': caracol, 'BORBOLETA': borboleta,
          'TARTARUGA': tartaruga, 'ELEFANTE': elefante}



# ------------------------------------------------------------- transporte
def barco():
    casco = poli((8, 34), (92, 34), (78, 12), (22, 12), (8, 34))
    mastro = poli((50, 34), (50, 94))
    vela_g = poli((50, 88), (84, 44), (50, 44))
    vela_p = poli((50, 84), (22, 48), (50, 48))
    mar = [LEVANTA, (2, 8), (40, 8), LEVANTA, (54, 8), (98, 8)]
    return juntar(casco, [LEVANTA], mastro, [LEVANTA], vela_g,
                  [LEVANTA], vela_p, mar)


def carro():
    corpo = poli((6, 22), (10, 42), (28, 42), (40, 60), (68, 60), (76, 42),
                 (94, 42), (96, 22), (6, 22))
    jan1 = poli((34, 42), (42, 56), (54, 56), (54, 42), (34, 42))
    jan2 = poli((58, 42), (58, 56), (66, 56), (72, 42), (58, 42))
    r1 = juntar(elipse(28, 20, 12, 12), [LEVANTA], elipse(28, 20, 5, 5))
    r2 = juntar(elipse(74, 20, 12, 12), [LEVANTA], elipse(74, 20, 5, 5))
    return juntar(corpo, [LEVANTA], jan1, [LEVANTA], jan2, [LEVANTA], r1,
                  [LEVANTA], r2)


def aviao():
    fus = juntar(elipse(50, 52, 46, 9, 0, 180, 18),
                 poli((4, 52), (10, 44), (88, 44)),
                 elipse(96, 50, 8, 6, 270, 90, 8))
    asa = poli((54, 50), (40, 18), (56, 18), (74, 50))
    asa2 = poli((54, 56), (42, 84), (58, 84), (74, 56))
    leme = poli((10, 56), (4, 80), (18, 80), (22, 58))
    jan = []
    for x in range(34, 84, 9):
        jan += [LEVANTA] + elipse(x, 52, 3, 3)
    return juntar(fus, [LEVANTA], asa, [LEVANTA], asa2, [LEVANTA], leme, jan)


def bicicleta():
    r1 = juntar(elipse(22, 26, 21, 21), [LEVANTA], elipse(22, 26, 4, 4))
    r2 = juntar(elipse(78, 26, 21, 21), [LEVANTA], elipse(78, 26, 4, 4))
    quadro = poli((22, 26), (44, 26), (34, 58), (62, 58), (44, 26),
                  (62, 58), (78, 26), (44, 26))
    guidao = juntar(poli((62, 58), (66, 70)), [LEVANTA], poli((56, 70), (76, 70)))
    selim = juntar(poli((34, 58), (32, 68)), [LEVANTA], poli((24, 70), (42, 68)))
    raios = []
    for k in range(6):
        a = math.radians(k * 60)
        raios += [LEVANTA, (22, 26), (22 + 19 * math.cos(a), 26 + 19 * math.sin(a))]
        raios += [LEVANTA, (78, 26), (78 + 19 * math.cos(a), 26 + 19 * math.sin(a))]
    return juntar(r1, [LEVANTA], r2, [LEVANTA], quadro, [LEVANTA], guidao,
                  [LEVANTA], selim, raios)


# ---------------------------------------------------------------- cozinha
def garrafa():
    corpo = poli((30, 4), (30, 50), (40, 64), (40, 86))
    gargalo = juntar(poli((40, 86), (38, 94)), poli((38, 94), (62, 94)),
                     poli((62, 94), (60, 86)))
    volta = poli((60, 86), (60, 64), (70, 50), (70, 4), (30, 4))
    rotulo = juntar([LEVANTA], poli((30, 18), (70, 18)), [LEVANTA],
                    poli((30, 38), (70, 38)))
    return juntar(corpo, gargalo, volta, rotulo)


def panela():
    corpo = poli((20, 12), (24, 56), (76, 56), (80, 12), (20, 12))
    tampa = juntar(elipse(50, 56, 32, 10, 0, 180, 14),
                   poli((50, 66), (50, 76)), elipse(50, 78, 7, 5))
    cabo1 = elipse(14, 46, 10, 8, 270, 90, 8)
    cabo2 = elipse(86, 46, 10, 8, 90, 270, 8)
    return juntar(corpo, [LEVANTA], tampa, [LEVANTA], cabo1, [LEVANTA], cabo2)


def garfo():
    dentes = []
    for x in (36, 44, 52, 60):
        dentes += [LEVANTA, (x, 94), (x, 68)]
    base = juntar(elipse(48, 68, 14, 10, 180, 360, 10),
                  poli((44, 58), (44, 8)), poli((44, 8), (52, 8)),
                  poli((52, 8), (52, 58)))
    return juntar(dentes, [LEVANTA], base)


def casa():
    corpo = poli((16, 4), (16, 54), (84, 54), (84, 4), (16, 4))
    telhado = poli((8, 54), (50, 86), (92, 54))
    porta = poli((40, 4), (40, 30), (58, 30), (58, 4))
    jan1 = juntar(poli((24, 34), (24, 48)), poli((24, 48), (36, 48)),
                  poli((36, 48), (36, 34)), poli((36, 34), (24, 34)),
                  [LEVANTA], poli((30, 34), (30, 48)))
    jan2 = juntar(poli((64, 34), (64, 48)), poli((64, 48), (76, 48)),
                  poli((76, 48), (76, 34)), poli((76, 34), (64, 34)),
                  [LEVANTA], poli((70, 34), (70, 48)))
    chamine = poli((68, 68), (68, 86), (78, 86), (78, 60))
    return juntar(corpo, [LEVANTA], telhado, [LEVANTA], chamine,
                  [LEVANTA], porta, [LEVANTA], jan1, [LEVANTA], jan2)


TRANSPORTE = {'BARCO': barco, 'CARRO': carro, 'AVIAO': aviao,
              'BICICLETA': bicicleta}
COZINHA = {'GARRAFA': garrafa, 'PANELA': panela, 'GARFO': garfo,
           'XICARA': xicara}


TUDO = {}


def desenho(nome, levantar=True):
    """`levantar=False` costura tudo numa linha so, sem tirar a pena do
    papel: e o que a LOUSA exige, porque o brinquedo nao levanta o traco.
    A NANQUIM usa o padrao, com as levantadas."""
    if not TUDO:
        for d in (BICHOS, PLANTAS, OBJETOS, PREDIOS, TRANSPORTE,
                  COZINHA, {'CASA': casa}): TUDO.update(d)
    pts = caber(TUDO[nome]())
    if not levantar:
        pts = [p for p in pts if p[0] is not None]
    return {'nome': nome, 'pontos': arredondar(pts)}
