#!/usr/bin/env python3
"""AUTODROMO — circuito visto de cima, carros dando voltas.

A raia paralela mostra quem é mais rápido; o circuito mostra o que isso
significa. Ao fim de duas voltas do líder, o último ainda está na primeira
curva, e **isso se vê num quadro só** — é a diferença entre ler um número e
sentir a distância.

A pista é uma curva fechada em coordenadas polares, com harmônicas sorteadas
pelo SEED: cada vídeo tem um traçado diferente sem nenhum desenho à mão. Ela
é carimbada uma vez num buffer; por quadro só os carros são desenhados.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

PISTA_Y0, PISTA_Y1 = 74, 252
N_AMOSTRAS = 1400


def tracado(seed, larg, alt):
    """Centro da pista, amostrado. r(t) com harmônicas dá curvas e retas sem
    desenhar nada à mão, e o SEED muda o circuito inteiro."""
    rng = np.random.default_rng(seed * 97 + 13)
    a2, a3, a5 = rng.uniform(.06, .20), rng.uniform(.04, .16), rng.uniform(.0, .08)
    p2, p3, p5 = rng.uniform(0, 6.3), rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    th = np.linspace(0, 2 * math.pi, N_AMOSTRAS, endpoint=False)
    r = 1 + a2 * np.sin(2 * th + p2) + a3 * np.sin(3 * th + p3) + a5 * np.sin(5 * th + p5)
    r = r / r.max()                       # normaliza: senão a harmônica estoura a área
    rx = larg * .40
    ry = (PISTA_Y1 - PISTA_Y0) * .42      # a pista cabe na faixa dela, não na tela
    x = larg / 2 + np.cos(th) * r * rx
    y = (PISTA_Y0 + PISTA_Y1) / 2 + np.sin(th) * r * ry
    d = np.concatenate([[0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    volta = d[-1] + math.hypot(x[0] - x[-1], y[0] - y[-1])
    return x, y, d, volta


def construir(u, seed=111, saida='autodromo.mp4', dirsaida='out-autodromo'):
    corr = sorted(u['corredores'], key=lambda c: -c['v'])
    n = len(corr)
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    tviagem = u.get('segundos', 24.0)
    total = 2.2 + tviagem + 5.0
    tela = PX.Tela(paleta=u.get('paleta', 'asfalto'))
    rng = np.random.default_rng(seed * 101 + 7)
    un = u.get('unidade', 'KM/H')
    voltas = u.get('voltas', 3)

    # cores escolhidas por contraste entre si, não em sequência: 6,7,8 são
    # três tons do mesmo cinza em metade das paletas e os carros somem
    CORES = [9, 12, 15, 10, 11, 6, 7, 5]
    X, Y, D, VOLTA = tracado(seed, PX.LARG, PX.ALT)
    vmax = corr[0]['v']
    # o líder completa `voltas` no tempo do vídeo; os outros, proporcional
    px_por_s = VOLTA * voltas / tviagem

    # a pista é carimbada uma vez: por quadro só os carros mudam
    fundo = PX.Tela(paleta=u.get('paleta', 'asfalto'))
    fundo.limpar(1)
    fundo.ret(0, PISTA_Y0 - 10, PX.LARG, PISTA_Y1 - PISTA_Y0 + 20, 2)
    # asfalto: duas passadas de disco ao longo da curva, a de fora mais
    # escura, fazendo a borda. Disco grande a cada amostra vira bolota — o
    # passo curto é que transforma a sequência numa faixa contínua.
    for raio, cor in ((9, 4), (7, 3)):
        for k in range(0, N_AMOSTRAS, 2):
            fundo.disco(X[k], Y[k], raio, cor)
    # zebra: tiquinhos alternados FORA da pista, na normal da curva
    for k in range(0, N_AMOSTRAS, 24):
        k2 = (k + 6) % N_AMOSTRAS
        nx, ny = X[k2] - X[k], Y[k2] - Y[k]
        m = math.hypot(nx, ny) or 1
        for lado in (-1, 1):
            fundo.ret(X[k] - ny / m * 8.5 * lado - 1, Y[k] + nx / m * 8.5 * lado - 1,
                      2, 2, 11 if (k // 24) % 2 else 15)
    for k in range(10, N_AMOSTRAS, 30):                 # eixo tracejado
        fundo.px(X[k], Y[k], 5)
    # largada
    for j in range(-9, 10):
        nx, ny = X[1] - X[0], Y[1] - Y[0]
        m = math.hypot(nx, ny) or 1
        fundo.px(X[0] - ny / m * j, Y[0] + nx / m * j, 11 if (j // 2) % 2 else 0)
    base = fundo.buf.copy()

    def pos_em(dist):
        k = int((dist % VOLTA) / VOLTA * N_AMOSTRAS) % N_AMOSTRAS
        return X[k], Y[k]

    def quadro(t, i):
        tl = max(0.0, t - 2.2)
        pulso = bat.pulso(t, .12)
        tela.buf[:] = base

        classif = []
        for k, c in enumerate(corr):
            dist = px_por_s * (c['v'] / vmax) * min(tl, tviagem)
            x, y = pos_em(dist)
            cor = CORES[k % len(CORES)]
            # rastro curto na direção do movimento
            for j in range(1, 5):
                rx, ry = pos_em(max(0, dist - j * 2.4))
                tela.px(rx, ry, cor if j < 3 else 3)
            tela.ret(x - 3, y - 3, 6, 6, 0)
            tela.ret(x - 2, y - 2, 4, 4, cor)
            tela.px(x, y, 11)
            classif.append((dist, c, cor))

        tela.ret(0, 0, PX.LARG, PISTA_Y0 - 12, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 4, 6, tam=9, centro=True)
        lider = classif[0]
        tela.texto(f'{lider[0]/VOLTA:.2f}', PX.LARG // 2, 16, 11,
                   tam=int(28 * (1 + .08 * pulso)), centro=True, sombra=3)
        tela.texto('VOLTAS DO LIDER', PX.LARG // 2, 48, 8, tam=9, centro=True)

        # classificação ao vivo
        tela.ret(0, PISTA_Y1 + 12, PX.LARG, PX.ALT - PISTA_Y1 - 12, 0)
        for j, (dist, c, cor) in enumerate(sorted(classif, key=lambda z: -z[0])[:4]):
            y = PISTA_Y1 + 16 + j * 12
            tela.ret(5, y + 1, 5, 7, cor)
            tela.texto(f'{j+1}', 13, y, 8, tam=9)
            tela.texto_ajustado(c['nome'], 24, y, 11 if j == 0 else 8, 9, 96)
            tela.texto(f"{c['v']:g} {un}", PX.LARG - 5, y, 6, tam=9, centro='d')
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .35 + .55 * min(1, tt / total))
    A.put(mix, A.riser(rng, 2.0, kit['root']), .2, .5)
    A.put(mix, A.fanfare(rng, kit['root'], kit), 2.2 + tviagem, .5)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_autodromo.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{n} carros · {voltas} voltas · {nq} quadros em {dt:.1f}s = '
          f'{nq/dt:.1f} fps ({total/dt:.2f}x tempo real) · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 111,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-autodromo')
