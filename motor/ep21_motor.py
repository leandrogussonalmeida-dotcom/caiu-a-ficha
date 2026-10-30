#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep21 — Como funciona a descarga do vaso (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (clique do botão, água baixinha, glug,
                          chiado da válvula de entrada), nos mesmos instantes

A descarga inteira sai de `ep21_desenho.ciclo(p)`, com p = etapa (0..5). Cada
cena só diz como p anda no tempo (câmera lenta nas etapas, 1 etapa por
compasso no capítulo da música); desenho, painel e sons leem o mesmo estado.

    python3 ep21_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep21_motor.py <saida.mp4> etapa1 etapa2       # só esses capítulos (teste)
    python3 ep21_motor.py --folha <saida.png>             # 2 quadros por capítulo
    python3 ep21_motor.py --folha <saida.png> etapa3      # 5 quadros (FR=.1,.3,.5,.7,.9)
"""
import math, os, sys
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ritmo_marca as RM
import quizaudio as QA
import ep21_desenho as D
from ep21_desenho import (ciclo, rampa, dec, ETAPAS, etiqueta_fio, rotulo, medidor, barra, gota, bolha,
                          seta_dir, manometro, garrafa, NIVEL0, BOCA_Y, PISO)
from ep21_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2121, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False

PX0 = 306
SR = LG.SR

VASO = D.Vaso(0)
VASO_P = D.Vaso(0, caixa=False)


def x_corte(cap):
    for c in CORTES:
        if c['de'][0] == cap or c['ate'][0] == cap: return c['x']
    return 46


SH_V = 16          # no corte vertical a cena sobe 16 px: a legenda do Short cai no piso


def hud_v(tela, cap, linhas, y=34):
    """No corte vertical o painel some: os números vão para o alto, à esquerda,
    no vazio em cima da bacia (coordenadas antes da subida de SH_V)."""
    if not VERTICAL: return
    x = x_corte(cap) + 4
    for k, (txt, cor) in enumerate(linhas):
        w = tela.largura_texto(txt, 9) + 8
        painel(tela, x, y + k * 15 - 3, w, 14, borda=cor)
        tela.texto(txt, x + 4, y + k * 15, cor, tam=9)


def et(tela, cap, txt, lx, ly, ponto, cor=AMARELO, centro=True):
    """Etiqueta com fio. No corte vertical só aparece se couber no recorte
    e não bater no quadro de números."""
    if VERTICAL:
        x0 = x_corte(cap)
        w = tela.largura_texto(txt, 9)
        a = lx - w // 2 - 5 if centro else lx - 5
        if a < x0 + 2 or a + w + 10 > x0 + 178 or ly < 24: return
        if a < x0 + 126 and 26 < ly + 10 and ly - 3 < 80: return
    etiqueta_fio(tela, txt, lx, ly, ponto[0], ponto[1], cor, centro)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def tit(tela, txt, y, cor=BRANCO, tam=17, x=PX0, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO, centro=centro)


def mangueira(tela):
    """Registro na parede e a mangueira que some atrás da louça."""
    pts = [(229, 152), (220, 150), (210, 144), (200, 136)]
    for a, b in zip(pts, pts[1:]):
        linha_grossa(tela, a[0], a[1], b[0], b[1], 5, PRETO)
    for a, b in zip(pts, pts[1:]):
        linha_grossa(tela, a[0], a[1], b[0], b[1], 3, ACO2)
        tela.linha(a[0], a[1] - 1, b[0], b[1] - 1, ACO3)
    tela.ret(222, 146, 7, 10, PRETO); tela.ret(223, 147, 5, 8, ACO3); tela.ret(223, 147, 5, 1, ACO4)
    tela.ret(221, 143, 3, 4, PRETO); tela.ret(222, 144, 1, 2, ACO4)


def cenario(tela, t, e, gota_on=True, marca=True, corte=True, corte_x=None):
    D.fundo_banheiro(tela, t)
    D.parede_corte(tela)
    mangueira(tela)
    VASO.desenhar(tela, e, t, corte=corte, corte_x=corte_x)
    if corte and corte_x is None:
        D.bolhas_sifao(VASO, tela, e, t)
        if gota_on:
            g = VASO.caminho_gota(e)
            if g: gota(tela, g[0], g[1], t, marca)


def painel_etapa(tela, e, t, k_at=None, titulo=True):
    """Painel de sempre: etapa, litros na caixa, usados e o estado das válvulas."""
    fundo_painel(tela)
    p = e['p']
    k = min(4, int(p)) if k_at is None else k_at
    nome, sub, cor = ETAPAS[k]
    if titulo:
        tit(tela, f"ETAPA {k + 1} DE 5", 9, ACO3, 9)
        tit(tela, nome, 20, cor, 17)
    for j in range(5):
        c = ETAPAS[j][2] if j == k else (ACO1 if j > k else FUNDO3)
        tela.ret(PX0 + j * 32, 42, 28, 5, PRETO)
        tela.ret(PX0 + j * 32 + 1, 43, 26, 3, c)
    # caixa
    medidor(tela, PX0 + 2, 60, 20, 60, e['V'] / 6.0, t, marca=1.0)
    tit(tela, 'CAIXA', 54, ACO3, 9, PX0 + 32)
    tit(tela, f"{dec(e['V'])} L", 65, MISTURA2, 17, PX0 + 32)
    tit(tela, 'USADOS', 90, ACO3, 9, PX0 + 32)
    tit(tela, f"{dec(e['usados'])} L", 101, AMARELO, 17, PX0 + 32)
    # estados
    linhas = [('COMPORTA', 'ABERTA' if e['flap'] > .05 else 'FECHADA', VERMELHO if e['flap'] > .05 else ACO2),
              ('ENTRADA', 'ABERTA' if e['entrada'] else 'FECHADA', VERDE if e['entrada'] else ACO2),
              ('SIFÃO',) + D.estado_txt(e)]
    for j, (a, b, c) in enumerate(linhas):
        y = 130 + j * 14
        tit(tela, a, y, ACO3, 9)
        tit(tela, b, y, c, 9, PX0 + 62)
    tit(tela, 'BACIA', 174, ACO3, 9)
    fr = (D.NIVEL_MIN - e['Lb']) / (D.NIVEL_MIN - D.NIVEL_MAX)
    barra(tela, PX0 + 62, 175, 96, fr, MISTURA)
    nx = PX0 + 62 + int(95 * (D.NIVEL_MIN - NIVEL0) / (D.NIVEL_MIN - D.NIVEL_MAX))
    tela.ret(nx, 172, 1, 12, AMARELO)
    tit(tela, 'NÍVEL DE REPOUSO', 188, ACO2, 9, PX0 + 62)


# ----------------------------------------------------------------- sons
def tique(f=1800, dur=.012):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))).astype(np.float32)


def bloop(f0=140, f1=280, dur=.08):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * tt / dur
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.sin(np.pi * tt / dur)).astype(np.float32)


def baque(f=85, dur=.12):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / .03)).astype(np.float32)


def agua_som(fx, t0, t1, g=.04, lo=180, hi=1400):
    """Água correndo: ruído filtrado em pedaços que se emendam (baixinho)."""
    t = t0
    while t < t1 - .2:
        d = min(2.4, t1 - t)
        fx.put(fx.chiado(d, lo, hi, .2), t, g, math.sin(t * .7) * .3)
        t += 1.8


def sons_descarga(fx, t0, dur, pfun, vol=6.0, escala=1.0, caixa=True):
    """Sons de uma cena que roda `ciclo` com p = pfun(t)."""
    passo = .05
    ts = np.arange(0, dur, passo)
    es = [ciclo(pfun(t), vol, caixa) for t in ts]
    rng = np.random.default_rng(int(t0 * 10) + 3)

    def faixas(cond):
        out, a = [], None
        for t, e in zip(ts, es):
            c = cond(e)
            if c and a is None: a = t
            if not c and a is not None: out.append((a, t)); a = None
        if a is not None: out.append((a, dur))
        return out

    for k in range(1, len(ts)):
        b0 = max(es[k - 1]['botao'], es[k - 1]['botao_meio']); b1 = max(es[k]['botao'], es[k]['botao_meio'])
        if b0 < .5 <= b1: fx.put(tique(1700), t0 + ts[k], .35 * escala)
        if b0 >= .5 > b1: fx.put(tique(1300), t0 + ts[k], .2 * escala)
        if es[k - 1]['flap'] > .3 >= es[k]['flap'] and caixa: fx.put(baque(), t0 + ts[k], .35 * escala)
    for a, b in faixas(lambda e: (e['q'] if caixa else e.get('qv', 0)) > .05 and not e['sif']):
        if b - a > .3: agua_som(fx, t0 + a, t0 + b, .035 * escala)
    for a, b in faixas(lambda e: e['sif']):
        if b - a > .3: agua_som(fx, t0 + a, t0 + b, .05 * escala, 90, 700)
    for a, b in faixas(lambda e: e['ar'] > .05):
        t = a
        while t < b:
            f0 = 110 + rng.random() * 80
            fx.put(bloop(f0, f0 * 2.2, .07 + rng.random() * .05), t0 + t, .09 * escala, rng.random() * .4 - .2)
            t += .18 + rng.random() * .25
    if caixa:
        for a, b in faixas(lambda e: e['entrada']):
            if b - a > .5: agua_som(fx, t0 + a, t0 + b, .012 * escala, 2500, 7000)


# ================================================================== cenas
class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.L = trilha.L
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def batidas(self, tipo='batida'):
        return [e['t'] - self.t0 for e in self.L.entre(tipo, self.t0 - 1e-4, self.t0 + self.dur - 1e-3)]


# ============================================================ gancho
class Gancho(Cena):
    def p(self, t): return max(0.0, (t - 1.0) * .45)

    def desenhar(self, tela, t, tg):
        e = ciclo(min(4.99, self.p(t)))
        cenario(tela, t, e)
        if t > 1.3 and not VERTICAL:
            et(tela, 'gancho', 'APERTOU!' if e['p'] < 1 else ('PARA ONDE VAI?' if e['p'] < 3.2 else 'QUEM ENCHE?'),
               100, 40, VASO.pontos()['botao'] if e['p'] < 1 else (VASO.pontos()['sifao'] if e['p'] < 3.2 else VASO.pontos()['boia']))
        hud_v(tela, 'gancho', [(f"USADOS {dec(e['usados'])} L", AMARELO)])
        if VERTICAL: return
        painel_etapa(tela, e, t)

    def sons(self, fx):
        sons_descarga(fx, self.t0, self.dur, lambda t: min(4.99, self.p(t)))


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        D.fundo_banheiro(tela, t)
        for k in range(26):
            x = (k * 53 + 7) % W
            y = (k * 37 + t * (40 + k % 5 * 8)) % 230 - 20
            gota(tela, x, y, t, marca=False, cor=MISTURA2 if k % 3 else CIANO)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA A", "DESCARGA DO VASO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 16)]
            painel(tela, W // 2 - larg // 2 - 8, 52 + j * 34 - 6, larg + 16, 32, borda=FUNDO3) if vis else None
            tela.texto(vis, W // 2 - larg // 2, 52 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", W // 2, 130, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k, (nome, _, cor) in enumerate(ETAPAS):
                x = W // 2 - 86 + k * 36
                c = cor if t > 2.0 + k * .35 else FUNDO2
                tela.ret(x - 1, 155, 30, 16, PRETO)
                tela.ret(x, 156, 28, 14, c)
                tela.texto(str(k + 1), x + 11, 160, PRETO, tam=9)

    def sons(self, fx):
        for k in range(5):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + 2.0 + k * .35, .18)


# ============================================================ o vaso (de fora -> cortado)
class Vaso(Cena):
    T_CORTE = 21.9

    def desenhar(self, tela, t, tg):
        e = ciclo(0.0)
        u = (t - self.T_CORTE) / 4.6
        if u <= 0:
            cenario(tela, t, e, corte=False)
        elif u < 1:
            cenario(tela, t, e, corte_x=40 + ease(u) * 200)
        else:
            cenario(tela, t, e, marca=False)
        P = VASO.pontos()
        if t < self.T_CORTE:
            et(tela, 'vaso', 'CAIXA ACOPLADA', 96, 20, (152, 50), AMARELO)
            et(tela, 'vaso', 'BACIA', 80, 70, (80, 128), CIANO)
            if t >= 7.3:
                et(tela, 'vaso', '6 LITROS DE ÁGUA', 96, 40, (160, 90), MISTURA2)
        if 14.6 <= t < self.T_CORTE:
            for k, txt in enumerate(('SEM MOTOR', 'SEM BOMBA')):
                x, y = 40 + k * 76, 92
                if VERTICAL: x, y = x_corte('vaso') + 10 + k * 64, 92
                tela.texto(txt, x, y, BRANCO, tam=9, contorno=PRETO)
                w = tela.largura_texto(txt, 9)
                if int(t * 2) % 2 == 0 or t > 16.5:
                    tela.linha(x - 2, y + 9, x + w + 2, y - 2, VERMELHO)
                    tela.linha(x - 2, y + 8, x + w + 2, y - 3, VERMELHO)
        if t >= self.T_CORTE + 5:
            et(tela, 'vaso', 'POR DENTRO', 100, 60, P['bacia'], AMARELO)
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'VASO COM', 9, ACO3, 9)
        tit(tela, 'CAIXA ACOPLADA', 20, AMARELO, 17)
        medidor(tela, PX0 + 2, 50, 26, 70, 1.0, t, marca=1.0)
        tit(tela, '6 L', 56, MISTURA2, 26, PX0 + 40)
        tit(tela, 'POR DESCARGA', 86, ACO3, 9, PX0 + 40)
        tit(tela, 'NORMA BRASILEIRA', 100, ACO2, 9, PX0 + 40)
        if t >= 14.6:
            tit(tela, 'FUNCIONA COM:', 138, ACO3, 9)
            for k, (txt, c) in enumerate((('ÁGUA', MISTURA2), ('GRAVIDADE', BRANCO), ('UM CANO CURVO', AMARELO))):
                if t >= 14.6 + k * .75:
                    tit(tela, '+ ' + txt, 151 + k * 13, c, 9)

    def sons(self, fx):
        fx.put(fx.chiado(4.4, 1500, 6000, .4), self.t0 + self.T_CORTE, .05, .2)
        for k, ta in enumerate((7.3, 14.6, 15.35, 16.1)):
            fx.put(fx.blip(74 + k * 2, .08), self.t0 + ta, .12)


# ============================================================ as peças
PECAS = [('caixa', 'CAIXA', '6 LITROS GUARDADOS'),
         ('botao', 'BOTÃO E ALAVANCA', 'PUXAM A CORRENTE'),
         ('comporta', 'COMPORTA', 'VEDAÇÃO DO FURO'),
         ('ladrao', 'LADRÃO', 'NÃO DEIXA TRANSBORDAR'),
         ('boia', 'BOIA E VÁLVULA', 'ENCHEM A CAIXA'),
         ('aro', 'ARO E JATO', 'LEVAM A ÁGUA'),
         ('sifao', 'SIFÃO', 'O CANO CURVO')]
PONTOS = dict(caixa=['caixa'], botao=['botao', 'alavanca'], comporta=['comporta'], ladrao=['ladrao'],
              boia=['boia', 'entrada'], aro=['aro', 'furos', 'jato'], sifao=['sifao'])


class Pecas(Cena):
    def preparar(self):
        self.slot = self.dur / len(PECAS)

    def desenhar(self, tela, t, tg):
        k_at = min(len(PECAS) - 1, int(t / self.slot))
        nome = PECAS[k_at][0]
        u = t - k_at * self.slot
        e = ciclo(0.0)
        # cada peça mexe um pouco (sem tirar água da caixa)
        if nome == 'aro':
            e = dict(e); e['refil'] = 1.0           # o fiozinho mostra o caminho pelo aro
        cenario(tela, t, e, gota_on=False)
        P = VASO.pontos()
        pisca = int(t * 4) % 2 == 0
        for nm in PONTOS[nome]:
            x, y = P[nm]
            tela.anel(x, y, 6 + 2 * math.sin(t * 6), AMARELO if pisca else CHAMA0, .6)
        if nome == 'sifao':
            for k in range(6):
                s = (t * 30 + k * 18) % VASO.L_SIF
                x, y = D._ponto(VASO.SIF_PTS, s)
                tela.disco(x, y, 1.5, AMARELO)
        if nome == 'caixa' and pisca:
            tela.ret_vazado(151, 37, 73, 79, AMARELO)
        if VERTICAL:
            rot = PECAS[k_at][1]
            lx = x_corte('pecas') + 70
            painel(tela, lx - tela.largura_texto(rot, 9) // 2 - 5, 6, tela.largura_texto(rot, 9) + 10, 14, borda=AMARELO)
            tela.texto(rot, lx, 9, AMARELO, tam=9, centro=True)
            for p in PONTOS[nome]:
                tela.linha(lx, 19, P[p][0], P[p][1], AMARELO)
            return
        fundo_painel(tela)
        for k, (nm, rot, desc) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 8 + k * 24
            atual = k == k_at
            tela.ret(PX0 - 2, y + 1, 5, 5, AMARELO if atual else ACO1)
            tit(tela, rot, y, AMARELO if atual else ACO2, 9, PX0 + 8)
            if atual:
                tit(tela, desc, y + 11, BRANCO, 9, PX0 + 8)
                if u > .4:
                    for p in PONTOS[nm]:
                        x1, y1 = P[p]
                        tela.linha(PX0 - 4, y + 4, x1, y1, PRETO)
                        tela.linha(PX0 - 4, y + 3, x1, y1, AMARELO)
                        tela.disco(x1, y1, 1.8, PRETO); tela.disco(x1, y1, 1.0, AMARELO)
        tit(tela, f"PEÇA {k_at + 1} DE {len(PECAS)}", 186, ACO3, 9)
        for k in range(len(PECAS)):
            tela.ret(PX0 + 80 + k * 11, 188, 8, 5, AMARELO if k <= k_at else FUNDO3)

    def sons(self, fx):
        for k in range(len(PECAS)):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + k * self.slot + .4, .15)
        s5 = self.t0 + 5 * self.slot
        agua_som(fx, s5, s5 + self.slot, .015, 2500, 7000)


# ============================================================ fecho hídrico
class Selo(Cena):
    T_COPO = 21.9

    def estado(self, t):
        e = ciclo(0.0)
        e = dict(e)
        u = t - self.T_COPO
        if 0 <= u < 7:
            sobe = rampa(u, [(1.0, 0), (2.4, 3.0), (3.6, 3.0), (5.5, 0)])
            e['Lb'] = NIVEL0 - sobe
            e['f'] = rampa(u, [(1.6, 0), (2.6, .25), (4.0, .2), (5.6, 0)])
        return e

    def desenhar(self, tela, t, tg):
        e = self.estado(t)
        cenario(tela, t, e, gota_on=False)
        P = VASO.pontos()
        # gás do esgoto subindo pelo lado que desce e parando na água
        if t >= 7.3:
            for k in range(7):
                u = (t * .25 + k / 7) % 1.0
                s = VASO.L_SIF - u * (VASO.L_SIF - VASO.S_CRISTA + 10)
                x, y = D._ponto(VASO.SIF_PTS, s)
                x += math.sin(t * 3 + k) * 2
                c = GAS2 if u < .7 else GAS
                tela.disco(x, y, 2.2 - u, c)
                tela.px(x - 1, y - 1, ACO3)
            if t >= 9.0:
                x, y = D._ponto(VASO.SIF_PTS, VASO.S_CRISTA - 8)
                if int(t * 3) % 2 == 0:
                    tela.linha(x - 3, y - 3, x + 3, y + 3, VERMELHO); tela.linha(x - 3, y + 3, x + 3, y - 3, VERMELHO)
                et(tela, 'selo', 'GÁS', 262, 186, (182, 186), GAS2)
                et(tela, 'selo', 'BARRADO', 262, 150, (x + 3, y), VERMELHO)
        if t < 7.3:
            et(tela, 'selo', 'ÁGUA PARADA', 90, 60, (100, 168), MISTURA2)
            et(tela, 'selo', 'SIFÃO', 262, 132, P['sifao'], AMARELO)
        # a régua dos 5 cm
        if 14.6 <= t < self.T_COPO + .5:
            x = 132
            y0, y1 = NIVEL0, BOCA_Y
            tela.ret(x, y0, 1, y1 - y0 + 1, AMARELO)
            tela.ret(x - 2, y0, 5, 1, AMARELO); tela.ret(x - 2, y1, 5, 1, AMARELO)
            tela.ret(110, y1, 22, 1, CHAMA0)
            et(tela, 'selo', 'FECHO HÍDRICO: 5 CM OU MAIS', 110, 70, (x, (y0 + y1) // 2), AMARELO)
        # o copo
        u = t - self.T_COPO
        if 0 <= u < 6:
            cx, cy = 100, 92
            inc = rampa(u, [(.3, 0), (1.0, 55), (3.2, 55), (3.9, 0)])
            a = math.radians(inc)
            pts = [(-6, -8), (6, -8), (5, 8), (-5, 8)]
            rot = [(cx + px_ * math.cos(a) + py_ * math.sin(a), cy - px_ * math.sin(a) + py_ * math.cos(a)) for px_, py_ in pts]
            poligono(tela, [(x - 1, y - 1) for x, y in rot], PRETO)
            poligono(tela, rot, ACO3)
            if 1.0 <= u < 3.4:
                bx, by = cx - 9, cy - 4
                ys = VASO._sup_bacia(bx, e, t)
                for k in range(int((ys - by) / 2)):
                    tela.ret(int(bx + math.sin(k + t * 9) * .6), int(by + k * 2), 2, 2, MISTURA2 if k % 3 else CIANO)
            et(tela, 'selo', 'CRISTA', 262, 118, P['crista'], AMARELO) if u > 2.0 else None
        hud_v(tela, 'selo', [('FECHO HÍDRICO', AMARELO), ('MÍNIMO: 5 CM', AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'O VASO PARADO', 9, ACO3, 9)
        tit(tela, 'FECHO HÍDRICO', 20, AMARELO, 17)
        tit(tela, 'ÁGUA NO FUNDO:', 46, ACO3, 9)
        tit(tela, 'UMA TAMPA', 57, MISTURA2, 17)
        tit(tela, 'GÁS DO ESGOTO:', 84, ACO3, 9)
        tit(tela, 'BARRADO' if t >= 9 else '...', 95, VERMELHO if t >= 9 else ACO2, 17)
        if t >= 14.6:
            tit(tela, 'NORMA (NBR 8160):', 122, ACO3, 9)
            tit(tela, 'MÍN. 5 CM', 133, AMARELO, 17)
        if t >= self.T_COPO:
            tit(tela, 'NÍVEL DA BACIA', 160, ACO3, 9)
            sobe = NIVEL0 - e['Lb']
            tit(tela, '+' + dec(sobe * .4) + ' CM' if sobe > .2 else 'IGUAL', 172, MISTURA2, 17)

    def sons(self, fx):
        fx.put(tique(1200), self.t0 + 9.0, .15)
        fx.put(fx.chiado(2.4, 400, 3000, .2), self.t0 + self.T_COPO + 1.0, .05, -.2)
        agua_som(fx, self.t0 + self.T_COPO + 2.4, self.t0 + self.T_COPO + 5.0, .02, 150, 900)


# ============================================================ o que é um sifão
class SifaoDemo(Cena):
    T_ENCHE, T_FLUI, T_AR, T_PARA = 8.0, 11.5, 24.0, 25.6
    YL0, YL1 = 80.0, 136.0

    def preparar(self):
        self.PTS = [(66, 140), (66, 60), (72, 48), (86, 42), (186, 42), (196, 48), (200, 60), (200, 184)]
        m, S, N, L = D._tubo(self.PTS, 2.6)
        self.M, self.S, self.Ltot = m, S, L
        self.s_topo = D._comprimento(self.PTS[:4]) + 50

    def yl(self, t):
        return rampa(t, [(self.T_FLUI, self.YL0), (self.T_AR, self.YL1)]) if t < self.T_AR else \
            self.YL1 + rampa(t, [(self.T_AR, 0), (self.T_PARA, 2)])

    def yr(self, t):
        return 190 - (self.yl(t) - self.YL0) * 60 / 94

    def desenhar(self, tela, t, tg):
        D.fundo_banheiro(tela, t)
        yy, xx = np.mgrid[0:H, 0:W]
        # suporte do balde de cima
        tela.ret(28, 149, 76, 5, PRETO); tela.ret(29, 150, 74, 3, LATAO)
        for x in (34, 94):
            tela.ret(x, 154, 5, PISO - 154, PRETO); tela.ret(x + 1, 154, 3, PISO - 154, OLEO0)
        # baldes
        for (x0, y0, x1, y1, lev) in ((36, 72, 96, 146, self.yl(t)), (168, 150, 262, 193, self.yr(t))):
            tela.ret(x0 - 4, y0, x1 - x0 + 8, y1 - y0 + 4, PRETO)
            tela.ret(x0 - 3, y0, x1 - x0 + 6, y1 - y0 + 3, ACO3)
            tela.ret(x0 - 3, y0, 1, y1 - y0 + 3, ACO4)
            dither(tela, x0, y0, x1 - x0, y1 - y0, FUNDO3, FUNDO2)
            sup = lev + np.sin(xx[0, x0:x1] * .3 - t * 2.4) * .6
            for i, x in enumerate(range(x0, x1)):
                a = int(round(sup[i]))
                if a < y1:
                    tela.ret(x, a, 1, y1 - a, MISTURA if (x + a) % 2 else MISTURA)
                    tela.px(x, a, MISTURA2)
            dither(tela, x0, int(lev) + 16, x1 - x0, max(0, y1 - int(lev) - 16), MISTURA, FUNDO3) if lev + 16 < y1 else None
        # a mangueira
        tela.buf[D._dilata(self.M, 1)] = PRETO
        tela.buf[self.M] = ACO1
        fluindo = self.T_FLUI <= t < self.T_AR
        if t < self.T_ENCHE:
            agua = np.zeros_like(self.M)
        elif t < self.T_FLUI:
            fr = (t - self.T_ENCHE) / (self.T_FLUI - self.T_ENCHE)
            agua = self.M & (self.S < fr * self.Ltot)
        elif t < self.T_AR:
            agua = self.M.copy()
        else:
            u = (t - self.T_AR) / 1.6
            desce = self.s_topo + (self.Ltot - self.s_topo) * min(1, u)
            agua = self.M & (((self.S > desce) & (u < 1)) | (yy >= self.yl(t)) & (self.S < 100))
        cor = np.where(((self.S - t * 50) % 12 < 3) & fluindo, MISTURA2, MISTURA)
        tela.buf[agua] = cor[agua]
        tela.buf[self.M & ~agua & ((xx + yy) % 2 == 0)] = ACO2
        if fluindo:
            for k in range(5):
                u = (t * 2.5 + k / 5) % 1.0
                y = 184 + u * (self.yr(t) - 184)
                if y > 184: tela.ret(199 + (k % 3), int(y), 1, 2, MISTURA2)
            seta_dir(tela, 214, 150, 0, 1, 40, AMARELO)
            rotulo(tela, 'PUXA', 220, 120, AMARELO)
            seta_dir(tela, 52, 70, 0, -1, 18, VERDE)
            rotulo(tela, 'SOBE', 34, 52, VERDE)
        if self.T_AR - .2 <= t < self.T_PARA + 1:
            u = (t - self.T_AR + .2) / 1.8
            x, y = D._ponto(self.PTS, max(0, u) * self.s_topo)
            bolha(tela, x, y, 2.2)
        # rótulos
        if t < self.T_ENCHE:
            rotulo(tela, 'TUBO COM AR', 104, 26, ACO3)
            if int(t * 2) % 2 == 0: rotulo(tela, 'NADA ACONTECE', 104, 52, VERMELHO)
        elif t < self.T_FLUI:
            rotulo(tela, 'ENCHENDO O TUBO', 104, 26, MISTURA2)
        elif t < self.T_AR:
            rotulo(tela, 'A ÁGUA SOBE A CURVA', 90, 26, AMARELO)
        else:
            rotulo(tela, 'ENTROU AR: PAROU', 98, 26, CIANO)
        if t >= 21.9:
            tela.ret(110, int(self.yl(t)), 150, 1, CHAMA0) if not VERTICAL else None
            rotulo(tela, 'SAÍDA MAIS BAIXA', 210, 196 - 10 if False else 70, BRANCO)
            tela.linha(230, 80, 202, 182, ACO3)
        estado = ('VAZIO', ACO2) if t < self.T_ENCHE else (('ENCHENDO', MISTURA2) if t < self.T_FLUI else
                                                           (('PUXANDO!', AMARELO) if t < self.T_AR else ('QUEBRADO', CIANO)))
        hud_v(tela, 'sifao', [(f"SIFÃO: {estado[0]}", estado[1])])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'O SIFÃO', 9, AMARELO, 17)
        tit(tela, 'ESTADO', 34, ACO3, 9)
        tit(tela, estado[0], 45, estado[1], 17)
        tit(tela, 'BALDE DE CIMA', 74, ACO3, 9)
        medidor(tela, PX0 + 2, 86, 18, 50, (146 - self.yl(t)) / 74, t)
        tit(tela, 'BALDE DE BAIXO', 74, ACO3, 9, PX0 + 84)
        medidor(tela, PX0 + 86, 86, 18, 50, (193 - self.yr(t)) / 43, t)
        tit(tela, 'LADO QUE DESCE', 150, ACO3, 9)
        tit(tela, 'É O MAIS COMPRIDO', 162, BRANCO, 9)
        tit(tela, 'SEM BOMBA', 182, VERDE, 17)

    def sons(self, fx):
        agua_som(fx, self.t0 + self.T_ENCHE, self.t0 + self.T_AR, .03, 200, 1200)
        for k in range(5):
            fx.put(bloop(130 + k * 20, 300, .08), self.t0 + self.T_AR + k * .25, .08)


# ============================================================ as 5 etapas (câmera lenta)
ROT_ETAPA = {
    0: [('BOTÃO', 120, 22, 'botao', BRANCO), ('ALAVANCA', 262, 30, 'alavanca', ACO4), ('CORRENTE', 262, 66, (180, 75), ACO3),
        ('COMPORTA', 262, 100, 'comporta', VERMELHO)],
    1: [('FUROS DO ARO', 90, 70, 'furos', MISTURA2), ('JATO', 22, 160, 'jato', CIANO),
        ('CRISTA', 262, 140, 'crista', AMARELO)],
    2: [('SIFÃO CHEIO', 262, 140, 'sifao', AMARELO), ('COMPORTA', 262, 100, 'comporta', VERMELHO)],
    3: [('AR ENTRANDO', 262, 140, (128, 180), CIANO)],
    4: [('BOIA', 100, 40, 'boia', VERDE), ('VÁLVULA DE ENTRADA', 100, 84, 'entrada', VERDE),
        ('TUBINHO', 262, 30, 'refil', CIANO), ('LADRÃO', 262, 74, 'ladrao', ACO4)],
}


class Etapa(Cena):
    K = 0

    def p(self, t): return self.K + t / self.dur

    def desenhar(self, tela, t, tg):
        e = ciclo(self.p(t))
        cenario(tela, t, e)
        P = VASO.pontos()
        for (txt, lx, ly, pt, cor) in ROT_ETAPA[self.K]:
            ponto = P[pt] if isinstance(pt, str) else pt
            et(tela, self.c['id'], txt, lx, ly, ponto, cor)
        if self.K == 2 and e['sif']:
            x, y = D._ponto(VASO.SIF_PTS, VASO.L_SIF - 30)
            seta_dir(tela, x + 12, y + 14, 0, 1, 16, AMARELO)
        if self.K == 2 and not e['sif'] and e['f'] < 1:
            rotulo(tela, f"CANO {int(e['f'] * 100)}% CHEIO", 90, 40, MISTURA2)
        if self.K < 4 and not VERTICAL:
            if int(t * 1.5) % 3: rotulo(tela, 'CÂMERA LENTA', 8, 8, ACO3)
        nome = ETAPAS[self.K][0]
        hud_v(tela, self.c['id'], [(f"ETAPA {self.K + 1} DE 5", ETAPAS[self.K][2]), (nome, ETAPAS[self.K][2]),
                                    (f"CAIXA {dec(e['V'])} L", MISTURA2)])
        if VERTICAL: return
        painel_etapa(tela, e, t, self.K)

    def sons(self, fx):
        sons_descarga(fx, self.t0, self.dur, self.p)


class Etapa1(Etapa): K = 0
class Etapa2(Etapa): K = 1
class Etapa3(Etapa): K = 2
class Etapa4(Etapa): K = 3
class Etapa5(Etapa): K = 4


# ============================================================ no ritmo da música
class Ciclo(Cena):
    def preparar(self):
        self.cps = self.batidas('compasso')
        self.bar = self.cps[1] - self.cps[0] if len(self.cps) > 1 else 2.4

    def p(self, t):
        return (t / self.bar - .12) % 5.0

    def desenhar(self, tela, t, tg):
        e = ciclo(self.p(t))
        cenario(tela, t, e)
        k = min(4, int(e['p']))
        pulso = self.L.env('compasso', tg, .25)
        nome, sub, cor = ETAPAS[k]
        if not VERTICAL:
            w = tela.largura_texto(nome, 17)
            painel(tela, 150 - w // 2 - 8, 6, w + 16, 22, borda=cor)
            tela.texto(nome, 150, 10, cor if pulso < .6 else BRANCO, tam=17, centro=True)
        n = int((t + .01) / (5 * self.bar))
        hud_v(tela, 'ciclo', [(f"ETAPA {k + 1} DE 5", cor), (nome, cor)])
        if VERTICAL: return
        painel_etapa(tela, e, t, k)
        tit(tela, f"DESCARGA {min(3, n + 1)} DE 3", 196 - 1, ACO3, 9, PX0 + 62) if False else None

    def sons(self, fx):
        sons_descarga(fx, self.t0, self.dur, self.p, escala=.8)


# ============================================================ dois botões
class Duplo(Cena):
    A0, B0, PASSO = 1.0, 18.3, 3.2

    def estado(self, t):
        if t < self.B0 - .3:
            return ciclo(min(4.99, max(0, (t - self.A0) / self.PASSO)), 3.0), 3.0
        return ciclo(min(4.99, max(0, (t - self.B0) / self.PASSO)), 6.0), 6.0

    def desenhar(self, tela, t, tg):
        e, vol = self.estado(t)
        cenario(tela, t, e)
        P = VASO.pontos()
        if t < 15.1:
            et(tela, 'duplo', 'MENOR: 3 L', 120, 14, P['botao_meio'], CIANO)
            et(tela, 'duplo', 'MAIOR: 6 L', 262, 14, P['botao'], AMARELO)
        meia = D.FUNDO_CX - 3 * D.PX_L
        if t < self.B0 - .3 and t > 4:
            tela.ret(155, int(meia), 4, 1, CIANO); tela.ret(196, int(meia), 4, 1, CIANO)
            et(tela, 'duplo', 'FECHA NA METADE', 90, 64, (156, int(meia)), CIANO)
        hud_v(tela, 'duplo', [('BOTÃO MENOR' if vol < 5 else 'BOTÃO MAIOR', CIANO if vol < 5 else AMARELO),
                              (f"USADOS {dec(e['usados'])} L", CIANO if vol < 5 else AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'DOIS BOTÕES', 9, AMARELO, 17)
        medidor(tela, PX0 + 2, 36, 20, 60, e['V'] / 6.0, t, marca=.5)
        tit(tela, 'CAIXA', 36, ACO3, 9, PX0 + 32)
        tit(tela, f"{dec(e['V'])} L", 47, MISTURA2, 17, PX0 + 32)
        tit(tela, 'COMPORTA', 72, ACO3, 9, PX0 + 32)
        tit(tela, 'ABERTA' if e['flap'] > .05 else 'FECHADA', 83, VERMELHO if e['flap'] > .05 else ACO2, 9, PX0 + 32)
        u_meia = 3.0 if t >= self.B0 - .3 else e['usados']
        u_comp = e['usados'] if t >= self.B0 - .3 else 0.0
        tit(tela, 'MEIA (BOTÃO MENOR)', 112, CIANO, 9)
        barra(tela, PX0, 124, 120, u_meia / 6.0, CIANO)
        tit(tela, f"{dec(u_meia)} L", 121, CIANO, 9, PX0 + 126)
        tit(tela, 'COMPLETA (MAIOR)', 142, AMARELO, 9)
        barra(tela, PX0, 154, 120, u_comp / 6.0, AMARELO)
        tit(tela, f"{dec(u_comp)} L", 151, AMARELO, 9, PX0 + 126)
        if t >= 29.7:
            tit(tela, 'MEIA: ATÉ 2/3', 172, BRANCO, 9)
            tit(tela, 'DA COMPLETA (USP)', 184, ACO3, 9)

    def sons(self, fx):
        sons_descarga(fx, self.t0 + self.A0, self.B0 - .3 - self.A0, lambda t: min(4.99, t / self.PASSO), 3.0)
        sons_descarga(fx, self.t0 + self.B0, self.dur - self.B0, lambda t: min(4.99, t / self.PASSO), 6.0)


# ============================================================ quantos litros
class Litros(Cena):
    LINHAS = [('VASO ANTIGO (SABESP)', 12, 7.8, LARANJA), ('HOJE: DESCARGA COMPLETA', 6, 15.1, AMARELO),
              ('MEIA DESCARGA', 3, 18.9, CIANO)]

    def preparar(self):
        self.bt = self.batidas()

    def cheio(self, t, t_ini, k):
        """Fração da garrafa k da linha que começa em t_ini (1 garrafa por batida)."""
        ts = [b for b in self.bt if b >= t_ini - 1e-6]
        if k >= len(ts): return 0.0
        a = ts[k]
        return max(0.0, min(1.0, (t - a) / .7))

    def desenhar(self, tela, t, tg):
        D.fundo_banheiro(tela, t)
        x0 = x_corte('litros') + 6 if VERTICAL else 18
        # a garrafa de exemplo
        if t < 7.8:
            u = min(1.0, t / 6.0)
            bx = x_corte('litros') + 60 if VERTICAL else 110
            garrafa(tela, bx, 100, u, t, esc=3)
            rotulo(tela, '= 1 LITRO', bx + 40, 140, AMARELO)
            for j in range(5):
                yy = 50 + ((t * 70 + j * 9) % 46)
                if u < 1: tela.ret(bx + 14, int(yy), 2, 3, MISTURA2)
            tela.ret(bx + 11, 0, 10, 44, PRETO); tela.ret(bx + 12, 0, 8, 43, ACO2); tela.ret(bx + 12, 0, 1, 43, ACO4)
            tela.ret(bx + 6, 40, 20, 8, PRETO); tela.ret(bx + 7, 41, 18, 6, ACO3); tela.ret(bx + 7, 41, 18, 1, ACO4)
        for j, (rot, n, ti, cor) in enumerate(self.LINHAS):
            if t < ti - .3: continue
            y = 10 + j * 64
            tot = sum(self.cheio(t, ti, k) for k in range(n))
            tela.texto(rot, x0, y, cor, tam=9, contorno=PRETO)
            tela.texto(f"{dec(tot)} L", x0 + tela.largura_texto(rot, 9) + 8, y - 4, cor, tam=17, contorno=PRETO)
            for k in range(n):
                f = self.cheio(t, ti, k)
                if VERTICAL:
                    xx, yb = x0 + (k % 6) * 28, y + 14 + (k // 6) * 22
                    garrafa(tela, xx, yb, f, t)
                else:
                    garrafa(tela, x0 + k * 23, y + 14, f, t, esc=2)
        hud_v(tela, 'litros', [('LITROS POR DESCARGA', AMARELO)], y=190)
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'LITROS POR', 9, ACO3, 9)
        tit(tela, 'DESCARGA', 20, AMARELO, 17)
        for j, (rot, n, ti, cor) in enumerate(self.LINHAS):
            if t < ti - .3: continue
            y = 48 + j * 22
            barra(tela, PX0, y + 6, 120, n / 12.0 * min(1.0, (t - ti + .3) / 2), cor)
            tit(tela, f"{n} L", y + 4, cor, 9, PX0 + 126)
        if t >= 22.4:
            tit(tela, 'NA CONTA DE ÁGUA', 124, ACO3, 9)
            tit(tela, 'DA CASA:', 135, ACO3, 9)
            u = min(1.0, (t - 22.4) / 2.0)
            cx, cy, r = PX0 + 120, 156, 22
            tela.disco(cx, cy, r + 1, PRETO)
            tela.disco(cx, cy, r, FUNDO3)
            yy, xx = np.mgrid[0:H, 0:W]
            ang = (np.degrees(np.arctan2(xx - cx, -(yy - cy))) + 360) % 360
            m = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r) & (ang <= 360 * .29 * u)
            tela.buf[m] = MISTURA
            tit(tela, f"{int(round(29 * u))}%", 150, AMARELO, 26)

    def sons(self, fx):
        for j, (rot, n, ti, cor) in enumerate(self.LINHAS):
            ts = [b for b in self.bt if b >= ti - 1e-6][:n]
            for k, b in enumerate(ts):
                fx.put(bloop(400 + k * 30, 900 + k * 40, .06), self.t0 + b, .06)
        agua_som(fx, self.t0 + .2, self.t0 + 6.0, .02, 500, 3000)


# ============================================================ válvula de parede
class Parede(Cena):
    PASSO = 3.4
    CICLOS = [(2.0,), (22.6,)]

    def p(self, t):
        for (a,) in reversed(self.CICLOS):
            if t >= a: return min(4.99, (t - a) / self.PASSO)
        return 0.0

    def estado(self, t):
        e = dict(ciclo(self.p(t), caixa=False))
        p = e['p']
        # a válvula fica aberta enquanto a "comporta" do ciclo estaria aberta; no fim, um fio repõe a bacia
        e['qv'] = max(e['flap'], .3 if 4.0 <= p < 4.8 else 0.0)
        e['V'] = 0.0
        return e

    def desenhar(self, tela, t, tg):
        e = self.estado(t)
        D.fundo_banheiro(tela, t)
        D.parede_corte(tela)
        VASO_P.desenhar(tela, e, t)
        D.bolhas_sifao(VASO_P, tela, e, t)
        g = VASO_P.caminho_gota(e)
        aberta = e['qv'] > .05
        # cano dentro da parede, vindo de cima (da caixa d'água)
        tela.ret(229, 0, 6, 70, PRETO); tela.ret(230, 0, 4, 70, MISTURA if True else ACO1)
        for k in range(6):
            y = (t * (70 if aberta else 6) + k * 12) % 70
            tela.ret(231, int(y), 2, 3, MISTURA2)
        # corpo da válvula
        tela.ret(220, 66, 14, 22, PRETO); tela.ret(221, 67, 12, 20, ACO3); tela.ret(221, 67, 12, 1, ACO4)
        tela.ret(221, 86, 12, 1, ACO1)
        b = 2 if (aberta and e['p'] < .4) else 0
        tela.ret(214 + b, 72, 7, 8, PRETO); tela.ret(215 + b, 73, 5, 6, ACO4); tela.ret(215 + b, 73, 1, 6, BRANCO)
        # parafuso de regulagem
        ang = t * 3 if 29.7 <= t < 36 else 0.0
        tela.disco(227, 82, 2.4, PRETO); tela.disco(227, 82, 1.8, LATAO)
        tela.linha(227 - 2 * math.cos(ang), 82 - 2 * math.sin(ang), 227 + 2 * math.cos(ang), 82 + 2 * math.sin(ang), PRETO)
        # cano da válvula até a entrada do vaso
        pts = [(226, 88), (226, 100), (201, 100), (201, 114)]
        for a_, b_ in zip(pts, pts[1:]):
            linha_grossa(tela, a_[0], a_[1], b_[0], b_[1], 8, PRETO)
        for a_, b_ in zip(pts, pts[1:]):
            linha_grossa(tela, a_[0], a_[1], b_[0], b_[1], 5, MISTURA if aberta else ACO1)
        if aberta:
            for k in range(6):
                s = (t * 60 + k * 9) % 49
                x, y = D._ponto(pts, s)
                tela.ret(int(x), int(y), 2, 2, MISTURA2)
        # manômetro no cano
        pres = .35 if not aberta else .28 + .02 * math.sin(t * 9)
        tela.ret(235, 38, 8, 4, PRETO); tela.ret(235, 39, 8, 2, ACO3)
        manometro(tela, 250, 40, 7, pres)
        if g and 1.0 <= e['p'] < 2.9: gota(tela, g[0], g[1], t)
        P = VASO_P.pontos()
        if VERTICAL and t < 22.4:
            et(tela, 'parede', 'VÁLVULA', 150, 92, (216, 75), AMARELO)
        if t < 15.1:
            et(tela, 'parede', 'VÁLVULA DE PAREDE', 120, 40, (216, 75), AMARELO)
            et(tela, 'parede', 'VEM DA CAIXA D\'ÁGUA', 120, 12, (230, 20), MISTURA2)
        elif t < 29.7:
            et(tela, 'parede', 'PRESSÃO', 120, 30, (243, 40), AMARELO)
            et(tela, 'parede', 'SEM CAIXA', 120, 80, (190, 112), ACO4)
        else:
            et(tela, 'parede', 'PARAFUSO', 120, 50, (227, 82), LATAO)
        hud_v(tela, 'parede', [(f"USADOS {dec(e['usados'])} L", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'VÁLVULA', 9, ACO3, 9)
        tit(tela, 'DE PAREDE', 20, AMARELO, 17)
        tit(tela, 'VÁLVULA', 44, ACO3, 9)
        tit(tela, 'ABERTA' if aberta else 'FECHADA', 44, VERDE if aberta else ACO2, 9, PX0 + 60)
        tit(tela, 'SIFÃO', 57, ACO3, 9)
        s, c = D.estado_txt(e)
        tit(tela, s, 57, c, 9, PX0 + 60)
        tit(tela, 'CANO: DN 32 OU 40', 74, BRANCO, 9)
        if t >= 22.4:
            tit(tela, 'PRESSÃO MÍNIMA', 94, ACO3, 9)
            tit(tela, '20 KPA', 105, AMARELO, 17)
            tit(tela, '= UNS 2 M DE ALTURA', 124, MISTURA2, 9)
            # caixa d'água a 2 m
            x, y = PX0 + 136, 92
            tela.ret(x - 9, y, 18, 10, PRETO); tela.ret(x - 8, y + 1, 16, 8, ACO2)
            dither(tela, x - 7, y + 4, 14, 4, MISTURA, MISTURA2)
            tela.ret(x, y + 10, 1, 26, MISTURA)
            seta_dir(tela, x + 12, y + 36, 0, 1, 34, AMARELO, 1, 3)
        if t >= 29.7:
            tit(tela, 'REGULADA (ANTIGA)', 144, ACO3, 9)
            barra(tela, PX0, 155, 110, 10 / 12, LARANJA); tit(tela, '10 L', 153, LARANJA, 9, PX0 + 116)
        if t >= 36.3:
            tit(tela, 'DESCARGA REDUZIDA', 170, ACO3, 9)
            barra(tela, PX0, 181, 110, 6 / 12, AMARELO); tit(tela, '6 L', 179, AMARELO, 9, PX0 + 116)

    def sons(self, fx):
        sons_descarga(fx, self.t0, self.dur, self.p, caixa=False)


# ============================================================ resumo
class Resumo(Cena):
    PASSO = 6.4

    def p(self, t): return min(4.99, t / self.PASSO)

    def desenhar(self, tela, t, tg):
        e = ciclo(self.p(t))
        cenario(tela, t, e)
        k = min(4, int(e['p']))
        hud_v(tela, 'resumo', [(f"{k + 1}. {ETAPAS[k][0]}", ETAPAS[k][2])])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'AS 5 ETAPAS', 9, AMARELO, 17)
        for j, (nome, sub, cor) in enumerate(ETAPAS):
            y = 36 + j * 32
            on = j == k
            feito = j < k
            painel(tela, PX0 - 2, y - 3, 160, 28, borda=cor if on else (ACO1 if feito else FUNDO3))
            tit(tela, f"{j + 1}. {nome}", y + 1, cor if on else (ACO2 if feito else ACO1), 9, PX0 + 4)
            tit(tela, sub, y + 12, BRANCO if on else ACO1, 9, PX0 + 4)

    def sons(self, fx):
        sons_descarga(fx, self.t0, self.dur, self.p, escala=.8)
        for k in range(5):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + k * self.PASSO + .3, .12)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS POR DENTRO'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            D.fundo_banheiro(tela, t)
            u = t - RM.OUTRO_S
            e = ciclo(0.0)
            VASO.desenhar(tela, e, t, corte=True)
            for k in range(10):
                x = (k * 47 + 20) % 280 + 10
                y = (k * 31 + u * 50) % 200
                gota(tela, x, y, t, marca=False, cor=MISTURA2)
            tela.texto("OBRIGADO POR ASSISTIR!", 360, 70, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", 360, 96, AMARELO, tam=9, centro=True, contorno=PRETO)

    def fim_vinheta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# longo.py chama `pos` (RGB pronto) quando a cena tem esse método: só o Fim usa.
Fim.pos = Fim.fim_vinheta

CENAS = dict(gancho=Gancho, titulo=Titulo, vaso=Vaso, pecas=Pecas, selo=Selo, sifao=SifaoDemo,
             etapa1=Etapa1, etapa2=Etapa2, etapa3=Etapa3, etapa4=Etapa4, etapa5=Etapa5,
             ciclo=Ciclo, duplo=Duplo, litros=Litros, parede=Parede, resumo=Resumo, fim=Fim)


def _sobe(desenhar):
    def f(self, tela, t, tg):
        desenhar(self, tela, t, tg)
        if VERTICAL:
            tela.buf[0:PALCO_H - SH_V] = tela.buf[SH_V:PALCO_H].copy()
            tela.buf[PALCO_H - SH_V:PALCO_H] = tela.buf[PALCO_H - SH_V - 1]
    return f


for _cls in CENAS.values():
    _cls.desenhar = _sobe(_cls.desenhar)


if __name__ == '__main__':
    import ep21_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if len(sys.argv) > 3:
            c = next(c for c in trilha.caps if c['id'] == sys.argv[3])
            fr = [float(x) for x in sys.argv[4:]] or [float(x) for x in os.environ.get('FR', '.1,.3,.5,.7,.9').split(',')]
            ts = [c['t0'] + c['dur'] * f for f in fr]
        else:
            fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
            for c in trilha.caps:
                ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
