#!/usr/bin/env python3
"""MODO FOCO — uma cena só, longa, com progresso lento e visível.

O formato mais barato por minuto entregue, e o que puxa tempo de exibição.
A regra: **o laço não pode ser perceptível.** Se a chuva repete a cada 10 s,
o espectador percebe em 30 s e sai. Então cada elemento tem período próprio
e irracional entre si — nunca voltam todos à mesma posição.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf


def _chuva(tela, t, rng, est, pulso):
    H, W = PX.ALT, PX.LARG
    tela.limpar(0)
    tela.ret(0, 0, W, H, 1)
    for bx, bw, bh in est['predios']:
        tela.ret(bx, H - 86 - bh, bw, bh + 86, 2)
        for wy in range(4, bh - 4, 7):
            for wx in range(2, bw - 3, 5):
                if (wx * 7 + wy * 3 + bx) % 11 < 4:
                    tela.px(bx + wx, H - 86 - bh + wy, 9 if pulso > .7 else 8)
    rel = math.sin(t * .37) * math.sin(t * .131)        # períodos primos entre si
    if rel > .985:
        tela.ret(0, 0, W, H // 2, 11)
    for gx, gy, gv in est['gotas']:
        x = (gx * W - t * 9) % W
        y = (gy * H + t * 340 * gv) % H
        tela.ret(x, y, 1, int(5 + 7 * gv), 6 if gv > .8 else 5)
    tela.ret(0, H - 14, W, 14, 3)                        # peitoril


def _fogueira(tela, t, rng, est, pulso):
    H, W = PX.ALT, PX.LARG
    BASE = H - 58
    tela.limpar(0)
    tela.ret(0, 0, W, H, 1)
    tela.ret(0, BASE, W, H - BASE, 2)
    cx = W // 2
    # halo quente no chão: sem ele a fogueira flutua num vazio preto
    for k in range(7):
        r = 26 + k * 11
        tela.ret(cx - r, BASE - 3 - k, 2 * r, 2 + k // 2, 2 if k > 3 else 3)
    for k, (fx, fp, fa) in enumerate(est['chamas']):
        alt = 104 + 52 * math.sin(t * fp + fa) + 26 * pulso
        larg = 19 + 12 * math.sin(t * fp * 1.7 + fa)
        for j in range(int(alt)):
            q = j / max(1, alt)
            w = max(1, larg * (1 - q) ** .68)
            # branco no núcleo, laranja no corpo, e a ponta some em vez de
            # virar vermelho escuro — fogo não tem ponta escura
            if q < .16: cor = 11
            elif q < .42: cor = 9
            elif q < .78: cor = 7
            else: cor = 6
            if q > .92 and (j + int(t * 20)) % 3: continue
            tela.ret(cx + fx - w / 2 + math.sin(t * 2.3 + q * 5 + fa) * 4 * q,
                     BASE - 4 - j, w, 1, cor)
    for ex, ep, ea in est['brasas']:
        y = BASE - 4 - ((t * 26 * ep + ea * 190) % 236)
        tela.px(cx + ex + math.sin(t * ep * 3 + ea) * 15, y, 9 if y % 3 else 7)
    for lx, lw in est['lenha']:
        tela.ret(cx + lx, BASE - 4, lw, 9, 3)
        tela.ret(cx + lx, BASE - 4, lw, 2, 5)


def _mar(tela, t, rng, est, pulso):
    H, W = PX.ALT, PX.LARG
    tela.limpar(0)
    tela.ret(0, 0, W, H, 1)
    mare = math.sin(t * .021) * 26                        # maré lenta
    hor = int(H * .42 + mare * .3)
    tela.ret(0, 0, W, hor, 2)
    tela.disco(W * .7, hor - 44, 15, 8)
    # A crista é HORIZONTAL e se aproxima: o período cresce com a distância
    # ao horizonte, que é o que dá perspectiva. Deslocar a fase por linha
    # fazia uma diagonal uniforme, que lia como tecido, não como mar.
    xs = np.arange(W)
    for j in range(hor, H):
        q = (j - hor) / max(1, H - hor)
        per = 2.2 + q * q * 24
        banda = math.sin(((j - hor) / per - t * .85) * 6.2832)
        ondul = (np.sin(xs * (.055 + .11 * (1 - q)) + t * 1.2 + j * .05) * .5
                 + np.sin(xs * (.021 + .04 * (1 - q)) - t * .73 + j * .11) * .32)
        v = banda + ondul
        tela.buf[j] = np.where(v > .92, 8, np.where(v > .25, 6,
                               np.where(v > -.55, 4, 3)))
    tela.ret(0, int(H - 26 + mare), W, 40, 5)             # areia


CENAS = dict(chuva=_chuva, fogueira=_fogueira, mar=_mar)


def construir(u, seed=91, saida='ambiente.mp4', dirsaida='out-ambiente'):
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = u.get('segundos', 60.0)
    tela = PX.Tela(paleta=u.get('paleta', 'gelo'))
    rng = np.random.default_rng(seed * 79 + 11)
    cena = CENAS[u.get('cena', 'chuva')]
    est = dict(
        gotas=[(rng.random(), rng.random(), .4 + rng.random()) for _ in range(110)],
        predios=[(x, int(rng.integers(14, 30)), int(rng.integers(20, 90)))
                 for x in range(-6, PX.LARG + 6, 26)],
        chamas=[(int(rng.integers(-16, 17)), .8 + rng.random() * 1.9,
                 rng.random() * 6.3) for _ in range(7)],
        brasas=[(int(rng.integers(-26, 27)), .5 + rng.random(), rng.random())
                for _ in range(26)],
        lenha=[(-34, 28), (4, 30), (-16, 34)])

    def quadro(t, i):
        pulso = bat.pulso(t, .3)
        cena(tela, t, rng, est, pulso)
        # o progresso é discreto: em vídeo de uma hora, HUD grande cansa
        tela.ret(0, 0, PX.LARG, 14, 0)
        tela.texto(u['titulo'], 6, 3, 6, tam=9)
        m, sg = divmod(int(total - t), 60)
        tela.texto(f'{m}:{sg:02d}', PX.LARG - 6, 3, 8, tam=9, centro='d')
        tela.ret(0, 14, int(PX.LARG * t / total), 1, 12)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .20 + .12 * math.sin(tt * .03))
    mix, lufs, tp = A.master(mix, -16.0)      # ambiente entra mais baixo
    wav = os.path.join(dirsaida, '_ambiente.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida), crf=20)
    dt = time.time() - t0
    print(f'cena {u.get("cena")} · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 91,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-ambiente')
