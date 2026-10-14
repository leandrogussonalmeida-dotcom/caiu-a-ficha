#!/usr/bin/env python3
"""ESCALA — duas coisas lado a lado, uma crescendo contra a outra.

O mecanismo: a referência fica parada e o desafiante cresce até a altura
verdadeira. Quando o desafiante não cabe mais, a câmera afasta e **a
referência encolhe** — é o encolhimento que dói, não o crescimento. Um
Cristo Redentor virando um tracinho ao lado do Burj Khalifa diz mais que
qualquer número.

O contador sobe na batida. Como de costume, o instante da batida é calculado,
não detectado.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import formas as F
import soundfile as sf

CHAO = 286                 # linha do chão, em pixels da tela baixa
TOPO = 74                  # altura útil começa aqui (abaixo do HUD)
DUR_UNIDADE = 30.0         # segundos por comparação


def fase(t, dur=DUR_UNIDADE):
    """Reparte a unidade: entra a referência, entra o desafiante, cresce,
    assenta. Devolve o quanto de cada fase já passou."""
    return dict(ref=min(1.0, t / 1.6),
                alvo=min(1.0, max(0.0, (t - 2.0) / 1.4)),
                cresce=min(1.0, max(0.0, (t - 4.2) / (dur - 12.0))),
                ancora=min(1.0, max(0.0, (t - dur + 8.5) / 1.2)),
                saida=min(1.0, max(0.0, (t - dur + 1.0) / 1.0)))


def desenhar_unidade(tela, bat, u, t, pal_cores, dur=DUR_UNIDADE):
    """Um quadro de uma comparação."""
    f = fase(t, dur)
    ref, alvo = u['ref'], u['alvo']
    razao = alvo['valor'] / max(1e-9, ref['valor'])

    # quanto da razão já foi revelada; passa do ponto e volta, para o número
    # final "bater" em vez de chegar escorregando
    e = 1 - (1 - f['cresce']) ** 3
    razao_agora = 1 + (razao - 1) * e

    alt_util = CHAO - TOPO
    # a escala que mantém o desafiante dentro da área útil
    px_por_ref = min(alt_util * .34, alt_util / max(1.0, razao_agora))
    h_ref = max(2, int(px_por_ref))
    h_alvo = max(2, int(px_por_ref * razao_agora))

    corpo, claro, escuro = pal_cores
    pulso = bat.pulso(t, .12)

    # --- chão
    tela.ret(0, CHAO, PX.LARG, PX.ALT - CHAO, escuro)
    tela.ret(0, CHAO, PX.LARG, 1, claro)

    # --- régua: um traço por referência empilhada, enquanto couber
    if h_ref >= 4 and razao_agora > 1.5:
        marcas = min(40, int(razao_agora))
        for k in range(1, marcas + 1):
            y = CHAO - k * h_ref
            if y < TOPO: break
            tela.ret(86, y, 5, 1, corpo)

    # --- a referência, parada à esquerda
    if f['ref'] > 0:
        a = 1 - (1 - f['ref']) ** 3
        F.desenhar(tela, ref['forma'], 44, CHAO - int((1 - a) * 40),
                   max(2, int(h_ref * a)), (corpo, claro, escuro), larg_max=72)

    # --- o desafiante, crescendo à direita
    if f['alvo'] > 0:
        a = 1 - (1 - f['alvo']) ** 3
        F.desenhar(tela, alvo['forma'], 132, CHAO, max(2, int(h_alvo * a)),
                   (claro, 11, corpo), larg_max=78)

    # --- rodapé com os dois rótulos, por cima de tudo
    tela.ret(0, CHAO + 1, PX.LARG, PX.ALT - CHAO - 1, escuro)
    tela.ret(88, CHAO + 4, 1, 22, corpo)
    if f['ref'] > 0:
        tela.texto_ajustado(ref['nome'], 44, CHAO + 5, claro, 8, 84, centro=True)
        tela.texto(f"{ref['valor']:g} {ref['un']}", 44, CHAO + 15, corpo, tam=8, centro=True)
    if f['alvo'] > 0:
        tela.texto_ajustado(alvo['nome'], 132, CHAO + 5, 11, 8, 86, centro=True)
        tela.texto(f"{alvo['valor']:g} {alvo['un']}", 132, CHAO + 15, corpo, tam=8, centro=True)

    # --- HUD: a razão é o conteúdo
    tela.ret(0, 0, PX.LARG, TOPO - 10, 0)
    tela.ret(0, TOPO - 10, PX.LARG, 1, escuro)
    n = razao_agora
    txt = f'{n:.0f}' if n >= 10 else f'{n:.1f}'.replace('.0', '')
    esc = 1 + .16 * pulso * f['cresce']
    tela.texto(txt, PX.LARG // 2, 16, 11, tam=int(34 * esc), centro=True, sombra=escuro)
    # O plural vem da unidade. Em português ele não se deriva: PAO vira
    # PAES, ONIBUS não muda, e cortar a primeira palavra e colar um S
    # produziu "6,9 PAOS" no vídeo das montanhas.
    tela.texto(ref.get('rotulo') or f"{ref['nome'].split()[0]}S".replace('SS', 'S'),
               PX.LARG // 2, 52, claro, tam=9, centro=True)

    # --- a âncora, no fim
    if f['ancora'] > 0:
        a = 1 - (1 - f['ancora']) ** 3
        y = CHAO - 26 + int((1 - a) * 14)
        tela.ret(5, y - 5, PX.LARG - 10, 19, 0)
        tela.ret(5, y - 5, 2, 19, 11)
        tela.texto_ajustado(u['ancora'], PX.LARG // 2, y, claro, 10, PX.LARG - 22, centro=True)


def construir(u, seed=11, saida='escala.mp4',
              dirsaida='out-escala', dur=DUR_UNIDADE):
    # contrato único de todos os simuladores: recebem a unidade inteira e
    # tiram dela a aparência. Enquanto este aqui recebia a lista e a paleta
    # soltas, o executor passava o dicionário sem reclamar e o vídeo saía
    # vazio — com 'ok' no relatório.
    unidades = u['unidades']
    paleta = u.get('paleta', 'gelo')
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = len(unidades) * dur
    tela = PX.Tela(paleta=paleta)
    rng = np.random.default_rng(seed * 17 + 3)
    estrelas = [(int(rng.integers(0, PX.LARG)), int(rng.integers(TOPO, CHAO)),
                 int(rng.integers(0, 3))) for _ in range(90)]
    cores = (6, 8, 2)

    def quadro(t, i):
        k = min(len(unidades) - 1, int(t / dur))
        tl = t - k * dur
        tela.limpar(0)
        tela.ret(0, 0, PX.LARG, PX.ALT, 1)
        p = bat.pulso(t, .14)
        for ex, ey, ec in estrelas:                      # céu que pisca na batida
            tela.px(ex, ey, 6 if (ec == 2 and p > .6) else (3 if ec else 2))
        desenhar_unidade(tela, bat, unidades[k], tl, cores, dur)
        tela.ret(0, PX.ALT - 3, int(PX.LARG * (t / total)), 3, 12)
        return tela

    def energia(t):
        tl = (t % dur) / dur
        return .35 + .55 * min(1.0, tl / .72)

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, energia)
    for k in range(len(unidades)):                        # marca a virada de unidade
        A.put(mix, A.whoosh(rng, .5, up=True), k * dur - .4, .5)
        A.put(mix, A.correct(rng, kit['root']), k * dur + dur - 6.4, .45)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_escala.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))

    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    som = 'MUDO' if PX.MUDO else f'{lufs} LUFS / {tp} dBTP'
    print(f'{len(unidades)} unidades · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {bat.bpm:.0f}bpm · {som}')


if __name__ == '__main__':
    us = json.load(open(sys.argv[1], encoding='utf-8'))
    construir(us['unidades'], seed=int(sys.argv[2]) if len(sys.argv) > 2 else 11,
              paleta=us.get('paleta', 'gelo'),
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-escala')
