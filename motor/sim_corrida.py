#!/usr/bin/env python3
"""CORRIDA 8-BIT — velocidades reais correndo lado a lado.

A graça não é quem ganha, é **quanto** ganha. Um guepardo contra um carro de
Fórmula 1 não é uma disputa, é um massacre — e ver o massacre acontecer em
tempo real diz mais que a tabela de velocidades.

Por isso a pista rola até o primeiro colocado cruzar: quem ficou para trás
fica para trás na tela, não numa legenda.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

TOPO = 92
PISTA_X0, PISTA_X1 = 16, 164


def construir(u, seed=71, saida='corrida.mp4', dirsaida='out-corrida'):
    corr = sorted(u['corredores'], key=lambda c: -c['v'])
    n = len(corr)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    tviagem = u.get('segundos', 22.0)
    total = 2.4 + tviagem + 5.0
    tela = PX.Tela(paleta=u.get('paleta', 'asfalto'))
    rng = np.random.default_rng(seed * 67 + 9)
    vmax = corr[0]['v']
    alt = min(22, (262 - TOPO) // n)
    un = u.get('unidade', 'KM/H')

    def quadro(t, i):
        tl = max(0.0, t - 2.4)
        u_ = min(1.0, tl / tviagem)
        pulso = bat.pulso(t, .12)
        tela.limpar(0)
        tela.ret(0, TOPO - 6, PX.LARG, n * alt + 12, 1)

        # linha de chegada, piscando
        tela.ret(PISTA_X1, TOPO - 4, 2, n * alt + 8, 11 if pulso > .5 else 8)

        ordem = []
        for k, c in enumerate(corr):
            y = TOPO + k * alt
            p = min(1.0, c['v'] / vmax * u_)
            x = PISTA_X0 + (PISTA_X1 - PISTA_X0) * p
            ordem.append((p, c))
            tela.ret(PISTA_X0 - 2, y + alt - 2, PX.LARG - 20, 1, 3)   # raia
            cor = 6 + (k % 6)
            # rastro proporcional à velocidade: quem corre, risca
            tr = int(4 + 16 * (c['v'] / vmax))
            for j in range(tr):
                tela.px(x - 6 - j, y + alt // 2, cor if j < tr // 2 else 3)
            tela.ret(x - 5, y + 2, 10, alt - 5, cor)
            tela.ret(x - 5, y + 2, 10, 1, 11)
            # o nome vai à direita do corredor; se não couber à direita, vai
            # à esquerda. Nunca para fora da tela, que era o que acontecia
            # com o líder.
            larg = tela.largura_texto(c['nome'], 8)
            if x + 10 + larg <= PX.LARG - 4:
                tela.texto(c['nome'], x + 10, y + 2, 8, tam=8)
            else:
                tela.texto(c['nome'], max(4, x - 8 - larg), y + 2, 8, tam=8)

        # --- HUD
        tela.ret(0, 0, PX.LARG, TOPO - 8, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 6, 6, tam=9, centro=True)
        lider = corr[0]
        esc = 1 + .1 * pulso
        tela.texto(f"{lider['v']:g}", PX.LARG // 2, 20, 11, tam=int(34 * esc),
                   centro=True, sombra=3)
        # ajustado, nao fixo: "FALCAO-PEREGRINO (MERGULHO)" estourava a tela
        # pelos dois lados e virava um borrao cortado
        tela.texto_ajustado(f"{un} · {lider['nome']}", PX.LARG // 2, 58, 8, 9,
                            PX.LARG - 12, centro=True)
        tela.texto(f'{u_*100:.0f}%', PX.LARG - 6, 6, 6, tam=9, centro='d')

        # pódio no fim
        if u_ >= 1.0:
            y = TOPO + n * alt + 14
            tela.ret(8, y, PX.LARG - 16, 46, 0)
            tela.ret(8, y, 2, 46, 11)
            for j, (pp, c) in enumerate(sorted(ordem, key=lambda z: -z[0])[:3]):
                tela.texto(f'{j+1}', 16, y + 5 + j * 13, 11, tam=10)
                tela.texto_ajustado(c['nome'], 30, y + 5 + j * 13, 8, 10, 92)
                tela.texto(f"{c['v']:g}", PX.LARG - 14, y + 5 + j * 13, 8,
                           tam=10, centro='d')
        elif u.get('rodape'):
            tela.texto_ajustado(u['rodape'], PX.LARG // 2, TOPO + n * alt + 20,
                                6, 9, PX.LARG - 16, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .35 + .55 * min(1, tt / total))
    A.put(mix, A.riser(rng, 2.2, kit['root']), .2, .5)
    A.put(mix, A.fanfare(rng, kit['root'], kit), 2.4 + tviagem, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_corrida.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{n} corredores · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 71,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-corrida')
