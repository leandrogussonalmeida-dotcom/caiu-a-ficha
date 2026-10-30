#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep05 — o desenho da geladeira (em corte) e do circuito.

Uma variável manda no circuito inteiro: a posição `s` da porção de fluido
no circuito, de 0 a 4 (uma unidade por etapa):

  0..1  compressor     gás: 0,6 -> 6 bar, -25 -> mais de 45 °C
  1..2  condensador    6 bar; esfria até 45 °C e vira líquido
  2..3  tubo capilar   6 -> 0,6 bar; 45 -> -25 °C; um pouco já ferve
  3..4  evaporador     0,6 bar, -25 °C; ferve até virar gás

`estado(s)` devolve temperatura, pressão e fração de gás; o cano é pintado
com a mesma função (cada ponto do cano tem o seu s), então a cor do cano e o
painel nunca discordam. Valores: NIST (pressão de saturação do isobutano) e a
faixa de evaporação e condensação de um compressor de geladeira a R-600a.

`Tubo` rasteriza um cano uma vez (para cada pixel: posição ao longo do cano e
distância ao eixo); por quadro só se pinta o conteúdo: gás = pontinhos que
correm, líquido = cheio por baixo (cano deitado), bolhas onde ferve.
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
import idioma as I

ETAPAS = [('COMPRESSOR', VERMELHO), ('CONDENSADOR', LARANJA), ('TUBO CAPILAR', VERDE), ('EVAPORADOR', CIANO)]
P_BAIXA, P_ALTA = 0.6, 6.0           # bar (absoluta): saturação do isobutano a -25 e a 45 °C (NIST)
T_EVAP, T_COND, T_DESC = -25.0, 45.0, 65.0
T_COZINHA = 25.0


# ================================================================ estado do fluido
def estado(s):
    """(T °C, P bar, vapor 0..1, etapa) da porção na posição s (0..4)."""
    s = s % 4.0
    k = int(s); u = s - k
    if k == 0:
        q = suave(u)
        P = P_BAIXA * (P_ALTA / P_BAIXA) ** q
        T = T_EVAP + (T_DESC - T_EVAP) * q
        vap = 1.0
    elif k == 1:
        P = P_ALTA
        T = T_DESC - (T_DESC - T_COND) * min(1.0, u / .22) if u < .22 else T_COND
        vap = 1.0 if u < .22 else max(0.0, 1 - (u - .22) / .66)
    elif k == 2:
        q = suave(u)
        P = P_ALTA - (P_ALTA - P_BAIXA) * q
        T = T_COND - (T_COND - T_EVAP) * q
        vap = .2 * max(0.0, (u - .35) / .65)
    else:
        P, T = P_BAIXA, T_EVAP
        vap = min(1.0, .2 + .8 * u / .85)
    return T, P, vap, k


def estado_vet(s):
    s = np.asarray(s, float) % 4.0
    out = [estado(x) for x in s]
    return (np.array([o[0] for o in out]), np.array([o[1] for o in out]), np.array([o[2] for o in out]))


_LIM = [(-15, MISTURA), (-2, CIANO), (12, MISTURA2), (30, AMARELO), (42, CHAMA1), (52, LARANJA)]


def cor_temp(T):
    for lim, c in _LIM:
        if T <= lim: return c
    return VERMELHO


def cor_temp_vet(T):
    T = np.asarray(T)
    conds = [T <= lim for lim, _ in _LIM]
    return np.select(conds, [c for _, c in _LIM], VERMELHO).astype(np.uint8)


CLARA = {MISTURA: MISTURA2, CIANO: MISTURA2, MISTURA2: BRANCO, AMARELO: CHAMA0, CHAMA1: AMARELO,
         LARANJA: CHAMA1, VERMELHO: ROSA}


def fmt_bar(P):
    if abs(P - P_ALTA) < .05: return '6 BAR'
    if abs(P - P_BAIXA) < .02: return '0,6 BAR'
    return f"{I.decimal(P, 1)} BAR"


def fmt_temp(T):
    if T > T_COND + .5: return '> 45 °C'
    return f"{int(round(T))} °C"


def fmt_fase(vap):
    if vap >= .995: return 'GÁS'
    if vap <= .005: return 'LÍQUIDO'
    return 'LÍQUIDO + GÁS'


# ================================================================ trajetos e canos
class Trajeto:
    def __init__(self, pts):
        self.p = np.array(pts, float)
        seg = np.hypot(*np.diff(self.p, axis=0).T)
        self.cum = np.concatenate([[0.0], np.cumsum(seg)])
        self.L = float(self.cum[-1])

    def em(self, u):
        d = min(max(u, 0.0), 1.0) * self.L
        i = int(min(np.searchsorted(self.cum, d, 'right') - 1, len(self.p) - 2))
        f = (d - self.cum[i]) / max(1e-9, self.cum[i + 1] - self.cum[i])
        x, y = self.p[i] + (self.p[i + 1] - self.p[i]) * f
        return float(x), float(y)

    def amostras(self, passo=.5):
        n = max(2, int(self.L / passo) + 1)
        ds = np.linspace(0, self.L, n)
        xs = np.interp(ds, self.cum, self.p[:, 0]); ys = np.interp(ds, self.cum, self.p[:, 1])
        return xs, ys, ds / max(self.L, 1e-9)


def serpentina(xa, xb, y0, passo, linhas, nb=12):
    """Cano em zigue-zague: linhas retas de xa a xb (e volta), curvas em U por fora."""
    pts, r = [], passo / 2.0
    for k in range(linhas):
        y = y0 + k * passo
        a, b = (xa, xb) if k % 2 == 0 else (xb, xa)
        pts += [(a, y), (b, y)]
        if k < linhas - 1:
            sg = 1 if b > a else -1
            for j in range(1, nb):
                ang = math.pi * j / nb
                pts.append((b + sg * r * math.sin(ang), y + r - r * math.cos(ang)))
    return pts


class Tubo:
    """Cano rasterizado: para cada pixel, u (0..1 ao longo), distância ao eixo
    e dy (altura em relação ao eixo, para o líquido deitar no fundo)."""

    def __init__(self, pts, r):
        self.tr = Trajeto(pts); self.r = float(r)
        xs, ys, us = self.tr.amostras(.5)
        R = self.r + .01
        x0, x1 = int(math.floor(xs.min() - R - 1)), int(math.ceil(xs.max() + R + 1))
        y0, y1 = int(math.floor(ys.min() - R - 1)), int(math.ceil(ys.max() + R + 1))
        h, w = y1 - y0 + 1, x1 - x0 + 1
        best = np.full((h, w), 1e9); U = np.zeros((h, w)); DY = np.zeros((h, w))
        ri = int(math.ceil(R)) + 1
        for x, y, u in zip(xs, ys, us):
            cx, cy = int(round(x)) - x0, int(round(y)) - y0
            a0, a1 = max(0, cy - ri), min(h, cy + ri + 1)
            b0, b1 = max(0, cx - ri), min(w, cx + ri + 1)
            yy, xx = np.mgrid[a0:a1, b0:b1]
            px, py = xx + x0 + .5, yy + y0 + .5
            d = np.hypot(px - x - .5, py - y - .5)
            sub = best[a0:a1, b0:b1]
            m = d < sub
            sub[m] = d[m]
            U[a0:a1, b0:b1][m] = u
            DY[a0:a1, b0:b1][m] = (py - y - .5)[m]
        m = best <= R
        iy, ix = np.nonzero(m)
        self.Y, self.X = iy + y0, ix + x0
        self.U, self.D, self.DY = U[m], best[m], DY[m]
        self.S = self.U * self.tr.L
        ok = (self.Y >= 0) & (self.Y < H) & (self.X >= 0) & (self.X < W)
        for nome in ('Y', 'X', 'U', 'D', 'DY', 'S'):
            setattr(self, nome, getattr(self, nome)[ok])

    def desenhar(self, tela, T, vap, t, vel=20.0, ferve=None, apagado=0.0):
        """T, vap: arrays por pixel (ou escalares). ferve: array bool (bolhas)."""
        r = self.r
        T = np.broadcast_to(np.asarray(T, float), self.U.shape)
        vap = np.broadcast_to(np.asarray(vap, float), self.U.shape)
        c = cor_temp_vet(T)
        clara = np.vectorize(lambda k: CLARA.get(int(k), BRANCO), otypes=[np.uint8])(c) if c.size else c
        out = np.full(self.U.shape, PRETO, np.uint8)
        S, DY, D = self.S, self.DY, self.D
        mov = S - t * vel
        if r < 3.6:
            dentro = D <= r - 1.0
            gas_pt = ((np.floor(mov) + np.floor(DY + 9)) % 2 == 0)
            liq = vap < .5
            out[dentro & liq] = c[dentro & liq]
            g = dentro & ~liq
            out[g] = np.where(gas_pt[g] | (vap[g] < .8), c[g], FUNDO3)
            if apagado > 0:
                pm = dentro & (((self.X + self.Y) % 2) == 0) & (apagado > .5)
                out[pm] = FUNDO3
        else:
            Ri = r - 2.0
            parede = (D > r - 2.0) & (D <= r - .8)
            out[parede] = ACO2
            out[parede & (DY < -.5)] = ACO4
            out[parede & (DY > .5)] = ACO1
            dentro = D <= r - 2.0
            nivel = (1 - 2 * (1 - vap)) * Ri               # líquido: abaixo do nível
            liq = dentro & (DY > nivel)
            gas = dentro & ~liq
            out[gas] = FUNDO2
            pts = gas & ((mov + (DY * 2.3).astype(int) * 3) % 6 < 1.0) & ((np.round(DY) % 2) == 0)
            out[pts] = c[pts]
            out[liq] = c[liq]
            sup = liq & (DY <= nivel + 1.0) & (vap > .01)
            out[sup] = clara[sup]
            onda = liq & ((mov * .7 + DY * 5) % 11 < 1) & (DY > nivel + 1.5)
            out[onda] = clara[onda]
            if ferve is not None:
                fv = np.broadcast_to(np.asarray(ferve, bool), self.U.shape)
                k = np.floor((S - t * vel * 1.3) / 5)
                bol = liq & fv & ((S - t * vel * 1.3) % 5 < 1.6) & (np.abs(DY - ((k * 7) % (2 * Ri) - Ri)) < 1.0)
                out[bol] = BRANCO
        tela.buf[self.Y, self.X] = out


# ================================================================ peças pequenas
def calor(tela, x, y, brilho=1):
    """Uma 'pitada' de calor: cruz laranja com miolo claro."""
    x, y = int(x), int(y)
    tela.ret(x - 1, y, 3, 1, LARANJA); tela.ret(x, y - 1, 1, 3, LARANJA)
    tela.px(x, y, CHAMA0 if brilho else CHAMA1)


def floco(tela, x, y, cor=MISTURA2):
    x, y = int(x), int(y)
    tela.px(x, y, BRANCO); tela.px(x - 1, y, cor); tela.px(x + 1, y, cor); tela.px(x, y - 1, cor); tela.px(x, y + 1, cor)


def parcela(tela, x, y, T, vap, t, r=3.5):
    """A protagonista: uma porção de fluido. Gás = nuvem de pontos que giram,
    líquido = gota cheia; brilha na cor da temperatura."""
    c = cor_temp(T); cl = CLARA.get(c, BRANCO)
    pis = int(t * 4) % 2
    tela.anel(x, y, r + 3, BRANCO if pis else c, .6)
    if vap > .6:
        for k in range(6):
            a = t * 3 + k * math.pi / 3
            px_, py_ = x + math.cos(a) * r * .9, y + math.sin(a) * r * .9
            tela.ret(int(px_) - 1, int(py_) - 1, 3, 3, PRETO)
            tela.px(px_, py_, c)
        tela.ret(int(x) - 1, int(y) - 1, 3, 3, PRETO); tela.px(x, y, cl)
    else:
        tela.disco(x, y, r + 1, PRETO)
        tela.disco(x, y, r, c)
        tela.px(x - 1, y - 2, cl); tela.px(x - 2, y - 1, cl)
        if vap > .02:
            tela.px(x + 1, y + 1, BRANCO)
            if int(t * 6) % 2: tela.px(x - 1, y + 2, BRANCO)


def seta(tela, x, y, dirx, diry, cor, tam=5):
    """Setinha cheia apontando em (dirx, diry) (um dos 4 sentidos)."""
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if diry:
            yy = y + (k if diry > 0 else -k)
            tela.ret(x - w // 2, yy, w, 1, cor)
        else:
            xx = x + (k if dirx > 0 else -k)
            tela.ret(xx, y - w // 2, 1, w, cor)


def termometro(tela, x, y, h, frac, cor, fundo=FUNDO2):
    """Termômetro vertical: tubo de altura h com bulbo embaixo (x, y = topo)."""
    tela.ret(x - 3, y - 1, 7, h + 2, PRETO)
    tela.ret(x - 2, y, 5, h, fundo)
    tela.disco(x, y + h + 3, 5, PRETO)
    tela.disco(x, y + h + 3, 4, cor)
    n = int(round(max(0.0, min(1.0, frac)) * (h - 2)))
    tela.ret(x - 1, y + h - n, 3, n + 1, cor)
    tela.px(x - 1, y + h + 1, CLARA.get(cor, BRANCO))
    for k in range(0, h, 6):
        tela.ret(x + 3, y + k, 2, 1, ACO2)


def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com bolinha na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.disco(x1, y1, 1.6, cor)


def painel_estado(tela, k, T, P, vap, prog, x0=302, titulo=True):
    """Painel da direita: etapa, pressão, temperatura, estado e o trilho das 4 etapas."""
    nome, cor = ETAPAS[k]
    tela.texto(f"ETAPA {k + 1} DE 4", x0, 8, ACO3, tam=17, contorno=PRETO)
    tela.texto(nome, x0, 28, cor, tam=17, contorno=PRETO)
    # pressão
    tela.texto('PRESSÃO', x0, 52, ACO3, tam=9, contorno=PRETO)
    tela.texto(fmt_bar(P), x0, 62, BRANCO, tam=17, contorno=PRETO)
    tela.ret(x0, 80, 150, 5, PRETO); tela.ret(x0 + 1, 81, 148, 3, FUNDO2)
    n = int(148 * min(1.0, P / 7.0))
    tela.ret(x0 + 1, 81, n, 3, ROXO if P > 3 else ACO3)
    # temperatura
    c = cor_temp(T)
    tela.texto('TEMPERATURA', x0, 92, ACO3, tam=9, contorno=PRETO)
    tela.texto(fmt_temp(T), x0, 102, c, tam=17, contorno=PRETO)
    tela.ret(x0, 120, 150, 5, PRETO)
    for j in range(148):
        TT = -30 + j / 147 * 100
        tela.ret(x0 + 1 + j, 121, 1, 3, cor_temp(TT) if (j % 2 == 0 or True) else FUNDO2)
    jx = int((min(70, max(-30, T)) + 30) / 100 * 147)
    tela.ret(x0 + jx - 1, 118, 3, 9, BRANCO); tela.ret(x0 + jx, 119, 1, 7, PRETO)
    # estado
    tela.texto('ESTADO', x0, 132, ACO3, tam=9, contorno=PRETO)
    tela.texto(fmt_fase(vap), x0, 142, MISTURA2 if vap < .995 else ACO4, tam=17, contorno=PRETO)
    # trilho das etapas
    for j, (nm, cc) in enumerate(ETAPAS):
        x = x0 + j * 40
        aceso = j == k
        tela.ret(x, 166, 34, 16, cc if aceso else FUNDO2)
        tela.ret_vazado(x, 166, 34, 16, cc)
        tela.texto(str(j + 1), x + 14, 170, PRETO if aceso else cc, tam=9)
    xp = x0 + int(min(159, max(0, (k + prog) * 40)))
    tela.ret(x0, 188, 154, 1, ACO1)
    tela.disco(xp, 188, 3, PRETO); tela.disco(xp, 188, 2, cor_temp(T))


# ================================================================ cenário
def fundo_cozinha(tela, piso=198):
    """Parede de azulejo escura e piso de madeira."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 16):
        tela.ret(x, 0, 1, piso, FUNDO2)
    for y in range(8, piso, 12):
        tela.ret(0, y, W, 1, FUNDO2)
    tela.ret(0, piso - 30, W, 2, FUNDO3)                    # rodameio
    dither(tela, 0, piso, W, PALCO_H - piso, OLEO0, FUNDO)
    tela.ret(0, piso, W, 1, LATAO)
    for x in range(-8, W, 37):
        tela.ret(x, piso + 1, 1, PALCO_H - piso, PRETO)


# ================================================================ a geladeira em corte
class Geladeira:
    """Geladeira de duas portas vista de lado, com a lateral removida.
    Frente (porta) à esquerda, costas (condensador, compressor) à direita."""

    X0, X1, Y0, Y1 = 60, 192, 14, 194       # gabinete

    def __init__(self, dx=0, dy=0):
        self.dx, self.dy = dx, dy
        D = lambda pts: [(x + dx, y + dy) for x, y in pts]
        e1 = D([(198, 186), (206, 186), (212, 184), (216, 178), (219, 172)])
        e2 = D([(219, 172), (219, 166), (238, 166), (238, 26), (226, 26)] + serpentina(226, 204, 26, 8, 17))
        e3 = D([(204, 154), (204, 160), (195, 160), (195, 24), (182, 24), (182, 26)])
        e4 = D(serpentina(182, 166, 26, 6, 6) + [(189, 56), (189, 186), (198, 186)])
        self.trajs = [Trajeto(p) for p in (e1, e2, e3, e4)]
        self.tubos = [Tubo(e2, 2.5), Tubo(e3, 1.6), Tubo(e4, 2.5)]
        self.tubo_k = [1, 2, 3]
        self.s_px = []
        for tb, k in zip(self.tubos, self.tubo_k):
            ss = k + np.clip(tb.U, 0, .9999)
            Tv, Pv, Vv = estado_vet(np.round(ss, 3))
            self.s_px.append((Tv, Vv))
        rng = np.random.default_rng(5)
        self.rng_pts = rng.uniform(0, 1, (40, 3))

    def pos(self, s):
        s = s % 4.0
        k = int(s)
        return self.trajs[k].em(s - k)

    # ------------------------------------------------------------ peças
    def X(self, x): return x + self.dx
    def Y(self, y): return y + self.dy

    def _r(self, tela, x, y, w, h, c): tela.ret(self.X(x), self.Y(y), w, h, c)
    def _d(self, tela, x, y, w, h, c1, c2): dither(tela, self.X(x), self.Y(y), w, h, c1, c2)

    def condensador_fios(self, tela):
        for x in range(207, 225, 3):
            self._r(tela, x, 22, 1, 137, ACO0)
        self._r(tela, 206, 22, 20, 1, ACO1); self._r(tela, 206, 158, 20, 1, ACO1)

    def compressor(self, tela, t, ligado=True, d=(0, 0)):
        tr = int(math.sin(t * 90) > 0) if ligado else 0
        x0, y0 = 197 + d[0] + tr, 171 + d[1]
        cx = self.X(x0 + 18); cy = self.Y(y0 + 14)
        # cúpula: elipse em cima de um corpo
        pts = [(cx + 18 * math.cos(a), cy - 13 * math.sin(a)) for a in np.linspace(0, math.pi, 20)]
        pts += [(cx - 18, cy + 12), (cx + 18, cy + 12)]
        poligono(tela, [(x, y) for x, y in pts[:20]] + [(cx - 18, cy + 12), (cx + 18, cy + 12)], PRETO)
        pts2 = [(cx + 16.5 * math.cos(a), cy - 11.5 * math.sin(a)) for a in np.linspace(0, math.pi, 20)]
        poligono(tela, pts2 + [(cx - 16.5, cy + 11), (cx + 16.5, cy + 11)], ACO0)
        dither(tela, cx - 16, cy - 10, 14, 20, ACO1, ACO0)
        tela.ret(cx - 12, cy - 9, 6, 1, ACO2); tela.ret(cx - 14, cy - 7, 2, 4, ACO2)
        tela.ret(cx - 20, cy + 11, 40, 3, ACO1); tela.ret(cx - 20, cy + 11, 40, 1, ACO2)
        # caixinha elétrica e luz de ligado
        tela.ret(cx + 8, cy - 2, 8, 7, PRETO); tela.ret(cx + 9, cy - 1, 6, 5, FUNDO3)
        tela.ret(cx + 11, cy + 1, 2, 2, VERDE if ligado else BRASA)
        if ligado and int(t * 3) % 2 == 0: tela.px(cx + 11, cy, BRANCO)

    def gabinete(self, tela, t, porta=0.0, luz=False, comida=True, temp_dentro=4.0):
        X, Y = self.X, self.Y
        x0, x1, y0, y1 = self.X0, self.X1, self.Y0, self.Y1
        # pés
        for x in (64, 182):
            self._r(tela, x, 194, 6, 4, PRETO)
        # casca e isolamento
        self._r(tela, x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
        self._d(tela, x0, y0, x1 - x0, y1 - y0, CHAMA0, CERAMICA)
        self._r(tela, x0, y0, x1 - x0, 1, BRANCO)
        self._r(tela, x1 - 1, y0, 1, y1 - y0, ACO3)
        # interiores (frios)
        frio = (FUNDO2, FUNDO3)
        cz = (20, 62); gd = (70, 188)
        for (a, b) in (cz, gd):
            self._r(tela, 65, a - 1, 122, b - a + 2, ACO2)
            self._d(tela, 66, a, 120, b - a, *frio)
        if luz:
            self._r(tela, 74, 71, 10, 3, AMARELO)
            for k in range(3):
                self._d(tela, 70 + k * 4, 74 + k * 6, 22 - k * 8, 6, FUNDO3, ACO0)
        # prateleiras de vidro
        for y in (104, 136, 162):
            self._r(tela, 66, y, 120, 2, ACO3); self._r(tela, 66, y, 120, 1, ACO4)
        # gaveta de baixo
        self._r(tela, 70, 166, 108, 20, ACO1); self._r(tela, 71, 167, 106, 18, FUNDO3)
        self._r(tela, 70, 166, 108, 1, ACO3)
        if comida: self._comida(tela, t)
        # pés do gabinete no chão
        self._r(tela, x0, y1, x1 - x0, 1, ACO0)

    def _comida(self, tela, t):
        r = self._r
        # congelador: forma de gelo e caixa
        r(tela, 74, 52, 30, 10, PRETO); r(tela, 75, 53, 28, 8, MISTURA2)
        for k in range(4): r(tela, 76 + k * 7, 54, 5, 5, BRANCO); r(tela, 76 + k * 7, 58, 5, 1, MISTURA2)
        r(tela, 110, 34, 28, 28, PRETO); r(tela, 111, 35, 26, 26, ROXO); r(tela, 111, 35, 26, 2, ROSA)
        r(tela, 115, 44, 18, 6, CERAMICA); r(tela, 116, 46, 10, 1, ROXO)
        # 1ª prateleira: garrafa, leite, queijo
        r(tela, 72, 76, 10, 28, PRETO); r(tela, 73, 82, 8, 21, VERDE); r(tela, 75, 77, 4, 5, VERDE)
        r(tela, 74, 84, 2, 14, AGUA1)
        r(tela, 90, 82, 18, 22, PRETO); r(tela, 91, 83, 16, 20, BRANCO); r(tela, 91, 89, 16, 6, CIANO)
        poligono(tela, [(self.X(90), self.Y(83)), (self.X(99), self.Y(76)), (self.X(108), self.Y(83))], PRETO)
        poligono(tela, [(self.X(92), self.Y(83)), (self.X(99), self.Y(78)), (self.X(106), self.Y(83))], ACO4)
        poligono(tela, [(self.X(116), self.Y(104)), (self.X(140), self.Y(104)), (self.X(140), self.Y(92))], AMARELO)
        r(tela, 128, 99, 2, 2, CHAMA1); r(tela, 134, 101, 2, 2, CHAMA1)
        # 2ª prateleira: maçãs e pote
        for k in range(3):
            cx = self.X(80 + k * 13); cy = self.Y(130)
            tela.disco(cx, cy, 6, PRETO); tela.disco(cx, cy, 5, VERMELHO); tela.px(cx - 2, cy - 2, ROSA)
            tela.ret(cx, cy - 7, 1, 2, OLEO1)
        r(tela, 128, 118, 30, 18, PRETO); r(tela, 129, 119, 28, 17, LARANJA); r(tela, 129, 119, 28, 3, CHAMA1)
        # 3ª: jarra
        r(tela, 150, 140, 20, 22, PRETO); r(tela, 151, 141, 18, 21, AGUA0); r(tela, 151, 146, 18, 15, CIANO)
        r(tela, 152, 147, 2, 12, MISTURA2)
        # gaveta: verduras
        for k in range(6):
            cx = self.X(80 + k * 16); cy = self.Y(176 + (k % 2) * 3)
            tela.disco(cx, cy, 6, PRETO); tela.disco(cx, cy, 5, VERDE); tela.px(cx - 2, cy - 2, AGUA1)

    def portas(self, tela, abre=0.0):
        """Porta fechada: faixa de 6 px na frente. Aberta: gira para o lado de
        quem olha; de perfil ela vira um painel que cresce para a esquerda."""
        for (a, b) in ((14, 64), (66, 194)):
            w = int(6 + abre * 52) if b > 100 else 6
            x = self.X0 - w
            self._r(tela, x - 1, a - 1, w + 1, b - a + 2, PRETO)
            self._d(tela, x, a, w, b - a, CERAMICA, CHAMA0)
            self._r(tela, x, a, w, 1, BRANCO)
            if w > 12:                                     # face de dentro, com prateleiras da porta
                self._r(tela, x + 2, a + 4, w - 4, b - a - 8, ACO2)
                self._d(tela, x + 3, a + 5, w - 6, b - a - 10, FUNDO2, FUNDO3)
                for k, y in enumerate((a + 40, a + 80, a + 112)):
                    self._r(tela, x + 3, y, w - 6, 3, ACO3)
                    for j in range(max(0, (w - 10) // 9)):
                        cc = (VERDE, BRANCO, CHAMA1)[(j + k) % 3]
                        self._r(tela, x + 5 + j * 9, y - 12, 6, 12, PRETO)
                        self._r(tela, x + 6 + j * 9, y - 11, 4, 11, cc)
                self._r(tela, x - 4, a + 30, 4, 26, PRETO); self._r(tela, x - 3, a + 31, 2, 24, ACO3)
            else:
                self._r(tela, x - 4, a + 10, 4, 22, PRETO); self._r(tela, x - 3, a + 11, 2, 20, ACO3)
            self._r(tela, self.X0, a, 1, b - a, PRETO)              # borracha

    # ------------------------------------------------------------ circuito
    def canos(self, tela, t, vel=20.0, ligado=True, so=None, apagado=0.0):
        v = vel if ligado else 0.0
        for j, (tb, k) in enumerate(zip(self.tubos, self.tubo_k)):
            if so is not None and k not in so: continue
            Tv, Vv = self.s_px[j]
            ferve = (k == 3)
            tb.desenhar(tela, Tv, Vv, t, vel=v, apagado=apagado)

    def desenhar(self, tela, t, s=None, ligado=True, porta=0.0, pecas=None, vel=20.0, luz=None,
                 desloc=None, gelo=0.0, comida=True, apagado=0.0):
        """pecas = conjunto entre {'compressor','condensador','capilar','evaporador','fluido'} (None = tudo)."""
        ve = lambda n: pecas is None or n in pecas
        dz = desloc or {}
        fluido = ve('fluido')
        if ve('condensador'):
            self._desloc(tela, dz.get('condensador'), lambda: self.condensador_fios(tela))
        self.gabinete(tela, t, porta, luz=(porta > .3) if luz is None else luz, comida=comida)
        # canos: sem fluido, ficam cinza
        so = set()
        if ve('condensador'): so.add(1)
        if ve('capilar'): so.add(2)
        if ve('evaporador'): so.add(3)
        for j, (tb, k) in enumerate(zip(self.tubos, self.tubo_k)):
            if k not in so: continue
            d = dz.get(('condensador', 'capilar', 'evaporador')[k - 1])
            if d and d != (0, 0): continue
            if fluido:
                Tv, Vv = self.s_px[j]
                tb.desenhar(tela, Tv, Vv, t, vel=vel if ligado else 0.0, apagado=apagado)
            else:
                tb.desenhar(tela, 20.0, 0.0, t, vel=0.0)
                tela.buf[tb.Y[tb.D <= tb.r - 1.0], tb.X[tb.D <= tb.r - 1.0]] = ACO2
        for nome in ('condensador', 'capilar', 'evaporador'):
            d = dz.get(nome)
            if d and d != (0, 0):
                k = ('condensador', 'capilar', 'evaporador').index(nome)
                self._tubo_deslocado(tela, self.tubos[k], d)
        if gelo > 0: self._gelo(tela, t, gelo)
        if ve('compressor'):
            self.compressor(tela, t, ligado and fluido, dz.get('compressor', (0, 0)))
        self.portas(tela, porta)
        if s is not None and fluido:
            x, y = self.pos(s)
            T, P, vap, k = estado(s)
            parcela(tela, x, y, T, vap, t)

    def _desloc(self, tela, d, fn):
        if not d or d == (0, 0): fn(); return
        dx0 = self.dx; self.dx += int(d[0]); dy0 = self.dy; self.dy += int(d[1])
        fn()
        self.dx, self.dy = dx0, dy0

    def _tubo_deslocado(self, tela, tb, d):
        Y = tb.Y + int(d[1]); X = tb.X + int(d[0])
        ok = (Y >= 0) & (Y < PALCO_H) & (X >= 0) & (X < W)
        tela.buf[Y[ok], X[ok]] = np.where(tb.D[ok] > tb.r - 1, PRETO, ACO2)

    def _gelo(self, tela, t, gelo):
        tb = self.tubos[2]
        m = (tb.U < .62) & (tb.D > tb.r - 1.2)
        idx = np.nonzero(m)[0]
        n = int(len(idx) * min(1.0, gelo))
        sel = idx[(np.arange(len(idx)) * 7919) % max(1, len(idx)) < n]
        for i in sel[::2]:
            x, y = tb.X[i], tb.Y[i]
            tela.px(x, y - 1, BRANCO); tela.px(x, y, MISTURA2)

    # ------------------------------------------------------------ calor
    def calor_dentro(self, tela, t, n=14, rate=.35):
        """Pitadas de calor saindo da comida e indo para o evaporador."""
        alvo = (self.X(174), self.Y(42))
        fontes = [(100, 92), (80, 128), (142, 126), (160, 150), (100, 176), (124, 48), (88, 56)]
        for i in range(n):
            fx_, fy_ = fontes[i % len(fontes)]
            u = (t * rate + i / n) % 1.0
            sx, sy = self.X(fx_), self.Y(fy_)
            x = sx + (alvo[0] - sx) * ease(u)
            y = sy + (alvo[1] - sy) * u + math.sin(u * 9 + i) * 3
            if u < .92: calor(tela, x, y, int(t * 5 + i) % 2)

    def calor_fora(self, tela, t, n=16, rate=.5, forte=1.0):
        """Calor saindo pelo condensador e subindo atrás da geladeira."""
        for i in range(n):
            u = (t * rate + i / n) % 1.0
            y0 = 30 + (i * 37) % 125
            x = self.X(214 + (i % 3) * 6) + u * 50 * forte
            y = self.Y(y0) - u * 22 + math.sin(u * 8 + i) * 2
            if x < 296:
                if u < .7: calor(tela, x, y, int(t * 5 + i) % 2)
                else: tela.px(x, y, BRASA)

    def ondas(self, tela, t, x0=242, y0=30, y1=160, cor=LARANJA):
        """Ar quente subindo atrás da geladeira (ondinhas)."""
        for k in range(5):
            x = self.X(x0) + k * 9
            for j in range(10):
                yy = self.Y(y1) - ((t * 18 + j * 14 + k * 5) % (y1 - y0))
                xx = x + math.sin(yy * .25 + k) * 2
                tela.px(xx, yy, cor if j % 2 else CHAMA1)


# ================================================================ closes das 4 etapas
class CloseCompressor:
    """Compressor aberto: motor, manivela, pistão deitado e o cabeçote com as
    duas palhetas (sucção embaixo, descarga em cima)."""
    CX, CY, RM, BI = 104, 84, 33.0, 70.0
    HEAD = 244

    def __init__(self):
        rng = np.random.default_rng(12)
        self.n = 34
        self.u = rng.uniform(.08, .92, self.n); self.v = rng.uniform(.1, .9, self.n)
        self.ordem = np.sort(rng.uniform(0, .9, self.n))
        self.fase = rng.uniform(0, 6.28, self.n)
        self.suc = Trajeto([(294, 150), (262, 150), (262, 92), (250, 92)])
        self.desc = Trajeto([(250, 70), (262, 70), (262, 36), (294, 36)])
        self.t_suc = Tubo(self.suc.p.tolist(), 6)
        self.t_desc = Tubo(self.desc.p.tolist(), 6)
        self.V_bdc = self.vol(180.0); self.V_tdc = self.vol(0.0)
        th_d = 312.0
        self.V_d = self.vol(th_d)
        self.nexp = math.log(P_ALTA / P_BAIXA) / math.log(self.V_bdc / self.V_d)
        self.th_d = th_d

    def face(self, th):
        a = math.radians(th)
        return self.CX + self.RM * math.cos(a) + math.sqrt(self.BI ** 2 - (self.RM * math.sin(a)) ** 2) + 23

    def vol(self, th): return max(2.0, self.HEAD - self.face(th))

    def estado_th(self, th):
        """(T, P, fase) do gás na câmara: 'suc' admissão, 'comp', 'desc'."""
        T_ = th % 360
        if T_ < 180: return T_EVAP, P_BAIXA, 'suc'
        if T_ < self.th_d:
            P = min(P_ALTA, P_BAIXA * (self.V_bdc / self.vol(T_)) ** self.nexp)
            q = math.log(P / P_BAIXA) / math.log(P_ALTA / P_BAIXA)
            return T_EVAP + (T_DESC - T_EVAP) * q, P, 'comp'
        return T_DESC, P_ALTA, 'desc'

    def desenhar(self, tela, th, t, mostra_motor=True, rotulos=True):
        T_, P, fase = self.estado_th(th)
        a = math.radians(th)
        # carcaça cortada
        cx, cy = 150, 112
        tela.disco(cx, 70, 0, PRETO)
        casca = [(cx + 124 * math.cos(b), 112 - 90 * math.sin(b)) for b in np.linspace(0, math.pi, 30)]
        poligono(tela, casca + [(26, 196), (274, 196)], PRETO)
        casca2 = [(cx + 119 * math.cos(b), 112 - 85 * math.sin(b)) for b in np.linspace(0, math.pi, 30)]
        poligono(tela, casca2 + [(31, 192), (269, 192)], ACO1)
        casca3 = [(cx + 114 * math.cos(b), 112 - 80 * math.sin(b)) for b in np.linspace(0, math.pi, 30)]
        poligono(tela, casca3 + [(36, 188), (264, 188)], FUNDO)
        dither(tela, 36, 150, 228, 38, FUNDO2, FUNDO)
        for b in np.linspace(.5, 2.6, 16):
            tela.px(cx + 121 * math.cos(b), 112 - 87 * math.sin(b), ACO3)
        tela.ret(20, 194, 260, 6, ACO0); tela.ret(20, 194, 260, 1, ACO2)
        # óleo no fundo
        tela.ret(37, 180, 226, 8, OLEO0); tela.ret(37, 180, 226, 1, OLEO1)
        # motor elétrico (estator com bobinas de cobre) e rotor girando
        if mostra_motor:
            tela.ret(44, 118, 120, 58, PRETO); tela.ret(45, 119, 118, 56, ACO1)
            for k in range(9):
                x = 50 + k * 12
                tela.ret(x, 124, 9, 46, OLEO1); tela.ret(x, 124, 9, 1, CHAMA1)
                for j in range(0, 46, 3): tela.ret(x, 124 + j, 9, 1, LATAO)
            tela.ret(84, 130, 40, 34, PRETO); tela.ret(85, 131, 38, 32, ACO2)
            for k in range(5):
                yy = 131 + int((k * 7 + t * 40) % 32)
                tela.ret(85, yy, 38, 2, ACO3)
            tela.ret(102, 84, 4, 50, ACO3); tela.ret(102, 84, 1, 50, ACO4)
            if rotulos: tela.texto('MOTOR', 104, 178, ACO3, tam=9, centro=True, contorno=PRETO)
        abre_s = fase == 'suc' and math.sin(a) > .05
        abre_d = fase == 'desc'
        # canos de sucção e descarga
        self.t_suc.desenhar(tela, T_EVAP, 1.0, t, vel=14 if abre_s else 0)
        self.t_desc.desenhar(tela, T_DESC, 1.0, t, vel=22 if abre_d else 4)
        # cilindro
        tela.ret(148, 58, 98, 48, PRETO)
        tela.ret(149, 59, 96, 5, ACO2); tela.ret(149, 100, 96, 5, ACO2)
        tela.ret(149, 59, 96, 1, ACO4)
        tela.ret(149, 64, 96, 36, FUNDO)
        # câmara: gás
        xf = self.face(th)
        self._gas(tela, th, t, xf, T_, fase)
        # cabeçote e palhetas
        tela.ret(244, 56, 10, 52, PRETO); tela.ret(245, 57, 8, 50, ACO2); tela.ret(245, 57, 1, 50, ACO4)
        tela.ret(244, 66, 10, 8, FUNDO); tela.ret(244, 88, 10, 8, FUNDO)
        abre_s = fase == 'suc' and math.sin(a) > .05
        abre_d = fase == 'desc'
        # palheta de sucção (abre para dentro da câmara)
        if abre_s: tela.linha(244, 88, 238, 95, AMARELO)
        else: tela.ret(243, 88, 1, 8, AMARELO)
        if abre_d: tela.linha(254, 66, 259, 60, AMARELO)
        else: tela.ret(254, 66, 1, 8, AMARELO)
        # pistão, biela, manivela
        xp = xf - 23
        px_, py_ = self.CX + self.RM * math.cos(a), self.CY + self.RM * math.sin(a)
        tela.disco(self.CX, self.CY, 38, PRETO); tela.disco(self.CX, self.CY, 36, ACO1)
        tela.disco(self.CX, self.CY, 30, ACO0)
        for k in range(3):
            b = a + k * 2.094
            tela.disco(self.CX + math.cos(b) * 20, self.CY + math.sin(b) * 20, 4, FUNDO2)
        tela.disco(self.CX - math.cos(a) * 18, self.CY - math.sin(a) * 18, 9, ACO2)      # contrapeso
        tela.ret(xp - 8, 65, xf - xp + 8, 34, PRETO)
        tela.ret(xp - 7, 66, xf - xp + 6, 32, ACO2)
        dither(tela, xp - 6, 70, xf - xp + 4, 24, ACO2, ACO1)
        tela.ret(xp - 7, 66, xf - xp + 6, 2, ACO4)
        for k in range(3): tela.ret(xf - 6 - k * 3, 66, 1, 32, ACO0)
        linha_grossa(tela, px_, py_, xp, 82, 9, PRETO)
        linha_grossa(tela, px_, py_, xp, 82, 6, ACO3)
        linha_grossa(tela, px_ - 1, py_ - 1, xp, 81, 1.5, ACO4)
        tela.disco(px_, py_, 7, PRETO); tela.disco(px_, py_, 6, ACO3); tela.disco(px_, py_, 3, LATAO)
        tela.disco(xp, 82, 4, PRETO); tela.disco(xp, 82, 3, LATAO)
        tela.disco(self.CX, self.CY, 5, ACO3); tela.disco(self.CX, self.CY, 2, ACO0)
        return T_, P, fase

    def _gas(self, tela, th, t, xf, T_, fase):
        Tm = th % 360
        L = self.HEAD - xf
        c = cor_temp(T_)
        if fase == 'suc':
            q = Tm / 180.0
            vis = self.ordem < q
        else:
            vis = np.ones(self.n, bool)
        if fase == 'desc':
            q = (Tm - self.th_d) / (360 - self.th_d)
            saiu = self.ordem < q * 1.05
        else:
            saiu = np.zeros(self.n, bool)
        if T_ > 30:                                          # gás quente: a câmara brilha
            dither(tela, xf + 1, 65, max(1, L - 1), 34, FUNDO, BRASA if T_ < 55 else CHAMA2)
        for i in range(self.n):
            if not vis[i]: continue
            x = xf + 2 + self.u[i] * max(1, L - 4) + math.sin(t * 6 + self.fase[i]) * min(2, L * .1)
            y = 66 + self.v[i] * 30 + math.cos(t * 5 + self.fase[i]) * 1.2
            if fase == 'suc':
                idade = (Tm / 180.0 - self.ordem[i]) / .15
                if idade < 1:                                # entrando pela palheta de baixo
                    x = 246 + (x - 246) * idade; y = 92 + (y - 92) * idade
            if saiu[i]:
                w = min(1.0, (q * 1.05 - self.ordem[i]) / .5)
                px_, py_ = self.desc.em(w * .9)
                x, y = px_, py_ + math.sin(i) * 2
            tela.ret(int(x) - 1, int(y) - 1, 3, 3, PRETO)
            tela.ret(int(x), int(y), 2, 2, c)


class CloseCondensador:
    """A grade das costas, de perto: 6 voltas de cano com arames."""

    def __init__(self):
        pts = [(4, 26)] + serpentina(36, 266, 26, 32, 6, nb=20) + [(36, 186), (4, 186)]
        self.tubo = Tubo(pts, 7)
        self.tr = self.tubo.tr
        ss = 1 + np.clip(self.tubo.U, 0, .9999)
        self.Tv, _, self.Vv = estado_vet(np.round(ss, 3))

    def desenhar(self, tela, t, u_parc=None, vel=26.0):
        # arames (na frente da grade, finos)
        for x in range(30, 278, 7):
            tela.ret(x, 14, 1, 186, ACO0)
        tela.ret(28, 14, 252, 2, ACO1); tela.ret(28, 198, 252, 2, ACO1)
        self.tubo.desenhar(tela, self.Tv, self.Vv, t, vel=vel)
        for x in range(30, 278, 21):
            tela.ret(x, 14, 1, 186, ACO1)
        # calor saindo: ondinhas subindo de cada volta, mais forte em cima
        for k in range(6):
            y = 26 + k * 32
            forca = 1.0 - k / 7.0
            for j in range(int(9 * forca)):
                x = 44 + (j * 29 + k * 13) % 220
                u = (t * .9 + j * .37 + k * .21) % 1.0
                yy = y - 9 - u * 18
                xx = x + math.sin(u * 7 + j) * 2
                if u < .75: calor(tela, xx, yy, int(t * 4 + j) % 2)
        if u_parc is not None:
            x, y = self.tr.em(u_parc)
            pis = int(t * 4) % 2
            c = BRANCO if pis else AMARELO
            for sx in (-1, 1):
                for sy in (-1, 1):
                    tela.ret(int(x + sx * 10) - (0 if sx > 0 else 0), int(y + sy * 10), 1, 1, c)
                    tela.ret(int(x + sx * 10) - (3 if sx > 0 else 0), int(y + sy * 10), 4, 1, c)
                    tela.ret(int(x + sx * 10), int(y + sy * 10) - (3 if sy > 0 else 0), 1, 4, c)


class CloseCapilar:
    """Linha de líquido grossa -> tubo capilar enrolado -> entrada do evaporador."""

    def __init__(self):
        pts = [(4, 140), (60, 140)]
        n = 400
        for i in range(n + 1):
            f = i / n
            ph = f * 2 * math.pi * 4.5
            x = 70 + 160 * f + 10 * math.sin(ph)
            y = 140 - 28 * (1 - math.cos(ph)) * .5 * 2 + 0
            pts.append((x, y))
        pts += [(238, 140), (296, 140)]
        self.tr = Trajeto(pts)
        # partes: grossa (0..60), capilar, grossa de novo
        L = self.tr.L
        self.u_a = 56 / L
        self.u_b = (L - 58) / L
        self.grosso1 = Tubo([(4, 140), (62, 140)], 7)
        self.grosso2 = Tubo([(236, 140), (296, 140)], 7)
        self.fino = Tubo(pts[1:-1], 2.2)

    def s_de(self, u):
        """Posição s (2..3) em função de u no trajeto."""
        if u <= self.u_a: return 2.0
        if u >= self.u_b: return 2.9999
        return 2.0 + (u - self.u_a) / (self.u_b - self.u_a) * .9999

    def desenhar(self, tela, t, vel=8.0, rotulos=True):
        uf = self.u_a + self.fino.U * (self.u_b - self.u_a)
        Tf, _, Vf = estado_vet(np.round([self.s_de(x) for x in uf], 3))
        # cone de redução
        poligono(tela, [(58, 132), (70, 137), (70, 143), (58, 148)], PRETO)
        poligono(tela, [(59, 134), (69, 138), (69, 142), (59, 146)], ACO2)
        poligono(tela, [(240, 132), (228, 137), (228, 143), (240, 148)], PRETO)
        poligono(tela, [(239, 134), (229, 138), (229, 142), (239, 146)], ACO2)
        self.grosso1.desenhar(tela, T_COND, 0.0, t, vel=vel)
        self.fino.desenhar(tela, Tf, Vf, t, vel=vel * 3)
        g2 = self.grosso2
        self.grosso2.desenhar(tela, T_EVAP, .25, t, vel=vel, ferve=True)
        # manômetros nas duas pontas
        for (cx, P, rot) in ((34, P_ALTA, 'ANTES'), (266, P_BAIXA, 'DEPOIS')):
            tela.ret(cx - 2, 104, 5, 30, PRETO); tela.ret(cx - 1, 104, 3, 30, ACO2)
            tela.disco(cx, 78, 23, PRETO); tela.disco(cx, 78, 21, ACO2); tela.disco(cx, 78, 18, CERAMICA)
            for k in range(9):
                b = math.radians(225 - k * 270 / 8)
                tela.linha(cx + math.cos(b) * 14, 78 - math.sin(b) * 14, cx + math.cos(b) * 17, 78 - math.sin(b) * 17, PRETO)
            b = math.radians(225 - min(8, P + math.sin(t * 7) * .05) / 8 * 270)
            tela.linha(cx, 78, cx + math.cos(b) * 15, 78 - math.sin(b) * 15, VERMELHO)
            tela.disco(cx, 78, 2, PRETO)
            tela.texto('BAR', cx, 86, ACO1, tam=9, centro=True)
            tela.texto(fmt_bar(P), cx, 46, BRANCO, tam=9, centro=True, contorno=PRETO)
        if rotulos:
            tela.texto('LÍQUIDO MORNO', 8, 158, CHAMA1, tam=9, contorno=PRETO)
            tela.texto('GELADO, COM BOLHAS', 292, 158, MISTURA2, tam=9, centro='d', contorno=PRETO)
        else:
            tela.texto('MORNO', 74, 158, CHAMA1, tam=9, contorno=PRETO)
            tela.texto('GELADO', 232, 158, MISTURA2, tam=9, centro='d', contorno=PRETO)


class CloseEvaporador:
    """Dentro do congelador: a placa do evaporador e a comida dando calor."""

    def __init__(self):
        pts = [(292, 34), (262, 34)] + serpentina(262, 170, 34, 30, 6, nb=20)[1:] + [(292, 184)]
        self.tubo = Tubo(pts, 6)
        self.tr = self.tubo.tr
        ss = 3 + np.clip(self.tubo.U, 0, .9999)
        self.Tv, _, self.Vv = estado_vet(np.round(ss, 3))

    def desenhar(self, tela, t, u_parc=None, vel=12.0, intens=1.0):
        tela.buf[:PALCO_H] = FUNDO
        dither(tela, 0, 0, 298, PALCO_H, FUNDO2, FUNDO3)
        tela.ret(152, 14, 136, 186, PRETO); dither(tela, 153, 15, 134, 184, ACO1, ACO0)
        tela.ret(153, 15, 134, 1, ACO3)
        self.tubo.desenhar(tela, self.Tv, self.Vv, t, vel=vel, ferve=self.Vv < .99)
        # gelinho nas bordas do cano
        m = (self.tubo.D > self.tubo.r - 1.0) & (self.tubo.DY < -2)
        idx = np.nonzero(m)[0][::5]
        tela.buf[self.tubo.Y[idx] - 1, self.tubo.X[idx]] = BRANCO
        # comida: forma de gelo, caixa, saco de ervilhas
        tela.ret(14, 150, 64, 22, PRETO); tela.ret(15, 151, 62, 20, MISTURA2)
        for k in range(5): tela.ret(18 + k * 12, 154, 9, 9, BRANCO); tela.ret(18 + k * 12, 160, 9, 2, MISTURA2)
        tela.ret(90, 112, 52, 60, PRETO); tela.ret(91, 113, 50, 58, ROXO); tela.ret(91, 113, 50, 3, ROSA)
        tela.ret(98, 132, 36, 14, CERAMICA); tela.ret(102, 136, 20, 2, ROXO); tela.ret(102, 140, 14, 2, ROXO)
        tela.disco(46, 112, 24, PRETO); tela.disco(46, 112, 22, AGUA1)
        for k in range(9):
            tela.disco(34 + (k % 3) * 12, 102 + (k // 3) * 10, 4, VERDE); tela.px(33 + (k % 3) * 12, 101 + (k // 3) * 10, BRANCO)
        tela.ret(0, 172, 160, 3, ACO3); tela.ret(0, 172, 160, 1, ACO4)
        # calor da comida e do ar indo para o cano
        n = int(16 * intens)
        for i in range(n):
            sx, sy = ((46, 100), (116, 112), (46, 150), (120, 160), (20, 60), (80, 40))[i % 6]
            u = (t * .3 + i / max(1, n)) % 1.0
            ty = 40 + (i * 31) % 140
            x = sx + (168 - sx) * ease(u)
            y = sy + (ty - sy) * u + math.sin(u * 8 + i) * 4
            if u < .95: calor(tela, x, y, int(t * 5 + i) % 2)
        # flocos no ar
        for i in range(10):
            x = (i * 53 + t * 6) % 150
            y = (i * 37 + t * 9) % 140 + 10
            tela.px(x, y, MISTURA2)
        if u_parc is not None:
            x, y = self.tr.em(u_parc)
            c = BRANCO if int(t * 4) % 2 else AMARELO
            for sx in (-1, 1):
                for sy in (-1, 1):
                    tela.ret(int(x + sx * 10) - (3 if sx > 0 else 0), int(y + sy * 10), 4, 1, c)
                    tela.ret(int(x + sx * 10), int(y + sy * 10) - (3 if sy > 0 else 0), 1, 4, c)


def mira(tela, x, y, t, r=10):
    c = BRANCO if int(t * 4) % 2 else AMARELO
    for sx in (-1, 1):
        for sy in (-1, 1):
            tela.ret(int(x + sx * r) - (3 if sx > 0 else 0), int(y + sy * r), 4, 1, c)
            tela.ret(int(x + sx * r), int(y + sy * r) - (3 if sy > 0 else 0), 1, 4, c)


# ================================================================ curva de fervura (NIST)
NIST = [(-30, .46622), (-25, .58427), (-20, .72477), (-15, .89053), (-10, 1.0845), (-5, 1.3098), (0, 1.5696),
        (5, 1.8672), (10, 2.2061), (15, 2.5899), (20, 3.0222), (25, 3.5067), (30, 4.0472), (35, 4.6477),
        (40, 5.3121), (45, 6.0444), (50, 6.8490)]


def t_ferve(P):
    """Temperatura de fervura do isobutano na pressão P (bar), da tabela do NIST."""
    Ps = [p for _, p in NIST]; Ts = [tt for tt, _ in NIST]
    return float(np.interp(P, Ps, Ts))
