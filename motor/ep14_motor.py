#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep14 — Como o submarino afunda e sobe (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (respiro, ar soprando, bolhas, hélice, ping),
                          nos mesmos instantes do desenho

A física manda no desenho: o peso do submarino sai da água nos tanques; o
empuxo cresce com a parte submersa e para de crescer quando ele some na água
(Arquimedes); a fundura sai de integrar peso - empuxo (`D.Vertical`). O painel
e o contador leem os mesmos números.

    python3 ep14_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep14_motor.py <saida.mp4> mergulho subir      # só esses capítulos (teste)
    python3 ep14_motor.py --folha <saida.png>             # 2 quadros por capítulo
    python3 ep14_motor.py --folha <saida.png> mergulho    # 5 quadros (FR=.1,.3,.5,.7,.9)
    python3 ep14_motor.py --folha <saida.png> mergulho 0.2 0.6
"""
import math, os, sys
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ritmo_marca as RM
import quizaudio as QA
import ep14_desenho as D
from ep14_desenho import PXM, Sub, Vertical, rotulo, fio, seta, forca, bolhas, seta_dir, arco
from ep14_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2614, 43
GANHO_MUSICA = -10.0          # trilha baixa: o texto e os sons do mar mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
SR = LG.SR

SUB = Sub(210, 28)            # o protagonista
SUB_G = Sub(262, 38)          # grande, para as peças
SUB_V = Sub(150, 22)          # nos cortes verticais
SUB_P = Sub(110, 16)          # pequeno (limite, sonar)
SUB_M = Sub(70, 11)           # miniatura (resumo, painel)
HM, DM = SUB.Hm, SUB.Dm       # alturas (m) do protagonista: quilha->vela, diâmetro


def milhar(n): return f"{int(round(n)):,}".replace(',', '.')
def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')


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


def sub(): return SUB_V if VERTICAL else SUB
def cx_de(cap, cx): return x_corte(cap) + 90 if VERTICAL else cx


def hud_v(tela, cap, linhas, y=6):
    """No corte vertical o painel some: os números vão para o alto do recorte."""
    if not VERTICAL: return
    x = x_corte(cap) + 90
    for k, (txt, cor) in enumerate(linhas):
        w = tela.largura_texto(txt, 9) + 8
        painel(tela, x - w // 2, y + k * 15 - 3, w, 14, borda=cor)
        tela.texto(txt, x, y + k * 15, cor, tam=9, centro=True)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def tit(tela, txt, y, cor=BRANCO, tam=17, x=PX0, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO, centro=centro)


def etiqueta(tela, txt, x, y, cor, tam=9, centro=True):
    w = tela.largura_texto(txt, tam)
    hh = 14 if tam < 14 else 22
    xx = x - w // 2 if centro else x
    painel(tela, xx - 5, y - 4, w + 10, hh + 2, borda=cor)
    tela.texto(txt, xx, y, cor, tam=tam)


def camera(eixo_m, y_alvo=110, ys0=70):
    """Fundura (m) do alto da tela: a superfície fica em ys0 até o submarino
    passar de y_alvo; daí a câmera desce junto."""
    return max(-ys0 / PXM, eixo_m - y_alvo / PXM)


def prof_txt(zk):
    """Contador: fundura do eixo do casco, ou SUPERFÍCIE com a vela de fora."""
    if zk < HM - .3: return 'SUPERFÍCIE'
    return f"{milhar(zk - DM / 2)} M"


def estado_txt(zk, v):
    if zk < HM - .3 and abs(v) < .25: return 'FLUTUA', CIANO
    if v > .12: return 'DESCE', VERMELHO
    if v < -.12: return 'SOBE', VERDE
    return 'PARADO', AMARELO


def painel_sub(tela, t, zk, v, lastro, Wt, Bt, extra=()):
    """O painel de sempre: fundura, tanques de lastro, peso x empuxo, estado."""
    fundo_painel(tela)
    tit(tela, 'PROFUNDIDADE', 9, ACO3, 9)
    p = prof_txt(zk)
    tit(tela, p, 21 if len(p) > 6 else 19, AMARELO, 17 if len(p) > 6 else 26)
    tit(tela, 'TANQUES', 56, ACO3, 9)
    tit(tela, 'DE LASTRO', 66, ACO3, 9)
    D.medidor_tanque(tela, PX0 + 2, 80, 24, 46, lastro, None, t)
    tela.texto(f"{int(round(lastro * 100))}%", PX0 + 14, 130, MISTURA2, tam=9, centro=True, contorno=PRETO)
    tela.texto('ÁGUA', PX0 + 14, 141, ACO3, tam=9, centro=True, contorno=PRETO)
    D.barra_forca(tela, PX0 + 64, 58, 100, Wt - .8, .25, VERMELHO, 'PESO', '')
    D.barra_forca(tela, PX0 + 64, 84, 100, Bt - .8, .25, VERDE, 'EMPUXO', '')
    est, cor = estado_txt(zk, v)
    tit(tela, est, 110, cor, 17, PX0 + 64)
    for k, (txt, c) in enumerate(extra):
        tit(tela, txt, 160 + k * 12, c, 9)


def mascara(S, cx, cy, ang, est, t):
    tmp = PX.Tela(W, H, paleta=LG.PAL)
    tmp.buf[:] = D.VAZIO
    S.desenhar(tmp, cx, cy, ang, est, t)
    return tmp.buf != D.VAZIO


def respiro_ar(tela, S, cx, cy, ang, ys, t, forca_=1.0, seed=0):
    """Ar saindo pelos respiros: névoa no ar, bolhas embaixo d'água."""
    if forca_ <= .02: return
    for k, nome in enumerate(('respiro_proa', 'respiro_popa')):
        x, y = S.tela_xy(nome, cx, cy, ang)
        if ys is not None and y < ys + 1:
            n = int(4 + 10 * forca_)
            for j in range(n):
                u = (t * 2.2 + j / n + k * .3) % 1.0
                a = (j * 2.39 + k) % 1.6 - .8
                xx = x + math.sin(a) * 14 * u
                yy = y - u * (8 + 22 * forca_)
                tela.px(xx, yy, BRANCO if u < .4 else (ACO4 if u < .7 else ACO2))
        else:
            bolhas(tela, x, y, t, sobe=60 * forca_ + 20, n=int(3 + 6 * forca_), vel=1.3, abre=8, seed=k + seed,
                   ymin=(ys + 2) if ys is not None else None)


def agua_entrando(tela, S, cx, cy, ang, t, para_fora=False, forca_=1.0):
    """Riscos de água nas válvulas de baixo (entrando ou sendo empurrada para fora)."""
    if forca_ <= .02: return
    for k, nome in enumerate(('valvula_proa', 'valvula_popa')):
        x, y = S.tela_xy(nome, cx, cy, ang)
        for j in range(5):
            u = (t * 2.5 + j / 5 + k * .5) % 1.0
            if para_fora:
                tela.ret(int(x - 4 + j * 2), int(y + 2 + u * 12), 1, 2, MISTURA2)
            else:
                tela.ret(int(x - 4 + j * 2), int(y + 14 - u * 12), 1, 2, MISTURA2)
        if para_fora:
            bolhas(tela, x, y + 14, t, sobe=10, n=3, vel=1.5, abre=6, seed=k)


# ----------------------------------------------------------------- sons
def tique(f=1800, dur=.012):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))).astype(np.float32)


def bloop(f0=300, f1=900, dur=.05):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * tt / dur
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.sin(np.pi * tt / dur)).astype(np.float32)


def rangido(dur=.6, f=70):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f * tt - 8 * tt * tt)) * (1 + .5 * np.sin(2 * np.pi * 23 * tt))
    return (y * np.sin(np.pi * tt / dur) / 1.5).astype(np.float32)


def zumbido(dur=2.0, f=110):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * 2 * f * tt)) * np.minimum(1, np.minimum(tt, dur - tt) / .2)
    return (y / 1.3).astype(np.float32)


def bolhas_som(fx, t0, t1, taxa=3.0, g=.05, seed=0):
    rng = np.random.default_rng(seed)
    t = t0
    while t < t1:
        f0 = 250 + rng.random() * 300
        fx.put(bloop(f0, f0 * 2.5, .04 + rng.random() * .03), t, g, rng.random() * .8 - .4)
        t += rng.exponential(1 / taxa)


def mar_som(fx, t0, t1, g=.025):
    t = t0
    while t < t1 - .5:
        d = min(4.2, t1 - t)
        fx.put(fx.chiado(d, 90, 500), t, g, math.sin(t) * .3)
        t += 3.3


def helice_som(fx, t0, t1, rps_fn, g=.03):
    """Um pulso grave a cada passagem de pá (5 pás)."""
    t = t0
    while t < t1:
        r = rps_fn(t - t0)
        if r < .05:
            t += .1; continue
        fx.put(fx.pulso(), t, g, -.2)
        t += 1.0 / (r * 5)


# ================================================================== cenas
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


def cena_vertical(tela, t, cap, sim, cx, est, ang=0.0, xoff=0.0, y_alvo=110, ys0=70, regua_x=None):
    """Mar + neve + submarino na fundura da simulação. Devolve (ys, cy, cam)."""
    zk = sim(t)
    eixo = zk - DM / 2
    cam = camera(eixo, y_alvo, ys0)
    ys = D.mar(tela, cam, t)
    D.neve(tela, cam, xoff, t, ys)
    if regua_x is not None and not VERTICAL:
        D.regua(tela, regua_x, cam, 10, 50, ysurf=ys)
    cy = (eixo - cam) * PXM
    sub().desenhar(tela, cx, cy, ang, est, t)
    return ys, cy, cam


# ============================================================ gancho
class Gancho(Cena):
    def W(self, t):
        f = rampa(t, [(2.0, 0.0), (6.0, 1.0), (9.3, 1.0), (11.5, 0.0)])
        return .9 + .13 * f

    def lastro(self, t): return rampa(t, [(2.0, 0.0), (6.0, 1.0), (9.3, 1.0), (11.5, .1)])

    def preparar(self):
        self.sim = Vertical(self.W, self.dur, .9 * HM, HM)

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('gancho', 130)
        est = dict(corte=False, respiros=2.0 <= t < 7.5, valvulas=True, helice=t * 4, lemes=0)
        ys, cy, cam = cena_vertical(tela, t, 'gancho', self.sim, cx, est, 0.0, xoff=t * 2, ys0=64)
        if 2.0 <= t < 7.0:
            respiro_ar(tela, S, cx, cy, 0, ys, t, 1 - (t - 2) / 6)
        if 9.3 <= t < 12.5:
            agua_entrando(tela, S, cx, cy, 0, t, para_fora=True, forca_=1 - (t - 9.3) / 3.2)
        D.superficie(tela, ys, t)
        zk, v = self.sim(t), self.sim.vel(t)
        if t > 2.5 and not VERTICAL:
            est_, cor = estado_txt(zk, v)
            etiqueta(tela, est_, cx, 12 if ys is None or ys > 30 else ys + 8, cor, 17)
        hud_v(tela, 'gancho', [(f"PROFUNDIDADE {prof_txt(zk)}", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PROFUNDIDADE', 9, ACO3, 9)
        p = prof_txt(zk)
        tit(tela, p, 21 if len(p) > 6 else 19, AMARELO, 17 if len(p) > 6 else 26)
        tit(tela, 'TANQUES DE LASTRO', 60, ACO3, 9)
        D.medidor_tanque(tela, PX0 + 2, 74, 40, 70, self.lastro(t), None, t)
        tit(tela, f"{int(round(self.lastro(t) * 100))}% ÁGUA", 110, MISTURA2, 9, PX0 + 52)
        D.regua(tela, PX0 + 120, cam if cam > 0 else 0, 10, 50)

    def sons(self, fx):
        mar_som(fx, self.t0, self.t0 + self.dur)
        fx.put(tique(1500), self.t0 + 2.0, .3)
        fx.put(fx.chiado(4.5, 600, 4000), self.t0 + 2.1, .07, .2)
        bolhas_som(fx, self.t0 + 4.5, self.t0 + 8, 4, .04, 1)
        fx.put(tique(1200), self.t0 + 9.3, .3)
        fx.put(fx.chiado(2.5, 300, 2500), self.t0 + 9.4, .08, -.2)
        bolhas_som(fx, self.t0 + 9.5, self.t0 + 12.5, 6, .05, 2)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        cam = 14.0
        D.mar(tela, cam, t)
        D.neve(tela, cam, t * 4, t)
        x = -130 + t * 95
        SUB.desenhar(tela, x, 168, 0, dict(helice=t * 9), t)
        hx, hy = SUB.tela_xy('helice', x, 168)
        bolhas(tela, hx - 6, hy, t, sobe=26, n=8, vel=1.6, abre=10)
        n = int(t / .045)
        for j, linha in enumerate(("COMO O SUBMARINO", "AFUNDA E SOBE")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 17)]
            tela.texto(vis, W // 2 - larg // 2, 22 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("COMO VOA / FLUTUA", W // 2, 96, AMARELO, tam=17, centro=True, contorno=PRETO)

    def sons(self, fx):
        for k in range(3):
            fx.put(fx.blip(72 + k * 4, .1), self.t0 + 1.2 + k * .25, .2)
        bolhas_som(fx, self.t0, self.t0 + 6, 3, .03, 3)


# ============================================================ Arquimedes
class Arquimedes(Cena):
    YS = 92

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('arquimedes', 140)
        zk = .9 * HM + .15 * math.sin(t * 1.3)
        cam = -self.YS / PXM
        ys = D.mar(tela, cam, t)
        D.neve(tela, cam, t * .5, t, ys)
        cy = ys + (zk - DM / 2) * PXM
        aberto = t >= 28.8
        est = dict(corte=True, lastro=0.0, helice=t * .8, valvulas=aberto and int(t * 2) % 2 == 0)
        S.desenhar(tela, cx, cy, 0, est, t)
        # a parte submersa = a água que ele empurra
        if t < 14.6:
            m = mascara(S, cx, cy, 0, est, t)
            yy, xx = np.mgrid[0:H, 0:W]
            sel = m & (yy > ys + 1) & ((xx + yy) % 2 == 0) & ((xx // 2 + yy // 2 + int(t * 4)) % 4 == 0)
            tela.buf[sel] = MISTURA2
        D.superficie(tela, ys, t)
        bc = cy + (S.D * .5)
        if t < 7.8:
            rotulo(tela, 'ÁGUA EMPURRADA', cx - 40, ys + 46, MISTURA2)
            fio(tela, cx - 10, ys + 44, cx - 10, cy + 6, MISTURA2)
        # forças: iguais na superfície
        pulso = 1 + (.15 * math.sin(t * 6) if 7.8 <= t < 14.6 else 0)
        forca(tela, cx + 18, cy, 30, False, VERMELHO)
        forca(tela, cx - 18, cy, 30 * pulso, True, VERDE)
        rotulo(tela, 'PESO', cx + 26, cy + 22, VERMELHO)
        rotulo(tela, 'EMPUXO', cx - 26, cy - 34, VERDE, centro='d')
        if 7.8 <= t < 14.6:
            for k in range(5):
                x = cx - 70 + k * 35
                u = (t * 1.5 + k * .2) % 1.0
                seta(tela, x, int(bc + 14 - u * 6), 0, -1, VERDE, 4)
        if aberto:
            for nome in ('lastro_proa', 'lastro_popa'):
                x, y = S.tela_xy(nome, cx, cy)
                fio(tela, cx, 40 if not VERTICAL else 34, x, y, MISTURA2)
            if not VERTICAL: rotulo(tela, 'ENCHER DE ÁGUA DO MAR?', cx, 28, MISTURA2, centro=True)
            agua_entrando(tela, S, cx, cy, 0, t, forca_=.6)
        hud_v(tela, 'arquimedes', [("PESO = EMPUXO", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PESO X EMPUXO', 9, AMARELO, 17)
        D.barra_forca(tela, PX0, 34, 160, .9, 1.0, VERMELHO, 'PESO', '')
        D.barra_forca(tela, PX0, 58, 160, .9 * pulso if t < 14.6 else .9, 1.0, VERDE, 'EMPUXO', '')
        if t < 7.8:
            tit(tela, 'LEMBRA DO EP. 6,', 86, ACO3, 9); tit(tela, 'O DO NAVIO?', 98, ACO3, 9)
        elif t >= 14.8:
            tit(tela, '= IGUAIS: FLUTUA', 84, CIANO, 9)
        if t >= 21.8:
            casos = [('MAIOR: SOBE', VERDE, -1), ('MENOR: DESCE', VERMELHO, 1), ('IGUAL: PARADO', AMARELO, 0)]
            ativo = min(2, int((t - 21.8) / 2.3)) if t < 28.8 else -1
            for k, (txt, cor, s) in enumerate(casos):
                y = 104 + k * 24
                on = ativo == k or t >= 28.8
                dither(tela, PX0, y, 46, 20, FUNDO3, FUNDO2)
                tela.ret_vazado(PX0 - 1, y - 1, 48, 22, cor if ativo == k else ACO1)
                ph = ((t * .5 + k * .3) % 1.0)
                yy = y + 10 + (s * (ph * 14 - 7) if s else math.sin(t * 2) * .6)
                SUB_M.desenhar(tela, PX0 + 23, yy, 0, dict(helice=t), t)
                tela.ret(PX0, y - 1, 46, 1, MISTURA2)
                tit(tela, 'EMPUXO', y + 1, ACO3 if not on else BRANCO, 9, PX0 + 54)
                tit(tela, txt, y + 11, cor if on else ACO1, 9, PX0 + 54)
        if t >= 28.8:
            tit(tela, 'O PESO MUDA COM', 180, MISTURA2, 9); tit(tela, 'ÁGUA NOS TANQUES', 191, MISTURA2, 9)

    def sons(self, fx):
        mar_som(fx, self.t0, self.t0 + self.dur)
        for ta, m in ((7.8, 76), (14.8, 79), (21.8, 72), (24.1, 74), (26.4, 77), (28.8, 81)):
            fx.put(fx.blip(m, .08), self.t0 + ta, .12)


# ============================================================ as peças
PECAS = [('casco', 'CASCO RESISTENTE', 'TUBO DE AÇO GROSSO'),
         ('lastro', 'TANQUES DE LASTRO', 'AR OU ÁGUA DO MAR'),
         ('ajuste', 'TANQUES DE AJUSTE', 'PESO E NÍVEL'),
         ('ar', 'AR COMPRIMIDO', 'ESVAZIA OS TANQUES'),
         ('lemes', 'LEMES DE PROFUNDIDADE', 'PROA E POPA'),
         ('helice', 'HÉLICE', 'EMPURRA PARA A FRENTE'),
         ('sonar', 'SONAR', 'OS OUVIDOS')]
PONTOS = dict(casco=['casco', 'aneis'], lastro=['lastro_proa', 'lastro_popa'],
              ajuste=['trim_proa', 'ajuste', 'trim_popa'], ar=['ar'], lemes=['leme_proa', 'leme_popa'],
              helice=['helice'], sonar=['sonar'])


class Partes(Cena):
    def preparar(self):
        self.slot = self.dur / len(PECAS)

    def desenhar(self, tela, t, tg):
        S = SUB_V if VERTICAL else SUB_G
        k_at = min(len(PECAS) - 1, int(t / self.slot))
        nome = PECAS[k_at][0]
        u = t - k_at * self.slot
        cam = 8.0
        D.mar(tela, cam, t)
        D.neve(tela, cam, t * 1.5, t)
        cx = cx_de('partes', 150) - int(320 * (1 - ease(t / 1.5)))
        cy = 112 + math.sin(t * 1.1) * 1.2
        lastro = .55 * math.sin(min(1, u / 5.0) * math.pi) if nome == 'lastro' else 0.0
        trim = (.5 + .3 * math.sin(u * 1.2), .5 - .3 * math.sin(u * 1.2)) if nome == 'ajuste' else (.5, .5)
        est = dict(corte=True, lastro=lastro, trim=trim, ajuste=.4, sopro=nome == 'ar',
                   transf=(1 if math.cos(u * 1.2) > 0 else -1) if nome == 'ajuste' else 0,
                   lemes=14 * math.sin(u * 2.2) if nome == 'lemes' else 0.0,
                   helice=t * (9 if nome == 'helice' else 1.0), respiros=nome == 'lastro')
        S.desenhar(tela, cx, cy, 0, est, t)
        if nome == 'helice':
            hx, hy = S.tela_xy('helice', cx, cy)
            bolhas(tela, hx - 4, hy - 4, t, sobe=30, n=10, vel=1.8, abre=12)
        if nome == 'sonar':
            sx, sy = S.tela_xy('sonar', cx, cy)
            for j in range(3):
                r = ((t * 40 + j * 22) % 66) + 4
                arco(tela, sx + 2, sy, r, -40, 40, CIANO if r < 40 else ACO2)
        if nome == 'casco' and int(t * 3) % 2 == 0:
            a, b = S.RESIST
            x0, y0 = cx + a * S.L, cy - S.R
            tela.ret_vazado(int(x0) - 1, int(y0) - 1, int((b - a) * S.L) + 3, int(S.D) + 3, AMARELO)
        if VERTICAL:
            rot = PECAS[k_at][1]
            lx = x_corte('partes') + 90
            rotulo(tela, rot, lx, 30, AMARELO, centro=True)
            for p in PONTOS[nome]:
                fio(tela, lx, 40, *S.tela_xy(p, cx, cy))
            return
        fundo_painel(tela)
        for k, (nm, rot, desc) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 8 + k * 28
            atual = k == k_at
            tela.ret(PX0 - 2, y + 1, 5, 5, AMARELO if atual else ACO1)
            tit(tela, rot, y, AMARELO if atual else ACO2, 9, PX0 + 8)
            if atual:
                tit(tela, desc, y + 11, BRANCO, 9, PX0 + 8)
                if u > .4:
                    for p in PONTOS[nm]:
                        fio(tela, PX0 - 4, y + 4, *S.tela_xy(p, cx, cy))

    def sons(self, fx):
        bolhas_som(fx, self.t0, self.t0 + self.dur, 1.2, .025, 4)
        for k in range(len(PECAS)):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + k * self.slot + .4, .15)
        s5 = self.t0 + 5 * self.slot
        helice_som(fx, s5, s5 + self.slot, lambda t: 9 / (2 * math.pi), .03)
        s6 = self.t0 + 6 * self.slot
        for j in range(4):
            fx.put(fx.sino(93, .5), s6 + .5 + j * 1.65, .08)


# ============================================================ mergulho
class Mergulho(Cena):
    T_ABRE, T_CHEIO, T_AJ0, T_AJ1 = 7.2, 26.0, 35.3, 38.3

    def f(self, t): return rampa(t, [(self.T_ABRE + .3, 0.0), (self.T_CHEIO, 1.0)])
    def aj(self, t): return rampa(t, [(self.T_AJ0, .3), (self.T_AJ1, .7)])
    def W(self, t): return .9 + .1 * self.f(t) + .04 * (self.aj(t) - .3) / .4

    def preparar(self):
        self.sim = Vertical(self.W, self.dur, .9 * HM, HM)

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('mergulho', 140)
        aberto = t >= self.T_ABRE
        est = dict(corte=True, lastro=self.f(t), ajuste=self.aj(t), respiros=aberto and t < 30.0,
                   valvulas=aberto, helice=t * .8)
        ys, cy, cam = cena_vertical(tela, t, 'mergulho', self.sim, cx, est, 0.0, xoff=t * .4,
                                    regua_x=4)
        df = self.f(t + .05) - self.f(t - .05)
        if aberto and df > 0:
            k = min(1.0, df / .006)
            respiro_ar(tela, S, cx, cy, 0, ys, t, k)
            agua_entrando(tela, S, cx, cy, 0, t, forca_=k)
        D.superficie(tela, ys, t)
        zk, v = self.sim(t), self.sim.vel(t)
        if 7.0 <= t < 20.8:
            ya = 18 if ys is None or ys > 40 else ys + 6
            if t < 14.0:
                rotulo(tela, 'RESPIROS ABERTOS', cx, ya, AMARELO, centro=True)
                for n in ('respiro_proa', 'respiro_popa'): fio(tela, cx, ya + 10, *S.tela_xy(n, cx, cy))
            else:
                rotulo(tela, 'O AR SAI POR CIMA', cx, ya, BRANCO, centro=True)
                rotulo(tela, 'A ÁGUA ENTRA POR BAIXO', cx, min(186, cy + 30), MISTURA2, centro=True)
        if self.T_AJ0 - .3 <= t < 42 and not VERTICAL:
            x, y = S.tela_xy('ajuste', cx, cy)
            rotulo(tela, 'TANQUE DE AJUSTE', cx + 30, min(190, cy + 34), MISTURA2, centro=True)
            fio(tela, cx + 30, min(188, cy + 32), x, y + 3, MISTURA2)
        hud_v(tela, 'mergulho', [(f"PROFUNDIDADE {prof_txt(zk)}", AMARELO),
                                 (f"LASTRO {int(round(self.f(t) * 100))}% ÁGUA", MISTURA2)])
        if VERTICAL: return
        painel_sub(tela, t, zk, v, self.f(t), self.W(t), self.sim.emp(t),
                   extra=[('TANQUE DE AJUSTE', ACO3), (f"{int(round(self.aj(t) * 100))}% ÁGUA", MISTURA2)] if t >= 35 else ())

    def sons(self, fx):
        mar_som(fx, self.t0, self.t0 + 28)
        a = self.t0 + self.T_ABRE
        fx.put(tique(1500), a, .3); fx.put(tique(1100), a + .15, .25)
        fx.put(fx.chiado(self.T_CHEIO - self.T_ABRE - 1, 700, 4500, .3), a + .3, .07, .25)
        bolhas_som(fx, a + 4, self.t0 + self.T_CHEIO, 3, .04, 5)
        fx.put(fx.sino(76, 1.2), self.t0 + self.T_CHEIO + .5, .12)
        fx.put(zumbido(self.T_AJ1 - self.T_AJ0, 95), self.t0 + self.T_AJ0, .05)
        fx.put(tique(1200), self.t0 + 30.0, .2)


# ============================================================ equilíbrio (parado a 50 m)
class Equilibrio(Cena):
    def preparar(self):
        self.z_ini = None          # fundura em que o mergulho terminou (lida no 1º quadro)

    def eixo(self, t):
        if self.z_ini is None:
            cap = next(c for c in self.T.caps if c['id'] == 'mergulho')
            sim = CENA_INST['mergulho'].sim
            self.z_ini = sim(cap['dur']) - DM / 2
            self.v_ini = sim.vel(cap['dur'])
        # chega em 50 m freando (a velocidade de saída do mergulho vai a zero)
        T = 6.0
        d = 50.0 - self.z_ini
        u = min(1.0, t / T)
        return self.z_ini + d * (1 - (1 - u) ** 2) + .25 * math.sin(t * .9) * min(1, t / 8)

    def ang(self, t):
        return rampa(t, [(0, -1.0), (4.0, -5.0), (9.0, -5.0), (20.0, 0.0)]) + .3 * math.sin(t * .8)

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('equilibrio', 140)
        e = self.eixo(t)
        cam = e - 104 / PXM
        D.mar(tela, cam, t)
        D.neve(tela, cam, t * .2, t)
        if not VERTICAL: D.regua(tela, 4, cam, 10, 50)
        tf = rampa(t, [(0, .55), (4.0, .8), (9.0, .8), (20.0, .5)])
        a = self.ang(t)
        est = dict(corte=True, lastro=1.0, trim=(tf, 1.3 - tf - .3), ajuste=rampa(t, [(0, .7), (6, .3)]),
                   transf=1 if 9.0 <= t < 20.0 else 0, helice=t * .4)
        S.desenhar(tela, cx, 104, a, est, t)
        if 14.8 <= t < 21.6 or (7.8 <= t < 14.6 and not VERTICAL):
            for n, txt, dx in (('trim_proa', 'PROA', 40), ('trim_popa', 'POPA', -40)):
                x, y = S.tela_xy(n, cx, 104, a)
                rotulo(tela, txt, x + dx, 160, MISTURA2, centro=True)
                fio(tela, x + dx, 158, x, y + 4, MISTURA2)
        if 7.8 <= t < 14.6:
            x, y = S.tela_xy('sonar', cx, 104, a)
            seta_dir(tela, x + 6, y + 14, 0, 1, 16, VERMELHO)
            rotulo(tela, 'MAIS PESO', x - 4, y + 22, VERMELHO, centro='d')
        hud_v(tela, 'equilibrio', [(f"{milhar(e)} M", AMARELO),
                                   ('NIVELADO' if abs(a) < 1 else f"NARIZ {dec(a, 0)} GRAUS", BRANCO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PROFUNDIDADE', 9, ACO3, 9)
        tit(tela, f"{milhar(e)} M", 19, AMARELO, 26)
        tit(tela, 'PESO = EMPUXO', 50, AMARELO if t >= .5 else ACO3, 9)
        D.barra_forca(tela, PX0, 60, 160, .2, .25, VERMELHO, 'PESO', '')
        D.barra_forca(tela, PX0, 84, 160, .2, .25, VERDE, 'EMPUXO', '')
        tit(tela, 'NÍVEL', 110, ACO3, 9)
        D.nivel_bolha(tela, PX0 + 80, 128, 140, a)
        tit(tela, 'NIVELADO' if abs(a) < 1 else 'NARIZ PARA BAIXO', 140, VERDE if abs(a) < 1 else VERMELHO, 9)
        tit(tela, 'AJUSTE: PROA  POPA', 158, ACO3, 9)
        D.medidor_tanque(tela, PX0 + 62, 170, 26, 26, tf, None, t)
        D.medidor_tanque(tela, PX0 + 100, 170, 26, 26, 1 - tf, None, t)
        if 9.0 <= t < 20.0:
            seta(tela, PX0 + 96, 183, 1, 0, MISTURA2, 4) if int(t * 3) % 2 else None

    def sons(self, fx):
        fx.put(zumbido(11.0, 85), self.t0 + 9.0, .04)
        fx.put(fx.sino(79, 1.2), self.t0 + 21.8, .14)
        bolhas_som(fx, self.t0, self.t0 + self.dur, .7, .025, 6)


# ============================================================ subir
class Subir(Cena):
    T_FECHA, T_SOPRA0, T_SOPRA1, T_FIM0, T_FIM1 = 2.5, 8.5, 22.0, 33.0, 38.0

    def f(self, t):
        return rampa(t, [(self.T_SOPRA0, 1.0), (self.T_SOPRA1, .62), (self.T_FIM0, .62), (self.T_FIM1, 0.0)])

    def W(self, t): return .9 + .1 * self.f(t)

    def preparar(self):
        self.sim = Vertical(self.W, self.dur, 50 + DM / 2, HM)

    def soprando(self, t):
        return self.T_SOPRA0 <= t < self.T_SOPRA1 or self.T_FIM0 <= t < self.T_FIM1

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('subir', 140)
        est = dict(corte=True, lastro=self.f(t), ajuste=.3, respiros=t < self.T_FECHA, valvulas=True,
                   sopro=self.soprando(t), helice=t * .6)
        ys, cy, cam = cena_vertical(tela, t, 'subir', self.sim, cx, est, 0.0, xoff=t * .4, regua_x=4)
        if self.soprando(t):
            agua_entrando(tela, S, cx, cy, 0, t, para_fora=True)
        D.superficie(tela, ys, t)
        zk, v = self.sim(t), self.sim.vel(t)
        if t < 7.6:
            ya = 20 if ys is None else ys + 6
            rotulo(tela, 'RESPIROS FECHADOS' if t >= self.T_FECHA else 'RESPIROS', cx, ya, AMARELO, centro=True)
            for n in ('respiro_proa', 'respiro_popa'): fio(tela, cx, ya + 10, *S.tela_xy(n, cx, cy))
        elif t < 14.6:
            x, y = S.tela_xy('ar', cx, cy)
            rotulo(tela, 'AR COMPRIMIDO', cx - 30, 22, BRANCO, centro=True)
            fio(tela, cx - 30, 32, x, y)
        elif t < 21.6:
            rotulo(tela, 'A ÁGUA SAI POR BAIXO', cx, min(186, cy + 30), MISTURA2, centro=True)
        eixo = zk - DM / 2
        p_mar = 1 + max(0.0, eixo) / 10
        hud_v(tela, 'subir', [(f"PROFUNDIDADE {prof_txt(zk)}", AMARELO),
                              (f"LASTRO {int(round(self.f(t) * 100))}% ÁGUA", MISTURA2)])
        if VERTICAL: return
        extra = []
        if t >= 28.8:
            extra = [('MAR LÁ FORA:', ACO3), (f"{dec(p_mar, 1)} ATM" if zk >= HM - .3 else '1 ATM', AMARELO),
                     ('O AR PRECISA DE MAIS', BRANCO)]
        painel_sub(tela, t, zk, v, self.f(t), self.W(t), self.sim.emp(t), extra=extra)
        if t >= 7.8 and t < 28.8:
            u = 1 - .35 * min(1, max(0, (t - self.T_SOPRA0) / (self.T_SOPRA1 - self.T_SOPRA0)))
            D.manometro(tela, PX0 + 130, 170, 16, u, 1.0, 'AR', CIANO)
            tit(tela, 'GARRAFAS', 160, ACO3, 9)
            tit(tela, 'DE AR', 171, ACO3, 9)

    def sons(self, fx):
        fx.put(tique(1300), self.t0 + self.T_FECHA, .3); fx.put(tique(900), self.t0 + self.T_FECHA + .12, .25)
        fx.put(fx.chiado(self.T_SOPRA1 - self.T_SOPRA0, 250, 3000, .4), self.t0 + self.T_SOPRA0, .09, -.1)
        bolhas_som(fx, self.t0 + self.T_SOPRA0, self.t0 + self.T_SOPRA1, 6, .045, 7)
        fx.put(fx.chiado(self.T_FIM1 - self.T_FIM0, 250, 2500, .3), self.t0 + self.T_FIM0, .06)
        ts = np.arange(0, self.dur, .02)
        sup = next((t for t in ts if self.sim(t) < HM - .3), None)
        if sup:
            fx.put(fx.chiado(1.2, 400, 5000, .02), self.t0 + sup, .2)
            fx.put(fx.explosao(.8), self.t0 + sup, .12)
            mar_som(fx, self.t0 + sup, self.t0 + self.dur)


# ============================================================ lemes de profundidade
class Lemes(Cena):
    Z0 = 80.0

    def lemes(self, t):
        return rampa(t, [(7.8, 0), (8.8, -15), (14.8, -15), (15.8, 0), (21.8, 0), (22.8, 15), (28.0, 15),
                         (29.0, 0), (40.5, 0), (41.5, -15)])

    def vel(self, t):
        return rampa(t, [(0, 7.0), (35.8, 7.0), (41.0, .25)])

    def preparar(self):
        dt = .01
        self.ts = np.arange(0, self.dur + .2, dt)
        th, z, x = 0.0, self.Z0, 0.0
        ths, zs, xs = [], [], []
        for t in self.ts:
            v = self.vel(t)
            th += v * (.13 * self.lemes(t) - .16 * th) * dt
            z += -v * math.sin(math.radians(th)) * dt
            x += v * dt
            ths.append(th); zs.append(z); xs.append(x)
        self.th, self.z, self.x = np.array(ths), np.array(zs), np.array(xs)

    def it(self, arr, t): return float(np.interp(t, self.ts, arr))

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('lemes', 150)
        th, z, xo = self.it(self.th, t), self.it(self.z, t), self.it(self.x, t)
        cam = z - 104 / PXM
        D.mar(tela, cam, t)
        D.neve(tela, cam, xo, t)
        if not VERTICAL: D.regua(tela, 4, cam, 10, 50)
        v = self.vel(t)
        fase = self.it(self.x, t) * 1.8
        est = dict(corte=False, lemes=self.lemes(t), helice=fase)
        S.desenhar(tela, cx, 104, th, est, t)
        hx, hy = S.tela_xy('helice', cx, 104, th)
        if v > 1:
            bolhas(tela, hx - 6, hy - 3, t, sobe=14, n=8, vel=1.6, abre=16, seed=2)
            for k in range(6):                                      # rastro
                u = (t * 1.3 + k / 6) % 1.0
                tela.px(hx - 8 - u * 40, hy - 2 + math.sin(u * 7 + k) * 3, MISTURA2 if u < .5 else ACO2)
        # setas: água passando pelos lemes
        if 7.8 <= t < 29 or t >= 40:
            for n in ('leme_proa', 'leme_popa'):
                x, y = S.tela_xy(n, cx, 104, th)
                k = int(t * 4) % 2
                tela.anel(x, y, 6 + k, AMARELO, .5)
        if v > .8 and not VERTICAL:
            sx, sy = S.tela_xy('sonar', cx, 104, th)
            for j in range(3):
                u = (t * 2 + j / 3) % 1.0
                tela.ret(int(sx + 20 + 40 * (1 - u)), int(sy - 10 + j * 10), 6, 1, ACO2)
        hud_v(tela, 'lemes', [(f"PROFUNDIDADE {milhar(z)} M", AMARELO),
                              (f"LEMES {dec(self.lemes(t), 0)} GRAUS", BRANCO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PROFUNDIDADE', 9, ACO3, 9)
        tit(tela, f"{milhar(z)} M", 19, AMARELO, 26)
        tit(tela, 'LEMES', 52, ACO3, 9)
        # o leme visto de perto, girando
        lx, ly = PX0 + 34, 76
        ang = math.radians(self.lemes(t))
        dx, dy = math.cos(ang), -math.sin(ang)
        linha_grossa(tela, lx - dx * 16, ly - dy * 16, lx + dx * 22, ly + dy * 22, 7, PRETO)
        linha_grossa(tela, lx - dx * 16, ly - dy * 16, lx + dx * 22, ly + dy * 22, 5, ACO3)
        linha_grossa(tela, lx - dx * 16, ly - dy * 16, lx + dx * 22, ly + dy * 22, 1, ACO4)
        tela.disco(lx, ly, 2, PRETO)
        for j in range(3):
            u = (t * 1.5 * min(1, v / 3) + j / 3) % 1.0
            if v > .5: tela.ret(int(lx + 30 - u * 64), ly - 12 + j * 12, 5, 1, MISTURA2)
        tit(tela, f"{dec(self.lemes(t), 0)} GRAUS", 70, BRANCO, 9, PX0 + 72)
        tit(tela, 'NARIZ', 100, ACO3, 9)
        tit(tela, 'PARA BAIXO' if th < -1.5 else ('PARA CIMA' if th > 1.5 else 'RETO'), 111,
            VERMELHO if th < -1.5 else (VERDE if th > 1.5 else BRANCO), 9)
        tit(tela, 'VELOCIDADE', 130, ACO3, 9)
        tela.ret(PX0, 142, 160, 8, PRETO)
        n = int(158 * v / 7.0)
        tela.ret(PX0 + 1, 143, n, 6, CIANO); tela.ret(PX0 + 1, 143, n, 1, BRANCO)
        tit(tela, 'HÉLICE GIRANDO' if v > 6.9 else ('HÉLICE PARADA' if t > 36 else 'HÉLICE'), 154, ACO3, 9)
        if 28.8 <= t < 35.6:
            # avião com o profundor (genérico, de lado)
            ax, ay = PX0 + 88, 182
            poligono(tela, [(ax - 30, ay), (ax + 26, ay - 2), (ax + 30, ay + 2), (ax - 28, ay + 4)], ACO3)
            poligono(tela, [(ax - 30, ay), (ax - 34, ay - 10), (ax - 26, ay - 10), (ax - 22, ay)], ACO2)
            a2 = math.radians(14 * math.sin(t * 2.5))
            linha_grossa(tela, ax - 34, ay + 1, ax - 34 - 10 * math.cos(a2), ay + 1 + 10 * math.sin(a2), 2, AMARELO)
            tela.ret(ax - 6, ay + 1, 14, 2, ACO2)
            tit(tela, 'PROFUNDOR', 160, AMARELO, 9, PX0 + 96)

    def sons(self, fx):
        helice_som(fx, self.t0, self.t0 + self.dur, lambda t: self.vel(t) * 1.8 / (2 * math.pi), .035)
        for ta in (7.8, 15.0, 21.8, 28.2, 40.5):
            fx.put(tique(900), self.t0 + ta, .2)
        bolhas_som(fx, self.t0, self.t0 + 36, 2.0, .025, 8)


# ============================================================ pressão
class Pressao(Cena):
    def eixo(self, t):
        s0 = .9 * HM - DM / 2 + .15 * math.sin(t * 1.3)
        return rampa(t, [(7.8, s0), (14.0, 30.0), (21.0, 100.0), (28.4, 104.0), (33.5, 300.0), (54, 302.0)])

    def ang(self, t):
        return rampa(t, [(7.0, 0), (8.5, -12), (20.0, -12), (21.5, -1), (28.0, -1), (29.0, -14),
                         (32.5, -14), (34.0, 0)])

    def desenhar(self, tela, t, tg):
        S = sub()
        cx = cx_de('pressao', 150)
        e = self.eixo(t)
        cam = camera(e, 104, 70)
        ys = D.mar(tela, cam, t)
        D.neve(tela, cam, t * 3, t, ys)
        if not VERTICAL:
            D.regua(tela, 4, cam, 10, 50 if e > 60 else 10, ysurf=ys)
            # atmosferas na régua
            for d in range(0, 401, 10):
                y = (d - cam) * PXM
                if 0 <= y < PALCO_H and (d % 50 == 0 or (e < 60 and d <= 50)):
                    tela.texto(f"{milhar(1 + d / 10)} ATM", 60, int(y) - 3, CIANO, tam=9, contorno=PRETO)
        cy = (e - cam) * PXM
        a = self.ang(t)
        corte = t >= 42.8
        est = dict(corte=corte, lastro=1.0 if t > 8 else 0.0, helice=t * 5, lemes=-10 if a < -3 else 0)
        S.desenhar(tela, cx, cy, a, est, t)
        D.superficie(tela, ys, t)
        agua = max(0.0, e) / 10.0
        if t >= 28.8 or corte:
            # a água apertando o casco por todos os lados
            k = 1 + .15 * math.sin(t * 5)
            comp = 6 + 10 * min(1, agua / 30) * k
            for j in range(14):
                ang = 2 * math.pi * j / 14
                rx, ry = S.L * .5 + 10, S.R + 10
                x, y = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
                seta_dir(tela, x - math.cos(ang) * 2, y - math.sin(ang) * 2, -math.cos(ang), -math.sin(ang),
                         comp, AMARELO, 1, 3)
        if corte:
            etiqueta(tela, 'DENTRO: 1 ATM', cx, int(cy) - 4, VERDE)
            if not VERTICAL: etiqueta(tela, f"FORA: {milhar(1 + agua)} ATM", cx, 14, AMARELO, 17)
        if 28.0 < t < 33.5 and not VERTICAL:
            rotulo(tela, '(TEMPO ACELERADO)', 90, 196, ACO2)
        hud_v(tela, 'pressao', [(f"{milhar(e) if t > 8 else '0'} M", AMARELO),
                                (f"ÁGUA: +{milhar(agua) if t > 8 else '0'} ATM", CIANO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PROFUNDIDADE', 9, ACO3, 9)
        tit(tela, prof_txt(e + DM / 2) if t < 8 else f"{milhar(e)} M", 19 if t >= 8 else 21, AMARELO, 26 if t >= 8 else 17)
        tit(tela, 'PRESSÃO LÁ FORA', 50, ACO3, 9)
        ag = agua if t >= 8 else 0.0
        tit(tela, f"AR 1 + ÁGUA {milhar(ag)}", 62, BRANCO, 9)
        tit(tela, f"= {milhar(1 + ag)} ATM", 74, CIANO, 17)
        D.manometro(tela, PX0 + 140, 82, 20, 1 + ag, 32, None, VERMELHO)
        if t >= 14.8:
            tit(tela, 'EM CADA CENTÍMETRO', 106, ACO3, 9)
            tit(tela, 'QUADRADO, SÓ DA ÁGUA:', 117, ACO3, 9)
            kg = 1.03 * ag
            tit(tela, f"CERCA DE {milhar(kg)} KG", 130, VERMELHO, 9)
            D.pesinhos(tela, PX0 + 4, 200, round(kg))
            if round(kg) < 1:
                D.pesinhos(tela, PX0 + 4, 200, 1, ACO2)
                tit(tela, '1 ATM = ~1 KG', 186, ACO3, 9, PX0 + 50)

    def sons(self, fx):
        mar_som(fx, self.t0, self.t0 + 12)
        fx.put(tique(1500), self.t0 + 7.8, .25)
        bolhas_som(fx, self.t0 + 8, self.t0 + 14, 3, .035, 9)
        for k, ta in enumerate((33.8, 37.5, 41.0, 45.5, 50.0)):
            fx.put(rangido(.7, 65 + k * 4), self.t0 + ta, .12, -.3 + k * .15)
        helice_som(fx, self.t0 + 8, self.t0 + self.dur, lambda t: 5 / (2 * math.pi), .025)


# ============================================================ por que redondo
class Casco(Cena):
    R0 = 30

    def p(self, t): return rampa(t, [(2.5, 0.0), (14.0, 1.0)])

    def desenhar(self, tela, t, tg):
        cam = 260.0
        D.mar(tela, cam, t, raios=False)
        D.neve(tela, cam, t * .5, t)
        p = self.p(t)
        xq, xc = (105, 195) if VERTICAL else (85, 215)
        cy = 88
        if t < 21.6:
            self.quadrado(tela, xq, cy, t, p)
            self.redondo(tela, xc, cy, t, p, oval=0.0)
            rotulo(tela, 'QUADRADO', xq, cy + 48, ACO4 if t < 14.8 else ACO1, centro=True)
            rotulo(tela, 'REDONDO', xc, cy + 48, VERDE if t >= 14.8 else ACO4, centro=True)
            if t >= 11.5:
                rotulo(tela, 'ENTORTOU', xq, cy - 50, VERMELHO, centro=True)
            if t >= 14.8:
                rotulo(tela, 'AGUENTA', xc, cy - 50, VERDE, centro=True)
        elif t < 28.6:
            self.tubo(tela, t - 21.8, cx=150 if not VERTICAL else 150)
        else:
            ov = suave((t - 28.8) / 2.0)
            self.redondo(tela, 150, cy, t, 1.0, oval=ov)
            if ov > .5:
                rotulo(tela, '(DESENHO EXAGERADO)', 150, cy + 50, ACO2, centro=True)
                rotulo(tela, '2,5 CM', 150 + self.R0 + 18, cy - 4, AMARELO)
        hud_v(tela, 'casco', [('PRESSÃO DE FORA', AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PRESSÃO', 9, ACO3, 9)
        tela.ret(PX0, 22, 160, 8, PRETO)
        tela.ret(PX0 + 1, 23, int(158 * p), 6, AMARELO); tela.ret(PX0 + 1, 23, int(158 * p), 1, CHAMA0)
        if t < 21.6:
            tit(tela, 'QUADRADO', 44, ACO3, 9)
            tit(tela, 'PAREDES ENTORTAM' if t >= 7.8 else '...', 56, VERMELHO if t >= 7.8 else ACO1, 9)
            tit(tela, 'REDONDO', 80, ACO3, 9)
            tit(tela, 'SÓ APERTA, NÃO DOBRA' if t >= 14.8 else '...', 92, VERDE if t >= 14.8 else ACO1, 9)
        elif t < 28.6:
            tit(tela, 'ANÉIS DE AÇO', 44, AMARELO, 17)
            tit(tela, 'REFORÇAM O TUBO', 66, BRANCO, 9)
            tit(tela, 'CONTRA ENTORTAR', 78, BRANCO, 9)
        else:
            ov = suave((t - 28.8) / 2.0)
            tit(tela, 'FORA DO REDONDO', 44, AMARELO, 9)
            tit(tela, 'RESISTÊNCIA', 64, ACO3, 9)
            r = 1 - .32 * ov
            tela.ret(PX0, 76, 160, 8, PRETO)
            tela.ret(PX0 + 1, 77, int(158 * r), 6, VERDE if r > .9 else VERMELHO)
            tit(tela, f"{int(round(r * 100))}%" if ov < .99 else 'MENOS DE 70%', 90, VERMELHO if ov > .5 else VERDE, 9)

    def setas_em_volta(self, tela, pts_normais, p, t):
        comp = 4 + 9 * p * (1 + .12 * math.sin(t * 6))
        for x, y, nx, ny in pts_normais:
            seta_dir(tela, x + nx * 3, y + ny * 3, -nx, -ny, comp, AMARELO, 1, 3)

    def quadrado(self, tela, cx, cy, t, p):
        R = self.R0
        b = 14 * max(0.0, p - .35) ** 1.3 / .65 ** 1.3
        if t > 11.5: b = 14 + 2.0 * math.sin(t * 9) * math.exp(-(t - 11.5))
        pts = []
        cantos = [(-R, -R), (R, -R), (R, R), (-R, R)]
        for k in range(4):
            (ax, ay), (bx, by) = cantos[k], cantos[(k + 1) % 4]
            nx, ny = (ay + by) / 2 / R, -(ax + bx) / 2 / R
            nx, ny = (0, -1) if k == 0 else (1, 0) if k == 1 else (0, 1) if k == 2 else (-1, 0)
            for j in range(10):
                u = j / 10
                off = b * math.sin(u * math.pi)
                pts.append((cx + ax + (bx - ax) * u - nx * off, cy + ay + (by - ay) * u - ny * off))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0), (0, -2), (0, 2)):
            poligono(tela, [(x + dx, y + dy) for x, y in pts], PRETO)
        poligono(tela, [(x + (1 if x < cx else -1) * 0, y) for x, y in pts], ACO2)
        inner = [(cx + (x - cx) * .86, cy + (y - cy) * .86) for x, y in pts]
        poligono(tela, inner, FUNDO2)
        dither(tela, cx - 4, cy - 4, 8, 8, FUNDO2, FUNDO3)
        if t > 11.5:
            for j in range(3):
                x0 = cx - R + 8 + j * 20
                tela.linha(x0, cy - R + b + 2, x0 + 4, cy - R + b + 7, VERMELHO)
        nrm = []
        for k, (nx, ny) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
            for j in (-.5, 0, .5):
                if k % 2 == 0: nrm.append((cx + j * R * 1.4, cy + ny * (R + 2), nx, ny))
                else: nrm.append((cx + nx * (R + 2), cy + j * R * 1.4, nx, ny))
        self.setas_em_volta(tela, nrm, p, t)

    def redondo(self, tela, cx, cy, t, p, oval=0.0):
        R = self.R0
        n = 48
        pts, inner = [], []
        for k in range(n):
            a = 2 * math.pi * k / n
            rx, ry = R * (1 + .12 * oval), R * (1 - .12 * oval)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
            inner.append((cx + (rx - 5) * math.cos(a), cy + (ry - 5) * math.sin(a)))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            poligono(tela, [(x + dx, y + dy) for x, y in pts], PRETO)
        poligono(tela, pts, ACO2)
        brilho = t >= 14.8 and oval == 0 and int(t * 3) % 2 == 0
        arco(tela, cx, cy, R - 1, 30, 150, ACO4 if not brilho else VERDE, .8)
        poligono(tela, inner, FUNDO2)
        dither(tela, cx - R + 8, cy - 3, 2 * R - 16, 6, FUNDO2, FUNDO3)
        if oval > 0:
            for k in range(0, 72, 2):
                a = 2 * math.pi * k / 72
                tela.px(cx + (R + 3) * math.cos(a), cy + (R + 3) * math.sin(a), AMARELO)
        nrm = []
        for k in range(12):
            a = 2 * math.pi * k / 12
            rx, ry = R * (1 + .12 * oval), R * (1 - .12 * oval)
            nrm.append((cx + (rx + 2) * math.cos(a), cy + (ry + 2) * math.sin(a), math.cos(a), math.sin(a)))
        self.setas_em_volta(tela, nrm, p, t)

    def tubo(self, tela, u, cx):
        """O casco resistente cortado ao comprido, com os anéis aparecendo."""
        x0, x1 = cx - 120, cx + 120
        if VERTICAL: x0, x1 = cx - 82, cx + 82
        yt, yb = 56, 124
        tela.ret(x0, yt - 2, x1 - x0, yb - yt + 4, PRETO)
        dither(tela, x0, yt + 3, x1 - x0, yb - yt - 6, FUNDO3, FUNDO2)
        tela.ret(x0, yt - 1, x1 - x0, 4, ACO2); tela.ret(x0, yt - 1, x1 - x0, 1, ACO4)
        tela.ret(x0, yb - 3, x1 - x0, 4, ACO1)
        n = int((x1 - x0 - 16) / 14)
        vis = int(u / .25)
        for k in range(min(n, vis)):
            x = x0 + 10 + k * 14
            for y in range(yt + 3, yb - 3):
                v = (y - yt) / (yb - yt)
                dx = int(round(3 * math.sin(v * math.pi)))
                tela.px(x + dx, y, ACO3 if v < .5 else ACO2)
                tela.px(x + dx + 1, y, ACO1)
        rotulo(tela, 'ANÉIS', cx, yb + 12, AMARELO, centro=True)
        fio(tela, cx, yb + 10, x0 + 10 + 14 * min(n - 1, max(0, vis - 1)) + 2, yb - 8)
        for j in range(5):
            x = x0 + 20 + j * (x1 - x0 - 40) / 4
            seta_dir(tela, x, yt - 4, 0, 1, 10, AMARELO, 1, 3)
            seta_dir(tela, x, yb + 3, 0, -1, 10, AMARELO, 1, 3)

    def sons(self, fx):
        for k, ta in enumerate((8.0, 10.0, 11.5)):
            fx.put(rangido(.5, 80 - k * 8), self.t0 + ta, .14)
        fx.put(fx.explosao(.8), self.t0 + 11.5, .2)
        fx.put(fx.sino(79), self.t0 + 14.8, .14)
        for k in range(14):
            fx.put(tique(1000 + k * 30), self.t0 + 21.8 + k * .25, .08)


# ============================================================ até onde ele desce
class Limite(Cena):
    Y0, Y1, MAXM = 16, 192, 500.0

    def y(self, m): return self.Y0 + m / self.MAXM * (self.Y1 - self.Y0)

    def prof(self, t):
        return rampa(t, [(7.8, 0), (10.0, 100), (11.0, 100), (13.5, 200), (15.5, 200), (19.0, 330),
                         (22.0, 300), (35.5, 300), (40.0, 470)])

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        x1 = W if VERTICAL else 298
        yy, xx = np.mgrid[0:PALCO_H, 0:x1]
        m = (yy - self.Y0) / (self.Y1 - self.Y0) * self.MAXM
        lev = np.clip(np.interp(m, [-1, 0, 40, 150, 350, 500], [-1, 0, 1, 2, 3, 3.6]), -1, 3.99)
        i = np.floor(np.maximum(lev, 0)).astype(int); f = np.maximum(lev, 0) - i
        idx = np.clip(i + (D.B4[yy % 4, xx % 4] < f), 0, 4)
        cor = D.RAMPA[idx]
        cor[m < 0] = FUNDO2
        tela.buf[0:PALCO_H, 0:x1] = cor
        D.superficie(tela, self.Y0, t, 0, x1)
        xs = 40
        # régua
        for d in range(0, 501, 50):
            y = int(self.y(d))
            tela.ret(xs - (6 if d % 100 == 0 else 3), y, 6 if d % 100 == 0 else 3, 1, BRANCO)
            if d % 100 == 0:
                tela.texto(f"{d} M", xs - 8, y - 3, BRANCO, tam=9, centro='d', contorno=PRETO)
        tela.ret(xs, self.Y0, 1, self.Y1 - self.Y0, ACO3)
        xr = 120
        def faixa(m0, m1, cor, txt, ta, lado=0):
            if t < ta: return
            a, b = int(self.y(m0)), int(self.y(m1))
            if b - a < 2:
                tela.ret(xs + 2, a, xr - xs + 140, 1, cor)
            else:
                dither(tela, xs + 2, a, 70, b - a, cor, FUNDO2)
                tela.ret(xs + 2, a, 70, 1, cor); tela.ret(xs + 2, b, 70, 1, cor)
            rotulo(tela, txt, xs + 6 + lado, a - 10 if b - a < 2 else a + 2, cor)
        faixa(100, 100, AMARELO, 'PRIMEIRA GUERRA: ATÉ 100 M', 7.8)
        faixa(200, 200, LARANJA, 'SEGUNDA GUERRA: ATÉ 200 M', 10.5)
        faixa(250, 400, VERDE, 'AÇO, HOJE: 250 A 400 M', 14.8)
        if t >= 17.0 and not VERTICAL:
            rotulo(tela, 'TITÂNIO: TESTE A 1.000 M', 150, 182, CIANO, centro=True)
            seta(tela, 150, 196, 0, 1, CIANO, 5)
        # o exemplo: teste e projeto
        if t >= 21.8:
            yt = int(self.y(300))
            tela.ret(xs + 2, yt, 250 if not VERTICAL else 170, 1, BRANCO)
            rotulo(tela, 'TESTE (EXEMPLO)', 210 if not VERTICAL else 190, yt - 10, BRANCO, centro=True)
        if t >= 28.8:
            yp = int(self.y(450))
            tela.ret(xs + 2, yp, 250 if not VERTICAL else 170, 1, VERMELHO)
            rotulo(tela, 'PROJETO', 210 if not VERTICAL else 190, yp - 10, VERMELHO, centro=True)
            xb = 252 if not VERTICAL else 214
            tela.ret(xb, int(self.y(0)) + 2, 1, yp - int(self.y(0)) - 2, ACO3)
            tela.ret(xb + 4, int(self.y(0)) + 2, 1, yt - int(self.y(0)) - 2, AMARELO)
            rotulo(tela, '2/3', xb + 8, int(self.y(150)), AMARELO)
        if t >= 35.8:
            yp = int(self.y(450))
            k = int(t * 4) % 2
            dither(tela, xs + 2, yp + 1, 250 if not VERTICAL else 170, self.Y1 - yp, VERMELHO if k else BRASA, FUNDO)
            rotulo(tela, 'ESMAGAMENTO', 160 if not VERTICAL else 150, yp + 4, BRANCO, centro=True)
            etiqueta(tela, 'SEGREDO', 180 if not VERTICAL else 150, 40, VERMELHO, 17)
        # o submarino descendo a régua
        pm = self.prof(t)
        ys = self.y(pm)
        sx = 175 if not VERTICAL else 150
        ang = -10 if self.prof(t + .1) > pm + .2 else 0
        crush = t >= 39.0
        SUB_P.desenhar(tela, sx, ys, ang, dict(helice=t * 4), t)
        if crush and int(t * 6) % 2 == 0:
            tela.anel(sx, ys, 30, VERMELHO, .6)
        tela.ret(xs - 2, int(ys), 5, 1, AMARELO)
        if not VERTICAL:
            rotulo(tela, f"{milhar(pm)} M", sx + 60, int(ys) - 4, AMARELO)
        hud_v(tela, 'limite', [(f"{milhar(pm)} M", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'LIMITES', 9, AMARELO, 17)
        itens = [('TESTE', 'USO NORMAL, SEM GUERRA', 21.8, BRANCO),
                 ('PROJETO', 'A CONTA DO CASCO', 28.8, VERMELHO),
                 ('ESMAGAMENTO', 'O CASCO CEDE', 35.8, VERMELHO)]
        for k, (a, b, ta, cor) in enumerate(itens):
            y = 36 + k * 30
            on = t >= ta
            tit(tela, a, y, cor if on else ACO1, 9)
            tit(tela, b, y + 11, ACO3 if on else FUNDO3, 9)
        if t >= 28.8:
            tit(tela, 'TESTE = 2/3 DO PROJETO', 134, AMARELO, 9)
            tit(tela, '(MARINHA DOS EUA)', 145, ACO3, 9)
        if t >= 35.8:
            tit(tela, 'NÚMERO DE CADA UM:', 168, ACO3, 9)
            tit(tela, 'SEGREDO', 180, VERMELHO, 17)

    def sons(self, fx):
        for ta, m in ((7.8, 72), (10.5, 74), (14.8, 77), (21.8, 79), (28.8, 81)):
            fx.put(fx.blip(m, .1), self.t0 + ta, .13)
        fx.put(rangido(.9, 60), self.t0 + 39.0, .16)
        fx.put(fx.sino(70, 1.0), self.t0 + 35.8, .1)


# ============================================================ sonar
class Sonar(Cena):
    LENTO = 4.0                 # câmera lenta: 1 s de som = 4 s na tela
    T_DEMO, T_PING = 8.5, 15.0

    def geo(self):
        if VERTICAL:
            xc = x_corte('sonar')
            return xc + 55, 112, xc + 165       # submarino, y, rocha
        return 75, 112, 280

    def desenhar(self, tela, t, tg):
        cam = 250.0
        D.mar(tela, cam, t, raios=False)
        D.neve(tela, cam, t * .6, t)
        sx, sy, rx = self.geo()
        S = SUB_P
        # rocha (monte submarino)
        pts = [(rx - 18, PALCO_H), (rx - 10, 120), (rx - 2, 96), (rx + 10, 60), (rx + 30, 40), (rx + 60, 30),
               (rx + 80, PALCO_H)]
        poligono(tela, [(x + 1, y + 1) for x, y in pts], PRETO)
        poligono(tela, pts, FUNDO3)
        for k in range(30):
            x = rx - 6 + (k * 37) % 70; y = 50 + (k * 53) % 150
            tela.px(x + (y - 50) * 0 + max(0, 30 - y // 4), y, ACO0)
        S.desenhar(tela, sx, sy, 0, dict(helice=t * 3), t)
        bx, by = S.tela_xy('sonar', sx, sy)
        dist_px = rx - 6 - bx
        v_px = dist_px / self.LENTO                      # px por segundo de tela (1 s real = LENTO)
        # escuro: só o que o sonar "acende"
        if self.T_DEMO <= t < self.T_PING - .5:
            r = (t - self.T_DEMO) * v_px
            if r < dist_px + 10: arco(tela, bx + 2, by, r, -55, 55, CIANO)
            yb = sy + 34
            tela.ret(int(bx), yb, int(dist_px), 1, ACO2)
            tela.ret(int(bx), yb - 2, 1, 5, ACO2); tela.ret(int(bx + dist_px), yb - 2, 1, 5, ACO2)
            rotulo(tela, '1.500 M', bx + dist_px / 2, yb + 4, BRANCO, centro=True)
        if t >= self.T_PING:
            u = t - self.T_PING
            for j in range(3):
                r = u * v_px - j * 5
                if 0 < r < dist_px + 4:
                    arco(tela, bx + 2, by, r, -55, 55, CIANO if j == 0 else ACO2)
            ue = u - self.LENTO
            if ue > 0:
                if ue < .8:
                    tela.disco(rx - 6, by, 4 + ue * 4, CIANO)
                for j in range(3):
                    r = ue * v_px - j * 5
                    if 0 < r < dist_px + 4:
                        arco(tela, rx - 6, by, r, 125, 235, AMARELO if j == 0 else LATAO)
            if ue > self.LENTO and ue < self.LENTO + 3 and int(t * 4) % 2 == 0:
                tela.anel(bx, by, 8, AMARELO, .6)
        if t >= 28.8:
            # passivo: barulho de hélice de longe chegando
            ox, oy = (rx + 40, 18) if not VERTICAL else (rx + 5, 20)
            u = t - 28.8
            for j in range(4):
                r = ((u * 24 + j * 14) % 70) + 3
                arco(tela, ox, oy, r, 180, 300, ACO3)
            tela.disco(ox, oy, 2.5, ACO2)
        cor_txt = CIANO
        if not VERTICAL and 8 < t < self.T_PING - .5:
            rotulo(tela, f"CÂMERA LENTA ({int(self.LENTO)}X)", 150, 8, ACO3, centro=True)
        if not VERTICAL and t >= self.T_PING and t < 28.8:
            rotulo(tela, f"CÂMERA LENTA ({int(self.LENTO)}X)", 150, 8, ACO3, centro=True)
        real = max(0.0, min(2.0, (t - self.T_PING) / self.LENTO))
        hud_v(tela, 'sonar', [(f"ECO: {dec(real, 1)} S" if t >= self.T_PING else 'SOM: 1.500 M/S', cor_txt)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'SONAR', 9, AMARELO, 17)
        tit(tela, 'SOM NA ÁGUA DO MAR', 32, ACO3, 9)
        tit(tela, '1.500 M/S', 43, CIANO, 17)
        if t >= self.T_PING:
            tit(tela, 'IDA E VOLTA', 70, ACO3, 9)
            tit(tela, f"{dec(real, 1)} S", 81, AMARELO, 26)
            if real >= 2.0:
                tit(tela, '1.500 X 2 / 2', 112, BRANCO, 9)
                tit(tela, '= 1.500 M', 123, AMARELO, 17)
        if t >= 28.8:
            tit(tela, 'ATIVO: REVELA', 156, VERMELHO, 9)
            tit(tela, 'PASSIVO: SÓ ESCUTA', 170, VERDE, 9)

    def sons(self, fx):
        fx.put(fx.sino(91, 1.0), self.t0 + self.T_DEMO, .08)
        fx.put(fx.sino(93, 1.4), self.t0 + self.T_PING, .16)
        fx.put(fx.sino(93, 1.4), self.t0 + self.T_PING + 2 * self.LENTO, .06, .3)
        for k in range(8):
            fx.put(fx.pulso(), self.t0 + 29.0 + k * .9, .03, .6)
        bolhas_som(fx, self.t0, self.t0 + self.dur, .5, .02, 10)


# ============================================================ resumo
class Resumo(Cena):
    CX = [64, 178, 292, 406]
    NOMES = [('ÁGUA ENTRA', 'DESCE'), ('PESO = EMPUXO', 'PARA'), ('AR EMPURRA', 'SOBE'), ('CASCO REDONDO', '+1 ATM / 10 M')]
    TS = [0.5, 7.3, 14.7, 22.1]

    def desenhar(self, tela, t, tg):
        cam = 30.0
        D.mar(tela, cam, t)
        D.neve(tela, cam, t * .5, t)
        k_at = max(k for k, ta in enumerate(self.TS) if t >= ta) if t >= self.TS[0] else 0
        for k in range(4):
            cx = self.CX[k]
            aceso = k == k_at
            cor = AMARELO if aceso else ACO1
            painel(tela, cx - 52, 18, 104, 150, borda=cor)
            self._icone(tela, k, cx, 70, t, aceso)
            tela.texto(self.NOMES[k][0], cx, 132, AMARELO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(self.NOMES[k][1], cx, 146, BRANCO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(str(k + 1), cx - 44, 24, cor, tam=9)
        tela.texto('O SUBMARINO MUDA O PRÓPRIO PESO', W // 2, 184, AMARELO, tam=9, centro=True, contorno=PRETO)

    def _icone(self, tela, k, cx, cy, t, aceso):
        x0, y0, w, h = cx - 44, cy - 38, 88, 86
        dither(tela, x0, y0, w, h, FUNDO3, FUNDO2)
        tela.ret(x0, y0 + 10, w, 1, MISTURA2)
        u = (t * .3) % 1.0 if aceso else .5
        if k == 0:
            y = y0 + 24 + u * 46
            SUB_M.desenhar(tela, cx, y, -4, dict(corte=False, helice=t), t)
            seta_dir(tela, cx + 40, y + 10, 0, 1, 10, VERMELHO, 1, 3)
            D.medidor_tanque(tela, x0 + 4, y0 + 18, 8, 24, .2 + .8 * u, None, t)
        elif k == 1:
            y = cy + 4 + math.sin(t * 1.5) * .8
            SUB_M.desenhar(tela, cx, y, 0, dict(helice=t), t)
            D.nivel_bolha(tela, cx, y0 + 76, 50, 0)
        elif k == 2:
            y = y0 + 70 - u * 46
            SUB_M.desenhar(tela, cx, y, 4, dict(helice=t), t)
            bolhas(tela, cx - 20, y + 8, t, sobe=20, n=5)
            bolhas(tela, cx + 22, y + 8, t, sobe=20, n=5, seed=3)
            seta_dir(tela, cx + 40, y - 12, 0, -1, 10, VERDE, 1, 3)
        else:
            R = 20
            tela.disco(cx, cy + 6, R + 1, PRETO); tela.disco(cx, cy + 6, R, ACO2); tela.disco(cx, cy + 6, R - 4, FUNDO2)
            arco(tela, cx, cy + 6, R - 1, 30, 150, ACO4, .8)
            pp = 1 + (.2 * math.sin(t * 6) if aceso else 0)
            for j in range(8):
                a = 2 * math.pi * j / 8
                seta_dir(tela, cx + (R + 3) * math.cos(a), cy + 6 + (R + 3) * math.sin(a), -math.cos(a), -math.sin(a),
                         8 * pp, AMARELO, 1, 3)

    def sons(self, fx):
        for k, ta in enumerate(self.TS):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + ta, .14)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            cam = -150 / PXM
            ys = D.mar(tela, cam, t)
            u = t - RM.OUTRO_S
            x = -120 + u * 45
            zk = .9 * HM + .15 * math.sin(t * 1.3)
            SUB.desenhar(tela, x, ys + (zk - DM / 2) * PXM, 0, dict(helice=t * 3), t)
            D.superficie(tela, ys, t)
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 30, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 52, AMARELO, tam=9, centro=True, contorno=PRETO)

    def fim_vinheta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# longo.py chama `pos` (RGB pronto) quando a cena tem esse método: só o Fim usa.
Fim.pos = Fim.fim_vinheta

CENAS = dict(gancho=Gancho, titulo=Titulo, arquimedes=Arquimedes, partes=Partes, mergulho=Mergulho,
             equilibrio=Equilibrio, subir=Subir, lemes=Lemes, pressao=Pressao, casco=Casco, limite=Limite,
             sonar=Sonar, resumo=Resumo, fim=Fim)

# o Equilíbrio começa onde o Mergulho terminou: as cenas se registram aqui
CENA_INST = {}
for _nome, _cls in list(CENAS.items()):
    _orig = _cls.preparar

    def _prep(self, _orig=_orig, _nome=_nome):
        CENA_INST[_nome] = self
        _orig(self)
    _cls.preparar = _prep


if __name__ == '__main__':
    import ep14_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if len(sys.argv) > 3:
            c = next(c for c in trilha.caps if c['id'] == sys.argv[3])
            fr = [float(x) for x in sys.argv[4:]] or [float(x) for x in os.environ.get('FR', '.1,.3,.5,.7,.9').split(',')]
            ts = [c['t0'] + c['dur'] * f for f in fr]
        else:
            fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
            for c in trilha.caps:
                ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
