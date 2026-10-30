#!/usr/bin/env python3
"""NOSSO MUNDO PIXEL — ep08 (série FEITO DE PIXELS): Como um videogame desenha um quadro.

O roteiro é dado, não código: capítulos, trilha de cada um e legendas com o
instante (segundos relativos ao começo do capítulo). O desenho mora em
`ep08_motor.py` e `ep08_desenho.py`.

Legenda: até 2 linhas, até 37 caracteres (fonte 2x, 448 px). *palavra* sai
em amarelo. Mínimo de leitura: 4 s.

FATOS E FONTES (todas lidas em 30/10/2026)
  F1  O laço do jogo: a cada volta, processa a entrada, atualiza o estado do
      jogo e desenha. Java Design Patterns, "Game Loop".
  F2  60 quadros por segundo é considerado há muito tempo o mínimo para jogo
      liso; um jogo pode ter média de 60 e parecer travado por causa do tempo
      de cada quadro (frame time). Wikipedia, "Frame rate".
  F3  1 s / 30 = 33,3 ms; 1 s / 60 = 16,7 ms; 1 s / 120 = 8,3 ms. (conta)
  F4  Jogos testam colisão com formas invisíveis simples (hitbox, caixas
      alinhadas aos eixos) a cada passo da simulação. Wikipedia, "Collision detection".
  F5  Jogo de tiles: a área de jogo é feita de imagens pequenas (tiles) numa
      grade; reaproveitar tiles economiza memória; 8 x 8 pixels virou o tamanho
      de tile mais comum. Wikipedia, "Tile-based video game".
  F6  Sprite: imagem 2D integrada a uma cena maior, que se move por cima do
      fundo sem apagar o fundo. Wikipedia, "Sprite (computer graphics)".
  F7  Paralaxe: o fundo passa mais devagar que a frente e dá ilusão de
      profundidade. Wikipedia, "Parallax scrolling".
  F8  Algoritmo do pintor: pinta do mais longe para o mais perto, por cima do
      que já está lá; o nome vem dos pintores. Wikipedia, "Painter's algorithm".
  F9  Malha de triângulos: triângulos ligados por lados e vértices comuns.
      Wikipedia, "Triangle mesh".
  F10 Vertex shader: roda uma vez para cada vértice e leva a posição 3D para a
      coordenada 2D na tela; shaders rodam na GPU. Wikipedia, "Shader".
  F11 Rasterização de triângulo: entra o pixel cujo centro fica dentro do
      triângulo. Wikipedia, "Rasterisation".
  F12 Z-buffer: guarda a profundidade de cada pixel; o novo só substitui se
      estiver mais perto; costuma ser feito no hardware da placa de vídeo.
      Wikipedia, "Z-buffering".
  F13 Textura: imagem 2D aplicada sobre o modelo 3D; cada vértice ganha uma
      coordenada de textura (UV). Wikipedia, "Texture mapping".
  F14 Sombreamento: a cor das faces muda com o ângulo da superfície em relação
      à luz. Wikipedia, "Shading".
  F15 Pixel shader calcula a cor de cada pixel; shaders rodam em paralelo na
      GPU; desenhar a imagem é um problema "embaraçosamente paralelo".
      Wikipedia, "Shader".
  F16 GPUs modernas têm centenas ou milhares de unidades de cálculo; as
      funções gráficas são em geral independentes. Wikipedia, "Graphics processing unit".
  F17 Framebuffer: parte da memória com a imagem de um quadro inteiro que
      alimenta a tela. Wikipedia, "Framebuffer".
  F18 Buffer duplo: um buffer está na tela (frente), o outro recebe o desenho
      (trás); quando o de trás fica pronto, os papéis trocam; a cópia costuma
      ser sincronizada com a varredura da tela para evitar o rasgo.
      Wikipedia, "Multiple buffering".
  F19 Rasgo (tearing): a tela mostra pedaços de vários quadros numa mesma
      varredura; vsync segura a placa até a tela terminar; o vsync causa atraso
      na resposta (input lag). Wikipedia, "Screen tearing".
  F20 1.920 x 1.080 = 2.073.600 pixels; x 60 = 124.416.000 por segundo. (conta)

NÃO LIDAS (bloqueadas na hora da pesquisa): gameprogrammingpatterns.com/game-loop.html,
developer.mozilla.org/en-US/docs/Games/Anatomy. Não usadas.
"""

TITULO = "Como um videogame desenha um quadro | 16,7 ms por dentro, em pixel art"
LINGUA = 'pt'

CAPITULOS = [
    dict(id='gancho', gen='lofi', bars=4, papel='break'),           # 12 s
    dict(id='titulo', gen='lofi', bars=2, papel='break'),           # 6 s
    dict(id='jogo', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='laco', gen='lofi', bars=10, papel='drop'),             # 30 s
    dict(id='controle', gen='lofi', bars=8, papel='drop'),          # 24 s
    dict(id='fisica', gen='lofi', bars=14, papel='drop'),           # 42 s
    dict(id='tiles', gen='chiptune', bars=22, papel='drop'),        # 35,2 s
    dict(id='camadas', gen='lofi', bars=12, papel='drop'),          # 36 s
    dict(id='malha', gen='synthwave', bars=15, papel='drop'),       # 36 s
    dict(id='raster', gen='lofi', bars=12, papel='drop'),           # 36 s
    dict(id='profundidade', gen='lofi', bars=12, papel='drop'),     # 36 s
    dict(id='gpu', gen='chiptune', bars=22, papel='drop'),          # 35,2 s
    dict(id='buffer', gen='lofi', bars=14, papel='drop'),           # 42 s
    dict(id='fps', gen='lofi', bars=12, papel='drop'),              # 36 s
    dict(id='resumo', gen='lofi', bars=10, papel='drop'),           # 30 s
    dict(id='fim', gen='lofi', bars=5, papel='break'),              # 15 s
]

LEGENDAS = {
    'gancho': [
        (0.6, 6.0, "NUM JOGO A 60 QUADROS POR SEGUNDO,", "SAI UMA IMAGEM A CADA *16,7 MS*.", ('F3',)),
        (6.2, 11.6, "O QUE ACONTECE NESSE PISCAR?", "VAMOS *PAUSAR* UM QUADRO.", ()),
    ],
    'jogo': [
        (0.8, 7.4, "UM JOGO DE PLATAFORMA INVENTADO", "PARA ESTE VÍDEO.", ()),
        (7.8, 14.6, "PARECE MOVIMENTO, MAS SÃO IMAGENS", "*PARADAS*, UMA ATRÁS DA OUTRA.", ('F2',)),
        (15.0, 21.8, "CADA IMAGEM É UM *QUADRO*. MUITOS", "JOGOS MIRAM EM *60 POR SEGUNDO*.", ('F2',)),
        (22.2, 29.4, "1 SEGUNDO / 60 = *16,7 MS*.", "ESSE É O ORÇAMENTO DE CADA QUADRO.", ('F3',)),
    ],
    'laco': [
        (0.5, 7.2, "POR DENTRO, TODO JOGO RODA UM *LAÇO*:", "OS MESMOS PASSOS, QUADRO A QUADRO.", ('F1',)),
        (7.6, 14.8, "1: *LER O CONTROLE*.", "2: *ATUALIZAR* O MUNDO DO JOGO.", ('F1',)),
        (15.2, 22.0, "3: *DESENHAR* A IMAGEM.", "4: *MOSTRAR*. E DE NOVO.", ('F1',)),
        (22.4, 29.6, "VAMOS SEGUIR UM QUADRO SÓ, EM", "*CÂMERA LENTA*, DE 0 A 16,7 MS.", ('F3',)),
    ],
    'controle': [
        (0.5, 7.4, "PASSO 1: O JOGO PERGUNTA AO", "CONTROLE O QUE ESTÁ APERTADO.", ('F1',)),
        (7.8, 15.0, "CADA BOTÃO TEM DOIS ESTADOS:", "*APERTADO* OU *SOLTO*.", ()),
        (15.4, 23.4, "NESTE QUADRO: DIREITA E *PULO*.", "O JOGO ANOTA E SEGUE.", ('F1',)),
    ],
    'fisica': [
        (0.5, 7.4, "PASSO 2: *ATUALIZAR*. NADA É", "DESENHADO AINDA: SÓ CONTAS.", ('F1',)),
        (7.8, 14.8, "O PULO DÁ AO HERÓI UMA", "VELOCIDADE PARA *CIMA*.", ()),
        (15.2, 22.2, "A CADA QUADRO, A *GRAVIDADE* TIRA", "UM POUCO DESSA VELOCIDADE.", ()),
        (22.6, 29.6, "CADA PONTO: ONDE O HERÓI ESTARÁ NUM", "QUADRO. O PULO VIRA *DEGRAUS*.", ()),
        (30.0, 36.0, "*COLISÃO*: O JOGO TESTA SE CAIXAS", "INVISÍVEIS SE ENCOSTAM.", ('F4',)),
        (36.4, 41.6, "ENCOSTOU NA MOEDA: *+1*.", "NA PLATAFORMA: PARA DE CAIR.", ('F4',)),
    ],
    'tiles': [
        (0.5, 6.8, "PASSO 3: *DESENHAR*. PRIMEIRO, O", "JEITO CLÁSSICO DOS JOGOS 2D.", ()),
        (7.2, 14.0, "O CENÁRIO É MONTADO COM *TILES*:", "QUADRADINHOS NUMA GRADE.", ('F5',)),
        (14.4, 21.2, "POUCOS DESENHOS, REPETIDOS MUITAS", "VEZES: *ECONOMIZA MEMÓRIA*.", ('F5',)),
        (21.6, 28.4, "O MAPA DA FASE É UMA TABELA: CADA", "NÚMERO DIZ QUAL TILE VAI ALI.", ('F5',)),
        (28.8, 35.0, "*8 X 8 PIXELS* VIROU O TAMANHO", "DE TILE MAIS COMUM NOS JOGOS.", ('F5',)),
    ],
    'camadas': [
        (0.5, 7.0, "O HERÓI E A MOEDA SÃO *SPRITES*:", "DESENHOS QUE ANDAM SOBRE O FUNDO.", ('F6',)),
        (7.4, 14.2, "A IMAGEM É PINTADA EM *CAMADAS*,", "DO FUNDO PARA A FRENTE.", ('F8',)),
        (14.6, 21.4, "O QUE VEM DEPOIS COBRE O QUE VEIO", "ANTES: O *ALGORITMO DO PINTOR*.", ('F8',)),
        (21.8, 28.6, "O FUNDO ANDA MAIS DEVAGAR QUE A", "FRENTE: PARECE TER *PROFUNDIDADE*.", ('F7',)),
        (29.0, 35.6, "POR ÚLTIMO, O *PLACAR*,", "POR CIMA DE TUDO.", ('F8',)),
    ],
    'malha': [
        (0.5, 7.0, "E NUM JOGO *3D*? O MESMO HERÓI", "VIRA UM MODELO DE *TRIÂNGULOS*.", ('F9',)),
        (7.4, 14.2, "UMA *MALHA*: TRIÂNGULOS QUE", "*COMPARTILHAM* LADOS E CANTOS.", ('F9',)),
        (14.6, 21.4, "CADA CANTO É UM *VÉRTICE*:", "UM PONTO COM POSIÇÃO EM 3D.", ('F9', 'F10')),
        (21.8, 28.6, "A GPU RODA UM PROGRAMA PARA CADA", "VÉRTICE: O *VERTEX SHADER*.", ('F10',)),
        (29.0, 35.6, "ELE LEVA O PONTO 3D PARA O LUGAR", "CERTO NA *TELA 2D*.", ('F10',)),
    ],
    'raster': [
        (0.5, 7.0, "QUAIS PIXELS CADA TRIÂNGULO COBRE?", "É A *RASTERIZAÇÃO*.", ('F11',)),
        (7.4, 14.2, "ENTRA O PIXEL CUJO *CENTRO* CAI", "DENTRO DO TRIÂNGULO.", ('F11',)),
        (14.6, 21.4, "PARA CADA PIXEL, OUTRO PROGRAMA", "CALCULA A COR: O *PIXEL SHADER*.", ('F15',)),
        (21.8, 28.6, "A COR MUDA COM O ÂNGULO", "ENTRE A SUPERFÍCIE E A *LUZ*...", ('F14',)),
        (29.0, 35.6, "...E COM UMA IMAGEM COLADA NO", "MODELO: A *TEXTURA*.", ('F13',)),
    ],
    'profundidade': [
        (0.5, 7.0, "E SE DOIS TRIÂNGULOS CAEM", "NO MESMO PIXEL?", ()),
        (7.4, 14.2, "A GPU GUARDA A *PROFUNDIDADE* DE", "CADA PIXEL: É O *Z-BUFFER*.", ('F12',)),
        (14.6, 21.4, "UM TRIÂNGULO NOVO MAIS PERTO?", "ELE *PINTA POR CIMA*.", ('F12',)),
        (21.8, 28.6, "MAIS LONGE QUE O GUARDADO?", "*FICA ESCONDIDO*. NÃO PINTA.", ('F12',)),
        (29.0, 35.6, "ASSIM, O QUE ESTÁ NA FRENTE", "SEMPRE APARECE NA FRENTE.", ('F12',)),
    ],
    'gpu': [
        (0.5, 7.0, "UMA TELA *1.920 X 1.080*", "TEM 2.073.600 PIXELS.", ('F20',)),
        (7.4, 14.2, "A 60 QUADROS POR SEGUNDO, SÃO", "*124.416.000* PIXELS POR SEGUNDO.", ('F20',)),
        (14.6, 21.4, "UM DE CADA VEZ NÃO DARIA. A GPU", "FAZ *MUITOS AO MESMO TEMPO*.", ('F15',)),
        (21.8, 28.6, "ELA TEM *CENTENAS OU MILHARES*", "DE UNIDADES DE CÁLCULO.", ('F16',)),
        (29.0, 35.0, "CADA PIXEL É UMA CONTA SEPARADA:", "DÁ PARA FAZER MUITAS JUNTAS.", ('F15', 'F16')),
    ],
    'buffer': [
        (0.5, 7.0, "PASSO 4: *MOSTRAR*. A IMAGEM PRONTA", "FICA NUMA MEMÓRIA: O *FRAMEBUFFER*.", ('F17',)),
        (7.4, 14.2, "SÃO DOIS: UM ESTÁ *NA TELA*, O", "OUTRO RECEBE O DESENHO NOVO.", ('F18',)),
        (14.6, 21.4, "QUANDO O NOVO FICA PRONTO,", "OS DOIS *TROCAM DE PAPEL*.", ('F18',)),
        (21.8, 28.6, "A TELA SE REDESENHA AOS POUCOS.", "TROCAR NO MEIO DÁ UM *RASGO*.", ('F18', 'F19')),
        (29.0, 35.6, "O *VSYNC* ESPERA A TELA TERMINAR", "ANTES DE TROCAR: SEM RASGO.", ('F19',)),
        (36.0, 41.6, "O PREÇO: A RESPOSTA AO CONTROLE", "PODE *ATRASAR* UM POUCO.", ('F19',)),
    ],
    'fps': [
        (0.5, 7.0, "30 QUADROS POR SEGUNDO: CADA UM", "PODE LEVAR ATÉ *33,3 MS*.", ('F3',)),
        (7.4, 14.2, "60 POR SEGUNDO: *16,7 MS*.", "120 POR SEGUNDO: SÓ *8,3 MS*.", ('F3',)),
        (14.6, 21.4, "MAIS QUADROS, MAIS DEGRAUS NO PULO:", "O MOVIMENTO FICA MAIS *LISO*.", ('F2',)),
        (21.8, 28.6, "PARA MUITOS JOGADORES, 60 POR SEGUNDO", "É O MÍNIMO PARA PARECER *LISO*.", ('F2',)),
        (29.0, 35.6, "E A MÉDIA NÃO BASTA: QUADROS QUE", "ATRASAM DÃO *TRANCOS* NO MOVIMENTO.", ('F2', 'F19')),
    ],
    'resumo': [
        (0.5, 8.6, "LER, ATUALIZAR, DESENHAR, MOSTRAR:", "TUDO EM ATÉ *16,7 MS*.", ('F1', 'F3')),
        (9.0, 17.6, "TILES E SPRITES NO 2D. TRIÂNGULOS,", "PIXELS E PROFUNDIDADE NO 3D.", ('F5', 'F9', 'F12')),
        (18.0, 29.4, "E DEPOIS, TUDO DE NOVO:", "*60 VEZES POR SEGUNDO*.", ('F2',)),
    ],
}

FONTES = {
    'F1': ('Java Design Patterns, "Game Loop"', 'https://www.java-design-patterns.com/patterns/game-loop'),
    'F2': ('Wikipedia, "Frame rate"', 'https://en.wikipedia.org/wiki/Frame_rate'),
    'F3': ('Conta: 1 s / 30, 1 s / 60 e 1 s / 120', None),
    'F4': ('Wikipedia, "Collision detection"', 'https://en.wikipedia.org/wiki/Collision_detection'),
    'F5': ('Wikipedia, "Tile-based video game"', 'https://en.wikipedia.org/wiki/Tile-based_video_game'),
    'F6': ('Wikipedia, "Sprite (computer graphics)"', 'https://en.wikipedia.org/wiki/Sprite_(computer_graphics)'),
    'F7': ('Wikipedia, "Parallax scrolling"', 'https://en.wikipedia.org/wiki/Parallax_scrolling'),
    'F8': ('Wikipedia, "Painter\'s algorithm"', 'https://en.wikipedia.org/wiki/Painter%27s_algorithm'),
    'F9': ('Wikipedia, "Triangle mesh"', 'https://en.wikipedia.org/wiki/Triangle_mesh'),
    'F10': ('Wikipedia, "Shader" (vertex shader)', 'https://en.wikipedia.org/wiki/Shader'),
    'F11': ('Wikipedia, "Rasterisation"', 'https://en.wikipedia.org/wiki/Rasterisation'),
    'F12': ('Wikipedia, "Z-buffering"', 'https://en.wikipedia.org/wiki/Z-buffering'),
    'F13': ('Wikipedia, "Texture mapping"', 'https://en.wikipedia.org/wiki/Texture_mapping'),
    'F14': ('Wikipedia, "Shading"', 'https://en.wikipedia.org/wiki/Shading'),
    'F15': ('Wikipedia, "Shader" (pixel shader, execução em paralelo na GPU)', 'https://en.wikipedia.org/wiki/Shader'),
    'F16': ('Wikipedia, "Graphics processing unit"', 'https://en.wikipedia.org/wiki/Graphics_processing_unit'),
    'F17': ('Wikipedia, "Framebuffer"', 'https://en.wikipedia.org/wiki/Framebuffer'),
    'F18': ('Wikipedia, "Multiple buffering"', 'https://en.wikipedia.org/wiki/Multiple_buffering'),
    'F19': ('Wikipedia, "Screen tearing"', 'https://en.wikipedia.org/wiki/Screen_tearing'),
    'F20': ('Conta: 1.920 x 1.080 e x 60', None),
}

CAPITULOS_YT = {'gancho': 'Introdução', 'jogo': 'Imagens paradas, 60 por segundo', 'laco': 'O laço do jogo',
                'controle': 'Passo 1: ler o controle', 'fisica': 'Passo 2: física e colisão',
                'tiles': 'Passo 3: tiles', 'camadas': 'Sprites, camadas e o algoritmo do pintor',
                'malha': '3D: triângulos e vértices', 'raster': 'Rasterização, luz e textura',
                'profundidade': 'O z-buffer', 'gpu': 'A GPU: muitos pixels ao mesmo tempo',
                'buffer': 'Passo 4: framebuffer, rasgo e vsync', 'fps': '30, 60 e 120 quadros por segundo',
                'resumo': 'Resumo'}

DESCRICAO = """O que um videogame faz nos 16,7 milésimos de segundo de um único quadro? A gente pausa um jogo de plataforma inventado para este vídeo e segue um quadro em câmera lenta: o jogo lê o controle, atualiza a física (o pulo, a gravidade, a colisão com a moeda), desenha a imagem do jeito clássico 2D (tiles, sprites, camadas e o algoritmo do pintor) e do jeito 3D (triângulos, vértices, rasterização, luz, textura e z-buffer), e manda tudo para a tela com framebuffer duplo e vsync. No fim, comparamos 30, 60 e 120 quadros por segundo.

Cada quadro é pixel art desenhada por código, e a música é original. O jogo do vídeo roda de verdade: a física é calculada quadro a quadro, a 60 por segundo, e os pontos do pulo que aparecem na tela são as posições que o código calculou.

Capítulos
{capitulos}

Simplificado de propósito
- Os tempos de cada etapa no cronômetro (ler 0,5 ms, atualizar até 3 ms, desenhar até 12 ms) são um exemplo; cada jogo e cada aparelho gasta tempos diferentes. Só os 16,7 ms (1 s / 60) são conta.
- Na vida real o processador (CPU) e a placa de vídeo (GPU) trabalham ao mesmo tempo, em quadros diferentes; aqui mostramos um quadro de cada vez, em fila.
- O jogo 2D do vídeo tem 140 x 78 pixels, ampliados no desenho; as contas de 2.073.600 pixels são de uma tela 1.920 x 1.080.
- O herói 3D tem só 96 triângulos, para dar para ver cada um. A grade da rasterização e a do z-buffer são ampliadas: cada quadradinho é um pixel.
- No z-buffer do vídeo, número menor = mais perto. Placas de vídeo de verdade guardam números com fração e podem usar outra convenção.
- A GPU do desenho tem 128 unidades e faz um bloco de 16 x 8 pixels por vez. GPUs de verdade têm centenas ou milhares de unidades e organizam o trabalho de outros jeitos.
- No capítulo do rasgo a tela varre em câmera lenta e os quadros trocados são de momentos mais distantes do jogo, para o rasgo ficar visível.
- Na rasterização, os pixels exatamente na borda seguem uma regra própria (a regra de cima e da esquerda); não mostramos esse detalhe.
- O gráfico de tempo de cada quadro é um exemplo, não a medição de um jogo.

Fontes
{fontes}

#pixelart #comofunciona #videogame #gpu #programacao #nossomundopixel"""

# ---------------------------------------------------------------- Shorts (cortes verticais)
# x = coluna da tela larga onde começa o recorte de 180 px. O jogo ampliado
# ocupa x 8..288 com o herói perto de x 96; a grade da rasterização, 20..196;
# no modo vertical o z-buffer e as colunas de FPS empilham dentro de 0..180;
# o monitor do framebuffer fica em 20..160.
PREFIXO = 'ep08-quadro'
CORTES = [
    dict(id='c1', de=('fisica', 0.0), ate=('fisica', 36.0), x=40, gancho=['O PULO', 'EM QUADROS'],
         titulo='Como um jogo calcula um pulo, quadro a quadro 🎮',
         descricao='A cada quadro o jogo lê o controle e atualiza a física: o pulo dá velocidade para cima, a gravidade tira um pouco a cada quadro e caixas invisíveis testam a colisão.'),
    dict(id='c2', de=('camadas', 0.0), ate=('camadas', 21.4), x=0, gancho=['O PINTOR', 'DO JOGO'],
         titulo='O algoritmo do pintor: como um jogo 2D monta a imagem',
         descricao='Um jogo 2D pinta a imagem em camadas, do fundo para a frente: céu, montanhas, tiles, sprites e placar. O que vem depois cobre o que veio antes.'),
    dict(id='c3', de=('raster', 0.0), ate=('raster', 21.4), x=18, gancho=['TRIÂNGULO', 'VIRA PIXEL'],
         titulo='Rasterização: como um triângulo vira pixels 🔺',
         descricao='Num jogo 3D, cada triângulo vira pixels: entra o pixel cujo centro cai dentro do triângulo, e um programa na GPU calcula a cor de cada um.'),
    dict(id='c4', de=('profundidade', 0.0), ate=('profundidade', 36.0), x=0, gancho=['QUEM FICA', 'NA FRENTE?'],
         titulo='O z-buffer: como a GPU sabe o que está na frente',
         descricao='A GPU guarda a profundidade de cada pixel. Um triângulo novo só pinta por cima se estiver mais perto; se estiver mais longe, fica escondido.'),
    dict(id='c5', de=('buffer', 14.6), ate=('buffer', 41.6), x=0, gancho=['POR QUE A', 'TELA RASGA'],
         titulo='Por que a imagem do jogo rasga (e o que o vsync faz)',
         descricao='O jogo desenha num buffer enquanto a tela mostra outro. Se trocar no meio da varredura da tela, aparece um rasgo. O vsync espera a tela terminar, mas pode atrasar a resposta.'),
    dict(id='c6', de=('fps', 0.0), ate=('fps', 21.4), x=0, gancho=['30, 60 OU', '120 FPS?'],
         titulo='30, 60 ou 120 quadros por segundo: o mesmo pulo 🕹️',
         descricao='A 30 quadros por segundo cada quadro pode levar até 33,3 ms; a 60, 16,7 ms; a 120, só 8,3 ms. Mais quadros, mais degraus no pulo e movimento mais liso.'),
]
