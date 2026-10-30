#!/usr/bin/env python3
"""ep10 — desenho: o helicóptero (de lado e de cima), o rotor, o prato cíclico,
o ar que passa pelo rotor, o chão e os ícones do painel.

Convenções (as mesmas em todo o episódio):
  rotor     gira no sentido anti-horário visto de cima. Azimute psi: 0 = a pá
            aponta para o nariz, 90° = para a esquerda do helicóptero, 180° =
            para a cauda, 270° = para a direita. A pá avança do lado direito.
  3D        X = para o nariz, Y = para a esquerda, Z = para cima. De lado o
            nariz fica à direita da tela e vemos o lado DIREITO (Y entra na tela).
  prato     a haste de passo de cada pá fica 1/4 de volta À FRENTE dela (no
            sentido do giro), presa num braço do lado do bordo de ataque. Assim
            o prato inclina para o mesmo lado que o disco vai inclinar: a pá
            muda de ângulo e responde 90° depois (F10). Tudo sai da mesma conta,
            `Cabeca.passo`, que o desenho do prato, o ícone e o rotor de cima leem.
"""
import math
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, dither, linha_grossa, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3,
                   ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA,
                   MISTURA2, GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0)
from ep02_desenho import pol, contorno, brilho, gradiente, seta_forca, barra, perfil_w

RAD = math.pi / 180


def arco_seta(tela, cx, cy, rx, ry, a0, a1, cor, cab=5, n=28):
    """Arco de elipse de a0 a a1 (graus, anti-horário na tela) com ponta em a1."""
    pts = []
    for k in range(n + 1):
        a = (a0 + (a1 - a0) * k / n) * RAD
        pts.append((cx + rx * math.cos(a), cy - ry * math.sin(a)))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        linha_grossa(tela, x0, y0, x1, y1, 3, PRETO)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        tela.linha(x0, y0, x1, y1, cor)
        tela.linha(x0, y0 + 1, x1, y1 + 1, cor)
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    dx, dy = xb - xa, yb - ya
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    tri = [(xb + ux * cab, yb + uy * cab), (xb + nx * cab * .8, yb + ny * cab * .8), (xb - nx * cab * .8, yb - ny * cab * .8)]
    contorno(tela, tri, PRETO)
    pol(tela, tri, cor)


def rotulo(tela, txt, x, y, ax, ay, cor=AMARELO, tam=9, direita=False):
    """Rótulo com fio até a peça (ax, ay). `direita`: o texto termina em x."""
    w = tela.largura_texto(txt, tam)
    h = 7 if tam < 14 else 14
    tx = x - w if direita else x
    tela.texto(txt, tx, y, cor, tam=tam, contorno=PRETO)
    lx = x + 2 if direita else x - 3
    yy = y + h // 2
    tela.linha(lx, yy, ax, ay, PRETO if cor != PRETO else ACO1)
    tela.linha(lx, yy - 1, ax, ay - 1, cor)
    tela.disco(ax, ay, 1.6, cor)


def caixa(tela, x, y, w, h, titulo=None, borda=ACO1):
    """Caixa de zoom (inset) com grade fina."""
    tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
    tela.ret(x - 1, y - 1, w + 2, h + 2, borda)
    tela.ret(x, y, w, h, FUNDO)
    for gx in range(x, x + w, 12): tela.ret(gx, y, 1, h, FUNDO2)
    for gy in range(y + 6, y + h, 12): tela.ret(x, gy, w, 1, FUNDO2)
    if titulo:
        tela.texto(titulo, x + 3, y + 2, ACO3, tam=9, contorno=PRETO)


# =================================================================== perfil (ícone do ângulo da pá)
_PERF = perfil_w(.1, 60)


def perfil_icone(tela, x, y, c, ang, cor=ACO3, cor2=ACO2, bordo=AMARELO, ref=True, texto=True, vento=False, t=0.0):
    """Corte da pá (bordo de ataque à esquerda, a pá anda para a esquerda),
    inclinado `ang` graus (nariz para cima). c = corda em px."""
    a = ang * RAD
    k = c / 4.0
    # perfil_w: bordo de ataque em x≈-2 (esquerda), de fuga em +2. Nariz para
    # cima com o bordo de ataque à esquerda = girar no sentido horário.
    z = _PERF * np.exp(-1j * a)
    xs = x + z.real * k; ys = y - z.imag * k
    pts = list(zip(xs.tolist(), ys.tolist()))
    if ref:
        for kk in range(-int(c * 1.2), int(c * .6), 3):
            tela.px(x + kk, y, ACO1)
    contorno(tela, pts, PRETO)
    pol(tela, pts, cor, cor2)
    i_le = int(np.argmin(_PERF.real))
    for i in range(int(i_le * .4), i_le + 1):
        tela.px(xs[i], ys[i], ACO4)
    xl, yl = xs[i_le], ys[i_le]
    tela.disco(xl, yl, 1.3, bordo)
    if ref:
        # linha da corda (pontilhada) e o arco entre ela e a horizontal, à frente do bordo de ataque
        xt, yt = x + 2 * k * math.cos(-a), y - 2 * k * math.sin(-a)
        r = c * 1.12
        for j in range(int(c * .95), int(r) + 1, 2):
            tela.px(xt - math.cos(-a) * j, yt + math.sin(-a) * j, AMARELO)
        n = max(2, int(abs(ang) * 1.5))
        for j in range(n + 1):
            aa = math.pi - a * j / n
            tela.px(xt + math.cos(aa) * r, yt - math.sin(aa) * r, AMARELO)
    if texto:
        s = f"{int(round(ang))}°"
        tela.texto(s, x + int(c * .55), y - 16, AMARELO, tam=9, contorno=PRETO)
    if vento:                                   # o ar vem de frente (a pá anda para a esquerda)
        for q in range(3):
            u = (t * 1.6 + q / 3) % 1.0
            xx = x - c * .6 - 22 + u * 12
            tela.ret(xx, y - 6 + q * 6, 6, 1, ACO2)


# =================================================================== cabeça do rotor e prato cíclico
class Cabeca:
    """Mastro, prato fixo, rolamento, prato giratório, hastes de passo,
    braços e as duas pás, em 3D com projeção oblíqua (visto de lado e de cima)."""
    RF, RG, RM = 1.8, 1.5, .32            # raios: prato fixo, prato giratório (= raio das hastes), mastro
    TH = .22                              # espessura de cada prato
    CURSO = .44                           # quanto o prato sobe com o coletivo (0..1)
    ZHUB = 3.5                            # altura do cubo
    THMIN = 1.0                           # ângulo da pá com coletivo 0 e prato reto (graus)
    E = .42                               # quanto a profundidade sobe na tela

    def __init__(self):
        # comprimento da haste: com coletivo 0 e prato reto, a pá fica com THMIN
        self.L = self.ZHUB + self.RG * math.sin(self.THMIN * RAD) - self._z_giro_topo(0.0, 0.0, 0.0, 0.0)

    # ---------------------------------------------------- mecânica
    def zc(self, h): return h * self.CURSO

    def incl(self, a, r, f, l):
        """Altura extra do prato no azimute a (rad) por causa da inclinação.
        f, l = seno da inclinação para a frente / para a esquerda (lado baixo)."""
        return -r * (f * math.cos(a) + l * math.sin(a))

    def _z_giro_topo(self, a, h, f, l):
        return self.zc(h) + .08 + 2 * self.TH + self.incl(a, self.RG, f, l)

    def passo(self, psi_b, h, f, l):
        """Ângulo (graus) da pá que está no azimute psi_b (rad)."""
        aL = psi_b + math.pi / 2
        zh = self._z_giro_topo(aL, h, f, l) + self.L
        s = (zh - self.ZHUB) / self.RG
        return math.degrees(math.asin(max(-1, min(1, s))))

    # ---------------------------------------------------- desenho
    def desenhar(self, tela, cx, cy, s, psi, h=0.0, f=0.0, l=0.0, rb=6.0, destaque=None, t=0.0, ponto=False):
        """psi = azimute da pá A (rad). Devolve âncoras (x, y) para rótulos."""
        E = self.E
        Pj = lambda X, Y, Z: (cx + s * X, cy - s * Z - s * Y * E)
        pisca = (int(t * 4) % 2 == 0)
        cor = lambda nome, normal: (AMARELO if pisca else normal) if destaque == nome else normal
        anc = {}
        zc = self.zc(h)
        # ---- caixa de transmissão
        zb = -2.5
        x0, y0 = Pj(-2.4, 0, zb)
        x1, y1 = Pj(2.4, 0, zb - 1.1)
        tela.ret(x0 - 1, y0 - s * E * 1.2 - 1, x1 - x0 + 2, y1 - y0 + s * E * 1.2 + 2, PRETO)
        dither(tela, x0, y0, x1 - x0, y1 - y0, ACO1, ACO0)
        tela.ret(x0, y0 - s * E * 1.2, x1 - x0, s * E * 1.2, ACO2)
        tela.ret(x0, y0 - s * E * 1.2, x1 - x0, 1, ACO3)
        for k in range(5):
            bx = x0 + 3 + k * (x1 - x0 - 6) / 4
            tela.px(bx, y0 + 3, ACO3); tela.px(bx + 1, y0 + 3, ACO4)
        anc['caixa'] = ((x0 + x1) / 2, y1 - 2)
        # ---- hastes de comando (3, fixas): da caixa ao prato fixo
        for k, a in enumerate((0.0, 2.2, 4.1)):
            pb = Pj(self.RF * .9 * math.cos(a), self.RF * .9 * math.sin(a), zb)
            pt = Pj(self.RF * .9 * math.cos(a), self.RF * .9 * math.sin(a),
                    zc - self.TH + self.incl(a, self.RF * .9, f, l))
            c = cor('comando', ACO2)
            linha_grossa(tela, *pb, *pt, max(2, s * .16) + 2, PRETO)
            linha_grossa(tela, *pb, *pt, max(2, s * .16), c)
            tela.linha(pb[0] - 1, pb[1], pt[0] - 1, pt[1], ACO3 if c == ACO2 else BRANCO)
            tela.disco(*pb, max(1.5, s * .12), ACO1)
            if k == 0: anc['comando'] = ((pb[0] + pt[0]) / 2, (pb[1] + pt[1]) / 2)
        # ---- mastro (parte de baixo)
        self._mastro(tela, Pj, s, zb, zc, psi, cor('mastro', None))
        # ---- prato fixo
        self._prato(tela, Pj, self.RF, zc - self.TH, zc, f, l, cor('fixo', ACO2), cor('fixo', ACO1), None)
        anc['fixo'] = Pj(self.RF * .98, 0, zc - self.TH * .5 + self.incl(0, self.RF, f, l))
        # parafusos fixos (não giram)
        for a in np.arange(0, 2 * math.pi, math.pi / 4):
            if math.sin(a) < -.1:
                tela.px(*Pj(self.RF * .9 * math.cos(a), self.RF * .9 * math.sin(a), zc + self.incl(a, self.RF * .9, f, l)), ACO3)
        # ---- rolamento
        self._prato(tela, Pj, self.RG + .1, zc + .0, zc + .08, f, l, cor('rolamento', LATAO), cor('rolamento', OLEO0), None)
        anc['rolamento'] = Pj(-self.RG - .1, 0, zc + .04 + self.incl(math.pi, self.RG, f, l))
        # ---- prato giratório (com parafusos que giram junto)
        z0g = zc + .08
        self._prato(tela, Pj, self.RG, z0g, z0g + 2 * self.TH, f, l, cor('giratorio', ACO4), cor('giratorio', ACO3), psi)
        anc['giratorio'] = Pj(-self.RG * .7, -self.RG * .7, z0g + 2 * self.TH + self.incl(math.radians(225), self.RG, f, l))
        # ---- peças acima do prato, ordenadas pela profundidade (Y maior = mais longe = antes)
        itens = []
        for j, nome in ((0, 'A'), (1, 'B')):
            pb = psi + j * math.pi
            aL = pb + math.pi / 2
            itens.append((self.RG * math.sin(aL), 'haste', j, pb, aL))
            itens.append((.9 * math.sin(pb) + .01, 'pa', j, pb, aL))
        itens.append((0.0, 'cubo', 0, 0, 0))
        itens.sort(key=lambda it: -it[0])
        for prof, tipo, j, pb, aL in itens:
            if tipo == 'cubo':
                self._mastro(tela, Pj, s, z0g + 2 * self.TH + self.incl(0, 0, f, l), self.ZHUB, psi, cor('mastro', None))
                # cubo
                hx0, hy0 = Pj(-.75, 0, self.ZHUB + .35)
                hx1, hy1 = Pj(.75, 0, self.ZHUB - .3)
                tela.ret(hx0 - 1, hy0 - 1, hx1 - hx0 + 2, hy1 - hy0 + 2, PRETO)
                dither(tela, hx0, hy0, hx1 - hx0, hy1 - hy0, ACO3, ACO2)
                tela.ret(hx0, hy0, hx1 - hx0, 1, ACO4)
                nx, ny = Pj(0, 0, self.ZHUB + .6)
                tela.disco(nx, ny, max(1.5, s * .22), PRETO); tela.disco(nx, ny, max(1, s * .16), ACO3)
                tela.px(nx - 1, ny - 1, BRANCO)
                anc['mastro'] = Pj(self.RM, 0, (zc + self.ZHUB) * .5 + .9)
                continue
            th = self.passo(pb, h, f, l)
            if tipo == 'haste':
                zt = self._z_giro_topo(aL, h, f, l)
                p0 = Pj(self.RG * math.cos(aL), self.RG * math.sin(aL), zt)
                p1 = Pj(self.RG * math.cos(aL), self.RG * math.sin(aL), zt + self.L)
                c = cor('haste', AMARELO if j == 0 else LARANJA)
                linha_grossa(tela, *p0, *p1, max(2, s * .14) + 2, PRETO)
                linha_grossa(tela, *p0, *p1, max(2, s * .14), c)
                tela.disco(*p0, max(1.5, s * .12), ACO1); tela.disco(*p1, max(1.5, s * .12), ACO1)
                if j == 0: anc['haste'] = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            else:
                self._pa(tela, Pj, s, pb, th, rb, j, cor('pa', None), cor('braco', None))
                zt = self._z_giro_topo(aL, h, f, l) + self.L
                if j == 0:
                    rr = min(rb * .8, 3.6)
                    anc['pa'] = Pj(rr * math.cos(pb), rr * math.sin(pb), self.ZHUB)
                    anc['braco'] = Pj(self.RG * .8 * math.cos(aL), self.RG * .8 * math.sin(aL), zt)
        return anc

    def _mastro(self, tela, Pj, s, z0, z1, psi, cor):
        x0, ya = Pj(-self.RM, 0, z1)
        x1, yb = Pj(self.RM, 0, z0)
        w = max(3, int(round(x1 - x0)))
        tela.ret(x0 - 1, ya, w + 2, yb - ya, PRETO)
        c1, c2, c3 = (ACO4, ACO3, ACO2) if cor is None else (cor, cor, ACO3)
        tela.ret(x0, ya, w, yb - ya, c2)
        tela.ret(x0, ya, max(1, w // 3), yb - ya, c1)
        tela.ret(x0 + w - max(1, w // 3), ya, max(1, w // 3), yb - ya, c3)
        # risca que gira com o mastro: só aparece do lado de cá
        for d in (0.0, math.pi):
            a = psi + d + .6
            if math.sin(a) < 0:
                xx = (x0 + x1) / 2 + math.cos(a) * w / 2 * .9
                tela.ret(xx, ya, 1, yb - ya, LATAO)

    def _prato(self, tela, Pj, r, zb, zt, f, l, c1, c2, giro):
        n = 40
        a = np.linspace(0, 2 * math.pi, n, endpoint=False)
        inc = np.array([self.incl(x, r, f, l) for x in a])
        bot = [Pj(r * math.cos(x), r * math.sin(x), zb + d) for x, d in zip(a, inc)]
        top = [Pj(r * math.cos(x), r * math.sin(x), zt + d) for x, d in zip(a, inc)]
        contorno(tela, bot, PRETO)
        contorno(tela, top, PRETO)
        pol(tela, bot, c2, ACO0 if c2 != OLEO0 else FUNDO3)
        pol(tela, top, c1, c2)
        # brilho na borda de trás e sombra na da frente
        for i in range(n):
            j = (i + 1) % n
            if math.sin(a[i]) > 0:
                tela.linha(*top[i], *top[j], BRANCO if c1 in (ACO4, AMARELO) else ACO4)
        if giro is not None:
            for k in range(6):
                x = giro + k * math.pi / 3
                if math.sin(x) < .2:
                    tela.px(*Pj(r * .82 * math.cos(x), r * .82 * math.sin(x), zt + self.incl(x, r * .82, f, l)), ACO1)

    def _pa(self, tela, Pj, s, pb, th, rb, j, cor, cor_braco):
        ux, uy = math.cos(pb), math.sin(pb)
        vx, vy = -uy, ux                          # sentido do giro: bordo de ataque
        c = .9
        a = th * RAD
        hc = (vx * math.cos(a) * c / 2, vy * math.cos(a) * c / 2, math.sin(a) * c / 2)
        def P(r, sg):
            return Pj(ux * r + sg * hc[0], uy * r + sg * hc[1], self.ZHUB + sg * hc[2])
        # braço (garra) da pá, do cubo até r = 1,1
        g0 = Pj(ux * .5, uy * .5, self.ZHUB); g1 = Pj(ux * 1.2, uy * 1.2, self.ZHUB)
        linha_grossa(tela, *g0, *g1, max(3, s * .3) + 2, PRETO)
        linha_grossa(tela, *g0, *g1, max(3, s * .3), ACO2 if cor_braco is None else cor_braco)
        # braço de passo: da garra até o ponto da haste (1/4 de volta à frente)
        aL = pb + math.pi / 2
        zt = self.ZHUB + self.RG * math.sin(a)
        b1 = Pj(self.RG * math.cos(aL), self.RG * math.sin(aL), zt)
        b0 = Pj(ux * .9 + vx * c * .3, uy * .9 + vy * c * .3, self.ZHUB + math.sin(a) * c * .3)
        linha_grossa(tela, *b0, *b1, max(2, s * .14) + 2, PRETO)
        linha_grossa(tela, *b0, *b1, max(2, s * .14), ACO3 if cor_braco is None else cor_braco)
        quad = [P(1.15, 1), P(rb, 1), P(rb, -1), P(1.15, -1)]
        contorno(tela, quad, PRETO)
        base = cor if cor is not None else (ACO3 if j == 0 else ACO2)
        pol(tela, quad, base, ACO2 if j == 0 else ACO1)
        tela.linha(*P(1.15, 1), *P(rb, 1), ACO4)              # bordo de ataque claro
        if j == 0:                                            # faixa amarela da pá A
            for r0 in (2.2, 2.4):
                tela.linha(*P(r0, 1), *P(r0, -1), AMARELO)


# =================================================================== helicóptero de lado
class Heli:
    """Helicóptero genérico de 2 pás, de lado, nariz para a direita. Unidade:
    comprimento ~ 90. Origem no centro, sob o mastro; esqui em y = +17."""
    CAB = [(-12, -9), (-2, -13), (8, -12.5), (16, -9.5), (22, -4), (24, 1), (22, 7), (15, 11), (2, 12), (-10, 11),
           (-14, 4), (-14, -4)]
    VIDRO = [(4, -11.6), (11, -10.6), (17, -7.6), (21.6, -2.6), (23, 2), (15, 2), (9, -1), (4, -4)]
    CAPO = [(-13, -6), (-9, -13), (5, -14.2), (7, -12), (-2, -11), (-11, -5)]
    CAUDA = [(-13, -6.5), (-60, -4.6), (-60, -1.4), (-13, 1.5)]
    DERIVA = [(-55, -4.5), (-62, -15), (-65.5, -15), (-62, -1.5)]
    VENTRAL = [(-57, -1.5), (-61, 5), (-63.2, 5), (-61.5, -1.5)]
    ESTAB = [(-45, -2.6), (-52, -3.2), (-52.5, -.4), (-45, .6)]
    HUB = (0, -21.0)
    R = 42.0
    TR = (-61.5, -7.5)
    RT = 7.0

    def P_(self, ox, oy, k, ang):
        a = ang * RAD
        ca, sa = math.cos(a), math.sin(a)
        return lambda x, y: (ox + k * (x * ca + y * sa), oy + k * (-x * sa + y * ca))

    def desenhar(self, tela, ox, oy, k, ang=0.0, t=0.0, psi=0.0, giro=0.0, disco=0.0, psi_c=0.0, giro_c=0.0,
                 motor=True, sombra_y=None, luz=True, cor=ACO4, pa_a=True, rotores=None, cauda_rotor=True):
        """ox, oy = origem na tela; ang = nariz para cima (graus); psi = azimute
        da pá A (rad); giro = voltas/s (para o borrão); disco = inclinação extra
        do disco para a frente (graus); psi_c / giro_c = rotor de cauda."""
        P = self.P_(ox, oy, k, ang)
        L = lambda pts: [P(x, y) for x, y in pts]
        # ---- sombra no chão
        if sombra_y is not None:
            d = max(0.0, sombra_y - (oy + 17 * k))
            w = k * 38 * (1 - min(.6, d / 260))
            if d < 200:
                xs = ox - w / 2
                for yy in range(int(sombra_y) - 1, int(sombra_y) + 2):
                    for xx in range(int(xs), int(xs + w)):
                        if (xx + yy) % 2 == 0: tela.px(xx, yy, PRETO)
        # ---- calor do escape
        if motor:
            for j in range(7):
                u = (t * 2.1 + j / 7) % 1.0
                x, y = P(-12 - u * 18, -10 - u * 3 + math.sin(t * 11 + j * 2) * .8)
                tela.px(x, y, GAS2 if u < .5 else TRACO)
        # ---- deriva, cauda, estabilizador
        for poly, c1, c2 in ((self.DERIVA, ACO3, ACO2), (self.VENTRAL, ACO3, ACO2), (self.CAUDA, cor, ACO3)):
            contorno(tela, L(poly), PRETO)
            pol(tela, L(poly), c1, c2)
        tela.linha(*P(-14, -6.0), *P(-59, -4.2), BRANCO)
        pol(tela, L([(-13, -0.4), (-60, -2.4), (-60, -1.4), (-13, 1.5)]), ACO2)
        contorno(tela, L(self.ESTAB), PRETO); pol(tela, L(self.ESTAB), ACO3)
        # ---- esquis
        for (a, b) in (((-5, 11), (-8, 17)), ((13, 10), (15, 17))):
            linha_grossa(tela, *P(*a), *P(*b), max(1.5, k * 1.4) + 2, PRETO)
            linha_grossa(tela, *P(*a), *P(*b), max(1.5, k * 1.4), ACO2)
        linha_grossa(tela, *P(-17, 17.2), *P(22, 17.2), max(2, k * 1.6) + 2, PRETO)
        linha_grossa(tela, *P(-17, 17.2), *P(22, 17.2), max(2, k * 1.6), ACO2)
        linha_grossa(tela, *P(22, 17.2), *P(25.5, 15.2), max(2, k * 1.6), ACO2)
        tela.linha(*P(-16, 16.6), *P(21, 16.6), ACO3)
        # ---- capô e cabine
        contorno(tela, L(self.CAPO), PRETO); pol(tela, L(self.CAPO), ACO3, ACO2)
        tela.linha(*P(-8, -12.6), *P(4, -13.6), ACO4)
        cab = L(self.CAB)
        contorno(tela, cab, PRETO)
        pol(tela, cab, cor)
        pol(tela, L([(22, 7), (15, 11), (2, 12), (-10, 11), (-14, 4), (-14, 1), (20, 4)]), ACO3, cor)
        pol(tela, L([(15, 11), (2, 12), (-10, 11), (-12, 8), (16, 9)]), ACO2)
        vid = L(self.VIDRO)
        pol(tela, vid, FUNDO2, FUNDO3)
        tela.linha(*P(6, -10.6), *P(16, -7.2), CIANO)
        tela.linha(*P(17.5, -6), *P(21, -1.5), MISTURA2)
        # porta e listra
        for u, v in (((-6, -9), (-6, 9)), ((-6, -9), (3, -11)), ((3, -11), (3, 2))):
            tela.linha(*P(*u), *P(*v), ACO2)
        tela.linha(*P(-13, 3), *P(21, 3.4), LARANJA)
        tela.linha(*P(-13, 4), *P(20.5, 4.4), BRASA)
        # luzes
        if luz and (t % 1.2) < .12:
            b = P(-30, -5.8); brilho(tela, b[0], b[1], 4, VERMELHO); tela.disco(b[0], b[1], 1.3, VERMELHO)
        else:
            b = P(-30, -5.8); tela.px(b[0], b[1], BRASA)
        nl = P(0, 12.2); tela.px(nl[0], nl[1], VERDE)
        # ---- rotor de cauda (de frente na vista de lado)
        if cauda_rotor:
            self._cauda(tela, P, k, psi_c, giro_c)
        # ---- mastro e rotor principal (ou os rotores dados: coaxial)
        if rotores is None:
            rotores = [dict(hub=self.HUB, R=self.R, psi=psi, giro=giro, pa_a=pa_a)]
        topo = min(r['hub'][1] for r in rotores)
        linha_grossa(tela, *P(0, -14), *P(0, topo), max(2, k * 1.6) + 2, PRETO)
        linha_grossa(tela, *P(0, -14), *P(0, topo), max(2, k * 1.6), ACO2)
        for r in sorted(rotores, key=lambda r: -r['hub'][1]):
            self._rotor(tela, P, k, ang, r['psi'], r['giro'], disco, r.get('pa_a', False), hub=r['hub'], R=r['R'])
            hx, hy = P(*r['hub'])
            tela.disco(hx, hy, max(1.5, k * 1.6), PRETO); tela.disco(hx, hy, max(1, k * 1.1), ACO3)

    def _cauda(self, tela, P, k, psi, giro):
        cx, cy = P(*self.TR)
        r = self.RT * k
        if giro > 2.0:
            for j in range(int(r) + 1):
                pass
            # borrão: disco pontilhado
            yy, xx = np.mgrid[int(cy - r - 1):int(cy + r + 2), int(cx - r - 1):int(cx + r + 2)]
            d = np.hypot(xx - cx, yy - cy)
            m = (d <= r) & (d >= r * .25) & ((xx + yy) % 2 == 0)
            for y0, x0 in zip(yy[m], xx[m]): tela.px(x0, y0, ACO1)
            tela.anel(cx, cy, r, ACO2, .7)
            for j in range(2):
                a = psi + j * math.pi
                tela.linha(cx, cy, cx + math.cos(a) * r, cy + math.sin(a) * r, ACO3)
        else:
            for j in range(2):
                a = psi + j * math.pi
                linha_grossa(tela, cx, cy, cx + math.cos(a) * r, cy + math.sin(a) * r, max(2, k * 1.2) + 2, PRETO)
                linha_grossa(tela, cx, cy, cx + math.cos(a) * r, cy + math.sin(a) * r, max(2, k * 1.2), ACO3)
        tela.disco(cx, cy, max(1.5, k * 1.1), ACO2)

    def pontos_rotor(self, ox, oy, k, ang, psi, disco, r, hub=None):
        """Ponta da pá (raio r em unidades) no azimute psi, na tela."""
        P = self.P_(ox, oy, k, ang)
        dt = disco * RAD
        hub = self.HUB if hub is None else hub
        x = hub[0] + r * math.cos(psi) * math.cos(dt)
        y = hub[1] + r * math.cos(psi) * math.sin(dt) - r * .035
        sx, sy = P(x, y)
        return sx, sy - k * r * math.sin(psi) * .12

    def _rotor(self, tela, P, k, ang, psi, giro, disco, pa_a, hub=None, R=None):
        hub = self.HUB if hub is None else hub
        R = self.R if R is None else R
        hx, hy = P(*hub)
        ox, oy = P(0, 0)
        ponto = lambda ps, r: self.pontos_rotor(ox, oy, k, ang, ps, disco, r, hub)
        if giro > 1.2:
            # borrão: o disco vira uma elipse pontilhada com fantasmas das pás
            n = 48
            ring = [ponto(2 * math.pi * i / n, R) for i in range(n)]
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                if i % 2 == 0: tela.linha(*a, *b, ACO2)
            for i in range(0, n, 3):
                x, y = ring[i]
                tela.px(x, y, ACO3)
            for q in range(3):
                for j in range(2):
                    a = psi + j * math.pi - q * .18
                    x, y = ponto(a, R)
                    tela.linha(hx, hy, x, y, ACO1 if q else ACO2)
            return
        ordem = sorted((0, 1), key=lambda j: -math.sin(psi + j * math.pi))
        for j in ordem:
            a = psi + j * math.pi
            x, y = ponto(a, R)
            x2, y2 = ponto(a, 3)
            esp = max(2, k * 1.5)
            linha_grossa(tela, x2, y2, x, y, esp + 2, PRETO)
            c = ACO3 if math.sin(a) < 0 else ACO2
            linha_grossa(tela, x2, y2, x, y, esp, c)
            tela.linha(x2, y2 - 1, x, y - 1, ACO4)
            if j == 0 and pa_a:
                xm, ym = ponto(a, R * .86)
                linha_grossa(tela, xm, ym, x, y, esp, AMARELO)


# =================================================================== helicóptero visto de cima
class HeliTopo:
    """Vista de cima, nariz para cima. (u, v) = (direita, frente) em unidades."""
    R = 42.0

    def T(self, cx, cy, s, yaw):
        a = yaw * RAD
        ca, sa = math.cos(a), math.sin(a)
        return lambda u, v: (cx + s * (u * ca - v * sa), cy - s * (u * sa + v * ca))

    def elipse(self, u0, v0, ru, rv, n=24, a0=0, a1=360):
        return [(u0 + ru * math.cos(a * RAD), v0 + rv * math.sin(a * RAD)) for a in np.linspace(a0, a1, n, endpoint=a1 - a0 < 360)]

    def corpo(self, tela, cx, cy, s, yaw=0.0, t=0.0, psi_c=0.0, giro_c=0.0, sombra=True, fantasma=False, cauda=True,
              destaque_cauda=False, eixo=None):
        T = self.T(cx, cy, s, yaw)
        L = lambda pts: [T(u, v) for u, v in pts]
        if sombra:
            S = self.T(cx + 6, cy + 8, s, yaw)
            for poly in (self.elipse(0, 4, 9, 14), [(-2.2, -8), (2.2, -8), (1.2, -60), (-1.2, -60)]):
                pts = [S(u, v) for u, v in poly]
                ys = [p[1] for p in pts]; xs = [p[0] for p in pts]
                sub = tela.buf.copy()
                pol(tela, pts, 255)
                m = tela.buf == 255
                tela.buf[:] = sub
                yy, xx = np.nonzero(m)
                k = (xx + yy) % 2 == 0
                tela.buf[yy[k], xx[k]] = PRETO
        c_corpo = ACO1 if fantasma else ACO4
        c_esc = ACO0 if fantasma else ACO2
        # esquis
        for u in (-10, 10):
            linha_grossa(tela, *T(u, -9), *T(u, 19), max(2, s * 1.4) + 2, PRETO)
            linha_grossa(tela, *T(u, -9), *T(u, 19), max(2, s * 1.4), c_esc)
        for v in (-3, 12):
            linha_grossa(tela, *T(-10, v), *T(10, v), max(2, s * 1.0), c_esc)
        # cauda
        boom = [(-2.4, -8), (2.4, -8), (1.2, -60), (-1.2, -60)]
        estab = [(-9, -45), (9, -45), (9, -48.5), (-9, -48.5)]
        fin = [(-.9, -56), (.9, -56), (.9, -65), (-.9, -65)]
        for poly, c1, c2 in ((estab, ACO3, ACO2), (boom, c_corpo, ACO3), (fin, ACO3, ACO2)):
            if fantasma: c1, c2 = ACO1, ACO0
            contorno(tela, L(poly), PRETO); pol(tela, L(poly), c1, c2)
        if not fantasma:
            tela.linha(*T(-1.2, -9), *T(-.6, -59), BRANCO)
        if eixo is not None:                            # eixo da cauda aceso, andando
            for kk in range(0, 52, 3):
                v = -8 - kk
                on = ((kk / 3 + int(eixo * 8)) % 3) == 0
                tela.px(*T(0, v), AMARELO if on else LATAO)
        # capô e cabine
        cap = [(-5, 0), (5, 0), (4, -12), (-4, -12)]
        contorno(tela, L(cap), PRETO); pol(tela, L(cap), ACO0 if fantasma else ACO3, c_esc)
        cab = self.elipse(0, 6, 8.5, 13)
        contorno(tela, L(cab), PRETO)
        pol(tela, L(cab), c_corpo, ACO3 if not fantasma else ACO0)
        vid = self.elipse(0, 8.5, 7, 9.5, 18, 15, 165)
        vid = vid + [(0, 9)]
        pol(tela, L(vid), FUNDO2, FUNDO3)
        tela.linha(*T(-4, 15), *T(2, 17), CIANO if not fantasma else FUNDO3)
        if not fantasma:
            tela.linha(*T(-7.5, 4), *T(-7.5, -1), BRANCO)
        # rotor de cauda: visto de cima fica de lado (um traço) no lado esquerdo da deriva
        if cauda:
            a0, a1 = T(-2.8, -54), T(-2.8, -68)
            if giro_c > 2:
                linha_grossa(tela, *a0, *a1, max(2, s * 1.3) + 2, PRETO)
                for q in range(9):
                    u = q / 8
                    x = a0[0] + (a1[0] - a0[0]) * u; y = a0[1] + (a1[1] - a0[1]) * u
                    tela.px(x, y, ACO3 if (q + int(t * 30)) % 2 else ACO1)
            else:
                v = 7 * math.cos(psi_c)
                b0, b1 = T(-2.8, -61 + v), T(-2.8, -61 - v)
                linha_grossa(tela, *b0, *b1, max(2, s * 1.3) + 2, PRETO)
                linha_grossa(tela, *b0, *b1, max(2, s * 1.3), ACO3)
            hc = T(-2.8, -61)
            tela.disco(*hc, max(1.5, s * .9), AMARELO if destaque_cauda and int(t * 4) % 2 == 0 else ACO2)
        return T

    def rotor(self, tela, cx, cy, s, yaw, psi, giro=0.0, pa_a=True, passo_fn=None, chord=2.8, cor_b=ACO3):
        """Rotor de cima. psi = azimute da pá A no corpo (rad)."""
        T = self.T(cx, cy, s, yaw)
        R = self.R
        if giro > 1.2:
            # disco borrado pontilhado
            rpx = R * s
            yy, xx = np.mgrid[int(cy - rpx - 1):int(cy + rpx + 2), int(cx - rpx - 1):int(cx + rpx + 2)]
            d = np.hypot(xx - cx, yy - cy)
            m = (d <= rpx) & (d > 4) & ((xx + 2 * yy) % 4 == 0)
            yy, xx = yy[m], xx[m]
            ok = (yy >= 0) & (yy < PALCO_H) & (xx >= 0) & (xx < W)
            tela.buf[yy[ok], xx[ok]] = ACO1
            tela.anel(cx, cy, rpx, ACO2, .8)
            for q in range(4):
                for j in (0, 1):
                    a = psi + j * math.pi - q * .14
                    tip = T(-R * math.sin(a), R * math.cos(a))
                    tela.linha(cx, cy, *tip, ACO2 if q == 0 else ACO1)
            tela.disco(cx, cy, max(2, s * 3), PRETO); tela.disco(cx, cy, max(1.5, s * 2.2), ACO3)
            return
        for j in (1, 0):
            a = psi + j * math.pi
            du, dv = -math.sin(a), math.cos(a)          # direção da pá
            wu, wv = -dv, du                             # sentido do giro (anti-horário): bordo de ataque
            c = chord
            quad = [(du * 3 + wu * c * .55, dv * 3 + wv * c * .55), (du * R + wu * c * .55, dv * R + wv * c * .55),
                    (du * R - wu * c * .45, dv * R - wv * c * .45), (du * 3 - wu * c * .45, dv * 3 - wv * c * .45)]
            pts = L = [T(u, v) for u, v in quad]
            contorno(tela, pts, PRETO)
            pol(tela, pts, cor_b if j else ACO3, ACO2)
            tela.linha(*pts[0], *pts[1], ACO4)
            if j == 0 and pa_a:
                ext = [(du * R * .84 + wu * c * .55, dv * R * .84 + wv * c * .55), quad[1], quad[2],
                       (du * R * .84 - wu * c * .45, dv * R * .84 - wv * c * .45)]
                pol(tela, [T(u, v) for u, v in ext], AMARELO)
        tela.disco(cx, cy, max(2, s * 3), PRETO); tela.disco(cx, cy, max(1.5, s * 2.2), ACO3)
        tela.px(cx - 1, cy - 1, BRANCO)

    def ponta(self, cx, cy, s, yaw, psi, r=None):
        T = self.T(cx, cy, s, yaw)
        r = self.R if r is None else r
        return T(-r * math.sin(psi), r * math.cos(psi))


# =================================================================== ar passando pelo rotor (de lado)
class ArRotor:
    """Filetes de ar que atravessam o rotor (como os do túnel de vento do ep02):
    colunas fixas, com traços que andam ao longo delas. Para baixo: o ar entra
    por cima, sai mais rápido por baixo e se espalha no chão. Para cima
    (autorrotação): o ar entra por baixo e sai por cima."""

    def __init__(self, n=9, seed=4):
        self.cols = np.linspace(-.9, .9, n)
        rng = np.random.default_rng(seed)
        self.fase = rng.uniform(0, 1, n)

    def _pos(self, x0, s, hx, hy, R, baixo, chao):
        cima = 30.0
        if s < .22:
            u = s / .22
            return hx + x0 * R * (1.18 - .18 * u), hy - cima * (1 - u)
        u = (s - .22) / .78
        y = hy + baixo * u
        x = hx + x0 * R * (1 - .16 * u)
        if chao is not None and y > chao - 4:
            extra = y - (chao - 4)
            y = chao - 4 - min(3.0, extra * .05)
            x = hx + math.copysign(abs(x0) * R * .84 + extra * 1.6, x0)
        return x, y

    def desenhar(self, tela, hx, hy, R, t, sentido=1.0, forca=1.0, chao=None, vel=1.0, cor=CIANO, alt=90):
        """hx, hy = cubo na tela; R = raio em px; sentido 1 = para baixo, -1 = para cima."""
        if abs(sentido) < .05 or forca <= 0: return
        baixo = (chao - hy + 40) if chao is not None else alt
        up = sentido < 0
        n_tr = 12
        for c, x0 in enumerate(self.cols):
            for k in range(n_tr):
                s = (k / n_tr + self.fase[c] * .08 + t * .32 * vel * abs(sentido)) % 1.0
                if (k + c) % 3 == 0 and forca < .6: continue
                pts = []
                for d in (0, .018, .036):
                    ss = s - d
                    if ss < 0: break
                    pts.append(self._pos(x0, 1 - ss, hx, hy, R, alt, None) if up else
                               self._pos(x0, ss, hx, hy, R, baixo, chao))
                if len(pts) < 2: continue
                x, y = pts[0]
                if not (0 <= y < PALCO_H) or abs(x - hx) > R * 2.3: continue
                perto = abs(y - hy) < 46
                for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                    tela.linha(xa, ya, xb, yb, cor if perto else ACO2)
                tela.px(x, y, BRANCO if perto else ACO3)


# =================================================================== chão de lado
class Campo:
    """Chão de grama com árvores ao longe e o heliponto. xm = quanto o mundo andou."""

    def __init__(self, seed=5):
        rng = np.random.default_rng(seed)
        self.arv = []
        x = 0
        while x < 1600:
            self.arv.append((x, rng.uniform(5, 13), int(rng.integers(0, 3))))
            x += int(rng.integers(8, 26))
        self.tufos = [(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(90)]

    def desenhar(self, tela, hy, gy, xm, t, heliponto=150, vento=0.0, vento_x=None):
        """hy = horizonte, gy = linha do chão onde o helicóptero pousa."""
        if hy >= PALCO_H: return
        off = (xm * .15) % 1600
        for (x, r, tipo) in self.arv:
            xx = x - off
            if xx < -20: xx += 1600
            if xx > W + 20: continue
            tela.disco(xx, hy - r * .5, r, FUNDO2)
            tela.disco(xx - r * .3, hy - r * .7, r * .55, FUNDO3)
        gradiente(tela, 0, hy, W, PALCO_H - hy, [(0, FUNDO2), (.25, AGUA0), (.7, FUNDO2), (1, FUNDO)])
        # faixas de grama (perspectiva: mais rápidas perto)
        for j, (fy, vel) in enumerate(((.15, .4), (.35, .7), (.6, 1.0), (.85, 1.4))):
            y = hy + (PALCO_H - hy) * fy
            for k in range(-1, 26):
                x = k * 22 - (xm * vel + j * 7) % 22
                tela.ret(x, y, 9, 1, AGUA1 if j % 2 else AGUA0)
        # tufos que deitam com o vento do rotor
        for (u, v) in self.tufos:
            x = (u * (W + 40) - xm) % (W + 40) - 20
            y = gy + 3 + v * (PALCO_H - gy - 4) if gy < PALCO_H - 6 else hy + v * (PALCO_H - hy)
            if y >= PALCO_H or y < hy: continue
            inc = 0
            if vento > 0 and vento_x is not None:
                d = x - vento_x
                if abs(d) < 120: inc = int(math.copysign(1, d) * 2 * vento * (1 - abs(d) / 120) * (1 + .5 * math.sin(t * 20 + u * 9)))
            tela.linha(x, y, x + inc, y - 3, AGUA1)
            tela.px(x + inc, y - 3, VERDE)
        # heliponto
        if heliponto is not None and gy < PALCO_H + 8:
            x = heliponto - xm
            if -60 < x < W + 60:
                ry = 5
                for (rx, c) in ((52, PRETO), (50, ACO1), (46, ACO0)):
                    pts = [(x + rx * math.cos(a), gy + 1 + ry * (rx / 50) * math.sin(a)) for a in np.linspace(0, 6.28, 30)]
                    pol(tela, pts, c)
                pts = [(x + 36 * math.cos(a), gy + 1 + 3.6 * math.sin(a)) for a in np.linspace(0, 6.28, 40)]
                for (a, b) in zip(pts, pts[1:]): tela.linha(*a, *b, AMARELO)
                # H achatado
                for dx in (-9, 7):
                    tela.ret(x + dx, gy - 1, 3, 4, BRANCO)
                tela.ret(x - 7, gy, 14, 2, BRANCO)
                tela.ret(x - 50, gy - 4, 100, 1, ACO2)


def chao_topo(tela, t, xm=0.0, ym=0.0, heliponto=True):
    """Chão visto de cima: grama em dither, trilhas e o heliponto com H."""
    dither(tela, 0, 0, W, PALCO_H, AGUA0, FUNDO2)
    for k in range(0, PALCO_H, 16):
        tela.ret(0, (k + ym) % PALCO_H, W, 1, FUNDO2)
    for j in range(40):
        x = (j * 53 + xm) % W; y = (j * 37 + ym) % PALCO_H
        tela.ret(x, y, 2, 1, AGUA1); tela.px(x + 1, y - 1, VERDE)
    if heliponto:
        cx, cy = 150, 88
        tela.disco(cx, cy, 82, ACO0)
        dither(tela, cx - 58, cy - 58, 116, 116, ACO0, ACO1)
        tela.anel(cx, cy, 82, ACO1, 1.5)
        tela.anel(cx, cy, 70, AMARELO, 1.2)
        for dx in (-22, 14):
            tela.ret(cx + dx, cy - 26, 8, 52, BRANCO)
        tela.ret(cx - 14, cy - 4, 28, 8, BRANCO)


# =================================================================== ícones do painel
def alavanca(tela, x, y, frac, destaque=False):
    """Alavanca do coletivo, de lado: pivô à esquerda; frac 0 = baixa, 1 = alta."""
    a = (-8 + 38 * frac) * RAD
    L = 34
    px, py = x + 2, y + 24
    ex, ey = px + math.cos(a) * L, py - math.sin(a) * L
    tela.ret(x - 2, y + 24, 12, 5, ACO1); tela.ret(x - 2, y + 24, 12, 1, ACO3)
    linha_grossa(tela, px, py, ex, ey, 5, PRETO)
    linha_grossa(tela, px, py, ex, ey, 3, AMARELO if destaque else ACO3)
    tela.disco(px, py, 2.5, ACO2)
    gx, gy = ex + math.cos(a) * 4, ey - math.sin(a) * 4
    linha_grossa(tela, ex, ey, gx, gy, 7, PRETO)
    linha_grossa(tela, ex, ey, gx, gy, 5, ACO1)
    # escala
    for k in range(5):
        aa = (-8 + 38 * k / 4) * RAD
        tela.px(px + math.cos(aa) * (L + 9), py - math.sin(aa) * (L + 9), ACO2)


def manche(tela, x, y, fx, fy, destaque=False):
    """Cíclico: caixa com cruz; o ponto mostra para onde o manche foi
    (fy = frente, para cima no ícone; fx = direita)."""
    tela.ret(x - 1, y - 1, 30, 30, PRETO)
    tela.ret(x, y, 28, 28, FUNDO2)
    tela.ret_vazado(x, y, 28, 28, ACO1)
    tela.ret(x + 14, y + 2, 1, 24, FUNDO3); tela.ret(x + 2, y + 14, 24, 1, FUNDO3)
    px, py = x + 14 + fx * 11, y + 14 - fy * 11
    tela.linha(x + 14, y + 14, px, py, ACO2)
    tela.disco(px, py, 3, PRETO); tela.disco(px, py, 2.2, AMARELO if destaque else ACO4)
    tela.px(x + 14, y + 1, ACO3); tela.px(x + 13, y + 2, ACO3); tela.px(x + 15, y + 2, ACO3)   # marca da frente


def pedais(tela, x, y, p, destaque=False):
    """p = -1 pedal esquerdo no fundo, +1 direito, 0 neutros."""
    for j, lado in enumerate((-1, 1)):
        fundo = max(0.0, p * lado)
        yy = y + int(fundo * 6) - int(max(0.0, -p * lado) * 3)
        xx = x + j * 22
        tela.ret(xx - 1, yy - 1, 16, 12, PRETO)
        tela.ret(xx, yy, 14, 10, AMARELO if (fundo > .3 and destaque) else ACO2)
        tela.ret(xx, yy, 14, 1, ACO4)
        for q in range(3): tela.ret(xx + 2, yy + 3 + q * 2, 10, 1, ACO1)
        tela.texto('E' if lado < 0 else 'D', xx + 4, yy + 13 + 1, ACO3, tam=9, contorno=PRETO)


def rpm_barra(tela, x, y, w, pct, verde=(.95, 1.04)):
    """Barra do giro do rotor de 0 a 115%, com a faixa verde."""
    tela.ret(x - 1, y - 1, w + 2, 8, ACO1)
    tela.ret(x, y, w, 6, FUNDO2)
    a, b = verde
    tela.ret(x + int(w * a / 1.15), y, max(1, int(w * (b - a) / 1.15)), 6, AGUA1)
    f = max(0.0, min(1.0, pct / 115.0))
    c = VERDE if a * 100 - .5 <= pct <= b * 100 + .5 else (AMARELO if pct > 80 else VERMELHO)
    xp = x + int(w * f)
    tela.ret(xp - 1, y - 2, 3, 10, PRETO); tela.ret(xp, y - 1, 1, 8, c)
