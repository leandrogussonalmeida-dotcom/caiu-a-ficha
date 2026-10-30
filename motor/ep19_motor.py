#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep19 — A jornada de um contêiner pelo porto (PT-BR).

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (caminhão, bipe da câmera, motor do
                          guindaste, as travas, o lacre, o mar, a buzina),
                          nos mesmos instantes do desenho
Os guindastes leem quadros-chave (x do trole, altura do spreader, intervalos
de trava) definidos por capítulo; o som das travas usa os MESMOS instantes.
No guindaste e no ritmo, os instantes de trava são os compassos da trilha
(`trilha.L`), então o clique cai na batida.

    python3 ep19_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep19_motor.py <saida.mp4> guindaste ritmo     # só esses capítulos (teste)
    python3 ep19_motor.py --folha <saida.png> [ids]       # quadros por capítulo (FR=.3,.8)
    python3 ep19_motor.py --quadros <saida.png> id:t ...  # quadros escolhidos
"""
import math, os, sys
import numpy as np
import ep19_desenho as D                      # registra a paleta 'ep19' (antes de qualquer Tela)
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
from ep19_desenho import (CEU0, CEU1, CEU2, CEU3, CEU4, CEUD0, CEUD1, SOL, MAR0, MAR1, MAR2, MAR3, ESPUMA,
                          LAR0, LAR1, LAR2, LAR3, LAR4, CIN0, CIN1, CIN2, ASF0, ASF1, ASF2, CON0, CON1, CON2,
                          CAS0, CAS1, VMC0, VMC1, VMC2, VDC1, VDC2, AZC1, AZC2,
                          P_LAR, P_AZ, P_VD, P_VM, P_CI, P_BR, OUTRAS, ETAPAS, CODIGO,
                          rotulo, fio, seta, halo, luz, mira, caixa, grad_v, check, xis, lerp, um)
import ritmo_marca as RM
import idioma as I
from ep19_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2619, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
SR = LG.SR

CEU_NOITE = (CEU0, CEU0, CEU1, CEU2, CEU3)
CEU_TARDE = (CEU1, CEU2, CEU3, CEU4, CEU4)
CEU_DIA = (CEUD0, CEUD0, CEUD1, CEUD1, BRANCO)
CEU_AURORA = (CEU1, CEU2, CEU3, CEU4, SOL)


def fase(t, a, b): return um((t - a) / max(1e-6, b - a))


def kf(t, keys):
    """Quadros-chave [(t, v)...] com transição suave; v número ou tupla."""
    if t <= keys[0][0]: return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if t < tb:
            u = suave((t - ta) / max(1e-6, tb - ta))
            if isinstance(va, tuple): return tuple(a + (b - a) * u for a, b in zip(va, vb))
            return va + (vb - va) * u
    return keys[-1][1]


def trava_de(t, travas, gira=.25):
    """0..1 do giro dos pinos; `travas` = [(t_trava, t_solta)]."""
    for a, b in travas:
        if a - gira <= t < a: return (t - (a - gira)) / gira
        if a <= t < b: return 1.0
        if b <= t < b + gira: return 1 - (t - b) / gira
    return 0.0


def carregando(t, travas): return any(a <= t < b for a, b in travas)


def faixa_brilho(tela, x0, x1, y0, y1, pos, larg=8, incl=.5):
    """Faixa de luz passando pela chapa: cada tom do laranja sobe um degrau."""
    x0, x1, y0, y1 = max(0, int(x0)), min(W, int(x1)), max(0, int(y0)), min(PALCO_H, int(y1))
    if x1 <= x0 or y1 <= y0: return
    sub = tela.buf[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = np.abs(xx + (yy - y0) * incl - pos) < larg
    lut = np.arange(256, dtype=np.uint8)
    lut[LAR0], lut[LAR1], lut[LAR2], lut[LAR3] = LAR1, LAR2, LAR3, LAR4
    sub[m] = lut[sub[m]]


def lupa(tela, x, y, w, h, titulo, cor=AMARELO, alvo=None):
    """Janela de zoom com moldura; devolve a área interna (x, y, w, h)."""
    if alvo:
        tela.linha(x + w // 2, y + h, alvo[0], alvo[1], cor)
        tela.disco(alvo[0], alvo[1], 2, cor)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, FUNDO)
    dither(tela, x + 1, y + 1, w - 2, h - 2, FUNDO, FUNDO2)
    tela.ret_vazado(x, y, w, h, cor)
    tela.ret(x, y, w, 11, cor)
    tela.texto(titulo, x + 4, y + 2, PRETO, tam=9)
    return x + 2, y + 12, w - 4, h - 14


def oval(tela, cx, cy, rx, ry, ang, cor, n=24):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        px_, py_ = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + px_ * math.cos(ang) - py_ * math.sin(ang), cy + px_ * math.sin(ang) + py_ * math.cos(ang)))
    poligono(tela, pts, cor)


def quad(tela, cx, cy, w, h, ang, cor):
    c, s = math.cos(ang), math.sin(ang)
    pts = [(cx + dx * c - dy * s, cy + dx * s + dy * c) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    poligono(tela, pts, cor)
    return pts


# ================================================================ sons
def _tom(f, dur, dec, harm=(), ataque=.002):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt)
    for h, a in harm: y = y + a * np.sin(2 * np.pi * f * h * tt)
    y = y * np.minimum(1, tt / ataque) * np.exp(-tt / dec)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def tique(f=2400): return _tom(f, .03, .005)


def clac():
    """Trava giratória: dois tiques metálicos curtos (senoides, sem ruído)."""
    a = _tom(1250, .06, .012, ((2.76, .5),)); b = _tom(1900, .05, .008, ((2.4, .4),))
    out = np.zeros(int(.08 * SR), np.float32)
    out[:len(a)] += a * .8
    i = int(.014 * SR); out[i:i + len(b)] += b * .6
    return out / (np.abs(out).max() + 1e-9)


def baque(f=62): return _tom(f, .35, .08, ((1.5, .35), (2.1, .15)), ataque=.004)


def zumbido(dur, f=46.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt) + .45 * np.sin(2 * np.pi * 2 * f * tt) + .2 * np.sin(2 * np.pi * 3.02 * f * tt)
    y *= 1 + .15 * np.sin(2 * np.pi * 5.5 * tt)
    env = np.minimum(1, tt / .25) * np.minimum(1, (dur - tt) / .3)
    return (y * env / 1.8).astype(np.float32)


def buzina(dur=1.8, f=92.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * tt) + .6 * np.sin(2 * np.pi * 2 * f * tt) + .35 * np.sin(2 * np.pi * 3 * f * tt) + .15 * np.sin(2 * np.pi * 4 * f * tt)
    env = np.minimum(1, tt / .12) * np.minimum(1, (dur - tt) / .4)
    return (y * env / 2.1).astype(np.float32)


def mar_som(fx, t0, dur, g=.05):
    fx.put(fx.chiado(dur, 150, 900, ataque=1.0), t0, g)


# ================================================================ base
class Cena:
    legenda = True
    brilho = None
    K = 0                     # etapa do painel (0..7); -1 = fora das etapas
    VX = 150                  # centro do recorte vertical

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.L = trilha.L
        self.t0, self.dur = cap['t0'], cap['dur']
        self.bar = 4 * 60.0 / cap['bpm']
        self.B = [e['t'] - self.t0 for e in self.L.lista('compasso') if self.t0 - 1e-3 <= e['t'] < self.t0 + self.dur - 1e-3]
        if len(self.B) < cap['bars']:
            self.B = [k * self.bar for k in range(cap['bars'])]
        self.preparar()

    def b(self, k):
        """Instante do compasso k (relativo ao capítulo)."""
        return self.B[k] if k < len(self.B) else k * self.bar

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    def painel(self, tela, t, selo=None, **kw):
        if VERTICAL:
            D.selo_vertical(tela, max(0, self.K), self.VX, selo)
        else:
            D.painel_jornada(tela, self.K, t, **kw)

    def rot(self, tela, txt, x, y, cor=BRANCO, alvo=None, centro=False):
        """Rótulo com fio opcional; no Short some se sair do recorte."""
        w = tela.largura_texto(txt, 9)
        xa = x - w // 2 if centro else x
        if VERTICAL and (xa < self.VX - 88 or xa + w > self.VX + 88): return
        if not VERTICAL and xa + w > 292: return
        if alvo:
            ax = xa + w // 2
            ay = y + 9 if alvo[1] > y else y - 2
            fio(tela, ax, ay, alvo[0], alvo[1], cor)
        rotulo(tela, txt, x, y, cor, centro=centro)

    def lupa_x(self, x_largo, w):
        """No Short a lupa vem para dentro do recorte."""
        if VERTICAL: return int(min(max(x_largo, self.VX - 88), self.VX + 88 - w))
        return x_largo

    def sons_movimento(self, fx, X, travas, g=.12):
        """Motor do guindaste enquanto o trole anda; clac em cada trava/solta."""
        for a, b in travas:
            fx.put(clac(), self.t0 + a, .42, -.1)
            fx.put(clac(), self.t0 + b, .32, .1)
        for (ta, xa), (tb, xb) in zip(X, X[1:]):
            if abs(xb - xa) > 4 and tb - ta > .2:
                fx.put(zumbido(tb - ta), self.t0 + ta, g)


def grade(tela, x0=0, x1=W):
    tela.buf[:PALCO_H] = FUNDO
    for x in range(x0, x1, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(12, PALCO_H, 24): tela.ret(x0, y, x1 - x0, 1, FUNDO2)


# ================================================================ cenários compartilhados
YQ, YW, XLANE = 150, 160, 84            # cais, linha d'água, faixa do caminhão (vista do cais)
SLOT_NOSSO = (4, 5)                     # fileira 02 (r = 4), camada 6 (k = 5)


def horizonte(tela, t, y=128, x0=0, x1=W, cor=CEU1, luzes=True):
    """Silhueta da cidade e de guindastes distantes, com janelas acesas."""
    for k in range(0, x1 - x0, 14):
        h = 6 + (k * 37) % 17
        tela.ret(x0 + k, y - h, 12, h + 30, cor)
        if luzes:
            for j in range(2, h, 4):
                if (k * 7 + j * 3 + int(t * .5)) % 5 == 0: tela.px(x0 + k + 3 + (j % 3) * 2, y - h + j, CHAMA0)
    for gx in (x0 + 60, x0 + 200, x0 + 330):
        if gx > x1 - 10: continue
        tela.ret(gx, y - 26, 2, 26, cor); tela.ret(gx + 14, y - 26, 2, 26, cor)
        tela.ret(gx - 8, y - 30, 40, 2, cor)
        if int(t * 1.5 + gx) % 2: tela.px(gx + 30, y - 31, VMC2)


def navio_corte(seed=3, deck=()):
    """Navio (vista do cais) com o porão cheio; `deck` = slots extras do convés."""
    C = D.Corte(x0=176, rows=10, deck_y=140, tiers_h=4, tiers_d=4)
    rng = np.random.default_rng(seed)
    for r in range(10):
        for k in range(4):
            C.slots[(r, k)] = OUTRAS[int(rng.integers(0, len(OUTRAS)))]
    for rk in deck:
        C.slots[rk] = OUTRAS[int(rng.integers(0, len(OUTRAS)))]
    return C


def cena_cais(tela, t, C, st, ceu=CEU_NOITE, caminhao=P_LAR, cam_x=XLANE, amarras=False, cidade=True):
    """O cais visto de frente: céu, cidade, mar, navio em corte, caminhão e o STS.
    st = (trole_x, gancho_y, trava, carregando)."""
    D.ceu(tela, YW, t, estrelas=ceu is CEU_NOITE, cores=ceu)
    if cidade: horizonte(tela, t, 132, 140, 294, CEU1 if ceu is CEU_NOITE else CEU2)
    D.mar(tela, 150, 294, YW, PALCO_H, t)
    D.cais(tela, 0, 160, YQ, trilhos=(D.STS['xl'], D.STS['xs']))
    # faixas pintadas no cais
    for x in range(64, 106, 6): tela.ret(x, YQ + 3, 3, 1, CHAMA0)
    C.casco(tela, YW, t)
    C.cargas(tela, t)
    if amarras: C.amarras(tela)
    if caminhao is not None:
        D.caminhao_frente(tela, cam_x, YQ, t, cont=caminhao is not False, pal=caminhao if caminhao else P_LAR,
                          codigo=caminhao is P_LAR)
    x, y, tr, car = st
    D.sts(tela, t, x, y, tr, carga=car)


def zoom_trava(tela, x, y, w, h, desce, gira, t, titulo='PINO NO FURO (DE CIMA)'):
    """Lupa: a peça de canto vista de cima, com o furo oval; o pino do spreader
    entra (desce 0..1) e gira 90° (gira 0..1). Quando gira, as pontas do pino
    ficam embaixo da chapa (tracejado): não sai mais."""
    ix, iy, iw, ih = lupa(tela, x, y, w, h, titulo, AMARELO)
    cx, cy = ix + iw // 2 - 18, iy + ih // 2
    # chapa da peça de canto
    tela.ret(cx - 24, cy - 20, 48, 40, PRETO)
    grad_v(tela, cx - 23, cy - 19, 46, 38, [CIN2, CIN1, CIN1, CIN0])
    tela.ret(cx - 23, cy - 19, 46, 1, ACO4)
    # furo oval (deitado)
    oval(tela, cx, cy, 13, 6.5, 0, PRETO)
    ang = math.pi / 2 * suave(gira)
    if desce < 1:
        # pino ainda em cima: maior e com sombra
        s = 1 + (1 - desce) * .35
        oy = -(1 - desce) * 10
        oval(tela, cx + 2, cy + 3, 11 * s, 5 * s, 0, FUNDO)
        oval(tela, cx, cy + oy, 11 * s, 5 * s, 0, PRETO)
        oval(tela, cx, cy + oy, 10 * s, 4 * s, 0, ACO3)
        tela.ret(int(cx - 6 * s), int(cy + oy - 1), int(12 * s), 1, ACO4)
    else:
        # pino dentro: só aparece o que está no furo; o resto, tracejado
        oval(tela, cx, cy, 10.5, 4.5, ang, 250)
        sub_y0, sub_x0 = int(cy - 14), int(cx - 14)
        blk = tela.buf[sub_y0:sub_y0 + 29, sub_x0:sub_x0 + 29]
        yy, xx = np.mgrid[sub_y0:sub_y0 + 29, sub_x0:sub_x0 + 29]
        dentro = ((xx - cx) / 13.0) ** 2 + ((yy - cy) / 6.5) ** 2 <= 1.0
        m = blk == 250
        blk[m & dentro] = ACO3
        blk[m & ~dentro & ((xx + yy) % 3 == 0)] = AMARELO
        blk[m & ~dentro & ((xx + yy) % 3 != 0)] = CIN1
        tela.linha(cx - 9 * math.cos(ang), cy - 9 * math.sin(ang), cx + 9 * math.cos(ang), cy + 9 * math.sin(ang), ACO4)
    # leitura
    tx = ix + iw - 50
    graus = int(round(90 * suave(gira)))
    tela.texto(f"{graus}°", tx, iy + 4, AMARELO if graus else ACO3, tam=17, contorno=PRETO)
    trav = gira >= 1
    tela.texto('TRAVADO' if trav else ('GIRANDO' if gira > 0 else ('ENCAIXA' if desce < 1 else 'SOLTO')),
               tx, iy + 26, VERDE if trav else ACO3, tam=9, contorno=PRETO)
    if trav: check(tela, tx + 2, iy + 38, VERDE)
    tela.texto('FURO OVAL', ix + 2, iy + ih - 9, ACO3, tam=9)


# ---------------------------------------------------------------- pátio (vista pela ponta)
PAT = dict(yb=186, x0=24, x1=214, ytopo=34, lane=48, rows=[70, 94, 118, 142, 166], alt=[3, 2, 3, 4, 2])


def y_pilha(n, yb=PAT['yb']): return yb - n * 22


def cena_patio(tela, t, st, ceu=CEU_NOITE, caminhao=P_LAR, cam_dx=0.0, nosso_na_pilha=False, navio=0.0):
    """Pátio de contêineres: fileiras empilhadas, faixa do caminhão e o RTG."""
    D.ceu(tela, 150, t, estrelas=ceu is CEU_NOITE, cores=ceu)
    # navio chegando lá longe (silhueta)
    if navio > 0:
        nx = int(lerp(300, 214, ease(navio)))
        tela.ret(nx, 126, 80, 8, CAS1); tela.ret(nx + 6, 118, 50, 8, CEU2)
        tela.ret(nx + 60, 108, 8, 18, CERAMICA)
    horizonte(tela, t, 140, 0, 294, CEU1 if ceu is CEU_NOITE else CEU2)
    # blocos do fundo (mais escuros)
    for k in range(9):
        x = k * 33 - 4
        for j in range(1 + (k * 5) % 3):
            tela.ret(x, 150 - (j + 1) * 12, 30, 11, [FUNDO3, CAS1, ACO0][(k + j) % 3])
            tela.ret(x, 150 - (j + 1) * 12, 30, 1, ACO1)
    # RTG de fundo, pequeno, andando
    bx = int(250 + 30 * math.sin(t * .2))
    tela.ret(bx, 98, 3, 52, LATAO); tela.ret(bx + 40, 98, 3, 52, LATAO); tela.ret(bx - 3, 96, 49, 4, LATAO)
    D.asfalto(tela, 150, t, faixa=False)
    for x in range(0, 294, 24): tela.ret(x, PAT['yb'] + 4, 12, 1, CHAMA0)
    tela.ret(PAT['lane'] - 14, 152, 1, 34, BRANCO); tela.ret(PAT['lane'] + 14, 152, 1, 34, BRANCO)
    # pilhas
    for i, (x, n) in enumerate(zip(PAT['rows'], PAT['alt'])):
        for k in range(n):
            pal = OUTRAS[(i * 3 + k * 5) % len(OUTRAS)]
            D.cont_frente(tela, x, y_pilha(k + 1), 20, 22, pal)
        tela.texto(f"{i + 1}", x + 10, PAT['yb'] + 8, ACO2, tam=9, centro=True)
    if nosso_na_pilha:
        D.cont_frente(tela, PAT['rows'][1], y_pilha(3), 20, 22, P_LAR, codigo=True)
    if caminhao is not None:
        D.caminhao_frente(tela, PAT['lane'] + cam_dx, PAT['yb'], t, cont=caminhao is not False,
                          pal=caminhao if caminhao else P_LAR, w=20, h=22, codigo=caminhao is P_LAR)
    x, y, tr, car = st
    D.rtg(tela, PAT['x0'], PAT['x1'], PAT['yb'], PAT['ytopo'], x, y, tr, t, carga=car)


# ---------------------------------------------------------------- portão (de lado)
PORTAL_X = 118


def cena_portao(tela, t, xcam, dist, ceu=CEU_TARDE, varre=None, cancela=0.0, raiox=None):
    """Portão do terminal de lado: arco das câmeras, guarita e cancela.
    xcam = traseira da carreta. `varre` = x da cortina de luz das câmeras."""
    D.ceu(tela, 176, t, estrelas=False, cores=ceu)
    tela.disco(60, 60, 9, CEU4); tela.disco(60, 60, 6, SOL)
    horizonte(tela, t, 150, 0, 294, CEU2, luzes=True)
    # cerca
    for x in range(0, 294, 6): tela.ret(x, 148, 1, 28, ACO0)
    tela.ret(0, 148, 294, 1, ACO1); tela.ret(0, 160, 294, 1, ACO0)
    D.asfalto(tela, 176, t, scroll=0)
    # arco das câmeras (poste da frente + viga por cima da pista)
    px_ = PORTAL_X
    tela.ret(px_ - 1, 84, 6, 92, PRETO); tela.ret(px_, 85, 4, 91, ACO3); tela.ret(px_, 85, 1, 91, ACO4)
    tela.ret(px_ - 6, 80, 120, 7, PRETO); tela.ret(px_ - 5, 81, 118, 5, ACO3); tela.ret(px_ - 5, 81, 118, 1, ACO4)
    for k in range(4):
        cx_ = px_ + 10 + k * 28
        tela.ret(cx_, 86, 7, 5, PRETO); tela.ret(cx_ + 1, 87, 5, 3, ACO1)
        tela.px(cx_ + 3, 89, VERMELHO if int(t * 3 + k) % 2 else VMC0)
    tela.ret(px_ - 6, 120, 6, 6, PRETO); tela.ret(px_ - 5, 121, 4, 4, ACO1); tela.px(px_ - 4, 123, CIANO)
    tela.texto('OCR', px_ + 44, 72, CIANO, tam=9, contorno=PRETO)
    if varre is not None:
        vx = int(varre)
        for y in range(91, 176, 2):
            tela.ret(vx, y, 2, 1, CIANO)
        halo(tela, vx, 130, 10, CIANO)
    # guarita
    gx = 238
    tela.ret(gx - 1, 128, 42, 49, PRETO); grad_v(tela, gx, 129, 40, 47, [CON2, CON1, CON1, CON0])
    tela.ret(gx - 4, 124, 48, 5, PRETO); tela.ret(gx - 3, 125, 46, 3, VMC1)
    tela.ret(gx + 6, 136, 26, 14, PRETO); tela.ret(gx + 7, 137, 24, 12, CHAMA0); tela.ret(gx + 7, 137, 24, 3, SOL)
    # caminhão
    r = D.caminhao(tela, xcam, 192, t, dist, raiox=raiox)
    # cancela (pivô na guarita, braço para a esquerda)
    pvx, pvy = gx - 4, 162
    ang = math.pi / 2 * suave(cancela)
    L = 46
    ex, ey = pvx - L * math.cos(ang), pvy - L * math.sin(ang)
    linha_grossa(tela, pvx, pvy, ex, ey, 4, PRETO)
    for k in range(6):
        a, b = k / 6, (k + 1) / 6
        tela.linha(pvx + (ex - pvx) * a, pvy + (ey - pvy) * a, pvx + (ex - pvx) * b, pvy + (ey - pvy) * b,
                   VERMELHO if k % 2 == 0 else BRANCO)
    tela.ret(pvx - 3, pvy - 3, 7, 18, PRETO); tela.ret(pvx - 2, pvy - 2, 5, 16, CIN1)
    return r


# ---------------------------------------------------------------- fábrica / armazém (de lado)
def paletes(n, w=61, h=26):
    """Posições (dx, dy) dos volumes dentro do contêiner: da frente (direita) para as portas."""
    out = []
    for k in range(10):
        col, lin = k // 2, k % 2
        out.append((w - 4 - (col + 1) * 11, h - 2 - (lin + 1) * 11))
    return out[:n]


def volume(tela, x, y, s=10):
    tela.ret(x - 1, y - 1, s + 2, s + 2, PRETO)
    tela.ret(x, y, s, s, CERAMICA); tela.ret(x, y, s, 1, BRANCO)
    tela.ret(x, y + s // 2, s, 1, LATAO); tela.ret(x + s // 2, y, 1, s, LATAO)


def cena_fabrica(tela, t, n_vol, xcam=92, dist=0.0, scroll=0.0, portas=1.0, raiox=True, ceu=CEU_TARDE, armazem=False,
                 empilhadeira=None):
    """Doca da fábrica (ou o armazém de destino), o caminhão de ré, a carga."""
    D.ceu(tela, 178, t, estrelas=False, cores=ceu)
    tela.disco(230 - scroll * .1, 54, 9, CEU4); tela.disco(230 - scroll * .1, 54, 6, SOL)
    # guindastes do porto ao longe (aparecem com o caminho)
    if scroll > 200:
        a = min(1.0, (scroll - 200) / 200)
        for k in range(3):
            gx = int(330 - (scroll - 200) * .35 + k * 40)
            if -40 < gx < 300:
                tela.ret(gx, 118, 2, 40, CEU1); tela.ret(gx + 14, 118, 2, 40, CEU1); tela.ret(gx - 10, 112, 44, 3, CEU1)
    horizonte(tela, t, 160, 0, 294, CEU2, luzes=False)
    # o prédio (fica para trás quando o caminhão sai)
    fx0 = int(-scroll)
    if fx0 > -120:
        tela.ret(fx0 - 1, 80, 92, 98, PRETO)
        grad_v(tela, fx0, 81, 90, 97, [CON2, CON1, CON1, CON0])
        for k in range(0, 90, 8): tela.ret(fx0 + k, 82, 1, 86, CON0)
        tela.ret(fx0 - 2, 76, 96, 5, PRETO); tela.ret(fx0 - 1, 77, 94, 3, VMC1)
        tela.texto('ARMAZÉM' if armazem else 'FÁBRICA', fx0 + 45, 88, PRETO, tam=9, centro=True)
        # porta da doca acesa
        tela.ret(fx0 + 56, 120, 34, 46, PRETO)
        grad_v(tela, fx0 + 57, 121, 33, 45, [CHAMA0, CHAMA1, LATAO, BRASA])
        for k in range(3):
            volume(tela, fx0 + 60 + k * 9, 155 - (k % 2) * 10, 8)
        tela.ret(fx0, 166, 92, 12, PRETO); tela.ret(fx0, 167, 90, 10, CON1); tela.ret(fx0, 167, 90, 1, CON2)
        for k in range(0, 90, 10): tela.ret(fx0 + k, 168, 6, 2, CHAMA0 if k % 20 else PRETO)
    D.asfalto(tela, 178, t, scroll=scroll)
    vols = paletes(n_vol)

    def dentro(tl, x, y, w, h):
        for dx, dy in vols: volume(tl, x + dx, y + dy, 10)

    r = D.caminhao(tela, xcam, 204, t, dist, raiox=dentro if raiox else None, portas=0.0)
    cx, cy, cw, ch = r
    if portas > 0:
        # portas abertas, dobradas contra o lado (perto do fundo)
        L = int(16 * portas)
        tela.ret(cx - 1, cy, L + 2, ch, PRETO)
        tela.ret(cx, cy + 1, L, ch - 2, LAR1)
        for k in range(2, L, 4): tela.ret(cx + k, cy + 2, 1, ch - 4, LAR0)
    if empilhadeira is not None:
        ex, carga_ = empilhadeira
        ex = int(ex)
        tela.ret(ex - 1, 154, 14, 13, PRETO); tela.ret(ex, 155, 12, 11, AMARELO); tela.ret(ex, 155, 12, 1, CHAMA0)
        tela.ret(ex + 3, 147, 1, 9, ACO2); tela.ret(ex + 9, 147, 1, 9, ACO2); tela.ret(ex + 3, 147, 7, 1, ACO2)
        tela.ret(ex + 12, 146, 2, 21, ACO1); tela.ret(ex + 12, 164, 9, 2, ACO2)
        tela.disco(ex + 3, 166, 2, ASF0); tela.disco(ex + 10, 166, 2, ASF0)
        if carga_: volume(tela, ex + 13, 153, 10)
    return r


def lacre(tela, x, y, fechado=1.0, rompido=False, numero=True):
    """Lacre de garrafa (bolt seal): cabeça amarela com número e o pino de aço."""
    dx = int((1 - fechado) * 26)
    # pino
    tela.ret(x - 1 + dx, y + 4, 4, 22, PRETO); tela.ret(x + dx, y + 5, 2, 20, ACO3)
    if rompido:
        tela.ret(x - 2 + dx, y + 14, 6, 3, FUNDO)
        tela.px(x + dx, y + 13, ACO4); tela.px(x + 1 + dx, y + 17, ACO4)
    # cabeça
    tela.ret(x - 6 + dx, y - 2, 14, 8, PRETO); tela.ret(x - 5 + dx, y - 1, 12, 6, AMARELO)
    tela.ret(x - 5 + dx, y - 1, 12, 1, CHAMA0)
    tela.ret(x - 2 + dx, y + 25, 6, 5, PRETO); tela.ret(x - 1 + dx, y + 26, 4, 3, ACO2)


# ================================================================ gancho
class Gancho(Cena):
    K = 3
    VX = 160

    def preparar(self):
        self.C = navio_corte(5, deck=[(r, 4) for r in range(10)] + [(r, 5) for r in (0, 1, 2, 7, 8, 9)])
        tl, tu = 2.6, 10.4
        self.travas = [(tl, tu)]
        yl = 127
        xs, ys = self.C.xy(*SLOT_NOSSO)
        self.X = [(0, 150.0), (1.6, XLANE), (5.0, XLANE), (7.4, xs + 5.0), (12, xs + 5.0)]
        self.Y = [(0, 70.0), (1.6, 70.0), (2.4, yl), (tl, yl), (3.2, yl), (5.0, 62.0), (7.4, 62.0), (9.8, ys - 5.0),
                  (tu, ys - 5.0), (11.6, 70.0)]

    def desenhar(self, tela, t, tg):
        car = carregando(t, self.travas)
        posto = t >= self.travas[0][1]
        C = self.C
        if posto: C.slots[SLOT_NOSSO] = P_LAR
        else: C.slots.pop(SLOT_NOSSO, None)
        st = (kf(t, self.X), kf(t, self.Y), trava_de(t, self.travas), car)
        cena_cais(tela, t, C, st, CEU_NOITE, caminhao=(P_LAR if t < self.travas[0][0] else False))
        # o protagonista
        if t >= 6.2:
            if car:
                x, y = kf(t, self.X) - 5, kf(t, self.Y) + 5
            elif posto:
                x, y = C.xy(*SLOT_NOSSO)
            else:
                x, y = XLANE - 5, YQ - 18
            mira(tela, x + 5, y + 5, t, 9)
            self.rot(tela, 'ESTE AQUI', int(x) - 20, int(y) - 22, AMARELO)
        if not VERTICAL:
            tela.ret(294, 0, W - 294, PALCO_H, FUNDO); tela.ret(294, 0, 1, PALCO_H, TRACO)
            u = fase(t, .4, 1.4)
            if t < 6.0:
                tela.texto('90%', 386, 40 - int((1 - ease(u)) * 20), AMARELO, tam=26, centro=True, contorno=PRETO)
                tela.texto('DA CARGA QUE NÃO', 386, 82, BRANCO, tam=9, centro=True, contorno=PRETO)
                tela.texto('VAI A GRANEL VIAJA', 386, 94, BRANCO, tam=9, centro=True, contorno=PRETO)
                tela.texto('EM CONTÊINERES', 386, 106, BRANCO, tam=9, centro=True, contorno=PRETO)
                for k in range(10):
                    D.cont_frente(tela, 336 + k * 10, 130, 9, 10, P_CI if k == 9 else OUTRAS[k % 6])
            else:
                tela.texto('A JORNADA', 386, 40, BRANCO, tam=17, centro=True, contorno=PRETO)
                tela.texto('DE UM', 386, 60, BRANCO, tam=17, centro=True, contorno=PRETO)
                tela.texto('CONTÊINER', 386, 80, LAR3, tam=17, centro=True, contorno=PRETO)
                tela.texto(CODIGO, 386, 110, LAR3, tam=9, centro=True, contorno=PRETO)
                D.cont_frente(tela, 356, 124, 60, 58, P_LAR, codigo=True)

    def sons(self, fx):
        self.sons_movimento(fx, self.X, self.travas, .1)
        mar_som(fx, self.t0, 11.5, .04)
        fx.put(fx.sino(76, 1.4), self.t0 + 6.2, .12)


# ================================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        D.ceu(tela, PALCO_H, t, cores=CEU_NOITE)
        D.mar(tela, 0, W, 170, PALCO_H, t)
        tela.texto('SÉRIE A JORNADA', W // 2, 16, ACO3, tam=9, centro=True, contorno=PRETO)
        n = int(t / .04)
        for j, linha in enumerate(("A JORNADA DE", "UM CONTÊINER")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 12)]
            tela.texto(vis, W // 2 - larg // 2, 34 + j * 32, BRANCO if j == 0 else LAR3, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto('DA FÁBRICA AO OUTRO LADO DO MAR', W // 2, 102, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 1.8:
            for k, (nome, cor) in enumerate(ETAPAS):
                x = W // 2 - 8 * 20 // 2 + k * 20
                c = cor if t > 1.8 + k * .3 else FUNDO2
                tela.ret(x, 128, 16, 16, PRETO); tela.ret(x + 1, 129, 14, 14, c)
                tela.texto(str(k + 1), x + 8, 133, PRETO, tam=9, centro=True)
        # o nosso, balançando no cabo
        yy = 150 + int(2 * math.sin(t * 2.2))
        xx = 40 + int(t * 6)
        tela.linha(xx + 20, 0, xx + 20, yy - 6, ACO2)
        D.spreader(tela, xx + 20, yy - 6, 40, 1.0, t)
        D.cont_lado(tela, xx, yy, 40, 17, P_LAR, t, codigo=True)
        x2 = 380 - int(t * 4)
        D.cont_lado(tela, x2, 158, 50, 20, P_AZ, t)

    def sons(self, fx):
        for k in range(8):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12)[k], .08), self.t0 + 1.8 + k * .3, .12)


# ================================================================ conheça a caixa
class Caixa(Cena):
    K = -1
    VX = 150
    CX, CY, CW, CH, CD = 30, 84, 200, 84, 40

    def y_caixa(self, t):
        u = fase(t, 0.2, 1.3)
        y = self.CY - (1 - ease(u)) * 150
        if 1.3 <= t < 1.7: y += 2 * math.sin((t - 1.3) / .4 * math.pi)
        return int(y + (1 if 25.2 < t < 30.6 and fase(t, 26, 29) > .5 else 0))

    def peso(self, t):
        u = fase(t, 26.0, 29.6)
        return 2200 + (30480 - 2200) * suave(u)

    def desenhar(self, tela, t, tg):
        grade(tela)
        if t < 30.8:
            self.perspectiva(tela, t)
        else:
            self.comparar(tela, t - 30.8)
        if t < 12.8:
            lin = [('MEDIDA', '20 PÉS', LAR3), ('EM METROS', '6,06×2,44×2,59', BRANCO)]
        elif t < 19.0:
            lin = [('PAREDES', 'AÇO CORRUGADO', LAR3), ('CHÃO', 'MADEIRA', BRANCO)]
        elif t < 25.2:
            lin = [('PEÇAS DE CANTO', '8', AMARELO), ('CADA UMA', 'FURO OVAL', BRANCO)]
        elif t < 30.8:
            lin = [('VAZIO (TARA)', '2.200 KG', BRANCO), ('MÁXIMO, CHEIO', '30.480 KG+', LAR3)]
        else:
            lin = [('20 PÉS', '1 TEU', LAR3), ('40 PÉS', '2 TEU', CIANO)]
        self.painel(tela, t, selo='CONHEÇA O CONTÊINER', cab=('CONHEÇA', 'A CAIXA', LAR3), linhas=lin,
                    estado=('PESO AGORA', f"{I.milhar(self.peso(t))} KG", AMARELO) if 25.2 <= t < 30.8 else None)

    def perspectiva(self, tela, t):
        x, y, w, h, d = self.CX, self.y_caixa(t), self.CW, self.CH, self.CD
        # sombra no chão
        dither(tela, x + 4, self.CY + h + 2, w + d - 6, 4, FUNDO, FUNDO2)
        acesas = ()
        if 19.0 <= t < 25.2:
            n = int((t - 19.4) / .6) + 1
            acesas = tuple(range(max(0, min(8, n))))
        pos = D.cont_iso(tela, x, y, w, h, d, P_LAR, t, codigo=True, acesas=acesas)
        faixa_brilho(tela, x, x + w, y, y + h, ((t * 60) % 420) - 60 + x, 7)
        if t > 1.4 and t < 6.6:
            self.rot(tela, 'O NOSSO CONTÊINER', x + w // 2 - 50, y - 30 - 8, AMARELO, alvo=(x + w // 2, y - 12))
        # medidas
        if 6.6 <= t < 12.8:
            u = ease(fase(t, 6.8, 8.0))
            yy = y + h + 8
            xb = x + int(w * u)
            tela.ret(x, yy, xb - x, 1, AMARELO); tela.ret(x, yy - 3, 1, 7, AMARELO)
            if u >= 1: tela.ret(x + w - 1, yy - 3, 1, 7, AMARELO); seta(tela, x + w - 2, yy, 1, 0, AMARELO, 4); seta(tela, x + 1, yy, -1, 0, AMARELO, 4)
            if u > .5: rotulo(tela, '6,06 M', x + w // 2, yy + 4, AMARELO, centro=True)
            u2 = ease(fase(t, 8.0, 9.0))
            if u2 > 0:
                xx = x - 8
                tela.ret(xx, y + h - int(h * u2), 1, int(h * u2), CIANO)
                if u2 >= 1: seta(tela, xx, y + 1, 0, -1, CIANO, 4); seta(tela, xx, y + h - 2, 0, 1, CIANO, 4)
                if u2 > .5:
                    tela.texto('2,59', xx - 3, y + h // 2 - 8, CIANO, tam=9, centro='d', contorno=PRETO)
                    tela.texto('M', xx - 3, y + h // 2 + 2, CIANO, tam=9, centro='d', contorno=PRETO)
            u3 = ease(fase(t, 9.0, 10.0))
            if u3 > 0:
                xa, ya = x + w + 6, y + h + 4
                tela.linha(xa, ya, xa + d * u3, ya - d * .6 * u3, VERDE)
                if u3 > .5: rotulo(tela, '2,44 M', xa + d // 2 + 6, ya - d // 3, VERDE)
        # chapa corrugada
        if 12.8 <= t < 19.0:
            ix, iy, iw, ih = lupa(tela, self.lupa_x(4, 150), 4, 150, 50, 'CHAPA DE CIMA PARA BAIXO', AMARELO)
            off = int(t * 8) % 12
            for k in range(-1, iw // 12 + 2):
                x0 = ix + k * 12 - off
                pts = [(x0, iy + 26), (x0 + 3, iy + 12), (x0 + 6, iy + 12), (x0 + 9, iy + 26), (x0 + 12, iy + 26)]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    if ix <= ax < ix + iw - 1 and ix <= bx < ix + iw - 1:
                        linha_grossa(tela, ax, ay, bx, by, 3, LAR2)
                        tela.linha(ax, ay - 1, bx, by - 1, LAR4)
            tela.texto('DOBRA = MAIS FIRME', ix + 4, iy + ih - 8, ACO4, tam=9)
            self.rot(tela, 'AÇO CORRUGADO', x + 58, y + h + 10, LAR3, alvo=(x + 70, y + h - 20))
        # peças de canto
        if 19.0 <= t < 25.2:
            n = max(0, min(8, int((t - 19.4) / .6) + 1))
            ix, iy, iw, ih = lupa(tela, self.lupa_x(4, 110), 4, 110, 50, 'PEÇA DE CANTO', AMARELO)
            tela.ret(ix + 18, iy + 4, 34, 30, PRETO); grad_v(tela, ix + 19, iy + 5, 32, 28, [CIN2, CIN1, CIN0])
            oval(tela, ix + 35, iy + 19, 9, 4.5, 0, PRETO)
            tela.texto(f"{n} DE 8", ix + 62, iy + 12, AMARELO, tam=9, contorno=PRETO)
            if n >= 8: tela.texto('(UMA ATRÁS)', ix + 58, iy + 24, ACO3, tam=9)
        # peso
        if 25.2 <= t < 30.8:
            p = self.peso(t)
            cheio = fase(t, 26, 29.6)
            ix, iy, iw, ih = lupa(tela, self.lupa_x(4, 120), 4, 120, 50, 'BALANÇA', AMARELO)
            tela.texto(f"{I.milhar(p)} KG", ix + iw // 2, iy + 6, AMARELO if cheio > .9 else BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto('VAZIO' if cheio < .05 else ('CHEIO' if cheio >= 1 else 'ENCHENDO...'), ix + iw // 2, iy + 26, ACO3, tam=9, centro=True)
            # caixas entrando pela porta
            if 0 < cheio < 1:
                for k in range(3):
                    u = (t * 1.5 + k / 3) % 1.0
                    bx = int(x + w + d + 30 - u * 40)
                    volume(tela, bx, y + h - 20 - k * 4, 8)

    def comparar(self, tela, u):
        """20 pés = 1 TEU; 40 pés = 2 TEU (o dobro de comprimento)."""
        y1, y2 = 120, 52
        D.cont_lado(tela, 30, y1, 100, 43, P_LAR, u, codigo=True)
        rotulo(tela, '20 PÉS = 1 TEU', 80, y1 + 50, LAR3, centro=True)
        a = ease(fase(u, .3, 1.4))
        x2 = int(lerp(300, 30, a))
        D.cont_lado(tela, x2, y2, 201, 43, P_AZ, u)
        if a >= 1:
            for yy in range(y2, y2 + 43, 3): tela.px(30 + 100, yy, BRANCO)
            rotulo(tela, '40 PÉS = 2 TEU', 130, y2 - 12, CIANO, centro=True)
            rotulo(tela, '1', 80, y2 + 16, BRANCO, tam=17, centro=True)
            rotulo(tela, '2', 180, y2 + 16, BRANCO, tam=17, centro=True)
        faixa_brilho(tela, 30, 130, y1, y1 + 43, ((u * 70) % 200) + 10, 5)

    def sons(self, fx):
        fx.put(baque(), self.t0 + 1.3, .5)
        for k in range(8):
            fx.put(tique(1800 + k * 120), self.t0 + 19.4 + k * .6, .2)
        fx.put(fx.chiado(3.6, 200, 900), self.t0 + 26.0, .05)
        fx.put(baque(80), self.t0 + 30.8 + 1.4, .35)


# ================================================================ o código e o dígito
class Codigo(Cena):
    K = -1
    VX = 240
    S = 'MPXU190426'
    LABS = [('DONO', 0, 3, CIANO), ('CATEGORIA', 3, 4, AMARELO), ('SÉRIE', 4, 10, BRANCO), ('DÍGITO', 10, 11, LAR3)]

    def preparar(self):
        self.vals, self.pesos, self.prods, self.soma, self.resto = D.conta_digito()

    def lay(self):
        """Posições dos 10 quadradinhos (x, y) e tamanho."""
        if VERTICAL:
            w, gap = 32, 3
            x0 = self.VX - (5 * w + 4 * gap) // 2
            return [(x0 + (i % 5) * (w + gap), 52 + (i // 5) * 62) for i in range(10)], w
        w, gap = 40, 6
        x0 = W // 2 - (10 * w + 9 * gap) // 2
        return [(x0 + i * (w + gap), 66) for i in range(10)], w

    def cod_grande(self, tela, t, y, tam, digito_vis):
        txt = 'MPXU 190426 ' + ('5' if digito_vis else '?')
        cx = self.VX if VERTICAL else W // 2
        larg = tela.largura_texto(txt, tam)
        x0 = cx - larg // 2
        cores = [CIANO] * 3 + [AMARELO] + [BRANCO] * 8 + [LAR3]
        n = int(t / .06)
        xs = []
        for i, ch in enumerate(txt):
            xi = x0 + tela.largura_texto(txt[:i + 1], tam) - tela.largura_texto(ch, tam) if ch != ' ' else None
            xs.append(xi)
            if ch == ' ' or i >= n: continue
            cor = cores[i]
            if i == 12 and not digito_vis and int(t * 3) % 2: cor = AMARELO
            tela.texto(ch, xi, y, cor, tam=tam, contorno=PRETO)
        return x0, larg, xs

    def desenhar(self, tela, t, tg):
        grade(tela)
        dig = not (12.8 <= t < 33.0)
        tam = 17 if VERTICAL else 26
        y = 10 if VERTICAL else 12
        x0, larg, xs = self.cod_grande(tela, t, y, tam, dig)
        if t < 6.6 and not VERTICAL:
            tela.texto('(INVENTADO PARA O VÍDEO)', W // 2, 40, ACO3, tam=9, centro=True, contorno=PRETO)
        # chaves com as partes do código
        if 6.6 <= t < 12.8:
            hh = 24 if tam == 26 else 16
            idx = [i for i, ch in enumerate('MPXU 190426 5') if ch != ' ']
            for j, (nm, a, b, cor) in enumerate(self.LABS):
                if t < 6.8 + j * 1.2: continue
                ia, ib = idx[a], idx[b - 1]
                xa = xs[ia]; xb = xs[ib] + tela.largura_texto('M', tam)
                yy = y + (26 if tam == 26 else 18)
                tela.ret(xa, yy, xb - xa, 1, cor); tela.ret(xa, yy - 3, 1, 3, cor); tela.ret(xb - 1, yy - 3, 1, 3, cor)
                tela.texto(nm, (xa + xb) // 2, yy + 4 + (11 if j % 2 else 0), cor, tam=9, centro=True, contorno=PRETO)
            if not VERTICAL:
                tela.texto('U = CONTÊINER DE CARGA', W // 2, 120, AMARELO, tam=17, centro=True, contorno=PRETO)
                tela.texto('AS 3 LETRAS DO DONO SÃO REGISTRADAS NO BIC', W // 2, 146, ACO3, tam=9, centro=True, contorno=PRETO)
        if 12.8 <= t < 19.0:
            cx = self.VX if VERTICAL else W // 2
            tela.texto('QUAL É O DÍGITO?', cx, 70 if VERTICAL else 80, AMARELO, tam=17, centro=True, contorno=PRETO)
            tela.texto('ELE SAI DE UMA CONTA COM', cx, 104, ACO3, tam=9, centro=True, contorno=PRETO)
            tela.texto('AS OUTRAS 10 POSIÇÕES', cx, 116, ACO3, tam=9, centro=True, contorno=PRETO)
            for k in range(10):
                bx = cx - 75 + k * 15
                on = (int(t * 6) - k) % 10 < 3
                tela.ret(bx, 140, 12, 12, PRETO); tela.ret(bx + 1, 141, 10, 10, AMARELO if on else FUNDO3)
        if 19.0 <= t < 36.6:
            self.conta(tela, t)
        if t >= 36.6:
            self.tipo(tela, t - 36.6)

    def conta(self, tela, t):
        pos, w = self.lay()
        voff = 0 if not VERTICAL else 0
        for i, (x, y) in enumerate(pos):
            ta = 19.2 + i * .4
            if t < ta: continue
            u = ease(fase(t, ta, ta + .3))
            yy = int(y - (1 - u) * 16)
            ch = self.S[i]
            letra = ch.isalpha()
            cor = CIANO if i < 3 else (AMARELO if i == 3 else BRANCO)
            pulso = 1 if (t > 33.0 and int(t * 4 + i) % 4 == 0) else 0
            tela.ret(x - 1, yy - 1, w + 2, 22, PRETO)
            tela.ret(x, yy, w, 20, FUNDO3 if not pulso else TRACO)
            tela.ret(x, yy, w, 1, cor)
            tela.texto(ch, x + w // 2, yy + 2, cor, tam=17, centro=True, contorno=PRETO)
            # valor
            if t > ta + .5:
                v = self.vals[i]
                dv = 22 if not VERTICAL else 21
                tela.texto(str(v), x + w // 2, yy + dv, AMARELO if letra else BRANCO, tam=17 if not VERTICAL else 9,
                           centro=True, contorno=PRETO)
            # peso
            tp = 25.0 + i * .25
            if t > tp:
                dy = 44 if not VERTICAL else 32
                tela.texto(f"×{self.pesos[i]}", x + w // 2, yy + dy, ACO3, tam=9, centro=True, contorno=PRETO)
            tq = 27.0 + i * .2
            if t > tq:
                dy = 56 if not VERTICAL else 42
                tela.ret(x + 2, yy + dy - 2, w - 4, 1, ACO1)
                tela.texto(f"={I.milhar(self.prods[i])}", x + w // 2, yy + dy, CHAMA0, tam=9, centro=True, contorno=PRETO)
        cx = self.VX if VERTICAL else W // 2
        ys = 140 if not VERTICAL else 178
        if 19.0 <= t < 24.8:
            tela.texto('M=24  P=27  U=32  X=36', cx, ys + (22 if not VERTICAL else 14), ACO3, tam=9, centro=True, contorno=PRETO)
            tela.texto('(A=10, B=12... PULA 11, 22 E 33)', cx, ys + (34 if not VERTICAL else 24), ACO2, tam=9,
                       centro=True, contorno=PRETO)
            if not VERTICAL:
                k = 3 - int((t - 19.0) / 1.0) if t < 22.0 else 0
                if k > 0: tela.texto(f"PAUSE E TENTE! {k}", cx, ys, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t >= 28.6:
            s = int(self.soma * min(1.0, (t - 28.6) / 1.2))
            tela.texto(f"SOMA = {I.milhar(s)}", cx, ys, BRANCO if s < self.soma else AMARELO, tam=17, centro=True, contorno=PRETO)
        if t >= 31.0:
            q = self.soma // 11
            tela.texto(f"{I.milhar(self.soma)} / 11 = {q}, SOBRA {self.resto}", cx, ys + (22 if not VERTICAL else 16), BRANCO,
                       tam=17 if not VERTICAL else 9, centro=True, contorno=PRETO)
        if t >= 33.0:
            u = fase(t, 33.0, 33.4)
            tela.texto('DÍGITO = 5', cx - 8, ys + (44 if not VERTICAL else 28), VERDE, tam=17 if not VERTICAL else 9, centro=True, contorno=PRETO)
            check(tela, cx + (60 if not VERTICAL else 32), ys + (48 if not VERTICAL else 28), VERDE)

    def tipo(self, tela, u):
        cx = self.VX if VERTICAL else W // 2
        tela.texto('22G1', cx, 56, BRANCO, tam=26, centro=True, contorno=PRETO)
        itens = [('2', '20 PÉS DE COMPRIMENTO', LAR3), ('2', '2,59 M DE ALTURA', CIANO), ('G1', 'CARGA GERAL (USO GERAL)', VERDE)]
        for j, (a, b, cor) in enumerate(itens):
            if u < .4 + j * .9: continue
            yy = 100 + j * 24
            tela.texto(a, cx - (110 if not VERTICAL else 80), yy, cor, tam=17, contorno=PRETO)
            tela.texto(b, cx - (80 if not VERTICAL else 54), yy + 4, BRANCO, tam=9, contorno=PRETO)
        D.cont_lado(tela, cx - 30 + int(4 * math.sin(u * 2)), 172, 60, 26, P_LAR, u, codigo=True)

    def sons(self, fx):
        for i in range(13):
            fx.put(tique(2000 + (i % 4) * 150), self.t0 + i * .06, .08)
        for i in range(10):
            fx.put(fx.blip(67 + i, .06), self.t0 + 19.2 + i * .4, .1)
            fx.put(tique(2600), self.t0 + 27.0 + i * .2, .08)
        fx.put(fx.sino(84, 1.2), self.t0 + 33.0, .22)
        fx.put(fx.sino(88, 1.2), self.t0 + 33.12, .16)


# ================================================================ 1 fábrica
class Fabrica(Cena):
    K = 0
    VX = 140
    T_LACRE = 15.0

    def n_vol(self, t): return max(0, min(10, int((t - 7.0) / .55) + 1)) if t >= 7.0 else 0

    def scroll(self, t):
        u = t - 20.4
        return 0.0 if u < 0 else 18 * u * u / 2 if u < 2 else 36 + 36 * (u - 2)

    def desenhar(self, tela, t, tg):
        portas = 1.0 - fase(t, 13.2, 14.2)
        sc = self.scroll(t)
        emp = None
        if 6.8 <= t < 12.8:
            ph = ((t - 7.0) / .55) % 1.0
            ex = 30 + 50 * (1 - abs(1 - 2 * ph))
            emp = (ex, ph < .5)
        r = cena_fabrica(tela, t, self.n_vol(t), dist=sc / 10, scroll=sc, portas=portas, raiox=t < 19.8,
                         empilhadeira=emp)
        cx, cy, cw, ch = r
        if t < 6.6:
            self.rot(tela, 'O NOSSO, VAZIO', cx + 4, cy - 22, AMARELO, alvo=(cx + 20, cy + 2))
            self.rot(tela, 'PORTAS ABERTAS', cx - 70, cy - 46, ACO3, alvo=(cx + 6, cy + 4))
        if 6.8 <= t < 13.0:
            tela.texto(f"{self.n_vol(t)} DE 10", cx + cw // 2, cy - 12, AMARELO, tam=9, centro=True, contorno=PRETO)
        if 13.2 <= t < 19.6:
            lx = self.lupa_x(150, 140)
            ix, iy, iw, ih = lupa(tela, lx, 6, 140, 78, 'AS PORTAS, DE PERTO', AMARELO, alvo=(cx + 2, cy + 12))
            D.cont_frente(tela, ix + 8, iy + 2, 64, 60, P_LAR)
            u = fase(t, 14.0, self.T_LACRE)
            lacre(tela, ix + 38, iy + 22, suave(u))
            if t >= self.T_LACRE:
                tela.texto('LACRE', ix + 80, iy + 14, AMARELO, tam=9, contorno=PRETO)
                tela.texto('Nº 004217', ix + 80, iy + 26, BRANCO, tam=9, contorno=PRETO)
                if t < self.T_LACRE + .3: halo(tela, ix + 40, iy + 24, 10, CHAMA0)
        if 19.8 <= t < 26.4:
            lx = self.lupa_x(150, 140)
            ix, iy, iw, ih = lupa(tela, lx, 6, 140, 70, 'INTEIRO OU ROMPIDO?', AMARELO)
            lacre(tela, ix + 30, iy + 10, 1.0)
            check(tela, ix + 26, iy + 46, VERDE)
            lacre(tela, ix + 96, iy + 10, 1.0, rompido=True)
            xis(tela, ix + 92, iy + 46, VERMELHO)
        if t >= 20.4:
            self.rot(tela, 'A CAMINHO DO PORTO →', cx + 6, cy - 20, AMARELO)
        est = ('CARGA', f"{self.n_vol(t)} DE 10 VOLUMES", BRANCO) if t < 13.2 else \
            (('LACRE', 'Nº 004217', AMARELO) if t >= self.T_LACRE else ('PORTAS', 'FECHANDO', ACO3))
        if t >= 20.4: est = ('DESTINO', 'O PORTO', VERDE)
        self.painel(tela, t, mov=0, estado=est)

    def sons(self, fx):
        for k in range(10):
            fx.put(baque(110), self.t0 + 7.0 + k * .55 + .45, .12)
        fx.put(zumbido(6.0, 70), self.t0 + 6.8, .05)
        fx.put(baque(90), self.t0 + 14.2, .3)
        fx.put(clac(), self.t0 + self.T_LACRE, .5)
        fx.put(zumbido(6.0, 38), self.t0 + 20.4, .12)


# ================================================================ 2 portão
class Portao(Cena):
    K = 1
    VX = 150
    CHECKS = [('CÓDIGO', CODIGO, 9.0), ('PLACA', 'PXL4E19', 10.6), ('AVARIAS', 'NENHUMA', 12.0),
              ('LACRE', 'PRESENTE', 15.6), ('DÍGITO', '5 CONFERE', 22.0)]

    def xcam(self, t):
        if t < 6.0:
            u = t / 6.0
            return -120 + (103 + 120) * (1 - (1 - u) ** 2)
        if t < 26.4: return 103.0
        u = t - 26.4
        return 103 + 20 * u * u

    def desenhar(self, tela, t, tg):
        varre = None
        if 6.8 <= t < 12.6:
            u = ((t - 6.8) / 2.9) % 1.0
            varre = 100 + 70 * u
        cancela = fase(t, 25.8, 26.6)
        r = cena_portao(tela, t, self.xcam(t), self.xcam(t) / 10, varre=varre, cancela=cancela)
        cx, cy, cw, ch = r
        if t < 6.6:
            self.rot(tela, 'O NOSSO', cx + 10, cy - 22, AMARELO, alvo=(cx + 20, cy + 2))
        if t < 6.6:
            self.rot(tela, 'CÂMERAS', PORTAL_X + 70, 60, CIANO, alvo=(PORTAL_X + 40, 86))
        if 6.8 <= t < 13.0:
            lx = self.lupa_x(6, 150)
            ix, iy, iw, ih = lupa(tela, lx, 4, 150, 52, 'CÂMERA 1: O CÓDIGO', CIANO)
            dither(tela, ix, iy, iw, ih, LAR2, LAR1)
            n = int((t - 7.0) / .16)
            txt = CODIGO
            tw = tela.largura_texto(txt, 17)
            x0 = ix + (iw - tw) // 2
            tela.texto(txt, x0, iy + 8, BRANCO, tam=17, contorno=LAR0)
            k = 0
            for i, chh in enumerate(txt):
                if chh == ' ': continue
                if k < n:
                    xi = x0 + tela.largura_texto(txt[:i + 1], 17) - tela.largura_texto(chh, 17)
                    tela.ret_vazado(xi - 1, iy + 6, tela.largura_texto(chh, 17) + 2, 19, VERDE)
                k += 1
            if n >= 11: tela.texto('LIDO', ix + iw - 28, iy + 28, VERDE, tam=9, contorno=PRETO)
        if 13.2 <= t < 19.4:
            lx = self.lupa_x(6, 120)
            ix, iy, iw, ih = lupa(tela, lx, 4, 120, 70, 'CÂMERA 2: AS PORTAS', CIANO, alvo=(cx + 2, cy + 10))
            D.cont_frente(tela, ix + 6, iy + 2, 52, 50, P_LAR)
            lacre(tela, ix + 30, iy + 14, 1.0)
            if t > 15.6:
                tela.ret_vazado(ix + 22, iy + 10, 18, 36, VERDE)
                tela.texto('LACRE', ix + 64, iy + 12, VERDE, tam=9, contorno=PRETO)
                tela.texto('OK', ix + 64, iy + 24, VERDE, tam=9, contorno=PRETO)
        if 19.6 <= t < 25.6:
            lx = self.lupa_x(6, 160)
            ix, iy, iw, ih = lupa(tela, lx, 4, 160, 54, 'O SISTEMA CONFERE', CIANO)
            tela.texto('MPXU190426 → 4.878', ix + 4, iy + 4, BRANCO, tam=9, contorno=PRETO)
            if t > 20.6: tela.texto('4.878 / 11 → SOBRA 5', ix + 4, iy + 16, BRANCO, tam=9, contorno=PRETO)
            if t > 22.0:
                tela.texto('PINTADO: 5', ix + 4, iy + 28, LAR3, tam=9, contorno=PRETO)
                check(tela, ix + 72, iy + 28, VERDE)
                tela.texto('CERTO', ix + 84, iy + 28, VERDE, tam=9, contorno=PRETO)
        if VERTICAL:
            self.painel(tela, t)
            return
        D.painel_jornada(tela, self.K, t, linhas=[], estado=None)
        for j, (nm, val, ta) in enumerate(self.CHECKS):
            y = 50 + j * 21
            tela.texto(nm, PX0, y, ACO3, tam=9, contorno=PRETO)
            if t >= ta:
                tela.texto(val, PX0 + 54, y, BRANCO, tam=9, contorno=PRETO)
                check(tela, PX0 + 160, y, VERDE)
            elif t >= 6.8:
                pts = '.' * (1 + int(t * 4) % 3)
                tela.texto('LENDO' + pts if ta < 13.2 or t >= 13.2 else '...', PX0 + 54, y, ACO2, tam=9, contorno=PRETO)
            else:
                tela.texto('-', PX0 + 54, y, ACO1, tam=9)
        tela.texto('CANCELA', PX0, 158 - 10 - 8, ACO3, tam=9, contorno=PRETO) if False else None

    def sons(self, fx):
        fx.put(zumbido(6.0, 40), self.t0, .1)
        for nm, val, ta in self.CHECKS:
            fx.put(fx.blip(84, .08), self.t0 + ta, .14)
        fx.put(fx.chiado(5.6, 1800, 4000), self.t0 + 7.0, .02)
        fx.put(zumbido(.8, 120), self.t0 + 25.8, .08)
        fx.put(zumbido(3.5, 40), self.t0 + 26.4, .12)


# ================================================================ 3 pátio
class Patio(Cena):
    K = 2
    VX = 120
    YL = 149                                  # spreader travando no caminhão (y)
    YA = 48                                   # altura de viagem

    def preparar(self):
        b = self.b
        rx = PAT['rows'][1] + 10
        y_p = y_pilha(3) - 8                  # spreader quando o nosso está na camada 3
        self.t1, self.t2 = b(5), b(8)         # trava / solta (1º movimento)
        self.t3, self.t4 = b(9) + 1.5, b(10) + 1.5
        self.travas = [(self.t1, self.t2), (self.t3, self.t4)]
        L = PAT['lane']
        self.X = [(0, 140.0), (5.8, L), (self.t1 + 3.0, L), (self.t1 + 5.6, rx), (self.t3 - 1.6, rx),
                  (self.t3 + 1.0, rx), (self.t3 + 2.2, L), (self.dur, L)]
        self.Y = [(0, self.YA), (12.0, self.YA), (14.6, self.YL), (self.t1 + .3, self.YL), (self.t1 + 2.8, self.YA),
                  (self.t1 + 5.6, self.YA), (self.t2 - .4, y_p), (self.t2 + .4, y_p), (self.t2 + 2.0, self.YA),
                  (self.t3 - 1.5, self.YA), (self.t3 - .2, y_p), (self.t3 + .2, y_p), (self.t3 + 1.0, self.YA + 30),
                  (self.t3 + 2.2, self.YA + 30), (self.t4 - .3, self.YL), (self.t4 + .3, self.YL), (self.dur, self.YL - 20)]

    def desenhar(self, tela, t, tg):
        car = carregando(t, self.travas)
        na_pilha = self.t2 <= t < self.t3
        cam = P_LAR if t < self.t1 else (False if t < self.t2 + .6 else None)
        cam_dx = 0.0
        if self.t2 + .6 <= t < 26.2:
            cam, cam_dx = False, -(t - self.t2 - .6) * 60
        if t >= 26.2:
            cam = P_LAR if t >= self.t4 else False
            cam_dx = -max(0.0, 1 - (t - 26.2) / 1.0) * 80
        ceu = CEU_NOITE if t < 26.2 else CEU_AURORA
        st = (kf(t, self.X), kf(t, self.Y), trava_de(t, self.travas), car)
        cena_patio(tela, t, st, ceu, caminhao=cam, cam_dx=cam_dx, nosso_na_pilha=na_pilha, navio=fase(t, 26.2, 29))
        if 6.8 <= t < 13.0:
            self.rot(tela, 'RTG', PAT['x1'] + 10, 20, AMARELO, alvo=(PAT['x1'] - 2, 30))
            self.rot(tela, 'PNEUS', PAT['x1'] + 14, 150, AMARELO, alvo=(PAT['x1'] + 6, 180))
            self.rot(tela, 'FAIXA DO CAMINHÃO', 8, 112, BRANCO, alvo=(PAT['lane'], 150))
            self.rot(tela, 'FILEIRAS', 160, 56, BRANCO, alvo=(150, 96))
        if t < 6.6:
            self.rot(tela, 'O NOSSO', 10, 120, AMARELO, alvo=(PAT['lane'], 156))
        # o nosso marcado
        if car:
            x, y = kf(t, self.X), kf(t, self.Y) + 8 + 11
        elif na_pilha:
            x, y = PAT['rows'][1] + 10, y_pilha(3) + 11
        else:
            x, y = PAT['lane'] + cam_dx, PAT['yb'] - 18
        if 19.6 <= t < 26.0 and na_pilha:
            mira(tela, x, y, t, 14, 14)
        mov = (1 if t >= self.t2 else 0) + (1 if t >= self.t4 else 0)
        if t < self.t1: est = ('POSIÇÃO', 'NO CAMINHÃO', BRANCO)
        elif car: est = ('POSIÇÃO', 'NO AR', AMARELO)
        elif na_pilha: est = ('POSIÇÃO', 'PILHA 2, CAMADA 3', BRANCO)
        else: est = ('POSIÇÃO', 'INDO PARA O CAIS', VERDE)
        if 26.2 <= t < 29.0 and not VERTICAL:
            tela.texto('O NAVIO CHEGOU!', 150, 70, CHAMA1, tam=17, centro=True, contorno=PRETO)
        self.painel(tela, t, mov=mov, estado=est)

    def sons(self, fx):
        self.sons_movimento(fx, self.X, self.travas, .1)
        fx.put(buzina(1.6), self.t0 + 26.4, .18)


# ================================================================ 4 guindaste
class Guindaste(Cena):
    K = 3
    VX = 160
    YA = 62

    def preparar(self):
        b = self.b
        self.C = navio_corte(7, deck=[(r, 4) for r in range(10)] + [(r, 5) for r in (0, 1, 8, 9)])
        xs, ys = self.C.xy(*SLOT_NOSSO)
        self.xs, self.ys = xs + 5.0, ys - 5.0
        self.tl, self.tu = b(8), b(13)            # trava no compasso 8 (19,2 s); solta no 13 (31,2 s)
        self.travas = [(self.tl, self.tu)]
        self.X = [(0, 236.0), (b(1) + .8, 236.0), (b(3), XLANE), (b(10), XLANE), (b(11) + 1.2, self.xs),
                  (self.tu + .8, self.xs), (self.dur, 200.0)]
        self.Y = [(0, self.YA), (b(3), self.YA), (b(5), 127.0), (b(10), 127.0), (b(10) + 1.6, self.YA),
                  (b(11) + 1.2, self.YA), (b(12) + 1.6, self.ys), (self.tu, self.ys), (self.tu + 1.6, self.YA),
                  (self.dur, self.YA)]
        # pinos: descem devagar dentro dos furos de b(5) a b(7); giram até b(8)
        self.desce = (b(5), b(7))
        self.gira = (self.tl - .6, self.tl)

    def desenhar(self, tela, t, tg):
        car = carregando(t, self.travas)
        C = self.C
        if t >= self.tu: C.slots[SLOT_NOSSO] = P_LAR
        else: C.slots.pop(SLOT_NOSSO, None)
        gira = fase(t, *self.gira)
        trav = gira if t < self.tl else trava_de(t, self.travas)
        st = (kf(t, self.X), kf(t, self.Y), trav, car)
        cena_cais(tela, t, C, st, CEU_NOITE, caminhao=(P_LAR if t < self.tl else False))
        if t < 6.6:
            self.rot(tela, 'TRILHOS', 8, 166, AMARELO, alvo=(D.STS['xl'], YQ))
            self.rot(tela, 'PERNAS', 136, 96, AMARELO, alvo=(D.STS['xs'] + 2, 110))
            self.rot(tela, 'LANÇA', 230, 18, AMARELO, alvo=(250, 36))
        if 6.6 <= t < 12.6:
            tx = kf(t, self.X)
            self.rot(tela, 'TROLE', int(tx) + 14, 52, AMARELO, alvo=(int(tx) + 6, 42))
            self.rot(tela, 'CABINE', int(tx) - 60, 64, AMARELO, alvo=(int(tx) - 20, 52))
            self.rot(tela, 'SPREADER', int(tx) + 12, int(kf(t, self.Y)) + 8, AMARELO, alvo=(int(tx) + 6, int(kf(t, self.Y)) + 1))
        if 12.0 <= t < 24.4:
            d = fase(t, *self.desce)
            lx = self.lupa_x(150, 140)
            zoom_trava(tela, lx, 48, 140, 70, d, gira, t)
            tela.linha(lx, 90, XLANE + 7, 128, AMARELO)
        if t >= 6.2 and not (12.0 <= t < 24.4):
            if car: x, y = kf(t, self.X), kf(t, self.Y) + 10
            elif t >= self.tu: x, y = self.xs, self.ys + 10
            else: x, y = XLANE, YQ - 12
            mira(tela, x, y, t, 9)
        mov = 3 if t >= self.tu else 2
        if t >= 30.6:
            est = ('UM GUINDASTE FAZ', '25 A 30 POR HORA', VERDE)
        elif car:
            est = ('POSIÇÃO', 'NO SPREADER', AMARELO)
        elif t >= self.tu:
            est = ('POSIÇÃO', 'NO NAVIO', VERDE)
        else:
            est = ('PINOS', 'GIRANDO' if 0 < gira < 1 else 'SOLTOS', ACO3)
        self.painel(tela, t, mov=mov, estado=est)

    def sons(self, fx):
        self.sons_movimento(fx, self.X, self.travas, .1)
        for (ta, ya), (tb, yb) in zip(self.Y, self.Y[1:]):
            if abs(yb - ya) > 10 and tb - ta > .3:
                fx.put(zumbido(tb - ta, 62), self.t0 + ta, .06)
        mar_som(fx, self.t0, self.dur - .5, .03)


# ================================================================ o guindaste no ritmo
class Ritmo(Cena):
    K = 3
    VX = 160

    def preparar(self):
        self.C0 = navio_corte(7, deck=[(r, 4) for r in range(10)] + [(r, 5) for r in (0, 1, 8, 9)])
        self.C0.slots[SLOT_NOSSO] = P_LAR
        livres = [(r, 5) for r in (2, 3, 5, 6, 7)] + [(r, 6) for r in range(10)] + [(r, 7) for r in range(10)]
        self.alvos = livres[:len(self.B)]
        rng = np.random.default_rng(11)
        self.pals = [OUTRAS[int(rng.integers(0, len(OUTRAS)))] for _ in self.alvos]
        self.n = len(self.alvos)

    def ciclo(self, t):
        """(x, y, trava, carregando, k) no compasso k."""
        k = max(0, min(self.n - 1, int(np.searchsorted(self.B, t + 1e-6)) - 1))
        b0 = self.B[k]
        u = t - b0
        bb = self.bar
        xs, ys = self.C0.xy(*self.alvos[k])
        xs += 5; ys -= 5
        yl, ya = 127.0, 70.0 if self.alvos[k][1] < 7 else 60.0
        keys_x = [(0, XLANE), (.2 * bb, XLANE), (.45 * bb, xs), (.75 * bb, xs), (.95 * bb, XLANE), (bb, XLANE)]
        keys_y = [(0, yl), (.2 * bb, ya), (.45 * bb, ya), (.7 * bb, ys), (.75 * bb, ys), (.85 * bb, ya), (.92 * bb, ya), (bb, yl)]
        x, y = kf(u, keys_x), kf(u, keys_y)
        car = u < .75 * bb
        tr = 1.0 if car else 0.0
        return x, y, tr, car, k

    def desenhar(self, tela, t, tg):
        x, y, tr, car, k = self.ciclo(t)
        C = self.C0
        for j, a in enumerate(self.alvos):
            if j < k or (j == k and not car): C.slots[a] = self.pals[j]
            else: C.slots.pop(a, None)
        # caminhão: chega pela esquerda no fim do compasso anterior
        u = t - self.B[k]
        bb = self.bar
        if car:
            cam, dx = False, -min(1.0, max(0.0, (u - .3 * bb) / (.3 * bb))) * 90
        else:
            cam, dx = (self.pals[k + 1] if k + 1 < self.n else P_CI), -(1 - min(1.0, (u - .75 * bb) / (.2 * bb))) * 90
        cena_cais(tela, t, C, (x, y, tr, car), CEU_NOITE, caminhao=cam, cam_x=XLANE + dx)
        if car:
            D.cont_frente(tela, x - 5, y + 5, 10, 11, self.pals[k])
        xs, ys = C.xy(*SLOT_NOSSO)
        mira(tela, xs + 5, ys + 5, t, 8)
        # selo de velocidade pulsando na batida
        p = self.L.env('kick', tg, .12)
        bx = 196 if not VERTICAL else 196
        tela.ret(bx - 1, 51, 50, 22, PRETO)
        tela.ret(bx, 52, 48, 20, VMC1 if p > .3 else VMC0)
        tela.texto('60×', bx + 24, 55 - int(p * 2), BRANCO, tam=17, centro=True, contorno=PRETO)
        n_mov = sum(1 for j in range(self.n) if self.B[j] + .75 * bb <= t)
        self.painel(tela, t, mov=3, estado=('NESTE NAVIO, AGORA', (f"+{n_mov} CAIXAS" if n_mov != 1 else '+1 CAIXA'), AMARELO))

    def sons(self, fx):
        for j in range(self.n):
            fx.put(clac(), self.t0 + self.B[j], .42, -.1)
            fx.put(clac(), self.t0 + self.B[j] + .75 * self.bar, .3, .1)
            fx.put(zumbido(.5 * self.bar, 58), self.t0 + self.B[j] + .2 * self.bar, .05)


# ================================================================ 5 plano de carga
class Plano(Cena):
    K = 4
    VX = 130
    GX, GY, CWp, CHp = 70, 70, 14, 11          # grade: 10 fileiras x 8 camadas
    ROWS, TIERS = 10, 8

    def preparar(self):
        rng = np.random.default_rng(19)
        self.peso = {}
        for r in range(self.ROWS):
            for k in range(self.TIERS):
                base = 28 - k * 2.6
                self.peso[(r, k)] = int(max(4, min(30, base + rng.integers(-2, 3))))
        self.peso[(4, 5)] = 14
        self.ordem = sorted(self.peso, key=lambda rk: (rk[1], abs(rk[0] - 4.5)))

    def cell(self, r, k):
        y = self.GY + (self.TIERS - 1 - k) * self.CHp + (0 if k >= 4 else 4)
        return self.GX + r * self.CWp, y

    def cor_peso(self, p):
        return VMC1 if p >= 24 else (LAR1 if p >= 18 else (LAR3 if p >= 12 else CHAMA0))

    def desenhar(self, tela, t, tg):
        grade(tela)
        # folha (azul de projeto)
        u = ease(fase(t, .2, 1.4))
        sx0, sy0, sw = 8, 6, 280
        sh = int(196 * u)
        tela.ret(sx0 - 1, sy0 - 1, sw + 2, sh + 2, PRETO)
        dither(tela, sx0, sy0, sw, sh, AZC1, D.AZC0)
        for x in range(sx0, sx0 + sw, 10): tela.ret(x, sy0, 1, sh, D.AZC0)
        for y in range(sy0, sy0 + sh, 10): tela.ret(sx0, y, sw, 1, D.AZC0)
        if u < 1: return self.fim(tela, t)
        tela.texto('PLANO DE CARGA', sx0 + 6, sy0 + 4, BRANCO, tam=9, contorno=PRETO)
        self.navio_mini(tela, t)
        self.grade_baia(tela, t)
        self.estabilidade(tela, t)
        self.fim(tela, t)

    def fim(self, tela, t):
        if t < 6.6: est = ('CADA CAIXA', 'TEM UMA VAGA', BRANCO)
        elif t < 24.6: est = ('VAGA = 3 NÚMEROS', 'BAIA-FILEIRA-CAMADA', AMARELO)
        elif t < 30.6: est = ('REGRA', 'PESADO EMBAIXO', VERDE)
        else: est = ('VAGA DO NOSSO', '13-02-06', LAR3)
        self.painel(tela, t, mov=3, estado=est)

    def navio_mini(self, tela, t):
        """Navio de lado no alto da folha: baias numeradas da proa (direita) para trás."""
        x0, yw, L = 26, 46, 250
        poligono(tela, [(x0, yw - 8), (x0 + L - 10, yw - 8), (x0 + L, yw - 13), (x0 + L - 8, yw), (x0 + 6, yw)], CAS1)
        tela.ret(x0, yw - 8, L - 10, 1, ACO2); tela.ret(x0 + 6, yw, L - 14, 1, MAR3)
        tela.ret(x0 + 16, yw - 22, 8, 14, CERAMICA)
        if t < 6.6: return
        hl = None
        if 12.6 <= t < 18.6:
            hl = min(13, 1 + 2 * int((t - 12.8) / .6))
        elif t >= 30.6 or (6.6 <= t < 12.6):
            hl = 13
        for j in range(17):
            n = j + 1                                    # baia 01 na proa
            bx = x0 + L - 26 - j * 12
            if bx < x0 + 28: break
            cor = OUTRAS[j % 5][2]
            if hl is not None and n == hl: cor = LAR2
            tela.ret(bx - 1, yw - 17, 11, 10, PRETO); tela.ret(bx, yw - 16, 9, 8, cor)
            if n % 2 == 1 and n <= 17 and (t >= 12.6):
                tela.texto(f"{n:02d}", bx + 4, yw - 27 + (0 if (n // 2) % 2 == 0 else -0), ACO4 if n != hl else AMARELO,
                           tam=9, centro=True) if n in (1, 5, 9, 13, 17) or n == hl else None
        if t >= 12.6 and t < 18.6 and not VERTICAL:
            tela.texto('PROA', x0 + L - 4, yw + 3, BRANCO, tam=9, centro=True)
            tela.texto('ÍMPAR = 20 PÉS', 236, 56, BRANCO, tam=9, centro=True, contorno=PRETO)
            tela.texto('PAR = 40 PÉS', 236, 66, CIANO, tam=9, centro=True, contorno=PRETO)
        if hl is not None:
            bx = x0 + L - 26 - (hl - 1) * 12
            mira(tela, bx + 4, yw - 12, t, 7, 6)
            tela.texto('BAIA 13', bx + 4, yw - 6 + 4, AMARELO, tam=9, centro=True, contorno=PRETO) if t >= 30.6 else None

    def grade_baia(self, tela, t):
        GX, GY, CW, CH = self.GX, self.GY, self.CWp, self.CHp
        # casco em volta do porão
        xa, xb = GX - 6, GX + self.ROWS * CW + 6
        yh = GY + 4 * CH + 4
        ybot = GY + 8 * CH + 10
        poligono(tela, [(xa, yh - 2), (xb, yh - 2), (xb, ybot - 6), (xb - 6, ybot), (xa + 6, ybot), (xa, ybot - 6)], D.AZC0)
        tela.ret(xa, yh - 2, xb - xa, 1, BRANCO)
        tela.ret(GX - 2, GY + 4 * CH, self.ROWS * CW + 4, 3, ACO3)             # tampa da escotilha
        fill_n = 0
        if t >= 24.6:
            fill_n = int((t - 24.8) / .06)
        mostrados = set(self.ordem[:max(0, fill_n)]) if t >= 24.6 else set()
        for r in range(self.ROWS):
            for k in range(self.TIERS):
                x, y = self.cell(r, k)
                tela.ret_vazado(x, y, CW + 1, CH + 1, MAR3)
                if (r, k) in mostrados:
                    p = self.peso[(r, k)]
                    nosso = (r, k) == SLOT_NOSSO
                    tela.ret(x + 1, y + 1, CW - 1, CH - 1, self.cor_peso(p) if not (nosso and t >= 30.6) else LAR2)
                    tela.texto(str(p), x + CW // 2 + 1, y + 2, PRETO, tam=9, centro=True)
        if t >= 30.6:
            x, y = self.cell(*SLOT_NOSSO)
            if int(t * 4) % 2: tela.ret_vazado(x - 1, y - 1, CW + 3, CH + 3, AMARELO)
            mira(tela, x + CW // 2, y + CH // 2, t, 10, 9)
            self.rot(tela, 'O NOSSO', x + 26, GY - 13, AMARELO, alvo=(x + CW // 2 + 2, y))
        # eixos
        if 6.6 <= t:
            u = ease(fase(t, 6.6, 7.6))
            yb = GY + 8 * CH + 16
            tela.ret(GX, yb, int(self.ROWS * CW * u), 1, VERDE)
            tela.texto('FILEIRA', GX + self.ROWS * CW // 2, yb + 4, VERDE, tam=9, centro=True, contorno=PRETO) if t >= 7.6 and t < 18.6 else None
            u2 = ease(fase(t, 7.6, 8.6))
            xc = GX - 14
            h = int(8 * CH * u2)
            tela.ret(xc, GY + 8 * CH + 4 - h, 1, h, ROSA)
            if u2 >= 1:
                seta(tela, xc, GY - 4, 0, -1, ROSA, 4)
                if t < 18.6: tela.texto('CAMADA', xc - 2, GY - 16, ROSA, tam=9, centro=True, contorno=PRETO)
        if t >= 18.6:
            m = self.ROWS // 2
            nshow = int((t - 18.8) / .25) + 1
            for r in range(self.ROWS):
                d = (m - r) if r < m else (r - m + 1)
                if d > nshow: continue
                num = 2 * (m - r) if r < m else 2 * (r - m) + 1
                x, _ = self.cell(r, 0)
                tela.texto(f"{num:02d}", x + CW // 2 + 1, GY + 8 * CH + 20, VERDE if num != 2 else AMARELO, tam=9, centro=True)
            for y in range(GY - 6, GY + 8 * CH + 10, 3): tela.px(GX + m * CW, y, BRANCO)
            for k in range(self.TIERS):
                if (t - 19.6) / .3 < k: continue
                _, y = self.cell(0, k)
                tela.texto(str(k + 1), GX - 8, y + 2, ROSA if k != 5 else AMARELO, tam=9, centro=True)
            if not VERTICAL and t < 24.6:
                tela.texto('BOMBORDO', GX + 2, GY + 8 * CH + 32, ACO4, tam=9)
                tela.texto('BORESTE', GX + self.ROWS * CW - 44, GY + 8 * CH + 32, ACO4, tam=9)
        if t >= 24.6 and not VERTICAL:
            yb = GY + 8 * CH + 30
            for j, (nm, p) in enumerate((('PESADO', 28), ('MÉDIO', 20), ('LEVE', 8))):
                tela.ret(GX + j * 52, yb, 8, 8, self.cor_peso(p))
                tela.texto(nm, GX + j * 52 + 11, yb, BRANCO, tam=9, contorno=PRETO)
            tela.texto('NÚMEROS = TONELADAS', GX, yb + 11, ACO4, tam=9, contorno=PRETO)

    def estabilidade(self, tela, t):
        """Dois navios em corte balançando: pesado embaixo (ok) x pesado em cima."""
        if t < 24.6 or VERTICAL: return
        for j in range(2):
            cx, cy = 252, 96 + j * 52
            ang = (.10 if j == 0 else .32) * math.sin(t * 2.2 + j)
            if j == 1 and int(t / 3) % 2: ang = .42 * math.sin(t * 2.2 + j)
            quad(tela, cx, cy + 6, 34, 10, ang, CAS1)
            for k in range(3):
                pesado = (k == 0) if j == 0 else (k == 2)
                dy = -3 - k * 7
                c, s = math.cos(ang), math.sin(ang)
                px_, py_ = cx - dy * s, cy + 6 + dy * c - 4
                quad(tela, px_, py_, 26, 6, ang, VMC1 if pesado else CHAMA0)
            if j == 0: check(tela, cx - 4, cy + 18, VERDE)
            else: xis(tela, cx - 3, cy + 18, VERMELHO)

    def sons(self, fx):
        fx.put(fx.chiado(1.2, 800, 3000), self.t0 + .2, .05)
        for k in range(7):
            fx.put(fx.blip(72 + k, .05), self.t0 + 12.8 + k * .6, .08)
        for k in range(0, 80, 4):
            fx.put(tique(1500 + k * 10), self.t0 + 24.8 + k * .06, .06)
        fx.put(fx.sino(84, 1.0), self.t0 + 30.6, .2)


# ================================================================ 6 amarração
class Amarracao(Cena):
    K = 5
    VX = 110
    ROWS = 6
    NOSSO = (3, 5)

    def deck_y(self, t): return int(lerp(20, 140, ease(fase(t, 7.2, 8.8))))

    def corte(self, t):
        C = D.Corte(x0=40, rows=self.ROWS, deck_y=self.deck_y(t), tiers_h=4, tiers_d=3, s=2)
        rng = np.random.default_rng(4)
        for r in range(self.ROWS):
            for k in range(3): C.slots[(r, k)] = OUTRAS[int(rng.integers(0, len(OUTRAS)))]
            if r != 1 or t >= 6.0: C.slots[(r, 3)] = OUTRAS[int(rng.integers(0, len(OUTRAS)))]
        if t >= 12.4:
            for r in range(self.ROWS):
                if t >= 12.4 + r * .3: C.slots[(r, 4)] = OUTRAS[(r * 3 + 1) % len(OUTRAS)]
        if t >= 17.0:
            for r in (0, 1, 2, 4, 5): C.slots[(r, 5)] = OUTRAS[(r * 5 + 2) % len(OUTRAS)]
            C.slots[self.NOSSO] = P_LAR
        return C

    def desenhar(self, tela, t, tg):
        C = self.corte(t)
        D.ceu(tela, PALCO_H, t, cores=CEU_NOITE)
        yw = C.deck_y + 24
        D.mar(tela, 0, 294, yw, PALCO_H, t)
        tampa_on = t >= 12.0
        C.casco(tela, yw, t, tampa=tampa_on)
        if 0 <= t < 7.2:
            # guias de célula acesas
            for r in range(self.ROWS + 1):
                gx = C.x0 + r * C.cw - (1 if r == self.ROWS else 0)
                if int(t * 3 + r) % 2: tela.ret(gx, C.deck_y + 8, 1, C.hf - C.deck_y - 8, CIANO)
        C.cargas(tela, t)
        # contêiner descendo nas guias (fileira 1, camada 4)
        if t < 6.0:
            x, y = C.xy(1, 3)
            yy = int(lerp(-30, y, ease(fase(t, .4, 5.6))))
            D.cont_frente(tela, x + 1, yy + 1, C.cw - 1, C.ch - 1, P_CI)
            tela.linha(x + 10, 0, x + 10, yy, ACO2)
        if t < 7.2:
            self.rot(tela, 'GUIAS DE CÉLULA', 180, 60, CIANO, alvo=(C.x0 + 2 * C.cw, 70))
            self.rot(tela, 'PORÃO', 180, 100, ACO3, alvo=(C.x1 - 4, 110))
        # tampa descendo (antes de assentar)
        if 7.2 <= t < 12.0:
            ytampa = int(lerp(10, C.deck_y, ease(fase(t, 8.6, 12.0))))
            tela.linha(C.x0 + 60, 0, C.x0 + 60, ytampa, ACO2)
            C.tampa(tela, ytampa)
        if 7.2 <= t < 14.4:
            self.rot(tela, 'TAMPA DE ESCOTILHA', 176, C.deck_y - 34, AMARELO, alvo=(C.x1 - 10, C.deck_y + 2))
        # o nosso descendo
        if 14.6 <= t < 17.0:
            x, y = C.xy(*self.NOSSO)
            yy = int(lerp(-30, y, ease(fase(t, 14.6, 16.8))))
            D.cont_frente(tela, x + 1, yy + 1, C.cw - 1, C.ch - 1, P_LAR, codigo=True)
        # travas entre camadas (brilham)
        if 14.6 <= t < 22.0:
            for r in range(self.ROWS):
                for k in (5,):
                    if (r, k) in C.slots:
                        x, y = C.xy(r, k)
                        for dx in (2, C.cw - 2):
                            halo(tela, x + dx, y + C.ch, 3, AMARELO)
                            tela.ret(x + dx - 1, y + C.ch - 1, 3, 3, ACO4)
            lx = self.lupa_x(178, 112)
            self.zoom_cone(tela, lx, 8, 112, 96, fase(t, 17.4, 18.0), t)
            x, y = C.xy(*self.NOSSO)
            tela.linha(lx, 60, x + C.cw - 2, y + C.ch, AMARELO)
        # barras de amarração com esticador
        if t >= 22.0:
            n = int((t - 22.0) / .25) + 1
            j = 0
            for r in range(self.ROWS):
                x, y = C.xy(r, 4)
                yb = C.deck_y
                for (ax, bx) in ((x + 1, x + C.cw - 2), (x + C.cw - 2, x + 1)):
                    j += 1
                    if j > n: continue
                    u = min(1.0, (t - 22.0 - (j - 1) * .25) / .25)
                    tela.linha(ax, yb - 1, ax + (bx - ax) * u, yb - 1 - (yb - 1 - (y + 1)) * u, ACO4)
                    tela.ret(ax - 1, yb - 4, 3, 3, LATAO)
            lx = self.lupa_x(178, 112)
            self.zoom_esticador(tela, lx, 8, 112, 96, t)
            self.rot(tela, 'BARRAS DE AMARRAÇÃO', 8, C.deck_y - 64, AMARELO, alvo=(C.x0 + 8, C.deck_y - 14))
        x, y = C.xy(*self.NOSSO)
        if t >= 17.0:
            mira(tela, x + C.cw // 2, y + C.ch // 2, t, 13, 13)
        if t < 7.2: est = ('NO PORÃO', 'GUIAS DE CÉLULA', CIANO)
        elif t < 14.6: est = ('PORÃO', 'TAMPA FECHADA', AMARELO)
        elif t < 22.0: est = ('CANTOS', 'TRAVADOS' if t >= 18.0 else 'ENCAIXANDO', VERDE if t >= 18 else ACO3)
        else: est = ('PILHA', 'AMARRADA' if t >= 27.0 else 'APERTANDO', VERDE if t >= 27 else ACO3)
        self.painel(tela, t, mov=3, estado=est)

    def zoom_cone(self, tela, x, y, w, h, gira, t):
        """Lupa: trava giratória entre dois contêineres (de lado)."""
        ix, iy, iw, ih = lupa(tela, x, y, w, h, 'TRAVA ENTRE CAIXAS', AMARELO)
        cx = ix + 40
        # peça de canto de cima (do contêiner de cima)
        tela.ret(cx - 16, iy + 4, 32, 22, PRETO); grad_v(tela, cx - 15, iy + 5, 30, 20, [LAR3, LAR2, LAR1])
        tela.ret(cx - 7, iy + 20, 14, 6, FUNDO)
        # de baixo
        tela.ret(cx - 16, iy + 38, 32, 22, PRETO); grad_v(tela, cx - 15, iy + 39, 30, 20, [CIN2, CIN1, CIN0])
        tela.ret(cx - 7, iy + 38, 14, 6, FUNDO)
        # a trava: chapa no meio e dois cones que giram (largura muda com o giro)
        tela.ret(cx - 12, iy + 30, 24, 4, PRETO); tela.ret(cx - 11, iy + 31, 22, 2, ACO3)
        a = math.pi / 2 * suave(gira)
        wc = int(5 + 7 * abs(math.cos(a)))
        for yy, dy in ((iy + 22, -1), (iy + 36, 1)):
            tela.ret(cx - wc, yy - (4 if dy < 0 else 0), 2 * wc, 6, ACO4)
            tela.ret(cx - wc, yy - (4 if dy < 0 else 0), 2 * wc, 1, BRANCO)
        # alavanca
        ang = a
        tela.linha(cx + 12, iy + 32, cx + 12 + 14 * math.cos(ang), iy + 32 + 14 * math.sin(ang), AMARELO)
        trav = gira >= 1
        tela.texto('TRAVADO' if trav else 'GIRA 90°', ix + 66, iy + 30, VERDE if trav else ACO3, tam=9, contorno=PRETO)
        if trav: check(tela, ix + 70, iy + 44, VERDE)

    def zoom_esticador(self, tela, x, y, w, h, t):
        """Lupa: o esticador (rosca dos dois lados) girando e puxando a barra."""
        ix, iy, iw, ih = lupa(tela, x, y, w, h, 'ESTICADOR', AMARELO)
        aperto = suave(fase(t, 24.0, 27.0))
        cx, cy = ix + 50, iy + 40
        L = int(26 - 8 * aperto)
        tela.linha(cx - 40, cy + 20, cx - L, cy + 4, ACO4)          # barra (de baixo)
        tela.linha(cx + L, cy - 4, cx + 40, cy - 24, ACO4)          # barra (para o contêiner)
        quad(tela, cx, cy, 2 * L, 9, -.38, LATAO)
        fase_ = t * 9 * (1 - aperto) if aperto < 1 else 0
        for k in range(-2, 3):
            off = ((k * 8 + fase_ * 3) % 40) - 20
            if abs(off) < L - 2:
                tela.px(cx + off * math.cos(-.38), cy + off * math.sin(-.38), CHAMA0)
        tela.texto('APERTADO' if aperto >= 1 else 'GIRANDO', ix + 4, iy + ih - 10, VERDE if aperto >= 1 else ACO3, tam=9, contorno=PRETO)
        if aperto >= 1: check(tela, ix + 62, iy + ih - 10, VERDE)

    def sons(self, fx):
        fx.put(zumbido(5.2, 60), self.t0 + .4, .06)
        fx.put(baque(70), self.t0 + 5.6, .3)
        fx.put(zumbido(3.4, 55), self.t0 + 8.6, .06)
        fx.put(baque(55), self.t0 + 12.0, .45)
        for r in range(self.ROWS): fx.put(baque(95), self.t0 + 12.4 + r * .3 + .25, .12)
        fx.put(baque(80), self.t0 + 16.8, .25)
        fx.put(clac(), self.t0 + 18.0, .45)
        for k in range(12): fx.put(tique(1700), self.t0 + 22.0 + k * .25, .07)
        for k in range(10): fx.put(tique(900 + k * 40), self.t0 + 24.0 + k * .3, .07)
        fx.put(clac(), self.t0 + 27.0, .4)


# ================================================================ 7 viagem
class Viagem(Cena):
    K = 6
    VX = 150

    def ceu_mix(self, tela, t):
        etapas = [(0, CEU_DIA), (8, CEU_DIA), (11, CEU_TARDE), (14, CEU_NOITE), (27, CEU_NOITE), (31, CEU_AURORA)]
        a, b, u = etapas[0][1], etapas[0][1], 0.0
        for (ta, ca), (tb, cb) in zip(etapas, etapas[1:]):
            if ta <= t < tb:
                a, b, u = ca, cb, (t - ta) / (tb - ta)
                break
        else:
            a = b = etapas[-1][1]
        D.ceu(tela, 150, t, estrelas=False, cores=a)
        if a is not b and u > 0:
            tmp = tela.buf[:150].copy()
            D.ceu(tela, 150, t, estrelas=False, cores=b)
            yy, xx = np.mgrid[0:150, 0:W]
            m = LG.BAYER8[yy % 8, xx % 8] >= u
            tela.buf[:150][m] = tmp[m]
        if 13 < t < 30:
            for k in range(30):
                x = (k * 97 + 13) % W; y = (k * 53 + 7) % 70
                if math.sin(t * 1.7 + k * 2.3) > -.2: tela.px(x, y, BRANCO if k % 4 == 0 else ACO3)
        # sol / lua atravessando
        if t < 13.5:
            sx, sy = 40 + t * 16, 30 + t * t * .4
            luz(tela, sx, sy, 6, BRANCO, SOL, CEU4)
        elif t < 29:
            tela.disco(260 - (t - 14) * 8, 34, 6, ACO4); tela.disco(262 - (t - 14) * 8, 32, 5, CEU0 if t < 27 else CEU1)

    def desenhar(self, tela, t, tg):
        self.ceu_mix(tela, t)
        for k in range(4):
            x = int((k * 130 - t * (6 + k)) % (W + 120)) - 60
            D.nuvem(tela, x, 70 + k * 12, 50 + k * 8, CEU2 if t > 11 else CEUD0, CEU3 if t > 11 else CEUD1)
        mar_onda = 1.0 + (1.6 if 21.2 <= t < 27.4 else 0)
        D.mar(tela, 0, 294, 150, PALCO_H, t, vel=1.4, onda=mar_onda, scroll=t * 40)
        esc = 1.0 - .55 * ease(fase(t, 27.8, 31.0))
        L = int(270 * esc)
        arf = .5 * math.sin(t * 1.1) * (2.5 if 21.2 <= t < 27.4 else 1)
        yw = 150 + int(math.sin(t * 1.3) * (2 if 21.2 <= t < 27.4 else 1))
        if t >= 27.8:
            # o gigante aparece atrás (silhueta)
            u = ease(fase(t, 28.4, 32))
            gx = int(lerp(300, 10, u))
            poligono(tela, [(gx, 140), (gx + 280, 140), (gx + 290, 132), (gx + 286, 156), (gx + 6, 156)], CAS0)
            for k in range(0, 260, 5): tela.ret(gx + 10 + k, 140 - 4 - (k * 7) % 9 - 18, 4, 20 + (k * 7) % 9, CEU2)
        pos = D.navio_lado(tela, 14, yw, L, t, D=max(14, int(26 * esc)), nosso=(9, 2), cores_seed=5, arfagem=arf,
                           escala=max(.6, esc))
        if pos and t < 27.6:
            mira(tela, pos[0], pos[1], t, 6, 5)
            if t < 7.0: self.rot(tela, 'O NOSSO', pos[0] - 20, pos[1] - 26, AMARELO, alvo=(pos[0], pos[1] - 4))
        if 21.2 <= t < 27.4:
            lx = self.lupa_x(190, 100)
            ix, iy, iw, ih = lupa(tela, lx, 4, 100, 70, 'DE FRENTE', AMARELO)
            ang = .18 * math.sin(t * 1.9)
            cx, cy = ix + iw // 2, iy + 42
            c, s = math.cos(ang), math.sin(ang)
            quad(tela, cx, cy, 70, 14, ang, CAS1)
            for k in range(3):
                for r in range(4):
                    dx, dy = -18 + r * 12, -12 - k * 9
                    pal = P_LAR if (r, k) == (2, 1) else OUTRAS[(r + k) % 5]
                    quad(tela, cx + dx * c - dy * s, cy + dx * s + dy * c, 11, 8, ang, pal[2])
            for r in range(4):
                for sgn in (-1, 1):
                    dx0, dy0 = -18 + r * 12 + sgn * 5, -7
                    dx1, dy1 = -18 + r * 12 - sgn * 5, -16
                    tela.linha(cx + dx0 * c - dy0 * s, cy + dx0 * s + dy0 * c, cx + dx1 * c - dy1 * s, cy + dx1 * s + dy1 * c, ACO4)
        kn = 18 + int(round(2 * math.sin(t * .4)))
        kmh = int(round(kn * 1.852))
        hora = 'DIA' if t < 11 else ('TARDE' if t < 14 else ('NOITE' if t < 29 else 'AMANHECER'))
        self.painel(tela, t, mov=3, linhas=None, estado=('VELOCIDADE', f"{kn} NÓS = {kmh} KM/H", AMARELO))
        if not VERTICAL:
            # régua 16..25 nós com o ponteiro
            y = 150
            tela.texto('16', PX0, y - 1, ACO3, tam=9); tela.texto('25 NÓS', PX0 + 120, y - 1, ACO3, tam=9)
            tela.ret(PX0 + 16, y + 2, 100, 3, TRACO); tela.ret(PX0 + 16, y + 2, int(100 * (kn - 16) / 9), 3, AMARELO)
            tela.texto(hora, PX0 + 178 - 8, 186, CIANO, tam=9, centro='d')

    def sons(self, fx):
        mar_som(fx, self.t0, self.dur, .07)
        fx.put(zumbido(self.dur - .5, 36), self.t0 + .2, .08)
        fx.put(buzina(1.8), self.t0 + .6, .16)


# ================================================================ os gigantes
class Gigantes(Cena):
    K = 6
    VX = 150
    PXM = 272 / 400.0

    def desenhar(self, tela, t, tg):
        D.ceu(tela, 150, t, cores=CEU_TARDE, estrelas=False)
        D.mar(tela, 0, 294, 150, PALCO_H, t, scroll=t * 6)
        u = ease(fase(t, .3, 3.0))
        x0 = int(lerp(300, 10, u))
        alt = [10 + (k * 7) % 2 for k in range(60)]
        pos = D.navio_lado(tela, x0, 150, 272, t, D=22, alturas=alt, cores_seed=8, ponte_u=.72, escala=.68)
        teu = int(24000 * suave(fase(t, 1.0, 6.0)))
        cx = self.VX if VERTICAL else 150
        tela.texto(f"{I.milhar(teu)} TEU", cx, 8, AMARELO, tam=17, centro=True, contorno=PRETO)
        if 7.2 <= t < 14.2:
            yb = 172
            v = ease(fase(t, 7.4, 9.4))
            tela.ret(x0, yb, int(272 * v), 1, AMARELO)
            for m in range(0, 401, 50):
                if m * self.PXM <= 272 * v:
                    tela.ret(x0 + int(m * self.PXM), yb - 2, 1, 5, AMARELO)
            if v >= 1:
                rotulo(tela, '400 M', x0 + 136, yb + 6, AMARELO, centro=True)
                rotulo(tela, '0', x0, yb + 6, ACO3, centro=True)
            if t > 10.0:
                lx = self.lupa_x(196, 92)
                ix, iy, iw, ih = lupa(tela, lx, 30, 92, 60, 'DE FRENTE', AMARELO)
                wpx = int(61 * self.PXM)
                bx = ix + (iw - wpx) // 2
                tela.ret(bx, iy + 30, wpx, 10, CAS1)
                for k in range(25):
                    tela.ret(bx + int(k * wpx / 25), iy + 18, max(1, int(wpx / 25) - 0), 12, OUTRAS[k % 5][2])
                tela.ret(bx, iy + 42, wpx, 1, CIANO)
                tela.texto('61 M', ix + iw // 2, iy + 34 + 10, CIANO, tam=9, centro=True, contorno=PRETO)
        if 14.2 <= t < 21.2:
            n = min(66, int((t - 14.4) / .07) + 1)
            yb = 176
            for k in range(n):
                xk = x0 + k * 4
                pal = P_LAR if k == 0 else OUTRAS[k % 6]
                tela.ret(xk, yb, 4, 3, PRETO); tela.ret(xk, yb, 3, 2, pal[2])
            tela.texto(f"{n} CONTÊINERES DE 20 PÉS", x0 + 136, yb + 8, BRANCO, tam=9, centro=True, contorno=PRETO)
        if t >= 21.2:
            # pilha de 11, de frente, grande
            sx = (self.VX + 50) if VERTICAL else 236
            ntop = min(11, int((t - 21.4) / .3) + 1)
            for k in range(ntop):
                D.cont_frente(tela, sx, 140 - (k + 1) * 11, 14, 10, P_LAR if k == 0 else OUTRAS[k % 6])
                tela.texto(str(k + 1), sx - 6, 140 - (k + 1) * 11 + 1, ACO4 if k < 9 else AMARELO, tam=9, centro=True)
            tela.ret(sx - 4, 140, 22, 2, ACO2)
        self.painel(tela, t, selo='OS GIGANTES', cab=('OS', 'GIGANTES', AMARELO),
                    linhas=[('CAPACIDADE', '24.000 TEU', AMARELO), ('TAMANHO', '400 M × 61 M', BRANCO)],
                    estado=('NO CONVÉS', '10 OU 11 DE ALTURA', CIANO) if t >= 21.2 else None)

    def sons(self, fx):
        mar_som(fx, self.t0, self.dur, .05)
        fx.put(buzina(2.4, 69.3), self.t0 + .8, .2)
        for k in range(0, 66, 3): fx.put(tique(1400 + k * 10), self.t0 + 14.4 + k * .07, .05)
        for k in range(11): fx.put(baque(120 + k * 6), self.t0 + 21.4 + k * .3, .1)


# ================================================================ 8 chegada
class Chegada(Cena):
    K = 7
    VX = 150

    def preparar(self):
        self.C = navio_corte(9, deck=[(r, 4) for r in range(10)] + [(r, 5) for r in (0, 1, 2, 3, 5, 6, 7, 8, 9)])
        xs, ys = self.C.xy(*SLOT_NOSSO)
        self.xs, self.ys = xs + 5.0, ys - 5.0
        self.tl, self.tu = 9.0, 12.75
        self.X = [(0, 200.0), (7.0, self.xs), (self.tl + .3, self.xs), (11.2, XLANE), (13, XLANE)]
        self.Y = [(0, 60.0), (7.0, 60.0), (8.6, self.ys), (self.tl + .2, self.ys), (10.2, 60.0), (11.2, 60.0),
                  (12.4, 127.0), (13, 127.0)]
        L = PAT['lane']
        rx = PAT['rows'][1] + 10
        yp = y_pilha(3) - 8
        self.pa = [(14.0, 15.75), (17.0, 18.75)]
        self.PX = [(13.2, L), (14.3, L), (15.0, rx), (17.3, rx), (18.0, L), (19.4, L)]
        self.PY = [(13.2, 70.0), (13.7, 149.0), (14.2, 149.0), (14.6, 48.0), (15.0, 48.0), (15.5, yp), (16.0, yp),
                   (16.4, 48.0), (16.8, yp), (17.2, yp), (17.6, 48.0), (18.0, 48.0), (18.6, 149.0), (19.4, 120.0)]

    def desenhar(self, tela, t, tg):
        if t < 13.2: self.cais(tela, t)
        elif t < 19.6: self.patio(tela, t)
        elif t < 26.2: self.portao(tela, t)
        else: self.armazem(tela, t)
        mov = 3 + (t >= self.tu) + (t >= 15.75) + (t >= 18.75)
        if t < 6.8: est = ('POSIÇÃO', 'NO NAVIO', BRANCO)
        elif t < 13.2: est = ('POSIÇÃO', 'NO SPREADER' if self.tl <= t < self.tu else ('NO CAMINHÃO' if t >= self.tu else 'SOLTANDO AMARRAS'), AMARELO)
        elif t < 19.6: est = ('POSIÇÃO', 'NO PÁTIO', BRANCO)
        elif t < 26.2: est = ('PORTÃO', 'SAÍDA', CIANO)
        else: est = ('CARGA', 'ENTREGUE' if t >= 31.2 else 'DESCARREGANDO', VERDE)
        self.painel(tela, t, mov=mov, estado=est)

    def cais(self, tela, t):
        C = self.C
        car = self.tl <= t < self.tu
        if t < self.tl: C.slots[SLOT_NOSSO] = P_LAR
        else: C.slots.pop(SLOT_NOSSO, None)
        st = (kf(t, self.X), kf(t, self.Y), trava_de(t, [(self.tl, self.tu)]), car)
        cena_cais(tela, t, C, st, CEU_AURORA, caminhao=(P_LAR if t >= self.tu else False), amarras=t < 7.4)
        if t < 6.6 and not VERTICAL:
            tela.texto('PORTO DE DESTINO', 150, 70, CHAMA1, tam=17, centro=True, contorno=PRETO)
        if t < self.tl:
            x, y = C.xy(*SLOT_NOSSO); mira(tela, x + 5, y + 5, t, 8)
        elif car:
            mira(tela, kf(t, self.X), kf(t, self.Y) + 10, t, 8)
        else:
            mira(tela, XLANE, YQ - 12, t, 8)

    def patio(self, tela, t):
        car = carregando(t, self.pa)
        na_pilha = self.pa[0][1] <= t < self.pa[1][0]
        cam = P_LAR if t < self.pa[0][0] else (False if t < self.pa[1][1] else P_LAR)
        st = (kf(t, self.PX), kf(t, self.PY), trava_de(t, self.pa), car)
        cena_patio(tela, t, st, CEU_AURORA, caminhao=cam, nosso_na_pilha=na_pilha)
        if 16.0 <= t < 17.0 and not VERTICAL:
            tela.texto('ALGUNS DIAS DEPOIS...', 150, 70, CHAMA1, tam=9, centro=True, contorno=PRETO)

    def portao(self, tela, t):
        u = t - 19.6
        xcam = 20 + 30 * u if u < 2.4 else (92 if u < 4.4 else 92 + 22 * (u - 4.4) ** 2)
        varre = 100 + 70 * ((u - .6) / 1.8 % 1.0) if .6 <= u < 4.0 else None
        r = cena_portao(tela, t, xcam, xcam / 10, ceu=CEU_DIA, varre=varre, cancela=fase(u, 4.0, 4.6))
        if VERTICAL: return
        for j, (nm, ta) in enumerate((('CÓDIGO', 1.6), ('LACRE', 2.8))):
            y = 8 + j * 16
            tela.texto(nm, 160, y, BRANCO, tam=9, contorno=PRETO)
            if u >= ta:
                check(tela, 210, y, VERDE)

    def armazem(self, tela, t):
        u = t - 26.2
        n = 10 - max(0, min(10, int((u - 2.2) / .45))) if u >= 2.2 else 10
        portas = fase(u, 1.2, 2.0)
        emp = None
        if 2.2 <= u < 7.0:
            ph = ((u - 2.2) / .45) % 1.0
            emp = (30 + 50 * (1 - abs(1 - 2 * ph)), ph < .5)
        r = cena_fabrica(tela, t, n, portas=portas, raiox=True, ceu=CEU_DIA, armazem=True, empilhadeira=emp)
        cx, cy, cw, ch = r
        if u < 2.2:
            lx = self.lupa_x(150, 130)
            ix, iy, iw, ih = lupa(tela, lx, 6, 130, 60, 'O LACRE', AMARELO, alvo=(cx + 2, cy + 12))
            lacre(tela, ix + 30, iy + 6, 1.0, rompido=u > 1.0)
            tela.texto('INTEIRO', ix + 60, iy + 10, VERDE, tam=9, contorno=PRETO)
            check(tela, ix + 62, iy + 22, VERDE)
            if u > 1.0: tela.texto('(CORTADO AGORA,', ix + 50, iy + 34, ACO3, tam=9) or tela.texto('NA ENTREGA)', ix + 56, iy + 42, ACO3, tam=9)
        if u >= 5.0:
            mira(tela, cx + cw // 2, cy + ch // 2, t, 34, 16)
            self.rot(tela, 'VAZIO, PRONTO PARA OUTRA', cx - 10, cy - 24, AMARELO)

    def sons(self, fx):
        fx.put(buzina(1.6), self.t0 + .4, .14)
        for k in range(6): fx.put(tique(1200), self.t0 + 6.8 + k * .1, .1)
        fx.put(clac(), self.t0 + self.tl, .42); fx.put(clac(), self.t0 + self.tu, .32)
        fx.put(zumbido(1.0, 46), self.t0 + 10.2, .1)
        for a, b in self.pa:
            fx.put(clac(), self.t0 + a, .35); fx.put(clac(), self.t0 + b, .28)
        fx.put(zumbido(4.4, 40), self.t0 + 19.6, .1)
        fx.put(fx.blip(84, .08), self.t0 + 21.2, .14); fx.put(fx.blip(86, .08), self.t0 + 22.4, .14)
        fx.put(tique(3000), self.t0 + 27.2, .25)
        for k in range(10): fx.put(baque(110), self.t0 + 28.4 + k * .45, .1)


# ================================================================ Santos
class Santos(Cena):
    K = -1
    VX = 150
    GW, GH = 90, 60                       # grade de 5.400 pontinhos (cada um = 1.000 TEU)

    def preparar(self):
        rng = np.random.default_rng(23)
        self.cores = rng.integers(0, 5, size=(self.GH, self.GW))
        self.ordem = rng.permutation(self.GW * self.GH)

    def desenhar(self, tela, t, tg):
        grade(tela)
        cx = self.VX if VERTICAL else 146
        if t < 14.2:
            n = int(5400 * suave(fase(t, .8, 12.0)))
            x0, y0 = cx - self.GW * 3 // 2, 40
            tela.ret(x0 - 2, y0 - 2, self.GW * 3 + 4, self.GH * 2 + 4, PRETO)
            m = np.zeros(self.GW * self.GH, bool); m[self.ordem[:n]] = True
            m = m.reshape(self.GH, self.GW)
            pal = np.array([OUTRAS[k][2] for k in range(5)], np.uint8)
            blk = tela.buf[y0:y0 + self.GH * 2, x0:x0 + self.GW * 3]
            cores = pal[self.cores]
            big = np.repeat(np.repeat(np.where(m, cores, FUNDO2), 2, 0), 3, 1)
            big[1::2, :] = np.where(np.repeat(np.repeat(m, 2, 0), 3, 1)[1::2, :], LAR0, FUNDO2)
            blk[:] = big
            tela.texto(f"{I.milhar(n * 1000)} TEU", cx, 10, AMARELO, tam=17, centro=True, contorno=PRETO)
            tela.texto('CADA PONTINHO = 1.000 TEU', cx, y0 + self.GH * 2 + 8, ACO3, tam=9, centro=True, contorno=PRETO)
            tela.texto('PORTO DE SANTOS, 2024', cx, y0 + self.GH * 2 + 20, BRANCO, tam=9, centro=True, contorno=PRETO)
        elif t < 20.8:
            u = t - 14.2
            km = int(32713 * suave(fase(u, .4, 5.4)))
            tela.texto(f"{I.milhar(km)} KM", cx, 20, AMARELO, tam=26, centro=True, contorno=PRETO)
            tela.texto('DE CONTÊINERES EM FILA', cx, 52, BRANCO, tam=9, centro=True, contorno=PRETO)
            # a fila correndo em 3 faixas
            for j in range(3):
                y = 80 + j * 30
                off = (u * (90 + j * 40)) % 12
                for k in range(-1, 26):
                    x = int(k * 12 - off) + (j * 5)
                    if 0 <= x < 290:
                        D.cont_lado(tela, x, y, 11, 6, OUTRAS[(k + j * 3 + int(u * (90 + j * 40) / 12)) % 6], castanhas=False)
                tela.ret(0, y + 8, 292, 1, ACO1)
            D.caminhao(tela, cx - 60, 196, t, u * 30, cw=40, ch=17)
        else:
            u = t - 20.8
            # relógio de 24 h girando e a pilha do dia
            ccx, ccy = (cx - 50 if not VERTICAL else cx), 110
            tela.disco(ccx, ccy, 36, PRETO); tela.disco(ccx, ccy, 34, FUNDO3); tela.anel(ccx, ccy, 34, ACO3)
            for k in range(24):
                a = k / 24 * 2 * math.pi
                tela.px(ccx + 30 * math.sin(a), ccy - 30 * math.cos(a), ACO4 if k % 6 else BRANCO)
            a = (u / 5.0) * 2 * math.pi
            tela.linha(ccx, ccy, ccx + 26 * math.sin(a), ccy - 26 * math.cos(a), AMARELO)
            tela.disco(ccx, ccy, 2, AMARELO)
            tela.texto('24 HORAS', ccx, ccy + 42, ACO3, tam=9, centro=True, contorno=PRETO)
            n = int(14754 * min(1.0, u / 5.0))
            tela.texto(f"{I.milhar(n)} TEU", cx, 18, AMARELO, tam=17, centro=True, contorno=PRETO)
            tela.texto('EM UM DIA, EM MÉDIA', cx, 40, BRANCO, tam=9, centro=True, contorno=PRETO)
            if not VERTICAL:
                k = int(n / 14754 * 48)
                for j in range(k):
                    D.cont_frente(tela, 200 + (j % 8) * 11, 176 - (j // 8) * 11, 10, 10, OUTRAS[j % 6])
        self.painel(tela, t, selo='E NO BRASIL?', cab=('E NO', 'BRASIL?', VERDE),
                    linhas=[('PORTO DE SANTOS (SP)', '5,4 MI TEU', AMARELO), ('EM 2024', '+14,7%', VERDE)],
                    estado=('NA AMÉRICA LATINA', '1º EM CONTÊINER', CIANO))

    def sons(self, fx):
        for k in range(40): fx.put(tique(1800 + (k % 6) * 120), self.t0 + .8 + k * .28, .04)
        fx.put(zumbido(6.0, 44), self.t0 + 14.4, .06)
        for k in range(10): fx.put(fx.blip(76 + k % 3, .05), self.t0 + 21.0 + k * .5, .06)


# ================================================================ resumo
ICX = [33 + i * 59 for i in range(8)]


class Resumo(Cena):
    LIGA = [0.6, 1.8, 3.0, 4.4, 6.9, 8.2, 9.6, 11.0]
    MOVS = [(2, 13.4), (2, 14.0), (3, 14.8), (7, 15.6), (7, 16.2), (7, 16.8)]

    def desenhar(self, tela, t, tg):
        grade(tela)
        tela.texto('A JORNADA DO CONTÊINER EM 8 ETAPAS', W // 2, 12, ACO3, tam=17, centro=True, contorno=PRETO)
        for i in range(8):
            aceso = t >= self.LIGA[i]
            D.icone(tela, i, ICX[i], 70, t, aceso=aceso)
            tela.texto(str(i + 1), ICX[i], 94, ETAPAS[i][1] if aceso else ACO1, tam=9, centro=True, contorno=PRETO)
            if aceso:
                nm = ['FÁBRICA', 'PORTÃO', 'PÁTIO', 'GUINDASTE', 'PLANO', 'AMARRA', 'VIAGEM', 'CHEGADA'][i]
                tela.texto(nm, ICX[i], 106, BRANCO, tam=9, centro=True, contorno=PRETO)
            if i < 7:
                xa, xb = ICX[i] + 22, ICX[i + 1] - 22
                tela.ret(xa, 70, xb - xa, 1, ETAPAS[i][1] if t >= self.LIGA[i + 1] else ACO0)
        # o nosso andando de ícone em ícone
        k = sum(1 for a in self.LIGA if t >= a) - 1
        if k >= 0:
            x = ICX[k] - 8
            D.cont_lado(tela, x, 40 + int(math.sin(t * 4) * 1.5), 16, 7, P_LAR, castanhas=False)
        # contador de movimentos
        if t >= 13.2:
            n = sum(1 for _, a in self.MOVS if t >= a)
            tela.texto('MOVIMENTOS DE GUINDASTE', W // 2, 124, ACO3, tam=9, centro=True, contorno=PRETO)
            for j in range(6):
                on = j < n
                ix = ICX[self.MOVS[j][0]]
                D.cont_frente(tela, W // 2 - 66 + j * 22, 138, 18, 16, P_LAR if on else P_CI)
                if on: tela.texto(str(j + 1), W // 2 - 57 + j * 22, 158, AMARELO, tam=9, centro=True, contorno=PRETO)
        if t >= 20.2:
            tela.texto(CODIGO, W // 2, 178, LAR3, tam=17, centro=True, contorno=PRETO)
            if t >= 21.0: tela.texto('11 CARACTERES', W // 2, 196, ACO3, tam=9, centro=True, contorno=PRETO)

    def sons(self, fx):
        for i, a in enumerate(self.LIGA):
            fx.put(fx.blip(72 + (0, 2, 4, 5, 7, 9, 11, 12)[i], .1), self.t0 + a, .14)
        for _, a in self.MOVS: fx.put(clac(), self.t0 + a, .3)
        fx.put(fx.sino(84, 1.2), self.t0 + 20.2, .2)


# ================================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS A JORNADA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            D.ceu(tela, PALCO_H, t, cores=CEU_NOITE)
            D.mar(tela, 0, W, 170, PALCO_H, t, scroll=t * 10)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            D.navio_lado(tela, int(60 + t * 6), 170, 240, t, D=22, nosso=(8, 2), cores_seed=3)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, caixa=Caixa, codigo=Codigo, fabrica=Fabrica, portao=Portao,
             patio=Patio, guindaste=Guindaste, ritmo=Ritmo, plano=Plano, amarracao=Amarracao, viagem=Viagem,
             gigantes=Gigantes, chegada=Chegada, santos=Santos, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep19_motor as EP
    D.checar_codigo()
    if sys.argv[1] in ('--folha', '--quadros'):
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        ts = []
        if sys.argv[1] == '--folha':
            so = sys.argv[3:] or None
            fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
            for c in trilha.caps:
                if so and c['id'] not in so: continue
                ts += [c['t0'] + c['dur'] * f for f in fr]
        else:
            for a in sys.argv[3:]:
                cid, tt = a.split(':')
                c = next(x for x in trilha.caps if x['id'] == cid)
                ts.append(c['t0'] + float(tt))
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else len(ims)
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
