#!/usr/bin/env python3
"""Título e descrição dos Shorts NO RITMO (canal NOSSO MUNDO PIXEL).

    python3 ritmo_publicar.py <pasta>       # um .txt por Short (rNN-cena.txt)

PT-BR por padrão (LINGUA=en para a versão global). A abertura da descrição
muda de peça para peça: a política de conteúdo repetitivo olha o canal
inteiro, e trinta descrições com a mesma frase são o primeiro sinal de fábrica.
"""
import os, sys
import ritmo_musica as M
from ritmo_plano import PLANO
from idioma import T, LINGUA

TAGS = {'masmorra': ('#pixelart #ritmo', '#pixelart #rhythm'), 'rota': ('#pixelart #8bit', '#pixelart #8bit'),
        'foguete': ('#foguete #ritmo', '#rocket #rhythm'), 'lousa': ('#desenho #adivinha', '#drawing #guessinggame'),
        'corrida': ('#corrida #synthwave', '#racing #synthwave'), 'plataforma': ('#8bit #jogo', '#8bit #platformer'),
        'bolinha': ('#satisfatorio #melodia', '#satisfying #melody'), 'pistas': ('#bateria #ritmo', '#rhythmgame #drums'),
        'tunel': ('#hipnotico #visualizer', '#hypnotic #visualizer')}

ABRE_PT = [
    "Cada bumbo, caixa e nota daqui é um evento só: ele toca no som e mexe na tela no mesmo quadro.",
    "A música e a animação saem do mesmo código: nada é adivinhado, a batida É o movimento.",
    "Trilha original, feita junto com a pixel art. Cada golpe na tela é um golpe na música.",
    "Sem detectar batida e sem música de banco: o som e a imagem são escritos a partir das mesmas notas.",
    "Aumenta o som. O que você vê é a própria música, desenhada bloco a bloco.",
]
ABRE_EN = [
    "Every kick, snare and note here is one event: it plays in the audio and moves on screen in the same frame.",
    "The music and the animation come from the same code, so nothing is guessed: the beat IS the motion.",
    "Original track, made together with the pixel art. Each hit on screen is a hit in the song.",
    "No beat detection, no stock music: the song and the picture are written from the same notes.",
    "Turn the sound up. What you see is the song itself, drawn block by block.",
]


def genero(s):
    return M.GENEROS[s['gen']]['nome'].title().replace('And', 'and').replace('Uk', 'UK').replace('Lo-Fi', 'Lo-fi')


def montar():
    out = {}
    abre = ABRE_PT if LINGUA == 'pt' else ABRE_EN
    for k, p in enumerate(PLANO):
        gens = []
        for s in p['secoes']:
            if s['papel'] in ('build', 'fim'): continue
            item = f"{genero(s)} {int(s.get('bpm', M.GENEROS[s['gen']]['bpm']))}"
            if not gens or gens[-1] != item: gens.append(item)
        perg = p['pergunta'].capitalize()
        desc = (f"{abre[k % len(abre)]}\n\n"
                f"{T('Gêneros (BPM)', 'Tracklist (BPM)')}: {' → '.join(gens)}\n\n"
                f"{perg} {T('Comenta aí.', '')}".strip() + "\n\n"
                f"#shorts {T('#musicaeletronica', '#electronicmusic')} {T(*TAGS[p['cena']])} #nossomundopixel")
        nome = f"{p['id']}-{p['cena']}"
        out[nome] = f"{T('TÍTULO', 'TITLE')}\n{p['titulo']}\n\n{T('DESCRIÇÃO', 'DESCRIPTION')}\n{desc}\n"
    return out


if __name__ == '__main__':
    pasta = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(pasta, exist_ok=True)
    for nome, txt in montar().items():
        open(os.path.join(pasta, nome + '.txt'), 'w', encoding='utf-8').write(txt)
    print(f"{len(montar())} arquivos em {pasta}")
