#!/usr/bin/env python3
"""PISTAS — as notas descem e batem na linha no instante exato do som.

Quatro pistas, uma por instrumento: BUMBO, CAIXA, CHIMBAL e MELODIA (ou
BAIXO). Cada nota que desce é um evento da faixa; a posição dela é o tempo
que falta para ele tocar, então a nota encosta na linha no mesmo quadro em
que o som sai. A pessoa vê o padrão de cada gênero: o bumbo reto do house,
a caixa no 3 do dubstep, o chimbal picado do trap.
"""
import math
import numpy as np
from ritmo_base import CenaBase, W, H, ease, hsh

Y_LINHA = 222
Y_FUGA = 40


class Cena(CenaBase):
    zoom = 1

    def preparar(self):
        L = self.L
        v = self.v
        quarta = v.get('quarta', 'lead')
        self.pistas = [('BUMBO', 'kick', 15), ('CAIXA', 'costas', 9), ('CHIMBAL', 'hatf', 12),
                       ('BAIXO' if quarta == 'baixo' else 'MELODIA', quarta, 10)]
        self.ev = []
        for k, (_, tp, _) in enumerate(self.pistas):
            ts = []
            for e in L.lista(tp):
                if ts and e['t'] - ts[-1] < .07: continue
                ts.append(e['t'])
            self.ev.append(np.array(ts))
        self.pts = 0

    def faixa_x(self, k, y):
        """x do centro da pista k na altura y (perspectiva para o fundo)."""
        p = (y - Y_FUGA) / (Y_LINHA - Y_FUGA)
        largura = 36 + 110 * p
        return W / 2 + (k - 1.5) * largura / 4 * 1.0 * (largura / 146) * 4 / 4, largura / 4

    def mundo(self, tela, t, i):
        L = self.L
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        pk = L.env('kick', t, .14)
        tela.limpar(0)
        # luzes de palco que varrem no compasso
        nbar = L.conta('compasso', t)
        if drop:
            for k in range(3):
                ang = math.sin(t * 2.2 + k * 2.1) * .6
                x0 = 30 + k * 60
                for s in range(0, 220, 2):
                    x = x0 + math.sin(ang) * s
                    w = 1 + s * .08
                    if (s // 2) % 2 == 0: tela.ret(x - w / 2, s, w, 2, (13, 1, 2)[k])
        # pista: laterais em perspectiva
        look = 2.2 * sec['spb']           # duas batidas de antecedência
        for y in range(Y_FUGA, H):
            p = (y - Y_FUGA) / (Y_LINHA - Y_FUGA)
            larg = 36 + 110 * p
            x0 = W / 2 - larg / 2
            tela.ret(x0, y, larg, 1, 13)
            for k in range(5):
                tela.px(x0 + larg * k / 4, y, 3)
            # linhas de compasso descendo
        for nbk in range(0, 3):
            e = L.proximo('batida', t)
            if e is None: break
            tb = e['t'] + nbk * sec['spb']
            u = (tb - t) / look
            if 0 <= u <= 1:
                y = Y_LINHA - (Y_LINHA - Y_FUGA) * (u / (1 + u * 0.0)) ** .8
                p = (y - Y_FUGA) / (Y_LINHA - Y_FUGA)
                larg = 36 + 110 * p
                tela.ret(W / 2 - larg / 2, y, larg, 1, 4)
        # notas
        for k, (nome, tp, cor) in enumerate(self.pistas):
            ts = self.ev[k]
            a = np.searchsorted(ts, t - .05); b = np.searchsorted(ts, t + look)
            for te in ts[a:b]:
                u = (te - t) / look
                if u < 0: continue
                y = Y_LINHA - (Y_LINHA - Y_FUGA) * u ** .8
                p = (y - Y_FUGA) / (Y_LINHA - Y_FUGA)
                larg = 36 + 110 * p
                x = W / 2 - larg / 2 + larg * (k + .5) / 4
                gw = max(3, larg / 4 * .8); gh = max(2, 6 * p)
                tela.ret(x - gw / 2, y - gh / 2, gw, gh, cor)
                tela.ret(x - gw / 2, y - gh / 2, gw, 1, 11)
        # linha de acerto e receptores
        larg = 146
        x0 = W / 2 - larg / 2
        tela.ret(x0, Y_LINHA - 1, larg, 2, 11 if pk > .4 else 6)
        for k, (nome, tp, cor) in enumerate(self.pistas):
            x = x0 + larg * (k + .5) / 4
            d = L.desde(tp, t)
            acende = math.exp(-d / .1) if d < 2 else 0
            tela.ret(x - 15, Y_LINHA - 6, 30, 12, cor if acende > .3 else 3)
            tela.ret(x - 13, Y_LINHA - 4, 26, 8, 0)
            if acende > .3:
                tela.ret(x - 11, Y_LINHA - 2, 22, 4, cor)
                for q in range(6):
                    ang = -math.pi / 2 + (q - 2.5) * .45
                    rr = 8 + (1 - acende) * 22
                    tela.px(x + math.cos(ang) * rr, Y_LINHA + math.sin(ang) * rr, 11)
            tela.texto(nome, x, Y_LINHA + 9, cor, tam=7 if len(nome) > 5 else 8, centro=True)

    def sobre(self, tela, t, i):
        L = self.L
        if t < 2.6 or t >= self.F.secoes[-1]['t0']: return
        n = sum(int(np.searchsorted(ts, t, 'right')) for ts in self.ev)
        txt = f"{n} NOTAS"
        w = tela.largura_texto(txt, 11)
        tela.ret(W // 2 - w // 2 - 3, 44, w + 6, 16, 0)
        tela.texto(txt, W // 2, 46, 11, tam=11, centro=True)
        d = L.desde('drop', t)
        if t > 3 and d < .9:
            e = min(1, d / .15)
            tam = int(12 + 6 * e)
            tela.texto('PERFEITO!', W // 2, 120, 9, tam=tam, centro=True, sombra=0)
