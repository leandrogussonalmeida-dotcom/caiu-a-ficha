#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep03 (série A JORNADA): A jornada da sua mala no aeroporto.

A protagonista é UMA mala laranja com a sua etiqueta. Ela passa por 8 etapas
(despacho, esteira, inspeção, triagem, montagem, pátio, voo, chegada); o
painel da direita mostra "ETAPA n DE 8", a distância que ela já percorreu e
o relógio da viagem. A viagem é de exemplo (aeroporto genérico, voo de
900 km, códigos inventados); os números do mundo real têm fonte abaixo.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 29/10/2026)
  F1  Etiqueta: número de 10 dígitos ("license plate", Resolução 740 da IATA),
      impresso em código de barras (Interleaved 2 of 5) e por extenso. 1º dígito:
      0 = etiqueta normal (interline/online), 1 = reserva (fallback), 2 = "rush".
      Depois, o código de 3 dígitos da companhia e o número da mala. A etiqueta
      traz o código IATA de 3 letras do aeroporto de chegada. O número liga a
      mala à mensagem BSM (voo e passageiro); o sistema automático lê o código
      de barras e separa as malas. Leitura com leitor a laser pode ser só 85%;
      câmeras chegam a 99,5% em condições ideais; algumas companhias usam chip
      RFID. O passageiro fica com o canhoto, prova de que a mala é dele.
      Wikipedia, "Bag tag".
  F2  Recomendação internacional: até 23 kg por mala despachada, por saúde e
      segurança de quem carrega; máximo de 32 kg por mala em muitas regiões
      (UE, EUA). IATA, "Checking your bags".
  F3  Tomógrafo de mala despachada: CT gera imagem 3D; um algoritmo procura
      explosivos, inclusive líquidos; só abre a mala se der alarme; liberada,
      volta para a companhia carregar. TSA (EUA), comunicado de 07/08/2024.
  F4  Classificador de bandejas basculantes: 2 m/s, até 9.000 malas por hora,
      bandeja de 1.000 mm. Siemens Logistics, "VarioTiltTray".
  F5  Contêiner (ULD) para malas, carga e correio em aviões de corpo largo e
      alguns menores; facilita o cálculo de peso e equilíbrio e acelera o
      carregamento. LD3 (código AKE): 4,5 m³, 1,63 m de altura, 2 posições
      por fileira no porão. Wikipedia, "Unit load device".
  F6  SITA Baggage IT Insights 2026 (dados de 2025): 75% das malas com problema
      atrasaram; 4% se perderam; causas (conexão 39%, ...); rastreio no
      despacho, carregamento, conexão e chegada (Resolução 753 da IATA).
  F7  Em 2025: 5 bilhões de passageiros, 24 milhões de malas com problema,
      4,9 a cada 1.000 passageiros; conexão = 39% dos casos. Aviacionline,
      resumo do relatório da SITA.
  F8  Um terminal de Londres (T5 de Heathrow) tem 18 km de esteiras comuns e
      8 km de trilho rápido de malas. Wikipedia, "Heathrow Terminal 5".
  F9  Bandeja basculante: a bandeja inclina e a mala escorrega para a calha
      do destino; o circuito é fechado e a bandeja vazia volta para carregar.
      Wikipedia, "Tilt tray sorter".
  F10 2 m/s = 7,2 km/h; 9.000 por hora = 2,5 por segundo. (conta a partir de F4)
"""

TITULO = "A jornada da sua mala no aeroporto | Do despacho à esteira em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='despacho', gen='lofi', bars=14, papel='drop'),        # 42 s
    dict(id='etiqueta', gen='synthwave', bars=15, papel='drop'),   # 36 s
    dict(id='esteira', gen='lofi', bars=11, papel='drop'),         # 33 s
    dict(id='inspecao', gen='lofi', bars=13, papel='drop'),        # 39 s
    dict(id='triagem', gen='synthwave', bars=20, papel='drop'),    # 48 s
    dict(id='montagem', gen='lofi', bars=11, papel='drop'),        # 33 s
    dict(id='patio', gen='lofi', bars=12, papel='drop'),           # 36 s
    dict(id='voo', gen='synthwave', bars=15, papel='break'),       # 36 s
    dict(id='conexao', gen='lofi', bars=10, papel='drop'),         # 30 s
    dict(id='chegada', gen='lofi', bars=14, papel='drop'),         # 42 s
    dict(id='numeros', gen='lofi', bars=14, papel='break'),        # 42 s
    dict(id='resumo', gen='lofi', bars=11, papel='drop'),          # 33 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "VOCÊ DESPACHA A MALA E ELA SOME.", "PARA ONDE ELA VAI?", ()),
        (6.2, 11.6, "UM SÓ TERMINAL PODE TER *18 KM*", "DE ESTEIRAS ESCONDIDAS.", ('F8',)),
    ],
    'despacho': [
        (0.8, 7.0, "ETAPA 1: O *DESPACHO*.", "A MALA SOBE NA BALANÇA.", ()),
        (7.4, 14.0, "O RECOMENDADO É ATÉ *23 KG* POR MALA.", "EM MUITOS PAÍSES, O MÁXIMO É 32 KG.", ('F2',)),
        (14.4, 21.0, "O LIMITE PROTEGE A SAÚDE DE QUEM", "CARREGA AS MALAS.", ('F2',)),
        (21.4, 28.6, "A IMPRESSORA SOLTA A *ETIQUETA*,", "QUE VAI PRESA NA ALÇA.", ('F1',)),
        (29.0, 35.6, "VOCÊ FICA COM UM *COMPROVANTE*", "COM O MESMO NÚMERO.", ('F1',)),
        (36.0, 41.6, "E A MALA SAI PELA CORTINA,", "RUMO AOS BASTIDORES.", ()),
    ],
    'etiqueta': [
        (0.5, 7.0, "A ETIQUETA TEM UM NÚMERO DE", "*10 DÍGITOS*: A PLACA DA MALA.", ('F1',)),
        (7.4, 14.0, "O 1º DÍGITO DIZ O TIPO: 0 É NORMAL,", "1 É RESERVA, 2 É MALA *REENVIADA*.", ('F1',)),
        (14.4, 21.0, "OS 3 SEGUINTES: A *COMPANHIA*.", "O RESTO: O NÚMERO DA MALA.", ('F1',)),
        (21.4, 28.6, "AS BARRAS GUARDAM O NÚMERO. AS", "3 LETRAS: O *AEROPORTO* DE CHEGADA.", ('F1',)),
        (29.0, 35.6, "O NÚMERO APONTA PARA UMA *MENSAGEM*", "COM O VOO E O PASSAGEIRO.", ('F1',)),
    ],
    'esteira': [
        (0.6, 7.0, "ETAPA 2: A *ESTEIRA*. A MALA ENTRA", "NUM RIO DE MALAS.", ()),
        (7.4, 14.6, "UM PÓRTICO LÊ A ETIQUETA", "SEM NINGUÉM ENCOSTAR NELA.", ('F1',)),
        (15.0, 22.0, "COM LEITOR A *LASER*, A LEITURA PODE", "ACERTAR SÓ *85%* DAS ETIQUETAS.", ('F1',)),
        (22.4, 29.6, "COM CÂMERAS, ATÉ *99,5%*. ALGUMAS", "ETIQUETAS TÊM ATÉ UM CHIP.", ('F1',)),
    ],
    'inspecao': [
        (0.6, 7.0, "ETAPA 3: A *INSPEÇÃO*. A MALA", "ENTRA NUM TOMÓGRAFO.", ('F3',)),
        (7.4, 14.6, "COMO NO HOSPITAL: ELE GIRA E MONTA", "UMA *IMAGEM 3D* DA MALA.", ('F3',)),
        (15.0, 22.0, "UM PROGRAMA PROCURA EXPLOSIVOS,", "ATÉ OS LÍQUIDOS.", ('F3',)),
        (22.4, 30.0, "SE DER ALARME, A MALA É DESVIADA", "E UM AGENTE ABRE PARA CONFERIR.", ('F3',)),
        (30.4, 38.4, "A NOSSA PASSOU: *LIBERADA*", "PARA SEGUIR VIAGEM.", ('F3',)),
    ],
    'triagem': [
        (0.6, 7.0, "ETAPA 4: A *TRIAGEM*. UM CIRCUITO", "DE BANDEJAS QUE NÃO PARA.", ('F9',)),
        (7.4, 14.6, "CADA MALA GANHA UMA BANDEJA.", "O SISTEMA JÁ SABE O DESTINO DELA.", ('F9', 'F1')),
        (15.0, 22.6, "AS BANDEJAS ANDAM A *2 METROS*", "*POR SEGUNDO*: 7,2 KM/H.", ('F4', 'F10')),
        (23.0, 30.6, "NA SAÍDA CERTA, A BANDEJA *TOMBA*", "E A MALA ESCORREGA.", ('F9',)),
        (31.0, 38.6, "ATÉ *9.000 MALAS POR HORA*:", "2,5 POR SEGUNDO.", ('F4', 'F10')),
        (39.0, 47.0, "A NOSSA CAIU NA SAÍDA *PXL*:", "O CÓDIGO DO DESTINO DELA.", ('F1',)),
    ],
    'montagem': [
        (0.6, 7.0, "ETAPA 5: A *MONTAGEM*. A MALA", "DESCE PELA RAMPA DO VOO DELA.", ()),
        (7.4, 14.6, "UM FUNCIONÁRIO LÊ A ETIQUETA", "E CONFERE: É DESTE VOO.", ('F6',)),
        (15.0, 22.6, "A REGRA DO SETOR: REGISTRAR A", "MALA EM *4 PONTOS* DA VIAGEM.", ('F6',)),
        (23.0, 32.4, "ELA ENTRA NUM *CONTÊINER* COM AS", "OUTRAS MALAS DO MESMO VOO.", ('F5',)),
    ],
    'patio': [
        (0.6, 7.4, "ETAPA 6: O *PÁTIO*. UM TRATOR LEVA", "OS CONTÊINERES ATÉ O AVIÃO.", ()),
        (7.8, 15.0, "UM ELEVADOR ERGUE O CONTÊINER", "ATÉ A PORTA DO PORÃO.", ()),
        (15.4, 22.6, "UM MODELO MUITO USADO, O *LD3*:", "4,5 METROS CÚBICOS, 1,63 M DE ALTURA.", ('F5',)),
        (23.0, 30.0, "NO PORÃO VÃO *2 POR FILEIRA*,", "EMBAIXO DO PISO DOS PASSAGEIROS.", ('F5',)),
        (30.4, 35.6, "PORTA FECHADA. PRÓXIMA PARADA:", "O CÉU.", ()),
    ],
    'voo': [
        (0.6, 7.4, "ETAPA 7: O *VOO*. A MALA VIAJA", "NO PORÃO, DENTRO DO CONTÊINER.", ('F5',)),
        (7.8, 15.0, "O CONTÊINER AGILIZA A CARGA E", "AJUDA A CALCULAR O *PESO*.", ('F5',)),
        (15.4, 22.6, "ELE É USADO NOS AVIÕES GRANDES", "E EM ALGUNS MENORES.", ('F5',)),
        (23.0, 29.4, "NA NOSSA VIAGEM DE EXEMPLO,", "SÃO *900 KM* ATÉ O DESTINO.", ()),
        (29.8, 35.6, "E SE TIVESSE *CONEXÃO*?", "", ()),
    ],
    'conexao': [
        (0.6, 7.4, "NA CONEXÃO, A MALA TROCA DE AVIÃO", "SEM VOCÊ VER.", ('F6',)),
        (7.8, 15.0, "ELA SAI DE UM PORÃO E PRECISA", "ENTRAR NO OUTRO A TEMPO.", ('F6',)),
        (15.4, 22.6, "É ONDE MAIS DÁ ERRADO: *39%*", "DAS MALAS COM PROBLEMA.", ('F7',)),
        (23.0, 29.6, "NA NOSSA VIAGEM NÃO TEM CONEXÃO.", "*VOO DIRETO!*", ()),
    ],
    'chegada': [
        (0.6, 7.4, "ETAPA 8: A *CHEGADA*. O CONTÊINER", "DESCE DO PORÃO.", ()),
        (7.8, 15.0, "AS MALAS VÃO PARA UMA ESTEIRA", "QUE SOBE ATÉ O SAGUÃO.", ()),
        (15.4, 22.6, "NA *ESTEIRA DE BAGAGEM*, ELAS", "DÃO VOLTAS ATÉ O DONO CHEGAR.", ()),
        (23.0, 30.6, "LÁ VEM A NOSSA!", "", ()),
        (31.0, 41.4, "O NÚMERO DO COMPROVANTE CONFERE", "COM O DA ETIQUETA: *É SUA*.", ('F1',)),
    ],
    'numeros': [
        (0.6, 7.4, "EM 2025, *5 BILHÕES* DE PASSAGEIROS", "VOARAM PELO MUNDO.", ('F7',)),
        (7.8, 15.0, "*24 MILHÕES* DE MALAS TIVERAM", "ALGUM PROBLEMA.", ('F7',)),
        (15.4, 22.6, "DÁ UMAS *5 A CADA 1.000*", "PASSAGEIROS.", ('F7',)),
        (23.0, 30.6, "3 EM CADA 4 DESSAS SÓ *ATRASARAM*", "E CHEGARAM DEPOIS.", ('F6',)),
        (31.0, 41.4, "PERDIDAS DE VEZ: SÓ *4%* DELAS.", "QUASE TODA MALA ACHA O CAMINHO.", ('F6',)),
    ],
    'resumo': [
        (0.6, 8.0, "8 ETAPAS: DESPACHO, ESTEIRA,", "INSPEÇÃO, TRIAGEM, MONTAGEM...", ()),
        (8.4, 16.0, "...PÁTIO, VOO E CHEGADA. TUDO GUIADO", "POR UM NÚMERO DE *10 DÍGITOS*.", ('F1',)),
        (16.4, 24.0, "DA PRÓXIMA VEZ QUE DESPACHAR,", "OLHE BEM A SUA ETIQUETA.", ()),
        (24.4, 32.4, "E GUARDE O *COMPROVANTE* ATÉ", "PEGAR A MALA.", ('F1',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Bag tag"', 'https://en.wikipedia.org/wiki/Bag_tag'),
    'F2': ('IATA, "Checking your bags"', 'https://iata.org/en/programs/ops-infra/baggage/check-bag'),
    'F3': ('TSA, "TSA introduces new checked baggage screening equipment" (07/08/2024)',
           'https://tsa.gov/news/press/releases/2024/08/07/tsa-introduces-new-checked-baggage-screening-equipment-salem'),
    'F4': ('Siemens Logistics, "VarioTiltTray"',
           'https://www.siemens-logistics.com/en/airport-logistics/baggage-handling-systems/variotilttray'),
    'F5': ('Wikipedia, "Unit load device"', 'https://en.wikipedia.org/wiki/Unit_load_device'),
    'F6': ('SITA, Baggage IT Insights 2026 (dados de 2025), PDF',
           'https://www.fvw.de/news/media/33/Sita-Baggage-Report-2026-327348.pdf'),
    'F7': ('Aviacionline, "Report: airlines are losing fewer bags than ever as mishandled rate hits record low" (relatório da SITA)',
           'https://www.aviacionline.com/english/commercial-aviation/report-airlines-are-losing-fewer-bags-than-ever-as-mishandled-rate-hits-record-low_a6a46b6e08f397eeb8e442c95'),
    'F8': ('Wikipedia, "Heathrow Terminal 5"', 'https://en.wikipedia.org/wiki/Heathrow_Terminal_5'),
    'F9': ('Wikipedia, "Tilt tray sorter"', 'https://en.wikipedia.org/wiki/Tilt_tray_sorter'),
    'F10': ('Conta a partir de F4 (2 m/s x 3,6 = 7,2 km/h; 9.000 / 3.600 s = 2,5 por segundo)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'despacho': 'Etapa 1: o despacho e a balança',
                'etiqueta': 'Os 10 dígitos da etiqueta', 'esteira': 'Etapa 2: a esteira e a leitura',
                'inspecao': 'Etapa 3: o tomógrafo', 'triagem': 'Etapa 4: a triagem por bandejas',
                'montagem': 'Etapa 5: a montagem do voo', 'patio': 'Etapa 6: o contêiner LD3 e o pátio',
                'voo': 'Etapa 7: o voo no porão', 'conexao': 'E se tiver conexão?',
                'chegada': 'Etapa 8: a esteira de bagagem', 'numeros': 'Quantas malas se perdem?',
                'resumo': 'As 8 etapas'}

DESCRICAO = """O que acontece com a sua mala depois que ela some pela cortina do balcão? A gente segue UMA mala, com a etiqueta dela, pelas 8 etapas da viagem: balança, esteira, tomógrafo, triagem por bandejas, montagem do voo, contêiner, porão do avião e a esteira de bagagem na chegada.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O aeroporto é genérico. A distância e o relógio do painel são de uma viagem de exemplo (voo de 900 km, sem conexão); cada aeroporto tem o seu caminho.
- Os códigos PXL, BIT, RGB, CPU, LCD, USB e GIF, o voo 314 e o número 0 042 314159 são de exemplo, não de aeroporto ou companhia de verdade.
- O 1º dígito da etiqueta: 0 é a etiqueta normal (interline/online), 1 é a de reserva (fallback) e 2 é a de mala reenviada ao dono depois de um extravio (rush). Os outros números ficam a critério da companhia.
- A triagem real tem várias voltas, desvios e depósitos; aqui mostramos um circuito só. Em muitos aeroportos a triagem e a inspeção ficam em ordem diferente.
- O tomógrafo de verdade gira muito mais rápido; mostramos em câmera lenta.
- No porão, o contêiner LD3 entra pela porta e é empurrado para a sua posição; o desenho mostra essa entrada de lado.
- Aviões menores muitas vezes levam as malas soltas no porão, sem contêiner.
- Os números da SITA são do relatório Baggage IT Insights 2026 (dados de 2025). "Problema" inclui mala atrasada, danificada, furtada ou perdida.

Fontes
{fontes}

#aeroporto #mala #comofunciona #pixelart #viagem #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px.
PREFIXO = 'ep03-mala'
CORTES = [
    dict(id='c1', de=('despacho', 0.0), ate=('despacho', 29.0), x=96, gancho=['SUA MALA', 'NA BALANÇA'],
         titulo='O que acontece com a sua mala no balcão do aeroporto 🧳',
         descricao='A mala sobe na balança (o recomendado é até 23 kg; em muitos países o máximo é 32 kg) e ganha uma etiqueta com um número de 10 dígitos.'),
    dict(id='c2', de=('etiqueta', 0.0), ate=('etiqueta', 36.0), x=100, gancho=['O SEGREDO', 'DA ETIQUETA'],
         titulo='O que os números da etiqueta da mala significam',
         descricao='10 dígitos: o tipo da etiqueta, o código da companhia e o número da mala. As 3 letras grandes são o aeroporto de chegada.'),
    dict(id='c3', de=('inspecao', 0.0), ate=('inspecao', 39.0), x=96, gancho=['O RAIO-X', 'DA SUA MALA'],
         titulo='Como a mala despachada é inspecionada (tomografia 3D)',
         descricao='Um tomógrafo gira em volta da mala e monta uma imagem 3D. Um programa procura explosivos; se der alarme, um agente abre a mala.'),
    dict(id='c4', de=('triagem', 0.0), ate=('triagem', 31.0), x=78, gancho=['A BANDEJA', 'QUE TOMBA'],
         titulo='Como o aeroporto separa milhares de malas por hora 🛄',
         descricao='Cada mala ganha uma bandeja que anda a 2 metros por segundo. Na saída certa, a bandeja tomba e a mala escorrega para o voo dela.'),
    dict(id='c5', de=('patio', 0.0), ate=('patio', 36.0), x=76, gancho=['O CONTÊINER', 'DO PORÃO'],
         titulo='Como as malas entram no avião ✈️',
         descricao='As malas vão num contêiner LD3 (4,5 metros cúbicos). Um elevador ergue o contêiner até a porta do porão.'),
    dict(id='c6', de=('numeros', 1.5), ate=('numeros', 42.0), x=60, gancho=['QUANTAS', 'SE PERDEM?'],
         titulo='Quantas malas os aviões perdem por ano?',
         descricao='Em 2025, 24 milhões de malas tiveram algum problema, umas 5 a cada 1.000 passageiros (SITA). 3 em cada 4 só atrasaram; só 4% se perderam de vez.'),
]
