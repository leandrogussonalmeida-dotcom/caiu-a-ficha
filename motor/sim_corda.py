#!/usr/bin/env python3
"""A CORDA — uma corda descendo no escuro, sem fim à vista.

É o pilar do relaxamento, e ele tem uma regra própria: **nada pode terminar
na tela**. Na TORRE o prazer é chegar; aqui o prazer é não chegar. A corda
paga para baixo, a câmera desce junto a passo constante, e o fundo do mar
nunca entra no quadro.

O que segura não é o suspense, é o contador. A profundidade sobe sozinha e
de vez em quando cruza uma marca real — a piscina olímpica, o mergulho livre,
o Titanic. É o mesmo vício de número do resto do canal, em marcha lenta.

A descida é **logarítmica**, e isso não é um detalhe: é o que torna o vídeo
assistível. Descendo a metros por segundo constantes, a piscina, o cilindro
e a apneia passam voando nos primeiros cinco segundos e sobram oitenta
segundos de nada entre mil e o Titanic. Com a escala em décadas, a corda
anda sempre à mesma velocidade **na tela** e é o número que acelera — cada
casa decimal ganha o mesmo tempo, e toda marca real tem a sua vez. É a mesma
conta da VIAGEM, onde o viajante anda parelho e o relógio é que dispara.

Três coisas fazem a queda parecer queda, e nenhuma é a corda:
- a **luz acaba**: o azul do raso vira preto, e o que sobra é só o acento;
- as partículas **sobem**, e sobem mais rápido no raso que no fundo;
- a corda **balança com atraso** — a onda viaja por ela de cima para baixo,
  como uma onda viaja numa corda de verdade. Balançar tudo junto parece
  um elástico, não uma corda.
"""
import json, math, os, sys, time
import numpy as np
import altaengine as AL
import pixelengine as PX
import quizaudio as A
import soundfile as sf

PX_DEC = 560                # pixels de tela por década de profundidade
M0 = 1.0                    # onde o contador começa


def construir(u, seed=81, saida='corda.mp4', dirsaida='out-corda'):
    marcas = sorted(u['marcas'], key=lambda m: m['v'])
    fundo_m = marcas[-1]['v'] * u.get('folga', 1.35)
    dur = u.get('duracao', 90.0)
    L0, L1 = math.log10(M0), math.log10(fundo_m)
    taxa = (L1 - L0) / dur                  # décadas por segundo
    total = dur + 4.0
    est = AL.ESTILOS[u.get('estilo', 'noturno')]
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    rng = np.random.default_rng(seed * 13 + 7)
    q = AL.Quadro(est)

    CX = AL.LARG * .42                      # a corda fora do centro respira melhor
    # partículas: vivem em pixels de tela, não em metros — na escala log o
    # metro não tem tamanho fixo na tela, e a partícula não precisa dele
    NP = 90
    p_y = rng.random(NP) * (AL.ALT + 200)
    p_x = rng.random(NP) * AL.LARG
    p_r = 2 + rng.random(NP) * 7
    p_v = 40 + rng.random(NP) * 150

    def fmt(v):
        return f'{v:,.0f}'.replace(',', '.')

    def mistura(c1, c2, f):
        f = max(0.0, min(1.0, f))
        return tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))

    def quadro(t, i):
        L = L0 + min(dur, t) * taxa           # a década em que estamos
        prof = 10 ** L
        pulso = bat.pulso(t, .25)
        # a luz acaba por volta dos 200 m, como no mar de verdade
        esc = min(1.0, max(0.0, (L - math.log10(2.0)) / (math.log10(200.0) - math.log10(2.0))))
        topo = mistura((18, 46, 74), est.fundo, esc)
        baixo = mistura((6, 20, 38), (0, 0, 0), esc)

        q.limpar()
        # o gradiente de luz: faixas largas, porque ninguém vê a emenda num
        # degradê vertical de 1920 px dividido em 48
        for b in range(48):
            y = b * AL.ALT / 48
            q.ret(0, y, AL.LARG, AL.ALT / 48 + 2,
                  mistura(topo, baixo, b / 47))

        # --- partículas subindo. No raso sobem mais rápido: é o que diz ao
        # olho que a câmera desce, já que a água não tem textura própria.
        for j in range(NP):
            y = (p_y[j] - t * p_v[j]) % (AL.ALT + 200) - 100
            r = p_r[j] * (1 - .45 * esc)
            q.circulo(p_x[j], y, r, mistura(est.suave, est.fundo, .35 + .4 * esc))

        # --- a corda: a onda viaja por ela, de cima para baixo
        ant = None
        for yy in range(-20, AL.ALT + 20, 14):
            fase = t * 1.5 - yy * .012       # o atraso é o que faz ser corda
            x = CX + math.sin(fase) * (34 - 16 * esc) + math.sin(fase * .43) * 12
            if ant: q.linha(ant[0], ant[1], x, yy, est.suave, 7)
            ant = (x, yy)
        # o nó da ponta nunca aparece: a corda entra e sai do quadro

        # --- as marcas reais, deslizando para cima
        for mk in marcas:
            y = (math.log10(max(1e-6, mk['v'])) - L) * PX_DEC + AL.ALT * .5
            # a faixa do contador e a do rodapé são do HUD: marca que entra
            # nelas vira texto por cima de texto
            if not 400 < y < 1730: continue
            perto = max(0.0, 1 - abs(y - AL.ALT * .5) / 300)
            cor = mistura(est.suave, est.acento, perto)
            q.linha(0, y, AL.LARG, y, cor, 1.6, traco=(22, 16))
            q.ajustar(mk['nome'], AL.LARG - 60, y - 46, cor,
                      int(34 + 14 * perto), AL.LARG * .62, anc='ra')
            q.texto(f"{fmt(mk['v'])} m", AL.LARG - 60, y + 12, cor, 28,
                    fonte=est.fonte_rot, anc='ra')

        # --- o contador, que é o que de fato segura
        q.texto(u['titulo'], AL.LARG / 2, 108, est.suave, 30,
                fonte=est.fonte_rot, anc='ma', espaco=4)
        tam = int(132 * (1 + .04 * pulso))
        q.texto(fmt(prof), AL.LARG / 2, 170, est.tinta, tam,
                fonte=est.fonte_num, anc='ma')
        q.texto('METROS', AL.LARG / 2, 330, est.acento, 34,
                fonte=est.fonte_rot, anc='ma', espaco=8)
        q.texto('CAIU A FICHA', AL.LARG / 2, 1800, est.suave, 26,
                fonte=est.fonte_rot, anc='ma', espaco=5)
        return q.render(i)

    os.makedirs(dirsaida, exist_ok=True)
    # trilha: ambiente, sem fanfarra. Fanfarra aqui quebraria o pilar.
    mix = A.groove(total, kit, seed, lambda tt: .18 + .22 * min(1, tt / total))
    for mk in marcas:
        tt = (math.log10(max(1e-6, mk['v'])) - L0) / taxa
        if 0 < tt < total - 2: A.put(mix, A.tick(rng, 0, 1), tt, .4)
    mix, lufs, tp = A.master(mix, -16.0)     # ambiente vive 2 LU mais baixo
    wav = os.path.join(dirsaida, '_corda.wav')
    sf.write(wav, mix, AL.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    t0 = time.time()
    nq = AL.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f"{len(marcas)} marcas · ate {fmt(fundo_m)} m · estilo {est.nome} · "
          f"{nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps "
          f"({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS")


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 81,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-corda')
