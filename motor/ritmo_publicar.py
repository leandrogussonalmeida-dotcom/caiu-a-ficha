#!/usr/bin/env python3
"""Título, descrição e hashtags dos 30 Shorts NO RITMO -> titulos.txt"""
import sys
import ritmo_musica as M
from ritmo_plano import PLANO

TAGS = {'masmorra': '#pixelart #ritmo', 'rota': '#pixelart #8bit', 'foguete': '#foguete #ritmo',
        'lousa': '#desenho #adivinha', 'corrida': '#corrida #synthwave', 'cidade': '#equalizador #cidade',
        'plataforma': '#8bit #pixelart', 'bolinha': '#satisfatorio #melodia', 'pistas': '#ritmo #bateria',
        'tunel': '#hipnotico #visualizer'}

out = []
for p in PLANO:
    gens = []
    for s in p['secoes']:
        if s['papel'] in ('build', 'fim'): continue
        nome = M.GENEROS[s['gen']]['nome'].title().replace('And', 'and').replace('Uk', 'UK').replace('Lo-Fi', 'Lo-fi')
        bpm = int(s.get('bpm', M.GENEROS[s['gen']]['bpm']))
        item = f"{nome} {bpm}"
        if not gens or gens[-1] != item: gens.append(item)
    desc = (f"{' '.join(p['gancho']).capitalize()}. Toda a música deste vídeo foi gerada por código junto com "
            f"a imagem: cada bumbo, caixa e nota é o mesmo instante na tela e no som.\n\n"
            f"Gêneros, em BPM: {' → '.join(gens)}\n\n"
            f"{p['pergunta'].capitalize()} Comenta aí.\n\n"
            f"#shorts #musicaeletronica {TAGS[p['cena']]} #caiuaficha")
    out.append(f"===== {p['id']}-{p['cena']}.mp4\nTÍTULO: {p['titulo']}\n\n{desc}\n")
open(sys.argv[1] if len(sys.argv) > 1 else 'titulos.txt', 'w').write('\n'.join(out))
print(out[0]); print(out[9])
