#!/usr/bin/env python3
"""Gera a legenda do post a partir do próprio banco de unidades.

Na referência que puxou este formato, a educação inteira mora na legenda —
é por isso que o vídeo funciona sem voz. A estrutura deles, copiada aqui:
título com fone · a pergunta respondida em uma frase · um parágrafo com os
números específicos · quatro ou cinco hashtags.

Os números já estão nas unidades, com fonte. Um comando, 280 legendas.
"""
import json, sys

TAGS = ['#caiuaficha', '#curiosidades', '#pixelart', '#brasil']


def legenda(arq):
    d = json.load(open(arq, encoding='utf-8'))
    itens = (d.get('unidades') or d.get('marcos') or d.get('passos')
             or d.get('camadas') or d.get('corredores') or d.get('desenhos') or [])
    L = [f"{d['titulo']} \U0001f3a7", '']
    if d.get('chamada'): L += [d['chamada'], '']

    fatos = []
    for it in itens:
        nome = it.get('nome') or (it.get('alvo') or {}).get('nome')
        if not nome: continue
        un = d.get('unidade', '')
        for campo in ('v', 't', 'ate'):
            if campo in it:
                fatos.append(f'{nome}: {it[campo]:g} {un}'.strip()); break
        else:
            if 'alvo' in it:
                a, b = it['ref'], it['alvo']
                fatos.append(f"{b['nome']} tem {b['valor']:g} {b['un']}, "
                             f"{b['valor']/a['valor']:.0f} vezes {a['nome']}")
            elif it.get('ancora'):
                fatos.append(it['ancora'])
    if fatos: L += ['. '.join(fatos[:8]) + '.', '']

    fontes = sorted({it.get('fonte') for it in itens if it.get('fonte')}
                    | ({d['fonte']} if d.get('fonte') else set()))
    if fontes: L += ['Fontes: ' + ' · '.join(fontes), '']
    tags = TAGS + [t for t in d.get('tags', []) if t not in TAGS]
    L.append(' '.join(tags[:5]))
    return '\n'.join(L)


if __name__ == '__main__':
    for a in sys.argv[1:]:
        print('=' * 60); print(a); print('=' * 60)
        print(legenda(a)); print()
