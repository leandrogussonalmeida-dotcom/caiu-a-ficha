#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep06 — Por que um navio de aço flutua (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (respingo, água escorrendo, contêiner), nos
                          mesmos instantes do desenho
A física manda no desenho: o quanto um objeto afunda sai da conta de Arquimedes
(volume submerso x densidade da água = peso), e o painel lê os mesmos números.

    python3 ep06_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep06_motor.py <saida.mp4> cubo tigela      # só esses capítulos (teste)
    python3 ep06_motor.py --folha <saida.png>          # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ep06_desenho as D
from ep06_desenho import (rotulo, fio, seta, forca, bolha, kg, PX_CM, PX_M, Tanque, Navio, calado_px,
                          agua_fundo, agua_por_cima, ceu, jarra, balanca, medidor_densidade, barra_forca)
import ritmo_marca as RM
import idioma as I
from ep06_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2606, 41
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais

PORTE = 156907                # t de porte bruto (F6)
KG_PX = 40.0                  # setas de força: px por kg (tanque de 1 kg)


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def leitura_v(tela, txt, x, cor=BRANCO, y=1):
    """No Short o painel fica de fora: a leitura principal vai no alto do recorte."""
    if not VERTICAL: return
    w = tela.largura_texto(txt, 9) + 10
    painel(tela, x - w // 2, y, w, 13, borda=cor)
    tela.texto(txt, x, y + 3, cor, tam=9, centro=True)


def fundo_lab(tela):
    """Parede de laboratório: azulejo escuro (a mesa vem com o tanque)."""
    tela.buf[:PALCO_H] = FUNDO
    for x in range(0, W, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(8, PALCO_H, 12): tela.ret(0, y, W, 1, FUNDO2)
    tela.ret(298, 0, 1, PALCO_H, FUNDO3)


def titulo_painel(tela, l1, l2=None, c1=ACO3, c2=AMARELO):
    tela.texto(l1, PX0, 8, c1, tam=17, contorno=PRETO)
    if l2: tela.texto(l2, PX0, 26, c2, tam=17, contorno=PRETO)


def ondas_som(fx, t0, t1, g=.035):
    """Mar de fundo: chiado grave em ondas de ~4 s."""
    t = t0
    while t < t1 - .5:
        d = min(4.2, t1 - t)
        fx.put(fx.chiado(d, 120, 700), t, g, math.sin(t) * .4)
        t += 3.3


def respingo(fx, t, g=.4):
    fx.put(fx.chiado(.35, 900, 5000, .01), t, g)
    fx.put(fx.explosao(.4), t, g * .3)


def gotinhas(tela, x, y0, y1, t, cor=AGUA1, n=6, vel=3.0):
    for k in range(n):
        u = (t * vel + k / n) % 1.0
        y = y0 + u * (y1 - y0)
        tela.ret(int(x + (k % 2)), int(y), 1, 2, cor)
        tela.px(x + (k % 2), y, MISTURA2)


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


NAVIO = Navio(256)
NAVIO_V = Navio(170)          # o navio mais curto dos cortes verticais


def navio(): return NAVIO_V if VERTICAL else NAVIO
def x_navio(): return 75 if VERTICAL else 24


# ============================================================ gancho
class Gancho(Cena):
    YW = 150

    def bolt(self, t):
        """(x, y, ângulo) do parafuso: cai, bate na água em 1,6 s e afunda devagar."""
        x = 210 if VERTICAL else 380
        if t < .6: return x, -40, 0.0
        if t < 1.6:
            u = (t - .6) / 1.0
            return x, -40 + u * u * (self.YW + 44), u * .6
        u = min(1.0, (t - 1.6) / 4.2)
        return x + math.sin(t * 2.5) * 4 * (1 - u), self.YW + 4 + ease(u) * 34, .6 + u * .9

    def desenhar(self, tela, t, tg):
        yw = self.YW
        ceu(tela, t)
        agua_fundo(tela, 0, yw, W, PALCO_H)
        Nv = navio()
        frac = .55
        yq = yw + int(calado_px(frac)) + (1 if math.sin(t * 1.4) > .6 else 0)
        Nv.desenhar(tela, x_navio() - (40 if VERTICAL else 0), yq, t, n_cont=60)
        bx, by, ang = self.bolt(t)
        D.parafuso(tela, bx, by, ang)
        if 1.6 <= t < 6:
            for k in range(5):
                u = (t * .9 + k / 5) % 1.0
                if by - u * 30 > yw + 3: bolha(tela, bx + math.sin(u * 9 + k) * 3, by - u * 30, 1.2)
        agua_por_cima(tela, 0, yw, W, PALCO_H, t)
        if 1.6 <= t < 2.3:                                  # respingo
            u = (t - 1.6) / .7
            for k in range(8):
                a = math.pi * (k + .5) / 8
                tela.px(bx + math.cos(a) * u * 16, yw - math.sin(a) * 14 * u * (1.4 - u), MISTURA2)
        if t < 6.0:
            if t > 2.5:
                rotulo(tela, 'AÇO', bx + 14, by + 2, ACO4)
        else:
            u = ease((t - 6.0) / .6)
            xl = 120 if not VERTICAL else 150
            rotulo(tela, 'TAMBÉM AÇO', xl, 56, ACO4, centro=True)
            fio(tela, xl, 66, xl + 10, yq - 30, ACO4)
            if not VERTICAL:
                k = int(t * 3) % 2
                tela.texto('?', 400, 60 - k, AMARELO, tam=26, centro=True, contorno=PRETO)
                rotulo(tela, 'AFUNDA', 380, 96, VERMELHO, centro=True)
                rotulo(tela, 'FLUTUA', 380, 110, VERDE, centro=True)

    def sons(self, fx):
        ondas_som(fx, self.t0, self.t0 + self.dur)
        respingo(fx, self.t0 + 1.6, .5)
        for k in range(8):
            fx.put(fx.blip(84 + (k * 5) % 7, .04), self.t0 + 2.0 + k * .45, .05)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        yw = 182
        ceu(tela, t)
        agua_fundo(tela, 0, yw, W, PALCO_H)
        x0 = int(-260 + t * 45)
        NAVIO.desenhar(tela, x0, yw + 24, t, n_cont=70, fumaca=True)
        agua_por_cima(tela, 0, yw, W, PALCO_H, t)
        n = int(t / .045)
        for j, linha in enumerate(("POR QUE UM NAVIO", "DE AÇO FLUTUA?")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 16)]
            tela.texto(vis, W // 2 - larg // 2, 18 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("COMO VOA / FLUTUA", W // 2, 90, AMARELO, tam=17, centro=True, contorno=PRETO)

    def sons(self, fx):
        for k in range(3):
            fx.put(fx.blip(72 + k * 4, .1), self.t0 + 1.2 + k * .25, .2)


# ============================================================ densidade
class Densidade(Cena):
    ITENS = [(55, 'ÁGUA', 1.0, 7.8, 'agua'), (150, 'AÇO', 7.85, 14.8, 'aco'), (245, 'ÁGUA DO MAR', 1.025, 22.8, 'mar')]
    YP = 168
    LADO = 46                       # 10 cm a 4,6 px/cm

    def cubo1l(self, tela, cx, yb, tipo, t):
        l = self.LADO
        x0, y0 = cx - l // 2, yb - l
        if tipo == 'aco':
            D.cubo(tela, cx, yb, l, t)
            return
        c1, c2 = (AGUA1, AGUA0) if tipo == 'agua' else (MISTURA, FUNDO3)
        tela.ret(x0 - 1, y0 - 1, l + 2, l + 2, PRETO)
        dither(tela, x0, y0 + 3, l, l - 3, c1, c2)
        tela.ret(x0, y0, l, 3, FUNDO2)
        d = 1 if math.sin(t * 3) > .3 else 0
        tela.ret(x0, y0 + 3 - d, l, 1, MISTURA2)
        tela.ret(x0, y0, 1, l, MISTURA2); tela.ret(x0 + l - 1, y0, 1, l, ACO3)
        tela.ret(x0 + 4, y0 + 8, 1, l - 14, BRANCO)
        if tipo == 'mar':
            for k in range(6):
                tela.px(x0 + 8 + (k * 7) % (l - 12), y0 + 10 + (k * 11) % (l - 14), BRANCO)   # sal

    def desenhar(self, tela, t, tg):
        fundo_lab(tela)
        tela.ret(0, self.YP + 27, 300, PALCO_H - self.YP - 27, OLEO0)
        dither(tela, 0, self.YP + 29, 300, PALCO_H - self.YP - 29, OLEO0, FUNDO)
        tela.ret(0, self.YP + 27, 300, 1, LATAO)
        for cx, nome, val, ta, tipo in self.ITENS:
            if VERTICAL and cx == 245: continue
            cxv = cx + (10 if VERTICAL else 0)
            yb = self.YP
            leit = '0,00 KG'
            if t >= ta:
                u = (t - ta) / .7
                if u < 1:
                    yb = -10 + (self.YP + 10) * u * u
                pousou = u >= 1
                if pousou:
                    yb = self.YP + (1 if (t - ta) < .9 else 0)
                    v = val * ease((t - ta - .7) / .8)
                    leit = f"{I.decimal(v, 3 if tipo == 'mar' else 2)} KG"
                self.cubo1l(tela, cxv, yb, tipo, t)
            balanca(tela, cxv, self.YP, leit, VERDE if t >= ta + 1.5 else CIANO, w=78)
            cor = {'agua': AGUA1, 'aco': ACO4, 'mar': MISTURA2}[tipo]
            if t >= ta - 6.8 or t >= 0.8:
                rotulo(tela, nome, cxv, 98, cor, centro=True)
                rotulo(tela, '1 LITRO', cxv, 110, ACO2, centro=True)
        if VERTICAL:
            return
        titulo_painel(tela, 'DENSIDADE', 'KG POR LITRO')
        for j, (cx, nome, val, ta, tipo) in enumerate(self.ITENS):
            y = 56 + j * 34
            cor = {'agua': AGUA1, 'aco': ACO3, 'mar': MISTURA}[tipo]
            tela.texto(nome, PX0, y, BRANCO if t >= ta else ACO1, tam=9, contorno=PRETO)
            if t >= ta + .7:
                v = val * ease((t - ta - .7) / .8)
                tela.texto(I.decimal(v, 3 if tipo == 'mar' else 2), PX0 + 166, y, cor, tam=9, centro='d', contorno=PRETO)
                tela.ret(PX0, y + 11, 166, 8, PRETO)
                n = int(164 * v / 8.0)
                tela.ret(PX0 + 1, y + 12, n, 6, cor); tela.ret(PX0 + 1, y + 12, n, 1, BRANCO)
        if t >= 14.8 + 1.5:
            tela.texto('AÇO = QUASE 8 X A ÁGUA', PX0, 160, ACO4, tam=9, contorno=PRETO)
        if t >= 29.8:
            painel(tela, PX0, 176, 166, 22, borda=AMARELO)
            tela.texto('KG POR LITRO = G/CM³', PX0 + 83, 183, AMARELO, tam=9, centro=True)

    def sons(self, fx):
        for cx, nome, val, ta, tipo in self.ITENS:
            fx.put(fx.clique(1200 if tipo != 'aco' else 700, .05), self.t0 + ta + .7, .5)
            if tipo == 'aco': fx.put(fx.explosao(.5), self.t0 + ta + .7, .25)
            fx.put(fx.blip(84, .08), self.t0 + ta + 1.5, .12)


# ============================================================ empuxo (boia no tanque cheio)
class Empuxo(Cena):
    LARG, ALT, PESO = 74, 64, 2.0
    BASE_CM2 = 16.0 * 16.0

    def preparar(self):
        self.TQ = Tanque(nivel=Tanque.TY0 + 3, bico=True)
        self.d_eq = self.PESO * 1000 / self.BASE_CM2          # 7,8 cm

    def d_cm(self, t):
        if t < 3.0: return 0.0
        if t < 15.5: return self.d_eq * suave((t - 3.0) / 12.5)
        return self.d_eq + .25 * math.sin((t - 15.5) * 2.4) * math.exp(-(t - 15.5) * .5)

    def desenhar(self, tela, t, tg):
        fundo_lab(tela)
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        nivel = TQ.nivel0
        TQ.fundo(tela, nivel)
        d = self.d_cm(t)
        vol = self.BASE_CM2 * min(d, self.d_eq)               # cm³ que transbordaram
        cx = (TQ.TX0 + TQ.TX1) // 2
        base = nivel + d * PX_CM if t >= 3.0 else nivel - 2
        gancho_y = base - self.ALT
        D.gancho_corda(tela, cx, gancho_y, t, folga=1.0 if t > 15.5 else 0.0)
        D.boia(tela, cx, base, self.LARG, self.ALT, t)
        TQ.frente(tela, nivel, t)
        # forças
        emp = vol / 1000.0
        forca(tela, cx + 16, base - self.ALT // 2, self.PESO * 14, False, VERMELHO)
        forca(tela, cx - 16, base - self.ALT // 2, emp * 14, True, VERDE)
        if True:
            rotulo(tela, 'PESO', cx + 24, base - self.ALT // 2 + 22, VERMELHO)
            if emp > .3: rotulo(tela, 'EMPUXO', cx - 24, base - self.ALT // 2 - 12, VERDE, centro='d')
        # jarra na balança, recebendo o que transborda
        jx, jy, jw, jh = 236, 110, 34, 56
        if not VERTICAL:
            escorrendo = 3.0 < t < 15.6
            if escorrendo:
                gotinhas(tela, TQ.TX1 + 17, TQ.TY0 + 3, jy + jh - jh * min(1, vol / 2500), t, AGUA1, 7)
            balanca(tela, jx + jw // 2, 168, kg(vol / 1000), VERDE if t > 15.8 else CIANO, w=60)
            jarra(tela, jx, jy, jw, jh, vol / 2500.0, None, marcas=[(.4, ''), (.8, '')], t=t)
        leitura_v(tela, f"BOIA 2 KG   ÁGUA QUE SAIU {kg(vol / 1000)}", 137, VERDE if t > 15.8 else BRANCO)
        if VERTICAL: return
        titulo_painel(tela, 'ARQUIMEDES')
        barra_forca(tela, PX0, 34, 164, self.PESO, 2.5, VERMELHO, 'PESO DA BOIA', kg(self.PESO))
        barra_forca(tela, PX0, 62, 164, emp, 2.5, VERDE, 'ÁGUA QUE SAIU', kg(emp))
        if t >= 15.8:
            tela.texto('= IGUAIS', PX0, 90, AMARELO, tam=17, contorno=PRETO)
        if t >= 23.8:
            painel(tela, PX0, 114, 166, 40, borda=VERDE)
            tela.texto('EMPUXO =', PX0 + 8, 120, VERDE, tam=9)
            tela.texto('PESO DA ÁGUA', PX0 + 8, 131, BRANCO, tam=9)
            tela.texto('EMPURRADA', PX0 + 8, 142, BRANCO, tam=9)
            seta(tela, PX0 + 150, 122, 0, -1, VERDE, 6)
            tela.ret(PX0 + 149, 122, 3, 22, VERDE)
        if t >= 29.8:
            tela.texto('ARQUIMEDES DE SIRACUSA', PX0, 166, ACO4, tam=9, contorno=PRETO)
            tela.texto('287-212 A.C.', PX0, 178, AMARELO, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(12.0, 600, 3500), self.t0 + 3.4, .12, .4)
        fx.put(fx.sino(79), self.t0 + 15.8, .22)
        fx.put(fx.sino(84), self.t0 + 23.8, .15)


# ============================================================ cubo de 1 kg afunda
class Cubo(Cena):
    LADO_CM = 5.03
    T_SOLTA = 8.6

    def preparar(self):
        self.TQ = Tanque(nivel=104)
        self.lado = self.LADO_CM * PX_CM
        self.vol = 1000 / D.RHO_ACO                         # 127 cm³

    def base(self, t):
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        y_ar = TQ.nivel0 - 8
        fundo = TQ.TY1 - 1
        if t < self.T_SOLTA: return y_ar, False
        u = t - self.T_SOLTA
        y = y_ar + 90 * u * u                                   # caindo no ar
        if y < TQ.nivel0 + self.lado:
            return y, False
        # na água: velocidade quase constante (água freia)
        u_ag = math.sqrt((TQ.nivel0 + self.lado - y_ar) / 90)
        y = TQ.nivel0 + self.lado + (u - u_ag) * 22
        return min(fundo, y), y >= fundo

    def desenhar(self, tela, t, tg):
        fundo_lab(tela)
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        cx = (TQ.TX0 + TQ.TX1) // 2
        yb, chao = self.base(t)
        sub = max(0.0, min(1.0, (yb - TQ.nivel0) / self.lado))
        nivel = TQ.nivel0 - .8 * sub
        TQ.fundo(tela, nivel)
        if t < self.T_SOLTA:
            D.gancho_corda(tela, cx, yb - self.lado, t)
        D.cubo(tela, cx, yb, self.lado, t)
        if sub > 0 and not chao:
            for k in range(6):
                u = (t * 1.1 + k / 6) % 1.0
                by = yb - self.lado - 4 - u * 30
                if by > nivel + 3: bolha(tela, cx - 6 + (k * 5) % 14, by, 1.2)
        TQ.frente(tela, nivel, t)
        emp = self.vol * sub / 1000
        mid = min(yb - self.lado / 2, TQ.TY1 - 8 - KG_PX)
        forca(tela, cx + 22, mid, 1.0 * KG_PX, False, VERMELHO)
        if emp > .01: forca(tela, cx - 22, yb - 2, max(3, emp * KG_PX), True, VERDE)
        rotulo(tela, 'PESO 1 KG', cx + 28, mid + 18, VERMELHO)
        if emp > .01: rotulo(tela, 'EMPUXO', cx - 30, yb - 14, VERDE, centro='d')
        if t < 8.0:
            rotulo(tela, '5 CM', cx - self.lado / 2 - 6, yb - self.lado / 2 - 3, BRANCO, centro='d')
            tela.ret(int(cx - self.lado / 2), int(yb + 3), int(self.lado), 1, BRANCO)
            rotulo(tela, '1 KG DE AÇO', cx, yb + 6, ACO4, centro=True) if yb + 14 < TQ.nivel0 else None
        if chao and t > 15.8:
            rotulo(tela, 'AFUNDOU', cx, TQ.TY0 + 8, VERMELHO, 17, centro=True)
        leitura_v(tela, f"PESO 1,00 KG  EMPUXO {kg(emp)}", 137, VERMELHO if chao else BRANCO)
        if VERTICAL: return
        titulo_painel(tela, 'CUBO MACIÇO', '1 KG DE AÇO')
        barra_forca(tela, PX0, 50, 164, 1.0, 1.2, VERMELHO, 'PESO', kg(1.0))
        barra_forca(tela, PX0, 78, 164, emp, 1.2, VERDE, 'EMPUXO', kg(emp))
        jarra(tela, PX0 + 4, 112, 30, 60, self.vol * sub / 1000.0, None, marcas=[(1.0, '1 L'), (.5, '')], t=t)
        tela.texto('ÁGUA', PX0 + 56, 120, ACO3, tam=9, contorno=PRETO)
        tela.texto('EMPURRADA', PX0 + 56, 131, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{int(round(self.vol * sub))} ML", PX0 + 56, 144, CIANO, tam=17, contorno=PRETO)
        if t >= 15.8:
            tela.texto('AFUNDA', PX0 + 56, 172, VERMELHO, tam=17, contorno=PRETO)

    def sons(self, fx):
        # instante em que toca a água e o fundo
        ts = np.arange(self.T_SOLTA, self.dur, .005)
        ys = [self.base(t)[0] for t in ts]
        ag = next((t for t, y in zip(ts, ys) if y >= self.TQ.nivel0), None)
        ch = next((t for t, y in zip(ts, ys) if self.base(t)[1]), None)
        fx.put(fx.clique(2500, .03), self.t0 + self.T_SOLTA, .3)
        if ag: respingo(fx, self.t0 + ag, .35)
        if ch:
            fx.put(fx.explosao(.6), self.t0 + ch, .35)
            fx.put(fx.clique(600, .06), self.t0 + ch, .4)


# ============================================================ o mesmo aço em caixa flutua
class Tigela(Cena):
    LARG_CM, ALT_CM = 15.0, 8.0

    def preparar(self):
        self.TQ = Tanque(nivel=124)
        self.larg = self.LARG_CM * PX_CM            # 69 px
        self.alt = self.ALT_CM * PX_CM              # 37 px
        self.lado = 5.03 * PX_CM
        self.d_eq = 1000 / (self.LARG_CM * self.LARG_CM)     # 4,44 cm
        self.batidas = [1.6, 3.2, 4.8, 6.2]

    def d_cm(self, t):
        if t < 15.0: return -1.0
        if t < 27.0: return self.d_eq * suave((t - 15.0) / 12.0)
        return self.d_eq + .35 * math.sin((t - 27.0) * 2.2) * math.exp(-(t - 27.0) * .45)

    def forma(self, tela, t, cx, yb):
        """0..7,8 s: cubo -> chapa; 7,8..14,6: dobra as bordas."""
        if t < 7.8:
            k = sum(1 for b in self.batidas if t >= b)
            fr = [0, .3, .6, .85, 1.0][k]
            if k < 4 and k > 0:
                fr_ant = [0, .3, .6, .85, 1.0][k - 1]
                fr = fr_ant + (fr - fr_ant) * ease((t - self.batidas[k - 1]) / .15)
            w = self.lado + (self.larg + 2 * self.alt - self.lado) * fr
            h = max(2.0, self.lado * self.lado / w * (1 - fr) + 2 * fr)
            x0 = cx - w / 2
            tela.ret(int(x0) - 1, int(yb - h) - 1, int(w) + 2, int(h) + 2, PRETO)
            dither(tela, x0, yb - h, w, h, ACO2, ACO3)
            tela.ret(int(x0), int(yb - h), int(w), 1, ACO4)
            # marteladas: faíscas
            for b in self.batidas:
                if b <= t < b + .25:
                    for j in range(8):
                        a = j * .8 + b
                        r = (t - b) * 60
                        tela.px(cx + math.cos(a) * r, yb - h - 2 - abs(math.sin(a)) * r * .6, AMARELO)
            return
        u = ease((t - 7.8) / 5.5)
        ang = u * math.pi / 2
        meio = self.larg / 2
        D.chapa(tela, cx, yb, self.larg, 2)
        for s in (-1, 1):
            xa = cx + s * meio
            xb = xa + s * self.alt * math.cos(ang)
            yb2 = yb - 1 - self.alt * math.sin(ang)
            linha_grossa(tela, xa, yb - 1, xb, yb2, 4, PRETO)
            linha_grossa(tela, xa, yb - 1, xb, yb2, 2, ACO3)

    def desenhar(self, tela, t, tg):
        fundo_lab(tela)
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        cx = (TQ.TX0 + TQ.TX1) // 2
        d = self.d_cm(t)
        disp = max(0.0, min(d, self.d_eq)) * self.LARG_CM * self.LARG_CM     # cm³ (no balanço, o valor de equilíbrio)
        nivel = TQ.nivel0 - disp / TQ.area_cm2() * PX_CM
        TQ.fundo(tela, nivel)
        y_ar = TQ.nivel0 - 10
        if d < 0:
            yb = y_ar
            D.gancho_corda(tela, cx, yb - (self.alt if t >= 13.6 else 10), t)
            if t < 13.6:
                self.forma(tela, t, cx, yb)
            else:
                D.caixa(tela, cx, yb, self.larg, self.alt, t)
        else:
            yb = nivel + d * PX_CM
            yb = max(yb, y_ar)
            D.gancho_corda(tela, cx, yb - self.alt, t, folga=1.0 if t > 27 else 0.0)
            D.caixa(tela, cx, yb, self.larg, self.alt, t)
        caixa_pronta = d >= 0 or t >= 13.6
        TQ.frente(tela, nivel, t, excluir=D.caixa_ar(cx, yb, self.larg, self.alt) if caixa_pronta else ())
        emp = disp / 1000.0
        mid = yb - self.alt / 2
        if t >= 14.8:
            forca(tela, cx + 10, mid, 1.0 * KG_PX, False, VERMELHO)
            if emp > .02: forca(tela, cx - 10, yb - 3, emp * KG_PX, True, VERDE)
            rotulo(tela, 'PESO', cx + 16, mid + 30, VERMELHO)
            if emp > .02: rotulo(tela, 'EMPUXO', cx - 16, yb - 3 - emp * KG_PX - 4, VERDE, centro='d')
        if t < 7.8:
            rotulo(tela, '1 KG DE AÇO', cx, 20, ACO4, centro=True)
        elif t < 14.8:
            rotulo(tela, '15 CM', cx, yb + 8, BRANCO, centro=True)
            if t > 12: rotulo(tela, '8 CM', cx - self.larg / 2 - 6, yb - self.alt / 2 - 3, BRANCO, centro='d')
        if t >= 21.8 and d > 0:
            yl = int(nivel)
            xr = int(cx + self.larg / 2 + 3)
            tela.ret(xr, yl, 1, int(yb - yl), AMARELO)
            tela.ret(xr - 1, yl, 3, 1, AMARELO); tela.ret(xr - 1, int(yb) - 1, 3, 1, AMARELO)
            rotulo(tela, f"{I.decimal(min(d, 8), 1)} CM", xr + 4, int((yl + yb) / 2) - 3, AMARELO)
        if t >= 29.8:
            rotulo(tela, 'FLUTUA', cx, TQ.TY0 + 8, VERDE, 17, centro=True)
        leitura_v(tela, f"PESO 1,00 KG  EMPUXO {kg(emp)}", 137, VERDE if t > 27 else BRANCO)
        if VERTICAL: return
        titulo_painel(tela, 'O MESMO AÇO', 'EM CAIXA')
        barra_forca(tela, PX0, 50, 164, 1.0, 1.2, VERMELHO, 'PESO', kg(1.0))
        barra_forca(tela, PX0, 78, 164, emp, 1.2, VERDE, 'EMPUXO', kg(emp))
        jarra(tela, PX0 + 4, 112, 30, 60, disp / 1000.0, None, marcas=[(1.0, '1 L'), (.5, '')], t=t)
        tela.texto('ÁGUA', PX0 + 56, 114, ACO3, tam=9, contorno=PRETO)
        tela.texto('EMPURRADA', PX0 + 56, 125, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{I.milhar(disp)} ML", PX0 + 56, 138, CIANO, tam=17, contorno=PRETO)
        if t >= 35.8:
            # lado a lado: cubo afunda, caixa flutua
            tela.ret(PX0 + 56, 162, 112, 1, ACO1)
            D.cubo(tela, PX0 + 70, 192, 12, t)
            rotulo(tela, 'AFUNDA', PX0 + 70, 196, VERMELHO, centro=True)
            D.caixa(tela, PX0 + 136, 184, 34, 18, t, ar=False)
            rotulo(tela, 'FLUTUA', PX0 + 136, 196, VERDE, centro=True)
        elif t >= 7.8:
            tela.texto('CHAPA DE 1,8 MM', PX0 + 56, 176, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for b in self.batidas:
            fx.put(fx.clique(900, .05), self.t0 + b, .5)
            fx.put(fx.explosao(.3), self.t0 + b, .15)
        fx.put(fx.clique(1400, .04), self.t0 + 13.4, .3)
        ts = np.arange(15.0, 30.0, .01)
        ag = next((t for t in ts if self.d_cm(t) > 0.05), None)
        if ag: respingo(fx, self.t0 + ag, .25)
        fx.put(fx.sino(81), self.t0 + 29.8, .22)


# ============================================================ densidade média
class Media(Cena):
    def preparar(self):
        self.TQ = Tanque(nivel=124)
        self.larg, self.alt = 15 * PX_CM, 8 * PX_CM
        self.d = 1000 / 225

    def desenhar(self, tela, t, tg):
        fundo_lab(tela)
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        nivel = TQ.nivel0 - (1000 + 127) / TQ.area_cm2() * PX_CM
        TQ.fundo(tela, nivel)
        cx_c, cx_b = (82, 160) if not VERTICAL else (98, 176)
        yb = nivel + self.d * PX_CM + (1 if math.sin(t * 1.5) > .5 else 0)
        D.cubo(tela, cx_c, TQ.TY1 - 1, 5.03 * PX_CM, t)
        brilho_ar = t < 7.8 or int(t * 3) % 2 == 0
        D.caixa(tela, cx_b, yb, self.larg, self.alt, t, cor_ar=MISTURA2 if brilho_ar else ACO2)
        TQ.frente(tela, nivel, t, excluir=D.caixa_ar(cx_b, yb, self.larg, self.alt))
        if t < 7.8:
            rotulo(tela, 'AR', cx_b, 36, MISTURA2, 17, centro=True)
            fio(tela, cx_b, 54, cx_b, int(yb - self.alt / 2), MISTURA2)
        if t >= 7.8:
            rotulo(tela, '0,56', cx_b, int(yb - self.alt) - 22, VERDE, 17, centro=True)
        if t >= 22.8:
            rotulo(tela, '7,85', cx_c, TQ.TY1 - 48, VERMELHO, 17, centro=True)
            fio(tela, cx_c, TQ.TY1 - 30, cx_c, TQ.TY1 - 25, VERMELHO)
        leitura_v(tela, "DENSIDADE: CAIXA 0,56  CUBO 7,85" if t >= 22.8 else "DENSIDADE MÉDIA: 0,56", 137, VERDE)
        if VERTICAL: return
        titulo_painel(tela, 'DENSIDADE', 'MÉDIA')
        y = 54
        if t >= 7.8:
            tela.texto('CAIXA: AÇO + AR', PX0, y, BRANCO, tam=9, contorno=PRETO)
            tela.texto('1 KG / 1,8 L = 0,56', PX0, y + 12, VERDE, tam=9, contorno=PRETO)
        if t >= 22.8:
            tela.texto('CUBO: SÓ AÇO', PX0, y + 30, BRANCO, tam=9, contorno=PRETO)
            tela.texto('1 KG / 0,127 L = 7,85', PX0, y + 42, VERMELHO, tam=9, contorno=PRETO)
        marcas = []
        if t >= 7.8: marcas.append((.56, 'CAIXA', VERDE, True))
        if t >= 14.8: marcas.append((1.0, 'ÁGUA', AGUA1, False))
        if t >= 22.8: marcas.append((7.85, 'CUBO', VERMELHO, True))
        medidor_densidade(tela, PX0 + 4, 140, 158, marcas, t=t)
        if t >= 14.8:
            tela.texto('FLUTUA', PX0 + 2, 186, VERDE, tam=9, contorno=PRETO)
            tela.texto('AFUNDA', PX0 + 166, 186, VERMELHO, tam=9, centro='d', contorno=PRETO)
            seta(tela, PX0 + 44, 189, -1, 0, VERDE, 4)
            seta(tela, PX0 + 120, 189, 1, 0, VERMELHO, 4)

    def sons(self, fx):
        for ta, m in ((7.8, 76), (14.8, 79), (22.8, 72)):
            fx.put(fx.blip(m, .1), self.t0 + ta, .15)


# ============================================================ cena de mar com navio
def mar_com_navio(tela, t, yw, x0, frac, n_cont, corte=False, alagados=(), nivel_v=None, extra_px=0.0,
                  doce=False, agua_comp=None, bob=True, Nv=None):
    Nv = Nv or navio()
    ceu(tela, t)
    agua_fundo(tela, 0, yw, W, PALCO_H, doce=doce)
    yq = yw + int(round(calado_px(frac) + extra_px)) + (1 if bob and math.sin(t * 1.3) > .7 else 0)
    ex = Nv.desenhar(tela, x0, yq, t, n_cont=n_cont, corte=corte, alagados=alagados,
                     nivel_agua_v=nivel_v if nivel_v is not None else yq - yw, agua_comp=agua_comp)
    agua_por_cima(tela, 0, yw, W, PALCO_H, t, doce=doce, excluir=ex)
    return yq


# ============================================================ navio: as partes
PECAS = [('casco', 'CASCO DE AÇO'), ('porao', 'PORÕES'), ('antepara', 'ANTEPARAS'),
         ('linha', "LINHA D'ÁGUA"), ('helice', 'HÉLICE E LEME'), ('comp', 'QUASE 400 M')]


class PartesNavio(Cena):
    YW = 150

    def preparar(self):
        self.slot = self.dur / len(PECAS)

    def desenhar(self, tela, t, tg):
        Nv = navio()
        x0 = x_navio() - int(300 * (1 - ease(t / 1.5)))
        yq = mar_com_navio(tela, t, self.YW, x0, .5, 40, corte=True)
        k_at = min(len(PECAS) - 1, int(t / self.slot))
        nome, rot = PECAS[k_at]
        if nome == 'linha':
            for x in range(x0 - 6, x0 + Nv.L + 8, 3):
                tela.ret(x, self.YW, 2, 1, AMARELO)
        if nome == 'comp':
            y = yq - Nv.D - 64
            tela.ret(x0, y, Nv.L + 2, 1, AMARELO)
            seta(tela, x0, y, -1, 0, AMARELO, 4); seta(tela, x0 + Nv.L + 2, y, 1, 0, AMARELO, 4)
            tela.ret(x0, y - 4, 1, 9, AMARELO); tela.ret(x0 + Nv.L + 2, y - 4, 1, 9, AMARELO)
        if VERTICAL:
            if nome != 'comp':
                ax, ay = Nv.pos_peca(x0, yq, nome)
                lx = min(max(ax, 92), 238)
                rotulo(tela, rot, lx, 30, AMARELO, centro=True)
                fio(tela, lx, 40, ax, ay)
            else:
                rotulo(tela, rot, x0 + Nv.L // 2, yq - Nv.D - 78, AMARELO, centro=True)
            return
        for k, (nm, rt) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 10 + k * 22
            atual = k == k_at
            tela.texto(rt, PX0 + 8, y, AMARELO if atual else ACO2, tam=17 if len(rt) < 14 else 9,
                       contorno=PRETO)
            tela.ret(PX0 - 4, y + 4, 6, 6, AMARELO if atual else ACO1)
            if atual and nm not in ('comp',) and t - k * self.slot > .4:
                ax, ay = Nv.pos_peca(x0, yq, nm)
                fio(tela, PX0 - 6, y + 7, ax, ay)
                if nm == 'helice':
                    lx, ly = Nv.pos_peca(x0, yq, 'leme')
                    fio(tela, PX0 - 6, y + 7, lx, ly)

    def sons(self, fx):
        ondas_som(fx, self.t0, self.t0 + self.dur)
        for k in range(len(PECAS)):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + k * self.slot + .4, .15)


# ============================================================ carregando
class Carga(Cena):
    YW = 150
    T0C, T1C = 1.0, 46.0

    def frac(self, t): return min(1.0, max(0.0, (t - self.T0C) / (self.T1C - self.T0C)))

    def guindaste(self, tela, t, Nv, x0, yq, n):
        """Pórtico do cais, atrás do navio. O carrinho leva o próximo contêiner."""
        lx = (x0 + 70, x0 + 120) if not VERTICAL else (x0 + 40, x0 + 80)
        topo = 22
        for x in lx:
            tela.ret(x - 2, topo, 5, self.YW - topo - 2, PRETO)
            tela.ret(x - 1, topo, 3, self.YW - topo - 2, LARANJA)
            for y in range(topo + 6, self.YW - 4, 10):
                tela.linha(x - 1, y, x + 1, y + 5, BRASA)
        xf = min(296, x0 + Nv.L + 20)
        tela.ret(x0 + 20, topo - 3, xf - x0 - 20, 5, PRETO)
        tela.ret(x0 + 21, topo - 2, xf - x0 - 22, 3, LARANJA); tela.ret(x0 + 21, topo - 2, xf - x0 - 22, 1, CHAMA1)
        tela.ret(lx[0] - 6, topo - 12, 14, 10, PRETO); tela.ret(lx[0] - 5, topo - 11, 12, 8, CHAMA1)  # cabine
        if n >= len(Nv.slots) or not (self.T0C < t < self.T1C): return
        per = (self.T1C - self.T0C) / len(Nv.slots)
        u = ((t - self.T0C) % per) / per
        i, j = Nv.slots[n]
        xs = x0 + Nv.U_CARGA0 + i * 10
        ys = yq - Nv.D - 3 - (j + 1) * 5
        xc = xf - 12 + (xs - xf + 12) * min(1, u / .5)
        yc = topo + 4 + max(0.0, (u - .5) / .5) * (ys - topo - 4)
        tela.ret(int(xc) - 1, topo + 1, 12, 3, PRETO)
        tela.ret(int(xc) + 4, topo + 3, 1, int(yc - topo - 3), ACO4)
        D.conteiner(tela, int(xc), int(yc), D.CORES_CONT[(i * 5 + j * 3) % len(D.CORES_CONT)])

    def desenhar(self, tela, t, tg):
        Nv = navio()
        x0 = x_navio()
        f = self.frac(t)
        n = int(f * len(Nv.slots))
        yw = self.YW
        ceu(tela, t)
        # cais ao fundo
        tela.ret(0, yw - 6, W, 6, ACO0); tela.ret(0, yw - 6, W, 1, ACO2)
        agua_fundo(tela, 0, yw, W, PALCO_H)
        yq = yw + int(round(calado_px(f)))
        self.guindaste(tela, t, Nv, x0, yq, n)
        Nv.desenhar(tela, x0, yq, t, n_cont=n, fumaca=False)
        agua_por_cima(tela, 0, yw, W, PALCO_H, t)
        carga = f * PORTE
        cal = 7 + 9 * f
        leitura_v(tela, f"CARGA {I.milhar(carga)} T  CALADO {I.decimal(cal, 1)} M", 160, AMARELO, y=8)
        if t > 1 and not VERTICAL:
            rotulo(tela, '(TEMPO ACELERADO)', (x0 + 8) if not VERTICAL else 160, 196, ACO2,
                   centro=VERTICAL)
        if VERTICAL: return
        tela.texto('CARGA A BORDO', PX0, 6, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{I.milhar(carga)} T", PX0, 17, AMARELO, tam=17, contorno=PRETO)
        tela.texto('= ÁGUA EMPURRADA', PX0, 40, ACO3, tam=9, contorno=PRETO)
        tela.texto('A MAIS', PX0, 50, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{I.milhar(carga)} T", PX0, 61, CIANO, tam=17, contorno=PRETO)
        # porte bruto
        tela.texto('LIMITE (PORTE BRUTO)', PX0, 88, ACO3, tam=9, contorno=PRETO)
        tela.ret(PX0, 99, 112, 8, PRETO); tela.ret(PX0 + 1, 100, int(110 * f), 6, AMARELO)
        tela.ret(PX0 + 1, 100, int(110 * f), 1, CHAMA0)
        if t >= 23.8:
            tela.texto(f"{I.milhar(PORTE)} T", PX0, 112, BRANCO, tam=9, contorno=PRETO)
        if t >= 31.8:
            for k, s in enumerate(('CARGA', 'COMBUSTÍVEL', 'ÁGUA, COMIDA')):
                tela.texto('+ ' + s, PX0, 128 + k * 11, ACO3, tam=9, contorno=PRETO)
        # régua de calado (close das marcas da proa)
        tela.texto('CALADO', PX0 + 166, 6, ACO3, tam=9, centro='d', contorno=PRETO)
        D.regua_calado(tela, PX0 + 122, 20, 166, cal)
        tela.texto(f"{I.decimal(cal, 1)} M", PX0 + 166, 192, AMARELO, tam=9, centro='d', contorno=PRETO)
        if t >= 39.8:
            yy = int(20 + 166 - 16 * 166 / 18)
            tela.ret(PX0 + 114, yy, 8, 1, AMARELO)
            tela.texto('MÁX', PX0 + 112, yy - 3, AMARELO, tam=9, centro='d', contorno=PRETO)

    def sons(self, fx):
        ondas_som(fx, self.t0, self.t0 + self.dur, .03)
        N = len(NAVIO.slots)
        per = (self.T1C - self.T0C) / N
        for k in range(N):
            fx.put(fx.clique(800 + (k % 3) * 200, .04), self.t0 + self.T0C + (k + 1) * per - .02, .12,
                   -.3 + (k % 5) * .15)


# ============================================================ marca de Plimsoll
class Plimsoll(Cena):
    LETRAS = [('S', 'VERÃO'), ('W', 'INVERNO'), ('T', 'TRÓPICOS'), ('F', 'ÁGUA DOCE'),
              ('TF', 'DOCE TROPICAL'), ('WNA', 'INVERNO NO')]

    def ativa(self, t):
        if 15.8 <= t < 22.6:
            return ['S', 'W', 'T', 'F'][min(3, int((t - 15.8) / 1.7))]
        return None

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        cx, cy, esc = (140, 100, 5) if not VERTICAL else (110, 100, 2.6)
        # costado do navio em close: chapas e soldas
        dither(tela, 0, 0, 300, PALCO_H, FUNDO3, ACO0)
        for y in range(18, PALCO_H, 34): tela.ret(0, y, 300, 1, TRACO)
        for x in range(0, 300, 60):
            for y in range(0, PALCO_H, 34):
                tela.ret(x + (y // 34 % 2) * 30, y, 1, 34, TRACO)
        yred = cy + int(11 * esc)
        dither(tela, 0, yred, 300, PALCO_H - yred, VERMELHO, BRASA)
        ys = D.marca_plimsoll(tela, cx, cy, esc, ativa=self.ativa(t), t=t, rotulos=False)
        # nível da água: sobe até S (carregando), depois desce um pouco (linha de inverno)
        y_ini = PALCO_H - 8
        if t < 14.0:
            yw = y_ini + (ys['S'] - y_ini) * suave((t - 1.0) / 12.0)
        elif t < 22.8:
            yw = ys['S']
        else:
            yw = ys['S'] + (ys['W'] - ys['S']) * suave((t - 23.0) / 3.0)
        yw += math.sin(t * 2.2) * 1.5
        agua_por_cima(tela, 0, yw, 300, PALCO_H, t)
        D.marca_plimsoll(tela, cx, cy, esc, ativa=self.ativa(t), t=t, linhas=False)
        if 7.8 <= t < 15.6:
            rotulo(tela, 'LIMITE', cx - int(13 * esc) - 4, ys['S'] - 3, AMARELO, centro='d')
        if VERTICAL:
            a = self.ativa(t)
            txt = dict(self.LETRAS).get(a, 'MARCA DE PLIMSOLL') if a else 'MARCA DE PLIMSOLL'
            leitura_v(tela, (a + ': ' + txt) if a else txt, 130, AMARELO, y=4)
            return
        titulo_painel(tela, 'MARCA DE', 'PLIMSOLL')
        tela.texto('1876, SAMUEL PLIMSOLL', PX0, 46, ACO3, tam=9, contorno=PRETO)
        for k, (l, sig) in enumerate(self.LETRAS):
            y = 66 + k * 20
            at = self.ativa(t) == l or (t >= 22.8 and l == 'W')
            tela.texto(l, PX0, y, AMARELO if at else BRANCO, tam=17, contorno=PRETO)
            tela.texto(sig, PX0 + 44, y + 4, AMARELO if at else ACO3, tam=9, contorno=PRETO)
            if l == 'WNA': tela.texto('ATLÂNTICO NORTE', PX0 + 44, y + 14, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        ondas_som(fx, self.t0, self.t0 + self.dur, .05)
        for k in range(4):
            fx.put(fx.blip(76 + k * 3, .08), self.t0 + 15.8 + k * 1.7, .14)
        fx.put(fx.sino(79), self.t0 + 7.8, .18)


# ============================================================ rio ou mar
class Doce(Cena):
    YW = 150

    def fronteira(self, t):
        """x da divisa rio|mar na tela (rio à esquerda). O navio anda para a esquerda."""
        if t < 29.8:
            return -20 + 340 * suave((t - 3.0) / 11.0)
        return 320 - 340 * suave((t - 29.8) / 4.0)

    def doce_frac(self, t, Nv, x0):
        xb = self.fronteira(t)
        return max(0.0, min(1.0, (xb - x0 - Nv.L * .3) / (Nv.L * .4)))

    def desenhar(self, tela, t, tg):
        Nv = navio()
        x0 = x_navio()
        yw = self.YW
        xb = int(self.fronteira(t))
        f_doce = self.doce_frac(t, Nv, x0)
        ceu(tela, t)
        # margens do rio (terra e árvores no horizonte), andando com a divisa
        if xb > 0:
            for x in range(0, min(W, xb)):
                h = 6 + int(4 * math.sin(x * .05 + 1) + 3 * math.sin(x * .13))
                tela.ret(x, yw - h, 1, h, AGUA0)
                if (x * 7) % 19 == 0:
                    tela.disco(x, yw - h - 3, 3, VERDE); tela.disco(x - 1, yw - h - 4, 1.5, AGUA1)
        agua_fundo(tela, 0, yw, W, PALCO_H)
        if xb > 0: agua_fundo(tela, 0, yw, min(W, xb), PALCO_H, doce=True)
        extra = calado_px(.9) * .025 * f_doce
        yq = yw + int(round(calado_px(.9) + extra)) + (1 if math.sin(t * 1.3) > .7 else 0)
        Nv.desenhar(tela, x0, yq, t, n_cont=int(len(Nv.slots) * .9))
        xbc = max(0, min(W, xb))
        if xbc < W: agua_por_cima(tela, xbc, yw, W, PALCO_H, t)
        if xbc > 0: agua_por_cima(tela, 0, yw, xbc, PALCO_H, t, doce=True, obj=D.OBJ_RIO)
        if 0 < xb < W:
            for y in range(yw + 2, PALCO_H, 3): tela.px(xb + (y % 2), y, ACO3)
        if not VERTICAL and 4 < t < 22:
            if xb > 30: rotulo(tela, 'RIO', min(xb - 30, 260), 30, AGUA1, 17, centro=True)
            if xb < 230: rotulo(tela, 'MAR', max(xb + 30, 30), 30, MISTURA, 17, centro=True)
        rho = 1.025 - .025 * f_doce
        leitura_v(tela, f"ÁGUA {'DOCE' if f_doce > .5 else 'DO MAR'} {I.decimal(rho, 3)}  "
                        f"{'+2,5%' if f_doce > .5 else ''}", 160, AGUA1 if f_doce > .5 else MISTURA2, y=8)
        if VERTICAL: return
        titulo_painel(tela, 'ÁGUA', 'DOCE' if f_doce > .5 else 'DO MAR', c2=AGUA1 if f_doce > .5 else MISTURA)
        tela.texto('KG POR LITRO', PX0, 48, ACO3, tam=9, contorno=PRETO)
        tela.texto(I.decimal(rho, 3), PX0, 59, AGUA1 if f_doce > .5 else MISTURA2, tam=26, contorno=PRETO)
        if t >= 15.8:
            tela.texto('VOLUME SUBMERSO', PX0, 92, ACO3, tam=9, contorno=PRETO)
            tela.texto(f"+{I.decimal(2.5 * f_doce, 1)}%", PX0, 103, AMARELO, tam=17, contorno=PRETO)
        # close da marca: a água entre S e F
        painel(tela, PX0 + 62, 120, 106, 82, borda=ACO1)
        cx, cy = PX0 + 88, 162
        tela.ret(PX0 + 64, 122, 102, 78, FUNDO3)
        at = 'F' if f_doce > .5 else 'S'
        ys = D.marca_plimsoll(tela, cx, cy, 2, ativa=at, t=t, rotulos=False)
        yv = ys['S'] + (ys['F'] - ys['S']) * f_doce + math.sin(t * 2.2) * .8
        agua_por_cima(tela, PX0 + 64, yv, PX0 + 166, 200, t, doce=f_doce > .5)
        D.marca_plimsoll(tela, cx, cy, 2, ativa=at, t=t, linhas=False, letras=('S', 'F'))
        tela.texto('LINHA', PX0, 150, ACO3, tam=9, contorno=PRETO)
        tela.texto('F' if f_doce > .5 else 'S', PX0, 162, AMARELO, tam=26, contorno=PRETO)

    def sons(self, fx):
        ondas_som(fx, self.t0, self.t0 + self.dur, .04)
        fx.put(fx.sino(76), self.t0 + 15.8, .18)


# ============================================================ inundar
class Inundar(Cena):
    T_FURO, T_BORDA, T_FUNDO = 1.5, 15.8, 19.5
    T_NAVIO = 22.8

    def preparar(self):
        self.TQ = Tanque(nivel=124)
        self.larg, self.alt = 15 * PX_CM, 8 * PX_CM

    def h_in(self, t):
        """Altura (cm) da água dentro da caixa: sobe a vazão constante até a borda."""
        return 3.56 * max(0.0, min(1.0, (t - self.T_FURO) / (self.T_BORDA - self.T_FURO)))

    def caixa_estado(self, t):
        """(base y, água dentro px, densidade média)."""
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        h = self.h_in(t)
        nivel = TQ.nivel0 - (1000 + 225 * h) / TQ.area_cm2() * PX_CM
        if t < self.T_BORDA:
            d = 4.44 + h
            return nivel + d * PX_CM, h * PX_CM, (1000 + 225 * h) / 1800, nivel
        u = suave((t - self.T_BORDA) / (self.T_FUNDO - self.T_BORDA))
        yb0 = nivel + 8 * PX_CM
        yb = yb0 + (TQ.TY1 - 1 - yb0) * u
        dens = 1.0 + ((1000 + 1673) / 1800 - 1.0) * u      # cheia d'água: (1.000 g + 1.673 g) / 1,8 L = 1,48
        return yb, self.alt - 3, dens, nivel

    def desenhar(self, tela, t, tg):
        if t < self.T_NAVIO:
            self._caixa(tela, t)
        else:
            self._navio(tela, t - self.T_NAVIO, t)

    def _caixa(self, tela, t):
        fundo_lab(tela)
        TQ = self.TQ
        TQ.TY1 = 172 if VERTICAL else 192          # no Short a legenda cobre o pé do palco
        cx = (TQ.TX0 + TQ.TX1) // 2
        yb, agua_px, dens, nivel = self.caixa_estado(t)
        TQ.fundo(tela, nivel)
        D.caixa(tela, cx, yb, self.larg, self.alt, t, agua_dentro=agua_px, furo=t >= self.T_FURO)
        if self.T_FURO <= t < self.T_BORDA:                       # o jato entrando pelo furo
            hx = int(cx + self.larg * .2) + 1
            for k in range(6):
                u = (t * 4 + k / 6) % 1.0
                tela.px(hx + math.sin(u * 8) * 1.5, yb - 3 - u * 10, MISTURA2)
        if self.T_BORDA <= t < self.T_BORDA + 1.5:                # a água entra por cima da borda
            for s in (-1, 1):
                gotinhas(tela, cx + s * (self.larg / 2 - 4), nivel, nivel + 10, t, MISTURA2, 4)
        TQ.frente(tela, nivel, t, excluir=D.caixa_ar(cx, yb, self.larg, self.alt) if t < self.T_BORDA else ())
        if self.T_FURO <= t < self.T_BORDA:
            hx = int(cx + self.larg * .2)
            rotulo(tela, 'FURO', hx + 12, int(yb) + 8, VERMELHO)
        cor = VERDE if dens < 1 else VERMELHO
        rotulo(tela, I.decimal(dens, 2), cx, max(30, int(yb - self.alt) - 18), cor, 17, centro=True)
        leitura_v(tela, f"DENSIDADE MÉDIA {I.decimal(dens, 2)}", 137, cor)
        if VERTICAL: return
        titulo_painel(tela, 'ENTROU ÁGUA')
        tela.texto('DENSIDADE MÉDIA', PX0, 34, ACO3, tam=9, contorno=PRETO)
        tela.texto(I.decimal(dens, 2), PX0, 45, cor, tam=26, contorno=PRETO)
        tela.texto('AÇO + AR + ÁGUA', PX0, 76, ACO3, tam=9, contorno=PRETO)
        medidor_densidade(tela, PX0 + 4, 120, 158, [(dens, 'CAIXA', cor, True), (1.0, 'ÁGUA', AGUA1, False)], vmax=2.0)
        if t >= 15.8:
            tela.texto('AFUNDA', PX0, 172, VERMELHO, tam=17, contorno=PRETO)

    def _navio(self, tela, u, t):
        Nv = navio()
        x0 = x_navio()
        yw = 150
        ci = Nv.n_comp - 2
        enche = suave((u - .8) / 5.0)
        extra = 3.0 * enche
        yq = yw + int(round(calado_px(.4) + extra))
        ceu(tela, t)
        agua_fundo(tela, 0, yw, W, PALCO_H)
        nv = (yq - yw) * enche
        ex = Nv.desenhar(tela, x0, yq, t, n_cont=30, corte=True, alagados=(ci,) if enche > 0 else (),
                         nivel_agua_v=nv)
        ua, ub = Nv.ante[ci], Nv.ante[ci + 1]
        hx, hy = x0 + (ua + ub) // 2, yq - 8
        tela.ret(hx - 3, hy - 1, 6, 3, PRETO)
        agua_por_cima(tela, 0, yw, W, PALCO_H, t, excluir=ex)
        if enche < 1:
            for k in range(5):
                v = (t * 3 + k / 5) % 1.0
                tela.px(hx + math.sin(v * 9) * 2, hy - 2 - v * max(2, nv - 8), MISTURA2)
        rotulo(tela, 'FURO', hx, yq + 4, VERMELHO, centro=True)
        if u > 6:
            rotulo(tela, 'ANTEPARAS', hx, yq - Nv.D - 44, AMARELO, centro=True)
            fio(tela, hx - 6, yq - Nv.D - 34, x0 + ua, yq - Nv.D + 8)
            fio(tela, hx + 6, yq - Nv.D - 34, x0 + ub, yq - Nv.D + 8)
        leitura_v(tela, "ALAGADOS: 1  AINDA FLUTUA", 160, VERDE, y=8)
        if VERTICAL: return
        titulo_painel(tela, 'COMPARTI-', 'MENTOS')
        for k in range(Nv.n_comp):
            x = PX0 + k * 20
            al = k == ci and enche > .05
            tela.ret(x, 56, 17, 22, MISTURA if al else FUNDO2); tela.ret_vazado(x, 56, 17, 22, ACO3)
            if al: tela.ret(x + 1, 56 + 22 - int(20 * enche) - 1, 15, 1, MISTURA2)
        tela.texto('ALAGADOS', PX0, 92, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{1 if enche > .05 else 0} DE {Nv.n_comp}", PX0, 103, AMARELO, tam=17, contorno=PRETO)
        if u >= 7.0:
            tela.texto('AINDA', PX0, 140, VERDE, tam=17, contorno=PRETO)
            tela.texto('FLUTUA', PX0, 160, VERDE, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.clique(2200, .03), self.t0 + self.T_FURO, .4)
        fx.put(fx.chiado(self.T_BORDA - self.T_FURO, 1500, 6000), self.t0 + self.T_FURO, .06)
        respingo(fx, self.t0 + self.T_BORDA, .3)
        fx.put(fx.explosao(.6), self.t0 + self.T_FUNDO, .3)
        ondas_som(fx, self.t0 + self.T_NAVIO, self.t0 + self.dur)
        fx.put(fx.clique(700, .06), self.t0 + self.T_NAVIO + .8, .4)
        fx.put(fx.chiado(5.0, 400, 2500), self.t0 + self.T_NAVIO + .8, .1)


def recortar_abaixo(pts, y0):
    """Parte do polígono abaixo de y0 (Sutherland-Hodgman numa reta horizontal)."""
    out = []
    n = len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        a_in, b_in = ay >= y0, by >= y0
        if a_in: out.append((ax, ay))
        if a_in != b_in:
            u = (y0 - ay) / (by - ay)
            out.append((ax + (bx - ax) * u, y0))
    return out


# ============================================================ Titanic: diagrama de 16 compartimentos
class Titanic(Cena):
    N = 16
    T_GOLPE = 15.8

    def geom(self):
        if VERTICAL: return 74, 138, 70
        return 12, 248, 70

    def fill(self, t):
        """Quanto cada compartimento já encheu (0..1) até o nível do mar lá fora (0 = popa)."""
        f = [0.0] * self.N
        for j in range(6):                                     # os 6 abertos pelo iceberg
            ta = self.T_GOLPE + .5 + j * .4
            f[self.N - 1 - j] = suave((t - ta) / 6.0)
        for j in range(6, self.N):                             # por cima das anteparas
            ta = 22.8 + (j - 6) * 1.6
            f[self.N - 1 - j] = suave((t - ta) / 2.2)
        return f

    def angulo(self, t, f):
        return math.radians(min(9.0, .8 * sum(f)))

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        x0, L, yd = self.geom()
        Dh = 58
        f = self.fill(t)
        a = self.angulo(t, f)
        piv = (x0 + L * .25, yd + Dh)
        ca, sa = math.cos(a), math.sin(a)

        def R(x, y):
            dx, dy = x - piv[0], y - piv[1]
            return (piv[0] + dx * ca - dy * sa, piv[1] + dx * sa + dy * ca)
        yw = yd + 34
        xmax = 300 if not VERTICAL else W
        dither(tela, 0, yw, xmax, PALCO_H - yw, FUNDO3, FUNDO2)
        casco = [(x0, yd), (x0 + L, yd - 4), (x0 + L - 4, yd + Dh - 12), (x0 + L - 16, yd + Dh),
                 (x0 + 16, yd + Dh), (x0 + 2, yd + Dh - 16)]
        cr = [R(*p) for p in casco]
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            poligono(tela, [(x + dx, y + dy) for x, y in cr], ACO2)
        poligono(tela, cr, FUNDO2)
        cw = L / self.N
        h_ant = Dh * .62                           # anteparas: não chegam ao convés
        for k in range(self.N):
            xa, xb = x0 + k * cw + 1, x0 + (k + 1) * cw - 1
            yb_ = yd + Dh - 2
            q = [R(xa, yd + 3), R(xb, yd + 3), R(xb, yb_), R(xa, yb_)]
            ybot = max(p[1] for p in q)
            if f[k] > 0 and ybot > yw:
                lev = ybot - (ybot - yw) * f[k]
                pts = recortar_abaixo(q, lev)
                if len(pts) >= 3:
                    poligono(tela, pts, MISTURA)
                    tela.ret(int(min(p[0] for p in pts)), int(lev), int(cw) - 1, 1, MISTURA2)
            if t < 7.8 and not VERTICAL:
                n = int(t / .3)
                if k < n:
                    cxk, cyk = R((xa + xb) / 2, yd + Dh - 14)
                    tela.texto(str(k + 1), cxk, cyk - 3, ACO3, tam=9, centro=True)
            if 7.8 <= t < 15.6 and k >= self.N - 2 and int(t * 3) % 2 == 0:
                for (p, q2) in zip(q, q[1:] + q[:1]):
                    tela.linha(p[0], p[1], q2[0], q2[1], CIANO)
        for k in range(1, self.N):
            xk = x0 + k * cw
            p, q = R(xk, yd + Dh - 2), R(xk, yd + Dh - h_ant)
            linha_grossa(tela, p[0], p[1], q[0], q[1], 2, ACO3)
        p, q = R(x0, yd), R(x0 + L, yd - 4)
        linha_grossa(tela, p[0], p[1], q[0], q[1], 2, ACO4)
        # linha d'água (diagrama: tracejada por cima do casco)
        for x in range(0, xmax, 3): tela.ret(x, yw, 2, 1, MISTURA2)
        # iceberg
        if t >= self.T_GOLPE - 1.5:
            ix = x0 + L + 6 + int(20 * (1 - ease((t - self.T_GOLPE + 1.5) / 1.5)))
            pts = [(ix - 5, yw), (ix + 3, yw - 16), (ix + 11, yw - 9), (ix + 19, yw - 19), (ix + 27, yw)]
            poligono(tela, pts, BRANCO)
            poligono(tela, [(ix - 8, yw), (ix + 30, yw), (ix + 24, yw + 36), (ix - 3, yw + 30)], MISTURA2)
            for (p, q) in zip(pts, pts[1:]): tela.linha(p[0], p[1], q[0], q[1], PRETO)
        # rasgos no casco
        if t >= self.T_GOLPE:
            for j in range(6):
                if t < self.T_GOLPE + j * .4: continue
                k = self.N - 1 - j
                xa = x0 + k * cw + 2
                p, q = R(xa, yd + Dh - 10), R(xa + cw - 4, yd + Dh - 11)
                tela.linha(p[0], p[1], q[0], q[1], VERMELHO)
        # transbordando por cima da antepara
        if 22.8 <= t:
            j = min(self.N - 1, 6 + int((t - 22.8) / 1.6))
            k = self.N - 1 - j
            xk = x0 + (k + 1) * cw
            top = R(xk, yd + Dh - h_ant - 2)
            gotinhas(tela, top[0] - 2, top[1] - 3, top[1] + 10, t, MISTURA2, 5, 4.0)
            seta(tela, int(top[0]) - 4, int(top[1]) - 6, -1, 0, AMARELO, 4)
        n_al = sum(1 for x in f if x > .05)
        leitura_v(tela, f"ALAGADOS: {n_al} DE 16", 160, VERMELHO if n_al > 4 else BRANCO, y=8)
        if VERTICAL: return
        rotulo(tela, 'DIAGRAMA (NÃO É O NAVIO)', 8, 196, ACO2)
        titulo_painel(tela, '16 COMPARTI-', 'MENTOS')
        tela.texto('AGUENTAVA', PX0, 50, ACO3, tam=9, contorno=PRETO)
        tela.texto('2 ALAGADOS', PX0, 61, VERDE, tam=17, contorno=PRETO)
        tela.texto('(ATÉ 3 OU 4 EM ALGUNS CASOS)', PX0, 80, ACO3, tam=9, contorno=PRETO)
        if t >= self.T_GOLPE:
            tela.texto('O ICEBERG ABRIU', PX0, 98, ACO3, tam=9, contorno=PRETO)
            tela.texto('6', PX0, 109, VERMELHO, tam=26, contorno=PRETO)
            tela.texto('14/4/1912', PX0 + 30, 116, ACO3, tam=9, contorno=PRETO)
        tela.texto('ALAGADOS', PX0, 140, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{n_al} DE 16", PX0, 151, VERMELHO if n_al > 4 else BRANCO, tam=17, contorno=PRETO)
        if t >= 29.8:
            # forma de gelo inclinada enchendo
            bx, by = PX0 + 88, 176
            nc = 6
            for k in range(nc):
                x = bx + k * 13
                y = by + int((nc - k) * 1.5)
                tela.ret(x, y, 12, 12, PRETO)
                cheio = min(1.0, max(0.0, (t - 29.8) * 1.4 - (nc - 1 - k) * .9))
                tela.ret(x + 1, y + 1, 10, 10, FUNDO2)
                hh = int(10 * cheio)
                if hh: tela.ret(x + 1, y + 11 - hh, 10, hh, MISTURA)
            tela.texto('FORMA DE GELO', PX0 + 88, 194, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(2.4, 200, 1200), self.t0 + self.T_GOLPE, .25)
        fx.put(fx.explosao(2.0), self.t0 + self.T_GOLPE, .3)
        fx.put(fx.chiado(10.0, 300, 2000), self.t0 + self.T_GOLPE + .5, .06)
        for k in range(8):
            fx.put(fx.blip(70 - k, .06), self.t0 + 22.8 + k * 1.6, .08)


# ============================================================ resumo
class Resumo(Cena):
    CX = [64, 178, 292, 406]
    NOMES = [('EMPURRA', 'O SEU PESO'), ('AÇO + AR', 'MÉDIA < 1'), ('PLIMSOLL', 'O LIMITE'), ('ANTEPARAS', 'SEGURAM')]
    TS = [0.5, 8.8, 17.8, 26.8]

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        k_at = max(k for k, ta in enumerate(self.TS) if t >= ta) if t >= self.TS[0] else 0
        for k in range(4):
            cx = self.CX[k]
            aceso = k == k_at
            cor = AMARELO if aceso else ACO1
            painel(tela, cx - 52, 18, 104, 140, borda=cor)
            self._icone(tela, k, cx, 70, t, aceso)
            tela.texto(self.NOMES[k][0], cx, 120, AMARELO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(self.NOMES[k][1], cx, 134, BRANCO if aceso else ACO2, tam=9, centro=True, contorno=PRETO)
            tela.texto(str(k + 1), cx - 44, 24, cor, tam=9)
        tela.texto('FLUTUAR = EMPURRAR O PRÓPRIO PESO EM ÁGUA', W // 2, 180, AMARELO, tam=9, centro=True, contorno=PRETO)

    def _icone(self, tela, k, cx, cy, t, aceso):
        yw = cy + 6
        dither(tela, cx - 44, yw, 88, 34, AGUA1 if k < 2 else MISTURA, AGUA0 if k < 2 else FUNDO3)
        tela.ret(cx - 44, yw, 88, 1, MISTURA2)
        if k == 0:
            D.boia(tela, cx, yw + 10, 30, 22, t)
            forca(tela, cx + 8, yw - 2, 18 if aceso else 12, False, VERMELHO)
            forca(tela, cx - 8, yw + 6, 18 if aceso else 12, True, VERDE)
        elif k == 1:
            D.caixa(tela, cx + 16, yw + 8 + (1 if math.sin(t * 2) > 0 else 0), 30, 16, t, cor_ar=MISTURA2)
            D.cubo(tela, cx - 22, yw + 32, 10, t)
        elif k == 2:
            tela.ret(cx - 44, cy - 30, 88, 36 + 30 - 30, FUNDO3)
            D.marca_plimsoll(tela, cx - 16, cy - 4, 1.6, ativa='S' if aceso else None, t=t, rotulos=False)
            tela.ret(cx - 44, yw, 88, 1, MISTURA2)
        else:
            x0 = cx - 40
            tela.ret(x0 - 1, cy - 20, 82, 46, PRETO)
            tela.ret(x0, cy - 19, 80, 44, FUNDO3)
            for j in range(5):
                xx = x0 + j * 16
                al = j == 3 and aceso
                if al:
                    v = suave((t % 4.0) / 2.0)
                    hh = int(38 * v)
                    tela.ret(xx + 2, cy + 23 - hh, 13, hh, MISTURA)
                if j: tela.ret(xx, cy - 12, 2, 37, ACO3)
            tela.ret(x0, cy - 19, 80, 2, ACO4)

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
            yw = 170
            ceu(tela, t)
            agua_fundo(tela, 0, yw, W, PALCO_H)
            NAVIO.desenhar(tela, int(-260 + (t - RM.OUTRO_S) * 40), yw + 26, t, n_cont=80)
            agua_por_cima(tela, 0, yw, W, PALCO_H, t)
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 30, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 52, AMARELO, tam=9, centro=True, contorno=PRETO)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, densidade=Densidade, empuxo=Empuxo, cubo=Cubo, tigela=Tigela,
             media=Media, navio=PartesNavio, carga=Carga, plimsoll=Plimsoll, doce=Doce, inundar=Inundar,
             titanic=Titanic, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep06_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        so = sys.argv[3:] or None
        ts = []
        for c in trilha.caps:
            if so and c['id'] not in so: continue
            ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 4 if len(ims) > 4 else 2
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
