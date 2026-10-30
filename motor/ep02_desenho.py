#!/usr/bin/env python3
"""ep02 — desenho: o avião de lado, o céu, a pista, o túnel de vento e o turbofan.

  Aviao      jato genérico de 4 motores, de lado (vemos o lado DIREITO: luz de
             navegação verde na ponta da asa). Tudo é polígono, então gira
             com o ângulo do nariz. Flaps, slats e trem de pouso animados.
  Fluxo      túnel de vento. O ar é CALCULADO: escoamento potencial em volta
             de um perfil de Joukowski com a condição de Kutta (a circulação
             que deixa o ar sair liso pelo bordo de fuga). Daí sai tudo o que
             o vídeo mostra: o ar de cima mais rápido e chegando antes, o
             desvio para baixo atrás da asa e a pressão (Bernoulli,
             Cp = 1 - (v/U)²). As partículas são integradas no preparar() e
             guardadas quadro a quadro, então qualquer instante sai igual.
             O estol (separação) não existe em escoamento potencial: aqui ele
             é uma zona ilustrativa com redemoinhos (dito na descrição).
  Turbofan   corte do motor: ventilador, ar que contorna, núcleo, chama.
"""
import math
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1,
                   ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA,
                   MISTURA, MISTURA2, GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0)

BAY = LG.BAYER8
FPS = 30


# =================================================================== primitivas
def pol(tela, pts, c1, c2=None, fase=0):
    """Polígono cheio; com c2, em xadrez (o degradê de 8 bits)."""
    if len(pts) < 3: return
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys)))); y1 = min(tela.h - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + .5
        xs = []
        for i in range(n):
            ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a = max(0, int(round(xs[k]))); b = min(tela.w, int(round(xs[k + 1])))
            if b > a:
                if c2 is None:
                    tela.buf[y, a:b] = c1
                else:
                    xx = np.arange(a, b)
                    tela.buf[y, a:b] = np.where((xx + y + fase) % 2 == 0, c1, c2)


def contorno(tela, pts, cor):
    """Contorno escuro de 1 px: o polígono deslocado nas 4 direções."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pol(tela, [(x + dx, y + dy) for x, y in pts], cor)


def brilho(tela, x, y, r, cor):
    """Halo pontilhado em volta de uma luz (brilho sem alfa)."""
    x0, x1 = max(0, int(x - r - 1)), min(tela.w, int(x + r + 2))
    y0, y1 = max(0, int(y - r - 1)), min(tela.h, int(y + r + 2))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xx - x, yy - y)
    m = (d <= r) & ((xx + yy) % 2 == 0)
    tela.buf[y0:y1, x0:x1][m] = cor


def gradiente(tela, x, y, w, h, paradas, vertical=True, fase=0):
    """Degradê em degraus de Bayer 8x8 entre as cores de `paradas` [(f, cor)]."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(tela.w, int(x + w)), min(tela.h, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    f = ((yy - y) / max(1, h)) if vertical else ((xx - x) / max(1, w))
    fs = np.array([p[0] for p in paradas]); cs = np.array([p[1] for p in paradas])
    f = np.clip(f, fs[0], fs[-1] - 1e-6)
    i = np.clip(np.searchsorted(fs, f, side='right') - 1, 0, len(fs) - 2)
    u = (f - fs[i]) / (fs[i + 1] - fs[i])
    b = BAY[(yy + fase) % 8, xx % 8]
    tela.buf[y0:y1, x0:x1] = np.where(u > b, cs[i + 1], cs[i]).astype(np.uint8)


def seta_forca(tela, x0, y0, x1, y1, cor, esp=5, cab=8):
    """Seta grossa de força com contorno preto e filete de luz."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 2: return
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    bx, by = x1 - ux * cab, y1 - uy * cab
    cabeca = [(x1 + ux, y1 + uy), (bx + nx * cab * .8, by + ny * cab * .8), (bx - nx * cab * .8, by - ny * cab * .8)]
    haste = [(x0 + nx * esp / 2, y0 + ny * esp / 2), (bx + nx * esp / 2, by + ny * esp / 2),
             (bx - nx * esp / 2, by - ny * esp / 2), (x0 - nx * esp / 2, y0 - ny * esp / 2)]
    for p in (haste, cabeca):
        contorno(tela, p, PRETO)
    pol(tela, haste, cor); pol(tela, cabeca, cor)
    tela.linha(x0 + nx * (esp / 2 - 1), y0 + ny * (esp / 2 - 1), bx + nx * (esp / 2 - 1), by + ny * (esp / 2 - 1), BRANCO)


def barra(tela, x, y, w, h, frac, cor, fundo=FUNDO2, borda=ACO1):
    tela.ret(x - 1, y - 1, w + 2, h + 2, borda)
    tela.ret(x, y, w, h, fundo)
    f = max(0.0, min(1.0, frac))
    if f > 0:
        tela.ret(x, y, max(1, int(round(w * f))), h, cor)
        tela.ret(x, y, max(1, int(round(w * f))), 1, BRANCO if cor in (AMARELO, CIANO, VERDE) else ACO4)


def rotulo(tela, txt, x, y, ax, ay, cor=AMARELO, tam=9, direita=False):
    """Rótulo com fio até a peça (ax, ay)."""
    w = tela.largura_texto(txt, tam)
    h = 7 if tam < 14 else 14
    tx = x - w if direita else x
    tela.texto(txt, tx, y, cor, tam=tam, contorno=PRETO)
    lx = x + 2 if direita else x - 3
    if direita: lx = x + 3
    yy = y + h // 2
    tela.linha(lx, yy, ax, ay, cor)
    tela.disco(ax, ay, 1.4, cor)


# =================================================================== o avião
class Aviao:
    """Jato genérico de lado, nariz para a direita. Unidade: comprimento = 100."""
    FUS = [(-52, -3.0), (-44, -5.4), (-30, -6.0), (38, -6.0), (43, -5.4), (47, -4.2), (50, -2.4), (51.6, 0.0),
           (51, 1.8), (48, 3.6), (42, 4.8), (30, 5.2), (-14, 5.2), (-24, 4.6), (-36, 2.6), (-46, -0.4), (-52, -2.0)]
    BARRIGA = [(51.2, 1.4), (51, 1.8), (48, 3.6), (42, 4.8), (30, 5.2), (-14, 5.2), (-24, 4.6), (-36, 2.6),
               (-40, 1.4)]
    LEME = [(-29, -5.8), (-44, -25), (-51, -25), (-50.5, -21), (-47, -4.6)]
    ESTAB = [(-37, 0.6), (-45, 0.0), (-56, 4.0), (-52, 4.4)]
    ASA = [(14, 2.4), (2, 2.8), (-20, 9.0), (-15, 9.2)]
    MOTORES = [(12.0, 6.4), (-1.5, 9.0)]

    def desenhar(self, tela, ox, oy, k, ang=0.0, t=0.0, flaps=0.0, slats=None, trem=1.0, luz_pouso=False,
                 motor=1.0, piscar=True):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        P = lambda x, y: (ox + k * (x * ca + y * sa), oy + k * (-x * sa + y * ca))
        L = lambda pts: [P(x, y) for x, y in pts]
        slats = flaps if slats is None else slats
        # ---- calor do escape dos motores (atrás de tudo)
        if motor > 0:
            for (cx, cy) in self.MOTORES:
                for j in range(int(6 * motor)):
                    u = (t * 2.3 + j / 6) % 1.0
                    x, y = P(cx - 7 - u * 22, cy + math.sin(t * 13 + j * 2) * .8)
                    tela.px(x, y, GAS2 if u < .5 else TRACO)
                    tela.px(x + 1, y, GAS2 if u < .3 else TRACO)
        # ---- leme e estabilizador do outro lado (fundo)
        contorno(tela, L(self.LEME), PRETO)
        pol(tela, L(self.LEME), ACO3, ACO4)
        pol(tela, L([(-29, -5.8), (-44, -25), (-46, -25), (-33, -5.8)]), ACO4)       # bordo de ataque claro
        # ---- fuselagem
        fus = L(self.FUS)
        contorno(tela, fus, PRETO)
        pol(tela, fus, ACO4)
        pol(tela, L(self.BARRIGA), ACO3, ACO4)
        pol(tela, L([(48, 3.6), (42, 4.8), (30, 5.2), (-14, 5.2), (-24, 4.6), (-30, 3.8), (40, 3.8)]), ACO3)
        tela.linha(*P(-44, -5.0), *P(42, -5.0), BRANCO)                               # luz no dorso
        tela.linha(*P(-46, -4.2), *P(-30, -5.2), BRANCO)
        # janelas
        for x in range(-38, 41, 3):
            if -2 < x < 4 or 33 < x < 37: continue
            px, py = P(x, -1.8)
            tela.ret(px, py, max(1, int(k * .7)), max(1, int(k * .8)), FUNDO3)
        # portas
        for xd in (36.5, 2.5, -31):
            p0, p1, p2, p3 = P(xd, -3.8), P(xd + 2.2, -3.8), P(xd + 2.2, 2.6), P(xd, 2.6)
            for u, v in ((p0, p1), (p1, p2), (p2, p3), (p3, p0)):
                tela.linha(*u, *v, ACO2)
        # cabine
        cab = L([(44.6, -3.6), (48.0, -3.2), (49.6, -1.6), (45.0, -1.4)])
        pol(tela, cab, FUNDO2)
        x, y = P(46.2, -2.9); tela.ret(x, y, max(1, int(k * .8)), 1, CIANO)
        # ---- estabilizador do lado de cá
        contorno(tela, L(self.ESTAB), PRETO)
        pol(tela, L(self.ESTAB), ACO3)
        pol(tela, L([(-37, 0.6), (-45, 0.0), (-46, 0.8), (-38, 1.4)]), ACO4)
        # ---- trem de pouso
        if trem > .02:
            for (xg, rodas, y0) in ((41.0, (41.0,), 4.8), (-10.0, (-11.6, -8.4), 5.2), (-15.0, (-16.6, -13.4), 5.0)):
                yb = y0 + (11.0 - y0) * trem
                linha_grossa(tela, *P(xg, y0), *P(xg, yb - .6), max(1.5, k * .9), ACO1)
                for xr in rodas:
                    cx, cy = P(xr, yb)
                    tela.disco(cx, cy, max(1.5, k * 1.7), PRETO)
                    tela.disco(cx, cy, max(.8, k * .8), ACO2)
                    aa = -t * 30
                    tela.px(cx + math.cos(aa) * k * 1.2, cy + math.sin(aa) * k * 1.2, ACO0)
        # ---- motor de dentro (mais perto da fuselagem), depois a asa, depois o de fora
        self._motor(tela, P, L, *self.MOTORES[0], k, t)
        asa = L(self.ASA)
        contorno(tela, asa, PRETO)
        pol(tela, asa, ACO3, ACO2)
        pol(tela, L([(14, 2.4), (-15, 9.2), (-16.4, 9.2), (11, 2.5)]), ACO4)         # bordo de ataque
        pol(tela, L([(2, 2.8), (-20, 9.0), (-18.4, 9.1), (4, 2.75)]), ACO1)          # bordo de fuga
        # flaps: atrás da asa, descem e vão para trás
        if flaps > .02:
            f = flaps
            fl = [(1.0, 3.1), (-13.5, 7.2), (-13.5 - 2.6 * f, 7.2 + 2.4 * f), (1.0 - 2.6 * f, 3.1 + 2.8 * f)]
            contorno(tela, L(fl), PRETO)
            pol(tela, L(fl), ACO2, ACO1)
            tela.linha(*P(1.0 - 2.6 * f, 3.1 + 2.8 * f), *P(-13.5 - 2.6 * f, 7.2 + 2.4 * f), ACO3)
        if slats > .02:
            s = slats
            sl = [(13.4, 2.8 + .8 * s), (-11, 8.0 + .8 * s), (-10.2 + 1.2 * s, 8.6 + 1.2 * s),
                  (14.4 + 1.2 * s, 3.2 + 1.2 * s)]
            contorno(tela, L(sl), PRETO)
            pol(tela, L(sl), ACO4, ACO3)
        self._motor(tela, P, L, *self.MOTORES[1], k, t)
        # ---- luzes
        lp = P(-15.8, 9.4)                               # ponta da asa direita: verde
        brilho(tela, lp[0], lp[1], 3, VERDE); tela.disco(lp[0], lp[1], 1.2, VERDE); tela.px(lp[0], lp[1], BRANCO)
        if piscar and (t % 1.3) < .12:                    # farol rotativo vermelho
            for yy in (-6.6, 5.9):
                b = P(-6, yy)
                brilho(tela, b[0], b[1], 5, VERMELHO); tela.disco(b[0], b[1], 1.5, VERMELHO)
        if piscar and (t % 1.0) < .06:                    # estrobo branco
            brilho(tela, lp[0], lp[1], 7, BRANCO); tela.disco(lp[0], lp[1], 2, BRANCO)
        else:
            b = P(-6, -6.6); tela.px(b[0], b[1], BRASA)
        cauda = P(-52.6, -2.4); tela.px(cauda[0], cauda[1], BRANCO)
        if luz_pouso:
            lx, ly = P(13.2, 3.0)
            # facho de luz para a frente, pontilhado
            fe = [(lx, ly - 1), (lx + ca * 70 - sa * 14, ly - sa * 70 - 9), (lx + ca * 70 + sa * 14, ly - sa * 70 + 9), (lx, ly + 1)]
            m = np.zeros_like(tela.buf, dtype=bool)
            ys_ = [p[1] for p in fe]
            sub = tela.buf.copy()
            pol(tela, fe, 255)
            m = tela.buf == 255
            tela.buf[:] = sub
            yy, xx = np.nonzero(m)
            k3 = ((xx + 2 * yy) % 5 == 0)
            tela.buf[yy[k3], xx[k3]] = CHAMA0
            brilho(tela, lx, ly, 5, CHAMA0); tela.disco(lx, ly, 1.6, BRANCO)

    def _motor(self, tela, P, L, cx, cy, k, t):
        pod = [(cx + 5.6, cy - 2.1), (cx + 6.2, cy - 1.0), (cx + 6.2, cy + 1.0), (cx + 5.6, cy + 2.1),
               (cx - 3.5, cy + 1.9), (cx - 6.0, cy + 1.0), (cx - 6.0, cy - 1.0), (cx - 3.5, cy - 1.9)]
        pilone = [(cx + 2.5, cy - 1.9), (cx - 3.5, cy - 1.8), (cx - 5.0, cy - 3.8), (cx + 1.0, cy - 3.8)]
        contorno(tela, L(pilone), PRETO); pol(tela, L(pilone), ACO2)
        cone = [(cx - 6.0, cy - 1.0), (cx - 9.0, cy), (cx - 6.0, cy + 1.0)]
        contorno(tela, L(cone), PRETO); pol(tela, L(cone), ACO1)
        contorno(tela, L(pod), PRETO)
        pol(tela, L(pod), ACO4)
        pol(tela, L([(cx + 6.2, cy + .2), (cx + 5.6, cy + 2.1), (cx - 3.5, cy + 1.9), (cx - 6.0, cy + 1.0),
                     (cx - 6.0, cy + .2)]), ACO3, ACO2)
        tela.linha(*P(cx + 5.2, cy - 1.9), *P(cx + 5.2, cy + 1.9), ACO1)              # lábio da entrada
        tela.linha(*P(cx - 3, cy - 1.5), *P(cx + 4.8, cy - 1.5), BRANCO)


# =================================================================== avião visto de cima (ícone)
def aviao_topo(tela, cx, cy, s, cor=ACO3, cor2=ACO1, corte=False, t=0.0):
    """Silhueta genérica vista de cima, nariz para cima (ícone do painel)."""
    P = lambda pts: [(cx + x * s, cy + y * s) for x, y in pts]
    fus = [(0, -20), (2, -17), (2.2, 14), (0, 20), (-2.2, 14), (-2, -17)]
    asa = [(2, -3), (19, 6), (19, 8), (2, 4), (-2, 4), (-19, 8), (-19, 6), (-2, -3)]
    emp = [(1.6, 13), (8, 17.5), (8, 18.6), (0, 17.4), (-8, 18.6), (-8, 17.5), (-1.6, 13)]
    for p in (asa, emp, fus):
        contorno(tela, P(p), PRETO)
    pol(tela, P(asa), cor2); pol(tela, P(emp), cor2); pol(tela, P(fus), cor)
    for mx in (-12, -6.5, 6.5, 12):
        my = 1.2 + abs(mx) * .45
        tela.ret(cx + mx * s - 1, cy + my * s - 2, 2, 4, ACO4)
    if corte:
        x0, y0 = cx - 11 * s, cy - 3 * s
        x1, y1 = cx - 11 * s, cy + 9 * s
        for k in range(0, int(y1 - y0), 2):
            if (k // 2 + int(t * 6)) % 2 == 0: tela.px(x0, y0 + k, AMARELO)


# =================================================================== céu, nuvens, pista
class Ceu:
    PARADAS = [(0.0, PRETO), (.18, FUNDO), (.42, FUNDO2), (.62, FUNDO3), (.78, TRACO), (.88, ROXO),
               (.95, ROSA), (.985, LARANJA), (1.0, CHAMA1)]

    def __init__(self, seed=3):
        rng = np.random.default_rng(seed)
        self.estrelas = [(int(rng.integers(0, W)), int(rng.integers(0, 120)), float(rng.uniform(0, 6))) for _ in range(70)]
        self.nuvens = []
        for k in range(14):
            discos = []
            n = int(rng.integers(5, 9))
            larg = rng.uniform(30, 70)
            for j in range(n):
                dx = (j / (n - 1) - .5) * larg
                r = rng.uniform(5, 11) * (1 - abs(j / (n - 1) - .5) * .9)
                discos.append((dx, -r * .55 + rng.uniform(-2, 2), r))
            self.nuvens.append(discos)

    def horizonte(self, alt):
        """Linha do horizonte na tela: desce enquanto o avião sobe (o céu escurece)."""
        return 150 + alt / 1000.0 * 52

    def fundo(self, tela, alt, t, sol=True, sol_xy=None):
        hy = self.horizonte(alt)
        gradiente(tela, 0, 0, W, hy, self.PARADAS)
        vis = max(0.0, min(1.0, (alt - 1500) / 6000)) * .8 + .2
        for x, y, f in self.estrelas:
            if y < hy * .45 and math.sin(t * 1.7 + f * 3) > 1 - vis * 1.6:
                tela.px(x, y, BRANCO if f > 4.5 else ACO3)
        if sol:
            sx, sy = sol_xy if sol_xy else (392, min(hy - 6, 140))
            brilho(tela, sx, sy, 22, ROSA)
            brilho(tela, sx, sy, 15, LARANJA)
            tela.disco(sx, sy, 10, CHAMA1)
            tela.disco(sx, sy, 8, CHAMA0)
            tela.disco(sx - 2, sy - 2, 3, BRANCO)

    def nuvem(self, tela, x, y, discos, esc=1.0, luz=True):
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc + 2, r * esc + 1, PRETO)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc + 1.5, r * esc, ACO1)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc, r * esc * .92, ACO3)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc + 1.5, y + dy * esc - 1.5, r * esc * .6, ACO4)
        if luz:
            for dx, dy, r in discos[1:-1]:
                brilho(tela, x + dx * esc + 3, y + dy * esc - r * esc * .5, r * esc * .45, ROSA)

    def camada(self, tela, y, desloc, esc=1.0, densa=False, seed=0):
        """Uma fileira de nuvens que corre para a esquerda (`desloc` em px)."""
        passo = 70 * esc if not densa else 44 * esc
        n = int(W / passo) + 3
        for j in range(-1, n):
            idx = (j + int(desloc // passo) + seed) % len(self.nuvens)
            x = j * passo - (desloc % passo) + (idx * 13) % 20
            self.nuvem(tela, x, y + ((idx * 7) % 9) - 4, self.nuvens[idx], esc)

    def mar_nuvens(self, tela, y, desloc):
        """Tapete de nuvens visto de cima (cruzeiro)."""
        gradiente(tela, 0, y + 8, W, PALCO_H - y - 8, [(0, ACO2), (.5, ACO1), (1, ACO0)])
        self.camada(tela, y + 8, desloc * .7, esc=1.3, densa=True, seed=5)
        self.camada(tela, y, desloc, esc=1.0, densa=True, seed=2)


class Pista:
    """Chão do aeroporto: cidade ao longe, grama, pista com luzes. `xm` = quanto
    o mundo andou (px); `dy` empurra tudo para baixo quando o avião sobe."""

    def __init__(self, seed=5):
        rng = np.random.default_rng(seed)
        self.predios = []
        x = 0
        while x < 1400:
            w = int(rng.integers(8, 22)); h = int(rng.integers(6, 26))
            self.predios.append((x, w, h, int(rng.integers(0, 1000))))
            x += w + int(rng.integers(1, 6))

    def desenhar(self, tela, xm, dy, t, y_pista=176, luzes=True):
        hy = 150 + dy
        if hy >= PALCO_H: return
        # cidade (paralaxe lenta)
        off = (xm * .05) % 1400
        for (x, w, h, s) in self.predios:
            xx = x - off
            if xx < -30: xx += 1400
            if xx > W: continue
            tela.ret(xx, hy - h, w, h + 2, FUNDO2)
            tela.ret(xx, hy - h, 1, h, FUNDO3)
            for j in range(2, h - 2, 4):
                for i in range(2, w - 2, 4):
                    if (s + i * 7 + j * 13) % 5 == 0: tela.px(xx + i, hy - h + j, AMARELO if (s + i) % 3 else CHAMA0)
        # torre de controle genérica
        tx = 300 - (xm * .12) % 900
        if -30 < tx < W:
            tela.ret(tx, hy - 40, 5, 40, FUNDO3); tela.ret(tx + 1, hy - 40, 1, 40, TRACO)
            tela.ret(tx - 5, hy - 48, 15, 8, FUNDO3); tela.ret(tx - 4, hy - 46, 13, 3, CIANO)
            if (t % 1.5) < .2: tela.px(tx + 2, hy - 50, VERMELHO)
        # grama em faixas
        gradiente(tela, 0, hy, W, PALCO_H - hy, [(0, FUNDO2), (.3, AGUA0), (1, FUNDO)])
        for k in range(-1, 30):
            x = k * 20 - (xm * .6) % 20
            tela.ret(x, hy + 6 + dy * 0, 10, 1, AGUA0)
        # pista
        yp = y_pista + dy
        if yp < PALCO_H:
            dither(tela, 0, yp, W, 18, ACO0, FUNDO3)
            tela.ret(0, yp, W, 1, ACO2)
            tela.ret(0, yp + 18, W, 1, FUNDO2)
            for k in range(-1, 14):
                x = k * 40 - xm % 40
                tela.ret(x, yp + 9, 18, 2, BRANCO)
            if luzes:
                for k in range(-1, 26):
                    x = k * 20 - xm % 20
                    tela.px(x, yp - 1, AMARELO); tela.px(x, yp - 2, CHAMA0)
                    brilho(tela, x, yp - 1, 2, LARANJA)
                    tela.px(x + 6, yp + 18, BRANCO)


# =================================================================== túnel de vento
EPS = .12                     # espessura do perfil de Joukowski (~14%)


def joukowski(delta):
    mu = complex(-EPS, delta)
    R = abs(1 - mu)
    return mu, R


def perfil_w(delta, n=140):
    """Contorno do perfil no referencial da asa (complexo), começando no bordo
    de fuga e passando primeiro pelo extradorso (em cima)."""
    mu, R = joukowski(delta)
    th0 = math.atan2((1 - mu).imag, (1 - mu).real)
    th = th0 + np.linspace(0, 2 * math.pi, n, endpoint=False)
    zeta = mu + R * np.exp(1j * th)
    return zeta + 1 / zeta


def gama_kutta(alfa, delta):
    mu, R = joukowski(delta)
    zp = 1 - mu
    A = np.exp(-1j * alfa) - R * R * np.exp(1j * alfa) / zp ** 2
    return float((-A * 2 * math.pi * zp / 1j).real)


def vel_conj(z, alfa, delta, fg=1.0):
    """dw/dz no referencial da asa (vento U=1 vindo com ângulo alfa)."""
    mu, R = joukowski(delta)
    s = np.sqrt(z - 2) * np.sqrt(z + 2)
    z1 = (z + s) / 2; z2 = z - z1
    zeta = np.where(np.abs(z1 - mu) >= np.abs(z2 - mu), z1, z2)
    zp = zeta - mu
    dentro = np.abs(zp) < R * 1.0005
    G = gama_kutta(alfa, delta) * fg
    Wz = np.exp(-1j * alfa) - R * R * np.exp(1j * alfa) / zp ** 2 + 1j * G / (2 * math.pi * zp)
    dz = 1 - 1 / zeta ** 2
    with np.errstate(divide='ignore', invalid='ignore'):
        c = Wz / dz
    c = np.where(np.isfinite(c), c, 0)
    mag = np.abs(c)
    c = np.where(mag > 3.2, c / np.maximum(mag, 1e-9) * 3.2, c)
    return c, dentro


class Fluxo:
    """Túnel de vento: asa de corte em (cx, cy), `esc` px por unidade (corda ~4)."""

    def __init__(self, cx, cy, esc, regiao=(0, 8, 300, 200), U=64.0, passo=2):
        self.cx, self.cy, self.esc = cx, cy, esc
        self.x0, self.y0, self.x1, self.y1 = regiao
        self.U, self.p = U, passo
        self.gx = np.arange(self.x0, self.x1 + passo, passo, dtype=np.float64)
        self.gy = np.arange(self.y0, self.y1 + passo, passo, dtype=np.float64)
        self._cache = {}
        self.quadros = []
        self.n = 0

    # ---------------------------------------------------- geometria na tela
    def para_tela(self, z, alfa_g):
        zd = z * np.exp(-1j * math.radians(alfa_g))
        return self.cx + self.esc * zd.real, self.cy - self.esc * zd.imag

    def para_asa(self, x, y, alfa_g):
        zd = ((np.asarray(x) - self.cx) - 1j * (np.asarray(y) - self.cy)) / self.esc
        return zd * np.exp(1j * math.radians(alfa_g))

    def contorno_tela(self, alfa_g, delta):
        xs, ys = self.para_tela(perfil_w(delta), alfa_g)
        return list(zip(xs.tolist(), ys.tolist()))

    def extradorso(self, delta):
        z = perfil_w(delta, 200)
        i_le = int(np.argmin(z.real))
        cima = z[:i_le + 1]
        o = np.argsort(cima.real)
        return cima.real[o], cima.imag[o]

    # ---------------------------------------------------- campo (cache)
    def campo(self, alfa_g, delta, fg=1.0):
        ch = (round(alfa_g * 4) / 4, round(delta * 200) / 200, round(fg * 50) / 50)
        c = self._cache.get(ch)
        if c is None:
            a, d, g = math.radians(ch[0]), ch[1], ch[2]
            X, Y = np.meshgrid(self.gx, self.gy)
            zd = ((X - self.cx) - 1j * (Y - self.cy)) / self.esc
            z = zd * np.exp(1j * a)
            cc, dentro = vel_conj(z, a, d, g)
            vd = np.conj(cc) * np.exp(-1j * a)
            vx, vy = vd.real, -vd.imag
            vx[dentro] = 0; vy[dentro] = 0
            cp = 1 - (vx ** 2 + vy ** 2)
            cp[dentro] = 0
            c = (vx.astype(np.float32), vy.astype(np.float32), dentro, cp.astype(np.float32))
            if len(self._cache) > 400: self._cache.clear()
            self._cache[ch] = c
        return c

    def _amostra(self, grade, x, y):
        fx = np.clip((x - self.x0) / self.p, 0, len(self.gx) - 1.001)
        fy = np.clip((y - self.y0) / self.p, 0, len(self.gy) - 1.001)
        i, j = fy.astype(int), fx.astype(int)
        u, v = fy - i, fx - j
        return (grade[i, j] * (1 - u) * (1 - v) + grade[i, j + 1] * (1 - u) * v +
                grade[i + 1, j] * u * (1 - v) + grade[i + 1, j + 1] * u * v)

    # ---------------------------------------------------- simulação
    def simular(self, dur, alfa=lambda t: 4.0, delta=lambda t: .1, vel=lambda t: 1.0, estol=lambda t: 0.0,
                faixa=6, pulsos=(), espaco=14, aquecer=6.0, seed=1):
        """Integra as partículas de -aquecer até dur. Guarda por quadro:
        (x, y, vx, vy, tipo, ordem). tipo 0 = filete, 1+ = pulso k."""
        rng = np.random.default_rng(seed)
        faixas = np.arange(self.y0 + 3, self.y1 - 2, faixa, dtype=np.float64)
        fase = rng.uniform(0, espaco, len(faixas))
        X = np.zeros(0); Y = np.zeros(0); idade = np.zeros(0); tipo = np.zeros(0, np.int16)
        ordem = np.zeros(0, np.int32); faixa_i = np.zeros(0, np.int16)
        acum = espaco
        pend = sorted(pulsos)
        dt = 1.0 / FPS
        sub = 3
        n_aq = int(aquecer * FPS)
        self.quadros = []
        self.chegada = {}
        t = -aquecer
        nq = int(math.ceil(dur * FPS)) + 1
        for q in range(-n_aq, nq):
            t = q / FPS
            tc = max(0.0, t)
            a, d, uu, s = alfa(tc), delta(tc), vel(tc), estol(tc)
            fg = 1 - .45 * s
            vx_g, vy_g, dentro_g, _ = self.campo(a, d, fg)
            # nascer
            acum += uu * self.U * dt
            while acum >= espaco:
                acum -= espaco
                xs = self.x0 - 3 + acum - fase
                X = np.concatenate([X, xs]); Y = np.concatenate([Y, faixas + rng.uniform(-.4, .4, len(faixas))])
                idade = np.concatenate([idade, np.zeros(len(faixas))])
                tipo = np.concatenate([tipo, np.zeros(len(faixas), np.int16)])
                ordem = np.concatenate([ordem, np.arange(len(faixas), dtype=np.int32)])
                faixa_i = np.concatenate([faixa_i, np.arange(len(faixas), dtype=np.int16)])
            while pend and pend[0][0] <= t:
                tp, xp, ya, yb, esp = pend.pop(0)
                k = len(self.chegada) + 1
                ys = np.arange(ya, yb + .01, esp)
                X = np.concatenate([X, np.full(len(ys), float(xp))]); Y = np.concatenate([Y, ys])
                idade = np.concatenate([idade, np.zeros(len(ys))])
                tipo = np.concatenate([tipo, np.full(len(ys), k, np.int16)])
                ordem = np.concatenate([ordem, np.arange(len(ys), dtype=np.int32)])
                faixa_i = np.concatenate([faixa_i, np.zeros(len(ys), np.int16)])
                self.chegada[k] = dict(t0=tp, chegou={}, lado={})
            # integrar (ponto médio)
            vxs = vys = None
            for _ in range(sub):
                h = dt / sub
                ax_, ay_ = self._vel(X, Y, vx_g, vy_g, a, d, s, t, uu)
                mx, my = X + ax_ * h / 2, Y + ay_ * h / 2
                bx_, by_ = self._vel(mx, my, vx_g, vy_g, a, d, s, t, uu)
                X = X + bx_ * h; Y = Y + by_ * h
                vxs, vys = bx_, by_
            idade = idade + dt
            # chegada dos pulsos ao bordo de fuga
            if self.chegada:
                xte, yte = self.para_tela(np.array([2.0 + 0j]), a)
                for k, info in self.chegada.items():
                    m = (tipo == k)
                    for i in np.nonzero(m & (X >= xte[0]))[0]:
                        o = int(ordem[i])
                        if o not in info['chegou']:
                            info['chegou'][o] = t - info['t0']
                            info['lado'][o] = 'cima' if Y[i] < yte[0] else 'baixo'
            # matar
            dn = self._amostra(dentro_g.astype(np.float32), X, Y) > .5
            vivo = (X < self.x1 + 6) & (Y > self.y0 - 8) & (Y < self.y1 + 8) & ~dn & (idade < 16)
            X, Y, idade, tipo, ordem, faixa_i = X[vivo], Y[vivo], idade[vivo], tipo[vivo], ordem[vivo], faixa_i[vivo]
            vxs, vys = vxs[vivo], vys[vivo]
            if q >= 0:
                self.quadros.append((X.astype(np.float32), Y.astype(np.float32), vxs.astype(np.float32),
                                     vys.astype(np.float32), tipo.copy(), ordem.copy(), faixa_i.copy(),
                                     (a, d, uu, s)))
        self.n = len(self.quadros)

    def _vel(self, X, Y, vx_g, vy_g, a, d, s, t, uu):
        vx = self._amostra(vx_g, X, Y) * self.U * uu
        vy = self._amostra(vy_g, X, Y) * self.U * uu
        if s > 0:
            zw = self.para_asa(X, Y, a)
            xw, yw = zw.real, zw.imag
            ex, ey = self.extradorso(d)
            xs = 2.0 - 3.4 * s
            xc = np.clip(xw, ex[0], 2.0)
            yu = np.interp(xc, ex, ey)
            hz = .08 + .5 * s * np.clip(xw - xs, 0, 5)
            zona = (xw > xs) & (yw > yu - .05) & (yw < yu + hz) & (xw < 2.0 + 1.0)
            if zona.any():
                U = self.U * uu
                svx = np.full(X.shape, .22 * U); svy = np.zeros(X.shape)
                # redemoinhos que nascem no ponto de separação e descem com o ar
                p0 = self.para_tela(np.array([complex(xs, float(np.interp(xs, ex, ey)) + .18)]), a)
                Tv = .9
                rc = 6.0
                for j in range(8):
                    ida = (t % Tv) + j * Tv
                    vxp = p0[0][0] + .42 * U * ida
                    vyp = p0[1][0] + 7 * math.sin(j * 1.7 + t) + ida * 3.5
                    dx, dy = X - vxp, Y - vyp
                    r2 = np.maximum(dx * dx + dy * dy, rc * rc)
                    Gv = .9 * U * rc * min(1.0, ida / .3)
                    svx += -dy * Gv / r2
                    svy += dx * Gv / r2
                vx = np.where(zona, svx, vx)
                vy = np.where(zona, svy, vy)
        return vx, vy

    def estado(self, t):
        k = min(self.n - 1, max(0, int(round(t * FPS))))
        return self.quadros[k]

    # ---------------------------------------------------- desenho
    def pressao(self, tela, t, forca=1.0, clip_x=None):
        """Mapa de pressão em xadrez: azul = menor que a do ar em volta,
        laranja = maior. Densidade do ponto = tamanho da diferença."""
        a, d, uu, s = self.estado(t)[7]
        vx, vy, dentro, cp = self.campo(a, d, 1 - .45 * s)
        cpf = np.repeat(np.repeat(cp, self.p, 0), self.p, 1)
        x0, y0 = int(self.x0), int(self.y0)
        x1 = int(clip_x if clip_x else self.x1); y1 = int(self.y1)
        hh, ww = min(cpf.shape[0], y1 - y0), min(cpf.shape[1], x1 - x0)
        cpf = cpf[:hh, :ww]
        if s > 0:
            yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + ww]
            zw = self.para_asa(xx, yy, a)
            ex, ey = self.extradorso(d)
            xs = 2.0 - 3.4 * s
            yu = np.interp(np.clip(zw.real, ex[0], 2.0), ex, ey)
            zona = (zw.real > xs) & (zw.imag > yu - .05) & (zw.imag < yu + .1 + .5 * s * np.clip(zw.real - xs, 0, 5))
            cpf = np.where(zona & (cpf < 0), cpf * .25, cpf)
        b = np.tile(LG.AC.BAYER4, (hh // 4 + 1, ww // 4 + 1))[:hh, :ww]
        sub = tela.buf[y0:y0 + hh, x0:x0 + ww]
        baixa = np.clip((-cpf - .06) / 1.5, 0, 1) * forca
        alta = np.clip((cpf - .07) / .8, 0, 1) * forca
        m1 = baixa * .75 > b
        m1b = baixa * .75 > b + .45
        m2 = alta * .7 > b
        m2b = alta * .7 > b + .45
        sub[m1] = MISTURA; sub[m1b] = MISTURA2
        sub[m2] = BRASA; sub[m2b] = LARANJA

    def desenhar(self, tela, t, cor='faixa', rastro=1.0, pulso=True, so_pulsos=False, sem_filetes=False,
                 destaque=None, clip=None):
        X, Y, VX, VY, tipo, ordem, fi, (a, d, uu, s) = self.estado(t)
        U = self.U * max(uu, .2)
        cx0, cy0, cx1, cy1 = clip if clip else (0, 0, W, PALCO_H)
        if not so_pulsos and not sem_filetes:
            m = tipo == 0
            xs, ys, vx, vy, ff = X[m], Y[m], VX[m], VY[m], fi[m]
            sp = np.hypot(vx, vy) / U
            for i in range(len(xs)):
                x, y = xs[i], ys[i]
                if not (cx0 <= x < cx1 and cy0 <= y < cy1): continue
                if cor == 'vel':
                    r = sp[i]
                    c = ROXO if r < .6 else (ACO2 if r < .92 else (ACO3 if r < 1.12 else (CIANO if r < 1.45 else BRANCO)))
                else:
                    c = CIANO if ff[i] % 4 == 0 else ACO2
                L = .10 * rastro
                x2, y2 = x - vx[i] * L, y - vy[i] * L
                if x2 < cx0: x2 = cx0
                tela.linha(x, y, x2, y2, c)
                tela.px(x, y, BRANCO if c in (CIANO, BRANCO) else ACO3)
        if pulso:
            for k in sorted(set(tipo[tipo > 0].tolist())):
                m = np.nonzero(tipo == k)[0]
                o = np.argsort(ordem[m]); m = m[o]
                for i0, i1 in zip(m[:-1], m[1:]):
                    if ordem[i1] - ordem[i0] != 1: continue
                    if math.hypot(X[i1] - X[i0], Y[i1] - Y[i0]) > 26: continue
                    if not (cx0 <= X[i0] < cx1 and cx0 <= X[i1] < cx1): continue
                    linha_grossa(tela, X[i0], Y[i0] + .5, X[i1], Y[i1] + .5, 2.2, LARANJA)
                    tela.linha(X[i0], Y[i0], X[i1], Y[i1], AMARELO)
                for i in m:
                    if cx0 <= X[i] < cx1: tela.px(X[i], Y[i], CHAMA0)
        if destaque:
            for (k, o, cor_d) in destaque:
                m = np.nonzero((tipo == k) & (ordem == o))[0]
                if len(m):
                    i = m[0]
                    tela.anel(X[i], Y[i], 4, PRETO, 1.2)
                    tela.anel(X[i], Y[i], 3, cor_d, .7)
                    tela.disco(X[i], Y[i], 1.5, cor_d)

    def asa(self, tela, t=None, alfa_g=None, delta=None, cor=ACO3):
        if t is not None:
            a, d = self.estado(t)[7][:2]
        alfa_g = a if alfa_g is None else alfa_g
        delta = d if delta is None else delta
        desenhar_perfil(tela, self, alfa_g, delta)

    def ponto(self, xw, yw, alfa_g):
        x, y = self.para_tela(np.array([complex(xw, yw)]), alfa_g)
        return float(x[0]), float(y[0])

    def sustentacao(self, alfa_g, delta, s=0.0):
        """Coeficiente de sustentação relativo (Kutta-Joukowski: L = rho U Gamma)."""
        return gama_kutta(math.radians(alfa_g), delta) * (1 - .45 * s)


def desenhar_perfil(tela, F, alfa_g, delta, partes=None):
    """O corte da asa: pele de metal, longarinas, tanque. `partes` = (slat, flap)
    em 0..1 desenha a asa em 3 peças (slat e flap abertos)."""
    z = perfil_w(delta, 160)
    if partes is None:
        pts = F.contorno_tela(alfa_g, delta)
        contorno(tela, pts, PRETO)
        pol(tela, pts, ACO2, ACO1)
        _sombra(tela, F, z, alfa_g)
        _pele(tela, F, z, alfa_g)
        _longarinas(tela, F, z, alfa_g, -1.0, 1.0)
        return
    sl, fl = partes
    xr = z.real
    corpo = z[(xr >= -1.45) & (xr <= 1.15)]
    slat = z[xr < -1.35]
    flap = z[xr > 1.05]
    def mover(zz, piv, ang, desl):
        return (zz - piv) * np.exp(-1j * math.radians(ang)) + piv + desl
    # slat: desce e vai para a frente; flap: gira para baixo e vai para trás
    slat_m = mover(slat, complex(-1.4, 0), 16 * sl, complex(-.16 * sl, -.16 * sl))
    flap_m = mover(flap, complex(1.1, -.05), 28 * fl, complex(.18 * fl, -.08 * fl))
    for zz, c1, c2 in ((corpo, ACO1, ACO0), (slat_m, ACO2, ACO1), (flap_m, ACO2, ACO1)):
        o = np.argsort(np.angle(zz - zz.mean()))
        zz = zz[o]
        xs, ys = F.para_tela(zz, alfa_g)
        pts = list(zip(xs.tolist(), ys.tolist()))
        contorno(tela, pts, PRETO)
        pol(tela, pts, c1, c2)
        n = len(zz)
        for i in range(n):
            j = (i + 1) % n
            if zz[i].imag >= -0.02 and zz[j].imag >= -0.02:
                tela.linha(xs[i], ys[i], xs[j], ys[j], ACO4)
            else:
                tela.linha(xs[i], ys[i], xs[j], ys[j], ACO3)
    _longarinas(tela, F, z, alfa_g, -1.0, .6)


def _sombra(tela, F, z, alfa_g):
    """Metade de baixo do corte mais escura (luz vem de cima)."""
    xr = z.real
    i_le = int(np.argmin(xr))
    cima_x, cima_y = xr[:i_le + 1], z.imag[:i_le + 1]
    baixo = z[i_le:]
    oc = np.argsort(cima_x)
    meio = np.interp(baixo.real, cima_x[oc], cima_y[oc])
    linha = baixo.real + 1j * (baixo.imag + (meio - baixo.imag) * .45)
    zz = np.concatenate([baixo, linha[::-1]])
    xs, ys = F.para_tela(zz, alfa_g)
    pol(tela, list(zip(xs.tolist(), ys.tolist())), ACO1, ACO0)


def _pele(tela, F, z, alfa_g):
    xs, ys = F.para_tela(z, alfa_g)
    n = len(z)
    i_le = int(np.argmin(z.real))
    for i in range(n):
        j = (i + 1) % n
        cor = ACO4 if i < i_le else ACO3
        tela.linha(xs[i], ys[i], xs[j], ys[j], cor)
        # pele com 2 px: segunda linha para dentro
    for i in range(0, i_le, 2):
        tela.px(xs[i], ys[i] + 1, ACO3)
    # brilho do extradorso perto do bordo de ataque
    for i in range(int(i_le * .55), int(i_le * .9)):
        tela.px(xs[i], ys[i], BRANCO)


def _longarinas(tela, F, z, alfa_g, xa, xb):
    xr = z.real
    i_le = int(np.argmin(xr))
    cima_x, cima_y = xr[:i_le + 1], z.imag[:i_le + 1]
    baixo_x, baixo_y = xr[i_le:], z.imag[i_le:]
    oc = np.argsort(cima_x); ob = np.argsort(baixo_x)
    for xw in (xa, xb):
        yt = float(np.interp(xw, cima_x[oc], cima_y[oc])) - .05
        yb = float(np.interp(xw, baixo_x[ob], baixo_y[ob])) + .05
        p0 = F.ponto(xw, yt, alfa_g); p1 = F.ponto(xw, yb, alfa_g)
        linha_grossa(tela, p0[0], p0[1], p1[0], p1[1], 2.2, ACO2)
    # tanque de combustível entre as longarinas: pontilhado âmbar discreto
    for k in range(12):
        xw = xa + (xb - xa) * (k + .5) / 12
        yt = float(np.interp(xw, cima_x[oc], cima_y[oc])) - .12
        yb = float(np.interp(xw, baixo_x[ob], baixo_y[ob])) + .12
        for j in range(4):
            yw = yb + (yt - yb) * (j + .5) / 4
            x, y = F.ponto(xw, yw, alfa_g)
            if (k + j) % 2 == 0: tela.px(x, y, OLEO0)


def fundo_tunel(tela, t, x1=W, vento=1.0):
    """Túnel de vento: parede escura com grade, piso e teto rebitados."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24):
        tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24):
        tela.ret(0, y, W, 1, FUNDO2)
    for y0 in (0, 200):
        tela.ret(0, y0, x1, 8, ACO0)
        tela.ret(0, y0 + (7 if y0 == 0 else 0), x1, 1, ACO2)
        for x in range(4, x1, 16):
            tela.px(x, y0 + 3, ACO2); tela.px(x + 1, y0 + 3, ACO3)
    # setas do vento na parede de cima
    for k in range(-1, 12):
        x = k * 32 + (t * 40 * vento) % 32
        if x < x1 - 8:
            tela.ret(x, 3, 6, 1, ACO3); tela.px(x + 6, 2, ACO3); tela.px(x + 6, 4, ACO3); tela.px(x + 7, 3, ACO3)


# =================================================================== turbofan
class Turbofan:
    """Corte de um turbofan genérico, entrada à esquerda (o ar vai da esquerda
    para a direita). cx, cy = eixo; L = comprimento."""

    def __init__(self, cx, cy, s=1.0, seed=2):
        self.cx, self.cy, self.s = cx, cy, s
        rng = np.random.default_rng(seed)
        self.pb = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 6.28)) for _ in range(70)]
        self.pc = [(rng.uniform(0, 1), rng.uniform(-1, 1), rng.uniform(0, 6.28)) for _ in range(40)]

    def P(self, x, y): return self.cx + x * self.s, self.cy + y * self.s

    def L(self, pts): return [self.P(x, y) for x, y in pts]

    def desenhar(self, tela, t, giro=1.0, foco=None, mostrar=('fan', 'core', 'bypass', 'jato')):
        s = self.s
        # ---- jatos de saída (atrás de tudo)
        if 'jato' in mostrar:
            for k in range(26):
                u = (k / 26 + t * .9 * giro) % 1.0
                for lado in (-1, 1):
                    x, y = self.P(84 + u * 70, lado * (30 + u * 5) + math.sin(k * 3 + t * 4) * 2)
                    tela.ret(x, y, 3, 1, CIANO if u < .5 else ACO2)
            for k in range(22):
                u = (k / 22 + t * 1.3 * giro) % 1.0
                x, y = self.P(98 + u * 60, math.sin(k * 5 + t * 9) * (4 + u * 6))
                tela.ret(x, y, 2, 2, CHAMA0 if u < .2 else (CHAMA1 if u < .45 else (BRASA if u < .7 else GAS)))
        # ---- carenagem (nacele) em corte: parede de cima e de baixo
        for lado in (-1, 1):
            nac = [(-72, lado * 46), (-64, lado * 52), (40, lado * 50), (80, lado * 40), (78, lado * 36),
                   (40, lado * 44), (-60, lado * 44), (-70, lado * 42)]
            contorno(tela, self.L(nac), PRETO)
            pol(tela, self.L(nac), ACO3 if lado < 0 else ACO2, ACO2 if lado < 0 else ACO1)
            tela.linha(*self.P(-64, lado * 51), *self.P(40, lado * 49), ACO4 if lado < 0 else ACO3)
        # ---- ar que contorna (dutos do bypass)
        if 'bypass' in mostrar:
            for (u0, v0, f) in self.pb:
                u = (u0 + t * .55 * giro) % 1.0
                x = -60 + u * 150
                for lado in (-1, 1):
                    if x < -40: y = lado * (14 + v0 * 28)
                    else: y = lado * (26 + v0 * (16 - max(0, x - 40) * .1))
                    px, py = self.P(x, y)
                    tela.ret(px, py, 3, 1, CIANO if v0 > .3 else MISTURA2)
        # ---- núcleo: carcaça do motor
        nuc = [(-30, -20), (10, -18), (60, -14), (96, -8), (96, 8), (60, 14), (10, 18), (-30, 20)]
        contorno(tela, self.L(nuc), PRETO)
        pol(tela, self.L(nuc), FUNDO2)
        for lado in (-1, 1):
            cas = [(-30, lado * 20), (10, lado * 18), (60, lado * 14), (96, lado * 8), (96, lado * 11),
                   (60, lado * 17), (10, lado * 22), (-30, lado * 24)]
            pol(tela, self.L(cas), ACO2, ACO1)
        # compressor: estágios que encolhem
        if 'core' in mostrar:
            for j in range(8):
                x = -24 + j * 5.5
                hgt = 17 - j * 1.2
                fase = (t * 14 * giro + j * .7) % 2
                cor = ACO3 if fase < 1 else ACO4
                linha_grossa(tela, *self.P(x, -hgt), *self.P(x, hgt), max(1.5, 2.2 * s), cor)
                tela.ret(*self.P(x - 1, -hgt), 1, 2 * hgt * s, ACO1)
            # câmara de combustão: chama que pisca
            for k in range(30):
                u = (k * .618 + t * 2.2) % 1.0
                ang = k * 2.4
                x = 26 + u * 22
                y = math.sin(ang + t * 7) * (7 - u * 3)
                px, py = self.P(x, y)
                c = CHAMA0 if u < .25 else (CHAMA1 if u < .55 else CHAMA2)
                tela.ret(px, py, 2, 2, c)
            brilho(tela, *self.P(36, 0), 11 * s, CHAMA1)
            tela.disco(*self.P(34, 0), 3 * s, CHAMA0)
            # turbinas
            for j in range(5):
                x = 54 + j * 6
                hgt = 11 + j * .8
                fase = (t * 18 * giro + j * .5) % 2
                linha_grossa(tela, *self.P(x, -hgt), *self.P(x, hgt), max(1.5, 2.2 * s), LATAO if fase < 1 else ACO3)
            # eixos
            tela.ret(*self.P(-48, -1.5), int(150 * s), max(1, int(3 * s)), ACO2)
            tela.ret(*self.P(-48, -1.5), int(150 * s), 1, ACO4)
        # ---- ventilador
        if 'fan' in mostrar:
            cone = [(-66, 0), (-52, -11), (-44, -12), (-44, 12), (-52, 11)]
            tela.ret(*self.P(-54, -43), int(12 * s), int(86 * s), FUNDO3)
            n = 12
            for j in range(n):
                fase = (j / n + t * 1.6 * giro) % 1.0
                y = (fase * 2 - 1) * 41
                larg = 11 * abs(math.cos((fase * 2 - 1) * math.pi / 2)) + 2
                c = ACO4 if fase < .5 else ACO2
                x0, y0 = self.P(-48 - larg / 2, y - 2.5)
                tela.ret(x0, y0, max(2, int(larg * s)), max(2, int(5 * s)), c)
                tela.ret(x0, y0, max(2, int(larg * s)), 1, BRANCO if fase < .5 else ACO3)
            tela.ret(*self.P(-49, -42), max(1, int(2 * s)), int(84 * s), ACO1)
            contorno(tela, self.L(cone), PRETO)
            pol(tela, self.L(cone), ACO4, ACO3)
            x, y = self.P(-56, -6); tela.ret(x, y, 2, 2, BRANCO)
            # ar entrando
            for k in range(18):
                u = (k / 18 + t * .8 * giro) % 1.0
                y = ((k * 37) % 80) - 40
                x, yy = self.P(-110 + u * 46, y)
                tela.ret(x, yy, 3, 1, ACO3)
