#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep12 — o desenho: o alto-falante em corte (ímã, placas,
bobina móvel, aranha, cone, borda, carcaça, fios), o alto-falante de frente,
o ar feito de moléculas (onda longitudinal de verdade), gráficos, réguas e
o bumbo da trilha do canal como números.

A paleta do episódio é a `oficina` + cores de cobre, cone, ar e pressão.
Ela é registrada como 'ep12' e o `longo` passa a usá-la neste processo.

O AR: cada molécula tem um lugar de descanso x0 e é deslocada por
u(x0, t) = D(t - (x0 - xa) / c), onde D é o deslocamento do cone e c a
velocidade da onda no desenho. É a onda plana longitudinal: a molécula só
vai e volta em torno do seu lugar; quem anda é a compressão. A cor do fundo
é -du/dx (ar apertado = quente, ar espalhado = frio).
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
import ritmo_musica as M
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, BAYER8, FUNDO, FUNDO2, FUNDO3, TRACO,
                   ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO,
                   ROSA, ROXO, LATAO, MISTURA, MISTURA2, CHAMA1, BRASA, OLEO0, OLEO1)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#4a200e', '#9a4a22', '#d9803f', '#ffc78a',      # 32..35 cobre (bobina)
          '#18161c', '#2b2830', '#45404d', '#6c6577',      # 36..39 cone (papel escuro)
          '#252b3a', '#3a4560',                            # 40..41 ímã (ferrite)
          '#11283a', '#1f5a7a', '#45a6cf', '#9fe6ff',      # 42..45 ar (moléculas)
          '#2c1622', '#4e2232', '#7a3040',                 # 46..48 ar apertado
          '#0e1734', '#16245a',                            # 49..50 ar espalhado
          '#6e5a34', '#b39a5e',                            # 51..52 tecido da aranha
          '#3a2414', '#5e3b20', '#86592f',                 # 53..55 madeira da caixa
          '#123a26', '#1f6a40']                            # 56..57 placa de circuito
PX.PALETAS['ep12'] = _BASE + _EXTRA
LG.PAL = 'ep12'
(COBRE0, COBRE1, COBRE2, COBRE3, CONE0, CONE1, CONE2, CONE3, IMA0, IMA1, AR0, AR1, AR2, AR3,
 APE0, APE1, APE2, ESP0, ESP1, TEC0, TEC1, MAD0, MAD1, MAD2, PCB0, PCB1) = range(32, 58)

SR_VIDEO = LG.SR             # 48.000: a taxa de amostragem do áudio deste canal (longo.py)


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def milhar(n):
    s = f"{abs(int(round(n))):,}".replace(',', '.')
    return ('-' if n < 0 else '') + s
def sinal(n): return ('+' if n >= 0 else '') + milhar(n)
def clamp(u, a=0.0, b=1.0): return max(a, min(b, u))
def lerp(a, b, u): return a + (b - a) * u


# ------------------------------------------------------------------ o bumbo do canal
# O bumbo lo-fi do ritmo_musica não usa ruído: a conta é sempre a mesma, e é
# exatamente a que toca nos capítulos lo-fi deste vídeo (antes da mixagem).
KICK = M.Bateria(np.random.default_rng(0), 'lofi')._kick()
KICK16 = np.round(KICK * 32767).astype(np.int64)


# ------------------------------------------------------------------ curvas
class Curva:
    """Deslocamento do cone no tempo (px), amostrado numa grade fina para o ar
    poder perguntar D(t - x/c) de um vetor de x de uma vez."""

    def __init__(self, fn, t0=-6.0, t1=60.0, dt=1 / 600):
        self.g = np.arange(t0, t1, dt)
        self.v = np.array([fn(x) for x in self.g], np.float64)

    @classmethod
    def de_tabela(cls, g, v):
        o = cls.__new__(cls); o.g = np.asarray(g, float); o.v = np.asarray(v, float); return o

    def __call__(self, t):
        return np.interp(t, self.g, self.v, left=self.v[0], right=self.v[-1])


def curva_seno(trechos, t0=-6.0, t1=60.0, dt=1 / 600):
    """trechos = função t -> (freq_visual_hz, amplitude_px). A fase é integrada
    (troca de frequência sem salto)."""
    g = np.arange(t0, t1, dt)
    f = np.array([trechos(x)[0] for x in g]); a = np.array([trechos(x)[1] for x in g])
    fase = np.cumsum(f) * dt * 2 * math.pi
    return Curva.de_tabela(g, a * np.sin(fase))


# ------------------------------------------------------------------ textos
def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9):
    """Texto com fio até a peça (o fio sai do lado do texto mais perto da peça)."""
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    tela.linha(ex, hy + 1, ax, ay + 1, PRETO)
    tela.linha(ex, hy, ax, ay, cor)
    tela.disco(ax, ay, 2, PRETO); tela.disco(ax, ay, 1.2, cor)
    tela.ret(ex - 1, hy - 1, 3, 3, cor)
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)


def centro_preso(tela, txt, cx, y, cor, tam=9, xmin=2, xmax=296):
    w = tela.largura_texto(txt, tam)
    x = int(min(max(cx - w / 2, xmin), xmax - w))
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def seta(tela, x0, y0, x1, y1, cor, esp=2, ponta=5):
    """Seta grossa com ponta e contorno, de (x0, y0) para (x1, y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * ponta, y1 - uy * ponta
    linha_grossa(tela, x0, y0, bx, by, esp + 2, PRETO)
    linha_grossa(tela, x0, y0, bx, by, esp, cor)
    nx, ny = -uy, ux
    poligono(tela, [(x1 + ux * 1.5, y1 + uy * 1.5), (bx + nx * (ponta + 1.5), by + ny * (ponta + 1.5)),
                    (bx - nx * (ponta + 1.5), by - ny * (ponta + 1.5))], PRETO)
    poligono(tela, [(x1, y1), (bx + nx * ponta, by + ny * ponta), (bx - nx * ponta, by - ny * ponta)], cor)


def bloco(tela, x0, y0, x1, y1, corpo, luz, sombra, textura=None):
    """Peça maciça: contorno preto, corpo, filete de luz em cima, sombra embaixo
    e meio-tom em xadrez na metade de baixo."""
    x0, x1 = sorted((int(round(x0)), int(round(x1)))); y0, y1 = sorted((int(round(y0)), int(round(y1))))
    if x1 - x0 < 1 or y1 - y0 < 1: return
    tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
    tela.ret(x0, y0, x1 - x0, y1 - y0, corpo)
    if y1 - y0 >= 4:
        dither(tela, x0, y0 + (y1 - y0) * 2 // 3, x1 - x0, (y1 - y0) - (y1 - y0) * 2 // 3, corpo, sombra)
    tela.ret(x0, y0, x1 - x0, 1, luz)
    tela.ret(x0, y1 - 1, x1 - x0, 1, sombra)
    if textura is not None and x1 - x0 > 3:
        for k in range(y0 + 2, y1 - 1, 3):
            tela.px(x0 + 1 + (k * 7) % max(1, x1 - x0 - 2), k, textura)


def grade_fundo(tela, x1=W, passo=16):
    tela.buf[:PALCO_H, :x1] = FUNDO
    for x in range(0, x1, passo): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(8, PALCO_H, passo): tela.ret(0, y, x1, 1, FUNDO2)


# ------------------------------------------------------------------ alto-falante em corte
PECAS = ('ima', 'bobina', 'cone', 'aranha', 'borda', 'carcaca', 'fios')


class Corte:
    """Geometria do alto-falante cortado ao meio, eixo na horizontal, cone
    virado para +x (ou para -x com espelho=-1). Unidades: px em s=1."""
    APEX, RA = -8.0, 9.0          # vértice do cone (onde cola a bobina) e raio
    ARO, RR = 24.0, 50.0           # beira do cone
    BOB = (-31.0, -18.5)           # bobina (x) em repouso
    FACE = 30.0                    # frente do aro (onde o ar começa)

    def __init__(self, cx, cy, s=1.0, espelho=1):
        self.cx, self.cy, self.s, self.e = cx, cy, s, espelho

    def P(self, x, y):
        return self.cx + self.e * x * self.s, self.cy + y * self.s

    def face_x(self): return self.P(self.FACE, 0)[0]

    def desenhar(self, tela, d=0.0, corrente=0.0, pecas=None, t=0.0, campo=False, fantasma=(),
                 destaque=None, rotulo_membrana=False):
        """d = deslocamento do cone (px na tela, + = para fora). corrente em -1..1
        acende a bobina e mostra o sentido da corrente no corte do fio
        (ponto = saindo da tela, x = entrando)."""
        pecas = set(PECAS if pecas is None else pecas) | set(fantasma)
        s, e = self.s, self.e
        du = d / s                                   # deslocamento em unidades do desenho
        P = self.P
        pisca = destaque is not None and int(t * 4) % 2 == 0

        def cor_de(nome, c):
            return c

        # ---- carcaça (atrás de tudo): hastes da placa de cima até o aro
        if 'carcaca' in pecas:
            for sg in (-1, 1):
                ax, ay = P(-22, 34 * sg); bx, by = P(27, 57 * sg)
                linha_grossa(tela, ax, ay, bx, by, 4.5 * s, PRETO)
                linha_grossa(tela, ax, ay, bx, by, 2.6 * s, ACO1)
                linha_grossa(tela, ax, ay - .6 * s * sg, bx, by - .6 * s * sg, .9 * s, ACO3)
                x0, y0 = P(26, 55 * sg); x1, y1 = P(31, 63 * sg)
                bloco(tela, x0, y0, x1, y1, ACO2, ACO4, ACO0)
                # suporte da aranha
                x0, y0 = P(-16, 33 * sg); x1, y1 = P(-11, 39 * sg)
                bloco(tela, x0, y0, x1, y1, ACO1, ACO3, ACO0)
        # ---- ímã e placas de ferro (o "motor")
        if 'ima' in pecas:
            x0, y0 = P(-50, -34); x1, y1 = P(-44, 34)
            bloco(tela, x0, y0, x1, y1, ACO2, ACO4, ACO0, ACO1)                 # placa de trás
            x0, y0 = P(-44, -7); x1, y1 = P(-17, 7)
            bloco(tela, x0, y0, x1, y1, ACO2, ACO4, ACO0, ACO1)                 # polo central
            for sg in (-1, 1):
                x0, y0 = P(-44, 13.5 * sg); x1, y1 = P(-29, 34 * sg)
                bloco(tela, x0, y0, x1, y1, IMA1, ACO1, IMA0, FUNDO3)            # ímã (anel)
                x0, y0 = P(-29, 13.5 * sg); x1, y1 = P(-22, 34 * sg)
                bloco(tela, x0, y0, x1, y1, ACO2, ACO4, ACO0, ACO1)             # placa da frente
            if s >= .8:
                for sg in (-1, 1):
                    xa, ya = P(-32.5, 24 * sg); xb, yb = P(-40.5, 24 * sg)
                    tela.texto('N', xa - 2, ya - 3, VERMELHO, tam=9, contorno=PRETO)
                    tela.texto('S', xb - 2, yb - 3, MISTURA2, tam=9, contorno=PRETO)
            if campo:
                # campo na fenda: da placa da frente (N) para o polo central, atravessando a bobina
                for sg in (-1, 1):
                    for k in range(4):
                        xx = -28 + k * 1.9
                        xa, ya = P(xx, 13.3 * sg); xb, yb = P(xx, 7.2 * sg)
                        f = (t * 2.5 + k * .25) % 1.0
                        tela.px(xa, ya + (yb - ya) * f, AMARELO)
                        tela.px(xa, ya + (yb - ya) * ((f + .5) % 1.0), AMARELO)
        # ---- aranha (tecido ondulado do tubo da bobina até a carcaça)
        if 'aranha' in pecas:
            for sg in (-1, 1):
                pts = []
                n = 14
                for i in range(n + 1):
                    u = i / n
                    y = (8.6 + (35 - 8.6) * u) * sg
                    x = -13.5 + du * (1 - u) + (1.6 if i % 2 else -1.6) * (0 < i < n)
                    pts.append(P(x, y))
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    linha_grossa(tela, ax, ay, bx, by, 2.6 * s, PRETO)
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    linha_grossa(tela, ax, ay, bx, by, 1.2 * s, TEC1 if destaque != 'aranha' or not pisca else AMARELO)
                for (ax, ay) in pts[1:-1:2]: tela.px(ax, ay, TEC0)
        # ---- bobina e o tubo dela (andam com o cone)
        if 'bobina' in pecas:
            b0, b1 = self.BOB
            for sg in (-1, 1):
                ax, ay = P(b0 + du, 8.2 * sg); bx, by = P(self.APEX + du, 8.2 * sg)
                linha_grossa(tela, ax, ay, bx, by, 1.8 * s, PRETO)
                linha_grossa(tela, ax, ay, bx, by, .9 * s, CERAMICA_TUBO)
                x0, y0 = P(b0 + du, 8.7 * sg); x1, y1 = P(b1 + du, 12.6 * sg)
                acesa = abs(corrente) > .05
                corpo = COBRE2 if acesa else COBRE1
                bloco(tela, x0, y0, x1, y1, corpo, COBRE3 if acesa else COBRE2, COBRE0)
                xa, xb = sorted((x0, x1)); ya, yb = sorted((y0, y1))
                # espiras: um corte de fio a cada passo
                passo = max(3, int(round(2.6 * s)))
                for xx in range(int(xa) + 1, int(xb) - 1, passo):
                    tela.ret(xx + passo - 1, ya + 1, 1, max(1, yb - ya - 2), COBRE0)
                    if acesa:
                        # sentido da corrente no corte do fio: ponto (sai) ou x (entra)
                        sai = (corrente > 0) == (sg < 0)
                        mx, my = xx + (passo - 1) / 2, (ya + yb) / 2
                        if sai:
                            tela.px(mx, my, BRANCO)
                            if passo >= 4: tela.px(mx + 1, my, BRANCO)
                        else:
                            for ddx, ddy in ((-1, -1), (1, 1), (-1, 1), (1, -1), (0, 0)):
                                tela.px(mx + ddx, my + ddy, BRANCO)
                if destaque == 'bobina' and pisca:
                    tela.ret_vazado(xa - 2, ya - 2, xb - xa + 4, yb - ya + 4, AMARELO)
        # ---- cone (parede grossa) e tampa
        if 'cone' in pecas:
            # o lado de dentro do cone (a metade de trás, vista pelo corte)
            pts = [P(self.APEX + du, -self.RA), P(self.ARO + du, -self.RR), P(self.ARO + du, self.RR),
                   P(self.APEX + du, self.RA)]
            ys = [p[1] for p in pts]
            xs_ = [p[0] for p in pts]
            ya_, yb_ = int(min(ys)), int(max(ys)) + 1
            xa_, xb_ = int(min(xs_)), int(max(xs_)) + 1
            if xb_ > xa_ and yb_ > ya_:
                poligono(tela, pts, 254)
                reg = tela.buf[max(0, ya_):yb_, max(0, xa_):xb_]
                m = reg == 254
                yy, xx = np.mgrid[max(0, ya_):yb_, max(0, xa_):xb_]
                v = (yy - self.cy) / (self.RR * s)            # -1 em cima .. 1 embaixo
                b8 = BAYER8[yy % 8, xx % 8]
                lv = .55 - .45 * v + (b8 - .5) * .5
                cores = np.array([CONE0, CONE1, CONE2])
                reg[m] = cores[np.clip((lv[m] * 2.2).astype(int), 0, 2)]
                # anéis do papel (vistos de lado viram linhas)
                for k in (1, 2, 3):
                    u = k / 4
                    xr_ = P(self.APEX + du + (self.ARO - self.APEX) * u, 0)[0]
                    rr = (self.RA + (self.RR - self.RA) * u) * s
                    tela.ret(xr_, self.cy - rr + 2, 1, 2 * rr - 3, CONE0)
            for sg in (-1, 1):
                ax, ay = P(self.APEX + du, self.RA * sg); bx, by = P(self.ARO + du, self.RR * sg)
                linha_grossa(tela, ax, ay, bx, by, 4.4 * s, PRETO)
                linha_grossa(tela, ax, ay, bx, by, 2.8 * s, CONE2 if destaque != 'cone' or not pisca else CONE3)
                # luz na face de dentro (a que olha para a frente)
                ox, oy = .9 * s * e, -sg * .9 * s
                linha_grossa(tela, ax + ox, ay + oy, bx + ox, by + oy, .9 * s, CONE3)
                # nervuras do papel
                for k in range(1, 6):
                    u = k / 6
                    px_, py_ = ax + (bx - ax) * u, ay + (by - ay) * u
                    tela.px(px_, py_, CONE1)
            # tampa (domo) no centro
            pts = []
            for k in range(13):
                a = -math.pi / 2 + k * math.pi / 12
                pts.append(P(self.APEX + du + 7.5 * math.cos(a), self.RA * 1.02 * math.sin(a)))
            poligono(tela, [(x - 1 * e, y) for x, y in pts], PRETO)
            poligono(tela, pts, CONE2)
            cx_, cy_ = P(self.APEX + du + 3, -3)
            tela.disco(cx_, cy_, 2.2 * s, CONE3)
            tela.px(cx_ - 1, cy_ - 1, ACO4)
        # ---- borda (meia-cana de borracha entre o cone e o aro)
        if 'borda' in pecas:
            for sg in (-1, 1):
                xi, yi = self.ARO + du, self.RR * sg
                xo, yo = 27.0, 56.0 * sg
                mx, my = (xi + xo) / 2, (yi + yo) / 2
                r = math.hypot(xo - xi, yo - yi) / 2
                ang0 = math.atan2(yi - my, xi - mx)
                pts = [P(mx + r * math.cos(ang0 - k * math.pi / 8 * sg), my + r * math.sin(ang0 - k * math.pi / 8 * sg))
                       for k in range(9)]
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    linha_grossa(tela, ax, ay, bx, by, 3.2 * s, PRETO)
                for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                    linha_grossa(tela, ax, ay, bx, by, 1.7 * s,
                                 CONE1 if destaque != 'borda' or not pisca else CONE3)
                tela.px(*pts[4], CONE3)
        # ---- fios do sinal (cordão flexível da bobina até os terminais)
        if 'fios' in pecas:
            for sg in (-1, 1):
                a = P(-24 + du, 12 * sg); b = P(-17 + du * .5, 26 * sg); c = P(-9, 44 * sg)
                for (ax, ay), (bx, by) in ((a, b), (b, c)):
                    linha_grossa(tela, ax, ay, bx, by, 2.2 * s, PRETO)
                    linha_grossa(tela, ax, ay, bx, by, .9 * s, LATAO)
                x0, y0 = P(-12, 43 * sg); x1, y1 = P(-6, 47 * sg)
                bloco(tela, x0, y0, x1, y1, LATAO, AMARELO, OLEO0)
        # ---- peças que ainda não foram apresentadas: meio apagadas
        return self

    def terminais(self):
        return [self.P(-9, 45 * sg) for sg in (-1, 1)]


CERAMICA_TUBO = 27           # CERAMICA da oficina (tubo da bobina, papel claro)


def apagar_pecas(tela, x0, y0, x1, y1):
    """Fora de foco: metade dos pixels vira fundo (xadrez)."""
    x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(PALCO_H, int(y1))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sub = tela.buf[y0:y1, x0:x1]
    sub[((xx + yy) % 2 == 0) & (sub != FUNDO)] = FUNDO2


# ------------------------------------------------------------------ alto-falante de frente
_RAMPA_CONE = [CONE0, CONE1, CONE2, CONE3, ACO3]


def falante_frente(tela, cx, cy, R, d=0.0, t=0.0, aro=ACO1):
    """Alto-falante visto de frente: carcaça com parafusos, borda de borracha,
    cone em degradê com dither e a tampa. d > 0 = cone vindo para a frente:
    a tampa cresce e o cone clareia um pouco."""
    Rt = R + 8
    x0, x1 = int(cx - Rt - 1), int(cx + Rt + 2)
    y0, y1 = int(cy - Rt - 1), int(cy + Rt + 2)
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x1), min(PALCO_H, y1)
    if xb <= xa or yb <= ya: return
    yy, xx = np.mgrid[ya:yb, xa:xb]
    dx, dy = xx - cx + .5, yy - cy + .5
    r = np.sqrt(dx * dx + dy * dy) + 1e-6
    luz = -(dx + dy) / (r * 1.4142)                  # luz de cima à esquerda (-1..1)
    bay = BAYER8[yy % 8, xx % 8]
    sub = tela.buf[ya:yb, xa:xb]
    out = sub.copy()
    # carcaça
    m = r <= R + 8
    out[m] = PRETO
    m = r <= R + 7
    out[m] = np.where(luz[m] * .5 + .5 + (bay[m] - .5) * .5 > .55, ACO2, aro)
    # borda de borracha
    m = r <= R + 3
    v = np.clip(.5 + .45 * luz[m] * np.cos((r[m] - R) / 3 * 1.5) + (bay[m] - .5) * .35, 0, .999)
    out[m] = np.array([CONE0, CONE1, CONE2, CONE3])[(v * 4).astype(int)]
    m = (r > R - 2.6) & (r <= R - 1.6)
    out[m] = PRETO
    # cone: degradê do aro (escuro) para o centro (claro), lado de baixo-direita mais claro (côncavo)
    Rc = R - 2.6
    m = r <= Rc
    u = r[m] / Rc
    v = .25 + .35 * (1 - u) - .22 * luz[m] * (u ** .5) + .06 * d + (bay[m] - .5) * .55
    rid = (np.abs(((u * 5) % 1) - .5) < .07)
    v = np.where(rid, v - .18, v)
    out[m] = np.array(_RAMPA_CONE)[np.clip((v * 5).astype(int), 0, 4)]
    # tampa
    Rd = R * .3 * (1 + .035 * d)
    m = r <= Rd + 1
    out[m] = PRETO
    m = r <= Rd
    v = .55 + .4 * luz[m] * (r[m] / Rd) + (bay[m] - .5) * .4 + .04 * d
    out[m] = np.array([CONE1, CONE2, CONE3, ACO3, ACO4])[np.clip((v * 4).astype(int), 0, 4)]
    sub[:] = out
    # parafusos
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        bx_, by_ = cx + math.cos(a) * (R + 5), cy + math.sin(a) * (R + 5)
        tela.disco(bx_, by_, 1.8, PRETO); tela.disco(bx_, by_, 1.2, ACO3); tela.px(bx_ - .5, by_ - .5, ACO4)
    # brilho de luz na tampa
    tela.px(cx - Rd * .45, cy - Rd * .45, BRANCO)


# ------------------------------------------------------------------ o ar
class Ar:
    """Moléculas num retângulo. A onda vem do lado esquerdo (xa) e anda para a
    direita a c px/s (ou o contrário com sentido=-1)."""

    def __init__(self, x0, x1, y0, y1, passo=7, seed=1, xa=None, sentido=1):
        rng = np.random.default_rng(seed)
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.xa = x0 if xa is None else xa
        self.sentido = sentido
        gx, gy = np.meshgrid(np.arange(x0 + 3, x1 - 2, passo), np.arange(y0 + 3, y1 - 2, passo))
        n = gx.size
        self.xr = gx.ravel() + rng.uniform(-2, 2, n)
        self.yr = gy.ravel() + rng.uniform(-2, 2, n)
        self.fa = rng.uniform(0, 2 * math.pi, n); self.fb = rng.uniform(0, 2 * math.pi, n)
        self.wa = rng.uniform(2.5, 5.0, n)
        self.some = rng.random(n)                    # ordem em que somem no vácuo
        alvo = (x0 + (x1 - x0) * .38, (y0 + y1) / 2)
        self.prota = int(np.argmin((self.xr - alvo[0]) ** 2 + (self.yr - alvo[1]) ** 2))
        self.rastro = []

    def atraso(self, x, c):
        return (x - self.xa) / c if self.sentido > 0 else (self.xa - x) / c

    def u(self, x, t, D, c):
        return D(t - self.atraso(x, c)) * self.sentido

    def compressao(self, t, D, c):
        cols = np.arange(self.x0, self.x1, dtype=float)
        uc = self.u(cols, t, D, c)
        comp = -np.gradient(uc)
        comp[self.atraso(cols, c) > t + 30] = 0
        return cols, comp

    def desenhar(self, tela, t, D, c, escala=.25, vacuo=0.0, prota=False, bandas=True, tremor=.6,
                 cor=AR2, clip=None):
        x0, x1, y0, y1 = self.x0, self.x1, self.y0, self.y1
        cols, comp = self.compressao(t, D, c)
        lev = np.clip(comp / max(escala, 1e-6), -1, 1) * (1 - vacuo)
        if bandas:
            yy, xx = np.mgrid[y0:y1, x0:x1]
            ch = (xx + yy) % 2 == 0
            L = lev[None, :].repeat(y1 - y0, 0)
            b8 = BAYER8[yy % 8, xx % 8]
            out = np.full(L.shape, FUNDO, np.uint8)
            out = np.where(L > .15, np.where(ch, APE0, FUNDO), out)
            out = np.where(L > .4, np.where(b8 < (L - .4) / .6 + .2, APE1, APE0), out)
            out = np.where(L > .8, np.where(ch, APE2, APE1), out)
            out = np.where(L < -.15, np.where(ch, ESP0, FUNDO), out)
            out = np.where(L < -.5, np.where(b8 < (-L - .5) / .5 + .3, ESP1, ESP0), out)
            reg = tela.buf[y0:y1, x0:x1]
            reg[:] = np.where(reg == FUNDO, out, np.where(reg == FUNDO2, np.where(L > .4, APE0, np.where(L < -.5, ESP0, FUNDO2)), reg))
        n = len(self.xr)
        vis = self.some >= vacuo
        ux = self.u(self.xr, t, D, c)
        jx = np.sin(t * self.wa + self.fa) * tremor
        jy = np.cos(t * self.wa * .8 + self.fb) * tremor
        x = np.round(self.xr + ux + jx).astype(int)
        y = np.round(self.yr + jy).astype(int)
        xc0, xc1 = (x0, x1 - 2) if clip is None else clip
        ok = vis & (x >= xc0) & (x < xc1) & (y >= y0) & (y < y1 - 1)
        # cor pela pressão local
        ic = np.clip(np.round(self.xr - x0).astype(int), 0, len(lev) - 1)
        lv = lev[ic]
        claro = lv > .45
        x, y, claro = x[ok], y[ok], claro[ok]
        B = tela.buf
        B[y, x] = np.where(claro, AR3, cor); B[y, x + 1] = cor
        B[y + 1, x] = AR1; B[y + 1, x + 1] = AR1
        B[y, x] = np.where(claro, AR3, B[y, x])
        if prota and vis[self.prota]:
            px_ = self.xr[self.prota] + ux[self.prota]
            py_ = self.yr[self.prota]
            xr = self.xr[self.prota]
            # marca do lugar de descanso
            tela.ret(xr, py_ - 9, 1, 4, ROSA); tela.ret(xr, py_ + 6, 1, 4, ROSA)
            tela.anel(px_, py_ + .5, 5.2, ROSA, esp=.5)
            tela.disco(px_, py_ + .5, 3.8, PRETO)
            tela.disco(px_, py_ + .5, 3.0, ROSA)
            tela.px(px_ - 1, py_ - 1, BRANCO); tela.px(px_, py_ - 1, BRANCO)
        return cols, lev

    def pos_prota(self, t, D, c):
        return self.xr[self.prota] + float(self.u(self.xr[self.prota], t, D, c)), self.yr[self.prota]


# ------------------------------------------------------------------ gráficos
def osc(tela, x, y, w, h, vals, cor=CIANO, zero=True, grade=True, fundo=True, esp=1, ymax=1.0):
    """Tela de osciloscópio: vals (len qualquer, -ymax..ymax) desenhados da
    esquerda para a direita."""
    if fundo: painel(tela, x - 2, y - 2, w + 4, h + 4)
    if grade:
        for gx in range(x + 8, x + w, 16):
            for gy in range(y + 2, y + h, 4): tela.px(gx, gy, FUNDO2)
        for gy in (y + h // 4, y + 3 * h // 4):
            for gx in range(x + 2, x + w, 4): tela.px(gx, gy, FUNDO2)
    if zero: tela.ret(x, y + h // 2, w, 1, FUNDO3)
    n = len(vals)
    if n < 2: return
    xs = x + np.arange(n) * (w - 1) / (n - 1)
    ys = y + h / 2 - np.clip(np.asarray(vals, float) / ymax, -1, 1) * (h / 2 - 1)
    for i in range(n - 1):
        tela.linha(xs[i], ys[i], xs[i + 1], ys[i + 1], cor)
        if esp > 1: tela.linha(xs[i], ys[i] + 1, xs[i + 1], ys[i + 1] + 1, cor)


LOG20, LOG20K = math.log10(20), math.log10(20000)


def x_hz(x, w, f): return x + w * (math.log10(f) - LOG20) / (LOG20K - LOG20)


def regua_hz(tela, x, y, w, rotulos=True):
    """Régua logarítmica de 20 Hz a 20.000 Hz."""
    tela.ret(x - 1, y - 1, w + 2, 6, PRETO)
    tela.ret(x, y, w, 4, FUNDO3)
    for f in (20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        xx = x_hz(x, w, f)
        tela.ret(xx, y - 2, 1, 8, ACO2 if f in (20, 200, 2000, 20000) else ACO0)
    if rotulos:
        for f, txt in ((20, '20'), (200, '200'), (2000, '2.000'), (20000, '20.000')):
            xx = x_hz(x, w, f)
            tw = tela.largura_texto(txt, 9)
            tela.texto(txt, int(min(max(xx - tw / 2, x - 2), x + w - tw + 2)), y + 8, ACO3, tam=9, contorno=PRETO)


def faixa_hz(tela, x, y, w, f0, f1, cor, alto=4):
    a, b = x_hz(x, w, f0), x_hz(x, w, f1)
    tela.ret(a, y, b - a, alto, cor)
    tela.ret(a, y, b - a, 1, BRANCO if cor not in (ACO1, ACO2) else ACO4)


def medidor(tela, x, y, w, h, v, cor, centro=False):
    """Barra de nível. v em 0..1 (ou -1..1 com centro=True)."""
    painel(tela, x - 1, y - 1, w + 2, h + 2)
    if centro:
        mx = x + w // 2
        tela.ret(mx, y - 2, 1, h + 4, ACO2)
        a = int(round(abs(v) * (w // 2 - 1)))
        if v >= 0: tela.ret(mx + 1, y + 1, a, h - 2, cor)
        else: tela.ret(mx - a, y + 1, a, h - 2, cor)
    else:
        a = int(round(clamp(v) * (w - 2)))
        tela.ret(x + 1, y + 1, a, h - 2, cor)
        tela.ret(x + 1, y + 1, a, 1, BRANCO)


def ouvido(tela, cx, cy, s=1.0, cor=None, luz=None):
    """Orelha genérica de perfil, virada para a esquerda (só a forma)."""
    cor = LATAO if cor is None else cor
    luz = AMARELO if luz is None else luz
    pts = []
    for k in range(25):
        a = -math.pi * .62 + k * math.pi * 1.3 / 24
        r = 15 * s * (1 + .18 * math.sin(a))
        pts.append((cx + math.cos(a) * r * .75, cy + math.sin(a) * r * 1.15))
    pts.append((cx - 2 * s, cy + 12 * s)); pts.append((cx - 4 * s, cy + 2 * s))
    poligono(tela, [(x + 1, y + 1) for x, y in pts], PRETO)
    poligono(tela, [(x - 1, y - 1) for x, y in pts], PRETO)
    poligono(tela, pts, cor)
    for k in range(9):
        a = -math.pi * .5 + k * math.pi * .9 / 8
        tela.px(cx + 1 * s + math.cos(a) * 9 * s * .75, cy - 2 * s + math.sin(a) * 9 * s, luz)
    tela.disco(cx - 1 * s, cy + 1 * s, 2.6 * s, PRETO)


ROSA_PELE = LATAO
PELE2 = MAD1
