#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep04 — Como a tela do celular faz cada pixel (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

O protagonista é UM pixel: um ponto do sol na foto do celular (amarelo, com
o vermelho e o verde acesos e o azul apagado). O zoom chega nele, o LCD e o
OLED abrem um pixel igual a ele, e no fim o próprio vídeo é aberto até ele.

    python3 ep04_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep04_motor.py <saida.mp4> zoom cores       # só esses capítulos (teste)
    python3 ep04_motor.py --folha <saida.png>          # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import pixelengine as PX
import longo as LG
import ep04_desenho as D                      # registra a paleta 'ep04' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, painel, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0,
                   ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0, LATAO, OLEO0,
                   CERAMICA, PRETO, VERDE, ROXO)
from ep04_desenho import SUB, NEGRO, PRETO_LCD, AMA_P, CIA_P, MAG_P, MEDIA, SOL, IMG_W, IMG_H
import ritmo_marca as RM
from ep04_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2604, 48
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
PX0 = 302                     # coluna do painel da direita
CLIP = (0, 0, 296, PALCO_H)   # o palco à esquerda do painel


def milhar(n): return f"{int(round(n)):,}".replace(',', '.')
def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def lerp(a, b, u): return a + (b - a) * u
def zlog(z0, z1, u): return math.exp(math.log(z0) + (math.log(z1) - math.log(z0)) * u)


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def fundo(self, tela, t, grade=True):
        """Parede escura com uma grade de pixels muito apagada."""
        tela.buf[:PALCO_H] = FUNDO
        if grade:
            for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
            for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
            for x in range(12, W, 24):                      # trinca R G B apagada nos cruzamentos
                for y in range(0, PALCO_H, 24):
                    for k in range(3): tela.px(x - 1 + k, y, SUB[k, 0])

    def painel_titulo(self, tela, txt, y, cor=ACO3):
        if not VERTICAL: tela.texto(txt, PX0, y, cor, tam=9, contorno=PRETO)

    def painel_valor(self, tela, txt, y, cor=AMARELO):
        if not VERTICAL: tela.texto(txt, PX0, y, cor, tam=17, contorno=PRETO)


def mesa(tela, sx, sy, z, larg=296):
    """Celular de pé num suporte em cima da mesa (só quando o zoom é pequeno)."""
    sw, sh = IMG_W * z, IMG_H * z
    b = 2.2 * z
    fundo_y = sy + sh + b * 1.6
    if fundo_y > PALCO_H + 40: return
    tela.ret(0, fundo_y + 6 * z / 2, larg, PALCO_H - fundo_y, OLEO0)
    dither(tela, 0, fundo_y + 6 * z / 2, larg, 4 * z, LATAO, OLEO0)
    tela.ret(0, fundo_y + 6 * z / 2, larg, 1, CERAMICA)
    # suporte: calço atrás do celular
    sx0, sx1 = sx - b - 6 * z / 2, sx + sw + b + 6 * z / 2
    tela.ret(sx0 - 1, fundo_y - 1 * z, sx1 - sx0 + 2, 8 * z / 2 + 1, PRETO)
    tela.ret(sx0, fundo_y, sx1 - sx0, 6 * z / 2, ACO0)
    tela.ret(sx0, fundo_y, sx1 - sx0, 1, ACO2)


# ============================================================ 0 gancho
class Gancho(Cena):
    def camera(self, t):
        u = suave(t / 6.0)
        z = zlog(2.0, 44.0, u) if t < 6 else lerp(44.0, 52.0, (t - 6) / 6.0)
        p = min(1.0, math.log(z / 2.0) / math.log(44.0 / 2.0))
        ax, ay = lerp(255, 240, p), lerp(59, 104, p)
        return z, ax - (SOL[0] + .5) * z, ay - (SOL[1] + .5) * z

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        z, ox, oy = self.camera(t)
        mesa(tela, ox, oy, z, larg=W)
        D.celular(tela, D.paisagem(t), ox, oy, z, t, clip=(0, 0, W, PALCO_H))
        cx, cy = ox + (SOL[0] + .5) * z, oy + (SOL[1] + .5) * z
        if z >= 6:
            r = z / 2
            tela.ret_vazado(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, AMARELO)
        if t > 6.4:
            for k, (nome, tx, ty, dy) in enumerate((('VERMELHO', 60, 24, -12), ('VERDE', 150, 180, 14),
                                                    ('AZUL', 330, 40, -12))):
                if t < 6.4 + k * .5: continue
                ax = ox + (SOL[0] + (k + .5) / 3) * z
                D.rotulo(tela, nome, tx, ty, ax, cy + dy, SUB[k, 3], tam=17)

    def sons(self, fx):
        for k in range(12):
            fx.put(fx.blip(60 + k * 2, .06), self.t0 + .2 + k * .45, .10)
        for k, m in enumerate((72, 76, 79)):
            fx.put(fx.sino(m), self.t0 + 6.4 + k * .5, .35, -.4 + .4 * k)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        # trincas R G B apagadas andando no fundo
        for j in range(0, H, 12):
            for i in range(-1, W // 12 + 2):
                x = i * 12 + int(t * 6) % 12 - (j // 12 % 2) * 6
                for k in range(3): tela.ret(x + k * 3, j + 3, 2, 6, SUB[k, 0])
        n = int(t / .04)
        for j, linha in enumerate(("COMO A TELA DO CELULAR", "FAZ CADA PIXEL")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 22)]
            tela.texto(vis, W // 2 - larg // 2, 60 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.4:
            tela.texto("FEITO DE PIXELS", W // 2, 132, AMARELO, tam=17, centro=True, contorno=PRETO)
        for k in range(3):
            if t > 2.0 + k * .4:
                x = W // 2 - 60 + k * 44
                painel(tela, x - 2, 158, 26, 26, borda=SUB[k, 3])
                tela.ret(x + 2, 162, 18, 18, SUB[k, 3])
                tela.ret(x + 4, 164, 4, 14, BRANCO)
        if t > 3.4:
            x = W // 2 + 72
            tela.texto("=", x, 166, BRANCO, tam=17, contorno=PRETO)
            painel(tela, x + 16, 158, 26, 26, borda=BRANCO)
            tela.ret(x + 20, 162, 18, 18, BRANCO)

    def sons(self, fx):
        for k, m in enumerate((72, 76, 79)):
            fx.put(fx.blip(m, .1), self.t0 + 2.0 + k * .4, .25)
        fx.put(fx.sino(84), self.t0 + 3.4, .3)


# ============================================================ 2 zoom
class Zoom(Cena):
    def camera(self, t):
        if t < 8: z = 2.0
        elif t < 30: z = zlog(2.0, 30.0, suave((t - 8) / 22.0))
        else: z = lerp(30.0, 40.0, (t - 30) / 6.0)
        p = math.log(z / 2.0) / math.log(40.0 / 2.0)
        ax, ay = lerp(163, 148, min(1, p * 1.4)), lerp(59, 104, min(1, p * 1.4))
        return z, ax - (SOL[0] + .5) * z, ay - (SOL[1] + .5) * z

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        z, ox, oy = self.camera(t)
        mesa(tela, ox, oy, z)
        D.celular(tela, D.paisagem(t), ox, oy, z, t, clip=CLIP)
        cx, cy = ox + (SOL[0] + .5) * z, oy + (SOL[1] + .5) * z
        # alvo piscando no ponto do sol
        if t < 15.8 and int(t * 3) % 2 == 0:
            r = max(3, z * .5 + 2)
            tela.ret_vazado(cx - r, cy - r, 2 * r + 1, 2 * r + 1, AMARELO)
        if 15.8 <= t < 23.8 and z > 6:
            r = z * .5
            tela.ret_vazado(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, AMARELO)
            if not VERTICAL: D.rotulo(tela, '1 PIXEL', 196, 20, cx + r + 1, cy - r, AMARELO)
        if t >= 23.8:
            for k, (txt, tx, ty) in enumerate(((' ACESO', 62, 18), (' ACESO', 104, 186), (' APAGADO', 160, 34))):
                if t < 23.8 + k * .4: continue
                ax = ox + (SOL[0] + (k + .5) / 3) * z
                nome = D.NOME_CANAL[k] + ':' + txt
                D.rotulo(tela, nome, tx, ty, ax, cy + (-12 if k != 1 else 14), SUB[k, 3] if k < 2 else ACO3)
        # painel
        self.painel_titulo(tela, 'AUMENTO', 12)
        self.painel_valor(tela, f"{milhar(z / 2.0)}X", 24)
        self.painel_titulo(tela, 'O QUE APARECE', 56)
        fase = 'A FOTO' if z < 5 else ('PIXELS' if z < 16 else 'SUBPIXELS')
        self.painel_valor(tela, fase, 68, BRANCO)
        if not VERTICAL:
            # escada do zoom: foto -> pixels -> subpixels
            for j, (nome, lim) in enumerate((('FOTO', 2), ('PIXELS', 5), ('SUBPIXELS', 16))):
                y = 100 + j * 22
                aceso = z >= lim
                tela.ret(PX0, y + 1, 8, 8, AMARELO if aceso else FUNDO2)
                tela.texto(nome, PX0 + 14, y, BRANCO if aceso else ACO1, tam=9, contorno=PRETO)
            if t >= 30:
                tela.texto('ESTE PIXEL:', PX0, 172, ACO3, tam=9, contorno=PRETO)
                for k, n in enumerate((3, 3, 0)):
                    tela.ret(PX0 + k * 8, 184, 6, 14, SUB[k, n])
                tela.texto('=', PX0 + 30, 186, BRANCO, tam=9, contorno=PRETO)
                D.amostra(tela, PX0 + 42, 186, AMA_P, 10)
                tela.texto('AMARELO', PX0 + 58, 186, AMA_P, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k, t in enumerate((10, 14, 18, 22, 26)):
            fx.put(fx.blip(64 + k * 3, .08), self.t0 + t, .14)
        for k, m in enumerate((72, 76, 79)):
            fx.put(fx.sino(m), self.t0 + 23.8 + k * .4, .3, -.4 + .4 * k)


# ============================================================ 3 subpixel
class Subpixel(Cena):
    CICLO = [(255, 128, 0), (0, 255, 255), (170, 0, 255), (255, 255, 255)]

    def valores(self, t):
        if t < 8.0: return [255.0, 255.0, 0.0]
        if t < 16.0:
            u = min(1.0, max(0.0, (t - 8.6) / 6.4))
            return [255.0 * u, 0.0, 0.0]
        k = int((t - 16.0) / 2.0)
        u = suave(((t - 16.0) % 2.0) / .5)
        a = self.CICLO[k - 1] if k > 0 else (255, 0, 0)
        b = self.CICLO[min(k, len(self.CICLO) - 1)]
        return [lerp(a[i], b[i], u) for i in range(3)]

    def listra(self, tela, x, y, w, h, k, v, t):
        n = v / 85.0
        f0 = int(min(2, math.floor(n))); fr = n - f0
        x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(296, int(x + w)), min(PALCO_H, int(y + h))
        if x1 <= x0: return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        m = LG.BAYER8[yy % 8, xx % 8] < fr
        tela.buf[y0:y1, x0:x1] = np.where(m, SUB[k, min(3, f0 + 1)], SUB[k, f0])
        if v > 200:                                            # brilho subindo dentro da luz
            for j in range(4):
                u = (t * .5 + j / 4 + k * .2) % 1.0
                tela.ret(x + 6 + (j * 13) % max(1, int(w) - 12), y + h - u * h, 2, 2, BRANCO)

    def pixel(self, tela, x, y, L, vals, t):
        x0, x1 = max(0, x - 2), min(296, x + L + 2)
        if x1 <= x0: return
        tela.ret(x0, y - 2, x1 - x0, L + 4, NEGRO)
        g = max(2, L // 30)
        lw = (L - 4 * g) / 3
        for k in range(3):
            xs = x + g + k * (lw + g)
            self.listra(tela, xs, y + g, lw, L - 2 * g, k, vals[k], t)
            if vals[k] > 40 and xs + 3 < 296 and xs > 0:      # sombreado: luz na borda, sombra embaixo
                n = int(min(3, round(vals[k] / 85)))
                tela.ret(xs, y + g, min(3, 296 - xs), L - 2 * g, SUB[k, 3] if n < 3 else BRANCO)
                if xs + lw <= 296:
                    tela.ret(xs + lw - 3, y + g, 3, L - 2 * g, SUB[k, max(0, n - 1)])
                tela.ret(xs, y + L - g - 4, max(0, min(lw, 296 - xs)), 4, SUB[k, max(0, n - 1)])

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t, grade=False)
        vals = self.valores(t)
        L = 172
        x, y = 62, 18
        vz = [255, 160, 0]                                       # vizinhos: borda laranja do sol
        self.pixel(tela, x - L - 8, y, L, vz, t)
        self.pixel(tela, x + L + 8, y, L, [255, 255, 0], t)
        self.pixel(tela, x, y, L, vals, t)
        tela.ret_vazado(x - 4, y - 4, L + 8, L + 8, AMARELO)
        if not VERTICAL:
            for k in range(3):
                yy = 12 + k * 40
                tela.texto(D.NOME_CANAL[k], PX0, yy, SUB[k, 3], tam=17, contorno=PRETO)
                v = vals[k]
                tela.ret(PX0, yy + 20, 102, 8, PRETO); tela.ret(PX0 + 1, yy + 21, 100, 6, FUNDO2)
                tela.ret(PX0 + 1, yy + 21, int(100 * v / 255), 6, SUB[k, 3])
                tela.texto(str(int(round(v))), PX0 + 110, yy + 20, BRANCO, tam=9, contorno=PRETO)
            tela.texto('DE 0 A 255', PX0, 132, ACO3, tam=9, contorno=PRETO)
            n = [int(round(v / 85)) for v in vals]
            tela.texto('DE LONGE:', PX0, 152, ACO3, tam=9, contorno=PRETO)
            D.amostra(tela, PX0 + 60, 150, MEDIA[n[0], n[1], n[2]], 12)
            tela.texto(D.nome_cor(*n), PX0 + 80, 152, BRANCO, tam=9, contorno=PRETO)
            if t >= 16.0:
                tela.texto('CORES POSSÍVEIS', PX0, 172, ACO3, tam=9, contorno=PRETO)
                tela.texto('16.777.216', PX0, 184, AMARELO, tam=17, contorno=PRETO)

    def sons(self, fx):
        for k in range(9):
            fx.put(fx.blip(60 + k * 2, .05), self.t0 + 8.6 + k * .8, .09)
        for k in range(4):
            fx.put(fx.blip(76 + k * 2, .1), self.t0 + 16.0 + k * 2.0, .14)


# ============================================================ 4 cores
class Cores(Cena):
    POS_FIM = [(128, 76), (168, 76), (148, 110)]
    POS_INI = [(74, 86), (148, 86), (222, 86)]
    RAIO = 36

    def estado(self, t):
        """(posições, ligado 0..1 de cada luz)."""
        u = suave((t - 7.0) / 1.0)
        pos = [(lerp(a[0], b[0], u), lerp(a[1], b[1], u)) for a, b in zip(self.POS_INI, self.POS_FIM)]
        fases = [(0.0, (1, 1, 1)), (7.6, (1, 1, 0)), (15.0, (0, 1, 1)), (22.4, (1, 0, 1)), (29.8, (1, 1, 1)),
                 (33.4, (0, 0, 0)), (35.2, (1, 1, 1)), (36.8, (1, 1, 0))]
        lig = [0.0, 0.0, 0.0]
        for i in range(3):
            v = 0.0
            for (ta, fa), (tb, fb) in zip(fases, fases[1:] + [(999, fases[-1][1])]):
                if ta <= t < tb:
                    prev = fases[fases.index((ta, fa)) - 1][1][i] if ta > 0 else fa[i]
                    v = lerp(prev, fa[i], min(1.0, (t - ta) / .4))
            lig[i] = v
        return pos, lig

    def venn(self, tela, pos, lig, t):
        x0, y0, x1, y1 = 0, 0, 296, 176
        yy, xx = np.mgrid[y0:y1, x0:x1]
        bay = LG.BAYER8[yy % 8, xx % 8]
        bits = []
        halo = np.zeros(xx.shape, np.int16) - 1
        for k, (cx, cy) in enumerate(pos):
            d = np.hypot(xx - cx, yy - cy)
            on = (d <= self.RAIO) & (bay < lig[k])
            bits.append(on)
            hm = (d > self.RAIO) & (d <= self.RAIO + 4) & ((xx + yy) % 2 == 0) & (bay < lig[k])
            halo[hm & (halo < 0)] = k
        for k, (cx, cy) in enumerate(pos):                    # luz apagada: só a marca escura na parede
            d = np.hypot(xx - cx, yy - cy)
            borda = (np.abs(d - self.RAIO) < .8) & ~bits[k]
            tela.buf[y0:y1, x0:x1][borda] = SUB[k, 0]
        r, g, b = bits
        comb = np.array([FUNDO, SUB[2, 3], SUB[1, 3], CIA_P, SUB[0, 3], MAG_P, AMA_P, BRANCO], np.uint8)
        code = r.astype(int) * 4 + g.astype(int) * 2 + b.astype(int)
        sub = tela.buf[y0:y1, x0:x1]
        dentro = code > 0
        sub[dentro] = comb[code[dentro]]
        hk = (halo >= 0) & ~dentro
        sub[hk] = SUB[halo[hk], 1]

    def lampadas(self, tela, pos, lig, t, facho=False):
        for k, (cx, cy) in enumerate(pos):
            on = lig[k] > .5
            lx = cx - 5
            # facho da lâmpada até a parede (desenhado antes dos círculos)
            if on and facho:
                topo = int(cy + self.RAIO * .7)
                for yb in range(topo, 180):
                    j = 180 - yb
                    w = 6 + j * .55
                    for xx in range(int(cx - w / 2), int(cx + w / 2)):
                        if (xx + yb + int(t * 6)) % 3 == 0: tela.px(xx, yb, SUB[k, 1])
            if facho: continue
            tela.ret(lx - 1, 180, 12, 20, PRETO)
            tela.ret(lx, 181, 10, 18, SUB[k, 3] if on else SUB[k, 0])
            if on: tela.ret(lx + 2, 183, 2, 14, BRANCO)
            tela.ret(lx - 3, 199, 16, 4, ACO1); tela.ret(lx - 3, 199, 16, 1, ACO3)

    def receita(self, tela, y, cores, igual, nome, cor_nome):
        x = PX0
        for j, c in enumerate(cores):
            D.amostra(tela, x, y + 3, c, 9)
            x += 12
            if j < len(cores) - 1:
                tela.texto('+', x, y + 4, BRANCO, tam=9, contorno=PRETO); x += 9
        tela.texto('=', x + 1, y + 4, BRANCO, tam=9, contorno=PRETO)
        D.amostra(tela, x + 11, y + 1, igual, 13)
        tela.texto(nome, x + 30, y + 1, cor_nome, tam=17, contorno=PRETO)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t, grade=False)
        dither(tela, 0, 0, 296, 176, FUNDO, FUNDO2)
        tela.ret(0, 176, 296, PALCO_H - 176, FUNDO)
        tela.ret(0, 176, 296, 1, TRACO)
        pos, lig = self.estado(t)
        if t < 37.0:
            self.lampadas(tela, pos, lig, t, facho=True)
            self.venn(tela, pos, lig, t)
            self.lampadas(tela, pos, lig, t)
        else:
            # de perto -> de longe: uma telinha de pixels amarelos encolhendo até o olho juntar
            u = suave((t - 37.0) / 3.5)
            c = zlog(30, 3, u)
            nx, ny = 7, 5
            cx, cy = 110, 92
            x0, y0 = cx - nx * c / 2, cy - ny * c / 2
            tela.ret(x0 - 2, y0 - 2, nx * c + 4, ny * c + 4, NEGRO)
            lw = max(1, int(c / 3) - (1 if c >= 9 else 0))
            for i in range(nx):
                for j in range(ny):
                    for k, n in enumerate((3, 3, 0)):
                        tela.ret(int(x0 + i * c + k * c / 3), int(y0 + j * c), lw, max(1, int(c) - (1 if c >= 6 else 0)), SUB[k, n])
            D.centro_preso(tela, 'DE PERTO' if c > 10 else 'DE LONGE', cx, 20, ACO3, tam=17)
            if c <= 6:
                lado = int(nx * c)
                D.amostra(tela, 190, cy - lado // 2, AMA_P, lado)
                tela.texto('O OLHO VÊ', 190, cy + lado // 2 + 8, BRANCO, tam=9, contorno=PRETO)
                tela.texto('AMARELO', 190, cy + lado // 2 + 19, AMA_P, tam=9, contorno=PRETO)
                tela.texto('=', 160, cy - 6, BRANCO, tam=17, contorno=PRETO)
        if not VERTICAL:
            R, G, B = SUB[0, 3], SUB[1, 3], SUB[2, 3]
            linhas = [(7.6, [R, G], AMA_P, 'AMARELO', AMA_P), (15.0, [G, B], CIA_P, 'CIANO', CIA_P),
                      (22.4, [R, B], MAG_P, 'MAGENTA', MAG_P), (29.8, [R, G, B], BRANCO, 'BRANCO', BRANCO)]
            tela.texto('SOMANDO LUZ', PX0, 8, ACO3, tam=9, contorno=PRETO)
            for j, (ta, cs, ig, nome, cn) in enumerate(linhas):
                if t >= ta: self.receita(tela, 24 + j * 30, cs, ig, nome, cn)
            if t >= 33.4:
                tela.texto('NADA ACESO =', PX0, 152, ACO3, tam=9, contorno=PRETO)
                D.amostra(tela, PX0 + 78, 149, NEGRO, 13)
                tela.texto('PRETO', PX0 + 98, 150, ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        for ta, ms in ((7.6, (72, 76)), (15.0, (76, 79)), (22.4, (72, 79)), (29.8, (72, 76, 79)), (35.2, (72, 76, 79))):
            for k, m in enumerate(ms):
                fx.put(fx.sino(m), self.t0 + ta + k * .05, .25, -.3 + .3 * k)


# ============================================================ 4b a receita de cada pixel
def lupa(tela, lev, ax, ay, cx, cy, R, ui, vj, zz=20.0):
    """Lupa redonda em (cx, cy) mostrando os subpixels em volta do ponto (ui, vj)
    da imagem, ligada por um fio ao ponto (ax, ay) da tela do celular."""
    tela.linha(ax + 2, ay, cx - R * .7, cy - R * .7, ACO3)
    x0, y0, x1, y1 = int(cx - R), int(cy - R), int(cx + R + 1), int(cy + R + 1)
    guarda = tela.buf[y0:y1, x0:x1].copy()
    ox, oy = cx - (ui + .5) * zz, cy - (vj + .5) * zz
    D.render_niveis(tela, lev, D.normal_de(lev), ox, oy, zz, (x0, y0, x1, y1))
    r = zz / 2
    tela.ret_vazado(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, AMARELO)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    fora = np.hypot(xx - cx, yy - cy) > R
    sub = tela.buf[y0:y1, x0:x1]
    sub[fora] = guarda[fora]
    tela.anel(cx, cy, R, PRETO, 2.2)
    tela.anel(cx, cy, R, ACO3, .8)
    hx, hy = cx + R * .72, cy + R * .72
    for k in range(6):
        tela.ret(hx + k * 2, hy + k * 2, 4, 4, ACO1)


class Foto(Cena):
    SX, SY, Z = 50, 24, 2.0
    ROTA = [(0.0, (4, 71)), (1.8, (12, 74)), (3.6, (30, 76)), (5.4, (21, 42)), (7.8, (6, 12)),
            (15.2, (9, 31)), (22.6, (18, 59)), (28.6, SOL)]

    def ponto(self, t):
        rota = self.ROTA
        for (ta, pa), (tb, pb) in zip(rota, rota[1:] + [(999, rota[-1][1])]):
            if ta <= t < tb:
                if tb == 999: return pa
                anterior = rota[rota.index((ta, pa)) - 1][1] if ta > 0 else pa
                u = suave((t - ta) / .7)
                return (round(lerp(anterior[0], pa[0], u)), round(lerp(anterior[1], pa[1], u)))
        return rota[-1][1]

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        sx, sy, z = self.SX, self.SY, self.Z
        mesa(tela, sx, sy, z)
        lev = D.paisagem(t)
        D.celular(tela, lev, sx, sy, z, t)
        ui, vj = self.ponto(t)
        ax, ay = sx + (ui + .5) * z, sy + (vj + .5) * z
        tela.ret_vazado(ax - 3, ay - 3, 7, 7, AMARELO)
        lupa(tela, lev, ax, ay, 214, 100, 52, ui, vj)
        n = [int(x) for x in lev[vj, ui]]
        if VERTICAL: return
        tela.texto('ESTE PIXEL', PX0, 8, ACO3, tam=9, contorno=PRETO)
        for k in range(3):
            y = 24 + k * 30
            tela.texto(D.NOME_CANAL[k], PX0, y, SUB[k, 3], tam=9, contorno=PRETO)
            tela.ret(PX0, y + 11, 102, 8, PRETO); tela.ret(PX0 + 1, y + 12, 100, 6, FUNDO2)
            tela.ret(PX0 + 1, y + 12, int(100 * n[k] / 3), 6, SUB[k, 3])
            tela.texto(str(n[k] * 85), PX0 + 110, y + 11, BRANCO, tam=9, contorno=PRETO)
        tela.texto('RESULTADO', PX0, 122, ACO3, tam=9, contorno=PRETO)
        D.amostra(tela, PX0, 136, MEDIA[n[0], n[1], n[2]], 16)
        tela.texto(D.nome_cor(*n), PX0 + 24, 138, BRANCO, tam=17, contorno=PRETO)
        tela.texto('(0 A 255; NO DESENHO,', PX0, 172, ACO2, tam=9, contorno=PRETO)
        tela.texto('4 DEGRAUS: 0, 85, 170, 255)', PX0, 183, ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        for ta, _ in self.ROTA[1:]:
            fx.put(fx.blip(74, .06), self.t0 + ta, .12)


# ============================================================ 5 lcd (as camadas)
class Lcd(Cena):
    SLOT0, SLOT = 6.0, 6.0
    DESC = dict(luz='A LUZ VEM DAQUI', pol1='SÓ PASSA LUZ EM PÉ', cris='MOLÉCULAS EM ESPIRAL',
                pol2='VIRADO 90 GRAUS', filt='R, G OU B')
    LISTA = dict(luz='LUZ DE FUNDO', pol1='POLARIZADOR', cris='CRISTAL', pol2='POLARIZADOR 2', filt='FILTRO DE COR')

    def pecas(self, t):
        vis, dz = [], {}
        for k, nome in enumerate(D.ORDEM_LCD):
            tk = self.SLOT0 + k * self.SLOT
            if t >= tk:
                vis.append(nome)
                u = (t - tk) / .55
                if u < 1:
                    dz[nome] = -200 * (1 - u) ** 2 if u < .75 else -5 * math.sin((u - .75) / .25 * math.pi)
        return vis, dz

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 6.0:
            # o pixel de frente gira de lado e vira o corte
            u = suave((t - 4.0) / 2.0)
            L = 120
            w = int(L * (1 - u)) + 2
            x = int(lerp(100, 22, u))
            tela.ret(x - 2, 30 - 2, w + 4, 152 + 4, NEGRO)
            lw = max(1, (w - 8) // 3)
            for k in range(3):
                tela.ret(x + 2 + k * (lw + 2), 30, lw, 152, SUB[k, 3 if k < 2 else 0])
            if t < 4.0:
                D.centro_preso(tela, 'O PIXEL DO SOL, DE FRENTE', x + w / 2, 12, ACO3)
            vis, dz = [], {}
        else:
            vis, dz = self.pecas(t)
            saida = D.desenhar_lcd(tela, t, [3, 3, 3], pecas=vis, desloc=dz)
            if 'luz' in vis and not dz.get('luz'):
                D.janela_saida(tela, saida, filtro='filt' in vis and not dz.get('filt'))
                if 'filt' in vis and not dz.get('filt') and not VERTICAL:
                    D.pixel_de_longe(tela, saida, t=t)
            if not VERTICAL: D.centro_preso(tela, 'VOCÊ OLHA DAQUI', 169, 192, ACO3, xmax=296)
        if VERTICAL: return
        k_atual = None
        for k, nome in enumerate(D.ORDEM_LCD):
            if t >= self.SLOT0 + k * self.SLOT: k_atual = k
        for k, nome in enumerate(D.ORDEM_LCD):
            tk = self.SLOT0 + k * self.SLOT
            if t < tk: continue
            y = 10 + k * 28
            atual = k == k_atual
            tela.texto(self.LISTA[nome], PX0, y, AMARELO if atual else ACO2, tam=17, contorno=PRETO)
            if atual:
                tela.texto(self.DESC[nome], PX0, y + 17, BRANCO, tam=9, contorno=PRETO)
                if t - tk > .55:
                    a, b = D.LCD[nome]
                    ax, ay = (a + b) / 2, D.SLAB_Y0 + 6
                    tela.linha(PX0 - 4, y + 7, ax, ay, AMARELO)
                    tela.disco(ax, ay, 1.6, AMARELO)
                    tela.ret(PX0 - 6, y + 6, 3, 3, AMARELO)
        if t >= 12.6:                                          # chave dos símbolos da luz
            y = 154
            tela.ret(PX0 + 1, y + 4, 3, 1, BRANCO); tela.ret(PX0 + 2, y + 3, 1, 3, BRANCO)
            tela.texto('LUZ COMUM', PX0 + 10, y + 1, ACO3, tam=9, contorno=PRETO)
            tela.ret(PX0 + 2, y + 13, 1, 5, BRANCO)
            tela.texto('VIBRA EM PÉ', PX0 + 10, y + 12, ACO3, tam=9, contorno=PRETO)
            if t >= 18.6:
                tela.ret(PX0 + 1, y + 26, 2, 2, BRANCO)
                tela.texto('VIBRA PARA DENTRO', PX0 + 10, y + 23, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(5):
            t = self.t0 + self.SLOT0 + k * self.SLOT + .41
            fx.put(fx.clique(1800, .05), t, .4)
            fx.put(fx.explosao(.5), t, .2)


# ============================================================ 6 cristal
def cabecalho_lcd(tela):
    itens = [('LUZ', 18, ACO3), ('POL. 1', 41, ACO3), ('CRISTAL', 88, CIANO), ('FILTRO', 132, ACO3),
             ('POL. 2', 147, ACO3)]
    D.cabecalhos(tela, itens)


class Cristal(Cena):
    def niveis(self, t):
        b = lerp(3, 0, suave((t - 15.2) / 1.0))
        g = 3.0
        if t >= 30.0: g = lerp(3, 1.5, suave((t - 30.0) / 1.0))
        if t >= 36.0: g = lerp(1.5, 3, suave((t - 36.0) / 1.0))
        return [3.0, g, b]

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        nv = self.niveis(t)
        saida = D.desenhar_lcd(tela, t, nv)
        D.janela_saida(tela, saida)
        cabecalho_lcd(tela)
        # faixa em destaque quando muda
        foco = 2 if 15.2 <= t < 30.0 else (1 if t >= 30.0 else None)
        if foco is not None and int(t * 2.5) % 2 == 0:
            ly, lh = D.LANES[foco]
            tela.ret_vazado(D.LCD['cris'][0] - 2, ly - 3, D.LCD['cris'][1] - D.LCD['cris'][0] + 4, lh + 6, AMARELO)
        if t < 15.2 and int(t * 2.5) % 2 == 0:
            ly, lh = D.LANES[0]
            tela.ret_vazado(D.LCD['cris'][0] - 2, ly - 3, D.LCD['cris'][1] - D.LCD['cris'][0] + 4, lh + 6, AMARELO)
        if VERTICAL: return
        n, cor = D.pixel_de_longe(tela, saida, t=t)
        for k in range(3):
            y = 10 + k * 40
            tela.texto(D.NOME_CANAL[k], PX0, y, SUB[k, 3], tam=17, contorno=PRETO)
            ten = 1 - nv[k] / 3
            est = 'SEM TENSÃO' if ten < .1 else ('COM TENSÃO' if ten > .9 else 'MEIA TENSÃO')
            tela.texto(est, PX0, y + 19, AMARELO if ten > .1 else ACO3, tam=9, contorno=PRETO)
            tela.ret(PX0 + 84, y + 19, 62, 7, PRETO); tela.ret(PX0 + 85, y + 20, 60, 5, FUNDO2)
            tela.ret(PX0 + 85, y + 20, int(60 * saida[k]), 5, SUB[k, 3])
        tela.texto('O PIXEL FICA', PX0, 136, ACO3, tam=9, contorno=PRETO)
        D.amostra(tela, PX0, 150, cor, 14)
        tela.texto(D.nome_cor(*n), PX0 + 22, 150, BRANCO, tam=17, contorno=PRETO)

    def sons(self, fx):
        for t in (15.2, 30.0, 36.0):
            fx.put(fx.clique(2600, .03), self.t0 + t, .35)
            fx.put(fx.blip(67, .08), self.t0 + t + .05, .12)


# ============================================================ 7 preto do LCD
class Preto(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        nv = [lerp(3, 0, suave(t / 1.2))] * 3
        saida = D.desenhar_lcd(tela, t, nv, vaza=True)
        D.janela_saida(tela, saida, vaza=True, preto=PRETO_LCD)
        cabecalho_lcd(tela)
        # a luz de fundo, sempre ligada: brilho pulsando de leve
        if int(t * 2) % 2 == 0:
            tela.ret_vazado(D.LCD['luz'][0] - 3, D.SLAB_Y0 - 3, D.LCD['luz'][1] - D.LCD['luz'][0] + 6,
                            D.SLAB_Y1 - D.SLAB_Y0 + 6, AMARELO)
        if VERTICAL: return
        n, cor = D.pixel_de_longe(tela, saida, preto=PRETO_LCD, t=t)
        self.painel_titulo(tela, 'TENSÃO', 12)
        self.painel_valor(tela, 'NOS TRÊS', 24)
        self.painel_titulo(tela, 'LUZ DE FUNDO', 52)
        self.painel_valor(tela, 'LIGADA', 64)
        if t >= 8.4:
            self.painel_titulo(tela, 'O PRETO SAI', 96)
            D.amostra(tela, PX0, 110, PRETO_LCD, 16)
            tela.texto('QUASE PRETO', PX0 + 24, 112, ACO3, tam=17, contorno=PRETO)
            tela.texto('UM POUCO DE LUZ VAZA', PX0, 136, ACO3, tam=9, contorno=PRETO)
            tela.texto('PELO CRISTAL', PX0, 147, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.clique(2600, .03), self.t0 + .2, .35)
        fx.put(fx.chiado(6.0, 90, 400), self.t0 + 2.0, .08)


# ============================================================ 8 OLED
def cabecalho_oled(tela):
    D.cabecalhos(tela, [('ORGÂNICA', 70, CIANO), ('ÂNODO', 42, ACO3), ('VIDRO', 114, ACO3), ('CÁTODO', 98, ACO3)])
    D.centro_preso(tela, 'CIRCUITO', 21, 192, ACO3)


class Oled(Cena):
    def niveis(self, t):
        if t < 15.4: return [3.0, 3.0, 0.0]
        if t < 23.2:
            u = suave((t - 15.4) / 1.0); return [3.0, 3.0, 3 * u]
        return [3.0 * (1 - suave((t - 23.6 - k * 1.2) / .6)) for k in range(3)]

    def desenhar(self, tela, t, tg):
        if t >= 38.8:
            return self.noite(tela, t)
        self.fundo(tela, t)
        nv = self.niveis(t)
        saida = D.desenhar_oled(tela, t, [v / 3 for v in nv])
        D.janela_saida(tela, saida, preto=NEGRO)
        cabecalho_oled(tela)
        if VERTICAL: return
        n, cor = D.pixel_de_longe(tela, saida, preto=NEGRO, t=t)
        for k in range(3):
            y = 10 + k * 34
            tela.texto(D.NOME_CANAL[k], PX0, y, SUB[k, 3], tam=17, contorno=PRETO)
            on = nv[k] > .1
            tela.texto('ACESO' if on else 'APAGADO', PX0, y + 19, AMARELO if on else ACO2, tam=9, contorno=PRETO)
            tela.texto('CORRENTE' if on else 'SEM CORRENTE', PX0 + 60, y + 19, ACO3, tam=9, contorno=PRETO)
        if t < 23.2:
            self.painel_titulo(tela, 'LUZ DE FUNDO', 112)
            self.painel_valor(tela, 'NÃO TEM', 124, BRANCO)
        else:
            self.painel_titulo(tela, 'LUZ QUE SAI', 112)
            self.painel_valor(tela, 'ZERO' if sum(nv) < .3 else 'DIMINUINDO', 124, BRANCO)
        tela.texto('O PIXEL FICA', PX0, 154, ACO3, tam=9, contorno=PRETO)
        D.amostra(tela, PX0, 168, cor, 14)
        tela.texto(D.nome_cor(*n) if sum(n) else 'PRETO', PX0 + 22, 168, BRANCO, tam=17, contorno=PRETO)

    def noite(self, tela, t):
        tela.buf[:PALCO_H] = FUNDO
        u = t - 38.8
        lev = D.paisagem(t, noite=True)
        z = 1.5
        for k, (sx, nome, preto) in enumerate(((52, 'LCD', PRETO_LCD), (170, 'OLED', NEGRO))):
            sy = 34
            D.celular(tela, lev, sx, sy, z, t, preto=preto)
            D.centro_preso(tela, nome, sx + IMG_W * z / 2, 10, BRANCO, tam=17)
        if VERTICAL: return
        self.painel_titulo(tela, 'PRETO DO LCD', 20)
        D.amostra(tela, PX0, 34, PRETO_LCD, 16)
        tela.texto('BRILHA UM POUCO', PX0 + 24, 38, ACO3, tam=9, contorno=PRETO)
        self.painel_titulo(tela, 'PRETO DO OLED', 70)
        D.amostra(tela, PX0, 84, NEGRO, 16)
        tela.texto('APAGADO', PX0 + 24, 88, ACO3, tam=9, contorno=PRETO)
        self.painel_titulo(tela, 'NUM QUARTO ESCURO', 130)

    def sons(self, fx):
        fx.put(fx.blip(76, .1), self.t0 + 15.4, .15)
        for k in range(3):
            fx.put(fx.blip(72 - k * 3, .1), self.t0 + 23.6 + k * 1.2, .15)


# ============================================================ 9 resolução
class Resolucao(Cena):
    SX, SY, Z = 74, 24, 2.0

    def linhas(self, t):
        if t < 7.8: return None
        return float(int(2400.0 * min(1.0, (t - 7.8) / 14.6)))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        sx, sy, z = self.SX, self.SY, self.Z
        mesa(tela, sx, sy, z)
        lev = D.paisagem(t)
        r = self.linhas(t)
        D.celular(tela, lev, sx, sy, z, t)
        sw, sh = IMG_W * z, IMG_H * z
        if r is not None and r < 2400:
            yb = sy + sh * r / 2400
            tela.ret(sx, yb, sw, sy + sh - yb, NEGRO)
            for yy in range(int(yb) + 2, int(sy + sh), 3):
                for xx in range(int(sx) + 1, int(sx + sw), 3): tela.px(xx, yy, FUNDO2)
            tela.ret(sx, yb, sw, 1, AMARELO)
            tela.ret(sx, yb - 1, sw, 1, CHAMA0)
        # cotas
        tela.linha(sx, 12, sx + sw - 1, 12, AMARELO)
        tela.ret(sx, 9, 1, 7, AMARELO); tela.ret(sx + sw - 1, 9, 1, 7, AMARELO)
        D.centro_preso(tela, '1.080', sx + sw / 2, 1, AMARELO)
        xl = sx - 14
        tela.linha(xl, sy, xl, sy + sh - 1, AMARELO)
        tela.ret(xl - 3, sy, 7, 1, AMARELO); tela.ret(xl - 3, sy + sh - 1, 7, 1, AMARELO)
        tela.texto('2.400', xl - 4 - tela.largura_texto('2.400', 9), sy + sh / 2 - 4, AMARELO, tam=9, contorno=PRETO)
        # lupa nos subpixels do sol
        if t >= 23.4:
            self.lupa(tela, t, 222, 96, 46)
        if VERTICAL: return
        n = 0 if r is None else r
        self.painel_titulo(tela, 'COLUNAS', 10)
        self.painel_valor(tela, '1.080', 22)
        self.painel_titulo(tela, 'LINHAS', 46)
        self.painel_valor(tela, milhar(n) if r is not None else '2.400', 58, AMARELO)
        self.painel_titulo(tela, 'PIXELS', 82)
        self.painel_valor(tela, milhar(n * 1080) if r is not None else '?', 94, BRANCO)
        if t >= 23.4:
            self.painel_titulo(tela, 'SUBPIXELS (X 3)', 118)
            self.painel_valor(tela, '7.776.000', 130, BRANCO)
            for k in range(3): tela.ret(PX0 + 118 + k * 5, 130, 4, 12, SUB[k, 3])
        tela.texto('NO DESENHO, 1 PONTO', PX0, 178, ACO2, tam=9, contorno=PRETO)
        tela.texto('= 30 X 30 PIXELS', PX0, 189, ACO2, tam=9, contorno=PRETO)

    def lupa(self, tela, t, cx, cy, R):
        sx, sy, z = self.SX, self.SY, self.Z
        u = ease((t - 23.4) / .6)
        R = max(2, R * u)
        alvo = (sx + (SOL[0] + .5) * z, sy + (SOL[1] + .5) * z)
        tela.linha(alvo[0] + 2, alvo[1], cx - R * .7, cy - R * .7, ACO3)
        tela.ret_vazado(alvo[0] - 2, alvo[1] - 2, 5, 5, AMARELO)
        x0, y0, x1, y1 = int(cx - R), int(cy - R), int(cx + R + 1), int(cy + R + 1)
        guarda = tela.buf[y0:y1, x0:x1].copy()
        zz = 20.0
        lev = D.paisagem(t)
        ox = cx - (SOL[0] + .5 + math.sin(t * .4) * 1.2) * zz
        oy = cy - (SOL[1] + .5) * zz
        D.render_niveis(tela, lev, D.normal_de(lev), ox, oy, zz, (x0, y0, x1, y1))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        fora = np.hypot(xx - cx, yy - cy) > R
        sub = tela.buf[y0:y1, x0:x1]
        sub[fora] = guarda[fora]
        tela.anel(cx, cy, R, PRETO, 2.2)
        tela.anel(cx, cy, R, ACO3, .8)
        ax, ay = cx + R * .72, cy + R * .72
        for k in range(6):
            tela.ret(ax + k * 2, ay + k * 2, 4, 4, ACO1)

    def sons(self, fx):
        for k in range(int(14.6 / .3)):
            fx.put(fx.clique(5200, .01), self.t0 + 7.8 + k * .3, .06)
        fx.put(fx.sino(84), self.t0 + 22.4, .3)
        fx.put(fx.sino(79), self.t0 + 23.4, .25)


# ============================================================ 10 densidade
class Densidade(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        sx, sy, z = 22, 56, 1.0
        lev = D.paisagem(t)
        D.celular(tela, lev, sx, sy, z, t)
        sw, sh = IMG_W * z, IMG_H * z
        # diagonal
        n = int(min(1.0, t / 2.0) * 60)
        for i in range(n):
            u = i / 60
            tela.px(sx + sw * u, sy + sh * (1 - u), AMARELO)
        D.centro_preso(tela, 'DIAGONAL', sx + sw / 2, sy + sh + 12, ACO3)
        D.centro_preso(tela, '6,5 POL.', sx + sw / 2, sy + sh + 23, AMARELO)
        # a lupa: 1 milímetro da tela
        cx0, cy0 = sx + sw * .5, sy + sh * .4
        tela.anel(cx0, cy0, 4, AMARELO, .6)
        bx0, by0, bx1, by1 = 86, 36, 292, 168
        u = ease((t - 1.0) / 1.0)
        if u > 0:
            tela.linha(cx0 + 3, cy0 - 3, lerp(cx0, bx0, u), lerp(cy0, by0, u), ACO3)
            tela.linha(cx0 + 3, cy0 + 3, lerp(cx0, bx0, u), lerp(cy0, by1, u), ACO3)
        if u >= 1:
            painel(tela, bx0, by0, bx1 - bx0, by1 - by0, borda=ACO2, fundo=NEGRO)
            zz = 11.0
            xa = 100
            fila = lev[20:25, 10:26]
            D.render_niveis(tela, fila, D.normal_de(fila), xa, 50, zz, (xa, 50, xa + 16 * zz, 50 + 5 * zz))
            # régua
            ry = 112
            tela.ret(bx0 + 6, ry, bx1 - bx0 - 12, 26, CERAMICA)
            tela.ret(bx0 + 6, ry, bx1 - bx0 - 12, 1, BRANCO)
            tela.ret(bx0 + 6, ry + 25, bx1 - bx0 - 12, 1, ACO2)
            x1mm = xa + 15.94 * zz
            for k in range(11):
                x = xa + (x1mm - xa) * k / 10
                tela.ret(x, ry, 1, 12 if k in (0, 5, 10) else 6, PRETO)
            tela.texto('0', xa - 2, ry + 15, PRETO, tam=9)
            tela.texto('1 MM', x1mm - 22, ry + 15, PRETO, tam=9)
            tela.texto('0,5', xa + (x1mm - xa) / 2 - 8, ry + 15, PRETO, tam=9)
            # contando os pixels
            if t >= 15.8:
                k = min(16, int((t - 15.8) / .35) + 1)
                tela.ret_vazado(xa + (k - 1) * zz - 1, 49, zz + 2, 5 * zz + 2, AMARELO)
                tela.texto(str(k), xa + (k - .5) * zz - (3 if k < 10 else 6), 40, AMARELO, tam=9, contorno=PRETO)
                for j in range(k - 1):
                    tela.ret(xa + j * zz + 4, 46, 3, 2, AMARELO)
            tela.texto('1 MILÍMETRO DA TELA', bx0 + 8, by1 - 18, ACO3, tam=9, contorno=PRETO)
        if VERTICAL: return
        self.painel_titulo(tela, 'DIAGONAL', 10)
        self.painel_valor(tela, '2.632 PIXELS', 22, BRANCO)
        self.painel_titulo(tela, 'TAMANHO (EXEMPLO)', 48)
        self.painel_valor(tela, '6,5 POLEG.', 60, BRANCO)
        if t >= 7.8:
            self.painel_titulo(tela, 'PIXELS POR POLEGADA', 90)
            self.painel_valor(tela, '405', 102)
            tela.texto('2.632 / 6,5', PX0 + 44, 106, ACO3, tam=9, contorno=PRETO)
        if t >= 15.8:
            self.painel_titulo(tela, 'EM 1 MILÍMETRO', 132)
            self.painel_valor(tela, 'UNS 16', 144)
            tela.texto('405 / 25,4 MM', PX0, 166, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(16):
            fx.put(fx.blip(60 + k, .04), self.t0 + 15.8 + k * .35, .08)


# ============================================================ 11 Hz
class Hz(Cena):
    LENTO = 10.0
    VOLTAS = 3.0                         # voltas por segundo de verdade (a bolinha)
    P = [(46, 42, 60), (132, 42, 120)]   # (sx, sy, Hz)

    def bola(self, tela, sx, sy, z, hz, t):
        sw, sh = IMG_W * z, IMG_H * z
        tr = t / self.LENTO
        q = math.floor(tr * hz)
        cx, cy, R = sx + sw / 2, sy + sh * .42, 21
        dither(tela, sx, sy, sw, sh, FUNDO2, FUNDO)
        tela.ret(sx, sy, sw, 6, NEGRO)
        n = int(round(hz / self.VOLTAS))
        for j in range(n):                                     # onde a tela já desenhou a bola
            a = 2 * math.pi * self.VOLTAS * (q - j) / hz
            tela.ret(cx + math.sin(a) * R - 1, cy - math.cos(a) * R - 1, 2, 2, ACO1 if j > n // 2 else ACO2)
        a = 2 * math.pi * self.VOLTAS * q / hz
        bx, by = cx + math.sin(a) * R, cy - math.cos(a) * R
        tela.disco(bx, by, 5.5, PRETO); tela.disco(bx, by, 4.5, AMARELO); tela.px(bx - 2, by - 2, BRANCO)
        tela.texto(f"QUADRO {int(q) + 1}", sx + sw / 2, sy + sh - 30, BRANCO, tam=9, centro=True, contorno=PRETO)
        tela.texto(f"{n} POR VOLTA", sx + sw / 2, sy + sh - 18, ACO3, tam=9, centro=True, contorno=PRETO)
        return q

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        if t < 29.8:
            z = 1.8
            for sx, sy, hz in self.P:
                sw, sh = IMG_W * z, IMG_H * z
                D.celular_corpo(tela, sx, sy, sw, sh, 2.2 * z)
                self.bola(tela, sx, sy, z, hz, t)
                D.celular_camera(tela, sx, sy, sw, sh, 2.2 * z)
                D.centro_preso(tela, f"{hz} HZ", sx + sw / 2, 14, AMARELO if hz == 120 else BRANCO, tam=17, xmax=296)
            if VERTICAL: return
            self.painel_titulo(tela, 'CÂMERA LENTA', 10)
            self.painel_valor(tela, '10X', 22, CIANO)
            self.painel_titulo(tela, 'TEMPO DE VERDADE', 50)
            self.painel_valor(tela, dec(t / self.LENTO, 2) + ' S', 62, BRANCO)
            if t >= 22.6:
                self.painel_titulo(tela, 'CADA QUADRO DURA', 96)
                tela.texto('60 HZ:', PX0, 112, BRANCO, tam=9, contorno=PRETO)
                tela.texto('16,7 MS', PX0 + 48, 108, AMARELO, tam=17, contorno=PRETO)
                tela.texto('120 HZ:', PX0, 136, BRANCO, tam=9, contorno=PRETO)
                tela.texto('8,3 MS', PX0 + 48, 132, AMARELO, tam=17, contorno=PRETO)
                tela.texto('1 MS = 1 MILÉSIMO DE S', PX0, 160, ACO3, tam=9, contorno=PRETO)
        else:
            self.contagem(tela, t)

    def contagem(self, tela, t):
        z = 2.0
        sx, sy = 74, 24
        u = t - 29.8
        rolar = 0
        if t >= 37.4:
            parado = t < 40.6
            rolar = 0 if parado else int((t - 40.6) * 9)
        lev = D.paisagem(t)
        if rolar: lev[3:] = np.roll(lev[3:], -rolar, axis=0)
        mesa(tela, sx, sy, z)
        D.celular(tela, lev, sx, sy, z, t)
        sw, sh = IMG_W * z, IMG_H * z
        q = min(120, int(u / 6.0 * 120)) if t < 37.4 else 120
        if t < 36.0:                                           # cada quadro novo: um clarão de varredura
            f = (u / 6.0 * 120) % 1.0
            yb = sy + sh * f
            tela.ret(sx, yb, sw, 1, BRANCO)
        if VERTICAL: return
        if t < 37.4:
            self.painel_titulo(tela, '1 SEGUNDO, EM CÂMERA LENTA', 10)
            self.painel_titulo(tela, 'QUADROS', 34)
            self.painel_valor(tela, f"{q} / 120", 46, BRANCO)
            self.painel_titulo(tela, 'PIXELS DESENHADOS', 78)
            self.painel_valor(tela, milhar(q * 2592000), 90)
            tela.texto('2.592.000 POR QUADRO', PX0, 112, ACO3, tam=9, contorno=PRETO)
        else:
            parado = t < 40.6
            self.painel_titulo(tela, 'IMAGEM', 10)
            self.painel_valor(tela, 'PARADA' if parado else 'ROLANDO', 22, BRANCO)
            self.painel_titulo(tela, 'TAXA DA TELA', 54)
            alvo = .35 if parado else 1.0
            nivel = alvo if t < 37.9 else alvo
            if parado: nivel = lerp(1.0, .35, suave((t - 37.4) / 1.2))
            else: nivel = lerp(.35, 1.0, suave((t - 40.6) / .6))
            tela.ret(PX0, 70, 150, 12, PRETO); tela.ret(PX0 + 1, 71, 148, 10, FUNDO2)
            tela.ret(PX0 + 1, 71, int(148 * nivel), 10, VERDE)
            tela.texto('MENOS', PX0, 86, ACO3, tam=9, contorno=PRETO)
            tela.texto('MAIS', PX0 + 150 - 24, 86, ACO3, tam=9, contorno=PRETO)
            tela.texto('O CELULAR DECIDE', PX0, 110, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for sx, sy, hz in self.P:
            dt = self.LENTO / hz
            k = 0
            while k * dt < 29.6:
                fx.put(fx.clique(3000 if hz == 60 else 4800, .012), self.t0 + k * dt, .10, -.5 if hz == 60 else .5)
                k += 1
        for k in range(30):
            fx.put(fx.clique(5200, .01), self.t0 + 29.8 + k * .2, .05)
        fx.put(fx.sino(84), self.t0 + 35.8, .3)


# ============================================================ 12 este vídeo
class Meta(Cena):
    ALVO = (250, 60)                    # o ponto do sol dentro do quadro pequeno

    def preparar(self):
        self.mini = PX.Tela(W, H, paleta=LG.PAL)

    def quadro_mini(self, t):
        m = self.mini
        m.buf[:] = FUNDO
        for x in range(0, W, 24): m.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): m.ret(0, y, W, 1, FUNDO2)
        mesa(m, 200, 24, 2.0)
        D.celular(m, D.paisagem(t), 200, 24, 2.0, t)
        m.ret(0, PALCO_H + 2, W, H - PALCO_H - 2, PRETO)
        m.texto('ESTE VÍDEO TAMBÉM É FEITO DE PIXELS', W // 2, 230, BRANCO, tam=17, centro=True, contorno=PRETO)
        return m.buf

    def camera(self, t):
        marcos = [(7.8, .5), (14.0, 8.0), (15.2, 8.0), (20.0, 20.0), (22.6, 20.0), (28.0, 48.0)]
        z = marcos[0][1] if t < marcos[0][0] else marcos[-1][1]
        for (ta, za), (tb, zb) in zip(marcos, marcos[1:]):
            if ta <= t < tb: z = zlog(za, zb, suave((t - ta) / (tb - ta)))
        p = math.log(z / .5) / math.log(96)
        x0, y0 = 28, 34
        a0 = (x0 + (self.ALVO[0] + .5) * .5, y0 + (self.ALVO[1] + .5) * .5)
        ax, ay = lerp(a0[0], 148, min(1, p * 1.5)), lerp(a0[1], 104, min(1, p * 1.5))
        return z, ax - (self.ALVO[0] + .5) * z, ay - (self.ALVO[1] + .5) * z

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        buf = self.quadro_mini(t)
        z, ox, oy = self.camera(t)
        lev = D.NIVEIS_DE[buf]
        if z < .62:
            tela.ret(ox - 4, oy - 4, W * z + 8, H * z + 8, PRETO)
            tela.ret(ox - 3, oy - 3, W * z + 6, H * z + 6, ACO1)
            D.centro_preso(tela, 'ESTE VÍDEO', ox + W * z / 2, oy - 18, AMARELO, tam=17)
        D.render_niveis(tela, lev, buf, ox, oy, z, CLIP, div=4)
        cx, cy = ox + (self.ALVO[0] + .5) * z, oy + (self.ALVO[1] + .5) * z
        if z >= 6:
            # grade entre os pixels do desenho e foco no pixel do sol
            for i in range(int(-ox // z), int((296 - ox) // z) + 2):
                tela.ret(ox + i * z, 0, 1, PALCO_H, NEGRO)
            for j in range(int(-oy // z), int((PALCO_H - oy) // z) + 2):
                tela.ret(0, oy + j * z, 296, 1, NEGRO)
            D.apagar_fora(tela, cx - z / 2, cy - z / 2, cx + z / 2, cy + z / 2, CLIP)
        if 7.8 <= t and z >= 6:
            r = z / 2
            tela.ret_vazado(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, AMARELO)
            if not VERTICAL:
                D.rotulo(tela, '1 PIXEL DO DESENHO', 150, 14 if cy - r > 30 else 190, cx + r * .6, cy - r - 1 if cy - r > 30 else cy + r + 1, AMARELO)
        if z / 4 >= 3 and not VERTICAL:
            D.rotulo(tela, '4 X 4 PIXELS DO VÍDEO', 8, 190, cx - z / 2 + z / 8, cy + z / 2 - z / 8, BRANCO)
        if VERTICAL: return
        if t >= 7.8:
            self.painel_titulo(tela, 'NOSSO DESENHO', 10)
            self.painel_valor(tela, '480 X 270', 22, BRANCO)
            self.painel_valor(tela, '129.600', 40)
        if t >= 15.2:
            self.painel_titulo(tela, 'O VÍDEO (4 X 4)', 70)
            self.painel_valor(tela, '1.920 X 1.080', 82, BRANCO)
            self.painel_valor(tela, '2.073.600', 100)
        if t >= 22.6:
            self.painel_titulo(tela, 'QUADROS POR SEGUNDO', 130)
            self.painel_valor(tela, '30', 142, BRANCO)

    def sons(self, fx):
        for k, t in enumerate((7.8, 12.0, 15.2, 19.0, 22.6, 26.0)):
            fx.put(fx.blip(64 + k * 3, .08), self.t0 + t, .13)


# ============================================================ 13 resumo
class Resumo(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        nomes = [('SUBPIXELS', 'R + G + B'), ('LCD', 'LUZ DE FUNDO'), ('OLED', 'LUZ PRÓPRIA'),
                 ('PIXELS', '2.592.000'), ('QUADROS', '120 POR SEGUNDO')]
        for k, (a, b) in enumerate(nomes):
            tk = .5 + k * 1.5
            if t < tk: continue
            uu = ease((t - tk) / .3)
            x = 8 + k * 94
            y = 28 + int((1 - uu) * 20)
            painel(tela, x, y, 88, 140, borda=AMARELO if int((t - tk) * 4) < 2 else TRACO)
            cx, cy = x + 44, y + 58
            if k == 0:
                for j in range(3):
                    tela.ret(cx - 22 + j * 15, cy - 26, 13, 52, SUB[j, 3 if (int(t * 1.5) + j) % 4 else 1])
            elif k == 1:
                for j, (c1, c2) in enumerate(((BRANCO, ACO4), (ACO1, ACO3), (FUNDO3, CIANO), (ACO1, ACO3), (SUB[0, 2], SUB[0, 3]))):
                    dither(tela, x + 10 + j * 15, cy - 30, 8, 60, c1, c2)
                ph = (t * 30) % 70
                tela.ret(x + 10 + ph, cy, 2, 2, BRANCO if ph < 60 else SUB[0, 3])
            elif k == 2:
                for j in range(3):
                    on = (int(t * 1.2) + j) % 3 != 0
                    tela.ret(cx - 22 + j * 15, cy - 26, 13, 52, SUB[j, 3] if on else NEGRO)
                    if on:
                        ph = (t * 20 + j * 7) % 20
                        tela.ret(cx - 17 + j * 15, cy - 30 - ph, 2, 2, SUB[j, 3])
            elif k == 3:
                D.celular(tela, D.paisagem(t), cx - 18, cy - 46, 1.0, t)
            else:
                a_ = t * 2 * math.pi * .6
                for j in range(12):
                    b_ = a_ - j * .5
                    tela.ret(cx + math.sin(b_) * 22, cy - math.cos(b_) * 22, 2, 2, ACO2 if j else AMARELO)
                tela.disco(cx + math.sin(a_) * 22, cy - math.cos(a_) * 22, 4, AMARELO)
            tela.texto(a, cx, y + 112, BRANCO, tam=9, centro=True, contorno=PRETO)
            tela.texto(b, cx, y + 124, AMARELO, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for k, m in enumerate((72, 74, 76, 79, 84)):
            fx.put(fx.blip(m, .12), self.t0 + .5 + k * 1.5, .25)


# ============================================================ 14 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS FEITO DE PIXELS'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            self.fundo(tela, t)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            mesa(tela, W // 2 - 27, 70, 1.5, larg=W)
            D.celular(tela, D.paisagem(t), W // 2 - 27, 70, 1.5, t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, zoom=Zoom, subpixel=Subpixel, cores=Cores, foto=Foto, lcd=Lcd, cristal=Cristal,
             preto=Preto, oled=Oled, resolucao=Resolucao, densidade=Densidade, hz=Hz, meta=Meta, resumo=Resumo,
             fim=Fim)


if __name__ == '__main__':
    import ep04_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        so = sys.argv[3:] or None
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            fr = [float(x) for x in __import__('os').environ.get('FR', '.3,.8').split(',')]
            ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
