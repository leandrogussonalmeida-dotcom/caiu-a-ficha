#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep09 — o desenho do relógio mecânico (genérico, sem marca).

Toda peça é uma MÁSCARA (numpy) pintada por `pintar`: contorno escuro, chanfro
claro em cima/à esquerda e escuro embaixo/à direita, e um brilho em dither com
a luz vindo do alto à esquerda. Assim roda, ponte, âncora e rubi têm o mesmo
acabamento.

O ESCAPE (escape de âncora, 15 dentes) é uma conta só, `Escape`, e uma
variável manda nele: o tempo do relógio `tau`, contado em ALTERNÂNCIAS (meias
oscilações do balanço; 8 por segundo num relógio de 28.800 por hora).

  balanço   beta(tau) = A sen(pi (tau - tau0)): oscilador livre
  âncora    só se mexe quando o pino de impulso está dentro do garfo
            (|beta| < meio ângulo de levantamento): lambda = asen(-rp sen beta / Lf);
            fora disso fica encostada num pino de batente (+-lambda0)
  roda      travada enquanto a âncora está no batente; quando a âncora anda:
            DESTRAVA (a pedra sai do dente, roda parada), IMPULSO (o dente
            escorrega na face da pedra e a roda avança), QUEDA (a roda anda
            livre um pouquinho) e TRAVA na outra pedra = o TIC, no instante
            inteiro tau = k. Cada alternância anda meio dente (12 graus).
A posição das pedras sai da geometria da roda (as tangentes da roda passam
pelo eixo da âncora), e `checar_escape()` confere quadro a quadro que nenhum
dente atravessa uma pedra.
"""
import math
import numpy as np
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)

# (contorno, escuro, médio, claro, especular)
MAT = {
    'latao': (OLEO0, LATAO, OLEO1, AMARELO, CHAMA0),
    'aco':   (PRETO, ACO1, ACO2, ACO3, ACO4),
    'acoesc': (PRETO, ACO0, ACO1, ACO2, ACO3),
    'placa': (PRETO, FUNDO2, FUNDO3, ACO0, ACO1),
    'rubi':  (PRETO, BRASA, VERMELHO, ROSA, BRANCO),
    'azul':  (PRETO, FUNDO3, MISTURA, CIANO, MISTURA2),
    'couro': (PRETO, OLEO0, BRASA, LATAO, OLEO1),
    'mostr': (PRETO, FUNDO, FUNDO2, FUNDO3, TRACO),
    'rotor': (OLEO0, OLEO0, LATAO, OLEO1, AMARELO),
    'pele':  (PRETO, BRASA, OLEO1, LATAO, CHAMA1),
}


# ================================================================ máscara e pintura
class Mascara:
    """Tela de mentira para usar `poligono`/`linha_grossa` e ganhar uma máscara."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w), bool)

    def ret(self, x, y, w, h, cor=1):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        if x1 > x0 and y1 > y0: self.buf[y0:y1, x0:x1] = bool(cor)

    def disco(self, cx, cy, r, cor=1):
        x0, x1 = max(0, int(cx - r - 1)), min(self.w, int(cx + r + 2))
        y0, y1 = max(0, int(cy - r - 1)), min(self.h, int(cy + r + 2))
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        self.buf[y0:y1, x0:x1][(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = bool(cor)


def _erode(M):
    E = M.copy()
    E[1:] &= M[:-1]; E[:-1] &= M[1:]; E[:, 1:] &= M[:, :-1]; E[:, :-1] &= M[:, 1:]
    E[0, :] = E[-1, :] = False; E[:, 0] = E[:, -1] = False
    return E


def pintar(tela, M, x0, y0, mat, cx=None, cy=None, R=None, contorno=True, chanfro=True, brilho=True, cor_fixa=None):
    """Pinta a máscara M (h, w) com canto em (x0, y0) da tela."""
    h, w = M.shape
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(tela.w, x0 + w), min(PALCO_H, y0 + h)
    if X1 <= X0 or Y1 <= Y0: return
    M = np.pad(M, 1)
    c_out, c_esc, c_med, c_cla, c_esp = MAT[mat]
    out = np.full(M.shape, c_med if cor_fixa is None else cor_fixa, np.uint8)
    yy, xx = np.mgrid[-1:h + 1, -1:w + 1]
    xx = xx + x0; yy = yy + y0
    chk = (xx + yy) % 2 == 0
    if brilho and cor_fixa is None:
        if cx is None:
            ys, xs = np.nonzero(M)
            cx, cy = x0 - 1 + xs.mean(), y0 - 1 + ys.mean()
            R = max(3.0, max(np.ptp(xs), np.ptp(ys)) / 2)
        g = (-(xx - cx) - (yy - cy)) / (R * 1.41)
        out[(g > .22) & chk] = c_cla
        out[g > .52] = c_cla
        out[(g > .78) & chk] = c_esp
        out[(g < -.30) & chk] = c_esc
        out[g < -.60] = c_esc
    E1 = _erode(M)
    if chanfro:
        cima = E1 & ~np.roll(E1, 1, 0); esq = E1 & ~np.roll(E1, 1, 1)
        baixo = E1 & ~np.roll(E1, -1, 0); dir_ = E1 & ~np.roll(E1, -1, 1)
        out[baixo | dir_] = c_esc
        out[cima | esq] = c_esp if cor_fixa is None else c_cla
    if contorno:
        out[M & ~E1] = c_out
    out = out[1:-1, 1:-1]; M = M[1:-1, 1:-1]
    sub = tela.buf[Y0:Y1, X0:X1]
    m = M[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    sub[m] = out[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]


def pintar_tela(tela, Mk, mat, **kw):
    """Pinta uma Mascara do tamanho da tela (recorta a caixa primeiro)."""
    ys, xs = np.nonzero(Mk.buf)
    if len(xs) == 0: return
    a, b, c, d = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pintar(tela, Mk.buf[a:b, c:d], int(c), int(a), mat, **kw)


def brilho(tela, x, y, r, cor=AMARELO, forca=1.0):
    """Halo pontilhado em volta de um ponto (só sobre o que é escuro)."""
    x0, x1 = max(0, int(x - r)), min(tela.w, int(x + r + 1))
    y0, y1 = max(0, int(y - r)), min(PALCO_H, int(y + r + 1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / max(r, 1e-3)
    sub = tela.buf[y0:y1, x0:x1]
    escuro = sub <= TRACO
    bay = ((xx * 3 + yy * 5) % 4) / 4.0
    m = escuro & (d < 1) & ((1 - d) * forca > bay)
    sub[m] = cor


# ================================================================ rodas
def dente_escape(phi, r, R, Rr, h, k=1.0):
    """Dente de clava: face de travar inclinada para a frente, topo (face de
    impulso) que desce para trás e costas curtas: sobra vão para a pedra."""
    s = R / 40.0
    rtop = np.where(phi > -4.5 * k, R - 2 * s * (-phi) / (4.5 * k),
                    R - 2 * s - (R - 2 * s - Rr) * np.clip((-phi - 4.5 * k) / (7.5 * k), 0, 1) ** .6)
    face = -3 * k + 3 * k * np.clip((r - Rr) / h, 0, 1)
    return (phi >= -12 * k) & (r <= rtop) & (phi <= face)


def mascara_roda(cx, cy, R, n, ang, perfil='reto', h=None, raios=5, aro=None, cubo=None, furo=1.4, oco=None):
    """Máscara de roda dentada em coordenadas polares. ang em graus (tela:
    horário). perfil: 'reto' (dente trapézio), 'escape' (dente de clava do
    escape de âncora), 'catraca' (dente de serra), 'liso' (sem dente)."""
    if h is None: h = max(1.6, R * (.17 if perfil == 'escape' else .11))
    Rr = R - h
    x0, y0 = int(math.floor(cx - R - 2)), int(math.floor(cy - R - 2))
    w = hh = int(2 * R + 5)
    yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + w]
    dx, dy = xx + .5 - cx - .5, yy + .5 - cy - .5
    r = np.sqrt(dx * dx + dy * dy)
    th = np.degrees(np.arctan2(dy, dx))
    passo = 360.0 / n if n else 360.0
    if perfil == 'liso' or not n:
        M = r <= R
    elif perfil == 'reto':
        u = ((th - ang) % passo) / passo                 # 0..1 dentro do passo
        larg = .55 - .25 * np.clip((r - Rr) / h, 0, 1)   # o dente afina na ponta
        M = (r <= Rr) | ((r <= R) & (np.abs(u - .5) < larg / 2))
    elif perfil == 'catraca':
        u = ((th - ang) % passo) / passo
        M = (r <= Rr) | (r <= Rr + h * (1 - u))
    else:                                                # escape: passo de 24 graus para 15 dentes
        k = passo / 24.0
        phi = ((th - ang) % passo) - passo               # ponta em 0, corpo para trás (negativo)
        M = (r <= Rr) | dente_escape(phi, r, R, Rr, h, k)
    if aro is not None:                                  # raios ("cruzetas") por dentro do aro
        Rin = Rr - aro
        dentro = r < Rin
        if raios:
            a = np.radians(th - ang)
            best = np.full(r.shape, 1e9)
            for j in range(raios):
                aj = math.radians(360.0 * j / raios)
                best = np.minimum(best, np.abs(np.sin(a - aj)) * r + (np.cos(a - aj) < 0) * 1e9)
            esp = max(1.0, R * .07)
            raio_ok = best <= esp
        else:
            raio_ok = np.zeros_like(dentro)
        cub = r <= (cubo if cubo is not None else max(2.5, R * .22))
        M = M & (~dentro | raio_ok | cub)
    if oco is not None:
        M = M & (r >= oco)
    if furo:
        M = M & (r > furo)
    return M, x0, y0


def roda(tela, cx, cy, R, n, ang, mat='latao', **kw):
    M, x0, y0 = mascara_roda(cx, cy, R, n, ang, **kw)
    pintar(tela, M, x0, y0, mat, cx=cx, cy=cy, R=R)
    return M, x0, y0


def pinhao(tela, cx, cy, r, n, ang):
    roda(tela, cx, cy, r, n, ang, 'aco', h=max(1.2, r * .35), aro=None, furo=0.6)


def rubi(tela, x, y, r=2.2, brilhar=0.0):
    """Pedra (rubi sintético) num furo: anel vermelho com o eixo de aço no meio."""
    if brilhar > 0: brilho(tela, x, y, r * 3.2, ROSA, brilhar)
    M, x0, y0 = mascara_roda(x, y, r, 0, 0, perfil='liso', furo=None)
    pintar(tela, M, x0, y0, 'rubi', cx=x, cy=y, R=r)
    tela.px(x, y, ACO4 if r < 2.6 else ACO3)
    if r >= 2.6: tela.px(x - 1, y - 1, BRANCO)


def borrao(tela, cx, cy, R, mat='latao'):
    """Roda rápida demais para o olho: aro em dither, sem dente."""
    c = MAT[mat]
    M, x0, y0 = mascara_roda(cx, cy, R, 0, 0, perfil='liso', furo=None)
    hh, ww = M.shape
    yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + ww]
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    sub_ok = (yy >= 0) & (yy < PALCO_H) & (xx >= 0) & (xx < tela.w)
    for cond, ca, cb in ((r > R - 2.2, c[2], c[3]), (r <= R - 2.2, c[1], FUNDO)):
        m = M & cond & sub_ok
        cor = np.where((xx + yy) % 2 == 0, ca, cb)
        tela.buf[yy[m], xx[m]] = cor[m]
    tela.disco(cx, cy, max(2, R * .22), c[2])


def fantasma(tela, desenho):
    """Desenha por cima em xadrez: metade dos pixels some e deixa ver o que
    está embaixo (peça que fica na frente, como uma ponte de vidro)."""
    antes = tela.buf.copy()
    desenho()
    yy, xx = np.mgrid[0:tela.h, 0:tela.w]
    m = (xx + yy) % 2 == 0
    tela.buf[m] = antes[m]


# ================================================================ espiral (linha de mola)
def curva(tela, pts, cor, cor2=None, sombra=None):
    """Polilinha de 1 px (amostrada a 0,5 px). cor2 = metade de baixo/direita."""
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)) * 2) + 1
        for i in range(n):
            u = i / n
            x, y = ax + (bx - ax) * u, ay + (by - ay) * u
            if sombra is not None: tela.px(x + 1, y + 1, sombra)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay)) * 2) + 1
        for i in range(n):
            u = i / n
            x, y = ax + (bx - ax) * u, ay + (by - ay) * u
            tela.px(x, y, cor)


def espiral_pts(cx, cy, r0, r1, voltas, a_dentro, a_fora, n=None):
    """Espiral de Arquimedes do raio r0 (ponta de dentro, ângulo a_dentro) ao
    r1 (ponta de fora, presa). Girar a ponta de dentro aperta/afrouxa as voltas."""
    n = n or int(voltas * 60)
    pts = []
    for i in range(n + 1):
        s = i / n
        a = math.radians(a_dentro + 360 * voltas * s) * (1 - s) + math.radians(a_fora + 360 * voltas * s) * s
        a = math.radians(360 * voltas * s) + math.radians(a_dentro) * (1 - s) + math.radians(a_fora) * s
        r = r0 + (r1 - r0) * s
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


# ================================================================ o escape
class Escape:
    """Roda de escape (15 dentes), âncora com 2 pedras e garfo, rolete com o
    pino de impulso e o balanço. Eixo da roda -> âncora -> balanço na
    horizontal. Tudo em pixels de tela a partir de (ex, ey) e do raio Rw."""
    DENTES = 15
    PASSO = 24.0

    def __init__(self, ex, ey, Rw, Lf=None, rp=None, Rb=None, A=220.0, lam0=7.5, trava=1.6, levante=3.4):
        self.ex, self.ey, self.Rw = ex, ey, Rw
        s = Rw / 40.0
        self.s = s
        self.D = Rw / math.cos(math.radians(30))
        self.px, self.py = ex + self.D, ey
        self.Lf = Lf if Lf is not None else 50 * s
        self.rp = rp if rp is not None else 13 * s
        self.bx, self.by = self.px + self.Lf + self.rp, ey
        self.Rb = Rb if Rb is not None else 56 * s
        self.A = A
        self.lam0 = math.radians(lam0)
        self.trava, self.levante = trava * s, levante * s
        self.hw = 4.6                     # meia largura da pedra (graus da roda)
        self.comp = 11 * s                # comprimento da pedra
        self.betaw = math.degrees(math.asin(min(.99, self.Lf * math.sin(self.lam0) / self.rp)))
        self.Dt = math.asin(self.betaw / self.A) / math.pi      # meia janela, em alternâncias
        self.h = max(1.6, Rw * .17)
        # pedras: raio do canto de travar em lambda = 0, achado para que, no
        # batente "dentro", ele entre `trava` px no círculo das pontas
        self.r_sup = self._achar(-30.0, -self.lam0)
        self.c_inf = 30.0
        for _ in range(4):
            # a pedra de baixo é girada até as duas travas ficarem a meio dente
            # (12 graus) uma da outra: assim a roda anda 12 graus por tic
            self.r_inf = self._achar(self.c_inf, self.lam0)
            self.e_sup = self._contato(self._pts('sup', -self.lam0), -30 + self.hw - 11.8, 8)
            self.e_inf = self._contato(self._pts('inf', self.lam0), self.c_inf + self.hw - 11.8, 8)
            err = ((self.e_inf - self.e_sup - 12.0 + 12) % 24) - 12
            if abs(err) < .02: break
            self.c_inf -= err
        self._tabela()

    # ------------------------------------------------ geometria das pedras
    def _rot(self, x, y, lam):
        c, s_ = math.cos(lam), math.sin(lam)
        dx, dy = x - self.px, y - self.py
        return self.px + dx * c - dy * s_, self.py + dx * s_ + dy * c

    def _polar(self, r, a):
        return self.ex + r * math.cos(math.radians(a)), self.ey + r * math.sin(math.radians(a))

    def pedra(self, qual, lam):
        """Polígono da pedra (4 cantos) com a âncora girada lam (rad). O canto 0
        é o de travar (lado de onde vêm os dentes = ângulo menor)."""
        c, r = (-30.0, self.r_sup) if qual == 'sup' else (self.c_inf, self.r_inf)
        hw = self.hw
        p = [self._polar(r, c - hw), self._polar(r - self.levante, c + hw),
             self._polar(r + self.comp, c + hw), self._polar(r + self.comp, c - hw)]
        return [self._rot(x, y, lam) for x, y in p]

    def _pts(self, qual, lam):
        """Pontos do contorno da pedra (a cada ~0,25 px), em polar da roda."""
        p = self.pedra(qual, lam)
        xs, ys = [], []
        for (ax, ay), (bx, by) in zip(p, p[1:] + p[:1]):
            n = int(math.hypot(bx - ax, by - ay) * 4) + 1
            u = np.arange(n) / n
            xs.append(ax + (bx - ax) * u); ys.append(ay + (by - ay) * u)
        x, y = np.concatenate(xs) - self.ex, np.concatenate(ys) - self.ey
        return np.hypot(x, y), np.degrees(np.arctan2(y, x))

    def _dentro(self, r, a, eps):
        """Ponto (r, a) dentro de algum dente com a roda em eps? (mesmo perfil
        de `mascara_roda`). r, a: (n,); eps: (m,) -> (m, n)."""
        R, h = self.Rw, self.h
        Rr = R - h
        phi = ((a[None, :] - eps[:, None]) % 24.0) - 24.0
        rr = r[None, :]
        return (rr <= Rr) | dente_escape(phi, rr, R, Rr, h)

    def _contato(self, pts, e0, span, passo=.04):
        """Primeiro ângulo da roda, a partir de e0, em que um dente toca a pedra."""
        r, a = pts
        sel = r <= self.Rw + .5
        if not sel.any(): return e0 + span
        eps = e0 + np.arange(0, span, passo)
        hit = self._dentro(r[sel], a[sel], eps).any(1)
        i = np.argmax(hit)
        if not hit[i]: return e0 + span
        return float(eps[max(0, i - 1)])

    def _prof(self, c, r, lam):
        """Quanto o canto de travar entra no círculo das pontas (px)."""
        x, y = self._rot(*self._polar(r, c - self.hw), lam)
        return self.Rw - math.hypot(x - self.ex, y - self.ey)

    def _achar(self, c, lam_dentro):
        r = self.Rw
        for _ in range(40):
            r += (self._prof(c, r, lam_dentro) - self.trava)
        return r

    def _lam_beta(self, b):
        if abs(b) < self.betaw:
            return math.asin(max(-1, min(1, -self.rp * math.sin(math.radians(b)) / self.Lf)))
        return -self.lam0 if b > 0 else self.lam0

    def _tabela(self):
        """Uma passagem do balanço pelo centro, x = tau - instante da passagem.
        A roda anda o que a pedra que sai deixa (IMPULSO) e, livre, cai com
        velocidade limitada até a pedra que entra (QUEDA)."""
        x = np.arange(-self.Dt * 1.15, self.Dt + .06, .0004)
        self.tx = x
        self.tg, self.tf = {}, {}
        vmax = 700.0
        xl = []
        for par in (0, 1):
            sinal = 1 if par == 0 else -1
            sai, entra = ('inf', 'sup') if par == 0 else ('sup', 'inf')
            e_ant = self.e_inf if par == 0 else self.e_sup
            alvo = e_ant + 12.0
            g = np.zeros(len(x)); f = np.zeros(len(x), int)
            e = e_ant
            lam_ini = self._lam_beta(sinal * self.A * math.sin(math.pi * x[0]))
            for i, xi in enumerate(x):
                lam = self._lam_beta(sinal * self.A * math.sin(math.pi * xi))
                c_sai = self._contato(self._pts(sai, lam), e - .5, 14.5)
                lim = min(c_sai, alvo)
                novo = min(lim, e + vmax * .0004) if i else e
                ant = f[i - 1] if i else 0
                if novo >= alvo - .01: fase = 0                                # travou de novo
                elif abs(lam - lam_ini) < 1e-6: fase = 0                        # travada
                elif ant == 3 or (ant == 2 and c_sai > e + vmax * .0004 + .01): fase = 3   # queda livre
                elif ant == 2 or novo > e_ant + .3: fase = 2                                # impulso
                else: fase = 1                                                  # destrava
                e = max(e_ant, novo)
                g[i] = e - e_ant; f[i] = fase
            self.tg[par], self.tf[par] = g, f
            xl.append(x[np.argmax(g >= 12.0 - .01)])
        self.x_lock = float(np.mean(xl))
        self.tau0 = -self.x_lock
        # fração destravando, para o painel
        self.p_u = .25

    # ------------------------------------------------ estado em função de tau
    def beta(self, tau):
        return self.A * math.sin(math.pi * (tau - self.tau0))

    def lam(self, tau):
        return self._lam_beta(self.beta(tau))

    def trava_k(self, k):
        """Ângulo da roda travada depois do tic k (k par: pedra de cima)."""
        return self.e_sup + 12.0 * k

    FASES = ('TRAVADA', 'DESTRAVA', 'IMPULSO', 'QUEDA')

    def estado(self, tau):
        """(beta, lambda, eps, fase) — fase: 'TRAVADA', 'DESTRAVA', 'IMPULSO', 'QUEDA'."""
        b = self.beta(tau)
        lam = self._lam_beta(b)
        kc = int(round(tau - self.tau0))            # passagem pelo centro mais perto (= tic kc)
        x = tau - (kc + self.tau0)
        if x <= self.tx[0]: return b, lam, self.trava_k(kc - 1), 'TRAVADA'
        if x >= self.tx[-1]: return b, lam, self.trava_k(kc), 'TRAVADA'
        par = kc % 2
        i = int((x - self.tx[0]) / .0004)
        i = min(i, len(self.tx) - 2)
        u = (x - self.tx[i]) / .0004
        g = self.tg[par][i] * (1 - u) + self.tg[par][i + 1] * u
        return b, lam, self.trava_k(kc - 1) + g, self.FASES[self.tf[par][i]]

    # ------------------------------------------------ desenho
    def desenhar_roda(self, tela, eps, borrar=False):
        if borrar:
            borrao(tela, self.ex, self.ey, self.Rw, 'aco'); return
        if self.Rw < 20:
            M, x0, y0 = mascara_roda(self.ex, self.ey, self.Rw, 15, eps, perfil='escape', aro=1.6, raios=5, cubo=2.5, furo=.6)
            pintar(tela, M, x0, y0, 'aco', cx=self.ex, cy=self.ey, R=self.Rw, contorno=False)
            return
        roda(tela, self.ex, self.ey, self.Rw, 15, eps, 'aco', perfil='escape', aro=max(1.5, 4.5 * self.s),
             raios=5, cubo=max(2.5, 6 * self.s), furo=max(.6, 1.5 * self.s))

    def desenhar_ancora(self, tela, lam, brilho_pedra=None):
        s = self.s
        P = (self.px, self.py)
        rot = lambda x, y: self._rot(x, y, lam)
        Mk = Mascara()
        # braços até as pedras e o braço do garfo
        sup, inf = self.pedra('sup', 0), self.pedra('inf', 0)
        ms = ((sup[2][0] + sup[3][0]) / 2, (sup[2][1] + sup[3][1]) / 2)
        mi = ((inf[2][0] + inf[3][0]) / 2, (inf[2][1] + inf[3][1]) / 2)
        for q in (ms, mi):
            a = rot(*q)
            linha_grossa(Mk, P[0], P[1], a[0], a[1], max(2.5, 6 * s), 1)
            Mk.disco(a[0], a[1], max(1.5, 4 * s))
        fx_ = self.px + self.Lf
        a = rot(self.px, self.py); b = rot(fx_ - 7 * s, self.py)
        linha_grossa(Mk, a[0], a[1], b[0], b[1], max(2.0, 4.5 * s), 1)
        # garfo: dois chifres com a fenda do pino
        g = max(1.2, 2.2 * s)
        for sy in (-1, 1):
            q = [rot(fx_ - 8 * s, self.py + sy * g), rot(fx_ + 1 * s, self.py + sy * g),
                 rot(fx_ + 3 * s, self.py + sy * (g + 4.5 * s)), rot(fx_ - 8 * s, self.py + sy * (g + 4 * s))]
            poligono(Mk, q, 1)
        Mk.disco(*P, max(2.5, 5 * s))
        pintar_tela(tela, Mk, 'aco', cx=self.px + 10 * s, cy=self.py, R=30 * s)
        tela.disco(P[0], P[1], max(1, 1.6 * s), PRETO)
        rubi(tela, P[0], P[1], max(1.4, 2.4 * s))
        for q in ('sup', 'inf'):
            pts = self.pedra(q, lam)
            Mp = Mascara(); poligono(Mp, pts, 1)
            if brilho_pedra == q:
                brilho(tela, sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4, 9 * s, ROSA, .9)
            pintar_tela(tela, Mp, 'rubi')

    def batentes(self, tela):
        s = self.s
        d = self.Lf * .42
        for sy in (-1, 1):
            # o braço (meia largura ~2,25 s) encosta no pino quando |lambda| = lam0
            y = self.py + sy * (d * math.sin(self.lam0) + 2.3 * s + 1.4 * s)
            tela.disco(self.px + d, y, max(1, 1.4 * s), PRETO)
            tela.disco(self.px + d, y, max(.6, 1.0 * s), ACO3)

    def desenhar_balanco(self, tela, beta, espiral=True, mat='latao'):
        s = self.s
        bx, by, Rb = self.bx, self.by, self.Rb
        # aro + 3 braços
        M, x0, y0 = mascara_roda(bx, by, Rb, 0, beta, perfil='liso', aro=max(2.5, 6 * s), raios=3,
                                 cubo=max(2, 5 * s), furo=None)
        pintar(tela, M, x0, y0, mat, cx=bx, cy=by, R=Rb)
        # parafusos do aro
        for j in range(12):
            a = math.radians(beta + 15 + j * 30)
            x, y = bx + math.cos(a) * (Rb - 2.6 * s), by + math.sin(a) * (Rb - 2.6 * s)
            if s >= .7:
                tela.disco(x, y, 1.6 * s, OLEO0); tela.px(x - .5, y - .5, CHAMA0)
        if espiral:
            self.desenhar_espiral(tela, beta)

    def desenhar_espiral(self, tela, beta):
        s = self.s
        bx, by = self.bx, self.by
        r0, r1 = 5 * s, self.Rb * .62
        voltas = 9 if s >= .7 else 4
        pts = espiral_pts(bx, by, r0, r1, voltas, beta + 180, 300)
        curva(tela, pts, CIANO, sombra=FUNDO3 if s >= .7 else None)
        # pitão (ponta de fora presa)
        xe, ye = pts[-1]
        tela.ret(xe - 1, ye - 1, 3, 3, PRETO); tela.px(xe, ye, ACO3)

    def desenhar_rolete(self, tela, beta, brilhar=0.0):
        s = self.s
        a = math.radians(180 + beta)
        tela.disco(self.bx, self.by, self.rp + 1.5 * s, PRETO)
        tela.disco(self.bx, self.by, self.rp + .5 * s, ACO1)
        tela.disco(self.bx, self.by, self.rp - 1.5 * s, ACO2)
        tela.disco(self.bx - 1, self.by - 1, max(1, self.rp * .35), ACO3)
        x, y = self.bx + math.cos(a) * self.rp, self.by + math.sin(a) * self.rp
        rubi(tela, x, y, max(1.4, 2.2 * s), brilhar)
        tela.disco(self.bx, self.by, max(1, 2 * s), PRETO)
        tela.px(self.bx, self.by, ACO4)

    def pino(self, beta):
        a = math.radians(180 + beta)
        return self.bx + math.cos(a) * self.rp, self.by + math.sin(a) * self.rp

    def desenhar(self, tela, tau, balanco=True, espiral=True, borrar=False, brilho_tic=True):
        b, lam, eps, fase = self.estado(tau)
        if balanco: self.desenhar_balanco(tela, b, espiral=espiral)
        self.desenhar_roda(tela, eps, borrar=borrar)
        self.batentes(tela)
        pedra_ativa = None
        if fase in ('IMPULSO', 'DESTRAVA'):
            k = math.ceil(tau - 1e-9)
            pedra_ativa = 'inf' if k % 2 == 0 else 'sup'     # a que está saindo empurra
        self.desenhar_ancora(tela, lam, brilho_pedra=pedra_ativa if not borrar else None)
        self.desenhar_rolete(tela, b, brilhar=.8 if fase in ('IMPULSO', 'DESTRAVA') else 0)
        # o tic: estrelinha onde o dente bate
        frac = tau - math.floor(tau)
        if brilho_tic and frac < .06 and not borrar:
            k = round(tau)
            ang = self.e_sup if k % 2 == 0 else self.e_inf
            x, y = self._polar(self.Rw, ang + 1)
            brilho(tela, x, y, 8 * self.s, AMARELO, 1 - frac / .06)
            tela.px(x, y, BRANCO)
        return b, lam, eps, fase

    # ------------------------------------------------ conferência
    def mascara_dentes(self, eps):
        M, x0, y0 = mascara_roda(self.ex, self.ey, self.Rw, 15, eps, perfil='escape', furo=None)
        return M, x0, y0


def checar_escape(E, n=6, passo=.002):
    """Conta pixels em que um dente cai dentro de uma pedra, varrendo n tics."""
    pior = 0
    for i in range(int(n / passo)):
        tau = i * passo
        b, lam, eps, fase = E.estado(tau)
        M, x0, y0 = E.mascara_dentes(eps)
        for q in ('sup', 'inf'):
            Mp = Mascara(); poligono(Mp, E.pedra(q, lam), 1)
            # encolhe a pedra 1 px (encostar não é atravessar)
            Pm = _erode(Mp.buf)
            h, w = M.shape
            sub = Pm[max(0, y0):y0 + h, max(0, x0):x0 + w]
            mm = M[max(0, y0) - y0:max(0, y0) - y0 + sub.shape[0], max(0, x0) - x0:max(0, x0) - x0 + sub.shape[1]]
            ov = int((sub & mm).sum())
            if ov > pior: pior = ov; quando = (round(tau, 3), fase, q)
    return pior, (quando if pior else None)


# ================================================================ tambor e mola real
def tambor(tela, cx, cy, R, ang_tambor, ang_eixo, carga, catraca_ang=None):
    """Tambor aberto (sem tampa) com a mola real dentro. carga 0..1: com
    corda, as voltas se apertam no eixo; sem corda, encostam na parede."""
    roda(tela, cx, cy, R, 60, ang_tambor, 'latao', h=max(1.6, R * .06), furo=None)
    Rin = R * .86
    yy, xx = np.mgrid[0:PALCO_H, 0:tela.w]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    dentro = d2 <= Rin * Rin
    sub = tela.buf[:PALCO_H]
    sub[dentro] = np.where(((xx + yy) % 2 == 0) & ((xx - cx) + (yy - cy) < 0), FUNDO2, FUNDO)[dentro]   # fundo do tambor
    sub[(d2 > Rin * Rin) & (d2 <= (R * .9) ** 2)] = LATAO
    tela.anel(cx, cy, Rin, PRETO, .6)
    # a mola: N voltas, raio de cada ponto entre "apertada no eixo" e "na parede"
    N = 9
    gap = max(1.6, R * .045)
    ra = R * .16
    pts = []
    passos = N * 70
    for i in range(passos + 1):
        u = i / passos * N
        rc = ra + 1.5 + u * gap
        rw = Rin - 1.5 - (N - u) * gap
        q = 1 / (1 + math.exp((u - carga * N) * 2.2))
        r = rc * q + rw * (1 - q)
        a = math.radians(360 * u) + math.radians(ang_eixo) * (1 - u / N) + math.radians(ang_tambor) * (u / N)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    curva(tela, pts, ACO3, sombra=ACO0)
    # brilho da mola no alto à esquerda
    for x, y in pts[::5]:
        if (x - cx) + (y - cy) < -R * .5: tela.px(x, y, ACO4)
    # eixo com o gancho
    roda(tela, cx, cy, ra, 0, 0, 'aco', perfil='liso', furo=None)
    a = math.radians(ang_eixo)
    tela.px(cx + math.cos(a) * ra * .6, cy + math.sin(a) * ra * .6, PRETO)
    rubi(tela, cx, cy, max(1.5, ra * .35))


def mola_mini(tela, cx, cy, R, carga, ang):
    """Tambor pequeno visto de cima (com tampa e catraca), para o mapa."""
    roda(tela, cx, cy, R, 48, ang, 'latao', furo=None)
    roda(tela, cx, cy, R * .55, 24, -ang * 3, 'aco', perfil='catraca', furo=None)
    tela.disco(cx, cy, R * .14, PRETO)
    tela.disco(cx, cy, R * .1, ACO3)


# ================================================================ mostrador
def mostrador(tela, cx, cy, R, h, m, s, coroa=True, pulseira=True, segundos=True, numeros=False, cor_ponteiro=None):
    """Relógio de pulso visto de frente. h, m, s em horas/minutos/segundos
    (podem ser fracionários)."""
    if pulseira:
        w = R * 1.05
        for sy in (-1, 1):
            y0 = cy + sy * R * .8
            y1 = cy + sy * (R * 2.6)
            ya, yb = (min(y0, y1), max(y0, y1))
            ya, yb = max(0, ya), min(PALCO_H, yb)
            Mk = Mascara(); Mk.ret(cx - w / 2, ya, w, yb - ya)
            pintar_tela(tela, Mk, 'couro', cx=cx, cy=cy + sy * R * 1.7, R=R)
            for yy in range(int(ya) + 2, int(yb), 4):
                tela.px(cx - w / 2 + 2, yy, LATAO); tela.px(cx + w / 2 - 3, yy, LATAO)
        # alças (asas)
        for sy in (-1, 1):
            for sx in (-1, 1):
                Mk = Mascara()
                Mk.ret(cx + sx * w / 2 - (4 if sx > 0 else 0) * R / 40, cy + sy * R * .75 - (R * .25 if sy < 0 else 0),
                       4 * R / 40 + 1, R * .25)
                pintar_tela(tela, Mk, 'aco')
    if coroa:
        Mk = Mascara(); Mk.ret(cx + R - 1, cy - R * .14, R * .2, R * .28)
        pintar_tela(tela, Mk, 'aco')
        for k in range(int(R * .28) // 2):
            tela.px(cx + R + R * .2 - 2, cy - R * .14 + 1 + k * 2, ACO0)
    # caixa
    roda(tela, cx, cy, R, 0, 0, 'aco', perfil='liso', furo=None)
    roda(tela, cx, cy, R * .9, 0, 0, 'acoesc', perfil='liso', furo=None)
    Rm = R * .84
    M, x0, y0 = mascara_roda(cx, cy, Rm, 0, 0, perfil='liso', furo=None)
    pintar(tela, M, x0, y0, 'mostr', cx=cx, cy=cy, R=Rm, chanfro=False)
    # índices
    for k in range(60):
        a = math.radians(k * 6 - 90)
        if k % 5 == 0:
            r0, r1 = Rm * (.72 if k % 15 == 0 else .78), Rm * .92
            for d in np.linspace(r0, r1, int((r1 - r0) * 2) + 1):
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
                tela.px(x, y, ACO4)
                if R > 30: tela.px(x + 1, y, ACO3)
        elif R > 34:
            tela.px(cx + math.cos(a) * Rm * .92, cy + math.sin(a) * Rm * .92, ACO1)
    # ponteiros
    def ponteiro(ang_graus, comp, larg, mat, cauda=0.0):
        a = math.radians(ang_graus - 90)
        x1, y1 = cx + math.cos(a) * comp, cy + math.sin(a) * comp
        x0_, y0_ = cx - math.cos(a) * cauda, cy - math.sin(a) * cauda
        Mk = Mascara()
        linha_grossa(Mk, x0_, y0_, x1, y1, larg, 1)
        pintar_tela(tela, Mk, mat, cx=cx, cy=cy, R=comp)
    ponteiro(h * 30, Rm * .52, max(2.5, R * .09), 'aco', Rm * .1)
    ponteiro(m * 6, Rm * .8, max(2.0, R * .06), 'aco', Rm * .12)
    if segundos:
        a = math.radians(s * 6 - 90)
        cor = cor_ponteiro or VERMELHO
        tela.linha(cx - math.cos(a) * Rm * .2, cy - math.sin(a) * Rm * .2, cx + math.cos(a) * Rm * .88,
                   cy + math.sin(a) * Rm * .88, cor)
    tela.disco(cx, cy, max(1.5, R * .05), ACO3)
    tela.px(cx, cy, BRANCO)


# ================================================================ fundo
def fundo_bancada(tela):
    """Tapete de relojoeiro: azul escuro com grade fina."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24):
        tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24):
        tela.ret(0, y, W, 1, FUNDO2)


def placa(tela, cx, cy, R):
    """Platina com perlage (graneado em círculos) desenhado em dither."""
    M, x0, y0 = mascara_roda(cx, cy, R, 0, 0, perfil='liso', furo=None)
    pintar(tela, M, x0, y0, 'placa', cx=cx, cy=cy, R=R, brilho=False)
    hh, ww = M.shape
    yy, xx = np.mgrid[y0:y0 + hh, x0:x0 + ww]
    gx, gy = (xx % 10) - 5, (yy % 10) - 5 + ((xx // 10) % 2) * 5
    gy = (gy + 5) % 10 - 5
    d = np.sqrt(gx * gx + gy * gy)
    E = _erode(_erode(M))
    m = E & (np.abs(d - 3.5) < .6) & (yy >= 0) & (yy < PALCO_H) & (xx >= 0) & (xx < W)
    tela.buf[yy[m], xx[m]] = np.where(((xx[m] - cx) + (yy[m] - cy)) < 0, ACO0, FUNDO2)


# ================================================================ ajudas de texto
def fio(tela, x0, y0, x1, y1, cor=AMARELO):
    """Fio de rótulo: linha com quadradinho na ponta da peça."""
    tela.linha(x0, y0, x1, y1, cor)
    tela.ret(x1 - 1, y1 - 1, 3, 3, PRETO)
    tela.px(x1, y1, cor)


def rotulo(tela, txt, x, y, cor=BRANCO, tam=9, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, centro=centro, contorno=PRETO)


def barra(tela, x, y, w, h, frac, cor, fundo=FUNDO2):
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, fundo)
    n = int(round(w * max(0.0, min(1.0, frac))))
    if n > 0:
        tela.ret(x, y, n, h, cor)
        tela.ret(x, y, n, 1, BRANCO if cor in (AMARELO, CIANO, VERDE) else CHAMA0)
    for k in range(1, 10):
        tela.px(x + w * k // 10, y + h - 1, PRETO)


# ================================================================ o movimento inteiro (mapa)
def _intersec(a, ra, b, rb, escolher=1):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    x = (ra * ra - rb * rb + d * d) / (2 * d)
    y = math.sqrt(max(0.0, ra * ra - x * x))
    ex, ey = dx / d, dy / d
    return (a[0] + ex * x - escolher * ey * y, a[1] + ey * x + escolher * ex * y)


class Movimento:
    """O relógio aberto pelas costas: platina, tambor, rodas do centro, terceira
    e quarta, escape, âncora e balanço. Todas as rodas giram a partir do
    ângulo da roda de escape (quarta = escape / 16, terceira = quarta / 7,5,
    centro = terceira / 8, tambor = centro / 6): o trem anda aos tiquinhos,
    junto com o escape."""
    NOMES = ('tambor', 'rodas', 'escape', 'ancora', 'balanco', 'rubis')

    def __init__(self, cx=150, cy=104, R=100):
        self.cx, self.cy, self.R = cx, cy, R
        s = R / 100.0
        self.s = s
        self.E = Escape(cx + 10 * s, cy + 50 * s, 14 * s, Lf=18 * s, rp=5 * s, Rb=28 * s, A=220)
        self.C = (cx, cy)
        Es = (self.E.ex, self.E.ey)
        a = math.radians(-165)
        self.F = (Es[0] + 23.5 * s * math.cos(a), Es[1] + 23.5 * s * math.sin(a))
        self.T = _intersec(self.C, 35 * s, self.F, 28 * s, -1)
        b = math.radians(-40)
        self.B0 = (cx + 48 * s * math.cos(b), cy + 48 * s * math.sin(b))
        self.Rc, self.Rt, self.Rf, self.Rbar = 30 * s, 24 * s, 20 * s, 41 * s

    def angulos(self, tau):
        b, lam, eps, fase = self.E.estado(tau)
        quarta = -(eps - self.E.e_sup) / 16.0
        terceira = -quarta / 7.5
        centro = -terceira / 8.0
        tambor = -centro / 6.0
        return dict(beta=b, lam=lam, eps=eps, fase=fase, quarta=quarta, terceira=terceira, centro=centro, tambor=tambor)

    def ancoras(self):
        s, E = self.s, self.E
        return dict(tambor=(self.B0[0] + 20 * s, self.B0[1] - 30 * s), rodas=(self.T[0], self.T[1] - 18 * s),
                    escape=(E.ex - 10 * s, E.ey + 6 * s), ancora=(E.px + 1 * s, E.py - 8 * s),
                    balanco=(E.bx - 2 * s, E.by + 26 * s), rubis=self.C,
                    centro=self.C, terceira=self.T, quarta=self.F)

    def desenhar(self, tela, tau, vis=None, desl=None, brilho_rubis=0.0, rubis_acesos=None, placa_on=True, so_placa=False):
        vis = set(self.NOMES) if vis is None else vis
        desl = desl or {}
        s = self.s
        A = self.angulos(tau)
        if placa_on: placa(tela, self.cx, self.cy, self.R)
        if so_placa: return A
        # furos/pontos da platina onde as peças vão
        for p in (self.B0, self.C, self.T, self.F, (self.E.ex, self.E.ey), (self.E.px, self.E.py), (self.E.bx, self.E.by)):
            tela.disco(p[0], p[1], 2.2 * s, FUNDO)
        def d(nome, p):
            dx, dy = desl.get(nome, (0, 0))
            return p[0] + dx, p[1] + dy
        if 'tambor' in vis:
            x, y = d('tambor', self.B0)
            # haste e coroa (às 3 horas) com a roda de coroa que engrena na catraca
            a = math.atan2(self.cy - y, self.cx + self.R - x)
            rx, ry = x + math.cos(a) * (self.Rbar * .66 + 9 * s), y + math.sin(a) * (self.Rbar * .66 + 9 * s)
            Mk = Mascara(); linha_grossa(Mk, rx, ry, self.cx + self.R + 4 * s, self.cy, 3.5 * s, 1)
            Mk.ret(self.cx + self.R, self.cy - 7 * s, 9 * s, 14 * s)
            pintar_tela(tela, Mk, 'aco')
            roda(tela, x, y, self.Rbar, 70, A['tambor'], 'latao', furo=None)
            roda(tela, x, y, self.Rbar * .66, 30, A.get('catraca', 0.0), 'aco', perfil='catraca', furo=None)
            roda(tela, rx, ry, 9 * s, 16, -A.get('catraca', 0.0) * 2, 'aco', furo=None)
            tela.disco(x, y, 4 * s, PRETO); tela.disco(x, y, 3 * s, ACO3)
            for k in range(3):
                a = math.radians(k * 120 + 30)
                tela.disco(x + math.cos(a) * 11 * s, y + math.sin(a) * 11 * s, 1.6 * s, PRETO)
                tela.px(x + math.cos(a) * 11 * s, y + math.sin(a) * 11 * s, ACO3)
        if 'rodas' in vis:
            x, y = d('rodas', self.C)
            roda(tela, x, y, self.Rc, 72, A['centro'], 'latao', aro=3 * s, raios=4, furo=None)
            tx, ty = d('rodas', self.T)
            roda(tela, tx, ty, self.Rt, 64, A['terceira'], 'latao', aro=2.6 * s, raios=4, cubo=4 * s, furo=None)
            pinhao(tela, tx, ty, 5 * s, 8, A['terceira'])
            fx_, fy = d('rodas', self.F)
            roda(tela, fx_, fy, self.Rf, 60, A['quarta'], 'latao', aro=2.4 * s, raios=4, cubo=3.6 * s, furo=None)
            pinhao(tela, fx_, fy, 4 * s, 8, A['quarta'])
        E = self.E
        if 'escape' in vis:
            ox, oy = desl.get('escape', (0, 0))
            E.ex += ox; E.ey += oy
            pinhao(tela, E.ex, E.ey, 2.6 * s, 7, A['eps'])
            E.desenhar_roda(tela, A['eps'])
            E.ex -= ox; E.ey -= oy
        if 'ancora' in vis:
            ox, oy = desl.get('ancora', (0, 0))
            E.px += ox; E.py += oy
            E.desenhar_ancora(tela, A['lam'] if 'balanco' in vis else -E.lam0)
            E.px -= ox; E.py -= oy
        if 'balanco' in vis:
            ox, oy = desl.get('balanco', (0, 0))
            E.bx += ox; E.by += oy
            E.desenhar_balanco(tela, A['beta'], espiral=True)
            E.desenhar_rolete(tela, A['beta'])
            # ponte do balanço (galo) por cima, sem esconder a espiral
            Mk = Mascara()
            linha_grossa(Mk, E.bx, E.by, E.bx + 36 * s, E.by - 22 * s, 6 * s, 1)
            Mk.disco(E.bx, E.by, 5 * s)
            pintar_tela(tela, Mk, 'aco', cx=E.bx, cy=E.by, R=20 * s)
            E.bx -= ox; E.by -= oy
        # parafusos azulados da platina
        for k in range(5):
            a = math.radians(100 + k * 52)
            x, y = self.cx + math.cos(a) * self.R * .86, self.cy + math.sin(a) * self.R * .86
            tela.disco(x, y, 3 * s, PRETO); tela.disco(x, y, 2.2 * s, MISTURA)
            tela.ret(x - 2 * s, y, 4 * s, 1, FUNDO3); tela.px(x - 1, y - 1, CIANO)
        if 'rubis' in vis:
            pts = self.pontos_rubi()
            n = len(pts) if rubis_acesos is None else rubis_acesos
            for i, (x, y) in enumerate(pts[:n]):
                rubi(tela, x, y, 2.6 * s, brilho_rubis)
        return A

    def pontos_rubi(self):
        E = self.E
        return [self.C, self.T, self.F, (E.ex, E.ey), (E.px, E.py), (E.bx, E.by)]
