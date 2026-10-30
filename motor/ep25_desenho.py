#!/usr/bin/env python3
"""ep25 — desenho: o turbofan aberto ao meio, o modelo do ar, o avião, a pá da turbina.

  Modelo     o estado do ar ao longo do motor (pressão em vezes a de fora,
             temperatura em °C, velocidade relativa), CALCULADO: Brayton ideal
             com ar (gama 1,4), fan 1,5:1, 13 estágios com o mesmo salto até
             40:1, 1.500 °C na entrada da turbina, turbina de alta = trabalho
             do compressor de alta, turbina de baixa = fan (11 kg por kg do
             miolo) + booster; o bocal volta à pressão de fora.
  Turbofan   corte de um turbofan genérico, entrada à esquerda: o ar anda da
             esquerda para a direita. Unidades do motor: x de -100 (boca) a
             84 (ponta do cone de saída), r = raio (0 no eixo). Tudo vira
             pixel por uma câmera (cx, cy, k). Pás em projeção de giro de
             verdade (cada pá no ângulo teta aparece em y = r cos teta), com
             borrão quando gira rápido; as partículas do ar andam com a
             velocidade do modelo e têm a cor da temperatura.
  Aviao      bimotor genérico de lado, nariz para a esquerda (como o motor).
  Pa         a pá da turbina em corte, com canais de ar e furos de filme.
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
          '#2d6334', '#4f8f44', '#8a8478', '#55524c',                            # 38..41 grama, concreto, asfalto
          '#2f5bff', '#5b3fe0', '#9a32c8', '#d93087', '#ff3a3a', '#ff7a1f',      # 42..47 escala de calor
          '#ffc21f', '#fff3a0',                                                  # 48..49
          '#f2f6fc', '#c3cbd8', '#8e97a8',                                       # 50..52 casco do avião
          '#7fe0ff', '#c4f2ff']                                                  # 53..54 ar frio de resfriamento
PX.PALETAS['ep25'] = _BASE + _EXTRA
LG.PAL = 'ep25'
CEU0, CEU1, CEU2, CEU3, CEU4, CEU5 = 32, 33, 34, 35, 36, 37
GRAMA0, GRAMA1, CONCRETO, ASFALTO = 38, 39, 40, 41
Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7 = 42, 43, 44, 45, 46, 47, 48, 49
CASCO, CASCO2, CASCO3 = 50, 51, 52
FRIO0, FRIO1 = 53, 54

ESCALA_CALOR = [(15, Q0), (90, Q1), (200, Q2), (350, Q3), (550, Q4), (800, Q5), (1100, Q6), (1400, Q7),
                (1600, BRANCO)]
_CT = np.array([a for a, _ in ESCALA_CALOR], float)
_CC = [c for _, c in ESCALA_CALOR]


def hsh(i, k=0):
    """Ruído determinístico 0..1."""
    x = math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


def cor_calor(T, sel=0.5):
    """Cor da temperatura T (°C); `sel` 0..1 escolhe entre as 2 cores vizinhas
    (dither: passe o valor de Bayer do pixel ou um número da partícula)."""
    if T <= _CT[0]: return _CC[0]
    if T >= _CT[-1]: return _CC[-1]
    i = int(np.searchsorted(_CT, T)) - 1
    u = (T - _CT[i]) / (_CT[i + 1] - _CT[i])
    return _CC[i + 1] if u > sel else _CC[i]


def escala_calor(tela, x, y, w, h, Tmax=1600):
    """Barrinha horizontal com a escala de cor da temperatura."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, ACO1)
    for i in range(w):
        T = 15 + (Tmax - 15) * i / max(1, w - 1)
        for j in range(h):
            tela.px(x + i, y + j, cor_calor(T, BAY[j % 8, i % 8]))


def milhar(n): return f"{int(round(n)):,}".replace(',', '.')
def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')


# =================================================================== o modelo do ar
class Modelo:
    """Estado do ar no miolo e por fora (bypass) em função de x (unidades do motor)."""
    T0, P0 = 288.15, 1.0
    PI_FAN, PI_TOT, T4 = 1.5, 40.0, 1773.15
    BPR = 10.0
    G = 1.4
    E = .4 / 1.4                       # (gama - 1) / gama
    BOOST = [-58.0, -53.0, -48.0]
    HPC = [-38.0 + 4 * i for i in range(10)]
    HPT = [27.5, 31.0]
    LPT = [37.0, 41.5, 46.0, 50.5, 55.0]
    X_FAN = -77.0

    def __init__(self):
        e = self.E
        rot = self.BOOST + self.HPC
        pi_e = (self.PI_TOT / self.PI_FAN) ** (1 / 13)
        p = [self.PI_FAN * pi_e ** (i + 1) for i in range(13)]
        T2 = self.T0 * self.PI_FAN ** e                         # depois do fan
        Tc = [T2 * (pp / self.PI_FAN) ** e for pp in p]
        self.T2, self.T3 = T2, Tc[-1]
        T_boost = Tc[2]
        # turbina de alta: trabalho do compressor de alta; de baixa: fan (11 kg) + booster
        dT_hpt = self.T3 - T_boost
        dT_lpt = (self.BPR + 1) * (T2 - self.T0) + (T_boost - T2)
        T45 = self.T4 - dT_hpt
        T5 = T45 - dT_lpt
        Tt = [self.T4 - dT_hpt * (i + 1) / 2 for i in range(2)] + [T45 - dT_lpt * (i + 1) / 5 for i in range(5)]
        pt = [self.PI_TOT * (TT / self.T4) ** (1 / e) for TT in Tt]
        self.T45, self.T5, self.p45, self.p5 = T45, T5, pt[1], pt[-1]
        T9 = T5 * (1 / pt[-1]) ** e
        self.T9 = T9
        # nós (x, p, T em K) do miolo
        nos = [(-260, 1.0, self.T0), (-81, 1.0, self.T0), (-73, self.PI_FAN, T2), (-60, self.PI_FAN, T2)]
        for x, pp, TT in zip(rot, p, Tc):
            nos += [(x - 1.2, nos[-1][1], nos[-1][2]), (x + 2.0, pp, TT)]
        nos += [(6.0, self.PI_TOT, self.T3), (22.0, self.PI_TOT, self.T4)]
        for x, pp, TT in zip(self.HPT + self.LPT, pt, Tt):
            nos += [(x - 2.6, nos[-1][1], nos[-1][2]), (x + 1.0, pp, TT)]
        nos += [(60.0, pt[-1], T5), (68.0, 1.0, T9), (110.0, 1.0, T9 * .75 + self.T0 * .25), (260.0, 1.0, self.T0 + 40)]
        self.nx = np.array([a for a, _, _ in nos]); self.np_ = np.array([b for _, b, _ in nos])
        self.nT = np.array([c for _, _, c in nos])
        # bypass
        self.bx = np.array([-260, -81, -73, 10, 34, 80, 260.0])
        self.bp = np.array([1.0, 1.0, self.PI_FAN, self.PI_FAN, 1.0, 1.0, 1.0])
        self.bT = np.array([self.T0, self.T0, T2, T2, self.T0 + 8, self.T0, self.T0])
        # velocidade de desenho (unidades/s) — só relativa: devagar no compressor, rápida no bocal
        self.vx = np.array([-260, -105, -82, -66, -60, 0, 4, 24, 26, 58, 70, 90, 260.0])
        self.vv = np.array([40, 44, 56, 50, 34, 30, 26, 26, 52, 60, 120, 165, 165.0])
        self.wx = np.array([-260, -105, -82, -70, 10, 34, 70, 260.0])
        self.wv = np.array([40, 44, 56, 60, 62, 105, 120, 120.0])
        # tempo de percurso tau(x) = integral dx / v: as partículas andam com a velocidade do modelo
        self.gx = np.linspace(-260, 260, 5201)
        for nome, (xs, vs) in (('c', (self.vx, self.vv)), ('b', (self.wx, self.wv))):
            v = np.interp(self.gx, xs, vs)
            tau = np.concatenate([[0], np.cumsum(np.diff(self.gx) / ((v[1:] + v[:-1]) / 2))])
            setattr(self, 'tau_' + nome, tau)

    def p(self, x): return float(np.interp(x, self.nx, self.np_))
    def T(self, x): return float(np.interp(x, self.nx, self.nT)) - 273.15
    def v(self, x): return float(np.interp(x, self.vx, self.vv))
    def pb(self, x): return float(np.interp(x, self.bx, self.bp))
    def Tb(self, x): return float(np.interp(x, self.bx, self.bT)) - 273.15

    def x_de_tau(self, tau, nome='c'):
        return np.interp(tau, getattr(self, 'tau_' + nome), self.gx)

    def tau_de_x(self, x, nome='c'):
        return float(np.interp(x, self.gx, getattr(self, 'tau_' + nome)))

    def onde(self, x):
        """(nome do lugar, estágio, total, tempo 0..3) do ar do miolo em x."""
        if x < -100: return ('LÁ FORA', 0, 0, 0)
        if x < -81: return ('ENTRADA', 0, 0, 0)
        if x < -70: return ('FAN', 0, 0, 0)
        if x < -60: return ('MIOLO', 0, 0, 1)
        if x < 3:
            rot = self.BOOST + self.HPC
            k = sum(1 for r in rot if x >= r - 1.2)
            return ('COMPRESSOR', max(1, k), 13, 1)
        if x < 24: return ('CÂMARA', 0, 0, 2)
        if x < 58:
            rot = self.HPT + self.LPT
            k = sum(1 for r in rot if x >= r - 2.6)
            return ('TURBINA', max(1, k), 7, 3)
        if x < 70: return ('BOCAL', 0, 0, 3)
        return ('JATO', 0, 0, 3)


MOD = Modelo()
TEMPOS = [('SUGA', MISTURA), ('ESPREME', VERDE), ('QUEIMA', LARANJA), ('SOPRA', ROXO)]   # as cores do ep01


# =================================================================== geometria do turbofan
NAC_OUT = [(-100, 47.5), (-98.5, 50.5), (-95, 52.6), (-88, 54.2), (-70, 55.2), (-30, 54.4), (0, 51.6), (20, 47.5),
           (34, 41.8)]
NAC_IN = [(-100, 45.6), (-94, 45.9), (-84, 46.3), (-72, 46.2), (-50, 45.2), (-20, 43.6), (10, 41.6), (34, 39.6)]
CB = [(-63, 20.6), (-60, 22.4), (-54, 24.0), (-40, 25.0), (-10, 25.4), (20, 25.2), (38, 23.6), (52, 21.2), (68, 17.4)]
CC = [(-63, 19.6), (-60, 19.0), (-46, 18.6), (-40, 18.0), (-2, 12.6), (2, 12.6), (5, 16.2), (23, 16.2),
      (25.5, 13.6), (33, 14.0), (57, 19.2), (62, 18.4), (68, 16.8)]
HUB = [(-74, 10.0), (-63, 10.5), (-46, 10.0), (-40, 9.6), (-2, 10.2), (2, 10.2), (5, 6.0), (23, 6.0), (25.5, 9.0),
       (33, 9.4), (57, 10.6), (62, 9.8), (70, 6.4), (84, 0.0)]
SPINNER = [(-98, 0), (-97, 2.2), (-94.5, 4.4), (-90.5, 6.6), (-85, 8.5), (-79, 9.7), (-74, 10.0)]
COMB = (5.5, 23.5)                     # câmara de combustão (x)
LINER = (8.0, 14.2)                    # tubo de chama (raio)


def _f(pts):
    xs = np.array([a for a, _ in pts], float); rs = np.array([b for _, b in pts], float)
    return lambda x: float(np.interp(x, xs, rs))


r_nac_in, r_nac_out, r_cb, r_cc, r_hub = _f(NAC_IN), _f(NAC_OUT), _f(CB), _f(CC), _f(HUB)


def r_meio(x):
    """Raio da linha do meio do caminho do ar do miolo (o nosso pedacinho de ar)."""
    if x < -100: return 15.0
    if x < -63:
        u = (x + 100) / 37
        return 15.0 * (1 - u) + 15.0 * u
    if x <= 84:
        return (r_hub(x) + r_cc(min(x, 68))) / 2 if x < 68 else 9.0 * (1 - (x - 68) / 40)
    return max(2.0, 9.0 - (x - 68) * .1)


class Camera:
    def __init__(self, cx, cy, k):
        self.cx, self.cy, self.k = cx, cy, k

    def P(self, x, r, lado=-1):
        return (self.cx + x * self.k, self.cy + lado * r * self.k)

    def L(self, pts, lado=-1):
        return [self.P(x, r, lado) for x, r in pts]


class Turbofan:
    """Corte do turbofan. `desenhar(tela, cam, t, **o)`; opções:
       giro       fator de rotação (0 = parado, 1 = normal)
       chama      0..1 (a câmara acesa)
       ar         0..1 densidade das partículas (0 = sem ar)
       aceso      dict {('c', i) ou ('t', i): 0..1} estágios iluminados
       foco       None ou 'fan' 'compressor' 'camara' 'turbina' 'eixos' 'bocal' (escurece o resto)
       spools     True: pinta o eixo de baixa (verde) e o de alta (laranja)
       zonas      0..1: as 4 zonas dos tempos acesas (SUGA ESPREME QUEIMA SOPRA)
       jato       0..1 (o jato de saída)
       fechado    True: nacele inteira (sem corte) — o motor visto de fora."""
    ROT_C = [(x, 'LP', 2.2) for x in MOD.BOOST] + [(x, 'HP', 1.8) for x in MOD.HPC]
    ROT_T = [(x, 'HP', 2.0) for x in MOD.HPT] + [(x, 'LP', 2.2) for x in MOD.LPT]

    def __init__(self, seed=2):
        rng = np.random.default_rng(seed)
        self.pc = [(rng.uniform(.08, .92), rng.uniform(0, 1), rng.integers(0, 2) * 2 - 1, rng.uniform())
                   for _ in range(150)]
        self.pb = [(rng.uniform(.06, .94), rng.uniform(0, 1), rng.integers(0, 2) * 2 - 1, rng.uniform())
                   for _ in range(130)]
        self.tc_tot = MOD.tau_de_x(200, 'c') - MOD.tau_de_x(-150, 'c')
        self.tb_tot = MOD.tau_de_x(200, 'b') - MOD.tau_de_x(-150, 'b')
        self.tc0 = MOD.tau_de_x(-150, 'c'); self.tb0 = MOD.tau_de_x(-150, 'b')

    # --------------------------------------------------------------- pás
    def _rotor(self, tela, cam, x, r0, r1, w, n, fase, cores, borrao=0.0, aceso=0.0, quente=0.0):
        """Fileira de pás girando, em projeção (y = r cos teta). cores = (luz, meio, sombra)."""
        k = cam.k
        cl, cm, cs = cores
        if aceso > .05:
            cl, cm, cs = BRANCO, AMARELO, (LARANJA if aceso > .5 else cm)
        X0 = cam.cx + (x - w / 2) * k
        ww = max(1, int(round(w * k)))
        varre = w * .35                                      # a ponta da pá um pouco para trás
        for lado in (-1, 1):
            luz = lado < 0
            pa = cam.L([(x - w / 2, r0), (x + w / 2, r0), (x + w / 2 + varre, r1), (x - w / 2 + varre * .4, r1)], lado)
            if ww >= 3: contorno(tela, pa, PRETO)
            if borrao > .3:
                pol(tela, pa, cm if luz else cs, FUNDO3 if borrao > .7 else (cl if luz else cm), fase=int(x))
            else:
                pol(tela, pa, cm if luz else cs)
            # bordo de ataque claro
            a, b = cam.P(x - w / 2, r0, lado), cam.P(x - w / 2 + varre * .4, r1, lado)
            tela.linha(a[0], a[1], b[0], b[1], cl)
        # o giro: as pás passando (cada pá no ângulo teta cruza a fileira em y = r1 cos teta,
        # sempre descendo do lado de cá), com rastro de borrão
        for j in range(n):
            th = fase + 2 * math.pi * j / n
            if math.sin(th) <= 0: continue
            for dt_, cor in ((0.0, cl), (-.12, cm), (-.24, cs)):
                if dt_ < 0 and borrao < .3: continue
                yy = r1 * math.cos(th + dt_)
                if abs(yy) < r0 + .4: continue
                frac = (abs(yy) - r0) / max(.1, r1 - r0)
                lado = -1 if yy < 0 else 1
                xa = x - w / 2 + varre * .4 * frac
                xb = x + w / 2 + varre * frac
                pa, pb = cam.P(xa, abs(yy), lado), cam.P(xb, abs(yy), lado)
                tela.ret(int(pa[0]) + 1, int(pa[1]), max(1, int(pb[0] - pa[0]) - 1), 1, cor if dt_ < 0 else BRANCO
                         if aceso <= .05 else cor)
        if quente > 0:
            for lado in (-1, 1):
                ym = cam.cy + lado * (r0 + r1) / 2 * k
                brilho(tela, X0 + ww / 2, ym, (r1 - r0) * k * .55 * quente, BRASA)

    def _estator(self, tela, cam, x, r0, r1, w, cor=ACO1, cor2=ACO2):
        k = cam.k
        for lado in (-1, 1):
            ya, yb = cam.cy + lado * r0 * k, cam.cy + lado * r1 * k
            y0, y1 = min(ya, yb), max(ya, yb)
            xx = cam.cx + (x - w / 2) * k
            ww = max(1, int(round(w * k * .6)))
            tela.ret(int(xx), int(y0), ww, max(1, int(y1 - y0)), cor)
            tela.ret(int(xx), int(y0), 1, max(1, int(y1 - y0)), cor2)

    # --------------------------------------------------------------- desenho
    def desenhar(self, tela, cam, t, giro=1.0, chama=1.0, ar=1.0, aceso=None, foco=None, spools=False, zonas=0.0,
                 jato=1.0, fechado=False, x1=W):
        k = cam.k
        aceso = aceso or {}
        P, L = cam.P, cam.L
        if fechado:
            self._fechado(tela, cam, t, giro)
            return
        # ---- fundo dos dutos (escuro), as duas metades
        for lado in (-1, 1):
            duto = [(x, r_nac_in(x)) for x in np.linspace(-100, 34, 14)] + \
                   [(x, r_hub(x) if x >= -74 else 0.0) for x in np.linspace(34, -100, 16)]
            pol(tela, L(duto, lado), FUNDO, FUNDO2, fase=0)
        # ---- jato de saída (atrás de tudo)
        if jato > 0:
            self._jato(tela, cam, t, jato * ar, chama)
        # ---- zonas dos 4 tempos (fundo colorido)
        if zonas > 0:
            for (xa, xb), (_, cor) in zip(((-100, -63), (-63, 3), (3, 24), (24, 84)), TEMPOS):
                for lado in (-1, 1):
                    pts = [(xa, r_cc(max(xa, -63)) if xa >= -63 else 46), (xb, r_cc(min(xb, 68)) if xb <= 68 else 2)]
                    zona = [(x, (r_cc(x) if x >= -63 else 45.0) if x <= 68 else max(1, 17 - (x - 68))) for x in
                            np.linspace(xa, xb, 6)] + [(x, r_hub(x) if x >= -74 else 0) for x in np.linspace(xb, xa, 6)]
                    if zonas >= .99: pol(tela, L(zona, lado), cor, FUNDO2)
                    else: pol(tela, L(zona, lado), cor, FUNDO, fase=int(t * 8))
        # ---- fan
        fL = t * 1.1 * giro * 2 * math.pi           # eixo de baixa (fan): gira mais devagar
        fH = t * 1.9 * giro * 2 * math.pi           # eixo de alta
        borrao = min(1.0, giro)
        sLP, sHP = spools in (True, 'LP'), spools in (True, 'HP')
        cor_lp = (VERDE, GRAMA1, GRAMA0) if sLP else None
        cor_hp = (CHAMA1, LARANJA, BRASA) if sHP else None
        self._rotor(tela, cam, -77, 9.5, 46.0, 8.0, 18, fL, cor_lp or (ACO4, ACO3, ACO1), borrao * .8,
                    aceso.get(('f', 0), 0.0))
        # estatores atrás do fan (por fora) e na entrada do miolo
        self._estator(tela, cam, -67, 25.0, 45.6, 2.0, ACO0, ACO1)
        self._estator(tela, cam, -61, 10.6, 19.3, 1.6)
        # ---- compressor (13 estágios)
        for i, (x, sp, w) in enumerate(self.ROT_C):
            r0, r1 = r_hub(x) + .2, r_cc(x) - .2
            fase = (fL if sp == 'LP' else fH) + i * .7
            cores = (cor_lp if sp == 'LP' else cor_hp) or (ACO3, ACO2, ACO1)
            self._rotor(tela, cam, x, r0, r1, w, 14, fase, cores, borrao, aceso.get(('c', i), 0.0))
            self._estator(tela, cam, x + w / 2 + 1.0, r_hub(x + 2) + .2, r_cc(x + 2) - .2, 1.2)
        # ---- turbina (2 de alta + 5 de baixa)
        for i, (x, sp, w) in enumerate(self.ROT_T):
            r0, r1 = r_hub(x) + .2, r_cc(x) - .2
            fase = (fL if sp == 'LP' else fH) + i * .9
            q = max(0.0, 1 - i / 4) * chama
            cores = ((cor_lp if sp == 'LP' else cor_hp) or
                     ((CHAMA1, LATAO, BRASA) if q > .6 else ((LATAO, ACO3, ACO1) if q > .2 else (ACO3, ACO2, ACO1))))
            self._estator(tela, cam, x - w / 2 - 1.2, r_hub(x - 2) + .2, r_cc(x - 2) - .2, 1.3,
                          BRASA if q > .5 else ACO1, LARANJA if q > .5 else ACO2)
            self._rotor(tela, cam, x, r0, r1, w, 16, fase, cores, borrao, aceso.get(('t', i), 0.0), quente=q * .7)
        # ---- câmara de combustão: tubo de chama e bicos
        self._camara(tela, cam, t, chama)
        # ---- partículas de ar
        if ar > 0:
            self._ar(tela, cam, t, ar, chama)
        # ---- corpos sólidos: nacele, carenagem do miolo, cubo com os eixos
        for lado in (-1, 1):
            luz = lado < 0
            nac = L(NAC_OUT, lado) + L(NAC_IN[::-1], lado)
            contorno(tela, nac, PRETO)
            pol(tela, nac, ACO3 if luz else ACO2, ACO2 if luz else ACO1)
            tela.linha(*P(-97, 51.5, lado), *P(20, 48.5, lado), ACO4 if luz else ACO3)
            # lábio da entrada
            tela.disco(*P(-99.4, 46.6, lado), max(1, 1.2 * k), CASCO if luz else ACO3)
            cb = L(CB, lado) + L(CC[::-1], lado)
            contorno(tela, cb, PRETO)
            pol(tela, cb, ACO2 if luz else ACO1, ACO1 if luz else ACO0)
            tela.linha(*P(-60, 22.6, lado), *P(52, 21.4, lado), ACO3 if luz else ACO2)
        self._cubo(tela, cam, t, fL, fH, sLP, sHP)
        # ---- foco: escurece o que não é a peça da vez
        if foco:
            faixas = dict(fan=(-84, -68), compressor=(-62, 2), camara=(3, 25), turbina=(24, 58), bocal=(56, 92),
                          eixos=None)
            fx = faixas.get(foco)
            if fx:
                a, b = cam.cx + fx[0] * k, cam.cx + fx[1] * k
                y0, y1 = cam.cy - 56 * k, cam.cy + 56 * k
                _escurecer(tela, 0, y0, a, y1 - y0)
                _escurecer(tela, b, y0, x1 - b, y1 - y0)

    def _fechado(self, tela, cam, t, giro):
        """O motor visto de fora: nacele inteira, o fan na boca, o cone de saída."""
        k = cam.k
        P, L = cam.P, cam.L
        top = NAC_OUT
        corpo = L(top, -1) + L(top[::-1], 1)
        contorno(tela, corpo, PRETO)
        pol(tela, corpo, CASCO2)
        for lado, cor, c2 in ((-1, CASCO, CASCO2), (1, CASCO3, CASCO2)):
            faixa = L([(x, r * .2) for x, r in top], lado) + L([(x, r * .95) for x, r in top[::-1]], lado)
            pol(tela, faixa, cor, c2 if lado < 0 else None)
        tela.linha(*P(-96, 52, -1), *P(20, 47.5, -1), BRANCO)
        # miolo saindo atrás
        cone = L([(34, 25), (52, 21.2), (68, 17.4)], -1) + L([(68, 17.4), (52, 21.2), (34, 25)], 1)
        contorno(tela, cone, PRETO)
        pol(tela, cone, ACO2, ACO1)
        plug = L([(66, 9.8), (70, 6.4), (84, 0)], -1) + L([(84, 0), (70, 6.4), (66, 9.8)], 1)
        pol(tela, plug, ACO3, ACO2)
        # boca: o fan visto de frente, girando (elipse)
        cx, cy = P(-100, 0)
        a, b = 3.0 * k, 45.6 * k
        yy = np.arange(int(cy - b), int(cy + b) + 1)
        for y in yy:
            u = (y - cy) / b
            wv = a * math.sqrt(max(0.0, 1 - u * u))
            tela.ret(int(cx - wv), int(y), max(1, int(2 * wv) + 1), 1, FUNDO2)
        n = 18
        for j in range(n):
            th = t * 1.1 * giro * 2 * math.pi + 2 * math.pi * j / n
            y = cy + math.cos(th) * b * .92
            if math.sin(th) > 0:
                tela.ret(int(cx - a * .6), int(y) - 1, max(1, int(a * 1.2)), 2, ACO3)
        tela.disco(cx, cy, max(1.5, 4 * k), ACO3)
        tela.disco(cx - .5, cy - .5, max(1, 2 * k), BRANCO)

    def _cubo(self, tela, cam, t, fL, fH, sLP, sHP):
        k = cam.k
        P, L = cam.P, cam.L
        spools = sLP or sHP
        corLP = (VERDE, GRAMA1) if sLP else (ACO3, ACO2)
        corHP = (CHAMA1, LARANJA) if sHP else (ACO4, ACO3)
        for lado in (-1, 1):
            cubo = L([(x, r) for x, r in HUB], lado) + [P(84, 0, lado), P(-74, 0, lado)]
            contorno(tela, cubo, PRETO)
            pol(tela, cubo, FUNDO3, FUNDO2)
            # discos das pás: ligam cada fileira ao seu eixo
            for i, (x, sp, w) in enumerate(self.ROT_C + self.ROT_T):
                re = 2.2 if sp == 'LP' else 5.4
                a, b = P(x - .5, r_hub(x), lado), P(x - .5, re, lado)
                tela.ret(int(a[0]), int(min(a[1], b[1])), max(1, int(k * .9)), max(1, int(abs(b[1] - a[1]))),
                         (corLP if sp == 'LP' else corHP)[1] if (sLP if sp == 'LP' else sHP) else ACO1)
            # disco do fan
            a, b = P(-78, 10, lado), P(-78, 2.2, lado)
            tela.ret(int(a[0]), int(min(a[1], b[1])), max(1, int(k * 1.6)), max(1, int(abs(b[1] - a[1]))),
                     corLP[1] if sLP else ACO2)
            # eixo de alta (oco): r 3..5,4 de x -40 a 32
            x0, y0 = P(-40, 5.4, lado); x1_, y1_ = P(32.5, 3.2, lado)
            tela.ret(int(x0), int(min(y0, y1_)), int(x1_ - x0), max(1, int(abs(y1_ - y0))), corHP[1])
            tela.ret(int(x0), int(y0 if lado < 0 else y1_ - 1), int(x1_ - x0), 1, corHP[0])
            # marcas do giro andando no eixo de alta
            for j in range(10):
                xx = -38 + ((j * 7.3 + fH * 1.2) % 70)
                a = P(xx, 5.0, lado)
                tela.ret(int(a[0]), int(min(a[1], P(xx, 3.4, lado)[1])), max(1, int(k * .7)),
                         max(1, int(2 * k)), corHP[0] if j % 2 else PRETO)
        # eixo de baixa (maciço, no meio): de x -78 a 57
        x0, y0 = P(-79, 2.2, -1); x1_, y1_ = P(57, 2.2, 1)
        tela.ret(int(x0), int(y0), int(x1_ - x0), max(1, int(y1_ - y0)), corLP[1])
        tela.ret(int(x0), int(y0), int(x1_ - x0), max(1, int(k * .8)), corLP[0])
        for j in range(14):
            xx = -76 + ((j * 9.7 + fL * 1.4) % 132)
            a = P(xx, 2.0, -1)
            tela.ret(int(a[0]), int(a[1]), max(1, int(k * .6)), max(1, int(4 * k)), PRETO if j % 2 else corLP[0])
        # cone da frente (spinner) e cone de saída
        for lado in (-1, 1):
            sp = L(SPINNER, lado) + [P(-74, 0, lado)]
            contorno(tela, sp, PRETO)
            pol(tela, sp, ACO4 if lado < 0 else ACO2, ACO3 if lado < 0 else ACO1)
        a = P(-93, 3, -1)
        tela.ret(int(a[0]), int(a[1]), max(1, int(k)), max(1, int(k)), BRANCO)

    def _camara(self, tela, cam, t, chama):
        k = cam.k
        P, L = cam.P, cam.L
        xa, xb = COMB
        ri, ro = LINER
        for lado in (-1, 1):
            # chama dentro do tubo
            if chama > 0:
                for i in range(int(46 * chama)):
                    u = (hsh(i, 1) + t * 1.6) % 1.0
                    x = xa + 3 + u * (xb - xa - 3)
                    r = (ri + ro) / 2 + (hsh(i, 2) - .5) * (ro - ri) * (.5 + .5 * u) + math.sin(t * 9 + i) * .6
                    px, py = P(x, r, lado)
                    c = CHAMA0 if u < .3 else (CHAMA1 if u < .6 else (CHAMA2 if u < .85 else BRASA))
                    sz = max(1, int(k * (1.4 - u * .7)))
                    tela.ret(int(px), int(py), sz, sz, c)
                cx, cy = P(xa + 7, (ri + ro) / 2, lado)
                brilho(tela, cx + 2 * k, cy, (ro - ri) * k * .9 * chama, CHAMA1)
                tela.disco(cx, cy, max(1, 1.6 * k * chama), CHAMA0)
            # paredes do tubo de chama, com furos
            for r in (ri, ro):
                a, b = P(xa + 2, r, lado), P(xb, r, lado)
                tela.ret(int(a[0]), int(a[1]) - (0 if lado > 0 else 0), int(b[0] - a[0]), max(1, int(k * .5)), ACO3)
                for j in range(6):
                    xx = xa + 5 + j * 3
                    h = P(xx, r, lado)
                    tela.px(int(h[0]), int(h[1]), PRETO)
            # cúpula (frente do tubo) e o bico de combustível
            cup = L([(xa + 2, ri), (xa + .5, ri + 1.5), (xa, (ri + ro) / 2), (xa + .5, ro - 1.5), (xa + 2, ro)], lado)
            for (x0, y0), (x1_, y1_) in zip(cup, cup[1:]):
                tela.linha(x0, y0, x1_, y1_, ACO3)
            bico = L([(xa - 1.5, r_cc(xa) - .2), (xa + 1.2, (ri + ro) / 2 + .6), (xa + 1.2, (ri + ro) / 2 - .6),
                      (xa - 1.5, r_cc(xa) - 1.5)], lado)
            pol(tela, bico, LATAO)
            if chama > 0:
                for i in range(8):
                    u = (hsh(i, 7) + t * 3) % 1.0
                    x = xa + 1.5 + u * 4
                    r = (ri + ro) / 2 + (hsh(i, 8) - .5) * u * 3
                    px, py = P(x, r, lado)
                    tela.px(int(px), int(py), OLEO1)

    def _ar(self, tela, cam, t, ar, chama):
        k = cam.k
        P = cam.P
        n = int(len(self.pc) * ar)
        taus = self.tc0 + (np.array([p[1] for p in self.pc[:n]]) * self.tc_tot + t) % self.tc_tot
        xs = MOD.x_de_tau(taus, 'c')
        for (u0, _, lado, sel), x in zip(self.pc[:n], xs):
            if x < -150 or x > 200: continue
            if x < -63:
                rr = 10.5 + u0 * (r_nac_in(max(x, -100)) - 10.5) * .2 + u0 * 8 if x >= -100 else 4 + u0 * 18
            elif x <= 68:
                if COMB[0] < x < COMB[1]:
                    rr = LINER[0] + .5 + u0 * (LINER[1] - LINER[0] - 1)
                else:
                    rr = r_hub(x) + .4 + u0 * (r_cc(x) - r_hub(x) - .8)
            else:
                rr = (1 + u0 * 15) * max(.55, 1 - (x - 68) / 160)
            T = MOD.T(x) if chama > .3 or x < COMB[0] else MOD.T(min(x, COMB[0]))
            c = cor_calor(T, sel)
            vel = MOD.v(x)
            ln = max(1, int(k * (.6 + vel / 70)))
            px, py = P(x, rr, lado)
            tela.ret(int(px) - ln + 1, int(py), ln, 1, c)
        nb = int(len(self.pb) * ar)
        taus = self.tb0 + (np.array([p[1] for p in self.pb[:nb]]) * self.tb_tot + t) % self.tb_tot
        xs = MOD.x_de_tau(taus, 'b')
        for (u0, _, lado, sel), x in zip(self.pb[:nb], xs):
            if x < -150 or x > 200: continue
            if x < -100: rr = 20 + u0 * 26
            elif x < -63: rr = 20.5 + u0 * (r_nac_in(x) - 21.5)
            elif x <= 34: rr = r_cb(x) + .5 + u0 * (r_nac_in(x) - r_cb(x) - 1)
            else: rr = r_cb(min(x, 68)) + .5 + u0 * (39.6 - r_cb(34)) * max(.6, 1 - (x - 34) / 200) if x < 68 else 17 + u0 * 18
            c = FRIO1 if sel > .55 else (FRIO0 if sel > .2 else CIANO)
            vel = float(np.interp(x, MOD.wx, MOD.wv))
            ln = max(1, int(k * (.6 + vel / 70)))
            px, py = P(x, rr, lado)
            tela.ret(int(px) - ln + 1, int(py), ln, 1, c)

    def _jato(self, tela, cam, t, forca, chama):
        """Pluma de saída: o gás quente no meio, o ar frio do fan em volta."""
        k = cam.k
        P = cam.P
        if chama > .2:
            for lado in (-1, 1):
                pl = cam.L([(68, 16.6), (110, 18), (150, 20), (150, 0), (84, 0), (70, 6.4)], lado)
                pol(tela, pl, Q2, FUNDO, fase=int(t * 12))
            for i in range(60):
                u = (hsh(i, 3) + t * 1.4) % 1.0
                x = 70 + u * 90
                r = (hsh(i, 4) - .5) * 2 * (6 + u * 10)
                px, py = P(x, r, 1)
                c = cor_calor(MOD.T(x), hsh(i, 5))
                tela.ret(int(px), int(py), max(1, int(k * (1.8 - u))), 1, c)


def _escurecer(tela, x, y, w, h):
    """Apaga metade dos pixels de uma área em xadrez (fora de foco, sem alfa)."""
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(tela.w, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def parcela(tela, cam, x, t, lado=-1, raio=3.2, aceso=1.0, rastro=True):
    """O nosso pedacinho de ar: bolinha com a cor da temperatura, contorno e rastro."""
    k = cam.k
    r = r_meio(x)
    px, py = cam.P(x, r, lado)
    T = MOD.T(x)
    cor = cor_calor(T, .5)
    if rastro:
        for j in range(1, 6):
            xx = x - j * 2.2 * max(.6, MOD.v(x) / 50) / max(.6, k / 1.4) * 1.4
            qx, qy = cam.P(xx, r_meio(xx), lado)
            tela.disco(qx, qy, max(.8, raio * (1 - j / 6)), cor_calor(MOD.T(xx), .5) if j % 2 else FUNDO3)
    pulso = 1 + .25 * math.sin(t * 8)
    brilho(tela, px, py, raio * 2.4 * pulso * aceso, BRANCO)
    tela.disco(px, py, raio + 1.2, PRETO)
    tela.disco(px, py, raio, cor)
    tela.disco(px - raio * .35, py - raio * .35, max(.8, raio * .35), BRANCO)
    return px, py


# =================================================================== o avião (nariz à esquerda)
FUS = [(52, -3.0), (44, -5.4), (30, -6.0), (-38, -6.0), (-43, -5.4), (-47, -4.2), (-50, -2.4), (-51.6, 0.0),
       (-51, 1.8), (-48, 3.6), (-42, 4.8), (-30, 5.2), (14, 5.2), (24, 4.6), (36, 2.6), (46, -0.4), (52, -2.0)]
LEME = [(29, -5.8), (44, -24), (51, -24), (50.5, -20), (47, -4.6)]
ESTAB = [(37, 0.6), (45, 0.0), (55, 3.6), (51, 4.0)]
ASA = [(-12, 2.6), (2, 2.8), (20, 9.4), (15, 9.6)]


class Aviao:
    """Bimotor genérico de lado, nariz à esquerda, branco, sem pintura de companhia."""

    def desenhar(self, tela, ox, oy, s, ang=0.0, t=0.0, giro=1.0, trem=0.0, empuxo=0.0):
        ca, sa = math.cos(ang), math.sin(ang)

        def P(x, y): return (ox + (x * ca - y * sa) * s, oy + (x * sa + y * ca) * s)

        def L(pts): return [P(x, y) for x, y in pts]
        # asa do outro lado (atrás)
        asa2 = L([(-8, 1.6), (4, 1.8), (17, -2.6), (13, -2.8)])
        pol(tela, asa2, CASCO3, ACO1)
        # estabilizador do outro lado
        pol(tela, L([(38, -1.0), (46, -1.4), (52, -5.2), (49, -5.4)]), CASCO3)
        # leme
        contorno(tela, L(LEME), PRETO)
        pol(tela, L(LEME), CASCO2, CASCO)
        # fuselagem
        contorno(tela, L(FUS), PRETO)
        pol(tela, L(FUS), CASCO2)
        pol(tela, L([(52, -3.0), (44, -5.4), (30, -6.0), (-38, -6.0), (-43, -5.4), (-47, -4.2), (-50, -2.4),
                     (-51.2, -.6), (40, -.6)]), CASCO)
        pol(tela, L([(-51, 1.8), (-48, 3.6), (-42, 4.8), (-30, 5.2), (14, 5.2), (24, 4.6), (36, 2.6), (30, 2.6),
                     (-40, 3.0)]), CASCO3)
        tela.linha(*P(-40, -5.2), *P(30, -5.2), BRANCO)
        # janelas e cabine
        for i in range(24):
            x = -36 + i * 2.6
            a = P(x, -2.6)
            tela.ret(int(a[0]), int(a[1]), max(1, int(s * .9)), max(1, int(s * .9)), FUNDO3)
        cab = L([(-48.6, -2.4), (-46.5, -3.9), (-44, -3.9), (-44.5, -2.2)])
        pol(tela, cab, FUNDO3)
        # porta
        a, b = P(-41, -4.0), P(-39, 2.2)
        tela.ret(int(a[0]), int(a[1]), 1, max(1, int(b[1] - a[1])), CASCO3)
        # estabilizador deste lado
        contorno(tela, L(ESTAB), PRETO)
        pol(tela, L(ESTAB), CASCO, CASCO2)
        # trem de pouso
        if trem > 0:
            for x, h in ((-38, 6.8), (6, 7.4)):
                a, b = P(x, 4.6), P(x, 4.6 + 3.4 * trem)
                tela.linha(*a, *b, ACO1)
                tela.disco(*P(x, 4.6 + 3.6 * trem), max(1.2, 1.4 * s), PRETO)
        # asa deste lado
        contorno(tela, L(ASA), PRETO)
        pol(tela, L(ASA), CASCO2, CASCO)
        # motor sob a asa (turbofan fechado, entrada à esquerda)
        mx, my = -4.0, 8.2
        nac = L([(mx - 7, my - 2.6), (mx + 6, my - 2.4), (mx + 9, my - 1.0), (mx + 9, my + 1.0), (mx + 6, my + 2.3),
                 (mx - 7, my + 2.6)])
        contorno(tela, nac, PRETO)
        pol(tela, nac, CASCO2)
        pol(tela, L([(mx - 7, my - 2.6), (mx + 6, my - 2.4), (mx + 9, my - 1.0), (mx - 7, my - .6)]), CASCO)
        pol(tela, L([(mx - 7.4, my - 2.3), (mx - 6.4, my - 2.3), (mx - 6.4, my + 2.3), (mx - 7.4, my + 2.3)]), FUNDO2)
        n = 6
        for j in range(n):
            th = t * 6 * giro + 2 * math.pi * j / n
            if math.sin(th) > 0:
                a = P(mx - 6.9, my + math.cos(th) * 2.1)
                tela.px(int(a[0]), int(a[1]), ACO4)
        pil = L([(mx - 2, my - 2.4), (mx + 4, my - 2.4), (mx + 7, my - 5.6), (mx + 1, my - 5.6)])
        pol(tela, pil, CASCO2)
        if empuxo > 0:
            for i in range(14):
                u = (hsh(i, 9) + t * 2.5) % 1.0
                x = mx + 9 + u * 24 * empuxo
                y = my + (hsh(i, 10) - .5) * (2 + u * 4)
                a = P(x, y)
                tela.px(int(a[0]), int(a[1]), GAS2 if u > .4 else (ACO2 if i % 2 else CIANO))
        return P


def ceu_dia(tela, t, y1=PALCO_H, desloc=0.0, nuvens=True):
    """Céu de dia com nuvens que correm (o avião anda para a esquerda)."""
    gradiente(tela, 0, 0, W, y1, [(0, CEU4), (.35, CEU3), (.7, CEU2), (1, CEU1)])
    if not nuvens: return
    for i in range(9):
        base = hsh(i, 21) * (W + 160)
        x = (base + desloc * (.4 + .6 * hsh(i, 22))) % (W + 160) - 80
        y = 20 + hsh(i, 23) * (y1 - 60)
        e = .6 + hsh(i, 24) * .9
        for j in range(5):
            dx = (j - 2) * 9 * e
            r = (7 - abs(j - 2) * 2) * e + 2
            tela.disco(x + dx, y + 1.5, r + .5, CEU1)
        for j in range(5):
            dx = (j - 2) * 9 * e
            r = (7 - abs(j - 2) * 2) * e + 2
            tela.disco(x + dx, y, r, CEU0)
            tela.disco(x + dx - 1.5, y - 1.5, r * .6, BRANCO)


# =================================================================== a pá da turbina em corte
PERFIL = [(-30, 6), (-26, 1), (-18, -3.5), (-6, -6.5), (8, -7), (20, -5), (30, -2.5), (38, 0), (30, .6), (18, .6),
          (6, 1.6), (-6, 4.2), (-18, 6.6), (-26, 7.8)]


def pa_corte(tela, cx, cy, s, t, frio=1.0, furos=1.0, camada=1.0, gas=1.0, perigo=False):
    """A pá de turbina vista em corte (perfil de asa), com o gás quente passando,
    os canais de ar frio por dentro e o filme de ar saindo pelos furos."""
    def P(x, y): return (cx + x * s, cy + y * s)

    def L(pts): return [P(x, y) for x, y in pts]
    # gás quente passando em volta (da esquerda para a direita)
    if gas > 0:
        # o gás quente em faixas que contornam a pá (desvia por cima e por baixo)
        x0, x1 = int(cx - 72 * s), int(cx + 82 * s)
        dither(tela, x0, int(cy - 30 * s), x1 - x0, int(60 * s), FUNDO, BRASA if gas > .5 else FUNDO2)
        for i in range(260):
            u = (hsh(i, 31) + t * .55) % 1.0
            x = -72 + u * 154
            y0 = (hsh(i, 32) - .5) * 58
            desvio = math.exp(-((x - 4) / 34) ** 2) * 9 * max(0.0, 1 - abs(y0) / 29)
            y = y0 + (desvio if y0 > 0 else -desvio)
            if abs(y) < 9.5 and -33 < x < 40: continue
            a = P(x, y)
            c = cor_calor(1550 - u * 200 - abs(y0) * 6, hsh(i, 33))
            tela.ret(int(a[0]), int(a[1]), max(2, int(s * 2.4)), 1, c)
    # camada isolante (cerâmica) por fora
    if camada > 0:
        maior = [(x * 1.06, y * 1.25 + (.4 if y > 0 else -.4)) for x, y in PERFIL]
        contorno(tela, L(maior), PRETO)
        pol(tela, L(maior), CERAMICA, ACO4 if camada < 1 else None)
    contorno(tela, L(PERFIL), PRETO)
    pol(tela, L(PERFIL), ACO2, ACO3)
    pol(tela, L([(x, y) for x, y in PERFIL if y < 0] + [(30, -.6), (-26, -.6)]), ACO3, ACO4)
    if perigo:
        # sem proteção: o metal fica em brasa e pisca (derreteria)
        quente = .5 + .5 * math.sin(t * 6)
        pol(tela, L(PERFIL), VERMELHO if quente > .5 else BRASA, LARANJA)
        brilho(tela, cx, cy, 34 * s * .5, VERMELHO)
        return
    # canais por dentro
    canais = [(-20, -14), (-10, -4), (0, 6), (10, 16), (20, 25)]
    for a, b in canais:
        ys = [y for x, y in PERFIL]
        top = np.interp((a + b) / 2, [x for x, y in PERFIL[:8]], [y for x, y in PERFIL[:8]]) + 1.2
        bot = np.interp((a + b) / 2, [x for x, y in PERFIL[8:]][::-1], [y for x, y in PERFIL[8:]][::-1]) - 1.2
        if bot - top < 1: continue
        pol(tela, L([(a, top), (b, top), (b, bot), (a, bot)]), FUNDO2)
        if frio > 0:
            for j in range(4):
                u = (j / 4 + t * 1.2 + a * .03) % 1.0
                yy = bot - u * (bot - top)
                p0 = P(a + 1, yy)
                tela.ret(int(p0[0]), int(p0[1]), max(1, int((b - a - 2) * s)), max(1, int(s * .6)),
                         FRIO1 if j % 2 else FRIO0)
    # furos e o filme de ar frio saindo e colando na pá
    if furos > 0:
        for i, (xh, lado) in enumerate(((-26, -1), (-14, -1), (-2, -1), (10, -1), (-18, 1), (2, 1))):
            yh = np.interp(xh, [x for x, y in PERFIL[:8]], [y for x, y in PERFIL[:8]]) if lado < 0 else \
                np.interp(xh, [x for x, y in PERFIL[8:]][::-1], [y for x, y in PERFIL[8:]][::-1])
            a = P(xh, yh)
            tela.disco(a[0], a[1], max(1, .9 * s), PRETO)
            for j in range(7):
                u = (j / 7 + t * 1.5 + i * .13) % 1.0
                x = xh + u * 16 * furos
                ys = (np.interp(x, [x_ for x_, y in PERFIL[:8]], [y for x_, y in PERFIL[:8]]) - 1.4) if lado < 0 else \
                    (np.interp(x, [x_ for x_, y in PERFIL[8:]][::-1], [y for x_, y in PERFIL[8:]][::-1]) + 1.4)
                p = P(x, ys)
                tela.ret(int(p[0]), int(p[1]), max(1, int(s * 1.4)), max(1, int(s * .5)), FRIO1 if u < .5 else FRIO0)
