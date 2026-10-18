#!/usr/bin/env python3
"""A tela do quiz na lingua da marca: colagem.

A vinheta do canal sempre foi colagem (papel rasgado, letra de revista,
meio-tom, desregistro de riso) e a tela do quiz era o template de quiz que
todo canal gerado por IA usa: pilula branca arredondada, bolinha A/B/C e anel
brilhando no canto. Eram dois canais colados um no outro.

Este modulo devolve EXATAMENTE as mesmas pecas que o desenho antigo
(`card`, `badge`, `pills` nos tres estados, `fact`, `ch`), nos mesmos
tamanhos, para a animacao do motor continuar funcionando sem saber da
troca. O que muda e so o que esta desenhado dentro delas.

A cor de destaque continua vindo da paleta do deck: a colagem e a gramatica
comum, e cada video tem a sua cor.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import quizbrand as B
import fontes as FT

F_PERG = FT.f('Lora-Variable.ttf')          # serifada: recorte de jornal
F_ALT  = FT.f('Inter-SemiBold.otf')
F_LET  = FT.f('DejaVuSansMono-Bold.ttf')    # mono: cara de carimbo
F_EXP  = FT.f('Inter-Medium.otf')
F_CAB  = FT.f('Poppins-Bold.ttf')

TINTA  = (26, 22, 20)
PAPEIS = [(253, 250, 243), (248, 244, 234), (255, 252, 247)]
NOTA   = (252, 236, 168)


def _quebra(probe, txt, fonte, larg):
    linhas, atual = [], ''
    for p in txt.split():
        t = (atual + ' ' + p).strip()
        if probe.textlength(t, font=fonte) <= larg: atual = t
        else:
            if atual: linhas.append(atual)
            atual = p
    if atual: linhas.append(atual)
    return linhas or ['']


def _cabe(probe, txt, caminho, tam, larg, maxlin, piso):
    """Diminui a fonte ate o texto caber em `maxlin` linhas."""
    while tam > piso:
        f = ImageFont.truetype(caminho, tam)
        if len(_quebra(probe, txt, f, larg)) <= maxlin: return f
        tam -= 2
    return ImageFont.truetype(caminho, piso)


def _carimbo_letra(L, letra, cor_fundo, cor_tinta, rng):
    """A letra num quadradinho de tinta, torto. Nao e um circulo liso."""
    s = L['s']; lado = int(L['opt_h'] * .62)
    im = Image.new('RGBA', (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, lado - 1, lado - 1], int(7 * s), fill=cor_fundo + (240,))
    f = ImageFont.truetype(F_LET, int(lado * .58))
    d.text((lado / 2, lado / 2 - int(2 * s)), letra, font=f, fill=cor_tinta + (255,), anchor='mm')
    return im.rotate(float(rng.uniform(-5, 5)), Image.BICUBIC, expand=True)


def _marcatexto(w, h, cor, rng):
    """Risco de marca-texto: traco largo, irregular, que passa do fim."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    alt = int(h * .62)
    y0 = (h - alt) // 2
    pts = []
    for k in range(24):
        x = int(w * k / 23)
        pts.append((x, y0 + rng.normal(0, h * .035)))
    for dy in range(alt):
        d.line([(x, y + dy) for x, y in pts], fill=cor + (96,), width=3)
    return im.filter(ImageFilter.GaussianBlur(1.2))


def _caneta(w, h, cor, rng, voltas=2):
    """Circulo de caneta feito a mao: duas voltas que nao fecham iguais."""
    cv = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    for v in range(voltas):
        pts = []
        for k in range(97):
            a = k / 96 * 2 * np.pi + v * .3
            rx = (w - 26) / 2 * (1 + .012 * np.sin(a * 3 + v))
            ry = (h - 22) / 2 * (1 + .035 * np.cos(a * 2 + v))
            pts.append((w / 2 + rx * np.cos(a) + rng.normal(0, 1.5),
                        h / 2 + ry * np.sin(a) + rng.normal(0, 1.5)))
        d.line(pts, fill=cor + (208,), width=max(4, w // 150), joint='curve')
    return cv


def _com_sombra_na_caixa(peca, W, H, desl=(5, 7), desf=6, forca=.46):
    """Cola a peca numa caixa de tamanho EXATO, com a sombra dentro dela.

    O motor compoe as camadas sem sombra, direto. No papel claro do palco,
    recorte branco sobre folha branca simplesmente some: e a sombra que faz
    o papel levantar. Como a caixa tem tamanho fixo (o motor conta com isso
    para posicionar), a sombra tem que caber dentro em vez de crescer o
    canvas, que e o que o com_sombra do quizbrand faz.
    """
    som = B.com_sombra(peca, desl, desf, forca)
    cx = (W - som.width) // 2
    cy = (H - som.height) // 2
    caixa = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    caixa.alpha_composite(som, (max(0, cx), max(0, cy)))
    return caixa


def carimbo_tempo(L, pal, frac, quente):
    """O cronometro como carimbo de tinta que falha, nao anel que brilha."""
    s = L['s']; cx, cy, R = L['ring']
    lado = int(R * 2 + 36 * s)
    rng = np.random.default_rng(int(frac * 1000) + (7 if quente else 3))
    im = Image.new('RGBA', (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cor = (198, 44, 44) if quente else tuple(int(c * .82) for c in pal['accent'])
    w = max(5, int(10 * s))
    caixa = [int(14 * s), int(14 * s), lado - int(14 * s), lado - int(14 * s)]
    d.arc(caixa, -90, -90 + 360 * max(.02, frac), fill=cor + (240,), width=w)
    d.ellipse([caixa[0] + w * 2, caixa[1] + w * 2, caixa[2] - w * 2, caixa[3] - w * 2],
              outline=cor + (90,), width=max(2, int(3 * s)))
    a = np.asarray(im, np.float32)
    ru = B._ruido(lado, lado, rng, 2.0)
    a[..., 3] *= np.clip(.74 + ru * 1.2, 0, 1)      # tinta falhada do carimbo
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im = im.rotate(-8, Image.BICUBIC)
    return im, (cx - lado // 2, cy - lado // 2)


def fundo(W, H, pal, seed, n=1):
    """O palco: papel, a folha grande colada torta, fita nos cantos, meio-tom.

    E FIXO. Papel nao se mexe - grao de filme se mexe, fibra de papel nao -
    e fundo parado tambem e o que o x264 sabe prever, entao o arquivo cai.
    """
    rng = np.random.default_rng(seed * 31 + 7)
    base = Image.fromarray(B.folha(W, H, (174, 163, 142), rng, 15).astype(np.uint8)).convert('RGBA')
    gw, gh = int(W * .94), int(H * .90)
    pg = B.recorte(gw, gh, (201, 190, 166), rng, amp=.022, grao=10)
    pg = B.com_sombra(pg.rotate(-0.6, Image.BICUBIC, expand=True), (10, 13), 12, .40)
    base.alpha_composite(pg, (int((W - pg.width) / 2), int((H - pg.height) / 2)))
    m = int(min(W, H) * .028)
    for x, y, a in ((m, m, -28), (W - m - 210, m - 6, 24),
                    (m, H - m - 60, 17), (W - m - 210, H - m - 66, -15)):
        ft = B.fita(int(W * .11), int(H * .029), rng).rotate(a, Image.BICUBIC, expand=True)
        base.alpha_composite(ft, (int(x), int(y)))
    img = B.meiotom(base.convert('RGB'), passo=5, ang=19.0, forca=.20)
    quadro = np.asarray(img, np.uint8)
    return [quadro] * max(1, n)


def chrome(W, H, L, pal, titulo, seed):
    """Tarja de cor com o nome do bloco, em letra de revista e desregistrada."""
    rng = np.random.default_rng(seed * 17 + 3)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s = L['s']
    f = ImageFont.truetype(F_CAB, int(38 * s))
    txt = '   '.join(titulo)
    d0 = ImageDraw.Draw(im)
    larg = int(d0.textlength(txt, font=f)) + int(56 * s)
    alt = int(64 * s)
    tar = Image.new('RGBA', (larg, alt), tuple(pal['accent']) + (236,))
    dt = ImageDraw.Draw(tar)
    dt.text((larg / 2, alt / 2 - int(2 * s)), txt, font=f,
            fill=(250, 246, 236, 255), anchor='mm')
    tar = B.desregistro(tar, (34, 176, 212), (5, -4), .30)
    tar = tar.rotate(-1.6, Image.BICUBIC, expand=True)
    x = int(W * .06) if not L['v'] else int((W - tar.width) / 2)
    im.alpha_composite(tar, (x, int(L['head_y'] - 18 * s)))
    return im


def camadas(q, n, L, pal, fonts, seed):
    """As mesmas pecas do desenho antigo, desenhadas em colagem."""
    rng = np.random.default_rng(seed * 7919 + n * 131 + 5)
    s = L['s']
    probe = ImageDraw.Draw(Image.new('RGB', (8, 8)))
    acc = tuple(pal['accent'])

    # ---- a pergunta, num recorte de jornal
    inner = L['card_w'] - int(104 * s)
    maxlin = 3 if L['v'] else 2
    fq = _cabe(probe, q['q'], F_PERG, L['f_q'], inner, maxlin, int(L['f_q'] * .58))
    linhas = _quebra(probe, q['q'], fq, inner)
    lh = int(fq.size * 1.26)
    ch = int(74 * s) + lh * len(linhas)
    card = B.recorte(L['card_w'], ch, PAPEIS[0], rng, amp=.028, grao=7).convert('RGBA')
    d = ImageDraw.Draw(card)
    y = int(34 * s)
    for ln in linhas:
        d.text((L['card_w'] / 2, y), ln, font=fq, fill=TINTA + (255,), anchor='ma')
        y += lh
    card = B.desregistro(card, acc, (4, -3), .16)
    card = _com_sombra_na_caixa(card, L['card_w'], ch, (5, 7), 6, .44)

    # ---- o numero: etiqueta colada no canto
    bs = int(88 * s)
    badge = Image.new('RGBA', (bs, bs), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0, 0, bs - 1, bs - 1], int(10 * s), fill=acc + (245,))
    fnum = ImageFont.truetype(F_CAB, int(bs * .55))
    bd.text((bs / 2, bs / 2 - int(2 * s)), str(n), font=fnum,
            fill=(252, 248, 238, 255), anchor='mm')
    badge = badge.rotate(-7, Image.BICUBIC, expand=True)

    # ---- alternativas: tiras rasgadas, cada uma torta de um jeito
    ow, oh = L['opt_w'], L['opt_h']
    letras = 'ABCDEFG'
    pills = []
    for i, opt in enumerate(q['opts']):
        fop = _cabe(probe, opt, F_ALT, L['f_o'], ow - oh - int(70 * s), 1, int(L['f_o'] * .55))
        st = []
        for modo in ('idle', 'ok', 'dim'):
            papel = PAPEIS[i % len(PAPEIS)]
            if modo == 'dim':
                papel = tuple(int(c * .62 + 150 * .38) for c in papel)
            im = Image.new('RGBA', (ow, oh), (0, 0, 0, 0))
            # a tira tem o tamanho do que esta escrito nela. Papel recortado
            # nao vem em barra de largura fixa: isso e botao de interface.
            larg = int(oh * .92 + probe.textlength(opt, font=fop) + 54 * s)
            # no vertical a tira precisa de presenca: resposta curta virava
            # um selinho perdido no meio da tela, e a revelacao sumia
            piso = .66 if L['v'] else .40
            larg = max(int(ow * piso), min(ow - int(14 * s), larg))
            tira = B.recorte(larg, oh - int(10 * s), papel, rng,
                             amp=.036, grao=8).convert('RGBA')
            tinta = TINTA if modo != 'dim' else (118, 112, 104)
            sel = _carimbo_letra(L, letras[i],
                                 TINTA if modo != 'ok' else acc,
                                 (250, 246, 236) if modo != 'ok' else TINTA, rng)
            tira.alpha_composite(sel, (int(24 * s), int((oh - sel.height) / 2) - int(4 * s)))
            dt = ImageDraw.Draw(tira)
            dt.text((int(oh * .92), (oh - int(10 * s)) / 2 - int(3 * s)), opt, font=fop,
                    fill=tinta + (255,), anchor='lm')
            if modo == 'ok':
                tira.alpha_composite(_marcatexto(tira.width, tira.height, acc, rng))
            tira = B.com_sombra(tira, (5, 6), 5, .42)
            if modo == 'ok':
                cv = _caneta(int(tira.width * .94), int(tira.height * .80),
                             (214, 36, 56), rng)
                tira.alpha_composite(cv, (int(tira.width * .03), int(tira.height * .10)))
            im.alpha_composite(tira, (0, max(0, (oh - tira.height) // 2)))
            if modo == 'dim':
                a = np.asarray(im, np.float32); a[..., 3] *= .34
                im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
            st.append(im)
        pills.append(st)

    # ---- a explicacao: papel amarelo colado com fita
    texto = (q.get('fato_curto') if L['v'] and not _reuso() and q.get('fato_curto')
             else q.get('fato', ''))
    ff = ImageFont.truetype(F_EXP, L['f_f'])
    topo = L['band_y0'] + L['opt_h'] + int(34 * s)
    disp = max(int(140 * s), L.get('fact_y1', L['band_y1']) - topo)
    tam = ff.size
    while tam > int(23 * s):
        ft = ImageFont.truetype(F_EXP, tam)
        nl = len(_quebra(probe, texto, ft, ow - int(96 * s)))
        if int(66 * s) + int(tam * 1.38) * max(1, nl) <= disp: break
        tam -= 2
    ff = ImageFont.truetype(F_EXP, tam)
    fl = _quebra(probe, texto, ff, ow - int(96 * s))
    flh = int(ff.size * 1.38)
    fhh = int(66 * s) + flh * max(1, len(fl))
    fact = Image.new('RGBA', (ow, fhh), (0, 0, 0, 0))
    nota = B.recorte(ow - int(20 * s), fhh - int(16 * s), NOTA, rng,
                     amp=.030, grao=9).convert('RGBA')
    dn = ImageDraw.Draw(nota)
    y = int(30 * s)
    for ln in fl:
        dn.text((int(44 * s), y), ln, font=ff, fill=(34, 28, 22, 255)); y += flh
    nota = B.com_sombra(nota, (5, 7), 6, .44)
    fact.alpha_composite(nota, (max(0, (ow - nota.width) // 2), 0))
    return dict(card=card, badge=badge, pills=pills, fact=fact, ch=ch)


def _reuso():
    import os
    return os.environ.get('REUSO', '') == '1'
