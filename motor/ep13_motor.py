#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep13 — Como funciona o motor elétrico (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (inversão da corrente, bobina que liga,
                          zumbido do rotor), nos mesmos instantes do desenho
O rotor anda por uma função do tempo por capítulo (simulada com a força de
verdade no motor de corrente contínua, ou presa à grade da música nos
capítulos de ritmo); o desenho e o som leem a mesma função.

Física conferida (ver o cabeçalho de `ep13_desenho.py`): norte à esquerda,
sul à direita, campo para a direita; o lado da bobina com X (corrente
entrando) é empurrado para baixo, o com ponto para cima: o rotor gira no
sentido ANTI-HORÁRIO e o comutador inverte a corrente quando a bobina está em
pé. `checar_fisica()` confere isso na simulação.

    python3 ep13_motor.py <saida.mp4>                   # o episódio inteiro
    python3 ep13_motor.py <saida.mp4> dcmotor batida    # só esses capítulos (teste)
    python3 ep13_motor.py --folha <saida.png> [ids]     # quadros por capítulo (FR=.3,.8)
"""
import math, os, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import ep13_desenho as D
from ep13_desenho import (P, MotorCC, MotorBL, Mascara, pintar, pintar_tela, pintar_pol, pintar_ret, pintar_disco,
                          pintar_setor, brilho, fio, rotulo, barra, seta, seta_arco, fio_corte, fundo_oficina,
                          ima_barra, linhas_dipolo, linhas_ima, tracejar, bussola, pilha, fio_eletrico, ventoinha, maquina,
                          carro, grade, escurecer, COR_FASE)
import ritmo_marca as RM
import idioma as I
from ep13_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2613, 45
GANHO_MUSICA = -10.0          # trilha baixa: o som da máquina e o texto mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 304                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
CX, CY = 140, 104             # centro do motor (o corte vertical pega x 50..230)


def milhar(n):
    return I.milhar(int(n))


# ------------------------------------------------------------ som
def tique(f=3000.0, dur=.03, dec=.006):
    """Um "tic" de seno curtinho (sem ruído: o clique de ruído estoura o pico)."""
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    env = np.minimum(1.0, tt / .0015) * np.exp(-tt / dec)
    y = (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 1.5 * tt) + .3 * np.sin(2 * np.pi * f * .5 * tt)) * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def zumbido(dur, f0, f1, harm=.35, ataque=.25):
    """Zumbido do motor: seno que sobe de f0 a f1 (o tom acompanha o giro)."""
    sr = LG.SR
    n = max(16, int(dur * sr))
    f = np.linspace(f0, f1, n)
    ph = np.cumsum(f) / sr
    y = np.sin(2 * np.pi * ph) + harm * np.sin(4 * np.pi * ph) + .15 * np.sin(6 * np.pi * ph)
    tt = np.arange(n) / sr
    env = np.minimum(1, tt / ataque) * np.minimum(1, (dur - tt) / .3)
    y = y * np.clip(env, 0, 1)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def baque(f=80.0, dur=.18):
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    y = np.sin(2 * np.pi * (f * tt + 30 * (1 - np.exp(-tt / .03)))) * np.minimum(1, tt / .002) * np.exp(-tt / .05)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


# ------------------------------------------------------------ física do motor de corrente contínua
def simular_cc(dur, a0=180.0, k=120.0, c=1.0, comutador=True, t_liga=0.0, sA_fixo=-1, dt=1 / 600.0):
    """Integra o rotor: aceleração = k * torque(a) - c * w (graus/s^2).
    Com comutador, a corrente em A troca a cada meia volta (torque sempre >= 0)."""
    n = int(dur / dt) + 2
    a = np.zeros(n); w = np.zeros(n); s = np.zeros(n, np.int8)
    ang, vel = a0, 0.0
    for i in range(n):
        t = i * dt
        sA = 0
        if t >= t_liga:
            sA = MotorCC.sinal_A(ang) if comutador else sA_fixo
        acc = (k * MotorCC.torque(ang, sA) if sA else 0.0) - c * vel
        a[i], w[i], s[i] = ang, vel, sA
        vel += acc * dt
        ang += vel * dt
    return dict(dt=dt, a=a, w=w, s=s)


def ler_sim(S, t):
    i = int(min(len(S['a']) - 1, max(0, t / S['dt'])))
    return float(S['a'][i]), float(S['w'][i]), int(S['s'][i])


def checar_fisica():
    """O rotor com comutador gira ANTI-HORÁRIO (ângulo crescendo), e sem
    comutador para com o lado A embaixo (270°): N da bobina apontando para o S."""
    S = simular_cc(20, comutador=True)
    assert S['a'][-1] > 180 + 360 * 2, 'rotor deveria girar anti-horário'
    S2 = simular_cc(30, comutador=False, k=250, c=.6)
    assert abs(((S2['a'][-1] - 270) + 180) % 360 - 180) < 3, S2['a'][-1]
    # força: lado com X (sA=-1) na esquerda (cos<0) dá torque positivo
    assert MotorCC.torque(180, -1) > 0 and MotorCC.torque(0, 1) > 0
    return True


def resp(u, k=7.0):
    """Resposta amortecida crítica de 0 a 1 (o ímã alcançando o polo)."""
    u = max(0.0, u)
    return 1 - (1 + k * u) * math.exp(-k * u)


# ------------------------------------------------------------ painéis
def etiqueta(tela, txt, x, y, ax, ay, cor=AMARELO, tam=9, direita=False):
    """Rótulo com fio até a peça. `direita`: o texto termina em x."""
    if VERTICAL: return
    w = tela.largura_texto(txt, tam)
    xt = x - w if direita else x
    rotulo(tela, txt, xt, y, cor, tam)
    hy = y + (3 if tam == 9 else 7)
    x0 = xt - 3
    if ax > x: x0 = xt + w + 3
    fio(tela, x0, hy, ax, ay, cor)


def titulo_painel(tela, l1, l2=None, cor=BRANCO, cor2=AMARELO, y=8):
    if VERTICAL: return
    tela.texto(l1, PX0, y, cor, tam=17, contorno=PRETO)
    if l2: tela.texto(l2, PX0, y + 18, cor2, tam=17, contorno=PRETO)


def hud(tela, voltas, rpm, y=150, nota=None, cor=AMARELO):
    """Placar do protagonista: voltas do rotor e RPM."""
    if VERTICAL: return
    h = 50 if nota else 40
    painel(tela, PX0 - 6, y, 172, h, borda=TRACO)
    tela.texto('VOLTAS', PX0 + 2, y + 6, ACO3, tam=9, contorno=PRETO)
    tela.texto(milhar(max(0, voltas)), PX0 + 74, y + 3, cor, tam=17, centro='d', contorno=PRETO)
    tela.texto('RPM', PX0 + 90, y + 6, ACO3, tam=9, contorno=PRETO)
    tela.texto(milhar(round(abs(rpm))), PX0 + 162, y + 3, BRANCO, tam=17, centro='d', contorno=PRETO)
    tela.texto('NO DESENHO' if nota is None else nota, PX0 + 2, y + 26, ACO1, tam=9)


def hud_vertical(tela, linhas, x=CX):
    """No Short o painel some: uma tarja curta no alto do recorte."""
    if not VERTICAL: return
    for j, (s, cor) in enumerate(linhas):
        w = tela.largura_texto(s, 9) + 10
        painel(tela, x - w // 2, 2 + j * 15, w, 13, borda=cor)
        tela.texto(s, x, 5 + j * 15, cor, tam=9, centro=True)


def corrente_icone(tela, x, y, sinal, txt=True):
    """Ícone do sentido da corrente no fio (ponto / X) com legenda."""
    fio_corte(tela, x + 7, y + 7, 7, sinal)
    if txt:
        s = 'SAINDO DA TELA' if sinal > 0 else ('ENTRANDO NA TELA' if sinal < 0 else 'SEM CORRENTE')
        tela.texto(s, x + 20, y + 4, BRANCO if sinal else ACO2, tam=9, contorno=PRETO)


class Cena:
    legenda = True
    brilho = None

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.spb = 60.0 / cap['bpm']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass


def pendulo(alvo_fn, dur, a0, k=60.0, c=3.0, dt=1 / 240.0):
    """Agulha (ou ímã num eixo) puxada para alvo_fn(t): torque k sen(alvo - a)."""
    n = int(dur / dt) + 2
    out = np.zeros(n)
    a, w = a0, 0.0
    for i in range(n):
        t = i * dt
        out[i] = a
        alvo = alvo_fn(t)
        acc = k * math.sin(math.radians(alvo - a)) * 57.3 - c * w
        w += acc * dt; a += w * dt
    return out


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        self.M = MotorBL(CX, CY, 80)

    def fase(self, t):
        """Campo em passos (1 bobina por batida no começo, acelerando)."""
        # passos: cada vez mais curtos até virar borrão em 6 s
        if t < 6.0:
            u = t / 6.0
            passos = 1.0 * t + 12.0 * u ** 3 * 6.0 / 3.0     # passos dados
            return passos
        return self.fase(5.999) + 40.0 * (t - 6.0)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        p = self.fase(t)
        k = int(math.floor(p))
        rho = 90 + 120 * (k - 1) + 120 * resp(p - k, 6)
        rapido = t >= 6.0
        corr = [0, 0, 0]
        if not rapido: corr[k % 3] = 1
        else: corr = [.6, .6, .6]
        self.M.desenhar(tela, t, rho, corr, borrao=rapido, letras=not rapido)
        if rapido:
            for j in range(3):
                x, y = P(CX, CY, 56, 90 + 120 * j + t * 900)
                brilho(tela, x, y, 10, COR_FASE['ABC'[j]], .7)
        voltas = int((rho - 90) / 360) if not rapido else int(p / 3)
        rpm = 3600 * min(1, (t - 6) / 4 + .45) if rapido else (p - self.fase(max(0, t - .5))) / .5 / 3 * 60
        if VERTICAL:
            hud_vertical(tela, [(f"{milhar(rpm)} RPM", AMARELO)])
            return
        titulo_painel(tela, 'SÓ ÍMÃS E', 'CORRENTE', BRANCO, AMARELO, y=12)
        if t >= 6.0:
            u = ease((t - 6.0) / 1.2)
            painel(tela, PX0 - 6, 62, 172, 52, borda=VERDE)
            tela.texto('EFICIÊNCIA', PX0 + 2, 68, ACO3, tam=9, contorno=PRETO)
            barra(tela, PX0 + 2, 82, 120, 10, .85 * u, VERDE)
            tela.ret(PX0 + 2 + int(120 * .97 * u), 81, 1, 12, AMARELO)
            tela.texto('85% A 97%', PX0 + 2, 98, VERDE, tam=9, contorno=PRETO)
        hud(tela, voltas, rpm, y=150, nota='VELOCIDADE DO DESENHO' if not rapido else 'MOTOR DE 2 POLOS A 60 HZ')

    def sons(self, fx):
        ts = np.arange(0, 6.0, .002)
        ps = np.array([self.fase(t) for t in ts])
        idx = np.nonzero(np.diff(np.floor(ps)) > 0)[0]
        for i in idx:
            t = ts[i + 1]
            fx.put(tique(1800 + 300 * (int(ps[i + 1]) % 3), .04), self.t0 + t, .22, -.2 + .2 * (int(ps[i + 1]) % 3))
        fx.put(zumbido(6.0, 220, 900), self.t0 + 6.0, .14)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def preparar(self):
        self.M1 = MotorBL(70, 200, 46)
        self.M2 = MotorBL(420, 40, 40)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        for M, a in ((self.M1, t * 140), (self.M2, -t * 160)):
            M.desenhar(tela, t, a, (0, 0, 0), letras=False)
        escurecer(tela, 0, 0, W, PALCO_H)
        escurecer(tela, 0, 0, W, PALCO_H)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA O", "MOTOR ELÉTRICO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 15)]
            tela.texto(vis, W // 2 - larg // 2, 60 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", W // 2, 130, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            b = int((t - 2.0) / self.spb)
            for k, nome in enumerate('ABC'):
                x = W // 2 - 50 + k * 36
                on = b % 3 == k
                c = COR_FASE[nome] if on else FUNDO2
                tela.ret(x, 160, 26, 18, c); tela.ret_vazado(x, 160, 26, 18, PRETO)
                tela.texto(nome, x + 13, 163, PRETO if on else ACO2, tam=9, centro=True)

    def sons(self, fx):
        for k in range(5):
            t = 2.0 + k * self.spb
            if t < self.dur - .2: fx.put(fx.blip(72 + (0, 4, 7)[k % 3], .1), self.t0 + t, .16)


# ============================================================ ímãs
class Imas(Cena):
    def preparar(self):
        self.linhas1 = linhas_ima(140, 100, 0, 35, n=4)
        self.linhas2 = linhas_ima(125, 100, 0, 70, n=4, passo_a=10, passo_b=12)
        # ímã no eixo (22,6 s em diante): começa quase do avesso e se alinha
        self.T_PIV = 22.6
        self.piv = pendulo(lambda t: 0.0, self.dur - self.T_PIV + .1, 150.0, k=9.0, c=1.1)

    def pos_b(self, t):
        """Posição x do ímã B (atrai: chega e gruda; empurra: vem e volta)."""
        if t < 7.8: return None
        if t < 15.2:
            u = min(1.0, (t - 8.4) / 2.2)
            if t < 8.4: return 250.0
            return 250 - 90 * u ** 2.4                    # acelera ao chegar (atração cresce)
        if t < 16.4: return 250.0
        # lançado contra o A: freia, para e volta
        tt = t - 16.4
        per = 3.0
        k = tt % per
        x_min = 182.0
        return x_min + 68 * (2 * k / per - 1) ** 2

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        lado = 'atrai'
        if t < 7.8:
            y = 100 + 2 * math.sin(t * 2)
            for pts in self.linhas1:
                tracejar(tela, [(x, yy + (y - 100)) for x, yy in pts], t)
            ima_barra(tela, 140, y, 70, 24, 0)
            if not VERTICAL and t > 1.0:
                etiqueta(tela, 'NORTE', 214, 58, 165, y - 8, VERMELHO)
                etiqueta(tela, 'SUL', 52, 58, 115, y - 8, MISTURA2, direita=True)
                etiqueta(tela, 'LINHAS DE CAMPO', 230, 160, 190, 128, CIANO)
        elif t < 22.6:
            ax = 90
            xb = self.pos_b(t)
            atrai = t < 15.2
            ang_b = 0.0
            if 15.2 <= t < 16.4:
                ang_b = 180 * suave((t - 15.2) / 1.0)
            elif not atrai:
                ang_b = 180.0
            gap0, gap1 = ax + 35, xb - 35
            # campo no vão
            if gap1 - gap0 > 4:
                for k in range(-2, 3):
                    yy = 100 + k * 7
                    if atrai:
                        tracejar(tela, [(gap0, yy), (gap1, yy)], t + k * .2, FUNDO3, CIANO)
                    else:
                        m = (gap0 + gap1) / 2
                        sgn = 1 if k >= 0 else -1
                        pts = [(gap0, yy), (m - 4, yy + sgn * (10 + abs(k) * 10)), (m - 2, yy + sgn * (30 + abs(k) * 14))]
                        pts2 = [(gap1, yy), (m + 4, yy + sgn * (10 + abs(k) * 10)), (m + 2, yy + sgn * (30 + abs(k) * 14))]
                        tracejar(tela, pts, t + k * .2, FUNDO3, CIANO); tracejar(tela, pts2, t + k * .2, FUNDO3, CIANO)
            ima_barra(tela, ax, 100, 70, 24, 0)
            ima_barra(tela, xb, 100, 70, 24, ang_b)
            # força em B
            if atrai and gap1 - gap0 > 3 and t > 8.4:
                seta(tela, xb, 76, xb - 22, 76, AMARELO, cab=4, esp=2)
                seta(tela, ax, 76, ax + 22, 76, AMARELO, cab=4, esp=2)
            if atrai and gap1 - gap0 <= 3:
                for pts in self.linhas2:
                    tracejar(tela, pts, t, FUNDO3, CIANO)
                ima_barra(tela, ax, 100, 70, 24, 0)
                ima_barra(tela, xb, 100, 70, 24, ang_b)
                brilho(tela, gap0, 100, 14, AMARELO, max(0, 1 - (t - 10.6) * 1.5))
            if not atrai and t > 16.4:
                d = gap1 - gap0
                f = max(0.0, min(1.0, 30.0 / max(d, 8)))
                seta(tela, xb, 76, xb + 8 + 22 * f, 76, AMARELO, cab=4, esp=2)
                seta(tela, ax, 76, ax - 8 - 22 * f, 76, AMARELO, cab=4, esp=2)
        else:
            tp = t - self.T_PIV
            a = float(self.piv[min(len(self.piv) - 1, int(tp * 240))])
            for k in range(-2, 3):
                yy = 100 + k * 7
                tracejar(tela, [(125, yy), (176, yy)], t + k * .2, FUNDO3, CIANO, forca=.6)
            ima_barra(tela, 90, 100, 70, 24, 0)
            # base e eixo do ímã solto
            pintar_ret(tela, 205, 132, 30, 8, 'acoesc')
            tela.ret(218, 104, 4, 30, ACO1)
            ima_barra(tela, 220, 100, 60, 18, a)
            pintar_disco(tela, 220, 100, 3, 'aco')
            if not VERTICAL:
                etiqueta(tela, 'EIXO', 252, 150, 221, 128, ACO3)
        if VERTICAL:
            txt = 'POLOS' if t < 7.8 else ('ATRAI' if t < 15.2 else ('EMPURRA' if t < 22.6 else 'ALINHA E PARA'))
            hud_vertical(tela, [(txt, AMARELO)])
            return
        titulo_painel(tela, 'ÍMÃS', None, BRANCO, y=10)
        itens = [('N', 'S', 'ATRAEM', 7.8), ('N', 'N', 'EMPURRAM', 15.2), ('S', 'S', 'EMPURRAM', 15.2)]
        for j, (p1, p2, txt, ta) in enumerate(itens):
            y = 40 + j * 30
            on = (t >= ta) and ((j == 0 and t < 15.2) or (j > 0 and 15.2 <= t < 22.6))
            painel(tela, PX0 - 6, y, 172, 24, borda=AMARELO if on else TRACO)
            for q, pp in enumerate((p1, p2)):
                x = PX0 + 2 + q * 22
                tela.ret(x, y + 5, 16, 14, VERMELHO if pp == 'N' else MISTURA)
                tela.texto(pp, x + 8, y + 8, BRANCO, tam=9, centro=True)
            tela.texto(txt, PX0 + 54, y + 4, AMARELO if on else ACO2, tam=17, contorno=PRETO)
        if t >= 22.6:
            tp = t - self.T_PIV
            a = float(self.piv[min(len(self.piv) - 1, int(tp * 240))])
            w = abs(float(self.piv[min(len(self.piv) - 1, int(tp * 240) + 1)]) - a) * 240
            painel(tela, PX0 - 6, 140, 172, 44, borda=VERMELHO if w < 5 else TRACO)
            tela.texto('ÍMÃ NO EIXO', PX0 + 2, 146, ACO3, tam=9, contorno=PRETO)
            tela.texto('PAROU' if w < 5 else 'GIRANDO', PX0 + 2, 160, VERMELHO if w < 5 else BRANCO, tam=17, contorno=PRETO)

    def sons(self, fx):
        # B gruda no A
        ts = np.arange(8.4, 15.2, .002)
        for t in ts:
            if self.pos_b(t) <= 160.5:
                fx.put(baque(140, .12), self.t0 + t, .35); fx.put(tique(2400, .05), self.t0 + t, .2)
                break
        fx.put(fx.chiado(1.0, 300, 2500), self.t0 + 15.2, .08)
        for k in range(3):
            t = 16.4 + 1.5 + k * 3.0
            if t < 22.6: fx.put(fx.chiado(.5, 200, 1200), self.t0 + t - .25, .08)


# ============================================================ Oersted
class Orsted(Cena):
    T_LIGA, T_INVERTE = 2.5, 16.5

    def preparar(self):
        self.bs = []
        for r, n, off in ((40, 8, 0), (72, 12, 15)):
            for k in range(n):
                self.bs.append((r, off + k * 360 / n))
        self.ag = []
        for r, b in self.bs:
            self.ag.append(pendulo(lambda t, r=r, b=b: self.alvo(t, r, b), self.dur + .1, 90.0, k=30, c=4.0))

    def sinal(self, t):
        if t < self.T_LIGA: return 0
        return 1 if t < self.T_INVERTE else -1

    def alvo(self, t, r, b):
        s = self.sinal(t)
        ex, ey = 0.0, 1.0                                 # campo da Terra: norte para cima
        K = 160.0 / r * s
        tx, ty = math.cos(math.radians(b + 90)), math.sin(math.radians(b + 90))   # ponto: campo anti-horário
        return math.degrees(math.atan2(ey + K * ty, ex + K * tx))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        s = self.sinal(t)
        if s:
            for rr in (24, 56, 88):
                n = 48
                pts = [P(CX, CY, rr, (k * 360 / n) * s) for k in range(n + 1)]
                tracejar(tela, pts, t, FUNDO3, CIANO, vel=12, passo=12)
        for j, (r, b) in enumerate(self.bs):
            x, y = P(CX, CY, r, b)
            a = float(self.ag[j][min(len(self.ag[j]) - 1, int(t * 240))])
            bussola(tela, x, y, 9, a)
        fio_corte(tela, CX, CY, 9, s)
        if s: brilho(tela, CX, CY, 18, AMARELO, .5)
        if VERTICAL:
            hud_vertical(tela, [('FIO LIGADO' if s else 'FIO DESLIGADO', AMARELO if s else ACO2)])
            return
        etiqueta(tela, 'FIO (EM CORTE)', 214, 186, CX + 6, CY + 8, AMARELO)
        titulo_painel(tela, '1820', 'A BÚSSOLA MEXE', AMARELO, BRANCO, y=10)
        painel(tela, PX0 - 6, 56, 172, 64, borda=AMARELO if s else TRACO)
        tela.texto('CORRENTE NO FIO', PX0 + 2, 62, ACO3, tam=9, contorno=PRETO)
        corrente_icone(tela, PX0 + 2, 76, s)
        tela.texto('LIGADA' if s else 'DESLIGADA', PX0 + 2, 98, AMARELO if s else ACO2, tam=17, contorno=PRETO)
        painel(tela, PX0 - 6, 128, 172, 56, borda=TRACO)
        tela.texto('AGULHAS', PX0 + 2, 134, ACO3, tam=9, contorno=PRETO)
        txt = 'APONTAM O NORTE' if not s else ('EM CÍRCULO: ANTI-HORÁRIO' if s > 0 else 'EM CÍRCULO: HORÁRIO')
        tela.texto(txt, PX0 + 2, 148, BRANCO, tam=9, contorno=PRETO)
        bussola(tela, PX0 + 150, 170, 8, 90 + 40 * math.sin(t * 3) * (1 if s else .1))
        if s:
            seta_arco(tela, PX0 + 20, 170, 9, 0 if s > 0 else 180, 270 if s > 0 else -90, CIANO, cab=3)

    def sons(self, fx):
        fx.put(tique(1500, .05, .01), self.t0 + self.T_LIGA, .3)
        fx.put(tique(1300, .05, .01), self.t0 + self.T_INVERTE, .3)
        fx.put(zumbido(13.0, 120, 120, .1, .6), self.t0 + self.T_LIGA, .05)
        fx.put(zumbido(7.4, 120, 120, .1, .6), self.t0 + self.T_INVERTE, .05)


# ============================================================ bobina
class Bobina(Cena):
    T_NUCLEO, T_DESL, T_INV = 15.8, 22.8, 25.4
    X0, X1, RY, N = 76, 204, 28, 9

    def preparar(self):
        self.ag1 = pendulo(lambda t: self.alvo(t, 'eixo'), self.dur + .1, 90.0, k=30, c=4.0)
        self.ag2 = pendulo(lambda t: self.alvo(t, 'cima'), self.dur + .1, 90.0, k=30, c=4.0)

    def corrente(self, t):
        """+1: na frente da bobina a corrente SOBE (norte à esquerda); -1: desce."""
        if t < .3: return 0
        if t < self.T_DESL: return -1
        if t < self.T_INV: return 0
        return 1

    def norte_dir(self, t):
        return self.corrente(t) < 0

    def alvo(self, t, onde):
        s = self.corrente(t)
        if s == 0: return 90.0
        forte = 3.0 if t >= self.T_NUCLEO else 1.6
        n_dir = s < 0
        if onde == 'eixo':                                  # bússola à direita, no eixo
            fx_ = forte if n_dir else -forte
            return math.degrees(math.atan2(1.0, fx_))
        fx_ = -forte * .8 if n_dir else forte * .8           # por fora, o campo volta
        return math.degrees(math.atan2(1.0, fx_))

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        s = self.corrente(t)
        x0, x1, ry, n = self.X0, self.X1, self.RY, self.N
        cy = 100
        passo = (x1 - x0) / n
        nucleo = t >= self.T_NUCLEO
        forca = 0.0 if s == 0 else 1.0
        n_dir = s < 0
        # ---- linhas de campo (por fora: arcos; por dentro: retas)
        if s:
            js = range(5 if nucleo else 3)
            for j in js:
                a, b = 76 + 22 * j, 42 + 16 * j
                for lado in (1, -1):
                    pts = [(140 + a * math.cos(math.radians(q)), cy - lado * b * math.sin(math.radians(q))) for q in range(0, 181, 6)]
                    if not n_dir: pts = pts[::-1]
                    tracejar(tela, pts, t + j * .3, FUNDO3, CIANO, vel=18 if nucleo else 12, passo=10, forca=forca)
        # ---- metade de trás das espiras
        for k in range(n):
            xa = x0 + k * passo + passo / 2
            for q in range(91, 270, 3):
                x = xa + 3 * math.cos(math.radians(q)) + passo / 2 * (q - 90) / 180
                y = cy - ry * math.sin(math.radians(q))
                tela.px(x, y, OLEO0)
        # ---- núcleo de ferro
        if nucleo:
            u = ease((t - self.T_NUCLEO) / 1.2)
            nx = -150 + (x0 - 6 + 150) * u
            pintar_ret(tela, nx, cy - 14, (x1 - x0) + 12, 28, 'ferro')
        if s:
            for k in (-1, 0, 1):
                yy = cy + k * 9
                pts = [(x0 + 4, yy), (x1 - 4, yy)] if n_dir else [(x1 - 4, yy), (x0 + 4, yy)]
                tracejar(tela, pts, t + k * .2, ACO1 if nucleo else FUNDO3, CIANO if not nucleo else BRANCO, vel=18, passo=9)
        # ---- metade da frente (cobre) com a corrente andando
        for k in range(n):
            xa = x0 + k * passo
            pts = []
            for q in range(-90, 91, 6):
                x = xa + 3 * math.cos(math.radians(q)) + passo / 2 * (q + 90) / 180
                y = cy - ry * math.sin(math.radians(q))
                pts.append((x, y))
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                linha_grossa(tela, ax, ay, bx, by, 4, OLEO0)
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                linha_grossa(tela, ax, ay, bx, by, 2, CHAMA1 if s else OLEO1)
            for (ax, ay) in pts[2:6]: tela.px(ax - 1, ay, CHAMA0 if s else LARANJA)
            if s:
                u = (t * 1.6 * (1 if s > 0 else -1) + k * .13) % 1.0
                i = int(u * (len(pts) - 1))
                ax, ay = pts[i]
                tela.ret(ax - 1, ay - 1, 3, 3, AMARELO)
        # ---- fios até a pilha
        on = s != 0
        mais, menos = (122, 192), (158, 192)
        pilha_x = 124
        pintar_ret(tela, 120, 186, 40, 14, 'verde')
        tela.ret(156, 190, 4, 6, ACO2)
        tela.texto('+' if s >= 0 else '-', 128, 189, BRANCO, tam=9, contorno=PRETO)
        tela.texto('-' if s >= 0 else '+', 150, 189, BRANCO, tam=9, contorno=PRETO)
        fio_eletrico(tela, [(x0 + 2, cy + ry), (x0 + 2, 193), (120, 193)], t, on, -1 if s > 0 else 1)
        fio_eletrico(tela, [(x1 + 2, cy + ry), (x1 + 2, 193), (160, 193)], t, on, 1 if s > 0 else -1)
        # ---- bússolas
        a1 = float(self.ag1[min(len(self.ag1) - 1, int(t * 240))])
        a2 = float(self.ag2[min(len(self.ag2) - 1, int(t * 240))])
        bussola(tela, 236, cy, 9, a1)
        bussola(tela, 140, 26, 9, a2)
        # ---- polos
        if s and t >= 7.8:
            for x, nome in ((x1 + 14, 'N' if n_dir else 'S'), (x0 - 14, 'S' if n_dir else 'N')):
                cor = VERMELHO if nome == 'N' else MISTURA
                tela.disco(x, cy - 40, 9, PRETO); tela.disco(x, cy - 40, 8, cor)
                tela.texto(nome, x, cy - 47, BRANCO, tam=17, centro=True)
        if VERTICAL:
            hud_vertical(tela, [('ELETROÍMÃ' if s else 'DESLIGADO', AMARELO if s else ACO2)])
            return
        titulo_painel(tela, 'BOBINA', 'ELETROÍMÃ' if s else 'DESLIGADA', BRANCO, AMARELO if s else ACO2, y=10)
        painel(tela, PX0 - 6, 58, 172, 40, borda=TRACO)
        tela.texto('CORRENTE NA FRENTE', PX0 + 2, 64, ACO3, tam=9, contorno=PRETO)
        txt = 'DESLIGADA' if s == 0 else ('DESCENDO' if s < 0 else 'SUBINDO')
        tela.texto(txt, PX0 + 2, 76, AMARELO if s else ACO2, tam=17, contorno=PRETO)
        if s: seta(tela, PX0 + 150, 76 if s > 0 else 66, PX0 + 150, 66 if s > 0 else 92, AMARELO, cab=3)
        painel(tela, PX0 - 6, 104, 172, 52, borda=CIANO if nucleo and s else TRACO)
        tela.texto('FORÇA DO CAMPO', PX0 + 2, 110, ACO3, tam=9, contorno=PRETO)
        f = 0.0 if s == 0 else (.18 if not nucleo else .18 + .82 * ease((t - self.T_NUCLEO) / 1.2))
        barra(tela, PX0 + 2, 124, 156, 9, f, CIANO)
        if nucleo:
            tela.texto('COM NÚCLEO DE FERRO', PX0 + 2, 140, CIANO, tam=9, contorno=PRETO)
        else:
            tela.texto('SÓ O FIO ENROLADO', PX0 + 2, 140, ACO2, tam=9, contorno=PRETO)
        if s and t >= 7.8:
            painel(tela, PX0 - 6, 162, 172, 24, borda=TRACO)
            tela.texto('NORTE À ' + ('DIREITA' if n_dir else 'ESQUERDA'), PX0 + 2, 168, VERMELHO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for t in (.3, self.T_DESL, self.T_INV):
            fx.put(tique(1400, .05, .01), self.t0 + t, .3)
        fx.put(baque(90, .2), self.t0 + self.T_NUCLEO + 1.2, .3)
        fx.put(fx.chiado(1.2, 300, 1600), self.t0 + self.T_NUCLEO, .1)


# ============================================================ peças
PECAS = [('estator', 'ÍMÃS (ESTATOR)', VERMELHO), ('rotor', 'BOBINA (ROTOR)', LARANJA), ('eixo', 'EIXO', ACO3),
         ('comutador', 'COMUTADOR', LATAO), ('escovas', 'ESCOVAS', ACO2), ('pilha', 'PILHA', VERDE)]


class Pecas(Cena):
    def preparar(self):
        self.M = MotorCC(CX, CY, 80)
        self.slot = self.dur / len(PECAS)
        self.t_liga = 5 * self.slot + 1.2
        self.S = simular_cc(self.dur - self.t_liga + .2, a0=180.0, k=120, c=1.0)

    def rotor(self, t):
        if t < self.t_liga: return 180.0 + 4 * math.sin(t * 1.3) * (t > self.slot), 0.0, 0
        return ler_sim(self.S, t - self.t_liga)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        k_atual = min(len(PECAS) - 1, int(t / self.slot))
        vis, desl = set(), {}
        for k, (nome, rot, cor) in enumerate(PECAS):
            tk = k * self.slot
            if t >= tk:
                vis.add(nome)
                u = (t - tk) / .55
                if u < 1:
                    y = -190 * (1 - u) ** 2 if u < .75 else -5 * math.sin((u - .75) / .25 * math.pi)
                    desl[nome] = (0, int(y))
        a, w, s = self.rotor(t)
        self.M.desenhar(tela, t, a, s, vis=vis, desl=desl, forca=False, polos=s != 0, pilha_on=t >= self.t_liga)
        if VERTICAL:
            hud_vertical(tela, [(PECAS[k_atual][1], PECAS[k_atual][2])])
            return
        A = self.M.ancoras(a)
        for k, (nome, rot, cor) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 10 + k * 21
            atual = k == k_atual
            tela.texto(rot, PX0, y, AMARELO if atual else ACO2, tam=17, contorno=PRETO)
            if atual and t - k * self.slot > .55:
                ax, ay = A[nome]
                tela.ret(PX0 - 6, y + 6, 3, 3, AMARELO)
                fio(tela, PX0 - 6, y + 7, ax, ay)
        if t >= self.t_liga:
            hud(tela, int((a - 180) / 360), w / 6, y=142, nota='CORRENTE LIGADA')

    def sons(self, fx):
        for k in range(len(PECAS)):
            t = self.t0 + k * self.slot + .41
            fx.put(baque(110 + k * 10, .12), t, .25)
            fx.put(fx.sino(76 + k * 2, .5), t, .06)
        fx.put(tique(1400, .05, .01), self.t0 + self.t_liga, .3)
        S = self.S
        sA = S['s']
        idx = np.nonzero(np.diff(sA.astype(int)) != 0)[0]
        for i in idx:
            if i == 0: continue
            fx.put(tique(2600, .03), self.t0 + self.t_liga + i * S['dt'], .14)
        fx.put(zumbido(self.dur - self.t_liga, 60, 140, .2, 2.0), self.t0 + self.t_liga, .05)


# ============================================================ o motor de corrente contínua
class DcMotor(Cena):
    T1_LIGA, T2 = 1.0, 17.8

    def preparar(self):
        self.M = MotorCC(CX, CY, 80)
        self.S1 = simular_cc(self.T2 - self.T1_LIGA + .1, a0=180.0, k=250, c=.6, comutador=False, sA_fixo=-1)
        self.S2 = simular_cc(self.dur - self.T2 + .1, a0=180.0, k=120, c=1.0, comutador=True, t_liga=.6)

    def estado(self, t):
        if t < self.T1_LIGA: return 180.0, 0.0, 0, False
        if t < self.T2:
            a, w, s = ler_sim(self.S1, t - self.T1_LIGA)
            return a, w, s, False
        a, w, s = ler_sim(self.S2, t - self.T2)
        return a, w, s, True

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        a, w, s, com = self.estado(t)
        flash = 0.0
        if com:
            # brilho logo depois de cada inversão
            i = int((t - self.T2) / self.S2['dt'])
            ss = self.S2['s']
            j = i
            while j > 0 and ss[j] == ss[i] and i - j < 200: j -= 1
            if ss[j] != ss[i] and ss[j] != 0: flash = 1 - (i - j) / 200
        self.M.desenhar(tela, t, a, s, comut_corte=com, flash=flash)
        if t >= self.T2 and t < self.T2 + 1.0:
            escurecer(tela, 0, 0, 300, PALCO_H)
        tq = MotorCC.torque(a, s) if s else 0.0
        if VERTICAL:
            hud_vertical(tela, [(('COM COMUTADOR' if com else 'SEM INVERTER'), AMARELO if com else VERMELHO),
                                (f"VOLTAS {max(0, int((a - 180) / 360))}", BRANCO)])
            return
        if self.M.ponta_forca: etiqueta(tela, 'FORÇA', 238, 30, *self.M.ponta_forca, AMARELO)
        titulo_painel(tela, 'COM COMUTADOR' if com else 'SEM INVERTER', None, AMARELO if com else VERMELHO, y=8)
        painel(tela, PX0 - 6, 30, 172, 52, borda=TRACO)
        tela.texto('LADO A DA BOBINA', PX0 + 2, 36, ACO3, tam=9, contorno=PRETO)
        corrente_icone(tela, PX0 + 2, 50, s)
        tela.texto('FORÇA DE GIRO', PX0 + 2, 70, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0 + 80, 70, 80, 7, abs(tq), AMARELO if abs(tq) > .1 else VERMELHO)
        painel(tela, PX0 - 6, 88, 172, 52, borda=VERDE if com else TRACO)
        tela.texto('COMUTADOR', PX0 + 2, 94, ACO3, tam=9, contorno=PRETO)
        if com:
            n_inv = int(np.count_nonzero(np.diff(self.S2['s'][:int((t - self.T2) / self.S2['dt']) + 1].astype(int)) != 0))
            tela.texto(f"INVERSÕES {max(0, n_inv - 1)}", PX0 + 2, 108, VERDE, tam=17, contorno=PRETO)
            tela.texto('A CADA MEIA VOLTA', PX0 + 2, 126, BRANCO, tam=9, contorno=PRETO)
        else:
            tela.texto('DESLIGADO', PX0 + 2, 108, ACO2, tam=17, contorno=PRETO)
            parado = abs(w) < 8 and t > 6
            tela.texto('PAROU ALINHADA' if parado else 'BALANÇA E PARA', PX0 + 2, 126, VERMELHO if parado else BRANCO, tam=9, contorno=PRETO)
        hud(tela, int((a - 180) / 360) if com else 0, w / 6, y=146, nota='CÂMERA LENTA')

    def sons(self, fx):
        fx.put(tique(1400, .05, .01), self.t0 + self.T1_LIGA, .3)
        fx.put(fx.chiado(.8, 300, 2400), self.t0 + self.T2 - .2, .1)
        S = self.S2
        idx = np.nonzero(np.diff(S['s'].astype(int)) != 0)[0]
        for i in idx:
            if S['s'][i] == 0:
                fx.put(tique(1400, .05, .01), self.t0 + self.T2 + (i + 1) * S['dt'], .3); continue
            fx.put(tique(2600, .03), self.t0 + self.T2 + (i + 1) * S['dt'], .2, .1)


# ============================================================ no ritmo da música
class Batida(Cena):
    T_DOBRA = 16.0

    def preparar(self):
        self.M = MotorCC(CX, CY, 80)

    def meias(self, t):
        """Meias voltas dadas (uma inversão em cada inteiro): 1 por batida, depois 2."""
        b = t / self.spb
        if t < self.T_DOBRA: u = b
        else: u = self.T_DOBRA / self.spb + 2 * (t - self.T_DOBRA) / self.spb
        return u - .22 * math.sin(2 * math.pi * u) / (2 * math.pi)     # mais lento na hora da inversão

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        n = self.meias(t)
        a = 90 + 180 * n                     # A no alto em n inteiro: bobina em pé, hora de inverter
        s = MotorCC.sinal_A(a)
        dobra = t >= self.T_DOBRA
        div = self.spb / (2 if dobra else 1)
        fr = (t % div) / div
        flash = max(0.0, 1 - fr * 4)
        self.M.desenhar(tela, t, a, s, flash=flash)
        if flash > 0: brilho(tela, CX, CY, 22, AMARELO, flash * .8)
        voltas = int(n // 2)
        rpm = 120 if dobra else 60
        if VERTICAL:
            hud_vertical(tela, [(f"{rpm} RPM", AMARELO), (f"VOLTAS {voltas}", BRANCO)])
            return
        titulo_painel(tela, 'NA BATIDA', None, BRANCO, y=8)
        batida = int(t / self.spb) % 4
        for j in range(4):
            x = PX0 + j * 40
            aceso = j == batida
            tela.ret(x, 30, 32, 26, AMARELO if aceso else FUNDO2)
            tela.ret_vazado(x, 30, 32, 26, AMARELO)
            if dobra:
                for q in range(2):
                    on = aceso and (t % self.spb) >= q * self.spb / 2
                    tela.ret(x + 5 + q * 12, 49, 9, 4, PRETO if on else ACO0)
            tela.texto(str(j + 1), x + 16, 34, PRETO if aceso else AMARELO, tam=17, centro=True)
        tela.texto('INVERSÕES POR BATIDA', PX0, 66, ACO3, tam=9, contorno=PRETO)
        tela.texto('2' if dobra else '1', PX0, 78, AMARELO, tam=26, contorno=PRETO)
        tela.texto('2 POR VOLTA', PX0 + 30, 86, CIANO, tam=9, contorno=PRETO)
        tela.texto('120 BATIDAS POR MINUTO', PX0, 112, ACO2, tam=9, contorno=PRETO)
        corrente_icone(tela, PX0, 124, s, txt=False)
        tela.texto('LADO A', PX0 + 20, 128, BRANCO, tam=9, contorno=PRETO)
        hud(tela, voltas, rpm, y=146, nota='NO RITMO DA MÚSICA')

    def sons(self, fx):
        ts = np.arange(0, self.dur, .0005)
        ns = np.array([self.meias(t) for t in ts])
        idx = np.nonzero(np.diff(np.floor(ns)) > 0)[0]
        for i in idx:
            t = ts[i + 1]
            fx.put(tique(2600 if int(ns[i + 1]) % 2 else 2000, .035), self.t0 + t, .2, .15 if int(ns[i + 1]) % 2 else -.15)


# ============================================================ escovas
class Escovas(Cena):
    T_SAI, T_BL = 7.8, 15.8

    def preparar(self):
        self.M = MotorCC(CX, CY, 80)
        self.B = MotorBL(CX, CY, 80)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        if t < self.T_BL:
            a = 90 + 700 * t
            s = MotorCC.sinal_A(a)
            vis = {'estator', 'rotor', 'eixo', 'comutador'}
            if t < self.T_SAI: vis |= {'escovas', 'pilha'}
            self.M.desenhar(tela, t, a, s if t < self.T_SAI else 0, vis=vis, forca=False, polos=False)
            # faísca/poeira de carvão nas escovas
            if t < self.T_SAI:
                for k in range(6):
                    u = (t * 2.3 + k * .17) % 1.0
                    x = CX + 6 + u * 16 * math.cos(k)
                    y = CY + 21 + u * 10
                    tela.px(x, y, ACO0 if k % 2 else TRACO)
            else:
                u = ease((t - self.T_SAI) / 1.0)
                # controlador entrando no lugar das escovas
                x = int(-80 + (24 + 80) * u)
                pintar_ret(tela, x, 150, 40, 26, 'verde')
                for k in range(5): tela.ret(x + 4 + k * 7, 176, 3, 4, ACO3)
                tela.ret(x + 10, 156, 20, 12, PRETO)
                tela.texto('CHIP', x + 20, 158, ACO3, tam=9, centro=True)
                if not VERTICAL and u >= 1:
                    etiqueta(tela, 'CONTROLADOR', 70, 190, x + 30, 160, VERDE, direita=False)
        else:
            u = (t - self.T_BL)
            p = u / .45
            k = int(p)
            rho = 90 + 120 * (k - 1) + 120 * resp(p - k, 6)
            corr = [0, 0, 0]; corr[k % 3] = 1
            self.B.desenhar(tela, t, rho, corr)
            if u < .5: escurecer(tela, 0, 0, 300, PALCO_H)
            if not VERTICAL and u > 1:
                etiqueta(tela, 'ÍMÃ GIRA', 240, 70, CX + 18, CY - 10, VERMELHO)
                etiqueta(tela, 'BOBINAS PARADAS', 236, 190, CX + 40, CY + 50, LARANJA)
        if VERTICAL:
            txt = 'ESCOVAS GASTAM' if t < self.T_SAI else ('ELETRÔNICA' if t < self.T_BL else 'SEM ESCOVAS')
            hud_vertical(tela, [(txt, AMARELO)])
            return
        if t < self.T_BL:
            titulo_painel(tela, 'ESCOVAS', None, BRANCO, y=8)
            # lupa: a escova raspando no anel
            painel(tela, PX0 - 6, 30, 172, 82, borda=TRACO)
            desg = min(1.0, t / self.T_SAI)
            cx = PX0 + 80
            ys = 92                                     # topo do anel (lupa)
            pintar_ret(tela, PX0 - 3, ys, 166, 16, 'cobre')
            for k in range(9):                          # vãos do comutador passando
                x = PX0 + ((k * 20 - t * 140) % 180) - 6
                if PX0 - 2 < x < PX0 + 158: tela.ret(x, ys + 1, 2, 14, OLEO0)
            hb = int(26 * (1 - .45 * desg)) if t < self.T_SAI else 0
            if hb:
                tela.ret(cx - 1, 60, 3, ys - hb - 60, ACO1)          # mola
                for yy in range(62, ys - hb, 3): tela.ret(cx - 4, yy, 9, 1, ACO2)
                pintar_ret(tela, cx - 10, ys - hb, 20, hb, 'carvao')
                for k in range(5):                      # pó de carvão saindo
                    u = (t * 1.7 + k * .21) % 1.0
                    tela.px(cx + 12 + u * 30, ys - 2 - u * 10 + k, ACO1 if k % 2 else TRACO)
                brilho(tela, cx, ys, 8, AMARELO, .5 + .5 * math.sin(t * 40))
            tela.texto('DESGASTE', PX0 + 2, 36, ACO3, tam=9, contorno=PRETO)
            barra(tela, PX0 + 2, 48, 70, 7, .45 * desg if t < self.T_SAI else 0, VERMELHO)
            painel(tela, PX0 - 6, 120, 172, 64, borda=VERDE if t >= self.T_SAI else TRACO)
            if t >= self.T_SAI:
                tela.texto('SEM ESCOVAS:', PX0 + 2, 126, VERDE, tam=9, contorno=PRETO)
                tela.texto('A ELETRÔNICA', PX0 + 2, 140, BRANCO, tam=17, contorno=PRETO)
                tela.texto('TROCA A CORRENTE', PX0 + 2, 160, BRANCO, tam=9, contorno=PRETO)
            else:
                tela.texto('RASPANDO O TEMPO TODO', PX0 + 2, 126, BRANCO, tam=9, contorno=PRETO)
                tela.texto('UM DIA, TROCAR', PX0 + 2, 140, VERMELHO, tam=17, contorno=PRETO)
        else:
            titulo_painel(tela, 'SEM ESCOVAS', None, VERDE, y=8)
            painel(tela, PX0 - 6, 34, 172, 70, borda=TRACO)
            tela.texto('FIXO (ESTATOR)', PX0 + 2, 40, ACO3, tam=9, contorno=PRETO)
            tela.texto('BOBINAS', PX0 + 2, 52, LARANJA, tam=17, contorno=PRETO)
            tela.texto('GIRA (ROTOR)', PX0 + 2, 74, ACO3, tam=9, contorno=PRETO)
            tela.texto('ÍMÃ', PX0 + 2, 86, VERMELHO, tam=17, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(self.T_SAI, 1500, 6000, ataque=.5), self.t0, .05)
        fx.put(zumbido(self.T_BL, 300, 300, .3, .4), self.t0, .06)
        fx.put(fx.chiado(.9, 300, 2400), self.t0 + self.T_SAI, .1)
        n = int((self.dur - self.T_BL) / .45)
        for k in range(1, n + 1):
            fx.put(tique(1800 + 300 * (k % 3), .03), self.t0 + self.T_BL + k * .45, .12)


# ============================================================ sem escovas
class Brushless(Cena):
    def preparar(self):
        self.B = MotorBL(CX, CY, 80)
        # passos (instante em que a próxima bobina liga): presos à grade da música
        spb = self.spb
        self.passos = []
        t = 1.2
        while t < self.dur - .05:
            self.passos.append(t)
            if t < 8.8: t += 2 * spb
            elif t < 26.8: t += spb
            else: t += spb / 2
        self.passos = [round(x / (spb / 2)) * (spb / 2) for x in self.passos]

    def estado(self, t):
        import bisect
        i = bisect.bisect_right(self.passos, t) - 1
        if i < 0: return 90.0, -1, 0.0, 0.0
        t_k = self.passos[i]
        T = (self.passos[i + 1] - t_k) if i + 1 < len(self.passos) else self.spb / 2
        k = i + 1                                          # bobina ligada: k % 3 (0 = A)
        rho = 90 + 120 * (k - 1) + 120 * resp((t - t_k) / max(T, .25), 6)
        return rho, k, t - t_k, T

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        rho, k, desde, T = self.estado(t)
        corr = [0, 0, 0]
        if k >= 0: corr[k % 3] = 1
        sensores = (60.0, 180.0, 300.0)
        aceso = None
        for sa in sensores:
            if abs(((rho - sa) + 180) % 360 - 180) < 22: aceso = sa
        self.B.desenhar(tela, t, rho, corr, campo=((90 + 120 * k) if k >= 0 else 90, 1.0 if k >= 0 else 0.0))
        for sa in sensores:
            x, y = P(CX, CY, 80 * .5, sa)
            tela.ret(x - 2, y - 2, 5, 5, PRETO)
            tela.ret(x - 1, y - 1, 3, 3, VERDE if aceso == sa else ACO0)
            if aceso == sa: brilho(tela, x, y, 8, VERDE, .8)
        if k >= 0 and desde < .25:
            x, y = P(CX, CY, 46, 90 + 120 * k)
            brilho(tela, x, y, 18, COR_FASE['ABC'[k % 3]], 1 - desde / .25)
        voltas = int((rho - 90) // 360)
        rpm = (120.0 / max(T, 1e-3)) / 6.0 if k >= 0 else 0.0
        if VERTICAL:
            hud_vertical(tela, [(f"BOBINA {'ABC'[k % 3]}" if k >= 0 else 'PARADO', COR_FASE['ABC'[k % 3]] if k >= 0 else ACO2)])
            return
        if t > 1.5 and k >= 0:
            etiqueta(tela, 'CAMPO', 236, 176, *P(CX, CY, 24, 90 + 120 * k), CIANO)
        if t >= 26.8:
            etiqueta(tela, 'SENSOR', 244, 30, *P(CX, CY, 40, 60), VERDE)
        titulo_painel(tela, 'CONTROLADOR', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 28, 172, 64, borda=TRACO)
        tela.texto('BOBINA LIGADA', PX0 + 2, 34, ACO3, tam=9, contorno=PRETO)
        for j, nome in enumerate('ABC'):
            x = PX0 + 2 + j * 52
            on = k >= 0 and k % 3 == j
            tela.ret(x, 48, 44, 26, COR_FASE[nome] if on else FUNDO2)
            tela.ret_vazado(x, 48, 44, 26, COR_FASE[nome])
            tela.texto(nome, x + 22, 52, PRETO if on else COR_FASE[nome], tam=17, centro=True)
        if k >= 0:
            seq = ' '.join('ABC'[q % 3] for q in range(max(0, k - 5), k + 1))
            tela.texto(seq, PX0 + 2, 78, ACO2, tam=9, contorno=PRETO)
            tela.texto('<- AGORA', PX0 + 6 + tela.largura_texto(seq, 9), 78, AMARELO, tam=9, contorno=PRETO)
        painel(tela, PX0 - 6, 98, 172, 42, borda=VERDE if aceso else TRACO)
        tela.texto('SENSOR DE POSIÇÃO', PX0 + 2, 104, ACO3, tam=9, contorno=PRETO)
        tela.texto('ÍMÃ PASSANDO' if aceso else 'ESPERANDO', PX0 + 2, 118, VERDE if aceso else ACO2, tam=17, contorno=PRETO)
        por = 'POR 2 BATIDAS' if T > self.spb * 1.5 else ('POR BATIDA' if T > self.spb * .75 else 'POR MEIA BATIDA')
        hud(tela, voltas, rpm, y=146, nota=f"1 BOBINA {por}")

    def sons(self, fx):
        for i, t in enumerate(self.passos):
            k = (i + 1) % 3
            fx.put(tique((2000, 2400, 2800)[k], .035), self.t0 + t, .16, (-.3, 0, .3)[k])
            fx.put(baque(70 + 10 * k, .08), self.t0 + t, .12)


# ============================================================ indução
class Inducao(Cena):
    W_CAMPO = 90.0                 # graus por segundo no desenho (o real é muito mais rápido)
    S_VIS = .12                    # escorregamento exagerado no desenho

    def preparar(self):
        dt = 1 / 240.0
        n = int((self.dur + .2) / dt)
        self.rho = np.zeros(n); w = 0.0; r = 90.0
        for i in range(n):
            t = i * dt
            alvo = self.W_CAMPO * (1 - self.S_VIS)
            w += (alvo - w) * dt / 2.2
            r += w * dt
            self.rho[i] = r
        self.dt = dt

    def estado(self, t):
        i = min(len(self.rho) - 1, int(t / self.dt))
        rho = float(self.rho[i])
        w = (float(self.rho[min(len(self.rho) - 1, i + 1)]) - rho) / self.dt
        return 90 + self.W_CAMPO * t, rho, w

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        phi, rho, w = self.estado(t)
        corr = [math.cos(math.radians(phi - a)) for _, a in MotorBL.FASES]
        s = 1 - w / self.W_CAMPO
        barras = []
        for j in range(14):
            b = rho + j * 360 / 14
            barras.append(min(1.0, s / self.S_VIS) * math.cos(math.radians(b - phi)) * 1.0)
        B = MotorBL(CX, CY, 80) if not hasattr(self, 'B') else self.B
        self.B = B
        B.desenhar(tela, t, rho, corr, tipo='gaiola', barras=barras, campo=(phi, 1.0))
        # marca do campo e do rotor no aro
        x, y = P(CX, CY, 96, phi)
        if VERTICAL:
            hud_vertical(tela, [('O ROTOR VAI ATRÁS', AMARELO)])
            return
        if t > 1.0:
            etiqueta(tela, 'BARRAS', 236, 176, *P(CX, CY, 29, rho + 360 / 14 * 3), ACO3)
            etiqueta(tela, 'CAMPO', 240, 20, *P(CX, CY, 20, phi), CIANO)
        titulo_painel(tela, 'INDUÇÃO', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 28, 172, 66, borda=TRACO)
        tela.texto('NO DESENHO', PX0 + 2, 34, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"CAMPO {milhar(self.W_CAMPO / 6)} RPM", PX0 + 2, 46, CIANO, tam=9, contorno=PRETO)
        tela.texto(f"ROTOR {I.decimal(w / 6, 1)} RPM", PX0 + 2, 58, BRANCO, tam=9, contorno=PRETO)
        dif = (phi - rho) / 360.0
        tela.texto(f"FICOU {I.decimal(max(0, dif), 1)} VOLTA ATRÁS", PX0 + 2, 74, AMARELO, tam=9, contorno=PRETO)
        if t >= 15.8:
            painel(tela, PX0 - 6, 100, 172, 42, borda=AMARELO if t >= 22.8 else TRACO)
            tela.texto('4 POLOS, 60 HZ:', PX0 + 2, 106, ACO3, tam=9, contorno=PRETO)
            tela.texto('CAMPO 1.800 RPM', PX0 + 2, 118, CIANO, tam=9, contorno=PRETO)
            tela.texto('ROTOR 1.710 A 1.791', PX0 + 2, 130, BRANCO, tam=9, contorno=PRETO)
        hud(tela, int((rho - 90) // 360), w / 6, y=148, nota='ESCORREGAMENTO EXAGERADO')

    def sons(self, fx):
        fx.put(zumbido(self.dur, 90, 110, .4, 1.5), self.t0, .06)


# ============================================================ em casa
class Casa(Cena):
    T_MAQ, T_CARRO = 14.0, 28.0

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        if t < self.T_MAQ:
            ang = -t * 420
            corte = 1.0 if t >= 7.0 else 0.0
            ventoinha(tela, CX, CY, 150, ang, corte, t)
            voltas = int(t * 420 / 360)
            if not VERTICAL and corte:
                etiqueta(tela, 'ÍMÃS (GIRAM)', 236, 40, *P(CX, CY, 25, 30), VERMELHO)
                etiqueta(tela, 'BOBINAS (PARADAS)', 236, 176, CX + 6, CY + 8, LARANJA)
            nome, cor = 'VENTOINHA', CIANO
        elif t < self.T_CARRO:
            u = t - self.T_MAQ
            ang = -u * 260
            pcx, pcy = maquina(tela, CX, CY, ang, u)
            voltas = int(u * 260 / 360)
            if not VERTICAL and u > 1:
                etiqueta(tela, 'CESTO', 236, 120, pcx + 20, pcy + 10, ACO3)
            nome, cor = 'MÁQUINA DE LAVAR', MISTURA2
        else:
            u = t - self.T_CARRO
            v = min(1.0, u / 3.0)
            ang = -u * 500 * v
            # estrada andando
            tela.ret(0, 170, W if not VERTICAL else 300, 38, FUNDO2)
            tela.ret(0, 170, 300, 1, TRACO)
            for k in range(8):
                x = ((k * 60 - u * 160 * v) % 360) - 40
                tela.ret(x, 188, 26, 3, ACO1)
            corte = 1.0 if u > 2.0 else 0.0
            (mx, my), _ = carro(tela, 40, 170, ang, t, corte, .6 if corte else 0)
            voltas = int(u * 500 * v / 360)
            if not VERTICAL and corte:
                etiqueta(tela, 'MOTOR', 160, 30, mx, my, AMARELO)
                etiqueta(tela, 'BATERIA', 236, 136, 160, 150, VERDE)
            nome, cor = 'CARRO ELÉTRICO', AMARELO
        if VERTICAL:
            hud_vertical(tela, [(nome, cor)])
            return
        titulo_painel(tela, 'NA SUA CASA', None, BRANCO, y=8)
        itens = (('VENTOINHA', CIANO, 0.0), ('MÁQUINA DE LAVAR', MISTURA2, self.T_MAQ), ('CARRO ELÉTRICO', AMARELO, self.T_CARRO))
        for j, (txt, c, ta) in enumerate(itens):
            y = 32 + j * 26
            on = txt == nome
            if t < ta: continue
            painel(tela, PX0 - 6, y, 172, 22, borda=c if on else TRACO)
            tela.texto(txt, PX0 + 2, y + 7, c if on else ACO2, tam=9, contorno=PRETO)
            if on: tela.texto('SEM ESCOVAS', PX0 + 162, y + 7, BRANCO, tam=9, centro='d', contorno=PRETO)
        if nome == 'MÁQUINA DE LAVAR' and t - self.T_MAQ >= 7.0:
            # antes x agora
            y = 114
            painel(tela, PX0 - 6, y, 172, 32, borda=VERDE)
            tela.texto('CORREIA', PX0 + 2, y + 4, ACO2, tam=9, contorno=PRETO)
            tela.ret(PX0 + 2, y + 8, 46, 1, VERMELHO)
            tela.texto('ENGRENAGENS', PX0 + 56, y + 4, ACO2, tam=9, contorno=PRETO)
            tela.ret(PX0 + 56, y + 8, 76, 1, VERMELHO)
            tela.texto('TRAÇÃO DIRETA', PX0 + 2, y + 18, VERDE, tam=9, contorno=PRETO)
        if nome == 'CARRO ELÉTRICO' and t - self.T_CARRO >= 7.0:
            y = 114
            painel(tela, PX0 - 6, y, 172, 30, borda=AMARELO)
            a = (t - self.T_CARRO) * 200
            pintar_disco(tela, PX0 + 14, y + 15, 9, 'aco'); pintar_disco(tela, PX0 + 34, y + 15, 6, 'aco')
            for q in range(6):
                x, yy = P(PX0 + 14, y + 15, 9, a + q * 60); tela.px(x, yy, PRETO)
            tela.texto('1 MARCHA,', PX0 + 48, y + 5, AMARELO, tam=9, contorno=PRETO)
            tela.texto('SEM EMBREAGEM', PX0 + 48, y + 17, BRANCO, tam=9, contorno=PRETO)
        painel(tela, PX0 - 6, 152, 172, 30, borda=TRACO)
        tela.texto('VOLTAS DO ROTOR', PX0 + 2, 158, ACO3, tam=9, contorno=PRETO)
        tela.texto(milhar(voltas), PX0 + 162, 160, AMARELO, tam=17, centro='d', contorno=PRETO)

    def sons(self, fx):
        fx.put(zumbido(self.T_MAQ, 160, 160, .2, .8), self.t0, .05)
        fx.put(zumbido(self.T_CARRO - self.T_MAQ, 70, 90, .4, .8), self.t0 + self.T_MAQ, .06)
        fx.put(zumbido(self.dur - self.T_CARRO, 120, 520, .3, 1.0), self.t0 + self.T_CARRO, .07)
        for t in (7.0, self.T_MAQ, self.T_CARRO, self.T_CARRO + 2.0):
            fx.put(fx.sino(79, .4), self.t0 + t, .06)


# ============================================================ eficiência
class Eficiencia(Cena):
    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        gx, ex, y0 = 24, 176, 44
        if VERTICAL and t < 15.8: gx = ex              # no Short, as duas grades se revezam no recorte
        if not (VERTICAL and t >= 15.8):
            grade(tela, gx, y0, 30, 0, t, .5)
        if t >= 15.8:
            grade(tela, ex, y0, 87, 4, t, 15.9)
        if not (VERTICAL and t >= 15.8): rotulo(tela, 'GASOLINA', gx + 54, 18, LARANJA, 17, centro=True)
        if t >= 15.8: rotulo(tela, 'ELÉTRICO', ex + 54, 18, VERDE, 17, centro=True)
        if t >= 7.8 and not (VERTICAL and t >= 15.8):
            rotulo(tela, 'CERCA DE 30%', gx + 54, 160, VERDE, 9, centro=True)
            rotulo(tela, 'VIRA MOVIMENTO', gx + 54, 172, ACO3, 9, centro=True)
        if t >= 17.6:
            rotulo(tela, '87% A 91%', ex + 54, 160, VERDE, 9, centro=True)
            rotulo(tela, 'COM A FRENAGEM', ex + 54, 172, ACO3, 9, centro=True)
        if VERTICAL:
            hud_vertical(tela, [('ENERGIA QUE VIRA MOVIMENTO', AMARELO)], x=231)
            return
        titulo_painel(tela, 'PARA ONDE VAI', 'A ENERGIA', BRANCO, AMARELO, y=8)
        itens = ((VERDE, 'MOVIMENTO'), (CIANO, 'FAIXA (87-91%)'), (VERMELHO, 'PERDAS (CALOR)'))
        for j, (c, txt) in enumerate(itens):
            if j == 1 and t < 15.8: continue
            y = 52 + j * 16
            tela.ret(PX0, y, 10, 10, c); tela.ret_vazado(PX0, y, 10, 10, PRETO)
            tela.texto(txt, PX0 + 16, y + 1, BRANCO, tam=9, contorno=PRETO)
        if t >= 22.8:
            painel(tela, PX0 - 6, 104, 172, 80, borda=TRACO)
            tela.texto('PERDAS DO MOTOR', PX0 + 2, 110, ACO3, tam=9, contorno=PRETO)
            for j, (txt, c) in enumerate((('ATRITO E VENTO', ACO3), ('CALOR NOS FIOS', LARANJA), ('CALOR NO FERRO', ACO2))):
                if t < 22.8 + j * .6: continue
                y = 124 + j * 16
                tela.ret(PX0 + 2, y + 1, 6, 6, c)
                tela.texto(txt, PX0 + 14, y, BRANCO, tam=9, contorno=PRETO)
        tela.texto('FONTE: ENERGY.GOV (EUA)', PX0, 190, ACO1, tam=9)

    def sons(self, fx):
        for i in range(0, 100, 5):
            fx.put(fx.blip(72 + (i // 10), .05), self.t0 + .5 + i * .012, .06)
            fx.put(fx.blip(76 + (i // 10), .05), self.t0 + 15.9 + i * .012, .06)


# ============================================================ torque
class Torque(Cena):
    T_CARRO = 15.8
    N0 = 100.0                         # RPM sem carga no desenho

    def preparar(self):
        self.B = MotorBL(110, 100, 66)
        dt = 1 / 240.0
        n = int((self.dur + .2) / dt)
        self.v = np.zeros(n); self.a = np.zeros(n)
        v, a = 0.0, 0.0
        for i in range(n):
            t = i * dt
            if t > 1.0:
                tq = 1 - v / self.N0
                v += (tq * 40 - v * .08) * dt        # torque menos carga leve
            a += v * 6 * dt
            self.v[i], self.a[i] = v, a
        self.dt = dt

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        i = min(len(self.v) - 1, int(t / self.dt))
        v, a = float(self.v[i]), float(self.a[i])
        tq = 1 - v / self.N0 if t > 1.0 else 0.0
        if t < self.T_CARRO:
            phi = 90 + a + 70
            corr = [math.cos(math.radians(phi - aa)) * (1 if t > 1.0 else 0) for _, aa in MotorBL.FASES]
            self.B.desenhar(tela, t, 90 + a, corr, letras=False)
            if tq > .05:
                seta_arco(tela, 110, 100, 80, 200, 200 + 120 * tq, AMARELO, cab=5)
                rotulo(tela, 'TORQUE', 200, 180, AMARELO, 9)
        else:
            u = t - self.T_CARRO
            vel = min(1.0, u / 6.0) ** .8
            tela.ret(0, 170, 300, 38, FUNDO2)
            tela.ret(0, 170, 300, 1, TRACO)
            dist = 160 * (u ** 2) / 12 if u < 6 else 160 * (3 + (u - 6))
            for k in range(8):
                x = ((k * 60 - dist) % 360) - 40
                tela.ret(x, 188, 26, 3, ACO1)
            # semáforo
            sx = 250 - dist * .5
            if sx > -10:
                tela.ret(sx, 110, 4, 60, ACO1)
                pintar_ret(tela, sx - 6, 92, 16, 22, 'plast')
                tela.disco(sx + 2, 98, 3, FUNDO3 if u > .3 else VERMELHO)
                tela.disco(sx + 2, 107, 3, VERDE if u > .3 else FUNDO3)
            carro(tela, 30, 170, -dist * 2.2, t, 1.0, .9 * (1 - vel) + .2)
        if VERTICAL:
            hud_vertical(tela, [('FORÇA DESDE O ZERO', AMARELO)])
            return
        titulo_painel(tela, 'TORQUE', None, BRANCO, y=8)
        # gráfico torque x velocidade (reta: máximo parado)
        gx, gy, gw, gh = PX0 + 14, 34, 140, 96
        painel(tela, PX0 - 6, 28, 172, 122, borda=TRACO)
        tela.ret(gx, gy, 1, gh, ACO2); tela.ret(gx, gy + gh, gw, 1, ACO2)
        tela.linha(gx, gy + 6, gx + gw - 6, gy + gh, AMARELO)
        tela.texto('TORQUE', gx + 4, gy, ACO3, tam=9, contorno=PRETO)
        tela.texto('RPM', gx + gw - 18, gy + gh + 4, ACO3, tam=9, contorno=PRETO)
        tela.texto('0', gx - 8, gy + gh + 4, ACO3, tam=9, contorno=PRETO)
        if t < self.T_CARRO:
            f = min(1.0, v / self.N0)
            px_, py_ = gx + f * (gw - 6), gy + 6 + f * (gh - 6)
            tela.disco(px_, py_, 4, PRETO); tela.disco(px_, py_, 3, BRANCO)
            if t > 1.0 and v < 8: brilho(tela, px_, py_, 12, AMARELO, .8)
            tela.texto('PARADO: MÁXIMO' if v < 8 else 'GIRANDO: MENOS', PX0 + 2, 136, AMARELO if v < 8 else BRANCO, tam=9, contorno=PRETO)
            hud(tela, int(a / 360), v, y=156, nota='MOTOR DE ÍMÃ')
        else:
            tela.texto('LARGADA COM', PX0 + 2, 136, AMARELO, tam=9, contorno=PRETO)
            tela.texto('TORQUE ALTO', PX0 + 80, 136, AMARELO, tam=9, contorno=PRETO)
            painel(tela, PX0 - 6, 156, 172, 28, borda=AMARELO)
            tela.texto('SEM EMBREAGEM', PX0 + 2, 165, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(zumbido(self.T_CARRO - 1.0, 40, 400, .3, .4), self.t0 + 1.0, .07)
        fx.put(zumbido(self.dur - self.T_CARRO - .3, 80, 700, .3, .3), self.t0 + self.T_CARRO + .3, .08)
        fx.put(fx.blip(84, .08), self.t0 + self.T_CARRO + .3, .12)


# ============================================================ história
class Historia(Cena):
    MARCOS = (('1820', 'OERSTED', 0.5), ('1821', 'FARADAY', 6.0), ('1832', 'STURGEON', 11.8), ('1885/87', 'FERRARIS, TESLA', 17.8))

    def preparar(self):
        self.CC = MotorCC(140, 92, 60)
        self.BL = MotorBL(140, 92, 60)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        k = 0
        for j, (_, _, ta) in enumerate(self.MARCOS):
            if t >= ta - .5: k = j
        u = t - self.MARCOS[k][2]
        if k == 0:
            # visto de cima: o fio passa POR CIMA da bússola, de sul para norte;
            # com corrente, a agulha vira para o oeste (para a esquerda)
            s = 1 if (u % 4.0) > 1.2 else 0
            pintar_ret(tela, 96, 52, 88, 88, 'acoesc')
            if s:
                tt = (u % 4.0) - 1.2
                a = 140 + 50 * math.exp(-tt * 2.5) * math.cos(tt * 9)
            else:
                a = 90 + 50 * math.exp(-(u % 4.0) * 2.5) * math.cos((u % 4.0) * 9) if u > 4 else 90
            bussola(tela, 140, 96, 34, a)
            tela.texto('N', 140, 40, BRANCO, tam=9, centro=True, contorno=PRETO)
            linha_grossa(tela, 140, 14, 140, 176, 6, PRETO)
            linha_grossa(tela, 140, 14, 140, 176, 4, OLEO1 if not s else CHAMA1)
            if s:
                for q in range(4):
                    y = 176 - ((u * 60 + q * 40) % 160)
                    tela.ret(139, y, 3, 3, AMARELO)
                seta(tela, 154, 160, 154, 120, AMARELO, cab=3)
        elif k == 1:
            # rotação de Faraday: o fio gira em volta do ímã num copo
            pintar_pol(tela, [(96, 120), (184, 120), (176, 160), (104, 160)], 'vidro')
            tela.ret(102, 124, 76, 10, ACO3); tela.ret(102, 124, 76, 1, BRANCO)
            ima_barra(tela, 140, 112, 46, 12, 90, letras=False)
            a = u * 200
            ex, ey = 140 + 26 * math.cos(math.radians(a)), 128 + 6 * math.sin(math.radians(a))
            linha_grossa(tela, 140, 30, ex, ey, 3, PRETO); tela.linha(140, 30, ex, ey, CHAMA1)
            pintar_ret(tela, 120, 24, 40, 8, 'aco')
            brilho(tela, ex, ey, 6, AMARELO, .8)
        elif k == 2:
            a = 180 + u * 260
            self.CC.desenhar(tela, t, a, MotorCC.sinal_A(a), forca=False, polos=False, vis={'estator', 'rotor', 'eixo', 'comutador', 'escovas'})
        else:
            phi = 90 + u * 240
            corr = [math.cos(math.radians(phi - aa)) for _, aa in MotorBL.FASES]
            self.BL.desenhar(tela, t, phi - 15, corr, campo=(phi, 1.0), letras=False)
        # linha do tempo
        y = 182
        tela.ret(20, y, 260, 2, ACO1)
        for j, (ano, nome, ta) in enumerate(self.MARCOS):
            x = 36 + j * 76
            on = j == k
            tela.disco(x, y + 1, 5 if on else 3, AMARELO if on else ACO2)
            if t >= ta - .5:
                tela.texto(ano, x, y - 14, AMARELO if on else ACO3, tam=9, centro=True, contorno=PRETO)
        if VERTICAL:
            hud_vertical(tela, [(self.MARCOS[k][0], AMARELO)])
            return
        titulo_painel(tela, 'HISTÓRIA', None, BRANCO, y=8)
        ano, nome, _ = self.MARCOS[k]
        painel(tela, PX0 - 6, 34, 172, 70, borda=AMARELO)
        tela.texto(ano, PX0 + 2, 40, AMARELO, tam=26, contorno=PRETO)
        tela.texto(nome, PX0 + 2, 72, BRANCO, tam=9, contorno=PRETO)
        sub = ('A CORRENTE MEXE A AGULHA', 'O PRIMEIRO GIRO', 'MOTOR COM COMUTADOR', 'O CAMPO QUE GIRA')[k]
        tela.texto(sub, PX0 + 2, 86, CIANO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for j, (_, _, ta) in enumerate(self.MARCOS):
            fx.put(fx.sino(72 + j * 3, .6), self.t0 + ta, .08)


# ============================================================ trifásico no ritmo
class Trifasico(Cena):
    T_VET, T_ACEL, T_REAL = 15.8, 24.0, 31.8

    def preparar(self):
        self.B = MotorBL(CX, CY, 80)
        spb = self.spb
        # trechos (t0, pulsos por batida): o pico de uma fase cai em cada pulso
        self.trechos = [(0.0, 1), (self.T_ACEL, 2), (28.0, 4)]

    def pulsos(self, t):
        """Picos de fase dados até t (A no 0, B no 1, C no 2...)."""
        spb = self.spb
        tot, ant_t, ant_r = 0.0, 0.0, 1
        for t0, r in self.trechos[1:]:
            if t < t0: break
            tot += (t0 - ant_t) / spb * ant_r
            ant_t, ant_r = t0, r
        return tot + (t - ant_t) / spb * ant_r

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        real = t >= self.T_REAL
        p = self.pulsos(min(t, self.T_REAL))
        phi = 90 + 120 * p
        if real:
            u = t - self.T_REAL
            phi += 360 * 60 * u * min(1, u / 2) * .02
        corr = [math.cos(math.radians(phi - a)) for _, a in MotorBL.FASES]
        if real:
            corr = [.6 * math.cos(t * 50 + j * 2.1) for j in range(3)]
        rho = phi - 15
        self.B.desenhar(tela, t, rho, corr, campo=None if real else (phi, 1.0), borrao=real)
        # vetores das fases (de 15,8 a 24 s): cada bobina empurra no seu eixo e a soma gira
        if self.T_VET <= t < self.T_ACEL:
            for j, (nome, a) in enumerate(MotorBL.FASES):
                L = 30 * corr[j]
                x, y = P(CX, CY, abs(L), a if L > 0 else a + 180)
                if abs(L) > 3: seta(tela, CX, CY, x, y, COR_FASE[nome], cab=3, esp=1)
        fr = p % 1.0
        if not real and fr < .25:
            k = int(math.floor(p)) % 3
            x, y = P(CX, CY, 46, MotorBL.FASES[k][1])
            brilho(tela, x, y, 18, COR_FASE['ABC'[k]], 1 - fr / .25)
        rpm = (120 * self.trechos[[i for i, (t0, _) in enumerate(self.trechos) if t >= t0][-1]][1] / self.spb) / 6 if not real else 3600 * min(1, (t - self.T_REAL) / 3)
        if VERTICAL:
            if real: hud_vertical(tela, [('60 VOLTAS POR SEGUNDO', AMARELO)])
            else:
                k = int(math.floor(p)) % 3
                hud_vertical(tela, [(f"FASE {'ABC'[k]}", COR_FASE['ABC'[k]])])
            return
        titulo_painel(tela, '3 FASES', None, BRANCO, y=8)
        # as três correntes (ondas) rolando: o pico de cada uma num pulso
        gx, gy, gw, gh = PX0, 32, 164, 64
        painel(tela, gx - 6, gy - 4, 172, gh + 8, borda=TRACO)
        tela.ret(gx, gy + gh // 2, gw, 1, FUNDO3)
        tela.ret(gx + gw - 30, gy, 1, gh, ACO1)
        if not real:
            for j, nome in enumerate('ABC'):
                cor = COR_FASE[nome]
                for xx in range(gw):
                    pp = p - (gw - 30 - xx) / 40.0          # 40 px por pulso
                    v = math.cos(math.radians(120 * pp - 120 * j))
                    tela.px(gx + xx, gy + gh // 2 - v * (gh // 2 - 4), cor)
            k = int(math.floor(p + .5)) % 3
            tela.texto(f"PICO: {'ABC'[k]}", gx + 2, gy + 2, COR_FASE['ABC'[k]], tam=9, contorno=PRETO)
        else:
            for j, nome in enumerate('ABC'):
                for xx in range(0, gw, 1):
                    v = math.sin(xx * .9 + j * 2.1 + t * 30)
                    tela.px(gx + xx, gy + gh // 2 - v * (gh // 2 - 4), COR_FASE[nome])
            tela.texto('60 HZ', gx + 2, gy + 2, BRANCO, tam=9, contorno=PRETO)
        # batidas
        batida = int(t / self.spb) % 4
        for j in range(4):
            x = PX0 + j * 41
            aceso = j == batida and not real
            k = (int(t / self.spb) - batida + j) % 3
            cor = COR_FASE['ABC'[k]] if t < self.T_ACEL else AMARELO
            tela.ret(x, 104, 34, 20, cor if aceso else FUNDO2)
            tela.ret_vazado(x, 104, 34, 20, cor)
            tela.texto('ABC'[k] if t < self.T_ACEL else str(j + 1), x + 17, 108, PRETO if aceso else cor, tam=9, centro=True)
        if t >= self.T_VET and t < self.T_ACEL:
            tela.texto('SOMA: SEMPRE DO MESMO TAMANHO', PX0, 130, CIANO, tam=9, contorno=PRETO)
        elif t >= self.T_ACEL and not real:
            tela.texto('ACELERANDO NO RITMO', PX0, 130, AMARELO, tam=9, contorno=PRETO)
        elif real:
            tela.texto('2 POLOS: 3.600 RPM', PX0, 130, AMARELO, tam=9, contorno=PRETO)
        hud(tela, int((rho - 75) // 360), rpm, y=146, nota='TOMADA: 60 HZ' if real else 'NO RITMO DA MÚSICA')

    def sons(self, fx):
        notas = (72, 76, 79)
        t = 0.0
        dt = .0005
        ts = np.arange(0, self.T_REAL, dt)
        ps = np.array([self.pulsos(x) for x in ts])
        idx = np.nonzero(np.diff(np.floor(ps + 1e-9)) > 0)[0]
        fx.put(fx.sino(notas[0], .5), self.t0 + .0, .14)
        for i in idx:
            tt = ts[i + 1]
            k = int(round(ps[i + 1])) % 3
            g = .14 if tt < self.T_ACEL else (.09 if tt < 28.0 else .05)
            fx.put(fx.sino(notas[k], .5 if tt < 28 else .25), self.t0 + tt, g, (-.4, 0, .4)[k])
        fx.put(zumbido(self.dur - self.T_REAL, 200, 1200, .3, 2.0), self.t0 + self.T_REAL, .1)


# ============================================================ resumo
class Resumo(Cena):
    def preparar(self):
        self.CC = MotorCC(CX, CY, 80)
        self.BL = MotorBL(210, 104, 60)

    def desenhar(self, tela, t, tg):
        fundo_oficina(tela)
        if t < 8.8:
            x = 220 - 50 * suave(min(1.0, t / 2.0))
            ima_barra(tela, 80, 70, 70, 22, 0)
            ima_barra(tela, x, 70, 70, 22, 0)
            if x > 152: seta(tela, x, 48, x - 18, 48, AMARELO, cab=3, esp=2)
            # eletroímã
            for k in range(7):
                xx = 70 + k * 14
                tela.ret(xx, 132, 6, 40, PRETO); tela.ret(xx + 1, 133, 4, 38, CHAMA1 if (int(t * 6) + k) % 7 else AMARELO)
            pintar_ret(tela, 62, 144, 108, 14, 'ferro')
            for k in range(7):
                xx = 70 + k * 14
                tela.ret(xx + 1, 144, 4, 14, CHAMA1)
            tela.texto('N', 182, 146, VERMELHO, tam=17, contorno=PRETO); tela.texto('S', 40, 146, MISTURA2, tam=17, contorno=PRETO)
        elif t < 17.8:
            a = 90 + 180 * ((t - 8.8) / .75)
            self.CC.desenhar(tela, t, a, MotorCC.sinal_A(a))
        else:
            u = t - 17.8
            ventoinha(tela, 70, 100, 100, -u * 400, 1.0, t)
            phi = 90 + u * 300
            corr = [math.cos(math.radians(phi - aa)) for _, aa in MotorBL.FASES]
            self.BL.desenhar(tela, t, phi - 15, corr, campo=(phi, 1.0), letras=False)
        if VERTICAL:
            hud_vertical(tela, [('RESUMO', AMARELO)])
            return
        titulo_painel(tela, 'RESUMO', None, BRANCO, y=8)
        passos = (('1', 'ÍMÃS: ATRAI E EMPURRA', 0.5), ('2', 'CORRENTE: ELETROÍMÃ', 3.0),
                  ('3', 'INVERTER NA HORA CERTA', 8.8), ('4', 'O ROTOR PERSEGUE', 12.0), ('5', 'NA CASA E NO CARRO', 17.8))
        for j, (n, txt, ta) in enumerate(passos):
            if t < ta: continue
            y = 34 + j * 26
            u = ease((t - ta) / .4)
            x = int(PX0 + (1 - u) * 150)
            on = (j < 4 and passos[j + 1][2] > t) or (j == 4)
            painel(tela, x - 6, y, 172, 22, borda=AMARELO if on else TRACO)
            tela.texto(n, x + 2, y + 7, AMARELO, tam=9, contorno=PRETO)
            tela.texto(txt, x + 14, y + 7, BRANCO if on else ACO2, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k, ta in enumerate((0.5, 3.0, 8.8, 12.0, 17.8)):
            fx.put(fx.blip(72 + k * 2, .12), self.t0 + ta, .14)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))
        self.B = MotorBL(W // 2, 132, 56)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            fundo_oficina(tela)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 18, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 38, AMARELO, tam=9, centro=True, contorno=PRETO)
            phi = 90 + 120 * (t / self.spb)
            corr = [math.cos(math.radians(phi - aa)) for _, aa in MotorBL.FASES]
            self.B.desenhar(tela, t, phi - 15, corr, campo=(phi, 1.0), letras=False)

    def tela_pronta(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .75)


# longo.py chama `cena.pos(baixo, t)` para a cena que entrega RGB pronto (a vinheta).
Fim.pos = Fim.tela_pronta

CENAS = dict(gancho=Gancho, titulo=Titulo, imas=Imas, orsted=Orsted, bobina=Bobina, pecas=Pecas, dcmotor=DcMotor,
             batida=Batida, escovas=Escovas, brushless=Brushless, inducao=Inducao, casa=Casa, eficiencia=Eficiencia,
             torque=Torque, historia=Historia, trifasico=Trifasico, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep13_motor as EP
    checar_fisica()
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
