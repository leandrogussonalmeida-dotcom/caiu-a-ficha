#!/usr/bin/env python3
"""Título e descrição de um vídeo longo, com capítulos (timestamps do roteiro)
e as fontes de cada fato. O YouTube só cria capítulos se o primeiro for 0:00,
houver 3 ou mais e cada um tiver 10 s ou mais.

    python3 longo_publicar.py ep01_roteiro saida.txt
"""
import importlib, sys
import ritmo_musica as M

NOMES = {'gancho': 'Intro', 'titulo': None, 'carro': 'Inside the car', 'pecas': 'The parts of a cylinder',
         'admissao': 'Stroke 1: Intake', 'compressao': 'Stroke 2: Compression', 'potencia': 'Stroke 3: Power',
         'escape': 'Stroke 4: Exhaust', 'ciclo': 'One full cycle', 'batidas': 'An engine on the beat',
         'rpm': 'Real engine speed', 'cilindros': 'Flywheel and 4 cylinders', 'energia': 'Where the energy goes',
         'resumo': 'Otto, 1876, and the nickname', 'fim': None}


def mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def montar(nome):
    R = importlib.import_module(nome)
    t = 0.0
    caps = []
    for c in R.CAPITULOS:
        bpm = c.get('bpm', M.GENEROS[c['gen']]['bpm'])
        dur = c['bars'] * 4 * 60.0 / bpm
        rot = NOMES.get(c['id'])
        if rot: caps.append((0.0 if not caps else t, rot, dur))
        elif caps:                                     # capítulo sem nome soma no anterior
            a, r, d = caps[-1]; caps[-1] = (a, r, d + dur)
        t += dur
    assert caps[0][0] == 0 and len(caps) >= 3
    assert all(d >= 10 for _, _, d in caps[:-1]), 'capítulo do YouTube com menos de 10 s'
    usados = []
    for itens in R.LEGENDAS.values():
        for *_, fatos in itens:
            for f in fatos:
                if f not in usados: usados.append(f)
    fontes = []
    vistos = set()
    for f in sorted(R.FONTES, key=lambda x: int(x[1:])):
        nome_f, url = R.FONTES[f]
        chave = (nome_f, url)
        if chave in vistos: continue
        vistos.add(chave)
        fontes.append(f"- {nome_f}" + (f": {url}" if url else ""))
    desc = R.DESCRICAO.format(capitulos='\n'.join(f"{mmss(a)} {r}" for a, r, _ in caps), fontes='\n'.join(fontes))
    return R.TITULO, desc


if __name__ == '__main__':
    tit, desc = montar(sys.argv[1])
    txt = f"TITLE\n{tit}\n\nDESCRIPTION\n{desc}\n"
    open(sys.argv[2], 'w', encoding='utf-8').write(txt)
    print(txt)
