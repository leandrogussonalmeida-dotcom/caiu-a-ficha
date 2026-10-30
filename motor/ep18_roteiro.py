#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep18 (série COMO VOA / FLUTUA): Como um foguete chega ao espaço.

A ideia: o foguete não se apoia no ar. Ele joga gás quente para baixo, muito
rápido, e o gás empurra o foguete para cima (3ª lei de Newton) — por isso
funciona até melhor no vácuo. Ele leva o próprio oxidante; turbobombas
empurram combustível e oxigênio líquido para a câmara de combustão; a tubeira
em forma de sino acelera o gás até ficar supersônico. Para sair do chão, o
empuxo tem que ser maior que o peso; quase toda a massa é propelente, então
ele fica mais leve e acelera mais; os estágios vazios são soltos. Ele sobe reto,
inclina um pouco e a gravidade vai deitando a trajetória (curva gravitacional):
o objetivo é andar DE LADO. Passa a linha de Kármán (100 km) e só fica lá em
cima com cerca de 7,8 km/s: caindo em volta da Terra e sempre errando o chão.
Toque brasileiro: Alcântara (MA), a base mais perto do equador, onde o chão já
anda a ~465 m/s para o leste.

Protagonista: um foguete genérico de 2 estágios (sem bandeira, logotipo nem
pintura de agência), com painel de altitude, velocidade, massa e estágio.
O voo é uma SIMULAÇÃO de verdade (ep18_desenho.Voo): 2 estágios, gravidade,
Terra redonda, curva gravitacional; sem arrasto do ar e sem a rotação da Terra.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  NASA Glenn, "Rocket Principles": 3ª lei — o foguete empurra o gás e o gás
      empurra o foguete; no espaço o gás de escape sai livre: foguetes
      "funcionam melhor no espaço do que no ar"; na plataforma as forças estão
      equilibradas; para subir o empuxo tem que ser maior que o peso; a maior
      parte da massa do foguete é propelente; a massa diminui durante o voo.
  F2  Wikipedia, "Rocket": movido só pelo propelente que carrega, sem precisar
      do oxigênio do ar; funciona fora da atmosfera (mais eficiente lá); para
      decolar na vertical os motores precisam dar mais que a gravidade local;
      sobe na vertical, vai inclinando (muitas vezes numa curva gravitacional)
      e fica cada vez mais horizontal até a velocidade de órbita, quando o
      motor desliga.
  F3  Wikipedia, "Liquid-propellant rocket": bipropelente = combustível líquido
      (hidrogênio, RP-1) + oxidante líquido (oxigênio líquido); turbobomba
      centrífuga leve empurra os propelentes para a câmara; a câmara mistura e
      queima os dois líquidos; os gases entram na tubeira por uma garganta.
  F4  Wikipedia, "Rocket engine nozzle": tubeira de Laval (convergente-
      divergente) acelera os gases a velocidades supersônicas; na garganta a
      velocidade fica sônica e depois cada vez mais supersônica; sino é a
      forma frequente; velocidade de escape de bipropelente líquido: 2,9 a 4,5 km/s.
  F5  Wikipedia, "Propellant mass fraction": tipicamente 0,8 a 0,9.
  F6  Wikipedia, "Multistage rocket": cada estágio tem motores e propelente
      próprios; soltar o estágio vazio diminui a massa; foguetes de 2
      estágios são bem comuns; raramente mais de 3.
  F7  Wikipedia, "Gravity turn": sobe reto, inclina alguns graus (pitchover) e
      a gravidade vai deitando a trajetória; o motor segue empurrando e o
      veículo chega com altitude e velocidade horizontal para a órbita.
  F8  Wikipedia, "Kármán line": FAI: 100 km; as Forças Armadas dos EUA usam
      50 milhas (80 km) para dar asas de astronauta.
  F9  Wikipedia, "Low Earth orbit": cerca de 7,8 km/s = 28.000 km/h em órbita
      baixa; quem está em órbita está em queda livre permanente em volta da Terra.
  F10 Wikipedia, "Earth's rotation": a Terra gira para o leste; no equador o
      chão anda cerca de 1.674,7 km/h (465,2 m/s); no Centro Espacial Kennedy
      (28,59° N), cerca de 1.470,2 km/h.
  F11 Britannica, "launch vehicle — Launch bases": base o mais perto possível do
      equador; muitos lançamentos vão para o leste para aproveitar a rotação.
  F12 Wikipedia, "Alcântara Space Center": no Maranhão, costa atlântica norte do
      Brasil, 02°20′ S; "a base de lançamento mais perto do equador".
  F13 Wikipedia, "Payload fairing": a coifa protege a carga da força e do calor do
      ar; fora da atmosfera ela é solta.
  F14 Conta / simulação deste vídeo (ep18_desenho.Voo): 548 t na decolagem,
      490 t de propelente (89%), empuxo 1,4 vez o peso, motor do 1º estágio
      desliga aos 2 min 25 s, 100 km aos 2 min 56 s, órbita (~7,8 km/s a ~190 km)
      aos ~8 min; 7,8 km/s x 3.600 = 28.080 km/h; na tubeira, área de saída 20
      vezes a da garganta -> Mach ~3,7, gás a ~2.900 m/s (dentro da faixa de F4).
"""

TITULO = "Como um foguete chega ao espaço | Empuxo, estágios e órbita em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=5, papel='break'),             # 15 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='newton', gen='lofi', bars=14, papel='drop'),             # 42 s
    dict(id='partes', gen='synthwave', bars=20, papel='drop'),        # 48 s (7 peças)
    dict(id='motor', gen='lofi', bars=14, papel='drop'),              # 42 s
    dict(id='decolagem', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='massa', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='subida', gen='synthwave', bars=24, papel='drop'),        # 57,6 s
    dict(id='separacao', gen='lofi', bars=10, papel='drop'),          # 30 s
    dict(id='karman', gen='lofi', bars=12, papel='break'),            # 36 s
    dict(id='orbita', gen='synthwave', bars=22, papel='drop'),        # 52,8 s
    dict(id='equador', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 6.4, "ESTE FOGUETE VAI ATÉ O ESPAÇO.", "CONTAGEM NO RITMO DA MÚSICA...", ()),
        (6.6, 14.6, "EM CERCA DE 8 MINUTOS ELE ESTARÁ", "A *28.000 KM/H*. COMO?", ('F14', 'F9')),
    ],
    'newton': [
        (0.5, 7.4, "SOLTE UM BALÃO CHEIO: O AR SAI", "PARA UM LADO E O BALÃO VAI PARA O OUTRO.", ()),
        (7.6, 14.4, "É A *3ª LEI DE NEWTON*: TODA AÇÃO", "TEM UMA REAÇÃO IGUAL E CONTRÁRIA.", ('F1',)),
        (14.6, 21.4, "O FOGUETE FAZ O MESMO: JOGA *GÁS*", "*QUENTE* PARA BAIXO, MUITO RÁPIDO.", ('F1',)),
        (21.6, 28.4, "O FOGUETE EMPURRA O GÁS, E O GÁS", "EMPURRA O FOGUETE *PARA CIMA*.", ('F1',)),
        (28.6, 35.4, "ELE NÃO PRECISA DE AR PARA", "SE APOIAR. NO ESPAÇO, O GÁS SAI LIVRE.", ('F1',)),
        (35.6, 41.6, "POR ISSO O FOGUETE FUNCIONA", "*ATÉ MELHOR NO VÁCUO*.", ('F1', 'F2')),
    ],
    'partes': [
        (0.3, 6.6, "NO TOPO, A *COIFA* PROTEGE A CARGA", "(UM SATÉLITE) DA FORÇA DO AR.", ('F13',)),
        (6.8, 13.4, "O *2º ESTÁGIO*: TANQUES E MOTOR", "PRÓPRIOS, PARA O FIM DA SUBIDA.", ('F6',)),
        (13.6, 20.2, "NO 1º ESTÁGIO, O *OXIGÊNIO LÍQUIDO*:", "O FOGUETE LEVA O SEU PRÓPRIO.", ('F2', 'F3')),
        (20.4, 27.0, "O *COMBUSTÍVEL*, NUM TANQUE", "SEPARADO (EX.: QUEROSENE, O RP-1).", ('F3',)),
        (27.2, 33.8, "*TURBOBOMBAS* EMPURRAM OS DOIS", "LÍQUIDOS PARA O MOTOR.", ('F3',)),
        (34.0, 40.6, "NA *CÂMARA DE COMBUSTÃO* ELES SE", "MISTURAM E QUEIMAM.", ('F3',)),
        (40.8, 47.6, "E A *TUBEIRA*, O BOCAL EM FORMA", "DE SINO, SOLTA O GÁS.", ('F4',)),
    ],
    'motor': [
        (0.5, 6.8, "VAMOS ABRIR O MOTOR. CÂMERA LENTA.", "AS TURBOBOMBAS GIRAM...", ('F3',)),
        (7.0, 13.8, "...E OS DOIS LÍQUIDOS ENTRAM NA", "*CÂMARA*, ONDE QUEIMAM.", ('F3',)),
        (14.0, 20.8, "O GÁS QUENTE CORRE PARA O PONTO", "MAIS ESTREITO: A *GARGANTA*.", ('F3', 'F4')),
        (21.0, 27.8, "NA GARGANTA ELE CHEGA À", "*VELOCIDADE DO SOM*.", ('F4',)),
        (28.0, 34.8, "NO SINO ELE SE EXPANDE E FICA", "CADA VEZ MAIS RÁPIDO: *SUPERSÔNICO*.", ('F4',)),
        (35.0, 41.6, "SAI A *2,9 A 4,5 KM/S*.", "AQUI: CERCA DE 2.900 M/S.", ('F4', 'F14')),
    ],
    'decolagem': [
        (0.5, 7.4, "NA PLATAFORMA, AS FORÇAS ESTÃO", "*EQUILIBRADAS*: O PESO PUXA PARA BAIXO.", ('F1',)),
        (7.6, 14.4, "OS MOTORES ACENDEM E O *EMPUXO*,", "O EMPURRÃO DO GÁS, VAI CRESCENDO.", ('F1',)),
        (14.6, 21.4, "SÓ SOBE QUANDO O EMPUXO FICA", "*MAIOR QUE O PESO*.", ('F1', 'F2')),
        (21.6, 28.4, "NO NOSSO FOGUETE, O EMPUXO É", "*1,4 VEZ* O PESO.", ('F14',)),
        (28.6, 35.6, "NO COMEÇO ELE SOBE DEVAGAR:", "ESTÁ NO SEU PESO *MÁXIMO*.", ('F1',)),
    ],
    'massa': [
        (0.5, 7.4, "QUASE TUDO NESTE FOGUETE É", "*PROPELENTE*: COMBUSTÍVEL E OXIDANTE.", ('F1',)),
        (7.6, 14.4, "NOS FOGUETES, EM GERAL, É DE", "*80% A 90%* DA MASSA NA DECOLAGEM.", ('F5',)),
        (14.6, 21.4, "NO NOSSO: *490 DE 548 TONELADAS*.", "ISSO DÁ 89%.", ('F14',)),
        (21.6, 28.4, "A CADA SEGUNDO ELE QUEIMA TONELADAS", "E FICA *MAIS LEVE*.", ('F1', 'F14')),
        (28.6, 35.6, "MESMO EMPUXO, MENOS MASSA:", "ELE *ACELERA CADA VEZ MAIS*.", ('F1',)),
    ],
    'subida': [
        (0.5, 7.6, "PRIMEIRO ELE SUBIU *RETO*.", "LOGO DEPOIS, INCLINOU UM POUCO.", ('F7',)),
        (7.8, 15.6, "AGORA A GRAVIDADE VAI DEITANDO", "A TRAJETÓRIA, AOS POUCOS.", ('F7',)),
        (15.8, 23.6, "É A *CURVA GRAVITACIONAL*.", "O MOTOR SÓ SEGUE EMPURRANDO.", ('F7',)),
        (23.8, 31.6, "O OBJETIVO NÃO É SÓ SUBIR:", "É GANHAR *VELOCIDADE DE LADO*.", ('F2', 'F7')),
        (31.8, 39.6, "OLHE O PAINEL: A VELOCIDADE", "SOBE CADA VEZ MAIS RÁPIDO.", ('F14',)),
        (39.8, 47.6, "E A MASSA DESPENCA: O TANQUE DO", "1º ESTÁGIO ESTÁ QUASE *VAZIO*.", ('F14',)),
        (47.8, 57.0, "O AR LÁ FORA É CADA VEZ MAIS RALO", "E O CÉU VAI FICANDO *PRETO*.", ()),
    ],
    'separacao': [
        (0.5, 5.8, "TANQUES DO 1º ESTÁGIO VAZIOS:", "O MOTOR *DESLIGA*.", ('F6', 'F14')),
        (6.0, 11.8, "O ESTÁGIO VAZIO É *SOLTO*:", "MENOS PESO MORTO PARA CARREGAR.", ('F6',)),
        (12.0, 18.8, "O *2º ESTÁGIO* ACENDE", "O SEU PRÓPRIO MOTOR.", ('F6',)),
        (19.0, 25.8, "FOGUETES DE 2 ESTÁGIOS SÃO BEM", "COMUNS. MAIS DE 3 É *RARO*.", ('F6',)),
        (26.0, 29.8, "E O 1º ESTÁGIO CAI DE VOLTA.", "", ()),
    ],
    'karman': [
        (0.5, 7.6, "ONDE COMEÇA O ESPAÇO?", "O AR NÃO ACABA DE UMA VEZ.", ('F8',)),
        (7.8, 14.6, "A *LINHA DE KÁRMÁN*, USADA PELA FAI:", "*100 KM* DE ALTITUDE.", ('F8',)),
        (14.8, 21.6, "AS FORÇAS ARMADAS DOS EUA USAM", "*80 KM* (50 MILHAS).", ('F8',)),
        (21.8, 28.6, "FORA DO AR, A *COIFA* É SOLTA:", "NÃO PRECISA MAIS PROTEGER A CARGA.", ('F13',)),
        (28.8, 35.6, "MAS CHEGAR AO ESPAÇO NÃO BASTA", "PARA FICAR LÁ EM CIMA...", ('F9',)),
    ],
    'orbita': [
        (0.5, 7.6, "O 2º ESTÁGIO EMPURRA QUASE NA", "*HORIZONTAL*. ACELERADO 14 VEZES.", ('F2', 'F14')),
        (7.8, 14.6, "EM ÓRBITA BAIXA SÃO CERCA DE", "*7,8 KM/S*: *28.000 KM/H*.", ('F9',)),
        (14.8, 21.8, "ATINGIU A VELOCIDADE:", "O MOTOR *DESLIGA*.", ('F2',)),
        (22.0, 29.6, "SE ELE PARASSE LÁ EM CIMA,", "*CAIRIA* DE VOLTA.", ('F9',)),
        (29.8, 37.4, "MAIS RÁPIDO, ELE CAI MAIS LONGE.", "", ('F9',)),
        (37.6, 45.2, "A 7,8 KM/S A TERRA *SE CURVA* E ELE", "SEMPRE ERRA O CHÃO.", ('F9',)),
        (45.4, 52.6, "É A *ÓRBITA*: CAINDO EM VOLTA DA", "TERRA SEM PARAR.", ('F9',)),
    ],
    'equador': [
        (0.5, 7.4, "A TERRA GIRA PARA O *LESTE*.", "E O CHÃO GIRA JUNTO.", ('F10',)),
        (7.6, 14.4, "NO EQUADOR, O CHÃO ANDA A", "*465 M/S*: CERCA DE 1.675 KM/H.", ('F10',)),
        (14.6, 21.4, "LANÇANDO PARA O LESTE, O FOGUETE", "JÁ SAI COM ESSE *EMPURRÃO*.", ('F11',)),
        (21.6, 28.4, "NO MARANHÃO, O *CENTRO DE LANÇAMENTO*", "*DE ALCÂNTARA* FICA A 2° DO EQUADOR.", ('F12',)),
        (28.6, 35.6, "É A BASE DE LANÇAMENTO", "*MAIS PERTO DO EQUADOR*.", ('F12',)),
    ],
    'resumo': [
        (0.5, 7.0, "O FOGUETE JOGA GÁS PARA BAIXO", "E O GÁS O EMPURRA PARA *CIMA*.", ('F1',)),
        (7.3, 14.4, "ELE LEVA O PRÓPRIO *OXIDANTE*:", "NÃO PRECISA DO AR.", ('F2',)),
        (14.7, 21.8, "SOLTA OS *ESTÁGIOS VAZIOS*", "NO CAMINHO.", ('F6',)),
        (22.1, 29.6, "E ANDA *DE LADO* A 28.000 KM/H:", "CAINDO EM VOLTA DA TERRA.", ('F9',)),
    ],
}

FONTES = {
    'F1': ('NASA Glenn Research Center, "Rocket Principles"', 'https://www.grc.nasa.gov/WWW/K-12/TRC/Rockets/rocket_principles.html'),
    'F2': ('Wikipedia, "Rocket"', 'https://en.wikipedia.org/wiki/Rocket'),
    'F3': ('Wikipedia, "Liquid-propellant rocket"', 'https://en.wikipedia.org/wiki/Liquid-propellant_rocket'),
    'F4': ('Wikipedia, "Rocket engine nozzle"', 'https://en.wikipedia.org/wiki/Rocket_engine_nozzle'),
    'F5': ('Wikipedia, "Propellant mass fraction" (tipicamente 0,8 a 0,9)', 'https://en.wikipedia.org/wiki/Propellant_mass_fraction'),
    'F6': ('Wikipedia, "Multistage rocket"', 'https://en.wikipedia.org/wiki/Multistage_rocket'),
    'F7': ('Wikipedia, "Gravity turn"', 'https://en.wikipedia.org/wiki/Gravity_turn'),
    'F8': ('Wikipedia, "Kármán line"', 'https://en.wikipedia.org/wiki/K%C3%A1rm%C3%A1n_line'),
    'F9': ('Wikipedia, "Low Earth orbit" (cerca de 7,8 km/s = 28.000 km/h; queda livre em volta da Terra)',
           'https://en.wikipedia.org/wiki/Low_Earth_orbit'),
    'F10': ('Wikipedia, "Earth\'s rotation" (465,2 m/s no equador)', 'https://en.wikipedia.org/wiki/Earth%27s_rotation'),
    'F11': ('Encyclopaedia Britannica, "launch vehicle: Launch bases"', 'https://britannica.com/technology/launch-vehicle/Launch-bases'),
    'F12': ('Wikipedia, "Alcântara Space Center"', 'https://en.wikipedia.org/wiki/Alc%C3%A2ntara_Space_Center'),
    'F13': ('Wikipedia, "Payload fairing"', 'https://en.wikipedia.org/wiki/Payload_fairing'),
    'F14': ('Conta / simulação deste vídeo: foguete genérico de 2 estágios (548 t, 490 t de propelente, '
            'empuxo 1,4 vez o peso), gravidade e Terra redonda, sem arrasto do ar', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'newton': 'Ação e reação: o balão e o foguete',
                'partes': 'As partes do foguete', 'motor': 'Dentro do motor: câmara e tubeira',
                'decolagem': 'Empuxo maior que o peso', 'massa': 'Quase tudo é propelente',
                'subida': 'A curva gravitacional', 'separacao': 'Separação dos estágios',
                'karman': 'Onde começa o espaço', 'orbita': '28.000 km/h: caindo em volta da Terra',
                'equador': 'Alcântara e o empurrão do equador', 'resumo': 'Resumo'}

DESCRICAO = """Como um foguete sai do chão e chega ao espaço? Ele não se apoia no ar: joga gás quente para baixo, muito rápido, e o gás empurra o foguete para cima. Por isso ele funciona até melhor no vácuo.

Neste vídeo a gente abre um foguete genérico de 2 estágios peça por peça (coifa, tanques de oxigênio líquido e de combustível, turbobombas, câmara de combustão e tubeira), entra no motor em câmera lenta para ver o gás ficar supersônico, e acompanha um voo inteiro com o painel de altitude, velocidade, massa e estágio: a decolagem, a curva gravitacional, a separação dos estágios, a linha de Kármán e a órbita a 28.000 km/h. No fim: por que lançar perto do equador ajuda, e o Centro de Lançamento de Alcântara, no Maranhão.

Cada quadro é pixel art desenhada por código, e a música é original. A contagem regressiva e a separação dos estágios caem nas batidas da música.

Capítulos
{capitulos}

Simplificado de propósito
- O foguete é genérico (não é nenhum foguete real) e o voo do painel é uma simulação feita para o vídeo: 2 estágios, gravidade e Terra redonda, mas sem o arrasto do ar e sem a rotação da Terra. Os números do painel (altitude, velocidade, massa, tempos) saem dessa simulação; um foguete real faz um caminho parecido, com números diferentes.
- A coifa foi solta sem mudar a massa no painel; a massa dela é pequena perto do resto.
- A contagem regressiva vai no ritmo da música (uma batida por número), mais rápida que a de verdade.
- O 1º estágio desenhado tem 1 motor; muitos foguetes têm vários motores no 1º estágio.
- No motor aberto, a velocidade do gás foi calculada com um modelo simples de tubeira (área de saída 20 vezes a da garganta); o resultado, cerca de 2.900 m/s, fica dentro da faixa de 2,9 a 4,5 km/s da fonte.
- As cenas de voo alternam câmera lenta e acelerado; o painel mostra quando.
- A Terra e a órbita do capítulo da órbita não estão em escala (a órbita baixa fica muito mais perto da Terra do que no desenho). Os "lançamentos" mais lentos que caem de volta são a ideia do canhão de Newton, não voos de verdade.
- "Mais de 3 estágios é raro" resume a fonte: foguetes de verdade raramente usam mais de 3.
- O mapa da América do Sul é aproximado.

Fontes
{fontes}

#foguete #espaco #comofunciona #pixelart #fisica #newton #alcantara #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nas cenas de voo o
# foguete fica centrado em x 150 (recorte 60..240).
PREFIXO = 'ep18-foguete'
CORTES = [
    dict(id='c1', de=('newton', 14.6), ate=('newton', 41.6), x=60, gancho=['SEM AR', 'PRA EMPURRAR'],
         titulo='Como o foguete anda no espaço, onde não tem ar? 🚀',
         descricao='O foguete joga gás quente para baixo, muito rápido, e o gás empurra o foguete para cima (3ª lei de Newton). Ele não precisa de ar para se apoiar: funciona até melhor no vácuo.'),
    dict(id='c2', de=('motor', 14.0), ate=('motor', 42.0), x=60, gancho=['GÁS', 'SUPERSÔNICO'],
         titulo='Dentro do motor do foguete: o gás fica supersônico 🔥',
         descricao='Na garganta da tubeira o gás chega à velocidade do som; no sino ele se expande e sai supersônico, a 2,9 a 4,5 km/s.'),
    dict(id='c3', de=('decolagem', 0.0), ate=('decolagem', 36.0), x=60, gancho=['POR QUE', 'ELE SOBE?'],
         titulo='Por que o foguete sobe? Empuxo maior que o peso',
         descricao='Na plataforma as forças estão equilibradas. O foguete só sobe quando o empuxo dos motores fica maior que o peso dele.'),
    dict(id='c4', de=('separacao', 0.0), ate=('separacao', 30.0), x=60, gancho=['SOLTANDO', 'O ESTÁGIO'],
         titulo='A separação dos estágios do foguete, em câmera lenta',
         descricao='Com os tanques vazios, o 1º estágio desliga e é solto: menos peso morto. O 2º estágio acende o seu próprio motor.'),
    dict(id='c5', de=('orbita', 22.0), ate=('orbita', 52.8), x=60, gancho=['CAINDO', 'SEM PARAR'],
         titulo='Por que o satélite não cai? Ele cai! 🌍',
         descricao='Em órbita baixa a cerca de 7,8 km/s (28.000 km/h), o foguete continua caindo, mas a Terra se curva e ele sempre erra o chão.'),
    dict(id='c6', de=('equador', 0.0), ate=('equador', 36.0), x=40, gancho=['O EMPURRÃO', 'DO EQUADOR'],
         titulo='Por que Alcântara é um ótimo lugar para lançar foguetes? 🇧🇷',
         descricao='No equador o chão anda a 465 m/s para o leste. Lançando para o leste, o foguete já sai com esse empurrão. O Centro de Lançamento de Alcântara, no Maranhão, é a base mais perto do equador.'),
]
