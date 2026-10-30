#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep20 (série FEITO DE PIXELS): Como funciona o QR code.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep20_motor.py` e `ep20_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

O código da tela é de verdade: versão 2 (25 X 25), nível Q, modo byte, com a
frase NOSSO MUNDO PIXEL. Calculado por `ep20_desenho.py` (codificador próprio,
conferido com a biblioteca segno e lido pelo decodificador do OpenCV).

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  QR = quick-response code; inventado em 1994 por Masahiro Hara, da
      japonesa Denso Wave, para etiquetar peças de carro; Reed–Solomon;
      versões 1 a 40, lado = 4 X versão + 17 (21 X 21 a 177 X 177); o formato
      guarda o nível de correção e a máscara, com 2 cópias, em 15 bits (código
      BCH 15,5); "masking is used to break up patterns in the data area that
      might confuse a scanner"; a mensagem vai da direita para a esquerda em
      zigue-zague; modo byte = 8 bits por caractere; versão 40-L: 7.089
      algarismos ou 2.953 bytes. Wikipedia, "QR code".
  F2  Localizadores nos 3 cantos; qualquer linha pelo centro tem a razão
      1:1:3:1:1, o que deixa ler de qualquer direção; sincronia = módulos
      claros e escuros alternados que dão a coordenada; alinhamento corrige a
      imagem distorcida; o formato é lido primeiro; margem de 4 módulos;
      correção: L 7%, M 15%, Q 25%, H 30%; ISO/IEC em 2000; feito pela
      DENSO WAVE em 1994. KEYENCE, "What is a QR code?".
  F3  Sincronia na linha e na coluna 6; localizador com o separador ocupa 8 X 8;
      alinhamento 5 X 5; o zigue-zague começa no canto de baixo à direita e
      pula as peças fixas; 8 máscaras (0 a 7), aplicadas com XOR só nos dados;
      castigo por fileiras de 5, blocos 2 X 2, padrão de localizador e
      equilíbrio claro/escuro (45% a 55%); vence a de menor castigo; o campo de
      modo tem 4 bits e depois vem a contagem de caracteres.
      Nayuki, "Creating a QR Code step by step".
  F4  Pix: o BR Code é o padrão de QR Code no Brasil (segue o EMV); no QR
      estático todos os dados da iniciação ficam no próprio código; o dinâmico
      leva uma URL acessada na hora da leitura. Banco Central do Brasil,
      Manual de Padrões para Iniciação do Pix (versão 2.10.0).
  F5  Versão 2-Q: 22 bytes de dados e 22 de correção, 1 bloco; versão 1-L: 19
      de dados. Thonky, "Error Correction Code Words and Block Information".
  F6  Capacidade em bytes: versão 1-L 17, versão 2-Q 20.
      Thonky, "Character Capacities by Version, Mode, and Error Correction".
  F7  ASCII: N = 78, O = 79, S = 83, espaço = 32, M = 77, U = 85, D = 68,
      P = 80, I = 73, X = 88, L = 76. freeCodeCamp, "ASCII Table".
  F8  Contas: 25 X 25 = 625; 177 X 177 = 31.329; 4 X 2 + 17 = 25; 17 letras X
      8 = 136 bits; 78 = 01001110; 17 = 00010001; 22 + 22 = 44 bytes; 11 de 44
      = 25%; peças fixas: 147 + 45 + 18 + 25 + 31 = 266; 625 - 266 = 359 =
      44 X 8 + 7.

NÃO LIDAS (pedido de acesso expirou): qrcode.com (Denso Wave) — páginas de
história e de correção de erro. Os mesmos números vieram de F1 e F2.
"""

TITULO = "Como funciona o QR code | Montamos um de verdade, pixel por pixel"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='drop'),                # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),               # 6 s
    dict(id='grade', gen='lofi', bars=10, papel='drop'),                # 30 s
    dict(id='localizador', gen='synthwave', bars=13, papel='drop'),     # 31,2 s
    dict(id='sincronia', gen='lofi', bars=8, papel='drop'),             # 24 s
    dict(id='formato', gen='lofi', bars=8, papel='drop'),               # 24 s
    dict(id='texto', gen='lofi', bars=10, papel='drop'),                # 30 s
    dict(id='bytes', gen='house', bars=20, papel='drop', bpm=120),      # 40 s
    dict(id='correcao', gen='synthwave', bars=18, papel='drop'),        # 43,2 s
    dict(id='mascara', gen='house', bars=20, papel='drop', bpm=120),    # 40 s
    dict(id='mancha', gen='lofi', bars=13, papel='drop'),               # 39 s
    dict(id='leitura', gen='synthwave', bars=13, papel='drop'),         # 31,2 s
    dict(id='versoes', gen='lofi', bars=13, papel='drop'),              # 39 s
    dict(id='historia', gen='lofi', bars=8, papel='drop'),              # 24 s
    dict(id='pix', gen='lofi', bars=8, papel='drop'),                   # 24 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),               # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),                  # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "ESTE QUADRADO É FEITO DE", "*625 PIXELS* CLAROS E ESCUROS.", ('F8',)),
        (6.2, 11.6, "E GUARDA UMA FRASE. VAMOS MONTAR", "UM DE VERDADE, *PEÇA POR PEÇA*.", ()),
    ],
    'grade': [
        (0.5, 7.0, "QR VEM DE *QUICK RESPONSE*:", "RESPOSTA RÁPIDA, EM INGLÊS.", ('F1',)),
        (7.4, 14.4, "CADA QUADRADINHO É UM *MÓDULO*.", "ESCURO VALE *1*, CLARO VALE *0*.", ('F1', 'F3')),
        (14.8, 21.8, "O NOSSO É A *VERSÃO 2*:", "25 X 25 = *625 MÓDULOS*.", ('F1', 'F8')),
        (22.2, 29.6, "EM VOLTA, UMA *MARGEM* LIMPA", "DE 4 MÓDULOS.", ('F2',)),
    ],
    'localizador': [
        (0.5, 7.0, "PRIMEIRO, 3 QUADRADOS GRANDES", "NOS CANTOS: OS *LOCALIZADORES*.", ('F2',)),
        (7.4, 14.4, "QUALQUER LINHA PELO MEIO DELES", "MEDE *1:1:3:1:1*. A CÂMERA BUSCA ISSO.", ('F2',)),
        (14.8, 22.4, "COM 3 CANTOS MARCADOS, ELA SABE", "ONDE É O *TOPO*, MESMO GIRADO.", ('F2',)),
        (22.8, 30.8, "UMA FAIXA CLARA SEPARA CADA UM", "DO RESTO: *8 X 8* COM ELA.", ('F3',)),
    ],
    'sincronia': [
        (0.5, 7.4, "ENTRE ELES, UMA LINHA PONTILHADA:", "A *SINCRONIA*. ELA É UMA RÉGUA.", ('F2', 'F3')),
        (7.8, 14.8, "ELA MOSTRA ONDE FICA CADA COLUNA", "E CADA LINHA DE MÓDULOS.", ('F2',)),
        (15.2, 23.6, "O QUADRADO MENOR É O *ALINHAMENTO*:", "AJUDA QUANDO A IMAGEM SAI TORTA.", ('F2', 'F3')),
    ],
    'formato': [
        (0.5, 7.4, "JUNTO DOS LOCALIZADORES, O *FORMATO*:", "15 BITS, ESCRITOS *2 VEZES*.", ('F1',)),
        (7.8, 15.4, "ELE DIZ O *NÍVEL DE CORREÇÃO*", "E QUAL *MÁSCARA* FOI USADA.", ('F1', 'F2')),
        (15.8, 23.6, "É A PRIMEIRA COISA QUE A CÂMERA LÊ.", "POR ENQUANTO, FICA *EM BRANCO*.", ('F2',)),
    ],
    'texto': [
        (0.5, 7.4, "AGORA, A FRASE: *NOSSO MUNDO PIXEL*.", "17 LETRAS, CONTANDO OS ESPAÇOS.", ('F8',)),
        (7.8, 14.8, "O *N*, POR EXEMPLO, É O NÚMERO 78.", "EM BITS: *01001110*.", ('F7', 'F8')),
        (15.2, 22.2, "CADA LETRA VIRA UM NÚMERO, E O", "NÚMERO VIRA *8 BITS*: 1 BYTE.", ('F1', 'F7')),
        (22.6, 29.6, "NA FRENTE VÃO 4 BITS DE *MODO*", "E 8 COM O TAMANHO: *17*.", ('F3', 'F8')),
    ],
    'bytes': [
        (0.5, 7.4, "OS BITS ENTRAM PELO *CANTO DE BAIXO*,", "À DIREITA, EM COLUNAS DE 2.", ('F3',)),
        (7.8, 14.8, "SOBEM EM *ZIGUE-ZAGUE*, DESCEM NA", "COLUNA SEGUINTE...", ('F1', 'F3')),
        (15.2, 22.2, "...E DESVIAM DAS PEÇAS FIXAS.", "*UMA LETRA* A CADA 2 BATIDAS.", ('F3',)),
        (22.6, 30.0, "NO FIM, BYTES DE ENCHIMENTO", "COMPLETAM OS *22 BYTES* DE DADOS.", ('F5',)),
        (30.4, 39.6, "CADA LETRA FICOU EM ALGUM LUGAR", "DESTE CAMINHO.", ()),
    ],
    'correcao': [
        (0.5, 7.4, "DEPOIS DOS DADOS VÊM BYTES DE", "*CORREÇÃO DE ERRO*: MAIS 22.", ('F5',)),
        (7.8, 14.8, "SÃO CALCULADOS A PARTIR DOS DADOS,", "COM A MATEMÁTICA DE *REED-SOLOMON*.", ('F1',)),
        (15.2, 22.6, "SE PARTE DO CÓDIGO SUMIR, ELES", "DEIXAM *REFAZER* O QUE FALTA.", ('F2',)),
        (23.0, 31.0, "SÃO 4 NÍVEIS: *L 7%*, *M 15%*,", "*Q 25%* E *H 30%* DO CÓDIGO.", ('F2',)),
        (31.4, 42.8, "O NOSSO É *Q*: AGUENTA PERDER UM", "QUARTO. MAIS CORREÇÃO, MENOS LETRAS.", ('F2', 'F6')),
    ],
    'mascara': [
        (0.5, 7.4, "SÓ COM OS DADOS, PODEM SOBRAR", "*BLOCOS* E LISTRAS QUE CONFUNDEM.", ('F1', 'F3')),
        (7.8, 14.8, "ENTÃO ENTRA UMA *MÁSCARA*:", "ELA INVERTE ALGUNS MÓDULOS.", ('F1', 'F3')),
        (15.2, 22.6, "SÃO *8 MÁSCARAS*. CADA UMA LEVA", "CASTIGO POR BLOCOS E LISTRAS.", ('F3',)),
        (23.0, 30.4, "VENCE A DE *MENOS PONTOS*:", "AQUI, A *MÁSCARA 2*.", ('F3',)),
        (30.8, 35.0, "O FORMATO GUARDA O NÚMERO DELA", "E O NÍVEL DE CORREÇÃO.", ('F1',)),
        (35.2, 39.6, "*625 DE 625*:", "O CÓDIGO ESTÁ PRONTO!", ('F8',)),
    ],
    'mancha': [
        (0.5, 7.4, "AGORA, UM ACIDENTE:", "CAIU *CAFÉ* NO CÓDIGO.", ()),
        (7.8, 15.0, "A MANCHA ESTRAGOU *6 DOS 44 BYTES*.", "E A CÂMERA AINDA LÊ A FRASE!", ('F5',)),
        (15.4, 23.4, "A CORREÇÃO DE ERRO REFAZ OS BYTES", "QUE O CAFÉ COBRIU.", ('F1', 'F2')),
        (23.8, 31.0, "MAS TEM LIMITE: NO NÍVEL Q, ATÉ", "*UM QUARTO* DO CÓDIGO.", ('F2', 'F8')),
        (31.4, 38.6, "MANCHA DEMAIS E A FRASE", "*NÃO VOLTA MAIS*.", ('F2',)),
    ],
    'leitura': [
        (0.5, 7.4, "E COMO A CÂMERA LÊ? PRIMEIRO ACHA", "OS 3 *LOCALIZADORES*...", ('F2',)),
        (7.8, 15.0, "...ENDIREITA A IMAGEM, MONTA A GRADE", "PELA SINCRONIA, LÊ O *FORMATO*...", ('F2',)),
        (15.4, 23.0, "...TIRA A MÁSCARA E LÊ OS BYTES", "NO MESMO *ZIGUE-ZAGUE*...", ('F1', 'F3')),
        (23.4, 30.8, "...CORRIGE OS ERROS. PRONTO:", "*NOSSO MUNDO PIXEL*.", ('F1',)),
    ],
    'versoes': [
        (0.5, 7.4, "O NOSSO É PEQUENO. SÃO *40 VERSÕES*;", "A 1 TEM 21 X 21 MÓDULOS.", ('F1',)),
        (7.8, 15.0, "CADA VERSÃO GANHA *4 MÓDULOS*", "DE LADO.", ('F1', 'F2')),
        (15.4, 23.0, "A VERSÃO 40 TEM *177 X 177*:", "*31.329 MÓDULOS*.", ('F1', 'F8')),
        (23.4, 31.0, "NELA CABEM ATÉ *2.953 BYTES*", "OU *7.089 ALGARISMOS*.", ('F1',)),
        (31.4, 38.6, "MAIS MÓDULOS, MAIS PEÇAS DE", "ALINHAMENTO ESPALHADAS.", ('F2',)),
    ],
    'historia': [
        (0.5, 7.4, "O QR CODE FOI INVENTADO EM *1994*", "POR MASAHIRO HARA, DA *DENSO*,", ('F1', 'F2', 'F9')),
        (7.8, 15.4, "(HOJE DENSO WAVE), NO JAPÃO, PARA", "ETIQUETAR *PEÇAS DE CARRO*.", ('F1', 'F9')),
        (15.8, 23.6, "EM 2000 ELE VIROU NORMA ISO/IEC.", "E *SAIU DA FÁBRICA*.", ('F2',)),
    ],
    'pix': [
        (0.5, 7.4, "NO BRASIL, O *PIX* USA QR CODE:", "O PADRÃO SE CHAMA *BR CODE*.", ('F4',)),
        (7.8, 15.4, "NO QR *ESTÁTICO*, CHAVE, VALOR E", "TEXTO VÃO DENTRO DO CÓDIGO.", ('F4',)),
        (15.8, 23.6, "NO *DINÂMICO*, O CÓDIGO LEVA UM", "ENDEREÇO QUE O APP CONSULTA.", ('F4',)),
    ],
    'resumo': [
        (0.5, 9.4, "LOCALIZADORES, SINCRONIA, FORMATO,", "DADOS E *CORREÇÃO DE ERRO*.", ('F2',)),
        (9.8, 19.4, "TUDO EM *625 MÓDULOS*,", "UM PIXEL DE CADA VEZ.", ('F8',)),
        (19.8, 29.6, "APONTE A CÂMERA PARA A TELA:", "ESTE CÓDIGO *FUNCIONA DE VERDADE*.", ()),
    ],
}

FONTES = {
    'F1': ('Wikipedia, "QR code"', 'https://en.wikipedia.org/wiki/QR_code'),
    'F2': ('KEYENCE, "What is a QR code?" (Basics of 2D codes)',
           'https://www.keyence.com/ss/products/auto_id/codereader/basic_2d/qr.jsp'),
    'F3': ('Nayuki, "Creating a QR Code step by step"', 'https://nayuki.io/page/creating-a-qr-code-step-by-step'),
    'F4': ('Banco Central do Brasil, "Manual de Padrões para Iniciação do Pix"',
           'https://www.bcb.gov.br/content/estabilidadefinanceira/pix/Regulamento_Pix/II_ManualdePadroesparaIniciacaodoPix.pdf'),
    'F5': ('Thonky, "Error Correction Code Words and Block Information"',
           'https://www.thonky.com/qr-code-tutorial/error-correction-table'),
    'F6': ('Thonky, "Character Capacities"', 'https://www.thonky.com/qr-code-tutorial/character-capacities'),
    'F7': ('freeCodeCamp, "ASCII Table"', 'https://www.freecodecamp.org/news/ascii-table-hex-to-ascii-value-character-code-chart-2/'),
    'F9': ('Britannica, "Denso Wave": em 1994 era uma divisão da Denso', 'https://britannica.com/topic/Denso-Wave'),
    'F8': ('Contas: 25 X 25; 177 X 177; 4 X versão + 17; 17 X 8; 78 e 17 em binário; 22 + 22; 11 / 44', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'grade': 'A grade de módulos', 'localizador': 'Os 3 localizadores',
                'sincronia': 'Sincronia e alinhamento', 'formato': 'O formato', 'texto': 'A frase vira bits',
                'bytes': 'O zigue-zague dos dados', 'correcao': 'Correção de erro (Reed-Solomon)',
                'mascara': 'As 8 máscaras', 'mancha': 'Caiu café no código', 'leitura': 'Como a câmera lê',
                'versoes': 'As 40 versões', 'historia': '1994: peças de carro', 'pix': 'O Pix e o BR Code',
                'resumo': 'Resumo'}

DESCRICAO = """Como funciona o QR code? A gente monta um de verdade, módulo por módulo, na frente da câmera: a grade de 25 X 25, os 3 localizadores (a razão 1:1:3:1:1 que a câmera procura), a sincronia, o alinhamento e o formato. Depois a frase NOSSO MUNDO PIXEL vira bytes, os bits entram em zigue-zague a partir do canto de baixo, chegam os 22 bytes de correção de erro de Reed-Solomon e as 8 máscaras disputam quem deixa o código mais fácil de ler. No fim cai café no código e ele continua lendo, a câmera faz tudo ao contrário, as 40 versões crescem até 177 X 177 e a gente passa pela fábrica de 1994 e pelo Pix.

Cada quadro é pixel art desenhada por código, e a música é original. O QR code da tela é calculado de verdade (nenhum módulo é desenhado à mão) e funciona: aponte a câmera do celular para o fim do vídeo. Os módulos e os bytes caem nas batidas da música.

Capítulos
{capitulos}

Simplificado de propósito
- O nosso código é a versão 2, nível Q, modo byte. Versões a partir da 7 também têm um bloco com o número da versão, e as maiores dividem os bytes em vários blocos intercalados; aqui há um bloco só.
- Os pontos de castigo das máscaras usam as 4 regras na forma mais comum. Bibliotecas diferentes contam a regra do padrão de localizador de jeitos um pouco diferentes e podem escolher outra máscara; todas dão um código válido.
- A "mancha" conta como estragado todo byte com algum módulo claro coberto de café. Na vida real a câmera pode errar mais ou menos, dependendo da luz e da cor da mancha.
- Correção de erro "de 25%" quer dizer que o nível Q recupera até cerca de um quarto do código; o limite exato depende de onde estão os erros.
- O capítulo do formato e o módulo escuro fixo perto do localizador de baixo foram juntados num só (aparece em laranja).
- As versões maiores (3, 5, 10, 20, 40) foram geradas por uma biblioteca (segno) com a mesma frase.

Fontes
{fontes}

#qrcode #comofunciona #pixelart #tecnologia #pix #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O código ocupa
# x 28..178 (cartão 4..202); o recorte em 13 pega o código inteiro.
PREFIXO = 'ep20-qrcode'
CORTES = [
    dict(id='c1', de=('localizador', 0.0), ate=('localizador', 30.8), x=13, gancho=['PRA QUE', 'ESSES 3?'],
         titulo='Para que servem os 3 quadrados do QR code? 🔳',
         descricao='São os localizadores: qualquer linha pelo meio deles mede 1:1:3:1:1. É isso que a câmera procura, e com 3 cantos marcados ela sabe onde é o topo, mesmo com o código girado.'),
    dict(id='c2', de=('bytes', 0.0), ate=('bytes', 30.0), x=13, gancho=['A FRASE', 'VIRA PIXEL'],
         titulo='Como uma frase vira pixels dentro do QR code',
         descricao='Cada letra vira 8 bits, e os bits entram pelo canto de baixo à direita, subindo e descendo em colunas de 2, desviando das peças fixas. Uma letra a cada 2 batidas da música.'),
    dict(id='c3', de=('mascara', 7.8), ate=('mascara', 39.6), x=13, gancho=['8 MÁSCARAS', '1 VENCE'],
         titulo='As 8 máscaras do QR code: só uma vence 🎭',
         descricao='Uma máscara inverte alguns módulos para quebrar blocos e listras. As 8 levam pontos de castigo e vence a de menos pontos.'),
    dict(id='c4', de=('mancha', 0.0), ate=('mancha', 38.6), x=13, gancho=['CAIU CAFÉ', 'E AGORA?'],
         titulo='Caiu café no QR code e ele ainda funciona ☕',
         descricao='A correção de erro de Reed-Solomon refaz os bytes estragados. No nível Q, o código aguenta perder até um quarto. Mancha demais e a frase não volta.'),
    dict(id='c5', de=('versoes', 0.0), ate=('versoes', 31.0), x=13, gancho=['DE 21 A 177', 'MÓDULOS'],
         titulo='As 40 versões do QR code, de 21 X 21 a 177 X 177',
         descricao='Cada versão ganha 4 módulos de lado. A versão 40 tem 31.329 módulos e guarda até 2.953 bytes.'),
    dict(id='c6', de=('pix', 0.0), ate=('pix', 23.6), x=118, gancho=['O PIX E O', 'QR CODE'],
         titulo='O QR code do Pix por dentro 🇧🇷',
         descricao='O Pix usa o padrão BR Code. No QR estático tudo o que o pagamento precisa vai dentro do código; no dinâmico, o código leva um endereço que o app consulta.'),
]
