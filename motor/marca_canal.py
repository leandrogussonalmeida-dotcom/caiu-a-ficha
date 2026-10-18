#!/usr/bin/env python3
"""Identidade do canal no YouTube: banner, foto de perfil e marca d'agua.

Tudo sai da mesma colagem da vinheta (`quizbrand`): a mesa de papel, as
letras recortadas de revista e a ficha de orelhao. Assim o canal tem uma
cara so, do banner ao ultimo quadro do video.

    python3 marca_canal.py <pasta_saida> [seed]

Medidas do YouTube:
  banner      2560x1440; o que aparece em TODOS os aparelhos e so a faixa
              central de 1546x423 (x 507-2053, y 508-931) - nada importante
              fora dela
  foto        800x800, exibida como circulo: o desenho cabe no circulo
  marca d'agua quadrada, PNG com fundo transparente, ate 1 MB
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import quizbrand as B
import fontes as FT

ACENTO = (72, 201, 190)            # o verde-agua do canal (faixa e etiquetas)
PAL = {'accent': ACENTO}
F_TAG = FT.f('Poppins-Bold.ttf')


def _letras(larg_alvo, seed):
    """O nome em uma linha, escalado para a largura pedida."""
    ref = 2000
    pecas = B.letras_colagem(ref, seed, duas_linhas=False)
    x0 = min(p['x'] - p['w'] / 2 for p in pecas); x1 = max(p['x'] + p['w'] / 2 for p in pecas)
    y0 = min(p['y'] - p['h'] / 2 for p in pecas); y1 = max(p['y'] + p['h'] / 2 for p in pecas)
    k = larg_alvo / (x1 - x0)
    W, H = int((x1 - x0) * k) + 40, int((y1 - y0) * k) + 40
    base = np.zeros((H, W, 4), np.float32)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for p in pecas:
        pc = p['im'].rotate(p['rot'], Image.BICUBIC, expand=True)
        pc = pc.resize((max(2, int(pc.width * k)), max(2, int(pc.height * k))), Image.LANCZOS)
        cx = (p['x'] - x0) * k + 20; cy = (p['y'] - y0) * k + 20
        im.alpha_composite(pc, (int(cx - pc.width / 2), int(cy - pc.height / 2)))
    return im


def _etiqueta(txt, alt, cor_fundo=(24, 20, 18), cor_txt=(250, 246, 236), seed=0):
    """Tira de fita preta com letra de maquina: o subtitulo."""
    rng = np.random.default_rng(seed + 3)
    f = ImageFont.truetype(F_TAG, int(alt * .52))
    d0 = ImageDraw.Draw(Image.new('L', (4, 4)))
    w = int(d0.textlength(txt, font=f) + alt * 1.2)
    pap = B.recorte(w, alt, cor_fundo, rng, amp=.05, lados=(0, 1, 0, 1), grao=8)
    g = ImageDraw.Draw(pap)
    g.text((w / 2, alt / 2 + alt * .03), txt, font=f, fill=cor_txt + (255,), anchor='mm')
    return B.com_sombra(pap.rotate(-1.2, Image.BICUBIC, expand=True), (6, 8), 6, .45)


def _comp(base, im, cx, cy):
    B._comp(base, im, cx, cy)


def banner(seed=11):
    W, H = 2560, 1440
    img = B.mesa(W, H, PAL, seed)
    # area segura: 1546x423 no centro (x 507-2053, y 508-931)
    sx0, sx1, sy0, sy1 = 507, 2053, 508, 931
    rng = np.random.default_rng(seed)
    ficha = B.desenhar_ficha(380, rng)
    ficha = B.com_sombra(ficha.rotate(-12, Image.BICUBIC, expand=True), (12, 16), 12, .5)
    nome = _letras_2(seed, alt=330)
    tag = _etiqueta('QUIZ  ·  CURIOSIDADES  ·  A RESPOSTA QUE NINGUÉM TE CONTOU', 56, seed=seed)
    # o grupo (ficha + nome) centralizado na area segura
    bloco = max(nome.width, tag.width)
    larg = ficha.width + 30 + bloco
    x0 = (sx0 + sx1) / 2 - larg / 2
    _comp(img, ficha, x0 + ficha.width / 2, (sy0 + sy1) / 2)
    bx = x0 + ficha.width + 30 + bloco / 2
    _comp(img, nome, bx, sy0 + 8 + nome.height / 2)
    _comp(img, tag, bx, sy1 - 34)
    img = np.asarray(Image.alpha_composite(Image.fromarray(img.astype(np.uint8)).convert('RGBA'),
                                           B._poeira(W, H, seed)), np.uint8)[..., :3]
    return Image.fromarray(img)


def _letras_2(seed, alt):
    """CAIU A / FICHA em duas linhas, como na vinheta, escalado pela altura."""
    ref = 1400
    pecas = B.letras_colagem(ref, seed, duas_linhas=True)
    x0 = min(p['x'] - p['w'] / 2 for p in pecas); x1 = max(p['x'] + p['w'] / 2 for p in pecas)
    y0 = min(p['y'] - p['h'] / 2 for p in pecas); y1 = max(p['y'] + p['h'] / 2 for p in pecas)
    k = alt / (y1 - y0)
    im = Image.new('RGBA', (int((x1 - x0) * k) + 40, int((y1 - y0) * k) + 40), (0, 0, 0, 0))
    for p in pecas:
        pc = p['im'].rotate(p['rot'], Image.BICUBIC, expand=True)
        pc = pc.resize((max(2, int(pc.width * k)), max(2, int(pc.height * k))), Image.LANCZOS)
        cx = (p['x'] - x0) * k + 20; cy = (p['y'] - y0) * k + 20
        im.alpha_composite(pc, (int(cx - pc.width / 2), int(cy - pc.height / 2)))
    return im


def foto(seed=11):
    """A ficha sozinha, grande, no papel com a faixa verde. No circulo do
    YouTube ela le em qualquer tamanho - inclusive nos 24 px de comentario."""
    W = 800
    rng = np.random.default_rng(seed + 5)
    img = B.folha(W, W, (240, 234, 220), rng, 16)
    fx = B.recorte(int(W * 1.4), int(W * .30), ACENTO, rng, amp=.07, lados=(1, 0, 1, 0), grao=10)
    fx = fx.rotate(-14, Image.BICUBIC, expand=True)
    B._comp(img, fx, W / 2, W * .55, .95)
    ficha = B.desenhar_ficha(int(W * .70), rng)
    ficha = B.com_sombra(ficha.rotate(-10, Image.BICUBIC, expand=True), (10, 14), 12, .5)
    B._comp(img, ficha, W / 2, W / 2)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def marca_dagua(lado=300, seed=11):
    """So a ficha, fundo transparente. Com um anel claro em volta: o YouTube
    poe a marca sobre qualquer imagem, e latao em cena escura sumia."""
    rng = np.random.default_rng(seed + 9)
    f = B.desenhar_ficha(int(lado * .86), rng)
    im = Image.new('RGBA', (lado, lado), (0, 0, 0, 0))
    a = Image.new('L', (lado, lado), 0)
    g = ImageDraw.Draw(a)
    m = lado * .05
    g.ellipse([m, m, lado - m, lado - m], fill=235)
    anel = Image.new('RGBA', (lado, lado), (250, 246, 236, 0)); anel.putalpha(a)
    im.alpha_composite(anel)
    im.alpha_composite(f, ((lado - f.width) // 2, (lado - f.height) // 2))
    return im


if __name__ == '__main__':
    out = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 11
    os.makedirs(out, exist_ok=True)
    banner(seed).save(os.path.join(out, 'banner-2560x1440.png'))
    foto(seed).save(os.path.join(out, 'foto-perfil-800x800.png'))
    marca_dagua(300, seed).save(os.path.join(out, 'marca-dagua-300x300.png'))
    marca_dagua(150, seed).save(os.path.join(out, 'marca-dagua-150x150.png'))
    print('ok', out)
