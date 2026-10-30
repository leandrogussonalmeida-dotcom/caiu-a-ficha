#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep14 — o desenho: o submarino (de lado, inteiro ou em corte),
o mar com a cor mudando com a fundura, a neve marinha e os medidores.

O submarino é genérico: casco cinza-escuro em charuto, vela (torre) sem número,
sem bandeira e sem marca. Ele é desenhado numa tela própria (sem rotação) e
colado na cena girado pelo ângulo do nariz (`colar`), então a inclinação dos
lemes inclina tudo junto: casco, tanques, água dentro dos tanques.

Coordenadas do submarino: u = 0 no meio do casco, u > 0 para a proa (direita),
v = 0 no eixo do casco, v > 0 para baixo. Na tela, (cx, cy) é o eixo no meio.
Escala vertical do mundo: PXM = 2 px por metro (contador de profundidade).

Peças em corte (submarino de casco simples, como diz a Wikipedia "Submarine
hull": os tanques de lastro principais ficam no casco leve, na proa e na popa):
  tanques de lastro   proa u .30L..43L e popa u -.42L..-.28L, cheios de ar ou água
  casco resistente    o tubo do meio, parede grossa, anéis por dentro
  tanques de ajuste   compensação na frente e atrás + o do meio (profundidade)
  ar comprimido       duas garrafas no teto, com o cano para os dois tanques
  respiros            em cima de cada tanque; válvulas de alagamento embaixo
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
from ep06_desenho import rotulo, fio, seta, forca, bolha, ceu, barra_forca

PXM = 2.0                                     # px por metro (vertical do mundo)
B4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16
VAZIO = 255                                   # "transparente" na tela própria do submarino

# fundura (m) -> cor do mar: claro perto da superfície, quase preto lá embaixo
RAMPA = np.array([MISTURA, FUNDO3, FUNDO2, FUNDO, PRETO], np.uint8)
PARADAS = [0.0, 16.0, 70.0, 190.0, 420.0]
CASCO = np.array([ACO3, ACO2, ACO1, ACO0, TRACO], np.uint8)


# ================================================================ mar
def mar(tela, cam_m, t, raios=True, x0=0, x1=W):
    """Pinta o mar visto de lado. `cam_m` = fundura (m) da linha y=0 da tela
    (negativa = a superfície aparece). Devolve o y da superfície ou None."""
    ys = np.arange(PALCO_H)
    m = cam_m + ys / PXM
    ysurf = None
    if cam_m < 0:
        ysurf = int(round(-cam_m * PXM))
        if ysurf > 0:
            ceu(tela, t, y1=min(PALCO_H, ysurf + 2))
    yy, xx = np.mgrid[0:PALCO_H, x0:x1]
    lev = np.interp(m, PARADAS, np.arange(len(PARADAS)))[yy]
    if raios:
        forca_r = np.clip(1 - m / 55.0, 0, 1)[yy] * .85
        faixa = ((xx + yy * .45 + t * 5.0) % 47) < 8
        faixa2 = ((xx * 1.0 - yy * .2 + t * 2.0) % 83) < 5
        lev = lev - (faixa | faixa2) * forca_r
    lev = np.clip(lev, 0, len(PARADAS) - 1.001)
    i = np.floor(lev).astype(int)
    f = lev - i
    idx = i + (B4[yy % 4, xx % 4] < f)
    cor = RAMPA[np.clip(idx, 0, len(RAMPA) - 1)]
    abaixo = (m >= 0)[yy]
    sub = tela.buf[0:PALCO_H, x0:x1]
    sub[abaixo] = cor[abaixo]
    return ysurf


def superficie(tela, ys, t, x0=0, x1=W):
    """Linha d'água com ondinhas que correm (desenhada POR CIMA do casco)."""
    if ys is None or ys < -2 or ys >= PALCO_H: return
    for x in range(max(0, x0), min(W, x1)):
        d = 1 if math.sin(x * .21 - t * 2.6) + .6 * math.sin(x * .07 + t * 1.3) > 1.0 else 0
        tela.px(x, ys - d, MISTURA2)
        if d == 0 and (x * 7 + int(t * 6)) % 23 == 0: tela.px(x, ys, BRANCO)
        tela.px(x, ys + 1, MISTURA)


_RNG = np.random.default_rng(1414)
_NEVE = dict(x=_RNG.random(120) * (W + 20), y=_RNG.random(120) * (PALCO_H + 20),
             p=.55 + .45 * _RNG.random(120), f=_RNG.random(120) * 6.28)


def neve(tela, cam_m, xoff, t, ysurf=None, x0=0, x1=W, n=110):
    """Neve marinha: grãozinhos parados na água. Quando o submarino anda ou
    desce, a câmera vai junto e eles passam: é o que mostra o movimento."""
    larg = x1 - x0
    for k in range(n):
        p = _NEVE['p'][k]
        y = (_NEVE['y'][k] - cam_m * PXM * p) % (PALCO_H + 20) - 10
        x = (_NEVE['x'][k] - xoff * PXM * p + math.sin(t * .5 + _NEVE['f'][k]) * 2) % (larg + 20) - 10 + x0
        if ysurf is not None and y < ysurf + 3: continue
        tela.px(x, y, ACO2 if p > .8 else ACO1)


def bolhas(tela, x, y, t, sobe=40, n=6, vel=1.2, abre=6, r=1.2, ymin=None, seed=0):
    """Bolhas subindo de (x, y): ar saindo pelo respiro, rastro da hélice."""
    for k in range(n):
        u = (t * vel + k / n + seed * .37) % 1.0
        yy = y - u * sobe
        if ymin is not None and yy < ymin: continue
        xx = x + math.sin(u * 9 + k * 1.7 + seed) * abre * u
        bolha(tela, xx, yy, r * (.6 + .6 * u))


def arco(tela, cx, cy, r, a0, a1, cor, passo=None):
    """Arco de círculo (graus, 0 = direita, sentido anti-horário na tela)."""
    passo = passo or max(.6, 40.0 / max(r, 1))
    a = a0
    while a <= a1:
        rad = math.radians(a)
        tela.px(cx + r * math.cos(rad), cy - r * math.sin(rad), cor)
        a += passo


def seta_dir(tela, x, y, dx, dy, comp, cor, esp=2, cabeca=4):
    """Seta que termina em (x, y) apontando na direção (dx, dy)."""
    L = math.hypot(dx, dy) or 1
    dx, dy = dx / L, dy / L
    xa, ya = x - dx * comp, y - dy * comp
    xb, yb = x - dx * cabeca, y - dy * cabeca
    nx, ny = -dy, dx
    linha_grossa(tela, xa, ya, xb, yb, esp + 2, PRETO)
    poligono(tela, [(x + dx * 1.5, y + dy * 1.5), (xb + nx * (cabeca + 1), yb + ny * (cabeca + 1)),
                    (xb - nx * (cabeca + 1), yb - ny * (cabeca + 1))], PRETO)
    linha_grossa(tela, xa, ya, xb, yb, esp, cor)
    poligono(tela, [(x, y), (xb + nx * cabeca, yb + ny * cabeca), (xb - nx * cabeca, yb - ny * cabeca)], cor)


# ================================================================ medidores
def medidor_tanque(tela, x, y, w, h, frac, rot=None, t=0.0, cor=MISTURA):
    """Visor do tanque: água subindo de baixo, ar em cima."""
    frac = max(0.0, min(1.0, frac))
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    dither(tela, x, y, w, h, FUNDO, FUNDO2)
    n = int(round(frac * h))
    if n > 0:
        dither(tela, x, y + h - n, w, n, cor, FUNDO3)
        if n < h:
            d = 1 if math.sin(t * 3) > .4 else 0
            tela.ret(x, y + h - n - d, w, 1, MISTURA2)
    for k in (1, 2, 3):
        tela.ret(x + w - 3, y + h * k // 4, 3, 1, ACO3)
    tela.ret(x - 1, y - 1, 1, h + 2, ACO3); tela.ret(x + w, y - 1, 1, h + 2, ACO1)
    if rot: tela.texto(rot, x + w // 2, y + h + 3, ACO3, tam=9, centro=True, contorno=PRETO)


def manometro(tela, cx, cy, r, val, vmax, rot=None, cor=AMARELO, n_tiques=6):
    """Mostrador de ponteiro (240 graus)."""
    tela.disco(cx, cy, r + 2, PRETO)
    tela.disco(cx, cy, r + 1, ACO3)
    tela.disco(cx, cy, r, FUNDO2)
    dither(tela, cx - r + 2, cy + 2, 2 * r - 4, r - 4, FUNDO2, FUNDO)
    for k in range(n_tiques + 1):
        a = math.radians(210 - 240 * k / n_tiques)
        for s in (r - 3, r - 1):
            tela.px(cx + s * math.cos(a), cy - s * math.sin(a), BRANCO if k % 2 == 0 else ACO3)
    u = max(0.0, min(1.0, val / vmax))
    a = math.radians(210 - 240 * u)
    xp, yp = cx + (r - 3) * math.cos(a), cy - (r - 3) * math.sin(a)
    tela.linha(cx, cy, xp, yp, cor)
    tela.linha(cx + .5, cy, xp + .5, yp, cor)
    tela.disco(cx, cy, 1.6, PRETO); tela.px(cx, cy, ACO4)
    if rot: tela.texto(rot, cx, cy + r + 4, ACO3, tam=9, centro=True, contorno=PRETO)


def regua(tela, x, cam_m, passo=10, rot_cada=50, cor=ACO3, ysurf=None):
    """Régua de fundura na beira da tela, rolando com a câmera."""
    m0 = math.floor(cam_m / passo) * passo
    d = m0
    while True:
        y = (d - cam_m) * PXM
        if y > PALCO_H: break
        if d >= 0 and y >= -2:
            grande = d % rot_cada == 0
            tela.ret(x, int(y), 8 if grande else 4, 1, BRANCO if grande else cor)
            if grande:
                tela.texto(f"{LG_milhar(d)} M", x + 11, int(y) - 3, BRANCO, tam=9, contorno=PRETO)
        d += passo
    tela.ret(x, 0 if ysurf is None else max(0, ysurf), 1, PALCO_H, ACO1)


def LG_milhar(n):
    return f"{int(round(n)):,}".replace(',', '.')


def pesinhos(tela, x, y, n, cor=VERMELHO, por_coluna=10):
    """n pesinhos de 1 kg empilhados (colunas de 10), base em y."""
    n = int(n)
    for k in range(n):
        c, l = divmod(k, por_coluna)
        xx, yy = x + c * 9, y - (l + 1) * 4
        tela.ret(xx - 1, yy - 1, 8, 5, PRETO)
        tela.ret(xx, yy, 6, 3, cor); tela.ret(xx, yy, 6, 1, ROSA if cor == VERMELHO else BRANCO)


def nivel_bolha(tela, cx, cy, w, ang_graus):
    """Nível de bolha: a bolha corre para o lado mais alto."""
    tela.ret(cx - w // 2 - 1, cy - 4, w + 2, 9, PRETO)
    dither(tela, cx - w // 2, cy - 3, w, 7, AGUA1, AGUA0)
    tela.ret(cx - 1, cy - 4, 1, 9, ACO4); tela.ret(cx + 1, cy - 4, 1, 9, ACO4)
    bx = cx - ang_graus * (w / 2 - 5) / 8.0
    bx = max(cx - w // 2 + 4, min(cx + w // 2 - 4, bx))
    tela.disco(bx, cy, 3, MISTURA2); tela.px(bx - 1, cy - 1, BRANCO)


# ================================================================ o submarino
class Sub:
    """Submarino genérico visto de lado, nariz para a direita."""

    def __init__(self, L=200, D=26):
        self.L, self.D = L, D
        self.R = D / 2.0
        self.hs = int(round(D * .55))                     # altura da vela
        self.mx = 14                                      # margem esquerda (hélice)
        self.oy = int(self.R + self.hs + 8)
        self.wc = L + self.mx + 10
        self.hc = int(self.oy + self.R + D * .55 + 8)
        self.ox = self.mx + L / 2.0                       # x do meio do casco na tela própria
        self._base = {}
        self.tela = PX.Tela(self.wc, self.hc, paleta=LG.PAL)
        # alturas em metros (escala do mundo)
        self.Dm = D / PXM
        self.Hm = (D + self.hs) / PXM                     # da quilha ao alto da vela

    # ------------------------------------------------ forma
    def r(self, u):
        L, R = self.L, self.R
        b = .17 * L
        if u >= L / 2: return 0.0
        if u > L / 2 - b:
            q = (u - (L / 2 - b)) / b
            return R * math.sqrt(max(0.0, 1 - q * q)) ** .9
        a = u + L / 2
        s = .32 * L
        if a <= 0: return 0.0
        if a < s:
            return R * (.13 + .87 * math.sin(a / s * math.pi / 2) ** .9)
        return R

    def X(self, u): return self.ox + u
    def Y(self, v): return self.oy + v

    # ------------------------------------------------ base (casco parado) em cache
    def _mascaras(self):
        L, R = self.L, self.R
        hc, wc = self.hc, self.wc
        yy, xx = np.mgrid[0:hc, 0:wc]
        u = xx + .5 - self.ox
        rr = np.array([self.r(x + .5 - self.ox) for x in range(wc)])
        rc = rr[None, :]
        casco = np.abs(yy + .5 - self.oy) <= rc
        casco &= rc > .5
        # vela
        vela = np.zeros_like(casco)
        ub, uf = .07 * L, .23 * L
        top = -R - self.hs
        t2 = PX.Tela(wc, hc, paleta=LG.PAL)
        t2.buf[:] = 0
        poligono(t2, [(self.X(ub), self.Y(-R + 3)), (self.X(ub + 3), self.Y(top + 1)), (self.X(uf - 6), self.Y(top)),
                      (self.X(uf - 1), self.Y(top + 4)), (self.X(uf + 1), self.Y(-R + 3))], 1)
        vela = t2.buf == 1
        # lemes verticais da popa (em cima e embaixo)
        t2.buf[:] = 0
        for s in (-1, 1):
            poligono(t2, [(self.X(-.385 * L), self.Y(s * R * .35)), (self.X(-.455 * L), self.Y(s * R * 1.12)),
                          (self.X(-.495 * L), self.Y(s * R * 1.12)), (self.X(-.485 * L), self.Y(s * R * .05))], 1)
        aletas = t2.buf == 1
        return yy, xx, u, rc, casco, vela, aletas

    def base(self, corte):
        if corte in self._base: return self._base[corte]
        L, R = self.L, self.R
        hc, wc = self.hc, self.wc
        yy, xx, u, rc, casco, vela, aletas = self._mascaras()
        buf = np.full((hc, wc), VAZIO, np.uint8)
        # casco: degradê de cima (claro) para baixo (escuro) com xadrez
        v = (yy + .5 - (self.oy - rc)) / np.maximum(1, 2 * rc)
        lev = np.clip(v * 4.2 - .2, 0, 4)
        i = np.floor(lev).astype(int); f = lev - i
        idx = np.clip(i + (B4[yy % 4, xx % 4] < f), 0, 4)
        buf[casco] = CASCO[idx][casco]
        # vela e aletas
        top = self.oy - R - self.hs
        vv = np.clip((yy - top) / max(1, self.hs + 3), 0, 1)
        lev2 = np.clip(vv * 2.6 + .3, 0, 4)
        i2 = np.floor(lev2).astype(int); f2 = lev2 - i2
        idx2 = np.clip(i2 + (B4[yy % 4, xx % 4] < f2), 0, 4)
        buf[vela] = CASCO[idx2][vela]
        al = aletas & ~casco
        buf[al] = np.where((xx + yy) % 2 == 0, ACO1, ACO0)[al]
        tudo = casco | vela | aletas
        # contorno preto
        d = tudo.copy()
        d[1:] |= tudo[:-1]; d[:-1] |= tudo[1:]; d[:, 1:] |= tudo[:, :-1]; d[:, :-1] |= tudo[:, 1:]
        buf[d & ~tudo] = PRETO
        T = self.tela
        T.buf = buf
        # brilho no alto do casco e da vela
        for x in range(wc):
            uu = x + .5 - self.ox
            r = self.r(uu)
            if r > 2 and -.47 * L < uu < .47 * L:
                y = int(round(self.oy - r + .5))
                if not (vela[max(0, y - 1), x]): T.px(x, y, ACO4 if abs(uu) < .3 * L else ACO3)
        T.ret(self.X(.07 * L) + 4, top + 1, int(.16 * L) - 9, 1, ACO4)
        # mastros (genéricos) em cima da vela
        xm = int(self.X(.17 * L))
        T.ret(xm, top - 5, 1, 5, ACO2); T.ret(xm + 4, top - 3, 1, 3, ACO1); T.px(xm, top - 6, ACO3)
        # junta das chapas e furos de alagamento (casco leve da proa e da popa)
        for uu in (-.2 * L, .0, .2 * L):
            x = int(self.X(uu))
            for y in range(int(self.oy - R + 3), int(self.oy + R - 2), 2): T.px(x, y, ACO0)
        for a, b in ((.30, .42), (-.41, -.29)):
            for uu in np.arange(a * L, b * L, 5):
                r = self.r(uu)
                if r > 4: T.ret(int(self.X(uu)), int(self.oy + r - 3), 2, 1, PRETO)
        if corte:
            self._corte(T, yy, xx, u, rc, casco)
        self._base[corte] = T.buf.copy()
        return self._base[corte]

    # regiões do corte (u em frações de L)
    TQ_PROA = (.30, .43)
    TQ_POPA = (-.42, -.28)
    RESIST = (-.27, .29)

    def _corte(self, T, yy, xx, u, rc, casco):
        L, R = self.L, self.R
        oy = self.oy
        dentro = casco & (np.abs(yy + .5 - oy) <= rc - 2.2) & (u > -.44 * L) & (u < .445 * L)
        buf = T.buf
        buf[dentro] = np.where((xx + yy) % 2 == 0, FUNDO2, FUNDO)[dentro]
        # sonar no nariz: arranjo de hidrofones
        son = dentro & (u > .43 * L)
        buf[son] = np.where((xx + yy) % 2 == 0, AGUA0, FUNDO3)[son]
        for uu in np.arange(.435 * L, .49 * L, 3):
            r = self.r(uu) - 3
            for vv in np.arange(-r, r + .1, 3):
                T.px(self.X(uu), self.Y(vv), CIANO)
        # tanques de lastro: paredes
        for a, b in (self.TQ_PROA, self.TQ_POPA):
            for uu in (a * L, b * L):
                r = self.r(uu)
                T.ret(int(self.X(uu)), int(oy - r + 2), 1, int(2 * r - 3), ACO3)
        # casco resistente: tubo de parede grossa com anéis
        a, b = self.RESIST
        x0, x1 = int(self.X(a * L)), int(self.X(b * L))
        rp = R - 1.5
        y0, y1 = int(oy - rp + 1), int(oy + rp - 1)
        dither(T, x0, y0, x1 - x0, y1 - y0, FUNDO3, FUNDO2)
        T.ret(x0, y0 - 1, x1 - x0, 3, ACO3); T.ret(x0, y0 - 1, x1 - x0, 1, ACO4)
        T.ret(x0, y1 - 1, x1 - x0, 3, ACO2); T.ret(x0, y1 + 1, x1 - x0, 1, ACO1)
        T.ret(x0 - 1, y0 - 1, 3, y1 - y0 + 3, ACO3); T.ret(x1 - 2, y0 - 1, 3, y1 - y0 + 3, ACO3)
        for x in range(x0 + 6, x1 - 3, 7):                 # anéis (cavernas)
            for y in range(y0 + 2, y1 - 1, 2): T.px(x, y, ACO1)
        piso = int(oy + rp * .30)
        T.ret(x0 + 2, piso, x1 - x0 - 4, 1, ACO2)
        for x in range(x0 + 8, x1 - 6, 16): T.px(x, y0 + 3, AMARELO)            # luzes
        # sala de controle sob a vela: periscópio e painéis
        xc = int(self.X(.15 * L))
        T.ret(xc, int(oy - R - self.hs + 4), 1, int(self.hs + R * .5), ACO3)
        for k, c in enumerate((CIANO, VERDE, AMARELO)):
            T.ret(xc - 14 + k * 9, piso - 5, 6, 4, PRETO); T.px(xc - 12 + k * 9, piso - 4, c); T.px(xc - 10 + k * 9, piso - 3, c)
        # eixo da hélice (atravessa o tanque da popa)
        T.ret(int(self.X(-.5 * L)) + 2, oy, int(.24 * L), 1, ACO3)

    # ------------------------------------------------ partes que mexem
    def _tanque_agua(self, T, a, b, frac, t, cor=MISTURA, cor2=FUNDO3):
        """Água dentro do tanque de lastro (região do casco entre u=a*L e b*L)."""
        L, R = self.L, self.R
        if frac <= 0: return
        yb, ytop = self.oy + R - 2.2, self.oy - R + 2.2
        yw = yb - frac * (yb - ytop)
        onda = math.sin(t * 2.5) * .8
        for x in range(int(self.X(a * L)) + 1, int(self.X(b * L))):
            uu = x + .5 - self.ox
            r = self.r(uu) - 2.2
            if r <= 0: continue
            ys = max(self.oy - r, yw + onda * (1 if (x // 6) % 2 else -1) * .5)
            ye = self.oy + r
            if ye <= ys: continue
            for y in range(int(math.ceil(ys)), int(ye) + 1):
                T.px(x, y, cor if (x + y) % 2 == 0 else cor2)
            if frac < .995: T.px(x, int(math.ceil(ys)), MISTURA2)

    def _caixa(self, T, a, b, frac, cor_borda=ACO3, h=None):
        """Tanque pequeno de ajuste no fundo do casco resistente."""
        L, R = self.L, self.R
        x0, x1 = int(self.X(a * L)), int(self.X(b * L))
        h = h or max(5, int(R * .62))
        y1 = int(self.oy + R - 3)
        y0 = y1 - h
        T.ret(x0 - 1, y0 - 1, x1 - x0 + 2, h + 2, cor_borda)
        dither(T, x0, y0, x1 - x0, h, FUNDO, FUNDO2)
        n = int(round(max(0, min(1, frac)) * h))
        if n: dither(T, x0, y1 - n, x1 - x0, n, MISTURA, FUNDO3); T.ret(x0, y1 - n, x1 - x0, 1, MISTURA2)
        return (x0 + x1) / 2, y0

    def desenhar_local(self, est, t):
        """Desenha na tela própria. `est`: corte, lastro (0..1 ou (proa, popa)),
        trim (proa, popa), ajuste, respiros, valvulas, sopro, transf (+1 proa->popa),
        lemes (graus, + = sobe), helice (fase rad), destaque (nome da peça)."""
        corte = est.get('corte', False)
        T = self.tela
        T.buf = self.base(corte).copy()
        L, R = self.L, self.R
        oy = self.oy
        if corte:
            la = est.get('lastro', 0.0)
            lf, lp = la if isinstance(la, tuple) else (la, la)
            self._tanque_agua(T, *self.TQ_PROA, lf, t)
            self._tanque_agua(T, *self.TQ_POPA, lp, t)
            tf, tp = est.get('trim', (.5, .5))
            cf = self._caixa(T, .19, .26, tf)
            cp = self._caixa(T, -.24, -.17, tp)
            cm = self._caixa(T, -.03, .04, est.get('ajuste', .3))
            yb = int(oy + R - 4)
            # cano de compensação (e a água correndo nele)
            T.ret(int(self.X(-.17 * L)), yb, int(.36 * L), 1, ACO2)
            tr = est.get('transf', 0)
            if tr:
                for k in range(8):
                    q = ((t * 1.2 * tr + k / 8) % 1.0)
                    x = self.X(.19 * L) - q * (.36 * L) if tr > 0 else self.X(-.17 * L) + q * (.36 * L)
                    T.ret(int(x), yb, 2, 1, MISTURA2)
            # garrafas de ar comprimido no teto
            a, b = -.15, -.03
            ya = int(oy - R + 4)
            for k in range(2):
                x0 = int(self.X((a + k * .065) * L))
                w = int(.055 * L)
                T.ret(x0, ya, w, 5, PRETO)
                T.ret(x0 + 1, ya + 1, w - 2, 3, LATAO); T.ret(x0 + 1, ya + 1, w - 2, 1, CHAMA0)
                T.px(x0 + w - 1, ya + 2, ACO3)
            yc = ya + 2
            xL, xR = int(self.X(self.TQ_POPA[1] * L)), int(self.X(self.TQ_PROA[0] * L))
            T.ret(xL, yc, int(self.X(a * L)) - xL, 1, ACO2)
            T.ret(int(self.X((a + .13) * L)) - 2, yc, xR - int(self.X((a + .13) * L)) + 2, 1, ACO2)
            if est.get('sopro'):
                for k in range(10):
                    q = (t * 1.6 + k / 10) % 1.0
                    xa = self.X((a + .13) * L) + q * (xR - self.X((a + .13) * L))
                    xb = self.X(a * L) - q * (self.X(a * L) - xL)
                    T.ret(int(xa), yc, 2, 1, BRANCO); T.ret(int(xb), yc, 2, 1, BRANCO)
        # respiros (em cima) e válvulas (embaixo) de cada tanque
        for uu in (.365 * L, -.35 * L):
            r = self.r(uu)
            x = int(self.X(uu))
            yt = int(oy - r)
            if est.get('respiros'):
                T.ret(x - 2, yt - 3, 5, 1, ACO4); T.ret(x - 2, yt - 2, 1, 2, ACO3); T.ret(x + 2, yt - 2, 1, 2, ACO3)
                T.ret(x - 1, yt - 1, 3, 2, PRETO)
            else:
                T.ret(x - 2, yt - 1, 5, 2, ACO4); T.ret(x - 2, yt - 2, 5, 1, PRETO)
            yv = int(oy + r)
            if est.get('valvulas'):
                T.ret(x - 2, yv - 1, 5, 2, PRETO)
            else:
                T.ret(x - 2, yv - 1, 5, 1, ACO2)
        # lemes de profundidade: proa (sobe = bordo de ataque para cima) e popa (ao contrário)
        ang = math.radians(est.get('lemes', 0.0))
        for uu, vv, comp, s in ((.33 * L, R * .25, .085 * L, 1), (-.445 * L, 0.0, .07 * L, -1)):
            px_, py_ = self.X(uu), self.Y(vv)
            dx, dy = math.cos(s * ang), -math.sin(s * ang)
            xa, ya = px_ - dx * comp * .4, py_ - dy * comp * .4
            xb, yb2 = px_ + dx * comp * .6, py_ + dy * comp * .6
            linha_grossa(T, xa, ya, xb, yb2, 4.2, PRETO)
            linha_grossa(T, xa, ya, xb, yb2, 2.2, ACO3)
            T.px(xb, yb2 - 1, ACO4)
        # hélice: as pás passam para cima e para baixo (disco visto de lado)
        fase = est.get('helice', 0.0)
        xh = self.X(-L / 2) - 2
        T.ret(int(xh) - 1, oy - 2, 4, 5, PRETO); T.ret(int(xh), oy - 1, 3, 3, ACO3)
        rp = R * .95
        for k in range(5):
            ph = fase + k * 2 * math.pi / 5
            s, c = math.sin(ph), math.cos(ph)
            yt = oy + s * rp
            if c > 0:
                linha_grossa(T, xh - 1, oy, xh - 2, yt, 3.0, PRETO)
                linha_grossa(T, xh - 1, oy, xh - 2, yt, 1.6, ACO4 if c > .7 else ACO3)
            else:
                T.linha(xh + 1, oy, xh + 1, yt, ACO1)
        return T.buf

    # ------------------------------------------------ peças (para os rótulos)
    def local(self, nome):
        L, R = self.L, self.R
        P = {
            'casco': (0.0, -R + 2), 'casco_baixo': (-.05 * L, R - 1),
            'lastro_proa': (.37 * L, R * .3), 'lastro_popa': (-.355 * L, R * .3),
            'respiro_proa': (.365 * L, -self.r(.365 * L) - 3), 'respiro_popa': (-.35 * L, -self.r(-.35 * L) - 3),
            'valvula_proa': (.365 * L, self.r(.365 * L)), 'valvula_popa': (-.35 * L, self.r(-.35 * L)),
            'trim_proa': (.225 * L, R - 6), 'trim_popa': (-.205 * L, R - 6), 'ajuste': (.005 * L, R - 6),
            'ar': (-.09 * L, -R + 6), 'leme_proa': (.36 * L, R * .25), 'leme_popa': (-.44 * L, 0.0),
            'helice': (-L / 2 - 3, R * .6), 'sonar': (.47 * L, 0.0), 'vela': (.15 * L, -R - self.hs * .5),
            'aneis': (-.13 * L, 0.0),
        }
        return P[nome]

    def tela_xy(self, nome, cx, cy, ang_graus=0.0):
        du, dv = self.local(nome)
        a = math.radians(ang_graus)
        return cx + du * math.cos(a) + dv * math.sin(a), cy - du * math.sin(a) + dv * math.cos(a)

    def desenhar(self, tela, cx, cy, ang_graus, est, t):
        src = self.desenhar_local(est, t)
        colar(tela, src, self.ox, self.oy, cx, cy, math.radians(ang_graus))


def colar(tela, src, px_, py_, cx, cy, a, y_max=PALCO_H):
    """Cola `src` (VAZIO = transparente) com o ponto (px_, py_) em (cx, cy),
    girado de `a` rad (positivo = nariz para cima). Vizinho mais próximo."""
    h, w = src.shape
    if abs(a) < 1e-4:
        x0, y0 = int(round(cx - px_)), int(round(cy - py_))
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(tela.w, x0 + w), min(y_max, y0 + h)
        if X1 <= X0 or Y1 <= Y0: return
        s = src[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        d = tela.buf[Y0:Y1, X0:X1]
        m = s != VAZIO
        d[m] = s[m]
        return
    ca, sa = math.cos(a), math.sin(a)
    cs = [(-px_, -py_), (w - px_, -py_), (-px_, h - py_), (w - px_, h - py_)]
    Xs = [cx + dx * ca + dy * sa for dx, dy in cs]
    Ys = [cy - dx * sa + dy * ca for dx, dy in cs]
    X0, X1 = max(0, int(min(Xs)) - 1), min(tela.w, int(max(Xs)) + 2)
    Y0, Y1 = max(0, int(min(Ys)) - 1), min(y_max, int(max(Ys)) + 2)
    if X1 <= X0 or Y1 <= Y0: return
    YY, XX = np.mgrid[Y0:Y1, X0:X1]
    Xr, Yr = XX + .5 - cx, YY + .5 - cy
    dx = Xr * ca - Yr * sa
    dy = Xr * sa + Yr * ca
    sx = np.floor(px_ + dx).astype(int)
    sy = np.floor(py_ + dy).astype(int)
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    v = np.full(sx.shape, VAZIO, np.uint8)
    v[ok] = src[sy[ok], sx[ok]]
    m = v != VAZIO
    d = tela.buf[Y0:Y1, X0:X1]
    d[m] = v[m]


# ================================================================ simulação vertical
class Vertical:
    """Fundura da quilha zk(t) (m) a partir do peso W(t) (fração do empuxo com o
    submarino todo embaixo d'água). O empuxo cresce com a parte submersa (paredes
    retas, simplificado) e para de crescer quando ele some na água (Arquimedes)."""

    def __init__(self, Wfn, dur, zk0, Hm, v0=0.0, dt=.01, cd=.032, cl=1.2, zmin=None):
        self.ts = np.arange(0, dur + .2, dt)
        z, v = zk0, v0
        zs, vs, bs = [], [], []
        for t in self.ts:
            Wt = Wfn(t)
            B = min(1.0, max(0.0, z / Hm))
            a = 9.8 * (Wt - B) - cd * v * abs(v) - (cl * v if z < Hm else 0.0)
            v += a * dt
            z += v * dt
            if zmin is not None and z < zmin: z, v = zmin, 0.0
            zs.append(z); vs.append(v); bs.append(B)
        self.z, self.v, self.b = np.array(zs), np.array(vs), np.array(bs)

    def __call__(self, t): return float(np.interp(t, self.ts, self.z))
    def vel(self, t): return float(np.interp(t, self.ts, self.v))
    def emp(self, t): return float(np.interp(t, self.ts, self.b))
