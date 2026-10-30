#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep07 (série A JORNADA): A jornada de uma mensagem de celular.

A ideia: seguir uma mensagem (texto + uma foto) do instante em que alguém
aperta ENVIAR em São Paulo até os tiques de "entregue" e "lida" num celular em
Lisboa. Protagonista: a mensagem, depois o PACOTE Nº 1 dela. Objetivo que sobe
na tela: "etapa 4 de 9", a distância percorrida (km) e o tempo de viagem (ms).
O desenho mora em `ep07_motor.py` (cenas) e `ep07_desenho.py` (celular, torre,
fibra, mapa, mar, data center, pacote, painel).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

O trajeto do exemplo (distâncias em linha reta, o mínimo possível):
  celular -> antena (rádio)       1 km   (exemplo; F7)
  São Paulo -> Fortaleza (fibra)  2.360 km   (F13)
  Fortaleza -> Sines (cabo no mar) 5.900 km  (F14)
  Sines -> Lisboa (fibra)          88 km     (F16)
  antena -> celular (rádio)       1 km
  total ~8.350 km; tempo só de viagem ~41,7 ms (F21)

FATOS E FONTES (todas lidas em 29-30/10/2026)
  F1  ASCII: cada caractere é um número de 0 a 127 (código de 7 bits);
      O = 79, I = 73, ! = 33. Wikipedia, "ASCII".
  F2  UTF-8: os 128 primeiros caracteres são os mesmos do ASCII, 1 byte cada;
      até 4 bytes por caractere; emoji usa 4 bytes. Wikipedia, "UTF-8".
  F3  Criptografia de ponta a ponta: só quem envia e quem recebe leem; nenhum
      terceiro, nem o provedor do serviço, consegue decifrar; usada por
      aplicativos de mensagem populares. Wikipedia, "End-to-end encryption".
  F4  Comutação de pacotes: cabeçalho + carga; o cabeçalho leva o pacote ao
      destino; cada pacote segue sozinho, às vezes por caminhos diferentes,
      chegando fora de ordem; no destino a mensagem é remontada pelos números
      de sequência. Wikipedia, "Packet switching".
  F5  Ethernet: MTU padrão de 1.500 bytes. Wikipedia, "Maximum transmission unit".
  F6  Conta (F5): foto de 300 KB (exemplo) = 300.000 bytes / 1.500 = 200;
      o cabeçalho ocupa parte de cada pacote, então são MAIS de 200.
  F7  O celular fala por ondas de rádio com uma antena local; nas cidades
      densas, as antenas ficam a 400-800 m umas das outras. Wikipedia, "Cell site".
  F8  Ondas de rádio são ondas eletromagnéticas; no ar viajam quase na
      velocidade da luz; é o que o celular usa. Wikipedia, "Radio wave".
  F9  Luz no vácuo: ~300.000 km/s; na fibra é ~35% mais lenta. Wikipedia, "Speed of light".
  F10 Na fibra, o sinal anda a ~200.000 km/s; a fibra revestida tem a grossura
      de um fio de cabelo; a luz fica presa no núcleo por reflexão interna
      total. Wikipedia, "Optical fiber".
  F11 Fibra: pulsos de luz; transmissor (laser/LED) converte sinal elétrico em
      luz; fotodetector converte de volta. Wikipedia, "Fiber-optic communication".
  F12 O "backhaul" liga a antena ao núcleo da rede da operadora; fibra é um dos
      dois métodos principais. Wikipedia, "Backhaul (telecommunications)".
  F13 São Paulo - Fortaleza: 2.360,5 km em linha reta. IBGE, Anuário
      Estatístico, tabela 1.1.1.3.
  F14 Cabo submarino Fortaleza (Brasil) - Sines (Portugal): ~5.900 km, desde
      2021; ida e volta em menos de 60 ms. Wikipedia, "EllaLink".
  F15 Cabos submarinos levam 99% do tráfego de dados que cruza os oceanos;
      têm uns 25 mm de diâmetro; repetidores a cada ~100 km. Wikipedia,
      "Submarine communications cable".
  F16 Lisboa - Sines: 88,5 km em linha reta. Himmera Distance Calculator.
  F17 TCP: detecta pacote perdido e pede de novo, reordena o que chegou fora
      de ordem, quem recebe manda confirmações (ACK). Wikipedia, "Transmission
      Control Protocol".
  F18 "Entregue" = o aparelho de quem recebe confirmou a entrega; "lida" =
      quem recebe marcou a conversa como lida. Stream, documentação de chat.
  F19 Roteador lê o endereço no cabeçalho e manda o pacote para a próxima
      rede, de roteador em roteador. Wikipedia, "Router (computing)".
  F20 Data center: prédio com equipamento eletrônico para processar, guardar e
      transmitir informação digital. Wikipedia, "Data center".
  F21 Conta (F9, F10, F13, F14, F16): 1 + 2.360 + 5.900 + 88 + 1 = 8.350 km;
      2.360/200.000 = 11,8 ms; 5.900/200.000 = 29,5 ms; total ~41,7 ms.
  F22 LTE (4G): latência no trecho de rádio abaixo de 5 ms em condições
      ideais. Wikipedia, "LTE (telecommunication)".
  F23 Um piscar de olhos dura em média 100 a 150 ms. Wikipedia, "Blinking".
"""

TITULO = "A jornada de uma mensagem de celular | Do ENVIAR ao LIDA em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='enviar', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='bits', gen='synthwave', bars=15, papel='drop'),       # 36 s
    dict(id='cadeado', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='pacotes', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='radio', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='fibra', gen='synthwave', bars=14, papel='drop'),      # 33,6 s
    dict(id='rede', gen='lofi', bars=11, papel='drop'),            # 33 s
    dict(id='oceano', gen='lofi', bars=16, papel='break'),         # 48 s
    dict(id='servidor', gen='lofi', bars=11, papel='drop'),        # 33 s
    dict(id='chegada', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='abrir', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='conta', gen='synthwave', bars=15, papel='break'),     # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 5.8, "VOCÊ APERTA *ENVIAR*.", "A MENSAGEM SAI DE SÃO PAULO...", ()),
        (6.0, 11.6, "...E CRUZA O OCEANO ATÉ LISBOA EM", "UNS *42 MILÉSIMOS DE SEGUNDO*.", ('F21',)),
    ],
    'enviar': [
        (0.8, 7.0, "UM CELULAR COMUM, UM APLICATIVO", "DE MENSAGENS. UM *OI* E UMA FOTO.", ()),
        (7.2, 14.4, "QUEM RECEBE ESTÁ EM *LISBOA*,", "DO OUTRO LADO DO ATLÂNTICO.", ()),
        (14.6, 21.8, "PARA CHEGAR LÁ, A MENSAGEM", "PASSA POR *9 ETAPAS*.", ()),
        (22.0, 29.6, "VAMOS SEGUIR ESSA MENSAGEM,", "DO *ENVIAR* ATÉ O *LIDA*.", ()),
    ],
    'bits': [
        (0.5, 7.4, "ETAPA 1: O CELULAR NÃO GUARDA", "LETRAS. ELE GUARDA *NÚMEROS*.", ('F1',)),
        (7.6, 14.6, "CADA LETRA TEM O SEU NÚMERO:", "*O = 79*, *I = 73*, *! = 33*.", ('F1',)),
        (14.8, 21.8, "E CADA NÚMERO VIRA *8 BITS*:", "ZEROS E UNS. 79 = 01001111.", ('F1', 'F2')),
        (22.0, 28.8, "8 BITS = 1 *BYTE*. UMA LETRA SIMPLES", "OCUPA 1 BYTE. UM EMOJI, 4.", ('F2',)),
        (29.0, 35.6, "A FOTO TAMBÉM VIRA BYTES:", "NESTE EXEMPLO, *300 MIL*.", ()),
    ],
    'cadeado': [
        (0.5, 7.4, "ETAPA 2: ANTES DE SAIR, OS BITS", "SÃO *EMBARALHADOS* COM UMA CHAVE.", ('F3',)),
        (7.6, 14.6, "É A *CRIPTOGRAFIA DE PONTA A*", "*PONTA*.", ('F3',)),
        (14.8, 21.8, "SÓ O SEU CELULAR E O DE QUEM", "RECEBE CONSEGUEM *LER*.", ('F3',)),
        (22.0, 28.8, "NO CAMINHO, QUEM PEGAR OS BITS", "SÓ VÊ UMA BAGUNÇA DE ZEROS E UNS.", ('F3',)),
        (29.0, 35.6, "NEM A EMPRESA DO APLICATIVO", "CONSEGUE *ABRIR*.", ('F3',)),
    ],
    'pacotes': [
        (0.5, 7.4, "ETAPA 3: A MENSAGEM É CORTADA", "EM PEDAÇOS: OS *PACOTES*.", ('F4',)),
        (7.6, 14.6, "CADA UM GANHA UM *CABEÇALHO*: DE", "ONDE VEM, PARA ONDE VAI, NÚMERO.", ('F4',)),
        (14.8, 21.8, "NA REDE, UM PACOTE TEM", "ATÉ *1.500 BYTES*.", ('F5',)),
        (22.0, 28.8, "O *OI* CABE NUM PACOTE SÓ. A FOTO", "DE 300 KB VIRA *MAIS DE 200*.", ('F5', 'F6')),
        (29.0, 35.6, "VAMOS SEGUIR UM DELES:", "O *PACOTE Nº 1*.", ()),
    ],
    'radio': [
        (0.5, 7.4, "ETAPA 4: O CELULAR TRANSFORMA", "OS BITS EM *ONDAS DE RÁDIO*.", ('F7', 'F8')),
        (7.6, 14.6, "ELAS VÃO ATÉ A *ANTENA* MAIS", "PERTO, NO ALTO DE UMA TORRE.", ('F7',)),
        (14.8, 21.8, "NA CIDADE, AS ANTENAS FICAM", "A *400 A 800 METROS* UMAS DAS OUTRAS.", ('F7',)),
        (22.0, 29.6, "E O RÁDIO VIAJA NA VELOCIDADE", "DA LUZ: *300.000 KM POR SEGUNDO*.", ('F8', 'F9')),
    ],
    'fibra': [
        (0.5, 7.0, "ETAPA 5: DA TORRE, O PACOTE DESCE", "PARA UM CABO DE *FIBRA ÓTICA*.", ('F12',)),
        (7.2, 13.8, "UM *LASER* PISCA: OS BITS VIRAM", "*PULSOS DE LUZ*.", ('F11',)),
        (14.0, 20.6, "A FIBRA É UM FIO DE VIDRO DA", "GROSSURA DE UM *FIO DE CABELO*.", ('F10',)),
        (20.8, 27.2, "A LUZ BATE NA PAREDE DO VIDRO", "E VOLTA: NÃO CONSEGUE ESCAPAR.", ('F10',)),
        (27.4, 33.4, "NO VIDRO A LUZ É MAIS LENTA:", "UNS *200.000 KM POR SEGUNDO*.", ('F9', 'F10')),
    ],
    'rede': [
        (0.5, 7.4, "ETAPA 6: A REDE DA OPERADORA", "É FEITA DE *ROTEADORES*.", ('F19',)),
        (7.6, 14.6, "CADA ROTEADOR LÊ O ENDEREÇO", "E ESCOLHE O *PRÓXIMO TRECHO*.", ('F19',)),
        (14.8, 21.8, "OUTROS PACOTES DA FOTO PODEM IR", "POR *OUTROS CAMINHOS*.", ('F4',)),
        (22.0, 28.4, "SÃO PAULO ATÉ FORTALEZA: *2.360 KM*", "EM LINHA RETA. UNS 12 MS.", ('F13', 'F21')),
        (28.6, 32.8, "EM FORTALEZA, O CABO", "*ENTRA NO MAR*.", ('F14',)),
    ],
    'oceano': [
        (0.5, 7.4, "ETAPA 7: NO FUNDO DO ATLÂNTICO,", "UM *CABO SUBMARINO*.", ('F14',)),
        (7.6, 14.6, "ELE LIGA FORTALEZA A SINES,", "EM PORTUGAL: UNS *5.900 KM*.", ('F14',)),
        (14.8, 21.8, "O CABO TEM UNS *2,5 CM* DE GROSSURA.", "AS FIBRAS FICAM BEM NO MEIO.", ('F15',)),
        (22.0, 28.8, "A CADA 100 KM, MAIS OU MENOS, UM", "*REPETIDOR* REFORÇA A LUZ.", ('F15',)),
        (29.0, 36.4, "CABOS ASSIM LEVAM *99%* DOS", "DADOS QUE CRUZAM OS OCEANOS.", ('F15',)),
        (36.6, 43.6, "A TRAVESSIA INTEIRA LEVA", "UNS *30 MILÉSIMOS DE SEGUNDO*.", ('F14', 'F21')),
        (43.8, 47.9, "TERRA À VISTA: *PORTUGAL*.", "", ()),
    ],
    'servidor': [
        (0.5, 7.4, "ETAPA 8: O PACOTE CHEGA A UM", "*DATA CENTER*, PRÉDIO DE COMPUTADORES.", ('F20',)),
        (7.6, 14.6, "LÁ ESTÁ O *SERVIDOR* DO APLICATIVO.", "NESTE EXEMPLO, PERTO DE LISBOA.", ('F16',)),
        (14.8, 21.8, "ELE LÊ O CABEÇALHO: SABE PARA", "QUEM É A MENSAGEM...", ('F4',)),
        (22.0, 28.4, "...MAS NÃO LÊ A MENSAGEM:", "ELA CONTINUA *TRANCADA*.", ('F3',)),
        (28.6, 32.8, "E MANDA O PACOTE ADIANTE.", "", ()),
    ],
    'chegada': [
        (0.5, 7.4, "ETAPA 9: FIBRA ATÉ A ANTENA E", "RÁDIO ATÉ O *OUTRO CELULAR*.", ('F7', 'F12')),
        (7.6, 14.6, "OS PACOTES DA FOTO CHEGAM", "*FORA DE ORDEM*.", ('F4',)),
        (14.8, 21.8, "O CELULAR USA OS NÚMEROS", "PARA *MONTAR* TUDO DE NOVO.", ('F4', 'F17')),
        (22.0, 28.8, "FALTOU UM? ELE AVISA, E", "O PACOTE É *MANDADO DE NOVO*.", ('F17',)),
        (29.0, 35.6, "AGORA A MENSAGEM ESTÁ INTEIRA.", "MAS AINDA *TRANCADA*.", ('F3',)),
    ],
    'abrir': [
        (0.5, 7.4, "SÓ ESTE CELULAR TEM A CHAVE.", "ELE *DESEMBARALHA* OS BITS.", ('F3',)),
        (7.6, 14.6, "OS BITS VIRAM NÚMEROS, E OS", "NÚMEROS VIRAM LETRAS: *OI!*", ('F1',)),
        (14.8, 21.8, "O CELULAR AVISA DE VOLTA:", "*ENTREGUE*.", ('F18',)),
        (22.0, 29.6, "QUANDO A PESSOA ABRE A CONVERSA,", "VAI OUTRO AVISO: *LIDA*.", ('F18',)),
    ],
    'conta': [
        (0.5, 7.4, "A VIAGEM INTEIRA, EM LINHA RETA:", "UNS *8.350 KM*.", ('F21',)),
        (7.6, 14.6, "SÓ VIAJANDO PELO AR E PELA FIBRA:", "UNS *42 MILÉSIMOS DE SEGUNDO*.", ('F21',)),
        (14.8, 21.8, "NA VIDA REAL É UM POUCO MAIS: O CABO", "FAZ CURVAS E CADA PARADA SOMA.", ('F9', 'F22')),
        (22.0, 28.8, "PARA COMPARAR: UM PISCAR DE OLHOS", "DURA *100 A 150 MS*.", ('F23',)),
        (29.0, 35.6, "E O OCEANO, IDA E VOLTA:", "*MENOS DE 60 MS*.", ('F14',)),
    ],
    'resumo': [
        (0.5, 7.4, "1 LETRAS VIRAM BITS. 2 OS BITS SÃO", "TRANCADOS. 3 VIRAM *PACOTES*.", ('F1', 'F3', 'F4')),
        (7.6, 14.6, "4 RÁDIO ATÉ A TORRE. 5 E 6 FIBRA,", "DE ROTEADOR EM ROTEADOR.", ('F7', 'F19')),
        (14.8, 21.8, "7 O CABO NO FUNDO DO MAR.", "8 O SERVIDOR, SEM LER NADA.", ('F15', 'F3')),
        (22.0, 29.6, "9 OUTRO CELULAR MONTA, DESTRANCA", "E MOSTRA: *OI!*", ('F4', 'F3')),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "ASCII"', 'https://en.wikipedia.org/wiki/ASCII'),
    'F2': ('Wikipedia, "UTF-8"', 'https://en.wikipedia.org/wiki/UTF-8'),
    'F3': ('Wikipedia, "End-to-end encryption"', 'https://en.wikipedia.org/wiki/End-to-end_encryption'),
    'F4': ('Wikipedia, "Packet switching"', 'https://en.wikipedia.org/wiki/Packet_switching'),
    'F5': ('Wikipedia, "Maximum transmission unit"', 'https://en.wikipedia.org/wiki/Maximum_transmission_unit'),
    'F6': ('Conta a partir de F5: 300.000 bytes / 1.500 bytes = 200 (e o cabeçalho ocupa parte de cada pacote)', None),
    'F7': ('Wikipedia, "Cell site"', 'https://en.wikipedia.org/wiki/Cell_site'),
    'F8': ('Wikipedia, "Radio wave"', 'https://en.wikipedia.org/wiki/Radio_wave'),
    'F9': ('Wikipedia, "Speed of light"', 'https://en.wikipedia.org/wiki/Speed_of_light'),
    'F10': ('Wikipedia, "Optical fiber"', 'https://en.wikipedia.org/wiki/Optical_fiber'),
    'F11': ('Wikipedia, "Fiber-optic communication"', 'https://en.wikipedia.org/wiki/Fiber-optic_communication'),
    'F12': ('Wikipedia, "Backhaul (telecommunications)"', 'https://en.wikipedia.org/wiki/Backhaul_(telecommunications)'),
    'F13': ('IBGE, Anuário Estatístico do Brasil, tabela 1.1.1.3 "Distância em linha reta entre os Municípios das Capitais"',
            'https://anuario.ibge.gov.br/images/aeb/2024/s1/2_pdf/s1t1103.pdf'),
    'F14': ('Wikipedia, "EllaLink" (cabo submarino Fortaleza - Sines)', 'https://en.wikipedia.org/wiki/EllaLink'),
    'F15': ('Wikipedia, "Submarine communications cable"', 'https://en.wikipedia.org/wiki/Submarine_communications_cable'),
    'F16': ('Himmera Distance Calculator, "Distance Lisbon to Sines"',
            'https://distancecalculator.himmera.com/distance-lisbon-sines-151601.html'),
    'F17': ('Wikipedia, "Transmission Control Protocol"', 'https://en.wikipedia.org/wiki/Transmission_Control_Protocol'),
    'F18': ('Stream, documentação de chat, "Delivered & Read Status"',
            'https://getstream.io/chat/docs/react/message-delivery-and-read-status/'),
    'F19': ('Wikipedia, "Router (computing)"', 'https://en.wikipedia.org/wiki/Router_(computing)'),
    'F20': ('Wikipedia, "Data center"', 'https://en.wikipedia.org/wiki/Data_center'),
    'F21': ('Conta a partir de F9, F10, F13, F14 e F16: 1 + 2.360 + 5.900 + 88 + 1 = 8.350 km; '
            '8.348 km / 200.000 km/s + 2 km / 300.000 km/s = 41,7 ms', None),
    'F22': ('Wikipedia, "LTE (telecommunication)"', 'https://en.wikipedia.org/wiki/LTE_(telecommunication)'),
    'F23': ('Wikipedia, "Blinking"', 'https://en.wikipedia.org/wiki/Blinking'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'enviar': 'Apertou enviar', 'bits': 'Etapa 1: letras viram bits',
                'cadeado': 'Etapa 2: criptografia de ponta a ponta', 'pacotes': 'Etapa 3: os pacotes',
                'radio': 'Etapa 4: ondas de rádio até a torre', 'fibra': 'Etapa 5: fibra ótica e pulsos de luz',
                'rede': 'Etapa 6: de roteador em roteador', 'oceano': 'Etapa 7: o cabo no fundo do mar',
                'servidor': 'Etapa 8: o servidor', 'chegada': 'Etapa 9: os pacotes chegam',
                'abrir': 'Entregue e lida', 'conta': 'Quanto tempo leva?', 'resumo': 'Resumo'}

DESCRICAO = """O que acontece entre apertar ENVIAR e aparecer LIDA? Neste vídeo a gente segue uma mensagem de celular, com um "oi" e uma foto, de São Paulo até Lisboa: as letras viram números e bits, os bits são trancados com criptografia de ponta a ponta, a mensagem é cortada em pacotes, vai por rádio até a torre, vira pulsos de luz na fibra ótica, passa de roteador em roteador, atravessa o Atlântico num cabo submarino, para num data center e chega ao outro celular, que monta, destranca e mostra a mensagem.

Um contador mostra a distância e o tempo de viagem: uns 8.350 km em uns 42 milésimos de segundo.

Cada quadro é pixel art desenhada por código, e a música é original. Celulares e aplicativo são genéricos.

Capítulos
{capitulos}

Simplificado de propósito
- As distâncias são em linha reta (o mínimo possível). Os cabos de verdade fazem curvas, então o caminho é mais longo e demora mais. O tempo de 42 ms é só o da viagem do sinal; antenas, roteadores, servidor e filas somam mais.
- O caminho é um exemplo: São Paulo, Fortaleza, o cabo submarino até Sines e Lisboa. Os pacotes podem ir por outras rotas, e o servidor do aplicativo pode ficar em outro país. Colocamos o servidor perto de Lisboa para simplificar.
- A foto de 300 KB é um exemplo. Hoje os celulares usam Unicode (UTF-8), que para letras simples dá os mesmos números do ASCII; letras com acento ocupam 2 bytes.
- "Aceso = 1, apagado = 0" é a ideia básica; as redes de verdade usam jeitos mais elaborados de pôr bits na luz e no rádio.
- A criptografia aparece como um cadeado e uma chave. Na prática são cálculos com chaves de cada aparelho. O servidor não lê o conteúdo, mas vê para quem a mensagem vai.
- Quem tem 4G ou 5G no celular fala com a antena por rádio; mostramos uma torre só de cada lado.
- Os tiques de entregue e lida são genéricos; cada aplicativo mostra de um jeito.

Fontes
{fontes}

#internet #comofunciona #pixelart #celular #tecnologia #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O protagonista de
# cada cena fica em x ~60..240 (celular, fibra, cabo, data center); no mapa, a
# rota fica em x ~95..235.
PREFIXO = 'ep07-mensagem'
CORTES = [
    dict(id='c1', de=('bits', 0.0), ate=('bits', 28.8), x=60, gancho=['OI! EM', 'ZEROS E UNS'],
         titulo='Como o celular transforma letras em zeros e uns 💬',
         descricao='O celular não guarda letras, guarda números: O = 79, I = 73, ! = 33. E cada número vira 8 bits. Um emoji ocupa 4 bytes.'),
    dict(id='c2', de=('cadeado', 0.0), ate=('cadeado', 36.0), x=60, gancho=['QUEM LÊ A', 'MENSAGEM?'],
         titulo='Criptografia de ponta a ponta, explicada em 30 segundos 🔒',
         descricao='Antes de sair do celular, a mensagem é embaralhada com uma chave. Só quem envia e quem recebe conseguem ler. Nem a empresa do aplicativo.'),
    dict(id='c3', de=('fibra', 0.0), ate=('fibra', 33.6), x=60, gancho=['INTERNET', 'É LUZ'],
         titulo='A sua mensagem vira luz dentro de um fio de vidro 💡',
         descricao='Na fibra ótica, um laser pisca e os bits viram pulsos de luz. A fibra tem a grossura de um fio de cabelo e a luz anda a uns 200.000 km por segundo.'),
    dict(id='c4', de=('oceano', 0.0), ate=('oceano', 36.4), x=60, gancho=['UM CABO NO', 'FUNDO DO MAR'],
         titulo='A internet passa por cabos no fundo do mar 🌊',
         descricao='Um cabo submarino de 5.900 km liga Fortaleza a Portugal. Cabos assim levam 99% dos dados que cruzam os oceanos.'),
    dict(id='c5', de=('chegada', 7.6), ate=('chegada', 35.6), x=60, gancho=['FORA DE', 'ORDEM?'],
         titulo='Os pedaços da sua foto chegam fora de ordem 🧩',
         descricao='A foto viaja em mais de 200 pacotes. Eles chegam fora de ordem e o celular usa os números para montar tudo. Faltou um? Ele pede de novo.'),
    dict(id='c6', de=('conta', 0.0), ate=('conta', 28.8), x=96, gancho=['8.350 KM', 'EM 42 MS'],
         titulo='Quanto tempo uma mensagem leva para cruzar o oceano? ⏱️',
         descricao='De São Paulo a Lisboa em linha reta são uns 8.350 km. Pelo ar e pela fibra, o sinal leva uns 42 milésimos de segundo. Um piscar de olhos dura 100 a 150 ms.'),
]
