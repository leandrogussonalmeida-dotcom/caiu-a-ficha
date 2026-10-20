#!/usr/bin/env python3
"""RITMO PIXEL (série NO RITMO) — a moldura comum dos Shorts.

Cada cena desenha o mundo. Esta base põe por cima o que é do canal:

  gancho      frase de desafio já no quadro 0 (o primeiro quadro é a capa)
  placa       nome do gênero e o BPM entrando a cada troca de seção
  hud         BPM atual e uma luz que pisca em cada bumbo
  cartão      no último trecho: pedido de inscrição com o botão apertado
              na batida e uma pergunta para os comentários
  vinheta     RITMO PIXEL (`ritmo_marca`): o pixel que quica e vira o nome
  acabamento  luz, vinheta, flash e transição (`ritmo_acabamento`)

Tudo que se mexe na moldura também obedece aos eventos da faixa.

Áreas de segurança do Short (em pixels da tela baixa, 180x320): o topo até
~24 tem a barra do app; a lateral direita a partir de ~150 tem os botões;
o rodapé a partir de ~250 tem título e legenda. Texto importante mora
entre y 34 e 240, x 10 e 148.
"""
import bisect, json, math, os, subprocess, sys
import numpy as np
import soundfile as sf
import pixelengine as PX
import ritmo_marca as PM
import ritmo_acabamento as AC
import quizaudio as QA
import ritmo_musica as M
import ritmo_paletas  # noqa: registra as paletas das cenas

FPS = 30
W, H = PX.LARG, PX.ALT
SAFE_Y0, SAFE_Y1 = 34, 240
SAFE_X0, SAFE_X1 = 10, 148


# =================================================================== eventos
class Linha:
    """Consulta rápida dos eventos da faixa por tipo e instante."""

    def __init__(self, F):
        self.F = F
        self.por = {}
        for e in F.eventos:
            self.por.setdefault(e['tipo'], []).append(e)
        self.ts = {k: [e['t'] for e in v] for k, v in self.por.items()}
        # aliases úteis: "costas" é a caixa ou a palma que marca o tempo forte
        cost = sorted(self.por.get('snare', []) + self.por.get('clap', []), key=lambda e: e['t'])
        cost = [e for e in cost if not e.get('ghost') and e.get('vel', 1) >= .6]
        self.por['costas'] = cost
        self.ts['costas'] = [e['t'] for e in cost]
        hat = [e for e in self.por.get('hat', []) if e.get('vel', 1) >= .4]
        self.por['hatf'] = hat
        self.ts['hatf'] = [e['t'] for e in hat]

    def lista(self, tipo):
        return self.por.get(tipo, [])

    def idx(self, tipo, t):
        """Índice do último evento <= t (ou -1)."""
        return bisect.bisect_right(self.ts.get(tipo, []), t + 1e-6) - 1

    def ultimo(self, tipo, t):
        i = self.idx(tipo, t)
        return self.por[tipo][i] if i >= 0 else None

    def proximo(self, tipo, t):
        ts = self.ts.get(tipo, [])
        i = bisect.bisect_right(ts, t + 1e-6)
        return self.por[tipo][i] if i < len(ts) else None

    def desde(self, tipo, t):
        e = self.ultimo(tipo, t)
        return t - e['t'] if e else 1e9

    def ate(self, tipo, t):
        e = self.proximo(tipo, t)
        return e['t'] - t if e else 1e9

    def env(self, tipo, t, dec=.12):
        d = self.desde(tipo, t)
        return math.exp(-d / dec) if d < 50 else 0.0

    def conta(self, tipo, t):
        return self.idx(tipo, t) + 1

    def secao(self, t):
        for s in reversed(self.F.secoes):
            if t >= s['t0'] - 1e-6: return s
        return self.F.secoes[0]

    def entre(self, tipo, t0, t1):
        ts = self.ts.get(tipo, [])
        a = bisect.bisect_left(ts, t0); b = bisect.bisect_right(ts, t1)
        return self.por.get(tipo, [])[a:b]


# =================================================================== sprites
class Sprite:
    """Sprite em texto: cada caractere é uma chave do mapa de cores; '.' é
    transparente. Compilado uma vez em índice de paleta."""

    def __init__(self, linhas, mapa):
        h = len(linhas); w = max(len(l) for l in linhas)
        a = np.full((h, w), 255, np.uint8)
        for y, l in enumerate(linhas):
            for x, c in enumerate(l):
                if c != '.' and c != ' ': a[y, x] = mapa[c]
        self.a = a
        self.w, self.h = w, h

    def por(self, tela, x, y, flip=False, cor=None, esc=1):
        a = self.a[:, ::-1] if flip else self.a
        if esc != 1: a = np.repeat(np.repeat(a, esc, 0), esc, 1)
        h, w = a.shape
        x, y = int(round(x)), int(round(y))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(tela.w, x + w), min(tela.h, y + h)
        if x1 <= x0 or y1 <= y0: return
        sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
        m = sub != 255
        if cor is not None:
            tela.buf[y0:y1, x0:x1][m] = cor
        else:
            tela.buf[y0:y1, x0:x1][m] = sub[m]


def ease(u): u = min(max(u, 0.0), 1.0); return 1 - (1 - u) ** 3
def back(u):
    u = min(max(u, 0.0), 1.0); c = 1.9
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


# =================================================================== moldura
def painel(tela, x, y, w, h, borda=9, fundo=0, luz=None, sombra=0):
    """Painel de HUD de jogo: sombra de 1 px, borda com cantos arredondados
    (o pixel do canto fica de fora) e um filete de luz por dentro do topo."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    if sombra is not None:
        tela.ret(x + 2, y + h, w - 2, 1, sombra); tela.ret(x + w, y + 2, 1, h - 2, sombra)
        tela.ret(x + 1, y + h, 1, 1, sombra)
    tela.ret(x + 1, y, w - 2, 1, borda); tela.ret(x + 1, y + h - 1, w - 2, 1, borda)
    tela.ret(x, y + 1, 1, h - 2, borda); tela.ret(x + w - 1, y + 1, 1, h - 2, borda)
    tela.ret(x + 1, y + 1, w - 2, h - 2, fundo)
    if luz is not None:
        tela.ret(x + 2, y + 1, w - 4, 1, luz)


def quebrar(tela, txt, tam, larg):
    """Quebra em linhas que cabem em `larg` (palavra inteira, nunca no meio)."""
    linhas, cur = [], ''
    for p in txt.split():
        tent = (cur + ' ' + p).strip()
        if cur and tela.largura_texto(tent, tam) > larg:
            linhas.append(cur); cur = p
        else:
            cur = tent
    if cur: linhas.append(cur)
    return linhas


def nome_placa(tela, nome):
    """Nome do gênero que cabe em 2x na margem segura (136 px): 'AND' vira '&'."""
    if tela.largura_texto(nome, 17) > 136: nome = nome.replace(' AND ', ' & ')
    return nome


class Moldura:
    """Gancho, placa de gênero, HUD e cartão final, desenhados como interface
    de jogo: fonte de pixel com contorno (sem tarja preta), painéis com borda
    e cantos, fases como pontinhos e não como texto. Em inglês: o canal é
    global. As cores vêm da paleta da cena pela convenção dos índices (11
    branco, 9 destaque, 10 secundário, 0 fundo, 3 traço)."""

    def __init__(self, F, L, cfg):
        self.F, self.L, self.cfg = F, L, cfg
        self.gancho = cfg.get('gancho', ['WAIT FOR', 'THE DROP'])
        self.sub = cfg.get('sub_gancho', '')
        self.pergunta = cfg.get('pergunta', 'WHICH STAGE WAS BEST?')
        self.drops = [s for s in F.secoes if s['papel'] == 'drop']
        self.t_fim = next(e['t'] for e in F.eventos if e['tipo'] == 'fim')
        sec_fim = [s for s in F.secoes if s['papel'] == 'fim']
        self.t_cartao = sec_fim[0]['t0'] if sec_fim else self.t_fim - 3.0
        self.placas = cfg.get('placas', True)
        self.hud = cfg.get('hud', True)
        self.dur_g = cfg.get('dur_gancho', 2.6)

    # ------------------------------------------------------------ desenhar
    def desenhar(self, tela, t):
        if t < self.dur_g: self._gancho(tela, t)
        if self.placas and t >= .2 and t < self.t_cartao: self._placa(tela, t)
        if self.hud and self.dur_g - .2 < t < self.t_cartao: self._hud(tela, t)
        if t >= self.t_cartao: self._cartao(tela, t - self.t_cartao, t)

    def _gancho(self, tela, t):
        """Duas linhas grandes que entram de cima uma depois da outra e
        quicam no bumbo. Já estão inteiras no quadro 0: ele é a capa."""
        L, dur = self.L, self.dur_g
        pk = L.env('kick', t, .10)
        sai = ease(max(0.0, (t - (dur - .3)) / .3))
        y0 = 58
        for k, linha in enumerate(self.gancho):
            tam = 17   # o verificador garante que cabe em 2x dentro da margem segura
            yy = y0 + k * 19 - int(pk * 2 * (1 if k == 0 else -1)) - int(sai * (90 + 20 * k))
            tela.texto(linha, W // 2, yy, 11 if k == 0 else 9, tam=tam, centro=True, contorno=0, sombra=0)
        if self.sub:
            yy = y0 + len(self.gancho) * 19 + 4 - int(sai * 130)
            tela.texto(self.sub, W // 2, yy, 10, tam=9, centro=True, contorno=0)
        if t < dur - .4:
            self._falante(tela, W // 2, y0 - 14, L.env('kick', t, .14))

    def _placa(self, tela, t):
        """Placa do gênero entrando na troca de seção: painel com o nome em
        grande e o BPM embaixo; entra pela esquerda com rebote, sai pela
        direita."""
        L = self.L
        s = L.secao(t)
        mostrar = (s['papel'] in ('drop', 'intro', 'break') and s['i'] > 0) or s['i'] == 0
        if not mostrar or s['papel'] == 'fim': return
        t_ref = s['t0'] if s['i'] > 0 else self.dur_g
        u = t - t_ref
        if not 0 <= u < 1.9: return
        ent = back(u / .28)
        sai = ease((u - 1.55) / .3)
        x_off = int((1 - ent) * -W + sai * W)
        y = self.cfg.get('y_placa', 66)
        nome, bpm = nome_placa(tela, s['nome']), f"{int(round(s['bpm']))} BPM"
        tam = 17 if tela.largura_texto(nome, 17) <= 136 else 9
        w = max(tela.largura_texto(nome, tam), tela.largura_texto(bpm, 9)) + 16
        h = (14 if tam == 17 else 7) + 7 + 12
        x = W // 2 - w // 2 + x_off
        painel(tela, x, y, w, h, borda=9, fundo=0, luz=3)
        tela.texto(nome, x + w // 2, y + 4, 11, tam=tam, centro=True)
        yb = y + 4 + (14 if tam == 17 else 7) + 3
        tela.texto(bpm, x + w // 2, yb, 9, tam=9, centro=True)

    def _hud(self, tela, t):
        """À esquerda o andamento com a luz do bumbo; à direita as fases em
        pontinhos (cheio = passou, aceso = agora)."""
        L = self.L
        s = L.secao(t)
        bpm = f"{int(round(s['bpm']))}"
        x, y = SAFE_X0, 28
        w = tela.largura_texto(bpm, 9) + tela.largura_texto('BPM', 9) + 18
        painel(tela, x - 2, y - 2, w, 12, borda=3, fundo=0)
        luz = L.env('kick', t, .09)
        tela.ret(x + 1, y + 1, 4, 4, 15 if luz > .4 else 3)
        if luz > .4: tela.ret(x + 2, y + 2, 1, 1, 11)
        tela.texto(bpm, x + 8, y, 11, tam=9)
        tela.texto('BPM', x + 12 + tela.largura_texto(bpm, 9), y, 10, tam=9)
        n = len(self.drops)
        if n > 1:
            k = sum(1 for q in self.drops if q['t0'] <= t + 1e-6)
            wv = n * 7 + 4
            xv = SAFE_X1 - wv
            painel(tela, xv, y - 2, wv, 12, borda=3, fundo=0)
            for j in range(n):
                px = xv + 3 + j * 7
                if j < k - 1: tela.ret(px, y + 1, 5, 5, 10)
                elif j == k - 1:
                    tela.ret(px, y + 1, 5, 5, 9)
                    if L.env('kick', t, .12) > .4: tela.ret(px + 1, y + 2, 3, 3, 11)
                else: tela.ret_vazado(px, y + 1, 5, 5, 3)

    def _falante(self, tela, cx, cy, p):
        tela.ret(cx - 7, cy - 3, 4, 6, 11)
        for k in range(4):
            tela.ret(cx - 3 + k, cy - 3 - k, 1, 6 + 2 * k, 11)
        for r, lim in ((5, .0), (8, .35), (11, .65)):
            if p > lim:
                for a in range(-40, 41, 8):
                    aa = math.radians(a)
                    tela.px(cx + 2 + r * math.cos(aa), cy + r * math.sin(aa), 9)

    def _cartao(self, tela, u, t):
        """Fim: o mundo continua tocando; por cima, um painel com a pergunta
        para os comentários. O pedido de inscrição fica com a vinheta."""
        L = self.L
        ent = back(u / .3)
        linhas = quebrar(tela, self.pergunta, 9, 132)
        h = 12 + 10 * len(linhas) + 12
        w = max(tela.largura_texto(l, 9) for l in linhas) + 20
        y = 96 + int((1 - ent) * 220)
        x = W // 2 - w // 2
        painel(tela, x, y, w, h, borda=9, fundo=0, luz=3)
        for k, l in enumerate(linhas):
            tela.texto(l, W // 2, y + 7 + 10 * k, 11, tam=9, centro=True)
        p = L.env('kick', t, .12)
        tela.texto('TELL ME BELOW', W // 2, y + h - 12 + int(p * 1), 9, tam=9, centro=True)
        seta = y + h + 4 + int(2 * math.sin(t * 8))
        for k in range(4):
            tela.ret(W // 2 - 3 + k, seta + k, 7 - 2 * k, 1, 9)


# =================================================================== pós
def tremer(tela, dx, dy):
    """Desloca o quadro inteiro (tremor de câmera) preenchendo com o fundo."""
    if dx == 0 and dy == 0: return
    b = np.roll(tela.buf, (int(dy), int(dx)), (0, 1))
    if dy > 0: b[:dy] = 0
    elif dy < 0: b[dy:] = 0
    if dx > 0: b[:, :dx] = 0
    elif dx < 0: b[:, dx:] = 0
    tela.buf[:] = b


def scanlines(rgb, forca=3):
    """Linha escura a cada bloco de pixel: tubo de TV sem custar quase nada."""
    v = rgb[PX.ESCALA - 1::PX.ESCALA]
    rgb[PX.ESCALA - 1::PX.ESCALA] = (v.astype(np.uint16) * forca // 4).astype(np.uint8)
    return rgb


# =================================================================== render
def renderizar(cena_cls, cfg, saida, dirsaida):
    """Faixa -> cena -> moldura -> vinheta -> mp4. Devolve relatório."""
    os.makedirs(dirsaida, exist_ok=True)
    seed = cfg['seed']
    F = M.compor(cfg['secoes'], seed=seed, raiz=cfg.get('raiz'))
    L = Linha(F)
    rng = np.random.default_rng(seed * 13 + 1)
    cena = cena_cls(F, L, cfg, rng)
    mold = Moldura(F, L, cfg)
    tela = PX.Tela(W, H, paleta=cfg['paleta'])
    t_fim = mold.t_fim
    pal_secao = cfg.get('paletas_secao')     # troca de paleta por seção

    # ---- áudio: música + som da vinheta encostado no fim do último compasso
    vin = PM.som_encerramento(seed)
    total = t_fim + PM.OUTRO_S
    n = int(total * M.SR)
    mix = np.zeros((n, 2), np.float32)
    a = F.audio[:n]
    mix[:len(a)] += a
    i0 = int(t_fim * M.SR)
    v = vin[:n - i0]
    mix[i0:i0 + len(v)] += v * .95
    mix, lufs, tp = QA.master(mix, -14.0)
    wav = os.path.join(dirsaida, saida.replace('.mp4', '.wav'))
    sf.write(wav, mix, M.SR, subtype='PCM_16')

    vin_q = list(PM.encerramento(W, H, FPS, cfg.get('chamadas', ['SUBSCRIBE', 'FOR MORE BEATS']), seed))
    acab = AC.Acabamento(L, cfg, W, H)
    scan = cfg.get('scanlines', False)
    pal_atual = [cfg['paleta']]

    def quadro(t, i):
        if t >= t_fim:
            k = min(len(vin_q) - 1, int((t - t_fim) * FPS))
            return vin_q[k]
        if pal_secao:
            s = L.secao(t)
            p = pal_secao[s['i'] % len(pal_secao)]
            if p != pal_atual[0]:
                tela.pal = p; tela.rgb = PX.paleta_rgb(p); pal_atual[0] = p
        cena.desenhar(tela, t, i)
        mold.desenhar(tela, t)
        dx, dy = cena.tremor(t) if hasattr(cena, 'tremor') else (0, 0)
        tremer(tela, dx, dy)
        baixo = acab.aplicar(tela, t)
        rgb = np.repeat(np.repeat(baixo, PX.ESCALA, 0), PX.ESCALA, 1)
        if scan: rgb = scanlines(rgb)
        return rgb

    caminho = os.path.join(dirsaida, saida)
    Wf, Hf = W * PX.ESCALA, H * PX.ESCALA
    args = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{Wf}x{Hf}', '-r', str(FPS), '-i', '-', '-i', wav,
            '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', str(cfg.get('crf', 20)),
            '-pix_fmt', 'yuv420p', '-g', str(FPS), '-sws_flags', 'neighbor',
            '-movflags', '+faststart', '-shortest', caminho]
    p = subprocess.Popen(args, stdin=subprocess.PIPE)
    nq = int(round(total * FPS))
    for i in range(nq):
        fr = quadro(i / FPS, i)
        p.stdin.write(np.ascontiguousarray(fr, dtype=np.uint8).tobytes())
    p.stdin.close(); p.wait()
    os.remove(wav)
    # grade de eventos para conferência e para editor
    ev = [dict(t=round(e['t'], 4), tipo=e['tipo']) for e in F.eventos
          if e['tipo'] in ('kick', 'snare', 'clap', 'drop', 'secao', 'batida')]
    json.dump(dict(id=cfg['id'], total=round(total, 3), lufs=lufs, tp=tp,
                   secoes=[{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()} for s in F.secoes],
                   eventos=ev), open(caminho.replace('.mp4', '.json'), 'w'), indent=0)
    return dict(id=cfg['id'], arquivo=caminho, dur=round(total, 2), lufs=lufs, tp=tp, quadros=nq)


def amostra(cena_cls, cfg, tempos, saida_png, escala=2):
    """Quadros soltos lado a lado num PNG, para olhar sem renderizar o vídeo."""
    from PIL import Image
    F = M.compor(cfg['secoes'], seed=cfg['seed'], raiz=cfg.get('raiz'))
    L = Linha(F)
    cena = cena_cls(F, L, cfg, np.random.default_rng(cfg['seed'] * 13 + 1))
    mold = Moldura(F, L, cfg)
    tela = PX.Tela(W, H, paleta=cfg['paleta'])
    acab = AC.Acabamento(L, cfg, W, H)
    ims = []
    for t in tempos:
        if cfg.get('paletas_secao'):
            p = cfg['paletas_secao'][L.secao(t)['i'] % len(cfg['paletas_secao'])]
            tela.pal = p; tela.rgb = PX.paleta_rgb(p)
        cena.desenhar(tela, t, int(t * FPS))
        mold.desenhar(tela, t)
        im = Image.fromarray(acab.aplicar(tela, t)).resize((W * escala, H * escala), Image.NEAREST)
        ims.append(im)
    out = Image.new('RGB', (len(ims) * (W * escala + 8), H * escala), (40, 40, 40))
    for k, im in enumerate(ims): out.paste(im, (k * (W * escala + 8), 0))
    out.save(saida_png)
    return F


# =================================================================== cena
class CenaBase:
    """Esqueleto das cenas. `zoom=2` desenha o mundo em meia resolução e
    dobra (pixel gordo); `sobre()` desenha por cima em resolução cheia."""
    zoom = 1

    def __init__(self, F, L, cfg, rng):
        self.F, self.L, self.cfg, self.rng = F, L, cfg, rng
        self.v = cfg.get('variante', {})
        self.preparar()

    def preparar(self): pass
    def mundo(self, tela, t, i): pass
    def sobre(self, tela, t, i): pass

    def desenhar(self, tela_out, t, i):
        if self.zoom == 1:
            self.mundo(tela_out, t, i)
        else:
            z = self.zoom
            if not hasattr(self, '_sub') or self._sub.pal != tela_out.pal:
                self._sub = PX.Tela(W // z, H // z, paleta=tela_out.pal)
            self.mundo(self._sub, t, i)
            tela_out.buf[:] = np.repeat(np.repeat(self._sub.buf, z, 0), z, 1)
        self.sobre(tela_out, t, i)

    def tremor(self, t):
        L = self.L
        drop = L.secao(t)['papel'] in ('drop', 'fim')
        p = L.env('drop', t, .25) * 4 + L.env('kick', t, .05) * (1.4 if drop else .3)
        k = int(t * 60)
        return (int(round(math.sin(k * 1.7) * p)), int(round(math.cos(k * 2.3) * p * .6)))


def nova_paleta(nome, cores):
    """Registra paleta própria de uma cena (16 cores, mesma convenção)."""
    assert len(cores) == 16, nome
    PX.PALETAS[nome] = cores
    return nome


def hsh(*a):
    """Hash inteiro estável para decoração procedural."""
    h = 2166136261
    for v in a:
        h = ((h ^ (int(v) & 0xffffffff)) * 16777619) & 0xffffffff
    return h
