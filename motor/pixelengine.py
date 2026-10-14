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
# CONVENÇÃO DOS ÍNDICES — toda paleta obedece, senão os simuladores mentem.
# Eles desenham por índice, não por cor, então o significado de cada posição
# tem que ser o mesmo em todas. Antes disso, "11" era branco numa paleta e
# marrom escuro em outra, e o mesmo número saía ilegível sem aviso.
#
#  0      fundo mais escuro
#  1  2   faixas de fundo
#  3  4   traços e separadores
#  5  6   tom médio
#  7  8   tom claro
#  9      destaque principal
# 10      destaque secundário
# 11      BRANCO, sempre
# 12      acento frio (barra de progresso)
# 13 14   apoio escuro
# 15      alerta
PALETAS = {
    'espaco':   ['#07060f', '#140f2b', '#241a4d', '#3d2a73', '#4b3a86', '#6b46c1',
                 '#a78bfa', '#c4b5fd', '#f0abfc', '#fbbf24', '#f97316', '#ffffff',
                 '#22d3ee', '#1e293b', '#64748b', '#ef4444'],
    'asfalto':  ['#0a0a0c', '#17171c', '#26262e', '#3a3a46', '#4a4a58', '#5a5a6b',
                 '#8b8b9c', '#c9c9d6', '#e6e6ee', '#fbbf24', '#f97316', '#ffffff',
                 '#06b6d4', '#2a2a33', '#7f1d1d', '#ef4444'],
    'neon':     ['#0d0221', '#190535', '#2d0b57', '#4a0e7a', '#5d1192', '#7209b7',
                 '#b5179e', '#f72585', '#ff6ec7', '#06ffa5', '#fee440', '#ffffff',
                 '#4cc9f0', '#390099', '#3f37c9', '#fb8500'],
    'papelao':  ['#1a1410', '#2e2318', '#4a3728', '#6b4f38', '#7d5d41', '#8f6b47',
                 '#b08968', '#d4b595', '#f0e0c8', '#c1440e', '#e07a3f', '#ffffff',
                 '#40916c', '#2d2219', '#457b9d', '#e63946'],
    'gelo':     ['#02121f', '#06283d', '#0b3d5c', '#13607f', '#1673a0', '#1b86a8',
                 '#2bb3cc', '#6fd9e8', '#b3f0f7', '#f59e0b', '#fbbf24', '#ffffff',
                 '#60a5fa', '#0a2436', '#334155', '#ef4444'],
    'floresta': ['#07130d', '#0d2818', '#14452a', '#1b6b3f', '#1f8049', '#249456',
                 '#35c46f', '#7ee787', '#c6f6d5', '#f59e0b', '#fef3c7', '#ffffff',
                 '#4cc9f0', '#0a1f14', '#475569', '#ef4444'],
    'brasa':    ['#140603', '#2b0c05', '#4a150a', '#6e2010', '#852a12', '#9c3415',
                 '#c75420', '#ef7b2e', '#ffa94d', '#ffd79a', '#ffe066', '#ffffff',
                 '#60a5fa', '#431407', '#a16207', '#dc2626'],
    'sangria':  ['#10040c', '#250919', '#420f2b', '#63153f', '#78194a', '#8c1c55',
                 '#b52a6d', '#d94f8c', '#f287b3', '#ffc9dd', '#fbbf24', '#ffffff',
                 '#22d3ee', '#1e1b4b', '#5b21b6', '#f43f5e'],
    'mostarda': ['#120e04', '#241d08', '#3d3010', '#5c481a', '#6d5620', '#7f6425',
                 '#a68432', '#cfa844', '#e8c76e', '#f7e3a8', '#fffbe8', '#ffffff',
                 '#2563eb', '#1a1406', '#57534e', '#ef4444'],
    'carvao':   ['#08090a', '#111315', '#1d2024', '#2c3036', '#373c43', '#424850',
                 '#5e6670', '#858e99', '#b4bcc6', '#f97316', '#fb923c', '#ffffff',
                 '#38bdf8', '#161a1e', '#1e3a8a', '#facc15'],
    'uva':      ['#0b0614', '#180d2b', '#271247', '#3b1a69', '#471e7c', '#53248f',
                 '#7035b5', '#9354d6', '#b87ef0', '#fbbf24', '#4ade80', '#ffffff',
                 '#22d3ee', '#120a20', '#312e81', '#f43f5e'],
    'menta':    ['#02110d', '#05241c', '#083a2d', '#0d5543', '#106550', '#13765c',
                 '#1c9a79', '#2fc39b', '#6fe0c0', '#fbbf24', '#f9a8d4', '#ffffff',
                 '#60a5fa', '#041a14', '#475569', '#f43f5e'],
    # paleta fixa da vinheta: a marca sai igual em todo vídeo, qualquer que
    # seja a paleta do conteúdo. Aqui 4..8 são o latão da ficha.
    'marca':    ['#0a0710', '#17102a', '#2a1b4d', '#000000', '#7c5a1e', '#b08436',
                 '#d6aa5c', '#ffe2a0', '#fff6dc', '#f72585', '#4cc9f0', '#ffffff',
                 '#fee440', '#3a2a0e', '#5b4a8a', '#ff8c42'],
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
        self._cache = {}

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

    def _mascara(self, txt, tam):
        """Máscara apertada do texto, em cache.

        A versão ingênua alocava uma imagem do tamanho da TELA a cada chamada;
        com cinco textos por quadro isso sozinho derrubava o render pela
        metade. Aqui a máscara tem o tamanho das letras e é calculada uma vez
        por (texto, corpo) — o mesmo rótulo em 1.800 quadros custa um.
        """
        ch = (txt, tam)
        m = self._cache.get(ch)
        if m is None:
            f = self._fonte(tam)
            d0 = ImageDraw.Draw(Image.new('L', (4, 4)))
            d0.fontmode = '1'
            cx0, cy0, cx1, cy1 = d0.textbbox((0, 0), txt, font=f)
            w, h = max(1, cx1 - cx0 + 2), max(1, cy1 - cy0 + 2)
            im = Image.new('L', (w, h), 0)
            d = ImageDraw.Draw(im)
            d.fontmode = '1'
            d.text((-cx0 + 1, -cy0 + 1), txt, font=f, fill=255)
            m = (np.asarray(im) > 127, cx0, cy0)
            if len(self._cache) > 400: self._cache.clear()
            self._cache[ch] = m
        return m

    def _blit(self, m, x, y, cor):
        h, w = m.shape
        x, y = int(round(x)), int(round(y))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0: return
        sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
        self.buf[y0:y1, x0:x1][sub] = cor

    def texto(self, txt, x, y, cor, tam=10, centro=False, sombra=None):
        """Texto sem antialias. `centro` True ou 'c' centraliza, 'd' alinha à
        direita, falso à esquerda. (True não é chave de dicionário: tratar
        antes, senão cai no alinhamento à esquerda.)"""
        if not txt: return
        m, bx, by = self._mascara(txt, tam)
        h, w = m.shape
        if centro is True or centro == 'c': x -= w / 2
        elif centro == 'd': x -= w
        y = y + by - 1
        if sombra is not None: self._blit(m, x + 1, y + 1, sombra)
        self._blit(m, x, y, cor)

    def largura_texto(self, txt, tam):
        return self._mascara(txt, tam)[0].shape[1]

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
