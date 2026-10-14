#!/usr/bin/env python3
"""O TRAÇO — adivinhe o desenho, a nanquim sobre papel.

Lê **o mesmo arquivo** da `sim_lousa`: um desenho é uma lista ordenada de
pontos numa caixa de 0 a 100. A mesma lista, aqui, vira outro vídeo.

A lousa tem uma regra: o traço nunca levanta e a diagonal sai em escada,
porque são dois botões girando juntos. A tinta tem a regra oposta — uma mão
segura a pena, e mão **treme**. Toda a linguagem está nisso:

- a linha ondula, com um ruído suave e contínuo ao longo do caminho (não
  por quadro: um traço que treme a cada quadro é chiado, não é mão);
- a pena **pesa** — engrossa onde desacelera, afina onde corre, e deixa um
  acúmulo nas quinas, onde a mão hesita;
- a tinta **acumula**: o traço feito não é redesenhado, fica no papel.

É o mesmo dado da série B saindo em duas linguagens que não se parecem. Isso
é o que torna 125 desenhos em 250 vídeos sem escrever um desenho a mais.
"""
import json, math, os, sys, time
import numpy as np
import altaengine as AL
import pixelengine as PX
import quizaudio as A
import soundfile as sf

CX, CY, LADO = AL.LARG / 2, 920, 900      # a área do papel onde se desenha
DUR = 24.0                                 # segundos por desenho
T_PALPITE = 5.5                            # tempo parado antes da resposta


def tremido(pts, rng, amp=1.1, passo=1.6):
    """Reamostra o caminho a passo constante e empurra cada ponto na
    perpendicular por um ruído **suave ao longo do caminho**. É a diferença
    entre uma linha desenhada à mão e uma linha com chiado."""
    denso = []
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(d / passo))
        for i in range(n):
            f = i / n
            denso.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    denso.append(tuple(pts[-1]))
    if len(denso) < 3: return denso, [0.0]

    # ruído suave: soma de poucas senoides com fases sorteadas. Barato, e
    # sem a descontinuidade que um random por ponto deixaria.
    m = len(denso)
    s = np.arange(m, dtype=np.float32)
    on = np.zeros(m, np.float32)
    for k, (per, pes) in enumerate(((23.0, 1.0), (9.0, .45), (41.0, .7))):
        on += pes * np.sin(s / per * 2 * math.pi + rng.random() * 6.283)
    on *= amp / 2.15

    saida, curv = [], []
    for i, (x, y) in enumerate(denso):
        a = denso[max(0, i - 1)]
        b = denso[min(m - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1.0
        px, py = -dy / n, dx / n          # a perpendicular ao caminho
        saida.append((x + px * on[i], y + py * on[i]))
        # quina = mudança brusca de direção. A pena engrossa onde a mão para.
        c = denso[max(0, i - 3)]
        d = denso[min(m - 1, i + 3)]
        v1 = (x - c[0], y - c[1]); v2 = (d[0] - x, d[1] - y)
        n1 = math.hypot(*v1) or 1.0; n2 = math.hypot(*v2) or 1.0
        cos = (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)
        curv.append(max(0.0, 1.0 - cos))
    return saida, curv


def construir(u, seed=71, saida='traco.mp4', dirsaida='out-traco'):
    des = u['desenhos']
    n = len(des)
    est = AL.ESTILOS[u.get('estilo', 'jornal')]
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = 2.0 + n * DUR + 3.0
    rng = np.random.default_rng(seed * 29 + 11)
    q = AL.Quadro(est)

    # cada desenho vira um caminho tremido, já em pixels da folha.
    # Um ponto nulo é a pena LEVANTANDO: a lousa não pode levantar o traço
    # (é a regra do brinquedo), mas uma pena pode, e sem isso todo detalhe
    # desenhado depois do contorno deixava um risco atravessando a figura.
    cams = []
    for d in des:
        pts = [None if (px is None or py is None) else
               (CX - LADO / 2 + px / 100 * LADO, CY + LADO / 2 - py / 100 * LADO)
               for px, py in d['pontos']]
        # cada trecho entre levantadas e tremido por si; o comprimento
        # acumulado atravessa os trechos para a mao nao acelerar nos saltos
        p, c, comp, saltos = [], [], [0.0], set()
        trecho, rg = [], np.random.default_rng(seed * 7 + len(cams))
        def fechar():
            if len(trecho) < 2: return
            tp, tc = tremido(trecho, rg, amp=LADO * .0030)
            if p: saltos.add(len(p))
            for pt in tp:
                if p: comp.append(comp[-1] + math.hypot(pt[0] - p[-1][0],
                                                        pt[1] - p[-1][1]))
                p.append(pt)
            c.extend(tc)
        # `pt`, nao `q`: `q` e a tela, e um `for q in pts` aqui sobrescrevia
        # a tela com uma tupla. O erro so aparecia 1.800 quadros depois.
        for pt in pts:
            if pt is None:
                fechar(); trecho = []
            else:
                trecho.append(pt)
        fechar()
        cams.append((p, c, comp, saltos))

    def caneta(px, py, pulso):
        """A pena. Precisa ser lida como pena no tamanho de miniatura, senão
        vira um risco solto no meio da folha — que foi o que ela era."""
        ux, uy = .46, -.89                       # inclinação da mão
        def P(d, lat=0.0):
            return (px + ux * d - uy * lat, py + uy * d + ux * lat)
        # a ponta: um bico que afina até o papel
        q.d.polygon([(q.s(a), q.s(b)) for a, b in
                     (P(0), P(44, 11), P(96, 9), P(96, -9), P(44, -11))],
                    fill=est.tinta)
        # o corpo, mais claro, e o anel
        q.d.polygon([(q.s(a), q.s(b)) for a, b in
                     (P(96, 13), P(250, 15), P(262, 0), P(250, -15), P(96, -13))],
                    fill=est.suave)
        q.linha(*P(112, 15), *P(112, -15), est.tinta, 5)
        q.linha(*P(236, 14), *P(236, -14), est.tinta, 4)
        # o ponto de tinta onde a pena toca
        q.circulo(px, py, 5 + 3 * pulso, est.acento)

    estado = {'k': -1, 'ate': 0}

    def quadro(t, i):
        tl = max(0.0, t - 2.0)
        k = min(n - 1, int(tl / DUR))
        tk = tl - k * DUR
        pulso = bat.pulso(t, .12)
        pts, curv, comp, saltos = cams[k]
        L = comp[-1]
        # desenhar ocupa tudo menos o palpite e a resposta
        t_des = DUR - T_PALPITE - 3.0
        prog = max(0.0, min(1.0, tk / t_des))
        alvo = prog * L

        if k != estado['k']:                 # folha nova: limpa e recomeça
            estado['k'], estado['ate'] = k, 0
            q._base = None
            q.limpar()
            q.fixar()
        else:
            q.limpar()

        # --- a tinta nova deste quadro, e só ela
        j = estado['ate']
        novo = j
        while novo + 1 < len(pts) and comp[novo + 1] <= alvo:
            novo += 1
        if novo > j:
            for m in range(j, novo):
                if m + 1 in saltos:        # aqui a pena estava no ar
                    continue
                # a pena pesa na quina e no começo do traço
                esp = 5.0 + 4.2 * min(1.0, curv[m] * 2.4)
                q.linha(pts[m][0], pts[m][1], pts[m + 1][0], pts[m + 1][1],
                        est.tinta, esp)
            estado['ate'] = novo
            q.fixar()                        # a tinta fica no papel

        # --- a pena: efêmera, redesenhada todo quadro por cima
        if prog < 1.0 and estado['ate'] < len(pts) - 1:
            caneta(*pts[estado['ate']], pulso)

        # --- HUD
        q.texto(u['titulo'], AL.LARG / 2, 150, est.suave, 32,
                fonte=est.fonte_rot, anc='ma', espaco=4)
        q.texto(f'{k+1:02d}/{n:02d}', AL.LARG / 2, 212, est.acento, 30,
                fonte=est.fonte_rot, anc='ma')

        if prog < 1.0:
            q.ajustar('O QUE E ISSO?', AL.LARG / 2, 1530, est.suave, 54,
                      AL.LARG - 140, anc='ma')
        elif tk < t_des + T_PALPITE:
            # a contagem: o único momento em que o espectador tem de decidir
            resta = t_des + T_PALPITE - tk
            q.ajustar('PALPITE AGORA', AL.LARG / 2, 1500, est.suave, 46,
                      AL.LARG - 140, anc='ma')
            r = 52 + 10 * pulso
            q.circulo(AL.LARG / 2, 1640, r, borda=est.acento, esp=5)
            q.texto(str(int(resta) + 1), AL.LARG / 2, 1640 - 34, est.tinta, 62,
                    fonte=est.fonte_num, anc='ma')
        else:
            esc = 1 + .08 * pulso
            q.ajustar(des[k]['nome'], AL.LARG / 2, 1520, est.acento,
                      int(104 * esc), AL.LARG - 120, anc='ma', fonte=est.fonte_num)

        q.linha(140, 1760, AL.LARG - 140, 1760, est.linha, 1.4)
        q.texto('CAIU A FICHA', AL.LARG / 2, 1786, est.suave, 26,
                fonte=est.fonte_rot, anc='ma', espaco=5)
        return q.render(i)

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .28 + .5 * min(1, tt / total))
    for j in range(n):
        A.put(mix, A.tick(rng, j, n), 2.0 + j * DUR + DUR - T_PALPITE - 3.0, .55)
        A.put(mix, A.fanfare(rng, kit['root'], kit), 2.0 + j * DUR + DUR - 3.0, .4)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_traco.wav')
    sf.write(wav, mix, AL.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    t0 = time.time()
    nq = AL.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f"{n} desenhos · estilo {est.nome} · {nq} quadros em {dt:.1f}s = "
          f"{nq/dt:.1f} fps ({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS")


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 71,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-traco')
