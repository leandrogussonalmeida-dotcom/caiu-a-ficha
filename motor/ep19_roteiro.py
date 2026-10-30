#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep19 (série A JORNADA): A jornada de um contêiner pelo porto.

A ideia: seguir UM contêiner de 20 pés (laranja, o protagonista) da fábrica
até o outro lado do mar: lacre, portão com câmeras, pátio (RTG), guindaste
de cais com o spreader e as travas giratórias, plano de carga (baia,
fileira, camada; pesado embaixo), amarração, viagem e chegada. Objetivo que
sobe na tela: "ETAPA 4 DE 8" e o contador de MOVIMENTOS DE GUINDASTE do
nosso contêiner (1 a 6). O código pintado nele, MPXU 190426 5, é INVENTADO
para o vídeo, mas segue o padrão ISO 6346 e o dígito verificador sai da
conta de verdade (vira um quebra-cabeça no capítulo do código). Navio,
guindastes, caminhão e portos são genéricos; nenhum nome ou logotipo de
empresa de navegação.

Desenho em `ep19_motor.py` (cenas) e `ep19_desenho.py` (paleta, contêiner,
caminhão, guindastes, navio, painel).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Navio porta-contêineres: guias de célula (estruturas verticais de metal
      no porão); tampas de escotilha com mais contêineres por cima; amarração
      com cabo, barras rígidas ou correntes, esticadores (turnbuckles); trava
      giratória encaixada no furo da peça de canto e girada; velocidade típica
      de 16 a 25 nós; ~90% da carga não-granel do mundo vai em navio de
      contêiner; coordenadas baia / fileira (pares a bombordo, ímpares a
      boreste, crescendo a partir do centro) / camada (a 1ª no fundo do porão).
      Wikipedia, "Container ship".
  F2  Contêiner de 20 pés: 6,058 x 2,438 x 2,591 m; 40 pés: 12,192 m; tara
      ~2.200 kg (20 pés); máximo bruto 30.480 kg na tabela e 36.000 kg pela
      ISO 668:2013 Amd 1; aço corrugado (CorTen), a corrugação dá rigidez;
      8 peças de canto que aguentam o empilhamento; TEU = um contêiner de
      20 pés; navios ultragrandes empilham 10 ou 11 de altura no convés.
      Wikipedia, "Intermodal container".
  F3  ISO 6346: dono (3 letras, registradas no BIC) + categoria (U = contêiner
      de carga) + série de 6 dígitos + dígito verificador; letras viram
      números a partir de A=10 pulando 11, 22, 33; pesos 2^posição (1, 2, 4
      ... 512); soma, divide por 11, o resto é o dígito (10 vira 0); o dígito
      valida o dono e a série. Tipo 22G1 = 20 pés, 8 pés e 6 pol. de altura,
      uso geral. Wikipedia, "ISO 6346".
  F4  Trava giratória (twistlock): a peça de canto tem um furo oval; o pino
      entra e a parte de cima gira 90°, aí não sai mais; usada em guindastes,
      carretas e no convés. Wikipedia, "Twistlock".
  F5  Lacre de contêiner: indica violação; tem número único que vai para o
      registro. New Zealand Customs Service, "Seals for sea freight".
  F6  Portão automático: câmeras leem o código do contêiner, a placa,
      detectam o lacre e avarias; os dados são conferidos com o manifesto.
      ABB, "Gate solutions" (OCR).
  F7  RTG: pórtico sobre pneus que empilha contêineres no pátio, passando por
      cima de várias faixas, uma delas para o caminhão; no pátio, os de
      exportação esperam o navio. Wikipedia, "Rubber tyred gantry crane".
  F8  Guindaste de cais: estrutura que anda em trilhos ao longo do cais; o
      trole corre pela lança; o operador vai numa cabine pendurada no trole;
      em vez de gancho, um spreader que trava nas 4 peças de canto com
      travas giratórias. Wikipedia, "Container crane".
  F9  Produtividade: média da Austrália ~28,1 contêineres por hora por
      guindaste; média mundial ~25 para navios de ~13.500 TEU; os melhores
      portos australianos ~30. Shipping Australia, 05/11/2021.
  F10 Conta (F9): 30 por hora = 1 a cada 2 minutos (120 s); no capítulo do
      ritmo, 1 movimento por compasso de 2 s (house a 120 bpm) = 60x mais
      rápido.
  F11 Plano de carga (bay plan): baias da proa para a popa, ímpares para
      20 pés e pares para 40 pés; camadas numeradas de baixo para cima;
      peso bem distribuído, o pesado embaixo do leve ("evitar inversão de
      peso"). Wikipedia, "Bay plan".
  F12 1 nó = 1 milha náutica por hora = 1,852 km/h (16 nós = 29,6 km/h,
      25 nós = 46,3 km/h). Wikipedia, "Knot (unit)".
  F13 Maiores porta-contêineres: 24.346 TEU, 399,9 m x 61,3 m (2023).
      Wikipedia, "List of largest container ships".
  F14 Conta (F2, F13): 400 m / 6,058 m = 66 contêineres de 20 pés em fila.
  F15 Santos (SP) movimentou 5,4 milhões de TEU em 2024 (+14,7%), o maior da
      América Latina em contêineres (ranking Lloyd's List).
      Agência iNFRA, 03/09/2025.
  F16 Conta (F2, F15): 5,4 milhões x 6,058 m = 32.713 km; 5,4 milhões / 366
      dias (2024) = 14.754 TEU por dia.
"""

TITULO = "A jornada de um contêiner pelo porto | Da fábrica ao navio em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='caixa', gen='lofi', bars=12, papel='drop'),           # 36 s
    dict(id='codigo', gen='lofi', bars=14, papel='drop'),          # 42 s
    dict(id='fabrica', gen='lofi', bars=9, papel='drop'),          # 27 s
    dict(id='portao', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='patio', gen='lofi', bars=11, papel='drop'),           # 33 s
    dict(id='guindaste', gen='synthwave', bars=15, papel='drop'),  # 36 s
    dict(id='ritmo', gen='house', bars=12, papel='drop', bpm=120),  # 24 s
    dict(id='plano', gen='lofi', bars=12, papel='drop'),           # 36 s
    dict(id='amarracao', gen='lofi', bars=10, papel='drop'),       # 30 s
    dict(id='viagem', gen='synthwave', bars=14, papel='drop'),     # 33,6 s
    dict(id='gigantes', gen='lofi', bars=10, papel='break'),       # 30 s
    dict(id='chegada', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='santos', gen='lofi', bars=9, papel='break'),          # 27 s
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),           # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 6.0, "TIRANDO GRÃO, MINÉRIO E PETRÓLEO,", "*90%* DA CARGA VIAJA EM CONTÊINER.", ('F1',)),
        (6.2, 11.6, "HOJE VAMOS SEGUIR *UMA* DESSAS", "CAIXAS, DA FÁBRICA ATÉ O NAVIO.", ()),
    ],
    'caixa': [
        (0.5, 6.4, "ESTE É O NOSSO *CONTÊINER*: UMA", "CAIXA DE AÇO DE TAMANHO PADRÃO.", ('F2',)),
        (6.6, 12.6, "O DE *20 PÉS*: 6,06 M DE COMPRIMENTO,", "2,44 M DE LARGURA E 2,59 M DE ALTURA.", ('F2',)),
        (12.8, 18.8, "AS PAREDES SÃO DE *AÇO CORRUGADO*:", "AS DOBRAS DEIXAM A CHAPA MAIS FIRME.", ('F2',)),
        (19.0, 25.0, "NOS 8 CANTOS, PEÇAS DE AÇO COM UM", "*FURO OVAL*: É POR ALI QUE ELE É PRESO.", ('F2', 'F4')),
        (25.2, 30.6, "VAZIO, PESA UNS *2.200 KG*. CHEIO,", "PODE PASSAR DE *30 TONELADAS*.", ('F2',)),
        (30.8, 35.6, "O DE *40 PÉS* TEM O DOBRO. A MEDIDA", "É O *TEU*: UM CONTÊINER DE 20 PÉS.", ('F2',)),
    ],
    'codigo': [
        (0.5, 6.4, "TODO CONTÊINER TEM UM *CÓDIGO*.", "O NOSSO É INVENTADO: MPXU 190426 5.", ('F3',)),
        (6.6, 12.6, "3 LETRAS DO *DONO*, A LETRA *U*", "(CONTÊINER DE CARGA) E 6 NÚMEROS.", ('F3',)),
        (12.8, 18.8, "O ÚLTIMO É O *DÍGITO VERIFICADOR*:", "UMA CONTA QUE CONFERE O RESTO.", ('F3',)),
        (19.0, 24.6, "TENTE COM A GENTE: CADA LETRA VIRA", "UM NÚMERO (A=10, B=12, PULA O 11).", ('F3',)),
        (24.8, 30.6, "VEZES 1, 2, 4, 8... SEMPRE O DOBRO.", "SOMANDO TUDO: *4.878*.", ('F3',)),
        (30.8, 36.4, "DIVIDE POR 11: SOBRA *5*.", "O DÍGITO É 5. *A CONTA FECHA!*", ('F3',)),
        (36.6, 41.6, "E O TIPO: *22G1* = 20 PÉS, 2,59 M", "DE ALTURA, CARGA GERAL.", ('F3',)),
    ],
    'fabrica': [
        (0.5, 6.6, "ETAPA 1: NA *FÁBRICA*, O CONTÊINER", "CHEGA VAZIO EM CIMA DE UM CAMINHÃO.", ()),
        (6.8, 13.0, "A CARGA ENTRA PELAS PORTAS DO FUNDO,", "CAIXA POR CAIXA, ATÉ ENCHER.", ()),
        (13.2, 19.6, "PORTAS FECHADAS, ELE GANHA UM *LACRE*", "COM NÚMERO ÚNICO.", ('F5',)),
        (19.8, 26.4, "SE ALGUÉM ABRIR NO CAMINHO,", "O *LACRE ROMPIDO* DENUNCIA.", ('F5',)),
    ],
    'portao': [
        (0.5, 6.6, "ETAPA 2: O *PORTÃO* DO TERMINAL.", "O CAMINHÃO PASSA DEVAGAR.", ()),
        (6.8, 13.0, "CÂMERAS LEEM O *CÓDIGO*, A PLACA", "E PROCURAM *AVARIAS*.", ('F6',)),
        (13.2, 19.4, "E CONFEREM SE O *LACRE* ESTÁ LÁ.", "TUDO É COMPARADO COM A RESERVA.", ('F6',)),
        (19.6, 25.6, "O *DÍGITO VERIFICADOR* CONFIRMA", "QUE A LEITURA DO CÓDIGO ESTÁ CERTA.", ('F3',)),
        (25.8, 29.9, "CANCELA ABERTA. PODE ENTRAR.", "", ()),
    ],
    'patio': [
        (0.5, 6.6, "ETAPA 3: O *PÁTIO*. AQUI O NOSSO", "ESPERA O NAVIO CHEGAR.", ('F7',)),
        (6.8, 13.0, "UM *PÓRTICO SOBRE PNEUS* (RTG) PASSA", "POR CIMA DAS FILEIRAS DE CAIXAS.", ('F7',)),
        (13.2, 19.4, "ELE BAIXA O *SPREADER*, TRAVA NOS", "4 CANTOS DE CIMA E LEVANTA.", ('F4', 'F8')),
        (19.6, 26.0, "E EMPILHA: *MOVIMENTO 1*. VAMOS", "CONTAR CADA VEZ QUE ELE VOA.", ()),
        (26.2, 32.6, "O NAVIO ATRACOU! O RTG TIRA O", "NOSSO DA PILHA: *MOVIMENTO 2*.", ()),
    ],
    'guindaste': [
        (0.5, 6.4, "ETAPA 4: O *GUINDASTE DE CAIS*. ELE", "ANDA EM TRILHOS AO LONGO DO CAIS.", ('F8',)),
        (6.6, 12.4, "UM *TROLE* CORRE PELA LANÇA. O", "OPERADOR VAI NUMA CABINE PENDURADA.", ('F8',)),
        (12.6, 18.4, "O SPREADER DESCE E ENCAIXA OS PINOS", "NOS *4 FUROS OVAIS* DE CIMA.", ('F4', 'F8')),
        (18.6, 24.4, "CADA PINO GIRA *90°* E NÃO SAI MAIS:", "É A *TRAVA GIRATÓRIA* (TWISTLOCK).", ('F4',)),
        (24.6, 30.4, "SOBE, ATRAVESSA E DESCE NO NAVIO:", "*MOVIMENTO 3*.", ()),
        (30.6, 35.6, "UM GUINDASTE FAZ UNS *25 A 30*", "MOVIMENTOS POR HORA.", ('F9',)),
    ],
    'ritmo': [
        (0.5, 7.6, "AGORA NO RITMO: *UM MOVIMENTO*", "*POR COMPASSO* DA MÚSICA.", ()),
        (7.8, 15.6, "30 POR HORA = 1 A CADA 2 MINUTOS.", "AQUI ESTÁ *60 VEZES MAIS RÁPIDO*.", ('F10',)),
        (15.8, 23.6, "CADA *CLIQUE* É O SPREADER TRAVANDO", "OU SOLTANDO OS 4 CANTOS.", ('F8',)),
    ],
    'plano': [
        (0.5, 6.4, "ETAPA 5: NADA VAI A ESMO.", "EXISTE UM *PLANO DE CARGA*.", ('F11',)),
        (6.6, 12.4, "CADA VAGA TEM 3 NÚMEROS: *BAIA*,", "*FILEIRA* E *CAMADA*.", ('F1',)),
        (12.6, 18.4, "BAIA: DA FRENTE PARA TRÁS. ÍMPAR É", "VAGA DE 20 PÉS; PAR, DE 40 PÉS.", ('F11',)),
        (18.6, 24.4, "FILEIRA: DO MEIO PARA OS LADOS.", "CAMADA: DE BAIXO PARA CIMA.", ('F1', 'F11')),
        (24.6, 30.4, "REGRA DE OURO: *PESADO EMBAIXO*,", "LEVE EM CIMA.", ('F11',)),
        (30.6, 35.6, "A VAGA DO NOSSO: BAIA *13*,", "FILEIRA *02*, CAMADA *6*.", ()),
    ],
    'amarracao': [
        (0.5, 7.0, "ETAPA 6: NO PORÃO, *GUIAS DE CÉLULA*", "(TRILHOS EM PÉ) SEGURAM AS PILHAS.", ('F1',)),
        (7.2, 14.4, "*TAMPAS DE ESCOTILHA* FECHAM O", "PORÃO. POR CIMA, MAIS CAIXAS.", ('F1',)),
        (14.6, 21.8, "ENTRE UMA CAIXA E OUTRA, *TRAVAS*", "*GIRATÓRIAS* PRENDEM OS CANTOS.", ('F1', 'F4')),
        (22.0, 29.6, "E *BARRAS* COM *ESTICADOR* PRENDEM", "AS PILHAS DO CONVÉS AO NAVIO.", ('F1',)),
    ],
    'viagem': [
        (0.5, 7.0, "ETAPA 7: A *VIAGEM*. BEM PRESO,", "O NOSSO CRUZA O OCEANO.", ()),
        (7.2, 14.0, "NAVIOS ASSIM ANDAM A *16 A 25 NÓS*:", "DE 30 A 46 KM/H.", ('F1', 'F12')),
        (14.2, 21.0, "PARECE POUCO, MAS ELE NÃO PARA:", "DIA E NOITE, DIAS SEGUIDOS.", ()),
        (21.2, 27.4, "NO MAR, O NAVIO *BALANÇA*.", "AS AMARRAS SEGURAM AS PILHAS.", ('F1',)),
        (27.6, 33.2, "E O NOSSO NAVIO É MÉDIO.", "OS MAIORES SÃO *GIGANTES*...", ()),
    ],
    'gigantes': [
        (0.5, 7.0, "OS MAIORES NAVIOS DE HOJE LEVAM", "*24.000 TEU*: 24 MIL CAIXAS DE 20 PÉS.", ('F13',)),
        (7.2, 14.0, "TÊM *400 M* DE COMPRIMENTO", "E 61 M DE LARGURA.", ('F13',)),
        (14.2, 21.0, "*66 CONTÊINERES* DE 20 PÉS EM FILA", "CABEM NO COMPRIMENTO DE UM DELES.", ('F14',)),
        (21.2, 29.4, "NO CONVÉS, AS PILHAS CHEGAM A", "*10 OU 11* CAIXAS DE ALTURA.", ('F2',)),
    ],
    'chegada': [
        (0.5, 6.6, "ETAPA 8: A *CHEGADA*. TUDO DE NOVO,", "SÓ QUE AO CONTRÁRIO.", ()),
        (6.8, 13.0, "SOLTAM AS AMARRAS. O GUINDASTE TIRA", "O NOSSO DO NAVIO: *MOVIMENTO 4*.", ('F1',)),
        (13.2, 19.4, "NO PÁTIO: *MOVIMENTO 5*. DEPOIS,", "PARA O CAMINHÃO: *MOVIMENTO 6*.", ()),
        (19.6, 26.0, "NO PORTÃO DE SAÍDA, O CÓDIGO E O", "*LACRE* SÃO CONFERIDOS DE NOVO.", ('F6',)),
        (26.2, 31.0, "LACRE INTEIRO. AS PORTAS ABREM:", "*A CARGA CHEGOU*.", ('F5',)),
        (31.2, 35.6, "VAZIO, O NOSSO CONTÊINER ESPERA", "A *PRÓXIMA VIAGEM*.", ()),
    ],
    'santos': [
        (0.5, 7.0, "E NO BRASIL? O *PORTO DE SANTOS* (SP)", "LIDERA A AMÉRICA LATINA.", ('F15',)),
        (7.2, 14.0, "EM 2024 PASSARAM POR LÁ", "*5,4 MILHÕES DE TEU*.", ('F15',)),
        (14.2, 20.6, "EM FILA, ESSAS CAIXAS DE 20 PÉS", "DARIAM UNS *32.700 KM*.", ('F16',)),
        (20.8, 26.6, "É UMA MÉDIA DE UNS *15 MIL TEU*", "POR DIA.", ('F16',)),
    ],
    'resumo': [
        (0.5, 6.6, "1 FÁBRICA E LACRE. 2 PORTÃO.", "3 PÁTIO. 4 *GUINDASTE*.", ()),
        (6.8, 13.0, "5 PLANO DE CARGA. 6 AMARRAÇÃO.", "7 VIAGEM. 8 *CHEGADA*.", ()),
        (13.2, 20.0, "*6 MOVIMENTOS* DE GUINDASTE", "E UM OCEANO NO MEIO.", ()),
        (20.2, 26.6, "TUDO GUIADO POR UM CÓDIGO", "DE *11 CARACTERES*.", ('F3',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Container ship"', 'https://en.wikipedia.org/wiki/Container_ship'),
    'F2': ('Wikipedia, "Intermodal container"', 'https://en.wikipedia.org/wiki/Intermodal_container'),
    'F3': ('Wikipedia, "ISO 6346"', 'https://en.wikipedia.org/wiki/ISO_6346'),
    'F4': ('Wikipedia, "Twistlock"', 'https://en.wikipedia.org/wiki/Twistlock'),
    'F5': ('New Zealand Customs Service, "Seals for sea freight"',
           'https://www.customs.govt.nz/media/crbdcszr/seals-for-sea-freight.pdf'),
    'F6': ('ABB, "Gate solutions" (OCR nos portões de terminal)',
           'https://www.abb.com/global/en/industries/ports/solutions/ocr-systems/gate-solutions'),
    'F7': ('Wikipedia, "Rubber tyred gantry crane"', 'https://en.wikipedia.org/wiki/Rubber_tyred_gantry_crane'),
    'F8': ('Wikipedia, "Container crane"', 'https://en.wikipedia.org/wiki/Container_crane'),
    'F9': ('Shipping Australia, 05/11/2021 (ACCC e Banco Mundial/IHS Markit: 25 a 28 por hora por guindaste)',
           'https://www.shippingaustralia.com.au/?p=19760'),
    'F10': ('Conta a partir de F9: 30 por hora = 1 a cada 120 s; 1 por compasso de 2 s = 60 vezes mais rápido', None),
    'F11': ('Wikipedia, "Bay plan"', 'https://en.wikipedia.org/wiki/Bay_plan'),
    'F12': ('Wikipedia, "Knot (unit)": 1 nó = 1,852 km/h', 'https://en.wikipedia.org/wiki/Knot_(unit)'),
    'F13': ('Wikipedia, "List of largest container ships" (24.346 TEU, 399,9 m x 61,3 m)',
            'https://en.wikipedia.org/wiki/List_of_largest_container_ships'),
    'F14': ('Conta a partir de F2 e F13: 400 m / 6,058 m = 66', None),
    'F15': ('Agência iNFRA, 03/09/2025: Santos, 5,4 milhões de TEU em 2024, maior da América Latina (Lloyd\'s List)',
            'https://agenciainfra.com/blog/?p=27144'),
    'F16': ('Conta a partir de F2 e F15: 5,4 milhões x 6,058 m = 32.713 km; 5,4 milhões / 366 dias = 14.754 por dia', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'caixa': 'Conheça o contêiner', 'codigo': 'O código e o dígito verificador',
                'fabrica': 'Etapa 1: fábrica e lacre', 'portao': 'Etapa 2: o portão com câmeras',
                'patio': 'Etapa 3: o pátio e o RTG', 'guindaste': 'Etapa 4: o guindaste e as travas giratórias',
                'ritmo': 'Um guindaste no ritmo da música', 'plano': 'Etapa 5: o plano de carga',
                'amarracao': 'Etapa 6: a amarração', 'viagem': 'Etapa 7: a viagem',
                'gigantes': 'Os maiores navios', 'chegada': 'Etapa 8: a chegada',
                'santos': 'O Porto de Santos', 'resumo': 'Resumo'}

DESCRICAO = """Como uma caixa de aço sai de uma fábrica e atravessa o oceano? Neste vídeo a gente segue UM contêiner de 20 pés: ele é carregado e lacrado, passa pelo portão com câmeras que leem o código, espera no pátio, é levantado pelo guindaste de cais com as travas giratórias, ganha uma vaga no plano de carga, é amarrado no convés, viaja e chega do outro lado. Um painel mostra a etapa (de 1 a 8) e conta cada movimento de guindaste do nosso contêiner.

No meio tem um quebra-cabeça: o código do contêiner termina num dígito verificador, e a gente faz a conta junto. E num trecho o guindaste trabalha no ritmo da música, um movimento por compasso.

Cada quadro é pixel art desenhada por código, e a música é original. Navios, guindastes, caminhões e portos são genéricos, sem nome nem logotipo de empresa.

Capítulos
{capitulos}

Simplificado de propósito
- O código MPXU 190426 5 foi inventado para o vídeo (não conferimos se MPX existe no registro do BIC, que é onde os donos de verdade registram as suas 3 letras). O dígito verificador, porém, sai da conta oficial do padrão ISO 6346.
- O guindaste de cais, o RTG e o navio são vistos "de frente" (olhando ao longo do cais), com menos fileiras e camadas do que um navio de verdade. A lança, as pernas e os cabos estão simplificados.
- Na vista de frente aparecem só 2 dos 4 pinos do spreader; os outros 2 ficam atrás.
- Nos planos de carga reais, as camadas do porão e do convés têm numerações próprias (de 2 em 2, e as do convés começam em 82). Aqui numeramos as camadas de 1 a 8, de baixo para cima.
- "90% da carga" é a parte que não viaja a granel (grão, minério, petróleo e outras cargas soltas ficam de fora), segundo a Wikipedia.
- Os 25 a 30 movimentos por hora são médias citadas pela Shipping Australia (média australiana de 28,1 e média mundial de cerca de 25); há portos bem mais rápidos e bem mais lentos.
- O peso máximo depende da versão da norma: 30.480 kg na tabela clássica e 36.000 kg pela ISO 668 atualizada. Por isso dizemos "pode passar de 30 toneladas".
- A fila de 32.700 km soma 5,4 milhões de contêineres de 20 pés; na vida real, parte desse volume é de contêineres de 40 pés (que contam 2 TEU).
- O portão real também confere documentos, reservas e o motorista; aqui mostramos só as câmeras.

Fontes
{fontes}

#conteiner #porto #navio #comofunciona #pixelart #logistica #portodesantos #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Na cena do
# guindaste, o caminhão fica em x 85 e a vaga do nosso no navio em x 216..226:
# o recorte de 70 a 250 pega os dois. O quebra-cabeça do código e o plano de
# carga mudam de arranjo quando VERTICAL = True para caber no recorte.
PREFIXO = 'ep19-conteiner'
CORTES = [
    dict(id='c1', de=('guindaste', 6.6), ate=('guindaste', 30.4), x=70, gancho=['A TRAVA', 'GIRATÓRIA'],
         titulo='Como um guindaste de porto pega um contêiner 🏗️',
         descricao='O spreader desce, encaixa 4 pinos nos furos ovais dos cantos e cada pino gira 90 graus. Pronto: o contêiner não sai mais. É a trava giratória (twistlock).'),
    dict(id='c2', de=('codigo', 12.8), ate=('codigo', 36.4), x=150, gancho=['QUAL É O', 'DÍGITO?'],
         titulo='O código do contêiner tem uma conta escondida 🔢',
         descricao='O último número do código de um contêiner é um dígito verificador: letras viram números, cada um vezes 1, 2, 4, 8..., soma tudo, divide por 11 e o resto é o dígito. O código deste vídeo é inventado.'),
    dict(id='c3', de=('ritmo', 0.0), ate=('ritmo', 24.0), x=70, gancho=['GUINDASTE', 'NO RITMO'],
         titulo='Um guindaste de porto no ritmo da música 🎵',
         descricao='Um movimento por compasso: o spreader trava e solta os 4 cantos na batida. Na vida real, um guindaste faz uns 25 a 30 movimentos por hora; aqui está 60 vezes mais rápido.'),
    dict(id='c4', de=('plano', 18.6), ate=('plano', 36.0), x=20, gancho=['PESADO', 'EMBAIXO'],
         titulo='Como se decide onde vai cada contêiner no navio 🚢',
         descricao='Cada vaga tem baia, fileira e camada. E a regra de ouro: o pesado embaixo, o leve em cima.'),
    dict(id='c5', de=('gigantes', 0.0), ate=('gigantes', 29.4), x=60, gancho=['24 MIL', 'CONTÊINERES'],
         titulo='O tamanho dos maiores navios de contêiner do mundo 🌊',
         descricao='Os maiores levam mais de 24.000 TEU, têm 400 metros de comprimento e 61 de largura. Cabem 66 contêineres de 20 pés em fila no comprimento de um deles.'),
    dict(id='c6', de=('portao', 0.0), ate=('portao', 29.9), x=40, gancho=['O PORTÃO', 'QUE LÊ'],
         titulo='O portão do porto que lê o contêiner sozinho 📷',
         descricao='Câmeras leem o código do contêiner e a placa, procuram avarias e conferem o lacre. O dígito verificador do código confirma a leitura.'),
]
