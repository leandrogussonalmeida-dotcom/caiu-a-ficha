#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep04 (série FEITO DE PIXELS): Como a tela do celular faz cada pixel.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep04_motor.py` e `ep04_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 29/10/2026)
  F1  Um pixel de tela colorida é feito de subpixels; nas telas LCD eles ficam
      em listras verticais. Wikipedia, "Pixel geometry".
  F2  Vermelho + verde = amarelo; azul + verde = ciano; vermelho + azul =
      magenta; os três = branco; nenhum = preto. UCSB, "Additive Color".
  F3  RGB é usado em aparelhos digitais (TV, computador); vermelho + verde em
      partes iguais = amarelo; os três = branco. Britannica, "primary color".
  F4  LCD: o cristal líquido não emite luz, usa luz de fundo; dois filtros
      polarizadores em geral perpendiculares; sem tensão a luz passa pela camada
      torcida 90 graus; com tensão, proporcional, as moléculas destorcem e
      bloqueiam; filtros de cor fazem os subpixels R, G, B; o preto pode não sair
      tão escuro porque o cristal não bloqueia toda a luz de fundo.
      Wikipedia, "Liquid-crystal display".
  F5  OLED: a camada orgânica emite luz quando passa corrente; não precisa de luz
      de fundo; cada pixel faz a própria luz; o elemento apagado não produz luz
      nem gasta energia ("true blacks"); usado em celulares. Wikipedia, "OLED".
  F6  Uma tela FHD em 20:9 tem 2400 x 1080 (exemplo de celular). 9to5Google.
  F7  1.080 x 2.400 = 2.592.000 pixels; x 3 = 7.776.000 subpixels;
      diagonal = raiz(1.080² + 2.400²) = 2.631,8 pixels. (conta a partir de F6)
  F8  PPI = diagonal em pixels / diagonal em polegadas. Wikipedia, "Pixel density".
      2.631,8 / 6,5 = 404,9 ppi; / 25,4 mm = 15,9 pixels por mm. (conta)
  F9  60 Hz = 60 vezes por segundo, 120 Hz = 120; 120 Hz já é comum nos
      celulares. Android Authority.
  F10 1 s / 60 = 16,7 ms; 1 s / 120 = 8,3 ms; 2.592.000 x 120 = 311.040.000. (conta)
  F11 24 bits = 8 bits para cada um de R, G e B; 2^24 = 16.777.216 cores.
      2^8 = 256 níveis. Wikipedia, "Color depth".
  F12 Este vídeo: desenhado em 480 x 270, ampliado 4x por vizinho mais próximo
      para 1.920 x 1.080, a 30 quadros por segundo (longo.py: W, H, ESC, FPS).
  F13 Pontinhos de luz R, G, B vistos da distância normal parecem uma cor só.
      Wikipedia, "Additive color".
  F14 Taxa adaptativa: o celular ajusta a taxa de atualização sozinho conforme o
      que está na tela. Tom's Guide.
"""

TITULO = "Como a tela do celular faz cada pixel | LCD, OLED e subpixels em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),           # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),           # 6 s
    dict(id='zoom', gen='lofi', bars=12, papel='drop'),             # 36 s
    dict(id='subpixel', gen='lofi', bars=8, papel='drop'),          # 24 s
    dict(id='cores', gen='synthwave', bars=18, papel='drop'),       # 43,2 s
    dict(id='foto', gen='lofi', bars=11, papel='drop'),             # 33 s
    dict(id='lcd', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='cristal', gen='lofi', bars=14, papel='drop'),          # 42 s
    dict(id='preto', gen='lofi', bars=6, papel='break'),            # 18 s
    dict(id='oled', gen='lofi', bars=16, papel='drop'),             # 48 s
    dict(id='resolucao', gen='synthwave', bars=18, papel='drop'),   # 43,2 s
    dict(id='densidade', gen='lofi', bars=8, papel='break'),        # 24 s
    dict(id='hz', gen='house', bars=22, papel='drop', bpm=120),     # 44 s
    dict(id='meta', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),            # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),              # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "TUDO NA TELA DO CELULAR É FEITO", "DE PONTINHOS DE LUZ: OS *PIXELS*.", ('F1',)),
        (6.2, 11.6, "DE PERTO, CADA UM É FEITO DE", "*VERMELHO*, *VERDE* E *AZUL*.", ('F1',)),
    ],
    'zoom': [
        (0.8, 7.6, "UM CELULAR QUALQUER, MOSTRANDO", "UMA PAISAGEM.", ()),
        (8.0, 15.4, "VAMOS CHEGAR PERTO DE UM PONTO", "DO *SOL*.", ()),
        (15.8, 23.4, "A IMAGEM VIRA UMA GRADE DE", "QUADRADINHOS: OS *PIXELS*.", ('F1',)),
        (23.8, 29.6, "MAIS PERTO AINDA: CADA PIXEL TEM", "*3 SUBPIXELS*, LADO A LADO.", ('F1',)),
        (30.0, 35.6, "NESTE PIXEL AMARELO, SÓ O *VERMELHO*", "E O *VERDE* ESTÃO ACESOS.", ('F2',)),
    ],
    'subpixel': [
        (0.5, 7.6, "CADA SUBPIXEL É UMA LUZ COM BRILHO", "PRÓPRIO, DE APAGADO ATÉ O MÁXIMO.", ('F4',)),
        (8.0, 15.6, "NO PADRÃO DE 24 BITS: *256 NÍVEIS*", "PARA CADA SUBPIXEL.", ('F11',)),
        (16.0, 23.6, "256 X 256 X 256 =", "*16.777.216 CORES* POSSÍVEIS.", ('F11',)),
    ],
    'cores': [
        (0.5, 7.4, "SÓ 3 CORES DE LUZ. E AS OUTRAS?", "SAEM *SOMANDO* LUZ.", ('F2',)),
        (7.8, 14.8, "*VERMELHO + VERDE = AMARELO*.", "", ('F2', 'F3')),
        (15.2, 22.2, "*VERDE + AZUL = CIANO*.", "", ('F2',)),
        (22.6, 29.6, "*VERMELHO + AZUL = MAGENTA*.", "", ('F2',)),
        (30.0, 36.6, "AS TRÊS JUNTAS: *BRANCO*.", "NENHUMA ACESA: PRETO.", ('F2', 'F3')),
        (37.0, 43.0, "OS SUBPIXELS SÃO TÃO PEQUENOS QUE", "O OLHO VÊ UMA COR SÓ.", ('F13',)),
    ],
    'foto': [
        (0.5, 7.4, "AGORA A FOTO INTEIRA: CADA PIXEL", "TEM A SUA RECEITA DE 3 LUZES.", ('F2',)),
        (7.8, 14.8, "CÉU: MUITO *AZUL* E UM POUCO DE", "VERDE.", ('F2',)),
        (15.2, 22.2, "NEVE: OS TRÊS NO MÁXIMO.", "RESULTADO: *BRANCO*.", ('F2',)),
        (22.6, 28.4, "LAGO: *VERDE + AZUL*, QUE DÁ CIANO.", "", ('F2',)),
        (28.6, 32.8, "E O SOL, NOSSO PIXEL: *AMARELO*.", "", ('F2',)),
    ],
    'lcd': [
        (0.5, 5.8, "PRIMEIRO TIPO: *LCD*, A TELA DE", "CRISTAL LÍQUIDO. ABRINDO UM PIXEL:", ('F4',)),
        (6.2, 11.8, "O CRISTAL NÃO BRILHA SOZINHO. A LUZ", "VEM DE TRÁS: A *LUZ DE FUNDO*.", ('F4',)),
        (12.2, 17.8, "UM *POLARIZADOR*: SÓ DEIXA PASSAR", "A LUZ QUE VIBRA EM PÉ.", ('F4',)),
        (18.2, 23.8, "O *CRISTAL LÍQUIDO*: MOLÉCULAS EM", "ESPIRAL, ENTRE DOIS VIDROS.", ('F4',)),
        (24.2, 29.8, "OUTRO *POLARIZADOR*, VIRADO", "90 GRAUS EM RELAÇÃO AO PRIMEIRO.", ('F4',)),
        (30.2, 35.8, "E O *FILTRO DE COR*: VERMELHO, VERDE", "OU AZUL, UM PARA CADA SUBPIXEL.", ('F4',)),
    ],
    'cristal': [
        (0.5, 7.6, "SEM TENSÃO, A ESPIRAL GIRA A LUZ", "EM *90 GRAUS*...", ('F4',)),
        (8.0, 14.8, "...E ELA PASSA PELO SEGUNDO", "POLARIZADOR: *SUBPIXEL ACESO*.", ('F4',)),
        (15.2, 22.4, "COM TENSÃO, AS MOLÉCULAS *DESTORCEM*", "E NÃO GIRAM MAIS A LUZ.", ('F4',)),
        (22.8, 29.6, "A LUZ BATE NO SEGUNDO POLARIZADOR", "E PARA: *SUBPIXEL APAGADO*.", ('F4',)),
        (30.0, 35.8, "TENSÃO NO MEIO: PASSA SÓ UMA PARTE.", "É ASSIM QUE SAEM OS NÍVEIS.", ('F4',)),
        (36.2, 41.8, "VERMELHO E VERDE ABERTOS, AZUL", "FECHADO: O PIXEL FICA *AMARELO*.", ('F2', 'F4')),
    ],
    'preto': [
        (0.5, 8.0, "E O PRETO? TENSÃO NOS TRÊS. MAS A", "LUZ DE FUNDO CONTINUA LIGADA...", ('F4',)),
        (8.4, 16.4, "...E UM POUCO DELA ESCAPA. O PRETO", "DO LCD SAI *QUASE PRETO*.", ('F4',)),
    ],
    'oled': [
        (0.5, 7.6, "SEGUNDO TIPO: *OLED*. AQUI CADA", "SUBPIXEL *FAZ A PRÓPRIA LUZ*.", ('F5',)),
        (8.0, 15.4, "UMA CAMADA ORGÂNICA BRILHA QUANDO", "A CORRENTE PASSA POR ELA.", ('F5',)),
        (15.8, 22.8, "NÃO PRECISA DE LUZ DE FUNDO", "NEM DE CRISTAL LÍQUIDO.", ('F5',)),
        (23.2, 30.4, "PARA FAZER PRETO, O SUBPIXEL", "SIMPLESMENTE *APAGA*.", ('F5',)),
        (30.8, 38.4, "APAGADO, NÃO DÁ LUZ E QUASE NÃO", "GASTA ENERGIA: *PRETO DE VERDADE*.", ('F5',)),
        (38.8, 46.6, "À NOITE, LADO A LADO: O PRETO DO LCD", "BRILHA UM POUCO. O DO OLED, NÃO.", ('F4', 'F5')),
    ],
    'resolucao': [
        (0.5, 7.4, "QUANTOS PIXELS CABEM NUMA TELA?", "UMA RESOLUÇÃO COMUM: *1.080 X 2.400*.", ('F6',)),
        (7.8, 15.0, "SÃO 1.080 PIXELS EM CADA LINHA", "E 2.400 LINHAS.", ('F6',)),
        (15.4, 23.0, "1.080 X 2.400 =", "*2.592.000 PIXELS*.", ('F7',)),
        (23.4, 30.8, "CADA UM COM 3 SUBPIXELS:", "*7.776.000* LUZINHAS.", ('F7',)),
        (31.2, 38.6, "E TODAS ELAS CABEM NA PALMA", "DA SUA MÃO.", ()),
    ],
    'densidade': [
        (0.5, 7.4, "NUMA TELA DE 6,5 POLEGADAS, A", "DIAGONAL TEM UNS *2.632 PIXELS*.", ('F7', 'F8')),
        (7.8, 15.4, "2.632 / 6,5 = CERCA DE *405 PIXELS*", "POR POLEGADA (2,54 CM).", ('F8',)),
        (15.8, 23.4, "NUM SÓ *MILÍMETRO* CABEM", "UNS 16 PIXELS ENFILEIRADOS.", ('F8',)),
    ],
    'hz': [
        (0.5, 7.4, "A TELA NÃO MOSTRA UMA IMAGEM SÓ.", "ELA TROCA DE QUADRO SEM PARAR.", ('F9',)),
        (7.8, 14.8, "*60 HZ*: A TELA SE REDESENHA", "60 VEZES POR SEGUNDO.", ('F9',)),
        (15.2, 22.2, "*120 HZ*: 120 VEZES POR SEGUNDO.", "O MOVIMENTO FICA MAIS LISO.", ('F9',)),
        (22.6, 29.6, "CADA QUADRO DURA *16,7 MS* A 60 HZ", "E *8,3 MS* A 120 HZ.", ('F10',)),
        (30.0, 37.0, "A 120 HZ, A TELA PODE TROCAR ATÉ", "*311.040.000 PIXELS* POR SEGUNDO.", ('F10',)),
        (37.4, 43.6, "MUITOS AJUSTAM A TAXA SOZINHOS,", "CONFORME O QUE ESTÁ NA TELA.", ('F14',)),
    ],
    'meta': [
        (0.5, 7.4, "E ESTE VÍDEO? TAMBÉM É", "FEITO DE PIXELS.", ('F12',)),
        (7.8, 14.8, "NÓS DESENHAMOS CADA QUADRO COM", "*480 X 270 = 129.600 PIXELS*.", ('F12',)),
        (15.2, 22.2, "CADA PIXEL VIRA UM BLOCO 4 X 4. SAI", "1.920 X 1.080 = *2.073.600*.", ('F12',)),
        (22.6, 29.6, "30 QUADROS POR SEGUNDO. NA SUA TELA,", "VIRAM LUZ *VERMELHA, VERDE E AZUL*.", ('F12', 'F1')),
    ],
    'resumo': [
        (0.5, 8.6, "LCD: LUZ DE FUNDO, CRISTAL E FILTRO.", "OLED: CADA SUBPIXEL BRILHA SOZINHO.", ('F4', 'F5')),
        (9.0, 17.6, "TRÊS LUZES SOMADAS FAZEM", "AS CORES QUE VOCÊ VÊ NA TELA.", ('F2',)),
        (18.0, 26.4, "2.592.000 PIXELS, ATÉ 120 VEZES", "POR SEGUNDO, NA *SUA MÃO*.", ('F7', 'F9')),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Pixel geometry"', 'https://en.wikipedia.org/wiki/Pixel_geometry'),
    'F2': ('UC Santa Barbara (Geografia), "Additive Color"', 'https://people.geog.ucsb.edu/~jeff/115a/additive.html'),
    'F3': ('Encyclopaedia Britannica, "primary color"', 'https://britannica.com/science/primary-color'),
    'F4': ('Wikipedia, "Liquid-crystal display"', 'https://en.wikipedia.org/wiki/Liquid-crystal_display'),
    'F5': ('Wikipedia, "OLED"', 'https://en.wikipedia.org/wiki/OLED'),
    'F6': ('9to5Google, "What do HD, FHD, QHD, and UHD mean for your phone?"',
           'https://9to5google.com/2023/08/23/hd-fhd-qhd-uhd-phone-meaning/'),
    'F7': ('Conta a partir da resolução 1.080 x 2.400 (F6)', None),
    'F8': ('Wikipedia, "Pixel density" (PPI = diagonal em pixels / diagonal em polegadas); conta para 6,5"',
           'https://en.wikipedia.org/wiki/Pixel_density'),
    'F9': ('Android Authority, "What is a phone refresh rate?"',
           'https://www.androidauthority.com/phone-refresh-rate-120hz-1086643/'),
    'F10': ('Conta: 1 s / 60 e 1 s / 120; 2.592.000 x 120', None),
    'F11': ('Wikipedia, "Color depth"', 'https://en.wikipedia.org/wiki/Color_depth'),
    'F12': ('Ficha técnica deste vídeo (motor do canal: 480 x 270 ampliado 4x, 30 quadros/s)', None),
    'F13': ('Wikipedia, "Additive color"', 'https://en.wikipedia.org/wiki/Additive_color'),
    'F14': ('Tom\'s Guide, "Smartphone display refresh rates explained"',
            'https://www.tomsguide.com/news/smartphone-display-refresh-rates-explained'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'zoom': 'Zoom até o pixel', 'subpixel': 'Os subpixels',
                'cores': 'Somando luz: as cores', 'foto': 'A receita de cada pixel', 'lcd': 'Por dentro da tela LCD',
                'cristal': 'O cristal líquido abre e fecha', 'preto': 'O preto do LCD',
                'oled': 'OLED: cada subpixel faz a sua luz', 'resolucao': 'Quantos pixels: 2.592.000',
                'densidade': 'Pixels por polegada', 'hz': '60 Hz e 120 Hz',
                'meta': 'Este vídeo também é feito de pixels', 'resumo': 'Resumo'}

DESCRICAO = """Como a tela do celular faz cada pixel? A gente chega perto de um ponto do sol numa foto até ele se abrir em três luzinhas: vermelha, verde e azul. Depois soma as luzes para fazer as outras cores, abre um pixel de tela LCD camada por camada (luz de fundo, polarizadores, cristal líquido, filtro de cor), compara com o OLED, em que cada subpixel faz a própria luz, e conta quantos pixels cabem numa tela e quantas vezes por segundo ela se redesenha.

Cada quadro é pixel art desenhada por código, e a música é original. No fim, a gente mostra que este vídeo também é feito de pixels.

Capítulos
{capitulos}

Simplificado de propósito
- A imagem do celular no desenho tem 36 x 80 pontos; cada ponto representa um bloco de 30 x 30 pixels de uma tela 1.080 x 2.400.
- Cada subpixel aparece com 4 níveis de brilho (apagado, fraco, médio, máximo); no padrão de 24 bits são 256.
- Mostramos os subpixels em listras R, G, B lado a lado. Muitas telas OLED usam outros arranjos (por exemplo, com mais subpixels verdes do que vermelhos e azuis), e aí a conta de "3 subpixels por pixel" muda.
- O LCD mostrado é o de cristal torcido (TN), o caso clássico. Muitos celulares usam outros tipos (como IPS), em que as moléculas giram de outro jeito, mas a ideia de luz de fundo + polarizadores + filtro é a mesma. A direção em que a luz vibra aparece como um tracinho (em pé) ou um ponto (para dentro da tela).
- O polarizador comum deixa passar cerca de metade da luz da luz de fundo; desenhamos metade dos "fótons" parando nele.
- No OLED mostramos só circuito, eletrodos, camada orgânica e vidro. Telas OLED de verdade têm mais camadas, incluindo um polarizador na frente para reduzir o reflexo.
- A densidade usa uma tela de exemplo de 6,5 polegadas com 1.080 x 2.400; outros celulares têm outros tamanhos.
- 311.040.000 é o máximo, se todos os pixels mudassem em todos os 120 quadros; na prática muitos pixels repetem a cor de um quadro para o outro.
- Os 60 Hz e 120 Hz aparecem em câmera lenta de 10 vezes; em velocidade real o olho não separa os quadros.

Fontes
{fontes}

#pixelart #comofunciona #celular #oled #lcd #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O corte do pixel
# (LCD e OLED) ocupa x 8..176; o zoom fica centrado em x 148; os dois
# celulares dos Hz em 40..202; o celular da resolução em 18..150.
PREFIXO = 'ep04-tela'
CORTES = [
    dict(id='c1', de=('cores', 0.0), ate=('cores', 36.6), x=58, gancho=['3 LUZES', 'TODA COR'],
         titulo='Como 3 luzes fazem todas as cores da tela 🌈',
         descricao='Vermelho + verde = amarelo, verde + azul = ciano, vermelho + azul = magenta e as três juntas = branco. É assim que cada pixel da tela do celular faz as cores.'),
    dict(id='c2', de=('cristal', 0.0), ate=('cristal', 30.0), x=4, gancho=['O CRISTAL', 'QUE GIRA'],
         titulo='O cristal líquido que acende e apaga cada subpixel',
         descricao='Numa tela LCD, sem tensão o cristal líquido gira a luz 90 graus e ela passa pelo segundo polarizador. Com tensão as moléculas destorcem e a luz para.'),
    dict(id='c3', de=('zoom', 8.0), ate=('zoom', 36.0), x=58, gancho=['ZOOM ATÉ', 'O PIXEL'],
         titulo='Zoom na tela do celular até o subpixel 🔍',
         descricao='Chegando perto de um ponto do sol numa foto no celular: a imagem vira quadradinhos, e cada quadradinho vira 3 luzes, vermelha, verde e azul.'),
    dict(id='c4', de=('oled', 0.0), ate=('oled', 38.4), x=4, gancho=['O PRETO', 'DO OLED'],
         titulo='Por que o preto do OLED é preto de verdade ⚫',
         descricao='No OLED cada subpixel faz a própria luz. Para mostrar preto ele simplesmente apaga: não dá luz nem gasta energia.'),
    dict(id='c5', de=('hz', 0.0), ate=('hz', 29.6), x=30, gancho=['60 HZ OU', '120 HZ?'],
         titulo='60 Hz x 120 Hz na tela do celular, em câmera lenta',
         descricao='A 60 Hz a tela desenha 60 quadros por segundo, um a cada 16,7 ms. A 120 Hz são 120, um a cada 8,3 ms: o movimento fica mais liso.'),
    dict(id='c6', de=('resolucao', 0.0), ate=('resolucao', 38.6), x=14, gancho=['2.592.000', 'PIXELS'],
         titulo='Quantos pixels tem a tela do seu celular? 📱',
         descricao='Uma resolução comum de celular é 1.080 x 2.400: são 2.592.000 pixels e, com 3 subpixels cada, 7.776.000 luzinhas.'),
]
