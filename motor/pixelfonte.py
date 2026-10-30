#!/usr/bin/env python3
"""Fonte de pixel do RITMO PIXEL: 5x7, desenhada letra a letra.

Antes o texto saía de uma fonte de computador (DejaVu Mono) rasterizada em
corpo 8-17 com limiar: os traços engrossavam e afinavam conforme o tamanho e
cada letra tinha um peso diferente. É o detalhe que denuncia "filtro de
pixel" em vez de pixel art. Aqui cada glifo é uma grade 5x7 e só cresce por
múltiplos inteiros (1x, 2x, 3x): o traço é sempre um bloco.

    m = mascara('SUBSCRIBE', esc=2)      # np.bool_ (h, w)
    largura('SUBSCRIBE', esc=2)

Acentos viram a letra sem acento (o canal escreve em inglês; o resto é
garantia). Caractere sem glifo vira '?', e `faltando()` lista quais são, para
o verificador reprovar texto que a fonte não sabe desenhar.
"""
import unicodedata
import numpy as np

ALTURA = 7
ESPACO = 1          # entre letras, em pixels da grade (multiplicado pela escala)
LARG_BRANCO = 3

_G = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    'J': ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '!': ["#", "#", "#", "#", "#", ".", "#"],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    '.': [".", ".", ".", ".", ".", ".", "#"],
    ',': ["..", "..", "..", "..", "##", ".#", "#."],
    ':': [".", ".", "#", ".", ".", "#", "."],
    ';': ["..", "..", ".#", "..", "..", ".#", "#."],
    "'": ["#", "#", ".", ".", ".", ".", "."],
    '"': ["#.#", "#.#", "...", "...", "...", "...", "..."],
    '-': ["...", "...", "...", "###", "...", "...", "..."],
    '+': ["...", "...", ".#.", "###", ".#.", "...", "..."],
    '=': ["....", "....", "####", "....", "####", "....", "...."],
    '_': [".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    '(': [".#", "#.", "#.", "#.", "#.", "#.", ".#"],
    ')': ["#.", ".#", ".#", ".#", ".#", ".#", "#."],
    '&': [".##..", "#..#.", "#..#.", ".##..", "#.#.#", "#..#.", ".##.#"],
    '#': [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    '%': ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    '*': [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
    '<': ["...#", "..#.", ".#..", "#...", ".#..", "..#.", "...#"],
    '>': ["#...", ".#..", "..#.", "...#", "..#.", ".#..", "#..."],
    '→': [".....", "..#..", "...#.", "#####", "...#.", "..#..", "....."],
    '♪': ["..##.", "..#.#", "..#..", "..#..", "###..", "###..", "....."],
    '•': ["...", "...", "###", "###", "###", "...", "..."],
    '♥': [".....", ".#.#.", "#####", "#####", ".###.", "..#..", "....."],
    'º': [".##.", "#..#", ".##.", "....", "####", "....", "...."],
    '°': [".##.", "#..#", ".##.", "....", "....", "....", "...."],
    '~': [".....", ".....", ".#..#", "#.##.", ".....", ".....", "....."],
    '★': ["..#..", "..#..", "#####", ".###.", ".#.#.", "#...#", "....."],
}

_BASE = {}
for _k, _v in _G.items():
    assert len(_v) == ALTURA, _k
    w = len(_v[0])
    assert all(len(l) == w for l in _v), _k
    _BASE[_k] = np.array([[c == '#' for c in l] for l in _v], bool)

# ---------------------------------------------------------------- acentos (PT-BR)
# A grade cresce para 10 linhas: 2 em cima (acento), as 7 da letra, 1 embaixo
# (cedilha). Toda letra ocupa as 10, então a linha de texto tem altura fixa e
# a letra sem acento continua exatamente onde estava (o desenho desconta as 2
# linhas de cima).
TOPO, BAIXO = 2, 1
ALTURA_TOTAL = TOPO + ALTURA + BAIXO


def _acento(tipo, w):
    a = np.zeros((TOPO, w), bool)
    c = w // 2
    if tipo == 'agudo':
        a[0, min(w - 1, c + 1)] = True; a[1, c] = True
    elif tipo == 'grave':
        a[0, max(0, c - 1)] = True; a[1, c] = True
    elif tipo == 'circ':
        a[0, c] = True; a[1, max(0, c - 1)] = True; a[1, min(w - 1, c + 1)] = True
    elif tipo == 'til':
        for x in (c - 1, c, c + 2): a[0, max(0, min(w - 1, x))] = True
        for x in (c - 2, c + 1): a[1, max(0, min(w - 1, x))] = True
    return a


_ACENTUADAS = {'Á': ('A', 'agudo'), 'À': ('A', 'grave'), 'Â': ('A', 'circ'), 'Ã': ('A', 'til'),
               'É': ('E', 'agudo'), 'Ê': ('E', 'circ'), 'Í': ('I', 'agudo'), 'Ó': ('O', 'agudo'),
               'Ô': ('O', 'circ'), 'Õ': ('O', 'til'), 'Ú': ('U', 'agudo'), 'Ü': ('U', 'circ'), 'Ç': ('C', 'cedilha')}
_GRADE = {}
for _k, _b in _BASE.items():
    g = np.zeros((ALTURA_TOTAL, _b.shape[1]), bool)
    g[TOPO:TOPO + ALTURA] = _b
    _GRADE[_k] = g
for _k, (_base, _tipo) in _ACENTUADAS.items():
    g = _GRADE[_base].copy()
    if _tipo == 'cedilha':
        w = g.shape[1]
        g[TOPO + ALTURA, w // 2] = True
        g[TOPO + ALTURA, max(0, w // 2 - 1)] = True
    else:
        g[:TOPO] = _acento(_tipo, g.shape[1])
    _GRADE[_k] = g

_TROCA = {'…': '...', '—': '-', '–': '-', '‘': "'", '’': "'", '“': '"', '”': '"', '×': 'X'}


def normalizar(txt):
    """Maiúsculas; acento do português fica (tem glifo); o resto perde o acento."""
    out = []
    for c in txt:
        if c in _TROCA: out.append(_TROCA[c]); continue
        if c in _GRADE or c == ' ': out.append(c); continue
        u = c.upper()
        if u in _GRADE: out.append(u); continue
        d = unicodedata.normalize('NFKD', u)
        d = ''.join(x for x in d if not unicodedata.combining(x))
        out.append(d if d and all(x in _GRADE or x == ' ' for x in d) else c)
    return ''.join(out)


def faltando(txt):
    """Caracteres que a fonte não desenha (depois de normalizar)."""
    return sorted({c for c in normalizar(txt) if c != ' ' and c not in _GRADE})


_cache = {}


def mascara(txt, esc=1):
    """Máscara booleana do texto: 10 linhas (2 de acento + 7 + 1 de cedilha)."""
    ch = (txt, esc)
    m = _cache.get(ch)
    if m is not None: return m
    t = normalizar(txt)
    cols = []
    for i, c in enumerate(t):
        if c == ' ':
            cols.append(np.zeros((ALTURA_TOTAL, LARG_BRANCO), bool))
        else:
            cols.append(_GRADE.get(c, _GRADE['?']))
        if i < len(t) - 1:
            cols.append(np.zeros((ALTURA_TOTAL, ESPACO), bool))
    a = np.concatenate(cols, 1) if cols else np.zeros((ALTURA_TOTAL, 1), bool)
    if esc > 1: a = np.repeat(np.repeat(a, esc, 0), esc, 1)
    if len(_cache) > 600: _cache.clear()
    _cache[ch] = a
    return a


def largura(txt, esc=1):
    return mascara(txt, esc).shape[1]


def escala_de(tam):
    """Corpo antigo (pontos da DejaVu) -> escala inteira da grade 5x7.
    A altura de maiúscula da DejaVu é ~0,73 do corpo: 7 px ~ corpo 9-13."""
    if tam >= 26: return 3
    if tam >= 14: return 2
    return 1


def dilatar(m, r=1):
    """Contorno de r pixels em volta da máscara (8 vizinhos)."""
    h, w = m.shape
    out = np.zeros((h + 2 * r, w + 2 * r), bool)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out[r + dy:r + dy + h, r + dx:r + dx + w] |= m
    return out
