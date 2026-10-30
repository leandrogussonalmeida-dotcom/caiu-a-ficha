#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep10: Como o helicóptero voa (série COMO VOA / FLUTUA).

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep10_motor.py` (cenas) e `ep10_desenho.py` (helicóptero de lado e de cima,
prato cíclico em 3D, ar descendo/subindo pelo rotor). O corte da pá usa o mesmo
túnel de vento calculado do ep02 (`ep02_desenho.Fluxo`).
`longo_verificar.py --roteiro ep10_roteiro` reprova legenda que não cabe,
caractere sem glifo, legenda curta e fato sem fonte.

Legenda: até 2 linhas, até ~37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Wikipedia, "Helicopter flight controls": o coletivo muda o ângulo de
      todas as pás ao mesmo tempo; o cíclico muda o ângulo de cada pá conforme
      a posição dela na volta; cíclico para a frente, o disco inclina para a
      frente; os pedais mudam o ângulo das pás do rotor de cauda e o nariz vira
      para o lado do pedal; o giro do rotor fica quase constante.
  F2  Wikipedia, "Tail rotor": o torque de reação do rotor gira o corpo no
      sentido oposto; o rotor de cauda, na ponta da cauda, contrabalança; pedais
      mudam o passo das pás da cauda; cerca de 10% da potência vai para a cauda;
      eixo saindo da transmissão principal.
  F3  NASA Glenn, "Newton's Third Law": o ar que passa pela asa é desviado para
      baixo; em reação, a asa é empurrada para cima (o mesmo do ep02).
  F4  Wikipedia, "Helicopter": pairar é a parte mais difícil de pilotar; o
      piloto corrige o tempo todo, cada comando mexe nos outros dois; o cíclico
      controla frente, trás, direita e esquerda; coaxial = dois rotores no mesmo
      eixo, um em cima do outro, girando em sentidos opostos; tandem = um na
      frente do outro; na autorrotação o rotor gira pelo ar que sobe por ele.
  F5  Wikipedia, "Helicopter rotor": as pás são aerofólios compridos e finos;
      o rotor dá a sustentação que segura o peso; joga ar para baixo
      (downwash); giro quase constante (95% a 102%); o ângulo das pás é o único
      jeito de mudar a força do rotor; o prato tem uma parte fixa e uma que gira.
  F6  Robinson R22 (helicóptero leve de 2 lugares), manual de voo, seção 1:
      rotor principal de 2 pás, 7,67 m; 100% = 510 RPM do rotor; ponta a 698
      pés/s com 104%; rotor de cauda de 42 polegadas, ponta a 622 pés/s com 104%.
  F7  Conta (F6): 510 / 60 = 8,5 voltas por segundo; 698 / 1,04 = 671 pés/s =
      204,5 m/s = 736 km/h; cauda: 622 pés/s / (pi x 3,5 pés) = 56,6 voltas/s =
      3.394 RPM com 104%, contra 530 do rotor principal = 6,4 vezes.
  F8  ANAC, ANACpédia (inglês-português): "swashplate" = "prato cíclico".
  F9  Wikipedia, "Swashplate (aeronautics)": prato fixo (ligado aos comandos
      por hastes) e prato giratório (gira com o mastro) unidos por rolamento;
      hastes de passo ligam o prato giratório aos braços das pás; o prato todo
      sobe e desce (coletivo) ou inclina (cíclico); a informação de passo vai
      adiantada em relação à posição da pá.
  F10 Part-66 Online, módulo 12.1 (apostila de mecânico aeronáutico, EASA):
      pairado = força vertical igual ao peso; o coletivo muda o tamanho da
      força, não a direção; o cíclico inclina o disco na direção do voo, e o
      piloto ajusta o coletivo porque parte da força deixa de segurar o peso; a
      resposta da pá vem 90° depois, no sentido do giro, e o prato já faz essa
      conta; o rotor de cauda faz uma força de lado contra o torque;
      autorrotação = o equivalente ao planeio de um avião.
  F11 Wikipedia, "Coaxial rotors": os torques opostos se cancelam; para virar,
      um rotor ganha ângulo e o outro perde.
  F12 Wikipedia, "Tandem-rotor aircraft": rotores em sentidos opostos, um
      cancelando o torque do outro.
  F13 FAA, Helicopter Flying Handbook (FAA-H-8083-21B), cap. 11: na
      autorrotação o motor é desligado do rotor pela roda livre e as pás giram
      só pelo ar que sobe pelo rotor; abaixar o coletivo imediatamente; usar o
      coletivo para cuidar do giro do rotor; perto do chão, cíclico para trás
      (flare) para frear; no fim, levantar o coletivo e usar a energia guardada
      no giro das pás para amortecer o pouso.
"""

TITULO = "Como o helicóptero voa | Rotor, coletivo, cíclico e autorrotação em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=5, papel='break'),             # 15 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),             # 6 s
    dict(id='asa', gen='lofi', bars=18, papel='drop'),                # 54 s
    dict(id='giro', gen='synthwave', bars=14, papel='drop'),          # 33,6 s
    dict(id='prato', gen='synthwave', bars=15, papel='drop'),         # 36 s
    dict(id='coletivo', gen='lofi', bars=16, papel='drop'),           # 48 s
    dict(id='pairar', gen='lofi', bars=8, papel='break'),             # 24 s
    dict(id='ciclico', gen='lofi', bars=20, papel='drop'),            # 60 s
    dict(id='torque', gen='synthwave', bars=18, papel='drop'),        # 43,2 s
    dict(id='pedais', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='dois', gen='lofi', bars=10, papel='break'),              # 30 s
    dict(id='autorrotacao', gen='lofi', bars=22, papel='drop'),       # 66 s
    dict(id='resumo', gen='lofi', bars=9, papel='drop'),              # 27 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.4, 5.0, "ESTE HELICÓPTERO ESTÁ PARADO NO AR,", "SEM ASA FIXA E SEM PISTA.", ()),
        (5.2, 9.8, "NUM HELICÓPTERO LEVE, O ROTOR GIRA", "A *510 VOLTAS POR MINUTO*.", ('F6',)),
        (10.0, 14.8, "COMO ISSO SEGURA ELE NO AR?", "E COMO ELE ESCOLHE PARA ONDE IR?", ()),
    ],
    'asa': [
        (0.4, 5.6, "CADA PÁ DO ROTOR É UMA *ASA*:", "COMPRIDA, FINA E COM PERFIL.", ('F5',)),
        (5.8, 11.0, "SÓ QUE ELA NÃO ANDA PARA A FRENTE.", "ELA ANDA *EM CÍRCULO*.", ()),
        (11.2, 16.6, "CORTE A PÁ: O PERFIL É PARECIDO", "COM O DA ASA DO AVIÃO.", ('F5',)),
        (16.8, 22.2, "COMO NO EPISÓDIO DO AVIÃO, ELA", "*DESVIA O AR PARA BAIXO*...", ('F3',)),
        (22.4, 27.6, "...E O AR EMPURRA A PÁ", "*PARA CIMA*.", ('F3',)),
        (27.8, 33.2, "QUANTO MAIS LONGE DO CENTRO,", "MAIS RÁPIDO A PÁ ANDA.", ('F7',)),
        (33.4, 38.8, "NA PONTA, ELA PASSA A", "*736 KM/H*.", ('F6', 'F7')),
        (39.0, 44.4, "O ROTOR INTEIRO JOGA UMA COLUNA", "DE AR *PARA BAIXO*.", ('F5',)),
        (44.6, 53.6, "E A FORÇA PARA CIMA É A QUE", "*SEGURA O PESO* DO HELICÓPTERO.", ('F5',)),
    ],
    'giro': [
        (0.4, 5.6, "ATÉ AGORA, CÂMERA LENTA.", "AGORA, A VELOCIDADE DE VERDADE:", ()),
        (5.8, 11.6, "*510 RPM*: 8,5 VOLTAS POR SEGUNDO.", "AS PÁS VIRAM UM BORRÃO.", ('F6', 'F7')),
        (11.8, 17.4, "E ESSE GIRO QUASE NÃO MUDA", "DURANTE O VOO.", ('F5',)),
        (17.6, 23.2, "ENTÃO, COMO ELE SOBE, DESCE E ANDA?", "MUDANDO O *ÂNGULO DAS PÁS*.", ('F5',)),
        (23.4, 33.2, "QUEM MUDA ESSE ÂNGULO É UMA PEÇA", "LOGO ABAIXO DO ROTOR.", ('F9',)),
    ],
    'prato': [
        (0.3, 5.8, "ESTE É O *PRATO CÍCLICO*.", "ELE FICA EM VOLTA DO MASTRO.", ('F8', 'F9')),
        (6.0, 11.8, "EMBAIXO, O *PRATO FIXO*: NÃO GIRA.", "OS COMANDOS DO PILOTO MEXEM NELE.", ('F9',)),
        (12.0, 17.8, "EM CIMA, O *PRATO GIRATÓRIO*:", "GIRA JUNTO COM O ROTOR.", ('F9',)),
        (18.0, 23.8, "ENTRE OS DOIS, UM *ROLAMENTO*", "DEIXA UM GIRAR SOBRE O OUTRO.", ('F9',)),
        (24.0, 29.8, "*HASTES DE PASSO* LIGAM O PRATO", "GIRATÓRIO A CADA PÁ.", ('F9',)),
        (30.0, 35.8, "A HASTE SOBE: A PÁ GIRA NO PRÓPRIO", "EIXO E O *ÂNGULO* AUMENTA.", ('F9',)),
    ],
    'coletivo': [
        (0.4, 5.6, "PRIMEIRO COMANDO: A ALAVANCA", "DO *COLETIVO*.", ('F1',)),
        (5.8, 11.2, "O PILOTO PUXA O COLETIVO E O PRATO", "*SOBE INTEIRO*, SEM INCLINAR.", ('F9',)),
        (11.4, 16.8, "TODAS AS PÁS GANHAM ÂNGULO", "*JUNTAS*, NA VOLTA TODA.", ('F1',)),
        (17.0, 22.4, "MAIS ÂNGULO, MAIS AR DESVIADO", "PARA BAIXO: *MAIS FORÇA*.", ('F3', 'F10')),
        (22.6, 28.0, "A FORÇA PASSA DO PESO", "E O HELICÓPTERO *SOBE*.", ('F10',)),
        (28.2, 33.6, "PARA DESCER, O PILOTO ABAIXA", "O COLETIVO: MENOS ÂNGULO.", ('F1',)),
        (33.8, 39.2, "MENOS FORÇA QUE O PESO:", "ELE *DESCE*.", ('F10',)),
        (39.4, 47.6, "O ROTOR CONTINUA GIRANDO IGUAL.", "SÓ O *ÂNGULO* MUDOU.", ('F5',)),
    ],
    'pairar': [
        (0.4, 5.6, "NO MEIO DO CAMINHO, O PONTO EXATO:", "FORÇA DO ROTOR *IGUAL AO PESO*.", ('F10',)),
        (5.8, 11.0, "O HELICÓPTERO FICA PARADO NO AR.", "ISSO É *PAIRAR*.", ('F10',)),
        (11.2, 16.6, "PARECE FÁCIL, MAS É A PARTE", "*MAIS DIFÍCIL* DE PILOTAR.", ('F4',)),
        (16.8, 23.6, "O PILOTO CORRIGE *O TEMPO TODO*:", "CADA COMANDO MEXE NOS OUTROS DOIS.", ('F4',)),
    ],
    'ciclico': [
        (0.4, 5.6, "SEGUNDO COMANDO: O MANCHE", "DO *CÍCLICO*.", ('F1',)),
        (5.8, 11.2, "O PILOTO EMPURRA O CÍCLICO PARA", "A FRENTE: O PRATO *INCLINA*.", ('F9',)),
        (11.4, 16.8, "AGORA CADA PÁ MUDA DE ÂNGULO", "*DURANTE A VOLTA*.", ('F1',)),
        (17.0, 22.4, "SIGA A PÁ AMARELA: DE UM LADO ELA", "GANHA ÂNGULO, DO OUTRO PERDE.", ('F1',)),
        (22.6, 28.0, "A PÁ SOBE E DESCE *1/4 DE VOLTA*", "DEPOIS DA MUDANÇA DE ÂNGULO.", ('F10',)),
        (28.2, 33.6, "POR ISSO O DISCO DO ROTOR", "*INCLINA PARA A FRENTE*.", ('F1', 'F10')),
        (33.8, 39.2, "A FORÇA DO ROTOR INCLINA JUNTO:", "PARTE DELA *PUXA PARA A FRENTE*.", ('F10',)),
        (39.4, 44.8, "O HELICÓPTERO ABAIXA O NARIZ", "E *ANDA PARA A FRENTE*.", ('F1',)),
        (45.0, 50.4, "CÍCLICO PARA O LADO: VAI PARA O", "LADO. PARA TRÁS: VAI PARA TRÁS.", ('F4',)),
        (50.6, 59.6, "PARTE DA FORÇA FOI PARA A FRENTE:", "O PILOTO DÁ *MAIS COLETIVO*.", ('F10',)),
    ],
    'torque': [
        (0.4, 5.6, "AGORA, UM PROBLEMA. O MOTOR GIRA", "O ROTOR PARA UM LADO...", ('F2',)),
        (5.8, 11.2, "...E O CORPO DO HELICÓPTERO TENTA", "*GIRAR PARA O OUTRO*.", ('F2',)),
        (11.4, 16.8, "SEM NADA PARA SEGURAR, ELE", "FICARIA *RODANDO SEM PARAR*.", ('F2',)),
        (17.0, 22.4, "A SOLUÇÃO MAIS COMUM: O *ROTOR*", "*DE CAUDA*, LÁ NA PONTA.", ('F2',)),
        (22.6, 28.0, "ELE EMPURRA A CAUDA DE LADO", "E *SEGURA O GIRO*.", ('F2', 'F10')),
        (28.2, 33.6, "UM *EIXO* LEVA A FORÇA DO MOTOR", "ATÉ LÁ ATRÁS.", ('F2',)),
        (33.8, 38.4, "ELE GASTA UNS *10%* DA POTÊNCIA", "DO MOTOR.", ('F2',)),
        (38.6, 43.0, "E GIRA UMAS *6 VEZES* MAIS RÁPIDO", "QUE O ROTOR DE CIMA.", ('F6', 'F7')),
    ],
    'pedais': [
        (0.4, 5.6, "TERCEIRO COMANDO: OS *PEDAIS*.", "ELES MUDAM O ÂNGULO DAS PÁS DA CAUDA.", ('F1', 'F2')),
        (5.8, 11.0, "MUDA O ÂNGULO, MUDA A FORÇA", "QUE EMPURRA A CAUDA.", ('F2', 'F10')),
        (11.2, 16.4, "PEDAL ESQUERDO: O NARIZ VIRA", "PARA A *ESQUERDA*.", ('F1',)),
        (16.6, 23.6, "PEDAL DIREITO: VIRA PARA A *DIREITA*.", "ASSIM O PILOTO APONTA O NARIZ.", ('F1',)),
    ],
    'dois': [
        (0.4, 5.6, "OUTRO JEITO: *DOIS ROTORES*", "GIRANDO EM SENTIDOS OPOSTOS.", ('F4',)),
        (5.8, 11.0, "UM EM CIMA DO OUTRO, NO MESMO", "EIXO: ROTORES *COAXIAIS*.", ('F4', 'F11')),
        (11.2, 16.4, "UM NA FRENTE E OUTRO ATRÁS:", "ROTORES EM *TANDEM*.", ('F4', 'F12')),
        (16.6, 22.0, "UM TORQUE *CANCELA* O OUTRO.", "NÃO PRECISA DE ROTOR DE CAUDA.", ('F11', 'F12')),
        (22.2, 29.6, "NO COAXIAL, PARA VIRAR, UM ROTOR", "GANHA ÂNGULO E O OUTRO PERDE.", ('F11',)),
    ],
    'autorrotacao': [
        (0.4, 5.6, "E SE O MOTOR *PARAR* NO AR?", "", ()),
        (5.8, 11.0, "UMA *RODA LIVRE* SOLTA O MOTOR.", "O ROTOR CONTINUA GIRANDO SOLTO.", ('F13',)),
        (11.2, 16.4, "NA HORA, O PILOTO *ABAIXA O*", "*COLETIVO*: MENOS ÂNGULO NAS PÁS.", ('F13',)),
        (16.6, 22.0, "O HELICÓPTERO DESCE E O AR AGORA", "ENTRA NO ROTOR *DE BAIXO PARA CIMA*.", ('F13',)),
        (22.2, 27.4, "ESSE VENTO DE BAIXO *GIRA O ROTOR*,", "COMO UM CATA-VENTO.", ('F13', 'F4')),
        (27.6, 32.8, "É A *AUTORROTAÇÃO*: O ROTOR GIRA", "SEM O MOTOR.", ('F13', 'F4')),
        (33.0, 38.2, "É COMO O *PLANEIO* DE UM AVIÃO:", "ELE DESCE, MAS SOB CONTROLE.", ('F10',)),
        (38.4, 43.6, "PERTO DO CHÃO, O PILOTO PUXA O", "CÍCLICO: O NARIZ SOBE E *FREIA*.", ('F13',)),
        (43.8, 49.0, "NO FIM, ELE *PUXA O COLETIVO*.", "A ENERGIA GUARDADA NO GIRO DAS PÁS...", ('F13',)),
        (49.2, 54.4, "...AMORTECE O POUSO.", "", ('F13',)),
        (54.6, 59.8, "O PILOTO CUIDA DO GIRO DO ROTOR", "*ATÉ O FIM*, COM O COLETIVO.", ('F13',)),
        (60.0, 65.6, "NO CHÃO, SÓ ENTÃO O ROTOR", "VAI PARANDO.", ()),
    ],
    'resumo': [
        (0.4, 6.4, "1. CADA PÁ É UMA ASA QUE GIRA E", "*EMPURRA O AR PARA BAIXO*.", ('F3', 'F5')),
        (6.6, 13.0, "2. *COLETIVO*: TODAS AS PÁS JUNTAS.", "*CÍCLICO*: O ÂNGULO MUDA NA VOLTA.", ('F1',)),
        (13.2, 19.6, "3. O *ROTOR DE CAUDA* SEGURA", "O CORPO CONTRA O TORQUE.", ('F2',)),
        (19.8, 26.6, "4. SEM MOTOR, O AR DE BAIXO GIRA", "O ROTOR: *AUTORROTAÇÃO*.", ('F13',)),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Helicopter flight controls"', 'https://en.wikipedia.org/wiki/Helicopter_flight_controls'),
    'F2': ('Wikipedia, "Tail rotor"', 'https://en.wikipedia.org/wiki/Tail_rotor'),
    'F3': ('NASA Glenn Research Center, "Newton\'s Third Law"',
           'https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/newtons-third-law-action-reaction/'),
    'F4': ('Wikipedia, "Helicopter"', 'https://en.wikipedia.org/wiki/Helicopter'),
    'F5': ('Wikipedia, "Helicopter rotor"', 'https://en.wikipedia.org/wiki/Helicopter_rotor'),
    'F6': ('Robinson Helicopter, R22 Pilot\'s Operating Handbook, seção 1 (especificações)',
           'https://shop.robinsonheli.com/wp-content/uploads/2022/01/r22_poh_1.pdf'),
    'F7': ('Conta a partir de F6: 510/60 = 8,5 voltas/s; 698/1,04 = 671 pés/s = 736 km/h; '
           'cauda 622 pés/s em 42 pol. = 3.394 RPM contra 530 (6,4 vezes)', None),
    'F8': ('ANAC, ANACpédia, "swashplate" = prato cíclico', 'https://www2.anac.gov.br/anacpedia/ing_por/tr3220.htm'),
    'F9': ('Wikipedia, "Swashplate (aeronautics)"', 'https://en.wikipedia.org/wiki/Swashplate_(aeronautics)'),
    'F10': ('Part-66 Online, módulo 12.1, "Theory of Flight — Rotary Wing Aerodynamics"',
            'https://www.part66online.com/study-notes/module/12/12.1/'),
    'F11': ('Wikipedia, "Coaxial rotors"', 'https://en.wikipedia.org/wiki/Coaxial_rotors'),
    'F12': ('Wikipedia, "Tandem-rotor aircraft"', 'https://en.wikipedia.org/wiki/Tandem-rotor_aircraft'),
    'F13': ('FAA, Helicopter Flying Handbook (FAA-H-8083-21B), cap. 11, "Helicopter Emergencies and Hazards"',
            'https://www.faa.gov/sites/faa.gov/files/regulations_policies/handbooks_manuals/aviation/helicopter_flying_handbook/hfh_ch11.pdf'),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'asa': 'A pá é uma asa que gira', 'giro': '510 voltas por minuto',
                'prato': 'O prato cíclico', 'coletivo': 'Coletivo: subir e descer', 'pairar': 'Pairar',
                'ciclico': 'Cíclico: inclinar e andar', 'torque': 'O torque e o rotor de cauda',
                'pedais': 'Os pedais', 'dois': 'Dois rotores: coaxial e tandem',
                'autorrotacao': 'Autorrotação: quando o motor para', 'resumo': 'Resumo'}

DESCRICAO = """Como um helicóptero fica parado no ar, sobe, desce e anda para qualquer lado? A gente desmonta o rotor em pixel art: cada pá é uma asa que gira e empurra o ar para baixo. Depois abre o prato cíclico, a peça que muda o ângulo das pás, e mostra os três comandos do piloto: coletivo, cíclico e pedais. No fim, o motor para no ar e o helicóptero pousa mesmo assim, com a autorrotação.

Cada quadro é pixel art desenhada por código, e a música é original. O ar em volta do corte da pá é calculado (o mesmo túnel de vento do episódio do avião).

Capítulos
{capitulos}

Simplificado de propósito
- O helicóptero é genérico, de 2 pás. Os números de giro e de velocidade da ponta são de um helicóptero leve de 2 lugares (Robinson R22); outros helicópteros giram em outros ritmos.
- Os ângulos das pás na tela (de 0° a uns 16°) e a inclinação do prato e do disco são ilustrativos e exagerados para dar para ver.
- No desenho, a haste de passo fica 1/4 de volta à frente da pá, para o prato inclinar para o mesmo lado que o disco. Cada helicóptero resolve esse adiantamento de um jeito.
- Não mostramos a articulação das pás (batimento), a diferença de força entre a pá que avança e a que recua, nem o efeito solo.
- Na cena do torque, o corpo gira sem o rotor de cauda para mostrar o problema; num helicóptero de verdade isso é uma emergência.
- Na autorrotação, o giro do rotor no painel é ilustrativo; os limites de cada helicóptero estão no manual dele. Tempo e altura estão comprimidos.

Fontes
{fontes}

#helicoptero #comofunciona #pixelart #aviacao #ciencia #fisica #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O helicóptero de
# lado fica em x ~30..190; o rotor visto de cima, em x ~40..220 (asa, giro,
# cíclico) ou centrado em 150 (torque, pedais).
PREFIXO = 'ep10-helicoptero'
CORTES = [
    dict(id='c1', de=('autorrotacao', 0.0), ate=('autorrotacao', 38.2), x=40, gancho=['SEM MOTOR,', 'E AGORA?'],
         titulo='O que acontece se o motor do helicóptero parar? 🚁',
         descricao='A roda livre solta o motor, o piloto abaixa o coletivo e o ar que sobe pelo rotor mantém as pás girando: é a autorrotação. Fonte: FAA, Helicopter Flying Handbook.'),
    dict(id='c2', de=('ciclico', 5.8), ate=('ciclico', 33.6), x=28, gancho=['COMO ELE', 'ANDA?'],
         titulo='Como o helicóptero anda para a frente',
         descricao='O cíclico inclina o prato, cada pá muda de ângulo durante a volta e o disco do rotor inclina. A força inclina junto e puxa o helicóptero.'),
    dict(id='c3', de=('torque', 0.0), ate=('torque', 28.0), x=60, gancho=['PRA QUE A', 'CAUDA?'],
         titulo='Para que serve o rotor de cauda do helicóptero?',
         descricao='O rotor gira para um lado e o corpo tenta girar para o outro. O rotor de cauda empurra a cauda de lado e segura o giro.'),
    dict(id='c4', de=('coletivo', 5.8), ate=('coletivo', 39.2), x=14, gancho=['SOBE E', 'DESCE'],
         titulo='Como o helicóptero sobe e desce sem mudar o giro',
         descricao='O coletivo levanta o prato cíclico inteiro: todas as pás ganham ângulo juntas e o rotor faz mais força. O giro do rotor quase não muda.'),
    dict(id='c5', de=('giro', 0.0), ate=('giro', 23.2), x=40, gancho=['510 VOLTAS', 'POR MINUTO'],
         titulo='A velocidade real do rotor de um helicóptero 🌀',
         descricao='Num helicóptero leve, o rotor gira a 510 RPM: 8,5 voltas por segundo. A ponta da pá passa a mais de 700 km/h.'),
    dict(id='c6', de=('pedais', 0.0), ate=('pedais', 23.6), x=60, gancho=['COMO ELE', 'VIRA?'],
         titulo='Como o piloto vira o nariz do helicóptero',
         descricao='Os pedais mudam o ângulo das pás do rotor de cauda. Mais força ou menos força na cauda, e o nariz vira para o lado do pedal.'),
]
