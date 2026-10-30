#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep02: Como um avião de 400 toneladas voa (série COMO VOA / FLUTUA).

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep02_motor.py` (cenas) e `ep02_desenho.py` (avião, céu, túnel de vento com o
escoamento calculado, turbofan). `longo_verificar.py --roteiro ep02_roteiro`
reprova legenda que não cabe, caractere sem glifo, legenda curta e fato sem fonte.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 29/10/2026)
  F1  O "tempo de trânsito igual" está errado: o ar de cima chega bem antes ao
      bordo de fuga; a forma curva os filetes de ar, pressão menor em cima e
      maior embaixo. Univ. de Cambridge, "How wings really work" (Babinsky).
  F2  NASA Glenn, "Equal Transit Theory": teoria errada; asa simétrica gera
      sustentação; avião voa invertido; o que importa é desviar (virar) o
      escoamento; o ar de cima anda mais rápido; a diferença de pressão produz a
      sustentação.
  F3  NASA Glenn, "Newton's Third Law": o ar que passa pela asa é desviado para
      baixo; em reação, a asa é empurrada para cima.
  F4  NASA Glenn, "Four Forces on an Airplane": peso (para o centro da Terra,
      inclui combustível), sustentação (quase toda das asas), arrasto, tração;
      equilibradas = velocidade constante; desequilibradas = acelera.
  F5  Boeing 747-400: peso máximo de decolagem 396.893 kg; 4 motores de
      251-282 kN cada; cruzeiro Mach 0,855. Wikipedia, "Boeing 747-400" (e
      "List of airliners by maximum takeoff weight": 396.900 kg).
  F6  Wikipedia, "Takeoff": jatos comerciais decolam a 240-285 km/h; slats e
      flaps abertos antes da decolagem e recolhidos na subida; na rotação o
      nariz sobe a 5°-15°.
  F7  Aerospaceweb, "Airliner Takeoff Speeds": 747 com 362.870 kg decola a
      ~290 km/h.
  F8  NASA Glenn, "The Lift Equation": L = Cl x densidade x V²/2 x área.
  F9  Wikipedia, "Stall (fluid dynamics)": ângulo crítico típico ~15°;
      separação do escoamento; sustentação cai; estol em qualquer velocidade;
      "stick shaker" padrão em aviões comerciais; sair abaixando o nariz;
      flaps/slats baixam a velocidade de estol.
  F10 Wikipedia, "Flap (aeronautics)": flap aumenta a curvatura e a
      sustentação máxima, aumenta o arrasto; parcial na decolagem, total no
      pouso (aproximação mais lenta, pouso mais curto); recolhido quando não precisa.
  F11 Wikipedia, "Leading-edge slat": slat deixa a asa ir a um ângulo maior
      antes do estol, voar mais devagar; recolhido em voo normal.
  F12 NASA Glenn, "Turbofan Engine": ventilador, ar que vai ao núcleo
      (compressor, queimador, turbinas, bocal) e ar que contorna; o ventilador
      e a turbina dele ligados por um eixo; a maioria dos aviões comerciais usa turbofan.
  F13 Wikipedia, "Cruise (aeronautics)": cruzeiro típico 9.400-11.600 m;
      widebodies a Mach 0,85 (~900 km/h); a altitude equilibra velocidade e a
      perda de tração/eficiência dos motores no alto; ar menos denso no alto.
  F14 Wikipedia, "International Standard Atmosphere": nível do mar 1,225 kg/m³
      e 15 °C; a 11.000 m 0,3639 kg/m³ e -56,5 °C.
  F15 NASA Glenn, "The Drag Equation": D = Cd x densidade x V²/2 x área.
  F16 Conta (F5): 4 x 282 kN = 1.128 kN; peso 396.893 kg x 9,81 = 3.894 kN;
      1.128/3.894 = 29% (menos de 1/3).
  F17 Conta (F14): 0,3639 / 1,225 = 30% (menos de 1/3).
  F18 Conta (F8): sustentação proporcional a V²: 2x a velocidade = 4x, 3x = 9x.
"""

TITULO = "Como um avião de 400 toneladas voa | Sustentação, estol e cruzeiro em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=5, papel='break'),             # 15 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='forcas', gen='synthwave', bars=16, papel='drop'),        # 38,4 s
    dict(id='mito', gen='lofi', bars=12, papel='drop'),               # 36 s
    dict(id='asa', gen='lofi', bars=16, papel='drop'),                # 48 s
    dict(id='velocidade', gen='house', bars=15, papel='drop', bpm=120),   # 30 s
    dict(id='decolagem', gen='synthwave', bars=19, papel='drop'),     # 45,6 s
    dict(id='angulo', gen='lofi', bars=11, papel='drop'),             # 33 s
    dict(id='estol', gen='lofi', bars=13, papel='break'),             # 39 s
    dict(id='motores', gen='synthwave', bars=15, papel='drop'),       # 36 s
    dict(id='altitude', gen='lofi', bars=16, papel='drop'),           # 48 s
    dict(id='cruzeiro', gen='lofi', bars=11, papel='break'),          # 33 s
    dict(id='pouso', gen='lofi', bars=11, papel='drop'),              # 33 s
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),              # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.4, 5.0, "ESTE JATO PODE DECOLAR PESANDO", "QUASE *400 TONELADAS*.", ('F5',)),
        (5.2, 9.8, "E MESMO ASSIM SAI DO CHÃO", "A UNS *290 KM/H*.", ('F7',)),
        (10.0, 14.8, "COMO? A RESPOSTA ESTÁ NA *ASA*.", "", ()),
    ],
    'forcas': [
        (0.4, 5.0, "NO AR, *4 FORÇAS* AGEM NO AVIÃO.", "", ('F4',)),
        (5.2, 9.8, "O *PESO* PUXA PARA BAIXO,", "SEMPRE PARA O CENTRO DA TERRA.", ('F4',)),
        (10.0, 14.6, "A *SUSTENTAÇÃO* EMPURRA PARA CIMA.", "QUASE TODA ELA VEM DAS ASAS.", ('F4',)),
        (14.8, 19.4, "O *ARRASTO* É O AR SEGURANDO", "O AVIÃO PARA TRÁS.", ('F4',)),
        (19.6, 24.2, "A *TRAÇÃO* DOS MOTORES", "EMPURRA PARA A FRENTE.", ('F4',)),
        (24.4, 29.6, "TRAÇÃO MAIOR QUE ARRASTO:", "O AVIÃO *ACELERA*.", ('F4',)),
        (29.8, 38.0, "FORÇAS EM EQUILÍBRIO: VOO RETO,", "COM *VELOCIDADE CONSTANTE*.", ('F4',)),
    ],
    'mito': [
        (0.4, 5.6, "TALVEZ VOCÊ TENHA APRENDIDO ASSIM:", "O AR DE CIMA FAZ UM CAMINHO MAIOR...", ()),
        (5.8, 11.0, "...ENTÃO CORRE MAIS PARA *CHEGAR*", "*JUNTO* COM O AR DE BAIXO.", ()),
        (11.2, 15.8, "ISSO É UM *MITO*. NASA E", "UNIVERSIDADE DE CAMBRIDGE EXPLICAM.", ('F1', 'F2')),
        (16.0, 21.6, "SOLTAMOS UMA FILEIRA DE AR NA", "FRENTE DA ASA. OLHE A CORRIDA.", ()),
        (21.8, 27.6, "O AR DE CIMA CHEGA *MUITO ANTES*.", "NINGUÉM ESPERA NINGUÉM.", ('F1',)),
        (27.8, 35.6, "E UMA ASA *SIMÉTRICA*, INCLINADA,", "TAMBÉM GERA SUSTENTAÇÃO.", ('F2',)),
    ],
    'asa': [
        (0.4, 5.4, "ENTÃO COMO É DE VERDADE? OLHE", "O AR PASSANDO PELA ASA.", ()),
        (5.6, 10.6, "A ASA É CURVA E UM POUCO", "INCLINADA. O AR SEGUE A CURVA...", ('F1',)),
        (10.8, 15.8, "...E SAI DA ASA *DESVIADO*", "*PARA BAIXO*.", ('F3',)),
        (16.0, 21.4, "A ASA EMPURRA O AR PARA BAIXO.", "O AR EMPURRA A ASA *PARA CIMA*.", ('F3',)),
        (21.6, 26.8, "E A PRESSÃO MUDA: EM CIMA", "DA ASA ELA FICA *MENOR*...", ('F1',)),
        (27.0, 32.0, "...E EMBAIXO FICA *MAIOR*", "QUE A DO AR EM VOLTA.", ('F1',)),
        (32.2, 37.6, "O AR DE CIMA ANDA *MAIS RÁPIDO*.", "MAIS VELOCIDADE, *MENOS PRESSÃO*.", ('F2',)),
        (37.8, 42.8, "A DIFERENÇA DE PRESSÃO EMPURRA", "A ASA PARA CIMA: *SUSTENTAÇÃO*.", ('F2',)),
        (43.0, 47.8, "DESVIAR O AR E MUDAR A PRESSÃO", "SÃO DOIS LADOS DA *MESMA COISA*.", ('F2', 'F3')),
    ],
    'velocidade': [
        (0.4, 5.4, "QUANTO MAIS RÁPIDO O AR PASSA,", "MAIS SUSTENTAÇÃO.", ('F8',)),
        (5.6, 11.0, "E CRESCE COM O *QUADRADO*: VENTO 2X", "MAIS RÁPIDO, SUSTENTAÇÃO *4X*.", ('F18',)),
        (11.2, 16.8, "VENTO 3 VEZES MAIS RÁPIDO:", "*9 VEZES* MAIS SUSTENTAÇÃO.", ('F18',)),
        (17.0, 22.6, "ELA CRESCE TAMBÉM COM O TAMANHO", "DA ASA E COM A *DENSIDADE DO AR*.", ('F8',)),
        (22.8, 29.6, "POR ISSO O AVIÃO PRECISA CORRER", "NA PISTA ANTES DE SUBIR.", ()),
    ],
    'decolagem': [
        (0.4, 5.4, "NA PISTA, ELE ABRE OS *SLATS*", "(NA FRENTE) E OS *FLAPS* (ATRÁS).", ('F6',)),
        (5.6, 11.0, "ELES DEIXAM A ASA *MAIS CURVA*:", "MAIS SUSTENTAÇÃO, MESMO MAIS DEVAGAR.", ('F10', 'F11')),
        (11.2, 16.4, "OS MOTORES VÃO PARA A FORÇA", "DE DECOLAGEM. A VELOCIDADE SOBE.", ()),
        (16.6, 22.0, "JATOS COMERCIAIS COSTUMAM", "DECOLAR ENTRE *240 E 285 KM/H*.", ('F6',)),
        (22.2, 27.6, "NA HORA CERTA, O PILOTO", "*LEVANTA O NARIZ*: DE 5° A 15°.", ('F6',)),
        (27.8, 33.0, "A ASA INCLINADA DESVIA MAIS AR.", "AS RODAS SAEM DO CHÃO.", ('F3', 'F6')),
        (33.2, 38.4, "O *TREM DE POUSO* SOBE", "PARA DENTRO DO AVIÃO.", ()),
        (38.6, 45.2, "NA SUBIDA, FLAPS E SLATS SÃO", "*RECOLHIDOS*: ELES DÃO ARRASTO.", ('F6', 'F10')),
    ],
    'angulo': [
        (0.4, 5.6, "O *ÂNGULO DE ATAQUE* É O ÂNGULO", "ENTRE A ASA E O VENTO.", ('F9',)),
        (5.8, 11.0, "MAIS ÂNGULO: A ASA DESVIA", "MAIS AR PARA BAIXO...", ('F3',)),
        (11.2, 16.4, "...E GERA *MAIS SUSTENTAÇÃO*,", "NA MESMA VELOCIDADE.", ('F8',)),
        (16.6, 22.0, "QUANTO MAIS DEVAGAR, MAIS ÂNGULO", "É PRECISO PARA SEGURAR O PESO.", ('F9',)),
        (22.2, 32.6, "MAS ESSE TRUQUE TEM UM *LIMITE*.", "", ()),
    ],
    'estol': [
        (0.4, 5.6, "PASSOU DE UNS *15 GRAUS*, O AR NÃO", "CONSEGUE MAIS SEGUIR A CURVA.", ('F9',)),
        (5.8, 11.0, "ELE SE *DESGRUDA* DA ASA", "E VIRA REDEMOINHO.", ('F9',)),
        (11.2, 16.4, "A SUSTENTAÇÃO *DESPENCA*.", "ISSO É O *ESTOL*.", ('F9',)),
        (16.6, 22.0, "PODE ACONTECER EM *QUALQUER*", "*VELOCIDADE*: QUEM MANDA É O ÂNGULO.", ('F9',)),
        (22.2, 27.6, "AVIÕES DE LINHA TÊM UM AVISO QUE", "*FAZ O MANCHE TREMER* ANTES.", ('F9',)),
        (27.8, 33.0, "PARA SAIR DO ESTOL:", "*ABAIXAR O NARIZ*, REDUZINDO O ÂNGULO.", ('F9',)),
        (33.2, 38.6, "O AR VOLTA A GRUDAR NA ASA", "E A SUSTENTAÇÃO VOLTA.", ('F9',)),
    ],
    'motores': [
        (0.4, 5.4, "E QUEM EMPURRA PARA A FRENTE?", "OS MOTORES: *TURBOFANS*.", ('F12',)),
        (5.6, 10.8, "UM *VENTILADOR* GIGANTE NA FRENTE", "PUXA O AR PARA DENTRO.", ('F12',)),
        (11.0, 16.2, "PARTE DO AR VAI AO *NÚCLEO*: É", "COMPRIMIDA E QUEIMA COM COMBUSTÍVEL.", ('F12',)),
        (16.4, 21.6, "O GÁS QUENTE GIRA AS *TURBINAS*.", "UM EIXO LIGA UMA DELAS AO VENTILADOR.", ('F12',)),
        (21.8, 27.0, "O RESTO DO AR *CONTORNA* O NÚCLEO.", "OS DOIS JATOS EMPURRAM O AVIÃO.", ('F12',)),
        (27.2, 31.4, "OS 4 MOTORES JUNTOS EMPURRAM COM", "*MENOS DE 1/3* DO PESO DO AVIÃO.", ('F5', 'F16')),
        (31.6, 35.8, "O MOTOR EMPURRA. QUEM SEGURA", "O PESO É A *ASA*.", ('F16',)),
    ],
    'altitude': [
        (0.4, 5.4, "DEPOIS DA DECOLAGEM, O AVIÃO", "*CONTINUA SUBINDO*.", ()),
        (5.6, 10.8, "JATOS COMERCIAIS COSTUMAM VOAR", "ENTRE *9.400 E 11.600 METROS*.", ('F13',)),
        (11.0, 16.2, "A 11.000 M O AR É *RALO*: MENOS", "DE 1/3 DA DENSIDADE LÁ DE BAIXO.", ('F14', 'F17')),
        (16.4, 21.6, "E LÁ FORA FAZ", "*-56,5 °C*.", ('F14',)),
        (21.8, 27.0, "NA MESMA VELOCIDADE, AR RALO", "DÁ *MENOS ARRASTO*.", ('F15',)),
        (27.2, 32.4, "MAS AR RALO TAMBÉM DÁ", "MENOS SUSTENTAÇÃO...", ('F8',)),
        (32.6, 37.8, "...ENTÃO ELE VOA *BEM MAIS RÁPIDO*", "COM O MESMO ARRASTO.", ('F8', 'F13')),
        (38.0, 43.2, "NO ALTO OS MOTORES PERDEM FORÇA.", "A ALTITUDE É UM *MEIO-TERMO*.", ('F13',)),
        (43.4, 47.8, "ACIMA DAS NUVENS, O AVIÃO", "*NIVELA*: É O CRUZEIRO.", ()),
    ],
    'cruzeiro': [
        (0.4, 5.6, "EM CRUZEIRO, UM JATO GRANDE ANDA", "A UNS *900 KM/H* (MACH 0,85).", ('F13',)),
        (5.8, 11.0, "SUSTENTAÇÃO IGUAL AO PESO.", "TRAÇÃO IGUAL AO ARRASTO.", ('F4',)),
        (11.2, 16.4, "TUDO EM *EQUILÍBRIO*: VELOCIDADE", "E ALTURA CONSTANTES.", ('F4',)),
        (16.6, 22.0, "O PESO INCLUI O COMBUSTÍVEL, QUE", "*DIMINUI* À MEDIDA QUE QUEIMA.", ('F4',)),
        (22.2, 32.6, "E A ASA SEGUE FAZENDO A MESMA", "COISA: *DESVIANDO AR PARA BAIXO*.", ('F3',)),
    ],
    'pouso': [
        (0.4, 5.6, "PARA POUSAR, O CAMINHO É O INVERSO:", "MENOS TRAÇÃO, E O AVIÃO DESCE.", ()),
        (5.8, 11.0, "OS FLAPS VÃO AO *MÁXIMO*: A ASA", "SEGURA O AVIÃO MAIS DEVAGAR.", ('F10',)),
        (11.2, 16.4, "ELE CHEGA MAIS LENTO E PARA", "EM *MENOS PISTA*.", ('F10',)),
        (16.6, 22.0, "O TREM DE POUSO DESCE.", "O NARIZ FICA UM POUCO PARA CIMA.", ()),
        (22.2, 32.6, "RODAS NO CHÃO.", "*POUSO COMPLETO*.", ()),
    ],
    'resumo': [
        (0.4, 6.4, "1. A ASA *DESVIA O AR PARA BAIXO*", "E A PRESSÃO EM CIMA FICA MENOR.", ('F2', 'F3')),
        (6.6, 13.0, "2. MAIS VELOCIDADE OU MAIS ÂNGULO:", "*MAIS SUSTENTAÇÃO*.", ('F8',)),
        (13.2, 19.6, "3. ÂNGULO DEMAIS: O AR SE SOLTA", "DA ASA. É O *ESTOL*.", ('F9',)),
        (19.8, 26.6, "4. OS MOTORES SÓ EMPURRAM.", "QUEM SEGURA AS 400 T É A *ASA*.", ('F16',)),
    ],
}

FONTES = {
    'F1': ('Universidade de Cambridge, "How wings really work" (H. Babinsky)',
           'https://www.cam.ac.uk/research/news/how-wings-really-work'),
    'F2': ('NASA Glenn Research Center, "Equal Transit Theory"',
           'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/foilw1'),
    'F3': ('NASA Glenn Research Center, "Newton\'s Third Law"',
           'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/newtons-third-law-action-reaction/'),
    'F4': ('NASA Glenn Research Center, "Four Forces on an Airplane"',
           'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/four-forces-on-an-airplane/'),
    'F5': ('Wikipedia, "Boeing 747-400" (especificações)', 'https://en.wikipedia.org/wiki/Boeing_747-400'),
    'F6': ('Wikipedia, "Takeoff"', 'https://en.wikipedia.org/wiki/Takeoff'),
    'F7': ('Aerospaceweb, "Airliner Takeoff Speeds"', 'https://aerospaceweb.org/question/performance/q0088.shtml'),
    'F8': ('NASA Glenn Research Center, "The Lift Equation"',
           'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-equation'),
    'F9': ('Wikipedia, "Stall (fluid dynamics)"', 'https://en.wikipedia.org/wiki/Stall_(fluid_dynamics)'),
    'F10': ('Wikipedia, "Flap (aeronautics)"', 'https://en.wikipedia.org/wiki/Flap_(aeronautics)'),
    'F11': ('Wikipedia, "Leading-edge slat"', 'https://en.wikipedia.org/wiki/Leading-edge_slat'),
    'F12': ('NASA Glenn Research Center, "Turbofan Engine"',
            'https://www.grc.nasa.gov/WWW/K-12/VirtualAero/BottleRocket/airplane/aturbf.html'),
    'F13': ('Wikipedia, "Cruise (aeronautics)"', 'https://en.wikipedia.org/wiki/Cruise_(aeronautics)'),
    'F14': ('Wikipedia, "International Standard Atmosphere"',
            'https://en.wikipedia.org/wiki/International_Standard_Atmosphere'),
    'F15': ('NASA Glenn Research Center, "The Drag Equation"',
            'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-equation'),
    'F16': ('Conta a partir de F5: 4 x 282 kN = 1.128 kN contra 396.893 kg x 9,81 = 3.894 kN (29%)', None),
    'F17': ('Conta a partir de F14: 0,3639 / 1,225 = 30%', None),
    'F18': ('Conta a partir de F8: a sustentação cresce com o quadrado da velocidade', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'forcas': 'As 4 forças do voo', 'mito': 'O mito do "caminho maior"',
                'asa': 'O que a asa faz com o ar', 'velocidade': 'Velocidade ao quadrado',
                'decolagem': 'Flaps, slats e decolagem', 'angulo': 'Ângulo de ataque', 'estol': 'O que é o estol',
                'motores': 'Os motores só empurram', 'altitude': 'Por que voar tão alto',
                'cruzeiro': 'Cruzeiro: tudo em equilíbrio', 'pouso': 'O pouso', 'resumo': 'Resumo'}

DESCRICAO = """Como um jato que pode decolar com quase 400 toneladas sai do chão? A gente coloca uma asa num túnel de vento em pixel art e mostra o ar de verdade passando por ela: o ar sai desviado para baixo, a pressão fica menor em cima e maior embaixo, e a diferença segura o avião. Depois acompanha o voo da pista ao cruzeiro: flaps e slats, ângulo de ataque, o estol, os motores e por que os aviões voam tão alto.

Spoiler: a explicação do "caminho maior em cima" que muita gente aprendeu na escola é um mito, e o vídeo mostra por quê.

Cada quadro é pixel art desenhada por código, e a música é original. O ar do túnel é calculado (escoamento potencial em volta de um perfil de Joukowski), não desenhado à mão.

Capítulos
{capitulos}

Simplificado de propósito
- O ar do túnel é um cálculo de escoamento ideal (sem viscosidade) em volta de uma asa de Joukowski, um perfil de livro-texto parecido com uma asa real. O redemoinho do estol é ilustrativo: esse cálculo não consegue prever a separação.
- O avião é genérico, inspirado num jato de 4 motores; os números de peso, motor e velocidade de decolagem são do Boeing 747-400 (e de jatos comerciais em geral, quando dito).
- Na cena da velocidade, a asa fica parada e o vento muda; na cena do ângulo, o vento fica igual e a asa gira. No ar é o mesmo efeito.
- O ângulo crítico do estol varia de asa para asa (8° a 20°); usamos o valor típico de cerca de 15°.
- Escalas de tempo, distância e altitude estão comprimidas para caber na tela.

Fontes
{fontes}

#aviao #comofunciona #pixelart #aviacao #ciencia #fisica #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. A asa do túnel
# ocupa x ~55..235; o avião de lado fica centrado em x ~150.
PREFIXO = 'ep02-aviao'
CORTES = [
    dict(id='c1', de=('mito', 0.0), ate=('mito', 27.6), x=58, gancho=['O MITO', 'DA ASA'],
         titulo='O que te ensinaram sobre a asa do avião está errado ✈️',
         descricao='O ar de cima NÃO precisa chegar junto com o de baixo. Num túnel de vento, o ar de cima chega muito antes. Fontes: NASA e Universidade de Cambridge.'),
    dict(id='c2', de=('asa', 5.6), ate=('asa', 32.0), x=58, gancho=['COMO A ASA', 'SEGURA?'],
         titulo='Como a asa segura um avião de 400 toneladas',
         descricao='A asa desvia o ar para baixo e o ar empurra a asa para cima. Ao mesmo tempo, a pressão fica menor em cima e maior embaixo.'),
    dict(id='c3', de=('estol', 0.0), ate=('estol', 33.0), x=58, gancho=['O QUE É', 'ESTOL?'],
         titulo='O que é o estol de um avião? 😱',
         descricao='Passou de uns 15 graus de ângulo, o ar se solta da asa e a sustentação despenca. Para sair: abaixar o nariz.'),
    dict(id='c4', de=('decolagem', 16.6), ate=('decolagem', 38.4), x=66, gancho=['A HORA DA', 'DECOLAGEM'],
         titulo='O momento exato em que o avião decola 🛫',
         descricao='Jatos comerciais decolam entre 240 e 285 km/h. O piloto levanta o nariz de 5 a 15 graus e as rodas saem do chão.'),
    dict(id='c5', de=('motores', 0.0), ate=('motores', 35.8), x=40, gancho=['POR DENTRO', 'DO MOTOR'],
         titulo='Por dentro do motor de um avião (turbofan)',
         descricao='Um ventilador gigante puxa o ar. Parte queima no núcleo, o resto contorna. E os 4 motores juntos empurram com menos de 1/3 do peso do avião.'),
    dict(id='c6', de=('altitude', 5.6), ate=('altitude', 37.8), x=66, gancho=['POR QUE TÃO', 'ALTO?'],
         titulo='Por que os aviões voam a 11 km de altura?',
         descricao='Lá em cima o ar tem menos de 1/3 da densidade do nível do mar: o avião voa bem mais rápido com o mesmo arrasto. E faz -56,5 °C lá fora.'),
]
