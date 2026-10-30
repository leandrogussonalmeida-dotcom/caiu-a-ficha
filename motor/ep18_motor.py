#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep18 — Como um foguete chega ao espaço (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (contagem, ronco grave, separação), nos
                          mesmos instantes do desenho

A física manda no desenho: o voo inteiro sai de `D.VOO` (simulação de 2
estágios, gravidade e Terra redonda, curva gravitacional). Cada cena de voo
tem um mapa tempo-do-vídeo -> tempo-de-voo (câmera lenta, tempo real ou
acelerado, escrito no painel); a inclinação do foguete, o céu, a massa, a
velocidade e o estágio do painel leem o mesmo instante. A chama sempre sai no
sentido oposto ao nariz. A contagem cai nas batidas da música e a separação
dos estágios num tempo forte (compasso).

    python3 ep18_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep18_motor.py <saida.mp4> subida separacao    # só esses capítulos (teste)
    python3 ep18_motor.py --folha <saida.png>             # 2 quadros por capítulo (FR=.3,.8)
    python3 ep18_motor.py --folha <saida.png> motor       # 5 quadros (FR=.1,.3,.5,.7,.9)
    python3 ep18_motor.py --folha <saida.png> motor 0.2 0.6
"""
import math, os, sys
import numpy as np
import longo as LG
import ep18_desenho as D          # registra a paleta do episódio (LG.PAL = 'ep18')
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
from ep18_desenho import (GAMA as GAMA_, VOO, FOG, pol, contorno, brilho, gradiente, seta_forca, barra, chama, CeuVoo,
                          Plataforma, fumaca, rastro, Tubeira, globo, globo_xy, terra_disco, hsh,
                          CEU0, CEU1, CEU2, CEU3, CEU4, CEU5, LOX, RP1, FUM0, FUM1, FUM2, MAR1, MAR2,
                          CASCO, CASCO2, CONCRETO, CHAO0)
import ritmo_marca as RM
import quizaudio as QA
from ep18_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2618, 45
GANHO_MUSICA = -10.0          # trilha baixa: o texto manda; o ronco fica por baixo da música
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do painel da direita
SR = LG.SR
K = 1.1                       # px por unidade do foguete (100 unidades = 60 m) nas cenas de voo
M_POR_U = .6
ESC = K / M_POR_U             # px por metro na mesma escala
FX, FY = 150, 105             # onde a câmera segura o foguete no voo
CEU = CeuVoo()
PLAT = Plataforma()
TF_SEP = VOO.tsep + 2.0       # o 1º estágio é solto 2 s depois do motor desligar
TF_COIFA = 190.0


def milhar(n): return f"{int(round(n)):,}".replace(',', '.')
def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')


def rampa(t, marcos):
    """Interpola linear entre marcos [(t, valor)]; devolve também a derivada."""
    if t <= marcos[0][0]:
        return marcos[0][1], (marcos[1][1] - marcos[0][1]) / (marcos[1][0] - marcos[0][0])
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * (t - a) / (b - a), (y - x) / (b - a)
    (a, x), (b, y) = marcos[-2], marcos[-1]
    return y + (t - b) * (y - x) / (b - a), (y - x) / (b - a)


def x_corte(cap):
    for c in CORTES:
        if c['de'][0] == cap or c['ate'][0] == cap: return c['x']
    return 60


def tit(tela, txt, y, cor=BRANCO, tam=17, x=PX0, centro=False):
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO, centro=centro)


def fundo_painel(tela, y0=4, y1=PALCO_H - 4):
    painel(tela, PX0 - 7, y0, W - PX0 + 3, y1 - y0, borda=TRACO)


def hud_v(tela, cap, linhas, y=6):
    """No corte vertical o painel some: os números vão para o alto do recorte."""
    if not VERTICAL: return
    x = x_corte(cap) + 90
    for k, (txt, cor) in enumerate(linhas):
        w = tela.largura_texto(txt, 9) + 8
        painel(tela, x - w // 2, y + k * 15 - 3, w, 14, borda=cor)
        tela.texto(txt, x, y + k * 15, cor, tam=9, centro=True)


def etiqueta(tela, txt, x, y, cor, tam=9, centro=True):
    w = tela.largura_texto(txt, tam)
    hh = 14 if tam < 14 else 22
    xx = x - w // 2 if centro else x
    painel(tela, xx - 5, y - 4, w + 10, hh + 2, borda=cor)
    tela.texto(txt, xx, y, cor, tam=tam)


def rotulo(tela, txt, x, y, ax, ay, cor=AMARELO, direita=False):
    """Rótulo 1x com fio até a peça (ax, ay) e bolinha na ponta."""
    w = tela.largura_texto(txt, 9)
    tx = x - w if direita else x
    tela.texto(txt, tx, y, cor, tam=9, contorno=PRETO)
    if direita: lx = x + 3 if ax > x else tx - 3
    else: lx = x - 3 if ax < x else x + w + 2
    tela.linha(lx, y + 3, ax, ay, cor)
    tela.disco(ax, ay, 1.5, cor)


def seta(tela, x0, y0, x1, y1, cor, esp=4, cab=7):
    seta_forca(tela, x0, y0, x1, y1, cor, esp, cab)


def tempo_txt(tf):
    s = abs(tf)
    return f"T{'-' if tf < 0 else '+'} {int(s // 60):02d}:{int(s % 60):02d}"


def ritmo_txt(r):
    if r <= .01: return 'PARADO', ACO2
    if r < .95: return f"CÂMERA LENTA {dec(r, 1)}X", CIANO
    if r < 1.05: return 'TEMPO REAL', VERDE
    return f"ACELERADO {dec(r, 0) if r >= 9.5 else dec(r, 1)}X", LARANJA


def massa_vis(q):
    """Massa mostrada: o 1º estágio vazio só sai da conta quando é solto."""
    m = q['m']
    if VOO.tsep <= q['tf'] < TF_SEP: m += VOO.SECO1
    return m


def painel_voo(tela, q, ritmo, extra=None, y_extra=136):
    """O painel de sempre do voo: tempo, altitude, velocidade, massa, estágio."""
    fundo_painel(tela)
    tf = q['tf']
    tit(tela, tempo_txt(tf), 9, ACO3, 9)
    rt, rc = ritmo_txt(ritmo)
    tela.texto(rt, W - 10, 9, rc, tam=9, centro='d', contorno=PRETO)
    tit(tela, 'ALTITUDE', 24, ACO3, 9)
    h = q['h']
    tit(tela, f"{milhar(h)} M" if h < 10e3 else f"{dec(h / 1e3, 1)} KM", 34, AMARELO, 17)
    tit(tela, 'VELOCIDADE', 56, ACO3, 9)
    tit(tela, f"{milhar(q['v'] * 3.6)} KM/H", 66, BRANCO, 17)
    tit(tela, 'MASSA', 88, ACO3, 9)
    m = massa_vis(q)
    tit(tela, f"{milhar(m / 1e3)} T", 98, BRANCO, 17)
    barra(tela, PX0 + 84, 101, 70, 8, m / VOO.M0, LARANJA)
    est = 1 if (tf < TF_SEP) else 2
    tit(tela, f"ESTÁGIO {est} DE 2", 120, CIANO, 9)
    for j in range(2):
        cor = CIANO if j < est else ACO0
        tela.ret(PX0 + 96 + j * 12, 120, 9, 8, PRETO)
        tela.ret(PX0 + 97 + j * 12, 121, 7, 6, cor)
    if extra: extra(tela, y_extra)


def estado_voo(tf, t, corte=False, niveis=None):
    """Dicionário de desenho do foguete no instante de voo tf."""
    q = VOO.q(tf)
    e = dict(t=t, vacuo=max(0.0, min(1.0, (q['h'] - 15e3) / 50e3)))
    e['chama1'] = 1.0 if (0 <= q['est'] == 1 or tf < 0) and tf < VOO.tsep else 0.0
    if tf < VOO.tsep and tf >= 0: e['chama1'] = 1.0
    e['quente1'] = 1.0 if tf < VOO.tsep + 3 else max(0.0, 1 - (tf - VOO.tsep - 3) / 6)
    if tf >= TF_SEP:
        d = tf - TF_SEP
        acc = max(0.0, tf - VOO.t2)
        ds = -(3.0 * d + .5 * 8.7 * acc * acc) / M_POR_U
        e['sep'] = (ds, -.4 * d, .09 * d)
        e['st1'] = ds > -260
    if VOO.t2 <= tf < VOO.tfim:
        e['chama2'] = min(1.0, (tf - VOO.t2) / .5)
        e['quente2'] = 1.0
    elif tf >= VOO.tfim:
        e['quente2'] = max(0.0, 1 - (tf - VOO.tfim) / 5)
    if tf >= TF_COIFA:
        ab = (tf - TF_COIFA) * .35
        if ab > 6: e['coifa'] = False
        else: e['coifa_sep'] = ab
    if corte:
        e['corte'] = True
        f1 = q['p1'] / VOO.PROP1
        f2 = q['p2'] / VOO.PROP2
        e['niveis'] = niveis or (f1, f1, f2, f2)
    return q, e


def riscos_ar(tela, q, t, x1=W):
    """Riscos do ar passando (só no ar denso): andam ao contrário do voo."""
    h = q['h']
    dens = max(0.0, 1 - h / 35e3)
    if dens <= 0 or q['v'] < 15: return
    gam = math.atan2(q['vt'], q['vr'])
    dx, dy = math.sin(gam), -math.cos(gam)
    vel = min(900.0, 60 + q['v'] * .5)
    L = min(22.0, 3 + q['v'] * .02)
    for i in range(int(22 * dens) + 2):
        bx, by = hsh(i, 1) * (x1 + 200) - 100, hsh(i, 2) * (PALCO_H + 200) - 100
        s = (t * vel + hsh(i, 3) * 900) % 900
        x = (bx - dx * s) % (x1 + 100) - 50
        y = (by - dy * s) % (PALCO_H + 100) - 50
        tela.linha(x, y, x + dx * L, y + dy * L, ACO4 if i % 3 else BRANCO)


def cena_voo(tela, t, tf, ritmo, x1=None, corte=False, k=K, cx=None, cy=FY, extra=None, sem_painel=False,
             niveis=None):
    """Céu + rastro + foguete na câmera que segue o voo + painel."""
    cx = cx if cx is not None else (FX if not VERTICAL else FX)
    x1 = x1 if x1 is not None else (W if VERTICAL else PX0 - 8)
    q, e = estado_voo(tf, t, corte, niveis)
    CEU.fundo(tela, q, t, x1=W)
    if q['h'] < 3000:
        gy = cy + 50 * k + q['h'] * ESC
        if gy < PALCO_H + 130:
            PLAT.desenhar(tela, gy, cx, t, braco=1.0)
    riscos_ar(tela, q, t)
    rastro(tela, VOO, tf, cx, cy, ESC * k / K, t)
    FOG.desenhar(tela, cx, cy, q['ang'], k, e)
    if not VERTICAL and not sem_painel:
        painel_voo(tela, q, ritmo, extra)
    return q, e


def trajetoria(tela, tf, y0=140, h=58, tmax=480.0, xmax=1450e3, hmax=220e3, cor=AMARELO, st1_arco=False):
    """Mini gráfico do caminho (distância x altitude), até o instante tf."""
    x0, w = PX0, 156
    tela.ret(x0, y0, w, h, FUNDO)
    tela.ret(x0, y0 + h, w, 1, ACO1)
    tela.ret(x0, y0, 1, h, ACO1)
    tela.texto('ALTITUDE', x0 + 3, y0 + 2, ACO2, tam=9)
    tela.texto('DISTÂNCIA', x0 + w - 2, y0 + h - 9, ACO2, tam=9, centro='d')
    a = VOO.a
    n = int(min(tf, len(a) * VOO.dt - 1) / VOO.dt)
    if n < 2: return
    idx = np.linspace(0, n, 90).astype(int)
    xs = x0 + 1 + a[idx, 9] / xmax * (w - 2)
    ys = y0 + h - 1 - a[idx, 1] / hmax * (h - 2)
    for i in range(len(idx) - 1):
        tela.linha(xs[i], ys[i], xs[i + 1], ys[i + 1], cor)
    tela.disco(xs[-1], ys[-1], 2, BRANCO)


# ----------------------------------------------------------------- sons
def tique(f=1800, dur=.03):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt / (dur / 4))).astype(np.float32)


def baque(f=70, dur=.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f * tt - 10 * tt * tt)) * np.exp(-tt / (dur / 4)) * np.minimum(1, tt / .004)
    return y.astype(np.float32)


_RNG = np.random.default_rng(18)


def ronco(dur, fc=110.0, ataque=.6, solta=.8):
    """Ronco do motor: ruído grave filtrado (abaixo de ~150 Hz), sem estalo."""
    n = max(16, int(dur * SR))
    x = _RNG.standard_normal(n).astype(np.float32)
    x = QA.lp(QA.lp(x, fc), fc)
    x = QA.hp(x, 30)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / max(ataque, 1e-3)) * np.minimum(1, (dur - tt) / max(solta, 1e-3))
    env *= 1 + .15 * np.sin(2 * np.pi * 3.1 * tt)
    y = x * np.clip(env, 0, None)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def zumbido(dur=2.0, f=440):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt + .3 * np.sin(2 * np.pi * 5 * tt)) * np.minimum(1, np.minimum(tt, dur - tt) / .3)
    return (y * .8).astype(np.float32)


def ronco_voo(fx, t0, t1, g_fn, passo=4.0):
    """Ronco em pedaços que se cruzam; o ganho de cada pedaço segue g_fn(t)."""
    t = t0
    while t < t1 - .2:
        d = min(passo + .8, t1 - t)
        g = g_fn(t + d / 2)
        if g > .002:
            fx.put(ronco(d, 100, .4, .4), t, g)
        t += passo


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

    def batidas(self, tipo='batida'):
        return [e['t'] - self.t0 for e in self.T.L.lista(tipo) if self.t0 - 1e-6 <= e['t'] < self.t0 + self.dur - 1e-6]


def cena_plataforma(tela, t, tf, ignicao, ritmo, painel_fn=None, k=K, gy0=186, forca_fn=None):
    """Plataforma vista de lado; a câmera segue o foguete quando ele sobe."""
    q, e = estado_voo(max(tf, 0.0), t)
    cy0 = gy0 - 50 * k
    alt_px = q['h'] * ESC if tf > 0 else 0.0
    cam = max(0.0, alt_px - (cy0 - 70))          # quanto a câmera subiu (px)
    cy = cy0 - alt_px + cam
    gy = gy0 + cam
    CEU.fundo(tela, q, t, x1=W)
    PLAT.desenhar(tela, gy, FX, t, braco=min(1.0, max(0.0, (t - ignicao + 3) / 2.5)) if ignicao is not None else 0.0)
    idade = (t - ignicao) if ignicao is not None else -1
    forca = 0.0
    if ignicao is not None and t >= ignicao:
        forca = min(1.0, (t - ignicao) / 1.2) if forca_fn is None else forca_fn(t)
        fumaca(tela, FX, gy, idade, t)
    else:
        # vapor do oxigênio líquido escapando (foguete abastecido)
        for i in range(6):
            u = (t * .5 + i / 6) % 1
            x = FX - 5 * k + (hsh(i, 4) - .5) * 6 + u * 10 * (1 if i % 2 else -1)
            y = cy - 2 * k + (hsh(i, 5)) * 20 + u * 22
            tela.disco(x, y, 1 + u * 3, FUM0 if u < .5 else FUM1)
    e['chama1'] = forca
    e['vacuo'] = 0.0
    if tf > 0: rastro(tela, VOO, tf, FX, cy, ESC, t)
    FOG.desenhar(tela, FX, cy, q['ang'], k, e)
    if forca > 0 and gy < PALCO_H + 4:
        brilho(tela, FX, gy - 2, 26 * forca, LARANJA)
    return q, cy, gy


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        bs = self.batidas('batida')
        bs = [b for b in bs if b >= 1.4]
        self.cont = bs[:5]                                   # 5, 4, 3, 2, 1 nas batidas
        self.ign = bs[5] if len(bs) > 5 else 5.25
        cs = [c for c in self.batidas('compasso') if c >= self.ign]
        self.dec = cs[0] if cs else 6.0                      # decolagem no tempo forte

    def tf(self, t): return t - self.dec

    def desenhar(self, tela, t, tg):
        tf = self.tf(t)
        q, cy, gy = cena_plataforma(tela, t, tf, self.ign, 1.0)
        n = sum(1 for b in self.cont if t >= b)
        cx_txt = x_corte('gancho') + 90 if VERTICAL else FX
        if 0 < n <= 5 and t < self.ign:
            dt = t - self.cont[n - 1]
            num = str(6 - n)
            painel(tela, cx_txt - 16, 14, 32, 34, borda=AMARELO)
            tela.texto(num, cx_txt, 20 - int(max(0, .12 - dt) * 40), AMARELO, tam=26, centro=True, contorno=PRETO)
        elif t >= self.ign and t < self.dec + 1.5:
            tela.texto('IGNIÇÃO!' if t < self.dec else 'DECOLAGEM!', cx_txt, 30, LARANJA, tam=17, centro=True,
                       contorno=PRETO)
        hud_v(tela, 'gancho', [(f"ALTITUDE {milhar(q['h'])} M", AMARELO)] if tf > 0 else [])
        if VERTICAL: return
        if tf < 0:
            fundo_painel(tela)
            tit(tela, 'CONTAGEM', 9, ACO3, 9)
            tit(tela, (f"T- {6 - n}" if n > 0 else 'T- 6') if t < self.ign else 'T- 0', 22, AMARELO, 26)
            tit(tela, 'NO RITMO DA MÚSICA', 52, ACO3, 9)
            tit(tela, 'ESTÁGIO 1 DE 2', 120, CIANO, 9)
            tit(tela, 'ALTITUDE 0 M', 90, BRANCO, 9)
        else:
            painel_voo(tela, VOO.q(tf), 1.0)

    def sons(self, fx):
        for k, b in enumerate(self.cont):
            fx.put(tique(1400 if k < 4 else 1900, .05), self.t0 + b, .16)
        fx.put(baque(55, .9), self.t0 + self.ign, .14)
        fx.put(ronco(self.dur - self.ign, 95, 1.2, 1.0), self.t0 + self.ign, .07)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        q = VOO.q(0)
        gradiente(tela, 0, 0, W, PALCO_H, [(0, PRETO), (.45, CEU5), (.8, CEU4), (1, CEU3)])
        for i in range(60):
            x, y = int(hsh(i, 1) * W), int(hsh(i, 2) * 110)
            if math.sin(t * 2 + i) > -.3: tela.px(x, y, BRANCO if i % 4 == 0 else ACO3)
        gy = 196
        PLAT.desenhar(tela, gy, 395, t, braco=0.0, k=.9)
        e = dict(t=t, chama1=0.0)
        FOG.desenhar(tela, 395, gy - 50 * .9, 0.0, .9, e)
        for i in range(6):
            u = (t * .5 + i / 6) % 1
            x = 395 - 5 + (hsh(i, 4) - .5) * 6 + u * 9 * (1 if i % 2 else -1)
            y = gy - 50 * .9 - 2 + hsh(i, 5) * 18 + u * 20
            tela.disco(x, y, 1 + u * 3, FUM0 if u < .5 else FUM1)
        n = int(t / .045)
        for j, linha in enumerate(("COMO UM FOGUETE", "CHEGA AO ESPAÇO")):
            vis = linha[:max(0, n - j * 16)]
            tela.texto(vis, 26, 40 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("COMO VOA / FLUTUA", 26, 112, AMARELO, tam=17, contorno=PRETO)

    def sons(self, fx):
        for k in range(3):
            fx.put(fx.blip(72 + k * 4, .1), self.t0 + 1.2 + k * .25, .2)


# ============================================================ newton
class Newton(Cena):
    """Balão no fio (0-14 s), foguete jogando gás (14-28 s), ar x vácuo (28-42 s)."""

    def desenhar(self, tela, t, tg):
        if t < 14.0: self.balao(tela, t)
        elif t < 28.4: self.foguete(tela, t - 14.0, t)
        else: self.vacuo(tela, t - 28.4, t)

    # ----------------------------------------------------------- balão
    def balao(self, tela, t):
        x1 = W if VERTICAL else PX0 - 8
        gradiente(tela, 0, 0, W, PALCO_H, [(0, FUNDO), (1, FUNDO2)])
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        ciclo = 7.0
        u = (t % ciclo)
        # poste e fio
        yf = 92
        tela.ret(14, yf - 4, 4, 120, ACO1); tela.ret(x1 - 18, yf - 4, 4, 120, ACO1)
        tela.ret(14, yf - 1, x1 - 28, 1, ACO3)
        tela.ret(14, yf, x1 - 28, 1, ACO1)
        # o balão: enche (0-1 s), solto em 1 s, acelera para a direita e murcha
        xa, xb = 112, x1 - 62
        if u < 1.0:
            x, cheio = xa, .5 + .5 * u
            jato = 0.0
        else:
            s = u - 1.0
            x = xa + (xb - xa) * min(1.0, (s / 5.2) ** 2)
            cheio = max(.45, 1 - s / 9)
            jato = 1.0 if s < 5.2 else max(0.0, 1 - (s - 5.2) * 2)
        rx, ry = 46 * cheio, 30 * cheio
        cy = yf + 4 + ry
        # canudo preso ao fio
        tela.ret(int(x - 14), yf - 2, 28, 4, PRETO); tela.ret(int(x - 13), yf - 1, 26, 2, ACO4)
        tela.disco(x, cy, ry + 1, PRETO)
        for dx in np.linspace(-rx + ry, rx - ry, 7):
            tela.disco(x + dx, cy, ry + 1, PRETO)
        for dx in np.linspace(-rx + ry, rx - ry, 7):
            tela.disco(x + dx, cy, ry, VERMELHO)
        for dx in np.linspace(-rx + ry, rx - ry, 7):
            tela.disco(x + dx - 2, cy - 3, ry * .7, ROSA)
        tela.disco(x - rx * .4, cy - ry * .45, ry * .25, BRANCO)
        tela.ret(int(x), int(yf + 2), 1, int(cy - ry - yf - 1), ACO3)
        # bico do balão (à esquerda) e o ar saindo para a ESQUERDA
        bx = x - rx - 3
        poligono(tela, [(x - rx + 2, cy - 4), (bx, cy - 2), (bx, cy + 2), (x - rx + 2, cy + 4)], VERMELHO)
        if jato > 0:
            for i in range(22):
                v = (u * 2.5 + i / 22) % 1
                ax = bx - 2 - v * 80
                ay = cy + (hsh(i, 3) - .5) * 16 * v
                tela.linha(ax, ay, ax + 3 + 4 * (1 - v), ay, MISTURA2 if v < .5 else CIANO)
            if t > 2.0:
                seta(tela, bx - 8, cy + 30, bx - 48, cy + 30, CIANO)
                tela.texto('AR', bx - 30, cy + 38, CIANO, tam=9, centro=True, contorno=PRETO)
                seta(tela, x + rx * .2, cy + 30, x + rx * .2 + 40, cy + 30, AMARELO)
                tela.texto('BALÃO', x + rx * .2 + 20, cy + 38, AMARELO, tam=9, centro=True, contorno=PRETO)
        hud_v(tela, 'newton', [('AÇÃO E REAÇÃO', AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'TERCEIRA LEI', 9, AMARELO, 17)
        tit(tela, 'DE NEWTON', 28, AMARELO, 17)
        tit(tela, 'AÇÃO:', 60, CIANO, 9)
        tit(tela, 'O BALÃO EMPURRA', 72, BRANCO, 9)
        tit(tela, 'O AR PARA TRÁS', 84, BRANCO, 9)
        tit(tela, 'REAÇÃO:', 104, AMARELO, 9)
        tit(tela, 'O AR EMPURRA', 116, BRANCO, 9)
        tit(tela, 'O BALÃO PARA A FRENTE', 128, BRANCO, 9)
        if t > 7.6:
            tit(tela, 'IGUAIS E CONTRÁRIAS', 156, VERDE, 9)
            seta(tela, PX0 + 70, 176, PX0 + 10, 176, CIANO, 3, 6)
            seta(tela, PX0 + 86, 176, PX0 + 146, 176, AMARELO, 3, 6)

    # ----------------------------------------------------------- foguete
    def foguete(self, tela, u, t):
        x1 = W if VERTICAL else PX0 - 8
        q = dict(h=3000.0 + u * 40, x=u * 30, v=0.0, tf=0)
        CEU.fundo(tela, dict(h=2500.0 + u * 60, x=0.0), t, x1=W)
        CEU.nuvens(tela, dict(h=1600.0 + u * 30, x=0.0), t, x1=W)
        cx, cy = 150, 82 - 4 * math.sin(u * .7)
        e = dict(t=t, chama1=1.0)
        # gás jogado para baixo: bolinhas rápidas saindo da tubeira
        bx, by = cx, cy + 50 * K
        for i in range(40):
            v = (t * 1.6 + i / 40) % 1
            gx = bx + (hsh(i, 7) - .5) * 8 * (1 + v * 2)
            gy = by + 8 + v * 120
            tela.disco(gx, gy, 1.2 + v, CHAMA1 if v < .25 else (CHAMA2 if v < .5 else FUM1))
        FOG.desenhar(tela, cx, cy, 0.0, K, e)
        if u > 1.0 and not VERTICAL:
            seta(tela, cx - 26, by + 18, cx - 26, by + 70, LARANJA, 5, 9)
            tela.texto('AÇÃO', cx - 34, by + 46, LARANJA, tam=9, centro='d', contorno=PRETO)
            tela.texto('GÁS P/ BAIXO', cx - 34, by + 58, LARANJA, tam=9, centro='d', contorno=PRETO)
        if u > 7.6 and not VERTICAL:
            seta(tela, cx + 26, cy + 40, cx + 26, cy - 20, AMARELO, 5, 9)
            tela.texto('REAÇÃO', cx + 34, cy + 2, AMARELO, tam=9, contorno=PRETO)
            tela.texto('FOGUETE P/ CIMA', cx + 34, cy + 14, AMARELO, tam=9, contorno=PRETO)
        hud_v(tela, 'newton', [('AÇÃO: GÁS PARA BAIXO', LARANJA), ('REAÇÃO: FOGUETE PARA CIMA', AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'NO FOGUETE', 9, AMARELO, 17)
        tit(tela, 'AÇÃO:', 40, LARANJA, 9)
        tit(tela, 'O FOGUETE EMPURRA', 52, BRANCO, 9)
        tit(tela, 'O GÁS PARA BAIXO', 64, BRANCO, 9)
        tit(tela, 'REAÇÃO:', 86, AMARELO, 9)
        tit(tela, 'O GÁS EMPURRA', 98, BRANCO, 9)
        tit(tela, 'O FOGUETE PARA CIMA', 110, BRANCO, 9)
        tit(tela, 'GÁS MAIS RÁPIDO', 140, ACO3, 9)
        tit(tela, '= EMPURRÃO MAIOR', 152, VERDE, 9)

    # ----------------------------------------------------------- ar x vácuo
    def vacuo(self, tela, u, t):
        meio = 150 if not VERTICAL else 150
        x1 = W if VERTICAL else PX0 - 8
        # esquerda: no ar; direita: no vácuo (no vertical, alterna a cada 5 s)
        lados = [('ar', 0, meio), ('vac', meio, x1)]
        if VERTICAL:
            xc = x_corte('newton')
            lados = [('ar' if int(u / 5) % 2 == 0 else 'vac', xc, xc + 180)]
        for tipo, a, b in lados:
            cxl = (a + b) / 2
            if tipo == 'ar':
                gradiente(tela, a, 0, b - a, PALCO_H, [(0, CEU2), (1, CEU0)])
                for i in range(70):
                    x = a + hsh(i, 1) * (b - a)
                    y = (hsh(i, 2) * PALCO_H + t * 8) % PALCO_H
                    # o jato empurra o ar de lado
                    dxn = x - cxl
                    if y > 120 and abs(dxn) < 22: x = cxl + math.copysign(22 + (22 - abs(dxn)) * .5, dxn or 1)
                    tela.disco(x, y, 1.2, CEU3)
                vac = 0.0
                rot = 'NO AR'
            else:
                tela.ret(int(a), 0, int(b - a), PALCO_H, PRETO)
                for i in range(40):
                    x = a + hsh(i, 3) * (b - a); y = hsh(i, 4) * PALCO_H
                    if math.sin(t * 2 + i) > -.4: tela.px(x, y, BRANCO if i % 3 == 0 else ACO2)
                vac = 1.0
                rot = 'NO VÁCUO'
            e = dict(t=t, chama1=1.0, vacuo=vac)
            FOG.desenhar(tela, cxl, 68 + 2 * math.sin(t * 1.3 + cxl), 0.0, .95, e)
            etiqueta(tela, rot, cxl, 10, AMARELO if tipo == 'vac' else CIANO, 9)
        if not VERTICAL:
            tela.ret(meio, 0, 1, PALCO_H, PRETO); tela.ret(meio + 1, 0, 1, PALCO_H, ACO1)
        
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'PRECISA DE AR?', 9, AMARELO, 17)
        tit(tela, 'NÃO: ELE EMPURRA O', 36, BRANCO, 9)
        tit(tela, 'PRÓPRIO GÁS, NÃO O AR', 48, BRANCO, 9)
        tit(tela, 'EMPUXO NO AR', 76, CIANO, 9)
        barra(tela, PX0, 88, 110, 8, .8, CIANO)
        tit(tela, 'EMPUXO NO VÁCUO', 108, AMARELO, 9)
        barra(tela, PX0, 120, 110, 8, .8 + .12 * min(1, u / 3), AMARELO)
        tit(tela, 'NO VÁCUO O GÁS SAI', 146, ACO3, 9)
        tit(tela, 'LIVRE: FUNCIONA MELHOR', 158, VERDE, 9)
        tit(tela, '(BARRAS ILUSTRATIVAS)', 184, ACO2, 9)

    def sons(self, fx):
        for k in range(2):
            fx.put(fx.chiado(5.5, 400, 2500), self.t0 + 1.0 + k * 7, .05, -.3)
        ronco_voo(fx, self.t0 + 14.0, self.t0 + self.dur, lambda t: .04)


# ============================================================ partes
PECAS = [('COIFA', 'E CARGA', (91, 0), 'cg'), ('2º ESTÁGIO', 'MOTOR PRÓPRIO', (70, 0), '2'),
         ('OXIGÊNIO LÍQUIDO', 'O OXIDANTE', (45, 0), 'o1'), ('COMBUSTÍVEL', 'QUEROSENE (RP-1)', (23, 0), 'c1'),
         ('TURBOBOMBAS', 'EMPURRAM OS LÍQUIDOS', (10.5, -1.6), 'tb'),
         ('CÂMARA', 'MISTURA E QUEIMA', (7.8, 0), 'cc'), ('TUBEIRA', 'BOCAL EM SINO', (2.5, 0), 'tu')]


class Partes(Cena):
    TS = [0.3, 6.8, 13.6, 20.4, 27.2, 34.0, 40.8]
    KP = 2.85

    def ativo(self, t):
        return max([k for k, a in enumerate(self.TS) if t >= a] or [0])

    def desenhar(self, tela, t, tg):
        x1 = W if VERTICAL else PX0 - 8
        # prancheta: grade azul que desliza devagar
        tela.buf[:PALCO_H] = FUNDO
        o = int(t * 4) % 24
        for x in range(-o, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(6, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        k_at = self.ativo(t)
        nome, sub, (s, u), chave = PECAS[k_at]
        if VERTICAL:
            # no corte vertical o foguete fica de pé e com zoom na peça
            k = 1.85
            cx = x_corte('partes') + 90
            cy = 104 + (s - 50) * k * .55
            ang = 0.0
        else:
            k, cx, cy, ang = self.KP, 150, 104 + math.sin(t * .8) * 1.5, math.pi / 2
        niv = (.92 + .02 * math.sin(t * 2), .92 + .02 * math.sin(t * 2 + 1), 1.0, 1.0)
        e = dict(t=t, corte=True, niveis=niv, acesos=(chave,), chama1=0.0)
        FOG.desenhar(tela, cx, cy, ang, k, e)
        f = D.eixo(cx, cy, ang, k)
        ax, ay = f(s, u)
        if chave in ('2', 'tu', 'cc', 'cg'):
            reg = {'2': (61, 80, 5.6), 'tu': (0, 6.5, 4.6), 'cc': (6.3, 9.3, 2.9), 'cg': (81.5, 95.5, 4.4)}[chave]
            pts = [f(reg[0], -reg[2]), f(reg[1], -reg[2]), f(reg[1], reg[2]), f(reg[0], reg[2])]
            if int(t * 4) % 2 == 0:
                for i in range(4):
                    a, b = pts[i], pts[(i + 1) % 4]
                    tela.linha(a[0], a[1], b[0], b[1], AMARELO)
        if VERTICAL:
            etiqueta(tela, nome, cx, 8, AMARELO, 9)
            return
        # painel com a lista; fio da peça ativa até ela
        fundo_painel(tela)
        for j, (n, sb, _, _) in enumerate(PECAS):
            y = 10 + j * 24
            if j > k_at: cor = ACO1
            elif j == k_at: cor = AMARELO
            else: cor = ACO3
            tela.ret(PX0, y + 1, 5, 5, cor)
            tela.texto(n, PX0 + 9, y, cor, tam=9, contorno=PRETO)
            if j == k_at:
                tela.texto(sb, PX0 + 9, y + 11, BRANCO, tam=9, contorno=PRETO)
                yy = y + 3
                yb = 52 if j < 2 else 160
                tela.linha(PX0 - 2, yy, PX0 - 8, yy, AMARELO)
                tela.linha(PX0 - 8, yy, ax, yb, AMARELO)
                tela.linha(ax, yb, ax, ay, AMARELO)
                tela.disco(ax, ay, 2, AMARELO)
                tela.disco(ax, yb, 1.5, AMARELO)
        tela.texto(f"PEÇA {k_at + 1} DE 7", PX0 + 2, 186, ACO3, tam=9)
        for j in range(7):
            tela.ret(PX0 + 96 + j * 9, 187, 7, 5, AMARELO if j <= k_at else ACO0)

    def sons(self, fx):
        for k, a in enumerate(self.TS):
            fx.put(fx.blip(72 + k, .08), self.t0 + a, .12)


# ============================================================ motor aberto
class Motor(Cena):
    N = 70

    def preparar(self):
        self.tb = Tubeira(cx=150, y_cam=82, y_gar=124, y_boca=184, hw_cam=30, hw_gar=7, razao=20.0)

    @staticmethod
    def SONDA_MARCOS(T):
        return [(0.0, T.yc + 10), (14.0, T.yc + 22), (21.0, T.yg - 3), (28.0, T.yg + 3), (35.0, T.yb - 3),
                (37.5, T.yb + 12), (42.5, T.yb + 12)]

    def gas(self, tela, t):
        """Gás dentro do motor, colorido pela temperatura: ele esfria ao acelerar."""
        T = self.tb
        for y in range(T.yc, min(PALCO_H, T.yb + 26)):
            if y <= T.yb:
                w = T.meia(y) - .5
            else:
                w = T.hb * (1 - (y - T.yb) * .012)
            M = T.M_em(min(y, T.yb))
            tr = 1 / (1 + .5 * (GAMA_ - 1) * M * M)
            if y > T.yb: tr *= max(.0, 1 - (y - T.yb) / 30)
            x0, x1 = int(T.cx - w), int(T.cx + w) + 1
            if x1 <= x0: continue
            xs = np.arange(x0, x1)
            b = D.BAY[y % 8, xs % 8]
            lv = [(.97, BRANCO), (.9, CHAMA0), (.78, CHAMA1), (.6, CHAMA2), (.42, BRASA), (.2, OLEO0), (-1, FUNDO2)]
            cores = np.full(len(xs), FUNDO2, np.uint8)
            for (lim, cor), (lim2, cor2) in zip(lv, lv[1:]):
                if tr >= lim:
                    cores[:] = cor
                    break
                if tr >= lim2:
                    u = (tr - lim2) / (lim - lim2)
                    cores[:] = np.where(u > b, cor, cor2)
                    break
            if y < T.yg - 6:
                cores = np.where(D.BAY[(y + int(t * 12)) % 8, xs % 8] > .8, CHAMA0, cores).astype(np.uint8)
            if y > T.yb:
                fora = (np.abs(xs - T.cx) / max(1.0, w)) > (1 - (y - T.yb) / 40) * .9 + b * .2
                cores = np.where(fora, tela.buf[y, x0:x1], cores).astype(np.uint8)
            tela.buf[y, x0:x1] = cores

    def acende(self, t, k):
        """Rótulos aparecem com as legendas."""
        return t >= (.5, 7.0, 14.0, 21.0, 28.0)[k]

    def desenhar(self, tela, t, tg):
        T = self.tb
        cx = T.cx
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        # ---- tanques (fundos) no alto, canos e turbobombas
        for xt, cor, cor2 in ((cx - 62, LOX, MISTURA2), (cx + 62, RP1, LATAO)):
            tela.disco(xt, -6, 24, PRETO); tela.disco(xt, -7, 23, ACO2); tela.disco(xt, -8, 20, cor)
            dither(tela, xt - 20, 4, 40, 4, cor, cor2)
        ang = t * 7.0
        for xp, cor in ((cx - 40, LOX), (cx + 40, RP1)):
            xt = cx - 62 if xp < cx else cx + 62
            # cano do tanque até a bomba
            tela.ret(int(xt) - 4, 14, 8, 26, PRETO); tela.ret(int(xt) - 3, 14, 6, 26, ACO2)
            tela.ret(int(min(xt, xp)) - 3, 36, int(abs(xp - xt)) + 6, 8, PRETO)
            tela.ret(int(min(xt, xp)) - 2, 37, int(abs(xp - xt)) + 4, 6, ACO2)
            # da bomba até a placa injetora
            tela.ret(int(xp) - 4, 52, 8, 26, PRETO); tela.ret(int(xp) - 3, 52, 6, 26, ACO2)
            # líquido andando (riscos)
            for j in range(6):
                v = (t * 1.2 + j / 6) % 1
                tela.ret(int(xt) - 1, int(15 + v * 24), 2, 3, cor)
                tela.ret(int(xp) - 1, int(53 + v * 23), 2, 3, cor)
            # a bomba: carcaça + rotor girando
            tela.disco(xp, 44, 12, PRETO); tela.disco(xp, 44, 11, ACO1); tela.disco(xp, 44, 9, ACO0)
            for j in range(6):
                a = ang * (1 if xp < cx else -1) + j * math.pi / 3
                tela.linha(xp, 44, xp + math.cos(a) * 8, 44 + math.sin(a) * 8, cor)
            tela.disco(xp, 44, 2.5, ACO4)
        # eixo e turbina no meio
        tela.ret(cx - 40, 43, 80, 3, ACO3); tela.ret(cx - 40, 46, 80, 1, ACO0)
        tela.disco(cx, 44, 9, PRETO); tela.disco(cx, 44, 8, LATAO)
        for j in range(8):
            a = ang * 1.3 + j * math.pi / 4
            tela.linha(cx, 44, cx + math.cos(a) * 7, 44 + math.sin(a) * 7, OLEO1)
        tela.disco(cx, 44, 2, CHAMA0)
        # ---- câmara, garganta e sino (cortados), cheios de gás quente
        self.gas(tela, t)
        self.particulas(tela, t)
        T.parede(tela, esp=6)
        # sonda: um pedaço de gás marcado, que anda junto com as legendas
        yp, _ = rampa(t, self.SONDA_MARCOS(T))
        yp += math.sin(t * 3) * .6 if yp < T.yg - 10 else 0
        tela.anel(cx, yp, 5, CIANO); tela.anel(cx, yp, 6, PRETO, .5); tela.disco(cx, yp, 2, BRANCO)
        M = T.M_em(yp); v = T.v_em(yp)
        # rótulos (com fio)
        if not VERTICAL:
            if self.acende(t, 0):
                rotulo(tela, 'OXIGÊNIO LÍQUIDO', 8, 20, cx - 66, 20, CIANO)
                rotulo(tela, 'COMBUSTÍVEL', 286, 20, cx + 66, 20, LARANJA, direita=True)
                rotulo(tela, 'TURBOBOMBA', 8, 56, cx - 44, 50, AMARELO)
            if self.acende(t, 1): rotulo(tela, 'CÂMARA', 8, 96, cx - 33, 96, AMARELO)
            if self.acende(t, 2): rotulo(tela, 'GARGANTA', 8, 124, cx - 9, T.yg, AMARELO)
            if self.acende(t, 4): rotulo(tela, 'SINO', 8, 160, cx - T.meia(160) - 3, 160, AMARELO)
            tela.texto('CÂMERA LENTA', 290, 196, CIANO, tam=9, centro='d', contorno=PRETO)
        mt = dec(M, 2) if M < .95 else dec(M, 1)
        hud_v(tela, 'motor', [(f"MACH {mt}", CIANO), (f"{milhar(v)} M/S", AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'O GÁS NA SONDA', 9, ACO3, 9)
        tit(tela, f"MACH {mt}", 21, CIANO, 26)
        reg = 'MAIS LENTO QUE O SOM' if M < .95 else ('VELOCIDADE DO SOM' if M < 1.08 else 'SUPERSÔNICO')
        tit(tela, reg, 50, VERDE if M >= 1.08 else (AMARELO if M >= .95 else ACO3), 9)
        tit(tela, 'VELOCIDADE', 66, ACO3, 9)
        tit(tela, f"{milhar(v)} M/S", 76, BRANCO, 17)
        # gráfico: velocidade ao longo do motor
        gx, gy0, gw, gh = PX0, 104, 156, 74
        tela.ret(gx, gy0, gw, gh, FUNDO)
        tela.ret(gx, gy0 + gh, gw, 1, ACO1); tela.ret(gx, gy0, 1, gh, ACO1)
        yrng = (T.yc, T.yb + 14)
        vmax = 3200.0
        pts = []
        for i in range(gw - 2):
            y = yrng[0] + (yrng[1] - yrng[0]) * i / (gw - 3)
            pts.append((gx + 1 + i, gy0 + gh - 1 - T.v_em(y) / vmax * (gh - 4)))
        for a, b in zip(pts, pts[1:]): tela.linha(a[0], a[1], b[0], b[1], LARANJA)
        xg = gx + 1 + (T.yg - yrng[0]) / (yrng[1] - yrng[0]) * (gw - 3)
        for yy in range(gy0 + 2, gy0 + gh, 3): tela.px(xg, yy, ACO2)
        tela.texto('GARGANTA', xg + 3, gy0 + 3, ACO2, tam=9)
        xp = gx + 1 + (min(yp, yrng[1]) - yrng[0]) / (yrng[1] - yrng[0]) * (gw - 3)
        tela.disco(xp, gy0 + gh - 1 - v / vmax * (gh - 4), 2.5, CIANO)
        tela.texto('VELOCIDADE AO LONGO DO MOTOR', gx, gy0 + gh + 5, ACO2, tam=9)

    def particulas(self, tela, t):
        T = self.tb
        for i in range(self.N):
            tau = (t * .9 + i / self.N * T.vida) % T.vida
            y = T.y_part(tau)
            if y > T.yb + 24 or y > PALCO_H: continue
            lat = (hsh(i, 1) * 2 - 1) * .85
            if y < T.yg - 12:
                lat += math.sin(t * 3 + i) * .08                  # turbulência na câmara
            w = T.meia(y) if y <= T.yb else T.hb * (1 + (y - T.yb) * .02)
            x = T.cx + lat * w
            M = T.M_em(min(y, T.yb))
            Lr = min(9.0, max(1.0, M * 2.4))
            cor = LARANJA if M < .5 else (BRANCO if M < 2.5 else CHAMA0)
            tela.linha(x, y - Lr, x, y, cor)

    def sons(self, fx):
        fx.put(zumbido(self.dur - .5, 330), self.t0 + .3, .025)
        ronco_voo(fx, self.t0 + .2, self.t0 + self.dur - .3, lambda t: .035)


# ============================================================ decolagem
class Decolagem(Cena):
    def preparar(self):
        cs = [c for c in self.batidas('compasso') if c >= 14.5]
        self.dec = cs[0] if cs else 15.0
        self.ign = 7.6
        self.marcos = [(self.dec, 0.0), (self.dec + 10.0, 5.0), (self.dec + 21.0, 16.0)]

    def tf(self, t):
        if t < self.dec: return t - self.dec, 0.0
        return rampa(t, self.marcos)

    def empuxo(self, t):
        """Fração do peso: 0 até a ignição, sobe até 1,41 em 6 s e fica."""
        if t < self.ign: return 0.0
        return min(VOO.F1 / (VOO.M0 * D.G0), 1.41 * suave((t - self.ign) / 6.5))

    def desenhar(self, tela, t, tg):
        tf, r = self.tf(t)
        emp = self.empuxo(t)
        q, cy, gy = cena_plataforma(tela, t, tf, self.ign, r if tf >= 0 else 0.0,
                                    forca_fn=lambda tt: min(1.0, emp / 1.41 + .1))
        # forças: peso (cg), empuxo (tubeira), apoio da plataforma
        f = D.eixo(FX, cy, 0.0, K)
        cgx, cgy = f(38, 0)
        pw = 40
        pp = pw * massa_vis(q) / VOO.M0
        xs = FX - 34
        seta(tela, xs, cgy, xs, cgy + pp, VERMELHO)
        tela.texto('PESO', xs - 6, cgy + 4, VERMELHO, tam=9, centro='d', contorno=PRETO)
        if emp > .02:
            bx, by = f(0, 0)
            seta(tela, FX + 30, by, FX + 30, by - pw * emp, AMARELO)
            tela.texto('EMPUXO', FX + 36, by - pw * emp, AMARELO, tam=9, contorno=PRETO)
        apoio = max(0.0, 1 - emp) if tf <= 0 else 0.0
        if apoio > .02 and not VERTICAL:
            seta(tela, FX - 70, gy, FX - 70, gy - pw * apoio, VERDE, 3, 6)
            tela.texto('APOIO', FX - 76, gy - pw * apoio - 2, VERDE, tam=9, centro='d', contorno=PRETO)
        hud_v(tela, 'decolagem', [(f"EMPUXO / PESO: {dec(emp, 2)}", AMARELO if emp > 1 else BRANCO)])
        if VERTICAL: return
        if tf < 0:
            fundo_painel(tela)
            tit(tela, tempo_txt(tf), 9, ACO3, 9)
            tit(tela, 'NA PLATAFORMA', 24, BRANCO, 9)
        else:
            painel_voo(tela, q, r)
            fundo_painel(tela, 130, PALCO_H - 4)
        y0 = 136 if tf >= 0 else 50
        tit(tela, 'EMPUXO', y0, AMARELO, 9)
        barra(tela, PX0, y0 + 11, 150, 7, emp / 1.6, AMARELO)
        tit(tela, 'PESO', y0 + 24, VERMELHO, 9)
        barra(tela, PX0, y0 + 35, 150, 7, (massa_vis(q) / VOO.M0) / 1.6, VERMELHO)
        xm = PX0 + int(150 / 1.6)
        for yy in range(y0 + 9, y0 + 45, 2): tela.px(xm, yy, BRANCO)
        tit(tela, f"EMPUXO / PESO = {dec(emp * VOO.M0 / massa_vis(q), 2)}", y0 + 50,
            VERDE if emp > 1.0 else ACO3, 9)
        if tf < 0:
            tit(tela, 'EMPUXO MAIOR QUE', 130, ACO3, 9)
            tit(tela, 'O PESO: ELE SOBE', 142, ACO3, 9)

    def sons(self, fx):
        fx.put(baque(55, .9), self.t0 + self.ign, .13)
        fx.put(ronco(self.dur - self.ign, 95, 3.0, 1.0), self.t0 + self.ign, .075)
        fx.put(tique(1900, .05), self.t0 + self.dec, .2)


# ============================================================ massa
class Massa(Cena):
    def preparar(self):
        self.marcos = [(0.0, 16.0), (self.dur, 60.0)]

    def desenhar(self, tela, t, tg):
        tf, r = rampa(t, self.marcos)
        kk = 1.5
        def extra(tela, y0):
            q = VOO.q(tf)
            fundo_painel(tela, 130, PALCO_H - 4)
            tit(tela, 'PROPELENTE', 136, LOX, 9)
            pf = q['prop'] / q['m']
            tela.texto(f"{int(round(pf * 100))}% DA MASSA", W - 10, 136, LOX, tam=9, centro='d', contorno=PRETO)
            # barra empilhada: propelente x o resto
            bx, bw = PX0, 156
            tela.ret(bx - 1, 148, bw + 2, 12, ACO1)
            wp = int(bw * pf)
            tela.ret(bx, 149, wp, 10, LOX); dither(tela, bx, 155, wp, 4, LOX, MISTURA)
            tela.ret(bx + wp, 149, bw - wp, 10, ACO2)
            tit(tela, 'ESTRUTURA E CARGA', 164, ACO3, 9)
            g = q['F'] / q['m'] / D.G0
            tit(tela, 'ACELERAÇÃO DO MOTOR', 180, ACO3, 9)
            tit(tela, f"{dec(g, 1)} G", 190, AMARELO, 9)
        q, e = cena_voo(tela, t, tf, r, corte=True, k=kk, cy=112, extra=extra)
        if not VERTICAL and t > .5:
            f = D.eixo(FX, 112, q['ang'], kk)
            ax, ay = f(45, 0); bx_, by_ = f(23, 0)
            rotulo(tela, 'OXIGÊNIO', 196, 40, ax + 4, ay, CIANO)
            rotulo(tela, 'COMBUSTÍVEL', 196, 80, bx_ + 4, by_, LARANJA)
        hud_v(tela, 'massa', [(f"MASSA {milhar(massa_vis(q) / 1e3)} T", BRANCO)])

    def sons(self, fx):
        ronco_voo(fx, self.t0, self.t0 + self.dur, lambda t: .065)


# ============================================================ subida
class Subida(Cena):
    def preparar(self):
        self.marcos = [(0.0, 60.0), (self.dur, 139.0)]

    def desenhar(self, tela, t, tg):
        tf, r = rampa(t, self.marcos)

        def extra(tela, y0):
            q = VOO.q(tf)
            tit(tela, f"INCLINAÇÃO {int(round(math.degrees(q['ang'])))}°", 134, AMARELO, 9)
            tit(tela, 'P/ CIMA', 146, ACO3, 9)
            barra(tela, PX0 + 54, 147, 100, 6, q['vr'] / 2500, VERDE)
            tit(tela, 'DE LADO', 157, ACO3, 9)
            barra(tela, PX0 + 54, 158, 100, 6, q['vt'] / 2500, AMARELO)
            trajetoria(tela, tf, y0=170, h=30, xmax=200e3, hmax=80e3)
        q, e = cena_voo(tela, t, tf, r, extra=extra)
        # vetor velocidade e suas duas partes (de lado e para cima)
        if not VERTICAL and t > 23.8:
            L = 46
            vx, vy = q['vt'] / q['v'] * L, -q['vr'] / q['v'] * L
            ox, oy = FX + 40, FY + 34
            seta(tela, ox, oy, ox + vx, oy, AMARELO, 3, 6)
            seta(tela, ox, oy, ox, oy + vy, VERDE, 3, 6)
            seta(tela, ox, oy, ox + vx, oy + vy, BRANCO, 3, 6)
            tela.texto('DE LADO', ox + vx / 2, oy + 6, AMARELO, tam=9, centro=True, contorno=PRETO)
        hud_v(tela, 'subida', [(f"{milhar(q['v'] * 3.6)} KM/H", BRANCO),
                               (f"INCLINAÇÃO {int(round(math.degrees(q['ang'])))}°", AMARELO)])

    def sons(self, fx):
        ronco_voo(fx, self.t0, self.t0 + self.dur, lambda t: .065 * (1 - .5 * (t - self.t0) / self.dur))


# ============================================================ separação
class Separacao(Cena):
    def preparar(self):
        cs = self.batidas('compasso')
        def prox(x): return min(cs, key=lambda c: abs(c - x)) if cs else x
        self.t_meco, self.t_sep, self.t_ign = prox(6.0), prox(9.0), prox(12.0)
        tm, ts, ti = VOO.tsep, TF_SEP, VOO.t2
        self.marcos = [(0.0, tm - self.t_meco), (self.t_meco, tm), (self.t_sep, ts), (self.t_ign, ti),
                       (self.dur, ti + self.dur - self.t_ign)]

    def desenhar(self, tela, t, tg):
        tf, r = rampa(t, self.marcos)

        def extra(tela, y0):
            self.inset(tela, tf)
        q, e = cena_voo(tela, t, tf, r, extra=extra)
        # sopro das molas / gás na separação
        if TF_SEP <= tf < TF_SEP + 2.5:
            f = D.eixo(FX, FY, q['ang'], K)
            u = (tf - TF_SEP) / 2.5
            for i in range(14):
                a = i / 14 * 2 * math.pi
                x, y = f(57, 0)
                rr = 4 + u * 26
                tela.px(x + math.cos(a) * rr, y + math.sin(a) * rr * .6, BRANCO if u < .5 else ACO3)
        cx_txt = x_corte('separacao') + 90 if VERTICAL else FX
        if self.t_meco <= t < self.t_meco + 2.2:
            etiqueta(tela, 'MOTOR DESLIGA', cx_txt, 10, VERMELHO, 9)
        elif self.t_sep <= t < self.t_sep + 2.2:
            etiqueta(tela, 'SEPARAÇÃO!', cx_txt, 10, AMARELO, 9)
        elif self.t_ign <= t < self.t_ign + 2.5:
            etiqueta(tela, 'IGNIÇÃO DO 2º ESTÁGIO', cx_txt, 10, LARANJA, 9)
        hud_v(tela, 'separacao', [(f"ESTÁGIO {1 if tf < TF_SEP else 2} DE 2", CIANO)])

    def inset(self, tela, tf):
        """O 1º estágio, solto, sobe um pouco e cai de volta (balístico)."""
        tit(tela, '1º ESTÁGIO SOLTO', 134, ACO3, 9)
        x0, y0, w, h = PX0, 146, 156, 52
        tela.ret(x0, y0, w, h, FUNDO)
        tela.ret(x0, y0 + h - 4, w, 4, D.CHAO1)
        q0 = VOO.q(VOO.tsep)
        hs, xs = q0['h'], q0['x']
        sc_h, sc_x = (h - 8) / 140e3, (w - 8) / 420e3
        def ponto(dt):
            hh = hs + q0['vr'] * dt - .5 * D.G0 * dt * dt
            return x0 + 4 + (xs + q0['vt'] * dt) * sc_x, y0 + h - 4 - max(0, hh) * sc_h, hh
        # caminho do 2º estágio até agora
        trajetoria_mini = [VOO.q(tt) for tt in np.linspace(0, max(1.0, tf), 40)]
        for a, b in zip(trajetoria_mini, trajetoria_mini[1:]):
            tela.linha(x0 + 4 + a['x'] * sc_x, y0 + h - 4 - a['h'] * sc_h,
                       x0 + 4 + b['x'] * sc_x, y0 + h - 4 - b['h'] * sc_h, AMARELO)
        if tf > TF_SEP:
            dmax = 300.0
            dt_now = min(dmax, (tf - VOO.tsep) * 12)          # o desenho do inset anda 12x
            for i in range(0, int(dt_now), 6):
                xa, ya, hh = ponto(i)
                if hh < 0 or xa > x0 + w - 3: break
                if (i // 6) % 2 == 0: tela.px(xa, ya, VERMELHO)
            xa, ya, hh = ponto(dt_now)
            if hh >= 0 and xa < x0 + w - 3: tela.disco(xa, ya, 1.5, VERMELHO)
            tela.texto('CAI', x0 + w - 4, y0 + 4, VERMELHO, tam=9, centro='d')

    def sons(self, fx):
        ronco_voo(fx, self.t0, self.t0 + self.t_meco, lambda t: .05)
        fx.put(tique(1200, .05), self.t0 + self.t_meco, .2)
        fx.put(baque(80, .4), self.t0 + self.t_sep, .14)
        fx.put(tique(2200, .04), self.t0 + self.t_sep, .15, .2)
        fx.put(baque(50, .7), self.t0 + self.t_ign, .12)
        ronco_voo(fx, self.t0 + self.t_ign, self.t0 + self.dur, lambda t: .035)


# ============================================================ Kármán
class Karman(Cena):
    def preparar(self):
        t0 = VOO.t2 + 30 - 12.0
        self.marcos = [(0.0, 167.0), (self.dur, 167.0 + self.dur)]
        self.esc_km = 3.2                                   # px por km na régua

    def desenhar(self, tela, t, tg):
        tf, r = rampa(t, self.marcos)

        def extra(tela, y0):
            q = VOO.q(tf)
            tit(tela, 'ONDE COMEÇA O ESPAÇO', 134, ACO3, 9)
            for j, (km, nome, cor) in enumerate(((100, 'KÁRMÁN (FAI)', AMARELO), (80, 'FORÇAS DOS EUA', CIANO))):
                yy = 148 + j * 24
                ok = q['h'] >= km * 1e3
                tela.ret(PX0, yy + 1, 7, 7, cor if ok else ACO0)
                if ok: tela.ret(PX0 + 2, yy + 3, 3, 3, BRANCO)
                tela.texto(f"{km} KM", PX0 + 12, yy, cor, tam=9, contorno=PRETO)
                tela.texto(nome, PX0 + 12, yy + 10, ACO3, tam=9, contorno=PRETO)
        q, e = cena_voo(tela, t, tf, r, extra=extra)
        x1 = W if VERTICAL else PX0 - 8
        # as linhas no céu: 80 km e 100 km
        for km, nome, cor in ((100, 'LINHA DE KÁRMÁN: 100 KM', AMARELO), (80, '80 KM (EUA)', CIANO)):
            y = FY + (q['h'] / 1e3 - km) * self.esc_km
            if -4 < y < PALCO_H + 4:
                for x in range(0, int(x1), 6):
                    tela.ret(x, int(y), 3, 1, cor)
                xt = x_corte('karman') + 6 if VERTICAL else 6
                tela.texto(nome, xt, int(y) - 10, cor, tam=9, contorno=PRETO)
        if TF_COIFA <= tf < TF_COIFA + 5 and not VERTICAL:
            etiqueta(tela, 'COIFA SOLTA', FX, 10, AMARELO, 9)
        hud_v(tela, 'karman', [(f"ALTITUDE {dec(q['h'] / 1e3, 1)} KM", AMARELO)])

    def sons(self, fx):
        ronco_voo(fx, self.t0, self.t0 + self.dur, lambda t: .03)
        t100 = VOO.t100 - 167.0
        fx.put(fx.sino(84, .9), self.t0 + t100, .12)
        fx.put(tique(1500, .05), self.t0 + TF_COIFA - 167.0, .2)


# ============================================================ órbita
class Orbita(Cena):
    T_SECO = 15.3
    T_DIAG = 22.0

    def preparar(self):
        self.marcos = [(0.0, 203.0), (self.T_SECO, VOO.tfim), (self.T_DIAG, VOO.tfim + self.T_DIAG - self.T_SECO)]
        # canhão de Newton (desenho fora de escala): integra 4 lançamentos
        self.R, self.r0 = 58.0, 82.0
        self.mu = 1.0
        self.v_circ = math.sqrt(self.mu / self.r0)
        self.trajs = {}
        for nome, f in (('parado', 0.0), ('lento', .55), ('medio', .8), ('orbita', 1.0)):
            x, y, vx, vy = 0.0, self.r0, f * self.v_circ, 0.0
            pts = [(x, y)]
            dt = .25
            for i in range(20000):
                r = math.hypot(x, y)
                ax, ay = -self.mu * x / r ** 3, -self.mu * y / r ** 3
                vx += ax * dt; vy += ay * dt; x += vx * dt; y += vy * dt
                pts.append((x, y))
                if math.hypot(x, y) < self.R: break
                if nome == 'orbita' and i * dt > 2 * math.pi * self.r0 / self.v_circ: break
            self.trajs[nome] = np.array(pts)

    def desenhar(self, tela, t, tg):
        if t < self.T_DIAG: return self.voo(tela, t)
        return self.canhao(tela, t)

    def voo(self, tela, t):
        tf, r = rampa(t, self.marcos)

        def extra(tela, y0):
            q = VOO.q(tf)
            tit(tela, 'VELOCIDADE DE ÓRBITA', 134, ACO3, 9)
            vc = math.sqrt(D.MU / (D.RT + q['h']))
            barra(tela, PX0, 146, 156, 8, q['v'] / vc, AMARELO if q['v'] < vc * .995 else VERDE)
            tit(tela, f"{dec(q['v'] / 1e3, 1)} DE {dec(vc / 1e3, 1)} KM/S", 158, BRANCO, 9)
            if tf >= VOO.tfim:
                tit(tela, 'MOTOR DESLIGADO', 176, VERDE, 9)
                tit(tela, 'EM ÓRBITA', 188, VERDE, 9)
        q, e = cena_voo(tela, t, tf, r, extra=extra, k=1.6, cx=175)
        hud_v(tela, 'orbita', [(f"{milhar(q['v'] * 3.6)} KM/H", BRANCO)])

    def canhao(self, tela, t):
        u = t - self.T_DIAG
        x1 = W if VERTICAL else PX0 - 8
        tela.buf[:PALCO_H] = PRETO
        for i in range(90):
            x, y = int(hsh(i, 1) * W), int(hsh(i, 2) * PALCO_H)
            if math.sin(t * 1.5 + i) > -.5: tela.px(x, y, BRANCO if i % 4 == 0 else ACO2)
        cx = x_corte('orbita') + 90 if VERTICAL else 150
        cy = 106
        S = 1.0
        globo(tela, cx, cy, self.R * S, -40 - t * 2.0, t, x1=W)
        # qual lançamento mostrar
        if u < 7.8: nomes = ['parado']
        elif u < 15.6: nomes = ['parado', 'lento', 'medio']
        else: nomes = ['parado', 'lento', 'medio', 'orbita']
        for nome in nomes:
            P = self.trajs[nome]
            ativo = nome == nomes[-1]
            t_ini = {'parado': 0.0, 'lento': 7.8, 'medio': 11.0, 'orbita': 15.6}[nome]
            prog = (u - t_ini) / (2.8 if nome != 'orbita' else 6.0)
            if nome == 'orbita' and prog > 1: prog = 1 + (prog - 1)
            n = len(P)
            if nome == 'orbita':
                k_fim = n - 1 if prog >= 1 else int(n * max(0.0, prog))
            else:
                k_fim = int(n * min(1.0, max(0.0, prog)))
            cor = {'parado': VERMELHO, 'lento': LARANJA, 'medio': AMARELO, 'orbita': VERDE}[nome]
            if not ativo: cor = ACO1 if nome != 'parado' else ACO1
            for i in range(0, max(0, k_fim - 1), 3):
                a = P[i]
                tela.px(cx + a[0] * S, cy - a[1] * S, cor)
            if nome == 'orbita' and prog >= 1:
                # dá voltas sem parar
                fase = ((u - t_ini - 6.0) / 6.0) % 1.0
                k = int(fase * (n - 1))
            else:
                k = max(0, min(n - 1, k_fim))
            if ativo:
                a = P[k]
                px, py = cx + a[0] * S, cy - a[1] * S
                vx_, vy_ = (P[min(n - 1, k + 1)] - P[max(0, k - 1)])
                ang = math.atan2(vx_, vy_) if (abs(vx_) + abs(vy_)) > 1e-6 else 0.0
                # foguete pequeno, nariz na direção do movimento
                ang_tela = math.atan2(vx_, vy_)
                FOG.desenhar(tela, px, py, ang_tela, .36, dict(t=t, st1=False, coifa=False, chama2=0.0))
                if nome == 'orbita' and prog >= 1:
                    # gravidade puxa para o centro; a velocidade é de lado
                    rr = math.hypot(a[0], a[1])
                    gx, gy = -a[0] / rr, a[1] / rr
                    seta(tela, px, py, px + gx * 18, py + gy * 18, VERMELHO, 3, 5)
                    vn = math.hypot(vx_, vy_)
                    seta(tela, px, py, px + vx_ / vn * 22, py - vy_ / vn * 22, AMARELO, 3, 5)
        # ponto de partida (fora de escala) e rótulos
        tela.disco(cx, cy - self.r0 * S, 2, BRANCO)
        if not VERTICAL:
            tela.texto('FORA DE ESCALA', 8, 196, ACO2, tam=9, contorno=PRETO)
        hud_v(tela, 'orbita', [('CAINDO EM VOLTA DA TERRA' if u > 15.6 else 'O CANHÃO DE NEWTON', VERDE)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'SE ELE ANDAR...', 9, ACO3, 9)
        itens = [('PARADO', 'CAI RETO', VERMELHO, 0.0), ('DEVAGAR', 'CAI PERTO', LARANJA, 7.8),
                 ('MAIS RÁPIDO', 'CAI LONGE', AMARELO, 11.0), ('7,8 KM/S', 'NUNCA CHEGA', VERDE, 15.6)]
        for j, (a, b, cor, ta) in enumerate(itens):
            if u < ta: continue
            y = 26 + j * 30
            tela.ret(PX0, y + 2, 6, 6, cor)
            tit(tela, a, y, cor, 9, PX0 + 10)
            tit(tela, b, y + 11, BRANCO, 9, PX0 + 10)
        if u > 15.6:
            tit(tela, '28.000 KM/H', 150, AMARELO, 17)
            tit(tela, 'A TERRA SE CURVA', 172, ACO3, 9)
            tit(tela, 'E ELE ERRA O CHÃO', 184, ACO3, 9)

    def sons(self, fx):
        ronco_voo(fx, self.t0, self.t0 + self.T_SECO, lambda t: .03)
        fx.put(tique(1200, .05), self.t0 + self.T_SECO, .2)
        fx.put(fx.sino(88, 1.0), self.t0 + self.T_SECO + .1, .1)
        for ta in (0.0, 7.8, 11.0, 15.6):
            fx.put(fx.blip(76, .08), self.t0 + self.T_DIAG + ta, .1)


# ============================================================ equador
class Equador(Cena):
    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = PRETO
        for i in range(80):
            x, y = int(hsh(i, 5) * W), int(hsh(i, 6) * PALCO_H)
            if math.sin(t * 1.4 + i) > -.5: tela.px(x, y, BRANCO if i % 4 == 0 else ACO2)
        if VERTICAL:
            cx, R = x_corte('equador') + 90, 80
        else:
            cx, R = 150, 90
        cy = 104
        lon0 = -20 - t * 1.0                    # diminui: a Terra gira para o LESTE
        globo(tela, cx, cy, R, lon0, t, equador=t > 7.6, lat_marca=D.KENNEDY[0] if (t > 7.6 and not VERTICAL) else None)
        # setas do giro: maiores no equador (o chão anda mais rápido)
        if t > 7.6:
            for lat in (0, 30, -30, 60, -60):
                v = math.cos(math.radians(lat))
                y = cy - R * math.sin(math.radians(lat))
                xr = cx + R * math.cos(math.radians(lat))
                L = 26 * v
                if L > 4: seta(tela, xr + 4, y, xr + 4 + L, y, AMARELO if lat == 0 else ACO3, 3 if lat == 0 else 2, 5)
        else:
            seta(tela, cx - 40, cy + R + 0, cx + 40, cy + R + 0, AMARELO, 3, 6)
            tela.texto('LESTE', cx + 46, cy + R - 4, AMARELO, tam=9, contorno=PRETO)
        # Alcântara: ponto que pisca e foguete subindo para o leste
        p = globo_xy(cx, cy, R, lon0, *D.ALCANTARA)
        if p and t > 14.6:
            px, py = p
            if t > 21.6:
                tela.anel(px, py, 3 + (t * 4) % 4, AMARELO)
            tela.disco(px, py, 2, VERMELHO)
            if t > 21.6 and not VERTICAL:
                rotulo(tela, 'ALCÂNTARA (MA)', 196, 150, px + 2, py + 2, AMARELO)
            u = (t - 14.6) % 6.0
            if u < 4.5:
                # foguete pequeno: sobe e vai deitando para o leste (direita)
                s = u / 4.5
                fx_, fy_ = px + 70 * s * s, py - 50 * s + 22 * s * s
                ang = math.atan2(140 * s + 1e-3, 50 - 44 * s)
                FOG.desenhar(tela, fx_, fy_, ang, .16, dict(t=t, chama1=1.0, vacuo=s))
        if not VERTICAL and t > 7.6:
            pk = globo_xy(cx, cy, R, lon0, *D.KENNEDY)
            tela.texto('EQUADOR', cx - R - 4, cy - 4, AMARELO, tam=9, centro='d', contorno=PRETO)
            tela.texto('28,6° N', cx - R * .86 - 4, cy - R * .48 - 4, LARANJA, tam=9, centro='d', contorno=PRETO)
        hud_v(tela, 'equador', [('NO EQUADOR: 465 M/S', AMARELO)] if t > 7.6 else [('A TERRA GIRA PARA O LESTE', AMARELO)])
        if VERTICAL: return
        fundo_painel(tela)
        tit(tela, 'VELOCIDADE DO CHÃO', 9, ACO3, 9)
        tit(tela, 'PARA O LESTE', 20, ACO3, 9)
        itens = [('EQUADOR', 1674.7, AMARELO, 7.6), ('ALCÂNTARA, 2° S', 1674.7 * math.cos(math.radians(2.34)), VERDE, 21.6),
                 ('KENNEDY (EUA), 28,6° N', 1470.2, LARANJA, 7.6)]
        y = 40
        for nome, kmh, cor, ta in itens:
            if t < ta: continue
            tit(tela, nome, y, cor, 9)
            barra(tela, PX0, y + 12, 100, 7, kmh / 1700, cor)
            tela.texto(f"{milhar(kmh)} KM/H", PX0 + 104, y + 12, BRANCO, tam=9, contorno=PRETO)
            y += 34
        if t < 7.6:
            tit(tela, 'A TERRA GIRA', 50, BRANCO, 17)
            tit(tela, 'PARA O LESTE', 70, AMARELO, 17)
            seta(tela, PX0 + 10, 104, PX0 + 140, 104, AMARELO)
        if t > 7.6:
            tit(tela, '465 M/S NO EQUADOR', 150, AMARELO, 9)
        if t > 14.6:
            tit(tela, 'LANÇANDO PARA O LESTE,', 168, BRANCO, 9)
            tit(tela, 'ESSE EMPURRÃO É GRÁTIS', 180, VERDE, 9)

    def sons(self, fx):
        fx.put(fx.blip(76, .1), self.t0 + 7.6, .12)
        fx.put(fx.sino(84, 1.0), self.t0 + 21.6, .12)
        for k in range(4):
            fx.put(ronco(4.0, 90, .5, 1.5), self.t0 + 14.6 + k * 6.0, .05)


# ============================================================ resumo
class Resumo(Cena):
    CX = [64, 178, 292, 406]
    NOMES = [('AÇÃO E REAÇÃO', 'GÁS P/ BAIXO'), ('LEVA O PRÓPRIO', 'OXIDANTE'), ('SOLTA O', 'PESO MORTO'),
             ('ANDA DE LADO', '28.000 KM/H')]
    TS = [0.5, 7.3, 14.7, 22.1]

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = PRETO
        for i in range(80):
            x, y = int(hsh(i, 7) * W), int(hsh(i, 8) * PALCO_H)
            if math.sin(t * 1.4 + i) > -.5: tela.px(x, y, ACO3 if i % 4 else BRANCO)
        k_at = max([k for k, a in enumerate(self.TS) if t >= a] or [0])
        for k in range(4):
            cx = self.CX[k]
            if VERTICAL and k != k_at: continue
            if VERTICAL: cx = x_corte('resumo') + 90
            aceso = k == k_at
            cor = AMARELO if aceso else ACO1
            painel(tela, cx - 52, 18, 104, 150, borda=cor)
            self._icone(tela, k, cx, 74, t, aceso)
            tela.texto(self.NOMES[k][0], cx, 134, AMARELO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(self.NOMES[k][1], cx, 148, BRANCO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(str(k + 1), cx - 44, 24, cor, tam=9)
        tela.texto('EMPURRAR GÁS, PERDER PESO, ANDAR DE LADO', W // 2, 184, AMARELO, tam=9, centro=True,
                   contorno=PRETO)

    def _icone(self, tela, k, cx, cy, t, aceso):
        x0, y0, w, h = cx - 44, cy - 46, 88, 92
        dither(tela, x0, y0, w, h, FUNDO2, FUNDO)
        u = (t * .4) % 1.0 if aceso else .5
        if k == 0:
            FOG.desenhar(tela, cx, cy - 8 - u * 10, 0.0, .55, dict(t=t, chama1=1.0))
            seta(tela, cx + 22, cy + 30, cx + 22, cy - 10, AMARELO, 3, 5)
            seta(tela, cx - 22, cy + 6, cx - 22, cy + 40, LARANJA, 3, 5)
        elif k == 1:
            for j, (cor, nome) in enumerate(((LOX, 'O'), (RP1, 'C'))):
                xx = cx - 22 + j * 26
                tela.ret(xx - 1, cy - 31, 20, 62, PRETO)
                tela.ret(xx, cy - 30, 18, 60, FUNDO3)
                nv = .5 + .4 * math.sin(t * 1.5 + j) if aceso else .7
                hh = int(58 * nv)
                tela.ret(xx + 1, cy + 29 - hh, 16, hh, cor)
        elif k == 2:
            sep = (u * 40) if aceso else 10
            FOG.desenhar(tela, cx, cy - 12, 0.0, .5, dict(t=t, sep=(-sep * 2.2, 0, .02 * sep), chama2=1.0 if sep > 8 else 0))
        else:
            R = 22
            globo(tela, cx, cy, R, -40 - t * 8, t, linhas=False)
            a = t * 1.6 if aceso else 1.0
            r = R + 12
            px, py = cx + r * math.cos(a), cy + r * math.sin(a)
            tela.anel(cx, cy, r, ACO1, .5)
            FOG.desenhar(tela, px, py, a + math.pi, .14, dict(t=t, st1=False, coifa=False))

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
            tela.buf[:PALCO_H] = PRETO
            for i in range(90):
                x, y = int(hsh(i, 1) * W), int(hsh(i, 2) * PALCO_H)
                if math.sin(t * 1.5 + i) > -.5: tela.px(x, y, BRANCO if i % 4 == 0 else ACO2)
            terra_disco(tela, W / 2, 208 + 900, 960, t * .05)
            u = t - RM.OUTRO_S
            x = -60 + u * 42
            FOG.desenhar(tela, x, 150, math.pi / 2 + .03, .9, dict(t=t, st1=False, coifa=False))
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

CENAS = dict(gancho=Gancho, titulo=Titulo, newton=Newton, partes=Partes, motor=Motor, decolagem=Decolagem,
             massa=Massa, subida=Subida, separacao=Separacao, karman=Karman, orbita=Orbita, equador=Equador,
             resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep18_motor as EP
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
