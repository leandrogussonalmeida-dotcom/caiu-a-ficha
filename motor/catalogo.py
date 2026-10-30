#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — o catálogo das 4 séries de vídeos longos (PT-BR).

Cada episódio: 7 a 9 min, sem voz, música baixa, legendas grandes, todo fato
com fonte. Ritmo: mais rápido que o piloto (o Leandro achou o ep01 lento em
29/10): câmera lenta só onde ela ensina, nada de 36 s parado num passo.

Ordem de produção = a ordem da lista dentro de cada onda. `estado`:
  pronto   roteiro + desenho + checagem de fatos aprovados; renderiza no PC
  fazendo  em produção
  fila     ainda não começou
"""

SERIES = {
    'dentro': 'POR DENTRO',          # a máquina aberta, peça por peça, e funcionando
    'jornada': 'A JORNADA',          # seguir um protagonista por dentro de um sistema
    'voa': 'COMO VOA / FLUTUA',      # força e física: o que segura, o que empurra
    'pixels': 'FEITO DE PIXELS',     # o mundo digital, contado em pixel
}

EPISODIOS = [
    # ---------------------------------------------------------------- onda 1
    dict(id='ep01', serie='dentro', titulo='Como funciona o motor do carro', estado='pronto', onda=1),
    dict(id='ep02', serie='voa', titulo='Como um avião de 400 toneladas voa', estado='pronto', onda=1,
         ideia='Sustentação (asa desvia o ar para baixo, diferença de pressão), empuxo, arrasto, peso; '
               'flaps na decolagem; ângulo de ataque; o que acontece no estol. Protagonista: o avião da '
               'pista ao cruzeiro, com o ar em partículas passando pela asa.'),
    dict(id='ep03', serie='jornada', titulo='A jornada da sua mala no aeroporto', estado='pronto', onda=1,
         ideia='Do check-in (etiqueta com código de barras) às esteiras, raio-x, triagem automática, '
               'carrinho, porão do avião, esteira de chegada. Protagonista: a mala, com a etiqueta.'),
    dict(id='ep04', serie='pixels', titulo='Como a tela do celular faz cada pixel', estado='pronto', onda=1,
         ideia='Subpixels vermelho/verde/azul, mistura de cor, LCD (luz de fundo + cristal líquido + '
               'filtro) contra OLED (cada subpixel acende), resolução, taxa de atualização. Meta: um '
               'canal de pixel explicando pixel.'),
    dict(id='ep05', serie='dentro', titulo='Como a geladeira faz frio', estado='pronto', onda=1,
         ideia='Ciclo de refrigeração: compressor, condensador (grade quente atrás), válvula de expansão, '
               'evaporador; o fluido que ferve frio. Protagonista: uma porção do fluido dando a volta.'),
    # ---------------------------------------------------------------- onda 2
    dict(id='ep06', serie='voa', titulo='Por que um navio de aço flutua', estado='pronto', onda=2),
    dict(id='ep07', serie='jornada', titulo='A jornada de uma mensagem de celular', estado='pronto', onda=2),
    dict(id='ep08', serie='pixels', titulo='Como um videogame desenha um quadro', estado='pronto', onda=2),
    dict(id='ep09', serie='dentro', titulo='Como funciona o relógio mecânico', estado='pronto', onda=2),
    # ---------------------------------------------------------------- onda 3
    dict(id='ep10', serie='voa', titulo='Como o helicóptero voa', estado='pronto', onda=3),
    dict(id='ep11', serie='jornada', titulo='A jornada da água: da represa até a sua tomada', estado='pronto', onda=3),
    dict(id='ep12', serie='pixels', titulo='Como o alto-falante faz som', estado='pronto', onda=3),
    dict(id='ep13', serie='dentro', titulo='Como funciona o motor elétrico', estado='pronto', onda=3),
    # ---------------------------------------------------------------- onda 4
    dict(id='ep14', serie='voa', titulo='Como o submarino afunda e sobe', estado='pronto', onda=4),
    dict(id='ep15', serie='jornada', titulo='A jornada de uma garfada pelo corpo', estado='pronto', onda=4),
    dict(id='ep16', serie='pixels', titulo='Como o processador pensa', estado='pronto', onda=4),
    dict(id='ep17', serie='dentro', titulo='Como funciona a fechadura e a chave', estado='fazendo', onda=4),
    # ---------------------------------------------------------------- onda 5
    dict(id='ep18', serie='voa', titulo='Como um foguete chega ao espaço', estado='pronto', onda=5),
    dict(id='ep19', serie='jornada', titulo='A jornada de um contêiner pelo porto', estado='fazendo', onda=5),
    dict(id='ep20', serie='pixels', titulo='Como funciona o QR code', estado='fazendo', onda=5),
    dict(id='ep21', serie='dentro', titulo='Como funciona a descarga do vaso', estado='fazendo', onda=5),
    # ---------------------------------------------------------------- onda 6
    dict(id='ep22', serie='voa', titulo='Como o balão de ar quente sobe', estado='fazendo', onda=6),
    dict(id='ep23', serie='jornada', titulo='A jornada de uma gota de chuva', estado='fila', onda=6),
    dict(id='ep24', serie='pixels', titulo='Como funciona o Wi-Fi', estado='fila', onda=6),
    dict(id='ep25', serie='dentro', titulo='Como funciona o motor a jato', estado='fila', onda=6),
]

assert len({e['id'] for e in EPISODIOS}) == len(EPISODIOS)
