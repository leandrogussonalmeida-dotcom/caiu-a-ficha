#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep16 (série FEITO DE PIXELS): Como o processador pensa.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep16_motor.py` e `ep16_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Bit: a menor unidade de informação na computação; um de dois valores,
      em geral 1 e 0; pode ser feito com um dispositivo de dois estados, por
      exemplo dois níveis de tensão ou de corrente; 8 bits = 1 byte.
      Wikipedia, "Bit".
  F2  Binário: só dois símbolos, 0 e 1; cada casa vale uma potência de 2;
      usado por quase todos os computadores modernos; contagem 0, 1, 10, 11,
      100; somar 1 + 1 dá 0 e vai 1 para a próxima casa.
      Wikipedia, "Binary number".
  F3  MOSFET: a tensão na porta (isolada) decide se o transistor conduz; ela
      cria um canal entre fonte e dreno por onde a corrente passa; é de longe
      o transistor mais comum dos circuitos digitais e faz as chaves das
      portas lógicas; chips digitais têm de milhares a bilhões deles; o
      primeiro MOSFET funcionando é de 1959. Wikipedia, "MOSFET".
  F4  Portas lógicas (tabelas-verdade de E, OU, NÃO e OU EXCLUSIVO); hoje a
      maioria das portas é feita de MOSFETs. Wikipedia, "Logic gate".
  F5  Somador completo de 1 bit: entram A, B e o vai-um (Cin); saem a soma
      S = A xor B xor Cin e o vai-um Cout = A.B + Cin.(A xor B); vários somadores
      fazem números maiores, cada um usa o Cout do anterior como Cin.
      IIIT Hyderabad Virtual Labs, "Adder Circuit".
  F6  Frequência do relógio: pulsos que sincronizam as peças do processador;
      medida em hertz; 3 GHz = três bilhões de ciclos por segundo; os
      primeiros computadores pessoais (anos 1970 e 1980) eram em MHz.
      Wikipedia, "Clock rate".
  F7  Ciclo de instrução: busca, decodificação e execução; o contador de
      programa (PC) guarda o endereço da próxima instrução e sobe 1 na busca;
      o registrador de instrução guarda a instrução; a unidade de controle
      decodifica; a ULA faz as contas; o ciclo roda do ligar ao desligar.
      Wikipedia, "Instruction cycle".
  F8  Um chip recente (2024): 28 bilhões de transistores, tecnologia de "3
      nanômetros" de segunda geração, CPU de até 10 núcleos (4 de desempenho
      e 6 de eficiência). Página do fabricante (sala de imprensa). O desenho
      é genérico, sem marca.
  F9  "3 nm" não tem relação direta com nenhuma medida física do transistor;
      é usado como nome comercial; a distância entre portas vizinhas (gate
      pitch) desses processos fica entre 45 e 54 nm. Wikipedia, "3 nm process".
  F10 O primeiro microprocessador num só chip (1971) tinha 2.250 transistores;
      áreas de pastilhas recentes: 103,8 mm² e 420,2 mm².
      Wikipedia, "Transistor count".
  F11 Luz no vácuo: 299.792.458 m/s; cerca de 30 cm por nanossegundo; num
      relógio de 1 GHz o sinal anda no máximo uns 30 cm por ciclo, por isso
      processador e memória ficam perto. Wikipedia, "Speed of light".
  F12 Processador de vários núcleos: um só chip com dois ou mais núcleos
      separados; roda instruções em núcleos diferentes ao mesmo tempo.
      Wikipedia, "Multi-core processor".
  F13 Contas: 299.792.458 / 3.000.000.000 = 0,0999 m (uns 10 cm por tique);
      1 / 3 GHz = 0,33 ns; raiz de 103,8 mm² = 10,2 mm e de 420,2 mm² = 20,5 mm
      (1 a 2 cm de lado); 28 bilhões / 2.250 = 12,4 milhões; 120 batidas por
      minuto = 2 por segundo; 5 + 3 = 8 (0101 + 0011 = 1000).
  F14 CMOS: a porta NÃO (inversor) é um transistor P em cima e um N embaixo,
      ligados à mesma entrada; a saída é o contrário da entrada; com entrada
      alta o N conduz e liga a saída ao 0. Wikipedia, "CMOS".

NÃO LIDA (bloqueada na hora da pesquisa): electronics-tutorials.ws (somador
completo). Não usada.
"""

TITULO = "Como o processador pensa | De 0 e 1 a bilhões de contas, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='drop'),               # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),              # 6 s
    dict(id='bits', gen='lofi', bars=10, papel='drop'),                # 30 s
    dict(id='contar', gen='lofi', bars=8, papel='drop'),               # 24 s
    dict(id='transistor', gen='synthwave', bars=16, papel='drop'),     # 38,4 s
    dict(id='portas', gen='lofi', bars=16, papel='drop'),              # 48 s
    dict(id='somador', gen='synthwave', bars=15, papel='drop'),        # 36 s
    dict(id='soma4', gen='lofi', bars=14, papel='drop'),               # 42 s
    dict(id='relogio', gen='house', bars=14, papel='drop', bpm=120),   # 28 s
    dict(id='cpu', gen='lofi', bars=10, papel='drop'),                 # 30 s
    dict(id='ciclo', gen='house', bars=24, papel='drop', bpm=120),     # 48 s
    dict(id='escala', gen='lofi', bars=14, papel='drop'),              # 42 s
    dict(id='luz', gen='lofi', bars=8, papel='drop'),                  # 24 s
    dict(id='nucleos', gen='synthwave', bars=12, papel='drop'),        # 28,8 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),              # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                 # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "ENQUANTO VOCÊ VÊ ISTO, UM PROCESSADOR", "DÁ *BILHÕES DE PASSOS* POR SEGUNDO.", ('F6',)),
        (6.2, 11.6, "E CADA PASSO É FEITO SÓ DE", "*0 E 1*. VAMOS ABRIR UM.", ('F1',)),
    ],
    'bits': [
        (0.5, 7.0, "UM *BIT* É A MENOR INFORMAÇÃO:", "SÓ PODE SER 0 OU 1.", ('F1',)),
        (7.4, 14.0, "NO CHIP, O BIT É UMA *TENSÃO*:", "ALTA = 1, BAIXA = 0.", ('F1',)),
        (14.4, 21.4, "8 BITS JUNTOS FORMAM *1 BYTE*.", "COM ELES DÁ PARA ESCREVER NÚMEROS.", ('F1', 'F2')),
        (21.8, 29.4, "EM BINÁRIO, CADA CASA VALE O *DOBRO*", "DA CASA DA DIREITA: 1, 2, 4, 8...", ('F2',)),
    ],
    'contar': [
        (0.5, 6.8, "CONTANDO EM BINÁRIO, UM NÚMERO", "A CADA BATIDA DA MÚSICA.", ('F2',)),
        (7.0, 13.4, "0, 1, 10, 11, 100... QUANDO A CASA", "ENCHE, *VAI 1* PARA A PRÓXIMA.", ('F2',)),
        (13.8, 18.6, "GUARDE ESTES DOIS: *5 = 0101*", "E *3 = 0011*.", ('F2',)),
        (18.8, 23.6, "MAS QUEM FAZ A CONTA?", "UMA *CHAVE* MINÚSCULA.", ()),
    ],
    'transistor': [
        (0.5, 7.4, "O *TRANSISTOR*: UMA CHAVE QUE LIGA", "E DESLIGA COM ELETRICIDADE.", ('F3',)),
        (7.8, 14.6, "ELE TEM 3 PONTAS: *FONTE*, *DRENO*", "E, EM CIMA, A *PORTA* (GATE).", ('F3',)),
        (15.0, 22.0, "PORTA SEM TENSÃO: NÃO HÁ CAMINHO.", "A CORRENTE *NÃO PASSA*.", ('F3',)),
        (22.4, 29.4, "TENSÃO NA PORTA: ABRE UM *CANAL*", "E A CORRENTE ATRAVESSA.", ('F3',)),
        (29.8, 37.8, "É O TRANSISTOR MAIS COMUM DOS CHIPS", "DIGITAIS: O *MOSFET*, DE 1959.", ('F3',)),
    ],
    'portas': [
        (0.5, 7.4, "JUNTE 2 TRANSISTORES E SAI UMA", "*PORTA LÓGICA*: A PORTA *NÃO*.", ('F4', 'F14')),
        (7.8, 15.4, "ENTRA 1, SAI 0. ENTRA 0, SAI 1.", "ELA *INVERTE* O BIT.", ('F4', 'F14')),
        (16.0, 23.4, "A PORTA *E* (AND) SÓ DÁ 1 SE AS", "DUAS ENTRADAS FOREM 1.", ('F4',)),
        (23.8, 31.4, "SÃO 4 COMBINAÇÕES DE ENTRADA.", "SÓ UMA ACENDE A SAÍDA.", ('F4',)),
        (32.0, 39.4, "A PORTA *OU* (OR) DÁ 1 SE PELO", "MENOS UMA ENTRADA FOR 1.", ('F4',)),
        (39.8, 47.4, "HOJE, QUASE TODA PORTA LÓGICA É", "FEITA DE *MOSFETS*.", ('F4',)),
    ],
    'somador': [
        (0.5, 7.4, "COM PORTAS DÁ PARA FAZER *CONTA*.", "ESTE É UM *SOMADOR* DE 1 BIT.", ('F5',)),
        (7.8, 14.8, "ENTRAM 3 BITS: *A*, *B* E O *VAI-UM*", "QUE VEM DA CASA DA DIREITA.", ('F5',)),
        (15.2, 22.2, "SAEM 2: A *SOMA* E UM NOVO VAI-UM", "PARA A CASA DA ESQUERDA.", ('F5',)),
        (22.6, 29.6, "A PORTA *XOR* DÁ 1 QUANDO AS", "DUAS ENTRADAS SÃO DIFERENTES.", ('F4', 'F5')),
        (30.0, 35.6, "1 + 1 = 10 EM BINÁRIO:", "SOMA 0 E *VAI 1*.", ('F2', 'F5')),
    ],
    'soma4': [
        (0.5, 7.4, "4 SOMADORES LADO A LADO SOMAM", "NÚMEROS DE 4 BITS: *5 + 3*.", ('F5',)),
        (7.8, 14.8, "CASA DA DIREITA: 1 + 1 = 10.", "SOMA 0 E *VAI 1* PARA A ESQUERDA.", ('F2', 'F5')),
        (15.2, 22.2, "O VAI-UM PASSA DE SOMADOR EM", "SOMADOR, COMO UMA *ONDA*.", ('F5',)),
        (22.6, 29.6, "RESULTADO: *1000*. EM BINÁRIO,", "ISSO É 8. *5 + 3 = 8*.", ('F2', 'F13')),
        (30.0, 35.6, "QUALQUER PAR DE 0 A 15 FUNCIONA:", "SÃO SÓ PORTAS E TRANSISTORES.", ('F5',)),
        (35.8, 41.6, "NÚMEROS MAIORES? É SÓ PÔR MAIS", "SOMADORES NA FILA.", ('F5',)),
    ],
    'relogio': [
        (0.5, 7.4, "QUEM DÁ O RITMO É O *RELÓGIO*:", "UM PULSO QUE SOBE E DESCE.", ('F6',)),
        (7.8, 14.6, "AQUI ELE BATE JUNTO COM A MÚSICA:", "*2 TIQUES POR SEGUNDO*.", ('F13',)),
        (15.0, 21.6, "A CADA TIQUE, O CHIP DÁ UM PASSO", "E GUARDA O RESULTADO.", ('F6',)),
        (22.0, 27.6, "NA VIDA REAL: *3 GHZ* = 3 BILHÕES", "DE TIQUES POR SEGUNDO.", ('F6',)),
    ],
    'cpu': [
        (0.5, 7.0, "AGORA, UM PROCESSADOR DE BRINQUEDO.", "NA *MEMÓRIA* FICA O PROGRAMA.", ('F7',)),
        (7.4, 14.4, "O *CONTADOR DE PROGRAMA* (PC) GUARDA", "O ENDEREÇO DA PRÓXIMA INSTRUÇÃO.", ('F7',)),
        (14.8, 21.8, "A *UNIDADE DE CONTROLE* LÊ A", "INSTRUÇÃO E DIZ O QUE FAZER.", ('F7',)),
        (22.2, 29.6, "*REGISTRADORES* GUARDAM NÚMEROS.", "A *ULA* FAZ AS CONTAS (O SOMADOR!).", ('F7',)),
    ],
    'ciclo': [
        (0.5, 6.8, "UMA ETAPA A CADA TIQUE. O PROGRAMA", "PÕE *5* EM A E *3* EM B.", ('F7',)),
        (7.2, 13.8, "CÂMERA LENTA. 1: *BUSCA*. O PC APONTA,", "A INSTRUÇÃO VEM E O PC SOBE.", ('F7',)),
        (14.0, 19.8, "2: *DECODIFICA*. O CONTROLE LÊ", "\"SOMA\" E LIGA A ULA.", ('F7',)),
        (20.0, 25.8, "3: *EXECUTA*. A ULA SOMA 5 + 3", "E GUARDA *8* EM A.", ('F7', 'F13')),
        (26.0, 31.8, "DEPOIS: GUARDA O 8 NA MEMÓRIA", "E *VOLTA* PARA A SOMA.", ()),
        (32.0, 39.6, "BUSCA, DECODIFICA, EXECUTA...", "E O NÚMERO EM A NÃO PARA DE SUBIR.", ('F7',)),
        (40.0, 47.6, "O CICLO RODA DO LIGAR AO DESLIGAR,", "*BILHÕES DE VEZES POR SEGUNDO*.", ('F7', 'F6')),
    ],
    'escala': [
        (0.5, 7.4, "QUANTOS TRANSISTORES CABEM NUM", "PROCESSADOR DE VERDADE?", ()),
        (7.8, 14.8, "UM CHIP RECENTE DE COMPUTADOR TEM", "*28 BILHÕES* DE TRANSISTORES.", ('F8',)),
        (15.2, 22.2, "E A PASTILHA TEM SÓ *1 A 2 CM*", "DE LADO.", ('F10', 'F13')),
        (22.6, 29.6, "O NOME *3 NM* É COMERCIAL: AS PORTAS", "FICAM A UNS *45 A 54 NM* DE DISTÂNCIA.", ('F8', 'F9')),
        (30.0, 36.8, "EM 1971, O PRIMEIRO MICROPROCESSADOR", "TINHA *2.250* TRANSISTORES.", ('F10',)),
        (37.2, 41.6, "HOJE: MAIS DE *12 MILHÕES*", "DE VEZES ISSO.", ('F8', 'F10', 'F13')),
    ],
    'luz': [
        (0.5, 7.4, "UM TIQUE A 3 GHZ É TÃO CURTO QUE", "ATÉ A *LUZ* ANDA POUCO NELE.", ('F6', 'F11')),
        (7.8, 14.8, "A LUZ FAZ *299.792 KM* POR SEGUNDO.", "EM 1 TIQUE: SÓ UNS *10 CM*.", ('F11', 'F13')),
        (15.2, 23.6, "POR ISSO O PROCESSADOR E A MEMÓRIA", "FICAM *PERTINHO* UM DO OUTRO.", ('F11',)),
    ],
    'nucleos': [
        (0.5, 7.4, "O QUE MONTAMOS É *1 NÚCLEO*.", "CHIPS DE HOJE TÊM VÁRIOS.", ('F12',)),
        (7.8, 14.8, "CADA NÚCLEO TEM O SEU PC E RODA", "O SEU PROGRAMA, *AO MESMO TEMPO*.", ('F12',)),
        (15.2, 22.2, "UM CHIP RECENTE TEM *ATÉ 10 NÚCLEOS*:", "4 DE DESEMPENHO E 6 DE ECONOMIA.", ('F8',)),
        (22.6, 28.4, "MAIS NÚCLEOS, MAIS TAREFAS", "EM *PARALELO*.", ('F12',)),
    ],
    'resumo': [
        (0.5, 9.0, "TRANSISTOR VIRA PORTA, PORTA VIRA", "SOMADOR, SOMADOR VIRA *PROCESSADOR*.", ('F4', 'F5', 'F14')),
        (9.4, 19.0, "O RELÓGIO BATE E O CICLO GIRA:", "*BUSCA, DECODIFICA, EXECUTA*.", ('F6', 'F7')),
        (19.4, 29.4, "E TUDO, NO FUNDO, É SÓ *0 E 1*,", "LIGANDO E DESLIGANDO.", ('F1',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Bit"', 'https://en.wikipedia.org/wiki/Bit'),
    'F2': ('Wikipedia, "Binary number"', 'https://en.wikipedia.org/wiki/Binary_number'),
    'F3': ('Wikipedia, "MOSFET"', 'https://en.wikipedia.org/wiki/MOSFET'),
    'F4': ('Wikipedia, "Logic gate"', 'https://en.wikipedia.org/wiki/Logic_gate'),
    'F5': ('IIIT Hyderabad Virtual Labs, "Adder Circuit"', 'https://cse15-iiith.vlabs.ac.in/exp/adder-circuit/theory.html'),
    'F6': ('Wikipedia, "Clock rate"', 'https://en.wikipedia.org/wiki/Clock_rate'),
    'F7': ('Wikipedia, "Instruction cycle"', 'https://en.wikipedia.org/wiki/Instruction_cycle'),
    'F8': ('Apple Newsroom, "Apple introduces M4 chip" (7/5/2024): 28 bilhões de transistores, 3 nm de 2ª geração, CPU de até 10 núcleos',
           'https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/'),
    'F9': ('Wikipedia, "3 nm process"', 'https://en.wikipedia.org/wiki/3_nm_process'),
    'F10': ('Wikipedia, "Transistor count"', 'https://en.wikipedia.org/wiki/Transistor_count'),
    'F11': ('Wikipedia, "Speed of light"', 'https://en.wikipedia.org/wiki/Speed_of_light'),
    'F12': ('Wikipedia, "Multi-core processor"', 'https://en.wikipedia.org/wiki/Multi-core_processor'),
    'F13': ('Contas: 299.792.458 / 3 bilhões; 1 / 3 GHz; raiz das áreas; 28 bilhões / 2.250; 120 / 60; 5 + 3 em binário', None),
    'F14': ('Wikipedia, "CMOS"', 'https://en.wikipedia.org/wiki/CMOS'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'bits': 'Tudo é 0 e 1: o bit', 'contar': 'Contando em binário',
                'transistor': 'O transistor: uma chave elétrica', 'portas': 'Portas lógicas: NÃO, E, OU',
                'somador': 'O somador de 1 bit', 'soma4': '5 + 3 = 8 em binário',
                'relogio': 'O relógio no ritmo da música', 'cpu': 'As peças do processador',
                'ciclo': 'Busca, decodifica, executa', 'escala': '28 bilhões de transistores',
                'luz': 'A luz e o tique do relógio', 'nucleos': 'Vários núcleos', 'resumo': 'Resumo'}

DESCRICAO = """Como um processador "pensa"? A gente começa no bit, um 0 ou 1 feito de tensão, conta em binário no ritmo da música e abre um transistor (MOSFET) para ver a porta abrir um canal e deixar a corrente passar. Com 2 transistores sai a porta NÃO; depois vêm as portas E e OU, um somador de 1 bit e 4 somadores em fila fazendo 5 + 3 = 8, com o vai-um passando de casa em casa. Aí entra o relógio, um processador de brinquedo (memória, contador de programa, unidade de controle, registradores e ULA) rodando busca, decodifica e executa, e no fim a escala de verdade: bilhões de transistores numa pastilha de 1 a 2 cm, a luz que anda só uns 10 cm por tique e os vários núcleos.

Cada quadro é pixel art desenhada por código, e a música é original. As portas, o somador e o processador são simulados de verdade: cada 0 e 1 da tela é calculado, não desenhado à mão. No capítulo do relógio, cada tique cai exatamente numa batida da música.

Capítulos
{capitulos}

Simplificado de propósito
- Tudo está em câmera lenta: o relógio da tela bate 2 vezes por segundo e os bits andam devagar pelos fios. Num chip de verdade são bilhões de tiques por segundo.
- O transistor é um MOSFET de canal N desenhado em corte, plano. Os transistores de hoje têm formato em 3D (aletas e folhas) e as medidas não estão em escala.
- A porta NÃO é desenhada com 2 transistores, como no CMOS. As portas E e OU, o somador e o processador aparecem como símbolos; por dentro, também são transistores.
- O processador de brinquedo tem 4 bits de endereço, 2 registradores e 5 instruções inventadas para o vídeo (carrega, soma, guarda, pula). Processadores reais têm centenas de instruções, memória rápida (cache), fazem várias etapas ao mesmo tempo (pipeline) e nem toda instrução leva um tique por etapa.
- "3 GHz" e "28 bilhões de transistores" são números de chips recentes, mostrados sem marca. A pastilha de 1 a 2 cm de lado vem das áreas de pastilhas recentes (103,8 e 420,2 mm²).
- Os 10 cm por tique são a distância da luz no vácuo; num fio de chip o sinal é mais lento ainda.

Fontes
{fontes}

#processador #computador #comofunciona #pixelart #binario #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Em VERTICAL as
# cenas destes cortes usam um arranjo mais estreito (ver ep16_motor.py).
PREFIXO = 'ep16-processador'
CORTES = [
    dict(id='c1', de=('contar', 0.0), ate=('contar', 24.0), x=60, gancho=['CONTANDO', 'EM BINÁRIO'],
         titulo='Contando em binário no ritmo da música 🎵',
         descricao='Um número a cada batida: 0, 1, 10, 11, 100... Quando a casa enche, vai 1 para a próxima. Cada casa vale o dobro da casa da direita.'),
    dict(id='c2', de=('transistor', 0.0), ate=('transistor', 37.8), x=60, gancho=['A CHAVE', 'DO CHIP'],
         titulo='O transistor: a chave que liga com eletricidade ⚡',
         descricao='Um MOSFET por dentro: sem tensão na porta não há caminho; com tensão, abre um canal e a corrente passa entre a fonte e o dreno.'),
    dict(id='c3', de=('soma4', 0.0), ate=('soma4', 29.6), x=43, gancho=['5 + 3', 'EM BINÁRIO'],
         titulo='Como o chip soma 5 + 3 (com o vai-um) ➕',
         descricao='4 somadores de 1 bit em fila: 0101 + 0011. O vai-um passa de casa em casa como uma onda até dar 1000, que é 8.'),
    dict(id='c4', de=('relogio', 0.0), ate=('relogio', 28.0), x=40, gancho=['O RELÓGIO', 'DO CHIP'],
         titulo='O relógio do processador batendo na música ⏱️',
         descricao='Aqui o relógio dá 2 tiques por segundo, junto com a batida. Num processador de 3 GHz são 3 bilhões de tiques por segundo.'),
    dict(id='c5', de=('ciclo', 7.0), ate=('ciclo', 32.0), x=98, gancho=['BUSCA', 'E EXECUTA'],
         titulo='Busca, decodifica, executa: uma instrução por dentro',
         descricao='O contador de programa aponta a instrução, a unidade de controle lê "soma" e a ULA faz 5 + 3 = 8. Depois o ciclo se repete.'),
    dict(id='c6', de=('luz', 0.0), ate=('luz', 23.6), x=0, gancho=['A LUZ É', 'LENTA?'],
         titulo='Em 1 tique de 3 GHz a luz anda só 10 cm 💡',
         descricao='A luz faz 299.792 km por segundo, mas um tique de 3 GHz dura 0,33 nanossegundo: dá para ela andar só uns 10 cm. Por isso processador e memória ficam perto.'),
]
