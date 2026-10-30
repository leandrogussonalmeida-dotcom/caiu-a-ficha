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
                   LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO1)
import motor_pixel as MP
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


CENAS = dict(gancho=Gancho, titulo=Titulo, carro=Carro, pecas=Pecas, admissao=Admissao, compressao=Compressao,
             potencia=Potencia, escape=Escape, ciclo=Ciclo, batidas=Batidas, rpm=Rpm, cilindros=Cilindros,
             energia=Energia, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep01_motor as EP
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
