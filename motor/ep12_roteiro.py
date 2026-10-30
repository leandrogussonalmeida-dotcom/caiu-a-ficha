#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep12 (série FEITO DE PIXELS): Como o alto-falante faz som.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep12_motor.py` e `ep12_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  Som no ar: onda longitudinal de desvios de pressão (compressão e
      rarefação); as partículas do meio não viajam com a onda; o som não se
      propaga no vácuo, não há meio. Wikipedia, "Sound".
  F2  No ar a 20 °C o som anda a cerca de 343 m/s; na água doce a 20 °C,
      1.481 m/s (pouco mais de 4 vezes). Wikipedia, "Speed of sound".
  F3  Faixa audível humana: cerca de 20 Hz a 20.000 Hz; o limite de cima
      costuma baixar com a idade; frequência mais alta = som mais agudo.
      Wikipedia, "Audio frequency".
  F4  Percebemos a frequência como altura (grave/agudo) e a amplitude como
      volume; som = mudança de pressão do ar. FabFilter, "Wave theory".
  F5  CD: PCM a 44.100 Hz, 16 bits, 2 canais; cada amostra é um inteiro com
      sinal de 16 bits, de -32.768 a +32.767; o CD representa até 22,05 kHz
      (frequência de Nyquist de 44,1 kHz). Wikipedia, "Compact Disc Digital Audio".
  F6  48.000 Hz virou o padrão do áudio e do vídeo profissionais.
      Wikipedia, "48,000 Hz".
  F7  DAC: converte o sinal digital num sinal analógico (tensão); a saída é
      uma escadinha, alisada por um filtro passa-baixa; o sinal vai para um
      amplificador que move os alto-falantes; o ADC faz o contrário.
      Wikipedia, "Digital-to-analog converter".
  F8  Alto-falante: a corrente faz da bobina um eletroímã variável numa fenda
      com o campo de um ímã permanente; a força move a bobina e o cone colado
      nela; corrente alternada faz o cone ir e voltar; a aranha (disco de
      tecido ondulado) dá a maior parte da força que traz o cone de volta; a
      borda centra o cone e prende na carcaça; o microfone dinâmico tem o
      mesmo desenho e funciona ao contrário, como gerador.
      Wikipedia, "Loudspeaker".
  F9  O cone ligado à bobina vai e volta e cria ondas de pressão alta e
      baixa no ar. Eminence, "How Speakers Work".
  F10 Woofer: graves e médios, tipicamente de 50 a 2.000 Hz; para os graves
      precisa mover um volume grande de ar. Wikipedia, "Woofer".
  F11 Tweeter: agudos, tipicamente de 2.000 a 20.000 Hz; cone muito pequeno
      e leve para mover rápido. Wikipedia, "Tweeter".
  F12 A trilha deste vídeo é sintetizada por código (ritmo_musica.py), sem
      nada gravado, a 48.000 amostras por segundo (longo.py: SR = 48000),
      gravada em 16 bits (PCM_16) e em 2 canais; o bumbo lo-fi é a conta
      sen(2 pi f t) com f = 48 + 70 e^(-t/0,03) (ritmo_musica.Bateria._kick).
  F13 Contas: 2^16 = 65.536; 44.100 x 2 = 88.200; 343 / f = comprimento da
      onda; 120 batidas por minuto = 2 por segundo; total de números de áudio
      do vídeo = duração x 48.000 x 2.
"""

TITULO = "Como o alto-falante faz som | De números a ar em movimento, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='drop'),            # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),           # 6 s
    dict(id='ar', gen='lofi', bars=12, papel='drop'),               # 36 s
    dict(id='velocidade', gen='lofi', bars=10, papel='drop'),       # 30 s
    dict(id='frequencia', gen='synthwave', bars=15, papel='drop'),  # 36 s
    dict(id='amplitude', gen='lofi', bars=8, papel='drop'),         # 24 s
    dict(id='amostras', gen='lofi', bars=14, papel='drop'),         # 42 s
    dict(id='bits', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='bumbo', gen='lofi', bars=12, papel='drop'),            # 36 s
    dict(id='dac', gen='lofi', bars=8, papel='drop'),               # 24 s
    dict(id='pecas', gen='synthwave', bars=22, papel='drop'),       # 52,8 s
    dict(id='empurra', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='ritmo', gen='house', bars=12, papel='drop', bpm=120),  # 24 s
    dict(id='woofer', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='microfone', gen='lofi', bars=8, papel='drop'),         # 24 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),              # 15 s
]


def _total():
    bpm = dict(lofi=80, synthwave=100, house=124)
    return sum(c['bars'] * 4 * 60.0 / c.get('bpm', bpm[c['gen']]) for c in CAPITULOS)


TOTAL_S = _total()                                   # 481,8 s
NUMEROS = TOTAL_S * 48000 * 2                        # números de áudio do vídeo inteiro
MILHOES = int(round(NUMEROS / 1e6))                  # 46

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "A MÚSICA DESTE VÍDEO É FEITA DE", "*NÚMEROS*, GERADOS POR CÓDIGO.", ('F12',)),
        (6.2, 11.6, "QUEM TRANSFORMA NÚMERO EM SOM?", "ESTE *CONE*. VAMOS ABRIR.", ('F8',)),
    ],
    'ar': [
        (0.5, 7.0, "PRIMEIRO: O QUE É *SOM*?", "COMEÇA COM ALGO EMPURRANDO O AR.", ('F9',)),
        (7.4, 14.4, "O CONE AVANÇA E *APERTA* AS", "MOLÉCULAS DE AR DA FRENTE.", ('F1', 'F9')),
        (14.8, 21.8, "DEPOIS VOLTA E O AR FICA", "*ESPALHADO*: PRESSÃO MAIS BAIXA.", ('F1', 'F9')),
        (22.2, 29.2, "SIGA A MOLÉCULA *ROSA*: SÓ VAI E", "VOLTA. QUEM VIAJA É A *ONDA*.", ('F1',)),
        (29.6, 35.6, "SEM AR, NÃO HÁ O QUE EMPURRAR:", "NO VÁCUO *NÃO EXISTE SOM*.", ('F1',)),
    ],
    'velocidade': [
        (0.5, 7.4, "A ONDA ANDA RÁPIDO: NO AR A 20 °C,", "*343 METROS POR SEGUNDO*.", ('F2',)),
        (7.8, 14.8, "EM 1 SEGUNDO, A FRENTE DA ONDA", "JÁ ESTÁ A *343 M* DO CONE.", ('F2',)),
        (15.2, 22.2, "NA ÁGUA, MAIS DE 4 VEZES MAIS", "RÁPIDO: *1.481 M/S*.", ('F2',)),
        (22.6, 29.4, "E A MOLÉCULA ROSA? CONTINUA", "*NO MESMO LUGAR*, INDO E VOLTANDO.", ('F1',)),
    ],
    'frequencia': [
        (0.5, 7.0, "*FREQUÊNCIA*: QUANTAS VEZES POR", "SEGUNDO O CONE VAI E VOLTA.", ('F4',)),
        (7.4, 14.2, "A CONTA É EM *HERTZ* (HZ):", "220 HZ = 220 VAIVÉNS POR SEGUNDO.", ('F3',)),
        (14.6, 21.4, "FREQUÊNCIA BAIXA: SOM *GRAVE*.", "FREQUÊNCIA ALTA: SOM *AGUDO*.", ('F3', 'F4')),
        (21.8, 28.6, "O OUVIDO HUMANO VAI DE UNS *20 HZ*", "ATÉ UNS *20.000 HZ*.", ('F3',)),
        (29.0, 35.6, "COM A IDADE, O LIMITE DE CIMA", "COSTUMA *BAIXAR*.", ('F3',)),
    ],
    'amplitude': [
        (0.5, 7.4, "*AMPLITUDE*: O QUANTO O CONE", "ANDA EM CADA VAIVÉM.", ('F4',)),
        (7.8, 15.0, "EMPURRÃO MAIOR, AR MAIS APERTADO:", "O SOM FICA MAIS *ALTO*.", ('F4',)),
        (15.4, 23.4, "MESMA FREQUÊNCIA, MESMA NOTA.", "SÓ O *VOLUME* MUDA.", ('F4',)),
    ],
    'amostras': [
        (0.5, 7.4, "NO COMPUTADOR, O SOM VIRA UMA", "LISTA DE *NÚMEROS*. COMO?", ()),
        (7.8, 14.8, "MEDE-SE A ONDA MUITAS VEZES POR", "SEGUNDO. CADA MEDIDA: UMA *AMOSTRA*.", ('F5',)),
        (15.2, 22.2, "NO CD: *44.100 AMOSTRAS* POR", "SEGUNDO, EM CADA CANAL.", ('F5',)),
        (22.6, 29.6, "NO ÁUDIO E NO VÍDEO PROFISSIONAL,", "O PADRÃO É *48.000*.", ('F6',)),
        (30.0, 36.6, "COM 44.100 POR SEGUNDO, O CD", "GUARDA SONS ATÉ *22.050 HZ*...", ('F5',)),
        (37.0, 41.6, "...ACIMA DOS *20.000 HZ*", "QUE A GENTE OUVE.", ('F3',)),
    ],
    'bits': [
        (0.5, 7.4, "CADA AMOSTRA É UM NÚMERO INTEIRO", "DE *16 BITS*: 16 ZEROS OU UNS.", ('F5',)),
        (7.8, 15.0, "16 BITS DÃO *65.536* DEGRAUS,", "DE -32.768 A +32.767.", ('F5', 'F13')),
        (15.4, 23.4, "COM 2 CANAIS, O CD GUARDA *88.200*", "NÚMEROS POR SEGUNDO.", ('F5', 'F13')),
    ],
    'bumbo': [
        (0.5, 7.4, "AGORA, A *NOSSA* MÚSICA. O BUMBO", "DESTE VÍDEO NASCE DE UMA CONTA.", ('F12',)),
        (7.8, 14.8, "A CONTA DIZ ONDE O CONE DEVE", "ESTAR EM CADA AMOSTRA.", ('F12',)),
        (15.2, 22.2, "SÃO *48.000 NÚMEROS* POR SEGUNDO,", "GUARDADOS EM 16 BITS.", ('F12',)),
        (22.6, 29.6, "OS PRIMEIROS NÚMEROS DO BUMBO,", "EM *CÂMERA LENTA*.", ('F12',)),
        (30.0, 35.6, "NENHUM SOM FOI GRAVADO.", "*TUDO É CONTA*.", ('F12',)),
    ],
    'dac': [
        (0.5, 7.4, "PARA TOCAR, OS NÚMEROS VÃO PARA", "O *DAC*: CONVERSOR DIGITAL-ANALÓGICO.", ('F7',)),
        (7.8, 15.0, "ELE TROCA CADA NÚMERO POR UMA", "*TENSÃO*: UMA ESCADINHA ELÉTRICA.", ('F7',)),
        (15.4, 23.4, "UM FILTRO ALISA A ESCADA E O", "*AMPLIFICADOR* DÁ FORÇA AO SINAL.", ('F7',)),
    ],
    'pecas': [
        (0.5, 7.4, "AGORA, POR DENTRO DO ALTO-FALANTE.", "UM CORTE BEM NO MEIO.", ()),
        (7.8, 14.8, "ATRÁS, UM *ÍMÃ PERMANENTE* FAZ UM", "CAMPO MAGNÉTICO FORTE NUMA FENDA.", ('F8',)),
        (15.2, 22.2, "NA FENDA FICA A *BOBINA MÓVEL*:", "UM FIO ENROLADO NUM TUBO.", ('F8',)),
        (22.6, 29.6, "A BOBINA É COLADA NO *CONE*.", "É ELE QUE EMPURRA O AR.", ('F8', 'F9')),
        (30.0, 37.0, "A *ARANHA*, DE TECIDO ONDULADO,", "PUXA O CONE DE VOLTA AO LUGAR.", ('F8',)),
        (37.4, 44.4, "A *BORDA* FLEXÍVEL PRENDE A BEIRA", "DO CONE E O MANTÉM NO CENTRO.", ('F8',)),
        (44.8, 52.2, "A *CARCAÇA* SEGURA TUDO.", "DOIS *FIOS* TRAZEM O SINAL.", ('F8',)),
    ],
    'empurra': [
        (0.5, 7.4, "QUANDO PASSA CORRENTE, A BOBINA", "VIRA UM *ELETROÍMÃ*.", ('F8',)),
        (7.8, 14.8, "CORRENTE NUM SENTIDO: A FORÇA", "*EMPURRA* A BOBINA PARA FORA.", ('F8',)),
        (15.2, 22.2, "NO OUTRO SENTIDO, A FORÇA *PUXA*", "A BOBINA PARA DENTRO.", ('F8',)),
        (22.6, 29.6, "O SINAL TROCA DE SENTIDO SEM PARAR:", "O CONE *VAI E VOLTA* JUNTO.", ('F8',)),
        (30.0, 35.6, "O CONE COPIA A FORMA DA ONDA", "E A ENTREGA AO *AR*.", ('F9',)),
    ],
    'ritmo': [
        (0.5, 7.6, "AGORA *DE VERDADE*: O CONE SEGUE", "CADA BUMBO DA MÚSICA DESTE VÍDEO.", ('F12',)),
        (8.0, 15.8, "A 120 BATIDAS POR MINUTO,", "SÃO *2 EMPURRÕES POR SEGUNDO*.", ('F13',)),
        (16.2, 23.6, "CADA EMPURRÃO SAI A *343 M/S*", "ATÉ O SEU OUVIDO.", ('F2',)),
    ],
    'woofer': [
        (0.5, 7.4, "GRAVE PEDE MOVER *MUITO AR*:", "CONE GRANDE, O *WOOFER*.", ('F10',)),
        (7.8, 14.8, "UM WOOFER TÍPICO TOCA DE", "*50 A 2.000 HZ*.", ('F10',)),
        (15.2, 22.2, "AGUDO PEDE IR E VOLTAR RÁPIDO:", "CONE PEQUENO E LEVE, O *TWEETER*.", ('F11',)),
        (22.6, 29.6, "UM TWEETER TÍPICO TOCA DE", "*2.000 A 20.000 HZ*.", ('F11',)),
    ],
    'microfone': [
        (0.5, 7.4, "O *MICROFONE* DINÂMICO TEM AS", "MESMAS PEÇAS E FAZ O CONTRÁRIO.", ('F8',)),
        (7.8, 15.0, "O AR EMPURRA A MEMBRANA, A BOBINA", "SE MEXE NO ÍMÃ E GERA *CORRENTE*.", ('F8',)),
        (15.4, 23.4, "UM *ADC* MEDE ESSE SINAL E", "O TRANSFORMA EM NÚMEROS DE NOVO.", ('F7',)),
    ],
    'resumo': [
        (0.5, 9.0, "NÚMEROS, DAC, AMPLIFICADOR,", "BOBINA, CONE, AR: E O *SOM* CHEGA.", ('F7', 'F8')),
        (9.4, 19.0, "*44.100* OU *48.000* NÚMEROS POR", "SEGUNDO, EM CADA CANAL.", ('F5', 'F6')),
        (19.4, 29.4, "ESTE VÍDEO INTEIRO TEM UNS", f"*{MILHOES} MILHÕES* DE NÚMEROS DE ÁUDIO.", ('F12', 'F13')),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "Sound"', 'https://en.wikipedia.org/wiki/Sound'),
    'F2': ('Wikipedia, "Speed of sound"', 'https://en.wikipedia.org/wiki/Speed_of_sound'),
    'F3': ('Wikipedia, "Audio frequency"', 'https://en.wikipedia.org/wiki/Audio_frequency'),
    'F4': ('FabFilter, "Wave theory" (The science of sound)', 'https://www.fabfilter.com/learn/science-of-sound/wave-theory'),
    'F5': ('Wikipedia, "Compact Disc Digital Audio"', 'https://en.wikipedia.org/wiki/Compact_Disc_Digital_Audio'),
    'F6': ('Wikipedia, "48,000 Hz"', 'https://en.wikipedia.org/wiki/48,000_Hz'),
    'F7': ('Wikipedia, "Digital-to-analog converter"', 'https://en.wikipedia.org/wiki/Digital-to-analog_converter'),
    'F8': ('Wikipedia, "Loudspeaker"', 'https://en.wikipedia.org/wiki/Loudspeaker'),
    'F9': ('Eminence, "How Speakers Work"', 'https://www.eminence.com/support/how-speakers-work'),
    'F10': ('Wikipedia, "Woofer"', 'https://en.wikipedia.org/wiki/Woofer'),
    'F11': ('Wikipedia, "Tweeter"', 'https://en.wikipedia.org/wiki/Tweeter'),
    'F12': ('O código deste canal: ritmo_musica.py (o bumbo e a trilha) e longo.py (48.000 amostras por segundo, 16 bits, 2 canais)', None),
    'F13': ('Contas: 2^16, 44.100 x 2, 343 / frequência, 120 / 60, duração x 48.000 x 2', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'ar': 'O que é som: o ar apertado e espalhado',
                'velocidade': '343 metros por segundo', 'frequencia': 'Frequência: grave e agudo',
                'amplitude': 'Amplitude: o volume', 'amostras': 'Som digital: amostras',
                'bits': '16 bits', 'bumbo': 'O bumbo deste vídeo em números',
                'dac': 'O DAC: de número a tensão', 'pecas': 'As peças do alto-falante',
                'empurra': 'Como a bobina empurra o cone', 'ritmo': 'O cone no ritmo da música',
                'woofer': 'Woofer e tweeter', 'microfone': 'O microfone faz o contrário',
                'resumo': 'Resumo'}

DESCRICAO = """Como um alto-falante transforma números em som? A gente começa pelo ar: um cone empurra as moléculas, o ar fica apertado e espalhado, e a onda anda a 343 metros por segundo enquanto cada molécula só vai e volta no lugar. Depois vê frequência (grave e agudo), amplitude (volume), como o som vira números (44.100 ou 48.000 amostras por segundo, 16 bits), o DAC que transforma número em tensão e, por dentro do alto-falante, o ímã, a bobina móvel, o cone, a aranha e a borda. No fim: woofer e tweeter, e o microfone, que faz o caminho contrário.

Cada quadro é pixel art desenhada por código, e a música é original e também feita por código: nenhum som foi gravado. O bumbo que aparece em números é o bumbo de verdade da trilha deste vídeo, e no capítulo do ritmo o cone se mexe exatamente em cada bumbo da música, porque o desenho e o som leem a mesma lista de eventos.

Capítulos
{capitulos}

Simplificado de propósito
- Na tela tudo está em câmera lenta: o cone vai e volta poucas vezes por segundo e a onda anda poucos pixels por segundo. Os números do painel (Hz, 343 m/s) são os de verdade.
- O deslocamento do cone e das moléculas está muito exagerado para dar para ver; num som comum as moléculas se mexem bem menos que a espessura de um fio de cabelo.
- O ar é desenhado como uma grade de bolinhas. O ar de verdade tem bilhões de moléculas se mexendo em todas as direções; aqui só aparece um tremor pequeno e o vaivém da onda.
- A força na bobina é a força do campo do ímã sobre o fio com corrente (a corrente atravessa o campo na fenda). No corte, o ponto e o x mostram o sentido da corrente no fio (saindo e entrando na tela).
- No alto-falante de verdade a força e o deslocamento não seguem a corrente de forma perfeita (o cone tem massa, a caixa tem ar, cada falante tem a sua ressonância).
- Os números do bumbo são os da conta do bumbo lo-fi da trilha antes da mixagem (antes do volume e do master); os números de amostra que passam no gancho são da trilha do próprio capítulo.
- A escadinha do DAC está desenhada com poucos degraus, bem largos; na vida real são 44.100 ou 48.000 degraus por segundo.
- Os valores de 50 a 2.000 Hz (woofer) e 2.000 a 20.000 Hz (tweeter) são faixas típicas; cada modelo tem a sua.
- "Uns {milhoes} milhões de números": duração do vídeo x 48.000 amostras por segundo x 2 canais, no áudio que sai do código, antes da compressão do YouTube.

Fontes
{fontes}

#altofalante #som #comofunciona #pixelart #audio #nossomundopixel""".replace('{milhoes}', str(MILHOES))

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. Nas cenas do ar o
# alto-falante em corte fica em x 10..90 e o ar logo à direita; o bumbo em
# números fica em 0..180 no modo vertical; no empurra o falante maior fica em
# 30..126.
PREFIXO = 'ep12-altofalante'
CORTES = [
    dict(id='c1', de=('ar', 0.0), ate=('ar', 29.6), x=8, gancho=['O QUE É', 'SOM?'],
         titulo='O que é som? O ar apertado e espalhado 🔊',
         descricao='Um cone empurra as moléculas de ar: elas ficam apertadas, depois espalhadas. Cada molécula só vai e volta no lugar; quem viaja é a onda de pressão.'),
    dict(id='c2', de=('frequencia', 0.0), ate=('frequencia', 28.6), x=6, gancho=['GRAVE OU', 'AGUDO?'],
         titulo='Grave ou agudo: o que é frequência? 🎵',
         descricao='Frequência é quantas vezes por segundo o cone vai e volta, em hertz. Frequência baixa, som grave; alta, agudo. O ouvido humano vai de uns 20 Hz até uns 20.000 Hz.'),
    dict(id='c3', de=('amostras', 7.8), ate=('amostras', 36.6), x=40, gancho=['O SOM VIRA', 'NÚMERO'],
         titulo='Como o som vira números: 44.100 amostras por segundo',
         descricao='O som digital é a onda medida muitas vezes por segundo. No CD são 44.100 amostras por segundo em cada canal; no vídeo, o padrão é 48.000.'),
    dict(id='c4', de=('bumbo', 0.0), ate=('bumbo', 36.0), x=0, gancho=['UM BUMBO', 'EM NÚMEROS'],
         titulo='O bumbo desta música é só uma conta 🥁',
         descricao='A trilha do canal é feita por código, sem nada gravado: o bumbo nasce de uma conta que diz onde o cone deve estar em cada uma das 48.000 amostras por segundo.'),
    dict(id='c5', de=('empurra', 0.0), ate=('empurra', 35.6), x=22, gancho=['COMO O CONE', 'SE MEXE'],
         titulo='Como a bobina empurra o cone do alto-falante ⚡',
         descricao='Quando passa corrente, a bobina vira um eletroímã no campo do ímã permanente: num sentido ela é empurrada para fora, no outro, puxada para dentro. O cone vai e volta junto.'),
    dict(id='c6', de=('ritmo', 0.0), ate=('ritmo', 24.0), x=8, gancho=['NO RITMO', 'DO BUMBO'],
         titulo='Um alto-falante seguindo cada bumbo da música 🔊',
         descricao='O cone deste desenho se mexe em cada bumbo da própria trilha do vídeo: a 120 batidas por minuto, 2 empurrões por segundo, e cada um sai pelo ar a 343 m/s.'),
]
