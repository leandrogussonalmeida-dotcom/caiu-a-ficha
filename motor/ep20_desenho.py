#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL ep20 — o desenho: o QR code de verdade, módulo a módulo.

O CÓDIGO NÃO É DESENHADO À MÃO. Este módulo tem um codificador de QR
próprio (versão 2, nível Q, modo byte), em Python puro, sem biblioteca:
monta os bytes da frase, calcula os 22 bytes de Reed–Solomon em GF(256),
desenha os padrões fixos, põe os bits em zigue-zague, testa as 8 máscaras
pelas 4 regras de castigo e escreve os 15 bits de formato. O resultado foi
comparado com a biblioteca `segno` (difere só no último byte de dados e,
por isso, nos bytes de correção; as duas versões leem) e lido por um decodificador (OpenCV) num quadro exportado;
a matriz final também fica guardada abaixo como literal (FINAL_V2_HEX), e
o import confere que a conta bate com ela.

As outras versões (1, 3, 5, 10, 20, 40), usadas só no capítulo das
versões, foram geradas pela `segno` e ficam aqui como literais: o render
não precisa de nenhum pacote novo.

A paleta é a `oficina` + papel, tinta e um par escuro/claro para cada peça
do código (localizador, sincronia, alinhamento, formato, dados, correção),
mais café (a mancha), papelão e madeira. Registrada como 'ep20'; o `longo`
passa a usá-la neste processo.
"""
import math
import numpy as np
import pixelengine as PX
import longo as LG
from longo import (W, H, PALCO_H, dither, poligono, linha_grossa, painel, FUNDO, FUNDO2, FUNDO3, TRACO,
                   ACO0, ACO1, ACO2, ACO3, ACO4, AMARELO, CIANO, BRANCO, LARANJA, VERMELHO, VERDE, PRETO,
                   ROSA, ROXO, LATAO, CHAMA0, CHAMA1, OLEO0, OLEO1)

# ------------------------------------------------------------------ paleta
_BASE = list(PX.PALETAS['oficina'])
_EXTRA = ['#8c8676', '#b7b09c', '#d7d0bb', '#ece6d4',      # 32..35 papel (sombra -> luz)
          '#0d0f17', '#1e2434', '#323a52',                 # 36..38 tinta (módulo escuro)
          '#0f4f6e', '#c4e9f5',                            # 39..40 localizador
          '#1d6a3a', '#cdeed5',                            # 41..42 sincronia
          '#55308a', '#e2d3f3',                            # 43..44 alinhamento
          '#8a3c0e', '#f6d7bc',                            # 45..46 formato
          '#6e5200', '#f4e4a2',                            # 47..48 dados
          '#87204f', '#f3c9dc',                            # 49..50 correção de erro
          '#3a1c0c', '#6a3818', '#94582c',                 # 51..53 café
          '#5a3b1f', '#8a5f34', '#b98a52',                 # 54..56 papelão
          '#2a1a10', '#4a2f1c']                            # 57..58 madeira
PX.PALETAS['ep20'] = _BASE + _EXTRA
LG.PAL = 'ep20'
(PAP0, PAP1, PAP2, PAP3, TIN0, TIN1, TIN2, LOC_E, LOC_C, SIN_E, SIN_C, ALI_E, ALI_C, FMT_E, FMT_C,
 DAD_E, DAD_C, ECC_E, ECC_C, CAF0, CAF1, CAF2, CAR0, CAR1, CAR2, MAD0, MAD1) = range(32, 59)


def dec(x, c=1): return f"{x:.{c}f}".replace('.', ',')
def milhar(n):
    s = f"{abs(int(round(n))):,}".replace(',', '.')
    return ('-' if n < 0 else '') + s
def clamp(u, a=0.0, b=1.0): return max(a, min(b, u))
def lerp(a, b, u): return a + (b - a) * u
def suave(u): u = clamp(u); return u * u * (3 - 2 * u)
def ease(u): u = clamp(u); return 1 - (1 - u) ** 3


# =================================================================== o codificador
TEXTO = "NOSSO MUNDO PIXEL"
N = 25                           # versão 2: 4 x 2 + 17
N_DADOS, N_ECC = 22, 22          # 2-Q: 22 bytes de dados + 22 de correção, 1 bloco (thonky)
RESTO = 7                        # bits de sobra da versão 2
EC_BITS = 0b11                   # nível Q

EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x; LOG[_x] = _i
    _x <<= 1
    if _x & 0x100: _x ^= 0x11D
for _i in range(255, 512): EXP[_i] = EXP[_i - 255]


def gmul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def rs_gerador(n):
    g = [1]
    for i in range(n):
        h = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            h[j] ^= c
            h[j + 1] ^= gmul(c, EXP[i])
        g = h
    return g


def rs_resto(dados, n):
    """Os n bytes de Reed–Solomon: o resto da divisão dos dados pelo gerador."""
    g = rs_gerador(n)
    r = list(dados) + [0] * n
    for i in range(len(dados)):
        c = r[i]
        if c:
            for j in range(1, len(g)): r[i + j] ^= gmul(g[j], c)
    return r[len(dados):]


def bits_dados(texto=TEXTO):
    """[(bit, rótulo)] do fluxo de dados: modo, tamanho, letras, fim, enchimento."""
    b = []
    for k in range(4): b.append(((0b0100 >> (3 - k)) & 1, ('modo', 0)))
    n = len(texto)
    for k in range(8): b.append(((n >> (7 - k)) & 1, ('conta', 0)))
    for i, ch in enumerate(texto.encode('latin-1')):
        for k in range(8): b.append(((ch >> (7 - k)) & 1, ('letra', i)))
    for k in range(4):
        if len(b) < N_DADOS * 8: b.append((0, ('fim', 0)))
    while len(b) % 8: b.append((0, ('fim', 0)))
    j = 0
    while len(b) < N_DADOS * 8:
        v = (0xEC, 0x11)[j % 2]
        for k in range(8): b.append(((v >> (7 - k)) & 1, ('enche', j)))
        j += 1
    return b


LOC, SEP, SIN, ALI, FMT, ESC = 1, 2, 3, 4, 5, 6
ALI_C0 = 18                      # centro do alinhamento na versão 2


def posicoes_formato():
    """As duas cópias dos 15 bits de formato, do bit 0 ao 14, como (x, y)."""
    a = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(14 - i, 8) for i in range(9, 15)]
    b = [(N - 1 - i, 8) for i in range(8)] + [(8, N - 15 + i) for i in range(8, 15)]
    return a, b


def funcoes():
    papel = np.zeros((N, N), np.int16)
    val = np.zeros((N, N), np.int16)
    for ox, oy in ((0, 0), (N - 7, 0), (0, N - 7)):
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                x, y = ox + dx, oy + dy
                if not (0 <= x < N and 0 <= y < N): continue
                if 0 <= dx <= 6 and 0 <= dy <= 6:
                    papel[y, x] = LOC; val[y, x] = 1 if max(abs(dx - 3), abs(dy - 3)) != 2 else 0
                else:
                    papel[y, x] = SEP; val[y, x] = 0
    for i in range(8, N - 8):
        papel[6, i] = SIN; val[6, i] = 1 - i % 2
        papel[i, 6] = SIN; val[i, 6] = 1 - i % 2
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            papel[ALI_C0 + dy, ALI_C0 + dx] = ALI
            val[ALI_C0 + dy, ALI_C0 + dx] = 1 if max(abs(dx), abs(dy)) != 1 else 0
    for cop in posicoes_formato():
        for (x, y) in cop: papel[y, x] = FMT
    papel[N - 8, 8] = ESC; val[N - 8, 8] = 1
    return papel, val


def bits_formato(mascara):
    d = (EC_BITS << 3) | mascara
    r = d
    for _ in range(10): r = (r << 1) ^ ((r >> 9) * 0x537)
    return ((d << 10) | r) ^ 0x5412


def ordem_dados(papel):
    """(x, y) na ordem em que os bits entram: colunas de 2, do canto de baixo à
    direita, subindo e descendo, pulando a coluna da sincronia e as peças fixas."""
    o = []
    right = N - 1
    while right >= 1:
        if right == 6: right = 5
        for vert in range(N):
            for j in range(2):
                x = right - j
                subindo = ((right + 1) & 2) == 0
                y = N - 1 - vert if subindo else vert
                if papel[y, x] == 0: o.append((x, y))
        right -= 2
    return o


MASCARAS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


def castigo(m):
    """As 4 regras: fileira de 5+ iguais, bloco 2x2, padrão de localizador,
    equilíbrio entre claro e escuro. Devolve (total, (r1, r2, r3, r4))."""
    m = [list(map(int, r)) for r in m]
    n = len(m)
    p1 = 0
    for linhas in (m, [list(c) for c in zip(*m)]):
        for row in linhas:
            run, cor = 1, row[0]
            for x in range(1, n):
                if row[x] == cor: run += 1
                else:
                    if run >= 5: p1 += 3 + run - 5
                    run, cor = 1, row[x]
            if run >= 5: p1 += 3 + run - 5
    p2 = sum(3 for y in range(n - 1) for x in range(n - 1)
             if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1])
    pa = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]; pb = pa[::-1]
    p3 = 0
    for linhas in (m, [list(c) for c in zip(*m)]):
        for row in linhas:
            for x in range(n - 10):
                s = row[x:x + 11]
                if s == pa or s == pb: p3 += 40
    esc = sum(sum(r) for r in m)
    p4 = 10 * (abs(esc * 20 - n * n * 10) // (n * n))
    return p1 + p2 + p3 + p4, (p1, p2, p3, p4)


def _montar():
    bits = bits_dados()
    dados = [int(''.join(str(x) for x, _ in bits[i:i + 8]), 2) for i in range(0, len(bits), 8)]
    ecc = rs_resto(dados, N_ECC)
    papel, val = funcoes()
    ordem = ordem_dados(papel)
    assert len(ordem) == (N_DADOS + N_ECC) * 8 + RESTO
    fluxo = [(cw >> (7 - k)) & 1 for cw in dados + ecc for k in range(8)] + [0] * RESTO
    cru = val.copy()
    for (x, y), b in zip(ordem, fluxo): cru[y, x] = b

    def aplicar(mk, com_formato=True):
        mm = cru.copy()
        for (x, y) in ordem:
            if MASCARAS[mk](x, y): mm[y, x] ^= 1
        if com_formato:
            f = bits_formato(mk)
            for cop in posicoes_formato():
                for i, (x, y) in enumerate(cop): mm[y, x] = (f >> i) & 1
        return mm

    todas = [aplicar(k) for k in range(8)]
    notas = [castigo(m) for m in todas]
    mk = min(range(8), key=lambda k: notas[k][0])
    return dict(bits=bits, dados=dados, ecc=ecc, papel=papel, val=val, ordem=ordem, fluxo=fluxo, cru=cru,
                todas=todas, notas=notas, mascara=mk, final=todas[mk], formato=bits_formato(mk))


Q = _montar()
PAPEL, ORDEM, FINAL, CRU, MASC = Q['papel'], Q['ordem'], Q['final'], Q['cru'], Q['mascara']
# índice do bit (0..358) de cada módulo de dados; -1 nas peças fixas
IDX = -np.ones((N, N), np.int32)
for _i, (_x, _y) in enumerate(ORDEM): IDX[_y, _x] = _i
LETRAS_BITS = {}                 # letra k -> lista de (x, y) dos seus 8 bits
for _i, (_b, _r) in enumerate(Q['bits']):
    if _r[0] == 'letra': LETRAS_BITS.setdefault(_r[1], []).append(ORDEM[_i])


def contagem():
    c = {k: int((PAPEL == k).sum()) for k in (LOC, SEP, SIN, ALI, FMT, ESC)}
    return c


# =================================================================== literais
def _de_hex(h, n):
    b = bin(int('1' + h, 16))[3:][:n * n]
    return np.array([int(c) for c in b], np.uint8).reshape(n, n)


# ------------------------------------------------------------------ cores das peças
COR_PECA = {LOC: (LOC_E, LOC_C), SEP: (LOC_E, LOC_C), SIN: (SIN_E, SIN_C), ALI: (ALI_E, ALI_C),
            FMT: (FMT_E, FMT_C), ESC: (FMT_E, FMT_C)}
PECA_DADO, PECA_ECC, PECA_RESTO = (DAD_E, DAD_C), (ECC_E, ECC_C), (TIN2, PAP1)


def par_de(x, y):
    p = int(PAPEL[y, x])
    if p: return COR_PECA[p]
    i = IDX[y, x]
    return PECA_DADO if i < N_DADOS * 8 else (PECA_ECC if i < (N_DADOS + N_ECC) * 8 else PECA_RESTO)


PAR_E = np.zeros((N, N), np.int16); PAR_C = np.zeros((N, N), np.int16)
for _y in range(N):
    for _x in range(N):
        PAR_E[_y, _x], PAR_C[_y, _x] = par_de(_x, _y)


def cores_de(valor, visivel, colorido):
    """Matriz de cores: -1 = encaixe vazio; colorido (bool NxN) = cor da peça."""
    v = np.asarray(valor).astype(bool)
    c = np.where(v, TIN0, PAP3).astype(np.int16)
    col = np.asarray(colorido, bool)
    c = np.where(col & v, PAR_E, c); c = np.where(col & ~v, PAR_C, c)
    return np.where(np.asarray(visivel, bool), c, -1).astype(np.int16)


# =================================================================== desenho do código
S = 6                            # px por módulo
MARGEM = 4                       # zona livre (módulos)
CX0, CY0 = 28, 29                # canto do primeiro módulo
CARTAO = (CX0 - MARGEM * S, CY0 - MARGEM * S, (N + 2 * MARGEM) * S, (N + 2 * MARGEM) * S)   # 4, 5, 198, 198


def centro_mod(x, y, x0=CX0, y0=CY0, s=S):
    return x0 + x * s + s / 2, y0 + y * s + s / 2


def imagem_qr(cores, s=S, margem=MARGEM, escuros=None, encaixe=True):
    """Imagem (índices de paleta, -2 = transparente) do cartão com o código."""
    n = cores.shape[0]
    tot = (n + 2 * margem) * s
    img = np.full((tot, tot), PAP3, np.int16)
    big = np.repeat(np.repeat(cores, s, 0), s, 1)
    o = margem * s
    reg = img[o:o + n * s, o:o + n * s]
    m = big >= 0
    reg[m] = big[m]
    if escuros is None: escuros = np.isin(cores, [TIN0, LOC_E, SIN_E, ALI_E, FMT_E, DAD_E, ECC_E, TIN2])
    vaz = cores < 0
    if encaixe and vaz.any():
        vb = np.repeat(np.repeat(vaz, s, 0), s, 1)
        reg[vb] = PAP2
        yy, xx = np.mgrid[0:n * s, 0:n * s]
        borda = vb & (((xx % s) == 0) | ((yy % s) == 0))
        reg[borda] = PAP1
    # relevo: luz no topo do borrão escuro, sombra no papel logo abaixo
    if s >= 4:
        e = np.asarray(escuros, bool) & ~vaz
        topo = e & ~np.vstack([np.zeros((1, n), bool), e[:-1]])
        baixo_claro = ~e & ~vaz & np.vstack([np.zeros((1, n), bool), e[:-1]])
        for (yy, xx) in zip(*np.nonzero(topo)):
            cor = TIN1 if cores[yy, xx] == TIN0 else int(cores[yy, xx])
            if cor != TIN1: continue
            reg[yy * s, xx * s:(xx + 1) * s] = TIN1
        for (yy, xx) in zip(*np.nonzero(baixo_claro)):
            if cores[yy, xx] == PAP3: reg[yy * s, xx * s:(xx + 1) * s] = PAP2
    # borda do cartão: papel sombreado embaixo e à direita, contorno escuro
    img[-3:, :] = np.where(img[-3:, :] == PAP3, PAP2, img[-3:, :])
    img[:, -3:] = np.where(img[:, -3:] == PAP3, PAP2, img[:, -3:])
    yy, xx = np.mgrid[0:tot, 0:tot]
    canto = ((yy >= tot - 3) | (xx >= tot - 3)) & ((xx + yy) % 2 == 0)
    img[canto & (img == PAP2)] = PAP1
    img[0, :] = PAP2; img[:, 0] = PAP2
    img[0, 0] = img[0, -1] = img[-1, 0] = img[-1, -1] = -2
    return img


def colar(tela, img, x, y, clip=(0, 0, W, PALCO_H)):
    h, w = img.shape
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(clip[0], x), max(clip[1], y)
    x1, y1 = min(clip[2], x + w), min(clip[3], y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x]
    reg = tela.buf[y0:y1, x0:x1]
    m = sub >= 0
    reg[m] = sub[m]


def cartao(tela, cores, x=CARTAO[0], y=CARTAO[1], s=S, sombra=True, **kw):
    img = imagem_qr(cores, s, **kw)
    if sombra:
        h = img.shape[0]
        dither(tela, x + 4, y + 4, h, h, FUNDO, PRETO)
        tela.ret(x - 1, y - 1, h + 2, h + 2, PRETO)
    colar(tela, img, x, y)
    return img


def colar_girado(tela, img, cx, cy, ang, escala=1.0, clip=(0, 0, W, PALCO_H), sombra=True):
    """Gira a imagem (vizinho mais próximo) em torno do centro (cx, cy)."""
    h, w = img.shape
    R = math.hypot(w, h) / 2 * escala + 2
    x0, x1 = int(max(clip[0], cx - R)), int(min(clip[2], cx + R))
    y0, y1 = int(max(clip[1], cy - R)), int(min(clip[3], cy + R))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ca, sa = math.cos(-ang), math.sin(-ang)
    dx, dy = (xx + .5 - cx) / escala, (yy + .5 - cy) / escala
    sx = ca * dx - sa * dy + w / 2
    sy = sa * dx + ca * dy + h / 2
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    ix, iy = np.clip(sx.astype(np.int32), 0, w - 1), np.clip(sy.astype(np.int32), 0, h - 1)
    v = img[iy, ix]
    ok &= v >= 0
    reg = tela.buf[y0:y1, x0:x1]
    if sombra:
        sh = np.zeros_like(ok); sh[4:, 4:] = ok[:-4, :-4]
        reg[sh & ~ok & ((xx.astype(int) + yy.astype(int)) % 2 == 0)] = PRETO
    reg[ok] = v[ok]


def colar_torto(tela, img, x, y, amp, t, clip=(0, 0, W, PALCO_H)):
    """Cartão dobrado (onda suave): para mostrar a imagem torta."""
    h, w = img.shape
    x0, x1 = max(clip[0], int(x) - 10), min(clip[2], int(x) + w + 10)
    y0, y1 = max(clip[1], int(y) - 10), min(clip[3], int(y) + h + 10)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    u, v = (xx - x) / w, (yy - y) / h
    sx = (xx - x) + amp * np.sin(v * math.pi * 1.0 + t) * 6 + amp * 8 * (u - .5) * (v - .5) * 4
    sy = (yy - y) + amp * np.sin(u * math.pi * 1.3 + t * .7) * 7
    ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
    ix, iy = np.clip(sx.astype(np.int32), 0, w - 1), np.clip(sy.astype(np.int32), 0, h - 1)
    vv = img[iy, ix]
    ok &= vv >= 0
    reg = tela.buf[y0:y1, x0:x1]
    reg[ok] = vv[ok]
    return sx, sy


def flash(tela, x, y, idade, x0=CX0, y0=CY0, s=S, cor=AMARELO):
    """Módulo que acabou de chegar: brilha e um anel se abre."""
    if idade < 0 or idade > .35: return
    px, py = x0 + x * s, y0 + y * s
    if idade < .12:
        tela.ret(px, py, s, s, BRANCO if idade < .05 else cor)
    k = int(idade / .35 * 4) + 1
    tela.ret_vazado(px - k, py - k, s + 2 * k, s + 2 * k, cor if idade < .2 else CHAMA1)


def contorno_mods(tela, mods, cor, x0=CX0, y0=CY0, s=S, esp=1):
    """Contorno em volta de um conjunto de módulos (só as bordas de fora)."""
    st = set(mods)
    for (x, y) in st:
        px, py = x0 + x * s, y0 + y * s
        if (x, y - 1) not in st: tela.ret(px - esp, py - esp, s + 2 * esp, esp, cor)
        if (x, y + 1) not in st: tela.ret(px - esp, py + s, s + 2 * esp, esp, cor)
        if (x - 1, y) not in st: tela.ret(px - esp, py - esp, esp, s + 2 * esp, cor)
        if (x + 1, y) not in st: tela.ret(px + s, py - esp, esp, s + 2 * esp, cor)


# =================================================================== textos e setas
def rotulo(tela, txt, tx, ty, ax, ay, cor=AMARELO, tam=9, cotovelo=None):
    """Texto com fio até a peça; `cotovelo` = ponto do meio (fio em L)."""
    w = tela.largura_texto(txt, tam)
    hy = ty + (3 if tam == 9 else 7)
    ex = tx - 3 if ax < tx else tx + w + 2
    pts = [(ex, hy)] + ([cotovelo] if cotovelo else []) + [(ax, ay)]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        tela.linha(a, b + 1, c, d + 1, PRETO)
        tela.linha(a + 1, b, c + 1, d, PRETO)
    for (a, b), (c, d) in zip(pts, pts[1:]):
        tela.linha(a, b, c, d, cor)
    tela.disco(ax, ay, 2.2, PRETO); tela.disco(ax, ay, 1.3, cor)
    tela.ret(ex - 1, hy - 1, 3, 3, cor)
    tela.texto(txt, tx, ty, cor, tam=tam, contorno=PRETO)


def centro_preso(tela, txt, cx, y, cor, tam=9, xmin=2, xmax=296):
    w = tela.largura_texto(txt, tam)
    x = int(min(max(cx - w / 2, xmin), xmax - w))
    tela.texto(txt, x, y, cor, tam=tam, contorno=PRETO)


def seta(tela, x0, y0, x1, y1, cor, esp=2, ponta=5):
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


def bloco(tela, x0, y0, x1, y1, corpo, luz, sombra):
    """Peça maciça: contorno, corpo, filete de luz, sombra e meio-tom embaixo."""
    x0, x1 = sorted((int(round(x0)), int(round(x1)))); y0, y1 = sorted((int(round(y0)), int(round(y1))))
    if x1 - x0 < 1 or y1 - y0 < 1: return
    tela.ret(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2, PRETO)
    tela.ret(x0, y0, x1 - x0, y1 - y0, corpo)
    if y1 - y0 >= 4:
        dither(tela, x0, y0 + (y1 - y0) * 2 // 3, x1 - x0, (y1 - y0) - (y1 - y0) * 2 // 3, corpo, sombra)
    tela.ret(x0, y0, x1 - x0, 1, luz)
    tela.ret(x0, y1 - 1, x1 - x0, 1, sombra)


def celula_bit(tela, x, y, v, w=9, h=11, pulso=0.0, cor1=AMARELO, cor0=FUNDO3):
    """Casa de um bit: 1 aceso (brilha), 0 apagado, com o algarismo dentro."""
    tela.ret(x - 1, y - 1, w + 2, h + 2, PRETO)
    if v:
        tela.ret(x, y, w, h, cor1)
        dither(tela, x, y + h * 2 // 3, w, h - h * 2 // 3, cor1, LARANJA if cor1 == AMARELO else ACO2)
        tela.ret(x, y, w, 1, CHAMA0 if cor1 == AMARELO else BRANCO)
    else:
        tela.ret(x, y, w, h, FUNDO2)
        tela.ret(x, y, w, 1, cor0)
    tela.texto('1' if v else '0', x + w // 2 - 2, y + (h - 7) // 2, PRETO if v else ACO2, tam=9)
    if pulso > 0:
        tela.ret_vazado(x - 2, y - 2, w + 4, h + 4, BRANCO if pulso > .5 else AMARELO)


def grade_fundo(tela, x1=W, t=0.0):
    """Fundo: mesa escura com uma grade de pixels bem apagada."""
    tela.buf[:PALCO_H, :x1] = FUNDO
    for x in range(0, x1, 12): tela.ret(x, 0, 1, PALCO_H, FUNDO2)
    for y in range(6, PALCO_H, 12): tela.ret(0, y, x1, 1, FUNDO2)
    k = int(t * 2)
    for j in range(6):
        gx = ((j * 97 + k * 12) % (x1 // 12)) * 12
        gy = ((j * 53 + k * 6) % (PALCO_H // 12)) * 12 + 6
        tela.ret(gx + 1, gy + 1, 11, 11, FUNDO2)


# =================================================================== a mancha de café
def mascara_mancha(cx, cy, r, seed=3, x0=0, y0=0, w=W, h=PALCO_H, gotas=True):
    """Máscara (h, w) de uma mancha: círculo com borda ondulada + respingos."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w].astype(np.float32)
    ang = np.arctan2(yy - cy, xx - cx)
    rr = np.hypot(xx - cx, yy - cy)
    ph = rng.uniform(0, 6.28, 4)
    borda = r * (1 + .12 * np.sin(3 * ang + ph[0]) + .08 * np.sin(5 * ang + ph[1]) + .05 * np.sin(9 * ang + ph[2]))
    m = rr < borda
    if gotas and r > 3:
        for k in range(7):
            a = rng.uniform(0, 6.28); d = r * rng.uniform(1.15, 1.5); rg = r * rng.uniform(.06, .14)
            m |= np.hypot(xx - (cx + math.cos(a) * d), yy - (cy + math.sin(a) * d)) < rg
    return m


def pintar_mancha(tela, m, x0=0, y0=0):
    """Café: escuro na borda (o anel que seca), xadrez por dentro e uns pontos
    de brilho. Opaca: a câmera vê a mancha toda como escura."""
    h, w = m.shape
    reg = tela.buf[y0:y0 + h, x0:x0 + w]
    dentro = m.copy()
    er = m.copy()
    er[1:, :] &= m[:-1, :]; er[:-1, :] &= m[1:, :]; er[:, 1:] &= m[:, :-1]; er[:, :-1] &= m[:, 1:]
    er2 = er.copy()
    er2[1:, :] &= er[:-1, :]; er2[:-1, :] &= er[1:, :]; er2[:, 1:] &= er[:, :-1]; er2[:, :-1] &= er[:, 1:]
    yy, xx = np.mgrid[0:h, 0:w]
    escuro_baixo = np.isin(reg, [TIN0, TIN1, TIN2, LOC_E, SIN_E, ALI_E, FMT_E, DAD_E, ECC_E])
    cor = np.where((xx + yy) % 2 == 0, CAF0, CAF1)          # opaca: esconde o que está embaixo
    reg[dentro] = cor[dentro]
    anel = m & ~er2
    reg[anel] = CAF0
    luz = er2 & ~np.roll(er2, 2, 0) & ((xx + yy) % 3 == 0)
    reg[luz] = CAF2


def mods_sob_mancha(m_tela):
    """Módulos (x, y) cujo centro está sob a mancha (máscara do tamanho da tela)."""
    out = []
    for y in range(N):
        for x in range(N):
            cx, cy = centro_mod(x, y)
            if m_tela[int(cy), int(cx)]: out.append((x, y))
    return out


def bytes_estragados(mods, final=None):
    """Bytes (0..43) com pelo menos 1 bit errado: módulo claro coberto de café
    vira escuro para a câmera."""
    final = FINAL if final is None else final
    est = set()
    for (x, y) in mods:
        i = IDX[y, x]
        if i >= 0 and i < (N_DADOS + N_ECC) * 8 and final[y, x] == 0:
            est.add(i // 8)
    return sorted(est)


def peca_fixa_sob(mods):
    return any(PAPEL[y, x] in (LOC, SEP, FMT, SIN, ALI) for (x, y) in mods)


# =================================================================== objetos
def celular(tela, x, y, w, h, t=0.0, tela_cor=FUNDO2):
    """Um celular genérico (sem marca): corpo, tela, botão lateral."""
    LG.painel(tela, x - 1, y - 1, w + 2, h + 2, borda=PRETO, fundo=PRETO)
    tela.ret(x, y + 2, w, h - 4, ACO0); tela.ret(x + 2, y, w - 4, h, ACO0)
    tela.ret(x + 1, y + 1, w - 2, h - 2, ACO0)
    tela.ret(x + 2, y + 1, w - 4, 1, ACO2)
    tela.ret(x + w, y + 20, 1, 12, ACO1)
    tela.ret(x + 3, y + 8, w - 6, h - 16, tela_cor)
    tela.ret(x + w // 2 - 4, y + 3, 8, 2, PRETO)
    return (x + 3, y + 8, w - 6, h - 16)


def mira(tela, x, y, w, h, cor=BRANCO, k=8):
    """Cantoneiras de visor de câmera em volta de (x, y, w, h)."""
    for (a, b, sx, sy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        tela.ret(a if sx > 0 else a - k, b if sy > 0 else b - 2, k, 2, cor)
        tela.ret(a if sx > 0 else a - 2, b if sy > 0 else b - k, 2, k, cor)


def caixa_papelao(tela, x, y, w, h, etiqueta=None, icone='engrenagem', t=0.0):
    bloco(tela, x, y, x + w, y + h, CAR1, CAR2, CAR0)
    tela.ret(x + w // 2 - 3, y, 6, h, CAR2)
    tela.ret(x + w // 2 - 3, y, 1, h, CAR0)
    if etiqueta is not None:
        e = etiqueta
        colar(tela, e, x + 4, y + h - e.shape[0] - 4)
    ix, iy = x + w - 14, y + 12
    if icone == 'engrenagem':
        pts = []
        for k in range(16):
            a = t * .0 + k * math.pi / 8
            rr = 7 if k % 2 == 0 else 5
            pts.append((ix + math.cos(a) * rr, iy + math.sin(a) * rr))
        poligono(tela, pts, CAR0); tela.disco(ix, iy, 2, CAR1)
    elif icone == 'pistao':
        tela.ret(ix - 5, iy - 6, 10, 8, CAR0); tela.ret(ix - 1, iy + 2, 2, 6, CAR0)
        tela.disco(ix, iy + 8, 2.5, CAR0)
    else:
        tela.disco(ix, iy, 6, CAR0); tela.disco(ix, iy, 3, CAR1)


# =================================================================== versões (gerado pela segno)
# Cada uma: a frase do vídeo forçada na versão, nível L. Linha a linha, 1 = escuro.
VERSOES_HEX = {
    1: (
        'fe0bfc14d06e82bb7585dba3aec16d07faafe00b00fbc5554b6238c715b358d97c8f806f93fa695049aebae965d52daeaa51'
        '0569cfef0b0'
    ),
    3: (
        'fe999bfc1777506e8eeebb744445dbaf772ec1488907faaaafe0177700e6e6679be7332885e445e2a28880bdb5ddb7988444'
        '38aebbb0352377b33b666bc2a6332833ec477a2848829f39ddfe00444473f93beab05b751aba467fbdd13322aea441af0588'
        '898fefdca68'
    ),
    5: (
        'fee85e83fc1706b0506ead60d6bb75a7ca75dba06b06aec14f94f907faaaaaafe0094f9400ce17a17978cf42f41c358fca7c'
        '9ce2ab06bc5a32c1ac591c635835f76c035830819d4f94351ff7a17bc9e242f436e4e7ca7cc971ab06be55a0c1ac589cc358'
        '357d9b83583112994f94152277a17a96e442f43648efca7cd832ab06bd7d28c1acf90073583477f803586a10594f951cba97'
        'a17fadd142f46cee8fca795d056b06986fe8c1ac7d8'
    ),
    10: (
        'fe08e504dfb33fc15bd929c472906e84b9d917c8cbb752e656315c25dba18e57edfa52ec16bd931c473107faaaaaaaaaaafe'
        '0055ce4472aa00fbe623bfec80d53c7cbe725cea821e98136cf3281469a6a31c6508a2d4bb04596751c438a569c7190244ab'
        '3d0136d954e541ca3a31c6508acaff3845967518b276869c719026b2a683936d954e041007631e6508aeac316458e7501ca2'
        '4109c4d90226d22e49373954e73c400e31269c45e6a29554ce137fae16ff508da3157e83feec8f845f7f0f159cec4be691ed'
        'ab932ab8ae4ae4c4772916fd8451bee6c8fe2393fff289ce5cbe64150f1132958ae6ffb28272946fd9192dcc6c8762391bec'
        'bb5ce54be4515225532958af617ea1f72946fd9669bfe6c87623d2603bb1ced472a8985bb023e5ec81c222e8be685ceaa905'
        'bf1369732871613ea31a6508c2df72245e475198796089c689024aaa9a51369154e601f0c631a65088aa02be45fe7518fa00'
        '4f9c71902646bfad136a954e6a104ce31c6508b1abacc45fe7511fa5d799c419022492eb7137d954a519052a31469c4414fe'
        '8954f6137f570'
    ),
    20: (
        'fee3106b10d60d66e53e51bfc146c960f3d0bd0a05e85c506eac57e53271c71c42f42e6bb7515da7c0835835760d6095dba2'
        '5706bfeb06b0fe53e50aec144f96045f29f2c41ac1a907faaaaaaaaaaaaaaaaaaaaafe002a3e391f42f41106b06900ce7532'
        '49fd83583fd60d60978eb198f9c46b06b77e53e5bf5cad1b29a017a17bf94f949530ba2bd0aa38e38fe17a17903133752c06'
        'be53e524f94f8a908d2a8350b583586729f29bf5ecd834f8706b06a7f29f09530326be39938e38f206b0780313d55249fbe5'
        '3e54560d2029084198f9c75835877e53c25f54cd0a38a106b06bfb6dbf6532b26b0d6a38e38fe8e38e38717cdcc2e7be53e5'
        '2306b06c9304d99e8475835864d60d68cf8cd0da12106b06b73e53e08dcb37bc1aa1ac1aff42f42dbc67d5c2487a7ca7d2d6'
        '0d60b4804d18f94794f94ebe53e53350cd2838b960d60d1b6db6d528b37a0d6638e38cc8e38e203c7ddcc2e1be53e4a306b0'
        '6497049d5e8675835864d60d64c60cf6ab02106b06b73e53e6a86b2590d6a1ac1affca7ca68cffd54c2efa7ca7dfb06b06fc'
        'e44d9de84794f94c4d60d644c2b91cb06b60d60ab3e53e6acf1abb0d51d60d631ca7ca51cbfd50c2ffc1ac1afb06b06fce2e'
        'eade83ca7ca714d60d620c3e984b03c71c71cb1c71c3ece3ef31c7c1ac1af8db6db74cbbd50ca7ca7ca7c929f29f24e62fad'
        '240f94f94141ac1a28c1b81cd62d60d60cb7a17a3ece32bf2f7cd60d638ca7ca74cbf916c2ecc1ac1a9306b0724e2dfade8c'
        '4a7ca714d60d628c1b885b04a71c71cb1c71c3ece32ffdc4fd60d630db6db74cb3156aa7d41ac1af29f28f24ea8cac240ca7'
        'ca7241ac072bc29885472c71c71c358358fe4813eef2bcd60d63c53e57c44a60deac0cc1ac1a94f94f8a4dcc4e035c4a7ca7'
        '1729f29eb749e875eca71c71cbd0bd0a73b12dffe4ff42f4309f29f303021d72a6d583582f29f29f6156c8a024c46b06b241'
        'ac1a18dc98c3474a17a17c35835866d310fef28fd60d62453e53dac5f9deac0fc1ac1afcf94f8fc944cec35c4a7ca7c729f2'
        '9c7ceba874faa71c71abd0bd0ab5b13cef291f42f43117a17912cf956ac0fd83583fcf94f8f8b008e435e86b06bbf29f297f'
        '5c8c824fbc17a178fd0bd0ad220fce728538e38e217a178c3c73548c163e53e5c4f94f959302af635db583587329f29535c8'
        '49acfa506b06cdf29f2b322074ea38df42f41106b06833c771684905835825d60d61393018f4f9e86b06bbfe53e5775c8582'
        'a9bc17a17cf94f94b7220fc2908538e38d217a17803c7314cc163e53e444f94f929300bc435db58358b729f297f5ef59a4f8'
        '506b06cff29f2b5229f82a39d38e38d206b07003ca330a48e3e53e44560d6729301be5f91b58358b7e53e77c5ad51a38e106'
        'b06cfb6db2b420bf928d4e38e38d28e38e007f6ab822f7be53e40306b07ad661fe9e8d75835884d60d63cc0f31c210506b06'
        'd73e53e54d4be92819d1ac1ad642f42f0cfb329248fa7ca7cfd60d60fc805721f9c794f94c7e53e5477f933a38eb60d60abb'
        '6db6eb305fb08d7138e38d18e38e113baba022efbe53e4fb06b07f95d1721e8f35835830d60d6546e9518307306b06853e53'
        'e00d05c818d501ac1ad7ca7ca72efeab922e0a7ca7d6b06b077d8'
    ),
    40: (
        'feac88f6095ff4920327b7560a98f97fca21859f5a3fc150c9563e0150c3af797510bfe7d7054caa6c2501506eb73a0aebaa'
        '02cb77b61a344759e1280cff9cb82a8bb75f419b6e3beb8e1531a3b098064a2f8cf460b6bb35dba288e7f8e58f2fa0327bfa'
        'e6a98f97e4faf859f5c2ec1518a947dc293c7af797c7c9fe7c7058c646c2501507faaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        'aaaaaaaafe00bcdf71525f191bbdb0d162fa0d194364d1e5c15100ce04f0bf8ba527ff5672ef9b5fadff82994ffa4a2017f4'
        '56447b04af7a690193d727057c3c7fe710c1cfafbae1b69b56e0ff378628474111a01c141d59a8c86d7f57ef2bdd0575d531'
        '69bbd80e2a23ace0a4067fce9c15115ea85f2ac8e2123ef566aebfb3fcdae839854fe4a20227455473b00ac7949019fdb973'
        '54c3cbf27d0c2ccafbae1b63af6e4feb61e2c434761b00c147d39c8c9ecfd57ef2b4d8574d5f1a5b8db0d162fa0e094364fc'
        'e5cd51d5ea87f4ac8e25278f4e72fa1b5fadaf829954fa4e20427456043b00ac7a690d93d727057c3c7fe710c1c7ac8ae1b6'
        '5a76e0feb78628474111a01c141d59a8c8697ec7ef2b7dc576d5f169bbd80e2623ace0a4067fce9c15d15ea87f2ac862523e'
        '9566aeb9b3fcdae839954fe5a24227456063b0cac7a4a019fdba7354c3cbf2710c2cca7b9e1b65a76e0feb79fac434771b00'
        'c147d39a8c9ecf9566f2b7dc577d5f16538db0d1623a0e094367fce5cd61d9ea87f2ac9625238f4872fa1b3fadaf839954fa'
        '4e38467456063b00ac7a690e93d727357c3c7f2710c1c7ac8ae1b65a76e0feb79e29c74111b01c141d39a8c86b7ec7ef2b7d'
        'c576d5f165bb580e2623a0e0a4367fce9f15d15ef87f2af862523f9566cff9b3fadff83995ffe5224fa7456063c4cac7ac60'
        '19cd467357cc47f271449cca7c5e2b65a72a0feb7ebac46c6b1b01c2a0539aeae6cf92a6f1b7dc717d5f15138d88f162380f'
        '1a8367f1d9cd6119ef87f2af962523ff486aff9b3e2cffe3995fe64e38fe7456063640ac7a850e9fd5e735bc545f271a41c7'
        'ac12e1d65a7660feb78a2dc74671b07c601d21ad886a7e83ee977dc476d5f15fb8580e8603a0f8a43a7f6e9f95db5e287eaa'
        '4062523d14e6ce69abface783f949fe562592725602364cac72860d9cd5e7f57c987f071a49cca421e0d6487660feb18bac4'
        '6c671d01c060539b58e6cf99a6f9b79c777d5f25f38d88e862380caa836736d9cd6539e2a7dabd16253bd1486ae69b3e2c7f'
        'e39929e64e39f6706e263208a47a860e9fd5e735bc545f273a41c4a401e0d2466e62f8b78badc74671b07c601d21ad886af8'
        '926f167cc766d6f15f38580e8603a0f8a43a7f6e9fd6db1228fe2cc163d23d1486ce69abface783f949fe563d923256023ac'
        '89c72860e9cd5e7f57c987f071a49c4a421e0d44e6c42e6b18badc6c671d01c060539b58e6af89a6f9a7bcd46d9f25f38588'
        'e862380caa836736d9fd6d39a2bfda9d16653bd1486ce69b3e2c7fe3992fe6563d96686e261288a44a860e9cd5e735bc545f'
        '273949c4a421e4d6466e22f8af8badc6c671b07c600521ac0e6af89a6f147cc746d6fd5f38588e86c380e8a83a7fed9fd6d3'
        '9028fe2cc163d63d1486ce69cbe2c67e3e941e6563d963256023bc89c72860e9cd5e4f5bc585f0b1e49c4a421e0d44e6c42e'
        '6b18badc6c670d07c660527b38e6af89a6f9a7bcd86d9f25f38588e860340e8a839706d9fd6d39afbfda9f96653bf9486cef'
        '9ab82cfff3f93fe6563dfe7c6e261c48a442c60e9cdc67f6bc4453073c79c4a445eaa6466ea2f8a9abadc686b1d17c6a0321'
        'b2b66af8ea6f187cc716d6fe713858bf16c38011ab3a73119fd6d190fafe2cf963d7bf9486d6f9cbe2affe3e92fa6563dfe3'
        '0560231889472ea0e9c1f64f5bf305f0b3b49f4a409e3dc5e6e3ae0b1ddad86c510d07d320527b72e72f8ae6e2277cc56daf'
        '24538688c360340f3a839723d93d6ed9a73fc283b67d3a8149eceb9ab82d3ff3f93966163d667e5e0e1e089442ea0e5cdf67'
        'f6bc30530734f9c49409ebde4e6412e0a9ddedc68511d17c320321b0d66aa0ae6f2070cb2adafe450858bc36c38033ab3a70'
        'c19ffaed9cb37a2cbd67d7a80c86d6b9cbe2b3fe3e924a6567d66369a1e09889442eace9c1f64f5bf305f0b3b49f4a409f0f'
        'a4e623ae0a9ddad86c510d07d320527b72e72f8ae7fa170cf56dafe4538688c36c340f3a839723d93d6ed9ab37a28bb67d7a'
        '8129eceb9cb82d3ff3e93966163d661e5a1e3a889442ea3e5cdf64f6bc30530b37f9c41409789a4e6272e0a9ddf5c68510d1'
        '7c2a0327b1566a80ae1f8170cf1adafe450058bc36c3403fab3972019feafd89a37a28b567d7a80c80d6b9cb82b5ff3e938a'
        '657fce7961a1e39889442eaceac1f64f6bf10530b377974a489f49a4e627ae0a9ddad9e8510d17d338327b13612f8ae7d817'
        '0cf56dafe453860bc36c342336b397231a3d6ed99b37a28b367d7a8129ed0b9cb83339f3e93927963d66165a1e3a889442ea'
        '3e5c2f64f6b332530b3779f41409749a4e6272e0a9ddf5869d10d17b2a02a7b1367a80ae1d8170cf1adafe450068b436c140'
        '3fabf972319feacda9fb7a38fd67d7af8c98d6f9ca02bfff5e93fa617fcff945a1e7c689442c6ce6c1464fabf44510b3c797'
        '4b445f6bb4e22b2e0a9abed9e82b0d77d6b832636b612f0aa7d1170ef1edafe510860bf14c342316b39b111a3d2f199fb122'
        '9fb67d7af8a9ed0f84b833f9f3ef3fa7963cfe141b9eb1a894c2c2fe5c21e8f6b32e530938b9f4147174fbee87b2e0c9abf5'
        '869c56d17b5602a7b0567280fa1c01b00cbadace4e0068b786c14039abf9719193eac7a93b0a30d767cfb50a98d6e1ca02ae'
        '7f5e93e2617fd17949a9d30ab1442c2fe6c11e4fabf1c510b38b97414b1f4db4ee7b300a98bf59e8450d77d4783263056128'
        '0da7c0160acba2afe5e0060bf84c342356b39b191a3eaf5993b0a48d73fd7ad0a98d0e04b83281f3ef3e2797fc9e141b1eb0'
        'a897c202fe6c21e8f6b32e530938b974147d74fb8e87b2e149ebf59e9c56d17b5782a7b0561280fa1c01800cbada0e4e0060'
        'b78ac142356bf97191a3eac7a93b0a30d7678fb50a98d087ca03281f5e83e2797fd17949a9d30ab1441c2fe6c22d4fab32e5'
        '10bf8b97414b174fb4ee7b300a80bf59e9dc0d77b5782a650561280de1c1160acba2afe9c0060b704cd42356bf98191a3eaf'
        '4a9330a48d73fd7ec8a98d0e04c03281f4ef3e2797fc8f949b1eb0a897c20efe6c21e8cab32e51c938b974143d74fb8e87b2'
        'e149edf59e9c56c77b5782c630561280da1c11800cbada0e4e0060b788c14e356bc9b191a3eaf7a9330a30d7678fb50a98d0'
        '864a05280f5ee3e2797fc97949a9d30ab14c1c2fe6c22d8fa832e9109f8ba74143174fa4ee7b300c80bf59a9dc6d76b57e2a'
        '650579280de1c1120acba2ace9c0063b704cd42355bf9819163eaf4a9fb4a48ff3fcfef8a9950f84c032f9f4ef3fa397fcff'
        '94591ebc6b17c2c6fe602468cab3c651c93c79771c4576bb0f46b50149ebf19e9eb6c77b6b82c632b61304ea1d1180ef182a'
        '0e710360b518c14e316bc9b311a32ad1a9fb0248ffbf8faf8b18d0fe4a052f8f5ee3fa793ecff90995db6a417c1e6f26c271'
        '8fa83829109ff3a74174575bb0e43b6814879f59a9d06d76b69e2a655b79081001c3190add8ea0e960063b528cd421b5bf98'
        '02162ea2da9f3022827ff8fe0ea99503e4c03251f4ee2b2387f9c790995db6ab17c1e9fe602818cab38251c9ff39771c4a75'
        'bb0e43b301487e719e9886c77b6982c655b61306879c3190add92a0e958360b6e8cd4e1b6bc98021a329ef69f30228273f8f'
        'e18b78d1fe4c05250f4ee2b2793e5db90995db6a417c1e6f16c2418ca838291c9ff3a7c174575bb0e43b6814861f41a9c86c'
        '76b69e2c655b79481001c3190add8ea0e9a00e3b5e8cd4e1b5bc9802160ea2fa9f3022827ff8fe7ea99307e4c05250f4ee2b'
        '238ff9df90995db6ab17c1c5fe632898ca838291c9ff32771c4675bb0e43b3014878719b18e6c76b69fac655b19306819c31'
        '90add92a0e96836336d8cd6e1b57c980226329ef69f30228273f8fe18b7951e64c1d25094ee2b3b93e5db90995db6a417c1e'
        '6f1602418ca4382b1c9ff3a7e174575b30e43b6814861f01a9c86c70b69e2de55b79501001c3990add8ea0e9a03e3b5e8ed4'
        'e1b5bc5802160aa23a9f3022827ff8fe7eb19307e5405250f48e2b238bf9bf90895db6aa17c9c5f26328980a838291e9ff32'
        '771f7675a31043b3014e78719b1ce6a76b69fac64db19306919c3590add96a0d96836335d8cd6e3b57c98c2263296f69f880'
        'a8ff5f8e6feb7950fe4c1d3f894ee4fbb93e5fb945151b4651fc145f1602c58ca43c6b1c9dc7a7f1f4676b11a46b287482a7'
        '01a9aa6c70b6be2de52b795076b9d1b9fa51be90e9183e3b518ed4e115bc5811160293121fa83adfffe0fefeb7930fe54053'
        'f8f48e2fa38be1fbf68d69952527c94df16323180a83ea91e9fdb27f1f6e47a1145cb2994e6c701b19e6a76b7ffac64a7195'
        '077d849592a8dbe60da083e33548cd6e2457c98cd260292068e000ae17fb8e72eb79318e4c1d22094ee56bb8be063fe9d51b'
        '9251ff17df16323d8ca432ab1c9ddb27f1f5e7bb51a42b287507c701b19a6c70b5ffade52719507659e9b9fa5dbe902a083e'
        '335782d6e1457c580d260292861e283ac97fe0bf2eb793196341d3a0949e36bb8be003fe8d69912527c97df163231b0a43ea'
        'b1e5fdb27f1f6e47a1145eb2994e7c701b19a7a70b7ffad84a7195077d849592a8dbe60da083e33578edae2657c68cd26029'
        '20696000ae17fb8e72eb793196547d238848e56bb8be063f89d51b9251ff97df1632318094326bde9dd827f1f5e76b51a46b'
        '287567c701b59a6a60b59fcde4a6995076598179fa5dbe901a083e305782d6ed454c58cde60292861e683ac97fe0a72eb792'
        '996341d5a0949e56fb8be063f8bd6991852fc97df163e31b0a40aab1e5ddb24f1f4e46b1045eb29f4e7c705b19a7a70a5ffa'
        'd848718d0775841996a8fbe50da083d33578edae1657c68dd26c29206962072e0bfa0e72eb613196547d3b8848e4ebbcbe06'
        '3f8bd79b9d52ff97df1a323180943a6bde9d1827f6f5e79b50246b29f567c301b59a6a60b59fcde4e69957f65821b97addfe'
        '501a0b3e305782d6ed454c58cde6005286563812efdfa0a7ff37929fe341d5f8949e5ffb8ba0fb807959ac452ff9453163e4'
        '5b0a40c6b1e5d472cf1fc67f910246b29f566a705b1ea7a70a2bfad84ab18d076b905897a31be5019183d335182dae3157c6'
        '8d124c29316bab8128fbfa0a6fed6131fe347d2f8849e5fbbcbe0fbdd3959b4952ff915c1a3209b0943d2bde5dc427faff2e'
        'e910243329f5600281b5a67a60b4bfcd84ea9957f51905897a25fe501bebbe306d82daecf54c68dfe6015024feb81281dfa0'
        'a77f37f2946347d448849e457b8a20ba8'
    ),
}
FINAL_V2_HEX = (
    'fef53fc13f906e896bb74745dbab9aec154d07faaafe0047007f0118f25fdad88ddafd16a72ca1ae162c2da6ed174f19dea0'
    'af1efd0079c57fa2eaf05051bba9dfedd479aeebac5305b061fe7e3d8'
)


def versao(v):
    """Matriz (n x n, 1 = escuro) da versão v."""
    if v == 2: return FINAL.astype(np.uint8)
    n = 4 * v + 17
    return _de_hex(VERSOES_HEX[v], n)


assert (_de_hex(FINAL_V2_HEX, N) == FINAL).all(), 'o codificador não bate com a matriz guardada'
