#!/usr/bin/env python3
"""ADIVINHA O DESENHO — o desenho se forma aos poucos, em blocos ou a lápis.

O desenho é uma grade em texto: uma linha por fileira, um caractere por
bloco, `.` para vazio e um dígito hexadecimal para o índice da paleta. Caber
num arquivo de texto é o que torna 125 desenhos viável — editável à mão,
versíonável e leve.

**A ordem da revelação é o que cria a tensão.** Nunca de cima para baixo:
começa pelo miolo, que confunde, e deixa a silhueta por último. Quem adivinha
cedo sente que é esperto; quem adivinha tarde fica até o fim.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

DUR = 24.0
T_PALPITE = 6.0
AREA_Y0, AREA_Y1 = 76, 256


def ler_grade(linhas):
    g = [[-1 if c == '.' else int(c, 16) for c in l] for l in linhas]
    return g, len(g[0]), len(g)


def ordem_revelacao(gx, gy, seed):
    """Do miolo para fora, com ruído: a silhueta — que entrega o desenho —
    fica para o fim."""
    rng = np.random.default_rng(seed)
    cx, cy = gx / 2, gy / 2
    cel = [(x, y) for y in range(gy) for x in range(gx)]
    peso = [((x - cx) ** 2 + (y - cy) ** 2) ** .5 + rng.normal(0, gx * .14)
            for x, y in cel]
    return [c for _, c in sorted(zip(peso, cel))]


def construir(b, seed=101, saida='revelar.mp4', dirsaida='out-revelar',
              dur=DUR):
    # a duracao por item vem da unidade quando ela traz: e isso que
    # permite ao Short encurtar sem um simulador separado. Enquanto
    # era so argumento de funcao, o ajuste que o shorts.py punha na
    # unidade era silenciosamente ignorado e o Short saia com 60,0 s.
    dur = float(b.get('dur', dur))
    des = b['desenhos']
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = len(des) * dur
    tela = PX.Tela(paleta=b.get('paleta', 'papelao'))
    rng = np.random.default_rng(seed * 89 + 3)
    modo = b.get('modo', 'pixel')          # pixel | lapis

    prep = []
    for k, d in enumerate(des):
        g, gx, gy = ler_grade(d['grade'])
        lado = min((AREA_Y1 - AREA_Y0) // gy, (PX.LARG - 20) // gx)
        prep.append(dict(g=g, gx=gx, gy=gy, lado=lado,
                         x0=(PX.LARG - gx * lado) // 2,
                         y0=AREA_Y0 + (AREA_Y1 - AREA_Y0 - gy * lado) // 2,
                         ordem=ordem_revelacao(gx, gy, seed * 7 + k),
                         nome=d['nome']))

    def quadro(t, i):
        k = min(len(prep) - 1, int(t / dur))
        tl = t - k * dur
        p = prep[k]
        pulso = bat.pulso(t, .13)
        t_des = dur - T_PALPITE - 1.0
        u = max(0.0, min(1.0, (tl - 1.0) / t_des))
        n = int(len(p['ordem']) * u)

        tela.limpar(0)
        tela.ret(0, AREA_Y0 - 10, PX.LARG, AREA_Y1 - AREA_Y0 + 20,
                 8 if modo == 'lapis' else 1)
        if modo == 'lapis':                       # pauta do papel
            for y in range(AREA_Y0 - 6, AREA_Y1 + 10, 9):
                tela.ret(8, y, PX.LARG - 16, 1, 7)

        L = p['lado']
        for j in range(n):
            x, y = p['ordem'][j]
            c = p['g'][y][x]
            if c < 0: continue
            px = p['x0'] + x * L
            py = p['y0'] + y * L
            if modo == 'lapis':
                # traço de lápis: hachura dentro da célula, não bloco cheio
                for h in range(0, L, 2):
                    tela.ret(px + h, py, 1, L, 2 if c > 6 else 0)
            else:
                tela.ret(px, py, L, L, c)
                if j >= n - 3:                     # a última pousa brilhando
                    tela.ret_vazado(px, py, L, L, 11)

        # --- HUD
        tela.ret(0, 0, PX.LARG, AREA_Y0 - 12, 0)
        tela.texto(b['titulo'], PX.LARG // 2, 6, 6, tam=10, centro=True)
        falta = max(0.0, dur - T_PALPITE - tl)
        if u >= 1 and falta > 0:
            tela.texto(str(int(math.ceil(falta))), PX.LARG // 2, 22, 11,
                       tam=int(30 * (1 + .18 * bat.pulso(t, .1))), centro=True,
                       sombra=3)
        else:
            tela.texto(f'{int(u*100)}%', PX.LARG // 2, 26, 8, tam=18, centro=True)

        if tl > dur - T_PALPITE:                   # a resposta
            y = PX.ALT - 42
            tela.ret(10, y - 4, PX.LARG - 20, 28, 0)
            tela.ret(10, y - 4, 2, 28, 11)
            tela.texto_ajustado(p['nome'], PX.LARG // 2, y + 2, 11, 17,
                                PX.LARG - 32, centro=True)
        tela.ret(0, PX.ALT - 3, int(PX.LARG * (t / total)), 3, 12)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .45 * ((tt % dur) / dur))
    for k in range(len(des)):
        A.put(mix, A.page(rng, kit['root']), k * dur, .5)
        A.put(mix, A.correct(rng, kit['root']), k * dur + dur - T_PALPITE, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_revelar.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{len(des)} desenhos ({modo}) · {nq} quadros em {dt:.1f}s = '
          f'{nq/dt:.1f} fps ({total/dt:.2f}x tempo real) · {total:.0f}s')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 101,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-revelar')
