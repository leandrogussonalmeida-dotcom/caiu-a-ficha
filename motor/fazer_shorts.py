#!/usr/bin/env python3
"""Recorta Shorts do vídeo longo reaproveitando a narração já gerada.

A regra: nada de regravar voz. Os .wav do vídeo longo servem como estão — só
entram acelerados, porque no Short cada segundo de fala disputa espaço com os
60 s de teto. Cada Short leva SEED próprio, então fundo, paleta e trilha mudam
sozinhos: o mesmo conteúdo, nunca a mesma cara.
"""
import json, os, subprocess, sys

BASE = 'decks/v01-palavras.json'
FONTE = 'outvoz'                  # onde está a narração do vídeo longo

# Duas perguntas por Short, não três: com a explicação longa do vídeo
# reaproveitada, três estouram os 60 s — e abaixo de 60 s o Short roda em loop,
# que é o que infla a retenção. Duas perguntas também rendem 15 Shorts de um
# vídeo só, em vez de 10.
SHORTS = [
    dict(id='s01', seed=301, idxs='0,3', fundo='synthwave', paleta='neon',
         titulo='Você escreve essas duas certo?',
         tela='As duas que mais pegam gente',
         chamadas=['Tem 30 dessas no canal', 'CAIU A FICHA']),
    dict(id='s02', seed=302, idxs='24,25', fundo='bauhaus', paleta='brasa',
         titulo='De onde vêm essas palavras?',
         tela='Nenhuma das duas é tupi',
         chamadas=['A origem surpreende', 'CAIU A FICHA']),
    dict(id='s03', seed=303, idxs='19,21', fundo='hud', paleta='menta',
         titulo='Junto, separado ou com hífen?',
         tela='As pegadinhas da escrita',
         chamadas=['Erra quem tem pressa', 'CAIU A FICHA']),
]

# a voz do vídeo longo entra acelerada: explicação de 11 s vira 9 s, e é o
# que faz duas perguntas caberem em 50 s com a vinheta nas pontas
VELOC = os.environ.get('VELOC', '1.18')


def main():
    deck = json.load(open(BASE, encoding='utf-8'))
    alvos = sys.argv[1:] or [c['id'] for c in SHORTS]
    for c in SHORTS:
        if c['id'] not in alvos: continue
        d = dict(deck)
        d.update(fundo=c['fundo'], paleta=c['paleta'],
                 titulo_short=c['titulo'], intro_short=c['tela'],
                 # a vinheta da marca faz a abertura e o fecho: sem fala aqui
                 fala_intro_short='', fala_outro_short='',
                 outro_titulo='Qual você errou?', outro_short='',
                 tempo_short=5, short_intro_s=1.0, short_outro_s=1.2,
                 chamadas_outro=c['chamadas'])
        dp = f"decks/short-{c['id']}.json"
        json.dump(d, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

        D = f"out-{c['id']}"
        env = dict(os.environ, SEED=str(c['seed']), NARR=FONTE, VELOC=VELOC, REUSO='1')
        print(f"\n=== {c['id']} · perguntas {c['idxs']} · {c['fundo']}/{c['paleta']} ===", flush=True)
        subprocess.run([sys.executable, 'quizengine.py', 'short', dp, D, c['idxs'], '0'],
                       env=env, check=True)
        subprocess.run([sys.executable, 'quizengine.py', 'vinheta', dp, D, 'v'],
                       env=env, check=True)
        subprocess.run([sys.executable, 'quizengine.py', 'montar', D, 'short.mp4',
                        f"caiu-a-ficha-{c['id']}.mp4"], env=env, check=True)


if __name__ == '__main__':
    main()
