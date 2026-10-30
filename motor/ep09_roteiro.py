#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep09 (série POR DENTRO): Como funciona o relógio mecânico.

A ideia: abrir um relógio de pulso mecânico genérico (sem marca) e montar peça
por peça: a mola real no tambor (a energia), as rodas (que multiplicam as
voltas), o escape (que solta a energia aos pouquinhos: o tic-tac), o balanço
com a espiral (o ritmo), os rubis, a redução dos ponteiros e o rotor do
automático. Protagonista: o balanço e os dentes da roda de escape, com um
placar de TIQUES e um painel com a energia que resta na mola. O escape é
animado pela física (trava, destrava, impulso, queda) e, no capítulo
`batida`, o tic cai na batida da música (120 BPM): 1 tique por batida e
depois a velocidade real, 8 por segundo = 4 por batida (semicolcheias).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Ritmos: 5 tiques/s (18.000/h) antes de 1970; hoje 6 (21.600), 8 (28.800)
      e alguns 10 (36.000); um tique = uma ida do balanço entre duas viradas;
      o período (uma oscilação inteira) tem 2 tiques; balanço + espiral formam
      um oscilador harmônico que mantém o tempo de cada tique constante; os
      melhores relógios de balanço no pulso erram poucos segundos por dia.
      Wikipedia, "Balance wheel".
  F2  Mola real: fita de aço em espiral dentro de um tambor; a coroa gira a
      catraca do tambor e uma lingueta impede a volta; a maioria anda 36 a 72 h;
      o tambor tem dentes e gira a roda do centro 1 vez por hora; a quarta roda
      gira 1 vez por minuto e leva o ponteiro dos segundos; os dentes da roda de
      escape travam alternadamente em duas pedras da âncora; o garfo pega o pino
      de impulso do balanço; rubis/safiras sintéticos; atrito aço-aço 0,58,
      safira-aço 0,10-0,15; redução de 12 para 1 até o ponteiro das horas;
      relógios antigos podiam errar 15 minutos por dia; o mecânico é menos exato
      que o quartzo. Wikipedia, "Mechanical watch".
  F3  Escape de âncora: trava, destrava, impulso (o dente escorrega na face
      inclinada da pedra), queda; o balanço fica livre a maior parte da
      oscilação; roda de escape com 15 dentes; Thomas Mudge, por volta de 1754.
      Wikipedia, "Lever escapement".
  F4  O tique vem da parada brusca do dente do escape; cada ida do balanço solta
      a roda "um tanto fixo"; o escape de âncora está na grande maioria dos
      relógios desde o século 19. Wikipedia, "Escapement".
  F5  Hoje a maioria dos rubis de relógio é rubi ou safira sintética; um
      relógio só de horas "completo" tem 17 rubis. Wikipedia, "Jewel bearing".
  F6  Automático: um peso que gira num eixo (rotor) dá corda com o movimento do
      pulso; uma embreagem deslizante impede corda demais; cheio, guarda energia
      para uns 2 dias. Wikipedia, "Automatic watch".
  F7  Cronômetro suíço (COSC): marcha média de -4 a +6 s por dia; cada
      movimento é testado 15 dias, em 5 posições e 3 temperaturas. Wikipedia, "COSC".
  F8  Relógio a quartzo comum: ganha ou perde 15 s a cada 30 dias. Wikipedia,
      "Quartz clock".
  F9  Contas: 8 tiques/s x 3.600 s = 28.800 por hora; x 24 = 691.200 por dia;
      2 tiques por oscilação -> 4 oscilações por segundo = 4 Hz (a partir de F1).
"""

TITULO = "Como funciona o relógio mecânico | O tic-tac por dentro, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='abrir', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='pecas', gen='synthwave', bars=25, papel='drop'),      # 60 s (6 peças x 10 s)
    dict(id='mola', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='engrenagens', gen='lofi', bars=12, papel='drop'),     # 36 s
    dict(id='escape', gen='lofi', bars=16, papel='break'),         # 48 s (1 tique por compasso)
    dict(id='balanco', gen='lofi', bars=12, papel='drop'),         # 36 s (1 tique por batida)
    dict(id='batida', gen='house', bars=16, papel='drop', bpm=120),  # 32 s (tique na batida)
    dict(id='rubis', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='ponteiros', gen='lofi', bars=9, papel='drop'),        # 27 s
    dict(id='automatico', gen='lofi', bars=12, papel='drop'),      # 36 s
    dict(id='precisao', gen='synthwave', bars=15, papel='drop'),   # 36 s
    dict(id='historia', gen='lofi', bars=8, papel='break'),        # 24 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "ESTE RELÓGIO NÃO TEM PILHA. ELE FAZ", "*TIC-TAC* 8 VEZES POR SEGUNDO.", ('F1',)),
        (6.0, 11.6, "SÃO *691.200 TIQUES* POR DIA.", "VAMOS VER COMO, PEÇA POR PEÇA.", ('F9',)),
    ],
    'abrir': [
        (0.8, 9.6, "UM RELÓGIO DE PULSO *MECÂNICO*:", "SÓ MOLAS, RODAS E PEDRAS.", ('F2',)),
        (9.8, 19.6, "ELE PRECISA DE DUAS COISAS:", "*ENERGIA* E UM *RITMO* CONSTANTE.", ('F1', 'F2')),
        (19.8, 29.6, "PELO FUNDO DE VIDRO DESTE AQUI,", "DÁ PARA VER O *MECANISMO* ANDANDO.", ()),
    ],
    'pecas': [
        (0.3, 9.6, "O *TAMBOR*: GUARDA A MOLA REAL,", "A FONTE DE ENERGIA.", ('F2',)),
        (10.3, 19.6, "AS *RODAS*: LEVAM A FORÇA DA MOLA", "E CONTAM O TEMPO.", ('F2',)),
        (20.3, 29.6, "A *RODA DE ESCAPE*: QUASE SEMPRE", "COM 15 DENTES.", ('F3',)),
        (30.3, 39.6, "A *ÂNCORA*: UMA ALAVANCA COM", "DUAS PEDRAS E UM GARFO.", ('F2',)),
        (40.3, 49.6, "O *BALANÇO* COM A ESPIRAL: QUANDO", "ELE CHEGA, TUDO COMEÇA A ANDAR.", ('F1',)),
        (50.3, 59.6, "E OS *RUBIS*: PEDRAS ONDE", "OS EIXOS GIRAM.", ('F5',)),
    ],
    'mola': [
        (0.5, 8.6, "A ENERGIA FICA NA *MOLA REAL*: UMA", "FITA DE AÇO ENROLADA NUM TAMBOR.", ('F2',)),
        (8.8, 17.6, "GIRAR A *COROA* ENROLA A MOLA. UMA", "LINGUETA NÃO DEIXA ELA VOLTAR.", ('F2',)),
        (17.8, 26.6, "DESENROLANDO, A MOLA GIRA O TAMBOR.", "E O TAMBOR TEM *DENTES*.", ('F2',)),
        (26.8, 35.6, "CHEIA, ELA TOCA O RELÓGIO POR", "*36 A 72 HORAS*, CONFORME O MODELO.", ('F2',)),
    ],
    'engrenagens': [
        (0.5, 8.6, "O TAMBOR GIRA DEVAGAR E EMPURRA", "UMA FILA DE *RODAS*.", ('F2',)),
        (8.8, 17.6, "RODA GRANDE TOCA PINHÃO PEQUENO:", "A CADA PASSO, O GIRO *MULTIPLICA*.", ('F2',)),
        (17.8, 26.6, "A *RODA DO CENTRO* DÁ 1 VOLTA", "POR HORA: É O PONTEIRO DOS MINUTOS.", ('F2',)),
        (26.8, 35.6, "A *QUARTA RODA* DÁ 1 VOLTA POR", "MINUTO: LEVA O DOS SEGUNDOS.", ('F2',)),
    ],
    'escape': [
        (0.5, 8.6, "O *ESCAPE* SOLTA A FORÇA DA MOLA", "AOS POUQUINHOS, NUM PASSO FIXO.", ('F4',)),
        (8.8, 17.6, "PARADA, UMA PEDRA DA ÂNCORA", "*TRAVA* UM DENTE DA RODA.", ('F3',)),
        (17.8, 26.6, "O BALANÇO PASSA, PUXA O GARFO", "E *DESTRAVA* A RODA.", ('F3',)),
        (26.8, 35.6, "O DENTE ESCORREGA NA PEDRA E", "EMPURRA O BALANÇO: É O *IMPULSO*.", ('F3',)),
        (35.8, 41.6, "A RODA *CAI* UM POUQUINHO E", "TRAVA NA OUTRA PEDRA.", ('F3',)),
        (41.8, 47.6, "ESSA BATIDA SECA É O *TIC-TAC*", "QUE A GENTE OUVE.", ('F4',)),
    ],
    'balanco': [
        (0.5, 8.6, "QUEM DÁ O RITMO É O *BALANÇO*: UM", "VOLANTE PRESO A UMA MOLA FININHA.", ('F1',)),
        (8.8, 17.6, "A *ESPIRAL* PUXA ELE DE VOLTA. ELE", "VAI E VEM SEMPRE NO MESMO TEMPO.", ('F1',)),
        (17.8, 26.6, "QUASE O TEMPO TODO ELE GIRA *SOLTO*:", "SÓ TOCA O GARFO NUM INSTANTE.", ('F3',)),
        (26.8, 35.6, "CADA IDA OU VOLTA É UM *TIQUE*.", "UMA OSCILAÇÃO INTEIRA: 2 TIQUES.", ('F1',)),
    ],
    'batida': [
        (0.5, 7.6, "AGORA NO RITMO DA MÚSICA: *1 TIQUE*", "*POR BATIDA*, 2 POR SEGUNDO.", ()),
        (7.8, 15.6, "UM RELÓGIO COMUM DE HOJE BATE", "*4 VEZES MAIS RÁPIDO*. OLHA:", ('F1',)),
        (16.0, 23.6, "*8 TIQUES POR SEGUNDO*: 4 EM CADA", "BATIDA. É A VELOCIDADE DE VERDADE.", ('F1',)),
        (23.8, 31.6, "SÃO *28.800 POR HORA*. COM 2 TIQUES", "POR OSCILAÇÃO, DÁ *4 HZ*.", ('F1', 'F9')),
    ],
    'rubis': [
        (0.5, 7.6, "OS PONTOS VERMELHOS SÃO *RUBIS*:", "PEDRAS SINTÉTICAS, RUBI OU SAFIRA.", ('F5',)),
        (7.8, 15.6, "OS EIXOS GIRAM DENTRO DELES. A PEDRA", "LISA E DURA DÁ *MENOS ATRITO*.", ('F2',)),
        (15.8, 22.6, "ATRITO DE AÇO EM AÇO: *0,58*.", "DE SAFIRA EM AÇO: *0,10 A 0,15*.", ('F2',)),
        (22.8, 29.6, "UM RELÓGIO SÓ DE HORAS, COMPLETO,", "COSTUMA TER *17 RUBIS*.", ('F5',)),
    ],
    'ponteiros': [
        (0.5, 8.6, "SOB O MOSTRADOR, MAIS UMA REDUÇÃO", "PEQUENA: DE *12 PARA 1*.", ('F2',)),
        (8.8, 17.6, "O PONTEIRO DOS MINUTOS DÁ 12 VOLTAS", "E O DAS HORAS DÁ *1 VOLTA*.", ('F2',)),
        (17.8, 26.6, "AQUI SÃO 2 PASSOS SEGUIDOS:", "3 X 4 = 12.", ()),
    ],
    'automatico': [
        (0.5, 8.6, "MUITOS RELÓGIOS SÃO *AUTOMÁTICOS*:", "DÃO CORDA SOZINHOS, NO PULSO.", ('F6',)),
        (8.8, 17.6, "UM PESO EM MEIA-LUA, O *ROTOR*, GIRA", "NUM EIXO QUANDO O BRAÇO MEXE.", ('F6',)),
        (17.8, 26.6, "CADA BALANÇO DO ROTOR DÁ", "UM POUCO DE CORDA NA MOLA REAL.", ('F6',)),
        (26.8, 35.6, "CHEIA, UMA *EMBREAGEM* DESLIZA E A", "MOLA NÃO PASSA DO PONTO.", ('F6',)),
    ],
    'precisao': [
        (0.5, 8.6, "E A PRECISÃO? UM BOM MECÂNICO ERRA", "*POUCOS SEGUNDOS POR DIA*.", ('F1',)),
        (8.8, 17.6, "O SELO SUÍÇO DE *CRONÔMETRO* PEDE", "DE *-4 A +6 SEGUNDOS* POR DIA.", ('F7',)),
        (17.8, 26.6, "O TESTE DURA 15 DIAS, EM 5 POSIÇÕES", "E EM 3 TEMPERATURAS.", ('F7',)),
        (26.8, 35.6, "UM RELÓGIO A *QUARTZO* COMUM ERRA", "CERCA DE *15 SEGUNDOS POR MÊS*.", ('F8', 'F2')),
    ],
    'historia': [
        (0.5, 7.6, "OS PRIMEIROS RELÓGIOS DE BOLSO PODIAM", "ERRAR ATÉ *15 MINUTOS POR DIA*.", ('F2',)),
        (7.8, 15.6, "POR VOLTA DE *1754*, THOMAS MUDGE", "INVENTOU O ESCAPE DE ÂNCORA.", ('F3',)),
        (15.8, 23.6, "DESDE O SÉCULO 19, ELE ESTÁ NA", "*GRANDE MAIORIA* DOS RELÓGIOS.", ('F4',)),
    ],
    'resumo': [
        (0.5, 9.6, "A *MOLA* GUARDA A ENERGIA.", "AS *RODAS* LEVAM E CONTAM.", ('F2',)),
        (9.8, 19.6, "O *ESCAPE* SOLTA AOS POUQUINHOS", "E O *BALANÇO* MARCA O PASSO.", ('F1', 'F4')),
        (19.8, 29.6, "8 TIQUES POR SEGUNDO,", "*691.200 POR DIA*. SEM PILHA.", ('F9',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Balance wheel"', 'https://en.wikipedia.org/wiki/Balance_wheel'),
    'F2': ('Wikipedia, "Mechanical watch"', 'https://en.wikipedia.org/wiki/Mechanical_watch'),
    'F3': ('Wikipedia, "Lever escapement"', 'https://en.wikipedia.org/wiki/Lever_escapement'),
    'F4': ('Wikipedia, "Escapement"', 'https://en.wikipedia.org/wiki/Escapement'),
    'F5': ('Wikipedia, "Jewel bearing"', 'https://en.wikipedia.org/wiki/Jewel_bearing'),
    'F6': ('Wikipedia, "Automatic watch"', 'https://en.wikipedia.org/wiki/Automatic_watch'),
    'F7': ('Wikipedia, "COSC" (Contrôle Officiel Suisse des Chronomètres)', 'https://en.wikipedia.org/wiki/COSC'),
    'F8': ('Wikipedia, "Quartz clock"', 'https://en.wikipedia.org/wiki/Quartz_clock'),
    'F9': ('Conta a partir de F1: 8 x 3.600 = 28.800 por hora; x 24 = 691.200 por dia; 2 tiques por oscilação = 4 Hz', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'abrir': 'Abrindo o relógio', 'pecas': 'As peças do mecanismo',
                'mola': 'A mola real: a energia', 'engrenagens': 'As rodas multiplicam as voltas',
                'escape': 'O escape em câmera superlenta', 'balanco': 'O balanço: o ritmo',
                'batida': 'O tic-tac no ritmo da música', 'rubis': 'Por que tem rubis',
                'ponteiros': 'Horas e minutos: 12 para 1', 'automatico': 'O rotor do automático',
                'precisao': 'Mecânico x quartzo', 'historia': 'Um pouco de história',
                'resumo': 'Resumo'}

DESCRICAO = """Como um relógio de pulso mecânico marca o tempo sem pilha? A gente abre um relógio (genérico, sem marca), monta o mecanismo peça por peça e mostra o caminho da energia: a mola real no tambor, as rodas que multiplicam as voltas, o escape que solta a energia aos pouquinhos (o tic-tac) e o balanço com a espiral, que dá o ritmo. Um placar conta os tiques e um painel mostra a energia que resta na mola.

O escape aparece em câmera superlenta (trava, destrava, impulso e queda) e, num trecho, bate exatamente no ritmo da música: 1 tique por batida e depois a velocidade de verdade, 8 tiques por segundo. Também: os rubis, a redução de 12 para 1 dos ponteiros, o rotor do automático e a precisão do mecânico comparada à do quartzo.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O relógio é genérico e desenhado "aberto", sem as pontes que cobrem as rodas. A posição das peças é inventada; num relógio de verdade cada fabricante arruma de um jeito.
- O escape é animado pela geometria (a âncora segue o pino do balanço e a roda anda o que a pedra deixa), mas o tamanho das pedras, o ângulo dos dentes e a amplitude do balanço (220 graus para cada lado) são exemplos. Faltam algumas peças de segurança do escape de verdade (o dardo e o rolete de segurança).
- Usamos o ritmo mais comum de hoje, 28.800 alternâncias por hora; há relógios com 18.000, 21.600 e 36.000.
- As relações entre as rodas (tambor 6, centro 8, terceira 7,5, quarta 16) são um exemplo que fecha a conta: a roda do centro dá 1 volta por hora e a quarta, 1 por minuto. A redução dos ponteiros em 3 x 4 também é um exemplo; cada movimento usa os seus números.
- A reserva de 48 horas no painel da mola é um exemplo dentro da faixa de 36 a 72 horas. No capítulo da mola, no das rodas e no dos ponteiros o tempo está acelerado, e o rotor do automático enche a mola bem mais rápido que na vida real.
- No balanço, o "toca o garfo" do gráfico é a janela em que o pino de impulso está dentro do garfo da âncora no nosso desenho.
- A faixa de erro do quartzo no painel (cerca de meio segundo por dia) é a conta de 15 segundos em 30 dias.

Fontes
{fontes}

#relogio #comofunciona #pixelart #relojoaria #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O escape em close
# ocupa x 0..230 (roda + âncora + rolete em 40..220); o balanço grande, 60..216;
# o tambor, 34..202; o mapa do mecanismo, 50..250.
PREFIXO = 'ep09-relogio'
CORTES = [
    dict(id='c1', de=('escape', 0.0), ate=('escape', 36.0), x=50, gancho=['O TIC-TAC', 'POR DENTRO'],
         titulo='O tic-tac do relógio em câmera superlenta ⏱️',
         descricao='O escape de âncora: a pedra trava a roda, o balanço destrava, o dente empurra (impulso) e a roda cai na outra pedra. Essa batida é o tic-tac.'),
    dict(id='c2', de=('batida', 0.0), ate=('batida', 32.0), x=50, gancho=['RELÓGIO NA', 'BATIDA'],
         titulo='Um relógio mecânico no ritmo da música 🎵',
         descricao='Primeiro 1 tique por batida. Depois a velocidade de verdade: 8 tiques por segundo, 28.800 por hora, 4 em cada batida a 120 BPM.'),
    dict(id='c3', de=('balanco', 0.0), ate=('balanco', 36.0), x=48, gancho=['O CORAÇÃO', 'DO RELÓGIO'],
         titulo='O balanço: o coração do relógio mecânico',
         descricao='Um volante preso a uma mola fininha, a espiral, vai e vem sempre no mesmo tempo. Cada ida ou volta é um tique.'),
    dict(id='c4', de=('mola', 0.0), ate=('mola', 36.0), x=34, gancho=['DAR CORDA', 'É ISSO'],
         titulo='O que acontece quando você dá corda no relógio?',
         descricao='Girar a coroa enrola a mola real dentro do tambor; uma lingueta não deixa ela voltar. Cheia, a mola toca o relógio por 36 a 72 horas, conforme o modelo.'),
    dict(id='c5', de=('automatico', 0.0), ate=('automatico', 36.0), x=60, gancho=['CORDA', 'SOZINHO?'],
         titulo='Como o relógio automático dá corda sozinho',
         descricao='Um peso em meia-lua, o rotor, gira quando o braço mexe e enrola a mola real. Cheia, uma embreagem desliza para não passar do ponto.'),
    dict(id='c6', de=('rubis', 0.0), ate=('rubis', 30.0), x=60, gancho=['RUBI NO', 'RELÓGIO?'],
         titulo='Por que relógio mecânico tem rubis? 💎',
         descricao='Os eixos giram dentro de pedras sintéticas (rubi ou safira): atrito de 0,10 a 0,15 contra 0,58 de aço em aço. Um relógio só de horas completo costuma ter 17.'),
]
