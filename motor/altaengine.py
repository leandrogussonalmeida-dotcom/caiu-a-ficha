#!/usr/bin/env python3
"""Motor em alta resolução — o segundo idioma visual do canal.

O `pixelengine` desenha em 180x320 e amplia: é 8 bits de verdade, e por isso
mesmo não serve para tudo. 280 peças no mesmo bloco serrilhado viram uma
peça só repetida 280 vezes, que é exatamente o que a política de conteúdo
inautêntico procura.

Aqui é o oposto: 1080x1920 com tipografia de verdade, linha fina, curva lisa.
O truque do antialias é **desenhar grande e reduzir** — PIL não suaviza
formas, mas uma redução suaviza tudo de uma vez. A redução é `reduce(SS)`,
não `resize(..., LANCZOS)`: com superamostragem inteira os dois fazem a
mesma conta (a média do bloco SSxSS), mas o LANCZOS ainda por cima soma um
halo de ringing e custa 18x mais — 137 ms contra 7,5 ms por quadro. Foi a
diferença entre 3 fps e 60 fps.

Grão e vinheta também são operações do PIL em uint8, não contas em float32:
um `blend` custa 3 ms onde a soma em numpy custava 80 ms.

Um ESTILO reúne cor, fonte e textura. Trocar de estilo troca a cara do vídeo
inteiro sem tocar no simulador.
"""
import math, os, subprocess
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

FPS = 30
SR = 48000
LARG, ALT = 1080, 1920
SS = 2                      # fator de superamostragem

F_TITULO = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
F_FORTE = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
F_TEXTO = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
F_MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
F_SERIF = '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'
F_GEO = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'


class Estilo:
    """Cor, fonte e textura de um vídeo. É o que faz dois vídeos do mesmo
    simulador não parecerem o mesmo vídeo."""

    def __init__(self, nome, fundo, tinta, suave, acento, acento2, linha,
                 fonte_num=F_TITULO, fonte_rot=F_MONO, fonte_txt=F_TEXTO,
                 grade=None, grao=0.0, vinheta=0.0, maiuscula=True):
        self.nome = nome
        self.fundo, self.tinta, self.suave = fundo, tinta, suave
        self.acento, self.acento2, self.linha = acento, acento2, linha
        self.fonte_num, self.fonte_rot, self.fonte_txt = fonte_num, fonte_rot, fonte_txt
        self.grade, self.grao, self.vinheta = grade, grao, vinheta
        self.maiuscula = maiuscula


ESTILOS = {
    # planta técnica: azul de cópia heliográfica, linha fina, cota com seta
    'planta': Estilo('planta', (12, 32, 62), (236, 244, 255), (142, 178, 222),
                     (255, 209, 102), (255, 107, 107), (86, 128, 184),
                     fonte_num=F_MONO, grade=(36, 22), grao=.012),
    # editorial suíço: papel quente, tipo gordo, pouca cor, muito ar
    'editorial': Estilo('editorial', (244, 241, 234), (24, 22, 20), (122, 116, 108),
                        (214, 64, 44), (36, 84, 168), (24, 22, 20),
                        fonte_num=F_TITULO, fonte_rot=F_MONO, grao=.018),
    # bauhaus: fundo creme, primárias chapadas, geométrico
    'bauhaus': Estilo('bauhaus', (233, 226, 212), (22, 20, 18), (120, 112, 100),
                      (206, 48, 38), (18, 62, 150), (22, 20, 18),
                      fonte_num=F_GEO, fonte_rot=F_GEO, fonte_txt=F_GEO, grao=.02),
    # noturno: quase preto, uma cor só, brilho suave
    'noturno': Estilo('noturno', (10, 11, 16), (240, 242, 248), (120, 128, 148),
                      (96, 224, 196), (255, 122, 162), (44, 50, 66),
                      fonte_num=F_TITULO, grao=.01, vinheta=.35),
    # jornal: papel velho, tinta preta, serifa
    'jornal': Estilo('jornal', (232, 226, 210), (28, 26, 24), (108, 102, 94),
                     (160, 36, 28), (52, 70, 96), (28, 26, 24),
                     fonte_num=F_SERIF, fonte_rot=F_MONO, fonte_txt=F_SERIF,
                     grao=.035, maiuscula=False),
}


class Quadro:
    """Uma tela em alta, desenhada grande e reduzida no fim."""

    def __init__(self, est, larg=LARG, alt=ALT):
        self.est = est
        self.w, self.h = larg, alt
        self._f = {}
        self._base = None
        self.im = Image.new('RGB', (larg * SS, alt * SS), est.fundo)
        self.d = ImageDraw.Draw(self.im, 'RGBA')
        self._pos()

    def s(self, v): return v * SS

    def _pos(self):
        """Tabelas que não mudam de quadro: ruído do grão e máscara da
        vinheta. Calculadas uma vez por vídeo, não 1800 vezes."""
        e = self.est
        self._ruido = None
        if e.grao:
            rng = np.random.default_rng(7)
            self._ruido = [Image.fromarray(
                np.repeat(rng.integers(0, 256, (self.h, self.w, 1), dtype=np.uint8), 3, 2))
                for _ in range(4)]
        self._vin = None
        if e.vinheta:
            gy, gx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
            r = ((gx / self.w - .5) * 1.25) ** 2 + ((gy / self.h - .5) * 1.1) ** 2
            m = (np.clip(1 - e.vinheta * r * 2.2, 0, 1) * 255).astype(np.uint8)
            self._vin = Image.fromarray(np.repeat(m[..., None], 3, 2))

    def limpar(self):
        """Começa o quadro seguinte. O fundo (cor e grade) é desenhado uma
        única vez e daí em diante copiado: a grade da planta custava 24 ms
        por quadro só para sair igual."""
        if self._base is None:
            self.fundo_base()
            self._base = self.im.copy()
        else:
            self.im.paste(self._base)
        return self

    def fonte(self, caminho, tam):
        c = (caminho, int(tam * SS))
        if c not in self._f: self._f[c] = ImageFont.truetype(caminho, int(tam * SS))
        return self._f[c]

    # ---------------------------------------------------------- primitivas
    def fundo_base(self):
        e = self.est
        self.d.rectangle([0, 0, self.w * SS, self.h * SS], fill=e.fundo)
        if e.grade:
            # papel milimetrado de verdade tem duas grades: a fina, que você
            # mal vê, e a grossa de 5 em 5, que é a que dá a leitura. Com uma
            # só o fundo ou some ou vira xadrez.
            passo, forca = e.grade
            fina, grossa = e.linha + (forca,), e.linha + (min(255, forca * 3),)
            for i, x in enumerate(range(0, self.w + 1, passo)):
                self.d.line([self.s(x), 0, self.s(x), self.h * SS],
                            fill=grossa if i % 5 == 0 else fina, width=SS)
            for i, y in enumerate(range(0, self.h + 1, passo)):
                self.d.line([0, self.s(y), self.w * SS, self.s(y)],
                            fill=grossa if i % 5 == 0 else fina, width=SS)

    def ret(self, x, y, w, h, cor, raio=0, borda=None, esp=2):
        box = [self.s(x), self.s(y), self.s(x + w), self.s(y + h)]
        if raio:
            self.d.rounded_rectangle(box, radius=self.s(raio), fill=cor,
                                     outline=borda, width=int(self.s(esp)))
        else:
            self.d.rectangle(box, fill=cor, outline=borda, width=int(self.s(esp)))

    def circulo(self, cx, cy, r, cor=None, borda=None, esp=2):
        self.d.ellipse([self.s(cx - r), self.s(cy - r), self.s(cx + r), self.s(cy + r)],
                       fill=cor, outline=borda, width=int(self.s(esp)))

    def linha(self, x0, y0, x1, y1, cor, esp=2, traco=None):
        if not traco:
            self.d.line([self.s(x0), self.s(y0), self.s(x1), self.s(y1)],
                        fill=cor, width=int(self.s(esp)))
            return
        n = math.hypot(x1 - x0, y1 - y0)
        if n < 1: return
        ux, uy = (x1 - x0) / n, (y1 - y0) / n
        p, on = 0.0, True
        while p < n:
            q = min(n, p + (traco[0] if on else traco[1]))
            if on:
                self.d.line([self.s(x0 + ux * p), self.s(y0 + uy * p),
                             self.s(x0 + ux * q), self.s(y0 + uy * q)],
                            fill=cor, width=int(self.s(esp)))
            p, on = q, not on

    def seta(self, x, y, ang, tam, cor):
        p = [(x, y),
             (x - math.cos(ang - .36) * tam, y - math.sin(ang - .36) * tam),
             (x - math.cos(ang + .36) * tam, y - math.sin(ang + .36) * tam)]
        self.d.polygon([(self.s(a), self.s(b)) for a, b in p], fill=cor)

    def cota(self, x, y0, y1, texto, cor=None, lado=1, tam=22):
        """Linha de cota com setas nas pontas e a medida no meio — o gesto
        que faz um desenho parecer um desenho técnico, e não um infográfico."""
        cor = cor or self.est.suave
        self.linha(x, y0, x, y1, cor, 1.6)
        self.seta(x, y0, math.pi / 2, 12, cor)
        self.seta(x, y1, -math.pi / 2, 12, cor)
        if texto and tam:
            self.texto(texto, x + lado * 16, (y0 + y1) / 2, cor, tam,
                       fonte=self.est.fonte_rot, anc='lm' if lado > 0 else 'rm')

    def texto(self, txt, x, y, cor, tam, fonte=None, anc='la', espaco=0):
        if self.est.maiuscula and fonte != self.est.fonte_txt:
            txt = txt.upper()
        f = self.fonte(fonte or self.est.fonte_txt, tam)
        if espaco:
            larg = self.largura(txt, tam, fonte, espaco)
            px = self.s(x) - (larg * SS / 2 if anc[0] == 'm' else
                              (larg * SS if anc[0] == 'r' else 0))
            for ch in txt:
                self.d.text((px, self.s(y)), ch, font=f, fill=cor, anchor='l' + anc[1])
                px += self.d.textlength(ch, font=f) + self.s(espaco)
            return
        self.d.text((self.s(x), self.s(y)), txt, font=f, fill=cor, anchor=anc)

    def largura(self, txt, tam, fonte=None, espaco=0):
        if self.est.maiuscula and fonte != self.est.fonte_txt: txt = txt.upper()
        f = self.fonte(fonte or self.est.fonte_txt, tam)
        return (self.d.textlength(txt, font=f) + self.s(espaco) * len(txt)) / SS

    def ajustar(self, txt, x, y, cor, tam, larg_max, **kw):
        while tam > 9 and self.largura(txt, tam, kw.get('fonte')) > larg_max:
            tam -= 1
        self.texto(txt, x, y, cor, tam, **kw)
        return tam

    # ------------------------------------------------------------- saida
    def render(self, i=0):
        """Devolve o quadro pronto em bytes rgb24. `i` é o número do quadro:
        é ele que troca a folha de grão, para o grão não congelar na tela."""
        im = self.im.reduce(SS) if SS > 1 else self.im
        if self._ruido is not None:
            im = Image.blend(im, self._ruido[i & 3], self.est.grao)
        if self._vin is not None:
            im = ImageChops.multiply(im, self._vin)
        return im.tobytes()


def gravar(gerador, total_s, wav, saida, crf=19):
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{LARG}x{ALT}', '-r', str(FPS), '-i', '-']
    if wav: args += ['-i', wav, '-map', '0:v', '-map', '1:a', '-c:a', 'aac',
                     '-b:a', '256k', '-ar', '48000', '-shortest']
    args += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
             '-pix_fmt', 'yuv420p', '-g', str(FPS * 2), '-movflags', '+faststart', saida]
    p = subprocess.Popen(args, stdin=subprocess.PIPE)
    n = int(round(total_s * FPS))
    for i in range(n):
        q = gerador(i / FPS, i)
        p.stdin.write(q if isinstance(q, bytes) else q.tobytes())
    p.stdin.close(); p.wait()
    return n
