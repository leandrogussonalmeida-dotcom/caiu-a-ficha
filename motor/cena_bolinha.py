#!/usr/bin/env python3
"""A BOLINHA QUE TOCA A MÚSICA — cada quique é uma nota da melodia.

A trajetória é calculada a partir das notas: entre duas notas a bolinha
faz uma parábola de gravidade constante, e a plataforma seguinte é posta
exatamente onde ela cai no instante da nota. A cor da plataforma é a nota
(as 12 notas da escala em 12 cores fixas), então a melodia fica escrita
na escada que a bolinha deixa para trás.
"""
import math
import numpy as np
from idioma import T
from ritmo_base import CenaBase, W, H, ease, hsh

CORES_NOTA = [15, 10, 9, 12, 6, 7, 11, 15, 10, 9, 12, 7]


class Cena(CenaBase):
    zoom = 1
    G = 900.0

    def preparar(self):
        L = self.L
        # quiques: as notas da melodia; onde a melodia cala (build, compasso
        # sem lead), o bumbo assume — senão a bolinha sumia num salto de 4 s
        fim = [s for s in self.F.secoes if s['papel'] == 'fim'][0]['t0']
        cand = [e for e in L.lista('lead') if e['t'] < fim]
        lt = np.array([e['t'] for e in cand]) if cand else np.array([-9.0])
        for e in L.lista('kick') + L.lista('costas'):
            if e['t'] < fim and np.min(np.abs(lt - e['t'])) > .28:
                cand.append(dict(t=e['t'], m=60 + (hsh(int(e['t'] * 1000)) % 12)))
        cand.sort(key=lambda e: e['t'])
        sel = []
        for e in cand:
            if sel and e['t'] - sel[-1]['t'] < .11: continue
            sel.append(e)
        self.notas = sel
        r = self.rng
        x, y = 90.0, 0.0
        vx_mod = 105.0
        dirx = 1
        P = [(sel[0]['t'], x, y, sel[0].get('m', 60))]
        self.traj = []
        for a, b in zip(sel, sel[1:]):
            dt = b['t'] - a['t']
            if r.random() < .22: dirx = -dirx
            nx = x + dirx * vx_mod * dt
            if nx < 24 or nx > 156:
                dirx = -dirx; nx = x + dirx * vx_mod * dt
            dy = 12 + 40 * dt
            vy = (dy - .5 * self.G * dt * dt) / dt
            self.traj.append(dict(t0=a['t'], t1=b['t'], x0=x, y0=y, vx=(nx - x) / dt, vy=vy))
            x, y = nx, y + dy
            P.append((b['t'], x, y, b.get('m', 60)))
        self.plats = P
        self.ts = np.array([p[0] for p in P])
        self.estilo = self.v.get('fundo', 'grade')

    def bola(self, t):
        k = int(np.searchsorted(self.ts, t, 'right')) - 1
        if k < 0: return self.plats[0][1], self.plats[0][2] - 60 * (1 - t / max(.01, self.ts[0])) ** 2
        if k >= len(self.traj):
            p = self.plats[-1]; return p[1], p[2]
        s = self.traj[k]
        u = t - s['t0']
        return s['x0'] + s['vx'] * u, s['y0'] + s['vy'] * u + .5 * self.G * u * u

    def mundo(self, tela, t, i):
        L = self.L
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        pk = L.env('kick', t, .14)
        bx, by = self.bola(t)
        # câmera vertical suave: a bolinha a 45% da altura
        cam = by - H * .45
        if not hasattr(self, '_cam'): self._cam = cam
        tela.limpar(0)
        # fundo
        if self.estilo == 'grade':
            off = int(cam * .5) % 16
            for y in range(-off, H, 16):
                tela.ret(0, y, W, 1, 1 if not (drop and pk > .3) else 2)
            for x in range(0, W, 16):
                tela.ret(x, 0, 1, H, 1)
        elif self.estilo == 'estrelas':
            for k in range(80):
                h = hsh(k, 4)
                y = ((h >> 8) % 600 - cam * .3) % H
                tela.px(h % W, y, 7 if (h >> 3) % 3 else 11)
        else:
            for k in range(12):
                h = hsh(k, 8)
                y = ((h >> 8) % 900 - cam * .2) % (H + 80) - 40
                tela.disco(h % W, y, 10 + h % 18, 1 if k % 2 else 13)
        # anel de batida no centro do fundo
        if drop:
            r = 20 + (1 - pk) * 80
            tela.anel(W / 2, H / 2, r, 2, 1)
        # plataformas (só as que já existem ou estão perto)
        kat = int(np.searchsorted(self.ts, t, 'right'))
        for k, (tp, x, y, m) in enumerate(self.plats):
            sy = y - cam
            if sy < -10 or sy > H + 10: continue
            batida = tp <= t + 1e-6
            cor = CORES_NOTA[m % 12] if batida else 3
            tela.ret(x - 13, sy + 6, 26, 4, cor)
            if batida:
                tela.ret(x - 13, sy + 6, 26, 1, 11)
                tela.ret(x - 13, sy + 10, 26, 1, 0)
                d = t - tp
                if d < .25:
                    tela.anel(x, sy + 7, 6 + d * 90, cor, 1.2)
                    tela.ret(x - 15, sy + 5, 30, 6, 11) if d < .05 else None
        # rastro
        for k in range(1, 9):
            tx, ty = self.bola(t - k * .018)
            tela.disco(tx, ty - cam, max(.5, 5.5 - k * .55), 2 if k > 4 else 5)
        # bolinha (amassa no impacto)
        d = t - self.ts[max(0, kat - 1)] if kat > 0 else 1
        sq = math.exp(-d / .05) if d >= 0 else 0
        r = 6.0
        for yy in range(-8, 9):
            for xx in range(-9, 10):
                if (xx / (r * (1 + .35 * sq))) ** 2 + (yy / (r * (1 - .3 * sq))) ** 2 <= 1:
                    tela.px(bx + xx, by - cam + yy + sq, 11 if (xx < 0 and yy < 0) else 9)

    def sobre(self, tela, t, i):
        if t < 2.6 or t >= self.F.secoes[-1]['t0']: return
        n = int(np.searchsorted(self.ts, t, 'right'))
        txt = T(f"{n} NOTAS", f"{n} NOTES")
        w = tela.largura_texto(txt, 11)
        tela.texto(txt, W // 2, 46, 11, tam=11, centro=True, contorno=0)
