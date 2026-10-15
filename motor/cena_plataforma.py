#!/usr/bin/env python3
"""PLATAFORMA NO RITMO — o pulo sai no bumbo, o obstáculo vem depois.

O mundo é construído a partir dos pulos, não o contrário: cada pulo
começa num bumbo e termina antes do próximo, e o espinho é posto no ponto
do chão que fica embaixo do ápice desse pulo. Moedas ficam na curva do
pulo, no instante dos chimbais. O personagem corre em colcheias.

No drop o chão acende a cada bumbo e o fundo troca de cor no compasso.
"""
import math
import numpy as np
from ritmo_base import CenaBase, Sprite, W, H, ease, hsh

CORRE_A = [
    "...hhhh...",
    "..hhhhhh..",
    ".FhssssF..",
    "FFssesseFF",
    ".F.ssmss.F",
    "...cccc...",
    "..cccccs..",
    ".sccCcc...",
    "...cccc...",
    "..cc..cc..",
    ".pp....pp.",
]
CORRE_B = [
    "...hhhh...",
    "..hhhhhh..",
    ".FhssssF..",
    "FFssesseFF",
    ".F.ssmss.F",
    "...cccc...",
    "..scccc...",
    "...cCccs..",
    "...cccc...",
    "...cccc...",
    "...pppp...",
]
ESPINHO = [
    "...x...",
    "..xxx..",
    "..xXx..",
    ".xxxxx.",
    ".xXxxx.",
    "xxxxxxx",
]


class Cena(CenaBase):
    zoom = 2
    CHAO = 128
    PX_X = 26

    def preparar(self):
        L = self.L
        v = self.v
        mapa = {'h': v.get('cabelo', 13), 'F': 9, 's': 8, 'e': 0, 'm': 15, 'c': v.get('roupa', 12), 'C': 11, 'p': 0}
        self.ca, self.cb = Sprite(CORRE_A, mapa), Sprite(CORRE_B, mapa)
        self.esp = Sprite(ESPINHO, {'x': v.get('espinho', 15), 'X': 11})
        dt = 1 / 240.
        n = int(self.F.total / dt) + 10
        X = np.zeros(n)
        for k in range(1, n):
            s = L.secao(k * dt)
            X[k] = X[k - 1] + 46 * s['bpm'] / 120 * dt
        self.X, self.dtX = X, dt
        kicks = [e['t'] for e in L.lista('kick') if L.secao(e['t'])['papel'] not in ('fim',)]
        pulos = []
        for a, b in zip(kicks, kicks[1:] + [kicks[-1] + 1]):
            gap = b - a
            if gap < .22: continue
            if pulos and a < pulos[-1]['t1']: continue
            dur = min(.62, gap * .92)
            pulos.append(dict(t0=a, t1=a + dur, alt=min(30, 14 + dur * 34)))
        self.pulos = pulos
        self.p_t0 = np.array([p['t0'] for p in pulos])
        # espinho em um pulo sim, um não (e sempre nos pulos longos): espinho
        # em todo bumbo virava um tapete de cones
        self.espinhos = [self.xw((p['t0'] + p['t1']) / 2) for k, p in enumerate(pulos)
                         if k % 2 == 0 or p['t1'] - p['t0'] > .45]
        # moedas: chimbais durante um pulo, na posição da curva naquele instante
        self.moedas = []
        for e in L.lista('hatf'):
            p = self._pulo(e['t'])
            if p is not None:
                self.moedas.append((e['t'], self.xw(e['t']) , self.CHAO - 11 - self._alt(p, e['t']) - 6))
        self.estilo = v.get('fundo', 'colinas')

    def xw(self, t):
        k = min(len(self.X) - 1, max(0, int(t / self.dtX)))
        return self.X[k] + self.PX_X

    def _pulo(self, t):
        k = int(np.searchsorted(self.p_t0, t, 'right')) - 1
        if k >= 0 and self.pulos[k]['t0'] <= t < self.pulos[k]['t1']: return self.pulos[k]
        return None

    def _alt(self, p, t):
        u = (t - p['t0']) / (p['t1'] - p['t0'])
        return p['alt'] * 4 * u * (1 - u)

    def mundo(self, tela, t, i):
        L = self.L
        Wt, Ht = tela.w, tela.h
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        pk = L.env('kick', t, .12)
        nbar = L.conta('compasso', t)
        cam = self.xw(t) - self.PX_X
        CH = self.CHAO
        # fundo
        ceu = (1, 2, 13, 1)[nbar % 4] if drop else 1
        tela.limpar(ceu)
        for k in range(30):
            h = hsh(k, 5)
            x = (h % 300 - cam * .1) % 120 - 15
            tela.px(x, (h >> 8) % 60, 7)
        if self.estilo == 'colinas':
            for x in range(Wt):
                hh = 26 + 10 * math.sin((x + cam * .3) * .05) + 5 * math.sin((x + cam * .3) * .13)
                tela.ret(x, CH - hh, 1, hh, 3)
                hh2 = 14 + 6 * math.sin((x + cam * .6) * .09 + 2)
                tela.ret(x, CH - hh2, 1, hh2, 4)
        else:
            for k in range(14):
                h = hsh(k, 77)
                bw = 8 + h % 10
                x = (k * 16 - cam * .4) % (Wt + 40) - 20
                bh = 20 + (h >> 5) % 40
                tela.ret(x, CH - bh, bw, bh, 3)
                for wy in range(int(CH - bh + 3), CH - 3, 4):
                    if (hsh(k, wy, nbar) % 3 == 0): tela.ret(x + 2, wy, 2, 2, 9 if drop else 6)
        # chão em blocos que acendem no bumbo
        off = int(cam) % 10
        for k in range(-1, Wt // 10 + 2):
            x = k * 10 - off
            bloco = int((cam + x) // 10)
            tela.ret(x, CH, 10, Ht - CH, 5)
            tela.ret(x, CH, 10, 2, 9 if (drop and pk > .25 and bloco % 2 == 0) else 6)
            tela.ret(x, CH + 2, 1, Ht - CH, 0)
            tela.ret(x + 3, CH + 6 + (bloco % 3) * 5, 2, 2, 4)
        # espinhos
        for k, xs in enumerate(self.espinhos):
            sx = xs - cam - 3
            if -10 < sx < Wt + 10:
                self.esp.por(tela, sx, CH - 6)
        # moedas
        for (tm, xm, ym) in self.moedas:
            sx = xm - cam
            if t < tm and -5 < sx < Wt + 5:
                gir = abs(math.sin(t * 8 + xm))
                w = max(1, int(6 * gir))
                tela.ret(sx - w / 2, ym - 1, w, 7, 9)
                tela.ret(sx - w / 2, ym - 1, max(1, w // 3), 7, 11)
                tela.ret(sx - w / 2, ym + 6, w, 1, 10)
            elif 0 <= t - tm < .25:
                u = (t - tm) / .25
                tela.anel(sx, ym + 2, 2 + u * 3, 11, .6)
        # personagem
        p = self._pulo(t)
        alt = self._alt(p, t) if p else 0
        y = CH - 11 - alt
        frame = self.ca if (L.conta('hat', t) % 2 or p) else self.cb
        if p is None and L.desde('kick', t) > .5: frame = self.ca if (int(t * 8) % 2) else self.cb
        tela.ret(self.PX_X - 3, CH - 1, 8 - int(alt / 8), 1, 0)
        frame.por(tela, self.PX_X - 5, y)
        if p and (t - p['t0']) < .08:
            for k in range(4):
                tela.px(self.PX_X - 6 - k * 2, CH - 1 - k % 2, 11)

    def sobre(self, tela, t, i):
        L = self.L
        if t < 2.6 or t >= self.F.secoes[-1]['t0']: return
        n = sum(1 for p in self.pulos if p['t0'] <= t)
        txt = f"{n} PULOS"
        w = tela.largura_texto(txt, 11)
        tela.ret(W // 2 - w // 2 - 3, 44, w + 6, 16, 0)
        tela.texto(txt, W // 2, 46, 11, tam=11, centro=True)
