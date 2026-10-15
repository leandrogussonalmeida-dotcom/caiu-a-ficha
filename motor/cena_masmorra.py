#!/usr/bin/env python3
"""MASMORRA NO RITMO — o herói só anda na batida.

Um passo por tempo, exatamente no tempo: o pulo começa no instante da
batida e pousa antes da próxima. O chão é xadrez e troca de cor em cada
batida; as tochas tremulam no chimbal; os bichos pulam no lugar no tempo
deles; e quando o herói chega ao lado de um, a caixa é o golpe.

A barra de ritmo embaixo (marcadores que vêm das duas pontas e se encontram
no meio) mostra a batida que vem — a pessoa sente que dá para jogar junto.

Tudo é gerado: o caminho é decidido batida a batida antes do primeiro
quadro, e a masmorra é construída em volta dele.
"""
import math
import numpy as np
from ritmo_base import Sprite, W, H, ease

T = 12          # lado do ladrilho em pixels da tela baixa

HEROI = [
    "....hhhh....",
    "..hhhhhhhh..",
    ".FhssssssF..",
    "FFssessessFF",
    "FFsssssssFF.",
    ".F.ssmmss.F.",
    "...cccccc...",
    "..cccccccc..",
    ".sccCcCccs..",
    "..cccccccc..",
    "..cc....cc..",
    ".pp......pp.",
]
GELECA = [
    "...gggg...",
    ".gggggggg.",
    "gggGggggGg",
    "gggggggggg",
    "gge.gg.egg",
    "gggggggggg",
    ".gggggggg.",
]
MORCEGO_A = [
    "w..........w",
    "ww..bbbb..ww",
    "www.beeb.www",
    ".wwwbbbbwww.",
    "..ww.bb.ww..",
]
MORCEGO_B = [
    "....bbbb....",
    "...wbeebw...",
    "..wwbbbbww..",
    ".ww..bb..ww.",
    "ww........ww",
]
CAVEIRA = [
    "..oooooo..",
    ".oooooooo.",
    ".o.oooo.o.",
    ".oooooooo.",
    "..o.oo.o..",
    "...oooo...",
    "..oooooo..",
    ".o.oooo.o.",
    "...o..o...",
    "..oo..oo..",
]
MOEDA = [".yy.", "yYyy", "yYyy", ".yy."]


class Cena:
    def __init__(self, F, L, cfg, rng):
        self.F, self.L, self.cfg, self.rng = F, L, cfg, rng
        v = cfg.get('variante', {})
        self.cor_piso = v.get('piso', (2, 1))          # índices do xadrez
        self.cor_luz = v.get('luz', (9, 12, 10, 15))   # cores do piso aceso no drop
        self.cor_parede = v.get('parede', (4, 3, 13))
        mapa_h = {'h': v.get('cabelo', 13), 'F': 9, 's': 8, 'e': 0, 'm': 15,
                  'c': v.get('roupa', 12), 'C': 11, 'p': 3}
        self.heroi = Sprite(HEROI, mapa_h)
        self.inimigos_spr = {
            'geleca': Sprite(GELECA, {'g': v.get('geleca', 10), 'G': 11, 'e': 0}),
            'morcego': (Sprite(MORCEGO_A, {'w': 6, 'b': 5, 'e': 15}),
                        Sprite(MORCEGO_B, {'w': 6, 'b': 5, 'e': 15})),
            'caveira': Sprite(CAVEIRA, {'o': 7}),
        }
        self.moeda = Sprite(MOEDA, {'y': 9, 'Y': 11})
        self._planejar()

    # --------------------------------------------------------- o caminho
    def _planejar(self):
        rng = self.rng
        bats = [e for e in self.L.lista('batida')]
        self.bats = bats
        x, y = 0, 0
        pos = [(x, y)]
        d = (0, -1)
        corrida = 0
        for k in range(len(bats)):
            # sobe a maior parte do tempo; desvia em trechos curtos
            if corrida <= 0:
                r = rng.random()
                if d != (0, -1): d, corrida = (0, -1), int(rng.integers(3, 7))
                elif r < .5: d, corrida = (int(rng.choice([-1, 1])), 0), int(rng.integers(2, 4))
                else: corrida = int(rng.integers(2, 5))
            nx, ny = x + d[0], y + d[1]
            if abs(nx) > 5: d = (0, -1); nx, ny = x, y - 1
            x, y = nx, ny
            pos.append((x, y))
            corrida -= 1
        self.pos = pos
        # piso: corredor de 3 em volta do caminho, salas de vez em quando
        piso = set()
        for i, (px_, py_) in enumerate(pos):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    piso.add((px_ + dx, py_ + dy))
            if i % 23 == 11:
                for dx in range(-3, 4):
                    for dy in range(-3, 2):
                        piso.add((px_ + dx, py_ + dy))
        self.piso = piso
        # inimigos ao lado do caminho; o encontro é marcado numa batida de caixa
        self.inimigos = []
        cost = set(round(e['t'], 3) for e in self.L.lista('costas'))
        ocup = set(pos)
        tipos = list(self.inimigos_spr)
        for i in range(6, len(pos) - 4, 1):
            if rng.random() > .30: continue
            px_, py_ = pos[i]
            # quando o herói chega ao lado (batida i), o golpe é na próxima batida
            for dx, dy in ((1, 0), (-1, 0), (0, -1)):
                c = (px_ + dx, py_ + dy)
                if c in piso and c not in ocup:
                    self.inimigos.append(dict(c=c, i=i, tipo=tipos[int(rng.integers(len(tipos)))],
                                              dx=dx))
                    ocup.add(c)
                    break
        # o golpe: na batida i o herói chega, na i+1 bate (a caixa costuma estar lá)
        for e in self.inimigos:
            k = min(len(bats) - 1, e['i'] + 1)
            e['t_golpe'] = bats[k]['t'] if k < len(bats) else 1e9
            # escolhe a batida de golpe que caia numa caixa, se houver por perto
            for kk in (e['i'] + 1, e['i'] + 2):
                if kk < len(bats) and round(bats[kk]['t'], 3) in cost:
                    e['t_golpe'] = bats[kk]['t']; break
        self.particulas = []
        self.combo_t = [b['t'] for b in bats]
        self.tochas = set()
        for (tx, ty) in piso:
            if (tx, ty - 1) not in piso and (tx * 7 + ty * 3) % 5 == 0:
                self.tochas.add((tx, ty - 1))

    def heroi_pos(self, t):
        """Posição no mundo (em ladrilhos) e altura do pulo."""
        L = self.L
        k = L.idx('batida', t)
        if k < 0: return self.pos[0][0], self.pos[0][1], 0.0, 0
        k = min(k, len(self.pos) - 2)
        b = self.bats[k]
        spb = L.secao(t)['spb']
        u = (t - b['t']) / min(.16, spb * .45)       # o pulo dura no máximo 160 ms
        a = self.pos[k]; c = self.pos[k + 1]
        if u >= 1:
            return c[0], c[1], 0.0, k
        e = ease(u)
        return a[0] + (c[0] - a[0]) * e, a[1] + (c[1] - a[1]) * e, math.sin(math.pi * u), k

    def tremor(self, t):
        L = self.L
        p = L.env('drop', t, .25) * 4 + L.env('kick', t, .05) * (1.2 if L.secao(t)['papel'] == 'drop' else .4)
        k = int(t * 60)
        return (int(round(math.sin(k * 1.7) * p)), int(round(math.cos(k * 2.3) * p * .6)))

    # --------------------------------------------------------- o quadro
    def desenhar(self, tela_out, t, i):
        # o mundo é desenhado em meia resolução e dobrado: pixel gordo de
        # console portátil, herói legível no celular
        import pixelengine as PX
        if not hasattr(self, 'sub') or self.sub.pal != tela_out.pal:
            self.sub = PX.Tela(W // 2, H // 2, paleta=tela_out.pal)
        tela = self.sub
        self._mundo(tela, t, i)
        tela_out.buf[:] = np.repeat(np.repeat(tela.buf, 2, 0), 2, 1)
        self._sobre(tela_out, t)

    def _mundo(self, tela, t, i):
        W_, H_ = tela.w, tela.h
        L = self.L
        hx, hy, pulo, kb = self.heroi_pos(t)
        self._cam = None
        self._pops = []
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        build = sec['papel'] == 'build'
        nb = L.conta('batida', t)
        # câmera: herói a 62% da altura, centralizado na horizontal
        cx = hx * T - W_ / 2 + T / 2
        cy = hy * T - H_ * .55
        self._cam = (cx, cy)
        tela.limpar(0)

        x0t, x1t = int(math.floor(cx / T)) - 1, int(math.ceil((cx + W_) / T)) + 1
        y0t, y1t = int(math.floor(cy / T)) - 1, int(math.ceil((cy + H_) / T)) + 1
        pk = L.env('kick', t, .12)
        c_a, c_b = self.cor_piso
        luzes = self.cor_luz
        par_c, par_esc, par_top = self.cor_parede
        hat = L.env('hatf', t, .06)
        for ty in range(y0t, y1t):
            for tx in range(x0t, x1t):
                sx, sy = tx * T - cx, ty * T - cy
                if (tx, ty) in self.piso:
                    xadrez = (tx + ty + nb) % 2
                    cor = c_a if xadrez else c_b
                    if drop and xadrez and pk > .15:
                        cor = luzes[(tx * 3 + ty * 5 + nb) % len(luzes)]
                    elif build and xadrez:
                        # no build o piso acende numa onda que sobe para o herói
                        if (ty - int(hy)) % 4 == (nb % 4): cor = luzes[0]
                    tela.ret(sx, sy, T, T, cor)
                    tela.ret(sx, sy, T, 1, 0)
                    tela.ret(sx, sy, 1, T, 0)
                elif any(((tx + dx, ty + dy) in self.piso) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    # parede: topo claro, face com tijolos
                    tela.ret(sx, sy, T, T, par_c)
                    tela.ret(sx, sy, T, 3, par_top)
                    for r in range(4, T, 4):
                        tela.ret(sx, sy + r, T, 1, par_esc)
                    off = 0 if (ty % 2) else 6
                    tela.ret(sx + off, sy + 4, 1, 4, par_esc)
                    if (tx, ty) in self.tochas:
                        fl = 2 + int(hat * 3) + int((i // 3 + tx) % 2)
                        tela.ret(sx + 5, sy + 6, 2, 4, 6)
                        tela.ret(sx + 4, sy + 6 - fl, 4, fl, 15)
                        tela.ret(sx + 5, sy + 6 - fl + 1, 2, max(1, fl - 2), 9)

        # ---- moedas e inimigos
        for e in self.inimigos:
            ex, ey = e['c']
            sx, sy = ex * T - cx, ey * T - cy
            if sy < -20 or sy > H_ + 20: continue
            if t < e['t_golpe']:
                # pulam no lugar a cada batida
                hop = math.sin(math.pi * min(1, L.desde('batida', t) / .14)) if L.desde('batida', t) < .14 else 0
                spr = self.inimigos_spr[e['tipo']]
                if e['tipo'] == 'morcego':
                    spr = spr[(nb + int(ex)) % 2]
                    spr.por(tela, sx + (T - spr.w) / 2, sy + 1 - hop * 3)
                else:
                    spr.por(tela, sx + (T - spr.w) / 2, sy + T - spr.h - hop * 3)
            else:
                d = t - e['t_golpe']
                if d < .45:
                    # explode em cacos que voam
                    r = np.random.default_rng(int(ex * 31 + ey * 17) & 0xffff)
                    for q in range(14):
                        a = r.random() * math.tau; vv = 20 + r.random() * 60
                        px_ = sx + 6 + math.cos(a) * vv * d
                        py_ = sy + 6 + math.sin(a) * vv * d + 80 * d * d
                        tela.ret(px_, py_, 2, 2, (9, 11, 15)[q % 3])
                    if d < .12:
                        tela.anel(sx + 6, sy + 6, 4 + d * 80, 11, 1)
                        # o corte em diagonal
                        for k in range(12):
                            tela.ret(sx - 2 + k, sy + 10 - k, 2, 1, 11)
                if d < 2.5:
                    # moeda fica no chão girando
                    self.moeda.por(tela, sx + 4, sy + 4 - abs(math.sin(t * 9)) * 2)
                if .05 < d < .7:
                    self._pops.append((sx * 2 + 12, sy * 2 - 8 - d * 40))

        # ---- herói
        sx, sy = hx * T - cx, hy * T - cy
        dirx = self.pos[min(kb + 1, len(self.pos) - 1)][0] - self.pos[kb][0] if kb >= 0 else 0
        squash = L.env('batida', t, .05)
        # sombra
        tela.ret(sx + 2, sy + T - 2, 8, 2, 0)
        self.heroi.por(tela, sx, sy - pulo * 5 + (1 if squash > .6 and pulo < .1 else 0), flip=dirx < 0)

    def _sobre(self, tela, t):
        L = self.L
        sec = L.secao(t)
        drop = sec['papel'] in ('drop', 'fim')
        nb = L.conta('batida', t)
        for (x, y) in self._pops:
            tela.texto('+1', x, y, 9, tam=10, centro=True, sombra=0)
        self._barra(tela, t)
        if nb > 2 and 2.6 < t < self.F.secoes[-1]['t0']:
            pc = L.env('batida', t, .1)
            tam = 11 + (2 if pc > .5 else 0)
            txt = f"COMBO {nb}"
            w = tela.largura_texto(txt, tam)
            tela.ret(W // 2 - w // 2 - 3, 44, w + 6, 17, 0)
            tela.texto(txt, W // 2, 46 + (1 if pc <= .5 else 0), 11, tam=tam, centro=True)
            if drop:
                tela.ret(W // 2 + w // 2 + 4, 44, 18, 13, 15)
                tela.texto('x2', W // 2 + w // 2 + 13, 46, 11, tam=10, centro=True)

    def _barra(self, tela, t):
        L = self.L
        y = 228
        cx = W // 2
        tela.ret(14, y - 1, W - 28, 1, 3)
        # marcadores das próximas 3 batidas, vindo das pontas
        sec = L.secao(t)
        spb = sec['spb']
        prox = L.proximo('batida', t)
        if prox is None: return
        for k in range(4):
            tb = prox['t'] + k * spb
            u = (tb - t) / (spb * 4)
            if 0 <= u <= 1:
                dx = int(u * (cx - 18))
                tela.ret(cx - dx - 2, y - 6, 3, 11, 12)
                tela.ret(cx + dx, y - 6, 3, 11, 12)
        # o centro pulsa na batida
        p = L.env('batida', t, .10)
        r = 6 + p * 3
        tela.disco(cx, y, r, 15 if p > .3 else 5)
        tela.disco(cx, y, r - 3, 11 if p > .5 else 9)
