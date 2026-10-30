#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep21 (série POR DENTRO): Como funciona a descarga do vaso.

A ideia: um vaso com caixa acoplada cortado ao meio, rodando. O botão puxa a
corrente, a comporta (vedação de borracha) abre e a água da caixa desce pelo
aro e pelo jato; a bacia enche até o cano curvo (o sifão) ficar cheio; aí ele
vira sifão de verdade e puxa a água; quando o nível baixa, entra ar e o sifão
para (o "glug"); a boia, que desceu com a água, abriu a válvula de entrada; um
tubinho manda parte da água nova pelo ladrão para repor o selo d'água da bacia;
a boia sobe e fecha. Depois: dois botões (3 e 6 litros), quanto se gastava antes
e a válvula de parede, que usa a pressão do cano em vez de uma caixa.
Protagonistas: o nível da água e uma gota; painel com litros, nível, estado
das válvulas e "ETAPA x DE 5".

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Wikipedia, "Flush toilet": a alavanca levanta a válvula de descarga do
      assento (a saída do fundo é tampada por uma vedação, o "flapper"); o aro
      tem furos inclinados alimentados pela caixa, que enchem e lavam a bacia;
      pode haver um furo de jato (~25 mm) no fundo, no sifão; o sifão segura
      água na bacia como selo contra os gases do esgoto; a água sobe e enche o
      tubo em S; o sifão "puxa" quase toda a água; quando entra ar a coluna se
      rompe e vem o gorgolejo; a boia controla a válvula de entrada e fecha no
      nível; sem caixa, a válvula (flushometer) usa a pressão do cano, muita
      vazão por pouco tempo; antes de 1994 nos EUA: 13 L; depois, 6,1 L.
  F2  Mr. Rooter, "How Does a Toilet Tank Work?": a alavanca puxa a corrente e
      levanta a comporta; a boia desce, a válvula abre; enche e fecha no nível;
      o tubo de reabastecimento liga ao ladrão para encher a bacia; o ladrão é
      a segurança contra transbordar a caixa.
  F3  USP (Superintendência do Espaço Físico), especificação de equipamentos
      economizadores: bacia com caixa acoplada de 6 L por descarga (nominal),
      ABNT NBR 15097 e NBR 15491; duplo acionamento: parcial de até 2/3 da
      completa; válvula de descarga DN 32 ou DN 40, de 20 kPa (baixa pressão)
      até 400 kPa (alta).
  F4  Wikipedia, "Dual flush toilet": um botão solta menos água (ex.: 3 L), o
      outro mais (ex.: 6 L); o menor para líquidos, o maior para sólidos.
  F5  Wikipedia, "Siphon": tubo em U invertido que faz o líquido subir acima do
      reservatório sem bomba; precisa ser enchido antes (escorvar); a saída fica
      mais baixa que a superfície; o ar que entra quebra o sifão; a gravidade
      puxa a coluna mais alta.
  F6  ABNT NBR 8160 (texto da norma): fecho hídrico = camada líquida que, num
      desconector, veda a passagem dos gases; altura mínima de 0,05 m.
  F7  Engenharia 360, "Diferentes tipos de descargas utilizadas em bacias
      sanitárias": a bacia é cerca de 29% dos gastos residenciais (de água); a
      válvula tem boa pressão, regulada por um parafuso; exige cano de diâmetro
      maior, vindo direto do reservatório.
  F8  Fecomercio-SP, cartilha da água (tabela com fonte Sabesp, 2014): bacia
      convencional 12 L por descarga; com válvula bem regulada 10 L; de
      descarga reduzida (VDR) 6 L.
  F9  Conta (F3): 1 metro de coluna d'água = cerca de 9,8 kPa; 20 kPa = cerca
      de 2 m.
"""

TITULO = "Como funciona a descarga do vaso | Sifão, boia e caixa acoplada em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),            # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),            # 6 s
    dict(id='vaso', gen='lofi', bars=10, papel='drop'),              # 30 s
    dict(id='pecas', gen='synthwave', bars=21, papel='drop'),        # 50,4 s (7 peças x 7,2 s)
    dict(id='selo', gen='lofi', bars=10, papel='drop'),              # 30 s
    dict(id='sifao', gen='lofi', bars=10, papel='break'),            # 30 s
    dict(id='etapa1', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='etapa2', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='etapa3', gen='lofi', bars=10, papel='drop'),            # 30 s
    dict(id='etapa4', gen='lofi', bars=6, papel='break'),            # 18 s
    dict(id='etapa5', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='ciclo', gen='synthwave', bars=15, papel='drop'),        # 36 s (3 descargas, 1 etapa por compasso)
    dict(id='duplo', gen='lofi', bars=12, papel='drop'),             # 36 s
    dict(id='litros', gen='lofi', bars=10, papel='break'),           # 30 s
    dict(id='parede', gen='lofi', bars=14, papel='drop'),            # 42 s
    dict(id='resumo', gen='lofi', bars=11, papel='drop'),            # 33 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),               # 15 s
]

_P = 7.2   # duração de cada peça
LEGENDAS = {
    'gancho': [
        (0.5, 6.0, "UM APERTO NO BOTÃO E *6 LITROS*", "DE ÁGUA DESCEM PELO VASO.", ('F3',)),
        (6.2, 11.6, "QUEM PUXA ESSA ÁGUA? E QUEM ENCHE", "TUDO DE NOVO, *SOZINHO*?", ()),
    ],
    'vaso': [
        (0.5, 7.0, "ESTE É UM VASO SANITÁRIO COM", "*CAIXA ACOPLADA*: A CAIXA FICA EM CIMA.", ()),
        (7.3, 14.3, "A CAIXA GUARDA A ÁGUA DA DESCARGA:", "*6 LITROS* NOS VASOS DE HOJE.", ('F3',)),
        (14.6, 21.6, "NÃO TEM MOTOR NEM BOMBA. SÓ ÁGUA,", "GRAVIDADE E UM *CANO CURVO*.", ('F1', 'F5')),
        (21.9, 29.4, "VAMOS *CORTAR O VASO AO MEIO*", "E VER TUDO POR DENTRO.", ()),
    ],
    'pecas': [
        (0 * _P + .3, 0 * _P + 6.9, "A *CAIXA*: 6 LITROS ESPERANDO", "A PRÓXIMA DESCARGA.", ('F3',)),
        (1 * _P + .3, 1 * _P + 6.9, "O *BOTÃO* EMPURRA UMA ALAVANCA,", "QUE PUXA UMA CORRENTE.", ('F2',)),
        (2 * _P + .3, 2 * _P + 6.9, "A *COMPORTA*: UMA VEDAÇÃO DE BORRACHA", "QUE TAMPA O FURO DO FUNDO.", ('F1',)),
        (3 * _P + .3, 3 * _P + 6.9, "O *LADRÃO*: SE A CAIXA ENCHER DEMAIS,", "A SOBRA ESCAPA POR ELE.", ('F2',)),
        (4 * _P + .3, 4 * _P + 6.9, "A *BOIA* E A *VÁLVULA DE ENTRADA*:", "ELAS ENCHEM A CAIXA DE NOVO.", ('F1', 'F2')),
        (5 * _P + .3, 5 * _P + 6.9, "O *ARO* É OCO, CHEIO DE FUROS. NA", "FRENTE, UM CANAL LEVA AO *JATO*.", ('F1',)),
        (6 * _P + .3, 6 * _P + 6.9, "E O *SIFÃO*: O CANO CURVO", "QUE LEVA TUDO PARA O ESGOTO.", ('F1',)),
    ],
    'selo': [
        (0.5, 7.0, "PARADO, O VASO GUARDA ÁGUA NO FUNDO.", "ELA FICA PRESA NA CURVA DO *SIFÃO*.", ('F1',)),
        (7.3, 14.3, "DO OUTRO LADO VEM O *GÁS DO ESGOTO*.", "A ÁGUA FUNCIONA COMO UMA TAMPA.", ('F1', 'F6')),
        (14.6, 21.6, "É O *FECHO HÍDRICO*. A NORMA PEDE", "PELO MENOS *5 CM* DE ÁGUA.", ('F6',)),
        (21.9, 29.4, "JOGUE UM COPO: A SOBRA PASSA PELA", "*CRISTA* E O NÍVEL VOLTA AO MESMO.", ('F1',)),
    ],
    'sifao': [
        (0.5, 7.0, "MAS O QUE É UM *SIFÃO*? UM TUBO", "EM U DE CABEÇA PARA BAIXO.", ('F5',)),
        (7.3, 14.3, "COM AR DENTRO, NADA ACONTECE.", "É PRECISO *ENCHER O TUBO* PRIMEIRO.", ('F5',)),
        (14.6, 21.6, "CHEIO, A ÁGUA *SOBE A CURVA* SOZINHA:", "O LADO QUE DESCE PUXA O RESTO.", ('F5',)),
        (21.9, 29.4, "A SAÍDA TEM QUE FICAR MAIS BAIXA.", "E SE ENTRA *AR*, O SIFÃO PARA.", ('F5',)),
    ],
    'etapa1': [
        (0.5, 7.0, "ETAPA 1: *APERTAR*. O BOTÃO DESCE", "E A ALAVANCA SOBE DO OUTRO LADO.", ('F2',)),
        (7.3, 14.3, "A CORRENTE LEVANTA A *COMPORTA*.", "O FURO DO FUNDO FICA ABERTO.", ('F1', 'F2')),
        (14.6, 23.4, "A ÁGUA DA CAIXA DESCE PELO FURO", "E CORRE PELO *CANAL DO ARO*.", ('F1',)),
    ],
    'etapa2': [
        (0.5, 7.0, "ETAPA 2: *A ÁGUA DESCE*. ELA SAI", "PELOS FUROS DO ARO E LAVA A BACIA.", ('F1',)),
        (7.3, 14.3, "PELO CANAL DA FRENTE ELA CHEGA AO", "*JATO*, NO FUNDO, VIRADO PRO SIFÃO.", ('F1',)),
        (14.6, 23.4, "O NÍVEL SOBE E A ÁGUA COMEÇA", "A PASSAR POR CIMA DA *CRISTA*.", ('F1',)),
    ],
    'etapa3': [
        (0.5, 7.5, "ETAPA 3: *O SIFÃO PUXA*. CHEGA TANTA", "ÁGUA QUE O CANO CURVO *ENCHE TODO*.", ('F1',)),
        (7.8, 15.0, "CHEIO, ELE VIRA UM SIFÃO: A ÁGUA QUE", "DESCE *PUXA* A ÁGUA DA BACIA.", ('F1', 'F5')),
        (15.3, 22.5, "A BACIA ESVAZIA DEPRESSA, LEVANDO", "TUDO PARA O ESGOTO.", ('F1',)),
        (22.8, 29.6, "A CAIXA SECOU: A COMPORTA", "CAI DE VOLTA E *TAMPA O FURO*.", ('F1',)),
    ],
    'etapa4': [
        (0.5, 8.5, "ETAPA 4: *GLUG!* A BACIA BAIXOU TANTO", "QUE O *AR* ENTRA NO SIFÃO.", ('F1',)),
        (8.8, 17.4, "O AR QUEBRA A COLUNA DE ÁGUA E O", "SIFÃO PARA. É O *GORGOLEJO* DO FIM.", ('F1', 'F5')),
    ],
    'etapa5': [
        (0.5, 7.5, "ETAPA 5: *REENCHER*. A BOIA DESCEU", "JUNTO COM A ÁGUA DA CAIXA...", ('F2',)),
        (7.8, 14.8, "...E A BOIA EMBAIXO ABRE A", "*VÁLVULA DE ENTRADA*: ÁGUA NOVA.", ('F1', 'F2')),
        (15.1, 22.1, "UM TUBINHO MANDA PARTE DELA PELO", "LADRÃO: ELA *REPÕE A ÁGUA DA BACIA*.", ('F2',)),
        (22.4, 29.4, "A ÁGUA SOBE, A BOIA SOBE JUNTO...", "E *FECHA A VÁLVULA* NO NÍVEL CERTO.", ('F1', 'F2')),
        (29.7, 35.6, "O SELO D'ÁGUA VOLTOU. O VASO", "ESTÁ PRONTO PARA A PRÓXIMA.", ('F1',)),
    ],
    'ciclo': [
        (0.5, 7.5, "AGORA SEM CÂMERA LENTA, NO RITMO DA", "MÚSICA: *1 ETAPA POR COMPASSO*.", ()),
        (7.8, 14.8, "APERTAR, DESCER, SIFÃO,", "GLUG E REENCHER.", ()),
        (15.1, 22.1, "*6 LITROS* POR DESCARGA,", "SEMPRE ATÉ O MESMO NÍVEL.", ('F3', 'F1')),
        (22.4, 29.4, "(DE VERDADE, ENCHER A CAIXA DEMORA", "BEM MAIS QUE UM COMPASSO.)", ()),
        (29.7, 35.6, "E A ÁGUA NUNCA PASSA DO *LADRÃO*:", "A BOIA FECHA ANTES.", ('F2',)),
    ],
    'duplo': [
        (0.5, 7.5, "MUITAS CAIXAS TÊM *DOIS BOTÕES*.", "", ('F4',)),
        (7.8, 14.8, "O MENOR, PARA LÍQUIDOS, SOLTA", "MENOS ÁGUA: CERCA DE *3 LITROS*.", ('F4',)),
        (15.1, 22.1, "AQUI A COMPORTA FECHA NA METADE", "DA CAIXA: É A *MEIA DESCARGA*.", ()),
        (22.4, 29.4, "O MAIOR, PARA SÓLIDOS, SOLTA", "A CAIXA TODA: *6 LITROS*.", ('F4', 'F3')),
        (29.7, 35.6, "UMA ESPECIFICAÇÃO DA USP ACEITA MEIA", "DESCARGA DE ATÉ *2/3* DA COMPLETA.", ('F3',)),
    ],
    'litros': [
        (0.5, 7.5, "QUANTA ÁGUA VAI EM UMA DESCARGA?", "CADA GARRAFA AQUI É *1 LITRO*.", ()),
        (7.8, 14.8, "UM VASO ANTIGO GASTAVA CERCA", "DE *12 LITROS* (DADO DA SABESP).", ('F8',)),
        (15.1, 22.1, "OS DE HOJE: *6 LITROS*, A METADE.", "MEIA DESCARGA: CERCA DE *3 LITROS*.", ('F3', 'F4')),
        (22.4, 29.6, "O VASO É UM DOS QUE MAIS GASTAM:", "CERCA DE *29%* DA ÁGUA DA CASA.", ('F7',)),
    ],
    'parede': [
        (0.5, 7.5, "MUITO VASO NO BRASIL NÃO TEM CAIXA:", "TEM *VÁLVULA DE PAREDE*.", ('F7',)),
        (7.8, 14.8, "O CANO VEM DIRETO DA *CAIXA D'ÁGUA*", "E É MAIS GROSSO (DN 32 OU DN 40).", ('F7', 'F3')),
        (15.1, 22.1, "APERTOU: A *PRESSÃO* DO CANO SOLTA", "MUITA ÁGUA, POR POUCO TEMPO.", ('F1',)),
        (22.4, 29.4, "ELA PEDE PELO MENOS *20 KPA*: CAIXA", "D'ÁGUA UNS *2 METROS* ACIMA.", ('F3', 'F9')),
        (29.7, 36.0, "UM *PARAFUSO* REGULA A VAZÃO. BEM", "REGULADA, GASTAVA CERCA DE *10 L*.", ('F7', 'F8')),
        (36.3, 41.6, "AS DE DESCARGA REDUZIDA:", "CERCA DE *6 LITROS*.", ('F8',)),
    ],
    'resumo': [
        (0.5, 6.6, "1. *APERTAR*: A CORRENTE", "LEVANTA A COMPORTA.", ('F1', 'F2')),
        (6.9, 12.9, "2. *A ÁGUA DESCE* PELO ARO", "E PELO JATO.", ('F1',)),
        (13.2, 19.3, "3. *O SIFÃO ENCHE* E PUXA", "A ÁGUA DA BACIA.", ('F1',)),
        (19.6, 25.6, "4. *GLUG*: O AR ENTRA", "E O SIFÃO PARA.", ('F1',)),
        (25.9, 32.6, "5. *REENCHER*: A BOIA SOBE E", "FECHA A VÁLVULA NO NÍVEL CERTO.", ('F2',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Flush toilet"', 'https://en.wikipedia.org/wiki/Flush_toilet'),
    'F2': ('Mr. Rooter, "How Does a Toilet Tank Work?"', 'https://www.mrrooter.com/about/blog/how-does-a-toilet-tank-work'),
    'F3': ('USP, Superintendência do Espaço Físico, "Equipamentos economizadores: especificações" (NBR 15097, NBR 15491)',
           'https://www.sef.usp.br/wp-content/uploads/sites/52/2016/07/EquipEconomizadores_Especificações_jun16.pdf'),
    'F4': ('Wikipedia, "Dual flush toilet"', 'https://en.wikipedia.org/wiki/Dual_flush_toilet'),
    'F5': ('Wikipedia, "Siphon"', 'https://en.wikipedia.org/wiki/Siphon'),
    'F6': ('ABNT NBR 8160, "Sistemas prediais de esgoto sanitário" (fecho hídrico, mínimo 0,05 m)',
           'https://www.masterhousesolucoes.com.br/download/NBR_8160.pdf'),
    'F7': ('Engenharia 360, "Diferentes tipos de descargas utilizadas em bacias sanitárias"',
           'https://engenharia360.com/diferentes-tipos-de-descargas-utilizadas-em-bacias-sanitarias/'),
    'F8': ('Fecomercio-SP, cartilha "Água: preservar" (tabela com fonte Sabesp, 2014)',
           'https://www.fecomercio.com.br/upload/pdf/2015/13/cartilha-agua-preservar.pdf'),
    'F9': ('Conta a partir de F3 (1 m de coluna d\'água = cerca de 9,8 kPa; 20 kPa = cerca de 2 m)', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'vaso': 'O vaso com caixa acoplada', 'pecas': 'As peças por dentro',
                'selo': 'Por que sempre tem água no fundo', 'sifao': 'O que é um sifão',
                'etapa1': 'Etapa 1: apertar', 'etapa2': 'Etapa 2: a água desce', 'etapa3': 'Etapa 3: o sifão puxa',
                'etapa4': 'Etapa 4: o glug', 'etapa5': 'Etapa 5: reencher', 'ciclo': 'A descarga no ritmo da música',
                'duplo': 'Dois botões: 3 ou 6 litros', 'litros': 'Quanta água vai embora',
                'parede': 'A válvula de parede', 'resumo': 'Resumo'}

DESCRICAO = """O que acontece quando você aperta o botão da descarga? A gente corta um vaso com caixa acoplada ao meio e acompanha uma gota: a comporta abre, a água desce pelo aro e pelo jato, o cano curvo enche e vira um sifão que puxa a água da bacia, o ar entra (o famoso "glug") e a boia abre a válvula que enche tudo de novo, até o nível certo.

Depois: por que sempre fica água no fundo (o fecho hídrico contra o gás do esgoto), o que é um sifão, os dois botões de 3 e 6 litros, quanto um vaso antigo gastava e como funciona a válvula de parede, que não tem caixa.

Cada quadro é pixel art desenhada por código, e a música é original.

Capítulos
{capitulos}

Simplificado de propósito
- O vaso é genérico e desenhado de lado. Cada fabricante arruma o mecanismo de um jeito; aqui a boia é um copo que corre na coluna da válvula de entrada.
- As 5 etapas aparecem em câmera lenta e, no capítulo da música, uma por compasso. De verdade, encher a caixa leva bem mais tempo que esvaziar.
- Nos dois botões, desenhamos a comporta fechando na metade da caixa. Muitos mecanismos de duplo acionamento usam outra peça (um "copo" que sobe), mas a ideia é a mesma: soltar só parte da água.
- O nível da água parada na bacia é a crista do sifão (a beira de baixo do cano no ponto mais alto). Os 5 cm do fecho hídrico são o mínimo da norma de esgoto para desconectores.
- Na válvula de parede, o fim da própria descarga repõe a água da bacia. A pressão de 20 kPa virar "uns 2 metros de caixa d'água" é conta nossa.
- Os 12 litros do vaso antigo e os 10 litros da válvula regulada são da tabela da Sabesp (2014) citada pela cartilha da Fecomercio-SP; nos EUA, antes de 1994, eram cerca de 13 litros.

Fontes
{fontes}

#descarga #vasosanitario #comofunciona #pixelart #sifao #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O vaso inteiro fica
# em x 46..226; na válvula de parede a parede vai até 236.
PREFIXO = 'ep21-descarga'
CORTES = [
    dict(id='c1', de=('etapa3', 0.0), ate=('etapa3', 30.0), x=46, gancho=['O SIFÃO', 'PUXA!'],
         titulo='Por que a descarga puxa a água do vaso? 🚽',
         descricao='Chega tanta água que o cano curvo atrás do vaso enche todo. Cheio, ele vira um sifão: a água que desce puxa a água da bacia.'),
    dict(id='c2', de=('etapa4', 0.0), ate=('etapa4', 18.0), x=46, gancho=['O GLUG', 'DA DESCARGA'],
         titulo='De onde vem o "glug" no fim da descarga?',
         descricao='Quando a bacia esvazia, o ar entra no sifão e quebra a coluna de água. O sifão para, e o barulho é esse gorgolejo.'),
    dict(id='c3', de=('etapa5', 0.0), ate=('etapa5', 36.0), x=46, gancho=['QUEM ENCHE', 'A CAIXA?'],
         titulo='Como a caixa da descarga enche sozinha? 💧',
         descricao='A boia desce com a água e abre a válvula de entrada. Um tubinho manda parte da água para repor a bacia, e quando a boia sobe, a válvula fecha.'),
    dict(id='c4', de=('selo', 0.0), ate=('selo', 30.0), x=46, gancho=['POR QUE TEM', 'ÁGUA ALI?'],
         titulo='Por que sempre fica água no fundo do vaso?',
         descricao='É o fecho hídrico: a água presa na curva do sifão funciona como tampa contra o gás do esgoto. A norma pede pelo menos 5 cm.'),
    dict(id='c5', de=('duplo', 0.0), ate=('duplo', 36.0), x=46, gancho=['3 OU 6', 'LITROS?'],
         titulo='Para que servem os dois botões da descarga?',
         descricao='O menor solta menos água, cerca de 3 litros, para líquidos. O maior solta a caixa toda, 6 litros, para sólidos.'),
    dict(id='c6', de=('parede', 0.0), ate=('parede', 30.0), x=52, gancho=['VÁLVULA DE', 'PAREDE'],
         titulo='Como funciona a válvula de descarga de parede?',
         descricao='Sem caixa: o cano vem direto da caixa d\'água e a pressão solta muita água por pouco tempo. Ela pede pelo menos 20 kPa, uns 2 metros de altura.'),
]
