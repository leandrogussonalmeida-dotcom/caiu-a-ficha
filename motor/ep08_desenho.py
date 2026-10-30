#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep08 — o desenho: o jogo de plataforma inventado (tiles,
sprites, camadas), a física do herói, o cronômetro do quadro, o mini
renderizador 3D (vértices, arame, triângulos com luz e textura, z-buffer) e
o controle genérico.

A paleta do episódio é a `oficina` + 35 cores do jogo (céu, grama, terra,
morros, herói, moeda, pedra). Ela é registrada como 'ep08' e o `longo`
passa a usá-la neste processo.

O jogo é desenhado de verdade num framebuffer próprio de 140 x 78 pixels
(uma `Tela` pequena), camada por camada, do fundo para a frente; a cena
amplia esse framebuffer 2x no palco. A física roda a 60 quadros por segundo
num laço de verdade (ler -> atualizar), então os pontos do pulo que o vídeo
mostra são as posições que o jogo calculou.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, painel, BAYER8, FUNDO, FUNDO2, FUNDO3, TRACO, ACO0,
                   ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO, CHAMA0,
                   CHAMA1, ROXO, ROSA)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#16204a', '#24397a', '#3f63b0', '#6f9ad8', '#a9cdf2',      # 32..36 céu
          '#174a26', '#2e8a3a', '#62c94a', '#b4f06a',                 # 37..40 grama
          '#2e1a10', '#5c3420', '#8f5530', '#c4844e',                 # 41..44 terra
          '#1e2c5c', '#2f4785', '#28603f', '#3d8a52',                 # 45..48 montanha longe / morro perto
          '#f5c09a', '#c98a64',                                       # 49..50 pele
          '#0e4f57', '#18888a', '#3fd0b4',                            # 51..53 roupa (verde-água)
          '#9a5a10', '#e8a520', '#ffe066',                            # 54..56 moeda
          '#c9d8f0', '#f4f8ff',                                       # 57..58 nuvem
          '#3c3a4a', '#6b6880', '#a09cb8',                            # 59..61 pedra
          '#3a2550', '#64408a',                                       # 62..63 calça (roxa)
          '#a6f2dc', '#ffe2cc', '#9a74c8']                            # 64..66 luz forte (3D)
PX.PALETAS['ep08'] = _BASE + _EXTRA
LG.PAL = 'ep08'
(CEU0, CEU1, CEU2, CEU3, CEU4, GRAMA0, GRAMA1, GRAMA2, GRAMA3, TERRA0, TERRA1, TERRA2, TERRA3,
 MORRO0, MORRO1, MORRO2, MORRO3, PELE, PELE2, ROUPA0, ROUPA1, ROUPA2, OURO0, OURO1, OURO2,
 NUVEM0, NUVEM1, PEDRA0, PEDRA1, PEDRA2, CALCA0, CALCA1, ROUPA3, PELE3, CALCA2) = range(32, 67)
RGB = PX.paleta_rgb('ep08').astype(int)
NCOR = len(RGB)
TRANSP = 255                       # "sem pixel" numa camada (o fundo aparece)


def _perto(alvo, proibidas=()):
    d = ((RGB - np.array(alvo)) ** 2).sum(1)
    for p in proibidas: d[p] = 10 ** 9
    return int(np.argmin(d))


# versões mais escura e mais clara de cada cor (sombra e luz do 3D)
SOMBRA = np.array([_perto(RGB[i] * .55) for i in range(NCOR)] + [0] * (256 - NCOR), np.uint8)
CLARO = np.array([_perto(np.minimum(255, RGB[i] * 1.25 + 30)) for i in range(NCOR)] + [0] * (256 - NCOR), np.uint8)
SOMBRA[TRANSP] = TRANSP; CLARO[TRANSP] = TRANSP
# cinzas da profundidade: 0 = perto (claro) .. 7 = longe (escuro)
CINZA = [BRANCO, ACO4, ACO3, ACO2, ACO1, ACO0, FUNDO3, FUNDO2]


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def milhar(n): return f"{int(round(n)):,}".replace(',', '.')


# ------------------------------------------------------------------ textos
def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9):
    """Texto com fio até a peça (o fio sai do lado do texto mais perto da peça)."""
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    tela.linha(ex, hy, ax, ay, cor)
    tela.disco(ax, ay, 1.5, cor)
    tela.ret(ex - 1, hy - 1, 3, 3, cor)


def centro_preso(tela, txt, cx, y, cor, tam=9, xmin=2, xmax=296):
    w = tela.largura_texto(txt, tam)
    x = int(min(max(cx - w / 2, xmin), xmax - w))
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def moldura(tela, x, y, w, h, cor=ACO1):
    """Borda escura + filete claro: a moldura das telas do jogo."""
    tela.ret(x - 2, y - 2, w + 4, h + 4, PRETO)
    tela.ret_vazado(x - 1, y - 1, w + 2, h + 2, cor)


# ------------------------------------------------------------------ sprites
def _sprite(linhas, cores):
    h, w = len(linhas), max(len(l) for l in linhas)
    a = np.full((h, w), TRANSP, np.uint8)
    for y, l in enumerate(linhas):
        for x, ch in enumerate(l):
            if ch != '.': a[y, x] = cores[ch]
    return a


_CH = dict(c=LARANJA, C=CHAMA1, k=PRETO, r=ROUPA1, R=ROUPA2, d=ROUPA0, s=PELE, S=PELE2, w=BRANCO, b=CALCA1, B=CALCA0, e=PRETO,
           o=OURO1, O=OURO2, q=OURO0)
_CABECA = ["..kkkkk..",
           ".kCCccck.",
           ".kcccccck",
           "kkkkkkkkkk",
           ".ksssswek",
           ".kSsssssk",
           "..kSsssk."]
HEROI = {
    'parado': _sprite(_CABECA + ["..kdrRdk.", ".ksrrrrsk", "..kbbbbk.", "..kbkkbk.", "..kk..kk."], _CH),
    'passo1': _sprite(_CABECA + ["..kdrRdk.", ".ksrrrrks", "..kbbbbk.", ".kbk..kbk", ".kk....kk"], _CH),
    'passo2': _sprite(_CABECA + ["..kdrRdk.", "..ksrrsk.", "..kbbbbk.", "...kbbk..", "...kkkk.."], _CH),
    'pulo': _sprite(["ks.kkkkk..", "kk.kCCccck", ".k.kcccccck", ".kkkkkkkkkk", "..ksssswek", "..kSsssssk",
                     "...kSsssk.", "..kdrRdk..", "..krrrrk..", "..kbbbbk..", ".kbk.kbk..", ".kk...kk.."], _CH),
}
HEROI_W, HEROI_H = 6, 12           # caixa de colisão (hitbox)
MOEDA = [_sprite(["..qq..", ".qOOq.", "qOooOq", "qOooOq", "qOooOq", "qOooOq", ".qooq.", "..qq.."], _CH),
         _sprite([".qq.", "qOOq", "qooq", "qooq", "qooq", "qooq", "qooq", ".qq."], _CH),
         _sprite(["q", "O", "o", "o", "o", "o", "o", "q"], _CH),
         _sprite([".qq.", "qOOq", "qooq", "qooq", "qooq", "qooq", "qooq", ".qq."], _CH)]


def carimbo(tela, spr, x, y, esp=False):
    """Copia um sprite para a tela, sem os pixels transparentes. `esp`
    espelha (herói olhando para a esquerda)."""
    if esp: spr = spr[:, ::-1]
    h, w = spr.shape
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(tela.w, x + w), min(tela.h, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    sub = tela.buf[y0:y1, x0:x1]
    m = s != TRANSP
    sub[m] = s[m]


# ------------------------------------------------------------------ tiles
TILE = 8


def _tile_grama():
    yy, xx = np.mgrid[0:8, 0:8]
    a = np.full((8, 8), TERRA1, np.uint8)
    a[(xx + 2 * yy) % 5 == 0] = TERRA2
    a[(3 * xx + yy) % 7 == 3] = TERRA0
    a[0] = GRAMA2; a[1] = GRAMA1; a[2] = GRAMA1
    a[0, ::3] = GRAMA3
    a[3] = np.where(xx[3] % 3 == 0, GRAMA1, GRAMA0)
    a[4, 1::4] = GRAMA0
    return a


def _tile_terra():
    yy, xx = np.mgrid[0:8, 0:8]
    a = np.full((8, 8), TERRA1, np.uint8)
    a[(xx + 2 * yy) % 5 == 0] = TERRA2
    a[(3 * xx + yy) % 7 == 3] = TERRA0
    a[2, 5] = TERRA3; a[6, 1] = TERRA3
    return a


def _tile_pedra():
    a = np.full((8, 8), PEDRA1, np.uint8)
    a[0, :] = PEDRA2; a[:, 0] = PEDRA2
    a[7, :] = PEDRA0; a[:, 7] = PEDRA0
    a[0, 7] = PEDRA1; a[7, 0] = PEDRA1
    a[3, 3] = PEDRA2; a[4, 4] = PEDRA0; a[2, 5] = PEDRA0
    return a


def _tile_ceu():
    return np.full((8, 8), TRANSP, np.uint8)


TILES = [_tile_ceu(), _tile_grama(), _tile_terra(), _tile_pedra()]
NOME_TILE = ['VAZIO', 'GRAMA', 'TERRA', 'PEDRA']

MW, MH = 64, 10                    # mapa da fase em tiles (repete na horizontal)
MAPA = np.zeros((MH, MW), np.uint8)
MAPA[8, :] = 1; MAPA[9, :] = 2
for c in (12, 13, 30, 31, 50, 51):
    MAPA[8, c] = 0; MAPA[9, c] = 0
for c0, c1 in ((19, 23), (38, 42), (57, 60)):
    MAPA[5, c0:c1] = 3
CHAO_Y = 64                        # topo da grama, em pixels do jogo
LARG_FASE = MW * TILE
# moedas (centro, em pixels do jogo): acima das plataformas e sobre os buracos
MOEDAS = [(21 * 8, 26), (40 * 8, 26), (58 * 8 + 4, 26), (13 * 8, 40), (31 * 8, 40), (51 * 8, 40), (6 * 8, 52),
          (45 * 8, 52)]


def solido(xw, yw):
    """Tile sólido no ponto (pixels do jogo, mundo que repete)?"""
    c = int(math.floor(xw / TILE)) % MW
    r = int(math.floor(yw / TILE))
    if r < 0 or r >= MH: return 0
    return MAPA[r, c]


# ------------------------------------------------------------------ o laço do jogo (física)
GRAV = 0.18                        # pixels por quadro, a cada quadro
PULO = -3.2                        # velocidade do pulo (para cima é negativo)
VX = 0.75                          # anda 0,75 pixel por quadro (45 por segundo)


class Simulacao:
    """O laço do jogo a 60 quadros por segundo: ler o controle (a IA aperta
    os botões), atualizar (gravidade, colisão com o chão e as moedas).
    Guarda o estado de cada quadro."""

    def __init__(self, n=60 * 520):
        x, y, vy, chao = 20.0, float(CHAO_Y), 0.0, True
        self.x = np.zeros(n); self.y = np.zeros(n); self.vy = np.zeros(n)
        self.chao = np.zeros(n, bool); self.pulo = np.zeros(n, bool)
        self.moedas_de = {}                     # (volta, i) -> quadro em que pegou
        self.placar = np.zeros(n, int)
        pontos = 0
        for f in range(n):
            # 1 ler o controle (aqui, a "mão" é uma regra simples)
            aperta = False
            if chao:
                frente = x + HEROI_W + 7
                if solido(frente, CHAO_Y + 2) == 0 and solido(x + 3, y + 1) != 0: aperta = True
                xr = x % LARG_FASE
                for c0, c1 in ((19, 23), (38, 42), (57, 60)):
                    if 14 <= c0 * 8 - xr <= 16 and y >= CHAO_Y - .5: aperta = True
            # 2 atualizar
            if aperta: vy = PULO; chao = False
            vy += GRAV
            ny = y + vy
            x += VX
            chao = False
            if vy >= 0:
                for pe in (x + 1, x + HEROI_W - 1):
                    t_ = math.floor(ny / TILE) * TILE
                    if solido(pe, ny) and y <= t_ + .01:
                        ny, vy, chao = t_, 0.0, True
                        break
            y = ny
            # moedas: caixa do herói encosta na caixa da moeda?
            volta = int(x // LARG_FASE)
            for v in (volta, volta + 1):
                for i, (mx, my) in enumerate(MOEDAS):
                    if (v, i) in self.moedas_de: continue
                    cx = mx + v * LARG_FASE
                    if x < cx + 3 and x + HEROI_W > cx - 3 and y - HEROI_H < my + 4 and y > my - 4:
                        self.moedas_de[(v, i)] = f
                        pontos += 1
            self.x[f], self.y[f], self.vy[f], self.chao[f], self.pulo[f] = x, y, vy, chao, aperta
            self.placar[f] = pontos
        self.n = n

    def quadro_de_pulo(self, depois=0):
        """Primeiro quadro, depois de `depois`, em que o botão de pulo foi lido."""
        idx = np.nonzero(self.pulo[depois:])[0]
        return int(idx[0]) + depois


SIM = Simulacao()


# ------------------------------------------------------------------ o jogo (camadas)
GW, GH = 140, 78
CAMADAS = ['ceu', 'nuvens', 'montanhas', 'morros', 'tiles', 'sprites', 'placar']
NOME_CAMADA = dict(ceu='CÉU', nuvens='NUVENS', montanhas='MONTANHAS', morros='MORROS', tiles='TILES',
                   sprites='SPRITES', placar='PLACAR')
PARALAXE = dict(nuvens=.12, montanhas=.25, morros=.5, tiles=1.0)


def camera_de(f):
    return SIM.x[int(f)] - 44


def _ceu(g):
    faixas = ((0, 14, CEU1, CEU1), (14, 26, CEU1, CEU2), (26, 40, CEU2, CEU2), (40, 52, CEU2, CEU3),
              (52, 62, CEU3, CEU3), (62, 78, CEU3, CEU4))
    for y0, y1, c1, c2 in faixas:
        dither(g, 0, y0, GW, y1 - y0, c1, c2)
    g.disco(118, 14, 6, OURO2); g.disco(118, 14, 4, NUVEM1)


def _nuvens(g, cam):
    ox = -int(cam * PARALAXE['nuvens']) % 160
    for k, (x, y, s) in enumerate(((10, 12, 1.0), (70, 22, .8), (125, 8, .7))):
        for rep in (-160, 0, 160):
            cx = x + ox + rep
            if cx < -30 or cx > GW + 30: continue
            for dx, dy, r in ((0, 0, 5), (6, -2, 6), (12, 0, 5), (6, 2, 5)):
                g.disco(cx + dx * s, y + dy * s, r * s, NUVEM1)
            g.ret(cx - 4 * s, y + 3 * s, 20 * s, 2, NUVEM0)


def _montanhas(g, cam):
    ox = cam * PARALAXE['montanhas']
    pts = [(-1, GH)]
    for x in range(-2, GW + 4, 2):
        xw = x + ox
        y = 34 + 9 * math.sin(xw * .045) + 5 * math.sin(xw * .11 + 1)
        pts.append((x, y))
    pts.append((GW + 4, GH))
    poligono(g, pts, MORRO1)
    for x in range(0, GW):
        xw = x + ox
        y = 34 + 9 * math.sin(xw * .045) + 5 * math.sin(xw * .11 + 1)
        if math.cos(xw * .045) < -.2: dither(g, x, int(y) + 1, 1, GH, MORRO1, MORRO0)
        g.px(x, int(y) + 1, MORRO0 if math.cos(xw * .045) < 0 else CEU3)


def _morros(g, cam):
    ox = cam * PARALAXE['morros']
    for x in range(GW):
        xw = x + ox
        y = 52 + 5 * math.sin(xw * .07) + 3 * math.sin(xw * .023 + 2)
        g.ret(x, int(y), 1, GH, MORRO3)
        if math.cos(xw * .07) < 0: dither(g, x, int(y) + 2, 1, GH, MORRO3, MORRO2)
        g.px(x, int(y), GRAMA2 if math.cos(xw * .07) > 0 else MORRO3)
    for k in range(-1, 6):                        # arbustos nos morros
        xb = k * 31 - (ox % 31)
        g.disco(xb, 58 + 2 * math.sin(k), 3, MORRO2)


def _tiles(g, cam, n_tiles=None, grade=False):
    """Desenha o mapa de tiles visível. `n_tiles` limita quantos tiles (em
    ordem de leitura) já foram copiados, para a cena da montagem."""
    c0 = int(math.floor(cam / TILE))
    off = int(math.floor(cam)) - c0 * TILE
    k = 0
    for r in range(MH):
        for j in range(GW // TILE + 2):
            c = (c0 + j) % MW
            tid = MAPA[r, c]
            if tid == 0: continue
            if n_tiles is not None and k >= n_tiles: return
            k += 1
            carimbo(g, TILES[tid], j * TILE - off, r * TILE)


def _sprites(g, f, cam, so=None):
    f = int(f)
    camx = int(math.floor(cam))
    volta = int(SIM.x[f] // LARG_FASE)
    if so in (None, 'moeda'):
        for v in (volta - 1, volta, volta + 1):
            for i, (mx, my) in enumerate(MOEDAS):
                pego = SIM.moedas_de.get((v, i))
                if pego is not None and pego <= f: continue
                x = mx + v * LARG_FASE - camx
                if -8 < x < GW + 8:
                    spr = MOEDA[(f // 6 + i) % 4]
                    carimbo(g, spr, x - spr.shape[1] // 2, my - 4)
    if so in (None, 'heroi'):
        spr = heroi_sprite(f)
        x = int(math.floor(SIM.x[f])) - camx
        carimbo(g, spr, x - 1, int(round(SIM.y[f])) - spr.shape[0])


def heroi_sprite(f):
    f = int(f)
    if not SIM.chao[f]: return HEROI['pulo']
    return HEROI[('passo1', 'parado', 'passo2', 'parado')[(f // 6) % 4]]


def _placar(g, f):
    f = int(f)
    carimbo(g, MOEDA[0], 4, 4)
    g.texto(f"X {SIM.placar[f]:02d}", 13, 5, BRANCO, tam=9, contorno=PRETO)
    g.texto(f"PONTOS {SIM.placar[f] * 100:05d}", GW - 4, 5, BRANCO, tam=9, contorno=PRETO, centro='d')


def desenhar_jogo(g, f, camadas=None, cam=None, n_tiles=None, fundo=True):
    """Pinta o quadro `f` do jogo na tela pequena `g`, camada por camada, do
    fundo para a frente (o algoritmo do pintor)."""
    cam = camera_de(f) if cam is None else cam
    cs = CAMADAS if camadas is None else camadas
    if fundo: g.buf[:] = TRANSP if 'ceu' not in cs else CEU2
    for c in cs:
        if c == 'ceu': _ceu(g)
        elif c == 'nuvens': _nuvens(g, cam)
        elif c == 'montanhas': _montanhas(g, cam)
        elif c == 'morros': _morros(g, cam)
        elif c == 'tiles': _tiles(g, cam, n_tiles)
        elif c == 'sprites': _sprites(g, f, cam)
        elif c == 'heroi': _sprites(g, f, cam, so='heroi')
        elif c == 'moeda': _sprites(g, f, cam, so='moeda')
        elif c == 'placar': _placar(g, f)


class Jogo:
    """Framebuffer do jogo (140 x 78) com cache dos quadros já pintados."""

    def __init__(self):
        self.g = PX.Tela(GW, GH, paleta='ep08')
        self._cache = {}

    def quadro(self, f, camadas=None, **kw):
        ch = (int(f), tuple(camadas) if camadas else None, tuple(sorted(kw.items())))
        b = self._cache.get(ch)
        if b is None:
            desenhar_jogo(self.g, f, camadas, **kw)
            b = self.g.buf.copy()
            if len(self._cache) > 120: self._cache.clear()
            self._cache[ch] = b
        return b


def colar(tela, buf, x, y, esc=2, clip=None, transp=True):
    """Amplia o framebuffer do jogo `esc` vezes e cola no palco."""
    a = np.repeat(np.repeat(buf, esc, 0), esc, 1) if esc != 1 else buf
    h, w = a.shape
    x, y = int(x), int(y)
    cx0, cy0, cx1, cy1 = clip if clip else (0, 0, tela.w, PALCO_H)
    x0, y0, x1, y1 = max(cx0, x), max(cy0, y), min(cx1, x + w), min(cy1, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = a[y0 - y:y1 - y, x0 - x:x1 - x]
    sub = tela.buf[y0:y1, x0:x1]
    if transp:
        m = s != TRANSP
        sub[m] = s[m]
    else:
        sub[:] = np.where(s == TRANSP, FUNDO, s)


# ------------------------------------------------------------------ o cronômetro do quadro
ORCAMENTO = 1000 / 60.0            # 16,7 ms
ETAPAS = [('LER O CONTROLE', 0.0, 0.5, CIANO), ('ATUALIZAR', 0.5, 3.0, VERDE),
          ('DESENHAR', 3.0, 12.0, AMARELO), ('MOSTRAR', 12.0, ORCAMENTO, ROSA)]


def etapa_de(ms):
    for k, (_, a, b, _) in enumerate(ETAPAS):
        if ms < b: return k
    return len(ETAPAS) - 1


def cronometro(tela, x, y, ms, quadro, w=160, lista=True, titulo=None, t=0.0):
    """O protagonista: quanto do orçamento de 16,7 ms do quadro já passou.
    Os tempos de cada etapa são de exemplo (cada jogo é diferente)."""
    ms = max(0.0, min(ORCAMENTO, ms))
    tela.texto(titulo or f"QUADRO Nº {milhar(quadro)}", x, y, ACO3, tam=9, contorno=PRETO)
    k = etapa_de(ms)
    tela.texto(f"{dec(ms)} MS", x, y + 11, ETAPAS[k][3], tam=17, contorno=PRETO)
    tela.texto("DE 16,7 MS", x + 84, y + 18, ACO3, tam=9, contorno=PRETO)
    by = y + 32
    painel(tela, x - 1, by - 1, w + 2, 10)
    for nome, a, b, cor in ETAPAS:
        xa, xb = x + a / ORCAMENTO * w, x + min(ms, b) / ORCAMENTO * w
        if ms > a:
            tela.ret(xa, by + 1, xb - xa, 6, cor)
            tela.ret(xa, by + 1, xb - xa, 1, BRANCO if cor != ROSA else ROSA)
        tela.ret(x + a / ORCAMENTO * w, by - 2, 1, 2, ACO2)
    xc = x + ms / ORCAMENTO * w
    if int(t * 6) % 2 == 0 or ms >= ORCAMENTO - .01:
        tela.ret(xc - 1, by - 3, 2, 14, BRANCO)
    tela.ret(x + w - 1, by - 3, 1, 14, VERMELHO)
    tela.texto("TEMPOS DE EXEMPLO", x, by + 12, ACO1, tam=9, contorno=PRETO)
    if lista:
        for j, (nome, a, b, cor) in enumerate(ETAPAS):
            yy = by + 26 + j * 12
            feito = ms >= b - 1e-6
            atual = j == k and not feito
            tela.ret(x, yy + 1, 7, 7, cor if (atual or feito) else FUNDO2)
            if feito: tela.ret(x + 2, yy + 3, 3, 3, PRETO)
            tela.texto(f"{j + 1} {nome}", x + 11, yy, BRANCO if atual else (ACO3 if feito else ACO1), tam=9,
                       contorno=PRETO)
        return by + 26 + len(ETAPAS) * 12
    return by + 22


# ------------------------------------------------------------------ o controle
def controle(tela, cx, cy, aperto, t, esc=1.0):
    """Controle genérico (sem marca): cruz à esquerda, dois botões à direita.
    `aperto` = conjunto dos botões apertados: 'dir', 'esq', 'cima', 'baixo',
    'pulo', 'acao'. Devolve a posição de cada botão."""
    e = esc
    # corpo: barra arredondada + duas alças
    for dx in (-44, 44):
        tela.disco(cx + dx * e, cy + 10 * e, 24 * e, PRETO)
    tela.ret(cx - 46 * e, cy - 22 * e, 92 * e, 46 * e, PRETO)
    tela.disco(cx - 46 * e, cy + 1 * e, 23 * e, PRETO); tela.disco(cx + 46 * e, cy + 1 * e, 23 * e, PRETO)
    for dx in (-44, 44):
        tela.disco(cx + dx * e, cy + 10 * e, 22 * e, ACO1)
        dither(tela, cx + dx * e - 12 * e, cy + 22 * e, 24 * e, 8 * e, ACO1, ACO0)
    tela.ret(cx - 46 * e, cy - 20 * e, 92 * e, 42 * e, ACO1)
    tela.disco(cx - 46 * e, cy + 1 * e, 21 * e, ACO1); tela.disco(cx + 46 * e, cy + 1 * e, 21 * e, ACO1)
    tela.ret(cx - 40 * e, cy - 20 * e, 80 * e, 2, ACO3)                      # luz no topo
    dither(tela, cx - 46 * e, cy + 12 * e, 92 * e, 10 * e, ACO1, ACO0)        # sombra embaixo
    # cruz
    px_, py_ = cx - 44 * e, cy
    b = 7 * e
    tela.ret(px_ - 3 * b / 2 - 1, py_ - b / 2 - 1, 3 * b + 2, b + 2, PRETO)
    tela.ret(px_ - b / 2 - 1, py_ - 3 * b / 2 - 1, b + 2, 3 * b + 2, PRETO)
    pos = {}
    for nome, dx, dy in (('esq', -1, 0), ('dir', 1, 0), ('cima', 0, -1), ('baixo', 0, 1)):
        x, y = px_ + dx * b - b / 2, py_ + dy * b - b / 2
        ap = nome in aperto
        tela.ret(x, y, b, b, ACO3 if ap else FUNDO3)
        tela.ret(x, y, b, 1, ACO4 if ap else ACO1)
        if ap: tela.ret(x + 1, y + 1, b - 2, b - 2, AMARELO)
        pos[nome] = (x + b / 2, y + b / 2)
    tela.ret(px_ - b / 2, py_ - b / 2, b, b, FUNDO3)
    # botões
    for nome, dx, dy, cor in (('pulo', 52, 4, VERDE), ('acao', 38, -8, VERMELHO)):
        x, y = cx + dx * e, cy + dy * e
        ap = nome in aperto
        tela.disco(x, y + 1, 6.5 * e, PRETO)
        tela.disco(x, y + (1 if ap else 0), 5.5 * e, cor)
        if ap:
            tela.disco(x, y + 1, 4 * e, AMARELO)
        else:
            tela.disco(x - 1.5 * e, y - 1.5 * e, 1.6 * e, BRANCO)
        pos[nome] = (x, y)
    # luz de ligado
    tela.ret(cx - 3, cy - 14 * e, 6, 3, VERDE if int(t * 2) % 2 else FUNDO3)
    return pos


# ------------------------------------------------------------------ 3D
def _caixa(x0, x1, y0, y1, z0, z1):
    """8 vértices e 6 faces (quadras na ordem anti-horária vista de fora)."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = dict(frente=(4, 5, 6, 7), tras=(1, 0, 3, 2), dir=(5, 1, 2, 6), esq=(0, 4, 7, 3), cima=(7, 6, 2, 3),
             baixo=(0, 1, 5, 4))
    return v, f


def _tex(linhas, cores):
    return _sprite(linhas, cores)


_TC = dict(c=LARANJA, C=CHAMA1, k=PRETO, r=ROUPA1, R=ROUPA2, d=ROUPA0, s=PELE, S=PELE2, w=BRANCO, b=CALCA1, B=CALCA0, o=OURO1,
           g=GRAMA1, G=GRAMA2, h=GRAMA0)
TEX = dict(
    rosto=_tex(["ssssssss", "ssssssss", "skwssskw", "skwssskw", "ssssssss", "sssSSsss", "ssskksss", "ssssssss"], _TC),
    camisa=_tex(["rrrrrrrr", "rRrrrrRr", "rrrwwrrr", "rrwrrwrr", "rrwrrwrr", "rrrwwrrr", "dddddddd", "kokkkkok"], _TC),
    pele=_tex(["s" * 8] * 8, _TC),
    calca=_tex(["bbbbbbbb", "bbbbbbbb", "bBbbbbBb", "bbbbbbbb", "bbbbbbbb", "bBbbbbBb", "bbbbbbbb", "BBBBBBBB"], _TC),
    bone=_tex(["cccccccc", "cCCCCCCc", "cccccccc", "cccccccc", "cccccccc", "cccccccc", "cccccccc", "cccccccc"], _TC),
    grama=_tex(["gggGgggg", "ghgggggG", "gggghggg", "Gggggggh", "ggGggggg", "gghgggGg", "gggggggg", "hgggGggg"], _TC),
)
COR_BASE = dict(rosto=PELE, camisa=ROUPA1, pele=PELE, calca=CALCA1, bone=LARANJA, grama=GRAMA1)


def modelo_heroi():
    """O herói em 3D: caixas (pernas, corpo, braços, cabeça, boné, aba).
    Devolve vértices (n, 3) e triângulos [(i, j, k, uvs, textura)]."""
    partes = [((-3, -.5, 0, 4.5, -1.6, 1.6), 'calca', {}), ((.5, 3, 0, 4.5, -1.6, 1.6), 'calca', {}),
              ((-3.5, 3.5, 4.5, 10.5, -2, 2), 'pele', {'frente': 'camisa', 'tras': 'camisa', 'dir': 'camisa',
                                                      'esq': 'camisa', 'cima': 'camisa'}),
              ((-5.2, -3.5, 5.5, 10, -1.2, 1.2), 'pele', {}), ((3.5, 5.2, 5.5, 10, -1.2, 1.2), 'pele', {}),
              ((-3.2, 3.2, 10.5, 16.5, -3, 3), 'pele', {'frente': 'rosto'}),
              ((-3.5, 3.5, 16, 18, -3.4, 3.4), 'bone', {}), ((-3.2, 3.2, 16, 16.8, 3.4, 7), 'bone', {})]
    V, T = [], []
    uvq = [(0, 1), (1, 1), (1, 0), (0, 0)]
    for (x0, x1, y0, y1, z0, z1), tex, esp in partes:
        v, faces = _caixa(x0, x1, y0, y1, z0, z1)
        b = len(V)
        V += v
        for nome, (a, bb, c, d) in faces.items():
            tx = esp.get(nome, tex)
            q = (b + a, b + bb, b + c, b + d)
            T.append((q[0], q[1], q[2], (uvq[0], uvq[1], uvq[2]), tx))
            T.append((q[0], q[2], q[3], (uvq[0], uvq[2], uvq[3]), tx))
    return np.array(V, float), T


def modelo_chao(n=4, lado=6.0):
    V, T = [], []
    for i in range(n + 1):
        for j in range(n + 1):
            V.append(((i - n / 2) * lado, 0.0, (j - n / 2) * lado))
    for i in range(n):
        for j in range(n):
            a, b, c, d = i * (n + 1) + j, (i + 1) * (n + 1) + j, (i + 1) * (n + 1) + j + 1, i * (n + 1) + j + 1
            T.append((a, d, c, ((0, 0), (0, 1), (1, 1)), 'grama'))
            T.append((a, c, b, ((0, 0), (1, 1), (1, 0)), 'grama'))
    return np.array(V, float), T


HV, HT = modelo_heroi()
CV, CT = modelo_chao()
LUZ = np.array([-.55, .75, .65]); LUZ = LUZ / np.linalg.norm(LUZ)


def projetar(V, yaw, pitch=.32, dist=46.0, foco=230.0, cx=150.0, cy=110.0, alvo_y=8.0):
    """Vértice 3D -> ponto na tela: gira (modelo), põe na frente da câmera
    (vista) e divide pela distância (projeção)."""
    c, s = math.cos(yaw), math.sin(yaw)
    x = V[:, 0] * c + V[:, 2] * s
    z = -V[:, 0] * s + V[:, 2] * c
    y = V[:, 1] - alvo_y
    cp, sp = math.cos(pitch), math.sin(pitch)
    y2 = y * cp - z * sp
    z2 = y * sp + z * cp
    zc = dist - z2
    sx = cx + foco * x / zc
    sy = cy - foco * y2 / zc
    return np.stack([sx, sy, zc], 1)


def _normal_mundo(V, i, j, k, yaw):
    a, b, c = V[i], V[j], V[k]
    n = np.cross(b - a, c - a)
    n = n / (np.linalg.norm(n) + 1e-9)
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    return np.array([n[0] * cy_ + n[2] * sy_, n[1], -n[0] * sy_ + n[2] * cy_])


def luz_de(V, tri, yaw, luz=LUZ):
    n = _normal_mundo(V, tri[0], tri[1], tri[2], yaw)
    return max(0.0, float(n @ luz))


class Raster3D:
    """Rasterizador de verdade, em miniatura: para cada triângulo, testa o
    centro de cada pixel da caixa dele, interpola profundidade e textura e
    só pinta se estiver mais perto que o que já está no z-buffer."""

    def __init__(self, area):
        self.area = area                         # (x0, y0, x1, y1) no palco
        x0, y0, x1, y1 = area
        self.w, self.h = x1 - x0, y1 - y0
        self.zb = np.full((self.h, self.w), np.inf)
        self.cb = np.full((self.h, self.w), TRANSP, np.uint8)

    def limpar(self):
        self.zb[:] = np.inf; self.cb[:] = TRANSP

    def triangulo(self, P, uvs, tex, luz, modo='textura', limite=None, cor_fixa=None):
        x0a, y0a = self.area[0], self.area[1]
        p = np.array(P, float); p[:, 0] -= x0a; p[:, 1] -= y0a
        ar = (p[1, 0] - p[0, 0]) * (p[2, 1] - p[0, 1]) - (p[1, 1] - p[0, 1]) * (p[2, 0] - p[0, 0])
        if ar >= -1e-6: return 0                # de costas (ou de lado): não desenha
        bx0, bx1 = max(0, int(math.floor(p[:, 0].min()))), min(self.w - 1, int(math.ceil(p[:, 0].max())))
        by0, by1 = max(0, int(math.floor(p[:, 1].min()))), min(self.h - 1, int(math.ceil(p[:, 1].max())))
        if bx1 < bx0 or by1 < by0: return 0
        yy, xx = np.mgrid[by0:by1 + 1, bx0:bx1 + 1]
        X, Y = xx + .5, yy + .5

        def e(a, b): return (p[b, 0] - p[a, 0]) * (Y - p[a, 1]) - (p[b, 1] - p[a, 1]) * (X - p[a, 0])
        w0, w1 = e(1, 2) / ar, e(2, 0) / ar
        w2 = 1 - w0 - w1
        dentro = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        z = w0 * p[0, 2] + w1 * p[1, 2] + w2 * p[2, 2]
        zsub = self.zb[by0:by1 + 1, bx0:bx1 + 1]
        m = dentro & (z < zsub)
        if limite is not None:
            m &= (yy * self.w + xx) < limite
        if not m.any(): return int(dentro.sum())
        if cor_fixa is not None:
            cor = np.full(m.shape, cor_fixa, np.uint8)
        else:
            if modo == 'textura':
                u = w0 * uvs[0][0] + w1 * uvs[1][0] + w2 * uvs[2][0]
                v = w0 * uvs[0][1] + w1 * uvs[1][1] + w2 * uvs[2][1]
                T = TEX[tex]
                th, tw = T.shape
                cor = T[np.clip((v * th).astype(int), 0, th - 1), np.clip((u * tw).astype(int), 0, tw - 1)]
            else:
                cor = np.full(m.shape, COR_BASE[tex], np.uint8)
            # luz: 0 = de lado/costas para a luz, 1 = de frente. Pontilhado
            # Bayer entre sombra forte, sombra, cor e luz forte.
            nivel = .35 + luz * 2.5 + (BAYER8[(yy + y0a) % 8, (xx + x0a) % 8] - .5) * .9
            cor = np.where(nivel < .9, SOMBRA[SOMBRA[cor]], np.where(nivel < 1.8, SOMBRA[cor],
                           np.where(nivel < 2.75, cor, CLARO[cor])))
        self.cb[by0:by1 + 1, bx0:bx1 + 1][m] = cor[m]
        zsub[m] = z[m]
        return int(dentro.sum())

    def colar(self, tela):
        x0, y0, x1, y1 = self.area
        sub = tela.buf[y0:y1, x0:x1]
        m = self.cb != TRANSP
        sub[m] = self.cb[m]


def cena3d(R, yaw, modo='textura', chao=True, luz=LUZ, ate=None, cx=150, cy=110, foco=230.0, dist=46.0):
    """Pinta o herói 3D (e o chão) no rasterizador R. `ate` = quantos
    triângulos do herói já foram pintados (montagem). Devolve os pontos
    projetados do herói."""
    R.limpar()
    kw = dict(cx=cx - R.area[0] + R.area[0], cy=cy, foco=foco, dist=dist)
    if chao:
        P = projetar(CV, yaw, **kw)
        for i, j, k, uv, tx in CT:
            R.triangulo(P[[i, j, k]], uv, tx, luz_de(CV, (i, j, k), yaw, luz), modo)
    P = projetar(HV, yaw, **kw)
    for n, (i, j, k, uv, tx) in enumerate(HT):
        if ate is not None and n >= ate: break
        R.triangulo(P[[i, j, k]], uv, tx, luz_de(HV, (i, j, k), yaw, luz), modo)
    return P


def arestas(T):
    """Arestas únicas dos triângulos (para o desenho em arame)."""
    s = set()
    for i, j, k, _, _ in T:
        for a, b in ((i, j), (j, k), (k, i)):
            s.add((min(a, b), max(a, b)))
    return sorted(s)


AR_H = arestas(HT)
AR_C = arestas(CT)


def visivel(P, T, i):
    """O triângulo i está de frente para a câmera?"""
    a, b, c = T[i][0], T[i][1], T[i][2]
    p = P[[a, b, c]]
    ar = (p[1, 0] - p[0, 0]) * (p[2, 1] - p[0, 1]) - (p[1, 1] - p[0, 1]) * (p[2, 0] - p[0, 0])
    return ar < 0


# ------------------------------------------------------------------ grade ampliada (rasterização, z-buffer)
def grade(tela, x0, y0, nx, ny, lado, cor_fundo=FUNDO2, cor_linha=PRETO):
    tela.ret(x0 - 1, y0 - 1, nx * lado + 1, ny * lado + 1, cor_linha)
    for j in range(ny):
        for i in range(nx):
            tela.ret(x0 + i * lado, y0 + j * lado, lado - 1, lado - 1, cor_fundo)


def dentro_tri(px, py, tri):
    (ax, ay), (bx, by), (cx, cy) = tri
    d1 = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    d2 = (cx - bx) * (py - by) - (cy - by) * (px - bx)
    d3 = (ax - cx) * (py - cy) - (ay - cy) * (px - cx)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def baric(px, py, tri):
    (ax, ay), (bx, by), (cx, cy) = tri
    ar = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    w0 = ((bx - px) * (cy - py) - (by - py) * (cx - px)) / ar
    w1 = ((cx - px) * (ay - py) - (cy - py) * (ax - px)) / ar
    return w0, w1, 1 - w0 - w1
