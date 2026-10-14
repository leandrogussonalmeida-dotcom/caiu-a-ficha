#!/usr/bin/env python3
"""Fundos animados gerados por codigo. Nenhuma imagem de banco.

7 familias x 8 paletas x parametros sorteados pelo SEED. A familia e a paleta
sao escolhidas pelo SEED do video, entao a identidade visual muda a cada
video sem nunca repetir. Cada familia devolve um loop perfeito de N quadros
em baixa resolucao, que o motor amplia por quadro.
"""
import math, numpy as np

# ---------------------------------------------------------------- paletas
# (fundo_topo, fundo_base, acento_1, acento_2, tinta_cartao, cor_cartao, luz)
PALETAS = {
 'noite':    dict(top=(10,12,34),  bot=(28,16,56),  a1=(96,58,196), a2=(32,96,178),
                  card=(252,251,255), ink=(17,17,34), accent=(255,196,64), head=(230,226,250), dark=True),
 'oceano':   dict(top=(4,28,52),   bot=(8,54,78),   a1=(22,122,160), a2=(14,86,140),
                  card=(250,253,255), ink=(10,28,42), accent=(94,230,212), head=(222,244,250), dark=True),
 'brasa':    dict(top=(44,10,22),  bot=(82,20,24),  a1=(196,52,54), a2=(230,110,40),
                  card=(255,250,244), ink=(42,14,12), accent=(255,186,72), head=(255,234,214), dark=True),
 'floresta': dict(top=(8,34,28),   bot=(14,58,42),  a1=(26,124,92), a2=(96,152,54),
                  card=(250,255,250), ink=(12,34,24), accent=(244,206,84), head=(222,248,232), dark=True),
 'papel':    dict(top=(120,88,56), bot=(86,60,36),  a1=(152,116,78), a2=(106,76,48),
                  card=(250,247,238), ink=(34,30,26), accent=(206,58,48), head=(250,244,230), dark=True),
 'uva':      dict(top=(32,10,46),  bot=(62,18,74),  a1=(140,48,166), a2=(78,40,180),
                  card=(253,250,255), ink=(28,12,38), accent=(255,154,206), head=(242,226,250), dark=True),
 'grafite':  dict(top=(18,18,20),  bot=(34,34,38),  a1=(72,72,80), a2=(52,52,60),
                  card=(250,250,252), ink=(18,18,22), accent=(255,214,76), head=(238,238,242), dark=True),
 'menta':    dict(top=(6,40,44),   bot=(10,64,62),  a1=(20,138,124), a2=(44,106,150),
                  card=(250,255,254), ink=(8,36,38), accent=(255,222,110), head=(216,248,244), dark=True),
 'neon':     dict(top=(16,4,42),   bot=(58,8,74),   a1=(236,52,154), a2=(54,214,228),
                  card=(252,248,255), ink=(22,8,34), accent=(94,240,240), head=(250,226,250), dark=True),
 'ferrugem': dict(top=(34,18,14),  bot=(62,32,20),  a1=(188,92,40), a2=(132,56,36),
                  card=(254,250,242), ink=(36,20,14), accent=(248,196,96), head=(250,230,206), dark=True),
}

FAMILIAS = ['aurora', 'raios', 'grade', 'bolhas', 'ondas', 'confete', 'losangos',
            'synthwave', 'bauhaus', 'pixel', 'hud']


def escolher(seed):
    """(familia, nome_da_paleta) a partir do SEED. Opcionalmente fixados no deck."""
    rng = np.random.default_rng(seed * 2654435761 % (2 ** 31) + 17)
    return FAMILIAS[rng.integers(len(FAMILIAS))], list(PALETAS)[rng.integers(len(PALETAS))]


def _base(pal, lw, lh):
    yy = np.mgrid[0:lh, 0:lw][0].astype(np.float32) / lh
    top = np.array(pal['top'], np.float32); bot = np.array(pal['bot'], np.float32)
    return top * (1 - yy[..., None]) + bot * yy[..., None]


def render(familia, pal, W, H, nloop, seed):
    """Lista de nloop quadros uint8 (lh x lw x 3), loop perfeito."""
    rng = np.random.default_rng(seed * 97 + 5)
    lw = 480; lh = int(round(lw * H / W)); ar = W / H
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32); xx /= lw; yy /= lh
    a1 = np.array(pal['a1'], np.float32); a2 = np.array(pal['a2'], np.float32)
    frames = []

    if familia == 'aurora':
        blobs = [(a1 if i % 2 else a2, rng.uniform(.22, .40), (rng.uniform(.1, .9), rng.uniform(.1, .9)),
                  (rng.uniform(.04, .10), rng.uniform(.03, .07)), int(rng.integers(1, 3))) for i in range(4)]
        for f in range(nloop):
            ph = 2 * np.pi * f / nloop; img = _base(pal, lw, lh)
            for col, r, (cx, cy), (ax, ay), k in blobs:
                bx = cx + ax * np.sin(k * ph + r * 10); by = cy + ay * np.cos(k * ph + r * 7)
                d2 = (((xx - bx) * ar) ** 2 + (yy - by) ** 2) / (2 * r * r)
                img += col * np.exp(-d2)[..., None] * .62
            frames.append(img)

    elif familia == 'raios':
        nr = int(rng.integers(10, 17)); cx, cy = .5, rng.uniform(.30, .52)
        ang = np.arctan2(yy - cy, (xx - cx) * ar); rad = np.hypot((xx - cx) * ar, yy - cy)
        spin = rng.choice([-1, 1]) * 2 * np.pi / nr
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            w = .5 + .5 * np.sign(np.sin(nr * (ang + spin * u)))
            w = w * np.clip(1.15 - rad * .85, 0, 1)
            img += a1 * w[..., None] * .50
            halo = np.exp(-(rad / .34) ** 2)
            img += a2 * halo[..., None] * (.34 + .07 * math.sin(2 * np.pi * u))
            frames.append(img)

    elif familia == 'grade':
        n = int(rng.integers(13, 22)); tilt = rng.uniform(-.25, .25)
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            gx = np.abs(((xx * n + u + yy * tilt) % 1) - .5)
            gy = np.abs(((yy * n * lh / lw * ar + u * .6) % 1) - .5)
            line = np.exp(-(gx / .055) ** 2) + np.exp(-(gy / .055) ** 2)
            fade = np.clip(1 - np.abs(yy - .5) * 1.5, .15, 1)
            img += a1 * (line * fade * .34)[..., None]
            glow = np.exp(-(((xx - .5) * ar) ** 2 + (yy - .42) ** 2) / .20)
            img += a2 * glow[..., None] * .40
            frames.append(img)

    elif familia == 'bolhas':
        n = int(rng.integers(16, 26))
        bs = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(.022, .085),
               rng.uniform(.25, 1.0) * rng.choice([-1, 1]), rng.uniform(0, 1)) for _ in range(n)]
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            acc = np.zeros((lh, lw), np.float32)
            for bx, by, r, sp, ph in bs:
                y = (by + sp * u) % 1.25 - .12
                x = bx + .035 * np.sin(2 * np.pi * (u * 2 + ph))
                d = np.hypot((xx - x) * ar, yy - y)
                acc += np.exp(-(d / r) ** 2) * .9 + np.clip(1 - np.abs(d - r) / (r * .22), 0, 1) * .5
            img += (a1 * .6 + a2 * .4) * np.clip(acc, 0, 2.2)[..., None] * .34
            frames.append(img)

    elif familia == 'ondas':
        nb = int(rng.integers(4, 8)); amp = rng.uniform(.03, .075)
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            for i in range(nb):
                k = 1.2 + i * .55; off = (i + 1) / (nb + 1)
                band = off + amp * np.sin(2 * np.pi * (xx * k + u + i * .22))
                d = np.abs(yy - band)
                col = a1 if i % 2 else a2
                img += col * np.clip(1 - d / .085, 0, 1)[..., None] * .42
            frames.append(img)

    elif familia == 'confete':
        n = int(rng.integers(55, 95))
        ps = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(.006, .017),
               rng.uniform(.5, 1.6), rng.uniform(0, 1), rng.integers(0, 2)) for _ in range(n)]
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            m1 = np.zeros((lh, lw), np.float32); m2 = np.zeros((lh, lw), np.float32)
            for px, py, r, sp, ph, c in ps:
                y = (py + sp * u) % 1.1 - .05
                x = px + .05 * np.sin(2 * np.pi * (u * sp * 1.6 + ph))
                d = np.hypot((xx - x) * ar, yy - y)
                m = np.clip(1 - d / r, 0, 1)
                (m1 if c else m2)[...] += m
            img += a1 * np.clip(m1, 0, 1)[..., None] * .75 + a2 * np.clip(m2, 0, 1)[..., None] * .75
            glow = np.exp(-(((xx - .5) * ar) ** 2 + (yy - .45) ** 2) / .26)
            img += (a1 * .5 + a2 * .5) * glow[..., None] * .30
            frames.append(img)


    elif familia == 'synthwave':
        # horizonte com grade em perspectiva e sol listrado: o visual dos anos 80
        hor = rng.uniform(.54, .64); nx = int(rng.integers(12, 20)); nz = 16
        sun_y = hor - rng.uniform(.14, .22); sun_r = rng.uniform(.10, .15)
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            # ceu com brilho no horizonte
            glow = np.exp(-((yy - hor) / .26) ** 2)
            img += a1 * glow[..., None] * .34
            # sol com faixas horizontais
            d = np.hypot((xx - .5) * ar, (yy - sun_y) / 1.0)
            disc = (d < sun_r).astype(np.float32)
            faixa = ((yy - sun_y) * 70 + u * 2) % 2.6
            disc = disc * np.clip(faixa, 0, 1)
            mixc = a2 * (1 - np.clip((yy - sun_y + sun_r) / (2 * sun_r), 0, 1))[..., None] + \
                   a1 * np.clip((yy - sun_y + sun_r) / (2 * sun_r), 0, 1)[..., None]
            img = img * (1 - disc[..., None] * .9) + mixc * disc[..., None] * .9
            # chao em perspectiva
            below = yy > hor
            dy = np.maximum(yy - hor, 1e-4)
            persp = 1.0 / dy
            vlin = np.abs(((xx - .5) * persp * .09 * nx) % 1 - .5)
            hlin = np.abs(((persp * .30 + u * (1.0 / nz)) * nz) % 1 - .5)
            linha = (np.exp(-(vlin / .07) ** 2) + np.exp(-(hlin / .07) ** 2)) * below
            fade = np.clip(1 - (yy - hor) * 1.1, 0, 1)
            img += a2 * (linha * fade * .70)[..., None]
            img += a1 * (below * np.clip(1 - (yy - hor) * 3.0, 0, 1) * .16)[..., None]
            frames.append(img)

    elif familia == 'bauhaus':
        # formas geometricas grandes girando devagar sobre fundo chapado
        n = int(rng.integers(6, 10))
        formas = [(rng.uniform(.02, .98), rng.uniform(.02, .98), rng.uniform(.13, .30),
                   int(rng.integers(0, 3)), rng.uniform(0, 1), rng.choice([-1, 1]),
                   rng.uniform(.03, .09)) for _ in range(n)]
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            for i, (cx, cy, r, tipo, ph, sp, orb) in enumerate(formas):
                px = cx + orb * np.cos(2 * np.pi * (u * sp + ph))
                py = cy + orb * np.sin(2 * np.pi * (u * sp + ph))
                dx = (xx - px) * ar; dy = yy - py
                th = 2 * np.pi * (u * sp * .5 + ph)
                rx = dx * np.cos(th) - dy * np.sin(th); ry = dx * np.sin(th) + dy * np.cos(th)
                if tipo == 0:      m = (np.hypot(rx, ry) < r)
                elif tipo == 1:    m = (np.abs(rx) < r * .85) & (np.abs(ry) < r * .85)
                else:              m = (np.abs(rx) + np.abs(ry) < r * 1.15) & (ry > -r * .5)
                col = a1 if i % 2 else a2
                al = .40 if i % 3 == 2 else .62
                img = img * (1 - m[..., None] * al) + col * m[..., None] * al
                ctr = (np.hypot(rx, ry) < r * .30) & (i % 3 == 0)
                img = img * (1 - ctr[..., None] * .5) + np.array(pal['accent'], np.float32) * ctr[..., None] * .5
            frames.append(img)

    elif familia == 'pixel':
        # campo quantizado em blocos grandes, como arte de 8 bits
        px = int(rng.integers(16, 26)); py = max(4, int(px * lh / lw))
        k1, k2 = rng.uniform(1.2, 2.6), rng.uniform(1.2, 2.6)
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            bx = np.floor(xx * px) / px; by = np.floor(yy * py) / py
            v = (np.sin(2 * np.pi * (bx * k1 + u)) + np.sin(2 * np.pi * (by * k2 - u)) +
                 np.sin(2 * np.pi * ((bx + by) * 1.7 + u * 2))) / 3.0
            v = np.floor((v * .5 + .5) * 3) / 2.0
            img += (a1 * .5 + a2 * .5) * v[..., None] * .26
            borda = ((np.abs((xx * px) % 1 - .5) > .46) | (np.abs((yy * py) % 1 - .5) > .46))
            img *= (1 - borda[..., None] * .05)
            frames.append(img)

    elif familia == 'hud':
        # anel de instrumento com marcas e linha de varredura
        cx, cy = .5, rng.uniform(.40, .52); R = rng.uniform(.22, .32)
        nt = int(rng.integers(28, 52)); sp = rng.choice([-1, 1])
        rad = np.hypot((xx - cx) * ar, yy - cy); ang = np.arctan2(yy - cy, (xx - cx) * ar)
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            for rr, w in [(R, .009), (R * .76, .005), (R * 1.22, .004)]:
                img += a2 * np.exp(-((rad - rr) / w) ** 2)[..., None] * .50
            marcas = np.abs(((ang + sp * 2 * np.pi * u) * nt / (2 * np.pi)) % 1 - .5)
            anel = np.exp(-((rad - R * 1.10) / .022) ** 2) * np.exp(-(marcas / .16) ** 2)
            img += a1 * anel[..., None] * .80
            arco = ((ang + sp * 2 * np.pi * u) % (2 * np.pi)) < 1.5
            img += a1 * (np.exp(-((rad - R) / .012) ** 2) * arco)[..., None] * .70
            varre = np.exp(-((yy - ((u * 1.3) % 1.2 - .1)) / .016) ** 2)
            img += a2 * varre[..., None] * .34
            img += a2 * np.exp(-(rad / (R * 1.9)) ** 2)[..., None] * .14
            frames.append(img)

    else:  # losangos
        n = int(rng.integers(7, 13)); sp = rng.choice([-1, 1])
        for f in range(nloop):
            u = f / nloop; img = _base(pal, lw, lh)
            dx = ((xx * n + sp * u) % 1) - .5; dy = ((yy * n * lh / lw * ar + u * .5) % 1) - .5
            dia = np.abs(dx) + np.abs(dy)
            cell = np.clip(1 - dia / .40, 0, 1) ** 1.5
            img += a1 * cell[..., None] * .36
            ring = np.clip(1 - np.abs(dia - .46) / .07, 0, 1)
            img += a2 * ring[..., None] * .30
            frames.append(img)

    out = []
    for img in frames:
        # textura fina para o x264 não "chapar" o degradê
        img = img + rng.uniform(-1, 1, (lh, lw, 1)).astype(np.float32) * 1.2
        out.append(np.clip(img, 0, 255).astype(np.uint8))
    return out


if __name__ == '__main__':
    import sys
    from PIL import Image, ImageDraw
    alvo = sys.argv[1:] or FAMILIAS
    cols = 4; rows = (len(alvo) + cols - 1) // cols
    sheet = Image.new('RGB', (320 * cols, 180 * rows), (0, 0, 0))
    for i, fam in enumerate(alvo):
        pal = PALETAS[list(PALETAS)[i % len(PALETAS)]]
        fr = render(fam, pal, 1920, 1080, 3, 5 + i)[1]
        im = Image.fromarray(fr).resize((320, 180), Image.BICUBIC)
        ImageDraw.Draw(im).text((8, 6), fam, fill=(255, 255, 255))
        sheet.paste(im, (320 * (i % cols), 180 * (i // cols)))
    sheet.save('/tmp/fundos.png')
    print(len(alvo), 'famílias x', len(PALETAS), 'paletas =', len(alvo) * len(PALETAS), 'combinações')
