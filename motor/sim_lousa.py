#!/usr/bin/env python3
"""A LOUSA — desenho de traço contínuo numa lousa de dois botões.

O brinquedo tem uma regra que nenhum outro meio tem: **o traço nunca levanta**.
Um botão move na horizontal, o outro na vertical, e a diagonal sai em escada
porque são os dois girando juntos. Essa limitação é um presente para código:
o desenho inteiro é **uma lista ordenada de pontos**, e não uma grade — muito
mais barato de escrever que pixel art, e o resultado é reconhecível na hora.

A troca de desenho é o chacoalhar: a tela treme, o pó de alumínio volta a
cobrir o vidro e o traço some. É a transição mais reconhecível que existe.

**Marca:** o brinquedo original é marca registrada, e a moldura vermelha com
o logo é identidade visual protegida. Esta lousa usa a paleta do canal e não
leva nome nenhum na moldura. O mecanismo é livre; o desenho da caixa não é.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

# a lousa ocupa o meio da tela; os botões ficam no rodapé da moldura
MOLD_X, MOLD_Y, MOLD_W, MOLD_H = 6, 58, 168, 196
TELA_X, TELA_Y = MOLD_X + 10, MOLD_Y + 12
TELA_W, TELA_H = MOLD_W - 20, MOLD_H - 46

DUR = 26.0          # segundos por desenho
T_PALPITE = 6.0     # quanto tempo o desenho fica pronto antes da resposta


def escada(p0, p1, passo=1.0):
    """Liga dois pontos como o brinquedo liga: alternando horizontal e
    vertical em degraus curtos. Diagonal perfeita não existe nessa lousa."""
    pts = []
    x, y = p0
    x1, y1 = p1
    dx, dy = x1 - x, y1 - y
    n = max(1, int(max(abs(dx), abs(dy)) / passo))
    for i in range(n):
        if abs(dx) > abs(dy):
            x += dx / n; pts.append((x, y))
            y += dy / n; pts.append((x, y))
        else:
            y += dy / n; pts.append((x, y))
            x += dx / n; pts.append((x, y))
    pts.append((x1, y1))
    return pts


def caminho(pontos):
    """Transforma a lista de vértices do desenho num traço em escada,
    já em pixels da tela baixa."""
    cam = []
    for a, b in zip(pontos, pontos[1:]):
        pa = (TELA_X + a[0] / 100 * TELA_W, TELA_Y + TELA_H - a[1] / 100 * TELA_H)
        pb = (TELA_X + b[0] / 100 * TELA_W, TELA_Y + TELA_H - b[1] / 100 * TELA_H)
        cam += escada(pa, pb)
    return cam


def desenhar_lousa(tela, cor_mold, cor_vidro, cor_po, tremor=0):
    """A caixa: moldura arredondada, vidro com pó, e os dois botões."""
    mx, my = MOLD_X + tremor, MOLD_Y
    tela.ret(mx + 3, my, MOLD_W - 6, MOLD_H, cor_mold)
    tela.ret(mx, my + 3, MOLD_W, MOLD_H - 6, cor_mold)
    tela.ret(TELA_X + tremor, TELA_Y, TELA_W, TELA_H, cor_vidro)
    tela.ret(TELA_X + tremor, TELA_Y, TELA_W, 1, cor_po)       # brilho do vidro
    tela.ret(TELA_X + tremor, TELA_Y + TELA_H - 1, TELA_W, 1, cor_po)


def botao(tela, cx, cy, ang, cor, cor_marca, r=7):
    tela.disco(cx, cy, r, cor)
    tela.anel(cx, cy, r, cor_marca, 1)
    tela.linha(cx, cy, cx + math.cos(ang) * (r - 2), cy + math.sin(ang) * (r - 2),
               cor_marca)


def construir(u, seed=21, saida='lousa.mp4',
              dirsaida='out-lousa', dur=DUR):
    desenhos = u['desenhos']
    paleta = u.get('paleta', 'papelao')
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = len(desenhos) * dur
    tela = PX.Tela(paleta=paleta)
    rng = np.random.default_rng(seed * 13 + 1)
    cams = [caminho(d['pontos']) for d in desenhos]

    MOLD, VIDRO, PO, TRACO, TXT = 9, 6, 7, 1, 8

    def quadro(t, i):
        k = min(len(desenhos) - 1, int(t / dur))
        tl = t - k * dur
        d, cam = desenhos[k], cams[k]
        pulso = bat.pulso(t, .13)

        # fases: chacoalha (0-1,2s) · desenha · palpite · resposta
        t_desenho = dur - T_PALPITE - 1.4
        u = max(0.0, min(1.0, (tl - 1.4) / t_desenho))
        chacoalha = max(0.0, 1 - tl / 1.1)
        tremor = int(round(math.sin(tl * 48) * 3 * chacoalha)) if chacoalha > .02 else 0

        tela.limpar(0)
        tela.ret(0, 0, PX.LARG, PX.ALT, 2)
        desenhar_lousa(tela, MOLD, VIDRO, PO, tremor)

        # --- o traço, até onde já foi desenhado
        n = int(len(cam) * u)
        if chacoalha > .02:
            # o pó voltando: o traço anterior vira ruído e some
            resto = int(len(cams[k - 1]) * (chacoalha ** .6)) if k else 0
            for j in range(0, resto, 2):
                x, y = cams[k - 1][j]
                if rng.random() < chacoalha:
                    tela.px(x + tremor + rng.integers(-1, 2), y + rng.integers(-1, 2), PO)
        else:
            for j in range(1, n):
                x0, y0 = cam[j - 1]; x1, y1 = cam[j]
                tela.linha(x0 + tremor, y0, x1 + tremor, y1, TRACO)
            if 0 < n < len(cam):                       # a ponta que risca
                x, y = cam[n - 1]
                tela.disco(x, y, 1.6, TRACO)
                tela.px(x, y, 11)

        # --- os botões giram conforme o traço anda em x e em y
        if n > 1:
            ax = sum(abs(cam[j][0] - cam[j - 1][0]) for j in range(max(1, n - 12), n))
            ay = sum(abs(cam[j][1] - cam[j - 1][1]) for j in range(max(1, n - 12), n))
        else:
            ax = ay = 0
        gx = (cam[n - 1][0] if n else 0) * .5
        gy = (cam[n - 1][1] if n else 0) * .5
        by = MOLD_Y + MOLD_H - 13
        botao(tela, MOLD_X + 18 + tremor, by, gx + ax, MOLD, PO)
        botao(tela, MOLD_X + MOLD_W - 18 + tremor, by, gy + ay, MOLD, PO)

        # --- HUD
        tela.ret(0, 0, PX.LARG, 52, 0)
        tela.texto('ADIVINHA O DESENHO', PX.LARG // 2, 8, PO, tam=10, centro=True)
        falta = max(0.0, dur - T_PALPITE - tl)
        if u >= 1 and falta > 0:
            seg = int(math.ceil(falta))
            esc = 1 + .2 * bat.pulso(t, .1)
            tela.texto(str(seg), PX.LARG // 2, 22, 11, tam=int(24 * esc),
                       centro=True, sombra=1)
        else:
            tela.texto(f'{int(u * 100)}%', PX.LARG // 2, 24, TXT, tam=16, centro=True)

        # --- a resposta
        if tl > dur - T_PALPITE:
            a = min(1.0, (tl - (dur - T_PALPITE)) / .4)
            y = PX.ALT - 42
            tela.ret(10, y - 6, PX.LARG - 20, 26, 0)
            tela.ret(10, y - 6, 2, 26, 11)
            tela.texto_ajustado(d['nome'], PX.LARG // 2, y, 11, 16,
                                PX.LARG - 30, centro=True)
            if pulso > .6 and a > .5:
                tela.ret_vazado(10, y - 6, PX.LARG - 20, 26, 11)

        tela.ret(0, PX.ALT - 3, int(PX.LARG * (t / total)), 3, 12)
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda t: .3 + .5 * ((t % dur) / dur))
    for k in range(len(desenhos)):
        A.put(mix, A.whoosh(rng, .9, up=False), k * dur, .55)            # chacoalhar
        A.put(mix, A.correct(rng, kit['root']), k * dur + dur - T_PALPITE, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_lousa.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))

    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    som = 'MUDO' if PX.MUDO else f'{lufs} LUFS / {tp} dBTP'
    print(f'{len(desenhos)} desenhos · {nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {som}')


if __name__ == '__main__':
    b = json.load(open(sys.argv[1], encoding='utf-8'))
    construir(b['desenhos'], seed=int(sys.argv[2]) if len(sys.argv) > 2 else 21,
              paleta=b.get('paleta', 'papelao'),
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-lousa')
