#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep05 — Como a geladeira faz frio (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (compressor, palhetas, chiado, porta),
                          nos mesmos instantes do desenho
O estado do fluido sai de `ep05_desenho.estado(s)`: a cor do cano, a porção
de fluido e o painel leem a mesma função.

    python3 ep05_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep05_motor.py <saida.mp4> etapa1 etapa2    # só esses capítulos (teste)
    python3 ep05_motor.py --folha <saida.png>          # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ep05_desenho as D
from ep05_desenho import ETAPAS, estado, cor_temp, calor, floco, parcela, mira, termometro, fio, painel_estado
import ritmo_marca as RM
import idioma as I
from ep05_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2605, 43
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def raio(tela, x, y, cor=AMARELO):
    """Raiozinho de energia elétrica (7x11)."""
    pts = [(x + 3, y), (x + 7, y), (x + 4, y + 4), (x + 7, y + 4), (x + 1, y + 11), (x + 2, y + 6), (x, y + 6)]
    poligono(tela, [(a - 1, b) for a, b in pts], PRETO)
    poligono(tela, [(a + 1, b) for a, b in pts], PRETO)
    poligono(tela, pts, cor)


def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def cartao(tela, t, k, x=150):
    """Cartão da etapa entrando pela esquerda (0..2 s)."""
    nome, cor = ETAPAS[k]
    if t >= 2.0 or VERTICAL: return
    u = ease(t / .4)
    larg = tela.largura_texto(nome, 26)
    xx = int(x - larg // 2 + (1 - u) * -300)
    painel(tela, xx - 8, 8, larg + 16, 34, borda=cor)
    tela.texto(nome, xx, 14, cor, tam=26, contorno=PRETO)


def leitura_vertical(tela, T, P, vap, x=150):
    """No Short o painel fica de fora: pressão e temperatura no alto do recorte."""
    if not VERTICAL: return
    s = f"{D.fmt_bar(P)}  {D.fmt_temp(T)}"
    w = tela.largura_texto(s, 9) + 10
    painel(tela, x - w // 2, 1, w, 13, borda=cor_temp(T))
    tela.texto(s, x, 4, cor_temp(T), tam=9, centro=True)


def zumbido(fx, t0, t1, g=.05):
    """Compressor ligado: pulsos curtos a 25 por segundo viram um zumbido."""
    k = 0
    while t0 + k / 25.0 < t1:
        fx.put(fx.pulso(), t0 + k / 25.0, g)
        k += 1


class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass


_G = None


def geladeira():
    global _G
    if _G is None: _G = D.Geladeira()
    return _G


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        self.G = geladeira()

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        if t < 6.0:
            porta = ease((t - .8) / 1.0) * (1 - ease((t - 5.2) / .6))
            if VERTICAL: porta *= .3
            G.desenhar(tela, t, s=None, porta=porta, vel=14)
            # névoa fria escorrendo pela frente e pelo chão
            if porta > .2:
                for i in range(26):
                    u = (t * .5 + i / 26) % 1.0
                    x = 58 - u * 58 + math.sin(u * 6 + i) * 3
                    y = 120 + u * 76 + (i % 4) * 2
                    tela.px(x, min(y, 196), MISTURA2 if i % 3 else BRANCO)
            if t > 1.6 and not VERTICAL:
                rotulo(tela, 'DE ONDE VEM', 316, 60, BRANCO, 17)
                rotulo(tela, 'ESSE FRIO?', 316, 82, CIANO, 17)
                for k in range(6):
                    floco(tela, 330 + k * 22, 120 + int(math.sin(t * 2 + k) * 4))
        else:
            G.desenhar(tela, t, s=(t - 6) * .55, vel=22)
            G.calor_dentro(tela, t, n=14, rate=.5)
            G.calor_fora(tela, t, n=18, rate=.6)
            G.ondas(tela, t)
            if not VERTICAL:
                rotulo(tela, 'O CALOR', 316, 60, LARANJA, 17)
                rotulo(tela, 'SAI POR TRÁS', 316, 82, LARANJA, 17)
                D.seta(tela, 300, 70, 1, 0, LARANJA, 6)

    def sons(self, fx):
        fx.put(fx.clique(1500, .04), self.t0 + .8, .4)
        fx.put(fx.chiado(4.0, 300, 2500), self.t0 + 1.2, .15)
        fx.put(fx.clique(900, .06), self.t0 + 5.8, .5)
        zumbido(fx, self.t0 + 6.0, self.t0 + self.dur, .05)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        for k in range(18):
            x = (k * 53) % 200 + 10
            y = (k * 31 + t * 12) % 200
            floco(tela, x, y)
        for k in range(14):
            x = 300 + (k * 41) % 170
            y = 200 - (k * 29 + t * 18) % 200
            calor(tela, x, y)
        n = int(t / .045)
        for j, linha in enumerate(("COMO A GELADEIRA", "FAZ FRIO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 16)]
            tela.texto(vis, W // 2 - larg // 2, 60 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", W // 2, 136, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 66 + k * 40
                c = cor if t > 2.0 + k * .35 else FUNDO2
                tela.ret(x, 160, 14, 14, c)
                tela.texto(str(k + 1), x + 4, 163, PRETO, tam=9)

    def sons(self, fx):
        for k in range(4):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + 2.0 + k * .35, .2)


# ============================================================ cozinha
class Cozinha(Cena):
    def preparar(self):
        self.G = geladeira()

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        G.desenhar(tela, t, s=None, vel=16)
        quente = t >= 14.8
        if quente:
            G.ondas(tela, t)
        if t >= 22.0:
            G.calor_dentro(tela, t, n=12, rate=.4)
            G.calor_fora(tela, t, n=16, rate=.5)
        # mão chegando nas costas
        if 14.8 <= t < 22.5:
            u = ease((t - 15.2) / 1.6)
            x = int(300 - u * (84 if VERTICAL else 58))
            y = 92
            self._mao(tela, x, y)
            if u > .9:
                rotulo(tela, 'QUENTE!', 196 if VERTICAL else 250, 122, LARANJA)
        if VERTICAL: return
        # painel: três termômetros
        tela.texto('TEMPERATURAS', PX0, 8, ACO3, tam=17, contorno=PRETO)
        itens = [('CONGELADOR', '-18 °C OU -', MISTURA, (-18 + 30) / 60, 7.8, (150, 40)),
                 ('GELADEIRA', '4 °C OU -', CIANO, (4 + 30) / 60, 7.8, (150, 150)),
                 ('COZINHA', '25 °C', AMARELO, (25 + 30) / 60, 1.0, None)]
        for j, (nome, val, cor, fr, t_ap, alvo) in enumerate(itens):
            if t < t_ap: continue
            y = 32 + j * 46
            u = ease((t - t_ap) / 1.0)
            termometro(tela, PX0 + 8, y, 26, fr * u, cor)
            tela.texto(nome, PX0 + 22, y + 2, BRANCO, tam=9, contorno=PRETO)
            tela.texto(val.replace(' OU -', ''), PX0 + 22, y + 14, cor, tam=17, contorno=PRETO)
            if 'OU' in val:
                tela.texto('OU MENOS', PX0 + 30 + tela.largura_texto(val.replace(' OU -', ''), 17), y + 18, ACO3, tam=9, contorno=PRETO)
            if j == 2: tela.texto('(EXEMPLO)', PX0 + 92, y + 18, ACO2, tam=9)
            if alvo and 7.8 <= t < 14.8:
                fio(tela, PX0 + 2, y + 6, alvo[0], alvo[1], cor)
        if quente:
            tela.texto('ATRÁS:', PX0, 182, ACO3, tam=9, contorno=PRETO)
            tela.texto('QUENTE', PX0 + 40, 178, LARANJA, tam=17, contorno=PRETO)

    def _mao(self, tela, x, y):
        """Mão genérica, de lado, palma para a geladeira."""
        tela.ret(x + 18, y + 4, 40, 18, PRETO); tela.ret(x + 19, y + 5, 38, 16, LATAO)    # punho/manga
        tela.ret(x + 30, y + 3, 30, 20, PRETO); tela.ret(x + 31, y + 4, 28, 18, ROXO)
        tela.ret(x + 31, y + 4, 28, 2, ROSA)
        tela.ret(x + 2, y - 1, 20, 24, PRETO); tela.ret(x + 3, y, 18, 22, LATAO)
        for k in range(4):
            tela.ret(x - 6, y + k * 6 - 1, 12, 6, PRETO); tela.ret(x - 5, y + k * 6, 10, 4, LATAO)
            tela.ret(x - 5, y + k * 6, 10, 1, OLEO1)
        tela.ret(x + 6, y - 6, 6, 9, PRETO); tela.ret(x + 7, y - 5, 4, 8, LATAO)       # polegar
        tela.ret(x + 3, y + 1, 1, 20, OLEO1)

    def sons(self, fx):
        zumbido(fx, self.t0, self.t0 + self.dur, .035)
        for k in range(3):
            fx.put(fx.blip(76 + k * 3, .08), self.t0 + 7.8 + k * .2, .12)


# ============================================================ calor
class Calor(Cena):
    def preparar(self):
        self.G = geladeira()

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        ligado = t >= 7.8
        G.desenhar(tela, t, s=(t - 7.8) * .5 if ligado else None, ligado=ligado, vel=20, apagado=0 if ligado else .6)
        if not ligado:
            # calor entrando sozinho pelas paredes (do quente para o frio)
            for i in range(18):
                u = (t * .35 + i / 18) % 1.0
                lado = i % 3
                if lado == 0: x, y = 30 + u * 60, 60 + (i * 23) % 120          # pela porta
                elif lado == 1: x, y = 80 + (i * 17) % 100, 2 + u * 30          # pelo teto
                else: x, y = 70 + (i * 13) % 100, 200 - u * 18                 # pelo fundo
                calor(tela, x, y, int(t * 5 + i) % 2)
        else:
            G.calor_dentro(tela, t, n=14, rate=.45)
            G.calor_fora(tela, t, n=18, rate=.55)
            G.ondas(tela, t)
        if t >= 15.8:
            raio(tela, 222, 150)
            if not VERTICAL:
                rotulo(tela, 'COMPRESSOR', 240, 199, AMARELO, centro=True)
                fio(tela, 252, 197, 228, 186)
        if VERTICAL: return
        # painel: quente -> frio sozinho; frio -> quente só empurrando
        tela.texto('PARA ONDE', PX0, 8, ACO3, tam=17, contorno=PRETO)
        tela.texto('ANDA O CALOR', PX0, 26, ACO3, tam=17, contorno=PRETO)
        for j, (nome, val, cor, y) in enumerate((('COZINHA', '25 °C', AMARELO, 58), ('GELADEIRA', '4 °C', CIANO, 128))):
            painel(tela, PX0, y, 120, 30, borda=cor)
            tela.texto(nome, PX0 + 8, y + 6, BRANCO, tam=9)
            tela.texto(val, PX0 + 8, y + 16, cor, tam=9)
        # seta descendo (sozinho)
        tela.ret(PX0 + 40, 90, 2, 34, LARANJA); D.seta(tela, PX0 + 41, 120, 0, 1, LARANJA, 5)
        tela.texto('SOZINHO', PX0 + 48, 100, LARANJA, tam=9, contorno=PRETO)
        u = (t * .6) % 1.0
        calor(tela, PX0 + 41, 92 + u * 26)
        if t >= 7.8:
            tela.ret(PX0 + 92, 92, 2, 34, VERDE); D.seta(tela, PX0 + 93, 92, 0, -1, VERDE, 5)
            calor(tela, PX0 + 93, 124 - u * 26)
            tela.texto('EMPURRADO', PX0 + 100, 104, VERDE, tam=9, contorno=PRETO)
            raio(tela, PX0 + 140, 88)
            n = int((t - 7.8) * 2.2)
            tela.texto(f"CALOR TIRADO: {n}", PX0, 170, AMARELO, tam=9, contorno=PRETO)
            tela.texto('(PITADAS)', PX0, 182, ACO2, tam=9)

    def sons(self, fx):
        fx.put(fx.clique(900, .06), self.t0 + 7.8, .5)
        zumbido(fx, self.t0 + 7.8, self.t0 + self.dur, .05)


# ============================================================ evaporar
class Evaporar(Cena):
    def preparar(self):
        rng = np.random.default_rng(3)
        self.gotas = [(int(x), float(r), float(f)) for x, r, f in
                      zip((56, 150, 246), (25, 29, 23), rng.uniform(0, 6, 3))]
        self.tubo = D.Tubo([(316, 120), (466, 120)], 7)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        dither(tela, 0, 0, 300, 110, FUNDO, FUNDO2)
        # a pele, em corte
        yp = 150
        tela.ret(0, yp - 1, 300, 1, PRETO)
        dither(tela, 0, yp, 300, PALCO_H - yp, LATAO, OLEO1)
        dither(tela, 0, yp + 24, 300, PALCO_H - yp - 24, OLEO1, BRASA)
        tela.ret(0, yp, 300, 1, CHAMA1)
        for k in range(12):
            x = 12 + k * 25
            tela.ret(x, yp + 2, 2, 6, OLEO0)                 # poros
        # o calor da pele subindo para as gotas
        for i in range(14):
            u = (t * .5 + i / 14) % 1.0
            x = (i * 47) % 290 + 5
            calor(tela, x, yp + 40 - u * 36, int(t * 5 + i) % 2)
        # gotas de suor encolhendo (evaporando) e vapor subindo levando calor
        enc = 1 - .45 * suave(t / self.dur)
        for i, (x, r, f) in enumerate(self.gotas):
            rr = r * enc
            pts = [(x + rr * math.cos(a), yp - rr * .8 * math.sin(a)) for a in np.linspace(0, math.pi, 18)]
            poligono(tela, [(px_ - 1, py_ - 1) for px_, py_ in pts] + [(x - rr - 1, yp + 1), (x + rr + 1, yp + 1)], PRETO)
            poligono(tela, pts + [(x - rr, yp), (x + rr, yp)], CIANO)
            tela.ret(int(x - rr * .5), int(yp - rr * .55), 3, 2, BRANCO)
            tela.ret(int(x - rr * .7), int(yp - rr * .2), 2, 2, MISTURA2)
            for j in range(9):
                u = (t * .3 + j / 9 + f) % 1.0
                vx = x + math.sin(u * 6 + i * 2 + j * 1.7) * (4 + u * 14) + (j - 4) * 2
                vy = yp - rr * .8 - 3 - u * 115
                if vy < 6: continue
                c = MISTURA2 if u < .5 else (ACO3 if u < .8 else ACO1)
                tela.disco(vx, vy, 2.6, PRETO); tela.disco(vx, vy, 1.8, c)
                if u < .7: calor(tela, vx + 5, vy - 2, int(t * 5 + j) % 2)
        rotulo(tela, 'PELE', 8, 188, CHAMA0)
        rotulo(tela, 'SUOR', 8, 128, CIANO)
        rotulo(tela, 'VAPOR + CALOR', 8, 20, MISTURA2)
        if VERTICAL: return
        # painel
        tela.texto('EVAPORAR', PX0, 8, ACO3, tam=17, contorno=PRETO)
        tela.texto('ROUBA CALOR', PX0, 26, AMARELO, tam=17, contorno=PRETO)
        fr = .7 - .25 * suave((t - 2) / 14)
        termometro(tela, PX0 + 10, 52, 40, fr, CHAMA1)
        tela.texto('PELE', PX0 + 24, 60, BRANCO, tam=9, contorno=PRETO)
        tela.texto('ESFRIA', PX0 + 24, 72, MISTURA2 if t > 4 else ACO2, tam=9, contorno=PRETO)
        if t >= 15.8:
            u = ease((t - 15.8) / .8)
            self.tubo.desenhar(tela, -25.0, .45, t, vel=10, ferve=True)
            tela.texto('O FLUIDO DA', PX0 + 10, 140, BRANCO, tam=9, contorno=PRETO)
            tela.texto('GELADEIRA FERVE', PX0 + 10, 151, BRANCO, tam=9, contorno=PRETO)
            tela.texto('NO FRIO', PX0 + 10, 164, MISTURA2, tam=17, contorno=PRETO)
            for k in range(4):
                floco(tela, 330 + k * 34, 192 + int(math.sin(t * 2 + k) * 2))

    def sons(self, fx):
        for k in range(30):
            fx.put(fx.blip(96 + (k * 5) % 7, .03), self.t0 + 1 + k * .75, .04, -.5 + (k % 5) * .25)


# ============================================================ peças
PECAS = [('compressor', 'COMPRESSOR', (215, 172)), ('condensador', 'CONDENSADOR', (228, 90)),
         ('capilar', 'TUBO CAPILAR', (195, 110)), ('evaporador', 'EVAPORADOR', (174, 30)),
         ('fluido', 'FLUIDO', None)]


class Pecas(Cena):
    def preparar(self):
        self.G = geladeira()
        self.slot = self.dur / len(PECAS)

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        k_atual = min(len(PECAS) - 1, int(t / self.slot))
        vis, desl = set(), {}
        for k, (nome, rot, anc) in enumerate(PECAS):
            tk = k * self.slot
            if t >= tk:
                vis.add(nome)
                u = (t - tk) / .55
                if u < 1 and nome != 'fluido':
                    y = -170 * (1 - u) ** 2 if u < .75 else -5 * math.sin((u - .75) / .25 * math.pi)
                    desl[nome] = (0, int(y))
        t_f = 4 * self.slot
        s = (t - t_f) * .35 if t >= t_f + .5 else None
        self.G.desenhar(tela, t, s=s, pecas=vis, desloc=desl, vel=20)
        if t >= t_f + 2:
            self.G.calor_dentro(tela, t, n=10, rate=.4)
            self.G.calor_fora(tela, t, n=12, rate=.5)
        if VERTICAL: return
        for k, (nome, rot, anc) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 14 + k * 26
            atual = k == k_atual
            cor = ETAPAS[k][1] if k < 4 else MISTURA2
            tela.texto(rot, PX0 + 8, y, cor if atual else ACO2, tam=17, contorno=PRETO)
            if k < 4: tela.ret(PX0 - 4, y + 4, 6, 6, cor if atual else ACO1)
            if atual and t - k * self.slot > .55:
                if anc is None:
                    anc = self.G.pos(s if s is not None else 0)
                fio(tela, PX0 - 6, y + 7, anc[0], anc[1], AMARELO)
        if k_atual == 4:
            tela.texto('ISOBUTANO (R-600A)', PX0 + 8, 134, ACO3, tam=9, contorno=PRETO)
            tela.texto('COR = TEMPERATURA', PX0 + 8, 156, BRANCO, tam=9, contorno=PRETO)
            for j in range(140):
                TT = -30 + j / 139 * 100
                tela.ret(PX0 + 8 + j, 168, 1, 6, cor_temp(TT))
            tela.texto('FRIO', PX0 + 8, 178, MISTURA, tam=9, contorno=PRETO)
            tela.texto('QUENTE', PX0 + 148, 178, VERMELHO, tam=9, centro='d', contorno=PRETO)

    def sons(self, fx):
        for k in range(4):
            t = self.t0 + k * self.slot + .41
            fx.put(fx.clique(1800, .05), t, .45)
            fx.put(fx.explosao(.5), t, .2)
        zumbido(fx, self.t0 + 4 * self.slot + .5, self.t0 + self.dur, .05)
        fx.put(fx.chiado(3.0, 400, 3000), self.t0 + 4 * self.slot + .5, .12)


# ============================================================ fluido: ponto de fervura x pressão
class Fluido(Cena):
    X0, X1, YB, YT = 44, 284, 184, 18
    PMAX, TMIN, TMAX = 7.0, -30.0, 50.0

    def px(self, P): return self.X0 + P / self.PMAX * (self.X1 - self.X0)
    def py(self, T): return self.YB - (T - self.TMIN) / (self.TMAX - self.TMIN) * (self.YB - self.YT)

    def ponto(self, t):
        """(P, travado em -11,8?) da gotinha no tempo t."""
        P_ar = 1.013
        if t < 8.8: return P_ar, True
        if t < 17.6:
            u = (t - 8.8) / 8.8
            return 1.013 + 1.6 * math.sin(u * math.pi * 2) * math.sin(u * math.pi), False
        if t < 21.0:
            return 1.013 + (D.P_BAIXA - 1.013) * ease((t - 17.8) / 1.5), False
        return D.P_BAIXA + (D.P_ALTA - D.P_BAIXA) * suave((t - 21.0) / 3.0), False

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        X0, X1, YB, YT = self.X0, self.X1, self.YB, self.YT
        # regiões: acima da curva = gás, abaixo = líquido
        curva = [(self.px(p), self.py(tt)) for tt, p in D.NIST]
        poligono(tela, [(X0, YT)] + [(self.px(D.NIST[0][1]), YT)] + curva + [(X1, curva[-1][1]), (X1, YT)], FUNDO)
        dither(tela, X0, YT, X1 - X0, YB - YT, FUNDO, FUNDO2)
        pts_liq = [(self.px(D.NIST[0][1]), YB)] + curva + [(X1, curva[-1][1]), (X1, YB)]
        poligono(tela, pts_liq, AGUA0)
        for y in range(YT, YB, 2):
            for x in range(X0 + (y // 2) % 4, X1, 8):
                if tela.buf[y, x] == AGUA0: tela.px(x, y, FUNDO2)
        # grade e eixos
        for P in range(0, 8):
            x = int(self.px(P))
            tela.ret(x, YT, 1, YB - YT, FUNDO3)
            tela.texto(str(P), x, YB + 5, ACO3, tam=9, centro=True)
        for T in (-20, 0, 20, 40):
            y = int(self.py(T))
            tela.ret(X0, y, X1 - X0, 1, FUNDO3)
            tela.texto(f"{T}", X0 - 4, y - 3, ACO3, tam=9, centro='d')
        tela.ret(X0, YT, 1, YB - YT + 1, ACO2); tela.ret(X0, YB, X1 - X0, 1, ACO2)
        tela.texto('°C', X0 - 4, YT - 2, ACO3, tam=9, centro='d')
        tela.texto('PRESSÃO (BAR)', X1, YB + 14, ACO3, tam=9, centro='d')
        tela.texto('GÁS', 70, 40, ACO4, tam=17, contorno=PRETO)
        tela.texto('LÍQUIDO', 270, 150, MISTURA2, tam=17, centro='d', contorno=PRETO)
        # a curva de fervura (NIST)
        for (a, b), (c, d) in zip(curva, curva[1:]):
            linha_grossa(tela, a, b, c, d, 4, PRETO)
        for (a, b), (c, d) in zip(curva, curva[1:]):
            linha_grossa(tela, a, b, c, d, 2, AMARELO)
        tela.texto('FERVE AQUI', 180, 58, AMARELO, tam=9, contorno=PRETO)
        # marcas
        marcas = [(1.013, -11.8, 'AR LIVRE', 0.0), (D.P_BAIXA, -25.0, 'POUCA', 17.8), (6.044, 45.0, 'MUITA', 21.0)]
        for P, T, nome, ta in marcas:
            if t < ta: continue
            x, y = self.px(P), self.py(T)
            tela.ret(int(x), int(y), 1, YB - int(y), ACO1)
            tela.disco(x, y, 3, PRETO); tela.disco(x, y, 2, BRANCO)
            dxl = 8 if nome != 'MUITA' else -8
            tela.texto(nome, x + dxl, y - 12 if nome != 'POUCA' else y + 6, BRANCO, tam=9,
                       centro=False if dxl > 0 else 'd', contorno=PRETO)
        # a gotinha
        P, trava = self.ponto(t)
        T = -11.8 if trava else D.t_ferve(P)
        x, y = self.px(P), self.py(T)
        parcela(tela, x, y, T, .3, t, r=4)
        leitura_vertical(tela, T, P, .3)
        if VERTICAL: return
        # painel
        tela.texto('ISOBUTANO', PX0, 8, MISTURA2, tam=17, contorno=PRETO)
        tela.texto('R-600A', PX0, 28, ACO3, tam=9, contorno=PRETO)
        tela.texto('PRESSÃO', PX0, 52, ACO3, tam=9, contorno=PRETO)
        s = '1 ATM (AR LIVRE)' if trava else D.fmt_bar(P)
        tela.texto(s, PX0, 62, BRANCO, tam=17 if not trava else 9, contorno=PRETO)
        tela.texto('FERVE A', PX0, 92, ACO3, tam=9, contorno=PRETO)
        st = '-11,8 °C' if trava else f"{int(round(T))} °C"
        tela.texto(st, PX0, 102, cor_temp(T), tam=26, contorno=PRETO)
        if t > 8.8:
            tela.texto('MAIS PRESSÃO =', PX0, 146, BRANCO, tam=9, contorno=PRETO)
            tela.texto('FERVE MAIS QUENTE', PX0, 158, AMARELO, tam=9, contorno=PRETO)
        tela.texto('FONTE: NIST', PX0, 190, ACO2, tam=9)

    def sons(self, fx):
        fx.put(fx.sino(76), self.t0 + 17.8, .25)
        fx.put(fx.sino(83), self.t0 + 24.0, .25)


# ============================================================ etapa 1: compressor
class Etapa1(Cena):
    def preparar(self):
        self.C = D.CloseCompressor()

    def teta(self, t):
        th_d = self.C.th_d
        marcos = [(0, 0.0), (2.0, 0.0), (10.0, 180.0), (20.0, th_d), (27.0, 360.0), (30.0, 400.0)]
        for (a, x), (b, y) in zip(marcos, marcos[1:]):
            if t <= b: return x + (y - x) * (suave((t - a) / (b - a)) if b > a else 1)
        return marcos[-1][1]

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        th = self.teta(t)
        T_, P, fase = self.C.desenhar(tela, th, t, rotulos=not VERTICAL)
        if th >= 360: T_, P, fase = D.T_DESC, D.P_ALTA, 'desc'       # a nossa porção já saiu
        prog = 0.0 if fase == 'suc' else (math.log(P / D.P_BAIXA) / math.log(D.P_ALTA / D.P_BAIXA) * .98)
        if not VERTICAL:
            rotulo(tela, 'DO EVAPORADOR', 296, 160, MISTURA2, centro='d')
            rotulo(tela, 'PARA O CONDENSADOR', 296, 6, LARANJA, centro='d')
            rotulo(tela, 'PISTÃO', 196, 110, ACO4, centro=True)
            painel_estado(tela, 0, T_, P, 1.0, prog)
        else:
            rotulo(tela, 'PISTÃO', 196, 110, ACO4, centro=True)
        leitura_vertical(tela, T_, P, 1.0, x=186)
        cartao(tela, t, 0)

    def sons(self, fx):
        C = self.C
        for t, f in ((2.05, 2400), (20.0, 3200)):
            fx.put(fx.clique(f, .03), self.t0 + t, .35, .4)
        fx.put(fx.chiado(7.5, 200, 1200), self.t0 + 2.2, .18, .4)
        fx.put(fx.chiado(6.5, 500, 3000), self.t0 + 20.2, .2, .5)
        zumbido(fx, self.t0, self.t0 + self.dur, .04)


# ============================================================ etapa 2: condensador
class Etapa2(Cena):
    def preparar(self):
        self.C = D.CloseCondensador()

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        dither(tela, 0, 0, 300, PALCO_H, FUNDO, FUNDO2)
        u = .02 + .96 * suave((t - 2.0) / 26.0)
        self.C.desenhar(tela, t, u_parc=None)
        x, y = self.C.tr.em(u)
        s = 1 + min(.9999, max(0, (u - .02) / .96))
        T, P, vap, k = estado(s)
        parcela(tela, x, y, T, vap, t, r=4)
        mira(tela, x, y, t, 12)
        rotulo(tela, 'DO COMPRESSOR', 8, 4, VERMELHO)
        rotulo(tela, 'PARA O CAPILAR', 8, 198, CHAMA1)
        rotulo(tela, 'AR DA COZINHA', 150, 4, ACO4)
        if not VERTICAL:
            painel_estado(tela, 1, T, P, vap, (s - 1))
        leitura_vertical(tela, T, P, vap)
        cartao(tela, t, 1)

    def sons(self, fx):
        fx.put(fx.chiado(26.0, 150, 700), self.t0 + 2.0, .08)
        zumbido(fx, self.t0, self.t0 + self.dur, .025)


# ============================================================ etapa 3: tubo capilar
class Etapa3(Cena):
    def preparar(self):
        self.C = D.CloseCapilar()

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, 300, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, 300, 1, FUNDO2)
        self.C.desenhar(tela, t, rotulos=not VERTICAL)
        u = .03 + .94 * suave((t - 2.0) / 26.0)
        x, y = self.C.tr.em(u)
        s = self.C.s_de(u)
        T, P, vap, k = estado(s)
        parcela(tela, x, y, T, vap, t, r=3.5)
        mira(tela, x, y, t, 9)
        if not VERTICAL:
            rotulo(tela, 'DO CONDENSADOR', 8, 186, ACO3)
            rotulo(tela, 'PARA O EVAPORADOR', 292, 186, ACO3, centro='d')
            painel_estado(tela, 2, T, P, vap, s - 2)
        leitura_vertical(tela, T, P, vap)
        cartao(tela, t, 2)

    def sons(self, fx):
        fx.put(fx.chiado(26.0, 2500, 7000), self.t0 + 2.0, .07)
        for k in range(18):
            fx.put(fx.blip(100 + k % 5, .02), self.t0 + 18.8 + k * .55, .03)


# ============================================================ etapa 4: evaporador
class Etapa4(Cena):
    def preparar(self):
        self.C = D.CloseEvaporador()

    def desenhar(self, tela, t, tg):
        u = .02 + .96 * suave((t - 2.0) / 26.0)
        self.C.desenhar(tela, t, u_parc=None)
        x, y = self.C.tr.em(u)
        s = 3 + min(.9999, max(0, (u - .02) / .96))
        T, P, vap, k = estado(s)
        parcela(tela, x, y, T, vap, t, r=4)
        mira(tela, x, y, t, 12)
        rotulo(tela, 'AR: -18 °C', 8, 6, MISTURA2)
        rotulo(tela, 'FLUIDO: -25 °C', 168, 4, MISTURA)
        rotulo(tela, 'CALOR DA COMIDA', 8, 186, CHAMA1)
        if not VERTICAL:
            painel_estado(tela, 3, T, P, vap, s - 3)
            if t > 18.8:
                tela.texto('VOLTA AO COMPRESSOR', 290, 198, ACO4, tam=9, centro='d', contorno=PRETO)
        leitura_vertical(tela, T, P, vap, x=200)
        cartao(tela, t, 3)

    def sons(self, fx):
        rng = np.random.default_rng(4)
        for k in range(60):
            fx.put(fx.blip(int(rng.integers(88, 100)), .025), self.t0 + 2 + k * .43 + rng.uniform(0, .2), .035,
                   float(rng.uniform(-.6, .6)))


# ============================================================ ciclo completo
class Ciclo(Cena):
    def preparar(self):
        self.G = geladeira()

    def s(self, t): return .2 + t * .42

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        s = self.s(t)
        G.desenhar(tela, t, s=s, vel=28)
        G.calor_dentro(tela, t, n=14, rate=.5)
        G.calor_fora(tela, t, n=18, rate=.6)
        G.ondas(tela, t)
        T, P, vap, k = estado(s)
        if 9.6 <= t < 19.0 and not VERTICAL:
            rotulo(tela, 'CALOR ENTRA', 70, 3, CHAMA1)
            fio(tela, 138, 7, 172, 30, CHAMA1)
            rotulo(tela, 'CALOR SAI', 244, 4, LARANJA)
            fio(tela, 256, 14, 230, 50, LARANJA)
        if VERTICAL:
            leitura_vertical(tela, T, P, vap)
            return
        painel_estado(tela, k, T, P, vap, s % 1.0)
        voltas = int(s / 4)
        tela.texto(f"VOLTAS: {voltas}", PX0, 196, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        zumbido(fx, self.t0, self.t0 + self.dur, .05)
        k = 1
        while True:
            t = (k * 4 - .2) / .42
            if t > self.dur: break
            fx.put(fx.sino(79), self.t0 + t, .18)
            k += 1


# ============================================================ termostato
class Termostato(Cena):
    T0, LIM_BAIXO, LIM_ALTO, ESFRIA, ESQUENTA = 5.0, 3.0, 5.0, .2, .25

    def preparar(self):
        self.G = geladeira()
        ts = np.arange(0, self.dur + .02, .02)
        T, lig = self.T0, True
        Tv, Lv, trocas = [], [], []
        for t in ts:
            Tv.append(T); Lv.append(lig)
            T += (-self.ESFRIA if lig else self.ESQUENTA) * .02
            if lig and T <= self.LIM_BAIXO: lig = False; trocas.append((float(t), False))
            elif not lig and T >= self.LIM_ALTO: lig = True; trocas.append((float(t), True))
        self.ts, self.Tv, self.Lv, self.trocas = ts, np.array(Tv), np.array(Lv), trocas
        # posição do fluido: só anda com o compressor ligado
        self.sv = np.concatenate([[0.0], np.cumsum(np.where(self.Lv[:-1], .4 * .02, 0.0))])

    def em(self, t):
        i = min(len(self.ts) - 1, int(t / .02))
        return float(self.Tv[i]), bool(self.Lv[i]), float(self.sv[i])

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        T, lig, s = self.em(t)
        G.desenhar(tela, t, s=s + .3, ligado=lig, vel=20, apagado=0 if lig else .6)
        if lig:
            G.calor_dentro(tela, t, n=10, rate=.45); G.calor_fora(tela, t, n=12, rate=.5)
        else:
            for i in range(10):
                u = (t * .3 + i / 10) % 1.0
                calor(tela, 30 + u * 60, 70 + (i * 23) % 110, int(t * 5 + i) % 2)
        # o termostato: caixinha com botão dentro da geladeira
        tela.ret(150, 72, 30, 12, PRETO); tela.ret(151, 73, 28, 10, CERAMICA)
        tela.disco(158, 78, 4, ACO2); tela.linha(158, 78, 158 + 3 * math.cos(1.2), 78 - 3 * math.sin(1.2), PRETO)
        tela.ret(168, 76, 6, 4, VERDE if lig else BRASA)
        if VERTICAL:
            s_ = f"{I.decimal(T, 1)} °C  {'LIGADO' if lig else 'DESLIGADO'}"
            w = tela.largura_texto(s_, 9) + 10
            painel(tela, 150 - w // 2, 1, w, 13, borda=VERDE if lig else BRASA)
            tela.texto(s_, 150, 4, BRANCO, tam=9, centro=True)
            return
        # painel: gráfico de temperatura e barra liga/desliga
        tela.texto('TERMOSTATO', PX0 + 4, 6, AMARELO, tam=9, contorno=PRETO)
        tela.texto('MEDE DENTRO:', PX0 + 4, 16, ACO3, tam=9, contorno=PRETO)
        fio(tela, PX0, 10, 180, 78, AMARELO)
        tela.texto(f"{I.decimal(T, 1)} °C", PX0 + 168, 8, cor_temp(T), tam=17, centro='d', contorno=PRETO)
        gx0, gx1, gy = PX0 + 22, PX0 + 166, lambda v: 118 - (v - 2.0) / 4.0 * 84
        tela.ret(gx0, 30, gx1 - gx0, 92, FUNDO); tela.ret_vazado(gx0 - 1, 29, gx1 - gx0 + 2, 94, ACO1)
        for v, rot in ((5.0, '5'), (3.0, '3')):
            y = int(gy(v))
            for x in range(gx0, gx1, 4): tela.ret(x, y, 2, 1, ACO2)
            tela.texto(rot, gx0 - 4, y - 3, ACO3, tam=9, centro='d')
        tela.texto('°C', gx0 - 4, 32, ACO3, tam=9, centro='d')
        n = int(t / .02)
        idx = np.arange(0, max(1, n), 2)
        xs = gx0 + idx * .02 / self.dur * (gx1 - gx0)
        for x, i in zip(xs, idx):
            y = gy(self.Tv[i])
            tela.ret(int(x), int(y) - 1, 2, 3, PRETO)
        for x, i in zip(xs, idx):
            tela.px(x, gy(self.Tv[i]), cor_temp(self.Tv[i]))
            tela.px(x + 1, gy(self.Tv[i]), cor_temp(self.Tv[i]))
        cx = gx0 + t / self.dur * (gx1 - gx0)
        tela.disco(cx, gy(T), 3, PRETO); tela.disco(cx, gy(T), 2, BRANCO)
        # barra do compressor
        tela.texto('COMPRESSOR', PX0, 130, ACO3, tam=9, contorno=PRETO)
        tela.ret(gx0 - 1, 142, gx1 - gx0 + 2, 8, PRETO)
        for x, i in zip(xs, idx):
            tela.ret(int(x), 143, 2, 6, VERDE if self.Lv[i] else FUNDO3)
        tela.texto('LIGADO' if lig else 'DESLIGADO', PX0, 156, VERDE if lig else ACO2, tam=17, contorno=PRETO)
        if lig: raio(tela, PX0 + 84, 156)
        tela.texto('(TEMPO ACELERADO)', PX0, 180, ACO2, tam=9)

    def sons(self, fx):
        for t, lig in self.trocas:
            fx.put(fx.clique(1200, .05), self.t0 + t, .5)
        a = 0.0
        for t, lig in self.trocas + [(self.dur, None)]:
            if lig is False or lig is None:
                if lig is None and not self.Lv[-1]: break
                zumbido(fx, self.t0 + a, self.t0 + t, .05)
            a = t


# ============================================================ porta aberta
class Porta(Cena):
    def preparar(self):
        self.G = geladeira()

    def abertura(self, t):
        return ease((t - .5) / 1.2) * (1 - ease((t - 26.8) / 1.0))

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        a = self.abertura(t)
        if VERTICAL: a *= .28
        gelo = suave((t - 17.0) / 8.0)
        G.desenhar(tela, t, s=.4 + t * .4, porta=a, gelo=gelo, vel=22)
        G.calor_fora(tela, t, n=18, rate=.65)
        G.ondas(tela, t)
        if a > .3:
            # o ar frio escorre por baixo, o da cozinha entra por cima
            for i in range(24):
                u = (t * .55 + i / 24) % 1.0
                x = 62 - u * 64 + math.sin(u * 5 + i) * 2
                y = 150 + u * 44 + (i % 3) * 3
                tela.ret(int(x), int(min(y, 196)), 2, 1, MISTURA2 if i % 2 else CIANO)
            for i in range(14):
                u = (t * .4 + i / 14) % 1.0
                x = 4 + u * 120
                y = 30 + (i * 13) % 50 + math.sin(u * 6 + i) * 3
                calor(tela, x, y, int(t * 5 + i) % 2)
                if i % 2 == 0: tela.px(x + 3, y + 2, GAS)              # umidade
        if VERTICAL: return
        # painel
        tela.texto('PORTA', PX0, 8, ACO3, tam=17, contorno=PRETO)
        tela.texto('ABERTA' if a > .05 else 'FECHADA', PX0 + 70, 8, LARANJA if a > .05 else VERDE, tam=17, contorno=PRETO)
        sobe = suave((t - 1.0) / 14.0) * (1 - suave((t - 27.0) / 12.0))
        termometro(tela, PX0 + 10, 36, 50, .55 + .3 * sobe, cor_temp(4 + sobe * 12))
        tela.texto('DENTRO', PX0 + 22, 44, BRANCO, tam=9, contorno=PRETO)
        tela.texto('ESQUENTA' if sobe > .1 and t < 27 else ('VOLTA A ESFRIAR' if t >= 27 else ''), PX0 + 22, 56,
                   LARANJA if t < 27 else MISTURA2, tam=9, contorno=PRETO)
        tela.texto('COMPRESSOR', PX0 + 22, 72, ACO3, tam=9, contorno=PRETO)
        tela.texto('SEM PARAR' if t >= 8.8 else 'LIGADO', PX0 + 22, 82, VERDE, tam=9, contorno=PRETO)
        raio(tela, PX0 + 96, 72)
        if t >= 17.8:
            tela.texto('GELO NO EVAPORADOR', PX0, 102, MISTURA2, tam=9, contorno=PRETO)
            n = int(gelo * 20)
            for j in range(n): floco(tela, PX0 + 4 + j * 7, 116)
        dicas = [(26.8, 'ABRA POUCO E RÁPIDO'), (30.5, 'ESFRIE A COMIDA ANTES'), (35.8, 'DEIXE ESPAÇO ATRÁS')]
        for j, (ta, txt) in enumerate(dicas):
            if t < ta: continue
            y = 134 + j * 22
            tela.ret(PX0, y, 14, 14, VERDE); tela.ret_vazado(PX0, y, 14, 14, PRETO)
            tela.linha(PX0 + 3, y + 7, PX0 + 6, y + 10, PRETO); tela.linha(PX0 + 6, y + 10, PX0 + 11, y + 3, PRETO)
            tela.texto(txt, PX0 + 20, y + 4, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.clique(1500, .04), self.t0 + .5, .4)
        fx.put(fx.chiado(25.0, 300, 2000), self.t0 + 1.0, .06)
        fx.put(fx.clique(900, .06), self.t0 + 27.7, .5)
        zumbido(fx, self.t0, self.t0 + self.dur, .055)


# ============================================================ esfriar a cozinha?
class Esfriar(Cena):
    def preparar(self):
        self.G = geladeira()

    def desenhar(self, tela, t, tg):
        D.fundo_cozinha(tela)
        G = self.G
        a = .28 if VERTICAL else 1.0
        G.desenhar(tela, t, s=t * .45, porta=a * ease(t / 1.0), vel=24)
        forte = 1.0 + .6 * suave((t - 8.8) / 4)
        G.calor_fora(tela, t, n=int(18 * forte), rate=.7, forte=forte)
        G.ondas(tela, t)
        G.calor_dentro(tela, t, n=10, rate=.6)
        for i in range(20):
            u = (t * .55 + i / 20) % 1.0
            x = 58 - u * 58 * a
            y = 150 + u * 44 + (i % 3) * 3
            tela.ret(int(x), int(min(y, 196)), 2, 1, MISTURA2 if i % 2 else CIANO)
        if t >= 18.8:
            u = (t * 2) % 1.0
            for k in range(4):
                calor(tela, 210 + k * 6, 168 - u * 14 - k * 2, int(t * 6 + k) % 2)
            rotulo(tela, 'MOTOR', 246, 178, AMARELO)
        if VERTICAL: return
        tela.texto('A COZINHA', PX0, 8, ACO3, tam=17, contorno=PRETO)
        sobe = suave((t - 8.8) / 20.0)
        termometro(tela, PX0 + 10, 36, 50, .55 + .3 * sobe, cor_temp(25 + 15 * sobe))
        tela.texto('ESQUENTA' if t >= 18.8 else ('?' if t < 8.8 else 'NÃO ESFRIA'), PX0 + 24, 50,
                   LARANJA if t >= 18.8 else BRANCO, tam=17, contorno=PRETO)
        if t >= 8.8:
            tela.texto('FRIO QUE SAI NA FRENTE', PX0, 104, MISTURA2, tam=9, contorno=PRETO)
            tela.ret(PX0, 116, 80, 8, PRETO); tela.ret(PX0 + 1, 117, 78, 6, CIANO)
            tela.texto('CALOR QUE SAI ATRÁS', PX0, 132, LARANJA, tam=9, contorno=PRETO)
            tela.ret(PX0, 144, 80, 8, PRETO); tela.ret(PX0 + 1, 145, 78, 6, LARANJA)
        if t >= 18.8:
            u = ease((t - 18.8) / 1.0)
            w = int(40 * u)
            tela.ret(PX0 + 80, 144, w + 1, 8, PRETO); tela.ret(PX0 + 80, 145, w, 6, VERMELHO)
            tela.texto('+ CALOR DO MOTOR', PX0, 160, VERMELHO, tam=9, contorno=PRETO)
            tela.texto('SALDO: MAIS CALOR', PX0, 182, AMARELO, tam=17 if False else 9, contorno=PRETO)

    def sons(self, fx):
        zumbido(fx, self.t0, self.t0 + self.dur, .055)
        fx.put(fx.clique(1500, .04), self.t0 + .1, .3)


# ============================================================ resumo
class Resumo(Cena):
    CX = [64, 178, 292, 406]
    YP = 92

    def preparar(self):
        xs = [12, 121, 235, 349, 462]
        trs = []
        for k in range(4):
            pts = [(xs[k], self.YP), (xs[k + 1], self.YP)]
            if k == 3:
                pts += [(466, self.YP), (466, 168), (6, 168), (6, self.YP), (12, self.YP)]
            trs.append(pts)
        self.trajs = [D.Trajeto(p) for p in trs]
        self.tubos = [D.Tubo(p, 3) for p in trs]
        self.tpx = []
        for k, tb in enumerate(self.tubos):
            Tv, _, Vv = D.estado_vet(np.round(k + np.clip(tb.U, 0, .9999), 3))
            self.tpx.append((Tv, Vv))

    def s(self, t): return .1 + t * .3

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        s = self.s(t)
        T, P, vap, k_at = estado(s)
        nomes = ['1 COMPRIME', '2 SOLTA CALOR', '3 BAIXA PRESSÃO', '4 FERVE']
        for k, (nome, cor) in enumerate(ETAPAS):
            x = self.CX[k] - 50
            aceso = k == k_at
            painel(tela, x, 22, 100, 118, borda=cor if aceso else ACO1)
            self._icone(tela, k, self.CX[k], 56, t, aceso)
            tela.texto(nome, self.CX[k], 108, cor if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(nomes[k], self.CX[k], 122, BRANCO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
        for k, tb in enumerate(self.tubos):
            tb.desenhar(tela, self.tpx[k][0], self.tpx[k][1], t, vel=20)
        kk = int(s % 4); u = s % 1.0
        x, y = self.trajs[kk].em(u)
        parcela(tela, x, y, T, vap, t, r=4)
        # calor entrando e saindo
        if t > 17.8:
            for j in range(6):
                v = (t * .5 + j / 6) % 1.0
                calor(tela, self.CX[3] - 30 + j * 12, 190 - v * 18, int(t * 4 + j) % 2)
                calor(tela, self.CX[1] - 30 + j * 12, 18 - v * 14 + 0, int(t * 4 + j) % 2)
            rotulo(tela, 'CALOR ENTRA', self.CX[3], 194, CHAMA1, centro=True)
            rotulo(tela, 'CALOR SAI', self.CX[1] + 60, 6, LARANJA, centro=False)
        txt = f"ETAPA {k_at + 1} DE 4   {D.fmt_bar(P)}   {D.fmt_temp(T)}"
        tela.texto(txt, W // 2, 176, cor_temp(T), tam=9, centro=True, contorno=PRETO)

    def _icone(self, tela, k, cx, cy, t, aceso):
        if k == 0:
            tela.disco(cx, cy + 4, 16, PRETO); tela.ret(cx - 17, cy + 4, 34, 14, PRETO)
            tela.disco(cx, cy + 4, 14, ACO1); tela.ret(cx - 15, cy + 4, 30, 12, ACO1)
            tela.ret(cx - 10, cy - 6, 6, 1, ACO3)
            if aceso: raio(tela, cx + 2, cy - 2)
        elif k == 1:
            for j in range(5):
                y = cy - 12 + j * 6
                tela.ret(cx - 18, y, 36, 3, PRETO); tela.ret(cx - 17, y + 1, 34, 1, LARANJA)
            if aceso:
                for j in range(4):
                    v = (t * .8 + j / 4) % 1.0
                    calor(tela, cx - 12 + j * 8, cy - 16 - v * 10)
        elif k == 2:
            for j in range(40):
                f = j / 40
                ph = f * math.pi * 2 * 3
                x = cx - 18 + 36 * f + 5 * math.sin(ph); y = cy - 8 * math.cos(ph)
                tela.ret(int(x), int(y), 2, 2, VERDE if aceso else ACO2)
        else:
            tela.ret(cx - 18, cy - 14, 36, 30, PRETO); tela.ret(cx - 17, cy - 13, 34, 28, ACO1)
            for j in range(4):
                tela.ret(cx - 14, cy - 10 + j * 7, 28, 2, MISTURA)
            for j in range(3):
                floco(tela, cx - 10 + j * 10, cy - 18 + int(math.sin(t * 2 + j) * 2))

    def sons(self, fx):
        for k in range(4):
            tt = (k + 1 - .1) / .3
            while tt < self.dur:
                fx.put(fx.blip(72 + k * 2, .1), self.t0 + tt, .12)
                tt += 4 / .3


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 30, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 52, AMARELO, tam=9, centro=True, contorno=PRETO)
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 76 + k * 40
                tela.ret(x, 100, 30, 30, cor); tela.ret_vazado(x, 100, 30, 30, PRETO)
                tela.texto(str(k + 1), x + 12, 111, PRETO, tam=9)
            u = (t * .5) % 1.0
            xp = W // 2 - 76 + u * 150
            T = estado(u * 4)[0]
            parcela(tela, xp, 146, T, .5, t, r=4)
            for k in range(10):
                floco(tela, 40 + k * 44, 180 + int(math.sin(t * 2 + k) * 3))

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, cozinha=Cozinha, calor=Calor, evaporar=Evaporar, pecas=Pecas,
             fluido=Fluido, etapa1=Etapa1, etapa2=Etapa2, etapa3=Etapa3, etapa4=Etapa4, ciclo=Ciclo,
             termostato=Termostato, porta=Porta, esfriar=Esfriar, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep05_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        so = sys.argv[3:] or None
        ts = []
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else 2
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
