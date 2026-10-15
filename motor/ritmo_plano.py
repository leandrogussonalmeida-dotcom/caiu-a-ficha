#!/usr/bin/env python3
"""NO RITMO — os 30 Shorts.

10 cenas x 3. Nenhum par (cena, paleta) se repete, e cada Short tem trilha
própria (seed, tônica, gêneros e andamentos). O BPM sempre sobe dentro do
Short: é a promessa do gancho e o que segura até o fim.

Formato de cada entrada:
  id, cena, paleta, seed, gancho (2 linhas), sub_gancho, pergunta (comentário),
  secoes (gênero, compassos, papel, bpm opcional), variante, titulo, descricao
"""


def J(*partes, fim=2):
    """Jornada: ('gen', compassos[, bpm]) ... ; 'B' antes de um item põe um
    build de 1 compasso no gênero anterior. O último gênero repete no 'fim'
    (cartão de inscrição)."""
    out = []
    ant = None
    for p in partes:
        if p == 'B':
            out.append(dict(gen=ant['gen'], bars=1, papel='build', **({'bpm': ant['bpm']} if 'bpm' in ant else {})))
            continue
        d = dict(gen=p[0], bars=p[1], papel='drop')
        if len(p) > 2: d['bpm'] = p[2]
        out.append(d)
        ant = d
    f = dict(gen=ant['gen'], bars=fim, papel='fim')
    if 'bpm' in ant: f['bpm'] = ant['bpm']
    out.append(f)
    return out


DESENHOS_OK = ['AMPULHETA', 'AVIAO', 'BARCO', 'BICICLETA', 'CACTO', 'CARACOL', 'CARRO',
               'CASA', 'CHAVE', 'COGUMELO', 'FAROL', 'FLOR', 'FOLHA', 'GARRAFA', 'GATO',
               'GUARDA-CHUVA', 'IGREJA', 'LAMPADA', 'OCULOS', 'PEIXE', 'PONTE', 'RELOGIO',
               'XICARA', 'TESOURA', 'PANELA']

PLANO = [
    # ---------------------------------------------------------------- masmorra
    dict(id='r01', cena='masmorra', paleta='espaco', seed=1001, scanlines=True,
         gancho=['ELE SÓ ANDA', 'NA BATIDA'], sub_gancho='LIGA O SOM',
         pergunta='QUAL FASE FOI A MELHOR?',
         secoes=J(('chiptune', 4, 112), 'B', ('chiptune', 4, 150), 'B', ('dnb', 6)),
         titulo='Ele só anda na batida 🎧 (112 → 174 BPM)'),
    dict(id='r02', cena='masmorra', paleta='brasa', seed=1002,
         variante=dict(piso=(2, 1), luz=(9, 10, 11, 8), parede=(5, 3, 7), roupa=12),
         gancho=['MASMORRA', 'NO PHONK'], sub_gancho='SEGURA ATÉ O FIM',
         pergunta='PHONK OU HARDSTYLE?',
         secoes=J(('phonk', 4, 126), 'B', ('phonk', 4, 140), 'B', ('hardstyle', 6)),
         titulo='Masmorra no ritmo do phonk 🔥 (126 → 150 BPM)'),
    dict(id='r03', cena='masmorra', paleta='gelo', seed=1003, scanlines=True,
         variante=dict(piso=(2, 1), luz=(11, 8, 9, 12), parede=(4, 3, 7), roupa=10, geleca=9),
         gancho=['TENTA NÃO', 'BALANÇAR A CABEÇA'], sub_gancho='',
         pergunta='BALANÇOU OU NÃO?',
         secoes=J(('techno', 4), 'B', ('trance', 5), 'B', ('gabber', 6)),
         titulo='Tenta não balançar a cabeça 💀 (132 → 190 BPM)'),
    # ---------------------------------------------------------------- rota
    dict(id='r04', cena='rota', paleta='rota', seed=1004,
         paletas_secao=['rota', 'rota', 'rota', 'rota_noite', 'rota_noite', 'rota_noite'],
         variante=dict(zonas=['campo', 'praia', 'cidade', 'caverna', 'neon', 'neon']),
         gancho=['DO MAIS LENTO', 'AO MAIS RÁPIDO'], sub_gancho='80 ATÉ 174 BPM',
         pergunta='QUAL ZONA É A SUA?',
         secoes=J(('lofi', 2), ('dembow', 3), ('house', 4), ('dubstep', 4), ('dnb', 6)),
         titulo='Do gênero mais lento ao mais rápido 🎮 (80 → 174 BPM)'),
    dict(id='r05', cena='rota', paleta='rota_outono', seed=1005,
         paletas_secao=['rota_outono', 'rota_outono', 'rota', 'rota_noite', 'rota_noite', 'rota_noite'],
         variante=dict(zonas=['outono', 'cidade', 'neve', 'caverna', 'neon', 'neon']),
         gancho=['CADA ZONA', 'É UM GÊNERO'], sub_gancho='ESCUTA A TROCA',
         pergunta='QUAL ZONA TE PEGOU?',
         secoes=J(('synthwave', 3), ('garage', 4), ('chiptune', 4), ('trap', 4), ('future', 5)),
         titulo='Cada zona é um gênero diferente 🗺️ (100 → 150 BPM)'),
    dict(id='r06', cena='rota', paleta='rota_noite', seed=1006, scanlines=True,
         paletas_secao=['rota_noite'],
         variante=dict(zonas=['campo', 'praia', 'cidade', 'caverna', 'neon', 'neon']),
         gancho=['UMA VIAGEM', 'POR 5 GÊNEROS'], sub_gancho='DO LO-FI AO D&B',
         pergunta='QUAL GÊNERO VOCÊ PULARIA?',
         secoes=J(('lofi', 2, 86), ('funk', 4), ('techno', 4), ('hardstyle', 4), ('dnb', 6)),
         titulo='Uma viagem por 5 gêneros eletrônicos 🎧'),
    # ---------------------------------------------------------------- foguete
    dict(id='r07', cena='foguete', paleta='neon', seed=1007,
         gancho=['CADA BARREIRA', 'CAI NO BUMBO'], sub_gancho='OLHA O DROP',
         pergunta='QUANTAS BARREIRAS VOCÊ CONTOU?',
         secoes=J(('synthwave', 4), 'B', ('trance', 6), 'B', ('hardstyle', 6)),
         titulo='Cada barreira explode no bumbo 🚀 (100 → 150 BPM)'),
    dict(id='r08', cena='foguete', paleta='espaco', seed=1008, scanlines=True,
         variante=dict(cores=[12, 9, 15, 7], nariz=10, aleta=10),
         gancho=['ATÉ ONDE', 'ELE CHEGA?'], sub_gancho='',
         pergunta='CHEGOU NO ESPAÇO?',
         secoes=J(('house', 4), 'B', ('dubstep', 6), 'B', ('dnb', 8)),
         titulo='Até onde o foguete chega no ritmo? 🚀 (124 → 174 BPM)'),
    dict(id='r09', cena='foguete', paleta='sangria', seed=1009,
         variante=dict(cores=[9, 12, 10, 11], nariz=12, aleta=12),
         gancho=['ACELERA', 'ATÉ 190 BPM'], sub_gancho='AGUENTA?',
         pergunta='AGUENTOU OS 190?',
         secoes=J(('techno', 4), 'B', ('techno', 4, 145), 'B', ('gabber', 8)),
         titulo='Foguete acelerando até 190 BPM 🚀'),
    # ---------------------------------------------------------------- lousa
    dict(id='r10', cena='lousa', paleta='carvao', seed=1010, y_placa=238,
         variante=dict(desenhos=['GATO', 'FAROL', 'BICICLETA', 'GUARDA-CHUVA', 'CARACOL']),
         gancho=['ADIVINHA', 'ANTES DO FIM'], sub_gancho='5 DESENHOS',
         pergunta='QUANTOS VOCÊ ACERTOU?',
         secoes=J(('house', 3), ('garage', 3), ('trap', 3), ('dnb', 4), ('dnb', 4, 180)),
         titulo='Adivinha o desenho antes de terminar ✏️'),
    dict(id='r11', cena='lousa', paleta='menta', seed=1011, y_placa=238,
         variante=dict(desenhos=['CASA', 'PEIXE', 'AVIAO', 'IGREJA', 'XICARA'], moldura=9, vidro=6, traco=0),
         gancho=['O DESENHO', 'ACELERA JUNTO'], sub_gancho='ADIVINHA ANTES',
         pergunta='QUAL FOI O MAIS DIFÍCIL?',
         secoes=J(('lofi', 2), ('synthwave', 3), ('house', 3), ('future', 3), ('dnb', 4)),
         titulo='O desenho acelera junto com a música ✏️ (80 → 174 BPM)'),
    dict(id='r12', cena='lousa', paleta='mostarda', seed=1012, y_placa=238,
         variante=dict(desenhos=['CACTO', 'CARRO', 'AMPULHETA', 'LAMPADA', 'BARCO'], moldura=15, vidro=8, traco=0, fundo=(2, 1)),
         gancho=['ACERTA OS', '5 DESENHOS?'], sub_gancho='ANTES DA BATIDA',
         pergunta='ACERTOU OS 5?',
         secoes=J(('dembow', 3), ('chiptune', 3, 130), ('phonk', 3, 140), ('hardstyle', 4), ('gabber', 4)),
         titulo='Acerta os 5 desenhos antes da batida? ✏️'),
    # ---------------------------------------------------------------- corrida
    dict(id='r13', cena='corrida', paleta='por_do_sol', seed=1013, y_placa=92,
         variante=dict(ceu='sol', carro=15),
         gancho=['DO ÚLTIMO', 'AO PRIMEIRO'], sub_gancho='NO RITMO',
         pergunta='EM QUE LUGAR VOCÊ CHEGARIA?',
         secoes=J(('synthwave', 4), 'B', ('house', 6), 'B', ('dnb', 8)),
         titulo='Do último ao primeiro lugar no ritmo 🏁 (100 → 174 BPM)'),
    dict(id='r14', cena='corrida', paleta='noite_cidade', seed=1014, y_placa=92, scanlines=True,
         variante=dict(ceu='noite', carro=10),
         gancho=['ULTRAPASSA', 'NA CAIXA'], sub_gancho='CONTA COMIGO',
         pergunta='TECHNO OU HARDSTYLE?',
         secoes=J(('techno', 4), 'B', ('trance', 6), 'B', ('hardstyle', 7)),
         titulo='Cada ultrapassagem cai na caixa 🏎️'),
    dict(id='r15', cena='corrida', paleta='deserto', seed=1015, y_placa=92,
         variante=dict(ceu='deserto', carro=15),
         gancho=['CORRIDA', 'NO PANCADÃO'], sub_gancho='DO REGGAETON AO D&B',
         pergunta='FUNK OU DRUM AND BASS?',
         secoes=J(('dembow', 4), ('funk', 5), 'B', ('trap', 5), 'B', ('dnb', 6)),
         titulo='Corrida no deserto no ritmo do funk 🏜️'),
    # ---------------------------------------------------------------- cidade
    dict(id='r16', cena='cidade', paleta='neon', seed=1016, variante=dict(chuva=True),
         gancho=['A CIDADE', 'DANÇA O SOM'], sub_gancho='OLHA OS PRÉDIOS',
         pergunta='QUAL PRÉDIO É O SEU?',
         secoes=J(('lofi', 3), ('synthwave', 4), 'B', ('future', 8)),
         titulo='A cidade que dança a música 🌃'),
    dict(id='r17', cena='cidade', paleta='gelo', seed=1017,
         gancho=['CADA PRÉDIO', 'É UMA FREQUÊNCIA'], sub_gancho='GRAVE NO MEIO',
         pergunta='VOCÊ SENTIU O GRAVE?',
         secoes=J(('house', 4), ('garage', 4), 'B', ('trance', 8)),
         titulo='Cada prédio é uma frequência do som 🏙️'),
    dict(id='r18', cena='cidade', paleta='brasa', seed=1018, variante=dict(chuva=True), scanlines=True,
         gancho=['ESPERA', 'O DROP'], sub_gancho='A CIDADE TREME',
         pergunta='QUAL DROP FOI MAIS FORTE?',
         secoes=J(('trap', 4), 'B', ('dubstep', 6), 'B', ('dnb', 8)),
         titulo='Espera o drop… a cidade inteira treme 🌆'),
    # ---------------------------------------------------------------- plataforma
    dict(id='r19', cena='plataforma', paleta='floresta', seed=1019, scanlines=True,
         variante=dict(fundo='colinas', roupa=10, espinho=15),
         gancho=['ELE PULA', 'NO BUMBO'], sub_gancho='NUNCA ERRA',
         pergunta='CONSEGUE PULAR JUNTO?',
         secoes=J(('chiptune', 4, 132), 'B', ('chiptune', 6, 160), 'B', ('dnb', 6)),
         titulo='Ele pula exatamente no bumbo 🎮 (132 → 174 BPM)'),
    dict(id='r20', cena='plataforma', paleta='noite_cidade', seed=1020,
         variante=dict(fundo='cidade', roupa=9, espinho=10),
         gancho=['NÃO ERRA', 'UM PULO'], sub_gancho='DUVIDA?',
         pergunta='ERROU ALGUM?',
         secoes=J(('house', 4), 'B', ('techno', 6), 'B', ('dnb', 8)),
         titulo='Ele não erra um pulo no ritmo 🌃 (124 → 174 BPM)'),
    dict(id='r21', cena='plataforma', paleta='uva', seed=1021,
         variante=dict(fundo='colinas', roupa=12, espinho=9),
         gancho=['PULA NO', 'PANCADÃO'], sub_gancho='DO FUNK AO HARDSTYLE',
         pergunta='FUNK, PHONK OU HARDSTYLE?',
         secoes=J(('funk', 5), 'B', ('phonk', 5, 140), 'B', ('hardstyle', 7)),
         titulo='Pulando no ritmo do funk ao hardstyle 🎮'),
    # ---------------------------------------------------------------- bolinha
    dict(id='r22', cena='bolinha', paleta='neon', seed=1022, variante=dict(fundo='grade'),
         gancho=['A BOLINHA', 'TOCA A MÚSICA'], sub_gancho='CADA QUIQUE É UMA NOTA',
         pergunta='ESSA MELODIA GRUDOU?',
         secoes=J(('trance', 4), 'B', ('trance', 8), fim=2),
         titulo='A bolinha que toca a música 🎵'),
    dict(id='r23', cena='bolinha', paleta='espaco', seed=1023, variante=dict(fundo='estrelas'),
         gancho=['CADA QUIQUE', 'É UMA NOTA'], sub_gancho='DO LO-FI AO FUTURE',
         pergunta='LO-FI OU FUTURE BASS?',
         secoes=J(('lofi', 3), ('synthwave', 4), 'B', ('future', 8)),
         titulo='Cada quique é uma nota da melodia 🎵 (80 → 150 BPM)'),
    dict(id='r24', cena='bolinha', paleta='sangria', seed=1024, variante=dict(fundo='bolhas'), scanlines=True,
         gancho=['OUVE', 'A MELODIA'], sub_gancho='E OLHA A BOLINHA',
         pergunta='CONSEGUE CANTAR JUNTO?',
         secoes=J(('chiptune', 4, 128), 'B', ('house', 5), 'B', ('chiptune', 6, 160)),
         titulo='Olha a bolinha e ouve a melodia 🎵'),
    # ---------------------------------------------------------------- pistas
    dict(id='r25', cena='pistas', paleta='neon', seed=1025,
         gancho=['CONSEGUE', 'TOCAR ISSO?'], sub_gancho='4 PISTAS',
         pergunta='QUAL PISTA É A MAIS DIFÍCIL?',
         secoes=J(('house', 4), 'B', ('dubstep', 5), 'B', ('dnb', 7)),
         titulo='Consegue tocar esse ritmo? 🥁 (124 → 174 BPM)'),
    dict(id='r26', cena='pistas', paleta='carvao', seed=1026, variante=dict(quarta='baixo'), scanlines=True,
         gancho=['O RITMO', 'DE CADA GÊNERO'], sub_gancho='OLHA O CHIMBAL',
         pergunta='QUAL RITMO É MAIS DIFÍCIL?',
         secoes=J(('trap', 4), ('phonk', 4), 'B', ('gabber', 7)),
         titulo='O ritmo de cada gênero, nota por nota 🥁'),
    dict(id='r27', cena='pistas', paleta='menta', seed=1027,
         gancho=['REGGAETON', 'FUNK E TECHNO'], sub_gancho='VÊ A DIFERENÇA',
         pergunta='QUAL VOCÊ DANÇA?',
         secoes=J(('dembow', 4), ('funk', 5), 'B', ('techno', 7)),
         titulo='Reggaeton, funk e techno: vê a diferença do ritmo 🥁'),
    # ---------------------------------------------------------------- túnel
    dict(id='r28', cena='tunel', paleta='espaco', seed=1028, scanlines=True,
         variante=dict(lados=[4, 6, 3, 8], cores=[12, 9, 15, 6]),
         gancho=['ENTRA', 'NO TÚNEL'], sub_gancho='COM FONE',
         pergunta='QUANTOS PORTAIS VOCÊ PASSOU?',
         secoes=J(('trance', 4), 'B', ('trance', 6), 'B', ('hardstyle', 7)),
         titulo='Entra no túnel do ritmo 🌀 (138 → 150 BPM)'),
    dict(id='r29', cena='tunel', paleta='sangria', seed=1029,
         variante=dict(lados=[6, 3, 4, 6], cores=[9, 12, 10, 11]),
         gancho=['CADA PORTAL', 'É UMA BATIDA'], sub_gancho='',
         pergunta='DUBSTEP OU DRUM AND BASS?',
         secoes=J(('dubstep', 5), 'B', ('dubstep', 4), 'B', ('dnb', 8)),
         titulo='Cada portal é uma batida 🌀 (140 → 174 BPM)'),
    dict(id='r30', cena='tunel', paleta='gelo', seed=1030,
         variante=dict(lados=[3, 4, 6, 8, 4], cores=[11, 9, 12, 15, 10]),
         gancho=['TÚNEL', 'DE 190 BPM'], sub_gancho='AGUENTA ATÉ O FIM?',
         pergunta='AGUENTOU ATÉ O FIM?',
         secoes=J(('synthwave', 4), 'B', ('future', 6), 'B', ('gabber', 8)),
         titulo='Túnel que acelera até 190 BPM 🌀'),
]

# nenhuma combinação (cena, paleta) repete
assert len({(p['cena'], p['paleta']) for p in PLANO}) == len(PLANO)
assert len({p['seed'] for p in PLANO}) == len(PLANO)
assert len(PLANO) == 30
# desenhos da lousa: nenhum repete entre os três vídeos e todos da lista boa
_des = [d for p in PLANO if p['cena'] == 'lousa' for d in p['variante']['desenhos']]
assert len(_des) == len(set(_des)) and all(d in DESENHOS_OK for d in _des)
