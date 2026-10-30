#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep07 — A jornada de uma mensagem de celular (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (toque no ENVIAR, bits, rádio, laser,
                          roteador, chegada), nos mesmos instantes do desenho
A distância do PACOTE Nº 1 sai de `km(t)` em cada capítulo; o painel e o
contador de milissegundos leem `ep07_desenho.viagem_ms(km)`.

    python3 ep07_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep07_motor.py <saida.mp4> bits fibra       # só esses capítulos (teste)
    python3 ep07_motor.py --folha <saida.png> [ids]    # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ep07_desenho as D
from ep07_desenho import (ETAPAS, rotulo, fio, seta, halo, luz, mira, caixa, tique, tiques, cadeado, chave,
                          foto, celular, chat, chat_recebido, pacote, torre, ondas, painel_viagem, fmt_km, fmt_ms,
                          viagem_ms, KM_RADIO1, KM_FORTALEZA, KM_SINES, KM_LISBOA, KM_TOTAL)
import ritmo_marca as RM
import idioma as I
from ep07_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2607, 47
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

BITS = {'O': '01001111', 'I': '01001001', '!': '00100001'}
NUM = {'O': 79, 'I': 73, '!': 33}


def leitura_vertical(tela, km, x=150, txt=None):
    """No Short o painel fica de fora: distância e tempo no alto do recorte."""
    if not VERTICAL: return
    s = txt or f"{fmt_km(km)}  {fmt_ms(viagem_ms(km))}"
    w = tela.largura_texto(s, 9) + 10
    painel(tela, x - w // 2, 1, w, 13, borda=AMARELO)
    tela.texto(s, x, 4, AMARELO, tam=9, centro=True)


def grade(tela, x0=0, x1=W):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(x0, x1, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(x0, y, x1 - x0, 1, FUNDO2)


def mao(tela, x, y, w, h, dedos=False):
    """Mão genérica segurando o celular (x, y, w, h = o celular). Chamar antes
    do celular (palma e pulso) e depois com dedos=True (dedos por cima)."""
    if not dedos:
        tela.ret(x - 5, y + h // 2 - 1, w + 10, h // 2 + 8, PRETO)
        tela.ret(x - 4, y + h // 2, w + 8, h // 2 + 6, LATAO)
        tela.ret(x - 4, y + h // 2, 2, h // 2 + 6, CHAMA0)
        tela.ret(x + 1, y + h + 6, w - 2, PALCO_H, PRETO)
        tela.ret(x + 2, y + h + 6, w - 4, PALCO_H, OLEO1)
        tela.ret(x + 2, y + h + 6, w - 4, 2, OLEO0)
        return
    for k in range(3):
        tela.ret(x + w - 2, y + h // 2 + 2 + k * 6, 6, 6, PRETO); tela.ret(x + w - 1, y + h // 2 + 3 + k * 6, 4, 4, LATAO)
        tela.ret(x + w - 1, y + h // 2 + 3 + k * 6, 4, 1, CHAMA0)
    tela.ret(x - 4, y + h // 2 - 4, 6, 12, PRETO); tela.ret(x - 3, y + h // 2 - 3, 4, 10, LATAO)


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


def rota_km(mapa, km):
    """Posição no mapa do pacote que já andou `km` (São Paulo -> Fortaleza -> Sines -> Lisboa)."""
    nos = ['SÃO PAULO', 'FORTALEZA', 'SINES', 'LISBOA']
    marcos = [KM_RADIO1, KM_FORTALEZA, KM_SINES, KM_LISBOA]
    pts = [mapa.cid(n) for n in nos]
    if km <= marcos[0]: return pts[0], 0
    for k in range(3):
        if km <= marcos[k + 1]:
            u = (km - marcos[k]) / (marcos[k + 1] - marcos[k])
            a, b = pts[k], pts[k + 1]
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), k + u
    return pts[-1], 3


def continentes(tela, M):
    for nome, lon, lat in (('BRASIL', -45.5, -8), ('ÁFRICA', -4, 14)):
        x, y = M.px(lon, lat)
        if M.x0 + 2 < x < M.x0 + M.w - 10 and M.y0 < y < M.y0 + M.h - 8:
            rotulo(tela, nome, x, y, AGUA1, centro=True)


def desenhar_rota(tela, mapa, km, t, cor=AMARELO):
    nos = ['SÃO PAULO', 'FORTALEZA', 'SINES', 'LISBOA']
    pts = [mapa.cid(n) for n in nos]
    D.rota_tracejada(tela, pts, t, ACO2)
    p, kk = rota_km(mapa, km)
    feitos = pts[:int(kk) + 1] + [p]
    for a, b in zip(feitos, feitos[1:]):
        linha_grossa(tela, a[0], a[1], b[0], b[1], 4, PRETO)
    for a, b in zip(feitos, feitos[1:]):
        linha_grossa(tela, a[0], a[1], b[0], b[1], 2, cor)
    return p


_MAPAS = {}


def mapa(nome):
    if nome not in _MAPAS:
        cfg = {'mundo_d': (-52, 45, 2.85, 140, 2, 160, 204),
               'mundo_c': (-52, 45, 2.85, 70, 2, 160, 204),
               'brasil': (-52, -1, 8.0, 70, 2, 160, 204),
               'mini': (-46, 40, 1.6, 8, 26, 84, 78)}[nome]
        _MAPAS[nome] = D.Mapa(*cfg)
    return _MAPAS[nome]


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        self.M = mapa('mundo_d')

    def km(self, t): return KM_TOTAL * suave((t - 3.0) / 8.0)

    def desenhar(self, tela, t, tg):
        grade(tela)
        s = celular(tela, 34, 24, 78, 156)
        if t < 1.0:
            chat(tela, s, t, enviada=False, digitando='OI!', apertar=max(0, (t - .6) / .4))
        else:
            caixas = chat(tela, s, t, ticks=0 if t < 11.0 else 2)
            if 1.0 <= t < 3.2 and caixas:
                bx, by, bw, bh = caixas[-1]
                halo(tela, bx + bw / 2, by + bh / 2, 22 * (1 - (t - 1) / 2.2), CIANO)
        M = self.M
        M.desenhar(tela)
        continentes(tela, M)
        km = self.km(t)
        M.ponto(tela, 'SÃO PAULO', t, BRANCO, lado='d', dy=-12)
        M.ponto(tela, 'LISBOA', t, BRANCO if km < KM_LISBOA else VERDE, lado='e', dy=-12)
        p = desenhar_rota(tela, M, km, t)
        # o pacote voando do celular até São Paulo no mapa, e depois pela rota
        if 1.6 <= t < 3.0:
            u = ease((t - 1.6) / 1.4)
            a = (100, 110); b = M.cid('SÃO PAULO')
            x = a[0] + (b[0] - a[0]) * u; y = a[1] + (b[1] - a[1]) * u - math.sin(u * math.pi) * 30
            pacote(tela, x - 12, y - 7, 1, t)
        elif t >= 3.0:
            luz(tela, p[0], p[1], 2.5, BRANCO, AMARELO, CHAMA1)
        # contadores
        x0 = 312
        tela.texto('DISTÂNCIA', x0, 30, ACO3, tam=9, contorno=PRETO)
        tela.texto(fmt_km(km), x0, 42, BRANCO, tam=17, contorno=PRETO)
        tela.texto('TEMPO DE VIAGEM', x0, 76, ACO3, tam=9, contorno=PRETO)
        tela.texto(fmt_ms(viagem_ms(km)), x0, 88, AMARELO, tam=17, contorno=PRETO)
        if 3.0 <= t:
            tela.texto('CÂMERA LENTA', x0, 124, CIANO if int(t * 2) % 2 else ACO3, tam=9, contorno=PRETO)
        if km >= KM_TOTAL - .5:
            tela.texto('CHEGOU!', x0, 150, VERDE, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.clique(2600, .03), self.t0 + .95, .5)
        fx.put(fx.blip(84, .08), self.t0 + 1.0, .25)
        fx.put(fx.chiado(1.4, 1500, 6000), self.t0 + 1.6, .15)
        fx.put(fx.chiado(8.0, 600, 2600), self.t0 + 3.0, .05)
        fx.put(fx.sino(84), self.t0 + 11.0, .35)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        for k in range(26):                                    # chuva de bits
            x = (k * 37) % W
            y = (k * 53 + t * (20 + k % 5 * 6)) % 230 - 20
            tela.texto('1' if (k + int(t * 4)) % 3 else '0', x, y, FUNDO3 if k % 2 else TRACO, tam=9)
        for k in range(3):                                     # pacotes cruzando
            u = (t * .18 + k / 3) % 1.0
            pacote(tela, -30 + u * (W + 60), 182 + k * 0, k + 1, t, brilho=False)
        tela.texto('SÉRIE A JORNADA', W // 2, 26, ACO3, tam=9, centro=True, contorno=PRETO)
        if t > 1.2:
            tela.texto('DO ENVIAR AO LIDA', W // 2, 132, AMARELO, tam=17, centro=True, contorno=PRETO)
        n = int(t / .045)
        for j, linha in enumerate(("A JORNADA DE UMA", "MENSAGEM DE CELULAR")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 17)]
            tela.texto(vis, W // 2 - larg // 2, 58 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 2.0:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 9 * 18 // 2 + k * 18
                c = cor if t > 2.0 + k * .3 else FUNDO2
                tela.ret(x, 158, 14, 14, PRETO); tela.ret(x + 1, 159, 12, 12, c)
                tela.texto(str(k + 1), x + 7, 162, PRETO, tam=9, centro=True)

    def sons(self, fx):
        for k in range(9):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12, 14)[k], .08), self.t0 + 2.0 + k * .3, .14)


# ============================================================ enviar
class Enviar(Cena):
    def preparar(self):
        self.M = mapa('mundo_d')

    def desenhar(self, tela, t, tg):
        grade(tela)
        s = celular(tela, 22, 8, 96, 192)
        sx, sy, sw, sh = s
        if t < 6.0:
            dig = 'OI!'[:max(0, int((t - 1.0) / .45))]
            chat(tela, s, t, enviada=False, digitando=dig or None, apertar=max(0.0, min(1.0, (t - 5.4) / .4)))
            if t >= 3.0:                                         # foto anexada
                u = ease((t - 3.0) / .5)
                fw, fh = 34, 22
                yy = sy + sh - 16 - int(fh * u) - 4
                D.bolha(tela, sx + 3, yy - 2, fw + 4, fh + 4, FUNDO3, rabo=False)
                foto(tela, sx + 5, yy, fw, fh, t)
                rotulo(tela, 'FOTO', sx + fw + 12, yy + 6, ACO3)
        else:
            caixas = chat(tela, s, t, ticks=0)
            if t >= 22.0 and caixas:
                x0 = min(c[0] for c in caixas); y0 = min(c[1] for c in caixas)
                x1 = max(c[0] + c[2] for c in caixas); y1 = max(c[1] + c[3] for c in caixas)
                mira(tela, (x0 + x1) / 2, (y0 + y1) / 2, t, max(x1 - x0, y1 - y0) / 2 + 4)
                rotulo(tela, 'A NOSSA', sx + 6, y1 + 22, AMARELO)
                rotulo(tela, 'MENSAGEM', sx + 6, y1 + 32, AMARELO)
                fio(tela, sx + 30, y1 + 20, sx + 30, y1 + 4, AMARELO)
        if t >= 6.0 and t < 6.6:
            halo(tela, sx + sw - 7, sy + sh - 6, 14, CIANO)
        M = self.M
        if t >= .8:
            M.desenhar(tela)
            continentes(tela, M)
            pts = [M.cid(n) for n in ('SÃO PAULO', 'FORTALEZA', 'SINES', 'LISBOA')]
            M.ponto(tela, 'SÃO PAULO', t, BRANCO, lado='d', dy=-12)
            rotulo(tela, 'VOCÊ', M.cid('SÃO PAULO')[0] + 6, M.cid('SÃO PAULO')[1] + 4, ACO3)
            if t >= 7.2:
                M.ponto(tela, 'LISBOA', t, VERDE, lado='e', dy=-12)
                rotulo(tela, 'QUEM RECEBE', M.cid('LISBOA')[0] - 6, M.cid('LISBOA')[1] + 4, ACO3, centro='d')
                D.rota_tracejada(tela, pts, t, AMARELO if t >= 14.6 else ACO2)
                rotulo(tela, 'OCEANO', 200, 130, MISTURA2)
                rotulo(tela, 'ATLÂNTICO', 196, 140, MISTURA2)
        acende = None
        if 14.6 <= t < 21.8:
            acende = min(8, int((t - 14.8) / .7))
        painel_viagem(tela, -1, 0, t, ('A MENSAGEM', 'NO CELULAR' if t >= 6 else 'DIGITANDO', CIANO), acende=acende)

    def sons(self, fx):
        for k in range(3):
            fx.put(fx.clique(3800, .012), self.t0 + 1.0 + k * .45, .25)
        fx.put(fx.clique(1600, .03), self.t0 + 3.0, .3)
        fx.put(fx.clique(2600, .03), self.t0 + 5.8, .5)
        fx.put(fx.blip(84, .08), self.t0 + 6.0, .25)
        for k in range(9):
            fx.put(fx.blip(72 + k, .06), self.t0 + 14.8 + k * .7, .12)


# ============================================================ etapa 1: bits
class Bits(Cena):
    LETRAS = ['O', 'I', '!']

    def lay(self):
        if VERTICAL: return dict(xl=66, xn=96, xb=132, yb0=14)
        return dict(xl=92, xn=126, xb=180, yb0=0)

    def desenhar(self, tela, t, tg):
        grade(tela)
        L = self.lay()
        ys = [48, 88, 128]
        # origem das letras: a bolha no celular (ou no alto, no Short)
        if not VERTICAL:
            s = celular(tela, 10, 40, 58, 112)
            chat(tela, s, t, foto_on=False, ticks=0, texto='OI!')
            orig = (s[0] + s[2] - 18, s[1] + 20)
        else:
            orig = (150, 24)
            D.bolha(tela, 132, 16, 36, 13, MISTURA, rabo=False)
            tela.texto('OI!', 141, 19, BRANCO, tam=9)
        if t >= 2.0:
            rotulo(tela, 'LETRA', L['xl'] + 11, 34, ACO3, centro=True)
            rotulo(tela, 'Nº' if VERTICAL else 'NÚMERO', L['xn'] + 14, 34, ACO3, centro=True)
            rotulo(tela, 'BITS' if VERTICAL else 'BITS (ZEROS E UNS)', L['xb'] + 52, 34, ACO3, centro=True)
        for j, ch in enumerate(self.LETRAS):
            y = ys[j]
            ta = 1.0 + j * .8
            if t < ta: continue
            u = ease((t - ta) / .8)
            x = orig[0] + (L['xl'] - orig[0]) * u
            yy = orig[1] + (y - orig[1]) * u
            caixa(tela, int(x), int(yy), 22, 26, FUNDO3, luz_=TRACO, sombra=FUNDO2)
            tela.texto(ch, int(x) + 11, int(yy) + 4, BRANCO, tam=26, centro=True, contorno=PRETO)
            if u < 1: continue
            tn = 8.0 + j * 1.5
            if t >= tn:
                tela.texto('→', L['xl'] + 26, y + 9, ACO3, tam=9)
                n = str(NUM[ch])
                k = min(len(n), int((t - tn) / .15) + 1)
                tela.texto(n[:k], L['xn'] + 4, y + 6, AMARELO, tam=17, contorno=PRETO)
            if t >= 15.0 + j * 1.6:
                tela.texto('→', L['xn'] + 30, y + 9, ACO3, tam=9)
            for i, b in enumerate(BITS[ch]):
                tb = 15.2 + j * 1.6 + i * .18
                bx = L['xb'] + i * 13
                if t < tb:
                    tela.ret(bx, y + 5, 11, 15, PRETO); tela.ret(bx + 1, y + 6, 9, 13, FUNDO2)
                    continue
                if b == '1':
                    tela.ret(bx, y + 5, 11, 15, PRETO); tela.ret(bx + 1, y + 6, 9, 13, AMARELO)
                    tela.ret(bx + 1, y + 6, 9, 1, CHAMA0); tela.ret(bx + 1, y + 18, 9, 1, OLEO1)
                    tela.texto('1', bx + 6, y + 9, PRETO, tam=9, centro=True)
                else:
                    tela.ret(bx, y + 5, 11, 15, PRETO); tela.ret(bx + 1, y + 6, 9, 13, FUNDO3)
                    tela.texto('0', bx + 6, y + 9, ACO2, tam=9, centro=True)
            if t >= 22.0 and j == 0:
                bx0, bx1 = L['xb'], L['xb'] + 8 * 13 - 2
                tela.ret(bx0, y + 22, bx1 - bx0, 1, CIANO)
                tela.ret(bx0, y + 20, 1, 3, CIANO); tela.ret(bx1, y + 20, 1, 3, CIANO)
                rotulo(tela, '8 BITS = 1 BYTE', (bx0 + bx1) // 2, y + 25, CIANO, centro=True)
        # emoji (4 bytes) e depois a foto (300 mil bytes)
        if 22.0 <= t < 29.0:
            ye = 166
            x = L['xl'] + 11
            halo(tela, x, ye + 10, 12, CHAMA1)
            tela.disco(x, ye + 10, 10, PRETO); tela.disco(x, ye + 10, 9, AMARELO)
            tela.ret(x - 4, ye + 6, 2, 3, PRETO); tela.ret(x + 3, ye + 6, 2, 3, PRETO)
            tela.ret(x - 4, ye + 13, 9, 1, PRETO); tela.px(x - 5, ye + 12, PRETO); tela.px(x + 5, ye + 12, PRETO)
            tela.texto('→', L['xl'] + 26, ye + 7, ACO3, tam=9)
            rotulo(tela, 'EMOJI', L['xn'] + 2, ye + 6, BRANCO)
            for g in range(4):
                for i in range(8):
                    bx = L['xb'] + g * 26 + i * 3
                    on = (g * 8 + i) * 7 % 5 < 2
                    tela.ret(bx, ye + 4, 2, 11, AMARELO if on else FUNDO3)
                rotulo(tela, f"{g + 1}", L['xb'] + g * 26 + 11, ye + 17, ACO3, centro=True)
            rotulo(tela, '4 BYTES', L['xb'] + 52, ye - 7, CIANO, centro=True)
        elif t >= 29.0:
            ye = 166
            foto(tela, L['xl'], ye, 30, 20, t)
            tela.texto('→', L['xl'] + 34, ye + 7, ACO3, tam=9)
            for i in range(36):
                u = (t * .8 + i / 36) % 1.0
                bx = L['xl'] + 42 + u * (L['xb'] + 100 - L['xl'] - 42)
                by = ye + 2 + (i * 7) % 16
                tela.texto('1' if (i * 5 + int(t * 6)) % 3 else '0', bx, by, AMARELO if (i % 3) else CIANO, tam=9)
            n = int(300000 * ease((t - 29.0) / 3.0))
            rotulo(tela, f"{I.milhar(n)} BYTES", L['xb'] + 52, ye - 9, CIANO, centro=True)
        D.cartao(tela, t, 0, vertical=VERTICAL)
        if VERTICAL: return
        nb = sum(8 for j in range(3) if t >= 15.2 + j * 1.6 + 7 * .18)
        est = ('BITS DO OI!', f"{nb} BITS", CIANO)
        if t >= 29.0: est = ('COM A FOTO', '2.400.024 BITS', CIANO)
        painel_viagem(tela, 0, 0, t, est)

    def sons(self, fx):
        for j, ch in enumerate(self.LETRAS):
            fx.put(fx.chiado(.5, 1200, 5000), self.t0 + 1.0 + j * .8, .08)
            fx.put(fx.blip(76 + j * 2, .07), self.t0 + 8.0 + j * 1.5, .18)
            for i, b in enumerate(BITS[ch]):
                fx.put(fx.blip(88 if b == '1' else 76, .03), self.t0 + 15.2 + j * 1.6 + i * .18, .1 if b == '1' else .05)
        fx.put(fx.sino(81), self.t0 + 22.0, .15)
        for k in range(30):
            fx.put(fx.blip(90 + (k * 5) % 7, .02), self.t0 + 29.0 + k * .1, .04)


# ============================================================ etapa 2: cadeado
class Cadeado(Cena):
    def lay(self):
        if VERTICAL: return dict(xa=64, xb=202, w=34, h=66, y=100)
        return dict(xa=12, xb=244, w=46, h=88, y=100)

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        L = self.lay()
        cx = 150
        ya = L['y']
        sA = celular(tela, L['xa'], ya, L['w'], L['h'])
        sB = celular(tela, L['xb'], ya, L['w'], L['h'])
        for s, nm in ((sA, 'VOCÊ'), (sB, 'LISBOA')):
            tela.ret(s[0], s[1], s[2], 8, TRACO)
            tela.texto(nm, s[0] + 2, s[1] + 1, BRANCO, tam=9)
            dither(tela, s[0], s[1] + 8, s[2], s[3] - 8, FUNDO, FUNDO2)
        D.bolha(tela, sA[0] + sA[2] - 24, sA[1] + 14, 21, 11, MISTURA, rabo=False)
        tela.texto('OI!', sA[0] + sA[2] - 21, sA[1] + 16, BRANCO, tam=9)
        if t >= 33.0:
            D.bolha(tela, sB[0] + 3, sB[1] + 14, 21, 11, FUNDO3, rabo=False)
            cadeado(tela, sB[0] + 8, sB[1] + 13, 1, AMARELO)
        if not VERTICAL:
            rotulo(tela, 'CELULAR A', L['xa'] + L['w'] // 2, ya + L['h'] + 6, ACO3, centro=True)
            rotulo(tela, 'CELULAR B', L['xb'] + L['w'] // 2, ya + L['h'] + 6, ACO3, centro=True)
        # chaves em cima dos dois celulares (a de A entra na máquina e volta)
        ka = (L['xa'] + L['w'] // 2 - 8, ya - 16)
        kb = (L['xb'] + L['w'] // 2 - 8, ya - 16)
        brilha = 14.8 <= t < 22.0
        for (kx, ky) in (ka, kb):
            if brilha: halo(tela, kx + 8, ky, 14, CHAMA1)
            chave(tela, kx, ky, 1, AMARELO)
        if not VERTICAL:
            rotulo(tela, 'CHAVE', ka[0] + 8, ka[1] - 16, AMARELO, centro=True)
            rotulo(tela, 'CHAVE', kb[0] + 8, kb[1] - 16, AMARELO, centro=True)
        if brilha:
            for x in range(int(ka[0] + 26), int(kb[0] - 8), 3):
                if (x // 3 + int(t * 6)) % 2: tela.px(x, ka[1], CHAMA1)
            rotulo(tela, 'SÓ ESTES 2' if VERTICAL else 'SÓ ESTES 2 TÊM A CHAVE', cx, ka[1] + (-14 if VERTICAL else 6),
                   AMARELO, centro=True)
        # a máquina de embaralhar (no meio)
        my = 60 if not VERTICAL else 30
        caixa(tela, cx - 22, my - 14, 44, 28, ACO1, luz_=ACO3, sombra=ACO0)
        for k in range(4):
            a = t * 3 + k * math.pi / 2
            tela.px(cx + math.cos(a) * 7, my + math.sin(a) * 7, CHAMA1 if t < 7.6 else ACO2)
        tela.disco(cx, my, 3, PRETO); tela.disco(cx, my, 2, AMARELO if t < 7.6 else ACO2)
        if not VERTICAL: rotulo(tela, 'EMBARALHA', cx, my - 26, ACO3, centro=True)
        # fluxo de bits: legíveis de A até a máquina, embaralhados depois
        stream = '010011110100100100100001'
        rng_cores = (ROXO, ROSA, CIANO, LARANJA, VERDE)
        if t < 14.8:
            for i in range(24):
                u = (t * .22 - i * .03)
                if u < 0 or u > 1: continue
                if u < .5:
                    a = (sA[0] + sA[2] / 2, sA[1] + 10); b = (cx, my)
                    v = u / .5
                    x = a[0] + (b[0] - a[0]) * v; y = a[1] + (b[1] - a[1]) * v - math.sin(v * math.pi) * 18
                    tela.texto(stream[i], x, y - 3, BRANCO, tam=9, contorno=PRETO)
                else:
                    v = (u - .5) / .5
                    x = cx + v * 0; y = my + 20 + v * 20
                    if v < 1:
                        c = rng_cores[(i * 3 + int(t * 8)) % 5]
                        tela.texto('#%&@?!01'[(i * 5 + int(t * 9)) % 8], cx - 30 + (i % 8) * 8, my + 22 + (i // 8) * 9,
                                   c, tam=9, contorno=PRETO)
        # o bloco trancado
        if t >= 7.6:
            u = ease((t - 7.6) / 1.0)
            bx = cx - 26
            if t >= 29.0: bx = cx - 26 + (L['xb'] - 26 - (cx - 26)) * ease((t - 31.0) / 4.0) * (1 if t >= 31 else 0)
            by = 118 if not VERTICAL else 50
            if VERTICAL and t >= 29.0: by = 50 + 20 * ease((t - 31.0) / 4.0)
            halo(tela, bx + 26, by + 14, 22 * u, CHAMA1)
            caixa(tela, int(bx), int(by), 52, 28, ACO1, luz_=ACO3, sombra=ACO0)
            for j in range(3):
                for i in range(8):
                    c = rng_cores[(i * 7 + j * 3 + int(t * 5)) % 5]
                    tela.px(bx + 4 + i * 2, by + 6 + j * 6, c)
                    tela.px(bx + 4 + i * 2, by + 7 + j * 6, PRETO)
            cadeado(tela, int(bx + 26), int(by + 3), 2, AMARELO)
            if not VERTICAL and 8.6 <= t < 22.0:
                rotulo(tela, 'DADOS EMBARALHADOS', bx + 26, by + 36, ROSA, centro=True)
                fio(tela, bx + 12, by + 34, bx + 12, by + 22, ROSA)
        # bisbilhoteiro no caminho
        if 22.0 <= t < 29.0:
            ex, ey = cx + (0 if VERTICAL else 4), 166 if not VERTICAL else 40
            if VERTICAL: ey = 128
            u = ease((t - 22.0) / .6)
            tela.disco(ex - 30, ey, 7 * u + .5, PRETO); tela.disco(ex - 30, ey, 6 * u + .5, CERAMICA)
            tela.disco(ex - 30, ey, 3 * u + .5, TRACO); tela.disco(ex - 30, ey, 1.5 * u + .1, PRETO)
            painel(tela, ex - 18, ey - 9, 66, 18, borda=VERMELHO)
            tela.texto('#&%@!?01', ex - 12, ey - 3, ROSA if int(t * 4) % 2 else ROXO, tam=9)
            if not VERTICAL: rotulo(tela, 'QUEM PEGAR NO CAMINHO', ex + 15, ey + 14, ACO3, centro=True)
        # a empresa do aplicativo: nem ela abre
        if t >= 29.0:
            rx, ry = (cx - 60, 150) if not VERTICAL else (cx - 70, 150)
            if VERTICAL: rx, ry = cx - 20, 104
            D.rack(tela, rx, ry, 30, 46, t, seed=3)
            if not VERTICAL:
                rotulo(tela, 'SERVIDOR DO', rx + 36, ry + 8, ACO3)
                rotulo(tela, 'APLICATIVO', rx + 36, ry + 18, ACO3)
            xx, yy = (rx + 36, ry + 30) if not VERTICAL else (rx - 8, ry + 52)
            linha_grossa(tela, xx, yy, xx + 10, yy + 10, 3, VERMELHO)
            linha_grossa(tela, xx + 10, yy, xx, yy + 10, 3, VERMELHO)
            tela.texto('NÃO LÊ', xx + 14, yy + 2, VERMELHO, tam=9, contorno=PRETO)
        D.cartao(tela, t, 1, vertical=VERTICAL)
        if VERTICAL: return
        est = ('A MENSAGEM', 'ABERTA', VERDE) if t < 7.6 else ('A MENSAGEM', 'TRANCADA', AMARELO)
        painel_viagem(tela, 1, 0, t, est)
        if t >= 7.6: cadeado(tela, PX0 + 120, 134, 1, AMARELO)

    def sons(self, fx):
        for k in range(24):
            fx.put(fx.blip(80 + (k * 7) % 12, .02), self.t0 + 1.0 + k * .25, .04)
        fx.put(fx.clique(1200, .05), self.t0 + 8.0, .5)
        fx.put(fx.sino(76), self.t0 + 14.8, .2)
        fx.put(fx.blip(60, .2), self.t0 + 22.2, .15)
        fx.put(fx.blip(55, .25), self.t0 + 29.4, .15)


# ============================================================ etapa 3: pacotes
class Pacotes(Cena):
    X0, X1 = 66, 234

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        X0, X1 = self.X0, self.X1
        cortes = [X0 + 21 * k for k in range(1, 8)]
        # a mensagem inteira (trancada), cortada pela lâmina
        if t < 8.0:
            lam = X0 + (X1 - X0) * ease((t - 1.5) / 4.5)
            sep = ease((t - 6.0) / 1.0)
            for k in range(8):
                a = X0 + 21 * k; b = a + 21
                dx = (k - 3.5) * 3 * sep
                dy = 34 * ease((t - 6.6 - k * .08) / .8)
                caixa(tela, int(a + dx), int(22 + dy), 20 if lam > b or sep > 0 else 21, 20, ACO1, luz_=ACO3, sombra=ACO0)
                for i in range(4):
                    tela.px(a + dx + 3 + i * 4, 28 + dy, (ROXO, ROSA, CIANO, LARANJA)[(i + k) % 4])
                    tela.px(a + dx + 5 + i * 4, 34 + dy, (CIANO, ROXO, LARANJA, ROSA)[(i + k) % 4])
            cadeado(tela, X0 - 16, 22, 1, AMARELO)
            if 1.5 <= t < 6.2:
                halo(tela, lam, 32, 10, CIANO)
                tela.ret(int(lam), 14, 2, 36, BRANCO); tela.ret(int(lam) - 1, 12, 4, 3, MISTURA2)
            rotulo(tela, 'A MENSAGEM (TRANCADA)', 150, 8, ACO3, centro=True)
        # a fileira de pacotes
        if 7.0 <= t < 22.0:
            for k in range(6):
                u = ease((t - 7.0 - k * .12) / .6)
                x = X0 + k * 29
                y = 56 + (1 - u) * 10
                pacote(tela, x, y, k + 1, t, brilho=k == 0)
            rotulo(tela, '...', X1 - 6, 62, ACO3)
        # close do pacote nº 1
        if 7.6 <= t < 22.0:
            u = ease((t - 7.6) / .8)
            y0 = 96 + int((1 - u) * 20)
            hx0, hx1, dx1 = X0, X0 + 100, X1
            tela.ret(hx0 - 1, y0 - 1, dx1 - hx0 + 2, 52, PRETO)
            tela.ret(hx0, y0, hx1 - hx0, 50, AMARELO); tela.ret(hx0, y0, hx1 - hx0, 1, CHAMA0)
            tela.ret(hx0, y0 + 49, hx1 - hx0, 1, OLEO1)
            dither(tela, hx1, y0, dx1 - hx1, 50, ACO1, ACO0, int(t * 3) % 2)
            tela.ret(hx1, y0, 1, 50, PRETO)
            for k, linha in enumerate(('DE: CELULAR A', 'PARA: CELULAR B', 'Nº 1')):
                if t >= 8.2 + k * .6:
                    tela.texto(linha, hx0 + 4, y0 + 7 + k * 13, PRETO, tam=9)
            cadeado(tela, hx1 + 22, y0 + 12, 2, AMARELO)
            fio(tela, hx0 + 30, y0 - 8, hx0 + 30, y0 + 2, AMARELO)
            rotulo(tela, 'CABEÇALHO', hx0 + 2, y0 - 17, AMARELO)
            fio(tela, hx1 + 34, y0 - 8, hx1 + 34, y0 + 2, ACO4)
            rotulo(tela, 'DADOS', hx1 + 20, y0 - 17, ACO4)
            if t >= 14.8:
                v = ease((t - 14.8) / .8)
                xe = hx0 + (dx1 - hx0) * v
                tela.ret(hx0, y0 + 58, int(xe - hx0), 1, CIANO)
                tela.ret(hx0, y0 + 55, 1, 7, CIANO)
                if v >= 1: tela.ret(dx1 - 1, y0 + 55, 1, 7, CIANO)
                rotulo(tela, 'ATÉ 1.500 BYTES', (hx0 + dx1) // 2, y0 + 64, CIANO, centro=True)
        # contagem: o OI cabe num pacote; a foto vira mais de 200
        if 22.0 <= t < 29.0:
            pacote(tela, X0, 56, 1, t)
            rotulo(tela, 'O OI!: 1 PACOTE', X0 + 30, 60, BRANCO)
            n = int(201 * ease((t - 22.6) / 4.5))
            for i in range(n):
                x = X0 + (i % 20) * 8; y = 90 + (i // 20) * 8
                tela.ret(x, y, 7, 6, PRETO); tela.ret(x, y, 6, 5, LARANJA if i else AMARELO)
                tela.px(x, y, CHAMA0)
            txt = f"A FOTO: {n} PACOTES" if n < 201 else 'A FOTO: MAIS DE 200'
            rotulo(tela, txt, 150, 178, LARANJA, centro=True)
        if t >= 29.0:
            u = ease((t - 29.0) / 1.2)
            x = X0 + (126 - X0) * u; y = 90
            for i in range(1, 201, 7):
                xx = X0 + (i % 20) * 8; yy = 90 + (i // 20) * 8
                tela.ret(xx, yy, 6, 5, FUNDO3)
            pacote(tela, x, y, 1, t, s=2)
            mira(tela, x + 24, y + 14, t, 32)
            rotulo(tela, 'O PACOTE Nº 1', 150, 140, AMARELO, tam=17, centro=True)
        D.cartao(tela, t, 2, vertical=VERTICAL)
        if VERTICAL: return
        est = ('A MENSAGEM', 'CORTADA', LARANJA)
        if t >= 22.0: est = ('PACOTES', 'MAIS DE 200', LARANJA)
        if t >= 29.0: est = ('VAMOS SEGUIR', 'O Nº 1', AMARELO)
        painel_viagem(tela, 2, 0, t, est)

    def sons(self, fx):
        fx.put(fx.chiado(4.5, 3000, 8000), self.t0 + 1.5, .08)
        for k in range(7):
            fx.put(fx.clique(5000, .015), self.t0 + 1.5 + 4.5 * (k + 1) / 8, .25)
        for k in range(6):
            fx.put(fx.blip(79 + k, .05), self.t0 + 7.0 + k * .12, .1)
        for k in range(3):
            fx.put(fx.clique(2000, .03), self.t0 + 8.2 + k * .6, .2)
        for k in range(40):
            fx.put(fx.blip(84 + (k % 5), .02), self.t0 + 22.6 + k * .11, .04)
        fx.put(fx.sino(79), self.t0 + 29.0, .2)


# ============================================================ etapa 4: rádio
class Radio(Cena):
    def km(self, t): return KM_RADIO1 * suave((t - 2.0) / 26.0)

    def desenhar(self, tela, t, tg):
        D.cidade(tela, t, chao=176, seed=7)
        # torre do fundo (outra antena) e a nossa
        torre(tela, 132, 176, 70, t + .4, escala=.6)
        topo = torre(tela, 208, 176, 128, t)
        px_, py_ = 74, 120
        mao(tela, px_, py_, 24, 44)
        s = celular(tela, px_, py_, 24, 44)
        tela.ret(s[0], s[1], s[2], s[3], FUNDO3)
        tela.ret(s[0] + 2, s[1] + 3, s[2] - 4, 3, MISTURA)
        mao(tela, px_, py_, 24, 44, dedos=True)
        ant = (topo[0] - 6, topo[1] + 2)
        ondas(tela, px_ + 12, py_ - 2, ant[0], ant[1], t, ROXO, n=6, vel=.7)
        km = self.km(t)
        # o pacote nº 1 andando nas ondas
        u = km / KM_RADIO1
        x = px_ + 12 + (ant[0] - px_ - 12) * u; y = py_ - 2 + (ant[1] - py_ + 2) * u
        if t >= 2.0:
            luz(tela, x, y, 2.5, BRANCO, ROXO, ROSA)
            if t < 4: pacote(tela, px_ + 12 - 12, py_ - 22 - (t - 2) * 8, 1, t, brilho=False)
        if t >= 7.6 or VERTICAL:
            rotulo(tela, 'ANTENA', 236, 30, CERAMICA)
            fio(tela, 234, 34, topo[0] + 6, topo[1] + 2, CERAMICA)
            rotulo(tela, 'TORRE', 228, 120, ACO4)
            fio(tela, 226, 124, 214, 128, ACO4)
            rotulo(tela, 'ONDAS DE RÁDIO', 112, 68, ROXO, centro=True)
            rotulo(tela, 'CELULAR', 86, 194, ACO4, centro=True)
        if 14.8 <= t < 22.0:
            u = ease((t - 14.8) / .8)
            xa, xb = 132, 208
            y = 186
            tela.ret(xa, y, int((xb - xa) * u), 1, AMARELO)
            tela.ret(xa, y - 3, 1, 7, AMARELO)
            if u >= 1: tela.ret(xb, y - 3, 1, 7, AMARELO)
            rotulo(tela, '400 A 800 M', (xa + xb) // 2, y + 4, AMARELO, centro=True)
        D.cartao(tela, t, 3, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        painel_viagem(tela, 3, km, t, ('VELOCIDADE', '300.000 KM/S', ROXO), cam_lenta=True)

    def sons(self, fx):
        for k in range(int(self.dur / .7)):
            fx.put(fx.chiado(.4, 2000, 6000), self.t0 + 2.0 + k * .7, .035)
        fx.put(fx.blip(88, .06), self.t0 + 2.0, .2)
        fx.put(fx.sino(86), self.t0 + 28.0, .2)


# ============================================================ etapa 5: fibra
class Fibra(Cena):
    def km(self, t): return KM_RADIO1 + 40.0 * suave((t - 2.0) / 31.0)

    def lay(self):
        if VERTICAL: return dict(xl=62, x0=96, x1=240)
        return dict(xl=10, x0=44, x1=298)

    def desenhar(self, tela, t, tg):
        km = self.km(t)
        L = self.lay()
        if t < 7.2:
            # o pé da torre e o cabo descendo para debaixo da terra
            tela.buf[:PALCO_H] = FUNDO
            dither(tela, 0, 0, 300, 70, FUNDO, FUNDO2)
            tela.ret(0, 70, 300, 2, ACO2)
            dither(tela, 0, 72, 300, PALCO_H - 72, OLEO0, BRASA)
            dither(tela, 0, 120, 300, PALCO_H - 120, OLEO0, FUNDO2, 1)
            for k in range(14):
                tela.ret((k * 41) % 290, 80 + (k * 23) % 110, 4, 2, GAS2)
            for lado in (-1, 1):
                linha_grossa(tela, 150 + lado * 14, 70, 150 + lado * 6, -10, 3, PRETO)
                linha_grossa(tela, 150 + lado * 14, 70, 150 + lado * 6, -10, 1.4, ACO3)
            for k in range(5):
                y = 70 - k * 16
                tela.linha(150 - 13 + k * 1.6, y, 150 + 12 - k * 1.6, y - 16, ACO1)
            caixa(tela, 172, 52, 20, 18, ACO2, luz_=ACO4, sombra=ACO0)
            tela.px(176, 57, VERDE if int(t * 3) % 2 else ACO1)
            rotulo(tela, 'GABINETE', 182, 40, ACO4, centro=True)
            # duto: desce e segue para a direita
            pts = [(182, 70), (182, 140), (300, 140)]
            for (a, b), (c, d) in zip(pts, pts[1:]):
                linha_grossa(tela, a, b, c, d, 8, PRETO)
                linha_grossa(tela, a, b, c, d, 6, ACO1)
                linha_grossa(tela, a, b, c, d, 2, CIANO)
            u = ease((t - 1.0) / 5.5)
            Ls = [70, 118]
            dist = u * sum(Ls)
            if dist <= Ls[0]: p = (182, 70 + dist)
            else: p = (182 + dist - Ls[0], 140)
            if t >= 1.0: luz(tela, p[0], p[1], 3, BRANCO, CIANO, MISTURA)
            rotulo(tela, 'CABO DE FIBRA', 176, 96, CIANO, centro='d')
            rotulo(tela, 'ÓTICA, NO CHÃO', 176, 106, CIANO, centro='d')
        else:
            grade(tela, 0, 300)
            yc = 76
            D.laser(tela, L['xl'], yc, t)
            bits = '0100111101001001'
            vel = 26.0
            zy, (rc, rk, rp) = D.fibra_corte(tela, L['x0'], L['x1'], yc, t, bits=bits, vel=vel, raio_nucleo=9,
                                             destaque_reflexo=20.8 <= t < 27.2)
            # os bits em cima dos pulsos (o mesmo desenho de fibra_corte)
            bitlen = 14
            k0 = int(math.floor(-t * vel / bitlen)) - 1
            for k in range(k0, k0 + int((L['x1'] - L['x0']) / bitlen) + 3):
                xb = L['x0'] + t * vel + k * bitlen + bitlen * .39
                if not (L['x0'] + 4 < xb < L['x1'] - 4): continue
                b = bits[k % len(bits)]
                tela.texto(b, xb, yc - rp - 12, AMARELO if b == '1' else ACO2, tam=9, centro=True)
            rotulo(tela, 'LASER', L['xl'] + 15, yc + 22, ROSA, centro=True)
            if not VERTICAL:
                rotulo(tela, '1 = LUZ ACESA', L['xl'], 8, AMARELO)
                rotulo(tela, '0 = APAGADA', L['xl'] + 92, 8, ACO3)
            # rótulos das camadas
            xr = L['x1'] - 40
            for k, (nome, yy_peca, cor) in enumerate((('NÚCLEO', yc, CIANO), ('CASCA', yc + rk - 3, MISTURA2),
                                                      ('CAPA', yc + rp - 2, ACO4))):
                xt = L['x0'] + 10 + k * (52 if not VERTICAL else 46)
                yt = 112 + (k % 2) * 0
                rotulo(tela, nome, xt, yt, cor)
                fio(tela, xt + 8, yt - 2, xt + 8, yy_peca, cor)
            if 14.0 <= t < 20.8:
                # a ponta da fibra ao lado de um fio de cabelo
                cx1, cx2, cy = 116, 184, 148
                if VERTICAL: cx1, cx2 = 120, 186
                tela.disco(cx1, cy, 13, PRETO); tela.disco(cx1, cy, 12, ACO1)
                tela.disco(cx1, cy, 9, TRACO); tela.disco(cx1, cy, 3, CIANO)
                halo(tela, cx1, cy, 6, MISTURA2); tela.disco(cx1, cy, 2, BRANCO)
                tela.disco(cx2, cy, 12, PRETO); tela.disco(cx2, cy, 11, OLEO1)
                tela.disco(cx2 - 3, cy - 3, 4, LATAO)
                rotulo(tela, 'FIBRA', cx1, cy + 16, CIANO, centro=True)
                rotulo(tela, 'FIO DE CABELO', cx2, cy + 16, LATAO, centro=True)
                tela.texto('=', (cx1 + cx2) // 2, cy - 4, BRANCO, tam=17, centro=True, contorno=PRETO)
                rotulo(tela, 'DE PONTA, AUMENTADO', (cx1 + cx2) // 2, 125, ACO3, centro=True)
            if 20.8 <= t < 27.2:
                per = 4 * 9 + 6
                xr2 = L['x0'] + per * 2 + per / 4
                halo(tela, xr2, yc - 9, 7, BRANCO)
                xt, al = (xr2 + 4, 'd') if VERTICAL else (xr2 - 10, False)
                rotulo(tela, 'A LUZ BATE E VOLTA', xt, 136, BRANCO, centro=al)
                fio(tela, xr2, 134, xr2, yc - 9, BRANCO)
                rotulo(tela, 'NÃO ESCAPA DO VIDRO', xt, 148, ACO3, centro=al)
            if t >= 27.4:
                u = ease((t - 27.4) / 1.0)
                x0 = L['x0'] + (0 if VERTICAL else 10)
                wmax = (L['x1'] - x0 - 10)
                for k, (nome, frac, cor) in enumerate((('NO AR: 300.000 KM/S', 1.0, ROXO),
                                                       ('NO VIDRO: 200.000 KM/S', 2 / 3, CIANO))):
                    y = 128 + k * 22
                    rotulo(tela, nome, x0, y, cor)
                    tela.ret(x0, y + 11, int(wmax * frac * u) + 2, 7, PRETO)
                    tela.ret(x0 + 1, y + 12, int(wmax * frac * u), 5, cor)
        D.cartao(tela, t, 4, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        est = ('O PACOTE VIROU', 'PULSOS DE LUZ', CIANO) if t >= 7.2 else ('O PACOTE', 'DESCENDO O CABO', CIANO)
        painel_viagem(tela, 4, km, t, est, cam_lenta=True)

    def sons(self, fx):
        fx.put(fx.chiado(6.0, 200, 1200), self.t0 + 1.0, .1)
        fx.put(fx.chiado(26.0, 4000, 9000), self.t0 + 7.2, .03)
        bits = '0100111101001001'
        k = 0
        while 7.4 + k * (14 / 26.0) < self.dur:
            if bits[k % len(bits)] == '1':
                fx.put(fx.blip(96, .02), self.t0 + 7.4 + k * (14 / 26.0), .035)
            k += 1
        fx.put(fx.sino(88), self.t0 + 20.8, .12)


# ============================================================ etapa 6: rede (roteadores)
NOS = {'A': (-46.63, -23.55), 'B': (-43.9, -19.9), 'C': (-47.9, -15.8), 'D': (-38.5, -13.0),
       'E': (-42.8, -8.0), 'F': (-34.95, -8.05), 'H': (-38.54, -3.72)}
ARESTAS = [('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'), ('C', 'E'), ('D', 'E'), ('D', 'F'), ('E', 'H'), ('F', 'H')]
CAMINHOS = [['A', 'B', 'D', 'F', 'H'], ['A', 'C', 'E', 'H'], ['A', 'B', 'D', 'E', 'H']]


class Rede(Cena):
    def preparar(self):
        self.M = mapa('brasil')
        self.P = {k: self.M.px(*v) for k, v in NOS.items()}

    def pos_caminho(self, cam, u, pausa=.18):
        """Posição ao longo do caminho (u 0..1), parando um pouco em cada roteador."""
        pts = [self.P[n] for n in cam]
        n = len(pts) - 1
        f = u * n
        k = min(n - 1, int(f)); v = f - k
        v = 0.0 if v < pausa else (v - pausa) / (1 - pausa)
        a, b = pts[k], pts[k + 1]
        return (a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v), k, v

    def u1(self, t): return suave((t - 1.0) / 27.5)

    def km(self, t):
        return KM_RADIO1 + 40.0 + (KM_FORTALEZA - KM_RADIO1 - 40.0) * self.u1(t)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        M = self.M
        M.desenhar(tela)
        for a, b in ARESTAS:
            (x0, y0), (x1, y1) = self.P[a], self.P[b]
            linha_grossa(tela, x0, y0, x1, y1, 3, PRETO)
            tela.linha(x0, y0, x1, y1, TRACO)
            for k in range(0, 20):
                u = (k / 20 + t * .15) % 1.0
                if k % 5 == 0: tela.px(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, MISTURA)
        # cabo saindo para o mar em Fortaleza
        fx_, fy_ = self.P['H']
        if t >= 28.6:
            for k in range(30):
                if (k + int(t * 6)) % 2: continue
                tela.px(fx_ + k * 1.6, fy_ - k * 1.0, CIANO)
        # outros pacotes da foto, por outros caminhos
        if t >= 14.8:
            for j, (cam, cor) in enumerate(((CAMINHOS[1], LARANJA), (CAMINHOS[2], ROXO))):
                u = suave((t - 14.8 - j * 1.5) / 11.0)
                p, _, _ = self.pos_caminho(cam, u)
                pacote(tela, p[0] - 6, p[1] - 4, j + 2, t, brilho=False, trancado=False, cor=cor, rotulo_n=True)
        # o pacote nº 1
        u = self.u1(t)
        p, k, v = self.pos_caminho(CAMINHOS[0], u)
        ativo = CAMINHOS[0][k] if v == 0.0 else None
        for n, (x, y) in self.P.items():
            aceso = n == ativo and 0 < u < 1
            caixa(tela, int(x - 6), int(y - 4), 12, 8, ACO3 if aceso else ACO1, luz_=BRANCO if aceso else ACO3,
                  sombra=ACO0)
            tela.px(int(x - 3), int(y), VERDE if aceso or int(t * 2 + x) % 3 else FUNDO2)
            tela.px(int(x), int(y), VERDE if (int(t * 3 + y) % 2) else FUNDO2)
            if aceso: halo(tela, x, y, 10, VERDE)
        M.ponto(tela, 'SÃO PAULO', t, BRANCO, rot=False)
        rotulo(tela, 'SÃO PAULO', self.P['A'][0] - 8, self.P['A'][1] + 8, BRANCO, centro='d' if False else False)
        M.ponto(tela, 'FORTALEZA', t, AMARELO if t >= 28.6 else BRANCO, rot=False)
        rotulo(tela, 'FORTALEZA', self.P['H'][0] - 34, self.P['H'][1] + 7, AMARELO if t >= 28.6 else BRANCO)
        luz(tela, p[0], p[1], 2.5, BRANCO, AMARELO, CHAMA1)
        pacote(tela, p[0] - 12, p[1] - 20, 1, t, brilho=False)
        if 7.6 <= t < 14.6 and ativo:
            x, y = self.P[ativo]
            painel(tela, x + 10, y - 22, 74, 18, borda=VERDE)
            tela.texto('PARA: LISBOA', x + 14, y - 16, VERDE, tam=9)
        if 7.6 <= t < 14.6:
            bx, by = self.P['B']
            rotulo(tela, 'ROTEADOR', bx + 18, by + 18, VERDE)
            fio(tela, bx + 16, by + 20, bx + 5, by + 4, VERDE)
        if 22.0 <= t < 28.4:
            (x0, y0), (x1, y1) = self.P['A'], self.P['H']
            for k in range(0, int(math.hypot(x1 - x0, y1 - y0)), 3):
                f = k / math.hypot(x1 - x0, y1 - y0)
                tela.px(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, AMARELO)
            rotulo(tela, '2.360 KM', (x0 + x1) / 2 - 30, (y0 + y1) / 2, AMARELO)
            rotulo(tela, 'EM LINHA RETA', (x0 + x1) / 2 - 30, (y0 + y1) / 2 + 10, ACO3)
        km = self.km(t)
        D.cartao(tela, t, 5, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        hops = sum(1 for j in range(1, len(CAMINHOS[0])) if u * (len(CAMINHOS[0]) - 1) >= j)
        painel_viagem(tela, 5, km, t, ('ROTEADORES', f"{hops} DE 4", VERDE), cam_lenta=True)

    def sons(self, fx):
        n = len(CAMINHOS[0]) - 1
        ts = np.arange(0, self.dur, .02)
        prev = -1
        for t in ts:
            k = int(self.u1(t) * n)
            if k != prev and 0 < self.u1(t) < 1:
                fx.put(fx.blip(74 + k * 2, .07), self.t0 + t, .14)
                fx.put(fx.clique(2200, .02), self.t0 + t, .15)
            prev = k
        fx.put(fx.chiado(4.0, 300, 1500), self.t0 + 28.6, .08)


# ============================================================ etapa 7: oceano
class Oceano(Cena):
    V, REP = 30.0, 150

    def preparar(self):
        self.mar = D.Mar()

    def km(self, t): return KM_FORTALEZA + (KM_SINES - KM_FORTALEZA) * suave((t - .5) / 46.5)

    def desenhar(self, tela, t, tg):
        mar = self.mar
        des = self.V * t
        mar.desenhar(tela, t, des)
        land = 300 - (t - 43.4) * 34 if t > 43.4 else None
        xp = 150.0
        if t >= 45.0 and land is not None: xp = 150 + (land + 22 - 150) * ease((t - 45.0) / 2.6)
        def yc(x): return mar.chao(x, des) - 1
        x1 = int(land) if land is not None else W
        D.cabo_submarino(tela, 0, min(W, x1 + 4), yc, t, ponta_x=xp, rep_passo=self.REP, desloc=des)
        if land is not None:
            # a costa de Portugal subindo do fundo
            pts = [(land, PALCO_H), (land + 30, 120), (land + 60, 60), (land + 80, 20), (W + 400, 20), (W + 400, PALCO_H)]
            poligono(tela, [(a - 1, b) for a, b in pts], PRETO)
            poligono(tela, pts, LATAO)
            dither(tela, int(land + 40), 30, W, PALCO_H, OLEO0, LATAO)
            caixa(tela, int(land + 84), 4, 22, 16, CERAMICA, luz_=BRANCO, sombra=ACO2)
            rotulo(tela, 'SINES', int(land + 84), 24, BRANCO)
            rotulo(tela, 'PORTUGAL', int(land + 50), 50, CHAMA0)
        if not VERTICAL and not (14.8 <= t < 22.0) and not (29.0 <= t < 36.4):
            m = mapa('mini')
            m.desenhar(tela)
            a, b = m.cid('FORTALEZA'), m.cid('SINES')
            D.rota_tracejada(tela, [a, b], t, ACO2)
            f = (self.km(t) - KM_FORTALEZA) / (KM_SINES - KM_FORTALEZA)
            linha_grossa(tela, a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, 2, AMARELO)
            luz(tela, a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, 1.5, BRANCO, AMARELO)
            rotulo(tela, 'VOCÊ ESTÁ AQUI', 10, 108, ACO3)
        if land is None or land > 120:
            pass
        luz(tela, xp, yc(int(xp)) - 1, 3.2, BRANCO, CIANO, MISTURA)
        pacote(tela, xp - 12, yc(int(xp)) - 26, 1, t, brilho=False)
        if not VERTICAL and t < 14.8:
            rotulo(tela, 'CABO SUBMARINO', 20, 140, ACO4)
            fio(tela, 50, 150, 60, yc(60) - 2, ACO4)
        if 14.8 <= t < 22.0:
            D.corte_cabo(tela, 150, 74, 26, t)
            rotulo(tela, 'O CABO, DE FRENTE', 150, 36, BRANCO, centro=True)
            fio(tela, 196, 82, 152, 76, CIANO)
            rotulo(tela, 'FIBRAS', 198, 78, CIANO)
            tela.ret(110, 48, 1, 53, AMARELO); tela.ret(107, 48, 7, 1, AMARELO); tela.ret(107, 100, 7, 1, AMARELO)
            rotulo(tela, 'UNS', 104, 64, AMARELO, centro='d')
            rotulo(tela, '2,5 CM', 104, 74, AMARELO, centro='d')
            rotulo(tela, '(AUMENTADO)', 150, 106, ACO3, centro=True)
        if 22.0 <= t < 28.8:
            xr = round((150 + des) / self.REP) * self.REP - des
            if -20 < xr < W:
                halo(tela, xr, yc(int(max(0, xr))) - 2, 16, CIANO)
                rotulo(tela, 'REPETIDOR', xr, 110, CIANO, centro=True)
                fio(tela, xr, 120, xr, yc(int(max(0, xr))) - 7, CIANO)
                rotulo(tela, 'REFORÇA A LUZ', xr, 92, ACO3, centro=True)
        if 29.0 <= t < 36.4:
            n = int(100 * ease((t - 29.0) / 2.0))
            for i in range(n):
                x = 120 + (i % 10) * 6; y = 34 + (i // 10) * 6
                tela.ret(x, y, 5, 5, PRETO); tela.ret(x, y, 4, 4, CIANO if i < 99 else ACO2)
            if t > 31.0:
                tela.texto('99%', 150, 100, CIANO, tam=26, centro=True, contorno=PRETO)
                rotulo(tela, 'DOS DADOS ENTRE OCEANOS', 150, 126, BRANCO, centro=True)
        km = self.km(t)
        D.cartao(tela, t, 6, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        # progresso Fortaleza -> Sines
        painel_viagem(tela, 6, km, t, None, cam_lenta=True)
        f = (km - KM_FORTALEZA) / (KM_SINES - KM_FORTALEZA)
        tela.texto('FORTALEZA', PX0, 126, ACO3, tam=9, contorno=PRETO)
        tela.texto('SINES', PX0 + 166, 126, ACO3, tam=9, centro='d', contorno=PRETO)
        for x in range(PX0, PX0 + 166, 2):
            tela.px(x, 142 + int(1.5 * math.sin(x * .2 + t * 2)), MISTURA)
        tela.ret(PX0, 146, int(166 * f), 2, CIANO)
        luz(tela, PX0 + 166 * f, 147, 1.5, BRANCO, CIANO)
        tela.texto(f"{I.milhar(km - KM_FORTALEZA)} DE 5.900 KM", PX0, 150, CIANO, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(47.0, 80, 400), self.t0, .08)
        k = 1
        while True:
            t = (k * self.REP - 150) / self.V
            if t > self.dur: break
            if t > 0: fx.put(fx.sino(93, .5), self.t0 + t, .07)
            k += 1
        for k in range(20):
            fx.put(fx.blip(98, .02), self.t0 + 29.0 + k * .1, .03)
        fx.put(fx.sino(81), self.t0 + 47.0, .2)


# ============================================================ etapa 8: servidor
class Servidor(Cena):
    RX = [16, 72, 130, 188, 246]

    def km(self, t): return KM_SINES + (KM_LISBOA - KM_SINES) * suave((t - .5) / 7.0)

    def pos(self, t):
        """Caminho do pacote: entra pela calha, desce no rack do meio, sai pela direita."""
        if t < 6.0:
            u = ease(t / 6.0) if False else min(1.0, t / 6.0)
            return -14 + (150 + 14) * u, 26
        if t < 8.0:
            u = ease((t - 6.0) / 2.0)
            return 150, 26 + (98 - 26) * u
        if t < 28.6: return 150, 98
        if t < 30.6:
            u = ease((t - 28.6) / 2.0)
            return 150, 98 - (98 - 26) * u
        u = min(1.0, (t - 30.6) / 2.4)
        return 150 + (W - 150 + 20) * u, 26

    def desenhar(self, tela, t, tg):
        D.datacenter(tela, t)
        for k, x in enumerate(self.RX):
            D.rack(tela, x, 44, 40 if k != 2 else 40, 134, t, seed=k + 1, destaque=k == 2)
        tela.ret(148, 26, 4, 18, PRETO); tela.ret(149, 26, 2, 18, CIANO)
        x, y = self.pos(t)
        grande = 8.0 <= t < 28.6
        if grande:
            halo(tela, 150, 112, 40, CHAMA1)
            pacote(tela, 150 - 24, 98, 1, t, s=2)
        else:
            luz(tela, x, y, 2.5, BRANCO, CIANO)
            pacote(tela, x - 12, y + 6, 1, t, brilho=False)
        if t >= 7.6 and t < 28.6 and not VERTICAL:
            rotulo(tela, 'SERVIDOR DO', 150, 184, ROSA, centro=True)
            rotulo(tela, 'APLICATIVO', 150, 194, ROSA, centro=True)
        if t < 7.6 and not VERTICAL:
            rotulo(tela, 'DATA CENTER', 8, 6, ROSA)
            rotulo(tela, '(EXEMPLO: PERTO DE LISBOA)', 8, 186, ACO3)
        if 14.8 <= t < 28.4:
            le_dados = t >= 22.0
            bx = 126 + (16 if not le_dados else 34 + 10 * math.sin(t * 4))
            halo(tela, bx, 112, 6, VERDE if not le_dados else VERMELHO)
            tela.ret(int(bx), 94, 1, 36, VERDE if not le_dados else VERMELHO)
            painel(tela, 96, 46, 108, 40, borda=VERDE if not le_dados else VERMELHO)
            if not le_dados:
                tela.texto('PARA: CELULAR B', 102, 52, VERDE, tam=9)
                tela.texto('DE: CELULAR A', 102, 63, ACO4, tam=9)
                tela.texto('Nº 1', 102, 74, ACO4, tam=9)
                tique(tela, 190, 52, VERDE)
            else:
                tela.texto('CONTEÚDO:', 102, 52, ACO4, tam=9)
                tela.texto('#&%@!?', 102, 64, ROSA if int(t * 4) % 2 else ROXO, tam=9)
                tela.texto('TRANCADO', 146, 72, VERMELHO, tam=9)
        km = self.km(t)
        D.cartao(tela, t, 7, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        est = ('O SERVIDOR LÊ', 'O ENDEREÇO', VERDE) if t < 22.0 else ('O CONTEÚDO', 'CONTINUA TRANCADO', AMARELO)
        painel_viagem(tela, 7, km, t, est)

    def sons(self, fx):
        fx.put(fx.chiado(6.0, 2000, 7000), self.t0, .05)
        fx.put(fx.clique(1500, .04), self.t0 + 8.0, .4)
        fx.put(fx.chiado(6.0, 600, 2000), self.t0 + 14.8, .05)
        fx.put(fx.blip(84, .1), self.t0 + 16.0, .15)
        fx.put(fx.blip(58, .25), self.t0 + 22.5, .15)
        fx.put(fx.chiado(2.4, 2000, 7000), self.t0 + 30.6, .06)


# ============================================================ etapa 9: chegada
ORDEM = [3, 1, 5, 2, 8, 4, 6, 10, 9, 12, 11]


class Chegada(Cena):
    def km(self, t): return KM_LISBOA + (KM_TOTAL - KM_LISBOA) * suave((t - 2.5) / 4.5)

    def desenhar(self, tela, t, tg):
        km = self.km(t)
        if t < 7.6:
            D.cidade(tela, t, chao=176, seed=21)
            topo = torre(tela, 110, 176, 120, t)
            px_, py_ = 196, 116
            mao(tela, px_, py_, 26, 46)
            s = celular(tela, px_, py_, 26, 46)
            tela.ret(s[0], s[1], s[2], s[3], FUNDO3)
            mao(tela, px_, py_, 26, 46, dedos=True)
            ant = (topo[0] + 6, topo[1] + 2)
            # sobe pela torre (fibra) e vai por rádio até o celular
            if t < 2.5:
                u = ease(t / 2.5)
                p = (110, 176 - (176 - ant[1]) * u)
            else:
                u = (km - KM_LISBOA) / (KM_TOTAL - KM_LISBOA)
                p = (ant[0] + (px_ + 13 - ant[0]) * u, ant[1] + (py_ - 2 - ant[1]) * u)
                ondas(tela, ant[0], ant[1], px_ + 13, py_ - 2, t, ROXO, n=5, vel=.8)
            luz(tela, p[0], p[1], 2.5, BRANCO, CHAMA1, AMARELO)
            rotulo(tela, 'LISBOA', 8, 6, BRANCO)
            rotulo(tela, 'CELULAR B', px_ + 13, 194, ACO4, centro=True)
        else:
            grade(tela, 0, 300)
            rotulo(tela, 'MONTANDO A FOTO' if VERTICAL else 'MONTANDO A FOTO (AMOSTRA: 12 PACOTES)', 150, 22, ACO3,
                   centro=True)
            slots = {}
            for n in range(1, 13):
                c = (n - 1) % 4; r = (n - 1) // 4
                slots[n] = (70 + c * 41, 40 + r * 26)
            junta = ease((t - 29.0) / 1.5) if t >= 29.0 else 0.0
            for n, (x, y) in slots.items():
                if junta > 0:
                    x = x + (150 - 12 - x) * 0 ;
                tela.ret(x - 1, y - 1, 34, 20, PRETO); tela.ret(x, y, 32, 18, FUNDO2)
                tela.texto(str(n), x + 16, y + 6, TRACO, tam=9, centro=True)
            chegou = {}
            for i, n in enumerate(ORDEM):
                ta = 8.0 + i * 1.25
                if t >= ta: chegou[n] = ta
            if t >= 26.0: chegou[7] = 26.0
            falta7 = 22.0 <= t < 26.0
            for n, ta in chegou.items():
                x, y = slots[n]
                u = ease((t - ta) / .7)
                xi = 150 - 12 if n != 7 else 150 - 12
                yi = -16
                xx = xi + (x + 4 - xi) * u; yy = yi + (y + 2 - yi) * u
                if junta > 0:
                    xx = xx + (150 - 12 - xx) * junta
                    yy = yy + (132 - yy) * junta
                if junta < .95:
                    pacote(tela, xx, yy, n, t, brilho=u < 1, trancado=False, cor=AMARELO if n == 1 else LARANJA)
            if falta7:
                x, y = slots[7]
                if int(t * 4) % 2: tela.ret_vazado(x - 2, y - 2, 36, 22, VERMELHO)
                rotulo(tela, 'FALTA O Nº 7!', 150, 124, VERMELHO, centro=True)
                if t >= 23.0:
                    for k in range(5):
                        yy = 156 - ((t * 30 + k * 6) % 22)
                        seta(tela, 150, int(yy), 0, -1, AMARELO, 4)
                    rotulo(tela, 'MANDA DE NOVO, POR FAVOR', 150, 160, AMARELO, centro=True)
            if junta > 0:
                u = junta
                halo(tela, 150, 142, 30 * u, CHAMA1)
                caixa(tela, 120, 128, 60, 28, ACO1, luz_=ACO3, sombra=ACO0)
                for k in range(10):
                    tela.px(124 + k * 2, 134 + (k % 3) * 6, (ROXO, ROSA, CIANO)[k % 3])
                cadeado(tela, 150, 133, 2, AMARELO)
                if t >= 30.5: rotulo(tela, 'INTEIRA, MAS TRANCADA', 150, 162, AMARELO, centro=True)
            if not VERTICAL and t < 22.0:
                rotulo(tela, 'CADA UM VAI PARA O', 150, 130, ACO3, centro=True)
                rotulo(tela, 'LUGAR DO SEU NÚMERO', 150, 140, ACO3, centro=True)
        D.cartao(tela, t, 8, vertical=VERTICAL)
        leitura_vertical(tela, km)
        if VERTICAL: return
        n = len([1 for i, nn in enumerate(ORDEM) if t >= 8.0 + i * 1.25]) + (1 if t >= 26.0 else 0)
        est = ('O PACOTE Nº 1', 'CHEGANDO', CHAMA1) if t < 7.6 else ('PACOTES', f"{min(12, n)} DE 12", CHAMA1)
        painel_viagem(tela, 8, km, t, est, cam_lenta=t < 7.6)

    def sons(self, fx):
        fx.put(fx.chiado(2.4, 200, 1000), self.t0, .08)
        for k in range(6):
            fx.put(fx.chiado(.4, 2000, 6000), self.t0 + 2.5 + k * .8, .03)
        fx.put(fx.sino(88), self.t0 + 7.0, .2)
        for i, n in enumerate(ORDEM):
            fx.put(fx.blip(76 + n, .06), self.t0 + 8.0 + i * 1.25 + .65, .12)
        fx.put(fx.blip(60, .3), self.t0 + 22.2, .15)
        fx.put(fx.blip(83, .06), self.t0 + 26.65, .15)
        fx.put(fx.clique(1200, .05), self.t0 + 30.0, .4)


# ============================================================ abrir: destrancar, entregue, lida
class Abrir(Cena):
    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        sB = celular(tela, 120, 4, 104, 198)
        sx, sy, sw, sh = sB
        cx = sx + sw // 2
        tela.ret(sx, sy, sw, 11, TRACO); tela.texto('CELULAR B', sx + 4, sy + 2, BRANCO, tam=9)
        sA = celular(tela, 62, 100, 52, 96)
        ax, ay, aw, ah = sA
        tela.ret(ax, ay, aw, 9, TRACO); tela.texto('A', ax + 3, ay + 1, BRANCO, tam=9)
        # o celular A: a bolha "OI!" e os tiques
        nt = 0 if t < 16.6 else 2
        ct = ACO3 if t < 23.8 else CIANO
        D.bolha(tela, ax + aw - 40, ay + 30, 36, 12, MISTURA, rabo=False)
        tela.texto('OI!', ax + aw - 37, ay + 33, BRANCO, tam=9)
        if nt == 0: D.relogio(tela, ax + aw - 14, ay + 33, MISTURA2)
        else: tiques(tela, ax + aw - 16, ay + 34, 2, ct)
        foto(tela, ax + aw - 34, ay + 12, 28, 15, t)
        if t >= 16.6:
            rotulo(tela, 'ENTREGUE' if t < 23.8 else 'LIDA', ax + aw // 2, ay - 12, ACO4 if t < 23.8 else CIANO, centro=True)
        # tela do B
        if t < 12.6:
            dither(tela, sx, sy + 11, sw, sh - 11, FUNDO, FUNDO2)
        if t < 7.6:
            ab = ease((t - 3.6) / 1.0)
            if ab < 1:
                halo(tela, cx, 80, 24, CHAMA1)
                caixa(tela, cx - 30, 66, 60, 30, ACO1, luz_=ACO3, sombra=ACO0)
                for k in range(12):
                    tela.px(cx - 26 + k * 2, 72 + (k % 3) * 7, (ROXO, ROSA, CIANO)[k % 3])
            cadeado(tela, cx - 10, 52 - int(ab * 6), 2, AMARELO, aberto=ab)
            # a chave do celular B entra no cadeado
            u = ease((t - 1.0) / 2.4)
            kx = sx + 8 + (cx - 24 - sx - 8) * u
            ky = sy + 150 + (66 - sy - 150) * u
            chave(tela, kx, ky, 1, AMARELO, ang=-.4 * (1 - u))
            if ab < 1: rotulo(tela, 'A CHAVE DO B', cx, 120, AMARELO, centro=True)
            if ab >= 1:
                for i in range(24):
                    tela.texto('01001111010010010010000'[i % 23], sx + 6 + (i % 12) * 7, 100 + (i // 12) * 10, CIANO, tam=9)
        elif t < 12.6:
            for j, ch in enumerate('OI!'):
                y = 50 + j * 30
                fase = 0 if t < 9.2 + j * .3 else (1 if t < 10.8 + j * .3 else 2)
                if fase == 0: tela.texto(BITS[ch], cx, y, CIANO, tam=9, centro=True)
                elif fase == 1: tela.texto(str(NUM[ch]), cx, y - 3, AMARELO, tam=17, centro=True, contorno=PRETO)
                else: tela.texto(ch, cx, y - 6, BRANCO, tam=26, centro=True, contorno=PRETO)
        else:
            chat_recebido(tela, sB, t, mostra=ease((t - 12.6) / 1.2), nome='SÃO PAULO')
        # os avisos voltando para o A
        for ta, txt, cor in ((14.8, 'ENTREGUE', ACO4), (22.0, 'LIDA', CIANO)):
            if ta <= t < ta + 1.8:
                u = ease((t - ta) / 1.8)
                x = cx + (ax + aw // 2 - cx) * u
                y = 100 + (ay + 20 - 100) * u - math.sin(u * math.pi) * 40
                halo(tela, x, y, 10, cor)
                caixa(tela, int(x - 9), int(y - 5), 18, 10, FUNDO3, luz_=cor, sombra=FUNDO2)
                tiques(tela, int(x - 6), int(y - 2), 2, cor)
                rotulo(tela, txt, x, y - 16, cor, centro=True)
        if 22.0 <= t < 24.0:
            mira(tela, cx, 80, t, 30)
            rotulo(tela, 'ABRIU A CONVERSA', cx, 196, BRANCO, centro=True)
        if VERTICAL: return
        est = ('A MENSAGEM', 'TRANCADA', AMARELO)
        if t >= 4.6: est = ('A MENSAGEM', 'DESTRANCADA', VERDE)
        if t >= 16.6: est = ('O AVISO', 'ENTREGUE', ACO4)
        if t >= 23.8: est = ('O AVISO', 'LIDA', CIANO)
        painel_viagem(tela, 8, KM_TOTAL, t, est, tudo_feito=t >= 16.6)

    def sons(self, fx):
        fx.put(fx.clique(2400, .03), self.t0 + 3.4, .35)
        fx.put(fx.clique(1200, .06), self.t0 + 4.2, .5)
        fx.put(fx.sino(84), self.t0 + 4.4, .2)
        for j in range(3):
            fx.put(fx.blip(80 + j * 2, .05), self.t0 + 9.2 + j * .3, .12)
            fx.put(fx.blip(86 + j * 2, .05), self.t0 + 10.8 + j * .3, .12)
        fx.put(fx.blip(88, .08), self.t0 + 16.6, .2); fx.put(fx.blip(93, .08), self.t0 + 16.75, .2)
        fx.put(fx.blip(91, .08), self.t0 + 23.8, .2); fx.put(fx.blip(96, .08), self.t0 + 23.95, .2)


# ============================================================ a conta
class Conta(Cena):
    def preparar(self):
        self.M = mapa('mundo_c')

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        if t < 22.0:
            M = self.M
            M.desenhar(tela)
            continentes(tela, M)
            km = KM_TOTAL * ((t * .25) % 1.0)
            pts = [M.cid(n) for n in ('SÃO PAULO', 'FORTALEZA', 'SINES', 'LISBOA')]
            for a, b in zip(pts, pts[1:]):
                linha_grossa(tela, a[0], a[1], b[0], b[1], 4, PRETO)
                linha_grossa(tela, a[0], a[1], b[0], b[1], 2, AMARELO)
            if t >= 14.8:
                # o cabo de verdade faz curvas
                for a, b in zip(pts, pts[1:]):
                    L = math.hypot(b[0] - a[0], b[1] - a[1])
                    nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
                    for k in range(int(L)):
                        if k % 2: continue
                        f = k / L
                        o = 6 * math.sin(f * math.pi * 3)
                        tela.px(a[0] + (b[0] - a[0]) * f + nx * o, a[1] + (b[1] - a[1]) * f + ny * o, LARANJA)
                rotulo(tela, 'O CABO REAL', 76, 96, LARANJA)
                rotulo(tela, 'FAZ CURVAS', 76, 106, LARANJA)
                for p in pts:
                    caixa(tela, int(p[0] + 4), int(p[1] + 4), 7, 5, ACO2, luz_=ACO4, sombra=ACO0)
            for nm, lado in (('SÃO PAULO', 'd'), ('FORTALEZA', 'd'), ('LISBOA', 'e')):
                M.ponto(tela, nm, t, BRANCO, lado=lado, dy=-12)
            p, _ = rota_km(M, km)
            luz(tela, p[0], p[1], 2.5, BRANCO, AMARELO, CHAMA1)
            ms = [((pts[0][0] + pts[1][0]) / 2 + 6, (pts[0][1] + pts[1][1]) / 2, '2.360 KM'),
                  ((pts[1][0] + pts[2][0]) / 2 - 6, (pts[1][1] + pts[2][1]) / 2 - 4, '5.900 KM'),
                  (pts[3][0] - 6, pts[3][1] + 8, '88 KM')]
            for x, y, s in ms:
                rotulo(tela, s, x, y, AMARELO, centro='d' if s != '2.360 KM' else False)
            if t >= 7.6 and not VERTICAL:
                painel(tela, 118, 185, 110, 18, borda=AMARELO)
                tela.texto('8.350 KM = ~42 MS', 173, 190, AMARELO, tam=9, centro=True)
        else:
            base = 162
            esc = .85
            bars = [(78, 'VIAGEM', 'SÓ IDA', 42, 42, CIANO, '42 MS', 22.0),
                    (134, 'OCEANO', 'IDA+VOLTA', 60, 60, MISTURA, '< 60 MS', 29.0),
                    (190, 'PISCAR', 'DE OLHOS', 100, 150, ROSA, '100-150 MS', 22.6)]
            rotulo(tela, 'MILÉSIMOS DE SEGUNDO (MS)', 150, 6, ACO3, centro=True)
            for v in (50, 100, 150):
                y = base - int(v * esc)
                for x in range(66, 234, 4): tela.px(x, y, FUNDO3)
                if not VERTICAL: rotulo(tela, str(v), 64, y - 3, ACO2, centro='d')
            for x, n1, n2, v1, v2, cor, val, ta in bars:
                if t < ta: continue
                u = ease((t - ta) / 1.2)
                h1, h2 = int(v1 * esc * u), int(v2 * esc * u)
                tela.ret(x - 1, base - h2 - 1, 34, h2 + 2, PRETO)
                dither(tela, x, base - h2, 32, h2 - h1, cor, FUNDO2)
                tela.ret(x, base - h1, 32, h1, cor)
                tela.ret(x, base - h1, 32, 1, BRANCO)
                rotulo(tela, val, x + 16, base - h2 - 12, cor, centro=True)
                rotulo(tela, n1, x + 16, base + 4, BRANCO, centro=True)
                if not VERTICAL: rotulo(tela, n2, x + 16, base + 13, ACO3, centro=True)
            if t >= 22.6:
                ex, ey = 232, 70
                fecha = int(t * .8) % 3 == 0 and (t * .8) % 1 < .18
                for dx in range(-11, 12):
                    hh = int(7 * math.sqrt(max(0, 1 - (dx / 11) ** 2)))
                    tela.ret(ex + dx, ey - hh - 1, 1, 2 * hh + 3, PRETO)
                    if fecha: tela.ret(ex + dx, ey - hh, 1, 2 * hh + 1, LATAO)
                    else: tela.ret(ex + dx, ey - hh, 1, 2 * hh + 1, CERAMICA)
                if fecha: tela.ret(ex - 10, ey, 21, 1, OLEO0)
                else: tela.disco(ex, ey, 4, TRACO); tela.disco(ex, ey, 2, PRETO); tela.px(ex - 2, ey - 2, BRANCO)
        if VERTICAL:
            if t < 22.0: leitura_vertical(tela, KM_TOTAL)
            return
        painel_viagem(tela, 8, KM_TOTAL, t, ('SÓ A VIAGEM', '~42 MS', AMARELO), tudo_feito=True)

    def sons(self, fx):
        for k in range(int(22 / 4)):
            fx.put(fx.chiado(.6, 1500, 5000), self.t0 + k * 4, .04)
        fx.put(fx.blip(76, .1), self.t0 + 22.0, .2)
        fx.put(fx.blip(79, .1), self.t0 + 22.6, .2)
        fx.put(fx.blip(83, .1), self.t0 + 29.0, .2)


# ============================================================ resumo
CARTAS = ['BITS', 'CADEADO', 'PACOTES', 'RÁDIO', 'FIBRA', 'REDE', 'OCEANO', 'SERVIDOR', 'CHEGADA']
T_CARTA = [0.5, 2.8, 5.1, 7.6, 10.0, 12.3, 14.8, 18.3, 22.0]


class Resumo(Cena):
    def centro(self, k):
        r = k // 3; c = k % 3
        if r == 1: c = 2 - c                      # caminho em S
        return 92 + c * 58, 37 + r * 64

    def desenhar(self, tela, t, tg):
        grade(tela, 0, 300)
        at = max([k for k, ta in enumerate(T_CARTA) if t >= ta] or [0])
        # caminho
        for k in range(8):
            a, b = self.centro(k), self.centro(k + 1)
            linha_grossa(tela, a[0], a[1], b[0], b[1], 3, TRACO)
        for k in range(9):
            x, y = self.centro(k)
            nome, cor = ETAPAS[k]
            aceso = k <= at
            painel(tela, x - 26, y - 28, 52, 56, borda=cor if k == at else (ACO1 if aceso else FUNDO3))
            tela.texto(str(k + 1), x - 22, y - 25, cor if aceso else ACO1, tam=9)
            self.icone(tela, k, x, y - 4, t, aceso)
            tela.texto(CARTAS[k], x, y + 16, cor if aceso else ACO1, tam=9, centro=True)
        # o pacote andando pelo S
        if t < T_CARTA[-1]:
            k = at
            ta, tb = T_CARTA[k], T_CARTA[min(8, k + 1)]
            u = ease((t - ta) / max(.1, (tb - ta))) if k < 8 else 0
            a, b = self.centro(k), self.centro(min(8, k + 1))
            p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        else:
            p = self.centro(8)
        luz(tela, p[0] + 22, p[1] - 24, 2.2, BRANCO, AMARELO, CHAMA1)
        if VERTICAL: return
        painel_viagem(tela, 8, KM_TOTAL, t, ('ENTREGUE E LIDA', 'OI!', BRANCO), tudo_feito=t >= 22.0)
        tiques(tela, PX0 + 40, 140, 2, CIANO)

    def icone(self, tela, k, x, y, t, aceso):
        c = None if aceso else ACO1
        if k == 0:
            tela.texto('01', x, y - 6, c or CIANO, tam=17, centro=True, contorno=PRETO)
        elif k == 1:
            cadeado(tela, x - 10, y - 10, 2, c or AMARELO)
        elif k == 2:
            pacote(tela, x - 18, y - 8, 1, t, brilho=False, cor=c or AMARELO, trancado=False)
            pacote(tela, x - 4, y - 2, 2, t, brilho=False, cor=c or LARANJA, trancado=False)
        elif k == 3:
            tela.linha(x - 6, y + 10, x, y - 8, c or ACO3); tela.linha(x + 6, y + 10, x, y - 8, c or ACO3)
            tela.linha(x - 4, y + 4, x + 4, y + 4, c or ACO2)
            if aceso:
                for r in (5, 9):
                    tela.anel(x, y - 8, r + (t * 6) % 4, ROXO, .5)
                tela.ret(x - 6, y - 12, 12, 2, FUNDO2)
        elif k == 4:
            tela.ret(x - 20, y - 4, 40, 9, PRETO); tela.ret(x - 20, y - 3, 40, 7, ACO1)
            tela.ret(x - 20, y - 1, 40, 3, TRACO)
            if aceso:
                for j in range(4):
                    xx = x - 20 + ((t * 30 + j * 10) % 40)
                    tela.ret(int(xx), y, 4, 1, BRANCO); tela.px(int(xx) - 1, y, CIANO)
        elif k == 5:
            for dx, dy in ((-12, -6), (12, -6), (0, 8)):
                caixa(tela, x + dx - 5, y + dy - 3, 10, 6, c or ACO3, luz_=None, sombra=None)
            tela.linha(x - 12, y - 6, x + 12, y - 6, c or VERDE); tela.linha(x - 12, y - 6, x, y + 8, c or VERDE)
            tela.linha(x + 12, y - 6, x, y + 8, c or VERDE)
        elif k == 6:
            for xx in range(x - 20, x + 20):
                tela.px(xx, y - 8 + int(1.5 * math.sin(xx * .5 + t * 3)), c or MISTURA2)
            dither(tela, x - 20, y - 6, 40, 12, c or MISTURA, FUNDO2)
            tela.ret(x - 20, y + 7, 40, 2, c or ACO2)
        elif k == 7:
            D.rack(tela, x - 10, y - 12, 20, 24, t, seed=9) if aceso else caixa(tela, x - 10, y - 12, 20, 24, ACO0)
        elif k == 8:
            caixa(tela, x - 8, y - 13, 16, 26, c or ACO2, luz_=ACO4 if aceso else None, sombra=None)
            tela.ret(x - 6, y - 10, 12, 20, FUNDO)
            if aceso: tiques(tela, x - 5, y - 2, 2, CIANO)

    def sons(self, fx):
        for k, ta in enumerate(T_CARTA):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12, 14)[k], .1), self.t0 + ta, .14)


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
            s = celular(tela, W // 2 - 30, 70, 60, 112)
            chat(tela, s, t, ticks=2, cor_tick=CIANO, foto_on=True)
            for k in range(3):
                u = (t * .2 + k / 3) % 1.0
                pacote(tela, -30 + u * (W + 60), 190, k + 1, t, brilho=False)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, enviar=Enviar, bits=Bits, cadeado=Cadeado, pacotes=Pacotes,
             radio=Radio, fibra=Fibra, rede=Rede, oceano=Oceano, servidor=Servidor, chegada=Chegada,
             abrir=Abrir, conta=Conta, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep07_motor as EP
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
