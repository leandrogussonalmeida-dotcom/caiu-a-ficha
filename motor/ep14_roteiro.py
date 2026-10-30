#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep14 (série COMO VOA / FLUTUA): Como o submarino afunda e sobe.

A ideia: o submarino não muda de tamanho, muda de PESO. Pela regra de
Arquimedes (ep06, o navio), o empuxo é o peso da água que ele empurra; com o
casco todo embaixo d'água esse empuxo não cresce mais. Então: água do mar nos
tanques de lastro -> mais pesado que o empuxo -> desce; tanques de ajuste
acertam o peso e o nível -> para no meio da água; ar comprimido empurra a água
para fora -> mais leve -> sobe. Andando, os lemes de profundidade inclinam o
nariz e a hélice leva para baixo ou para cima. Lá embaixo, +1 atmosfera a cada
10 m: por isso o casco é um tubo redondo e grosso, e há limites de fundura
(muitas vezes secretos). O sonar enxerga com o som. Protagonista: um submarino
genérico (sem bandeira nem número), com contador de fundura e visor dos tanques.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Wikipedia, "Archimedes' principle": o empuxo é igual ao peso do fluido
      deslocado; força resultante positiva sobe, negativa afunda, zero = fica
      parado (flutuação neutra); "todo navio, submarino e dirigível precisa
      deslocar ao menos o seu próprio peso".
  F2  Wikipedia, "Ballast tank": na superfície os tanques ficam vazios
      (flutuação positiva); para mergulhar a tripulação abre os respiros em
      cima dos tanques de lastro principais e as válvulas embaixo; a água entra
      e o ar sai pelos respiros; tanques principais cheios = flutuação quase
      neutra; tanques de controle de profundidade fazem o ajuste fino; para
      subir, fecham os respiros e soltam ar comprimido nos tanques, que empurra
      a água para fora pelas válvulas de baixo; água passada entre os tanques de
      compensação equilibra o submarino na horizontal.
  F3  Wikipedia, "Submarine": tanques de lastro com água para submergir e com
      ar para subir; neutro não é estável no nível; tanques de compensação na
      frente e atrás; tanques de controle de profundidade; lemes de
      profundidade (hidroplanos); hélice atrás; casco resistente de aço grosso
      de alta resistência; aço de hoje: 250 a 400 m; o Komsomolets (titânio):
      teste a 1.000 m; sonar ativo usa o eco do som emitido, é pouco usado
      porque revela o submarino; sonar passivo = hidrofones que só escutam.
  F4  Wikipedia, "Diving plane": lemes na proa e na popa; a posição deles
      controla o ângulo do submarino e, com ele andando para a frente, a
      fundura; os de trás funcionam como o profundor de um avião.
  F5  Wikipedia, "Submarine hull": o casco resistente é o casco de dentro, que
      segura a pressão do mar e mantém dentro a pressão atmosférica normal;
      seção redonda porque outras formas são muito mais fracas; um desvio de
      uma polegada (2,5 cm) do redondo pode tirar mais de 30% da carga que ele
      aguenta; anéis (cavernas) reforçam contra a flambagem; casco leve por
      fora, alagado, não segura pressão; em casco simples os tanques de lastro
      ficam na proa e na popa; 1ª Guerra: teste até 100 m; 2ª Guerra: até 200 m.
  F6  Wikipedia, "Submarine depth ratings": cada 10 m de água soma cerca de 1
      atmosfera (101 kPa); a 300 m, 30 atmosferas; profundidade de teste =
      limite do uso normal em tempo de paz; profundidade de projeto; máxima de
      operação; esmagamento (implosão), em geral um pouco abaixo da de projeto;
      na Marinha dos EUA o teste é 2/3 da profundidade de projeto.
  F7  The Lean Submariner, "How low can you go? (an unclassified accounting of
      the term Test Depth)": cita um livro de 1958 — a informação de fundura
      "é tão importante que tem que ser secreta"; o autor não revela as dos
      seus submarinos.
  F8  Wikipedia, "Speed of sound": na água salgada o som anda cerca de 1.500 m/s.
  F9  Conta (F6): 1 atm = 101 kPa = 101.325 N por metro quadrado / 9,8 = cerca de
      1,03 kg-força por centímetro quadrado (~1 kg); 100 m = 10 atm = ~10 kg;
      300 m = 30 atm = ~31 kg por centímetro quadrado.
  F10 Conta (F8): eco em 2 s = 1 s de ida + 1 s de volta = 1.500 m.
  F11 Conta (F6): para o ar empurrar a água para fora do tanque, ele precisa de
      mais pressão que a água lá fora (a 50 m, mais de 5 atm além da do ar).
"""

TITULO = "Como o submarino afunda e sobe | Tanques de lastro, pressão e sonar em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=5, papel='break'),             # 15 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='arquimedes', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='partes', gen='synthwave', bars=18, papel='drop'),        # 43,2 s (7 peças)
    dict(id='mergulho', gen='lofi', bars=16, papel='drop'),           # 48 s
    dict(id='equilibrio', gen='lofi', bars=10, papel='break'),        # 30 s
    dict(id='subir', gen='lofi', bars=14, papel='drop'),              # 42 s
    dict(id='lemes', gen='synthwave', bars=20, papel='drop'),         # 48 s
    dict(id='pressao', gen='lofi', bars=18, papel='drop'),            # 54 s
    dict(id='casco', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='limite', gen='lofi', bars=14, papel='break'),            # 42 s
    dict(id='sonar', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 7.0, "ESTE SUBMARINO É DE AÇO E FLUTUA.", "AGORA ELE VAI *AFUNDAR*. DE PROPÓSITO.", ()),
        (7.2, 14.6, "E DEPOIS VOLTA A *SUBIR*.", "SEM ASA E SEM BOIA: SÓ ÁGUA E AR.", ('F3',)),
    ],
    'arquimedes': [
        (0.5, 7.6, "LEMBRA DO NAVIO? TUDO O QUE FLUTUA", "EMPURRA O SEU *PRÓPRIO PESO* EM ÁGUA.", ('F1',)),
        (7.8, 14.6, "A ÁGUA EMPURRA DE VOLTA PARA CIMA:", "É O *EMPUXO*.", ('F1',)),
        (14.8, 21.6, "NA SUPERFÍCIE, O PESO DO SUBMARINO", "E O EMPUXO *SE EQUILIBRAM*.", ('F1',)),
        (21.8, 28.6, "EMPUXO MAIOR QUE O PESO: *SOBE*.", "MENOR: *DESCE*. IGUAL: *FICA PARADO*.", ('F1',)),
        (28.8, 35.6, "O TRUQUE DO SUBMARINO: MUDAR O", "PRÓPRIO PESO COM *ÁGUA DO MAR*.", ('F3',)),
    ],
    'partes': [
        (0.3, 6.0, "O *CASCO RESISTENTE*: UM TUBO DE AÇO", "GROSSO. DENTRO, AR NA PRESSÃO NORMAL.", ('F5', 'F3')),
        (6.5, 12.2, "NA PROA E NA POPA, OS *TANQUES DE*", "*LASTRO*: CHEIOS DE AR OU DE ÁGUA.", ('F2', 'F5')),
        (12.7, 18.4, "*TANQUES DE AJUSTE*: POUCA ÁGUA,", "PARA ACERTAR O PESO E O NÍVEL.", ('F2', 'F3')),
        (18.9, 24.6, "GARRAFAS DE *AR COMPRIMIDO*:", "SÃO ELAS QUE ESVAZIAM OS TANQUES.", ('F2',)),
        (25.1, 30.8, "OS *LEMES DE PROFUNDIDADE*, NA PROA", "E NA POPA, INCLINAM O SUBMARINO.", ('F4',)),
        (31.3, 37.0, "A *HÉLICE*, ATRÁS, EMPURRA", "O SUBMARINO PARA A FRENTE.", ('F3',)),
        (37.5, 43.0, "NO NARIZ, O *SONAR*:", "OS OUVIDOS DO SUBMARINO.", ('F3',)),
    ],
    'mergulho': [
        (0.5, 6.8, "NA SUPERFÍCIE, OS TANQUES DE LASTRO", "ESTÃO CHEIOS DE *AR*.", ('F2',)),
        (7.0, 13.8, "PARA MERGULHAR, ABREM-SE OS *RESPIROS*", "EM CIMA E AS VÁLVULAS EMBAIXO.", ('F2',)),
        (14.0, 20.8, "A ÁGUA DO MAR ENTRA POR BAIXO", "E EMPURRA O AR PARA FORA, POR CIMA.", ('F2',)),
        (21.0, 27.8, "MAIS ÁGUA, MAIS PESO. O SUBMARINO", "DESCE ATÉ *SUMIR* NA ÁGUA.", ('F3', 'F1')),
        (28.0, 34.8, "TANQUES CHEIOS: O PESO FICA QUASE", "IGUAL AO EMPUXO. ELE QUASE PARA.", ('F2',)),
        (35.0, 41.8, "UM POUCO MAIS DE ÁGUA NO TANQUE DE", "AJUSTE: MAIS PESO. *ELE DESCE*.", ('F2', 'F1')),
        (42.0, 47.6, "NÃO PRECISA DE MOTOR PARA DESCER:", "BASTA PESAR MAIS QUE O *EMPUXO*.", ('F1',)),
    ],
    'equilibrio': [
        (0.5, 7.6, "AGORA O PESO É IGUAL AO EMPUXO:", "ELE *PARA* NO MEIO DA ÁGUA.", ('F1', 'F3')),
        (7.8, 14.6, "MAS ESTÁ DE NARIZ PARA BAIXO:", "TEM MAIS PESO NA FRENTE.", ('F3',)),
        (14.8, 21.6, "OS *TANQUES DE AJUSTE* PASSAM ÁGUA", "DA FRENTE PARA TRÁS.", ('F2', 'F3')),
        (21.8, 29.6, "NIVELADO E EQUILIBRADO, ELE FICA", "PARADO A *50 METROS*.", ('F1',)),
    ],
    'subir': [
        (0.5, 7.6, "HORA DE VOLTAR. OS RESPIROS", "DE CIMA SÃO *FECHADOS*.", ('F2',)),
        (7.8, 14.6, "O *AR COMPRIMIDO* DAS GARRAFAS", "É SOLTO DENTRO DOS TANQUES.", ('F2',)),
        (14.8, 21.6, "O AR EMPURRA A ÁGUA PARA FORA", "PELAS VÁLVULAS DE BAIXO.", ('F2',)),
        (21.8, 28.6, "MENOS ÁGUA, MENOS PESO. O EMPUXO", "GANHA: O SUBMARINO *SOBE*.", ('F1', 'F3')),
        (28.8, 35.6, "PARA EMPURRAR A ÁGUA, O AR PRECISA", "DE *MAIS PRESSÃO* QUE O MAR LÁ FORA.", ('F6', 'F11')),
        (35.8, 41.6, "NA SUPERFÍCIE, TANQUES VAZIOS:", "ELE *FLUTUA* DE NOVO.", ('F2',)),
    ],
    'lemes': [
        (0.5, 7.6, "ANDANDO, O SUBMARINO TEM OUTRO", "JEITO DE MUDAR DE FUNDURA.", ('F4',)),
        (7.8, 14.6, "OS *LEMES DE PROFUNDIDADE* VIRAM", "E O NARIZ APONTA PARA BAIXO.", ('F4',)),
        (14.8, 21.6, "COM A HÉLICE EMPURRANDO,", "ELE DESCE *EM DIAGONAL*.", ('F4', 'F3')),
        (21.8, 28.6, "LEMES AO CONTRÁRIO: NARIZ PARA", "CIMA. ELE *SOBE*.", ('F4',)),
        (28.8, 35.6, "OS LEMES DE TRÁS FUNCIONAM COMO", "O *PROFUNDOR* DE UM AVIÃO.", ('F4',)),
        (35.8, 42.6, "MAS SE A HÉLICE PARA, ELE", "PERDE VELOCIDADE...", ()),
        (42.8, 47.6, "...E OS LEMES PERDEM A FORÇA: ELES", "PRECISAM DA *ÁGUA PASSANDO*.", ('F4',)),
    ],
    'pressao': [
        (0.5, 7.6, "NA SUPERFÍCIE, O AR JÁ APERTA TUDO", "COM *1 ATMOSFERA* DE PRESSÃO.", ('F6',)),
        (7.8, 14.6, "A CADA *10 METROS* DE ÁGUA DO MAR,", "A PRESSÃO SOBE MAIS 1 ATMOSFERA.", ('F6',)),
        (14.8, 21.6, "1 ATMOSFERA É CERCA DE *1 KG*", "EM CADA CENTÍMETRO QUADRADO.", ('F9',)),
        (21.8, 28.6, "A 100 METROS: MAIS 10 ATMOSFERAS.", "*10 KG* EM CADA CENTÍMETRO QUADRADO.", ('F6', 'F9')),
        (28.8, 35.6, "A 300 METROS: *30 ATMOSFERAS*", "DE ÁGUA APERTANDO O CASCO.", ('F6',)),
        (35.8, 42.6, "É COMO *31 KG* EM CADA", "CENTÍMETRO QUADRADO DO CASCO.", ('F9',)),
        (42.8, 48.4, "LÁ DENTRO, O AR CONTINUA COM", "*1 ATMOSFERA*, COMO AQUI EM CIMA.", ('F5',)),
        (48.6, 53.6, "O CASCO SEGURA TODA", "ESSA *DIFERENÇA*.", ('F5',)),
    ],
    'casco': [
        (0.5, 7.6, "POR QUE O CASCO É UM *TUBO REDONDO*?", "VAMOS APERTAR DOIS FORMATOS.", ('F5',)),
        (7.8, 14.6, "NO QUADRADO, AS PAREDES RETAS", "*ENTORTAM* PARA DENTRO.", ('F5',)),
        (14.8, 21.6, "NO REDONDO, A PRESSÃO SE ESPALHA", "POR IGUAL. ELE *AGUENTA* MUITO MAIS.", ('F5',)),
        (21.8, 28.6, "POR DENTRO, *ANÉIS DE AÇO* REFORÇAM", "O TUBO, COMO COSTELAS.", ('F5',)),
        (28.8, 35.6, "UM DESVIO DE SÓ 2,5 CM DO REDONDO", "TIRA *MAIS DE 30%* DA RESISTÊNCIA.", ('F5',)),
    ],
    'limite': [
        (0.5, 7.6, "ATÉ ONDE UM SUBMARINO PODE DESCER?", "DEPENDE DO CASCO.", ('F5',)),
        (7.8, 14.6, "NA PRIMEIRA GUERRA, ATÉ *100 M*.", "NA SEGUNDA, ATÉ *200 M*.", ('F5',)),
        (14.8, 21.6, "HOJE, OS DE AÇO: CERCA DE", "*250 A 400 METROS*.", ('F3',)),
        (21.8, 28.6, "A *PROFUNDIDADE DE TESTE* É O LIMITE", "DO USO NORMAL, SEM GUERRA.", ('F6',)),
        (28.8, 35.6, "NA MARINHA DOS EUA, ELA É *2/3*", "DA PROFUNDIDADE DE PROJETO.", ('F6',)),
        (35.8, 41.6, "MAIS FUNDO, O CASCO É *ESMAGADO*.", "O NÚMERO DE CADA UM É *SEGREDO*.", ('F6', 'F7')),
    ],
    'sonar': [
        (0.5, 7.6, "LÁ EMBAIXO É ESCURO. O SUBMARINO", "ENXERGA COM O *SOM*: É O SONAR.", ('F3',)),
        (7.8, 14.6, "NA ÁGUA DO MAR, O SOM ANDA", "CERCA DE *1.500 METROS POR SEGUNDO*.", ('F8',)),
        (14.8, 21.6, "O *SONAR ATIVO* SOLTA UM PING", "E ESPERA O ECO VOLTAR.", ('F3',)),
        (21.8, 28.6, "ECO EM 2 SEGUNDOS, IDA E VOLTA:", "A ROCHA ESTÁ A *1.500 METROS*.", ('F10',)),
        (28.8, 35.6, "MAS O PING REVELA ONDE ELE ESTÁ.", "POR ISSO ELE MAIS *ESCUTA*: PASSIVO.", ('F3',)),
    ],
    'resumo': [
        (0.5, 7.0, "PARA DESCER: *ÁGUA* NOS TANQUES.", "MAIS PESO QUE EMPUXO.", ('F2', 'F1')),
        (7.3, 14.4, "PARA PARAR: PESO *IGUAL* AO EMPUXO,", "ACERTADO NOS TANQUES DE AJUSTE.", ('F2', 'F1')),
        (14.7, 21.8, "PARA SUBIR: O *AR COMPRIMIDO*", "EMPURRA A ÁGUA PARA FORA.", ('F2',)),
        (22.1, 29.6, "E O CASCO REDONDO AGUENTA *+1 ATM*", "A CADA 10 METROS DE MAR.", ('F6', 'F5')),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Archimedes\' principle"', 'https://en.wikipedia.org/wiki/Archimedes%27_principle'),
    'F2': ('Wikipedia, "Ballast tank"', 'https://en.wikipedia.org/wiki/Ballast_tank'),
    'F3': ('Wikipedia, "Submarine"', 'https://en.wikipedia.org/wiki/Submarine'),
    'F4': ('Wikipedia, "Diving plane"', 'https://en.wikipedia.org/wiki/Diving_plane'),
    'F5': ('Wikipedia, "Submarine hull"', 'https://en.wikipedia.org/wiki/Submarine_hull'),
    'F6': ('Wikipedia, "Submarine depth ratings"', 'https://en.wikipedia.org/wiki/Submarine_depth_ratings'),
    'F7': ('The Lean Submariner, "How low can you go? (an unclassified accounting of the term Test Depth)"',
           'https://theleansubmariner.com/2019/06/26/how-low-can-you-go-an-unclassified-accounting-of-the-term-test-depth/'),
    'F8': ('Wikipedia, "Speed of sound" (cerca de 1.500 m/s na água salgada)', 'https://en.wikipedia.org/wiki/Speed_of_sound'),
    'F9': ('Conta a partir de F6 (1 atm = 101 kPa = cerca de 1,03 kg-força por centímetro quadrado)', None),
    'F10': ('Conta a partir de F8 (1.500 m/s x 2 s / 2 = 1.500 m)', None),
    'F11': ('Conta a partir de F6 (a pressão da água cresce com a fundura)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'arquimedes': 'Arquimedes de novo: peso e empuxo',
                'partes': 'As partes do submarino', 'mergulho': 'Como ele afunda: tanques de lastro',
                'equilibrio': 'Parado no meio da água', 'subir': 'Como ele sobe: ar comprimido',
                'lemes': 'Lemes de profundidade e hélice', 'pressao': '1 atmosfera a cada 10 metros',
                'casco': 'Por que o casco é redondo', 'limite': 'Até onde ele desce',
                'sonar': 'Sonar: enxergar com o som', 'resumo': 'Resumo'}

DESCRICAO = """Como um submarino de aço consegue afundar, parar no meio da água e voltar para a superfície? Ele não muda de tamanho: muda de peso, enchendo os tanques de lastro com água do mar ou com ar.

Neste vídeo a gente relembra Arquimedes (do episódio do navio), abre o submarino peça por peça e acompanha um mergulho com o contador de fundura e o visor dos tanques: respiros abertos, água entrando, tanques de ajuste, ar comprimido para subir. Depois: os lemes de profundidade e a hélice, a pressão que sobe 1 atmosfera a cada 10 metros, por que o casco é um tubo redondo, até onde um submarino pode descer e como o sonar enxerga com o som.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O submarino desenhado é genérico e de casco simples (tanques de lastro na proa e na popa); muitos submarinos têm casco duplo, com tanques em volta do casco resistente.
- Peso e empuxo aparecem como barras, sem números. Na superfície, o quanto ele afunda foi calculado como se o casco tivesse paredes retas.
- O contador de fundura mede o eixo do casco. As fundas do mergulho (50 m, 100 m) são exemplos da animação, não de um submarino real.
- Mostramos um tanque de ajuste no meio e dois de compensação (proa e popa); cada projeto tem o seu arranjo.
- Na superfície, submarinos de verdade costumam terminar de esvaziar os tanques com um soprador de baixa pressão; aqui o ar comprimido faz tudo.
- "Cerca de 1 kg por centímetro quadrado" arredonda 1,03 kg-força. A pressão do ar (1 atm) já existe na superfície; a fundura soma mais 1 atm a cada 10 m.
- As fontes dão 250 a 400 m (Wikipedia, "Submarine") e 250 a 350 m (Wikipedia, "Submarine hull") para submarinos de aço de hoje; usamos a primeira faixa.
- No sonar, o som foi desenhado em câmera lenta (4 vezes mais devagar).

Fontes
{fontes}

#submarino #comofunciona #pixelart #fisica #arquimedes #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nos cortes o submarino é
# desenhado mais curto (150 px) e centrado no recorte (x + 90).
PREFIXO = 'ep14-submarino'
CORTES = [
    dict(id='c1', de=('mergulho', 0.0), ate=('mergulho', 36.0), x=60, gancho=['COMO ELE', 'AFUNDA?'],
         titulo='Como um submarino afunda de propósito? 🌊',
         descricao='Respiros abertos em cima, válvulas abertas embaixo: a água do mar entra nos tanques de lastro e empurra o ar para fora. Mais peso que empuxo, e ele desce.'),
    dict(id='c2', de=('subir', 0.0), ate=('subir', 36.0), x=60, gancho=['COMO ELE', 'SOBE?'],
         titulo='Como um submarino volta para a superfície?',
         descricao='Os respiros fecham e o ar comprimido das garrafas empurra a água para fora dos tanques. Menos peso, o empuxo ganha e ele sobe.'),
    dict(id='c3', de=('pressao', 7.8), ate=('pressao', 42.6), x=60, gancho=['A 300 M', 'DE FUNDO'],
         titulo='Quanto a água aperta um submarino a 300 metros?',
         descricao='A cada 10 metros de mar a pressão sobe 1 atmosfera, cerca de 1 kg em cada centímetro quadrado. A 300 metros são 30 atmosferas a mais.'),
    dict(id='c4', de=('casco', 0.0), ate=('casco', 22.0), x=60, gancho=['POR QUE', 'REDONDO?'],
         titulo='Por que o casco do submarino é redondo? ⭕',
         descricao='Apertado por fora, o quadrado entorta as paredes retas. No redondo a pressão se espalha por igual, e ele aguenta muito mais.'),
    dict(id='c5', de=('lemes', 0.0), ate=('lemes', 29.0), x=60, gancho=['DESCER', 'ANDANDO'],
         titulo='Para que servem os lemes de profundidade do submarino?',
         descricao='Andando, o submarino inclina os lemes da proa e da popa: o nariz aponta para baixo ou para cima e a hélice leva ele em diagonal.'),
    dict(id='c6', de=('sonar', 0.0), ate=('sonar', 29.0), x=40, gancho=['ENXERGAR', 'COM SOM'],
         titulo='Como o submarino enxerga no escuro? 🔊',
         descricao='Com o sonar. O som anda cerca de 1.500 metros por segundo no mar: um eco que volta em 2 segundos vem de algo a 1.500 metros.'),
]
