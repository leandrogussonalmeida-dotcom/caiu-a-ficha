#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep22 (série COMO VOA / FLUTUA): Como o balão de ar quente sobe.

A ideia: ar quente é menos denso (as moléculas se mexem mais rápido e se
afastam; com a boca aberta embaixo, parte do ar sai e sobra menos ar no mesmo
espaço). O empuxo é o peso do ar frio que o balão tira do lugar (Arquimedes,
o mesmo do navio do ep06, agora no ar). Cada metro cúbico de ar quente
levanta só ~0,26 kg, por isso o envelope é enorme (2.800 metros cúbicos, o
tamanho mais usado). As partes; como enche; como sobe (queimador) e desce
(esfria / paraquedas); como "dirige" (camadas de vento). História: Gusmão em
Lisboa (1709) e os Montgolfier (1783). No fim, um aviso: soltar balão que pode
causar incêndio é crime no Brasil.

Protagonista: um balão genérico de listras inventadas, com painel de
altitude, temperatura do ar de dentro e empuxo x peso. O voo dos capítulos
"subir" e "descer" é CALCULADO (ep22_desenho.Voo): queimador, perda de calor,
paraquedas, empuxo, peso, arrasto e ar mais ralo com a altitude. Os jatos do
queimador caem nas batidas da música.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Wikipedia, "Kinetic theory of gases": o gás é feito de partículas
      minúsculas em movimento constante e aleatório; a energia cinética média
      das moléculas é proporcional à temperatura absoluta ("quanto mais quente,
      mais violento o movimento", Hooke).
  F2  Wikipedia, "Density of air": a 20 °C e 101,325 kPa, ar seco = 1,2041 kg/m³;
      ar mais quente é menos denso que o mais frio e sobe por empuxo.
  F3  Wikipedia, "Hot air balloon": 2.800 m³ a 99 °C: ar de dentro 0,9486 kg/m³,
      levanta 723,5 kg; a 120 °C, 0,8978 kg/m³ e 867,3 kg; a 99 °C são precisos
      ~3,91 m³ para cada kg; temperatura máxima ~120 °C (o tecido enfraquece);
      tamanho mais usado ~2.800 m³, para 3 a 5 pessoas; combustível: propano;
      cada queimador: 2 a 3 MW; chama-piloto; o paraquedas no topo solta ar
      quente para descer; também se desce deixando o ar esfriar; não dá para
      dirigir: o piloto muda de altitude para pegar ventos diferentes; o
      empuxo cai ~3% a cada 1.000 m; cesto de vime; irmãos Montgolfier em 1783;
      primeiro voo livre com pessoas em 21/11/1783.
  F4  Wikipedia, "Buoyancy": um objeto num fluido é empurrado para cima com
      força igual ao peso do fluido que ele desloca (Arquimedes); vale para
      gases também; um balão para de subir quando ele e o ar deslocado pesam igual.
  F5  Universidade de Bristol (Escola de Química), "Hot air balloon parts":
      a parte mais baixa do envelope é de tecido resistente a chamas (a saia);
      no topo, um grande buraco fechado pelo paraquedas, aberto por uma corda;
      envelope de náilon reforçado que aguenta calor; queimador alimentado
      por botijões de propano no cesto; cesto de vime (salgueiro) trançado:
      leve, forte e flexível, amortece o pouso.
  F6  Portal do Trânsito, "Como se pilota um balão": "o envelope, como é
      chamado o balão, é feito de nylon rip-stop"; cesto de vime; maçarico;
      inflado com ar ambiente por uma grande ventoinha; com ~60% do espaço
      ocupado, liga-se o maçarico; para descer abre-se uma tampa em forma de
      paraquedas que solta o ar quente; o balão vai guiado pelo vento.
  F7  balloonmuseum.com, "How Do Hot Air Balloons Work?": botijões de propano
      no cesto; o paraquedas no topo solta ar quente para descer; não existe
      mecanismo de direção: o piloto controla a altitude e o vento leva.
  F8  Olhar Digital, "Como um balão voa?": para descer, o piloto reduz o
      aquecimento e deixa o ar esfriar; ajusta a altitude para aproveitar
      correntes de vento diferentes.
  F9  Wikipedia, "Bartolomeu de Gusmão": nascido em Santos, no Brasil colônia;
      em 8 de agosto de 1709, na sala da Casa da Índia, em Lisboa, diante da
      Corte, fez um pequeno balão subir até o teto com a combustão de uma chama.
  F10 SEMIL (Secretaria de Meio Ambiente de SP): Lei 9.605/1998, art. 42:
      "Fabricar, vender, transportar ou soltar balões que possam provocar
      incêndios..." Pena: detenção de 1 a 3 anos ou multa, ou ambas.
  F11 Contas / simulação deste vídeo: 1,2041 x 293,15 / 372,15 = 0,95 kg/m³
      (gás ideal, mesma pressão); 2.800 x 1,207 = 3.380 kg de ar frio deslocado,
      2.800 x 0,9486 = 2.656 kg de ar quente: sobram ~720 kg (F3); 723,5 / 2.800
      = 0,26 kg por metro cúbico; o perfil desenhado com 2.800 m³ tem ~19,4 m de
      altura e ~17,5 m de largura; velocidade das moléculas proporcional à raiz
      da temperatura absoluta: raiz(372/293) = 1,13 (13% mais rápidas); voo
      calculado com 700 kg: decola com o ar a ~97 °C.
"""

TITULO = "Como o balão de ar quente sobe? | Empuxo, queimador e vento em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),             # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='particulas', gen='lofi', bars=16, papel='drop'),         # 48 s
    dict(id='empuxo', gen='lofi', bars=12, papel='drop'),             # 36 s
    dict(id='conta', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='partes', gen='synthwave', bars=20, papel='drop'),        # 48 s (6 peças x 8 s)
    dict(id='inflar', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='subir', gen='lofi', bars=18, papel='drop'),              # 54 s
    dict(id='descer', gen='lofi', bars=14, papel='drop'),             # 42 s
    dict(id='vento', gen='synthwave', bars=24, papel='drop'),         # 57,6 s
    dict(id='historia', gen='lofi', bars=14, papel='break'),          # 42 s
    dict(id='resumo', gen='lofi', bars=12, papel='drop'),             # 36 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 6.2, "SEM MOTOR, SEM ASA, SEM HÉLICE:", "ESTE BALÃO LEVA ATÉ *5 PESSOAS*.", ('F3',)),
        (6.4, 11.8, "O SEGREDO É SÓ *AR QUENTE*.", "MAS POR QUE AR QUENTE SOBE?", ('F2',)),
    ],
    'particulas': [
        (0.5, 7.6, "O AR É FEITO DE *MOLÉCULAS* MINÚSCULAS,", "SEMPRE EM MOVIMENTO.", ('F1',)),
        (7.8, 15.6, "AQUECIDAS, ELAS SE MEXEM *MAIS RÁPIDO*", "E SE EMPURRAM PARA LONGE.", ('F1',)),
        (15.8, 23.6, "A CAIXA É ABERTA EMBAIXO, COMO O", "BALÃO: PARTE DO AR *SAI*.", ('F11',)),
        (23.8, 31.6, "1 METRO CÚBICO DE AR A 20 °C", "PESA CERCA DE *1,2 KG*.", ('F2',)),
        (31.8, 39.6, "O MESMO METRO CÚBICO A 99 °C:", "SÓ *0,95 KG*. MENOS MOLÉCULAS.", ('F3', 'F11')),
        (39.8, 47.6, "AR QUENTE É *MENOS DENSO*: MAIS LEVE", "QUE O AR FRIO EM VOLTA.", ('F2',)),
    ],
    'empuxo': [
        (0.5, 7.4, "LEMBRA DO NAVIO? A ÁGUA EMPURRA PARA", "CIMA COM O PESO DA ÁGUA TIRADA.", ('F4',)),
        (7.6, 14.4, "O *AR* FAZ O MESMO. É O *EMPUXO*,", "O PRINCÍPIO DE ARQUIMEDES.", ('F4',)),
        (14.6, 21.4, "O BALÃO TIRA DO LUGAR 2.800 METROS", "CÚBICOS DE AR FRIO: *3.380 KG*.", ('F3', 'F11')),
        (21.6, 28.4, "O AR QUENTE QUE FICA NO LUGAR", "PESA SÓ *2.660 KG*.", ('F3', 'F11')),
        (28.6, 35.6, "A DIFERENÇA, *720 KG*, É O QUE", "SOBRA PARA LEVANTAR O BALÃO.", ('F3',)),
    ],
    'conta': [
        (0.5, 7.4, "CADA METRO CÚBICO DE AR A 99 °C", "LEVANTA SÓ UNS *0,26 KG*.", ('F11',)),
        (7.6, 14.4, "PARA ERGUER 1 KG, SÃO PRECISOS", "UNS *3,9 METROS CÚBICOS*.", ('F3',)),
        (14.6, 21.4, "POR ISSO O ENVELOPE É ENORME: O", "MAIS USADO TEM *2.800 METROS CÚBICOS*.", ('F3',)),
        (21.6, 28.4, "LEVA DE *3 A 5 PESSOAS* E TEM QUASE", "20 METROS DE ALTURA.", ('F3', 'F11')),
        (28.6, 35.6, "MAIS QUENTE LEVANTA MAIS, MAS O LIMITE", "É UNS *120 °C*: O TECIDO NÃO AGUENTA.", ('F3',)),
    ],
    'partes': [
        (0.3, 8.0, "O *ENVELOPE* É O BALÃO EM SI:", "NÁILON QUE AGUENTA CALOR.", ('F5', 'F6')),
        (8.3, 16.0, "NO TOPO, O *PARAQUEDAS*: UMA TAMPA", "QUE O PILOTO ABRE PARA SOLTAR AR.", ('F5', 'F7')),
        (16.3, 24.0, "EMBAIXO, A *SAIA*: UM TECIDO", "QUE RESISTE AO FOGO.", ('F5',)),
        (24.3, 32.0, "O *QUEIMADOR* (OU MAÇARICO) SOLTA", "UMA CHAMA DE GÁS *PROPANO*.", ('F3', 'F6')),
        (32.3, 40.0, "O GÁS VAI EM *BOTIJÕES*", "DENTRO DO CESTO.", ('F5', 'F7')),
        (40.3, 47.6, "E O *CESTO* DE VIME TRANÇADO: LEVE,", "FORTE, E AMORTECE O POUSO.", ('F5', 'F6')),
    ],
    'inflar': [
        (0.5, 7.4, "ANTES DE DECOLAR, UMA *VENTOINHA*", "ENCHE O ENVELOPE COM AR DO LUGAR.", ('F6',)),
        (7.6, 14.4, "COM UNS *60%* CHEIO, O QUEIMADOR", "ACENDE E ESQUENTA ESSE AR.", ('F6',)),
        (14.6, 21.4, "O AR QUENTE EMPURRA PARA CIMA", "E O ENVELOPE *SE LEVANTA*.", ('F4',)),
        (21.6, 29.6, "O CESTO FICA DE PÉ.", "PRONTO PARA SUBIR.", ()),
    ],
    'subir': [
        (0.5, 7.4, "CADA QUEIMADOR SOLTA *2 A 3*", "*MEGAWATTS* DE CALOR.", ('F3',)),
        (7.6, 14.4, "QUANDO O EMPUXO PASSA DO PESO,", "O BALÃO *DECOLA*.", ('F4',)),
        (14.6, 21.4, "NOSSO BALÃO PESA 700 KG NO TOTAL.", "DECOLOU COM O AR A UNS *97 °C*.", ('F11',)),
        (21.6, 28.4, "MAIS JATOS: O AR ESQUENTA MAIS", "E A SUBIDA *ACELERA*.", ('F11',)),
        (28.6, 35.4, "O AR ESFRIA AOS POUCOS: O PILOTO", "*REPETE OS JATOS* PARA SEGUIR.", ('F8', 'F11')),
        (35.6, 43.4, "MENOS JATOS: O AR FICA NA MESMA", "TEMPERATURA E A SUBIDA, *CONSTANTE*.", ('F11',)),
        (43.6, 53.6, "LÁ EM CIMA O AR É MAIS RALO: A CADA", "1.000 M O BALÃO LEVANTA *3% MENOS*.", ('F3',)),
    ],
    'descer': [
        (0.5, 7.4, "PARA DESCER, O PILOTO *PARA OS JATOS*.", "O AR ESFRIA DEVAGAR.", ('F8',)),
        (7.6, 14.4, "EMPUXO MENOR QUE O PESO:", "O BALÃO *DESCE*.", ('F4', 'F11')),
        (14.6, 21.4, "PARA DESCER MAIS RÁPIDO, ELE ABRE O", "*PARAQUEDAS*: O AR QUENTE ESCAPA.", ('F3', 'F5', 'F6')),
        (21.6, 28.4, "PARAQUEDAS FECHADO, O PILOTO JÁ", "COMEÇA A *FREAR* COM JATOS.", ('F11',)),
        (28.6, 35.4, "PERTO DO CHÃO, A DESCIDA", "FICA *MAIS LENTA*.", ('F11',)),
        (35.6, 41.6, "E O CESTO DE VIME", "*AMORTECE* O POUSO.", ('F5',)),
    ],
    'vento': [
        (0.5, 7.6, "E PARA VIRAR? O BALÃO *NÃO TEM LEME*:", "ELE VAI PARA ONDE O VENTO VAI.", ('F7',)),
        (7.8, 15.6, "MAS O VENTO MUDA DE DIREÇÃO", "EM *ALTURAS DIFERENTES*.", ('F3', 'F8')),
        (15.8, 23.6, "AQUI, EMBAIXO, O VENTO VAI PARA", "A *DIREITA*...", ()),
        (23.8, 31.6, "O PILOTO SOBE ATÉ A CAMADA DE CIMA,", "ONDE O VENTO VAI PARA A *ESQUERDA*.", ('F3',)),
        (31.8, 39.6, "SUBINDO E DESCENDO, ELE ESCOLHE", "A *CAMADA DE VENTO* CERTA...", ('F3', 'F8')),
        (39.8, 47.6, "...E VOLTA, PASSANDO PELAS CAMADAS,", "ATÉ UM CAMPO PARA *POUSAR*.", ('F8',)),
        (47.8, 57.2, "DIREÇÃO, SÓ COM O VENTO.", "O PILOTO SÓ ESCOLHE A *ALTURA*.", ('F7',)),
    ],
    'historia': [
        (0.5, 7.4, "A IDEIA É ANTIGA. EM *1709*, EM LISBOA,", "BARTOLOMEU DE GUSMÃO...", ('F9',)),
        (7.6, 14.4, "...NASCIDO EM *SANTOS*, NO BRASIL,", "FEZ UM BALÃOZINHO SUBIR ATÉ O TETO.", ('F9',)),
        (14.6, 21.4, "ELE USOU A CHAMA DE UM FOGO,", "NUMA SALA, DIANTE DA CORTE.", ('F9',)),
        (21.6, 28.4, "EM *1783*, NA FRANÇA, OS IRMÃOS", "*MONTGOLFIER* FIZERAM BALÕES GRANDES.", ('F3',)),
        (28.6, 35.4, "EM *21 DE NOVEMBRO DE 1783*: O", "PRIMEIRO VOO LIVRE COM PESSOAS.", ('F3',)),
        (35.6, 41.6, "O PRINCÍPIO É O MESMO ATÉ HOJE:", "*AR QUENTE SOBE*.", ('F2',)),
    ],
    'resumo': [
        (0.5, 7.0, "AR QUENTE É *MENOS DENSO*:", "MAIS LEVE QUE O AR FRIO.", ('F2',)),
        (7.3, 14.0, "O AR FRIO EM VOLTA EMPURRA O", "BALÃO PARA CIMA: O *EMPUXO*.", ('F4',)),
        (14.3, 21.0, "QUEIMADOR ACESO: ELE *SOBE*.", "AR ESFRIANDO: ELE *DESCE*.", ('F3', 'F8')),
        (21.3, 28.0, "PARA OS LADOS, SÓ ACHANDO A", "*CAMADA DE VENTO* CERTA.", ('F3',)),
        (28.3, 35.6, "E ATENÇÃO: SOLTAR BALÃO QUE PODE", "CAUSAR INCÊNDIO É *CRIME* NO BRASIL.", ('F10',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Kinetic theory of gases"', 'https://en.wikipedia.org/wiki/Kinetic_theory_of_gases'),
    'F2': ('Wikipedia, "Density of air" (1,2041 kg/m³ a 20 °C)', 'https://en.wikipedia.org/wiki/Density_of_air'),
    'F3': ('Wikipedia, "Hot air balloon"', 'https://en.wikipedia.org/wiki/Hot_air_balloon'),
    'F4': ('Wikipedia, "Buoyancy" (princípio de Arquimedes)', 'https://en.wikipedia.org/wiki/Buoyancy'),
    'F5': ('Universidade de Bristol, "Hot air balloon parts"',
           'https://www.chm.bris.ac.uk/webprojects2003/hetherington/final/Hot_air_balloon_parts.html'),
    'F6': ('Portal do Trânsito, "Como se pilota um balão"',
           'https://www.portaldotransito.com.br/noticias/mobilidade-e-tecnologia/curiosidades/como-se-pilota-um-balao/'),
    'F7': ('balloonmuseum.com, "How Do Hot Air Balloons Work?"', 'https://balloonmuseum.com/?p=9647'),
    'F8': ('Olhar Digital, "Como um balão voa?"',
           'https://olhardigital.com.br/2025/06/21/carros-e-tecnologia/acidente-em-santa-catarina-como-um-balao-voa/'),
    'F9': ('Wikipedia, "Bartolomeu de Gusmão"', 'https://en.wikipedia.org/wiki/Bartolomeu_de_Gusm%C3%A3o'),
    'F10': ('SEMIL-SP, "Saiba como ajudar a combater a prática da soltura de balões" (Lei 9.605/1998, art. 42)',
            'https://semil.sp.gov.br/educacaoambiental/2024/08/saiba-como-ajudar-a-combater-a-pratica-da-soltura-de-baloes/'),
    'F11': ('Contas e simulação deste vídeo (gás ideal a mesma pressão; balão de 2.800 m³ e 700 kg; '
            'números de F2 e F3)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'particulas': 'Por que o ar quente é mais leve',
                'empuxo': 'Arquimedes no ar: o empuxo', 'conta': 'Por que o balão é tão grande',
                'partes': 'As partes do balão', 'inflar': 'Enchendo o balão',
                'subir': 'Como ele sobe: o queimador', 'descer': 'Como ele desce: o paraquedas',
                'vento': 'Como "dirigir": as camadas de vento', 'historia': 'Gusmão (1709) e os Montgolfier (1783)',
                'resumo': 'Resumo'}

DESCRICAO = """Como um balão de ar quente sobe, se ele não tem motor, asa nem hélice? O segredo é o ar quente: menos denso que o ar frio em volta. E o resto é Arquimedes, o mesmo do navio, só que no ar.

Neste vídeo a gente olha as moléculas do ar frio e do ar quente, faz a conta do empuxo (por que o balão precisa ser enorme), abre o balão peça por peça (envelope, paraquedas, saia, queimador, botijões e cesto), enche o envelope, decola, desce e "dirige" usando as camadas de vento. No fim, Bartolomeu de Gusmão em Lisboa (1709) e os irmãos Montgolfier (1783).

Cada quadro é pixel art desenhada por código, e a música é original. Os jatos do queimador caem nas batidas da música.

Capítulos
{capitulos}

Simplificado de propósito
- As moléculas foram desenhadas enormes, poucas e lentas. De 20 °C para 99 °C elas ficam só cerca de 13% mais rápidas; no desenho a diferença foi exagerada para dar para ver.
- O balão é genérico (listras inventadas). O voo dos capítulos de subida e descida é uma simulação feita para o vídeo: 2.800 metros cúbicos, 700 kg no total, um queimador de 2 MW de calor útil, perda de calor pelo tecido, arrasto do ar e atmosfera padrão. Um balão de verdade faz algo parecido, com números diferentes.
- As contas usam ar seco a 20 °C no chão e o ar de dentro na mesma pressão do ar de fora.
- Os 3.380 kg e 2.660 kg do capítulo do empuxo são contas a partir dos números da Wikipedia para 2.800 metros cúbicos a 99 °C (723,5 kg de sobra); arredondamos para 720 kg.
- As camadas de vento do mapa (para a direita embaixo, para a esquerda em cima) são um exemplo inventado, e esse trecho está acelerado 20 vezes. O balão desenhado no mapa está fora de escala.
- A ventoinha, o balão de 1709 e o de 1783 são desenhos genéricos, sem pessoas.
- O tamanho do balão saiu da conta: um envelope com o nosso perfil e 2.800 metros cúbicos tem cerca de 19,4 m de altura e 17,5 m de largura.

Fontes
{fontes}

#balao #baloismo #comofunciona #pixelart #fisica #arquimedes #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nas cenas de voo o
# balão fica centrado em x 150 (recorte 60..240).
PREFIXO = 'ep22-balao'
CORTES = [
    dict(id='c1', de=('particulas', 0.0), ate=('particulas', 31.6), x=110, gancho=['POR QUE', 'AR QUENTE SOBE?'],
         titulo='Por que o ar quente sobe? As moléculas explicam 🔥',
         descricao='Aquecidas, as moléculas do ar se mexem mais rápido e se empurram para longe. Com a caixa aberta embaixo, como a boca de um balão, parte do ar sai: sobra menos ar no mesmo espaço, e ele fica mais leve.'),
    dict(id='c2', de=('empuxo', 7.6), ate=('empuxo', 36.0), x=110, gancho=['ARQUIMEDES', 'NO AR'],
         titulo='Arquimedes no ar: a conta que faz o balão subir 🎈',
         descricao='Um balão de 2.800 metros cúbicos tira do lugar cerca de 3.380 kg de ar frio. O ar quente de dentro pesa cerca de 2.660 kg. Sobram uns 720 kg de empuxo para levantar o balão.'),
    dict(id='c3', de=('inflar', 0.0), ate=('inflar', 30.0), x=110, gancho=['ENCHENDO', 'O BALÃO'],
         titulo='Como se enche um balão de ar quente',
         descricao='Uma ventoinha enche o envelope com o ar do lugar. Com uns 60% cheio, o queimador acende, o ar esquenta e o envelope se levanta sozinho.'),
    dict(id='c4', de=('subir', 0.0), ate=('subir', 35.4), x=60, gancho=['DECOLANDO', 'NO RITMO'],
         titulo='A decolagem do balão, com os jatos no ritmo da música 🎵',
         descricao='Cada jato do queimador solta 2 a 3 megawatts de calor. Quando o empuxo passa do peso, o balão decola. Voo calculado: 700 kg, ar a uns 97 °C na decolagem.'),
    dict(id='c5', de=('descer', 7.6), ate=('descer', 42.0), x=60, gancho=['COMO O BALÃO', 'DESCE?'],
         titulo='Como o balão desce: o paraquedas no topo',
         descricao='Para descer mais rápido, o piloto puxa a corda do paraquedas, no topo do envelope: o ar quente escapa por cima e o ar frio entra pela boca. Depois, jatos do queimador freiam a descida até o pouso.'),
    dict(id='c6', de=('vento', 7.8), ate=('vento', 47.6), x=60, gancho=['BALÃO', 'TEM VOLANTE?'],
         titulo='Como um balão "dirige" sem leme? 🌬️',
         descricao='O balão não tem leme: vai para onde o vento vai. Mas o vento muda de direção em alturas diferentes, e o piloto sobe ou desce para pegar a camada certa.'),
]
