#!/usr/bin/env python3
"""VIAGEM — um relógio correndo enquanto algo atravessa uma distância grande
demais.

A decisão que faz o formato funcionar: **o viajante anda em ritmo constante
na tela, e o relógio é que acelera.** Se o espaço fosse linear, o fóton
passaria por Mercúrio, Terra e Marte nos três primeiros segundos e ficaria
dez minutos atravessando o vazio até Netuno. Invertendo — cada marco ganha o
mesmo tempo de tela, e o relógio salta — o salto do relógio vira o conteúdo.
É ali que cai a ficha.

O viajante fica parado num x fixo e o mundo rola por trás dele, com paralaxe.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import formas as F
import soundfile as sf

X_VIAJANTE = 62          # onde o viajante fica, parado
FAIXA_Y0, FAIXA_Y1 = 118, 214     # a faixa onde a viagem acontece
BARRA_Y = 240
DUR = 34.0


def fmt_tempo(t, un):
    """O relógio. Troca de unidade sozinho quando o número fica grande demais
    para ser sentido: 300 minutos não dizem nada, 5 horas dizem."""
    if un == 'min':
        if t < 1: return f'{t*60:.0f} S', 'SEGUNDOS'
        if t < 90: return f'{int(t)}:{int((t%1)*60):02d}', 'MINUTOS'
        if t < 2880: return f'{int(t//60)}:{int(t%60):02d}', 'HORAS'
        if t < 525600: return f'{t/1440:.1f}'.replace('.0', ''), 'DIAS'
        return f'{t/525600:.2f}'.rstrip('0').rstrip('.'), 'ANOS'
    if un == 'dia':
        if t < 1: return f'{t*24:.0f}', 'HORAS'
        if t < 365: return f'{t:.0f}', 'DIAS'
        return f'{t/365:.1f}'.replace('.0', ''), 'ANOS'
    return f'{t:.0f}', un.upper()


def construir(u, seed=31, saida='viagem.mp4', dirsaida='out-viagem', dur=DUR):
    marcos = u['marcos']
    n = len(marcos)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = dur
    tela = PX.Tela(paleta=u.get('paleta', 'espaco'))
    rng = np.random.default_rng(seed * 29 + 7)
    un = u.get('unidade', 'min')

    # três camadas de estrelas, cada uma com a sua velocidade
    camadas = [[(rng.random() * 3.0, rng.random(), int(rng.integers(0, 3)))
                for _ in range(c)] for c in (120, 70, 36)]
    VEL = (.18, .45, 1.0)

    def tempo_em(pos):
        """Interpola o tempo real entre os marcos, pela posição na lista."""
        if pos <= 0: return 0.0
        if pos >= n - 1: return marcos[-1]['t']
        i = int(pos)
        a, b = marcos[i]['t'], marcos[i + 1]['t']
        return a + (b - a) * (pos - i)

    def quadro(t, i):
        tl = min(1.0, max(0.0, (t - 1.2) / (dur - 5.0)))
        pos = tl * (n - 1)
        treal = tempo_em(pos)
        pulso = bat.pulso(t, .13)
        idx = int(pos)
        # quanto falta para encostar no próximo marco
        frac = pos - idx
        chegou = frac > .93 or (pos >= n - 1)

        tela.limpar(0)
        tela.ret(0, FAIXA_Y0 - 26, PX.LARG, FAIXA_Y1 - FAIXA_Y0 + 52, 1)

        # --- estrelas, rolando em três velocidades
        for c, (pontos, v) in enumerate(zip(camadas, VEL)):
            for ex, ey, et in pontos:
                x = (ex * PX.LARG - pos * 58 * v) % (PX.LARG * 3)
                if x > PX.LARG: continue
                y = FAIXA_Y0 - 22 + ey * (FAIXA_Y1 - FAIXA_Y0 + 44)
                tela.px(x, y, 11 if (c == 2 and pulso > .6) else (6 if c else 4))

        # --- os marcos, chegando pela direita e passando
        cy = (FAIXA_Y0 + FAIXA_Y1) // 2
        for k, m in enumerate(marcos):
            x = X_VIAJANTE + (k - pos) * 112
            if x < -60 or x > PX.LARG + 60: continue
            r = m.get('r', 10)
            passou = k <= pos
            tela.disco(x, cy, r, 9 if passou else 5)
            tela.anel(x, cy, r, 11 if passou else 6, 1)
            if abs(x - X_VIAJANTE) < 104:
                # o nome segue o disco mas nunca sai da tela
                tx = min(PX.LARG - 34, max(34, x))
                tela.texto_ajustado(m['nome'], tx, cy + r + 6,
                                    11 if passou else 6, 8, 100, centro=True)

        # --- a trilha percorrida e o viajante
        tela.ret(0, cy, X_VIAJANTE, 1, 3)
        rastro = int(16 + 16 * pulso)
        for j in range(rastro):
            tela.px(X_VIAJANTE - 4 - j, cy, 9 if j < 5 else (6 if j < 11 else 4))
        # o viajante é um ponto que brilha, não uma silhueta: em 4 px de
        # diâmetro qualquer desenho vira sujeira, e luz é ponto mesmo
        tela.disco(X_VIAJANTE, cy, 3 + pulso, 11)
        tela.anel(X_VIAJANTE, cy, 5 + 2 * pulso, 9, 1)

        # --- HUD: o relógio é o conteúdo
        tela.ret(0, 0, PX.LARG, FAIXA_Y0 - 28, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 8, 6, tam=9, centro=True)
        val, rot = fmt_tempo(treal, un)
        esc = 1 + .12 * pulso
        tela.texto(val, PX.LARG // 2, 30, 11, tam=int(40 * esc), centro=True, sombra=3)
        tela.texto(rot, PX.LARG // 2, 74, 8, tam=10, centro=True)

        # --- barra de distância, com um tique por marco
        tela.ret(14, BARRA_Y, PX.LARG - 28, 3, 3)
        tela.ret(14, BARRA_Y, int((PX.LARG - 28) * tl), 3, 12)
        for k in range(n):
            x = 14 + (PX.LARG - 28) * k / max(1, n - 1)
            tela.ret(int(x) - 1, BARRA_Y - 3, 2, 9, 11 if k <= pos else 5)

        # --- o cartão do marco alcançado
        if chegou:
            m = marcos[min(n - 1, int(round(pos)))]
            y = BARRA_Y + 16
            tela.ret(10, y, PX.LARG - 20, 28, 0)
            tela.ret(10, y, 2, 28, 11)
            tela.texto_ajustado(m['nome'], PX.LARG // 2, y + 4, 11, 13,
                                PX.LARG - 32, centro=True)
            vv, rr = fmt_tempo(m['t'], un)
            tela.texto(f'{vv} {rr}', PX.LARG // 2, y + 18, 8, tam=8, centro=True)
        elif u.get('rodape'):
            tela.texto_ajustado(u['rodape'], PX.LARG // 2, BARRA_Y + 22, 6, 9,
                                PX.LARG - 20, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .6 * min(1, tt / (dur * .8)))
    for k, m in enumerate(marcos):                 # um toque em cada marco
        tm = 1.2 + (dur - 5.0) * k / max(1, n - 1)
        A.put(mix, A.pop(rng, k), tm, .5)
    A.put(mix, A.correct(rng, kit['root']), dur - 3.6, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_viagem.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))

    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    som = 'MUDO' if PX.MUDO else f'{lufs} LUFS / {tp} dBTP'
    print(f'{n} marcos · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {som}')


if __name__ == '__main__':
    d = json.load(open(sys.argv[1], encoding='utf-8'))
    construir(d, seed=int(sys.argv[2]) if len(sys.argv) > 2 else 31,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-viagem')
