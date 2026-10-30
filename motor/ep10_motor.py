#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep10 — Como o helicóptero voa (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (rotor, motor, vento, alarme), nos
                          mesmos instantes do desenho

O giro do rotor de cada cena é uma função voltas/s integrada no preparar()
(`Fase`): o desenho e o som leem a mesma fase, então cada "vup" do rotor soa
quando a pá passa. O ângulo de cada pá sai de `Cabeca.passo` (o prato).

    python3 ep10_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep10_motor.py <saida.mp4> prato ciclico       # só esses capítulos (teste)
    python3 ep10_motor.py --folha <saida.png>             # 2 quadros por capítulo
    python3 ep10_motor.py --folha <saida.png> ciclico 0.1 0.5 0.9   # quadros escolhidos
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, AGUA0, AGUA1)
import ritmo_marca as RM
from ep02_desenho import Ceu, Fluxo, desenhar_perfil
import ep10_desenho as D
from ep10_desenho import (pol, contorno, brilho, gradiente, seta_forca, barra, rotulo, caixa, arco_seta,
                          perfil_icone, Cabeca, Heli, HeliTopo, ArRotor, Campo, chao_topo, alavanca, manche,
                          pedais, rpm_barra)
from ep10_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2610, 45
GANHO_MUSICA = -10.0          # trilha baixa: o texto e o som do rotor mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
RPM100 = 510                  # F6: 100% = 510 RPM no helicóptero leve
VOLTAS_S = RPM100 / 60.0      # 8,5 voltas por segundo (F7)
KMH_PONTA = 736               # F7
RPM_CAUDA = 3264              # F7 (3.394 com 104% -> 3.264 com 100%)
HELI = Heli()
TOPO = HeliTopo()
CAB = Cabeca()
G = 2 * math.pi


def milhar(n):
    return f"{int(round(n)):,}".replace(',', '.')


def dec(x, c=1):
    return f"{x:.{c}f}".replace('.', ',')


def rampa(t, marcos):
    """Interpola suave entre marcos [(t, valor)]."""
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * suave((t - a) / max(1e-6, b - a))
    return marcos[-1][1]


def x_corte(cap):
    for c in CORTES:
        if c['de'][0] == cap or c['ate'][0] == cap: return c['x']
    return 60


def hud_vertical(tela, cap, linhas):
    """No corte vertical o painel some: os números vão para o topo do recorte."""
    x = x_corte(cap) + 6
    for k, (txt, cor) in enumerate(linhas):
        tela.texto(txt, x, 12 + k * 11, cor, tam=9, contorno=PRETO)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def tit(tela, txt, y, cor=BRANCO, tam=17, x=PX0):
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def direcao(c):
    fx, fy = c
    if abs(fx) < .15 and abs(fy) < .15: return 'CENTRO'
    if abs(fy) >= abs(fx): return 'FRENTE' if fy > 0 else 'TRÁS'
    return 'DIREITA' if fx > 0 else 'ESQUERDA'


def painel_voo(tela, col, cic=(0.0, 0.0), rpm=100.0, alt=0.0, dest=(), extra=(), y1=PALCO_H - 4):
    """O painel de sempre: coletivo, cíclico, giro do rotor e altitude."""
    fundo_painel(tela, 4, y1)
    x = PX0
    on = lambda k: AMARELO if k in dest else ACO3
    tit(tela, 'COLETIVO', 9, on('col'), 9)
    alavanca(tela, x + 2, 16, col, 'col' in dest)
    tit(tela, f"{int(round(col * 100))}%", 24, BRANCO, 17, x + 64)
    tit(tela, 'CÍCLICO', 56, on('cic'), 9)
    manche(tela, x, 70, cic[0], cic[1], 'cic' in dest)
    tit(tela, direcao(cic), 76, BRANCO, 17, x + 38)
    tit(tela, 'GIRO DO ROTOR', 104, on('rpm'), 9)
    cor = VERDE if 94.5 <= rpm <= 104.5 else (AMARELO if rpm > 80 else VERMELHO)
    tit(tela, f"{int(round(rpm))}%", 115, cor, 17)
    tit(tela, f"= {milhar(RPM100 * rpm / 100)} RPM", 120, ACO3, 9, x + 56)
    rpm_barra(tela, x, 136, 150, rpm)
    tit(tela, 'ALTURA', 150, on('alt'), 9)
    tit(tela, f"{milhar(alt)} M", 161, BRANCO, 17)
    for k, (txt, c) in enumerate(extra):
        tit(tela, txt, 182 + k * 11, c, 9)


def fundo_oficina(tela):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)


def etiqueta(tela, txt, x, y, cor, tam=17, borda=None):
    """Plaquinha (painel) com texto: CÂMERA LENTA, VELOCIDADE REAL..."""
    w = tela.largura_texto(txt, tam)
    hh = 14 if tam < 14 else 22
    painel(tela, x - 5, y - 4, w + 10, hh + 4, borda=borda or cor)
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


class Fase:
    """Fase do rotor (rad) integrada a partir de voltas/s = fn(t)."""

    def __init__(self, fn, dur, passo=.002):
        self.ts = np.arange(0, dur + .1, passo)
        self.v = np.array([fn(t) for t in self.ts])
        self.ph = np.concatenate([[0], np.cumsum(self.v[:-1] * passo)]) * G
        self.fn = fn

    def __call__(self, t): return float(np.interp(t, self.ts, self.ph))

    def passagens(self, t0, t1, pas=2):
        """Instantes em que uma pá passa pela frente (2 pás: a cada meia volta)."""
        k = np.floor(self.ph * pas / G)
        idx = np.nonzero(np.diff(k) > 0)[0]
        return [float(self.ts[i + 1]) for i in idx if t0 <= self.ts[i + 1] < t1]


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

    def vento(self, fx, t0, t1, ganho=.1, lo=200, hi=1400):
        t = t0
        while t < t1 - .2:
            d = min(6.5, t1 - t)
            fx.put(fx.chiado(d, lo, hi, ataque=.8), self.t0 + t, ganho)
            t += 6.0

    def turbina(self, fx, t0, t1, ganho=.1):
        """Motor: ronco grave + chiado agudo de turbina."""
        t = t0
        while t < t1 - .2:
            d = min(6.5, t1 - t)
            fx.put(fx.chiado(d, 40, 300, ataque=.6), self.t0 + t, ganho)
            fx.put(fx.chiado(d, 2400, 5200, ataque=.6), self.t0 + t, ganho * .18)
            t += 6.0

    def rotor_som(self, fx, fase, t0, t1, ganho=.2):
        """Cada passagem de pá: 'vup' (rápido) ou um sopro (câmera lenta)."""
        for t in fase.passagens(t0, t1):
            v = fase.fn(t)
            if v > 3.0:
                fx.put(fx.pulso(), self.t0 + t, ganho * .55)
            elif v > .05:
                fx.put(fx.chiado(min(.45, .25 / max(v, .3)), 180, 900, ataque=.08), self.t0 + t, ganho * .55)


# ============================================================ cenário de voo
class Voo(Cena):
    def preparar(self):
        self.ceu = Ceu(seed=3)
        self.campo = Campo(seed=5)
        self.ar = ArRotor(80, seed=4)

    def cenario(self, tela, t, alt_ceu=0.0, xm=0.0, gy=176, heliponto=150, vento=0.0, vento_x=None, sol_xy=None):
        self.ceu.fundo(tela, alt_ceu, t, sol_xy=sol_xy)
        hy = self.ceu.horizonte(alt_ceu)
        self.campo.desenhar(tela, hy, gy, xm, t, heliponto=heliponto, vento=vento, vento_x=vento_x)

    def heli(self, tela, ox, skid_y, k, t, ang=0.0, psi=0.0, giro=VOLTAS_S, disco=0.0, ar=1.0, sentido=1.0,
             chao=176, motor=True, sombra=True, mostrar_ar=True, cauda=VOLTAS_S * 6.4):
        """Helicóptero com o esqui em skid_y, mais a coluna de ar do rotor."""
        oy = skid_y - 17 * k
        hx, hy = HELI.P_(ox, oy, k, ang)(*HELI.HUB)
        if mostrar_ar and ar > 0:
            self.ar.desenhar(tela, hx, hy, HELI.R * k, t, sentido=sentido, forca=ar,
                             chao=chao if chao - skid_y < 70 else None, vel=1.2, alt=min(120, chao - hy + 8))
        HELI.desenhar(tela, ox, oy, k, ang, t, psi=psi, giro=giro, disco=disco, psi_c=t * 37.0, giro_c=cauda,
                      motor=motor, sombra_y=chao if sombra else None)
        return hx, hy, oy


# ============================================================ 0 gancho
class Gancho(Voo):
    def preparar(self):
        super().preparar()
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)

    def desenhar(self, tela, t, tg):
        bob = math.sin(t * 1.4) * 1.5
        sk = 136 + bob
        self.cenario(tela, t, vento=1.0, vento_x=140)
        self.heli(tela, 140, sk, 1.35, t, psi=self.fase(t), ar=.9)
        if VERTICAL: return
        painel_voo(tela, .55, (0.0, 0.0), 100, 3, dest=('rpm',) if 5.2 <= t < 9.8 else (),
                   extra=[('PARADO NO AR', VERDE)] if t < 5.2 else [])

    def sons(self, fx):
        self.turbina(fx, 0, self.dur, .1)
        self.rotor_som(fx, self.fase, 0, self.dur, .2)
        self.vento(fx, 0, self.dur, .06)


# ============================================================ 1 título
class Titulo(Voo):
    legenda = False

    def preparar(self):
        super().preparar()
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)

    def desenhar(self, tela, t, tg):
        self.ceu.fundo(tela, 2500, t, sol_xy=(400, 40))
        self.ceu.camada(tela, 182, t * 40, esc=1.2, densa=True, seed=3)
        x = -70 + t * 60
        HELI.desenhar(tela, x, 168 - t * 4, .8, -6, t, psi=self.fase(t), giro=VOLTAS_S, giro_c=40, psi_c=t * 30)
        n = int(t / .04)
        for j, linha in enumerate(("COMO O", "HELICÓPTERO VOA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 7)]
            tela.texto(vis, W // 2 - larg // 2, 40 + j * 34, BRANCO if j == 0 else AMARELO, tam=26, contorno=PRETO,
                       sombra=TRACO)
        if t > 1.3:
            tela.texto("ROTOR, COLETIVO, CÍCLICO E CAUDA", W // 2, 112, CIANO, tam=17, centro=True, contorno=PRETO)


# ============================================================ 2 a pá é uma asa
class Asa(Voo):
    CX, CY, S = 130, 104, 2.0
    T_LADO = 39.0
    INSET = (PX0, 8, 164, 92)

    def preparar(self):
        super().preparar()
        self.fase = Fase(lambda t: .16 if t < self.T_LADO else VOLTAS_S, self.dur)
        x, y, w, h = self.INSET
        self.F = Fluxo(x + 80, y + 50, 19, regiao=(x + 1, y + 1, x + w - 1, y + h - 1), U=36)
        self.F.simular(self.T_LADO + .5, alfa=lambda t: 6.0, delta=lambda t: .1, seed=6, faixa=5, espaco=10)

    def desenhar(self, tela, t, tg):
        if t >= self.T_LADO:
            return self.lado(tela, t)
        fundo_oficina(tela)
        cx, cy, s = self.CX, self.CY, self.S
        psi = self.fase(t)
        TOPO.corpo(tela, cx, cy, s, 0, t, sombra=False, fantasma=True, cauda=False)
        TOPO.rotor(tela, cx, cy, s, 0, psi)
        R = TOPO.R * s
        # sentido do giro
        if 5.8 <= t < 27.8 or t < 5.8:
            arco_seta(tela, cx, cy, R + 9, R + 9, 200, 250, CIANO, cab=6)
            if not VERTICAL or True:
                tela.texto('GIRA', cx - R - 8, cy + 30, CIANO, tam=9, contorno=PRETO)
        if t < 11.2 and not VERTICAL:
            # tamanho da pá (F6)
            xa, ya = TOPO.ponta(cx, cy, s, 0, psi, 3)
            xb, yb = TOPO.ponta(cx, cy, s, 0, psi)
            rotulo(tela, 'PÁ', cx + R - 4, 16, (xa + xb) / 2, (ya + yb) / 2, AMARELO, 17)
        if 11.2 <= t < 27.8:
            # o corte: um traço atravessando a pá amarela
            r = TOPO.R * .7
            u, v = -math.sin(psi), math.cos(psi)
            wu, wv = -v, u
            p0 = (cx + s * (r * u + wu * 4), cy - s * (r * v + wv * 4))
            p1 = (cx + s * (r * u - wu * 4), cy - s * (r * v - wv * 4))
            for q in range(0, 9, 2):
                tela.px(p0[0] + (p1[0] - p0[0]) * q / 8, p0[1] + (p1[1] - p0[1]) * q / 8, BRANCO)
            tela.disco(*p0, 1.5, BRANCO)
            if not VERTICAL:
                tela.linha(p0[0], p0[1], PX0 - 4, 54, ACO3)
        if 27.8 <= t:
            # velocidade ao longo da pá: maior na ponta
            u = ease((t - 27.8) / .8)
            for fr in (.3, .55, .8, 1.0):
                r = TOPO.R * fr
                du, dv = -math.sin(psi), math.cos(psi)
                wu, wv = -dv, du
                b = (cx + s * r * du, cy - s * r * dv)
                L = 40 * fr * u
                e = (b[0] + wu * L, b[1] - wv * L)
                seta_forca(tela, b[0], b[1], e[0], e[1], LARANJA if fr == 1.0 else AMARELO, esp=3, cab=5)
            if t >= 33.4:
                x, y = TOPO.ponta(cx, cy, s, 0, psi)
                etiqueta(tela, f"{KMH_PONTA} KM/H", min(x + 6, 230), max(8, min(y - 8, 186)), LARANJA, 9)
        if VERTICAL:
            if t >= 27.8: hud_vertical(tela, 'asa', [(f"PONTA: {KMH_PONTA} KM/H", LARANJA)])
            return
        # ---- painel
        etiqueta(tela, 'CÂMERA LENTA', 20, 10, CIANO, 9)
        if t < 11.2:
            fundo_painel(tela)
            tit(tela, 'A PÁ', 12)
            tit(tela, 'COMPRIDA E FINA', 34, ACO3, 9)
            tit(tela, 'ROTOR DE 2 PÁS', 50, ACO3, 9)
            tit(tela, '7,7 M DE PONTA', 66, BRANCO, 9)
            tit(tela, 'A PONTA', 77, BRANCO, 9)
            # ícone: pá esticada
            tela.ret(PX0, 100, 150, 6, ACO3); tela.ret(PX0, 100, 150, 1, ACO4); tela.ret(PX0 + 130, 100, 20, 6, AMARELO)
            tela.disco(PX0 + 2, 103, 4, ACO2)
            tit(tela, 'ANDA EM CÍRCULO', 120, CIANO, 9) if t >= 5.8 else None
            perfil_icone(tela, PX0 + 70, 160, 60, 6, texto=False, ref=False)
            tit(tela, 'O CORTE?', 182, ACO3, 9)
            return
        if t < 27.8:
            x, y, w, h = self.INSET
            caixa(tela, x, y, w, h, 'CORTE DA PÁ')
            self.F.desenhar(tela, t, cor='faixa', clip=(x + 1, y + 1, x + w - 1, y + h - 1))
            desenhar_perfil(tela, self.F, 6.0, .1)
            fundo_painel(tela, 106, 204)
            tit(tela, 'O AR VEM DE FRENTE:', 112, ACO3, 9)
            tit(tela, 'A PÁ ANDA CONTRA ELE', 123, ACO3, 9)
            if t >= 16.8:
                u = ease((t - 16.8) / .6)
                for j, yy in enumerate((58, 72, 86)):
                    x0 = x + 128 + (j % 2) * 6
                    seta_forca(tela, x0, yy, x0 + 14 * u, yy + 9 * u, AMARELO, esp=3, cab=5)
                tit(tela, 'AR PARA BAIXO', 144, AMARELO, 17)
            if t >= 22.4:
                u = ease((t - 22.4) / .5)
                xx, yy = self.F.ponto(-0.6, .5, 6.0)
                seta_forca(tela, xx, yy - 3, xx, yy - 3 - 30 * u, CIANO, esp=4, cab=6)
                tit(tela, 'PÁ PARA CIMA', 166, CIANO, 17)
            return
        fundo_painel(tela)
        tit(tela, 'VELOCIDADE', 12)
        tit(tela, 'DA PÁ (A 100%)', 32, ACO3, 9)
        for j, (nome, fr) in enumerate((('PERTO DO CENTRO', .25), ('NO MEIO', .5), ('NA PONTA', 1.0))):
            y = 54 + j * 34
            tit(tela, nome, y, ACO3, 9)
            barra(tela, PX0, y + 12, 110, 6, fr * ease((t - 27.8) / 1.5), LARANJA if fr == 1 else AMARELO)
            tit(tela, f"{milhar(KMH_PONTA * fr)} KM/H", y + 10, BRANCO, 9, PX0 + 116)
        tit(tela, 'RAIO MAIOR,', 160, ACO3, 9)
        tit(tela, 'CAMINHO MAIOR', 171, ACO3, 9)
        tit(tela, 'NA MESMA VOLTA', 182, ACO3, 9)

    def lado(self, tela, t):
        u = t - self.T_LADO
        bob = math.sin(t * 1.4) * 1.2
        sk = 140 + bob
        self.cenario(tela, t, vento=1.0, vento_x=130)
        hx, hy, oy = self.heli(tela, 130, sk, 1.3, t, psi=self.fase(t), ar=1.0)
        if u >= 5.6:
            v = ease((u - 5.6) / .6)
            seta_forca(tela, hx, hy - 6, hx, hy - 6 - 40 * v, CIANO)
            seta_forca(tela, 130, oy + 26, 130, oy + 26 + 40 * v, VERMELHO)
            if v > .8 and not VERTICAL:
                tela.texto('FORÇA DO ROTOR', hx + 8, hy - 44, CIANO, tam=9, contorno=PRETO)
                tela.texto('PESO', 138, oy + 56, VERMELHO, tam=9, contorno=PRETO)
        if not VERTICAL:
            tela.texto('AR PARA BAIXO', 8, 120, CIANO, tam=9, contorno=PRETO)
            painel_voo(tela, .55, (0, 0), 100, 3, extra=[('FORÇA = PESO', VERDE)] if u >= 5.6 else [])

    def sons(self, fx):
        self.rotor_som(fx, self.fase, 0, self.T_LADO, .3)
        self.vento(fx, 11.2, 27.8, .07)
        self.turbina(fx, self.T_LADO, self.dur, .1)
        self.rotor_som(fx, self.fase, self.T_LADO, self.dur, .2)
        for tt in (11.2, 16.8, 22.4, 27.8, 33.4):
            fx.put(fx.blip(74, .1), self.t0 + tt, .18)


# ============================================================ 3 o giro de verdade
class Giro(Voo):
    CX, CY, S = 130, 104, 2.0
    T_LADO = 23.4

    def voltas(self, t):
        if t < 5.8: return .16
        u = min(1.0, (t - 5.8) / 4.6)
        return math.exp(math.log(.16) + (math.log(VOLTAS_S) - math.log(.16)) * suave(u))

    def rpm_pct(self, t):
        base = self.voltas(t) / VOLTAS_S * 100
        if t > 11.8: base += 1.2 * math.sin(t * 1.7) + .6 * math.sin(t * 4.1)
        return base

    def preparar(self):
        super().preparar()
        self.fase = Fase(self.voltas, self.dur)

    def desenhar(self, tela, t, tg):
        v = self.voltas(t)
        if t < self.T_LADO:
            fundo_oficina(tela)
            cx, cy, s = self.CX, self.CY, self.S
            TOPO.corpo(tela, cx, cy, s, 0, t, sombra=False, fantasma=True, cauda=False)
            TOPO.rotor(tela, cx, cy, s, 0, self.fase(t), giro=v)
            if v < 1.2:
                arco_seta(tela, cx, cy, TOPO.R * s + 9, TOPO.R * s + 9, 200, 250, CIANO, cab=6)
            lento = t < 7.0
            if VERTICAL:
                x = x_corte('giro') + 90
                etiqueta(tela, 'CÂMERA LENTA' if lento else 'VELOCIDADE REAL', x - (40 if lento else 50), 190,
                         CIANO if lento else AMARELO, 9)
                hud_vertical(tela, 'giro', [(f"{milhar(v * 60)} RPM", AMARELO)])
                return
            etiqueta(tela, 'CÂMERA LENTA' if lento else 'VELOCIDADE REAL', 20, 10, CIANO if lento else AMARELO, 9)
        else:
            self.cenario(tela, t, alt_ceu=0, vento=1.0, vento_x=120)
            hx, hy, oy = self.heli(tela, 120, 150 + math.sin(t * 1.4), 1.4, t, psi=self.fase(t), ar=.9)
            # zoom na cabeça do rotor
            if not VERTICAL:
                bx, by, bw, bh = 196, 10, 100, 112
                u = ease((t - self.T_LADO) / .6)
                tela.linha(hx, hy, bx, by + bh, AMARELO); tela.linha(hx, hy, bx + bw, by + bh, AMARELO)
                tela.anel(hx, hy, 8, AMARELO, 1.0)
                if u > .5:
                    caixa(tela, bx, by, bw, bh, None, borda=AMARELO)
                    CAB.desenhar(tela, bx + 50, by + 74, 8.5, self.fase(t) * .02, h=.4, rb=5.2)
                    if int(t * 3) % 2 == 0:
                        tela.texto('?', bx + 50, by + 4, AMARELO, tam=17, contorno=PRETO)
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'GIRO DO ROTOR', 12, ACO3, 9)
        tit(tela, f"{milhar(v * 60)} RPM", 24, AMARELO if v > 8 else BRANCO, 26)
        tit(tela, f"{dec(v, 1)} VOLTAS POR SEGUNDO", 56, BRANCO, 9)
        pct = self.rpm_pct(t)
        rpm_barra(tela, PX0, 72, 150, pct)
        if t >= 11.8:
            # gráfico do giro: fica na faixa verde
            gx, gy, gw, gh = PX0, 88, 150, 40
            tela.ret(gx, gy + gh, gw, 1, ACO2); tela.ret(gx, gy, 1, gh, ACO2)
            y100 = gy + gh - (100 - 60) / 50 * gh
            dither(tela, gx + 1, gy + gh - (102 - 60) / 50 * gh, gw - 1, (102 - 95) / 50 * gh, AGUA0, FUNDO)
            prev = None
            for k in range(0, 61):
                tt = t - 6.0 + k * .1
                if tt < 11.8: continue
                p = (gx + k * 2.4, gy + gh - (self.rpm_pct(tt) - 60) / 50 * gh)
                if prev: tela.linha(*prev, *p, VERDE)
                prev = p
            tit(tela, 'QUASE CONSTANTE', gy + gh + 4, VERDE, 9)
        if t >= 17.6:
            a = 4 + 9 * (.5 + .5 * math.sin((t - 17.6) * 1.6))
            perfil_icone(tela, PX0 + 70, 168, 52, a)
            tit(tela, 'O QUE MUDA:', 146, ACO3, 9)
            tit(tela, 'O ÂNGULO', 190, AMARELO, 9)

    def sons(self, fx):
        self.rotor_som(fx, self.fase, 0, self.dur, .25)
        self.turbina(fx, 5.8, self.dur, .1)
        fx.put(fx.chiado(4.6, 200, 2400, ataque=3.0), self.t0 + 5.8, .12)


# ============================================================ 4 o prato cíclico
class Prato(Cena):
    PARTES = [('PRATO CÍCLICO', 'rolamento', None, 0.0), ('PRATO FIXO', 'fixo', 'fixo', 6.0),
              ('PRATO GIRATÓRIO', 'giratorio', 'giratorio', 12.0), ('ROLAMENTO', 'rolamento', 'rolamento', 18.0),
              ('HASTE DE PASSO', 'haste', 'haste', 24.0), ('ÂNGULO DA PÁ', 'pa', 'pa', 30.0)]
    CX, CY, S = 150, 126, 20

    def preparar(self):
        self.fase = Fase(lambda t: .12, self.dur)

    def h(self, t):
        if t < 30.0: return .25
        return .25 + .55 * (.5 - .5 * math.cos((t - 30.0) * 1.3))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        k_at = max(i for i, p in enumerate(self.PARTES) if t >= p[3])
        nome, anc_n, dest, t0 = self.PARTES[k_at]
        psi = self.fase(t)
        anc = CAB.desenhar(tela, self.CX, self.CY, self.S, psi, h=self.h(t), rb=5.0, destaque=dest, t=t)
        etiqueta(tela, 'CÂMERA LENTA', 8, 10, CIANO, 9)
        # rótulos fixos de "gira / não gira"
        if 6.0 <= t < 24.0:
            fx_, fy_ = anc['fixo']
            tela.texto('NÃO GIRA', 18, fy_ + 6, ACO3, tam=9, contorno=PRETO)
            gx_, gy_ = anc['giratorio']
            tela.texto('GIRA', 18, gy_ - 10, LATAO, tam=9, contorno=PRETO)
            arco_seta(tela, 60, gy_ - 6, 10, 3, 200, 340, LATAO, cab=4)
        if t >= 6.0 and t < 12.0:
            x, y = anc['comando']
            tela.texto('COMANDOS', x + 14, y + 10, ACO3, tam=9, contorno=PRETO)
        # ---- lista de peças com fio
        fundo_painel(tela)
        for i, (n, an, de, tt) in enumerate(self.PARTES):
            if t < tt: continue
            y = 12 + i * 22
            atual = i == k_at
            tela.texto(n, PX0, y, AMARELO if atual else ACO2, tam=17 if len(n) < 14 else 9, contorno=PRETO)
            if atual and t - tt > .3:
                ax, ay = anc[an]
                tela.linha(PX0 - 4, y + 6, ax, ay, AMARELO)
                tela.disco(ax, ay, 1.8, AMARELO)
                tela.ret(PX0 - 6, y + 5, 3, 3, AMARELO)
        if t >= 30.0:
            th = CAB.passo(psi, self.h(t), 0, 0)
            perfil_icone(tela, PX0 + 70, 178, 50, th)
            tela.texto('PÁ AMARELA', PX0, 152, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for _, _, _, tt in self.PARTES:
            fx.put(fx.clique(1800, .05), self.t0 + tt + .3, .35)
            fx.put(fx.blip(76, .08), self.t0 + tt + .3, .15)
        self.rotor_som(fx, self.fase, 0, self.dur, .2)


# ============================================================ 5 coletivo
class Coletivo(Voo):
    OX, K = 96, 1.2
    COL = [(0, .15), (5.8, .15), (11.2, .4), (17.0, .4), (22.6, .62), (24.5, .8), (28.2, .8), (30.5, .32),
           (39.4, .32), (41.6, .55), (48, .55)]
    ALT = [(0, 0.0), (21.6, 0.0), (29.6, 16.0), (31.0, 16.0), (39.8, 5.0), (48, 5.0)]
    INSET = (192, 8, 106, 196)

    def col(self, t): return rampa(t, self.COL)
    def alt(self, t): return rampa(t, self.ALT)
    def forca(self, t): return self.col(t) / .55

    def preparar(self):
        super().preparar()
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)
        self.lenta = Fase(lambda t: .2, self.dur)

    def desenhar(self, tela, t, tg):
        c, a = self.col(t), self.alt(t)
        sk = 176 - a * 4
        bob = math.sin(t * 1.5) * .8 if a > .5 else 0
        self.cenario(tela, t, vento=min(1.0, c * 1.5), vento_x=self.OX)
        self.heli(tela, self.OX, sk + bob, self.K, t, psi=self.fase(t), ar=.3 + .7 * min(1.0, self.forca(t)))
        th = CAB.passo(0, c, 0, 0)
        if VERTICAL:
            hud_vertical(tela, 'coletivo', [(f"COLETIVO {int(round(c * 100))}%", AMARELO), (f"ÂNGULO {int(round(th))}°", BRANCO),
                                            (f"ALTURA {milhar(a)} M", CIANO)])
            return
        # ---- zoom no prato
        x, y, w, h = self.INSET
        caixa(tela, x, y, w, h, 'PRATO CÍCLICO')
        psi = self.lenta(t)
        CAB.desenhar(tela, x + 53, y + 122, 10.5, psi, h=c, rb=4.6)
        tela.texto('CÂMERA LENTA', x + 3, y + 12, CIANO, tam=9, contorno=PRETO)
        if 5.8 <= t < 17.0:
            seta_forca(tela, x + 12, y + 128, x + 12, y + 108, AMARELO, esp=3, cab=5)
            tela.texto('SOBE', x + 4, y + 132, AMARELO, tam=9, contorno=PRETO)
        for j, (rot, ps) in enumerate((('A', psi), ('B', psi + math.pi))):
            ang = CAB.passo(ps, c, 0, 0)
            px = x + 27 + j * 52
            perfil_icone(tela, px, y + 182, 24, ang, cor=ACO3 if j == 0 else ACO2, texto=False, ref=False)
            tela.texto(f"{rot}: {int(round(ang))}°", px - 14, y + 160, AMARELO if j == 0 else LARANJA, tam=9, contorno=PRETO)
        # ---- painel
        f = self.forca(t)
        extra = [('FORÇA DO ROTOR', CIANO), ('PESO', VERMELHO)]
        painel_voo(tela, c, (0, 0), 100, a, dest=('col',) if t >= 5.8 else (), extra=[])
        tit(tela, 'FORÇA', 180, CIANO, 9)
        barra(tela, PX0 + 40, 181, 110, 5, f / 1.6, CIANO)
        tit(tela, 'PESO', 192, VERMELHO, 9)
        barra(tela, PX0 + 40, 193, 110, 5, 1 / 1.6, VERMELHO)

    def sons(self, fx):
        self.turbina(fx, 0, self.dur, .1)
        self.rotor_som(fx, self.fase, 0, self.dur, .18)
        fx.put(fx.chiado(5.0, 100, 700, ataque=1.5), self.t0 + 22.6, .14)       # mais força: mais ar
        for tt in (5.8, 28.2, 39.4):
            fx.put(fx.clique(1400, .04), self.t0 + tt, .3)


# ============================================================ 6 pairar
class Pairar(Voo):
    OX, K = 140, 1.35

    def preparar(self):
        super().preparar()
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)

    def comandos(self, t):
        u = min(1.0, max(0.0, (t - 16.8) / 1.0)) * .7 + .3
        col = .55 + .04 * math.sin(t * 2.3) * u
        cic = (.35 * math.sin(t * 1.9) * u, .3 * math.sin(t * 1.3 + 1) * u)
        ped = .5 * math.sin(t * 1.1 + 2) * u
        return col, cic, ped

    def desenhar(self, tela, t, tg):
        col, cic, ped = self.comandos(t)
        dx = -cic[0] * 6
        sk = 156 + math.sin(t * 1.6) * 1.2
        self.cenario(tela, t, vento=1.0, vento_x=self.OX + dx)
        # rajadas de vento
        for q in range(6):
            u = (t * .7 + q / 6) % 1.0
            x = -20 + u * (W + 40)
            y = 30 + q * 22
            tela.ret(x, y, 10, 1, ACO2); tela.ret(x + 12, y, 4, 1, ACO2)
        hx, hy, oy = self.heli(tela, self.OX + dx, sk, self.K, t, ang=-cic[1] * 3, psi=self.fase(t), ar=1.0)
        if t >= .4:
            u = ease((t - .4) / .6)
            seta_forca(tela, hx, hy - 6, hx, hy - 6 - 42 * u, CIANO)
            seta_forca(tela, self.OX + dx, oy + 28, self.OX + dx, oy + 28 + 42 * u, VERMELHO)
            if u > .8:
                tela.texto('=', hx + 10, hy + 4, VERDE, tam=26, contorno=PRETO)
        if VERTICAL: return
        dest = ('col', 'cic') if t >= 16.8 else ()
        painel_voo(tela, col, cic, 100 + math.sin(t * 2) * .6, 5, dest=dest)
        if t >= 16.8:
            tit(tela, 'PEDAIS', 182, AMARELO, 9)
            pedais(tela, PX0 + 50, 180, ped, destaque=True)
        else:
            tit(tela, 'FORÇA = PESO', 184, VERDE, 17) if t >= 5.8 else None

    def sons(self, fx):
        self.turbina(fx, 0, self.dur, .1)
        self.rotor_som(fx, self.fase, 0, self.dur, .18)
        self.vento(fx, 0, self.dur, .07, 150, 900)


# ============================================================ 7 cíclico
class Ciclico(Voo):
    CX, CY, S = 118, 102, 1.9
    INSET = (204, 8, 94, 160)
    T_LADO, T_TOPO, T_VOLTA = 33.8, 45.0, 50.6
    INC = 6.0                                    # inclinação do prato com o cíclico todo (graus)

    def f(self, t): return math.sin(self.INC * math.pi / 180) * rampa(t, [(5.8, 0.0), (7.8, 1.0)])

    def preparar(self):
        super().preparar()
        self.lenta = Fase(lambda t: .2, self.dur)
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)
        ts = np.arange(0, self.dur + .05, .05)
        vs = np.array([self.vel(u) for u in ts])
        self._ts, self._xm = ts, np.concatenate([[0], np.cumsum(vs[:-1] * .05)])

    def vel(self, t):   # px/s do chão passando
        return rampa(t, [(self.T_LADO, 0.0), (41.0, 120.0)])

    def cic_topo(self, t):
        """Cíclico na parte vista de cima: esquerda, trás, direita."""
        u = t - self.T_TOPO
        return rampa(u, [(0, (0)), (.01, 0)]) if False else None

    def desenhar(self, tela, t, tg):
        if t >= self.T_TOPO and t < self.T_VOLTA:
            return self.topo_dirs(tela, t)
        if t >= self.T_LADO:
            return self.lado(tela, t)
        fundo_oficina(tela)
        cx, cy, s = self.CX, self.CY, self.S
        psi = self.lenta(t)
        f = self.f(t)
        h = .5
        R = TOPO.R * s
        TOPO.corpo(tela, cx, cy, s, 0, t, sombra=False, fantasma=True, cauda=False)
        # disco: metade de trás mais clara quando inclinado (está mais alta)
        if t >= 22.6:
            u = ease((t - 22.6) / 1.0)
            yy, xx = np.mgrid[int(cy - R):int(cy + R) + 1, int(cx - R):int(cx + R) + 1]
            d = np.hypot(xx - cx, yy - cy)
            m = (d < R) & (d > 6)
            atras = m & (yy > cy + 4) & ((xx + yy) % 3 == 0) & (np.abs(yy - cy) / R < u + .01)
            frente = m & (yy < cy - 4) & ((xx + yy) % 4 == 0) & (np.abs(yy - cy) / R < u + .01)
            tela.buf[yy[atras], xx[atras]] = TRACO
            tela.buf[yy[frente], xx[frente]] = PRETO
        # anel com o ângulo em cada ponto da volta
        if t >= 11.4:
            med = CAB.passo(0, h, 0, 0)
            for k in range(60):
                a = k * G / 60
                th = CAB.passo(a, h, f, 0)
                c = LARANJA if th > med + 1.0 else (CIANO if th < med - 1.0 else ACO2)
                x, y = TOPO.ponta(cx, cy, s, 0, a, TOPO.R + 4)
                tela.ret(x - 1, y - 1, 3, 3, PRETO); tela.px(x, y, c); tela.px(x + 1, y, c)
        TOPO.rotor(tela, cx, cy, s, 0, psi)
        th = CAB.passo(psi, h, f, 0)
        x, y = TOPO.ponta(cx, cy, s, 0, psi, TOPO.R + 13)
        tela.texto(f"{int(round(th))}°", x - 8, y - 4, AMARELO, tam=9, contorno=PRETO)
        # nariz
        tela.texto('FRENTE', cx - 18, 2, ACO3, tam=9, contorno=PRETO)
        if t >= 17.0:
            tela.texto('+ÂNGULO', cx - R - 12 if not VERTICAL else cx - R + 2, cy + 6, LARANJA, tam=9, contorno=PRETO)
            tela.texto('-ÂNGULO', cx + R - 30, cy + 6, CIANO, tam=9, contorno=PRETO)
        if t >= 22.6:
            u = ease((t - 22.6) / .8)
            arco_seta(tela, cx, cy, R * .55, R * .55, 180, 180 + 90 * u, AMARELO, cab=5)
            tela.texto('1/4 DE VOLTA', cx - R * .55 - 6, cy + R * .55 + 4, AMARELO, tam=9, contorno=PRETO)
            tela.texto('SOBE', cx - 12, cy + R - 14, BRANCO, tam=9, contorno=PRETO)
            tela.texto('DESCE', cx - 14, cy - R + 10, ACO3, tam=9, contorno=PRETO)
        if VERTICAL:
            hud_vertical(tela, 'ciclico', [(f"PÁ AMARELA: {int(round(th))}°", AMARELO),
                                           ('CÍCLICO: FRENTE' if f > .01 else 'CÍCLICO: CENTRO', BRANCO)])
            return
        etiqueta(tela, 'CÂMERA LENTA', 8, 192, CIANO, 9)
        # ---- prato, visto de lado
        x0, y0, w, hh = self.INSET
        caixa(tela, x0, y0, w, hh, 'PRATO DE LADO')
        CAB.desenhar(tela, x0 + 48, y0 + 112, 9.5, psi, h=h, f=f, rb=4.4)
        tela.texto('FRENTE >', x0 + 40, y0 + hh - 12, ACO3, tam=9, contorno=PRETO)
        if f > .01:
            tela.texto('INCLINA', x0 + 3, y0 + 14, AMARELO, tam=9, contorno=PRETO)
        # ---- painel
        fundo_painel(tela)
        tit(tela, 'CÍCLICO', 9, AMARELO if t >= 5.8 else ACO3, 9)
        fy = f / math.sin(self.INC * math.pi / 180)
        manche(tela, PX0, 22, 0, fy, t >= 5.8)
        tit(tela, direcao((0, fy)), 28, BRANCO, 17, PX0 + 38)
        tit(tela, 'PÁ AMARELA', 58, ACO3, 9)
        perfil_icone(tela, PX0 + 62, 82, 44, th, texto=False)
        tit(tela, f"{int(round(th))}°", 72, AMARELO, 17, PX0 + 112)
        # gráfico: ângulo x posição na volta
        gx, gy, gw, gh = PX0 + 2, 112, 150, 52
        tela.ret(gx, gy + gh, gw, 1, ACO2); tela.ret(gx, gy, 1, gh, ACO2)
        Y = lambda a: gy + gh - (a - 0) / 22 * gh
        prev = None
        for k in range(0, 61):
            a = k * G / 60
            p = (gx + k * gw / 60, Y(CAB.passo(a, h, f, 0)))
            if prev: tela.linha(*prev, *p, LARANJA if CAB.passo(a, h, f, 0) > CAB.passo(0, h, 0, 0) + 1 else CIANO)
            prev = p
        aa = psi % G
        p = (gx + aa / G * gw, Y(th))
        tela.disco(*p, 3.2, PRETO); tela.disco(*p, 2.3, AMARELO)
        for j, nm in enumerate(('FR', 'ESQ', 'TRÁS', 'DIR')):
            tela.texto(nm, gx + j * gw / 4 - 2, gy + gh + 3, ACO3, tam=9, contorno=PRETO)
        tit(tela, 'ÂNGULO NA VOLTA', gy - 12, ACO3, 9)
        if t >= 28.2:
            # disco de lado, inclinado para a frente
            u = ease((t - 28.2) / .8)
            dx, dy = 52, 8 * u
            yc = 192
            linha_grossa(tela, PX0 + 70 - dx, yc - dy, PX0 + 70 + dx, yc + dy, 3, AMARELO)
            tela.texto('DISCO', PX0 + 2, yc - 12, ACO3, tam=9, contorno=PRETO)

    def lado(self, tela, t):
        u = t - self.T_LADO
        xm = float(np.interp(t, self._ts, self._xm))
        ang = rampa(t, [(37.0, 0.0), (41.0, -8.0)])
        disco = rampa(t, [(self.T_LADO, 0.0), (36.0, 5.0)])
        col = .55 if t < self.T_VOLTA else rampa(t, [(self.T_VOLTA, .55), (53.0, .68)])
        sk = 118 + math.sin(t * 1.2)
        if t >= self.T_VOLTA:
            sk -= rampa(t, [(52.0, 0.0), (58.0, 6.0)])
        self.cenario(tela, t, alt_ceu=150, xm=xm, gy=260, heliponto=None)
        ox, k = 150, 1.3
        hx, hy, oy = self.heli(tela, ox, sk, k, t, ang=ang, psi=self.fase(t), disco=disco, ar=.8, chao=300, sombra=False)
        # força do rotor inclinada e as partes
        a = (ang - disco) * math.pi / 180
        L = 46 * (col / .55)
        ex, ey = hx - math.sin(a) * L, hy - math.cos(a) * L
        seta_forca(tela, hx, hy - 4, ex, ey, CIANO)
        if u >= 5.0:
            for q in range(0, int(abs(ex - hx)), 3):
                tela.px(hx + q * math.copysign(1, ex - hx), ey, AMARELO)
            seta_forca(tela, hx, ey + 6, ex, ey + 6, AMARELO, esp=3, cab=6)
            if not VERTICAL: tela.texto('PARA A FRENTE', ex + 6, ey + 2, AMARELO, tam=9, contorno=PRETO)
        if not VERTICAL:
            tela.texto('FORÇA DO ROTOR', hx - 96, ey - 6, CIANO, tam=9, contorno=PRETO)
        if VERTICAL: return
        cic = (0.0, rampa(t, [(self.T_LADO, 1.0), (44.0, .5)]))
        extra = [('ANDANDO PARA A FRENTE', AMARELO)] if u >= 5.6 else []
        if t >= self.T_VOLTA: extra = [('MAIS COLETIVO', AMARELO), ('PARA NÃO PERDER ALTURA', ACO3)]
        painel_voo(tela, col, cic, 100, 30, dest=('cic',) if t < self.T_VOLTA else ('col',), extra=extra)

    def topo_dirs(self, tela, t):
        """O cíclico para os lados e para trás, visto de cima."""
        u = t - self.T_TOPO
        # esquerda (0..1,8), trás (1,8..3,6), direita (3,6..5,4)
        etapas = [((-1.0, 0.0), 'ESQUERDA'), ((0.0, -1.0), 'TRÁS'), ((1.0, 0.0), 'DIREITA')]
        k = min(2, int(u / 1.8))
        (cx_, cy_), nome = etapas[k]
        uu = (u - k * 1.8) / 1.8
        m = ease(uu / .3) * (1 - ease((uu - .8) / .2))
        # o chão corre ao contrário do movimento
        xm = -cx_ * u * 60
        ym = cy_ * u * 60
        chao_topo(tela, t, xm=xm, ym=ym, heliponto=False)
        cx, cy = 140 + cx_ * 10 * m, 104 - cy_ * 10 * m
        TOPO.corpo(tela, cx, cy, 1.15, 0, t, giro_c=40, psi_c=t * 30)
        TOPO.rotor(tela, cx, cy, 1.15, 0, self.fase(t), giro=VOLTAS_S)
        seta_forca(tela, cx + cx_ * 56, cy - cy_ * 56, cx + cx_ * 86, cy - cy_ * 86, AMARELO)
        etiqueta(tela, 'VISTO DE CIMA', 8, 10, ACO3, 9, borda=ACO1)
        if VERTICAL: return
        painel_voo(tela, .55, (cx_ * m, cy_ * m), 100, 30, dest=('cic',), extra=[(f"VAI PARA: {nome}", AMARELO)])

    def sons(self, fx):
        self.rotor_som(fx, self.lenta, 0, self.T_LADO, .25)
        self.turbina(fx, self.T_LADO, self.dur, .1)
        self.rotor_som(fx, self.fase, self.T_LADO, self.dur, .18)
        self.vento(fx, 38.0, self.dur, .08, 200, 1600)
        for tt in (5.8, 22.6, 28.2):
            fx.put(fx.blip(76, .1), self.t0 + tt, .18)


# ============================================================ 8 torque e rotor de cauda
class Torque(Cena):
    CX, CY, S = 150, 88, 1.6
    T_CAUDA, T_LIGA, T_EIXO = 17.0, 19.0, 28.2

    def voltas(self, t): return .35

    def omega(self, t):            # giro do corpo, graus/s (negativo = horário)
        sobe = rampa(t, [(5.8, 0.0), (11.0, -75.0)])
        if t < self.T_LIGA: return sobe
        return rampa(t, [(self.T_LIGA, -75.0), (23.5, 0.0)])

    def preparar(self):
        self.fase = Fase(self.voltas, self.dur)
        ts = np.arange(0, self.dur + .05, .01)
        w = np.array([self.omega(u) for u in ts])
        yaw = np.concatenate([[0], np.cumsum(w[:-1] * .01)])
        i = int(23.5 / .01)
        alvo = round(yaw[i] / 360.0) * 360.0
        for j in range(i, len(ts)):
            yaw[j] = yaw[i] + (alvo - yaw[i]) * suave((ts[j] - 23.5) / 3.5)
        self._ts, self._yaw = ts, yaw
        self.giro_c = lambda t: 0.0 if t < self.T_LIGA else min(1.0, (t - self.T_LIGA) / 1.5) * self.voltas(t) * 6.4

    def yaw(self, t): return float(np.interp(t, self._ts, self._yaw))

    def desenhar(self, tela, t, tg):
        cx, cy, s = self.CX, self.CY, self.S
        chao_topo(tela, t)
        y = self.yaw(t)
        gc = self.giro_c(t)
        T = TOPO.corpo(tela, cx, cy, s, y, t, psi_c=t * gc * G, giro_c=gc,
                       destaque_cauda=self.T_CAUDA <= t < 22.6, eixo=t if t >= self.T_EIXO else None)
        TOPO.rotor(tela, cx, cy, s, 0, self.fase(t))
        R = TOPO.R * s
        # o rotor gira para um lado (anti-horário)
        arco_seta(tela, cx, cy, R + 8, R + 8, 100, 160, CIANO, cab=6)
        tela.texto('ROTOR', cx - R - 6, cy - R + 2, CIANO, tam=9, contorno=PRETO)
        w = self.omega(t)
        if abs(w) > 5 and t < 23.5:
            # o corpo gira para o outro (horário)
            arco_seta(tela, cx, cy, 30, 30, 60, -40, VERMELHO, cab=6)
            tela.texto('CORPO', cx + 26, cy - 34, VERMELHO, tam=9, contorno=PRETO)
        if t >= self.T_LIGA:
            # força da cauda (para a direita do helicóptero) e o ar soprando ao contrário
            u = min(1.0, (t - self.T_LIGA) / 1.5)
            a0 = T(1.0, -61); a1 = T(1.0 + 18 * u, -61)
            seta_forca(tela, *a0, *a1, AMARELO, esp=4, cab=6)
            for q in range(5):
                uu = (t * 2.2 + q / 5) % 1.0
                p = T(-4 - uu * 22 * u, -58 - q * 2)
                tela.ret(p[0], p[1], 3, 1, CIANO)
        if self.T_CAUDA <= t < 28.2 and not VERTICAL:
            p = T(-2.8, -61)
            rotulo(tela, 'ROTOR DE CAUDA', 10, 186, p[0], p[1], AMARELO)
        if t >= self.T_EIXO and not VERTICAL:
            p = T(0, -30)
            rotulo(tela, 'EIXO', 236, 176, p[0], p[1], AMARELO)
        if VERTICAL:
            st = 'CAUDA: DESLIGADA' if t < self.T_LIGA else 'CAUDA: LIGADA'
            hud_vertical(tela, 'torque', [(st, AMARELO if t >= self.T_LIGA else VERMELHO)])
            return
        etiqueta(tela, 'VISTO DE CIMA', 8, 10, ACO3, 9, borda=ACO1)
        # ---- painel
        fundo_painel(tela)
        tit(tela, 'TORQUE', 10)
        tit(tela, 'ROTOR DE CAUDA', 34, ACO3, 9)
        lig = t >= self.T_LIGA
        if t >= self.T_CAUDA or True:
            tit(tela, 'LIGADO' if lig else 'DESLIGADO', 45, VERDE if lig else VERMELHO, 17)
        tit(tela, 'GIRO DO CORPO', 70, ACO3, 9)
        barra(tela, PX0, 82, 150, 6, abs(w) / 80, VERMELHO)
        tit(tela, 'PARADO' if abs(w) < 3 else 'RODANDO', 92, VERDE if abs(w) < 3 else VERMELHO, 9)
        if t >= 33.8:
            tit(tela, 'POTÊNCIA DO MOTOR', 112, ACO3, 9)
            u = ease((t - 33.8) / 1.0)
            tela.ret(PX0 - 1, 123, 152, 10, ACO1)
            tela.ret(PX0, 124, int(135 * u), 8, CIANO)
            tela.ret(PX0 + 135, 124, int(15 * u), 8, AMARELO)
            tit(tela, 'ROTOR', 136, CIANO, 9)
            tit(tela, '10% CAUDA', 136, AMARELO, 9, PX0 + 96)
        if t >= 38.6:
            tit(tela, 'GIRO (A 100%)', 156, ACO3, 9)
            tit(tela, f"ROTOR: {RPM100} RPM", 168, CIANO, 9)
            tit(tela, f"CAUDA: {milhar(RPM_CAUDA)} RPM", 180, AMARELO, 9)
            tit(tela, '6,4 VEZES', 192, BRANCO, 9)

    def sons(self, fx):
        self.turbina(fx, 0, self.dur, .09)
        self.rotor_som(fx, self.fase, 0, self.dur, .22)
        fx.put(fx.chiado(4.0, 200, 600, ataque=2.0), self.t0 + 6.0, .1)
        fx.put(fx.clique(1600, .04), self.t0 + self.T_LIGA, .3)
        fx.put(fx.chiado(self.dur - self.T_LIGA, 900, 3200, ataque=1.2), self.t0 + self.T_LIGA, .07)


# ============================================================ 9 pedais
class Pedais(Cena):
    CX, CY, S = 150, 88, 1.6
    PED = [(0, 0.0), (5.8, 0.0), (6.6, -.45), (8.6, -.45), (9.4, .45), (10.4, .45), (11.0, 0.0), (11.4, 0.0),
           (12.0, -1.0), (15.0, -1.0), (15.8, 0.0), (16.8, 0.0), (17.4, 1.0), (21.8, 1.0), (22.6, 0.0), (24, 0.0)]

    def ped(self, t): return rampa(t, self.PED)

    def preparar(self):
        self.fase = Fase(lambda t: .35, self.dur)
        ts = np.arange(0, self.dur + .05, .01)
        w = np.array([-self.ped(u) * 32.0 for u in ts])
        self._ts, self._yaw = ts, np.concatenate([[0], np.cumsum(w[:-1] * .01)])

    def yaw(self, t): return float(np.interp(t, self._ts, self._yaw))

    def desenhar(self, tela, t, tg):
        cx, cy, s = self.CX, self.CY, self.S
        chao_topo(tela, t)
        p = self.ped(t)
        y = self.yaw(t)
        gc = .35 * 6.4
        T = TOPO.corpo(tela, cx, cy, s, y, t, psi_c=t * gc * G, giro_c=gc)
        TOPO.rotor(tela, cx, cy, s, 0, self.fase(t))
        forca = 1.0 - .6 * p
        a0 = T(1.0, -61); a1 = T(1.0 + 16 * forca, -61)
        seta_forca(tela, *a0, *a1, AMARELO, esp=4, cab=6)
        for q in range(5):
            uu = (t * 2.2 + q / 5) % 1.0
            pp = T(-4 - uu * 20 * forca, -58 - q * 2)
            tela.ret(pp[0], pp[1], 3, 1, CIANO)
        if abs(p) > .2:
            # o nariz virando
            n = T(0, 24)
            a = math.degrees(math.atan2(-(n[1] - cy), n[0] - cx))
            if p < 0: arco_seta(tela, cx, cy, 44, 44, a - 25, a + 25, VERDE, cab=6)
            else: arco_seta(tela, cx, cy, 44, 44, a + 25, a - 25, VERDE, cab=6)
        lado = 'ESQUERDO' if p < -.2 else ('DIREITO' if p > .2 else None)
        if VERTICAL:
            hud_vertical(tela, 'pedais', [(f"PEDAL {lado}" if lado else 'PEDAIS NO MEIO', AMARELO)])
            return
        etiqueta(tela, 'VISTO DE CIMA', 8, 10, ACO3, 9, borda=ACO1)
        fundo_painel(tela)
        tit(tela, 'PEDAIS', 10)
        pedais(tela, PX0 + 8, 34, p, destaque=True)
        if lado: tit(tela, lado, 38, AMARELO, 9, PX0 + 64)
        tit(tela, 'ÂNGULO DAS PÁS', 70, ACO3, 9)
        tit(tela, 'DA CAUDA', 80, ACO3, 9)
        perfil_icone(tela, PX0 + 64, 110, 40, 8 - 6 * p)
        tit(tela, 'FORÇA NA CAUDA', 136, ACO3, 9)
        barra(tela, PX0, 148, 150, 6, forca / 1.7, AMARELO)
        if abs(p) > .2:
            tit(tela, 'NARIZ VIRA PARA A', 166, ACO3, 9)
            tit(tela, 'ESQUERDA' if p < 0 else 'DIREITA', 177, VERDE, 17)

    def sons(self, fx):
        self.turbina(fx, 0, self.dur, .09)
        self.rotor_som(fx, self.fase, 0, self.dur, .2)
        for tt in (6.6, 9.4, 12.0, 17.4):
            fx.put(fx.clique(900, .05), self.t0 + tt, .3)


# ============================================================ 10 dois rotores
def tandem(tela, ox, oy, k, t, psi1, psi2, giro):
    """Helicóptero genérico de 2 rotores em tandem, de lado."""
    P = lambda x, y: (ox + k * x, oy + k * y)
    L = lambda pts: [P(x, y) for x, y in pts]
    corpo = [(-56, -8), (-46, -14), (24, -14), (32, -10), (36, -2), (34, 6), (26, 10), (-50, 10), (-58, 2)]
    pilone = [(-58, -8), (-50, -26), (-38, -26), (-36, -12)]
    for poly, c1, c2 in ((pilone, ACO3, ACO2), (corpo, ACO4, ACO3)):
        contorno(tela, L(poly), PRETO); pol(tela, L(poly), c1, c2)
    pol(tela, L([(36, -2), (34, 6), (26, 10), (-50, 10), (-58, 2), (30, 2)]), ACO3, ACO2)
    pol(tela, L([(24, -12), (30, -9), (33, -3), (25, -4)]), FUNDO2, FUNDO3)
    tela.linha(*P(26, -11), *P(31, -6), CIANO)
    for x in range(-40, 18, 7):
        tela.ret(*P(x, -6), max(2, int(k * 3)), max(2, int(k * 3)), FUNDO3)
    tela.linha(*P(-54, -1), *P(34, -1), LARANJA)
    for xr in (-40, 12):
        tela.disco(*P(xr, 13), max(2, k * 3), PRETO); tela.disco(*P(xr, 13), max(1, k * 1.8), ACO2)
    for (hx, hy, ps) in ((22, -20, psi1), (-44, -32, psi2)):
        linha_grossa(tela, *P(hx, hy + 6), *P(hx, hy), max(2, k * 1.6), ACO2)
        HELI._rotor(tela, P, k, 0, ps, giro, 0, False, hub=(hx, hy), R=32)
        tela.disco(*P(hx, hy), max(1.5, k * 1.6), PRETO); tela.disco(*P(hx, hy), max(1, k * 1.1), ACO3)


def sentido(tela, cx, cy, rx, ry, anti, cor):
    """Seta na frente do disco: anti-horário (visto de cima) = a parte de cá anda para a direita."""
    if anti: arco_seta(tela, cx, cy, rx, ry, 235, 305, cor, cab=5)
    else: arco_seta(tela, cx, cy, rx, ry, 305, 235, cor, cab=5)


def mini_disco(tela, cx, cy, r, anti, cor, t, rot=0.0):
    tela.anel(cx, cy, r, cor, 1.0)
    a0 = rot
    if anti: arco_seta(tela, cx, cy, r - 4, r - 4, a0 + 20, a0 + 140, cor, cab=4)
    else: arco_seta(tela, cx, cy, r - 4, r - 4, a0 + 140, a0 + 20, cor, cab=4)


class Dois(Cena):
    def preparar(self):
        self.fase = Fase(lambda t: .5, self.dur)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        ps = self.fase(t)
        # ---- coaxial
        ox, oy, k = 84, 150, 1.05
        rot = [dict(hub=(0, -27.0), R=40, psi=-ps + .7, giro=0), dict(hub=(0, -20.5), R=40, psi=ps, giro=0)]
        HELI.desenhar(tela, ox, oy, k, 0, t, rotores=rot, cauda_rotor=False, sombra_y=None)
        P = HELI.P_(ox, oy, k, 0)
        a1, a2 = P(0, -27), P(0, -20.5)
        sentido(tela, a1[0], a1[1] - 2, 46, 8, False, LARANJA)
        sentido(tela, a2[0], a2[1] + 4, 46, 8, True, CIANO)
        tela.texto('COAXIAL', ox - 30, 186, BRANCO if t < 11.2 or t >= 22.2 else ACO3, tam=17, contorno=PRETO)
        # ---- tandem
        tx, ty, tk = 236, 150, .95
        tandem(tela, tx, ty, tk, t, ps, -ps + 1.0, 0)
        f1, f2 = (tx + 22 * tk, ty - 20 * tk), (tx - 44 * tk, ty - 32 * tk)
        sentido(tela, f1[0], f1[1] + 4, 32, 7, True, CIANO)
        sentido(tela, f2[0], f2[1] + 4, 32, 7, False, LARANJA)
        tela.texto('TANDEM', tx - 30, 186, BRANCO if 11.2 <= t < 22.2 or t < 5.8 else ACO3, tam=17, contorno=PRETO)
        if 5.8 <= t < 11.2 and int(t * 3) % 2 == 0:
            tela.ret_vazado(ox - 70, 40, 128, 140, AMARELO)
        if 11.2 <= t < 16.4 and int(t * 3) % 2 == 0:
            tela.ret_vazado(tx - 80, 40, 132, 140, AMARELO)
        etiqueta(tela, 'CÂMERA LENTA', 8, 10, CIANO, 9)
        # ---- painel
        fundo_painel(tela)
        tit(tela, 'DOIS ROTORES', 10)
        tit(tela, 'VISTOS DE CIMA', 30, ACO3, 9)
        mini_disco(tela, PX0 + 34, 70, 26, True, CIANO, t)
        mini_disco(tela, PX0 + 116, 70, 26, False, LARANJA, t)
        tit(tela, 'ANTI-HORÁRIO', 100, CIANO, 9)
        tit(tela, 'HORÁRIO', 100, LARANJA, 9, PX0 + 96)
        if t >= 16.6:
            tit(tela, 'TORQUE', 120, ACO3, 9)
            tit(tela, '+1', 132, CIANO, 17)
            tit(tela, '-1', 132, LARANJA, 17, PX0 + 50)
            tit(tela, '= 0', 132, VERDE, 17, PX0 + 96)
        if t >= 22.2:
            tit(tela, 'COAXIAL VIRANDO:', 160, AMARELO, 9)
            tit(tela, 'CIMA +ÂNGULO', 172, LARANJA, 9)
            tit(tela, 'BAIXO -ÂNGULO', 184, CIANO, 9)
            # o coaxial gira o nariz devagar: ícone de cima
            yaw = (t - 22.2) * 25
            x0, y0 = PX0 + 128, 182
            a = math.radians(90 + yaw)
            tela.disco(x0, y0, 8, ACO1)
            tela.linha(x0, y0, x0 + math.cos(a) * 12, y0 - math.sin(a) * 12, AMARELO)

    def sons(self, fx):
        self.vento(fx, 0, self.dur, .06)
        for t in self.fase.passagens(0, self.dur):
            fx.put(fx.chiado(.3, 180, 900, ataque=.06), self.t0 + t, .12)
        for tt in (5.8, 11.2, 16.6, 22.2):
            fx.put(fx.blip(74, .1), self.t0 + tt, .18)


# ============================================================ 11 autorrotação
class Autorrotacao(Voo):
    OX, K = 130, 1.25
    T_PANE, T_TOCA = 3.0, 50.5

    def rpm(self, t):
        if t < self.T_PANE: return 100.0
        if t < self.T_TOCA - 5.5:
            r = rampa(t, [(self.T_PANE, 100.0), (5.0, 88.0), (9.0, 100.0), (40.0, 100.0), (44.0, 102.5)])
            return r + (.6 * math.sin(t * 1.3) if t > 9 else 0)
        if t < self.T_TOCA: return rampa(t, [(self.T_TOCA - 5.5, 102.5), (self.T_TOCA, 84.0)])
        return rampa(t, [(self.T_TOCA, 84.0), (66.0, 22.0)])

    def col(self, t):
        return rampa(t, [(3.6, .55), (5.0, .08), (44.6, .08), (49.6, .72), (52.0, .72), (54.0, .05)])

    def cic(self, t):
        return (0.0, rampa(t, [(0, .3), (39.0, .3), (41.0, -.8), (46.5, -.8), (48.5, 0.0)]))

    def ang(self, t):
        return rampa(t, [(0, -4.0), (39.0, -4.0), (42.5, 12.0), (46.5, 12.0), (49.5, 0.0)])

    def disco(self, t):
        return rampa(t, [(0, 3.0), (39.0, 3.0), (41.5, -7.0), (46.5, -7.0), (49.0, 0.0)])

    def sentido(self, t): return rampa(t, [(3.8, 1.0), (10.0, -1.0), (self.T_TOCA - .5, -1.0), (self.T_TOCA + .5, 0.0)])

    def preparar(self):
        super().preparar()
        ts = np.arange(0, self.dur + .05, .02)
        def taxa(t):
            if t < self.T_PANE: return 0.0
            return rampa(t, [(self.T_PANE, 0.0), (9.0, 1.0), (39.0, 1.0), (46.0, .35), (self.T_TOCA, .12)]) if t < self.T_TOCA else 0.0
        r = np.array([taxa(u) for u in ts])
        sacc = np.concatenate([[0], np.cumsum(r[:-1] * .02)])
        tot = float(np.interp(self.T_TOCA, ts, sacc))
        self._ts, self._alt = ts, np.maximum(0.0, 300.0 * (1 - sacc / tot))
        v = np.array([rampa(u, [(0, 1.0), (39.0, 1.0), (47.0, .25), (self.T_TOCA, 0.0)]) if u < self.T_TOCA else 0.0
                      for u in ts])
        self._xm = np.concatenate([[0], np.cumsum(v[:-1] * .02)]) * 110
        self.fase = Fase(lambda t: VOLTAS_S * self.rpm(t) / 100.0, self.dur)

    def alt(self, t): return float(np.interp(t, self._ts, self._alt))

    def desenhar(self, tela, t, tg):
        a = self.alt(t)
        xm = float(np.interp(t, self._ts, self._xm))
        sk = 176 - 3 * min(a, 30.0)
        gy = 176 if a < 30 else 176 + 3 * (a - 30)
        self.ceu.fundo(tela, a, t)
        # nuvens que sobem enquanto ele desce
        for hc, esc, sd in ((230.0, 1.1, 2), (130.0, 1.4, 5)):
            yc = sk + (a - hc) * .9
            if -30 < yc < PALCO_H + 30:
                self.ceu.camada(tela, yc, xm * 1.2, esc=esc, densa=False, seed=sd)
        hy = self.ceu.horizonte(a)
        self.campo.desenhar(tela, hy, gy, xm, t, heliponto=None, vento=1.0 if a < 8 else 0.0, vento_x=self.OX)
        motor = t < self.T_PANE
        hx, hy_, oy = self.heli(tela, self.OX, sk, self.K, t, ang=self.ang(t), psi=self.fase(t),
                                giro=self.fase.fn(t), disco=self.disco(t), ar=.9 if t < self.T_TOCA else .2,
                                sentido=self.sentido(t), chao=gy, motor=motor, sombra=a < 30)
        if 16.6 <= t < self.T_TOCA:
            u = ease((t - 16.6) / .6)
            for dx in (-60, 62):
                seta_forca(tela, hx + dx, hy_ + 34, hx + dx, hy_ + 34 - 26 * u, CIANO, esp=3, cab=5)
            if not VERTICAL:
                tela.texto('AR DE BAIXO', hx + 70, hy_ + 22, CIANO, tam=9, contorno=PRETO)
        if self.T_TOCA <= t < self.T_TOCA + 1.4:
            u = (t - self.T_TOCA) / 1.4
            for j in range(10):
                d = (j - 4.5) * 6 * (1 + u * 2)
                tela.disco(self.OX + d, 174 - u * 6 - (j % 3), 2 + u * 3, ACO3 if j % 2 else ACO2)
        if t >= self.T_PANE and t < 10 and int(t * 4) % 2 == 0:
            etiqueta(tela, 'MOTOR PAROU!', (x_corte('autorrotacao') + 40) if VERTICAL else 20, 30 if VERTICAL else 12,
                     VERMELHO, 9 if VERTICAL else 17)
        if VERTICAL:
            hud_vertical(tela, 'autorrotacao', [(f"ROTOR {int(round(self.rpm(t)))}%", VERDE if self.rpm(t) > 94 else AMARELO),
                                                (f"ALTURA {milhar(a)} M", BRANCO)])
            return
        st = [('MOTOR: LIGADO', VERDE)] if motor else [('MOTOR: PAROU', VERMELHO)]
        if t >= 5.8 and t < self.T_TOCA: st.append(('RODA LIVRE: SOLTA', AMARELO))
        if t >= self.T_TOCA: st = [('NO CHÃO', VERDE)]
        dest = ()
        if 3.6 <= t < 16.4 or 43.8 <= t < 54.4: dest = ('col',)
        elif 38.4 <= t < 43.8: dest = ('cic',)
        elif 54.6 <= t < 60.0: dest = ('rpm',)
        painel_voo(tela, self.col(t), self.cic(t), self.rpm(t), a, dest=dest, extra=st)

    def sons(self, fx):
        self.turbina(fx, 0, self.T_PANE + .3, .12)
        fx.put(fx.explosao(1.2), self.t0 + self.T_PANE, .35)
        fx.put(fx.chiado(2.5, 1500, 4000, ataque=.01), self.t0 + self.T_PANE, .1)      # turbina desligando
        for k in range(6):                                                               # alarme de giro baixo
            fx.put(fx.blip(84 if k % 2 == 0 else 79, .2), self.t0 + 3.4 + k * .3, .14)
        fx.put(fx.clique(900, .05), self.t0 + 5.8, .3)
        self.rotor_som(fx, self.fase, 0, self.dur, .22)
        self.vento(fx, 4.0, self.T_TOCA, .12, 200, 1800)
        fx.put(fx.explosao(.7), self.t0 + self.T_TOCA, .45)
        fx.put(fx.clique(600, .06), self.t0 + self.T_TOCA, .4)


# ============================================================ 12 resumo
class Resumo(Cena):
    CARTOES = [(0.4, '1', 'PÁ = ASA', 'QUE GIRA'), (6.6, '2', 'COLETIVO E', 'CÍCLICO'),
               (13.2, '3', 'A CAUDA SEGURA', 'O TORQUE'), (19.8, '4', 'SEM MOTOR:', 'AUTORROTAÇÃO')]

    def preparar(self):
        self.fase = Fase(lambda t: .4, self.dur)
        self.ar = ArRotor(24, seed=9)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        caixas = [(8, 8), (244, 8), (8, 108), (244, 108)]
        ps = self.fase(t)
        for j, ((t0, num, l1, l2), (bx, by)) in enumerate(zip(self.CARTOES, caixas)):
            if t < t0: continue
            u = ease((t - t0) / .4)
            atual = j == max(i for i, c in enumerate(self.CARTOES) if t >= c[0])
            by2 = by + int((1 - u) * 10)
            painel(tela, bx, by2, 228, 94, borda=AMARELO if atual else ACO1)
            tela.texto(num, bx + 8, by2 + 6, AMARELO, tam=26, contorno=PRETO)
            tela.texto(l1, bx + 30, by2 + 6, BRANCO, tam=17, contorno=PRETO)
            tela.texto(l2, bx + 30, by2 + 24, AMARELO if atual else ACO3, tam=17, contorno=PRETO)
            cx, cy = bx + 150, by2 + 64
            if j == 0:
                TOPO.rotor(tela, bx + 60, by2 + 66, .55, 0, ps)
                for q in range(3):
                    x = bx + 140 + q * 22
                    yy = by2 + 50 + ((t * 30 + q * 9) % 30)
                    seta_forca(tela, x, yy, x, yy + 8, CIANO, esp=2, cab=4)
                perfil_icone(tela, bx + 190, by2 + 58, 30, 8, texto=False, ref=False)
            elif j == 1:
                hgt = 6 * math.sin(t * 1.5)
                HELI.desenhar(tela, bx + 64, by2 + 62 - hgt, .5, 0, t, psi=ps * 20, giro=VOLTAS_S, giro_c=40, psi_c=t * 30)
                CAB.desenhar(tela, bx + 168, by2 + 66, 5.5, ps, h=.5 + .4 * math.sin(t * 1.5), f=.08 * math.sin(t * .9),
                             rb=3.6)
            elif j == 2:
                T = TOPO.corpo(tela, bx + 110, by2 + 48, .5, -90, t, sombra=False, giro_c=40, psi_c=t * 30)
                TOPO.rotor(tela, bx + 110, by2 + 48, .5, -90, ps)
                a0 = T(1.0, -61); a1 = T(1.0 + 16, -61)
                seta_forca(tela, *a0, *a1, AMARELO, esp=3, cab=5)
            else:
                yy = by2 + 52 + ((t * 6) % 10)
                HELI.desenhar(tela, bx + 100, yy, .5, -3, t, psi=ps * 6, giro=VOLTAS_S, giro_c=40, motor=False)
                for dx in (-26, 26):
                    seta_forca(tela, bx + 100 + dx, by2 + 88, bx + 100 + dx, by2 + 76, CIANO, esp=2, cab=4)

    def sons(self, fx):
        for k, (t0, *_r) in enumerate(self.CARTOES):
            fx.put(fx.blip(72 + k * 2, .14), self.t0 + t0, .28)


# ============================================================ 13 fim
class Fim(Voo):
    legenda = False
    brilho = 0.0

    def preparar(self):
        super().preparar()
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))
        self.fase = Fase(lambda t: VOLTAS_S, self.dur)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            self.ceu.fundo(tela, 3000, t)
            self.ceu.camada(tela, 190, t * 40, esc=1.2, densa=True, seed=3)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            u = (t - RM.OUTRO_S) / (self.dur - RM.OUTRO_S)
            HELI.desenhar(tela, -50 + u * 580, 140 - u * 40, 1.0, -7, t, psi=self.fase(t), giro=VOLTAS_S,
                          giro_c=40, psi_c=t * 30, disco=3)

    def fim_vinheta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# longo.py chama `pos` (RGB pronto) quando a cena tem esse método: só o Fim usa.
Fim.pos = Fim.fim_vinheta

CENAS = dict(gancho=Gancho, titulo=Titulo, asa=Asa, giro=Giro, prato=Prato, coletivo=Coletivo, pairar=Pairar,
             ciclico=Ciclico, torque=Torque, pedais=Pedais, dois=Dois, autorrotacao=Autorrotacao, resumo=Resumo,
             fim=Fim)


if __name__ == '__main__':
    import ep10_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if len(sys.argv) > 3:
            c = next(c for c in trilha.caps if c['id'] == sys.argv[3])
            fr = [float(x) for x in sys.argv[4:]] or [.1, .3, .5, .7, .9]
            ts = [c['t0'] + c['dur'] * f for f in fr]
        else:
            for c in trilha.caps:
                ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
