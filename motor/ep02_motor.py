#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep02 — Como um avião de 400 toneladas voa (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (vento, motor, trem de pouso, alarme),
                          nos mesmos instantes do desenho

O ar do túnel de vento sai de `ep02_desenho.Fluxo` (escoamento calculado) e é
integrado no preparar() de cada capítulo: o desenho só lê o quadro guardado.

    python3 ep02_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep02_motor.py <saida.mp4> mito asa         # só esses capítulos (teste)
    python3 ep02_motor.py --folha <saida.png>          # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, AGUA0)
import ritmo_marca as RM
import ep02_desenho as D
from ep02_desenho import (pol, contorno, brilho, gradiente, seta_forca, barra, rotulo, Aviao, Ceu, Pista, Fluxo,
                          Turbofan, fundo_tunel, desenhar_perfil, aviao_topo)
from ep02_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2602, 45
GANHO_MUSICA = -10.0          # trilha baixa: o texto e o som do ar mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
AVIAO = Aviao()
KMH_DECOLA = 290              # F7: 747 pesado decola a ~290 km/h


def milhar(n):
    return f"{int(round(n)):,}".replace(',', '.')


def dec(x, c=1):
    return f"{x:.{c}f}".replace('.', ',')


def lerp(a, b, u): return a + (b - a) * u


def rampa(t, marcos):
    """Interpola suave entre marcos [(t, valor)]."""
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * suave((t - a) / max(1e-6, b - a))
    return marcos[-1][1]


def x_corte(cap):
    """Coluna do recorte vertical que usa este capítulo (para o HUD do Short)."""
    for c in CORTES:
        if c['de'][0] == cap or c['ate'][0] == cap: return c['x']
    return 60


def hud_vertical(tela, cap, linhas):
    """No corte vertical o painel da direita some: os números vão para o topo
    do recorte, em 1x, com contorno. linhas = [(texto, cor)]."""
    x = x_corte(cap) + 6
    for k, (txt, cor) in enumerate(linhas):
        tela.texto(txt, x, 12 + k * 11, cor, tam=9, contorno=PRETO)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    """Caixa escura atrás do painel nas cenas de céu (texto legível sobre sol e cidade)."""
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def titulo_painel(tela, txt, y=12, cor=BRANCO, tam=17):
    tela.texto(txt, PX0, y, cor, tam=tam, contorno=PRETO)


def pose_no_chao(xr, yc, ang, k, roda=(-12.5, 11.0)):
    """Origem do avião para a roda principal tocar o chão em (xr, yc)."""
    a = math.radians(ang)
    x, y = roda
    ox = xr - k * (x * math.cos(a) + y * math.sin(a))
    oy = yc - k * (-x * math.sin(a) + y * math.cos(a))
    return ox, oy


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

    def vento(self, fx, t0, t1, ganho=.12, lo=200, hi=1400):
        """Chiado de vento contínuo, em blocos de 6 s com emenda suave."""
        t = t0
        while t < t1 - .2:
            d = min(6.5, t1 - t)
            fx.put(fx.chiado(d, lo, hi, ataque=.8), self.t0 + t, ganho)
            t += 6.0

    def ronco(self, fx, t0, t1, ganho=.18):
        t = t0
        while t < t1 - .2:
            d = min(6.5, t1 - t)
            fx.put(fx.chiado(d, 40, 320, ataque=.6), self.t0 + t, ganho)
            fx.put(fx.chiado(d, 900, 2600, ataque=.6), self.t0 + t, ganho * .25)
            t += 6.0


# ============================================================ cenário de voo (reaproveitado)
class Voo(Cena):
    """Base das cenas com o avião no céu."""
    def preparar(self):
        self.ceu = Ceu(seed=3)
        self.pista = Pista(seed=5)

    def ar_ralo(self, tela, t, dens, vel=1.0, n=90, seed=0):
        """Pontinhos de ar passando: a quantidade mostra a densidade."""
        rng = np.random.default_rng(seed)
        xs = rng.uniform(0, 1, n); ys = rng.uniform(4, PALCO_H - 4, n); ws = rng.uniform(.7, 1.3, n)
        for i in range(int(n * dens)):
            x = (xs[i] * (W + 20) - t * 160 * vel * ws[i]) % (W + 20) - 10
            tela.ret(x, ys[i], 3, 1, ACO2)


# ============================================================ 0 gancho
class Gancho(Voo):
    T_ROT, T_SOLTA = 8.6, 9.8

    def vel(self, t):                       # km/h
        return KMH_DECOLA * min(1.0, (t / self.T_ROT) ** 1.25) if t < self.T_ROT else KMH_DECOLA + (t - self.T_ROT) * 6

    def xm(self, t):                        # quanto a pista andou (px): integra a velocidade
        ts = np.linspace(0, t, 120)
        return float(np.trapezoid([self.vel(u) for u in ts], ts)) / 3.6 * 2.2

    def desenhar(self, tela, t, tg):
        ang = rampa(t, [(self.T_ROT, 0), (self.T_ROT + 1.4, 10.0)])
        alt = 0.0 if t < self.T_SOLTA else 9.0 * (t - self.T_SOLTA) ** 1.6
        dy = alt * 1.0
        self.ceu.fundo(tela, alt * 10, t)
        xm = self.xm(t)
        self.pista.desenhar(tela, xm, dy, t)
        k = 2.0
        xr = 150
        ox, oy = pose_no_chao(xr, 176 + 0.0, ang, k)
        oy -= 0.0
        if alt > 0: oy -= min(alt * 1.0, 40) * 0 + 0
        trem = 1.0
        AVIAO.desenhar(tela, ox, oy - 0 if alt <= 0 else oy, k, ang, t, flaps=.5, trem=trem, luz_pouso=True)
        # painel
        if not VERTICAL:
            fundo_painel(tela, 4, 146 if t > self.T_SOLTA else 124)
            titulo_painel(tela, 'PESO MÁXIMO', 12, ACO3, 9)
            titulo_painel(tela, 'NA DECOLAGEM', 22, ACO3, 9)
            n = 396893 * ease(min(1, t / 2.5))
            titulo_painel(tela, f"{milhar(n)} KG", 34, AMARELO)
            titulo_painel(tela, '(747-400)', 54, ACO2, 9)
            titulo_painel(tela, 'VELOCIDADE', 78, ACO3, 9)
            titulo_painel(tela, f"{milhar(min(self.vel(t), 320))} KM/H", 90, BRANCO)
            barra(tela, PX0, 112, 150, 6, self.vel(t) / 320, CIANO)
            if t > self.T_SOLTA:
                titulo_painel(tela, 'NO AR!', 126, VERDE)

    def sons(self, fx):
        self.ronco(fx, 0, self.dur, .22)
        for k in range(int(self.T_SOLTA * 6)):                  # emendas da pista: tum-tum cada vez mais rápido
            t = (k / (self.T_SOLTA * 6)) ** .6 * self.T_SOLTA
            fx.put(fx.clique(900, .03), self.t0 + t, .12)


# ============================================================ 1 título
class Titulo(Voo):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        self.ceu.fundo(tela, 2500, t, sol_xy=(66, 40))
        self.ceu.camada(tela, 182, t * 40, esc=1.2, densa=True, seed=3)
        AVIAO.desenhar(tela, -60 + t * 50, 176 - t * 3, .9, 4, t, trem=0, motor=1)
        n = int(t / .04)
        for j, linha in enumerate(("COMO UM AVIÃO DE", "400 TONELADAS VOA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 16)]
            tela.texto(vis, W // 2 - larg // 2, 46 + j * 34, BRANCO if j == 0 else AMARELO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.3:
            sub = "SUSTENTAÇÃO, ESTOL E CRUZEIRO"
            tela.texto(sub, W // 2, 118, CIANO, tam=17, centro=True, contorno=PRETO)


# ============================================================ 2 as 4 forças
class Forcas(Voo):
    TT = dict(peso=5.2, sust=10.0, arr=14.8, tra=19.6, acel=24.4, eq=29.8)

    def tracao(self, t):
        return rampa(t, [(24.4, 40), (25.4, 62), (29.6, 62), (30.6, 40)])

    def velocidade(self, t):
        # acelera enquanto tração > arrasto
        if t < 24.6: return 850.0
        u = min(t, 30.2) - 24.6
        return 850.0 + u * 9.0

    def desenhar(self, tela, t, tg):
        self.ceu.fundo(tela, 5200, t, sol_xy=(262, 34))
        v = self.velocidade(t)
        desl = t * 60 + max(0, min(t, 30.2) - 24.6) ** 2 * 6
        self.ceu.camada(tela, 178, desl * 1.4, esc=1.1, densa=True, seed=1)
        cx, cy, k = 170, 104, 1.6
        bob = math.sin(t * 1.3) * 1.2
        AVIAO.desenhar(tela, cx, cy + bob, k, 0, t, trem=0)
        T = self.TT
        def ap(t0): return t >= t0
        def cres(t0): return ease((t - t0) / .5)
        if ap(T['peso']):
            L = 52 * cres(T['peso'])
            seta_forca(tela, cx, cy + 22 + bob, cx, cy + 22 + L + bob, VERMELHO)
            if L > 30: tela.texto('PESO', cx + 10, cy + 50 + bob, VERMELHO, tam=17, contorno=PRETO)
        if ap(T['sust']):
            L = 52 * cres(T['sust'])
            seta_forca(tela, cx - 4, cy - 14 + bob, cx - 4, cy - 14 - L + bob, CIANO)
            if L > 30: tela.texto('SUSTENTAÇÃO', cx - 12 - tela.largura_texto('SUSTENTAÇÃO', 17), cy - 60 + bob, CIANO, tam=17, contorno=PRETO)
        if ap(T['arr']):
            L = 40 * cres(T['arr'])
            seta_forca(tela, cx - 86, cy + 2 + bob, cx - 86 - L, cy + 2 + bob, LARANJA)
            if L > 30 and not VERTICAL: tela.texto('ARRASTO', cx - 150, cy + 12 + bob, LARANJA, tam=17, contorno=PRETO)
        if ap(T['tra']):
            L = self.tracao(t) * cres(T['tra'])
            seta_forca(tela, cx + 86, cy + 2 + bob, cx + 86 + L, cy + 2 + bob, AMARELO)
            if L > 30 and not VERTICAL: tela.texto('TRAÇÃO', cx + 52, cy + 14 + bob, AMARELO, tam=17, contorno=PRETO)
        if VERTICAL: return
        # painel: as 4 forças com barra, e o estado
        itens = [('PESO', 'peso', VERMELHO, 52), ('SUSTENTAÇÃO', 'sust', CIANO, 52), ('ARRASTO', 'arr', LARANJA, 40),
                 ('TRAÇÃO', 'tra', AMARELO, self.tracao(t))]
        fundo_painel(tela, 4, 196)
        titulo_painel(tela, '4 FORÇAS', 10)
        for j, (nome, ch, cor, val) in enumerate(itens):
            y = 34 + j * 24
            on = t >= T[ch]
            tela.texto(nome, PX0, y, cor if on else FUNDO3, tam=9, contorno=PRETO)
            barra(tela, PX0, y + 10, 120, 5, (val / 70) * cres(T[ch]) if on else 0, cor)
        y = 136
        tela.texto('VELOCIDADE', PX0, y, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{milhar(v)} KM/H", PX0, y + 11, BRANCO, tam=17, contorno=PRETO)
        if T['acel'] <= t < T['eq']:
            if int(t * 3) % 2 == 0: tela.texto('ACELERANDO', PX0, y + 34, AMARELO, tam=17, contorno=PRETO)
        elif t >= T['eq']:
            tela.texto('EQUILÍBRIO', PX0, y + 34, VERDE, tam=17, contorno=PRETO)

    def sons(self, fx):
        self.ronco(fx, 0, self.dur, .1)
        for k, ch in enumerate(('peso', 'sust', 'arr', 'tra')):
            fx.put(fx.blip(72 + k * 3, .12), self.t0 + self.TT[ch], .22)
        fx.put(fx.chiado(5.0, 60, 500, ataque=.4), self.t0 + 24.4, .2)
        fx.put(fx.sino(79, 1.2), self.t0 + self.TT['eq'], .25)


# ============================================================ túnel: base
class Tunel(Cena):
    CX, CY, ESC = 140, 112, 40
    U = 64.0

    def novo_fluxo(self, **kw):
        return Fluxo(self.CX, self.CY, self.ESC, regiao=(0, 8, 300, 200), U=kw.pop('U', self.U))

    def painel_corte(self, tela, t, y=150):
        """Ícone do avião visto de cima com o corte da asa marcado."""
        if VERTICAL: return
        aviao_topo(tela, PX0 + 26, y + 22, 1.1, corte=True, t=t)
        tela.texto('CORTE DA', PX0 + 56, y + 8, ACO3, tam=9, contorno=PRETO)
        tela.texto('ASA', PX0 + 56, y + 18, ACO3, tam=9, contorno=PRETO)

    def seta_sust(self, tela, F, a, d, comp, cor=CIANO, s=0.0):
        ex, ey = F.extradorso(d)
        x, y = F.ponto(-0.6, float(np.interp(-0.6, ex, ey)), a)
        if comp > 3: seta_forca(tela, x, y - 4, x, y - 4 - comp, cor)
        return x, y


# ============================================================ 3 o mito
class Mito(Tunel):
    PULSOS = [(16.4, 22, 62, 162, 2.0), (30.4, 22, 62, 162, 2.0)]

    def alfa(self, t): return rampa(t, [(27.8, 4.0), (29.2, 7.0)])
    def delta(self, t): return rampa(t, [(27.8, .1), (29.2, .0)])

    def preparar(self):
        self.F = self.novo_fluxo()
        self.F.simular(self.dur, alfa=self.alfa, delta=self.delta, pulsos=self.PULSOS, seed=3)
        info = self.F.chegada.get(1, {'lado': {}, 'chegou': {}})
        cima = sorted(o for o, l in info['lado'].items() if l == 'cima')
        baixo = sorted(o for o, l in info['lado'].items() if l == 'baixo')
        o_c = cima[-2] if len(cima) > 2 else (cima[-1] if cima else 0)
        o_b = baixo[2] if len(baixo) > 3 else (baixo[0] if baixo else 1)
        self.par = (o_c, o_b)
        self.tc = info['chegou'].get(o_c, 0.0)
        self.tb = info['chegou'].get(o_b, 0.0)

    def _caminhos(self, tela, a, d, u_pts, cor_c=AMARELO, cor_b=ROSA):
        z = D.perfil_w(d, 160)
        i_le = int(np.argmin(z.real))
        cima = z[:i_le + 1][::-1]                # do bordo de ataque ao de fuga
        baixo = z[i_le:]
        out = []
        for zz, cor, off in ((cima, cor_c, .16), (baixo, cor_b, -.16)):
            zo = zz + 1j * off
            xs, ys = self.F.para_tela(zo, a)
            for i in range(0, len(xs) - 1, 2):
                if (i // 2) % 2 == 0: tela.linha(xs[i], ys[i], xs[i + 1], ys[i + 1], cor)
            # comprimento acumulado (para andar com a mesma fração de tempo)
            seg = np.hypot(np.diff(xs), np.diff(ys)); acc = np.concatenate([[0], np.cumsum(seg)])
            out.append((xs, ys, acc))
        return out

    def desenhar(self, tela, t, tg):
        fundo_tunel(tela, t, x1=300)
        a, d = self.alfa(t), self.delta(t)
        F = self.F
        if t < 15.6:
            # ---- a explicação da escola, desenhada em câmera lenta
            cam = self._caminhos(tela, a, d, None)
            u = suave((t - 1.5) / 7.0)
            for (xs, ys, acc), cor in zip(cam, (AMARELO, ROSA)):
                s = u * acc[-1]
                x = float(np.interp(s, acc, xs)); y = float(np.interp(s, acc, ys))
                tela.disco(x, y, 3.5, PRETO); tela.disco(x, y, 2.6, cor); tela.px(x - 1, y - 1, BRANCO)
            desenhar_perfil(tela, F, a, d)
            tela.texto('CAMINHO MAIOR', 92, 64, AMARELO, tam=9, contorno=PRETO)
            tela.texto('CAMINHO MENOR', 104, 140, ROSA, tam=9, contorno=PRETO)
            if 8.6 < t:
                txt = 'JUNTOS?' if VERTICAL else 'CHEGAM JUNTOS?'
                tela.texto(txt, 140, 22 if VERTICAL else 168, BRANCO, tam=17, centro=True, contorno=PRETO)
            if t >= 11.2:
                u2 = ease((t - 11.2) / .25)
                for (x0, y0, x1, y1) in ((76, 70, 204, 150), (76, 150, 204, 70)):
                    xm, ym = x0 + (x1 - x0) * u2, y0 + (y1 - y0) * u2
                    linha_grossa(tela, x0, y0, xm, ym, 7, PRETO)
                    linha_grossa(tela, x0, y0, xm, ym, 5, VERMELHO)
                tr = int(3 * (1 - u2)) * (1 if int(t * 30) % 2 else -1)
                larg = tela.largura_texto('MITO', 26)
                painel(tela, 140 - larg // 2 - 10 + tr, 22, larg + 20, 34, borda=VERMELHO)
                tela.texto('MITO', 140 - larg // 2 + tr, 28, VERMELHO, tam=26, contorno=PRETO)
            if not VERTICAL:
                titulo_painel(tela, 'A EXPLICAÇÃO', 12, ACO3, 9)
                titulo_painel(tela, 'DA ESCOLA', 22, ACO3, 9)
                titulo_painel(tela, 'MESMO TEMPO?', 40, BRANCO)
                if t >= 11.2: titulo_painel(tela, 'ERRADO', 64, VERMELHO, 17)
                self.painel_corte(tela, t)
            return
        # ---- o ar de verdade
        F.desenhar(tela, t, cor='faixa', destaque=[(1, self.par[0], AMARELO), (1, self.par[1], ROSA)])
        desenhar_perfil(tela, F, a, d)
        # a corrida
        tp = self.PULSOS[0][0]
        corre = t - tp
        linhas = []
        for nome, tf, cor in (('CIMA', self.tc, AMARELO), ('BAIXO', self.tb, ROSA)):
            if corre < 0: s = '-'
            elif corre < tf: s = dec(corre, 2) + ' S'
            else: s = dec(tf, 2) + ' S'
            linhas.append((nome, s, cor, corre >= tf > 0))
        if not VERTICAL:
            titulo_painel(tela, 'A CORRIDA' if t < 27.8 else 'ASA SIMÉTRICA', 12, BRANCO)
            if t < 27.8:
                tela.texto('TEMPO ATÉ O FIM', PX0, 34, ACO3, tam=9, contorno=PRETO)
                tela.texto('DA ASA (LINHA BRANCA)', PX0, 44, ACO3, tam=9, contorno=PRETO)
                for j, (nome, s, cor, chegou) in enumerate(linhas):
                    y = 62 + j * 34
                    tela.disco(PX0 + 4, y + 7, 3, cor)
                    tela.texto(nome, PX0 + 12, y, cor, tam=17, contorno=PRETO)
                    tela.texto(s, PX0 + 84, y, BRANCO, tam=17, contorno=PRETO)
                    if chegou: tela.texto('CHEGOU', PX0 + 12, y + 18, VERDE, tam=9, contorno=PRETO)
            else:
                tela.texto('IGUAL EM CIMA', PX0, 36, ACO3, tam=9, contorno=PRETO)
                tela.texto('E EMBAIXO, MAS', PX0, 46, ACO3, tam=9, contorno=PRETO)
                tela.texto('INCLINADA:', PX0, 56, ACO3, tam=9, contorno=PRETO)
                tela.texto(f"ÂNGULO {int(round(a))}°", PX0, 72, AMARELO, tam=17, contorno=PRETO)
                tela.texto('SUSTENTA!', PX0, 96, CIANO, tam=17, contorno=PRETO)
            self.painel_corte(tela, t)
        else:
            if t < 27.8:
                hud_vertical(tela, 'mito', [(f"{n}: {s}", c) for n, s, c, _ in linhas])
        # marca no bordo de fuga
        xte, yte = F.ponto(2.0, 0, a)
        for k in range(0, 30, 3):
            tela.px(xte, yte - 15 + k, BRANCO)
        if t >= 27.8:
            self.seta_sust(tela, F, a, d, 34 * ease((t - 29.2) / .6))

    def sons(self, fx):
        self.vento(fx, 15.6, self.dur, .1)
        fx.put(fx.explosao(.8), self.t0 + 11.2, .45)
        for tp, *_ in self.PULSOS:
            fx.put(fx.blip(76, .1), self.t0 + tp, .25)
        tp = self.PULSOS[0][0]
        fx.put(fx.sino(84, .8), self.t0 + tp + self.tc, .35)
        fx.put(fx.sino(72, .8), self.t0 + tp + self.tb, .35)


# ============================================================ 4 a asa de verdade
class Asa(Tunel):
    ALFA = 5.0

    def preparar(self):
        self.F = self.novo_fluxo()
        self.F.simular(self.dur, alfa=lambda t: self.ALFA, delta=lambda t: .1, seed=4)
        self.cl = self.F.sustentacao(self.ALFA, .1)

    def etapa(self, t):
        if t < 10.8: return 1
        if t < 21.6: return 2
        if t < 32.2: return 3
        if t < 37.8: return 4
        return 5

    def desenhar(self, tela, t, tg):
        fundo_tunel(tela, t, x1=300)
        F, a = self.F, self.ALFA
        e = self.etapa(t)
        if t >= 21.6:
            F.pressao(tela, t, forca=ease((t - 21.6) / 1.5) * (1.0 if t < 32.2 or t >= 37.8 else .35))
        F.desenhar(tela, t, cor='vel' if 32.2 <= t < 37.8 else 'faixa')
        desenhar_perfil(tela, F, a, .1)
        # desvio para baixo atrás da asa
        if 10.8 <= t < 21.6:
            u = ease((t - 10.8) / .6)
            for j, yy in enumerate((96, 116, 136)):
                x0 = 232 + (j % 2) * 8
                ph = (t * 1.2 + j * .3) % 1.0
                seta_forca(tela, x0, yy, x0 + 26 * u, yy + 12 * u, AMARELO, esp=3, cab=6)
            if not VERTICAL or True:
                tela.texto('AR PARA BAIXO', 160 if VERTICAL else 196, 158, AMARELO, tam=9, contorno=PRETO)
        if 16.0 <= t < 21.6:
            self.seta_sust(tela, F, a, .1, 46 * ease((t - 16.0) / .5))
            x, y = F.ponto(-0.6, .45, a)
            tela.texto('ASA PARA CIMA', x - 40, y - 66, CIANO, tam=9, contorno=PRETO)
        if 21.6 <= t < 32.2:
            if t >= 21.6: tela.texto('PRESSÃO MENOR', 92, 50, MISTURA2, tam=9, contorno=PRETO)
            if t >= 27.0: tela.texto('PRESSÃO MAIOR', 92, 150, LARANJA, tam=9, contorno=PRETO)
        if t >= 37.8:
            # setinhas de pressão: em cima puxa, embaixo empurra; somadas = sustentação
            u = ease((t - 37.8) / .8)
            for xw in (-1.3, -.7, -.1, .5, 1.1):
                xt, yt = F.ponto(xw, .62 - abs(xw) * .18, a)
                seta_forca(tela, xt, yt - 4, xt, yt - 4 - 12 * u, MISTURA2, esp=3, cab=5)
                xb, yb = F.ponto(xw, -.28 - abs(xw) * .05, a)
                seta_forca(tela, xb, yb + 18 * u + 4, xb, yb + 4, LARANJA, esp=3, cab=5)
            if t >= 39.0:
                self.seta_sust(tela, F, a, .1, 50 * ease((t - 39.0) / .6))
                x, y = F.ponto(-0.6, .45, a)
                tela.texto('SUSTENTAÇÃO', x - 30, y - 70, CIANO, tam=17, contorno=PRETO)
        if VERTICAL: return
        # painel: etapa e legenda da cor
        nomes = {1: ('O AR SEGUE', 'A CURVA'), 2: ('SAI DESVIADO', 'PARA BAIXO'), 3: ('A PRESSÃO', 'MUDA'),
                 4: ('O AR DE CIMA', 'É MAIS RÁPIDO'), 5: ('A DIFERENÇA', 'SUSTENTA')}
        titulo_painel(tela, f"ETAPA {min(e, 4)} DE 4" if e < 5 else 'RESULTADO', 10, ACO3, 9)
        n1, n2 = nomes[e]
        titulo_painel(tela, n1, 22, BRANCO); titulo_painel(tela, n2, 40, AMARELO)
        y = 66
        if e == 3 or e == 5:
            for j, (txt, c1, c2) in enumerate((('MENOR', MISTURA, MISTURA2), ('IGUAL AO AR', FUNDO, FUNDO2),
                                               ('MAIOR', BRASA, LARANJA))):
                dither(tela, PX0, y + j * 16, 12, 12, c1, c2)
                tela.ret_vazado(PX0 - 1, y + j * 16 - 1, 14, 14, ACO1)
                tela.texto('PRESSÃO ' + txt if j != 1 else txt, PX0 + 18, y + j * 16 + 2, BRANCO, tam=9, contorno=PRETO)
        if e == 4:
            for j, (txt, c) in enumerate((('MAIS RÁPIDO', BRANCO), ('RÁPIDO', CIANO), ('NORMAL', ACO3), ('LENTO', ROXO))):
                tela.ret(PX0, y + j * 14 + 3, 12, 2, c)
                tela.texto(txt, PX0 + 18, y + j * 14, c, tam=9, contorno=PRETO)
        if e == 2:
            tela.texto('AÇÃO: ASA EMPURRA', PX0, y, AMARELO, tam=9, contorno=PRETO)
            tela.texto('O AR PARA BAIXO', PX0, y + 10, AMARELO, tam=9, contorno=PRETO)
            if t >= 16.0:
                tela.texto('REAÇÃO: AR EMPURRA', PX0, y + 28, CIANO, tam=9, contorno=PRETO)
                tela.texto('A ASA PARA CIMA', PX0, y + 38, CIANO, tam=9, contorno=PRETO)
        if e == 1:
            tela.texto(f"ÂNGULO: {int(a)}°", PX0, y, ACO3, tam=9, contorno=PRETO)
            tela.texto('VENTO: DA ESQUERDA', PX0, y + 12, ACO3, tam=9, contorno=PRETO)
        self.painel_corte(tela, t)

    def sons(self, fx):
        self.vento(fx, 0, self.dur, .12)
        for tt in (10.8, 16.0, 21.6, 32.2, 37.8):
            fx.put(fx.blip(74, .1), self.t0 + tt, .2)


# ============================================================ 5 velocidade
class Velocidade(Tunel):
    U = 46.0
    MARCOS = [(0, 1.0), (5.6, 1.0), (6.8, 2.0), (11.2, 2.0), (12.4, 3.0), (17.0, 3.0), (18.2, 1.6), (30, 1.6)]

    def vel(self, t): return rampa(t, self.MARCOS)

    def preparar(self):
        self.F = self.novo_fluxo()
        self.F.simular(self.dur, alfa=lambda t: 5.0, delta=lambda t: .1, vel=self.vel, seed=5, espaco=16)

    def desenhar(self, tela, t, tg):
        v = self.vel(t)
        fundo_tunel(tela, t, x1=300, vento=v)
        F = self.F
        F.desenhar(tela, t, cor='faixa', rastro=1.0)
        desenhar_perfil(tela, F, 5.0, .1)
        self.seta_sust(tela, F, 5.0, .1, 9 * v * v)
        if VERTICAL:
            hud_vertical(tela, 'velocidade', [(f"VENTO {dec(v, 1)}X", BRANCO), (f"SUSTENTAÇÃO {dec(v * v, 1)}X", CIANO)])
            return
        titulo_painel(tela, 'VENTO', 10, ACO3, 9)
        titulo_painel(tela, f"{milhar(v * 100)} KM/H", 22, BRANCO)
        barra(tela, PX0, 44, 150, 6, v / 3, BRANCO)
        titulo_painel(tela, 'SUSTENTAÇÃO', 60, ACO3, 9)
        titulo_painel(tela, f"{dec(v * v, 1)}X", 72, CIANO, 26)
        barra(tela, PX0, 102, 150, 6, v * v / 9, CIANO)
        for j, (vv, txt) in enumerate(((1, '1X  >  1X'), (2, '2X  >  4X'), (3, '3X  >  9X'))):
            ativo = abs(v - vv) < .05
            tela.texto(txt, PX0, 118 + j * 12, AMARELO if ativo else FUNDO3, tam=9, contorno=PRETO)
        if t >= 17.0:
            tela.texto('CRESCE COM:', PX0, 158, ACO3, tam=9, contorno=PRETO)
            tela.texto('VELOCIDADE, ÁREA,', PX0, 169, BRANCO, tam=9, contorno=PRETO)
            tela.texto('DENSIDADE, ÂNGULO', PX0, 180, BRANCO, tam=9, contorno=PRETO)
        else:
            tela.texto('VENTO  >  SUSTENTAÇÃO', PX0, 158, ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.vento(fx, 0, 5.8, .08)
        self.vento(fx, 5.6, 11.2, .14, 300, 2200)
        self.vento(fx, 11.2, 17.2, .2, 400, 3200)
        self.vento(fx, 17.0, self.dur, .11)
        for tt, m in ((6.2, 76), (11.8, 81)):
            fx.put(fx.blip(m, .15), self.t0 + tt, .25)


# ============================================================ 6 decolagem
class Decolagem(Voo):
    T_MOTOR, T_ROT, T_SOLTA = 11.2, 22.4, 24.2
    INSET = (PX0, 8, 166, 88)

    def preparar(self):
        super().preparar()
        x, y, w, h = self.INSET
        self.F = Fluxo(x + 84, y + 50, 20, regiao=(x + 1, y + 1, x + w - 1, y + h - 1), U=36)
        self.F.simular(self.dur, alfa=lambda t: 4.0, delta=self.delta, seed=6, faixa=5, espaco=10)
        ts = np.arange(0, self.dur + .05, .05)
        vs = np.array([self.vel(u) for u in ts])
        self._ts, self._xm = ts, np.concatenate([[0], np.cumsum(vs[:-1] * .05)]) / 3.6 * 1.7

    def flaps(self, t): return rampa(t, [(1.0, 0.0), (5.0, .55), (38.6, .55), (43.0, 0.0)])
    def delta(self, t): return .1 + .07 * self.flaps(t) / .55

    def vel(self, t):
        if t < self.T_MOTOR: return 0.0
        if t < self.T_ROT: return KMH_DECOLA * ((t - self.T_MOTOR) / (self.T_ROT - self.T_MOTOR)) ** 1.15
        return KMH_DECOLA + (t - self.T_ROT) * 4

    def alt(self, t):
        return 0.0 if t < self.T_SOLTA else 2.2 * (t - self.T_SOLTA) ** 1.7

    def desenhar(self, tela, t, tg):
        alt = self.alt(t)
        dy = alt
        self.ceu.fundo(tela, 600 + alt * 6, t)
        xm = float(np.interp(t, self._ts, self._xm))
        self.pista.desenhar(tela, xm, dy, t)
        ang = rampa(t, [(self.T_ROT, 0.0), (self.T_ROT + 1.5, 10.0), (36.0, 10.0), (40.0, 7.0)])
        k = 1.6
        trem = rampa(t, [(33.2, 1.0), (35.6, 0.0)])
        fl = self.flaps(t)
        ox, oy = pose_no_chao(146, 176, ang, k)
        oy -= min(alt, 1e9) * 0
        AVIAO.desenhar(tela, ox, oy, k, ang, t, flaps=fl, trem=trem, luz_pouso=True,
                       motor=.4 if t < self.T_MOTOR else 1.0)
        # rótulos na asa do avião
        if t < 11.0 and fl > .2 and not VERTICAL:
            a = math.radians(ang)
            P = lambda x, y: (ox + k * (x * math.cos(a) + y * math.sin(a)), oy + k * (-x * math.sin(a) + y * math.cos(a)))
            sx, sy = P(13.4, 4.2); fx_, fy = P(-6, 9.0)
            rotulo(tela, 'SLAT', 214, 128, sx, sy, AMARELO)
            rotulo(tela, 'FLAP', 64, 150, fx_, fy, AMARELO, direita=True)
        if VERTICAL:
            hud_vertical(tela, 'decolagem', [(f"{milhar(min(self.vel(t), 330))} KM/H", BRANCO),
                                             (f"NARIZ {int(round(ang))}°", AMARELO)])
            return
        # ---- zoom na asa: corte com slat e flap
        fundo_painel(tela, 4, 204)
        x, y, w, h = self.INSET
        tela.ret(x - 1, y - 1, w + 2, h + 2, ACO1)
        tela.ret(x, y, w, h, FUNDO)
        for gx in range(x, x + w, 12): tela.ret(gx, y, 1, h, FUNDO2)
        if t >= 5.6:
            self.F.desenhar(tela, t, cor='faixa', clip=(x + 1, y + 1, x + w - 1, y + h - 1))
        desenhar_perfil(tela, self.F, 4.0, .1, partes=(fl / .55, fl / .55))
        tela.texto('ZOOM NO CORTE DA ASA', x + 3, y + 2, ACO3, tam=9, contorno=PRETO)
        if fl > .15:
            sx, sy = self.F.ponto(-2.25, -.25, 4.0)
            tela.texto('SLAT', x + 4, y + h - 12, AMARELO, tam=9, contorno=PRETO)
            tela.linha(x + 14, y + h - 14, sx, sy + 2, AMARELO)
            fx2, fy2 = self.F.ponto(2.3, -.65, 4.0)
            tela.texto('FLAP', x + w - 30, y + h - 12, AMARELO, tam=9, contorno=PRETO)
            tela.linha(x + w - 20, y + h - 14, fx2, fy2, AMARELO)
        if 5.6 <= t < 22.0:
            tela.texto('MAIS CURVA', x + w - 64, y + 14, CIANO, tam=9, contorno=PRETO)
        # ---- etapas e velocidade
        etapas = [('FLAPS E SLATS', 0.0), ('ACELERAR', self.T_MOTOR), ('LEVANTAR O NARIZ', self.T_ROT),
                  ('SUBIR', self.T_SOLTA)]
        atual = max(j for j, (_, t0) in enumerate(etapas) if t >= t0)
        for j, (nome, t0) in enumerate(etapas):
            yy = 104 + j * 12
            cor = AMARELO if j == atual else (ACO3 if j < atual else FUNDO3)
            tela.texto(f"{j + 1} {nome}", PX0, yy, cor, tam=9, contorno=PRETO)
            if j < atual: tela.texto('OK', PX0 + 150, yy, VERDE, tam=9, contorno=PRETO)
        tela.texto('VELOCIDADE', PX0, 158, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{milhar(min(self.vel(t), 330))} KM/H", PX0, 169, BRANCO, tam=17, contorno=PRETO)
        if t >= self.T_ROT:
            tela.texto(f"NARIZ {int(round(ang))}°", PX0 + 100, 158, AMARELO, tam=9, contorno=PRETO)
        if 33.2 <= t < 38.4:
            tela.texto('TREM SUBINDO', PX0 + 70, 191, CIANO, tam=9, contorno=PRETO)
        if t >= 38.6:
            tela.texto('RECOLHENDO FLAPS', PX0 + 40, 191, CIANO, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(4.0, 300, 700, ataque=.3), self.t0 + 1.0, .12)          # motor dos flaps
        self.ronco(fx, 0, self.T_MOTOR, .08)
        self.ronco(fx, self.T_MOTOR, self.dur, .24)
        n = 40
        for kk in range(n):
            u = kk / n
            t = self.T_MOTOR + (self.T_SOLTA - self.T_MOTOR) * u ** .55
            fx.put(fx.clique(900, .03), self.t0 + t, .12)
        fx.put(fx.explosao(.6), self.t0 + 35.6, .3)                            # trem trava
        fx.put(fx.clique(700, .05), self.t0 + 35.6, .4)
        fx.put(fx.chiado(4.4, 300, 700, ataque=.3), self.t0 + 38.6, .1)


# ============================================================ 7 ângulo de ataque
class Angulo(Tunel):
    MARCOS = [(0, 0.0), (1.0, 0.0), (5.8, 4.0), (11.0, 8.0), (16.4, 12.0), (22.0, 13.5), (33, 14.0)]

    def alfa(self, t): return rampa(t, self.MARCOS)

    def preparar(self):
        self.F = self.novo_fluxo()
        self.F.simular(self.dur, alfa=self.alfa, delta=lambda t: .1, seed=7)
        self.cl0 = self.F.sustentacao(0, .1)

    def desenhar(self, tela, t, tg):
        fundo_tunel(tela, t, x1=300)
        a = self.alfa(t)
        F = self.F
        F.desenhar(tela, t, cor='faixa')
        desenhar_perfil(tela, F, a, .1)
        # o ângulo: corda da asa (amarelo) x direção do vento (branco), à frente da asa
        xl, yl = F.ponto(-2.03, 0, a)
        xt, yt = F.ponto(2.0, 0, a)
        ux, uy = (xl - xt), (yl - yt)
        n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
        for k in range(0, 56, 3):
            tela.px(xl + ux * k, yl + uy * k, AMARELO)
            tela.px(xl - k, yl, BRANCO)
        ang0 = math.atan2(-uy, ux)
        for j in range(0, 16):
            aa = math.pi - (math.pi - ang0) * j / 15
            tela.px(xl + math.cos(aa) * 40, yl - math.sin(aa) * 40, AMARELO)
        tela.texto(f"{int(round(a))}°", xl - 46, yl - 30, AMARELO, tam=17, contorno=PRETO)
        tela.texto('VENTO', xl - 58, yl + 5, BRANCO, tam=9, contorno=PRETO)
        cl = F.sustentacao(a, .1)
        self.seta_sust(tela, F, a, .1, 10 + 34 * (cl / self.cl0 - 1) * .5 + 10)
        if VERTICAL:
            hud_vertical(tela, 'angulo', [(f"ÂNGULO {int(round(a))}°", AMARELO)])
            return
        titulo_painel(tela, 'ÂNGULO DE', 10, ACO3, 9)
        titulo_painel(tela, 'ATAQUE', 20, ACO3, 9)
        titulo_painel(tela, f"{int(round(a))}°", 32, AMARELO, 26)
        grafico_cl(tela, PX0, 72, 160, 84, a, mostrar_queda=False)

    def sons(self, fx):
        self.vento(fx, 0, self.dur, .12)
        for tt in (5.8, 11.0, 16.4):
            fx.put(fx.clique(2000, .03), self.t0 + tt, .2)


def cl_modelo(a):
    """Curva de sustentação ilustrativa: reta até ~15° (F9), depois cai."""
    base = (a + 5.2) / 20.2
    if a <= 15: return base
    return (15 + 5.2) / 20.2 - (a - 15) * .09


def grafico_cl(tela, x, y, w, h, a, mostrar_queda=True):
    """Sustentação x ângulo, com o ponto atual."""
    tela.ret(x, y + h, w, 1, ACO2); tela.ret(x, y, 1, h, ACO2)
    tela.texto('SUSTENTAÇÃO', x + 3, y - 2, ACO3, tam=9, contorno=PRETO)
    tela.texto('ÂNGULO >', x + 3, y + h + 3, ACO3, tam=9, contorno=PRETO)
    X = lambda aa: x + (aa + 0) / 20 * (w - 6)
    Y = lambda c: y + h - c * (h - 12)
    amax = 20 if mostrar_queda else 15
    prev = None
    for k in range(0, int(amax * 4) + 1):
        aa = k / 4
        p = (X(aa), Y(cl_modelo(aa)))
        if prev: tela.linha(*prev, *p, CIANO if aa <= 15 else VERMELHO)
        prev = p
    # 15°
    xc = X(15)
    for k in range(0, h, 3): tela.px(xc, y + k, FUNDO3 if not mostrar_queda else VERMELHO)
    tela.texto('15°', xc - 8, y + h + 3, ACO3 if not mostrar_queda else VERMELHO, tam=9, contorno=PRETO)
    aa = min(a, amax)
    px, py = X(aa), Y(cl_modelo(aa))
    tela.disco(px, py, 3.5, PRETO); tela.disco(px, py, 2.5, AMARELO if aa <= 15 else VERMELHO)


# ============================================================ 8 estol
class Estol(Tunel):
    MARCOS = [(0, 14.0), (5.5, 18.0), (27.8, 18.0), (32.6, 6.0), (39, 6.0)]

    def alfa(self, t): return rampa(t, self.MARCOS)
    def s(self, t): return max(0.0, min(1.0, (self.alfa(t) - 15.0) / 2.5))

    def preparar(self):
        self.F = self.novo_fluxo()
        self.F.simular(self.dur, alfa=self.alfa, delta=lambda t: .1, estol=self.s, seed=8)
        self.cl0 = self.F.sustentacao(0, .1)

    def desenhar(self, tela, t, tg):
        fundo_tunel(tela, t, x1=300)
        a = self.alfa(t)
        F = self.F
        F.desenhar(tela, t, cor='faixa')
        desenhar_perfil(tela, F, a, .1)
        cl = cl_modelo(a)
        self.seta_sust(tela, F, a, .1, 62 * cl, cor=CIANO if a <= 15 else VERMELHO)
        x, y = F.ponto(.4, 1.3, a)
        if self.s(t) > .3 and t < 27.8:
            tela.texto('REDEMOINHO', min(x, 220), max(14, y - 24), LARANJA, tam=9, contorno=PRETO)
        alarme = 11.2 <= t < 30.0 and self.s(t) > .2
        if alarme and int(t * 4) % 2 == 0:
            larg = tela.largura_texto('ESTOL!', 26)
            xx = x_corte('estol') + 90 if VERTICAL else 140
            ye = 132 if VERTICAL else 160
            painel(tela, xx - larg // 2 - 8, ye, larg + 16, 32, borda=VERMELHO)
            tela.texto('ESTOL!', xx - larg // 2, ye + 5, VERMELHO, tam=26, contorno=PRETO)
        if VERTICAL:
            hud_vertical(tela, 'estol', [(f"ÂNGULO {int(round(a))}°", AMARELO if a <= 15 else VERMELHO)])
            return
        titulo_painel(tela, 'ÂNGULO', 10, ACO3, 9)
        titulo_painel(tela, f"{int(round(a))}°", 20, AMARELO if a <= 15 else VERMELHO, 26)
        grafico_cl(tela, PX0, 64, 160, 70, a, mostrar_queda=True)
        if 22.2 <= t < 28.0:
            manche(tela, PX0 + 40, 200, t, treme=True)
            tela.texto('MANCHE', PX0 + 80, 168, AMARELO, tam=9, contorno=PRETO)
            tela.texto('TREMENDO', PX0 + 80, 178, AMARELO, tam=9, contorno=PRETO)
        elif t >= 28.0:
            manche(tela, PX0 + 40, 200, t, treme=False, empurra=ease((t - 28.0) / 1.5))
            tela.texto('NARIZ', PX0 + 80, 168, VERDE, tam=9, contorno=PRETO)
            tela.texto('PARA BAIXO', PX0 + 80, 178, VERDE, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.vento(fx, 0, self.dur, .12)
        for k in range(int((30.0 - 11.2) * 2)):                         # alarme
            fx.put(fx.blip(88 if k % 2 == 0 else 84, .12), self.t0 + 11.2 + k * .5, .12)
        for k in range(int((28.0 - 22.2) * 18)):                         # manche tremendo
            fx.put(fx.clique(600, .02), self.t0 + 22.2 + k / 18, .12)
        for k in range(14):                                              # turbulência na asa
            fx.put(fx.explosao(.5), self.t0 + 5.8 + k * 1.5, .06)


def manche(tela, x, y, t, treme=False, empurra=0.0):
    """Manche (coluna de controle) de lado, genérico."""
    dx = (math.sin(t * 70) * 2.2) if treme else 0
    topo = (x + 8 * empurra + dx, y - 34)
    linha_grossa(tela, x, y, topo[0], topo[1], 4, ACO2)
    tela.ret(topo[0] - 14, topo[1] - 3, 28, 6, ACO3)
    tela.ret(topo[0] - 14, topo[1] - 3, 28, 1, ACO4)
    tela.ret(topo[0] - 16, topo[1] - 6, 4, 12, ACO1); tela.ret(topo[0] + 12, topo[1] - 6, 4, 12, ACO1)
    tela.ret(x - 10, y, 20, 4, ACO1)
    if treme:
        for k in range(3):
            tela.px(topo[0] - 22 - k * 2, topo[1] + (k - 1) * 4, AMARELO)
            tela.px(topo[0] + 22 + k * 2, topo[1] + (k - 1) * 4, AMARELO)
    if empurra > 0:
        seta_forca(tela, topo[0] - 6, topo[1] - 14, topo[0] + 10, topo[1] - 14, VERDE, esp=3, cab=5)


# ============================================================ 9 motores
class Motores(Cena):
    def preparar(self):
        self.M = Turbofan(146, 102, 1.0)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        M = self.M
        mostrar = ['fan']
        if t >= 5.6: mostrar.append('bypass')
        if t >= 11.0: mostrar.append('core')
        if t >= 16.4 or True: mostrar.append('jato')
        M.desenhar(tela, t, giro=1.0, mostrar=tuple(mostrar))
        P = M.P
        if not (VERTICAL and t >= 27.2):
            if 5.6 <= t:
                rotulo(tela, 'VENTILADOR', 40, 12, *P(-48, -30), AMARELO if t < 11 else ACO3)
            if 11.0 <= t and not VERTICAL:
                rotulo(tela, 'COMPRESSOR', 40, 190, *P(-10, 12), AMARELO if t < 16.4 else ACO3)
                rotulo(tela, 'QUEIMA', 130, 190, *P(36, 4), AMARELO if t < 16.4 else ACO3)
            if 16.4 <= t and not VERTICAL:
                rotulo(tela, 'TURBINAS', 196, 190, *P(64, 10), AMARELO if t < 21.8 else ACO3)
            if 21.8 <= t:
                rotulo(tela, 'AR QUE CONTORNA', 150, 12, *P(20, -34), CIANO)
        if VERTICAL:
            if t >= 27.2: hud_vertical(tela, 'motores', [('4 MOTORES JUNTOS:', AMARELO), ('29% DO PESO', AMARELO)])
            return
        titulo_painel(tela, 'TURBOFAN', 10, BRANCO)
        tela.texto('CORTE DE UM MOTOR', PX0, 30, ACO3, tam=9, contorno=PRETO)
        if t >= 27.2:
            u = ease((t - 27.2) / 1.2)
            aviao_topo(tela, PX0 + 140, 76, 1.0, t=t)
            tela.texto('PESO', PX0, 60, VERMELHO, tam=9, contorno=PRETO)
            barra(tela, PX0, 72, 110, 8, u, VERMELHO)
            tela.texto('3.894 KN', PX0, 84, BRANCO, tam=9, contorno=PRETO)
            tela.texto('4 MOTORES', PX0, 102, AMARELO, tam=9, contorno=PRETO)
            barra(tela, PX0, 114, 110, 8, .29 * u, AMARELO)
            tela.texto('4 X 282 = 1.128 KN', PX0, 126, BRANCO, tam=9, contorno=PRETO)
            tela.texto('29%', PX0 + 118, 110, AMARELO, tam=17, contorno=PRETO) if u > .9 else None
            tela.texto('MÁXIMOS DO 747-400', PX0, 144, ACO2, tam=9, contorno=PRETO)
        else:
            passos = [('1 ENTRA AR', 5.6), ('2 COMPRIME', 11.0), ('3 QUEIMA', 11.0), ('4 GIRA A TURBINA', 16.4),
                      ('5 AR CONTORNA', 21.8)]
            for j, (txt, t0) in enumerate(passos):
                tela.texto(txt, PX0, 52 + j * 14, AMARELO if t >= t0 else FUNDO3, tam=9, contorno=PRETO)
            if t >= 21.8:
                tela.texto('JATO FRIO', PX0, 138, CIANO, tam=9, contorno=PRETO)
                tela.texto('+ JATO QUENTE', PX0, 149, CHAMA1, tam=9, contorno=PRETO)
                tela.texto('= TRAÇÃO', PX0, 160, BRANCO, tam=17, contorno=PRETO)

    def sons(self, fx):
        self.ronco(fx, 0, self.dur, .2)
        for tt in (5.6, 11.0, 16.4, 21.8, 27.2):
            fx.put(fx.blip(76, .1), self.t0 + tt, .18)


# ============================================================ 10 subida / altitude
class Altitude(Voo):
    def alt(self, t): return rampa(t, [(0, 900.0), (43.0, 11000.0)])
    def ang(self, t): return rampa(t, [(0, 8.0), (41.5, 8.0), (44.0, 0.0)])

    @staticmethod
    def dens(h):  # densidade relativa da atmosfera padrão (troposfera, F14)
        return (1 - 2.25577e-5 * h) ** 4.2559

    @staticmethod
    def temp(h): return 15 - 6.5 * h / 1000

    def kmh(self, t): return rampa(t, [(0, 520.0), (40.0, 900.0)])

    def desenhar(self, tela, t, tg):
        h = self.alt(t)
        self.ceu.fundo(tela, h, t)
        d = self.dens(h)
        self.ar_ralo(tela, t, d, vel=1.2, n=110)
        # camadas de nuvem em alturas fixas: passam para baixo enquanto o avião sobe
        for (hc, esc, seed) in ((2200, 1.4, 1), (4500, 1.1, 4), (7000, 1.0, 7), (9200, 1.3, 2)):
            y = 120 + (h - hc) * .05
            if -30 < y < PALCO_H + 30:
                self.ceu.camada(tela, y, t * 90 * esc, esc=esc, densa=True, seed=seed)
        if h > 9600:
            self.ceu.mar_nuvens(tela, 120 + (h - 9200) * .05 + 4, t * 90 * 1.3)
        ang = self.ang(t)
        AVIAO.desenhar(tela, 150, 100, 1.4, ang, t, trem=0)
        if VERTICAL:
            hud_vertical(tela, 'altitude', [(f"ALTITUDE {milhar(round(h / 10) * 10)} M", BRANCO),
                                            (f"AR: {int(round(d * 100))}%", CIANO),
                                            (f"{milhar(self.temp(h))} °C" if self.temp(h) >= 0 else f"-{milhar(-self.temp(h))} °C", AMARELO)])
            return
        fundo_painel(tela)
        x = PX0
        tela.texto('ALTITUDE', x, 10, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{milhar(round(h / 10) * 10)} M", x, 21, BRANCO, tam=17, contorno=PRETO)
        # faixa de cruzeiro (F13) na régua
        rx, ry, rh = x + 150, 10, 150
        tela.ret(rx, ry, 4, rh, FUNDO2)
        y94 = ry + rh - 9400 / 12000 * rh; y116 = ry + rh - 11600 / 12000 * rh
        tela.ret(rx - 1, y116, 6, y94 - y116, VERDE)
        ya = ry + rh - h / 12000 * rh
        tela.ret(rx - 4, ya - 1, 12, 3, AMARELO)
        tela.texto('DENSIDADE DO AR', x, 46, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{int(round(d * 100))}%", x, 57, CIANO, tam=17, contorno=PRETO)
        barra(tela, x + 44, 60, 90, 6, d, CIANO)
        tc = self.temp(h)
        tela.texto('TEMPERATURA', x, 82, ACO3, tam=9, contorno=PRETO)
        st = f"{dec(tc, 1)} °C"
        tela.texto(st, x, 93, AMARELO if tc > 0 else CIANO, tam=17, contorno=PRETO)
        tela.texto('VELOCIDADE', x, 118, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{milhar(round(self.kmh(t) / 10) * 10)} KM/H", x, 129, BRANCO, tam=17, contorno=PRETO)
        if t >= 21.8:
            arr = d
            tela.texto('ARRASTO', x, 152, LARANJA, tam=9, contorno=PRETO)
            barra(tela, x + 54, 153, 80, 5, arr, LARANJA)
            tela.texto('(MESMA VELOCIDADE)', x, 163, ACO2, tam=9, contorno=PRETO)
        if t >= 38.0:
            tela.texto('MOTORES PERDEM FORÇA', x, 180, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.ronco(fx, 0, self.dur, .16)
        self.vento(fx, 0, self.dur, .06)


# ============================================================ 11 cruzeiro
class Cruzeiro(Voo):
    def desenhar(self, tela, t, tg):
        self.ceu.fundo(tela, 11000, t, sol_xy=(44, 30))
        self.ceu.mar_nuvens(tela, 168, t * 140)
        cx, cy, k = 160, 96, 1.6
        bob = math.sin(t * 1.1) * 1.0
        # ar desviado para baixo atrás da asa (o mesmo do túnel, em pontinhos)
        if t >= 22.2:
            rng = np.random.default_rng(9)
            for i in range(60):
                u = (rng.uniform() + t * .9) % 1.0
                y0 = cy - 30 + rng.uniform() * 70
                x = W + 10 - u * (W + 20)
                desvio = max(0.0, (cx + 10 - x) / 120.0) * 22 if abs(y0 - (cy + 12)) < 30 else 0
                tela.ret(x, y0 + desvio, 3, 1, CIANO if desvio > 2 else ACO2)
        AVIAO.desenhar(tela, cx, cy + bob, k, 0, t, trem=0)
        if 5.8 <= t:
            u = ease((t - 5.8) / .6)
            seta_forca(tela, cx, cy + 22 + bob, cx, cy + 22 + 46 * u + bob, VERMELHO)
            seta_forca(tela, cx - 4, cy - 14 + bob, cx - 4, cy - 14 - 46 * u + bob, CIANO)
            seta_forca(tela, cx - 86, cy + 2 + bob, cx - 86 - 32 * u, cy + 2 + bob, LARANJA)
            seta_forca(tela, cx + 86, cy + 2 + bob, cx + 86 + 32 * u, cy + 2 + bob, AMARELO)
        comb = 1.0 - max(0.0, t - 16.6) * .03
        if VERTICAL:
            hud_vertical(tela, 'cruzeiro', [('900 KM/H', BRANCO), ('11.000 M', CIANO)])
            return
        fundo_painel(tela)
        x = PX0
        tela.texto('ALTITUDE', x, 10, ACO3, tam=9, contorno=PRETO)
        tela.texto('11.000 M', x, 21, BRANCO, tam=17, contorno=PRETO)
        tela.texto('VELOCIDADE', x, 44, ACO3, tam=9, contorno=PRETO)
        tela.texto('~900 KM/H', x, 55, BRANCO, tam=17, contorno=PRETO)
        tela.texto('MACH 0,85', x, 75, AMARELO, tam=9, contorno=PRETO)
        tela.texto('LÁ FORA', x, 92, ACO3, tam=9, contorno=PRETO)
        tela.texto('-56 °C', x, 103, CIANO, tam=17, contorno=PRETO)
        if t >= 11.2:
            tela.texto('EQUILÍBRIO', x, 128, VERDE, tam=17, contorno=PRETO)
        if t >= 16.6:
            tela.texto('COMBUSTÍVEL', x, 152, ACO3, tam=9, contorno=PRETO)
            barra(tela, x, 164, 120, 6, .7 * comb, LATAO)
            tela.texto('PESO DIMINUINDO', x, 175, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.ronco(fx, 0, self.dur, .12)
        self.vento(fx, 0, self.dur, .05)


# ============================================================ 12 pouso
class Pouso(Voo):
    T_TOCA, T_NARIZ = 24.6, 27.0

    def alt(self, t): return max(0.0, rampa(t, [(0, 420.0), (20.0, 60.0), (self.T_TOCA, 0.0)]))
    def flaps(self, t): return rampa(t, [(5.8, .3), (9.0, 1.0)])
    def trem(self, t): return rampa(t, [(16.6, 0.0), (19.0, 1.0)])
    def ang(self, t): return rampa(t, [(0, 2.0), (21.0, 2.5), (self.T_TOCA - .3, 5.0), (self.T_NARIZ, 5.0), (self.T_NARIZ + 1.4, 0.0)])

    def kmh(self, t):
        if t < self.T_TOCA: return 260.0
        return max(40.0, 260.0 - (t - self.T_TOCA) * 28)

    def desenhar(self, tela, t, tg):
        h = self.alt(t)
        self.ceu.fundo(tela, h * 6, t)
        xm = t * 150 if t < self.T_TOCA else self.T_TOCA * 150 + sum(1 for _ in ()) + \
            (t - self.T_TOCA) * 150 - (t - self.T_TOCA) ** 2 * 10
        xm = max(xm, 0)
        dy = h * .9
        self.pista.desenhar(tela, xm, dy, t)
        ang = self.ang(t)
        k = 1.6
        ox, oy = pose_no_chao(150, 176, ang, k)
        AVIAO.desenhar(tela, ox, oy, k, ang, t, flaps=self.flaps(t), trem=self.trem(t), luz_pouso=True,
                       motor=.5)
        if self.T_TOCA <= t < self.T_TOCA + 1.2:                          # fumaça do pneu no toque
            u = (t - self.T_TOCA) / 1.2
            for j in range(8):
                tela.disco(150 - u * 40 - j * 4, 172 - u * 6 - (j % 3), 2 + u * 4, ACO3 if j % 2 else ACO2)
        if VERTICAL: return
        fundo_painel(tela, 4, 156)
        x = PX0
        tela.texto('ALTURA', x, 10, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{milhar(round(h / 5) * 5)} M", x, 21, BRANCO, tam=17, contorno=PRETO)
        fl = self.flaps(t)
        tela.texto('FLAPS', x, 46, ACO3, tam=9, contorno=PRETO)
        tela.texto('TOTAL' if fl > .95 else ('ABRINDO' if t >= 5.8 else 'PARCIAL'), x, 57,
                   AMARELO if fl > .95 else BRANCO, tam=17, contorno=PRETO)
        barra(tela, x, 78, 120, 5, fl, AMARELO)
        tr = self.trem(t)
        tela.texto('TREM DE POUSO', x, 92, ACO3, tam=9, contorno=PRETO)
        tela.texto('EMBAIXO' if tr > .95 else ('DESCENDO' if tr > 0 else 'RECOLHIDO'), x, 103,
                   VERDE if tr > .95 else BRANCO, tam=17, contorno=PRETO)
        if t >= self.T_TOCA:
            tela.texto('NO CHÃO', x, 132, VERDE, tam=17, contorno=PRETO)

    def sons(self, fx):
        self.ronco(fx, 0, self.T_TOCA, .12)
        fx.put(fx.chiado(3.2, 300, 700, ataque=.3), self.t0 + 5.8, .1)
        fx.put(fx.chiado(2.4, 200, 500, ataque=.2), self.t0 + 16.6, .12)
        fx.put(fx.clique(700, .05), self.t0 + 19.0, .4)
        fx.put(fx.chiado(1.2, 800, 4000, ataque=.01), self.t0 + self.T_TOCA, .3)   # pneu
        fx.put(fx.explosao(.7), self.t0 + self.T_TOCA, .35)
        fx.put(fx.explosao(.5), self.t0 + self.T_NARIZ + 1.4, .2)
        self.ronco(fx, self.T_TOCA + .5, self.T_TOCA + 6.5, .2)                    # reverso


# ============================================================ 13 resumo
class Resumo(Cena):
    CARTOES = [(0.4, '1', 'DESVIA O AR', 'PARA BAIXO'), (6.6, '2', 'VELOCIDADE', 'E ÂNGULO'),
               (13.2, '3', 'ÂNGULO DEMAIS', '= ESTOL'), (19.8, '4', 'MOTOR EMPURRA,', 'ASA SEGURA')]

    def preparar(self):
        self.F = Fluxo(64, 54, 11, regiao=(8, 26, 228, 98), U=30)
        self.F.simular(self.dur, alfa=lambda t: 6.0, delta=lambda t: .1, seed=13, faixa=5, espaco=8)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        caixas = [(8, 8), (244, 8), (8, 108), (244, 108)]
        for j, ((t0, num, l1, l2), (bx, by)) in enumerate(zip(self.CARTOES, caixas)):
            if t < t0: continue
            u = ease((t - t0) / .4)
            atual = j == max(i for i, c in enumerate(self.CARTOES) if t >= c[0])
            painel(tela, bx, by + int((1 - u) * 10), 228, 94, borda=AMARELO if atual else ACO1)
            tela.texto(num, bx + 8, by + 6, AMARELO, tam=26, contorno=PRETO)
            tela.texto(l1, bx + 30, by + 6, BRANCO, tam=17, contorno=PRETO)
            tela.texto(l2, bx + 30, by + 24, AMARELO if atual else ACO3, tam=17, contorno=PRETO)
            cx, cy = bx + 114, by + 66
            if j == 0:
                self.F.desenhar(tela, t, cor='faixa', clip=(bx + 2, by + 44, bx + 226, by + 92))
                desenhar_perfil(tela, self.F, 6.0, .1)
                seta_forca(tela, 180, 66, 196, 76, AMARELO, esp=3, cab=5)
            elif j == 1:
                a = 3 + 7 * (.5 + .5 * math.sin(t * 1.6))
                F = Fluxo(cx - 30, cy + 6, 9, regiao=(0, 0, 2, 2))
                desenhar_perfil(tela, F, a, .1)
                xx, yy = F.ponto(-.6, .5, a)
                seta_forca(tela, xx, yy - 4, xx, yy - 8 - a * 2.2, CIANO, esp=3, cab=5)
                tela.texto(f"{int(a)}°", cx + 22, cy - 6, AMARELO, tam=17, contorno=PRETO)
                for q in range(4):
                    x = bx + 160 + ((t * 80 + q * 18) % 60)
                    tela.ret(x, cy + 10 - q * 3, 6, 1, ACO3)
            elif j == 2:
                F = Fluxo(cx - 30, cy + 8, 9, regiao=(0, 0, 2, 2))
                desenhar_perfil(tela, F, 18, .1)
                for q in range(3):
                    vx, vy = cx - 6 + q * 22, cy - 12 + q * 3
                    for s in range(10):
                        aa = s * .7 + t * 5 + q
                        r = 2 + s * .5
                        tela.px(vx + math.cos(aa) * r, vy + math.sin(aa) * r, LARANJA)
                tela.texto('ESTOL', cx + 46, cy + 4, VERMELHO, tam=9, contorno=PRETO)
            else:
                AVIAO.desenhar(tela, cx - 10, cy + 6, .7, 0, t, trem=0)
                seta_forca(tela, cx - 10, cy - 4, cx - 10, cy - 24, CIANO, esp=3, cab=5)
                seta_forca(tela, cx + 28, cy + 6, cx + 44, cy + 6, AMARELO, esp=3, cab=5)
                tela.texto('ASA', cx - 2, cy - 26, CIANO, tam=9, contorno=PRETO)
                tela.texto('MOTOR', cx + 48, cy + 2, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k, (t0, *_r) in enumerate(self.CARTOES):
            fx.put(fx.blip(72 + k * 2, .14), self.t0 + t0, .28)


# ============================================================ 14 fim
class Fim(Voo):
    legenda = False
    brilho = 0.0

    def preparar(self):
        super().preparar()
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            self.ceu.fundo(tela, 3000, t)
            self.ceu.camada(tela, 190, t * 40, esc=1.2, densa=True, seed=3)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            u = (t - RM.OUTRO_S) / (self.dur - RM.OUTRO_S)
            AVIAO.desenhar(tela, -40 + u * 560, 150 - u * 50, 1.0, 5, t, trem=0)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, forcas=Forcas, mito=Mito, asa=Asa, velocidade=Velocidade,
             decolagem=Decolagem, angulo=Angulo, estol=Estol, motores=Motores, altitude=Altitude,
             cruzeiro=Cruzeiro, pouso=Pouso, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep02_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        for c in trilha.caps:
            ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
