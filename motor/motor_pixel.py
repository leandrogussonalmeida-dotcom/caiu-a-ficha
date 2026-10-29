#!/usr/bin/env python3
"""O cilindro de um motor de 4 tempos, em corte, desenhado por geometria.

Uma única variável manda em tudo: o ângulo do ciclo `teta` (0 a 720 graus,
0 = ponto morto superior no começo da admissão).

  pistão     posição pela fórmula da biela: y = r cos(a) + raiz(l² - r² sen²(a))
  comandos   giram a teta/2 (metade do virabrequim, fonte F2)
  válvulas   a abertura é LIDA do perfil do came no ponto que toca a haste,
             então came e válvula nunca discordam
  faísca     a 340 graus (20 graus antes do PMS, fonte F4)
  gases      partículas em coordenadas normalizadas da câmara: quando o pistão
             sobe, elas se apertam sozinhas (a compressão aparece de graça)

Tempos (simplificados de propósito, ver a descrição do vídeo):
  0-180 admissão (admissão aberta) | 180-360 compressão (fechadas)
  360-540 potência (fechadas)      | 540-720 escape (escape aberta)

`Cilindro(ox, oy, s)` desenha com origem no centro do virabrequim e escala s
(1 = close-up, .5 = um dos quatro do bloco).
"""
import math
import numpy as np
from longo import (dither, poligono, linha_grossa, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2,
                   ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1,
                   CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, PRETO)

R_MANIVELA, BIELA = 22.0, 62.0
FAISCA = 340.0
TEMPOS = [('INTAKE', 0, 180, MISTURA), ('COMPRESSION', 180, 360, 29), ('POWER', 360, 540, LARANJA),
          ('EXHAUST', 540, 720, 28)]


def tempo_de(teta):
    t = teta % 720
    for k, (nome, a, b, cor) in enumerate(TEMPOS):
        if a <= t < b: return k, nome, cor
    return 3, 'EXHAUST', 28


def y_pino(teta):
    """Altura do pino do pistão acima do centro do virabrequim (positivo = acima)."""
    a = math.radians(teta)
    return R_MANIVELA * math.cos(a) + math.sqrt(BIELA ** 2 - (R_MANIVELA * math.sin(a)) ** 2)


Y_PMS = y_pino(0)              # 84
Y_PMI = y_pino(180)            # 40
TOPO_CAMARA = -(Y_PMS + 12 + 5)   # cabeçote: 5 px acima do pistão no PMS -> taxa ~10:1


def lobo(delta_graus):
    """Perfil do came: raio extra (0..6) para um desvio angular do nariz."""
    c = math.cos(math.radians(delta_graus))
    lim = math.cos(math.radians(45))
    return 6.0 * max(0.0, (c - lim) / (1 - lim)) ** 1.5


# ângulo do nariz do came em função de teta (tela: 90 = para baixo, na haste)
def nariz(teta, valvula):
    base = 45.0 if valvula == 'adm' else 135.0
    return base + teta / 2.0          # mesmo sentido do virabrequim (horário na tela)


def abertura(teta, valvula):
    """Abertura da válvula (0..6 px) lida do came no ponto de contato (para baixo)."""
    return lobo(90.0 - nariz(teta, valvula))


class Particulas:
    """Gases da câmara: 90 partículas com casa normalizada (u, v) e o instante
    em que entram (admissão) e saem (escape)."""

    def __init__(self, n=90, seed=1):
        rng = np.random.default_rng(seed)
        self.u = rng.uniform(.03, .97, n)
        self.v = rng.uniform(.03, .97, n)
        self.entra = np.sort(rng.uniform(.02, .92, n))
        self.sai = rng.uniform(.05, .95, n)
        self.gota = rng.random(n) < .18          # gotinhas de combustível na mistura
        self.fase = rng.uniform(0, 6.28, n)
        self.n = n


class Cilindro:
    def __init__(self, ox, oy, s=1.0, seed=1):
        self.ox, self.oy, self.s = ox, oy, s
        self.P = Particulas(seed=seed)
        self.pecas = None                 # None = todas; ou conjunto de nomes visíveis
        self.gases = True                 # False = câmara vazia (montagem peça a peça)

    # ------------------------------------------------------ transformação
    def X(self, x): return self.ox + x * self.s
    def Y(self, y): return self.oy + y * self.s

    def r(self, tela, x, y, w, h, cor):
        s = self.s
        x0, y0 = math.floor(self.ox + x * s), math.floor(self.oy + y * s)
        x1, y1 = math.ceil(self.ox + (x + w) * s), math.ceil(self.oy + (y + h) * s)
        if x1 - x0 < 1: x1 = x0 + 1
        if y1 - y0 < 1: y1 = y0 + 1
        tela.ret(x0, y0, x1 - x0, y1 - y0, cor)

    def d(self, tela, x, y, w, h, c1, c2):
        s = self.s
        x0, y0 = math.floor(self.ox + x * s), math.floor(self.oy + y * s)
        x1, y1 = math.ceil(self.ox + (x + w) * s), math.ceil(self.oy + (y + h) * s)
        dither(tela, x0, y0, x1 - x0, y1 - y0, c1, c2)

    def disco(self, tela, x, y, rr, cor):
        tela.disco(self.X(x), self.Y(y), max(.6, rr * self.s), cor)

    def ve(self, nome):
        return self.pecas is None or nome in self.pecas

    # ------------------------------------------------------ desenho
    def desenhar(self, tela, teta, t=0.0, quente=1.0, borrao=0, deslocar=None, volante=0.0):
        """Desenha o cilindro no ângulo `teta`. `borrao` > 0 desenha o pistão,
        a biela e a manivela em várias posições (rotação rápida demais para o
        olho). `deslocar` = {peça: (dx, dy)} para a montagem peça a peça."""
        dz = deslocar or {}
        self._bloco(tela, t, dz.get('cylinder', (0, 0)))
        if volante > 0 and self.ve('crankshaft'): self._volante(tela, teta, volante)
        if self.ve('crankshaft') or self.ve('rod') or self.ve('piston'):
            if borrao:
                for k in range(borrao):
                    self._movel(tela, teta + k * 720.0 / borrao, dz, fantasma=True)
            else:
                self._movel(tela, teta, dz)
        if self.ve('cylinder'): self._camara(tela, teta, t, quente, borrao)
        if self.ve('piston') and not borrao: self._pistao(tela, teta, dz.get('piston', (0, 0)))
        self._cabecote(tela, teta, t, dz)

    def _bloco(self, tela, t, d):
        if not self.ve('cylinder'):
            return
        dx, dy = d
        top = TOPO_CAMARA
        # cárter e corpo do bloco
        self.r(tela, -54 + dx, -32 + dy, 108, 64, ACO0)
        self.r(tela, -52 + dx, -30 + dy, 104, 60, FUNDO)
        self.d(tela, -52 + dx, -30 + dy, 104, 22, FUNDO2, FUNDO)
        self.r(tela, -54 + dx, -32 + dy, 108, 1, ACO2)
        self.r(tela, -54 + dx, -32 + dy, 1, 64, ACO2)
        # mancal do virabrequim preso ao bloco
        self.r(tela, -16 + dx, -3 + dy, 32, 6, ACO0)
        for x in (-14, 11):
            self.r(tela, x + dx, -2 + dy, 3, 3, ACO3)
        # óleo no fundo do cárter
        self.r(tela, -52 + dx, 22 + dy, 104, 9, OLEO0)
        self.r(tela, -52 + dx, 22 + dy, 104, 1, OLEO1)
        for k in range(0, 104, 9):
            o = int((math.sin(t * 2 + k) + 1) * 1.5)
            self.r(tela, -52 + k + o + dx, 22 + dy, 3, 1, LATAO)
        # paredes do cilindro com camisa d'água
        for lado in (-1, 1):
            x0 = -37 if lado < 0 else 29
            self.r(tela, x0 + dx, top + dy, 8, -30 - top, ACO1)
            self.r(tela, (x0 if lado < 0 else x0 + 7) + dx, top + dy, 1, -30 - top, ACO0)
            self.r(tela, (x0 + 7 if lado < 0 else x0) + dx, top + dy, 1, -30 - top, ACO3)
            # canal de água (corte): fluxo descendo
            self.r(tela, x0 + 2 + dx, top + 6 + dy, 4, -30 - top - 12, AGUA0)
            for k in range(0, int(-30 - top - 12), 6):
                yy = top + 6 + (k + t * 9) % (-30 - top - 12)
                self.r(tela, x0 + 3 + dx, yy + dy, 2, 2, AGUA1)
        # costelas externas do bloco
        for k in range(4):
            self.r(tela, -41 + dx, top + 8 + k * 14 + dy, 4, 6, ACO0)
            self.r(tela, 37 + dx, top + 8 + k * 14 + dy, 4, 6, ACO0)

    def _volante(self, tela, teta, raio):
        """Volante: disco pesado no virabrequim, com a cremalheira do arranque."""
        R = 34 * raio
        self.disco(tela, 0, 0, R, ACO0)
        self.disco(tela, 0, 0, R - 2, ACO1)
        self.disco(tela, 0, 0, R - 9, ACO0)
        for k in range(24):
            a = math.radians(teta + k * 15)
            self.r(tela, math.cos(a) * (R - 1) - .5, math.sin(a) * (R - 1) - .5, 2, 2, ACO3)
        for k in range(3):
            a = math.radians(teta + k * 120)
            self.disco(tela, math.cos(a) * R * .55, math.sin(a) * R * .55, 3, FUNDO2)

    def _movel(self, tela, teta, dz, fantasma=False):
        a = math.radians(teta)
        px_, py_ = R_MANIVELA * math.sin(a), -R_MANIVELA * math.cos(a)
        yp = -y_pino(teta)
        cr = dz.get('crankshaft', (0, 0)); rd = dz.get('rod', (0, 0))
        if self.ve('crankshaft'):
            c_peso = ACO0 if fantasma else ACO1
            # contrapeso oposto à manivela
            for rr, cor in ((17, ACO0), (15, c_peso)):
                pts = []
                for k in range(-70, 71, 10):
                    b = a + math.pi + math.radians(k)
                    pts.append((self.X(math.sin(b) * rr + cr[0]), self.Y(-math.cos(b) * rr + cr[1])))
                pts.append((self.X(cr[0]), self.Y(cr[1])))
                poligono(tela, pts, cor)
            linha_grossa(tela, self.X(cr[0]), self.Y(cr[1]), self.X(px_ + cr[0]), self.Y(py_ + cr[1]), 12 * self.s,
                         ACO0 if fantasma else ACO2)
            self.disco(tela, cr[0], cr[1], 8, LATAO)
            self.disco(tela, cr[0], cr[1], 5, ACO3)
        if self.ve('rod'):
            cor = ACO1 if fantasma else ACO3
            linha_grossa(tela, self.X(px_ + rd[0]), self.Y(py_ + rd[1]), self.X(rd[0]), self.Y(yp + rd[1]), 7 * self.s, cor)
            if not fantasma:
                linha_grossa(tela, self.X(px_ + rd[0] - 1), self.Y(py_ + rd[1]), self.X(rd[0] - 1), self.Y(yp + rd[1]),
                             2 * self.s, ACO4)
            self.disco(tela, px_ + rd[0], py_ + rd[1], 7, cor)
            self.disco(tela, px_ + rd[0], py_ + rd[1], 3.5, LATAO)
            self.disco(tela, rd[0], yp + rd[1], 4, cor)
        if fantasma and self.ve('piston'):
            topo = yp - 12
            self.r(tela, -28, topo, 56, 24, ACO0)
            self.r(tela, -28, topo, 56, 2, ACO2)

    def _pistao(self, tela, teta, d):
        dx, dy = d
        yp = -y_pino(teta)
        topo = yp - 12
        self.r(tela, -28 + dx, topo + dy, 56, 24, ACO2)
        self.d(tela, -27 + dx, topo + 3 + dy, 54, 19, ACO2, ACO1)
        self.r(tela, -28 + dx, topo + dy, 56, 2, ACO4)
        for k in range(3):                                  # anéis
            self.r(tela, -28 + dx, topo + 4 + k * 3 + dy, 56, 1, ACO0)
        self.r(tela, -28 + dx, topo + dy, 1, 24, ACO3)
        self.r(tela, 27 + dx, topo + dy, 1, 24, ACO0)
        self.disco(tela, dx, yp + dy, 3, ACO0)              # furo do pino

    def _camara(self, tela, teta, t, quente, borrao):
        top = TOPO_CAMARA
        topo_p = -y_pino(teta) - 12
        if borrao:
            # rápido demais: a câmara vira uma mancha quente que pisca
            yb = -Y_PMI - 12
            self.r(tela, -29, top, 58, yb - top, FUNDO2)
            pis = int(t * 60) % 3
            self.d(tela, -28, top + 1, 56, int((yb - top) * .55), CHAMA2 if pis else CHAMA1, BRASA)
            self.r(tela, -28, -Y_PMS - 12, 56, int(Y_PMS - Y_PMI), ACO1)
            self.d(tela, -28, -Y_PMS - 12, 56, int(Y_PMS - Y_PMI), ACO1, ACO0)
            return
        h = topo_p - top
        self.r(tela, -29, top, 58, h, FUNDO)
        if not self.gases: return
        T = teta % 720
        P = self.P
        # frente de chama a partir da vela
        if FAISCA <= T < 540:
            raio = min(1.0, (T - FAISCA) / 40.0) * 75
            calor = 1 - max(0.0, (T - 380) / 160.0)
            yy, xx = np.mgrid[0:max(1, int(h)), 0:58]
            dist = np.hypot(xx - 29, yy)
            m = dist <= raio
            cores = np.where(calor > .6, np.where((xx + yy) % 2 == 0, CHAMA1, LARANJA),
                             np.where(calor > .25, np.where((xx + yy) % 2 == 0, CHAMA2, BRASA), BRASA))
            borda = m & (dist > raio - 4) & (raio < 74)
            y0s, x0s = int(self.Y(top)), int(self.X(-29))
            if self.s == 1:
                sub = tela.buf[y0s:y0s + m.shape[0], x0s:x0s + 58]
                hh, ww = sub.shape
                sub[m[:hh, :ww]] = cores[:hh, :ww][m[:hh, :ww]]
                sub[borda[:hh, :ww]] = CHAMA0
            else:
                for (yy_, xx_) in zip(*np.nonzero(m[::2, ::2])):
                    tela.px(self.X(-29 + xx_ * 2), self.Y(top + yy_ * 2), int(cores[yy_ * 2, xx_ * 2]))
        # partículas
        if T < 180:
            presentes = P.entra < T / 180.0
            idade = (T / 180.0 - P.entra) / .12
        elif T < 540:
            presentes = np.ones(P.n, bool); idade = np.full(P.n, 9.0)
        else:
            presentes = P.sai > (T - 540) / 180.0
            idade = np.full(P.n, 9.0)
        saindo = (T >= 540) & ((P.sai - (T - 540) / 180.0) < .1) & presentes
        for i in np.nonzero(presentes)[0]:
            x = -27 + P.u[i] * 54 + math.sin(t * 3 + P.fase[i]) * 1.2
            y = top + 1 + P.v[i] * max(1.0, h - 2)
            if idade[i] < 1:                            # entrando pela válvula de admissão
                u = idade[i]
                x = -14 + (x + 14) * u
                y = top + (y - top) * u
            if saindo[i]:
                u = 1 - (P.sai[i] - (T - 540) / 180.0) / .1
                x = x + (14 - x) * u
                y = y + (top - y) * u
            if T < FAISCA:
                cor = MISTURA2 if (T > 250 and P.fase[i] > 3) else MISTURA
                if P.gota[i]: cor = AMARELO
            elif T < 540:
                cor = CHAMA0 if T < 400 else (CHAMA1 if T < 450 else BRASA)
            else:
                cor = GAS if P.fase[i] > 2 else GAS2
            self.r(tela, x, y, 1.6, 1.6, cor)
        # faísca
        if FAISCA - 2 <= T < FAISCA + 6 and self.ve('spark'):
            cx, cy = self.X(0), self.Y(top + 1)
            for k in range(6):
                a = k * 1.05 + t * 40
                tela.linha(cx, cy, cx + math.cos(a) * 5 * self.s * 1.6, cy + math.sin(a) * 4 * self.s * 1.6, CHAMA0)
            tela.disco(cx, cy, 2 * max(.7, self.s), BRANCO)

    def _cabecote(self, tela, teta, t, dz):
        top = TOPO_CAMARA
        T = teta % 720
        if self.ve('cylinder'):
            dx, dy = dz.get('cylinder', (0, 0))
            self.r(tela, -56 + dx, top - 27 + dy, 112, 27, ACO1)
            self.d(tela, -55 + dx, top - 26 + dy, 110, 25, ACO1, ACO2)
            self.r(tela, -56 + dx, top - 27 + dy, 112, 1, ACO3)
            self.r(tela, -56 + dx, top - 1 + dy, 112, 1, ACO0)
            # dutos: cada um desce em curva até o assento da SUA válvula
            for lado in (-1, 1):
                pts = [(56, top - 22), (30, top - 22), (18, top - 12), (6, top - 1),
                       (22, top - 1), (27, top - 7), (33, top - 12), (56, top - 12)]
                poligono(tela, [(self.X(lado * x + dx), self.Y(y + dy)) for x, y in pts], FUNDO)
                for (x0, y0), (x1, y1) in zip(pts[:3], pts[1:4]):            # parede de cima do duto
                    tela.linha(self.X(lado * x0 + dx), self.Y(y0 - 1 + dy), self.X(lado * x1 + dx), self.Y(y1 - 1 + dy), ACO3)
            # assentos das válvulas (anel mais claro onde a válvula fecha)
            for xv in (-14, 14):
                self.r(tela, xv - 9 + dx, top - 2 + dy, 2, 2, ACO4)
                self.r(tela, xv + 7 + dx, top - 2 + dy, 2, 2, ACO4)
            # fluxo nos dutos
            fluxo_adm = abertura(T, 'adm') > .3 and self.gases and self.ve('valves')
            fluxo_esc = abertura(T, 'esc') > .3 and self.gases and self.ve('valves')
            for k in range(7):
                if fluxo_adm:
                    u = (k / 7 + t * .8) % 1.0
                    self.r(tela, -56 + u * 36, top - 17 + math.sin(u * 6) * 2, 2, 2, AMARELO if k % 3 == 0 else MISTURA)
                if fluxo_esc:
                    u = (k / 7 + t * .9) % 1.0
                    self.r(tela, 20 + u * 36, top - 17 + math.sin(u * 5) * 2, 2, 2, GAS)
            # parafusos do cabeçote
            for x in (-50, -32, 30, 48):
                self.r(tela, x + dx, top - 25 + dy, 3, 3, ACO3)
                self.r(tela, x + 1 + dx, top - 24 + dy, 1, 1, ACO0)
        # tampa do comando (em corte): a caixa onde moram comandos e molas
        if self.ve('cams'):
            dx, dy = dz.get('cams', (0, 0))
            self.r(tela, -30 + dx, top - 60 + dy, 60, 33, ACO0)
            self.r(tela, -29 + dx, top - 59 + dy, 58, 31, FUNDO2)
            self.r(tela, -30 + dx, top - 60 + dy, 60, 1, ACO2)
            self.r(tela, -32 + dx, top - 28 + dy, 64, 2, ACO1)
        # válvulas
        for nome, xv, cor in (('adm', -14, MISTURA), ('esc', 14, 28)):
            if not self.ve('valves'): break
            dx, dy = dz.get('valves', (0, 0))
            L = abertura(T, nome)
            y_cab = top + L                                 # face da cabeça da válvula
            self.r(tela, xv - 1 + dx, top - 44 + L + dy, 2, 44, ACO3)          # haste
            self.r(tela, xv - 8 + dx, y_cab - 3 + dy, 16, 3, ACO3)            # cabeça
            self.r(tela, xv - 8 + dx, y_cab - 1 + dy, 16, 1, ACO4)
            # mola (zigue-zague), comprime quando abre
            n = 5
            alto = 12 - L
            for k in range(n):
                yy = top - 44 + L + 2 + k * alto / n
                self.r(tela, xv - 5 + (k % 2) * 3 + dx, yy + dy, 7, 1, LATAO)
            self.r(tela, xv - 6 + dx, top - 44 + L + dy, 12, 2, ACO2)           # prato da mola
            self.r(tela, xv - 6 + dx, top - 30 + dy, 12, 2, ACO0)
        # comandos de válvulas
        if self.ve('cams'):
            dx, dy = dz.get('cams', (0, 0))
            for nome, xv in (('adm', -14), ('esc', 14)):
                cx, cy = xv, top - 49
                ang = nariz(T, nome)
                pts = []
                for k in range(0, 360, 12):
                    rr = 5 + lobo(k - ang)
                    pts.append((self.X(cx + math.cos(math.radians(k)) * rr + dx), self.Y(cy + math.sin(math.radians(k)) * rr + dy)))
                poligono(tela, [(x + (1 if x > self.X(cx) else -1) * .0, y) for x, y in pts], ACO0)
                pts2 = [(self.X(cx + dx) + (x - self.X(cx + dx)) * .82, self.Y(cy + dy) + (y - self.Y(cy + dy)) * .82) for x, y in pts]
                poligono(tela, pts2, ACO2)
                self.disco(tela, cx + dx, cy + dy, 2.5, ACO3)
                self.disco(tela, cx + dx, cy + dy, 1.2, ACO0)
        # vela de ignição
        if self.ve('spark'):
            dx, dy = dz.get('spark', (0, 0))
            self.r(tela, -3 + dx, top - 46 + dy, 6, 18, CERAMICA)
            self.r(tela, -3 + dx, top - 46 + dy, 1, 18, BRANCO)
            for k in range(3):
                self.r(tela, -3 + dx, top - 44 + k * 4 + dy, 6, 1, ACO3)
            self.r(tela, -5 + dx, top - 28 + dy, 10, 5, ACO2)
            self.r(tela, -5 + dx, top - 28 + dy, 10, 1, ACO4)
            self.r(tela, -2 + dx, top - 23 + dy, 4, 22, ACO1)
            self.r(tela, -1 + dx, top - 2 + dy, 2, 2, ACO4)
            self.r(tela, -1 + dx, top - 50 + dy, 2, 4, VERMELHO)       # cabo


def mostrador(tela, cx, cy, R, teta, s=1):
    """O relógio do ciclo: anel em 4 cores (cada tempo = 1/4 do anel = 180
    graus de virabrequim) e o ponteiro em teta/720."""
    T = teta % 720
    yy, xx = np.mgrid[int(cy - R - 2):int(cy + R + 3), int(cx - R - 2):int(cx + R + 3)]
    d = np.hypot(xx - cx, yy - cy)
    ang = (np.degrees(np.arctan2(xx - cx, -(yy - cy))) + 360) % 360          # 0 = topo, horário
    anel = (d <= R) & (d >= R - 7)
    k_atual = tempo_de(T)[0]
    for k, (nome, a, b, cor) in enumerate(TEMPOS):
        m = anel & (ang >= a / 2) & (ang < b / 2)
        if k != k_atual:
            m = m & ((xx + yy) % 2 == 0)
        y0, x0 = int(cy - R - 2), int(cx - R - 2)
        sub = tela.buf[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
        sub[m[:sub.shape[0], :sub.shape[1]]] = cor
    tela.anel(cx, cy, R - 8, TRACO, .6)
    a = math.radians(T / 2)
    tela.linha(cx, cy, cx + math.sin(a) * (R - 3), cy - math.cos(a) * (R - 3), BRANCO)
    tela.disco(cx, cy, 2.5, BRANCO)
    # marca da faísca
    af = math.radians(FAISCA / 2)
    tela.disco(cx + math.sin(af) * (R + 4), cy - math.cos(af) * (R + 4), 1.6, AMARELO)
