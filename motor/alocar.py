#!/usr/bin/env python3
"""Reserva a identidade visual de cada vídeo e de cada Short do plano.

Sorteio não serve aqui. Em 60 SEEDs aleatórios saem só 47 combinações
distintas de 110 — ou seja, repetição garantida antes do vídeo 60. Para 50
vídeos mais 80 Shorts a alocação tem que ser **reservada**, não sorteada, e
conferida no fim: nenhum par (família, paleta) pode aparecer duas vezes.

Cada pilar tem famílias assinatura, para o espectador reconhecer o tipo de
vídeo pela cara. A paleta é que varia dentro do pilar.
"""
import json, itertools

# 11 de hoje + 5 a construir no Lote 0
FAMILIAS_HOJE = ['aurora', 'bauhaus', 'bolhas', 'confete', 'grade', 'hud',
                 'losangos', 'ondas', 'pixel', 'raios', 'synthwave']
FAMILIAS_NOVAS = ['papel', 'fitas', 'particulas', 'liquido', 'vitral']
FAMILIAS = FAMILIAS_HOJE + FAMILIAS_NOVAS

PALETAS_HOJE = ['brasa', 'ferrugem', 'floresta', 'grafite', 'menta', 'neon',
                'noite', 'oceano', 'papel', 'uva']
PALETAS_NOVAS = ['sangria', 'gelo', 'mostarda', 'carvao']
PALETAS = PALETAS_HOJE + PALETAS_NOVAS

# pilar: (nº de vídeos, famílias assinatura, kits de trilha)
PILARES = [
    ('P01 Português que todo mundo erra', 5, ['bauhaus', 'papel', 'grade'],      ['pop', 'lofi']),
    ('P02 Anos 80, 90 e 2000',            5, ['synthwave', 'pixel', 'vitral'],   ['arcade', 'funk']),
    ('P03 Brasil de ponta a ponta',       5, ['tropical' if 0 else 'fitas', 'confete', 'ondas'], ['tropical', 'marcha']),
    ('P04 Mundo: países e bandeiras',     5, ['losangos', 'grade', 'particulas'],['marcha', 'pop']),
    ('P05 Ciência do dia a dia',          5, ['hud', 'particulas', 'liquido'],   ['arcade', 'lofi']),
    ('P06 Bicho e natureza',              5, ['aurora', 'bolhas', 'liquido'],    ['tropical', 'pop']),
    ('P07 Cinema, TV e música',           5, ['raios', 'vitral', 'confete'],     ['funk', 'arcade']),
    ('P08 Lógica e pegadinha',            5, ['hud', 'grade', 'losangos'],       ['lofi', 'marcha']),
    ('P09 Comida e bebida',               5, ['fitas', 'bolhas', 'papel'],       ['tropical', 'funk']),
    ('P10 Objetos que sumiram',           5, ['pixel', 'papel', 'ferrugem' if 0 else 'raios'], ['lofi', 'arcade']),
]

usados = set()


def reservar(familias_pref, i, j=None):
    """Pega o primeiro par livre entre as famílias assinatura do pilar.

    A ordem gira com `i`, para que vídeos seguidos do mesmo pilar não caiam
    todos na mesma família: o pilar tem 3 assinaturas e os 5 vídeos passam
    por todas elas. Se o pilar esgotar, cai para qualquer família livre.
    """
    fp = list(familias_pref)
    fp = fp[i % len(fp):] + fp[:i % len(fp)]
    ordem = fp + [f for f in FAMILIAS if f not in fp]
    j = i if j is None else j
    for f in ordem:
        for p in PALETAS[j % len(PALETAS):] + PALETAS[:j % len(PALETAS)]:
            if (f, p) not in usados:
                usados.add((f, p)); return f, p
    raise SystemExit('combinações esgotadas')


plano = {'videos': [], 'shorts': []}
seed = 1001
for pi, (nome, n, fams, kits) in enumerate(PILARES):
    for v in range(n):
        f, p = reservar(fams, v, pi * 7 + v * 3)
        plano['videos'].append(dict(id=f'V{len(plano["videos"])+1:02d}', pilar=nome,
                                    fundo=f, paleta=p, kit=kits[v % len(kits)], seed=seed))
        seed += 1

# 80 Shorts: 8 por lote de 5 vídeos; cada Short usa família diferente do pai
seed = 3001
for i in range(80):
    pai = plano['videos'][(i * 5 // 8) % 50]
    fams = [f for f in FAMILIAS if f != pai['fundo']]
    f, p = reservar(fams, i)
    plano['shorts'].append(dict(id=f'S{i+1:02d}', pai=pai['id'], fundo=f, paleta=p, seed=seed))
    seed += 1

pares = [(x['fundo'], x['paleta']) for x in plano['videos'] + plano['shorts']]
assert len(pares) == len(set(pares)), 'REPETIU'
json.dump(plano, open('plano-visual.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(plano["videos"])} vídeos + {len(plano["shorts"])} Shorts = {len(pares)} identidades')
print(f'nenhum par repetido · capacidade {len(FAMILIAS)}x{len(PALETAS)} = {len(FAMILIAS)*len(PALETAS)}')
print(f'folga depois do plano: {len(FAMILIAS)*len(PALETAS) - len(pares)} combinações')
for v in plano['videos'][:3]: print(' ', v)
