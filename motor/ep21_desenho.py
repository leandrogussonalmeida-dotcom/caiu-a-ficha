#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep21 — o desenho: o vaso sanitário com caixa acoplada,
visto de lado e cortado ao meio, e a física da descarga em "passos".

O vaso é genérico (louça branca, sem marca). Coordenadas da tela 480x270,
palco y 0..208, o vaso inteiro cabe em x 46..226 (180 px: cabe no corte
vertical). `dx` empurra o vaso inteiro para os lados.

  caixa        x 150..224, y 34..116 (por dentro 154..220, 38..112)
               6 L = 54 px de água (nível cheio em y 58); o LADRÃO (tubo
               de transbordo) abre em y 52: a água nunca passa dele
  comporta     vedação de borracha sobre o furo do fundo (x 182..204), com
               dobradiça no ladrão; uma corrente liga à alavanca do botão
  válvula de   coluna à esquerda (x 158..164) com a BOIA (copo que corre na
  entrada      coluna) e o tubinho de reabastecimento até a boca do ladrão
  aro          canal oco y 119..125 de x 50 até o furo da caixa, com furos
               embaixo (x 62..142); da frente do aro desce o canal do JATO
  sifão        tubo de raio 6 que sai do fundo da bacia, sobe até a crista
               (beira de baixo do tubo em y 163 = nível da água parada) e
               desce até o esgoto, no piso

A descarga inteira é uma função de um "passo" p (0..5, uma ETAPA por
unidade): `ciclo(p, vol)` devolve o estado (litros na caixa, comporta,
nível da bacia, quanto do lado que desce do sifão está cheio, etc.).
Regras de física que o estado respeita: a caixa nunca passa do nível cheio
(abaixo do ladrão); o sifão só puxa (`sif`) com o lado que desce 100% cheio;
o ar só entra quando o nível da bacia desce abaixo da boca do sifão.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, suave, ease,
                   FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO,
                   LARANJA, OLEO0, OLEO1, VERMELHO, CHAMA0, CHAMA1, CHAMA2, BRASA, MISTURA, MISTURA2,
                   GAS, GAS2, AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA)

VAZIO = 255
CHEIO_Y = 58          # nível da caixa cheia (6 L)
FUNDO_CX = 112        # fundo da caixa por dentro
LADRAO_Y = 52         # boca do ladrão
PX_L = (FUNDO_CX - CHEIO_Y) / 6.0     # px por litro na caixa
NIVEL0 = 163          # nível da água parada na bacia (= beira de baixo da crista do sifão)
BOCA_Y = 176          # abaixo disso o ar entra no sifão
NIVEL_MAX = 150       # o mais alto que a bacia sobe na descarga
NIVEL_MIN = 186       # o mais baixo (depois do glug)
PISO = 196

B4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')


def curva(p, pts):
    """Interpolação linear entre marcos [(p, valor)]."""
    xs = [a for a, _ in pts]; ys = [b for _, b in pts]
    return float(np.interp(p, xs, ys))


def rampa(t, marcos):
    if t <= marcos[0][0]: return marcos[0][1]
    for (a, x), (b, y) in zip(marcos, marcos[1:]):
        if t <= b: return x + (y - x) * suave((t - a) / max(1e-6, b - a))
    return marcos[-1][1]


# ================================================================ a descarga em passos
def ciclo(p, vol=6.0, caixa=True):
    """Estado da descarga no passo p (0..5). vol = litros da descarga
    (6 = completa, 3 = meia). Sem caixa (válvula de parede) a água vem do cano."""
    e = {}
    meia = vol < 5.0
    e['botao'] = rampa(p, [(.12, 0), (.15, 1), (.27, 1), (.31, 0)]) if not meia else 0.0
    e['botao_meio'] = rampa(p, [(.12, 0), (.15, 1), (.27, 1), (.31, 0)]) if meia else 0.0
    p_fecha = 2.75 if not meia else 1.55
    abre = rampa(p, [(.15, 0), (.36, 1)])
    fecha = rampa(p, [(p_fecha, 1), (p_fecha + .1, 0)])
    e['flap'] = min(abre, fecha)
    # litros na caixa: desce com a comporta aberta, sobe depois que ela fecha
    if p < p_fecha + .1:
        if meia:
            V = curva(p, [(.3, 6.0), (1.0, 4.6), (1.55, 3.0)])
        else:
            V = curva(p, [(.3, 6.0), (1.0, 4.6), (2.0, 2.2), (2.75, 0.0)])
    else:
        V0 = 6.0 - vol
        if meia:
            V = curva(p, [(1.65, V0), (4.0, 4.6), (4.5, 5.6), (4.85, 6.0)])
        else:
            V = curva(p, [(2.85, 0.0), (4.0, 1.0), (4.5, 3.9), (4.85, 6.0)])
    e['V'] = min(6.0, max(0.0, V))
    e['usados'] = min(vol, 6.0 - e['V']) if p < p_fecha + .1 else vol
    e['entrada'] = .33 < p < 4.85 and e['V'] < 5.99
    # vazão da caixa para a bacia (0..1) e a frente da primeira água no canal
    e['q'] = e['flap'] * (.35 + .65 * math.sqrt(max(0.0, e['V']) / 6.0)) if e['V'] > .02 else 0.0
    e['canal'] = rampa(p, [(.36, 0), (.95, 1)])
    e['refil'] = 1.0 if e['entrada'] else 0.0
    # bacia e sifão
    e['Lb'] = curva(p, [(0, NIVEL0), (.95, NIVEL0), (1.7, NIVEL_MAX), (2.2, NIVEL_MAX), (3.08, BOCA_Y),
                        (3.25, NIVEL_MIN), (4.0, NIVEL_MIN), (4.8, NIVEL0), (5, NIVEL0)])
    e['f'] = curva(p, [(0, 0), (1.25, 0), (1.35, .15), (2.0, .8), (2.2, 1.0), (3.08, 1.0), (3.75, 0.0), (5, 0)])
    e['sif'] = 2.2 <= p < 3.08
    e['ar'] = rampa(p, [(3.05, 0), (3.12, 1), (3.6, 1), (3.85, 0)]) if 3.05 <= p < 3.85 else 0.0
    e['caixa'] = caixa
    e['p'] = p
    return e


def estado_txt(e):
    """Textos do painel."""
    if e['sif']: s = ('PUXANDO!', AMARELO)
    elif e['ar'] > 0: s = ('ENTROU AR', CIANO)
    elif e['f'] > .02: s = ('ENCHENDO', MISTURA2)
    else: s = ('PARADO', ACO3)
    return s


ETAPAS = [('APERTAR', 'A VEDAÇÃO ABRE', VERMELHO),
          ('A ÁGUA DESCE', 'ARO E JATO', MISTURA2),
          ('O SIFÃO PUXA', 'CANO CHEIO', AMARELO),
          ('GLUG!', 'O AR ENTRA', CIANO),
          ('REENCHER', 'BOIA E VÁLVULA', VERDE)]


# ================================================================ máscaras
def _mask_poli(pts):
    tmp = PX.Tela(W, H, paleta=LG.PAL)
    tmp.buf[:] = 0
    poligono(tmp, pts, 1)
    return tmp.buf == 1


def _tubo(pts, r):
    """Máscara de um tubo (linha de centro `pts`, raio r) com, para cada
    pixel, a posição ao longo do tubo (S, px) e o lado (N, px; + = esquerda
    de quem anda no sentido do tubo)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xx += .5; yy += .5
    best = np.full((H, W), 1e9, np.float32)
    S = np.zeros((H, W), np.float32); N = np.zeros((H, W), np.float32)
    acc = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1
        u = np.clip(((xx - ax) * dx + (yy - ay) * dy) / (L * L), 0, 1)
        d = np.hypot(xx - (ax + u * dx), yy - (ay + u * dy))
        n = ((xx - ax) * dy - (yy - ay) * dx) / L
        sel = d < best
        best[sel] = d[sel]; S[sel] = acc + u[sel] * L; N[sel] = n[sel]
        acc += L
    return best <= r, S, N, acc


def _ponto(pts, s):
    """Ponto a uma distância s ao longo da linha."""
    acc = 0.0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        if s <= acc + L or (bx, by) == pts[-1]:
            u = max(0.0, min(1.0, (s - acc) / max(L, 1e-6)))
            return ax + (bx - ax) * u, ay + (by - ay) * u
        acc += L
    return pts[-1]


def _comprimento(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _borda(m):
    """Pixels da máscara que encostam em algo fora dela."""
    e = m.copy()
    e[1:] &= m[:-1]; e[:-1] &= m[1:]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
    return m & ~e


def _dilata(m, k=1):
    o = m.copy()
    for _ in range(k):
        n = o.copy()
        n[1:] |= o[:-1]; n[:-1] |= o[1:]; n[:, 1:] |= o[:, :-1]; n[:, :-1] |= o[:, 1:]
        o = n
    return o


# ================================================================ o banheiro
def fundo_banheiro(tela, t, x0=0, x1=W, parede=True):
    """Azulejo na parede, piso cortado embaixo."""
    yy, xx = np.mgrid[0:PISO, x0:x1]
    base = np.where(((xx + yy) % 2 == 0) & (yy > 120), FUNDO2, FUNDO2)
    base = np.where((yy < 60) & ((xx + yy) % 2 == 0), FUNDO, base)
    rej = ((xx % 20) == 0) | ((yy % 20) == 0)
    base = np.where(rej, FUNDO3, base)
    brilho = ((xx % 20) == 1) & ((yy % 20) == 1)
    base = np.where(brilho, TRACO, base)
    tela.buf[0:PISO, x0:x1] = base
    # rodapé + piso (corte da laje)
    tela.ret(x0, PISO - 3, x1 - x0, 3, TRACO)
    tela.ret(x0, PISO, x1 - x0, PALCO_H - PISO, FUNDO3)
    yy, xx = np.mgrid[PISO:PALCO_H, x0:x1]
    hach = ((xx + yy) % 6 == 0)
    tela.buf[PISO:PALCO_H, x0:x1][hach] = TRACO
    tela.ret(x0, PISO, x1 - x0, 1, ACO1)


def parede_corte(tela, x=228, larg=8):
    """A parede atrás do vaso, cortada (de onde sai o cano de água)."""
    tela.ret(x, 0, larg, PISO, TRACO)
    yy, xx = np.mgrid[0:PISO, x:x + larg]
    tela.buf[0:PISO, x:x + larg][(xx + yy) % 5 == 0] = FUNDO3
    tela.ret(x, 0, 1, PISO, ACO1)
    tela.ret(x + larg - 1, 0, 1, PISO, FUNDO2)


# ================================================================ o vaso
class Vaso:
    def __init__(self, dx=0, caixa=True):
        self.dx = dx
        self.tem_caixa = caixa
        X = lambda x: x + dx
        self.X = X
        # --- louça (fora)
        ext = [(46, 116), (224, 116), (224, 128), (210, 132), (198, 140), (191, 152), (188, 170), (190, 188),
               (194, PISO), (80, PISO), (84, 184), (78, 176), (68, 168), (58, 158), (50, 146), (45, 134), (44, 124)]
        self.EXT = _mask_poli([(X(a), b) for a, b in ext])
        cx_ext = [(150, 36), (224, 36), (224, 116), (150, 116)]
        tampa = [(147, 30), (227, 30), (227, 35), (147, 35)]
        self.CX_EXT = _mask_poli([(X(a), b) for a, b in cx_ext]) if caixa else np.zeros((H, W), bool)
        self.TAMPA = _mask_poli([(X(a), b) for a, b in tampa]) if caixa else np.zeros((H, W), bool)
        # --- cavidades
        bacia = [(56, 128), (150, 128), (147, 138), (140, 148), (132, 156), (126, 164), (124, 172), (124, 178),
                 (120, 190), (100, 192), (92, 186), (84, 174), (72, 162), (62, 148), (57, 136)]
        self.BACIA = _mask_poli([(X(a), b) for a, b in bacia])
        self.SIF_PTS = [(X(a), b) for a, b in [(108, 184), (126, 184), (138, 178), (146, 170), (152, 162),
                                                (160, 157), (168, 160), (174, 170), (178, 184), (180, 214)]]
        self.R_SIF = 6
        m, S, N, L = _tubo(self.SIF_PTS, self.R_SIF)
        self.SIF, self.S, self.N, self.L_SIF = m, S, N, L
        self.S_CRISTA = _comprimento(self.SIF_PTS[:6])
        self.SOBE = m & (S < self.S_CRISTA)
        self.DESCE = m & (S >= self.S_CRISTA)
        self.ARO_PTS = [(X(a), b) for a, b in [(193, 112), (193, 122), (150, 122), (52, 122)]]
        self.ARO = _mask_poli([(X(50), 119), (X(200), 119), (X(200), 125), (X(50), 125)])
        self.DUTO = _mask_poli([(X(188), 108), (X(199), 108), (X(199), 120), (X(188), 120)]) if caixa else \
            _mask_poli([(X(196), 112), (X(206), 112), (X(206), 120), (X(196), 120)])
        self.JATO_PTS = [(X(a), b) for a, b in [(51, 122), (51, 136), (55, 148), (63, 160), (74, 171), (84, 180),
                                                 (90, 185), (97, 188)]]
        mj, SJ, _, LJ = _tubo(self.JATO_PTS, 2.0)
        self.JATO, self.SJ, self.L_JATO = mj & ~self.BACIA, SJ, LJ
        self.FUROS = [X(x) for x in range(62, 146, 10)]
        self.CX_IN = _mask_poli([(X(154), 38), (X(220), 38), (X(220), FUNDO_CX), (X(154), FUNDO_CX)]) if caixa \
            else np.zeros((H, W), bool)
        self.CAV = self.BACIA | self.SIF | self.ARO | self.DUTO | self.JATO | self.CX_IN
        for x in self.FUROS:
            self.CAV[125:128, x:x + 2] = True
        self.LOUCA = (self.EXT | self.CX_EXT | self.TAMPA) & ~self.CAV
        self.LOUCA[:, :] &= True
        self._base()

    # ------------------------------------------------------------ camadas fixas
    def _base(self):
        yy, xx = np.mgrid[0:H, 0:W]
        # vista em corte: face cortada (creme com hachura) + cavidades escuras
        c = np.full((H, W), VAZIO, np.uint8)
        L = self.LOUCA
        face = np.where((xx - yy) % 7 == 0, ACO4, CERAMICA)
        c[L] = face[L]
        # sombra da face perto das cavidades (dá profundidade ao corte)
        perto = _dilata(self.CAV, 1) & L
        c[perto] = ACO3
        # cavidade: o fundo de louça visto lá atrás, em sombra
        fundo_cav = np.where(((xx + yy) % 2 == 0) & (yy > 150), FUNDO3, ACO0)
        fundo_cav = np.where((yy < 140) & ((xx + yy) % 2 == 0), ACO1, fundo_cav)
        c[self.CAV] = fundo_cav[self.CAV]
        cx_f = np.where((xx + yy) % 2 == 0, FUNDO3, FUNDO2)
        c[self.CX_IN] = cx_f[self.CX_IN]
        tudo = self.EXT | self.CX_EXT | self.TAMPA
        c[_borda(tudo)] = PRETO
        c[_borda(self.CAV) & ~_borda(tudo)] = TRACO
        self.base_corte = c
        # vista de fora: louça inteira com volume
        f = np.full((H, W), VAZIO, np.uint8)
        f[tudo] = CERAMICA
        luz = tudo & ~_dilata(~tudo, 3)
        sombra_b = tudo & ~np.roll(_dilata(~tudo, 2), -3, axis=1)
        f[tudo & (xx > self.X(170)) & (yy > 130)] = ACO4
        f[tudo & (yy > 182)] = ACO4
        dith = tudo & (yy > 176) & ((xx + yy) % 2 == 0)
        f[dith] = ACO3
        borda2 = _borda(tudo) | _borda(_dilata(_borda(tudo), 0))
        f[_dilata(_borda(tudo), 1) & tudo & (yy > 140)] = ACO3
        # brilho em cima da tampa, do aro e na frente da caixa
        f[self.TAMPA & (yy == 31)] = BRANCO
        f[tudo & (yy >= 117) & (yy <= 118) & (xx < self.X(146))] = BRANCO
        f[self.CX_EXT & (xx >= self.X(154)) & (xx <= self.X(156)) & (yy > 40) & (yy < 110)] = BRANCO
        f[self.CX_EXT & (xx >= self.X(216))] = ACO4
        # linha da junção caixa / bacia e da tampa
        f[(yy == 116) & tudo] = ACO3
        f[(yy == 35) & tudo] = ACO3
        f[_borda(tudo)] = PRETO
        self.base_fora = f

    def colar(self, tela, cam, x0=0, x1=W):
        sub = cam[:, x0:x1]
        m = sub != VAZIO
        tela.buf[:, x0:x1][m] = sub[m]

    # ------------------------------------------------------------ desenho
    def desenhar(self, tela, e, t, corte=True, corte_x=None, mecanismo=True, cano_parede=False):
        """Desenha o vaso no estado `e` (de `ciclo`). corte_x: até onde o
        corte já foi revelado (o resto aparece fechado)."""
        if corte_x is None:
            self.colar(tela, self.base_corte if corte else self.base_fora)
            if not corte:
                self._botoes(tela, e)
                return
        else:
            cx = int(max(0, min(W, corte_x)))
            self.colar(tela, self.base_corte, 0, cx)
            self.colar(tela, self.base_fora, cx, W)
            # a lâmina do corte
            if 0 < cx < W:
                tela.ret(cx, 20, 1, PISO - 20, AMARELO)
                tela.ret(cx + 1, 20, 1, PISO - 20, CHAMA0)
        self._agua(tela, e, t)
        if self.tem_caixa and mecanismo:
            self._mecanismo(tela, e, t)
        self._botoes(tela, e)
        if corte_x is not None:
            cx = int(max(0, min(W, corte_x)))
            sub = self.base_fora[:, cx:]
            m = sub != VAZIO
            tela.buf[:, cx:][m] = sub[m]
            self._botoes(tela, e, x_min=cx)

    # ------------------------------------------------------------ água
    def _agua(self, tela, e, t):
        X = self.X
        yy, xx = np.mgrid[0:H, 0:W]
        buf = tela.buf
        # --- caixa
        if self.tem_caixa:
            ny = FUNDO_CX - e['V'] * PX_L
            onda = (np.sin(xx * .35 + t * 3.1) * .6 + np.sin(xx * .13 - t * 1.7) * .5)
            if e['q'] > .05:   # descendo: um redemoinho fundo perto do furo
                onda = onda + 2.5 * e['q'] * np.exp(-((xx - X(193)) / 9.0) ** 2)
            sup = ny + onda
            m = self.CX_IN & (yy >= sup)
            agua = np.where(((xx + yy) % 2 == 0) & (yy > ny + 18), FUNDO3, MISTURA)
            agua = np.where((yy > ny + 34) & ((xx + yy) % 2 == 1), FUNDO3, agua)
            buf[m] = agua[m]
            linha = self.CX_IN & (yy >= sup) & (yy < sup + 1.2)
            buf[linha] = MISTURA2
            if ny < FUNDO_CX - 1:
                for k in range(5):
                    x = X(158 + (k * 17 + int(t * 9)) % 60)
                    tela.px(x, int(ny + .5), BRANCO)
        # --- duto + aro + jato (com a primeira água avançando)
        q = e['q'] if self.tem_caixa else e.get('qv', 0.0)
        refil = e['refil'] * (1 if self.tem_caixa else 0)
        flui = max(q, .35 * refil)
        if flui > .01:
            frente = e['canal'] if q > .01 else 1.0
            # a água vai do furo para a frente: x da frente
            xf = X(200) - frente * (X(200) - X(50))
            mA = (self.ARO | self.DUTO) & (xx >= xf)
            if q < .01:     # só o fiozinho do reabastecimento: pouca água no fundo do canal
                mA = self.DUTO & (xx >= X(188)) & (xx <= X(199)) | (self.ARO & (yy >= 124) & (xx > X(52)))
            ag = np.where(((xx * 1 + int(t * 40)) % 9 < 2) & (yy % 3 == 0), MISTURA2, MISTURA)
            buf[mA] = ag[mA]
            # furos: fios caindo pela parede da bacia até a água
            if frente > .05:
                for k, x in enumerate(self.FUROS):
                    if x < xf: continue
                    y0 = 128
                    y1 = self._sup_bacia(x, e, t)
                    if y1 <= y0: continue
                    n = 3 if q > .01 else 1
                    for j in range(n):
                        u = (t * (2.2 + .3 * (k % 3)) + j / n + k * .37) % 1.0
                        yb = y0 + u * (y1 - y0)
                        xb = x + (1 if k % 2 else 0) + int(u * (2 if x < X(100) else -2))
                        tela.ret(xb, int(yb), 1, 3, MISTURA2 if j == 0 else MISTURA)
                    tela.px(x, 128, MISTURA2)
            # jato
            if q > .01 and frente > .98:
                mJ = self.JATO
                agj = np.where(((self.SJ - t * 60) % 10) < 3, MISTURA2, MISTURA)
                buf[mJ] = agj[mJ]
        # --- bacia + sifão
        Lb = e['Lb']
        onda = np.sin(xx * .3 - t * 2.4) * .7 + np.sin(xx * .11 + t * 1.3) * .5
        if q > .05 and e['f'] < 1: onda = onda + np.sin(xx * .9 + t * 13) * .6 * q
        sup = Lb + onda
        corpo = (self.BACIA | self.SOBE)
        if e['sif']:
            corpo_ag = (self.BACIA & (yy >= sup)) | self.SOBE | self.DESCE
        else:
            corpo_ag = corpo & (yy >= sup)
            # lado que desce: a correnteza encosta na parede de fora e vai engrossando
            f = e['f']
            if f > .005:
                r = self.R_SIF
                lado = self.DESCE & (-self.N > r - f * 2 * r - .5)
                corpo_ag = corpo_ag | lado
        if e['ar'] > 0:
            # o ar entrou: a coluna do sifão se rompe em bolsões
            fr = e['f']
            ar_m = self.SIF & (((self.S - t * 70) % 26) > 26 * max(.15, fr))
            corpo_ag = (corpo_ag | (self.SIF & (self.S > self.S_CRISTA - 8) & (-self.N > self.R_SIF - fr * 2 * self.R_SIF))) & ~ar_m
            corpo_ag = corpo_ag | (self.BACIA & (yy >= sup))
        prof = yy - sup
        ag = np.where(((xx + yy) % 2 == 0) & (prof > 14), FUNDO3, MISTURA)
        corr = e['sif'] or e['f'] > .02
        if corr:
            vel = 90 if e['sif'] else 45
            listra = (((self.S - t * vel) % 12) < 2) & self.SIF
            ag = np.where(listra, MISTURA2, ag)
        buf[corpo_ag] = ag[corpo_ag]
        lin = self.BACIA & (yy >= sup) & (yy < sup + 1.2)
        buf[lin] = MISTURA2
        for k in range(4):
            x = X(76 + (k * 13 + int(t * 7)) % 50)
            y = int(self._sup_bacia(x, e, t) + .5)
            if self.BACIA[min(H - 1, y), min(W - 1, x)]: tela.px(x, y, BRANCO)
        # cano do piso (esgoto)
        xs = int(X(180))
        tela.ret(xs - 7, PISO, 2, PALCO_H - PISO, ACO1)
        tela.ret(xs + 6, PISO, 2, PALCO_H - PISO, ACO1)
        tela.ret(xs - 5, PISO, 11, PALCO_H - PISO, PRETO)
        if e['sif'] or e['f'] > .05:
            w = 11 if e['sif'] else max(2, int(e['f'] * 9))
            for y in range(PISO, PALCO_H):
                tela.ret(xs + 6 - w, y, w, 1, MISTURA2 if (y * 3 + int(t * 60)) % 7 == 0 else MISTURA)
        # jato saindo embaixo d'água
        if q > .01 and e['canal'] > .98 and Lb < 186:
            for j in range(6):
                u = (t * 2.6 + j / 6) % 1.0
                x = X(98) + u * 22
                y = 188 - u * 3 + (j % 2)
                tela.ret(int(x), int(y), 3, 1, MISTURA2)

    def _sup_bacia(self, x, e, t):
        return e['Lb'] + math.sin(x * .3 - t * 2.4) * .7 + math.sin(x * .11 + t * 1.3) * .5

    # ------------------------------------------------------------ peças da caixa
    def boia_y(self, e):
        ny = FUNDO_CX - e['V'] * PX_L
        return max(55.0, min(FUNDO_CX - 5.0, ny - 4))     # topo do copo da boia

    def pontos(self):
        """Pontos de cada peça, para os fios dos rótulos."""
        X = self.X
        return dict(caixa=(X(214), 92), botao=(X(189), 27), botao_meio=(X(202), 27), alavanca=(X(186), 44),
                    comporta=(X(190), 107), ladrao=(X(207), 70), boia=(X(161), 62), entrada=(X(161), 96),
                    refil=(X(186), 47), aro=(X(100), 122), furos=(X(92), 127), jato=(X(57), 150),
                    sifao=(X(160), 152), crista=(X(160), 163), fecho=(X(118), 170), esgoto=(X(180), 200),
                    bacia=(X(90), 160))

    def _mecanismo(self, tela, e, t):
        X = self.X
        # --- válvula de entrada (coluna) e cano que entra por baixo
        tela.ret(X(158) - 1, 50, 8, FUNDO_CX - 50 + 5, PRETO)
        tela.ret(X(158), 50, 6, FUNDO_CX - 50 + 4, ACO2)
        tela.ret(X(158), 50, 1, FUNDO_CX - 50 + 4, ACO4)
        tela.ret(X(163), 50, 1, FUNDO_CX - 50 + 4, ACO1)
        if e['entrada']:
            for k in range(5):
                y = FUNDO_CX + 2 - ((t * 40 + k * 12) % 60)
                tela.ret(X(160), int(y), 2, 3, CIANO)
        # cabeça da válvula
        tela.ret(X(154), 44, 15, 10, PRETO)
        tela.ret(X(155), 45, 13, 8, ACO3)
        tela.ret(X(155), 45, 13, 1, ACO4)
        tela.ret(X(155), 52, 13, 1, ACO1)
        luz = VERDE if e['entrada'] else VERMELHO
        tela.ret(X(165), 47, 2, 2, luz)
        # bico (a água nova cai na caixa)
        tela.ret(X(152), 51, 3, 6, PRETO); tela.ret(X(153), 51, 1, 5, ACO2)
        if e['entrada']:
            ny = FUNDO_CX - e['V'] * PX_L
            for k in range(6):
                u = (t * 2.8 + k / 6) % 1.0
                y = 57 + u * (ny - 57)
                tela.ret(X(153) - (k % 2), int(y), 1, 2, MISTURA2 if k % 2 else CIANO)
        # boia (copo que corre na coluna)
        by = self.boia_y(e)
        tela.ret(X(155) - 1, int(by) - 1, 14, 11, PRETO)
        tela.ret(X(155), int(by), 12, 9, VERDE)
        tela.ret(X(155), int(by), 12, 2, CHAMA0 if False else BRANCO)
        tela.ret(X(155), int(by) + 7, 12, 2, AGUA1)
        tela.ret(X(158), int(by) + 2, 6, 5, AGUA0)
        # haste da boia até a cabeça
        tela.ret(X(166), 53, 1, max(1, int(by) - 53), ACO3)
        # --- tubinho de reabastecimento: da cabeça até a boca do ladrão
        pts = []
        for k in range(15):
            u = k / 14
            x = X(168) + u * (X(209) - X(168))
            y = 48 - math.sin(u * math.pi) * 5 + u * 2
            pts.append((x, y))
        for (ax, ay), (bx, by_) in zip(pts, pts[1:]):
            linha_grossa(tela, ax, ay, bx, by_, 3, PRETO)
        for (ax, ay), (bx, by_) in zip(pts, pts[1:]):
            tela.linha(ax, ay, bx, by_, ACO1)
        if e['refil'] > 0:
            for k in range(3):
                u = (t * 1.6 + k / 3) % 1.0
                x, y = pts[int(u * 14)]
                tela.px(x, y, CIANO)
        # --- ladrão (tubo de transbordo)
        lx = X(204)
        tela.ret(lx - 1, LADRAO_Y - 1, 8, FUNDO_CX - LADRAO_Y + 1, PRETO)
        tela.ret(lx, LADRAO_Y, 6, FUNDO_CX - LADRAO_Y, ACO2)
        tela.ret(lx, LADRAO_Y, 1, FUNDO_CX - LADRAO_Y, ACO4)
        tela.ret(lx + 5, LADRAO_Y, 1, FUNDO_CX - LADRAO_Y, ACO0)
        tela.ret(lx + 1, LADRAO_Y, 4, 1, PRETO)
        if e['refil'] > 0:
            for k in range(4):
                y = LADRAO_Y + ((t * 50 + k * 15) % (FUNDO_CX - LADRAO_Y))
                tela.ret(lx + 2, int(y), 2, 2, CIANO)
        # marca de nível cheio
        for x in range(X(170), X(202), 4):
            tela.px(x, CHEIO_Y - 1, ACO3)
        # --- assento da comporta e a comporta
        tela.ret(X(181), FUNDO_CX - 3, 24, 3, PRETO)
        tela.ret(X(182), FUNDO_CX - 3, 4, 3, ACO3)
        tela.ret(X(199), FUNDO_CX - 3, 5, 3, ACO3)
        hx, hy = X(204), FUNDO_CX - 5
        a = math.radians(70 * e['flap'])
        tx, ty = hx - 22 * math.cos(a), hy - 22 * math.sin(a)
        linha_grossa(tela, hx, hy, tx, ty, 6, PRETO)
        linha_grossa(tela, hx, hy, tx, ty, 4, VERMELHO)
        tela.linha(hx, hy - 1.5, tx, ty - 1.5, ROSA)
        tela.disco(hx, hy, 2.2, PRETO); tela.disco(hx, hy, 1.2, ACO3)
        # água saindo pelo furo
        if e['q'] > .02:
            for k in range(6):
                u = (t * 3.2 + k / 6) % 1.0
                x = X(189) + (k * 3) % 10
                tela.ret(x, int(FUNDO_CX - 3 + u * 9), 1, 2, MISTURA2)
        # --- alavanca e corrente
        pvx, pvy = X(198), 44
        b = math.radians(30 * max(e['botao'], e['botao_meio'] * .55))
        lx_, ly_ = pvx - 22 * math.cos(b), pvy - 22 * math.sin(b)
        rx_, ry_ = pvx + 6 * math.cos(b), pvy + 6 * math.sin(b)
        linha_grossa(tela, lx_, ly_, rx_, ry_, 4, PRETO)
        linha_grossa(tela, lx_, ly_, rx_, ry_, 2, ACO3)
        tela.disco(pvx, pvy, 1.6, ACO4)
        # haste do botão até a ponta curta da alavanca
        tela.ret(int(rx_), 35, 1, max(1, int(ry_) - 35), ACO2)
        # corrente: da ponta da alavanca até a ponta da comporta (com folga)
        cx0, cy0 = lx_ + 1, ly_ + 1
        cx1, cy1 = tx + 2 * math.cos(a), ty - 1
        dist = math.hypot(cx1 - cx0, cy1 - cy0)
        folga = max(0.0, 62.0 - dist)
        n = int(dist / 2) + 1
        for k in range(n + 1):
            u = k / max(1, n)
            x = cx0 + (cx1 - cx0) * u + math.sin(u * math.pi) * folga * .6
            y = cy0 + (cy1 - cy0) * u
            tela.px(x, y, ACO4 if k % 2 == 0 else ACO1)

    def _botoes(self, tela, e, x_min=0):
        if not self.tem_caixa: return
        X = self.X
        d1 = int(round(3 * e['botao']))
        d2 = int(round(3 * e['botao_meio']))
        if X(181) >= x_min:
            tela.ret(X(181), 25 + d1, 16, 6 - d1, PRETO)
            tela.ret(X(182), 26 + d1, 14, 4 - d1, ACO4 if d1 < 2 else ACO3)
            tela.ret(X(182), 26 + d1, 14, 1, BRANCO)
        if X(198) >= x_min:
            tela.ret(X(198), 26 + d2, 9, 5 - d2, PRETO)
            tela.ret(X(199), 27 + d2, 7, 3 - d2, ACO4 if d2 < 2 else ACO3)
            tela.ret(X(199), 27 + d2, 7, 1, BRANCO)

    # ------------------------------------------------------------ caminhos
    def caminho_gota(self, e):
        """Posição da GOTA protagonista no passo p (ou None)."""
        X = self.X
        p = e['p']
        if p < .4:
            u = p / .4
            return X(176) + 14 * u, 96 + 8 * u
        if p < 1.0:
            u = (p - .4) / .6
            pts = [(X(190), 104), (X(193), 112), (X(193), 122), (X(96), 122)]
            return _ponto(pts, u * _comprimento(pts))
        if p < 1.35:
            u = (p - 1.0) / .35
            y1 = self._sup_bacia(X(96), e, 0) + 1
            return X(96) + u * 4, 128 + u * (y1 - 128)
        if p < 2.2:
            u = (p - 1.35) / .85
            y1 = self._sup_bacia(X(100), e, 0) + 2
            return X(100) + u * 12, y1 + u * (182 - y1)
        if p < 2.9:
            u = (p - 2.2) / .7
            return _ponto(self.SIF_PTS, u * self.L_SIF)
        if p < 4.0:
            return None
        if p < 4.9:
            u = (p - 4.0) / .9
            pts = [(X(168), 48), (X(188), 44), (X(207), 50), (X(207), 108), (X(194), 116), (X(194), 122),
                   (X(110), 122), (X(110), 128), (X(110), 163)]
            return _ponto(pts, u * _comprimento(pts))
        return X(110), self._sup_bacia(X(110), e, 0) + 2


def gota(tela, x, y, t, marca=True, cor=CIANO):
    """A gota protagonista: contorno escuro, brilho, anel amarelo que pulsa."""
    if marca:
        r = 6 + math.sin(t * 6) * 1.2
        tela.anel(x, y, r, AMARELO, .5)
    tela.disco(x, y + 1, 2.6, PRETO)
    tela.ret(int(x) - 1, int(y) - 3, 2, 2, PRETO)
    tela.disco(x, y + 1, 1.8, cor)
    tela.px(x, y - 2, cor)
    tela.px(x - 1, y, BRANCO)


def bolha(tela, x, y, r=1.5):
    tela.anel(x, y, r, MISTURA2, .5)
    tela.px(x - .5, y - .8, BRANCO)


def bolhas_sifao(V, tela, e, t):
    """Bolsões de ar subindo pelo sifão no glug."""
    if e['ar'] <= 0: return
    for k in range(5):
        u = (t * .9 + k / 5) % 1.0
        x, y = _ponto(V.SIF_PTS, u * V.S_CRISTA)
        bolha(tela, x + math.sin(u * 8 + k) * 2, y - 1, 1.6 + 1.2 * e['ar'] * (1 - u))
    x0 = V.X(118)
    for k in range(3):
        u = (t * 1.3 + k / 3) % 1.0
        bolha(tela, x0 - 4 + k * 4, 184 - u * 10, 1.2)


# ================================================================ rótulos e painel
def rotulo(tela, txt, x, y, cor=BRANCO, centro=False):
    tela.texto(txt, x, y, cor, tam=9, centro=centro, contorno=PRETO)


def etiqueta_fio(tela, txt, lx, ly, px_, py_, cor=AMARELO, centro=True):
    """Etiqueta com moldura e fio até a peça (bolinha na ponta)."""
    w = tela.largura_texto(txt, 9)
    x0 = lx - w // 2 if centro else lx
    # o fio sai do lado da etiqueta mais perto da peça
    ax = min(max(px_, x0 - 2), x0 + w + 2)
    ay = ly + 9 if py_ > ly + 8 else (ly - 3 if py_ < ly - 3 else ly + 3)
    tela.linha(ax, ay, px_, py_, PRETO)
    tela.linha(ax, ay - 1 if ay > py_ else ay, px_, py_, cor)
    tela.disco(px_, py_, 1.8, PRETO)
    tela.disco(px_, py_, 1.0, cor)
    painel(tela, x0 - 4, ly - 3, w + 8, 13, borda=cor)
    tela.texto(txt, x0, ly, cor, tam=9)


def medidor(tela, x, y, w, h, frac, t, cor=MISTURA, marca=None):
    """Visor vertical (caixa): água subindo de baixo."""
    frac = max(0.0, min(1.0, frac))
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    dither(tela, x, y, w, h, FUNDO, FUNDO2)
    n = int(round(frac * h))
    if n > 0:
        dither(tela, x, y + h - n, w, n, cor, FUNDO3)
        if n < h:
            d = 1 if math.sin(t * 3) > .4 else 0
            tela.ret(x, y + h - n - d, w, 1, MISTURA2)
    for k in range(1, 6):
        tela.ret(x + w - 3, y + h * k // 6, 3, 1, ACO3)
    if marca is not None:
        tela.ret(x - 3, y + int(h * (1 - marca)), w + 6, 1, AMARELO)
    tela.ret(x - 1, y - 1, 1, h + 2, ACO3); tela.ret(x + w, y - 1, 1, h + 2, ACO1)


def barra(tela, x, y, w, frac, cor):
    tela.ret(x, y, w, 6, PRETO)
    tela.ret(x + 1, y + 1, w - 2, 4, FUNDO2)
    n = int((w - 2) * max(0.0, min(1.0, frac)))
    if n > 0:
        tela.ret(x + 1, y + 1, n, 4, cor)
        tela.ret(x + 1, y + 1, n, 1, BRANCO)


def seta_dir(tela, x, y, dx, dy, comp, cor, esp=2, cabeca=4):
    L = math.hypot(dx, dy) or 1
    dx, dy = dx / L, dy / L
    xa, ya = x - dx * comp, y - dy * comp
    xb, yb = x - dx * cabeca, y - dy * cabeca
    nx, ny = -dy, dx
    linha_grossa(tela, xa, ya, xb, yb, esp + 2, PRETO)
    poligono(tela, [(x + dx * 1.5, y + dy * 1.5), (xb + nx * (cabeca + 1), yb + ny * (cabeca + 1)),
                    (xb - nx * (cabeca + 1), yb - ny * (cabeca + 1))], PRETO)
    linha_grossa(tela, xa, ya, xb, yb, esp, cor)
    poligono(tela, [(x, y), (xb + nx * cabeca, yb + ny * cabeca), (xb - nx * cabeca, yb - ny * cabeca)], cor)


def manometro(tela, cx, cy, r, u, cor=AMARELO):
    tela.disco(cx, cy, r + 2, PRETO)
    tela.disco(cx, cy, r + 1, ACO3)
    tela.disco(cx, cy, r, FUNDO2)
    for k in range(7):
        a = math.radians(210 - 240 * k / 6)
        for s in (r - 3, r - 1):
            tela.px(cx + s * math.cos(a), cy - s * math.sin(a), BRANCO if k % 2 == 0 else ACO3)
    u = max(0.0, min(1.0, u))
    a = math.radians(210 - 240 * u)
    xp, yp = cx + (r - 3) * math.cos(a), cy - (r - 3) * math.sin(a)
    tela.linha(cx, cy, xp, yp, cor)
    tela.linha(cx + .5, cy, xp + .5, yp, cor)
    tela.disco(cx, cy, 1.6, PRETO); tela.px(cx, cy, ACO4)


def garrafa(tela, x, y, frac, t, cor=MISTURA, esc=1):
    """Garrafa de 1 litro (10x18 vezes esc), cheia até frac. (x, y) = canto de cima."""
    e = esc
    tela.ret(x - e, y + 3 * e, 12 * e, 16 * e, PRETO)
    tela.ret(x + 2 * e, y - e, 6 * e, 5 * e, PRETO)
    tela.ret(x, y + 4 * e, 10 * e, 14 * e, FUNDO2)
    tela.ret(x + 3 * e, y, 4 * e, 4 * e, FUNDO2)
    tela.ret(x + 3 * e, y - e, 4 * e, e, ACO2)
    n = int(round(14 * e * max(0.0, min(1.0, frac))))
    if n > 0:
        dither(tela, x, y + 18 * e - n, 10 * e, n, cor, FUNDO3)
        d = 1 if (frac < 1 and math.sin(t * 5) > 0) else 0
        tela.ret(x, y + 18 * e - n - d, 10 * e, 1, MISTURA2)
    tela.ret(x + e, y + 5 * e, e, 11 * e, ACO3)
    tela.ret(x + 10 * e - 1, y + 4 * e, 1, 14 * e, ACO1)
