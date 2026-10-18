#!/usr/bin/env python3
"""A resposta que se VE: a foto colada na colagem.

O quiz perguntava "qual pais tem um fuzil na bandeira?" e, na resposta,
mostrava so a palavra "Mocambique". A curiosidade estava ali e a tela nao
mostrava. Este modulo poe a prova na tela: uma foto (moldura branca de
revelacao, fita crepe, legenda a caneta) que bate no papel no instante da
revelacao.

Deck, por pergunta (tudo opcional):

    "midia": {"bandeira": "mz", "legenda": "MOCAMBIQUE"}
    "midia": {"bandeira": "ch", "formato": "1x1"}          # a quadrada
    "midia": {"bandeiras": ["np", "bt"], "legenda": "..."}  # lado a lado
    "midia": {"imagem": "midia/arquivo.png", "legenda": "..."}

`bandeira` e o codigo ISO de duas letras (flag-icons, licenca MIT, ja
rasterizado em ativos/bandeiras.zip). `imagem` e relativo a pasta decks/.
Sem `midia`, nada muda: o motor desenha exatamente o que desenhava.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import fontes as FT
import quizbrand as B

import io, zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
# um zip so, lido direto: 540 PNGs soltos eram 540 arquivos para copiar
# para o PC a cada atualizacao do motor
BAND_ZIP = os.path.join(AQUI, 'ativos', 'bandeiras.zip')
_ZIP = None
DECKS = os.path.join(os.path.dirname(AQUI), 'decks')
F_LEG = FT.f('Poppins-Bold.ttf')


def _zip():
    global _ZIP
    if _ZIP is None: _ZIP = zipfile.ZipFile(BAND_ZIP)
    return _ZIP


def tem_bandeira(cod, formato='4x3'):
    return f'{formato}/{cod.lower()}.png' in _zip().namelist()


def bandeira(cod, formato='4x3'):
    return Image.open(io.BytesIO(_zip().read(f'{formato}/{cod.lower()}.png'))).convert('RGBA')


def checar(q):
    """Erro de conteudo aparece antes do render, nao depois de meia hora."""
    m = q.get('midia')
    if not m: return []
    erros = []
    for cod in ([m['bandeira']] if 'bandeira' in m else []) + list(m.get('bandeiras', [])):
        if not tem_bandeira(cod, m.get('formato', '4x3')):
            erros.append(f"bandeira '{cod}' nao existe em ativos/bandeiras.zip")
    if 'imagem' in m and not os.path.exists(os.path.join(DECKS, m['imagem'])):
        erros.append(f"imagem '{m['imagem']}' nao existe em decks/")
    if not any(k in m for k in ('bandeira', 'bandeiras', 'imagem')):
        erros.append('midia sem bandeira nem imagem')
    return erros


def _foto(m):
    fmt = m.get('formato', '4x3')
    if 'imagem' in m:
        return [Image.open(os.path.join(DECKS, m['imagem'])).convert('RGBA')]
    cods = [m['bandeira']] if 'bandeira' in m else m['bandeiras']
    return [bandeira(c, fmt) for c in cods]


def polaroide(q, L, seed=0):
    """A foto pronta (RGBA, com sombra) ou None se a pergunta nao tem midia."""
    m = q.get('midia')
    if not m: return None
    s = L['s']
    rng = np.random.default_rng(seed * 977 + len(q['q']))
    fotos = _foto(m)
    # altura da imagem: generosa no 16:9 (sobra o lado direito inteiro),
    # contida no 9:16 (divide o topo com o cartao da pergunta)
    alt = int((215 if L['v'] else 230) * s)
    ims = []
    for f in fotos:
        w = int(f.width * alt / f.height)
        ims.append(f.resize((w, alt), Image.LANCZOS))
    gap = int(18 * s)
    larg = sum(i.width for i in ims) + gap * (len(ims) - 1)
    borda, rod = int(18 * s), int(66 * s) if m.get('legenda') else int(18 * s)
    W, H = larg + 2 * borda, alt + borda + rod
    # papel fotografico: branco quente, grao leve
    papel = Image.fromarray(B.folha(W, H, (250, 248, 242), rng, grao=8.0).astype(np.uint8)).convert('RGBA')
    x = borda
    for im in ims:
        # a imagem recebe uma borda fina escura: bandeira branca (Japao)
        # some no papel branco sem ela
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width - 1, im.height - 1], outline=(40, 36, 32, 90), width=max(1, int(2 * s)))
        papel.alpha_composite(im, (x, borda))
        x += im.width + gap
    if m.get('legenda'):
        d = ImageDraw.Draw(papel)
        txt = m['legenda'].upper()
        tam = int(40 * s)
        f = ImageFont.truetype(F_LEG, tam)
        while d.textlength(txt, font=f) > W - 2 * borda and tam > 16:
            tam -= 2; f = ImageFont.truetype(F_LEG, tam)
        d.text((W / 2, alt + borda + rod / 2 + int(2 * s)), txt, font=f, fill=(30, 26, 24, 255), anchor='mm')
    # fita crepe nos dois cantos de cima
    for cx in (int(W * .18), int(W * .82)):
        fita = B.fita(int(110 * s), int(34 * s), rng)
        fita = fita.rotate(float(rng.uniform(-28, 28)), expand=True, resample=Image.BICUBIC)
        papel.alpha_composite(fita, (max(0, cx - fita.width // 2), 0))
    # inclinacao propria e sombra no papel de baixo
    ang = float(rng.uniform(3, 6)) * (1 if rng.random() < .5 else -1)
    gir = papel.rotate(ang, expand=True, resample=Image.BICUBIC)
    sombra = Image.new('RGBA', (gir.width + int(40 * s), gir.height + int(40 * s)), (0, 0, 0, 0))
    a = gir.split()[3].point(lambda v: int(v * .45))
    blk = Image.new('RGBA', gir.size, (20, 14, 8, 255)); blk.putalpha(a)
    sombra.alpha_composite(blk, (int(14 * s), int(18 * s)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(9 * s))
    sombra.alpha_composite(gir, (0, 0))
    return sombra


def posicao(L, im):
    """Canto de cima-esquerda da foto. 16:9: no vazio a direita da resposta
    certa, que sobe para a primeira linha. 9:16: no topo, onde estava o
    cronometro (ele some na revelacao)."""
    if L['v']:
        # o cartao da pergunta comeca em card_y: a foto termina antes dele
        cx, cy = L['W'] // 2, L['card_y'] - im.height // 2 + int(6 * L['s'])
    else:
        # a direita da prancha: a pergunta ocupa o topo inteiro e a
        # explicacao vai ate x=1550; ali ao lado nao cobre texto nenhum
        cx, cy = int(L['W'] * .893), L['band_y0'] + int(150 * L['s'])
    return cx - im.width // 2, cy - im.height // 2


def quadro(im, u):
    """Animacao de 'tapa na mesa': chega grande e girada, assenta com um
    pequeno ressalto. u de 0 a 1 em ~0,45 s."""
    if u >= 1: return im, 0, 0, 1.0
    u = max(0.0, u)
    k = 1.45 - .45 * (1 - (1 - u) ** 3) + .06 * math.sin(math.pi * min(1, u * 1.25)) * (1 - u)
    ang = 10 * (1 - u) ** 2
    nw, nh = max(8, int(im.width * k)), max(8, int(im.height * k))
    g = im.resize((nw, nh), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC)
    return g, (im.width - nw) // 2, (im.height - nh) // 2, min(1.0, u * 2.2)
