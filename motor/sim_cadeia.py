#!/usr/bin/env python3
"""CADEIA — um vira dois, dois viram quatro, e em pouca geração não cabe mais.

O problema do crescimento exponencial na tela: até a geração 12 cabe tudo, e
daí em diante não cabe nada. A saída é trocar de registro no meio do caminho:
**enquanto dá para contar, mostra os pontos; quando não dá, a tela vira massa
sólida e o número toma conta.** A virada é o momento mais forte do vídeo.

Cada geração cai numa batida.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

TOPO, BASE = 84, 262
CAP = 2600                 # acima disso a tela vira massa


def humano(n):
    """O número em palavra: 4 bilhões diz mais que 4.294.967.296."""
    if n < 1000: return f'{int(n)}', ''
    if n < 1e6: return f'{n/1e3:.1f}'.replace('.0', ''), 'MIL'
    if n < 1e9: return f'{n/1e6:.1f}'.replace('.0', ''), 'MILHOES'
    if n < 1e12: return f'{n/1e9:.1f}'.replace('.0', ''), 'BILHOES'
    if n < 1e15: return f'{n/1e12:.1f}'.replace('.0', ''), 'TRILHOES'
    e = int(math.log10(n))
    return f'10^{e}', ''


def construir(u, seed=41, saida='cadeia.mp4', dirsaida='out-cadeia'):
    ger = u['geracoes']
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    por_ger = u.get('por_geracao', 2)          # batidas por geração
    dur_ger = bat.spb * por_ger
    total = 2.0 + ger * dur_ger + 4.0
    tela = PX.Tela(paleta=u.get('paleta', 'brasa'))
    rng = np.random.default_rng(seed * 37 + 1)

    # posição de cada ponto: a cada geração o espaço se divide em dois
    _a = rng.random(CAP) * math.tau
    _d = np.sqrt(rng.random(CAP))
    PX_X = (PX.LARG / 2 + np.cos(_a) * _d * PX.LARG * .44).astype(np.int32)
    PX_Y = ((TOPO + BASE) / 2 + np.sin(_a) * _d * (BASE - TOPO) * .46).astype(np.int32)

    # O ruído da massa é GROSSO de propósito, em blocos de 3 px e trocando a
    # cada 3 quadros. Ruído fino por pixel é incompressível: o x264 engasgava
    # e o render caía de 1,3x para 0,4x do tempo real, sem ficar melhor — em
    # 8 bits o grão grosso até lê melhor.
    ALT_M = BASE - TOPO + 8
    GR = 3
    ruidos = [np.repeat(np.repeat(rng.random((ALT_M // GR + 1, PX.LARG // GR + 1)),
                                  GR, 0), GR, 1)[:ALT_M, :PX.LARG] for _ in range(6)]

    def quadro(t, i):
        tl = max(0.0, t - 2.0)
        g = min(ger, int(tl / dur_ger))
        frac = min(1.0, (tl / dur_ger) - g) if g < ger else 1.0
        n = 2 ** g
        pulso = bat.pulso(t, .12)

        tela.limpar(0)
        tela.ret(0, TOPO - 4, PX.LARG, BASE - TOPO + 8, 1)

        if n <= CAP:
            vis = int(n * (1 if frac > .5 else .5 + frac))
            # os pontos saem de uma só atribuição por deslocamento, não de
            # um laço Python: 2.600 chamadas por quadro derrubavam o render de
            # 1,3x para 0,4x do tempo real
            lado = 5 if n < 64 else (3 if n < 512 else 2)
            vis = min(CAP, vis)
            meio = min(vis, n // 2)
            for fatia, cor, extra in ((slice(0, meio), 6, 0),
                                      (slice(meio, vis),
                                       11 if pulso > .4 else 9,
                                       2 if pulso > .5 else 0)):
                X, Y = PX_X[fatia], PX_Y[fatia]
                if not len(X): continue
                L = lado + extra
                for dy in range(L):
                    yy = np.clip(Y - L // 2 + dy, 0, PX.ALT - 1)
                    for dx in range(L):
                        tela.buf[yy, np.clip(X - L // 2 + dx, 0, PX.LARG - 1)] = cor
        else:
            # massa: não cabe mais um ponto, então a tela satura e fica
            # fervendo. Vazio com pontinhos leria como pouco; tem que ferver.
            sat = min(1.0, math.log2(n / CAP) / 8)
            tela.ret(0, TOPO - 4, PX.LARG, BASE - TOPO + 8, 5 if sat < .5 else 6)
            ruido = ruidos[(i // 3) % 6]
            lim = .34 + .34 * sat + .14 * pulso
            faixa = tela.buf[TOPO - 4:TOPO - 4 + ALT_M]
            faixa[ruido < lim * .55] = 9
            faixa[ruido > 1 - lim * .3] = 11

        # --- HUD
        tela.ret(0, 0, PX.LARG, TOPO - 6, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 6, 6, tam=9, centro=True)
        val, un = humano(n)
        esc = 1 + .16 * pulso
        tela.texto(val, PX.LARG // 2, 22, 11, tam=int(36 * esc), centro=True, sombra=3)
        if un: tela.texto(un, PX.LARG // 2, 62, 8, tam=11, centro=True)
        tela.ret(0, BASE + 8, PX.LARG, 1, 3)
        tela.texto(f'GERACAO {g}', PX.LARG // 2, BASE + 14, 8, tam=11, centro=True)
        if g >= ger:
            tela.texto_ajustado(u['fecho'], PX.LARG // 2, BASE + 32, 11, 11,
                                PX.LARG - 16, centro=True)
        elif u.get('rodape'):
            tela.texto_ajustado(u['rodape'], PX.LARG // 2, BASE + 32, 6, 9,
                                PX.LARG - 16, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .6 * min(1, tt / total))
    for k in range(ger + 1):
        A.put(mix, A.pop(rng, min(11, k)), 2.0 + k * dur_ger, .42)
    A.put(mix, A.fanfare(rng, kit['root'], kit), total - 4.2, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_cadeia.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{ger} geracoes · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 41,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-cadeia')
