#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep11 — A jornada da água: da represa até a sua tomada (PT-BR).

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (chuva, comporta, água correndo,
                          turbina, gerador, zumbido do transformador,
                          interruptor), nos mesmos instantes do desenho
A posição da gota (e depois da energia) sai de uma função do tempo em cada
capítulo; o painel lê a mesma função (etapa, forma da energia, tensão).

    python3 ep11_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep11_motor.py <saida.mp4> turbina gerador     # só esses capítulos (teste)
    python3 ep11_motor.py --folha <saida.png> [ids]       # 2 quadros por capítulo
    python3 ep11_motor.py --quadros <saida.png> id:t ...  # quadros escolhidos
"""
import math, sys
import numpy as np
import ep11_desenho as D                      # registra a paleta 'ep11' (antes de qualquer Tela)
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep11_desenho import (CEU0, CEU1, CEU2, GRAMA0, GRAMA1, GRAMA2, TERRA0, TERRA1, CONC0, CONC1, CONC2,
                          AGP, AGM, AGC, ESPUMA, COBRE0, COBRE1, COBRE2, NUVEM0, NUVEM1,
                          ETAPAS, rotulo, fio, seta, halo, luz, mira, caixa, gota, marca_gota, faisca,
                          agua, nuvem, ceu, chuva, morro, interp, ao_longo, arvore, tubo, grad_v, grad_h,
                          fmt_v, lerp, V_GERADOR, V_LINHA, V_SUB, V_DIST, V_CASA)
import ritmo_marca as RM
import idioma as I
from ep11_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2611, 43
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px


def um(u): return min(1.0, max(0.0, u))


def fase(t, a, b): return um((t - a) / max(1e-6, b - a))


class Cena:
    legenda = True
    brilho = None
    K = 0                     # etapa do painel (0..8)
    VX = 150                  # centro do recorte vertical (selo da etapa no Short)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def painel(self, tela, t, selo=None, **kw):
        if VERTICAL:
            D.selo_vertical(tela, self.K, self.VX, selo)
        else:
            D.painel_jornada(tela, self.K, t, **kw)

    def rot(self, tela, txt, x, y, cor=BRANCO, alvo=None, centro=False):
        """Rótulo com fio opcional; no Short some se sair do recorte."""
        if VERTICAL:
            w = tela.largura_texto(txt, 9)
            xa = x - w // 2 if centro else x
            if xa < self.VX - 88 or xa + w > self.VX + 88: return
        rotulo(tela, txt, x, y, cor, centro=centro)
        if alvo:
            w = tela.largura_texto(txt, 9)
            xa = x - w // 2 if centro else x
            ax = xa + w // 2
            ay = y + 9 if alvo[1] > y else y - 2
            fio(tela, ax, ay, alvo[0], alvo[1], cor)


def grade(tela, x0=0, x1=W):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(x0, x1, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(x0, y, x1 - x0, 1, FUNDO2)


# ============================================================ gancho
ICX = [30 + i * 52.5 for i in range(9)]


class Gancho(Cena):
    def desenhar(self, tela, t, tg):
        if t < 5.8:
            self.quarto(tela, t)
        else:
            self.trilha_inversa(tela, t - 5.8)

    def quarto(self, tela, t):
        ligada = t >= 1.3
        tela.buf[:PALCO_H] = FUNDO
        dither(tela, 0, 0, W, 170, FUNDO2 if ligada else FUNDO, FUNDO)
        if ligada:
            a = um((t - 1.3) / .3)
            pisca = a < 1 and int(t * 20) % 2
            if not pisca:
                for r, c in ((150, FUNDO3), (100, TRACO), (60, ACO0)):
                    D.halo(tela, 240, 64, r * (.6 + .4 * a), c, fase=r // 50)
        # piso e rodapé
        grad_v(tela, 0, 170, W, PALCO_H - 170, [TERRA1, TERRA0, TERRA0])
        tela.ret(0, 168, W, 2, PRETO)
        for x in range(0, W, 36): tela.ret(x, 172, 1, PALCO_H - 172, TERRA0)
        # janela com chuva lá fora
        jx, jy = 40, 40
        caixa(tela, jx, jy, 70, 60, CEU0, ACO1, ACO0)
        tela.ret(jx + 34, jy, 2, 60, ACO1); tela.ret(jx, jy + 29, 70, 2, ACO1)
        chuva(tela, jx + 2, jx + 68, jy + 2, jy + 58, t, n=16, vel=90)
        # mesa e lâmpada pendurada
        caixa(tela, 330, 140, 90, 6, TERRA1, LATAO, TERRA0)
        tela.ret(338, 146, 4, 24, TERRA0); tela.ret(408, 146, 4, 24, TERRA0)
        D.lampada(tela, 240, 64, 1.0 if (ligada and not (um((t - 1.3) / .3) < 1 and int(t * 20) % 2)) else 0.0, t, fio_ate=0)
        # interruptor na parede
        D.interruptor(tela, 300, 112, ligada)
        if t < 1.6:
            mira(tela, 300, 112, t, 9)
        if ligada:
            self.rot(tela, 'A LUZ', 254, 92, CHAMA0, alvo=(246, 74))

    def trilha_inversa(self, tela, u):
        """O caminho de volta: da lâmpada até a nuvem, ícone por ícone."""
        tela.buf[:PALCO_H] = FUNDO
        grade(tela)
        tela.texto('DE ONDE VEM A ENERGIA?', W // 2, 18, ACO3, tam=17, centro=True, contorno=PRETO)
        prog = um(u / 4.2)                         # 1 = chegou na nuvem
        for i in range(9):
            j = 8 - i                              # acende de trás para frente
            aceso = prog * 9 >= i - .2
            D.icone(tela, j, ICX[j], 100, u, aceso=aceso)
            tela.texto(str(j + 1), ICX[j], 128, ETAPAS[j][1] if aceso else ACO1, tam=9, centro=True, contorno=PRETO)
            if j < 8:
                xa = ICX[j] + 22; xb = ICX[j + 1] - 22
                tela.ret(xa, 100, xb - xa, 1, ACO1 if not aceso else ETAPAS[j][1])
        x = lerp(ICX[8], ICX[0], ease(prog))
        luz(tela, x, 142, 2.5, BRANCO, AMARELO, CHAMA1)
        tela.ret(ICX[0], 142, ICX[8] - ICX[0], 1, FUNDO3)
        if prog >= 1:
            v = um((u - 4.2) / 1.2)
            gota(tela, ICX[0], 156 + 0 * v, 1.6, u)
            rotulo(tela, 'UMA GOTA DE CHUVA', ICX[0] + 14, 152, AMARELO)
        rotulo(tela, 'NUVEM', ICX[0], 166 + 12, ACO3, centro=True) if prog >= 1 else None
        rotulo(tela, 'SUA LUZ', ICX[8], 166 + 12, CHAMA1, centro=True)

    def sons(self, fx):
        fx.put(fx.clique(2400, .03), self.t0 + 1.25, .6)
        fx.put(fx.sino(81, 1.2), self.t0 + 1.35, .25)
        fx.put(fx.chiado(5.5, 1500, 5000), self.t0 + .2, .06)
        for i in range(9):
            fx.put(fx.blip(84 - i * 2, .06), self.t0 + 5.8 + i * 4.2 / 9, .12)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        chuva(tela, 0, W, 0, PALCO_H, t, n=50, vel=110, cor=FUNDO3, seed=3)
        tela.texto('SÉRIE A JORNADA', W // 2, 22, ACO3, tam=9, centro=True, contorno=PRETO)
        n = int(t / .045)
        for j, linha in enumerate(("A JORNADA", "DA ÁGUA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 10)]
            tela.texto(vis, W // 2 - larg // 2, 44 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto('DA REPRESA ATÉ A SUA TOMADA', W // 2, 118, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 9 * 18 // 2 + k * 18
                c = cor if t > 2.0 + k * .3 else FUNDO2
                tela.ret(x, 146, 14, 14, PRETO); tela.ret(x + 1, 147, 12, 12, c)
                tela.texto(str(k + 1), x + 7, 150, PRETO, tam=9, centro=True)
        y = 40 + (t * 40) % 140
        gota(tela, 80, y, 1.6, t)
        gota(tela, 400, 40 + (t * 40 + 70) % 140, 1.6, t, prota=False)

    def sons(self, fx):
        for k in range(9):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12, 14)[k], .08), self.t0 + 2.0 + k * .3, .14)


# ============================================================ 1 chuva
G_CHUVA = [(-2, 74), (22, 66), (46, 70), (76, 90), (106, 116), (136, 144), (160, 160), (180, 168), (300, 168)]
CORREGO = [(58, 80), (72, 90), (90, 103), (106, 118), (122, 132), (140, 148), (156, 160), (172, 171)]


class Chuva(Cena):
    K, VX = 0, 150

    def pos_gota(self, t):
        if t < 5.0: return (70, 46), 'NA NUVEM'
        if t < 8.0:
            u = ((t - 5.0) / 3.0) ** 2
            return (lerp(70, 58, u), lerp(46, 78, u)), 'CAINDO'
        if t < 16.0:
            return ao_longo(CORREGO, suave((t - 8.0) / 8.0)), 'NO CÓRREGO'
        if t < 26.0:
            u = (t - 16.0) / 10.0
            return (lerp(172, 258, u), 173 + math.sin(t * 3) * .8), 'NO RIO'
        return (258 + math.sin(t) * 2, 174 + math.sin(t * 2.5)), 'NA REPRESA'

    def desenhar(self, tela, t, tg):
        ceu(tela, 140, 0, 300, t, estrelas=False, cores=(CEU0, CEU1, CEU1, CEU2))
        # morros do fundo
        fundo = [(x, 112 - 18 * math.sin(x * .03 + 1) - 8 * math.sin(x * .09)) for x in range(-4, 304, 8)]
        morro(tela, fundo, GRAMA0, TRACO)
        # chão
        poligono(tela, [(-2, PALCO_H)] + G_CHUVA + [(300, PALCO_H)], GRAMA1)
        grad_v(tela, 0, 120, 300, PALCO_H - 120, [GRAMA1, GRAMA0, GRAMA0], mascara=lambda xx, yy: yy > np.array([interp(G_CHUVA, x) + 6 for x in range(0, 300)])[xx])
        for (ax, ay), (bx, by) in zip(G_CHUVA, G_CHUVA[1:]):
            tela.linha(ax, ay, bx, by, GRAMA2)
        for x in (12, 30, 40, 88, 100, 196, 214):
            arvore(tela, x, interp(G_CHUVA, x) + 2, 12 + (x % 3) * 2)
        # córrego
        for (ax, ay), (bx, by) in zip(CORREGO, CORREGO[1:]):
            linha_grossa(tela, ax, ay, bx, by, 4, PRETO)
        for (ax, ay), (bx, by) in zip(CORREGO, CORREGO[1:]):
            linha_grossa(tela, ax, ay, bx, by, 2.4, AGM)
        for k in range(14):
            p = ao_longo(CORREGO, (k / 14 + t * .12) % 1.0)
            tela.px(p[0], p[1] - 1, ESPUMA if k % 3 == 0 else AGC)
        # rio e represa
        tela.ret(150, 167, 82, 20, PRETO)
        agua(tela, 152, 232, 170, 186, t, onda=.6)
        grad_v(tela, 150, 186, 82, PALCO_H - 186, [GRAMA0, TERRA0])
        agua(tela, 228, 300, 168, PALCO_H, t, onda=.8)
        for k in range(8):
            x = 160 + ((k * 23 + t * 18) % 70)
            tela.ret(x, 175 + (k % 3) * 3, 3, 1, ESPUMA)
        # nuvens e chuva
        dx = math.sin(t * .2) * 6
        chuva(tela, 20, 280, 40, PALCO_H, t, n=46, vel=160, chao=lambda x: interp(G_CHUVA, x) if x < 228 else 168)
        nuvem(tela, 200 + dx * .5, 20, 64, chuva=True)
        nuvem(tela, 70 + dx, 28, 84, chuva=True)
        # a gota
        (gx, gy), onde = self.pos_gota(t)
        if t < 5.0:
            s = .5 + .5 * ease(t / 3.0)
            gota(tela, gx, gy, s, t)
        else:
            gota(tela, gx, gy, 1.0, t)
        if 7.9 < t < 8.5: D.respingo(tela, 58, 79, (t - 7.9) / .6)
        if t > .8:
            lado = -1 if gx > 200 else 1
            marca_gota(tela, gx, gy, t, 'A NOSSA GOTA', lado=lado, dy=-24 if gy > 60 else 14)
        if not VERTICAL:
            self.rot(tela, 'MORRO', 6, 96, GRAMA2)
            if t > 7.6: self.rot(tela, 'CÓRREGO', 112, 104, AGC, alvo=(108, 118))
            if t > 14.8: self.rot(tela, 'RIO', 186, 190, AGC)
            if t > 22.0:
                self.rot(tela, 'REPRESA', 238, 190, ESPUMA)
                seta(tela, 288, 194, 1, 0, ESPUMA, 4)
        self.painel(tela, t, forma=0, tensao=0, estado=('ONDE ESTÁ A GOTA', onde, AGC))

    def sons(self, fx):
        for k in range(6):
            fx.put(fx.chiado(5.5, 2500, 7000), self.t0 + k * 5.0, .05)
        fx.put(fx.blip(88, .05), self.t0 + 7.95, .18)
        fx.put(fx.chiado(18.0, 300, 1200, ataque=1.0), self.t0 + 8.0, .07)


# ============================================================ 2 represa
NIVEL, CAUDA = 52, 178        # superfície da represa e do rio lá embaixo (y)
BARR = [(150, 44), (166, 44), (232, 196), (150, 196)]


def x_jusante(y):            # face de jusante da barragem
    return 166 + (y - 44) / (196 - 44) * (232 - 166)


class Represa(Cena):
    K, VX = 1, 150

    def desenhar(self, tela, t, tg):
        ceu(tela, 120, 0, 300, t, estrelas=True, cores=(CEU0, CEU0, CEU1, CEU2))
        serra = [(x, 64 - 14 * math.sin(x * .04) - 6 * math.sin(x * .13 + 2)) for x in range(-4, 304, 6)]
        morro(tela, serra, FUNDO3, TRACO)
        # rocha / fundo
        grad_v(tela, 0, 190, 300, PALCO_H - 190, [TERRA1, TERRA0, TERRA0])
        # represa (montante)
        agua(tela, 0, 151, NIVEL, 196, t, cores=(AGC, AGM, AGM, AGP, AGP, AGP))
        # rio a jusante
        agua(tela, 248, 300, CAUDA, 196, t, onda=.6)
        # barragem
        D.concreto(tela, BARR, t)
        tela.ret(148, 41, 20, 3, PRETO); tela.ret(149, 42, 18, 1, ACO3)
        for x in range(150, 167, 4): tela.ret(x, 38, 1, 4, ACO2)
        tela.ret(150, 38, 17, 1, ACO2)
        # tomada d'água e conduto (em corte, tracejado)
        tela.ret(150, 140, 4, 14, PRETO)
        for y in range(141, 153, 2): tela.ret(150, y, 3, 1, ACO2)
        D.tubo(tela, 154, 147, 222, 172, 7, t, fluxo=True, vel=40)
        # casa de força no pé da barragem
        D.casa_de_forca(tela, 212, 150, 38, 36, t)
        tela.ret(232, 172, 18, 8, PRETO); agua(tela, 233, 250, 174, 186, t, onda=.4, brilho=False)
        # marcação da queda
        for x in range(150, 292, 4):
            tela.px(x, NIVEL, AGC if x > 166 else ESPUMA)
        for x in range(250, 292, 4):
            tela.px(x, CAUDA, AGC)
        mostra_q = t > 14.8
        if mostra_q:
            pulso = 1 + .3 * math.sin(t * 5)
            cor = AMARELO if t < 29 else AGC
            tela.ret(281, NIVEL + 4, 3, CAUDA - NIVEL - 8, PRETO); tela.ret(282, NIVEL + 4, 1, CAUDA - NIVEL - 8, cor)
            seta(tela, 282, NIVEL + 1, 0, -1, cor, 4) if False else None
            for k in range(4):
                tela.ret(282 - k, NIVEL + 1 + k, 2 * k + 1, 1, cor)
                tela.ret(282 - k, CAUDA - 1 - k, 2 * k + 1, 1, cor)
            tela.texto('QUEDA', 276, 74, cor, tam=17, centro='d', contorno=PRETO)
            if t > 22.0:
                tela.texto('ITAIPU:', 276, 94, BRANCO, tam=9, centro='d', contorno=PRETO)
                tela.texto('118 M', 276, 105, AMARELO, tam=17, centro='d', contorno=PRETO)
        # a gota
        if t < 26.0:
            gx, gy = 70 + math.sin(t * .6) * 6, NIVEL - 2 + math.sin(t * 2.2) * 1
        else:
            u = suave((t - 26.0) / 9.5)
            gx, gy = lerp(76, 146, u), lerp(NIVEL - 2, 146, u)
        gota(tela, gx, gy, 1.0, t)
        if t > 29.0:
            halo(tela, gx, gy - 2, 9 + math.sin(t * 6), AGC)
            gota(tela, gx, gy, 1.0, t)
        marca_gota(tela, gx, gy, t, 'A GOTA', lado=1, dy=-26 if gy < 120 else -26)
        if not VERTICAL:
            self.rot(tela, 'REPRESA', 18, 72, ESPUMA)
            self.rot(tela, 'BARRAGEM', 186, 50, BRANCO, alvo=(164, 66))
            if t > 7.6:
                self.rot(tela, 'USINA', 216, 136, BRANCO, alvo=(228, 150))
                self.rot(tela, 'RIO', 262, 186, ESPUMA)
        else:
            if t > 7.6: self.rot(tela, 'RIO', 222, 190, ESPUMA)
        est = ('A GOTA ESTÁ', 'NO ALTO', AGC) if t < 29 else ('ENERGIA', 'GUARDADA', AGC)
        self.painel(tela, t, forma=0, tensao=0, estado=est)

    def sons(self, fx):
        fx.put(fx.chiado(12.0, 120, 500, ataque=2.0), self.t0 + .5, .08)
        fx.put(fx.chiado(10.0, 120, 500, ataque=2.0), self.t0 + 13.0, .06)
        fx.put(fx.sino(76, 1.0), self.t0 + 14.9, .2)
        fx.put(fx.sino(79, 1.0), self.t0 + 22.1, .2)
        fx.put(fx.chiado(9.0, 200, 900, ataque=1.0), self.t0 + 26.0, .06)


# ============================================================ 3 conduto
P0, P1 = (48, 66), (316, 206)         # eixo do conduto (sai da tela embaixo à direita)
ESP_TUBO = 26


def no_tubo(u, off=0.0):
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    return P0[0] + dx * u + nx * off, P0[1] + dy * u + ny * off


class Conduto(Cena):
    K, VX = 2, 130

    def abertura(self, t): return suave((t - 8.0) / 3.0)

    def u_gota(self, t):
        if t < 11.0: return None
        return 0.88 * um((t - 11.0) / 22.0)

    def desenhar(self, tela, t, tg):
        # concreto da barragem por trás de tudo
        grad_v(tela, 0, 0, 300, PALCO_H, [CONC1, CONC1, CONC0, CONC0])
        for y in range(10, PALCO_H, 14): tela.ret(36, y, 264, 1, CONC0)
        for k in range(30):
            tela.px(40 + (k * 83) % 250, (k * 37) % 200, CONC2)
        # a represa à esquerda
        agua(tela, 0, 34, 6, PALCO_H, t, cores=(AGC, AGM, AGM, AGP, AGP))
        tela.ret(34, 0, 3, PALCO_H, PRETO); tela.ret(35, 0, 1, PALCO_H, CONC2)
        # o corte em volta do tubo
        linha_grossa(tela, P0[0] - 8, P0[1], P1[0], P1[1], ESP_TUBO + 12, CONC0)
        ab = self.abertura(t)
        D.tubo(tela, P0[0], P0[1], P1[0], P1[1], ESP_TUBO, t, fluxo=True, vel=34, aberto=ab, agua_on=ab > 0)
        # flanges do tubo
        for k in range(1, 9):
            a = no_tubo(k * .11, -ESP_TUBO / 2 - 2); b = no_tubo(k * .11, ESP_TUBO / 2 + 2)
            tela.linha(a[0], a[1], b[0], b[1], ACO0)
        # boca da tomada d'água + grade
        tela.ret(34, 50, 16, 33, PRETO)
        tela.ret(36, 52, 14, 29, AGM if ab > 0 else AGP)
        for x in range(36, 49, 3): tela.ret(x, 50, 1, 33, ACO3)
        tela.ret(36, 50, 13, 1, ACO3); tela.ret(36, 82, 13, 1, ACO3)
        # comporta (sobe de 50 para 10)
        gy = 50 - 40 * ab
        tela.ret(50, gy - 1, 10, 35, PRETO)
        grad_h(tela, 51, gy, 8, 33, [ACO3, ACO2, ACO1])
        for yy in range(int(gy) + 4, int(gy) + 32, 7): tela.ret(51, yy, 8, 1, ACO0)
        tela.ret(54, 0, 2, gy, ACO2)                        # haste
        # manômetros sobre o tubo
        for j, u in enumerate((.18, .5, .78)):
            mx, my = no_tubo(u, -ESP_TUBO / 2 - 14)
            prof = (no_tubo(u)[1] - 6) / 200.0
            tela.linha(mx, my + 6, no_tubo(u, -ESP_TUBO / 2)[0], no_tubo(u, -ESP_TUBO / 2)[1], ACO1)
            tela.disco(mx, my, 8, PRETO); tela.disco(mx, my, 7, CERAMICA)
            tela.anel(mx, my, 6, ACO3, .4)
            a = math.pi * (.8 + 1.4 * prof * ab) + math.sin(t * 9 + j) * .03
            tela.linha(mx, my, mx + math.cos(a) * 5, my + math.sin(a) * 5, VERMELHO)
            tela.px(mx, my, PRETO)
        if not VERTICAL or True:
            mx, my = no_tubo(.18, -ESP_TUBO / 2 - 14)
            if t > 18.4: self.rot(tela, 'MANÔMETRO', mx - 30, my - 22, BRANCO, alvo=(mx - 4, my - 7))
        # a gota
        u = self.u_gota(t)
        if u is None:
            gx, gy = 20 + math.sin(t * 1.4) * 2, 66 + math.sin(t * 2) * 2
        else:
            gx, gy = no_tubo(u, math.sin(t * 3) * 2)
            if u < .02: gx = lerp(20, gx, um((t - 11.0) / .6))
        gota(tela, gx, gy, 1.1, t)
        if t > 1.0:
            marca_gota(tela, gx, gy, t, 'A GOTA', lado=1 if gx < 200 else -1, dy=16)
        # rótulos
        if t > .5 and t < 12.4:
            self.rot(tela, "TOMADA D'ÁGUA", 62, 96, BRANCO, alvo=(44, 82))
        if 6.4 < t < 18.4:
            self.rot(tela, 'GRADE', 2, 92, ACO4, alvo=(38, 80))
            self.rot(tela, 'COMPORTA', 66, 20, ACO4, alvo=(58, gy + 6))
        if t > 12.4:
            p = no_tubo(.62, ESP_TUBO / 2 + 2)
            self.rot(tela, 'CONDUTO FORÇADO', 96, 168, BRANCO, alvo=(p[0], p[1]))
        # caixa da queda livre
        if 24.4 <= t < 30.4 and not VERTICAL:
            painel(tela, 150, 8, 140, 34, borda=AMARELO)
            tela.texto('QUEDA LIVRE DE 118 M', 220, 13, BRANCO, tam=9, centro=True)
            tela.texto('UNS 170 KM/H', 220, 24, AMARELO, tam=9, centro=True)
            tela.texto('(SEM ATRITO)', 220, 33, ACO3, tam=9, centro=True) if False else None
        # pressão
        prof = 0 if u is None else gy / 200.0
        nome = 'BAIXA' if prof < .45 else ('MÉDIA' if prof < .75 else 'ALTA')
        cor = AGC if prof < .45 else (AMARELO if prof < .75 else LARANJA)
        self.painel(tela, t, forma=0, tensao=0, estado=('PRESSÃO NA GOTA', nome if u is not None else 'NORMAL', cor))
        if not VERTICAL:
            tela.ret(PX0 + 90, 140, 70, 6, PRETO)
            tela.ret(PX0 + 91, 141, int(68 * um(prof)), 4, cor)

    def sons(self, fx):
        fx.put(fx.clique(900, .08), self.t0 + 8.0, .5)
        for k in range(10):
            fx.put(fx.clique(1800, .02), self.t0 + 8.0 + k * .3, .15)
        fx.put(fx.clique(700, .1), self.t0 + 11.0, .5)
        fx.put(fx.chiado(25.0, 150, 1100, ataque=2.0), self.t0 + 9.0, .14)


# ============================================================ 4 turbina
class Turbina(Cena):
    K, VX = 3, 150

    def preparar(self):
        self.C = D.Caracol(150, 104)
        # ângulo do rotor integrado (velocidade sobe quando as palhetas abrem)
        ts = np.arange(0, self.dur + .1, 1 / 60)
        om = np.array([self.omega(x) for x in ts])
        self.ts, self.ang = ts, np.cumsum(om) / 60

    def abertura(self, t): return .35 + .65 * suave((t - 14.5) / 3.0)
    def omega(self, t): return .5 + 1.6 * self.abertura(t)

    def ang_rotor(self, t):
        return float(np.interp(t, self.ts, self.ang))

    def pos_gota(self, t):
        C = self.C
        ytub = C.cy - (C.R0 + C.RI) / 2
        if t < 7.0:
            return (lerp(-6, C.cx, suave(t / 7.0)), ytub), 'NO CONDUTO', 1.0
        if t < 14.0:
            s = .62 * (t - 7.0) / 7.0
            r = C.RI + (C.R(s) - C.RI) * .5
            return C.p(s, r), 'NO CARACOL', 1.0
        if t < 20.6:
            u = (t - 14.0) / 6.6
            s = .62 + .16 * u
            r0 = C.RI + (C.R(.62) - C.RI) * .5
            return C.p(s, lerp(r0, C.RG - 2, suave(u))), 'NAS PALHETAS', 1.0
        if t < 27.6:
            u = (t - 20.6) / 7.0
            a0 = -math.pi / 2 + .78 * 2 * math.pi
            a = a0 + (self.ang_rotor(t) - self.ang_rotor(20.6))
            r = lerp(C.RG - 2, 16, suave(u))
            return (C.cx + math.cos(a) * r, C.cy + math.sin(a) * r), 'EMPURRA AS PÁS', 1.0
        u = um((t - 27.6) / 4.0)
        a0 = -math.pi / 2 + .78 * 2 * math.pi
        a = a0 + (self.ang_rotor(t) - self.ang_rotor(20.6))
        r = 16 * (1 - u)
        return (C.cx + math.cos(a) * r, C.cy + math.sin(a) * r), 'DESCE', 1.0 - .7 * u

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        grad_v(tela, 0, 0, 300, PALCO_H, [FUNDO3, FUNDO2, FUNDO2])
        for x in range(0, 300, 20): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(0, PALCO_H, 20): tela.ret(0, y, 300, 1, FUNDO2)
        C = self.C
        ab = self.abertura(t)
        C.desenhar(tela, t, abertura=ab, ang_rotor=self.ang_rotor(t), fluxo=.6 + ab)
        (gx, gy), onde, s = self.pos_gota(t)
        if t < 31.6:
            gota(tela, gx, gy, s * 1.1, t)
            if t > 27.6:
                halo(tela, C.cx, C.cy, 8 + 3 * math.sin(t * 6), AGC)
        if t > 1.0 and t < 31.6:
            lado = -1 if gx > 200 else 1
            marca_gota(tela, gx, gy, t, 'A GOTA', lado=lado, dy=-24 if gy > 40 else 12)
        if t > 28.0:
            # setinha: a água desce pelo meio, para fora do desenho
            k = int(t * 3) % 3
            for j in range(3):
                tela.disco(C.cx, C.cy, 2 + ((k + j) % 3) * 3, AGC if j == 0 else AGM)
            tela.disco(C.cx, C.cy, 2, PRETO)
            self.rot(tela, 'A ÁGUA DESCE', C.cx + 18, C.cy - 4, ESPUMA)
        # rótulos
        self.rot(tela, 'VISTA DE CIMA', 4, 196, ACO3)
        self.rot(tela, 'DO CONDUTO →', 4, 52, ACO3) if not VERTICAL else None
        if t > 7.2: self.rot(tela, 'CARACOL', 232, 20, ESPUMA, alvo=(221, 52))
        if t > 14.0: self.rot(tela, 'PALHETAS', 206, 184, ACO4, alvo=(188, 141))
        if t > 20.8: self.rot(tela, 'ROTOR', 72, 180, ACO4, alvo=(126, 128))
        self.painel(tela, t, forma=0 if t < 20.8 else 1, tensao=0, estado=('A GOTA', onde, LARANJA if t >= 20.8 else AGC))

    def sons(self, fx):
        fx.put(fx.chiado(34.0, 120, 900, ataque=2.0), self.t0 + 1.0, .14)
        # pás passando: cliques graves com a velocidade do rotor
        t = .5
        while t < self.dur - .5:
            fx.put(fx.clique(500, .03), self.t0 + t, .05)
            t += 2 * math.pi / 13 / max(.3, self.omega(t))
        for k in range(8):
            fx.put(fx.clique(1500, .02), self.t0 + 14.5 + k * .35, .12)


# ============================================================ saída (tubo de sucção)
CL_SUC = [(120, 122), (120, 148), (126, 164), (140, 176), (164, 182), (210, 183), (268, 183)]
HW_SUC = [10, 11, 13, 15, 17, 21, 26]


class Saida(Cena):
    K, VX = 3, 186

    def preparar(self):
        # tempo por comprimento: v ~ 1/área (área ~ largura²): mais largo, mais lento
        n = 400
        us = np.linspace(0, 1, n)
        pts = [ao_longo(CL_SUC, u) for u in us]
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        hw = np.interp(us, np.linspace(0, 1, len(HW_SUC)), HW_SUC)
        dt = (hw / hw[0]) ** 2 * (L / n)
        self.cum = np.concatenate([[0], np.cumsum(dt[1:])])
        self.cum /= self.cum[-1]
        self.us = us

    def lado_tubo(self):
        esq, dir_ = [], []
        n = 40
        for i in range(n + 1):
            u = i / n
            x, y = ao_longo(CL_SUC, u)
            x2, y2 = ao_longo(CL_SUC, min(1, u + .01))
            x1, y1 = ao_longo(CL_SUC, max(0, u - .01))
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            hw = float(np.interp(u, np.linspace(0, 1, len(HW_SUC)), HW_SUC))
            esq.append((x + nx * hw, y + ny * hw)); dir_.append((x - nx * hw, y - ny * hw))
        return esq, dir_

    def pos_gota(self, t):
        if t < 3.0:
            a = t * 4
            return (120 + math.cos(a) * 10, 112 + math.sin(a) * 3), 'NO ROTOR'
        if t < 15.0:
            v = (t - 3.0) / 12.0
            u = float(np.interp(v, self.cum, self.us))
            x, y = ao_longo(CL_SUC, u)
            return (x, y + math.sin(t * 4) * 1.5), 'DESACELERA'
        u = suave((t - 15.0) / 6.0)
        return (lerp(268, 284, u), lerp(183, 160, u) + math.sin(t * 2) * .8), 'DE VOLTA AO RIO'

    def desenhar(self, tela, t, tg):
        grad_v(tela, 0, 0, 300, PALCO_H, [CONC1, CONC0, CONC0])
        for y in range(6, PALCO_H, 14): tela.ret(0, y, 262, 1, CONC0)
        # céu e rio do lado de fora
        grad_v(tela, 262, 0, 40, 160, [CEU0, CEU1, CEU2])
        agua(tela, 258, 300, 158, PALCO_H, t, onda=.7)
        tela.ret(258, 0, 4, 158, PRETO); tela.ret(259, 0, 2, 157, CONC2)
        # gerador em cima
        caixa(tela, 64, 8, 112, 36, ACO1, ACO2, ACO0)
        for x in range(70, 172, 8): tela.ret(x, 14, 4, 24, COBRE1 if (x // 8) % 2 else COBRE0)
        tela.ret(64, 25, 112, 2, PRETO)
        # eixo girando
        tela.ret(115, 44, 11, 52, PRETO)
        grad_h(tela, 116, 44, 9, 52, [ACO3, ACO2, ACO1, ACO0])
        for k in range(6):
            y = 44 + ((k * 9 + t * 0) % 52)
            off = (t * 10 + k * 3) % 9
            tela.ret(116 + off, y, 1, 3, ACO4)
        # caracol em corte (dois círculos)
        for cx, cy, r in ((76, 106, 20), (164, 106, 14)):
            tela.disco(cx, cy, r + 3, PRETO); tela.disco(cx, cy, r + 2, ACO1); tela.disco(cx, cy, r, AGM)
            tela.disco(cx - r * .3, cy - r * .3, r * .5, AGC)
            for k in range(5):
                a = t * 3 + k * 1.25
                tela.px(cx + math.cos(a) * r * .7, cy + math.sin(a) * r * .7, ESPUMA)
        tela.ret(94, 96, 56, 26, PRETO); tela.ret(95, 97, 54, 24, AGM)
        # rotor de lado
        tela.ret(98, 92, 44, 5, PRETO); tela.ret(99, 93, 42, 3, ACO2)
        for k in range(7):
            x = 98 + ((k * 7 + t * 22) % 44)
            w = 3 if 104 < x < 136 else 2
            tela.ret(x, 97, w, 21, PRETO)
            tela.ret(x, 98, max(1, w - 1), 19, ACO3)
        tela.ret(100, 118, 40, 4, PRETO); tela.ret(101, 119, 38, 2, ACO2)
        # tubo de sucção
        esq, dir_ = self.lado_tubo()
        poligono(tela, esq + dir_[::-1], PRETO)
        e2, d2 = [], []
        for (ax, ay), (bx, by) in zip(esq, dir_):
            cx, cy = (ax + bx) / 2, (ay + by) / 2
            e2.append((ax + (cx - ax) * .12, ay + (cy - ay) * .12)); d2.append((bx + (cx - bx) * .12, by + (cy - by) * .12))
        poligono(tela, e2 + d2[::-1], AGM)
        for k in range(26):
            u = (k / 26 + t * .05) % 1.0
            v = float(np.interp(u, self.cum, self.us))
            x, y = ao_longo(CL_SUC, v)
            hw = float(np.interp(v, np.linspace(0, 1, len(HW_SUC)), HW_SUC))
            off = ((k * 7) % 9 - 4) / 5 * hw * .7
            tela.ret(x - 1, y + off, 3, 1, AGC if k % 3 else ESPUMA)
        # a gota
        (gx, gy), onde = self.pos_gota(t)
        gota(tela, gx, gy, 1.1, t)
        if t > .5:
            marca_gota(tela, gx, gy, t, 'A GOTA', lado=-1 if gx > 200 else 1, dy=-24 if gy > 150 else 16)
        # a energia sobe pelo eixo
        if t > 17.0:
            for k in range(3):
                y = 96 - ((t - 17.0) * 26 + k * 18) % 52
                faisca(tela, 120, y, t + k, 2)
            self.rot(tela, 'ENERGIA', 132, 58, AMARELO, alvo=(124, 70))
        # rótulos
        self.rot(tela, 'GERADOR', 96, 47, BRANCO) if t < 17.0 else None
        self.rot(tela, 'ROTOR', 52, 140, ACO4, alvo=(100, 114))
        if t > 6.2: self.rot(tela, 'TUBO DE SUCÇÃO', 158, 142, ESPUMA, alvo=(178, 166))
        if t > 12.0: self.rot(tela, 'RIO', 270, 196, ESPUMA)
        est = ('A GOTA', onde, AGC) if t < 18.0 else ('A ENERGIA', 'SOBE PELO EIXO', AMARELO)
        self.painel(tela, t, forma=1, tensao=0, estado=est)

    def sons(self, fx):
        fx.put(fx.chiado(14.0, 100, 600, ataque=1.0), self.t0 + .5, .12)
        fx.put(fx.chiado(6.0, 200, 1400, ataque=.5), self.t0 + 15.0, .08)
        for k in range(5):
            fx.put(fx.blip(76 + k * 2, .06), self.t0 + 17.5 + k * .5, .08)


# ============================================================ 5 gerador
class Gerador(Cena):
    K, VX = 4, 124
    CX, CY = 124, 104

    def preparar(self):
        ts = np.arange(0, self.dur + .1, 1 / 60)
        om = np.array([self.omega(x) for x in ts])
        self.ts, self.ang = ts, np.cumsum(om) / 60

    def omega(self, t): return .55 + 2.6 * suave((t - 29.0) / 3.0)

    def a(self, t): return float(np.interp(t, self.ts, self.ang))

    def emf(self, phi, t):
        return -math.sin(6 * (phi - self.a(t)))

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        grad_v(tela, 0, 0, 300, PALCO_H, [FUNDO2, FUNDO2, FUNDO3])
        for x in range(0, 300, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO)
        cx, cy = self.CX, self.CY
        on = t > 14.8 or True
        D.gerador_frente(tela, cx, cy, self.a(t), t, brilho_bobina=(lambda phi: self.emf(phi, t)) if t > 14.8 else None)
        top = -math.pi / 2
        e = self.emf(top, t)
        if t > 14.8:
            mira(tela, cx, cy - 68, t, 8)
            if not VERTICAL: self.rot(tela, 'ESTA BOBINA', 150, 4, AMARELO, alvo=(cx + 6, cy - 72))
        # rótulos
        if t > 7.6:
            self.rot(tela, 'ÍMÃS', 4, 96, ROSA, alvo=(cx - 52, cy + 2))
            self.rot(tela, 'BOBINAS', 4, 172, COBRE2, alvo=(cx - 46, cy + 46))
        if t < 29.0:
            tela.texto('CÂMERA LENTA', 4, 4, CIANO if int(t * 2) % 2 else ACO3, tam=9, contorno=PRETO) if not VERTICAL else None
        # o gráfico da corrente na bobina de cima
        if not VERTICAL:
            self.grafico(tela, t, 214, 30, 76, 66)
        else:
            self.grafico(tela, t, cx - 34, 186 - 18, 68, 18, mini=True)
        forma = 1 if t < 14.8 else 2
        v = V_GERADOR * suave((t - 15.0) / 3.0)
        if t < 22.0: est = ('O ROTOR', 'GIRA', LARANJA) if t < 14.8 else ('NA BOBINA', 'CORRENTE!', AMARELO)
        elif t < 29.0: est = ('CORRENTE', 'ALTERNADA', AMARELO)
        else: est = ('FREQUÊNCIA', '60 HZ', AMARELO)
        self.painel(tela, t, forma=forma, tensao=v, estado=est)

    def grafico(self, tela, t, x, y, w, h, mini=False):
        painel(tela, x - 2, y - 2, w + 4, h + 4, borda=TRACO, fundo=PRETO)
        ym = y + h // 2
        for xx in range(x, x + w, 3): tela.px(xx, ym, FUNDO3)
        if not mini:
            tela.texto('CORRENTE', x, y - 14, ACO3, tam=9, contorno=PRETO)
            tela.texto('VAI', x + w + 0, y + 2, AMARELO, tam=9, centro='d')
            tela.texto('VOLTA', x + w, y + h - 9, CIANO, tam=9, centro='d')
        if t < 14.8:
            return
        rapido = t > 29.0
        jan = 6.0
        pts = []
        for i in range(w):
            if rapido:
                ph = (i / w) * 8 * 2 * math.pi - t * 12
                v = math.sin(ph) * um((t - 29.0) / 2.0) + self.emf(-math.pi / 2, t - (1 - i / w) * jan) * (1 - um((t - 29.0) / 2.0))
            else:
                tt = t - (1 - i / w) * jan
                v = self.emf(-math.pi / 2, tt) if tt > 14.8 else 0.0
            pts.append((x + i, ym - v * (h / 2 - 3)))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            c = AMARELO if (ay + by) / 2 < ym else CIANO
            tela.linha(ax, ay, bx, by, c)
        tela.disco(pts[-1][0], pts[-1][1], 1.5, BRANCO)
        if rapido and not mini:
            tela.texto('60 VEZES', x + w // 2, y + h + 6, AMARELO, tam=9, centro=True, contorno=PRETO)
            tela.texto('POR SEGUNDO', x + w // 2, y + h + 16, AMARELO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        # um toque a cada polo que passa pela bobina de cima (som do que se vê)
        t = 15.0
        last = None
        while t < 29.0:
            e = self.emf(-math.pi / 2, t)
            s = e > 0
            if last is not None and s != last:
                fx.put(fx.blip(69 if s else 64, .06), self.t0 + t, .1)
            last = s
            t += 1 / 60
        fx.put(fx.chiado(7.0, 60, 260, ataque=1.0), self.t0 + 29.0, .25)


# ============================================================ Itaipu (escala)
class Itaipu(Cena):
    K, VX = 4, 150
    N = 20

    def ligadas(self, t): return int(min(self.N, max(0, (t - 7.8) / 5.6 * self.N + .999))) if t > 7.8 else 0

    def desenhar(self, tela, t, tg):
        ceu(tela, 60, 0, 300, t, estrelas=True, cores=(CEU0, CEU1, CEU2))
        morro(tela, [(x, 34 - 6 * math.sin(x * .05)) for x in range(-4, 304, 8)], FUNDO3, TRACO)
        agua(tela, 0, 300, 38, 48, t, onda=.4, brilho=False)
        # crista e face da barragem
        tela.ret(0, 44, 300, 4, PRETO); tela.ret(0, 45, 300, 2, CONC2)
        grad_v(tela, 0, 48, 300, 104, [CONC2, CONC1, CONC1, CONC0])
        n_on = self.ligadas(t)
        x0, passo = 8, 14
        dest = 9
        for i in range(self.N):
            x = x0 + i * passo
            tela.ret(x - 1, 48, 1, 104, CONC0)
            # conduto descendo pela face
            tela.ret(x + 3, 56, 7, 96, PRETO)
            grad_h(tela, x + 4, 56, 5, 96, [ACO3, ACO2, ACO1])
            if i < n_on:
                for k in range(3):
                    yy = 58 + ((t * 40 + k * 31 + i * 7) % 90)
                    tela.ret(x + 5, yy, 2, 3, AGC)
        # casa de força comprida
        caixa(tela, 4, 150, 284, 30, CONC1, CONC2, CONC0)
        tela.ret(2, 146, 288, 4, PRETO); tela.ret(3, 147, 286, 2, ACO2)
        brasil = t > 29.0
        for i in range(self.N):
            x = x0 + i * passo
            on = i < n_on
            if brasil:
                c = VERDE if i < 10 else CIANO
            else:
                c = CHAMA0 if on else FUNDO3
            tela.ret(x + 2, 156, 9, 8, PRETO); tela.ret(x + 3, 157, 7, 6, c if on else FUNDO3)
            if on: tela.px(x + 4, 158, BRANCO)
            tela.texto(str(i + 1), x + 6, 168, ACO1 if not on else PRETO, tam=9, centro=True) if False else None
        # canal de fuga com espuma das unidades ligadas
        agua(tela, 0, 300, 182, PALCO_H, t, onda=.5)
        for i in range(n_on):
            x = x0 + i * passo + 6
            for k in range(3):
                tela.px(x - 3 + (k * 3 + int(t * 9)) % 7, 184 + k * 2, ESPUMA)
        # destaque: uma unidade e os 700 m³/s
        if 14.8 <= t < 22.0:
            x = x0 + dest * passo + 6
            mira(tela, x, 100, t, 12)
            for k in range(5):
                yy = 58 + ((t * 70 + k * 18) % 90)
                tela.ret(x - 1, yy, 2, 4, ESPUMA)
            self.rot(tela, '700 M³ POR SEGUNDO', x - 54, 14, AMARELO, alvo=(x, 86))
        if 22.0 <= t < 29.0 and not VERTICAL:
            painel(tela, 22, 62, 252, 70, borda=AMARELO)
            tela.texto('VAZÃO × QUEDA × GRAVIDADE', 148, 70, ACO3, tam=9, centro=True)
            tela.texto('700 M³/S × 118 M × 9,8', 148, 84, BRANCO, tam=17, centro=True)
            tela.texto('= UNS 810 MW NA ÁGUA', 148, 104, AMARELO, tam=17, centro=True)
            if t > 25.0: tela.texto('A UNIDADE ENTREGA 700 MW', 148, 121, VERDE, tam=9, centro=True)
        if brasil:
            self.rot(tela, '10 × 60 HZ: BRASIL', 78, 194, VERDE, centro=True)
            self.rot(tela, '10 × 50 HZ: PARAGUAI', 214, 194, CIANO, centro=True)
        if t < 7.6:
            self.rot(tela, 'RIO PARANÁ', 8, 26, ESPUMA)
        mw = n_on * 700
        if VERTICAL:
            D.selo_vertical(tela, 0, self.VX, f"ITAIPU: {n_on} UNIDADES, {I.milhar(mw)} MW")
            return
        est = None
        if 14.8 <= t < 22.0: est = ('ÁGUA POR TURBINA', '700 M³/S', AGC)
        elif 22.0 <= t < 29.0: est = ('FORÇA DA ÁGUA', 'UNS 810 MW', AMARELO)
        elif t >= 29.0: est = ('FREQUÊNCIA', '60 HZ E 50 HZ', VERDE)
        D.painel_jornada(tela, 4, t, cab=('TAMANHO REAL', 'ITAIPU', CIANO), estado=est,
                         linhas=[('UNIDADES GERADORAS', f'{n_on} DE 20', BRANCO), ('POTÊNCIA', f'{I.milhar(mw)} MW', AMARELO)],
                         rodape='EXEMPLO DE ESCALA')

    def sons(self, fx):
        for i in range(self.N):
            tt = 7.8 + i / self.N * 5.6
            fx.put(fx.blip(60 + (i % 8) * 2, .07), self.t0 + tt, .1)
        fx.put(fx.chiado(20.0, 100, 700, ataque=3.0), self.t0 + 8.0, .1)


# ============================================================ 6 transformador elevador
class Elevador(Cena):
    K, VX = 5, 150

    def tensao(self, t):
        return V_GERADOR + (V_LINHA - V_GERADOR) * suave((t - 22.5) / 3.5)

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        # tanque em corte (óleo escuro em volta)
        dither(tela, 44, 14, 216, 184, FUNDO2, OLEO0)
        tela.ret_vazado(43, 13, 218, 186, ACO2)
        for x in range(44, 260, 6): tela.px(x, 13, PRETO)
        ac = math.sin(2 * math.pi * .5 * t)            # corrente alternada (devagar, para ver)
        D.nucleo(tela, 70, 28, 160, 150, perna=30, t=t, fluxo=ac if t > 14.8 else 0.0)
        # fios de entrada (grossos) e saída (finos)
        corr_p = 1.0
        corr_s = .25 if t > 22.0 else .25
        for y in (40, 166):
            tela.ret(0, y - 2, 66, 5, PRETO); tela.ret(0, y - 1, 66, 3, COBRE1); tela.ret(0, y - 1, 66, 1, COBRE2)
        for y in (40, 166):
            tela.ret(234, y - 1, 70, 3, PRETO); tela.ret(234, y, 70, 1, COBRE2)
        tela.ret(64, 40, 4, 12, COBRE1); tela.ret(64, 154, 4, 12, COBRE1)
        tela.ret(232, 40, 2, 8, COBRE2); tela.ret(232, 158, 2, 8, COBRE2)
        D.bobina(tela, 85, 52, 154, 42, 6, t, corrente=corr_p if t > 14.8 else .6, fase=0, esp=9)
        D.bobina(tela, 215, 48, 158, 34, 22, t, corrente=corr_s if t > 14.8 else 0, fase=math.pi, esp=3)
        # pontos de corrente nos fios (grandes na entrada, pequenos na saída)
        for k in range(6):
            x = (k * 11 + t * 30 * math.copysign(1, ac) ) % 66
            tela.disco(x, 40, 1.8, AMARELO); tela.disco(66 - x, 166, 1.8, AMARELO)
            if t > 14.8:
                x2 = 234 + (k * 11 + t * 30 * math.copysign(1, ac)) % 66
                tela.px(x2, 40, AMARELO); tela.px(300 - (x2 - 234), 166, AMARELO)
        # rótulos
        if not VERTICAL:
            self.rot(tela, 'DO GERADOR', 2, 26, ACO3)
            tela.texto('13,8 KV', 2, 172, AMARELO, tam=9, contorno=PRETO)
            self.rot(tela, 'PARA A LINHA', 232, 26, ACO3)
            tela.texto(fmt_v(self.tensao(t)) if t > 22.0 else '?', 238, 172, AMARELO, tam=9, contorno=PRETO)
        if t > 7.6:
            self.rot(tela, 'NÚCLEO', 150, 8, ACO4, alvo=(150, 30), centro=True)
            self.rot(tela, 'POUCAS VOLTAS', 85, 184, COBRE2, centro=True)
            self.rot(tela, 'MUITAS VOLTAS', 215, 184, COBRE2, centro=True)
        if 14.8 <= t:
            self.rot(tela, 'FLUXO MAGNÉTICO', 150, 92, ROXO, centro=True)
            self.rot(tela, 'VAI E VOLTA', 150, 104, ACO3, centro=True)
        v = self.tensao(t)
        est = ('CORRENTE', 'ALTA', LARANJA) if t < 24.0 else ('CORRENTE', 'BAIXA', VERDE)
        self.painel(tela, t, forma=2, tensao=v, estado=est)

    def sons(self, fx):
        n = int(self.dur / .5)
        for k in range(n):
            fx.put(fx.blip(43, .25), self.t0 + .3 + k * .5, .05)
        fx.put(fx.chiado(3.5, 400, 2500, ataque=1.0), self.t0 + 22.5, .08)


# ============================================================ 7 transmissão
class Linhas(Cena):
    K, VX = 6, 146

    def desenhar(self, tela, t, tg):
        if t < 7.0:
            self.paisagem(tela, t)
            est = ('A ENERGIA', 'VIAJANDO', CIANO)
        elif t < 13.8:
            self.fio_zoom(tela, t - 7.0)
            est = ('O FIO', 'ESQUENTA', LARANJA)
        elif t < 27.4:
            self.quadrados(tela, t)
            est = ('PERDA', 'R × CORRENTE²', LARANJA)
        else:
            self.comparar(tela, t)
            est = ('1.000 MW, 160 KM', 'MAIS TENSÃO, MENOS PERDA', VERDE)
        self.painel(tela, t, forma=2, tensao=V_LINHA, estado=est)

    # ----- 0..7: as torres passando
    def paisagem(self, tela, t):
        ceu(tela, 150, 0, 300, t, estrelas=True, cores=(CEU0, CEU0, CEU1, CEU2))
        sc = t * 36
        morro(tela, [(x, 128 - 16 * math.sin((x + sc * .3) * .025) - 6 * math.sin((x + sc * .3) * .08)) for x in range(-4, 304, 6)], FUNDO3, TRACO)
        morro(tela, [(x, 166 - 4 * math.sin((x + sc) * .05)) for x in range(-4, 304, 6)], GRAMA0, GRAMA1)
        grad_v(tela, 0, 172, 300, PALCO_H - 172, [GRAMA0, GRAMA0, TERRA0])
        passo = 150
        torres = []
        for k in range(-1, 4):
            x = 30 + k * passo - (sc % passo)
            torres.append((x, D.torre(tela, x, 176, 112)))
        for (xa, pa), (xb, pb) in zip(torres, torres[1:]):
            for j in range(3):
                a, b = pa[j], pb[j]
                D.catenaria(tela, a[0], a[1] + 2, b[0], b[1] + 2, 16, ACO3)
                D.isolador(tela, a[0], a[1] - 3, 3)
        # energia correndo nos fios
        for j in range(3):
            for k in range(3):
                X = (k * 110 + j * 37 + t * 150) % 330 - 15
                for (xa, pa), (xb, pb) in zip(torres, torres[1:]):
                    if xa <= X < xb:
                        a, b = pa[j], pb[j]
                        u = (X - a[0]) / max(1, b[0] - a[0])
                        x, y = D.ponto_cat(a[0], a[1] + 2, b[0], b[1] + 2, 16, um(u))
                        faisca(tela, x, y, t + k, 1.6)
        self.rot(tela, 'LINHA DE TRANSMISSÃO', 8, 186, CIANO)

    # ----- 7..13,8: o fio esquentando
    def fio_zoom(self, tela, u):
        grade(tela, 0, 300)
        alta = (int(u / 3.4) % 2) == 1
        cor_val = 1.0 if alta else .3
        y = 100
        x0, x1 = (self.VX - 86, self.VX + 86) if VERTICAL else (10, 290)
        # calor subindo
        if alta:
            for k in range(14):
                xx = x0 + 8 + (k * 19) % (x1 - x0 - 16)
                ph = (u * 1.4 + k * .3) % 1.0
                yy = y - 14 - ph * 50
                for j in range(5):
                    tela.px(xx + math.sin(yy * .3 + j + k) * 2, yy - j * 2, CHAMA1 if ph < .5 else BRASA)
            halo(tela, (x0 + x1) / 2, y, 30, BRASA)
            for k in range(0, x1 - x0, 6): halo(tela, x0 + k, y, 10, CHAMA2, fase=k)
        # o cabo (alumínio em fios trançados)
        tela.ret(x0, y - 10, x1 - x0, 21, PRETO)
        for k in range(x0, x1, 4):
            for j in range(4):
                c = (CHAMA1 if j == 1 else LARANJA) if alta else (ACO3 if j == 1 else ACO2)
                tela.ret(k + j, y - 9 + j * 5, 3, 4, c)
        tela.ret(x0, y - 9, x1 - x0, 1, CHAMA0 if alta else ACO4)
        # pontos da corrente
        n = 16 if alta else 5
        for k in range(n):
            xx = x0 + ((k * (x1 - x0) / n + u * 60) % (x1 - x0))
            tela.disco(xx, y + ((k * 7) % 11) - 5, 1.6, AMARELO)
        txt = 'CORRENTE ALTA' if alta else 'CORRENTE BAIXA'
        tela.texto(txt, (x0 + x1) // 2, 140, LARANJA if alta else AGC, tam=17, centro=True, contorno=PRETO)
        tela.texto('O FIO ESQUENTA' if alta else 'QUASE NÃO ESQUENTA', (x0 + x1) // 2, 162, ACO3, tam=9, centro=True, contorno=PRETO)
        tela.texto('UM PEDAÇO DO CABO, DE PERTO', (x0 + x1) // 2, 20, ACO3, tam=9, centro=True, contorno=PRETO)

    # ----- 13,8..27,4: corrente 2x = perda 4x
    def cartao(self, tela, x, y, w, h, tens, corr, perda, t, destaque):
        painel(tela, x, y, w, h, borda=AMARELO if destaque else TRACO, fundo=PRETO)
        cx = x + w // 2
        if tens: tela.texto(tens, cx, y + 5, CIANO, tam=9, centro=True)
        tela.texto(f'CORRENTE {corr}', cx, y + 16, AMARELO, tam=9, centro=True)
        yf = y + 32
        tela.ret(x + 6, yf - 2, w - 12, 5, PRETO); tela.ret(x + 6, yf - 1, w - 12, 3, ACO2)
        for k in range(corr * 4):
            xx = x + 6 + ((k * (w - 12) / (corr * 4) + t * 40) % (w - 12))
            tela.disco(xx, yf, 1.5, AMARELO)
        # blocos de calor: corrente² quadradinhos
        lado = 14
        n = corr
        bx = cx - (n * (lado + 2)) // 2
        by = yf + 10
        for i in range(n):
            for j in range(n):
                xx, yy = bx + i * (lado + 2), by + j * (lado + 2)
                tela.ret(xx - 1, yy - 1, lado + 2, lado + 2, PRETO)
                fl = int(t * 6 + i * 2 + j) % 3
                tela.ret(xx, yy, lado, lado, (CHAMA2, CHAMA1, LARANJA)[fl])
                tela.ret(xx, yy, lado, 1, CHAMA0)
        tela.texto(f'PERDA {perda}', cx, y + h - 13, LARANJA, tam=9, centro=True)

    def quadrados(self, tela, t):
        grade(tela, 0, 300)
        segunda = t >= 20.6
        if VERTICAL:
            xa, xb, ya, yb, w, h = self.VX - 84, self.VX - 84, 18, 112, 168, 90
        else:
            xa, xb, ya, yb, w, h = 10, 152, 26, 26, 134, 120
        if not segunda:
            self.cartao(tela, xa, ya, w, h, None, 1, '1', t, False)
            self.cartao(tela, xb, yb, w, h, None, 2, '4 VEZES', t, True)
            if not VERTICAL: tela.texto('MESMO FIO, MESMA DISTÂNCIA', 150, 160, ACO3, tam=9, centro=True, contorno=PRETO)
        else:
            self.cartao(tela, xa, ya, w, h, 'TENSÃO 1', 2, '4', t, False)
            self.cartao(tela, xb, yb, w, h, 'TENSÃO 2', 1, '4 VEZES MENOR', t, True)
            if not VERTICAL: tela.texto('A MESMA ENERGIA PASSANDO', 150, 160, ACO3, tam=9, centro=True, contorno=PRETO)
        if not VERTICAL: tela.texto('PERDA = RESISTÊNCIA × CORRENTE²', 150, 8, ACO3, tam=9, centro=True, contorno=PRETO)

    # ----- 27,4..40,8: 345 kV x 765 kV
    def comparar(self, tela, t):
        grade(tela, 0, 300)
        if VERTICAL: x0, wmax = self.VX - 84, 168
        else: x0, wmax = 12, 270
        esc = (wmax - 4) / 4.4
        tela.texto('1.000 MW POR 160 KM', x0 + wmax // 2, 10, BRANCO, tam=9, centro=True, contorno=PRETO)
        for j, (rot, pmin, pmax, cor, aparece) in enumerate((('345 KV', 4.2, 4.2, LARANJA, 27.4), ('765 KV', .5, 1.1, VERDE, 34.2))):
            if t < aparece: continue
            y = 34 + j * 76
            u = ease((t - aparece) / 1.5)
            tela.texto(rot, x0, y, cor, tam=17, contorno=PRETO)
            # o fio: quente ou frio
            fy = y + 24
            tela.ret(x0, fy - 3, wmax, 7, PRETO)
            tela.ret(x0, fy - 2, wmax, 5, BRASA if j == 0 else ACO2)
            tela.ret(x0, fy - 2, wmax, 1, CHAMA1 if j == 0 else ACO4)
            if j == 0:
                for k in range(0, wmax, 10):
                    ph = (t * 1.2 + k * .07) % 1.0
                    tela.px(x0 + k + math.sin(t * 3 + k) * 2, fy - 6 - ph * 14, CHAMA1)
            # barra da perda
            by = fy + 12
            tela.texto('PERDA', x0, by, ACO3, tam=9)
            bx = x0 + 36
            tela.ret(bx, by, int(esc * pmax * u) + 2, 9, PRETO)
            tela.ret(bx + 1, by + 1, int(esc * pmin * u), 7, cor)
            if pmax > pmin:
                for k in range(int(esc * pmin * u), int(esc * pmax * u)):
                    if (k // 2) % 2 == 0: tela.ret(bx + 1 + k, by + 1, 1, 7, cor)
            txt = '4,2%' if j == 0 else '0,5% A 1,1%'
            tela.texto(txt, min(bx + int(esc * pmax * u) + 6, x0 + wmax - tela.largura_texto(txt, 17)), by + 12, cor, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(7.0, 3000, 8000, ataque=1.0), self.t0, .05)
        for k in range(2):
            fx.put(fx.chiado(3.0, 200, 3000, ataque=.3), self.t0 + 7.0 + 3.4 + k * 6.8, .08)
        fx.put(fx.sino(72, .8), self.t0 + 13.9, .2)
        fx.put(fx.sino(79, .8), self.t0 + 20.7, .2)
        fx.put(fx.blip(60, .2), self.t0 + 27.5, .15)
        fx.put(fx.blip(72, .2), self.t0 + 34.3, .15)


# ============================================================ 8 subestação
TRAJ_SUB = [(0, 64), (43, 66), (84, 72), (106, 112), (118, 120), (132, 112), (160, 96), (172, 130), (182, 134),
            (192, 130), (228, 82), (268, 82), (300, 82)]
# instantes de passagem por cada ponto da trajetória
T_SUB = [1.0, 3.0, 5.0, 8.0, 9.0, 12.5, 14.5, 16.5, 17.5, 19.5, 22.5, 25.0, 27.0]


class Subestacao(Cena):
    K, VX = 7, 150

    def energia(self, t):
        if t <= T_SUB[0]: return TRAJ_SUB[0]
        for i in range(len(T_SUB) - 1):
            if t < T_SUB[i + 1]:
                u = (t - T_SUB[i]) / (T_SUB[i + 1] - T_SUB[i])
                a, b = TRAJ_SUB[i], TRAJ_SUB[i + 1]
                return lerp(a[0], b[0], u), lerp(a[1], b[1], u)
        return TRAJ_SUB[-1]

    def tensao(self, t):
        if t < 10.0: return V_LINHA
        if t < 12.5: return V_LINHA + (V_SUB - V_LINHA) * suave((t - 10.0) / 2.5)
        if t < 17.5: return V_SUB
        if t < 19.5: return V_SUB + (V_DIST - V_SUB) * suave((t - 17.5) / 2.0)
        return V_DIST

    def desenhar(self, tela, t, tg):
        ceu(tela, 172, 0, 300, t, estrelas=True, cores=(CEU0, CEU0, CEU1, CEU2))
        # cidade ao fundo
        for k in range(12):
            x = 200 + k * 9; h = 20 + (k * 37) % 40
            tela.ret(x, 170 - h, 8, h, FUNDO2)
            for j in range(0, h - 4, 5):
                if (k * 7 + j) % 3: tela.px(x + 2 + (j % 2) * 3, 170 - h + 3 + j, CHAMA1 if (k + j) % 4 else FUNDO3)
        # chão de brita
        dither(tela, 0, 170, 300, PALCO_H - 170, ACO0, FUNDO3)
        tela.ret(0, 170, 300, 1, ACO1)
        # cerca
        for x in range(60, 210, 10):
            tela.ret(x, 154, 1, 16, ACO1)
        tela.ret(60, 156, 150, 1, ACO1); tela.ret(60, 163, 150, 1, ACO1)
        # torre que chega
        D.torre(tela, 24, 172, 120)
        # pórticos
        for x, yt in ((84, 70), (160, 94)):
            tela.ret(x - 12, yt, 3, 172 - yt, PRETO); tela.ret(x - 11, yt, 1, 172 - yt, ACO2)
            tela.ret(x + 10, yt, 3, 172 - yt, PRETO); tela.ret(x + 11, yt, 1, 172 - yt, ACO2)
            tela.ret(x - 12, yt, 25, 3, PRETO); tela.ret(x - 11, yt + 1, 23, 1, ACO2)
        # transformadores
        D.transformador_tanque(tela, 100, 170, 40, 40, t)
        D.transformador_tanque(tela, 170, 170, 26, 28, t, alta=False)
        # fios
        for j in range(3):
            D.catenaria(tela, 5 + j * 19, 64 + (j % 2) * 10, 76 + j * 8, 72, 6, ACO3)
        for dx in (-4, 0, 4):
            tela.linha(84 + dx, 72, 106 + dx, 110, ACO3)
            D.catenaria(tela, 132 + dx, 112, 160 + dx, 96, 4, ACO3)
            tela.linha(160 + dx, 96, 176 + dx, 128, ACO3)
        # postes de distribuição até a cidade
        for x in (228, 268):
            tela.ret(x - 2, 82, 5, 90, PRETO); tela.ret(x - 1, 82, 3, 90, CONC1)
            tela.ret(x - 10, 84, 21, 3, PRETO); tela.ret(x - 9, 85, 19, 1, TERRA1)
        for dy in (-6, 0, 6):
            D.catenaria(tela, 192, 130, 228 + dy, 84, 4, ACO2)
            D.catenaria(tela, 228 + dy, 84, 268 + dy, 84, 5, ACO2)
            D.catenaria(tela, 268 + dy, 84, 300, 86, 4, ACO2)
        # brilho do transformador trabalhando
        if 9.0 <= t < 12.5: halo(tela, 120, 150, 26, AMARELO)
        if 16.5 <= t < 19.5: halo(tela, 183, 156, 18, AMARELO)
        if t >= 1.0:
            x, y = self.energia(t)
            faisca(tela, x, y, t, 2.6)
        # rótulos
        if t > 7.6:
            self.rot(tela, '500 → 138 KV', 82, 176, AMARELO)
            if t > 14.8: self.rot(tela, '138 → 13,8 KV', 150, 188, AMARELO)
        if not VERTICAL:
            self.rot(tela, 'SUBESTAÇÃO', 96, 22, VERDE)
            if t > 22.0: self.rot(tela, 'CIDADE', 236, 110, CHAMA1)
        self.painel(tela, t, forma=2, tensao=self.tensao(t), estado=('A TENSÃO', 'BAIXANDO' if t < 20 else 'DISTRIBUIÇÃO', VERDE))

    def sons(self, fx):
        for k in range(int(self.dur / .5)):
            fx.put(fx.blip(43, .2), self.t0 + .2 + k * .5, .03)
        fx.put(fx.chiado(3.0, 300, 2000), self.t0 + 9.5, .08)
        fx.put(fx.chiado(2.0, 300, 2000), self.t0 + 17.0, .08)
        fx.put(fx.sino(74, .8), self.t0 + 12.5, .15)
        fx.put(fx.sino(79, .8), self.t0 + 19.5, .15)


# ============================================================ 9 sua casa
POSTE_X = 64
CASA = (150, 292)
CAMINHO_CASA = [  # (t, x, y)
    (0.6, -4, 26), (5.0, 46, 26), (6.2, 64, 26), (7.2, 78, 50),
    (12.6, 78, 74), (13.6, 78, 86), (15.8, 156, 94), (16.8, 156, 110), (17.6, 146, 120),
    (20.4, 152, 132), (21.4, 162, 132), (22.6, 162, 152), (25.0, 270, 152), (26.0, 270, 158),
]
CAMINHO_LUZ = [(34.8, 176, 140), (35.8, 176, 100), (37.0, 226, 100), (37.6, 226, 110)]


def no_caminho(cam, t):
    if t <= cam[0][0]: return cam[0][1], cam[0][2]
    for (ta, xa, ya), (tb, xb, yb) in zip(cam, cam[1:]):
        if t < tb:
            u = (t - ta) / (tb - ta)
            return lerp(xa, xb, u), lerp(ya, yb, u)
    return cam[-1][1], cam[-1][2]


class Casa(Cena):
    K, VX = 8, 202
    LUZ_T = 37.6

    def tensao(self, t):
        if t < 8.5: return V_DIST
        if t < 12.0: return V_DIST + (V_CASA - V_DIST) * suave((t - 8.5) / 3.5)
        return V_CASA

    def desenhar(self, tela, t, tg):
        acesa = 1.0 if t >= self.LUZ_T else 0.0
        ceu(tela, 180, 0, 300, t, estrelas=True, cores=(CEU0, CEU0, CEU0, CEU1))
        tela.disco(30, 150, 0, FUNDO)
        if t > 40.8:
            nuvem(tela, 40, 30, 40, chuva=True)
            chuva(tela, 20, 70, 40, 176, t, n=10, vel=120)
        # rua e calçada
        dither(tela, 0, 182, 300, PALCO_H - 182, ACO0, FUNDO3)
        tela.ret(0, 176, 300, 6, CONC0); tela.ret(0, 176, 300, 1, CONC1)
        for x in range(10, 140, 28): tela.ret(x, 194, 12, 2, ACO2)
        # casa (em corte)
        x0, x1 = CASA
        poligono(tela, [(x0 - 8, 96), (226, 48), (x1 + 20, 96)], PRETO)
        poligono(tela, [(x0 - 5, 95), (226, 50), (x1 + 18, 95)], VERMELHO)
        for k in range(6):
            yy = 58 + k * 7
            tela.linha(226 - (yy - 50) * 1.6, yy, 226 + (yy - 50) * 1.6, yy, BRASA)
        tela.ret(x0, 96, x1 - x0 + 8, 4, PRETO)
        # parede e cômodo
        if acesa:
            grad_v(tela, x0 + 6, 100, x1 - x0, 76, [LATAO, OLEO1, OLEO1, OLEO0])
        else:
            dither(tela, x0 + 6, 100, x1 - x0, 76, FUNDO2, FUNDO)
        tela.ret(x0, 96, 6, 82, PRETO); tela.ret(x0 + 1, 97, 4, 80, CERAMICA)
        tela.ret(x0 + 1, 97, 1, 80, BRANCO)
        tela.ret(x0, 174, x1 - x0 + 8, 3, TERRA0)
        # janela e quadro na parede
        caixa(tela, 244, 112, 30, 24, CEU0 if not acesa else CEU1, ACO2, ACO0)
        tela.ret(258, 112, 2, 24, ACO2)
        # fiação dentro da parede (tracejada)
        for (ax, ay), (bx, by) in (((152, 132), (162, 132)), ((162, 132), (162, 152)), ((162, 152), (270, 152)),
                                   ((176, 140), (176, 100)), ((176, 100), (226, 100))):
            n = int(max(abs(bx - ax), abs(by - ay)))
            for i in range(0, n, 3):
                u = i / max(1, n)
                tela.px(ax + (bx - ax) * u, ay + (by - ay) * u, COBRE1)
        # medidor do lado de fora, mastro e ramal
        D.medidor(tela, 132, 112, t, ligado=t > 17.0)
        tela.ret(155, 86, 3, 26, PRETO); tela.ret(156, 86, 1, 26, ACO2)
        D.tomada(tela, 270, 158, 1, t, viva=1.0 if t > 25.0 else 0.0) if False else self.tomada_parede(tela, t)
        D.interruptor(tela, 176, 140, t >= 35.5)
        D.lampada(tela, 226, 112, acesa, t, fio_ate=100)
        # poste e transformador
        topo = D.poste(tela, POSTE_X, 182, 160, t)
        for j, dx in enumerate((-18, 0, 18)):
            tela.linha(-4, 24 + j * 0, POSTE_X + dx, 24, ACO3)
        tela.linha(POSTE_X - 18, 24, 72, 46, ACO3); tela.linha(POSTE_X + 18, 24, 81, 46, ACO3)
        D.catenaria(tela, POSTE_X + 10, 86, 156, 88, 8, ACO2)
        if 6.8 <= t < 12.6:
            halo(tela, 78, 62, 18 + 2 * math.sin(t * 6), AMARELO)
        # a energia
        if t < 26.0:
            x, y = no_caminho(CAMINHO_CASA, t)
            if not (7.2 <= t < 12.6): faisca(tela, x, y, t, 2.2)
        if 34.8 <= t < self.LUZ_T:
            x, y = no_caminho(CAMINHO_LUZ, t)
            faisca(tela, x, y, t, 2.2)
        # zoom da tomada
        if 27.2 <= t < 34.0:
            self.zoom_tomada(tela, t)
        # rótulos
        if t < 13.6:
            self.rot(tela, 'TRANSFORMADOR', 88, 54, AMARELO, alvo=(86, 62))
        if t < 6.8 and not VERTICAL:
            self.rot(tela, '13,8 KV', 4, 32, ACO3)
        if 13.6 <= t < 27.2:
            self.rot(tela, 'MEDIDOR', 116, 136, BRANCO, alvo=(132, 124)) if not VERTICAL else self.rot(tela, 'MEDIDOR', 114, 136, BRANCO)
        if 20.4 <= t < 27.2:
            self.rot(tela, 'TOMADA', 236, 160, BRANCO, alvo=(262, 158))
        if t >= 34.0:
            self.rot(tela, 'INTERRUPTOR', 158, 156, ACO4, alvo=(176, 146))
        est = ('A ENERGIA', 'NO POSTE', AMARELO)
        if t >= 13.6: est = ('A ENERGIA', 'NO MEDIDOR', AMARELO)
        if t >= 20.4: est = ('A ENERGIA', 'NA TOMADA', AMARELO)
        if t >= 27.2: est = ('NA TOMADA', '127 OU 220 V', AMARELO)
        if t >= self.LUZ_T: est = ('A LÂMPADA', 'ACESA!', CHAMA0)
        self.painel(tela, t, forma=2, tensao=self.tensao(t), estado=est, tudo=t >= 40.8)

    def tomada_parede(self, tela, t):
        x, y = 270, 158
        caixa(tela, x - 5, y - 7, 11, 14, CERAMICA, BRANCO, ACO3)
        tela.disco(x, y, 3, ACO3)
        tela.px(x - 1, y + 1, PRETO); tela.px(x + 1, y + 1, PRETO); tela.px(x, y - 1, PRETO)
        if 25.0 <= t and int(t * 6) % 2: halo(tela, x, y, 7, AMARELO)

    def zoom_tomada(self, tela, t):
        cx = self.VX if VERTICAL else 214
        x0 = cx - 70
        painel(tela, x0, 104 - 96, 140, 82, borda=AMARELO, fundo=FUNDO2)
        D.tomada(tela, x0 + 34, 46, 2, t, viva=1.0)
        tela.texto('127 V', x0 + 90, 22, AMARELO, tam=17, centro=True, contorno=PRETO)
        tela.texto('OU', x0 + 90, 40, ACO3, tam=9, centro=True)
        tela.texto('220 V', x0 + 90, 52, AMARELO, tam=17, centro=True, contorno=PRETO)
        tela.texto('DEPENDE DA', x0 + 90, 70, ACO3, tam=9, centro=True)
        tela.linha(x0 + 70, 90, 266, 150, AMARELO) if not VERTICAL else None

    def sons(self, fx):
        for k in range(int(5.8 / .5)):
            fx.put(fx.blip(43, .25), self.t0 + 7.0 + k * .5, .05)
        fx.put(fx.chiado(1.5, 1500, 5000), self.t0 + 13.6, .05)
        for k in range(8):
            fx.put(fx.clique(3000, .01), self.t0 + 17.2 + k * .33, .1)
        fx.put(fx.blip(84, .08), self.t0 + 25.0, .15)
        fx.put(fx.clique(2400, .03), self.t0 + 35.5, .6)
        fx.put(fx.sino(81, 1.4), self.t0 + self.LUZ_T, .3)
        fx.put(fx.chiado(7.0, 2500, 7000, ataque=1.0), self.t0 + 40.8, .05)


# ============================================================ Brasil e o ciclo
BARRAS = [('HIDRÁULICA', 55.3, None), ('EÓLICA', 14.1, CIANO), ('SOLAR', 9.3, AMARELO), ('BIOMASSA', 8.1, VERDE),
          ('GÁS NATURAL', 6.3, LARANJA), ('OUTRAS', 7.0, ACO2)]


class Brasil(Cena):
    K, VX = 8, 130

    def desenhar(self, tela, t, tg):
        if t < 21.8:
            self.grafico(tela, t)
            est = ('HIDRELÉTRICAS', '55,3%', AGC)
        else:
            self.ciclo(tela, t - 21.8)
            est = ('A GOTA', 'EVAPORA' if t < 29.0 else 'VIRA CHUVA', AGC)
        if VERTICAL:
            D.selo_vertical(tela, 0, self.VX, 'BRASIL, 2024: DE ONDE VEM A LUZ')
            return
        D.painel_jornada(tela, 8, t, cab=('E NO', 'BRASIL?', VERDE), estado=est, tudo=True,
                         linhas=[('ELETRICIDADE EM 2024', 'ÁGUA: 55,3%', AGC), ('FONTE', 'EPE, BEN 2025', ACO3)],
                         rodape='OFERTA INTERNA, 2024')

    def grafico(self, tela, t):
        grade(tela, 0, 300)
        if VERTICAL:
            x0, wmax, y0, dy = self.VX - 84, 166, 22, 30
        else:
            x0, wmax, y0, dy = 12, 186, 26, 24
        tela.texto('ELETRICIDADE DO BRASIL, 2024', (x0 + (x0 + wmax + (0 if VERTICAL else 90))) // 2 if False else x0, 8, ACO3, tam=9, contorno=PRETO)
        esc = wmax / 56.0
        for i, (nome, pct, cor) in enumerate(BARRAS):
            a = .6 + i * .5
            if t < a: continue
            u = ease((t - a) / 1.4)
            if VERTICAL:
                ty, by = y0 + i * dy, y0 + i * dy + 10
                bx = x0
            else:
                ty, by = y0 + i * dy + 6, y0 + i * dy + 4
                bx = x0 + 78
            tela.texto(nome, x0, ty, BRANCO if i == 0 else ACO4, tam=9, contorno=PRETO)
            w = max(2, int(esc * pct * u))
            hh = 14 if i == 0 else 10
            if VERTICAL: hh = 12 if i == 0 else 8
            tela.ret(bx - 1, by - 1, w + 2, hh + 2, PRETO)
            if cor is None:
                agua(tela, bx, bx + w, by + 2, by + hh, t, onda=.6, brilho=False)
                tela.ret(bx, by, w, 2, CEU2)
            else:
                tela.ret(bx, by, w, hh, cor); tela.ret(bx, by, w, 1, BRANCO if cor != ACO2 else ACO4)
            txt = f"{I.decimal(pct, 1)}%"
            tx = bx + w + 4
            if not VERTICAL or tx + tela.largura_texto(txt, 9) < x0 + 176:
                tela.texto(txt, tx, by + (2 if i == 0 else 1), AMARELO if i == 0 else BRANCO, tam=9, contorno=PRETO)
            if i == 0 and t > 7.6:
                mira(tela, bx + w / 2, by + hh / 2, t, max(8, hh))
        if t > 14.8:
            yy = y0 + 6 * dy + 6
            tela.texto('OUTRAS: NUCLEAR, CARVÃO, PETRÓLEO,', x0, yy, ACO2, tam=9, contorno=PRETO)
            tela.texto('ENERGIA IMPORTADA', x0, yy + 10, ACO2, tam=9, contorno=PRETO)

    def ciclo(self, tela, u):
        ceu(tela, 160, 0, 300, u, estrelas=False, cores=(CEU1, CEU2, CEU2, CEU2))
        # sol
        sx, sy = (self.VX - 60, 36) if VERTICAL else (40, 36)
        halo(tela, sx, sy, 22 + math.sin(u * 3), CHAMA1)
        tela.disco(sx, sy, 13, PRETO); tela.disco(sx, sy, 12, AMARELO); tela.disco(sx - 3, sy - 3, 6, CHAMA0)
        for k in range(8):
            a = k * math.pi / 4 + u * .4
            tela.linha(sx + math.cos(a) * 16, sy + math.sin(a) * 16, sx + math.cos(a) * 20, sy + math.sin(a) * 20, AMARELO)
        morro(tela, [(x, 150 - 10 * math.sin(x * .04)) for x in range(-4, 304, 6)], GRAMA1, GRAMA2)
        agua(tela, 0, 300, 162, PALCO_H, u, onda=.8)
        cx = self.VX if VERTICAL else 160
        cresce = um((u - 2.0) / 4.0)
        if cresce > 0:
            nuvem(tela, cx, 40, 30 + 40 * cresce, chuva=u > 7.2)
        if u < 7.2:
            v = um((u - 1.0) / 5.0)
            gx, gy = cx, lerp(166, 54, ease(v))
            if v < .05:
                gota(tela, gx, gy, 1.2, u)
            else:
                for k in range(6):
                    ph = (u * .8 + k / 6) % 1.0
                    tela.px(cx - 10 + k * 4 + math.sin(u * 3 + k) * 2, lerp(160, 60, ph), ESPUMA if k % 2 else BRANCO)
                tela.disco(gx, gy, 2.5 * (1 - v * .5), ESPUMA)
                tela.px(gx + 4, gy - 3, AMARELO)
            if v > .05: self.rot(tela, 'VAPOR', cx + 10, (166 + gy) / 2, ESPUMA)
        else:
            chuva(tela, cx - 34, cx + 34, 56, 162, u, n=18, vel=120)
            y = lerp(60, 160, ((u - 7.2) / 3.0) % 1.0)
            gota(tela, cx + 4, y, 1.0, u)
            self.rot(tela, 'DE NOVO: CHUVA', cx + 20, 80, AGC)

    def sons(self, fx):
        for i in range(6):
            fx.put(fx.blip(72 + i * 2, .08), self.t0 + .6 + i * .5, .12)
        fx.put(fx.chiado(6.0, 400, 2000, ataque=2.0), self.t0 + 23.0, .05)
        fx.put(fx.chiado(6.5, 2500, 7000, ataque=1.0), self.t0 + 29.0, .06)


# ============================================================ resumo
class Resumo(Cena):
    LIGA = [0.8, 2.6, 4.4, 7.8, 10.0, 15.0, 16.8, 18.6, 22.2]
    FORMA = [0, 0, 0, 1, 2, 2, 2, 2, 2]
    TENS = [None, None, None, None, '13,8 KV', '500 KV', '500 KV', '13,8 KV', '220 V']

    def desenhar(self, tela, t, tg):
        grade(tela)
        tela.texto('A JORNADA DA ÁGUA EM 9 ETAPAS', W // 2, 14, ACO3, tam=17, centro=True, contorno=PRETO)
        for i in range(9):
            aceso = t >= self.LIGA[i]
            D.icone(tela, i, ICX[i], 72, t, aceso=aceso)
            tela.texto(str(i + 1), ICX[i], 98, ETAPAS[i][1] if aceso else ACO1, tam=9, centro=True, contorno=PRETO)
            if aceso:
                nm = ETAPAS[i][0] if i != 5 else 'TRANSF.'
                tela.texto(nm, ICX[i], 110, BRANCO, tam=9, centro=True, contorno=PRETO) if len(nm) <= 8 else \
                    tela.texto(nm[:8], ICX[i], 110, BRANCO, tam=9, centro=True, contorno=PRETO)
                f = D.FORMAS[self.FORMA[i]]
                tela.ret(ICX[i] - 22, 126, 45, 4, f[1])
                if self.TENS[i]: tela.texto(self.TENS[i], ICX[i], 136, AMARELO, tam=9, centro=True, contorno=PRETO)
            if i < 8:
                xa, xb = ICX[i] + 22, ICX[i + 1] - 22
                tela.ret(xa, 72, xb - xa, 1, ETAPAS[i][1] if t >= self.LIGA[i + 1] else ACO0)
        # legenda das formas
        for j, (nm, cor) in enumerate(D.FORMAS):
            x = 70 + j * 120
            tela.ret(x, 164, 10, 4, cor)
            tela.texto(nm, x + 14, 162, cor, tam=9, contorno=PRETO)
        # protagonista andando de ícone em ícone
        k = sum(1 for a in self.LIGA if t >= a) - 1
        if k >= 0:
            x = ICX[k]
            if self.FORMA[k] == 0: gota(tela, x, 42, 1.0, t)
            else: faisca(tela, x, 44, t, 2.4)
        if t > 22.2:
            D.lampada(tela, ICX[8], 186, 1.0, t)

    def sons(self, fx):
        for i, a in enumerate(self.LIGA):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12, 14)[i], .1), self.t0 + a, .16)
        fx.put(fx.sino(84, 1.2), self.t0 + 22.2, .2)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS A JORNADA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            grade(tela)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            nuvem(tela, W // 2, 90, 70, chuva=True)
            chuva(tela, W // 2 - 40, W // 2 + 40, 100, 190, t, n=16, vel=100)
            gota(tela, W // 2 + 6, 110 + (t * 30) % 70, 1.4, t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, chuva=Chuva, represa=Represa, conduto=Conduto, turbina=Turbina,
             saida=Saida, gerador=Gerador, itaipu=Itaipu, elevador=Elevador, linhas=Linhas,
             subestacao=Subestacao, casa=Casa, brasil=Brasil, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep11_motor as EP
    if sys.argv[1] in ('--folha', '--quadros'):
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if sys.argv[1] == '--folha':
            so = sys.argv[3:] or None
            for c in trilha.caps:
                if so and c['id'] not in so: continue
                ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        else:
            for a in sys.argv[3:]:
                cid, tt = a.split(':')
                c = next(x for x in trilha.caps if x['id'] == cid)
                ts.append(c['t0'] + float(tt))
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else 2
        if len(ims) == 1: cols = 1
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
