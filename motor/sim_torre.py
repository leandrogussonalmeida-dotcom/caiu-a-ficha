#!/usr/bin/env python3
"""A TORRE — bloco cai na batida, a pilha cresce, a câmera sobe.

Prova de conceito do motor de pixel: cada bloco toca o chão exatamente no
instante de uma batida, porque o instante da batida é `n * 60/bpm` e nós
geramos a trilha. Não há detecção de beat em lugar nenhum.

Marcos brasileiros entram como linha de referência conforme a torre passa
por eles — é o que transforma dopamina em conteúdo.
"""
import math, sys, os
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

METRO_POR_BLOCO = 10
BLOCO_H = 9                      # altura do bloco em pixels da tela baixa
BLOCO_W = 54

# altura em metros, nome. Conferir antes de publicar.
MARCOS = [(38, 'CRISTO REDENTOR'), (168, 'EDIFICIO ITALIA'),
          (224, 'TORRE DE TV, DF'), (396, 'PAO DE ACUCAR')]

CORES = [6, 8, 9, 10, 12, 13, 5, 4]

# prédios da base: (x, largura, altura) em pixels da tela baixa
SKYLINE = [(0, 22, 26), (24, 14, 38), (40, 18, 20), (60, 12, 30),
           (108, 16, 34), (126, 20, 22), (148, 13, 40), (163, 17, 28)]


def construir(seed=7, blocos=52, paleta='neon', saida='torre.mp4', dirsaida='.'):
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    # o vídeo termina 2,2 s depois do último bloco, para o número respirar
    total = bat.t_de(blocos) + 2.2
    tela = PX.Tela(paleta=paleta)
    rng = np.random.default_rng(seed * 31 + 5)

    estrelas = [(rng.integers(0, PX.LARG), rng.integers(0, 4000),
                 int(rng.integers(0, 3))) for _ in range(220)]

    def altura_em(t):
        """Quantos blocos já pousaram em t."""
        return max(0, min(blocos, int(t / bat.spb)))

    def energia(t):
        return min(1.0, .35 + .65 * (t / max(1, total)))

    def quadro(t, i):
        n = altura_em(t)
        topo_m = n * METRO_POR_BLOCO

        # --- câmera: mantém o topo da pilha a 62% da tela, subindo suave
        alvo = n * BLOCO_H
        cam = alvo - PX.ALT * .38
        # o bloco em queda puxa a câmera um pouco antes de pousar
        prox = (t % bat.spb) / bat.spb
        if n < blocos: cam += BLOCO_H * prox

        # --- tremor no impacto, decaindo rápido
        pul = bat.pulso(t, .11)
        tremor = int(round(pul * pul * 2.4)) if n > 0 else 0

        tela.limpar(0)

        # --- céu: faixas escuras que clareiam com a altitude
        faixa = min(3, int(topo_m / 160))
        if faixa: tela.ret(0, 0, PX.LARG, PX.ALT, faixa)

        # --- estrelas, piscando na batida
        for ex, ey, ec in estrelas:
            y = PX.ALT - (ey - cam * .35) % 4000
            if 0 <= y < PX.ALT:
                c = 11 if (ec == 2 and pul > .55) else (6 if ec else 5)
                tela.px(ex, y, c)

        # --- marcos já alcançados, descendo junto com a câmera
        for m, nome in MARCOS:
            ym = PX.ALT - (m / METRO_POR_BLOCO * BLOCO_H - cam)
            if -12 < ym < PX.ALT:
                passou = topo_m >= m
                c = 11 if passou else 14
                tx0 = (PX.LARG - BLOCO_W) // 2 - 3     # a linha para na torre
                tx1 = tx0 + BLOCO_W + 6
                for x in range(3, PX.LARG - 3, 6):
                    if x < tx0 or x > tx1: tela.ret(x, int(ym), 3, 1, c)
                tela.texto(nome, PX.LARG - 4, int(ym) - 10, c, tam=7,
                           centro='d', sombra=0)
                tela.texto(f'{m}M', 4, int(ym) - 10, c, tam=7, sombra=0)

        # --- a pilha
        base_y = PX.ALT + cam

        # silhueta de cidade na base: a torre precisa sair de algum lugar
        if base_y - 40 < PX.ALT:
            tela.ret(0, base_y, PX.LARG, PX.ALT, 1)
            for j, (lx, lw, lh) in enumerate(SKYLINE):
                tela.ret(lx, base_y - lh, lw, lh, 2)
                for wy in range(3, lh - 2, 5):
                    for wx in range(2, lw - 2, 4):
                        if (j * 7 + wy * 3 + wx) % 5 < 2:
                            tela.px(lx + wx, base_y - lh + wy, 13 if pul > .5 else 14)
        for k in range(n):
            y = base_y - (k + 1) * BLOCO_H
            if y < -BLOCO_H or y > PX.ALT: continue
            x = (PX.LARG - BLOCO_W) // 2 + tremor * (1 if k % 2 else -1)
            c = CORES[k % len(CORES)]
            tela.ret(x, y, BLOCO_W, BLOCO_H, c)
            tela.ret(x, y, BLOCO_W, 1, 11)                    # topo iluminado
            tela.ret(x, y + 1, 2, BLOCO_H - 2, 11)            # canto de luz
            tela.ret(x, y + BLOCO_H - 1, BLOCO_W, 1, 0)       # sombra embaixo
            tela.ret(x + BLOCO_W - 4, y + 1, 4, BLOCO_H - 2, 0)

        # --- o bloco que está caindo, pousando exatamente na batida
        if n < blocos:
            u = prox
            y_final = base_y - (n + 1) * BLOCO_H
            y = y_final - (1 - u) ** 2 * (y_final + BLOCO_H + 34)
            x = (PX.LARG - BLOCO_W) // 2
            c = CORES[n % len(CORES)]
            if y > -BLOCO_H:
                tela.ret(x, y, BLOCO_W, BLOCO_H, c)
                tela.ret(x, y, BLOCO_W, 1, 11)
                for r in range(1, 4):                          # rastro
                    tela.ret(x + 6 * r, y - r * 5, BLOCO_W - 12 * r, 1, c)

        # --- poeira do impacto
        if n > 0 and pul > .25:
            y = base_y - n * BLOCO_H
            esp = (1 - pul) * 26
            for j in range(10):
                a = j / 10 * math.pi
                tela.px((PX.LARG // 2) + math.cos(a) * (BLOCO_W * .5 + esp),
                        y + math.sin(a) * 2, 11 if pul > .6 else 6)

        # --- HUD: o número é o conteúdo
        esc = 1 + .14 * bat.pulso(t, .09)
        tela.ret(0, 0, PX.LARG, 42, 0)
        tela.ret(0, 42, PX.LARG, 1, 3)
        tam = int(26 * esc)
        tela.texto(f'{topo_m}', PX.LARG // 2, 18 - tam // 2, 11,
                   tam=tam, centro=True, sombra=4)
        tela.texto('METROS DE TORRE', PX.LARG // 2, 33, 14, tam=7, centro=True)
        tela.ret(0, 43, int(PX.LARG * n / blocos), 2, 12)
        return tela

    # --- trilha, com a mesma grade de tempo
    mix = A.groove(total, kit, seed, energia)
    for k in range(blocos):                      # um baque em cada pouso
        A.put(mix, A.kick(np.random.default_rng(k), 1.2), bat.t_de(k), .5)
    mix, lufs, tp = A.master(mix, -14.0)
    os.makedirs(dirsaida, exist_ok=True)
    wav = os.path.join(dirsaida, '_torre.wav')
    sf.write(wav, mix, PX.SR)

    nb = PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))

    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    som = 'MUDO' if PX.MUDO else f'{lufs} LUFS / {tp} dBTP'
    print(f'{nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.1f}s · {bat.bpm:.0f}bpm '
          f'· {nb} batidas marcadas · {som}')
    return dict(frames=nq, seg=round(dt, 1), total=round(total, 1), bpm=kit['bpm'])


if __name__ == '__main__':
    construir(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 7,
              blocos=int(sys.argv[2]) if len(sys.argv) > 2 else 52,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-torre')
