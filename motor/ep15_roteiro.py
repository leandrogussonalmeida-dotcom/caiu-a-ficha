#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep15 (série A JORNADA): A jornada de uma garfada pelo corpo.

A ideia: seguir UMA garfada de arroz com feijão (a protagonista) pelo tubo
digestivo, e depois os nutrientes que saem dela: boca (dentes, saliva com
amilase), garganta (epiglote), esôfago (peristalse no ritmo da música),
estômago (ácido, muco, pepsina, quimo), intestino delgado (fígado, vesícula,
pâncreas, vilosidades, sangue), intestino grosso (água, bactérias) e a saída.
Objetivo que sobe na tela: "etapa 4 de 7", o tempo típico de cada etapa
(sempre "em geral", em faixas) e o tamanho de cada trecho. O desenho mora
em `ep15_motor.py` (cenas) e `ep15_desenho.py` (paleta, corpo em corte,
tubos com volume, garfada, bactérias, painel).

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Boca, faringe e esôfago: adulto tem 32 dentes (8 incisivos, 4 caninos,
      8 pré-molares, 12 molares); a amilase salivar quebra o amido; a língua
      junta a comida num bolo; na deglutição a epiglote dobra e cobre a
      glote; esôfago de ~25,4 cm; ondas de peristalse empurram o bolo; o
      esfíncter inferior relaxa para a comida passar; o processo todo de
      engolir leva 4 a 8 s para comida sólida (~1 s para líquido).
      OpenStax, Anatomy and Physiology, 23.3.
  F2  Estômago: HCl dá pH 1,5 a 3,5; pepsina começa a digestão das proteínas;
      muco com bicarbonato protege a parede; ondas de mistura a cada ~20 s;
      vira quimo; esvazia em 2 a 4 h (comida gordurosa: 6 h ou mais); o
      piloro solta ~3 mL por vez; vazio = um punho, estica até 4 L.
      OpenStax 23.4.
  F3  Intestinos: duodeno de 25,4 cm; o quimo sai do delgado em 3 a 5 h;
      segmentação mistura; 20 a 40 vilosidades por mm²; cada vilosidade tem
      capilares; o delgado absorve ~90% da água ingerida; o resíduo fica no
      grosso 12 a 24 h; trilhões de bactérias, mais de 700 espécies; elas
      fermentam os carboidratos que sobraram (feijão: mais gás); fazem
      vitaminas como a K; as fezes têm comida não digerida, bactérias,
      células da parede, sais e água. OpenStax 23.5.
  F4  Fígado ~1 L de bile por dia; a vesícula guarda, concentra e solta a
      bile; sais biliares emulsificam a gordura; pâncreas > 1 L de suco por
      dia; o bicarbonato tampona o ácido; amilase, lipase e tripsina; bile e
      suco entram juntos no duodeno. OpenStax 23.6.
  F5  Amido -> monossacarídeos (glicose); proteína -> aminoácidos; entram
      nos capilares das vilosidades e vão ao fígado pela veia porta; a
      gordura entra nos vasos linfáticos (lácteos). OpenStax 23.7.
  F6  Delgado: 3 a 5 m numa pessoa viva; área da mucosa ~30 m².
      Wikipedia, "Small intestine".
  F7  Intestino grosso: ~1,8 m; tira água e sais e deixa o resíduo sólido.
      Cleveland Clinic, "Colon (Large Intestine)".
  F8  ~6 h para estômago + delgado; no cólon, até 36 a 48 h; varia de pessoa
      para pessoa. Mayo Clinic, "Digestion: How long does it take?".
  F9  A digestão começa na boca e termina no fim do íleo (delgado).
      Cleveland Clinic, "How Long Does It Take To Digest Food?".
  F10 Feijão: proteína, ferro, fibras; arroz com feijão dá todos os
      aminoácidos essenciais. Embrapa Arroz e Feijão, "O feijão na
      alimentação" (2004).
  F11 Amido: o carboidrato mais comum da dieta humana; muito presente no
      arroz. Wikipedia, "Starch".
  F12 Veia porta: leva o sangue do tubo digestivo ao fígado, que processa o
      que foi ingerido antes da circulação geral. Wikipedia, "Hepatic portal vein".
  F13 Esôfago de ~25 cm; a epiglote inclina para trás e impede a comida de
      ir para a laringe. Wikipedia, "Esophagus".
  F14 Conta (F2, F3, F8): menor soma 2 + 3 + 12 = 17 h; com o cólon
      levando até 48 h, passa de 2 dias.
"""

TITULO = "A jornada de uma garfada pelo corpo | Como funciona a digestão em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),                 # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),                 # 6 s
    dict(id='prato', gen='lofi', bars=8, papel='drop'),                   # 24 s
    dict(id='mapa', gen='lofi', bars=8, papel='drop'),                    # 24 s
    dict(id='boca', gen='lofi', bars=12, papel='drop'),                   # 36 s
    dict(id='engolir', gen='lofi', bars=8, papel='break'),                # 24 s
    dict(id='esofago', gen='house', bars=15, papel='drop', bpm=120),      # 30 s
    dict(id='estomago', gen='synthwave', bars=15, papel='drop'),          # 36 s
    dict(id='delgado', gen='lofi', bars=12, papel='drop'),                # 36 s
    dict(id='ajudantes', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='vilosidades', gen='synthwave', bars=15, papel='drop'),       # 36 s
    dict(id='sangue', gen='lofi', bars=8, papel='drop'),                  # 24 s
    dict(id='grosso', gen='lofi', bars=10, papel='drop'),                 # 30 s
    dict(id='bacterias', gen='chiptune', bars=15, papel='drop', bpm=120),  # 30 s
    dict(id='saida', gen='lofi', bars=6, papel='break'),                  # 18 s
    dict(id='relogio', gen='lofi', bars=12, papel='drop'),                # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),                 # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                    # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.5, 5.8, "ARROZ COM FEIJÃO. UMA *GARFADA*.", "PARA ONDE ELA VAI DEPOIS?", ()),
        (6.0, 11.6, "ELA VAI PERCORRER *VÁRIOS METROS*", "DENTRO DE VOCÊ.", ('F6', 'F7')),
    ],
    'prato': [
        (0.5, 6.4, "ESTA É A NOSSA PROTAGONISTA:", "*UMA GARFADA* DE ARROZ COM FEIJÃO.", ()),
        (6.6, 12.4, "O *ARROZ* É CHEIO DE *AMIDO*, O", "CARBOIDRATO MAIS COMUM DA COMIDA.", ('F11',)),
        (12.6, 18.2, "O *FEIJÃO* TRAZ *PROTEÍNA*, FERRO", "E MUITA *FIBRA*.", ('F10',)),
        (18.4, 23.6, "JUNTOS, DÃO TODOS OS AMINOÁCIDOS", "*ESSENCIAIS*. BOA DUPLA.", ('F10',)),
    ],
    'mapa': [
        (0.5, 6.4, "O CAMINHO É UM *TUBO* COMPRIDO:", "DA BOCA ATÉ O FIM DO INTESTINO.", ()),
        (6.6, 12.4, "BOCA, GARGANTA, ESÔFAGO, ESTÔMAGO,", "INTESTINO DELGADO E GROSSO.", ()),
        (12.6, 18.2, "NO CAMINHO, *AJUDANTES* MANDAM SUCOS:", "FÍGADO, VESÍCULA E PÂNCREAS.", ('F4',)),
        (18.4, 23.6, "SÃO *7 ETAPAS*. VAMOS SEGUIR", "A GARFADA.", ()),
    ],
    'boca': [
        (0.5, 6.6, "ETAPA 1: A *BOCA*. OS DENTES", "CORTAM E TRITURAM.", ('F1',)),
        (6.8, 12.6, "UM ADULTO TEM *32 DENTES*:", "INCISIVOS NA FRENTE, MOLARES ATRÁS.", ('F1',)),
        (12.8, 18.8, "A *SALIVA* MOLHA TUDO. E TRAZ", "UMA ENZIMA: A *AMILASE*.", ('F1',)),
        (19.0, 25.2, "A AMILASE JÁ COMEÇA A QUEBRAR", "O *AMIDO* DO ARROZ.", ('F1',)),
        (25.4, 31.2, "A *LÍNGUA* JUNTA TUDO NUMA BOLINHA:", "O *BOLO ALIMENTAR*.", ('F1',)),
        (31.4, 35.8, "PRONTO PARA ENGOLIR.", "", ()),
    ],
    'engolir': [
        (0.5, 6.2, "ETAPA 2: *ENGOLIR*. A LÍNGUA", "EMPURRA O BOLO PARA TRÁS.", ('F1',)),
        (6.4, 12.2, "NA GARGANTA HÁ DOIS CANOS: UM DO", "*AR* E UM DA *COMIDA*.", ('F1',)),
        (12.4, 18.2, "A *EPIGLOTE*, UMA TAMPINHA, DOBRA", "E FECHA O CAMINHO DO AR.", ('F1', 'F13')),
        (18.4, 23.6, "O BOLO DESCE PELO ESÔFAGO.", "(AQUI, EM CÂMERA LENTA.)", ('F1',)),
    ],
    'esofago': [
        (0.5, 5.8, "ETAPA 3: O *ESÔFAGO*, UM TUBO", "DE UNS *25 CM*.", ('F1', 'F13')),
        (6.0, 11.4, "ANÉIS DE MÚSCULO APERTAM EM ONDAS", "E *EMPURRAM*: É A *PERISTALSE*.", ('F1',)),
        (11.6, 17.2, "AQUI, CADA APERTO CAI NUMA", "*BATIDA* DA MÚSICA.", ()),
        (17.4, 23.0, "COMIDA SÓLIDA, DA BOCA AO ESTÔMAGO:", "EM GERAL, *4 A 8 SEGUNDOS*.", ('F1',)),
        (23.2, 29.6, "NO FIM, UM ANEL DE MÚSCULO *ABRE*", "E A COMIDA ENTRA NO ESTÔMAGO.", ('F1',)),
    ],
    'estomago': [
        (0.5, 5.6, "ETAPA 4: O *ESTÔMAGO*, UM SACO", "DE MÚSCULO QUE ESTICA.", ('F2',)),
        (5.8, 10.8, "VAZIO, TEM O TAMANHO DE UM PUNHO.", "CHEIO, CABE ATÉ *4 LITROS*.", ('F2',)),
        (11.0, 16.0, "LÁ DENTRO TEM *ÁCIDO*:", "PH DE *1,5 A 3,5*. MUITO ÁCIDO.", ('F2',)),
        (16.2, 21.2, "UMA CAMADA DE *MUCO* PROTEGE A", "PAREDE DO PRÓPRIO ÁCIDO.", ('F2',)),
        (21.4, 26.4, "A *PEPSINA* COMEÇA A QUEBRAR AS", "PROTEÍNAS DO FEIJÃO.", ('F2',)),
        (26.6, 31.2, "ONDAS DE MÚSCULO MEXEM TUDO E A", "GARFADA VIRA UMA PASTA: O *QUIMO*.", ('F2',)),
        (31.4, 35.8, "EM GERAL, EM *2 A 4 HORAS* O PILORO", "SOLTA TUDO, AOS POUCOS.", ('F2',)),
    ],
    'delgado': [
        (0.5, 6.4, "ETAPA 5: O *INTESTINO DELGADO*.", "FINO, MAS MUITO COMPRIDO.", ('F6',)),
        (6.6, 12.6, "NUMA PESSOA VIVA, TEM UNS", "*3 A 5 METROS*, TODO DOBRADO.", ('F6',)),
        (12.8, 18.6, "O COMEÇO DELE, O *DUODENO*,", "TEM UNS 25 CM.", ('F3',)),
        (18.8, 24.8, "ANÉIS DE MÚSCULO APERTAM AQUI E", "ALI: *MISTURAM* O QUIMO.", ('F3',)),
        (25.0, 30.4, "AQUI A GARFADA FICA, EM GERAL,", "*3 A 5 HORAS*.", ('F3',)),
        (30.6, 35.8, "E É AQUI QUE A DIGESTÃO *TERMINA*.", "", ('F9',)),
    ],
    'ajudantes': [
        (0.5, 6.2, "NO DUODENO CHEGAM SUCOS DE TRÊS", "*AJUDANTES*.", ('F4',)),
        (6.4, 12.0, "O *FÍGADO* FAZ A *BILE*:", "UNS 1 LITRO POR DIA.", ('F4',)),
        (12.2, 17.8, "A *VESÍCULA* GUARDA E CONCENTRA", "A BILE ATÉ A HORA DE SOLTAR.", ('F4',)),
        (18.0, 23.6, "A BILE QUEBRA A GORDURA DO TEMPERO", "EM *GOTINHAS*. FICA MAIS FÁCIL.", ('F4',)),
        (23.8, 29.6, "O *PÂNCREAS* MANDA MAIS DE 1 LITRO", "DE SUCO POR DIA.", ('F4',)),
        (29.8, 35.8, "ELE *ACALMA O ÁCIDO* E TRAZ ENZIMAS", "PARA AMIDO, GORDURA E PROTEÍNA.", ('F4',)),
    ],
    'vilosidades': [
        (0.5, 6.2, "A PAREDE DO DELGADO É CHEIA DE", "DOBRAS E *VILOSIDADES*.", ('F3',)),
        (6.4, 12.0, "SÃO DEDINHOS: *20 A 40* EM CADA", "MILÍMETRO QUADRADO.", ('F3',)),
        (12.2, 17.8, "O AMIDO JÁ VIROU *GLICOSE*. A", "PROTEÍNA VIROU *AMINOÁCIDOS*.", ('F5',)),
        (18.0, 23.6, "ELES ATRAVESSAM A PAREDE E", "*CAEM NO SANGUE* DOS VASINHOS.", ('F5',)),
        (23.8, 29.6, "ABERTA, ESSA PAREDE COBRIRIA UNS", "*30 METROS QUADRADOS*.", ('F6',)),
        (29.8, 35.8, "O DELGADO TAMBÉM ABSORVE UNS", "*90% DA ÁGUA* QUE VOCÊ INGERE.", ('F3',)),
    ],
    'sangue': [
        (0.5, 6.2, "AGORA A GARFADA É *NUTRIENTE*", "VIAJANDO NO SANGUE.", ('F5',)),
        (6.4, 12.0, "A *VEIA PORTA* LEVA ESSE SANGUE", "PRIMEIRO PARA O *FÍGADO*.", ('F5', 'F12')),
        (12.2, 17.8, "O FÍGADO PROCESSA TUDO ANTES DE", "SEGUIR PARA O *CORPO TODO*.", ('F12',)),
        (18.0, 23.6, "A GORDURA VAI POR OUTRO CANO:", "OS VASOS DA *LINFA*.", ('F5',)),
    ],
    'grosso': [
        (0.5, 6.2, "ETAPA 6: O *INTESTINO GROSSO*.", "MAIS LARGO E MAIS CURTO.", ('F7', 'F6')),
        (6.4, 12.0, "TEM UNS *1,8 METRO*. AQUI CHEGA", "O QUE NÃO FOI ABSORVIDO.", ('F7', 'F3')),
        (12.2, 17.8, "ELE TIRA *ÁGUA E SAIS* E DEIXA", "O RESTO MAIS FIRME.", ('F7',)),
        (18.0, 23.8, "É A PARTE MAIS LENTA: EM GERAL,", "DE *12 HORAS A 2 DIAS*.", ('F3', 'F8')),
        (24.0, 29.6, "E ISSO *VARIA MUITO* DE UMA", "PESSOA PARA OUTRA.", ('F8',)),
    ],
    'bacterias': [
        (0.5, 6.2, "AQUI MORAM *TRILHÕES* DE BACTÉRIAS.", "MAIS DE *700 ESPÉCIES*.", ('F3',)),
        (6.4, 12.0, "ELAS COMEM O QUE SOBROU,", "COMO A *FIBRA* DO FEIJÃO.", ('F3', 'F10')),
        (12.2, 17.8, "ESSA FERMENTAÇÃO SOLTA *GASES*.", "É A FAMA DO FEIJÃO.", ('F3',)),
        (18.0, 23.8, "EM TROCA, ELAS FAZEM VITAMINAS,", "COMO A *VITAMINA K*.", ('F3',)),
        (24.0, 29.6, "UM ZOOLÓGICO INTEIRO", "TRABALHANDO PARA VOCÊ.", ()),
    ],
    'saida': [
        (0.5, 6.0, "ETAPA 7: O QUE O CORPO NÃO USOU", "*SAI DO CORPO*.", ('F3',)),
        (6.2, 11.8, "FIBRA, ÁGUA, SAIS, BACTÉRIAS E", "CÉLULAS VELHAS DA PAREDE.", ('F3',)),
        (12.0, 17.6, "E A JORNADA DA GARFADA", "*TERMINA AQUI*.", ()),
    ],
    'relogio': [
        (0.5, 6.6, "O RELÓGIO DA GARFADA, EM GERAL:", "DA BOCA AO ESTÔMAGO, *SEGUNDOS*.", ('F1',)),
        (6.8, 12.6, "NO ESTÔMAGO, *2 A 4 HORAS*.", "NO DELGADO, MAIS *3 A 5 HORAS*.", ('F2', 'F3')),
        (12.8, 18.6, "NO GROSSO, DE *12 HORAS* A", "*2 DIAS*. A PARTE MAIS LONGA.", ('F3', 'F8')),
        (18.8, 24.6, "COMIDA GORDUROSA PODE FICAR NO", "ESTÔMAGO *6 HORAS OU MAIS*.", ('F2',)),
        (24.8, 30.6, "SOMANDO: DE UNS *17 HORAS* A", "MAIS DE *2 DIAS*.", ('F14',)),
        (30.8, 35.8, "CADA CORPO TEM O SEU RITMO.", "", ('F8',)),
    ],
    'resumo': [
        (0.5, 7.4, "1 BOCA, 2 GARGANTA, 3 ESÔFAGO:", "A GARFADA VIRA *BOLO* E DESCE.", ('F1',)),
        (7.6, 14.6, "4 NO ESTÔMAGO ELA VIRA *QUIMO*.", "5 NO DELGADO, *NUTRIENTES*.", ('F2', 'F5')),
        (14.8, 21.8, "OS NUTRIENTES CAEM NO SANGUE E", "SEGUEM PARA O *CORPO TODO*.", ('F12',)),
        (22.0, 29.6, "6 O GROSSO TIRA A ÁGUA.", "7 E O RESTO *SAI DO CORPO*.", ('F7',)),
    ],
}

FONTES = {
    'F1': ('OpenStax, Anatomy and Physiology, 23.3 "The Mouth, Pharynx, and Esophagus"',
           'https://openstax.org/books/anatomy-and-physiology/pages/23-3-the-mouth-pharynx-and-esophagus'),
    'F2': ('OpenStax, Anatomy and Physiology, 23.4 "The Stomach"',
           'https://openstax.org/books/anatomy-and-physiology/pages/23-4-the-stomach'),
    'F3': ('OpenStax, Anatomy and Physiology, 23.5 "The Small and Large Intestines"',
           'https://openstax.org/books/anatomy-and-physiology/pages/23-5-the-small-and-large-intestines'),
    'F4': ('OpenStax, Anatomy and Physiology, 23.6 "Accessory Organs in Digestion: The Liver, Pancreas, and Gallbladder"',
           'https://openstax.org/books/anatomy-and-physiology/pages/23-6-accessory-organs-in-digestion-the-liver-pancreas-and-gallbladder'),
    'F5': ('OpenStax, Anatomy and Physiology, 23.7 "Chemical Digestion and Absorption: A Closer Look"',
           'https://openstax.org/books/anatomy-and-physiology/pages/23-7-chemical-digestion-and-absorption-a-closer-look'),
    'F6': ('Wikipedia, "Small intestine"', 'https://en.wikipedia.org/wiki/Small_intestine'),
    'F7': ('Cleveland Clinic, "Colon (Large Intestine)"', 'https://my.clevelandclinic.org/health/body/22134-colon-large-intestine'),
    'F8': ('Mayo Clinic, "Digestion: How long does it take?"',
           'https://www.mayoclinic.org/digestive-system/expert-answers/faq-20058340'),
    'F9': ('Cleveland Clinic, "How Long Does It Take To Digest Food?"',
           'https://health.clevelandclinic.org/how-long-does-it-take-to-digest-food'),
    'F10': ('Embrapa Arroz e Feijão, "O feijão na alimentação" (2004)',
            'https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/217250/1/feijao.pdf'),
    'F11': ('Wikipedia, "Starch"', 'https://en.wikipedia.org/wiki/Starch'),
    'F12': ('Wikipedia, "Hepatic portal vein"', 'https://en.wikipedia.org/wiki/Hepatic_portal_vein'),
    'F13': ('Wikipedia, "Esophagus"', 'https://en.wikipedia.org/wiki/Esophagus'),
    'F14': ('Conta a partir de F2, F3 e F8: 2 h + 3 h + 12 h = 17 h no mínimo; com o cólon levando até 48 h, passa de 2 dias', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'prato': 'A garfada: arroz com feijão', 'mapa': 'O mapa da viagem',
                'boca': 'Etapa 1: a boca', 'engolir': 'Etapa 2: engolir e a epiglote',
                'esofago': 'Etapa 3: o esôfago e a peristalse', 'estomago': 'Etapa 4: o estômago',
                'delgado': 'Etapa 5: o intestino delgado', 'ajudantes': 'Fígado, vesícula e pâncreas',
                'vilosidades': 'As vilosidades: nutrientes no sangue', 'sangue': 'Veia porta e fígado',
                'grosso': 'Etapa 6: o intestino grosso', 'bacterias': 'As bactérias do intestino',
                'saida': 'Etapa 7: a saída', 'relogio': 'Quanto tempo leva', 'resumo': 'Resumo'}

DESCRICAO = """Para onde vai a comida depois que você engole? Neste vídeo a gente segue UMA garfada de arroz com feijão por dentro do corpo: os dentes trituram, a saliva começa a quebrar o amido, a epiglote fecha o caminho do ar, o esôfago empurra em ondas, o estômago mistura tudo com ácido, o intestino delgado recebe a bile e o suco do pâncreas e absorve os nutrientes pelas vilosidades, o sangue leva tudo ao fígado e o intestino grosso tira a água, com a ajuda de trilhões de bactérias. O resto sai do corpo.

Um painel mostra a etapa (de 1 a 7), o tamanho de cada trecho e o tempo típico em cada um. Os tempos são sempre "em geral": mudam muito de pessoa para pessoa e de refeição para refeição.

Cada quadro é pixel art desenhada por código, e a música é original. O corpo é um manequim genérico, desenhado em corte simplificado.

Capítulos
{capitulos}

Simplificado de propósito
- O corpo e os órgãos são estilizados: menos dobras, cores de desenho e proporções ajustadas para caber na tela. O intestino delgado aparece com poucas voltas.
- As cenas andam em velocidade de desenho, não de verdade. No estômago, as ondas de mistura vêm a cada ~20 segundos (OpenStax); aqui elas aparecem bem mais rápido. A peristalse do esôfago foi colocada no ritmo da música.
- As fontes não concordam nos tempos: o OpenStax dá 2 a 4 h no estômago, 3 a 5 h no delgado e 12 a 24 h no grosso; a Mayo Clinic fala em cerca de 6 h para estômago + delgado e até 36 a 48 h no cólon; a Cleveland Clinic dá 40 a 120 minutos ou mais no estômago. Por isso mostramos faixas e a soma vai de uns 17 horas a mais de 2 dias.
- O tamanho do intestino delgado depende de como se mede: 3 a 5 m numa pessoa viva (em cadáver parece mais longo). A área de 30 m² é uma estimativa recente; livros mais antigos falam em 200 m².
- A amilase da saliva só começa o trabalho; a maior parte do amido é digerida no intestino delgado. A gordura do tempero vai para os vasos linfáticos, não direto para a veia porta.
- O arroz com feijão tem pouca gordura; a gordura do exemplo vem do tempero.
- A saída foi representada por uma porta, sem detalhes.

Fontes
{fontes}

#digestao #corpohumano #comofunciona #pixelart #arrozcomfeijao #ciencia #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nas cenas de close
# o protagonista fica entre x 60 e 240 (centro ~150); a boca, entre 90 e 268.
# O relógio (linha do tempo larga) não tem corte vertical.
PREFIXO = 'ep15-garfada'
CORTES = [
    dict(id='c1', de=('engolir', 0.0), ate=('engolir', 24.0), x=60, gancho=['A TAMPINHA', 'DA GARGANTA'],
         titulo='Por que a comida não vai para o pulmão? 🫁',
         descricao='Na garganta há dois canos: um do ar e um da comida. Quando você engole, a epiglote, uma tampinha, dobra e fecha o caminho do ar.'),
    dict(id='c2', de=('esofago', 0.0), ate=('esofago', 30.0), x=50, gancho=['ESÔFAGO NO', 'RITMO'],
         titulo='O esôfago empurra a comida em ondas 🎵',
         descricao='O esôfago tem uns 25 cm. Anéis de músculo apertam em ondas e empurram a comida: é a peristalse. Aqui, cada aperto cai numa batida da música.'),
    dict(id='c3', de=('estomago', 0.0), ate=('estomago', 36.0), x=60, gancho=['DENTRO DO', 'ESTÔMAGO'],
         titulo='O que acontece com a comida no estômago 🍛',
         descricao='Ácido com pH de 1,5 a 3,5, muco que protege a parede, pepsina quebrando proteína e ondas de músculo que transformam a garfada em quimo. Em geral, 2 a 4 horas.'),
    dict(id='c4', de=('vilosidades', 0.0), ate=('vilosidades', 30.0), x=57, gancho=['30 METROS', 'DOBRADOS'],
         titulo='A parede do intestino que cobriria 30 metros quadrados',
         descricao='O intestino delgado é forrado de vilosidades, dedinhos com vasos de sangue. É por elas que a glicose e os aminoácidos caem no sangue.'),
    dict(id='c5', de=('bacterias', 0.0), ate=('bacterias', 30.0), x=57, gancho=['TRILHÕES DE', 'BACTÉRIAS'],
         titulo='As bactérias que moram no seu intestino 🦠',
         descricao='No intestino grosso moram trilhões de bactérias, de mais de 700 espécies. Elas comem a fibra que sobrou (gases, olá feijão) e fazem vitaminas como a K.'),
    dict(id='c6', de=('boca', 0.0), ate=('boca', 36.0), x=88, gancho=['DENTRO DA', 'BOCA'],
         titulo='O que a boca faz com uma garfada de arroz com feijão 🍚',
         descricao='Os dentes trituram (um adulto tem 32), a saliva traz a amilase, que já começa a quebrar o amido do arroz, e a língua junta tudo num bolo pronto para engolir.'),
]
