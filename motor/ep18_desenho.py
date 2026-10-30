#!/usr/bin/env python3
"""ep18 — desenho: o foguete, a chama, o céu do voo, a plataforma, a Terra e o motor aberto.

  Voo        o voo de verdade, CALCULADO: ponto de massa em volta de uma Terra
             redonda (gravidade GM/r²), 2 estágios com empuxo e consumo
             constantes, subida reta, inclinação de 4,5° aos 10 s e depois
             curva gravitacional (o empuxo segue a velocidade); o 2º estágio
             usa a lei da tangente linear até a velocidade de órbita circular.
             Sem arrasto do ar e sem a rotação da Terra (dito na descrição).
             O painel, a inclinação do foguete e o céu leem estes números.
  Foguete    foguete genérico de 2 estágios, de lado, em coordenadas do eixo
             (s = 0 na boca da tubeira, 100 na ponta da coifa; u = de lado).
             Tudo é polígono: gira com a inclinação. Corte mostra os tanques.
  chama      a chama sai SEMPRE no sentido -eixo (oposto ao movimento): curta,
             com diamantes de choque, embaixo; larga e comprida no vácuo.
  Tubeira    o motor aberto: área-Mach de uma tubeira de Laval (gama 1,2),
             razão de áreas 20 -> Mach 3,7 na saída, gás a ~2.900 m/s.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO,
                   CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS,
                   GAS2, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep02_desenho import pol, contorno, brilho, gradiente, seta_forca, barra

BAY = LG.BAYER8

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#a8dcff', '#6cb6f2', '#3f86d6', '#2a5aa8', '#1a3670', '#0f1f45',      # 32..37 céu
          '#1d3d27', '#2d6334', '#4f8f44', '#8a8478',                            # 38..41 chão, concreto
          '#0e2f5c', '#1c5596', '#3a86c8',                                       # 42..44 mar
          '#3f6a2a', '#71963c',                                                  # 45..46 terra (globo)
          '#f2f6fc', '#c3cbd8',                                                  # 47..48 casco
          '#e4ded4', '#aaa398', '#6e6a64',                                       # 49..51 fumaça
          '#c4ecff', '#e8a640']                                                  # 52..53 LOX, RP-1
PX.PALETAS['ep18'] = _BASE + _EXTRA
LG.PAL = 'ep18'
CEU0, CEU1, CEU2, CEU3, CEU4, CEU5 = 32, 33, 34, 35, 36, 37
CHAO0, CHAO1, CHAO2, CONCRETO = 38, 39, 40, 41
MAR0, MAR1, MAR2, SOLO0, SOLO1 = 42, 43, 44, 45, 46
CASCO, CASCO2 = 47, 48
FUM0, FUM1, FUM2 = 49, 50, 51
LOX, RP1 = 52, 53
VAZIO = 255


def hsh(i, k=0):
    """Ruído determinístico 0..1."""
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


# =================================================================== o voo
MU, RT, G0 = 3.986e14, 6.371e6, 9.80665


class Voo:
    """Simulação do voo (passo de 0,05 s). Consulta por instante de voo tf (s)."""
    PROP1, SECO1, PROP2, SECO2, CARGA = 380e3, 40e3, 110e3, 8e3, 10e3
    F1, VE1, F2, VE2 = 7.6e6, 2900.0, 1.1e6, 3450.0
    T_KICK, KICK = 10.0, 4.5
    B0, CC = math.radians(25.2), .0014

    def __init__(self, dt=.05, t_fim=1200.0):
        x, y, vx, vy = 0.0, RT, 0.0, 0.0
        m = self.PROP1 + self.SECO1 + self.PROP2 + self.SECO2 + self.CARGA
        self.M0 = m
        p1, p2 = self.PROP1, self.PROP2
        est, t, fim, tsep = 1, 0.0, None, None
        rows = []
        while t < t_fim:
            r = math.hypot(x, y); ux, uy = x / r, y / r; ex, ey = uy, -ux
            vr = vx * ux + vy * uy; vt = vx * ex + vy * ey
            F = 0.0
            if est == 1:
                F = self.F1; md = F / self.VE1
                if t < self.T_KICK: ang = 0.0
                elif t < self.T_KICK + 8: ang = math.radians(self.KICK) * (t - self.T_KICK) / 8
                else: ang = math.atan2(vt, vr)
                p1 -= md * dt; m -= md * dt
                if p1 <= 0: est = 15; tsep = t; m -= self.SECO1; F = 0.0
            elif est == 15:
                ang = math.atan2(vt, vr)
                if t > tsep + 4: est = 2
            elif est == 2:
                F = self.F2; md = F / self.VE2
                beta = math.atan(math.tan(self.B0) - self.CC * (t - tsep - 4))
                ang = math.pi / 2 - beta
                p2 -= md * dt; m -= md * dt
                if vt >= math.sqrt(MU / r): est = 3; fim = t; F = 0.0
            else:
                ang = rows[-1][6]
            dirx = ux * math.cos(ang) + ex * math.sin(ang); diry = uy * math.cos(ang) + ey * math.sin(ang)
            rows.append((t, r - RT, math.hypot(vx, vy), vr, vt, m, ang, est, F, math.atan2(x, y) * RT,
                         p1 + max(0, p2), max(0.0, p1), max(0.0, p2)))
            ax = -MU * x / r ** 3 + F / m * dirx; ay = -MU * y / r ** 3 + F / m * diry
            vx += ax * dt; vy += ay * dt; x += vx * dt; y += vy * dt; t += dt
        self.a = np.array(rows)
        self.dt, self.tsep, self.tfim = dt, tsep, fim
        self.t2 = tsep + 4
        self.t100 = float(self.a[np.argmax(self.a[:, 1] > 100e3), 0])

    def _i(self, tf):
        return min(len(self.a) - 2, max(0, int(tf / self.dt)))

    def q(self, tf):
        """dict com h (m), v, vr, vt (m/s), m (kg), ang (rad do vertical), est, F, x (m), prop."""
        if tf <= 0:
            r = self.a[0]
            return dict(h=0.0, v=0.0, vr=0.0, vt=0.0, m=r[5], ang=0.0, est=1, F=0.0, x=0.0, prop=r[10],
                        p1=r[11], p2=r[12], tf=tf)
        i = self._i(tf); u = (tf - i * self.dt) / self.dt
        r = self.a[i] * (1 - u) + self.a[i + 1] * u
        est = int(self.a[i][7])
        return dict(h=r[1], v=r[2], vr=r[3], vt=r[4], m=r[5], ang=r[6], est=est, F=self.a[i][8], x=r[9],
                    prop=r[10], p1=r[11], p2=r[12], tf=tf)


VOO = Voo()


def estagio_de(q):
    return 1 if q['est'] == 1 else 2


# =================================================================== o foguete
def eixo(cx, cy, ang, k, ref=50.0):
    """Converte (s, u) do eixo do foguete em (x, y) da tela."""
    sa, ca = math.sin(ang), math.cos(ang)

    def f(s, u):
        d = (s - ref) * k
        return (cx + d * sa + u * k * ca, cy - d * ca + u * k * sa)
    return f


def _quad(f, s0, s1, u0, u1):
    return [f(s0, u0), f(s1, u0), f(s1, u1), f(s0, u1)]


# perfil do corpo: (s, meia-largura)
CORPO1 = [(8, 5), (56, 5)]
INTER = (56, 61)
CORPO2 = (61, 80)
COIFA = [(80, 5.3), (85, 5.3), (90, 4.7), (94, 3.6), (97, 2.3), (99, 1.0), (100, 0)]
SINO1 = [(0, 4.1), (2, 3.5), (4, 2.6), (6, 1.7), (7, 1.6), (8, 2.4)]
SINO2 = [(53, 3.5), (55, 2.8), (57, 2.0), (59, 1.2), (60, 1.2), (61, 2.0)]
# cores do casco, da esquerda (luz) para a direita (sombra), em faixas de u
FAIXAS = [(-1.0, -.78, ACO3, None), (-.78, -.45, CASCO, BRANCO), (-.45, .05, CASCO, None),
          (.05, .35, CASCO, CASCO2), (.35, .7, CASCO2, None), (.7, 1.0, ACO2, CASCO2)]


def _cilindro(tela, f, s0, s1, hw, faixas=FAIXAS, cores=None):
    for a, b, c1, c2 in faixas:
        if cores: c1, c2 = cores.get(c1, c1), (cores.get(c2, c2) if c2 is not None else None)
        pol(tela, _quad(f, s0, s1, a * hw, b * hw), c1, c2)


def _perfil_pts(f, perfil, lado=1):
    return [f(s, w * lado) for s, w in perfil]


def _sino(tela, f, perfil, quente=0.0):
    pts = _perfil_pts(f, perfil, 1) + _perfil_pts(f, perfil[::-1], -1)
    contorno(tela, pts, PRETO)
    pol(tela, pts, ACO1)
    # luz à esquerda, sombra à direita
    esq = [f(s, -w) for s, w in perfil] + [f(s, -w * .35) for s, w in perfil[::-1]]
    pol(tela, esq, ACO2, ACO3)
    dir_ = [f(s, w * .45) for s, w in perfil] + [f(s, w) for s, w in perfil[::-1]]
    pol(tela, dir_, ACO0)
    if quente > 0:
        # boca em brasa: a borda da tubeira esquenta
        s0, w0 = perfil[0]
        s1 = s0 + (perfil[1][0] - s0) * .8
        pts2 = [f(s0, -w0), f(s0, w0), f(s1, perfil[1][1]), f(s1, -perfil[1][1])]
        pol(tela, pts2, BRASA, VERMELHO if quente > .5 else ACO1)


class Foguete:
    """Foguete de 2 estágios. `desenhar(tela, cx, cy, ang, k, e)`; e (dict):
       st1 (bool) 1º estágio presente; sep (offset do 1º estágio: ds, du, giro)
       coifa (bool) / coifa_sep (abertura 0..1); corte (bool); niveis (o1, c1, o2, c2)
       chama1, chama2 (0..1); vacuo (0..1); t."""

    def __init__(self):
        pass

    def desenhar(self, tela, cx, cy, ang, k, e):
        t = e.get('t', 0.0)
        f = eixo(cx, cy, ang, k)
        vac = e.get('vacuo', 0.0)
        # ---- 1º estágio (pode estar se afastando)
        if e.get('st1', True):
            ds, du, giro = e.get('sep', (0.0, 0.0, 0.0))
            ang1 = ang + giro
            # centro do 1º estágio: gira em volta do seu meio (s=32)
            pc = f(32 + ds, du)
            f1 = eixo(pc[0], pc[1], ang1, k, ref=32)
            if e.get('chama1', 0) > 0:
                bx, by = f1(0, 0)
                chama(tela, bx, by, ang1, k, 4.1, e['chama1'], t, vac, seed=1)
            self._estagio1(tela, f1, e, k)
        # ---- 2º estágio + coifa
        sep_longe = (not e.get('st1', True)) or e.get('sep', (0.0,))[0] < -1.0
        if e.get('chama2', 0) > 0 and sep_longe:
            bx, by = f(53, 0)
            chama(tela, bx, by, ang, k, 3.5, e['chama2'], t, vac, seed=2)
        self._estagio2(tela, f, e, k, sino=sep_longe)

    # ------------------------------------------------------------------
    def _estagio1(self, tela, f, e, k):
        corte = e.get('corte', False)
        sil = [f(8, -5), f(61, -5), f(61, 5), f(8, 5)]
        aleta = [f(8, 5), f(17, 5), f(8, 9), f(4, 9)]
        aleta2 = [f(8, -5), f(17, -5), f(8, -9), f(4, -9)]
        for p in (sil, aleta, aleta2):
            contorno(tela, p, PRETO)
        _sino(tela, f, SINO1, e.get('quente1', 0.0))
        pol(tela, aleta, ACO0); pol(tela, aleta2, ACO1, ACO2)
        _cilindro(tela, f, 8, 56, 5)
        # interestágio (escuro) e faixas
        _cilindro(tela, f, 56, 61, 5, cores={CASCO: ACO1, CASCO2: ACO0, BRANCO: ACO2, ACO3: ACO2, ACO2: ACO0})
        for s in (8, 33.5):
            _cilindro(tela, f, s, s + 1.2, 5, cores={CASCO: ACO2, CASCO2: ACO1, BRANCO: ACO3, ACO3: ACO3, ACO2: ACO1})
        if corte:
            o1, c1 = e.get('niveis', (1, 1, 1, 1))[:2]
            self._tanque(tela, f, 35, 55, 4.1, o1, LOX, e.get('t', 0), 'o1' in e.get('acesos', ()))
            self._tanque(tela, f, 13, 33, 4.1, c1, RP1, e.get('t', 0), 'c1' in e.get('acesos', ()))
            # baía do motor: bombas e cano que desce do tanque de oxigênio
            pol(tela, _quad(f, 8.6, 12.4, -4.2, 4.2), FUNDO, FUNDO2)
            a, b = f(35, 2.6), f(11, 2.6)
            tela.linha(a[0], a[1], b[0], b[1], LOX)
            gx, gy = f(10.5, -1.6)
            gx2, gy2 = f(10.5, 1.8)
            r = max(1.0, 1.5 * k)
            luz = 'tb' in e.get('acesos', ())
            tela.disco(gx, gy, r + .6, PRETO); tela.disco(gx, gy, r, AMARELO if luz else LATAO)
            tela.disco(gx2, gy2, r + .6, PRETO); tela.disco(gx2, gy2, r, AMARELO if luz else LATAO)
            rot = e.get('t', 0) * 9
            tela.px(gx + math.cos(rot) * r * .6, gy + math.sin(rot) * r * .6, PRETO)
            tela.px(gx2 + math.cos(-rot) * r * .6, gy2 + math.sin(-rot) * r * .6, PRETO)
            # câmara
            cam = [f(6.5, -2.4), f(9, -2.4), f(9, 2.4), f(6.5, 2.4)]
            pol(tela, cam, CHAMA1 if 'cc' in e.get('acesos', ()) else ACO2, ACO1)

    def _tanque(self, tela, f, s0, s1, hw, nivel, cor, t, aceso=False):
        pol(tela, _quad(f, s0, s1, -hw - .6, hw + .6), PRETO)
        pol(tela, _quad(f, s0 + .3, s1 - .3, -hw, hw), FUNDO2, FUNDO)
        sl = s0 + .3 + (s1 - s0 - .6) * max(0.0, min(1.0, nivel))
        if nivel > 0.005:
            pol(tela, _quad(f, s0 + .3, sl, -hw, hw), cor)
            pol(tela, _quad(f, s0 + .3, sl, hw * .35, hw), cor, FUNDO3 if cor == LOX else LATAO)
            a, b = f(sl, -hw), f(sl, hw)
            tela.linha(a[0], a[1], b[0], b[1], BRANCO if cor == LOX else CHAMA0)
        if aceso:
            pts = _quad(f, s0, s1, -hw - .6, hw + .6)
            for i in range(4):
                a, b = pts[i], pts[(i + 1) % 4]
                tela.linha(a[0], a[1], b[0], b[1], AMARELO)

    def _estagio2(self, tela, f, e, k, sino=False):
        corte = e.get('corte', False)
        sil = [f(61, -5), f(80, -5), f(80, 5), f(61, 5)]
        contorno(tela, sil, PRETO)
        if sino:
            _sino(tela, f, SINO2, e.get('quente2', 0.0))
        _cilindro(tela, f, 61, 80, 5)
        _cilindro(tela, f, 78.8, 80, 5, cores={CASCO: ACO2, CASCO2: ACO1, BRANCO: ACO3, ACO3: ACO3, ACO2: ACO1})
        if corte:
            n = e.get('niveis', (1, 1, 1, 1))
            self._tanque(tela, f, 71, 78.5, 4.1, n[2], LOX, e.get('t', 0), '2' in e.get('acesos', ()))
            self._tanque(tela, f, 62.5, 70.5, 4.1, n[3], RP1, e.get('t', 0), '2' in e.get('acesos', ()))
        # coifa
        ab = e.get('coifa_sep', 0.0)
        if e.get('coifa', True):
            if ab <= 0:
                self._coifa(tela, f, k, corte, e)
            else:
                self._carga(tela, f, k)
                for lado in (-1, 1):
                    # cada metade gira para fora em volta da base e se afasta
                    a = ab * 1.4
                    ds, du = ab * 10, lado * ab * 14
                    pts = []
                    for s, w in COIFA:
                        ss, uu = s - 80, w * lado
                        rs = ss * math.cos(a) - uu * math.sin(a) * lado * -1
                        ru = ss * math.sin(a) * lado + uu * math.cos(a)
                        pts.append(f(80 + rs + ds, ru + du))
                    pts.append(f(80 + ds, du))
                    contorno(tela, pts, PRETO)
                    pol(tela, pts, CASCO if lado < 0 else CASCO2, BRANCO if lado < 0 else None)
        else:
            self._carga(tela, f, k)

    def _coifa(self, tela, f, k, corte, e):
        pts = [f(s, -w) for s, w in COIFA] + [f(s, w) for s, w in COIFA[::-1]]
        contorno(tela, pts, PRETO)
        pol(tela, pts, CASCO)
        luz = [f(s, -w) for s, w in COIFA] + [f(s, -w * .3) for s, w in COIFA[::-1]]
        pol(tela, luz, CASCO, BRANCO)
        som = [f(s, w * .45) for s, w in COIFA] + [f(s, w) for s, w in COIFA[::-1]]
        pol(tela, som, CASCO2, ACO3)
        a, b = f(80.4, -5.3), f(80.4, 5.3)
        tela.linha(a[0], a[1], b[0], b[1], ACO2)
        if corte:
            inner = [f(s, -w * .82) for s, w in COIFA[:-1]] + [f(s, w * .82) for s, w in COIFA[-2::-1]]
            pol(tela, inner, FUNDO, FUNDO2)
            self._carga(tela, f, k, 'cg' in e.get('acesos', ()))

    def _carga(self, tela, f, k, aceso=False):
        """Satélite genérico dobrado: caixa dourada com painel solar."""
        corpo = _quad(f, 82, 90, -2.8, 2.8)
        contorno(tela, corpo, PRETO)
        pol(tela, corpo, AMARELO if aceso else LATAO, OLEO1)
        pol(tela, _quad(f, 90, 93, -1.2, 1.2), ACO3)
        pol(tela, _quad(f, 83, 89, -4.0, -2.9), MISTURA, FUNDO3)
        pol(tela, _quad(f, 83, 89, 2.9, 4.0), MISTURA, FUNDO3)
        a, b = f(93, 0), f(95.5, 0)
        tela.linha(a[0], a[1], b[0], b[1], ACO4)


FOG = Foguete()


# =================================================================== chama
def chama(tela, x, y, ang, k, hw0, forca, t, vac=0.0, seed=0, comp=1.0):
    """Chama na boca da tubeira (x, y), saindo no sentido -eixo (oposto ao
    nariz). Embaixo: estreita, com diamantes de choque. No vácuo: abre."""
    if forca <= 0.01: return
    dx, dy = -math.sin(ang), math.cos(ang)          # -eixo
    nx, ny = math.cos(ang), math.sin(ang)
    w0 = hw0 * k
    L = k * (34 + 14 * forca) * forca * (1 + 1.2 * vac) * comp
    fl = .85 + .15 * math.sin(t * 37 + seed) * math.sin(t * 23 + 1.3 * seed)
    L *= fl
    n = 12

    def camada(Lc, abre, cor, c2=None, enc=0.0):
        esq, dir_ = [], []
        for i in range(n + 1):
            u = i / n
            s = u * Lc
            larg = w0 * (1 - enc) * (1 + abre * u) * (1 - u ** 2.2) + .6
            j = (hsh(int(t * 30) + i, seed) - .5) * 1.6 * u
            esq.append((x + dx * s - nx * (larg + j), y + dy * s - ny * (larg + j)))
            dir_.append((x + dx * s + nx * (larg - j), y + dy * s + ny * (larg - j)))
        pol(tela, esq + dir_[::-1], cor, c2)

    abre = .25 + 2.6 * vac
    brilho(tela, x + dx * L * .25, y + dy * L * .25, w0 * 2.2 + 4, LARANJA)
    camada(L, abre, CHAMA2, BRASA)
    camada(L * .78, abre * .9, CHAMA2)
    camada(L * .6, abre * .7, CHAMA1, enc=.2)
    camada(L * .38, abre * .4, CHAMA0, enc=.45)
    camada(L * .14, 0, BRANCO, enc=.55)
    if vac < .4 and forca > .5:
        # diamantes de choque
        for j in range(1, 4):
            s = L * (.18 + j * .16)
            cx, cy = x + dx * s, y + dy * s
            r = max(1.0, w0 * .45 * (1 - j * .18))
            pts = [(cx + dx * r * 1.6, cy + dy * r * 1.6), (cx + nx * r, cy + ny * r),
                   (cx - dx * r * 1.6, cy - dy * r * 1.6), (cx - nx * r, cy - ny * r)]
            pol(tela, pts, BRANCO if j == 1 else CHAMA0)


# =================================================================== céu do voo
class CeuVoo:
    """Fundo das cenas de voo: degradê que escurece com a altitude, nuvens que
    passam (paralaxe), estrelas acima de ~40 km e a borda curva da Terra."""
    CORES = [  # (altitude m, [(f, cor)...])
        (0, [(0, CEU2), (.6, CEU1), (1, CEU0)]),
        (6e3, [(0, CEU3), (.55, CEU2), (1, CEU1)]),
        (16e3, [(0, CEU4), (.5, CEU3), (1, CEU2)]),
        (30e3, [(0, CEU5), (.5, CEU4), (1, CEU3)]),
        (45e3, [(0, PRETO), (.5, CEU5), (1, CEU4)]),
        (65e3, [(0, PRETO), (.6, FUNDO), (1, CEU5)]),
        (90e3, [(0, PRETO), (.7, PRETO), (1, FUNDO)]),
    ]

    def __init__(self, seed=5):
        rng = np.random.default_rng(seed)
        self.estrelas = [(int(rng.integers(0, W)), int(rng.integers(0, PALCO_H)), float(rng.uniform(0, 6)))
                         for _ in range(110)]
        self.nuv = []
        for k in range(10):
            n = int(rng.integers(5, 9)); larg = rng.uniform(30, 70)
            d = []
            for j in range(n):
                dx = (j / (n - 1) - .5) * larg
                r = rng.uniform(5, 11) * (1 - abs(j / (n - 1) - .5) * .9)
                d.append((dx, -r * .5 + rng.uniform(-2, 2), r))
            self.nuv.append(d)

    def fundo(self, tela, q, t, x1=W):
        h = q['h']
        sel = self.CORES[0][1]
        for hh, c in self.CORES:
            if h >= hh: sel = c
        gradiente(tela, 0, 0, x1, PALCO_H, sel)
        vis = max(0.0, min(1.0, (h - 25e3) / 30e3))
        if vis > 0:
            for x, y, f in self.estrelas:
                if x < x1 and hsh(x, y) < vis and math.sin(t * 1.3 + f * 3) > -.6:
                    tela.px(x, y, BRANCO if f > 4.5 else ACO3)
        if h > 18e3:
            self.terra(tela, h, q.get('x', 0.0), t, x1)
        self.nuvens(tela, q, t, x1)

    def nuvens(self, tela, q, t, x1=W, cy=105):
        """Camadas de nuvens a 1,5, 4 e 8 km; passam para baixo enquanto ele sobe."""
        esc = .045                                  # px por metro (paralaxe)
        for j, hc in enumerate((1500.0, 4000.0, 8000.0)):
            y = cy + (q['h'] - hc) * esc
            if y < -30 or y > PALCO_H + 30: continue
            xo = q.get('x', 0.0) * esc * .6
            for i in range(-1, 6):
                idx = (i + j * 3) % len(self.nuv)
                xx = i * 110 + (j * 37) - xo % 110 + (idx * 13) % 30
                if xx > x1 + 40: continue
                self.nuvem(tela, xx, y + (idx * 5) % 12 - 6, self.nuv[idx], 1.0 + .2 * j)

    def nuvem(self, tela, x, y, discos, esc=1.0):
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc + 2, r * esc + 1, PRETO)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc + 1.5, r * esc, ACO3)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc, y + dy * esc, r * esc * .92, ACO4)
        for dx, dy, r in discos:
            tela.disco(x + dx * esc - 1.5, y + dy * esc - 1.5, r * esc * .6, BRANCO)

    def terra(self, tela, h, xm, t, x1=W):
        """Borda curva da Terra subindo na parte de baixo da tela."""
        u = max(0.0, min(1.0, (h - 18e3) / 160e3))
        topo = PALCO_H + 6 - 46 * u ** .6
        R = 2400 - 1900 * u
        terra_disco(tela, x1 / 2, topo + R, R, xm * 2e-5, x1, faixa=(int(topo) - 6, PALCO_H))


def terra_disco(tela, cx, cy, R, rot, x1=W, faixa=(0, PALCO_H), atm=True):
    """Disco da Terra: mar com nuvens em listras, terra, atmosfera azul na borda."""
    y0, y1 = max(0, int(faixa[0])), min(PALCO_H, int(faixa[1]))
    x0 = max(0, int(cx - R - 4)); xe = min(int(x1), int(cx + R + 5))
    if y1 <= y0 or xe <= x0: return
    yy, xx = np.mgrid[y0:y1, x0:xe]
    d = np.hypot(xx - cx, yy - cy)
    dentro = d <= R
    ang = np.arctan2(yy - cy, xx - cx)
    # textura: listras de nuvem e manchas de terra que correm com `rot`
    a = ang * R / 40.0 + rot
    rr = (R - d) / 18.0
    tex = np.sin(a * 1.7 + np.sin(rr * 1.3) * 2) + np.sin(a * .53 + rr * .7 + 1.0)
    cor = np.where(tex > 1.15, SOLO1, np.where(tex > .85, SOLO0, MAR1))
    nuv = np.sin(a * 2.9 + rr * 2.1) * np.sin(a * 1.1 - rr * .9)
    b = BAY[yy % 8, xx % 8]
    cor = np.where(nuv > .55 + b * .3, BRANCO, cor)
    cor = np.where((R - d < 2.5), np.where(b > .5, MAR2, CEU1), cor)
    sub = tela.buf[y0:y1, x0:xe]
    sub[dentro] = cor[dentro].astype(np.uint8)
    if atm:
        borda = (d > R) & (d < R + 3)
        sub[borda & (b < .7)] = CEU1
        borda2 = (d >= R + 3) & (d < R + 6) & (b < .35)
        sub[borda2] = CEU3


# =================================================================== plataforma
class Plataforma:
    """Chão da base: mar ao fundo (base no litoral), concreto, vala da chama e
    a torre de serviço treliçada. `gy` = y do chão na tela."""

    def desenhar(self, tela, gy, cx, t, braco=0.0, x1=W, k=1.1):
        if gy > PALCO_H + 120: return
        gyi = int(gy)
        # horizonte: mar e costa ao longe
        hz = gyi - 26
        if hz < PALCO_H:
            tela.ret(0, hz, x1, 4, MAR0)
            dither(tela, 0, hz + 4, x1, 4, MAR0, MAR1)
            tela.ret(0, hz + 8, x1, 18, CHAO1)
            dither(tela, 0, hz + 8, x1, 3, CHAO1, CHAO2)
            for i in range(0, x1, 9):
                hh = 3 + int(hsh(i, 2) * 5)
                tela.ret(i, hz + 8 - hh + 2, 6, hh, CHAO0)
        # concreto
        tela.ret(0, gyi, x1, PALCO_H - gyi + 2, CHAO0)
        tela.ret(int(cx - 60 * k), gyi, int(120 * k), 10, CONCRETO)
        tela.ret(int(cx - 60 * k), gyi, int(120 * k), 1, ACO4)
        dither(tela, cx - 60 * k, gyi + 6, 120 * k, 4, CONCRETO, ACO1)
        # vala da chama
        tela.ret(int(cx - 9 * k), gyi, int(18 * k), 10, PRETO)
        # torre à direita
        tx = int(cx + 16 * k)
        alt = int(86 * k)
        tw = int(10 * k)
        tela.ret(tx - 1, gyi - alt - 1, tw + 2, alt + 1, PRETO)
        tela.ret(tx, gyi - alt, tw, alt, FUNDO3)
        for yy in range(gyi - alt, gyi, int(6 * k) or 1):
            tela.linha(tx, yy, tx + tw - 1, yy + int(6 * k), ACO1)
            tela.linha(tx + tw - 1, yy, tx, yy + int(6 * k), ACO1)
            tela.ret(tx, yy, tw, 1, ACO2)
        tela.ret(tx, gyi - alt, 1, alt, ACO3)
        tela.ret(tx + tw - 1, gyi - alt, 1, alt, ACO0)
        tela.ret(tx - 3, gyi - alt - 4, tw + 6, 4, ACO1)
        tela.px(tx + tw // 2, gyi - alt - 6, VERMELHO if int(t * 2) % 2 else BRASA)
        # braço de serviço (gira para longe)
        ya = gyi - int(70 * k)
        L = (tx - (cx + 5 * k))
        bx = tx - L * math.cos(braco * 1.3)
        by = ya - L * math.sin(braco * 1.3)
        tela.linha(tx, ya, bx, by, ACO2)
        tela.linha(tx, ya + 1, bx, by + 1, ACO1)


def fumaca(tela, cx, gy, idade, t, x1=W, forca=1.0):
    """Nuvem de fumaça e vapor que sai da vala para os lados e cresce."""
    if idade <= 0: return
    n = 16
    for i in range(n):
        lado = -1 if i % 2 else 1
        h = hsh(i, 7)
        vida = min(idade, 6.0)
        dist = (14 + 70 * h) * (1 - math.exp(-vida * (.7 + h * .5))) * forca
        x = cx + lado * dist
        y = gy - 2 - (4 + 16 * hsh(i, 3)) * (1 - math.exp(-vida * .4)) - math.sin(t * .8 + i) * 1.5
        r = (5 + 8 * hsh(i, 9)) * min(1.0, .3 + vida * .5) * (.5 + .5 * forca)
        if x < -20 or x > x1 + 20: continue
        tela.disco(x, y + 1.5, r + 1, FUM2)
        tela.disco(x, y, r, FUM1)
        tela.disco(x - r * .25, y - r * .3, r * .7, FUM0)
        if dist < 40:
            brilho(tela, x, y, r * .8, LARANJA)


def rastro(tela, voo, tf, cx, cy, esc, t, x1=W, dur=2.0):
    """Fumaça deixada no ar (posições do passado, vistas da câmera de agora)."""
    q = voo.q(tf)
    if q['h'] > 40e3 or tf <= 0: return
    a = 1 - q['h'] / 40e3
    n = 44
    for i in range(n):
        tau = tf - (i + 1) / n * dur - (t * 30 % 1) / n * dur
        if tau < 0: break
        p = voo.q(tau)
        # ponto da tubeira no passado
        dx = (p['x'] - q['x']) * esc
        dy = (q['h'] - p['h']) * esc
        ex = -math.sin(p['ang']) * 30 * 1.1; ey = math.cos(p['ang']) * 30 * 1.1
        x = cx + dx + ex; y = cy + dy + ey
        if x < -20 or x > x1 + 20 or y < -20 or y > PALCO_H + 20: continue
        r = (3.2 + 7 * (i / n)) * a
        if r < 1: continue
        tela.disco(x, y + 1, r + .8, FUM2)
        tela.disco(x, y, r, FUM1 if i > n // 3 else FUM0)


# =================================================================== motor aberto (tubeira)
GAMA = 1.2


def area_mach(M):
    return (1 / M) * ((1 + .5 * (GAMA - 1) * M * M) / (.5 * (GAMA + 1))) ** ((GAMA + 1) / (2 * (GAMA - 1)))


def mach_de_area(ar, super_=False):
    lo, hi = (1.0, 8.0) if super_ else (1e-4, 1.0)
    for _ in range(60):
        mid = (lo + hi) / 2
        if (area_mach(mid) > ar) ^ super_: lo = mid
        else: hi = mid
    return (lo + hi) / 2


A0 = 1215.0           # velocidade do som na câmara (m/s): gás a ~3.500 K


def vel_gas(M):
    return M * A0 / math.sqrt(1 + .5 * (GAMA - 1) * M * M)


class Tubeira:
    """Motor aberto, de pé. Perfil em px: y do topo da câmara até a boca."""

    def __init__(self, cx=150, y_cam=78, y_gar=122, y_boca=186, hw_cam=30, hw_gar=7, razao=20.0):
        self.cx, self.yc, self.yg, self.yb = cx, y_cam, y_gar, y_boca
        self.hc, self.hg = hw_cam, hw_gar
        self.hb = hw_gar * math.sqrt(razao)
        self.razao = razao
        ys = np.arange(y_cam, y_boca + 1, .5)
        self.ys = ys
        self.hw = np.array([self.meia(y) for y in ys])
        M = []
        for y, w in zip(ys, self.hw):
            ar = max(1.0, (w / hw_gar) ** 2)
            M.append(mach_de_area(ar, super_=y > y_gar) if ar > 1.0001 else 1.0)
        self.M = np.array(M)
        self.v = np.array([vel_gas(m) for m in self.M])
        # trajetória de uma partícula: dy/dtau = max(vmin, v * c)
        c, vmin = 70.0 / vel_gas(mach_de_area(razao, True)), 14.0
        tau, y = [0.0], [y_cam + 2]
        while y[-1] < y_boca + 40:
            vv = max(vmin, self.v_em(y[-1]) * c)
            y.append(y[-1] + vv * .02); tau.append(tau[-1] + .02)
        self.p_tau, self.p_y = np.array(tau), np.array(y)
        self.vida = self.p_tau[-1]

    def meia(self, y):
        if y <= self.yc + 30: return self.hc
        if y <= self.yg:
            u = (y - self.yc - 30) / (self.yg - self.yc - 30)
            return self.hg + (self.hc - self.hg) * (math.cos(u * math.pi) * .5 + .5)
        u = (y - self.yg) / (self.yb - self.yg)
        return self.hg + (self.hb - self.hg) * (1 - (1 - u) ** 1.8) if u < 1 else self.hb

    def M_em(self, y):
        if y >= self.yb: return float(self.M[-1])
        return float(np.interp(y, self.ys, self.M))

    def v_em(self, y):
        if y >= self.yb: return float(self.v[-1])
        return float(np.interp(y, self.ys, self.v))

    def y_part(self, tau):
        return float(np.interp(tau, self.p_tau, self.p_y))

    def parede(self, tela, esp=4):
        cx = self.cx
        ys = list(range(self.yc, self.yb + 1))
        for lado in (-1, 1):
            ext = [(cx + lado * (self.meia(y) + esp), y) for y in ys]
            inn = [(cx + lado * self.meia(y), y) for y in ys[::-1]]
            pts = ext + inn
            contorno(tela, pts, PRETO)
            pol(tela, pts, ACO2 if lado < 0 else ACO1, ACO3 if lado < 0 else None)
            # canais de refrigeração (riscos)
            for y in range(self.yc + 6, self.yb, 5):
                x = cx + lado * (self.meia(y) + esp * .5)
                tela.px(x, y, ACO0 if lado < 0 else FUNDO3)
        # topo: placa injetora
        tela.ret(cx - self.hc - 5, self.yc - 5, 2 * self.hc + 10, 6, PRETO)
        tela.ret(cx - self.hc - 4, self.yc - 4, 2 * self.hc + 8, 4, ACO3)
        tela.ret(cx - self.hc - 4, self.yc - 4, 2 * self.hc + 8, 1, ACO4)
        for i in range(-self.hc + 3, self.hc - 2, 5):
            tela.px(cx + i, self.yc, PRETO)


# =================================================================== o globo
# contornos APROXIMADOS (lat, lon) — só para o desenho, o vídeo avisa
AM_SUL = [(12, -72), (11, -64), (10, -61), (8, -60), (5, -52), (2, -50), (0, -50), (-2, -44), (-3, -40),
          (-5, -35), (-8, -35), (-13, -38.5), (-18, -39.5), (-23, -42), (-25, -48), (-29, -49), (-33, -52),
          (-35, -57), (-39, -62), (-42, -64), (-47, -66), (-51, -69), (-55, -68), (-53, -74), (-46, -75),
          (-40, -73.5), (-30, -71.5), (-18, -70.3), (-14, -76), (-5, -81), (-1, -80), (2, -79), (7, -77.5),
          (9, -76), (11, -74)]
AM_NORTE = [(60, -60), (50, -56), (45, -66), (41, -70), (35, -76), (31, -81), (27, -80), (25.2, -80.4),
            (26.5, -82), (29.8, -84), (30.2, -88), (29.3, -94), (26, -97.3), (22, -97.8), (19, -96),
            (18.5, -91.5), (21.5, -90), (21.5, -87), (16, -88.5), (15.8, -84), (11, -83.7), (9.2, -79.8),
            (8, -77.4), (7.5, -80), (9, -85), (13, -87.5), (16, -95), (20, -105.5), (23, -106), (31, -113.5),
            (34, -120), (40, -124), (48, -125), (60, -140)]
AFRICA = [(35, -6), (37, 10), (32, 32), (30, 32.5), (22, 37), (12, 44), (11, 51), (2, 46), (-5, 39.5),
          (-10, 40), (-15, 40.5), (-25, 35), (-34, 26), (-34.8, 20), (-30, 17), (-22, 14), (-17, 11.8),
          (-12, 13.8), (-5, 12), (0, 9.5), (4, 9), (4.5, 6), (6, 1), (5, -4), (4.5, -7.5), (7, -12), (10, -15),
          (15, -17), (21, -17), (28, -13), (32, -9)]
EUROPA = [(36, -9.5), (43, -9), (44, -1.5), (48, -4.5), (51, 2), (54, 8), (60, 5), (70, 20), (70, 60),
          (40, 60), (37, 36), (36, 28), (38, 24), (40, 20), (38, 16), (44, 12), (43, 4), (36, -5)]
ALCANTARA = (-2.34, -44.42)
KENNEDY = (28.59, -80.65)


def _mascara_terra():
    from matplotlib.path import Path
    lats = np.arange(-90, 90, .5) + .25
    lons = np.arange(-180, 180, .5) + .25
    LO, LA = np.meshgrid(lons, lats)
    pts = np.stack([LO.ravel(), LA.ravel()], 1)
    m = np.zeros(LO.size, bool)
    for poly in (AM_SUL, AM_NORTE, AFRICA, EUROPA):
        m |= Path([(lo, la) for la, lo in poly]).contains_points(pts)
    return m.reshape(LO.shape)


TERRA_MASK = _mascara_terra()


def globo(tela, cx, cy, R, lon0, t=0.0, x1=W, linhas=True, equador=False, lat_marca=None, sombra=True):
    """Globo em projeção ortográfica (norte para cima). `lon0` = longitude do
    centro (graus). Diminuir lon0 com o tempo = a Terra girando para o leste."""
    x0, xe = max(0, int(cx - R - 1)), min(int(x1), int(cx + R + 2))
    y0, ye = max(0, int(cy - R - 1)), min(PALCO_H, int(cy + R + 2))
    if xe <= x0 or ye <= y0: return
    yy, xx = np.mgrid[y0:ye, x0:xe]
    X = (xx + .5 - cx) / R; Y = -(yy + .5 - cy) / R
    rr = X * X + Y * Y
    dentro = rr <= 1.0
    Z = np.sqrt(np.clip(1 - rr, 0, 1))
    lat = np.degrees(np.arcsin(np.clip(Y, -1, 1)))
    lon = (np.degrees(np.arctan2(X, Z)) + lon0 + 180) % 360 - 180
    ia = np.clip(((lat + 90) * 2).astype(int), 0, 359); io = np.clip(((lon + 180) * 2).astype(int), 0, 719)
    terra = TERRA_MASK[ia, io]
    b = BAY[yy % 8, xx % 8]
    luz = (-X * .55 + Y * .35 + Z * .76)                       # sol à esquerda e acima
    cor = np.where(terra, np.where(luz > .55 + b * .25, SOLO1, SOLO0), np.where(luz > .6 + b * .25, MAR2, MAR1))
    if sombra:
        cor = np.where(luz < -.05 + b * .3, np.where(terra, CHAO0, MAR0), cor)
    if linhas:
        g1 = (np.abs(((lon + 180) % 30) - 15) > 14.2) | (np.abs(((lat + 90) % 30) - 15) > 14.2)
        cor = np.where(g1 & (b < .5), np.where(terra, CHAO1, MAR0), cor)
    if equador:
        e = (np.abs(lat) < .9) & (b < .75)
        cor = np.where(e, AMARELO, cor)
    if lat_marca is not None:
        e = (np.abs(lat - lat_marca) < .8) & (b < .5)
        cor = np.where(e, LARANJA, cor)
    borda = dentro & (rr > (1 - 2.2 / R) ** 2)
    cor = np.where(borda, np.where(b < .6, CEU1, MAR2), cor)
    sub = tela.buf[y0:ye, x0:xe]
    sub[dentro] = cor[dentro].astype(np.uint8)
    halo = (~dentro) & (rr < (1 + 3.0 / R) ** 2) & (b < .5)
    sub[halo] = CEU3


def globo_xy(cx, cy, R, lon0, lat, lon):
    """Tela de um ponto (lat, lon) no globo; None se estiver atrás."""
    la, lo = math.radians(lat), math.radians(lon - lon0)
    Z = math.cos(la) * math.cos(lo)
    if Z < 0: return None
    return cx + R * math.cos(la) * math.sin(lo), cy - R * math.sin(la)
