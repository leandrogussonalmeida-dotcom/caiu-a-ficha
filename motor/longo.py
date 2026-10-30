#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — o vídeo longo explicativo (16:9, sem voz).

Tela de 480x270 ampliada 4x por vizinho mais próximo = 1920x1080. O dobro
de pixels do 9:16 dos Shorts: é o que deixa desenhar um motor por dentro com
detalhe (parafuso, camisa d'água, anel do pistão) sem perder o bloco.

  palco     y 0..208: a imagem
  legenda   y 212..268: faixa escura com até 2 linhas na fonte 2x (37 letras);
            *palavra* sai em amarelo; a linha "digita" em 0,25 s
  trilha    um `ritmo_musica.compor` por capítulo, mesma semente e tônica
            (a música do vídeo inteiro tem a mesma progressão), baixa
  efeitos   sons do que se vê (válvula, faísca, explosão, escape), ditos
            pelo episódio como eventos com instante
  troca     entre capítulos a tela fecha em blocos 8x8 e abre (0,25 s)

O episódio fornece CAPITULOS, LEGENDAS e uma classe por capítulo com
`desenhar(tela, t, ctx)`; `renderizar_episodio` faz o resto.
"""
import math, os, subprocess, json
import numpy as np
import soundfile as sf
import pixelengine as PX
import pixelfonte as PF
import quizaudio as QA
import ritmo_musica as M
import ritmo_acabamento as AC
import ritmo_base as RB

W, H, ESC, FPS = 480, 270, 4, 30
SR = 48000
PALCO_H = 208
LEG_Y = 212

PAL = 'oficina'
PX.PALETAS[PAL] = [
    '#0b0d17', '#141a2b', '#1f2840', '#2e3a57', '#44506e', '#5d6a88', '#7c89a6', '#a3aec4',
    '#d2d9e6', '#ffcf4a', '#4fd8ff', '#ffffff', '#ff8a3d', '#2a1c12', '#c7832b', '#ff4d5e',
    '#fff1a8', '#ffb13b', '#e0532b', '#8f2a1e', '#3c7dff', '#9fe8ff', '#6d6a73', '#4a4650',
    '#1d4a40', '#3f9c84', '#b07a3a', '#e8e0cc', '#9a5cd6', '#57d17a', '#07080e', '#ff5fa8']
# nomes dos índices (convenção da tela baixa + extras da oficina)
FUNDO, FUNDO2, FUNDO3, TRACO, ACO0, ACO1, ACO2, ACO3, ACO4 = 0, 1, 2, 3, 4, 5, 6, 7, 8
AMARELO, CIANO, BRANCO, LARANJA, OLEO0, OLEO1, VERMELHO = 9, 10, 11, 12, 13, 14, 15
CHAMA0, CHAMA1, CHAMA2, BRASA = 16, 17, 18, 19
MISTURA, MISTURA2, GAS, GAS2 = 20, 21, 22, 23
AGUA0, AGUA1, LATAO, CERAMICA, ROXO, VERDE, PRETO, ROSA = 24, 25, 26, 27, 28, 29, 30, 31

BAYER8 = (np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
                    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
                    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) + .5) / 64


def ease(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def suave(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


# =================================================================== desenho
def dither(tela, x, y, w, h, c1, c2, fase=0):
    """Retângulo em xadrez de duas cores: o degradê de 8 bits."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(tela.w, int(x + w)), min(tela.h, int(y + h))
    if x1 <= x0 or y1 <= y0: return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    tela.buf[y0:y1, x0:x1] = np.where((xx + yy + fase) % 2 == 0, c1, c2)


def poligono(tela, pts, cor):
    """Preenche um polígono (lista de (x, y) em pixels de tela) por varredura."""
    ys = [p[1] for p in pts]
    y0, y1 = max(0, int(math.floor(min(ys)))), min(tela.h - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + .5
        xs = []
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a, b = int(round(xs[k])), int(round(xs[k + 1]))
            if b > a: tela.ret(a, y, b - a, 1, cor)


def linha_grossa(tela, x0, y0, x1, y1, esp, cor):
    """Barra de espessura `esp` entre dois pontos (biela, alavanca)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * esp / 2, dx / L * esp / 2
    poligono(tela, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], cor)


def texto_marcado(tela, txt, x, y, tam, cor=BRANCO, cor_marca=AMARELO, n_letras=None, contorno=PRETO, centro=False):
    """Texto em que *palavra* sai na cor de marca. `n_letras` corta o texto
    (efeito de digitação). Devolve a largura."""
    pedacos, marca, cur = [], False, ''
    for ch in txt:
        if ch == '*':
            if cur: pedacos.append((cur, marca)); cur = ''
            marca = not marca
        else:
            cur += ch
    if cur: pedacos.append((cur, marca))
    total = sum(tela.largura_texto(p, tam) for p, _ in pedacos) + \
        PF.ESPACO * PF.escala_de(tam) * (len(pedacos) - 1)
    xx = x - total // 2 if centro else x
    resto = n_letras if n_letras is not None else 10 ** 9
    for p, m in pedacos:
        if resto <= 0: break
        vis = p[:resto]
        resto -= len(p)
        if vis.strip():
            tela.texto(vis, xx, y, cor_marca if m else cor, tam=tam, contorno=contorno)
        xx += tela.largura_texto(p, tam) + PF.ESPACO * PF.escala_de(tam)
    return total


def painel(tela, x, y, w, h, borda=TRACO, fundo=PRETO, luz=FUNDO3):
    RB.painel(tela, x, y, w, h, borda=borda, fundo=fundo, luz=luz, sombra=FUNDO)


# =================================================================== legenda
class Legendas:
    def __init__(self, itens):
        self.itens = sorted(itens)

    def desenhar(self, tela, t):
        """Faixa de legenda. Sempre desenhada (mesmo vazia), para a imagem
        não pular de tamanho quando a legenda some."""
        tela.ret(0, LEG_Y - 2, W, H - LEG_Y + 2, PRETO)
        tela.ret(0, LEG_Y - 2, W, 1, TRACO)
        tela.ret(0, LEG_Y - 1, W, 1, FUNDO2)
        for a, b, l1, l2, _ in self.itens:
            if a <= t < b:
                u = t - a
                n = int(u / .25 * 40)                     # 0,25 s para "digitar" a linha
                y1 = LEG_Y + 10 if l2 else LEG_Y + 20
                texto_marcado(tela, l1, W // 2, y1, 17, n_letras=n, centro=True)
                if l2:
                    n2 = int(max(0, u - .12) / .25 * 40)
                    texto_marcado(tela, l2, W // 2, y1 + 22, 17, n_letras=n2, centro=True)


# =================================================================== trilha
class Trilha:
    """Música do vídeo inteiro, montada capítulo a capítulo. Mesma semente e
    tônica em todos: muda o gênero e o arranjo, a música continua a mesma."""

    def __init__(self, capitulos, seed=2026, raiz=45):
        self.caps = []
        t = 0.0
        partes = []
        eventos = []
        secoes = []
        for i, c in enumerate(capitulos):
            sec = [dict(gen=c['gen'], bars=c['bars'], papel=c['papel'], **({'bpm': c['bpm']} if 'bpm' in c else {}))]
            F = M.compor(sec, seed=seed, raiz=raiz, cauda=1.5, suave=True)
            bpm = float(c.get('bpm', M.GENEROS[c['gen']]['bpm']))
            dur = c['bars'] * 4 * 60.0 / bpm
            self.caps.append(dict(c, t0=t, t1=t + dur, dur=dur, bpm=bpm, i=i))
            partes.append((t, F.audio))
            for e in F.eventos:
                d = dict(e); d['t'] = e['t'] + t
                if d['tipo'] == 'fim': continue
                eventos.append(d)
            for s in F.secoes:
                secoes.append(dict(s, t0=s['t0'] + t, t1=s['t1'] + t, i=len(secoes)))
            t += dur
        self.total = t
        n = int((t + 2) * SR)
        mix = np.zeros((n, 2), np.float32)
        k = int(.04 * SR)
        for t0, a in partes:
            a = a.copy()
            a[:k] *= np.linspace(0, 1, k)[:, None]          # sem estalo na emenda
            i0 = int(round(t0 * SR))
            j = min(n, i0 + len(a))
            mix[i0:j] += a[:j - i0]
        self.audio = mix
        eventos.sort(key=lambda e: e['t'])
        self.F = type('F', (), {})()
        self.F.eventos = eventos
        self.F.secoes = secoes
        self.L = RB.Linha(self.F)

    def cap(self, t):
        for c in reversed(self.caps):
            if t >= c['t0'] - 1e-9: return c
        return self.caps[0]


# =================================================================== efeitos
class Efeitos:
    """Banco de efeitos sonoros (sintetizados, nada gravado)."""

    def __init__(self, total, seed=7):
        self.buf = np.zeros((int((total + 3) * SR), 2), np.float32)
        self.rng = np.random.default_rng(seed)

    def put(self, s, t, ganho=1.0, pan=0.0):
        if s.ndim == 1: s = s[:, None] * np.array([[math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)]], np.float32) * 1.41
        i = int(round(t * SR)); j = min(len(self.buf), i + len(s))
        if j > i >= 0: self.buf[i:j] += s[:j - i] * ganho

    # ----------------------------------------------------- timbres
    def _env(self, n, a, d):
        tt = np.arange(n) / SR
        return (np.minimum(1, tt / max(a, 1e-4)) * np.exp(-tt / d)).astype(np.float32)

    def chiado(self, dur, f_lo, f_hi, ataque=.05):
        """Ar entrando/saindo: ruído com filtro passa-banda que abre e fecha."""
        n = max(8, int(dur * SR))
        x = self.rng.standard_normal(n).astype(np.float32)
        x = QA.bp(x, f_lo, f_hi)
        tt = np.linspace(0, 1, n)
        env = np.sin(np.pi * np.clip(tt, 0, 1)) ** .8 * np.minimum(1, tt * dur / max(ataque, 1e-3))
        return (x * env / (np.abs(x).max() + 1e-9)).astype(np.float32)

    def clique(self, f=4200, dur=.018):
        n = int(dur * SR)
        x = QA.hp(self.rng.standard_normal(n).astype(np.float32), f) * self._env(n, .0005, dur / 4)
        return x / (np.abs(x).max() + 1e-9)

    def faisca(self):
        n = int(.06 * SR)
        x = QA.hp(self.rng.standard_normal(n).astype(np.float32), 5000) * self._env(n, .0003, .012)
        crep = (self.rng.random(n) < .02).astype(np.float32) * self._env(n, .0, .03)
        y = x + crep * .8
        return y / (np.abs(y).max() + 1e-9)

    def explosao(self, lento=1.0):
        """Queima: baque grave + ruído abafado. `lento` > 1 estica no tempo
        (câmera lenta), descendo o tom junto, como num slow motion."""
        dur = .35 * lento
        n = int(dur * SR)
        tt = np.arange(n) / SR
        f0 = 90 / lento ** .5
        baque = np.sin(2 * np.pi * (f0 * tt + 40 / lento * (1 - np.exp(-tt / (.04 * lento))))) * self._env(n, .002, .12 * lento)
        rui = QA.lp(self.rng.standard_normal(n).astype(np.float32), 900 / lento ** .5) * self._env(n, .003, .09 * lento)
        y = baque * .9 + rui * 1.6
        return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)

    def pulso(self):
        """Um disparo curto (motor em rotação): vira ronco quando se repete rápido."""
        n = int(.05 * SR)
        tt = np.arange(n) / SR
        y = np.sin(2 * np.pi * 70 * tt) * self._env(n, .001, .012) + \
            QA.lp(self.rng.standard_normal(n).astype(np.float32), 1500) * self._env(n, .0005, .006) * .7
        return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)

    def sino(self, m, dur=.9):
        f = 440 * 2 ** ((m - 69) / 12)
        n = int(dur * SR)
        tt = np.arange(n) / SR
        y = (np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * 2 * f * tt) + .12 * np.sin(2 * np.pi * 3.01 * f * tt)) \
            * self._env(n, .003, dur / 3.5)
        return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)

    def blip(self, m, dur=.12):
        f = 440 * 2 ** ((m - 69) / 12)
        n = int(dur * SR)
        tt = np.arange(n) / SR
        y = np.where((tt * f) % 1 < .5, 1.0, -1.0) * self._env(n, .002, dur / 3)
        return QA.lp(y.astype(np.float32), 3000)


# =================================================================== acabamento
class Acabamento16:
    """Brilho em degraus, vinheta pontilhada e a troca de capítulo em blocos."""

    def __init__(self, trilha, brilho=.42):
        self.T, self.brilho = trilha, brilho
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - PALCO_H / 2) / (PALCO_H / 2)) ** 2) / np.sqrt(2)
        bay = np.tile(AC.BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]
        nivel = np.floor(np.clip((r - .55) / .45, 0, 1) ** 1.5 * 3 + bay)
        v = (1 - .22 * nivel / 3).astype(np.float32)
        v[LEG_Y - 2:] = 1.0                                  # legenda sem vinheta
        self.vin = v[..., None]
        by, bx = np.mgrid[0:H, 0:W]
        self.bloco = BAYER8[(by // 8) % 8, (bx // 8) % 8].astype(np.float32)
        self.trocas = [c['t0'] for c in trilha.caps[1:]]

    def aplicar(self, tela, t, brilho=None, sem_troca=False):
        x = tela.rgb[tela.buf].astype(np.float32) / 255.0
        b = self.brilho if brilho is None else brilho
        if b > 0:
            palco = x[:LEG_Y - 2]
            x[:LEG_Y - 2] = AC.iluminar(palco, b, .62, 1.3, 4.5, 1.0)
        x = x * self.vin
        out = (np.clip(x, 0, 1) * 255).astype(np.uint8)
        if not sem_troca and self.trocas:
            d = min(self.trocas, key=lambda a: abs(a - t))
            u = (t - d) / .25
            if -1 < u < 1:
                cobre = 1 - abs(u)
                m = (self.bloco < cobre * 1.02) & (np.arange(H)[:, None] < LEG_Y - 2)
                out[m] = tela.rgb[PRETO]
        return out


def limitar(x, teto, A=480):
    """Limitador com antecipação de 10 ms: o ganho desce antes do pico e
    volta suave (sem distorcer), até nenhuma amostra passar do teto."""
    import scipy.signal as sg
    from scipy.ndimage import minimum_filter1d
    req = np.minimum(1.0, teto / (np.abs(x).max(1) + 1e-12)).astype(np.float32)
    if req.min() >= 1.0: return x
    gmin = minimum_filter1d(req, 2 * A + 1)
    win = np.hanning(2 * A + 3)[1:-1]; win /= win.sum()
    gs = np.minimum(sg.oaconvolve(np.pad(gmin, A + 1, mode='edge'), win.astype(np.float32), 'same')[A + 1:-(A + 1)], 1.0)
    return (x * gs[:, None]).astype(np.float32)


# =================================================================== render
def preparar(ep):
    """Trilha, efeitos e cenas do episódio (o que o vídeo longo e os cortes
    verticais compartilham)."""
    trilha = Trilha(ep.CAPITULOS, seed=ep.SEED, raiz=ep.RAIZ)
    fx = Efeitos(trilha.total)
    cenas = {}
    for c in trilha.caps:
        cenas[c['id']] = ep.CENAS[c['id']](c, trilha, fx)
    for c in trilha.caps:                      # cada cena põe os seus sons
        cenas[c['id']].sons(fx)
    return trilha, fx, cenas


def mixar(ep, trilha, fx):
    """Trilha baixa + efeitos, sem master (cada formato masteriza o seu)."""
    n = int(trilha.total * SR)
    return (trilha.audio[:n] * QA.g(ep.GANHO_MUSICA) + fx.buf[:n] * QA.g(ep.GANHO_EFEITOS)).astype(np.float32)


def renderizar_episodio(ep, saida, crf=18, so=None, quadros_amostra=None):
    """`ep` é o módulo do episódio. `so` = lista de ids de capítulo (teste).
    `quadros_amostra` = lista de tempos -> devolve PNGs em vez de vídeo."""
    trilha, fx, cenas = preparar(ep)
    tela = PX.Tela(W, H, paleta=PAL)
    acab = Acabamento16(trilha)
    legs = {c['id']: Legendas([(a + c['t0'], b + c['t0'], l1, l2, f) for a, b, l1, l2, f in ep.LEGENDAS.get(c['id'], [])])
            for c in trilha.caps}

    def quadro(t):
        c = trilha.cap(t)
        cena = cenas[c['id']]
        tela.buf[:] = FUNDO
        cena.desenhar(tela, t - c['t0'], t)
        if getattr(cena, 'legenda', True):
            legs[c['id']].desenhar(tela, t)
        baixo = acab.aplicar(tela, t, brilho=getattr(cena, 'brilho', None))
        if hasattr(cena, 'pos'):                # cena que entrega RGB pronto (vinheta)
            baixo = cena.pos(baixo, t - c['t0'])
        return baixo

    if quadros_amostra is not None:
        return [quadro(t) for t in quadros_amostra], trilha

    # ---- áudio: trilha baixa + efeitos, master a -16 LUFS
    mix = mixar(ep, trilha, fx)
    k = int(1.5 * SR)
    mix[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
    mix, lufs, tp = QA.master(mix.astype(np.float32), ep.LUFS)
    mix = limitar(mix, QA.g(-2.2))           # folga: o AAC sobe o pico ~0,5 dB (reprovou em -0,7)
    lufs = round(float(QA.lufs(mix)), 2)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    wav = saida.replace('.mp4', '.wav')
    sf.write(wav, mix, SR, subtype='PCM_16')

    t_ini, t_fim = 0.0, trilha.total
    if so:
        cs = [c for c in trilha.caps if c['id'] in so]
        t_ini, t_fim = cs[0]['t0'], cs[-1]['t1']
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{W * ESC}x{H * ESC}', '-r', str(FPS), '-i', '-',
            '-ss', f'{t_ini:.3f}', '-t', f'{t_fim - t_ini:.3f}', '-i', wav,
            '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
            '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation', '-crf', str(crf),
            '-pix_fmt', 'yuv420p', '-g', str(FPS * 2), '-movflags', '+faststart', '-shortest', saida]
    p = subprocess.Popen(args, stdin=subprocess.PIPE)
    n0, n1 = int(round(t_ini * FPS)), int(round(t_fim * FPS))
    for i in range(n0, n1):
        b = quadro(i / FPS)
        p.stdin.write(np.ascontiguousarray(np.repeat(np.repeat(b, ESC, 0), ESC, 1)).tobytes())
    p.stdin.close(); p.wait()
    os.remove(wav)
    rel = dict(arquivo=saida, total=round(trilha.total, 2), quadros=n1 - n0, lufs=lufs, tp=tp,
               capitulos=[(c['id'], round(c['t0'], 2), round(c['t1'], 2)) for c in trilha.caps])
    json.dump(rel, open(saida.replace('.mp4', '.json'), 'w'), indent=1)
    return rel
