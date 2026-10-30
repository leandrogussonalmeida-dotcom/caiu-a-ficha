#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep09 — Como funciona o relógio mecânico (PT-BR). Os capítulos desenhados.

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (tic, tac, catraca da corda), nos
                          mesmos instantes do desenho
O relógio inteiro anda por UMA variável: `tau`, o tempo do relógio contado em
tiques (alternâncias do balanço). Cada capítulo diz só como `tau` anda no tempo
do vídeo (tempo real = 8 tiques por segundo, câmera lenta, na batida da música);
o balanço, a âncora, a roda de escape, as rodas e os ponteiros saem dela
(`ep09_desenho.Escape.estado` e `Movimento.angulos`). O tic soa no quadro em
que o dente bate na pedra: o som lê a mesma `tau`.

    python3 ep09_motor.py <saida.mp4>                  # o episódio inteiro
    python3 ep09_motor.py <saida.mp4> escape batida    # só esses capítulos (teste)
    python3 ep09_motor.py --folha <saida.png> [ids]    # 2 quadros por capítulo
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2, GAS, GAS2,
                   AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA, OLEO0, OLEO1)
import pixelengine as PX
import ep09_desenho as D
from ep09_desenho import (Escape, Movimento, Mascara, pintar, pintar_tela, roda, pinhao, rubi, brilho, borrao,
                          tambor, mostrador, fundo_bancada, placa, fio, rotulo, barra, curva, espiral_pts)
import ritmo_marca as RM
import idioma as I
from ep09_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2609, 45
GANHO_MUSICA = -10.0          # trilha baixa: o tic-tac e o texto mandam
GANHO_EFEITOS = 0.0
LUFS = -16.0

PX0 = 304                     # coluna do painel da direita
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px
TIQUES_S = 8                  # 28.800 alternâncias por hora = 8 tiques por segundo (fonte F1)
RESERVA_H = 48                # exemplo de reserva de marcha (36 a 72 h, fonte F2)
FASE_COR = {'TRAVADA': ACO3, 'DESTRAVA': CIANO, 'IMPULSO': AMARELO, 'QUEDA': LARANJA}
FASE_TXT = {'TRAVADA': 'TRAVA', 'DESTRAVA': 'DESTRAVA', 'IMPULSO': 'IMPULSO', 'QUEDA': 'QUEDA'}


def milhar(n):
    return I.milhar(int(n))


# ------------------------------------------------------------ peças compartilhadas
_CACHE = {}


def peca(nome):
    """Uma instância por desenho (a tabela do escape custa ~0,4 s para montar)."""
    if nome not in _CACHE:
        if nome == 'mapa': _CACHE[nome] = Movimento(150, 104, 100)
        elif nome == 'perto': _CACHE[nome] = Escape(40, 104, 70, Rb=62)
        elif nome == 'balanco':
            E = Escape(-300, 104, 40, Rb=78, rp=13)
            E.bx, E.by = 138, 104
            _CACHE[nome] = E
    return _CACHE[nome]


def cruzamentos(fn, t0, t1, alvo=0.0, passo=.001):
    """Instantes em que fn(t) passa por um inteiro + alvo, entre t0 e t1."""
    ts = np.arange(t0, t1, passo)
    v = np.array([fn(t) for t in ts]) - alvo
    k = np.floor(v + 1e-9)
    idx = np.nonzero(np.diff(k) > 0)[0]
    return [(float(ts[i + 1]), int(k[i + 1])) for i in idx]


def etiqueta(tela, txt, x, y, ax, ay, cor=AMARELO, tam=9, direita=False):
    """Rótulo com fio até a peça. `direita`: o texto termina em x."""
    if VERTICAL: return
    w = tela.largura_texto(txt, tam)
    xt = x - w if direita else x
    rotulo(tela, txt, xt, y, cor, tam)
    hy = y + (3 if tam == 9 else 7)
    x0 = xt - 3 if not direita else x + 3
    if ax > x: x0 = xt + w + 3
    fio(tela, x0, hy, ax, ay, cor)


def hud(tela, tiques, carga=None, y=150, rotulo_t='TIQUES'):
    """Placar do protagonista: tiques contados e energia na mola."""
    if VERTICAL:
        s = f"{rotulo_t} {milhar(tiques)}"
        return
    h = 54 if carga is not None else 32
    painel(tela, PX0 - 6, y, 172, h, borda=TRACO)
    tela.texto(rotulo_t, PX0 + 2, y + 6, ACO3, tam=9, contorno=PRETO)
    tela.texto(milhar(tiques), PX0 + 164 - 2, y + 4, AMARELO, tam=17, centro='d', contorno=PRETO)
    if carga is not None:
        tela.texto('MOLA', PX0 + 2, y + 30, ACO3, tam=9, contorno=PRETO)
        cor = VERDE if carga > .35 else (AMARELO if carga > .15 else VERMELHO)
        barra(tela, PX0 + 34, y + 30, 92, 8, carga, cor)
        tela.texto(f"{int(round(carga * 100))}%", PX0 + 164 - 2, y + 30, BRANCO, tam=9, centro='d', contorno=PRETO)
        tela.texto('ENERGIA GUARDADA', PX0 + 2, y + 42, ACO1, tam=9)


def hud_vertical(tela, linhas, x=150):
    """No Short o painel some: uma tarja curta no alto do recorte."""
    if not VERTICAL: return
    for j, (s, cor) in enumerate(linhas):
        w = tela.largura_texto(s, 9) + 10
        painel(tela, x - w // 2, 2 + j * 15, w, 13, borda=cor)
        tela.texto(s, x, 5 + j * 15, cor, tam=9, centro=True)


def titulo_painel(tela, l1, l2=None, cor=BRANCO, cor2=AMARELO, y=8):
    if VERTICAL: return
    tela.texto(l1, PX0, y, cor, tam=17, contorno=PRETO)
    if l2: tela.texto(l2, PX0, y + 18, cor2, tam=17, contorno=PRETO)


def seta(tela, x, y, dx, dy, cor, tam=5):
    for k in range(tam):
        w = (tam - k) * 2 - 1
        if dy: tela.ret(x - w // 2, y + (k if dy > 0 else -k), w, 1, cor)
        else: tela.ret(x + (k if dx > 0 else -k), y - w // 2, 1, w, cor)


def escurecer(tela, x, y, w, h):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(PALCO_H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def tique(fx, f=3000.0, dur=.03):
    """O tic: um "plim" metálico curtinho (senos com ataque de 1,5 ms). Sem
    ruído branco: o clique de ruído estoura o pico entre amostras."""
    sr = LG.SR
    n = int(dur * sr)
    tt = np.arange(n) / sr
    env = np.minimum(1.0, tt / .0015) * np.exp(-tt / .006)
    y = (np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 1.51 * tt) + .3 * np.sin(2 * np.pi * f * .5 * tt)) * env
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def tic_tac(fx, t, k, ganho=.35, pan=-.1):
    """O tic (dente batendo na pedra): par = TIC, ímpar = TAC (um pouco mais grave)."""
    if k % 2 == 0: fx.put(tique(fx, 3400), t, ganho, pan)
    else: fx.put(tique(fx, 2600), t, ganho * .9, -pan)


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

    def tau(self, t):
        return TIQUES_S * t

    def sons_tic(self, fx, ganho=.3, t0=0.0, t1=None, maximo=None):
        """Um tic por inteiro de tau (o instante em que a roda trava)."""
        t1 = self.dur if t1 is None else t1
        for t, k in cruzamentos(self.tau, t0 - .0015, t1):
            t = max(t, t0)
            fx.put(tique(fx, 3400 if k % 2 == 0 else 2600), self.t0 + t, ganho, -.15 if k % 2 == 0 else .15)


# ============================================================ gancho
class Gancho(Cena):
    def preparar(self):
        self.E = peca('perto')

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        tau = self.tau(t)
        b, lam, eps, fase = self.E.estado(tau)
        seg = 21 + (eps - self.E.e_sup) / 12.0 / TIQUES_S          # o ponteiro anda com o escape: 8 passos/s
        cx = 140
        mostrador(tela, cx, 104, 80, 10 + 8 / 60, 8 + seg / 60, seg)
        # brilho na ponta do ponteiro dos segundos a cada tique
        a = math.radians(seg * 6 - 90)
        fr = tau - math.floor(tau)
        brilho(tela, cx + math.cos(a) * 60, 104 + math.sin(a) * 60, 6, AMARELO, max(0, 1 - fr * 3))
        n = int(math.floor(tau))
        if VERTICAL:
            hud_vertical(tela, [(f"TIQUES {milhar(n)}", AMARELO)], x=140)
            return
        titulo_painel(tela, 'SEM PILHA,', 'SÓ MOLA', BRANCO, AMARELO, y=14)
        painel(tela, PX0 - 6, 60, 172, 56, borda=AMARELO if fr < .3 else TRACO)
        tela.texto('TIQUES CONTADOS', PX0 + 2, 66, ACO3, tam=9, contorno=PRETO)
        tela.texto(milhar(n), PX0 + 82, 82, AMARELO, tam=26, centro=True, contorno=PRETO)
        if t > 6.0:
            u = ease((t - 6.0) / .6)
            painel(tela, PX0 - 6, 128, 172, 48, borda=CIANO)
            tela.texto('EM 1 DIA:', PX0 + 2, 134, ACO3, tam=9, contorno=PRETO)
            tela.texto(milhar(int(691200 * u)), PX0 + 82, 148, CIANO, tam=17, centro=True, contorno=PRETO)

    def sons(self, fx):
        self.sons_tic(fx, .15)


# ============================================================ título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        roda(tela, 62, 196, 54, 60, t * 8, 'placa', aro=5, raios=5, furo=None)
        roda(tela, 136, 236, 34, 40, -t * 8 * 54 / 34, 'placa', aro=4, raios=4, furo=None)
        roda(tela, 424, 36, 44, 50, -t * 6, 'placa', aro=4, raios=5, furo=None)
        n = int(t / .045)
        for j, linha in enumerate(("COMO FUNCIONA O", "RELÓGIO MECÂNICO")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 15)]
            tela.texto(vis, W // 2 - larg // 2, 60 + j * 34, BRANCO, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tela.texto("POR DENTRO", W // 2, 130, AMARELO, tam=17, centro=True, contorno=PRETO)
        if t > 2.0:
            cores = (VERDE, LATAO, CIANO, ROSA, AMARELO)
            for k in range(5):
                x = W // 2 - 86 + k * 36
                c = cores[k] if t > 2.0 + k * .3 else FUNDO2
                tela.ret(x, 160, 14, 14, c); tela.ret_vazado(x, 160, 14, 14, PRETO)
                tela.texto(str(k + 1), x + 4, 163, PRETO, tam=9)
        # o tique no canto, para não ficar parado
        b = 60 * math.sin(math.pi * t * 2)
        roda(tela, 452, 186, 14, 0, b, 'latao', perfil='liso', aro=2, raios=3, furo=None)

    def sons(self, fx):
        for k in range(5):
            fx.put(fx.blip(72 + k * 2, .1), self.t0 + 2.0 + k * .3, .18)


# ============================================================ abrir
class Abrir(Cena):
    T_VIRA = 10.0

    def preparar(self):
        self.M = peca('mapa')
        self.tmp = PX.Tela(W, H, paleta=LG.PAL)

    def _frente(self, tela, t):
        fundo_bancada(tela)
        seg = 21 + t
        mostrador(tela, 150, 104, 70, 10 + 8 / 60, 8 + seg / 60, math.floor(seg * 8) / 8)

    def _costas(self, tela, t):
        fundo_bancada(tela)
        # caixa (aço) com o fundo de vidro
        roda(tela, 150, 104, 106, 0, 0, 'aco', perfil='liso', furo=None)
        roda(tela, 150, 104, 103, 0, 0, 'acoesc', perfil='liso', furo=None)
        self.M.desenhar(tela, TIQUES_S * t)
        # reflexo do vidro
        for k in range(10):
            tela.ret(84 + k * 2, 40 + k * 2, 2, 1, ACO2)

    def desenhar(self, tela, t, tg):
        tv = self.T_VIRA
        if t < tv - .6:
            self._frente(tela, t)
            if not VERTICAL and t > 1.0:
                etiqueta(tela, 'COROA', 250, 70, 228, 100, AMARELO)
                etiqueta(tela, 'PONTEIROS', 250, 140, 168, 110, AMARELO)
                etiqueta(tela, 'MOSTRADOR', 20, 30, 112, 70, AMARELO)
        elif t < tv + .6:
            # vira de costas: a imagem encolhe na horizontal e abre do outro lado
            u = (t - (tv - .6)) / 1.2
            sx = abs(math.cos(u * math.pi))
            T = self.tmp
            T.buf[:] = FUNDO
            (self._frente if u < .5 else self._costas)(T, t)
            fundo_bancada(tela)
            xs = np.arange(0, 300)
            src = np.clip((150 + (xs - 150) / max(sx, .04)).astype(int), 0, 299)
            ok = np.abs(xs - 150) <= 112 * sx + 1
            col = T.buf[:PALCO_H, :300][:, src]
            fundo = tela.buf[:PALCO_H, :300]
            fundo[:, ok] = col[:, ok]
        else:
            self._costas(tela, t)
            if not VERTICAL and t > 21:
                A = self.M.ancoras()
                etiqueta(tela, 'MECANISMO', 8, 14, 70, 60, AMARELO)
        if VERTICAL: return
        titulo_painel(tela, 'DO QUE ELE', 'PRECISA?', BRANCO, AMARELO, y=10)
        itens = [('ENERGIA', VERDE, 10.0), ('UM RITMO', CIANO, 14.0)]
        for j, (txt, cor, ta) in enumerate(itens):
            if t < ta: continue
            y = 56 + j * 34
            u = ease((t - ta) / .4)
            x = int(PX0 + (1 - u) * 160)
            painel(tela, x - 6, y, 160, 26, borda=cor)
            tela.ret(x, y + 7, 10, 10, cor)
            tela.texto(txt, x + 16, y + 5, cor, tam=17, contorno=PRETO)
        if t >= 20.0:
            tela.texto('FUNDO DE VIDRO:', PX0, 134, ACO3, tam=9, contorno=PRETO)
            tela.texto('DÁ PARA VER', PX0, 146, BRANCO, tam=9, contorno=PRETO)
            tela.texto('TUDO ANDANDO', PX0, 158, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.chiado(1.2, 400, 3000), self.t0 + self.T_VIRA - .6, .15)
        for t, k in cruzamentos(lambda t: TIQUES_S * t, self.T_VIRA + .6, self.dur):
            fx.put(tique(fx, 3400 if k % 2 == 0 else 2600), self.t0 + t, .1)


# ============================================================ peças
PECAS = [('tambor', 'TAMBOR E MOLA', VERDE), ('rodas', 'RODAS', LATAO), ('escape', 'RODA DE ESCAPE', CIANO),
         ('ancora', 'ÂNCORA', ACO3), ('balanco', 'BALANÇO', ROSA), ('rubis', 'RUBIS', VERMELHO)]


class Pecas(Cena):
    def preparar(self):
        self.M = peca('mapa')
        self.slot = self.dur / len(PECAS)
        self.t_anda = 4 * self.slot + .6           # o balanço chega e tudo começa a andar

    def tau(self, t):
        return max(0.0, t - self.t_anda) * TIQUES_S

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        k_atual = min(len(PECAS) - 1, int(t / self.slot))
        vis, desl = set(), {}
        for k, (nome, rot, cor) in enumerate(PECAS):
            tk = k * self.slot
            if t >= tk:
                vis.add(nome)
                u = (t - tk) / .55
                if u < 1:
                    y = -170 * (1 - u) ** 2 if u < .75 else -5 * math.sin((u - .75) / .25 * math.pi)
                    desl[nome] = (0, y)
        tau = self.tau(t)
        self.M.desenhar(tela, tau, vis=vis, desl=desl, brilho_rubis=.6 if k_atual == 5 else 0.0)
        if VERTICAL: return
        A = self.M.ancoras()
        for k, (nome, rot, cor) in enumerate(PECAS):
            if t < k * self.slot: continue
            y = 12 + k * 22
            atual = k == k_atual
            tela.texto(rot, PX0, y, AMARELO if atual else ACO2, tam=17, contorno=PRETO)
            if atual and t - k * self.slot > .55:
                if nome == 'rubis':
                    ax, ay = self.M.pontos_rubi()[3]
                else:
                    ax, ay = A[nome]
                tela.ret(PX0 - 6, y + 6, 3, 3, AMARELO)
                fio(tela, PX0 - 6, y + 7, ax, ay)
        if t >= self.t_anda:
            painel(tela, PX0 - 6, 150, 172, 30, borda=VERDE)
            tela.texto('ANDANDO: 8 TIQUES/S', PX0 + 2, 154, VERDE, tam=9, contorno=PRETO)
            tela.texto(f'TIQUES {milhar(math.floor(tau))}', PX0 + 2, 166, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(len(PECAS)):
            t = self.t0 + k * self.slot + .41
            fx.put(fx.clique(1800, .05), t, .22)
            fx.put(fx.sino(76 + k * 2, .5), t, .08)
        self.sons_tic(fx, .1, t0=self.t_anda)


# ============================================================ mola real
class Mola(Cena):
    T_CORDA = (3.0, 21.0)
    DENTES_CATRACA = 30

    def carga(self, t):
        a, b = self.T_CORDA
        if t < a: return .08
        if t < b: return .08 + .92 * suave((t - a) / (b - a))
        return 1.0 - .30 * (t - b) / (self.dur - b)          # acelerado: 1 s = 2 h de relógio

    def ang_eixo(self, t):
        """O eixo (catraca) gira quando se dá corda: 10 voltas de 0 a 100%."""
        a, b = self.T_CORDA
        return 360 * 10 * (self.carga(min(t, b)) - .08) / .92

    def ang_tambor(self, t):
        a, b = self.T_CORDA
        return 0.0 if t < b else 360 * 3 * (t - b) / (self.dur - b)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        cx, cy, R = 118, 104, 84
        q = self.carga(t)
        ae, at = self.ang_eixo(t), self.ang_tambor(t)
        tambor(tela, cx, cy, R, at, ae + at, q)
        # catraca por cima, em fantasma (dá para ver a mola embaixo)
        Rc = R * .32
        a_c = ae + at
        D.fantasma(tela, lambda: roda(tela, cx, cy, Rc, self.DENTES_CATRACA, a_c, 'aco', perfil='catraca',
                                      h=4, aro=3, raios=3, cubo=7, furo=None))
        tela.disco(cx, cy, 5, PRETO); Mk = Mascara(); Mk.ret(cx - 3, cy - 3, 7, 7); pintar_tela(tela, Mk, 'aco')
        # lingueta (trava a catraca): pula a cada dente quando se dá corda
        u = ((a_c / (360.0 / self.DENTES_CATRACA)) % 1.0)
        girando = self.T_CORDA[0] <= t < self.T_CORDA[1]
        lev = 3.0 * u if girando else 0
        pa = math.radians(-150)
        px_, py_ = cx + math.cos(pa) * (Rc + 16), cy + math.sin(pa) * (Rc + 16)
        tip = math.radians(-128)
        tx, ty = cx + math.cos(tip) * (Rc - 2 + lev), cy + math.sin(tip) * (Rc - 2 + lev)
        Mk = Mascara(); linha_grossa(Mk, px_, py_, tx, ty, 4, 1); Mk.disco(px_, py_, 4)
        pintar_tela(tela, Mk, 'aco')
        tela.px(px_, py_, PRETO)
        # roda de coroa + haste + coroa (à direita)
        a = math.radians(-12)
        rx, ry = cx + math.cos(a) * (Rc + 11), cy + math.sin(a) * (Rc + 11)
        Mk = Mascara(); linha_grossa(Mk, rx, ry, 262, ry, 5, 1); pintar_tela(tela, Mk, 'aco')
        roda(tela, rx, ry, 11, 14, -a_c * Rc / 11, 'aco', furo=None)
        Mk = Mascara(); Mk.ret(258, ry - 12, 16, 24); pintar_tela(tela, Mk, 'aco')
        girando = self.T_CORDA[0] <= t < self.T_CORDA[1]
        for k in range(6):
            yk = ry - 11 + ((k * 4 + (a_c * .2 if girando else 0)) % 24)
            tela.ret(260, int(yk), 12, 1, ACO0)
        if girando:
            seta(tela, 280, int(ry) - 6, 0, -1, AMARELO, 5)
            tela.ret(279, int(ry) - 6, 3, 14, AMARELO)
        if t >= self.T_CORDA[1]:
            # o tambor gira e empurra as rodas: brilho nos dentes que engrenam
            ad = math.radians(20)
            brilho(tela, cx + math.cos(ad) * R, cy + math.sin(ad) * R, 7, AMARELO, .8)
        if VERTICAL:
            hud_vertical(tela, [(f"MOLA {int(round(q * 100))}%", VERDE)], x=118)
            return
        etiqueta(tela, 'MOLA REAL', 8, 16, cx - 46, cy - 40, AMARELO)
        etiqueta(tela, 'TAMBOR', 8, 190, cx - 64, cy + 50, AMARELO)
        etiqueta(tela, 'COROA', 246, 150, 266, ry + 12, AMARELO)
        etiqueta(tela, 'CATRACA', 196, 190, cx + 20, cy + 28, ACO3)
        if t > 9:
            etiqueta(tela, 'LINGUETA', 150, 6, int(px_), int(py_) - 3, CIANO)
        # painel
        titulo_painel(tela, 'ENERGIA', 'NA MOLA', BRANCO, VERDE, y=10)
        painel(tela, PX0 - 6, 54, 172, 40, borda=VERDE)
        cor = VERDE if q > .35 else (AMARELO if q > .15 else VERMELHO)
        barra(tela, PX0 + 2, 62, 120, 10, q, cor)
        tela.texto(f"{int(round(q * 100))}%", PX0 + 162, 60, BRANCO, tam=17, centro='d', contorno=PRETO)
        st = 'PARADA' if t < self.T_CORDA[0] else ('DANDO CORDA' if girando else 'DESENROLANDO')
        tela.texto(st, PX0 + 2, 79, AMARELO if girando else ACO3, tam=9, contorno=PRETO)
        if t >= 17.8:
            painel(tela, PX0 - 6, 104, 172, 52, borda=TRACO)
            tela.texto('RESERVA DE MARCHA', PX0 + 2, 110, ACO3, tam=9, contorno=PRETO)
            if t >= 26.8:
                tela.texto('36 A 72 H', PX0 + 2, 124, AMARELO, tam=17, contorno=PRETO)
            else:
                h = RESERVA_H * q
                tela.texto(f"{int(h)} H {int((h % 1) * 60):02d} MIN", PX0 + 2, 124, AMARELO, tam=17, contorno=PRETO)
                tela.texto(f"(EXEMPLO: {RESERVA_H} H CHEIA)", PX0 + 2, 144, ACO2, tam=9)
        if t >= self.T_CORDA[1]:
            tela.texto('ACELERADO: 1 S = 2 H', PX0, 168, CIANO, tam=9, contorno=PRETO)

    def sons(self, fx):
        a, b = self.T_CORDA
        passo = 360.0 / self.DENTES_CATRACA
        ult = 0
        for i in range(int((b - a) / .002)):
            t = a + i * .002
            k = int(self.ang_eixo(t) / passo)
            if k > ult:
                fx.put(tique(fx, 2000, .04), self.t0 + t, .2, .3)
                ult = k
        for k in range(int((self.dur - b) * 6)):
            fx.put(tique(fx, 3400), self.t0 + b + k / 6, .06)


# ============================================================ engrenagens
class Engrenagens(Cena):
    """O trem de rodas a 60x: 1 minuto do vídeo = 1 hora do relógio."""
    X = 60.0

    def preparar(self):
        def apos(p, ang, d):
            return (p[0] + math.cos(math.radians(ang)) * d, p[1] + math.sin(math.radians(ang)) * d)
        self.Bc, self.RB = (62, 148), 54
        self.Cc, self.RC = apos(self.Bc, -50, 54 + 8), 44
        self.Tc, self.RT = apos(self.Cc, 8, 44 + 7), 36
        self.Fc, self.RF = apos(self.Tc, -48, 36 + 6), 30
        self.Ec, self.RE = apos(self.Fc, 30, 30 + 5), 20

    def angs(self, t):
        seg = t * self.X                           # segundos do relógio
        centro = -360 * seg / 3600.0
        terceira = -centro * 8
        quarta = -terceira * 7.5
        escape = -quarta * 16
        tambor = -centro / 6
        return tambor, centro, terceira, quarta, escape

    def foco(self, t):
        for a, k in ((26.8, 3), (17.8, 1), (8.8, 2), (0.0, 0)):
            if t >= a: return k
        return 0

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        tb, ce, te, qu, es = self.angs(t)
        # quem empurra fica por cima; o pinhão de cada roda aparece por cima de tudo
        roda(tela, *self.Bc, self.RB, 90, tb, 'latao', furo=None)
        tela.disco(*self.Bc, self.RB * .8, OLEO0)
        tela.anel(*self.Bc, self.RB * .8, LATAO, .6)
        roda(tela, *self.Bc, self.RB * .55, 30, tb, 'aco', perfil='catraca', aro=3, raios=3, cubo=8, furo=None)
        borrao(tela, *self.Ec, self.RE, 'aco')
        roda(tela, *self.Fc, self.RF, 80, qu, 'latao', aro=3.5, raios=4, furo=None)
        roda(tela, *self.Tc, self.RT, 75, te, 'latao', aro=3.5, raios=4, furo=None)
        roda(tela, *self.Cc, self.RC, 80, ce, 'latao', aro=4, raios=4, furo=None)
        pinhao(tela, *self.Cc, 8, 10, ce)
        pinhao(tela, *self.Tc, 7, 10, te)
        pinhao(tela, *self.Fc, 6, 8, qu)
        pinhao(tela, *self.Ec, 5, 7, es)
        # ponteiros presos nos eixos: minutos na roda do centro, segundos na quarta
        foco = self.foco(t)
        for (c, ang, comp, cor, larg) in ((self.Cc, -ce, 50, ACO4, 3), (self.Fc, -qu, 40, VERMELHO, 1)):
            a = math.radians(ang - 90)
            x1, y1 = c[0] + math.cos(a) * comp, c[1] + math.sin(a) * comp
            if larg > 1:
                Mk = Mascara(); linha_grossa(Mk, c[0], c[1], x1, y1, larg, 1); pintar_tela(tela, Mk, 'aco')
            else:
                tela.linha(c[0], c[1], x1, y1, cor)
            tela.disco(c[0], c[1], 2.5, cor)
        for c in (self.Cc, self.Tc, self.Fc, self.Ec):
            rubi(tela, c[0], c[1], 2.4)
        # energia correndo pela fila de rodas
        caminho = [self.Bc, self.Cc, self.Tc, self.Fc, self.Ec]
        for i in range(10):
            u = (t * .35 + i / 10) % 1.0
            seg = u * 4; j = int(seg); f = seg - j
            a, b = caminho[j], caminho[j + 1]
            x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            tela.ret(int(x) - 1, int(y) - 1, 3, 3, PRETO); tela.px(x, y, AMARELO)
        # destaque da roda do capítulo
        alvo = {1: (self.Cc, self.RC), 2: (self.Tc, self.RT), 3: (self.Fc, self.RF)}.get(foco)
        if alvo and int(t * 3) % 2 == 0:
            tela.anel(alvo[0][0], alvo[0][1], alvo[1] + 3, AMARELO, .5)
        if VERTICAL:
            hud_vertical(tela, [("60X MAIS RÁPIDO", CIANO)], x=130)
            return
        etiqueta(tela, 'TAMBOR', 140, 192, int(self.Bc[0] + 44), int(self.Bc[1] + 24), AMARELO if foco == 0 else ACO3)
        etiqueta(tela, 'CENTRO', 8, 12, int(self.Cc[0] - 26), int(self.Cc[1] - 22), AMARELO if foco == 1 else ACO3)
        etiqueta(tela, 'TERCEIRA', 232, 170, int(self.Tc[0] + 20), int(self.Tc[1] + 26), AMARELO if foco == 2 else ACO3)
        etiqueta(tela, 'QUARTA', 120, 8, int(self.Fc[0] - 16), int(self.Fc[1] - 22), AMARELO if foco == 3 else ACO3)
        etiqueta(tela, 'ESCAPE', 244, 12, int(self.Ec[0] + 10), int(self.Ec[1] - 14), ACO3)
        titulo_painel(tela, 'VOLTAS', 'DE CADA RODA', BRANCO, ACO3, y=8)
        linhas = [('CENTRO', '1 POR HORA', 1), ('TERCEIRA', '8 POR HORA', 2), ('QUARTA', '1 POR MINUTO', 3)]
        for j, (a, b, k) in enumerate(linhas):
            y = 52 + j * 30
            on = foco >= k or foco == 0
            cor = AMARELO if foco == k else (BRANCO if on else ACO1)
            tela.texto(a, PX0, y, ACO3 if on else ACO1, tam=9, contorno=PRETO)
            tela.texto(b, PX0, y + 11, cor, tam=17 if foco == k else 9, contorno=PRETO)
        painel(tela, PX0 - 6, 150, 172, 34, borda=CIANO)
        tela.texto('TEMPO 60X MAIS RÁPIDO', PX0 + 2, 156, CIANO, tam=9, contorno=PRETO)
        hm = t * self.X / 60
        tela.texto(f"RELÓGIO ANDOU {int(hm)} MIN", PX0 + 2, 168, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(int(self.dur)):
            fx.put(tique(fx, 2400), self.t0 + k + .5, .1)


# ============================================================ escape (câmera superlenta)
class EscapeCena(Cena):
    """Um tique por compasso (3 s): o tic cai no 1 do compasso. Dentro do
    compasso o tempo do relógio corre rápido no balanço solto e quase para na
    passagem pelo centro (destrava, impulso, queda)."""

    def preparar(self):
        from scipy.interpolate import PchipInterpolator
        self.E = peca('perto')
        self.bar = 4 * self.spb
        self.f = PchipInterpolator([0, .22, .42, 1.0], [0, .04, .86, 1.0])

    def tau(self, t):
        k = math.floor(t / self.bar)
        u = t / self.bar - k
        return k + float(self.f(u))

    def velocidade(self, t):
        d = 1e-3
        return (self.tau(t + d) - self.tau(t - d)) / (2 * d)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        E = self.E
        tau = self.tau(t)
        b, lam, eps, fase = E.estado(tau)
        # balanço ao fundo, fora de foco
        E.desenhar_balanco(tela, b, espiral=False)
        escurecer(tela, E.bx - E.Rb - 2, E.by - E.Rb - 2, 2 * E.Rb + 5, 2 * E.Rb + 5)
        E.desenhar_roda(tela, eps)
        E.batentes(tela)
        k = math.ceil(tau - 1e-9)
        ativa = ('inf' if k % 2 == 0 else 'sup') if fase in ('IMPULSO', 'DESTRAVA') else None
        E.desenhar_ancora(tela, lam, brilho_pedra=ativa)
        E.desenhar_rolete(tela, b, brilhar=.9 if fase in ('IMPULSO', 'DESTRAVA') else 0)
        fr = tau - math.floor(tau)
        if fr < .03:
            fase = 'TRAVADA'
            kk = round(tau)
            ang = E.e_sup if kk % 2 == 0 else E.e_inf
            x, y = E._polar(E.Rw, ang + 1)
            brilho(tela, x, y, 12, AMARELO, 1 - fr / .03)
            tela.px(x, y, BRANCO)
            if not VERTICAL: rotulo(tela, 'TIC!' if kk % 2 == 0 else 'TAC!', int(x) + 8, int(y) - 14, AMARELO, 17)
        n = int(math.floor(tau))
        if VERTICAL:
            hud_vertical(tela, [(FASE_TXT[fase], FASE_COR[fase])], x=130)
            return
        etiqueta(tela, 'RODA DE ESCAPE', 8, 8, 48, 50, ACO3)
        etiqueta(tela, 'ÂNCORA', 132, 8, int(E.px) + 2, int(E.py) - 10, ACO3)
        etiqueta(tela, 'PEDRAS', 132, 192, int(E._rot(*E._polar(E.r_inf + 6, E.c_inf), lam)[0]),
                 int(E._rot(*E._polar(E.r_inf + 6, E.c_inf), lam)[1]), ROSA)
        px_, py_ = E.pino(b)
        etiqueta(tela, 'PINO DE IMPULSO', 196, 192, int(px_), int(py_) + 2, ROSA)
        etiqueta(tela, 'BALANÇO', 236, 8, int(E.bx + 30), int(E.by - 44), ACO3)
        # painel: as 4 fases, a atual acesa
        titulo_painel(tela, 'ESCAPE', None, BRANCO, y=8)
        tela.texto('CÂMERA SUPERLENTA', PX0, 28, CIANO, tam=9, contorno=PRETO)
        for j, f in enumerate(('TRAVADA', 'DESTRAVA', 'IMPULSO', 'QUEDA')):
            y = 44 + j * 24
            on = f == fase
            cor = FASE_COR[f]
            painel(tela, PX0 - 6, y, 150, 20, borda=cor if on else TRACO, fundo=PRETO)
            tela.ret(PX0, y + 6, 8, 8, cor if on else FUNDO2)
            tela.texto(f"{j + 1} {FASE_TXT[f]}", PX0 + 14, y + 3, cor if on else ACO1, tam=17 if on else 9, contorno=PRETO)
        hud(tela, n, None, y=150)

    def sons(self, fx):
        self.sons_tic(fx, .22)
        # o destrava: um clique baixinho quando o pino entra no garfo
        E = self.E
        for t, k in cruzamentos(self.tau, 0, self.dur, alvo=1 - E.x_lock - E.Dt):
            fx.put(tique(fx, 1800), self.t0 + t, .07)


# ============================================================ balanço
class Balanco(Cena):
    def preparar(self):
        self.E = peca('balanco')

    def tau(self, t):
        return t / self.spb                         # um tique por batida da música

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        E = self.E
        tau = self.tau(t)
        b = E.beta(tau)
        E.desenhar_balanco(tela, b, espiral=True)
        E.desenhar_rolete(tela, b, brilhar=0)
        # ponte por cima, presa no centro (só um braço, para a espiral aparecer)
        Mk = Mascara(); linha_grossa(Mk, E.bx, E.by, E.bx + 96, E.by + 70, 9, 1); Mk.disco(E.bx, E.by, 7)
        pintar_tela(tela, Mk, 'aco', cx=E.bx, cy=E.by, R=40)
        rubi(tela, E.bx, E.by, 3.4)
        # a ponta do garfo da âncora, que só encosta na passagem pelo centro
        lam = E._lam_beta(b)
        gx = E.bx - E.rp - 4
        Mk = Mascara()
        c, s_ = math.cos(lam), math.sin(lam)
        for sy in (-1, 1):
            Mk.ret(gx - 30, E.by + sy * 3 - (2 if sy < 0 else 0) + math.sin(lam) * -30, 30, 2)
        linha_grossa(Mk, gx - 40, E.by - math.sin(lam) * 40, gx, E.by, 5, 1)
        pintar_tela(tela, Mk, 'aco')
        toca = abs(b) < E.betaw
        if toca:
            px_, py_ = E.pino(b)
            brilho(tela, px_, py_, 10, AMARELO, .9)
        n = int(math.floor(tau))
        if VERTICAL:
            hud_vertical(tela, [(f"TIQUES {n}", AMARELO), ('TOCA O GARFO' if toca else 'SOLTO', AMARELO if toca else CIANO)], x=140)
            return
        etiqueta(tela, 'BALANÇO', 8, 12, int(E.bx - 66), int(E.by - 40), AMARELO)
        etiqueta(tela, 'ESPIRAL', 8, 190, int(E.bx - 30), int(E.by + 22), CIANO)
        etiqueta(tela, 'GARFO', 8, 100, int(gx - 34), int(E.by), ACO3)
        # gráfico: o ângulo do balanço no tempo; em amarelo, quando toca o garfo
        titulo_painel(tela, 'ÂNGULO DO', 'BALANÇO', BRANCO, ROSA, y=6)
        gx0, gy0, gw, gh = PX0 - 2, 50, 166, 70
        painel(tela, gx0 - 4, gy0 - 4, gw + 8, gh + 8, borda=TRACO)
        tela.ret(gx0, gy0 + gh // 2, gw, 1, FUNDO3)
        janela = 6.0
        for i in range(gw):
            tt = t - janela + janela * i / gw
            if tt < 0: continue
            bb = E.beta(self.tau(tt))
            y = gy0 + gh // 2 - bb / E.A * (gh // 2 - 3)
            tela.px(gx0 + i, y, CIANO)
        k0 = math.ceil(self.tau(max(0.0, t - janela)) - E.tau0)
        k1 = math.floor(self.tau(t) - E.tau0)
        for k in range(k0, k1 + 1):
            tc = (k + E.tau0) * self.spb                 # passagem pelo centro (beta = 0)
            i = int((tc - (t - janela)) / janela * gw)
            if 0 <= i < gw:
                tela.ret(gx0 + i - 1, gy0 + gh // 2 - 6, 3, 13, AMARELO)
        tela.ret(gx0 + gw - 1, gy0, 1, gh, BRANCO)
        tela.texto('SOLTO', PX0, 128, CIANO, tam=9, contorno=PRETO)
        tela.texto('TOCA O GARFO', PX0 + 54, 128, AMARELO, tam=9, contorno=PRETO)
        hud(tela, n, None, y=148, rotulo_t='TIQUES (IDA OU VOLTA)')
        tela.texto('1 POR BATIDA DA MÚSICA', PX0, 186, ACO2, tam=9)

    def sons(self, fx):
        self.sons_tic(fx, .18)


# ============================================================ batida
class Batida(Cena):
    T_REAL = 16.0

    def preparar(self):
        self.E = peca('perto')

    def tau(self, t):
        if t < self.T_REAL: return t / self.spb                           # 1 por batida
        return self.tau(self.T_REAL - 1e-9) + TIQUES_S * (t - self.T_REAL)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        E = self.E
        tau = self.tau(t)
        real = t >= self.T_REAL
        b, lam, eps, fase = E.estado(tau)
        E.desenhar_balanco(tela, b, espiral=False)
        escurecer(tela, E.bx - E.Rb - 2, E.by - E.Rb - 2, 2 * E.Rb + 5, 2 * E.Rb + 5)
        E.desenhar_roda(tela, eps)
        E.batentes(tela)
        E.desenhar_ancora(tela, lam)
        E.desenhar_rolete(tela, b)
        fr = tau - math.floor(tau)
        if fr < (.3 if real else .08):
            kk = round(tau)
            x, y = E._polar(E.Rw, (E.e_sup if kk % 2 == 0 else E.e_inf) + 1)
            brilho(tela, x, y, 12, AMARELO, 1 - fr / (.3 if real else .08))
        batida = int(t / self.spb) % 4
        if VERTICAL:
            hud_vertical(tela, [(f"{8 if real else 2} TIQUES POR SEGUNDO", AMARELO if real else CIANO)], x=130)
            return
        titulo_painel(tela, 'NA BATIDA', None, BRANCO, y=8)
        for j in range(4):
            x = PX0 + j * 40
            aceso = j == batida
            cor = AMARELO if real else CIANO
            tela.ret(x, 30, 32, 26, cor if aceso else FUNDO2)
            tela.ret_vazado(x, 30, 32, 26, cor)
            if real:
                for q in range(4):
                    on = aceso and int((t % self.spb) / (self.spb / 4)) >= q
                    tela.ret(x + 3 + q * 7, 49, 5, 4, PRETO if on else ACO0)
            tela.texto(str(j + 1), x + 12, 34, PRETO if aceso else cor, tam=17)
        tela.texto('TIQUES POR SEGUNDO', PX0, 66, ACO3, tam=9, contorno=PRETO)
        tela.texto('8' if real else '2', PX0, 78, AMARELO if real else CIANO, tam=26, contorno=PRETO)
        tela.texto('VELOCIDADE REAL' if real else '4X MAIS LENTO', PX0 + 30, 86, AMARELO if real else CIANO, tam=9, contorno=PRETO)
        # ritmos comuns (fonte F1)
        tela.texto('RITMOS COMUNS', PX0, 112, ACO3, tam=9, contorno=PRETO)
        for j, (bph, ps) in enumerate(((18000, 5), (21600, 6), (28800, 8), (36000, 10))):
            y = 124 + j * 12
            on = real and bph == 28800
            cor = AMARELO if on else ACO2
            tela.texto(f"{milhar(bph)}/H", PX0, y, cor, tam=9, contorno=PRETO)
            tela.texto(f"{ps} POR S", PX0 + 64, y, cor, tam=9, contorno=PRETO)
            if on and t >= 23.8: tela.texto('= 4 HZ', PX0 + 118, y, CIANO, tam=9, contorno=PRETO)
        tela.texto(f"TIQUES {milhar(math.floor(tau))}", PX0, 180, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        self.sons_tic(fx, .18)


# ============================================================ rubis
class Rubis(Cena):
    def preparar(self):
        self.M = peca('mapa')

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        tau = TIQUES_S * t
        pts = self.M.pontos_rubi()
        acesos = min(len(pts), 1 + int(t / .6))
        self.M.desenhar(tela, tau, rubis_acesos=acesos, brilho_rubis=.5 + .3 * math.sin(t * 4))
        if VERTICAL:
            hud_vertical(tela, [("17 RUBIS", VERMELHO)], x=150)
            return
        if t < 7.8:
            for i, (x, y) in enumerate(pts[:acesos]):
                if i == acesos - 1: brilho(tela, x, y, 10, ROSA, .9)
        # painel: o mancal com rubi em corte e a comparação de atrito
        titulo_painel(tela, 'MANCAL', 'DE RUBI', BRANCO, ROSA, y=6)
        cx, cy = PX0 + 34, 74
        tela.disco(cx, cy, 24, PRETO)
        roda(tela, cx, cy, 22, 0, 0, 'rubi', perfil='liso', furo=None)
        tela.disco(cx, cy, 6, PRETO)
        tela.disco(cx - 3, cy - 3, 3, ROSA)
        # o eixo de aço girando no furo, com a gotinha de óleo
        a = t * 7
        tela.disco(cx, cy, 4.5, ACO2)
        tela.linha(cx - math.cos(a) * 4, cy - math.sin(a) * 4, cx + math.cos(a) * 4, cy + math.sin(a) * 4, ACO4)
        tela.ret(cx + 9, cy - 16, 3, 3, AMARELO)
        tela.texto('EIXO', cx + 30, cy - 18, ACO3, tam=9, contorno=PRETO)
        tela.texto('RUBI', cx + 30, cy - 6, ROSA, tam=9, contorno=PRETO)
        tela.texto('ÓLEO', cx + 30, cy + 6, AMARELO, tam=9, contorno=PRETO)
        if t >= 15.8:
            tela.texto('ATRITO', PX0, 106, ACO3, tam=9, contorno=PRETO)
            u = ease((t - 15.8) / 1.2)
            for j, (nome, v, cor) in enumerate((('AÇO NO AÇO', .58, ACO3), ('SAFIRA NO AÇO', .125, ROSA))):
                y = 118 + j * 24
                tela.texto(nome, PX0, y, cor, tam=9, contorno=PRETO)
                barra(tela, PX0, y + 11, int(140 * v / .6 * u) + 1, 6, 1.0, cor)
                tela.texto('0,58' if j == 0 else '0,10-0,15', PX0 + 166, y, BRANCO, tam=9, centro='d', contorno=PRETO)
        if t >= 22.8:
            painel(tela, PX0 - 6, 166, 172, 24, borda=VERMELHO)
            tela.texto('COMPLETO: 17 RUBIS', PX0 + 2, 172, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for i in range(6):
            fx.put(fx.sino(79 + (i % 3) * 3, .4), self.t0 + i * .6, .1)


# ============================================================ ponteiros (redução 12 para 1)
class Ponteiros(Cena):
    def preparar(self):
        self.C = (132, 104)
        a = math.radians(-35)
        self.Mn = (self.C[0] + math.cos(a) * 52, self.C[1] + math.sin(a) * 52)

    def minutos(self, t):
        return 60 * (t / 2.25)                      # uma volta dos minutos a cada 2,25 s (duas batidas... 3 batidas)

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        C, Mn = self.C, self.Mn
        m = self.minutos(t)
        a_can = m * 6                               # pinhão de canhão: com os minutos
        a_min = -a_can / 3                          # roda de minutos: 12 dentes -> 36
        a_hor = a_can / 12                          # roda das horas: 1/12
        # fundo: o mostrador visto por dentro, em contorno
        tela.anel(C[0], C[1], 96, FUNDO3, 1)
        roda(tela, *C, 40, 48, a_hor, 'latao', aro=4, raios=4, cubo=9, furo=None)       # roda das horas
        roda(tela, *Mn, 36, 36, a_min, 'latao', aro=4, raios=4, cubo=6, furo=None)      # roda de minutos
        pinhao(tela, *Mn, 12, 12, a_min)                                                  # seu pinhão
        roda(tela, *C, 16, 12, a_can, 'aco', furo=None)                                  # pinhão de canhão
        # ponteiros por cima
        for ang, comp, larg, mat in ((a_hor, 58, 6, 'aco'), (a_can, 88, 4, 'aco')):
            a = math.radians(ang - 90)
            Mk = Mascara()
            linha_grossa(Mk, C[0] - math.cos(a) * 10, C[1] - math.sin(a) * 10,
                         C[0] + math.cos(a) * comp, C[1] + math.sin(a) * comp, larg, 1)
            pintar_tela(tela, Mk, mat, cx=C[0], cy=C[1], R=comp)
        tela.disco(*C, 4, PRETO); tela.disco(*C, 3, ACO3); tela.px(C[0], C[1], BRANCO)
        rubi(tela, Mn[0], Mn[1], 2.4)
        voltas = m / 60
        if VERTICAL:
            hud_vertical(tela, [(f"MINUTOS {int(voltas)} VOLTAS", BRANCO), (f"HORAS {int(voltas) % 12 if voltas < 12 else 12}/12", AMARELO)], x=132)
            return
        etiqueta(tela, 'CANHÃO', 8, 196, C[0] - 8, C[1] + 12, ACO3)
        etiqueta(tela, 'RODA DAS HORAS', 8, 8, C[0] - 30, C[1] - 22, AMARELO)
        etiqueta(tela, 'RODA DE MINUTOS', 196, 8, int(Mn[0]) + 18, int(Mn[1]) - 24, AMARELO)
        titulo_painel(tela, 'REDUÇÃO', '12 PARA 1', BRANCO, AMARELO, y=8)
        mostrador(tela, PX0 + 40, 92, 34, voltas % 12, m % 60, 0, coroa=False, pulseira=False, segundos=False)
        painel(tela, PX0 - 6, 136, 172, 50, borda=TRACO)
        tela.texto('MINUTOS', PX0 + 2, 142, ACO3, tam=9, contorno=PRETO)
        tela.texto(f"{int(voltas)} VOLTAS", PX0 + 70, 140, BRANCO, tam=9, contorno=PRETO)
        tela.texto('HORAS', PX0 + 2, 160, ACO3, tam=9, contorno=PRETO)
        hv = min(voltas, 12) / 12
        barra(tela, PX0 + 70, 160, 80, 8, hv % 1.0 if voltas < 12 else 1.0, AMARELO)
        tela.texto(f"{min(int(voltas), 12)}/12 DE VOLTA", PX0 + 70, 172, AMARELO, tam=9, contorno=PRETO)
        tela.texto('ACELERADO', PX0 + 92, 108, CIANO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(int(self.dur / 2.25)):
            fx.put(fx.blip(84, .05), self.t0 + (k + 1) * 2.25, .12)


# ============================================================ automático
class Automatico(Cena):
    def preparar(self):
        self.M = peca('mapa')
        dt = 1 / 240.0
        n = int(self.dur / dt) + 2
        self.ts = np.arange(n) * dt
        al = np.array([self.braco(t) for t in self.ts])
        dal = np.gradient(al, dt)
        phi, w = math.radians(90), 0.0
        ph = np.zeros(n); carga = np.zeros(n)
        q = .55
        for i in range(n):
            # rotor = pêndulo no eixo; atrito com a caixa (que gira com o braço)
            acc = -38.0 * math.cos(phi) - 2.2 * (w - dal[i])
            w += acc * dt; phi += w * dt
            ph[i] = phi
            rel = abs(w - dal[i])
            if self.ts[i] > 1.0: q = min(1.0, q + rel * dt * .018)
            carga[i] = q
        self.al, self.ph, self.cg = al, ph, carga

    def braco(self, t):
        return math.radians(28 * math.sin(2 * math.pi * t / 1.5) + 22 * math.sin(2 * math.pi * t / 4.1 + 1))

    def em(self, arr, t):
        return float(np.interp(t, self.ts, arr))

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        M = self.M
        q = self.em(self.cg, t)
        A = M.angulos(TIQUES_S * t)
        roda(tela, 150, 104, 106, 0, 0, 'aco', perfil='liso', furo=None)
        roda(tela, 150, 104, 103, 0, 0, 'acoesc', perfil='liso', furo=None)
        M.desenhar(tela, TIQUES_S * t)
        # o rotor (meia-lua) gira em volta do centro, no referencial da caixa
        rel = math.degrees(self.em(self.ph, t) - self.em(self.al, t))
        Mk = Mascara()
        pts = [(150 + math.cos(math.radians(rel - 90 + k * 3)) * 96, 104 + math.sin(math.radians(rel - 90 + k * 3)) * 96)
               for k in range(61)]
        poligono(Mk, pts + [(150, 104)], 1)
        Mk2 = Mascara(); Mk2.disco(150, 104, 26)
        Mk.buf &= ~Mk2.buf
        Mk.disco(150, 104, 12)
        a = math.radians(rel)
        linha_grossa(Mk, 150, 104, 150 + math.cos(a) * 40, 104 + math.sin(a) * 40, 10, 1)
        pintar_tela(tela, Mk, 'rotor', cx=150, cy=104, R=96)
        # gravação simples no rotor (riscos concêntricos), sem marca
        for r in (60, 74):
            for k in range(0, 61, 2):
                b = math.radians(rel - 90 + k * 3)
                tela.px(150 + math.cos(b) * r, 104 + math.sin(b) * r, OLEO0)
        rubi(tela, 150, 104, 3.2)
        cheia = q >= .999
        if VERTICAL:
            hud_vertical(tela, [(f"MOLA {int(round(q * 100))}%", VERDE if not cheia else AMARELO)], x=150)
            return
        etiqueta(tela, 'ROTOR', 8, 14, int(150 + math.cos(math.radians(rel)) * 70), int(104 + math.sin(math.radians(rel)) * 70), AMARELO)
        # braço com o relógio, balançando (no alto do painel)
        bx, by = PX0 + 6, 52
        al = self.em(self.al, t) * .8
        P = lambda d: (bx + math.cos(al) * d, by + math.sin(al) * d * .5)
        Mk = Mascara(); linha_grossa(Mk, *P(0), *P(70), 15, 1); pintar_tela(tela, Mk, 'azul', cx=bx + 30, cy=by, R=40)
        Mk = Mascara(); linha_grossa(Mk, *P(66), *P(128), 11, 1); Mk.disco(*P(134), 8)
        pintar_tela(tela, Mk, 'pele', cx=bx + 100, cy=by, R=40)
        wx, wy = P(104)
        Mk = Mascara(); linha_grossa(Mk, *P(100), *P(108), 13, 1); pintar_tela(tela, Mk, 'couro')
        tela.disco(wx, wy, 6, PRETO); tela.disco(wx, wy, 5, ACO2); tela.disco(wx, wy, 3.5, FUNDO2)
        tela.linha(wx, wy, wx + math.cos(math.radians(rel)) * 3, wy + math.sin(math.radians(rel)) * 3, AMARELO)
        tela.texto('O BRAÇO MEXE', PX0, 8, ACO3, tam=9, contorno=PRETO)
        painel(tela, PX0 - 6, 96, 172, 56, borda=AMARELO if cheia else VERDE)
        tela.texto('MOLA REAL', PX0 + 2, 102, ACO3, tam=9, contorno=PRETO)
        barra(tela, PX0 + 2, 116, 108, 10, q, AMARELO if cheia else VERDE)
        tela.texto(f"{int(round(q * 100))}%", PX0 + 160, 114, BRANCO, tam=17, centro='d', contorno=PRETO)
        if cheia:
            tela.texto('CHEIA: A EMBREAGEM', PX0 + 2, 130, AMARELO, tam=9, contorno=PRETO)
            tela.texto('DESLIZA', PX0 + 2, 140, AMARELO, tam=9, contorno=PRETO)
        else:
            tela.texto('DANDO CORDA...', PX0 + 2, 132, VERDE, tam=9, contorno=PRETO)
        tela.texto('PARADO E CHEIO, ANDA', PX0, 164, ACO3, tam=9, contorno=PRETO)
        tela.texto('CERCA DE 2 DIAS', PX0, 176, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        ult = 0
        for i in range(0, len(self.ts), 4):
            k = int(self.cg[i] * 400)
            if k > ult and self.cg[i] < .999:
                fx.put(tique(fx, 1900), self.t0 + self.ts[i], .1, .2)
                ult = k
        for t, k in cruzamentos(lambda t: TIQUES_S * t, 0, self.dur):
            if k % 2 == 0: fx.put(tique(fx, 3400), self.t0 + t, .08)


# ============================================================ precisão
class Precisao(Cena):
    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        vert = VERTICAL
        pos = ((150, 64), (150, 156)) if vert else ((78, 96), (222, 96))
        R = 44 if vert else 54
        seg = 30 + t
        # mecânico: o ponteiro anda em 8 passos por segundo; quartzo: 1 salto por segundo
        mostrador(tela, pos[0][0], pos[0][1], R, 10, 9 + seg / 60, math.floor(seg * 8) / 8, pulseira=False)
        mostrador(tela, pos[1][0], pos[1][1], R, 10, 9 + seg / 60, math.floor(seg), pulseira=False, cor_ponteiro=CIANO)
        if not vert:
            rotulo(tela, 'MECÂNICO', pos[0][0], 164, AMARELO, 17, centro=True)
            rotulo(tela, '8 PASSOS/S', pos[0][0], 184, ACO3, 9, centro=True)
            rotulo(tela, 'QUARTZO', pos[1][0], 164, CIANO, 17, centro=True)
            rotulo(tela, '1 SALTO/S', pos[1][0], 184, ACO3, 9, centro=True)
        if vert:
            hud_vertical(tela, [('-4 A +6 S/DIA', AMARELO)], x=150)
            return
        titulo_painel(tela, 'ERRO POR DIA', None, BRANCO, y=8)
        # régua de -10 a +10 s por dia
        x0, x1, y = PX0 + 4, PX0 + 160, 50
        esc = lambda v: x0 + (v + 10) / 20 * (x1 - x0)
        tela.ret(x0, y, x1 - x0, 1, ACO2)
        for v in (-10, -5, 0, 5, 10):
            tela.ret(int(esc(v)), y - 2, 1, 5, ACO2)
            tela.texto(f"{v:+d}" if v else "0", int(esc(v)), y + 6, ACO2, tam=9, centro=True)
        tela.texto('SEGUNDOS', PX0 + 82, y + 18, ACO1, tam=9, centro=True)
        faixas = []
        if t >= 8.8: faixas.append(('CRONÔMETRO MECÂNICO', -4, 6, AMARELO, 80))
        if t >= 26.8: faixas.append(('QUARTZO COMUM', -.5, .5, CIANO, 118))
        for nome, a, b, cor, yy in faixas:
            tela.texto(nome, PX0, yy, cor, tam=9, contorno=PRETO)
            tela.ret(int(esc(a)), yy + 12, max(2, int(esc(b) - esc(a))), 8, cor)
            tela.ret_vazado(int(esc(a)), yy + 12, max(2, int(esc(b) - esc(a))), 8, PRETO)
            v = (a + b) / 2 + (b - a) / 2 * math.sin(t * 1.7 + yy)
            tela.ret(int(esc(v)), yy + 10, 1, 12, BRANCO)
        if 8.8 <= t:
            tela.texto('-4 A +6 S POR DIA', PX0, 102, AMARELO, tam=9, contorno=PRETO)
        if t >= 26.8:
            tela.texto('~15 S POR MÊS', PX0, 140, CIANO, tam=9, contorno=PRETO)
        if 17.8 <= t:
            painel(tela, PX0 - 6, 154, 172, 36, borda=TRACO)
            tela.texto('TESTE: 15 DIAS,', PX0 + 2, 160, BRANCO, tam=9, contorno=PRETO)
            tela.texto('5 POSIÇÕES, 3 TEMPERATURAS', PX0 + 2, 172, BRANCO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for k in range(int(self.dur)):
            fx.put(tique(fx, 2400), self.t0 + k + .001, .12, .4)
        for k in range(int(self.dur * 8)):
            if k % 2 == 0: fx.put(tique(fx, 3400), self.t0 + k / 8, .06, -.4)


# ============================================================ história
class Historia(Cena):
    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        # relógio de bolso antigo, genérico (argola em cima)
        cx, cy = 110, 100
        tela.anel(cx, cy - 66, 9, PRETO, 2); tela.anel(cx, cy - 66, 8, LATAO, 1)
        Mk = Mascara(); Mk.ret(cx - 5, cy - 62, 10, 8); pintar_tela(tela, Mk, 'latao')
        roda(tela, cx, cy, 58, 0, 0, 'latao', perfil='liso', furo=None)
        M, x0, y0 = D.mascara_roda(cx, cy, 50, 0, 0, perfil='liso', furo=None)
        pintar(tela, M, x0, y0, 'mostr', cx=cx, cy=cy, R=50, chanfro=False)
        tela.disco(cx, cy, 48, CERAMICA)
        for k in range(12):
            a = math.radians(k * 30 - 90)
            tela.ret(int(cx + math.cos(a) * 41) - 1, int(cy + math.sin(a) * 41) - 1, 3, 3, OLEO0)
        # um ponteiro só (os primeiros relógios eram assim), andando
        a = math.radians(t * 20 - 90)
        tela.linha(cx, cy, cx + math.cos(a) * 34, cy + math.sin(a) * 34, OLEO0)
        tela.linha(cx + 1, cy, cx + 1 + math.cos(a) * 34, cy + math.sin(a) * 34, OLEO0)
        tela.disco(cx, cy, 3, OLEO0)
        # linha do tempo embaixo
        y = 186
        tela.ret(10, y, 280, 1, ACO2)
        for ano in (1700, 1750, 1800, 1850, 1900, 1950, 2000):
            x = 10 + (ano - 1700) / 330 * 280
            tela.ret(int(x), y - 3, 1, 7, ACO2)
            tela.texto(str(ano), int(x), y + 6, ACO2, tam=9, centro=True)
        if t >= 7.8:
            x = 10 + (1754 - 1700) / 330 * 280
            u = ease((t - 7.8) / .5)
            tela.ret(int(x) - 1, y - 12, 3, 12, AMARELO)
            rotulo(tela, '1754', int(x), int(y - 30 * u), AMARELO, 17, centro=True)
        if t >= 15.8:
            xa = 10 + (1800 - 1700) / 330 * 280
            xb = 290
            u = ease((t - 15.8) / 1.5)
            tela.ret(int(xa), y - 6, int((xb - xa) * u), 4, VERDE)
            rotulo(tela, 'ESCAPE DE ÂNCORA', 200, 150, VERDE, 9, centro=True)
        if VERTICAL:
            hud_vertical(tela, [('1754', AMARELO)], x=150)
            return
        titulo_painel(tela, 'ERRO POR DIA', None, BRANCO, y=8)
        painel(tela, PX0 - 6, 34, 172, 44, borda=VERMELHO)
        tela.texto('BOLSO, ANTIGO', PX0 + 2, 40, ACO3, tam=9, contorno=PRETO)
        tela.texto('~15 MIN', PX0 + 2, 54, VERMELHO, tam=17, contorno=PRETO)
        if t >= 15.8:
            painel(tela, PX0 - 6, 90, 172, 44, borda=VERDE)
            tela.texto('MECÂNICO BOM, HOJE', PX0 + 2, 96, ACO3, tam=9, contorno=PRETO)
            tela.texto('ALGUNS SEGUNDOS', PX0 + 2, 110, VERDE, tam=9, contorno=PRETO)

    def sons(self, fx):
        fx.put(fx.sino(76, 1.0), self.t0 + 7.8, .25)
        fx.put(fx.sino(83, 1.0), self.t0 + 15.8, .2)
        for k in range(int(self.dur * 5 / 2)):
            fx.put(tique(fx, 2400), self.t0 + k * .4, .07)


# ============================================================ resumo
class Resumo(Cena):
    ETAPAS = [('MOLA REAL', 'GUARDA', VERDE, 'tambor'), ('RODAS', 'LEVAM E CONTAM', LATAO, 'rodas'),
              ('ESCAPE', 'SOLTA AOS POUCOS', CIANO, 'escape'), ('BALANÇO', 'MARCA O PASSO', ROSA, 'balanco')]

    def preparar(self):
        self.M = peca('mapa')

    def desenhar(self, tela, t, tg):
        fundo_bancada(tela)
        tau = TIQUES_S * t
        self.M.desenhar(tela, tau)
        if t < 19.8: k_on = (0 if t < 5.0 else 1) if t < 9.8 else (2 if t < 14.8 else 3)
        else: k_on = int(t / self.spb) % 4
        if VERTICAL:
            hud_vertical(tela, [(f"TIQUES {milhar(math.floor(tau))}", AMARELO)], x=150)
            return
        A = self.M.ancoras()
        for j, (a, b, cor, nome) in enumerate(self.ETAPAS):
            y = 10 + j * 32
            on = j == k_on
            painel(tela, PX0 - 6, y, 172, 26, borda=cor if on else TRACO)
            tela.texto(a, PX0 + 2, y + 4, cor if on else ACO2, tam=9, contorno=PRETO)
            tela.texto(b, PX0 + 2, y + 14, BRANCO if on else ACO1, tam=9, contorno=PRETO)
            if j < 3: seta(tela, PX0 + 150, y + 27, 0, 1, cor if on else TRACO, 4)
            if on: fio(tela, PX0 - 6, y + 13, *A[nome], cor)
        hud(tela, math.floor(tau), None, y=144)
        if t >= 19.8:
            tela.texto('POR DIA: 691.200', PX0, 184, AMARELO, tam=9, contorno=PRETO)

    def sons(self, fx):
        for t, k in cruzamentos(lambda t: TIQUES_S * t, 0, self.dur):
            fx.put(tique(fx, 3400 if k % 2 == 0 else 2600), self.t0 + t, .1)


# ============================================================ fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS COMO FUNCIONA'], SEED, baixo=True))
        self.E = peca('balanco')

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            fundo_bancada(tela)
            tela.buf[PALCO_H:] = FUNDO
            tela.texto("OBRIGADO POR ASSISTIR!", W // 2, 20, BRANCO, tam=17, centro=True, contorno=PRETO)
            tela.texto("NOSSO MUNDO PIXEL", W // 2, 40, AMARELO, tam=9, centro=True, contorno=PRETO)
            E = self.E
            bx, by = E.bx, E.by
            E.bx, E.by = W // 2, 130
            E.desenhar_balanco(tela, E.beta(t / self.spb), espiral=True)
            E.bx, E.by = bx, by

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .75)


CENAS = dict(gancho=Gancho, titulo=Titulo, abrir=Abrir, pecas=Pecas, mola=Mola, engrenagens=Engrenagens,
             escape=EscapeCena, balanco=Balanco, batida=Batida, rubis=Rubis, ponteiros=Ponteiros,
             automatico=Automatico, precisao=Precisao, historia=Historia, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep09_motor as EP
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
