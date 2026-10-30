#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep24 (série FEITO DE PIXELS): Como funciona o Wi-Fi.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep24_motor.py` (cenas) e `ep24_desenho.py` (paleta, aparelhos, ondas, a
constelação 16-QAM, o painel).

A ideia: seguir UM pacote (um bloco de bits que brilha) do celular até o
roteador. Protagonista: o PACOTE Nº n. Objetivo que sobe na tela: o painel
da direita (frequência, comprimento de onda, bits por símbolo, sinal em dBm,
pacote nº).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

A constelação NÃO é desenhada à mão: `ep24_desenho.qam16()` monta o 16-QAM
com código de Gray (2 bits no eixo I, 2 no eixo Q; 00 -3, 01 -1, 11 +1,
10 +3) e confere, no import, que todo vizinho difere em 1 bit só. Os bits do
pacote viram pontos e cada ponto vira o pedaço de onda I cos - Q sen.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Wi-Fi: aparelhos trocam dados por ondas de rádio; usa mais as faixas de
      2,4 GHz (120 mm) e 5 GHz (60 mm), e a de 6 GHz nas gerações novas; a
      2,4 GHz também é usada por micro-ondas e sofre interferência; paredes,
      pilares e eletrodomésticos reduzem muito o alcance; metal afeta muito;
      água (como a das plantas) também; o 5 GHz é mais absorvido pelos
      materiais de construção e costuma alcançar menos; alcance de um ponto
      de acesso dentro de casa: uns 20 m; canais usados em half duplex: só um
      transmissor fala num canal de cada vez; um sinal ocupa pelo menos
      20 MHz; 1, 6 e 11 são os 3 canais que não se sobrepõem (América do
      Norte); EUA 11 canais, Europa 13, Japão 14; pacotes são recebidos por
      todas as estações sintonizadas no canal; CSMA/CA; o roteador sem fio
      junta ponto de acesso e roteador e liga ao modem; WPA2 (2004), seguro
      com senha forte; WPA3 anunciado em 2018. Wikipedia, "Wi-Fi".
  F2  Ondas de rádio são radiação eletromagnética; no vácuo andam na
      velocidade da luz; são irradiadas por cargas aceleradas, correntes que
      variam no tempo, nas antenas; comprimento inversamente proporcional à
      frequência. Wikipedia, "Radio wave".
  F3  A luz que o olho vê é uma parte muito pequena do espectro (cerca de
      380 a 760 nm); as ondas de rádio têm os maiores comprimentos.
      Wikipedia, "Electromagnetic spectrum".
  F4  Antena: o transmissor aplica corrente alternada; a antena irradia a
      energia como ondas de rádio, na velocidade da luz; na antena que
      recebe, o campo induz tensão e corrente. Wikipedia, "Antenna (radio)".
  F5  Velocidade da luz no vácuo: exatamente 299.792.458 m/s; toda radiação
      eletromagnética anda a essa velocidade. Wikipedia, "Speed of light".
  F6  Wi-Fi 6 (802.11ax): 1024-QAM; o Wi-Fi 6E acrescenta a faixa de 6 GHz.
      Wikipedia, "Wi-Fi 6" (IEEE 802.11ax).
  F7  A Anatel destinou em 25/02/2021 a faixa de 5,925 a 7,125 GHz (1,2 GHz)
      ao Wi-Fi 6E. O Povo, "Anatel destina toda a faixa de 6 GHz para super
      Wi-Fi" (25/02/2021).
  F8  QAM: muda a amplitude e a fase; o número de pontos é potência de 2 e
      dá os bits por símbolo; usada no Wi-Fi 802.11; com mais pontos eles
      ficam mais perto e o ruído atrapalha mais.
      Wikipedia, "Quadrature amplitude modulation".
  F9  Constelação: cada símbolo é um ponto; a distância até o centro é a
      amplitude; o ângulo é a fase; o ruído espalha os pontos e um ponto que
      cai na região de outro vira erro. Wikipedia, "Constellation diagram".
  F10 Código de Gray: pontos vizinhos da constelação diferem em 1 bit só, o
      que deixa a transmissão menos sensível ao ruído. Wikipedia, "Gray code".
  F11 802.11ac (Wi-Fi 5): 256-QAM; faixa de 5 GHz; 2013.
      Wikipedia, "IEEE 802.11ac-2013".
  F12 IEEE 802.11: faixas de 2,4, 5, 6 e 60 GHz; a de 2,4 GHz tem 14 canais
      a cada 5 MHz; CSMA/CA; quem recebe manda um ACK a quem enviou.
      Wikipedia, "IEEE 802.11".
  F13 Espaço livre: a potência se espalha e cai com o quadrado da distância
      (lei do inverso do quadrado). Wikipedia, "Free-space path loss".
  F14 dBm: nível de potência em decibéis em relação a 1 mW; 0 dBm = 1 mW;
      +10 dB = 10 vezes a potência; Wi-Fi: de -10 dBm (máximo recebido) a
      -100 dBm (mínimo). Wikipedia, "DBm".
  F15 Micro-ondas: em torno de 2,45 GHz; aquece pela água; às vezes
      interfere no Wi-Fi e no Bluetooth. Wikipedia, "Microwave oven".
  F16 CSMA/CA: só transmite com o canal livre; se ocupado, espera um tempo
      (geralmente sorteado); depois espera o ACK; sem ACK, supõe colisão e
      repete. Wikipedia, "Carrier-sense multiple access with collision avoidance".
  F17 WPA2 usa AES com chave de 128 bits; cada aparelho criptografa o
      tráfego; só protege de quem não tem a senha; WPA3 anunciado em janeiro
      de 2018. Wikipedia, "Wi-Fi Protected Access".
  F18 Contas: c / f (2,4 GHz -> 12,5 cm; 5 GHz -> 6,0 cm; 6 GHz -> 5,0 cm);
      2^4 = 16, 2^8 = 256, 2^10 = 1024; 10 m / c = 33 ns; 2 vezes a distância
      = 1/4 da potência = -6 dB; 2,4 GHz = 2,4 bilhões de ciclos por segundo.
  F19 O episódio "A jornada de uma mensagem de celular" (ep07 deste canal).

NÃO LIDAS (pedido de acesso expirou): gov.br/anatel (notícia da faixa de 6 GHz)
e wi-fi.org/discover-wi-fi/security. Os mesmos fatos vieram de F7, F1 e F17.
"""

TITULO = "Como funciona o Wi-Fi | Ondas de rádio, bits e a sua senha, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='drop'),                # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),               # 6 s
    dict(id='casa', gen='lofi', bars=10, papel='drop'),                 # 30 s
    dict(id='antena', gen='synthwave', bars=13, papel='drop'),          # 31,2 s
    dict(id='frequencia', gen='lofi', bars=14, papel='drop'),           # 42 s
    dict(id='bits', gen='house', bars=16, papel='drop', bpm=120),       # 32 s
    dict(id='qam', gen='synthwave', bars=16, papel='drop'),             # 38,4 s
    dict(id='pontos', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='distancia', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='paredes', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='microondas', gen='lofi', bars=8, papel='drop'),            # 24 s
    dict(id='canais', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='vez', gen='house', bars=18, papel='drop', bpm=120),        # 36 s
    dict(id='senha', gen='lofi', bars=10, papel='drop'),                # 30 s
    dict(id='internet', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                  # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "AGORA MESMO, O SEU CELULAR CONVERSA", "COM O ROTEADOR *SEM NENHUM FIO*.", ('F1',)),
        (6.2, 11.6, "SÃO PACOTES DE BITS VOANDO PELO AR.", "VAMOS SEGUIR *UM DELES*.", ('F1',)),
    ],
    'casa': [
        (0.5, 7.0, "CELULAR E ROTEADOR CONVERSAM POR", "*ONDAS DE RÁDIO*.", ('F1',)),
        (7.4, 14.4, "SÃO ONDAS *ELETROMAGNÉTICAS*,", "DA MESMA FAMÍLIA DA LUZ.", ('F2', 'F3')),
        (14.8, 21.8, "MAS O OLHO SÓ VÊ UMA FAIXA ESTREITA.", "AS DO WI-FI SÃO *INVISÍVEIS*.", ('F3',)),
        (22.2, 29.6, "ENTÃO, NESTE VÍDEO, A GENTE", "*DESENHA* AS ONDAS.", ()),
    ],
    'antena': [
        (0.5, 7.4, "DENTRO DA ANTENA DO ROTEADOR HÁ", "*ELÉTRONS* QUE PODEM SE MEXER.", ('F4',)),
        (7.8, 15.0, "O ROTEADOR EMPURRA ELES PARA CIMA", "E PARA BAIXO: *CORRENTE ALTERNADA*.", ('F4',)),
        (15.4, 22.6, "CARGA QUE BALANÇA SOLTA UMA *ONDA*", "QUE SAI VOANDO PELO ESPAÇO.", ('F2', 'F4')),
        (23.0, 30.8, "NO CELULAR, A ONDA BALANÇA OS", "ELÉTRONS DA ANTENA DELE: *SINAL*!", ('F4',)),
    ],
    'frequencia': [
        (0.5, 7.0, "*FREQUÊNCIA*: QUANTOS VAIVÉNS", "POR SEGUNDO. O WI-FI USA *2,4 GHZ*:", ('F1',)),
        (7.4, 14.0, "2,4 *BILHÕES* DE VAIVÉNS", "POR SEGUNDO!", ('F18',)),
        (14.4, 21.0, "A ONDA ANDA NA *VELOCIDADE DA LUZ*:", "299.792 KM POR SEGUNDO.", ('F2', 'F5')),
        (21.4, 28.0, "DE UMA CRISTA À OUTRA, A 2,4 GHZ:", "UNS *12,5 CM*. DESENHO EM ESCALA.", ('F1', 'F18')),
        (28.4, 35.0, "A *5 GHZ*, A ONDA É MAIS CURTA: 6 CM.", "A *6 GHZ* (WI-FI 6E), 5 CM.", ('F1', 'F6', 'F18')),
        (35.4, 41.6, "EM 2021, A ANATEL LIBEROU OS 6 GHZ.", "EM 2027, O WI-FI FICA COM *UMA PARTE*.", ('F7', 'F20')),
    ],
    'bits': [
        (0.5, 7.4, "UMA ONDA QUE SÓ BALANÇA NÃO DIZ", "NADA. PARA LEVAR BITS, ELA *MUDA*.", ('F8',)),
        (7.8, 15.4, "PODE MUDAR A *ALTURA* (AMPLITUDE):", "ALTA = 1, BAIXA = 0.", ('F8',)),
        (15.8, 23.4, "OU O *PASSO* (FASE): A ONDA COMEÇA", "SUBINDO OU DESCENDO.", ('F8',)),
        (23.8, 31.6, "CADA PEDAÇO DE ONDA É UM *SÍMBOLO*.", "AQUI, UM A CADA 2 BATIDAS.", ()),
    ],
    'qam': [
        (0.5, 7.4, "MUDANDO ALTURA E FASE JUNTAS, CADA", "SÍMBOLO VIRA UM *PONTO* NESTE MAPA.", ('F8', 'F9')),
        (7.8, 14.8, "LONGE DO CENTRO: ONDA MAIS *ALTA*.", "O *ÂNGULO* DO PONTO É A FASE.", ('F9',)),
        (15.2, 22.6, "16 PONTOS: *16-QAM*. 16 = 2X2X2X2,", "ENTÃO CADA SÍMBOLO LEVA *4 BITS*.", ('F8', 'F18')),
        (23.0, 30.4, "VIZINHOS DIFEREM EM *1 BIT* SÓ:", "UM ERRO PEQUENO ESTRAGA POUCO.", ('F10',)),
        (30.8, 38.0, "O PACOTE SAI DO CELULAR ASSIM:", "*4 BITS POR VEZ*.", ('F8',)),
    ],
    'pontos': [
        (0.5, 7.4, "O WI-FI 5 USA ATÉ *256-QAM*:", "8 BITS POR SÍMBOLO.", ('F11', 'F18')),
        (7.8, 15.0, "O WI-FI 6 CHEGA A *1024-QAM*:", "10 BITS POR SÍMBOLO.", ('F6', 'F12', 'F18')),
        (15.4, 22.4, "MAS OS PONTOS FICAM *APERTADOS*, E", "O RUÍDO ESPALHA CADA UM.", ('F8', 'F9')),
        (22.8, 29.6, "SE O PONTO CAI NA CASA DO VIZINHO:", "*ERRO*. LONGE, USAM-SE MENOS PONTOS.", ('F8', 'F9')),
    ],
    'distancia': [
        (0.5, 6.4, "O PACOTE Nº 1 SAI DO CELULAR NA", "VELOCIDADE DA LUZ.", ('F2', 'F5')),
        (6.6, 12.4, "10 METROS EM *33 NANOSSEGUNDOS*:", "33 BILIONÉSIMOS DE SEGUNDO.", ('F18',)),
        (12.6, 18.4, "A ONDA SE ESPALHA PARA TODO LADO.", "DOBROU A DISTÂNCIA? CHEGA *1/4*.", ('F13', 'F18')),
        (18.6, 24.4, "O SINAL SE MEDE EM *DBM*:", "0 DBM = 1 MILIWATT.", ('F14',)),
        (24.6, 30.2, "CADA *10 DB* A MENOS: *10 VEZES*", "MENOS POTÊNCIA.", ('F14',)),
        (30.4, 35.8, "NO WI-FI, DE UNS *-10 DBM* (PERTO)", "ATÉ UNS *-100 DBM* (QUASE NADA).", ('F14',)),
    ],
    'paredes': [
        (0.5, 7.4, "NO CAMINHO HÁ *PAREDES*. CADA UMA", "ROUBA UM POUCO DO SINAL.", ('F1',)),
        (7.8, 14.4, "*METAL* É O PIOR: A GELADEIRA", "FAZ SOMBRA NO SINAL.", ('F1',)),
        (14.8, 21.4, "A *ÁGUA* TAMBÉM SEGURA A ONDA:", "ATÉ AS PLANTAS ATRAPALHAM.", ('F1',)),
        (21.8, 28.4, "O 5 GHZ É MAIS ABSORVIDO PELAS", "PAREDES: VAI *MENOS LONGE*.", ('F1',)),
        (28.8, 35.6, "DENTRO DE CASA, UM ROTEADOR", "ALCANÇA UNS *20 METROS*.", ('F1',)),
    ],
    'microondas': [
        (0.5, 7.4, "O *MICRO-ONDAS* TAMBÉM USA ONDAS:", "PERTO DE *2,45 GHZ*.", ('F15',)),
        (7.8, 15.4, "ELAS AGITAM A ÁGUA DA COMIDA.", "É ASSIM QUE ELA ESQUENTA.", ('F15',)),
        (15.8, 23.6, "É A FAIXA DO WI-FI DE 2,4 GHZ:", "ÀS VEZES O FORNO *ATRAPALHA*.", ('F1', 'F15')),
    ],
    'canais': [
        (0.5, 7.4, "A FAIXA DE 2,4 GHZ É DIVIDIDA EM", "*14 CANAIS*, UM A CADA 5 MHZ.", ('F12',)),
        (7.8, 15.0, "MAS UM SINAL OCUPA *20 MHZ*:", "CANAIS VIZINHOS SE ATROPELAM.", ('F1',)),
        (15.4, 22.4, "NOS EUA, SÓ 3 NÃO SE TOCAM:", "OS CANAIS *1, 6 E 11*.", ('F1',)),
        (22.8, 29.6, "CADA PAÍS LIBERA ALGUNS: OS EUA, 11;", "A EUROPA, 13; O JAPÃO, OS 14.", ('F1',)),
    ],
    'vez': [
        (0.5, 6.4, "NUM CANAL, SÓ *UM* FALA DE CADA", "VEZ. OS APARELHOS SE REVEZAM.", ('F1',)),
        (6.6, 12.4, "ANTES DE FALAR, CADA UM *ESCUTA*:", "O AR ESTÁ LIVRE?", ('F16',)),
        (12.6, 18.4, "OCUPADO? ESPERA UM TEMPO *SORTEADO*", "E ESCUTA DE NOVO.", ('F16',)),
        (18.6, 24.4, "LIVRE: MANDA O PACOTE. O NOME", "DISSO É *CSMA/CA*.", ('F12', 'F16')),
        (24.6, 30.2, "CHEGOU? O ROTEADOR RESPONDE", "*ACK*: RECEBI!", ('F12', 'F16')),
        (30.4, 35.8, "SEM ACK, O CELULAR ACHA QUE DEU", "*COLISÃO* E MANDA DE NOVO.", ('F16',)),
    ],
    'senha': [
        (0.5, 7.4, "A ONDA NÃO TEM DONO: QUEM ESTÁ NO", "MESMO CANAL TAMBÉM A *RECEBE*.", ('F1',)),
        (7.8, 15.0, "POR ISSO OS BITS SÃO *EMBARALHADOS*", "COM UMA CHAVE: *CRIPTOGRAFIA*.", ('F17',)),
        (15.4, 22.4, "SEM A *SENHA* DA REDE, O VIZINHO", "SÓ VÊ BITS SEM SENTIDO.", ('F17',)),
        (22.8, 29.6, "O *WPA2* É DE 2004. O *WPA3*,", "ANUNCIADO EM 2018, É O SUCESSOR.", ('F1', 'F17')),
    ],
    'internet': [
        (0.5, 7.4, "O ROTEADOR TIRA O PACOTE DA ONDA", "E MANDA PELO *CABO* ATÉ O MODEM.", ('F1',)),
        (7.8, 15.4, "DALI ELE SEGUE PELA *INTERNET*:", "FIBRAS, CABOS NO MAR, SERVIDORES.", ('F19',)),
        (15.8, 23.6, "ESSA VIAGEM ESTÁ NO VÍDEO *A JORNADA*", "*DE UMA MENSAGEM DE CELULAR*.", ('F19',)),
    ],
    'resumo': [
        (0.5, 9.4, "ELÉTRONS BALANÇAM, A ONDA VOA E", "CADA SÍMBOLO LEVA DE *1 A 10 BITS*.", ('F4', 'F8', 'F18')),
        (9.8, 19.4, "PAREDES ENFRAQUECEM, CADA UM FALA", "NA SUA VEZ E CADA PACOTE GANHA *ACK*.", ('F1', 'F16')),
        (19.8, 29.6, "E TUDO ISSO EMBARALHADO PELA", "*SENHA* DA SUA REDE.", ('F17',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Wi-Fi"', 'https://en.wikipedia.org/wiki/Wi-Fi'),
    'F2': ('Wikipedia, "Radio wave"', 'https://en.wikipedia.org/wiki/Radio_wave'),
    'F3': ('Wikipedia, "Electromagnetic spectrum"', 'https://en.wikipedia.org/wiki/Electromagnetic_spectrum'),
    'F4': ('Wikipedia, "Antenna (radio)"', 'https://en.wikipedia.org/wiki/Antenna_(radio)'),
    'F5': ('Wikipedia, "Speed of light"', 'https://en.wikipedia.org/wiki/Speed_of_light'),
    'F6': ('Wikipedia, "Wi-Fi 6" (IEEE 802.11ax)', 'https://en.wikipedia.org/wiki/IEEE_802.11ax'),
    'F7': ('O Povo, "Anatel destina toda a faixa de 6 GHz para super Wi-Fi" (25/02/2021)',
           'https://www.opovo.com.br/noticias/economia/2021/02/25/anatel-destina-toda-a-faixa-de-6-ghz-para-super-wi-fi.html'),
    'F8': ('Wikipedia, "Quadrature amplitude modulation"', 'https://en.wikipedia.org/wiki/Quadrature_amplitude_modulation'),
    'F9': ('Wikipedia, "Constellation diagram"', 'https://en.wikipedia.org/wiki/Constellation_diagram'),
    'F10': ('Wikipedia, "Gray code"', 'https://en.wikipedia.org/wiki/Gray_code'),
    'F11': ('Wikipedia, "IEEE 802.11ac-2013"', 'https://en.wikipedia.org/wiki/IEEE_802.11ac-2013'),
    'F12': ('Wikipedia, "IEEE 802.11"', 'https://en.wikipedia.org/wiki/IEEE_802.11'),
    'F13': ('Wikipedia, "Free-space path loss"', 'https://en.wikipedia.org/wiki/Free-space_path_loss'),
    'F14': ('Wikipedia, "DBm"', 'https://en.wikipedia.org/wiki/DBm'),
    'F15': ('Wikipedia, "Microwave oven"', 'https://en.wikipedia.org/wiki/Microwave_oven'),
    'F16': ('Wikipedia, "Carrier-sense multiple access with collision avoidance"',
            'https://en.wikipedia.org/wiki/Carrier-sense_multiple_access_with_collision_avoidance'),
    'F17': ('Wikipedia, "Wi-Fi Protected Access"', 'https://en.wikipedia.org/wiki/Wi-Fi_Protected_Access'),
    'F18': ('Contas: velocidade da luz / frequência; 2^4, 2^8, 2^10; 10 m / velocidade da luz; inverso do quadrado', None),
    'F20': ('Teletime, 13/08/2026: Anatel limita o Wi-Fi à parte de baixo da faixa de 6 GHz (5.925 a 6.425 MHz) a partir de 01/03/2027', 'https://teletime.com.br/13/08/2026/anatel-wi-fi-banda-inferior-6-ghz/'),
    'F19': ('NOSSO MUNDO PIXEL, "A jornada de uma mensagem de celular" (episódio 7)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'casa': 'Ondas de rádio invisíveis', 'antena': 'Como a antena faz a onda',
                'frequencia': '2,4, 5 e 6 GHz', 'bits': 'Bits dentro da onda', 'qam': 'O mapa 16-QAM',
                'pontos': '256 e 1024-QAM', 'distancia': 'Velocidade da luz e dBm',
                'paredes': 'Paredes, metal e água', 'microondas': 'O micro-ondas atrapalha?',
                'canais': 'Os canais', 'vez': 'Cada um na sua vez (CSMA/CA e ACK)',
                'senha': 'A senha embaralha o rádio', 'internet': 'Do roteador para a internet',
                'resumo': 'Resumo'}

DESCRICAO = """Como funciona o Wi-Fi? A gente segue um pacote de bits do celular até o roteador. Primeiro, a onda: elétrons balançando na antena soltam ondas de rádio, da mesma família da luz, só que invisíveis, a 2,4, 5 ou 6 GHz. Depois, como os bits entram na onda: mudando a altura e a fase, cada símbolo vira um ponto no mapa 16-QAM e leva 4 bits (o Wi-Fi 5 vai a 256-QAM e o Wi-Fi 6 a 1024-QAM). No caminho, a onda enfraquece com a distância e com paredes, metal e água, o micro-ondas atrapalha, os canais se atropelam, os aparelhos se revezam (CSMA/CA) e cada pacote ganha um ACK. No fim, a senha embaralha tudo (WPA2 e WPA3) e o roteador manda o pacote para a internet.

Cada quadro é pixel art desenhada por código, e a música é original. O mapa 16-QAM é calculado de verdade (código de Gray, conferido no programa), e os símbolos e os pacotes saem nas batidas da música.

Capítulos
{capitulos}

Simplificado de propósito
- Tudo na tela está em câmera lenta: a onda de 2,4 GHz vai e volta 2,4 bilhões de vezes por segundo; o desenho mostra poucas por segundo. Os números do painel (GHz, cm, bits por símbolo) são os de verdade.
- O Wi-Fi de verdade não manda um símbolo de cada vez numa onda só: ele usa OFDM, dezenas a milhares de ondas vizinhas ao mesmo tempo, cada uma com o seu símbolo QAM. Aqui mostramos uma.
- No Wi-Fi 6 (OFDMA), vários aparelhos podem falar ao mesmo tempo em pedaços do canal.
- Longe do roteador, o Wi-Fi cai para modos mais simples, de 1 ou 2 bits por símbolo.
- Os valores de sinal em dBm do painel são exemplos (a conta do inverso do quadrado a partir de -40 dBm a 1 m, e um desconto por parede e por obstáculo escolhido para o desenho). Cada casa, parede e aparelho dá um número diferente.
- No capítulo da bolha, a onda está no espaço livre; dentro de casa os reflexos mudam a conta.
- Os canais aparecem desenhados um a cada 5 MHz, como diz a norma; quais podem ser usados depende do país.
- O "embaralhar" da senha é desenhado como uma troca de bits com uma chave. O WPA2 usa a cifra AES com chave de 128 bits, bem mais complicada; a senha não é a chave, ela serve para chegar até ela.
- O CSMA/CA tem mais detalhes (intervalos fixos entre quadros, o RTS/CTS opcional, a espera que dobra a cada colisão); aqui ficaram só escutar, esperar um tempo sorteado, falar e esperar o ACK.

Fontes
{fontes}

#wifi #comofunciona #pixelart #tecnologia #internet #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. A antena fica em
# x 30..200; o mapa 16-QAM em 140..300; a régua da onda em 20..200; a casa
# das paredes em 10..190; a fila do CSMA/CA em 20..200.
PREFIXO = 'ep24-wifi'
CORTES = [
    dict(id='c1', de=('antena', 0.0), ate=('antena', 30.8), x=26, gancho=['COMO NASCE', 'O WI-FI'],
         titulo='Como a antena do roteador faz a onda do Wi-Fi 📶',
         descricao='Elétrons balançam para cima e para baixo dentro da antena e soltam uma onda de rádio, que voa na velocidade da luz até o celular e balança os elétrons da antena dele.'),
    dict(id='c2', de=('frequencia', 14.4), ate=('frequencia', 41.6), x=20, gancho=['A ONDA DO', 'WI-FI: 12,5 CM'],
         titulo='A onda do Wi-Fi em escala: 12,5 cm',
         descricao='A 2,4 GHz, a distância entre duas cristas da onda do Wi-Fi é de uns 12,5 cm (velocidade da luz dividida pela frequência). A 5 GHz, 6 cm; a 6 GHz, 5 cm.'),
    dict(id='c3', de=('qam', 0.0), ate=('qam', 38.0), x=128, gancho=['4 BITS EM', '1 PEDAÇO'],
         titulo='Como o Wi-Fi põe bits numa onda: o mapa 16-QAM',
         descricao='Mudando a altura e a fase da onda, cada símbolo vira um dos 16 pontos do mapa e leva 4 bits. Vizinhos diferem em 1 bit só (código de Gray).'),
    dict(id='c4', de=('paredes', 0.0), ate=('paredes', 35.6), x=14, gancho=['O QUE MATA', 'O WI-FI?'],
         titulo='O que enfraquece o sinal do Wi-Fi em casa 🧱',
         descricao='Paredes, metal (a geladeira!) e água seguram a onda. O 5 GHz é mais absorvido pelas paredes e vai menos longe; dentro de casa um roteador alcança uns 20 metros.'),
    dict(id='c5', de=('microondas', 0.0), ate=('microondas', 23.6), x=28, gancho=['MICRO-ONDAS', 'X WI-FI'],
         titulo='O micro-ondas atrapalha o Wi-Fi? 🍲',
         descricao='O forno usa ondas perto de 2,45 GHz para agitar a água da comida. É a mesma faixa do Wi-Fi de 2,4 GHz, e às vezes ele atrapalha.'),
    dict(id='c6', de=('vez', 0.0), ate=('vez', 35.8), x=20, gancho=['UM DE CADA', 'VEZ!'],
         titulo='Como os aparelhos dividem o Wi-Fi: escutar antes de falar',
         descricao='Num canal, só um aparelho fala de cada vez. Cada um escuta, espera um tempo sorteado se estiver ocupado, manda o pacote e espera o ACK do roteador.'),
]
