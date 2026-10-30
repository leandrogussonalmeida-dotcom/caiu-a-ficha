#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep03 — A jornada da sua mala no aeroporto (PT-BR).

Cada capítulo é uma classe com:
  desenhar(tela, t, tg)   t = segundos desde o começo do capítulo, tg = global
  sons(fx)                o que se ouve (esteira, bipe do leitor, bandeja, baque)
A protagonista é uma mala laranja com a etiqueta 0 042 314159 (exemplo). O
painel da direita mostra ETAPA n DE 8, a distância percorrida e o relógio da
viagem de exemplo; nos cortes verticais ele vira uma tarja no alto do recorte.

    python3 ep03_motor.py <saida.mp4>                     # o episódio inteiro
    python3 ep03_motor.py <saida.mp4> triagem patio       # só esses capítulos
    python3 ep03_motor.py --folha <saida.png> [t1 t2 ...] # 2 quadros por capítulo (ou só os instantes)
"""
import math, sys
import numpy as np
import longo as LG
from longo import (W, H, PALCO_H, ease, suave, dither, poligono, linha_grossa, texto_marcado, painel,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)
import pixelfonte as PF
import ritmo_marca as RM
import idioma
import ep03_desenho as D
from ep03_roteiro import CAPITULOS, LEGENDAS, CORTES, PREFIXO

SEED, RAIZ = 2603, 45
GANHO_MUSICA = -10.0
GANHO_EFEITOS = 0.0
LUFS = -16.0
VERTICAL = False              # True durante os cortes verticais: some o que não cabe em 180 px

PX0 = 306                     # coluna do texto do painel
ETAPAS = ['DESPACHO', 'ESTEIRA', 'INSPEÇÃO', 'TRIAGEM', 'MONTAGEM', 'PÁTIO', 'VOO', 'CHEGADA']
H19 = 19 * 60
# distância (m) e relógio (min) no começo e no fim de cada etapa: viagem de exemplo
ROTA = {
    'despacho': (0, 5, H19, H19 + 3),
    'etiqueta': (5, 5, H19 + 3, H19 + 3),
    'esteira': (5, 320, H19 + 3, H19 + 7),
    'inspecao': (320, 360, H19 + 7, H19 + 9),
    'triagem': (360, 900, H19 + 9, H19 + 14),
    'montagem': (900, 930, H19 + 14, H19 + 40),
    'patio': (930, 1650, H19 + 40, H19 + 65),
    'voo': (1650, 901650, H19 + 75, H19 + 165),
    'chegada': (901650, 902100, H19 + 170, H19 + 190),
    'resumo': (902100, 902100, H19 + 190, H19 + 190),
}


def fmt_dist(m):
    if m < 1000: return f"{idioma.milhar(m)} M"
    return f"{idioma.decimal(m / 1000.0, 1)} KM"


def fmt_hora(mi):
    mi = int(mi)
    return f"{(mi // 60) % 24:02d}:{mi % 60:02d}"


def tx(tela, s, x, y, cor, tam=9, centro=False):
    tela.texto(s, int(x), int(y), cor, tam=tam, centro=centro, contorno=PRETO)


def escurecer(tela, x, y, w, h):
    """Apaga metade dos pixels de uma área em xadrez (fora de foco)."""
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(W, int(x + w)), min(H, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[(xx + yy) % 2 == 0] = FUNDO


def interp(marcos, t):
    """Interpolação suave entre marcos [(t, valor)]."""
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * suave((t - a) / max(1e-6, b - a))
    return marcos[-1][1]


def interp_lin(marcos, t):
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * (t - a) / max(1e-6, b - a)
    return marcos[-1][1]


def ao_longo(pts, d):
    """Ponto a distância d ao longo da polilinha `pts` (None fora dela)."""
    if d < 0: return None
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        if d <= L:
            u = d / L
            return ax + (bx - ax) * u, ay + (by - ay) * u
        d -= L
    return None


def comprimento(pts):
    return sum(math.hypot(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(pts, pts[1:]))


def texto_grande(tela, s, x, y, cor, esc=5, contorno=PRETO):
    """Texto em escala maior que 3x (o código de destino na etiqueta)."""
    m = PF.mascara(s, esc)
    yy = int(y) + 1 - PF.TOPO * esc - 1
    if contorno is not None:
        tela._blit(PF.dilatar(m, 1), int(x) - 1, yy - 1, contorno)
    tela._blit(m, int(x), yy, cor)
    return m.shape[1]


def m3(tela, x, y, num, cor):
    """'4,5 M³' com o 3 pequeno no alto (a fonte não tem ³)."""
    s = f"{num} M"
    tx(tela, s, x, y, cor, 17)
    w = tela.largura_texto(s, 17)
    tx(tela, '3', x + w + 2, y - 2, cor, 9)


# ======================================================================= etiqueta grande
TAG = dict(x=12, y=40, w=280, h=116)


def pos_digitos(tela, x0, y, tam=17):
    """x de cada dígito da placa '0 042 314159' escrita a partir de x0."""
    s = '0 042 314159'
    xs = []
    for i, ch in enumerate(s):
        if ch == ' ': continue
        xs.append((x0 + (tela.largura_texto(s[:i], tam) + PF.ESPACO * PF.escala_de(tam) if i else 0),
                   tela.largura_texto(ch, tam)))
    return s, xs


def etiqueta_grande(tela, t, dy=0, laser=None, ate_barras=None, stub=0.0):
    """A etiqueta de bagagem em close. Devolve as posições úteis
    (caixas dos dígitos, do código de destino e das barras)."""
    x, y, w, h = TAG['x'], TAG['y'] + dy, TAG['w'], TAG['h']
    # sombra e corpo
    tela.ret(x + 3, y + 3, w, h, FUNDO)
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    tela.ret(x, y, w, h, CERAMICA)
    dither(tela, x, y + h - 10, w, 10, CERAMICA, ACO4)
    tela.ret(x, y, w, 6, VERDE); tela.ret(x, y + 6, w, 1, AGUA1)
    tela.ret(x, y + h - 4, w, 4, VERDE)
    tela.ret(x + 1, y + 1, w - 2, 1, CHAMA0) if False else None
    # código de destino enorme
    wd = texto_grande(tela, D.DESTINO, x + 12, y + 18, PRETO, esc=4, contorno=None)
    caixa_dest = (x + 8, y + 14, wd + 9, 36)
    tela.texto('VOO 314', x + 12, y + 64, PRETO, tam=17)
    tela.texto('PARTIDA 20:15', x + 12, y + 86, OLEO0, tam=9)
    tela.texto('A. EXEMPLO', x + 12, y + 97, OLEO0, tam=9)
    # código de barras de verdade (Interleaved 2 of 5) e o número por extenso
    bx, by, bh = x + 96, y + 16, 46
    lb = D.largura_barras(D.PLACA, 2, 4)
    D.desenhar_barras(tela, bx, by, bh, D.PLACA, 2, 4, PRETO, ate=ate_barras)
    s, xs = pos_digitos(tela, 0, 0)
    larg = tela.largura_texto(s, 17)
    x0 = bx + lb // 2 - larg // 2
    tela.texto(s, x0, by + bh + 6, PRETO, tam=17)
    caixas = [(x0 + dx - 2, by + bh + 3, dw + 4, 20) for dx, dw in xs]
    # canhoto picotado à direita
    xp = x + w - 30
    for yy in range(y + 8, y + h - 6, 4): tela.ret(xp, yy, 1, 2, ACO2)
    if stub <= 0:
        for k in range(4): tela.ret(xp + 6, y + 30 + k * 6, 18, 2, PRETO)
    if laser is not None:
        lx = int(bx + laser * lb)
        tela.ret(lx - 1, by - 6, 3, bh + 12, VERMELHO)
        tela.ret(lx, by - 6, 1, bh + 12, CHAMA0)
        tela.disco(lx, by - 7, 2.5, VERMELHO)
    return dict(digitos=caixas, destino=caixa_dest, barras=(bx, by, lb, bh), canhoto=xp)


def canhoto(tela, x, y, num_ok=True):
    """O comprovante que fica com o passageiro."""
    tela.ret(x - 1, y - 1, 52, 28, PRETO)
    tela.ret(x, y, 50, 26, CERAMICA)
    tela.ret(x, y, 50, 3, VERDE)
    D.desenhar_barras(tela, x + 4, y + 6, 10, D.PLACA[:6] + '00', 1, 2, PRETO)
    tela.texto('PXL', x + 4, y + 17, PRETO, tam=9)


# ======================================================================= base
class Cena:
    legenda = True
    brilho = None
    ETAPA, NOME = None, ''

    def __init__(self, cap, trilha, fx):
        self.c, self.T, self.fx = cap, trilha, fx
        self.t0, self.dur = cap['t0'], cap['dur']
        self.preparar()

    def preparar(self): pass
    def sons(self, fx): pass
    def desenhar(self, tela, t, tg): pass

    # --------------------------------------------------- recorte vertical
    def xv(self, tg):
        if not VERTICAL: return None
        caps = {c['id']: c['t0'] for c in self.T.caps}
        for c in CORTES:
            a = caps[c['de'][0]] + c['de'][1]; b = caps[c['ate'][0]] + c['ate'][1]
            if a - .05 <= tg <= b + .05: return c['x']
        return 75

    # --------------------------------------------------- distância e relógio
    def rota(self, u):
        r = ROTA.get(self.c['id'])
        if r is None or u is None: return None, None
        u = min(1.0, max(0.0, u))
        return r[0] + (r[1] - r[0]) * u, r[2] + (r[3] - r[2]) * u

    def hud(self, tela, t, tg, u=None, etapa=None, nome=None, cab=None, rodape=None):
        """Painel da direita: etapa, nome, (miolo é da cena), distância e
        relógio. Em VERTICAL, uma tarja no alto do recorte. Devolve True se a
        cena deve desenhar o miolo do painel."""
        etapa = self.ETAPA if etapa is None else etapa
        nome = nome or self.NOME
        d, mi = self.rota(u)
        xc = self.xv(tg)
        if xc is not None:
            painel(tela, xc + 2, 2, 176, 15, borda=TRACO)
            s = f"ETAPA {etapa}/8 {nome}" if etapa else (cab or nome)
            tx(tela, s, xc + 6, 6, AMARELO)
            if d is not None:
                tx(tela, fmt_dist(d), xc + 174, 6, BRANCO, centro='d')
            return False
        painel(tela, 300, 4, 177, 202, borda=TRACO, fundo=PRETO, luz=FUNDO3)
        if cab:
            tx(tela, cab, PX0, 11, BRANCO, 17)
        elif etapa:
            texto_marcado(tela, f"ETAPA *{etapa}* DE 8", PX0, 11, 17)
        for k in range(8):
            x = PX0 + k * 20
            if etapa and k + 1 < etapa: c = VERDE
            elif etapa and k + 1 == etapa: c = AMARELO if (t * 2) % 1 < .7 else CHAMA1
            else: c = FUNDO3
            tela.ret(x, 31, 16, 7, PRETO if c != FUNDO3 else TRACO)
            tela.ret(x + 1, 32, 14, 5, c)
            if c != FUNDO3: tela.ret(x + 1, 32, 14, 1, CHAMA0 if c != VERDE else ACO4)
        if nome: tx(tela, nome, PX0, 44, CIANO, 17)
        tela.ret(PX0 - 2, 62, 166, 1, TRACO)
        tela.ret(PX0 - 2, 152, 166, 1, TRACO)
        if rodape:
            for k, l in enumerate(rodape):
                tx(tela, l, PX0, 160 + k * 12, ACO2)
        elif d is not None:
            tx(tela, 'DISTÂNCIA', PX0, 161, ACO2)
            tx(tela, fmt_dist(d), 470, 158, BRANCO, 17, centro='d')
            tx(tela, 'RELÓGIO', PX0, 184, ACO2)
            tx(tela, fmt_hora(mi), 470, 181, BRANCO, 17, centro='d')
        return True

    def zumbido(self, fx, a, b, ganho=.06):
        """Ronco baixinho de esteira entre a e b (relativos ao capítulo)."""
        if b - a > .2: fx.put(fx.chiado(b - a, 60, 260, ataque=.4), self.t0 + a, ganho)


# ======================================================================= 0 gancho
class Gancho(Cena):
    PTS = [(-60, 60), (380, 60), (450, 110), (60, 110), (-10, 160), (560, 160)]

    def preparar(self):
        self.L = comprimento(self.PTS)

    def d_prota(self, t):
        return 120 + 92 * t

    def desenhar(self, tela, t, tg):
        D.fundo_bastidor(tela, t, chao=196)
        tela.ret(300, 0, W - 300, PALCO_H, FUNDO2) if False else None
        D.esteira(tela, -10, 392, 60, t, 92)
        D.rampa(tela, 380, 60, 450, 110, t, 92)
        D.esteira(tela, 52, 470, 110, t, -92)
        D.rampa(tela, 60, 110, -10, 160, t, 92)
        D.esteira(tela, -10, W + 10, 160, t, 92, chao=196)
        dp = self.d_prota(t)
        for k in range(-14, 15):
            d = dp + k * 41
            p = ao_longo(self.PTS, d)
            if p is None: continue
            x, y = p
            if k == 0: continue
            D.mala_lado(tela, x - 13, y, 26, 11, D.outra(k), t, tag=(k % 3 == 0))
        p = ao_longo(self.PTS, dp)
        if p:
            x, y = p
            # rastro de velocidade
            sent = 1 if (dp < 440 or dp > 1000) else -1
            for j in range(4):
                tela.ret(int(x - sent * (20 + j * 7)) - 3, int(y - 4 - j * 2), 6 - j, 1, ACO3)
            D.mala_lado(tela, x - 15, y, 30, 12, 'prota', t, tag=True, balanco=2)
            D.marcador(tela, x, y - 16, t, 'SUA MALA')
        if t >= 6.0 and not VERTICAL:
            u = ease((t - 6.0) / 1.2)
            painel(tela, 352, 6, 120, 44, borda=AMARELO)
            tx(tela, 'UM SÓ TERMINAL:', 360, 12, ACO3)
            tx(tela, f"{int(round(18 * u))} KM", 360, 24, AMARELO, 26)
        elif t >= 6.0:
            xc = self.xv(tg)
            u = ease((t - 6.0) / 1.2)
            painel(tela, xc + 40, 6, 100, 30, borda=AMARELO)
            tx(tela, f"{int(round(18 * u))} KM", xc + 90, 12, AMARELO, 17, centro=True)

    def sons(self, fx):
        self.zumbido(fx, 0, 12, .08)
        for k in range(12):
            fx.put(fx.clique(2200, .02), self.t0 + .3 + k * .45, .12)


# ======================================================================= 1 título
class Titulo(Cena):
    legenda = False

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        # códigos de barras ao fundo, passando devagar
        for k in range(-1, 6):
            x = int(k * 110 - (t * 14) % 110)
            D.desenhar_barras(tela, x, 18, 26, D.PLACA, 1, 3, FUNDO2)
            D.desenhar_barras(tela, x + 50, 168, 22, D.PLACA[::-1], 1, 3, FUNDO2)
        tx(tela, 'SÉRIE A JORNADA', W // 2, 52, CIANO, 9, centro=True)
        n = int(t / .045)
        for j, linha in enumerate(("A JORNADA DA", "SUA MALA")):
            larg = tela.largura_texto(linha, 26)
            vis = linha[:max(0, n - j * 12)]
            tela.texto(vis, W // 2 - larg // 2, 66 + j * 32, BRANCO if j == 0 else LARANJA, tam=26, contorno=PRETO, sombra=TRACO)
        if t > 1.2:
            tx(tela, "NO AEROPORTO", W // 2, 134, AMARELO, 17, centro=True)
        D.esteira(tela, -10, W + 10, 186, t, 70, chao=208)
        x = -40 + (t / 6.0) * (W + 80)
        D.mala_lado(tela, x, 186, 32, 13, 'prota', t, tag=True, balanco=2)
        for k in (1, 2):
            D.mala_lado(tela, x - k * 70, 186, 26, 11, D.outra(k), t)
            D.mala_lado(tela, x + k * 70, 186, 26, 11, D.outra(k + 3), t)

    def sons(self, fx):
        for k, m in enumerate((67, 72, 76)):
            fx.put(fx.blip(m, .1), self.t0 + .3 + k * .25, .18)


# ======================================================================= 2 despacho
class Despacho(Cena):
    ETAPA, NOME = 1, ETAPAS[0]
    CX = 190          # meio da mala na balança

    def preparar(self):
        rng = np.random.default_rng(31)
        self.estrelas = [(int(rng.integers(0, 296)), int(rng.integers(12, 96)), float(rng.uniform(0, 6))) for _ in range(30)]

    def peso(self, t):
        if t < 1.4: return 0.0
        u = ease((t - 1.4) / 2.2)
        return 18.4 * u + math.sin(t * 23) * .4 * (1 - u)

    def x_mala(self, t):
        if t < 36.4: return self.CX
        return self.CX + (t - 36.4) ** 1.3 * 26

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO2
        # janelão do saguão (noite)
        tela.ret(0, 6, 300, 92, FUNDO)
        dither(tela, 0, 70, 300, 28, FUNDO, FUNDO2)
        for x, y, f in self.estrelas:
            if math.sin(t * 1.5 + f) > -.3: tela.px(x, y, ACO2)
        xa = (t * 9) % 360 - 30                                     # um avião passando longe
        tela.ret(int(xa), 30, 7, 1, ACO1); tela.px(int(xa) + 7, 30, VERMELHO if int(t * 2) % 2 else FUNDO)
        for x in range(0, 300, 37):
            tela.ret(x, 6, 3, 92, FUNDO3); tela.ret(x, 6, 1, 92, TRACO)
        tela.ret(0, 6, 300, 3, FUNDO3); tela.ret(0, 96, 300, 4, FUNDO3); tela.ret(0, 96, 300, 1, TRACO)
        # painel de voos
        painel(tela, 158, 14, 128, 46, borda=ACO0)
        tx(tela, 'VOO  DESTINO  HORA', 164, 18, ACO2)
        linhas = (('314  PXL      20:15', AMARELO), ('271  RGB      20:40', ACO3), ('159  BIT      21:05', ACO3))
        for k, (l, c) in enumerate(linhas):
            if k == 0 and (t * 1.5) % 1 < .3: c = CHAMA1
            tela.texto(l, 164, 30 + k * 9, c, tam=9)
        # piso
        tela.ret(0, 196, 300, 12, FUNDO3)
        for x in range(0, 300, 24): tela.ret(x, 196, 1, 12, TRACO)
        dither(tela, 0, 200, 300, 8, FUNDO3, FUNDO2)
        # balcão
        tela.ret(28, 64, 2, 48, ACO0)
        painel(tela, 12, 52, 76, 14, borda=CIANO)
        tx(tela, 'DESPACHO 12', 16, 55, CIANO)
        D.caixa(tela, 14, 112, 112, 84, ACO1, ACO2, ACO0)
        tela.ret(12, 110, 116, 6, PRETO); tela.ret(13, 111, 114, 4, ACO3); tela.ret(13, 111, 114, 1, ACO4)
        for x in range(26, 120, 24): tela.ret(x, 122, 1, 66, ACO0)
        # monitor (de costas) e impressora de etiquetas
        D.caixa(tela, 30, 88, 32, 22, ACO0, ACO1, FUNDO3)
        tela.ret(44, 106, 4, 5, ACO0)
        D.caixa(tela, 84, 100, 34, 11, ACO2, ACO3, ACO1)
        tela.ret(90, 100, 22, 2, PRETO)
        tela.px(112, 104, VERDE if (t * 2) % 1 < .5 else AGUA0)
        # visor da balança na frente do balcão
        painel(tela, 82, 136, 40, 16, borda=ACO0)
        tela.texto(idioma.decimal(max(0.0, self.peso(t)), 1), 86, 140, VERDE, tam=9)
        # balança + esteira de saída
        tela.ret(126, 172, 128, 24, PRETO)
        D.caixa(tela, 127, 176, 126, 20, ACO0, ACO1, FUNDO3)
        vel = 0.0 if t < 36.4 else 40.0
        D.esteira(tela, 126, 300, 170, t, vel)
        for x in (150, 230):
            tela.ret(x, 180, 3, 3, ACO2)
        # parede com a boca da cortina
        tela.ret(254, 100, 46, 70, FUNDO3); tela.ret(254, 100, 2, 70, TRACO)
        tela.ret(258, 132, 42, 38, PRETO)
        tela.ret(259, 133, 40, 37, FUNDO)
        tx(tela, 'BAGAGEM', 256, 118, ACO2)
        # a mala
        cx = self.x_mala(t)
        yb = 170
        if t < 1.4:
            u = min(1.0, max(0.0, (t - .6) / .8))
            yb = 170 - 60 * (1 - u) ** 2 if u < .8 else 170 - 4 * math.sin((u - .8) / .2 * math.pi)
        puxa = 1.0 - suave((t - 3.0) / .8)
        tag = t >= 26.0
        D.mala_frente(tela, cx, yb, 1.0, 'prota', t, puxador=puxa, tag=tag, balanco=1.2)
        empurra = max(0.0, min(1.0, (cx + 14 - 258) / 20.0)) if cx + 12 > 258 else 0.0
        D.cortina(tela, 259, 133, 40, 36, t, empurra if cx < 320 else 0.0)
        # etiqueta saindo da impressora e voando até a alça
        if 21.4 <= t < 24.0:
            hgt = int(min(1.0, (t - 21.4) / 1.6) * 26)
            tela.ret(96, 100 - hgt, 12, hgt, PRETO)
            tela.ret(97, 101 - hgt, 10, hgt - 1, CERAMICA)
            tela.ret(97, 101 - hgt, 10, 2, VERDE)
            for k in range(0, hgt - 6, 3): tela.ret(98, 104 - hgt + k, 8, 1, PRETO)
        elif 24.0 <= t < 26.0:
            u = ease((t - 24.0) / 2.0)
            ax, ay = 102, 80
            bx, by = cx + 8, 170 - 32 - 3
            x = ax + (bx - ax) * u
            y = ay + (by - ay) * u - math.sin(u * math.pi) * 30
            tela.ret(int(x) - 4, int(y) - 6, 9, 13, PRETO)
            tela.ret(int(x) - 3, int(y) - 5, 7, 11, CERAMICA)
            tela.ret(int(x) - 3, int(y) - 5, 7, 2, VERDE)
        # comprovante voando para o painel
        if 29.0 <= t < 30.4 and not VERTICAL:
            u = ease((t - 29.0) / 1.4)
            canhoto(tela, int(100 + (PX0 + 40 - 100) * u), int(84 - math.sin(u * math.pi) * 40), True)
        if t < 21.4 or t >= 36.0:
            tela.texto('PESO', 0, 0, FUNDO, tam=9) if False else None
        if not VERTICAL and t > 1.2 and t < 21.4:
            tx(tela, f"{idioma.decimal(self.peso(t), 1)} KG", cx, 120, AMARELO, 9, centro=True)
        mostra = self.hud(tela, t, tg, u=suave((t - 36.4) / 5.0))
        if mostra: self.miolo(tela, t)
        elif t > 1.2 and t < 21.4:
            xc = self.xv(tg)
            tx(tela, f"{idioma.decimal(self.peso(t), 1)} KG", cx, 120, AMARELO, 17, centro=True)

    def miolo(self, tela, t):
        if t < 21.4:
            p = max(0.0, self.peso(t))
            tx(tela, 'PESO NA BALANÇA', PX0, 68, ACO3)
            tx(tela, f"{idioma.decimal(p, 1)} KG", PX0, 80, AMARELO, 26)
            x0, y0, L = PX0, 114, 156
            k = L / 32.0
            tela.ret(x0 - 1, y0 - 1, L + 2, 10, PRETO)
            tela.ret(x0, y0, L, 8, FUNDO2)
            tela.ret(x0, y0, int(min(32, p) * k), 8, VERDE)
            tela.ret(x0, y0, int(min(32, p) * k), 1, ACO4)
            x23 = x0 + int(23 * k)
            tela.ret(x23, y0 - 4, 2, 16, AMARELO)
            tela.ret(x0 + L - 2, y0 - 4, 2, 16, VERMELHO)
            tx(tela, '23', x23 - 5, y0 - 15, AMARELO)
            tx(tela, '32', x0 + L - 12, y0 - 15, VERMELHO)
            tx(tela, '23 KG: RECOMENDADO', PX0, 128, AMARELO)
            tx(tela, '32 KG: MÁXIMO COMUM', PX0, 139, VERMELHO)
        elif t < 29.0:
            tx(tela, 'ETIQUETA IMPRESSA', PX0, 68, ACO3)
            tela.ret(PX0 - 1, 81, 158, 40, PRETO)
            tela.ret(PX0, 82, 156, 38, CERAMICA)
            tela.ret(PX0, 82, 156, 3, VERDE)
            tela.texto('PXL', PX0 + 6, 90, PRETO, tam=26)
            D.desenhar_barras(tela, PX0 + 70, 88, 18, D.PLACA, 1, 2, PRETO)
            tela.texto('0 042 314159', PX0 + 70, 109, PRETO, tam=9)
            tx(tela, 'PRESA NA ALÇA', PX0, 130, ACO3)
        else:
            tx(tela, 'SEU COMPROVANTE', PX0, 68, ACO3)
            canhoto(tela, PX0, 82)
            tx(tela, 'NÚMERO', PX0 + 58, 84, ACO2)
            tx(tela, '0042', PX0 + 58, 96, BRANCO)
            tx(tela, '314159', PX0 + 58, 106, BRANCO)
            tx(tela, 'O MESMO DA', PX0, 120, AMARELO)
            tx(tela, 'ETIQUETA DA MALA', PX0, 131, AMARELO)

    def sons(self, fx):
        fx.put(fx.explosao(.4), self.t0 + 1.35, .25)
        for k in range(8):
            fx.put(fx.blip(84 + (k % 2) * 2, .03), self.t0 + 1.5 + k * .25, .05)
        fx.put(fx.blip(91, .12), self.t0 + 3.7, .14)
        fx.put(fx.chiado(2.4, 1500, 5000), self.t0 + 21.4, .12)            # impressora
        fx.put(fx.clique(2500, .03), self.t0 + 26.0, .3)
        fx.put(fx.chiado(.6, 2000, 6000), self.t0 + 29.0, .08)
        self.zumbido(fx, 36.4, 42.0, .1)


# ======================================================================= 3 etiqueta
class Etiqueta(Cena):
    ETAPA, NOME = 1, 'A ETIQUETA'

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        dy = int(round(math.sin(t * 1.3) * 1.5))
        laser = None
        if 21.4 <= t < 26.0:
            laser = ((t - 21.4) / 1.4) % 1.0
        P = etiqueta_grande(tela, t, dy, laser=laser)
        cx = P['digitos']
        # destaques
        if t < 7.4:
            if (t * 2) % 1 < .75:
                a, b = cx[0], cx[-1]
                tela.ret(a[0], a[1] + a[3], b[0] + b[2] - a[0], 2, AMARELO)
            if not VERTICAL: self.fio(tela, (cx[0][0] + cx[-1][0] + cx[-1][2]) // 2, cx[0][1] + cx[0][3] + 2, 88, AMARELO, baixo=True)
        elif t < 14.4:
            self.moldura(tela, cx[0], AMARELO, t)
            if not VERTICAL: self.fio(tela, cx[0][0] + cx[0][2] // 2, cx[0][1] + cx[0][3], 80, AMARELO, baixo=True)
        elif t < 21.4:
            a = self.uniao(cx[1:4]); b = self.uniao(cx[4:])
            self.moldura(tela, a, CIANO, t)
            self.moldura(tela, b, VERDE, t + .3)
            if not VERTICAL:
                self.fio(tela, a[0] + a[2] // 2, a[1] + a[3], 82, CIANO, baixo=True)
                self.fio(tela, b[0] + b[2] // 2, b[1] + b[3], 112, VERDE, baixo=True)
        elif t < 29.0:
            if t >= 25.0:
                self.moldura(tela, P['destino'], LARANJA, t)
                if not VERTICAL: self.fio(tela, P['destino'][0] + P['destino'][2], P['destino'][1] + 20, 122, LARANJA)
        else:
            bx, by, lb, bh = P['barras']
            if not VERTICAL:
                # pacotes de dados indo da etiqueta para a mensagem
                ax, ay = bx + lb, by + bh // 2
                for k in range(5):
                    u = ((t - 29.0) * .8 + k / 5) % 1.0
                    x = ax + (PX0 - 8 - ax) * u
                    tela.ret(int(x), ay - 1, 3, 3, CIANO)
                tela.linha(ax, ay, PX0 - 8, ay, TRACO) if False else None
        if self.hud(tela, t, tg, u=0.0):
            self.miolo(tela, t)

    def uniao(self, cxs):
        a, b = cxs[0], cxs[-1]
        return (a[0], a[1], b[0] + b[2] - a[0], a[3])

    def moldura(self, tela, c, cor, t):
        x, y, w, h = c
        if (t * 2.5) % 1 < .8:
            tela.ret_vazado(x - 1, y - 1, w + 2, h + 2, cor)
            tela.ret_vazado(x - 2, y - 2, w + 4, h + 4, PRETO)

    def fio(self, tela, x, y, y_painel, cor, baixo=False):
        """Fio da peça até o painel (sai para baixo e vai em L até a borda)."""
        x, y = int(x), int(y)
        yb = 170 if baixo else y
        if baixo:
            tela.ret(x, y + 2, 1, yb - y - 2, cor)
            tela.ret(x, yb, 296 - x, 1, cor)
            tela.ret(296, y_painel + 4, 1, yb - y_painel - 4 + 1, cor) if yb > y_painel else tela.ret(296, yb, 1, y_painel - yb + 4, cor)
            tela.ret(296, y_painel + 4, 6, 1, cor)
        else:
            tela.ret(x, y, 296 - x, 1, cor)
            lo, hi = sorted((y, y_painel + 4))
            tela.ret(296, lo, 1, hi - lo + 1, cor)
            tela.ret(296, y_painel + 4, 6, 1, cor)
        tela.disco(x, y, 1.6, cor)

    def miolo(self, tela, t):
        if t < 7.4:
            tx(tela, 'A PLACA DA MALA', PX0, 68, ACO3)
            tx(tela, '10 DÍGITOS', PX0, 84, AMARELO, 17)
            tx(tela, '0 042 314159', PX0, 108, BRANCO, 17)
            tx(tela, '(NÚMERO DE EXEMPLO)', PX0, 130, ACO2)
        elif t < 14.4:
            tx(tela, '1º DÍGITO: O TIPO', PX0, 68, ACO3)
            for k, (n, s) in enumerate((('0', 'NORMAL'), ('1', 'RESERVA'), ('2', 'URGENTE'))):
                y = 82 + k * 20
                c = AMARELO if k == 0 else ACO2
                tela.ret(PX0, y, 14, 16, c if k == 0 else FUNDO2)
                tela.texto(n, PX0 + 3, y + 2, PRETO if k == 0 else ACO3, tam=17)
                tx(tela, s, PX0 + 22, y + 2, c, 17)
        elif t < 21.4:
            tx(tela, '042', PX0, 70, CIANO, 17)
            tx(tela, 'COMPANHIA AÉREA', PX0 + 42, 70, CIANO)
            tx(tela, '(EXEMPLO)', PX0 + 42, 80, ACO2)
            tx(tela, '314159', PX0, 100, VERDE, 17)
            tx(tela, 'NÚMERO DA MALA', PX0, 120, VERDE)
            tx(tela, 'NAQUELE DIA', PX0, 131, ACO2)
        elif t < 29.0:
            tx(tela, 'LEITOR DE BARRAS', PX0, 68, ACO3)
            n = int(min(10, max(0, (t - 21.6) / 2.6 * 10)))
            s = D.PLACA[:n] + '_' * (10 - n)
            tx(tela, s, PX0, 82, VERMELHO if n < 10 else BRANCO, 17)
            if t >= 25.0:
                tx(tela, 'PXL', PX0, 106, LARANJA, 26)
                tx(tela, 'AEROPORTO DE', PX0 + 62, 108, LARANJA)
                tx(tela, 'CHEGADA', PX0 + 62, 119, LARANJA)
                tx(tela, '(CÓDIGO DE EXEMPLO)', PX0, 136, ACO2)
        else:
            tx(tela, 'MENSAGEM', PX0, 68, ACO3)
            linhas = (('PLACA', '0042314159'), ('VOO', '314'), ('DESTINO', 'PXL'), ('PASSAGEIRO', 'A. EXEMPLO'))
            for k, (a, b) in enumerate(linhas):
                if t < 29.6 + k * .9: break
                y = 82 + k * 15
                tx(tela, a, PX0, y, ACO2)
                tx(tela, b, 468, y, CIANO if k else BRANCO, centro='d')

    def sons(self, fx):
        for k in range(4):
            fx.put(fx.chiado(.5, 2000, 6000), self.t0 + 21.4 + k * 1.4, .06)
        fx.put(fx.blip(88, .1), self.t0 + 24.2, .15)
        for k in range(4):
            fx.put(fx.blip(76 + k * 2, .05), self.t0 + 29.6 + k * .9, .1)


# ======================================================================= 4 esteira
class Esteira(Cena):
    ETAPA, NOME = 2, ETAPAS[1]
    V = 46.0
    XS = [-120, -60, 0, 50, 110, 175, 226, 280]       # posições na tela (a 110 é a nossa)
    PORTICO = 600

    def sx_portico(self, t):
        return self.PORTICO - self.V * t

    def leitura(self, i, t):
        """Instante em que a mala i passa sob o pórtico."""
        cx = self.XS[i] + 15
        return (self.PORTICO + 25 - cx) / self.V

    def desenhar(self, tela, t, tg):
        s = self.V * t
        D.fundo_bastidor(tela, t, scroll=s, chao=196)
        # esteira de cima, no fundo (outras malas, outro sentido)
        D.esteira(tela, -10, W + 10, 96, t, -30, fase=int(-s))
        for k in range(-2, 12):
            x = (k * 52 + t * 30 - s) % 620 - 60
            D.mala_lado(tela, x, 96, 22, 9, D.outra(k + 2), t, rodas=False)
        escurecer(tela, 0, 70, W, 40)
        D.esteira(tela, -10, W + 10, 150, t, 0.0, chao=196, fase=int(-s))
        # pórtico de leitura (parte de trás)
        sx = self.sx_portico(t)
        if -70 < sx < 320:
            for px_ in (sx, sx + 50):
                tela.ret(px_ - 1, 74, 6, 76, PRETO); tela.ret(px_, 74, 4, 76, ACO1); tela.ret(px_, 74, 1, 76, ACO3)
        # malas
        for i, x in enumerate(self.XS):
            prota = i == 4
            D.mala_lado(tela, x, 150, 30, 12, 'prota' if prota else D.outra(i), t, tag=True, balanco=.6)
            if i == 6:      # etiqueta amassada: um borrão cinza por cima
                tela.ret(x + 19, 136, 7, 8, ACO2); tela.px(x + 21, 138, ACO0); tela.px(x + 23, 141, ACO0)
        # pórtico (frente) e o feixe
        if -70 < sx < 320:
            D.caixa(tela, sx - 8, 62, 66, 16, ACO1, ACO3, ACO0)
            for k in range(6):
                tela.ret(sx - 2 + k * 10, 77, 4, 2, CIANO)
            sob = None
            for i, x in enumerate(self.XS):
                if sx - 4 <= x + 15 <= sx + 54: sob = i
            if sob is not None:
                for k in range(6):
                    a = sx + 2 + k * 9
                    xb = self.XS[sob] + 5 + ((k * 7 + int(t * 40)) % 22)
                    tela.linha(a, 79, xb, 138, VERMELHO)
                ok = sob != 6
                painel(tela, sx - 4, 44, 58, 14, borda=VERDE if ok else VERMELHO)
                tx(tela, 'LIDA' if ok else 'SEM LEITURA', sx + 25, 47, VERDE if ok else VERMELHO, centro=True)
            else:
                for k in range(6):
                    if (t * 3 + k) % 2 < 1: tela.px(sx + 2 + k * 9, 82, VERMELHO)
        D.marcador(tela, self.XS[4] + 15, 134, t)
        if self.hud(tela, t, tg, u=t / self.dur):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        if t < 15.0:
            tx(tela, 'LEITURAS', PX0, 68, ACO3)
            lidas = sorted([(self.leitura(i, t), i) for i in range(len(self.XS))])
            feitas = [(tl, i) for tl, i in lidas if tl <= t][-5:]
            for k, (tl, i) in enumerate(feitas):
                y = 80 + k * 13
                if i == 6:
                    tx(tela, '??????????', PX0, y, VERMELHO); tx(tela, 'ERRO', 468, y, VERMELHO, centro='d')
                else:
                    num = D.PLACA if i == 4 else f"0042{(314159 + (i - 4) * 37) % 1000000:06d}"
                    c = AMARELO if i == 4 else ACO3
                    tx(tela, num, PX0, y, c); tx(tela, 'OK', 468, y, VERDE, centro='d')
        else:
            tx(tela, 'MALAS LIDAS', PX0, 68, ACO3)
            barras = (('CÓDIGO DE BARRAS', 85.0, '85%', ACO3, 15.0, '(PODE CAIR A)'),
                      ('CÂMERAS', 99.5, '99,5%', VERDE, 22.4, '(CHEGA A)'))
            for k, (rot, v, s, c, t_on, obs) in enumerate(barras):
                if t < t_on: continue
                y = 80 + k * 30
                u = ease((t - t_on) / 1.2)
                tx(tela, rot, PX0, y, c)
                tela.ret(PX0, y + 11, 90, 8, FUNDO2)
                tela.ret(PX0, y + 11, int(90 * v / 100 * u), 8, c)
                tx(tela, s, 470, y + 7, AMARELO, 17, centro='d')
                tx(tela, obs, PX0 + 96, y, ACO2) if False else None
            if t >= 26.0:
                tela.ret(PX0, 141, 8, 8, LATAO); tela.ret(PX0 + 2, 143, 4, 4, OLEO0)
                tx(tela, 'ALGUMAS: CHIP RFID', PX0 + 12, 141, LATAO)

    def sons(self, fx):
        self.zumbido(fx, 0, self.dur, .07)
        for i in range(len(self.XS)):
            tl = self.leitura(i, 0)
            if 0 < tl < self.dur:
                if i == 6: fx.put(fx.blip(52, .25), self.t0 + tl, .14)
                else: fx.put(fx.blip(93, .07), self.t0 + tl, .12)


# ======================================================================= 5 inspeção
class Inspecao(Cena):
    ETAPA, NOME = 3, ETAPAS[2]
    GX = 180          # x do anel do tomógrafo (dentro da máquina)

    def x_prota(self, t):
        return interp_lin([(0, -40), (4.5, 112), (16, 210), (19, 254), (31, 254), (34, 330)], t)

    def x_cinza(self, t):
        return interp_lin([(0, -120), (14, -40), (18, 112), (24, 210), (27, 220), (32, 220), (33, 254), (38, 330)], t)

    def p_scan(self, x):
        return min(1.0, max(0.0, (x + 30 - self.GX) / 30.0))

    def desenhar(self, tela, t, tg):
        D.fundo_bastidor(tela, t, chao=196)
        xp, xg = self.x_prota(t), self.x_cinza(t)
        # esteira de baixo (inspeção manual) e rampa de cima (liberadas)
        D.esteira(tela, -10, 300, 165, t, 30, chao=196)
        subir = 31.0 <= t
        D.rampa(tela, 254, 165, 300, 136, t, 30)
        tx(tela, 'LIBERADAS', 252, 118, VERDE)
        tx(tela, 'INSPEÇÃO', 250, 180, VERMELHO)
        # malas fora da máquina
        def mala(x, cor, tag=True):
            if x < 254:
                D.mala_lado(tela, x, 165, 30, 12, cor, t, tag=tag, balanco=.6)
            elif cor == 'prota' and subir:
                u = (x - 254) / 46.0
                D.mala_lado(tela, x, 165 - 29 * u, 30, 12, cor, t, tag=tag, balanco=.6)
            else:
                D.mala_lado(tela, x, 165, 30, 12, cor, t, tag=tag, balanco=.6)
        mala(xg, 'cinza')
        mala(xp, 'prota')
        # a máquina (cobre as malas que estão dentro)
        D.caixa(tela, 106, 66, 144, 104, ACO1, ACO2, ACO0)
        dither(tela, 108, 68, 140, 10, ACO2, ACO1)
        tela.ret(106, 160, 144, 10, ACO0)
        for x in (114, 240):
            tela.ret(x - 6, 128, 14, 37, PRETO); tela.ret(x - 5, 129, 12, 36, FUNDO)
        # placa de radiação (triângulo genérico)
        poligono(tela, [(126, 92), (136, 76), (146, 92)], PRETO)
        poligono(tela, [(128, 91), (136, 78), (144, 91)], AMARELO)
        tela.disco(136, 87, 1.6, PRETO)
        # janela em corte: o anel girando por dentro
        jx, jy, jw, jh = 150, 92, 80, 64
        tela.ret(jx - 1, jy - 1, jw + 2, jh + 2, PRETO)
        tela.ret(jx, jy, jw, jh, FUNDO)
        D.esteira(tela, jx, jx + jw, 165 - 10, t, 30) if False else None
        tela.ret(jx, jy + jh - 9, jw, 3, ACO0); tela.ret(jx, jy + jh - 9, jw, 1, ACO1)
        for xb, cor in ((xp, 'prota'), (xg, 'cinza')):
            if jx - 30 < xb < jx + jw:
                sub_x0 = int(max(jx, xb)); sub_x1 = int(min(jx + jw, xb + 32))
                if sub_x1 > sub_x0:
                    salvo = tela.buf[jy:jy + jh, :].copy()
                    D.mala_lado(tela, xb, jy + jh - 9, 30, 12, cor, t, tag=True, balanco=.3)
                    m = np.zeros_like(salvo, bool); m[:, jx:jx + jw] = True
                    tela.buf[jy:jy + jh, :] = np.where(m, tela.buf[jy:jy + jh, :], salvo)
        dentro = None
        for xb, nome in ((xp, 'prota'), (xg, 'cinza')):
            if 106 <= xb <= 226: dentro = nome
        # o anel visto de lado: uma faixa que gira, com a fonte subindo e descendo
        gx = self.GX
        tela.ret(gx - 5, jy + 2, 10, jh - 12, ACO0)
        tela.ret(gx - 4, jy + 2, 1, jh - 12, ACO2)
        ang = t * 3.0
        ys = jy + 4 + (jh - 16) * (.5 + .5 * math.sin(ang))
        yd = jy + 4 + (jh - 16) * (.5 - .5 * math.sin(ang))
        if dentro:
            tela.disco(gx, ys, 3, CHAMA0); tela.disco(gx, ys, 1.5, BRANCO)
            for k in range(-3, 4):
                tela.linha(gx, ys, gx + k * 2, yd, AMARELO if k % 2 else CHAMA1)
            tela.ret(gx - 4, int(yd) - 1, 8, 3, CIANO)
        tx(tela, 'EM CORTE', jx + 2, jy + 2, ACO2)
        # luz de estado em cima da máquina
        alarme = 22.5 <= t < 33.0 and dentro != 'prota'
        cor_luz = VERMELHO if alarme and (t * 3) % 1 < .6 else (AMARELO if dentro else VERDE)
        tela.ret(200, 58, 12, 8, PRETO); tela.ret(201, 59, 10, 6, cor_luz); tela.ret(203, 60, 4, 1, CHAMA0)
        # cortinas
        D.cortina(tela, 109, 129, 12, 35, t, .6 if any(100 < x + 30 and x < 120 for x in (xp, xg)) else 0)
        D.cortina(tela, 235, 129, 12, 35, t, .6 if any(220 < x + 30 and x < 248 for x in (xp, xg)) else 0)
        # estado da nossa mala depois da saída
        if 19.0 <= t < 34.0 and not VERTICAL:
            ok = t >= 30.4
            painel(tela, 252, 132 - (29 if t >= 31 else 0) * min(1, (t - 31) / 3) if t >= 31 else 132, 44, 12, borda=VERDE if ok else AMARELO)
        if 19.0 <= t < 34.0:
            ok = t >= 30.4
            yy = 133 if t < 31 else 133 - int(29 * min(1.0, (t - 31) / 3.0))
            xx = xp + 15
            if xx < 300:
                tx(tela, 'LIBERADA' if ok else 'AGUARDE', xx, yy - 12, VERDE if ok else AMARELO, centro=True)
        # vista de frente do tomógrafo (o anel girando de verdade)
        if dentro and not VERTICAL:
            self.vista_frente(tela, 52, 52, t, dentro, alarme)
        elif dentro:
            xc = self.xv(tg)
            if xc is not None and xc < 40:
                self.vista_frente(tela, xc + 40, 52, t, dentro, alarme)
        D.marcador(tela, min(xp + 15, 290), (165 if xp < 254 else 165 - 29 * min(1, (xp - 254) / 46)) - 16 if not (106 <= xp <= 236) else 60, t)
        if self.hud(tela, t, tg, u=suave((t - 4.0) / 30.0)):
            self.miolo(tela, t, xp, xg)

    def vista_frente(self, tela, cx, cy, t, quem, alarme):
        R = 34
        tela.disco(cx, cy, R + 4, PRETO)
        tela.disco(cx, cy, R + 3, ACO0)
        tela.disco(cx, cy, R - 4, FUNDO)
        tela.anel(cx, cy, R, ACO1, 2.5)
        a = t * 3.0
        sx, sy = cx + math.cos(a) * R, cy + math.sin(a) * R
        # leque de raios até o detector do outro lado
        for k in range(-6, 7):
            b = a + math.pi + k * .09
            dx, dy = cx + math.cos(b) * (R - 1), cy + math.sin(b) * (R - 1)
            tela.linha(sx, sy, dx, dy, AMARELO if k % 2 else CHAMA1)
        for k in range(-7, 8):
            b = a + math.pi + k * .09
            tela.disco(cx + math.cos(b) * R, cy + math.sin(b) * R, 1.6, CIANO)
        # corte da mala no meio
        cor = D.CORES[quem][0]
        tela.ret(cx - 15, cy - 6, 30, 12, PRETO); tela.ret(cx - 14, cy - 5, 28, 10, cor)
        tela.ret(cx - 10, cy - 2, 8, 4, LARANJA if quem == 'prota' else ACO2)
        if alarme: tela.ret(cx + 3, cy - 2, 6, 4, VERMELHO)
        tela.disco(sx, sy, 4, CHAMA0); tela.disco(sx, sy, 2, BRANCO)
        tx(tela, 'VISTO DE FRENTE', cx, cy + R + 6, ACO3, centro=True)

    def imagem(self, tela, x, y, p, quem, t, analisa=None, alarme=False):
        """Monitor: a imagem montada fatia por fatia (cores do raio-x:
        laranja = orgânico, verde = misto, azul = metal)."""
        w, h = 156, 70
        tela.ret(x - 1, y - 1, w + 2, h + 2, ACO0)
        tela.ret(x, y, w, h, FUNDO)
        for yy in range(y, y + h, 3): tela.ret(x, yy, w, 1, FUNDO2)
        ate = x + int(w * p)
        mx, my, mw, mh = x + 10, y + 10, w - 20, h - 20
        itens = []
        if quem == 'prota':
            itens = [(4, 4, 40, 20, LARANJA), (48, 6, 30, 16, CHAMA1), (82, 4, 22, 24, LARANJA),
                     (108, 18, 24, 10, VERDE), (6, 28, 26, 14, CHAMA2), (40, 30, 38, 12, LARANJA),
                     (84, 32, 16, 10, MISTURA)]
        else:
            itens = [(4, 4, 46, 22, LARANJA), (56, 6, 26, 30, CHAMA1), (88, 8, 18, 12, VERMELHO if alarme else VERDE),
                     (8, 30, 40, 12, LARANJA), (60, 38, 50, 8, MISTURA), (112, 24, 16, 16, CHAMA2)]
        salvo = tela.buf[y:y + h, ate:x + w].copy()
        tela.ret(mx, my, mw, mh, FUNDO2)
        tela.ret_vazado(mx, my, mw, mh, ACO2)
        tela.ret(mx + 4, my - 4, 2, 4, MISTURA); tela.ret(mx + mw - 6, my - 4, 2, 4, MISTURA)
        tela.ret(mx + 4, my - 5, mw - 8, 1, MISTURA)
        for ix, iy, iw, ih, c in itens:
            tela.ret(mx + ix, my + iy, iw, ih, c)
            dither(tela, mx + ix, my + iy + ih // 2, iw, ih - ih // 2, c, FUNDO2)
        tela.ret(mx + 2, my + mh - 3, mw - 4, 1, MISTURA)
        tela.buf[y:y + h, ate:x + w] = salvo
        if p < 1:
            tela.ret(ate, y, 1, h, CIANO)
        if analisa is not None:
            k = int(analisa)
            for j, (ix, iy, iw, ih, c) in enumerate(itens[:k + 1]):
                corq = VERDE if j < k or (analisa % 1) > .5 else AMARELO
                tela.ret_vazado(mx + ix - 1, my + iy - 1, iw + 2, ih + 2, corq)
        if alarme:
            ix, iy, iw, ih, c = itens[2]
            if (t * 3) % 1 < .7:
                tela.ret_vazado(mx + ix - 2, my + iy - 2, iw + 4, ih + 4, VERMELHO)
                tela.ret_vazado(mx + ix - 3, my + iy - 3, iw + 6, ih + 6, VERMELHO)

    def miolo(self, tela, t, xp, xg):
        X, Y = PX0 - 1, 80
        if t < 4.5:
            tx(tela, 'TOMÓGRAFO', PX0, 68, ACO3)
            self.imagem(tela, X, Y, 0.0, 'prota', t)
            tx(tela, 'ESPERANDO MALA', PX0 + 78, Y + 32, ACO2, centro=True)
        elif t < 15.0:
            tx(tela, 'IMAGEM 3D', PX0, 68, ACO3)
            self.imagem(tela, X, Y, self.p_scan(xp), 'prota', t)
        elif t < 22.4:
            tx(tela, 'PROCURANDO AMEAÇAS', PX0, 68, ACO3)
            self.imagem(tela, X, Y, 1.0, 'prota', t, analisa=min(6.99, (t - 15.0) / 1.0))
        elif t < 30.4:
            pisca = (t * 3) % 1 < .7
            tx(tela, 'ALARME: OUTRA MALA', PX0, 68, VERMELHO if pisca else BRASA)
            self.imagem(tela, X, Y, self.p_scan(xg), 'cinza', t, alarme=self.p_scan(xg) > .7)
            tx(tela, 'VAI PARA UM AGENTE', PX0, 140, VERMELHO) if t > 25 else None
        else:
            tx(tela, 'A NOSSA MALA', PX0, 68, ACO3)
            self.imagem(tela, X, Y, 1.0, 'prota', t)
            painel(tela, X + 30, Y + 24, 96, 22, borda=VERDE)
            tx(tela, 'LIBERADA', X + 78, Y + 28, VERDE, 17, centro=True)

    def sons(self, fx):
        self.zumbido(fx, 0, self.dur, .06)
        fx.put(fx.chiado(14.0, 300, 1200, ataque=1.0), self.t0 + 4.5, .05)        # o anel girando
        for k in range(7):
            fx.put(fx.blip(86, .04), self.t0 + 15.5 + k, .07)
        for k in range(10):
            fx.put(fx.blip(57, .18), self.t0 + 22.6 + k * .7, .1)
        fx.put(fx.blip(84, .12), self.t0 + 30.5, .14); fx.put(fx.blip(91, .16), self.t0 + 30.7, .14)


# ======================================================================= 6 triagem
CHUTES_C = [(90, 'BIT'), (130, 'RGB'), (170, 'PXL'), (210, 'CPU')]     # saem para cima
CHUTES_B = [(150, 'LCD'), (190, 'USB'), (226, 'GIF')]                  # saem para baixo


class Triagem(Cena):
    ETAPA, NOME = 4, ETAPAS[3]
    X0, X1, YB, YT, R = 62, 236, 162, 50, 56
    V = 23.0
    N = 38
    P_IND = 38.0

    def preparar(self):
        self.Ls = self.X1 - self.X0
        self.arc = math.pi * self.R
        self.P = 2 * self.Ls + 2 * self.arc
        self.sp = self.P / self.N
        self.phi = (self.P_IND - self.V * 8.0) % self.P          # bandeja 0 passa na indução em t = 8
        # saídas: posição p de cada uma
        self.saidas = {}
        for x, c in CHUTES_B: self.saidas[c] = (x - self.X0, +1, x)
        for x, c in CHUTES_C: self.saidas[c] = (self.Ls + self.arc + (self.X1 - x), -1, x)
        rng = np.random.default_rng(5)
        T = self.P / self.V
        self.eventos = []      # (t_ind, t_out, k, código, cor, prota)
        for k in range(self.N):
            for cyc in range(-2, 4):
                t_ind = 8.0 + (self.P_IND - self.P_IND - k * self.sp) / self.V + cyc * T
                t_ind = 8.0 - k * self.sp / self.V + cyc * T
                prota = (k == 0 and cyc == 0)
                if not prota and rng.random() > .55: continue
                cod = 'PXL' if prota else str(rng.choice([c for _, c in CHUTES_C + CHUTES_B]))
                pj = self.saidas[cod][0]
                t_out = t_ind + ((pj - self.P_IND) % self.P) / self.V
                cor = 'prota' if prota else D.outra(int(rng.integers(0, 60)))
                self.eventos.append((t_ind, t_out, k, cod, cor, prota))
        self.t_prota = next(e[1] for e in self.eventos if e[5])
        self.IND = [(-30, 186), (76, 186), (100, 168)]
        self.L_ind = comprimento(self.IND)

    def pos(self, p):
        p %= self.P
        if p < self.Ls: return self.X0 + p, self.YB
        p -= self.Ls
        if p < self.arc:
            a = p / self.R
            return self.X1 + self.R * math.sin(a), (self.YB + self.YT) / 2 + self.R * math.cos(a)
        p -= self.arc
        if p < self.Ls: return self.X1 - p, self.YT
        a = (p - self.Ls) / self.R
        return self.X0 - self.R * math.sin(a), (self.YB + self.YT) / 2 - self.R * math.cos(a)

    def p_bandeja(self, k, t):
        return (k * self.sp + self.V * t + self.phi) % self.P

    def faixa(self, tela, xa, ya, xb, yb, larg, t, vel):
        """Esteira vista de cima."""
        L = math.hypot(xb - xa, yb - ya) or 1
        nx, ny = -(yb - ya) / L * larg / 2, (xb - xa) / L * larg / 2
        poligono(tela, [(xa + nx * 1.2, ya + ny * 1.2), (xb + nx * 1.2, yb + ny * 1.2), (xb - nx * 1.2, yb - ny * 1.2), (xa - nx * 1.2, ya - ny * 1.2)], PRETO)
        poligono(tela, [(xa + nx, ya + ny), (xb + nx, yb + ny), (xb - nx, yb - ny), (xa - nx, ya - ny)], ACO0)
        off = (t * vel) % 6
        for k in range(int(L // 6) + 1):
            u = (k * 6 + off) / L
            if u > 1: continue
            cx, cy = xa + (xb - xa) * u, ya + (yb - ya) * u
            tela.linha(cx + nx * .9, cy + ny * .9, cx - nx * .9, cy - ny * .9, FUNDO3)

    def calha(self, tela, x, sentido, cod, t, destaque=False):
        """Saída (calha) que vai do circuito até a borda."""
        y0, y1 = (0, self.YT - 9) if sentido < 0 else (self.YB + 9, PALCO_H)
        tela.ret(x - 10, y0, 20, y1 - y0, PRETO)
        tela.ret(x - 9, y0, 18, y1 - y0, ACO0)
        for yy in range(y0, y1, 4):
            o = int((t * 30 * -sentido)) % 4
            tela.ret(x - 8, yy + o, 16, 1, TRACO)
        tela.ret(x - 9, y0, 1, y1 - y0, ACO1); tela.ret(x + 8, y0, 1, y1 - y0, ACO1)
        yl = y0 + 3 if sentido < 0 else y1 - 11
        cor = AMARELO if destaque else CIANO
        painel(tela, x - 12, yl - 2, 24, 11, borda=cor)
        tx(tela, cod, x, yl, cor, centro=True)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, 300, 16): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(8, PALCO_H, 16): tela.ret(0, y, 300, 1, FUNDO2)
        yc = (self.YB + self.YT) / 2
        destaque = t >= 39.0 and (t * 2) % 1 < .7
        for x, c in CHUTES_C: self.calha(tela, x, -1, c, t, destaque and c == 'PXL')
        for x, c in CHUTES_B: self.calha(tela, x, +1, c, t)
        # leito do circuito
        for cx in (self.X0, self.X1):
            tela.anel(cx, yc, self.R, PRETO, 11)
            tela.anel(cx, yc, self.R, FUNDO3, 9.5)
        tela.ret(self.X0, self.YT - 11, self.Ls, 23, PRETO); tela.ret(self.X0, self.YT - 10, self.Ls, 21, FUNDO3)
        tela.ret(self.X0, self.YB - 11, self.Ls, 23, PRETO); tela.ret(self.X0, self.YB - 10, self.Ls, 21, FUNDO3)
        # ilha do meio (máquinas)
        tela.disco(self.X0, yc, self.R - 11, FUNDO2); tela.disco(self.X1, yc, self.R - 11, FUNDO2)
        tela.ret(self.X0, self.YT + 11, self.Ls, self.YB - self.YT - 22, FUNDO2)
        dither(tela, self.X0, self.YT + 12, self.Ls, self.YB - self.YT - 24, FUNDO2, FUNDO)
        for x in range(self.X0 + 20, self.X1 - 10, 40):
            D.caixa(tela, x, yc - 10, 24, 18, ACO0, ACO1, FUNDO3)
            tela.px(x + 4, yc - 6, VERDE if int(t * 2 + x) % 3 else AGUA0)
        tx(tela, 'CIRCUITO DE BANDEJAS', (self.X0 + self.X1) // 2, int(yc) + 14, ACO1, centro=True)
        # indução
        self.faixa(tela, -30, 186, 76, 186, 13, t, 20.5)
        self.faixa(tela, 76, 186, 100, 168, 13, t, 20.5)
        # bandejas
        ocup = {}
        for (t_ind, t_out, k, cod, cor, prota) in self.eventos:
            if t_ind <= t < t_out + .45: ocup[k] = (t_ind, t_out, cod, cor, prota)
        for k in range(self.N):
            p = self.p_bandeja(k, t)
            x, y = self.pos(p)
            tomba = 0.0; sentido = 0
            if k in ocup:
                t_ind, t_out, cod, cor, prota = ocup[k]
                if t >= t_out:
                    tomba = min(1.0, (t - t_out) / .25)
                    sentido = self.saidas[cod][1]
            if tomba > 0:
                o = int(round(2 * tomba)) * sentido
                D.caixa(tela, x - 7, y - 7 + o, 14, 14, ACO0, ACO1, FUNDO3)
                tela.ret(int(x) - 6, int(y) - 6 + o + (10 if sentido > 0 else 0), 12, 2, ACO3)
            else:
                D.caixa(tela, x - 7, y - 7, 14, 14, ACO1, ACO3, ACO0)
        # malas nas bandejas, na indução e caindo nas calhas
        prota_xy = None
        for (t_ind, t_out, k, cod, cor, prota) in self.eventos:
            if t < t_ind - self.L_ind / 20.5 - .1: continue
            if t < t_ind:
                d = self.L_ind - (t_ind - t) * 20.5
                q = ao_longo(self.IND, d)
                if q is None: continue
                x, y = q
            elif t < t_out:
                x, y = self.pos(self.p_bandeja(k, t))
            else:
                pj, sentido, xc = self.saidas[cod]
                tau = t - t_out
                xs, ys = self.pos(pj)
                if prota:
                    o = min(1.0, tau / 1.6) ** 1.6 * (self.YT - 14)
                else:
                    o = (tau / 1.4) ** 1.6 * 70
                    if o > 70: continue
                x, y = xc, ys + sentido * o
            D.mala_topo(tela, x, y, 12, 9, cor, t, tag=prota)
            if prota: prota_xy = (x, y)
        if prota_xy:
            D.marcador(tela, prota_xy[0], prota_xy[1] - 7, t)
        if self.hud(tela, t, tg, u=suave((t - 8.0) / (self.t_prota - 8.0 + 2.0))):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        tx(tela, 'BANDEJA BASCULANTE', PX0, 68, ACO3)
        # a bandeja de lado: carrinho no trilho e a bandeja que tomba
        cx, cy = PX0 + 80, 104
        ciclo = (t % 3.0)
        a = 0.0
        if ciclo > 1.4: a = min(1.0, (ciclo - 1.4) / .3)
        if ciclo > 2.3: a = max(0.0, 1 - (ciclo - 2.3) / .4)
        ang = math.radians(28) * a
        tela.ret(cx - 60, cy + 12, 120, 3, ACO0); tela.ret(cx - 60, cy + 12, 120, 1, ACO2)
        D.caixa(tela, cx - 14, cy, 28, 12, ACO0, ACO1, FUNDO3)
        tela.disco(cx - 9, cy + 13, 3, PRETO); tela.disco(cx + 9, cy + 13, 3, PRETO)
        ca, sa = math.cos(ang), math.sin(ang)
        def rot(px_, py_): return (cx + px_ * ca - py_ * sa, cy - 4 + px_ * sa + py_ * ca)
        poligono(tela, [rot(-30, -3), rot(30, -3), rot(30, 2), rot(-30, 2)], PRETO)
        poligono(tela, [rot(-29, -2), rot(29, -2), rot(29, 1), rot(-29, 1)], ACO2)
        tela.disco(cx, cy - 2, 2, ACO3)
        desl = 0.0 if a < 1 else min(1.0, (ciclo - 1.7) / .6) * 40
        bx = -10 + desl
        p0 = rot(bx - 10, -3)
        p1 = rot(bx + 10, -3)
        if bx < 32:
            poligono(tela, [p0, p1, (p1[0] + sa * -9 * 0 + -sa * 9 * 0 + 0 - 9 * sa * -1 * 0 + 0, p1[1] - 9 * ca), (p0[0], p0[1] - 9 * ca)], PRETO)
            q0 = rot(bx - 9, -4); q1 = rot(bx + 9, -4)
            poligono(tela, [q0, q1, (q1[0] + 8 * sa, q1[1] - 8 * ca), (q0[0] + 8 * sa, q0[1] - 8 * ca)], CHAMA2)
        tx(tela, 'TOMBA NA SAÍDA CERTA', PX0, 122, ACO2)
        c1 = AMARELO if 15.0 <= t < 23.0 else BRANCO
        c2 = AMARELO if 31.0 <= t < 39.0 else BRANCO
        tx(tela, 'VELOCIDADE', PX0, 134, ACO3); tx(tela, '2 M/S', 470, 132, c1, 9, centro='d')
        tx(tela, 'ATÉ', PX0, 144, ACO3); tx(tela, '9.000 MALAS/H', 470, 144, c2, 9, centro='d')

    def sons(self, fx):
        self.zumbido(fx, 0, self.dur, .06)
        for (t_ind, t_out, k, cod, cor, prota) in self.eventos:
            if 0 < t_out < self.dur:
                fx.put(fx.clique(900 if prota else 1400, .04), self.t0 + t_out, .3 if prota else .1, -.3 if self.saidas[cod][1] < 0 else .3)
        fx.put(fx.explosao(.4), self.t0 + self.t_prota + 1.6, .2)


# ======================================================================= 7 montagem
class Montagem(Cena):
    ETAPA, NOME = 5, ETAPAS[4]
    CHUTE = [(-10, 52), (112, 146)]
    MESA_Y = 150
    LD = (214, 186, 74, 58)            # x, base, largura, altura do contêiner

    def pos_mala(self, t):
        """(x, base) da nossa mala: desce a calha, pousa na mesa, vai para o contêiner."""
        if t < 5.0:
            u = max(0.0, (t - .4) / 4.6) ** 1.5
            (ax, ay), (bx, by) = self.CHUTE
            return ax - 40 + (bx - 20 - ax + 40) * u, ay + (by - ay) * u - 1, 'rampa'
        if t < 23.0:
            return 104, self.MESA_Y, 'mesa'
        if t < 27.0:
            u = ease((t - 23.0) / 4.0)
            x0, y0 = 104, self.MESA_Y
            x1, y1 = self.LD[0] + 26, self.LD[1] - 26
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - math.sin(u * math.pi) * 30, 'mao'
        return self.LD[0] + 26, self.LD[1] - 26, 'dentro'

    def desenhar(self, tela, t, tg):
        D.fundo_bastidor(tela, t, chao=196)
        # calha de roletes vinda da triagem
        (ax, ay), (bx, by) = self.CHUTE
        D.rampa(tela, ax, ay, bx, by, t, 50)
        tela.ret(14, 4, 1, 1, FUNDO)
        tx(tela, 'SAÍDA PXL', 22, 22, AMARELO)
        # mesa de montagem
        tela.ret(96, self.MESA_Y, 84, 6, PRETO); tela.ret(97, self.MESA_Y + 1, 82, 4, ACO1); tela.ret(97, self.MESA_Y + 1, 82, 1, ACO3)
        for x in (100, 172): tela.ret(x, self.MESA_Y + 6, 4, 196 - self.MESA_Y - 6, ACO0)
        # contêiner na carreta
        x, yb, w, h = self.LD
        D.carrinho(tela, x - 2, yb, w + 4, t)
        D.ld3(tela, x, yb, w, h, porta='aberta')
        self.malas_dentro(tela, t)
        if t >= 29.0:
            u = min(1.0, (t - 29.0) / 1.5)
            self.rede(tela, u)
        # a nossa mala
        mx, my, onde = self.pos_mala(t)
        if onde != 'dentro':
            D.mala_lado(tela, mx, my, 30, 12, 'prota', t, tag=True, balanco=.8)
        # funcionário
        lado = -1 if t < 22.0 else 1
        braco = 0.0
        if 7.4 <= t < 14.6: braco = min(1.0, (t - 7.4) / .6)
        mao = None
        if 23.0 <= t < 27.0:
            braco = .9
        fx_ = 192 if t < 22 else interp([(22, 192), (25, 196)], t)
        hx, hy = D.funcionario(tela, fx_, 196, t, lado=lado, braco=braco, scanner=t < 22.0)
        if 8.2 <= t < 14.0:
            # feixe do leitor de mão na etiqueta
            alvo = (104 + 19 + 4, self.MESA_Y - 12 + 3)
            if (t * 6) % 1 < .8:
                tela.linha(hx - 4, hy - 2, alvo[0], alvo[1], VERMELHO)
                tela.disco(alvo[0], alvo[1], 1.6, VERMELHO)
        if onde in ('mesa', 'rampa') or onde == 'mao':
            D.marcador(tela, mx + 15, my - 16, t)
        else:
            D.marcador(tela, self.LD[0] + 26 + 15, self.LD[1] - 26 - 16, t)
        if self.hud(tela, t, tg, u=suave(t / self.dur)):
            self.miolo(tela, t)

    def malas_dentro(self, tela, t):
        x, yb, w, h = self.LD
        fixas = [(x + 3, yb - 2, 22, 'azul'), (x + 27, yb - 2, 22, 'verde'),
                 (x + 3, yb - 14, 22, 'cinza'), (x + 27, yb - 14, 22, 'roxo'), (x + 3, yb - 26, 22, 'marrom')]
        for mx, my, mw, cor in fixas:
            D.mala_lado(tela, mx, my, mw, 10, cor, t, alca=False, rodas=False)
        if self.pos_mala(t)[2] == 'dentro':
            D.mala_lado(tela, x + 26, yb - 26, 30, 12, 'prota', t, tag=True, balanco=.3)

    def rede(self, tela, u):
        x, yb, w, h = self.LD
        top = yb - h
        bw = int(round(w * .78)); kink = yb - int(h * .48)
        ylim = top + 2 + int((h - 4) * u)
        for yy in range(top + 4, ylim, 5):
            xr = x + w - 2 if yy <= kink else x + bw + int((w - bw) * (yb - yy) / max(1, yb - kink)) - 2
            tela.ret(x + 2, yy, xr - x - 2, 1, LATAO)
        for xx in range(x + 5, x + w - 2, 6):
            yr = yb - 2 if xx <= x + bw else kink + int((yb - kink) * (x + w - xx) / max(1, w - bw))
            tela.ret(xx, top + 2, 1, min(yr, ylim) - top - 2, LATAO)

    def miolo(self, tela, t):
        if t < 7.4:
            tx(tela, 'VOO 314 PARA PXL', PX0, 68, ACO3)
            tx(tela, 'SAÍDA PXL', PX0, 82, AMARELO, 17)
            tx(tela, 'A RAMPA LEVA', PX0, 104, ACO2)
            tx(tela, 'ATÉ A MONTAGEM', PX0, 115, ACO2)
        elif t < 15.0:
            tx(tela, 'LEITOR DE MÃO', PX0, 68, ACO3)
            if t > 8.4:
                tx(tela, D.PLACA, PX0, 82, BRANCO, 17)
            if t > 9.4:
                tx(tela, 'VOO 314', PX0, 106, CIANO, 17)
                painel(tela, PX0 + 92, 104, 60, 18, borda=VERDE)
                tx(tela, 'CONFERE', PX0 + 122, 108, VERDE, centro=True)
        elif t < 23.0:
            tx(tela, 'REGISTROS DA MALA', PX0, 68, ACO3)
            pts = ('DESPACHO', 'CARREGAMENTO', 'CONEXÃO', 'CHEGADA')
            for k, p in enumerate(pts):
                y = 82 + k * 15
                feito = k == 0 or (k == 1 and t > 16.0)
                cor = VERDE if feito else FUNDO3
                tela.ret(PX0, y + 1, 7, 7, cor)
                tx(tela, p, PX0 + 12, y, BRANCO if feito else ACO1)
            tx(tela, '(RESOLUÇÃO 753 IATA)', PX0, 141, ACO2)
        else:
            tx(tela, 'CONTÊINER DO VOO', PX0, 68, ACO3)
            n = 5 + (1 if self.pos_mala(t)[2] == 'dentro' else 0)
            tx(tela, f"{n} MALAS", PX0, 82, BRANCO, 17)
            tx(tela, 'TODAS PARA PXL', PX0, 104, AMARELO)
            if t > 29: tx(tela, 'REDE FECHADA', PX0, 118, ACO2)

    def sons(self, fx):
        fx.put(fx.chiado(4.4, 200, 900), self.t0 + .5, .1)
        fx.put(fx.explosao(.5), self.t0 + 5.0, .25)
        fx.put(fx.blip(95, .1), self.t0 + 9.4, .16)
        fx.put(fx.explosao(.6), self.t0 + 27.0, .22)
        fx.put(fx.chiado(1.5, 800, 3000), self.t0 + 29.0, .06)


# ======================================================================= 8 pátio
def cena_patio(tela, t, estrelas, porta=1.0, plat=178, conts=(), trem_x=None, luzes=True):
    """O pátio à noite: avião (nariz à esquerda), elevador e contêineres.
    conts = [(x, base, prota)]. Contêiner para trás da pele do avião some
    depois da porta (o pixel salvo volta)."""
    D.ceu_noite(tela, t, estrelas, horizonte=150)
    # prédio do terminal ao longe
    tela.ret(0, 128, 300, 22, FUNDO2)
    for x in range(4, 300, 7):
        if (x * 13) % 5 != 0: tela.px(x, 134 + (x % 3) * 4, CHAMA1 if x % 4 else AMARELO)
    for xm in (60, 250):
        tela.ret(xm, 96, 2, 54, ACO0)
        tela.ret(xm - 5, 94, 12, 3, ACO2); tela.ret(xm - 4, 96, 10, 1, CHAMA0)
    # pátio
    tela.ret(0, 150, W, PALCO_H - 150, ACO0)
    dither(tela, 0, 150, W, 14, TRACO, ACO0)
    dither(tela, 0, 176, W, PALCO_H - 176, ACO0, ACO1)
    tela.ret(0, 200, 300, 2, AMARELO)
    for xm in (60, 250): D.cone_luz(tela, xm + 1, 98, 200, 6, 90, ACO2, so_em=[ACO0, ACO1, TRACO])
    top, bot = D.fuselagem(tela, 24, t, porta=porta, luzes=luzes)
    D.trem_pouso(tela, 82, bot - 4, 196)
    # trator e carretas (atrás do elevador)
    if trem_x is not None:
        D.trator(tela, trem_x, 196, t)
        for k in (1, 2):
            D.carrinho(tela, trem_x - 10 - k * 49 + 12, 186, 38, t)
    D.elevador(tela, 112, 196, plat, 56)
    for (cx, cb, prota) in conts:
        salvo = tela.buf[100:126, 224:300].copy() if porta > 0 else None
        D.ld3(tela, cx, cb, 30, 23, porta='rede' if prota else 'fechada', malas=['prota', 'azul', 'verde', 'cinza'] if prota else None)
        if prota: D.marcador(tela, cx + 15, cb - 25, t)
        if salvo is not None and cx + 31 > 224 and cb <= 126:
            tela.buf[100:126, 224:300] = salvo


class Patio(Cena):
    ETAPA, NOME = 6, ETAPAS[5]

    def preparar(self):
        rng = np.random.default_rng(8)
        self.estrelas = [(int(rng.integers(0, 300)), int(rng.integers(0, 120)), float(rng.uniform(0, 6))) for _ in range(40)]

    def trem(self, t):
        if t < 33.0: return interp([(0, -120), (6.5, 113)], t)
        return 113 + (t - 33.0) ** 2 * 18

    def plat(self, t):
        return interp([(0, 178), (10, 178), (14, 120), (19, 120), (23, 178), (25.5, 178), (28, 120)], t)

    def conts(self, t):
        tx_ = self.trem(t)
        d1 = tx_ - 10 - 49 + 12 + 4
        d2 = tx_ - 10 - 98 + 12 + 4
        p = self.plat(t)
        out = []
        # contêiner 1 (o nosso)
        if t < 7.8: c1 = (d1, 186)
        elif t < 10: u = ease((t - 7.8) / 2.2); c1 = (d1 + (125 - d1) * u, 186 + (p - 186) * u - math.sin(u * math.pi) * 4)
        elif t < 15: c1 = (125, p)
        elif t < 19: c1 = (125 + (300 - 125) * suave((t - 15) / 4), 120)
        else: c1 = None
        if t < 23: c2 = (d2, 186)
        elif t < 25.5: u = ease((t - 23) / 2.5); c2 = (d2 + (125 - d2) * u, 186 + (p - 186) * u - math.sin(u * math.pi) * 4)
        elif t < 28: c2 = (125, p)
        elif t < 30.5: c2 = (125 + (300 - 125) * suave((t - 28) / 2.5), 120)
        else: c2 = None
        if c2: out.append((c2[0], c2[1], False))
        if c1: out.append((c1[0], c1[1], True))
        return out

    def desenhar(self, tela, t, tg):
        porta = 1.0 - suave((t - 30.4) / 2.6)
        cena_patio(tela, t, self.estrelas, porta=porta, plat=self.plat(t), conts=self.conts(t), trem_x=self.trem(t))
        if self.hud(tela, t, tg, u=suave(t / 30.0)):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        if t < 15.4:
            tx(tela, 'PORÃO DIANTEIRO', PX0, 68, ACO3)
            tx(tela, 'VOO 314', PX0, 82, BRANCO, 17)
            tx(tela, '2 CONTÊINERES', PX0, 104, AMARELO)
            alt = int(round((178 - self.plat(t)) / 58 * 100))
            tx(tela, 'ELEVADOR', PX0, 120, ACO2)
            tela.ret(PX0 + 60, 121, 90, 6, FUNDO2); tela.ret(PX0 + 60, 121, int(90 * alt / 100), 6, CIANO)
        elif t < 23.0:
            tx(tela, 'CONTÊINER LD3 (AKE)', PX0, 68, CIANO)
            m3(tela, PX0, 84, '4,5', AMARELO)
            tx(tela, '1,63 M DE ALTURA', PX0, 106, BRANCO)
            D.ld3(tela, PX0 + 104, 146, 50, 40, porta='fechada')
            tela.ret(PX0 + 98, 106, 1, 40, AMARELO); tela.ret(PX0 + 96, 106, 5, 1, AMARELO); tela.ret(PX0 + 96, 145, 5, 1, AMARELO)
            tx(tela, '1,63', PX0 + 70, 122, AMARELO)
        else:
            tx(tela, 'O AVIÃO EM CORTE', PX0, 68, ACO3)
            cx, cy, R = PX0 + 80, 108, 38
            tela.disco(cx, cy, R + 2, PRETO); tela.disco(cx, cy, R, ACO2); tela.disco(cx, cy, R - 3, FUNDO2)
            tela.ret(cx - R + 3, cy + 6, 2 * R - 6, 2, ACO3)
            for k in range(-3, 4):
                tela.ret(cx + k * 9 - 3, cy - 6, 6, 10, MISTURA); tela.ret(cx + k * 9 - 3, cy - 6, 6, 2, MISTURA2)
            # dois LD3 lado a lado, chanfro para fora
            w, h = 24, 20
            D.ld3(tela, cx + 2, cy + 9 + h, w, h, porta='fechada', nome=False)
            salvo_x0 = cx - 2 - w
            tmp = tela.buf.copy()
            D.ld3(tela, salvo_x0, cy + 9 + h, w, h, porta='fechada', nome=False)
            reg = tela.buf[cy + 7:cy + 11 + h, salvo_x0 - 1:salvo_x0 + w + 3].copy()
            tela.buf[cy + 7:cy + 11 + h, salvo_x0 - 1:salvo_x0 + w + 3] = tmp[cy + 7:cy + 11 + h, salvo_x0 - 1:salvo_x0 + w + 3]
            tela.buf[cy + 7:cy + 11 + h, salvo_x0 - 1:salvo_x0 + w + 3] = reg[:, ::-1]
            tx(tela, '2 LADO A LADO', cx, 140, AMARELO, centro=True)

    def sons(self, fx):
        for k in range(int(6.5 * 12)):
            fx.put(fx.pulso(), self.t0 + k / 12.0, .06)
        for a, b in ((10, 14), (19, 23), (25.5, 28)):
            fx.put(fx.chiado(b - a, 120, 500, ataque=.3), self.t0 + a, .1)
        for a in (7.8, 15.0, 23.0, 28.0):
            fx.put(fx.chiado(2.0, 400, 1600), self.t0 + a, .05)
        fx.put(fx.explosao(.8), self.t0 + 33.0, .25)


# ======================================================================= 9 voo
class Voo(Cena):
    ETAPA, NOME = 7, ETAPAS[6]

    def preparar(self):
        rng = np.random.default_rng(12)
        self.estrelas = [(int(rng.integers(0, W)), int(rng.integers(0, 120)), float(rng.uniform(0, 6))) for _ in range(70)]
        self.nuvens = [(float(rng.uniform(0, 600)), float(rng.uniform(20, 190)), float(rng.uniform(18, 46)), int(rng.integers(0, 2))) for _ in range(14)]
        self.luzes = [(float(rng.uniform(0, 900)), int(rng.integers(192, 207))) for _ in range(90)]

    def desenhar(self, tela, t, tg):
        D.ceu_noite(tela, t, self.estrelas, horizonte=180)
        tela.disco(250, 26, 9, CERAMICA); tela.disco(246, 24, 2, ACO4)
        # luzes de cidade bem lá embaixo
        tela.ret(0, 186, W, PALCO_H - 186, FUNDO)
        for x, y in self.luzes:
            xx = (x - t * 12) % 900 - 100
            if 0 <= xx < W: tela.px(xx, y, CHAMA1 if int(x) % 3 else AMARELO)
        # nuvens (atrás)
        for x, y, w, camada in self.nuvens:
            if camada: continue
            xx = (x - t * 25) % 640 - 80
            self.nuvem(tela, xx, y, w, FUNDO3, TRACO)
        bob = math.sin(t * .9) * 2
        yc = 92 + bob
        D.aviao(tela, 22, yc, t, corte=self.porao)
        # rastro dos motores
        for k in range(30):
            xx = 150 - k * 6 + (t * 40) % 6
            if xx < 0: break
            if k % 2 == 0: tela.px(xx, yc + 16 + k * .05, ACO1 if k < 12 else TRACO)
        # zoom do porão
        if not VERTICAL or True:
            zx, zy, zw, zh = 96, 136, 124, 52
            tela.linha(92, yc + 4, zx, zy, CIANO); tela.linha(212, yc + 4, zx + zw, zy, CIANO)
            tela.ret(zx - 1, zy - 1, zw + 2, zh + 2, CIANO)
            tela.ret(zx, zy, zw, zh, FUNDO)
            tela.ret(zx, zy + zh - 4, zw, 4, ACO0); tela.ret(zx, zy + zh - 4, zw, 1, ACO1)
            for k in range(3):
                cx = zx + 6 + k * 40
                if k == 1:
                    D.ld3(tela, cx, zy + zh - 4, 34, 28, porta='rede', malas=['azul', 'verde', 'cinza', 'prota', 'roxo', 'marrom'])
                else:
                    D.ld3(tela, cx, zy + zh - 4, 34, 28, porta='fechada')
            tx(tela, 'PORÃO', zx + 3, zy + 2, CIANO)
            D.marcador(tela, zx + 6 + 40 + 17, zy - 1, t)
        # nuvens (frente)
        for x, y, w, camada in self.nuvens:
            if not camada: continue
            xx = (x - t * 55) % 700 - 100
            if 120 < y < 190 and 70 < xx < 240: continue
            self.nuvem(tela, xx, y, w, TRACO, ACO0)
        if self.hud(tela, t, tg, u=suave(t / (self.dur - .5))):
            self.miolo(tela, t)

    def porao(self, tela, x0, y0, x1, y1):
        tela.ret(x0, y0, x1 - x0, y1 - y0, PRETO)
        tela.ret(x0 + 1, y0 + 1, x1 - x0 - 2, y1 - y0 - 2, FUNDO)
        for k in range((x1 - x0) // 14):
            cx = x0 + 3 + k * 14
            tela.ret(cx, y0 + 3, 11, y1 - y0 - 4, ACO1); tela.ret(cx, y0 + 3, 11, 1, ACO3)
            if k == 3: tela.ret(cx + 3, y0 + 5, 5, 3, CHAMA2)

    def nuvem(self, tela, x, y, w, cor, luz):
        for k in range(4):
            tela.disco(x + k * w / 4, y - math.sin(k * 1.3) * w * .12, w * .22, cor)
        tela.ret(int(x - w * .1), int(y), int(w * .95), int(w * .16), cor)
        for k in range(4):
            tela.px(x + k * w / 4, y - math.sin(k * 1.3) * w * .12 - w * .22, luz)

    def miolo(self, tela, t):
        tx(tela, 'ROTA DE EXEMPLO', PX0, 68, ACO3)
        ax, ay, bx, by = PX0 + 8, 128, PX0 + 150, 88
        for k in range(0, 30):
            u = k / 29
            tela.px(ax + (bx - ax) * u, ay + (by - ay) * u - math.sin(u * math.pi) * 18, ACO1)
        if t >= 29.8:
            hx, hy = PX0 + 70, 140
            for k in range(0, 20):
                u = k / 19
                tela.px(ax + (hx - ax) * u, ay + (hy - ay) * u, ROXO)
                tela.px(hx + (bx - hx) * u, hy + (by - hy) * u, ROXO)
            tela.disco(hx, hy, 2.5, ROXO); tx(tela, 'HUB?', hx + 6, hy - 3, ROXO)
        u = suave(t / (self.dur - .5))
        px_, py_ = ax + (bx - ax) * u, ay + (by - ay) * u - math.sin(u * math.pi) * 18
        tela.disco(ax, ay, 3, ACO3); tela.disco(bx, by, 3, AMARELO)
        tx(tela, 'ORIGEM', ax - 2, ay + 6, ACO3)
        tx(tela, 'PXL', bx - 18, by - 12, AMARELO)
        poligono(tela, [(px_ + 5, py_), (px_ - 4, py_ - 4), (px_ - 2, py_), (px_ - 4, py_ + 4)], BRANCO)
        txts = ((7.8, 'PORÃO DA FRENTE'), (15.4, 'PESO JÁ CONHECIDO'), (23.0, 'AVIÃO GRANDE: LD3'), (99, '900 KM DE VOO'))
        s = 'PORÃO DA FRENTE'
        for a, l in ((0, 'NO PORÃO DA FRENTE'), (7.8, 'PESO JÁ CONHECIDO'), (15.4, 'AVIÃO GRANDE: LD3'), (23.0, '900 KM DE VOO')):
            if t >= a: s = l
        tx(tela, s, PX0, 74 + 0, ACO3) if False else tx(tela, s, PX0, 140, CIANO)

    def sons(self, fx):
        fx.put(fx.chiado(self.dur, 80, 400, ataque=1.5), self.t0, .12)


# ======================================================================= 10 conexão
class Conexao(Cena):
    ETAPA, NOME = 7, 'CONEXÃO?'

    def preparar(self):
        rng = np.random.default_rng(14)
        self.estrelas = [(int(rng.integers(0, 300)), int(rng.integers(0, 110)), float(rng.uniform(0, 6))) for _ in range(40)]

    def aviao_chao(self, tela, x, t, porta_aberta=True, s=.55):
        yc = 132
        D.aviao(tela, x, yc, t, s=s)
        # trem de pouso
        for gx in (x + 60 * s, x + 135 * s, x + 225 * s):
            tela.ret(int(gx), int(yc + 14 * s), 2, int(196 - yc - 14 * s - 5), ACO1)
            tela.disco(gx + 1, 191, 5, PRETO); tela.disco(gx + 1, 191, 2, ACO1)
        # porta do porão
        dx, dy = int(x + 180 * s), int(yc + 4)
        tela.ret(dx - 1, dy - 1, 16, 9, PRETO)
        tela.ret(dx, dy, 14, 7, FUNDO if porta_aberta else ACO2)
        if porta_aberta: tela.ret(dx + 1, dy + 1, 12, 1, CHAMA0)
        return dx + 7, dy + 6

    def desenhar(self, tela, t, tg):
        D.ceu_noite(tela, t, self.estrelas, horizonte=150)
        tela.ret(0, 150, W, PALCO_H - 150, ACO0)
        dither(tela, 0, 176, W, PALCO_H - 176, ACO0, ACO1)
        tela.ret(0, 200, 300, 2, AMARELO)
        pa = self.aviao_chao(tela, -86, t, True)
        fecha_b = 18.0 <= t < 23.0
        pb = self.aviao_chao(tela, 150, t, not fecha_b)
        tx(tela, 'VOO 1', 10, 100, ACO2)
        tx(tela, 'VOO 2', 196, 100, ACO2)
        # 1ª corrida: a nossa mala troca de avião a tempo; 2ª: outra mala perde
        for (t0, cor, chega) in ((0.0, 'prota', True), (14.0, 'cinza', False)):
            tt = t - t0
            if tt < 0 or tt > 14.0: continue
            xc = interp([(0, -40), (2.5, 30), (4.0, 30), (10.0, 186), (14.0, 186)], tt)
            D.trator(tela, xc + 30, 196, t, 20)
            D.carrinho(tela, xc - 12, 186, 38, t, 20)
            if tt < 2.5:
                u = tt / 2.5
                mx, my = pa[0] + (xc - 6 - pa[0]) * u, pa[1] + (186 - pa[1]) * u
            elif tt < 10.0 or not chega:
                mx, my = xc - 6, 186
            else:
                u = min(1.0, (tt - 10.0) / 2.5)
                mx, my = xc - 6 + (pb[0] - 15 - xc + 6) * u, 186 + (pb[1] - 186) * u
            if not (chega and tt > 12.5):
                D.mala_lado(tela, mx, my, 26, 10, cor, t, tag=True, balanco=.6)
            if cor == 'prota': D.marcador(tela, mx + 13, my - 13, t)
            if not chega and tt > 8.0:
                if (t * 2) % 1 < .7:
                    painel(tela, xc - 30, 150, 74, 13, borda=VERMELHO)
                    tx(tela, 'PERDEU O VOO', xc + 7, 153, VERMELHO, centro=True)
        if t >= 23.0:
            escurecer(tela, 0, 0, 300, PALCO_H)
            u = ease((t - 23.0) / .5)
            xc = self.xv(tg)
            cx = 150 if xc is None else xc + 90
            painel(tela, cx - 76, 76, 152, 40, borda=VERDE)
            tx(tela, 'VOO DIRETO', cx, 84 - int((1 - u) * 20), VERDE, 26 if xc is None else 17, centro=True)
        if self.hud(tela, t, tg, rodape=['CENA HIPOTÉTICA:', 'NA NOSSA VIAGEM', 'NÃO TEM CONEXÃO']):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        if t < 15.4:
            tx(tela, 'TEMPO DE CONEXÃO', PX0, 68, ACO3)
            m = int(interp_lin([(0, 55), (14, 9), (30, 9)], t))
            tx(tela, f"{m} MIN", PX0, 82, AMARELO, 26)
            tx(tela, 'PARA TROCAR', PX0, 114, ACO2)
            tx(tela, 'DE AVIÃO', PX0, 125, ACO2)
        else:
            tx(tela, 'MALAS COM PROBLEMA', PX0, 68, ACO3)
            tx(tela, '39%', PX0, 80, VERMELHO, 26)
            tx(tela, 'NA CONEXÃO', PX0 + 64, 86, VERMELHO)
            for k in range(20):
                c = VERMELHO if k < 8 else FUNDO3
                tela.ret(PX0 + (k % 10) * 15, 112 + (k // 10) * 14, 12, 11, c)
            tx(tela, 'SITA, 2025', PX0, 141, ACO2)

    def sons(self, fx):
        for a in (0.0, 14.0):
            for k in range(int(10 * 10)):
                fx.put(fx.pulso(), self.t0 + a + k / 10.0, .05)
        fx.put(fx.explosao(.6), self.t0 + 19.0, .2)
        fx.put(fx.blip(52, .3), self.t0 + 22.2, .12)
        fx.put(fx.blip(79, .1), self.t0 + 23.1, .14); fx.put(fx.blip(84, .2), self.t0 + 23.3, .14)


# ======================================================================= 11 chegada
class Chegada(Cena):
    ETAPA, NOME = 8, ETAPAS[7]
    CX, CY, RX, RY = 150, 146, 118, 30

    def preparar(self):
        rng = np.random.default_rng(9)
        self.estrelas = [(int(rng.integers(0, 300)), int(rng.integers(0, 120)), float(rng.uniform(0, 6))) for _ in range(40)]
        self.malas = [(k * 2 * math.pi / 9 + .3, D.outra(k)) for k in range(9)]
        self.RAMPA = [(-10, 196), (236, 86)]

    def th_prota(self, t):
        if t < 24.6: return None
        return -math.pi / 2 + (t - 24.6) * .33

    def desenhar(self, tela, t, tg):
        if t < 7.6:
            plat = interp([(0, 120), (.4, 120), (4.6, 178)], t)
            if t < 4.6: conts = [(125, plat, True)]
            else:
                u = ease((t - 4.6) / 2.6)
                conts = [(125 - 70 * u, 178 + 8 * u, True)]
            cena_patio(tela, t, self.estrelas, porta=1.0, plat=plat, conts=conts, trem_x=113)
        elif t < 15.2:
            self.rampa(tela, t)
        else:
            self.esteira(tela, t)
        if self.hud(tela, t, tg, u=suave(t / 34.0)):
            self.miolo(tela, t)

    def rampa(self, tela, t):
        D.fundo_bastidor(tela, t, chao=196)
        (ax, ay), (bx, by) = self.RAMPA
        tela.ret(236, 50, 64, 146, FUNDO3); tela.ret(236, 50, 2, 146, TRACO)
        tela.ret(244, 58, 56, 34, PRETO); tela.ret(245, 59, 55, 33, FUNDO)
        tx(tela, 'SAGUÃO', 248, 40, ACO3)
        D.rampa(tela, ax, ay, bx, by, t, 30)
        for xx in range(30, 230, 44):
            yy = ay + (by - ay) * (xx - ax) / (bx - ax)
            tela.ret(xx, int(yy) + 8, 3, int(196 - yy - 8), FUNDO3)
        L = math.hypot(bx - ax, by - ay)
        ang = math.atan2(by - ay, bx - ax)
        for k in range(-3, 6):
            d = (t - 7.6) * 30 + k * 44
            if d < 0 or d > L - 10: continue
            u = d / L
            x, y = ax + (bx - ax) * u, ay + (by - ay) * u
            prota = k == 0
            self.mala_inclinada(tela, x, y, ang, 'prota' if prota else D.outra(k + 5), prota)
            if prota: D.marcador(tela, x + 12, y - 18, t)
        D.cortina(tela, 246, 60, 52, 32, t, .4)

    def mala_inclinada(self, tela, x, y, ang, cor, tag):
        b, l, s = D.CORES[cor]
        ca, sa = math.cos(ang), math.sin(ang)
        def P(u, v): return (x + u * ca - v * sa, y + u * sa + v * ca)
        w, h = 28, 11
        poligono(tela, [P(-1, 1), P(w + 1, 1), P(w + 1, -h - 1), P(-1, -h - 1)], PRETO)
        poligono(tela, [P(0, 0), P(w, 0), P(w, -h), P(0, -h)], b)
        poligono(tela, [P(0, 0), P(w, 0), P(w, -h / 2), P(0, -h / 2)], s)
        tela.linha(*P(1, -h + 1), *P(w - 1, -h + 1), l)
        tela.linha(*P(1, -h / 2), *P(w - 1, -h / 2), PRETO)
        if tag:
            tx_, ty_ = P(w / 2 + 3, -h - 2)
            tela.ret(int(tx_), int(ty_), 5, 7, PRETO); tela.ret(int(tx_) + 1, int(ty_) + 1, 3, 5, CERAMICA)

    def ponto(self, th, dr=0):
        return self.CX + (self.RX - 12 + dr) * math.cos(th), self.CY + (self.RY - 6) * math.sin(th)

    def esteira(self, tela, t):
        tela.buf[:PALCO_H] = FUNDO2
        dither(tela, 0, 0, 300, 30, FUNDO, FUNDO2)
        for y in range(40, 120, 26): tela.ret(0, y, 300, 1, FUNDO3)
        # placa
        painel(tela, 60, 8, 180, 18, borda=AMARELO)
        tx(tela, 'ESTEIRA 5 - VOO 314', 150, 13, AMARELO, centro=True)
        # boca e escorregador
        tela.ret(118, 42, 64, 40, PRETO); tela.ret(119, 43, 62, 39, FUNDO)
        tela.ret(116, 40, 68, 3, ACO1)
        poligono(tela, [(120, 82), (180, 82), (196, 118), (104, 118)], ACO1)
        poligono(tela, [(122, 83), (178, 83), (192, 116), (108, 116)], ACO2)
        for k in range(5): tela.linha(126 + k * 12, 84, 116 + k * 17, 115, ACO1)
        # o carrossel
        cx, cy, rx, ry = self.CX, self.CY, self.RX, self.RY
        yy, xx = np.mgrid[0:PALCO_H, 0:300]
        e_out = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        e_in = ((xx - cx) / (rx - 26)) ** 2 + ((yy - cy) / (ry - 10)) ** 2 <= 1
        sub = tela.buf[:PALCO_H, :300]
        # saia da frente
        saia = (((xx - cx) / rx) ** 2 + ((yy - cy - 12) / ry) ** 2 <= 1) & (yy > cy) & ~e_out
        sub[saia] = ACO0
        sub[saia & ((xx + yy) % 2 == 0) & (yy > cy + ry - 2)] = FUNDO3
        borda = (((xx - cx) / (rx + 1.5)) ** 2 + ((yy - cy) / (ry + 1.5)) ** 2 <= 1) & ~e_out
        sub[borda] = PRETO
        sub[e_out & ~e_in] = ACO1
        # placas de borracha andando
        th = np.arctan2((yy - cy) / ry, (xx - cx) / rx)
        fase = (th - t * .33) % (2 * math.pi / 40)
        sub[e_out & ~e_in & (fase < .03)] = ACO0
        sub[e_out & ~e_in & (((xx - cx) / (rx - 3)) ** 2 + ((yy - cy) / (ry - 1.5)) ** 2 > 1)] = ACO2
        sub[e_in] = ACO2
        sub[e_in & (yy < cy - 4)] = ACO3
        tela.ret(cx - rx + 30, int(cy) - 1, 2 * rx - 60, 1, ACO4)
        # malas no carrossel (de trás para a frente)
        objs = []
        for th0, cor in self.malas:
            a = th0 + t * .33
            objs.append((math.sin(a), a, cor, False))
        tp = self.th_prota(t)
        if tp is not None: objs.append((math.sin(tp), tp, 'prota', True))
        objs.sort()
        for s_, a, cor, prota in objs:
            x, y = self.ponto(a)
            D.mala_lado(tela, x - 13, y + 4, 26, 10, cor, t, tag=prota, balanco=.5)
            if prota: D.marcador(tela, x, y - 12, t)
        # a nossa descendo o escorregador
        if 23.0 <= t < 24.6:
            u = (t - 23.0) / 1.6
            x, y = 150, 82 + (self.CY - 24 - 82) * u ** 1.5
            D.mala_lado(tela, x - 13, y + 4, 26, 10, 'prota', t, tag=True)
            D.marcador(tela, x, y - 12, t)
        # silhuetas de passageiros na frente
        for k, (x, h) in enumerate(((40, 52), (88, 48), (226, 54), (270, 46))):
            D.silhueta(tela, x, PALCO_H + 6, h, PRETO, t, k)

    def miolo(self, tela, t):
        if t < 15.2:
            tx(tela, 'DESEMBARQUE', PX0, 68, ACO3)
            tx(tela, 'PXL', PX0, 82, AMARELO, 26)
            tx(tela, 'DESTINO', PX0 + 62, 88, ACO2)
            tx(tela, 'DO PORÃO AO SAGUÃO', PX0, 118, ACO2)
        elif t < 31.0:
            tx(tela, 'ESTEIRA DE BAGAGEM', PX0, 68, ACO3)
            tx(tela, 'ESTEIRA 5', PX0, 82, BRANCO, 17)
            tx(tela, 'VOO 314', PX0, 102, CIANO, 17)
            if t >= 23.0: tx(tela, 'A SUA ESTÁ CHEGANDO', PX0, 126, AMARELO)
        else:
            tx(tela, 'CONFERÊNCIA', PX0, 68, ACO3)
            tx(tela, 'ETIQUETA', PX0, 82, ACO2); tx(tela, D.PLACA, 468, 82, BRANCO, centro='d')
            tx(tela, 'COMPROVANTE', PX0, 96, ACO2)
            if t > 32.0: tx(tela, D.PLACA, 468, 96, BRANCO, centro='d')
            if t > 33.4:
                painel(tela, PX0 + 6, 112, 150, 24, borda=VERDE)
                tx(tela, 'É SUA!', PX0 + 81, 117, VERDE, 17, centro=True)

    def sons(self, fx):
        fx.put(fx.chiado(4.2, 120, 500, ataque=.3), self.t0 + .4, .1)
        self.zumbido(fx, 7.6, 15.2, .08)
        self.zumbido(fx, 15.2, self.dur, .05)
        fx.put(fx.chiado(1.6, 300, 1500), self.t0 + 23.0, .1)
        fx.put(fx.explosao(.5), self.t0 + 24.6, .2)
        fx.put(fx.blip(84, .1), self.t0 + 33.4, .14); fx.put(fx.blip(91, .2), self.t0 + 33.6, .14)


# ======================================================================= 12 números
class Numeros(Cena):
    VERM = [137, 402, 618, 771, 903]

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        xc = self.xv(tg)
        if t < 23.0:
            if xc is None: x0, y0, cols, cw, ch = 12, 20, 40, 7, 7
            else: x0, y0, cols, cw, ch = xc + 1, 24, 30, 6, 5
            if xc is None: tx(tela, '1.000 PASSAGEIROS', 12, 6, ACO3)
            for i in range(1000):
                ti = .6 + (i // cols) * .12 + (i % cols) * .004
                if t < ti: continue
                x, y = x0 + (i % cols) * cw, y0 + (i // cols) * ch
                red = i in self.VERM and t >= 15.4
                c = VERMELHO if red else (ACO1 if i % 7 else ACO2)
                if xc is None:
                    tela.ret(x, y + 1, 5, 4, c); tela.ret(x + 1, y, 3, 1, c)
                else:
                    tela.ret(x, y + 1, 4, 3, c); tela.px(x + 1, y, c)
                if red and (t * 2) % 1 < .6:
                    tela.anel(x + 2, y + 2, 5, VERMELHO, .6)
        else:
            if xc is None: x0, y0, lado = 30, 22, 16
            else: x0, y0, lado = xc + 10, 22, 16
            cores = [AMARELO] * 75 + [ACO2] * 21 + [VERMELHO] * 4
            for i in range(100):
                ti = 23.2 + (i % 10) * .03 + (i // 10) * .08
                if t < ti: continue
                cx, cy = x0 + (i % 10) * lado, y0 + (i // 10) * lado
                c = cores[i]
                if c == ACO2 and t < 31.0: c = ACO1
                if c == VERMELHO and t < 31.0: c = ACO1
                tela.ret(cx, cy, lado - 3, lado - 3, c)
                tela.px(cx, cy, BRANCO if c == AMARELO else ACO4)
                if c == VERMELHO and (t * 2) % 1 < .6:
                    tela.ret_vazado(cx - 1, cy - 1, lado - 1, lado - 1, CHAMA0)
            if xc is not None:
                tx(tela, 'ATRASOU 75%', xc + 10, 186, AMARELO)
                if t >= 31: tx(tela, 'PERDIDA 4%', xc + 10, 197, VERMELHO)
            else:
                tx(tela, '100 MALAS COM PROBLEMA', x0, 8, ACO3)
        if self.hud(tela, t, tg, cab='EM 2025', nome='RELATÓRIO SITA', etapa=0,
                    rodape=['FONTE: SITA, BAGGAGE', 'IT INSIGHTS 2026', '(DADOS DE 2025)']):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        if t < 23.0:
            tx(tela, '5 BILHÕES', PX0, 68, BRANCO, 17)
            tx(tela, 'DE PASSAGEIROS', PX0, 86, ACO3)
            if t >= 7.8:
                tx(tela, '24 MILHÕES', PX0, 102, AMARELO, 17)
                tx(tela, 'DE MALAS COM PROBLEMA', PX0, 120, ACO3)
            if t >= 15.4:
                tx(tela, '4,9 POR 1.000', PX0, 134, VERMELHO, 9)
                tx(tela, 'PASSAGEIROS', PX0 + 88, 134, VERMELHO) if False else None
        else:
            itens = (('ATRASOU', '75%', AMARELO, 23.0), ('OUTROS', '21%', ACO2, 31.0), ('PERDIDA', '4%', VERMELHO, 31.0))
            for k, (a, b, c, t_on) in enumerate(itens):
                if t < t_on: continue
                y = 70 + k * 24
                tela.ret(PX0, y + 3, 10, 10, c)
                tx(tela, a, PX0 + 16, y + 1, BRANCO, 17)
                tx(tela, b, 468, y + 1, c, 17, centro='d')
            if t >= 31.0: tx(tela, 'OUTROS: DANO, FURTO', PX0, 142, ACO2)

    def sons(self, fx):
        for i in range(0, 25, 2):
            fx.put(fx.blip(64 + i // 2, .04), self.t0 + .6 + i * .12, .05)
        for k in range(5):
            fx.put(fx.blip(57, .12), self.t0 + 15.4 + k * .12, .1)
        for i in range(0, 10):
            fx.put(fx.blip(72 + i, .04), self.t0 + 23.2 + i * .08, .05)
        fx.put(fx.blip(55, .3), self.t0 + 31.0, .12)


# ======================================================================= 13 resumo
NOS = [(36, 50), (106, 50), (176, 50), (246, 50), (246, 140), (176, 140), (106, 140), (36, 140)]


class Resumo(Cena):
    def preparar(self):
        self.L = comprimento(NOS)

    def icone(self, tela, k, x, y, t, aceso):
        painel(tela, x - 16, y - 14, 32, 28, borda=AMARELO if aceso else TRACO, fundo=FUNDO2 if aceso else PRETO)
        if k == 0:
            tela.ret(x - 10, y + 7, 20, 4, ACO1)
            D.mala_frente(tela, x, y + 7, .5, 'prota', t, tag=False)
        elif k == 1:
            D.esteira(tela, x - 13, x + 13, y + 6, t, 20)
            D.mala_lado(tela, x - 8, y + 6, 16, 7, 'prota', t, alca=False)
        elif k == 2:
            D.caixa(tela, x - 12, y - 9, 24, 18, ACO1, ACO2, ACO0)
            tela.ret(x - 6, y - 1, 12, 9, FUNDO)
            poligono(tela, [(x - 4, y - 3), (x, y - 9), (x + 4, y - 3)], AMARELO)
        elif k == 3:
            tela.anel(x, y, 9, ACO1, 2)
            for j in range(6):
                a = t * 1.5 + j * 1.047
                tela.ret(int(x + math.cos(a) * 9) - 2, int(y + math.sin(a) * 9) - 2, 4, 4, ACO3)
        elif k == 4:
            D.ld3(tela, x - 10, y + 9, 20, 17, porta='rede', malas=['prota', 'azul'], nome=False)
        elif k == 5:
            D.trator(tela, x - 13, y + 11, t) if False else None
            tela.ret(x - 12, y + 4, 24, 4, AMARELO); tela.ret(x - 6, y - 4, 2, 8, ACO0); tela.ret(x - 7, y - 5, 10, 2, ACO0)
            tela.disco(x - 8, y + 9, 2.5, PRETO); tela.disco(x + 8, y + 9, 2.5, PRETO)
        elif k == 6:
            poligono(tela, [(x - 12, y), (x + 10, y - 2), (x + 13, y), (x + 10, y + 2)], ACO3)
            poligono(tela, [(x - 2, y), (x + 3, y), (x - 4, y + 7)], ACO2)
            poligono(tela, [(x - 12, y), (x - 8, y), (x - 12, y - 6)], ACO2)
        else:
            tela.anel(x, y + 2, 10, ACO1, 1.5)
            for j in range(4):
                a = t * .8 + j * 1.57
                D.mala_lado(tela, x + math.cos(a) * 9 - 4, y + 2 + math.sin(a) * 3 + 2, 8, 4, 'prota' if j == 0 else D.outra(j), t, alca=False, rodas=False)

    def desenhar(self, tela, t, tg):
        tela.buf[:PALCO_H] = FUNDO
        for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
        for y in range(12, PALCO_H, 24): tela.ret(0, y, W, 1, FUNDO2)
        d = self.L * suave((t - .6) / 14.0)
        # caminho
        for (ax, ay), (bx, by) in zip(NOS, NOS[1:]):
            linha_grossa(tela, ax, ay, bx, by, 4, TRACO)
        feito = 0.0
        for (ax, ay), (bx, by) in zip(NOS, NOS[1:]):
            L = math.hypot(bx - ax, by - ay)
            u = min(1.0, max(0.0, (d - feito) / L))
            if u > 0: linha_grossa(tela, ax, ay, ax + (bx - ax) * u, ay + (by - ay) * u, 2, AMARELO)
            feito += L
        acum = 0.0
        for k, (x, y) in enumerate(NOS):
            if k: acum += math.hypot(x - NOS[k - 1][0], y - NOS[k - 1][1])
            aceso = d >= acum - 1
            self.icone(tela, k, x, y, t, aceso)
            tx(tela, f"{k + 1} {ETAPAS[k]}", x, y + 18, AMARELO if aceso else ACO2, centro=True)
        p = ao_longo(NOS, d) or NOS[-1]
        if t < 16.0:
            D.mala_lado(tela, p[0] - 8, p[1] - 15, 16, 7, 'prota', t, tag=True)
        if t >= 16.4:
            escurecer(tela, 0, 0, 300, PALCO_H)
            u = ease((t - 16.4) / .6)
            dy = int((1 - u) * 120)
            stub = suave((t - 24.4) / 1.2)
            salvo = None
            P = etiqueta_grande(tela, t, dy + 6)
            if stub > 0:
                # o canhoto se solta e desce
                xp = P['canhoto']
                y0 = TAG['y'] + dy + 6
                reg = tela.buf[y0 - 1:y0 + TAG['h'] + 1, xp + 1:TAG['x'] + TAG['w'] + 1].copy()
                tela.buf[y0 - 1:y0 + TAG['h'] + 1, xp + 1:TAG['x'] + TAG['w'] + 2] = FUNDO
                oy = int(stub * 40)
                h_ = min(reg.shape[0], PALCO_H - (y0 - 1 + oy))
                if h_ > 0:
                    tela.buf[y0 - 1 + oy:y0 - 1 + oy + h_, xp + 5:xp + 5 + reg.shape[1]] = reg[:h_]
                if stub >= 1:
                    tx(tela, 'GUARDE!', xp + 18, y0 + TAG['h'] + 4 + 40 - 30, AMARELO, centro=True) if False else None
        if self.hud(tela, t, tg, cab='RESUMO', nome='A JORNADA', etapa=0, u=1.0):
            self.miolo(tela, t)

    def miolo(self, tela, t):
        for k in range(8):
            tela.ret(PX0 + k * 20 + 1, 32, 14, 5, VERDE)
        tx(tela, 'DISTÂNCIA TOTAL', PX0, 68, ACO3)
        tx(tela, '902,1 KM', PX0, 80, AMARELO, 17)
        tx(tela, 'TEMPO TOTAL', PX0, 102, ACO3)
        tx(tela, '3H10', PX0, 114, AMARELO, 17)
        tx(tela, '(VIAGEM DE EXEMPLO)', PX0, 138, ACO2)

    def sons(self, fx):
        for k in range(8):
            tk = .6 + 14.0 * (k / 7.0) ** 1.0
            fx.put(fx.blip(72 + [0, 2, 4, 5, 7, 9, 11, 12][k], .08), self.t0 + tk, .1)
        fx.put(fx.chiado(.6, 2000, 6000), self.t0 + 24.4, .1)


# ======================================================================= 14 fim
class Fim(Cena):
    legenda = False
    brilho = 0.0

    def preparar(self):
        self.vin = list(RM.encerramento(W, H, LG.FPS, ['INSCREVA-SE', 'TEM MAIS A JORNADA'], SEED, baixo=True))

    def desenhar(self, tela, t, tg):
        tela.buf[:] = FUNDO
        if t >= RM.OUTRO_S:
            tela.buf[:] = FUNDO
            for x in range(0, W, 24): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
            tela.buf[PALCO_H:] = FUNDO
            tx(tela, "OBRIGADO POR ASSISTIR!", W // 2, 24, BRANCO, 17, centro=True)
            tx(tela, "NOSSO MUNDO PIXEL", W // 2, 44, AMARELO, 9, centro=True)
            D.esteira(tela, -10, W + 10, 186, t, 40, chao=208)
            x = (t * 40) % (W + 80) - 40
            D.mala_lado(tela, x, 186, 32, 13, 'prota', t, tag=True, balanco=2)

    def pos(self, baixo, t):
        if t < RM.OUTRO_S:
            k = min(len(self.vin) - 1, int(t * LG.FPS))
            return self.vin[k]
        return baixo

    def sons(self, fx):
        fx.put(RM.som_encerramento(SEED), self.t0, .9)


CENAS = dict(gancho=Gancho, titulo=Titulo, despacho=Despacho, etiqueta=Etiqueta, esteira=Esteira,
             inspecao=Inspecao, triagem=Triagem, montagem=Montagem, patio=Patio, voo=Voo, conexao=Conexao,
             chegada=Chegada, numeros=Numeros, resumo=Resumo, fim=Fim)


if __name__ == '__main__':
    import ep03_motor as EP
    if sys.argv[1] == '--folha':
        from PIL import Image
        trilha = LG.Trilha(CAPITULOS, seed=SEED, raiz=RAIZ)
        if len(sys.argv) > 3:
            ts = []
            for a in sys.argv[3:]:
                if ':' in a:
                    cap, s = a.split(':')
                    c = next(x for x in trilha.caps if x['id'] == cap)
                    ts.append(c['t0'] + float(s))
                else:
                    ts.append(float(a))
        else:
            ts = []
            for c in trilha.caps:
                ts += [c['t0'] + c['dur'] * .3, c['t0'] + c['dur'] * .8]
        quadros, _ = LG.renderizar_episodio(EP, 'x.mp4', quadros_amostra=ts)
        ims = [Image.fromarray(q).resize((W * 2, H * 2), Image.NEAREST) for q in quadros]
        cols = 2 if len(ims) > 1 else 1
        o = Image.new('RGB', (cols * W * 2, ((len(ims) + cols - 1) // cols) * H * 2))
        for k, im in enumerate(ims): o.paste(im, ((k % cols) * W * 2, (k // cols) * H * 2))
        o.save(sys.argv[2])
    else:
        print(LG.renderizar_episodio(EP, sys.argv[1], so=sys.argv[2:] or None))
