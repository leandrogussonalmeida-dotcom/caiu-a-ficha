#!/usr/bin/env python3
"""FOGUETE NO RITMO — cada barreira é atravessada exatamente no bumbo.

As barreiras descem a tela e o foguete passa pela fenda delas; a posição de
cada uma é calculada de trás para frente a partir do instante do bumbo, pela
distância percorrida (integral da velocidade, que muda por seção). Por isso
o estouro nunca escorrega, nem quando o BPM dobra.

Reage:
  bumbo    a barreira explode em cacos e onda de choque
  chimbal  os blocos da próxima barreira piscam
  baixo    a chama cresce
  drop     estrelas viram riscos de hiperespaço, a velocidade sobe
  build    faixas de alerta e o foguete treme carregando
"""
import math
import numpy as np
from ritmo_base import CenaBase, Sprite, ease, hsh, nova_paleta

FOG = [
    "....nn....",
    "...nwwn...",
    "..nwwwwn..",
    "..wwjjww..",
    "..wjccjw..",
    "..wjccjw..",
    "..wwjjww..",
    "..wwwwww..",
    "..wwwwww..",
    ".rwwwwwwr.",
    "rrwwwwwwrr",
    "rr.wwww.rr",
    "r..g..g..r",
]


class Cena(CenaBase):
    zoom = 2

    def preparar(self):
        v = self.v
        L = self.L
        self.wt, self.ht = 90, 160
        self.ry = 116
        self.fog = Sprite(FOG, {'n': v.get('nariz', 15), 'w': 11, 'j': v.get('janela', 12),
                                'c': 0, 'r': v.get('aleta', 15), 'g': 14})
        # velocidade por seção e distância acumulada amostrada a 240 Hz
        dt = 1 / 240.
        n = int(self.F.total / dt) + 10
        D = np.zeros(n)
        for k in range(1, n):
            s = L.secao(k * dt)
            vel = 70 * s['bpm'] / 120 * (1.5 if s['papel'] in ('drop', 'fim') else 1.0)
            D[k] = D[k - 1] + vel * dt
        self.D, self.dtD = D, dt
        # barreiras: nos bumbos das seções cheias; uma a cada 2 batidas nas outras
        rng = self.rng
        bar = []
        ult = -1
        for s in self.F.secoes:
            if s['papel'] == 'fim': continue
            if s['papel'] in ('drop',):
                tempos = [e['t'] for e in L.entre('kick', s['t0'], s['t1'] - 1e-3)]
            elif s['papel'] == 'build':
                tempos = []
            else:
                tempos = [e['t'] for e in L.entre('batida', s['t0'], s['t1'] - 1e-3) if e['k'] in (0, 2)]
            for tt in tempos:
                if tt - ult < .26: continue
                ult = tt
                bar.append(dict(t=tt, gx=float(rng.uniform(18, 72)), gw=24 if s['bpm'] < 150 else 26,
                                cor=int(rng.choice(v.get('cores', [9, 10, 12, 15])))))
        self.barreiras = bar
        self.ts_bar = [b['t'] for b in bar]
        r = np.random.default_rng(self.cfg['seed'] + 5)
        self.estrelas = [(r.uniform(0, 90), r.uniform(0, 2000), int(r.integers(1, 4))) for _ in range(90)]
        self.planetas = [(r.uniform(10, 80), 300 + k * 900 + r.uniform(0, 300), r.uniform(6, 16), int(r.choice([5, 6, 10, 12])))
                         for k in range(12)]

    def dist(self, t):
        k = min(len(self.D) - 1, max(0, int(t / self.dtD)))
        return self.D[k]

    def xfog(self, t):
        import bisect
        i = bisect.bisect_right(self.ts_bar, t)
        if i >= len(self.barreiras): return self.barreiras[-1]['gx'] if self.barreiras else 45
        nxt = self.barreiras[i]
        if i == 0: return nxt['gx']
        prv = self.barreiras[i - 1]
        u = (t - prv['t']) / max(1e-3, nxt['t'] - prv['t'])
        return prv['gx'] + (nxt['gx'] - prv['gx']) * ease(min(1, u * 1.4))

    def mundo(self, tela, t, i):
        L = self.L
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        build = sec['papel'] == 'build'
        d = self.dist(t)
        # céu: faixas do escuro que mudam a cada seção
        fundo = (0, 1, 0, 13, 1)[sec['i'] % 5]
        tela.limpar(fundo)
        # planetas lentos
        for (px_, py_, pr, pc) in self.planetas:
            yy = (d * .15 - py_)
            if -20 < yy < 180:
                tela.disco(px_, yy, pr, pc)
                tela.disco(px_ - pr * .3, yy - pr * .3, pr * .55, min(15, pc + 1))
        # estrelas em três planos; no drop viram riscos
        for (sx, sy, z) in self.estrelas:
            y = (sy + d * z * .45) % 180 - 10
            if drop:
                ln = int(2 + z * 3 * (1 + L.env('kick', t, .2)))
                tela.ret(sx, y - ln, 1, ln, 11 if z == 3 else 7)
            else:
                tela.px(sx, y, 11 if z == 3 else (7 if z == 2 else 4))
        # alerta no build
        if build:
            u = (t - sec['t0']) / max(.01, sec['t1'] - sec['t0'])
            if L.env('snare', t, .08) > .3:
                for k in range(-2, 12):
                    x0 = k * 10 + int(t * 40) % 10
                    tela.linha(x0, 0, x0 + 6, 6, 15)
                    tela.linha(x0, 153, x0 + 6, 159, 15)
        # barreiras
        ry = self.ry
        hat = L.env('hatf', t, .05)
        for b in self.barreiras:
            y = ry - (self.dist(b['t']) - d)
            dd = t - b['t']
            if dd < 0:
                if y < -10: continue
                gx, gw = b['gx'], b['gw']
                c = b['cor']
                for x in range(0, 90, 6):
                    if gx - gw / 2 - 5 < x < gx + gw / 2: continue
                    cc = 11 if (hat > .5 and (x // 6) % 2 == 0) else c
                    tela.ret(x, y - 3, 5, 6, cc)
                    tela.ret(x, y - 3, 5, 1, 11)
                # bordas da fenda acesas
                tela.ret(gx - gw / 2 - 2, y - 5, 2, 10, 11)
                tela.ret(gx + gw / 2, y - 5, 2, 10, 11)
            elif dd < .7:
                # explosão: cacos saem da linha da barreira
                rr = np.random.default_rng(int(b['t'] * 1000) & 0xffff)
                yb = ry + dd * 30
                for q in range(26):
                    x0 = rr.uniform(0, 90)
                    if abs(x0 - b['gx']) < b['gw'] / 2: continue
                    vx = (x0 - b['gx']) * rr.uniform(1.2, 3.0)
                    vy = rr.uniform(-60, 20)
                    tela.ret(x0 + vx * dd, yb + vy * dd + 120 * dd * dd, 2, 2, (b['cor'], 11)[q % 2])
                if dd < .18:
                    tela.anel(b['gx'], ry, 6 + dd * 260, 11, 1.2)
        # foguete
        x = self.xfog(t)
        tre = 0
        if build: tre = int(round(math.sin(t * 90) * 1.2))
        bas = L.env('baixo', t, .15)
        chama = 6 + bas * 5 + (6 if drop else 0) + (i % 3)
        fy = ry - 6
        cx = x + tre
        tela.ret(cx - 2, fy + 13, 4, chama, 10)
        tela.ret(cx - 1, fy + 13, 2, chama * .7, 9)
        tela.ret(cx - 1, fy + 13, 2, chama * .35, 11)
        self.fog.por(tela, cx - 5, fy)

    def sobre(self, tela, t, i):
        L = self.L
        n = sum(1 for b in self.barreiras if b['t'] <= t + 1e-6)
        if n > 0 and 2.6 < t < self.F.secoes[-1]['t0']:
            p = L.env('kick', t, .1)
            txt = f"{n} BARREIRAS"
            tam = 11 + (1 if p > .5 else 0)
            w = tela.largura_texto(txt, tam)
            tela.ret(90 - w // 2 - 3, 44, w + 6, 16, 0)
            tela.texto(txt, 90, 46, 11, tam=tam, centro=True)
