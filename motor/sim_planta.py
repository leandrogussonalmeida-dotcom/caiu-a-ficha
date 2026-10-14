#!/usr/bin/env python3
"""A PRANCHETA — a mesma comparação de escala, desenhada como projeto técnico.

É o primeiro simulador do segundo idioma visual. A conta é a mesma do
`sim_escala`: dois objetos, o de referência e o desafiante, na mesma escala,
com a câmera abrindo para caber o maior — e por isso a referência **encolhe**
na tela enquanto o desafiante cresce. O que muda é tudo o resto.

Aqui nada é preenchido: o objeto é contorno de linha fina, com linhas de
chamada tracejadas saindo das extremidades e uma cota com setas medindo a
altura. O desenho não aparece pronto, ele é **traçado** — um retângulo por
vez, na batida, como quem risca na prancheta. O número da cota sobe junto.

Rodar o mesmo dado em 8 bits e em planta é a defesa contra a repetição: 280
peças no mesmo serrilhado são uma peça repetida 280 vezes.
"""
import json, math, os, sys, time
import numpy as np
import altaengine as AL
import formas as FM
import pixelengine as PX
import quizaudio as A
import soundfile as sf

TOPO, CHAO = 430, 1430          # a faixa onde o desenho vive
MARGEM = 96


LADO_W = 480                    # a largura util de cada metade do desenho


def _cx(lado):
    return 270 if lado == 0 else 810


def _razao_larg(nome):
    """Quanto a forma e larga por unidade de altura. O Cristo de bracos
    abertos tem 92 de largura numa caixa de 100: escalado so pela altura ele
    sai da folha pelos dois lados."""
    rs = FM.FORMAS.get(nome, FM.FORMAS['predio'])
    return max(r[0] + r[2] for r in rs) / 100.0


def construir(u, seed=61, saida='planta.mp4', dirsaida='out-planta'):
    pares = u['unidades']
    n = len(pares)
    est = AL.ESTILOS[u.get('estilo', 'planta')]
    kit = A.pick_kit(seed)
    bat = PX.Batida(kit['bpm'])
    por = u.get('batidas_por_passo', 8)
    dp = bat.spb * por
    total = 2.0 + n * dp + 4.0
    rng = np.random.default_rng(seed * 17 + 5)
    q = AL.Quadro(est)

    def fmt(v):
        if v >= 1e6: return f'{v/1e6:.1f}'.replace('.0', '') + ' mi'
        if v >= 1000: return f'{v:,.0f}'.replace(',', '.')
        return f'{v:.0f}' if abs(v - round(v)) < .05 else f'{v:.1f}'.replace('.', ',')

    def medida(x, ytopo, txt, cor, dentro):
        """A medida vai **acima** da linha de chamada, como em prancheta de
        verdade — nao ao lado da cota. Ao lado ela ou cai em cima do objeto
        ou sai pela borda, que foi o que aconteceu com os 700 M do morro."""
        q.texto(txt, x + (10 if dentro > 0 else -10), ytopo - 40, cor, 28,
                fonte=est.fonte_rot, anc='la' if dentro > 0 else 'ra')

    def silhueta(nome, cx, base, alt, prog, cor, esp):
        """Desenha a forma em contorno, revelando um retângulo por vez.
        Em planta o objeto não é massa, é borda: é isso que diferencia um
        desenho técnico de um infográfico.

        A altura é a escala verdadeira — é ela que a cota mede e é dela que
        o vídeo fala. A largura é só desenho, então quando uma forma larga
        (o morro, os braços abertos) não cabe na metade dela, ela é
        **achatada na horizontal** em vez de encolher inteira. Encolher
        inteira era pior: deixava o desenho do tamanho de um selo no meio
        de uma folha vazia."""
        rs = FM.FORMAS.get(nome, FM.FORMAS['predio'])
        ky = alt / 100.0
        kx = min(ky, LADO_W / max(1e-6, max(r[0] + r[2] for r in rs) * ky)) * ky
        kx = max(kx, ky * .58)
        larg = max(r[0] + r[2] for r in rs) * kx
        x0 = cx - larg / 2
        m = len(rs) * prog
        for j, (rx, ry, rw, rh, tom) in enumerate(rs):
            f = max(0.0, min(1.0, m - j))
            if f <= 0: break
            c = cor if tom != 1 else est.acento
            q.ret(x0 + rx * kx, base - (ry + rh * f) * ky, rw * kx, rh * f * ky,
                  None, borda=c, esp=esp)

    def quadro(t, i):
        tl = max(0.0, t - 2.0)
        pos = min(n - 1e-6, tl / dp)
        j = int(pos)
        f = pos - j
        par = pares[j]
        vr = float(par['ref']['valor'])
        valvo = float(par['alvo']['valor'])
        # o desafiante cresce com folga no fim para a cota assentar
        cres = 1 - (1 - min(1.0, f / .62)) ** 3
        va = max(vr * .04, valvo * cres)
        pulso = bat.pulso(t, .10)

        q.limpar()
        H = CHAO - TOPO
        # a camera abre pelo que estourar primeiro: a altura do maior ou a
        # largura da forma mais larga. A **mesma** escala vale para os dois,
        # senao a comparacao deixa de ser uma comparacao.
        k = (H * .88) / max(vr, va)
        hr, ha = vr * k, va * k

        # chão: a linha de terra do projeto
        q.linha(MARGEM - 40, CHAO, AL.LARG - MARGEM + 40, CHAO, est.suave, 2)
        for x in range(MARGEM - 36, AL.LARG - MARGEM + 40, 26):   # hachura
            q.linha(x, CHAO, x - 12, CHAO + 14, est.linha, 1.4)

        # --- referência (esquerda): já traçada, encolhendo
        silhueta(par['ref'].get('forma', 'pessoa'), _cx(0), CHAO, hr, 1.0,
                 est.suave, 2)
        q.linha(60, CHAO - hr, _cx(0) + LADO_W / 2, CHAO - hr,
                est.linha, 1.4, traco=(14, 10))
        q.cota(60, CHAO - hr, CHAO, '', est.suave, tam=0)
        medida(60, CHAO - hr, f"{fmt(vr)} {par['ref'].get('un','m')}", est.suave, 1)
        q.ajustar(par['ref']['nome'], _cx(0), CHAO + 36, est.suave, 28, LADO_W,
                  anc='ma', fonte=est.fonte_rot)

        # --- desafiante (direita): sendo traçado agora
        silhueta(par['alvo'].get('forma', 'predio'), _cx(1), CHAO, ha,
                 min(1.0, f / .62), est.acento, 3)
        q.linha(_cx(1) - LADO_W / 2, CHAO - ha, AL.LARG - 60, CHAO - ha,
                est.acento, 1.6, traco=(14, 10))
        q.cota(AL.LARG - 60, CHAO - ha, CHAO, '', est.acento, tam=0)
        medida(AL.LARG - 60, CHAO - ha,
               f"{fmt(valvo * cres)} {par['alvo'].get('un','m')}", est.acento, -1)
        q.ajustar(par['alvo']['nome'], _cx(1), CHAO + 36, est.acento, 30, LADO_W,
                  anc='ma', fonte=est.fonte_rot)

        # --- a razão, que é a frase do vídeo em um número só
        raz = valvo * cres / max(1e-9, vr)
        q.texto(u['titulo'], AL.LARG / 2, 108, est.suave, 30,
                fonte=est.fonte_rot, anc='ma', espaco=4)
        tam = int(150 * (1 + .06 * pulso))
        q.texto(f'{raz:.1f}'.replace('.', ',') + '×', AL.LARG / 2, 190,
                est.tinta, tam, fonte=est.fonte_num, anc='ma')
        q.ajustar(par.get('ancora', ''), AL.LARG / 2, 1560, est.tinta, 46,
                  AL.LARG - 120, anc='ma')
        # carimbo de prancheta: o rodapé de uma folha de projeto
        q.linha(MARGEM, 1700, AL.LARG - MARGEM, 1700, est.linha, 1.4)
        q.texto('CAIU A FICHA', MARGEM, 1726, est.suave, 26,
                fonte=est.fonte_rot, espaco=5)
        q.texto(f'{j+1:02d}/{n:02d}', AL.LARG - MARGEM, 1726, est.suave, 26,
                fonte=est.fonte_rot, anc='ra')
        return q.render(i)

    os.makedirs(dirsaida, exist_ok=True)
    mix = A.groove(total, kit, seed, lambda tt: .3 + .6 * min(1, tt / total))
    for jj in range(n):
        A.put(mix, A.tick(rng, jj, n), 2.0 + jj * dp, .5)
    A.put(mix, A.fanfare(rng, kit['root'], kit), total - 4.2, .45)
    mix, lufs, tp = A.master(mix, -14.0)
    wav = os.path.join(dirsaida, '_planta.wav')
    sf.write(wav, mix, AL.SR)
    PX.exportar_batidas(bat, total, os.path.join(dirsaida, 'batidas.json'))
    t0 = time.time()
    nq = AL.gravar(quadro, total, wav, os.path.join(dirsaida, saida))
    dt = time.time() - t0
    print(f"{n} pares · estilo {est.nome} · {nq} quadros em {dt:.1f}s = "
          f"{nq/dt:.1f} fps ({total/dt:.2f}x tempo real) · {total:.0f}s · {lufs} LUFS")


if __name__ == '__main__':
    construir(json.load(open(sys.argv[1], encoding='utf-8')),
              seed=int(sys.argv[2]) if len(sys.argv) > 2 else 61,
              dirsaida=sys.argv[3] if len(sys.argv) > 3 else 'out-planta')
