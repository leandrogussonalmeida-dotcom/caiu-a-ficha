#!/usr/bin/env python3
"""A DESCIDA — a câmera desce por camadas, sem corte, até o fundo.

Ao contrário da ESCADA do LIMITE, aqui não se vê onde termina. É o oposto
da promessa: o espectador fica porque **não sabe quando acaba**, e cada
camada nova é a resposta parcial. Serve para o centro da Terra, a fossa, a
mina, o poço e a queda livre.

A profundidade corre em escala própria por camada: a crosta e o manto não
podem ter o mesmo número de pixels por quilômetro, senão a crosta some.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

TOPO, BASE = 88, 272


def construir(u, seed=61, saida='descida.mp4', dirsaida='out-descida'):
    cam = u['camadas']
    n = len(cam)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    por = u.get('batidas_por_camada', 6)
    dc = bat.spb * por
    total = 1.6 + n * dc + 4.0
    tela = PX.Tela(paleta=u.get('paleta', 'carvao'))
    rng = np.random.default_rng(seed * 59 + 5)
    un = u.get('unidade', 'M')
    ALT = BASE - TOPO

    # textura fixa de cada camada, pré-calculada
    GR = 3
    tex = [np.repeat(np.repeat(rng.random((ALT // GR + 2, PX.LARG // GR + 1)),
                               GR, 0), GR, 1)[:ALT + GR, :PX.LARG] for _ in range(n)]

    def fmt(v):
        if abs(v) >= 1e6: return f'{v/1e6:.2f}'.rstrip('0').rstrip('.') + 'M'
        if abs(v) >= 10000: return f'{v/1000:.1f}'.replace('.0', '') + 'K'
        return f'{v:.0f}'

    def quadro(t, i):
        tl = max(0.0, t - 1.6)
        pos = min(n, tl / dc)
        k = min(n - 1, int(pos))
        frac = min(1.0, pos - k)
        prof = cam[k]['ate'] * frac + (cam[k - 1]['ate'] if k else 0) * (1 - frac)
        pulso = bat.pulso(t, .14)

        tela.limpar(0)
        # as camadas rolam para cima; cada uma tem a sua cor e a sua textura
        desl = (pos % 1.0) * ALT
        for d in (-1, 0, 1):
            j = k + d
            if not (0 <= j < n): continue
            y0 = int(TOPO + ALT * d - desl)
            y1 = y0 + ALT + 2
            a0, a1 = max(TOPO, y0), min(BASE, y1)
            if a1 <= a0: continue
            c = cam[j].get('cor', 2 + (j % 5))
            tela.ret(0, a0, PX.LARG, a1 - a0, c)
            tt = tex[j][(a0 - y0):(a0 - y0) + (a1 - a0)]
            faixa = tela.buf[a0:a1]
            if tt.shape[0] == faixa.shape[0]:
                # textura discreta: densidade alta lia como chuvisco de TV
                faixa[tt < .045] = max(0, c - 1)
                faixa[tt > .975] = min(15, c + 2)
            if y0 > TOPO:
                # o nome da camada vai sobre faixa escura: em cima da rocha
                # clara, texto claro some
                tela.ret(0, y0, PX.LARG, 1, 11)
                tela.ret(0, y0 + 1, PX.LARG, 15, 0)
                tela.texto_ajustado(cam[j]['nome'], 8, y0 + 4, 11, 11, PX.LARG - 86)
                tela.texto(f"{fmt(cam[j - 1]['ate'] if j else 0)} {un}",
                           PX.LARG - 8, y0 + 4, 8, tam=9, centro='d')

        # o cabo e a cabine, sempre no mesmo lugar
        tela.ret(PX.LARG // 2 - 1, TOPO, 2, 128, 3)
        cx, cy = PX.LARG // 2, TOPO + 128
        tela.ret(cx - 13, cy - 16, 26, 32, 0)
        tela.ret_vazado(cx - 13, cy - 16, 26, 32, 11)
        tela.ret(cx - 9, cy - 12, 18, 13, 9 if pulso > .5 else 8)
        tela.ret(cx - 4, cy + 4, 8, 9, 3)

        # --- HUD
        tela.ret(0, 0, PX.LARG, TOPO - 8, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 6, 6, tam=9, centro=True)
        esc = 1 + .1 * pulso
        tela.texto(fmt(prof), PX.LARG // 2, 20, 11, tam=int(36 * esc),
                   centro=True, sombra=3)
        tela.texto(f'{un} DE PROFUNDIDADE', PX.LARG // 2, 60, 8, tam=9, centro=True)
        tela.ret(PX.LARG - 7, TOPO, 4, BASE - TOPO, 3)
        tela.ret(PX.LARG - 7, TOPO, 4, int((BASE - TOPO) * min(1, pos / n)), 12)
        tela.ret(0, BASE + 2, PX.LARG, PX.ALT - BASE - 2, 0)
        nota = cam[k].get('nota', cam[k]['nome'])
        tela.texto_ajustado(nota, PX.LARG // 2, BASE + 8, 8, 11, PX.LARG - 16,
                            centro=True)
        if pos >= n and u.get('fecho'):
            tela.texto_ajustado(u['fecho'], PX.LARG // 2, BASE + 26, 11, 11,
                                PX.LARG - 16, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .28 + .5 * min(1, tt / total))
    for j in range(n):
        A.put(mix, A.page(rng, kit['root']), 1.6 + j * dc, .5)
    A.put(mix, A.correct(rng, kit['root']), total - 4.0, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_descida.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{n} camadas · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 61,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-descida')
