#!/usr/bin/env python3
"""TÚNEL — anéis que chegam na borda da tela exatamente na batida.

Cada anel nasce longe e é calculado de trás para frente: no instante do
bumbo (ou da semicolcheia, no drop) ele está do tamanho da tela e estoura
em branco. O formato do anel muda por seção (quadrado, hexágono,
triângulo, losango), o giro acompanha o baixo, e o centro do túnel passeia
em Lissajous para dar a sensação de curva.
"""
import math
import numpy as np
from ritmo_base import CenaBase, W, H, ease, hsh


class Cena(CenaBase):
    zoom = 2

    def preparar(self):
        L = self.L
        aneis = []
        for s in self.F.secoes:
            if s['papel'] == 'drop' or s['papel'] == 'fim':
                ts = [e['t'] for e in L.entre('batida', s['t0'], s['t1'] - 1e-3)]
                ts = sorted(set([round(x, 4) for x in ts] + [round(x + s['spb'] / 2, 4) for x in ts]))
            else:
                ts = [e['t'] for e in L.entre('batida', s['t0'], s['t1'] - 1e-3)]
            for tt in ts:
                aneis.append(dict(t=tt, sec=s['i'], forte=any(abs(tt - k['t']) < .01 for k in L.entre('kick', tt - .02, tt + .02))))
        self.aneis = aneis
        self.lados = self.v.get('lados', [4, 6, 3, 4, 6, 8])
        self.cores = self.v.get('cores', [9, 12, 10, 15, 6, 7])

    def mundo(self, tela, t, i):
        L = self.L
        Wt, Ht = tela.w, tela.h
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        pk = L.env('kick', t, .12)
        tela.limpar(0 if not (drop and pk > .6) else 1)
        cx = Wt / 2 + math.sin(t * .9) * 12
        cy = Ht * .46 + math.sin(t * 1.3 + 1) * 10
        giro = t * (.4 + .8 * drop) + L.env('baixo', t, .2) * .25
        janela = 4 * sec['spb']               # um anel leva 4 batidas para chegar
        # estrelas fugindo do centro
        for k in range(50):
            h = hsh(k, 13)
            a = (h % 628) / 100
            z = ((h >> 10) % 100 / 100 + t * (.35 + .5 * drop)) % 1
            r = 4 + z * z * 120
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            if drop: tela.linha(x, y, cx + math.cos(a) * r * .85, cy + math.sin(a) * r * .85, 7)
            else: tela.px(x, y, 7)
        for an in self.aneis:
            u = (an['t'] - t) / janela          # 1 longe, 0 na borda
            if u < -.12 or u > 1: continue
            z = .12 + u * 3.0
            R = 58 / z
            n = self.lados[an['sec'] % len(self.lados)]
            cor = self.cores[an['sec'] % len(self.cores)]
            if u < 0:
                cor = 11; R = 58 / .12 * (1 - u * 3)
            elif u < .05 and an['forte']:
                cor = 11
            esp = 1 if u > .4 else (2 if u > .15 else 3)
            pts = [(cx + math.cos(giro + q * math.tau / n + an['sec']) * R,
                    cy + math.sin(giro + q * math.tau / n + an['sec']) * R) for q in range(n + 1)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                for e in range(esp):
                    tela.linha(x0, y0 + e, x1, y1 + e, cor)
        # nave no meio
        bob = math.sin(t * 6) * 1.5
        nx, ny = Wt / 2, Ht * .78 + bob
        tela.ret(nx - 1, ny - 5, 3, 6, 11)
        tela.ret(nx - 5, ny, 11, 2, 12)
        tela.ret(nx - 6, ny + 2, 3, 2, 15); tela.ret(nx + 4, ny + 2, 3, 2, 15)
        fl = 2 + int(pk * 4) + (i % 2)
        tela.ret(nx, ny + 2, 1, fl, 9)

    def sobre(self, tela, t, i):
        if t < 2.6 or t >= self.F.secoes[-1]['t0']: return
        n = sum(1 for a in self.aneis if a['t'] <= t)
        txt = f"{n} PORTAIS"
        w = tela.largura_texto(txt, 11)
        tela.ret(W // 2 - w // 2 - 3, 44, w + 6, 16, 0)
        tela.texto(txt, W // 2, 46, 11, tam=11, centro=True)
