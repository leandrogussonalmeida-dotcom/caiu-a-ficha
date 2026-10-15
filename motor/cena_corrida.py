#!/usr/bin/env python3
"""CORRIDA NO RITMO — estrada de fliperama em pseudo-3D.

A estrada é desenhada linha por linha, com profundidade por perspectiva.
O comprimento de cada faixa de zebra é escolhido para que DUAS faixas
passem pelo carro a cada batida: a estrada inteira é um metrônomo. Como a
velocidade é proporcional ao BPM, a zebra continua cravada no tempo quando
o andamento sobe.

Cada ultrapassagem acontece numa caixa (2 e 4): o adversário é posto na
pista de trás para frente a partir desse instante. A posição na corrida cai
de 9º para 1º até o fim.

Reage:
  batida   zebra e faixa central (pelo comprimento)
  bumbo    carro quica, sol pulsa
  caixa    ultrapassagem
  drop     turbo: chama no escapamento, riscos de velocidade, curva mais funda
"""
import math
import numpy as np
from ritmo_base import CenaBase, Sprite, W, H, ease, hsh, nova_paleta


CARRO = [
    "....kkkkkkkk....",
    "...kvvvvvvvvk...",
    "..kvvvvvvvvvvk..",
    ".kccccccccccccc.",
    "kcccccccccccccck",
    "kcLLccccccccLLck",
    "kccccccppcccccck",
    "kkkkkkkkkkkkkkkk",
    ".kk..........kk.",
]


class Cena(CenaBase):
    zoom = 1
    YH = 150          # horizonte

    def preparar(self):
        L = self.L
        v = self.v
        self.ceu = v.get('ceu', 'sol')
        self.cor_carro = v.get('carro', 15)
        self.carro = Sprite(CARRO, {'k': 0, 'v': 12, 'c': self.cor_carro, 'L': 9, 'p': 11})
        self.SEG = 1.0
        dt = 1 / 240.
        n = int(self.F.total / dt) + 10
        P = np.zeros(n)
        for k in range(1, n):
            s = L.secao(k * dt)
            P[k] = P[k - 1] + (2 * self.SEG / s['spb']) * dt     # 2 faixas por batida
        self.P, self.dtP = P, dt
        # ultrapassagens: caixas em seções cheias, uma a cada duas
        cost = [e for e in L.lista('costas') if L.secao(e['t'])['papel'] in ('drop',)]
        self.passes = []
        ult = -9
        for e in cost:
            if e['t'] - ult < .9: continue
            ult = e['t']
            self.passes.append(dict(t=e['t'], lado=1 if len(self.passes) % 2 else -1,
                                    cor=(10, 12, 9, 6, 3)[len(self.passes) % 5]))
        # no máximo 11 ultrapassagens, espalhadas: largar em 27º não é
        # corrida, é engarrafamento
        if len(self.passes) > 11:
            idx = np.linspace(0, len(self.passes) - 1, 11).round().astype(int)
            self.passes = [self.passes[k] for k in idx]
            for k, ps in enumerate(self.passes):
                ps['lado'] = 1 if k % 2 else -1
        self.n_pass = len(self.passes)
        self.rivais = [Sprite(CARRO, {'k': 0, 'v': 12, 'c': c, 'L': 9, 'p': 11}) for c in (10, 12, 9, 3, 6)
                       if c != self.cor_carro]
        r = np.random.default_rng(self.cfg['seed'] + 3)
        self.montanhas = [int(18 + 14 * abs(math.sin(k * .21)) + 9 * abs(math.sin(k * .57 + 1)) + r.uniform(0, 4)) for k in range(W + 40)]
        self.predios = [(int(r.integers(0, W + 60)), int(r.integers(8, 34)), int(r.integers(10, 26))) for _ in range(26)]

    def pos(self, t):
        k = min(len(self.P) - 1, max(0, int(t / self.dtP)))
        return self.P[k]

    def curva(self, d):
        return math.sin(d * .045) * .9 + math.sin(d * .013 + 1.3) * .6

    def mundo(self, tela, t, i):
        L = self.L
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        nb = L.conta('batida', t)
        pk = L.env('kick', t, .12)
        d = self.pos(t)
        YH = self.YH
        cv = self.curva(d) * (1.4 if drop else 1.0)
        # ------------------------------------------------ céu
        if self.ceu == 'sol':
            for k, c in enumerate((0, 1, 2, 3, 4)):
                tela.ret(0, k * YH // 5, W, YH // 5 + 1, c)
            r = 34 + pk * 3
            cx, cy = W // 2 - cv * 14, YH - 18
            for yy in range(int(cy - r), int(cy) + 1):
                hw = math.sqrt(max(0, r * r - (yy - cy) ** 2))
                fr = (yy - (cy - r)) / r
                cor = 9 if fr < .35 else (8 if fr < .6 else (7 if fr < .8 else 6))
                # cortes horizontais do sol que descem uma linha por batida
                if fr > .45 and (yy + nb) % 5 == 0: continue
                tela.ret(cx - hw, yy, hw * 2, 1, cor)
            base = 5
        elif self.ceu == 'deserto':
            for k, c in enumerate((7, 7, 6, 6, 5)):
                tela.ret(0, k * YH // 5, W, YH // 5 + 1, c)
            tela.disco(W * .75, 50, 12 + pk * 2, 11)
            base = 2
        else:
            tela.limpar(0)
            for k in range(60):
                h_ = hsh(k, 3)
                tela.px(h_ % W, (h_ >> 8) % (YH - 40), 11 if (h_ >> 4) % 3 else 7)
            base = 3
        # montanhas ou prédios no horizonte, deslizam com a curva
        off = int(cv * 20 + d * .4) % 40
        if self.ceu == 'noite':
            for (px_, ph, pw) in self.predios:
                x = (px_ - off * 2) % (W + 60) - 30
                tela.ret(x, YH - ph - 6, pw, ph + 6, 2)
                for wy in range(YH - ph - 3, YH - 3, 4):
                    for wx in range(x + 2, x + pw - 2, 4):
                        if hsh(wx + px_, wy, nb // 2) % 3 == 0: tela.ret(wx, wy, 2, 2, (9, 10, 12)[(wx + wy) % 3])
        else:
            for x in range(W):
                hm = self.montanhas[(x + off) % len(self.montanhas)]
                tela.ret(x, YH - hm, 1, hm, base)
        # ------------------------------------------------ chão e estrada
        chao_a, chao_b = {'sol': (13, 14), 'deserto': (3, 4), 'noite': (13, 1)}[self.ceu]
        zebra_a, zebra_b = (11, 15) if not (drop and pk > .3) else (9, 12)
        dx = 0.0; xoff = 0.0
        for y in range(YH, H):
            p = (y - YH + 1) / (H - YH)
            z = 1.0 / p
            dist = d + z * 2.2
            listra = int(dist / self.SEG) % 2
            # a base da estrada fica sob o carro; a curva entorta o fundo
            cx = W / 2 + cv * 70 * (1 - p) ** 2.2
            hw = 8 + (y - YH) * .62
            tela.ret(0, y, W, 1, chao_a if listra else chao_b)
            if self.ceu == 'sol' and (y - YH) % 9 == int(d * 3) % 9:
                tela.ret(0, y, W, 1, 10)       # grade neon do chão
            rw = max(1, hw * .14)
            tela.ret(cx - hw - rw, y, rw, 1, zebra_a if listra else zebra_b)
            tela.ret(cx + hw, y, rw, 1, zebra_a if listra else zebra_b)
            tela.ret(cx - hw, y, hw * 2, 1, 14 if listra else 13 if self.ceu != 'deserto' else 14)
            if self.ceu == 'deserto': tela.ret(cx - hw, y, hw * 2, 1, 13 if listra else 14)
            if listra:
                tela.ret(cx - max(1, hw * .03), y, max(1, hw * .06), 1, 11)
            self._cx_linha = getattr(self, '_cx_linha', {})
            self._cx_linha[y] = (cx, hw)
        # postes na beira: um a cada batida, na largura certa
        for k in range(int(d / (2 * self.SEG)) + 1, int(d / (2 * self.SEG)) + 14):
            dz = (k * 2 * self.SEG - d) / 2.2
            if dz <= 0.05: continue
            y = int(YH - 1 + (H - YH) / dz)
            if y >= H or y <= YH: continue
            cx, hw = self._cx_linha.get(y, (W / 2, 10))
            sc = (y - YH) / (H - YH)
            for lado in (-1, 1):
                x = cx + lado * (hw + 8 * sc + 6)
                alt = int(60 * sc) + 2
                tela.ret(x, y - alt, max(1, 2 * sc + 1), alt, 0 if self.ceu != 'deserto' else 1)
                luz = 9 if (k + nb) % 2 else 12
                if self.ceu == 'deserto':
                    tela.ret(x - 6 * sc, y - alt, 12 * sc + 2, max(1, 5 * sc), 1)   # cacto-placa
                else:
                    tela.ret(x - lado * 6 * sc, y - alt, max(1, 8 * sc), max(1, 3 * sc), luz if pk > .2 else 7)
        # ------------------------------------------------ adversários
        vrel = 1.0
        for k, ps in enumerate(self.passes):
            u = ps['t'] - t                       # segundos até a ultrapassagem
            if u < -.4 or u > 3.2: continue
            dz = .55 + u * 1.25
            y = int(YH - 1 + (H - YH) / max(.3, dz) * .55)
            if y <= YH or y >= H: continue
            cx, hw = self._cx_linha.get(min(H - 1, y), (W / 2, 20))
            sc = (y - YH) / (H - YH)
            x = cx + ps['lado'] * hw * .45
            esc = 1 if sc < .3 else (2 if sc < .62 else 3)
            spr = self.rivais[k % len(self.rivais)]
            spr.por(tela, x - 8 * esc, y - 9 * esc, esc=esc)

        # ------------------------------------------------ nosso carro
        quica = int(round(pk * 2))
        incl = -cv * 4
        cx = W / 2 + incl
        cy = H - 70 - quica
        self.carro.por(tela, cx - 24, cy, esc=3)
        if drop:
            for k in range(2):
                fl = 6 + (i % 3) * 3 + int(pk * 6)
                tela.ret(cx - 14 + k * 24, cy + 27, 5, fl, 10)
                tela.ret(cx - 13 + k * 24, cy + 27, 3, fl // 2, 9)
            for k in range(10):
                h_ = hsh(k, i // 2)
                x = h_ % W
                tela.ret(x, (h_ >> 8) % 150 + 160, 1, 10 + (h_ >> 4) % 12, 11)

    def sobre(self, tela, t, i):
        L = self.L
        if t < 2.6 or t >= self.F.secoes[-1]['t0']: return
        feitos = sum(1 for p in self.passes if p['t'] <= t + 1e-6)
        posicao = max(1, self.n_pass + 1 - feitos)
        p = L.env('costas', t, .15)
        txt = f"{posicao}º"
        tam = 18 + (3 if p > .5 and feitos else 0)
        w = tela.largura_texto(txt, tam)
        tela.ret(W // 2 - w // 2 - 5, 44, w + 10, tam + 6, 0)
        tela.texto(txt, W // 2, 46, 9 if posicao == 1 else 11, tam=tam, centro=True)
        sec = L.secao(t)
        kmh = int(sec['bpm'] * 2 * (1.25 if sec['papel'] == 'drop' else 1))
        txt = f"{kmh} KM/H"
        w = tela.largura_texto(txt, 9)
        tela.ret(W // 2 - w // 2 - 3, 72, w + 6, 13, 0)
        tela.texto(txt, W // 2, 74, 12, tam=9, centro=True)
