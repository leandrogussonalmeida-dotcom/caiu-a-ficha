#!/usr/bin/env python3
"""CIDADE EQUALIZADOR — os prédios são as barras do espectro.

A única cena que lê o áudio em vez dos eventos: a altura de cada prédio é a
energia de uma banda de frequência, medida no próprio som que o vídeo toca
(FFT a 30 quadros por segundo, sobe rápido e desce devagar como um VU).
O grave fica no meio da cidade, o agudo nas pontas.

E o que vem dos eventos: a lua pulsa no bumbo, as janelas trocam no drop,
fogos sobem no prato, e a água embaixo espelha tudo com ondulação.
"""
import math
import numpy as np
import ritmo_musica as M
from ritmo_base import CenaBase, W, H, ease, hsh


class Cena(CenaBase):
    zoom = 2

    def preparar(self):
        self.esp = M.espectro(self.F, 30, 24)
        n = len(self.esp)
        sm = np.zeros_like(self.esp)
        a = np.zeros(self.esp.shape[1])
        for k in range(n):
            x = self.esp[k]
            a = np.where(x > a, a + (x - a) * .75, a * .86)      # VU: sobe rápido, cai devagar
            sm[k] = a
        self.sm = sm
        self.nb = 15
        # banda de cada prédio: grave no meio, agudo nas pontas
        ordem = []
        meio = self.nb // 2
        for k in range(self.nb):
            d = abs(k - meio)
            ordem.append(min(23, int(d * 23 / meio)))
        self.ordem = ordem
        r = np.random.default_rng(self.cfg['seed'] + 7)
        self.base = [int(r.integers(6, 18)) for _ in range(self.nb)]
        self.fogos = [e['t'] for e in self.L.lista('crash')]
        self.chuva = self.v.get('chuva', False)
        self.estilo = self.v.get('estilo', 'neon')

    def mundo(self, tela, t, i):
        L = self.L
        Wt, Ht = tela.w, tela.h
        q = min(len(self.sm) - 1, int(t * 30))
        sp = self.sm[q]
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        pk = L.env('kick', t, .14)
        nb = L.conta('batida', t)
        HZ = 104                 # linha d'água
        # céu em faixas
        for k, c in enumerate((0, 13, 1, 2)):
            tela.ret(0, k * HZ // 4, Wt, HZ // 4 + 1, c)
        for k in range(40):
            h = hsh(k, 9)
            tela.px(h % Wt, (h >> 7) % 70, 11 if (h >> 3) % 4 else 7)
        # lua pulsando no bumbo
        lr = 9 + pk * 2.5
        tela.disco(Wt * .72, 26, lr, 8)
        tela.disco(Wt * .72 - 3, 24, lr * .45, 11)
        # fogos no prato
        for tf in self.fogos:
            d = t - tf
            if 0 <= d < 1.2:
                hh = hsh(int(tf * 100))
                fx, fy = 15 + hh % 60, 20 + (hh >> 8) % 30
                if d < .3:
                    tela.ret(fx, fy + (1 - d / .3) * 50, 1, 4, 11)
                else:
                    u = (d - .3) / .9
                    for a in range(12):
                        ang = a * math.tau / 12
                        rr = 4 + u * 16
                        tela.px(fx + math.cos(ang) * rr, fy + math.sin(ang) * rr + u * u * 6,
                                (9, 10, 12, 15)[(a + hh) % 4] if u < .8 else 4)
        # prédios
        bw = Wt / self.nb
        for k in range(self.nb):
            e = float(sp[self.ordem[k]])
            hgt = int(self.base[k] + e * 70)
            x0 = int(k * bw); w = int(bw) - 1
            y0 = HZ - hgt
            cor_p = 3 if k % 2 else 4
            tela.ret(x0, y0, w, hgt, cor_p)
            tela.ret(x0, y0, w, 1, 12 if e > .7 else 5)
            # janelas: acesas conforme a energia, coloridas no drop
            for wy in range(y0 + 3, HZ - 2, 4):
                for wx in range(x0 + 1, x0 + w - 1, 3):
                    hh = hsh(wx, wy, k)
                    acesa = (hh % 100) < 25 + e * 70
                    if acesa:
                        if drop and pk > .25:
                            c = (9, 10, 12, 15)[(wx // 3 + wy // 4 + nb) % 4]
                        else:
                            c = 9 if (hh >> 9) % 3 else 7
                        tela.ret(wx, wy, 2, 2, c)
            # antena piscando no chimbal
            if hgt > 50:
                tela.ret(x0 + w // 2, y0 - 5, 1, 5, 6)
                if L.env('hatf', t, .06) > .4: tela.px(x0 + w // 2, y0 - 6, 15)
        # água: reflexo espelhado com ondulação
        tela.ret(0, HZ, Wt, Ht - HZ, 13)
        for y in range(HZ, Ht):
            src = HZ - (y - HZ) * 1 - 1
            if src < 0: break
            onda = int(round(math.sin(y * .7 + t * 6) * (1 + (y - HZ) * .03)))
            linha = tela.buf[src].copy()
            linha = np.roll(linha, onda)
            # escurece: só os acesos passam, um em cada duas linhas
            if (y - HZ) % 2 == 0:
                m = (linha == 9) | (linha == 12) | (linha == 10) | (linha == 15) | (linha == 8) | (linha == 11)
                tela.buf[y][m] = linha[m]
            elif (y - HZ) < 20:
                m = (linha == 3) | (linha == 4)
                tela.buf[y][m] = 1
        tela.ret(0, HZ, Wt, 1, 6 if pk < .3 else 11)
        # chuva
        if self.chuva:
            for k in range(70):
                h = hsh(k, 21)
                x = (h % 120 + t * 40) % (Wt + 20) - 10
                y = ((h >> 8) % 200 + t * 160 * (1.4 if drop else 1)) % (Ht + 10) - 5
                tela.ret(x, y, 1, 3, 7)
            if L.env('drop', t, .15) > .3:
                tela.buf[:HZ][tela.buf[:HZ] < 3] = 7     # relâmpago no drop

    def sobre(self, tela, t, i):
        pass
