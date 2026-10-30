#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep05 (série POR DENTRO): Como a geladeira faz frio.

A ideia: a geladeira não fabrica frio, ela tira calor de dentro e joga fora,
atrás dela. Protagonista: uma porção de fluido refrigerante dando a volta no
circuito (compressor -> condensador -> tubo capilar -> evaporador), com a cor
mudando com a temperatura e um painel com pressão, temperatura, estado e
"etapa 2 de 4". O desenho mora em `ep05_motor.py` e `ep05_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 29/10/2026)
  F1  Geladeira a 4 °C ou menos; congelador a -18 °C ou menos. FoodSafety.gov (EUA).
  F2  A geladeira tem uma bomba de calor que leva o calor de dentro para fora; o ar
      de dentro é mais quente que o fluido do evaporador; faixa ótima 3 a 5 °C; R-600a
      (isobutano) é o principal refrigerante na Europa; ao abrir a porta, alguns
      modelos param o ventilador para limitar o gelo no evaporador. Wikipedia, "Refrigerator".
  F3  Compressor = coração; gás sai dele quente e com pressão alta; condensador fica
      atrás e é quente ao toque; tubo capilar = cano fino que serve de dispositivo de
      expansão; evaporador fica dentro e evaporar o fluido esfria em volta; o sensor
      desliga o compressor quando está frio o bastante e liga de novo quando esquenta.
      Danfoss, "How a refrigerator works - basic training".
  F4  Os 4 componentes e os estados: vapor entra no compressor, sai superaquecido;
      no condensador vira líquido; a válvula/capilar faz a pressão cair de repente e
      parte do líquido evapora na hora, o que esfria a mistura; no evaporador ele
      ferve de novo. Wikipedia, "Vapor-compression refrigeration".
  F5  Isobutano ferve a -11,78 °C (à pressão do ar). Wikipedia, "Isobutane".
  F6  Pressão de saturação do isobutano: -25 °C -> 0,58 bar; 45 °C -> 6,04 bar.
      NIST Chemistry WebBook (tabela de saturação).
  F7  Compressor de geladeira a R-600a: evaporação de -35 a -10 °C; ensaios de
      condensação de 35 a 65 °C. Ficha técnica Embraco (fabricante).
  F8  "Tira a energia térmica do interior frio e empurra para a cozinha mais quente";
      as serpentinas ficam atrás ou embaixo; o compressor é a peça que mais gasta
      eletricidade; o capilar funciona como um bico. Penn State, EGEE 102.
  F9  Clausius: o calor não passa do frio para o quente sem que algo mais aconteça;
      na geladeira isso só acontece forçado por um agente externo. Wikipedia,
      "Second law of thermodynamics".
  F10 O suor que evapora esfria a pele. Wikipedia, "Perspiration".
  F11 Não abrir a porta toda hora; deixar a comida quente esfriar antes; deixar espaço
      atrás para o ar circular no condensador. EMSD, governo de Hong Kong.
  F12 A maior parte da energia vai para bombear o calor para fora; abrir a porta o
      menos possível e rápido; deixar alguns centímetros atrás. Departamento de
      Energia das Filipinas, "Fridge Facts".
  F13 Porta aberta: o ar frio escapa, mas a geladeira esquenta a cozinha mais do que
      esfria; abrir a porta esquenta o interior, o termostato liga e o motor roda,
      somando calor. University of Illinois, Physics Van.
  F14 6 / 0,6 = 10 vezes (conta a partir de F6).
  F15 Quanto mais a porta é aberta, mais tempo o compressor roda. Frigidaire, suporte.
"""

TITULO = "Como a geladeira faz frio | O ciclo de refrigeração em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='cozinha', gen='lofi', bars=10, papel='drop'),         # 30 s
    dict(id='calor', gen='lofi', bars=8, papel='drop'),            # 24 s
    dict(id='evaporar', gen='lofi', bars=8, papel='break'),        # 24 s
    dict(id='pecas', gen='synthwave', bars=25, papel='drop'),      # 60 s (5 peças x 12 s)
    dict(id='fluido', gen='lofi', bars=9, papel='break'),          # 27 s
    dict(id='etapa1', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='etapa2', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='etapa3', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='etapa4', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='ciclo', gen='synthwave', bars=12, papel='drop'),      # 28,8 s
    dict(id='termostato', gen='lofi', bars=12, papel='drop'),      # 36 s
    dict(id='porta', gen='lofi', bars=14, papel='drop'),           # 42 s
    dict(id='esfriar', gen='lofi', bars=10, papel='break'),        # 30 s
    dict(id='resumo', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 6.0, "A GELADEIRA NÃO *FABRICA FRIO*.", "", ()),
        (6.0, 11.6, "ELA *TIRA O CALOR* DE DENTRO", "E JOGA FORA, ATRÁS DELA.", ('F2', 'F3')),
    ],
    'cozinha': [
        (0.8, 7.6, "UMA GELADEIRA COMUM, NA COZINHA.", "O *CONGELADOR* FICA EM CIMA.", ()),
        (7.8, 14.6, "NA GELADEIRA: *4 °C OU MENOS*.", "NO CONGELADOR: *-18 °C OU MENOS*.", ('F1',)),
        (14.8, 21.8, "AGORA PONHA A MÃO ATRÁS DELA,", "NOS CANOS: *ESTÁ QUENTE*.", ('F3',)),
        (22.0, 29.6, "ESSE CALOR VEIO LÁ DE DENTRO:", "DA COMIDA, DO AR, DAS PAREDES.", ('F8',)),
    ],
    'calor': [
        (0.5, 7.6, "SOZINHO, O CALOR SÓ ANDA DO QUENTE", "PARA O FRIO. ELE VAI ENTRANDO.", ('F9',)),
        (7.8, 15.6, "PARA TIRAR O CALOR DE LÁ, É PRECISO", "*EMPURRAR*. E ISSO GASTA ENERGIA.", ('F9', 'F12')),
        (15.8, 23.6, "QUEM EMPURRA É O *COMPRESSOR*, A", "PEÇA QUE MAIS GASTA ELETRICIDADE.", ('F8',)),
    ],
    'evaporar': [
        (0.5, 7.6, "O TRUQUE TODO É UM SÓ:", "*EVAPORAR ROUBA CALOR*.", ('F3',)),
        (7.8, 15.6, "É POR ISSO QUE O SUOR REFRESCA:", "AO SECAR, ELE LEVA CALOR DA PELE.", ('F10',)),
        (15.8, 23.6, "A GELADEIRA FAZ ISSO LÁ DENTRO, COM", "UM LÍQUIDO QUE *FERVE NO FRIO*.", ('F3', 'F5')),
    ],
    'pecas': [
        (0.3, 11.6, "O *COMPRESSOR* FICA EMBAIXO, ATRÁS.", "É O CORAÇÃO DA GELADEIRA.", ('F3',)),
        (12.3, 23.6, "O *CONDENSADOR*: A GRADE DE CANOS", "NAS COSTAS. É ELE QUE ESQUENTA.", ('F3',)),
        (24.3, 35.6, "O *TUBO CAPILAR*: UM CANO FININHO", "QUE FUNCIONA COMO UM BICO.", ('F3', 'F8')),
        (36.3, 47.6, "O *EVAPORADOR*: CANOS LÁ DENTRO.", "É ELE QUE FICA GELADO.", ('F3',)),
        (48.3, 59.6, "E O *FLUIDO REFRIGERANTE*, QUE DÁ", "A VOLTA POR TUDO ISSO, SEM PARAR.", ('F4',)),
    ],
    'fluido': [
        (0.5, 8.6, "MUITAS GELADEIRAS USAM *ISOBUTANO*.", "À PRESSÃO DO AR, FERVE A -11,8 °C.", ('F2', 'F5')),
        (8.8, 17.6, "MAS O PONTO DE FERVURA MUDA", "COM A *PRESSÃO*.", ('F6',)),
        (17.8, 26.6, "POUCA PRESSÃO: FERVE A *-25 °C*.", "MUITA PRESSÃO: SÓ A *45 °C*.", ('F6', 'F7')),
    ],
    'etapa1': [
        (2.0, 9.6, "ETAPA 1: O GÁS VOLTA, JÁ MORNO,", "E CHEGA AO *COMPRESSOR*.", ('F4',)),
        (9.8, 18.6, "O PISTÃO ESPREME O GÁS: A PRESSÃO", "SOBE *10 VEZES*, DE 0,6 PARA 6 BAR.", ('F6', 'F14')),
        (18.8, 29.6, "GÁS ESPREMIDO ESQUENTA:", "SAI DALI *MAIS QUENTE QUE 45 °C*.", ('F3', 'F4')),
    ],
    'etapa2': [
        (2.0, 9.6, "ETAPA 2: O GÁS QUENTE PASSA PELA", "GRADE DAS COSTAS, O *CONDENSADOR*.", ('F3',)),
        (9.8, 18.6, "A COZINHA ESTÁ MAIS FRIA QUE ELE,", "ENTÃO O *CALOR SAI* PARA O AR.", ('F4', 'F9')),
        (18.8, 29.6, "PERDENDO CALOR, O GÁS *VIRA LÍQUIDO*,", "COMO O VAPOR NA TAMPA DA PANELA.", ('F4',)),
    ],
    'etapa3': [
        (2.0, 9.6, "ETAPA 3: O LÍQUIDO ENTRA NO", "*TUBO CAPILAR*, BEM FININHO.", ('F3',)),
        (9.8, 18.6, "DO OUTRO LADO A PRESSÃO É BAIXA.", "ELA CAI DE 6 PARA *0,6 BAR*.", ('F4', 'F6')),
        (18.8, 29.6, "UM POUCO DELE JÁ FERVE, E ISSO", "GELA O RESTO: CAI PARA *-25 °C*.", ('F4', 'F6')),
    ],
    'etapa4': [
        (2.0, 9.6, "ETAPA 4: O LÍQUIDO GELADO CORRE", "PELO *EVAPORADOR*, LÁ DENTRO.", ('F3',)),
        (9.8, 18.6, "ELE FERVE A -25 °C E PUXA O CALOR", "DO AR E DA COMIDA: *É O FRIO*.", ('F2', 'F3', 'F6')),
        (18.8, 29.6, "JÁ VIROU GÁS DE NOVO. ELE VOLTA", "AO COMPRESSOR E TUDO RECOMEÇA.", ('F4',)),
    ],
    'ciclo': [
        (0.5, 9.4, "4 ETAPAS: ESPREMER, ESFRIAR,", "SOLTAR A PRESSÃO E FERVER.", ('F4',)),
        (9.6, 19.0, "O CALOR ENTRA NO *EVAPORADOR*", "E SAI NO *CONDENSADOR*.", ('F3',)),
        (19.2, 28.4, "O FLUIDO NÃO SE GASTA: É SEMPRE", "O MESMO, DANDO VOLTAS.", ('F4',)),
    ],
    'termostato': [
        (0.5, 8.6, "MAS A GELADEIRA NÃO FICA", "LIGADA O TEMPO TODO.", ('F3',)),
        (8.8, 17.6, "O *TERMOSTATO* MEDE: GELOU O BASTANTE?", "ELE *DESLIGA* O COMPRESSOR.", ('F3',)),
        (17.8, 26.6, "A TEMPERATURA SOBE DEVAGAR.", "PASSOU DO PONTO? *LIGA DE NOVO*.", ('F3',)),
        (26.8, 35.6, "ASSIM ELA FICA ENTRE *3 E 5 °C*,", "A FAIXA BOA PARA A COMIDA.", ('F2',)),
    ],
    'porta': [
        (0.5, 8.6, "PORTA ABERTA: O AR FRIO ESCAPA", "E O DE DENTRO *ESQUENTA*.", ('F13',)),
        (8.8, 17.6, "O TERMOSTATO PERCEBE, E O", "COMPRESSOR *TRABALHA MAIS*.", ('F13', 'F15')),
        (17.8, 26.6, "E A UMIDADE DO AR VIRA *GELO*", "NOS CANOS DO EVAPORADOR.", ('F2',)),
        (26.8, 35.6, "ABRA A PORTA POUCO E FECHE LOGO.", "DEIXE A COMIDA QUENTE ESFRIAR ANTES.", ('F11', 'F12')),
        (35.8, 41.6, "E DEIXE ESPAÇO ATRÁS: O CALOR", "PRECISA DE AR PARA SAIR.", ('F11', 'F12')),
    ],
    'esfriar': [
        (0.5, 8.6, "DÁ PARA ESFRIAR A COZINHA", "DEIXANDO A GELADEIRA ABERTA?", ()),
        (8.8, 18.6, "NÃO. O CALOR QUE ELA TIRA DA FRENTE", "VOLTA PARA A COZINHA PELAS COSTAS.", ('F13',)),
        (18.8, 29.6, "E O MOTOR AINDA SOMA O CALOR DELE.", "A COZINHA *ESQUENTA*.", ('F13',)),
    ],
    'resumo': [
        (0.5, 8.6, "RESUMINDO: A GELADEIRA É UMA", "*BOMBA DE CALOR*.", ('F2',)),
        (8.8, 17.6, "1 COMPRIME, 2 SOLTA O CALOR,", "3 BAIXA A PRESSÃO, 4 FERVE.", ('F4',)),
        (17.8, 26.6, "O FRIO É O QUE SOBRA", "QUANDO O CALOR É LEVADO EMBORA.", ('F2', 'F8')),
        (26.8, 35.6, "E TUDO DEPENDE DE UM LÍQUIDO", "QUE *FERVE NO FRIO*.", ('F5', 'F6')),
    ],
}

FONTES = {
    'F1': ('FoodSafety.gov (governo dos EUA), "Cold Food Storage Chart"',
           'https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts'),
    'F2': ('Wikipedia, "Refrigerator"', 'https://en.wikipedia.org/wiki/Refrigerator'),
    'F3': ('Danfoss, "How a refrigerator works - basic training"',
           'https://www.danfoss.com/en/about-danfoss/our-businesses/cooling/the-fridge-how-it-works'),
    'F4': ('Wikipedia, "Vapor-compression refrigeration"', 'https://en.wikipedia.org/wiki/Vapor-compression_refrigeration'),
    'F5': ('Wikipedia, "Isobutane"', 'https://en.wikipedia.org/wiki/Isobutane'),
    'F6': ('NIST Chemistry WebBook, isobutano: propriedades de saturação',
           'https://webbook.nist.gov/cgi/fluid.cgi?Action=Load&ID=C75285&Type=SatP&Digits=4&THigh=60&TLow=-30&TInc=5&RefState=DEF&TUnit=C&PUnit=bar&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=uPa*s&STUnit=N%2Fm'),
    'F7': ('Embraco, ficha técnica de compressor R-600a (faixa de evaporação e condensação)',
           'https://embraco.com/productselector/pdfs/FT024785_4.pdf'),
    'F8': ('Penn State, EGEE 102, "6.4 Refrigerators"', 'https://courses.ems.psu.edu/egee102/node/2402'),
    'F9': ('Wikipedia, "Second law of thermodynamics"', 'https://en.wikipedia.org/wiki/Second_law_of_thermodynamics'),
    'F10': ('Wikipedia, "Perspiration"', 'https://en.wikipedia.org/wiki/Perspiration'),
    'F11': ('EMSD (governo de Hong Kong), "Energy Saving Tips: Refrigerator"',
            'https://www.emsd.gov.hk/energyland/en/tips/home/refrigerator.html'),
    'F12': ('Departamento de Energia das Filipinas, "Fridge Facts"',
            'https://legacy.doe.gov.ph/sites/default/files/pdf/consumer_connect/fridge_facts.pdf'),
    'F13': ('University of Illinois, Physics Van, "Open Refrigerator"',
            'https://van.physics.illinois.edu/qa/listing.php?id=1790'),
    'F14': ('Conta a partir de F6 (6 bar / 0,6 bar = 10)', None),
    'F15': ('Frigidaire, "Why does my refrigerator run most of the time?"',
            'https://owner.frigidaire.com/support-articles/article/1847710-refrigerators-why-does-my-refrigerator-run-most-of-the-time-is-this-normal-'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'cozinha': 'Frio dentro, quente atrás', 'calor': 'O calor só desce a ladeira',
                'evaporar': 'O truque: evaporar rouba calor', 'pecas': 'As 4 peças do circuito',
                'fluido': 'Um líquido que ferve no frio', 'etapa1': 'Etapa 1: compressor',
                'etapa2': 'Etapa 2: condensador', 'etapa3': 'Etapa 3: tubo capilar', 'etapa4': 'Etapa 4: evaporador',
                'ciclo': 'O ciclo completo', 'termostato': 'O termostato liga e desliga',
                'porta': 'Por que não deixar a porta aberta', 'esfriar': 'Dá para esfriar a cozinha?',
                'resumo': 'Resumo'}

DESCRICAO = """Geladeira não fabrica frio: ela tira o calor de dentro e joga fora, pelas costas. Neste vídeo a gente acompanha uma porção de fluido refrigerante dando a volta no circuito, etapa por etapa: compressor, condensador, tubo capilar e evaporador. Um painel mostra a pressão, a temperatura e se o fluido está como gás ou líquido.

Também: por que a parte de trás da geladeira é quente, como o termostato liga e desliga o compressor, por que não deixar a porta aberta e se dá para esfriar a cozinha com a geladeira aberta.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- As pressões são absolutas e as temperaturas do fluido (-25 °C no evaporador, 45 °C no condensador) são um exemplo dentro da faixa de trabalho de um compressor de geladeira a R-600a; cada geladeira trabalha um pouco diferente.
- O gás volta ao compressor já morno, aquecido pelo cano de volta; o painel mostra -25 °C na entrada para simplificar.
- Na saída do compressor o gás passa de 45 °C; não damos um número exato porque ele varia com o aparelho.
- Desenhamos um compressor de pistão e um condensador de grade nas costas; existem outros tipos (compressor rotativo, condensador embaixo ou embutido na lateral).
- Nas geladeiras de verdade o tubo capilar costuma correr encostado no cano de volta ao compressor; aqui eles ficam separados para dar para ver.
- Os 25 °C da cozinha são um exemplo. No capítulo do termostato o tempo está acelerado: na geladeira de verdade um ciclo liga-desliga demora bem mais.
- Muitas geladeiras usam isobutano (R-600a); outras usam outros fluidos, mas o ciclo é o mesmo.

Fontes
{fontes}

#geladeira #comofunciona #pixelart #ciencia #fisica #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. A geladeira em corte
# ocupa x 54..238; os closes, x 8..292 (o miolo cabe em 60..240).
PREFIXO = 'ep05-geladeira'
CORTES = [
    dict(id='c1', de=('etapa1', 0.0), ate=('etapa1', 30.0), x=96, gancho=['APERTOU,', 'ESQUENTOU'],
         titulo='Por que o compressor da geladeira esquenta o gás? 🔥',
         descricao='O pistão espreme o gás refrigerante: a pressão sobe 10 vezes, de 0,6 para 6 bar, e o gás sai mais quente que 45 °C. É a etapa 1 do ciclo da geladeira.'),
    dict(id='c2', de=('etapa3', 0.0), ate=('etapa3', 30.0), x=60, gancho=['UM CANO', 'QUE GELA'],
         titulo='O cano fininho que faz a geladeira gelar ❄️',
         descricao='No tubo capilar a pressão do fluido cai de 6 para 0,6 bar. Um pouco dele ferve na hora, e isso gela o resto até -25 °C.'),
    dict(id='c3', de=('etapa4', 0.0), ate=('etapa4', 30.0), x=110, gancho=['FERVE A', '-25 °C'],
         titulo='Dentro da geladeira, um líquido fervendo a -25 °C',
         descricao='No evaporador o fluido ferve a -25 °C e puxa o calor do ar e da comida. É isso que a gente chama de frio.'),
    dict(id='c4', de=('cozinha', 7.8), ate=('cozinha', 30.0), x=68, gancho=['POR QUE', 'É QUENTE?'],
         titulo='Por que a parte de trás da geladeira é quente?',
         descricao='Dentro, 4 °C ou menos; no congelador, -18 °C ou menos. E atrás, os canos são quentes: é o calor que saiu lá de dentro (da comida, do ar e das paredes).'),
    dict(id='c5', de=('porta', 0.0), ate=('porta', 36.0), x=44, gancho=['PORTA', 'ABERTA?'],
         titulo='O que acontece quando a porta da geladeira fica aberta?',
         descricao='O ar frio escapa, o termostato percebe e o compressor trabalha mais. E a umidade do ar vira gelo no evaporador.'),
    dict(id='c6', de=('esfriar', 0.0), ate=('esfriar', 30.0), x=44, gancho=['ESFRIA A', 'COZINHA?'],
         titulo='Dá para esfriar a cozinha com a geladeira aberta? 🤔',
         descricao='Não: o calor que ela tira pela frente volta pelas costas, e o motor ainda soma o calor dele. A cozinha esquenta.'),
]
