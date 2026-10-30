#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep13 (série POR DENTRO): Como funciona o motor elétrico.

A ideia: abrir um motor elétrico genérico (sem marca) e montar a ideia peça
por peça: ímãs (polos que atraem e empurram), a corrente que faz campo
(Oersted, 1820), a bobina que vira eletroímã, o motor de corrente contínua
(estator, rotor, comutador e escovas: a corrente inverte a cada meia volta),
o motor sem escovas (o controlador liga as bobinas em sequência e o ímã
persegue o campo), o de indução (a gaiola que vai sempre um pouco atrás),
os motores da casa, a eficiência e o torque desde o zero. Protagonista: o
ROTOR, com contador de VOLTAS e painel de RPM, e os pulsos de corrente. No
capítulo `batida` a corrente inverte na batida da música; em `brushless` o
controlador liga uma bobina por batida; no final (`trifasico`) as três fases
têm o pico em batidas seguidas (A, B, C) e o campo gira no compasso.

O desenho mora em `ep13_motor.py` (cenas) e `ep13_desenho.py` (peças).
`longo_verificar.py --roteiro ep13_roteiro` reprova legenda que não cabe,
caractere sem glifo, legenda curta demais e fato sem fonte.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Todo ímã tem dois polos, norte e sul; polos iguais se repelem e
      diferentes se atraem; os polos vêm sempre em par. LibreTexts,
      "Introduction to Physics (Park)", 10.2 Magnets.
  F2  Em 1820, Oersted publicou que uma agulha de bússola era desviada por uma
      corrente elétrica próxima. Wikipedia, "Hans Christian Ørsted".
  F3  A corrente na bobina cria um campo concentrado no centro dela; o campo
      some quando a corrente é desligada; um núcleo pode deixar o campo
      "milhares de vezes" mais forte; regra da mão direita (o sentido do campo
      segue o sentido da corrente); Sturgeon fez o primeiro eletroímã em 1824;
      Oersted, 1820. Wikipedia, "Electromagnet".
  F4  Motor de corrente contínua com escovas: estator de ímã permanente é o
      mais comum nos motores pequenos; o comutador inverte a corrente na bobina
      quando o torque cai a zero, a cada meia volta (motor de 2 polos), e o
      rotor passa por esse ponto no embalo; as escovas se gastam e precisam ser
      trocadas; no de ímã permanente, o torque é máximo com o eixo parado e
      cai em linha reta com a velocidade. Wikipedia, "Brushed DC electric motor".
  F5  Oersted 1820; Faraday mostrou o primeiro giro em 3/9/1821; Sturgeon, o
      primeiro motor com comutador capaz de mover máquinas (1832); o comutador
      inverte a corrente a cada meia volta (180°); no sem escovas, uma chave
      eletrônica sincronizada com o rotor faz o papel do comutador; corrente
      alternada nos enrolamentos cria polos que giram; usos em casa (máquina
      de lavar, ventilador...); motores sem escovas de até ~100 kW em carros
      elétricos; eficiência de 15-20% (polo sombreado) a 98% (ímã permanente).
      Wikipedia, "Electric motor".
  F6  Sem escovas: um controlador eletrônico substitui escovas e comutador;
      ímãs no rotor giram em volta da armadura fixa; o controlador liga os
      enrolamentos em sequência e o campo gira, com o rotor de ímã atrás; um
      sensor (Hall, por exemplo) mede a posição do rotor; 3 enrolamentos no
      estator; ventoinhas de equipamentos eletrônicos usam exclusivamente
      motores sem escovas; nas máquinas de lavar permitiram trocar correia e
      caixa de engrenagens por tração direta; usados em carros elétricos.
      Wikipedia, "Brushless DC electric motor".
  F7  Indução: o campo do estator gira com a corrente alternada e induz uma
      corrente no rotor, como no secundário de um transformador; não precisa
      de ligação elétrica no rotor; rotor de gaiola com barras; o rotor gira
      sempre um pouco mais devagar que o campo (na velocidade do campo não há
      corrente induzida nem torque); escorregamento de ~0,5% a 5% (projeto B);
      4 polos a 60 Hz = 1.800 RPM; eficiência em plena carga de 85% a 97%;
      perdas: atrito e ventilação, núcleo, enrolamentos do estator e do rotor;
      Ferraris (1885) e Tesla (1887). Wikipedia, "Induction motor".
  F8  Trifásico: 3 correntes com 1/3 de ciclo (120°) de diferença; produzem um
      campo magnético que gira, com sentido definido e intensidade constante.
      Wikipedia, "Three-phase electric power".
  F9  Um carro elétrico típico é 87%-91% eficiente (contando a frenagem
      regenerativa), (gasolina: 16-25% no uso misto, F13).
      Departamento de Energia dos EUA, Fact of the Week #1360 (2024).
  F10 Motores elétricos dão torque alto desde a largada; a maioria dos carros
      elétricos usa câmbio de relação fixa e não tem embreagem. Wikipedia,
      "Electric car".
  F11 Brasil: rede de 60 Hz (127/220 V e 220/380 V). Wikipedia, "Mains
      electricity by country".
  F12 Conta: 60 ciclos por segundo, 2 polos -> o campo dá 60 voltas por
      segundo = 3.600 RPM (com 4 polos, metade: 1.800, como em F7).
"""

TITULO = "Como funciona o motor elétrico | Ímãs, bobinas e o campo que gira, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),             # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='imas', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='orsted', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='bobina', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='pecas', gen='synthwave', bars=20, papel='drop'),         # 48 s (6 peças x 8 s)
    dict(id='dcmotor', gen='lofi', bars=12, papel='break'),           # 36 s
    dict(id='batida', gen='house', bars=12, papel='drop', bpm=120),   # 24 s (inverte na batida)
    dict(id='escovas', gen='synthwave', bars=10, papel='drop'),       # 24 s
    dict(id='brushless', gen='synthwave', bars=15, papel='drop'),     # 36 s (1 bobina por batida)
    dict(id='inducao', gen='lofi', bars=10, papel='drop'),            # 30 s
    dict(id='casa', gen='lofi', bars=14, papel='drop'),               # 42 s
    dict(id='eficiencia', gen='lofi', bars=10, papel='break'),        # 30 s
    dict(id='torque', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='historia', gen='lofi', bars=8, papel='break'),           # 24 s
    dict(id='trifasico', gen='house', bars=20, papel='drop', bpm=120),  # 40 s (A, B, C na batida)
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),              # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "SEM FOGO, SEM FUMAÇA, SEM EXPLOSÃO.", "SÓ *ÍMÃS* E *CORRENTE ELÉTRICA*.", ()),
        (6.0, 11.6, "E QUASE TUDO VIRA GIRO: *85% A 97%*", "NUM MOTOR DE INDUÇÃO, EM CARGA TOTAL.", ('F7',)),
    ],
    'imas': [
        (0.5, 7.6, "TODO ÍMÃ TEM DOIS POLOS: *NORTE*", "(VERMELHO) E *SUL* (AZUL).", ('F1',)),
        (7.8, 15.0, "POLOS DIFERENTES SE *ATRAEM*.", "", ('F1',)),
        (15.2, 22.4, "POLOS IGUAIS SE *EMPURRAM*.", "", ('F1',)),
        (22.6, 29.6, "UM ÍMÃ NUM EIXO GIRA, SE ALINHA E", "*PARA*. COMO FAZER ELE NÃO PARAR?", ('F1',)),
    ],
    'orsted': [
        (0.5, 7.6, "EM *1820*, OERSTED VIU UMA BÚSSOLA", "SE MEXER PERTO DE UM FIO LIGADO.", ('F2',)),
        (7.8, 15.6, "A CORRENTE NO FIO CRIA UM", "*CAMPO MAGNÉTICO* EM VOLTA DELE.", ('F2', 'F3')),
        (15.8, 23.6, "INVERTA A CORRENTE E AS AGULHAS", "*VIRAM PARA O OUTRO LADO*.", ('F3',)),
    ],
    'bobina': [
        (0.5, 7.6, "ENROLE O FIO NUMA *BOBINA*: O CAMPO", "SE CONCENTRA NO MEIO DELA.", ('F3',)),
        (7.8, 15.6, "A BOBINA VIRA UM ÍMÃ, COM NORTE", "E SUL: UM *ELETROÍMÃ*.", ('F3',)),
        (15.8, 22.6, "COM UM NÚCLEO DE FERRO, O CAMPO PODE", "FICAR *MILHARES DE VEZES* MAIS FORTE.", ('F3',)),
        (22.8, 29.6, "DESLIGOU, O CAMPO SOME. INVERTEU A", "CORRENTE: *NORTE E SUL TROCAM*.", ('F3',)),
    ],
    'pecas': [
        (0.3, 7.6, "OS *ÍMÃS* FICAM PARADOS:", "É O *ESTATOR*.", ('F4',)),
        (8.3, 15.6, "NO MEIO, UMA *BOBINA* QUE GIRA:", "É O *ROTOR*.", ('F4',)),
        (16.3, 23.6, "O *EIXO* LEVA O GIRO PARA FORA:", "PARA A HÉLICE, A RODA, A BOMBA.", ()),
        (24.3, 31.6, "O *COMUTADOR*: UM ANEL CORTADO", "EM DUAS METADES, PRESO NO EIXO.", ('F4',)),
        (32.3, 39.6, "AS *ESCOVAS* ENCOSTAM NO ANEL E", "LEVAM A CORRENTE ATÉ A BOBINA.", ('F4',)),
        (40.3, 47.6, "E A *PILHA*: A CORRENTE CONTÍNUA", "QUE FAZ TUDO ANDAR.", ()),
    ],
    'dcmotor': [
        (0.5, 8.6, "A CORRENTE FAZ DA BOBINA UM ÍMÃ.", "O *SUL* DO ESTATOR PUXA O *NORTE* DELA.", ('F1', 'F3')),
        (8.8, 17.6, "SÓ QUE, ALINHADA, A FORÇA DE GIRO", "*CAI A ZERO*. ELA PARARIA ALI.", ('F4',)),
        (17.8, 26.6, "NA HORA CERTA, O *COMUTADOR* INVERTE", "A CORRENTE: OS POLOS DELA TROCAM.", ('F4',)),
        (26.8, 35.6, "ISSO A CADA *MEIA VOLTA*. ELA PASSA", "NO EMBALO E SEGUE GIRANDO.", ('F4', 'F5')),
    ],
    'batida': [
        (0.5, 7.6, "AGORA NO RITMO: A CORRENTE INVERTE", "*EM CADA BATIDA* DA MÚSICA.", ()),
        (7.8, 15.6, "2 INVERSÕES POR VOLTA, 2 BATIDAS POR", "SEGUNDO: 1 VOLTA POR SEGUNDO, *60 RPM*.", ('F4',)),
        (16.0, 23.6, "INVERTENDO 2 VEZES POR BATIDA,", "O GIRO DOBRA: *120 RPM*.", ('F4',)),
    ],
    'escovas': [
        (0.5, 7.6, "MAS AS ESCOVAS *RASPAM* NO ANEL O", "TEMPO TODO: SE GASTAM E SÃO TROCADAS.", ('F4',)),
        (7.8, 15.6, "A SAÍDA: TIRAR AS ESCOVAS E DEIXAR", "A *ELETRÔNICA* TROCAR A CORRENTE.", ('F5', 'F6')),
        (15.8, 23.6, "É O MOTOR *SEM ESCOVAS*: O ÍMÃ GIRA", "E AS BOBINAS FICAM PARADAS.", ('F6',)),
    ],
    'brushless': [
        (0.5, 8.6, "AGORA AS *BOBINAS* FICAM EM VOLTA", "E O ÍMÃ GIRA NO MEIO.", ('F6',)),
        (8.8, 17.6, "O CONTROLADOR LIGA AS BOBINAS", "*EM SEQUÊNCIA*: A, B, C, A, B, C...", ('F6',)),
        (17.8, 26.6, "O ÍMÃ VAI ATRÁS DO POLO QUE ACENDEU.", "O CAMPO *GIRA* E ELE PERSEGUE.", ('F6',)),
        (26.8, 35.6, "UM *SENSOR* LÊ ONDE O ÍMÃ ESTÁ PARA", "SABER A HORA DE TROCAR.", ('F6',)),
    ],
    'inducao': [
        (0.5, 7.6, "NO MOTOR DE *INDUÇÃO*, O ROTOR É UMA", "GAIOLA DE BARRAS, SEM FIO LIGADO.", ('F7',)),
        (7.8, 15.6, "O CAMPO QUE GIRA *INDUZ CORRENTE*", "NAS BARRAS, E O ROTOR É PUXADO.", ('F7',)),
        (15.8, 22.6, "ELE VAI SEMPRE UM POUCO *ATRÁS*: NA", "MESMA VELOCIDADE, A FORÇA SUMIRIA.", ('F7',)),
        (22.8, 29.6, "ESSE ATRASO, O *ESCORREGAMENTO*,", "FICA EM TORNO DE *0,5% A 5%*.", ('F7',)),
    ],
    'casa': [
        (0.5, 6.8, "NUMA *VENTOINHA* DE COMPUTADOR, O", "MOTOR É SEMPRE *SEM ESCOVAS*.", ('F6',)),
        (7.0, 13.6, "OS ÍMÃS GIRAM COM AS PÁS, EM VOLTA", "DAS BOBINAS PARADAS NO MEIO.", ('F6',)),
        (14.2, 20.8, "EM MUITAS *MÁQUINAS DE LAVAR*, ELE", "GIRA O CESTO DIRETO.", ('F6',)),
        (21.0, 27.6, "SEM CORREIA E SEM CAIXA DE", "ENGRENAGENS: *TRAÇÃO DIRETA*.", ('F6',)),
        (28.2, 34.8, "MUITOS *CARROS ELÉTRICOS* USAM MOTORES", "ASSIM PARA MOVER AS RODAS.", ('F5', 'F6')),
        (35.0, 41.6, "A MAIORIA TEM CÂMBIO DE *1 MARCHA*", "E NÃO TEM EMBREAGEM.", ('F10',)),
    ],
    'eficiencia': [
        (0.5, 7.6, "NO MOTOR A GASOLINA, A MAIOR PARTE", "DA ENERGIA SE PERDE COMO *CALOR*.", ('F9',)),
        (7.8, 15.6, "CARRO A GASOLINA: SÓ *16% A 25%*", "DA ENERGIA CHEGA ÀS RODAS.", ('F13',)),
        (15.8, 22.6, "CARRO ELÉTRICO: *87% A 91%*, CONTANDO", "A ENERGIA QUE A FRENAGEM DEVOLVE.", ('F9',)),
        (22.8, 29.6, "SEM QUEIMA, SOBRAM PERDAS PEQUENAS:", "ATRITO E CALOR NOS FIOS E NO FERRO.", ('F7',)),
    ],
    'torque': [
        (0.5, 7.6, "E ELE JÁ TEM FORÇA *PARADO*: NESTE", "MOTOR, O TORQUE É MÁXIMO NO ZERO.", ('F4',)),
        (7.8, 15.6, "TORQUE É A FORÇA DE GIRO. QUANTO MAIS", "RÁPIDO ELE GIRA, *MENOS TORQUE* SOBRA.", ('F4',)),
        (15.8, 23.6, "NO CARRO ELÉTRICO, O TORQUE MÁXIMO", "JÁ VEM DO ZERO: *SAI FORTE NA LARGADA*.", ('F10',)),
    ],
    'historia': [
        (0.5, 5.8, "*1820*: OERSTED VÊ A CORRENTE", "MEXER NA BÚSSOLA.", ('F2',)),
        (6.0, 11.6, "*1821*: FARADAY TRANSFORMA A CORRENTE", "EM GIRO PELA PRIMEIRA VEZ.", ('F5',)),
        (11.8, 17.6, "*1832*: STURGEON, O MOTOR COM", "COMUTADOR QUE MOVE MÁQUINAS.", ('F5',)),
        (17.8, 23.6, "*1885 E 1887*: FERRARIS E TESLA", "MOSTRAM O CAMPO QUE GIRA.", ('F7',)),
    ],
    'trifasico': [
        (0.5, 7.6, "O FINAL NO RITMO: 3 BOBINAS, 3 FASES,", "*A, B E C*, UMA EM CADA BATIDA.", ()),
        (7.8, 15.6, "AS CORRENTES SOBEM E DESCEM, CADA", "UMA *1/3 DE CICLO* DEPOIS DA OUTRA.", ('F8',)),
        (15.8, 23.6, "JUNTAS, FAZEM UM CAMPO QUE *GIRA*", "LISO E SEMPRE DO MESMO TAMANHO.", ('F8',)),
        (23.8, 31.6, "NA REDE DO BRASIL: *60 CICLOS*", "*POR SEGUNDO*, 60 HZ.", ('F11',)),
        (31.8, 39.6, "COM 2 POLOS, O CAMPO DÁ 60 VOLTAS", "POR SEGUNDO: *3.600 RPM*.", ('F12',)),
    ],
    'resumo': [
        (0.5, 8.6, "ÍMÃS SE ATRAEM E SE EMPURRAM.", "A CORRENTE FAZ UM *ELETROÍMÃ*.", ('F1', 'F3')),
        (8.8, 17.6, "TROCAR A CORRENTE NA HORA CERTA DEIXA", "O ROTOR SEMPRE *PERSEGUINDO* O CAMPO.", ('F4', 'F6')),
        (17.8, 26.6, "ASSIM GIRAM A VENTOINHA, A MÁQUINA", "DE LAVAR E O *CARRO ELÉTRICO*.", ('F5', 'F6')),
    ],
}

FONTES = {
    'F1': ('LibreTexts, "Introduction to Physics (Park)", 10.2 Magnets',
           'https://phys.libretexts.org/Bookshelves/Conceptual_Physics/Introduction_to_Physics_(Park)/04%3A_Unit_3-_Classical_Physics_-_Thermodynamics_Electricity_and_Magnetism_and_Light/10%3A_Magnetism/10.02%3A_Magnets'),
    'F2': ('Wikipedia, "Hans Christian Ørsted"', 'https://en.wikipedia.org/wiki/Hans_Christian_%C3%98rsted'),
    'F3': ('Wikipedia, "Electromagnet"', 'https://en.wikipedia.org/wiki/Electromagnet'),
    'F4': ('Wikipedia, "Brushed DC electric motor"', 'https://en.wikipedia.org/wiki/Brushed_DC_electric_motor'),
    'F5': ('Wikipedia, "Electric motor"', 'https://en.wikipedia.org/wiki/Electric_motor'),
    'F6': ('Wikipedia, "Brushless DC electric motor"', 'https://en.wikipedia.org/wiki/Brushless_DC_electric_motor'),
    'F7': ('Wikipedia, "Induction motor"', 'https://en.wikipedia.org/wiki/Induction_motor'),
    'F8': ('Wikipedia, "Three-phase electric power"', 'https://en.wikipedia.org/wiki/Three-phase_electric_power'),
    'F9': ('Departamento de Energia dos EUA, "FOTW #1360: A Typical EV is 87%–91% Efficient Compared to 30% for a Conventional Gasoline Vehicle"',
           'https://www.energy.gov/node/4844725'),
    'F10': ('Wikipedia, "Electric car"', 'https://en.wikipedia.org/wiki/Electric_car'),
    'F11': ('Wikipedia, "Mains electricity by country"', 'https://en.wikipedia.org/wiki/Mains_electricity_by_country'),
    'F13': ('fueleconomy.gov (Departamento de Energia dos EUA), "Where the Energy Goes: Gasoline Vehicles"',
            'https://www.fueleconomy.gov/feg/atv.shtml'),
    'F12': ('Conta a partir de F11 e F7: 60 ciclos por segundo x 60 s = 3.600 RPM com 2 polos (1.800 com 4)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'imas': 'Ímãs: atrai e empurra', 'orsted': 'A corrente faz campo (1820)',
                'bobina': 'A bobina vira eletroímã', 'pecas': 'As peças de um motor simples',
                'dcmotor': 'O comutador: inverte a cada meia volta', 'batida': 'Um motor no ritmo da música',
                'escovas': 'O problema das escovas', 'brushless': 'O motor sem escovas',
                'inducao': 'O motor de indução', 'casa': 'Ventoinha, máquina de lavar e carro elétrico',
                'eficiencia': 'Por que ele é tão eficiente', 'torque': 'Força desde o zero',
                'historia': 'Um pouco de história', 'trifasico': 'As 3 fases no ritmo da música',
                'resumo': 'Resumo'}

DESCRICAO = """Como um motor elétrico transforma corrente em giro? A gente abre um motor (genérico, sem marca) e monta a ideia peça por peça: os ímãs que se atraem e se empurram, a corrente que cria um campo magnético (a descoberta de Oersted, em 1820), a bobina que vira eletroímã e o motor de corrente contínua com o comutador e as escovas, que invertem a corrente a cada meia volta. Depois o motor sem escovas, em que o controlador liga as bobinas em sequência e o ímã persegue o campo, e o motor de indução, em que o rotor vai sempre um pouco atrás.

O rotor tem um contador de voltas e um painel de RPM. Em dois trechos o motor anda no ritmo da música: a corrente inverte em cada batida e, no final, as três fases A, B e C batem uma em cada batida enquanto o campo gira.

Também: onde estão esses motores na casa (ventoinha, máquina de lavar, carro elétrico), por que o carro elétrico aproveita muito mais a energia do que o carro a gasolina e por que ele já tem força parado.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O motor de corrente contínua tem uma bobina só, vista de lado (em corte: os dois lados da bobina aparecem como dois fios, um com a corrente entrando na tela e outro saindo). Motores de verdade têm várias bobinas num núcleo de ferro e um comutador com muitos segmentos.
- O giro do motor de corrente contínua sai de uma conta simples (força proporcional ao cosseno do ângulo, mais atrito), não de medições de um motor real.
- No motor sem escovas, o controlador liga uma bobina de cada vez (3 passos por volta). Os controladores de verdade costumam ligar duas de cada vez (6 passos) ou usar correntes em forma de onda.
- No trifásico, mostramos o motor de 2 polos e o campo girando 1/3 de volta por batida; depois aceleramos até a velocidade da tomada só no texto e no borrão, já que 60 voltas por segundo não dá para ver.
- No motor de indução, a velocidade do rotor e o escorregamento do painel são um exemplo dentro da faixa de 0,5% a 5%; o campo da animação gira bem mais devagar que na vida real.
- Os 85% a 97% são a eficiência em plena carga de motores de indução; motores pequenos e baratos podem ser bem menos eficientes (os de polo sombreado ficam em 15% a 20%).
- Gasolina: 16% a 25% da energia chega às rodas no uso misto (o mesmo número do nosso vídeo do motor a combustão). Elétrico: 87% a 91%, contando a frenagem regenerativa. Ambos do Departamento de Energia dos EUA; dependem do trajeto.
- O gráfico de torque é o de um motor simples de ímã permanente. No carro elétrico, o controlador mantém o torque máximo quase constante até uma certa velocidade; só depois ele cai.

Fontes
{fontes}

#motoreletrico #comofunciona #pixelart #eletricidade #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O motor em corte
# fica centrado em x 140 (estator 60..220); o motor sem escovas, em 140; as
# grades da eficiência: no Short as duas se revezam em x 176..286.
PREFIXO = 'ep13-motor-eletrico'
CORTES = [
    dict(id='c1', de=('dcmotor', 0.0), ate=('dcmotor', 36.0), x=50, gancho=['POR QUE', 'ELE GIRA?'],
         titulo='Por que o motor elétrico não para de girar? ⚡',
         descricao='A corrente faz da bobina um ímã que é puxado pelo ímã de fora. Quando ela se alinha, o comutador inverte a corrente e os polos trocam: a cada meia volta.'),
    dict(id='c2', de=('batida', 0.0), ate=('batida', 24.0), x=50, gancho=['MOTOR NA', 'BATIDA'],
         titulo='Um motor elétrico no ritmo da música 🎵',
         descricao='A corrente inverte em cada batida: 2 inversões por volta, 2 batidas por segundo, 60 RPM. Depois dobra.'),
    dict(id='c3', de=('trifasico', 0.0), ate=('trifasico', 32.0), x=50, gancho=['A, B, C', 'NA BATIDA'],
         titulo='As 3 fases do motor no ritmo da música',
         descricao='Três bobinas, três correntes, cada uma 1/3 de ciclo depois da outra. Juntas fazem um campo que gira liso, e o ímã do meio vai atrás.'),
    dict(id='c4', de=('brushless', 0.0), ate=('brushless', 36.0), x=50, gancho=['SEM', 'ESCOVAS'],
         titulo='Como funciona o motor sem escovas (brushless)',
         descricao='O controlador liga as bobinas em sequência, A, B, C, e o ímã do rotor persegue o polo que acendeu. Um sensor lê a posição do ímã para saber a hora de trocar.'),
    dict(id='c5', de=('orsted', 0.0), ate=('orsted', 24.0), x=50, gancho=['A BÚSSOLA', 'SE MEXEU'],
         titulo='1820: a descoberta que levou ao motor elétrico 🧭',
         descricao='Oersted viu a agulha de uma bússola se mexer perto de um fio com corrente. A corrente cria um campo magnético em volta do fio; invertendo a corrente, as agulhas viram.'),
    dict(id='c6', de=('eficiencia', 3.0), ate=('eficiencia', 30.0), x=141, gancho=['25% CONTRA', '90%'],
         titulo='Carro elétrico x carro a gasolina: quem aproveita a energia? 🔋',
         descricao='Segundo o Departamento de Energia dos EUA, um carro elétrico típico é 87% a 91% eficiente (contando a frenagem regenerativa), contra 16% a 25% da energia que chega às rodas num carro a gasolina típico (uso misto).'),
]
