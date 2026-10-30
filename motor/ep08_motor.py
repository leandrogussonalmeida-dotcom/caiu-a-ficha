#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep08 — Como um videogame desenha um quadro (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

O protagonista é UM quadro do jogo inventado (o quadro NQ, em que o herói
aperta o pulo rumo a uma plataforma com moeda) e o cronômetro dos 16,7 ms
dele, no painel da direita. O laço lê o controle, atualiza a física e
desenha: do jeito 2D (tiles, sprites, camadas) e do jeito 3D (triângulos,
vértices, rasterização, z-buffer); depois a imagem vai para o framebuffer
e para a tela.

    python3 ep08_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep08_motor.py <saida.mp4> fisica tiles     # só esses capítulos (teste)
    python3 ep08_motor.py --folha <saida.png> [ids]    # 2 quadros por capítulo (FR=.3,.8)
"""
import math, os, sys
import numpy as np
import pixelengine as PX
import longo as LG
import ep08_desenho as D                      # registra a paleta 'ep08' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, FUNDO, FUNDO2, FUNDO3,
                   TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE,
                   PRETO, ROSA, ROXO, CHAMA0, CHAMA1, BRASA)
from ep08_desenho import (SIM, GW, GH, TRANSP, dec, milhar, rotulo, centro_preso, moldura, colar, cronometro,
                          ORCAMENTO, CINZA, OURO1, OURO2, GRAMA1, GRAMA2, ROUPA1, ROUPA2, PEDRA1, PEDRA2,
                          CEU2, CEU3, PELE, LARANJA as _LAR)
import ritmo_marca as RM
from ep08_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2608, 50
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
PX0 = 304                     # coluna do painel da direita
VX0, VY0 = 8, 10              # canto do jogo ampliado 2x no palco (280 x 156)
CLIP = (0, 0, 298, PALCO_H)


def lerp(a, b, u): return a + (b - a) * u
def clamp(u): return max(0.0, min(1.0, u))


def _escolher_quadro():
    """O quadro protagonista: o herói aperta o pulo no chão, pega a moeda e
    pousa numa plataforma nos quadros seguintes."""
    f = 1500
    while True:
        f = SIM.quadro_de_pulo(f + 1)
        pegou = [q for (v, i), q in SIM.moedas_de.items() if f < q <= f + 45]
        pousa = [k for k in range(1, 50) if SIM.chao[f + k] and SIM.y[f + k] < 50]
        if pegou and pousa and SIM.y[f - 1] >= 63.9:
            return f, min(pegou), f + pousa[0]


NQ, NQ_MOEDA, NQ_POUSO = _escolher_quadro()
JOGO = D.Jogo()


def ms_de(t, dur, a, b):
    return lerp(a, b, clamp(t / dur))


def escurecer(tela, x, y, w, h, fase=0):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy + fase) % 2 == 0] = FUNDO


def seta(tela, x0, y0, x1, y1, cor, esp=2, ponta=5):
    """Seta grossa com ponta, de (x0, y0) para (x1, y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * ponta, y1 - uy * ponta
    linha_grossa(tela, x0, y0, bx, by, esp + 2, PRETO)
    linha_grossa(tela, x0, y0, bx, by, esp, cor)
    nx, ny = -uy, ux
    poligono(tela, [(x1 + ux, y1 + uy), (bx + nx * (ponta + 1), by + ny * (ponta + 1)),
                    (bx - nx * (ponta + 1), by - ny * (ponta + 1))], PRETO)
    poligono(tela, [(x1, y1), (bx + nx * ponta, by + ny * ponta), (bx - nx * ponta, by - ny * ponta)], cor)


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

    def fundo(self, tela, t):
        """Parede escura com uma grade de tiles muito apagada."""
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(8, PALCO_H, 16): tela.ret(0, y, W, 1, FUNDO2)
        if not VERTICAL:
            tela.ret(298, 0, 1, PALCO_H, TRACO)
            tela.ret(299, 0, W - 299, PALCO_H, FUNDO)

    def jogo(self, tela, f, camadas=None, x=VX0, y=VY0, esc=2, moldura=True, **kw):
        b = JOGO.quadro(f, camadas, **kw)
        if moldura: D.moldura(tela, x, y, GW * esc, GH * esc)
        colar(tela, b, x, y, esc, clip=CLIP, transp=False)
        return b

    def cron(self, tela, ms, t, quadro=NQ, x=PX0, lista=True, titulo=None, w=160):
        if VERTICAL: return 0
        return cronometro(tela, x, 6, ms, quadro, w=w, lista=lista, titulo=titulo, t=t)

    def ptxt(self, tela, txt, y, cor=ACO3, tam=9, x=PX0):
        if not VERTICAL: tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def heroi_tela(f, x=VX0, y=VY0, esc=2):
    """Caixa do herói (hitbox) no quadro f, em pixels do palco."""
    cam = math.floor(D.camera_de(f))
    hx = x + (math.floor(SIM.x[f]) - cam) * esc
    hy = y + (SIM.y[f] - D.HEROI_H) * esc
    return hx, hy, D.HEROI_W * esc, D.HEROI_H * esc


def mundo_tela(xw, yw, f, x=VX0, y=VY0, esc=2):
    cam = math.floor(D.camera_de(f))
    return x + (xw - cam) * esc, y + yw * esc


# ============================================================ 0 gancho
class Gancho(Cena):
    def f(self, t): return NQ - 360 + int(min(t, 6.0) * 60)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        f = self.f(t)
        self.jogo(tela, f)
        if t < 6.0:
            self.ptxt(tela, 'O JOGO RODANDO', 10)
            self.ptxt(tela, '60 QUADROS', 24, BRANCO, 17)
            self.ptxt(tela, 'POR SEGUNDO', 44, BRANCO, 17)
            self.ptxt(tela, f'QUADRO Nº {milhar(f)}', 72, AMARELO, 9)
            if not VERTICAL:
                for k in range(8):                    # fita de quadros passando
                    x = PX0 + k * 21 - (f * 7) % 21
                    if PX0 - 2 <= x < 450:
                        tela.ret(x, 90, 18, 12, FUNDO3); tela.ret(x + 1, 91, 16, 10, CEU2)
                        tela.ret(x + 1, 98, 16, 3, GRAMA1)
        else:
            u = t - 6.0
            self.cron(tela, 0.0, t)
            if int(u * 3) % 2 == 0:
                painel(tela, VX0 + 104, VY0 + 64, 72, 26, borda=AMARELO)
                tela.texto('PAUSA', VX0 + 140, VY0 + 70, AMARELO, tam=17, centro=True, contorno=PRETO)
            hx, hy, hw, hh = heroi_tela(f)
            tela.ret_vazado(hx - 3, hy - 3, hw + 6, hh + 6, AMARELO)

    def sons(self, fx):
        for k in range(12):
            fx.put(fx.blip(64 + (k % 4) * 3, .05), self.t0 + .3 + k * .5, .07)
        for q in range(NQ - 360, NQ):
            if SIM.pulo[q]: fx.put(fx.blip(76, .08), self.t0 + (q - NQ + 360) / 60, .12)
        fx.put(fx.sino(79), self.t0 + 6.0, .35)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        tela.buf[:, 298:] = FUNDO
        for x in range(0, W, 16): tela.ret(x, 0, 1, H, FUNDO2)
        # a fase passando embaixo, sem o placar (4 telas pequenas lado a lado)
        f = NQ - 200 + int(t * 60)
        b = JOGO.quadro(f, D.CAMADAS[:6])
        for k in range(4):
            colar(tela, b, k * 140 - int(t * 20) % 140, H - 78, 1, clip=(0, 0, W, H), transp=False)
        tela.ret(0, H - 79, W, 1, PRETO)
        n = int(t / .04)
        for j, linha in enumerate(("COMO UM VIDEOGAME", "DESENHA UM QUADRO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 18)]
            tela.texto(vis, W // 2 - larg // 2, 24 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.4:
            w = tela.largura_texto("FEITO DE PIXELS", 17) + 20
            painel(tela, W // 2 - w // 2, 98, w, 24, borda=AMARELO)
            tela.texto("FEITO DE PIXELS", W // 2, 104, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.2:
            u = min(1.0, (t - 2.2) / 3.0)
            tela.texto(f"{dec(u * ORCAMENTO)} MS", W // 2, 136, CIANO, tam=17, centro=True, contorno=PRETO)
            tela.ret(W // 2 - 81, 157, 162, 8, PRETO)
            tela.ret(W // 2 - 80, 158, 160 * u, 6, CIANO)

    def sons(self, fx):
        fx.put(fx.sino(84), self.t0 + 1.4, .3)
        fx.put(fx.blip(88, .1), self.t0 + 5.2, .2)


# ============================================================ 2 o jogo
class Jogo(Cena):
    def f(self, t):
        if t < 15.0: return NQ - 1500 + int(t * 60)
        return NQ - 1500 + 900 + int((t - 15.0) * 2)           # câmera lenta: 2 quadros por segundo

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        f = self.f(t)
        self.jogo(tela, f)
        # fita: os últimos quadros, parados, um atrás do outro
        if 7.8 <= t:
            n = 6
            for k in range(n):
                q = f - (n - 1 - k) * (6 if t < 15 else 1)
                b = JOGO.quadro(q)[::3, ::3]
                x = VX0 + k * 48
                if VERTICAL and x > 170: continue
                tela.ret(x - 1, 171, b.shape[1] + 2, b.shape[0] + 2, AMARELO if k == n - 1 else ACO1)
                colar(tela, b, x, 172, 1, clip=CLIP, transp=False)
        if VERTICAL: return
        self.ptxt(tela, 'QUADROS POR SEGUNDO', 10)
        self.ptxt(tela, '60', 22, BRANCO, 26)
        self.ptxt(tela, f'QUADRO Nº {milhar(f)}', 52, AMARELO, 9)
        if t >= 15.0:
            painel(tela, PX0 - 4, 70, 168, 22, borda=CIANO)
            tela.texto('CÂMERA LENTA', PX0 + 80, 76, CIANO, tam=17, centro=True, contorno=PRETO)
        if t >= 22.2:
            tela.texto('1 S / 60 =', PX0, 106, BRANCO, tam=17, contorno=PRETO)
            tela.texto('16,7 MS', PX0, 128, AMARELO, tam=26, contorno=PRETO)
            tela.texto('POR QUADRO', PX0, 158, BRANCO, tam=17, contorno=PRETO)
            u = ((t - 22.2) % .5) / .5
            tela.ret(PX0, 184, 160, 8, FUNDO2)
            tela.ret(PX0, 184, 160 * u, 8, AMARELO)
            tela.texto('ORÇAMENTO DE CADA QUADRO', PX0, 196, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for q in range(NQ - 1500, NQ - 600):
            if SIM.pulo[q]: fx.put(fx.blip(76, .08), self.t0 + (q - NQ + 1500) / 60, .1)
        for k in range(30):
            fx.put(fx.clique(2500, .02), self.t0 + 15.0 + k * .5, .2)


# ============================================================ 3 o laço
CAIXAS = [('1 LER O CONTROLE', -90, CIANO), ('2 ATUALIZAR', 30, VERDE), ('3 DESENHAR', 150, AMARELO)]
LACO_C, LACO_R = (148, 112), (100, 80)


def icone(tela, k, x, y, t):
    """Ícones de 16 px: controle, engrenagem (contas), pincel."""
    if k == 0:
        tela.ret(x, y + 4, 16, 9, PRETO); tela.ret(x + 1, y + 5, 14, 7, ACO2)
        tela.ret(x + 3, y + 7, 4, 1, PRETO); tela.ret(x + 4, y + 6, 1, 3, PRETO)
        tela.ret(x + 11, y + 6, 2, 2, VERDE); tela.ret(x + 9, y + 8, 2, 2, VERMELHO)
    elif k == 1:
        a = t * 2
        pts = []
        for j in range(16):
            r = 7.5 if j % 2 == 0 else 5.5
            b = a + j * math.pi / 8
            pts.append((x + 8 + math.cos(b) * r, y + 8 + math.sin(b) * r))
        poligono(tela, pts, VERDE); tela.disco(x + 8, y + 8, 2.5, PRETO)
    else:
        linha_grossa(tela, x + 3, y + 15, x + 11, y + 4, 3, ACO3)
        tela.disco(x + 12, y + 3, 3, AMARELO); tela.px(x + 11, y + 2, BRANCO)
        tela.ret(x + 1, y + 14, 3, 2, AMARELO)


class Laco(Cena):
    VOLTA = 7.4

    def ang(self, t):
        """Ângulo do ponto que dá a volta (graus, -90 = caixa 1)."""
        if t < 7.4: return -90 + t * 360 * 6               # rápido (borrado)
        if t < 22.2: return -90 + (t - 7.4) / self.VOLTA * 360
        return -90.0

    def f(self, t):
        if t < 7.4: return NQ - 120 + int(t * 12)
        if t < 22.2: return NQ - 30 + int((t - 7.4) / self.VOLTA)
        return NQ

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cx, cy = LACO_C
        rx, ry = LACO_R
        # trilho da volta
        for k in range(120):
            a = math.radians(k * 3)
            tela.ret(cx + math.cos(a) * rx - 1, cy + math.sin(a) * ry - 1, 2, 2, TRACO)
        rapido = t < 7.4
        if rapido:
            for k in range(0, 360, 4):
                a = math.radians(k)
                tela.ret(cx + math.cos(a) * rx - 1, cy + math.sin(a) * ry - 1, 3, 3, BRANCO if (k // 4 + int(t * 30)) % 3 else CIANO)
        # mini jogo no meio
        f = self.f(t)
        self.jogo(tela, f, x=cx - 70, y=cy - 58, esc=1)
        a = self.ang(t)
        # o ponto que corre (por baixo das caixas: a caixa acesa mostra onde ele está)
        if not rapido:
            r = math.radians(a)
            px_, py_ = cx + math.cos(r) * rx, cy + math.sin(r) * ry
            for j in range(1, 7):
                rr = math.radians(a - j * 4)
                tela.ret(cx + math.cos(rr) * rx - 1, cy + math.sin(rr) * ry - 1, 3, 3, AMARELO if j < 3 else LARANJA)
            tela.disco(px_, py_, 4, PRETO); tela.disco(px_, py_, 3, BRANCO)
        ativa = int(((a + 90) % 360) // 120)
        for k, (nome, ang, cor) in enumerate(CAIXAS):
            r = math.radians(ang)
            bx, by = cx + math.cos(r) * rx, cy + math.sin(r) * ry
            w = 118
            x0 = int(bx - w / 2)
            acesa = (not rapido) and k == ativa and t < 22.2 or (t >= 22.2 and k == 0)
            painel(tela, x0, by - 14, w, 28, borda=cor if acesa else TRACO, fundo=PRETO)
            icone(tela, k, x0 + 5, by - 8, t)
            tela.texto(nome, x0 + 25, by - 3, cor if acesa else ACO3, tam=9, contorno=PRETO)
        if VERTICAL: return
        if t < 22.2:
            self.ptxt(tela, 'UMA VOLTA = UM QUADRO', 10)
            self.ptxt(tela, 'CÂMERA LENTA' if not rapido else 'VELOCIDADE REAL', 24, CIANO if not rapido else AMARELO, 17)
            if rapido:
                self.ptxt(tela, '60 VOLTAS', 50, BRANCO, 17)
                self.ptxt(tela, 'POR SEGUNDO', 70, BRANCO, 17)
            else:
                self.ptxt(tela, 'VOLTAS:', 50, ACO3)
                self.ptxt(tela, str(int((t - 7.4) / self.VOLTA) + 1), 62, BRANCO, 26)
            self.ptxt(tela, f'QUADRO Nº {milhar(f)}', 100, AMARELO)
        else:
            self.cron(tela, 0.0, t)
            self.ptxt(tela, 'ESTE É O NOSSO QUADRO.', 150, BRANCO)
            self.ptxt(tela, 'O RELÓGIO COMEÇA EM 0.', 162, ACO3)

    def sons(self, fx):
        for k in range(2):
            for j in range(3):
                fx.put(fx.blip((72, 76, 79)[j], .08), self.t0 + 7.4 + k * self.VOLTA + j * self.VOLTA / 3, .16)
        fx.put(fx.sino(84), self.t0 + 22.4, .25)


# ============================================================ 4 o controle
BOTOES = [('dir', 'DIREITA'), ('esq', 'ESQUERDA'), ('cima', 'CIMA'), ('baixo', 'BAIXO'), ('pulo', 'PULO'),
          ('acao', 'AÇÃO')]


class Controle(Cena):
    def apertados(self, t):
        s = {'dir'}
        if t >= 13.0: s.add('pulo')
        return s

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 0.0, 0.5)
        ap = self.apertados(t)
        cx, cy, e = 148, 92, 1.75
        # cabo até o painel
        if not VERTICAL:
            pts = [(cx, cy - 40 * e + 4), (cx, 14), (296, 14)]
            for (a, b), (c, d) in zip(pts, pts[1:]):
                linha_grossa(tela, a, b, c, d, 3, PRETO); linha_grossa(tela, a, b, c, d, 1, ACO2)
            for k in range(3):                      # pulsos de leitura descendo pelo cabo
                u = (t * .9 + k / 3) % 1.0
                tela.ret(296 - u * (296 - cx) - 1, 13, 3, 3, CIANO)
        else:
            linha_grossa(tela, cx, cy - 40 * e + 4, cx, 0, 3, PRETO); linha_grossa(tela, cx, cy - 40 * e + 4, cx, 0, 1, ACO2)
        pos = D.controle(tela, cx, cy, ap, t, e)
        # dedos
        dx, dy = pos['dir']
        tela.disco(dx + 4, dy + 3, 7, PRETO); tela.disco(dx + 4, dy + 3, 6, D.PELE); tela.disco(dx + 6, dy + 5, 3, D.PELE2)
        px_, py_ = pos['pulo']
        desce = 0 if t >= 13.0 else 6 * (1 - clamp((t - 11.5) / 1.5)) + 3
        tela.disco(px_ + 3, py_ + 3 - (-desce), 7, PRETO); tela.disco(px_ + 3, py_ + 3 + desce, 6, D.PELE)
        tela.disco(px_ + 5, py_ + 5 + desce, 3, D.PELE2)
        # leitura: um quadrado passa por cada botão, um de cada vez
        k = int(t * 3) % len(BOTOES)
        nome = BOTOES[k][0]
        bx, by = pos[nome]
        tela.ret_vazado(bx - 8, by - 8, 17, 17, CIANO)
        tela.ret_vazado(bx - 9, by - 9, 19, 19, PRETO)
        if not VERTICAL:
            rotulo(tela, 'CRUZ', 30, 150, pos['baixo'][0], pos['baixo'][1] + 5, ACO3)
            rotulo(tela, 'BOTÃO DE PULO', 196, 152, pos['pulo'][0] + 2, pos['pulo'][1] + 6, VERDE if 'pulo' in ap else ACO3)
        else:
            tela.texto('PULO' if 'pulo' in ap else '', 150, 140, VERDE, tam=17, contorno=PRETO)
        if VERTICAL: return
        y = self.cron(tela, ms, t)
        self.ptxt(tela, 'O QUE O JOGO LEU:', y + 2)
        for j, (n, rot) in enumerate(BOTOES):
            yy = y + 14 + j * 11
            lido = (t >= 2.0) and (j < int(t * 3) % len(BOTOES) or t > 4)
            on = n in ap
            tela.texto(rot, PX0, yy, BRANCO if lido else ACO1, tam=9, contorno=PRETO)
            if lido:
                tela.ret(PX0 + 64, yy + 1, 6, 6, VERDE if on else FUNDO3)
                tela.texto('APERTADO' if on else 'SOLTO', PX0 + 74, yy, VERDE if on else ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(int(self.dur * 3)):
            fx.put(fx.clique(5000, .01), self.t0 + k / 3, .1)
        fx.put(fx.clique(1500, .04), self.t0 + 13.0, .5)
        fx.put(fx.blip(79, .1), self.t0 + 13.05, .2)


# ============================================================ 5 a física
class Fisica(Cena):
    def k_fantasma(self, t):
        """Quadro futuro onde está o 'fantasma' do herói."""
        if t < 15.2: return 0
        n = NQ_POUSO - NQ + 10
        if t < 22.6: return min(n, int((t - 15.2) * 4))
        return int(((t - 22.6) * 8) % (n + 12))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 0.5, 3.0)
        f = NQ
        self.jogo(tela, f)
        # nada desenhado ainda: o mundo vira números e caixas
        escurecer(tela, VX0, VY0, 280, 156); escurecer(tela, VX0, VY0, 280, 156, 1)
        escurecer(tela, VX0, VY0, 280, 156)
        cam = math.floor(D.camera_de(f))
        c0 = int(cam // 8)
        for r in range(D.MH):
            for j in range(GW // 8 + 2):
                if D.MAPA[r, (c0 + j) % D.MW]:
                    x = VX0 + ((c0 + j) * 8 - cam) * 2
                    y = VY0 + r * 16
                    if x < VX0 - 16 or x > VX0 + 280: continue
                    x0, x1 = max(VX0, x), min(VX0 + 280, x + 16)
                    y1 = min(VY0 + 156, y + 16)
                    if x1 > x0:
                        tela.ret(x0, y, x1 - x0, 1, ACO1); tela.ret(x0, y, 1, y1 - y, ACO1)
        # moedas e herói como caixas
        fut = NQ_MOEDA if t < 36.4 else NQ_MOEDA - 1
        volta = int(SIM.x[f] // D.LARG_FASE)
        moeda_alvo = None
        for v in (volta, volta + 1):
            for i, (mx, my) in enumerate(D.MOEDAS):
                q = SIM.moedas_de.get((v, i))
                if q is not None and q <= f: continue
                x, y = mundo_tela(mx + v * D.LARG_FASE - 3, my - 4, f)
                if VX0 <= x < VX0 + 270:
                    alvo = q == NQ_MOEDA
                    if alvo: moeda_alvo = (x, y)
                    tela.ret_vazado(x, y, 12, 16, OURO2 if alvo else OURO1)
        hx, hy, hw, hh = heroi_tela(f)
        k = self.k_fantasma(t)
        # pontos do pulo: onde o herói vai estar em cada quadro seguinte
        if t >= 15.2:
            for j in range(0, k + 1):
                q = f + j
                xx, yy = mundo_tela(SIM.x[q] + 3, SIM.y[q] - 6, f)
                if xx < VX0 + 278:
                    tela.ret(xx - 1, yy - 1, 3, 3, PRETO); tela.px(xx, yy, AMARELO if j % 10 else BRANCO)
            q = f + k
            gx, gy = mundo_tela(SIM.x[q], SIM.y[q] - D.HEROI_H, f)
            if k > 0:
                tela.ret_vazado(gx, gy, hw, hh, ACO2)
                D.carimbo(tela, np.repeat(np.repeat(D.heroi_sprite(q), 2, 0), 2, 1), gx - 2, gy) if t >= 22.6 else None
                if t >= 30.0 and moeda_alvo and q >= NQ_MOEDA - 1 and q <= NQ_MOEDA + 6:
                    tela.ret_vazado(gx - 2, gy - 2, hw + 4, hh + 4, AMARELO)
                    tela.texto('ENCOSTOU!', gx + 14, gy - 14, AMARELO, tam=9, contorno=PRETO)
                if t >= 30.0 and q >= NQ_POUSO and q <= NQ_POUSO + 8:
                    tela.ret(gx - 4, gy + hh, hw + 8, 2, VERDE)
                    tela.texto('PISOU', gx + 16, gy + hh - 4, VERDE, tam=9, contorno=PRETO)
        # o herói de agora
        D.carimbo(tela, np.repeat(np.repeat(D.heroi_sprite(f), 2, 0), 2, 1), hx - 2, hy)
        tela.ret_vazado(hx - 1, hy - 1, hw + 2, hh + 2, CIANO)
        if t >= 7.8:
            L = 3.2 * 10
            seta(tela, hx + hw + 6, hy + hh // 2, hx + hw + 6, hy + hh // 2 - L, AMARELO)
            if not VERTICAL: tela.texto('VELOCIDADE', hx + hw + 12, hy - 12, AMARELO, tam=9, contorno=PRETO)
        if t >= 15.2:
            seta(tela, hx - 8, hy + 2, hx - 8, hy + 22, LARANJA)
            if not VERTICAL: tela.texto('GRAVIDADE', hx - 66, hy + 10, LARANJA, tam=9, contorno=PRETO)
        if t >= 30.0 and not VERTICAL:
            tela.texto('CAIXAS INVISÍVEIS (HITBOX)', VX0 + 4, VY0 + 160, CIANO, tam=9, contorno=PRETO)
        if VERTICAL: return
        y = self.cron(tela, ms, t)
        self.ptxt(tela, 'NO NOSSO JOGO, POR QUADRO:', y + 2)
        q = f + (k if t >= 15.2 else 0)
        vy = -SIM.vy[q]
        self.ptxt(tela, f"ALTURA: {dec(64 - SIM.y[q])} PX", y + 14, BRANCO)
        if SIM.chao[q] and q != NQ: self.ptxt(tela, 'PARADO NO CHÃO', y + 26, VERDE)
        else: self.ptxt(tela, ('SOBE ' if vy > 0 else 'DESCE ') + f"{dec(abs(vy), 2)} PX", y + 26, AMARELO)
        self.ptxt(tela, 'GRAVIDADE: -0,18 A CADA', y + 38, LARANJA)
        self.ptxt(tela, 'QUADRO', y + 48, LARANJA)
        if t >= 15.2:
            self.ptxt(tela, f'QUADRO +{k}', y + 62, ACO3)
        if t >= 36.4:
            self.ptxt(tela, 'MOEDAS +1', y + 62, OURO2, 17)

    def sons(self, fx):
        fx.put(fx.blip(72, .1), self.t0 + 7.8, .2)
        for j in range(NQ_POUSO - NQ + 11):
            fx.put(fx.clique(3500, .01), self.t0 + 15.2 + j / 4, .06)
        fx.put(fx.sino(88), self.t0 + 36.4, .35); fx.put(fx.sino(93), self.t0 + 36.55, .3)


# ============================================================ 6 tiles
class Tiles(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 3.0, 6.0)
        f = NQ
        cam = math.floor(D.camera_de(f))
        if t < 7.2:
            self.jogo(tela, f)
        else:
            nt = None if t > 14.0 else int((t - 7.2) * 6)
            moldura(tela, VX0, VY0, 280, 156)
            tela.ret(VX0, VY0, 280, 156, PRETO)
            dither(tela, VX0, VY0, 280, 156, PRETO, FUNDO2)
            b = JOGO.quadro(f, ['tiles'], n_tiles=nt)
            colar(tela, b, VX0, VY0, 2, clip=(VX0, VY0, VX0 + 280, VY0 + 156))
            # grade dos tiles
            off = (cam % 8) * 2
            for x in range(VX0 - off, VX0 + 281, 16):
                if x >= VX0: tela.ret(x, VY0, 1, 156, FUNDO3)
            for y in range(VY0, VY0 + 157, 16): tela.ret(VX0, y, 280, 1, FUNDO3)
            if nt is not None:                  # o tile sendo copiado agora
                c0 = int(cam // 8)
                cheios = [(r, j) for r in range(D.MH) for j in range(GW // 8 + 2) if D.MAPA[r, (c0 + j) % D.MW]]
                if nt < len(cheios):
                    r, c = cheios[nt]
                    x, y = VX0 + c * 16 - off, VY0 + r * 16
                    tela.ret_vazado(x - 2, y - 2, 20, 20, AMARELO)
                    tid = int(D.MAPA[r, (c0 + c) % D.MW])
                    if not VERTICAL:            # de onde ele vem: o tile da lista à direita
                        tela.linha(x + 18, y + 8, PX0 + tid * 40 + 12, 127, AMARELO)
            if t >= 21.6:                       # o mapa é uma tabela de números
                c0 = int(cam // 8)
                for r in range(D.MH):
                    for j in range(GW // 8 + 2):
                        x = VX0 + j * 16 - off
                        y = VY0 + r * 16
                        if x < VX0 or x + 12 > VX0 + 280 or y + 12 > VY0 + 156: continue
                        tid = D.MAPA[r, (c0 + j) % D.MW]
                        tela.texto(str(tid), x + 6, y + 5, BRANCO if tid else ACO1, tam=9, contorno=PRETO)
            if t >= 28.8:
                c0 = int(cam // 8)
                j = next(j for j in range(2, 12) if D.MAPA[8, (c0 + j) % D.MW] == 1)
                x, y = VX0 + j * 16 - off, VY0 + 8 * 16
                tela.ret_vazado(x - 2, y - 2, 20, 20, AMARELO)
                if VERTICAL:
                    tela.texto('8 X 8 PIXELS', 90, 186, AMARELO, tam=9, contorno=PRETO, centro=True)
                else:
                    tela.linha(x + 8, y - 3, x + 8, VY0 + 100, AMARELO)
                    tela.linha(x + 8, VY0 + 100, PX0 + 8, VY0 + 100, AMARELO)
                    tela.linha(PX0 + 8, VY0 + 100, PX0 + 8, 114, AMARELO)
        if VERTICAL: return
        y = self.cron(tela, ms, t)
        if t < 28.8:
            self.ptxt(tela, 'OS TILES DESTA FASE:', y + 2)
            for k in range(4):
                x = PX0 + k * 40
                tela.ret(x - 1, y + 15, 26, 26, PRETO)
                if k == 0: dither(tela, x, y + 16, 24, 24, FUNDO2, PRETO)
                else: colar(tela, D.TILES[k], x, y + 16, 3, clip=(0, 0, W, PALCO_H))
                tela.texto(str(k), x + 9, y + 44, AMARELO, tam=9, contorno=PRETO)
            if t >= 14.4:
                c0 = int(math.floor(D.camera_de(NQ)) // 8)
                n_cheios = sum(1 for r in range(D.MH) for j in range(GW // 8 + 2) if D.MAPA[r, (c0 + j) % D.MW])
                self.ptxt(tela, f'TILES COPIADOS: {n_cheios}', y + 58, BRANCO)
                self.ptxt(tela, 'DESENHOS DIFERENTES: 3', y + 70, AMARELO)
        else:
            T = D.TILES[1]
            x0, y0 = PX0 + 10, y + 4
            tela.ret(x0 - 1, y0 - 1, 8 * 9 + 1, 8 * 9 + 1, PRETO)
            for j in range(8):
                for i in range(8):
                    tela.ret(x0 + i * 9, y0 + j * 9, 8, 8, T[j, i])
            tela.texto('8 X 8 =', x0 + 80, y0 + 20, BRANCO, tam=9, contorno=PRETO)
            tela.texto('64 PIXELS', x0 + 80, y0 + 32, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(40):
            fx.put(fx.clique(3000 + (k % 6) * 300, .012), self.t0 + 7.2 + k / 6, .12)
        fx.put(fx.sino(76), self.t0 + 21.6, .2)
        fx.put(fx.sino(81), self.t0 + 28.8, .25)


# ============================================================ 7 camadas
ORDEM = [('ceu', 'CÉU'), ('nuvens', 'NUVENS'), ('montanhas', 'MONTANHAS'), ('morros', 'MORROS'),
         ('tiles', 'TILES'), ('sprites', 'SPRITES'), ('placar', 'PLACAR')]


class Camadas(Cena):
    T_PILHA = 7.6

    def canto(self, k, u=0.0):
        """Canto da camada k na pilha (u = 1: pilha fechada)."""
        if VERTICAL: x, y = 6 + k * 6, 92 - k * 13
        else: x, y = 10 + k * 22, 122 - k * 17
        x0, y0 = (6 + 3 * 6, 92 - 3 * 13) if VERTICAL else (10 + 3 * 22, 122 - 3 * 17)
        return lerp(x, x0, u), lerp(y, y0, u)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 6.0, 12.0)
        f = NQ
        if t < 7.4:
            self.jogo(tela, f)
            for (x, y, w, h), nome in self.sprites(f):
                tela.ret_vazado(x - 2, y - 2, w + 4, h + 4, AMARELO)
            (x, y, w, h), _ = self.sprites(f)[0]
            if not VERTICAL and t > 1.0:
                rotulo(tela, 'SPRITE: O HERÓI', VX0 + 150, VY0 + 160, x + w // 2, y + h + 2, AMARELO)
                (x2, y2, w2, h2), _ = self.sprites(f)[1]
                rotulo(tela, 'SPRITE: A MOEDA', x2 + w2 + 24, y2 + 16, x2 + w2 + 2, y2 + 8, OURO2)
            k_at = -1
        elif t < 21.6:
            u = suave((t - 18.6) / 2.4)
            k_at = min(6, int((t - self.T_PILHA) / 1.5)) if t >= self.T_PILHA else -1
            for k, (cam_, nome) in enumerate(ORDEM):
                if k > k_at: break
                x, y = self.canto(k, u)
                b = JOGO.quadro(f, [cam_])
                tela.ret_vazado(x - 1, y - 1, GW + 2, GH + 2, AMARELO if (k == k_at and u == 0) else ACO1)
                colar(tela, b, x, y, 1, clip=CLIP)
                if u == 0:                          # etiqueta com o número da camada
                    tela.ret(x, y, 9, 11, AMARELO if k == k_at else PRETO)
                    tela.texto(str(k + 1), x + 2, y + 2, PRETO if k == k_at else ACO3, tam=9)
            if k_at >= 0 and u == 0 and not VERTICAL:
                tela.texto('PINTANDO AGORA:', 10, 8, ACO3, tam=9, contorno=PRETO)
                tela.texto(f"{k_at + 1} {ORDEM[k_at][1]}", 10, 20, AMARELO, tam=17, contorno=PRETO)
            if k_at >= 0 and u == 0:                # pincel sobre a camada que está sendo pintada
                x, y = self.canto(k_at)
                a = (t - self.T_PILHA) % 1.5 / 1.5
                bx, by = x + 10 + a * (GW - 20), y + 30 + 10 * math.sin(a * 12)
                linha_grossa(tela, bx, by, bx + 12, by - 14, 3, ACO3)
                tela.disco(bx, by, 3, AMARELO); tela.px(bx - 1, by - 1, BRANCO)
        elif t < 29.0:
            k_at = 7
            fp = NQ + int((t - 21.6) * 20)
            self.jogo(tela, fp, D.CAMADAS[:6])
            if not VERTICAL:
                for j, (nome, vel, y) in enumerate((('NUVENS', .12, 30), ('MONTANHAS', .25, 74), ('MORROS', .5, 112),
                                                    ('TILES', 1.0, 140))):
                    L = 10 + vel * 50
                    x0 = VX0 + 278 - L - 4
                    seta(tela, x0 + L, y, x0, y, BRANCO if j < 3 else AMARELO, 1, 4)
                    tela.texto(nome, x0 - 4, y - 4, BRANCO, tam=9, contorno=PRETO, centro='d')
        else:
            k_at = 7
            b = JOGO.quadro(f, [c for c, _ in ORDEM[:6]])
            moldura(tela, VX0, VY0, 280, 156)
            colar(tela, b, VX0, VY0, 2, clip=CLIP, transp=False)
            if t >= 30.4:
                u = clamp((t - 30.4) / .5)
                b2 = JOGO.quadro(f, ['placar'])
                colar(tela, b2, VX0, VY0 - int((1 - u) * 20), 2, clip=(VX0, VY0, VX0 + 280, VY0 + 156))
                if u >= 1 and not VERTICAL:
                    rotulo(tela, 'PLACAR: A ÚLTIMA CAMADA', VX0 + 70, VY0 + 60, VX0 + 40, VY0 + 26, AMARELO)
        if VERTICAL: return
        y = self.cron(tela, ms, t)
        self.ptxt(tela, 'ORDEM DE PINTURA:', y + 2)
        for j, (c, nome) in enumerate(ORDEM):
            yy = y + 13 + j * 10
            feito = j < k_at or (j == 6 and t >= 30.4)
            atual = j == k_at
            tela.texto(f"{j + 1} {nome}", PX0, yy, AMARELO if atual else (BRANCO if feito else ACO1), tam=9, contorno=PRETO)
            if feito: tela.ret(PX0 + 90, yy + 2, 4, 4, VERDE)
        if 21.6 <= t < 29.0:
            self.ptxt(tela, 'VÁRIOS QUADROS SEGUIDOS', y + 86, CIANO)

    def sprites(self, f):
        hx, hy, hw, hh = heroi_tela(f)
        out = [((hx - 2, hy, 18, hh), 'heroi')]
        volta = int(SIM.x[f] // D.LARG_FASE)
        for v in (volta, volta + 1):
            for i, (mx, my) in enumerate(D.MOEDAS):
                q = SIM.moedas_de.get((v, i))
                if q is not None and q <= f: continue
                x, y = mundo_tela(mx + v * D.LARG_FASE - 3, my - 4, f)
                if VX0 <= x < VX0 + 266: out.append(((x, y, 12, 16), 'moeda'))
        return out

    def sons(self, fx):
        for k in range(7):
            fx.put(fx.chiado(.5, 1500, 5000), self.t0 + self.T_PILHA + k * 1.5, .25, -.4 + k * .13)
        fx.put(fx.clique(1200, .05), self.t0 + 21.0, .4)
        fx.put(fx.sino(84), self.t0 + 30.9, .3)


# ============================================================ 8 a malha 3D
AREA3D = (8, 4, 296, 206)
K3 = dict(cy=104, foco=320.0)                   # câmera do 3D: herói grande no palco
VI = 62                                         # o vértice em destaque: ponta da aba do boné


class Malha(Cena):
    def preparar(self):
        self.R = D.Raster3D(AREA3D)

    def yaw(self, t): return -.6 + t * .2

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 3.0, 6.0)
        yaw = self.yaw(t)
        cx = 90 if VERTICAL else 150
        P = D.projetar(D.HV, yaw, cx=cx, **K3)
        PC = D.projetar(D.CV, yaw, cx=cx, **K3)
        if t < 7.4:
            D.cena3d(self.R, yaw, 'textura', cx=cx, **K3)
            self.R.colar(tela)
        elif t < 14.6:
            # arame: só os triângulos de frente
            for i, j in D.AR_C:
                tela.linha(PC[i, 0], PC[i, 1], PC[j, 0], PC[j, 1], D.GRAMA0)
            vis = [n for n in range(len(D.HT)) if D.visivel(P, D.HT, n)]
            for n in vis:
                a, b, c = D.HT[n][:3]
                for p, q in ((a, b), (b, c), (c, a)):
                    tela.linha(P[p, 0], P[p, 1], P[q, 0], P[q, 1], CIANO)
            # um triângulo em destaque (entre os maiores na tela)
            def area(n):
                a, b, c = D.HT[n][:3]
                return abs((P[b, 0] - P[a, 0]) * (P[c, 1] - P[a, 1]) - (P[b, 1] - P[a, 1]) * (P[c, 0] - P[a, 0]))
            grandes = sorted(vis, key=area)[-8:]
            n = grandes[int(t * .8) % len(grandes)]
            a, b, c = D.HT[n][:3]
            poligono(tela, [tuple(P[a, :2]), tuple(P[b, :2]), tuple(P[c, :2])], AMARELO)
            if not VERTICAL:
                m = P[[a, b, c], :2].mean(0)
                rotulo(tela, '1 TRIÂNGULO', 200, 30, m[0], m[1], AMARELO)
        else:
            for i, j in D.AR_C:
                tela.linha(PC[i, 0], PC[i, 1], PC[j, 0], PC[j, 1], D.GRAMA0)
            for i, j in D.AR_H:
                tela.linha(P[i, 0], P[i, 1], P[j, 0], P[j, 1], ACO1)
            nv = len(D.HV)
            feitos = nv if t < 21.8 else int(clamp((t - 21.8) / 6.0) * nv)
            if t >= 29.0: feitos = nv
            for i in range(nv):
                cor = AMARELO if (i < feitos) else ACO1
                tela.ret(P[i, 0] - 1, P[i, 1] - 1, 3, 3, PRETO)
                tela.px(P[i, 0], P[i, 1], cor)
            vi = VI                                   # ponta da aba do boné
            tela.anel(P[vi, 0], P[vi, 1], 4, BRANCO)
            if not VERTICAL:
                rotulo(tela, 'VÉRTICE', 210, 26, P[vi, 0] + 4, P[vi, 1] - 2, BRANCO)
            self.vi = vi
        if VERTICAL: return
        y = self.cron(tela, ms, t, titulo='O MESMO QUADRO, EM 3D')
        self.ptxt(tela, 'O HERÓI EM 3D:', y + 2)
        self.ptxt(tela, f'{len(D.HT)} TRIÂNGULOS', y + 14, CIANO)
        self.ptxt(tela, f'{len(D.HV)} VÉRTICES', y + 26, AMARELO)
        if t >= 14.6:
            v = D.HV[VI]
            self.ptxt(tela, 'NO MODELO (3D):', y + 42)
            self.ptxt(tela, f'X {dec(v[0])}  Y {dec(v[1])}  Z {dec(v[2])}', y + 52, BRANCO)
            if t >= 21.8:
                p = P[VI]
                self.ptxt(tela, 'NA TELA (2D):', y + 66)
                self.ptxt(tela, f'X {int(p[0])}  Y {int(p[1])}', y + 76, AMARELO)

    def sons(self, fx):
        fx.put(fx.chiado(.8, 400, 3000), self.t0 + 7.4, .2)
        for k in range(0, 64, 4):
            fx.put(fx.blip(60 + k // 2, .04), self.t0 + 21.8 + k / 64 * 6.0, .08)


# ============================================================ 9 rasterização
GX, GY, GN, GM, GL = 20, 22, 16, 13, 11       # grade: canto, colunas, linhas, lado
TRI = [(1.8, 1.4), (15.2, 5.0), (5.6, 12.2)]   # em células


class Raster(Cena):
    def preparar(self):
        self.R = D.Raster3D(AREA3D)
        self.dentro = np.zeros((GM, GN), bool)
        for j in range(GM):
            for i in range(GN):
                self.dentro[j, i] = D.dentro_tri(i + .5, j + .5, TRI)

    def n_testados(self, t):
        if t < 7.4: return 0
        return min(GN * GM, int((t - 7.4) * 34))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 6.0, 10.0)
        if t < 21.6:
            self.grade(tela, t)
        else:
            yaw = .3 + .45 * math.sin((t - 21.6) * .45)       # sempre de frente: o rosto aparece
            if t < 29.0:
                a = (t - 21.6) * .9
                luz = np.array([math.cos(a) * .8, .6, math.sin(a) * .8]); luz /= np.linalg.norm(luz)
                modo = 'cor'
            else:
                luz, modo = D.LUZ, 'textura'
            cx = 90 if VERTICAL else 150
            D.cena3d(self.R, yaw, modo, luz=luz, cx=cx, **K3)
            self.R.colar(tela)
            if t < 29.0:
                # o "sol" que gira em volta
                sx, sy = cx + luz[0] * 125, 34 + luz[2] * 14
                tela.disco(sx, sy, 7, PRETO); tela.disco(sx, sy, 6, AMARELO); tela.disco(sx - 2, sy - 2, 2, BRANCO)
                for k in range(8):
                    b = k * math.pi / 4 + t
                    tela.px(sx + math.cos(b) * 10, sy + math.sin(b) * 10, AMARELO)
                if not VERTICAL: tela.texto('LUZ', sx + 10, sy - 3, AMARELO, tam=9, contorno=PRETO)
        if VERTICAL: return
        y = self.cron(tela, ms, t, titulo='O MESMO QUADRO, EM 3D')
        if t < 21.6:
            n = self.n_testados(t)
            pint = int(self.dentro.reshape(-1)[:n].sum())
            self.ptxt(tela, f'PIXELS TESTADOS: {n}', y + 2, BRANCO)
            self.ptxt(tela, f'DENTRO (PINTA): {pint}', y + 14, AMARELO)
            self.ptxt(tela, f'FORA: {n - pint}', y + 26, ACO2)
        elif t >= 29.0:
            self.ptxt(tela, 'TEXTURAS DO HERÓI:', y + 2)
            for k, nome in enumerate(('rosto', 'camisa', 'calca')):
                x = PX0 + k * 34
                tela.ret(x - 1, y + 13, 26, 26, PRETO)
                colar(tela, D.TEX[nome], x, y + 14, 3, clip=(0, 0, W, PALCO_H))
            self.ptxt(tela, 'IMAGENS 8 X 8 COLADAS', y + 46, ACO3)
            self.ptxt(tela, 'NOS TRIÂNGULOS', y + 56, ACO3)
        else:
            self.ptxt(tela, 'DE FRENTE PARA A LUZ:', y + 2)
            self.ptxt(tela, 'MAIS CLARO', y + 12, AMARELO)
            self.ptxt(tela, 'DE COSTAS: MAIS ESCURO', y + 26, ACO2)

    def grade(self, tela, t):
        D.grade(tela, GX, GY, GN, GM, GL)
        n = self.n_testados(t)
        (ax, ay), (bx, by), (cx, cy) = [(GX + x * GL, GY + y * GL) for x, y in TRI]
        for k in range(min(n, GN * GM)):
            j, i = divmod(k, GN)
            x, y = GX + i * GL, GY + j * GL
            if self.dentro[j, i]:
                cor = AMARELO
                if t >= 14.6:
                    # pixel shader: cada pixel ganha a sua cor (luz que cai pelo triângulo)
                    s = clamp((t - 14.6) / 3.0) * (GN + GM)
                    if i + j < s:
                        w0, w1, w2 = D.baric(i + .5, j + .5, TRI)
                        luz = w0 * 1.0 + w1 * .55 + w2 * .1
                        rampa = [D.SOMBRA[ROUPA1], ROUPA1, ROUPA2, D.ROUPA3]
                        nv = luz * 3.2 + (LG.BAYER8[j % 8, i % 8] - .5) * .8
                        cor = rampa[int(min(3, max(0, nv)))]
                tela.ret(x, y, GL - 1, GL - 1, cor)
            else:
                tela.px(x + GL // 2, y + GL // 2, ACO1)
        if 7.4 <= t and n < GN * GM:
            j, i = divmod(n, GN)
            tela.ret_vazado(GX + i * GL - 1, GY + j * GL - 1, GL + 1, GL + 1, CIANO)
        # pontos centrais e o triângulo por cima
        if t < 14.6:
            for j in range(GM):
                for i in range(GN):
                    if j * GN + i >= n: tela.px(GX + i * GL + GL // 2, GY + j * GL + GL // 2, ACO2)
        for (p, q) in (((ax, ay), (bx, by)), ((bx, by), (cx, cy)), ((cx, cy), (ax, ay))):
            tela.linha(p[0], p[1], q[0], q[1], BRANCO)
        for (x, y) in ((ax, ay), (bx, by), (cx, cy)):
            tela.disco(x, y, 2.5, PRETO); tela.disco(x, y, 1.6, CIANO)
        if not VERTICAL:
            rotulo(tela, 'VÉRTICE', 230, 40, bx + 2, by, CIANO)
            if 7.4 <= t < 14.6:
                rotulo(tela, 'CENTRO DO PIXEL', 214, 176, GX + 13 * GL + GL // 2, GY + 11 * GL + GL // 2, ACO3)
            if t >= 14.6:
                rotulo(tela, 'COR DE CADA PIXEL', 214, 176, GX + 7 * GL + 5, GY + 7 * GL + 5, ROUPA2)

    def sons(self, fx):
        for k in range(0, GN * GM, 3):
            j, i = divmod(k, GN)
            if self.dentro[j, i]: fx.put(fx.blip(72 + (k % 5), .03), self.t0 + 7.4 + k / 34, .05)
        fx.put(fx.chiado(1.2, 800, 4000), self.t0 + 14.6, .15)
        fx.put(fx.sino(79), self.t0 + 29.0, .25)


# ============================================================ 10 profundidade (z-buffer)
ZN, ZM = 10, 8
ZTRI = [  # (vértices em células, profundidade, cor, nome)
    ([(0.2, 7.8), (9.8, 7.8), (5.0, 0.6)], 7, GRAMA1, 'MORRO'),
    ([(0.8, 0.8), (6.2, 2.4), (2.6, 7.6)], 2, ROUPA1, 'HERÓI'),
    ([(3.6, 2.2), (9.8, 0.4), (8.6, 7.6)], 5, PEDRA1, 'PEDRA'),
]
ZT = [7.4, 14.6, 21.8]                          # quando cada triângulo começa


class Profundidade(Cena):
    def preparar(self):
        # pré-calcula a ordem de varredura e o resultado de cada teste
        self.passos = []                        # (tempo, tri, i, j, pinta)
        z = np.full((ZM, ZN), 99);
        for k, (tri, prof, cor, nome) in enumerate(ZTRI):
            cel = [(j, i) for j in range(ZM) for i in range(ZN) if D.dentro_tri(i + .5, j + .5, tri)]
            for n, (j, i) in enumerate(cel):
                tt = ZT[k] + .4 + n * (5.4 / max(1, len(cel)))
                pinta = prof < z[j, i]
                if pinta: z[j, i] = prof
                self.passos.append((tt, k, i, j, pinta))

    def layout(self):
        if VERTICAL: return (50, 14), (50, 96), 8
        return (14, 40), (162, 40), 13

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        ms = ms_de(t, self.dur, 10.0, 11.5)
        (cx0, cy0), (dx0, dy0), L = self.layout()
        D.grade(tela, cx0, cy0, ZN, ZM, L)
        D.grade(tela, dx0, dy0, ZN, ZM, L, cor_fundo=FUNDO)
        tela.texto('COR', cx0, cy0 - 11, BRANCO, tam=9, contorno=PRETO)
        tela.texto('Z-BUFFER' if VERTICAL else 'PROFUNDIDADE (Z-BUFFER)', dx0, dy0 - 11, BRANCO, tam=9, contorno=PRETO)
        z = np.full((ZM, ZN), 99); cor = np.full((ZM, ZN), -1)
        ultimo, antes = None, 99
        for (tt, k, i, j, pinta) in self.passos:
            if tt > t: break
            antes = int(z[j, i])
            if pinta: z[j, i] = ZTRI[k][1]; cor[j, i] = ZTRI[k][2]
            ultimo = (tt, k, i, j, pinta)
        for j in range(ZM):
            for i in range(ZN):
                if cor[j, i] >= 0:
                    tela.ret(cx0 + i * L, cy0 + j * L, L - 1, L - 1, int(cor[j, i]))
                    tela.px(cx0 + i * L, cy0 + j * L, BRANCO)
                if z[j, i] < 99:
                    tela.ret(dx0 + i * L, dy0 + j * L, L - 1, L - 1, CINZA[z[j, i]])
                    tela.texto(str(z[j, i]), dx0 + i * L + (L - 5) // 2, dy0 + j * L + (L - 7) // 2,
                               PRETO if z[j, i] < 4 else BRANCO, tam=9)
                else:
                    tela.texto('-', dx0 + i * L + (L - 5) // 2, dy0 + j * L + (L - 7) // 2, FUNDO3, tam=9)
        # contornos dos triângulos já começados
        for k, (tri, prof, c, nome) in enumerate(ZTRI):
            if t < ZT[k]: continue
            pts = [(cx0 + x * L, cy0 + y * L) for x, y in tri]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                tela.linha(pts[a][0], pts[a][1], pts[b][0], pts[b][1], BRANCO if t < ZT[k] + 6 else ACO2)
        if ultimo and t - ultimo[0] < .5:
            tt, k, i, j, pinta = ultimo
            for (x0, y0) in ((cx0, cy0), (dx0, dy0)):
                tela.ret_vazado(x0 + i * L - 2, y0 + j * L - 2, L + 3, L + 3, VERDE if pinta else VERMELHO)
            if not pinta:
                x, y = cx0 + i * L, cy0 + j * L
                tela.linha(x, y, x + L - 2, y + L - 2, VERMELHO); tela.linha(x + L - 2, y, x, y + L - 2, VERMELHO)
        if VERTICAL: return
        # legenda das profundidades
        y0 = 160
        tela.texto('PERTO', dx0, y0, BRANCO, tam=9, contorno=PRETO)
        for k in range(8):
            tela.ret(dx0 + 34 + k * 8, y0, 7, 7, CINZA[k])
        tela.texto('LONGE', dx0 + 100, y0, ACO2, tam=9, contorno=PRETO)
        tela.texto('MENOR = MAIS PERTO', dx0, y0 + 12, ACO3, tam=9, contorno=PRETO)
        y = self.cron(tela, ms, t, titulo='O MESMO QUADRO, EM 3D')
        k_at = sum(1 for x in ZT if t >= x) - 1
        if k_at >= 0:
            tri, prof, c, nome = ZTRI[k_at]
            self.ptxt(tela, 'PINTANDO:', y + 2)
            tela.ret(PX0 + 60, y + 3, 6, 6, c)
            self.ptxt(tela, f'{nome} ({prof})', y + 2, BRANCO, x=PX0 + 70)
        if ultimo and t - ultimo[0] < 1.0:
            tt, k, i, j, pinta = ultimo
            self.ptxt(tela, 'TESTE DESTE PIXEL:', y + 18)
            self.ptxt(tela, f'NOVO: {ZTRI[k][1]}', y + 30, BRANCO)
            self.ptxt(tela, 'GUARDADO: ' + ('VAZIO' if antes >= 99 else str(antes)), y + 42, BRANCO)
            self.ptxt(tela, 'MAIS PERTO: PINTA' if pinta else 'MAIS LONGE: NÃO PINTA', y + 56,
                      VERDE if pinta else VERMELHO)

    def sons(self, fx):
        for (tt, k, i, j, pinta) in self.passos[::2]:
            fx.put(fx.blip(76 if pinta else 52, .04), self.t0 + tt, .06 if pinta else .1)


# ============================================================ 11 GPU
UN_C, UN_L = 16, 8                              # 128 unidades no desenho


class Gpu(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        f = NQ
        b = JOGO.quadro(f)
        moldura(tela, VX0, VY0, 280, 156)
        tela.ret(VX0, VY0, 280, 156, FUNDO2)
        npx = GW * GH
        if t < 14.6:
            feitos = int(t * 48)                 # um pixel de cada vez
            m = np.arange(npx).reshape(GH, GW) < feitos
            onda = None
        else:
            u = t - 14.6
            per = 4.6
            fase = (u % per) / (per - .6)
            nblocos = math.ceil(GW / UN_C) * math.ceil(GH / UN_L)
            k = int(min(1.0, fase) * nblocos)
            yy, xx = np.mgrid[0:GH, 0:GW]
            bloco = (yy // UN_L) * math.ceil(GW / UN_C) + (xx // UN_C)
            m = bloco < k
            onda = k if fase < 1 else None
            if onda is not None: m_on = bloco == k
        fantasma = D.SOMBRA[D.SOMBRA[b]]              # o que ainda falta: bem apagado
        colar(tela, fantasma, VX0, VY0, 2, clip=CLIP, transp=False)
        escurecer(tela, VX0, VY0, 280, 156)
        img = np.where(m, b, TRANSP).astype(np.uint8)
        colar(tela, img, VX0, VY0, 2, clip=CLIP)
        if t < 14.6:
            p = feitos
            j, i = divmod(p, GW)
            x, y = VX0 + i * 2, VY0 + j * 2
            tela.ret_vazado(x - 2, y - 2, 6, 6, AMARELO)
            if not VERTICAL: rotulo(tela, '1 PIXEL DE CADA VEZ', VX0 + 120, VY0 + 120, x + 2, y + 4, AMARELO)
        elif onda is not None:
            nc = math.ceil(GW / UN_C)
            j, i = divmod(onda, nc)
            x, y = VX0 + i * UN_C * 2, VY0 + j * UN_L * 2
            tela.ret_vazado(x - 1, y - 1, UN_C * 2 + 2, UN_L * 2 + 2, AMARELO)
            # a faixa sendo feita: 128 pixels de uma vez
            sub = np.where((np.mgrid[0:GH, 0:GW][0] // UN_L == j) & (np.mgrid[0:GH, 0:GW][1] // UN_C == i), b, TRANSP).astype(np.uint8)
            colar(tela, sub, VX0, VY0, 2, clip=CLIP)
        if VERTICAL:
            tela.texto('1 POR VEZ' if t < 14.6 else '128 POR VEZ', 100, 176, AMARELO, tam=17, centro=True, contorno=PRETO)
            return
        tela.texto(f'NESTE DESENHO: 140 X 78 = {milhar(npx)} PIXELS', VX0, VY0 + 162, ACO3, tam=9, contorno=PRETO)
        # painel
        if t < 14.6:
            self.ptxt(tela, 'TELA 1.920 X 1.080:', 10)
            self.ptxt(tela, '2.073.600', 22, BRANCO, 26)
            self.ptxt(tela, 'PIXELS POR QUADRO', 50)
            if t >= 7.4:
                self.ptxt(tela, 'X 60 POR SEGUNDO =', 70)
                self.ptxt(tela, '124.416.000', 82, AMARELO, 17)
                self.ptxt(tela, 'PIXELS POR SEGUNDO', 102)
            self.ptxt(tela, '1 UNIDADE DE CÁLCULO:', 130, ACO3)
            tela.ret(PX0, 144, 10, 10, AMARELO if int(t * 8) % 2 else LARANJA)
            self.ptxt(tela, f'FEITOS: {milhar(min(npx, int(t * 48)))}', 146, BRANCO, x=PX0 + 16)
        else:
            self.ptxt(tela, 'GPU: MUITAS UNIDADES', 10)
            self.ptxt(tela, 'DE CÁLCULO JUNTAS', 20)
            self.ptxt(tela, '(AQUI, 128 NO DESENHO)', 32, ACO2)
            gx, gy = PX0 + 4, 48
            u = t - 14.6
            for j in range(UN_L):
                for i in range(UN_C):
                    x, y = gx + i * 9, gy + j * 9
                    on = onda is not None and (int(u * 20) + i + j) % 3 != 0
                    tela.ret(x, y, 8, 8, PRETO)
                    tela.ret(x + 1, y + 1, 6, 6, VERDE if on else FUNDO3)
                    if on: tela.px(x + 2, y + 2, BRANCO)
            q = int(u / 4.6)
            self.ptxt(tela, f'QUADROS PRONTOS: {q}', 130, BRANCO)
            self.ptxt(tela, 'CADA PIXEL É UMA CONTA', 150, ACO3)
            self.ptxt(tela, 'SEPARADA DAS OUTRAS', 160, ACO3)

    def sons(self, fx):
        for k in range(int(14.6 * 4)):
            fx.put(fx.clique(4000, .008), self.t0 + k / 4, .08)
        u = 0.0
        while 14.6 + u < self.dur:
            for k in range(0, 50, 5):
                fx.put(fx.pulso(), self.t0 + 14.6 + u + k * (4.0 / 50), .12)
            fx.put(fx.blip(84, .08), self.t0 + 14.6 + u + 4.0, .15)
            u += 4.6


# ============================================================ 12 framebuffer
P_VARRE = 3.2                                    # uma varredura da tela (câmera lenta)
TROCAS = [(-99, NQ - 1), (16.0, NQ), (19.2, NQ + 1), (23.6, NQ + 13), (26.9, NQ + 25), (32.0, NQ + 37),
          (35.2, NQ + 49), (38.4, NQ + 61), (41.6, NQ + 73)]
PRONTO = {NQ + 37: 30.2, NQ + 49: 33.5, NQ + 61: 37.0, NQ + 73: 40.2}
BUF_A, BUF_B = (10, 20), (10, 116)
MON = (164, 54)


class Buffer(Cena):
    def frente(self, t):
        q, k = TROCAS[0][1], 0
        for n, (tt, f) in enumerate(TROCAS):
            if tt <= t: q, k = f, n
        return q, k

    def tela_monitor(self, t):
        """O que o monitor mostra: cada linha vem do buffer da frente no
        instante em que a varredura passou por ela."""
        out = np.zeros((GH, GW), np.uint8)
        yb = (t % P_VARRE) / P_VARRE * GH
        for r in range(GH):
            tp = t - ((yb - r) % GH) / GH * P_VARRE if r <= yb else t - (yb + GH - r) / GH * P_VARRE
            out[r] = JOGO.quadro(self.frente(tp)[0])[r]
        return out, yb

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        q, k = self.frente(t)
        prox = TROCAS[k + 1][1] if k + 1 < len(TROCAS) else q + 12
        a_na_tela = k % 2 == 0
        # buffer de trás: desenhando (camadas aparecem) ou pronto
        t_ini = TROCAS[k][0] if k > 0 else 7.4
        if prox in PRONTO: dur_des = PRONTO[prox] - t_ini
        else: dur_des = (TROCAS[k + 1][0] - t_ini - .4) if k + 1 < len(TROCAS) else 3.0
        if k == 0: dur_des = 7.0
        nc = int(clamp((t - t_ini) / max(.5, dur_des)) * 7) if (k > 0 or t >= 7.4) else 0
        pronto = nc >= 7
        for n, (bx, by) in enumerate((BUF_A, BUF_B)):
            frente = (n == 0) == a_na_tela
            if VERTICAL: continue
            if frente:
                b = JOGO.quadro(q)
            else:
                b = JOGO.quadro(prox, D.CAMADAS[:nc]) if nc > 0 else np.full((GH, GW), TRANSP, np.uint8)
            tela.ret(bx - 3, by - 3, GW + 6, GH + 6, PRETO)
            tela.ret_vazado(bx - 2, by - 2, GW + 4, GH + 4, VERDE if frente else (LARANJA if pronto else AMARELO))
            if not frente: dither(tela, bx, by, GW, GH, FUNDO, FUNDO2)
            colar(tela, b, bx, by, 1, clip=CLIP)
            # pentes de memória embaixo da moldura
            for i in range(0, GW, 10): tela.ret(bx + i + 2, by + GH + 3, 5, 3, D.OURO1)
            nome = 'BUFFER ' + 'AB'[n]
            estado = 'NA TELA' if frente else ('ESPERANDO' if pronto and t >= 29 else ('PRONTO' if pronto else 'DESENHANDO'))
            if t < 7.4 and n == 1: estado = 'VAZIO'
            if True:
                tela.texto(nome + ': ', bx, by - 13, BRANCO, tam=9, contorno=PRETO)
                tela.texto(estado, bx + tela.largura_texto(nome + ': ', 9) + 3, by - 13,
                           VERDE if frente else (LARANJA if pronto else AMARELO), tam=9, contorno=PRETO)
        # monitor
        mx, my = MON if not VERTICAL else (20, 30)
        tela.ret(mx - 6, my - 6, GW + 12, GH + 12, PRETO)
        tela.ret(mx - 5, my - 5, GW + 10, GH + 10, ACO1)
        tela.ret(mx - 5, my - 5, GW + 10, 1, ACO3)
        tela.ret(mx + GW // 2 - 8, my + GH + 6, 16, 10, ACO0)
        tela.ret(mx + GW // 2 - 24, my + GH + 15, 48, 4, ACO1)
        img, yb = self.tela_monitor(t)
        colar(tela, img, mx, my, 1, clip=(0, 0, W, PALCO_H), transp=False)
        tela.ret(mx, my + int(yb), GW, 1, BRANCO)
        tela.ret(mx - 3, my + int(yb) - 1, 2, 3, CIANO)
        if not VERTICAL:
            tela.texto('TELA', mx + GW // 2, my - 18, BRANCO, tam=9, centro=True, contorno=PRETO)
            # cabo do buffer da frente até a tela
            bx, by = BUF_A if a_na_tela else BUF_B
            pts = [(bx + GW + 2, by + GH // 2), (mx - 12, by + GH // 2), (mx - 12, my + GH // 2), (mx - 6, my + GH // 2)]
            for (a, b_), (c, d) in zip(pts, pts[1:]):
                linha_grossa(tela, a, b_, c, d, 3, PRETO); linha_grossa(tela, a, b_, c, d, 1, VERDE)
        # rasgo: linhas vizinhas de quadros diferentes
        fontes = []
        for r in range(GH):
            tp = t - ((yb - r) / GH * P_VARRE if r <= yb else (yb + GH - r) / GH * P_VARRE)
            fontes.append(self.frente(tp)[0])
        for r in range(1, GH):
            if fontes[r] != fontes[r - 1] and abs(r - yb) > 1.5:   # a fronteira na varredura é normal
                yy = my + r
                for x in range(mx - 4, mx + GW + 4, 4): tela.ret(x, yy, 2, 1, VERMELHO)
                tela.texto('RASGO', mx + GW + 6 if not VERTICAL else mx + GW - 30, yy - 3, VERMELHO, tam=9, contorno=PRETO)
        if VERTICAL:
            if 21.8 <= t < 29: tela.texto('SEM VSYNC', 90, 136, VERMELHO, tam=17, centro=True, contorno=PRETO)
            elif t >= 29: tela.texto('COM VSYNC', 90, 136, VERDE, tam=17, centro=True, contorno=PRETO)
            else: tela.texto('TELA', 90, 136, BRANCO, tam=17, centro=True, contorno=PRETO)
            return
        # painel
        if t < 16.0:
            ms = lerp(12.0, ORCAMENTO, clamp(t / 16.0))
            yy = self.cron(tela, ms, t, x=318, w=150, lista=False)
            self.ptxt(tela, 'ESPERANDO A TELA', yy + 2, ROSA, x=318)
            self.ptxt(tela, 'TERMINAR A VARREDURA', yy + 12, ROSA, x=318)
        else:
            yy = self.cron(tela, ORCAMENTO, t, x=318, w=150, lista=False)
            self.ptxt(tela, 'TROCOU! O QUADRO', yy + 2, VERDE, x=318)
            self.ptxt(tela, f'{milhar(NQ)} ESTÁ NA TELA.', yy + 12, VERDE, x=318)
        if 21.8 <= t < 29.0:
            painel(tela, 316, 132, 154, 40, borda=VERMELHO)
            self.ptxt(tela, 'VSYNC: DESLIGADO', 138, VERMELHO, x=322)
            self.ptxt(tela, 'TROCA QUANDO FICA', 150, BRANCO, x=322)
            self.ptxt(tela, 'PRONTO', 160, BRANCO, x=322)
        elif t >= 29.0:
            painel(tela, 316, 132, 154, 40, borda=VERDE)
            self.ptxt(tela, 'VSYNC: LIGADO', 138, VERDE, x=322)
            self.ptxt(tela, 'TROCA SÓ NO FIM', 150, BRANCO, x=322)
            self.ptxt(tela, 'DA VARREDURA', 160, BRANCO, x=322)
            if t >= 36.0:
                self.ptxt(tela, 'ESPERAR = ATRASO', 182, LARANJA, x=318)
        else:
            self.ptxt(tela, 'A TELA SE REDESENHA', 140, ACO3, x=318)
            self.ptxt(tela, 'DE CIMA PARA BAIXO', 150, ACO3, x=318)

    def sons(self, fx):
        for tt, f in TROCAS[1:]:
            fx.put(fx.clique(1800, .04), self.t0 + tt, .4)
            fx.put(fx.blip(79, .06), self.t0 + tt + .02, .12)
        fx.put(fx.chiado(.4, 2000, 6000), self.t0 + 23.6, .3)
        fx.put(fx.chiado(.4, 2000, 6000), self.t0 + 26.9, .3)


# ============================================================ 13 FPS
TAXAS = [(30, '33,3 MS'), (60, '16,7 MS'), (120, '8,3 MS')]
LENTO = 8.0                                     # câmera lenta do pulo
VY0_S, G_S, VX_S = 192.0, 648.0, 45.0           # o pulo do jogo em px/s (3,2 e 0,18 por quadro a 60)
T_PULO = 2 * VY0_S / G_S


class Fps(Cena):
    def caixa(self, k):
        if VERTICAL: return 2, 4 + k * 54, 176, 50
        return 6 + k * 97, 8, 92, 160

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 21.6:
            self.colunas(tela, t)
        else:
            self.grafico(tela, t)
        if VERTICAL: return
        self.ptxt(tela, 'TEMPO DE CADA QUADRO', 10)
        for k, (fps, ms) in enumerate(TAXAS):
            y = 26 + k * 24
            tela.texto(f'{fps} FPS', PX0, y, BRANCO, tam=17, contorno=PRETO)
            tela.texto(ms, PX0 + 92, y + 4, AMARELO, tam=9, contorno=PRETO)
        self.ptxt(tela, '1 SEGUNDO / FPS', 100, ACO3)
        if t < 21.6:
            self.ptxt(tela, f'CÂMERA LENTA {int(LENTO)}X', 124, CIANO, 17)
        else:
            self.ptxt(tela, 'MÉDIA PERTO DE 60,', 124, BRANCO)
            self.ptxt(tela, 'MAS UM QUADRO ATRASOU', 136, VERMELHO)

    def colunas(self, tela, t):
        for k, (fps, ms) in enumerate(TAXAS):
            x, y, w, h = self.caixa(k)
            painel(tela, x, y, w, h, borda=TRACO, fundo=FUNDO2 if True else PRETO)
            dither(tela, x + 1, y + 1, w - 2, h - 2, D.CEU1, D.CEU2)
            chao = y + h - 14 if not VERTICAL else y + h - 6
            colar(tela, np.tile(D.TILES[1], (1, 30))[:, :(w - 2) // 2], x + 1, chao, 2, clip=(x + 1, y + 1, x + w - 1, y + h - 1))
            if VERTICAL:
                tela.texto(f'{fps} FPS', x + 4, y + 6, BRANCO, tam=17, contorno=PRETO)
                tela.texto(ms, x + 4, y + 26, AMARELO, tam=9, contorno=PRETO)
                x_pulo, esc = x + 92, 1.0
            else:
                tela.texto(f'{fps} FPS', x + w // 2, y + 6, BRANCO, tam=17, centro=True, contorno=PRETO)
                tela.texto(ms, x + w // 2, y + 26, AMARELO, tam=9, centro=True, contorno=PRETO)
                x_pulo, esc = x + 12, 2.0
            g = ((t % 6.0) / LENTO)                      # segundos do jogo
            g = min(g, T_PULO)
            gq = math.floor(g * fps) / fps               # o jogo só atualiza a cada quadro
            n = int(T_PULO * fps)
            for i in range(n + 1):
                tt = i / fps
                if tt > gq + 1e-9: break
                px_ = x_pulo + VX_S * tt * esc + 6 * esc / 2
                py_ = chao - (VY0_S * tt - G_S * tt * tt / 2) * esc - 6 * esc
                tela.px(px_, py_, AMARELO)
            hx = x_pulo + VX_S * gq * esc
            hy = chao - (VY0_S * gq - G_S * gq * gq / 2) * esc
            spr = D.HEROI['pulo'] if 0 < gq < T_PULO else D.HEROI['parado']
            if esc == 2: spr = np.repeat(np.repeat(spr, 2, 0), 2, 1)
            D.carimbo(tela, spr, hx, hy - spr.shape[0])
            if not VERTICAL:
                tela.texto(f'{min(n, int(gq * fps + 1e-6))} QUADROS', x + w // 2, y + h + 4, ACO3, tam=9, centro=True,
                           contorno=PRETO)

    def grafico(self, tela, t):
        x0, y0, w, h = (4, 14, 172, 150) if VERTICAL else (14, 20, 270, 150)
        painel(tela, x0 - 4, y0 - 6, w + 8, h + 30)
        esc_ms = h / 30.0                                    # 30 ms de altura
        base = y0 + h
        for ms in (10, 20, 30):
            yy = base - ms * esc_ms
            for xx in range(x0 + 18, x0 + w, 4): tela.px(xx, yy, FUNDO3)
            tela.texto(str(ms), x0, yy - 3, ACO2, tam=9)
        # tempos de exemplo: perto de 15 ms, um quadro que passa de 16,7
        rng = np.random.default_rng(8)
        vals = 13.5 + rng.random(400) * 2.6
        vals[np.arange(400) % 37 == 20] = 25.0
        des = int((t - 21.6) * 6)
        larg = 8
        nb = (w - 18) // larg
        for i in range(nb):
            n = des + i
            v = vals[n % 400]
            xx = x0 + 18 + i * larg
            alto = v > ORCAMENTO
            tela.ret(xx, base - v * esc_ms, larg - 2, v * esc_ms, VERMELHO if alto else VERDE)
            tela.ret(xx, base - v * esc_ms, larg - 2, 1, BRANCO if not alto else ROSA)
            if alto and xx > x0 + 20 and not VERTICAL:
                tela.texto('ATRASOU', xx - 10, base - v * esc_ms - 22, VERMELHO, tam=9, contorno=PRETO)
                tela.texto('REPETE O QUADRO', xx - 30, base - v * esc_ms - 12, VERMELHO, tam=9, contorno=PRETO)
        yo = base - ORCAMENTO * esc_ms
        for xx in range(x0 + 18, x0 + w, 3): tela.ret(xx, yo, 2, 1, AMARELO)
        tela.texto('16,7 MS', x0 + w - 44, yo - 10, AMARELO, tam=9, contorno=PRETO)
        tela.texto('TEMPO DE CADA QUADRO (EXEMPLO)', x0, base + 6, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k, (fps, _) in enumerate(TAXAS[:1]):
            for i in range(int(21.6 * fps / LENTO)):
                tt = i / fps * LENTO
                if (tt % 6.0) / LENTO <= T_PULO: fx.put(fx.clique(3000, .01), self.t0 + tt, .05)
        for n in range(int((self.dur - 21.6) * 6)):
            pass


# ============================================================ 14 resumo
class Resumo(Cena):
    def varre(self, t):
        """Posição do cursor no quadro (0..1) e quantos quadros já passaram."""
        if t < 18.0:
            per = 2.0
            return (t % per) / per, int(t / per)
        per = max(1 / 60, 2.0 * (1 - clamp((t - 18.0) / 6.0)) + 1 / 60)
        # integra a velocidade (aproximação: conta como se fosse constante no trecho)
        return (t * 60) % 1.0 if per < .1 else ((t - 18.0) % per) / per, 9 + int((t - 18.0) / per)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        u, n = self.varre(t)
        rapido = t >= 22.0
        f = NQ + n if not rapido else NQ + 9 + int((t - 22.0) * 60)
        self.jogo(tela, f, x=78, y=12, esc=1)
        x0, y0, w = 14, 128, 270
        for k, (nome, a, b, cor) in enumerate(D.ETAPAS):
            xa, xb = x0 + a / ORCAMENTO * w, x0 + b / ORCAMENTO * w
            acesa = (a / ORCAMENTO <= u < b / ORCAMENTO) and not rapido
            tela.ret(xa, y0, xb - xa - 1, 14, cor if acesa or rapido else FUNDO3)
            tela.ret(xa, y0, xb - xa - 1, 1, BRANCO if acesa else TRACO)
        tela.ret_vazado(x0 - 2, y0 - 2, w + 4, 18, ACO1)
        for k, (nome, xx, yy) in enumerate((('LER', 6, 40), ('ATUALIZAR', 30, 20), ('DESENHAR', 120, 40),
                                            ('MOSTRAR', 214, 20))):
            yy += y0
            if k < 3: icone(tela, k, xx, yy, t)
            else:
                tela.ret(xx, yy + 2, 16, 11, PRETO); tela.ret(xx + 1, yy + 3, 14, 9, CIANO); tela.ret(xx + 6, yy + 13, 4, 3, ACO1)
            tela.texto(nome, xx + 20, yy + 4, D.ETAPAS[k][3], tam=9, contorno=PRETO)
        tela.texto('0 MS', x0, y0 - 12, ACO3, tam=9, contorno=PRETO)
        tela.texto('16,7 MS', x0 + w, y0 - 12, ACO3, tam=9, contorno=PRETO, centro='d')
        if not rapido:
            xc = x0 + u * w
            tela.ret(xc - 1, y0 - 4, 3, 22, BRANCO)
        else:
            tela.texto('60 VEZES POR SEGUNDO', x0 + w // 2, y0 + 62, AMARELO, tam=17, centro=True, contorno=PRETO)
        if VERTICAL: return
        if 9.0 <= t < 17.6:
            painel(tela, PX0, 20, 164, 60, borda=AMARELO)
            tela.texto('2D', PX0 + 8, 28, AMARELO, tam=17, contorno=PRETO)
            tela.texto('TILES + SPRITES', PX0 + 8, 48, BRANCO, tam=9, contorno=PRETO)
            tela.texto('EM CAMADAS', PX0 + 8, 60, BRANCO, tam=9, contorno=PRETO)
            painel(tela, PX0, 92, 164, 60, borda=CIANO)
            tela.texto('3D', PX0 + 8, 100, CIANO, tam=17, contorno=PRETO)
            tela.texto('TRIÂNGULOS, PIXELS', PX0 + 8, 120, BRANCO, tam=9, contorno=PRETO)
            tela.texto('E Z-BUFFER', PX0 + 8, 132, BRANCO, tam=9, contorno=PRETO)
        else:
            self.ptxt(tela, 'QUADROS:', 20)
            self.ptxt(tela, milhar(f), 32, BRANCO, 26)

    def sons(self, fx):
        for k in range(9):
            for j, m in enumerate((72, 76, 79, 84)):
                fx.put(fx.blip(m, .05), self.t0 + k * 2.0 + D.ETAPAS[j][1] / ORCAMENTO * 2.0, .07)


# ============================================================ 15 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS FEITO DE PIXELS'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            self.fundo(tela, t)
            tela.buf[:, 298:] = FUNDO
            for x in range(0, W, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            b = JOGO.quadro(NQ + int(t * 60))
            D.moldura(tela, W // 2 - 140, 62, 280, 140)
            colar(tela, b[:70], W // 2 - 140, 62, 2, clip=(0, 0, W, PALCO_H), transp=False)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, jogo=Jogo, laco=Laco, controle=Controle, fisica=Fisica, tiles=Tiles,
             camadas=Camadas, malha=Malha, raster=Raster, profundidade=Profundidade, gpu=Gpu, buffer=Buffer,
             fps=Fps, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep08_motor as EP
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
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
