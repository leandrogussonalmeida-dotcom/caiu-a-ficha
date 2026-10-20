#!/usr/bin/env python3
"""ROTA 8-BIT — a viagem a pé pelos gêneros.

Visão de cima, como os RPGs de console portátil: o herói sobe pela rota um
ladrilho por batida. Cada seção da música é uma ZONA com chão, decoração e
paleta próprios — o campo do lo-fi, a cidade do house, a praia do reggaeton,
a caverna de cristal do dubstep, a cidade neon do drum and bass. Atravessar
a fronteira é trocar de som: a troca acontece no compasso exato em que o pé
pisa na zona nova.

O que reage a quê:
  batida   passo do herói, flores trocam de quadro, bichos pulam
  chimbal  capim alto balança
  bumbo    cristais e postes acendem, ondas quebram
  drop     clarão pontilhado e a zona inteira passa a piscar no bumbo
"""
import math
import numpy as np
import pixelengine as PX
from ritmo_base import CenaBase, Sprite, W, H, ease, hsh, nova_paleta
from cena_masmorra import HEROI

T = 10


ARVORE = [
    "...ggg...",
    ".ggGggGg.",
    "gGggggggg",
    "gggggGggg",
    ".gGggggg.",
    "..ggggg..",
    "....t....",
    "....t....",
]
PINHEIRO = [
    "....g....",
    "...ggg...",
    "..gGggg..",
    "...ggg...",
    "..ggGgg..",
    ".ggggggg.",
    "....t....",
]
PALMEIRA = [
    "..gg.gg..",
    ".gGggggGg",
    "gggGgGggg",
    "g.g.t.g.g",
    "g...t...g",
    "....t....",
    "....t....",
    "...t.....",
    "...t.....",
    "..tt.....",
]
CASA = [
    "...rrrrrr...",
    "..rrrrrrrr..",
    ".rrrrrrrrrr.",
    "rrrrrrrrrrrr",
    ".wwwwwwwwww.",
    ".wbbwwwwbbw.",
    ".wbbwddwbbw.",
    ".wwwwddwwww.",
]
CRISTAL = [
    "..c..",
    ".cCc.",
    ".cCc.",
    "cCCcc",
    ".ccc.",
]
COELHO = [
    ".w.w.",
    ".w.w.",
    "wwwww",
    "wewew",
    "wwwww",
    ".w.w.",
]


ZONAS = {
    'campo':   dict(chao=2, chao2=3, trilha=4, borda=5, deco=('arvore', 'capim', 'flor', 'flor', 'coelho')),
    'outono':  dict(chao=2, chao2=3, trilha=4, borda=5, deco=('arvore', 'capim', 'flor', 'coelho')),
    'cidade':  dict(chao=14, chao2=14, trilha=4, borda=14, deco=('casa', 'poste', 'cerca', 'flor')),
    'praia':   dict(chao=4, chao2=4, trilha=8, borda=5, deco=('palmeira', 'concha', 'palmeira')),
    'caverna': dict(chao=5, chao2=14, trilha=14, borda=0, deco=('cristal', 'pedra', 'cristal')),
    'neon':    dict(chao=1, chao2=2, trilha=3, borda=0, deco=('predio', 'poste', 'predio')),
    'neve':    dict(chao=11, chao2=7, trilha=14, borda=7, deco=('pinheiro', 'pinheiro', 'pedra')),
}


class Cena(CenaBase):
    zoom = 2

    def preparar(self):
        v = self.v
        self.zonas = v.get('zonas', ['campo', 'cidade', 'praia', 'caverna', 'neon'])
        self.heroi = Sprite(HEROI, {'h': 13, 'F': 15, 's': 8, 'e': 0, 'm': 15, 'c': 12, 'C': 11, 'p': 0})
        self.spr = {
            'arvore': Sprite(ARVORE, {'g': 1, 'G': 3, 't': 5}),
            'pinheiro': Sprite(PINHEIRO, {'g': 1, 'G': 3, 't': 5}),
            'palmeira': Sprite(PALMEIRA, {'g': 1, 'G': 3, 't': 5}),
            'casa': Sprite(CASA, {'r': 13, 'w': 11, 'b': 6, 'd': 5}),
            'cristal': Sprite(CRISTAL, {'c': 12, 'C': 11}),
            'cristal_ap': Sprite(CRISTAL, {'c': 6, 'C': 7}),
            'coelho': Sprite(COELHO, {'w': 11, 'e': 0}),
        }
        bats = self.L.lista('batida')
        self.bats = bats
        rng = self.rng
        x = 0
        pos = [(0, 0)]
        lado = 0
        for k in range(len(bats)):
            if lado == 0 and rng.random() < .16:
                lado = int(rng.choice([-1, 1])) * int(rng.integers(1, 3))
            if lado != 0 and abs(x + np.sign(lado)) <= 2:
                x += int(np.sign(lado)); lado -= int(np.sign(lado))
                pos.append((x, pos[-1][1]))
            else:
                lado = 0
                pos.append((x, pos[-1][1] - 1))
        self.pos = pos
        # zona de cada linha: a seção da batida em que o herói pisa nela
        self.zona_linha = {}
        for k, (px_, py_) in enumerate(pos[1:]):
            s = self.L.secao(bats[min(k, len(bats) - 1)]['t'])
            self.zona_linha.setdefault(py_, s['i'])
        self.ymin = min(p[1] for p in pos)
        self.trilha = set(pos)

    def zona(self, ty):
        if ty in self.zona_linha: si = self.zona_linha[ty]
        elif ty < self.ymin: si = len(self.F.secoes) - 1
        else: si = 0
        return ZONAS[self.zonas[si % len(self.zonas)]], self.zonas[si % len(self.zonas)]

    def heroi_pos(self, t):
        L = self.L
        k = L.idx('batida', t)
        if k < 0: return self.pos[0][0], self.pos[0][1], 0.0, 0
        k = min(k, len(self.pos) - 2)
        spb = L.secao(t)['spb']
        u = (t - self.bats[k]['t']) / min(.15, spb * .45)
        a, c = self.pos[k], self.pos[k + 1]
        if u >= 1: return c[0], c[1], 0.0, k
        e = ease(u)
        return a[0] + (c[0] - a[0]) * e, a[1] + (c[1] - a[1]) * e, math.sin(math.pi * u), k

    def mundo(self, tela, t, i):
        L = self.L
        Wt, Ht = tela.w, tela.h
        hx, hy, pulo, kb = self.heroi_pos(t)
        nb = L.conta('batida', t)
        pk = L.env('kick', t, .14)
        ph = L.env('hatf', t, .07)
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        cx = hx * T - Wt / 2 + T / 2
        cy = hy * T - Ht * .58
        tela.limpar(0)
        x0, x1 = int(math.floor(cx / T)) - 1, int(math.ceil((cx + Wt) / T)) + 1
        y0, y1 = int(math.floor(cy / T)) - 2, int(math.ceil((cy + Ht) / T)) + 2
        altos = []
        for ty in range(y0, y1):
            Z, zn = self.zona(ty)
            for tx in range(x0, x1):
                sx, sy = int(round(tx * T - cx)), int(round(ty * T - cy))
                h = hsh(tx, ty, 7)
                na_trilha = any((tx + d, ty) in self.trilha for d in (-1, 0, 1)) and abs(tx - self._xtrilha(ty)) <= 1
                if (tx, ty) in self.trilha or (abs(tx - self._xtrilha(ty)) <= 0 and ty >= self.ymin - 30):
                    cor = Z['trilha']
                    tela.ret(sx, sy, T, T, cor)
                    if zn == 'cidade' or zn == 'neon':
                        tela.ret(sx, sy, T, 1, Z['borda']); tela.ret(sx, sy, 1, T, Z['borda'])
                        if zn == 'neon' and drop and (tx + ty + nb) % 3 == 0 and pk > .2:
                            tela.ret(sx + 1, sy + 1, T - 1, T - 1, (10, 12, 9)[(ty + nb) % 3])
                    elif h % 5 == 0:
                        tela.px(sx + h % 7 + 1, sy + (h >> 3) % 7 + 1, Z['borda'])
                    continue
                cor = Z['chao'] if (h % 11) else Z['chao2']
                tela.ret(sx, sy, T, T, cor)
                dist = tx - self._xtrilha(ty)
                if zn == 'praia' and dist >= 3:
                    # mar numa faixa só, com a espuma quebrando no bumbo
                    tela.ret(sx, sy, T, T, 6 if dist > 3 else 7)
                    onda = (i // 5 + ty * 3) % 10
                    if onda < 6: tela.ret(sx + onda, sy + 4, 3, 1, 7 if dist > 3 else 11)
                    if dist == 3 and pk > .3: tela.ret(sx, sy, 3, T, 11)
                    continue
                if zn == 'campo' or zn == 'outono':
                    if h % 4 == 0: tela.px(sx + h % 8, sy + (h >> 4) % 8, 3)
                if abs(tx - self._xtrilha(ty)) == 1:
                    continue                            # beira da trilha livre
                d = Z['deco'][(h >> 5) % len(Z['deco'])]
                if (h >> 9) % 100 > 46: continue
                quica = 0
                if L.desde('batida', t) < .14 and (tx + ty) % 2 == nb % 2:
                    quica = int(round(math.sin(math.pi * L.desde('batida', t) / .14) * 2))
                if d == 'capim':
                    bal = int(round(ph * 2 * (1 if (tx + nb) % 2 else -1)))
                    for k in range(3):
                        tela.ret(sx + 1 + k * 3 + bal, sy + 3, 1, 6, 1)
                        tela.ret(sx + 2 + k * 3 + bal, sy + 2, 1, 7, 3)
                elif d == 'flor':
                    q = (nb + tx) % 2
                    cf = (9, 15, 11)[h % 3]
                    tela.ret(sx + 3, sy + 5 + q, 1, 3, 1)
                    tela.ret(sx + 2 - q, sy + 3 + q, 3 + 2 * q, 2, cf)
                    tela.px(sx + 3, sy + 4, 10)
                elif d == 'concha':
                    tela.ret(sx + 3, sy + 4, 3, 2, 11); tela.px(sx + 4, sy + 3, 10)
                elif d == 'agua':
                    tela.ret(sx, sy, T, T, 6)
                    onda = (i // 6 + tx * 3 + ty) % 6
                    tela.ret(sx + onda, sy + 3, 3, 1, 7)
                    if pk > .4: tela.ret(sx + 1, sy + 7, T - 2, 1, 11)
                elif d == 'pedra':
                    tela.ret(sx + 2, sy + 4, 6, 4, 14); tela.ret(sx + 3, sy + 3, 4, 1, 11 if zn == 'neve' else 7)
                elif d == 'poste':
                    tela.ret(sx + 4, sy - 6, 1, 14, 0)
                    luz = 9 if pk > .3 else 10
                    if zn == 'neon': luz = (12, 10, 15)[(nb + tx) % 3] if pk > .3 else 3
                    tela.ret(sx + 3, sy - 8, 3, 2, luz)
                elif d == 'cerca':
                    tela.ret(sx, sy + 4, T, 1, 5); tela.ret(sx + 2, sy + 2, 1, 6, 5); tela.ret(sx + 7, sy + 2, 1, 6, 5)
                elif d == 'predio':
                    altos.append(('predio', sx, sy, h, quica))
                elif d == 'cristal':
                    altos.append(('cristal', sx, sy, h, quica))
                elif d in ('arvore', 'pinheiro', 'palmeira', 'casa', 'coelho'):
                    altos.append((d, sx, sy, h, quica))
        # objetos altos desenhados depois, de cima para baixo
        for d, sx, sy, h, q in sorted(altos, key=lambda a: a[2]):
            if d == 'predio':
                hh = 14 + h % 12
                tela.ret(sx, sy + T - hh, T - 1, hh, 2)
                for wy in range(sy + T - hh + 2, sy + T - 1, 3):
                    for wx in (sx + 2, sx + 5):
                        if (hsh(wx, wy, i // 8) % 3 == 0) or (pk > .3 and (wx + wy) % 2):
                            tela.px(wx, wy, (9, 12, 10)[(wx // 3 + wy) % 3])
            elif d == 'cristal':
                spr = self.spr['cristal'] if pk > .25 or (h % 3 == 0) else self.spr['cristal_ap']
                spr.por(tela, sx + 2, sy + 3 - q)
            elif d == 'casa':
                self.spr['casa'].por(tela, sx - 1, sy + T - 8 - 4)
                if pk > .35:
                    tela.ret(sx + 1, sy + 1, 2, 2, 9); tela.ret(sx + 7, sy + 1, 2, 2, 9)
            elif d == 'coelho':
                self.spr['coelho'].por(tela, sx + 2, sy + 3 - q * 2)
            else:
                spr = self.spr[d]
                bal = int(round(L.env('costas', t, .12) * (1 if h % 2 else -1)))
                spr.por(tela, sx + bal * (d == 'palmeira'), sy + T - spr.h - q)
        # herói
        sx, sy = hx * T - cx, hy * T - cy
        dirx = (self.pos[min(kb + 1, len(self.pos) - 1)][0] - self.pos[kb][0]) if kb >= 0 else 0
        tela.ret(sx + 1, sy + T - 1, 9, 2, 0)
        self.heroi.por(tela, sx - 1, sy - 3 - pulo * 4, flip=dirx < 0)

    def _xtrilha(self, ty):
        if not hasattr(self, '_xt'):
            self._xt = {}
            for (x, y) in self.pos: self._xt.setdefault(y, x)
        return self._xt.get(ty, self.pos[-1][0] if ty < self.ymin else 0)

    def sobre(self, tela, t, i):
        L = self.L
        # clarão pontilhado na troca de zona (pixel não tem transparência)
        d = L.desde('secao', t)
        if t > .3 and d < .22:
            u = 1 - d / .22
            m = (np.add.outer(np.arange(H), np.arange(W)) % 2 == 0) if u < .6 else np.ones((H, W), bool)
            tela.buf[m] = 11
        # contador de passos no rodapé seguro
        nb = L.conta('batida', t)
        if nb > 0 and 2.6 < t < self.F.secoes[-1]['t0']:
            txt = f"{nb} STEPS"
            w = tela.largura_texto(txt, 10)
            tela.texto(txt, W // 2, 46, 11, tam=10, centro=True, contorno=0)
