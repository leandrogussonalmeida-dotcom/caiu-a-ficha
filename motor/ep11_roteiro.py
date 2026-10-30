#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep11 (série A JORNADA): A jornada da água, da represa até a sua tomada.

A ideia: seguir UMA gota de chuva (a protagonista) por uma usina hidrelétrica
e depois seguir a energia que ela deixou: chuva, represa, conduto forçado,
turbina Francis, gerador, transformador elevador, linha de transmissão,
subestação e o poste da rua, até a tomada e a lâmpada. Objetivo que sobe na
tela: "etapa 4 de 9", a forma da energia (potencial -> movimento -> elétrica)
e a tensão no fio. O desenho mora em `ep11_motor.py` (cenas) e
`ep11_desenho.py` (paleta, gota, barragem, caracol, gerador, transformador,
torre, poste, casa, ícones, painel).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

A tensão do exemplo (todas padronizadas no Brasil, F9):
  gerador 13,8 kV (gerador grande sai com 480 V a 22 kV, F7)
  -> transformador elevador 500 kV -> linha de transmissão 500 kV
  -> subestação 138 kV -> 13,8 kV (distribuição) -> poste 220/127 V

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Hidrelétrica: a energia vem da energia potencial da água represada,
      que move turbina e gerador; um tubo grande (conduto forçado, "penstock")
      leva a água da represa à turbina; a potência depende do volume e da
      diferença de altura (a queda). Wikipedia, "Hydroelectricity".
  F2  USGS: a tomada d'água fica perto do fundo da barragem; a água desce pelo
      conduto, gira a turbina, cujo eixo move o gerador; ímã passando por um
      condutor faz a eletricidade andar; depois da turbina a água segue pelo
      canal de fuga para o rio. USGS Water Science School.
  F3  Turbina Francis: a mais usada; queda de 40 a 600 m; caixa espiral
      (caracol) em volta do rotor; palhetas (wicket gates) controlam a vazão;
      palhetas convertem pressão em velocidade; o tubo de sucção (draft tube)
      reduz a velocidade da água na saída. Wikipedia, "Francis turbine".
  F4  Itaipu: 14 GW (14.000 MW) instalados, 20 unidades de 700 MW, turbinas
      Francis; queda de projeto 118 m; 700 m³/s por unidade; dez geram em
      60 Hz para o Brasil, dez em 50 Hz para o Paraguai; no rio Paraná.
      Wikipedia, "Itaipu Dam".
  F5  Alternador: converte energia mecânica em corrente alternada; campo
      magnético girando (rotor) e bobinas paradas (estator); condutor que se
      move em relação a um campo magnético ganha tensão (lei de Faraday).
      Wikipedia, "Alternator".
  F6  Transformador: duas bobinas de fio de cobre em volta de um núcleo
      magnético; corrente variando numa bobina varia o fluxo e induz tensão na
      outra; razão de tensões = razão de espiras. Wikipedia, "Transformer".
  F7  Transmissão: o gerador produz de ~480 V a 22 kV; transformadores sobem
      para 100 a 1.000 kV; perdas proporcionais ao quadrado da corrente; mais
      tensão e menos corrente = menos perda; 1.000 MW por 160 km: 765 kV
      perde 0,5% a 1,1%, 345 kV perde 4,2%; subestações baixam a tensão.
      Wikipedia, "Electric power transmission".
  F8  Transformador de distribuição: a última redução de tensão; no poste.
      Wikipedia, "Distribution transformer".
  F9  Tensões padronizadas no Brasil: transmissão 750, 500, 230, 138, 69 kV...;
      distribuição primária 34,5 e 13,8 kV; secundária 380/220 e 220/127 V.
      Decreto nº 73.080/1973, art. 47.
  F10 Brasil, 2024: hidráulica = 55,3% da oferta interna de energia elétrica;
      eólica 14,1%, solar 9,3%, biomassa 8,1%, gás natural 6,3%, nuclear
      2,1%, carvão 1,9%, petróleo 1,5%, importada 1,5%. EPE, BEN 2025 (Síntese).
  F11 Conta (F1, F4): 1.000 kg/m³ x 9,8 m/s² x 700 m³/s x 118 m = 809 MW na
      água; a unidade entrega 700 MW.
  F12 Conta (F4): queda livre sem atrito de 118 m: v = raiz(2 x 9,8 x 118)
      = 48 m/s = 173 km/h ("uns 170 km/h").
  F13 Conta (F7): perda = R x I²; com a mesma potência, tensão 2x -> corrente
      pela metade -> perda 4x menor.
  F14 Grades (trash racks) nas tomadas d'água protegem as turbinas de
      detritos. Water (MDPI), 2022, 14(17), 2609.
  F15 Conduto forçado (penstock): tubo fechado que leva a água às turbinas,
      com comportas para controlar a vazão. Wikipedia, "Penstock".
"""

TITULO = "A jornada da água: da represa até a sua tomada | Como funciona a hidrelétrica em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),          # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),          # 6 s
    dict(id='chuva', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='represa', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='conduto', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='turbina', gen='synthwave', bars=15, papel='drop'),    # 36 s
    dict(id='saida', gen='lofi', bars=8, papel='break'),           # 24 s
    dict(id='gerador', gen='lofi', bars=12, papel='drop'),         # 36 s
    dict(id='itaipu', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='elevador', gen='lofi', bars=10, papel='drop'),        # 30 s
    dict(id='linhas', gen='synthwave', bars=17, papel='drop'),     # 40,8 s
    dict(id='subestacao', gen='lofi', bars=10, papel='drop'),      # 30 s
    dict(id='casa', gen='lofi', bars=16, papel='drop'),            # 48 s
    dict(id='brasil', gen='lofi', bars=12, papel='break'),         # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),             # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 5.8, "VOCÊ APERTA O INTERRUPTOR E A", "*LUZ ACENDE*. DE ONDE ELA VEM?", ()),
        (6.0, 11.6, "ESSA ENERGIA COMEÇOU COMO", "*UMA GOTA DE CHUVA*.", ()),
    ],
    'chuva': [
        (0.5, 7.4, "ETAPA 1: TUDO COMEÇA COM *CHUVA*.", "ESTA É A NOSSA GOTA.", ()),
        (7.6, 14.6, "ELA CAI NUM MORRO E ESCORRE", "POR UM *CÓRREGO*.", ()),
        (14.8, 21.8, "O CÓRREGO DESÁGUA NUM *RIO*,", "E O RIO DESCE PELO VALE.", ()),
        (22.0, 29.6, "MAIS ADIANTE, UMA *BARRAGEM* FECHA", "O RIO: ALI FICA A REPRESA.", ('F1',)),
    ],
    'represa': [
        (0.5, 7.4, "ETAPA 2: A *BARRAGEM* SEGURA A", "ÁGUA NO ALTO. É A *REPRESA*.", ('F1',)),
        (7.6, 14.6, "DO OUTRO LADO, DEPOIS DA USINA,", "O RIO SEGUE LÁ EMBAIXO.", ('F2',)),
        (14.8, 21.8, "ESSA DIFERENÇA DE ALTURA", "É A *QUEDA*.", ('F1',)),
        (22.0, 28.8, "EM ITAIPU, A QUEDA DE PROJETO", "É DE *118 METROS*.", ('F4',)),
        (29.0, 35.6, "LÁ NO ALTO, A ÁGUA TEM *ENERGIA*", "*POTENCIAL*: ENERGIA GUARDADA.", ('F1',)),
    ],
    'conduto': [
        (0.5, 6.2, "ETAPA 3: PERTO DO FUNDO FICA", "A *TOMADA D'ÁGUA*.", ('F2',)),
        (6.4, 12.2, "UMA *GRADE* SEGURA GALHOS E LIXO.", "A *COMPORTA* ABRE.", ('F14', 'F15')),
        (12.4, 18.2, "A GOTA ENTRA NO *CONDUTO FORÇADO*,", "UM TUBO ENORME ATÉ A TURBINA.", ('F1', 'F15')),
        (18.4, 24.2, "QUANTO MAIS FUNDO, MAIS *PRESSÃO*:", "A ÁGUA DE CIMA EMPURRA A DE BAIXO.", ()),
        (24.4, 30.2, "SE CAÍSSE LIVRE OS 118 METROS,", "CHEGARIA A UNS *170 KM/H*.", ('F12',)),
        (30.4, 35.6, "TODA ESSA FORÇA VAI DIRETO", "PARA A *TURBINA*.", ('F1',)),
    ],
    'turbina': [
        (0.5, 7.0, "ETAPA 4: A *TURBINA*. NAS GRANDES", "USINAS É COMUM A *FRANCIS*.", ('F3', 'F4')),
        (7.2, 13.8, "A ÁGUA ENTRA NUM *CARACOL*", "QUE DÁ A VOLTA NA TURBINA.", ('F3',)),
        (14.0, 20.6, "*PALHETAS* ABREM E FECHAM:", "CONTROLAM QUANTA ÁGUA PASSA.", ('F3',)),
        (20.8, 27.4, "ALI A PRESSÃO VIRA *VELOCIDADE*.", "A GOTA EMPURRA AS PÁS DO *ROTOR*.", ('F3',)),
        (27.6, 35.6, "O ROTOR GIRA. E A GOTA SAI", "POR BAIXO, PELO MEIO.", ('F3',)),
    ],
    'saida': [
        (0.5, 6.0, "A GOTA DEIXOU A ENERGIA DELA", "NO *ROTOR*. AGORA ELA SAI...", ()),
        (6.2, 11.8, "...PELO *TUBO DE SUCÇÃO*, QUE ALARGA", "E DEIXA A ÁGUA MAIS DEVAGAR.", ('F3',)),
        (12.0, 17.8, "E VOLTA PARA O RIO.", "A ÁGUA *NÃO É GASTA*.", ('F2',)),
        (18.0, 23.6, "DAQUI EM DIANTE, SEGUIMOS A", "*ENERGIA*: ELA SOBE PELO EIXO.", ('F2',)),
    ],
    'gerador': [
        (0.5, 7.4, "ETAPA 5: O EIXO DA TURBINA GIRA", "O *GERADOR*, LOGO ACIMA.", ('F2',)),
        (7.6, 14.6, "NO EIXO, UM *ROTOR* CHEIO DE ÍMÃS.", "EM VOLTA, *BOBINAS* DE FIO PARADAS.", ('F5',)),
        (14.8, 21.8, "ÍMÃ PASSANDO PERTO DO FIO FAZ A", "CORRENTE ANDAR: É A *INDUÇÃO*.", ('F2', 'F5')),
        (22.0, 28.8, "NORTE, SUL, NORTE... A CORRENTE VAI", "E VOLTA: *CORRENTE ALTERNADA*.", ('F5',)),
        (29.0, 35.6, "NO BRASIL, ELA VAI E VOLTA", "*60 VEZES POR SEGUNDO*: 60 HZ.", ('F4',)),
    ],
    'itaipu': [
        (0.5, 7.4, "PARA TER IDEIA DO TAMANHO:", "*ITAIPU*, NO RIO PARANÁ.", ('F4',)),
        (7.6, 14.6, "SÃO *20 UNIDADES* DE 700 MW:", "*14.000 MW* AO TODO.", ('F4',)),
        (14.8, 21.8, "CADA TURBINA RECEBE *700 M³*", "DE ÁGUA POR SEGUNDO.", ('F4',)),
        (22.0, 28.8, "700 M³/S CAINDO 118 M DÃO UNS", "*810 MW*. SAEM 700: A MAIOR PARTE.", ('F11',)),
        (29.0, 35.6, "10 GERAM EM 60 HZ, PARA O BRASIL;", "10 EM *50 HZ*, PARA O PARAGUAI.", ('F4',)),
    ],
    'elevador': [
        (0.5, 7.4, "ETAPA 6: NA SAÍDA DA USINA,", "UM *TRANSFORMADOR*.", ('F7',)),
        (7.6, 14.6, "DUAS *BOBINAS* DE FIO DE COBRE EM", "VOLTA DE UM *NÚCLEO* MAGNÉTICO.", ('F6',)),
        (14.8, 21.8, "A CORRENTE QUE VAI E VOLTA NUMA", "BOBINA *INDUZ* TENSÃO NA OUTRA.", ('F6',)),
        (22.0, 29.6, "MAIS VOLTAS DE FIO, MAIS TENSÃO:", "DE 13,8 KV PARA *500 KV*.", ('F6', 'F9')),
    ],
    'linhas': [
        (0.5, 6.8, "ETAPA 7: AS *LINHAS DE TRANSMISSÃO*", "LEVAM A ENERGIA PARA LONGE.", ('F7',)),
        (7.0, 13.6, "POR QUE TANTA TENSÃO? PORQUE O", "FIO *ESQUENTA* COM A CORRENTE.", ('F7',)),
        (13.8, 20.4, "E A PERDA CRESCE COM O *QUADRADO*:", "CORRENTE 2 VEZES, PERDA 4 VEZES.", ('F7',)),
        (20.6, 27.2, "TENSÃO 2 VEZES MAIOR: METADE DA", "CORRENTE E *4 VEZES MENOS PERDA*.", ('F13',)),
        (27.4, 34.0, "1.000 MW POR 160 KM: EM 345 KV,", "A LINHA PERDE *4,2%*.", ('F7',)),
        (34.2, 40.6, "EM 765 KV, SÓ *0,5% A 1,1%*.", "POR ISSO A TENSÃO SOBE TANTO.", ('F7',)),
    ],
    'subestacao': [
        (0.5, 7.4, "ETAPA 8: PERTO DA CIDADE,", "UMA *SUBESTAÇÃO*.", ('F7',)),
        (7.6, 14.6, "LÁ, TRANSFORMADORES FAZEM O", "CONTRÁRIO: *BAIXAM* A TENSÃO.", ('F7',)),
        (14.8, 21.8, "DE 500 KV PARA 138 KV, E DEPOIS", "PARA *13,8 KV*.", ('F9',)),
        (22.0, 29.6, "COM 13,8 KV, A ENERGIA ENTRA NA", "*REDE DE DISTRIBUIÇÃO* DA CIDADE.", ('F9',)),
    ],
    'casa': [
        (0.5, 6.6, "ETAPA 9: NA RUA, O ÚLTIMO", "*TRANSFORMADOR*, NO ALTO DO POSTE.", ('F8',)),
        (6.8, 13.4, "ELE BAIXA DE 13,8 KV PARA", "*220 V E 127 V*.", ('F8', 'F9')),
        (13.6, 20.2, "O FIO ENTRA NA CASA E PASSA", "PELO *MEDIDOR*, O RELÓGIO DE LUZ.", ()),
        (20.4, 27.0, "DEPOIS CORRE DENTRO DA PAREDE", "ATÉ A *TOMADA*.", ()),
        (27.2, 33.8, "CONFORME A CIDADE, A TOMADA", "TEM *127 V OU 220 V*.", ('F9',)),
        (34.0, 40.6, "VOCÊ APERTA O INTERRUPTOR E...", "*A LUZ ACENDE*.", ()),
        (40.8, 47.6, "ESSA LUZ COMEÇOU COMO", "UMA *GOTA DE CHUVA*.", ()),
    ],
    'brasil': [
        (0.5, 7.4, "E NO BRASIL? A ÁGUA É A *FONTE Nº 1*", "DA NOSSA ELETRICIDADE.", ('F10',)),
        (7.6, 14.6, "EM 2024, *55%* DA ELETRICIDADE", "VEIO DAS HIDRELÉTRICAS.", ('F10',)),
        (14.8, 21.8, "DEPOIS VÊM O VENTO (*14%*), O SOL", "(*9%*) E A BIOMASSA (*8%*).", ('F10',)),
        (22.0, 28.8, "E A NOSSA GOTA? O SOL ESQUENTA", "O RIO E ELA *EVAPORA*.", ()),
        (29.0, 35.6, "VIRA NUVEM, VIRA CHUVA...", "E A JORNADA *RECOMEÇA*.", ()),
    ],
    'resumo': [
        (0.5, 7.4, "1 CHUVA, 2 REPRESA, 3 CONDUTO:", "A ÁGUA DESCE COM *PRESSÃO*.", ()),
        (7.6, 14.6, "4 A TURBINA GIRA. 5 O GERADOR", "FAZ *CORRENTE ALTERNADA*.", ()),
        (14.8, 21.8, "6 A TENSÃO SOBE, 7 VIAJA LONGE,", "8 E A SUBESTAÇÃO BAIXA DE NOVO.", ()),
        (22.0, 29.6, "9 O POSTE, A TOMADA...", "E A *LUZ ACENDE*.", ()),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Hydroelectricity"', 'https://en.wikipedia.org/wiki/Hydroelectricity'),
    'F2': ('USGS Water Science School, "Hydroelectric Power: How it Works"',
           'https://www.usgs.gov/water-science-school/science/hydroelectric-power-how-it-works'),
    'F3': ('Wikipedia, "Francis turbine"', 'https://en.wikipedia.org/wiki/Francis_turbine'),
    'F4': ('Wikipedia, "Itaipu Dam"', 'https://en.wikipedia.org/wiki/Itaipu_Dam'),
    'F5': ('Wikipedia, "Alternator"', 'https://en.wikipedia.org/wiki/Alternator'),
    'F6': ('Wikipedia, "Transformer"', 'https://en.wikipedia.org/wiki/Transformer'),
    'F7': ('Wikipedia, "Electric power transmission"', 'https://en.wikipedia.org/wiki/Electric_power_transmission'),
    'F8': ('Wikipedia, "Distribution transformer"', 'https://en.wikipedia.org/wiki/Distribution_transformer'),
    'F9': ('Decreto nº 73.080/1973, art. 47 (tensões padronizadas)',
           'https://brasil.justia.com/nacionales/decretos/73-080-de-5-11-1973/gdoc'),
    'F10': ('EPE, Balanço Energético Nacional 2025, Relatório Síntese (ano-base 2024)',
            'https://uploads.eixos.com.br/2025/05/Sintese_BEN2025.pdf'),
    'F11': ('Conta a partir de F1 e F4: 1.000 kg/m³ x 9,8 m/s² x 700 m³/s x 118 m = 809 MW', None),
    'F12': ('Conta a partir de F4: queda livre sem atrito de 118 m, v = raiz(2 x 9,8 x 118) = 48 m/s = 173 km/h', None),
    'F13': ('Conta a partir de F7: perda = R x I²; mesma potência com o dobro da tensão = metade da corrente = 1/4 da perda', None),
    'F14': ('Water (MDPI), 2022, 14(17), 2609: grades (trash racks) protegem as turbinas',
            'https://www.mdpi.com/2073-4441/14/17/2609'),
    'F15': ('Wikipedia, "Penstock"', 'https://en.wikipedia.org/wiki/Penstock'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'chuva': 'Etapa 1: a chuva', 'represa': 'Etapa 2: a represa e a queda',
                'conduto': 'Etapa 3: tomada d\'água e conduto forçado', 'turbina': 'Etapa 4: a turbina Francis',
                'saida': 'A água volta para o rio', 'gerador': 'Etapa 5: o gerador e a corrente alternada',
                'itaipu': 'O tamanho de Itaipu', 'elevador': 'Etapa 6: o transformador elevador',
                'linhas': 'Etapa 7: por que alta tensão?', 'subestacao': 'Etapa 8: a subestação',
                'casa': 'Etapa 9: do poste à tomada', 'brasil': 'A água na eletricidade do Brasil',
                'resumo': 'Resumo'}

DESCRICAO = """Como a água de uma represa vira a luz da sua casa? Neste vídeo a gente segue UMA gota de chuva: ela cai num morro, desce pelo rio até a represa, entra pela tomada d'água, desce o conduto forçado, empurra as pás de uma turbina Francis e volta para o rio. A energia que ela deixou segue viagem: o gerador transforma giro em corrente alternada, um transformador sobe a tensão para 500 mil volts, as linhas de transmissão levam a energia para longe, a subestação baixa a tensão, o transformador do poste deixa em 127 ou 220 volts e a lâmpada acende.

Um painel mostra a etapa (de 1 a 9), a forma da energia (potencial, movimento, elétrica) e a tensão no fio. Usamos Itaipu como exemplo de escala: 20 unidades de 700 MW.

Cada quadro é pixel art desenhada por código, e a música é original. Usina, casa e equipamentos são genéricos.

Capítulos
{capitulos}

Simplificado de propósito
- A usina do desenho é genérica. Os números de Itaipu (queda de projeto de 118 m, 700 m³/s, 700 MW por unidade) são usados como exemplo; a queda real muda com o nível da represa e do rio.
- A conta de 810 MW multiplica vazão, queda e gravidade. A diferença para os 700 MW entregues inclui as perdas e a queda de projeto usada na conta; não é uma medição da eficiência.
- No conduto forçado a velocidade da água quase não muda (o tubo tem a mesma largura); o que cresce com a profundidade é a pressão. As palhetas e o rotor transformam essa pressão em velocidade e giro.
- O caracol, as palhetas e o rotor aparecem vistos de cima, com menos peças do que uma turbina real. O gerador tem 12 polos no desenho; os de Itaipu têm muito mais e giram mais rápido do que mostramos (câmera lenta).
- A luz amarela que anda pelos fios representa a energia. Na corrente alternada os elétrons não viajam da usina até a sua casa: eles vão e voltam no lugar, 60 vezes por segundo, e a energia é que segue pela rede.
- O caminho de tensões (13,8 kV, 500 kV, 138 kV, 13,8 kV, 220/127 V) é um exemplo com tensões padronizadas no Brasil; cada usina e cada cidade tem o seu. O transformador do desenho tem poucas voltas de fio; o de verdade tem a proporção certa para ir de 13,8 para 500 kV.
- As perdas de 4,2% e 0,5% a 1,1% são um exemplo de 1.000 MW por 160 km, citado pela Wikipedia; cada linha perde diferente.
- A participação das hidrelétricas (55,3%) é da oferta interna de eletricidade de 2024, no Balanço Energético Nacional 2025 da EPE.
- Nem toda unidade de Itaipu fica do lado que pintamos: separamos 10 de 60 Hz e 10 de 50 Hz no desenho só para contar.

Fontes
{fontes}

#hidreletrica #energia #comofunciona #pixelart #itaipu #eletricidade #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. A turbina (vista
# de cima) ocupa x 58..242; o gerador, 38..210; o tubo de sucção, 96..276; a
# casa, 112..292. Nas cenas de linhas e do Brasil o desenho muda de arranjo
# quando VERTICAL = True para caber no recorte.
PREFIXO = 'ep11-agua'
CORTES = [
    dict(id='c1', de=('turbina', 0.0), ate=('turbina', 36.0), x=60, gancho=['DENTRO DE', 'UMA TURBINA'],
         titulo='Uma gota de água dentro de uma turbina de hidrelétrica 💧',
         descricao='A água entra num caracol, passa pelas palhetas e empurra as pás do rotor. É a turbina Francis, a mais usada nas grandes usinas.'),
    dict(id='c2', de=('gerador', 0.0), ate=('gerador', 36.0), x=34, gancho=['COMO NASCE', 'A ENERGIA'],
         titulo='Como um gerador transforma giro em eletricidade ⚡',
         descricao='Ímãs girando perto de bobinas de fio fazem a corrente andar: é a indução. Norte, sul, norte: a corrente vai e volta 60 vezes por segundo no Brasil.'),
    dict(id='c3', de=('linhas', 7.0), ate=('linhas', 40.8), x=56, gancho=['POR QUE', '500.000 V?'],
         titulo='Por que as linhas de transmissão usam tanta tensão? 🔌',
         descricao='O fio esquenta com a corrente, e a perda cresce com o quadrado dela. Dobrar a tensão corta a corrente pela metade e a perda por 4.'),
    dict(id='c4', de=('casa', 20.4), ate=('casa', 48.0), x=112, gancho=['DO POSTE', 'À TOMADA'],
         titulo='O último trecho da energia: do poste até a lâmpada 💡',
         descricao='O transformador do poste baixa a tensão para 220 ou 127 volts. O fio passa pelo medidor, corre na parede até a tomada e a luz acende.'),
    dict(id='c5', de=('saida', 0.0), ate=('saida', 23.6), x=96, gancho=['A ÁGUA É', 'GASTA?'],
         titulo='A hidrelétrica gasta a água? 🌊',
         descricao='Não: depois de empurrar a turbina, a água sai pelo tubo de sucção, mais devagar, e volta para o rio. Quem segue viagem é a energia.'),
    dict(id='c6', de=('brasil', 0.0), ate=('brasil', 21.8), x=40, gancho=['55% DA', 'NOSSA LUZ'],
         titulo='De onde vem a eletricidade do Brasil? 🇧🇷',
         descricao='Em 2024, 55,3% da eletricidade do Brasil veio das hidrelétricas (EPE, Balanço Energético Nacional 2025). Depois vêm vento, sol e biomassa.'),
]
