#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep16 — Como o processador pensa (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

Protagonistas: o bit (um pixel aceso que corre pelos fios: é a frente de
cada 1 que chega) e o contador de programa (PC), que sobe. Toda porta,
somador e o processador de brinquedo são SIMULADOS (`ep16_desenho.Circuito`
e `ep16_desenho.CPU`): nenhum 0 ou 1 da tela é escrito à mão. O relógio do
processador lê as batidas da própria trilha (eventos 'batida' de
longo.Trilha), as mesmas que viram som.

    python3 ep16_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep16_motor.py <saida.mp4> bits ciclo       # só esses capítulos (teste)
    python3 ep16_motor.py --folha <saida.png> [ids]    # quadros por capítulo (FR=.3,.8)
"""
import math, os, sys, bisect
import numpy as np
import pixelengine as PX
import longo as LG
import ep16_desenho as D                      # registra a paleta 'ep16' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, ease, dither, poligono, linha_grossa, painel, texto_marcado,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, VERDE, PRETO, ROSA, ROXO, LATAO, MISTURA, MISTURA2, CHAMA0, CHAMA1,
                   AGUA1)
from ep16_desenho import (Fio, Circuito, Mosfet, CPU, ETAPAS, rotulo, centro_preso, seta, bloco, caixa,
                          bit_luz, celula, porta, porta_forma, chave_mos, tabela, die, placa, pacote,
                          mascara_poligono, pintar, texto_instr, binario, dec, milhar, clamp, lerp, suave,
                          SIP0, SIP1, SIP2, SIN0, SIN1, SIN2, OX0, OX1, COB0, COB1, COB2, DIE0, DIE1, DIE2,
                          DIE3, PCB0, PCB1, PCB2, POR0, POR1, POR2, FIO0)
import ritmo_marca as RM
from ep16_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 1616, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: arranjo estreito, sem painel
PX0 = 306                     # coluna do painel da direita
SR = LG.SR
GHZ = 3.0e9                   # relógio de referência (F6)
C_LUZ = 299792458.0           # m/s (F11)
TRANS_CHIP = 28_000_000_000   # F8
TRANS_1971 = 2250             # F10


class Cena:
    legenda = True
    brilho = None
    XV = 150                   # centro do recorte vertical (x do corte + 90)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.L = trilha.L
        self.bt = [e['t'] - self.t0 for e in self.L.entre('batida', self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    # ---- batidas
    def nb(self, t):
        """Quantas batidas já tocaram até t (a do instante 0 conta)."""
        return bisect.bisect_right(self.bt, t + 1e-6)

    def tb(self, k):
        if k < len(self.bt): return self.bt[k]
        p = self.bt[1] - self.bt[0] if len(self.bt) > 1 else .75
        return self.bt[-1] + (k - len(self.bt) + 1) * p

    def desde_batida(self, t):
        k = self.nb(t) - 1
        return t - self.tb(k) if k >= 0 else 9.0

    # ---- moldura
    def fundo(self, tela, t):
        D.grade_fundo(tela, W, t)
        if not VERTICAL:
            tela.ret(298, 0, 1, PALCO_H, TRACO)
            tela.ret(299, 0, W - 299, PALCO_H, FUNDO)

    def ptxt(self, tela, txt, y, cor=ACO3, tam=9, x=PX0):
        if not VERTICAL: tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)

    def ptit(self, tela, txt, y=6, cor=ACO3):
        if VERTICAL: return
        tela.texto(txt, PX0, y, cor, tam=9, contorno=PRETO)
        tela.ret(PX0, y + 10, 160, 1, FUNDO3)

    def vtxt(self, tela, txt, cor=BRANCO, y=5, tam=9):
        """Leitura curta no topo do recorte vertical (só nos Shorts)."""
        if VERTICAL: centro_preso(tela, txt, self.XV, y, cor, tam=tam, xmin=self.XV - 88, xmax=self.XV + 88)

    # ---- sons curtos (seno com decaimento: pico baixo, sem estalo)
    def tique(self, fx, t, f=1500.0, dur=.05, g=.06, pan=0.0):
        n = int(dur * SR); tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4)) * np.minimum(1, tt / .002)
        fx.put(y.astype(np.float32), self.t0 + t, g, pan)

    def nota(self, fx, t, m, dur=.08, g=.05, pan=0.0):
        self.tique(fx, t, 440 * 2 ** ((m - 69) / 12), dur, g, pan)


def media_degrau(fn, t, rampa=.25, n=6):
    """Suaviza uma função de degrau (0/1) numa rampa curta."""
    return sum(fn(t - rampa * k / (n - 1)) for k in range(n)) / n


def fio_reto(a, b, xm=None):
    """Fio em ângulo reto de a até b, dobrando em x = xm."""
    if xm is None: xm = (a[0] + b[0]) / 2
    return Fio([a, (xm, a[1]), (xm, b[1]), b])


# ============================================================ 0 gancho
class Gancho(Cena):
    VEL = 160.0                     # px/s do bit nos fios

    def preparar(self):
        rng = np.random.default_rng(16)
        self.flip = [int(x) for x in rng.integers(0, 4, 64)]
        estados = [[1, 0, 0, 1]]
        for f in self.flip:
            e = list(estados[-1]); e[f] ^= 1; estados.append(e)
        self.est = estados
        s = 1.2
        self.cel = [(10, 30), (10, 64), (10, 126), (10, 160)]
        g1 = porta_forma('E', 80, 50, s); g2 = porta_forma('OU', 80, 140, s)
        g3 = porta_forma('XOR', 160, 95, s); g4 = porta_forma('NAO', 226, 95, s)
        self.g = (g1, g2, g3, g4)
        cs = [(x + 14, y + 7) for x, y in self.cel]
        self.f = {
            'x0': fio_reto(cs[0], g1[1][0], 56), 'x1': fio_reto(cs[1], g1[1][1], 56),
            'x2': fio_reto(cs[2], g2[1][0], 56), 'x3': fio_reto(cs[3], g2[1][1], 56),
            'g1': fio_reto(g1[2], g3[1][0], 136), 'g2': fio_reto(g2[2], g3[1][1], 140),
            'g3': Fio([g3[2], g4[1][0]]), 'g4': Fio([g4[2], (276, 95)]),
        }
        C = Circuito()
        for i in range(4): C.entrada(f'x{i}', (lambda i: lambda t: self.ent(i, t))(i))
        dw = lambda n: self.f[n].L / self.VEL
        C.porta('g1', 'E', [('x0', dw('x0')), ('x1', dw('x1'))], .1)
        C.porta('g2', 'OU', [('x2', dw('x2')), ('x3', dw('x3'))], .1)
        C.porta('g3', 'XOR', [('g1', dw('g1')), ('g2', dw('g2'))], .1)
        C.porta('g4', 'NAO', [('g3', dw('g3'))], .1)
        self.C = C

    def ent(self, i, t):
        k = max(0, self.nb(t) - 1) if t >= 0 else 0
        return self.est[min(k, len(self.est) - 1)][i]

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        C = self.C
        frentes = []
        for n, f in self.f.items():
            frentes += f.desenhar(tela, C.no_fio(n, f.L / self.VEL, t), t, herois=False)
        for nome, tipo, x0, y in (('g1', 'E', 80, 50), ('g2', 'OU', 80, 140), ('g3', 'XOR', 160, 95), ('g4', 'NAO', 226, 95)):
            porta(tela, tipo, x0, y, 1.2, saida=C.val(nome, t))
        for k, (x, y) in enumerate(self.cel):
            celula(tela, x, y, 14, 14, C.val(f'x{k}', t), tam=9)
        vo = C.val('g4', t - self.f['g4'].L / self.VEL)
        celula(tela, 276, 88, 16, 16, vo, tam=9)
        for x, y in frentes: bit_luz(tela, x, y, 1, 2.6)
        # painel: quantos tiques um chip de 3 GHz já deu desde o play
        self.ptit(tela, "UM PROCESSADOR DE 3 GHZ")
        self.ptxt(tela, "TIQUES DESDE O PLAY", 22, ACO3)
        self.ptxt(tela, dec(max(0.0, tg) * 3.0, 1), 34, AMARELO, 26)
        self.ptxt(tela, "BILHÕES", 62, BRANCO, 17)
        if not VERTICAL:
            # o relógio de verdade borrado: rápido demais para ver
            for x in range(160):
                v = (int((x + tg * 400) * 1.7) % 4) < 2
                tela.px(PX0 + x, 98 if v else 108, AMARELO if v else ACO2)
            self.ptxt(tela, "RELÓGIO DE VERDADE: UM BORRÃO", 114, ACO2)
            self.ptit(tela, "NA TELA, BEM DEVAGAR:", 136)
            self.ptxt(tela, "CADA PIXEL ACESO É UM 1", 152, AMARELO)
            self.ptxt(tela, "CADA FIO APAGADO É UM 0", 164, ACO2)

    def sons(self, fx):
        for k in range(1, len(self.bt)):
            self.nota(fx, self.bt[k], 72 + 3 * self.flip[k - 1], .06, .035, -.4 + .25 * self.flip[k - 1])


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def preparar(self):
        self.f1 = Fio([(20, 186), (280, 186)])
        self.f2 = Fio([(280, 26), (20, 26)])

    def desenhar(self, tela, t, tg):
        D.grade_fundo(tela, W)
        tela.buf[:PALCO_H, 298:] = FUNDO
        for x in range(0, W, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(8, PALCO_H, 16): tela.ret(0, y, W, 1, FUNDO2)
        f1 = Fio([(14, 186), (466, 186)]); f2 = Fio([(466, 22), (14, 22)])
        f1.desenhar(tela, lambda u: int(((t * 1.6 - u * 4) % 1) < .45), t, r=2.6)
        f2.desenhar(tela, lambda u: int(((t * 1.3 - u * 5 + .3) % 1) < .35), t, r=2.6)
        n = int(t / .045)
        for j, linha in enumerate(("COMO O PROCESSADOR", "PENSA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 19)]
            tela.texto(vis, W // 2 - larg // 2, 52 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.3:
            tela.texto("DE 0 E 1 A BILHÕES DE CONTAS", W // 2, 128, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k in range(16):
                b = (int(t * 8) + k * 5) % 3 != 0
                x = W // 2 - 88 + k * 11
                tela.ret(x, 154, 9, 11, AMARELO if b else FUNDO3)
                tela.texto('1' if b else '0', x + 2, 156, PRETO if b else ACO2, tam=9)
        porta(tela, 'E', 30, 104, 1.0, nome=False)
        porta(tela, 'NAO', 420, 104, 1.0, nome=False)


# ============================================================ 2 o bit
class Bits(Cena):
    BYTES = [0b01001101, 0b10110010, 0b11100111, 0b00011000, 0b10101010]
    NUMS = [5, 12, 42, 100]

    def preparar(self):
        self.fio = Fio([(50, 172), (290, 172)])
        self.fios8 = [Fio([(14 + j * 34 + 14, 76), (14 + j * 34 + 14, 150)]) for j in range(8)]

    def b(self, t):
        return (self.nb(t) + 1) % 2 if t >= 0 else 0

    def byte(self, t):
        if t < 21.8:
            k = max(0, (self.nb(t) - self.nb(14.4)) // 2)
            return self.BYTES[k % len(self.BYTES)]
        k = int(clamp((t - 21.8) / 2.0, 0, 3.999))
        return self.NUMS[k]

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 14.2:
            u = suave((t - 7.0) / .8)
            sz = lerp(60, 36, u)
            x = lerp(118, 14, u); y = lerp(36, 30, u)
            v = self.b(t)
            pul = math.exp(-self.desde_batida(t) / .15)
            celula(tela, x, y, sz, sz, v, tam=26 if sz > 50 else 17, pulso=pul)
            if t < 7.2:
                centro_preso(tela, "1 = LIGADO" if v else "0 = DESLIGADO", 148, 108, AMARELO if v else ACO3, tam=17)
                centro_preso(tela, "UM BIT", 148, 18, ACO3)
                bit_luz(tela, 148 + 70 * math.cos(t * 2.0), 150 + 20 * math.sin(t * 4.0), 1, 3)
            if t >= 7.0:
                # a tensão no tempo: o mesmo bit, desenhado como gráfico
                gx, gy, gw, gh = 70, 26, 220, 70
                painel(tela, gx - 4, gy - 4, gw + 8, gh + 8)
                yA, yB = gy + 10, gy + gh - 10
                for c in range(gw):
                    tt = t - (gw - 1 - c) / gw * 4.0
                    vv = self.b(tt) if tt >= 0 else 0
                    tela.px(gx + c, yA if vv else yB, AMARELO if vv else ACO2)
                    tt2 = t - (gw - c) / gw * 4.0
                    v2 = self.b(tt2) if tt2 >= 0 else 0
                    if v2 != vv: tela.ret(gx + c, yA, 1, yB - yA, ACO3)
                tela.texto("ALTA = 1", gx + 2, yA + 3, AMARELO, tam=9, contorno=PRETO)
                tela.texto("BAIXA = 0", gx + 2, yB - 10, ACO3, tam=9, contorno=PRETO)
                tela.texto("TEMPO", gx + gw - 30, gy + gh + 6, ACO2, tam=9, contorno=PRETO)
                tela.texto("TENSÃO", gx, gy + gh + 6, ACO2, tam=9, contorno=PRETO)
                seta(tela, 52, 48, 64, 48, ACO3, esp=1, ponta=3)
                # o fio levando a sequência de bits
                fr = self.fio.desenhar(tela, lambda uu: self.b(t - uu * 2.4) if t - uu * 2.4 >= 0 else 0, t, r=2.8)
                tela.texto("NUM FIO, OS BITS VIAJAM COMO TENSÃO", 50, 182, ACO3, tam=9, contorno=PRETO)
                Fio([(32, 66), (32, 172), (50, 172)]).desenhar(tela, lambda uu: self.b(t), t, herois=False)
        else:
            val = self.byte(t)
            y0 = 40
            if t < 21.8:
                centro_preso(tela, "8 BITS = 1 BYTE", 150, 20, BRANCO, tam=17)
            for j in range(8):
                x = 14 + j * 34
                bit = (val >> (7 - j)) & 1
                pul = math.exp(-self.desde_batida(t) / .2) if bit else 0
                celula(tela, x, y0, 28, 28, bit, tam=17, pulso=pul)
                if t >= 21.8:
                    pv = 1 << (7 - j)
                    centro_preso(tela, str(pv), x + 14, y0 + 34, AMARELO if bit else ACO1, xmin=0, xmax=298)
            if t < 21.8:
                for j, f in enumerate(self.fios8):
                    def vf(uu, j=j):
                        tt = t - uu * 1.2
                        return (self.byte(tt) >> (7 - j)) & 1 if tt >= 14.4 else 0
                    f.desenhar(tela, vf, t, r=2.2)
                tela.texto("8 FIOS, 8 BITS AO MESMO TEMPO", 64, 160, ACO3, tam=9, contorno=PRETO)
            else:
                tela.ret(14, y0 + 46, 270, 1, FUNDO3)
                partes = [str(1 << (7 - j)) for j in range(8) if (val >> (7 - j)) & 1]
                centro_preso(tela, " + ".join(partes) + f" = {val}", 150, 110, BRANCO, tam=17, xmin=4, xmax=296)
                centro_preso(tela, "CADA CASA VALE O DOBRO DA DA DIREITA", 150, 146, ACO3)
                for j in range(7):
                    xa = 14 + (j + 1) * 34 + 6; xb = 14 + j * 34 + 22
                    yy = 168 + 4 * math.sin(t * 3 + j)
                    seta(tela, xa, yy, xb, yy, ACO1, esp=1, ponta=3)
                    tela.texto("X2", (xa + xb) // 2 - 5, yy + 6, ACO2, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "O BIT" if t < 14.2 else "O BYTE")
        if t < 14.2:
            v = self.b(t)
            self.ptxt(tela, str(v), 22, AMARELO if v else ACO3, 26)
            self.ptxt(tela, "TENSÃO ALTA" if v else "TENSÃO BAIXA", 54, AMARELO if v else ACO3)
            self.ptxt(tela, "SÓ DOIS VALORES:", 80, ACO3)
            self.ptxt(tela, "0 OU 1", 92, BRANCO, 17)
            self.ptxt(tela, "TROCA A CADA BATIDA", 120, ACO2)
            self.ptxt(tela, f"BATIDA Nº {self.nb(t)}", 132, ACO2)
        else:
            val = self.byte(t)
            self.ptxt(tela, binario(val >> 4) + " " + binario(val), 22, AMARELO, 17)
            self.ptxt(tela, "EM DECIMAL", 50, ACO3)
            self.ptxt(tela, str(val), 62, BRANCO, 26)
            self.ptxt(tela, "8 BITS: 256 VALORES", 100, ACO2)
            self.ptxt(tela, "(DE 0 A 255)", 112, ACO2)

    def sons(self, fx):
        for k in range(1, len(self.bt)):
            t = self.bt[k]
            if t < 14.2:
                self.nota(fx, t, 76 if (k + 1) % 2 else 69, .07, .04)
            elif t < 21.8 and (self.nb(t) - self.nb(14.4)) % 2 == 0:
                self.nota(fx, t, 81, .05, .03)
        for k in range(4): self.nota(fx, 21.8 + 2 * k, 79 + 2 * k, .09, .05)


# ============================================================ 3 contar em binário
class Contar(Cena):
    XV = 150

    def n(self, t):
        return min(15, max(0, self.nb(t) - 1))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 13.8:
            n = self.n(t)
            tk = self.tb(n)
            ant = n - 1 if n > 0 else 0
            for j in range(4):                      # j = casa (0 = da direita)
                x = 66 + (3 - j) * 42
                atraso = .12 * j
                bit = ((n if t - tk >= atraso else ant) >> j) & 1
                pul = math.exp(-max(0, t - tk - atraso) / .18) if ((n >> j) & 1) != ((ant >> j) & 1) and n > 0 else 0
                celula(tela, x, 40, 34, 34, bit, tam=17, pulso=pul)
                centro_preso(tela, str(1 << j), x + 17, 80, AMARELO if bit else ACO1, xmin=0, xmax=298)
            # o "vai 1": a casa que estoura manda um bit para a esquerda
            if n > 0:
                for j in range(3):
                    if (ant >> j) & 1 and not (n >> j) & 1:
                        u = (t - tk - .12 * j) / .12
                        if 0 <= u <= 1:
                            xa = 66 + (3 - j) * 42 + 17; xb = xa - 42
                            bit_luz(tela, lerp(xa, xb, u), 34 - 14 * math.sin(math.pi * u), 1, 3)
                            if u > .2: centro_preso(tela, "VAI 1", lerp(xa, xb, u), 14, AMARELO)
            centro_preso(tela, f"= {n}", 150, 104, BRANCO, tam=26)
            # régua das contas já feitas
            for k in range(n + 1):
                x = 70 + k * 10
                tela.ret(x, 150, 7, 7, AMARELO if k == n else ACO1)
            centro_preso(tela, "UMA CONTA POR BATIDA", 150, 164, ACO2)
            self.vtxt(tela, f"{binario(n)} = {n}", AMARELO, y=6, tam=17)
        else:
            u = suave((t - 13.8) / .6)
            for r, (val, nome) in enumerate(((5, "5 ="), (3, "3 ="))):
                y = 30 + r * 52
                for j in range(4):
                    x = 102 + (3 - j) * 34
                    bit = (val >> j) & 1
                    pul = math.exp(-self.desde_batida(t) / .2) if bit else 0
                    celula(tela, x, y, 28, 28, bit, tam=17, pulso=pul)
                tela.texto(nome, 64, y + 7, BRANCO, tam=17, contorno=PRETO)
            if t >= 18.8:
                k = suave((t - 18.8) / .8)
                xm = 150
                chave_mos(tela, xm, 160, 'n', int(t * 1.5) % 2 == 0, s=1.4, val_porta=int(t * 1.5) % 2 == 0)
                centro_preso(tela, "?", xm + 26, 150, AMARELO, tam=17)
            self.vtxt(tela, "0101 E 0011", AMARELO, y=6, tam=17)
        # painel
        self.ptit(tela, "CONTANDO EM BINÁRIO")
        if not VERTICAL:
            n = self.n(t) if t < 13.8 else 15
            ini = max(0, n - 9)
            for k in range(ini, n + 1):
                y = 22 + (k - ini) * 12
                cor = AMARELO if k == n and t < 13.8 else ACO3
                tela.texto(f"{k:>2}", PX0, y, ACO1, tam=9, contorno=PRETO)
                tela.texto(binario(k), PX0 + 24, y, cor, tam=9, contorno=PRETO)
            self.ptxt(tela, "QUANDO ENCHE, VAI 1", 150, ACO2)
            self.ptxt(tela, "PARA A CASA DA ESQUERDA", 161, ACO2)

    def sons(self, fx):
        for k in range(1, 16):
            if k < len(self.bt): self.nota(fx, self.bt[k], 60 + k, .07, .045)


# ============================================================ 4 o transistor
class Transistor(Cena):
    XV = 150

    def vg_alvo(self, t):
        if t < 7.6:
            return 1 if (self.nb(t) // 4) % 2 == 1 else 0
        if t < 22.4: return 0
        if t < 29.8: return 1
        return 1 if (self.nb(t) // 2) % 2 == 0 else 0

    def vg(self, t): return media_degrau(self.vg_alvo, t, .3)

    def preparar(self):
        self.Mn = Mosfet(50, 88, 1.0)
        self.Mv = Mosfet(75, 98, .75)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        M = self.Mv if VERTICAL else self.Mn
        vg = self.vg(t)
        on = vg > .6
        tc = M.topo_contatos()
        xl, xr = M.x - 14, M.x + M.w + 14
        yb = M.y + M.h + 14
        ytop = M.y - 30 * M.s
        # o laço: fonte -> pilha -> lâmpada -> dreno
        laco = Fio([tc['fonte'], (tc['fonte'][0], ytop), (xl, ytop), (xl, yb), (xr, yb), (xr, ytop),
                    (tc['dreno'][0], ytop), tc['dreno']])
        laco.desenhar(tela, lambda u: 1 if on else 0, t, herois=False, fluxo=on)
        if on:
            for k in range(14):
                u = ((k / 14) - t * .12) % 1
                x, y = laco.ponto(u)
                tela.ret(x, y, 2, 2, CIANO)
        # pilha (esquerda) e lâmpada (direita)
        ym = (ytop + yb) / 2
        tela.ret(xl - 7, ym - 7, 16, 14, FUNDO)
        tela.ret(xl - 7, ym - 4, 16, 2, ACO4); tela.ret(xl - 4, ym + 2, 10, 2, ACO3)
        tela.texto("+", xl + 7, ym - 13, VERMELHO, tam=9, contorno=PRETO)
        tela.disco(xr + 1, ym, 8, PRETO)
        tela.disco(xr + 1, ym, 6.5, AMARELO if on else FUNDO3)
        if on:
            tela.disco(xr + 1, ym, 3.5, CHAMA0)
            for k in range(8):
                a = k * math.pi / 4 + t
                tela.px(xr + 1 + math.cos(a) * 11, ym + math.sin(a) * 11, AMARELO)
        # fio da porta
        g = tc['porta']
        fg = Fio([(g[0] - 50 * M.s, 10), (g[0], 10), g])
        fg.desenhar(tela, lambda u: 1 if self.vg_alvo(t - u * .2) else 0, t, r=2.6)
        celula(tela, g[0] - 50 * M.s - 18, 3, 14, 14, self.vg_alvo(t), tam=9)
        M.desenhar(tela, vg, t, corrente=on)
        # rótulos com fio
        R = M.regioes()
        rot = [(7.8, "FONTE", R['fonte']), (8.8, "DRENO", R['dreno']), (9.8, "PORTA", (g[0] + 6 * M.s, M.y - 18 * M.s)),
               (11.0, "ISOLANTE", M.P(142, -3)), (12.2, "SILÍCIO", R['silicio'])]
        posr = {"FONTE": (M.x + 4, M.y + 50 * M.s), "DRENO": (M.x + M.w - 34, M.y + 50 * M.s),
                "PORTA": M.P(116, -70), "ISOLANTE": M.P(150, -52),
                "SILÍCIO": (M.x + M.w / 2 - 20, M.y + M.h - 12)}
        if 7.8 <= t < 29.8:
            for a, nome, (ax, ay) in rot:
                if t >= a:
                    tx, ty = posr[nome]
                    cor = AMARELO if t < a + 1.6 else ACO3
                    if nome in ("FONTE", "DRENO", "SILÍCIO"):
                        tela.texto(nome, int(tx), int(ty), cor, tam=9, contorno=PRETO)
                    else:
                        rotulo(tela, nome, int(tx), int(ty), ax, ay, cor=cor)
        if 15.0 <= t < 22.4:
            xc, yc = R['canal']
            for k in range(3):
                xx = xc - 30 * M.s + ((t * 20 + k * 8) % 18)
                tela.px(xx, yc + 2, CIANO)
            tela.texto("X", int(xc - 3), int(yc + 6), VERMELHO, tam=17, contorno=PRETO)
            centro_preso(tela, "SEM CANAL", xc, yc + 26 * M.s, VERMELHO, xmin=M.x, xmax=M.x + M.w)
        if 22.4 <= t < 29.8 and vg > .5:
            xc, yc = R['canal']
            centro_preso(tela, "CANAL ABERTO", xc, yc + 26 * M.s, CIANO, xmin=M.x, xmax=M.x + M.w)
        if t >= 29.8:
            centro_preso(tela, "MOSFET (1959)", 150, M.y + M.h + 22 if not VERTICAL else M.y + M.h + 20, BRANCO,
                         xmin=M.x - 10, xmax=M.x + M.w + 10)
        self.vtxt(tela, "PORTA: " + ("COM TENSÃO" if self.vg_alvo(t) else "SEM TENSÃO"),
                  AMARELO if self.vg_alvo(t) else ACO3, y=26)
        # painel
        self.ptit(tela, "TENSÃO NA PORTA")
        if not VERTICAL:
            tela.ret(PX0, 22, 160, 10, PRETO); tela.ret(PX0 + 1, 23, 158 * vg, 8, AMARELO)
            self.ptxt(tela, "0", 36, ACO3); self.ptxt(tela, "1", 36, AMARELO, x=PX0 + 154)
            self.ptxt(tela, "CANAL", 56, ACO3)
            self.ptxt(tela, "ABERTO" if on else "FECHADO", 66, CIANO if on else ACO2, 17)
            self.ptxt(tela, "CORRENTE", 92, ACO3)
            self.ptxt(tela, "PASSA" if on else "NÃO PASSA", 102, AMARELO if on else VERMELHO, 17)
            # a chave equivalente
            self.ptit(tela, "É COMO UMA CHAVE:", 132)
            y = 164
            tela.ret(PX0 + 20, y, 30, 2, ACO3); tela.disco(PX0 + 50, y + 1, 2.5, ACO4)
            tela.ret(PX0 + 100, y, 40, 2, ACO3); tela.disco(PX0 + 100, y + 1, 2.5, ACO4)
            ang = lerp(-.5, 0, vg)
            x2, y2 = PX0 + 50 + 50 * math.cos(ang), y + 1 + 50 * math.sin(ang)
            linha_grossa(tela, PX0 + 50, y + 1, x2, y2, 3, AMARELO if on else ACO2)
            self.ptxt(tela, "LIGADA" if on else "DESLIGADA", 176, AMARELO if on else ACO2)

    def sons(self, fx):
        ant = 0
        for i in range(int(self.dur * 30)):
            t = i / 30
            v = self.vg_alvo(t)
            if v != ant: self.nota(fx, t, 79 if v else 67, .09, .05)
            ant = v


# ============================================================ 5 portas lógicas
def trilho(tela, x0, x1, y, v, txt):
    tela.ret(x0 - 1, y - 2, x1 - x0 + 2, 5, PRETO)
    tela.ret(x0, y - 1, x1 - x0, 3, AMARELO if v else FIO0)
    if v: tela.ret(x0, y - 1, x1 - x0, 1, CHAMA0)
    tela.texto(txt, x1 + 4, y - 3, AMARELO if v else ACO3, tam=9, contorno=PRETO)


def inversor(tela, cx, vp, vo, t, yt=22, yb=186, yp=64, yn=144, yo=104, rot=True):
    """CMOS NÃO: transistor P em cima (liga com 0), N embaixo (liga com 1)."""
    trilho(tela, cx - 30, cx + 30, yt, 1, "1 (+)")
    trilho(tela, cx - 30, cx + 30, yb, 0, "0 (TERRA)")
    p_on, n_on = vp == 0, vp == 1
    Fio([(cx, yt + 2), (cx, yp - 12)]).desenhar(tela, lambda u: 1, t, herois=False)
    Fio([(cx, yp + 12), (cx, yo)]).desenhar(tela, lambda u: vo if p_on else vo, t, herois=False)
    Fio([(cx, yo), (cx, yn - 12)]).desenhar(tela, lambda u: vo, t, herois=False)
    Fio([(cx, yn + 12), (cx, yb - 2)]).desenhar(tela, lambda u: 0, t, herois=False)
    gp = chave_mos(tela, cx, yp, 'p', p_on, val_porta=vp)
    gn = chave_mos(tela, cx, yn, 'n', n_on, val_porta=vp)
    if rot:
        tela.texto("P: LIGA COM 0", cx + 10, yp - 4, AMARELO if p_on else ACO2, tam=9, contorno=PRETO)
        tela.texto("N: LIGA COM 1", cx + 10, yn - 4, AMARELO if n_on else ACO2, tam=9, contorno=PRETO)
    return gp, gn, (cx, yo)


class Portas(Cena):
    VEL = 150.0
    VEL2 = 300.0

    def preparar(self):
        # porta NÃO em transistores
        self.cx = 170
        self.fp = Fio([(34, 104), (110, 104), (110, 64), (158, 64)])
        self.fn = Fio([(34, 104), (110, 104), (110, 144), (163, 144)])
        self.fo = Fio([(170, 104), (250, 104)])
        C = Circuito()
        C.entrada('in', lambda t: (max(0, self.nb(t) - 1) // 2) % 2)
        self.d_in = self.fp.L / self.VEL
        C.porta('out', 'NAO', [('in', self.d_in)], .15)
        self.Cn = C
        # E e OU
        self.g = {}
        for nome, t0 in (('E', 16.0), ('OU', 32.0)):
            pts, ent, out = porta_forma(nome, 120, 104, 2.2)
            fa = fio_reto((36, 74), ent[0], 80); fb = fio_reto((36, 134), ent[1], 80)
            fo = Fio([out, (248, 104)])
            C2 = Circuito()
            C2.entrada('a', (lambda t0: lambda t: self.combo(t, t0)[0])(t0))
            C2.entrada('b', (lambda t0: lambda t: self.combo(t, t0)[1])(t0))
            C2.porta('s', nome, [('a', fa.L / self.VEL2), ('b', fb.L / self.VEL2)], .15)
            lat = max(fa.L, fb.L) / self.VEL2 + .15 + fo.L / self.VEL2
            self.g[nome] = dict(t0=t0, fa=fa, fb=fb, fo=fo, C=C2, ent=ent, out=out, lat=lat)

    def combo(self, t, t0):
        if t < t0: return (0, 0)
        k = max(0, (self.nb(t) - self.nb(t0 - 1e-3)) // 2)
        k = k % 4
        return ((k >> 1) & 1, k & 1)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 16.0:
            C = self.Cn
            vp = C.val('in', t - self.d_in)
            vo = C.val('out', t)
            fr = self.fp.desenhar(tela, C.no_fio('in', self.fp.L / self.VEL, t), t, herois=False)
            fr += self.fn.desenhar(tela, C.no_fio('in', self.fn.L / self.VEL, t), t, herois=False)
            fr += self.fo.desenhar(tela, C.no_fio('out', self.fo.L / self.VEL, t), t, herois=False)
            inversor(tela, self.cx, vp, vo, t)
            for x, y in fr: bit_luz(tela, x, y, 1, 2.6)
            celula(tela, 16, 96, 18, 18, C.val('in', t), tam=9)
            celula(tela, 250, 95, 20, 20, C.val('out', t - self.fo.L / self.VEL), tam=9)
            tela.texto("ENTRADA", 8, 84, ACO3, tam=9, contorno=PRETO)
            tela.texto("SAÍDA", 248, 84, ACO3, tam=9, contorno=PRETO)
            # o caminho ligado
            if vp == 0:
                tela.texto("SAÍDA LIGADA AO 1", 176, 118, AMARELO, tam=9, contorno=PRETO)
            else:
                tela.texto("SAÍDA LIGADA AO 0", 176, 118, CIANO, tam=9, contorno=PRETO)
            nome = 'NAO'
            linhas = [[0, 1], [1, 0]]
            atual = C.val('in', t - self.d_in - .15)
            vistos = {0, 1} if t > 4 else {atual}
        else:
            nome = 'E' if t < 32.0 else 'OU'
            G = self.g[nome]
            C = G['C']
            fr = G['fa'].desenhar(tela, C.no_fio('a', G['fa'].L / self.VEL2, t), t, herois=False)
            fr += G['fb'].desenhar(tela, C.no_fio('b', G['fb'].L / self.VEL2, t), t, herois=False)
            fr += G['fo'].desenhar(tela, C.no_fio('s', G['fo'].L / self.VEL2, t), t, herois=False)
            vs = C.val('s', t)
            porta(tela, nome, 120, 104, 2.2, saida=vs, destaque=vs == 1)
            for x, y in fr: bit_luz(tela, x, y, 1, 2.8)
            celula(tela, 16, 66, 18, 18, C.val('a', t), tam=9)
            celula(tela, 16, 126, 18, 18, C.val('b', t), tam=9)
            so = C.val('s', t - G['fo'].L / self.VEL2)
            celula(tela, 248, 92, 26, 26, so, tam=17, pulso=0)
            tela.texto("A", 6, 70, BRANCO, tam=9, contorno=PRETO)
            tela.texto("B", 6, 130, BRANCO, tam=9, contorno=PRETO)
            tela.texto("SAÍDA", 246, 80, ACO3, tam=9, contorno=PRETO)
            tela.texto("PORTA " + ("E (AND)" if nome == 'E' else "OU (OR)"), 96, 18, BRANCO, tam=17, contorno=PRETO)
            f = D.FUNCOES[nome]
            linhas = [[a, b, f([a, b])] for a in (0, 1) for b in (0, 1)]
            ta = t - G['lat']
            a_, b_ = self.combo(ta, G['t0'])
            atual = a_ * 2 + b_ if ta >= G['t0'] else -1
            vistos = set()
            for j in range(5):
                tj = ta - j * 1.5
                if tj >= G['t0']:
                    a2, b2 = self.combo(tj, G['t0']); vistos.add(a2 * 2 + b2)
        # painel: a tabela-verdade (calculada pela função da porta)
        self.ptit(tela, "TABELA-VERDADE")
        if not VERTICAL:
            if nome == 'NAO':
                porta(tela, 'NAO', PX0 + 60, 36, 1.2, saida=vo)
                tela.texto("=", PX0 + 30, 32, BRANCO, tam=17, contorno=PRETO)
                tabela(tela, PX0 + 40, 64, ["ENTRA", "SAI"], linhas, atual=atual, vistos=vistos, larg=[40, 40])
                self.ptxt(tela, "2 TRANSISTORES:", 120, ACO3)
                self.ptxt(tela, "UM P E UM N", 131, ACO3)
                self.ptxt(tela, "SEMPRE UM LIGADO E", 150, ACO2)
                self.ptxt(tela, "O OUTRO DESLIGADO", 161, ACO2)
            else:
                tabela(tela, PX0 + 20, 24, ["A", "B", "SAÍDA"], linhas, atual=atual, vistos=vistos, larg=[30, 30, 50])
                self.ptxt(tela, "SÓ 1 + 1 DÁ 1" if nome == 'E' else "SÓ 0 + 0 DÁ 0", 100, AMARELO)
                self.ptxt(tela, "PORTA LÓGICA:", 130, ACO3)
                self.ptxt(tela, "ENTRAM BITS, SAI UM BIT", 141, ACO3)
                self.ptxt(tela, "POR DENTRO: TRANSISTORES", 160, ACO2)

    def sons(self, fx):
        ant = None
        for i in range(int(self.dur * 30)):
            t = i / 30
            if t < 16:
                v = self.Cn.val('out', t - self.fo.L / self.VEL)
            else:
                G = self.g['E' if t < 32 else 'OU']
                v = G['C'].val('s', t - G['fo'].L / self.VEL2)
            if ant is not None and v != ant: self.nota(fx, t, 81 if v else 69, .07, .045)
            ant = v


# ============================================================ 6 somador de 1 bit
class Somador(Cena):
    VEL = 140.0
    S = 1.2

    def entradas(self, t):
        if t < 1.0: return (0, 0, 0)
        if t >= 29.8: return (1, 1, 0)
        k = min(7, int((t - 1.0) / 3.6))
        return ((k >> 2) & 1, (k >> 1) & 1, k & 1)

    def preparar(self):
        s = self.S
        self.G = dict(x1=('XOR', 86, 49), a1=('E', 86, 110), x2=('XOR', 172, 63), a2=('E', 172, 142), o=('OU', 226, 124))
        P = {k: porta_forma(tp, x, y, s) for k, (tp, x, y) in self.G.items()}
        self.P = P
        A, B, V = (24, 37), (24, 61), (24, 173)
        F = {}
        F['a_x1'] = fio_reto(A, P['x1'][1][0], 60); F['a_a1'] = fio_reto(A, P['a1'][1][0], 50)
        F['b_x1'] = fio_reto(B, P['x1'][1][1], 70); F['b_a1'] = fio_reto(B, P['a1'][1][1], 62)
        F['x1_x2'] = fio_reto(P['x1'][2], P['x2'][1][0], 152); F['x1_a2'] = fio_reto(P['x1'][2], P['a2'][1][0], 144)
        F['v_x2'] = fio_reto(V, P['x2'][1][1], 134); F['v_a2'] = fio_reto(V, P['a2'][1][1], 160)
        F['a1_o'] = fio_reto(P['a1'][2], P['o'][1][0], 220); F['a2_o'] = fio_reto(P['a2'][2], P['o'][1][1], 216)
        F['s'] = Fio([P['x2'][2], (266, 63)]); F['vai'] = Fio([P['o'][2], (266, 124)])
        self.F = F
        dw = lambda n: F[n].L / self.VEL
        C = Circuito()
        C.entrada('A', lambda t: self.entradas(t)[0]); C.entrada('B', lambda t: self.entradas(t)[1])
        C.entrada('V', lambda t: self.entradas(t)[2])
        dg = .15
        C.porta('x1', 'XOR', [('A', dw('a_x1')), ('B', dw('b_x1'))], dg)
        C.porta('a1', 'E', [('A', dw('a_a1')), ('B', dw('b_a1'))], dg)
        C.porta('x2', 'XOR', [('x1', dw('x1_x2')), ('V', dw('v_x2'))], dg)
        C.porta('a2', 'E', [('x1', dw('x1_a2')), ('V', dw('v_a2'))], dg)
        C.porta('o', 'OU', [('a1', dw('a1_o')), ('a2', dw('a2_o'))], dg)
        self.C = C
        self.src = dict(a_x1='A', a_a1='A', b_x1='B', b_a1='B', x1_x2='x1', x1_a2='x1', v_x2='V', v_a2='V',
                        a1_o='a1', a2_o='a2', s='x2', vai='o')

    def saidas(self, t):
        return (self.C.val('x2', t - self.F['s'].L / self.VEL), self.C.val('o', t - self.F['vai'].L / self.VEL))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        C = self.C
        fr = []
        for n, f in self.F.items():
            fr += f.desenhar(tela, C.no_fio(self.src[n], f.L / self.VEL, t), t, herois=False)
        for k, (tp, x, y) in self.G.items():
            v = C.val(k, t)
            porta(tela, tp, x, y, self.S, saida=v, destaque=(k == 'x1' or k == 'x2') and 22.6 <= t < 29.6)
        for x, y in fr: bit_luz(tela, x, y, 1, 2.4)
        a, b, v = self.entradas(t)
        for (x, y), val, nome in (((8, 29), a, "A"), ((8, 53), b, "B"), ((8, 165), v, "VEM 1")):
            celula(tela, x, y, 16, 16, val, tam=9)
        tela.texto("A", 8, 19, BRANCO, tam=9, contorno=PRETO)
        tela.texto("B", 28, 53, BRANCO, tam=9, contorno=PRETO)
        tela.texto("VEM 1", 8, 155, BRANCO, tam=9, contorno=PRETO)
        s, vai = self.saidas(t)
        celula(tela, 266, 55, 18, 18, s, tam=9)
        celula(tela, 266, 116, 18, 18, vai, tam=9)
        tela.texto("SOMA", 260, 44, AMARELO, tam=9, contorno=PRETO)
        tela.texto("VAI 1", 258, 105, AMARELO, tam=9, contorno=PRETO)
        if t >= 30.0:
            centro_preso(tela, "1 + 1 = 10", 200, 186, BRANCO, tam=17, xmin=170, xmax=296)
        # painel: a tabela das 8 combinações, calculada pelas mesmas funções
        self.ptit(tela, "SOMADOR DE 1 BIT")
        if not VERTICAL:
            linhas = []
            for k in range(8):
                aa, bb, vv = (k >> 2) & 1, (k >> 1) & 1, k & 1
                linhas.append([aa, bb, vv, D.FUNCOES['SOMA']([aa, bb, vv]), D.FUNCOES['VAI']([aa, bb, vv])])
            ts = t - 2.0
            if ts >= 1.0 and ts < 29.8:
                atual = min(7, int((ts - 1.0) / 3.6)); vistos = set(range(atual + 1))
            elif ts >= 29.8:
                atual, vistos = 6, set(range(8))
            else:
                atual, vistos = -1, set()
            tabela(tela, PX0 + 4, 20, ["A", "B", "VEM", "SOMA", "VAI"], linhas, atual=atual, vistos=vistos,
                   larg=[24, 24, 30, 38, 34], alto=11, n_out=2)
            tela.ret(PX0 + 82, 30, 1, 100, FUNDO3)
            self.ptxt(tela, f"{a} + {b} + {v} = {a + b + v}", 136, BRANCO, 17)
            self.ptxt(tela, f"EM BINÁRIO: {vai}{s}", 158, AMARELO)
            ok = (vai * 2 + s) == a + b + v
            self.ptxt(tela, "(VAI 1, SOMA)" if ok else "(CALCULANDO...)", 170, ACO2 if ok else LARANJA)

    def sons(self, fx):
        ant = None
        for i in range(int(self.dur * 30)):
            t = i / 30
            s = self.saidas(t)
            if ant is not None:
                if s[0] != ant[0]: self.nota(fx, t, 79 if s[0] else 72, .06, .04, .3)
                if s[1] != ant[1]: self.nota(fx, t, 84 if s[1] else 74, .06, .04, .5)
            ant = s


# ============================================================ 7 somar 4 bits
class Soma4(Cena):
    XV = 133
    PARES = [(30.0, 6, 7), (33.0, 9, 4), (36.0, 2, 11), (39.0, 7, 7)]

    def num(self, t):
        if t < 4.0: return (0, 0)
        a, b = 5, 3
        for t0, x, y in self.PARES:
            if t >= t0: a, b = x, y
        return (a, b)

    def lento(self, t): return t < 29.5
    def dwA(self, t): return 1.0 if self.lento(t) else .2
    def dg(self, t): return 1.0 if self.lento(t) else .15
    def dwC(self, t): return 2.4 if self.lento(t) else .35
    def dwS(self, t): return .6 if self.lento(t) else .15

    def bx(self, i): return 188 - 42 * i

    def preparar(self):
        C = Circuito()
        C.entrada('Z', lambda t: 0)
        for i in range(4):
            C.entrada(f'A{i}', (lambda i: lambda t: (self.num(t)[0] >> i) & 1)(i))
            C.entrada(f'B{i}', (lambda i: lambda t: (self.num(t)[1] >> i) & 1)(i))
        for i in range(4):
            vin = ('Z', 0) if i == 0 else (f'K{i - 1}', self.dwC)
            ins = [(f'A{i}', self.dwA), (f'B{i}', self.dwA), vin]
            C.porta(f'S{i}', 'SOMA', ins, self.dg)
            C.porta(f'K{i}', 'VAI', ins, self.dg)
        self.C = C
        self.fa, self.fb, self.fs, self.fk = [], [], [], []
        for i in range(4):
            x = self.bx(i)
            self.fa.append(Fio([(x + 8, 43), (x + 8, 84)]))
            self.fb.append(Fio([(x + 25, 43), (x + 25, 84)]))
            self.fs.append(Fio([(x + 17, 118), (x + 17, 150)]))
            if i < 3:
                self.fk.append(Fio([(x + 4, 118), (x + 4, 130), (x - 4, 130), (x - 4, 112), (x - 8, 112)]))
            else:
                self.fk.append(Fio([(x + 4, 118), (x + 4, 132), (50, 132), (50, 121)]))

    def resultado(self, t):
        bits = [self.C.val(f'S{i}', t - self.dwS(t)) for i in range(4)]
        k = self.C.val('K3', t - self.dwC(t))
        return bits, k

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        C = self.C
        a, b = self.num(t)
        fr = []
        for i in range(4):
            fr += self.fa[i].desenhar(tela, C.no_fio(f'A{i}', self.dwA, t), t, herois=False)
            fr += self.fb[i].desenhar(tela, C.no_fio(f'B{i}', self.dwA, t), t, herois=False)
            fr += self.fs[i].desenhar(tela, C.no_fio(f'S{i}', self.dwS, t), t, herois=False)
            fr += self.fk[i].desenhar(tela, C.no_fio(f'K{i}', self.dwC, t), t, herois=False)
        for i in range(4):
            x = self.bx(i)
            # o somador acende enquanto as entradas dele estão mudando
            ativo = any(C.val(n, t - self.dg(t) * .0) != C.val(n, t - self.dg(t)) for n in (f'S{i}', f'K{i}'))
            ent_mudou = False
            for dt in (0.0, self.dg(t) * .5):
                vv = [C.val(f'A{i}', t - self.dwA(t) - dt), C.val(f'B{i}', t - self.dwA(t) - dt),
                      C.val(f'K{i - 1}', t - self.dwC(t) - dt) if i else 0]
                ww = [C.val(f'A{i}', t - self.dwA(t) - self.dg(t)), C.val(f'B{i}', t - self.dwA(t) - self.dg(t)),
                      C.val(f'K{i - 1}', t - self.dwC(t) - self.dg(t)) if i else 0]
                ent_mudou |= vv != ww
            bloco(tela, x, 84, x + 34, 118, POR2 if ent_mudou else POR1, ACO4, POR0)
            tela.texto("+", x + 17, 92, AMARELO if ent_mudou else ACO3, tam=17, centro=True, contorno=PRETO)
            # entradas e resultado
            celula(tela, x + 2, 30, 13, 13, (a >> i) & 1, tam=9)
            celula(tela, x + 19, 30, 13, 13, (b >> i) & 1, tam=9)
            tela.texto("A", x + 6, 20, ACO2, tam=9, contorno=PRETO)
            tela.texto("B", x + 23, 20, ACO2, tam=9, contorno=PRETO)
        bits, k = self.resultado(t)
        for i in range(4):
            x = self.bx(i)
            celula(tela, x + 9, 150, 16, 16, bits[i], tam=9)
        celula(tela, 43, 107, 14, 14, k, tam=9)
        tela.texto("VAI", 41, 97, ACO2, tam=9, contorno=PRETO)
        for x, y in fr: bit_luz(tela, x, y, 1, 2.6)
        r = sum(bv << i for i, bv in enumerate(bits)) + (k << 4)
        ok = r == a + b and t >= 4.0
        cor = VERDE if ok else LARANJA
        centro_preso(tela, f"= {r}" + ("" if ok else " ?"), 133, 176, cor if t >= 4.0 else ACO2, tam=17, xmin=44, xmax=222)
        for i in range(4):
            centro_preso(tela, f"CASA {i}", self.bx(i) + 17, 8, ACO2, xmin=0, xmax=298)
        self.vtxt(tela, f"{binario(a)} + {binario(b)}", AMARELO, y=192, tam=9)
        # painel
        self.ptit(tela, "SOMANDO 4 BITS")
        self.ptxt(tela, f"A = {binario(a)}  ({a})", 22, BRANCO)
        self.ptxt(tela, f"B = {binario(b)}  ({b})", 34, BRANCO)
        tela.ret(PX0, 46, 120, 1, ACO2) if not VERTICAL else None
        self.ptxt(tela, (str(k) if k else " ") + binario(r, 4) + f"  ({r})", 52, cor, 17)
        if ok:
            self.ptxt(tela, f"CERTO: {a} + {b} = {a + b}", 78, VERDE)
        elif t >= 4.0:
            self.ptxt(tela, "ESPERANDO O VAI-UM...", 78, LARANJA)
        if not VERTICAL and t >= 4.0:
            self.ptit(tela, "O VAI-UM DE CADA CASA", 100)
            for i in range(4):
                kv = C.val(f'K{i}', t)
                self.ptxt(tela, f"CASA {i}: VAI {kv}", 116 + i * 12, AMARELO if kv else ACO2)
            self.ptxt(tela, "CÂMERA LENTA" if self.lento(t) else "MAIS RÁPIDO", 172, ACO2)

    def sons(self, fx):
        ant = None
        for i in range(int(self.dur * 30)):
            t = i / 30
            bits, k = self.resultado(t)
            if ant is not None:
                for j in range(4):
                    if bits[j] != ant[0][j]: self.nota(fx, t, 72 + j * 3 + (4 if bits[j] else 0), .06, .035, -.4 + j * .25)
            ant = (bits, k)


# ============================================================ 8 o relógio
class Relogio(Cena):
    XV = 130

    def clk(self, t):
        if t < 0: return 0
        return 1 if self.desde_batida(t) < .25 else 0

    def valor(self, t): return max(0, self.nb(t) - 1)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        n = self.valor(t)
        # o relógio
        bloco(tela, 44, 24, 92, 58, ACO1, ACO3, ACO0)
        bloco(tela, 54, 34, 82, 48, LATAO, CHAMA1, D.COB0)
        tela.texto("RELÓGIO", 46, 12, BRANCO, tam=9, contorno=PRETO)
        on = self.clk(t)
        tela.disco(86, 30, 2.5, PRETO); tela.disco(86, 30, 1.8, VERDE if on else D.PCB0)
        # fio do relógio até o registrador
        fc = Fio([(92, 41), (168, 41), (168, 112)])
        fc.desenhar(tela, lambda u: self.clk(t - u * .12), t, r=2.6)
        tela.texto("TIQUE", 100, 30, ACO3, tam=9, contorno=PRETO)
        # registrador de 6 bits
        x0 = 118
        for j in range(6):
            bit = (n >> (5 - j)) & 1
            pul = math.exp(-self.desde_batida(t) / .15)
            celula(tela, x0 + j * 17, 114, 15, 18, bit, tam=9, pulso=pul if bit else 0)
        tela.texto("REGISTRADOR", 172, 102, ACO3, tam=9, contorno=PRETO)
        # +1: o somador que conta
        bloco(tela, 44, 112, 72, 134, D.POR1, ACO4, D.POR0)
        tela.texto("+1", 58, 118, AMARELO, tam=9, centro=True, contorno=PRETO)
        volta = Fio([(168, 133), (168, 148), (58, 148), (58, 135)])
        volta.desenhar(tela, lambda u: 1 if n else 0, t, herois=False, fluxo=False)
        ida = Fio([(73, 123), (116, 123)])
        ida.desenhar(tela, lambda u: 1, t, herois=False, fluxo=False)
        # o número viajando: sai do registrador, passa no +1 e espera o tique
        u = clamp(self.desde_batida(t) / .45)
        x, y = volta.ponto(u) if u < 1 else (95, 123)
        lbl = binario(n, 6) if u < 1 else binario(n + 1, 6)
        w = tela.largura_texto(lbl, 9) + 6
        painel(tela, x - w / 2, y - 6, w, 11, borda=CIANO, fundo=PRETO)
        tela.texto(lbl, int(x - w / 2 + 3), int(y - 4), CIANO, tam=9)
        # a lâmpada do tique, grande
        if not VERTICAL:
            pul = math.exp(-self.desde_batida(t) / .12)
            tela.disco(250, 50, 20, PRETO)
            tela.disco(250, 50, 18, AMARELO if pul > .3 else FUNDO3)
            if pul > .3:
                tela.disco(250, 50, 10, CHAMA0)
                for k in range(12):
                    a = k * math.pi / 6
                    r = 22 + 6 * (1 - pul)
                    tela.ret(250 + math.cos(a) * r, 50 + math.sin(a) * r, 2, 2, AMARELO)
            centro_preso(tela, f"{self.nb(t)}", 250, 44, PRETO if pul > .3 else ACO3, tam=17, xmin=200, xmax=296)
        # a onda do relógio no tempo
        gx0, gx1 = (44, 218) if VERTICAL else (16, 290)
        gy0, gy1 = 168, 196
        gw = gx1 - gx0
        janela = 3.0
        for c in range(gw):
            tt = t - (gw - 1 - c) / gw * janela
            v = self.clk(tt)
            tela.px(gx0 + c, gy0 + 2 if v else gy1 - 2, AMARELO if v else ACO2)
            tt2 = t - (gw - c) / gw * janela
            if self.clk(tt2) != v: tela.ret(gx0 + c, gy0 + 2, 1, gy1 - gy0 - 4, ACO3 if v else ACO1)
        tela.ret(gx1, gy0 - 2, 1, gy1 - gy0 + 4, BRANCO)
        tela.texto("AGORA", gx1 - 32, gy0 - 10, BRANCO, tam=9, contorno=PRETO)
        tela.texto("SOBE, DESCE: 1 TIQUE", gx0, gy0 - 10, ACO2, tam=9, contorno=PRETO)
        self.vtxt(tela, f"TIQUE Nº {self.nb(t)}", AMARELO, y=70, tam=17)
        # painel
        self.ptit(tela, "O RELÓGIO")
        self.ptxt(tela, f"TIQUE Nº {self.nb(t)}", 20, AMARELO, 17)
        self.ptxt(tela, "AQUI: 2 TIQUES POR SEGUNDO", 42, BRANCO)
        self.ptxt(tela, "(120 BATIDAS POR MINUTO)", 53, ACO2)
        self.ptxt(tela, f"REGISTRADOR: {n}", 72, CIANO)
        if t >= 22.0:
            self.ptit(tela, "NA VIDA REAL, A 3 GHZ", 96, AMARELO)
            self.ptxt(tela, milhar(GHZ), 112, BRANCO, 17)
            self.ptxt(tela, "TIQUES POR SEGUNDO", 132, ACO3)
            self.ptxt(tela, "1 TIQUE = " + dec(1e9 / GHZ, 2) + " NANOSSEGUNDO", 146, ACO3)
            self.ptxt(tela, f"{dec(GHZ / 2 / 1e9, 1)} BILHÕES DE VEZES", 164, ACO2)
            self.ptxt(tela, "MAIS RÁPIDO QUE AQUI", 175, ACO2)
        elif t >= 15.0:
            self.ptxt(tela, "A CADA SUBIDA:", 100, ACO3)
            self.ptxt(tela, "O +1 SOMA E O REGISTRADOR", 112, ACO3)
            self.ptxt(tela, "GUARDA O NÚMERO NOVO", 123, ACO3)

    def sons(self, fx):
        for tk in self.bt:
            self.tique(fx, tk, 1900.0, .03, .05, .2)


# ============================================================ processador de brinquedo (diagrama)
LAYOUT = {
    False: dict(mem=(4, 8, 132, 194), pc=(152, 8, 58, 36), uc=(216, 8, 80, 36), ir=(152, 50, 144, 30),
                ra=(152, 88, 64, 34), rb=(232, 88, 64, 34), ula=(160, 136, 128, 56), bus=144, volta=148),
    True: dict(mem=(98, 8, 48, 194), pc=(150, 8, 36, 36), uc=(190, 8, 88, 36), ir=(150, 50, 128, 30),
               ra=(150, 88, 58, 34), rb=(220, 88, 58, 34), ula=(156, 136, 116, 56), bus=148, volta=148),
}
OPNOME = {1: 'CARREGA', 2: 'CARREGA', 3: 'SOMA', 4: 'GUARDA', 5: 'PULA'}


def texto_curto(op, arg):
    return {1: f"A=M{arg}", 2: f"B=M{arg}", 3: "A=A+B", 4: f"M{arg}=A", 5: f"VAI {arg}"}.get(op, "")


class Diagrama:
    """Desenha o processador de brinquedo (estado `st` da CPU)."""

    def __init__(self, compacto=False):
        self.c = compacto
        self.Lt = LAYOUT[compacto]

    def linha_mem(self, i):
        x, y, w, h = self.Lt['mem']
        return y + 18 + i * 15

    def ancora(self, nome, i=0):
        Lt = self.Lt
        if nome == 'mem': x, y, w, h = Lt['mem']; return (x + w, self.linha_mem(i) + 3)
        x, y, w, h = Lt[nome]
        return dict(cima=(x + w / 2, y), baixo=(x + w / 2, y + h), esq=(x, y + h / 2), dir=(x + w, y + h / 2),
                    centro=(x + w / 2, y + h / 2))

    def desenhar(self, tela, st, t, mostrar=None, ativo=(), pc_mostra=None, ir_mostra=None, a_mostra=None,
                 b_mostra=None, mem_mostra=None, uc_txt=None, ula_txt=None, linha_pc=True, ctrl=False):
        Lt = self.Lt
        mostrar = set(mostrar or ('mem', 'pc', 'uc', 'ir', 'ra', 'rb', 'ula'))
        pc = st['pc'] if pc_mostra is None else pc_mostra
        ir = st['ir'] if ir_mostra is None else ir_mostra
        av = st['a'] if a_mostra is None else a_mostra
        bv = st['b'] if b_mostra is None else b_mostra
        mem = st['mem'] if mem_mostra is None else mem_mostra
        # barramentos (atrás das caixas)
        cb = ACO0
        bus, volta = Lt['bus'], Lt['volta']
        xm, ym, wm, hm = Lt['mem']
        xi, yi, wi, hi = Lt['ir']
        xa, ya, wa, ha = Lt['ra']; xb, yb, wb, hb = Lt['rb']
        xu, yu, wu, hu = Lt['ula']
        def lin(pts, cor=cb):
            for (a1, b1), (a2, b2) in zip(pts, pts[1:]):
                linha_grossa(tela, a1, b1, a2, b2, 3, PRETO)
                linha_grossa(tela, a1, b1, a2, b2, 1, cor)
        if 'ir' in mostrar: lin([(xm + wm, ym + 30), (bus, ym + 30), (bus, yi + hi / 2), (xi, yi + hi / 2)])
        if 'ra' in mostrar:
            lin([(bus, yi + hi / 2), (bus, ya + ha / 2), (xa, ya + ha / 2)])
            lin([(xa + wa / 2, ya + ha), (xa + wa / 2, yu)]); lin([(xb + wb / 2, yb + hb), (xb + wb / 2, yu)])
            lin([(xb + wb / 2, ya - 4), (bus + 6, ya - 4)])
            lin([(xu + wu / 2, yu + hu), (xu + wu / 2, yu + hu + 6), (volta, yu + hu + 6), (volta, ya + ha - 6),
                 (xa, ya + ha - 6)])
        if 'ula' in mostrar and 'uc' in mostrar:
            xc = xu + wu / 2
            on = ctrl
            for k in range(int(yi + hi), int(yu), 3):
                tela.ret(xc, k, 1, 2, AMARELO if on else FUNDO3)
        # memória
        if 'mem' in mostrar:
            caixa(tela, xm, ym, wm, hm, "MEMÓRIA", ativo='mem' in ativo)
            for i in range(11):
                y = self.linha_mem(i)
                if i == pc and linha_pc and 'pc' in mostrar:
                    tela.ret(xm + 2, y - 2, wm - 4, 11, FUNDO3)
                if i in (5, 6, 7):
                    tela.texto("...", xm + 18, y, ACO0, tam=9) if not self.c else None
                    if self.c: tela.texto(f"{i}", xm + 3, y, ACO0, tam=9)
                    continue
                w8 = mem[i]
                tela.texto(f"{i}", xm + 3, y, ACO1, tam=9)
                if i < 5:
                    op, arg = w8 >> 4, w8 & 15
                    txt = texto_instr(op, arg) if not self.c else texto_curto(op, arg)
                    cor = CIANO
                else:
                    txt = f"= {w8}" if not self.c else f"{w8}"
                    cor = VERDE
                if not self.c:
                    tela.texto(binario(w8 >> 4) + " " + binario(w8), xm + 18, y, ACO3 if i == pc else ACO2, tam=9)
                    tela.texto(txt, xm + 78, y, cor, tam=9)
                else:
                    tela.texto(txt, xm + (14 if i < 10 else 16), y, cor, tam=9)
        else:
            tela.ret_vazado(xm, ym, wm, hm, FUNDO3)
        # PC
        x, y, w, h = Lt['pc']
        if 'pc' in mostrar:
            caixa(tela, x, y, w, h, "PC", ativo='pc' in ativo)
            tela.texto(str(pc), x + w // 2 + (6 if not self.c else 4), y + 4, AMARELO, tam=17, centro=True,
                       contorno=PRETO)
            tela.texto(binario(pc), x + w // 2, y + 25, ACO3, tam=9, centro=True)
            if linha_pc:
                ly = self.linha_mem(pc) + 3
                seta(tela, x - 1, ly, xm + wm + 1, ly, AMARELO if 'pc' in ativo else ACO2, esp=1, ponta=3)
        else:
            tela.ret_vazado(x, y, w, h, FUNDO3)
        # controle
        x, y, w, h = Lt['uc']
        if 'uc' in mostrar:
            caixa(tela, x, y, w, h, "CONTROLE", ativo='uc' in ativo)
            if uc_txt: centro_preso(tela, uc_txt, x + w / 2, y + 22, AMARELO, xmin=x + 2, xmax=x + w - 2)
        else:
            tela.ret_vazado(x, y, w, h, FUNDO3)
        # registrador de instrução
        x, y, w, h = Lt['ir']
        if 'ir' in mostrar:
            caixa(tela, x, y, w, h, "INSTRUÇÃO", ativo='ir' in ativo)
            op, arg = ir >> 4, ir & 15
            if ir:
                if not self.c:
                    tela.texto(binario(op) + " " + binario(arg), x + 4, y + 15, ACO3, tam=9)
                    tela.texto(texto_instr(op, arg), x + 64, y + 15, CIANO, tam=9)
                else:
                    tela.texto(binario(op) + binario(arg), x + 4, y + 15, ACO3, tam=9)
                    tela.texto(texto_curto(op, arg), x + 60, y + 15, CIANO, tam=9)
        else:
            tela.ret_vazado(x, y, w, h, FUNDO3)
        # registradores
        for nome, val, key in (("A", av, 'ra'), ("B", bv, 'rb')):
            x, y, w, h = Lt[key]
            if key in mostrar:
                caixa(tela, x, y, w, h, "REG. " + nome if not self.c else nome, ativo=key in ativo)
                tela.texto(binario(val >> 4) + binario(val), x + 4, y + 13, ACO3, tam=9)
                tela.texto(f"= {val}", x + 4, y + 23, BRANCO, tam=9)
            else:
                tela.ret_vazado(x, y, w, h, FUNDO3)
        # ULA (o V clássico)
        x, y, w, h = Lt['ula']
        pts = [(x, y), (x + w * .42, y), (x + w * .5, y + 10), (x + w * .58, y), (x + w, y), (x + w * .8, y + h),
               (x + w * .2, y + h)]
        if 'ula' in mostrar:
            m, mx, my = mascara_poligono(pts)
            on = 'ula' in ativo
            pintar(tela, m, mx, my, D.POR2 if on else D.POR1, ACO4, D.POR0, contorno=AMARELO if on else PRETO)
            tela.texto("ULA", int(x + w / 2), int(y + 14), BRANCO, tam=9, centro=True, contorno=PRETO)
            if ula_txt:
                for j, l in enumerate(ula_txt):
                    centro_preso(tela, l, x + w / 2, y + 25 + j * 10, AMARELO, xmin=x + w * .18, xmax=x + w * .82 + 2)
        else:
            for (a1, b1), (a2, b2) in zip(pts, pts[1:] + pts[:1]):
                tela.linha(a1, b1, a2, b2, FUNDO3)

    def pacote(self, tela, pts, u, txt, cor=AMARELO):
        """Os bits viajando de uma peça para outra (um pacote aceso)."""
        f = Fio(pts)
        x, y = f.ponto(u)
        for k in range(1, 5):
            xx, yy = f.ponto(u - k * .04)
            if u - k * .04 > 0: tela.ret(xx - 1, yy - 1, 2, 2, CHAMA1 if k < 3 else LARANJA)
        w = tela.largura_texto(txt, 9) + 6
        bit_luz(tela, x, y, 1, 4)
        painel(tela, x - w / 2, y - 14, w, 11, borda=cor, fundo=PRETO)
        tela.texto(txt, int(x - w / 2 + 3), int(y - 12), cor, tam=9)


# ============================================================ 9 as peças do processador
class Pecas(Cena):
    ORDEM = [(0.5, 'mem', "MEMÓRIA"), (7.4, 'pc', "CONTADOR (PC)"), (14.8, 'ir', "INSTRUÇÃO (IR)"),
             (14.8, 'uc', "CONTROLE"), (22.2, 'ra', "REGISTRADORES"), (22.2, 'ula', "ULA (AS CONTAS)")]

    def preparar(self):
        self.Dg = Diagrama(False)
        self.cpu = CPU()

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        mostrar = [k for a, k, _ in self.ORDEM if t >= a]
        if 'ra' in mostrar: mostrar.append('rb')
        atual = [k for a, k, _ in self.ORDEM if a <= t < a + 3.0]
        if 'ra' in atual: atual.append('rb')
        st = self.cpu.estado()
        # cada peça "trabalha" um pouco quando aparece
        pc = 0
        if t >= 7.4:
            pc = min(4, max(0, self.nb(t) - self.nb(7.4)))
        ir = st['mem'][pc] if t >= 14.8 else 0
        uc = OPNOME.get(ir >> 4) if t >= 14.8 else None
        a_ = 5 if t >= 23.5 else 0
        b_ = 3 if t >= 24.5 else 0
        ula = None
        if t >= 22.2:
            ops = ["+", "-", "E", "OU"]
            ula = [ops[(self.nb(t) // 2) % 4] if t < 25.5 else "5 + 3"]
        self.Dg.desenhar(tela, st, t, mostrar=mostrar, ativo=atual, pc_mostra=pc, ir_mostra=ir, a_mostra=a_,
                         b_mostra=b_, uc_txt=uc, ula_txt=ula, linha_pc=t >= 7.4, ctrl=t >= 18 and int(t * 2) % 2 == 0)
        if t < 7.4:
            # leitura passando pela memória
            i = int(t * 2) % 11
            if i not in (5, 6, 7):
                y = self.Dg.linha_mem(i)
                tela.ret(6, y - 2, 128, 1, CIANO); tela.ret(6, y + 8, 128, 1, CIANO)
        # painel
        self.ptit(tela, "AS PEÇAS")
        n = len([1 for a, _, _ in self.ORDEM if t >= a])
        self.ptxt(tela, f"PEÇA {n} DE 6", 20, BRANCO, 17)
        for j, (a, k, nome) in enumerate(self.ORDEM):
            y = 46 + j * 16
            if VERTICAL: continue
            ok = t >= a
            tela.ret(PX0, y + 1, 8, 8, (AMARELO if k in atual else VERDE) if ok else FUNDO2)
            if ok: tela.ret(PX0 + 2, y + 3, 4, 4, PRETO)
            tela.texto(nome, PX0 + 13, y, BRANCO if k in atual else (ACO3 if ok else ACO0), tam=9, contorno=PRETO)
        self.ptxt(tela, "UM PROCESSADOR DE VERDADE", 154, ACO2)
        self.ptxt(tela, "TEM ESSAS PEÇAS, SÓ QUE", 165, ACO2)
        self.ptxt(tela, "MUITO MAIORES", 176, ACO2)

    def sons(self, fx):
        for k, (a, _, _) in enumerate(self.ORDEM):
            if k in (3,): continue
            self.nota(fx, a, 76 + k * 2, .5, .05)


# ============================================================ 10 o ciclo
class Ciclo(Cena):
    XV = 188

    def preparar(self):
        self.DgN, self.DgC = Diagrama(False), Diagrama(True)
        # agenda das etapas, em batidas (0,5 s cada): cada etapa começa numa batida
        dur_b = [2] * 6 + [14, 12, 12] + [2] * 6 + [1] * 16 + [.5] * 16 + [.25] * 32
        ini = []
        b = 2.0
        for d in dur_b:
            ini.append(b); b += d
        self.ini = [self.tbf(x) for x in ini]
        self.fim = [self.tbf(x) for x in ini[1:]] + [self.tbf(b)]
        cpu = CPU()
        self.est = [cpu.estado()]
        for _ in dur_b: self.est.append(cpu.passo())

    def tbf(self, b):
        """Instante da batida b (fração = entre batidas)."""
        k = int(math.floor(b)); f = b - k
        return self.tb(k) + f * (self.tb(k + 1) - self.tb(k))

    def etapa(self, t):
        i = bisect.bisect_right(self.ini, t) - 1
        if i < 0: return -1, 0.0
        i = min(i, len(self.ini) - 1)
        u = clamp((t - self.ini[i]) / max(1e-6, self.fim[i] - self.ini[i]))
        return i, u

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        Dg = self.DgC if VERTICAL else self.DgN
        i, u = self.etapa(t)
        if i < 0:
            st = self.est[0]; Dg.desenhar(tela, st, t, ativo=('pc',))
            self.painel(tela, t, st, -1, 0)
            return
        a0, a1 = self.est[i], self.est[i + 1]
        e = a1['etapa']
        op, arg = a1['ir'] >> 4, a1['ir'] & 15
        kw = dict(pc_mostra=a0['pc'], ir_mostra=a0['ir'], a_mostra=a0['a'], b_mostra=a0['b'], mem_mostra=a0['mem'])
        ativo, pac, uc, ula, ctrl = [], None, None, None, False
        if e == 0:                                   # BUSCA
            ativo = ['pc', 'mem'] if u < .2 else ['mem', 'ir']
            if u >= .75: kw['ir_mostra'] = a1['ir']; ativo = ['ir']
            if u >= .85: kw['pc_mostra'] = a1['pc']; ativo = ['ir', 'pc']
            if .2 <= u < .75:
                x0, y0 = Dg.ancora('mem', a0['pc'])
                bus = Dg.Lt['bus']; xi, yi, wi, hi = Dg.Lt['ir']
                pac = ([(x0, y0), (bus, y0), (bus, yi + hi / 2), (xi, yi + hi / 2)], (u - .2) / .55,
                       binario(a1['ir'] >> 4) + binario(a1['ir']))
        elif e == 1:                                 # DECODIFICA
            ativo = ['ir', 'uc']
            xi, yi, wi, hi = Dg.Lt['ir']; xc, yc, wc, hc = Dg.Lt['uc']
            if u < .6:
                xx = xc + wc / 2
                pac = ([(xx, yi + hi / 2), (xx, yc + hc - 6)], u / .6, binario(op))
            else:
                uc = OPNOME[op]; ctrl = op == 3
                if op == 3: ativo = ['uc', 'ula']
        else:                                        # EXECUTA
            uc = OPNOME[op]
            xa, ya, wa, ha = Dg.Lt['ra']; xb, yb, wb, hb = Dg.Lt['rb']; xu, yu, wu, hu = Dg.Lt['ula']
            bus = Dg.Lt['bus']; volta = Dg.Lt['volta']
            if op in (1, 2):
                alvo = 'ra' if op == 1 else 'rb'
                ativo = ['mem', alvo]
                x0, y0 = Dg.ancora('mem', arg)
                if op == 1: pts = [(x0, y0), (bus, y0), (bus, ya + ha / 2), (xa, ya + ha / 2)]
                else: pts = [(x0, y0), (bus, y0), (bus, ya - 4), (xb + wb / 2, ya - 4), (xb + wb / 2, yb)]
                if u < .8: pac = (pts, u / .8, str(a0['mem'][arg]))
                else:
                    kw['a_mostra' if op == 1 else 'b_mostra'] = a1['a'] if op == 1 else a1['b']
            elif op == 3:
                ativo = ['ra', 'rb', 'ula']; ctrl = True
                if u < .3:
                    uu = u / .3
                    pac = ([(xa + wa / 2, ya + ha), (xa + wa / 2, yu + 4)], uu, str(a0['a']))
                    self._pac2 = ([(xb + wb / 2, yb + hb), (xb + wb / 2, yu + 4)], uu, str(a0['b']))
                elif u < .78:
                    # a soma bit a bit, da direita para a esquerda (com o vai-um)
                    uu = (u - .3) / .48
                    a, b = a0['a'], a0['b']
                    s = a + b
                    nb_ = min(8, int(uu * 8.999))
                    mask = (1 << nb_) - 1
                    parcial = s & mask
                    ula = [f"{a} + {b}", binario(parcial, 8)[8 - nb_:].rjust(8, '.') if nb_ else "........"]
                else:
                    ula = [f"{a0['a']} + {a0['b']} = {a1['a']}"]
                    if u < .97:
                        pac = ([(xu + wu / 2, yu + hu), (xu + wu / 2, yu + hu + 6), (volta, yu + hu + 6),
                                (volta, ya + ha - 6), (xa, ya + ha - 6)], (u - .78) / .19, str(a1['a']))
                    else:
                        kw['a_mostra'] = a1['a']; ativo = ['ra']
            elif op == 4:
                ativo = ['ra', 'mem']
                x0, y0 = Dg.ancora('mem', arg)
                if u < .8:
                    pac = ([(xa, ya + ha / 2), (bus, ya + ha / 2), (bus, y0), (x0, y0)], u / .8, str(a0['a']))
                else: kw['mem_mostra'] = a1['mem']
            elif op == 5:
                ativo = ['ir', 'pc']
                xi, yi, wi, hi = Dg.Lt['ir']; xp, yp, wp, hp = Dg.Lt['pc']
                if u < .7:
                    pac = ([(xp + wp / 2, yi), (xp + wp / 2, yp + hp)], u / .7, str(arg))
                else: kw['pc_mostra'] = a1['pc']
        Dg.desenhar(tela, a0, t, ativo=ativo, uc_txt=uc, ula_txt=ula, ctrl=ctrl, **kw)
        rapido = self.fim[i] - self.ini[i] < .3
        if pac and not (rapido and VERTICAL is False and False):
            Dg.pacote(tela, pac[0], clamp(pac[1]), pac[2])
            if e == 2 and op == 3 and u < .3: Dg.pacote(tela, *self._pac2)
        nome = ETAPAS[e]
        self.vtxt(tela, f"{e + 1}: {nome}", AMARELO, y=196, tam=9)
        self.painel(tela, t, a1, e, i)

    def painel(self, tela, t, st, e, i):
        self.ptit(tela, "O CICLO DE INSTRUÇÃO")
        if VERTICAL: return
        for j, nome in enumerate(ETAPAS):
            y = 20 + j * 14
            on = j == e
            tela.ret(PX0, y, 160, 12, FUNDO3 if on else PRETO)
            tela.texto(f"{j + 1}  {nome}", PX0 + 4, y + 2, AMARELO if on else ACO1, tam=9, contorno=PRETO)
        nt = self.nb(t)
        self.ptxt(tela, f"TIQUE Nº {nt}", 66, BRANCO)
        on = self.desde_batida(t) < .12
        tela.disco(PX0 + 150, 69, 3, PRETO); tela.disco(PX0 + 150, 69, 2.2, VERDE if on else D.PCB0)
        if i >= 0:
            self.ptxt(tela, "PC", 84, ACO3)
            self.ptxt(tela, str(self.est[i + 1]['pc'] if e != 0 else self.est[i]['pc']), 94, AMARELO, 26)
            self.ptxt(tela, "A", 84, ACO3, x=PX0 + 60)
            self.ptxt(tela, str(self.est[i]['a']), 94, VERDE, 26, x=PX0 + 60)
            self.ptxt(tela, f"INSTRUÇÕES FEITAS: {self.est[i]['n']}", 126, ACO3)
            d = self.fim[i] - self.ini[i]
            if d > 1.01: txt = f"AQUI: 1 ETAPA A CADA {dec(d, 0)} S"
            elif d > .99: txt = "AQUI: 1 ETAPA POR SEGUNDO"
            else: txt = f"AQUI: {dec(1.0 / d, 0)} ETAPAS POR SEGUNDO"
            self.ptxt(tela, txt, 144, ACO2)
            if t >= 40.0:
                self.ptxt(tela, "NA VIDA REAL: BILHÕES", 160, AMARELO)
                self.ptxt(tela, "DE TIQUES POR SEGUNDO", 171, AMARELO)

    def sons(self, fx):
        for k, (a, b) in enumerate(zip(self.ini, self.fim)):
            e = self.est[k + 1]['etapa']
            g = .05 if b - a >= .5 else (.035 if b - a >= .25 else .022)
            self.nota(fx, a, [76, 79, 83][e], .05, g, [-.3, 0, .3][e])


# ============================================================ 11 a escala
def _tela_nivel():
    return PX.Tela(296, 208, paleta=LG.PAL)


def nivel_transistor(tela):
    D.grade_fundo(tela, 296)
    M = Mosfet(48, 82, 1.0)
    M.desenhar(tela, 1.0, 0.0)
    tela.texto("FONTE", 58, 140, ACO4, tam=9, contorno=PRETO)
    tela.texto("DRENO", 200, 140, ACO4, tam=9, contorno=PRETO)
    tela.texto("PORTA", 128, 26, ACO4, tam=9, contorno=PRETO)


def nivel_inversor(tela):
    D.grade_fundo(tela, 296)
    Fio([(60, 104), (110, 104), (110, 64), (158, 64)]).desenhar(tela, lambda u: 0, 0, herois=False)
    Fio([(60, 104), (110, 104), (110, 144), (163, 144)]).desenhar(tela, lambda u: 0, 0, herois=False)
    Fio([(170, 104), (230, 104)]).desenhar(tela, lambda u: 1, 0, herois=False)
    inversor(tela, 170, 0, 1, 0.0)


def nivel_portas(tela):
    D.grade_fundo(tela, 296)
    rng = np.random.default_rng(5)
    tipos = ['NAO', 'E', 'OU', 'XOR']
    for r in range(5):
        for c in range(6):
            x0, y = 14 + c * 46, 22 + r * 40
            tp = 'NAO' if (r, c) == (2, 2) else tipos[int(rng.integers(0, 4))]
            v = int(rng.integers(0, 2))
            Fio([(x0 - 10, y), (x0, y)]).desenhar(tela, lambda u, v=v: v, 0, herois=False)
            porta(tela, tp, x0, y, .9, nome=False)


def nivel_nucleo(tela):
    D.grade_fundo(tela, 296)
    cpu = CPU()
    Diagrama(False).desenhar(tela, cpu.estado(), 0.0, ula_txt=["PORTAS"])


def nivel_die(tela):
    tela.buf[:] = FUNDO
    x, y, w = 78, 34, 140
    tela.ret(x - 1, y - 1, w + 2, w + 2, PRETO)
    tela.ret(x, y, w, w, DIE1)
    for k in range(x + 3, x + w - 3, 4):
        tela.px(k, y + 2, COB2); tela.px(k, y + w - 3, COB2)
    for k in range(y + 3, y + w - 3, 4):
        tela.px(x + 2, k, COB2); tela.px(x + w - 3, k, COB2)
    for (cx, cy) in ((84, 40), (152, 40), (84, 88), (152, 88)):
        tela.ret(cx, cy, 60, 42, DIE2); tela.ret(cx, cy, 60, 1, DIE3)
        for k in range(cx + 2, cx + 58, 3):
            for j in range(cy + 3, cy + 40, 3):
                if (k * 7 + j * 3) % 11 < 3: tela.px(k, j, DIE3)
    tela.ret(84, 136, 128, 32, DIE0)
    for k in range(85, 211, 2):
        for j in range(137, 167, 2): tela.px(k, j, DIE2 if (k + j) % 4 == 0 else DIE1)


class Escala(Cena):
    NOMES = ["TRANSISTOR", "PORTA LÓGICA", "MUITAS PORTAS (ULA)", "NÚCLEO", "PASTILHA", "CHIP"]
    # onde cada nível de dentro mora no nível de fora (proporção 296:208)
    RS = [(156, 134, 28, 19.68), (14 + 2 * 46 - 4, 22 + 2 * 40 - 13, 36, 25.3), (160, 120, 128, 89.9),
          (84, 40, 60, 42.2), (105, 74, 86, 60.4)]
    T0, PASSO, ZOOM = .4, 2.4, 1.8

    def preparar(self):
        self.img = []
        for fn in (nivel_transistor, nivel_inversor, nivel_portas, nivel_nucleo, nivel_die):
            tl = _tela_nivel(); fn(tl); self.img.append(tl.buf.copy())
        tl = _tela_nivel(); self.desenhar_placa(tl, 0.0); self.img.append(tl.buf.copy())
        yy, xx = np.mgrid[0:208, 0:296]
        self.sx, self.sy = xx + .5, yy + .5

    def desenhar_placa(self, tela, t, R=None):
        tela.buf[:208, :296] = FUNDO
        placa(tela, 10, 14, 276, 180)
        b = 60
        tela.ret(148 - b / 2 - 1, 104 - b / 2 - 1, b + 2, b + 2, PRETO)
        dither(tela, 148 - b / 2, 104 - b / 2, b, b, PCB2, PCB1)
        for k in range(int(148 - b / 2) + 2, int(148 + b / 2) - 1, 3):
            tela.px(k, 104 + b / 2 - 2, LATAO); tela.px(k, 104 - b / 2 + 1, LATAO)
        x0, y0 = 105 + .264 * 86, 74 + .163 * 60.4
        lado = .472 * 86
        D.die(tela, x0, y0, lado, lado, t=t, nucleos=2)
        for k in range(4):
            bloco(tela, 30 + k * 16, 150, 42 + k * 16, 180, ACO0, ACO2, PRETO)
        tela.texto("MEMÓRIA", 30, 140, ACO3, tam=9, contorno=PRETO)

    def nivel(self, t):
        """(k, u): k = nível de dentro; u = 0 (dentro enche a tela) .. 1 (fora inteiro)."""
        for k in range(5):
            a = self.T0 + k * self.PASSO + (self.PASSO - self.ZOOM)
            if t < a: return k, 0.0
            if t < a + self.ZOOM: return k, suave((t - a) / self.ZOOM)
        return 5, 1.0

    def compor(self, tela, k, u):
        if k >= 5:
            return
        O, I = self.img[k + 1], self.img[k]
        rx, ry, rw, rh = self.RS[k]
        Z = 296 / rw
        z = Z ** (1 - u)
        rcx, rcy = rx + rw / 2, ry + rh / 2
        f = (1 - 1 / z) / (1 - 1 / Z)
        cx = rcx + (148 - rcx) * f; cy = rcy + (104 - rcy) * f
        ox = cx + (self.sx - 148) / z
        oy = cy + (self.sy - 104) / z
        dentro = (ox >= rx) & (ox < rx + rw) & (oy >= ry) & (oy < ry + rh)
        ix = np.clip(((ox - rx) / rw * 296).astype(int), 0, 295)
        iy = np.clip(((oy - ry) / rh * 208).astype(int), 0, 207)
        jx = np.clip(ox.astype(int), 0, 295); jy = np.clip(oy.astype(int), 0, 207)
        out = np.where(dentro, I[iy, ix], O[jy, jx])
        tela.buf[:208, :296] = out
        # moldura amarela do que estava na tela
        x0 = 148 + (rx - cx) * z; y0 = 104 + (ry - cy) * z
        if u > .02:
            tela.ret_vazado(int(x0) - 1, int(y0) - 1, int(rw * z) + 2, int(rh * z) + 2, AMARELO)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 22.6:
            k, u = self.nivel(t)
            if k < 5 and (u > 0 or k > 0 or True):
                if u == 0 and k > 0:
                    # nível k inteiro na tela (o de dentro do próximo zoom)
                    tela.buf[:208, :296] = self.img[k]
                    rx, ry, rw, rh = self.RS[k]
                    if int(t * 4) % 2 == 0: tela.ret_vazado(int(rx) - 1, int(ry) - 1, int(rw) + 2, int(rh) + 2, AMARELO)
                    nome = self.NOMES[k]
                elif u == 0:
                    tela.buf[:208, :296] = self.img[0]
                    nome = self.NOMES[0]
                else:
                    self.compor(tela, k, u)
                    nome = self.NOMES[k + 1] if u > .5 else self.NOMES[k]
            else:
                self.desenhar_placa(tela, t)
                nome = self.NOMES[5]
                # régua da pastilha
                x0, y0 = 105 + .264 * 86, 74 + .163 * 60.4
                lado = .472 * 86
                if t >= 15.2:
                    yb = y0 + lado + 22
                    tela.ret(x0, yb, lado, 1, AMARELO)
                    tela.ret(x0, yb - 3, 1, 7, AMARELO); tela.ret(x0 + lado - 1, yb - 3, 1, 7, AMARELO)
                    centro_preso(tela, "1 A 2 CM", x0 + lado / 2, yb + 5, AMARELO)
                    tela.ret(x0 + lado / 2, y0 + lado, 1, yb - y0 - lado, AMARELO)
                rotulo(tela, "PASTILHA (DIE)", 196, 40, x0 + lado - 4, y0 + 4, cor=ACO4)
            centro_preso(tela, nome, 148, 194, BRANCO, tam=17, xmin=4, xmax=294)
        elif t < 30.0:
            self.desenhar_pitch(tela, t)
        else:
            self.desenhar_1971(tela, t)
        # painel
        self.ptit(tela, "DO TRANSISTOR AO CHIP")
        if not VERTICAL:
            k, u = self.nivel(t)
            kk = k + (1 if u > .5 else 0)
            for j, nome in enumerate(self.NOMES):
                y = 20 + j * 11
                on = j == min(kk, 5) and t < 22.6
                tela.texto(nome, PX0 + 8, y, AMARELO if on else (ACO3 if j <= kk else ACO0), tam=9, contorno=PRETO)
                if on: tela.texto(">", PX0, y, AMARELO, tam=9, contorno=PRETO)
            if t >= 7.8:
                self.ptit(tela, "TRANSISTORES NUM CHIP", 92, AMARELO)
                self.ptxt(tela, milhar(TRANS_CHIP), 106, BRANCO, 17)
                self.ptxt(tela, "28 BILHÕES", 126, AMARELO)
            if t >= 15.2:
                self.ptxt(tela, "PASTILHA: 103,8 A 420,2 MM", 146, ACO3)
                self.ptxt(tela, "DE ÁREA = 1 A 2 CM DE LADO", 157, ACO3)
            if t >= 30.0:
                self.ptxt(tela, "EM 1971: " + milhar(TRANS_1971), 176, VERDE)
                self.ptxt(tela, f"HOJE: {dec(TRANS_CHIP / TRANS_1971 / 1e6, 1)} MILHÕES DE VEZES", 188, AMARELO)

    def desenhar_pitch(self, tela, t):
        """Corte de uma fileira de portas: a distância entre elas (pitch)."""
        u = suave((t - 22.6) / .8)
        y0 = 80
        tela.ret(10, y0 + 40, 278, 60, PRETO)
        dither(tela, 11, y0 + 41, 276, 58, SIP1, SIP0)
        passo = 46
        for k in range(6):
            x = 22 + k * passo
            on = (k + int(t * 2)) % 3 == 0
            tela.ret(x - 6, y0 + 41, 30, 10, SIN1)
            if on:
                tela.ret(x - 6, y0 + 41, 30, 2, CIANO)
            bloco(tela, x, y0 + 4, x + 18, y0 + 36, ACO3 if on else ACO2, ACO4, ACO0)
            tela.ret(x - 2, y0 + 36, 22, 4, OX0)
        # régua do pitch
        xa, xb = 22 + passo + 9, 22 + 2 * passo + 9
        yr = y0 - 12
        tela.ret(xa, yr, xb - xa, 1, AMARELO)
        tela.ret(xa, yr - 3, 1, 7, AMARELO); tela.ret(xb, yr - 3, 1, 7, AMARELO)
        tela.ret(xa, yr, 1, 16, AMARELO); tela.ret(xb, yr, 1, 16, AMARELO)
        centro_preso(tela, "45 A 54 NM", (xa + xb) / 2, yr - 13, AMARELO, tam=17, xmin=4, xmax=294)
        tela.texto("PORTAS VIZINHAS (CORTE)", 12, 190, ACO3, tam=9, contorno=PRETO)
        # o "3 nm" riscado
        bx, by = 196, 20
        painel(tela, bx, by, 92, 36, borda=VERMELHO)
        tela.texto("3 NM", bx + 46, by + 5, BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto("É SÓ O NOME", bx + 46, by + 24, VERMELHO, tam=9, centro=True, contorno=PRETO)
        tela.texto("1 NM = 1 MILIONÉSIMO DE MM", 12, 20, ACO3, tam=9, contorno=PRETO)

    def desenhar_1971(self, tela, t):
        # 2.250 transistores: uma grade de 50 x 45, um pixel aceso cada
        gx, gy = 20, 40
        painel(tela, gx - 6, gy - 22, 112, 126, borda=VERDE)
        tela.texto("1971", gx, gy - 16, VERDE, tam=9, contorno=PRETO)
        n = 0
        for r in range(45):
            for c in range(50):
                on = ((r * 50 + c) * 7 + int(t * 12)) % 13 < 4
                tela.px(gx + c * 2, gy + r * 2, VERDE if on else D.PCB1)
                n += 1
        assert n == TRANS_1971
        tela.texto("2.250", gx, gy + 92, BRANCO, tam=9, contorno=PRETO)
        # hoje: a mesma área nem mostra
        hx = 150
        painel(tela, hx - 6, gy - 22, 146, 126, borda=AMARELO)
        tela.texto("HOJE", hx, gy - 16, AMARELO, tam=9, contorno=PRETO)
        dither(tela, hx, gy, 134, 90, DIE3, DIE2)
        fase = int(t * 20)
        for k in range(160):
            x = hx + (k * 37 + fase * 13) % 134; y = gy + (k * 53 + fase * 7) % 90
            tela.px(x, y, BRANCO)
        tela.texto(milhar(TRANS_CHIP), hx, gy + 92, BRANCO, tam=9, contorno=PRETO)
        if t >= 37.2:
            centro_preso(tela, f"{dec(TRANS_CHIP / TRANS_1971 / 1e6, 1)} MILHÕES DE VEZES MAIS", 150, 176, AMARELO,
                         tam=9, xmin=4, xmax=294)
        tela.texto("1 PIXEL = 1 TRANSISTOR", gx - 4, 190, ACO3, tam=9, contorno=PRETO) if t < 37.2 else None

    def sons(self, fx):
        for k in range(5):
            a = self.T0 + k * self.PASSO + (self.PASSO - self.ZOOM)
            self.nota(fx, a + self.ZOOM, 72 + 2 * k, .5, .04)
        for a in (22.6, 30.0, 37.2): self.nota(fx, a, 84, .4, .04)


# ============================================================ 12 a luz
class Luz(Cena):
    XV = 90

    def regua(self):
        if VERTICAL: return 10, 6.4, 25
        return 24, 6.5, 40

    def tique_k(self, t):
        """Os tiques desta cena: 1 a cada 4 batidas (câmera lenta)."""
        return max(0, (self.nb(t) - 1) // 4)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        x0, ppc, cm = self.regua()
        cm_tique = C_LUZ / GHZ * 100                    # 9,99 cm
        T = self.tb(4) - self.tb(0)                     # 3 s por tique
        # régua
        y = 58
        tela.ret(x0 - 2, y - 2, cm * ppc + 4, 12, PRETO)
        tela.ret(x0, y, cm * ppc, 8, ACO1)
        for c in range(cm + 1):
            xx = x0 + c * ppc
            tela.ret(xx, y, 1, 4 if c % 5 else 8, PRETO)
            if c % 10 == 0 and c < cm - 3:
                tela.texto(f"{c}", int(xx - 2), y + 12, ACO3, tam=9, contorno=PRETO)
        tela.texto("CM", int(x0 + cm * ppc - 12), y + 12, ACO2, tam=9, contorno=PRETO)
        # o chip que manda o sinal
        bloco(tela, x0 - 8, 22, x0 + 6, 40, DIE2, DIE3, DIE0)
        # um pulso de luz sai a cada tique e anda a c (em câmera lenta)
        k = self.tique_k(t)
        ta = self.tb(4 * k + 1) if t >= self.tb(1) else None
        if t >= self.tb(1):
            for j in range(max(0, k - 3), k + 1):
                tj = self.tb(4 * j + 1)
                if t < tj: continue
                d = (t - tj) / T * cm_tique
                if d > cm: continue
                xx = x0 + d * ppc
                for r in range(1, 10):
                    tela.ret(xx - r * 2, 31, 2, 2, CHAMA1 if r < 4 else LARANJA)
                bit_luz(tela, xx, 32, 1, 3.5)
            for m in range(1, 4):
                xm = x0 + m * cm_tique * ppc
                if xm > x0 + cm * ppc: break
                tela.ret(xm, 44, 1, 12, AMARELO)
                tela.texto(f"{m} TIQUE" + ("S" if m > 1 else ""), int(xm - 18), 46 - 12 - 26, AMARELO, tam=9,
                           contorno=PRETO) if False else None
            xm = x0 + cm_tique * ppc
            centro_preso(tela, "1 TIQUE", xm, 82, AMARELO, xmin=2, xmax=x0 + cm * ppc + 4)
            tela.ret(xm, 70, 1, 10, AMARELO)
        # placa vista de cima: processador, memória e o alcance de 1 tique
        if not VERTICAL:
            bx, by = 24, 98
        else:
            bx, by = 10, 98
        placa(tela, bx, by, 160 if VERTICAL else 266, 104)
        pcx, pcy = bx + 24, by + 52
        alcance = cm_tique * ppc
        for a in range(0, 64):
            ang = -math.pi / 2 + math.pi * a / 63
            xx, yy = pcx + math.cos(ang) * alcance, pcy + math.sin(ang) * alcance
            if by < yy < by + 104 and (a + int(t * 8)) % 3 == 0: tela.ret(xx, yy, 2, 2, AMARELO)
        pacote(tela, pcx, pcy, 14, t=t, nucleos=2)
        for j in range(2):
            mx = pcx + 26 + j * 14
            bloco(tela, mx, pcy - 16, mx + 8, pcy + 16, ACO0, ACO2, PRETO)
        tela.texto("MEMÓRIA", int(pcx + 22), int(pcy + 22), ACO3, tam=9, contorno=PRETO)
        if t >= 15.2:
            tela.texto("ALCANCE DE 1 TIQUE", int(pcx + alcance - 60), by + 6, AMARELO, tam=9, contorno=PRETO)
        self.vtxt(tela, "1 TIQUE = " + dec(cm_tique, 2) + " CM", AMARELO, y=6, tam=9)
        # painel
        self.ptit(tela, "A LUZ NUM TIQUE")
        self.ptxt(tela, "VELOCIDADE DA LUZ", 20, ACO3)
        self.ptxt(tela, milhar(C_LUZ) + " M/S", 31, BRANCO)
        self.ptxt(tela, "1 TIQUE A 3 GHZ", 50, ACO3)
        self.ptxt(tela, dec(1e9 / GHZ, 2) + " NS", 61, BRANCO, 17)
        self.ptxt(tela, "(BILIONÉSIMOS DE SEGUNDO)", 80, ACO2)
        self.ptxt(tela, "A LUZ ANDA", 98, ACO3)
        self.ptxt(tela, dec(cm_tique, 2) + " CM", 109, AMARELO, 26)
        self.ptxt(tela, f"TIQUE Nº {self.tique_k(t) + (1 if t >= self.tb(1) else 0)}", 146, BRANCO)
        self.ptxt(tela, "AQUI: 1 TIQUE EM 3 S", 160, ACO2)
        self.ptxt(tela, "(CÂMERA BEM LENTA)", 171, ACO2)

    def sons(self, fx):
        k = 0
        while 4 * k + 1 < len(self.bt):
            self.tique(fx, self.bt[4 * k + 1], 2200.0, .04, .06, -.5)
            k += 1


# ============================================================ 13 vários núcleos
class Nucleos(Cena):
    XV = 110
    DADOS = [(5, 3), (2, 7), (1, 1), (4, 4), (6, 2), (3, 3), (9, 1), (2, 2), (7, 1), (1, 5)]

    def preparar(self):
        self.runs = []
        for a, b in self.DADOS:
            cpu = CPU(); cpu.mem[8], cpu.mem[9] = a, b
            seq = [cpu.estado()]
            for _ in range(200): seq.append(cpu.passo())
            self.runs.append(seq)

    def fase(self, t): return 0 if t < 7.8 else (1 if t < 15.2 else 2)

    def passos(self, t, j):
        """Etapas que o núcleo j já fez: os grandes 1 por batida, os pequenos 1 a cada 2."""
        t_ini = 0.0 if j == 0 else (7.8 if j < 4 else 15.2)
        n = max(0, self.nb(t) - self.nb(t_ini - 1e-3))
        if j >= 4: n //= 2
        return min(n, 200)

    def caixas(self, f):
        x0, y0, w = 26, 22, 168
        if f == 0: return [(x0 + 4, y0 + 4, w - 8, 128)]
        if f == 1:
            m = (w - 12) / 2
            return [(x0 + 4 + (k % 2) * (m + 4), y0 + 4 + (k // 2) * 66, m, 62) for k in range(4)]
        out = [(x0 + 4 + (k % 2) * 82, y0 + 4 + (k // 2) * 46, 78, 42) for k in range(4)]
        out += [(x0 + 4 + (k % 3) * 54, y0 + 98 + (k // 3) * 20, 50, 17) for k in range(6)]
        return out

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        f = self.fase(t)
        x0, y0, w = 26, 22, 168
        tela.ret(x0 - 1, y0 - 1, w + 2, 140 + 2, PRETO)
        tela.ret(x0, y0, w, 140, DIE1)
        tela.ret(x0, y0, w, 1, DIE3)
        for k in range(x0 + 2, x0 + w - 2, 4):
            tela.px(k, y0 + 1, COB2); tela.px(k, y0 + 138, COB2)
        tot = 0
        for j, (cx, cy, cw, ch) in enumerate(self.caixas(f)):
            n = self.passos(t, j)
            st = self.runs[j][n]
            tot += st['n']
            on = self.desde_batida(t) < .15 and (f < 2 or j < 4 or (self.nb(t) % 2 == 0))
            tela.ret(cx - 1, cy - 1, cw + 2, ch + 2, AMARELO if on else PRETO)
            tela.ret(cx, cy, cw, ch, DIE2)
            tela.ret(cx, cy, cw, 1, DIE3)
            if ch >= 40:
                tela.texto(f"NÚCLEO {j + 1}", int(cx + 3), int(cy + 3), BRANCO, tam=9, contorno=PRETO)
                tela.texto("PC", int(cx + 3), int(cy + 15), ACO3, tam=9, contorno=PRETO)
                for b in range(4):
                    bit = (st['pc'] >> (3 - b)) & 1
                    celula(tela, cx + 18 + b * 9, cy + 14, 8, 9, bit, rotulo_txt=False)
                tela.texto(f"A = {st['a']}", int(cx + 3), int(cy + 28), VERDE, tam=9, contorno=PRETO)
                if ch >= 60:
                    tela.texto(ETAPAS[st['etapa']], int(cx + 3), int(cy + 40), AMARELO, tam=9, contorno=PRETO)
                    tela.texto(f"INSTRUÇÕES: {st['n']}", int(cx + 3), int(cy + ch - 10), ACO3, tam=9, contorno=PRETO)
            else:
                for b in range(4):
                    bit = (st['pc'] >> (3 - b)) & 1
                    celula(tela, cx + 3 + b * 7, cy + 4, 6, 8, bit, rotulo_txt=False)
                tela.texto(str(st['a']), int(cx + 33), int(cy + 5), VERDE, tam=9, contorno=PRETO)
        if f == 2:
            tela.texto("DESEMPENHO", x0 + 4, y0 + 144, AMARELO, tam=9, contorno=PRETO)
            tela.texto("ECONOMIA", x0 + 104, y0 + 144, CIANO, tam=9, contorno=PRETO)
            tela.ret(x0 + 2, y0 + 96, w - 4, 1, DIE3)
        n_nuc = len(self.caixas(f))
        self.vtxt(tela, f"{n_nuc} NÚCLEO" + ("S" if n_nuc > 1 else ""), AMARELO, y=4, tam=17)
        if not VERTICAL:
            centro_preso(tela, f"{n_nuc} NÚCLEO" + ("S" if n_nuc > 1 else "") + " NUM SÓ CHIP", 110, 186, BRANCO,
                         tam=9, xmin=4, xmax=294)
            # do lado: as tarefas rodando em paralelo
            for j in range(min(n_nuc, 10)):
                y = 24 + j * 15
                n = self.passos(t, j)
                tela.texto(f"{j + 1:>2}", 206, y, ACO2, tam=9, contorno=PRETO)
                for q in range(10):
                    on = q < (n % 11)
                    tela.ret(222 + q * 7, y, 5, 7, (AMARELO if j < 4 or f < 2 else CIANO) if on else FUNDO2)
        # painel
        self.ptit(tela, "NÚCLEOS")
        self.ptxt(tela, str(n_nuc), 20, AMARELO, 26)
        self.ptxt(tela, "AO MESMO TEMPO", 50, BRANCO)
        self.ptxt(tela, "INSTRUÇÕES FEITAS", 74, ACO3)
        self.ptxt(tela, "(SOMANDO TODOS)", 85, ACO2)
        self.ptxt(tela, str(tot), 97, VERDE, 17)
        if f == 2:
            self.ptxt(tela, "4 DE DESEMPENHO", 124, AMARELO)
            self.ptxt(tela, "6 DE ECONOMIA (MAIS", 136, CIANO)
            self.ptxt(tela, "DEVAGAR, GASTAM MENOS)", 147, CIANO)
        self.ptxt(tela, "CADA UM COM SEU PC", 170, ACO2)

    def sons(self, fx):
        for k, tk in enumerate(self.bt):
            f = self.fase(tk)
            self.tique(fx, tk, 1400.0 + 200 * f, .03, .03 + .01 * f, -.3 + .3 * f)
        for a in (7.8, 15.2): self.nota(fx, a, 81, .4, .05)


# ============================================================ 14 resumo
class Resumo(Cena):
    XS = [34, 92, 150, 208, 266]
    NOMES = ["TRANSISTOR", "PORTA", "SOMADOR", "NÚCLEO", "CHIP"]

    def preparar(self):
        self.f = Fio([(14, 70), (286, 70)])

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        k = max(0, self.nb(t) - 1)
        u = clamp(self.desde_batida(t) / .45)
        pos = k % 6
        # o fio da corrente de peças
        xb = lerp(self.XS[pos - 1] if pos > 0 else 14, self.XS[min(pos, 4)], ease(u)) if pos < 5 else 286
        self.f.desenhar(tela, lambda uu: 1 if 14 + uu * 272 <= xb else 0, t, herois=False)
        ativo = min(pos, 4) if u >= 1 and pos < 5 else (pos - 1 if pos > 0 else -1)
        for j, x in enumerate(self.XS):
            on = j <= ativo
            painel(tela, x - 24, 46, 48, 48, borda=AMARELO if j == ativo else (ACO2 if on else ACO0))
            if j == 0: chave_mos(tela, x + 4, 70, 'n', on, val_porta=on)
            elif j == 1: porta(tela, 'E', x - 13, 70, .95, saida=on, nome=False)
            elif j == 2:
                bloco(tela, x - 14, 58, x + 14, 82, D.POR2 if on else D.POR1, ACO4, D.POR0)
                tela.texto("+", x, 62, AMARELO if on else ACO3, tam=17, centro=True, contorno=PRETO)
            elif j == 3:
                for q in range(4):
                    bx, by = x - 16 + (q % 2) * 17, 54 + (q // 2) * 17
                    tela.ret(bx, by, 14, 14, (CIANO if q == (k % 4) else ACO1) if on else FUNDO3)
            else:
                D.die(tela, x - 18, 52, 36, 36, t=t, nucleos=2, aceso=None if on else [])
            centro_preso(tela, self.NOMES[j], x, 100, AMARELO if j == ativo else ACO3, xmin=2, xmax=296)
        bit_luz(tela, xb, 71, 1, 3.5)
        # o ciclo, uma etapa por batida
        e = k % 3
        for j, nome in enumerate(ETAPAS):
            x = 20 + j * 92
            on = j == e
            painel(tela, x, 130, 82, 24, borda=AMARELO if on else ACO1)
            centro_preso(tela, nome, x + 41, 138, AMARELO if on else ACO2, xmin=x + 2, xmax=x + 80)
            if j < 2: seta(tela, x + 83, 142, x + 91, 142, ACO2, esp=1, ponta=3)
        Fio([(266, 156), (266, 168), (60, 168), (60, 156)]).desenhar(tela, lambda uu: 1 if e == 2 else 0, t,
                                                                       herois=False)
        tela.texto("E DE NOVO, A CADA TIQUE", 96, 176, ACO2, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "TIQUES DESTE VÍDEO")
        self.ptxt(tela, "SE FOSSE UM CHIP DE 3 GHZ:", 20, ACO3)
        self.ptxt(tela, milhar(int(tg * 3)), 32, AMARELO, 17)
        self.ptxt(tela, "BILHÕES DE TIQUES", 52, BRANCO)
        self.ptit(tela, "AQUI NA TELA", 76)
        self.ptxt(tela, f"{self.nb(t)} TIQUES", 92, BRANCO, 17)
        self.ptxt(tela, "TUDO FEITO DE 0 E 1:", 130, ACO3)
        bits = ''.join('1' if ((q * 5 + int(tg * 6)) % 3) else '0' for q in range(24))
        self.ptxt(tela, bits, 142, AMARELO)

    def sons(self, fx):
        for k, tk in enumerate(self.bt):
            self.nota(fx, tk + .4, 72 + [0, 3, 7, 10, 12, 15][k % 6], .06, .035)


# ============================================================ 15 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            D.grade_fundo(tela, W)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            pacote(tela, W // 2, 130, 44, t=t, nucleos=4)
            f = Fio([(60, 130), (W // 2 - 36, 130)]); g = Fio([(W // 2 + 36, 130), (W - 60, 130)])
            f.desenhar(tela, lambda u: int(((t * 1.4 - u * 3) % 1) < .4), t)
            g.desenhar(tela, lambda u: int(((t * 1.4 - u * 3 + .5) % 1) < .4), t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, bits=Bits, contar=Contar, transistor=Transistor, portas=Portas,
             somador=Somador, soma4=Soma4, relogio=Relogio, cpu=Pecas, ciclo=Ciclo, escala=Escala, luz=Luz,
             nucleos=Nucleos, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep16_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        so = sys.argv[3:] or None
        fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = int(os.environ.get('COLS', 4 if len(ims) > 4 else len(ims)))
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
