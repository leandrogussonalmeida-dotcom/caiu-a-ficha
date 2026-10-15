#!/usr/bin/env python3
"""NO RITMO — a moldura comum dos 30 Shorts.

Cada cena desenha o mundo. Esta base põe por cima o que é do canal:

  gancho      frase de desafio já no quadro 0 (o primeiro quadro é a capa)
  placa       nome do gênero e o BPM entrando a cada troca de seção
  hud         BPM atual e uma luz que pisca em cada bumbo
  cartão      no último trecho: pedido de inscrição com o botão apertado
              na batida e uma pergunta para os comentários
  vinheta     a ficha 8-bit de `pixelmarca`, no fim, com o som dela

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
import pixelmarca as PM
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
class Moldura:
    """Gancho, placas, HUD e cartão final. As cores vêm da paleta da cena,
    pelos índices da convenção (11 branco, 9 destaque, 10 secundário, 0
    fundo)."""

    def __init__(self, F, L, cfg):
        self.F, self.L, self.cfg = F, L, cfg
        self.gancho = cfg.get('gancho', ['ESPERA O DROP'])
        self.sub = cfg.get('sub_gancho', '')
        self.pergunta = cfg.get('pergunta', 'QUAL FASE FOI A MELHOR?')
        self.n_fases = len([s for s in F.secoes if s['papel'] in ('drop',)])
        self.t_fim = next(e['t'] for e in F.eventos if e['tipo'] == 'fim')
        sec_fim = [s for s in F.secoes if s['papel'] == 'fim']
        self.t_cartao = sec_fim[0]['t0'] if sec_fim else self.t_fim - 3.0
        self.placas = cfg.get('placas', True)
        self.hud = cfg.get('hud', True)

    def faixa_texto(self, tela, txt, y, tam, cor, fundo, larg_max=None, pad=3):
        larg_max = larg_max or (SAFE_X1 - SAFE_X0 + 20)
        tam_ok = tam
        while tam_ok > 6 and tela.largura_texto(txt, tam_ok) > larg_max: tam_ok -= 1
        w = tela.largura_texto(txt, tam_ok)
        x = W // 2 - w // 2
        if fundo is not None:
            tela.ret(x - pad, y - pad + 1, w + 2 * pad, tam_ok + 2 * pad - 1, fundo)
        tela.texto(txt, W // 2, y, cor, tam=tam_ok, centro=True)
        return tam_ok

    def desenhar(self, tela, t):
        L = self.L
        # ------------------------------------------------ gancho (0 a ~2.6 s)
        dur_g = self.cfg.get('dur_gancho', 2.6)
        if t < dur_g:
            pk = L.env('kick', t, .10)
            sai = max(0.0, (t - (dur_g - .35)) / .35)
            y0 = int(54 - 40 * ease(sai) ** 2)
            for k, linha in enumerate(self.gancho):
                tam = 17 if len(linha) <= 11 else (14 if len(linha) <= 14 else 12)
                yy = y0 + k * (tam + 7) - int(pk * 2)
                cor = 11 if k == 0 else 9
                self.faixa_texto(tela, linha, yy, tam, cor if sai < .9 else 0, 0 if sai < .5 else None, pad=4)
            if self.sub and sai < .5:
                self.faixa_texto(tela, self.sub, y0 + len(self.gancho) * 22 + 2, 9, 10, 0)
            # alto-falante piscando: "liga o som"
            if t < dur_g - .4:
                self._falante(tela, W // 2, y0 - 16, L.env('kick', t, .14))

        # ------------------------------------------------ placa de seção
        if self.placas and t >= .2:
            s = L.secao(t)
            dt = t - s['t0']
            mostrar = s['papel'] in ('drop', 'intro', 'break') and s['i'] > 0 or (s['i'] == 0 and dt > dur_g)
            if mostrar and s['papel'] != 'fim' and t < self.t_cartao:
                t_ref = s['t0'] if s['i'] > 0 else dur_g
                u = t - t_ref
                if 0 <= u < 1.9:
                    ent = back(u / .28)
                    sai = ease((u - 1.55) / .3)
                    x_off = int((1 - ent) * -W + sai * W)
                    y = self.cfg.get('y_placa', 66)
                    nome = s['nome']
                    bpm = f"{int(round(s['bpm']))} BPM"
                    tam = 15 if len(nome) <= 9 else 12
                    w = max(tela.largura_texto(nome, tam), tela.largura_texto(bpm, 9)) + 14
                    x = W // 2 - w // 2 + x_off
                    tela.ret(x + 2, y + 2, w, tam + 16, 0)
                    tela.ret(x, y, w, tam + 16, 9)
                    tela.ret(x + 1, y + 1, w - 2, tam + 14, 0)
                    tela.texto(nome, x + w // 2, y + 3, 11, tam=tam, centro=True)
                    tela.texto(bpm, x + w // 2, y + tam + 5, 9, tam=9, centro=True)

        # ------------------------------------------------ HUD (BPM + luz)
        if self.hud and t > dur_g - .2 and t < self.t_cartao:
            s = L.secao(t)
            bpm = f"{int(round(s['bpm']))}"
            x, y = SAFE_X0, 30
            tela.ret(x - 2, y - 2, 44, 13, 0)
            luz = L.env('kick', t, .09)
            tela.disco(x + 3, y + 4, 2.6, 15 if luz > .4 else 3)
            tela.texto(bpm, x + 9, y, 11, tam=9)
            tela.texto('BPM', x + 9 + tela.largura_texto(bpm, 9) + 2, y + 1, 10, tam=8)
            if self.n_fases > 1:
                drops = [q for q in self.F.secoes if q['papel'] == 'drop']
                k = sum(1 for q in drops if q['t0'] <= t + 1e-6)
                txt = f"FASE {max(1, k)}/{len(drops)}"
                wv = tela.largura_texto(txt, 8)
                tela.ret(SAFE_X1 - wv - 2, y - 2, wv + 4, 13, 0)
                tela.texto(txt, SAFE_X1 - wv, y + 1, 10, tam=8)

        # ------------------------------------------------ cartão final
        if t >= self.t_cartao:
            self.cartao(tela, t - self.t_cartao, t)

    def _falante(self, tela, cx, cy, p):
        tela.ret(cx - 7, cy - 3, 4, 6, 11)
        for k in range(4):
            tela.ret(cx - 3 + k, cy - 3 - k, 1, 6 + 2 * k, 11)
        for r, lim in ((5, .0), (8, .35), (11, .65)):
            if p > lim:
                for a in range(-40, 41, 8):
                    aa = math.radians(a)
                    tela.px(cx + 2 + r * math.cos(aa), cy + r * math.sin(aa), 9)

    def cartao(self, tela, u, t):
        L = self.L
        ent = ease(u / .35)
        # escurece o mundo atrás em faixas (pixel, sem transparência)
        h_cx = int(150 * ent)
        y0 = 120 - h_cx // 2
        tela.ret(0, y0, W, h_cx, 0)
        tela.ret(0, y0, W, 1, 9); tela.ret(0, y0 + h_cx - 1, W, 1, 9)
        if ent < .9: return
        tela.texto_ajustado(self.cfg.get('cartao_titulo', 'CURTIU O SOM?'), W // 2, 62, 11, 15, 150, centro=True)
        # botão: afunda em cada bumbo, como se alguém batesse nele no tempo
        p = L.env('kick', t, .10)
        bw, bh = 120, 26
        bx, by = W // 2 - bw // 2, 92 + int(p * 3)
        tela.ret(bx + 2, 92 + bh + 2 - 0, bw, 4 - int(p * 3), 13)
        tela.ret(bx, by, bw, bh, 15)
        tela.ret(bx, by, bw, 2, 11 if p > .5 else 15)
        tela.texto('INSCREVA-SE', W // 2, by + 7, 11, tam=13, centro=True)
        # cursor de mão que bate no botão
        mx, my = bx + bw - 14, by + bh - 4 - int((1 - p) * 6)
        mao = [
            "..X.....",
            ".XWX....",
            ".XWX....",
            ".XWXXX..",
            "XXWWWWX.",
            "XWWWWWWX",
            "XWWWWWWX",
            ".XWWWWX.",
            "..XXXX..",
        ]
        Sprite(mao, {'X': 0, 'W': 11}).por(tela, mx, my)
        # sininho
        sx, sy = W // 2, 132
        tela.texto(self.pergunta, W // 2, 140, 9, tam=9, centro=True) if tela.largura_texto(self.pergunta, 9) < 160 else \
            tela.texto_ajustado(self.pergunta, W // 2, 140, 9, 9, 160, centro=True)
        tela.texto('COMENTA AQUI', W // 2, 156, 10, tam=9, centro=True)
        seta_y = 172 + int(3 * math.sin(t * 9))
        for k in range(5):
            tela.ret(W // 2 - 4 + k, seta_y + k, 9 - 2 * k, 1, 9)


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

    vin_q = list(PM.encerramento(W, H, FPS, cfg.get('chamadas', ['INSCREVA-SE', 'TEM MAIS SOM NO CANAL']), seed))
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
        rgb = tela.quadro()
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
    ims = []
    for t in tempos:
        if cfg.get('paletas_secao'):
            p = cfg['paletas_secao'][L.secao(t)['i'] % len(cfg['paletas_secao'])]
            tela.pal = p; tela.rgb = PX.paleta_rgb(p)
        cena.desenhar(tela, t, int(t * FPS))
        mold.desenhar(tela, t)
        im = Image.fromarray(tela.rgb[tela.buf]).resize((W * escala, H * escala), Image.NEAREST)
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
