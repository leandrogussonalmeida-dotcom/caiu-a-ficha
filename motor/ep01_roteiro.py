#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep01: Como funciona o motor do carro (o ciclo de 4 tempos).

Versão PT-BR (29/10/2026). A versão em inglês do piloto está guardada em
`_en/ep01_roteiro_en.py` para quando o canal ganhar a versão global.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep01_motor.py`; `longo_verificar.py --roteiro ep01_roteiro` reprova legenda
que não cabe, caractere sem glifo, legenda curta demais e fato sem fonte.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES
  F1  4 tempos: admissão (válvula de admissão aberta, pistão desce),
      compressão (as duas fechadas, sobe), combustão/potência (fechadas,
      desce), escape (escape aberta, sobe). 1 ciclo = 2 voltas do virabrequim.
      Britannica, "four-stroke cycle"; Wikipedia, "Four-stroke engine".
  F2  O comando gira à metade da velocidade do virabrequim. Wikipedia, "Camshaft".
  F3  Taxa de compressão de motor a gasolina de carro: 8:1 a 12:1. Wikipedia, "Compression ratio".
  F4  A faísca vem antes do ponto morto superior (~20°). Univ. of Windsor, manual.
  F5  Marcha lenta típica: 600 a 1.000 RPM. MechanicBase.
  F6  3.000 RPM = 50 voltas/s; 1 queima a cada 2 voltas = 25/s por cilindro; 6.000 = 50/s. (conta)
  F7  Volante: mantém o giro entre os impulsos. Univ. of Windsor, manual.
  F8  Ordem de queima mais comum do 4 em linha: 1-3-4-2. Rick's Free Auto Repair Advice.
      Num 4 cilindros, um impulso começa a cada 180° (meia volta). (conta, checagem de 29/10)
  F9  16-25% da energia move o carro no uso combinado; perdas no motor 68-72%,
      principalmente calor. fueleconomy.gov (Departamento de Energia dos EUA).
  F10 Otto construiu um motor de 4 tempos em 1876. Britannica, "Nikolaus Otto".
  F11 Injeção direta; e comprimir antes de queimar tornou o motor de Otto muito
      mais eficiente. Wikipedia, "Four-stroke engine".
  F12 No Brasil os 4 tempos aparecem como admissão, compressão, explosão e
      escape (Prepara Enem) ou com "combustão" no 3º (InfoEscola). Lidos em 29/10.

  Capítulos extras (30/10/2026, para passar de 8 min):
  F13 A vela precisa de 12.000 a 25.000 volts ou mais; folga de 0,6 a 1,8 mm
      nos carros; isolador de cerâmica. Wikipedia, "Spark plug".
  F14 Bobina: primário de poucas voltas de fio grosso, secundário de milhares
      de voltas; o circuito abre e o secundário dá a alta tensão (15 a 40 kV).
      Wikipedia, "Ignition coil".
  F15 Injetor: atomiza o combustível por um bico pequeno sob pressão, abre e
      fecha por sinal elétrico; na injeção multiponto é intermitente e no
      ritmo da ordem de queima. Wikipedia, "Fuel injection" e "Manifold injection".
  F16 Mistura estequiométrica em massa: gasolina 14,7:1, etanol 9:1.
      Wikipedia, "Stoichiometry" (tabela); "Air–fuel ratio" (sonda lambda).
  F17 O motor queima combustível mais quente que o ponto de fusão dos seus
      materiais; bomba circula o líquido pelo motor e radiador; as peças
      que se mexem dependem do óleo para esfriar; alguns motores espirram
      óleo embaixo do pistão. Wikipedia, "Internal combustion engine cooling".
  F18 Gol 1.6 Total Flex, março de 2003, o primeiro flex comercial do Brasil
      (a marca não aparece no vídeo); a sonda lambda diz à central qual
      mistura está queimando. Wikipedia, "Flexible-fuel vehicles in Brazil".
  F19 Flex funciona com qualquer proporção de gasolina com etanol e etanol
      puro; a gasolina do posto tem 30% de etanol anidro desde agosto de 2025.
      Jornal da USP.
  F20 Bateria de carro: 6 células em série, sistema nominal de 12 V
      (partida, luz e ignição). Wikipedia, "Automotive battery".
"""

TITULO = "Como funciona o motor do carro | O ciclo de 4 tempos em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='carro', gen='lofi', bars=8, papel='drop'),            # 24 s
    dict(id='pecas', gen='synthwave', bars=21, papel='drop'),      # 50,4 s (7 peças x 3 compassos)
    dict(id='injetor', gen='lofi', bars=10, papel='drop'),         # 30 s (extra)
    dict(id='admissao', gen='lofi', bars=8, papel='drop'),         # 24 s
    dict(id='compressao', gen='lofi', bars=8, papel='drop'),       # 24 s
    dict(id='faisca', gen='synthwave', bars=13, papel='drop'),     # 31,2 s (extra: faísca a cada 2 batidas)
    dict(id='potencia', gen='lofi', bars=8, papel='drop'),         # 24 s
    dict(id='escape', gen='lofi', bars=8, papel='drop'),           # 24 s
    dict(id='ciclo', gen='lofi', bars=4, papel='break'),           # 12 s
    dict(id='batidas', gen='house', bars=12, papel='drop', bpm=120),   # 24 s
    dict(id='rpm', gen='synthwave', bars=14, papel='break'),       # 33,6 s
    dict(id='cilindros', gen='lofi', bars=14, papel='drop'),       # 42 s
    dict(id='energia', gen='lofi', bars=8, papel='break'),         # 24 s
    dict(id='calor', gen='lofi', bars=11, papel='drop'),           # 33 s (extra)
    dict(id='flex', gen='lofi', bars=10, papel='drop'),            # 30 s (extra)
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),           # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "DENTRO DO MOTOR DE UM CARRO, O", "COMBUSTÍVEL QUEIMA SEM PARAR.", ()),
        (6.0, 11.6, "A 3.000 RPM: *25 VEZES POR SEGUNDO*", "EM CADA CILINDRO.", ('F6',)),
    ],
    'carro': [
        (0.8, 7.8, "ESTE É UM CARRO A GASOLINA.", "O QUE FAZ ELE ANDAR?", ()),
        (8.0, 13.8, "SOB O CAPÔ: O *MOTOR*. MUITOS CARROS", "TÊM 4 CILINDROS EM LINHA.", ()),
        (14.0, 18.8, "CADA CILINDRO FAZ O MESMO TRABALHO,", "SÓ QUE EM MOMENTOS DIFERENTES.", ('F8',)),
        (19.0, 23.6, "VAMOS ABRIR *UM CILINDRO*.", "", ()),
    ],
    'pecas': [
        (0.3, 7.0, "O *CILINDRO*: UM TUBO DE METAL FORTE.", "É AQUI QUE TUDO ACONTECE.", ()),
        (7.5, 14.2, "O *PISTÃO* SOBE E DESCE.", "ANÉIS EM VOLTA DELE VEDAM A FOLGA.", ()),
        (14.7, 21.4, "A *BIELA* LIGA O PISTÃO", "AO VIRABREQUIM.", ()),
        (21.9, 28.6, "O *VIRABREQUIM* TRANSFORMA O SOBE E", "DESCE EM GIRO.", ()),
        (29.1, 35.8, "*VÁLVULAS*: UMA DEIXA ENTRAR AR E", "COMBUSTÍVEL; A OUTRA SOLTA O GÁS.", ('F1',)),
        (36.3, 43.0, "O *COMANDO* ABRE AS VÁLVULAS E", "DÁ 1 VOLTA A CADA 2 DO VIRABREQUIM.", ('F2',)),
        (43.5, 50.2, "A *VELA DE IGNIÇÃO* SOLTA UMA FAÍSCA", "QUE ACENDE A MISTURA.", ()),
    ],
    'injetor': [
        (0.5, 7.4, "FALTOU UMA PEÇA: O *INJETOR*. É ELE", "QUE PÕE O COMBUSTÍVEL NO MOTOR.", ('F15',)),
        (7.6, 14.8, "UM SINAL ELÉTRICO PUXA A AGULHA E O", "COMBUSTÍVEL SAI EM *SPRAY FINO*.", ('F15',)),
        (15.0, 22.0, "ELE ABRE EM *PULSOS*, NO RITMO", "DE CADA CILINDRO.", ('F15',)),
        (22.2, 29.6, "NA GASOLINA PURA: *14,7 G DE AR*", "PARA CADA 1 G DE COMBUSTÍVEL.", ('F16',)),
    ],
    'admissao': [
        (2.0, 8.8, "O PISTÃO DESCE E A *VÁLVULA DE*", "*ADMISSÃO* ABRE.", ('F1',)),
        (9.0, 15.8, "AR E COMBUSTÍVEL SÃO PUXADOS PARA", "DENTRO DO CILINDRO.", ('F1',)),
        (16.0, 23.6, "(ALGUNS MOTORES INJETAM O COMBUSTÍVEL", "DIRETO NO CILINDRO.)", ('F11',)),
    ],
    'compressao': [
        (2.0, 8.8, "*AS DUAS VÁLVULAS FECHAM.*", "O PISTÃO SOBE.", ('F1',)),
        (9.0, 15.8, "A MISTURA É ESPREMIDA NUM ESPAÇO", "*8 A 12 VEZES* MENOR.", ('F3',)),
        (16.0, 23.6, "COMPRIMIR ANTES DE QUEIMAR DEIXA", "O MOTOR MUITO MAIS EFICIENTE.", ('F11',)),
    ],
    'faisca': [
        (0.5, 7.4, "AGORA FALTA A FAÍSCA. A BATERIA", "DO CARRO TEM SÓ *12 VOLTS*.", ('F20',)),
        (7.6, 14.4, "A VELA PRECISA DE *12.000 A 25.000*", "VOLTS OU MAIS PARA FAISCAR.", ('F13',)),
        (14.6, 22.0, "A *BOBINA* SOBE A TENSÃO: POUCAS", "VOLTAS DE UM LADO, MILHARES DO OUTRO.", ('F14',)),
        (22.2, 30.8, "A CORRENTE É CORTADA E O CHOQUE PULA", "A FOLGA DA VELA: *0,6 A 1,8 MM*.", ('F14', 'F13')),
    ],
    'potencia': [
        (2.0, 8.8, "LOGO ANTES DO PISTÃO CHEGAR AO TOPO,", "A *VELA* SOLTA A FAÍSCA.", ('F4',)),
        (9.0, 15.8, "A MISTURA QUEIMA RÁPIDO. O GÁS QUENTE", "SE EXPANDE E EMPURRA O PISTÃO.", ('F1',)),
        (16.0, 23.6, "ESTE É O *ÚNICO TEMPO*", "QUE GERA FORÇA.", ('F1',)),
    ],
    'escape': [
        (2.0, 8.8, "A *VÁLVULA DE ESCAPE* ABRE.", "O PISTÃO SOBE DE NOVO.", ('F1',)),
        (9.0, 15.8, "ELE EMPURRA O GÁS QUEIMADO PARA", "O CANO DE ESCAPAMENTO.", ('F1',)),
        (16.0, 23.6, "E O CICLO INTEIRO", "COMEÇA DE NOVO.", ()),
    ],
    'ciclo': [
        (0.5, 11.6, "4 TEMPOS = *2 VOLTAS DO VIRABREQUIM*.", "UM CICLO COMPLETO.", ('F1',)),
    ],
    'batidas': [
        (0.5, 7.8, "4 TEMPOS, 4 BATIDAS: UM TEMPO", "EM CADA BATIDA DESTA MÚSICA.", ()),
        (8.0, 15.8, "NESSE RITMO O VIRABREQUIM DÁ", "60 VOLTAS POR MINUTO: *60 RPM*.", ('F1',)),
        (16.0, 23.6, "UM MOTOR DE VERDADE É BEM MAIS", "RÁPIDO. VAMOS ACELERAR.", ()),
    ],
    'rpm': [
        (5.0, 11.0, "*800 RPM*: MARCHA LENTA, COMO PARADO", "NO SINAL (600 A 1.000 RPM).", ('F5',)),
        (15.0, 23.0, "*3.000 RPM*: CADA CILINDRO QUEIMA", "25 VEZES POR SEGUNDO.", ('F6',)),
        (27.0, 33.4, "*6.000 RPM*: 50 VEZES POR SEGUNDO.", "RÁPIDO DEMAIS: DESENHAMOS BORRADO.", ('F6',)),
    ],
    'cilindros': [
        (0.5, 7.4, "SÓ 1 TEMPO EM 4 EMPURRA.", "ENTÃO O QUE MANTÉM O GIRO?", ('F1',)),
        (7.6, 14.8, "UM *VOLANTE* PESADO NO VIRABREQUIM", "MANTÉM O GIRO ENTRE OS EMPURRÕES.", ('F7',)),
        (15.2, 23.0, "E *MAIS CILINDROS*: NUM MOTOR DE 4,", "ELES SE REVEZAM.", ()),
        (23.2, 31.4, "UMA ORDEM DE QUEIMA COMUM É *1-3-4-2*.", "UM NOVO EMPURRÃO A CADA MEIA VOLTA.", ('F8',)),
        (31.6, 41.6, "ESCUTE: CADA FAÍSCA", "TOCA A SUA PRÓPRIA NOTA.", ()),
    ],
    'energia': [
        (0.5, 7.6, "PARA ONDE VAI A ENERGIA", "DO COMBUSTÍVEL?", ()),
        (8.0, 15.8, "NUM CARRO A GASOLINA TÍPICO, SÓ", "*16% A 25%* FAZEM O CARRO ANDAR.", ('F9',)),
        (16.0, 23.6, "A MAIOR PARTE SE PERDE NO MOTOR,", "PRINCIPALMENTE COMO *CALOR*.", ('F9',)),
    ],
    'calor': [
        (0.5, 8.0, "A CHAMA PASSA DO PONTO DE FUSÃO DO", "METAL DO MOTOR. COMO ELE AGUENTA?", ('F17',)),
        (8.3, 16.0, "UMA *BOMBA* FAZ A ÁGUA DO MOTOR", "CIRCULAR ATÉ O *RADIADOR*.", ('F17',)),
        (16.3, 24.0, "LÁ O AR ESFRIA A ÁGUA, QUE VOLTA", "PARA BUSCAR MAIS CALOR.", ('F17',)),
        (24.3, 32.6, "O PISTÃO, QUE NÃO PARA DE SE MEXER,", "É ESFRIADO PELO *ÓLEO*.", ('F17',)),
    ],
    'flex': [
        (0.5, 7.4, "DESDE 2003, O BRASIL TEM O CARRO", "*FLEX*: ETANOL, GASOLINA OU OS DOIS.", ('F18',)),
        (7.6, 14.6, "ELE ACEITA *QUALQUER MISTURA* DOS", "DOIS NO MESMO TANQUE.", ('F19',)),
        (14.8, 22.0, "O ETANOL PEDE MAIS COMBUSTÍVEL PARA", "O MESMO AR: *9 PARA 1*, NÃO 14,7.", ('F16',)),
        (22.2, 29.6, "A *SONDA LAMBDA* NO ESCAPE AVISA A", "CENTRAL, QUE AJUSTA O INJETOR.", ('F18',)),
    ],
    'resumo': [
        (0.5, 8.8, "NIKOLAUS OTTO CONSTRUIU UM MOTOR DE", "4 TEMPOS EM *1876*. A IDEIA SEGUE VIVA.", ('F10',)),
        (9.2, 17.8, "OS 4 TEMPOS: ADMISSÃO, COMPRESSÃO,", "COMBUSTÃO (OU EXPLOSÃO) E ESCAPE.", ('F12',)),
        (18.0, 26.6, "A 3.000 RPM, CADA CILINDRO REPETE", "TUDO ISSO *1.500 VEZES POR MINUTO*.", ('F6',)),
    ],
}

FONTES = {
    'F1': ('Encyclopaedia Britannica, "four-stroke cycle"', 'https://www.britannica.com/technology/four-stroke-cycle'),
    'F2': ('Wikipedia, "Camshaft"', 'https://en.wikipedia.org/wiki/Camshaft'),
    'F3': ('Wikipedia, "Compression ratio"', 'https://en.wikipedia.org/wiki/Compression_ratio'),
    'F4': ('University of Windsor, "Four Stroke Cycle Engines"',
           'https://courses.washington.edu/engr100/Section_Wei/engine/UofWindsorManual/Four%20Stroke%20Cycle%20Engines.htm'),
    'F5': ('MechanicBase, "What RPM Should a Car Idle at?"', 'https://mechanicbase.com/?p=34863'),
    'F6': ('Conta a partir do ciclo de 4 tempos (1 queima a cada 2 voltas do virabrequim)', None),
    'F7': ('University of Windsor, "Four Stroke Cycle Engines"',
           'https://courses.washington.edu/engr100/Section_Wei/engine/UofWindsorManual/Four%20Stroke%20Cycle%20Engines.htm'),
    'F8': ('Rick\'s Free Auto Repair Advice, "Firing order for a 4-cylinder engine"',
           'https://ricksfreeautorepairadvice.com/what-is-the-firing-order-for-a-4-cylinder-engine/'),
    'F9': ('fueleconomy.gov (Departamento de Energia dos EUA), "Where the Energy Goes: Gasoline Vehicles"',
           'https://www.fueleconomy.gov/feg/atv.shtml'),
    'F10': ('Encyclopaedia Britannica, "Nikolaus Otto"', 'https://www.britannica.com/biography/Nikolaus-Otto'),
    'F11': ('Wikipedia, "Four-stroke engine"', 'https://en.wikipedia.org/wiki/Four-stroke_engine'),
    'F12': ('Prepara Enem, "Motor de combustão interna" (admissão, compressão, explosão, escape); InfoEscola, "Motor de quatro tempos" (combustão)',
            'https://www.preparaenem.com/fisica/motor-combustao-interna.htm'),
    'F13': ('Wikipedia, "Spark plug"', 'https://en.wikipedia.org/wiki/Spark_plug'),
    'F14': ('Wikipedia, "Ignition coil"', 'https://en.wikipedia.org/wiki/Ignition_coil'),
    'F15': ('Wikipedia, "Fuel injection" e "Manifold injection"', 'https://en.wikipedia.org/wiki/Manifold_injection'),
    'F16': ('Wikipedia, "Stoichiometry" (tabela de proporção ar/combustível)', 'https://en.wikipedia.org/wiki/Stoichiometry'),
    'F17': ('Wikipedia, "Internal combustion engine cooling"', 'https://en.wikipedia.org/wiki/Internal_combustion_engine_cooling'),
    'F18': ('Wikipedia, "Flexible-fuel vehicles in Brazil"', 'https://en.wikipedia.org/wiki/Flexible-fuel_vehicles_in_Brazil'),
    'F19': ('Jornal da USP, "Gasolina mais verde: agora com 30% de etanol sem prejudicar o seu carro"',
            'https://jornal.usp.br/noticias/gasolina-mais-verde-agora-com-30-de-etanol-sem-prejudicar-o-seu-carro/'),
    'F20': ('Wikipedia, "Automotive battery"', 'https://en.wikipedia.org/wiki/Automotive_battery'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'carro': 'Dentro do carro', 'pecas': 'As peças de um cilindro',
                'injetor': 'O injetor de combustível',
                'admissao': 'Tempo 1: admissão', 'compressao': 'Tempo 2: compressão',
                'faisca': 'De onde vem a faísca', 'potencia': 'Tempo 3: combustão', 'escape': 'Tempo 4: escape', 'ciclo': 'Um ciclo completo',
                'batidas': 'Um motor no ritmo da música', 'rpm': 'Na velocidade de verdade',
                'cilindros': 'Volante e 4 cilindros', 'energia': 'Para onde vai a energia',
                'calor': 'Por que o motor não derrete', 'flex': 'O carro flex brasileiro',
                'resumo': 'Otto, 1876, e os 4 tempos'}

DESCRICAO = """Como um motor de carro funciona de verdade? A gente abre um cilindro, monta peça por peça e roda em câmera lenta: admissão, compressão, combustão e escape. No caminho, abrimos o injetor que solta o combustível em spray e a bobina que transforma os 12 volts da bateria na faísca da vela. Depois acelera até a velocidade real, junta mais três cilindros, mostra para onde vai a energia do combustível, por que o motor não derrete e como o carro flex brasileiro aceita etanol e gasolina no mesmo tanque.

Cada quadro é pixel art desenhada por código, e a música é original. Em um trecho, o motor roda exatamente no ritmo da música: 4 tempos, 4 batidas.

Capítulos
{capitulos}

Simplificado de propósito
- Mostramos 2 válvulas por cilindro; muitos motores têm 4 (2 de admissão, 2 de escape).
- As válvulas de verdade abrem um pouco antes e fecham um pouco depois de cada tempo; aqui elas abrem e fecham na virada dos tempos.
- O ponto da faísca muda com a rotação; ela aparece cerca de 20 graus antes do topo.
- A divisão da energia (cerca de 70% perdas no motor, 20% nas rodas, 10% outras) é a faixa de uso combinado cidade + estrada do Departamento de Energia dos EUA.
- O injetor aparece no duto, antes da válvula de admissão (injeção indireta); muitos motores novos injetam direto no cilindro. Os jatos estão em câmera lenta: um a cada 2 batidas da música.
- A conta 14,7 para 1 (gasolina) e 9 para 1 (etanol) é em massa e para a queima completa; o motor nem sempre trabalha exatamente nela.
- Desenhamos a bobina com os dois enrolamentos lado a lado; na bobina de verdade um fica em volta do outro. A faísca sai a cada 2 batidas da música; a 3.000 RPM são 25 por segundo em cada cilindro.
- Chamamos de "água" o líquido de arrefecimento (água com aditivo). Não mostramos a válvula termostática nem a ventoinha. A bomba parada no começo do capítulo é só para mostrar o motor esquentando.
- O jato de óleo embaixo do pistão existe em alguns motores, não em todos.
- No carro flex, a central usa a sonda lambda e outros sensores; o atraso do ajuste está exagerado para dar para ver. Os 30% de etanol na gasolina do posto valem desde agosto de 2025.

Fontes
{fontes}

#motor #comofunciona #pixelart #carros #ciencia #carroflex #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O cilindro do
# close-up ocupa x 105..225; a grade da energia, 34..194.
PREFIXO = 'ep01-motor'
CORTES = [
    dict(id='c1', de=('potencia', 0.0), ate=('potencia', 24.0), x=75, gancho=['A QUEIMA', 'DEVAGAR'],
         titulo='A queima dentro do motor, em câmera lenta 🔥',
         descricao='O tempo de combustão: a vela solta a faísca um pouco antes do topo e o gás quente empurra o pistão para baixo. É o único dos 4 tempos que gera força.'),
    dict(id='c2', de=('ciclo', 0.0), ate=('batidas', 24.0), x=75, gancho=['4 TEMPOS', '4 BATIDAS'],
         titulo='Um motor tocando no ritmo da música 🎵',
         descricao='4 tempos, 4 batidas: a cada batida da música o motor faz um tempo. Nesse ritmo o virabrequim dá 60 voltas por minuto.'),
    dict(id='c3', de=('rpm', 0.0), ate=('rpm', 33.6), x=75, gancho=['DE 60 A', '6.000 RPM'],
         titulo='Um motor de 60 a 6.000 RPM 🏎️',
         descricao='A 3.000 RPM cada cilindro queima combustível 25 vezes por segundo. A 6.000, 50 vezes: rápido demais para o olho.'),
    dict(id='c4', de=('cilindros', 0.0), ate=('cilindros', 15.0), x=75, gancho=['PRA QUE', 'O VOLANTE?'],
         titulo='Por que o motor precisa de um volante pesado?',
         descricao='Só 1 dos 4 tempos empurra o pistão. Nos outros 3, quem mantém o giro é o volante, um disco pesado no virabrequim.'),
    dict(id='c5', de=('energia', 0.0), ate=('energia', 24.0), x=30, gancho=['ONDE VAI A', 'GASOLINA?'],
         titulo='Para onde vai a energia da gasolina? ⛽',
         descricao='Num carro a gasolina típico, só 16% a 25% da energia do combustível fazem o carro andar (uso misto, Departamento de Energia dos EUA). A maior parte vira calor no motor.'),
    dict(id='c6', de=('admissao', 0.0), ate=('compressao', 24.0), x=75, gancho=['ADMISSÃO E', 'COMPRESSÃO'],
         titulo='Os 2 primeiros tempos do motor, por dentro',
         descricao='Admissão: o pistão desce e a mistura de ar e combustível entra. Compressão: as válvulas fecham e o pistão espreme a mistura num espaço de 8 a 12 vezes menor.'),
    dict(id='c7', de=('faisca', 0.0), ate=('faisca', 31.2), x=105, gancho=['DE 12 VOLTS', 'A 25.000'],
         titulo='Como 12 volts viram a faísca da vela ⚡',
         descricao='A bateria do carro tem 12 volts, mas a vela precisa de 12.000 a 25.000 volts ou mais. Quem faz o salto é a bobina: poucas voltas de fio de um lado, milhares do outro. Cortou a corrente, o choque pula a folga da vela.'),
]
