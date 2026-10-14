# -*- coding: utf-8 -*-
"""Vinheta do canal CAIU A FICHA — em colagem.

A ideia da marca: "caiu a ficha" é o instante em que a pessoa entende. Então a
vinheta é literalmente uma ficha de orelhão que cai, bate no papel, espirra
tinta — e o impacto é o que monta o nome.

A estética é colagem de revista recortada (ransom note): cada letra vem de um
papel diferente, com fonte diferente, cortada torta à tesoura, com sombra de
papel e desregistro de risografia. Nada é alinhado de propósito; a beleza da
colagem está no que está torto.

Tudo é procedural, em numpy/PIL. Não há um único recurso externo: o papel é
ruído filtrado, a borda rasgada é um passeio aleatório, o meio-tom é uma grade
de pontos, a tinta é blob gaussiano com limiar.
"""
import math
import fontes as FT
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# a mistura de fontes é o coração do visual: sans gorda, geométrica, serifada,
# e máquina de escrever. Letra vizinha nunca repete a família.
FONTES = [FT.f('InterDisplay-Black.otf'),
          FT.f('Poppins-Bold.ttf'),
          FT.f('Lora-Variable.ttf'),
          FT.f('DejaVuSerif-Bold.ttf'),
          FT.f('DejaVuSansMono-Bold.ttf')]
F_MED = FT.f('Inter-SemiBold.otf')

LATAO = (206, 164, 88)
LATAO_ESC = (124, 90, 38)
LATAO_CLA = (255, 229, 168)

# papéis da pilha de recortes: jornal, kraft, cartão vermelho, azul, amarelo,
# branco sujo. A tinta escura e a clara decidem a cor da letra em cada um.
PAPEIS = [((232, 228, 216), (26, 24, 22)),
          ((206, 176, 130), (38, 28, 18)),
          ((198,  52,  48), (255, 246, 232)),
          (( 36,  60, 128), (255, 246, 232)),
          ((238, 196,  54), (28, 24, 18)),
          ((246, 244, 238), (22, 20, 20)),
          (( 28,  26, 26), (242, 238, 228))]

T_QUEDA = .58                # instante da batida; o som e a imagem usam o mesmo
INTRO_S = 2.30
OUTRO_S = 3.40


# ------------------------------------------------------------------- papel
def _ruido(w, h, rng, escala=3.0):
    """Ruído suave: ruído branco borrado. Base de tudo que tem textura aqui."""
    n = rng.random((max(2, int(h / escala)), max(2, int(w / escala)))).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                   np.float32) / 255.0
    return n


def folha(w, h, cor, rng, grao=16.0):
    """Um pedaço de papel liso: cor base, grão fino, manchas largas e uma
    leve vinheta, para não parecer preenchimento chapado."""
    base = np.ones((h, w, 3), np.float32) * np.array(cor, np.float32)
    base += (_ruido(w, h, rng, 1.6)[..., None] - .5) * grao          # grão
    base += (_ruido(w, h, rng, 26.0)[..., None] - .5) * grao * 1.8   # manchas
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    vig = 1 - .10 * (((gx / max(1, w) - .5) * 2) ** 2 + ((gy / max(1, h) - .5) * 2) ** 2)
    return np.clip(base * vig[..., None], 0, 255)


def borda_rasgada(w, h, rng, amp=.045, lados=(1, 1, 1, 1)):
    """Máscara de um retângulo com as bordas rasgadas à mão.

    Cada lado é um passeio aleatório suavizado: é o que separa papel rasgado
    de papel cortado na guilhotina. `lados` liga o rasgo em cima/direita/
    baixo/esquerda, porque recorte de revista costuma ter dois lados retos.
    """
    S = 2
    W, H = w * S, h * S
    m = Image.new('L', (W, H), 0)
    g = ImageDraw.Draw(m)

    def perfil(n, a):
        r = np.cumsum(rng.normal(0, 1, n + 24))
        r = np.convolve(r, np.ones(9) / 9, 'same')
        r -= r.mean()
        mx = np.abs(r).max() or 1
        return (r / mx * a)[12:12 + n]

    ax, ay = W * amp, H * amp
    nx, ny = max(8, w // 3), max(8, h // 3)
    cima = perfil(nx, ay if lados[0] else ay * .12)
    dire = perfil(ny, ax if lados[1] else ax * .12)
    baix = perfil(nx, ay if lados[2] else ay * .12)
    esqu = perfil(ny, ax if lados[3] else ax * .12)

    pts = []
    for i in range(nx): pts.append((ax + (W - 2 * ax) * i / (nx - 1), ay + cima[i]))
    for i in range(ny): pts.append((W - ax + dire[i], ay + (H - 2 * ay) * i / (ny - 1)))
    for i in range(nx): pts.append((W - ax - (W - 2 * ax) * i / (nx - 1), H - ay + baix[i]))
    for i in range(ny): pts.append((ax + esqu[i], H - ay - (H - 2 * ay) * i / (ny - 1)))
    g.polygon(pts, fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    # fibra: come a borda em pontinhos, como papel de verdade rasga
    fib = (_ruido(w, h, rng, 1.3) * 255).astype(np.uint8)
    a = np.asarray(m, np.float32)
    a = np.where((a > 40) & (a < 215), np.where(np.asarray(fib, np.float32) > 118, 255, 0), a)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def recorte(w, h, cor, rng, amp=.05, lados=(1, 1, 1, 1), grao=16.0):
    """Papel + borda rasgada + a sombra que faz parecer colado por cima."""
    pap = folha(w, h, cor, rng, grao)
    msk = borda_rasgada(w, h, rng, amp, lados)
    im = Image.fromarray(pap.astype(np.uint8)).convert('RGBA')
    im.putalpha(msk)
    # lábio claro na borda: a fibra exposta do papel rasgado é mais clara
    lab = np.asarray(msk, np.float32) / 255.0
    bordo = np.clip(lab - np.asarray(msk.filter(ImageFilter.MinFilter(5)), np.float32) / 255.0, 0, 1)
    a = np.asarray(im, np.float32)
    a[..., :3] += bordo[..., None] * 46
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def com_sombra(im, desl=(7, 9), desf=7, forca=.52):
    """Sombra projetada do recorte, num canvas maior. Papel colado levanta."""
    pad = desf * 3 + max(abs(desl[0]), abs(desl[1])) + 4
    out = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sm = Image.new('RGBA', out.size, (0, 0, 0, 0))
    alpha = im.split()[3]
    sm.paste((18, 14, 12, int(255 * forca)), (pad + desl[0], pad + desl[1]), alpha)
    sm = sm.filter(ImageFilter.GaussianBlur(desf))
    out = Image.alpha_composite(out, sm)
    out.paste(im, (pad, pad), im)
    return out


def meiotom(im, passo=6, ang=22.0, forca=.40):
    """Trama de meio-tom por cima: a impressão barata de revista. O ponto
    cresce onde a imagem é escura, igual a uma rotativa de verdade."""
    a = np.asarray(im, np.float32)
    h, w = a.shape[:2]
    lum = a[..., :3].mean(2) / 255.0
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = math.radians(ang)
    u = (gx * math.cos(r) + gy * math.sin(r)) % passo
    v = (-gx * math.sin(r) + gy * math.cos(r)) % passo
    d = np.sqrt((u - passo / 2) ** 2 + (v - passo / 2) ** 2) / (passo * .62)
    ponto = np.clip((1 - lum) * 1.25 - d, 0, 1)
    a[..., :3] *= (1 - ponto[..., None] * forca)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def desregistro(im, cor=(228, 42, 120), desl=(4, -3), alpha=.30):
    """Desregistro de risografia: a chapa da segunda cor saiu fora de lugar.
    É o detalhe que faz o olho ler 'impresso de verdade'."""
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    fantasma = Image.new('RGBA', im.size, cor + (0,))
    fantasma.putalpha(im.split()[3].point(lambda p: int(p * alpha)))
    out.paste(fantasma, desl, fantasma)
    return Image.alpha_composite(out, im)


def fita(w, h, rng, cor=(226, 214, 176)):
    """Fita crepe: translúcida, com fiapos nas pontas e brilho de plástico."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pap = folha(w, h, cor, rng, 10)
    msk = Image.new('L', (w, h), 0)
    g = ImageDraw.Draw(msk)
    g.rectangle([0, 0, w, h], fill=215)
    for x in (0, w - 1):                             # pontas rasgadas
        for y in range(h):
            dent = int(abs(rng.normal(0, 1)) * w * .06)
            if x == 0: g.line([0, y, dent, y], fill=0)
            else: g.line([w - dent, y, w, y], fill=0)
    im = Image.fromarray(pap.astype(np.uint8)).convert('RGBA')
    im.putalpha(msk)
    a = np.asarray(im, np.float32)
    gy = np.linspace(0, math.pi, h, dtype=np.float32)[:, None]
    a[..., :3] += ((np.sin(gy) ** 3) * 26)[..., None]              # lombo brilhante da fita
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# -------------------------------------------------------------------- tinta
def blob(d, rng, lobulos=7, irreg=.42):
    """Mancha de tinta orgânica: raio variando por soma de senos. Nunca sai
    um círculo, que é o que denuncia desenho feito por código."""
    S = 3
    D = d * S
    im = Image.new('L', (D, D), 0)
    g = ImageDraw.Draw(im)
    fases = rng.random(4) * math.tau
    pesos = rng.random(4) * irreg
    pts = []
    for i in range(240):
        a = math.tau * i / 240
        r = D / 2 * .78
        for k in range(4):
            r *= 1 + math.sin(a * (k + 2) + fases[k]) * pesos[k] / (k + 2)
        pts.append((D / 2 + math.cos(a) * r, D / 2 + math.sin(a) * r))
    g.polygon(pts, fill=255)
    return im.filter(ImageFilter.GaussianBlur(S * .6)).resize((d, d), Image.LANCZOS)


def respingo(W, H, cx, cy, rng, cor, n=22, alcance=1.0):
    """Os pingos que saem da batida. Gotas maiores perto, menores longe, e
    cada uma com um rastro curto na direção do voo."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    for _ in range(n):
        a = rng.random() * math.tau
        dist = (rng.random() ** .55) * W * .46 * alcance
        px, py = cx + math.cos(a) * dist, cy + math.sin(a) * dist * .62
        d = max(3, int((1 - dist / (W * .5)) * W * .030 * (.4 + rng.random())))
        b = blob(d, rng, irreg=.55)
        cm = Image.new('RGBA', b.size, cor + (0,)); cm.putalpha(b)
        im.paste(cm, (int(px - d / 2), int(py - d / 2)), cm)
        if d > 6:                                     # rastro da gota
            for k in range(1, 4):
                dd = max(2, int(d * (1 - k * .26)))
                bb = blob(dd, rng, irreg=.6)
                cc = Image.new('RGBA', bb.size, cor + (0,))
                cc.putalpha(bb.point(lambda p: int(p * (.7 - k * .15))))
                qx = px - math.cos(a) * d * k * .9
                qy = py - math.sin(a) * d * k * .9 * .62
                im.paste(cc, (int(qx - dd / 2), int(qy - dd / 2)), cc)
    return im


def pingos_escorrendo(W, H, cx, cy, rng, cor, n=7, limite=None):
    """Os escorridos que descem da mancha — é o que dá o "pingando".

    Cada fio afina conforme desce (a tinta vai acabando), desacelera no fim e
    carrega uma gota mais gorda na ponta. `limite` é o y onde a tinta para,
    para o escorrido não atravessar o nome.
    """
    teto = limite if limite is not None else H
    pistas = []
    for _ in range(n):
        x = cx + rng.normal(0, W * .070)
        larg = max(3.0, abs(rng.normal(W * .0095, W * .0045)))
        comp_ = min(teto - cy, H * (.06 + rng.random() * .22))
        pistas.append((x, larg, max(W * .02, comp_), rng.random() * .26))

    def quadro(u):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        g = ImageDraw.Draw(im)
        for x, larg, comp_, atraso in pistas:
            uu = max(0.0, min(1.0, (u - atraso) / max(.12, 1 - atraso)))
            if uu <= 0: continue
            L = comp_ * (1 - (1 - uu) ** 2.2)          # desacelera ao secar
            passos = max(3, int(L / max(2, W * .004)))
            for k in range(passos):                     # fio que afina
                f0, f1 = k / passos, (k + 1) / passos
                w0 = larg * (1 - f0 * .72)
                g.rounded_rectangle([x - w0 / 2, cy + L * f0, x + w0 / 2, cy + L * f1 + 1],
                                    radius=w0 / 2, fill=cor + (255,))
            gota = larg * (.95 + .32 * math.sin(uu * 7))
            g.ellipse([x - gota / 2, cy + L - gota * .5, x + gota / 2, cy + L + gota * .9],
                      fill=cor + (255,))
        return im.filter(ImageFilter.GaussianBlur(1.0))
    return quadro


def estrela_impacto(d, cor, rng, pontas=13):
    """A explosão de quadrinho, recortada em papel: raios de comprimento
    irregular, cortados torto. Substitui o anel de luz — brilho digital é a
    única coisa que não cabe numa colagem."""
    S = 2
    D = d * S
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    pts = []
    for i in range(pontas * 2):
        a = math.tau * i / (pontas * 2) + rng.random() * .07
        r = (D / 2 * (.97 if i % 2 == 0 else .50)) * (.80 + rng.random() * .22)
        pts.append((D / 2 + math.cos(a) * r, D / 2 + math.sin(a) * r))
    g.polygon(pts, fill=cor + (255,))
    im = im.resize((d, d), Image.LANCZOS)
    # grão e lábio de papel, para não virar vetor liso
    a = np.asarray(im, np.float32)
    a[..., :3] += (_ruido(d, d, rng, 1.8)[..., None] - .5) * 22
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def confetes(W, rng, n=18):
    """Cacos de papel que saltam da batida. Cada um guarda o próprio ângulo
    inicial, velocidade e giro — assim nenhum voo se repete."""
    out = []
    for _ in range(n):
        d = int(W * (.016 + rng.random() * .030))
        cor = PAPEIS[int(rng.integers(len(PAPEIS)))][0]
        pc = recorte(d, int(d * (.5 + rng.random() * 1.0)), cor, rng, amp=.12)
        out.append(dict(im=pc,
                        ang=rng.random() * math.tau,
                        vel=W * (.26 + rng.random() * .40),
                        giro=rng.normal(0, 420),
                        sobe=W * (.10 + rng.random() * .22)))
    return out


# ------------------------------------------------------------------ a ficha
def desenhar_ficha(d_px, rng):
    """A ficha de orelhão, vista de frente. Recortada da revista como o resto:
    tem meio-tom por cima e um lábio de papel em volta."""
    S = 4
    D = d_px * S
    im = Image.new('RGBA', (D, D), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    c, r = D / 2, D / 2 - 2

    for i in range(28):                                # serrilha cunhada
        a0, a1 = math.tau * i / 28, math.tau * (i + .52) / 28
        pts = [(c + math.cos(a) * r, c + math.sin(a) * r) for a in (a0, a1)]
        pts += [(c + math.cos(a) * r * .93, c + math.sin(a) * r * .93) for a in (a1, a0)]
        g.polygon(pts, fill=LATAO_ESC + (255,))

    g.ellipse([c - r * .94, c - r * .94, c + r * .94, c + r * .94], fill=LATAO + (255,))
    g.ellipse([c - r * .86, c - r * .90, c + r * .70, c + r * .62], fill=LATAO_CLA + (95,))
    g.ellipse([c - r * .80, c - r * .80, c + r * .80, c + r * .80],
              outline=LATAO_ESC + (215,), width=int(S * 2.2))
    g.ellipse([c - r * .62, c - r * .62, c + r * .62, c + r * .62],
              outline=LATAO_CLA + (165,), width=int(S * 1.6))

    fw, fh = r * .17, r * 1.02                          # a fenda do orelhão
    g.rounded_rectangle([c - fw / 2, c - fh / 2, c + fw / 2, c + fh / 2],
                        radius=fw / 2, fill=(26, 18, 8, 255))
    try:
        f = ImageFont.truetype(FONTES[0], int(r * .44))
        for txt, dx in (('C', -r * .35), ('F', r * .35)):
            g.text((c + dx, c), txt, font=f, fill=LATAO_ESC + (238,), anchor='mm')
    except Exception:
        pass

    im = im.filter(ImageFilter.GaussianBlur(S * .5)).resize((d_px, d_px), Image.LANCZOS)
    return meiotom(im, passo=max(4, d_px // 46), ang=14, forca=.26)


def ficha_girada(base, ang):
    """A ficha girando no eixo vertical: a largura encolhe por |cos|, que é
    como um disco gira de verdade visto de frente. De canto vira uma lasca."""
    w = max(2, int(round(base.width * abs(math.cos(ang)))))
    perfil = max(3, int(base.width * .075))
    if w < perfil:
        im = Image.new('RGBA', (perfil, base.height), (0, 0, 0, 0))
        g = ImageDraw.Draw(im)
        g.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.width / 2,
                            fill=LATAO_ESC + (255,))
        g.line([im.width / 2, 2, im.width / 2, im.height - 2],
               fill=LATAO_CLA + (175,), width=max(1, im.width // 4))
        return im
    im = base.resize((w, base.height), Image.LANCZOS)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if math.cos(ang) < 0 else im


# ------------------------------------------------------------- as letras
def letras_colagem(W, seed, duas_linhas=True):
    """CAIU A / FICHA, cada letra num recorte próprio.

    Devolve dicionários com o recorte pronto e a posição de repouso relativa
    ao centro do bloco do nome. Metade das letras é tinta sobre papel; a outra
    metade é a letra vazada no papel colorido. Nenhuma fonte se repete em
    letras vizinhas, e o empilhamento das linhas usa a altura real dos
    recortes — altura nominal de fonte mente quando cada letra tem uma.
    """
    rng = np.random.default_rng(seed * 977 + 17)
    linhas = [('CAIU A', .092), ('FICHA', .170)] if duas_linhas else [('CAIU A FICHA', .073)]
    montadas = []
    ult_f, ult_p = -1, -1

    for txt, tam in linhas:
        px = int(W * tam)
        pecas, larguras = [], []
        for ch in txt:
            if ch == ' ':
                pecas.append(None); larguras.append(px * .62); continue
            fi = int(rng.integers(len(FONTES)))
            while fi == ult_f: fi = int(rng.integers(len(FONTES)))
            ult_f = fi
            pi = int(rng.integers(len(PAPEIS)))
            while pi == ult_p: pi = int(rng.integers(len(PAPEIS)))
            ult_p = pi
            cor_pap, cor_tinta = PAPEIS[pi]
            f = ImageFont.truetype(FONTES[fi], px)

            tmp = ImageDraw.Draw(Image.new('L', (4, 4)))
            bb = tmp.textbbox((0, 0), ch, font=f)
            gw, gh = bb[2] - bb[0], bb[3] - bb[1]
            marg = int(px * (.15 + rng.random() * .11))
            cw, chh = gw + marg * 2, gh + marg * 2

            # o furo mostra o que está atrás: em papel claro a letra sumiria
            vazada = sum(cor_pap) < 560 and rng.random() < .62
            lados = tuple(int(rng.random() < .62) for _ in range(4))
            pap = recorte(cw, chh, cor_pap, rng, amp=.055, lados=lados,
                          grao=18 if sum(cor_pap) > 420 else 12)
            g = ImageDraw.Draw(pap)
            if vazada:
                # a letra é o buraco: some o papel onde ela está e fica só um
                # fio de sombra na beirada, como tesoura de precisão
                mg = Image.new('L', pap.size, 0)
                ImageDraw.Draw(mg).text((marg - bb[0], marg - bb[1]), ch, font=f, fill=255)
                a = np.asarray(pap, np.float32)
                mm = np.asarray(mg, np.float32) / 255.0
                esc = np.asarray(mg.filter(ImageFilter.GaussianBlur(px * .035)), np.float32) / 255.0
                a[..., :3] *= (1 - esc[..., None] * .55)
                a[..., 3] *= (1 - mm)
                pap = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
            else:
                g.text((marg - bb[0], marg - bb[1]), ch, font=f, fill=cor_tinta + (255,))
                pap = meiotom(pap, passo=max(4, px // 22), ang=rng.random() * 60, forca=.22)

            pap = pap.rotate(rng.normal(0, 5.0), Image.BICUBIC, expand=True)
            if rng.random() < .30:
                pap = desregistro(pap, (228, 42, 120) if rng.random() < .5 else (34, 176, 212),
                                  (int(rng.integers(-5, 6)), int(rng.integers(-5, 6))), .26)
            pap = com_sombra(pap, (int(px * .05), int(px * .065)), max(4, int(px * .035)), .50)
            pecas.append(pap)
            larguras.append(gw + marg * 1.0)
        montadas.append((pecas, larguras, txt, px))

    # empilha pelas alturas reais, com uma folga que impede encavalar
    alturas = [max((p.height for p in pc if p is not None), default=0)
               for pc, _, _, _ in montadas]
    folga = W * .012
    total_h = sum(alturas) + folga * (len(alturas) - 1)
    saida, y = [], -total_h / 2

    for (pecas, larguras, txt, px), alt in zip(montadas, alturas):
        tot = sum(larguras) + (len(txt) - 1) * W * .013
        x = -tot / 2
        ymeio = y + alt / 2
        for pc, lw in zip(pecas, larguras):
            if pc is not None:
                saida.append(dict(im=pc, x=x + lw / 2,
                                  y=ymeio + rng.normal(0, W * .006),
                                  rot=float(rng.normal(0, 4.0)), w=pc.width, h=pc.height))
            x += lw + W * .013
        y += alt + folga
    return saida


# --------------------------------------------------------------- composição
def _comp(base, layer, cx, cy, alpha=1.0):
    """Cola um RGBA pelo centro, recortando o que sai da tela."""
    H, W = base.shape[:2]
    x0, y0 = int(round(cx - layer.width / 2)), int(round(cy - layer.height / 2))
    x1, y1 = x0 + layer.width, y0 + layer.height
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    a = np.asarray(layer, np.float32)[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    al = (a[:, :, 3:4] / 255.0) * alpha
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - al) + a[:, :, :3] * al


def mesa(W, H, pal, seed):
    """A mesa onde a colagem é montada: papel de fundo, uma folha grande
    colada torta, uma faixa de cor, fita crepe nos cantos e meio-tom.

    É fixa durante a vinheta inteira — o que se move é só o que cai em cima.
    """
    rng = np.random.default_rng(seed * 31 + 7)
    img = folha(W, H, (222, 215, 198), rng, 18)

    # folha grande colada torta: o palco da colagem
    gw, gh = int(W * .92), int(H * (.62 if H > W else .74))
    pg = recorte(gw, gh, (244, 241, 231), rng, amp=.028, grao=14)
    pg = pg.rotate(rng.normal(0, 1.9), Image.BICUBIC, expand=True)
    pg = com_sombra(pg, (10, 14), 14, .40)
    _comp(img, pg, W / 2, H * (.455 if H > W else .50))

    # faixa de cor atravessada, na cor de destaque do deck
    acc = tuple(int(c) for c in pal['accent'])
    fw, fh = int(W * 1.25), int(H * (.085 if H > W else .12))
    fx = recorte(fw, fh, acc, rng, amp=.07, lados=(1, 0, 1, 0), grao=10)
    fx = fx.rotate(rng.uniform(-7, -3), Image.BICUBIC, expand=True)
    _comp(img, fx, W / 2, H * (.60 if H > W else .64), .95)

    # recortes de papel soltos ao fundo, fora do miolo
    for _ in range(7):
        d = int(W * (.05 + rng.random() * .09))
        c = PAPEIS[int(rng.integers(len(PAPEIS)))][0]
        pc = recorte(d, int(d * (.4 + rng.random() * .9)), c, rng, amp=.09)
        pc = pc.rotate(rng.uniform(0, 360), Image.BICUBIC, expand=True)
        ang = rng.random() * math.tau
        _comp(img, pc, W / 2 + math.cos(ang) * W * (.38 + rng.random() * .18),
              H / 2 + math.sin(ang) * H * (.34 + rng.random() * .16), .88)

    for xy, rot in (((W * .12, H * .055), -22), ((W * .89, H * .95), 14)):
        ft = fita(int(W * .22), int(W * .055), rng).rotate(rot, Image.BICUBIC, expand=True)
        _comp(img, ft, xy[0], xy[1], .92)

    img = np.asarray(meiotom(Image.fromarray(img.astype(np.uint8)).convert('RGBA'),
                             passo=max(5, W // 230), ang=18, forca=.17), np.float32)[..., :3]
    return np.clip(img, 0, 255)


def _poeira(W, H, seed):
    """Sujeira de scanner: riscos e pontos pretos. Entra por cima de tudo."""
    rng = np.random.default_rng(seed * 7 + 2)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    for _ in range(90):
        x, y = rng.random() * W, rng.random() * H
        r = rng.random() * W * .0016 + .6
        g.ellipse([x - r, y - r, x + r, y + r], fill=(30, 26, 22, int(70 + rng.random() * 110)))
    for _ in range(5):
        x = rng.random() * W
        g.line([x, 0, x + rng.normal(0, 12), H], fill=(40, 34, 30, 26), width=1)
    return im


# ---------------------------------------------------------------- abertura
def abertura(W, H, fps, pal, seed=0):
    """A ficha cai sobre a colagem, bate, espirra tinta — e o nome é colado
    letra a letra no susto da batida. Os escorridos descem até o fim."""
    rng = np.random.default_rng(seed * 101 + 5)
    N = int(round(INTRO_S * fps))
    vert = H > W
    d = int(W * (.26 if vert else .145))
    ficha = desenhar_ficha(d, rng)
    letras = letras_colagem(W, seed, duas_linhas=vert)
    fundo = mesa(W, H, pal, seed)
    poeira = _poeira(W, H, seed)

    cx, cy = W / 2, H * (.33 if vert else .35)
    nome_y = cy + d * 1.52                 # centro do bloco do nome
    T_BAT = T_QUEDA
    tinta = (26, 22, 20)
    splat = respingo(W, H, cx, cy, rng, tinta, n=26)
    mancha = blob(int(d * 1.06), rng, irreg=.5)
    mancha_rgba = Image.new('RGBA', mancha.size, tinta + (0,)); mancha_rgba.putalpha(mancha)
    escorre = pingos_escorrendo(W, H, cx, cy + d * .50, rng, tinta, n=9,
                            limite=nome_y + d * 1.15)
    acc = tuple(int(c) for c in pal['accent'])
    estrela = estrela_impacto(int(d * 2.5), acc, rng)
    cacos = confetes(W, rng, 20)

    for i in range(N):
        t = i / fps
        img = fundo.copy()

        if t >= T_BAT:
            u = (t - T_BAT) / max(.001, INTRO_S - T_BAT)
            # a mancha de tinta cresce de estalo e fica
            mu = min(1.0, (t - T_BAT) / .16)
            esc = .25 + .75 * (1 - (1 - mu) ** 3)
            mm = mancha_rgba.resize((max(2, int(mancha.width * esc)),
                                     max(2, int(mancha.height * esc))), Image.BILINEAR)
            _comp(img, mm, cx, cy + d * .24, .90)
            _comp(img, escorre(min(1.0, (t - T_BAT) / .95)), W / 2, H / 2, .92)
            if (t - T_BAT) < .5:
                _comp(img, splat, W / 2, H / 2, min(1.0, (t - T_BAT) / .08) * (1 - (t - T_BAT) / .5) ** .4)

            # estrela de impacto: abre de estalo e some em 4 quadros
            eu = (t - T_BAT) / .20
            if eu < 1:
                es = .35 + eu * 1.0
                ei = estrela.resize((max(2, int(estrela.width * es)),
                                     max(2, int(estrela.height * es))), Image.BILINEAR)
                _comp(img, ei, cx, cy, (1 - eu) ** 1.4 * .92)

            # cacos de papel saltando, com gravidade e giro
            cu = (t - T_BAT) / .85
            if cu < 1:
                for c in cacos:
                    px = cx + math.cos(c['ang']) * c['vel'] * cu
                    py = (cy + math.sin(c['ang']) * c['vel'] * cu * .52
                          - c['sobe'] * math.sin(math.pi * min(1, cu * .9)))
                    im_ = c['im'].rotate(c['giro'] * cu, Image.BILINEAR, expand=True)
                    _comp(img, im_, px, py, min(1.0, (1 - cu) * 2.2))

        if t < T_BAT:                                  # --- a queda
            u = t / T_BAT
            y = -d * .9 + (cy + d * .14) * (u * u)
            fr = ficha_girada(ficha, u * math.pi * 5.5 + 1.1)
            for k in range(3):                         # rastro
                _comp(img, fr, cx, y - (k + 1) * d * .32 * (1 - u), .14 * (1 - u))
            _comp(img, fr, cx, y, 1.0)
        else:                                          # --- repouso, quicando
            te = t - T_BAT
            q = max(0.0, 1 - te / .22)
            ww, hh = int(d * (1 + .26 * q * q)), int(d * (1 - .32 * q * q))
            # dois quiques curtos, depois assenta
            osc = math.sin(te * 23) * math.exp(-te * 6.5) * d * .085
            fr = ficha.resize((max(2, ww), max(2, hh)), Image.LANCZOS)
            _comp(img, fr, cx, cy + d * .14 - abs(osc), 1.0)

            # --- o nome é colado, letra a letra, crescendo
            for n, g_ in enumerate(letras):
                lu = (te - .05 - n * .026) / .30
                if lu <= 0: continue
                lu = min(1.0, lu)
                e = 1 - (1 - lu) ** 4
                # passa do ponto e volta: é o gesto de bater a letra na mesa
                esc_ = .20 + 1.08 * e - .28 * math.sin(min(1, lu) * math.pi) * (1 - e)
                esc_ = max(.05, esc_)
                im_ = g_['im']
                if abs(esc_ - 1) > .02:
                    im_ = im_.resize((max(2, int(g_['w'] * esc_)), max(2, int(g_['h'] * esc_))),
                                     Image.BILINEAR)
                if lu < 1:                              # chega torta e endireita
                    im_ = im_.rotate(g_['rot'] * (1 - e) * 3.2, Image.BILINEAR, expand=True)
                _comp(img, im_, cx + g_['x'], nome_y + g_['y'], min(1.0, lu * 2.0))

        _comp(img, poeira, W / 2, H / 2)
        yield np.clip(img, 0, 255).astype(np.uint8)


# ------------------------------------------------------------ encerramento
def encerramento(W, H, fps, pal, linhas, seed=0):
    """O nome já está colado; a ficha desce e entra na fenda, levando o gesto
    de volta ao começo. As chamadas sobem embaixo, em recortes de papel."""
    rng = np.random.default_rng(seed * 211 + 9)
    N = int(round(OUTRO_S * fps))
    vert = H > W
    d = int(W * (.17 if vert else .105))
    ficha = desenhar_ficha(d, rng)
    letras = letras_colagem(W, seed, duas_linhas=vert)
    fundo = mesa(W, H, pal, seed + 3)
    poeira = _poeira(W, H, seed + 3)
    cx, cy = W / 2, H * (.34 if vert else .33)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    acc = np.array(pal['accent'], np.float32)
    fenda_y = cy + d * (3.1 if vert else 3.4)

    # as chamadas, cada uma num recorte de papel com fita
    f_l = ImageFont.truetype(F_MED, int(W * .047))
    chamadas = []
    for n, txt in enumerate(linhas):
        tmp = ImageDraw.Draw(Image.new('L', (4, 4)))
        lw = int(tmp.textlength(txt, font=f_l))
        cor_pap, cor_tinta = PAPEIS[(5, 4, 3)[n % 3]]
        pad = int(W * .035)
        pc = recorte(lw + pad * 2, int(f_l.size * 1.9), cor_pap, rng, amp=.05,
                     lados=(0, 1, 0, 1))
        ImageDraw.Draw(pc).text((pad, int(f_l.size * .35)), txt, font=f_l,
                                fill=cor_tinta + (255,))
        pc = pc.rotate(rng.normal(0, 2.1), Image.BICUBIC, expand=True)
        chamadas.append(com_sombra(pc, (5, 7), 6, .44))

    # a fenda recortada no papel: um rasgo preto, não um retângulo
    fw = int(d * .30)
    sl = Image.new('RGBA', (fw, int(d * .19)), (0, 0, 0, 0))
    ImageDraw.Draw(sl).rounded_rectangle([0, 0, sl.width - 1, sl.height - 1],
                                         radius=sl.height / 2, fill=(16, 12, 8, 236))
    sl = sl.rotate(-2.0, Image.BICUBIC, expand=True)

    for i in range(N):
        t = i / fps
        img = fundo.copy()

        for n, g_ in enumerate(letras):                # nome entra rápido
            lu = min(1.0, max(0.0, (t - n * .016) / .26))
            if lu <= 0: continue
            e = 1 - (1 - lu) ** 3
            _comp(img, g_['im'], cx + g_['x'], cy + g_['y'] - (1 - e) * d * .22, lu)

        _comp(img, sl, cx, fenda_y, min(1.0, t / .3))

        tq = 1.05
        if t > tq:                                     # a ficha entra na fenda
            u = min(1.0, (t - tq) / .90)
            y = cy + d * 1.15 + (fenda_y - cy - d * 1.15) * (u * u)
            fr = ficha_girada(ficha, u * math.pi * 3.0)
            corte = max(0, int((y + fr.height / 2) - fenda_y))
            if corte < fr.height - 2:
                if corte > 0:
                    fr = fr.crop((0, 0, fr.width, fr.height - corte)); y -= corte / 2
                _comp(img, fr, cx, y, 1.0)
            if u > .96:
                pu = (u - .96) / .04
                g_ = np.exp(-(((gx - cx) / (W * .30)) ** 2 + ((gy - fenda_y) / (H * .040)) ** 2))
                img += g_[:, :, None] * acc * (1 - pu) * 1.0

        for n, pc in enumerate(chamadas):
            lu = min(1.0, max(0.0, (t - .40 - n * .24) / .36))
            if lu <= 0: continue
            e = 1 - (1 - lu) ** 3
            _comp(img, pc, cx, fenda_y + d * (1.0 + n * .62) + (1 - e) * d * .26, lu)

        _comp(img, poeira, W / 2, H / 2)
        yield np.clip(img, 0, 255).astype(np.uint8)


# ============================================================ som da vinheta
def som_abertura(seed=0, kit=None):
    """A trilha da abertura: assobio da queda, a batida de metal no papel, e
    os tapinhas de cada letra sendo colada. Sintetizado, como todo o resto."""
    import quizaudio as A
    SR = A.SR
    rng = np.random.default_rng(seed * 57 + 3)
    n = int(INTRO_S * SR)
    out = np.zeros(n, np.float32)

    def por(x, t0, gain=1.0):
        k = int(t0 * SR)
        m = min(len(x), n - k)
        if m > 0: out[k:k + m] += x[:m].astype(np.float32) * gain

    # --- a queda: ruído descendo + nota caindo de tom, acelerando
    nq = int(T_QUEDA * SR)
    t = np.arange(nq) / SR
    u = t / T_QUEDA
    nz = A.bp(rng.standard_normal(nq), 500, 7000)
    nz = nz / (np.abs(nz).max() + 1e-9) * (u ** 2.0)
    f = 1500 * 2 ** (-2.2 * u ** 1.6)                   # despenca de tom
    sib = np.sin(2 * np.pi * np.cumsum(f) / SR) * (u ** 2.4) * .5
    por(((nz * .5 + sib) * .5).astype(np.float32), 0.0, 1.0)

    # --- a batida: metal + estouro grave + o baque do papel na mesa
    nb = int(1.3 * SR)
    tb = np.arange(nb) / SR
    met = np.zeros(nb, np.float32)
    for p, dec, amp in ((1860, .42, 1.0), (2790, .30, .55), (4310, .22, .34),
                        (5980, .16, .22), (7730, .12, .14)):
        met += (np.sin(2 * np.pi * p * tb + rng.random() * 6) *
                np.exp(-tb / dec) * amp).astype(np.float32)
    met *= 1 + .5 * np.exp(-tb / .004)                  # o estalo do ataque
    por(met / (np.abs(met).max() + 1e-9) * .52, T_QUEDA)
    por(A.kick(rng, 1.25), T_QUEDA, .95)
    baque = A.lp(rng.standard_normal(int(.3 * SR)), 420)
    baque = baque / (np.abs(baque).max() + 1e-9) * A.env(len(baque), .002, .10)
    por(baque.astype(np.float32), T_QUEDA, .55)
    por(A.clap(rng), T_QUEDA + .012, .40)

    # --- cada letra colada dá um tapinha seco, subindo de tom
    for i in range(11):
        d = int(.09 * SR)
        td = np.arange(d) / SR
        s = (np.sin(2 * np.pi * (320 + i * 46) * td) * np.exp(-td / .013) * .6
             + A.bp(rng.standard_normal(d), 1800, 8000) * np.exp(-td / .006) * .5)
        por((s / (np.abs(s).max() + 1e-9) * .22).astype(np.float32),
            T_QUEDA + .06 + i * .026)

    # --- acorde curto fechando, para a vinheta não terminar seca
    por(A.stab([57, 61, 64, 69], .9, rng), T_QUEDA + .20, .40)

    mix = np.stack([out, out], 1).astype(np.float32)
    mix, _, _ = A.master(mix, -14.0)
    return mix


def som_encerramento(seed=0):
    """Trilha do encerramento: acorde que sustenta, a ficha entrando na fenda
    e um sino curto quando ela some."""
    import quizaudio as A
    SR = A.SR
    rng = np.random.default_rng(seed * 83 + 11)
    n = int(OUTRO_S * SR)
    out = np.zeros(n, np.float32)

    def por(x, t0, gain=1.0):
        k = int(t0 * SR)
        m = min(len(x), n - k)
        if m > 0: out[k:k + m] += x[:m].astype(np.float32) * gain

    por(A.stab([50, 57, 62, 66], 2.4, rng), 0.0, .52)
    for i, m in enumerate((69, 73, 76)):
        por(A.bell(m, 1.6, rng), .10 + i * .09, .34)
    por(A.whoosh(rng, .55, up=False), 1.05, .50)        # a ficha descendo
    met = np.zeros(int(.7 * SR), np.float32)
    tb = np.arange(len(met)) / SR
    for p, dec, amp in ((2480, .22, 1.0), (3720, .15, .5), (5210, .10, .3)):
        met += (np.sin(2 * np.pi * p * tb) * np.exp(-tb / dec) * amp).astype(np.float32)
    por(met / (np.abs(met).max() + 1e-9) * .40, 1.92)   # entrou na fenda
    por(A.bell(81, 1.2, rng), 1.95, .40)

    mix = np.stack([out, out], 1).astype(np.float32)
    mix, _, _ = A.master(mix, -14.0)
    return mix
