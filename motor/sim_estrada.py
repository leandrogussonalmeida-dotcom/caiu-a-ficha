#!/usr/bin/env python3
"""ESTRADA INFINITA — perspectiva falsa, câmera que não pára.

Estrada em pseudo-3D do jeito que o arcade fazia: para cada linha da tela,
a largura da pista sai da distância até o horizonte, e o tracejado rola por
uma coordenada de profundidade. Não há 3D nenhum — há uma conta por linha.

Serve para a série ESTRADA INFINITA e para o MODO FOCO, que é a mesma cena
em 40 minutos em vez de 20 segundos.
"""
import json, math, os, sys
import numpy as np
import pixelengine as PX
import quizaudio as A
import soundfile as sf

HOR = 128                 # o horizonte
LARG_PISTA = 150.0


def construir(u, seed=81, saida='estrada.mp4', dirsaida='out-estrada'):
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    total = u.get('segundos', 30.0)
    tela = PX.Tela(paleta=u.get('paleta', 'neon'))
    rng = np.random.default_rng(seed * 73 + 3)
    vel = u.get('velocidade', 36.0)            # unidades de profundidade por s
    km_por_u = u.get('km_por_unidade', 0.02)
    chuva = u.get('chuva', False)
    marcos = u.get('marcos', [])

    XS = np.arange(PX.LARG, dtype=np.float32)
    ys = np.arange(HOR + 1, PX.ALT)
    # z cresce para o infinito perto do horizonte: é o que dá a sensação
    zz = 1.0 / ((ys - HOR) / (PX.ALT - HOR) + 0.016)
    meia = ((ys - HOR) / (PX.ALT - HOR)) ** 1.25 * LARG_PISTA / 2 + 3

    estrelas = [(int(rng.integers(0, PX.LARG)), int(rng.integers(6, HOR - 6)),
                 int(rng.integers(0, 3))) for _ in range(90)]
    gotas = [(rng.random(), rng.random(), .4 + rng.random()) for _ in range(90)]

    def quadro(t, i):
        d = t * vel
        pulso = bat.pulso(t, .13)
        tela.limpar(0)
        # céu e sol
        tela.ret(0, 0, PX.LARG, HOR, 1)
        for ex, ey, ec in estrelas:
            tela.px(ex, ey, 9 if (ec == 2 and pulso > .6) else (6 if ec else 3))
        tela.disco(PX.LARG // 2, HOR - 26, 22, 2)
        for k in range(6):
            tela.ret(PX.LARG // 2 - 22, HOR - 36 + k * 5, 44, 2, 1)
        tela.ret(0, HOR - 1, PX.LARG, 2, 9)

        # A pista sai de comparações sobre a grade inteira, não de um laço com
        # cinco chamadas por linha: são 192 linhas por quadro e o MODO FOCO
        # precisa renderizar uma hora de vídeo.
        cx = PX.LARG / 2
        faixa = (((zz + d) * .5).astype(np.int32) % 2).astype(bool)
        dx = np.abs(XS[None, :] - cx)
        mm = meia[:, None]
        chao = np.where(faixa[:, None], 2, 1)
        asf = np.where(faixa[:, None], 4, 3)
        borda = np.where(faixa[:, None], 11, 5)
        img = np.where(dx <= mm, asf, chao)
        img = np.where(np.abs(dx - mm) <= 1.5, borda, img)
        img = np.where((dx <= 1) & faixa[:, None] & (mm > 10), 11, img)
        tela.buf[HOR + 1:PX.ALT] = img

        # postes passando, com paralaxe pela mesma profundidade
        for k in range(10):
            z = (k * 7 + 7) - (d % 7)
            if z <= .4: continue
            q = 1.0 / z
            y = int(HOR + q * (PX.ALT - HOR) * .9)
            if y <= HOR or y >= PX.ALT: continue
            m = (y - HOR) / (PX.ALT - HOR) * LARG_PISTA / 2 + 3
            h = int(q * 90)
            for sx in (cx - m - 6, cx + m + 4):
                tela.ret(sx, y - h, max(1, int(q * 7)), h, 5)
                tela.ret(sx - 1, y - h, max(2, int(q * 10)), max(1, int(q * 10)), 9)

        if chuva:
            for gx, gy, gv in gotas:
                x = (gx * PX.LARG - t * 14) % PX.LARG
                y = (gy * PX.ALT + t * 420 * gv) % PX.ALT
                tela.ret(x, y, 1, int(4 + 6 * gv), 6)

        # --- HUD
        km = d * km_por_u
        tela.ret(0, 0, PX.LARG, 56, 0)
        tela.texto(u['titulo'], PX.LARG // 2, 3, 6, tam=9, centro=True)
        tela.texto(f'{km:.1f}'.replace('.0', ''), PX.LARG // 2, 15, 11,
                   tam=int(26 * (1 + .08 * pulso)), centro=True, sombra=3)
        tela.texto('KM', PX.LARG // 2, 45, 8, tam=9, centro=True)
        for mk in marcos:
            if abs(km - mk['km']) < .9:
                tela.ret(8, PX.ALT - 34, PX.LARG - 16, 24, 0)
                tela.ret(8, PX.ALT - 34, 2, 24, 11)
                tela.texto_ajustado(mk['nome'], PX.LARG // 2, PX.ALT - 28, 11,
                                    12, PX.LARG - 28, centro=True)
                break
        return tela

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .34 + .4 * min(1, tt / 12))
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_estrada.wav')
    sf.write(wav, mix, PX.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    import time
    t0 = time.time()
    nq = PX.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f'{nq} quadros em {dt:.1f}s = {nq/dt:.1f} fps '
          f'({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS')


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 81,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-estrada')
