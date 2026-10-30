#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep01 — Como funciona o motor do carro (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                põe no banco de efeitos o que se ouve (válvula,
                          faísca, queima, escape), nos mesmos instantes do desenho
Toda posição do motor sai de uma função teta(t) por capítulo: o desenho e o
som leem a mesma função, então a explosão soa no quadro em que a chama nasce.

    python3 ep01_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep01_motor.py <saida.mp4> pecas potencia   # só esses capítulos (teste)
    python3 ep01_motor.py --folha <saida.png>          # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1, AGUA0, AGUA1)
import motor_pixel as MP
import ep01_extra as EX
from ep01_extra import rotulo, hsh
import ritmo_marca as RM
from ep01_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2601, 45
GANHO_MUSICA = -10.0          # trilha baixa: o som da máquina e o texto mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0

OX, OY = 165, 172             # centro do virabrequim no close-up
NOMES = ['ADMISSÃO', 'COMPRESSÃO', 'COMBUSTÃO', 'ESCAPE']


def milhar(n):
    return f"{int(n):,}".replace(',', '.')
PX0 = 302                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px


def amostrar_teta(fn, t0, t1, passo=.001):
    ts = np.arange(t0, t1, passo)
    return ts, np.array([fn(t) for t in ts])


def cruzamentos(fn, t0, t1, alvo, periodo=720.0, passo=.001):
    """Instantes em que teta passa por `alvo` (mod período) entre t0 e t1."""
    ts, th = amostrar_teta(fn, t0, t1, passo)
    k = np.floor((th - alvo) / periodo)
    idx = np.nonzero(np.diff(k) > 0)[0]
    return [float(ts[i + 1]) for i in idx]


def cor_tempo(k): return MP.TEMPOS[k][3]


def painel_ciclo(tela, teta, numero=True, y0=10):
    """Painel da direita: tempo atual, relógio do ciclo, válvulas, ângulo."""
    k, _, cor = MP.tempo_de(teta)
    nome = NOMES[k]
    if numero:
        tela.texto(f"TEMPO {k + 1} DE 4", PX0, y0, ACO3, tam=17, contorno=PRETO)
    tela.texto(nome, PX0, y0 + 20, cor, tam=17, contorno=PRETO)
    MP.mostrador(tela, PX0 + 50, y0 + 76, 30, teta)
    T = teta % 720
    for j, (rot, val) in enumerate((('VÁLVULA DE ADMISSÃO', 'adm'), ('VÁLVULA DE ESCAPE', 'esc'))):
        aberta = MP.abertura(T, val) > .3
        y = y0 + 114 + j * 30
        tela.texto(rot, PX0, y, ACO3, tam=9, contorno=PRETO)
        tela.ret(PX0, y + 13, 8, 8, VERDE if aberta else ACO0)
        if aberta: tela.ret(PX0 + 2, y + 15, 3, 3, BRANCO)
        tela.texto('ABERTA' if aberta else 'FECHADA', PX0 + 13, y + 10, VERDE if aberta else ACO2, tam=17, contorno=PRETO)
    tela.texto(f"VIRABREQUIM {int(T) % 720}°", PX0, y0 + 176, ACO3, tam=9, contorno=PRETO)


def rotulos_dutos(tela, ox=OX, oy=OY):
    if VERTICAL: return
    top = MP.TOPO_CAMARA
    y = oy + top - 21
    tela.texto('ADMISSÃO', ox - 59 - tela.largura_texto('ADMISSÃO', 9), y, MISTURA2, tam=9, contorno=PRETO)
    tela.texto('ENTRA', ox - 59 - tela.largura_texto('ENTRA', 9), y + 10, ACO3, tam=9, contorno=PRETO)
    tela.texto('ESCAPE', ox + 59, y, ACO3, tam=9, contorno=PRETO)
    tela.texto('SAI', ox + 59, y + 10, ACO3, tam=9, contorno=PRETO)


def seta(tela, x, y, para_baixo, cor, tam=6):
    for k in range(tam):
        w = (tam - k) * 2 - 1 if para_baixo else k * 2 + 1
        yy = y + k
        tela.ret(x - w // 2, yy, w, 1, cor)


def escurecer(tela, x, y, w, h):
    """Apaga metade dos pixels de uma área em xadrez (fora de foco, sem alfa)."""
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def engrenagem(tela, cx, cy, r, dentes, ang, cor, cor2):
    pts = []
    for k in range(dentes * 2):
        a = ang + k * math.pi / dentes
        rr = r + (2.5 if k % 2 == 0 else 0)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    poligono(tela, pts, cor)
    tela.disco(cx, cy, r * .55, cor2)
    tela.disco(cx, cy, r * .2, cor)


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

    def fundo_oficina(self, tela, t):
        """Fundo das cenas do motor: parede escura com grade de oficina."""
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24):
            tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24):
            tela.ret(0, y, W, 1, FUNDO2)

    def sons_do_ciclo(self, fx, fn, t0, t1, lento=1.0, ganho=1.0, chiado=True):
        """Sons de um cilindro seguindo teta=fn(t) entre t0 e t1 (relativos)."""
        g0 = self.t0
        for t in cruzamentos(fn, t0, t1, MP.FAISCA):
            fx.put(fx.faisca(), g0 + t, .5 * ganho, .05)
        for t in cruzamentos(fn, t0, t1, MP.FAISCA + 6):
            fx.put(fx.explosao(lento), g0 + t, .9 * ganho)
        for alvo in (180.0, 720.0):                     # válvula assentando
            for t in cruzamentos(fn, t0, t1, alvo):
                fx.put(fx.clique(3000, .02), g0 + t, .3 * ganho, -.3 if alvo == 180 else .3)
        if chiado:
            ini_a = cruzamentos(fn, t0, t1, 0.0); fim_a = cruzamentos(fn, t0, t1, 180.0)
            for a in ini_a:
                b = next((x for x in fim_a if x > a), None)
                if b and b - a > .05: fx.put(fx.chiado(b - a, 250, 1800), g0 + a, .55 * ganho, -.4)
            ini_e = cruzamentos(fn, t0, t1, 540.0); fim_e = cruzamentos(fn, t0, t1, 720.0)
            for a in ini_e:
                b = next((x for x in fim_e if x > a), None)
                if b and b - a > .05: fx.put(fx.chiado(b - a, 120, 900), g0 + a, .65 * ganho, .4)


# ============================================================ 0 gancho
class Gancho(Cena):
    def preparar(self):
        self.cil = MP.Cilindro(240, OY, 1.0, seed=3)

    def teta(self, t):
        if t < 6.0: return 3000 / 60 * 360 * t                   # 3.000 RPM de verdade
        u = (t - 6.0) / 6.0
        return 330 + 110 * suave(u)                                # câmera lenta na queima

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        rapido = t < 6.0
        self.cil.desenhar(tela, self.teta(t), t, borrao=6 if rapido else 0)
        if rapido:
            tela.texto('3.000 RPM', 330, 30, AMARELO, tam=17, contorno=PRETO)
        else:
            tela.texto('CÂMERA LENTA', 330, 30, CIANO, tam=17, contorno=PRETO)

    def sons(self, fx):
        # rápido: um pulso por ignição (25 por segundo) vira ronco
        for k in range(int(6.0 * 25)):
            fx.put(fx.pulso(), self.t0 + .02 + k / 25.0, .22)
        self.sons_do_ciclo(fx, self.teta, 6.0, 12.0, lento=3.0, ganho=1.0, chiado=False)


# ============================================================ 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        engrenagem(tela, 70, 205, 46, 14, t * .6, FUNDO2, FUNDO)
        engrenagem(tela, 148, 232, 30, 9, -t * .6 * 46 / 30 + .2, FUNDO2, FUNDO)
        engrenagem(tela, 420, 40, 38, 12, -t * .5, FUNDO2, FUNDO)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA", "O MOTOR DO CARRO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 13)]
            tela.texto(vis, W // 2 - larg // 2, 66 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            sub = "O CICLO DE 4 TEMPOS"
            tela.texto(sub, W // 2, 136, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            for k in range(4):
                x = W // 2 - 66 + k * 40
                cor = cor_tempo(k) if t > 2.0 + k * .35 else FUNDO2
                tela.ret(x, 160, 14, 14, cor)
                tela.texto(str(k + 1), x + 4, 163, PRETO, tam=9)


# ============================================================ 2 carro
class Carro(Cena):
    def preparar(self):
        self.ceu = np.random.default_rng(11)
        self.estrelas = [(int(self.ceu.integers(0, W)), int(self.ceu.integers(0, 90)), float(self.ceu.uniform(0, 6))) for _ in range(60)]
        self.bloco4 = [MP.Cilindro(138 + k * 68, 152, .6, seed=20 + k) for k in range(4)]
        self.desloc = [0, 540, 180, 360]          # cil 1, 2, 3, 4 (ordem 1-3-4-2)

    # ---------------------------------------------------- o carro de lado
    def _carro(self, tela, x0, y0, t, raiox=0.0, k=1.6):
        P = lambda pts: [(x0 + x * k, y0 + y * k) for x, y in pts]
        R = lambda x, y, w, h, c: tela.ret(int(x0 + x * k), int(y0 + y * k), max(1, int(round(w * k))), max(1, int(round(h * k))), c)
        corpo = [(4, 52), (4, 36), (10, 32), (40, 30), (58, 14), (104, 12), (124, 28), (156, 32), (164, 38), (164, 52)]
        for cx in (40, 132):
            tela.disco(x0 + cx * k, y0 + 52 * k, 16 * k, PRETO)
        if raiox < .5:
            poligono(tela, P(corpo), VERMELHO)
            poligono(tela, P([(6, 46), (164, 46), (164, 52), (6, 52)]), BRASA)
            R(12, 33, 140, 1, ROSA)
            poligono(tela, P([(62, 16), (84, 15), (84, 28), (64, 28)]), FUNDO3)
            poligono(tela, P([(88, 15), (102, 15), (116, 28), (88, 28)]), FUNDO3)
            R(66, 18, 10, 1, CIANO)
            R(90, 17, 8, 1, CIANO)
            R(84, 15, 4, 14, BRASA)                    # coluna
            R(160, 36, 4, 4, AMARELO)                  # farol
            R(4, 36, 3, 4, BRASA)                      # lanterna
            R(98, 34, 8, 1, PRETO)                     # maçaneta
        else:
            # raio-x: o carro vira contorno pontilhado e o motor aparece
            for (ax, ay), (bx, by) in zip(corpo, corpo[1:] + corpo[:1]):
                n = int(max(abs(bx - ax), abs(by - ay)))
                for i in range(0, n, 2):
                    u = i / max(1, n)
                    tela.ret(int(x0 + (ax + (bx - ax) * u) * k), int(y0 + (ay + (by - ay) * u) * k), 2, 2, CIANO)
            R(120, 30, 40, 18, FUNDO2)
            R(121, 31, 38, 1, ACO3)
            teta = t * 240
            for j in range(4):
                xx = 124 + j * 9
                R(xx, 33, 7, 13, ACO0)
                yp = MP.y_pino((teta - self.desloc[j]) % 720)
                h = int((yp - MP.Y_PMI) / (MP.Y_PMS - MP.Y_PMI) * 6)
                R(xx + 1, 40 - h, 5, 3, ACO3)
                kk, _, cor = MP.tempo_de(teta - self.desloc[j])
                if kk == 2: R(xx + 1, 34, 5, 6 - h, CHAMA1)
        for cx in (40, 132):
            wx, wy = x0 + cx * k, y0 + 52 * k
            tela.disco(wx, wy, 12 * k, FUNDO2)
            tela.disco(wx, wy, 10 * k, ACO0)
            tela.disco(wx, wy, 5 * k, ACO2)
            for j in range(5):
                a = -t * 9 + j * 1.2566
                tela.linha(wx, wy, wx + math.cos(a) * 9 * k, wy + math.sin(a) * 9 * k, ACO3)

    def _estrada(self, tela, t):
        # céu em faixas pontilhadas
        for k, (y0, y1, c1, c2) in enumerate(((0, 40, FUNDO, FUNDO), (40, 80, FUNDO, FUNDO2), (80, 120, FUNDO2, FUNDO2),
                                              (120, 150, FUNDO2, FUNDO3))):
            dither(tela, 0, y0, W, y1 - y0, c1, c2)
        for x, y, f in self.estrelas:
            if math.sin(t * 2 + f) > -.3: tela.px(x, y, BRANCO if f > 4 else ACO3)
        tela.disco(400, 38, 13, CERAMICA)
        tela.disco(395, 35, 3, ACO4)
        # montanhas distantes (devagar) e morros perto (mais rápido)
        for camada, (vel, alt, cor, base) in enumerate(((8, 34, FUNDO3, 150), (30, 18, TRACO, 160))):
            pts = [(0, PALCO_H)]
            for x in range(0, W + 20, 10):
                xx = x + (t * vel) % 20
                y = base - alt * (.5 + .5 * math.sin((x + t * vel) * .021 + camada * 2) * math.sin((x + t * vel) * .007))
                pts.append((x - (t * vel) % 10, y))
            pts.append((W, PALCO_H))
            poligono(tela, pts, cor)
        # estrada
        dither(tela, 0, 168, W, PALCO_H - 168, ACO0, FUNDO3)
        tela.ret(0, 168, W, 1, ACO2)
        for k in range(-1, 12):
            x = k * 48 - (t * 120) % 48
            tela.ret(int(x), 188, 24, 2, AMARELO)
        for k in range(-1, 8):
            x = k * 80 - (t * 60) % 80
            tela.ret(int(x), 156, 2, 12, ACO1)

    def desenhar(self, tela, t, tg):
        if t < 14.0:
            self._estrada(tela, t)
            raiox = 1.0 if t >= 8.0 else 0.0
            pulo = int(math.sin(t * 7) > .9)
            self._carro(tela, 106, 85 - pulo, t, raiox)
            # fumaça do escapamento
            for k in range(4):
                u = (t * 1.5 + k / 4) % 1.0
                tela.disco(110 - u * 40, 160 - u * 10, 1 + u * 4, GAS if u < .6 else GAS2)
            if raiox:
                xm = 106 + int(140 * 1.6)
                tela.texto('MOTOR', xm - tela.largura_texto('MOTOR', 17) // 2, 52, CIANO, tam=17, contorno=PRETO)
                tela.linha(xm, 68, xm, 132, CIANO)
        else:
            self.fundo_oficina(tela, t)
            teta = (t - 14) * 240
            foco = t >= 19.0
            for k, c in enumerate(self.bloco4):
                c.desenhar(tela, teta - self.desloc[k], t)
                cor = BRANCO
                tela.texto(str(k + 1), c.ox - 3, 180, AMARELO if (foco and k == 0) else cor, tam=17, contorno=PRETO)
                if foco and k > 0:
                    escurecer(tela, c.ox - 34, 0, 68, PALCO_H)
            if foco:
                u = (t - 19) * 3
                if int(u) % 2 == 0:
                    tela.ret_vazado(self.bloco4[0].ox - 36, 52, 72, 124, AMARELO)

    def sons(self, fx):
        # motor em marcha lenta ao fundo enquanto o carro anda (pulsos suaves)
        for k in range(int(14 * 27)):
            fx.put(fx.pulso(), self.t0 + k / 27.0, .12)


# ============================================================ 3 peças
PECAS = [('cylinder', 'CILINDRO', (37, -66)), ('piston', 'PISTÃO', (28, -60)), ('rod', 'BIELA', (6, -30)),
         ('crankshaft', 'VIRABREQUIM', (14, 4)), ('valves', 'VÁLVULAS', (22, -102)), ('cams', 'COMANDO', (20, -150)),
         ('spark', 'VELA', (3, -140))]


class Pecas(Cena):
    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=4)
        self.cil.gases = False
        self.slot = self.dur / len(PECAS)

    def teta(self, t):
        t_gira = 3 * self.slot + 2.0
        return 90.0 if t < t_gira else 90.0 + (t - t_gira) * 60.0

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        k_atual = min(len(PECAS) - 1, int(t / self.slot))
        vis = set()
        desl = {}
        for k, (nome, rot, ancora) in enumerate(PECAS):
            tk = k * self.slot
            if t >= tk:
                vis.add(nome)
                u = (t - tk) / .55
                if u < 1:
                    # cai de cima e quica uma vez (pouso no tempo 1 do compasso)
                    y = -150 * (1 - u) ** 2 if u < .75 else -6 * math.sin((u - .75) / .25 * math.pi)
                    desl[nome] = (0, y)
        self.cil.pecas = vis
        self.cil.desenhar(tela, self.teta(t), t, deslocar=desl, )
        # lista das peças à direita: a atual em amarelo, ligada à peça por um fio
        for k, (nome, rot, ancora) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 14 + k * 22
            atual = k == k_atual
            tela.texto(rot, PX0, y, AMARELO if atual else ACO2, tam=17, contorno=PRETO)
            if atual and t - k * self.slot > .55:
                ax, ay = OX + ancora[0], OY + ancora[1]
                if nome == 'piston': ay = OY - MP.y_pino(self.teta(t)) - 2
                tela.linha(PX0 - 4, y + 7, ax + 8, ay, AMARELO)
                tela.disco(ax + 8, ay, 1.6, AMARELO)
                tela.ret(PX0 - 6, y + 6, 3, 3, AMARELO)
        if k_atual == 4:
            tela.texto('MUITOS MOTORES TÊM 4.', PX0, 176, ACO3, tam=9, contorno=PRETO)
            tela.texto('MOSTRAMOS 2 PARA', PX0, 186, ACO3, tam=9, contorno=PRETO)
            tela.texto('FICAR MAIS CLARO.', PX0, 196, ACO3, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(len(PECAS)):
            t = self.t0 + k * self.slot + .41
            fx.put(fx.clique(1800, .05), t, .45)
            fx.put(fx.explosao(.5), t, .25)


# ============================================================ 4-7 os quatro tempos
class Tempo(Cena):
    """Um tempo em câmera lenta: cartão de 3 s, depois o pistão percorre o
    tempo dele até 30 s, parado até 36 s."""
    faixa = (0.0, 180.0)
    marcos = None                 # [(t, teta)] para curvas não lineares

    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=5)

    def teta(self, t):
        if self.marcos:
            ts = [m[0] for m in self.marcos]; th = [m[1] for m in self.marcos]
            if t <= ts[0]: return th[0]
            for (a, x), (b, y) in zip(self.marcos, self.marcos[1:]):
                if t <= b: return x + (y - x) * suave((t - a) / (b - a))
            return th[-1]
        a, b = self.faixa
        return a + (b - a) * suave((t - 2.0) / 18.0)

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        th = self.teta(t)
        self.cil.desenhar(tela, th, t)
        rotulos_dutos(tela)
        painel_ciclo(tela, th)
        # seta do sentido do pistão
        a = math.radians(th)
        desce = math.sin(a) > 0 if (th % 360) not in (0, 180) else False
        yseta = OY - MP.y_pino(th) + 16
        if 2.0 < t < 20.0:
            seta(tela, OX + 44, yseta - 4, desce, AMARELO, 5)
        if t < 2.0 and not VERTICAL:
            k, _, cor = MP.tempo_de(self.faixa[0] + 1)
            nome = NOMES[k]
            u = ease(t / .4)
            larg = tela.largura_texto(nome, 26)
            x = int(OX - larg // 2 + (1 - u) * -300)
            painel(tela, x - 8, 8, larg + 16, 34, borda=cor)
            tela.texto(nome, x, 14, cor, tam=26, contorno=PRETO)

    def sons(self, fx):
        lento = 3.0
        self.sons_do_ciclo(fx, self.teta, 0.0, self.dur, lento=lento)


class Admissao(Tempo):
    faixa = (0.0, 180.0)


class Compressao(Tempo):
    faixa = (180.0, 335.0)        # para logo antes da faísca: ela é do próximo capítulo


class Potencia(Tempo):
    faixa = (360.0, 540.0)
    marcos = [(2.0, 335.0), (8.0, 368.0), (20.0, 540.0)]

    def desenhar(self, tela, t, tg):
        super().desenhar(tela, t, tg)
        th = self.teta(t)
        if 360 < th < 540 and t > 8 and not VERTICAL:
            tela.texto('EMPURRA!', OX - 146, OY - MP.y_pino(th) - 14, AMARELO, tam=17, contorno=PRETO)


class Escape(Tempo):
    faixa = (540.0, 720.0)


# ============================================================ 8 ciclo completo
class Ciclo(Cena):
    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=6)

    def teta(self, t):
        return 720.0 * suave(min(1, max(0, (t - .5) / 11.0)))

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        th = self.teta(t)
        self.cil.desenhar(tela, th, t)
        rotulos_dutos(tela)
        painel_ciclo(tela, th)
        voltas = th / 360.0
        tela.texto(f"VOLTAS: {voltas:.1f}".replace('.', ','), PX0, 196, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0, self.dur, lento=1.5)


# ============================================================ 9 na batida
class Batidas(Cena):
    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=7)
        self.spb = 60.0 / self.c['bpm']

    def teta(self, t):
        return 180.0 * t / self.spb                     # um tempo do motor por batida

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        th = self.teta(t)
        self.cil.desenhar(tela, th, t)
        rotulos_dutos(tela)
        k, _, cor = MP.tempo_de(th)
        nome = NOMES[k]
        tela.texto("BATIDA", PX0, 12, ACO3, tam=17, contorno=PRETO)
        for j in range(4):
            x = PX0 + j * 40
            c = cor_tempo(j)
            aceso = j == k
            tela.ret(x, 34, 34, 34, c if aceso else FUNDO2)
            tela.ret_vazado(x, 34, 34, 34, c)
            tela.texto(str(j + 1), x + 11, 44, PRETO if aceso else c, tam=17)
        tela.texto(nome, PX0, 78, cor, tam=17, contorno=PRETO)
        MP.mostrador(tela, PX0 + 50, 140, 30, th)
        tela.texto("60 RPM", PX0, 182, AMARELO, tam=17, contorno=PRETO)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0, self.dur, lento=.8, ganho=.8)


# ============================================================ 10 acelerando
class Rpm(Cena):
    MARCOS = [(0, 60), (1, 60), (5, 800), (11, 800), (15, 3000), (23, 3000), (27, 6000), (60, 6000)]

    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=8)
        ts = np.arange(0, self.dur + .01, .001)
        self.ts = ts
        self.rpm_v = np.array([self.rpm(t) for t in ts])
        self.th_v = np.concatenate([[0], np.cumsum(self.rpm_v[:-1] / 60 * 360 * .001)])

    def rpm(self, t):
        for (a, x), (b, y) in zip(self.MARCOS, self.MARCOS[1:]):
            if t <= b:
                u = suave((t - a) / (b - a)) if b > a else 1
                return math.exp(math.log(x) + (math.log(y) - math.log(x)) * u)
        return self.MARCOS[-1][1]

    def teta(self, t):
        return float(np.interp(t, self.ts, self.th_v))

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        r = self.rpm(t)
        th = self.teta(t)
        borrao = 0 if r < 150 else 6
        self.cil.desenhar(tela, th, t, borrao=borrao)
        # conta-giros
        cx, cy, R = PX0 + 80, 92, 62
        for k in range(0, 71):
            a = math.radians(210 - k * 240 / 70)
            r0 = R - (8 if k % 10 == 0 else 4)
            cor = VERMELHO if k >= 60 else ACO2
            tela.linha(cx + math.cos(a) * r0, cy - math.sin(a) * r0, cx + math.cos(a) * R, cy - math.sin(a) * R, cor)
        for k in range(0, 8):
            a = math.radians(210 - k * 10 * 240 / 70)
            tela.texto(str(k), cx + math.cos(a) * (R - 16) - 2, cy - math.sin(a) * (R - 16) - 3, ACO3, tam=9)
        a = math.radians(210 - min(r, 7000) / 100 * 240 / 70)
        tela.linha(cx, cy, cx + math.cos(a) * (R - 6), cy - math.sin(a) * (R - 6), LARANJA)
        tela.disco(cx, cy, 3, LARANJA)
        tela.texto("X1000", cx - 14, cy + 18, ACO2, tam=9)
        s = f"{milhar(round(r / 10) * 10)} RPM"
        tela.texto(s, cx - tela.largura_texto(s, 17) // 2, 160, AMARELO, tam=17, contorno=PRETO)
        fps_ = r / 120.0
        s2 = f"{fps_:.0f} QUEIMAS POR SEGUNDO" if fps_ >= 1.5 else f"1 QUEIMA A CADA {1 / fps_:.0f} S"
        tela.texto(s2, cx - tela.largura_texto(s2, 9) // 2, 182, BRANCO, tam=9, contorno=PRETO)
        tela.texto("(UM CILINDRO)", cx - tela.largura_texto("(UM CILINDRO)", 9) // 2, 193, ACO3, tam=9)

    def sons(self, fx):
        ts, th = self.ts, self.th_v
        k = np.floor((th - MP.FAISCA) / 720)
        idx = np.nonzero(np.diff(k) > 0)[0]
        for i in idx:
            t = float(ts[i + 1])
            r = self.rpm(t)
            if r < 150:
                fx.put(fx.explosao(1.0), self.t0 + t, .6)
            else:
                fx.put(fx.pulso(), self.t0 + t, .26)


# ============================================================ 11 vários cilindros
class Cilindros(Cena):
    NOTAS = {0: 72, 2: 76, 3: 79, 1: 84}        # cil 1, 3, 4, 2 -> dó, mi, sol, dó

    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=9)
        self.bloco4 = [MP.Cilindro(118 + k * 68, 152, .6, seed=30 + k) for k in range(4)]
        self.desloc = [0, 540, 180, 360]

    def teta(self, t):
        if t < 15.0: return 240.0 * t                   # 40 RPM: um tempo por batida da trilha (80 BPM)
        return 160.0 + 240.0 * (t - 15.0)                # faísca do cilindro 1 cai numa batida (15 s = 20 batidas)

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        th = self.teta(t)
        if t < 15.0:
            vol = 0.0 if t < 7.5 else min(1.0, (t - 7.5) / 1.2)
            self.cil.desenhar(tela, th, t, volante=vol)
            rotulos_dutos(tela)
            k, nome, cor = MP.tempo_de(th)
            empurra = k == 2
            tela.texto("EMPURRANDO" if empurra else "NO EMBALO", PX0, 20, AMARELO if empurra else ACO2, tam=17, contorno=PRETO)
            for j in range(4):
                tela.ret(PX0 + j * 30, 44, 24, 10, cor_tempo(j) if j == k else FUNDO2)
            tela.ret(PX0 + 60, 56, 24, 2, AMARELO)
            tela.texto("SÓ ESTE", PX0 + 58, 62, AMARELO, tam=9, contorno=PRETO)
            if vol > 0:
                tela.texto("VOLANTE", OX - 78, OY + 26, CIANO, tam=9, contorno=PRETO)
            MP.mostrador(tela, PX0 + 50, 120, 30, th)
        else:
            ativo = None
            for k, c in enumerate(self.bloco4):
                tk = th - self.desloc[k]
                c.desenhar(tela, tk, t)
                kk = MP.tempo_de(tk)[0]
                if kk == 2: ativo = k
                tela.texto(str(k + 1), c.ox - 3, 180, AMARELO if kk == 2 else BRANCO, tam=17, contorno=PRETO)
            tela.texto("ORDEM", 388, 20, BRANCO, tam=17, contorno=PRETO)
            tela.texto("DE QUEIMA", 388, 38, BRANCO, tam=9, contorno=PRETO)
            for j, cil in enumerate((1, 3, 4, 2)):
                y = 64 + j * 26
                aceso = ativo == cil - 1
                tela.ret(388, y, 20, 20, AMARELO if aceso else FUNDO2)
                tela.texto(str(cil), 394, y + 3, PRETO if aceso else ACO2, tam=17)
                if aceso: tela.texto("FORÇA", 414, y + 6, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0.0, 15.0, lento=1.0, ganho=.5)
        for k in range(4):
            fn = lambda t, k=k: self.teta(t) - self.desloc[k]
            for t in cruzamentos(fn, 15.0, self.dur, MP.FAISCA):
                if t < 15.0: continue
                fx.put(fx.faisca(), self.t0 + t, .2)
                fx.put(fx.explosao(.7), self.t0 + t + .015, .22)
                if t >= 31.5:
                    fx.put(fx.sino(self.NOTAS[k]), self.t0 + t, .5, -.45 + .3 * k)


# ============================================================ 12 energia
class Energia(Cena):
    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        x0, y0, lado = 34, 20, 16
        grupos = ([VERDE] * 20 + [VERMELHO] * 70 + [ACO1] * 10)
        for i in range(100):
            if t < .5 + i * .025: continue
            cx, cy = x0 + (i % 10) * lado, y0 + (i // 10) * lado
            cor = AMARELO
            if t > 8.0 + (i % 10) * .05 + (i // 10) * .12:
                cor = grupos[i]
            tela.ret(cx, cy, lado - 3, lado - 3, cor)
            tela.px(cx, cy, BRANCO if cor == AMARELO else ACO4)
            if cor == VERMELHO and t > 16.0:
                u = (t * .8 + i * .37) % 1.0
                if (i * 7) % 3 == 0:
                    tela.px(cx + 6 + math.sin(t * 5 + i) * 2, cy - u * 14, CHAMA1 if u < .5 else BRASA)
        if t > 3.0 and t <= 8.0:
            tela.texto("100 UNIDADES DE", 220, 40, AMARELO, tam=17, contorno=PRETO)
            tela.texto("ENERGIA", 220, 60, AMARELO, tam=17, contorno=PRETO)
        if t > 8.5:
            itens = (("MOVE O CARRO", "16-25%", VERDE), ("PERDAS NO MOTOR", "68-72%", VERMELHO), ("OUTRAS PERDAS", "O RESTO", ACO1))
            for j, (a, b, cor) in enumerate(itens):
                if t < 8.5 + j * 1.2: continue
                y = 30 + j * 44
                tela.ret(220, y + 2, 12, 12, cor)
                tela.texto(a, 240, y, BRANCO, tam=17, contorno=PRETO)
                tela.texto(b, 240, y + 18, cor, tam=17, contorno=PRETO)
            tela.texto("USO MISTO: CIDADE + ESTRADA", 220, 170, ACO3, tam=9)
            tela.texto("FONTE: FUELECONOMY.GOV (EUA)", 220, 181, ACO3, tam=9)

    def sons(self, fx):
        for i in range(0, 100, 5):
            fx.put(fx.blip(72 + (i // 10), .05), self.t0 + .5 + i * .025, .08)


# ============================================================ 13 resumo
class Resumo(Cena):
    def preparar(self):
        self.mini = [MP.Cilindro(90 + k * 100, 150, .45, seed=40 + k) for k in range(4)]
        self.spb = 60.0 / self.c['bpm']

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        if t < 9.0:
            # motor de 1876: horizontal, com um volante enorme (silhueta)
            cx, cy = 300, 110
            a = t * 2.0
            tela.disco(cx, cy, 52, ACO0); tela.disco(cx, cy, 46, FUNDO)
            for k in range(6):
                b = a + k * math.pi / 3
                tela.linha(cx, cy, cx + math.cos(b) * 46, cy + math.sin(b) * 46, ACO1)
            tela.disco(cx, cy, 6, ACO2)
            tela.ret(110, 92, 110, 36, ACO1)
            tela.ret(110, 92, 110, 2, ACO3)
            for k in range(5): tela.ret(120 + k * 20, 92, 3, 36, ACO0)
            px = 220 + 18 * math.cos(a)
            linha_grossa(tela, px - 60, cy, cx + math.cos(a) * 30, cy + math.sin(a) * 30, 4, ACO3)
            tela.ret(100, 128, 220, 6, ACO0)
            tela.texto("1876", 60, 30, AMARELO, tam=26, contorno=PRETO)
            tela.texto("O MOTOR DE OTTO", 60, 58, BRANCO, tam=17, contorno=PRETO)
        else:
            medio = (90, 270, 400, 630)
            for k, c in enumerate(self.mini):
                th = medio[k] + 40 * math.sin(t * 2.0 + k)
                c.desenhar(tela, th, t)
                t_k = 9.2 + k * self.spb
                if t >= t_k:
                    u = min(1.0, (t - t_k) / .2)
                    tela.texto(str(k + 1), c.ox - 5, 170 - int((1 - u) * 6), cor_tempo(k), tam=17, contorno=PRETO)
                    tela.texto(NOMES[k], c.ox - tela.largura_texto(NOMES[k], 9) // 2, 190, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k, m in enumerate((72, 74, 79, 76)):
            fx.put(fx.blip(m, .14), self.t0 + 9.2 + k * self.spb, .3)


# ============================================================ 14 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))
        self.cil = MP.Cilindro(240, 200, .5, seed=50)

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            self.fundo_oficina(tela, t)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, tam=9, centro=True, contorno=PRETO)
            self.cil.desenhar(tela, t * 240, t)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


# ============================================================ extra: o injetor
class Injetor(Cena):
    """A peça que faltou na montagem. 0-7,6 s: o injetor cai no duto de
    admissão do cilindro (a lista de peças ganha a 8ª linha); depois o
    close-up em corte: a bobina puxa a agulha e o bico solta o spray, um
    jato a cada 2 batidas da trilha. Painel: sinal elétrico, agulha, jatos
    e, no fim, a conta 14,7 g de ar para 1 g de gasolina (F16)."""
    T_ZOOM = 7.6
    CX, Y0 = 120, 18
    ABERTO = .36

    def preparar(self):
        self.cil = MP.Cilindro(OX, OY, 1.0, seed=12)
        self.spb = 60.0 / self.c['bpm']
        self.jatos = []
        t = self.T_ZOOM + 1.0 * self.spb                 # 8,35 s: cai numa batida
        t = math.ceil(t / self.spb) * self.spb
        while t < self.dur - .5:
            self.jatos.append(t)
            t += 2 * self.spb
        self.gotas = [(a + j * self.ABERTO / 26, k * 26 + j) for k, a in enumerate(self.jatos) for j in range(26)]

    def teta(self, t):
        return 240.0 * t

    def aberto(self, t):
        return any(a <= t < a + self.ABERTO for a in self.jatos)

    def n_jatos(self, t):
        return sum(1 for a in self.jatos if a <= t)

    # ------------------------------------------------ 1: no cilindro
    def _cilindro(self, tela, t):
        self.fundo_oficina(tela, t)
        th = self.teta(t)
        self.cil.desenhar(tela, th, t)
        rotulos_dutos(tela)
        u = (t - .4) / .55
        if u < 0: dy = -200
        elif u < 1: dy = -150 * (1 - u) ** 2 if u < .75 else -6 * math.sin((u - .75) / .25 * math.pi)
        else: dy = 0
        T = th % 720
        if u >= 1 and 20 < T < 170:
            EX.spray_mini(tela, self.cil, t, 1.0)
        ax, ay = EX.injetor_mini(tela, self.cil, dy, aceso=u >= 1 and 20 < T < 170)
        for k, (nome, rot, ancora) in enumerate(PECAS):
            tela.texto(rot, PX0, 14 + k * 22, ACO2, tam=17, contorno=PRETO)
        if t > .4:
            y = 14 + 7 * 22
            tela.texto('INJETOR', PX0, y, AMARELO, tam=17, contorno=PRETO)
            if u >= 1:
                tx, ty = OX - 42, OY + MP.TOPO_CAMARA - 50
                tela.linha(PX0 - 4, y + 7, tx + 6, ty, AMARELO)
                tela.disco(tx + 6, ty, 1.6, AMARELO)
                tela.ret(PX0 - 6, y + 6, 3, 3, AMARELO)
        # moldura do zoom saindo do injetor
        if t > self.T_ZOOM - .5:
            z = suave((t - (self.T_ZOOM - .5)) / .5)
            x0, y0 = OX - 50, OY + MP.TOPO_CAMARA - 56
            x1, y1 = x0 + (0 - x0) * z, y0 + (0 - y0) * z
            w = 12 + (W - 12) * z; h = 40 + (PALCO_H - 40) * z
            tela.ret_vazado(int(x1), int(y1), int(w), int(h), AMARELO)

    # ------------------------------------------------ 2: close-up
    def _duto(self, tela, t):
        y0, y1 = 108, 172
        dither(tela, 0, y0 + 5, 296, y1 - y0 - 10, FUNDO, FUNDO2)
        for yy, cor in ((y0, ACO1), (y1 - 5, ACO1)):
            tela.ret(0, yy - 1, 296, 7, PRETO)
            tela.ret(0, yy, 296, 5, cor)
            tela.ret(0, yy, 296, 1, ACO3)
        for k in range(24):                                   # ar andando para a direita
            u = (hsh(k) + t * .32) % 1.0
            x = int(u * 300) - 10
            y = int(y0 + 10 + hsh(k, 2) * (y1 - y0 - 22))
            tela.ret(x, y, 5, 1, ACO3 if k % 3 else CIANO)
        tela.texto('AR', 8, 128, CIANO, tam=17, contorno=PRETO)
        seta(tela, 36, 136, False, CIANO, 1)
        for k in range(3):
            tela.ret(34 + k * 2, 136, 1, 1, CIANO)
        # saída: a válvula de admissão, no fim do duto
        tela.texto('PARA A', 248, 140, ACO3, tam=9, contorno=PRETO)
        tela.texto('VÁLVULA', 244, 150, ACO3, tam=9, contorno=PRETO)
        for k in range(4):
            tela.ret(286 + k, 141 + k, 1, 12 - 2 * k, AMARELO)

    def _closeup(self, tela, t):
        self.fundo_oficina(tela, t)
        self._duto(tela, t)
        ab = self.aberto(t)
        energia = 1.0 if ab else 0.0
        an = EX.injetor_grande(tela, self.CX, self.Y0, 1.0 if ab else 0.0, energia, t)
        bx, by = an['bico']
        for x, y, a, i in EX.spray(tela, bx, by + 2, self.gotas, t, vento=95.0):
            if x > 292: continue
            y = min(y, 164)
            cor = CHAMA0 if a < .4 else (AMARELO if i % 3 else MISTURA)
            tela.px(x, y, cor)
            if a < .25 and i % 4 == 0: tela.px(x + 1, y, CHAMA0)
        # fio do sinal elétrico até o painel
        cxn, cyn = an['conector']
        pts = [(cxn + 1, cyn), (292, cyn), (292, 57), (PX0 - 2, 57)]
        EX.fio(tela, pts)
        for a in self.jatos:
            if a - .25 <= t < a:
                px_, py_ = EX.ponto_no_caminho(pts[::-1], (t - (a - .25)) / .25)
                tela.disco(px_, py_, 2, AMARELO)
        # rótulos
        rotulo(tela, 'COMBUSTÍVEL SOB PRESSÃO', 8, 4, an['tubo'][0], an['tubo'][1], ACO4, AMARELO)
        rotulo(tela, 'SOLENOIDE', 20, 48, an['bobina'][0], an['bobina'][1], BRANCO, AMARELO)
        rotulo(tela, 'AGULHA', 20, 70, self.CX - 2, an['agulha'][1], BRANCO, AMARELO)
        rotulo(tela, 'BICO', 40, 92, bx - 6, by - 4, BRANCO, AMARELO)
        tela.texto('SINAL ELÉTRICO', 166, cyn - 12, ACO4, tam=9, contorno=PRETO)
        if t > 8.4:
            rotulo(tela, 'SPRAY FINO', 176, 118, bx + 12, by + 14, AMARELO, AMARELO)
        # painel
        tela.texto('INJETOR', PX0, 8, AMARELO, tam=17, contorno=PRETO)
        tela.texto('SINAL ELÉTRICO', PX0, 32, ACO3, tam=9, contorno=PRETO)
        painel(tela, PX0, 42, 166, 32, borda=TRACO)
        for k in range(1, 6):
            tela.ret(PX0 + k * 28, 44, 1, 28, FUNDO2)
        prev = None
        for k in range(160):
            tt = t - (159 - k) * .02
            y = 48 if self.aberto(tt) else 67
            if prev is not None and prev != y:
                tela.ret(PX0 + 3 + k, 48, 1, 20, VERDE)
            tela.ret(PX0 + 3 + k, y, 1, 2, VERDE)
            prev = y
        tela.texto('AGULHA', PX0, 82, ACO3, tam=9, contorno=PRETO)
        tela.ret(PX0, 95, 8, 8, VERDE if ab else ACO0)
        if ab: tela.ret(PX0 + 2, 97, 3, 3, BRANCO)
        tela.texto('ABERTA' if ab else 'FECHADA', PX0 + 13, 92, VERDE if ab else ACO2, tam=17, contorno=PRETO)
        tela.texto('JATOS', PX0, 118, ACO3, tam=9, contorno=PRETO)
        tela.texto(str(self.n_jatos(t)), PX0, 128, AMARELO, tam=26, contorno=PRETO)
        if t >= 22.2:
            tela.texto('14,7 G DE AR', PX0, 160, CIANO, tam=9, contorno=PRETO)
            for j in range(15):
                if t < 22.4 + j * .12: break
                w = 7 if j == 14 else 9
                tela.ret(PX0 + j * 10, 171, w, 8, CIANO)
                tela.px(PX0 + j * 10, 171, BRANCO)
            if t > 22.4 + 15 * .12:
                tela.ret(PX0, 186, 9, 8, AMARELO)
                tela.px(PX0, 186, BRANCO)
                tela.texto('1 G DE GASOLINA', PX0 + 14, 187, AMARELO, tam=9, contorno=PRETO)

    def desenhar(self, tela, t, tg):
        if t < self.T_ZOOM: self._cilindro(tela, t)
        else: self._closeup(tela, t)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0.0, self.T_ZOOM - .3, lento=1.0, ganho=.45, chiado=False)
        fx.put(fx.clique(1800, .05), self.t0 + .4 + .41, .4)
        for a in self.jatos:
            fx.put(fx.clique(2600, .012), self.t0 + a, .22, -.2)
            fx.put(fx.chiado(self.ABERTO, 2500, 7000, ataque=.01), self.t0 + a, .1, -.1)
        for j in range(15):
            fx.put(EX.tique(fx, 1400 + j * 40), self.t0 + 22.4 + j * .12, .12)


# ============================================================ extra: a faísca
class Faisca(Cena):
    """De onde vem a faísca: bateria (12 V) -> bobina -> vela. A corrente
    enche o primário; a cada 2 batidas a chave corta e o secundário solta
    o pulso de alta tensão, que pula a folga da vela NA batida."""
    PERIODO_BATIDAS = 2

    def preparar(self):
        self.spb = 60.0 / self.c['bpm']
        self.per = self.PERIODO_BATIDAS * self.spb
        self.disparos = [k * self.per for k in range(1, int(self.dur / self.per) + 1) if k * self.per < self.dur - .2]
        self.P_PRIM = [(27, 134), (27, 50), (101, 50)]
        self.P_VOLTA = [(101, 118), (80, 118)]
        self.P_ALTA = [(208, 44), (232, 44), (232, 16), (262, 16), (262, 24)]

    def fase(self, t):
        """(carga 0..1, disparo 0..1, segundos desde o último disparo)."""
        ult = max([d for d in self.disparos if d <= t], default=None)
        dt = t - ult if ult is not None else 99.0
        ini = ult if ult is not None else 0.0
        carga = min(1.0, (t - ini - .12) / (self.per - .2)) if dt > .12 else 0.0
        if ult is None: carga = min(1.0, t / self.per)
        disparo = max(0.0, 1 - dt / .16)
        return max(0.0, carga), disparo, dt

    def volts(self, t):
        carga, disparo, dt = self.fase(t)
        if dt < .03: return 25000 * dt / .03
        if dt < .2: return 25000 * math.exp(-(dt - .03) / .05)
        return 0

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        carga, disparo, dt = self.fase(t)
        fechada = dt > .1
        # circuito do primário
        EX.fio(tela, self.P_PRIM)
        EX.fio(tela, self.P_VOLTA)
        EX.fio(tela, [(64, 118), (64, 134)])
        EX.fio(tela, self.P_ALTA, cor2=VERMELHO)
        (bmx, bmy), (bnx, bny) = EX.bateria(tela, 14, 140)
        an = EX.bobina(tela, 106, 34, 96, 100, carga, disparo, t)
        # chave (a central corta a corrente)
        ang = 0.0 if fechada else -.7
        tela.disco(64, 118, 2.5, ACO3)
        linha_grossa(tela, 64, 118, 64 + math.cos(ang) * 17, 118 + math.sin(ang) * 17, 3, LATAO)
        tela.disco(81, 118, 1.5, ACO4)
        # corrente andando no primário (enquanto a chave está fechada)
        if fechada:
            laco = self.P_PRIM + [(101, 118), (64, 118), (64, 134)]
            for k in range(10):
                x, y = EX.ponto_no_caminho(laco, k / 10 + t * .35)
                if 101 < x < 102 and 50 < y < 118: continue
                tela.ret(int(x) - 1, int(y) - 1, 3, 3, AMARELO)
        # pulso de alta tensão correndo no fio até a vela
        if dt < .07:
            for k in range(3):
                x, y = EX.ponto_no_caminho(self.P_ALTA, min(1.0, dt / .06) - k * .05)
                tela.disco(x, y, 2.5 - k * .6, BRANCO if k == 0 else CIANO)
        va = EX.vela_grande(tela, 262, 24, disparo if dt < .16 else 0.0, t)
        # rótulos
        tela.texto('BOBINA', 154, 20, BRANCO, tam=17, centro=True, contorno=PRETO)
        tela.texto('ALTA TENSÃO', 208, 4, VERMELHO, tam=9, contorno=PRETO)
        rotulo(tela, 'VELA', 218, 72, 249, 84, BRANCO, AMARELO)
        if not VERTICAL: rotulo(tela, 'FOLGA', 232, 166, va['folga'][0] + 2, va['folga'][1] + 2, AMARELO, AMARELO)
        rotulo(tela, 'POUCAS VOLTAS', 108, 140, 110, 110, BRANCO, AMARELO)
        rotulo(tela, 'MILHARES DE VOLTAS', 140, 152, 196, 126, BRANCO, AMARELO)
        if not VERTICAL:
            rotulo(tela, 'CORTA A CORRENTE', 84, 164, 72, 120, ACO4, AMARELO)
            tela.texto('BATERIA', 18, 192, BRANCO, tam=9, contorno=PRETO)
        if VERTICAL: return
        # painel: a tensão subindo, faíscas contadas
        v = self.volts(t)
        tela.texto('TENSÃO', PX0, 8, BRANCO, tam=17, contorno=PRETO)
        bx, by, bw = PX0, 32, 164
        painel(tela, bx, by, bw, 12, borda=TRACO)
        lx = lambda vv: bx + 2 + int(min(1.0, math.log10(max(vv, 1)) / 5) * (bw - 4))
        tela.ret(lx(12000), by + 2, lx(25000) - lx(12000), 8, FUNDO3)
        if v > 1:
            tela.ret(bx + 2, by + 3, lx(v) - bx - 2, 6, CIANO if v < 12000 else AMARELO)
        else:
            tela.ret(bx + 2, by + 3, lx(12) - bx - 2, 6, ACO2)
        for vv, txt in ((12, '12 V'), (12000, '12.000')):
            tela.ret(lx(vv), by + 12, 1, 3, ACO3)
        tela.texto('12 V', lx(12) - 10, by + 16, ACO3, tam=9, contorno=PRETO)
        tela.texto('12.000 A 25.000', lx(12000) - 62, by + 16, ACO3, tam=9, contorno=PRETO)
        tela.texto('BATERIA: 12 V', PX0, 64, ACO3, tam=9, contorno=PRETO)
        tela.texto('NA VELA:', PX0, 78, ACO3, tam=9, contorno=PRETO)
        s = f"{milhar(round(v / 100) * 100)} V" if v > 1 else '0 V'
        tela.texto(s, PX0, 90, AMARELO if v > 1 else ACO2, tam=26, contorno=PRETO)
        n = sum(1 for d in self.disparos if d <= t)
        tela.texto('FAÍSCAS', PX0, 126, ACO3, tam=9, contorno=PRETO)
        tela.texto(str(n), PX0, 136, AMARELO, tam=26, contorno=PRETO)
        if t >= 14.6:
            tela.texto('PRIMÁRIO: POUCAS VOLTAS', PX0, 168, LATAO, tam=9, contorno=PRETO)
            tela.texto('SECUNDÁRIO: MILHARES', PX0, 179, AMARELO, tam=9, contorno=PRETO)
        if t >= 22.2:
            tela.texto('FOLGA: 0,6 A 1,8 MM', PX0, 192, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for d in self.disparos:
            fx.put(fx.clique(3200, .01), self.t0 + d - .02, .12, -.3)
            fx.put(fx.faisca(), self.t0 + d, .32, .25)


# ============================================================ extra: o calor
class Calor(Cena):
    """Por que o motor não derrete. 0-8,3 s: a bomba parada e o ponteiro
    subindo para PERIGO; depois a bomba gira, a água leva o calor até o
    radiador e o ponteiro volta ao normal. A gota de água marcada é a
    protagonista: o painel conta as voltas dela. 24,3 s: o óleo."""
    LIGA = 8.3
    VEL = 55.0
    T_OLEO = 24.3
    OX2 = 118
    LACO = [(149, 128), (149, 76), (196, 76), (196, 49), (226, 49), (226, 159), (190, 159), (190, 128), (149, 128)]
    H1 = [(156, 76), (196, 76), (196, 49), (214, 49)]
    H2 = [(214, 159), (190, 159), (190, 128), (156, 128)]

    def preparar(self):
        self.cil = MP.Cilindro(self.OX2, OY, 1.0, seed=13)
        self.L = EX.comprimento(self.LACO)

    def teta(self, t):
        return 240.0 * t

    def andou(self, t):
        if t < self.LIGA: return 0.0
        if t < self.LIGA + 1: return self.VEL * (t - self.LIGA) ** 2 / 2
        return self.VEL / 2 + self.VEL * (t - self.LIGA - 1)

    def temp(self, t):
        T8 = .45 + .5 * suave(self.LIGA / self.LIGA)
        if t < self.LIGA: return .45 + .5 * (t / self.LIGA) ** 1.2
        return .5 + (T8 - .5) * math.exp(-(t - self.LIGA) / 2.2) + .01 * math.sin(t * 4)

    def voltas(self, t):
        return int(self.andou(t) / self.L)

    def _mangueira(self, tela, pts):
        for (a, b), (c, d) in zip(pts, pts[1:]):
            linha_grossa(tela, a, b, c, d, 8, PRETO)
        for (a, b), (c, d) in zip(pts, pts[1:]):
            linha_grossa(tela, a, b, c, d, 6, TRACO)
        for (a, b), (c, d) in zip(pts, pts[1:]):
            if b == d: tela.linha(a, b - 2, c, d - 2, FUNDO3)       # brilho em cima da borracha

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        ox, oy = self.OX2, OY
        th = self.teta(t)
        Tm = self.temp(t)
        self.cil.desenhar(tela, th, t)
        # metal esquentando: pontos de brasa nas paredes
        if Tm > .7:
            dens = (Tm - .7) / .3
            top = MP.TOPO_CAMARA
            for k in range(60):
                if hsh(k, 3) > dens: continue
                lado = -1 if k % 2 else 1
                x = ox + lado * (30 + hsh(k, 4) * 10)
                y = oy + top + hsh(k, 5) * (-30 - top)
                if int(t * 6 + k) % 3: tela.px(x, y, BRASA if k % 3 else CHAMA2)
        # óleo: película entre pistão e cilindro + jato embaixo do pistão
        if t >= self.T_OLEO:
            yp = -MP.y_pino(th)
            topo = oy + yp - 12
            for yy in range(int(oy - MP.Y_PMS - 12), oy - 30):
                c = LATAO if (topo - 2 <= yy <= topo + 26) else (OLEO1 if yy % 2 else None)
                if c is not None:
                    tela.px(ox - 29, yy, c); tela.px(ox + 28, yy, c)
            jx, jy = ox + 24, oy - 24
            tela.ret(jx - 2, jy, 5, 6, ACO3)
            alvo_y = oy + yp + 12
            for k in range(10):
                u = (k / 10 + t * 2.2) % 1.0
                x = jx + (ox + 10 - jx) * u
                y = jy + (alvo_y - jy) * u
                tela.ret(int(x), int(y), 2, 2, LATAO if k % 2 else OLEO1)
        # mangueiras, bomba e radiador
        self._mangueira(tela, self.H1)
        self._mangueira(tela, self.H2)
        flui = self.andou(t) > 0
        an = EX.radiador(tela, 214, 44, 48, 120, .9 if flui else .2, 1.0 if flui else 0.0, t)
        EX.bomba(tela, 190, 143, 7, self.andou(t) / 6.0)
        if flui:
            for k in range(36):
                d = (self.andou(t) + k * self.L / 36) % self.L
                x, y = EX.ponto_no_caminho(self.LACO, d / self.L)
                if x < 156 or 212 <= x <= 264: continue
                quente = d < EX.comprimento(self.LACO[:5])
                tela.ret(int(x) - 1, int(y) - 1, 2, 2, LARANJA if quente else AGUA1)
            # ar atravessando o radiador
            for k in range(8):
                u = (t * .9 + k / 8) % 1.0
                yy = 56 + k * 13
                tela.ret(int(262 + u * 30), yy, 4, 1, CIANO)
        # a protagonista: uma gota de água marcada
        d0 = self.andou(t) % self.L
        gx, gy = EX.ponto_no_caminho(self.LACO, d0 / self.L)
        quente = d0 < EX.comprimento(self.LACO[:5])
        tela.disco(gx, gy, 3.2, BRANCO)
        tela.disco(gx, gy, 2, LARANJA if quente and flui else AGUA1)
        # rótulos
        rotulo(tela, 'RADIADOR', 210, 30, 238, 44, BRANCO, AMARELO)
        rotulo(tela, 'BOMBA', 200, 172, 192, 150, BRANCO, AMARELO)
        rotulo(tela, 'CAMISA', 20, 86, ox - 33, oy - 72, AGUA1, AMARELO)
        tela.texto("D'ÁGUA", 20, 96, AGUA1, tam=9, contorno=PRETO)
        if t < self.LIGA:
            if int(t * 3) % 2 == 0:
                tela.texto('BOMBA PARADA:', 8, 140, VERMELHO, tam=9, contorno=PRETO)
                tela.texto('A ÁGUA NÃO ANDA', 8, 150, VERMELHO, tam=9, contorno=PRETO)
        if t >= self.T_OLEO:
            yp = -MP.y_pino(th)
            rotulo(tela, 'ÓLEO', 22, 120, ox - 29, int(oy + yp), LATAO, AMARELO)
            rotulo(tela, 'JATO DE ÓLEO', 176, 188, ox + 22, oy - 22, LATAO, AMARELO)
        # painel
        tela.texto('TEMPERATURA', PX0, 8, BRANCO, tam=17, contorno=PRETO)
        tela.texto('CHAMA', PX0, 32, ACO3, tam=9, contorno=PRETO)
        painel(tela, PX0, 42, 164, 10, borda=TRACO)
        for x in range(PX0 + 2, PX0 + 162):
            c = CHAMA1 if (x + int(t * 20)) % 5 else CHAMA0
            tela.ret(x, 44, 1, 6, c)
        tela.ret(PX0 + 96, 39, 2, 16, BRANCO)
        tela.texto('LIMITE DO METAL', PX0 + 70, 57, BRANCO, tam=9, contorno=PRETO)
        tela.texto('MOTOR', PX0, 74, ACO3, tam=9, contorno=PRETO)
        painel(tela, PX0, 84, 164, 12, borda=TRACO)
        tela.ret(PX0 + 2, 86, 96, 8, AGUA0)
        tela.ret(PX0 + 98, 86, 30, 8, BRASA)
        tela.ret(PX0 + 128, 86, 34, 8, VERMELHO)
        nx = PX0 + 2 + int(min(1.0, Tm) * 160)
        tela.ret(nx - 1, 82, 3, 16, BRANCO)
        if Tm > .8: est, cor = 'PERIGO!', VERMELHO
        elif Tm > .62: est, cor = 'ESQUENTANDO', LARANJA
        else: est, cor = 'NORMAL', VERDE
        if not (est == 'PERIGO!' and int(t * 4) % 2):
            tela.texto(est, PX0, 102, cor, tam=17, contorno=PRETO)
        tela.texto("BOMBA D'ÁGUA", PX0, 126, ACO3, tam=9, contorno=PRETO)
        tela.ret(PX0, 139, 8, 8, VERDE if flui else ACO0)
        if flui: tela.ret(PX0 + 2, 141, 3, 3, BRANCO)
        tela.texto('LIGADA' if flui else 'PARADA', PX0 + 13, 136, VERDE if flui else VERMELHO, tam=17, contorno=PRETO)
        tela.texto('VOLTAS DA GOTA', PX0, 162, ACO3, tam=9, contorno=PRETO)
        tela.disco(PX0 + 96, 165, 3.2, BRANCO); tela.disco(PX0 + 96, 165, 2, AGUA1)
        tela.texto(str(self.voltas(t)), PX0, 174, AMARELO, tam=26, contorno=PRETO)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0.0, self.dur, lento=1.0, ganho=.4, chiado=False)
        fx.put(fx.clique(1500, .04), self.t0 + self.LIGA, .35)
        for v in range(1, 10):
            # instante em que andou(t) = v*L
            d = v * self.L
            t = self.LIGA + 1 + (d - self.VEL / 2) / self.VEL
            if t < self.dur: fx.put(EX.tique(fx, 1760), self.t0 + t, .2)


# ============================================================ extra: carro flex
class Flex(Cena):
    """O carro flex brasileiro. O tanque começa com gasolina comum (32%
    de etanol, F19) e o bico verde põe etanol: o contador sobe. A sonda
    lambda no escape vê que sobra ar e avisa a central, que deixa o injetor
    aberto mais tempo (o ajuste chega com atraso, como na vida real)."""
    S = .75
    OXF, OYF = 205, 174
    ENCHE = (8.0, 20.0)

    def preparar(self):
        self.cil = MP.Cilindro(self.OXF, self.OYF, self.S, seed=14)
        ts = np.arange(0, self.dur + .02, .01)
        e = np.array([self.etanol(t) for t in ts])
        a = np.zeros_like(e); a[0] = e[0]
        for i in range(1, len(ts)):                       # a central corrige com atraso (1,2 s)
            a[i] = a[i - 1] + (e[i] - a[i - 1]) * .01 / 1.2
        self.ts, self.aj = ts, a

    def teta(self, t):
        return 240.0 * t

    def nivel(self, t):
        a, b = self.ENCHE
        return .30 + .60 * suave((t - a) / (b - a))

    def etanol(self, t):
        L = self.nivel(t)
        return (.32 * .30 + (L - .30)) / L

    def ajuste(self, t):
        return float(np.interp(t, self.ts, self.aj))

    @staticmethod
    def afr(e):
        return 14.7 * (1 - e) + 9.0 * e

    def desenhar(self, tela, t, tg):
        self.fundo_oficina(tela, t)
        e, aj = self.etanol(t), self.ajuste(t)
        th = self.teta(t)
        T = th % 720
        # escapamento com a sonda
        for (a, b), (c, d) in (((247, 85), (288, 85)), ((288, 85), (288, 150))):
            linha_grossa(tela, a, b, c, d, 9, PRETO)
            linha_grossa(tela, a, b, c, d, 7, ACO1)
        tela.ret(247, 82, 41, 1, ACO3)
        if 540 <= T < 720:
            for k in range(5):
                u = ((T - 540) / 180 + k / 5) % 1.0
                tela.disco(288 + math.sin(k * 2 + t) * 3, 152 + u * 40, 1 + u * 3, GAS if k % 2 else GAS2)
        self.cil.desenhar(tela, th, t)
        dentro = 20 < T < 170
        if dentro: EX.spray_mini(tela, self.cil, t, .6 + .4 * aj)
        EX.injetor_mini(tela, self.cil, 0, aceso=dentro)
        # sonda lambda
        EX.contorno_ret(tela, 264, 74, 9, 7, ACO2)
        EX.contorno_ret(tela, 266, 69, 5, 5, ACO3)
        tela.ret(267, 81, 3, 4, ACO4)
        # central
        EX.contorno_ret(tela, 30, 6, 70, 36, FUNDO2)
        tela.ret(30, 6, 70, 1, ACO3)
        tela.ret(54, 12, 22, 12, PRETO)
        for k in range(5):
            tela.ret(55 + k * 4, 10, 2, 2, ACO3); tela.ret(55 + k * 4, 24, 2, 2, ACO3)
        tela.texto('CENTRAL', 65, 30, BRANCO, tam=9, centro=True, contorno=PRETO)
        fio_l = [(268, 69), (268, 14), (101, 14)]
        fio_i = [(101, 27), (172, 27), (172, 58)]
        EX.fio(tela, fio_l)
        EX.fio(tela, fio_i)
        # sinais: a sonda fala com a central, a central manda abrir o injetor
        for k in range(3):
            x, y = EX.ponto_no_caminho(fio_l, (t * .7 + k / 3) % 1.0)
            tela.ret(int(x) - 1, int(y) - 1, 3, 3, CIANO)
        if 0 <= T < 40 or 700 < T:
            u = ((T + 20) % 720) / 60.0
            x, y = EX.ponto_no_caminho(fio_i, min(1.0, u))
            tela.disco(x, y, 2, AMARELO)
        # tanque e linha de combustível
        linha = [(113, 140), (150, 140), (150, 68), (169, 68)]
        for (a, b), (c, d) in zip(linha, linha[1:]):
            linha_grossa(tela, a, b, c, d, 5, PRETO)
            linha_grossa(tela, a, b, c, d, 3, ACO2)
        for k in range(8):
            x, y = EX.ponto_no_caminho(linha, (t * .25 + k / 8) % 1.0)
            tela.ret(int(x), int(y) - 1, 2, 2, EX.ETANOL if hsh(k, 11) < e else EX.GASOLINA)
        EX.contorno_ret(tela, 28, 116, 8, 12, ACO2)
        yt = EX.tanque(tela, 18, 128, 94, 62, self.nivel(t), e, t)
        a, b = self.ENCHE
        if a - .6 <= t <= b + .6:
            ent = suave((t - (a - .6)) / .6) * (1 - suave((t - b) / .6))
            y0 = int(78 + (1 - ent) * -90)
            EX.contorno_ret(tela, 20, y0, 28, 12, EX.ETANOL)          # gatilho e corpo do bico
            tela.ret(20, y0, 28, 2, CHAMA0)
            EX.contorno_ret(tela, 30, y0 + 12, 4, 18, ACO3)
            tela.texto('ETANOL', 52, y0 + 2, EX.ETANOL, tam=9, contorno=PRETO)
            if a <= t <= b:
                for yy in range(y0 + 30, yt, 2):
                    tela.ret(31 + int(math.sin(yy * .5 + t * 20)), yy, 2, 2, EX.ETANOL if yy % 4 else CHAMA0)
        if t < a - .6:
            tela.texto('GASOLINA COMUM', 8, 94, EX.GASOLINA, tam=9, contorno=PRETO)
            tela.texto('(32% DE ETANOL)', 8, 104, EX.GASOLINA, tam=9, contorno=PRETO)
        tela.texto('TANQUE', 65, 194, BRANCO, tam=9, centro=True, contorno=PRETO)
        rotulo(tela, 'INJETOR', 110, 50, 168, 64, BRANCO, AMARELO)
        rotulo(tela, 'SONDA', 248, 98, 265, 80, BRANCO, AMARELO)
        tela.texto('LAMBDA', 248, 108, BRANCO, tam=9, contorno=PRETO)
        # painel
        tela.texto('ETANOL NO TANQUE', PX0, 8, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{int(round(e * 100))}%", PX0, 20, EX.ETANOL, tam=26, contorno=PRETO)
        painel(tela, PX0, 48, 164, 10, borda=TRACO)
        we = int(160 * e)
        tela.ret(PX0 + 2, 50, we, 6, EX.ETANOL)
        tela.ret(PX0 + 2 + we, 50, 160 - we, 6, EX.GASOLINA)
        tela.texto('AR PARA 1 DE COMBUSTÍVEL', PX0, 66, ACO3, tam=9, contorno=PRETO)
        tela.texto('GASOLINA: 14,7', PX0, 78, EX.GASOLINA, tam=9, contorno=PRETO)
        tela.texto('ETANOL: 9', PX0 + 100, 78, EX.ETANOL, tam=9, contorno=PRETO)
        tela.texto('TEMPO DO JATO', PX0, 98, ACO3, tam=9, contorno=PRETO)
        painel(tela, PX0, 108, 164, 10, borda=TRACO)
        wj = int(160 * (1 / self.afr(aj)) / (1 / 9.0))
        tela.ret(PX0 + 2, 110, wj, 6, AMARELO)
        tela.texto('MISTURA NA CÂMARA', PX0, 128, ACO3, tam=9, contorno=PRETO)
        sobra = e - aj > .025
        tela.texto('SOBRA AR' if sobra else 'NA MEDIDA', PX0, 140, LARANJA if sobra else VERDE, tam=17, contorno=PRETO)
        if sobra:
            tela.texto('CENTRAL: AJUSTANDO...', PX0, 166, CIANO, tam=9, contorno=PRETO)
        else:
            tela.texto('CENTRAL: AJUSTADA', PX0, 166, VERDE, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.sons_do_ciclo(fx, self.teta, 0.0, self.dur, lento=1.0, ganho=.4, chiado=False)
        ult = int(round(self.etanol(0) * 100)) // 5
        for t in np.arange(0, self.dur, .02):
            k = int(round(self.etanol(t) * 100)) // 5
            if k > ult:
                fx.put(EX.tique(fx, 1200 + k * 30), self.t0 + float(t), .14)
                ult = k


CENAS = dict(gancho=Gancho, titulo=Titulo, carro=Carro, pecas=Pecas, injetor=Injetor, admissao=Admissao,
             compressao=Compressao, faisca=Faisca, potencia=Potencia, escape=Escape, ciclo=Ciclo, batidas=Batidas,
             rpm=Rpm, cilindros=Cilindros, energia=Energia, calor=Calor, flex=Flex, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep01_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        import os
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        fr = [float(x) for x in os.environ.get('FR', '.3,.8').split(',')]
        ids = sys.argv[3:]                    # opcional: só esses capítulos
        ts = []
        for c in trilha.caps:
            if ids and c['id'] not in ids: continue
            ts += [c['t0'] + c['dur'] * f for f in fr]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = max(1, min(len(fr) if len(fr) > 2 else 4, len(ims)))
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
