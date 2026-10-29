#!/usr/bin/env python3
"""Título, descrição e hashtags dos Shorts NO RITMO (canal NOSSO MUNDO PIXEL) -> titulos.txt

Em inglês (canal global). A descrição muda de forma de peça para peça: a
política de conteúdo repetitivo olha o canal inteiro, e trinta descrições com
a mesma frase são o primeiro sinal de fábrica.
"""
import sys
import ritmo_musica as M
from ritmo_plano import PLANO

TAGS = {'masmorra': '#pixelart #rhythm', 'rota': '#pixelart #8bit', 'foguete': '#rocket #rhythm',
        'lousa': '#drawing #guessinggame', 'corrida': '#racing #synthwave', 'cidade': '#visualizer #citylights',
        'plataforma': '#8bit #platformer', 'bolinha': '#satisfying #melody', 'pistas': '#rhythmgame #drums',
        'tunel': '#hypnotic #visualizer'}

ABRE = [
    "Every kick, snare and note here is one event: it plays in the audio and moves on screen in the same frame.",
    "The music and the animation come from the same code, so nothing is guessed: the beat IS the motion.",
    "Original track, made together with the pixel art. Each hit on screen is a hit in the song.",
    "No beat detection, no stock music: the song and the picture are written from the same notes.",
    "Turn the sound up. What you see is the song itself, drawn block by block.",
]


def genero(s):
    return M.GENEROS[s['gen']]['nome'].title().replace('And', 'and').replace('Uk', 'UK').replace('Lo-Fi', 'Lo-fi')


def montar():
    out = []
    for k, p in enumerate(PLANO):
        gens = []
        for s in p['secoes']:
            if s['papel'] in ('build', 'fim'): continue
            item = f"{genero(s)} {int(s.get('bpm', M.GENEROS[s['gen']]['bpm']))}"
            if not gens or gens[-1] != item: gens.append(item)
        desc = (f"{ABRE[k % len(ABRE)]}\n\n"
                f"Tracklist (BPM): {' → '.join(gens)}\n\n"
                f"{p['pergunta'].capitalize()}\n\n"
                f"#shorts #electronicmusic {TAGS[p['cena']]} #nossomundopixel")
        out.append(f"===== {p['id']}-{p['cena']}.mp4\nTITLE: {p['titulo']}\n\n{desc}\n")
    return out


if __name__ == '__main__':
    out = montar()
    open(sys.argv[1] if len(sys.argv) > 1 else 'titulos.txt', 'w', encoding='utf-8').write('\n'.join(out))
    print(out[0]); print(out[9])
