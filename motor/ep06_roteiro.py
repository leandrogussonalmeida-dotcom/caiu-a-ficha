#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep06 (série COMO VOA / FLUTUA): Por que um navio de aço flutua.

A ideia: flutuar é empurrar água. Um objeto que flutua tira do lugar o seu
próprio peso em água (Arquimedes). O aço é quase 8 vezes mais denso que a
água, então 1 kg de aço em cubo afunda; o mesmo 1 kg em forma de caixa
empurra muito mais água e flutua, porque a caixa é aço + ar. O navio é a
mesma caixa, gigante: carrega, afunda mais (marcas de calado e marca de
Plimsoll), flutua mais alto no mar que no rio, e as anteparas seguram a
água se o casco furar. Protagonistas: o cubo/caixa de 1 kg no tanque e o
navio, com o contador de carga e de água deslocada.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 29-30/10/2026)
  F1  Empuxo = peso do fluido deslocado; "qualquer objeto que flutua desloca o
      próprio peso em fluido"; todo navio precisa deslocar ao menos o próprio peso;
      o ferro é quase 8 vezes mais denso que a água. Wikipedia, "Archimedes' principle".
  F2  Densidade do aço: 7,75 a 8,05 g/cm³ (usamos 7,85). Wikipedia, "Steel".
  F3  Água do mar: média na superfície 1,025 kg/L (1.020 a 1.029 kg/m³); água pura
      1,0 kg/L a 4 °C. Wikipedia, "Seawater".
  F4  Mais denso que o fluido afunda, menos denso flutua; um navio flutua mesmo
      feito de aço porque encerra um volume de ar; Arquimedes de Siracusa,
      212 a.C. Wikipedia, "Buoyancy".
  F5  Porte bruto (deadweight): soma de carga, combustível, água doce, lastro,
      mantimentos, passageiros e tripulação; não inclui o navio vazio.
      Wikipedia, "Deadweight tonnage".
  F6  Um porta-contêineres de 397 m: 156.907 t de porte bruto, calado de 16,02 m.
      Wikipedia, "Emma Mærsk" (só os números; o navio desenhado é genérico).
  F7  Marca de Plimsoll (1876, Samuel Plimsoll); TF, F, T, S, W, WNA; o navio
      flutua mais fundo na água doce (1.000 kg/m³) que no mar (1.025 kg/m³).
      Wikipedia, "Load line (watercraft)".
  F8  Anteparas criam compartimentos estanques que seguram a água se o casco
      furar. Wikipedia, "Bulkhead (partition)".
  F9  Titanic: 16 compartimentos; flutuava com 2 alagados e, em certas
      combinações, 3 ou até 4; o iceberg abriu 6; as anteparas não eram
      fechadas em cima e a água passou por cima, como numa forma de gelo;
      afundou em 15/4/1912. Wikipedia, "Sinking of the Titanic".
  F10 Contas: 1 kg de aço / 7,85 = 127 cm³ = cubo de 5 cm; empuxo 0,127 kg.
      Caixa 15 x 15 x 8 cm = 705 cm² de chapa -> 1,8 mm; 1 L / 225 cm² = 4,4 cm
      dentro d'água; densidade média 1.000 g / 1.800 cm³ = 0,56.
  F11 Conta: 1,025 / 1,000 -> 2,5% mais volume submerso na água doce.
"""

TITULO = "Por que um navio de aço flutua? | Arquimedes em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='densidade', gen='lofi', bars=12, papel='drop'),       # 36 s
    dict(id='empuxo', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='cubo', gen='lofi', bars=10, papel='drop'),            # 30 s
    dict(id='tigela', gen='lofi', bars=14, papel='drop'),          # 42 s
    dict(id='media', gen='lofi', bars=10, papel='break'),          # 30 s
    dict(id='navio', gen='synthwave', bars=20, papel='drop'),      # 48 s (6 peças x 8 s)
    dict(id='carga', gen='lofi', bars=18, papel='drop'),           # 54 s
    dict(id='plimsoll', gen='lofi', bars=10, papel='drop'),        # 30 s
    dict(id='doce', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='inundar', gen='lofi', bars=12, papel='break'),        # 36 s
    dict(id='titanic', gen='lofi', bars=12, papel='break'),        # 36 s
    dict(id='resumo', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 6.0, "UM PARAFUSO DE AÇO *AFUNDA*.", "", ()),
        (6.0, 11.6, "UM NAVIO GIGANTE, TODO DE AÇO,", "*FLUTUA*. COMO?", ('F4',)),
    ],
    'densidade': [
        (0.8, 7.6, "PRIMEIRO, UMA BALANÇA E", "CUBOS DE *1 LITRO*.", ()),
        (7.8, 14.6, "1 LITRO DE *ÁGUA* PESA 1 KG.", "", ('F3',)),
        (14.8, 22.6, "1 LITRO DE *AÇO*: CERCA DE 7,85 KG.", "QUASE 8 VEZES MAIS.", ('F2', 'F1')),
        (22.8, 29.6, "1 LITRO DE ÁGUA DO MAR: *1,025 KG*.", "O SAL DEIXA A ÁGUA MAIS DENSA.", ('F3',)),
        (29.8, 35.6, "ISSO É A *DENSIDADE*:", "QUANTO PESA CADA LITRO.", ()),
    ],
    'empuxo': [
        (0.5, 7.6, "AGORA, UM TANQUE CHEIO ATÉ A BORDA", "E UMA *BOIA* DE 2 KG.", ()),
        (7.8, 15.6, "A BOIA ENTRA E EMPURRA ÁGUA", "PARA FORA. ELA *TRANSBORDA*.", ('F1',)),
        (15.8, 23.6, "A BOIA PAROU. A ÁGUA QUE SAIU PESA", "*2 KG*: O MESMO QUE A BOIA.", ('F1',)),
        (23.8, 29.6, "A ÁGUA EMPURRA DE VOLTA PARA CIMA:", "É O *EMPUXO*.", ('F1',)),
        (29.8, 35.6, "QUEM DESCOBRIU FOI *ARQUIMEDES*,", "UM GREGO, HÁ MAIS DE 2.200 ANOS.", ('F4',)),
    ],
    'cubo': [
        (0.5, 7.6, "AGORA, *1 KG DE AÇO* EM CUBO:", "UM CUBINHO DE 5 CM DE LADO.", ('F10',)),
        (7.8, 15.6, "ELE SÓ EMPURRA 127 ML DE ÁGUA.", "EMPUXO: *0,13 KG*.", ('F10', 'F1')),
        (15.8, 22.6, "PESO 1 KG, EMPUXO 0,13 KG:", "O PESO GANHA. *AFUNDA*.", ('F1',)),
        (22.8, 29.6, "MACIÇO, O AÇO É DENSO DEMAIS", "PARA FLUTUAR.", ('F4',)),
    ],
    'tigela': [
        (0.5, 7.6, "O MESMO 1 KG DE AÇO, AGORA", "*AMASSADO* NUMA CHAPA FININHA.", ('F10',)),
        (7.8, 14.6, "DOBRANDO AS BORDAS, VIRA UMA", "*CAIXA* DE 15 X 15 X 8 CM.", ('F10',)),
        (14.8, 21.6, "NA ÁGUA, ELA VAI AFUNDANDO E", "EMPURRANDO CADA VEZ *MAIS ÁGUA*.", ('F1',)),
        (21.8, 29.6, "COM 4,4 CM DENTRO DA ÁGUA, ELA JÁ", "EMPURROU *1 LITRO*: 1 KG.", ('F10', 'F1')),
        (29.8, 35.6, "EMPUXO = PESO. ELA *PARA* AÍ", "E FLUTUA.", ('F1',)),
        (35.8, 41.6, "MESMO AÇO, MESMO PESO.", "SÓ MUDOU A *FORMA*.", ()),
    ],
    'media': [
        (0.5, 7.6, "O SEGREDO É O QUE TEM DENTRO", "DA CAIXA: *AR*.", ('F4',)),
        (7.8, 14.6, "AÇO + AR: 1 KG EM 1,8 LITRO.", "DENSIDADE MÉDIA: *0,56*.", ('F10',)),
        (14.8, 22.6, "MENOR QUE A DA ÁGUA, QUE É 1.", "POR ISSO ELA *FLUTUA*.", ('F4',)),
        (22.8, 29.6, "O CUBO MACIÇO TINHA *7,85*.", "POR ISSO AFUNDOU.", ('F2', 'F4')),
    ],
    'navio': [
        (0.3, 7.6, "UM NAVIO É A MESMA CAIXA, SÓ QUE", "GIGANTE. O *CASCO* É DE AÇO.", ('F4',)),
        (8.3, 15.6, "DENTRO: *PORÕES* COM CARGA E AR.", "", ('F4',)),
        (16.3, 23.6, "PAREDES DE AÇO, AS *ANTEPARAS*,", "DIVIDEM O CASCO EM COMPARTIMENTOS.", ('F8',)),
        (24.3, 31.6, "A *LINHA D'ÁGUA*: ATÉ ONDE", "O CASCO ESTÁ AFUNDADO.", ()),
        (32.3, 39.6, "ATRÁS, EMBAIXO DA ÁGUA:", "A *HÉLICE* E O *LEME*.", ()),
        (40.3, 47.6, "OS MAIORES PORTA-CONTÊINERES", "TÊM QUASE *400 METROS*.", ('F6',)),
    ],
    'carga': [
        (0.5, 7.6, "HORA DE CARREGAR. CADA CONTÊINER", "PÕE MAIS PESO NO NAVIO.", ()),
        (7.8, 15.6, "MAIS PESO: O NAVIO *AFUNDA MAIS*", "E EMPURRA MAIS ÁGUA.", ('F1',)),
        (15.8, 23.6, "CADA TONELADA A BORDO EMPURRA", "*1 TONELADA DE ÁGUA* A MAIS.", ('F1',)),
        (23.8, 31.6, "UM GIGANTE DESSES LEVA ATÉ", "*156.907 TONELADAS*.", ('F6',)),
        (31.8, 39.6, "CONTA TUDO: CARGA, COMBUSTÍVEL, ÁGUA,", "COMIDA. É O *PORTE BRUTO*.", ('F5',)),
        (39.8, 46.6, "CARREGADO, O FUNDO FICA", "*16 METROS* ABAIXO DA ÁGUA.", ('F6',)),
        (46.8, 53.6, "AS MARCAS NA PROA MOSTRAM", "QUANTO ELE AFUNDOU: O *CALADO*.", ()),
    ],
    'plimsoll': [
        (0.5, 7.6, "MAS ATÉ ONDE ELE PODE AFUNDAR?", "NO MEIO DO CASCO TEM UMA MARCA.", ('F7',)),
        (7.8, 15.6, "É A *MARCA DE PLIMSOLL*, DE 1876.", "A ÁGUA NÃO PODE PASSAR DA LINHA.", ('F7',)),
        (15.8, 22.6, "*S*: VERÃO. *W*: INVERNO.", "*T*: TRÓPICOS. *F*: ÁGUA DOCE.", ('F7',)),
        (22.8, 29.6, "QUANTO MAIS BAIXA A LINHA,", "MENOS PESO O NAVIO PODE LEVAR.", ('F1', 'F7')),
    ],
    'doce': [
        (0.5, 7.6, "AGORA O NAVIO SAI DO MAR", "E ENTRA NUM *RIO*.", ()),
        (7.8, 15.6, "ÁGUA DOCE É MENOS DENSA:", "1 LITRO PESA 1 KG, NÃO 1,025.", ('F3',)),
        (15.8, 23.6, "PARA EMPURRAR O MESMO PESO EM", "ÁGUA, ELE AFUNDA *2,5% MAIS*.", ('F1', 'F11')),
        (23.8, 29.6, "POR ISSO A LINHA *F*, DE ÁGUA DOCE,", "FICA MAIS ALTA NA MARCA.", ('F7',)),
        (29.8, 35.6, "NO MAR, O MESMO NAVIO", "*FLUTUA MAIS ALTO*.", ('F7',)),
    ],
    'inundar': [
        (0.5, 7.6, "E SE ENTRAR ÁGUA?", "UM FURO NA CAIXA DE AÇO...", ()),
        (7.8, 15.6, "A ÁGUA TOMA O LUGAR DO AR.", "A DENSIDADE MÉDIA *SOBE*.", ('F4',)),
        (15.8, 22.6, "PASSOU DE 1? *AFUNDA*.", "", ('F4',)),
        (22.8, 29.6, "NO NAVIO, AS *ANTEPARAS* PRENDEM A", "ÁGUA NUM COMPARTIMENTO SÓ.", ('F8',)),
        (29.8, 35.6, "ELE FICA MAIS BAIXO,", "MAS *CONTINUA FLUTUANDO*.", ('F8',)),
    ],
    'titanic': [
        (0.5, 7.6, "O TITANIC TINHA", "*16 COMPARTIMENTOS*.", ('F9',)),
        (7.8, 15.6, "AGUENTAVA 2 ALAGADOS, E ATÉ 3 OU 4", "EM ALGUNS CASOS.", ('F9',)),
        (15.8, 22.6, "EM 1912, O ICEBERG ABRIU *6*.", "", ('F9',)),
        (22.8, 29.6, "AS ANTEPARAS NÃO ERAM FECHADAS EM", "CIMA. A ÁGUA *PASSOU POR CIMA*.", ('F9',)),
        (29.8, 35.6, "COMO UMA *FORMA DE GELO* ENCHENDO,", "UMA CASINHA DEPOIS DA OUTRA.", ('F9',)),
    ],
    'resumo': [
        (0.5, 8.6, "FLUTUAR É EMPURRAR ÁGUA:", "O SEU PRÓPRIO PESO EM ÁGUA.", ('F1',)),
        (8.8, 17.6, "O AÇO MACIÇO É DENSO DEMAIS.", "COM *AR* DENTRO, A MÉDIA FICA LEVE.", ('F4',)),
        (17.8, 26.6, "CARGA ENTRA, O NAVIO DESCE.", "A *MARCA DE PLIMSOLL* DÁ O LIMITE.", ('F1', 'F7')),
        (26.8, 35.6, "E AS *ANTEPARAS* SEGURAM A ÁGUA", "SE O CASCO FURAR.", ('F8',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Archimedes\' principle"', 'https://en.wikipedia.org/wiki/Archimedes%27_principle'),
    'F2': ('Wikipedia, "Steel" (densidade de 7,75 a 8,05 g/cm³)', 'https://en.wikipedia.org/wiki/Steel'),
    'F3': ('Wikipedia, "Seawater"', 'https://en.wikipedia.org/wiki/Seawater'),
    'F4': ('Wikipedia, "Buoyancy"', 'https://en.wikipedia.org/wiki/Buoyancy'),
    'F5': ('Wikipedia, "Deadweight tonnage"', 'https://en.wikipedia.org/wiki/Deadweight_tonnage'),
    'F6': ('Wikipedia, "Emma Mærsk" (397 m, 156.907 t de porte bruto, calado de 16,02 m)',
           'https://en.wikipedia.org/wiki/Emma_M%C3%A6rsk'),
    'F7': ('Wikipedia, "Load line (watercraft)"', 'https://en.wikipedia.org/wiki/Load_line_(watercraft)'),
    'F8': ('Wikipedia, "Bulkhead (partition)"', 'https://en.wikipedia.org/wiki/Bulkhead_(partition)'),
    'F9': ('Wikipedia, "Sinking of the Titanic"', 'https://en.wikipedia.org/wiki/Sinking_of_the_Titanic'),
    'F10': ('Conta a partir de F1 e F2 (1 kg de aço a 7,85 g/cm³; caixa de 15 x 15 x 8 cm)', None),
    'F11': ('Conta a partir de F3 (1,025 / 1,000 = 2,5% a mais de volume submerso)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'densidade': 'Quanto pesa 1 litro', 'empuxo': 'O empuxo de Arquimedes',
                'cubo': '1 kg de aço em cubo afunda', 'tigela': 'O mesmo aço em forma de caixa flutua',
                'media': 'Aço + ar: a densidade média', 'navio': 'As partes do navio',
                'carga': 'Carregando o navio', 'plimsoll': 'A marca de Plimsoll',
                'doce': 'Rio ou mar?', 'inundar': 'E se entrar água?', 'titanic': 'O caso do Titanic',
                'resumo': 'Resumo'}

DESCRICAO = """Como um navio de aço, com milhares de toneladas, consegue flutuar se um parafuso de aço afunda? A resposta é de Arquimedes: tudo o que flutua empurra para o lado o seu próprio peso em água.

Neste vídeo a gente pesa 1 litro de água e 1 litro de aço, joga 1 kg de aço em cubo num tanque (afunda) e depois amassa o mesmo 1 kg numa caixa (flutua). Daí vai para o navio: as partes do casco, o carregamento com um contador de toneladas, as marcas de calado, a marca de Plimsoll, a diferença entre rio e mar, e o que acontece quando entra água no casco, com o caso do Titanic.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O aço tem densidade de 7,75 a 8,05 g/cm³ conforme a liga; usamos 7,85 nas contas.
- A caixa de 15 x 15 x 8 cm é uma conta: a chapa teria 1,8 mm, e a espessura da parede foi ignorada no volume.
- Os números do navio grande (397 m, 156.907 t de porte bruto, 16 m de calado) são de um porta-contêineres real; o navio desenhado é genérico e menor na tela. O calado do navio vazio (7 m) é um exemplo.
- No carregamento, o navio desce em linha reta com a carga (como se o casco tivesse paredes retas); um casco de verdade tem curvas.
- Na marca de Plimsoll, a distância entre as linhas muda de navio para navio; o desenho é um exemplo.
- Os 2,5% a mais no rio valem para o volume submerso; o calado aumenta um pouco menos ou um pouco mais conforme a forma do casco.
- No capítulo do Titanic o desenho é um diagrama genérico de 16 compartimentos, não o navio.

Fontes
{fontes}

#navio #comofunciona #pixelart #fisica #arquimedes #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O tanque ocupa x 49..225;
# o navio fica em x0 = 24..284 (no corte vertical ele é desenhado mais curto, em x 70..250).
PREFIXO = 'ep06-navio'
CORTES = [
    dict(id='c1', de=('cubo', 0.0), ate=('cubo', 30.0), x=47, gancho=['AÇO NA', 'ÁGUA'],
         titulo='Por que 1 kg de aço afunda na água? ⚓',
         descricao='Um cubo de 1 kg de aço tem 5 cm de lado e só empurra 127 ml de água. O empuxo (0,13 kg) perde para o peso (1 kg) e ele afunda.'),
    dict(id='c2', de=('tigela', 0.0), ate=('tigela', 40.0), x=47, gancho=['MESMO AÇO', 'FLUTUA!'],
         titulo='O mesmo aço que afunda agora flutua 🚢',
         descricao='O mesmo 1 kg de aço, amassado numa caixa de 15 x 15 x 8 cm, afunda só 4,4 cm: aí ele já empurrou 1 litro de água, 1 kg. Empuxo igual ao peso: flutua.'),
    dict(id='c3', de=('carga', 0.0), ate=('carga', 40.0), x=70, gancho=['CARREGANDO', 'O GIGANTE'],
         titulo='O que acontece quando um navio é carregado?',
         descricao='Cada tonelada que entra no navio faz ele empurrar 1 tonelada de água a mais. Um porta-contêineres gigante leva até 156.907 toneladas e fica com o fundo 16 metros abaixo da água.'),
    dict(id='c4', de=('plimsoll', 0.0), ate=('plimsoll', 30.0), x=40, gancho=['A LINHA', 'DO LIMITE'],
         titulo='Para que serve essa marca no casco dos navios?',
         descricao='É a marca de Plimsoll, obrigatória desde 1876: a água não pode passar da linha. S é verão, W inverno, T trópicos e F água doce.'),
    dict(id='c5', de=('doce', 0.0), ate=('doce', 36.0), x=70, gancho=['RIO OU', 'MAR?'],
         titulo='Por que o navio afunda mais no rio do que no mar? 🌊',
         descricao='A água do mar é mais densa (1,025 kg por litro). Na água doce o navio precisa afundar 2,5% mais para empurrar o mesmo peso em água.'),
    dict(id='c6', de=('titanic', 0.0), ate=('titanic', 36.0), x=70, gancho=['POR QUE O', 'TITANIC?'],
         titulo='Por que as anteparas não salvaram o Titanic?',
         descricao='Ele tinha 16 compartimentos e aguentava 2 alagados (até 3 ou 4 em alguns casos). O iceberg abriu 6, e a água passou por cima das anteparas, como numa forma de gelo.'),
]
