#!/usr/bin/env python3
"""Motor de vídeo em pixel art, sincronizado ao som por construção.

A aposta central: **desenhar pequeno e ampliar por vizinho mais próximo**.
Um quadro 9:16 de 1080x1920 tem 2,07 milhões de pixels; o mesmo quadro em
180x320 tem 57,6 mil — 36 vezes menos conta. Ampliado 6x com NEAREST, cada
pixel vira um bloco de 6x6 perfeitamente quadrado. Isso dá as duas coisas ao
mesmo tempo: o visual 8-bit de verdade (não um filtro por cima) e velocidade
que torna 80 vídeos possível.

A segunda aposta: **nós geramos a música, então sabemos a batida**. Ninguém
precisa detectar beat em áudio: o compasso é `60/bpm` e o tempo de cada
batida é exato na amostra. A sincronia não é aproximada, é construída.
"""
import json, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- troca de trilha -------------------------------------------------------
# MUDO=1 entrega o vídeo sem faixa de áudio, para casar com som da plataforma.
# BPM=<n> força a grade de batida: o visual passa a travar no andamento de uma
# música de fora, em vez de na nossa. Sem isso, trocar a trilha quebra a
# sincronia, que é justamente o que diferencia este canal.
MUDO = os.environ.get('MUDO', '') == '1'
BPM_FORA = float(os.environ.get('BPM', 0)) or None

FPS = 30
SR = 48000
ESCALA = 6
LARG, ALT = 180, 320                 # 1080x1920 dividido por 6
LARG_H, ALT_H = 320, 180             # 1920x1080 dividido por 6

# Fonte de bitmap: TTF renderizada SEM antialias. Em 8 px o antialias vira
# borrão cinza e mata o visual; com fontmode='1' cada pixel é ligado ou
# desligado, que é como fonte de console sempre foi.
F_PIX = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'


# =============================================================== paletas
# Paleta fechada, como um console de verdade. Desenhar com índice em vez de
# RGB garante coerência: nenhuma cor "quase igual" entra sem querer.
PALETAS = {
    'espaco':   ['#07060f', '#140f2b', '#241a4d', '#3d2a73', '#6b46c1', '#a78bfa',
                 '#f0abfc', '#fde68a', '#fbbf24', '#f97316', '#ef4444', '#ffffff',
                 '#22d3ee', '#0ea5e9', '#64748b', '#1e293b'],
    'asfalto':  ['#0a0a0c', '#17171c', '#26262e', '#3a3a46', '#5a5a6b', '#8b8b9c',
                 '#c9c9d6', '#ffffff', '#fbbf24', '#f97316', '#ef4444', '#22c55e',
                 '#06b6d4', '#a855f7', '#fde047', '#7f1d1d'],
    'neon':     ['#0d0221', '#190535', '#2d0b57', '#4a0e7a', '#7209b7', '#b5179e',
                 '#f72585', '#ff6ec7', '#4cc9f0', '#4895ef', '#3f37c9', '#ffffff',
                 '#06ffa5', '#fee440', '#fb8500', '#390099'],
    'papelao':  ['#1a1410', '#2e2318', '#4a3728', '#6b4f38', '#8f6b47', '#b08968',
                 '#d4b595', '#f0e0c8', '#fffaf0', '#c1440e', '#e07a3f', '#2d6a4f',
                 '#40916c', '#1d3557', '#457b9d', '#e63946'],
    'gelo':     ['#02121f', '#06283d', '#0b3d5c', '#13607f', '#1b86a8', '#2bb3cc',
                 '#6fd9e8', '#b3f0f7', '#ffffff', '#e0f7ff', '#f59e0b', '#ef4444',
                 '#1e3a5f', '#334155', '#94a3b8', '#fbbf24'],
    'floresta': ['#07130d', '#0d2818', '#14452a', '#1b6b3f', '#249456', '#35c46f',
                 '#7ee787', '#c6f6d5', '#fef3c7', '#f59e0b', '#b45309', '#78350f',
                 '#ffffff', '#1e293b', '#475569', '#ef4444'],
}


def paleta_rgb(nome):
    p = PALETAS[nome]
    return np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in p], np.uint8)


# =============================================================== a tela
class Tela:
    """Framebuffer indexado. Cada posição guarda o índice da cor na paleta,
    não a cor — é o que um console de 8 bits fazia, e é o que impede a
    paleta de escapar."""

    def __init__(self, larg=LARG, alt=ALT, paleta='espaco'):
        self.w, self.h = larg, alt
        self.pal = paleta
        self.rgb = paleta_rgb(paleta)
        self.buf = np.zeros((alt, larg), np.uint8)
        self._fontes = {}

    def limpar(self, cor=0):
        self.buf[:] = cor

    def px(self, x, y, cor):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h: self.buf[y, x] = cor

    def ret(self, x, y, w, h, cor):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        if x1 > x0 and y1 > y0: self.buf[y0:y1, x0:x1] = cor

    def ret_vazado(self, x, y, w, h, cor):
        self.ret(x, y, w, 1, cor); self.ret(x, y + h - 1, w, 1, cor)
        self.ret(x, y, 1, h, cor); self.ret(x + w - 1, y, 1, h, cor)

    def disco(self, cx, cy, r, cor):
        """Círculo preenchido. Em pixel art o círculo é a máscara de
        distância, sem suavizar a borda — a escada faz parte do visual."""
        r = max(0.5, r)
        x0, x1 = max(0, int(cx - r - 1)), min(self.w, int(cx + r + 2))
        y0, y1 = max(0, int(cy - r - 1)), min(self.h, int(cy + r + 2))
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        m = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        self.buf[y0:y1, x0:x1][m] = cor

    def anel(self, cx, cy, r, cor, esp=1.0):
        r = max(0.5, r)
        x0, x1 = max(0, int(cx - r - esp - 1)), min(self.w, int(cx + r + esp + 2))
        y0, y1 = max(0, int(cy - r - esp - 1)), min(self.h, int(cy + r + esp + 2))
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        self.buf[y0:y1, x0:x1][np.abs(d - r) <= esp] = cor

    def linha(self, x0, y0, x1, y1, cor):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            u = i / max(1, n - 1)
            self.px(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, cor)

    def _fonte(self, tam):
        if tam not in self._fontes:
            self._fontes[tam] = ImageFont.truetype(F_PIX, tam)
        return self._fontes[tam]

    def texto(self, txt, x, y, cor, tam=10, centro=False, sombra=None):
        # centro: True/'c' centraliza, 'd' alinha à direita
        """Texto sem antialias. Desenha numa máscara 1-bit e carimba o
        índice de cor — assim o texto nunca traz cor fora da paleta."""
        f = self._fonte(tam)
        im = Image.new('L', (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = '1'                              # sem antialias
        # centro True ou 'c' centraliza, 'd' alinha à direita, falso à esquerda.
        # (True não é chave do dicionário: tratar antes, senão cai no 'la'.)
        anc = 'ma' if centro is True else {'c': 'ma', 'd': 'ra'}.get(centro, 'la')
        d.text((x, y), txt, font=f, fill=255, anchor=anc)
        m = np.asarray(im) > 127
        if sombra is not None:
            ms = np.zeros_like(m)
            ms[1:, 1:] = m[:-1, :-1]
            self.buf[ms & ~m] = sombra
        self.buf[m] = cor

    def largura_texto(self, txt, tam):
        d = ImageDraw.Draw(Image.new('L', (4, 4)))
        d.fontmode = '1'
        return d.textlength(txt, font=self._fonte(tam))

    def texto_ajustado(self, txt, x, y, cor, tam, larg_max, **kw):
        """Encolhe a fonte até o texto caber na largura dada. Em 180 px de
        tela, nome comprido ou vaza ou é cortado no meio da palavra; aqui ele
        só fica menor, que é o único dos três que não incomoda."""
        while tam > 5 and self.largura_texto(txt, tam) > larg_max:
            tam -= 1
        self.texto(txt, x, y, cor, tam=tam, **kw)
        return tam

    def quadro(self):
        """Converte índices em RGB e amplia por vizinho mais próximo."""
        return np.repeat(np.repeat(self.rgb[self.buf], ESCALA, 0), ESCALA, 1)


# =============================================================== a batida
class Batida:
    """A grade de tempo do vídeo. Como a trilha é nossa, a batida é
    aritmética, não estimativa.

    `BPM=<n>` no ambiente manda em tudo: o visual trava no andamento de uma
    música de fora e a nossa trilha é gerada no mesmo compasso (ou descartada
    com `MUDO=1`). É o que permite trocar o som sem perder a sincronia.
    """

    def __init__(self, bpm, compassos=4):
        if BPM_FORA: bpm = BPM_FORA
        self.bpm = bpm
        self.spb = 60.0 / bpm              # segundos por batida
        self.bar = compassos * self.spb

    def n(self, t):
        """Qual batida está tocando em t."""
        return int(t / self.spb)

    def t_de(self, n):
        """Instante exato da batida n."""
        return n * self.spb

    def pulso(self, t, decaimento=.16):
        """0 a 1: 1 no instante da batida, caindo até a próxima. É o que faz
        qualquer coisa 'dançar' — escala, brilho, tremor."""
        d = (t % self.spb) / self.spb
        return math.exp(-d * self.spb / decaimento)

    def pulso_compasso(self, t, decaimento=.30):
        d = (t % self.bar) / self.bar
        return math.exp(-d * self.bar / decaimento)


# =============================================================== saída
def exportar_batidas(bat, total_s, caminho):
    """Grava a grade de batida em JSON. Com isso o vídeo mudo pode ser
    alinhado a qualquer música em qualquer editor: os instantes estão todos
    aqui, ao milésimo."""
    tempos = [round(bat.t_de(n), 4) for n in range(int(total_s / bat.spb) + 1)]
    json.dump(dict(bpm=round(bat.bpm, 3), spb=round(bat.spb, 6),
                   compasso_s=round(bat.bar, 6), total_s=round(total_s, 3),
                   batidas=tempos, fps=FPS,
                   quadros=[round(t * FPS, 2) for t in tempos]),
              open(caminho, 'w'), indent=1)
    return len(tempos)


def gravar(gerador, total_s, wav, saida, larg=LARG, alt=ALT, crf=18):
    """Despeja os quadros ampliados direto no ffmpeg. O gerador entrega a
    Tela já desenhada; a ampliação acontece aqui, uma vez por quadro."""
    W, H = larg * ESCALA, alt * ESCALA
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo',
            '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    if wav and not MUDO:
        args += ['-i', wav, '-map', '0:v', '-map', '1:a',
                 '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest']
    args += ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
             '-pix_fmt', 'yuv420p', '-g', str(FPS * 2),
             # sem suavizar na escala: o bloco tem que continuar quadrado
             '-sws_flags', 'neighbor', '-movflags', '+faststart', saida]
    p = subprocess.Popen(args, stdin=subprocess.PIPE)
    n = int(round(total_s * FPS))
    for i in range(n):
        tela = gerador(i / FPS, i)
        p.stdin.write(tela.quadro().tobytes())
    p.stdin.close(); p.wait()
    return n
