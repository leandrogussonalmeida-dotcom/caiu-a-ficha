#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep25 (série POR DENTRO): Como funciona o motor a jato.

Par do ep01 (motor do carro, 4 tempos). O gancho: o motor a jato faz os mesmos
4 tempos do motor do carro (admissão, compressão, combustão, escape), só que
TODOS AO MESMO TEMPO, cada um num lugar do motor, sem parar: SUGA (fan),
ESPREME (compressor), QUEIMA (câmara de combustão) e SOPRA (turbina e bocal).

Protagonista: um pedacinho de ar que atravessa um turbofan genérico aberto ao
meio (sem logotipo, sem pintura de companhia), com um painel: pressão (vezes a
de fora), temperatura, velocidade e onde ele está (ESTÁGIO x DE 13). Os números
do painel saem de um MODELO SIMPLES deste vídeo (ep25_desenho.Modelo): ciclo de
Brayton ideal com ar (NASA, F5), fan 1,5:1, pressão total 40:1 (dentro da faixa
de F4), 13 estágios de compressor com o mesmo salto cada, 1.500 °C na entrada da
turbina (dentro de F7), turbina de alta tirando o trabalho do compressor de alta
e a de baixa o do fan (10 kg por fora para 1 kg no miolo) e do booster.
Resultado: 553 °C na saída do compressor (F11 dá 200 a 550 °C), pressão
40 -> ~15 -> ~3,4 na turbina e ~608 °C na saída dela.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Rolls-Royce UTC / Univ. de Cambridge, "How does a Jet Engine work?": o
      motor empurra o ar para trás e a reação empurra o avião para a frente
      (3ª lei de Newton); o ciclo resumido em "Suck-Squeeze-Bang-Blow".
  F2  NASA Glenn, "Turbofan Engine": o núcleo é cercado por um fan na frente e
      uma turbina a mais atrás; parte do ar passa pelo fan e entra no
      compressor do núcleo e depois no queimador, onde é misturado ao
      combustível e queima; o resto contorna o motor; o gás quente passa pelas
      turbinas e sai pelo bocal; fan e turbina do fan num eixo separado
      ("two spool"); o empuxo vem do núcleo e do fan.
  F3  Wikipedia, "Bypass ratio": motores de aviões de passageiros até 12:1
      (tabela: CFM56 5,0 a 6,6 ... PW1000G 12,5); 10:1 = 10 kg por fora para
      1 kg pelo núcleo; no turbofan de alto bypass o fan e o bocal dele dão a
      maior parte do empuxo.
  F4  Wikipedia, "Overall pressure ratio": motores civis modernos operam
      entre 40 e 55:1.
  F5  NASA Glenn, "Brayton Cycle": o compressor aumenta a pressão e a
      temperatura; a queima acontece a pressão constante; a turbina tira
      trabalho do gás; turbina e compressor no mesmo eixo; o bocal leva o gás
      de volta à pressão de fora.
  F6  Wikipedia, "Gas turbine": motor de fluxo contínuo; o ar passa sem parar
      pelo compressor, pela câmara e pela turbina; turbofans modernos têm 2
      ou 3 eixos e muitas fileiras de pás no compressor e na turbina.
  F7  Wikipedia, "Turbine blade": o gás (1.300 a 1.800 K, cerca de 1.030 a
      1.530 °C) pode passar do ponto de fusão do material da pá (1.300 a
      1.400 K); o resfriamento usa ar mais frio tirado do compressor; no
      resfriamento por filme o ar sai por muitos furos pequenos; revestimentos
      de barreira térmica aguentam ~90 °C a mais.
  F8  Wikipedia, "Jet engine": motores a jato fazem empuxo jogando um jato
      para trás em alta velocidade; o foguete leva todo o propelente e o
      oxidante a bordo e não precisa do ar (o motor a jato respira o ar); ondas
      de choque da ponta supersônica do fan na decolagem; patente de Whittle
      em janeiro de 1930; motor HeS 1 de von Ohain funcionando em setembro de
      1937; He 178 voou em 27 de agosto de 1939.
  F9  Wikipedia, "Frank Whittle": patente em 1930; o motor WU começou os
      testes em 12 de abril de 1937; o E.28/39 voou em 15 de maio de 1941;
      Whittle acabou convencido de que o trabalho de von Ohain foi
      independente; von Ohain fez o primeiro motor a jato a voar.
  F10 Wikipedia, "Embraer E-Jet family": jatos regionais da Embraer
      (brasileira), bimotores, com 2 turbofans sob as asas.
  F11 Stanford (projeto de alunos), "The Jet Engine: a historical
      introduction": SUCK, SQUEEZE, BANG, BLOW; o compressor esquenta o ar a
      200 a 550 °C; compressores passam de 40:1.
  F12 Conta / modelo deste vídeo (ver acima e ep25_desenho.Modelo).
  F13 Wikipedia, "Four-stroke engine": admissão, compressão, combustão
      (potência) e escape.
  F14 Wikipedia, "Turbofan": spool = fan ou compressor e a turbina que o
      move, no mesmo eixo; fan no eixo de baixa pressão e compressor no de
      alta; o eixo de baixa gira mais devagar para manter a velocidade da
      ponta do fan (grande) dentro do limite; eixos coaxiais.
"""

TITULO = "Como funciona o motor a jato | Um turbofan por dentro em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=5, papel='break'),                  # 15 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),                  # 6 s
    dict(id='aviao', gen='lofi', bars=8, papel='drop'),                    # 24 s
    dict(id='pecas', gen='synthwave', bars=20, papel='drop'),              # 48 s (6 peças x 8 s)
    dict(id='admissao', gen='lofi', bars=12, papel='drop'),                # 36 s  tempo 1
    dict(id='compressor', gen='house', bars=16, papel='drop', bpm=120),    # 32 s  tempo 2 (13 estágios nos compassos)
    dict(id='combustao', gen='lofi', bars=12, papel='drop'),               # 36 s  tempo 3
    dict(id='turbina', gen='lofi', bars=12, papel='drop'),                 # 36 s
    dict(id='eixos', gen='synthwave', bars=10, papel='drop'),              # 24 s
    dict(id='calor', gen='lofi', bars=10, papel='break'),                  # 30 s
    dict(id='bocal', gen='lofi', bars=12, papel='drop'),                   # 36 s  tempo 4
    dict(id='decolagem', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='foguete', gen='lofi', bars=8, papel='break'),                 # 24 s
    dict(id='ritmo', gen='house', bars=12, papel='drop', bpm=120),         # 24 s
    dict(id='historia', gen='lofi', bars=11, papel='break'),               # 33 s
    dict(id='resumo', gen='lofi', bars=11, papel='drop'),                  # 33 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                     # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 7.4, "O MOTOR DO CARRO FAZ 4 TEMPOS,", "*UM DE CADA VEZ*.", ('F13',)),
        (7.6, 14.6, "O MOTOR A JATO FAZ OS MESMOS 4,", "*TODOS AO MESMO TEMPO, SEM PARAR*.", ('F6', 'F1')),
    ],
    'aviao': [
        (0.5, 6.8, "UM JATO DE PASSAGEIROS VOA COM", "MOTORES *TURBOFAN* SOB AS ASAS.", ('F2', 'F10')),
        (7.0, 13.4, "OS JATOS REGIONAIS FEITOS NO BRASIL", "TAMBÉM USAM *DOIS TURBOFANS*.", ('F10',)),
        (13.6, 19.4, "LÁ DENTRO NÃO TEM PISTÃO.", "SÓ FILEIRAS DE PÁS QUE *GIRAM*.", ('F6',)),
        (19.6, 23.8, "VAMOS *ABRIR UM* AO MEIO.", "", ()),
    ],
    'pecas': [
        (0.3, 7.6, "NA FRENTE, O *FAN*: UM VENTILADOR", "GIGANTE QUE PUXA O AR.", ('F2',)),
        (8.0, 15.6, "O *COMPRESSOR*: MUITAS FILEIRAS DE", "PÁS PEQUENAS QUE APERTAM O AR.", ('F2', 'F6')),
        (16.0, 23.6, "A *CÂMARA DE COMBUSTÃO*: AQUI O", "COMBUSTÍVEL QUEIMA COM O AR.", ('F2',)),
        (24.0, 31.6, "A *TURBINA*: O GÁS QUENTE", "FAZ AS PÁS DELA GIRAREM.", ('F2', 'F5')),
        (32.0, 39.6, "OS *EIXOS* LEVAM ESSE GIRO DA", "TURBINA ATÉ O COMPRESSOR E O FAN.", ('F2', 'F5')),
        (40.0, 47.6, "E O *BOCAL*: POR ONDE O GÁS SAI", "PARA TRÁS, MUITO RÁPIDO.", ('F2', 'F8')),
    ],
    'admissao': [
        (0.5, 6.8, "TEMPO 1: *SUGA*. ACOMPANHE ESTE", "PEDACINHO DE AR.", ('F1', 'F11')),
        (7.0, 13.4, "O FAN PUXA MUITO AR. A MAIOR PARTE", "*CONTORNA* O MIOLO DO MOTOR.", ('F2',)),
        (13.6, 20.4, "PARA CADA 1 KG QUE ENTRA NO MIOLO,", "*DE 5 A 12 KG* PASSAM POR FORA.", ('F3',)),
        (20.6, 27.4, "ESSE AR DE FORA, SÓ SOPRADO PELO", "FAN, DÁ *A MAIOR PARTE DO EMPURRÃO*.", ('F3',)),
        (27.6, 35.6, "NA DECOLAGEM, A PONTA DAS PÁS DO", "FAN PASSA DA *VELOCIDADE DO SOM*.", ('F8', 'F14')),
    ],
    'compressor': [
        (0.5, 6.6, "TEMPO 2: *ESPREME*. O NOSSO AR", "ENTRA NO COMPRESSOR.", ('F1', 'F2')),
        (6.8, 12.8, "CADA FILEIRA DE PÁS EMPURRA E", "APERTA UM POUCO MAIS. *NO RITMO*.", ('F5', 'F6')),
        (13.0, 19.6, "AQUI SÃO *13 ESTÁGIOS*. A PRESSÃO", "SOBE EM CADA UM.", ('F12', 'F5')),
        (19.8, 25.8, "NO FIM: *40 VEZES* A PRESSÃO DE FORA.", "OS MOTORES DE HOJE: 40 A 55.", ('F4', 'F12')),
        (26.0, 31.8, "APERTADO, O AR ESQUENTA:", "*CERCA DE 550 °C*.", ('F5', 'F11', 'F12')),
    ],
    'combustao': [
        (0.5, 6.8, "TEMPO 3: *QUEIMA*. UM BICO BORRIFA", "COMBUSTÍVEL NO AR APERTADO.", ('F1', 'F2')),
        (7.0, 13.8, "NO CARRO, CADA QUEIMA É UM ESTOURO.", "AQUI A CHAMA *NÃO APAGA*.", ('F13', 'F6')),
        (14.0, 20.8, "O AR CHEGA SEM PARAR, E A CHAMA", "QUEIMA *SEM PARAR*.", ('F6',)),
        (21.0, 27.8, "O GÁS CHEGA A *CERCA DE 1.500 °C*.", "E A PRESSÃO QUASE NÃO MUDA.", ('F7', 'F5')),
        (28.0, 35.6, "QUENTE, ELE SE EXPANDE E CORRE", "PARA A SAÍDA: *A TURBINA*.", ('F5',)),
    ],
    'turbina': [
        (0.5, 6.8, "O GÁS EMPURRA AS PÁS DA *TURBINA*,", "COMO O VENTO NUM CATA-VENTO.", ('F5',)),
        (7.0, 13.8, "A TURBINA *TIRA ENERGIA* DO GÁS:", "A PRESSÃO E A TEMPERATURA CAEM.", ('F5',)),
        (14.0, 20.8, "ESSA ENERGIA GIRA O COMPRESSOR", "E O FAN, LÁ NA FRENTE.", ('F2', 'F5')),
        (21.0, 27.8, "A PRESSÃO DESCE DE *40* PARA", "*CERCA DE 3* VEZES A DE FORA.", ('F12',)),
        (28.0, 35.6, "E O GÁS SAI DA TURBINA AINDA", "QUENTE: *CERCA DE 600 °C*.", ('F12',)),
    ],
    'eixos': [
        (0.3, 6.0, "SÃO *DOIS EIXOS*, UM DENTRO DO", "OUTRO, GIRANDO SEPARADOS.", ('F2', 'F14')),
        (6.2, 12.0, "O DE *ALTA*: A TURBINA DA FRENTE", "GIRA O COMPRESSOR.", ('F14',)),
        (12.2, 18.0, "O DE *BAIXA*: A TURBINA DE TRÁS", "GIRA O FAN, MAIS DEVAGAR.", ('F2', 'F14')),
        (18.2, 23.8, "DEVAGAR PARA A PONTA DO FAN, QUE", "É ENORME, NÃO PASSAR DO LIMITE.", ('F14',)),
    ],
    'calor': [
        (0.5, 7.4, "UM PROBLEMA: O GÁS É *MAIS QUENTE*", "*QUE O PONTO DE FUSÃO* DO METAL.", ('F7',)),
        (7.6, 14.4, "POR QUE A PÁ NÃO DERRETE? AR DO", "COMPRESSOR CORRE *POR DENTRO* DELA.", ('F7',)),
        (14.6, 21.4, "ELE SAI POR *FUROS MINÚSCULOS* E", "COBRE A PÁ COM UMA PELE DE AR.", ('F7',)),
        (21.6, 29.6, "E UMA *CAMADA ISOLANTE* POR FORA", "PROTEGE O METAL DO CALOR.", ('F7',)),
    ],
    'bocal': [
        (0.5, 6.8, "TEMPO 4: *SOPRA*. NO BOCAL O GÁS", "VOLTA À PRESSÃO DE FORA E ACELERA.", ('F1', 'F5')),
        (7.0, 13.8, "O AR DO FAN SAI EM VOLTA, FRIO,", "*TAMBÉM EMPURRADO PARA TRÁS*.", ('F2',)),
        (14.0, 20.8, "O MOTOR EMPURRA O AR PARA TRÁS,", "O AR EMPURRA O MOTOR *PARA A FRENTE*.", ('F1',)),
        (21.0, 27.8, "É A *TERCEIRA LEI DE NEWTON*,", "A MESMA DO FOGUETE.", ('F1',)),
        (28.0, 35.6, "ESSE EMPURRÃO PARA A FRENTE", "SE CHAMA *EMPUXO*.", ('F8',)),
    ],
    'decolagem': [
        (0.5, 7.4, "NA PISTA, OS MOTORES VÃO PARA", "A *FORÇA MÁXIMA*.", ()),
        (7.6, 14.4, "O EMPUXO VENCE O ATRITO E O AR:", "O AVIÃO *ACELERA*.", ('F8',)),
        (14.6, 21.4, "RÁPIDO O BASTANTE, AS ASAS FAZEM", "O RESTO: O AVIÃO *DECOLA*.", ()),
        (21.6, 29.6, "O MOTOR SÓ EMPURRA PARA A FRENTE.", "QUEM SEGURA O AVIÃO NO AR É A *ASA*.", ()),
    ],
    'foguete': [
        (0.5, 7.4, "O FOGUETE TAMBÉM JOGA GÁS PARA", "TRÁS, MAS LEVA O *PRÓPRIO OXIDANTE*.", ('F8',)),
        (7.6, 15.4, "O MOTOR A JATO *USA O AR DE FORA*:", "O OXIGÊNIO VEM DE GRAÇA.", ('F8',)),
        (15.6, 23.6, "POR ISSO ELE *NÃO FUNCIONA* NO", "ESPAÇO, ONDE NÃO TEM AR.", ('F8',)),
    ],
    'ritmo': [
        (0.5, 7.6, "NO CARRO: UM TEMPO POR BATIDA,", "*UM DE CADA VEZ*.", ('F13',)),
        (8.0, 15.6, "NO JATO: OS 4 TEMPOS EM *TODAS*", "AS BATIDAS, CADA UM NO SEU LUGAR.", ('F6',)),
        (16.0, 23.6, "*SUGA, ESPREME, QUEIMA E SOPRA*.", "SEM PARAR.", ('F1', 'F11')),
    ],
    'historia': [
        (0.5, 7.6, "EM *1930*, O INGLÊS FRANK WHITTLE", "PATENTEOU UM MOTOR A JATO.", ('F9', 'F8')),
        (7.8, 14.6, "EM *1937*, OS PRIMEIROS MOTORES", "A JATO FUNCIONARAM EM TESTE.", ('F9', 'F8')),
        (14.8, 21.6, "NA ALEMANHA, HANS VON OHAIN FEZ O", "SEU *SEM DEPENDER* DO INGLÊS.", ('F9',)),
        (21.8, 28.4, "EM *1939*, O MOTOR DELE FEZ VOAR", "O PRIMEIRO AVIÃO A JATO.", ('F8', 'F9')),
        (28.6, 32.8, "OS DE HOJE SÃO TURBOFANS: O MESMO", "MIOLO, COM UM *FAN GIGANTE*.", ('F2',)),
    ],
    'resumo': [
        (0.5, 7.6, "*SUGA*: O FAN PUXA O AR.", "A MAIOR PARTE PASSA POR FORA.", ('F2', 'F3')),
        (7.8, 15.0, "*ESPREME*: 13 FILEIRAS DE PÁS,", "40 VEZES A PRESSÃO DE FORA.", ('F4', 'F12')),
        (15.2, 22.4, "*QUEIMA*: A CHAMA NÃO APAGA,", "CERCA DE 1.500 °C.", ('F6', 'F7')),
        (22.6, 32.6, "*SOPRA*: O GÁS GIRA A TURBINA E", "SAI ATRÁS, EMPURRANDO O AVIÃO.", ('F1', 'F5')),
    ],
}

FONTES = {
    'F1': ('Rolls-Royce UTC / Universidade de Cambridge, "How does a Jet Engine work?"',
           'https://www.rrutc.msm.cam.ac.uk/node/247'),
    'F2': ('NASA Glenn Research Center, "Turbofan Engine"', 'https://www.grc.nasa.gov/www/k-12/airplane/aturbf.html'),
    'F3': ('Wikipedia, "Bypass ratio"', 'https://en.wikipedia.org/wiki/Bypass_ratio'),
    'F4': ('Wikipedia, "Overall pressure ratio" (motores civis modernos: 40 a 55:1)',
           'https://en.wikipedia.org/wiki/Overall_pressure_ratio'),
    'F5': ('NASA Glenn Research Center, "Brayton Cycle"', 'https://www.grc.nasa.gov/www/k-12/airplane/brayton.html'),
    'F6': ('Wikipedia, "Gas turbine"', 'https://en.wikipedia.org/wiki/Gas_turbine'),
    'F7': ('Wikipedia, "Turbine blade"', 'https://en.wikipedia.org/wiki/Turbine_blade'),
    'F8': ('Wikipedia, "Jet engine"', 'https://en.wikipedia.org/wiki/Jet_engine'),
    'F9': ('Wikipedia, "Frank Whittle"', 'https://en.wikipedia.org/wiki/Frank_Whittle'),
    'F10': ('Wikipedia, "Embraer E-Jet family"', 'https://en.wikipedia.org/wiki/Embraer_E-Jet_family'),
    'F11': ('Stanford University (projeto de alunos), "The Jet Engine: a historical introduction"',
            'https://cs.stanford.edu/people/eroberts/courses/ww2/projects/jet-airplanes/how.html'),
    'F12': ('Conta / modelo deste vídeo: ciclo de Brayton ideal com ar, fan 1,5:1, pressão total 40:1 em 13 '
            'estágios iguais, 1.500 °C na entrada da turbina, 10 kg por fora para 1 kg no miolo', None),
    'F13': ('Wikipedia, "Four-stroke engine"', 'https://en.wikipedia.org/wiki/Four-stroke_engine'),
    'F14': ('Wikipedia, "Turbofan"', 'https://en.wikipedia.org/wiki/Turbofan'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'aviao': 'O turbofan sob a asa', 'pecas': 'As peças do motor a jato',
                'admissao': 'Tempo 1: suga (o fan e o ar que contorna)', 'compressor': 'Tempo 2: espreme (13 estágios no ritmo)',
                'combustao': 'Tempo 3: queima (a chama que não apaga)', 'turbina': 'A turbina tira energia do gás',
                'eixos': 'Dois eixos, um dentro do outro', 'calor': 'Mais quente que o ponto de fusão',
                'bocal': 'Tempo 4: sopra (Newton e o empuxo)', 'decolagem': 'A decolagem',
                'foguete': 'Jato x foguete: o oxigênio de graça', 'ritmo': 'Os 4 tempos no ritmo da música',
                'historia': 'Whittle, von Ohain e 1939', 'resumo': 'Resumo'}

DESCRICAO = """O motor a jato faz os mesmos 4 tempos do motor do carro (admissão, compressão, combustão e escape), só que todos ao mesmo tempo, cada um num lugar do motor, sem parar: SUGA, ESPREME, QUEIMA e SOPRA.

Neste vídeo a gente abre ao meio um turbofan genérico, igual aos que ficam sob a asa dos jatos de passageiros, e acompanha um pedacinho de ar do começo ao fim, com um painel de pressão, temperatura e velocidade: o fan gigante (a maior parte do ar passa por fora do miolo), os 13 estágios do compressor apertando o ar até 40 vezes a pressão de fora (no ritmo da música), a chama que nunca apaga a cerca de 1.500 °C, a turbina que tira energia do gás para girar o compressor e o fan, os dois eixos, o truque que impede as pás de derreter e o bocal, onde a terceira lei de Newton vira empuxo. No fim: por que o jato não funciona no espaço (e o foguete sim), e Whittle e von Ohain, que inventaram o motor a jato nos anos 1930.

É o par do episódio do motor do carro: lá os 4 tempos acontecem um de cada vez, no mesmo cilindro.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O motor é genérico (não é nenhum motor real). Desenhamos 3 estágios de booster + 10 de compressor de alta (13 no total), 2 de turbina de alta e 5 de baixa; motores de verdade variam.
- Os números do painel saem de um modelo simples deste vídeo: ciclo de Brayton ideal com ar, sem perdas (fan 1,5:1, pressão total 40:1 com o mesmo salto em cada estágio, 1.500 °C na entrada da turbina, 10 kg de ar por fora para cada 1 kg no miolo). Um motor real perde um pouco em cada etapa, então as temperaturas e pressões de verdade são parecidas, não iguais.
- A velocidade no painel é só uma barra (devagar no compressor, rápida no bocal), sem número.
- O motor está desenhado em corte, com as pás de lado; o giro aparece como pás passando. A velocidade de giro na tela é muito mais lenta que a real.
- Na câmara de combustão desenhamos um bico só, de cada lado; motores reais têm vários bicos em volta do anel.
- Na cena do bocal, o ar do fan e o gás quente saem por bocais separados, como na maioria dos turbofans de jatos de passageiros.
- A pá de turbina aberta é um desenho esquemático: os canais e os furos de resfriamento de verdade são bem menores e mais numerosos.

Fontes
{fontes}

#motoraJato #turbofan #aviao #comofunciona #pixelart #fisica #newton #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Em VERTICAL as
# cenas recentram a câmera do motor em x_corte + 90 (= 150 para x = 60).
PREFIXO = 'ep25-jato'
CORTES = [
    dict(id='c1', de=('compressor', 0.0), ate=('compressor', 32.0), x=60, gancho=['13 ESTÁGIOS', 'NO RITMO'],
         titulo='O compressor do motor a jato apertando o ar no ritmo da música ✈️',
         descricao='Cada fileira de pás aperta o ar um pouco mais. Em 13 estágios a pressão chega a 40 vezes a de fora, e o ar esquenta até cerca de 550 °C.'),
    dict(id='c2', de=('combustao', 0.0), ate=('combustao', 36.0), x=60, gancho=['A CHAMA', 'QUE NÃO APAGA'],
         titulo='A chama que nunca apaga dentro do motor a jato 🔥',
         descricao='No carro, cada queima é um estouro. No motor a jato o ar chega sem parar e a chama queima sem parar, a cerca de 1.500 °C.'),
    dict(id='c3', de=('calor', 0.0), ate=('calor', 30.0), x=60, gancho=['POR QUE', 'NÃO DERRETE?'],
         titulo='O gás é mais quente que o ponto de fusão da pá. Por que ela não derrete?',
         descricao='Ar do compressor corre por dentro da pá da turbina e sai por furos minúsculos, cobrindo a pá com uma pele de ar. Uma camada isolante por fora ajuda.'),
    dict(id='c4', de=('admissao', 7.0), ate=('admissao', 36.0), x=60, gancho=['O AR QUE', 'PASSA POR FORA'],
         titulo='A maior parte do ar nem entra no motor a jato 🌀',
         descricao='Para cada 1 kg de ar que entra no miolo do turbofan, de 5 a 12 kg passam por fora, soprados pelo fan. Esse ar de fora dá a maior parte do empurrão.'),
    dict(id='c5', de=('bocal', 7.0), ate=('bocal', 36.0), x=60, gancho=['AÇÃO E', 'REAÇÃO'],
         titulo='Como o motor a jato empurra o avião: a terceira lei de Newton',
         descricao='O motor empurra o ar para trás, e o ar empurra o motor para a frente. Esse empurrão se chama empuxo.'),
    dict(id='c6', de=('ritmo', 0.0), ate=('ritmo', 24.0), x=60, gancho=['CARRO', 'X JATO'],
         titulo='Motor do carro x motor a jato: os mesmos 4 tempos 🎵',
         descricao='No carro, um tempo por batida, um de cada vez. No jato, os 4 tempos acontecem o tempo todo, cada um num lugar do motor: suga, espreme, queima e sopra.'),
]
