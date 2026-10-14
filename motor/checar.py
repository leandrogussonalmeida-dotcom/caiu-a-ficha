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
    # a paleta vem do plano (plano-280.json), nao da unidade: e o plano que
    # garante que duas pecas nao saem com a mesma cara
    if not d.get('paleta') and not str(d.get('id', '')).startswith('V'):
        avisos.append('sem paleta: vai sortear')

    # Toda chave de lista que algum simulador usa precisa estar aqui. Um
    # verificador cego a um formato nao reprova nada nele - ele so diz
    # "sem itens" e o conteudo passa sem conferencia nenhuma.
    CHAVES = ('unidades', 'marcos', 'marcas', 'passos', 'camadas',
              'corredores', 'desenhos', 'itens')
    # so chave que carrega LISTA: 'geracoes' e um numero e entrava aqui como
    # se fosse a lista de itens
    itens = next((d[k] for k in CHAVES if isinstance(d.get(k), list) and d[k]), [])
    # a CADEIA nao tem lista: ela e descrita por um numero de geracoes e uma
    # taxa. Nesse caso o que se confere e a fonte do documento inteiro.
    # Formatos sem lista: a CADEIA (um numero de geracoes e uma taxa) e o
    # MODO FOCO (so o nome de uma cena). Nos dois o que se confere e a fonte
    # do documento. Cena sintetizada nao tem dado externo, mas tem de DIZER
    # isso - 'nao ha dado a conferir' e uma declaracao, nao um silencio.
    if not itens and (isinstance(d.get('geracoes'), (int, float)) or d.get('cena')):
        if not d.get('fonte'): _erro(e, 'sem fonte')
        if d.get('confianca') not in CONF: _erro(e, 'sem confianca valida')
        return e, avisos
    if not itens: _erro(e, 'sem itens (' + '/'.join(CHAVES) + ')')
    # a FILEIRA tem um objeto de referencia fora da lista
    if d.get('itens') and not (d.get('ref') or {}).get('valor'):
        _erro(e, 'formato fileira sem ref.valor')

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

    # 'ate' e 'v' na mesma camada: o simulador usa 'ate' e o outro vira um
    # numero fantasma que so existe no arquivo. Foi assim que a crosta ficou
    # com 35 km no video e 70 km na fonte declarada.
    for it in itens:
        if isinstance(it, dict) and 'ate' in it and 'v' in it and it['ate'] != it['v']:
            _erro(e, f"{it.get('nome','item')}: tem 'ate'={it['ate']} e 'v'={it['v']} "
                     f"ao mesmo tempo, e o simulador so le um dos dois")

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
