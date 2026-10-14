#!/usr/bin/env python3
"""A FILEIRA — quantos cabem deitados.

A ESCALA compara alturas: ela desenha tudo em pé e cresce para cima. Para
comprimento isso mente. Uma baleia de 33 metros não é uma coisa de 33 metros
de altura, e desenhá-la em pé ao lado de um ônibus em pé é bonito e errado.

Aqui o eixo é deitado. O desafiante atravessa a tela, e embaixo dele o
objeto de referência vai sendo **enfileirado**, um por batida, até cobrir o
comprimento inteiro. O número que sobe é a conta que o espectador ia fazer
de cabeça: quantos ônibus cabem na baleia.

É o mesmo prazer do empilhamento da TORRE, deitado — e é o único jeito
honesto de comparar comprimento com os simuladores que eu tenho.
"""
import json, math, os, sys, time
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

ESQ, DIR = 12, PX.LARG - 12
Y_ALVO, Y_REF = 118, 190          # a faixa do desafiante e a da fileira
DUR = 30.0


def construir(u, seed=121, saida='fileira.mp4', dirsaida='out-fileira'):
    itens = u['itens']
    ref = u['ref']
    n = len(itens)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = n * DUR
    tela = PX.Tela(paleta=u.get('paleta', 'oceano' if 'oceano' in PX.PALETAS else 'gelo'))
    rng = np.random.default_rng(seed * 23 + 7)
    vr = float(ref['valor'])
    # UMA escala para o video inteiro, ditada pelo maior item. Normalizar
    # item a item fazia todo bicho ocupar a tela toda: o que crescia na
    # tela era o numero, e o onibus e que parecia encolher. Com a escala
    # fixa o onibus vira unidade de medida de verdade e o bicho cresce.
    vmax = max([vr] + [float(x['valor']) for x in itens])

    def fmt(v):
        return (f'{v:.0f}' if abs(v - round(v)) < .05 else
                f'{v:.1f}'.replace('.', ','))

    def quadro(t, i):
        k = min(n - 1, int(t / DUR))
        tl = t - k * DUR
        it = itens[k]
        va = float(it['valor'])
        quantos = va / vr
        pulso = bat.pulso(t, .14)

        # a fileira enche na batida, não no relógio: é o que faz o olho
        # contar junto
        passo = bat.spb * u.get('batidas_por_item', 1)
        postos = min(quantos, max(0.0, (tl - 2.0) / passo))

        tela.limpar(0)
        tela.ret(0, 0, PX.LARG, PX.ALT, 1)

        larg = DIR - ESQ
        esc = larg / vmax               # pixels por metro, igual o video todo

        # --- o desafiante, deitado e atravessando a tela
        wa = va * esc
        tela.ret(ESQ, Y_ALVO, wa, 26, 9)
        tela.ret(ESQ, Y_ALVO, wa, 2, 11)
        # nome dentro da barra so quando cabe; senao vai por cima dela, que
        # e melhor que espremer "CROCODILO-DE-AGUA-SALGADA" em 20 pixels
        if wa > 96:
            tela.texto_ajustado(it['nome'], ESQ + 3, Y_ALVO + 8, 0, 10,
                                int(wa) - 6)
        else:
            tela.texto_ajustado(it['nome'], ESQ, Y_ALVO - 13, 11, 10,
                                PX.LARG - 24)
        tela.texto(f"{fmt(va)} {it.get('un','m')}",
                   min(DIR, ESQ + wa + 4) if wa < PX.LARG - 70 else DIR,
                   Y_ALVO + 30, 8, tam=9,
                   centro='d' if wa >= PX.LARG - 70 else False)

        # --- a fileira de referências, encostadas uma na outra
        wr = vr * esc
        cheios = int(postos)
        for j in range(cheios + 1):
            f = min(1.0, postos - j)
            if f <= 0: break
            x = ESQ + j * wr
            tela.ret(x, Y_REF, max(1, wr * f) - 1, 20, 3 if j % 2 else 4)
            if wr > 14 and f >= 1:
                tela.ret(x + 1, Y_REF + 2, wr - 4, 2, 6)
        tela.texto(ref['nome'], ESQ, Y_REF + 26, 8, tam=9)
        tela.texto(f"{fmt(vr)} {ref.get('un','m')} cada", DIR, Y_REF + 26, 6,
                   tam=8, centro='d')

        # --- o número
        tela.ret(0, 0, PX.LARG, Y_ALVO - 14, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 8, 6, tam=9, centro=True)
        esc_n = 1 + .14 * pulso
        tela.texto(fmt(postos), PX.LARG // 2, 26, 11,
                   tam=int(40 * esc_n), centro=True, sombra=3)
        tela.texto_ajustado(ref.get('rotulo', ref['nome']), PX.LARG // 2, 72,
                            8, 11, PX.LARG - 20, centro=True)

        if postos >= quantos - 1e-6 and it.get('ancora'):
            tela.texto_ajustado(it['ancora'], PX.LARG // 2, Y_REF + 52, 11,
                                11, PX.LARG - 16, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .55 * min(1, tt / total))
    for k in range(n):
        q = float(itens[k]['valor']) / vr
        passo = bat.spb * u.get('batidas_por_item', 1)
        for j in range(int(q) + 1):
            tt = k * DUR + 2.0 + j * passo
            if tt < (k + 1) * DUR - 1: A.put(mix, A.tick(rng, j, 12), tt, .42)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_fileira.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{n} itens · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 121,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-fileira')
