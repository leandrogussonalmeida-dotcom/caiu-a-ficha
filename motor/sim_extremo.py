#!/usr/bin/env python3
"""O LIMITE — uma escada vertical de valores, com o ponteiro subindo.

Diferente da VIAGEM, aqui **a escada inteira fica à vista desde o começo**.
O espectador vê quanto falta, e é isso que segura: ele quer chegar no topo.
A escala é logarítmica, senão a vela e o raio ficam no mesmo pixel.

Serve para calor, frio, pressão, profundidade e velocidade — muda só a
unidade e o sentido.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

TOPO, BASE = 96, 268
EIXO_X = 132


def construir(u, seed=51, saida='extremo.mp4', dirsaida='out-extremo'):
    passos = u['passos']
    n = len(passos)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    por = u.get('batidas_por_passo', 4)
    dp = bat.spb * por
    total = 2.0 + n * dp + 4.0
    tela = PX.Tela(paleta=u.get('paleta', 'brasa'))
    rng = np.random.default_rng(seed * 43 + 3)
    desc = u.get('descendo', False)
    un = u.get('unidade', '')

    # a escada sobe em ordem de valor, sempre: lista fora de ordem faz o
    # ponteiro andar para trás e desmonta a leitura
    passos = sorted(passos, key=lambda p: p['v'], reverse=bool(u.get('descendo')))
    vals = [p['v'] for p in passos]
    # log puro quando tudo é positivo. Com um deslocamento grande o log vira
    # quase linear e esmaga a base — 37, 100 e 250 caíam no mesmo pixel.
    # Escala LINEAR para grandezas que JA SAO logaritmicas: decibel, pH,
    # Richter. Passar decibel pelo log seria log de log, e a escada sairia
    # mentindo - alem de 0 dB quebrar o log10. Nessas, cada degrau igual na
    # tela ja representa um salto de dez vezes na energia, que e o que a
    # unidade significa.
    linear = u.get('escala') == 'linear'
    if linear:
        lo, hi = min(vals), max(vals)
        marg = (hi - lo) * .04 or 1.0
        lo, hi = lo - marg, hi + marg

        def ypos(v):
            q = (v - lo) / max(1e-9, hi - lo)
            return BASE - q * (BASE - TOPO) if not desc else TOPO + q * (BASE - TOPO)
    else:
        base0 = 0.0 if min(vals) > 0 else min(vals) - (max(vals) - min(vals)) * .02 - 1e-6
        lg = [math.log10(max(1e-9, v - base0)) for v in vals]
        lo, hi = min(lg), max(lg)

        def ypos(v):
            q = (math.log10(max(1e-9, v - base0)) - lo) / max(1e-9, hi - lo)
            return BASE - q * (BASE - TOPO) if not desc else TOPO + q * (BASE - TOPO)

    def fmt(v):
        a = abs(v)
        if a >= 1e6: return f'{v/1e6:.1f}'.replace('.0', '') + 'M'
        if a >= 10000: return f'{v/1000:.0f}' + 'K'
        if a >= 10: return f'{v:.0f}'
        return f'{v:.1f}'.replace('.0', '')

    def quadro(t, i):
        tl = max(0.0, t - 2.0)
        pos = min(n - 1, tl / dp)
        k = int(pos)
        frac = pos - k
        v = vals[k] + (vals[min(n - 1, k + 1)] - vals[k]) * (1 - (1 - frac) ** 3)
        pulso = bat.pulso(t, .12)
        y = ypos(v)

        tela.limpar(0)
        # o fundo esquenta (ou esfria) conforme sobe
        q = (y - TOPO) / (BASE - TOPO)
        tela.ret(0, TOPO - 8, PX.LARG, BASE - TOPO + 16, 1)
        quente = int(max(0, min(4, (1 - q) * 5))) if not desc else int(max(0, min(4, q * 5)))
        if quente: tela.ret(0, TOPO - 8, PX.LARG, BASE - TOPO + 16, 1 + quente // 2)

        # a escada: todos os degraus à vista
        tela.ret(EIXO_X, TOPO - 6, 2, BASE - TOPO + 12, 3)
        # rótulo só entra se não encostar no anterior; o degrau atual tem
        # prioridade e empurra o vizinho para fora
        # prioridade: o degrau em destaque primeiro, depois o atual, depois o
        # resto. O item de que o vídeo trata nunca pode perder o rótulo para
        # um vizinho — foi o que aconteceu com o BRASIL no primeiro render.
        atual_j = min(n - 1, int(round(pos)))
        dest = [j for j, p in enumerate(passos) if p.get('destaque')]
        ocupado = []
        ordem = dest + [atual_j] + [j for j in range(n) if j != atual_j and j not in dest]
        rotulos = {}
        for j in ordem:
            yj = int(ypos(passos[j]['v']))
            if all(abs(yj - o) >= 11 for o in ocupado):
                ocupado.append(yj); rotulos[j] = yj
        for j, p in enumerate(passos):
            yj = int(ypos(p['v']))
            feito = j <= pos
            d = p.get('destaque')
            cor_m = 9 if d else (11 if feito else 5)
            tela.ret(EIXO_X - (12 if d else 8), yj, 26 if d else 18, 1, cor_m)
            if d: tela.ret(EIXO_X - 12, yj - 1, 26, 3, 9)
            if j in rotulos:
                tela.texto_ajustado(p['nome'], EIXO_X - (18 if d else 14), yj - 4,
                                    cor_m, 10 if d else 9, 108, centro='d')
                tela.texto(fmt(p['v']), EIXO_X + (20 if d else 14), yj - 4,
                           cor_m if d else (8 if feito else 4), tam=8)

        # a coluna preenchida e o ponteiro
        if not desc:
            tela.ret(EIXO_X - 2, y, 6, BASE - y + 2, 9)
        else:
            tela.ret(EIXO_X - 2, TOPO, 6, y - TOPO, 9)
        tela.ret(EIXO_X - 6, int(y) - 1, 14, 3, 11)
        tela.disco(EIXO_X + 1, y, 3 + 2 * pulso, 11)

        # --- HUD
        tela.ret(0, 0, PX.LARG, TOPO - 10, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 6, 6, tam=9, centro=True)
        esc = 1 + .12 * pulso
        tela.texto(fmt(v), PX.LARG // 2, 24, 11, tam=int(38 * esc), centro=True, sombra=3)
        tela.texto(un, PX.LARG // 2, 66, 8, tam=12, centro=True)
        tela.ret(0, BASE + 14, PX.LARG, 1, 3)
        atual = passos[min(n - 1, int(round(pos)))]
        tela.texto_ajustado(atual.get('nota', atual['nome']), PX.LARG // 2,
                            BASE + 22, 8, 11, PX.LARG - 16, centro=True)
        if pos >= n - 1 and u.get('fecho'):
            tela.texto_ajustado(u['fecho'], PX.LARG // 2, BASE + 38, 11, 11,
                                PX.LARG - 16, centro=True)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .6 * min(1, tt / total))
    for j in range(n):
        A.put(mix, A.tick(rng, j, n), 2.0 + j * dp, .5)
    A.put(mix, A.fanfare(rng, kit['root'], kit), total - 4.2, .45)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_extremo.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{n} passos · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 51,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-extremo')
