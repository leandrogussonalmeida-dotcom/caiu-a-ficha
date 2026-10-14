#!/usr/bin/env python3
"""Trava de conteúdo: recusa a unidade antes de gastar render.

O mesmo princípio do `checar_deck()` do quiz. Erro de dado é o mais caro de
todos — num canal cujo produto é "este número é maior do que você imagina",
o número errado destrói o canal, e descobrir depois de publicado é tarde.
"""
import json, math, sys

CONF = ('alta', 'media', 'baixa')
MIN_CONF = 'media'


def _erro(e, msg): e.append(msg)


def checar_unidades(arq):
    d = json.load(open(arq, encoding='utf-8'))
    e, avisos = [], []
    if not d.get('titulo'): _erro(e, 'sem titulo')
    if not d.get('paleta'): avisos.append('sem paleta: vai sortear')

    itens = (d.get('unidades') or d.get('marcos') or d.get('passos')
             or d.get('camadas') or d.get('corredores') or d.get('desenhos') or [])
    if not itens: _erro(e, 'sem itens (unidades/marcos/passos/camadas/corredores/desenhos)')

    nomes = set()
    for i, it in enumerate(itens, 1):
        rot = it.get('nome') or (it.get('alvo') or {}).get('nome') or f'item {i}'
        if not (it.get('nome') or it.get('alvo')):
            _erro(e, f'item {i}: sem nome')
        if rot in nomes: _erro(e, f'{rot}: aparece duas vezes')
        nomes.add(rot)
        if len(str(rot)) > 22:
            avisos.append(f'{rot}: nome com {len(str(rot))} caracteres, vai encolher muito')

        # todo numero precisa de fonte e de confianca declarada
        tem_num = any(k in it for k in ('v', 't', 'ate', 'valor'))
        if 'alvo' in it: tem_num = True
        if tem_num:
            if not it.get('fonte') and not d.get('fonte'):
                _erro(e, f'{rot}: numero sem fonte')
            c = it.get('confianca', d.get('confianca'))
            if c not in CONF:
                _erro(e, f'{rot}: confianca ausente ou invalida ({c})')
            elif CONF.index(c) > CONF.index(MIN_CONF):
                _erro(e, f'{rot}: confianca {c}, abaixo do limiar {MIN_CONF}')

        for campo in ('v', 't', 'ate'):
            if campo in it and not isinstance(it[campo], (int, float)):
                _erro(e, f'{rot}: {campo} nao e numero')

        if 'grade' in it:
            g = it['grade']
            if len(set(len(l) for l in g)) != 1:
                _erro(e, f'{rot}: grade com linhas de larguras diferentes')
            if any(c not in '.0123456789abcdef' for l in g for c in l):
                _erro(e, f'{rot}: grade com caractere invalido')
            if sum(c != '.' for l in g for c in l) < 12:
                _erro(e, f'{rot}: grade quase vazia')

        if 'ancora' in it and len(it['ancora']) > 34:
            avisos.append(f'{rot}: ancora longa, vai encolher')

    # escadas e viagens tem que ser monotonicas, senao o ponteiro anda para tras
    for chave in ('t', 'ate'):
        vs = [it[chave] for it in itens if chave in it]
        if len(vs) > 1 and vs != sorted(vs):
            _erro(e, f'campo {chave} fora de ordem crescente')

    return e, avisos


if __name__ == '__main__':
    ruim = False
    for arq in sys.argv[1:]:
        e, a = checar_unidades(arq)
        nome = arq.split('/')[-1]
        for x in a: print(f'  aviso  {nome}: {x}')
        for x in e: print(f'  ERRO   {nome}: {x}')
        if e: ruim = True
        else: print(f'  ok     {nome}')
    sys.exit(1 if ruim else 0)
