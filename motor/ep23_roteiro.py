#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep23 (série A JORNADA): A jornada de uma gota de chuva.

A ideia: seguir UMA molécula de água (a protagonista, um ponto que brilha com
rastro; quando vira gota, uma gota redonda que brilha, sem rosto) pelo ciclo
da água com sotaque brasileiro: evapora do Atlântico, sobe e esfria, gruda
num grão de sal e vira gotinha de nuvem, junta 1 milhão de gotinhas e vira
gota de chuva, cai na Amazônia, entra numa árvore e sai pela folha, viaja no
rio voador até o Sudeste, chove, desce o rio até a represa (ponte para o
ep11, "a jornada da água") e volta para o mar. Objetivo que sobe na tela:
"ETAPA 4 DE 9", altitude, temperatura, tamanho da gota e dias de viagem. O
desenho mora em `ep23_motor.py` (cenas) e `ep23_desenho.py` (paleta, gota,
molécula, céu, mar, nuvem, árvore, mapa, painel).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Ciclo da água movido pela energia do Sol; 86% da evaporação do planeta
      acontece sobre o oceano; os oceanos guardam ~97% da água; tempo médio
      de residência: atmosfera 9 dias, oceanos 3.200 anos, rios 2 a 6 meses,
      umidade do solo 1 a 2 meses, geleiras 20 a 100 anos, água subterrânea
      rasa 100 a 200 anos e funda 10.000 anos. Wikipedia, "Water cycle".
  F2  Ar subindo sem condensar esfria 9,8 °C/km (adiabática seca); depois de
      saturar, condensa, solta calor latente e esfria menos, tipicamente
      ~5 °C/km. Atmosfera-padrão (ICAO): 6,5 °C/km. Wikipedia, "Lapse rate".
  F3  Gotinha de nuvem média: ~20 micrômetros de diâmetro (0,02 mm); gota de
      chuva média: 2 mm; são precisas 1 milhão de gotinhas (raio 10 µm)
      para uma gota de chuva; o vapor precisa de núcleos de condensação
      (sal marinho é dos maiores); colisão e coalescência: as maiores caem
      mais rápido e recolhem as menores. Univ. do Havaí, "Atmospheric
      Processes and Phenomena", cap. 7.
  F4  Gotas pequenas (raio < 1 mm) são esféricas; maiores têm forma de pão de
      hambúrguer; grandes demais se deformam e se partem. USGS Water Science
      School, "Raindrops are Different Shapes".
  F5  A água se junta em partículas de poeira e fumaça nas nuvens; a tensão
      superficial deixa a gota redonda; caindo, vira "a metade de cima de um
      pão de hambúrguer"; grande demais, se parte. NASA GPM, "The Shape of a
      Raindrop".
  F6  Núcleos de condensação: poeira, gelo e sal. Wikipedia, "Rain".
  F7  Gota de 2 mm: velocidade terminal de 6,5 m/s. J. M. Viñas
      (divulgameteo), "Velocidad terminal de gotas y granizos".
  F8  Gotinha de nuvem (raio 10 µm): ~1 cm/s. The Weather Guys (Univ. de
      Wisconsin-Madison, SSEC), "How fast do raindrops fall?".
  F9  Rios voadores: cursos de água atmosféricos; a umidade evaporada no
      Atlântico chega levada pelos ventos alísios; uma árvore grande (copa de
      20 m) transpira bem mais de 1.000 litros por dia (estudos do INPA); os
      Andes (4.000 m) são uma barreira; o vapor segue para o Centro-Oeste,
      Sudeste e Sul. Projeto Rios Voadores, "Fenômeno dos rios voadores".
  F10 A floresta solta ~20 bilhões de toneladas de água por dia (cálculo de
      Antonio Nobre, INPE); o rio Amazonas despeja ~17 bilhões por dia no
      Atlântico. Projeto Rios Voadores, "The Flying Rivers Phenomenon".
  F11 Transpiração: a água entra pela raiz, sobe pelo xilema e sai pelos
      estômatos; 97% a 99,5% da água absorvida sai assim. Wikipedia,
      "Transpiration".
  F12 Conta (F7, F8): 6,5 m/s x 3,6 = 23 km/h; 1.000 m / 6,5 m/s = 154 s
      (~2,5 min); 1.000 m / 0,01 m/s = 100.000 s = 28 h (mais de 1 dia).
  F13 Conta (F3): 2 mm / 0,02 mm = 100 vezes mais larga; 100 x 100 x 100 =
      1 milhão de vezes mais água.
  F14 Conta (F2): exemplo com 25 °C no nível do mar; a 1 km, 25 - 9,8 = 15 °C;
      acima, ~5 °C a menos por km.
  F16 Nuvem de 1 km cúbico com 0,5 g de água por m cúbico: ~500.000 kg; o ar da nuvem é
      menos denso que o ar seco. USGS, "How Much Does a Cloud Weigh?".
  F17 Gotinhas pequenas são seguras pela circulação do ar; grandes e pesadas
      demais, caem como chuva. Wikipedia, "Cloud".
  F15 Na hidrelétrica, a água represada move a turbina e o gerador.
      Wikipedia, "Hydroelectricity" (o mesmo do ep11).
"""

TITULO = "A jornada de uma gota de chuva | O ciclo da água e os rios voadores em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='oceano', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='subida', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='nucleo', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='flutua', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='colisao', gen='synthwave', bars=15, papel='drop'),    # 36 s
    dict(id='queda', gen='lofi', bars=14, papel='drop'),           # 42 s
    dict(id='floresta', gen='lofi', bars=16, papel='drop'),        # 48 s
    dict(id='rios', gen='synthwave', bars=20, papel='drop'),       # 48 s
    dict(id='sudeste', gen='lofi', bars=14, papel='drop'),         # 42 s
    dict(id='mar', gen='lofi', bars=12, papel='drop'),             # 36 s
    dict(id='tempo', gen='lofi', bars=10, papel='break'),          # 30 s
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),           # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 5.8, "ESTA GOTA DE CHUVA JÁ FOI MAR,", "NUVEM E ATÉ *PARTE DE UMA ÁRVORE*.", ()),
        (6.0, 11.8, "VAMOS SEGUIR *UMA GOTA* PELO", "CAMINHO INTEIRO DA ÁGUA.", ()),
    ],
    'oceano': [
        (0.5, 6.5, "ETAPA 1: O *OCEANO ATLÂNTICO*,", "PERTO DA COSTA DO BRASIL.", ()),
        (6.7, 12.9, "O *SOL* ESQUENTA A ÁGUA. A NOSSA", "MOLÉCULA SE AGITA MAIS E MAIS...", ('F1',)),
        (13.1, 19.3, "...ATÉ ESCAPAR DA SUPERFÍCIE:", "ELA *EVAPOROU*. VIROU VAPOR.", ('F1',)),
        (19.5, 25.7, "O VAPOR D'ÁGUA É *INVISÍVEL*.", "A GENTE PINTOU PARA VOCÊ VER.", ()),
        (25.9, 31.7, "*86%* DE TODA A EVAPORAÇÃO DA TERRA", "ACONTECE SOBRE OS OCEANOS.", ('F1',)),
        (31.9, 35.9, "E OS OCEANOS GUARDAM *97%*", "DA ÁGUA DO PLANETA.", ('F1',)),
    ],
    'subida': [
        (0.5, 6.5, "ETAPA 2: OS *VENTOS ALÍSIOS*", "EMPURRAM O VAPOR PARA O CONTINENTE.", ('F9',)),
        (6.7, 12.9, "O AR QUENTE E ÚMIDO É LEVE:", "ELE *SOBE*.", ()),
        (13.1, 19.3, "LÁ EM CIMA A PRESSÃO É MENOR:", "O AR SE EXPANDE E *ESFRIA*.", ('F2',)),
        (19.5, 25.7, "AR SUBINDO SEM NUVEM ESFRIA UNS", "*10 °C A CADA 1 KM*.", ('F2',)),
        (25.9, 31.7, "NESTE EXEMPLO, A 1 KM O AR JÁ ESTÁ", "A *15 °C*: FRIO DEMAIS PARA O VAPOR.", ('F14',)),
        (31.9, 35.9, "O VAPOR VAI VIRAR", "*ÁGUA LÍQUIDA* DE NOVO.", ('F2',)),
    ],
    'nucleo': [
        (0.5, 6.5, "ETAPA 3: O VAPOR PRECISA DE UM", "*NÚCLEO* PARA VIRAR GOTINHA.", ('F3',)),
        (6.7, 12.9, "SOBRE O MAR, MUITOS NÚCLEOS SÃO", "GRÃOS DE *SAL MARINHO* NO AR.", ('F3',)),
        (13.1, 19.3, "POEIRA E FUMAÇA TAMBÉM SERVEM.", "A NOSSA MOLÉCULA *GRUDOU* NUM SAL.", ('F5', 'F6')),
        (19.5, 25.7, "NASCEU UMA *GOTINHA DE NUVEM*:", "UNS *0,02 MM*. MINÚSCULA.", ('F3',)),
        (25.9, 31.7, "AO CONDENSAR, O VAPOR *SOLTA CALOR*.", "O AR SEGUE SUBINDO, MAIS DEVAGAR.", ('F2',)),
        (31.9, 35.9, "JUNTAS, AS GOTINHAS", "FORMAM A *NUVEM*.", ('F3',)),
    ],
    'flutua': [
        (0.5, 6.5, "SE A NUVEM É FEITA DE ÁGUA,", "POR QUE ELA *NÃO CAI*?", ()),
        (6.7, 12.9, "UMA NUVEM DE 1 KM DE LADO TEM UNS", "*500.000 KG* DE ÁGUA.", ('F16',)),
        (13.1, 19.3, "MAS ESSA ÁGUA ESTÁ ESPALHADA: SÓ", "*MEIO GRAMA* POR METRO CÚBICO.", ('F16',)),
        (19.5, 25.7, "CADA GOTINHA CAI A ~1 CM/S, E O AR", "QUE SOBE *SEGURA* AS GOTINHAS NO ALTO.", ('F8', 'F17')),
        (25.9, 31.7, "E O AR ÚMIDO DA NUVEM É *MENOS*", "*DENSO* QUE O AR SECO EM VOLTA.", ('F16',)),
        (31.9, 35.9, "ATÉ A GOTA FICAR GRANDE", "E PESADA DEMAIS...", ('F17',)),
    ],
    'colisao': [
        (0.5, 6.5, "ETAPA 4: GOTINHAS DE NUVEM SÃO TÃO", "LEVES QUE QUASE NÃO CAEM: *1 CM/S*.", ('F8',)),
        (6.7, 12.9, "MAS ELAS SE *CHOCAM* E SE JUNTAM.", "É A *COALESCÊNCIA*.", ('F3',)),
        (13.1, 19.3, "A GOTA MAIOR CAI MAIS RÁPIDO E", "VAI *ENGOLINDO* AS MENORES.", ('F3',)),
        (19.5, 25.7, "UMA GOTA DE CHUVA DE *2 MM* LEVA", "*1 MILHÃO* DE GOTINHAS DE NUVEM.", ('F3',)),
        (25.9, 31.7, "ELA É 100 VEZES MAIS LARGA, ENTÃO", "TEM 100 X 100 X 100 VEZES MAIS ÁGUA.", ('F13',)),
        (31.9, 35.9, "PESADA, A NOSSA GOTA", "FINALMENTE *CAI*.", ()),
    ],
    'queda': [
        (0.5, 6.5, "ETAPA 5: A QUEDA. E A GOTA *NÃO*", "*TEM FORMA DE LÁGRIMA*!", ('F4',)),
        (6.7, 12.9, "GOTAS PEQUENAS SÃO *REDONDAS*:", "A TENSÃO DA SUPERFÍCIE AS SEGURA.", ('F4', 'F5')),
        (13.1, 19.3, "AS MAIORES ACHATAM POR BAIXO,", "COMO UM *PÃO DE HAMBÚRGUER*.", ('F4', 'F5')),
        (19.5, 25.7, "E AS GRANDES DEMAIS O AR *RASGA*", "EM GOTAS MENORES.", ('F4', 'F5')),
        (25.9, 31.7, "A NOSSA, DE 2 MM, CAI A *6,5 M/S*:", "UNS *23 KM/H*.", ('F7', 'F12')),
        (31.9, 37.7, "1 KM DE QUEDA: UNS *2,5 MINUTOS*.", "UMA GOTINHA DE NUVEM: MAIS DE 1 DIA.", ('F8', 'F12')),
        (37.9, 41.9, "LÁ EMBAIXO:", "A *FLORESTA AMAZÔNICA*.", ()),
    ],
    'floresta': [
        (0.5, 6.5, "ETAPA 6: A GOTA BATE NAS FOLHAS", "E PINGA ATÉ O *CHÃO*.", ()),
        (6.7, 12.9, "ELA ENTRA NO SOLO, E UMA *RAIZ*", "PUXA A ÁGUA PARA DENTRO DA ÁRVORE.", ('F11',)),
        (13.1, 19.3, "POR TUBOS FININHOS NO TRONCO, O", "*XILEMA*, ELA SOBE ATÉ AS FOLHAS.", ('F11',)),
        (19.5, 25.7, "NA FOLHA HÁ POROS MINÚSCULOS:", "OS *ESTÔMATOS*. ELES SE ABREM...", ('F11',)),
        (25.9, 31.7, "...E A NOSSA MOLÉCULA SAI", "COMO *VAPOR* DE NOVO.", ('F11',)),
        (31.9, 37.7, "DA ÁGUA QUE A RAIZ PUXA, *97% A 99,5%*", "SAI ASSIM. É A *TRANSPIRAÇÃO*.", ('F11',)),
        (37.9, 43.7, "UMA ÁRVORE GRANDE TRANSPIRA", "*MAIS DE 1.000 LITROS* POR DIA.", ('F9',)),
        (43.9, 47.9, "A FLORESTA INTEIRA SOLTA VAPOR", "NO CÉU, SEM PARAR.", ('F9',)),
    ],
    'rios': [
        (0.5, 6.5, "ETAPA 7: ESSE VAPOR SEGUE NO VENTO.", "É UM *RIO VOADOR*.", ('F9',)),
        (6.7, 12.9, "O VENTO TRAZ UMIDADE DO *ATLÂNTICO*", "E A FLORESTA DEVOLVE O VAPOR AO AR.", ('F9',)),
        (13.1, 19.3, "ELE CORRE PARA O OESTE ATÉ OS", "*ANDES*: UMA PAREDE DE 4.000 M.", ('F9',)),
        (19.5, 25.7, "AÍ O RIO VOADOR *VIRA PARA O SUL*,", "RUMO AO CENTRO-OESTE E AO SUDESTE.", ('F9',)),
        (25.9, 32.5, "A FLORESTA SOLTA UNS *20 BILHÕES DE*", "*TONELADAS* DE ÁGUA POR DIA.", ('F10',)),
        (32.7, 39.3, "O RIO AMAZONAS DESPEJA NO MAR UNS", "17 BILHÕES. O DO CÉU É *MAIOR*!", ('F10',)),
        (39.5, 47.8, "E A NOSSA MOLÉCULA VAI JUNTO,", "ATÉ O *SUDESTE* DO BRASIL.", ('F9',)),
    ],
    'sudeste': [
        (0.5, 6.5, "ETAPA 8: NO *SUDESTE*, O AR SOBE,", "ESFRIA, E O VAPOR VIRA NUVEM.", ('F2', 'F9')),
        (6.7, 12.9, "NÚCLEO, GOTINHA, 1 MILHÃO DE", "COLISÕES... E *CHOVE* DE NOVO.", ('F3',)),
        (13.1, 19.3, "A NOSSA GOTA CAI NUM MORRO", "E ESCORRE ATÉ UM *CÓRREGO*.", ()),
        (19.5, 25.7, "O CÓRREGO DESÁGUA NUM *RIO*,", "E O RIO ENCHE UMA *REPRESA*.", ()),
        (25.9, 32.5, "ALI ELA PODE GIRAR UMA TURBINA", "E VIRAR A *LUZ* DA SUA CASA.", ('F15',)),
        (32.7, 41.8, "ESSA PARTE DA VIAGEM ESTÁ NO", "*EPISÓDIO DA ÁGUA*. A JORNADA SEGUE!", ()),
    ],
    'mar': [
        (0.5, 6.5, "ETAPA 9: DEPOIS DA REPRESA, O RIO", "SEGUE ATÉ O *MAR*.", ()),
        (6.7, 12.9, "NUM RIO, A ÁGUA FICA EM MÉDIA", "DE *2 A 6 MESES*.", ('F1',)),
        (13.1, 19.3, "A NOSSA GOTA CHEGA AO", "*OCEANO ATLÂNTICO*.", ()),
        (19.5, 25.7, "AQUI ELA PODE FICAR, EM MÉDIA,", "*3.200 ANOS* ATÉ SAIR DE NOVO.", ('F1',)),
        (25.9, 31.7, "OU O SOL ESQUENTA A ÁGUA AMANHÃ", "E ELA *EVAPORA* OUTRA VEZ.", ('F1',)),
        (31.9, 35.9, "A NOSSA GOTA", "*VOLTOU PARA CASA*.", ()),
    ],
    'tempo': [
        (0.5, 6.5, "QUANTO TEMPO A ÁGUA FICA EM CADA", "LUGAR? É O *TEMPO DE RESIDÊNCIA*.", ('F1',)),
        (6.7, 12.9, "NO AR: SÓ *9 DIAS*. NO SOLO: 1 A 2", "MESES. NOS RIOS: 2 A 6 MESES.", ('F1',)),
        (13.1, 19.3, "NAS GELEIRAS: *20 A 100 ANOS*.", "NO OCEANO: *3.200 ANOS*.", ('F1',)),
        (19.5, 25.7, "NA ÁGUA SUBTERRÂNEA FUNDA:", "ATÉ *10.000 ANOS*.", ('F1',)),
        (25.9, 29.9, "O AR É O *ATALHO MAIS RÁPIDO*", "DO CICLO DA ÁGUA.", ('F1',)),
    ],
    'resumo': [
        (0.5, 6.5, "1 EVAPORA, 2 SOBE E ESFRIA,", "3 GRUDA NUM SAL, 4 JUNTA 1 MILHÃO.", ('F1', 'F2', 'F3')),
        (6.7, 13.5, "5 CAI A 23 KM/H, 6 A ÁRVORE PUXA", "E TRANSPIRA, 7 VOA NO RIO VOADOR...", ('F11', 'F12', 'F9')),
        (13.7, 20.5, "8 CHOVE NO SUDESTE, 9 E O RIO", "A LEVA DE VOLTA PARA O MAR.", ()),
        (20.7, 26.6, "E A *JORNADA RECOMEÇA*.", "", ()),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Water cycle" (tabela de tempos de residência; 86% da evaporação sobre o oceano)',
           'https://en.wikipedia.org/wiki/Water_cycle'),
    'F2': ('Wikipedia, "Lapse rate" (9,8 °C/km seco; ~5 °C/km úmido; calor latente)',
           'https://en.wikipedia.org/wiki/Lapse_rate'),
    'F3': ('University of Hawaii, "Atmospheric Processes and Phenomena", cap. 7 (Precipitation Processes)',
           'https://pressbooks-dev.oer.hawaii.edu/atmo/chapter/chapter-7-precipitation-processes/'),
    'F4': ('USGS Water Science School, "Raindrops are Different Shapes"',
           'https://www.usgs.gov/water-science-school/science/are-raindrops-shaped-teardrops'),
    'F5': ('NASA GPM, "The Shape of a Raindrop"',
           'https://gpm.nasa.gov/resources/students-and-educators/the-shape-of-a-raindrop'),
    'F6': ('Wikipedia, "Rain"', 'https://en.wikipedia.org/wiki/Rain'),
    'F7': ('José Miguel Viñas (divulgameteo), "Velocidad terminal de gotas y granizos": gota de 2 mm a 6,5 m/s',
           'https://www.divulgameteo.es/archivos/articulos/misarticulos/Velocidad%20terminal-gotas-granizos.pdf'),
    'F8': ('The Weather Guys (Univ. de Wisconsin-Madison, SSEC), "How fast do raindrops fall?"',
           'https://wxguys.ssec.wisc.edu/?p=581'),
    'F9': ('Projeto Rios Voadores, "Fenômeno dos rios voadores"',
           'https://riosvoadores.com.br/o-projeto/fenomeno-dos-rios-voadores/'),
    'F10': ('Projeto Rios Voadores, "The Flying Rivers Phenomenon" (cálculo de Antonio Nobre, INPE)',
            'https://riosvoadores.com.br/?p=583'),
    'F11': ('Wikipedia, "Transpiration"', 'https://en.wikipedia.org/wiki/Transpiration'),
    'F12': ('Conta a partir de F7 e F8: 6,5 m/s x 3,6 = 23 km/h; 1.000 m / 6,5 m/s = 154 s; 1.000 m / 0,01 m/s = 28 h', None),
    'F13': ('Conta a partir de F3: 2 mm / 0,02 mm = 100; 100 x 100 x 100 = 1.000.000', None),
    'F14': ('Conta a partir de F2: exemplo com 25 °C no nível do mar; 25 - 9,8 = 15 °C a 1 km', None),
    'F15': ('Wikipedia, "Hydroelectricity"', 'https://en.wikipedia.org/wiki/Hydroelectricity'),
    'F16': ('USGS Water Science School, "How Much Does a Cloud Weigh?" (1 km cúbico, 0,5 g por m cúbico, ~500.000 kg; menos denso que o ar seco)',
            'https://www.usgs.gov/water-science-school/science/how-much-does-a-cloud-weigh'),
    'F17': ('Wikipedia, "Cloud" (gotinhas seguras pela circulação do ar; grandes e pesadas demais, caem como chuva)',
            'https://en.wikipedia.org/wiki/Cloud'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'oceano': 'Etapa 1: a evaporação no Atlântico',
                'subida': 'Etapa 2: o ar sobe e esfria', 'nucleo': 'Etapa 3: o núcleo de sal e a gotinha',
                'flutua': 'Por que a nuvem não cai?',
                'colisao': 'Etapa 4: 1 milhão de gotinhas', 'queda': 'Etapa 5: a queda (e a forma da gota)',
                'floresta': 'Etapa 6: dentro de uma árvore da Amazônia', 'rios': 'Etapa 7: o rio voador',
                'sudeste': 'Etapa 8: chuva no Sudeste e a represa', 'mar': 'Etapa 9: de volta ao mar',
                'tempo': 'Quanto tempo a água fica em cada lugar', 'resumo': 'Resumo'}

DESCRICAO = """Por onde passa uma gota de chuva antes de cair na sua cidade? Neste vídeo a gente segue UMA molécula de água: o Sol a faz evaporar do Oceano Atlântico, o ar sobe e esfria, ela gruda num grãozinho de sal e vira gotinha de nuvem (e a gente mostra por que uma nuvem de 500 toneladas não cai), se junta com um milhão de outras e vira gota de chuva. A gota cai na Amazônia (e não tem forma de lágrima!), entra numa árvore pela raiz, sai pela folha como vapor e viaja num rio voador até o Sudeste. Lá ela chove de novo, desce o rio, passa pela represa e volta para o mar.

Um painel mostra a etapa (de 1 a 9), a altitude, a temperatura, o tamanho da gota e os dias de viagem.

Cada quadro é pixel art desenhada por código, e a música é original. A parte da represa até a tomada da sua casa está no nosso episódio "A jornada da água".

Capítulos
{capitulos}

Simplificado de propósito
- A molécula, a gotinha e a gota estão fora de escala: uma gota de 2 mm tem 100 vezes a largura de uma gotinha de nuvem, e as moléculas são bilhões de vezes menores do que aparecem.
- A nuvem de 500.000 kg é o exemplo do USGS (1 km cúbico com 0,5 g de água por metro cúbico); cada nuvem tem a sua quantidade de água.
- O vapor d'água é invisível; pintamos o vapor e o rio voador para você ver o caminho.
- As temperaturas são um exemplo: 25 °C no nível do mar, esfriando 9,8 °C por km até a base da nuvem (1 km neste exemplo) e cerca de 5 °C por km dentro dela. No mundo real a base da nuvem e as temperaturas mudam todo dia.
- O contador de dias é ilustrativo: ele segue as médias (cerca de 9 dias no ar, meses no rio), mas uma molécula de verdade pode levar de horas a anos em cada etapa. Também mostramos poucas colisões; para uma gota de 2 mm são cerca de 1 milhão.
- A gota de chuva pode crescer de outros jeitos (com gelo, nas nuvens altas); aqui mostramos só a colisão e coalescência, que é o caminho das nuvens quentes dos trópicos.
- No mapa, a costa, a Amazônia e os Andes são desenhados à mão, sem escala exata, e o rio voador é um caminho típico, não o de um dia específico.
- A árvore aparece em corte, com um tubo de xilema; de verdade são milhares de tubos microscópicos.

Fontes
{fontes}

#ciclodaagua #riosvoadores #amazonia #chuva #comofunciona #pixelart #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. As cenas centram
# o protagonista em x ~146 (recorte 56..236); no mapa do rio voador e no
# gráfico do tempo o desenho muda de arranjo quando VERTICAL = True.
PREFIXO = 'ep23-gota'
CORTES = [
    dict(id='c1', de=('queda', 0.0), ate=('queda', 31.7), x=56, gancho=['GOTA NÃO É', 'LÁGRIMA!'],
         titulo='Gota de chuva não tem forma de lágrima 💧',
         descricao='Gotas pequenas são redondas; as maiores achatam por baixo como um pão de hambúrguer, e as grandes demais se partem. Uma gota de 2 mm cai a uns 6,5 m/s (USGS, NASA GPM).'),
    dict(id='c2', de=('colisao', 0.0), ate=('colisao', 31.7), x=56, gancho=['1 MILHÃO', 'DE GOTINHAS'],
         titulo='Quantas gotinhas de nuvem fazem uma gota de chuva? ☁️',
         descricao='Gotinhas de nuvem têm uns 0,02 mm e quase não caem. Elas se chocam e se juntam: uma gota de chuva de 2 mm leva cerca de 1 milhão delas.'),
    dict(id='c3', de=('rios', 13.1), ate=('rios', 47.8), x=56, gancho=['O RIO QUE', 'VOA'],
         titulo='Os rios voadores da Amazônia 🌳☁️',
         descricao='O vapor que a floresta solta viaja no vento para o oeste, bate nos Andes e vira para o sul, levando chuva ao Centro-Oeste, Sudeste e Sul do Brasil (Projeto Rios Voadores).'),
    dict(id='c4', de=('floresta', 6.7), ate=('floresta', 43.7), x=56, gancho=['A ÁRVORE', 'QUE SUA'],
         titulo='Uma árvore da Amazônia transpira mais de 1.000 litros por dia 🌳',
         descricao='A raiz puxa a água, ela sobe pelo xilema e sai pelos estômatos das folhas como vapor. Uma árvore grande transpira mais de 1.000 litros por dia (estudos do INPA).'),
    dict(id='c5', de=('nucleo', 0.0), ate=('nucleo', 31.7), x=56, gancho=['NUVEM NASCE', 'DO SAL'],
         titulo='Toda gotinha de nuvem tem um grão no meio 🧂',
         descricao='O vapor precisa de um núcleo para virar gota: sobre o mar, muitos são grãos de sal marinho. Poeira e fumaça também servem.'),
    dict(id='c6', de=('tempo', 0.0), ate=('tempo', 29.9), x=56, gancho=['9 DIAS NO AR', '3.200 NO MAR'],
         titulo='Quanto tempo a água fica no ar, no rio e no mar? 🌊',
         descricao='Em média: 9 dias na atmosfera, 2 a 6 meses nos rios, 3.200 anos nos oceanos e até 10.000 anos na água subterrânea funda.'),
]
