#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep12 — Como o alto-falante faz som (PT-BR). Os capítulos.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve, nos mesmos instantes do desenho

Protagonistas: o cone do alto-falante (sempre em movimento, seguindo uma
curva D(t) de deslocamento) e uma molécula de ar (a rosa). O ar é uma onda
longitudinal de verdade: cada molécula é deslocada por D(t - x/c), então a
compressão anda e a molécula só vai e volta. Nos capítulos do bumbo e do
ritmo, o cone lê os números e os eventos de bumbo da própria trilha do
episódio (longo.Trilha -> ritmo_base.Linha), os mesmos que viram som.

    python3 ep12_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep12_motor.py <saida.mp4> ar bumbo         # só esses capítulos (teste)
    python3 ep12_motor.py --folha <saida.png> [ids]    # 2 quadros por capítulo (FR=.3,.8)
"""
import math, os, sys
import numpy as np
import longo as LG
import ep12_desenho as D                      # registra a paleta 'ep12' (antes de qualquer Tela)
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel, texto_marcado,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, VERDE, PRETO, ROSA, ROXO, LATAO, MISTURA, MISTURA2, AGUA0, AGUA1,
                   CHAMA1, BRASA, CERAMICA)
from ep12_desenho import (Corte, Ar, Curva, curva_seno, rotulo, centro_preso, seta, bloco, osc, regua_hz,
                          faixa_hz, x_hz, medidor, falante_frente, apagar_pecas, dec, milhar, sinal, clamp,
                          lerp, KICK16, COBRE2, COBRE3, CONE1, CONE2, CONE3, AR1, AR2, AR3, APE1, APE2,
                          ESP1, MAD0, MAD1, MAD2, PCB0, PCB1, IMA1)
import ritmo_marca as RM
from ep12_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO, MILHOES

SEED, RAIZ = 2612, 47
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
PX0 = 306                     # coluna do painel da direita
SR = LG.SR
C_SOM = 343.0                 # m/s no ar a 20 °C (F2)


def _env_sobe(t, a, d=1.0): return suave((t - a) / d)


class Cena:
    legenda = True
    brilho = None
    XV = 98                    # centro do recorte vertical (x do corte + 90)

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.L = trilha.L
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def fundo(self, tela, t):
        D.grade_fundo(tela, W)
        if not VERTICAL:
            tela.ret(298, 0, 1, PALCO_H, TRACO)
            tela.ret(299, 0, W - 299, PALCO_H, FUNDO)

    def ptxt(self, tela, txt, y, cor=ACO3, tam=9, x=PX0):
        if not VERTICAL: tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)

    def ptit(self, tela, txt, y=6, cor=ACO3):
        if VERTICAL: return
        tela.texto(txt, PX0, y, cor, tam=9, contorno=PRETO)
        tela.ret(PX0, y + 10, 160, 1, FUNDO3)

    def vtxt(self, tela, txt, cor=BRANCO, y=5, tam=17):
        """Leitura curta no topo do recorte vertical (só nos Shorts)."""
        if VERTICAL: centro_preso(tela, txt, self.XV, y, cor, tam=tam, xmin=self.XV - 88, xmax=self.XV + 88)

    def tom(self, fx, f, t, dur, ganho, pan=0.0, curva=None):
        n = int(dur * SR); tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * f * tt) + .18 * np.sin(4 * np.pi * f * tt)
        k = int(.03 * SR)
        e = np.ones(n); e[:k] = np.linspace(0, 1, k); e[-k:] = np.linspace(1, 0, k)
        if curva is not None: e = e * curva(tt)
        fx.put((y * e * .6).astype(np.float32), self.t0 + t, ganho, pan)

    def faixa_musica(self, tela, tg, gx, gy, gw, gh):
        """A trilha de verdade em volta do agora (passado claro, futuro apagado),
        com uma marca amarela em cada bumbo."""
        if VERTICAL: return
        a = self.T.audio
        painel(tela, gx - 2, gy - 2, gw + 4, gh + 4)
        n = int(tg * SR)
        meio = gw // 2
        passo = 160
        for c in range(gw):
            i0 = n + (c - meio) * passo
            if i0 < 0 or i0 + passo >= len(a): continue
            seg = a[i0:i0 + passo, 0]
            hi, lo = float(seg.max()), float(seg.min())
            tela.ret(gx + c, gy + gh / 2 - hi * gh * .9, 1, max(1, (hi - lo) * gh * .9), CIANO if c < meio else ACO1)
        for e in self.L.entre('kick', tg - meio * passo / SR, tg + meio * passo / SR):
            xk = gx + meio + (e['t'] - tg) * SR / passo
            tela.ret(xk, gy - 1, 1, 3, AMARELO)
        tela.ret(gx + meio, gy - 3, 1, gh + 6, BRANCO)

    def rastro(self, tela, x, y, w, h, fn, t, janela=4.0, cor=ROSA, ymax=6.0, titulo=None):
        if VERTICAL: return
        ts = np.linspace(t - janela, t, 80)
        vals = fn(ts)
        osc(tela, x, y, w, h, vals, cor=cor, ymax=ymax)
        tela.disco(x + w - 1, y + h / 2 - clamp(float(vals[-1]) / ymax, -1, 1) * (h / 2 - 1), 1.6, BRANCO)


def kicks_do_capitulo(cena):
    return [(e['t'] - cena.t0, e.get('vel', 1.0)) for e in cena.L.entre('kick', cena.t0 - 1, cena.t0 + cena.dur + .5)]


def curva_kicks(ks, A=6.0, t1=60.0):
    """Deslocamento do cone: um empurrão rápido para fora em cada bumbo e a
    volta pela aranha, com um pouco de rebote."""
    g = np.arange(-6.0, t1, 1 / 600)
    v = np.zeros_like(g)
    for tk, vel in ks:
        u = g - tk
        m = u >= 0
        uu = u[m]
        v[m] += A * vel * (1 - np.exp(-uu / .012)) * np.exp(-uu / .11) * (1 - .3 * np.sin(np.clip(uu, 0, .35) * 14))
    return Curva.de_tabela(g, v)


# ============================================================ 0 gancho
class Gancho(Cena):
    def preparar(self):
        self.ks = kicks_do_capitulo(self)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cx, cy, R = 150, 100, 64
        # ondas saindo do cone em cada bumbo
        for tk, vel in self.ks:
            a = t - tk
            if 0 <= a < 1.3:
                r = R + 10 + a * 120
                cor = AR3 if a < .25 else (AR2 if a < .7 else AR1)
                tela.anel(cx, cy, r, PRETO, esp=1.6)
                tela.anel(cx, cy, r, cor, esp=.7)
        d = 6 * self.L.env('kick', tg, .09)
        falante_frente(tela, cx, cy, R, d, t)
        if not VERTICAL:
            tela.ret(298, 0, 1, PALCO_H, TRACO); tela.ret(299, 0, W - 299, PALCO_H, FUNDO)
        # painel: os números da música agora
        n = int(tg * SR)
        self.ptit(tela, "A MÚSICA AGORA, EM NÚMEROS")
        self.ptxt(tela, f"AMOSTRA Nº {milhar(n)}", 20, BRANCO, 9)
        if not VERTICAL:
            a = self.T.audio
            for j in range(9):
                i = n - 8 + j
                v = int(round(float(a[max(0, i), 0]) * 32767))
                cor = AMARELO if j == 8 else (ACO3 if j > 4 else ACO1)
                tela.texto(f"{milhar(i)}", PX0, 34 + j * 12, ACO1, tam=9, contorno=PRETO)
                tela.texto(sinal(v), PX0 + 100, 34 + j * 12, cor, tam=9, contorno=PRETO)
            seg = a[max(0, n - 1920):n + 1, 0] if n > 0 else np.zeros(2)
            if len(seg) > 10:
                vals = seg[::12]
                osc(tela, PX0, 150, 160, 36, vals * 1.6, cor=CIANO)
            self.ptxt(tela, "OS ÚLTIMOS 40 MS", 192, ACO2)
        else:
            self.vtxt(tela, f"Nº {milhar(n)}", AMARELO)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        D.grade_fundo(tela, W)
        for k, (x, y, R) in enumerate(((44, 176, 26), (436, 40, 22), (408, 178, 14))):
            d = 3 * math.sin(t * 5 + k)
            falante_frente(tela, x, y, R, d, t)
        n = int(t / .045)
        for j, linha in enumerate(("COMO O ALTO-FALANTE", "FAZ SOM")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 19)]
            tela.texto(vis, W // 2 - larg // 2, 64 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.3:
            tela.texto("DE NÚMEROS A AR EM MOVIMENTO", W // 2, 140, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k in range(16):
                b = (int(t * 8) + k * 5) % 3 != 0
                x = W // 2 - 88 + k * 11
                tela.ret(x, 166, 9, 11, AMARELO if b else FUNDO3)
                tela.texto('1' if b else '0', x + 2, 168, PRETO if b else ACO2, tam=9)


# ============================================================ cenas do ar (base)
class CenaAr(Cena):
    """Alto-falante em corte à esquerda, ar à direita."""
    FAL = (60, 100, 1.0)
    AR = (96, 296, 28, 172)
    C = 55.0
    ESCALA = .2

    def preparar(self):
        cx, cy, s = self.FAL
        self.F = Corte(cx, cy, s)
        x0, x1, y0, y1 = self.AR
        self.ar = Ar(x0, x1, y0, y1, passo=6, seed=12, xa=self.F.face_x() + 2)
        self.D = Curva(self.d, -6, self.dur + 2)
        self.extra()

    def extra(self): pass
    def d(self, t): return 0.0

    def palco_ar(self, tela, t, vacuo=0.0, prota=False, corrente=0.0, campo=False):
        dd = float(self.D(t))
        cols, lev = self.ar.desenhar(tela, t, self.D, self.C, escala=self.ESCALA, vacuo=vacuo, prota=prota)
        self.F.desenhar(tela, dd, corrente=corrente, t=t, campo=campo)
        return cols, lev, dd


# ============================================================ 2 o ar
class ArCena(CenaAr):
    XV = 98
    C = 50.0
    ESCALA = .32

    def d(self, t):
        if t < 2.5: return 0.0
        return 7.0 * math.sin(2 * math.pi * .45 * (t - 2.5)) * suave((t - 2.5) / .8)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        vac = suave((t - 30.2) / 3.0)
        cols, lev, dd = self.palco_ar(tela, t, vacuo=vac, prota=t >= 21.6)
        x0, x1 = self.AR[0], self.AR[1]
        # rótulos que seguem a compressão e a rarefação
        if 7.4 <= t < 14.6 or 14.8 <= t < 22.0:
            alvo = np.argmax(lev) if t < 14.6 else np.argmin(lev)
            # a banda mais perto do cone que já existe
            m = (lev > .7) if t < 14.6 else (lev < -.7)
            idx = np.nonzero(m)[0]
            if len(idx):
                # primeiro grupo contíguo
                fim = idx[0]
                while fim + 1 < len(lev) and m[fim + 1]: fim += 1
                xc = x0 + (idx[0] + fim) / 2
                txt, cor = ("AR APERTADO", LARANJA) if t < 14.6 else ("AR ESPALHADO", MISTURA2)
                centro_preso(tela, txt, xc, 14, cor, xmin=x0, xmax=x1)
                seta(tela, xc, 23, xc, 30, cor, esp=1, ponta=3)
        if 1.0 < t < 30:
            seta(tela, 200, 186, 250, 186, ACO3, esp=1, ponta=4)
            tela.texto("ONDA", 168, 182, ACO3, tam=9, contorno=PRETO)
        if t >= 29.8:
            u = suave((t - 29.8) / .6)
            if u > .5:
                centro_preso(tela, "VÁCUO: NADA PARA EMPURRAR", 196, 182, VERMELHO, xmin=100, xmax=296)
        # painel
        self.ptit(tela, "PRESSÃO DO AR NO CAMINHO")
        if not VERTICAL:
            vals = lev[::2]
            osc(tela, PX0, 24, 160, 50, vals, cor=LARANJA, ymax=1.05)
            tela.texto("ALTA", PX0 + 2, 26, LARANJA, tam=9, contorno=PRETO)
            tela.texto("BAIXA", PX0 + 2, 64, MISTURA2, tam=9, contorno=PRETO)
            self.ptxt(tela, "CONE        LONGE DO CONE", 80, ACO2)
            if t >= 21.6:
                self.ptit(tela, "A MOLÉCULA ROSA", 98, ROSA)
                ux = float(self.ar.u(self.ar.xr[self.ar.prota], t, self.D, self.C))
                if vac > .5:
                    self.ptxt(tela, "(NÃO HÁ MAIS AR)", 112, VERMELHO, 9)
                else:
                    self.ptxt(tela, f"FORA DO LUGAR: {'+' if ux >= 0 else '-'}{dec(abs(ux))} PX", 112, BRANCO, 9)
                fn = lambda ts: self.ar.u(self.ar.xr[self.ar.prota], ts, self.D, self.C) * (1 - vac)
                self.rastro(tela, PX0, 126, 160, 44, fn, t, janela=5.0, ymax=8.0)
                self.ptxt(tela, "VAI E VOLTA, NÃO VIAJA", 176, ACO3)
            else:
                self.ptxt(tela, "CONE", 100, ACO3)
                self.ptxt(tela, f"POSIÇÃO: {'+' if dd >= 0 else '-'}{dec(abs(dd))} PX", 112, BRANCO)
                self.rastro(tela, PX0, 126, 160, 44, self.D, t, janela=5.0, cor=CONE3, ymax=8.0)
        if VERTICAL and t >= 21.6:
            self.vtxt(tela, "MOLÉCULA ROSA", ROSA, tam=9, y=8)


# ============================================================ 3 velocidade
class Velocidade(Cena):
    XA, XB = 34, 290

    def preparar(self):
        self.Fa = Corte(17, 62, .32)
        self.Fw = Corte(17, 128, .32)
        self.ar = Ar(36, 140, 164, 202, passo=7, seed=33, xa=36)
        self.D = Curva(lambda t: 3.5 * math.sin(2 * math.pi * .8 * t), -6, self.dur + 2)

    def escala(self, t):
        """metros por pixel: 0..400 m no começo, 0..1.600 m quando a água entra."""
        return lerp(400.0, 1600.0, suave((t - 14.6) / 1.4)) / (self.XB - self.XA)

    def corrida(self, t):
        if t < 15.0: return clamp((t - 1.2) / 9.0)            # 1 s de som em 9 s de vídeo
        return clamp((t - 16.6) / 9.0)

    def pista(self, tela, y, m, mpp, agua, t, nome):
        XA, XB = self.XA, self.XB
        h = 22
        painel(tela, XA - 2, y - h // 2 - 2, XB - XA + 4, h + 4)
        if agua:
            dither(tela, XA, y - h // 2, XB - XA, h, AGUA0, D.AR0)
            for k in range(14):
                bx = XA + (k * 37 + int(t * 7)) % (XB - XA); by = y + h // 2 - 3 - ((k * 13 + int(t * 9)) % (h - 4))
                tela.px(bx, by, AGUA1)
        else:
            for k in range(70):
                bx = XA + (k * 23) % (XB - XA); by = y - h // 2 + 2 + (k * 7) % (h - 4)
                tela.px(bx + math.sin(t * 3 + k) * .6, by, AR1)
        xf = XA + m / mpp
        if m > 0:
            # a frente da onda e o ar apertado atrás dela
            for k in range(0, 40):
                xx = xf - k
                if xx < XA: break
                cor = APE2 if k < 3 else (APE1 if k < 10 else (D.APE0 if k < 18 else None))
                if cor is not None and xx <= XB:
                    tela.ret(xx, y - h // 2, 1, h, cor)
            if xf <= XB:
                tela.ret(xf, y - h // 2 - 3, 1, h + 6, BRANCO)
                if xf > XA + 90:
                    tela.texto("FRENTE DA ONDA", int(xf - tela.largura_texto("FRENTE DA ONDA", 9) - 3), y - h // 2 - 12,
                               BRANCO, tam=9, contorno=PRETO)
        # régua
        passo = 50 if mpp * (XB - XA) <= 500 else 200
        rot = 100 if passo == 50 else 400
        k = 0
        while k * passo / mpp <= XB - XA + .5:
            xx = XA + k * passo / mpp
            tela.ret(xx, y + h // 2 + 2, 1, 3 if (k * passo) % rot else 5, ACO2)
            if (k * passo) % rot == 0 and k > 0:
                txt = milhar(k * passo)
                tw = tela.largura_texto(txt, 9)
                tela.texto(txt, int(min(xx - tw / 2, 296 - tw)), y + h // 2 + 8, ACO2, tam=9, contorno=PRETO)
            k += 1
        tela.texto(nome, XA, y - h // 2 - 12, AGUA1 if agua else AR3, tam=9, contorno=PRETO)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        mpp = self.escala(t)
        u = self.corrida(t)
        agua = t >= 14.8
        ya = 62 if True else 0
        self.pista(tela, ya, C_SOM * u, mpp, False, t, "AR A 20 °C")
        d = 2.5 * math.sin(t * 9) if (0 < u < 1 or (t > 1.2 and t < 1.6)) else 0
        self.Fa.desenhar(tela, d * .3, t=t, pecas=('ima', 'cone', 'borda', 'carcaca'))
        if agua:
            self.pista(tela, 128, 1481.0 * u, mpp, True, t, "ÁGUA A 20 °C")
            self.Fw.desenhar(tela, d * .3, t=t, pecas=('ima', 'cone', 'borda', 'carcaca'))
        # marcas de chegada
        if u >= 1:
            xm = self.XA + C_SOM / mpp
            centro_preso(tela, "343 M", xm, 34, AMARELO, xmin=4, xmax=296)
            if agua:
                xw = self.XA + 1481 / mpp
                centro_preso(tela, "1.481 M", xw, 100, CIANO, xmin=4, xmax=296)
        # lupa na molécula rosa
        if t >= 21.8:
            painel(tela, 30, 160, 114, 44, borda=ROSA)
            self.ar.desenhar(tela, t, self.D, 50.0, escala=.4, prota=True, bandas=False)
            tela.texto("PERTO DO CONE:", 150, 170, ROSA, tam=9, contorno=PRETO)
            tela.texto("NO MESMO LUGAR", 150, 182, ROSA, tam=9, contorno=PRETO)
        # painel
        tsim = u * 1.0
        self.ptit(tela, "A FRENTE DA ONDA")
        self.ptxt(tela, "TEMPO", 22, ACO3)
        self.ptxt(tela, f"{dec(tsim, 2)} S", 32, BRANCO, 17)
        self.ptxt(tela, "NO AR", 62, AR3)
        self.ptxt(tela, f"{milhar(C_SOM * u)} M", 72, AMARELO, 17)
        if agua:
            self.ptxt(tela, "NA ÁGUA", 102, AGUA1)
            self.ptxt(tela, f"{milhar(1481 * u)} M", 112, CIANO, 17)
        self.ptxt(tela, "CÂMERA LENTA: 1 S", 150, ACO2)
        self.ptxt(tela, "DE SOM EM 9 S DE VÍDEO", 161, ACO2)


# ============================================================ 4 frequência
class Frequencia(CenaAr):
    FAL = (48, 98, .85)
    AR = (80, 296, 30, 166)
    C = 80.0
    ESCALA = .3
    XV = 96
    TRECHOS = [(0.0, 110), (7.4, 220), (14.6, 110), (18.0, 880), (21.8, 440)]

    def freq(self, t):
        f = self.TRECHOS[0][1]
        for a, ff in self.TRECHOS:
            if t >= a: f = ff
        return f

    def preparar(self):
        cx, cy, s = self.FAL
        self.F = Corte(cx, cy, s)
        x0, x1, y0, y1 = self.AR
        self.ar = Ar(x0, x1, y0, y1, passo=6, seed=14, xa=self.F.face_x() + 2)
        amp = lambda f: {110: 8.0, 220: 6.0, 440: 3.6, 880: 2.0}[f]
        self.D = curva_seno(lambda t: (self.freq(t) / 220.0, amp(self.freq(t)) * suave((t + .5) / 1.0)), -6, self.dur + 2)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cols, lev, dd = self.palco_ar(tela, t)
        f = self.freq(t)
        if 14.6 <= t < 21.6:
            txt, cor = ("GRAVE", MISTURA2) if f < 220 else ("AGUDO", LARANJA)
            centro_preso(tela, txt, 188, 12, cor, tam=17, xmin=82, xmax=296)
        if not VERTICAL:
            tela.texto("CÂMERA LENTA", 82, 176, ACO2, tam=9, contorno=PRETO)
        self.vtxt(tela, f"{milhar(f)} HZ", AMARELO, y=4)
        # painel
        self.ptit(tela, "FREQUÊNCIA")
        self.ptxt(tela, f"{milhar(f)} HZ", 20, AMARELO, 26)
        self.ptxt(tela, f"{milhar(f)} VAIVÉNS POR SEGUNDO", 48, BRANCO)
        if not VERTICAL:
            yr = 88
            if t >= 21.8:
                fim = 20000.0
                if t >= 29.0:
                    fim = 20000.0 * (1 - .45 * suave((t - 29.4) / 2.5))
                faixa_hz(tela, PX0, yr - 6, 160, 20, fim, VERDE, alto=3)
                tela.texto("OUVIDO HUMANO", PX0, yr - 19, VERDE, tam=9, contorno=PRETO)
                if t >= 29.4:
                    xx = x_hz(PX0, 160, fim)
                    seta(tela, xx + 14, yr - 13, xx + 2, yr - 13, VERMELHO, esp=1, ponta=3)
            regua_hz(tela, PX0, yr, 160)
            xm = x_hz(PX0, 160, f)
            poligono(tela, [(xm - 4, yr - 6), (xm + 4, yr - 6), (xm, yr - 1)], PRETO)
            poligono(tela, [(xm - 3, yr - 5), (xm + 3, yr - 5), (xm, yr - 2)], AMARELO)
            tela.texto("GRAVE", PX0, yr + 20, MISTURA2, tam=9, contorno=PRETO)
            tela.texto("AGUDO", PX0 + 160 - tela.largura_texto("AGUDO", 9), yr + 20, LARANJA, tam=9, contorno=PRETO)
            lam = C_SOM / f
            self.ptxt(tela, "TAMANHO DE 1 ONDA NO AR", 124, ACO3)
            self.ptxt(tela, (f"{dec(lam, 2)} M" if lam >= 1 else f"{dec(lam * 100, 0)} CM"), 135, BRANCO, 17)
            self.ptxt(tela, "343 / FREQUÊNCIA", 154, ACO2)
            self.rastro(tela, PX0, 168, 160, 30, self.D, t, janela=2.0, cor=CONE3, ymax=8.5)

    def sons(self, fx):
        ts = [a for a, _ in self.TRECHOS] + [self.dur]
        for (a, f), b in zip(self.TRECHOS, ts[1:]):
            g = .12 if f < 400 else .07
            self.tom(fx, f, a + .05, b - a - .1, g)


# ============================================================ 5 amplitude
class Amplitude(CenaAr):
    FAL = (48, 98, .85)
    AR = (80, 296, 30, 166)
    C = 80.0
    ESCALA = .5

    def amp(self, t):
        if t < 7.8: return 1.8
        if t < 15.2: return lerp(1.8, 7.0, suave((t - 7.8) / 5.0))
        return 1.8 + 5.2 * (.5 + .5 * math.cos(2 * math.pi * (t - 15.2) / 5.0))

    def preparar(self):
        cx, cy, s = self.FAL
        self.F = Corte(cx, cy, s)
        x0, x1, y0, y1 = self.AR
        self.ar = Ar(x0, x1, y0, y1, passo=6, seed=15, xa=self.F.face_x() + 2)
        self.D = curva_seno(lambda t: (1.0, self.amp(t)), -6, self.dur + 2)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        cols, lev, dd = self.palco_ar(tela, t)
        a = self.amp(t)
        # régua do vaivém do cone
        fx_ = self.F.face_x() - 6
        tela.ret(fx_ - 10, 170, 22, 1, ACO2)
        tela.ret(fx_ + 1 - a, 167, 1, 7, AMARELO); tela.ret(fx_ + 1 + a, 167, 1, 7, AMARELO)
        tela.texto("VAIVÉM", 12, 178, AMARELO, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "AMPLITUDE")
        if not VERTICAL:
            medidor(tela, PX0, 22, 160, 12, a / 7.2, AMARELO)
            self.ptxt(tela, "O QUANTO O CONE ANDA", 40, ACO3)
            self.ptit(tela, "VOLUME", 62)
            # alto-falante pequeno com barras de volume
            for k in range(8):
                on = k < int(round(a / 7.0 * 8))
                hh = 6 + k * 3
                tela.ret(PX0 + 30 + k * 12, 108 - hh, 9, hh, (LARANJA if k > 5 else AMARELO) if on else FUNDO2)
            falante_frente(tela, PX0 + 12, 98, 9, float(self.D(t)) * .6, t)
            self.ptxt(tela, "FREQUÊNCIA: 220 HZ", 122, BRANCO)
            self.ptxt(tela, "(A MESMA O TEMPO TODO)", 133, ACO2)
            self.rastro(tela, PX0, 152, 160, 40, self.D, t, janela=3.0, cor=CONE3, ymax=7.5)

    def sons(self, fx):
        dur = self.dur - .2
        amp = np.vectorize(self.amp)
        self.tom(fx, 220, .1, dur, .13, curva=lambda tt: (amp(tt + .1) / 7.0) ** 1.3)


# ============================================================ 6 amostras
class Amostras(Cena):
    GX, GY, GW, GH = 14, 24, 276, 120
    XV = 130

    def onda(self, x):
        x = np.asarray(x, float)
        return .55 * np.sin(2 * np.pi * x / 130 + .3) + .25 * np.sin(2 * np.pi * x / 47 + 1.1) + .12 * np.sin(2 * np.pi * x / 21 + 2)

    def espaco(self, t):
        if t < 15.2: return 18
        if t < 22.6: return 9
        return 8

    def nyq(self, t): return t >= 30.0

    def amostrar(self, t):
        """(posições x das amostras já medidas, valores) e a posição da sonda."""
        if t < 7.8: return [], [], None
        if self.nyq(t):
            e = 12; vel = 80.0; t_ini = 30.0
        else:
            e = self.espaco(t); vel = 40.0 if t < 15.2 else 120.0
            t_ini = 7.8 if t < 15.2 else (15.2 if t < 22.6 else 22.6)
        sonda = self.GX + ((t - t_ini) * vel) % (self.GW + 30)
        n = int(min(sonda, self.GW) // e) + 1
        xs = [self.GX + k * e for k in range(n) if self.GX + k * e <= sonda]
        return xs, xs, sonda

    def valor(self, x, t):
        if self.nyq(t):
            k = round((x - self.GX) / 12)
            return .8 * (1 if k % 2 == 0 else -1)
        return float(self.onda(x - self.GX))

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        GX, GY, GW, GH = self.GX, self.GY, self.GW, self.GH
        cy = GY + GH / 2
        painel(tela, GX - 4, GY - 4, GW + 8, GH + 8)
        for gx in range(GX, GX + GW, 12):
            for gy in range(GY, GY + GH, 4): tela.px(gx, gy, FUNDO2)
        tela.ret(GX, cy, GW, 1, FUNDO3)
        xs = np.arange(GX, GX + GW)
        if self.nyq(t):
            ys = cy - .8 * np.cos(np.pi * (xs - GX) / 12) * (GH / 2 - 4)
            cor_onda = LARANJA
        else:
            ys = cy - self.onda(xs - GX) * (GH / 2 - 4)
            cor_onda = CIANO
        for i in range(len(xs) - 1):
            tela.linha(xs[i], ys[i] + 1, xs[i + 1], ys[i + 1] + 1, PRETO)
            tela.linha(xs[i], ys[i], xs[i + 1], ys[i + 1], cor_onda)
        if t < 7.4:
            for k in range(10):
                fx_ = GX + 20 + k * 26; fy = GY + 10 + ((k * 37 + int(t * 20)) % (GH - 20))
                tela.texto(str((k * 7 + int(t * 3)) % 10), fx_, fy, FUNDO3, tam=9)
        pos, _, sonda = self.amostrar(t)
        e = 12 if self.nyq(t) else self.espaco(t)
        vals = []
        for x in pos:
            v = self.valor(x, t)
            vals.append(v)
            yy = cy - v * (GH / 2 - 4)
            tela.ret(x, min(yy, cy), 1, abs(yy - cy) + 1, AMARELO)
            tela.disco(x, yy, 2.2 if e >= 9 else 1.6, PRETO)
            tela.disco(x, yy, 1.5 if e >= 9 else 1.0, AMARELO)
        if sonda is not None and sonda <= GX + GW:
            tela.ret(sonda, GY - 2, 1, GH + 4, BRANCO)
            poligono(tela, [(sonda - 4, GY - 8), (sonda + 4, GY - 8), (sonda, GY - 2)], BRANCO)
        if pos and e >= 9 and not self.nyq(t):
            # o número da última amostra
            x = pos[-1]; v = vals[-1]
            n16 = int(round(v * 32767 * .9))
            yy = cy - v * (GH / 2 - 4)
            centro_preso(tela, sinal(n16), x, yy - 14 if v >= 0 else yy + 6, AMARELO, xmin=GX, xmax=GX + GW)
        if self.nyq(t) and t >= 31.0:
            centro_preso(tela, "2 AMOSTRAS POR VAIVÉM", 150, GY + GH + 10, LARANJA, xmin=10, xmax=296)
        elif not VERTICAL:
            tela.texto("TEMPO", GX + GW - tela.largura_texto("TEMPO", 9), GY + GH + 8, ACO2, tam=9, contorno=PRETO)
            if t >= 7.8:
                tela.texto("AMPLIADO MUITAS VEZES", GX, GY + GH + 8, ACO2, tam=9, contorno=PRETO)
        # contador
        self.vtxt(tela, f"AMOSTRA Nº {len(pos)}" if pos else "UMA ONDA", AMARELO, y=4, tam=9)
        # painel
        self.ptit(tela, "AMOSTRAS")
        if t < 15.2:
            self.ptxt(tela, f"MEDIDAS: {len(pos)}", 20, BRANCO, 17)
        else:
            taxa = 44100 if t < 22.6 or self.nyq(t) else 48000
            self.ptxt(tela, f"{milhar(taxa)}", 20, AMARELO, 26)
            self.ptxt(tela, "AMOSTRAS POR SEGUNDO", 48, BRANCO)
            self.ptxt(tela, "1 A CADA " + ("0,0227 MS" if taxa == 44100 else "0,0208 MS"), 60, ACO3)
        if not VERTICAL and pos and not self.nyq(t):
            self.ptit(tela, "OS NÚMEROS GUARDADOS", 78)
            for j, k in enumerate(range(max(0, len(pos) - 7), len(pos))):
                n16 = int(round(vals[k] * 32767 * .9))
                y = 94 + j * 12
                cor = AMARELO if k == len(pos) - 1 else ACO3
                tela.texto(f"Nº {k + 1}", PX0, y, ACO1, tam=9, contorno=PRETO)
                tela.texto(sinal(n16), PX0 + 60, y, cor, tam=9, contorno=PRETO)
        if self.nyq(t) and not VERTICAL:
            self.ptit(tela, "O LIMITE", 78)
            self.ptxt(tela, "44.100 / 2 =", 94, ACO3)
            self.ptxt(tela, "22.050 HZ", 106, LARANJA, 17)
            self.ptxt(tela, "OUVIMOS ATÉ UNS", 134, ACO3)
            self.ptxt(tela, "20.000 HZ", 146, VERDE, 17)

    def sons(self, fx):
        ult = -1
        for i in range(int(self.dur * 30)):
            t = i / 30
            pos, _, _ = self.amostrar(t)
            e = 12 if self.nyq(t) else self.espaco(t)
            n = len(pos)
            if n != ult and n > 0 and ult >= 0 and n > ult and e >= 9:
                fx.put(fx.clique(5000, .012), self.t0 + t, .10, -.2 + .4 * ((pos[-1] - 14) / 276))
            ult = n


# ============================================================ 7 bits
class Bits(Cena):
    IDX = [130, 260, 410, 700, 1050, 1500, 2100, 2900, 3700, 5000, 6400, 8000, 9500, 11000, 12500, 14000]

    def valor(self, t):
        k = int(max(0, t - .5) // 1.6)
        i = self.IDX[k % len(self.IDX)]
        return i, int(KICK16[i])

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        i, v = self.valor(t)
        u = (max(0, t - .5) % 1.6) / .35            # os bits viram da direita para a esquerda
        bits = v & 0xFFFF
        _, vant = self.valor(t - 1.6) if t > 2.1 else (0, 0)
        bant = vant & 0xFFFF
        x0 = 14
        tela.texto("UM NÚMERO DO BUMBO DESTE VÍDEO: AMOSTRA Nº " + milhar(i), x0, 10, ACO3, tam=9, contorno=PRETO)
        for k in range(16):
            pos = 15 - k                           # bit mais à esquerda = 15 (sinal)
            vira = k / 16 < 1 - min(1, u)
            b = ((bant if vira else bits) >> pos) & 1
            x = x0 + k * 17
            cor = AMARELO if b else FUNDO2
            tela.ret(x - 1, 26, 17, 22, PRETO)
            tela.ret(x, 27, 15, 20, cor)
            tela.ret(x, 27, 15, 1, BRANCO if b else FUNDO3)
            tela.texto(str(b), x + 4, 31, PRETO if b else ACO2, tam=17)
        tela.texto("SINAL", x0, 52, ACO2, tam=9, contorno=PRETO)
        tela.texto("16 BITS", x0 + 16 * 17 - tela.largura_texto("16 BITS", 9), 52, ACO2, tam=9, contorno=PRETO)
        centro_preso(tela, "= " + sinal(v), 150, 64, BRANCO, tam=26, xmin=10, xmax=296)
        if t < 7.6:
            gx, gy, gw, gh = 20, 100, 264, 80
            N = 14400
            painel(tela, gx - 3, gy - 3, gw + 6, gh + 6)
            tela.ret(gx, gy + gh // 2, gw, 1, FUNDO3)
            for c in range(gw):
                seg = KICK16[c * N // gw:(c + 1) * N // gw]
                hi, lo = int(seg.max()), int(seg.min())
                ya = gy + gh / 2 - hi / 32767 * (gh / 2 - 2); yb = gy + gh / 2 - lo / 32767 * (gh / 2 - 2)
                tela.ret(gx + c, ya, 1, max(1, yb - ya + 1), ACO1)
            xm = gx + i / N * gw
            ym = gy + gh / 2 - v / 32767 * (gh / 2 - 2)
            tela.ret(xm, gy, 1, gh, AMARELO)
            tela.disco(xm, ym, 3, PRETO); tela.disco(xm, ym, 2, AMARELO)
            tela.texto("O BUMBO (0,3 S)", gx, gy + gh + 6, ACO2, tam=9, contorno=PRETO)
        if 7.6 <= t < 15.2:
            # a régua dos 65.536 degraus
            y = 120
            xa, xb = 20, 284
            tela.ret(xa - 1, y - 1, xb - xa + 2, 8, PRETO)
            dither(tela, xa, y, xb - xa, 6, FUNDO3, TRACO)
            tela.ret((xa + xb) // 2, y - 3, 1, 12, ACO3)
            xm = xa + (v + 32768) / 65535 * (xb - xa)
            poligono(tela, [(xm - 5, y - 8), (xm + 5, y - 8), (xm, y - 1)], AMARELO)
            tela.texto("-32.768", xa, y + 11, MISTURA2, tam=9, contorno=PRETO)
            tela.texto("0", (xa + xb) // 2 - 2, y + 11, ACO3, tam=9, contorno=PRETO)
            tela.texto("+32.767", xb - tela.largura_texto("+32.767", 9), y + 11, LARANJA, tam=9, contorno=PRETO)
            # lupa: degraus vizinhos
            lx, ly = int(min(max(xm - 60, 14), 166)), 140
            painel(tela, lx, ly, 120, 46, borda=AMARELO)
            for k in range(-2, 3):
                bx = lx + 8 + (k + 2) * 22
                hh = 10 + (k + 2) * 5
                tela.ret(bx, ly + 40 - hh, 22, hh, AMARELO if k == 0 else FUNDO3)
                tela.ret(bx, ly + 40 - hh, 22, 1, BRANCO if k == 0 else ACO1)
                if k in (-1, 0, 1):
                    tt = milhar(v + k) if v + k < 0 else '+' + milhar(v + k)
                    tela.texto(tt[-4:], bx + 1, ly + 3, BRANCO if k == 0 else ACO2, tam=9, contorno=PRETO)
            tela.texto("DEGRAUS", lx + 2, ly + 48, AMARELO, tam=9, contorno=PRETO)
        if t >= 15.2:
            # dois canais: números passando
            for c, (nome, xc, off) in enumerate((("ESQUERDO", 30, 0), ("DIREITO", 166, 37))):
                painel(tela, xc - 4, 98, 120, 98)
                tela.texto(nome, xc, 102, CIANO, tam=9, contorno=PRETO)
                base = int((t - 15.2) * 44.1 * 3) + off
                for j in range(6):
                    n = base + j
                    val = int(KICK16[(n * 17) % 14000]) if c == 0 else int(KICK16[(n * 17 + 300) % 14000] * .8)
                    tela.texto(sinal(val), xc, 116 + j * 12, AMARELO if j == 5 else ACO3, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "16 BITS")
        self.ptxt(tela, "65.536", 20, AMARELO, 26)
        self.ptxt(tela, "VALORES POSSÍVEIS", 48, BRANCO)
        self.ptxt(tela, "(2 X 2 X 2... 16 VEZES)", 59, ACO2)
        self.ptxt(tela, "MENOR: -32.768", 78, MISTURA2)
        self.ptxt(tela, "MAIOR: +32.767", 90, LARANJA)
        if t >= 15.4:
            self.ptit(tela, "NO CD, POR SEGUNDO", 112)
            self.ptxt(tela, "2 CANAIS X 44.100", 128, ACO3)
            self.ptxt(tela, "= 88.200", 140, AMARELO, 17)

    def sons(self, fx):
        for k in range(int((self.dur - .5) // 1.6) + 1):
            fx.put(fx.blip(76 + (k % 4) * 2, .06), self.t0 + .5 + k * 1.6, .08)


# ============================================================ 8 o bumbo em números
class Bumbo(Cena):
    GX, GY, GW, GH = 74, 22, 216, 92
    XV = 90
    LENTO0 = 22.6
    VEL = 24.0                     # amostras por segundo de vídeo na câmera lenta

    def preparar(self):
        self.F = Corte(34, 96, .62)
        self.ks = kicks_do_capitulo(self)
        self.ar = Ar(56, 72, 50, 142, passo=6, seed=8, xa=55)

    def n_atual(self, t):
        """Qual amostra do bumbo está 'tocando' agora (ou -1)."""
        if t >= self.LENTO0:
            return int((t - self.LENTO0) * self.VEL)
        ult = None
        for tk, v in self.ks:
            if tk <= t: ult = (tk, v)
        if ult is None: return -1
        n = int((t - ult[0]) * 48000)
        return n if n < len(KICK16) else -1

    def d_cone(self, t):
        n = self.n_atual(t)
        if n < 0 or n >= len(KICK16): return 0.0
        return float(KICK16[n]) / 32767 * 6

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        GX, GY, GW, GH = self.GX, self.GY, self.GW, self.GH
        cy = GY + GH / 2
        n = self.n_atual(t)
        lento = t >= self.LENTO0
        painel(tela, GX - 4, GY - 4, GW + 8, GH + 8)
        tela.ret(GX, cy, GW, 1, FUNDO3)
        if not lento:
            N = 14400                                         # 0,3 s de bumbo
            col = np.arange(GW)
            a0 = (col * N) // GW; a1 = ((col + 1) * N) // GW
            for c in range(GW):
                seg = KICK16[a0[c]:a1[c]]
                lo, hi = int(seg.min()), int(seg.max())
                ya, yb = cy - hi / 32767 * (GH / 2 - 2), cy - lo / 32767 * (GH / 2 - 2)
                tocado = 0 <= n and a0[c] <= n
                tela.ret(GX + c, ya, 1, max(1, yb - ya + 1), CIANO if tocado else ACO1)
            if 0 <= n < N:
                xc = GX + n / N * GW
                tela.ret(xc, GY - 2, 1, GH + 4, BRANCO)
            tela.texto("0,3 S DE BUMBO", GX, GY + GH + 6, ACO2, tam=9, contorno=PRETO)
        else:
            # câmera lenta: cada amostra é um palito
            esc = 2.0
            janela = int(GW / esc)
            ini = max(0, n - janela + 12)
            for k in range(ini, ini + janela):
                if k > n: break
                x = GX + (k - ini) * esc
                v = int(KICK16[k]); yy = cy - v / 32767 * (GH / 2 - 2)
                yy = min(max(yy, GY + 1), GY + GH - 2)
                tela.ret(x, min(yy, cy), 1, abs(yy - cy) + 1, AMARELO if k == n else LARANJA)
                tela.px(x, yy, BRANCO if k == n else AMARELO)
            xn = GX + (n - ini) * esc
            v = int(KICK16[n]); yy = cy - v / 32767 * (GH / 2 - 2)
            yy = min(max(yy, GY + 1), GY + GH - 2)
            tela.disco(xn, yy, 2.5, PRETO); tela.disco(xn, yy, 1.6, AMARELO)
            centro_preso(tela, sinal(v), xn, yy - 13 if v >= 0 else yy + 6, AMARELO, xmin=GX, xmax=GX + GW)
            tela.texto("1 PALITO = 1 AMOSTRA", GX, GY + GH + 6, ACO2, tam=9, contorno=PRETO)
        # o cone segue o número
        Dk = Curva.de_tabela([-1e3, 1e3], [0, 0])
        dd = self.d_cone(t)
        self.F.desenhar(tela, dd, t=t, corrente=dd / 6)
        # lista de números (no Short ela fica embaixo do gráfico)
        if VERTICAL:
            xl, yl, nl = GX, GY + GH + 18, 3
        else:
            xl, yl, nl = PX0, 92, 8
        if n >= 0:
            for j in range(nl):
                k = n - (nl - 1) + j
                if k < 0: continue
                cor = AMARELO if j == nl - 1 else ACO3
                tela.texto(f"Nº {milhar(k)}", xl, yl + j * 12, ACO1, tam=9, contorno=PRETO)
                tela.texto(sinal(int(KICK16[k])), xl + 58, yl + j * 12, cor, tam=9, contorno=PRETO)
        self.vtxt(tela, "CÂMERA LENTA" if lento else "BUMBO DA TRILHA", AMARELO if lento else CIANO, y=4, tam=9)
        # painel
        self.ptit(tela, "O BUMBO DA TRILHA")
        if t < 15.2:
            self.ptxt(tela, "A CONTA: UMA ONDA QUE", 20, ACO3)
            self.ptxt(tela, "COMEÇA EM 118 HZ E CAI", 31, ACO3)
            self.ptxt(tela, "PARA 48 HZ, E SOME", 42, ACO3)
            self.ptxt(tela, f"BUMBO Nº {self.L.conta('kick', tg) - self.L.conta('kick', self.t0 - .01)}", 58, BRANCO, 17)
        else:
            self.ptxt(tela, "48.000", 18, AMARELO, 26)
            self.ptxt(tela, "NÚMEROS POR SEGUNDO", 46, BRANCO)
            self.ptxt(tela, "CADA UM EM 16 BITS", 57, ACO3)
        self.ptit(tela, "AMOSTRA       VALOR", 76)

    def sons(self, fx):
        k = 0
        while self.LENTO0 + k / self.VEL * 4 < self.dur - .1:
            fx.put(fx.clique(3600, .01), self.t0 + self.LENTO0 + k * 4 / self.VEL, .07, -.3)
            k += 1


# ============================================================ 9 DAC
class Dac(Cena):
    PASSO = .5

    def numeros(self):
        xs = np.arange(40)
        return [int(round(26000 * (.7 * math.sin(2 * math.pi * k / 14) + .3 * math.sin(2 * math.pi * k / 5.3)))) for k in xs]

    def preparar(self):
        self.N = self.numeros()
        self.F = Corte(262, 162, .45)

    def k_de(self, t): return int(max(0.0, t - .8) / self.PASSO)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        k = self.k_de(t)
        fr = (max(0.0, t - .8) % self.PASSO) / self.PASSO
        # placa de circuito
        dither(tela, 4, 24, 162, 104, PCB0, D.FUNDO)
        tela.ret_vazado(4, 24, 162, 104, PCB1)
        for j in range(5):
            tela.ret(8, 36 + j * 18, 70, 1, PCB1)
        # fila de números subindo para o chip
        tela.texto("FILA", 12, 28, PCB1, tam=9, contorno=PRETO)
        for j in range(5):
            idx = k + j
            y = 44 if j == 0 else 44 + j * 15 - suave(fr * 3) * 15
            if y > 118: continue
            v = self.N[idx % len(self.N)]
            painel(tela, 12, y - 3, 60, 13, borda=AMARELO if j == 0 else ACO1)
            tela.texto(sinal(v), 16, y, AMARELO if j == 0 else ACO3, tam=9)
        seta(tela, 74, 47, 88, 62, AMARELO, esp=1, ponta=3)
        # o chip
        cx0, cy0 = 96, 50
        for j in range(5):
            tela.ret(cx0 - 5, cy0 + 6 + j * 10, 5, 3, ACO3); tela.ret(cx0 + 50, cy0 + 6 + j * 10, 5, 3, ACO3)
        bloco(tela, cx0, cy0, cx0 + 50, cy0 + 56, D.CONE0, D.CONE2, PRETO)
        tela.disco(cx0 + 6, cy0 + 6, 2, D.CONE2)
        tela.texto("DAC", cx0 + 25, cy0 + 22, BRANCO, tam=17, centro=True, contorno=PRETO)
        if int(t * 8) % 2 == 0: tela.px(cx0 + 44, cy0 + 50, VERDE)
        # saída: a escadinha
        gx, gy, gw, gh = 178, 26, 112, 80
        painel(tela, gx - 3, gy - 3, gw + 6, gh + 6)
        cy = gy + gh / 2
        tela.ret(gx, cy, gw, 1, FUNDO3)
        larg = 8
        nmax = gw // larg
        ini = max(0, k - nmax + 1)
        pts = []
        for j in range(ini, k + 1):
            v = self.N[j % len(self.N)]
            x = gx + (j - ini) * larg
            y = cy - v / 32767 * (gh / 2 - 3)
            tela.ret(x, min(y, cy), larg, abs(y - cy) + 1, D.ESP0)
            tela.ret(x, y, larg, 2, AMARELO)
            if j > ini:
                yp = cy - self.N[(j - 1) % len(self.N)] / 32767 * (gh / 2 - 3)
                tela.ret(x, min(y, yp), 1, abs(y - yp) + 2, AMARELO)
            pts.append((x + larg / 2, y))
        tela.linha(cx0 + 55, cy0 + 26, gx - 4, cy0 + 26, AMARELO)
        tela.texto("TENSÃO", gx, gy + gh + 5, AMARELO, tam=9, contorno=PRETO)
        if t >= 15.4 and len(pts) > 2:
            u = suave((t - 15.4) / 1.2)
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if bx > gx + u * gw: break
                linha_grossa(tela, ax, ay, bx, by, 2, VERDE)
            tela.texto("ALISADA", gx + 60, gy + gh + 5, VERDE, tam=9, contorno=PRETO)
        # amplificador e falante
        v_out = self.N[k % len(self.N)] / 32767
        if t >= 15.4:
            ax0, ay0 = 160, 148
            tela.linha(gx + gw // 2, gy + gh + 16, gx + gw // 2, ay0 - 6, VERDE)
            tela.linha(gx + gw // 2, ay0 - 6, ax0 - 10, ay0 - 6, VERDE)
            tela.linha(ax0 - 10, ay0 - 6, ax0 - 10, ay0 + 16, VERDE)
            tela.linha(ax0 - 10, ay0 + 16, ax0, ay0 + 16, VERDE)
            poligono(tela, [(ax0 - 1, ay0 - 1), (ax0 + 41, ay0 + 16), (ax0 - 1, ay0 + 33)], PRETO)
            poligono(tela, [(ax0, ay0 + 1), (ax0 + 38, ay0 + 16), (ax0, ay0 + 31)], ACO1)
            tela.linha(ax0 + 1, ay0 + 3, ax0 + 30, ay0 + 14, ACO3)
            tela.texto("AMPLIFICADOR", ax0 - 30, ay0 + 38, BRANCO, tam=9, contorno=PRETO)
            on = int(t * 10) % 2
            linha_grossa(tela, ax0 + 38, ay0 + 16, 238, ay0 + 16, 3 if on else 2, LARANJA)
            self.F.desenhar(tela, v_out * 3, t=t, corrente=v_out)
        # painel
        self.ptit(tela, "DIGITAL PARA ANALÓGICO")
        self.ptxt(tela, "ENTRA UM NÚMERO", 22, ACO3)
        self.ptxt(tela, sinal(self.N[k % len(self.N)]), 33, AMARELO, 17)
        self.ptxt(tela, "SAI UMA TENSÃO", 60, ACO3)
        if not VERTICAL:
            medidor(tela, PX0, 72, 160, 12, v_out, AMARELO, centro=True)
            tela.texto("-", PX0, 88, MISTURA2, tam=9, contorno=PRETO)
            tela.texto("+", PX0 + 155, 88, LARANJA, tam=9, contorno=PRETO)
            self.ptxt(tela, "NÚMERO MAIOR,", 108, ACO3)
            self.ptxt(tela, "TENSÃO MAIOR", 119, ACO3)
            self.ptxt(tela, f"DEGRAU Nº {k + 1}", 140, BRANCO)
            self.ptxt(tela, "(AQUI, 2 POR SEGUNDO;", 156, ACO2)
            self.ptxt(tela, "NA VIDA REAL, 48.000)", 167, ACO2)

    def sons(self, fx):
        for k in range(int((self.dur - .8) / self.PASSO)):
            v = self.N[k % len(self.N)]
            fx.put(fx.blip(64 + int((v + 32768) / 65536 * 14), .05), self.t0 + .8 + k * self.PASSO, .05)


# ============================================================ 10 as peças
class Pecas(Cena):
    ORDEM = [('ima', 7.8, 'ÍMÃ PERMANENTE'), ('bobina', 15.2, 'BOBINA MÓVEL'), ('cone', 22.6, 'CONE'),
             ('aranha', 30.0, 'ARANHA'), ('borda', 37.4, 'BORDA'), ('carcaca', 44.8, 'CARCAÇA E FIOS')]

    def preparar(self):
        self.F = Corte(116, 104, 1.45)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        F = self.F
        d = 1.4 * math.sin(2 * math.pi * .7 * t)
        feitos = [p for p, a, _ in self.ORDEM if t >= a]
        if 'carcaca' in feitos: feitos.append('fios')
        # fantasma do falante inteiro
        F.desenhar(tela, d, t=t)
        apagar_pecas(tela, 0, 0, 298, PALCO_H)
        apagar_pecas(tela, 1, 0, 298, PALCO_H)
        atual = None
        for p, a, _ in self.ORDEM:
            if a <= t < a + 2.5: atual = p
        if feitos:
            F.desenhar(tela, d, t=t, pecas=feitos, campo='ima' in feitos, destaque=atual)
        # de frente, no começo
        if t < 7.6:
            u = 1 - suave((t - 6.6) / 1.0)
            if u > 0:
                falante_frente(tela, 236, 100, 46, d, t)
                seta(tela, 186, 100, 172, 100, AMARELO, esp=2, ponta=5)
                tela.texto("DE FRENTE", 210, 160, ACO3, tam=9, contorno=PRETO)
                tela.texto("CORTADO", 20, 8, AMARELO, tam=9, contorno=PRETO)
        # rótulos com fio
        P = F.P
        sg_d = d / F.s
        rot = {
            'ima': ("ÍMÃ PERMANENTE", 186, 146, P(-36, 26)),
            'bobina': ("BOBINA MÓVEL", 186, 118, P(-23 + sg_d, 10.5)),
            'cone': ("CONE", 186, 48, P(10 + sg_d, -32)),
            'aranha': ("ARANHA", 186, 66, P(-13.5 + sg_d * .5, -24)),
            'borda': ("BORDA", 186, 28, P(25.5 + sg_d * .5, -54)),
            'carcaca': ("CARCAÇA", 186, 10, P(4, -46)),
            'fios': ("FIOS DO SINAL", 186, 172, P(-9, 45)),
        }
        for p in feitos:
            txt, tx, ty, (ax, ay) = rot[p]
            cor = AMARELO if (p == atual or (p == 'fios' and atual == 'carcaca')) else ACO3
            rotulo(tela, txt, tx, ty, ax, ay, cor=cor)
        if 'ima' in feitos and t < 15.2:
            tela.texto("CAMPO NA FENDA", 20, 196, AMARELO, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "AS PEÇAS")
        self.ptxt(tela, f"PEÇA {len([p for p, a, _ in self.ORDEM if t >= a])} DE 6", 20, BRANCO, 17)
        for j, (p, a, nome) in enumerate(self.ORDEM):
            y = 46 + j * 16
            ok = t >= a
            if VERTICAL: continue
            tela.ret(PX0, y + 1, 8, 8, (AMARELO if p == atual else VERDE) if ok else FUNDO2)
            if ok: tela.ret(PX0 + 2, y + 3, 4, 4, PRETO)
            tela.texto(nome, PX0 + 13, y, BRANCO if p == atual else (ACO3 if ok else ACO0), tam=9, contorno=PRETO)
        self.ptxt(tela, "CORTE AO MEIO: O FALANTE", 160, ACO2)
        self.ptxt(tela, "É REDONDO, O DESENHO", 171, ACO2)
        self.ptxt(tela, "MOSTRA SÓ A FATIA", 182, ACO2)

    def sons(self, fx):
        for k, (p, a, _) in enumerate(self.ORDEM):
            fx.put(fx.sino(76 + k * 2, .8), self.t0 + a, .22, -.2 + k * .08)


# ============================================================ 11 a bobina empurra
class Empurra(CenaAr):
    FAL = (84, 98, 1.2)
    AR = (128, 296, 26, 170)
    C = 70.0
    ESCALA = .22
    XV = 112

    def corrente(self, t):
        if t < 3.0: return 0.0
        if t < 15.0: return suave((t - 3.0) / .8)
        if t < 22.6: return 1 - 2 * suave((t - 15.0) / .9)
        return -math.cos(2 * math.pi * .55 * (t - 22.6))

    def d(self, t): return 5.0 * self.corrente(t)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        I = self.corrente(t)
        # fios que trazem o sinal (pontos andando no sentido da corrente)
        tt = self.F.terminais()
        fase = (t * 18 * I) if True else 0
        for j, (xt, yt) in enumerate(tt):
            ycab = 22 if j == 0 else 176
            pts = [(0, ycab), (xt - 14, ycab), (xt, yt)]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                linha_grossa(tela, ax, ay, bx, by, 4, PRETO)
                linha_grossa(tela, ax, ay, bx, by, 2, VERMELHO if j == 0 else MISTURA)
            if abs(I) > .05:
                sentido = 1 if j == 0 else -1
                L = xt - 14
                for k in range(8):
                    x = ((k * 12 + fase * 10 * sentido) % L)
                    tela.ret(x, ycab - 1, 2, 2, AMARELO)
        cols, lev, dd = self.palco_ar(tela, t, corrente=I, campo=True)
        # força
        if abs(I) > .08:
            P = self.F.P
            x0, y0 = P(-22 + dd / self.F.s, 0)
            comp = 26 * I
            seta(tela, x0, y0, x0 + comp, y0, AMARELO if I > 0 else CIANO, esp=2, ponta=5)
            tela.texto("FORÇA", min(x0, x0 + comp) - 2, y0 - 16, AMARELO if I > 0 else CIANO, tam=9, contorno=PRETO)
        txt = "PARA FORA" if I > .2 else ("PARA DENTRO" if I < -.2 else "PARADO")
        self.vtxt(tela, "CORRENTE " + ("+" if I > .05 else ("-" if I < -.05 else "0")) + "  " + txt, AMARELO, y=6, tam=9)
        # painel
        self.ptit(tela, "CORRENTE NA BOBINA")
        if not VERTICAL:
            medidor(tela, PX0, 22, 160, 12, I, AMARELO if I >= 0 else CIANO, centro=True)
            tela.texto("-", PX0, 38, CIANO, tam=9, contorno=PRETO)
            tela.texto("+", PX0 + 155, 38, AMARELO, tam=9, contorno=PRETO)
            self.ptxt(tela, "O CONE VAI", 52, ACO3)
            self.ptxt(tela, txt, 63, AMARELO if I > .2 else (CIANO if I < -.2 else ACO2), 17)
            self.ptit(tela, "NO CORTE DO FIO", 92)
            tela.disco(PX0 + 4, 112, 3, PRETO); tela.ret(PX0 + 3, 111, 2, 2, BRANCO)
            self.ptxt(tela, "CORRENTE SAINDO", 108, ACO3, x=PX0 + 14)
            tela.disco(PX0 + 4, 126, 3, PRETO)
            for a, b in ((-1, -1), (1, 1), (-1, 1), (1, -1), (0, 0)): tela.px(PX0 + 4 + a, 126 + b, BRANCO)
            self.ptxt(tela, "CORRENTE ENTRANDO", 122, ACO3, x=PX0 + 14)
            tela.ret(PX0 + 2, 138, 5, 1, AMARELO)
            self.ptxt(tela, "CAMPO DO ÍMÃ NA FENDA", 135, ACO3, x=PX0 + 14)
            self.rastro(tela, PX0, 154, 160, 40, self.D, t, janela=4.0, cor=CONE3, ymax=6.0)

    def sons(self, fx):
        for a in (3.0, 15.0):
            fx.put(fx.pulso(), self.t0 + a + .2, .25)


# ============================================================ 12 no ritmo
class Ritmo(CenaAr):
    FAL = (56, 96, 1.0)
    AR = (92, 296, 26, 164)
    C = 120.0
    ESCALA = .3
    XV = 98

    def preparar(self):
        self.F = Corte(*self.FAL)
        x0, x1, y0, y1 = self.AR
        self.ar = Ar(x0, x1, y0, y1, passo=6, seed=21, xa=self.F.face_x() + 2)
        self.ks = kicks_do_capitulo(self)
        self.D = curva_kicks(self.ks, A=6.0, t1=self.dur + 2)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        I = float(self.D(t)) / 6
        cols, lev, dd = self.palco_ar(tela, t, corrente=I)
        nb = self.L.conta('kick', tg) - self.L.conta('kick', self.t0 - .01)
        self.faixa_musica(tela, tg, 8, 176, 284, 26)
        self.vtxt(tela, f"BUMBO Nº {nb}", AMARELO, y=4, tam=17)
        # painel
        self.ptit(tela, "A MÚSICA DESTE VÍDEO")
        self.ptxt(tela, f"BUMBO Nº {nb}", 20, AMARELO, 17)
        self.ptxt(tela, "120 BATIDAS POR MINUTO", 42, ACO3)
        self.ptit(tela, "AMOSTRA DO VÍDEO", 62)
        self.ptxt(tela, milhar(int(tg * SR)), 76, BRANCO, 17)
        mm, ss = int(tg // 60), int(tg % 60)
        self.ptxt(tela, f"NO MINUTO {mm}:{ss:02d}", 96, ACO3)
        self.rastro(tela, PX0, 116, 160, 44, self.D, t, janela=2.0, cor=CONE3, ymax=6.5)
        self.ptxt(tela, "POSIÇÃO DO CONE", 166, ACO2)


# ============================================================ 13 woofer e tweeter
class Woofer(Cena):
    def preparar(self):
        self.ondas_w = []

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        # caixa de madeira
        x0, y0, x1, y1 = 26, 8, 150, 200
        tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
        dither(tela, x0, y0, x1 - x0, y1 - y0, MAD1, MAD0)
        tela.ret(x0, y0, x1 - x0, 2, MAD2); tela.ret(x0, y0, 2, y1 - y0, MAD2)
        tela.ret(x0, y1 - 2, x1 - x0, 2, MAD0)
        for k in range(6): tela.ret(x0 + 6 + k * 21, y0 + 3, 1, y1 - y0 - 6, MAD0)
        cw, ct = (88, 136), (88, 46)
        dw = 4.0 * math.sin(2 * math.pi * 1.1 * t)
        dt_ = 2.0 * math.sin(2 * math.pi * 6.0 * t)
        foco = 'w' if t < 15.0 else 't'
        # frentes de onda saindo para a direita
        for (cx, cy), lam, vel, cor, on in ((cw, 56.0, 60.0, LARANJA, True), (ct, 10.0, 60.0, CIANO, t >= 15.0)):
            if not on: continue
            fase = (t * vel) % lam
            r = 70 - lam + fase if lam > 20 else 30 + fase
            while r < 200:
                for k in range(-40, 41):
                    a = k * .02
                    x = cx + math.cos(a) * r; y = cy + math.sin(a) * r
                    if 152 < x < 296 and 2 < y < 204:
                        tela.px(x, y, cor if r < 190 else D.AR1)
                        if lam > 20: tela.px(x - 1, y, cor if r < 190 else D.AR1)
                r += lam
        falante_frente(tela, cw[0], cw[1], 44, dw, t)
        falante_frente(tela, ct[0], ct[1], 15, dt_, t)
        if foco == 'w':
            rotulo(tela, "WOOFER", 196, 128, cw[0] + 30, cw[1] - 26, cor=LARANJA)
            tela.texto("CONE GRANDE", 196, 140, ACO3, tam=9, contorno=PRETO)
        else:
            apagar_pecas(tela, cw[0] - 53, cw[1] - 53, cw[0] + 54, cw[1] + 54)
            rotulo(tela, "TWEETER", 196, 40, ct[0] + 12, ct[1] - 10, cor=CIANO)
            tela.texto("PEQUENO E LEVE", 196, 52, ACO3, tam=9, contorno=PRETO)
        # painel
        self.ptit(tela, "QUEM TOCA O QUÊ")
        if not VERTICAL:
            y = 58
            faixa_hz(tela, PX0, y - 18, 160, 20, 20000, ACO1, alto=3)
            tela.texto("OUVIDO HUMANO", PX0, y - 30, ACO2, tam=9, contorno=PRETO)
            if t >= 7.8:
                faixa_hz(tela, PX0, y - 9, 160, 50, 2000, LARANJA, alto=4)
            if t >= 22.6:
                faixa_hz(tela, PX0, y - 9, 160, 2000, 20000, CIANO, alto=4)
            regua_hz(tela, PX0, y, 160)
            self.ptxt(tela, "WOOFER", 84, LARANJA)
            self.ptxt(tela, "50 A 2.000 HZ" if t >= 7.8 else "GRAVES", 95, BRANCO, 17)
            if t >= 15.2:
                self.ptxt(tela, "TWEETER" + (" (HZ)" if t >= 22.6 else ""), 120, CIANO)
                self.ptxt(tela, "2.000 A 20.000" if t >= 22.6 else "AGUDOS", 131, BRANCO, 17)
            self.ptxt(tela, "FAIXAS TÍPICAS: CADA", 160, ACO2)
            self.ptxt(tela, "MODELO TEM A SUA", 171, ACO2)


# ============================================================ 14 microfone
class Microfone(Cena):
    C = 70.0

    def preparar(self):
        self.Fs = Corte(30, 100, .55)
        self.Fm = Corte(252, 100, .85, espelho=-1)
        self.ar = Ar(46, 222, 36, 164, passo=6, seed=31, xa=self.Fs.face_x() + 2)
        self.D = Curva(lambda t: 4.5 * math.sin(2 * math.pi * .7 * t) * suave((t + 1) / 1.0), -6, self.dur + 2)
        self.dist = (self.Fm.face_x() - self.ar.xa)

    def d_mic(self, t):
        return float(self.D(t - self.dist / self.C)) * .8

    def corrente(self, t):
        return (self.d_mic(t + .02) - self.d_mic(t - .02)) / .04 / (4.5 * .8 * 2 * math.pi * .7)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        self.ar.desenhar(tela, t, self.D, self.C, escala=.28, prota=False)
        self.Fs.desenhar(tela, float(self.D(t)), t=t, pecas=('ima', 'bobina', 'cone', 'aranha', 'borda', 'carcaca'))
        I = self.corrente(t)
        self.Fm.desenhar(tela, -self.d_mic(t), t=t, corrente=I, campo=True)
        # fios para o ADC (no painel)
        for j, (xt, yt) in enumerate(self.Fm.terminais()):
            ycab = 22 if j == 0 else 180
            for (ax, ay), (bx, by) in (((xt, yt), (xt + 8, ycab)), ((xt + 8, ycab), (298, ycab))):
                linha_grossa(tela, ax, ay, bx, by, 3, PRETO)
                linha_grossa(tela, ax, ay, bx, by, 1.5, VERMELHO if j == 0 else MISTURA)
            for k in range(3):
                x = xt + 8 + ((k * 13 + t * 40 * I * (1 if j == 0 else -1)) % (298 - xt - 8))
                tela.ret(x, ycab - 1, 2, 2, AMARELO)
        rotulo(tela, "MEMBRANA", 152, 12, *self.Fm.P(12, -32), cor=AMARELO)
        tela.texto("SOM CHEGANDO", 60, 176, ACO3, tam=9, contorno=PRETO)
        seta(tela, 140, 180, 170, 180, ACO3, esp=1, ponta=4)
        # painel
        self.ptit(tela, "MICROFONE + ADC")
        if not VERTICAL:
            self.ptxt(tela, "CORRENTE GERADA", 20, ACO3)
            medidor(tela, PX0, 32, 160, 12, clamp(I, -1, 1), AMARELO, centro=True)
            # chip ADC
            bloco(tela, PX0 + 4, 56, PX0 + 50, 92, D.CONE0, D.CONE2, PRETO)
            tela.texto("ADC", PX0 + 27, 66, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.ret(PX0 - 8, 22, 1, 52, VERMELHO); tela.ret(PX0 - 8, 74, 12, 1, VERMELHO)
            tela.ret(PX0 - 6, 74, 1, 106, MISTURA); tela.ret(PX0 - 6, 80, 10, 1, MISTURA)
            if t >= 15.4:
                self.ptit(tela, "NÚMEROS DE NOVO", 100)
                k0 = int((t - 15.4) * 8)
                for j in range(6):
                    k = k0 - 5 + j
                    if k < 0: continue
                    tk = 15.4 + k / 8
                    v = int(round(clamp(self.corrente(tk), -1, 1) * 30000))
                    tela.texto(f"Nº {k + 1}", PX0, 116 + j * 12, ACO1, tam=9, contorno=PRETO)
                    tela.texto(sinal(v), PX0 + 56, 116 + j * 12, AMARELO if j == 5 else ACO3, tam=9, contorno=PRETO)
            else:
                self.ptxt(tela, "O MESMO DESENHO DO", 104, ACO3)
                self.ptxt(tela, "ALTO-FALANTE, AO CONTRÁRIO:", 115, ACO3)
                self.ptxt(tela, "AR MOVE O CONE,", 130, BRANCO)
                self.ptxt(tela, "O CONE MOVE A BOBINA,", 141, BRANCO)
                self.ptxt(tela, "A BOBINA GERA CORRENTE", 152, AMARELO)

    def sons(self, fx):
        for k in range(int((self.dur - 15.4) * 8)):
            if k % 2 == 0: fx.put(fx.clique(4500, .01), self.t0 + 15.4 + k / 8, .05, .5)


# ============================================================ 15 resumo
class Resumo(Cena):
    def preparar(self):
        self.ks = kicks_do_capitulo(self)
        self.F = Corte(176, 96, .5)
        self.ar = Ar(194, 252, 66, 126, passo=6, seed=41, xa=193)
        self.D = curva_kicks(self.ks, A=4.0, t1=self.dur + 2)

    def desenhar(self, tela, t, tg):
        self.fundo(tela, t)
        tela.texto("DE NÚMEROS A SOM", 150, 10, BRANCO, tam=17, centro=True, contorno=PRETO)
        # quem está aceso: um pulso anda pela corrente em cada bumbo
        ult = max([tk for tk, _ in self.ks if tk <= t], default=-9)
        fase = (t - ult) / .6
        etapas = [(28, 'NÚMEROS'), (76, 'DAC'), (124, 'AMPLIF.'), (172, 'CONE'), (222, 'AR'), (272, 'OUVIDO')]
        ativo = int(fase * 6) if fase < 1 else -1
        cy = 96
        # setas
        for j in range(5):
            xa, xb = etapas[j][0] + 18, etapas[j + 1][0] - 18
            if j == 3: continue
            seta(tela, xa, cy, xb, cy, AMARELO if j < ativo else ACO1, esp=1, ponta=4)
        # 1 números
        painel(tela, 12, 76, 34, 40, borda=AMARELO if ativo == 0 else ACO1)
        for r in range(4):
            tela.texto(''.join('1' if ((r * 5 + k + int(t * 4)) % 3) else '0' for k in range(4)), 16, 80 + r * 9,
                       AMARELO if ativo == 0 else ACO3, tam=9)
        # 2 DAC
        bloco(tela, 62, 80, 92, 112, D.CONE0, D.CONE2, PRETO)
        tela.texto("DAC", 77, 90, AMARELO if ativo == 1 else BRANCO, tam=9, centro=True, contorno=PRETO)
        # 3 amplificador
        poligono(tela, [(111, 79), (141, 96), (111, 113)], PRETO)
        poligono(tela, [(112, 81), (138, 96), (112, 111)], AMARELO if ativo == 2 else ACO1)
        # 4 falante e 5 ar
        self.ar.desenhar(tela, t, self.D, 70.0, escala=.35)
        self.F.desenhar(tela, float(self.D(t)), t=t, corrente=float(self.D(t)) / 4)
        # 6 ouvido (forma genérica)
        D.ouvido(tela, 274, 96, .95, cor=LATAO, luz=AMARELO if ativo == 5 else D.MAD2)
        self.faixa_musica(tela, tg, 8, 166, 284, 28)
        if not VERTICAL:
            tela.texto("A TRILHA DESTE VÍDEO, AGORA", 8, 154, ACO2, tam=9, contorno=PRETO)
        for j, (x, nome) in enumerate(etapas):
            centro_preso(tela, nome, x, 136, AMARELO if j == ativo else ACO3)
        # contagem dos números do vídeo
        self.ptit(tela, "NÚMEROS DE ÁUDIO DO VÍDEO")
        self.ptxt(tela, "ATÉ AGORA", 20, ACO3)
        self.ptxt(tela, milhar(int(tg * SR * 2)), 31, AMARELO, 17)
        self.ptxt(tela, "48.000 POR SEGUNDO", 54, ACO3)
        self.ptxt(tela, "X 2 CANAIS", 65, ACO3)
        if t >= 19.4:
            tot = int(round(self.T.total * SR * 2))
            self.ptit(tela, "NO VÍDEO INTEIRO", 90)
            self.ptxt(tela, milhar(tot), 104, BRANCO, 17)
            self.ptxt(tela, f"UNS {MILHOES} MILHÕES", 126, VERDE)

    def sons(self, fx):
        for tk, v in self.ks:
            if 0 <= tk < self.dur: fx.put(fx.blip(84, .04), self.t0 + tk + .5, .04)


# ============================================================ 16 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            D.grade_fundo(tela, W)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            falante_frente(tela, W // 2, 150, 40, 3 * math.sin(t * 6), t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, ar=ArCena, velocidade=Velocidade, frequencia=Frequencia,
             amplitude=Amplitude, amostras=Amostras, bits=Bits, bumbo=Bumbo, dac=Dac, pecas=Pecas,
             empurra=Empurra, ritmo=Ritmo, woofer=Woofer, microfone=Microfone, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep12_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        so = sys.argv[3:] or None
        fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
